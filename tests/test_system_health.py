from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import system_health


class SystemHealthTests(unittest.TestCase):
    def test_successful_backup_and_mirror_jobs_are_healthy(self):
        timestamp = (datetime.now(ZoneInfo("Europe/London")) - timedelta(hours=2)).strftime("%a %Y-%m-%d %H:%M:%S BST")

        def run(*args):
            if args[0] == "list-unit-files":
                return "birdcanvas-mirror-push.timer enabled\nbirdcanvas-backup.timer enabled\n"
            unit = args[1]
            if unit.endswith(".timer"):
                return "LoadState=loaded\nActiveState=active\n"
            return f"LoadState=loaded\nResult=success\nExecMainStatus=0\nExecMainExitTimestamp={timestamp}\n"

        with patch.object(system_health, "_run", side_effect=run):
            checks = system_health.delivery_checks()
        self.assertEqual(checks["backup"]["status"], "ok")
        self.assertEqual(checks["mirror"]["status"], "ok")

    def test_failed_backup_is_not_displayed_as_healthy(self):
        def run(*args):
            if args[1].endswith(".timer"):
                return "LoadState=loaded\nActiveState=active\n"
            return "LoadState=loaded\nResult=exit-code\nExecMainStatus=1\n"
        with patch.object(system_health, "_run", side_effect=run):
            value = system_health._job("birdcanvas-backup.timer", "birdcanvas-backup.service", "Backup")
        self.assertEqual(value["status"], "error")

    def test_unmonitored_mirror_is_not_falsely_green(self):
        with patch.object(system_health, "_run", return_value=""):
            self.assertEqual(system_health.delivery_checks()["mirror"]["status"], "unknown")

    def test_cpu_temperature_reading_in_celsius(self):
        with patch.object(system_health, "CPU_TEMP_PATH") as sensor:
            sensor.read_text.return_value = "51500\n"
            reading = system_health.cpu_temperature_check()
        self.assertEqual(reading["status"], "ok")
        self.assertEqual(reading["celsius"], 51.5)
        self.assertIn("51.5°C", reading["message"])

    def test_cpu_temperature_warning_and_hot_thresholds(self):
        for milli_celsius, expected in [(69999, "ok"), (70000, "warning"), (79999, "warning"), (80000, "error")]:
            with self.subTest(milli_celsius=milli_celsius), patch.object(system_health, "CPU_TEMP_PATH") as sensor:
                sensor.read_text.return_value = str(milli_celsius)
                self.assertEqual(system_health.cpu_temperature_check()["status"], expected)

    def test_cpu_temperature_sensor_unavailable(self):
        with patch.object(system_health, "CPU_TEMP_PATH") as sensor:
            sensor.read_text.side_effect = OSError("unavailable")
            reading = system_health.cpu_temperature_check()
        self.assertEqual(reading["status"], "unknown")
        self.assertIn("unavailable", reading["message"])

    def test_cpu_temperature_invalid_sensor_value(self):
        with patch.object(system_health, "CPU_TEMP_PATH") as sensor:
            sensor.read_text.return_value = "not a temperature"
            reading = system_health.cpu_temperature_check()
        self.assertEqual(reading["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
