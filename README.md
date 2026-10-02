# BirdCanvas / GalleryOS

BirdCanvas creates artwork from BirdNET-Go garden-bird observations. On the phone control page you can choose daily, twice weekly or weekly generation and edit the excluded-bird list. GalleryOS provides the artwork library, journal, display controller, scheduling, uploads, presentation settings and diagnostics.

Development can run independently in GitHub Codespaces. Production uses one headless Pi for BirdNET-Go, GalleryOS and Samsung Frame delivery. See [Pi setup and deployment](deployment/PRODUCTION.md) and [backup / disaster recovery](deployment/BACKUP.md). Real hardware pairing and microphone detection must be verified on the Pi.

Use `deployment/install-headless.sh` for that Pi. The older `deployment/install.sh`, kiosk scripts and morning/midday/evening timers are retained only as a legacy fallback; running that installer would enable the old artwork schedule. The ZIP import and manual detection commands are also retained for testing. Do not remove `data/`, `imports/`, `output/current/` or `output/archive/`: they contain observations or artwork rather than disposable code.

## Start GalleryOS

From the project root:

```bash
python code/server.py
```

Open port `8000` in Codespaces.

- Display: `/`
- Phone control: `/control/`
- Gallery: `/gallery/`
- Magic Mirror bird feed: `/api/mirror/birds` (defaults to 12 tile-ready birds)
- Magic Mirror rendered panel: `/api/mirror/panel.jpg` (defaults to a 1200 × 900, 4 × 3 grid)
- Field-guide catalogue: `/api/birds/catalog` (all species BirdCanvas has recorded, with thumbnail health)

BirdCanvas does the display work for the Mirror: it selects the most recently heard species, shortens BirdNET names such as “Eurasian Blackbird” to “Blackbird”, alphabetises the selected set, caches square historical field-guide illustrations locally, and renders a finished named grid JPEG. The Mirror can therefore display one image and refresh it periodically. The Garden visitors page also keeps a persistent master thumbnail library of species BirdCanvas has encountered, clearly flagging any missing or failed field-guide image so the illustration set can be improved over time.

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

Version `0.19.0` — portrait GalleryOS, live bird sessions, Samsung Frame gallery delivery, tighter locally rendered Magic Mirror bird panel, persistent field-guide thumbnail auditing and off-device disaster recovery.
