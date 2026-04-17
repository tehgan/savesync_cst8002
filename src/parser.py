# This Python file uses the following encoding: utf-8
from dataclasses import dataclass
from pathlib import Path
import re
from PySide6.QtCore import QDateTime, QLocale

from icon_provider import IconProvider


@dataclass
class SaveFile:
    # Path converted to a string
    file_path: str
    file_info: str
    title: str
    description: str
    epoch_last_modified: int
    localized_last_modified: str


@dataclass
class FrameInfo:
    ic_position: int
    ic_format: str
    ic_speed: str


# Get bitfield of graphics format or speed (8 frames max)
def get_icon_slices(ic_fmt: bytes):
    gis_int = int.from_bytes(ic_fmt, byteorder='big')
    gis_bin = format(gis_int, f'016b')
    # Frames are highest (8th) to lowest (1st) by-default, reverse for easier parsing
    return reversed(re.findall('..', gis_bin))


# Currently parses only .gci (Nintendo GameCube) save files, but may be expanded upon and split up in the future
def parse(raw_directory_path: str, icon_provider: IconProvider):
    valid_files = []
    # Check if directory path is valid
    directory_path = Path(raw_directory_path)
    if directory_path.is_dir():
        """
        Case sensitivity must be explicitly set to False, otherwise it'll be true on POSIX platforms (Linux/macOS)
        See https://docs.python.org/3/library/pathlib.html#pathlib.Path.glob
        """
        # Get a list of all .gci (GCN save) files in directory
        file_paths = directory_path.glob('*.gci', case_sensitive=False)
        for file in file_paths:
            valid = True

            # TODO: Might be good to optimize this a little, esp. the beginning;
            #  reading 4 lil bytes probably has a lot of overhead.
            #  Can they be read all at once, then accessed from a bytearray?
            # .gci files don't have a "magic number" so I need to manually verify a few fields
            with open(file, 'rb') as f:
                if not f.seekable():
                    f.close()

                """
                I couldn't find concrete info, but according to GameTDB's wiitdb.txt files
                (https://www.gametdb.com/Wii/Downloads),
                it seems that the title must contain either capital letters or numbers.
                """
                # 3-letter 'title code', e.g. 'GFZ' for F-Zero GX, 'GAF' for Animal Crossing, etc.
                t_code = f.read(3)
                for char in t_code:
                    # chr() converts decimal ASCII values to characters
                    if not chr(char).isupper() and not chr(char).isdecimal():
                        valid = False
                        break

                # Region must be either J (Japan), E (North America), or P (Europe)
                r_code = f.read(1)
                if r_code != b'A' and r_code != b'E' and r_code != b'P':
                    valid = False

                # Publisher code has the same constraints as the title code
                p_code = f.read(2)
                for char in p_code:
                    if not chr(char).isupper() and not chr(char).isdecimal():
                        valid = False
                        break

                # Padding byte must always be 0xFF, left out of surugi's reference
                padding = f.read(1)
                if padding != b'\xff':
                    valid = False

                bnr_fmt = f.read(1)
                match bnr_fmt:
                    case b'\x00':
                        # No banner
                        bnr_seek_count = 0
                    case b'\x01':
                        # CI8; 3072 byte graphic (32x96), 512 byte palette
                        bnr_seek_count = 3584
                    case b'\x02':
                        # RGB5A3; 6144 byte graphic ((32x96) * 2 bytes/colour), no palette
                        bnr_seek_count = 6144
                    case b'\x05' | b'\x06':
                        # Animated banner (CI8 or RGB5A3), unsupported at the moment (and I haven't run into any)
                        valid = False
                    case _:
                        # TODO: Check TimeSplitters + 2 banner format
                        valid = False

                # If file is valid, get other metadata and add it to the list.
                if valid:
                    # Get file info for use as icon dict key, strip excess padding, convert to a string
                    b_file_info = f.read(32)
                    b_file_info = b_file_info.rstrip(b'\x00')
                    file_info = b_file_info.decode('cp1252')
                    # Seconds past 12/31/1999 11:59:59 PM
                    b_last_modified_offset = f.read(4)
                    # Convert binary byte string (from read()) to decimal.
                    # GameCube .gci files are big-endian (as the GameCube is PowerPC-based)
                    last_modified_offset = int.from_bytes(b_last_modified_offset, byteorder='big')
                    # Calculate datetime from seconds offset
                    base_datetime = QDateTime(1999, 12, 31, 23, 59, 59)
                    calculated_datetime = base_datetime.addSecs(last_modified_offset)
                    epoch_last_modified = calculated_datetime.toSecsSinceEpoch()
                    localized_last_modified = QLocale.system().toString(
                        calculated_datetime,
                        QLocale.FormatType.ShortFormat
                    )

                    # Graphic (bnr/icon) address offset
                    # It seems this offset takes place after the info offset,
                    # e.g. if info_offset = 0 and name/info are both 32 bytes, graphic offset will be 64
                    b_graphic_offset = f.read(4)
                    graphic_offset = int.from_bytes(b_graphic_offset, byteorder='big')
                    """
                    Surugi doc glossed over a few fields, so I'll also be referring to the struct names from
                    https://github.com/suloku/gcmm/blob/master/source/gci.h, but no further code.
                    """
                    icon_format = f.read(2)
                    icon_speed = f.read(2)
                    """
                    Extrapolating based on variable names from gcmm's gci.h, I may be incorrect;
                    1 byte = permission (whether or not file can be copied between memory cards)
                    1 byte = number of times copied
                    2 bytes = 'block'; not sure
                    2 bytes = 'length': lines up w/ "Number of blocked(sic) used" in Surugi doc. 8kb block count.
                    2 bytes = 'pad_01': padding (seems to be 'FF FF')
                    """
                    # Skip over the aforementioned fields
                    f.seek(8, 1)

                    # [0x3c] Info (title/description) offset, 4 bytes long, binary
                    b_info_offset = f.read(4)
                    info_offset = int.from_bytes(b_info_offset, byteorder='big')
                    f.seek(info_offset, 1)
                    # Game name (title), 32 bytes, ASCII
                    game_name = f.read(32)
                    # File info (description), 32 bytes, ASCII
                    file_desc = f.read(32)

                    # Banner size + graphic_offset, which appears to be calculated to take place the info_offset
                    first_frame_address = f.tell() + bnr_seek_count + (graphic_offset - 64)

            # File is now closed

            # Strip padding from game_name and file_info byte strings
            game_name = game_name.rstrip(b'\x00')
            file_desc = file_desc.rstrip(b'\x00')

            """
            It was very difficult to find information on memory card encoding,
             but according to https://x.com/Extrems/status/1592569400577904640 ,
            NA/Europe/Australia uses windows-1252 (extended ASCII), and eastern Asia uses Shift JIS.
            TODO: Implement Shift JIS and test w/ Japanese save files
            """
            # Decode name and description byte strings
            title = game_name.decode('cp1252')
            description = file_desc.decode('cp1252')

            # Parse icon, add to icon_provider's internal dict
            icon_provider.parse_icon(file, first_frame_address, icon_format, icon_speed, file_info)

            """
            TODO:
             1) Save files should be sorted if they aren't implicitly
            """
            sf = SaveFile(
                str(file),
                file_info,
                title,
                description,
                epoch_last_modified,
                localized_last_modified
            )
            valid_files.append(sf)

    return valid_files
