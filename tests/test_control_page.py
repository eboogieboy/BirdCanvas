import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import display


class ControlPageTests(unittest.TestCase):
    def test_query_selector_helpers_are_distinct(self):
        html = display.CONTROL_HTML
        self.assertIn(
            "const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];",
            html,
        )
        self.assertNotIn(
            "const $=s=>document.querySelector(s),$=s=>[...document.querySelectorAll(s)];",
            html,
        )
        self.assertIn("$$('.panel').forEach", html)
        self.assertIn("$$('.nav').forEach", html)
        self.assertIn("$$('.chip').forEach", html)

    def test_birds_navigation_and_panel_are_present(self):
        html = display.CONTROL_HTML
        self.assertIn('data-go="birds"', html)
        self.assertIn('id="birds" class="panel"', html)
        self.assertIn("/api/birds/current", html)


if __name__ == "__main__":
    unittest.main()
