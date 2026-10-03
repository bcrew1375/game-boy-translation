import csv
import re
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
GLOSSARY = PROJECT / "translation" / "glossary.tsv"
REFERENCE_INDEX = PROJECT / "analysis" / "bank3_text_reference_index.tsv"

EXPECTED_COLUMNS = [
    "term_id",
    "english",
    "romanization",
    "category",
    "evidence_addresses",
    "reference_count",
    "confidence",
    "notes",
]
ALLOWED_CATEGORIES = {"character", "species", "place", "event", "item", "technique", "concept"}
ALLOWED_CONFIDENCE = {"confirmed", "strong", "tentative"}
ADDRESS = re.compile(r"03:[0-9A-F]{4}")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")


def read_tsv(path: Path):
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        return reader.fieldnames, list(reader)


class TerminologyGlossaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.columns, cls.rows = read_tsv(GLOSSARY)
        _, index_rows = read_tsv(REFERENCE_INDEX)
        cls.known_addresses = {row["stream_address"] for row in index_rows}

    def test_schema_and_required_inventory(self):
        self.assertEqual(self.columns, EXPECTED_COLUMNS)
        self.assertGreaterEqual(len(self.rows), 40)
        identifiers = {row["term_id"] for row in self.rows}
        self.assertTrue(
            {
                "goku",
                "piccolo",
                "saiyan",
                "dragon_ball",
                "senzu_bean",
                "special_beam_cannon",
                "spirit_bomb",
                "kaioken",
                "great_ape",
                "power_level",
            }.issubset(identifiers)
        )

    def test_ids_and_english_terms_are_unique(self):
        identifiers = [row["term_id"] for row in self.rows]
        english = [row["english"].casefold() for row in self.rows]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(len(english), len(set(english)))
        for row in self.rows:
            self.assertRegex(row["term_id"], r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
            self.assertTrue(row["english"])
            self.assertTrue(row["romanization"])

    def test_enumerated_fields_and_reference_counts(self):
        for row in self.rows:
            self.assertIn(row["category"], ALLOWED_CATEGORIES)
            self.assertIn(row["confidence"], ALLOWED_CONFIDENCE)
            addresses = row["evidence_addresses"].split(";")
            self.assertGreaterEqual(int(row["reference_count"]), len(addresses))
            for address in addresses:
                self.assertRegex(address, ADDRESS)
                self.assertIn(address, self.known_addresses)

    def test_contains_terms_only_not_dialogue_or_cjk(self):
        text = GLOSSARY.read_text(encoding="utf-8")
        self.assertIsNone(CJK.search(text))
        for prohibited in ("\\n", "<WAIT>", "<END>", "「", "」"):
            self.assertNotIn(prohibited, text)
        for row in self.rows:
            self.assertNotIn("\n", row["notes"])
            self.assertLessEqual(len(row["notes"]), 180)


if __name__ == "__main__":
    unittest.main()