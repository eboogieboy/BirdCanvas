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


if __name__ == "__main__":
    unittest.main()
