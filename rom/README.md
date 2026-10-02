Place your legally obtained original ROM here as `original.gb`, or override `ROM`
when invoking `make`. ROM files are ignored by Git and are never included in the
repository or container image.

The supported input is exactly 262144 bytes with SHA-256:

```text
f63b95b5b03c399b8546e5f72004a2ebaf2e2826fa83a76705b2629bd4da817f
```

The build reads this file and writes a separate output under `build/`. It never
modifies the original ROM in place.
