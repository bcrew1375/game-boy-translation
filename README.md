# Multi-Project Game Boy Translation Workstation

This repository is a source-only workstation for reproducible Game Boy translation
projects. It separates reusable ROM, patching, text-allocation, graphics, project-loading,
and audit infrastructure from each game's addresses, formats, translations, artwork, and
expected hashes.

The repository intentionally does **not** distribute original ROMs, disassemblies,
extracted graphics or sound, decoded original-language catalogs, or generated ROM-derived
binary assets.

## Projects

List checked-in projects with:

```sh
gb-workstation list
```

The currently supported project is:

```text
gb-db-z-gokou    GB DBZ GOKOU
```

Each project is self-contained under `projects/<project-id>/` and provides:

- `project.toml` with input/output identity, adapter, manifests, and approved ranges;
- a game-specific Python package under `src/`;
- repository-authored English translation data under `translation/`;
- reviewed, dialogue-free terminology manifests under `translation/`, when a project needs
  evidence-backed naming consistency;
- reviewed, reasoned reverse-engineering notes and compact derived lookup tables under
  `analysis/`, when they are safe to distribute;
- project-specific tests under `tests/`.

Reusable code lives under `toolkit/gbworkbench/`. Generic toolkit modules never import a
game project. Project adapters may import toolkit primitives.

## Build the current project

Place a legally obtained original ROM at:

```text
roms/gb-db-z-gokou/original.gb
```

Then run:

```sh
make test
make translated
```

The translated output is written to:

```text
build/gb-db-z-gokou/translated.gb
```

Equivalent direct invocation:

```sh
gb-workstation build gb-db-z-gokou
```

Input and output paths can be overridden without changing project metadata:

```sh
gb-workstation build gb-db-z-gokou \
  --rom /path/to/original.gb \
  --output /path/to/translated.gb
```

The generic executor refuses to overwrite the input ROM and validates input size/hash,
output size/hash, and the adapter-reported digest. The project adapter additionally checks
game-specific pointers and ensures all changed bytes fall within declared or manifest-based
approved locations.

## Commands

```text
make projects                         List checked-in projects
make validate PROJECT=gb-db-z-gokou  Validate project metadata without a ROM
make test-toolkit                     Run generic synthetic tests without a ROM
make test-project PROJECT=...         Run one project's tests
make test                             Run toolkit and default-project tests
make translated PROJECT=...          Build one translated ROM
make info PROJECT=...                 Show resolved project metadata
make audit                            Audit repository source policy
make clean                            Remove generated build output
make run PROJECT=...                  Run a generated ROM in SameBoy
make debug PROJECT=...                Open a generated ROM in the debugger
```

`make translated` continues to default to `gb-db-z-gokou`. The deprecated
`gb-translate-build ROM -o OUTPUT` wrapper remains temporarily and delegates to the new
project-aware CLI.

The devcontainer runs `make self-test` after creation. This checks the shared toolkit,
discovers and validates every checked-in project, runs each project's ROM-independent
tests, exercises the disassembler with a synthetic ROM, and audits repository source
without requiring any user-supplied ROM.

## Add another game

1. Create `projects/<project-id>/project.toml`.
2. Put the adapter package under `projects/<project-id>/src/`.
3. Keep all game-specific hashes, offsets, formats, codecs, text rules, artwork, and
   translations in that project.
4. Use toolkit primitives for bounded writes, hashing, project loading, allocation, and
   Game Boy tile processing.
5. Add project tests under `projects/<project-id>/tests/`.
6. Put the user-supplied ROM under `roms/<project-id>/`; never track it.
7. Run `make test`, `make audit`, and a clean-room reconstruction.

Do not promote a format discovered in one game into the generic toolkit until another
project demonstrates actual reuse.

## Repository policy

Run:

```sh
make audit
```

The audit checks tracked and prospective non-ignored source files. It rejects ROMs,
generated binaries, extracted media, disassemblies, local decoded-original catalogs,
unreviewed Japanese/CJK content, and suspicious embedded byte arrays. Reviewed project-local
analysis documents are allowed. Compact character/encoding lookup tables may contain CJK only
in an explicitly allowlisted character column, with at most one CJK code point per row. The
`gb-db-z-gokou` terminology glossary is a narrow exception to the banned glossary basename: it
contains romanized isolated terms, English terminology, and ROM stream addresses, but no CJK or
decoded dialogue. Decoded dialogue and extracted graphics remain prohibited. Repository-authored
graphics definitions in source form are allowed.

Local ignored material may include:

```text
roms/<project-id>/original.gb
build/
analysis/
disassembly/
projects/*/analysis/tiles/
projects/*/analysis/bank3_text_tables.tsv
projects/*/local/
projects/*/translation/strings.tsv
projects/*/translation/text_layout.tsv
```

For `gb-db-z-gokou`, the tracked analysis consists of reasoned Markdown/JSON, a script-free
Bank 3 reference index, and the narrowly reviewed `font_tiles.tsv` and `text_encoding.tsv`
lookup tables. Its tracked `translation/glossary.tsv` records evidence-backed terminology
without original dialogue. The full decoded Japanese catalog and reconstructed tile sheets stay
local and ignored.

The audit is a technical safeguard, not legal advice.