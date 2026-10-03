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

The English source manifests are under `translation/`. Original-language catalogs and
reverse-engineering evidence remain local and ignored.