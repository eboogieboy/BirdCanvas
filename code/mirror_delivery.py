"""Push the current pre-rendered bird panel to the Magic Mirror Pi.

BirdCanvas remains the source of truth for today's selected species and image
composition. The Mirror receives one complete JPEG and stores it locally, so
the weather panel never needs a live BirdCanvas request while it is visible.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from mirror_panel import PANEL_META, build_mirror_panel
from paths import DATA_DIR

LOCAL = ZoneInfo("Europe/London")
STATE_PATH = DATA_DIR / "mirror_delivery.json"
DEFAULT_TIMEOUT_SECONDS = 15


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _target_url() -> str:
    return str(os.getenv("BIRDCANVAS_MIRROR_PUSH_URL", "")).strip()


def _token() -> str:
    return str(os.getenv("BIRDCANVAS_MIRROR_PUSH_TOKEN", "")).strip()


def deliver(*, force: bool = False, now: datetime | None = None) -> dict:
    """Build today's panel and deliver it only when the visible image changed."""
    target = _target_url()
    token = _token()

    if not target:
        return {"status": "not_configured", "reason": "BIRDCANVAS_MIRROR_PUSH_URL is empty"}
    if not token:
        return {"status": "not_configured", "reason": "BIRDCANVAS_MIRROR_PUSH_TOKEN is empty"}

    now = (now or datetime.now(LOCAL)).astimezone(LOCAL)
    panel_path = build_mirror_panel(
        now=now,
        width=1200,
        height=736,
        columns=4,
        limit=12,
    )
    metadata = _read_json(PANEL_META)
    signature = str(metadata.get("signature") or "").strip()
    day_key = str(metadata.get("day") or now.date().isoformat()).strip()
    updated_at = str(metadata.get("updated_at") or now.isoformat(timespec="seconds")).strip()

    if not signature:
        raise RuntimeError("Mirror panel metadata did not contain a signature")

    previous = _read_json(STATE_PATH)
    if (
        not force
        and previous.get("signature") == signature
        and previous.get("target") == target
    ):
        return {
            "status": "unchanged",
            "signature": signature,
            "day": day_key,
            "target": target,
        }

    payload = panel_path.read_bytes()
    request = Request(
        target,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "image/jpeg",
            "Content-Length": str(len(payload)),
            "X-BirdCanvas-Signature": signature,
            "X-BirdCanvas-Day": day_key,
            "X-BirdCanvas-Updated-At": updated_at,
            "User-Agent": "BirdCanvas-MirrorDelivery/1.0",
        },
    )

    timeout = max(
        3,
        min(
            60,
            int(os.getenv("BIRDCANVAS_MIRROR_PUSH_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)),
        ),
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(128 * 1024)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"MirrorDisplay returned HTTP {response.status}")
            try:
                reply = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                reply = {}
    except HTTPError as error:
        detail = error.read(4096).decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"MirrorDisplay returned HTTP {error.code}: {detail or error.reason}"
        ) from error
    except (URLError, TimeoutError, OSError) as error:
        raise RuntimeError(f"MirrorDisplay push failed: {error}") from error

    state = {
        "signature": signature,
        "day": day_key,
        "target": target,
        "delivered_at": datetime.now(LOCAL).isoformat(timespec="seconds"),
        "panel_bytes": len(payload),
        "mirror_reply": reply,
    }
    _write_json(STATE_PATH, state)

    return {
        "status": "delivered",
        "signature": signature,
        "day": day_key,
        "target": target,
        "panel_bytes": len(payload),
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    force = "--force" in argv
    try:
        result = deliver(force=force)
    except Exception as error:
        print(json.dumps({"status": "error", "error": str(error)}), flush=True)
        return 1

    print(json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
