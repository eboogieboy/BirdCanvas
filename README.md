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
- Visitor leaderboard: `/api/birds/leaderboard?period=30` (periods: 7, 30, 90, all; non-blocking daily-statistics backfill)
- Local rarity: `/api/birds/current`, `/api/birds/day` and `/api/birds/catalog` each include the same `rarity` object for each species (`level`, `label`, `region`, `context`, `basis`). The phone Garden visitors screen shows it on daily bird cards and field-guide tiles, with an `Uncommon +` filter.

BirdCanvas does the display work for the Mirror: it selects the most recently heard species, shortens BirdNET names such as “Eurasian Blackbird” to “Blackbird”, alphabetises the selected set, caches square historical field-guide illustrations locally, and renders a finished named grid JPEG. The Mirror can therefore display one image and refresh it periodically. The Garden visitors page starts with 20 common UK birds and then grows automatically as BirdCanvas encounters new species. It clearly distinguishes starter species from birds actually heard by BirdNET, flags any missing or failed field-guide image, and lets an individual illustration be replaced from the phone and restored to its curated default later. Those custom replacements are stored in BirdCanvas data, survive application deployments and are used by the rendered Magic Mirror panel.

The Garden Visitors leaderboard shows the top ten species by **distinct days heard**, not total calls. Its visitor score is the percentage of days successfully analysed in the requested period with at least one accepted detection; partial scores are clearly labelled until historical backfill finishes. The all-time range starts at the earliest BirdNET observation already evidenced by the catalogue or production artwork, rather than assuming earlier recordings. Statistics are cached under `data/visitor_leaderboard/days/` (included in nightly data backups) and are recalculated when the confidence threshold changes. Brief microphone outages cannot be distinguished from genuinely quiet days, so scores are indicative, not measures of continuous microphone uptime.

Local rarity refers to **indicative frequency around North Tyneside and the nearby North East coast**, not UK conservation status, a personal encounter rate, or a verified identification. Seasonal context is shown where useful. Unreviewed species are marked **Unrated** rather than incorrectly labelled rare. The reviewable baseline is in `code/bird_rarity.py`; BTO BirdFacts Places and Northumberland & Tyneside Bird Club records are useful when updating it. Rare or surprising BirdNET-Go detections still need audio review. These labels are display-only and do not change detection thresholds, artwork exclusions, generation or TV/Mirror delivery.

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

Version `0.23.0` — a clear five-service health overview on the phone control page and faster Tailscale browsing through lazy, cached JPEG thumbnails. Live display polling no longer reloads the full artwork library every 15 seconds.

The system screen distinguishes healthy, attention required, failure and unverified conditions. BirdNET-Go, generation and Frame status come from existing production state; backup and Mirror sender status are read-only observations of systemd timers and their last completed jobs. These do not independently prove cloud backup restorability or delivery to a powered-off TV.

Gallery artwork previews are built on demand and cached on disk under `output/gallery/thumbs/`. Full resolution originals stay in `output/archive/` and continue to be used for detail views and displays.


## Deployment safety

Pull requests now run the same regression suite, Python compilation, generated-page build and deployment-shell syntax checks in GitHub Actions before merge. The Pi auto-deployer also runs the full candidate test suite and page generation from its clean deployment checkout before it copies anything into the live installation. A bad candidate therefore fails preflight while the current live BirdCanvas instance remains untouched.
