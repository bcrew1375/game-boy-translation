# GB DBZ GOKOU translation project

Project ID: `gb-db-z-gokou`

## Required input

Place the supported original ROM at:

```text
roms/gb-db-z-gokou/original.gb
```

It must be exactly 262,144 bytes with SHA-256:

```text
f63b95b5b03c399b8546e5f72004a2ebaf2e2826fa83a76705b2629bd4da817f
```

## Build

```sh
gb-workstation validate gb-db-z-gokou
gb-workstation test gb-db-z-gokou
gb-workstation build gb-db-z-gokou
```

The output is written to `build/gb-db-z-gokou/translated.gb` and must have SHA-256:

```text
312798b43d2415fecbfe777e7d54c10f247b60bb68554657392aff6398a5150b
```

The confirmed build changes 3,572 bytes.

## Project-owned behavior

This project owns and tests:

- the game's resource compression format;
- the primary font location, layout, preserved UI glyphs, and English glyph mapping;
- bank-3 text encoding, controls, allocation, pointer tables, and pointer validation;
- English title and menu artwork;
- fixed English user-interface labels;
- ROM offsets, resource slot sizes, and checksum policy;
- approved modification ranges and the expected translated-ROM hash.

The English source manifests are under `translation/`. This includes `glossary.tsv`, a
reviewed terminology manifest with canonical English names, romanized source terms,
categories, representative Bank 3 stream addresses, recurrence counts, confidence, and
localization notes. It contains isolated terms only; decoded original-language dialogue and
the full ROM-derived text catalog remain local and ignored.

## Analysis coverage

The reviewed byte-range map is `analysis/project.json`. Generate current statistics and the SVG
bank map with:

```sh
gb-workstation analyze gb-db-z-gokou
```

Reports are written under `build/gb-db-z-gokou/analysis/`. Unmapped bytes are counted as
`unknown`, and nested ranges allow a broad resource to be refined into more specific tables or
other structures without double-counting total analyzed coverage.
