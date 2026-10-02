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
    def test_feed_selects_recent_species_then_sorts_tiles_alphabetically(self):
        session = {
            "start": "2026-10-03T04:00:00+01:00",
            "species_count": 4,
            # current_session returns birds most-recently-heard first.
            "birds": [
                {"name": "Wren", "scientific_name": "Troglodytes troglodytes"},
                {"name": "Robin", "scientific_name": "Erithacus rubecula"},
                {"name": "Blackbird", "scientific_name": "Turdus merula"},
                {"name": "Blue Tit", "scientific_name": "Cyanistes caeruleus"},
            ],
        }
        now = datetime(2026, 10, 3, 9, tzinfo=TZ)
        with patch.object(mirror_birds, "current_session", return_value=session):
            result = mirror_birds.mirror_birds(now=now, limit=3)

        self.assertEqual(
            [bird["name"] for bird in result["birds"]],
            ["Blackbird", "Robin", "Wren"],
        )
        self.assertEqual(result["species_count"], 4)
        self.assertEqual(result["tiles_returned"], 3)
        self.assertEqual(result["order"], "alphabetical")
        self.assertEqual(result["selection"], "most_recent_species")
        self.assertIn("name=Blackbird", result["birds"][0]["image_url"])

    def test_feed_limit_is_bounded(self):
        session = {"start": "", "species_count": 0, "birds": []}
        with patch.object(mirror_birds, "current_session", return_value=session):
            result = mirror_birds.mirror_birds(limit=999)
        self.assertEqual(result["max_tiles"], 24)


if __name__ == "__main__":
    unittest.main()
