# Bank 5 presentation and selection modules

## Scope

This pass classifies the previously unknown Bank 5 range `05:5993-$7FFF`
(9,837 bytes). It follows the compressed character/resource streams ending at
`05:5992`, but it is a separate mixture of command data, executable screen
logic, compressed graphics, layout data, a tilemap, and padding.

## Confirmed layout

| CPU range | ROM range | Size | Classification | Evidence |
|---|---:|---:|---|---|
| `05:5993-$5C42` | `$15993-$15C42` | 688 | Command/display data | Contains a 53-entry little-endian pointer table at `$5AA5` whose targets `$5B0F-$5C43` delimit variable command streams. Fixed-bank code also selects pointer-based strings through the table at `$5EA5`. |
| `05:5C43-$65D7` | `$15C43-$165D7` | 2,453 | Presentation and selection code with embedded tables | Fixed-bank callers select Bank 5 and enter `$5CAE`, `$6041`, `$6222`, and `$6296`. The routines stage OAM, update palettes/tilemaps, process input, and invoke graphics loading. Tables are retained within the broad code-owned range where exact instruction/data separation is not yet complete. |
| `05:65D8-$6C9C` | `$165D8-$16C9C` | 1,733 | Compressed graphics | Decoder consumes exactly 1,733 bytes and expands 1,920 bytes. `$6296` passes `$65D8` to `00:35CF` and copies the result to VRAM `$8010`. |
| `05:6C9D-$6DBB` | `$16C9D-$16DBB` | 287 | Compressed graphics | Decoder consumes exactly 287 bytes and expands 416 bytes. `$6296` loads it after the first resource and copies the result to VRAM `$8800`. |
| `05:6DBC-$7567` | `$16DBC-$17567` | 1,964 | Object, animation, and layout data | The presentation routines retain in-bank pointers into this interval, including `$6DBC`; generated instruction mnemonics are not treated as execution evidence. Exact record grammar remains unresolved. |
| `05:7568-$7923` | `$17568-$17923` | 956 | Compressed graphics | Decoder consumes exactly 956 bytes and expands 1,120 bytes. `$6296` passes `$7568` to `00:35CF` and copies the result to VRAM `$8A00`. |
| `05:7924-$79B2` | `$17924-$179B2` | 143 | Tilemap data | `$6296` copies an `$0D x $0B` rectangle (143 bytes) from `$7924` to tilemap address `$9844`. |
| `05:79B3-$7FFF` | `$179B3-$17FFF` | 1,613 | Zero padding | Every byte is `$00`; `$79B2` is the tilemap's final nonzero byte. |

These ranges form a gap-free partition of the newly classified Bank 5 suffix.

## Entry evidence

- `00:0C88` selects Bank 5 and calls `05:5CAE` between two 60-frame waits.
- The fixed-bank main flow calls `05:6041` while evaluating a selection and
  calls `05:6222` and `05:6296` from separate setup/presentation paths.
- `05:6296` initializes display state, loads all three compressed resources,
  copies the `$7924` tilemap, stages sprites through data beginning at `$6DBC`,
  and runs a timed input/update loop.

The exact game-facing names of these screens and effects remain unresolved.
Symbols therefore use conservative `Bank5_*` names.

## Remaining work

- Decode the command-stream grammar and determine the exact `$5AA5` table role.
- Split the embedded lookup and animation tables from executable code.
- Identify the visible screens and effects through runtime traces.
