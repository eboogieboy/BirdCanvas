import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

import mirror_birds

TZ = ZoneInfo("Europe/London")


class MirrorBirdFeedTests(unittest.TestCase):
    def test_feed_uses_today_then_selects_recent_species_and_sorts_alphabetically(self):
        session = {
            "start": "2026-10-03T00:00:00+01:00",
            "end": "2026-10-03T09:00:00+01:00",
            "species_count": 4,
            # day_session returns birds most-recently-heard first.
            "birds": [
                {"name": "Wren", "scientific_name": "Troglodytes troglodytes"},
                {"name": "Robin", "scientific_name": "Erithacus rubecula"},
                {"name": "Blackbird", "scientific_name": "Turdus merula"},
                {"name": "Blue Tit", "scientific_name": "Cyanistes caeruleus"},
            ],
        }
        now = datetime(2026, 10, 3, 9, tzinfo=TZ)
        with patch.object(mirror_birds, "day_session", return_value=session) as day:
            result = mirror_birds.mirror_birds(now=now, limit=3)

        day.assert_called_once_with("2026-10-03", now=now)
        self.assertEqual(
            [bird["name"] for bird in result["birds"]],
            ["Blackbird", "Robin", "Wren"],
        )
        self.assertEqual(result["species_count"], 4)
        self.assertEqual(result["tiles_returned"], 3)
        self.assertEqual(result["order"], "alphabetical")
        self.assertEqual(result["selection"], "calendar_day_most_recent_species")
        self.assertEqual(result["day_start"], "2026-10-03T00:00:00+01:00")
        self.assertEqual(result["day_end"], "2026-10-03T09:00:00+01:00")
        self.assertIn("name=Blackbird", result["birds"][0]["image_url"])

    def test_default_feed_capacity_is_four_rows(self):
        session = {
            "start": "2026-10-03T00:00:00+01:00",
            "end": "2026-10-03T09:00:00+01:00",
            "species_count": 20,
            "birds": [
                {"name": f"Bird {index:02d}", "scientific_name": f"Species {index:02d}"}
                for index in range(20)
            ],
        }
        now = datetime(2026, 10, 3, 9, tzinfo=TZ)
        with patch.object(mirror_birds, "day_session", return_value=session):
            result = mirror_birds.mirror_birds(now=now)

        self.assertEqual(result["max_tiles"], 16)
        self.assertEqual(result["tiles_returned"], 16)

    def test_feed_limit_is_bounded(self):
        session = {
            "start": "2026-10-03T00:00:00+01:00",
            "end": "2026-10-03T09:00:00+01:00",
            "species_count": 0,
            "birds": [],
        }
        now = datetime(2026, 10, 3, 9, tzinfo=TZ)
        with patch.object(mirror_birds, "day_session", return_value=session):
            result = mirror_birds.mirror_birds(now=now, limit=999)
        self.assertEqual(result["max_tiles"], 24)


if __name__ == "__main__":
    unittest.main()
