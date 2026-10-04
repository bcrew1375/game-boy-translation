# Banks 06-12 large graphics resource analysis

## Scope

This document now covers 114,688 unique bytes across six analysis operations.
The latest operation added all 16,384 bytes of Bank 12. The cumulative ranges
are:

- Bank 6 `06:4000-$4017`: eight shape-alias descriptor records (24 bytes).
- Bank 6 `06:4018-$4197`: 128 source-pointer/shape records (384 bytes).
- Bank 6 `06:4198-$41FA`: 33 secondary source-pointer/shape records (99 bytes).
- Bank 6 `06:41FB-$4402`: seven alias-selected tile-index layout records (520 bytes).
- Bank 6 `06:4403-$7EF1`: 18 unique compressed graphics streams (15,087 bytes).
- Bank 6 `06:7EF2-$7FFF`: zero padding (270 bytes).
- Bank 7 `07:4000-$7F4D`: 19 unique compressed graphics streams (16,206 bytes).
- Bank 7 `07:7F4E-$7FFF`: zero padding (178 bytes).
- Bank 8 `08:4000-$7FD0`: 30 unique compressed graphics streams (16,337 bytes).
- Bank 8 `08:7FD1-$7FFF`: zero padding (47 bytes).
- Bank 9 `09:4000-$7D98`: 26 compressed graphics streams (15,769 bytes).
- Bank 9 `09:7D99-$7FFF`: zero padding (615 bytes).
- Bank 10 `0A:4000-$5DED`: 12 compressed graphics streams (7,662 bytes).
- Bank 10 `0A:5DEE-$7E70`: 10 compressed graphics streams (8,323 bytes).
- Bank 10 `0A:7E71-$7FFF`: zero padding (399 bytes).
- Bank 11 `0B:4000-$58D5`: 10 primary compressed graphics streams (6,358 bytes).
- Bank 11 `0B:58D6-$7DCF`: 15 secondary compressed graphics streams (9,466 bytes).
- Bank 11 `0B:7DD0-$7FFF`: zero padding (560 bytes).
- Bank 12 `0C:4000-$6E20`: 18 secondary compressed graphics streams (11,809 bytes).
- Bank 12 `0C:6E21-$7FFF`: zero padding (4,575 bytes).

## Secondary descriptors and alias layouts

The 33 records at `06:4198-$41FA` use the same three-byte pointer/shape format
as the primary table. All use shape `$08`. The first 15 pointers identify the
secondary Bank 11 streams at `0B:58D6-$7DCF`; the remaining 18 identify a
contiguous Bank 12 family at `0C:4000-$6E20`.

The non-null words in the eight prefix records at `06:4000-$4017` point to
seven exact records at `06:41FB-$4402`. Six records contain one tile index per
placement cell: three 7x8 records of 56 bytes and three 12x8 records of 96 bytes.
The 10x6 record at `06:4303-$4342` contains 60 tile indices followed by the
four-byte trailer `$FF,$FF,$78,$FF`, whose purpose remains unresolved.

| Alias | Shape | Layout range | Size | Interpretation |
|---:|---:|---|---:|---|
| 0 | `$27` | `06:41FB-$4232` | 56 | 7x8 tile-index layout |
| 1 | `$27` | `06:4233-$426A` | 56 | 7x8 tile-index layout |
| 2 | `$2C` | `06:426B-$42CA` | 96 | 12x8 tile-index layout |
| 3 | `$27` | `06:42CB-$4302` | 56 | 7x8 tile-index layout |
| 4 | `$0A` | `06:4303-$4342` | 64 | 10x6 layout plus four-byte trailer |
| 5 | `$2C` | `06:4343-$43A2` | 96 | 12x8 tile-index layout |
| 6 | `$2C` | `06:43A3-$4402` | 96 | 12x8 tile-index layout |
| 7 | `$00` | null | 0 | terminator/null record |

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
shape. The other two bytes are a little-endian pointer to the corresponding
tile-index layout described above; the final alias uses a null pointer.

The eight prefix records are:

| Alias index | Effective shape | Layout pointer |
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

## Bank 9 streams

Bank 9 contains 26 unique streams for IDs `$46-$5F`. Every descriptor uses
placement shape `$08`, every stream expands to 768 bytes, and the streams form
an exact contiguous range through `09:7D98`.

| ID | CPU range | ROM range | Compressed | Output | Shape | Dimensions |
|---|---|---:|---:|---:|---:|---:|
| `$46` | `09:4000-$4220` | `$24000-$24220` | 545 | 768 | `$08` | 8x6 |
| `$47` | `09:4221-$4471` | `$24221-$24471` | 593 | 768 | `$08` | 8x6 |
| `$48` | `09:4472-$473B` | `$24472-$2473B` | 714 | 768 | `$08` | 8x6 |
| `$49` | `09:473C-$49D5` | `$2473C-$249D5` | 666 | 768 | `$08` | 8x6 |
| `$4A` | `09:49D6-$4C79` | `$249D6-$24C79` | 676 | 768 | `$08` | 8x6 |
| `$4B` | `09:4C7A-$4ED9` | `$24C7A-$24ED9` | 608 | 768 | `$08` | 8x6 |
| `$4C` | `09:4EDA-$509B` | `$24EDA-$2509B` | 450 | 768 | `$08` | 8x6 |
| `$4D` | `09:509C-$539A` | `$2509C-$2539A` | 767 | 768 | `$08` | 8x6 |
| `$4E` | `09:539B-$5508` | `$2539B-$25508` | 366 | 768 | `$08` | 8x6 |
| `$4F` | `09:5509-$576E` | `$25509-$2576E` | 614 | 768 | `$08` | 8x6 |
| `$50` | `09:576F-$5999` | `$2576F-$25999` | 555 | 768 | `$08` | 8x6 |
| `$51` | `09:599A-$5C1B` | `$2599A-$25C1B` | 642 | 768 | `$08` | 8x6 |
| `$52` | `09:5C1C-$5DDB` | `$25C1C-$25DDB` | 448 | 768 | `$08` | 8x6 |
| `$53` | `09:5DDC-$6023` | `$25DDC-$26023` | 584 | 768 | `$08` | 8x6 |
| `$54` | `09:6024-$6283` | `$26024-$26283` | 608 | 768 | `$08` | 8x6 |
| `$55` | `09:6284-$64BF` | `$26284-$264BF` | 572 | 768 | `$08` | 8x6 |
| `$56` | `09:64C0-$67A3` | `$264C0-$267A3` | 740 | 768 | `$08` | 8x6 |
| `$57` | `09:67A4-$69F9` | `$267A4-$269F9` | 598 | 768 | `$08` | 8x6 |
| `$58` | `09:69FA-$6C0E` | `$269FA-$26C0E` | 533 | 768 | `$08` | 8x6 |
| `$59` | `09:6C0F-$6E0C` | `$26C0F-$26E0C` | 510 | 768 | `$08` | 8x6 |
| `$5A` | `09:6E0D-$7074` | `$26E0D-$27074` | 616 | 768 | `$08` | 8x6 |
| `$5B` | `09:7075-$729D` | `$27075-$2729D` | 553 | 768 | `$08` | 8x6 |
| `$5C` | `09:729E-$7582` | `$2729E-$27582` | 741 | 768 | `$08` | 8x6 |
| `$5D` | `09:7583-$782B` | `$27583-$2782B` | 681 | 768 | `$08` | 8x6 |
| `$5E` | `09:782C-$7AB9` | `$2782C-$27AB9` | 654 | 768 | `$08` | 8x6 |
| `$5F` | `09:7ABA-$7D98` | `$27ABA-$27D98` | 735 | 768 | `$08` | 8x6 |

Bank 9 ends with 615 zero bytes at `09:7D99-$7FFF`.

## Bank 10 streams

The first 12 Bank 10 streams serve IDs `$60-$6B`. They are contiguous from
`0A:4000-$5DED`; each uses shape `$08` and expands to 768 bytes.

| ID | CPU range | ROM range | Compressed | Output | Shape | Dimensions |
|---|---|---:|---:|---:|---:|---:|
| `$60` | `0A:4000-$4275` | `$28000-$28275` | 630 | 768 | `$08` | 8x6 |
| `$61` | `0A:4276-$44CD` | `$28276-$284CD` | 600 | 768 | `$08` | 8x6 |
| `$62` | `0A:44CE-$47B6` | `$284CE-$287B6` | 745 | 768 | `$08` | 8x6 |
| `$63` | `0A:47B7-$4ABA` | `$287B7-$28ABA` | 772 | 768 | `$08` | 8x6 |
| `$64` | `0A:4ABB-$4D5F` | `$28ABB-$28D5F` | 677 | 768 | `$08` | 8x6 |
| `$65` | `0A:4D60-$4FDD` | `$28D60-$28FDD` | 638 | 768 | `$08` | 8x6 |
| `$66` | `0A:4FDE-$51BD` | `$28FDE-$291BD` | 480 | 768 | `$08` | 8x6 |
| `$67` | `0A:51BE-$544A` | `$291BE-$2944A` | 653 | 768 | `$08` | 8x6 |
| `$68` | `0A:544B-$56A5` | `$2944B-$296A5` | 603 | 768 | `$08` | 8x6 |
| `$69` | `0A:56A6-$5925` | `$296A6-$29925` | 640 | 768 | `$08` | 8x6 |
| `$6A` | `0A:5926-$5BC0` | `$29926-$29BC0` | 667 | 768 | `$08` | 8x6 |
| `$6B` | `0A:5BC1-$5DED` | `$29BC1-$29DED` | 557 | 768 | `$08` | 8x6 |

The remaining ten streams complete the primary descriptor family through ID
`$75`.

| ID | CPU range | ROM range | Compressed | Output | Shape | Dimensions |
|---|---|---:|---:|---:|---:|---:|
| `$6C` | `0A:5DEE-$60C2` | `$29DEE-$2A0C2` | 725 | 768 | `$08` | 8x6 |
| `$6D` | `0A:60C3-$632B` | `$2A0C3-$2A32B` | 617 | 768 | `$08` | 8x6 |
| `$6E` | `0A:632C-$659E` | `$2A32C-$2A59E` | 627 | 768 | `$08` | 8x6 |
| `$6F` | `0A:659F-$67BE` | `$2A59F-$2A7BE` | 544 | 768 | `$08` | 8x6 |
| `$70` | `0A:67BF-$6BB0` | `$2A7BF-$2ABB0` | 1,010 | 1,280 | `$2A` | 10x8 |
| `$71` | `0A:6BB1-$701F` | `$2ABB1-$2B01F` | 1,135 | 1,280 | `$2A` | 10x8 |
| `$72` | `0A:7020-$7426` | `$2B020-$2B426` | 1,031 | 1,280 | `$48` | 8x10 |
| `$73` | `0A:7427-$791D` | `$2B427-$2B91D` | 1,271 | 1,280 | `$48` | 8x10 |
| `$74` | `0A:791E-$7BCA` | `$2B91E-$2BBCA` | 685 | 768 | `$08` | 8x6 |
| `$75` | `0A:7BCB-$7E70` | `$2BBCB-$2BE70` | 678 | 768 | `$08` | 8x6 |

Bank 10 ends with 399 zero bytes at `0A:7E71-$7FFF`.

## Bank 11 primary streams

The ten primary streams for IDs `$76-$7F` occupy `0B:4000-$58D5`. All use
shape `$08`, expand to 768 bytes, and have unique pointers.

| ID | CPU range | ROM range | Compressed | Output | Shape | Dimensions |
|---|---|---:|---:|---:|---:|---:|
| `$76` | `0B:4000-$42BA` | `$2C000-$2C2BA` | 699 | 768 | `$08` | 8x6 |
| `$77` | `0B:42BB-$4560` | `$2C2BB-$2C560` | 678 | 768 | `$08` | 8x6 |
| `$78` | `0B:4561-$4856` | `$2C561-$2C856` | 758 | 768 | `$08` | 8x6 |
| `$79` | `0B:4857-$4AF4` | `$2C857-$2CAF4` | 670 | 768 | `$08` | 8x6 |
| `$7A` | `0B:4AF5-$4D75` | `$2CAF5-$2CD75` | 641 | 768 | `$08` | 8x6 |
| `$7B` | `0B:4D76-$4FE6` | `$2CD76-$2CFE6` | 625 | 768 | `$08` | 8x6 |
| `$7C` | `0B:4FE7-$5258` | `$2CFE7-$2D258` | 626 | 768 | `$08` | 8x6 |
| `$7D` | `0B:5259-$544F` | `$2D259-$2D44F` | 503 | 768 | `$08` | 8x6 |
| `$7E` | `0B:5450-$563A` | `$2D450-$2D63A` | 491 | 768 | `$08` | 8x6 |
| `$7F` | `0B:563B-$58D5` | `$2D63B-$2D8D5` | 667 | 768 | `$08` | 8x6 |

## Bank 11 secondary streams

The first 15 secondary descriptors at `06:4198` point to another exact,
contiguous Bank 11 stream family. Every stream expands to 768 bytes and uses
shape `$08`.

| Index | CPU range | ROM range | Compressed | Output |
|---:|---|---:|---:|---:|
| 0 | `0B:58D6-$5BB0` | `$2D8D6-$2DBB0` | 731 | 768 |
| 1 | `0B:5BB1-$5E6D` | `$2DBB1-$2DE6D` | 701 | 768 |
| 2 | `0B:5E6E-$60F5` | `$2DE6E-$2E0F5` | 648 | 768 |
| 3 | `0B:60F6-$634F` | `$2E0F6-$2E34F` | 602 | 768 |
| 4 | `0B:6350-$65E9` | `$2E350-$2E5E9` | 666 | 768 |
| 5 | `0B:65EA-$68E2` | `$2E5EA-$2E8E2` | 761 | 768 |
| 6 | `0B:68E3-$6B20` | `$2E8E3-$2EB20` | 574 | 768 |
| 7 | `0B:6B21-$6DD0` | `$2EB21-$2EDD0` | 688 | 768 |
| 8 | `0B:6DD1-$6FA3` | `$2EDD1-$2EFA3` | 467 | 768 |
| 9 | `0B:6FA4-$71CF` | `$2EFA4-$2F1CF` | 556 | 768 |
| 10 | `0B:71D0-$7387` | `$2F1D0-$2F387` | 440 | 768 |
| 11 | `0B:7388-$75B6` | `$2F388-$2F5B6` | 559 | 768 |
| 12 | `0B:75B7-$787F` | `$2F5B7-$2F87F` | 713 | 768 |
| 13 | `0B:7880-$7B1A` | `$2F880-$2FB1A` | 667 | 768 |
| 14 | `0B:7B1B-$7DCF` | `$2FB1B-$2FDCF` | 693 | 768 |

Bank 11 ends with 560 zero bytes at `0B:7DD0-$7FFF`.

## Bank 12 secondary streams

The remaining 18 descriptors at `06:41C5-$41FA` point into Bank 12. Every
stream expands to 768 bytes and uses shape `$08`. Descriptor indices 25 and 26
are stored out of pointer order (`$5AF2` then `$584B`), but sorting the unique
pointers gives one exact contiguous sequence from `0C:4000-$6E20`.

| Index | CPU range | ROM range | Compressed | Output |
|---:|---|---:|---:|---:|
| 15 | `0C:4000-$42CC` | `$30000-$302CC` | 717 | 768 |
| 16 | `0C:42CD-$44E5` | `$302CD-$304E5` | 537 | 768 |
| 17 | `0C:44E6-$466C` | `$304E6-$3066C` | 391 | 768 |
| 18 | `0C:466D-$4809` | `$3066D-$30809` | 413 | 768 |
| 19 | `0C:480A-$4A95` | `$3080A-$30A95` | 652 | 768 |
| 20 | `0C:4A96-$4D07` | `$30A96-$30D07` | 626 | 768 |
| 21 | `0C:4D08-$4F80` | `$30D08-$30F80` | 633 | 768 |
| 22 | `0C:4F81-$5274` | `$30F81-$31274` | 756 | 768 |
| 23 | `0C:5275-$5569` | `$31275-$31569` | 757 | 768 |
| 24 | `0C:556A-$584A` | `$3156A-$3184A` | 737 | 768 |
| 26 | `0C:584B-$5AF1` | `$3184B-$31AF1` | 679 | 768 |
| 25 | `0C:5AF2-$5E09` | `$31AF2-$31E09` | 792 | 768 |
| 27 | `0C:5E0A-$609C` | `$31E0A-$3209C` | 659 | 768 |
| 28 | `0C:609D-$6314` | `$3209D-$32314` | 632 | 768 |
| 29 | `0C:6315-$65FA` | `$32315-$325FA` | 742 | 768 |
| 30 | `0C:65FB-$68C0` | `$325FB-$328C0` | 710 | 768 |
| 31 | `0C:68C1-$6B84` | `$328C1-$32B84` | 708 | 768 |
| 32 | `0C:6B85-$6E20` | `$32B85-$32E20` | 668 | 768 |

Bank 12 ends with 4,575 zero bytes at `0C:6E21-$7FFF`.

## Remaining work

- Identify visible resource roles through runtime traces rather than artwork
  guesses.