"""Regression tests for the gallery's curated artistic-style rotation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from art_style_rotation import STYLES, choose_style


class ArtStyleRotationTests(unittest.TestCase):
    def test_storybook_illustration_is_not_a_selectable_style(self):
        names = [name for name, _ in STYLES]
        self.assertNotIn("Storybook illustration", names)
        self.assertEqual(len(names), len(set(names)))

    def test_old_storybook_history_does_not_restore_removed_style(self):
        history = [
            {"art_style": "Pop art"},
            {"art_style": "Oil painting"},
            {"art_style": "Storybook illustration"},
        ]
        self.assertNotEqual(choose_style(history)["name"], "Storybook illustration")

    def test_rotates_art_families_and_includes_abstract_and_graphic_art(self):
        history = []
        families = []
        for _ in range(15):
            choice = choose_style(history)
            self.assertNotIn(choice["family"], families[-2:])
            families.append(choice["family"])
            history.append({"art_style": choice["name"]})
        self.assertIn("modern_graphic", families)
        self.assertIn("abstract_experimental", families)
        self.assertIn("atmospheric", families)

    def test_explicit_pop_art_and_geometric_abstraction(self):
        self.assertEqual(choose_style([], preferred_style="Pop art")["family"], "modern_graphic")
        self.assertEqual(
            choose_style([], preferred_style="Geometric abstraction")["family"],
            "abstract_experimental",
        )
        with self.assertRaises(ValueError):
            choose_style([], preferred_style="Storybook illustration")

    def test_all_selected_styles_remain_in_active_collection(self):
        history = []
        for _ in range(len(STYLES) * 2):
            selected = choose_style(history)["name"]
            self.assertIn(selected, {name for name, _ in STYLES})
            history.append({"art_style": selected})


if __name__ == "__main__":
    unittest.main()
