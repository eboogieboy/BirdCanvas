import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import unquote

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

import bird_images
from bird_images import illustration_for


class BirdImageTests(unittest.TestCase):
    def test_expanded_historical_library_covers_common_species(self):
        expected = {
            "Long-tailed Tit": "Long-tailed Titmouse Grönvold.jpg",
            "Song Thrush": "Song Thrush Grönvold.jpg",
            "Mistle Thrush": "Missel Thrush Grönvold.jpg",
            "Nuthatch": "Nuthatch Grönvold.jpg",
            "Pied Wagtail": "Pied Wagtail Grönvold.jpg",
            "Treecreeper": "Tree Creeper Grönvold.jpg",
            "Stonechat": "Stonechat Grönvold.jpg",
            "Whitethroat": "Whitethroat Grönvold.jpg",
            "Dipper": "Dipper Grönvold.jpg",
            "Wheatear": "Wheatear Grönvold.jpg",
            "House Sparrow": "Feathered%20Favourites",
            "Starling": "00005.jpg",
            "Goldfinch": "11002252763",
            "Greenfinch": "Chloris%20chloris",
            "Chaffinch": "Chaffinch%20%28PSF%29.jpg",
            "Woodpigeon": "6092234605",
            "Collared Dove": "Columba%20decaocto%20Frivaldski.jpg",
            "Magpie": "14564915648",
            "Jackdaw": "14771431613",
            "Carrion Crow": "14568695650",
            "Black-headed Gull": "00047.jpg",
            "Herring Gull": "00122.jpg",
            "Green Woodpecker": "14565126947",
            "Great Spotted Woodpecker": "00015.jpg",
            "Swift": "Wellcome%20V0022226ER.jpg",
            "Swallow": "11001967465",
        }
        for name, filename in expected.items():
            with self.subTest(name=name):
                result = illustration_for(name)
                self.assertIsNotNone(result)
                self.assertIn(unquote(filename), unquote(result["image_url"]))
                self.assertEqual(result["license"], "Public domain")

    def test_scientific_name_can_resolve_an_illustration(self):
        result = illustration_for("Unexpected BirdNET label", "Aegithalos caudatus")
        self.assertIsNotNone(result)
        self.assertIn("Long-tailed%20Titmouse%20Gr%C3%B6nvold.jpg", result["image_url"])


    def test_tile_cache_downloads_once_and_serves_local_square_jpeg(self):
        with tempfile.TemporaryDirectory() as folder:
            payload = io.BytesIO()
            Image.new("RGB", (400, 700), "white").save(payload, "JPEG")
            response = MagicMock()
            response.read.return_value = payload.getvalue()
            response.__enter__.return_value = response
            response.__exit__.return_value = False

            with patch("paths.OUTPUT_DIR", Path(folder)), \
                 patch("urllib.request.urlopen", return_value=response) as opener:
                first = bird_images.mirror_tile_path("Blackbird", "Turdus merula")
                second = bird_images.mirror_tile_path("Blackbird", "Turdus merula")

            self.assertEqual(first, second)
            self.assertTrue(first.is_file())
            with Image.open(first) as image:
                self.assertEqual(image.size, (600, 600))
                self.assertEqual(image.format, "JPEG")
            self.assertEqual(opener.call_count, 1)
            metadata = json.loads(first.with_suffix(".json").read_text())
            self.assertEqual(metadata["status"], "ready")
            self.assertTrue(metadata["has_mapping"])

    def test_missing_mapping_creates_auditable_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch("paths.OUTPUT_DIR", Path(folder)):
                info = bird_images.mirror_tile_info("Mystery Bird", "Example missing")

            self.assertEqual(info["status"], "missing")
            self.assertFalse(info["has_mapping"])
            self.assertIn("No curated illustration", info["problem"])
            self.assertTrue(info["path"].is_file())


    def test_custom_override_takes_precedence_and_can_be_restored(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            payload = io.BytesIO()
            Image.new("RGB", (900, 500), "white").save(payload, "PNG")

            with patch("paths.DATA_DIR", root / "data"), \
                 patch("paths.OUTPUT_DIR", root / "output"):
                info = bird_images.save_tile_override(
                    "Collared Dove",
                    "Streptopelia decaocto",
                    payload.getvalue(),
                    filename="preferred-dove.png",
                )
                path = bird_images.mirror_tile_path(
                    "Collared Dove",
                    "Streptopelia decaocto",
                )

                self.assertTrue(info["overridden"])
                self.assertEqual(info["artist"], "Custom replacement")
                self.assertEqual(path, info["path"])
                self.assertTrue(path.is_file())
                with Image.open(path) as image:
                    self.assertEqual(image.size, (600, 600))
                    self.assertEqual(image.format, "JPEG")

                restored = bird_images.restore_tile_override(
                    "Collared Dove",
                    "Streptopelia decaocto",
                )
                self.assertTrue(restored)
                self.assertFalse(path.exists())

                with patch.object(
                    bird_images,
                    "illustration_for",
                    return_value=None,
                ):
                    default_info = bird_images.mirror_tile_info(
                        "Collared Dove",
                        "Streptopelia decaocto",
                    )

                self.assertFalse(default_info["overridden"])

    def test_custom_override_rejects_non_image_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch("paths.DATA_DIR", Path(folder) / "data"):
                with self.assertRaisesRegex(
                    ValueError,
                    "could not be read",
                ):
                    bird_images.save_tile_override(
                        "Collared Dove",
                        "Streptopelia decaocto",
                        b"not an image",
                        filename="bad.txt",
                    )


    def test_override_lookup_does_not_write_to_runtime_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data_dir = root / "data"
            output_dir = root / "output"
            data_dir.mkdir()
            data_dir.chmod(0o555)
            try:
                with patch("paths.DATA_DIR", data_dir), \
                     patch("paths.OUTPUT_DIR", output_dir):
                    info = bird_images.mirror_tile_info(
                        "Mystery Bird",
                        "Example missing",
                    )
            finally:
                data_dir.chmod(0o755)

            self.assertFalse((data_dir / "bird-image-overrides").exists())
            self.assertEqual(info["status"], "missing")


if __name__ == "__main__":
    unittest.main()
