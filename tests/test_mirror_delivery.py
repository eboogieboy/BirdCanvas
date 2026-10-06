import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

import mirror_delivery

TZ = ZoneInfo("Europe/London")


class MirrorDeliveryTests(unittest.TestCase):
    def test_delivers_changed_panel_and_skips_unchanged_signature(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            panel = root / "panel.jpg"
            meta = root / "panel.json"
            state = root / "delivery.json"
            panel.write_bytes(b"\xff\xd8birdcanvas\xff\xd9")
            meta.write_text(
                json.dumps({
                    "signature": "abc123",
                    "day": "2026-10-04",
                    "updated_at": "2026-10-04T08:00:00+01:00",
                }),
                encoding="utf-8",
            )

            response = MagicMock()
            response.status = 200
            response.read.return_value = b'{"ok": true}'
            response.__enter__.return_value = response
            response.__exit__.return_value = False

            with patch.dict(
                "os.environ",
                {
                    "BIRDCANVAS_MIRROR_PUSH_URL": "http://192.168.1.20:5050/api/birdcanvas-panel",
                    "BIRDCANVAS_MIRROR_PUSH_TOKEN": "x" * 32,
                },
                clear=False,
            ), patch.object(mirror_delivery, "PANEL_META", meta), \
                 patch.object(mirror_delivery, "STATE_PATH", state), \
                 patch.object(mirror_delivery, "build_mirror_panel", return_value=panel), \
                 patch.object(mirror_delivery, "urlopen", return_value=response) as opener:
                first = mirror_delivery.deliver(
                    now=datetime(2026, 10, 4, 8, 0, tzinfo=TZ)
                )
                second = mirror_delivery.deliver(
                    now=datetime(2026, 10, 4, 8, 1, tzinfo=TZ)
                )

            self.assertEqual(first["status"], "delivered")
            self.assertEqual(second["status"], "unchanged")
            self.assertEqual(opener.call_count, 1)
            self.assertEqual(
                mirror_delivery.build_mirror_panel.call_args_list[0].kwargs,
                {
                    "now": datetime(2026, 10, 4, 8, 0, tzinfo=TZ),
                    "width": 1200,
                    "height": 984,
                    "columns": 4,
                    "limit": 16,
                },
            )

            request = opener.call_args.args[0]
            self.assertEqual(request.get_header("Content-type"), "image/jpeg")
            self.assertEqual(request.get_header("X-birdcanvas-signature"), "abc123")
            self.assertEqual(request.get_header("X-birdcanvas-day"), "2026-10-04")
            self.assertEqual(
                request.get_header("Authorization"),
                "Bearer " + ("x" * 32),
            )

    def test_force_resends_same_panel(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            panel = root / "panel.jpg"
            meta = root / "panel.json"
            state = root / "delivery.json"
            panel.write_bytes(b"\xff\xd8same\xff\xd9")
            meta.write_text(
                json.dumps({
                    "signature": "same-signature",
                    "day": "2026-10-04",
                    "updated_at": "2026-10-04T09:00:00+01:00",
                }),
                encoding="utf-8",
            )
            state.write_text(
                json.dumps({
                    "signature": "same-signature",
                    "target": "http://mirror/api/birdcanvas-panel",
                }),
                encoding="utf-8",
            )

            response = MagicMock()
            response.status = 200
            response.read.return_value = b'{}'
            response.__enter__.return_value = response
            response.__exit__.return_value = False

            with patch.dict(
                "os.environ",
                {
                    "BIRDCANVAS_MIRROR_PUSH_URL": "http://mirror/api/birdcanvas-panel",
                    "BIRDCANVAS_MIRROR_PUSH_TOKEN": "y" * 32,
                },
                clear=False,
            ), patch.object(mirror_delivery, "PANEL_META", meta), \
                 patch.object(mirror_delivery, "STATE_PATH", state), \
                 patch.object(mirror_delivery, "build_mirror_panel", return_value=panel), \
                 patch.object(mirror_delivery, "urlopen", return_value=response) as opener:
                result = mirror_delivery.deliver(force=True)

            self.assertEqual(result["status"], "delivered")
            self.assertEqual(opener.call_count, 1)

    def test_missing_configuration_is_non_destructive(self):
        with patch.dict(
            "os.environ",
            {
                "BIRDCANVAS_MIRROR_PUSH_URL": "",
                "BIRDCANVAS_MIRROR_PUSH_TOKEN": "",
            },
            clear=False,
        ):
            result = mirror_delivery.deliver()

        self.assertEqual(result["status"], "not_configured")


if __name__ == "__main__":
    unittest.main()
