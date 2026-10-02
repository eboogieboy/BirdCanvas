import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

import bird_catalog


class BirdCatalogueTests(unittest.TestCase):
    def test_records_species_once_and_preserves_first_and_last_seen(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bird_catalog.json"
            bird_catalog.record_birds(
                [
                    {
                        "name": "Blackbird",
                        "scientific_name": "Turdus merula",
                        "first_heard": "2026-10-02T08:00:00+01:00",
                        "last_heard": "2026-10-02T08:10:00+01:00",
                    }
                ],
                path=path,
            )
            bird_catalog.record_birds(
                [
                    {
                        "name": "Blackbird",
                        "scientific_name": "Turdus merula",
                        "first_heard": "2026-10-02T09:00:00+01:00",
                        "last_heard": "2026-10-02T09:15:00+01:00",
                    }
                ],
                path=path,
            )

            data = json.loads(path.read_text())

        entry = next(iter(data["birds"].values()))
        self.assertEqual(entry["first_seen"], "2026-10-02T08:00:00+01:00")
        self.assertEqual(entry["last_seen"], "2026-10-02T09:15:00+01:00")

    def test_catalogue_marks_missing_tiles_for_easy_auditing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bird_catalog.json"
            bird_catalog.record_birds(
                [
                    {
                        "name": "Blackbird",
                        "scientific_name": "Turdus merula",
                        "first_heard": "2026-10-02T08:00:00+01:00",
                        "last_heard": "2026-10-02T08:10:00+01:00",
                    },
                    {
                        "name": "Mystery Bird",
                        "scientific_name": "Example missing",
                        "first_heard": "2026-10-02T08:30:00+01:00",
                        "last_heard": "2026-10-02T08:30:00+01:00",
                    },
                ],
                path=path,
            )

            def tile_info(name, scientific):
                return {
                    "path": Path(folder) / ("blackbird.jpg" if name == "Blackbird" else "mystery-bird.jpg"),
                    "status": "ready" if name == "Blackbird" else "missing",
                    "has_mapping": name == "Blackbird",
                    "artist": "Test Artist" if name == "Blackbird" else "",
                    "source_url": "",
                    "problem": "" if name == "Blackbird" else "No curated illustration yet.",
                }

            with patch.object(bird_catalog, "STARTER_BIRDS", []), \
                 patch.object(bird_catalog, "mirror_tile_info", side_effect=tile_info):
                result = bird_catalog.catalogue(path=path)

        self.assertEqual(result["species_count"], 2)
        self.assertEqual(result["starter_count"], 0)
        self.assertEqual(result["heard_count"], 2)
        self.assertEqual(result["ready_count"], 1)
        self.assertEqual(result["missing_count"], 1)
        self.assertEqual([bird["name"] for bird in result["birds"]], ["Blackbird", "Mystery Bird"])
        self.assertFalse(result["birds"][1]["image_ready"])

    def test_catalogue_starts_with_twenty_common_birds_without_faking_detections(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bird_catalog.json"

            def tile_info(name, scientific):
                slug = name.lower().replace(" ", "-")
                return {
                    "path": Path(folder) / f"{slug}.jpg",
                    "status": "ready",
                    "has_mapping": True,
                    "artist": "Historical plate",
                    "source_url": "",
                    "problem": "",
                }

            with patch.object(bird_catalog, "mirror_tile_info", side_effect=tile_info):
                result = bird_catalog.catalogue(path=path)

        self.assertEqual(result["starter_count"], 20)
        self.assertEqual(result["species_count"], 20)
        self.assertEqual(result["heard_count"], 0)
        self.assertEqual(result["missing_count"], 0)
        names = [bird["name"] for bird in result["birds"]]
        self.assertIn("Blackbird", names)
        self.assertIn("Robin", names)
        self.assertIn("Herring Gull", names)
        self.assertTrue(all(not bird["heard"] for bird in result["birds"]))


if __name__ == "__main__":
    unittest.main()
