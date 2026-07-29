import json
from pathlib import Path
from paths import DATA_DIR
FILE = DATA_DIR / "history.json"

MAX_HISTORY = 10


def load():

    if not FILE.exists():
        return []

    with open(FILE) as f:
        return json.load(f)


def save(history):

    FILE.parent.mkdir(exist_ok=True)

    with open(FILE, "w") as f:
        json.dump(history[-MAX_HISTORY:], f, indent=2)


def add(summary):

    history = load()

    history.append(summary)

    save(history)