import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from gb.translation import (  # noqa: E402
    ORIGINAL_ROM_SHA256,
    TRANSLATED_ROM_SHA256,
    TranslationBuildError,
    build_translated_rom,
    load_patches,
    load_ranges,
    load_references,
)


class TranslationBuildTest(unittest.TestCase):
    @classmethod
    def paths(cls):
        return {
            "encoding_path": ROOT / "translation" / "encoding.tsv",
            "patches_path": ROOT / "translation" / "patches.tsv",
            "references_path": ROOT / "translation" / "references.tsv",
            "ranges_path": ROOT / "translation" / "ranges.tsv",
        }

    def test_public_manifests_are_consistent(self):
        patches = load_patches(self.paths()["patches_path"])
        references = load_references(
            self.paths()["references_path"], {patch.identifier for patch in patches}
        )
        ranges = load_ranges(self.paths()["ranges_path"])
        self.assertEqual(len(patches), 46)
        self.assertEqual(len(references), 48)
        self.assertEqual(len(ranges), 3)

    def test_wrong_rom_is_rejected(self):
        with self.assertRaisesRegex(TranslationBuildError, "unsupported original ROM"):
            build_translated_rom(bytes(0x40000), **self.paths())

    def test_exact_rom_reconstruction_when_original_is_available(self):
        rom_path = ROOT / "rom" / "original.gb"
        if not rom_path.exists():
            self.skipTest("rom/original.gb is not available")
        original = rom_path.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), ORIGINAL_ROM_SHA256)
        result = build_translated_rom(original, **self.paths())
        self.assertEqual(result.sha256, TRANSLATED_ROM_SHA256)
        self.assertEqual(hashlib.sha256(result.data).hexdigest(), TRANSLATED_ROM_SHA256)
        self.assertGreater(len(result.changed_offsets), 0)


if __name__ == "__main__":
    unittest.main()