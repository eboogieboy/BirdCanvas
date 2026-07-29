from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from gallery_library import build_library
from display_settings import load_display_settings, is_within_display_hours
from reliability import load_last_good, log_event, remember_last_good
from current_artwork import assurance_status, newest_valid_birdcanvas
from paths import OUTPUT_DIR

STATE_FILE = Path("data/galleryos_state.json")
CURRENT_MANIFEST = OUTPUT_DIR / "current" / "manifest.json"
SCHEDULE_LIMIT = 100
LOCAL_TIMEZONE = ZoneInfo("Europe/London")


def _now() -> datetime:
    return datetime.now(LOCAL_TIMEZONE)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def default_state() -> dict[str, Any]:
    return {"mode": "automatic", "override": None, "schedules": []}


def load_state() -> dict[str, Any]:
    saved = _read_json(STATE_FILE) or {}
    schedules = saved.get("schedules", [])
    if not isinstance(schedules, list):
        schedules = []
    return {
        "mode": saved.get("mode", "automatic"),
        "override": saved.get("override"),
        "schedules": schedules,
    }


def save_state(state: dict[str, Any]) -> None:
    _write_json(STATE_FILE, state)


def _parse_datetime(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError("Use a valid date and time.") from error
    if parsed.tzinfo is None:
        # datetime-local values contain no timezone. Treat them as UK local time,
        # regardless of the Codespace or Raspberry Pi system timezone.
        parsed = parsed.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        parsed = parsed.astimezone(LOCAL_TIMEZONE)
    return parsed


def _find_artwork(artwork_id: str, include_hidden: bool = False) -> dict[str, Any] | None:
    library = build_library()
    for artwork in library.get("artworks", []):
        if artwork.get("id") == artwork_id and (include_hidden or not artwork.get("hidden", False)):
            return artwork
    return None


def _image_revision(image_url: str) -> str:
    """Return a stable cache-busting revision for an image served from output/."""
    relative = image_url.split("?", 1)[0].lstrip("/")
    path = OUTPUT_DIR / relative
    try:
        stat = path.stat()
    except OSError:
        return "missing"
    return f"{stat.st_mtime_ns}-{stat.st_size}"


def _with_display_revision(artwork: dict[str, Any]) -> dict[str, Any]:
    result = dict(artwork)
    image_url = str(result.get("image_url", ""))
    result["display_revision"] = _image_revision(image_url)
    return result


def _normalise_archive_url(artwork: dict[str, Any]) -> dict[str, Any]:
    result = dict(artwork)
    url = str(result.get("image_url", ""))
    result["image_url"] = f"/{url.removeprefix('../').removeprefix('/')}"
    return _with_display_revision(result)


def _automatic_artwork() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    artwork, source = newest_valid_birdcanvas()
    return artwork, assurance_status(artwork, source)


def _clean_state(state: dict[str, Any], now: datetime) -> dict[str, Any]:
    changed = False
    override = state.get("override")
    if isinstance(override, dict):
        try:
            ends_at = _parse_datetime(override.get("ends_at"))
        except ValueError:
            ends_at = now
        if ends_at <= now or not _find_artwork(str(override.get("artwork_id", ""))):
            state["override"] = None
            state["mode"] = "automatic"
            changed = True

    valid_schedules = []
    for schedule in state.get("schedules", []):
        if not isinstance(schedule, dict):
            changed = True
            continue
        try:
            ends_at = _parse_datetime(schedule.get("ends_at"))
        except ValueError:
            changed = True
            continue
        if ends_at <= now or not _find_artwork(str(schedule.get("artwork_id", "")), include_hidden=True):
            changed = True
            continue
        valid_schedules.append(schedule)
    state["schedules"] = valid_schedules

    if changed:
        save_state(state)
    return state


def _apply_display_behaviour(
    result: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    settings = load_display_settings()
    screen_on = is_within_display_hours(settings, now)

    if (
        not screen_on
        and settings.get("wake_for_overrides", True)
        and result.get("mode") in {"temporary_override", "scheduled"}
    ):
        screen_on = True

    artwork = result.get("artwork")
    if isinstance(artwork, dict):
        if str(artwork.get("collection", "")).lower() == "birdcanvas":
            remember_last_good(artwork)
    elif result.get("mode") == "automatic":
        fallback = load_last_good()
        if fallback:
            result["artwork"] = {
                "id": fallback.get("artwork_id", "last-good-birdcanvas"),
                "title": fallback.get("title", "Last valid BirdCanvas artwork"),
                "collection": "birdcanvas",
                "image_url": fallback.get("image_url"),
                "display_revision": fallback.get("recorded_at"),
            }
            result["mode"] = "fallback"
            result["assurance"] = {
                "status": "fallback",
                "message": "The last known valid BirdCanvas artwork is being used.",
                "source": "last_known_good",
            }
            log_event("warning", "Using last known valid BirdCanvas artwork")
    result["display_settings"] = settings
    result["screen_on"] = screen_on
    return result


def resolve_display() -> dict[str, Any]:
    now = _now()
    state = _clean_state(load_state(), now)

    override = state.get("override")
    if isinstance(override, dict):
        artwork = _find_artwork(str(override.get("artwork_id", "")))
        if artwork:
            return _apply_display_behaviour(
                {
                    "mode": "temporary_override",
                    "artwork": _normalise_archive_url(artwork),
                    "override": override,
                    "schedule": None,
                    "server_time": now.isoformat(timespec="seconds"),
                },
                now,
            )

    active = []
    for schedule in state.get("schedules", []):
        try:
            starts_at = _parse_datetime(schedule.get("starts_at"))
            ends_at = _parse_datetime(schedule.get("ends_at"))
        except ValueError:
            continue
        if starts_at <= now < ends_at:
            active.append((starts_at, schedule))

    if active:
        _, schedule = max(active, key=lambda item: item[0])
        artwork = _find_artwork(str(schedule.get("artwork_id", "")))
        if artwork:
            return _apply_display_behaviour(
                {
                    "mode": "scheduled",
                    "artwork": _normalise_archive_url(artwork),
                    "override": None,
                    "schedule": schedule,
                    "server_time": now.isoformat(timespec="seconds"),
                },
                now,
            )

    automatic_artwork, assurance = _automatic_artwork()
    return _apply_display_behaviour(
        {
            "mode": "automatic",
            "artwork": automatic_artwork,
            "assurance": assurance,
            "override": None,
            "schedule": None,
            "server_time": now.isoformat(timespec="seconds"),
        },
        now,
    )


def set_temporary_override(artwork_id: str, duration_minutes: int) -> dict[str, Any]:
    artwork = _find_artwork(artwork_id)
    if not artwork:
        raise ValueError("Artwork was not found or is hidden.")
    if duration_minutes < 1 or duration_minutes > 10080:
        raise ValueError("Duration must be between 1 minute and 7 days.")

    starts_at = _now()
    ends_at = starts_at + timedelta(minutes=duration_minutes)
    state = load_state()
    state["mode"] = "temporary_override"
    state["override"] = {
        "artwork_id": artwork_id,
        "starts_at": starts_at.isoformat(timespec="seconds"),
        "ends_at": ends_at.isoformat(timespec="seconds"),
    }
    save_state(state)
    return resolve_display()


def cancel_override() -> dict[str, Any]:
    state = load_state()
    state["mode"] = "automatic"
    state["override"] = None
    save_state(state)
    return resolve_display()


def list_schedules() -> list[dict[str, Any]]:
    now = _now()
    state = _clean_state(load_state(), now)
    result = []
    for schedule in state.get("schedules", []):
        artwork = _find_artwork(str(schedule.get("artwork_id", "")), include_hidden=True)
        if not artwork:
            continue
        result.append({**schedule, "artwork": _normalise_archive_url(artwork)})
    return sorted(result, key=lambda item: item.get("starts_at", ""))


def create_schedule(artwork_id: str, starts_at_text: str, ends_at_text: str) -> dict[str, Any]:
    if not _find_artwork(artwork_id):
        raise ValueError("Artwork was not found or is hidden.")
    starts_at = _parse_datetime(starts_at_text)
    ends_at = _parse_datetime(ends_at_text)
    if ends_at <= starts_at:
        raise ValueError("End time must be after the start time.")
    if ends_at <= _now():
        raise ValueError("The scheduled end time must be in the future.")
    if ends_at - starts_at > timedelta(days=31):
        raise ValueError("A schedule can run for up to 31 days.")

    state = load_state()
    if len(state.get("schedules", [])) >= SCHEDULE_LIMIT:
        raise ValueError("The schedule limit has been reached.")

    created = _now()
    schedule = {
        "id": f"schedule-{created.strftime('%Y%m%d-%H%M%S-%f')}",
        "artwork_id": artwork_id,
        "starts_at": starts_at.isoformat(timespec="seconds"),
        "ends_at": ends_at.isoformat(timespec="seconds"),
        "created_at": created.isoformat(timespec="seconds"),
    }
    state.setdefault("schedules", []).append(schedule)
    save_state(state)
    return schedule


def delete_schedule(schedule_id: str) -> None:
    state = load_state()
    original = state.get("schedules", [])
    filtered = [item for item in original if item.get("id") != schedule_id]
    if len(filtered) == len(original):
        raise ValueError("Schedule was not found.")
    state["schedules"] = filtered
    save_state(state)


def remove_artwork_references(artwork_id: str) -> None:
    state = load_state()
    override = state.get("override")
    if isinstance(override, dict) and override.get("artwork_id") == artwork_id:
        state["override"] = None
        state["mode"] = "automatic"
    state["schedules"] = [item for item in state.get("schedules", []) if item.get("artwork_id") != artwork_id]
    save_state(state)
