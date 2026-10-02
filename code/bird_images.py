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


def _safe_slug(value: str) -> str:
    import re
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(value).strip().casefold()).strip("-")
    return cleaned or "bird"


def mirror_tile_path(common_name: str, scientific_name: str = ""):
    """Return a locally cached square illustration suitable for Magic Mirror tiles."""
    import hashlib
    import io
    import urllib.request
    from pathlib import Path

    from PIL import Image, ImageDraw, ImageFont, ImageOps
    from paths import OUTPUT_DIR

    tile_dir = OUTPUT_DIR / "bird-tiles"
    tile_dir.mkdir(parents=True, exist_ok=True)

    illustration = illustration_for(common_name, scientific_name)
    source_url = illustration["image_url"] if illustration else ""
    revision = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:10] if source_url else "fallback"
    destination = tile_dir / f"{_safe_slug(common_name)}-{revision}.jpg"
    if destination.is_file():
        return destination

    if illustration:
        try:
            request = urllib.request.Request(
                source_url,
                headers={"User-Agent": "BirdCanvas/0.17 (+local Magic Mirror tile cache)"},
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = response.read(12 * 1024 * 1024)
            with Image.open(io.BytesIO(payload)) as opened:
                source = ImageOps.exif_transpose(opened).convert("RGB")
                contained = ImageOps.contain(source, (560, 560), method=Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (600, 600), "white")
                x = (600 - contained.width) // 2
                y = (600 - contained.height) // 2
                canvas.paste(contained, (x, y))
                canvas.save(destination, "JPEG", quality=90, optimize=True)
            return destination
        except Exception:
            pass

    # A local fallback means the Mirror never has to deal with broken external URLs.
    canvas = Image.new("RGB", (600, 600), (242, 240, 233))
    draw = ImageDraw.Draw(canvas)
    initial = (str(common_name).strip()[:1] or "?").upper()
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 180)
    except OSError:
        font = ImageFont.load_default()
    bounds = draw.textbbox((0, 0), initial, font=font)
    draw.text(
        ((600 - (bounds[2] - bounds[0])) / 2, (600 - (bounds[3] - bounds[1])) / 2 - 20),
        initial,
        fill=(70, 70, 70),
        font=font,
    )
    canvas.save(destination, "JPEG", quality=88, optimize=True)
    return destination
