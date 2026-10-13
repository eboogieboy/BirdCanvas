"""Read the BirdNET-Go detection ledger without copying it into BirdCanvas."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

LOCAL = ZoneInfo("Europe/London")


def base_url() -> str:
    return os.getenv("BIRDCANVAS_BIRDNET_URL", "http://127.0.0.1:8080").rstrip('/')


def _get(path: str, params: dict | None = None) -> dict:
    url = base_url() + path + ("?" + urlencode(params) if params else "")
    with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=12) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("Unexpected BirdNET-Go response")
    return value


def _timestamp(record: dict) -> datetime:
    value = record.get("timestamp")
    if value:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is not None:
            return parsed.astimezone(LOCAL)
    # Older BirdNET-Go installations expose separate station-local date/time.
    return datetime.fromisoformat(f'{record["date"]}T{record["time"]}').replace(tzinfo=LOCAL)


def _daily_rows(day) -> list[dict]:
    """Return every BirdNET-Go detection for one station-local calendar day."""
    rows: list[dict] = []
    offset = 0
    limit = 100
    date_text = day.isoformat()

    while True:
        page = _get(
            '/api/v2/detections',
            {
                "start_date": date_text,
                "end_date": date_text,
                "limit": limit,
                "offset": offset,
                "sortBy": "date_asc",
            },
        )
        page_rows = page.get("data")
        if not isinstance(page_rows, list) or not isinstance(page.get("total"), int):
            raise ValueError("BirdNET-Go returned an unexpected detections page")

        rows.extend(page_rows)
        offset += len(page_rows)

        if offset >= page["total"]:
            break
        if not page_rows or offset > 100000:
            raise RuntimeError(
                "BirdNET-Go pagination did not complete; collection remains pending"
            )

    return rows


def _window_rows(start: datetime, end: datetime) -> list[dict]:
    """Read all detections in [start, end) including below-threshold records."""
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError("A valid timezone-aware collection window is required")

    start, end = start.astimezone(LOCAL), end.astimezone(LOCAL)
    rows: list[dict] = []
    day = start.date()
    while day <= end.date():
        for row in _daily_rows(day):
            if start <= _timestamp(row) < end:
                rows.append(row)
        day += timedelta(days=1)

    rows.sort(key=_timestamp)
    return rows


def _minimum_confidence() -> float:
    minimum = float(os.getenv("BIRDCANVAS_MIN_CONFIDENCE", "0.5"))
    if not 0 <= minimum <= 1:
        raise ValueError("BIRDCANVAS_MIN_CONFIDENCE must be between 0 and 1")
    return minimum


def _filter_reason(row: dict, minimum: float) -> str | None:
    if str(row.get("verified", "")).casefold() in (
        "false_positive", "false positive", "rejected"
    ):
        return "rejected"
    if float(row.get("confidence", 0) or 0) < minimum:
        return "low_confidence"
    return None


def _activity_record(row: dict, minimum: float) -> dict:
    name = str(row.get("commonName") or row.get("scientificName") or "Unknown bird").strip()
    if name.casefold().startswith("eurasian "):
        name = name[len("Eurasian "):]
    reason = _filter_reason(row, minimum)
    return {
        "name": name,
        "timestamp": _timestamp(row).isoformat(timespec="seconds"),
        "confidence": float(row.get("confidence", 0) or 0),
        "filter_reason": reason,
        "accepted": reason is None,
    }


def detection_rows(start: datetime, end: datetime) -> list[dict]:
    """Return accepted BirdNET-Go rows for the exact [start, end) window."""
    minimum = _minimum_confidence()
    return [row for row in _window_rows(start, end)
            if _filter_reason(row, minimum) is None]


def detections(start: datetime, end: datetime) -> dict:
    """Read accepted birds and latest raw BirdNET-Go activity in one API pass."""
    minimum = _minimum_confidence()
    all_rows = _window_rows(start, end)
    accepted = [row for row in all_rows if _filter_reason(row, minimum) is None]
    species: dict[str, str] = {}
    for row in accepted:
        name = str(row.get("commonName") or row.get("scientificName") or "").strip()
        if name:
            species.setdefault(name.casefold(), name)

    last_accepted = accepted[-1] if accepted else None
    latest_raw = all_rows[-1] if all_rows else None
    return {
        "species": list(species.values()),
        "detections_total": len(accepted),
        "last_detection": _timestamp(last_accepted).isoformat() if last_accepted else None,
        "last_accepted_bird": _activity_record(last_accepted, minimum)
                              if last_accepted else None,
        "latest_birdnet_detection": _activity_record(latest_raw, minimum)
                                    if latest_raw else None,
        "minimum_confidence": minimum,
    }
