from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import custom_artwork


class CustomArtworkValidationTests(unittest.TestCase):
    def test_rejects_unsupported_content_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "JPG, PNG or WebP"):
            custom_artwork.save_custom_artwork(
                io.BytesIO(b"not-image"), "file.gif", "image/gif", "Test"
            )

    def test_png_signature_validation(self) -> None:
        custom_artwork._validate_signature("image/png", b"\x89PNG\r\n\x1a\nmore")
        with self.assertRaisesRegex(ValueError, "does not match"):
            custom_artwork._validate_signature("image/png", b"not a png")

    def test_webp_signature_validation(self) -> None:
        custom_artwork._validate_signature("image/webp", b"RIFF1234WEBPmore")
        with self.assertRaisesRegex(ValueError, "valid WebP"):
            custom_artwork._validate_signature("image/webp", b"RIFF1234NOPE")


if __name__ == "__main__":
    unittest.main()
