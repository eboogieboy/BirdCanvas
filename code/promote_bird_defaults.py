#!/usr/bin/env python3
"""Promote the current bird-image replacements into persistent BirdCanvas defaults."""
from __future__ import annotations

import json

from bird_images import promote_tile_overrides_to_defaults


def main() -> int:
    result = promote_tile_overrides_to_defaults()
    print(json.dumps(result, indent=2))
    return 0 if result.get("promoted", 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
