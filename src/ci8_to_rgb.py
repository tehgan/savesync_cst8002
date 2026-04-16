# This Python file uses the following encoding: utf-8
# Converts the GameCube's CI8 image format (256-colour palette, 32 levels of gradation) to RGB (24-bit / true colour)

def ci8_to_rgb(img: bytes, palette: bytes):
    """
    BANNER/GRAPHIC:
    3072 bytes (if 96x32 banner)
    8x4 tiles; 8 columns, 4 rows
    Start reading in top-left corner. First 8 columns, move down a row, next 8 columns, so on.
     After tile is read, move onto next 8 columns.

    Each pixel is a byte, referring to the NUMBER/INDEX (not address or offset) of a palette colour
    'x00' = first colour, which in Namco Museum's case, is black (00 00)
    'x99' = 153rd colour. Since each colour is 2 bytes, multiply by 2 (x132 or 306d) to get address
        NOTE: address based on extracted palette hex, actual address will be offset significantly
    """

    """
    PALETTE:
    512 bytes
    2 bytes per colour, so 256 colours total
    32 levels of gradation; ranges from 0 to 31
        Can be converted to RGB (24-bit colour, aka 'True Colour') by multiplying by 8
    
    Example:
    Colour at 0x132 is "D8 A9"
        Convert all hex to binary:
            D = 1101
            8 = 1000
            A = 1010
            9 = 1001
        Join binary together:
            1101100010101001
        Bit 1: Surugi claims this is transparency, but it seems to be ignored in CI8
        Bit 2-6: Red (10110) = 22d, (22 * 8) = 176d
        Bit 7-11: Green (00101) = 6d, (6 * 8) = 48d
        Bit 12-16: Blue (01001) = 9d, (9 * 8) = 72d
    """

    """
    Icon format, icon speed
    NAMCO MUSEUM: 00 05, 00 0F [Animated, 2 frames]
    ANIMAL XING (main): 00 01, 00 03 [Static]
    ANIMAL XING (nes): 00 01, 00 02 [Static]
    WORMS 3D: 00 AA, 00 AA [Animated, 4 frames]
        Interesting note about this one; I'd expect 0,1,2,3 then back to 0, but GCN seems to oscillate (0,1,2,3,2,1,0)
        Not sure if this is a flag that's set or if every animated icon has this behavior
    """