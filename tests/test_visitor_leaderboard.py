"""Visitor leaderboard scoring, filters, date boundaries and cache regressions."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import visitor_leaderboard as board

LOCAL = ZoneInfo("Europe/London")


class VisitorLeaderboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache_patch = patch.object(board, "CACHE_DIR", Path(self.tmp.name) / "visitor_cache")
        self.cache_patch.start()

    def tearDown(self):
        self.cache_patch.stop()
        self.tmp.cleanup()

    def _save(self, day, rows, checked_at="2026-10-14T14:00:00+01:00", confidence=.5):
        board._save_day(day, {
            "version": board.CACHE_VERSION,
            "date": day.isoformat(),
            "minimum_confidence": confidence,
            "checked_at": checked_at,
            "species": rows,
        })

    def test_accepted_detections_only_and_unique_species_per_day(self):
        day = date(2026, 10, 14)
        rows = [
            {"commonName": "Eurasian Robin", "scientificName": "Erithacus rubecula",
             "timestamp": "2026-10-14T08:00:00+01:00", "confidence": .9},
            {"commonName": "European Robin", "scientificName": "Erithacus rubecula",
             "timestamp": "2026-10-14T09:00:00+01:00", "confidence": .85},
            {"commonName": "Goldfinch", "scientificName": "Carduelis carduelis",
             "timestamp": "2026-10-14T10:00:00+01:00", "confidence": .32},
            {"commonName": "Magpie", "scientificName": "Pica pica",
             "timestamp": "2026-10-14T11:00:00+01:00", "confidence": .95,
             "verified": "false_positive"},
            {"commonName": "Blackbird", "scientificName": "Turdus merula",
             "timestamp": "2026-10-13T23:59:59+01:00", "confidence": .96},
        ]
        with patch.object(board.birdnet_go, "_daily_rows", return_value=rows):
            result = board._calculate_day(day, .5, datetime(2026, 10, 14, 12, tzinfo=LOCAL))
        self.assertEqual(len(result["species"]), 1)
        robin = result["species"][0]
        self.assertEqual(robin["name"], "Robin")
        self.assertEqual(robin["detections"], 2)

    def test_ranking_uses_days_heard_not_raw_detection_count(self):
        now = datetime(2026, 10, 14, 15, tzinfo=LOCAL)
        for day in [date(2026, 10, 11), date(2026, 10, 12), date(2026, 10, 13)]:
            self._save(day, [
                {"name": "Blackbird", "scientific_name": "Turdus merula", "detections": 1},
            ])
        self._save(date(2026, 10, 14), [
            {"name": "Robin", "scientific_name": "Erithacus rubecula", "detections": 150},
        ])
        with patch.object(board, "_observation_start", return_value=date(2026, 10, 11)), \
             patch.object(board.birdnet_go, "_minimum_confidence", return_value=.5):
            result = board.leaderboard("30", now)
        self.assertTrue(result["complete"])
        self.assertEqual(result["analysed_days"], 4)
        self.assertEqual(result["birds"][0]["name"], "Blackbird")
        self.assertEqual(result["birds"][0]["days_heard"], 3)
        self.assertEqual(result["birds"][0]["visitor_score"], 75)
        self.assertEqual(result["birds"][1]["visitor_score"], 25)
        self.assertEqual(result["birds"][1]["detections"], 150)

    def test_partial_backfill_uses_only_analysed_days_and_reports_progress(self):
        now = datetime(2026, 10, 14, 15, tzinfo=LOCAL)
        self._save(date(2026, 10, 14), [
            {"name": "Robin", "scientific_name": "Erithacus rubecula", "detections": 2},
        ])
        with patch.object(board, "_observation_start", return_value=date(2026, 10, 11)), \
             patch.object(board.birdnet_go, "_minimum_confidence", return_value=.5), \
             patch.object(board, "_request_missing") as queue:
            result = board.leaderboard("all", now)
        self.assertFalse(result["complete"])
        self.assertEqual(result["analysed_days"], 1)
        self.assertEqual(result["total_days"], 4)
        self.assertEqual(result["birds"][0]["visitor_score"], 100)
        self.assertEqual(len(queue.call_args.args[0]), 3)

    def test_completed_day_invalidates_midnight_snapshot_and_threshold_changes(self):
        today = datetime(2026, 10, 14, 15, tzinfo=LOCAL)
        yesterday = date(2026, 10, 13)
        self._save(yesterday, [], checked_at="2026-10-13T23:50:00+01:00")
        self.assertIsNone(board._cached_day(yesterday, today, .5))
        self._save(yesterday, [], checked_at="2026-10-14T02:00:00+01:00")
        self.assertIsNotNone(board._cached_day(yesterday, today, .5))
        self.assertIsNone(board._cached_day(yesterday, today, .7))

    def test_generated_garden_page_has_graph_and_all_periods(self):
        from display import CONTROL_HTML
        self.assertIn('id="visitor-leaderboard"', CONTROL_HTML)
        self.assertIn("async function refreshLeaderboard()", CONTROL_HTML)
        self.assertIn("a.thumbnail_url||a.image_url", CONTROL_HTML)
        for period in ("7", "30", "90", "all"):
            self.assertIn(f'data-leaderboard-period="{period}"', CONTROL_HTML)

    def test_leaderboard_server_route(self):
        from server import Handler
        from unittest.mock import Mock
        handler = Handler.__new__(Handler)
        handler.path = "/api/birds/leaderboard?period=7"
        handler.send_json = Mock()
        with patch("server.leaderboard", return_value={"birds": [], "period": "7"}) as runner:
            handler.do_GET()
        runner.assert_called_once_with("7")
        handler.send_json.assert_called_once_with({"birds": [], "period": "7"})

    def test_observation_start_does_not_count_manual_artwork_as_recording(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            manifest = base / "output/archive/manual/manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"observation_date": "2026-08-01"}))
            catalog = base / "data/bird_catalog.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(json.dumps({"birds": {
                "scientific:erithacus rubecula": {"first_seen": "2026-10-03T08:00:00+01:00"}
            }}))
            with patch.object(board, "DATA_DIR", base / "data"), \\
                 patch.object(board, "OUTPUT_DIR", base / "output"):
                self.assertEqual(board._observation_start(date(2026, 10, 14)), date(2026, 10, 3))

    def test_seven_day_window_and_invalid_period(self):
        now = datetime(2026, 10, 14, 12, tzinfo=LOCAL)
        with patch.object(board, "_observation_start", return_value=date(2026, 1, 1)), \
             patch.object(board.birdnet_go, "_minimum_confidence", return_value=.5), \
             patch.object(board, "_request_missing"):
            result = board.leaderboard("7", now)
        self.assertEqual(result["from"], "2026-10-08")
        self.assertEqual(result["total_days"], 7)
        with self.assertRaises(ValueError):
            board.leaderboard("500", now)


if __name__ == "__main__":
    unittest.main()
