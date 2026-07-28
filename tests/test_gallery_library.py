from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import gallery_library


class GalleryLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.archive = self.root / "output/archive"
        self.current = self.root / "output/current/manifest.json"
        self.library_dir = self.root / "output/gallery"
        self.library_file = self.library_dir / "library.json"
        self.patchers = [
            patch.object(gallery_library, "ARCHIVE_DIR", self.archive),
            patch.object(gallery_library, "CURRENT_MANIFEST", self.current),
            patch.object(gallery_library, "LIBRARY_DIR", self.library_dir),
            patch.object(gallery_library, "LIBRARY_FILE", self.library_file),
        ]
        for item in self.patchers:
            item.start()

    def tearDown(self) -> None:
        for item in reversed(self.patchers):
            item.stop()
        self.temp.cleanup()

    def create_artwork(self, artwork_id: str, *, current: bool = False) -> None:
        folder = self.archive / artwork_id
        folder.mkdir(parents=True)
        (folder / "artwork.png").write_bytes(b"image")
        manifest = {
            "id": artwork_id,
            "collection": "birdcanvas",
            "title": artwork_id,
            "created_at": "2026-07-18T08:00:00+01:00",
            "image": "artwork.png",
            "species": ["Robin"],
        }
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        if current:
            self.current.parent.mkdir(parents=True, exist_ok=True)
            self.current.write_text(json.dumps(manifest), encoding="utf-8")

    def test_build_library_collects_valid_artwork_and_stats(self) -> None:
        self.create_artwork("birdcanvas-1")
        payload = gallery_library.build_library()
        self.assertEqual(payload["stats"]["artwork_count"], 1)
        self.assertEqual(payload["artworks"][0]["species"], ["Robin"])
        self.assertTrue(self.library_file.is_file())

    def test_update_metadata_changes_title_and_flags(self) -> None:
        self.create_artwork("birdcanvas-1")
        updated = gallery_library.update_artwork_metadata(
            "birdcanvas-1", title="Morning Robin", favourite=True, hidden=True
        )
        self.assertEqual(updated["title"], "Morning Robin")
        self.assertTrue(updated["favourite"])
        self.assertTrue(updated["hidden"])

    def test_update_metadata_saves_notes(self) -> None:
        self.create_artwork("art-1")
        result = gallery_library.update_artwork_metadata("art-1", notes="A quiet morning memory.")
        self.assertEqual(result["notes"], "A quiet morning memory.")
        manifest = json.loads((self.archive / "art-1" / "manifest.json").read_text())
        self.assertEqual(manifest["notes"], "A quiet morning memory.")

    def test_update_metadata_rejects_empty_title(self) -> None:
        self.create_artwork("birdcanvas-1")
        with self.assertRaisesRegex(ValueError, "Title cannot be empty"):
            gallery_library.update_artwork_metadata("birdcanvas-1", title="   ")

    def test_delete_artwork_removes_archive(self) -> None:
        self.create_artwork("birdcanvas-1")
        result = gallery_library.delete_artwork("birdcanvas-1")
        self.assertEqual(result["id"], "birdcanvas-1")
        self.assertFalse((self.archive / "birdcanvas-1").exists())

    def test_delete_current_artwork_is_blocked(self) -> None:
        self.create_artwork("birdcanvas-1", current=True)
        with self.assertRaisesRegex(ValueError, "current BirdCanvas artwork"):
            gallery_library.delete_artwork("birdcanvas-1")
        self.assertTrue((self.archive / "birdcanvas-1").exists())

    def test_build_library_includes_exhibition_story(self):
        self.create_artwork("birdcanvas-1")
        library = gallery_library.build_library()
        artwork = library["artworks"][0]
        exhibition = artwork["exhibition"]
        self.assertIn("narrative", exhibition)
        self.assertEqual(exhibition["visitor_count"], len(artwork["species"]))
        self.assertIn("hero_birds", exhibition)



if __name__ == "__main__":
    unittest.main()
