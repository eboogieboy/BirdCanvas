"""Phone-editable BirdCanvas production settings."""
from __future__ import annotations

import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from paths import DATA_DIR

SETTINGS_FILE = DATA_DIR / "generation_settings.json"
TIMEZONE = ZoneInfo("Europe/London")
DEFAULTS = {"frequency": "daily", "excluded_birds": ["gull", "pigeon", "crow"]}
FREQUENCIES = {"daily", "twice_weekly", "weekly"}


def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return DEFAULTS.copy()
    value = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Generation settings must be an object")
    return validate(value)


def validate(value: dict) -> dict:
    frequency = value.get("frequency", DEFAULTS["frequency"])
    terms = value.get("excluded_birds", DEFAULTS["excluded_birds"])
    if frequency not in FREQUENCIES:
        raise ValueError("Choose daily, twice weekly, or weekly")
    if not isinstance(terms, list) or len(terms) > 100 or any(not isinstance(t, str) or not t.strip() or len(t) > 80 for t in terms):
        raise ValueError("Excluded birds must be a list of up to 100 names")
    return {"frequency": frequency, "excluded_birds": list(dict.fromkeys(t.strip().casefold() for t in terms))}


def save_settings(value: dict) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Settings must be an object")
    current = load_settings()
    current.update(value)
    result = validate(current)
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = SETTINGS_FILE.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, SETTINGS_FILE)
    return result


def excluded_birds() -> list[str]:
    return load_settings()["excluded_birds"]


def scheduled_boundary(now: datetime, frequency: str) -> datetime:
    """The most recent scheduled 04:00 boundary at or before now (UK time)."""
    local = now.astimezone(TIMEZONE)
    day = local.date()
    if local.hour < 4:
        day -= timedelta(days=1)
    while frequency == "weekly" and day.weekday() != 0 or frequency == "twice_weekly" and day.weekday() not in (0, 3):
        day -= timedelta(days=1)
    return datetime(day.year, day.month, day.day, 4, tzinfo=TIMEZONE)


def next_boundary(now: datetime, frequency: str) -> datetime:
    return _next(now, frequency)


def _next(now: datetime, frequency: str) -> datetime:
    local = now.astimezone(TIMEZONE)
    day = local.date()
    for offset in range(8):
        candidate_day = day + timedelta(days=offset)
        if frequency == "weekly" and candidate_day.weekday() != 0:
            continue
        if frequency == "twice_weekly" and candidate_day.weekday() not in (0, 3):
            continue
        candidate = datetime(candidate_day.year, candidate_day.month, candidate_day.day, 4, tzinfo=TIMEZONE)
        if candidate > local:
            return candidate
    raise RuntimeError("No next generation boundary")
