# Title-screen Japanese graphics

## Conclusion

The title-screen Japanese title and selectable menu labels are **fixed 2bpp
screen graphics**, not text rendered from a reusable 16x16 kanji font.

The game does arrange much of the artwork into shapes resembling 16x16
characters, but it loads compressed tile images and writes consecutive tile IDs
as whole rectangles. No character-index stream, kanji-to-glyph lookup table, or
16x16 text-rendering routine is used by these screens.

This system is separate from the primary dialogue font at Bank 1,
`01:5D3B-$6198` (ROM `$05D3B-$06198`), which contains 160 packed 1bpp 8x8
glyphs.

## Address and resource map

Bank 2 occupies ROM offsets `$08000-$0BFFF`. The relevant resources and code
are:

| Bank / CPU range | ROM range | Stored size | Decoded output | Interpretation |
|---|---:|---:|---:|---|
| `02:4000-$459D` | `$08000-$0859D` | `$059E` | `$07A0` bytes | 122 2bpp tiles for the main title screen |
| `02:459E-$465E` | `$0859E-$0865E` | `$00C1` | `$0168` bytes | 20x18 base title tilemap |
| `02:465F-$48E2` | `$0865F-$088E2` | `$0284` | `$02E0` bytes | 46 2bpp menu-label tiles |
| `02:48E3-$4922` | `$088E3-$08922` | `$0040` | raw | Four additional 2bpp tiles copied after the menu resource |
| `02:4923-$4A4B` | `$08923-$08A4B` | `$0129` | `$0140` bytes | 20 2bpp tiles containing the five-character title subtitle |
| `02:7133` | `$0B133` | — | — | Title-screen loader |
| `02:7194` | `$0B194` | — | — | Post-START menu loader and dispatcher |
| `02:721C` | `$0B21C` | — | — | Menu selection/cursor loop |

The compressed resources use the format decoded by `Call_000_35cf` at
`00:35CF`: a 16-bit output length, a 32-byte literal bitmap, and an LZ-style
token stream. The stored extents above are confirmed by the decoder's exact
consumed-byte counts and by the next resource boundaries.

## Main title composition

`TitleScreen_Load` at `02:7133` performs the following operations:

1. Decompresses `02:4000` and copies `$07A0` bytes to VRAM `$8000`, producing
   122 tiles with IDs `$00-$79`.
2. Decompresses `02:459E` and copies a 20x18 tilemap to `$9800`.
3. Decompresses `02:4923` and copies `$0140` bytes to VRAM `$8E00`, producing
   tile IDs `$E0-$F3` under unsigned `$8000-$8FFF` tile addressing.
4. Calls `Tilemap_FillIncrementingRectangle` with start tile `$E0`, dimensions
   10x2, and destination `$98E5`.

The resulting fixed rectangle displays the five-character title subtitle
(the raw Japanese is kept only in the local catalog):

| Glyph (left to right) | Top tiles | Bottom tiles |
|---|---|---|
| 1st | `$E0 $E1` | `$EA $EB` |
| 2nd | `$E2 $E3` | `$EC $ED` |
| 3rd | `$E4 $E5` | `$EE $EF` |
| 4th | `$E6 $E7` | `$F0 $F1` |
| 5th | `$E8 $E9` | `$F2 $F3` |

The apparent 16x16 character cells are a property of this particular image.
The ROM contains a compressed 20-tile bitmap, not a five-byte encoded string.

## Post-START menu composition

On first entry, `TitleMenu_Run` at `02:7194` decompresses `02:465F` to `$02E0`
bytes and copies it to VRAM `$8A00`, assigning tile IDs `$A0-$CD`. It then
copies the four raw tiles at `02:48E3` immediately after that block.

The menu code places these fixed rectangles using consecutive tile IDs:

| Tile range | Rectangle | Meaning (English gloss) |
|---|---:|---|
| `$A0-$A7` | 4x2 tiles | STORY |
| `$A8-$BD` | 11x2 tiles | WORLD TOURNAMENT |
| `$BE-$C5` | 4x2 tiles | VERSUS |
| `$C6-$CD` | 4x2 tiles | TRAINING |

The VERSUS label is omitted in the no-save/feature-disabled state, leaving three menu
choices instead of four.

The 11-tile width of the WORLD TOURNAMENT label is especially strong evidence against a
reusable 16x16 glyph sequence: six independent 16x16 cells would require 12
tile columns. Here the text and spacing are composed directly as one 88x16
pixel strip.

`TitleMenu_Select` at `02:721C` reads up/down input, wraps the selection index,
and derives a cursor sprite Y coordinate from that index. It does not inspect a
character string or redraw label glyphs.

## Reuse checks

Exact tile comparison found only one duplicated 8x8 tile involving the title
or menu resources: main-title tile index 23 equals menu tile index 12. None of
the eleven obvious 16x16 kanji groups (the five-character title subtitle and the
four menu labels) are byte-identical to one another.

An isolated repeated sub-tile is expected in graphical artwork and is not
evidence of a character font. No reusable character index or table was found
in the title loader, menu loader, or selection loop.

## Translation implications

Title/menu translation should use replacement graphics rather than the
dialogue text encoder.

The least invasive approach is:

1. Render replacement 2bpp artwork within the existing tile allocations.
2. Preserve the subtitle's 10x2 rectangle and tile IDs `$E0-$F3`.
3. Preserve the menu rectangles and tile IDs `$A0-$CD`.
4. Recompress the graphics with the existing `00:35CF` codec while retaining
   fixed resource slots or otherwise deliberately relocating later data.
5. Keep replacements conditional to the translated build so the original path
   remains byte-identical.

Changing label widths is possible, but it requires corresponding changes to
the rectangle dimensions, following tile allocations, and potentially label
placement. No run of zero or `$FF` bytes should be assumed to be free space.

## Implemented English replacement

The translated build now replaces both compressed resources while retaining
their original addresses, fixed slot sizes, decoded dimensions, tile IDs, and
tilemap rectangles. The selected artwork reads:

| Original label | English artwork | Rectangle |
|---|---|---:|
| title subtitle (5 chars) | `GOKU'S` / `SOARING LEGEND` | 10x2 tiles |
| menu label 1 | `STORY` | 4x2 tiles |
| menu label 2 | `WORLD TOURNAMENT` | 11x2 tiles |
| menu label 3 | `VERSUS` | 4x2 tiles |
| menu label 4 | `TRAINING` | 4x2 tiles |

The artwork is generated deterministically from repository-owned pixel glyphs
in `projects/gb-db-z-gokou/src/gb_db_z_gokou/title_graphics.py`; it does not
depend on host fonts. The project codec in
`projects/gb-db-z-gokou/src/gb_db_z_gokou/compression.py` encodes the `00:35CF`
resource format. There is no standalone `make title-assets` step; `make
translated` builds the fixed-size resources in memory:

- title menu labels: `$0284` bytes, including padding; the encoded stream uses
  406 bytes and expands to `$02E0` bytes.
- title subtitle: `$0129` bytes, including padding; the encoded stream uses 250
  bytes and expands to `$0140` bytes.

Optional reconstructed previews, when generated, are written under the ignored
`projects/gb-db-z-gokou/analysis/tiles/` directory (`title_menu_english.png`,
`title_subtitle_english.png`).

The project build adapter patches these resources directly into a verified copy
of the original ROM. The four raw menu tiles at `02:48E3-$4922` remain
unmodified because their exact purpose is still unknown.

The original and translated menu resources both use DMG 2bpp palette indices
`0`, `1`, and `3`; index `2` is unused. The title screen uses the normal `$E4`
background-palette mapping, so these correspond to white, light gray, and
black. The original Japanese labels use light-gray interiors (index `1`) with
black borders (index `3`). The translated menu renderer reproduces that same
fill/outline assignment rather than drawing black foreground text with a gray
drop shadow. This changes only translated menu pixels; palette setup, tilemap
placement, decoded dimensions, and fixed ROM resource boundaries are unchanged.

The generator verifies compression round trips and rejects output that exceeds
either fixed slot. Unit tests additionally verify resource sizes, deterministic
output, tile encoding round trips, preview dimensions, a common menu-label left
edge, height, and baseline, and the intended menu fill/outline palette indices.

## Confidence and remaining unknowns

- **Confirmed:** resource addresses and extents, decoded sizes, VRAM
  destinations, tile ranges, rectangle dimensions, visible Japanese artwork,
  and cursor-only selection behavior.
- **Confirmed conclusion:** these title/menu strings are fixed 2bpp graphics,
  not a reusable 16x16 kanji font.
- **Not yet assigned:** the exact visual role of the four raw tiles at
  `02:48E3-$4922`; they are copied after the menu-label resource but are not
  needed to establish the text format. They are deliberately preserved in the
  translated build.