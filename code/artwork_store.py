from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from presentation import DEFAULT_STYLE, create_gallery_presentation

OUTPUT_DIR = Path("output")
CURRENT_DIR = OUTPUT_DIR / "current"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LEGACY_IMAGE = OUTPUT_DIR / "final_scene.png"


def _safe_date(value: str) -> str:
    value = (value or "").strip()
    if len(value) == 10 and value[4] == "-" and value[7] == "-":
        return value
    return datetime.now().date().isoformat()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return slug or "daily"


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def publish_artwork(
    source_image: Path,
    observation_date: str,
    birds: list[str],
    brief: dict,
    presentation_style: str = DEFAULT_STYLE,
    edition: str = "daily",
    title: str | None = None,
    observation_window: str = "",
) -> dict:
    if not source_image.exists():
        raise FileNotFoundError(f"Artwork image not found: {source_image}")

    date_text = _safe_date(observation_date)
    edition_slug = _safe_slug(edition)
    artwork_id = f"birdcanvas-{date_text}-{edition_slug}"
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")

    archive_folder = ARCHIVE_DIR / artwork_id
    archive_folder.mkdir(parents=True, exist_ok=True)
    original_path = archive_folder / "original.png"
    presented_path = archive_folder / "artwork.png"
    shutil.copy2(source_image, original_path)
    presentation = create_gallery_presentation(
        original_path,
        presented_path,
        style=presentation_style,
    )

    edition_names = {
        "morning": "Morning Exhibition",
        "midday": "Midday Exhibition",
        "evening": "Evening Exhibition",
        "daily": "Garden Birds",
    }
    default_title = f"{edition_names.get(edition_slug, 'Garden Birds')} — {date_text}"

    manifest = {
        "schema_version": 2,
        "id": artwork_id,
        "provider": "birdcanvas",
        "collection": "birdcanvas",
        "title": title or default_title,
        "observation_date": date_text,
        "observation_window": observation_window,
        "edition": edition_slug,
        "created_at": created_at,
        "image": "artwork.png",
        "original_image": "original.png",
        "orientation": "portrait",
        "species": [str(bird) for bird in birds],
        "season": "",
        "style": brief.get("visual_language", ""),
        "palette": brief.get("palette", ""),
        "mood": brief.get("mood", ""),
        "favourite": False,
        "hidden": False,
        "creative_brief": brief,
        "presentation": presentation,
    }

    _write_json(archive_folder / "manifest.json", manifest)

    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(presented_path, CURRENT_DIR / "artwork.png")
    shutil.copy2(original_path, CURRENT_DIR / "original.png")
    _write_json(CURRENT_DIR / "manifest.json", manifest)

    from gallery_library import build_library

    build_library()
    return manifest


def migrate_legacy_artwork() -> bool:
    if not LEGACY_IMAGE.exists():
        return False

    current_image = CURRENT_DIR / "artwork.png"
    if current_image.exists():
        return False

    created_at = datetime.fromtimestamp(LEGACY_IMAGE.stat().st_mtime).astimezone()
    date_text = created_at.date().isoformat()

    publish_artwork(
        source_image=LEGACY_IMAGE,
        observation_date=date_text,
        birds=[],
        brief={"note": "Migrated from output/final_scene.png"},
        edition="legacy",
    )
    return True
