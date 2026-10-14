"""Incrementally cached visitor-frequency leaderboard from real BirdNET-Go records.

Read-only to BirdNET; never writes or alters detections, thresholds, or artwork.
Backfill happens in one daemon worker so slow historical API pages cannot block
the GalleryOS control page or interfere with production scheduling.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import birdnet_go
from paths import DATA_DIR, OUTPUT_DIR

LOCAL = ZoneInfo("Europe/London")
CACHE_DIR = DATA_DIR / "visitor_leaderboard"
CACHE_VERSION = 1
TODAY_TTL = timedelta(minutes=5)
HISTORY_TTL = timedelta(days=7)
PERIODS = {"7": 7, "30": 30, "90": 90, "all": None}
_LOCK = threading.Lock()
_REQUESTED: set[date] = set()
_RETRY_AFTER: dict[date, float] = {}
_RUNNING = False
_ACTIVE_DAY: date | None = None


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _observation_start(today: date) -> date:
    """Earliest evidenced BirdCanvas observation, not an invented install date."""
    candidates = []
    catalog = _read_json(DATA_DIR / "bird_catalog.json")
    if isinstance(catalog, dict) and isinstance(catalog.get("birds"), dict):
        for item in catalog["birds"].values():
            if isinstance(item, dict):
                value = str(item.get("first_seen") or "")[:10]
                try:
                    candidates.append(date.fromisoformat(value))
                except ValueError:
                    pass
    archive = OUTPUT_DIR / "archive"
    if archive.is_dir():
        for path in archive.glob("*/manifest.json"):
            manifest = _read_json(path)
            if isinstance(manifest, dict) and (
                manifest.get("generation_frequency") or manifest.get("observation_started_at")
            ):
                # Earlier hand-made artwork is not evidence BirdNET was recording.
                for field in ("observation_started_at", "observation_date"):
                    try:
                        candidates.append(date.fromisoformat(str(manifest.get(field) or "")[:10]))
                    except ValueError:
                        pass
    return min((d for d in candidates if d <= today), default=today)


def _cache_path(day: date) -> Path:
    return CACHE_DIR / "days" / f"{day.isoformat()}.json"


def _cached_day(day: date, now: datetime, minimum: float):
    value = _read_json(_cache_path(day))
    if not isinstance(value, dict) or value.get("version") != CACHE_VERSION:
        return None
    if value.get("date") != day.isoformat() or value.get("minimum_confidence") != minimum:
        return None
    if not isinstance(value.get("species"), list):
        return None
    try:
        checked = datetime.fromisoformat(value["checked_at"])
        if checked.tzinfo is None:
            return None
        # A snapshot taken while a day was still in progress cannot be
        # treated as a complete historical day after midnight.
        if day < now.date() and checked.date() == day:
            return None
        max_age = TODAY_TTL if day == now.date() else HISTORY_TTL
        if now - checked > max_age or now < checked - timedelta(minutes=5):
            return None
    except (ValueError, TypeError, KeyError):
        return None
    return value


def _calculate_day(day: date, minimum: float, now: datetime) -> dict:
    grouped = {}
    for record in birdnet_go._daily_rows(day):
        if birdnet_go._filter_reason(record, minimum) is not None:
            continue
        try:
            if birdnet_go._timestamp(record).date() != day:
                continue
        except (ValueError, KeyError, TypeError):
            continue
        raw = str(record.get("commonName") or record.get("scientificName") or "").strip()
        if not raw:
            continue
        name = raw[8:].strip() if raw.lower().startswith("eurasian ") else raw
        scientific = str(record.get("scientificName") or "").strip()
        key = (scientific or name).casefold()
        if key not in grouped:
            grouped[key] = {"name": name, "scientific_name": scientific, "detections": 0}
        grouped[key]["detections"] += 1
    return {
        "version": CACHE_VERSION,
        "date": day.isoformat(),
        "minimum_confidence": minimum,
        "checked_at": now.isoformat(timespec="seconds"),
        "species": list(grouped.values()),
    }


def _save_day(day: date, value: dict) -> None:
    path = _cache_path(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, path)


def _worker() -> None:
    global _RUNNING, _ACTIVE_DAY
    while True:
        with _LOCK:
            if not _REQUESTED:
                _ACTIVE_DAY = None
                _RUNNING = False
                return
            day = max(_REQUESTED)  # Most recent days first; prioritises the 7-day view.
            _REQUESTED.remove(day)
            _ACTIVE_DAY = day
        try:
            minimum = birdnet_go._minimum_confidence()
            _save_day(day, _calculate_day(day, minimum, datetime.now(LOCAL)))
            with _LOCK:
                _RETRY_AFTER.pop(day, None)
        except Exception:
            # Temporary BirdNET errors must not create an endless, expensive retry loop.
            with _LOCK:
                _RETRY_AFTER[day] = time.monotonic() + 300


def _request_missing(days: list[date]) -> None:
    global _RUNNING
    with _LOCK:
        for day in days:
            if day != _ACTIVE_DAY and time.monotonic() >= _RETRY_AFTER.get(day, 0):
                _REQUESTED.add(day)
        if _REQUESTED and not _RUNNING:
            _RUNNING = True
            threading.Thread(target=_worker, daemon=True, name="birdcanvas-visitor-stats").start()


def leaderboard(period: str = "30", now: datetime | None = None) -> dict:
    if period not in PERIODS:
        raise ValueError("Choose 7, 30, 90 or all.")
    now = (now or datetime.now(LOCAL)).astimezone(LOCAL)
    today = now.date()
    first = _observation_start(today)
    length = PERIODS[period]
    start = first if length is None else max(first, today - timedelta(days=length - 1))
    days = [start + timedelta(days=i) for i in range((today - start).days + 1)]
    minimum = birdnet_go._minimum_confidence()

    ready = []
    missing = []
    for day in days:
        cached = _cached_day(day, now, minimum)
        if cached is None:
            missing.append(day)
        else:
            ready.append(cached)
    if missing:
        _request_missing(missing)

    totals = {}
    for snapshot in ready:
        for bird in snapshot["species"]:
            name = str(bird.get("name") or "").strip()
            scientific = str(bird.get("scientific_name") or "").strip()
            if not name:
                continue
            key = (scientific or name).casefold()
            count = max(0, int(bird.get("detections") or 0))
            item = totals.setdefault(key, {
                "name": name, "scientific_name": scientific, "days_heard": 0, "detections": 0,
            })
            item["days_heard"] += 1
            item["detections"] += count
    analysed = len(ready)
    birds = sorted(totals.values(), key=lambda b: (-b["days_heard"], -b["detections"], b["name"].casefold()))
    for bird in birds:
        bird["visitor_score"] = round(100 * bird["days_heard"] / analysed) if analysed else 0

    with _LOCK:
        retrying = sum(1 for day in missing if _RETRY_AFTER.get(day, 0) > time.monotonic())
    return {
        "period": period,
        "from": start.isoformat(),
        "to": today.isoformat(),
        "minimum_confidence": minimum,
        "analysed_days": analysed,
        "total_days": len(days),
        "complete": not missing,
        "retrying_days": retrying,
        "birds": birds[:10],
        "total_species": len(birds),
    }
