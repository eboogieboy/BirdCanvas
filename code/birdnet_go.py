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


def detection_rows(start: datetime, end: datetime) -> list[dict]:
    """Return accepted BirdNET-Go rows for the exact [start, end) window."""
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError("A valid timezone-aware collection window is required")

    start, end = start.astimezone(LOCAL), end.astimezone(LOCAL)
    minimum = float(os.getenv("BIRDCANVAS_MIN_CONFIDENCE", "0.5"))
    if not 0 <= minimum <= 1:
        raise ValueError("BIRDCANVAS_MIN_CONFIDENCE must be between 0 and 1")

    accepted: list[dict] = []
    day = start.date()
    final_day = end.date()
    while day <= final_day:
        for row in _daily_rows(day):
            when = _timestamp(row)
            if not start <= when < end or float(row.get("confidence", 0)) < minimum:
                continue
            if str(row.get("verified", "")).casefold() in (
                "false_positive",
                "false positive",
                "rejected",
            ):
                continue
            accepted.append(row)
        day += timedelta(days=1)

    accepted.sort(key=_timestamp)
    return accepted


def detections(start: datetime, end: datetime) -> dict:
    """Read [start, end), querying BirdNET-Go one calendar day at a time."""
    rows = detection_rows(start, end)
    species: dict[str, str] = {}
    latest = None

    for row in rows:
        when = _timestamp(row)
        name = str(row.get("commonName") or row.get("scientificName") or "").strip()
        if name:
            species.setdefault(name.casefold(), name)
            if latest is None or when > latest:
                latest = when

    return {
        "species": list(species.values()),
        "detections_total": len(rows),
        "last_detection": latest.isoformat() if latest else None,
    }
