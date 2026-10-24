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

    def test_bird_page_distinguishes_collection_from_calendar_day(self):
        html = display.CONTROL_HTML
        self.assertIn("Birds heard or seen in this collection", html)
        self.assertIn("Since the last BirdCanvas artwork generation", html)
        self.assertIn("Daily birds", html)
        self.assertIn("midnight to midnight", html)
        self.assertIn("Current collection</button>", html)

    def test_manual_sighting_form_and_delete_are_present(self):
        html = display.CONTROL_HTML
        self.assertIn('id="bird-sighting-form"', html)
        self.assertIn('id="bird-sighting-options"', html)
        self.assertIn("/api/birds/sightings", html)
        self.assertIn("/api/birds/sightings/delete", html)
        self.assertIn("Seen manually", html)

    def test_bird_master_thumbnail_library_is_present(self):
        html = display.CONTROL_HTML
        self.assertIn('id="bird-catalog-grid"', html)
        self.assertIn("Field-guide library", html)
        self.assertIn("Missing images", html)
        self.assertIn("/api/birds/catalog", html)

    def test_bird_species_links_open_verified_rspb_profiles(self):
        html = display.CONTROL_HTML
        self.assertIn("bird.rspb_url", html)
        self.assertIn("card.href=rspb", html)
        self.assertIn("card.target='_blank'", html)
        self.assertIn("card.rel='noopener noreferrer'", html)
        self.assertIn('class=\"field-guide-species-link\"', html)
        self.assertIn('class=\"field-guide-rspb\"', html)
        self.assertIn('RSPB species guide', html)
        self.assertIn("data-bird-replace", html)
        self.assertIn("data-bird-restore", html)
    def test_heard_bird_thumbnail_shows_whole_illustration(self):
        html = display.CONTROL_HTML
        self.assertIn(
            ".bird-illustration{width:112px;height:112px;object-fit:contain;",
            html,
        )
        self.assertNotIn(
            ".bird-illustration{width:112px;height:112px;object-fit:cover;",
            html,
        )

    def test_field_guide_images_can_be_replaced_and_restored(self):
        html = display.CONTROL_HTML
        self.assertIn('id="bird-override-file"', html)
        self.assertIn("Replace", html)
        self.assertIn("Restore default", html)
        self.assertIn("/api/birds/illustration", html)
        self.assertIn("/api/birds/illustration/restore", html)

    def test_field_guide_changes_refresh_heard_bird_cards(self):
        html = display.CONTROL_HTML
        self.assertGreaterEqual(html.count("await refreshBirds();"), 2)
        self.assertIn("The bird list and Magic Mirror will pick it up automatically.", html)
        self.assertIn("[illustration.artist,illustration.license].filter(Boolean)", html)

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

    def test_gallery_detail_distinguishes_heard_and_featured_species(self):
        html = display.CONTROL_HTML
        self.assertIn("Featured in artwork", html)
        self.assertIn("Also heard", html)
        self.assertIn("species_detected", html)
        self.assertIn("species_used", html)

    def test_gallery_featured_bird_chips_do_not_inherit_home_hero_layout(self):
        html = display.CONTROL_HTML
        # The homepage .hero class has a 9:16 aspect ratio; never reuse it on
        # the featured-species chip group in the exhibition detail sheet.
        self.assertIn(".bird-role-list.featured span{background:#e9dfc8}", html)
        self.assertIn("['Featured in artwork',featured,'featured']", html)
        self.assertNotIn(".bird-role-list.hero span", html)
        self.assertNotIn("['Featured in artwork',featured,'hero']", html)

    def test_gallery_detail_has_send_to_tv_action(self):
        html = display.CONTROL_HTML
        self.assertIn('id="send-tv-button"', html)
        self.assertIn("Send to TV", html)
        self.assertIn("/api/artwork/send-to-frame", html)
        self.assertIn("Display in GalleryOS", html)


if __name__ == "__main__":
    unittest.main()
