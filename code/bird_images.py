"""Curated field-guide illustrations for the live bird views.

The UI uses stable Wikimedia Commons file redirects for public-domain
illustrations. The mapping is intentionally curated rather than searched at
runtime so the same bird keeps the same visual identity on the phone and
Magic Mirror.
"""
from __future__ import annotations

from urllib.parse import quote, urlencode

COMMONS_REDIRECT = "https://commons.wikimedia.org/wiki/Special:Redirect/file/{file}?width=700"
BIRD_OVERRIDE_MAX_BYTES = 10 * 1024 * 1024
OVERRIDE_ARTIST = "Custom replacement"

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

    # Sparrows, starlings and finches.
    "house sparrow": (
        "10 of 'Feathered Favourites. Twelve coloured pictures of British birds, from drawings by Joseph Wolf. (With descriptions in verse by various authors.)' (11042921903) (cropped).jpg",
        "Joseph Wolf",
    ),
    "passer domesticus": (
        "10 of 'Feathered Favourites. Twelve coloured pictures of British birds, from drawings by Joseph Wolf. (With descriptions in verse by various authors.)' (11042921903) (cropped).jpg",
        "Joseph Wolf",
    ),
    "tree sparrow": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00070.jpg",
        "von Wright brothers",
    ),
    "passer montanus": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00070.jpg",
        "von Wright brothers",
    ),
    "common starling": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00005.jpg",
        "von Wright brothers",
    ),
    "starling": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00005.jpg",
        "von Wright brothers",
    ),
    "sturnus vulgaris": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00005.jpg",
        "von Wright brothers",
    ),
    "european goldfinch": (
        "100 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11002252763).jpg",
        "Historical British bird plate",
    ),
    "goldfinch": (
        "100 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11002252763).jpg",
        "Historical British bird plate",
    ),
    "carduelis carduelis": (
        "100 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11002252763).jpg",
        "Historical British bird plate",
    ),
    "european greenfinch": ("Nederlandsche vogelen (KB) - Chloris chloris (072b).jpg", "Nederlandsche vogelen"),
    "greenfinch": ("Nederlandsche vogelen (KB) - Chloris chloris (072b).jpg", "Nederlandsche vogelen"),
    "chloris chloris": ("Nederlandsche vogelen (KB) - Chloris chloris (072b).jpg", "Nederlandsche vogelen"),
    "common chaffinch": ("Chaffinch (PSF).jpg", "Historical bird plate"),
    "chaffinch": ("Chaffinch (PSF).jpg", "Historical bird plate"),
    "fringilla coelebs": ("Chaffinch (PSF).jpg", "Historical bird plate"),
    "eurasian bullfinch": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00229.jpg",
        "von Wright brothers",
    ),
    "bullfinch": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00229.jpg",
        "von Wright brothers",
    ),
    "pyrrhula pyrrhula": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00229.jpg",
        "von Wright brothers",
    ),

    # Pigeons, doves and corvids.
    "common woodpigeon": ("A natural history of British birds (6092234605).jpg", "Historical British bird plate"),
    "woodpigeon": ("A natural history of British birds (6092234605).jpg", "Historical British bird plate"),
    "wood pigeon": ("A natural history of British birds (6092234605).jpg", "Historical British bird plate"),
    "columba palumbus": ("A natural history of British birds (6092234605).jpg", "Historical British bird plate"),
    "collared dove": ("Columba decaocto Frivaldski.jpg", "Imre Frivaldszky"),
    "eurasian collared dove": ("Columba decaocto Frivaldski.jpg", "Imre Frivaldszky"),
    "streptopelia decaocto": ("Columba decaocto Frivaldski.jpg", "Imre Frivaldszky"),
    "eurasian magpie": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14564915648).jpg",
        "F. O. Morris",
    ),
    "magpie": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14564915648).jpg",
        "F. O. Morris",
    ),
    "pica pica": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14564915648).jpg",
        "F. O. Morris",
    ),
    "western jackdaw": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14771431613).jpg",
        "F. O. Morris",
    ),
    "jackdaw": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14771431613).jpg",
        "F. O. Morris",
    ),
    "coloeus monedula": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14771431613).jpg",
        "F. O. Morris",
    ),
    "corvus monedula": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14771431613).jpg",
        "F. O. Morris",
    ),
    "carrion crow": ("Britain's birds and their nests (1910) (14568695650).jpg", "Historical British bird plate"),
    "corvus corone": ("Britain's birds and their nests (1910) (14568695650).jpg", "Historical British bird plate"),

    # Gulls and coastal visitors.
    "black-headed gull": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00047.jpg",
        "von Wright brothers",
    ),
    "chroicocephalus ridibundus": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00047.jpg",
        "von Wright brothers",
    ),
    "european herring gull": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00122.jpg",
        "von Wright brothers",
    ),
    "herring gull": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00122.jpg",
        "von Wright brothers",
    ),
    "larus argentatus": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00122.jpg",
        "von Wright brothers",
    ),

    # Woodpeckers and aerial summer visitors.
    "european green woodpecker": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14565126947).jpg",
        "F. O. Morris",
    ),
    "green woodpecker": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14565126947).jpg",
        "F. O. Morris",
    ),
    "picus viridis": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14565126947).jpg",
        "F. O. Morris",
    ),
    "great spotted woodpecker": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00015.jpg",
        "von Wright brothers",
    ),
    "dendrocopos major": (
        "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00015.jpg",
        "von Wright brothers",
    ),
    "common swift": ("A swift (Cypselus apus). Coloured engraving by Whimper. Wellcome V0022226ER.jpg", "Whimper"),
    "swift": ("A swift (Cypselus apus). Coloured engraving by Whimper. Wellcome V0022226ER.jpg", "Whimper"),
    "apus apus": ("A swift (Cypselus apus). Coloured engraving by Whimper. Wellcome V0022226ER.jpg", "Whimper"),
    "barn swallow": (
        "132 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11001967465).jpg",
        "Historical British bird plate",
    ),
    "swallow": (
        "132 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11001967465).jpg",
        "Historical British bird plate",
    ),
    "hirundo rustica": (
        "132 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11001967465).jpg",
        "Historical British bird plate",
    ),
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


def _override_paths(common_name: str, scientific_name: str = ""):
    import hashlib

    from paths import DATA_DIR

    identity = (
        str(scientific_name).strip().casefold()
        or str(common_name).strip().casefold()
    )
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:10]
    override_dir = DATA_DIR / "bird-image-overrides"
    stem = f"{_safe_slug(common_name)}-{digest}"
    return (
        override_dir / f"{stem}.jpg",
        override_dir / f"{stem}.json",
    )


def _override_info(common_name: str, scientific_name: str = "") -> dict | None:
    destination, metadata = _override_paths(common_name, scientific_name)
    if not destination.is_file():
        return None

    status = _read_tile_metadata(metadata)
    return {
        "path": destination,
        "status": "ready",
        "has_mapping": True,
        "problem": "",
        "artist": str(status.get("artist") or OVERRIDE_ARTIST),
        "source_url": "",
        "overridden": True,
    }


def display_illustration_for(common_name: str, scientific_name: str = "") -> dict | None:
    """Return the illustration used by the phone bird cards, including overrides."""
    override = _override_info(common_name, scientific_name)
    if override:
        path = override["path"]
        revision = path.name
        try:
            stat = path.stat()
            revision = f"{revision}-{stat.st_mtime_ns}-{stat.st_size}"
        except OSError:
            pass

        query = urlencode(
            {
                "name": str(common_name).strip(),
                "scientific": str(scientific_name).strip(),
                "v": revision,
            }
        )
        return {
            "image_url": f"/api/mirror/bird-image?{query}",
            "artist": str(override.get("artist") or OVERRIDE_ARTIST),
            "source": "BirdCanvas custom replacement",
            "source_url": "",
            "license": "",
            "overridden": True,
        }

    illustration = illustration_for(common_name, scientific_name)
    if illustration is None:
        return None
    return {**illustration, "overridden": False}


def _tile_cache(common_name: str, scientific_name: str = ""):
    import hashlib

    from paths import OUTPUT_DIR

    tile_dir = OUTPUT_DIR / "bird-tiles"
    tile_dir.mkdir(parents=True, exist_ok=True)
    illustration = illustration_for(common_name, scientific_name)
    source_url = illustration["image_url"] if illustration else ""
    revision = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:10] if source_url else "fallback"
    destination = tile_dir / f"{_safe_slug(common_name)}-{revision}.jpg"
    metadata = destination.with_suffix(".json")
    return illustration, destination, metadata


def _write_tile_metadata(path, payload: dict) -> None:
    import json
    from datetime import datetime
    from zoneinfo import ZoneInfo

    value = {
        "updated_at": datetime.now(ZoneInfo("Europe/London")).isoformat(timespec="seconds"),
        **payload,
    }
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _read_tile_metadata(path) -> dict:
    import json

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def save_tile_override(
    common_name: str,
    scientific_name: str,
    payload: bytes,
    *,
    filename: str = "",
) -> dict:
    """Validate and save a user-selected field-guide replacement as a square JPEG."""
    import io

    from PIL import Image, ImageOps

    name = str(common_name).strip()
    scientific = str(scientific_name).strip()
    if not name:
        raise ValueError("Bird name is required.")
    if not payload:
        raise ValueError("Choose an image to upload.")
    if len(payload) > BIRD_OVERRIDE_MAX_BYTES:
        raise ValueError("Replacement image must be 10 MB or smaller.")

    try:
        with Image.open(io.BytesIO(payload)) as opened:
            image_format = str(opened.format or "").upper()
            if image_format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("Replacement must be a JPG, PNG or WebP image.")

            source = ImageOps.exif_transpose(opened).convert("RGB")
            contained = ImageOps.contain(
                source,
                (560, 560),
                method=Image.Resampling.LANCZOS,
            )
    except ValueError:
        raise
    except Exception as error:
        raise ValueError("Replacement image could not be read.") from error

    canvas = Image.new("RGB", (600, 600), (246, 244, 237))
    x = (600 - contained.width) // 2
    y = (600 - contained.height) // 2
    canvas.paste(contained, (x, y))

    destination, metadata = _override_paths(name, scientific)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    canvas.save(temporary, "JPEG", quality=92, optimize=True)
    temporary.replace(destination)

    _write_tile_metadata(
        metadata,
        {
            "status": "ready",
            "has_mapping": True,
            "problem": "",
            "artist": OVERRIDE_ARTIST,
            "source_url": "",
            "overridden": True,
            "original_filename": str(filename).strip(),
        },
    )
    return mirror_tile_info(name, scientific)


def restore_tile_override(common_name: str, scientific_name: str = "") -> bool:
    """Remove a user-selected replacement and return to the curated default."""
    destination, metadata = _override_paths(common_name, scientific_name)
    existed = destination.is_file() or metadata.is_file()
    destination.unlink(missing_ok=True)
    metadata.unlink(missing_ok=True)
    return existed


def _fallback_tile(destination, common_name: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    canvas = Image.new("RGB", (600, 600), (246, 244, 237))
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


def mirror_tile_path(common_name: str, scientific_name: str = ""):
    """Return a locally cached square illustration suitable for Magic Mirror tiles."""
    import io
    import urllib.request

    from PIL import Image, ImageOps

    override_path, _ = _override_paths(common_name, scientific_name)
    if override_path.is_file():
        return override_path

    illustration, destination, metadata = _tile_cache(common_name, scientific_name)
    if destination.is_file():
        if not metadata.is_file():
            _write_tile_metadata(
                metadata,
                {
                    "status": "ready" if illustration else "missing",
                    "has_mapping": bool(illustration),
                    "problem": "" if illustration else "No curated illustration yet.",
                    "artist": (illustration or {}).get("artist", ""),
                    "source_url": (illustration or {}).get("source_url", ""),
                },
            )
        return destination

    if illustration:
        try:
            request = urllib.request.Request(
                illustration["image_url"],
                headers={"User-Agent": "BirdCanvas/0.19 (+local Magic Mirror tile cache)"},
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = response.read(12 * 1024 * 1024)
            with Image.open(io.BytesIO(payload)) as opened:
                source = ImageOps.exif_transpose(opened).convert("RGB")
                contained = ImageOps.contain(source, (560, 560), method=Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (600, 600), (246, 244, 237))
                x = (600 - contained.width) // 2
                y = (600 - contained.height) // 2
                canvas.paste(contained, (x, y))
                canvas.save(destination, "JPEG", quality=90, optimize=True)
            _write_tile_metadata(
                metadata,
                {
                    "status": "ready",
                    "has_mapping": True,
                    "problem": "",
                    "artist": illustration.get("artist", ""),
                    "source_url": illustration.get("source_url", ""),
                },
            )
            return destination
        except Exception as error:
            _fallback_tile(destination, common_name)
            _write_tile_metadata(
                metadata,
                {
                    "status": "missing",
                    "has_mapping": True,
                    "problem": f"Curated image could not be fetched: {type(error).__name__}",
                    "artist": illustration.get("artist", ""),
                    "source_url": illustration.get("source_url", ""),
                },
            )
            return destination

    _fallback_tile(destination, common_name)
    _write_tile_metadata(
        metadata,
        {
            "status": "missing",
            "has_mapping": False,
            "problem": "No curated illustration yet.",
            "artist": "",
            "source_url": "",
        },
    )
    return destination


def mirror_tile_info(common_name: str, scientific_name: str = "") -> dict:
    """Return the cached tile path plus whether the field-guide image is healthy."""
    override = _override_info(common_name, scientific_name)
    if override:
        return override

    illustration, destination, metadata = _tile_cache(common_name, scientific_name)
    mirror_tile_path(common_name, scientific_name)
    status = _read_tile_metadata(metadata)
    return {
        "path": destination,
        "status": status.get("status", "ready" if illustration else "missing"),
        "has_mapping": bool(status.get("has_mapping", bool(illustration))),
        "problem": str(status.get("problem", "")),
        "artist": str(status.get("artist") or (illustration or {}).get("artist", "")),
        "source_url": str(status.get("source_url") or (illustration or {}).get("source_url", "")),
        "overridden": False,
    }

