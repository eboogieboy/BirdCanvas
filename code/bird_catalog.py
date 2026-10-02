"""Persistent field-guide catalogue of bird species BirdCanvas has encountered."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from bird_images import mirror_tile_info
from paths import DATA_DIR

LOCAL = ZoneInfo("Europe/London")
CATALOG_PATH = DATA_DIR / "bird_catalog.json"


def _load(path: Path = CATALOG_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"birds": {}}
    if not isinstance(value, dict) or not isinstance(value.get("birds"), dict):
        return {"birds": {}}
    return value


def _save(value: dict, path: Path = CATALOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _key(name: str, scientific_name: str) -> str:
    scientific = str(scientific_name).strip().casefold()
    if scientific:
        return f"scientific:{scientific}"
    return f"name:{str(name).strip().casefold()}"


def record_birds(birds: list[dict], *, path: Path = CATALOG_PATH) -> None:
    """Merge observed species into the persistent catalogue without inflating counts."""
    if not birds:
        return

    catalog = _load(path)
    entries = catalog["birds"]
    changed = False

    for bird in birds:
        name = str(bird.get("name", "")).strip()
        scientific = str(bird.get("scientific_name", "")).strip()
        if not name:
            continue

        first_seen = str(bird.get("first_heard") or bird.get("last_heard") or "").strip()
        last_seen = str(bird.get("last_heard") or bird.get("first_heard") or "").strip()
        key = _key(name, scientific)
        existing = entries.get(key) if isinstance(entries.get(key), dict) else {}

        merged = {
            "name": name,
            "scientific_name": scientific,
            "first_seen": min(
                [value for value in (str(existing.get("first_seen", "")).strip(), first_seen) if value],
                default=first_seen,
            ),
            "last_seen": max(
                [value for value in (str(existing.get("last_seen", "")).strip(), last_seen) if value],
                default=last_seen,
            ),
        }

        if merged != existing:
            entries[key] = merged
            changed = True

    if changed:
        catalog["updated_at"] = datetime.now(LOCAL).isoformat(timespec="seconds")
        _save(catalog, path)


def catalogue(*, path: Path = CATALOG_PATH) -> dict:
    """Return every observed species with its local tile-health status."""
    stored = _load(path)
    birds = []

    for item in stored["birds"].values():
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        scientific = str(item.get("scientific_name", "")).strip()
        if not name:
            continue

        tile = mirror_tile_info(name, scientific)
        query = urlencode({
            "name": name,
            "scientific": scientific,
            "v": tile["path"].name,
        })
        birds.append(
            {
                "name": name,
                "scientific_name": scientific,
                "first_seen": item.get("first_seen"),
                "last_seen": item.get("last_seen"),
                "image_url": f"/api/mirror/bird-image?{query}",
                "image_status": tile["status"],
                "image_ready": tile["status"] == "ready",
                "has_mapping": tile["has_mapping"],
                "artist": tile.get("artist") or "",
                "source_url": tile.get("source_url") or "",
                "problem": tile.get("problem") or "",
            }
        )

    birds.sort(key=lambda bird: bird["name"].casefold())
    missing = sum(1 for bird in birds if not bird["image_ready"])
    return {
        "species_count": len(birds),
        "ready_count": len(birds) - missing,
        "missing_count": missing,
        "birds": birds,
    }
