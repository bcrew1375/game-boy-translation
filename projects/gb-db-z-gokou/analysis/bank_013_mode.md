# Bank 13 mode resources and gameplay module

## Confirmed ranges

The final 4 KiB of Bank 13 is unrelated to the Super Game Boy transfer pages
that occupy `0D:4000-$6FFF`. It contains the end of a compressed-resource
sequence, the banked loader and gameplay logic that consumes those resources,
embedded tables, and trailing zero padding.

| CPU range | ROM range | Classification | Evidence |
|---|---:|---|---|
| `0D:7000-$75A3` | `$37000-$375A3` | Compressed graphics resource tails and streams | Seven streams decode consecutively through `$75A3`; `0D:75A4` passes their addresses to `00:35CF`. |
| `0D:75A4-$7F9E` | `$375A4-$37F9E` | Mode loader and gameplay code with embedded tables | Fixed-bank callers select Bank 13 and call `$75A4`; the entry loads graphics/tilemaps, initializes objects, reads input, updates sprites/tilemaps, and returns. |
| `0D:7F9F-$7FFF` | `$37F9F-$37FFF` | Zero padding | All 97 bytes are `$00`, immediately after the final routine instruction at `$7F9E`. |

## Compressed resources

The loader at `0D:75A4` directly or indirectly selects these streams:

| Stream start | Stream end | Compressed bytes | Expanded bytes | Use established by loader |
|---|---:|---:|---:|---|
| `0D:6860` | `$6D01` | 1,186 | 1,536 | Copied to VRAM `$8A00`. |
| `0D:6D02` | `$7073` | 882 | 1,120 | Copied to VRAM `$8200`. |
| `0D:7074` | `$7184` | 273 | 480 | Copied to VRAM `$8020`. |
| `0D:7185` | `$72DB` | 343 | 704 | Conditionally copied to VRAM `$8400`. |
| `0D:72DC` | `$73C0` | 229 | 360 | Mode-selected tilemap copied to `$9800`. |
| `0D:73C1` | `$74A1` | 225 | 360 | Mode-selected tilemap copied to `$9800`. |
| `0D:74A2` | `$75A3` | 258 | 360 | Mode-selected tilemap copied to `$9800`. |

The first two streams begin within the previously classified SGB transfer
pages and continue across `$7000`. This is direct evidence that the ROM reuses
the same source bytes for different consumers; adjacency alone does not define
the data's purpose. The new manifest range starts at `$7000` so it does not
overlap the established `0D:4000-$6FFF` transfer-page classification.

`0D:767C-$7681` is a three-entry pointer table containing `$72DC`, `$73C1`,
and `$74A2`. `0D:7682-$7687` is a parallel three-entry table containing
`$4CF4`, `$4D52`, and `$4CF4`; these addresses are passed to `00:3F8A`, not to
the decompressor. `0D:7688-$768D` is another three-entry in-bank pointer table
used after the selected mode index has been retained.

## Entry and control-flow evidence

The fixed-bank selection path at `00:05B3-$05C6` accepts mode values zero
through two, selects Bank 13, passes the mode in `A`, and calls `0D:75A4`.
Another fixed-bank path does the same before continuing common UI cleanup.

At entry, `0D:75A4` stores the mode in HRAM `$FF99`. It then:

1. disables drawing state and decompresses/copies the common graphics;
2. conditionally loads the `$7185` graphics for modes two and three after
   masking `$FF99` to two bits;
3. selects one of the three compressed `$1214` tilemaps through `$767C`;
4. selects parallel object/setup data through `$7682` and `$7688`;
5. runs input-, timer-, sprite-, and tilemap-update routines through `$7F9E`;
6. restores display state and returns to the fixed-bank caller.

The exact game-facing name of this mode remains unresolved. Symbols therefore
use the conservative `Bank13_Mode*` prefix rather than assigning a speculative
minigame or menu name.

## Remaining work

- Identify the user-visible mode by tracing the fixed-bank selection screen.
- Decode the records selected through `$7682/$7688` and the object templates at
  `$7E65-$7E94` into narrower structures.
- Separate additional embedded tables from executable code in a later
  byte-identical source-annotation pass.