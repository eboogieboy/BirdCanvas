from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from gallery_library import build_library

LOCAL_TIMEZONE = ZoneInfo("Europe/London")
CURRENT_MANIFEST = Path("output/current/manifest.json")
CURRENT_DIR = Path("output/current")
EXPECTED_READY_TIME = time(hour=6, minute=0)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        parsed = parsed.astimezone(LOCAL_TIMEZONE)
    return parsed


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _image_revision(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError:
        return "missing"
    return f"{stat.st_mtime_ns}-{stat.st_size}"


def _normalise_archive_url(artwork: dict[str, Any]) -> dict[str, Any]:
    result = dict(artwork)
    url = str(result.get("image_url", ""))
    result["image_url"] = f"/{url.removeprefix('../').removeprefix('/')}"
    relative = result["image_url"].split("?", 1)[0].lstrip("/")
    path = Path("output") / relative
    result["display_revision"] = _image_revision(path)
    return result


def current_manifest_artwork() -> dict[str, Any] | None:
    manifest = _read_json(CURRENT_MANIFEST)
    if not manifest:
        return None

    collection = str(manifest.get("collection", "birdcanvas")).lower()
    provider = str(manifest.get("provider", "birdcanvas")).lower()
    if collection != "birdcanvas" and provider != "birdcanvas":
        return None

    image_name = str(manifest.get("image", "artwork.png"))
    image_path = CURRENT_DIR / image_name
    if not image_path.is_file() or image_path.stat().st_size == 0:
        return None

    return {
        "id": manifest.get("id", "current-birdcanvas"),
        "title": manifest.get("title", "BirdCanvas"),
        "collection": "birdcanvas",
        "provider": "birdcanvas",
        "image_url": f"/current/{image_name}",
        "display_revision": _image_revision(image_path),
        "observation_date": manifest.get("observation_date", ""),
        "created_at": manifest.get("created_at", ""),
        "species": [
            str(item)
            for item in manifest.get("species", [])
            if isinstance(item, (str, int, float))
        ],
    }


def archived_birdcanvas_artworks() -> list[dict[str, Any]]:
    library = build_library()
    artworks = []

    for item in library.get("artworks", []):
        if not isinstance(item, dict):
            continue
        if item.get("hidden", False):
            continue
        collection = str(item.get("collection", "")).lower()
        provider = str(item.get("provider", "")).lower()
        if collection != "birdcanvas" and provider != "birdcanvas":
            continue
        if not item.get("image_url"):
            continue
        artworks.append(_normalise_archive_url(item))

    def sort_key(item: dict[str, Any]) -> tuple[datetime, str]:
        created = _parse_datetime(item.get("created_at"))
        observed = _parse_date(item.get("observation_date"))
        if created is None and observed is not None:
            created = datetime.combine(
                observed,
                time.min,
                tzinfo=LOCAL_TIMEZONE,
            )
        return (
            created or datetime.min.replace(tzinfo=LOCAL_TIMEZONE),
            str(item.get("id", "")),
        )

    artworks.sort(key=sort_key, reverse=True)
    return artworks


def newest_valid_birdcanvas() -> tuple[dict[str, Any] | None, str]:
    current = current_manifest_artwork()
    if current:
        return current, "current"

    archived = archived_birdcanvas_artworks()
    if archived:
        return archived[0], "archive_fallback"

    return None, "unavailable"


def assurance_status(
    artwork: dict[str, Any] | None,
    source: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    local_now = now or datetime.now(LOCAL_TIMEZONE)
    expected_observation_date = local_now.date() - timedelta(days=1)

    observation_date = (
        _parse_date(artwork.get("observation_date"))
        if isinstance(artwork, dict)
        else None
    )
    created_at = (
        _parse_datetime(artwork.get("created_at"))
        if isinstance(artwork, dict)
        else None
    )

    expected_ready_at = datetime.combine(
        local_now.date(),
        EXPECTED_READY_TIME,
        tzinfo=LOCAL_TIMEZONE,
    )

    if artwork is None:
        status = "missing"
        message = "No valid BirdCanvas artwork is available."
    elif source == "archive_fallback":
        status = "fallback"
        message = "The latest valid archived BirdCanvas artwork is being used."
    elif (
        local_now >= expected_ready_at
        and observation_date is not None
        and observation_date < expected_observation_date
    ):
        status = "late"
        message = (
            "A new daily BirdCanvas artwork has not arrived yet. "
            "The most recent valid artwork remains on display."
        )
    else:
        status = "current"
        message = "The current BirdCanvas artwork is on display."

    return {
        "status": status,
        "message": message,
        "source": source,
        "expected_observation_date": expected_observation_date.isoformat(),
        "observation_date": (
            observation_date.isoformat() if observation_date else None
        ),
        "created_at": created_at.isoformat() if created_at else None,
        "checked_at": local_now.isoformat(timespec="seconds"),
    }
