import json
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
ANALYSIS = PROJECT / "analysis" / "project.json"
ORIGINAL_ROM = PROJECT / "original.gb"
BANK_SIZE = 0x4000
sys.path.insert(0, str(PROJECT / "src"))

from gb_db_z_gokou.compression import decompress_resource  # noqa: E402


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
            "01:4920": "SGBDynamicPatternRecordPointers",
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
            "Super Game Boy dynamic-pattern record pointers": 40 * 2,
        }
        by_name = {region["name"]: region for region in self.analysis["regions"]}
        for name, expected_size in expected_sizes.items():
            region = by_name[name]
            actual_size = parse_hex(region["cpu_end"]) - parse_hex(region["cpu_start"]) + 1
            with self.subTest(name=name):
                self.assertEqual(actual_size, expected_size)

    def test_bank4_resource_map_is_an_exact_partition(self):
        regions = sorted(
            (
                parse_hex(region["cpu_start"]),
                parse_hex(region["cpu_end"]),
            )
            for region in self.analysis["regions"]
            if region["bank"] == 4
        )
        self.assertEqual(regions[0][0], 0x4000)
        self.assertEqual(regions[-1][1], 0x7FFF)
        self.assertEqual(sum(end - start + 1 for start, end in regions), BANK_SIZE)
        for left, right in zip(regions, regions[1:]):
            self.assertEqual(left[1] + 1, right[0])

    def test_graphics_resource_catalog_and_streams(self):
        if not ORIGINAL_ROM.is_file():
            self.skipTest(f"{ORIGINAL_ROM.relative_to(PROJECT)} is not available")
        rom = ORIGINAL_ROM.read_bytes()
        catalog_offset = 4 * BANK_SIZE
        catalog = [
            int.from_bytes(rom[offset : offset + 2], "little")
            for offset in range(catalog_offset, catalog_offset + 0x70, 2)
        ]
        self.assertEqual(len(catalog), 0x38)

        expected_derived = {
            0x0B: (1, 0, [0x11]),
            0x0F: (2, 1, [0x11, 0x16]),
            0x13: (6, 3, [0x10, 0x11, 0x12, 0x15, 0x16, 0x17]),
            0x18: (2, 9, [0x16, 0x1B]),
            0x24: (1, 11, [0x10]),
            0x2D: (1, 12, [0x16]),
            0x31: (2, 13, [0x15, 0x1A]),
        }
        destination_indices = rom[catalog_offset + 0x70 : catalog_offset + 0x7F]
        used_indices = []
        for resource_id, (count, start, expected) in expected_derived.items():
            value = catalog[resource_id]
            with self.subTest(resource_id=f"${resource_id:02X}"):
                self.assertEqual((value >> 8, value & 0xFF), (count, start))
                self.assertEqual(
                    list(destination_indices[start : start + count]), expected
                )
                used_indices.extend(range(start, start + count))
        self.assertEqual(sorted(used_indices), list(range(15)))

        expected_stream_counts = {4: 31, 5: 13}
        expected_spans = {4: (0x416F, 0x7E47), 5: (0x4000, 0x5992)}
        for bank, first_id, last_id in ((4, 0x00, 0x28), (5, 0x28, 0x38)):
            streams = {}
            for resource_id in range(first_id, last_id):
                pointer = catalog[resource_id]
                if pointer < 0x4000:
                    self.assertIn(resource_id, expected_derived)
                    continue
                offset = bank * BANK_SIZE + pointer - 0x4000
                decoded = decompress_resource(rom[offset:])
                self.assertEqual(len(decoded.data), 560)
                streams[pointer] = decoded.bytes_consumed

            ordered = sorted(streams.items())
            with self.subTest(bank=bank):
                self.assertEqual(len(ordered), expected_stream_counts[bank])
                self.assertEqual(ordered[0][0], expected_spans[bank][0])
                self.assertEqual(
                    ordered[-1][0] + ordered[-1][1] - 1,
                    expected_spans[bank][1],
                )
                for (start, size), (next_start, _) in zip(ordered, ordered[1:]):
                    self.assertEqual(start + size, next_start)

        bank4_padding = rom[4 * BANK_SIZE + 0x3E48 : 5 * BANK_SIZE]
        self.assertEqual(bank4_padding, bytes(len(bank4_padding)))

    def test_large_graphics_descriptor_table_and_classified_streams(self):
        if not ORIGINAL_ROM.is_file():
            self.skipTest(f"{ORIGINAL_ROM.relative_to(PROJECT)} is not available")
        rom = ORIGINAL_ROM.read_bytes()
        bank6_offset = 6 * BANK_SIZE
        thresholds = list(rom[0x3974:0x397B])
        self.assertEqual(thresholds, [0x14, 0x28, 0x46, 0x60, 0x76, 0x8F, 0xFF])

        aliases = [
            (
                rom[bank6_offset + index * 3],
                int.from_bytes(
                    rom[bank6_offset + index * 3 + 1 : bank6_offset + index * 3 + 3],
                    "little",
                ),
            )
            for index in range(8)
        ]
        self.assertEqual(
            aliases,
            [
                (0x27, 0x41FB),
                (0x27, 0x4233),
                (0x2C, 0x426B),
                (0x27, 0x42CB),
                (0x0A, 0x4303),
                (0x2C, 0x4343),
                (0x2C, 0x43A3),
                (0x00, 0x0000),
            ],
        )

        descriptors = []
        for resource_id in range(0x80):
            offset = bank6_offset + 0x18 + resource_id * 3
            descriptors.append(
                (
                    int.from_bytes(rom[offset : offset + 2], "little"),
                    rom[offset + 2],
                )
            )
        self.assertEqual(len(descriptors), 128)

        def source_bank(resource_id):
            return 6 + next(
                index for index, threshold in enumerate(thresholds)
                if resource_id < threshold
            )

        self.assertEqual(
            [source_bank(resource_id) for resource_id in (0x00, 0x13, 0x14, 0x27, 0x28, 0x45, 0x46, 0x5F, 0x60, 0x75, 0x76, 0x7F)],
            [6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11],
        )
        for resource_id in (0x14, 0x28, 0x46, 0x60, 0x76):
            self.assertEqual(descriptors[resource_id][0], 0x4000)

        expected_outputs = {
            6: [960, 768, 896, 768, 768, 768, 896, 896, 896, 448, 448,
                1024, 1920, 1536, 1536, 576, 576, 1536, 1536, 1536],
            7: [768, 1536, 1536, 1152, 1536, 1536, 576, 1536, 1152, 1536, 960,
                144, 768, 1024, 1024, 768, 1024, 1152, 1536, 1536],
            8: [768] * 14 + [560] * 9 + [768] * 7,
            9: [768] * 26,
            10: [768] * 16 + [1280] * 4 + [768] * 2,
            11: [768] * 10,
        }
        for bank, first_id, last_id, expected_last in (
            (6, 0x00, 0x14, 0x7EF1),
            (7, 0x14, 0x28, 0x7F4D),
            (8, 0x28, 0x46, 0x7FD0),
            (9, 0x46, 0x60, 0x7D98),
            (10, 0x60, 0x76, 0x7E70),
            (11, 0x76, 0x80, 0x58D5),
        ):
            streams = {}
            for resource_id in range(first_id, last_id):
                pointer, shape = descriptors[resource_id]
                effective_shape = aliases[shape & 0x1F][0] if shape & 0x80 else shape
                width = effective_shape & 0x0F
                height = (effective_shape >> 4) + 6
                self.assertGreater(width, 0)
                self.assertLessEqual(width, 12)
                self.assertGreaterEqual(height, 6)
                self.assertLessEqual(height, 10)
                offset = bank * BANK_SIZE + pointer - 0x4000
                decoded = decompress_resource(rom[offset:])
                self.assertEqual(
                    len(decoded.data), expected_outputs[bank][resource_id - first_id]
                )
                streams[pointer] = decoded.bytes_consumed

            ordered = sorted(streams.items())
            with self.subTest(bank=bank):
                self.assertEqual(ordered[0][0], 0x4403 if bank == 6 else 0x4000)
                self.assertEqual(ordered[-1][0] + ordered[-1][1] - 1, expected_last)
                for (start, size), (next_start, _) in zip(ordered, ordered[1:]):
                    self.assertEqual(start + size, next_start)

        bank6_padding = rom[6 * BANK_SIZE + 0x3EF2 : 7 * BANK_SIZE]
        self.assertEqual(bank6_padding, bytes(270))
        bank7_padding = rom[7 * BANK_SIZE + 0x3F4E : 8 * BANK_SIZE]
        self.assertEqual(bank7_padding, bytes(178))
        bank8_padding = rom[8 * BANK_SIZE + 0x3FD1 : 9 * BANK_SIZE]
        self.assertEqual(bank8_padding, bytes(47))
        bank9_padding = rom[9 * BANK_SIZE + 0x3D99 : 10 * BANK_SIZE]
        self.assertEqual(bank9_padding, bytes(615))
        bank10_padding = rom[10 * BANK_SIZE + 0x3E71 : 11 * BANK_SIZE]
        self.assertEqual(bank10_padding, bytes(399))

        secondary_descriptors = []
        for index in range(33):
            offset = bank6_offset + 0x198 + index * 3
            secondary_descriptors.append(
                (
                    int.from_bytes(rom[offset : offset + 2], "little"),
                    rom[offset + 2],
                )
            )
        self.assertEqual([shape for _, shape in secondary_descriptors], [0x08] * 33)

        secondary_streams = {}
        for pointer, _ in secondary_descriptors[:15]:
            offset = 11 * BANK_SIZE + pointer - 0x4000
            decoded = decompress_resource(rom[offset:])
            self.assertEqual(len(decoded.data), 768)
            secondary_streams[pointer] = decoded.bytes_consumed
        ordered = sorted(secondary_streams.items())
        self.assertEqual(ordered[0][0], 0x58D6)
        self.assertEqual(ordered[-1][0] + ordered[-1][1] - 1, 0x7DCF)
        for (start, size), (next_start, _) in zip(ordered, ordered[1:]):
            self.assertEqual(start + size, next_start)

        bank11_padding = rom[11 * BANK_SIZE + 0x3DD0 : 12 * BANK_SIZE]
        self.assertEqual(bank11_padding, bytes(560))

        bank12_streams = {}
        for pointer, _ in secondary_descriptors[15:]:
            offset = 12 * BANK_SIZE + pointer - 0x4000
            decoded = decompress_resource(rom[offset:])
            self.assertEqual(len(decoded.data), 768)
            bank12_streams[pointer] = decoded.bytes_consumed
        self.assertEqual(
            [pointer for pointer, _ in secondary_descriptors[24:27]],
            [0x556A, 0x5AF2, 0x584B],
        )
        ordered = sorted(bank12_streams.items())
        self.assertEqual(ordered[0][0], 0x4000)
        self.assertEqual(ordered[-1][0] + ordered[-1][1] - 1, 0x6E20)
        for (start, size), (next_start, _) in zip(ordered, ordered[1:]):
            self.assertEqual(start + size, next_start)
        bank12_padding = rom[12 * BANK_SIZE + 0x2E21 : 13 * BANK_SIZE]
        self.assertEqual(bank12_padding, bytes(4_575))

        alias_layout_starts = [word for _, word in aliases[:-1]] + [0x4403]
        expected_layout_sizes = [56, 56, 96, 56, 64, 96, 96]
        self.assertEqual(
            [right - left for left, right in zip(alias_layout_starts, alias_layout_starts[1:])],
            expected_layout_sizes,
        )
        trailer = rom[bank6_offset + 0x33F : bank6_offset + 0x343]
        self.assertEqual(trailer, b"\xFF\xFF\x78\xFF")

    def test_second_graphics_batch_size(self):
        names = {
            "Graphics resource shape-alias descriptors",
            "Graphics resource source-pointer and shape descriptors",
            "Large graphics resources $00-$13 compressed streams",
            "Bank 6 trailing zero padding",
            "Large graphics resources $14-$1E compressed streams",
        }
        size = sum(
            parse_hex(region["rom_end"]) - parse_hex(region["rom_start"]) + 1
            for region in self.analysis["regions"]
            if region["name"] in names
        )
        self.assertEqual(size, 26_454)

    def test_third_graphics_batch_size(self):
        names = {
            "Large graphics resources $1F-$27 compressed streams",
            "Bank 7 trailing zero padding",
            "Large graphics resources $28-$45 compressed streams",
            "Bank 8 trailing zero padding",
        }
        size = sum(
            parse_hex(region["rom_end"]) - parse_hex(region["rom_start"]) + 1
            for region in self.analysis["regions"]
            if region["name"] in names
        )
        self.assertEqual(size, 22_079)

    def test_fourth_graphics_batch_size(self):
        names = {
            "Large graphics resources $46-$5F compressed streams",
            "Bank 9 trailing zero padding",
            "Large graphics resources $60-$6B compressed streams",
        }
        size = sum(
            parse_hex(region["rom_end"]) - parse_hex(region["rom_start"]) + 1
            for region in self.analysis["regions"]
            if region["name"] in names
        )
        self.assertEqual(size, 24_046)

    def test_fifth_graphics_batch_size(self):
        names = {
            "Secondary graphics resource source-pointer and shape descriptors",
            "Graphics shape-alias tile-index layouts",
            "Large graphics resources $6C-$75 compressed streams",
            "Bank 10 trailing zero padding",
            "Large graphics resources $76-$7F compressed streams",
            "Secondary graphics resources 0-14 compressed streams",
            "Bank 11 trailing zero padding",
        }
        size = sum(
            parse_hex(region["rom_end"]) - parse_hex(region["rom_start"]) + 1
            for region in self.analysis["regions"]
            if region["name"] in names
        )
        self.assertEqual(size, 25_725)

    def test_sixth_analysis_batch_size_and_sgb_pages(self):
        names = {
            "Secondary graphics resources 15-32 compressed streams",
            "Bank 12 trailing zero padding",
            "Super Game Boy border PCT_TRN and CHR_TRN transfer pages",
        }
        size = sum(
            parse_hex(region["rom_end"]) - parse_hex(region["rom_start"]) + 1
            for region in self.analysis["regions"]
            if region["name"] in names
        )
        self.assertEqual(size, 28_672)

        expected_symbols = {
            "00:0561": "SGB_LoadBorderTransferPages",
            "0D:4000": "SGBBorderTransferPage_Pct0",
            "0D:5000": "SGBBorderTransferPage_Pct1",
            "0D:6000": "SGBBorderTransferPage_Chr",
        }
        for address, name in expected_symbols.items():
            self.assertEqual(self.analysis["symbols"][address]["name"], name)

        if not ORIGINAL_ROM.is_file():
            self.skipTest(f"{ORIGINAL_ROM.relative_to(PROJECT)} is not available")
        rom = ORIGINAL_ROM.read_bytes()
        fixed_loader = rom[0x0561:0x05B0]
        self.assertEqual(len(fixed_loader), 0x4F)
        self.assertEqual(fixed_loader[-1], 0xC9)
        self.assertEqual(fixed_loader.count(b"\x3E\x0D\xC7"), 3)
        self.assertIn(b"\x11\x00\x40\x21\x00\x88\x01\x00\x10", fixed_loader)
        self.assertIn(b"\x11\x00\x50\x21\x00\x88\x01\x00\x10", fixed_loader)
        self.assertIn(b"\x11\x00\x60\x21\x00\x88\x01\x00\x10", fixed_loader)
        for setup_index in (4, 5, 6):
            self.assertIn(bytes((0x3E, setup_index, 0xCD, 0x2D, 0x41)), fixed_loader)

    def test_dynamic_pattern_records_match_bank6_resource_dimensions(self):
        if not ORIGINAL_ROM.is_file():
            self.skipTest(f"{ORIGINAL_ROM.relative_to(PROJECT)} is not available")
        rom = ORIGINAL_ROM.read_bytes()
        pointer_table = 0x4920
        pointers = [
            int.from_bytes(rom[offset : offset + 2], "little")
            for offset in range(pointer_table, 0x4970, 2)
        ]
        self.assertEqual(len(pointers), 40)
        self.assertEqual(pointers[-2:], [0x4C1B, 0x4C34])

        bank6 = 6 * BANK_SIZE
        for resource_id, start in enumerate(pointers):
            descriptor = bank6 + 0x18 + resource_id * 3
            shape = rom[descriptor + 2]
            if shape & 0x80:
                shape = rom[bank6 + (shape & 0x1F) * 3]
            width = shape & 0x0F
            height = (shape >> 4) + 6
            payload_size = (width * height + 3) // 4
            next_start = pointers[resource_id + 1] if resource_id < 39 else 0x4C4D
            padding = next_start - (start + 1 + payload_size)
            with self.subTest(resource_id=f"${resource_id:02X}"):
                self.assertGreater(width, 0)
                self.assertLessEqual(width, 20)
                self.assertLessEqual(height, 18)
                self.assertEqual(padding, 3 if resource_id == 0x20 else 0)
                if padding:
                    padding_start = start + 1 + payload_size
                    self.assertEqual(rom[padding_start:next_start], b"\x55" * padding)

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