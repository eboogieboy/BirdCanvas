from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import display_controller


class DisplayControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp.name) / "state.json"
        self.state_patch = patch.object(display_controller, "STATE_FILE", self.state_file)
        self.state_patch.start()
        self.artwork = {
            "id": "art-1",
            "title": "Artwork",
            "collection": "custom",
            "image_url": "../archive/art-1/artwork.png",
            "hidden": False,
        }

    def tearDown(self) -> None:
        self.state_patch.stop()
        self.temp.cleanup()

    def test_create_and_delete_schedule(self) -> None:
        now = display_controller._now()
        with patch.object(display_controller, "_find_artwork", return_value=self.artwork):
            schedule = display_controller.create_schedule(
                "art-1",
                (now + timedelta(hours=1)).isoformat(),
                (now + timedelta(hours=2)).isoformat(),
            )
        self.assertEqual(len(display_controller.load_state()["schedules"]), 1)
        display_controller.delete_schedule(schedule["id"])
        self.assertEqual(display_controller.load_state()["schedules"], [])

    def test_schedule_end_must_follow_start(self) -> None:
        now = display_controller._now()
        with patch.object(display_controller, "_find_artwork", return_value=self.artwork):
            with self.assertRaisesRegex(ValueError, "End time must be after"):
                display_controller.create_schedule(
                    "art-1",
                    (now + timedelta(hours=2)).isoformat(),
                    (now + timedelta(hours=1)).isoformat(),
                )

    def test_remove_artwork_references_clears_override_and_schedules(self) -> None:
        display_controller.save_state(
            {
                "mode": "temporary_override",
                "override": {"artwork_id": "art-1"},
                "schedules": [
                    {"id": "one", "artwork_id": "art-1"},
                    {"id": "two", "artwork_id": "art-2"},
                ],
            }
        )
        display_controller.remove_artwork_references("art-1")
        state = display_controller.load_state()
        self.assertEqual(state["mode"], "automatic")
        self.assertIsNone(state["override"])
        self.assertEqual([x["artwork_id"] for x in state["schedules"]], ["art-2"])

    def test_resolve_display_prefers_active_override(self) -> None:
        now = display_controller._now()
        display_controller.save_state(
            {
                "mode": "temporary_override",
                "override": {
                    "artwork_id": "art-1",
                    "starts_at": now.isoformat(),
                    "ends_at": (now + timedelta(hours=1)).isoformat(),
                },
                "schedules": [],
            }
        )
        with (
            patch.object(display_controller, "_find_artwork", return_value=self.artwork),
            patch.object(display_controller, "_apply_display_behaviour", side_effect=lambda result, now: result),
        ):
            result = display_controller.resolve_display()
        self.assertEqual(result["mode"], "temporary_override")
        self.assertEqual(result["artwork"]["id"], "art-1")


if __name__ == "__main__":
    unittest.main()
