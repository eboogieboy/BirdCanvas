# GalleryOS Sprint 14 — Exhibition Experience

Version 0.11.0

This in-place update replaces the compact artwork detail sheet with a full-screen exhibition catalogue experience.

## What changed

- Library artwork and Journal entries open a full-screen Exhibition view.
- The artwork is presented as the visual hero.
- Previous and next controls move through the visible collection.
- BirdCanvas entries show a generated archive narrative and all recorded visitors.
- Visitors are labelled as hero, character or supporting birds where the creative brief records those roles.
- The complete composition, visual language, palette, mood and archive note are shown.
- Personal notes remain editable.
- Generation and presentation details are displayed.
- Existing artwork management and display controls remain available.

## Verification

Run:

```bash
python code/check_project.py
```

Then start GalleryOS and open a Library artwork and a Journal entry. Both should open the same Exhibition view.
