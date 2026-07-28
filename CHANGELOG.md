# Changelog

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
