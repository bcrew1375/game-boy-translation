"""Codec for the LZ resource format consumed by the routine at 00:35CF."""

from __future__ import annotations

from dataclasses import dataclass


class ResourceCodecError(ValueError):
    """Raised when a compressed resource is malformed or cannot be encoded."""


@dataclass(frozen=True)
class DecodedResource:
    data: bytes
    bytes_consumed: int


def decompress_resource(data: bytes) -> DecodedResource:
    """Decode one literal-dictionary/LZ resource stream."""
    if len(data) < 34:
        raise ResourceCodecError("compressed resource is shorter than its 34-byte header")
    output_size = int.from_bytes(data[:2], "little")
    symbols = tuple(
        value
        for value in range(256)
        if data[2 + value // 8] & (1 << (value & 7))
    )
    if not symbols:
        raise ResourceCodecError("compressed resource has an empty literal dictionary")

    output = bytearray()
    cursor = 34
    while len(output) < output_size:
        if cursor >= len(data):
            raise ResourceCodecError(
                "compressed resource ends before the requested output size"
            )
        token = data[cursor]
        cursor += 1
        if token < len(symbols):
            output.append(symbols[token])
            continue

        if cursor >= len(data):
            raise ResourceCodecError("compressed resource ends inside a backreference")
        count = token - len(symbols) + 1
        distance = data[cursor] + 1
        cursor += 1
        if distance > len(output):
            raise ResourceCodecError(
                f"backreference distance {distance} exceeds {len(output)} output bytes"
            )
        if len(output) + count > output_size:
            raise ResourceCodecError("backreference exceeds the requested output size")
        for _ in range(count):
            output.append(output[-distance])

    return DecodedResource(bytes(output), cursor)


def compress_resource(data: bytes) -> bytes:
    """Encode bytes in the resource format consumed by the routine at 00:35CF."""
    if not data or len(data) > 0xFFFF:
        raise ResourceCodecError("resource data length must be 1..65535 bytes")
    symbols = tuple(sorted(set(data)))
    if len(symbols) >= 256:
        raise ResourceCodecError("resource data uses too many distinct byte values")
    symbol_index = {value: index for index, value in enumerate(symbols)}
    max_match = 256 - len(symbols)

    bitmap = bytearray(32)
    for value in symbols:
        bitmap[value // 8] |= 1 << (value & 7)

    encoded = bytearray(len(data).to_bytes(2, "little"))
    encoded.extend(bitmap)
    cursor = 0
    while cursor < len(data):
        best_length = 0
        best_distance = 0
        for distance in range(1, min(256, cursor) + 1):
            length = 0
            while (
                length < max_match
                and cursor + length < len(data)
                and data[cursor + length] == data[cursor + length - distance]
            ):
                length += 1
            if length > best_length:
                best_length = length
                best_distance = distance

        if best_length >= 3:
            encoded.append(len(symbols) + best_length - 1)
            encoded.append(best_distance - 1)
            cursor += best_length
        else:
            encoded.append(symbol_index[data[cursor]])
            cursor += 1
    return bytes(encoded)