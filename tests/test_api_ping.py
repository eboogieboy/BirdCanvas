"""Deployment readiness must stay independent of potentially slow BirdNET/systemd probes."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from server import Handler


class ReadinessTests(unittest.TestCase):
    def test_ping_requires_no_external_checks(self):
        handler = Handler.__new__(Handler)
        handler.path = "/api/ping"
        handler.send_json = Mock()
        handler.do_GET()
        handler.send_json.assert_called_once_with({"ok": True})

    def test_auto_deploy_checks_ping_not_full_health(self):
        script = (ROOT / "deployment/auto-deploy.sh").read_text()
        self.assertIn("/api/ping", script)
        self.assertNotIn("8000/api/health", script)


if __name__ == "__main__":
    unittest.main()
