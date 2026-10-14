from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import gallery_library
import gallery_thumbnails


class ThumbnailTests(unittest.TestCase):
    def test_thumbnail_is_small_cached_and_revised_with_original(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / "archive"
            folder = archive / "work-1"
            folder.mkdir(parents=True)
            original = folder / "artwork.png"
            Image.new("RGB", (1600, 2100), (82, 120, 95)).save(original)
            (folder / "manifest.json").write_text(json.dumps({
                "id": "work-1", "image": "artwork.png", "created_at": "2026-10-14T10:00:00+01:00"
            }))
            with patch.object(gallery_library, "ARCHIVE_DIR", archive), patch.object(
                gallery_thumbnails, "CACHE_DIR", Path(root) / "thumbs"
            ):
                first = gallery_thumbnails.thumbnail_path("work-1")
                self.assertTrue(first.is_file())
                with Image.open(first) as preview:
                    self.assertLessEqual(preview.width, 420)
                    self.assertLessEqual(preview.height, 560)
                self.assertEqual(first, gallery_thumbnails.thumbnail_path("work-1"))
                Image.new("RGB", (1200, 1200), (190, 100, 90)).save(original)
                second = gallery_thumbnails.thumbnail_path("work-1")
                self.assertNotEqual(first, second)
                self.assertTrue(second.is_file())
                self.assertTrue(original.is_file())

    def test_unrecognised_artwork_cannot_be_used_as_a_path(self):
        with tempfile.TemporaryDirectory() as root, patch.object(
            gallery_library, "ARCHIVE_DIR", Path(root)
        ):
            with self.assertRaisesRegex(ValueError, "not found"):
                gallery_thumbnails.thumbnail_path("../../etc/passwd")


if __name__ == "__main__":
    unittest.main()
