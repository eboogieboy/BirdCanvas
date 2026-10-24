"""Human-observed bird sightings, separate from BirdNET-Go audio detections."""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from paths import DATA_DIR

LOCAL = ZoneInfo("Europe/London")
SIGHTINGS_PATH = DATA_DIR / "manual_sightings.json"
_LOCK = threading.RLock()


def list_sightings(*, path: Path | None = None) -> list[dict]:
    target = path or SIGHTINGS_PATH
    if not target.exists():
        return []
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Cannot read saved bird sightings; no changes were made.") from error
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("Saved bird sightings are invalid; no changes were made.")
    return value


def _save(items: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def add_sighting(
    name: str,
    scientific_name: str = "",
    *,
    now: datetime | None = None,
    path: Path | None = None,
) -> dict:
    target = path or SIGHTINGS_PATH
    name = " ".join(str(name).split())
    scientific_name = " ".join(str(scientific_name).split())
    if not 2 <= len(name) <= 90 or not any(char.isalpha() for char in name):
        raise ValueError("Enter a bird species name (2–90 characters).")
    if len(scientific_name) > 120:
        raise ValueError("Scientific name must be no longer than 120 characters.")
    moment = (now or datetime.now(LOCAL)).astimezone(LOCAL)
    date_string = moment.date().isoformat()
    with _LOCK:
        existing = list_sightings(path=target)
        for item in existing:
            if str(item.get("seen_at", ""))[:10] != date_string:
                continue
            same_name = str(item.get("name", "")).casefold() == name.casefold()
            same_scientific = bool(scientific_name) and (
                str(item.get("scientific_name", "")).casefold() == scientific_name.casefold()
            )
            if same_name or same_scientific:
                return {"sighting": item, "duplicate": True}
        item = {
            "id": uuid4().hex,
            "name": name,
            "scientific_name": scientific_name,
            "seen_at": moment.isoformat(timespec="seconds"),
        }
        existing.append(item)
        _save(existing, target)
    return {"sighting": item, "duplicate": False}


def delete_sighting(sighting_id: str, *, path: Path | None = None) -> None:
    if not sighting_id:
        raise ValueError("A sighting ID is required.")
    target = path or SIGHTINGS_PATH
    with _LOCK:
        existing = list_sightings(path=target)
        remaining = [item for item in existing if item.get("id") != sighting_id]
        if len(remaining) == len(existing):
            raise ValueError("Manual sighting not found.")
        _save(remaining, target)


def sightings_between(start: datetime, end: datetime, *, path: Path | None = None) -> list[dict]:
    window = []
    for item in list_sightings(path=path):
        try:
            moment = datetime.fromisoformat(str(item["seen_at"])).astimezone(LOCAL)
        except (KeyError, TypeError, ValueError):
            continue
        if start <= moment < end:
            window.append(item)
    return window
