"""Deterministic English artwork for the fixed title and menu tile strips."""

from __future__ import annotations

from gb.font import GLYPH_ROWS
from PIL import Image

from gb.graphics import decode_tiles, encode_tiles


TITLE_WIDTH = 80
TITLE_HEIGHT = 16
TITLE_TILE_COUNT = 20
TITLE_DECOMPRESSED_SIZE = TITLE_TILE_COUNT * 16
TITLE_COMPRESSED_SLOT_SIZE = 0x129

MENU_DECOMPRESSED_SIZE = 46 * 16
MENU_COMPRESSED_SLOT_SIZE = 0x284

TITLE_LINES = ("GOKU'S", "SOARING LEGEND")
MENU_LABELS = (
    "STORY",
    "WORLD TOURNAMENT",
    "VERSUS",
    "TRAINING",
)
MENU_WIDTHS = (32, 88, 32, 32)
MENU_FILL_INDEX = 1
MENU_OUTLINE_INDEX = 3


SMALL_GLYPHS = {
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("1", "1", "1", "1", "1"),
    "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("1001", "1101", "1101", "1011", "1001"),
    "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "111", "011"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
}


def _new_canvas(width: int, height: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _trim_glyph(rows: tuple[str, ...]) -> tuple[str, ...]:
    occupied = [x for x in range(len(rows[0])) if any(row[x] == "1" for row in rows)]
    if not occupied:
        return rows
    return tuple(row[occupied[0] : occupied[-1] + 1] for row in rows)


def _measure(text: str, glyphs: dict[str, tuple[str, ...]], spacing: int, space: int) -> int:
    width = 0
    for character in text:
        width += space if character == " " else len(_trim_glyph(glyphs[character])[0])
        width += spacing
    return max(0, width - spacing)


def _draw_text(
    canvas: list[list[int]],
    text: str,
    glyphs: dict[str, tuple[str, ...]],
    y: int,
    *,
    spacing: int = 1,
    space: int = 3,
    scale_y: int = 1,
    x: int | None = None,
    effect: str = "shadow",
    effect_bounds: tuple[int, int, int, int] | None = None,
) -> None:
    if effect not in ("shadow", "outline"):
        raise ValueError(f"unsupported text effect: {effect}")
    text_width = _measure(text, glyphs, spacing, space)
    if x is None:
        x = (len(canvas[0]) - text_width) // 2
    if x < 0 or x + text_width > len(canvas[0]):
        raise ValueError(f"{text!r} is {text_width} pixels wide for {len(canvas[0])}-pixel canvas")
    foreground = set()
    for character in text:
        if character == " ":
            x += space + spacing
            continue
        rows = _trim_glyph(glyphs[character])
        for row_index, row in enumerate(rows):
            for column, bit in enumerate(row):
                if bit != "1":
                    continue
                for dy in range(scale_y):
                    py = y + row_index * scale_y + dy
                    px = x + column
                    if effect == "shadow":
                        if py + 1 < len(canvas) and px + 1 < len(canvas[0]):
                            canvas[py + 1][px + 1] = max(canvas[py + 1][px + 1], 1)
                        canvas[py][px] = 3
                    else:
                        foreground.add((px, py))
        x += len(rows[0]) + spacing

    if effect == "outline":
        min_x, min_y, max_x, max_y = effect_bounds or (
            0,
            0,
            len(canvas[0]) - 1,
            len(canvas) - 1,
        )
        for px, py in foreground:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    outline_x = px + dx
                    outline_y = py + dy
                    if min_x <= outline_x <= max_x and min_y <= outline_y <= max_y:
                        canvas[outline_y][outline_x] = MENU_OUTLINE_INDEX
        for px, py in foreground:
            canvas[py][px] = MENU_FILL_INDEX


def _canvas_tiles(canvas: list[list[int]]) -> list[list[list[int]]]:
    height = len(canvas)
    width = len(canvas[0])
    if width % 8 or height % 8:
        raise ValueError("canvas dimensions must be multiples of 8")
    return [
        [row[x : x + 8] for row in canvas[y : y + 8]]
        for y in range(0, height, 8)
        for x in range(0, width, 8)
    ]


def _tiles_canvas(tiles, width: int, height: int) -> list[list[int]]:
    columns = width // 8
    rows = height // 8
    if len(tiles) != columns * rows:
        raise ValueError("tile count does not match the requested canvas")
    canvas = _new_canvas(width, height)
    for index, tile in enumerate(tiles):
        x = (index % columns) * 8
        y = (index // columns) * 8
        for row_index, row in enumerate(tile):
            canvas[y + row_index][x : x + 8] = row
    return canvas


def _canvas_image(canvas: list[list[int]], scale: int = 4) -> Image.Image:
    palette = (255, 170, 85, 0)
    image = Image.new("L", (len(canvas[0]), len(canvas)), 255)
    pixels = image.load()
    for y, row in enumerate(canvas):
        for x, value in enumerate(row):
            pixels[x, y] = palette[value]
    if scale != 1:
        image = image.resize(
            (image.width * scale, image.height * scale), Image.Resampling.NEAREST
        )
    return image


def build_title_tiles() -> bytes:
    """Build the 10x2 tile strip for tile IDs $E0-$F3."""
    canvas = _new_canvas(TITLE_WIDTH, TITLE_HEIGHT)
    _draw_text(canvas, TITLE_LINES[0], GLYPH_ROWS, 0)
    _draw_text(canvas, TITLE_LINES[1], GLYPH_ROWS, 8, spacing=0)
    result = encode_tiles(_canvas_tiles(canvas), bpp=2)
    if len(result) != TITLE_DECOMPRESSED_SIZE:
        raise AssertionError("title tile output has the wrong size")
    return result


def build_menu_tiles() -> bytes:
    """Build the four row-major menu rectangles for tile IDs $A0-$CD."""
    output = bytearray()
    for width, label in zip(MENU_WIDTHS, MENU_LABELS):
        canvas = _new_canvas(width, 16)
        _draw_text(
            canvas,
            label,
            SMALL_GLYPHS,
            3,
            scale_y=2,
            x=1,
            effect="outline",
            effect_bounds=(0, 2, width - 1, 12),
        )
        output.extend(encode_tiles(_canvas_tiles(canvas), bpp=2))
    if len(output) != MENU_DECOMPRESSED_SIZE:
        raise AssertionError("menu tile output has the wrong size")
    return bytes(output)


def render_title_preview(data: bytes, scale: int = 4) -> Image.Image:
    """Reconstruct the title's 10x2 rectangle from row-major tile data."""
    if len(data) != TITLE_DECOMPRESSED_SIZE:
        raise ValueError("title data has the wrong size")
    return _canvas_image(_tiles_canvas(decode_tiles(data), 80, 16), scale)


def render_menu_preview(data: bytes, scale: int = 4) -> Image.Image:
    """Reconstruct all four differently sized menu rectangles in display order."""
    if len(data) != MENU_DECOMPRESSED_SIZE:
        raise ValueError("menu data has the wrong size")
    output = _new_canvas(max(MENU_WIDTHS), 70)
    tiles = decode_tiles(data)
    tile_cursor = 0
    y = 0
    for width in MENU_WIDTHS:
        count = width // 8 * 2
        label = _tiles_canvas(tiles[tile_cursor : tile_cursor + count], width, 16)
        for row_index, row in enumerate(label):
            output[y + row_index][:width] = row
        tile_cursor += count
        y += 18
    return _canvas_image(output, scale)