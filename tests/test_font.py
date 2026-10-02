import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from gb.font import (  # noqa: E402
    FONT_COMPRESSED_SLOT_SIZE,
    FONT_DECOMPRESSED_SIZE,
    FONT_ROM_OFFSET,
    ENGLISH_TILE_CHARACTERS,
    FontCodecError,
    build_english_font,
    compress_font,
    decompress_font,
)


class FontCodecTest(unittest.TestCase):
    def test_round_trip_with_literals_and_overlapping_backreferences(self):
        raw = (b"ABABABAB" * 40) + bytes(range(64)) + (b"\x00" * 300)
        compressed = compress_font(raw)
        decoded = decompress_font(compressed)
        self.assertEqual(decoded.data, raw)
        self.assertEqual(decoded.bytes_consumed, len(compressed))

    def test_invalid_backreference_is_rejected(self):
        data = b"\x01\x00" + (b"\x01" + b"\x00" * 31) + b"\x01\x00"
        with self.assertRaises(FontCodecError):
            decompress_font(data)

    def test_original_and_english_fonts(self):
        rom_path = ROOT / "rom" / "original.gb"
        if not rom_path.exists():
            self.skipTest("rom/original.gb is not available")
        rom = rom_path.read_bytes()
        original = decompress_font(
            rom[FONT_ROM_OFFSET : FONT_ROM_OFFSET + FONT_COMPRESSED_SLOT_SIZE]
        )
        self.assertEqual(len(original.data), FONT_DECOMPRESSED_SIZE)
        self.assertEqual(original.bytes_consumed, FONT_COMPRESSED_SLOT_SIZE)

        english = build_english_font(original.data)
        compressed = compress_font(english)
        self.assertLessEqual(len(compressed), FONT_COMPRESSED_SLOT_SIZE)
        self.assertEqual(decompress_font(compressed).data, english)
        self.assertEqual(english[0x80 * 8 :], original.data[0x80 * 8 :])

    def test_canonical_translation_characters_are_unique(self):
        canonical = [
            character
            for tile_id, character in ENGLISH_TILE_CHARACTERS.items()
            if not 0x96 <= tile_id <= 0x9D
        ]
        self.assertEqual(len(canonical), 85)
        duplicates = [
            character
            for character, count in Counter(canonical).items()
            if count > 1
        ]
        self.assertEqual(duplicates, [])


if __name__ == "__main__":
    unittest.main()