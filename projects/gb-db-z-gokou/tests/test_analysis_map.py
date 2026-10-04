import json
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
ANALYSIS = PROJECT / "analysis" / "project.json"
BANK_SIZE = 0x4000


def parse_hex(value: str) -> int:
    if not value.startswith("$"):
        raise ValueError(f"expected $-prefixed hexadecimal value: {value!r}")
    return int(value[1:], 16)


def rom_offset(bank: int, address: int) -> int:
    if bank == 0:
        if not 0 <= address <= 0x3FFF:
            raise ValueError("fixed-bank address outside $0000-$3FFF")
        return address
    if not 0x4000 <= address <= 0x7FFF:
        raise ValueError("switchable-bank address outside $4000-$7FFF")
    return bank * BANK_SIZE + address - 0x4000


class AnalysisMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))

    def test_region_addresses_match_rom_offsets(self):
        rom_size = self.analysis["rom"]["size_bytes"]
        for region in self.analysis["regions"]:
            bank = region["bank"]
            cpu_start = parse_hex(region["cpu_start"])
            cpu_end = parse_hex(region["cpu_end"])
            rom_start = parse_hex(region["rom_start"])
            rom_end = parse_hex(region["rom_end"])
            with self.subTest(name=region["name"]):
                self.assertLessEqual(cpu_start, cpu_end)
                self.assertEqual(rom_start, rom_offset(bank, cpu_start))
                self.assertEqual(rom_end, rom_offset(bank, cpu_end))
                self.assertLess(rom_end, rom_size)
                self.assertIn(region["confidence"], {"confirmed", "strong_inference"})

    def test_regions_only_overlap_when_one_classifies_nested_routine_data(self):
        by_bank = {}
        for region in self.analysis["regions"]:
            by_bank.setdefault(region["bank"], []).append(region)
        for bank, regions in by_bank.items():
            ordered = sorted(regions, key=lambda region: parse_hex(region["cpu_start"]))
            for index, left in enumerate(ordered):
                left_start = parse_hex(left["cpu_start"])
                left_end = parse_hex(left["cpu_end"])
                for right in ordered[index + 1 :]:
                    right_start = parse_hex(right["cpu_start"])
                    if right_start > left_end:
                        break
                    right_end = parse_hex(right["cpu_end"])
                    nested = (
                        left_start <= right_start <= right_end <= left_end
                        or right_start <= left_start <= left_end <= right_end
                    )
                    with self.subTest(bank=bank, left=left["name"], right=right["name"]):
                        self.assertTrue(nested)
                        self.assertIn("routine_data", {left["type"], right["type"]})

    def test_symbol_addresses_are_valid_and_unique(self):
        names = set()
        for address, symbol in self.analysis["symbols"].items():
            space, value = address.split(":", 1)
            with self.subTest(address=address):
                if space == "HRAM":
                    self.assertTrue(0xFF80 <= int(value, 16) <= 0xFFFE)
                else:
                    rom_offset(int(space, 16), int(value, 16))
                self.assertNotIn(symbol["name"], names)
                names.add(symbol["name"])
                self.assertIn(symbol["confidence"], {"confirmed", "strong_inference"})

    def test_first_bank1_pass_is_recorded(self):
        expected = {
            "01:4000": "SGB_SendPackets",
            "01:4172": "SGB_Initialize",
            "01:41F2": "SGBAttributeMap_ApplyRectangle",
            "01:42E0": "PresentationBuffers_Clear",
            "01:430B": "SGB_PlaySoundEffect",
            "01:442C": "SGBPaletteTransferImage",
            "01:471B": "SGBPatternIndexMap",
            "01:4754": "SGBFixedPatternRecords",
            "01:4920": "SGBPresentationRecordPointers",
            "01:4C4D": "SGBAttributeMapRectangleRecords",
        }
        for address, name in expected.items():
            with self.subTest(address=address):
                self.assertEqual(self.analysis["symbols"][address]["name"], name)

    def test_pal_transfer_image_has_an_exact_partition(self):
        regions = sorted(
            (
                parse_hex(region["cpu_start"]),
                parse_hex(region["cpu_end"]),
            )
            for region in self.analysis["regions"]
            if region["bank"] == 1
            and parse_hex(region["cpu_start"]) >= 0x442C
            and parse_hex(region["cpu_end"]) <= 0x542B
        )
        self.assertEqual(regions[0][0], 0x442C)
        self.assertEqual(regions[-1][1], 0x542B)
        self.assertEqual(sum(end - start + 1 for start, end in regions), 0x1000)
        for left, right in zip(regions, regions[1:]):
            self.assertEqual(left[1] + 1, right[0])

    def test_pal_transfer_nested_table_sizes(self):
        expected_sizes = {
            "Super Game Boy pattern-index map": 57,
            "Super Game Boy fixed 5x7 pattern records": 44 * 10,
            "Super Game Boy presentation-record pointers": 38 * 2,
        }
        by_name = {region["name"]: region for region in self.analysis["regions"]}
        for name, expected_size in expected_sizes.items():
            region = by_name[name]
            actual_size = parse_hex(region["cpu_end"]) - parse_hex(region["cpu_start"]) + 1
            with self.subTest(name=name):
                self.assertEqual(actual_size, expected_size)

    def test_attribute_rectangle_record_inventory(self):
        records = [
            (0x4C4D, 8, 8, True, 26),
            (0x4C52, 20, 10, True, 0),
            (0x4C57, 10, 10, True, 0),
            (0x4C5C, 10, 10, True, 10),
            (0x4C61, 10, 10, True, 10),
            (0x4C66, 10, 10, True, 0),
            (0x4C6B, 5, 8, True, 21),
            (0x4C70, 5, 8, True, 34),
            (0x4C75, 8, 8, True, 26),
            (0x4C7A, 20, 4, True, 200),
            (0x4C7F, 6, 6, False, 227),
            (0x4C8C, 16, 1, True, 302),
            (0x4C91, 20, 18, False, 0),
            (0x4CEF, 2, 8, True, 202),
            (0x4CF4, 20, 18, False, 0),
            (0x4D52, 20, 18, False, 0),
            (0x4DB0, 12, 10, False, 44),
            (0x4DD2, 11, 13, False, 44),
            (0x4DFA, 5, 7, False, 87),
            (0x4E07, 20, 18, False, 0),
        ]
        cursor = records[0][0]
        for start, width, height, repeated_fill, destination in records:
            with self.subTest(address=f"01:{start:04X}"):
                self.assertEqual(start, cursor)
                self.assertLessEqual(destination % 20 + width, 20)
                self.assertLessEqual(destination // 20 + height, 18)
                payload_size = 1 if repeated_fill else (width * height + 3) // 4
                cursor = start + 4 + payload_size
        self.assertEqual(cursor, 0x4E65)


if __name__ == "__main__":
    unittest.main()