# Bank 02 analysis and documentation

Bank 2 occupies CPU `$4000-$7FFF` and ROM offsets `$08000-$0BFFF`. The
analysis manifest now classifies every byte in the bank. The first `$0A4C`
bytes contain the previously documented title-screen resources; this note
records the remaining presentation resources, title/menu code, scenario data,
and exact padding boundaries.

Full coverage does not imply that every field in the pointer-selected scenario
records has been decoded. Generated mgbdis instruction labels inside the data
ranges are not treated as evidence that those bytes are executable.

## Mapped ranges

| CPU range | ROM range | Classification | Current interpretation | Confidence |
|---|---:|---|---|---|
| `02:4000-$4A4B` | `$08000-$08A4B` | Graphics/tilemap resources | Main title graphics, title tilemap, menu-label graphics, four raw tiles, and subtitle graphics documented in `title_screen_graphics.md`. | Confirmed |
| `02:4A4C-$4A73` | `$08A4C-$08A73` | Pointer table | 20 little-endian resource pointers. Repeated entries alias shared resources. | Confirmed |
| `02:4A74-$6C8C` | `$08A74-$0AC8C` | Compressed graphics | Thirteen unique, gap-free streams consumed by the fixed-bank presentation path. | Confirmed |
| `02:6C8D-$7132` | `$0AC8D-$0B132` | Data | Counted object-placement records and repeated presentation layouts. | Confirmed data ownership; individual visible roles partial |
| `02:7133-$726F` | `$0B133-$0B26F` | Code with embedded records | Title-screen loader, post-START menu setup, and the menu selection/cursor loop. | Confirmed |
| `02:7270-$72FF` | `$0B270-$0B2FF` | Padding | 144 zero bytes between modules. | Confirmed |
| `02:7300-$7E30` | `$0B300-$0BE30` | Data | Nested pointer tables and command-like records selected from fixed-bank state. | Strong inference; complete record grammar unresolved |
| `02:7E31-$7FFF` | `$0BE31-$0BFFF` | Padding | 463 trailing zero bytes. | Confirmed |

## Pointer-selected presentation resources

`00:3ADB` selects Bank 2, indexes the table at `02:4A4C`, passes the selected
address to the shared decompressor at `00:35CF`, and copies the decoded result
to VRAM `$8A00`. The table has 20 entries but only 13 unique targets because
several IDs deliberately reuse the same stream.

| Stream | Stored bytes | Decoded bytes |
|---|---:|---:|
| `02:4A74-$4D4F` | 732 | 768 |
| `02:4D50-$50CB` | 892 | 1,024 |
| `02:50CC-$5377` | 684 | 768 |
| `02:5378-$563F` | 712 | 768 |
| `02:5640-$5841` | 514 | 768 |
| `02:5842-$5ADF` | 670 | 768 |
| `02:5AE0-$5D67` | 648 | 768 |
| `02:5D68-$5F95` | 558 | 768 |
| `02:5F96-$61FB` | 614 | 768 |
| `02:61FC-$64C5` | 714 | 768 |
| `02:64C6-$67D5` | 784 | 768 |
| `02:67D6-$696A` | 405 | 384 |
| `02:696B-$6C8C` | 802 | 1,024 |

Every stream ends exactly at the next unique pointer. The final stream ends at
`02:6C8C`, immediately before the object/layout data used by the same fixed-bank
presentation routine.

After decompression, `00:3ADB` reads a count byte at `02:6C8D` and transforms
the following four-byte records into OAM staging entries. The larger interval
contains repeated coordinate/tile layouts of the same general form. Screen or
character names are intentionally deferred until runtime confirmation.

## Title and menu control code

The code at `02:7133-$726F` is reached directly from the fixed-bank main-state
dispatcher:

- `02:7133` decompresses and places the main title graphics, tilemap, and
  subtitle resources;
- `02:7194` loads and draws the post-START menu labels; and
- `02:721C` runs the directional selection and cursor update loop.

The exact 144-byte zero run at `02:7270-$72FF` separates this code from the next
pointer-selected data module.

## Scenario and UI records

Fixed-bank code at `00:03F5` selects Bank 2 and treats `02:7300` as a two-level
pointer structure. The first index comes from `$D8C1`; the selected subtable is
then indexed with `$D8C2 - 1`, and the resulting address is stored in
`$D7CD-$D7CE` for the later state path at `00:0641`.

The module contains dense nested pointers and command-like byte records through
`02:7E30`. This establishes data ownership and pointer selection, but not the
complete meaning of each command byte or every visible scene. The range is
therefore conservatively classified as scenario/UI records rather than as code.

## Remaining work

- Trace the `00:0641` consumer to document the complete `02:7300` record
  grammar and identify each game-facing scenario.
- Associate the `02:4A4C` presentation resource IDs and `02:6C8D` layouts with
  visible screens through runtime observation.
- Split broad data regions only when stable record boundaries and semantics are
  supported by direct evidence.