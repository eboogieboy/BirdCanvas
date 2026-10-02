"""Curated field-guide illustrations for the live bird views.

The UI uses stable Wikimedia Commons file redirects for public-domain
illustrations. The mapping is intentionally curated rather than searched at
runtime so the same bird keeps the same visual identity on the phone and
Magic Mirror.
"""
from __future__ import annotations

from urllib.parse import quote

COMMONS_REDIRECT = "https://commons.wikimedia.org/wiki/Special:Redirect/file/{file}?width=700"

# Common names are normalised to casefold before lookup.
# These are public-domain historical plates from Henrik Grönvold / F.O. Morris
# and related British bird works hosted on Wikimedia Commons.
ILLUSTRATIONS = {
    "eurasian blackbird": ("Blackbird Grönvold.jpg", "Henrik Grönvold"),
    "common blackbird": ("Blackbird Grönvold.jpg", "Henrik Grönvold"),
    "blackbird": ("Blackbird Grönvold.jpg", "Henrik Grönvold"),
    "eurasian blue tit": ("Blue Tit Grönvold.jpg", "Henrik Grönvold"),
    "blue tit": ("Blue Tit Grönvold.jpg", "Henrik Grönvold"),
    "great tit": ("Great Tit Grönvold.jpg", "Henrik Grönvold"),
    "coal tit": ("Coal Tit Frohawk.jpg", "Frederick William Frohawk"),
    "dunnock": ("Hedge Sparrow Grönvold.jpg", "Henrik Grönvold"),
    "hedge accentor": ("Hedge Sparrow Grönvold.jpg", "Henrik Grönvold"),
    "european robin": (
        "A history of British birds - by the Rev. F. O. Morris (1862) (14772306483).jpg",
        "F. O. Morris",
    ),
    "robin": (
        "A history of British birds - by the Rev. F. O. Morris (1862) (14772306483).jpg",
        "F. O. Morris",
    ),
    "eurasian wren": ("Wren Grönvold.jpg", "Henrik Grönvold"),
    "wren": ("Wren Grönvold.jpg", "Henrik Grönvold"),
    "goldcrest": ("Gold-creasted Wren Grönvold.jpg", "Henrik Grönvold"),
    "common chiffchaff": ("Chiff Chaff Grönvold.jpg", "Henrik Grönvold"),
    "chiffchaff": ("Chiff Chaff Grönvold.jpg", "Henrik Grönvold"),
    "eurasian blackcap": ("Blackcap Grönvold.jpg", "Henrik Grönvold"),
    "blackcap": ("Blackcap Grönvold.jpg", "Henrik Grönvold"),
    "willow warbler": ("Willow Warbler Grönvold.jpg", "Henrik Grönvold"),
    "grey wagtail": ("Grey Wagtail Grönvold.jpg", "Henrik Grönvold"),
    "yellow wagtail": ("Yellow Wagtail Grönvold.jpg", "Henrik Grönvold"),
    "fieldfare": ("Fieldfare Grönvold.jpg", "Henrik Grönvold"),
}


def illustration_for(common_name: str, scientific_name: str = "") -> dict | None:
    entry = ILLUSTRATIONS.get(str(common_name).strip().casefold())
    if entry is None:
        return None
    filename, artist = entry
    return {
        "image_url": COMMONS_REDIRECT.format(file=quote(filename, safe="")),
        "artist": artist,
        "source": "Wikimedia Commons",
        "source_url": f"https://commons.wikimedia.org/wiki/File:{quote(filename.replace(' ', '_'), safe='_:()-.')}",
        "license": "Public domain",
    }
