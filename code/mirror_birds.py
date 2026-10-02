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


def mirror_birds(now: datetime | None = None, limit: int = DEFAULT_TILE_LIMIT) -> dict:
    now = (now or datetime.now(LOCAL)).astimezone(LOCAL)
    session = current_session(now)

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = DEFAULT_TILE_LIMIT
    limit = min(max(limit, 1), 24)

    # Choose the most recently heard species first so a busy day cannot hide
    # new arrivals, then alphabetise that selected set for a stable grid.
    recent = list(session.get("birds", []))[:limit]
    selected = sorted(recent, key=lambda bird: str(bird.get("name", "")).casefold())

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
