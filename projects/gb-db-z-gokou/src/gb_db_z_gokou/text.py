"""Bank-3 text stream decoding helpers."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

from gbworkbench.text import (
    AllocationRange,
    TextEncodeError,
    TextEncoding,
    allocate_streams,
    encode_text,
    load_character_encoding as load_generic_character_encoding,
)


ROM_BANK_SIZE = 0x4000
BANK3_FILE_BASE = 3 * ROM_BANK_SIZE
ROOT_CPU_ADDRESS = 0x4000
ROOT_ENTRY_COUNT = 26


class TextDecodeError(ValueError):
    """Raised for an invalid pointer or malformed/unbounded text stream."""


def bank3_offset(cpu_address: int) -> int:
    """Convert a bank-3 CPU address to a ROM file offset."""
    if not 0x4000 <= cpu_address <= 0x7FFF:
        raise TextDecodeError(
            f"bank-3 CPU address must be $4000-$7FFF, got ${cpu_address:04X}"
        )
    return BANK3_FILE_BASE + cpu_address - 0x4000


def read_word_bank3(rom: bytes, cpu_address: int) -> int:
    """Read a little-endian word through the bank-3 ROM window."""
    offset = bank3_offset(cpu_address)
    if offset + 2 > len(rom):
        raise TextDecodeError(f"pointer read at 03:{cpu_address:04X} exceeds ROM")
    return rom[offset] | rom[offset + 1] << 8


def load_tile_characters(path: str | Path) -> dict[int, str]:
    """Load tile-to-character records from analysis/font_tiles.tsv."""
    import csv

    result: dict[int, str] = {}
    with Path(path).open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            result[int(row["tile_id"], 0)] = row["character"]
    return result


def load_character_encoding(path: str | Path) -> dict[str, int]:
    """Load the canonical translated character-to-stream-byte map."""
    return load_generic_character_encoding(path, maximum_value=0xAF)


def encode_translated_text(
    text: str,
    encoding: dict[str, int],
    *,
    max_line_tiles: int = 18,
) -> bytes:
    """Encode TSV-style translated text with line/wait controls and terminator."""
    return encode_text(
        text,
        TextEncoding(
            characters=encoding,
            controls=(("\\n", b"\xFD"), ("<WAIT>", b"\xFB")),
            terminator=b"\xFE",
            max_line_units=max_line_tiles,
            line_control="\\n",
        ),
    )


def _composite_character(value: int, tiles: dict[int, str]) -> str:
    """Reproduce the interpreter's base-tile and combining-mark arithmetic."""
    if value < 0xBF:
        tile, mark = (value + 0x56) & 0xFF, "\u3099"
    elif value < 0xC4:
        tile, mark = (value + 0x5B) & 0xFF, "\u3099"
    elif value < 0xD3:
        tile, mark = (value + 0x79) & 0xFF, "\u3099"
    elif value < 0xD8:
        tile, mark = (value + 0x7E) & 0xFF, "\u3099"
    elif value < 0xDD:
        tile, mark = (value + 0x42) & 0xFF, "\u309A"
    else:
        tile, mark = (value + 0x74) & 0xFF, "\u309A"

    base = tiles.get(tile)
    if not base:
        return f"<{value:02X}>"
    return unicodedata.normalize("NFC", base + mark)


@dataclass(frozen=True)
class DecodedStream:
    """Decoded text and its top-level bank-3 source location."""

    cpu_address: int
    text: str
    bytes_consumed: int


def allocate_translated_streams(
    encoded: list[tuple[str, bytes]], ranges: list[AllocationRange]
) -> dict[str, int]:
    """First-fit streams in order without splitting one across allocation ranges."""
    return allocate_streams(encoded, ranges, minimum=0x4000, maximum=0x7FFF)


@dataclass(frozen=True)
class TextTable:
    """One structurally inferred pointer table selected by the bank-3 root."""

    root_index: int
    cpu_address: int
    stream_pointers: tuple[int, ...]


def infer_text_table(
    rom: bytes, root_index: int, table_address: int, *, max_entries: int = 256
) -> TextTable:
    """Infer a pointer table ending immediately before its earliest stream.

    Each accepted word must point forward into bank 3. The smallest accepted
    stream pointer becomes the upper bound for subsequent table words. This is
    the structure used by all non-null entries in TextData_Bank3Root.
    """
    if not 0 <= root_index < ROOT_ENTRY_COUNT:
        raise TextDecodeError(
            f"root index must be $00-${ROOT_ENTRY_COUNT - 1:02X}"
        )
    if not 0x4000 <= table_address <= 0x7FFF:
        return TextTable(root_index, table_address, ())

    pointers: list[int] = []
    cursor = table_address
    first_stream = 0x8000
    while cursor + 1 < first_stream and len(pointers) < max_entries:
        pointer = read_word_bank3(rom, cursor)
        if not 0x4000 <= pointer <= 0x7FFF:
            break
        if pointer < cursor + 2:
            break
        pointers.append(pointer)
        first_stream = min(first_stream, pointer)
        cursor += 2
    return TextTable(root_index, table_address, tuple(pointers))


def enumerate_text_tables(rom: bytes) -> tuple[TextTable, ...]:
    """Infer all 26 root-selected bank-3 text pointer tables."""
    tables = []
    for root_index in range(ROOT_ENTRY_COUNT):
        table_address = read_word_bank3(
            rom, ROOT_CPU_ADDRESS + 2 * root_index
        )
        tables.append(infer_text_table(rom, root_index, table_address))
    return tuple(tables)


class Bank3TextDecoder:
    """Decode the stream format consumed by TextStream_VBlankStep."""

    def __init__(
        self,
        rom: bytes,
        tiles: dict[int, str],
        *,
        max_depth: int = 16,
        max_bytes: int = 0x10000,
    ):
        self.rom = rom
        self.tiles = tiles
        self.max_depth = max_depth
        self.max_bytes = max_bytes

    def message_pointer(self, message_id: int, context: int = 0) -> int:
        """Resolve a message ID using the same two pointer lookups as 00:329F."""
        if not 0 <= message_id <= 0xFF:
            raise TextDecodeError("message ID must be $00-$FF")
        if not 0 <= context <= 0x18:
            raise TextDecodeError("context must select root entry $01-$19")

        if message_id >= 0x80:
            table = read_word_bank3(self.rom, ROOT_CPU_ADDRESS)
            index = message_id - 0x80
        else:
            table = read_word_bank3(
                self.rom, ROOT_CPU_ADDRESS + 2 * (context + 1)
            )
            index = message_id

        if not 0x4000 <= table <= 0x7FFF:
            raise TextDecodeError(
                f"root entry resolves to invalid table pointer ${table:04X}"
            )
        pointer = read_word_bank3(self.rom, table + 2 * index)
        if not 0x4000 <= pointer <= 0x7FFF:
            raise TextDecodeError(
                f"message entry resolves to invalid stream pointer ${pointer:04X}"
            )
        return pointer

    def decode_message(self, message_id: int, context: int = 0) -> DecodedStream:
        """Resolve and decode one message."""
        return self.decode_pointer(self.message_pointer(message_id, context))

    def decode_pointer(self, cpu_address: int) -> DecodedStream:
        """Decode a stream at a known bank-3 CPU address."""
        byte_count = [0]
        text, consumed = self._decode(cpu_address, 0, byte_count, ())
        return DecodedStream(cpu_address, text, consumed)

    def _decode(
        self,
        cpu_address: int,
        depth: int,
        byte_count: list[int],
        stack: tuple[int, ...],
    ) -> tuple[str, int]:
        if depth > self.max_depth:
            raise TextDecodeError(
                f"nested expansion exceeds maximum depth {self.max_depth}"
            )
        if cpu_address in stack:
            chain = " -> ".join(
                f"03:{address:04X}" for address in (*stack, cpu_address)
            )
            raise TextDecodeError(f"recursive expansion cycle: {chain}")

        output: list[str] = []
        pointer = cpu_address
        while True:
            offset = bank3_offset(pointer)
            if offset >= len(self.rom):
                raise TextDecodeError(f"stream read at 03:{pointer:04X} exceeds ROM")
            value = self.rom[offset]
            pointer += 1
            byte_count[0] += 1
            if byte_count[0] > self.max_bytes:
                raise TextDecodeError(
                    f"decoding exceeds maximum of {self.max_bytes} bytes"
                )

            if value == 0xFE:
                return "".join(output), pointer - cpu_address
            if value == 0xFD:
                output.append("\n")
            elif value == 0xFB:
                output.append("<WAIT>")
            elif value < 0xB0:
                output.append(self.tiles.get(value) or f"<{value:02X}>")
            elif value < 0xE2:
                output.append(_composite_character(value, self.tiles))
            else:
                target = read_word_bank3(
                    self.rom, ROOT_CPU_ADDRESS + 2 * (value - 0xD8)
                )
                if not 0x4000 <= target <= 0x7FFF:
                    raise TextDecodeError(
                        f"token ${value:02X} resolves to invalid pointer ${target:04X}"
                    )
                nested, _ = self._decode(
                    target, depth + 1, byte_count, (*stack, cpu_address)
                )
                output.append(nested)