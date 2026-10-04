# Banks 04-05 graphics resource analysis

## Scope

This pass maps all 16,384 bytes of Bank 4 and Bank 5 CPU `$4000-$5992`
(6,547 bytes). Together these ranges add 22,931 uniquely classified ROM bytes.

The fixed-bank loader at `00:3784` masks the resource ID to seven bits and
looks it up in the 16-bit catalog at `04:4000`. IDs below `$28` use Bank 4;
IDs `$28` and above switch to Bank 5 before decompression. Direct catalog
entries are CPU pointers consumed by the LZ decoder at `00:35CF`.

Every direct stream in the mapped range decompresses to `$0230` bytes: 560
bytes, or 35 conventional 2bpp 8x8 tiles. This establishes the byte format and
extent without assigning speculative character, animation, or scene names to
the artwork.

The generated `mgbdis` project used for this pass rebuilt to the original
ROM's exact MD5 before the ranges were recorded.

## Bank 4 layout

| CPU range | ROM range | Size | Classification | Interpretation |
|---|---:|---:|---|---|
| `04:4000-$406F` | `$10000-$1006F` | 112 | Catalog | 56 little-endian entries for resource IDs `$00-$37`. |
| `04:4070-$407E` | `$10070-$1007E` | 15 | Data | Destination-block index lists used by all derived catalog entries. |
| `04:407F-$416E` | `$1007F-$1016E` | 240 | Graphics | 15 raw 2bpp auxiliary tiles used when constructing derived resources. Their precise visible roles remain unresolved. |
| `04:416F-$7E47` | `$1016F-$13E47` | 15,577 | Compressed graphics | 31 unique compressed streams serving IDs `$00-$27`. |
| `04:7E48-$7FFF` | `$13E48-$13FFF` | 440 | Padding | All zero bytes. |

The catalog, derived metadata, auxiliary tiles, compressed streams, and
padding form an exact, gap-free partition of Bank 4.

## Direct Bank 4 streams

Repeated IDs sharing one pointer intentionally share one stream. All sizes
include the 34-byte compression header.

| IDs | CPU range | ROM range | Compressed bytes | Output bytes |
|---|---|---:|---:|---:|
| `$00` | `04:416F-$434D` | `$1016F-$1034D` | 479 | 560 |
| `$01` | `04:434E-$450C` | `$1034E-$1050C` | 447 | 560 |
| `$02` | `04:450D-$46E8` | `$1050D-$106E8` | 476 | 560 |
| `$03` | `04:46E9-$48C8` | `$106E9-$108C8` | 480 | 560 |
| `$04` | `04:48C9-$4AA1` | `$108C9-$10AA1` | 473 | 560 |
| `$05` | `04:4AA2-$4CAC` | `$10AA2-$10CAC` | 523 | 560 |
| `$06` | `04:4CAD-$4E7A` | `$10CAD-$10E7A` | 462 | 560 |
| `$07` | `04:4E7B-$506A` | `$10E7B-$1106A` | 496 | 560 |
| `$08` | `04:506B-$5239` | `$1106B-$11239` | 463 | 560 |
| `$09` | `04:523A-$541D` | `$1123A-$1141D` | 484 | 560 |
| `$0A` | `04:541E-$5621` | `$1141E-$11621` | 516 | 560 |
| `$0C` | `04:5622-$5806` | `$11622-$11806` | 485 | 560 |
| `$0D` | `04:5807-$5A0F` | `$11807-$11A0F` | 521 | 560 |
| `$0E` | `04:5A10-$5C34` | `$11A10-$11C34` | 549 | 560 |
| `$10` | `04:5C35-$5E57` | `$11C35-$11E57` | 547 | 560 |
| `$11` | `04:5E58-$6062` | `$11E58-$12062` | 523 | 560 |
| `$12` | `04:6063-$6254` | `$12063-$12254` | 498 | 560 |
| `$14` | `04:6255-$6476` | `$12255-$12476` | 546 | 560 |
| `$15` | `04:6477-$6675` | `$12477-$12675` | 511 | 560 |
| `$16` | `04:6676-$6862` | `$12676-$12862` | 493 | 560 |
| `$17` | `04:6863-$6A70` | `$12863-$12A70` | 526 | 560 |
| `$19` | `04:6A71-$6C48` | `$12A71-$12C48` | 472 | 560 |
| `$1A` | `04:6C49-$6E35` | `$12C49-$12E35` | 493 | 560 |
| `$1B` | `04:6E36-$6FE3` | `$12E36-$12FE3` | 430 | 560 |
| `$1C-$20` | `04:6FE4-$71D0` | `$12FE4-$131D0` | 493 | 560 |
| `$21` | `04:71D1-$73E4` | `$131D1-$133E4` | 532 | 560 |
| `$22` | `04:73E5-$75D0` | `$133E5-$135D0` | 492 | 560 |
| `$23` | `04:75D1-$7787` | `$135D1-$13787` | 439 | 560 |
| `$25` | `04:7788-$79BD` | `$13788-$139BD` | 566 | 560 |
| `$26` | `04:79BE-$7BF5` | `$139BE-$13BF5` | 568 | 560 |
| `$27` | `04:7BF6-$7E47` | `$13BF6-$13E47` | 594 | 560 |

## Derived resource entries

A catalog value below `$4000` is not a ROM pointer. Its high byte is a count
of 16-byte tile blocks and its low byte is an offset into both the destination
index list at `04:4070` and the 15 raw source tiles at `04:407F`. The loader
retains the preceding direct stream as the base resource, then copies each
sequential raw source tile to the listed 16-byte destination block within that
560-byte decompressed base.

| ID | Catalog value | Index-list bytes | Destination block indices |
|---|---:|---:|---|
| `$0B` | `$0100` | `04:4070` | `$11` |
| `$0F` | `$0201` | `04:4071-$4072` | `$11,$16` |
| `$13` | `$0603` | `04:4073-$4078` | `$10,$11,$12,$15,$16,$17` |
| `$18` | `$0209` | `04:4079-$407A` | `$16,$1B` |
| `$24` | `$010B` | `04:407B` | `$10` |
| `$2D` | `$010C` | `04:407C` | `$16` |
| `$31` | `$020D` | `04:407D-$407E` | `$15,$1A` |

Every byte of the 15-byte list is consumed by exactly one of these records.

## Bank 5 streams

Bank 5 CPU `$4000-$5992` is an exact, contiguous sequence of 13 unique
compressed streams serving resource IDs `$28-$37`. IDs `$2E/$2F` share one
stream; `$2D` and `$31` are derived entries described above.

| IDs | CPU range | ROM range | Compressed bytes | Output bytes |
|---|---|---:|---:|---:|
| `$28` | `05:4000-$4205` | `$14000-$14205` | 518 | 560 |
| `$29` | `05:4206-$43BC` | `$14206-$143BC` | 439 | 560 |
| `$2A` | `05:43BD-$4593` | `$143BD-$14593` | 471 | 560 |
| `$2B` | `05:4594-$47D3` | `$14594-$147D3` | 576 | 560 |
| `$2C` | `05:47D4-$498B` | `$147D4-$1498B` | 440 | 560 |
| `$2E/$2F` | `05:498C-$4BA3` | `$1498C-$14BA3` | 536 | 560 |
| `$30` | `05:4BA4-$4D85` | `$14BA4-$14D85` | 482 | 560 |
| `$32` | `05:4D86-$4F75` | `$14D86-$14F75` | 496 | 560 |
| `$33` | `05:4F76-$517D` | `$14F76-$1517D` | 520 | 560 |
| `$34` | `05:517E-$5364` | `$1517E-$15364` | 487 | 560 |
| `$35` | `05:5365-$5584` | `$15365-$15584` | 544 | 560 |
| `$36` | `05:5585-$579B` | `$15585-$1579B` | 535 | 560 |
| `$37` | `05:579C-$5992` | `$1579C-$15992` | 503 | 560 |

## Loader and placement metadata

`GraphicsResource_LoadAndPlace` at `00:3879` reads three-byte placement/shape
descriptors from Bank 6 at `06:4018 + ID * 3`. It selects a resource bank,
decompresses through `00:35CF`, copies the resulting tiles into VRAM, derives
width and height from the descriptor, and combines the resource with the SGB
presentation path documented for Bank 1.

Descriptor shape bytes with bit 7 set redirect through their low five bits to
another Bank 6 descriptor for dimensions. The low nibble is width; the high
nibble plus six is height. These mechanics are confirmed, but the visual name
of each individual resource remains deliberately unresolved pending runtime
screen identification.

## Remaining work

- Identify the visible character, animation, or scene associated with each ID
  using runtime traces rather than visual guessing.
- Map Bank 5 after `05:5992`; code is confirmed at several fixed-bank entry
  points from `05:5CAE` onward, but mixed code and embedded tables need a
  separate control-flow pass.
- Continue the Bank 6-8 large-resource mapping beyond the ranges documented in
  `projects/gb-db-z-gokou/analysis/banks_006_008_graphics.md`.