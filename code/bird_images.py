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
    # Thrushes, chats and familiar garden birds.
    "eurasian blackbird": ("Blackbird Grönvold.jpg", "Henrik Grönvold"),
    "common blackbird": ("Blackbird Grönvold.jpg", "Henrik Grönvold"),
    "blackbird": ("Blackbird Grönvold.jpg", "Henrik Grönvold"),
    "turdus merula": ("Blackbird Grönvold.jpg", "Henrik Grönvold"),
    "song thrush": ("Song Thrush Grönvold.jpg", "Henrik Grönvold"),
    "turdus philomelos": ("Song Thrush Grönvold.jpg", "Henrik Grönvold"),
    "mistle thrush": ("Missel Thrush Grönvold.jpg", "Henrik Grönvold"),
    "missel thrush": ("Missel Thrush Grönvold.jpg", "Henrik Grönvold"),
    "turdus viscivorus": ("Missel Thrush Grönvold.jpg", "Henrik Grönvold"),
    "redwing": ("Redwing Grönvold.jpg", "Henrik Grönvold"),
    "turdus iliacus": ("Redwing Grönvold.jpg", "Henrik Grönvold"),
    "fieldfare": ("Fieldfare Grönvold.jpg", "Henrik Grönvold"),
    "turdus pilaris": ("Fieldfare Grönvold.jpg", "Henrik Grönvold"),
    "ring ouzel": ("Ring Ouzel Grönvold.jpg", "Henrik Grönvold"),
    "turdus torquatus": ("Ring Ouzel Grönvold.jpg", "Henrik Grönvold"),
    "european robin": ("Redbreast Grönvold.jpg", "Henrik Grönvold"),
    "robin": ("Redbreast Grönvold.jpg", "Henrik Grönvold"),
    "erithacus rubecula": ("Redbreast Grönvold.jpg", "Henrik Grönvold"),
    "common redstart": ("Redstart Grönvold.jpg", "Henrik Grönvold"),
    "redstart": ("Redstart Grönvold.jpg", "Henrik Grönvold"),
    "phoenicurus phoenicurus": ("Redstart Grönvold.jpg", "Henrik Grönvold"),
    "black redstart": ("Black Redstart Grönvold.jpg", "Henrik Grönvold"),
    "phoenicurus ochruros": ("Black Redstart Grönvold.jpg", "Henrik Grönvold"),
    "european stonechat": ("Stonechat Grönvold.jpg", "Henrik Grönvold"),
    "common stonechat": ("Stonechat Grönvold.jpg", "Henrik Grönvold"),
    "stonechat": ("Stonechat Grönvold.jpg", "Henrik Grönvold"),
    "saxicola rubicola": ("Stonechat Grönvold.jpg", "Henrik Grönvold"),
    "northern wheatear": ("Wheatear Grönvold.jpg", "Henrik Grönvold"),
    "wheatear": ("Wheatear Grönvold.jpg", "Henrik Grönvold"),
    "oenanthe oenanthe": ("Wheatear Grönvold.jpg", "Henrik Grönvold"),

    # Tits and other small woodland/garden species.
    "eurasian blue tit": ("Blue Tit Grönvold.jpg", "Henrik Grönvold"),
    "blue tit": ("Blue Tit Grönvold.jpg", "Henrik Grönvold"),
    "cyanistes caeruleus": ("Blue Tit Grönvold.jpg", "Henrik Grönvold"),
    "great tit": ("Great Tit Grönvold.jpg", "Henrik Grönvold"),
    "parus major": ("Great Tit Grönvold.jpg", "Henrik Grönvold"),
    "coal tit": ("Coal Tit Frohawk.jpg", "Frederick William Frohawk"),
    "periparus ater": ("Coal Tit Frohawk.jpg", "Frederick William Frohawk"),
    "marsh tit": ("Marsh Tit Grönvold.jpg", "Henrik Grönvold"),
    "poecile palustris": ("Marsh Tit Grönvold.jpg", "Henrik Grönvold"),
    "long-tailed tit": ("Long-tailed Titmouse Grönvold.jpg", "Henrik Grönvold"),
    "long-tailed titmouse": ("Long-tailed Titmouse Grönvold.jpg", "Henrik Grönvold"),
    "aegithalos caudatus": ("Long-tailed Titmouse Grönvold.jpg", "Henrik Grönvold"),
    "eurasian nuthatch": ("Nuthatch Grönvold.jpg", "Henrik Grönvold"),
    "nuthatch": ("Nuthatch Grönvold.jpg", "Henrik Grönvold"),
    "sitta europaea": ("Nuthatch Grönvold.jpg", "Henrik Grönvold"),
    "eurasian treecreeper": ("Tree Creeper Grönvold.jpg", "Henrik Grönvold"),
    "treecreeper": ("Tree Creeper Grönvold.jpg", "Henrik Grönvold"),
    "certhia familiaris": ("Tree Creeper Grönvold.jpg", "Henrik Grönvold"),
    "eurasian wren": ("Wren Grönvold.jpg", "Henrik Grönvold"),
    "wren": ("Wren Grönvold.jpg", "Henrik Grönvold"),
    "troglodytes troglodytes": ("Wren Grönvold.jpg", "Henrik Grönvold"),
    "dunnock": ("Hedge Sparrow Grönvold.jpg", "Henrik Grönvold"),
    "hedge accentor": ("Hedge Sparrow Grönvold.jpg", "Henrik Grönvold"),
    "prunella modularis": ("Hedge Sparrow Grönvold.jpg", "Henrik Grönvold"),
    "goldcrest": ("Gold-creasted Wren Grönvold.jpg", "Henrik Grönvold"),
    "regulus regulus": ("Gold-creasted Wren Grönvold.jpg", "Henrik Grönvold"),
    "firecrest": ("Fire-crested Wren Grönvold.jpg", "Henrik Grönvold"),
    "regulus ignicapilla": ("Fire-crested Wren Grönvold.jpg", "Henrik Grönvold"),

    # Warblers.
    "common chiffchaff": ("Chiff Chaff Grönvold.jpg", "Henrik Grönvold"),
    "chiffchaff": ("Chiff Chaff Grönvold.jpg", "Henrik Grönvold"),
    "phylloscopus collybita": ("Chiff Chaff Grönvold.jpg", "Henrik Grönvold"),
    "willow warbler": ("Willow Warbler Grönvold.jpg", "Henrik Grönvold"),
    "phylloscopus trochilus": ("Willow Warbler Grönvold.jpg", "Henrik Grönvold"),
    "eurasian blackcap": ("Blackcap Grönvold.jpg", "Henrik Grönvold"),
    "blackcap": ("Blackcap Grönvold.jpg", "Henrik Grönvold"),
    "sylvia atricapilla": ("Blackcap Grönvold.jpg", "Henrik Grönvold"),
    "garden warbler": ("Garden Warbler Grönvold.jpg", "Henrik Grönvold"),
    "sylvia borin": ("Garden Warbler Grönvold.jpg", "Henrik Grönvold"),
    "common whitethroat": ("Whitethroat Grönvold.jpg", "Henrik Grönvold"),
    "whitethroat": ("Whitethroat Grönvold.jpg", "Henrik Grönvold"),
    "curruca communis": ("Whitethroat Grönvold.jpg", "Henrik Grönvold"),
    "lesser whitethroat": ("Lesser Whitethroat Grönvold.jpg", "Henrik Grönvold"),
    "curruca curruca": ("Lesser Whitethroat Grönvold.jpg", "Henrik Grönvold"),
    "sedge warbler": ("Sedge Warbler Grönvold.jpg", "Henrik Grönvold"),
    "acrocephalus schoenobaenus": ("Sedge Warbler Grönvold.jpg", "Henrik Grönvold"),

    # Wagtails, pipits and waterside birds.
    "grey wagtail": ("Grey Wagtail Grönvold.jpg", "Henrik Grönvold"),
    "motacilla cinerea": ("Grey Wagtail Grönvold.jpg", "Henrik Grönvold"),
    "yellow wagtail": ("Yellow Wagtail Grönvold.jpg", "Henrik Grönvold"),
    "motacilla flava": ("Yellow Wagtail Grönvold.jpg", "Henrik Grönvold"),
    "pied wagtail": ("Pied Wagtail Grönvold.jpg", "Henrik Grönvold"),
    "white wagtail": ("White Wagtail Grönvold.jpg", "Henrik Grönvold"),
    "motacilla alba": ("Pied Wagtail Grönvold.jpg", "Henrik Grönvold"),
    "european rock pipit": ("Rock Pipit Grönvold.jpg", "Henrik Grönvold"),
    "rock pipit": ("Rock Pipit Grönvold.jpg", "Henrik Grönvold"),
    "anthus petrosus": ("Rock Pipit Grönvold.jpg", "Henrik Grönvold"),
    "tree pipit": ("Tree Pipit Grönvold.jpg", "Henrik Grönvold"),
    "anthus trivialis": ("Tree Pipit Grönvold.jpg", "Henrik Grönvold"),
    "white-throated dipper": ("Dipper Grönvold.jpg", "Henrik Grönvold"),
    "dipper": ("Dipper Grönvold.jpg", "Henrik Grönvold"),
    "cinclus cinclus": ("Dipper Grönvold.jpg", "Henrik Grönvold"),
}


def illustration_for(common_name: str, scientific_name: str = "") -> dict | None:
    common_key = str(common_name).strip().casefold()
    scientific_key = str(scientific_name).strip().casefold()
    entry = ILLUSTRATIONS.get(common_key) or ILLUSTRATIONS.get(scientific_key)
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
