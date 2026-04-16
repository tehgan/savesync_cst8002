# This Python file uses the following encoding: utf-8
import sys
from dataclasses import dataclass
from pathlib import Path
import re

#from parser_icon import parse_icon

from PySide6.QtCore import QDateTime, QLocale


@dataclass
class SaveFile:
    # Path converted to a string
    file_path: str
    # TODO: Refactor to QImage or similar
    icon: str
    title: str
    description: str
    last_modified: str


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
def parse(raw_directory_path: str):
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

            # TODO: Might be good to optimize this a little, esp. the beginning; reading 4 lil bytes probably has a lot of overhead. Can they be read all at once, then accessed from a bytearray?
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
                    # Seek to 'date last modified' address (0x28) from current position
                    f.seek(32, 1)
                    # Seconds past 12/31/1999 11:59:59 PM
                    b_last_modified_offset = f.read(4)
                    # Convert binary byte string (from read()) to decimal.
                    # GameCube .gci files are big-endian (as the GameCube is PowerPC-based)
                    last_modified_offset = int.from_bytes(b_last_modified_offset, byteorder='big')
                    # Calculate datetime from seconds offset
                    base_datetime = QDateTime(1999, 12, 31, 23, 59, 59)
                    calculated_datetime = base_datetime.addSecs(last_modified_offset)
                    last_modified = QLocale.system().toString(calculated_datetime, QLocale.FormatType.ShortFormat)

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
                    file_info = f.read(32)


                    # TODO: Refactor; get offset, close file, pass offset + f.tell (position of first frame) to image parser
                    #  Also decode name/info and append out of file
                    # 01-GAFE-DobutsunomoriP_F_SAVE - NES Save data; no banner, static icon, x00
                    # 01-GAFE-DobutsunomoriP_MURA - Town data; banner, static icon, x01
                    # 51-GWME-Worms3DSave - Worms 3D; no banner, animated icon (4 frames), x00
                    # AF-GNME-NAMCOMUSEUM - Namco Museum; banner, animated icon (2 frames), x01

                    # Banner size + graphic_offset, which appears to be calculated to take place the info_offset
                    seek_count = (graphic_offset - 64) + bnr_seek_count
                    print("Estimated seek:", (f.tell() + seek_count))
                    f.seek(seek_count, 1)
                    print("Current position after seek:", f.tell())

                    #######################
                    # ICON FORMAT / SPEED #
                    #######################
                    frame_info: list[FrameInfo] = list()
                    frame_position = f.tell()
                    uses_shared_palette = False

                    # None = 00, CI8_SHARED = 01 (1024b img + 512b palette at end of frame data),
                    # RGB5A3 = 10 (2048b img), CI8_UNIQUE = 11 (1024b img + 512b palette directly afterward)
                    icon_format_slices = get_icon_slices(icon_format)
                    for fs in icon_format_slices:
                        match fs:
                            case '00':
                                break
                            case '01':
                                frame_info.append(FrameInfo(frame_position, '01', ''))
                                frame_position += 1024
                                uses_shared_palette = True
                            case '10':
                                frame_info.append(FrameInfo(frame_position, '10', ''))
                                frame_position += 2048
                            case '11':
                                frame_info.append(FrameInfo(frame_position, '11', ''))
                                frame_position += 1536

                    # NO_ICON = 00, 4_FRAMES = 01, 8_FRAMES = 10, 12_FRAMES = 11
                    icon_speed_slices = get_icon_slices(icon_speed)
                    for i, ss in enumerate(icon_speed_slices):
                        if i >= len(frame_info) or ss == '00':
                            break
                        elif ss in ('01', '10', '11'):
                            frame_info[i].ic_speed = ss

                    # TODO: Parse static CI8 ('00 01' format) and animated CI8 ('00 05'?)
                    #icon = parse_icon(frame_info)


                    #######################
                    # NAME & INFO PARSING #
                    #######################
                    # Strip padding from game_name and file_info byte strings
                    game_name = game_name.rstrip(b'\x00')
                    file_info = file_info.rstrip(b'\x00')

                    """
                    It was very difficult to find information on memory card encoding,
                     but according to https://x.com/Extrems/status/1592569400577904640 ,
                    NA/Europe/Australia uses windows-1252 (extended ASCII), and eastern Asia uses Shift JIS.
                    TODO: Implement Shift JIS and test w/ Japanese save files
                    """
                    title = game_name.decode('cp1252')
                    description = file_info.decode('cp1252')

                    """
                    TODO:
                     1) Save files should be sorted if they aren't implicitly
                     2) Returned icon URL is always blank as I don't have image parsing ready yet
                    """
                    sf = SaveFile(str(file), '', title, description, last_modified)
                    valid_files.append(sf)
            # File is now closed, but still in loop (so valid can still be checked)

    return valid_files
