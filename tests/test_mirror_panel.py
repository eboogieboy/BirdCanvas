import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

import mirror_panel

TZ = ZoneInfo("Europe/London")


class MirrorPanelTests(unittest.TestCase):
    def test_builds_four_by_four_capable_jpeg_with_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tiles = {}
            for index, name in enumerate(("Blackbird", "Robin", "Wren")):
                path = root / f"tile-{index}.jpg"
                Image.new("RGB", (600, 600), (230 - index * 10, 225, 215)).save(path, "JPEG")
                tiles[name] = path

            birds = [
                {"name": "Blackbird", "scientific_name": "Turdus merula"},
                {"name": "Robin", "scientific_name": "Erithacus rubecula"},
                {"name": "Wren", "scientific_name": "Troglodytes troglodytes"},
            ]
            selected = (
                datetime(2026, 10, 3, 9, tzinfo=TZ),
                {"start": "2026-10-03T04:00:00+01:00"},
                birds,
            )

            with patch.object(mirror_panel, "selected_birds", return_value=selected), \
                 patch.object(mirror_panel, "record_birds") as record, \
                 patch.object(mirror_panel, "mirror_tile_path", side_effect=lambda name, scientific="": tiles[name]):
                path = mirror_panel.build_mirror_panel(
                    width=1200,
                    height=984,
                    columns=4,
                    limit=16,
                    output_dir=root / "panel",
                )

            self.assertTrue(path.is_file())
            with Image.open(path) as image:
                self.assertEqual(image.size, (1200, 984))
                self.assertEqual(image.format, "JPEG")

            meta = json.loads((root / "panel" / "panel.json").read_text())
            self.assertEqual(meta["columns"], 4)
            self.assertEqual(meta["slots"], 16)
            self.assertEqual(meta["birds"], ["Blackbird", "Robin", "Wren"])
            record.assert_called_once_with(birds)

    def test_grid_shape_expands_small_species_counts(self):
        self.assertEqual(mirror_panel._grid_shape(1, 4), (1, 1))
        self.assertEqual(mirror_panel._grid_shape(2, 4), (2, 1))
        self.assertEqual(mirror_panel._grid_shape(3, 4), (3, 1))
        self.assertEqual(mirror_panel._grid_shape(4, 4), (4, 1))
        self.assertEqual(mirror_panel._grid_shape(5, 4), (4, 2))
        self.assertEqual(mirror_panel._grid_shape(8, 4), (4, 2))
        self.assertEqual(mirror_panel._grid_shape(12, 4), (4, 3))
        self.assertEqual(mirror_panel._grid_shape(16, 4), (4, 4))

    def test_short_bird_name_stays_on_one_line(self):
        image = Image.new("RGB", (600, 300), "black")
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        label, font = mirror_panel._fit_label(draw, "Blue Tit", 220, 46)
        self.assertEqual(label, "Blue Tit")
        self.assertGreaterEqual(getattr(font, "size", 20), 40)

    def test_long_bird_name_can_wrap_before_shrinking(self):
        image = Image.new("RGB", (600, 300), "black")
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        label, font = mirror_panel._fit_label(draw, "Black-headed Gull", 220, 46)
        self.assertIn("\n", label)
        self.assertGreaterEqual(getattr(font, "size", 20), 26)

    def test_panel_font_is_scalable(self):
        font = mirror_panel._font(38, bold=True)
        self.assertGreaterEqual(getattr(font, "size", 38), 36)

    def test_renderer_version_change_invalidates_cached_panel(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tile = root / "blackbird.jpg"
            Image.new("RGB", (600, 600), "white").save(tile, "JPEG")
            selected = (
                datetime(2026, 10, 3, 9, tzinfo=TZ),
                {"start": "2026-10-03T04:00:00+01:00"},
                [{"name": "Blackbird", "scientific_name": "Turdus merula"}],
            )

            with patch.object(mirror_panel, "selected_birds", return_value=selected), \
                 patch.object(mirror_panel, "record_birds"), \
                 patch.object(mirror_panel, "mirror_tile_path", return_value=tile):
                mirror_panel.build_mirror_panel(output_dir=root / "panel")
                with patch.object(mirror_panel, "PANEL_RENDER_VERSION", mirror_panel.PANEL_RENDER_VERSION + 1), \
                     patch.object(mirror_panel, "_render", wraps=mirror_panel._render) as render:
                    mirror_panel.build_mirror_panel(output_dir=root / "panel")

            self.assertEqual(render.call_count, 1)

    def test_reuses_cached_panel_when_species_and_tiles_are_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tile = root / "blackbird.jpg"
            Image.new("RGB", (600, 600), "white").save(tile, "JPEG")
            selected = (
                datetime(2026, 10, 3, 9, tzinfo=TZ),
                {"start": "2026-10-03T04:00:00+01:00"},
                [{"name": "Blackbird", "scientific_name": "Turdus merula"}],
            )

            with patch.object(mirror_panel, "selected_birds", return_value=selected), \
                 patch.object(mirror_panel, "record_birds"), \
                 patch.object(mirror_panel, "mirror_tile_path", return_value=tile):
                first = mirror_panel.build_mirror_panel(output_dir=root / "panel")
                with patch.object(mirror_panel, "_render", side_effect=AssertionError("panel was rebuilt")):
                    second = mirror_panel.build_mirror_panel(output_dir=root / "panel")

            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
