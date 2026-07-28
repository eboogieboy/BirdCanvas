import json
from pathlib import Path
from typing import List


class CreativeHistory:

    def __init__(self, filename: str = "data/creative_history.json"):
        self.path = Path(filename)

    def load(self) -> List[dict]:
        """Load the creative history."""

        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, history: List[dict]) -> None:
        """Save the creative history."""

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def recent(self, count: int = 10) -> List[dict]:
        """Return the most recent history entries."""

        return self.load()[-count:]

    def append(self, record: dict) -> None:
        """Add a new artwork record."""

        history = self.load()
        history.append(record)
        self.save(history)