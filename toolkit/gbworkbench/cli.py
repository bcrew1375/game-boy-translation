"""Command-line interface for the multi-project translation workstation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .errors import WorkstationError
from .project import build_project, discover_projects, load_adapter, load_project, repository_root


def _project_summary(project) -> dict[str, object]:
    return {
        "id": project.identifier,
        "name": project.name,
        "platform": project.platform,
        "input": {
            "default_path": str(project.input.default_path),
            "size": project.input.size,
            "sha256": project.input.sha256,
        },
        "output": {
            "default_path": str(project.output.default_path),
            "size": project.output.size,
            "sha256": project.output.sha256,
        },
        "manifests": {name: str(path) for name, path in project.manifests.items()},
        "approved_ranges": [
            {"name": region.name, "start": region.start, "end": region.end}
            for region in project.approved_ranges
        ],
    }


def _validate_project(project) -> None:
    missing = [path for path in project.manifests.values() if not path.is_file()]
    if missing:
        raise WorkstationError(
            "missing project manifests: " + ", ".join(str(path) for path in missing)
        )
    adapter = load_adapter(project)
    validator = getattr(adapter, "validate", None)
    if validator is not None:
        validator(project)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gb-workstation", description="Build and validate Game Boy translation projects."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list checked-in translation projects")

    info = commands.add_parser("info", help="show resolved project metadata")
    info.add_argument("project")

    validate = commands.add_parser("validate", help="validate a project without requiring a ROM")
    validate.add_argument("project")

    build = commands.add_parser("build", help="build a translated ROM")
    build.add_argument("project")
    build.add_argument("--rom", type=Path)
    build.add_argument("-o", "--output", type=Path)

    test = commands.add_parser("test", help="run one project's unit tests")
    test.add_argument("project")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            for project in discover_projects():
                print(f"{project.identifier}\t{project.name}")
            return 0

        project = load_project(args.project)
        if args.command == "info":
            print(json.dumps(_project_summary(project), indent=2))
            return 0
        if args.command == "validate":
            _validate_project(project)
            print(f"Project {project.identifier} is valid.")
            return 0
        if args.command == "build":
            result = build_project(project, rom_path=args.rom, output_path=args.output)
            output = (args.output or project.output.default_path).resolve()
            print(f"Wrote {output} ({len(result.data)} bytes).")
            print(f"Changed {len(result.changed_offsets)} bytes in approved ranges.")
            print(f"SHA-256: {result.sha256}")
            return 0
        if args.command == "test":
            _validate_project(project)
            environment = {**os.environ, "PYTHONPATH": str(repository_root() / "toolkit")}
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    str(project.root / "tests"),
                    "-v",
                ],
                cwd=repository_root(),
                env=environment,
                check=False,
            )
            return completed.returncode
    except (OSError, WorkstationError, ValueError) as error:
        parser.error(str(error))
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())