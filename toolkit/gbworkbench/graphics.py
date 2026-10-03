from __future__ import annotations
from pathlib import Path
from PIL import Image

def decode_tiles(data: bytes, bpp: int = 2):
    if bpp not in (1, 2):
        raise ValueError("bpp must be 1 or 2")
    stride = 8 if bpp == 1 else 16
    tiles = []
    for off in range(0, len(data) - (stride - 1), stride):
        px = []
        chunk = data[off:off+stride]
        for y in range(8):
            if bpp == 1:
                lo = chunk[y]
                row = [((lo >> (7-x)) & 1) for x in range(8)]
            else:
                lo, hi = chunk[y*2], chunk[y*2+1]
                row = [(((hi >> (7-x)) & 1) << 1) | ((lo >> (7-x)) & 1) for x in range(8)]
            px.append(row)
        tiles.append(px)
    return tiles


def encode_tiles(tiles, bpp: int = 2) -> bytes:
    """Encode a sequence of 8x8 palette-index arrays as Game Boy tile data."""
    if bpp not in (1, 2):
        raise ValueError("bpp must be 1 or 2")
    maximum = (1 << bpp) - 1
    output = bytearray()
    for tile in tiles:
        if len(tile) != 8 or any(len(row) != 8 for row in tile):
            raise ValueError("each tile must contain exactly 8 rows of 8 pixels")
        for row in tile:
            if any(pixel < 0 or pixel > maximum for pixel in row):
                raise ValueError(f"pixel values must be in the range 0..{maximum}")
            low = sum((pixel & 1) << (7 - x) for x, pixel in enumerate(row))
            output.append(low)
            if bpp == 2:
                high = sum(((pixel >> 1) & 1) << (7 - x) for x, pixel in enumerate(row))
                output.append(high)
    return bytes(output)

def render_tiles(tiles, columns=16, scale=2, gap=1):
    if not tiles:
        raise ValueError("no complete tiles in requested range")
    rows = (len(tiles)+columns-1)//columns
    w = columns*8 + (columns-1)*gap
    h = rows*8 + (rows-1)*gap
    img = Image.new("L", (w,h), 255)
    palette = [255,170,85,0]
    p = img.load()
    for i,tile in enumerate(tiles):
        tx=(i%columns)*(8+gap); ty=(i//columns)*(8+gap)
        for y,row in enumerate(tile):
            for x,v in enumerate(row):
                p[tx+x,ty+y]=palette[v]
    if scale != 1:
        img=img.resize((w*scale,h*scale), Image.Resampling.NEAREST)
    return img

def save_tiles(data: bytes, output: Path, bpp=2, columns=16, scale=2, gap=1):
    tiles=decode_tiles(data,bpp)
    output.parent.mkdir(parents=True,exist_ok=True)
    render_tiles(tiles,columns,scale,gap).save(output)
    return len(tiles)
