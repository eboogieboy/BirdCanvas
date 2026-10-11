"""Regression tests for display-only local rarity labels."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from bird_rarity import rarity_for


class LocalRarityTests(unittest.TestCase):
    def test_common_garden_bird_is_labelled_locally(self):
        value = rarity_for("Eurasian Blackbird", "Turdus merula")
        self.assertEqual(value["level"], "common")
        self.assertEqual(value["label"], "Common")
        self.assertIn("North Tyneside", value["region"])

    def test_seasonal_bird_keeps_context(self):
        value = rarity_for("Redwing", "Turdus iliacus")
        self.assertEqual(value["level"], "common")
        self.assertIn("winter", value["context"])

    def test_less_regular_local_bird_is_uncommon(self):
        value = rarity_for("Grey Wagtail", "Motacilla cinerea")
        self.assertEqual(value["level"], "uncommon")

    def test_unfamiliar_bird_is_not_assigned_false_rare_label(self):
        value = rarity_for("Unexpected Bird", "Species not in catalogue")
        self.assertEqual(value["level"], "unrated")
        self.assertEqual(value["label"], "Unrated")

    def test_name_fallback_when_scientific_name_missing(self):
        self.assertEqual(rarity_for("Hooded Crow")["level"], "scarce")

    def test_scientific_name_takes_priority_over_common_name(self):
        self.assertEqual(rarity_for("Grey Wagtail", "Turdus merula")["level"], "common")


if __name__ == "__main__":
    unittest.main()
