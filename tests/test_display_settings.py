from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import display_settings


class DisplaySettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.settings_file = Path(self.temp.name) / "settings.json"
        self.patcher = patch.object(display_settings, "SETTINGS_FILE", self.settings_file)
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.temp.cleanup()

    def test_save_settings_normalises_values(self) -> None:
        saved = display_settings.save_display_settings(
            {
                "rotation": 90,
                "transition": "slow_fade",
                "transition_seconds": 99,
                "poll_seconds": 1,
                "sleep_start": "23:00",
                "wake_time": "07:00",
            }
        )
        self.assertEqual(saved["rotation"], 90)
        self.assertEqual(saved["transition_seconds"], 5)
        self.assertEqual(saved["poll_seconds"], 2)

    def test_invalid_rotation_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Rotation must be"):
            display_settings.save_display_settings({"rotation": 180})

    def test_overnight_display_hours(self) -> None:
        settings = {
            **display_settings.DEFAULT_SETTINGS,
            "use_display_hours": True,
            "sleep_start": "23:00",
            "wake_time": "07:00",
        }
        asleep = datetime(2026, 7, 18, 1, 0, tzinfo=display_settings.LOCAL_TIMEZONE)
        awake = datetime(2026, 7, 18, 12, 0, tzinfo=display_settings.LOCAL_TIMEZONE)
        self.assertFalse(display_settings.is_within_display_hours(settings, asleep))
        self.assertTrue(display_settings.is_within_display_hours(settings, awake))


if __name__ == "__main__":
    unittest.main()
