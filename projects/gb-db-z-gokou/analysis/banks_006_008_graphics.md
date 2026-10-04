# Banks 06-08 large graphics resource analysis

## Scope

This document now covers 48,533 unique bytes across three analysis operations.
The latest operation added 22,079 bytes by completing Bank 7 and all of Bank
8. The cumulative ranges are:

- Bank 6 `06:4000-$4017`: eight shape-alias descriptor records (24 bytes).
- Bank 6 `06:4018-$4197`: 128 source-pointer/shape records (384 bytes).
- Bank 6 `06:4403-$7EF1`: 18 unique compressed graphics streams (15,087 bytes).
- Bank 6 `06:7EF2-$7FFF`: zero padding (270 bytes).
- Bank 7 `07:4000-$7F4D`: 19 unique compressed graphics streams (16,206 bytes).
- Bank 7 `07:7F4E-$7FFF`: zero padding (178 bytes).
- Bank 8 `08:4000-$7FD0`: 30 unique compressed graphics streams (16,337 bytes).
- Bank 8 `08:7FD1-$7FFF`: zero padding (47 bytes).

Bank 6 `06:4198-$4402` remains intentionally unclassified. It is visibly
structured non-code data, but its consumers and exact internal boundaries have
not yet been established.

## Fixed-bank loader evidence

`GraphicsResource_LoadAndPlace` at `00:3879` masks the resource ID to seven
bits. The seven threshold bytes at `00:3974-$397A` are:

```text
$14, $28, $46, $60, $76, $8F, $FF
```

The loader begins with source bank 5 and increments the bank once for every
threshold that is less than or equal to the ID. For the reachable IDs
`$00-$7F`, this produces these source partitions:

| IDs | Source bank | Count |
|---|---:|---:|
| `$00-$13` | 6 | 20 |
| `$14-$27` | 7 | 20 |
| `$28-$45` | 8 | 30 |
| `$46-$5F` | 9 | 26 |
| `$60-$75` | 10 | 22 |
| `$76-$7F` | 11 | 10 |

After selecting a source bank, the loader indexes `06:4018 + ID * 3`. Each
three-byte descriptor consists of a little-endian compressed-stream CPU
pointer followed by a shape byte.

## Shape descriptors

For ordinary shape bytes, the low nibble is the placement width and the high
nibble plus six is the placement height:

```text
width = shape & $0F
height = (shape >> 4) + 6
```

When bit 7 is set, the low five bits select one of the three-byte records at
`06:4000`; the loader uses the selected record's first byte as the effective
shape. The other two bytes in each prefix record are pointer-like and remain
semantically unresolved, so this pass does not assign them a stronger name.

The eight prefix records are:

| Alias index | Effective shape | Remaining word |
|---:|---:|---:|
| 0 | `$27` | `$41FB` |
| 1 | `$27` | `$4233` |
| 2 | `$2C` | `$426B` |
| 3 | `$27` | `$42CB` |
| 4 | `$0A` | `$4303` |
| 5 | `$2C` | `$4343` |
| 6 | `$2C` | `$43A3` |
| 7 | `$00` | `$0000` |

The complete 128-entry table occupies exactly `06:4018-$4197`. Its source
pointers reset to `$4000` at IDs `$14`, `$28`, `$46`, `$60`, and `$76`, exactly
where the fixed-bank threshold logic advances to the next source bank.

## Bank 6 compressed streams

IDs `$09/$0A` share one stream and use shape aliases 0 and 1. IDs `$11/$12`
share another stream and use aliases 2 and 3. All other IDs in this partition
have unique pointers.

| IDs | CPU range | ROM range | Compressed | Output | Effective shape | Dimensions |
|---|---|---:|---:|---:|---:|---:|
| `$00` | `06:4403-$461B` | `$18403-$1861B` | 537 | 960 | `$0A` | 10x6 |
| `$01` | `06:461C-$48B0` | `$1861C-$188B0` | 661 | 768 | `$26` | 6x8 |
| `$02` | `06:48B1-$4B92` | `$188B1-$18B92` | 738 | 896 | `$18` | 8x7 |
| `$03` | `06:4B93-$4DF9` | `$18B93-$18DF9` | 615 | 768 | `$26` | 6x8 |
| `$04` | `06:4DFA-$50EA` | `$18DFA-$190EA` | 753 | 768 | `$08` | 8x6 |
| `$05` | `06:50EB-$5386` | `$190EB-$19386` | 668 | 768 | `$26` | 6x8 |
| `$06` | `06:5387-$56EB` | `$19387-$196EB` | 869 | 896 | `$18` | 8x7 |
| `$07` | `06:56EC-$5A45` | `$196EC-$19A45` | 858 | 896 | `$27` | 7x8 |
| `$08` | `06:5A46-$5DB9` | `$19A46-$19DB9` | 884 | 896 | `$27` | 7x8 |
| `$09/$0A` | `06:5DBA-$5F48` | `$19DBA-$19F48` | 399 | 448 | alias 0/1 -> `$27` | 7x8 |
| `$0B` | `06:5F49-$6264` | `$19F49-$1A264` | 796 | 1,024 | `$28` | 8x8 |
| `$0C` | `06:6265-$6771` | `$1A265-$1A771` | 1,293 | 1,920 | `$4C` | 12x10 |
| `$0D` | `06:6772-$6D42` | `$1A772-$1AD42` | 1,489 | 1,536 | `$2C` | 12x8 |
| `$0E` | `06:6D43-$71DF` | `$1AD43-$1B1DF` | 1,181 | 1,536 | `$2C` | 12x8 |
| `$0F` | `06:71E0-$73F6` | `$1B1E0-$1B3F6` | 535 | 576 | `$06` | 6x6 |
| `$10` | `06:73F7-$764B` | `$1B3F7-$1B64B` | 597 | 576 | `$06` | 6x6 |
| `$11/$12` | `06:764C-$7A01` | `$1B64C-$1BA01` | 950 | 1,536 | alias 2/3 -> `$2C/$27` | 12x8 / 7x8 |
| `$13` | `06:7A02-$7EF1` | `$1BA02-$1BEF1` | 1,264 | 1,536 | `$2C` | 12x8 |

Shape dimensions control later tilemap placement and SGB attribute-map record
selection; they do not universally equal decompressed graphics size. The
clearest counterexample is the shared `$09/$0A` stream, which expands to 448
bytes while both aliases describe a 7x8 placement rectangle. The shared
`$11/$12` stream expands to 1,536 bytes while its aliases select 12x8 and 7x8
placement shapes. The exact transformation from source tiles to every placed
rectangle remains unresolved.

Every unique stream begins immediately after the previous stream ends. The
final stream ends at `06:7EF1`, and `06:7EF2-$7FFF` contains 270 zero bytes.

## Bank 7 streams

The preceding pass mapped the first 11 streams in Bank 7, corresponding to IDs
`$14-$1E`. The continuation below completes the bank through ID `$27` and its
trailing zero padding.

| ID | CPU range | ROM range | Compressed | Output | Shape | Dimensions |
|---|---|---:|---:|---:|---:|---:|
| `$14` | `07:4000-$429A` | `$1C000-$1C29A` | 667 | 768 | `$08` | 8x6 |
| `$15` | `07:429B-$4735` | `$1C29B-$1C735` | 1,179 | 1,536 | `$2C` | 12x8 |
| `$16` | `07:4736-$4BDD` | `$1C736-$1CBDD` | 1,192 | 1,536 | `$2C` | 12x8 |
| `$17` | `07:4BDE-$4E7A` | `$1CBDE-$1CE7A` | 669 | 1,152 | `$29` | 9x8 |
| `$18` | `07:4E7B-$52C7` | `$1CE7B-$1D2C7` | 1,101 | 1,536 | `$2C` | 12x8 |
| `$19` | `07:52C8-$5730` | `$1D2C8-$1D730` | 1,129 | 1,536 | `$2C` | 12x8 |
| `$1A` | `07:5731-$593D` | `$1D731-$1D93D` | 525 | 576 | `$06` | 6x6 |
| `$1B` | `07:593E-$5D5C` | `$1D93E-$1DD5C` | 1,055 | 1,536 | `$2C` | 12x8 |
| `$1C` | `07:5D5D-$610E` | `$1DD5D-$1E10E` | 946 | 1,152 | `$29` | 9x8 |
| `$1D` | `07:610F-$66C1` | `$1E10F-$1E6C1` | 1,459 | 1,536 | `$2C` | 12x8 |
| `$1E` | `07:66C2-$69C0` | `$1E6C2-$1E9C0` | 767 | 960 | `$0A` | 10x6 |

| IDs | CPU range | ROM range | Compressed | Output | Effective shape | Dimensions |
|---|---|---:|---:|---:|---:|---:|
| `$1F` | `07:69C1-$6A1C` | `$1E9C1-$1EA1C` | 92 | 144 | alias 4 -> `$0A` | 10x6 |
| `$20` | `07:6A1D-$6BAA` | `$1EA1D-$1EBAA` | 398 | 768 | `$08` | 8x6 |
| `$21` | `07:6BAB-$6EC1` | `$1EBAB-$1EEC1` | 791 | 1,024 | `$28` | 8x8 |
| `$22` | `07:6EC2-$7220` | `$1EEC2-$1F220` | 863 | 1,024 | `$28` | 8x8 |
| `$23` | `07:7221-$7464` | `$1F221-$1F464` | 580 | 768 | `$26` | 6x8 |
| `$24` | `07:7465-$7778` | `$1F465-$1F778` | 788 | 1,024 | `$28` | 8x8 |
| `$25` | `07:7779-$7AC1` | `$1F779-$1FAC1` | 841 | 1,152 | `$29` | 9x8 |
| `$26/$27` | `07:7AC2-$7F4D` | `$1FAC2-$1FF4D` | 1,164 | 1,536 | aliases 5/6 -> `$2C` | 12x8 |

All Bank 7 streams from `07:4000-$7F4D` are contiguous. IDs `$26/$27`
share the final stream. Bank 7 ends with 178 zero bytes at
`07:7F4E-$7FFF`.

## Bank 8 streams

Bank 8 is an exact partition of 30 unique compressed streams followed by 47
zero bytes. IDs `$28-$35` and `$3F-$45` expand to 768 bytes. IDs `$36-$3E`
expand to 560 bytes and all use placement shape `$15`.

| ID | CPU range | ROM range | Compressed | Output | Shape | Dimensions |
|---|---|---:|---:|---:|---:|---:|
| `$28` | `08:4000-$4255` | `$20000-$20255` | 598 | 768 | `$08` | 8x6 |
| `$29` | `08:4256-$44A7` | `$20256-$204A7` | 594 | 768 | `$08` | 8x6 |
| `$2A` | `08:44A8-$478C` | `$204A8-$2078C` | 741 | 768 | `$08` | 8x6 |
| `$2B` | `08:478D-$4988` | `$2078D-$20988` | 508 | 768 | `$08` | 8x6 |
| `$2C` | `08:4989-$4C74` | `$20989-$20C74` | 748 | 768 | `$08` | 8x6 |
| `$2D` | `08:4C75-$4F1A` | `$20C75-$20F1A` | 678 | 768 | `$08` | 8x6 |
| `$2E` | `08:4F1B-$51D4` | `$20F1B-$211D4` | 698 | 768 | `$08` | 8x6 |
| `$2F` | `08:51D5-$5449` | `$211D5-$21449` | 629 | 768 | `$08` | 8x6 |
| `$30` | `08:544A-$5755` | `$2144A-$21755` | 780 | 768 | `$08` | 8x6 |
| `$31` | `08:5756-$5A69` | `$21756-$21A69` | 788 | 768 | `$08` | 8x6 |
| `$32` | `08:5A6A-$5D2C` | `$21A6A-$21D2C` | 707 | 768 | `$08` | 8x6 |
| `$33` | `08:5D2D-$5F19` | `$21D2D-$21F19` | 493 | 768 | `$08` | 8x6 |
| `$34` | `08:5F1A-$619A` | `$21F1A-$2219A` | 641 | 768 | `$08` | 8x6 |
| `$35` | `08:619B-$6430` | `$2219B-$22430` | 662 | 768 | `$08` | 8x6 |
| `$36` | `08:6431-$652F` | `$22431-$2252F` | 255 | 560 | `$15` | 5x7 |
| `$37` | `08:6530-$667A` | `$22530-$2267A` | 331 | 560 | `$15` | 5x7 |
| `$38` | `08:667B-$6787` | `$2267B-$22787` | 269 | 560 | `$15` | 5x7 |
| `$39` | `08:6788-$68FE` | `$22788-$228FE` | 375 | 560 | `$15` | 5x7 |
| `$3A` | `08:68FF-$6B1B` | `$228FF-$22B1B` | 541 | 560 | `$15` | 5x7 |
| `$3B` | `08:6B1C-$6C7D` | `$22B1C-$22C7D` | 354 | 560 | `$15` | 5x7 |
| `$3C` | `08:6C7E-$6DED` | `$22C7E-$22DED` | 368 | 560 | `$15` | 5x7 |
| `$3D` | `08:6DEE-$6F21` | `$22DEE-$22F21` | 308 | 560 | `$15` | 5x7 |
| `$3E` | `08:6F22-$7082` | `$22F22-$23082` | 353 | 560 | `$15` | 5x7 |
| `$3F` | `08:7083-$72AE` | `$23083-$232AE` | 556 | 768 | `$08` | 8x6 |
| `$40` | `08:72AF-$74E8` | `$232AF-$234E8` | 570 | 768 | `$08` | 8x6 |
| `$41` | `08:74E9-$7671` | `$234E9-$23671` | 393 | 768 | `$08` | 8x6 |
| `$42` | `08:7672-$7891` | `$23672-$23891` | 544 | 768 | `$08` | 8x6 |
| `$43` | `08:7892-$7B3A` | `$23892-$23B3A` | 681 | 768 | `$08` | 8x6 |
| `$44` | `08:7B3B-$7D64` | `$23B3B-$23D64` | 554 | 768 | `$08` | 8x6 |
| `$45` | `08:7D65-$7FD0` | `$23D65-$23FD0` | 620 | 768 | `$08` | 8x6 |

The final stream ends at `08:7FD0`; `08:7FD1-$7FFF` contains 47 zero bytes.

## Remaining work

- Identify the unresolved structured records at `06:4198-$4402` from their
  consumers before assigning a data type.
- Map the complete contiguous stream families in Banks 9-11 from the same
  descriptor table.
- Identify visible resource roles through runtime traces rather than artwork
  guesses.