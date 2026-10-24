import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

import bird_catalog
import bird_sessions
import manual_sightings

TZ = ZoneInfo("Europe/London")


class ManualSightingTests(unittest.TestCase):
    def test_store_deduplicates_one_species_per_day_and_deletes_by_id(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "manual_sightings.json"
            now = datetime(2026, 10, 24, 10, 35, tzinfo=TZ)
            first = manual_sightings.add_sighting("Kingfisher", "Alcedo atthis", now=now, path=path)
            again = manual_sightings.add_sighting("kingfisher", "Alcedo atthis", now=now+timedelta(minutes=1), path=path)
            self.assertFalse(first["duplicate"])
            self.assertTrue(again["duplicate"])
            self.assertEqual(len(manual_sightings.list_sightings(path=path)), 1)
            start = datetime(2026, 10, 24, 0, tzinfo=TZ)
            self.assertEqual(len(manual_sightings.sightings_between(start, start+timedelta(days=1), path=path)), 1)
            manual_sightings.delete_sighting(first["sighting"]["id"], path=path)
            self.assertEqual(manual_sightings.list_sightings(path=path), [])
            with self.assertRaises(ValueError):
                manual_sightings.delete_sighting(first["sighting"]["id"], path=path)

    def test_sighting_is_an_observation_not_a_fake_audio_detection(self):
        now = datetime(2026, 10, 24, 11, 0, tzinfo=TZ)
        sightings = [{
            "id": "s123", "name": "Kingfisher",
            "scientific_name": "Alcedo atthis", "seen_at": "2026-10-24T10:35:00+01:00",
        }]
        with patch.object(bird_sessions, "detection_rows", return_value=[]), \
             patch.object(bird_sessions, "sightings_between", return_value=sightings), \
             patch.object(bird_sessions, "load_settings", return_value={"excluded_birds": []}), \
             patch.object(bird_sessions, "display_illustration_for", return_value=None):
            result = bird_sessions.day_session("2026-10-24", now)
        self.assertEqual(result["species_count"], 1)
        self.assertEqual(result["detections_total"], 0)
        self.assertEqual(result["sightings_total"], 1)
        self.assertIsNone(result["last_detection"])
        bird = result["birds"][0]
        self.assertEqual(bird["detections"], 0)
        self.assertIsNone(bird["last_heard"])
        self.assertEqual(bird["sighting_ids"], ["s123"])
        self.assertTrue(bird["manually_seen"])

    def test_audio_and_visual_observations_merge_by_scientific_species(self):
        now = datetime(2026, 10, 24, 11, 0, tzinfo=TZ)
        audio = [{
            "commonName": "Common Kingfisher", "scientificName": "Alcedo atthis",
            "confidence": .92, "date": "2026-10-24", "time": "10:00:00",
        }]
        sightings = [{
            "id": "s123", "name": "Kingfisher",
            "scientific_name": "Alcedo atthis", "seen_at": "2026-10-24T10:35:00+01:00",
        }]
        with patch.object(bird_sessions, "detection_rows", return_value=audio), \
             patch.object(bird_sessions, "_timestamp", return_value=datetime(2026, 10, 24, 10, tzinfo=TZ)), \
             patch.object(bird_sessions, "sightings_between", return_value=sightings), \
             patch.object(bird_sessions, "load_settings", return_value={"excluded_birds": []}), \
             patch.object(bird_sessions, "display_illustration_for", return_value=None):
            result = bird_sessions.day_session("2026-10-24", now)
        self.assertEqual(result["species_count"], 1)
        self.assertEqual(result["detections_total"], 1)
        self.assertEqual(result["sightings_total"], 1)
        self.assertEqual(result["birds"][0]["detections"], 1)
        self.assertEqual(result["birds"][0]["max_confidence"], .92)
        self.assertTrue(result["birds"][0]["manually_seen"])

    def test_field_guide_includes_and_then_removes_a_manual_only_species(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bird_catalog.json"
            sighting = [{"id": "s123", "name": "Kingfisher",
                         "scientific_name": "Alcedo atthis", "seen_at": "2026-10-24T10:35:00+01:00"}]
            tile = {"path": Path(folder)/"kingfisher.jpg", "status": "missing",
                    "has_mapping": False, "artist": "", "source_url": "", "problem": ""}
            with patch.object(bird_catalog, "STARTER_BIRDS", []), \
                 patch.object(bird_catalog, "list_sightings", return_value=sighting), \
                 patch.object(bird_catalog, "mirror_tile_info", return_value=tile):
                result = bird_catalog.catalogue(path=path)
                bird_catalog.record_birds([{
                    "name": "Kingfisher", "scientific_name": "Alcedo atthis",
                    "detections": 0, "last_heard": None, "first_heard": None,
                }], path=path)
                self.assertFalse(path.exists())
            self.assertEqual(result["species_count"], 1)
            self.assertEqual(result["heard_count"], 0)
            self.assertEqual(result["sighted_count"], 1)
            self.assertTrue(result["birds"][0]["sighted"])
            with patch.object(bird_catalog, "STARTER_BIRDS", []), \
                 patch.object(bird_catalog, "list_sightings", return_value=[]):
                self.assertEqual(bird_catalog.catalogue(path=path)["species_count"], 0)


if __name__ == "__main__":
    unittest.main()
