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

BirdCanvas does the display work for the Mirror: it selects the most recently heard species, shortens BirdNET names such as “Eurasian Blackbird” to “Blackbird”, alphabetises the selected set, caches square historical field-guide illustrations locally, and renders a finished named grid JPEG. The Mirror can therefore display one image and refresh it periodically. The Garden visitors page starts with 20 common UK birds and then grows automatically as BirdCanvas encounters new species. It clearly distinguishes starter species from birds actually heard by BirdNET, flags any missing or failed field-guide image, and lets an individual illustration be replaced from the phone and restored to its curated default later. Those custom replacements are stored in BirdCanvas data, survive application deployments and are used by the rendered Magic Mirror panel.

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

Version `0.21.6` — field-guide replacements now update the heard-bird cards immediately as well as the field-guide library and Magic Mirror, with adaptive Mirror bird-grid sizing and the existing safe deployment preflight.


## Deployment safety

Pull requests now run the same regression suite, Python compilation, generated-page build and deployment-shell syntax checks in GitHub Actions before merge. The Pi auto-deployer also runs the full candidate test suite and page generation from its clean deployment checkout before it copies anything into the live installation. A bad candidate therefore fails preflight while the current live BirdCanvas instance remains untouched.
