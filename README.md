# Source-Only Game Boy Translation Builder

This repository builds an English-translated Game Boy ROM from a legally
obtained original ROM. It intentionally does **not** distribute the original
ROM, a disassembly, extracted graphics or sound, decoded original dialogue, or
generated ROM-derived binary assets.

## Required input

Place the supported original ROM at `rom/original.gb`. The required SHA-256 is:

```text
f63b95b5b03c399b8546e5f72004a2ebaf2e2826fa83a76705b2629bd4da817f
```

The original ROM is ignored by Git and is never modified.

## Build

```sh
make test
make translated
```

The translated ROM is written to `build/translated.gb`. The current expected
SHA-256 is:

```text
312798b43d2415fecbfe777e7d54c10f247b60bb68554657392aff6398a5150b
```

The builder validates both hashes and fails if the wrong original ROM is used
or if the generated output differs from the known translation build.

## How reconstruction works

`tools/bin/gb-translate-build` copies the original ROM in memory and applies
only deterministic, repository-owned replacements:

- English font glyphs defined in `tools/gb/font.py`;
- English title and menu artwork defined in `tools/gb/title_graphics.py`;
- English text from `translation/patches.tsv`;
- text pointer and allocation metadata from `translation/references.tsv` and
  `translation/ranges.tsv`;
- fixed English user-interface labels;
- a recalculated Game Boy global checksum.

Some numeric and user-interface glyphs needed by the game are retained by
reading them directly from the user's original ROM during the build. They are
not stored in this repository.

The build does not invoke RGBDS, use a disassembly, or consume extracted image,
audio, font, or binary resource files.

## Repository policy

Run the index-level policy check with:

```sh
make audit
```

The audit rejects tracked ROMs, generated binaries, extracted media,
disassembly and analysis directories, local decoded-original catalogs, and
unreviewed Japanese/CJK content. This is a technical safeguard, not legal
advice.

The following remain local and ignored if they exist in a development
workspace:

```text
rom/original.gb
build/
disassembly/
analysis/
translation/strings.tsv
translation/glossary.tsv
translation/text_layout.tsv
```

## Commands

```text
make test        Run repository-independent tests and the ROM-dependent test
                 when rom/original.gb is present
make translated  Build build/translated.gb directly from the original ROM
make audit       Check the Git index for prohibited material
make clean       Remove generated output
make run         Run the translated ROM in SameBoy
make debug       Open the translated ROM in the SameBoy debugger
```

The devcontainer includes Python, Pillow, SameBoy, and existing Game Boy
development utilities. Container startup and generic tests do not require a
ROM.