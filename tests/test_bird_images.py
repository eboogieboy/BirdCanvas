import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

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
        }
        for name, filename in expected.items():
            with self.subTest(name=name):
                result = illustration_for(name)
                self.assertIsNotNone(result)
                self.assertIn(filename.replace(" ", "%20"), result["image_url"])
                self.assertEqual(result["license"], "Public domain")

    def test_scientific_name_can_resolve_an_illustration(self):
        result = illustration_for("Unexpected BirdNET label", "Aegithalos caudatus")
        self.assertIsNotNone(result)
        self.assertIn("Long-tailed%20Titmouse%20Gr%C3%B6nvold.jpg", result["image_url"])


if __name__ == "__main__":
    unittest.main()
