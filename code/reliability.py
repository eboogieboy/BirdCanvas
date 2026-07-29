from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
from paths import BACKUP_DIR
from paths import DATA_DIR
from paths import OUTPUT_DIR

LOCAL_TIMEZONE = ZoneInfo("Europe/London")

LOG_DIR = Path("runtime/logs")
LAST_GOOD_FILE = DATA_DIR / "last_good_artwork.json"
VERSION_FILE = Path("VERSION")


def now_iso() -> str:
    return datetime.now(LOCAL_TIMEZONE).isoformat(timespec="seconds")


def log_event(level: str, message: str, details: dict[str, Any] | None = None) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": now_iso(), "level": level, "message": message, "details": details or {}}
    with (LOG_DIR / "canvasos.log").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_version() -> str:
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


def _disk_health() -> dict[str, Any]:
    usage = shutil.disk_usage(Path.cwd())
    free_mb = round(usage.free / (1024 * 1024))
    total_mb = round(usage.total / (1024 * 1024))
    used_percent = round((usage.used / usage.total) * 100, 1) if usage.total else 0
    return {"status": "ok" if free_mb >= 500 else "warning", "free_mb": free_mb, "total_mb": total_mb, "used_percent": used_percent}


def _json_file_health(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "ok", "exists": False, "path": str(path)}
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return {"status": "ok", "exists": True, "path": str(path)}
    except (OSError, json.JSONDecodeError) as error:
        return {"status": "error", "exists": True, "path": str(path), "message": str(error)}


def validate_image(path: Path) -> bool:
    if not path.exists() or not path.is_file(): return False
    try:
        from PIL import Image
        with Image.open(path) as image: image.verify()
        return True
    except Exception:
        try: return path.stat().st_size > 0
        except OSError: return False


def remember_last_good(artwork: dict[str, Any]) -> None:
    image_url = artwork.get("image_url") or artwork.get("_image_url")
    if not image_url: return
    payload = {"artwork_id": artwork.get("id"), "image_url": image_url, "title": artwork.get("title"), "recorded_at": now_iso()}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LAST_GOOD_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_last_good() -> dict[str, Any] | None:
    try:
        value = json.loads(LAST_GOOD_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError): return None


def health_report(current_status: dict[str, Any] | None = None) -> dict[str, Any]:
    artwork = (current_status or {}).get("artwork") if current_status else None
    artwork_health = {"status": "warning", "message": "No current artwork."}
    if isinstance(artwork, dict):
        image_url = artwork.get("image_url") or artwork.get("_image_url")
        if image_url:
            rel = str(image_url).lstrip("/")
            candidates = [Path(rel), OUTPUT_DIR / rel]
            local_path = next((p for p in candidates if p.exists()), candidates[-1])
            artwork_health = {"status": "ok" if validate_image(local_path) else "error", "artwork_id": artwork.get("id"), "image": str(local_path)}
        else:
            artwork_health = {"status": "error", "message": "No image URL."}
    checks = {
        "server": {"status": "ok"},
        "artwork": artwork_health,
        "state": _json_file_health(DATA_DIR / "galleryos_state.json"),
        "display_settings": _json_file_health(DATA_DIR / "display_settings.json"),
        "disk": _disk_health(),
    }
    overall = "error" if any(c.get("status") == "error" for c in checks.values()) else ("warning" if any(c.get("status") == "warning" for c in checks.values()) else "ok")
    return {"status": overall, "version": read_version(), "checked_at": now_iso(), "checks": checks}


def create_backup() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(LOCAL_TIMEZONE).strftime("%Y%m%d-%H%M%S")
    destination = BACKUP_DIR / f"canvasos-backup-{stamp}.zip"
    include = [
    DATA_DIR,
    OUTPUT_DIR / "archive",
    OUTPUT_DIR / "current",
    Path("VERSION"),
    Path("requirements.txt"),
]
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("backup-metadata.json", json.dumps({"created_at": now_iso(), "version": read_version(), "format": 1}, indent=2))
        for item in include:
            if item.is_file(): archive.write(item, item.as_posix())
            elif item.is_dir():
                for path in item.rglob("*"):
                    if path.is_file(): archive.write(path, path.as_posix())
    log_event("info", "Backup created", {"path": str(destination)})
    return destination


def create_diagnostics(current_status: dict[str, Any] | None = None) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(LOCAL_TIMEZONE).strftime("%Y%m%d-%H%M%S")
    destination = BACKUP_DIR / f"canvasos-diagnostics-{stamp}.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("health.json", json.dumps(health_report(current_status), indent=2))
        archive.writestr("display-status.json", json.dumps(current_status or {}, indent=2))
        for path in [DATA_DIR / "galleryos_state.json", DATA_DIR / "display_settings.json", LAST_GOOD_FILE, LOG_DIR / "canvasos.log", VERSION_FILE]:
            if path.exists() and path.is_file(): archive.write(path, path.as_posix())
    log_event("info", "Diagnostics package created", {"path": str(destination)})
    return destination
