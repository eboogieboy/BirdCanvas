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
            "const $=s=>document.querySelector(s),qa=s=>[...document.querySelectorAll(s)];",
            html,
        )
        self.assertNotIn(
            "const $=s=>document.querySelector(s),$=s=>[...document.querySelectorAll(s)];",
            html,
        )
        self.assertIn("qa('.panel').forEach", html)
        self.assertIn("qa('.nav').forEach", html)
        self.assertIn("qa('.chip').forEach", html)

    def test_birds_navigation_and_panel_are_present(self):
        html = display.CONTROL_HTML
        self.assertIn('data-go="birds"', html)
        self.assertIn('id="birds" class="panel"', html)
        self.assertIn("/api/birds/current", html)

    def test_bird_master_thumbnail_library_is_present(self):
        html = display.CONTROL_HTML
        self.assertIn('id="bird-catalog-grid"', html)
        self.assertIn("Field-guide library", html)
        self.assertIn("Missing images", html)
        self.assertIn("/api/birds/catalog", html)

    def test_field_guide_images_can_be_replaced_and_restored(self):
        html = display.CONTROL_HTML
        self.assertIn('id="bird-override-file"', html)
        self.assertIn("Replace", html)
        self.assertIn("Restore default", html)
        self.assertIn("/api/birds/illustration", html)
        self.assertIn("/api/birds/illustration/restore", html)

    def test_legacy_birdnet_import_is_not_shown_on_control_page(self):
        html = display.CONTROL_HTML
        self.assertNotIn('data-go="birdnet"', html)
        self.assertNotIn('id="birdnet" class="panel"', html)
        self.assertNotIn("$('#birdnet-form')", html)
        self.assertNotIn("$('#generate-artwork-button')", html)

    def test_gallery_uses_portrait_frame_proportions(self):
        html = display.CONTROL_HTML
        self.assertIn("aspect-ratio:9/16", html)
        self.assertIn("class=\"home-overview\"", html)
        self.assertIn("Portrait display", html)
        self.assertIn("BirdCanvas Gallery", html)

    def test_gallery_detail_has_send_to_tv_action(self):
        html = display.CONTROL_HTML
        self.assertIn('id="send-tv-button"', html)
        self.assertIn("Send to TV", html)
        self.assertIn("/api/artwork/send-to-frame", html)
        self.assertIn("Display in GalleryOS", html)


if __name__ == "__main__":
    unittest.main()
