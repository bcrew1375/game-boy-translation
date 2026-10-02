import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from gb.text import (  # noqa: E402
    AllocationRange,
    TextEncodeError,
    allocate_translated_streams,
    encode_translated_text,
    load_character_encoding,
)


class TranslatedTextEncodingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encoding = load_character_encoding(ROOT / "translation" / "encoding.tsv")

    def test_controls_and_terminator(self):
        encoded = encode_translated_text("A\\nB<WAIT>!", self.encoding)
        self.assertEqual(encoded, bytes([0x01, 0xFD, 0x02, 0xFB, 0x3A, 0xFE]))

    def test_unsupported_character_is_rejected(self):
        with self.assertRaises(TextEncodeError):
            encode_translated_text("Gokū", self.encoding)

    def test_line_overflow_is_rejected(self):
        with self.assertRaises(TextEncodeError):
            encode_translated_text("1234567890123456789", self.encoding)

    def test_literal_backslash_n_is_the_only_line_control(self):
        with self.assertRaises(TextEncodeError):
            encode_translated_text("A\nB", self.encoding)

    def test_allocator_moves_whole_stream_to_next_range(self):
        addresses = allocate_translated_streams(
            [("a", b"1234"), ("b", b"567")],
            [AllocationRange(0x4000, 0x4004), AllocationRange(0x5000, 0x5002)],
        )
        self.assertEqual(addresses, {"a": 0x4000, "b": 0x5000})

    def test_overlapping_allocation_ranges_are_rejected(self):
        with self.assertRaises(TextEncodeError):
            allocate_translated_streams(
                [("a", b"1")],
                [AllocationRange(0x4000, 0x4010), AllocationRange(0x4010, 0x4020)],
            )

    def test_allocation_exhaustion_is_rejected(self):
        with self.assertRaises(TextEncodeError):
            allocate_translated_streams(
                [("a", b"123")], [AllocationRange(0x4000, 0x4001)]
            )

    def test_fixed_width_yes_no_labels_match_canonical_tile_ids(self):
        self.assertEqual(
            bytes(self.encoding[character] for character in "YES"),
            bytes([0x19, 0x05, 0x13]),
        )
        self.assertEqual(
            bytes(self.encoding[character] for character in "NO "),
            bytes([0x0E, 0x0F, 0x00]),
        )


if __name__ == "__main__":
    unittest.main()