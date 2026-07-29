from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from presentation import DEFAULT_STYLE, STYLES, create_gallery_presentation
from paths import OUTPUT_DIR
ARCHIVE_DIR = OUTPUT_DIR / "archive"
CURRENT_DIR = OUTPUT_DIR / "current"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def reframe_folder(folder: Path, style: str, force: bool = False) -> bool:
    manifest_path = folder / "manifest.json"
    manifest = _read_json(manifest_path)
    if not manifest:
        return False

    current_name = str(manifest.get("image", "")).strip()
    if not current_name:
        return False
    current_image = folder / current_name
    if not current_image.is_file():
        return False

    original_name = str(manifest.get("original_image", "")).strip()
    if original_name:
        original_image = folder / original_name
    else:
        suffix = current_image.suffix.lower() or ".png"
        original_image = folder / f"original{suffix}"
        if not original_image.exists():
            shutil.copy2(current_image, original_image)
        manifest["original_image"] = original_image.name

    presented_image = folder / "artwork.png"
    current_presentation = manifest.get("presentation", {})
    already_done = (
        isinstance(current_presentation, dict)
        and current_presentation.get("mode") == style
        and presented_image.is_file()
    )
    if already_done and not force:
        return False

    presentation = create_gallery_presentation(
        original_image,
        presented_image,
        style=style,
    )
    manifest["image"] = presented_image.name
    manifest["presentation"] = presentation
    manifest.setdefault("schema_version", 1)
    _write_json(manifest_path, manifest)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply an adaptive black, white or no-mount presentation."
    )
    parser.add_argument("--style", default=DEFAULT_STYLE, choices=sorted(STYLES))
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--collection",
        choices=["all", "birdcanvas", "custom"],
        default="all",
    )
    args = parser.parse_args()

    changed = 0
    skipped = 0
    decisions: dict[str, int] = {"white": 0, "black": 0, "none": 0}

    for manifest_path in sorted(ARCHIVE_DIR.glob("*/manifest.json")):
        manifest = _read_json(manifest_path)
        if not manifest:
            skipped += 1
            continue
        collection = str(manifest.get("collection", ""))
        if args.collection != "all" and collection != args.collection:
            continue
        if reframe_folder(manifest_path.parent, args.style, args.force):
            changed += 1
            updated = _read_json(manifest_path) or {}
            applied = updated.get("presentation", {}).get("applied_mount")
            if applied in decisions:
                decisions[applied] += 1
        else:
            skipped += 1

    current_manifest = _read_json(CURRENT_DIR / "manifest.json")
    if current_manifest:
        artwork_id = str(current_manifest.get("id", ""))
        archive_folder = ARCHIVE_DIR / artwork_id
        archive_manifest = _read_json(archive_folder / "manifest.json")
        if archive_manifest:
            image_name = str(archive_manifest.get("image", "artwork.png"))
            original_name = str(archive_manifest.get("original_image", "original.png"))
            if (archive_folder / image_name).is_file():
                shutil.copy2(archive_folder / image_name, CURRENT_DIR / "artwork.png")
            if (archive_folder / original_name).is_file():
                shutil.copy2(archive_folder / original_name, CURRENT_DIR / original_name)
            _write_json(CURRENT_DIR / "manifest.json", archive_manifest)

    from gallery_library import build_library
    build_library()

    print(f"✓ Updated {changed} artwork(s) using {STYLES[args.style]['name']}")
    if args.style == "auto":
        print(
            "✓ Automatic choices: "
            f"{decisions['white']} white, "
            f"{decisions['black']} black, "
            f"{decisions['none']} no mount"
        )
    print(f"✓ Skipped {skipped} artwork(s)")
    print("✓ Gallery library rebuilt")


if __name__ == "__main__":
    main()
