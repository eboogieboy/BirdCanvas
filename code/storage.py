import json
from datetime import date, timedelta

from paths import DATA_DIR


TODAY_FILE = DATA_DIR / "today.json"
YESTERDAY_FILE = DATA_DIR / "yesterday.json"


def _today():
    return date.today().isoformat()


def _yesterday():
    return (date.today() - timedelta(days=1)).isoformat()


def empty_today():
    return {
        "date": _today(),
        "birds": [],
    }


def _read_json(path, default):
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except (OSError, json.JSONDecodeError):
        pass

    return default


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def rollover_today_if_needed():
    """
    If today.json belongs to an earlier calendar day, safely roll it over.

    Only data from the immediately previous day becomes yesterday.json.
    Older stale data is discarded rather than being mistaken for yesterday.

    Returns True when a rollover/reset occurred.
    """

    if not TODAY_FILE.exists():
        return False

    data = _read_json(
        TODAY_FILE,
        {
            "date": "",
            "birds": [],
        },
    )

    data_date = str(data.get("date", "")).strip()

    if not data_date:
        _write_json(TODAY_FILE, empty_today())
        return True

    if data_date == _today():
        return False

    if data_date == _yesterday():
        _write_json(
            YESTERDAY_FILE,
            {
                "date": data_date,
                "birds": list(data.get("birds", [])),
            },
        )

    # Whether yesterday's data was archived or the file was simply stale,
    # always start a clean file for the new calendar day.
    _write_json(TODAY_FILE, empty_today())

    return True


def load_today():
    rollover_today_if_needed()

    return _read_json(
        TODAY_FILE,
        empty_today(),
    )


def save_today(data):
    TODAY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with TODAY_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record(species):
    # This is deliberately before load_today so the first bird detected
    # after midnight cannot overwrite yesterday's data.
    rollover_today_if_needed()

    data = load_today()

    if species not in data["birds"]:
        data["birds"].append(species)

    save_today(data)


def get_birds():
    return load_today()["birds"]


def clear_today():
    save_today(empty_today())


def archive_today_as_yesterday():
    """
    Explicit/manual archive helper retained for compatibility.
    """

    data = load_today()

    _write_json(
        YESTERDAY_FILE,
        {
            "date": data.get("date", _today()),
            "birds": list(data.get("birds", [])),
        },
    )

    return data


def load_yesterday():
    # Important: the 04:00 generation job asks for yesterday before it
    # necessarily asks for today, so trigger rollover here too.
    rollover_today_if_needed()

    return _read_json(
        YESTERDAY_FILE,
        {
            "date": "",
            "birds": [],
        },
    )


def get_yesterday_birds():
    return load_yesterday()["birds"]
