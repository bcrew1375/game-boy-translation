# Bank 15 audio driver and sequence data

## Confirmed range

Bank 15 `0F:4000-$7FFF` (ROM offsets `$3C000-$3FFFF`) is the game's audio
subsystem: executable driver code, hardware-register lookup data, sound pointer
tables, and the sequence streams selected by those tables.

The whole bank is classified as `audio` rather than forcing generated mgbdis
instruction boundaries onto sequence data that the driver interprets.

## Entry points

The first six bytes are two explicit jump veneers:

| Entry | Bytes | Target | Confirmed caller/use |
|---|---|---|---|
| `0F:4000` | `JP $4006` | command processor | `00:0339` selects Bank 15 and calls `$4000` with the requested sound command in `A`. |
| `0F:4003` | `JP $4222` | periodic update | The VBlank handler selects Bank 15 and calls `$4003` once per frame. |

`0F:4006` stores the command in WRAM `$C0A3`, preserves all general register
pairs, handles stop/control values, and indexes a little-endian pointer table at
`0F:4B42` for ordinary commands. Initialization writes the Game Boy sound
registers (`NR10` through `NR52`) and clears the driver's WRAM state.

`0F:4222` updates active channels, dispatches interpreted stream commands, and
returns a status byte from `$C0A4`. The implementation writes the square, wave,
noise, volume, and routing registers and maintains per-channel state in
`$C0A0-$C15F`.

## Driver/data boundary evidence

The driver code extends through the arithmetic/register helpers near `$4ABF`.
From `$4AC0` onward, generated disassembly increasingly represents lookup and
sequence bytes as instructions. In particular:

- `0F:40D2` indexes the little-endian table at `$4B42` and passes the selected
  address to the sequence initializer at `$4158`.
- The table contains in-bank addresses such as `$692D`, `$6952`, `$6981`, and
  later stream starts.
- Channel processing repeatedly reads bytes through stored `DE` pointers and
  interprets command ranges rather than executing those addresses as CPU code.
- The final ROM byte is nonzero, so there is no unsupported assumption of
  trailing free space or padding.

These relationships establish the entire bank as audio-owned while leaving
the exact command grammar and individual song/effect boundaries for a later
structured decoding pass.

## Remaining work

- Determine the exact length and command-ID domain of the `$4B42` pointer table.
- Decode the sequence bytecode and distinguish music, jingles, and sound
  effects without inventing titles.
- Map the per-channel WRAM structures and document each command opcode.
- Promote confirmed driver code, pointer tables, and individual streams to
  narrower manifest regions after their complete boundaries are known.