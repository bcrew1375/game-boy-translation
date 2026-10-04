# Bank 00 analysis and documentation

Bank 00 is the fixed ROM window at CPU `$0000-$3FFF`; therefore its CPU addresses and ROM file offsets are identical. This document records the current static analysis of the complete bank. It intentionally separates **confirmed behavior** from contextual inference. The original RGBDS source remains byte-identical after the associated label/comment pass.

The analysis manifest now classifies every byte in this bank. Broad ranges that
contain both executable paths and embedded records remain conservatively named;
full coverage does not imply that every internal field or game-facing concept
has been resolved.

## Confidence terms

- **Confirmed**: established directly from instructions, hardware behavior, call structure, or exact data use.
- **Strong inference**: structure and callers support the description, but runtime context or banked callee semantics are incomplete.
- **Unknown/data**: mgbdis emitted instructions, but control flow or byte structure indicates that some or all of the range is data.

## Whole-bank map

| CPU / ROM range | Classification | Current interpretation | Confidence |
|---|---|---|---|
| `$0000-$000F` | Code | Paired MBC2 ROM-bank switch/save and restore RST handlers. Bank writes use `$2100`; HRAM `$FFA2/$FFA3` cache current/previous banks. | Confirmed |
| `$0010-$003F` | Code/stubs | Frame-delay RSTs at `$0010`, `$0020`, and `$0028`; other bytes include unused/padding-like RST slots and generated references that must remain compatible. | Mixed |
| `$0040-$0060` | Vectors | VBlank and LCD STAT vectors jump to `$01BB` and `$0258`; timer, serial, and joypad vectors return immediately. | Confirmed |
| `$0061-$00FF` | Padding | 159 zero bytes before the cartridge header. | Confirmed bytes; purpose conventional |
| `$0100-$014F` | Header | Entry jump, Nintendo logo, title `GB DBZ GOKOU`, DMG/MBC2+BATTERY/ROM-size metadata, and checksums. | Confirmed |
| `$0150-$01BA` | Code | Startup: waits for a safe LCD phase, disables interrupts/LCD, clears VRAM/WRAM/OAM-related storage, initializes HRAM state, installs OAM DMA code, initializes palettes, and enters banked initialization. | Confirmed |
| `$01BB-$020A` | Code | VBlank handler: saves registers/bank, invokes bank 3 and bank 15 callbacks, applies HRAM LCD shadows, restores bank/registers, and increments `$FFA8`. | Confirmed |
| `$020B-$0257` | Code | VBlank helper paths that selectively apply SCY/SCX/WX/LYC/LCDC/BGP state and return from interrupt. | Confirmed mechanics; modes not named |
| `$0258-$02D4` | Code | LCD STAT handler and scanline-mode dispatch. It selects behavior from `$FF9A`/LYC and manipulates WX, LCDC, LYC, and BGP for raster effects. | Confirmed mechanics; visual roles partly unknown |
| `$02D5-$0342` | Code | Small raster/value helpers followed by banked wrappers into banks 1 and 15. | Confirmed mechanics; high-level purpose unknown |
| `$0343-$05AF` | Code | Top-level scene/state initialization and dispatch. Uses `$D7C7/$D7C8` as progression/state fields, invokes banks 1/2/5, configures LCD shadows, tilemaps, and palettes. | Strong inference |
| `$05B0-$0F44` | Code + embedded records | Menu/UI/state handlers, frame waits, input-driven selection, bank-1 text/UI calls, object setup, and compact records referenced through fixed-bank tables. | Strong inference; individual states unresolved |
| `$0F45-$1202` | Code + tables | Initializes a large gameplay session under `$D7xx-$DAxx`, builds UI/tilemaps, invokes banked data routines, and enters a per-entity loop. | Strong inference |
| `$1203-$20D3` | Code + tables | Main battle/gameplay orchestration: entity iteration, selection screens, calculations, object/tile setup, transitions, and banked message/UI wrappers. Exact game terms are not yet assigned. | Strong inference |
| `$20D4-$27D3` | Code + tables | Gameplay calculations and state mutation over two parallel WRAM structures near `$D9B8/$D9E8`; includes counters, comparisons, random-dependent decisions, and UI/event dispatch. | Strong inference |
| `$27D4-$2866` | Data with generated labels | Dense byte and little-endian pointer tables. Many bytes disassemble as implausible instructions and are indexed by nearby dispatch code. | Confirmed data presence; formats partly unknown |
| `$2867-$2A31` | Code + tables | Event/message dispatch and condition checks using IDs, state bytes, and table-selected handlers. | Strong inference |
| `$2A32-$2D11` | Code + embedded records | More event/UI dispatch, bank-1 presentation wrappers, and compact tables such as `$2C96`, `$2CB2`, and `$2CC7`. | Strong inference |
| `$2D12-$2D9C` | Code | One- or two-controller joypad polling. HRAM `$FFA4/$FFA6` hold current buttons and `$FFA5/$FFA7` newly pressed buttons. | Confirmed |
| `$2D9D-$2DB4` | Code/routine data | Copies the ten-byte OAM DMA routine at `$2DAB-$2DB4` to HRAM `$FF80-$FF89`; DMA source is WRAM `$C000`. | Confirmed |
| `$2DB5-$2DCF` | Code | Safely waits for VBlank, masks VBlank interrupt, disables LCDC bit 7, updates the LCDC shadow, and restores IE. | Confirmed |
| `$2DD0-$2E30` | Code | Input-repeat/directional-state helper plus direct setters/clearers for LCDC shadow bits 0, 1, and 5. | Confirmed mechanics |
| `$2E31-$2E85` | Code | VBlank wait primitive and input-repeat timing update. `RST $20` enters the frame wait; `RST $10` repeats it A times. | Confirmed |
| `$2E86-$2F46` | Code | Unsigned division/multiplication and fixed-point-style arithmetic helpers. Register-level behavior is visible, but complete calling conventions still need focused tests. | Confirmed arithmetic family; interfaces partial |
| `$2F47-$301F` | Code | Numeric conversion, pointer arithmetic, signed/two's-complement helpers, indexed 16-bit lookup, linear copy, and add-with-carry helpers. | Confirmed mechanics |
| `$3020-$303B` | Code | General and small memory-fill loops. | Confirmed |
| `$303C-$3087` | Code | LCD-safe VRAM copy, byte-doubling copy, and a VRAM read helper; all wait until STAT mode 3 has ended. | Confirmed |
| `$3088-$3128` | Code | LCD-safe byte reads/writes and rectangular tilemap fill/copy helpers using the 32-byte tilemap stride. | Confirmed |
| `$3129-$315A` | Code + small data | Clears WRAM object/tile staging records, initializes DMG palettes, and performs a fixed-bank jump-table dispatch at `$3152`. | Confirmed mechanics |
| `$315B-$31E5` | Code | MBC2 save-slot writer/reader. A slot contains 126 decoded bytes represented as 252 nibble cells; checksum and marker handling are explicit. | Confirmed |
| `$31E6-$322C` | Code + data | Uploads a small fixed graphics pattern around `$320F/$3217` and enters a command-driven tilemap renderer. | Confirmed mechanics; asset meaning unknown |
| `$322D-$32D5` | Code | Parses a byte stream with `$FC/$FE` commands and character ranges, resolves bank-3 pointer tables, and queues rendering through `$C1A0/$C1A8-$C1A9`. This is direct text/font-system evidence. | Strong inference |
| `$32D6-$33B1` | Code | Renderer setup, terminated-string/record copies, numeric formatting into `$C5C0`, and stream-length/alignment helpers. | Strong inference |
| `$33B2-$3440` | Code | Full tilemap clear plus descriptor-driven tilemap copy/fill operations. | Confirmed mechanics |
| `$3441-$34C9` | Code | Input-driven grid cursor routine using WRAM cursor/object fields and frame waits. | Strong inference |
| `$34CA-$35CE` | Code | Tilemap-window drawing, border/rectangle manipulation, and layout helpers. | Strong inference |
| `$35CF-$365C` | Code | Graphics stream loader/decompressor family. Data are consumed through banked pointers and expanded to VRAM/staging buffers. Exact compression format remains to be documented. | Strong inference |
| `$365D-$36C5` | Code | OAM staging builder. It reads bank-1 sprite metadata and writes four-byte OAM entries under `$C000`, including X/Y transforms and flags. | Confirmed mechanics |
| `$36C6-$3783` | Code + data | Loads graphics, populates tilemaps, clears VRAM strips, initializes a 40-entry shadow OAM layout, and includes small fixed pattern data at `$3765`. | Strong inference |
| `$3784-$37EA` | Code | Bank-4/5 graphics-resource resolver and loader, including chained descriptors and tile-copy loops. | Strong inference |
| `$37EB-$3878` | Code | Four directional/paired transition helpers updating HRAM scroll/window shadows; returns carry while a transition remains active. | Confirmed mechanics; direction names deferred |
| `$3879-$397A` | Code + data | Bank-6 graphics/layout resolver, VRAM copy, and tilemap placement calculations. Small lookup data begins near `$397B`. | Strong inference |
| `$3980-$3A9D` | Code | Screen/tilemap clearing and bank-1 UI/message setup; maps record IDs to layout values at `$D728/$D72A`. | Strong inference |
| `$3A9E-$3B98` | Code | UI reset, input-controlled selection, OAM construction, and window show/hide transitions. | Strong inference |
| `$3B99-$3D25` | Code | Multi-row menu/grid rendering and cursor navigation using dimensions stored in HRAM `$FF92-$FF96`. | Strong inference |
| `$3D26-$3E71` | Code + tables | Additional cursor/grid movement, tilemap calculations, and rendering helpers. | Strong inference |
| `$3E72-$3F69` | Mostly data with some callable entries | Dense UI/layout records and pointer-like values; generated instruction labels inside this area are not reliable proof of executable code. | Confirmed data presence; boundaries partial |
| `$3F6A-$3FB8` | Code + 8-byte table | Bank-1 UI/message wrappers, writes IDs `$5B-$5D` or table `$51-$54` to `$D726...`, and leaves bank 1 selected at `$3FB0`. | Strong inference |
| `$3FB9-$3FFF` | Padding | 71 zero bytes to the end of bank 0. | Confirmed |

## Confirmed low-level interfaces

### Frame and LCD

- `00:2DB5` `LCD_DisableSafely`: waits until `LY >= $91`, clears LCDC bit 7, mirrors LCDC to `hShadowLCDC`, and preserves the previous IE value.
- `00:2E31` `Frame_WaitVBlank`: preserves all general registers, clears `hFrameCounter`, HALTs until VBlank increments it, advances `$FFA9`, and updates input-repeat state.
- `$2DF9/$2E00`: set/clear LCDC shadow bits 0-1 together.
- `$2E07/$2E0E`: set/clear LCDC shadow bit 0.
- `$2E15/$2E1C`: set/clear LCDC shadow bit 1.
- `$2E23/$2E2A`: set/clear LCDC shadow bit 5.

### VRAM and tilemaps

- `00:303C` `VRAM_CopySafe`: copies `BC` bytes from `DE` to `HL`, waiting out mode 3 for every write.
- `00:3058` `VRAM_CopySafeDouble`: copies `BC` source bytes and writes each byte twice.
- `00:3092/3093` `VRAM_WriteByteSafeFromA` / `VRAM_WriteByteSafe`: writes A/B to `[HL]` after mode 3.
- `00:30AD` `Tilemap_FillRectangle`: fills `B x C` cells at `HL` with tile `D`; destination rows have stride 32.
- `00:30BE` `Tilemap_FillIncrementingRectangle`: same shape, incrementing the tile ID per cell.
- `00:30E0` `Tilemap_CopyRectangle`: copies packed rows from `DE` into a tilemap rectangle at `HL`.
- `00:33B2` `Tilemap_Clear`: writes tile 0 to 1024 cells.

### MBC2 save representation

The MBC2 RAM enable/disable writes use `$00EF`, whose address bit 8 is clear as required by MBC2. MBC2 stores only a low nibble per address, so each logical byte is encoded in two cells. The first nibble is written after `swap`, and the second is the original low nibble.

- Slot 0 data starts at `$A004`; slot 1 at `$A102`.
- Each slot encodes 126 bytes from WRAM `$D8A8`, occupying 252 MBC2 cells.
- `$A002` stores a slot marker/status value.
- The checksum is the 8-bit sum of all 252 stored low nibbles.
- The read path decodes to `$D8A8` only if the stored checksum matches.

## Text rendering and ROM source data

The text path is now statically resolved far enough to identify where displayed message data comes from. It is a **bank-3 encoded text/tile stream**, not a raw glyph-bitmap upload.

### Message selection in bank 0

`00:329F` (`Text_ResolveMessageStream`) switches to bank 3 and performs two little-endian pointer lookups rooted at `03:4000` (ROM offset `$0C000`):

- For message IDs `$80-$FF`, root entry 0 selects table `03:4034`; entry `ID-$80` selects the stream.
- For message IDs `$00-$7F`, root entry `$D8C1+1` selects a context table; entry `ID` selects the stream.
- The resulting bank-3 CPU pointer is stored in `$C1A8/$C1A9`. `00:32C4` sets `$C1A0` and waits frame-by-frame until processing completes.

Confirmed examples are:

| Message selection | Pointer path | Encoded stream | ROM offset |
|---|---|---|---|
| ID `$84` | `03:4000 -> 03:4034`, entry 4 | `03:426E` | `$0C26E` |
| ID `$85` | `03:4000 -> 03:4034`, entry 5 | `03:4276` | `$0C276` |
| ID `$86` | `03:4000 -> 03:4034`, entry 6 | `03:427D` | `$0C27D` |
| Context `$D8C1=3`, ID `$02` | root entry 4 -> table `03:494D`, entry 2 | `03:49B9` | `$0C9B9` |
| Context `$D8C1=7`, ID `$02` | root entry 8 -> table `03:573F`, entry 2 | `03:5800` | `$0D800` |

For bank 3, convert CPU addresses to file offsets with `offset = $0C000 + (address - $4000)`. The pointer/table/stream data occupies `03:4000-$7BD6` (ROM `$0C000-$0FBD6`). It is now represented explicitly as a 26-entry `dw` root followed by byte-exact `db` stream data. `03:7BD7-$7DFF` (ROM `$0FBD7-$0FDFF`) is confirmed zero padding before the interpreter.

### VBlank stream interpreter

`03:7E00` (ROM offset `$0FE00`) is called directly by the fixed-bank VBlank handler while bank 3 is selected. It reads the stream pointer from `$C1A8/$C1A9` and writes tile IDs directly to the tilemap destination in `$C1A6/$C1A7`. This establishes that bank 3 supplies encoded character/control data; glyph pixels must already have been loaded into VRAM by another path.

Confirmed stream behavior includes:

- `$FE`: terminate the top-level stream, or return from a nested expansion saved in `$C1AF...`.
- `$FD`: advance/reposition the destination to the next tilemap row and apply line/page timing state.
- `$FB`: input-sensitive control handled using joypad state.
- Bytes below `$B0`: written directly as tile IDs.
- Ranges `$B0-$E1`: converted to tile IDs using bases `$56`, `$5B`, `$79`, `$7E`, `$42`, or `$74`; some ranges also write companion tiles one row above (`destination-$20`) with tile `$71` or `$72`.
- Extended bytes `$E2-$FF`, excluding recognized controls, can save the current stream pointer and follow a little-endian pointer indexed from `03:4000` by `token-$D8`. This is strong evidence for recursive dictionary/substring expansion, although not every possible token index is yet proven valid.

The primary font source is now confirmed at Bank 1, CPU `$5D3B-$6198` (ROM `$05D3B-$06198`). `FontTiles_Load` at `01:7B42` decompresses this resource through `$35CF` to exactly `$500` bytes: 160 packed 1bpp 8x8 glyphs. It then uses the byte-doubling VRAM copy at `$3058` to place the first `$400` bytes at VRAM `$9000-$97FF` (tile IDs `$00-$7F` in signed BG tile mode) and the final `$100` bytes at `$8800-$89FF` (tile IDs `$80-$9F`). Duplicating each source byte into both bitplanes produces two-color 2bpp tiles.

The exact text-glyph mapping is recorded in `projects/gb-db-z-gokou/analysis/font_tiles.tsv`, and the corresponding stream-byte mapping through `$E1` is recorded in `projects/gb-db-z-gokou/analysis/text_encoding.tsv`. The mapping was transcribed from the decompressed glyphs and checked against representative decoded messages — the save-confirmation, time-up, and "view instructions?" prompts at `03:426E`, `03:4276`, and `03:427D`. The raw Japanese for these prompts is kept only in the local decoded catalog. The regular ranges are hiragana `$01-$37`, katakana `$38-$6E`, punctuation/marks `$6F-$79`, digits `$80-$89`, Latin UI letters `$96-$9D`, and arrows `$9E/$9F`. Tiles `$7A-$7F` are blank. Tiles `$8A-$95` are multi-cell UI/meter graphics and are intentionally not assigned text characters. Direct stream bytes `$A0-$AF` remain unmapped because they address tile IDs outside this `$00-$9F` font upload and may refer to dynamically loaded graphics.

`$B0-$D7` encode voiced kana: the interpreter writes the calculated base kana in the current cell and dakuten tile `$71` one tilemap row above. `$D8-$E1` similarly encode semi-voiced kana with handakuten tile `$72`. The repository tool `gb-text-decode` reproduces direct characters, these composite kana, row controls, waits, and bounded recursive dictionary expansion. For example, `gb-text-decode roms/gb-db-z-gokou/original.gb --message-id 0x84` decodes the stream at `03:426E` as the save-confirmation message.

All 26 root entries and their inferred pointer tables are cataloged in `projects/gb-db-z-gokou/analysis/bank3_text_tables.tsv` (local; contains decoded Japanese). The committed script-free index is `projects/gb-db-z-gokou/analysis/bank3_text_reference_index.tsv`, and the full scene map and catalog methodology are documented in `projects/gb-db-z-gokou/analysis/bank_003_text.md`. The current ROM yields 479 table references to 419 unique decoded streams, with shared pointers deduplicated and runtime fragments explicitly flagged.

## Important unresolved work

- Name the top-level state fields `$D7C7/$D7C8/$D7E7` only after tracing their complete state domains.
- Split the large gameplay region `$0F45-$2D11` into stable routines and typed data records.
- Continue converting other confirmed table ranges to `db`/`dw` declarations in small byte-identical passes.
- Trace bank-1 routines around `$4099/$41E8/$41F2/$421C/$42E0` to identify the message/UI protocol.
- Continue cataloging message-table and stream boundaries using `gb-text-decode`; preserve unresolved dynamic tile IDs and control semantics explicitly.
- Finish documenting the `$35CF` compression format and the chained resource-descriptor behavior in `$3784`; the font resource provides a confirmed test vector.
- Verify the roles of the VBlank callbacks in banks 3 and 15.
