# User-supplied ROM inputs

Place legally obtained original ROMs under a directory matching the project ID:

```text
roms/<project-id>/original.gb
```

ROM files are ignored by Git and are never modified in place. Each project's
`project.toml` defines the accepted filename, size, and SHA-256 digest. Generated ROMs are
written separately under `build/<project-id>/`.