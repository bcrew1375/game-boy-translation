# Bank 01 analysis and documentation

Bank 1 occupies CPU `$4000-$7FFF` and ROM offsets `$04000-$07FFF`. This
document records the current focused mapping over the bank. The pass covers
the Super Game Boy transport and presentation helpers at `01:4000-$43AB`, the
packet block they use at `01:43AC-$442B`, the 4 KiB `PAL_TRN` image at
`01:442C-$542B`, and the already-confirmed compressed font at
`01:5D3B-$6198`.

The source used for this analysis was generated with the repository's
`gb-disassemble` wrapper. The generated RGBDS project rebuilt to the exact
SHA-256 of the supplied original ROM before conclusions were recorded.

## Confidence terms

- **Confirmed**: established directly from instructions, packet contents,
  callers, or exact data flow.
- **Strong inference**: mechanics are established, but a complete visual or
  game-state interpretation still needs runtime confirmation.
- **Unknown data**: bytes are demonstrably consumed as data, but their complete
  format or visible role has not been established.

## Mapped ranges

| CPU range | ROM range | Classification | Current interpretation | Confidence |
|---|---:|---|---|---|
| `01:4000-$4047` | `$04000-$04047` | Code | Sends one or more 16-byte SGB packets through `rP1`. The low three bits of the first byte select the packet count. | Confirmed |
| `01:4048-$4098` | `$04048-$04098` | Code | Stages a screen transfer through VRAM/tilemap state, temporarily changes LCD/interrupt shadows, sends a prepared SGB packet, and restores the previous state. | Confirmed mechanics; transfer purpose depends on caller |
| `01:4099-$4118` | `$04099-$04118` | Code | Prepares the SGB transfer screen and contains the SGB presence/controller-response probe used by presentation setup. | Strong inference |
| `01:4119-$4157` | `$04119-$04157` | Code | Builds fixed SGB command packets in WRAM and submits them with frame delays; `01:4150` combines command setup with a VRAM transfer. | Confirmed |
| `01:4158-$4171` | `$04158-$04171` | Data | Offset table and command-byte templates for fixed one-packet SGB commands. | Confirmed |
| `01:4172-$41B1` | `$04172-$041B1` | Code | SGB initialization: waits after startup, sends mask/control commands, sends eight fixed initialization packets, transfers supporting screen data, and marks SGB setup complete. | Confirmed mechanics; exact purpose of every fixed packet remains partly unresolved |
| `01:41B2-$41F1` | `$041B2-$041F1` | Code | Builds and sends the 16-byte presentation packet at `$D725-$D734`, including final mask/control transitions. | Confirmed |
| `01:41F2-$42DF` | `$041F2-$042DF` | Code | Applies rectangular two-bit SGB attribute-map records to a 20x18 work buffer, optionally remaps values, and repacks 360 cells into 90 bytes. | Confirmed |
| `01:42E0-$430A` | `$042E0-$0430A` | Code | Clears the three presentation work buffers and provides a combined clear/setup/finalize path. | Confirmed |
| `01:430B-$434B` | `$0430B-$0434B` | Code | Selects a three-byte SGB `SOUND` payload, suppresses effects while another timed SGB operation is active, and sends the packet. | Confirmed |
| `01:434C-$43AB` | `$0434C-$043AB` | Data | 32 three-byte SGB sound-effect records indexed by `01:430B`. | Confirmed |
| `01:43AC-$442B` | `$043AC-$0442B` | Data | Eight consecutive 16-byte SGB initialization packets sent by `01:4172`. | Confirmed structure; individual packet purposes partial |
| `01:442C-$471A` | `$0442C-$0471A` | SGB transfer data | Prefix of the 4 KiB image copied to VRAM and submitted with `PAL_TRN`; no narrower CPU-side structure is yet assigned. | Confirmed transfer extent; internal roles partial |
| `01:471B-$4753` | `$0471B-$04753` | Data | 57-entry ID-to-pattern index map used by fixed-bank presentation code. | Confirmed |
| `01:4754-$490B` | `$04754-$0490B` | Data | 44 fixed ten-byte records: one returned value and nine packed bytes describing a 5x7 two-bit pattern. | Confirmed |
| `01:490C-$491F` | `$0490C-$0491F` | Data | Small presentation-selection/value tables. | Confirmed data; individual fields partial |
| `01:4920-$496B` | `$04920-$0496B` | Pointer table | 38 little-endian pointers into `01:4970-$4C08`. | Confirmed |
| `01:496C-$496F` | `$0496C-$0496F` | Unknown data | Four bytes between the pointer table and its first target. | Confirmed bytes; purpose unknown |
| `01:4970-$4C4C` | `$04970-$04C4C` | Data | Variable presentation records selected through the pointer table at `01:4920`. | Confirmed data use; formats partial |
| `01:4C4D-$4E64` | `$04C4D-$04E64` | Data | 20 contiguous SGB attribute-map rectangle records using packed or repeated-fill forms. | Confirmed |
| `01:4E65-$542B` | `$04E65-$0542B` | SGB transfer data | Remainder of the 4 KiB `PAL_TRN` image; narrower CPU-side structures remain unresolved. | Confirmed transfer extent; internal roles partial |
| `01:5D3B-$6198` | `$05D3B-$06198` | Compressed graphics | Primary 160-glyph packed 1bpp font resource. | Confirmed |

## SGB packet transport

`SGB_SendPackets` at `01:4000` accepts `HL` pointing to packet data. It reads
the low three bits of the first packet byte as the number of 16-byte packets,
then transmits each bit through `rP1` while interrupts are disabled. A zero
packet count returns immediately. Between packets it waits until the prior SGB
delay tracked at HRAM `$FFB5` has expired.

The bit transport is directly visible:

1. write `$00` then `$30` to begin/reset the transfer;
2. send each source bit as `$10` or `$20`, followed by `$30`;
3. repeat for 16 bytes per packet;
4. finish with `$20`, `$30` and a four-frame delay.

This matches the standard SGB packet framing protocol rather than ordinary
joypad input.

## Fixed command templates

`01:412D` uses the offset table at `01:4158` to copy a command byte and optional
parameter byte into the 16-byte packet buffer at `$D735`; the rest of the
packet is cleared. The command bytes identify these standard one-packet SGB
commands:

| Setup index | First byte | Command | Fixed parameter when present |
|---:|---:|---|---:|
| `$00` | `$B9` | `MASK_EN` | `$01` |
| `$01` | `$B9` | `MASK_EN` | supplied later |
| `$02` | `$59` | `PAL_TRN` | — |
| `$03` | `$A9` | `ATTR_TRN` | — |
| `$04` | `$99` | `PCT_TRN` | — |
| `$05` | `$99` | `PCT_TRN` | `$01` |
| `$06` | `$A1` | `CHR_TRN` | — |
| `$07` | `$49` | `SOU_TRN` | — |
| `$08` | `$41` | `SOUND` | — |
| `$09` | `$89` | `MLT_REQ` | — |
| `$0A` | `$89` | `MLT_REQ` | `$01` |

The low bit is the one-packet count; the upper five bits are the command ID.
This table confirms that the surrounding routines are SGB support code and not
generic Game Boy serial or joypad routines.

## Initialization

`SGB_Initialize` at `01:4172` is called during startup from `00:01AF` after
Bank 1 is selected. It:

1. marks SGB setup in progress in `$D7C6`;
2. waits 120 frames;
3. submits setup index `$00` (`MASK_EN` with parameter `$01`);
4. sends eight 16-byte packets from `01:43AC-$442B`, with four-frame gaps;
5. submits setup index `$02` (`PAL_TRN`) while transferring screen data that
   begins at `01:442C`;
6. clears the visible tilemap and sends the packet prepared at `$D725`;
7. stores `$02` in `$D7C6` to mark completion.

The eight fixed packet boundaries and the `PAL_TRN` command are confirmed.
Their complete SNES-side bootstrap meaning is not yet assigned because the
payloads are opaque program/data packets rather than ordinary high-level SGB
commands.

## PAL_TRN image and attribute-map records

Initialization copies exactly `$1000` bytes from `01:442C-$542B` to VRAM and
then submits setup index `$02`, the standard SGB `PAL_TRN` command. The range is
therefore a confirmed SGB palette-transfer image. The CPU also reuses selected
bytes inside that image as lookup tables and attribute-map records; those
nested interpretations do not change its transfer-time role.

`SGBAttributeMap_ApplyRectangle` at `01:41F2` consumes a four-byte header from
`HL`:

- byte 0 is the rectangle width;
- byte 1 low seven bits are the rectangle height;
- byte 1 bit 7 selects the repeated-fill form;
- bytes 2-3 are a little-endian destination offset into the 20x18 buffer.

For an ordinary record, the header is followed by
`ceil(width * height / 4)` bytes, with four two-bit attribute values packed into
each byte. A repeated-fill record instead contains one packed byte that is
expanded over the requested rectangle. The decoded values are written to
`$C6C5` with a 20-byte row stride. Two optional transforms remap nonzero
attribute values before the complete 360-cell map is repacked into 90 bytes at
`$D6C5`.

The 360-cell and 90-byte sizes exactly match the standard SGB 20x18 attribute
map. Record boundaries from `01:4C4D` through `01:4E64` are validated by this
format; the following bytes do not form a valid rectangle header.

`PresentationBuffers_Clear` at `01:42E0` clears:

- `$C6C5-$C82C`: 360-byte unpacked pixel/attribute buffer;
- `$C82D-$C894`: 104-byte intermediate buffer;
- `$D6C5-$D71E`: 90-byte packed output buffer.

### Pattern and record tables inside the transfer image

`01:471B-$4753` is a 57-byte index map. Fixed-bank code masks an input ID to
seven bits, reads one table byte, multiplies it by ten, and selects a record at
`01:4754`. The map uses all record indices `$00-$2B`.

`01:4754-$490B` contains 44 fixed ten-byte records. The first byte is returned
to the fixed-bank caller. The remaining nine bytes are passed to the attribute
map decoder as a 5x7 packed pattern because `ceil(5 * 7 / 4) = 9`.

`01:4920-$496B` contains 38 little-endian pointers. Every pointer targets the
variable presentation-data area at `01:4970-$4C4C`; fixed-bank code selects
these pointers for another family of dynamically positioned attribute-map
records. Their complete higher-level format remains unresolved.

The contiguous rectangle records at `01:4C4D-$4E64` include repeated-fill
rectangles, partial packed rectangles, and several complete 20x18 maps. Known
callers combine these records to colorize different UI and gameplay screens.
Visible screen names remain deferred until runtime confirmation.

## SGB sound effects

`SGB_PlaySoundEffect` at `01:430B` indexes the 32 records at
`01:434C-$43AB`. It copies a selected three-byte record into `$D736-$D738`
after preparing setup index `$08`, whose first byte is the standard SGB
`SOUND` command `$41`. A record beginning with `$FF` is treated as unavailable.
The routine also avoids starting an effect while the SGB delay at `$FFB5` or
the timer at `$D7FA/$D7FB` is active.

## Known callers

The fixed bank invokes the mapped subsystem from several distinct contexts:

- startup calls `01:4172` and then loads the primary font at `01:7B42`;
- `00:0F3F`, `00:2C71`, `00:2CD5`, `00:2CEE`, `00:3F6A`, and `00:3F8A`
  prepare presentation buffers, apply one or more Bank 1 rectangle records, transfer
  the result, and finalize the SGB state;
- `00:3A00` uses the same record and transfer path for a dynamically chosen
  record;
- Bank 14 calls `01:4172` again during its own setup path;
- `00:02FE` calls `01:430B` to request an SGB sound effect.

These callers establish reuse across startup, UI, and gameplay. Exact visible
screen names are intentionally not assigned yet.

## Remaining Bank 1 work

- Resolve the narrower formats of `01:442C-$471A`, `01:490C-$491F`,
  `01:496C-$496F`, `01:4970-$4C4C`, and `01:4E65-$542B` without losing their
  shared `PAL_TRN`-image role.
- Determine the higher-level format selected by the pointer table at
  `01:4920` and how its records feed dynamically positioned rectangles.
- Confirm the two attribute-value remapping modes with runtime watchpoints on
  `$C6C5`, `$C82D`, and `$D6C5`.
- Identify the visual destinations of each fixed-bank presentation caller.
- Continue mapping the large mixed code/data area between the presentation
  records and the compressed font.
- Map the code after the font, including the confirmed font loader at
  `01:7B42`.