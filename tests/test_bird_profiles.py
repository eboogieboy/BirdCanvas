"""Expanded field-guide regressions: metadata, history and API."""
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from bird_profiles import profile_for
import visitor_leaderboard as board

LOCAL = ZoneInfo("Europe/London")


class BirdProfileTests(unittest.TestCase):
    def test_conservation_and_local_rarity_are_distinct(self):
        from bird_rarity import rarity_for
        robin = profile_for("Robin", "Erithacus rubecula")
        self.assertTrue(robin["reviewed"])
        self.assertEqual(robin["length_cm"], 14)
        self.assertIsNone(robin["conservation"])
        greenfinch = profile_for("Greenfinch", "Chloris chloris")
        self.assertEqual(greenfinch["conservation"], "Red")
        self.assertEqual(rarity_for("Greenfinch", "Chloris chloris")["level"], "common")

    def test_unknown_birds_do_not_get_invented_profiles(self):
        bird = profile_for("Mystery Bird", "Unknown example")
        self.assertFalse(bird["reviewed"])
        self.assertIsNone(bird["length_cm"])
        self.assertIsNone(bird["conservation"])

    def test_history_only_uses_cached_accepted_audio_and_separates_manual(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = datetime(2026, 10, 14, 15, tzinfo=LOCAL)
            with patch.object(board, "CACHE_DIR", Path(tmp)), \
                 patch.object(board, "_observation_start", return_value=date(2026, 10, 13)), \
                 patch.object(board.birdnet_go, "_minimum_confidence", return_value=0.5), \
                 patch("manual_sightings.list_sightings", return_value=[
                     {"name": "Robin", "scientific_name": "Erithacus rubecula", "seen_at": "2026-10-14T10:00:00+01:00"}]), \
                 patch.object(board, "_request_missing") as queue:
                board._save_day(date(2026, 10, 13), {
                    "version": board.CACHE_VERSION, "date": "2026-10-13",
                    "minimum_confidence": 0.5, "checked_at": "2026-10-14T02:00:00+01:00",
                    "species": [{"name": "Robin", "scientific_name": "Erithacus rubecula", "detections": 3}]})
                result = board.species_history("Robin", "Erithacus rubecula", now)
            self.assertEqual(result["detections"], 3)
            self.assertEqual(result["days_heard"], 1)
            self.assertEqual(result["manual_sightings"], 1)
            self.assertFalse(result["complete"])
            self.assertEqual(result["analysed_days"], 1)
            self.assertEqual(result["total_days"], 2)
            self.assertEqual(len(queue.call_args.args[0]), 1)

    def test_profile_api_route(self):
        from server import Handler
        handler = Handler.__new__(Handler)
        handler.path = "/api/birds/profile?name=Robin&scientific=Erithacus%20rubecula"
        handler.send_json = Mock()
        robin = {"name": "Robin", "scientific_name": "Erithacus rubecula", "profile": {"group": "Chats"}}
        with patch("server.catalogue", return_value={"birds": [robin]}), \
             patch("server.species_history", return_value={"days_heard": 2}) as history:
            handler.do_GET()
        history.assert_called_once_with("Robin", "Erithacus rubecula")
        handler.send_json.assert_called_once_with({"bird": robin, "history": {"days_heard": 2}})

    def test_generated_control_page_has_profile_and_filters(self):
        from display import CONTROL_HTML
        self.assertIn('id="bird-profile-modal"', CONTROL_HTML)
        self.assertIn('id="bird-catalog-search"', CONTROL_HTML)
        self.assertIn('id="bird-catalog-group"', CONTROL_HTML)
        self.assertIn('id="bird-catalog-sort"', CONTROL_HTML)
        self.assertIn("openBirdProfile(bird)", CONTROL_HTML)


if __name__ == "__main__":
    unittest.main()
