"""Build the English ROM directly from a user-supplied original ROM."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

from gb.compression import compress_resource
from gb.font import (
    FONT_COMPRESSED_SLOT_SIZE,
    FONT_ROM_OFFSET,
    build_english_font,
    compress_font,
    decompress_font,
)
from gb.text import (
    AllocationRange,
    allocate_translated_streams,
    bank3_offset,
    encode_translated_text,
    load_character_encoding,
)
from gb.title_graphics import (
    MENU_COMPRESSED_SLOT_SIZE,
    TITLE_COMPRESSED_SLOT_SIZE,
    build_menu_tiles,
    build_title_tiles,
)


ORIGINAL_ROM_SIZE = 0x40000
ORIGINAL_ROM_SHA256 = "f63b95b5b03c399b8546e5f72004a2ebaf2e2826fa83a76705b2629bd4da817f"
TRANSLATED_ROM_SHA256 = "312798b43d2415fecbfe777e7d54c10f247b60bb68554657392aff6398a5150b"

YES_NO_OFFSET = 0x03ECB
MENU_ROM_OFFSET = 0x0865F
TITLE_ROM_OFFSET = 0x08923
GLOBAL_CHECKSUM_OFFSET = 0x014E


class TranslationBuildError(ValueError):
    """Raised when the input or translation manifest cannot be built safely."""


@dataclass(frozen=True)
class TextPatch:
    identifier: str
    original_address: int
    english: str


@dataclass(frozen=True)
class TextReference:
    identifier: str
    table_address: int
    message_index: int


@dataclass(frozen=True)
class BuildResult:
    data: bytes
    sha256: str
    changed_offsets: frozenset[int]
    text_addresses: dict[str, int]


def parse_bank3_address(value: str) -> int:
    try:
        bank, address = value.split(":", 1)
        if int(bank, 16) != 3:
            raise ValueError
        result = int(address, 16)
    except ValueError as error:
        raise TranslationBuildError(f"invalid bank-3 address: {value!r}") from error
    if not 0x4000 <= result <= 0x7FFF:
        raise TranslationBuildError(f"bank-3 address outside $4000-$7FFF: {value}")
    return result


def _read_tsv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as source:
            return list(csv.DictReader(source, delimiter="\t"))
    except OSError as error:
        raise TranslationBuildError(str(error)) from error


def load_patches(path: Path) -> list[TextPatch]:
    patches = [
        TextPatch(row["id"], parse_bank3_address(row["original_address"]), row["english"])
        for row in _read_tsv(path)
    ]
    identifiers = [patch.identifier for patch in patches]
    if not patches or len(identifiers) != len(set(identifiers)):
        raise TranslationBuildError("patch manifest must contain unique records")
    if any(not patch.english for patch in patches):
        raise TranslationBuildError("every patch must contain English text")
    return patches


def load_references(path: Path, patch_ids: set[str]) -> list[TextReference]:
    references = [
        TextReference(
            row["id"],
            parse_bank3_address(row["table_address"]),
            int(row["message_index"], 0),
        )
        for row in _read_tsv(path)
    ]
    unknown = sorted({reference.identifier for reference in references} - patch_ids)
    missing = sorted(patch_ids - {reference.identifier for reference in references})
    if unknown or missing:
        raise TranslationBuildError(
            f"reference IDs do not match patches; unknown={unknown}, missing={missing}"
        )
    return references


def load_ranges(path: Path) -> list[AllocationRange]:
    ranges = [
        AllocationRange(parse_bank3_address(row["start"]), parse_bank3_address(row["end"]))
        for row in _read_tsv(path)
    ]
    if not ranges:
        raise TranslationBuildError("translation range manifest is empty")
    return ranges


def _slot(data: bytes, size: int, name: str) -> bytes:
    if len(data) > size:
        raise TranslationBuildError(f"{name} is {len(data)} bytes; slot is {size}")
    return data.ljust(size, b"\x00")


def _write_global_checksum(rom: bytearray) -> None:
    rom[GLOBAL_CHECKSUM_OFFSET : GLOBAL_CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = sum(rom) & 0xFFFF
    rom[GLOBAL_CHECKSUM_OFFSET : GLOBAL_CHECKSUM_OFFSET + 2] = checksum.to_bytes(2, "big")


def _allowed_offsets(ranges: list[AllocationRange], references: list[TextReference]) -> set[int]:
    allowed = set(range(GLOBAL_CHECKSUM_OFFSET, GLOBAL_CHECKSUM_OFFSET + 2))
    allowed.update(range(YES_NO_OFFSET, YES_NO_OFFSET + 6))
    allowed.update(range(FONT_ROM_OFFSET, FONT_ROM_OFFSET + FONT_COMPRESSED_SLOT_SIZE))
    allowed.update(range(MENU_ROM_OFFSET, MENU_ROM_OFFSET + MENU_COMPRESSED_SLOT_SIZE))
    allowed.update(range(TITLE_ROM_OFFSET, TITLE_ROM_OFFSET + TITLE_COMPRESSED_SLOT_SIZE))
    for region in ranges:
        allowed.update(range(bank3_offset(region.start), bank3_offset(region.end) + 1))
    for reference in references:
        offset = bank3_offset(reference.table_address + reference.message_index * 2)
        allowed.update((offset, offset + 1))
    return allowed


def build_translated_rom(
    original: bytes,
    *,
    encoding_path: Path,
    patches_path: Path,
    references_path: Path,
    ranges_path: Path,
    verify_output_hash: bool = True,
) -> BuildResult:
    """Apply all project-authored replacements to a validated original ROM."""
    digest = hashlib.sha256(original).hexdigest()
    if len(original) != ORIGINAL_ROM_SIZE or digest != ORIGINAL_ROM_SHA256:
        raise TranslationBuildError(
            "unsupported original ROM: expected "
            f"{ORIGINAL_ROM_SIZE} bytes with SHA-256 {ORIGINAL_ROM_SHA256}, "
            f"got {len(original)} bytes with SHA-256 {digest}"
        )

    patches = load_patches(patches_path)
    patch_by_id = {patch.identifier: patch for patch in patches}
    references = load_references(references_path, set(patch_by_id))
    ranges = load_ranges(ranges_path)
    encoding = load_character_encoding(encoding_path)
    encoded = [
        (patch.identifier, encode_translated_text(patch.english, encoding))
        for patch in patches
    ]
    addresses = allocate_translated_streams(encoded, ranges)

    rom = bytearray(original)
    original_font = decompress_font(
        original[FONT_ROM_OFFSET : FONT_ROM_OFFSET + FONT_COMPRESSED_SLOT_SIZE]
    ).data
    rom[FONT_ROM_OFFSET : FONT_ROM_OFFSET + FONT_COMPRESSED_SLOT_SIZE] = _slot(
        compress_font(build_english_font(original_font)),
        FONT_COMPRESSED_SLOT_SIZE,
        "English font",
    )
    rom[MENU_ROM_OFFSET : MENU_ROM_OFFSET + MENU_COMPRESSED_SLOT_SIZE] = _slot(
        compress_resource(build_menu_tiles()), MENU_COMPRESSED_SLOT_SIZE, "menu graphics"
    )
    rom[TITLE_ROM_OFFSET : TITLE_ROM_OFFSET + TITLE_COMPRESSED_SLOT_SIZE] = _slot(
        compress_resource(build_title_tiles()), TITLE_COMPRESSED_SLOT_SIZE, "title graphics"
    )
    rom[YES_NO_OFFSET : YES_NO_OFFSET + 6] = bytes(
        encoding[character] for character in "YESNO "
    )

    for region in ranges:
        start = bank3_offset(region.start)
        end = bank3_offset(region.end) + 1
        rom[start:end] = b"\x00" * (end - start)
    for identifier, data in encoded:
        offset = bank3_offset(addresses[identifier])
        rom[offset : offset + len(data)] = data
    for reference in references:
        pointer_address = reference.table_address + reference.message_index * 2
        pointer_offset = bank3_offset(pointer_address)
        actual = int.from_bytes(original[pointer_offset : pointer_offset + 2], "little")
        expected = patch_by_id[reference.identifier].original_address
        if actual != expected:
            raise TranslationBuildError(
                f"original pointer 03:{pointer_address:04X} is ${actual:04X}; "
                f"expected ${expected:04X} for {reference.identifier}"
            )
        rom[pointer_offset : pointer_offset + 2] = addresses[reference.identifier].to_bytes(
            2, "little"
        )

    _write_global_checksum(rom)
    changed = frozenset(
        offset for offset, (before, after) in enumerate(zip(original, rom)) if before != after
    )
    outside = changed - _allowed_offsets(ranges, references)
    if outside:
        first = min(outside)
        raise TranslationBuildError(f"build changed an unapproved byte at ROM ${first:05X}")

    output = bytes(rom)
    output_digest = hashlib.sha256(output).hexdigest()
    if verify_output_hash and output_digest != TRANSLATED_ROM_SHA256:
        raise TranslationBuildError(
            f"translated ROM SHA-256 is {output_digest}; expected {TRANSLATED_ROM_SHA256}"
        )
    return BuildResult(output, output_digest, changed, addresses)
