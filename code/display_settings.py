from __future__ import annotations

import json
from datetime import datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SETTINGS_FILE = Path("data/display_settings.json")
LOCAL_TIMEZONE = ZoneInfo("Europe/London")

DEFAULT_SETTINGS: dict[str, Any] = {
    "enabled": True,
    "sleep_start": "23:00",
    "wake_time": "07:00",
    "use_display_hours": False,
    "wake_for_overrides": True,
    "rotation": 0,
    "transition": "fade",
    "transition_seconds": 1.1,
    "fit_mode": "contain",
    "background": "black",
    "poll_seconds": 5,
}

VALID_TRANSITIONS = {"fade", "slow_fade", "cut"}
VALID_FIT_MODES = {"contain", "cover"}
VALID_BACKGROUNDS = {"black", "soft_black", "white"}


def _normalise_time(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = time.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field_name} must be a valid time.") from error
    return parsed.strftime("%H:%M")


def _normalise_rotation(value: Any) -> int:
    try:
        rotation = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Rotation must be 0, 90 or 270 degrees.") from error
    if rotation not in {0, 90, 270}:
        raise ValueError("Rotation must be 0, 90 or 270 degrees.")
    return rotation


def _choice(value: Any, allowed: set[str], default: str, field: str) -> str:
    choice = str(value or default).strip()
    if choice not in allowed:
        raise ValueError(f"{field} has an unsupported value.")
    return choice


def _seconds(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return round(max(minimum, min(maximum, number)), 2)


def _integer(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def load_display_settings() -> dict[str, Any]:
    saved: dict[str, Any] = {}
    if SETTINGS_FILE.exists():
        try:
            value = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                saved = value
        except (OSError, json.JSONDecodeError):
            saved = {}

    settings = {**DEFAULT_SETTINGS, **saved}

    try:
        settings["sleep_start"] = _normalise_time(
            settings["sleep_start"], "Sleep start"
        )
        settings["wake_time"] = _normalise_time(
            settings["wake_time"], "Wake time"
        )
        settings["rotation"] = _normalise_rotation(settings["rotation"])
        settings["transition"] = _choice(
            settings["transition"],
            VALID_TRANSITIONS,
            DEFAULT_SETTINGS["transition"],
            "Transition",
        )
        settings["fit_mode"] = _choice(
            settings["fit_mode"],
            VALID_FIT_MODES,
            DEFAULT_SETTINGS["fit_mode"],
            "Fit mode",
        )
        settings["background"] = _choice(
            settings["background"],
            VALID_BACKGROUNDS,
            DEFAULT_SETTINGS["background"],
            "Background",
        )
    except ValueError:
        settings = dict(DEFAULT_SETTINGS)

    settings["enabled"] = bool(settings.get("enabled", True))
    settings["use_display_hours"] = bool(
        settings.get("use_display_hours", False)
    )
    settings["wake_for_overrides"] = bool(
        settings.get("wake_for_overrides", True)
    )
    settings["transition_seconds"] = _seconds(
        settings.get("transition_seconds"),
        DEFAULT_SETTINGS["transition_seconds"],
        0,
        5,
    )
    settings["poll_seconds"] = _integer(
        settings.get("poll_seconds"),
        DEFAULT_SETTINGS["poll_seconds"],
        2,
        60,
    )
    return settings


def save_display_settings(payload: dict[str, Any]) -> dict[str, Any]:
    current = load_display_settings()

    transition = _choice(
        payload.get("transition", current["transition"]),
        VALID_TRANSITIONS,
        current["transition"],
        "Transition",
    )

    default_duration = {
        "cut": 0,
        "fade": 1.1,
        "slow_fade": 2.5,
    }[transition]

    updated = {
        "enabled": bool(payload.get("enabled", current["enabled"])),
        "sleep_start": _normalise_time(
            payload.get("sleep_start", current["sleep_start"]),
            "Sleep start",
        ),
        "wake_time": _normalise_time(
            payload.get("wake_time", current["wake_time"]),
            "Wake time",
        ),
        "use_display_hours": bool(
            payload.get("use_display_hours", current["use_display_hours"])
        ),
        "wake_for_overrides": bool(
            payload.get(
                "wake_for_overrides",
                current["wake_for_overrides"],
            )
        ),
        "rotation": _normalise_rotation(
            payload.get("rotation", current["rotation"])
        ),
        "transition": transition,
        "transition_seconds": _seconds(
            payload.get("transition_seconds", default_duration),
            default_duration,
            0,
            5,
        ),
        "fit_mode": _choice(
            payload.get("fit_mode", current["fit_mode"]),
            VALID_FIT_MODES,
            current["fit_mode"],
            "Fit mode",
        ),
        "background": _choice(
            payload.get("background", current["background"]),
            VALID_BACKGROUNDS,
            current["background"],
            "Background",
        ),
        "poll_seconds": _integer(
            payload.get("poll_seconds", current["poll_seconds"]),
            current["poll_seconds"],
            2,
            60,
        ),
    }

    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(updated, indent=2) + "\n",
        encoding="utf-8",
    )
    return updated


def is_within_display_hours(
    settings: dict[str, Any],
    now: datetime | None = None,
) -> bool:
    if not settings.get("enabled", True):
        return False
    if not settings.get("use_display_hours", False):
        return True

    local_now = now or datetime.now(LOCAL_TIMEZONE)
    current = local_now.timetz().replace(tzinfo=None)
    sleep_start = time.fromisoformat(str(settings["sleep_start"]))
    wake_time = time.fromisoformat(str(settings["wake_time"]))

    if sleep_start == wake_time:
        return True

    if sleep_start > wake_time:
        sleeping = current >= sleep_start or current < wake_time
    else:
        sleeping = sleep_start <= current < wake_time

    return not sleeping
