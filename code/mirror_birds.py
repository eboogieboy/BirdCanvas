"""Small, display-ready bird feed for the Magic Mirror.

BirdCanvas owns all selection and ordering logic. The Mirror only needs to
render the returned name and local image URL.
"""
from __future__ import annotations

from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from bird_sessions import current_session

LOCAL = ZoneInfo("Europe/London")
DEFAULT_TILE_LIMIT = 12


def _normalise_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = DEFAULT_TILE_LIMIT
    return min(max(value, 1), 24)


def selected_birds(now: datetime | None = None, limit: int = DEFAULT_TILE_LIMIT) -> tuple[datetime, dict, list[dict]]:
    """Return the selected species for Mirror clients.

    Selection is recency-based so new arrivals can displace older species when
    the collection exceeds the tile limit. The chosen set is then sorted
    alphabetically to keep the visible grid stable and easy to scan.
    """
    now = (now or datetime.now(LOCAL)).astimezone(LOCAL)
    session = current_session(now)
    limit = _normalise_limit(limit)
    recent = list(session.get("birds", []))[:limit]
    selected = sorted(recent, key=lambda bird: str(bird.get("name", "")).casefold())
    return now, session, selected


def mirror_birds(now: datetime | None = None, limit: int = DEFAULT_TILE_LIMIT) -> dict:
    now, session, selected = selected_birds(now=now, limit=limit)
    limit = _normalise_limit(limit)

    birds = []
    for bird in selected:
        name = str(bird.get("name", "")).strip()
        scientific = str(bird.get("scientific_name", "")).strip()
        if not name:
            continue
        query = urlencode({"name": name, "scientific": scientific})
        birds.append(
            {
                "name": name,
                "image_url": f"/api/mirror/bird-image?{query}",
            }
        )

    return {
        "updated_at": now.isoformat(timespec="seconds"),
        "collection_start": session.get("start"),
        "species_count": session.get("species_count", 0),
        "tiles_returned": len(birds),
        "max_tiles": limit,
        "order": "alphabetical",
        "selection": "most_recent_species",
        "birds": birds,
    }
