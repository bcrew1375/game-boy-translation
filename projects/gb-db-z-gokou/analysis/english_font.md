# English Font Replacement

## Build separation

The original ROM embeds its font resource at Bank 1, CPU `$5D3B-$6198` (ROM
`$05D3B-$06198`). The translated build replaces that resource in the same
`$45E`-byte slot. The generated resource is padded to exactly the original
length, so every following Bank 1 address remains unchanged.

Build the translated ROM with:

```sh
make translated
```

This writes `build/gb-db-z-gokou/translated.gb`. The project build adapter
(`projects/gb-db-z-gokou/src/gb_db_z_gokou/build.py`) generates the font and
title resources in memory and writes them straight into their fixed ROM slots,
so there is no longer a standalone `make font-assets` step.

The canonical font definition lives in
`projects/gb-db-z-gokou/src/gb_db_z_gokou/font.py`, and the English
character-to-byte mapping is the project manifest
`projects/gb-db-z-gokou/translation/encoding.tsv`. Generated previews, when
written, go under the ignored `projects/gb-db-z-gokou/analysis/tiles/`.

## Compression format

The font resource is decoded by `Call_000_35CF`. Its confirmed format is:

1. A little-endian 16-bit decompressed length.
2. A 32-byte bitmap identifying literal byte values. Bit `N` indicates that
   byte value `N` is present in the literal dictionary.
3. A token stream. Tokens below the dictionary size select literal values in
   ascending byte-value order. Other tokens encode an LZ copy length; the next
   byte encodes a backwards distance of 1 through 256 bytes.

The original `$45E`-byte stream expands to `$500` bytes: 160 packed 1bpp 8x8
tiles. The deterministic English stream is 627 bytes before padding, leaving
491 bytes unused inside the fixed resource slot.

## Tile allocation

The translated font uses:

- `$00`: space;
- `$01-$1A`: uppercase `A-Z`;
- `$1B-$34`: lowercase `a-z`;
- `$35-$48`: punctuation and symbols;
- `$49-$7F`: currently blank and available for later additions;
- `$80-$89`: original numeric glyphs, preserved byte-for-byte;
- `$8A-$95`: original UI/meter graphics, preserved byte-for-byte;
- `$96-$9D`: original direct-write UI letters, preserved byte-for-byte; and
- `$9E-$9F`: original arrows, preserved byte-for-byte.

The canonical translation encoding deliberately omits duplicate UI-letter
tiles `$96-$9D`; translated text uses the alphabet in `$01-$34`. English text
must use direct bytes below `$B0`. The original interpreter's composite kana
ranges `$B0-$E1` remain implemented but are not part of the English encoding.

## Current limitation

The current translated build also relocates the selected English Bank-3 strings
listed in `projects/gb-db-z-gokou/translation/patches.tsv`. Untranslated Bank-3
streams retain their original encoding and are outside the current patch scope.