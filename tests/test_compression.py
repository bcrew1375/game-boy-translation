import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from gb.compression import (  # noqa: E402
    ResourceCodecError,
    compress_resource,
    decompress_resource,
)


class ResourceCodecTest(unittest.TestCase):
    def test_round_trip_with_literals_and_overlapping_backreferences(self):
        raw = (b"ABABABAB" * 40) + bytes(range(64)) + (b"\x00" * 300)
        compressed = compress_resource(raw)
        decoded = decompress_resource(compressed)
        self.assertEqual(decoded.data, raw)
        self.assertEqual(decoded.bytes_consumed, len(compressed))

    def test_invalid_backreference_is_rejected(self):
        data = b"\x01\x00" + (b"\x01" + b"\x00" * 31) + b"\x01\x00"
        with self.assertRaises(ResourceCodecError):
            decompress_resource(data)


if __name__ == "__main__":
    unittest.main()