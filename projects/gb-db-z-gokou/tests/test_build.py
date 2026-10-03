import hashlib
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / "toolkit"))
sys.path.insert(0, str(PROJECT / "src"))

from gbworkbench.errors import WorkstationError  # noqa: E402
from gbworkbench.project import build_project, load_project  # noqa: E402
from gb_db_z_gokou.build import load_patches, load_ranges, load_references  # noqa: E402


class TranslationBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = load_project(PROJECT)

    def test_public_manifests_are_consistent(self):
        patches = load_patches(self.project.manifests["patches"])
        references = load_references(
            self.project.manifests["references"],
            {patch.identifier for patch in patches},
        )
        ranges = load_ranges(self.project.manifests["ranges"])
        self.assertEqual(len(patches), 46)
        self.assertEqual(len(references), 48)
        self.assertEqual(len(ranges), 3)

    def test_wrong_rom_is_rejected(self):
        wrong = REPOSITORY / "build" / "gb-db-z-gokou" / "wrong.gb"
        wrong.parent.mkdir(parents=True, exist_ok=True)
        wrong.write_bytes(bytes(self.project.input.size))
        self.addCleanup(wrong.unlink, missing_ok=True)
        with self.assertRaisesRegex(WorkstationError, "unsupported original ROM"):
            build_project(self.project, rom_path=wrong, write_output=False)

    def test_exact_rom_reconstruction_when_original_is_available(self):
        rom_path = self.project.input.default_path
        if not rom_path.exists():
            self.skipTest("roms/gb-db-z-gokou/original.gb is not available")
        original = rom_path.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), self.project.input.sha256)
        result = build_project(self.project, write_output=False)
        self.assertEqual(result.sha256, self.project.output.sha256)
        self.assertEqual(hashlib.sha256(result.data).hexdigest(), self.project.output.sha256)
        self.assertEqual(len(result.changed_offsets), 3572)


if __name__ == "__main__":
    unittest.main()