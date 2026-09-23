# BirdCanvas / GalleryOS

BirdCanvas creates artwork from BirdNET-Go garden-bird observations. On the phone control page you can choose daily, twice weekly or weekly generation and edit the excluded-bird list. GalleryOS provides the artwork library, journal, display controller, scheduling, uploads, presentation settings and diagnostics.

Development can run independently in GitHub Codespaces. Production uses one headless Pi for BirdNET-Go, GalleryOS and Samsung Frame delivery. See [Pi setup and deployment](deployment/PRODUCTION.md). Real hardware pairing and microphone detection must be verified on the Pi.

## Start GalleryOS

From the project root:

```bash
python code/server.py
```

Open port `8000` in Codespaces.

- Display: `/`
- Phone control: `/control/`
- Gallery: `/gallery/`

Stop the server with `Ctrl+C`.

## Rebuild the artwork library

```bash
python code/gallery_library.py
```

## Run the automated tests

```bash
python -m unittest discover -s tests -v
```

The tests use temporary folders and do not alter the live artwork library or display state.

## Run the complete project check

```bash
python code/check_project.py
```

This checks required files, JSON data, archived artwork manifests, Python compilation and the automated test suite.

To run the structural checks without tests:

```bash
python code/check_project.py --skip-tests
```

## Optional repository cleanup

Preview generated files that can be removed:

```bash
python code/cleanup_project.py
```

Apply the cleanup:

```bash
python code/cleanup_project.py --apply
```

This removes Python caches and old sprint ZIP files from the project root. It does not remove artwork, project data or saved backup packages in the `backups` folder.

## Main project areas

- `code/compose.py` — creates BirdCanvas artwork
- `code/birdnet_go.py` — reads the detection ledger for an exact collection window
- `code/production_pipeline.py` — schedules one publication and retries Frame delivery
- `code/gallery_library.py` — builds and edits the artwork collection
- `code/display_controller.py` — resolves automatic, temporary and scheduled display modes
- `code/display_settings.py` — validates display behaviour and hours
- `code/server.py` — GalleryOS HTTP server and API
- `output/control/index.html` — mobile control interface
- `output/gallery/index.html` — gallery interface
- `output/archive/` — archived artwork and manifests
- `tests/` — automated regression tests

## Current release

Version `0.12.0` — BirdNET-Go production pipeline.
