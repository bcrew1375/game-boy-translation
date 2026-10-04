import json
import tempfile
import unittest
from pathlib import Path

from gbworkbench.analysis import (
    UNKNOWN_TYPE,
    calculate_coverage,
    load_analysis_manifest,
    render_svg,
    report_document,
)
from gbworkbench.errors import WorkstationError


def fixture(regions, size=0x8000):
    return {
        "schema_version": 1,
        "rom": {"size_bytes": size, "rom_banks": size // 0x4000},
        "regions": regions,
    }


def region(bank, cpu_start, cpu_end, region_type, name):
    rom_start = cpu_start if bank == 0 else bank * 0x4000 + cpu_start - 0x4000
    rom_end = cpu_end if bank == 0 else bank * 0x4000 + cpu_end - 0x4000
    return {
        "bank": bank,
        "cpu_start": f"${cpu_start:04X}",
        "cpu_end": f"${cpu_end:04X}",
        "rom_start": f"${rom_start:05X}",
        "rom_end": f"${rom_end:05X}",
        "type": region_type,
        "name": name,
        "confidence": "confirmed",
    }


class AnalysisCoverageTest(unittest.TestCase):
    def load(self, document):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "analysis.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return load_analysis_manifest(path)

    def test_unknown_bytes_and_type_percentages_are_counted(self):
        manifest = self.load(
            fixture(
                [
                    region(0, 0x0000, 0x0FFF, "code", "fixed code"),
                    region(1, 0x4000, 0x5FFF, "data", "banked data"),
                ]
            )
        )
        report = calculate_coverage(manifest)
        self.assertEqual(
            report.type_bytes,
            {"code": 0x1000, "data": 0x2000, UNKNOWN_TYPE: 0x5000},
        )
        self.assertEqual(report.analyzed_bytes, 0x3000)
        self.assertEqual(report.analyzed_percent, 37.5)
        document = report_document(manifest, report)
        self.assertEqual(document["analyzed_percent"], 37.5)
        self.assertEqual(document["banks"][0]["analyzed_percent"], 25.0)
        self.assertEqual(document["banks"][1]["analyzed_percent"], 50.0)
        bank_one_data = next(
            item for item in document["banks"][1]["types"] if item["type"] == "data"
        )
        self.assertEqual(bank_one_data["percent_of_bank"], 50.0)
        self.assertEqual(bank_one_data["percent_of_bank_analyzed"], 100.0)

    def test_nested_region_uses_more_specific_type_without_double_counting(self):
        manifest = self.load(
            fixture(
                [
                    region(1, 0x4000, 0x4FFF, "graphics", "container"),
                    region(1, 0x4400, 0x44FF, "pointer_table", "nested table"),
                ]
            )
        )
        report = calculate_coverage(manifest)
        self.assertEqual(report.analyzed_bytes, 0x1000)
        self.assertEqual(report.type_bytes["graphics"], 0x0F00)
        self.assertEqual(report.type_bytes["pointer_table"], 0x0100)

    def test_partial_overlap_is_rejected(self):
        document = fixture(
            [
                region(0, 0x0100, 0x01FF, "code", "left"),
                region(0, 0x0180, 0x027F, "data", "right"),
            ]
        )
        with self.assertRaisesRegex(WorkstationError, "partially overlap"):
            self.load(document)

    def test_incorrect_rom_offset_is_rejected(self):
        item = region(1, 0x4000, 0x40FF, "data", "bad offset")
        item["rom_start"] = "$00000"
        with self.assertRaisesRegex(WorkstationError, "does not match"):
            self.load(fixture([item]))

    def test_svg_contains_bank_map_and_legend(self):
        manifest = self.load(fixture([region(0, 0, 0x3FFF, "code", "all fixed bank")]))
        svg = render_svg(manifest, calculate_coverage(manifest))
        self.assertIn("ROM analysis coverage", svg)
        self.assertIn("Bank 00", svg)
        self.assertIn("code 50.00%", svg)
        self.assertIn("unknown 50.00%", svg)


if __name__ == "__main__":
    unittest.main()