import tempfile
import unittest
from pathlib import Path

from gbworkbench.errors import WorkstationError
from gbworkbench.project import discover_projects, load_project


class ProjectTest(unittest.TestCase):
    def test_checked_in_project_is_discovered(self):
        projects = discover_projects()
        self.assertEqual([project.identifier for project in projects], ["gb-db-z-gokou"])

    def test_project_paths_are_resolved(self):
        project = load_project("gb-db-z-gokou")
        self.assertEqual(project.root.name, "gb-db-z-gokou")
        self.assertTrue(project.manifests["patches"].is_absolute())
        self.assertEqual(len(project.approved_ranges), 8)

    def test_directory_and_id_must_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "projects" / "directory-name"
            project.mkdir(parents=True)
            (project / "project.toml").write_text(
                """schema_version = 1
id = "different-name"
name = "Fixture"
platform = "game-boy"
adapter = "fixture"
[input]
default_path = "roms/fixture/original.gb"
size = 1
sha256 = "00"
[output]
default_path = "build/fixture/output.gb"
size = 1
sha256 = "00"
""",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(WorkstationError, "does not match directory"):
                load_project(project, root)


if __name__ == "__main__":
    unittest.main()