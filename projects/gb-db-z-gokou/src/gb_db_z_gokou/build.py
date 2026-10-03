"""Build the GB DBZ GOKOU English ROM from a verified original ROM."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gbworkbench.manifests import read_tsv, require_columns
from gbworkbench.patching import (
    BuildResult,
    bounded_write,
    changed_offsets,
    fixed_slot,
    sha256,
    validate_changed_scope,
    write_game_boy_global_checksum,
)
from gbworkbench.project import ProjectConfig

from .compression import compress_resource
from .font import (
    FONT_COMPRESSED_SLOT_SIZE,
    FONT_ROM_OFFSET,
    build_english_font,
    compress_font,
    decompress_font,
)
from .text import (
    AllocationRange,
    allocate_translated_streams,
    bank3_offset,
    encode_translated_text,
    load_character_encoding,
)
from .title_graphics import (
    MENU_COMPRESSED_SLOT_SIZE,
    TITLE_COMPRESSED_SLOT_SIZE,
    build_menu_tiles,
    build_title_tiles,
)


YES_NO_OFFSET = 0x03ECB
MENU_ROM_OFFSET = 0x0865F
TITLE_ROM_OFFSET = 0x08923
GLOBAL_CHECKSUM_OFFSET = 0x014E


class TranslationBuildError(ValueError):
    """Raised when the translation manifests cannot be built safely."""


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


def load_patches(path: Path) -> list[TextPatch]:
    rows = read_tsv(path)
    require_columns(path, rows, {"id", "original_address", "english"})
    patches = [
        TextPatch(row["id"], parse_bank3_address(row["original_address"]), row["english"])
        for row in rows
    ]
    identifiers = [patch.identifier for patch in patches]
    if not patches or len(identifiers) != len(set(identifiers)):
        raise TranslationBuildError("patch manifest must contain unique records")
    if any(not patch.english for patch in patches):
        raise TranslationBuildError("every patch must contain English text")
    return patches


def load_references(path: Path, patch_ids: set[str]) -> list[TextReference]:
    rows = read_tsv(path)
    require_columns(path, rows, {"id", "table_address", "message_index"})
    references = [
        TextReference(
            row["id"],
            parse_bank3_address(row["table_address"]),
            int(row["message_index"], 0),
        )
        for row in rows
    ]
    unknown = sorted({reference.identifier for reference in references} - patch_ids)
    missing = sorted(patch_ids - {reference.identifier for reference in references})
    if unknown or missing:
        raise TranslationBuildError(
            f"reference IDs do not match patches; unknown={unknown}, missing={missing}"
        )
    return references


def load_ranges(path: Path) -> list[AllocationRange]:
    rows = read_tsv(path)
    require_columns(path, rows, {"start", "end"})
    ranges = [
        AllocationRange(parse_bank3_address(row["start"]), parse_bank3_address(row["end"]))
        for row in rows
    ]
    if not ranges:
        raise TranslationBuildError("translation range manifest is empty")
    return ranges


def _allowed_offsets(project: ProjectConfig, references: list[TextReference]) -> set[int]:
    allowed = {
        offset
        for region in project.approved_ranges
        for offset in range(region.start, region.end + 1)
    }
    for reference in references:
        offset = bank3_offset(reference.table_address + reference.message_index * 2)
        allowed.update((offset, offset + 1))
    return allowed


def validate(project: ProjectConfig) -> None:
    """Validate public project manifests without requiring an original ROM."""
    patches = load_patches(project.manifests["patches"])
    load_references(project.manifests["references"], {patch.identifier for patch in patches})
    ranges = load_ranges(project.manifests["ranges"])
    encoding = load_character_encoding(project.manifests["encoding"])
    allocate_translated_streams(
        [
            (
                patch.identifier,
                encode_translated_text(patch.english, encoding),
            )
            for patch in patches
        ],
        ranges,
    )


def build(original: bytes, project: ProjectConfig) -> BuildResult:
    """Apply all project-authored replacements to an already validated ROM."""
    patches = load_patches(project.manifests["patches"])
    patch_by_id = {patch.identifier: patch for patch in patches}
    references = load_references(project.manifests["references"], set(patch_by_id))
    ranges = load_ranges(project.manifests["ranges"])
    encoding = load_character_encoding(project.manifests["encoding"])
    encoded = [
        (patch.identifier, encode_translated_text(patch.english, encoding))
        for patch in patches
    ]
    addresses = allocate_translated_streams(encoded, ranges)

    rom = bytearray(original)
    original_font = decompress_font(
        original[FONT_ROM_OFFSET : FONT_ROM_OFFSET + FONT_COMPRESSED_SLOT_SIZE]
    ).data
    bounded_write(
        rom,
        FONT_ROM_OFFSET,
        fixed_slot(
            compress_font(build_english_font(original_font)),
            FONT_COMPRESSED_SLOT_SIZE,
            "English font",
        ),
        "English font",
    )
    bounded_write(
        rom,
        MENU_ROM_OFFSET,
        fixed_slot(
            compress_resource(build_menu_tiles()),
            MENU_COMPRESSED_SLOT_SIZE,
            "menu graphics",
        ),
        "menu graphics",
    )
    bounded_write(
        rom,
        TITLE_ROM_OFFSET,
        fixed_slot(
            compress_resource(build_title_tiles()),
            TITLE_COMPRESSED_SLOT_SIZE,
            "title graphics",
        ),
        "title graphics",
    )
    bounded_write(
        rom,
        YES_NO_OFFSET,
        bytes(encoding[character] for character in "YESNO "),
        "YES/NO labels",
    )

    for region in ranges:
        start = bank3_offset(region.start)
        end = bank3_offset(region.end) + 1
        bounded_write(rom, start, b"\x00" * (end - start), "translated text range")
    for identifier, data in encoded:
        bounded_write(rom, bank3_offset(addresses[identifier]), data, identifier)
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
        bounded_write(
            rom,
            pointer_offset,
            addresses[reference.identifier].to_bytes(2, "little"),
            f"pointer for {reference.identifier}",
        )

    write_game_boy_global_checksum(rom, GLOBAL_CHECKSUM_OFFSET)
    output = bytes(rom)
    changed = changed_offsets(original, output)
    validate_changed_scope(changed, _allowed_offsets(project, references))
    return BuildResult(
        data=output,
        sha256=sha256(output),
        changed_offsets=changed,
        metadata={"text_addresses": addresses},
    )