"""Live and historical BirdNET-Go session summaries for phone and Mirror clients."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from bird_images import display_illustration_for
from birdnet_go import _timestamp, detection_rows
from generation_settings import load_settings
from production_pipeline import status as production_status

LOCAL = ZoneInfo("Europe/London")


def _excluded(name: str, terms: list[str]) -> bool:
    folded = name.casefold()
    return any(term.casefold() in folded for term in terms)


def _display_name(name: str) -> str:
    """Use concise UK-facing common names without BirdNET's Eurasian prefix."""
    cleaned = str(name).strip()
    if cleaned.casefold().startswith("eurasian "):
        return cleaned[len("Eurasian "):].strip()
    return cleaned


def _summary(start: datetime, end: datetime, *, label: str, kind: str) -> dict:
    rows = detection_rows(start, end)
    excluded_terms = load_settings()["excluded_birds"]
    grouped: dict[str, dict] = {}

    for row in rows:
        raw_common = str(row.get("commonName") or row.get("scientificName") or "").strip()
        common = _display_name(raw_common)
        scientific = str(row.get("scientificName") or "").strip()
        if not common:
            continue
        key = scientific.casefold() or common.casefold()
        when = _timestamp(row)
        confidence = float(row.get("confidence", 0) or 0)
        item = grouped.setdefault(
            key,
            {
                "name": common,
                "scientific_name": scientific,
                "detections": 0,
                "first_heard": when,
                "last_heard": when,
                "max_confidence": confidence,
            },
        )
        item["detections"] += 1
        item["first_heard"] = min(item["first_heard"], when)
        item["last_heard"] = max(item["last_heard"], when)
        item["max_confidence"] = max(item["max_confidence"], confidence)

    birds = []
    for item in grouped.values():
        illustration = display_illustration_for(item["name"], item["scientific_name"])
        birds.append(
            {
                "name": item["name"],
                "scientific_name": item["scientific_name"],
                "detections": item["detections"],
                "first_heard": item["first_heard"].isoformat(timespec="seconds"),
                "last_heard": item["last_heard"].isoformat(timespec="seconds"),
                "max_confidence": round(item["max_confidence"], 3),
                "excluded_from_artwork": _excluded(item["name"], excluded_terms),
                "illustration": illustration,
            }
        )

    birds.sort(key=lambda item: item["last_heard"], reverse=True)

    return {
        "kind": kind,
        "label": label,
        "start": start.isoformat(timespec="seconds"),
        "end": end.isoformat(timespec="seconds"),
        "species_count": len(birds),
        "detections_total": len(rows),
        "last_detection": birds[0]["last_heard"] if birds else None,
        "birds": birds,
    }


def current_session(now: datetime | None = None) -> dict:
    now = (now or datetime.now(LOCAL)).astimezone(LOCAL)
    production = production_status(now=now, include_birds=False)
    start = datetime.fromisoformat(production["collecting_since"]).astimezone(LOCAL)
    result = _summary(start, now, label="Current collection", kind="current")
    result["next_generation"] = production["next_generation"]
    result["frequency"] = production["settings"]["frequency"]
    return result


def day_session(value: str, now: datetime | None = None) -> dict:
    try:
        requested = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Date must use YYYY-MM-DD.") from error

    now = (now or datetime.now(LOCAL)).astimezone(LOCAL)
    if requested > now.date():
        raise ValueError("Future dates are not available.")

    start = datetime.combine(requested, time.min, tzinfo=LOCAL)
    end = datetime.combine(requested + timedelta(days=1), time.min, tzinfo=LOCAL)
    if requested == now.date():
        end = now

    return _summary(
        start,
        end,
        label=requested.strftime("%-d %B %Y"),
        kind="day",
    )
