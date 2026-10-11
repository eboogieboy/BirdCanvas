"""Conservative, display-only local bird frequency labels for North Tyneside.

These are *indicative* regional encounter-frequency labels, not UK conservation
status, not precise population estimates, and never confirmation that a BirdNET
detection is correct. In particular, we do not infer rarity from how often an
individual microphone hears a species. Unreviewed species stay "Unrated"
rather than being assigned a misleading "Rare" label.

Reference points for manual reviews:
- BTO BirdFacts Places: https://www.bto.org/learn/about-birds/birdfacts
- Northumberland & Tyneside Bird Club: https://www.ntbc.org.uk/?page_id=33
"""

from __future__ import annotations

REGION = "North Tyneside / North East coast"

LABELS = {
    "common": "Common",
    "uncommon": "Uncommon",
    "scarce": "Scarce",
    "rare": "Rare",
    "unrated": "Unrated",
}

# scientific name -> (local frequency, concise seasonal / habitat context).
# This deliberately starts with familiar local birds; unusual detections are
# left unrated until an evidence-based manual review can be made.
LOCAL_STATUSES = {
    "turdus merula": ("common", "Year-round"),
    "cyanistes caeruleus": ("common", "Year-round"),
    "corvus corone": ("common", "Year-round"),
    "fringilla coelebs": ("common", "Year-round"),
    "periparus ater": ("common", "Year-round"),
    "streptopelia decaocto": ("common", "Year-round"),
    "prunella modularis": ("common", "Year-round"),
    "carduelis carduelis": ("common", "Year-round"),
    "parus major": ("common", "Year-round"),
    "chloris chloris": ("common", "Year-round"),
    "larus argentatus": ("common", "Coast; year-round"),
    "passer domesticus": ("common", "Year-round"),
    "coloeus monedula": ("common", "Year-round"),
    "corvus monedula": ("common", "Year-round"),
    "aegithalos caudatus": ("common", "Year-round"),
    "pica pica": ("common", "Year-round"),
    "erithacus rubecula": ("common", "Year-round"),
    "turdus philomelos": ("common", "Year-round"),
    "sturnus vulgaris": ("common", "Year-round"),
    "columba palumbus": ("common", "Year-round"),
    "troglodytes troglodytes": ("common", "Year-round"),
    "anas platyrhynchos": ("common", "Local ponds and waterways"),
    "anthus pratensis": ("common", "Grassland and coastal passage"),
    "motacilla cinerea": ("uncommon", "Most associated with streams and rivers"),
    "motacilla alba": ("common", "Year-round; variable by habitat"),
    "turdus iliacus": ("common", "Mainly autumn and winter"),
    "haematopus ostralegus": ("common", "Coast; year-round"),
    "corvus frugilegus": ("common", "Year-round"),
    "phylloscopus collybita": ("common", "Mostly spring to autumn"),
    "psittacula krameri": ("uncommon", "Localised and increasing in parts of the UK"),
    "branta leucopsis": ("uncommon", "Mainly winter and passage"),
    "ardea cinerea": ("common", "Wetlands and coastline"),
    "fulica atra": ("common", "Ponds and freshwater"),
    "cygnus cygnus": ("uncommon", "Winter and passage"),
    "anas acuta": ("uncommon", "Winter; wetlands and estuaries"),
    "anser brachyrhynchus": ("common", "Mainly autumn and winter passage"),
    "corvus cornix": ("scarce", "Unusual locally; review an audio detection"),
    "numenius arquata": ("common", "Coastal areas and estuaries"),
    "chroicocephalus ridibundus": ("common", "Coast and inland waters"),
    "larus ridibundus": ("common", "Coast and inland waters"),
}

# A fallback for older catalogue entries or imported records without a
# scientific name. New BirdNET-Go records normally supply scientific names.
COMMON_TO_SCIENTIFIC = {
    "blackbird": "turdus merula",
    "blue tit": "cyanistes caeruleus",
    "carrion crow": "corvus corone",
    "chaffinch": "fringilla coelebs",
    "coal tit": "periparus ater",
    "collared dove": "streptopelia decaocto",
    "dunnock": "prunella modularis",
    "goldfinch": "carduelis carduelis",
    "great tit": "parus major",
    "greenfinch": "chloris chloris",
    "herring gull": "larus argentatus",
    "house sparrow": "passer domesticus",
    "jackdaw": "coloeus monedula",
    "long-tailed tit": "aegithalos caudatus",
    "magpie": "pica pica",
    "robin": "erithacus rubecula",
    "song thrush": "turdus philomelos",
    "starling": "sturnus vulgaris",
    "woodpigeon": "columba palumbus",
    "wren": "troglodytes troglodytes",
    "mallard": "anas platyrhynchos",
    "meadow pipit": "anthus pratensis",
    "grey wagtail": "motacilla cinerea",
    "pied wagtail": "motacilla alba",
    "redwing": "turdus iliacus",
    "oystercatcher": "haematopus ostralegus",
    "rook": "corvus frugilegus",
    "chiffchaff": "phylloscopus collybita",
    "ring-necked parakeet": "psittacula krameri",
    "barnacle goose": "branta leucopsis",
    "grey heron": "ardea cinerea",
    "coot": "fulica atra",
    "whooper swan": "cygnus cygnus",
    "northern pintail": "anas acuta",
    "pink-footed goose": "anser brachyrhynchus",
    "hooded crow": "corvus cornix",
    "curlew": "numenius arquata",
    "black-headed gull": "chroicocephalus ridibundus",
}


def rarity_for(name: str, scientific_name: str = "") -> dict[str, str]:
    """Return the same display metadata for daily cards and catalogue tiles."""
    scientific = str(scientific_name or "").strip().casefold()
    common = str(name or "").strip().casefold()
    if common.startswith("eurasian "):
        common = common[len("eurasian "):]
    key = scientific if scientific in LOCAL_STATUSES else COMMON_TO_SCIENTIFIC.get(common, "")
    row = LOCAL_STATUSES.get(key)
    if row is None:
        level, context = "unrated", "Local frequency not yet reviewed"
    else:
        level, context = row

    return {
        "level": level,
        "label": LABELS[level],
        "region": REGION,
        "context": context,
        "basis": "Indicative local frequency; not a verified sighting or conservation category",
    }
