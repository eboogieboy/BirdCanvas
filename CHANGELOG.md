## 0.23.1 — Generated Health Dashboard Fix

- Corrected the authoritative `code/display.py` page generator to show the live health summary and request health checks when System Status opens. Previously, the unreferenced legacy HTML file had been updated instead, leaving the actual page at "Checking GalleryOS…".
- The generated page now uses the actual release number rather than hard-coding v0.21.6.
- Applied cached gallery and journal thumbnails to the generated phone page, preserving existing bird pages and field-guide functionality.
- Made health checks responsive with a bounded, one-row BirdNET-Go probe instead of a full detection-ledger scan. Failed or slow checks show a retryable warning rather than hanging.
- Added dedicated regression tests for the generated page and BirdNET probe.

## 0.23.0 — System Health and Faster GalleryOS

- Added a compact five-service health summary to the phone dashboard, with detailed BirdNET-Go, generation, Samsung Frame, Mirror sender and nightly backup checks.
- Added bounded, read-only systemd status checks. Missing or unverified services are never reported as healthy.
- Added on-demand 420 × 560 maximum JPEG previews, with versioned cache URLs and lazy loading for gallery and journal lists. Full-resolution artworks remain unchanged.
- Separated 15-second live display polling from full-library refresh, preserving the current hero image unless it actually changes.
- Added regression tests for thumbnail invalidation, path safety and system health reports.

# Changelog

## 0.22.0 — Cost-Optimised Artwork Generation

- Replaced multiple creative-planning API calls with one consolidated GPT-5.6 Sol creative-director call at low reasoning.
- Moved bird selection and post-generation review to GPT-5.6 Luna with reasoning disabled.
- Combined ornithology verification and art critique into one visual review call.
- Added a persistent local species-recognition cache so known birds do not need repeated API descriptions.
- Switched final artwork generation from deprecated GPT Image 1 to GPT Image 2 at medium 1024x1536.
- Preserved rotating subject-balance modes, major-failure-only image retries, gallery metadata and creative-history anti-repetition.
- Stored per-generation model configuration and raw API usage metadata with each artwork for later cost analysis.


## 0.12.0 — BirdNET-Go Production Pipeline

- Added Daily, Monday/Thursday and Weekly collection schedules and a phone control for excluded birds.
- Read BirdNET-Go detections for exact UK-time collection windows; saved species and detection provenance in each artwork.
- Published once per window and saved Frame deliveries for retry without regenerating.
- Limited the TV to ten recorded BirdCanvas uploads while preserving the full Gallery archive.
- Updated headless services, GalleryOS health checks and Python 3.13 multipart upload handling.
- Added production path tests and deployment instructions.

## 0.11.0 — Exhibition Experience

- Replaced the artwork bottom sheet with a full-screen exhibition viewer.
- Artwork images and journal entries open the same exhibition experience.
- Added large hero artwork, contextual narrative, visitor list, creative direction, notes, and previous/next navigation.
- Retained all existing artwork management actions.

## 0.10.0 — Project Baseline and Automated Safety Tests

- Adds automated regression tests covering gallery-library building, metadata editing, artwork deletion and current-artwork protection.
- Adds tests for schedule creation/deletion, artwork-reference cleanup and temporary display overrides.
- Adds tests for display-setting validation and overnight display hours.
- Adds tests for JPG/PNG/WebP upload validation.
- Adds `python code/check_project.py` as the standard project verification command.
- Adds a safe, dry-run-first repository cleanup utility.
- Updates the README, roadmap, changelog and displayed version to match the current application.
- Adds `.gitignore` rules for Python caches, local environments, runtime logs and release ZIP files.

## 0.9.0 — Collection Manager

- Adds collection statistics including artwork, favourite, hidden and storage totals.
- Adds permanent deletion for BirdCanvas and custom artwork.
- Prevents deletion of the current or actively displayed artwork.
- Removes display references and schedules when an artwork is deleted.
- Keeps the previous custom-upload deletion endpoint for compatibility.

## 0.5.1 — Mobile Dashboard

- Replaces the long administration page with a mobile-first Gallery dashboard.
- Adds a large “Currently Showing” artwork card.
- Shows automatic, scheduled and temporary display modes clearly.
- Shows the next expected display change.
- Adds quick actions for Add Artwork, Schedule, Library and Favourites.
- Adds bottom navigation designed for one-handed phone use.

## 0.10.0 — BirdCanvas Stories
- Expanded artwork detail sheets into a curated story view.
- Added mood, visual language, palette, composition and bird-role sections.
- Added editable personal notes stored in each artwork manifest.
- Added previous and next artwork navigation.
- Added automated coverage for artwork notes.
