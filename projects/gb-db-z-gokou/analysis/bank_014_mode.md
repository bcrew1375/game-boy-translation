# Bank 14 primary mode and editor module

## Scope

Bank 14 is a mixed code/data bank selected by several fixed-bank paths. The
main entry is `0E:4000`; a separate fixed-bank path calls `0E:6DDB`, and another
calls `0E:7447`. The exact user-visible name of the mode is not yet confirmed,
so this note and the symbols use conservative names.

## Confirmed layout

| CPU range | ROM range | Size | Classification | Evidence |
|---|---:|---:|---|---|
| `0E:4000-$4B1F` | `$38000-$38B1F` | 2,848 | Primary mode code | Fixed-bank callers select Bank 14 and call `$4000`. The module initializes display state, loads the resources below, processes input and object state, updates tilemaps/OAM, and returns. |
| `0E:4B20-$4B6F` | `$38B20-$38B6F` | 80 | Tilemap data | `$40E6` copies a `$04 x $14` rectangle from `$4B20` to tilemap `$9C00`; 4 x 20 gives the exact 80-byte extent. |
| `0E:4B70-$526F` | `$38B70-$3926F` | 1,792 | Raw 2bpp graphics | `$40C3` copies exactly `$0700` bytes from `$4B70` to VRAM `$8000`. |
| `0E:5270-$550F` | `$39270-$3950F` | 672 | Raw 2bpp graphics | `$40D2` copies exactly `$02A0` bytes from `$5270` to VRAM `$8A00`. |
| `0E:5510-$6DCA` | `$39510-$3ADCA` | 6,331 | Lookup, map, and object data | The primary code indexes `$5510` and later in-bank structures. The interval includes long zero-filled areas and generated false instruction streams; it is retained as data pending structure decoding. |
| `0E:6DCB-$7461` | `$3ADCB-$3B461` | 1,687 | Editor/state-transform code with embedded tables | `00:0F9D` calls `$6DDB`; `00:0E5D` calls `$7447`. This block edits a 32-byte state at `$D828`, renders cursor/tilemap data, handles directional and confirmation input, and uses embedded pointer and command records near `$7366-$7446`. |
| `0E:7462-$7FFF` | `$3B462-$3BFFF` | 2,974 | Zero padding | Every byte is `$00`, beginning immediately after the `RET` at `$7461`. |

The ranges form an exact, gap-free partition of Bank 14.

## Main entry and resource use

The fixed-bank mode dispatcher selects Bank 14 and calls `0E:4000`. A second
fixed-bank wrapper preserves an argument in `C`, disables the LCD, and calls the
same entry with the argument restored in `A`.

`0E:40A4` establishes the graphics boundaries directly:

1. copy `$0700` bytes from `$4B70` to VRAM `$8000`;
2. copy `$02A0` bytes from `$5270` to VRAM `$8A00`;
3. copy a `$0414` tilemap rectangle from `$4B20` to `$9C00`.

The code later indexes data rooted at `$5510` while resolving board/map cells.
That establishes ownership of the following data interval but not yet every
record boundary or gameplay meaning.

## Secondary entries

`0E:6DDB` initializes a selectable/editor-like screen and enters a loop that
updates coordinates, validates a 32-byte state buffer, displays a cursor, and
accepts or rejects edits. `0E:7447` clears 64 bytes at `$D828`, calls the same
state helper used by the editor, transforms 32 entries through `0E:71A4`, and
returns. These mechanical descriptions are confirmed; “editor” is a structural
label, not a claim about the screen's final game-facing name.

## Remaining work

- Identify the mode and editor screens in-game.
- Decode the structures rooted at `$5510`, `$706F`, `$70FD`, `$7366`, and
  `$7376` into narrower typed records.
- Separate embedded tables from executable code without altering ROM layout.
