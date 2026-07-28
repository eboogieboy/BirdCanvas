from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO

from gallery_library import build_library
from presentation import DEFAULT_STYLE, create_gallery_presentation

ARCHIVE_DIR = Path("output/archive")
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_TYPES = {
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", b"RIFF"),
}


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned[:40] or "custom-artwork"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("The artwork manifest is damaged.") from error
    if not isinstance(value, dict):
        raise ValueError("The artwork manifest is invalid.")
    return value


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _manifest_path(artwork_id: str) -> Path:
    path = ARCHIVE_DIR / artwork_id / "manifest.json"
    if not path.is_file():
        raise ValueError("Artwork was not found.")
    return path


def _require_custom(manifest: dict[str, Any]) -> None:
    if manifest.get("collection") != "custom":
        raise ValueError("Only custom uploads can be edited or deleted here.")


def _validate_signature(content_type: str, first_bytes: bytes) -> None:
    expected = ALLOWED_TYPES[content_type][1]
    if content_type == "image/webp":
        if not (first_bytes.startswith(b"RIFF") and first_bytes[8:12] == b"WEBP"):
            raise ValueError("The uploaded file is not a valid WebP image.")
        return
    if not first_bytes.startswith(expected):
        raise ValueError("The uploaded file does not match its image type.")


def save_custom_artwork(
    file_stream: BinaryIO,
    filename: str,
    content_type: str,
    title: str,
    presentation_style: str = DEFAULT_STYLE,
) -> dict[str, Any]:
    if content_type not in ALLOWED_TYPES:
        raise ValueError("Please upload a JPG, PNG or WebP image.")

    title = title.strip() or Path(filename or "Custom artwork").stem or "Custom artwork"
    now = datetime.now().astimezone()
    timestamp = now.strftime("%Y%m%d-%H%M%S-%f")
    artwork_id = f"custom-{timestamp}-{_slug(title)}"
    extension = ALLOWED_TYPES[content_type][0]

    folder = ARCHIVE_DIR / artwork_id
    folder.mkdir(parents=True, exist_ok=False)
    original_path = folder / f"original{extension}"
    presented_path = folder / "artwork.png"

    total = 0
    first_chunk = file_stream.read(64 * 1024)
    if not first_chunk:
        shutil.rmtree(folder, ignore_errors=True)
        raise ValueError("The uploaded image is empty.")
    _validate_signature(content_type, first_chunk[:16])

    try:
        with original_path.open("wb") as output:
            output.write(first_chunk)
            total += len(first_chunk)
            while True:
                chunk = file_stream.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise ValueError("The image is larger than the 20 MB upload limit.")
                output.write(chunk)

        presentation = create_gallery_presentation(
            original_path,
            presented_path,
            style=presentation_style,
        )
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise

    manifest = {
        "schema_version": 1,
        "id": artwork_id,
        "provider": "upload",
        "collection": "custom",
        "title": title[:120],
        "created_at": now.isoformat(timespec="seconds"),
        "updated_at": now.isoformat(timespec="seconds"),
        "image": presented_path.name,
        "original_image": original_path.name,
        "source": "phone-upload",
        "original_filename": Path(filename or original_path.name).name,
        "species": [],
        "favourite": False,
        "hidden": False,
        "presentation": presentation,
    }
    _write_json(folder / "manifest.json", manifest)
    build_library()
    return manifest


def update_custom_artwork(artwork_id: str, *, title: str | None = None, favourite: bool | None = None, hidden: bool | None = None) -> dict[str, Any]:
    path = _manifest_path(artwork_id)
    manifest = _read_json(path)
    _require_custom(manifest)

    if title is not None:
        cleaned = title.strip()
        if not cleaned:
            raise ValueError("Title cannot be empty.")
        manifest["title"] = cleaned[:120]
    if favourite is not None:
        manifest["favourite"] = bool(favourite)
    if hidden is not None:
        manifest["hidden"] = bool(hidden)

    manifest["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _write_json(path, manifest)
    build_library()
    return manifest


def delete_custom_artwork(artwork_id: str) -> None:
    path = _manifest_path(artwork_id)
    manifest = _read_json(path)
    _require_custom(manifest)
    shutil.rmtree(path.parent)
    build_library()
