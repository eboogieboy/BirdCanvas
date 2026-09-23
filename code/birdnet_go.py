"""Read the BirdNET-Go detection ledger without copying it into BirdCanvas."""
from __future__ import annotations

import json
import os
from datetime import datetime
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


def detections(start: datetime, end: datetime) -> dict:
    """[start, end); request full calendar days, then filter exact timestamps locally."""
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError("A valid timezone-aware collection window is required")
    start, end = start.astimezone(LOCAL), end.astimezone(LOCAL)
    minimum = float(os.getenv("BIRDCANVAS_MIN_CONFIDENCE", "0.5"))
    if not 0 <= minimum <= 1:
        raise ValueError("BIRDCANVAS_MIN_CONFIDENCE must be between 0 and 1")
    species: dict[str, str] = {}
    count = 0
    latest = None
    offset = 0
    limit = 100
    while True:
        page = _get('/api/v2/detections', {"start_date": start.date().isoformat(), "end_date": end.date().isoformat(), "limit": limit, "offset": offset, "sortBy": "date_asc"})
        rows = page.get("data")
        if not isinstance(rows, list) or not isinstance(page.get("total"), int):
            raise ValueError("BirdNET-Go returned an unexpected detections page")
        for row in rows:
            when = _timestamp(row)
            if not start <= when < end or float(row.get("confidence", 0)) < minimum:
                continue
            if str(row.get("verified", "")).casefold() in ("false_positive", "false positive", "rejected"):
                continue
            name = str(row.get("commonName") or row.get("scientificName") or "").strip()
            if name:
                species.setdefault(name.casefold(), name)
                count += 1
                if latest is None or when > latest:
                    latest = when
        offset += len(rows)
        if offset >= page["total"]:
            break
        if not rows or offset > 100000:
            raise RuntimeError("BirdNET-Go pagination did not complete; collection remains pending")
    return {"species": list(species.values()), "detections_total": count, "last_detection": latest.isoformat() if latest else None}
