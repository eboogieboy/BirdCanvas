import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

import bird_sessions

TZ = ZoneInfo("Europe/London")


class BirdSessionTests(unittest.TestCase):
    def test_current_session_groups_species_and_marks_artwork_exclusions(self):
        rows = [
            {
                "timestamp": "2026-10-02T09:00:00+01:00",
                "commonName": "Eurasian Blackbird",
                "scientificName": "Turdus merula",
                "confidence": 0.71,
            },
            {
                "timestamp": "2026-10-02T09:05:00+01:00",
                "commonName": "Eurasian Blackbird",
                "scientificName": "Turdus merula",
                "confidence": 0.86,
            },
            {
                "timestamp": "2026-10-02T09:06:00+01:00",
                "commonName": "Black-headed Gull",
                "scientificName": "Chroicocephalus ridibundus",
                "confidence": 0.8,
            },
        ]
        production = {
            "collecting_since": "2026-10-02T04:00:00+01:00",
            "next_generation": "2026-10-03T04:00:00+01:00",
            "settings": {"frequency": "daily"},
        }
        now = datetime(2026, 10, 2, 10, tzinfo=TZ)

        with patch.object(bird_sessions, "production_status", return_value=production), \
             patch.object(bird_sessions, "detection_rows", return_value=rows), \
             patch.object(bird_sessions, "load_settings", return_value={"excluded_birds": ["gull"]}), \
             patch.object(
                 bird_sessions,
                 "illustration_for",
                 side_effect=lambda name, scientific: {"image_url": "blackbird.jpg"} if "Blackbird" in name else None,
             ):
            result = bird_sessions.current_session(now)

        self.assertEqual(result["species_count"], 2)
        self.assertEqual(result["detections_total"], 3)
        self.assertEqual(result["birds"][0]["name"], "Black-headed Gull")
        blackbird = next(b for b in result["birds"] if b["name"] == "Blackbird")
        gull = next(b for b in result["birds"] if b["name"] == "Black-headed Gull")
        self.assertEqual(blackbird["detections"], 2)
        self.assertEqual(blackbird["max_confidence"], 0.86)
        self.assertFalse(blackbird["excluded_from_artwork"])
        self.assertTrue(gull["excluded_from_artwork"])
        self.assertIsNotNone(blackbird["illustration"])

    def test_eurasian_prefix_is_removed_from_display_names(self):
        rows = [
            {
                "timestamp": "2026-10-02T09:00:00+01:00",
                "commonName": "Eurasian Wren",
                "scientificName": "Troglodytes troglodytes",
                "confidence": 0.88,
            }
        ]
        production = {
            "collecting_since": "2026-10-02T04:00:00+01:00",
            "next_generation": "2026-10-03T04:00:00+01:00",
            "settings": {"frequency": "daily"},
        }
        now = datetime(2026, 10, 2, 10, tzinfo=TZ)

        with patch.object(bird_sessions, "production_status", return_value=production), \
             patch.object(bird_sessions, "detection_rows", return_value=rows), \
             patch.object(bird_sessions, "load_settings", return_value={"excluded_birds": []}):
            result = bird_sessions.current_session(now)

        self.assertEqual(result["birds"][0]["name"], "Wren")
        self.assertNotIn("Eurasian", result["birds"][0]["name"])

    def test_day_session_rejects_future_dates(self):
        now = datetime(2026, 10, 2, 10, tzinfo=TZ)
        with self.assertRaises(ValueError):
            bird_sessions.day_session("2026-10-03", now)


if __name__ == "__main__":
    unittest.main()
