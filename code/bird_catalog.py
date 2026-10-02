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

# A useful day-one field-guide library. These are deliberately catalogue
# entries, not detections: "heard" remains false until BirdNET actually
# records the species.
STARTER_BIRDS = [
    ("Blackbird", "Turdus merula"),
    ("Blue Tit", "Cyanistes caeruleus"),
    ("Carrion Crow", "Corvus corone"),
    ("Chaffinch", "Fringilla coelebs"),
    ("Coal Tit", "Periparus ater"),
    ("Collared Dove", "Streptopelia decaocto"),
    ("Dunnock", "Prunella modularis"),
    ("Goldfinch", "Carduelis carduelis"),
    ("Great Tit", "Parus major"),
    ("Greenfinch", "Chloris chloris"),
    ("Herring Gull", "Larus argentatus"),
    ("House Sparrow", "Passer domesticus"),
    ("Jackdaw", "Coloeus monedula"),
    ("Long-tailed Tit", "Aegithalos caudatus"),
    ("Magpie", "Pica pica"),
    ("Robin", "Erithacus rubecula"),
    ("Song Thrush", "Turdus philomelos"),
    ("Starling", "Sturnus vulgaris"),
    ("Woodpigeon", "Columba palumbus"),
    ("Wren", "Troglodytes troglodytes"),
]


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
    """Return starter + observed species with local tile-health status."""
    stored = _load(path)
    observed = {
        key: item
        for key, item in stored["birds"].items()
        if isinstance(item, dict)
    }

    combined: dict[str, dict] = {}
    starter_keys = set()

    for name, scientific in STARTER_BIRDS:
        key = _key(name, scientific)
        starter_keys.add(key)
        combined[key] = {
            "name": name,
            "scientific_name": scientific,
            "first_seen": "",
            "last_seen": "",
        }

    # Real observations always win over the starter placeholder and new
    # species are added automatically as BirdNET encounters them.
    combined.update(observed)

    birds = []
    for key, item in combined.items():
        name = str(item.get("name", "")).strip()
        scientific = str(item.get("scientific_name", "")).strip()
        if not name:
            continue

        tile = mirror_tile_info(name, scientific)
        stat = tile["path"].stat()
        query = urlencode({
            "name": name,
            "scientific": scientific,
            "v": f"{tile['path'].name}-{stat.st_mtime_ns}-{stat.st_size}",
        })
        heard = key in observed and bool(item.get("first_seen") or item.get("last_seen"))
        birds.append(
            {
                "name": name,
                "scientific_name": scientific,
                "first_seen": item.get("first_seen") or None,
                "last_seen": item.get("last_seen") or None,
                "starter": key in starter_keys,
                "heard": heard,
                "image_url": f"/api/mirror/bird-image?{query}",
                "image_status": tile["status"],
                "image_ready": tile["status"] == "ready",
                "has_mapping": tile["has_mapping"],
                "artist": tile.get("artist") or "",
                "source_url": tile.get("source_url") or "",
                "problem": tile.get("problem") or "",
                "overridden": bool(tile.get("overridden")),
            }
        )

    birds.sort(key=lambda bird: bird["name"].casefold())
    missing = sum(1 for bird in birds if not bird["image_ready"])
    heard = sum(1 for bird in birds if bird["heard"])
    return {
        "species_count": len(birds),
        "starter_count": len(STARTER_BIRDS),
        "heard_count": heard,
        "ready_count": len(birds) - missing,
        "missing_count": missing,
        "birds": birds,
    }
