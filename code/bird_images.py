"""Curated, clean field-guide illustrations for the live bird views.

BirdCanvas uses stable Wikimedia Commons redirects for public-domain
scientific illustrations. Grönvold is preferred where a strong plate exists;
other public-domain natural-history artists fill gaps when their source is
clearer or more species-accurate. Every default is rendered through the same
local clean-field-guide tile pipeline before it reaches the phone or Mirror.
"""
from __future__ import annotations

from urllib.parse import quote, urlencode

COMMONS_REDIRECT = "https://commons.wikimedia.org/wiki/Special:Redirect/file/{file}?width=900"
BIRD_OVERRIDE_MAX_BYTES = 10 * 1024 * 1024
OVERRIDE_ARTIST = "Custom replacement"
TILE_RENDER_VERSION = 5
TILE_SIZE = 600
TILE_INSET = 548
TILE_BACKGROUND = (250, 249, 245)

# Common names are normalised to casefold before lookup.
#
# Finished colour field-guide plates are preferred over preparatory sketches.
# A per-source crop may isolate one bird from a multi-bird plate and remove
# printed captions before the common tile renderer normalises the background.

def _commons_entry(filename: str, artist: str, *, license_name: str = "Public domain", crop=None) -> dict:
    return {
        "image_url": COMMONS_REDIRECT.format(file=quote(filename, safe="")),
        "artist": artist,
        "source": "Wikimedia Commons",
        "source_url": f"https://commons.wikimedia.org/wiki/File:{quote(filename.replace(' ', '_'), safe='_:()-.')}",
        "license": license_name,
        "crop": crop,
    }


def _direct_entry(image_url: str, artist: str, source: str, source_url: str, license_name: str, crop=None) -> dict:
    return {
        "image_url": image_url,
        "artist": artist,
        "source": source,
        "source_url": source_url,
        "license": license_name,
        "crop": crop,
    }


_FINISHED_BLACKBIRD = _direct_entry(
    "https://images.rawpixel.com/image_social_landscape/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIyLTExL2xyL2ZuZzI5Nzg2Ny1pbWFnZS5qcGc.jpg",
    "Wilhelm von Wright",
    "Finnish National Gallery / Rawpixel",
    "https://www.rawpixel.com/image/8864828/blackbird-male-1828-1838-wilhelm-von-wright",
    "Public domain / CC0",
    crop=(0.02, 0.02, 0.98, 0.82),
)
_FINISHED_BLUE_TIT = _commons_entry(
    "Cyanistes caeruleus 1869.jpg",
    "John Gerrard Keulemans",
    crop=(0.04, 0.08, 0.78, 0.96),
)
_FINISHED_GREAT_TIT = _commons_entry(
    "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00141.jpg",
    "von Wright brothers",
    license_name="CC BY-SA 4.0",
    crop=(0.05, 0.08, 0.95, 0.70),
)
_FINISHED_COAL_TIT = _commons_entry(
    "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00087.jpg",
    "von Wright brothers",
    license_name="CC BY-SA 4.0",
    crop=(0.22, 0.07, 0.80, 0.43),
)
_FINISHED_DUNNOCK = _commons_entry(
    "John Gould and H.C. Richter, Accentor modularis (Dunnock), NGA 53544.jpg",
    "John Gould & H. C. Richter",
    crop=(0.08, 0.03, 0.92, 0.48),
)
_FINISHED_CROW = _commons_entry(
    "Wilhelm von Wright - Crow - A II 1254-133 - Finnish National Gallery.jpg",
    "Wilhelm von Wright",
    license_name="CC0 / Public domain",
)
_FINISHED_LONG_TAILED_TIT = _direct_entry(
    "https://images.rawpixel.com/image_800/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvcGQxMi10b25nLTEyM18wLmpwZw.jpg",
    "von Wright brothers",
    "Rawpixel",
    "https://www.rawpixel.com/image/325632/free-illustration-image-bird-tit-sketch",
    "Public domain",
    crop=(0.04, 0.04, 0.96, 0.76),
)
_FINISHED_WREN = _commons_entry(
    "Bird illustration from Svenska Fåglar (Swedish Birds) by the von Wright brothers from rawpixel's original edition of the publication 00088.jpg",
    "von Wright brothers",
    license_name="CC BY-SA 4.0",
    crop=(0.23, 0.43, 0.82, 0.80),
)
_FINISHED_HOUSE_SPARROW = _commons_entry(
    "Passer domesticus m.jpg",
    "Wilhelm von Wright",
)
_FINISHED_STARLING = _commons_entry(
    "Sturnus vulgaris m.jpg",
    "Wilhelm von Wright",
)

COLOUR_FIELD_GUIDE_ILLUSTRATIONS = {
    # Gould/Richter and similarly rich hand-coloured plates are preferred
    # where a good public-domain source exists. These deliberately favour
    # vivid, accurate plumage over the very plain study-drawing look.
    "great tit": _commons_entry("ParusMajorGould.jpg", "John Gould"),
    "parus major": _commons_entry("ParusMajorGould.jpg", "John Gould"),

    "european robin": _commons_entry(
        "Erithacus rubecula. John Gould. The birds of Great Britain. Volume II. 1873.jpg",
        "John Gould & H. C. Richter",
    ),
    "robin": _commons_entry(
        "Erithacus rubecula. John Gould. The birds of Great Britain. Volume II. 1873.jpg",
        "John Gould & H. C. Richter",
    ),
    "erithacus rubecula": _commons_entry(
        "Erithacus rubecula. John Gould. The birds of Great Britain. Volume II. 1873.jpg",
        "John Gould & H. C. Richter",
    ),

    "common starling": _commons_entry("SturnusVulgarisGould.jpg", "John Gould & H. C. Richter"),
    "starling": _commons_entry("SturnusVulgarisGould.jpg", "John Gould & H. C. Richter"),
    "sturnus vulgaris": _commons_entry("SturnusVulgarisGould.jpg", "John Gould & H. C. Richter"),

    "eurasian blue tit": _commons_entry(
        "60 of 'Feathered Favourites. Twelve coloured pictures of British birds, from drawings by Joseph Wolf. (With descriptions in verse by various authors.)' (11043862023).jpg",
        "Joseph Wolf",
    ),
    "blue tit": _commons_entry(
        "60 of 'Feathered Favourites. Twelve coloured pictures of British birds, from drawings by Joseph Wolf. (With descriptions in verse by various authors.)' (11043862023).jpg",
        "Joseph Wolf",
    ),
    "cyanistes caeruleus": _commons_entry(
        "60 of 'Feathered Favourites. Twelve coloured pictures of British birds, from drawings by Joseph Wolf. (With descriptions in verse by various authors.)' (11043862023).jpg",
        "Joseph Wolf",
    ),

    "european herring gull": _commons_entry("Larus argentatus Gould.jpg", "John Gould"),
    "herring gull": _commons_entry("Larus argentatus Gould.jpg", "John Gould"),
    "larus argentatus": _commons_entry("Larus argentatus Gould.jpg", "John Gould"),

    "common woodpigeon": _commons_entry("Wood pigeon.jpg", "John Gould & Edward Lear"),
    "woodpigeon": _commons_entry("Wood pigeon.jpg", "John Gould & Edward Lear"),
    "wood pigeon": _commons_entry("Wood pigeon.jpg", "John Gould & Edward Lear"),
    "columba palumbus": _commons_entry("Wood pigeon.jpg", "John Gould & Edward Lear"),
}

PLAIN_FIELD_GUIDE_ILLUSTRATIONS = {
    "eurasian blackbird": _FINISHED_BLACKBIRD,
    "common blackbird": _FINISHED_BLACKBIRD,
    "blackbird": _FINISHED_BLACKBIRD,
    "turdus merula": _FINISHED_BLACKBIRD,

    "eurasian blue tit": _FINISHED_BLUE_TIT,
    "blue tit": _FINISHED_BLUE_TIT,
    "cyanistes caeruleus": _FINISHED_BLUE_TIT,

    "great tit": _FINISHED_GREAT_TIT,
    "parus major": _FINISHED_GREAT_TIT,
    "coal tit": _FINISHED_COAL_TIT,
    "periparus ater": _FINISHED_COAL_TIT,
    "long-tailed tit": _FINISHED_LONG_TAILED_TIT,
    "long-tailed titmouse": _FINISHED_LONG_TAILED_TIT,
    "aegithalos caudatus": _FINISHED_LONG_TAILED_TIT,

    "dunnock": _FINISHED_DUNNOCK,
    "hedge accentor": _FINISHED_DUNNOCK,
    "prunella modularis": _FINISHED_DUNNOCK,

    "european robin": ("Redbreast.jpg", "Benjamin Fawcett"),
    "robin": ("Redbreast.jpg", "Benjamin Fawcett"),
    "erithacus rubecula": ("Redbreast.jpg", "Benjamin Fawcett"),
    "song thrush": ("Turdus philomelos 1873.jpg", "John Gerrard Keulemans"),
    "turdus philomelos": ("Turdus philomelos 1873.jpg", "John Gerrard Keulemans"),

    "eurasian wren": _FINISHED_WREN,
    "wren": _FINISHED_WREN,
    "troglodytes troglodytes": _FINISHED_WREN,

    "house sparrow": _FINISHED_HOUSE_SPARROW,
    "passer domesticus": _FINISHED_HOUSE_SPARROW,
    "common starling": _FINISHED_STARLING,
    "starling": _FINISHED_STARLING,
    "sturnus vulgaris": _FINISHED_STARLING,

    "european goldfinch": ("100 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11002252763).jpg", "Historical British bird plate"),
    "goldfinch": ("100 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11002252763).jpg", "Historical British bird plate"),
    "carduelis carduelis": ("100 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11002252763).jpg", "Historical British bird plate"),

    "common chaffinch": ("Fringilla coelebs m.jpg", "Wilhelm von Wright"),
    "chaffinch": ("Fringilla coelebs m.jpg", "Wilhelm von Wright"),
    "fringilla coelebs": ("Fringilla coelebs m.jpg", "Wilhelm von Wright"),

    "carrion crow": _FINISHED_CROW,
    "corvus corone": _FINISHED_CROW,
}

# Broader fallback library for species not yet represented by the stricter set.
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


    # Additional waterbirds and corvids encountered by the live listener.
    "eurasian curlew": (
        "166 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11002096075).jpg",
        "Historical British bird plate",
    ),
    "curlew": (
        "166 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11002096075).jpg",
        "Historical British bird plate",
    ),
    "numenius arquata": (
        "166 of 'British Ornithology; being the history, with a coloured representation of every known species of British birds' (11002096075).jpg",
        "Historical British bird plate",
    ),
    "hooded crow": (
        "Nederlandsche vogelen (KB) - Corvus cornix (205pl).jpg",
        "Nederlandsche vogelen",
    ),
    "corvus cornix": (
        "Nederlandsche vogelen (KB) - Corvus cornix (205pl).jpg",
        "Nederlandsche vogelen",
    ),
    "northern pintail": (
        "A history of British birds (10422094213).jpg",
        "Historical British bird plate",
    ),
    "pintail": (
        "A history of British birds (10422094213).jpg",
        "Historical British bird plate",
    ),
    "anas acuta": (
        "A history of British birds (10422094213).jpg",
        "Historical British bird plate",
    ),
    "pink-footed goose": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14564454277).jpg",
        "F. O. Morris",
    ),
    "anser brachyrhynchus": (
        "A history of British birds. By the Rev. F.O. Morris (1862) (14564454277).jpg",
        "F. O. Morris",
    ),
    "whooper swan": (
        "Nederlandsche vogelen (KB) - Cygnus cygnus (490b).jpg",
        "Nederlandsche vogelen",
    ),
    "cygnus cygnus": (
        "Nederlandsche vogelen (KB) - Cygnus cygnus (490b).jpg",
        "Nederlandsche vogelen",
    ),
}


def illustration_for(common_name: str, scientific_name: str = "") -> dict | None:
    common_key = str(common_name).strip().casefold()
    scientific_key = str(scientific_name).strip().casefold()
    entry = (
        COLOUR_FIELD_GUIDE_ILLUSTRATIONS.get(common_key)
        or COLOUR_FIELD_GUIDE_ILLUSTRATIONS.get(scientific_key)
        or PLAIN_FIELD_GUIDE_ILLUSTRATIONS.get(common_key)
        or PLAIN_FIELD_GUIDE_ILLUSTRATIONS.get(scientific_key)
        or ILLUSTRATIONS.get(common_key)
        or ILLUSTRATIONS.get(scientific_key)
    )
    if entry is None:
        return None
    if isinstance(entry, dict):
        return dict(entry)
    filename, artist = entry
    return {
        "image_url": COMMONS_REDIRECT.format(file=quote(filename, safe="")),
        "artist": artist,
        "source": "Wikimedia Commons",
        "source_url": f"https://commons.wikimedia.org/wiki/File:{quote(filename.replace(' ', '_'), safe='_:()-.')}",
        "license": "Public domain",
        "crop": None,
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
    """Return the same locally normalised field-guide tile used by the Mirror."""
    import hashlib

    override = _override_info(common_name, scientific_name)
    illustration = illustration_for(common_name, scientific_name)
    if override is None and illustration is None:
        return None

    if override:
        path = override["path"]
        revision = path.name
        try:
            stat = path.stat()
            revision = f"{revision}-{stat.st_mtime_ns}-{stat.st_size}"
        except OSError:
            pass
        artist = str(override.get("artist") or OVERRIDE_ARTIST)
        source = "BirdCanvas custom replacement"
        source_url = ""
        license_name = ""
        overridden = True
    else:
        source_url = str(illustration.get("source_url") or "")
        source_identity = str(illustration.get("image_url") or source_url)
        revision = hashlib.sha1(
            f"{TILE_RENDER_VERSION}|{source_identity}".encode("utf-8")
        ).hexdigest()[:12]
        artist = str(illustration.get("artist") or "")
        source = str(illustration.get("source") or "Wikimedia Commons")
        license_name = str(illustration.get("license") or "")
        overridden = False

    query = urlencode(
        {
            "name": str(common_name).strip(),
            "scientific": str(scientific_name).strip(),
            "v": revision,
        }
    )
    return {
        "image_url": f"/api/mirror/bird-image?{query}",
        "artist": artist,
        "source": source,
        "source_url": source_url,
        "license": license_name,
        "overridden": overridden,
    }


def _tile_cache(common_name: str, scientific_name: str = ""):
    import hashlib

    from paths import OUTPUT_DIR

    tile_dir = OUTPUT_DIR / "bird-tiles"
    tile_dir.mkdir(parents=True, exist_ok=True)
    illustration = illustration_for(common_name, scientific_name)
    source_url = illustration["image_url"] if illustration else ""
    crop = (illustration or {}).get("crop")
    revision = (
        hashlib.sha1(
            f"{TILE_RENDER_VERSION}|{source_url}|{crop}".encode("utf-8")
        ).hexdigest()[:10]
        if source_url
        else f"fallback-v{TILE_RENDER_VERSION}"
    )
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


def _clean_field_guide_tile(source, crop=None):
    """Normalise a finished bird plate into a calm, consistent square field-guide tile."""
    from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps, ImageStat

    image = ImageOps.exif_transpose(source).convert("RGB")
    if crop:
        width, height = image.size
        left, top, right, bottom = crop
        box = (
            max(0, min(width - 1, int(width * left))),
            max(0, min(height - 1, int(height * top))),
            max(1, min(width, int(width * right))),
            max(1, min(height, int(height * bottom))),
        )
        if box[2] > box[0] and box[3] > box[1]:
            image = image.crop(box)
    image.thumbnail((1100, 1100), Image.Resampling.LANCZOS)

    # The source scans vary a lot in age and saturation. A restrained lift
    # keeps plumage lively on the phone and Mirror without changing the
    # species' field marks or turning the tiles into poster art.
    image = ImageEnhance.Color(image).enhance(1.14)
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Sharpness(image).enhance(1.04)

    width, height = image.size
    edge = max(4, min(width, height) // 18)
    corners = (
        image.crop((0, 0, edge, edge)),
        image.crop((width - edge, 0, width, edge)),
        image.crop((0, height - edge, edge, height)),
        image.crop((width - edge, height - edge, width, height)),
    )
    medians = [ImageStat.Stat(corner).median for corner in corners]
    paper = tuple(
        int(round(sum(median[channel] for median in medians) / len(medians)))
        for channel in range(3)
    )

    # Shift the scan's paper tone towards the BirdCanvas neutral background
    # without recolouring the bird itself.
    channels = image.split()
    shifted_channels = []
    for channel, target, current in zip(channels, TILE_BACKGROUND, paper):
        offset = target - current
        shifted_channels.append(
            channel.point(lambda value, delta=offset: max(0, min(255, value + delta)))
        )
    image = Image.merge("RGB", shifted_channels)

    # Find the meaningful illustration area against the now-normalised paper.
    # A light morphological pass joins fine feather/branch detail and avoids
    # treating isolated scan speckles as part of the subject.
    flat = Image.new("RGB", image.size, TILE_BACKGROUND)
    difference = ImageChops.difference(image, flat).convert("L")
    mask = difference.point(lambda value: 255 if value >= 18 else 0)
    mask = mask.filter(ImageFilter.MaxFilter(5))
    bbox = mask.getbbox()

    if bbox:
        left, top, right, bottom = bbox
        content_width = right - left
        content_height = bottom - top
        if content_width > 0 and content_height > 0:
            pad = max(12, int(max(content_width, content_height) * 0.08))
            left = max(0, left - pad)
            top = max(0, top - pad)
            right = min(image.width, right + pad)
            bottom = min(image.height, bottom + pad)
            image = image.crop((left, top, right, bottom))

    contained = ImageOps.contain(
        image,
        (TILE_INSET, TILE_INSET),
        method=Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", (TILE_SIZE, TILE_SIZE), TILE_BACKGROUND)
    x = (TILE_SIZE - contained.width) // 2
    y = (TILE_SIZE - contained.height) // 2
    canvas.paste(contained, (x, y))
    return canvas


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

    canvas = Image.new("RGB", (TILE_SIZE, TILE_SIZE), TILE_BACKGROUND)
    x = (TILE_SIZE - contained.width) // 2
    y = (TILE_SIZE - contained.height) // 2
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

    canvas = Image.new("RGB", (TILE_SIZE, TILE_SIZE), TILE_BACKGROUND)
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
                canvas = _clean_field_guide_tile(opened, illustration.get("crop"))
                canvas.save(destination, "JPEG", quality=92, optimize=True)
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

