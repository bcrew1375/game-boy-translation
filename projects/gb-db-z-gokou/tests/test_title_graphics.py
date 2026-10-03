import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / "toolkit"))
sys.path.insert(0, str(PROJECT / "src"))

from gbworkbench.graphics import decode_tiles, encode_tiles  # noqa: E402
from gb_db_z_gokou.compression import compress_resource, decompress_resource  # noqa: E402
from gb_db_z_gokou.title_graphics import (  # noqa: E402
    MENU_COMPRESSED_SLOT_SIZE,
    MENU_DECOMPRESSED_SIZE,
    MENU_FILL_INDEX,
    MENU_LABELS,
    MENU_OUTLINE_INDEX,
    MENU_WIDTHS,
    SMALL_GLYPHS,
    TITLE_COMPRESSED_SLOT_SIZE,
    TITLE_DECOMPRESSED_SIZE,
    build_menu_tiles,
    build_title_tiles,
    render_menu_preview,
    render_title_preview,
)


class TitleGraphicsTest(unittest.TestCase):
    @staticmethod
    def _menu_canvases():
        tiles = decode_tiles(build_menu_tiles())
        tile_cursor = 0
        canvases = []
        for width in MENU_WIDTHS:
            columns = width // 8
            label_tiles = tiles[tile_cursor : tile_cursor + columns * 2]
            canvas = [[0 for _ in range(width)] for _ in range(16)]
            for index, tile in enumerate(label_tiles):
                x = index % columns * 8
                y = index // columns * 8
                for row_index, row in enumerate(tile):
                    canvas[y + row_index][x : x + 8] = row
            canvases.append(canvas)
            tile_cursor += columns * 2
        return canvases

    def test_graphics_fit_fixed_resources_and_round_trip(self):
        for raw, expected_size, slot_size in (
            (build_menu_tiles(), MENU_DECOMPRESSED_SIZE, MENU_COMPRESSED_SLOT_SIZE),
            (build_title_tiles(), TITLE_DECOMPRESSED_SIZE, TITLE_COMPRESSED_SLOT_SIZE),
        ):
            self.assertEqual(len(raw), expected_size)
            compressed = compress_resource(raw)
            self.assertLessEqual(len(compressed), slot_size)
            self.assertEqual(decompress_resource(compressed).data, raw)

    def test_tile_encoding_round_trip(self):
        for raw in (build_menu_tiles(), build_title_tiles()):
            self.assertEqual(encode_tiles(decode_tiles(raw), bpp=2), raw)

    def test_output_is_deterministic(self):
        self.assertEqual(build_menu_tiles(), build_menu_tiles())
        self.assertEqual(build_title_tiles(), build_title_tiles())

    def test_preview_dimensions(self):
        self.assertEqual(render_menu_preview(build_menu_tiles(), scale=1).size, (88, 70))
        self.assertEqual(render_title_preview(build_title_tiles(), scale=1).size, (80, 16))

    def test_menu_labels_share_left_edge_height_and_baseline(self):
        bounds = []
        for canvas in self._menu_canvases():
            occupied = [
                (x, y)
                for y, row in enumerate(canvas)
                for x, pixel in enumerate(row)
                if pixel
            ]
            bounds.append(
                (
                    min(x for x, _ in occupied),
                    min(y for _, y in occupied),
                    max(y for _, y in occupied),
                )
            )
        self.assertEqual(bounds, [(0, 2, 12)] * 4)

    def test_menu_n_has_a_distinct_diagonal(self):
        self.assertEqual(SMALL_GLYPHS["N"], ("1001", "1101", "1101", "1011", "1001"))
        self.assertNotEqual(SMALL_GLYPHS["N"], SMALL_GLYPHS["H"])

    def test_training_has_complete_right_outline(self):
        training_index = MENU_LABELS.index("TRAINING")
        canvas = self._menu_canvases()[training_index]
        self.assertTrue(any(row[-2] == MENU_OUTLINE_INDEX for row in canvas))
        self.assertTrue(all(row[-1] == 0 for row in canvas))

    def test_menu_uses_original_fill_and_outline_palette_indices(self):
        pixels = [
            pixel
            for tile in decode_tiles(build_menu_tiles())
            for row in tile
            for pixel in row
        ]
        self.assertEqual(set(pixels), {0, MENU_FILL_INDEX, MENU_OUTLINE_INDEX})
        self.assertEqual(MENU_FILL_INDEX, 1)
        self.assertEqual(MENU_OUTLINE_INDEX, 3)

    def test_every_menu_outline_pixel_touches_its_gray_fill(self):
        for canvas in self._menu_canvases():
            width = len(canvas[0])
            for y, row in enumerate(canvas):
                for x, pixel in enumerate(row):
                    if pixel != MENU_OUTLINE_INDEX:
                        continue
                    neighbors = (
                        canvas[neighbor_y][neighbor_x]
                        for neighbor_y in range(max(0, y - 1), min(16, y + 2))
                        for neighbor_x in range(max(0, x - 1), min(width, x + 2))
                    )
                    self.assertIn(MENU_FILL_INDEX, neighbors)


if __name__ == "__main__":
    unittest.main()