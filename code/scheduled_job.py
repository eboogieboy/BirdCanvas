from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

from artwork_store import publish_artwork
from compose import compose
from display import build_display_page
from storage import get_birds, load_yesterday

SLOTS = {
    "morning": {
        "source": "yesterday",
        "window": "Previous calendar day",
    },
    "midday": {
        "source": "today",
        "window": "Today, midnight to 12:00",
    },
    "evening": {
        "source": "today",
        "window": "Today, midnight to 17:00",
    },
}


def birds_for_slot(slot: str) -> tuple[list[str], str]:
    settings = SLOTS[slot]
    if settings["source"] == "yesterday":
        data = load_yesterday()
        return list(data.get("birds", [])), str(data.get("date", ""))

    return list(get_birds()), date.today().isoformat()


def expected_observation_date(slot: str) -> str:
    if slot == "morning":
        return (date.today() - timedelta(days=1)).isoformat()
    return date.today().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one scheduled BirdCanvas edition.")
    parser.add_argument("slot", choices=sorted(SLOTS))
    args = parser.parse_args()

    birds, observation_date = birds_for_slot(args.slot)
    if not observation_date:
        observation_date = expected_observation_date(args.slot)

    if not birds:
        print(f"No birds available for the {args.slot} edition. Existing artwork remains on display.")
        return 0

    window = SLOTS[args.slot]["window"]
    result = compose(
        source=SLOTS[args.slot]["source"],
        birds=birds,
        edition=args.slot,
        observation_window=window,
    )
    if not result:
        print("Artwork was not created. Existing artwork remains on display.")
        return 1

    manifest = publish_artwork(
        source_image=Path(result["output"]),
        observation_date=observation_date,
        birds=result["birds"],
        brief=result["brief"],
        edition=args.slot,
        observation_window=window,
    )
    build_display_page()

    print(f"✓ {args.slot.title()} BirdCanvas edition complete")
    print(f"✓ Current artwork: output/current/{manifest['image']}")
    print(f"✓ Archived artwork: output/archive/{manifest['id']}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
