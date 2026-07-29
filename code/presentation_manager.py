from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from gallery_library import build_library
from presentation import STYLES, create_gallery_presentation
from paths import OUTPUT_DIR
ARCHIVE_DIR = OUTPUT_DIR / "archive"
CURRENT_DIR = OUTPUT_DIR / "current"
ALLOWED_PRESENTATION_MODES = {"auto", "white_mount", "black_mount", "no_mount"}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("The artwork manifest is damaged.") from error
    if not isinstance(value, dict):
        raise ValueError("The artwork manifest is invalid.")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _find_manifest(artwork_id: str) -> Path:
    for candidate in ARCHIVE_DIR.glob("*/manifest.json"):
        manifest = _read_json(candidate)
        if str(manifest.get("id", "")) == artwork_id:
            return candidate
    raise ValueError("Artwork was not found.")


def _original_path(folder: Path, manifest: dict[str, Any]) -> Path:
    original_name = str(manifest.get("original_image", "")).strip()
    if original_name:
        candidate = folder / original_name
        if candidate.is_file():
            return candidate

    # Compatibility with artwork created before originals were explicitly named.
    for pattern in ("original.*", "source.*"):
        for candidate in folder.glob(pattern):
            if candidate.is_file():
                return candidate

    image_name = str(manifest.get("image", "artwork.png"))
    candidate = folder / image_name
    if candidate.is_file():
        return candidate
    raise ValueError("The original artwork image could not be found.")


def apply_presentation(artwork_id: str, mode: str) -> dict[str, Any]:
    mode = str(mode).strip()
    if mode not in ALLOWED_PRESENTATION_MODES:
        raise ValueError("Mount must be Auto, White, Black or None.")

    manifest_path = _find_manifest(artwork_id)
    folder = manifest_path.parent
    manifest = _read_json(manifest_path)
    original = _original_path(folder, manifest)
    destination = folder / "artwork.png"

    presentation = create_gallery_presentation(
        original,
        destination,
        style=mode,
    )
    manifest["image"] = destination.name
    manifest["presentation"] = presentation
    manifest["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _write_json(manifest_path, manifest)

    current_manifest_path = CURRENT_DIR / "manifest.json"
    if current_manifest_path.is_file():
        current_manifest = _read_json(current_manifest_path)
        if str(current_manifest.get("id", "")) == artwork_id:
            CURRENT_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, CURRENT_DIR / "artwork.png")
            current_manifest.update(manifest)
            _write_json(current_manifest_path, current_manifest)

    build_library()
    return {
        "id": artwork_id,
        "presentation": presentation,
        "available_modes": sorted(ALLOWED_PRESENTATION_MODES),
    }
