import json
from datetime import date
from pathlib import Path
from paths import DATA_DIR
TODAY_FILE = DATA_DIR / "today.json"
YESTERDAY_FILE = DATA_DIR / "yesterday.json"


def _today():
    return str(date.today())


def empty_today():
    return {
        "date": _today(),
        "birds": []
    }


def load_today():
    if not TODAY_FILE.exists():
        return empty_today()

    with open(TODAY_FILE, "r") as f:
        data = json.load(f)

    if data.get("date") != _today():
        return empty_today()

    return data


def save_today(data):
    TODAY_FILE.parent.mkdir(exist_ok=True)

    with open(TODAY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record(species):
    data = load_today()

    if species not in data["birds"]:
        data["birds"].append(species)

    save_today(data)


def get_birds():
    return load_today()["birds"]


def clear_today():
    save_today(empty_today())


def archive_today_as_yesterday():
    today = load_today()

    YESTERDAY_FILE.parent.mkdir(exist_ok=True)

    with open(YESTERDAY_FILE, "w") as f:
        json.dump(today, f, indent=2)

    return today


def load_yesterday():
    if not YESTERDAY_FILE.exists():
        return {
            "date": "",
            "birds": []
        }

    with open(YESTERDAY_FILE, "r") as f:
        return json.load(f)


def get_yesterday_birds():
    return load_yesterday()["birds"]