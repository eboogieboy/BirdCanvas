# Upgrade to GalleryOS v0.5.1

This release replaces only `code/display.py`.

It does not change your stored artwork, schedules, custom uploads, manifests, or server code.

## Install

1. Stop GalleryOS with `Ctrl+C` if the server is running.
2. Upload the included `display.py` into `BirdCanvas/code/` and replace the existing file.
3. Optionally upload `VERSION`, `CHANGELOG.md`, and `ROADMAP.md` into the top level of the repository.
4. From `/workspaces/BirdCanvas`, run:

```bash
python3 code/display.py
```

5. Restart GalleryOS:

```bash
python3 code/server.py
```

6. Open `/control/` and refresh the page.

## Rollback

Restore your previous `code/display.py`, then run:

```bash
python3 code/display.py
python3 code/server.py
```
