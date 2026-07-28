from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path("output")
ARCHIVE_DIR = OUTPUT_DIR / "archive"
CURRENT_MANIFEST = OUTPUT_DIR / "current" / "manifest.json"
LIBRARY_DIR = OUTPUT_DIR / "gallery"
LIBRARY_FILE = LIBRARY_DIR / "library.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _find_manifest_path(artwork_id: str) -> Path | None:
    cleaned_id = str(artwork_id).strip()
    if not cleaned_id or not ARCHIVE_DIR.exists():
        return None
    for candidate in ARCHIVE_DIR.glob("*/manifest.json"):
        manifest = _read_json(candidate)
        if manifest and str(manifest.get("id", "")).strip() == cleaned_id:
            return candidate
    return None


def _directory_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total




def _exhibition_story(manifest: dict[str, Any], creative_brief: dict[str, Any], species: list[str]) -> dict[str, Any]:
    observation_date = str(manifest.get("observation_date", "")).strip()
    collection = str(creative_brief.get("collection", "")).strip()
    mood = str(manifest.get("mood", creative_brief.get("mood", ""))).strip()
    composition = str(creative_brief.get("composition", "")).strip()
    hero = [str(item) for item in creative_brief.get("hero_birds", []) if str(item).strip()]
    character = [str(item) for item in creative_brief.get("character_birds", []) if str(item).strip()]
    supporting = [str(item) for item in creative_brief.get("supporting_birds", []) if str(item).strip()]

    if species:
        visitors = ", ".join(species[:-1]) + (f" and {species[-1]}" if len(species) > 1 else species[0])
        opening = f"This BirdCanvas artwork preserves a garden visit by {visitors}."
    else:
        opening = "This early BirdCanvas artwork preserves a day in the garden, although the individual visitors were not recorded."

    emphasis = ""
    if hero:
        emphasis = f" The composition gives particular prominence to {', '.join(hero)}."
    atmosphere = f" Its atmosphere is {mood.rstrip('.').lower()}." if mood else ""
    narrative = opening + emphasis + atmosphere

    return {
        "narrative": narrative,
        "collection": collection,
        "composition": composition,
        "hero_birds": hero,
        "character_birds": character,
        "supporting_birds": supporting,
        "visitor_count": len(species),
        "observation_date": observation_date,
    }


def _normalise_manifest(manifest: dict[str, Any], folder_name: str) -> dict[str, Any] | None:
    artwork_id = str(manifest.get("id", "")).strip()
    image_name = str(manifest.get("image", "")).strip()
    created_at = str(manifest.get("created_at", "")).strip()
    image_path = ARCHIVE_DIR / folder_name / image_name
    if not artwork_id or not image_name or not created_at or not image_path.is_file():
        return None

    species = manifest.get("species", [])
    if not isinstance(species, list):
        species = []
    creative_brief = manifest.get("creative_brief", {})
    if not isinstance(creative_brief, dict):
        creative_brief = {}
    presentation = manifest.get("presentation", {})
    if not isinstance(presentation, dict):
        presentation = {}

    try:
        image_size_bytes = image_path.stat().st_size
    except OSError:
        image_size_bytes = 0

    return {
        "id": artwork_id,
        "collection": str(manifest.get("collection", "birdcanvas")),
        "title": str(manifest.get("title", artwork_id)),
        "observation_date": str(manifest.get("observation_date", "")),
        "created_at": created_at,
        "updated_at": str(manifest.get("updated_at", created_at)),
        "image": image_name,
        "image_url": f"../archive/{folder_name}/{image_name}",
        "image_size_bytes": image_size_bytes,
        "species": [str(item) for item in species],
        "season": str(manifest.get("season", "")),
        "style": str(manifest.get("style", creative_brief.get("visual_language", ""))),
        "palette": str(manifest.get("palette", creative_brief.get("palette", ""))),
        "mood": str(manifest.get("mood", creative_brief.get("mood", ""))),
        "creative_collection": str(creative_brief.get("collection", "")),
        "creative_brief": creative_brief,
        "notes": str(manifest.get("notes", "")),
        "source": str(manifest.get("source", "birdcanvas")),
        "favourite": bool(manifest.get("favourite", False)),
        "hidden": bool(manifest.get("hidden", False)),
        "presentation": presentation,
        "exhibition": _exhibition_story(manifest, creative_brief, [str(item) for item in species]),
        "provider": str(manifest.get("provider", manifest.get("source", "birdcanvas"))),
        "orientation": str(manifest.get("orientation", "")),
    }


def build_library() -> dict[str, Any]:
    artworks: list[dict[str, Any]] = []
    if ARCHIVE_DIR.exists():
        for manifest_path in ARCHIVE_DIR.glob("*/manifest.json"):
            manifest = _read_json(manifest_path)
            if not manifest:
                continue
            normalised = _normalise_manifest(manifest, manifest_path.parent.name)
            if normalised:
                artworks.append(normalised)

    artworks.sort(key=lambda item: item.get("created_at", ""), reverse=True)

    collections: dict[str, dict[str, Any]] = {}
    for artwork in artworks:
        collection_id = artwork["collection"]
        collection = collections.setdefault(
            collection_id,
            {
                "id": collection_id,
                "title": "BirdCanvas" if collection_id == "birdcanvas" else collection_id.replace("-", " ").title(),
                "count": 0,
                "latest_created_at": artwork["created_at"],
            },
        )
        collection["count"] += 1

    current = _read_json(CURRENT_MANIFEST) if CURRENT_MANIFEST.exists() else None
    payload = {
        "version": 3,
        "current_artwork_id": current.get("id") if current else None,
        "collections": list(collections.values()),
        "stats": {
            "artwork_count": len(artworks),
            "favourite_count": sum(1 for artwork in artworks if artwork["favourite"]),
            "hidden_count": sum(1 for artwork in artworks if artwork["hidden"]),
            "storage_bytes": _directory_size(ARCHIVE_DIR),
        },
        "artworks": artworks,
    }

    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    LIBRARY_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def update_artwork_metadata(
    artwork_id: str,
    *,
    title: str | None = None,
    favourite: bool | None = None,
    hidden: bool | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    manifest_path = _find_manifest_path(artwork_id)
    if manifest_path is None:
        raise ValueError("Artwork was not found.")
    manifest = _read_json(manifest_path)
    if manifest is None:
        raise ValueError("The artwork manifest is damaged.")

    if title is not None:
        cleaned = str(title).strip()
        if not cleaned:
            raise ValueError("Title cannot be empty.")
        manifest["title"] = cleaned[:120]
    if favourite is not None:
        manifest["favourite"] = bool(favourite)
    if hidden is not None:
        manifest["hidden"] = bool(hidden)
    if notes is not None:
        manifest["notes"] = str(notes).strip()[:2000]

    manifest["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    build_library()
    normalised = _normalise_manifest(manifest, manifest_path.parent.name)
    if normalised is None:
        raise ValueError("The updated artwork is invalid.")
    return normalised


def delete_artwork(artwork_id: str) -> dict[str, Any]:
    cleaned_id = str(artwork_id).strip()
    if not cleaned_id:
        raise ValueError("Artwork ID is required.")

    current = _read_json(CURRENT_MANIFEST) if CURRENT_MANIFEST.exists() else None
    current_id = str(current.get("id", "")).strip() if current else ""
    if current_id and cleaned_id == current_id:
        raise ValueError(
            "This is the current BirdCanvas artwork. "
            "Display or generate another current artwork before deleting it."
        )

    manifest_path = _find_manifest_path(cleaned_id)
    if manifest_path is None:
        raise ValueError("Artwork was not found.")
    manifest = _read_json(manifest_path)
    title = str(manifest.get("title", cleaned_id)) if manifest else cleaned_id

    try:
        shutil.rmtree(manifest_path.parent)
    except OSError as error:
        raise OSError(f"Artwork could not be deleted: {error}") from error

    return {"id": cleaned_id, "title": title, "library": build_library()}


if __name__ == "__main__":
    library = build_library()
    print(f"✓ Gallery library built with {len(library['artworks'])} artwork(s)")
    print("✓ Saved to output/gallery/library.json")
