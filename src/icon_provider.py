# This Python file uses the following encoding: utf-8
# Parses CI8 icon files (32x32)
#  I haven't been able to implement RGB5A3 support due to lack of time to debug.
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from PySide6.QtGui import QImage


class IconProvider:
    @dataclass
    class FrameInfo:
        ic_position: int
        ic_format: str
        ic_speed: str

    class ARGB(NamedTuple):
        alpha: int
        red: int
        green: int
        blue: int

    def __init__(self):
        # Instantiate placeholder icon, for those that cannot be parsed
        self._icon_placeholder = QImage("../res/placeholder_32.png")

        # Initialize dictionary of icons ('Game ID' key, 'icon' value)
        self._icon_list = {}

    def get_icon(self, file_info: str) -> QImage | None:
        val = None
        try:
            val = self._icon_list[file_info]
        except KeyError:
            print(f"Icon for ID {file_info} not found.")
        return val

    def colour_to_argb(self, colour: int):
        """:param int colour: Colour byte. Must have been merged/unpacked from 2 bytes to 1, and converted to an int."""

        # Bitwise operation was tricky to figure out but https://bitwisecmd.com/
        #  provided a 'playground'/calculator which helped a lot.

        # Accurate bit-conversion formulae from https://threadlocalmutex.com/?page_id=60
        alpha_check = ((colour >> 15) & 1)
        if alpha_check == 0:
            # RGB4A3 (3 alpha bits, 4 R/G/B bits, not documented by Surugi :/)
            alpha = ((colour >> 12) & 7)
            red = ((colour >> 8) & 15)
            green = ((colour >> 4) & 15)
            blue = (colour & 15)
            return self.ARGB(
                (alpha * 146 + 1) >> 2,
                red * 17,
                green * 17,
                blue * 17
            )
        else:
            # RGB5A3 (0 alpha bits despite the name (apart from determinator), 5 R/G/B bits)
            red = ((colour >> 10) & 31)
            green = ((colour >> 5) & 31)
            blue = (colour & 31)
            return self.ARGB(
                255,
                (red * 527 + 23) >> 6,
                (green * 527 + 23) >> 6,
                (blue * 527 + 23) >> 6,
            )

    def palette_to_argb(self, palette: bytes):
        # Palettes contain 2 bytes per colour, merge bytes into 1 and store as unsigned short
        unpacked_palette = struct.unpack('>256H', palette)

        argb_palette: list[IconProvider.ARGB] = list()
        for colour in unpacked_palette:
            converted_colour = self.colour_to_argb(colour)
            argb_palette.append(converted_colour)

        return argb_palette

    def ci8_to_argb(self, cta_raw: bytes, cta_palette_raw: bytes) -> QImage:
        flattened_icon = bytearray(32*32*4)
        palette = self.palette_to_argb(cta_palette_raw)

        row_multiplier = -1
        for tile in range(32):
            # For calculating the current byte. 32 tiles (0..31), 32 bytes per tile.
            tile_offset = (32 * tile)

            # Also functions as a col_multiplier
            mod = tile % 4
            if mod == 0:
                row_multiplier += 1

            for row in range(4):
                real_row = (row + (4 * row_multiplier))
                for col in range(8):
                    real_col = (col + (8 * mod))

                    # Icon (cta_raw)'s current byte
                    ic_idx = (tile_offset + col + (row * 8))
                    palette_idx = cta_raw[ic_idx]
                    colour = palette[palette_idx]

                    # Flattened icon (bytearray)'s current byte
                    ba_idx = (real_row * 32 + real_col) * 4
                    flattened_icon[ba_idx] = colour.red
                    flattened_icon[ba_idx + 1] = colour.green
                    flattened_icon[ba_idx + 2] = colour.blue
                    flattened_icon[ba_idx + 3] = colour.alpha

        # TODO: Ensure image's bytearray cannot be garbage collected
        return QImage(flattened_icon, 32, 32, QImage.Format.Format_RGBA8888)

    # Get slices of icon's format or speed bytes (2 bytes, 2 bits/frame, 8 frames max)
    def get_icon_slices(self, ic_fmt: bytes):
        gis_int = int.from_bytes(ic_fmt, byteorder='big')
        gis_bin = format(gis_int, f'016b')
        # Frames are ordered last (7) to first (0) by-default, reverse for easier parsing
        return reversed(re.findall('..', gis_bin))

    def parse_icon(self, file: Path, first_frame_address: int, icon_format: bytes, icon_speed: bytes, file_info: str):
        ###############
        # STATIC ICON #
        ###############
        # Static CI8
        if icon_format == b'\x00\x01':
            print(f"{file}: Returning static CI8 as QImage")
            with open(file, 'rb') as f:
                f.seek(first_frame_address)
                icon_raw = f.read(1024)
                icon_palette = f.read(512)
            icon = self.ci8_to_argb(icon_raw, icon_palette)
            self._icon_list[file_info] = icon
            return

        # RGB5A3 (unsupported; couldn't get output working, Surugi doc's tile description may be inaccurate.
        if icon_format in (b'\x00\x02', b'\x00\x06'):
            print(f"{file}: Icon is RGB5A3, currently unsupported.")
            return

        #################
        # ANIMATED ICON #
        #################
        # TODO: I wrote a separate parser that functions standalone
        #  and outputs all frames as PAM (Portable Arbitrary Map) files,
        #   but animation is unimplemented as getting that working in Qt seems fairly complex.
        # No animated bit info from the Surugi doc, so unfortunately I had to refer to code,
        #  specifically the Enum classes used here: https://github.com/sopoforic/cgrr-gamecube/blob/master/gci.py
        frame_info: list[IconProvider.FrameInfo] = list()
        frame_position = first_frame_address
        uses_shared_palette = False

        # None = 00, CI8_SHARED = 01 (1024b img + 512b palette at end of frame data),
        # RGB5A3 = 10 (2048b img), CI8_UNIQUE = 11 (1024b img + 512b palette directly afterward)
        icon_format_slices = self.get_icon_slices(icon_format)
        for fs in icon_format_slices:
            match fs:
                case '00':
                    break
                case '01':
                    frame_info.append(IconProvider.FrameInfo(frame_position, '01', ''))
                    frame_position += 1024
                    uses_shared_palette = True
                case '10':
                    frame_info.append(IconProvider.FrameInfo(frame_position, '10', ''))
                    frame_position += 2048
                case '11':
                    frame_info.append(IconProvider.FrameInfo(frame_position, '11', ''))
                    frame_position += 1536

        # NO_ICON = 00, 4_FRAMES = 01, 8_FRAMES = 10, 12_FRAMES = 11
        icon_speed_slices = self.get_icon_slices(icon_speed)
        for i, ss in enumerate(icon_speed_slices):
            if i >= len(frame_info) or ss == '00':
                break
            elif ss in ('01', '10', '11'):
                frame_info[i].ic_speed = ss

        # Set placeholder if icon wasn't parsed
        try:
            foo = self._icon_list[file_info]
        except KeyError:
            self._icon_list[file_info] = self._icon_placeholder

        return

