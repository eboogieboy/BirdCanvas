# GalleryOS Roadmap

## Current — 0.10.0

Project baseline and automated safety tests:

- automated tests for library, metadata, deletion, scheduling, display resolution, display settings and upload validation
- one complete project-check command
- accurate documentation and versioning
- safe repository-cleanup tooling

## Existing capabilities

- daily BirdCanvas artwork generation and archiving
- presentation and mount management
- searchable artwork library with BirdCanvas/custom/favourite/hidden filters
- artwork detail, rename, favourite, hide and permanent deletion
- protection for currently displayed artwork
- BirdCanvas journal
- temporary display overrides and timed schedules
- uploads for JPG, PNG and WebP artwork
- display hours, rotation, transitions, fit and background settings
- health, backup, diagnostics and recovery tools

## Suggested next development areas

These should be selected only after reviewing the current code and priorities at the start of each sprint:

1. Consolidate generated HTML so the control interface has one authoritative source.
2. Add API-level integration tests for the server routes.
3. Improve artwork-generation provenance and journal detail.
4. Add optional collection/export tools.
5. Prepare Samsung Frame deployment separately from MirrorDisplay integration.
