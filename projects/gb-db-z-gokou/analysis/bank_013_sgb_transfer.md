# Bank 13 Super Game Boy transfer data

## Confirmed range

Bank 13 `0D:4000-$6FFF` (ROM offsets `$34000-$36FFF`) contains three exact
4 KiB screen-transfer pages used by `00:0561`:

| Source range | ROM range | VRAM destination | Setup index | SGB command |
|---|---:|---:|---:|---|
| `0D:4000-$4FFF` | `$34000-$34FFF` | `$8800-$97FF` | `$04` | `PCT_TRN` |
| `0D:5000-$5FFF` | `$35000-$35FFF` | `$8800-$97FF` | `$05` | `PCT_TRN`, parameter `$01` |
| `0D:6000-$6FFF` | `$36000-$36FFF` | `$8800-$97FF` | `$06` | `CHR_TRN` |

For each page, `00:0561` selects Bank 13, copies exactly `$1000` bytes to VRAM
with `00:303C`, restores Bank 1, prepares the fixed command through `01:412D`,
and submits the transfer through `01:405C`. The command identities come from
the confirmed fixed-command templates at `01:4158-$4171`.

Each page is exactly 256 conventional 2bpp 8x8 tiles. Raw tile rendering
confirms graphics/tilemap-like content in the first two pages and character
tile content in the third. The range is therefore classified conservatively as
SGB border transfer data; narrower SNES-side tile, tilemap, palette, and
attribute boundaries remain deferred.

`0D:7000` begins unrelated data and is not included merely because it is
adjacent.

## Remaining work

- Determine how `00:0561` is reached at runtime and which border state it
  installs.
- Decode the SNES-side `PCT_TRN` and `CHR_TRN` payload structures without
  changing the established three-page transfer boundaries.