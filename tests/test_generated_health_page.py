"""Regression tests for the canonical generated BirdCanvas control page."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import display
import reliability


class GeneratedPageTests(unittest.TestCase):
    def test_page_generator_uses_live_release_and_health_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(display, "OUTPUT_DIR", Path(tmp) / "output"), \
             patch.object(display, "migrate_legacy_artwork"), \
             patch.object(display, "build_library"):
            display.build_display_page()
            page = (Path(tmp) / "output/control/index.html").read_text()
        version = (ROOT / "VERSION").read_text().strip()
        self.assertIn(f"<div class=\"version\">v{version}</div>", page)
        self.assertNotIn("__BIRDCANVAS_VERSION__", page)
        self.assertIn("if(id==='system')refreshHealth()", page)
        self.assertIn("refresh();refreshGeneration();refreshHealth()", page)
        self.assertIn("id=\"health-overview\"", page)
        self.assertIn("thumbnail_url||a.image_url", page)
        self.assertIn("controller.abort()", page)
        self.assertIn("data-go=\"birds\"", page)

    def test_health_probe_is_limited_and_responds_to_errors(self):
        response = io.BytesIO(json.dumps({"data": [], "total": 0}).encode())
        with patch.object(reliability, "urlopen", return_value=response) as opener:
            result = reliability._birdnet_health()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(opener.call_args.kwargs.get("timeout"), 3)
        self.assertIn("limit=1", opener.call_args.args[0].full_url)

        with patch.object(reliability, "urlopen", side_effect=TimeoutError("slow")):
            result = reliability._birdnet_health()
        self.assertEqual(result["status"], "warning")


if __name__ == "__main__":
    unittest.main()
