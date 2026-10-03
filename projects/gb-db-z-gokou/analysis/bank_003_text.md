# Bank 3 Japanese Text Catalog

## Scope

Bank 3 contains the encoded dialogue, narration, prompts, battle responses, and
training instructions consumed by `TextStream_VBlankStep` at `03:7E00`.
`TextData_Bank3Root` at `03:4000` contains 26 little-endian root entries. Of
those entries, 25 select structurally valid pointer tables and root `$09` is
null.

The decoded story spans both:

- the 23rd Tenkaichi Budokai and the fight with Piccolo/Majunior; and
- the Saiyan story from Raditz's arrival through Vegeta's retreat.

## Generated catalogs

The catalog generator (`tools/bin/gb-text-catalog`) was removed during the
source-only restructure, so the current catalog files are static artifacts.
Two catalogs are relevant:

- `projects/gb-db-z-gokou/analysis/bank3_text_reference_index.tsv` (committed):
  every context/message reference, stream address, and scene label, with the
  decoded text column removed;
- `projects/gb-db-z-gokou/analysis/bank3_text_tables.tsv` (local): the same
  references plus the decoded Japanese, kept out of version control.

The current ROM produces:

- 479 pointer-table references;
- 419 unique stream addresses;
- 56 streams referenced more than once;
- 60 duplicate references beyond the first reference;
- 402 ordinary decoded records;
- 12 records requiring contextual speaker review; and
- 5 fragments surrounding runtime-inserted values.

The stable string ID is based on physical source location, for example
`b03_61eb` for Bank 3, CPU `$61EB`, ROM offset `$0E1EB`. Context and message ID
are references to that string, not its identity. This prevents shared strings
from being translated independently and drifting apart.

Newline controls are represented as the literal escape `\n` inside TSV fields.
The input-sensitive `$FB` control is represented as `<WAIT>`. Regenerating the
catalog preserves nonempty English fields and their translator-maintained
status in the English records of `projects/gb-db-z-gokou/translation/patches.tsv`.

## Root/context map

For low message IDs, root entry `N` corresponds to runtime context `N-1`.
Root `$00` is the global `$80-$FF` message table.

| Root | Runtime context | Table | Entries | Provisional scene |
|---|---|---:|---:|---|
| `$00` | global | `03:4034` | 7 | Global prompts and King Kai training |
| `$01` | `$00` | `03:4289` | 18 | Lookout training and Part 1 opening |
| `$02` | `$01` | `03:4465` | 30 | 23rd Tenkaichi Budokai venue and reunion |
| `$03` | `$02` | `03:4739` | 19 | Tournament preliminaries |
| `$04` | `$03` | `03:494D` | 3 | Tournament drawing |
| `$05` | `$04` | `03:49C8` | 58 | Tournament matches |
| `$06` | `$05` | `03:4FE1` | 22 | Late tournament and Piccolo conflict |
| `$07` | `$06` | `03:541A` | 30 | Goku versus Piccolo/Majunior |
| `$08` | `$07` | `03:573F` | 69 | Tournament ending and optional training |
| `$09` | `$08` | null | 0 | Unused/null root |
| `$0A` | `$09` | `03:60C0` | 17 | Part 2 opening and Raditz's arrival |
| `$0B` | `$0A` | `03:63B7` | 4 | Goku and Piccolo form an alliance |
| `$0C` | `$0B` | `03:6492` | 53 | Raditz battle and Saiyan warning |
| `$0D` | `$0C` | `03:6C20` | 13 | Afterlife and Snake Way |
| `$0E` | `$0D` | `03:6E07` | 5 | King Kai training and Saiyan countdown |
| `$0F` | `$0E` | `03:6F70` | 3 | Vegeta and Nappa arrive on Earth |
| `$10` | `$0F` | `03:6FE1` | 16 | Earth battle and Goku's return |
| `$11` | `$10` | `03:71CC` | 7 | Goku reaches the battlefield |
| `$12` | `$11` | `03:72C6` | 16 | Battle against Nappa |
| `$13` | `$12` | `03:7499` | 22 | Battle against Vegeta |
| `$14` | `$13` | `03:7858` | 20 | Vegeta retreats, evaluation, and ending |
| `$15` | `$14` | `03:4A08` | 26 | Alternate tournament battle responses |
| `$16` | `$15` | `03:5450` | 3 | Alternate Piccolo/Majunior responses |
| `$17` | `$16` | `03:64F4` | 4 | Alternate Raditz responses |
| `$18` | `$17` | `03:72D4` | 9 | Alternate Nappa responses |
| `$19` | `$18` | `03:74BB` | 5 | Alternate Vegeta responses |

## Confirmed Saiyan-story examples

| Address | ROM offset | Japanese subject |
|---|---:|---|
| `03:60E2` | `$0E0E2` | Five years after the battle with Demon King Piccolo |
| `03:61EB` | `$0E1EB` | Raditz tells Goku that he is a Saiyan |
| `03:642D` | `$0E42D` | Piccolo proposes joining forces with Goku |
| `03:6873` | `$0E873` | Special Beam Cannon |
| `03:6E74` | `$0EE74` | King Kai says the Saiyans arrive tomorrow |
| `03:6F76` | `$0EF76` | The two Saiyans invade Earth at 11:43 a.m. |
| `03:7347` | `$0F347` | Vegeta kills the incapacitated Nappa |
| `03:75EF` | `$0F5EF` | Goku says a failure may surpass an elite through effort |
| `03:7B63` | `$0FB63` | Ending narration after Vegeta retreats |

## Shared streams

Shared streams are intentional pointer reuse. Examples include:

- `03:6873`, referenced twice for Piccolo's Special Beam Cannon;
- `03:4D2C-$4FC3`, shared by the main and alternate tournament tables;
- `03:73B4-$7489`, shared by the main and alternate Nappa tables; and
- `03:775C-$7835`, shared by the main and alternate Vegeta tables.

Always translate the canonical English record in
`projects/gb-db-z-gokou/translation/patches.tsv`, not an individual row in the
reference index.

## Runtime fragments

These streams are not complete independent sentences:

- `03:5E5B` and `03:5E64` surround a runtime remaining-attempt count;
- `03:7A93` and `03:7AAE` surround a runtime overall-level value; and
- `03:7B54` precedes a runtime password display.

They are marked `dynamic_fragment` and must be translated together with the
code that inserts the missing value.

## Contextual speakers

Some streams contain `??` or omit a repeated speaker label. Context strongly
identifies several as Chi-Chi, especially `03:4DBC-$4E52`, `03:5A2B`,
`03:6046`, and `03:605F`. These are marked `needs_context`; the decoded
Japanese remains byte-derived, while speaker identification is stored only in
the notes. The speakers at `03:4935` and `03:4941` remain unresolved pending
sequence tracing.

## Remaining work

- Trace callers and event sequencing to confirm every provisional scene name.
- Resolve the unidentified tournament speaker at `03:4935/$4941`.
- Trace runtime insertion paths for the five dynamic fragments.
- Review punctuation such as the font's middle-dot-like mark in context before
  normalizing Japanese prose.
- Translate incrementally while retaining the original decoded Japanese and
  stable address-based IDs.