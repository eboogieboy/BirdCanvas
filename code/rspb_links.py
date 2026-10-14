"""Verified direct links to RSPB bird species profiles.

Never derive an unverified RSPB URL from an arbitrary BirdNET species name:
RSPB naming and URL slugs sometimes differ (for example, Eurasian Coot).
Unknown species deliberately have no link until a profile is confirmed.
"""
from __future__ import annotations

RSPB_BASE = "https://www.rspb.org.uk/birds-and-wildlife/"

# Scientific names are primary because BirdNET and RSPB use different common names.
_SPECIES = {
    "turdus merula": ("blackbird", "blackbird"),
    "cyanistes caeruleus": ("blue tit", "blue-tit"),
    "corvus corone": ("carrion crow", "carrion-crow"),
    "fringilla coelebs": ("chaffinch", "chaffinch"),
    "periparus ater": ("coal tit", "coal-tit"),
    "streptopelia decaocto": ("collared dove", "collared-dove"),
    "prunella modularis": ("dunnock", "dunnock"),
    "carduelis carduelis": ("goldfinch", "goldfinch"),
    "parus major": ("great tit", "great-tit"),
    "chloris chloris": ("greenfinch", "greenfinch"),
    "larus argentatus": ("herring gull", "herring-gull"),
    "passer domesticus": ("house sparrow", "house-sparrow"),
    "coloeus monedula": ("jackdaw", "jackdaw"),
    "aegithalos caudatus": ("long-tailed tit", "long-tailed-tit"),
    "pica pica": ("magpie", "magpie"),
    "erithacus rubecula": ("robin", "robin"),
    "turdus philomelos": ("song thrush", "song-thrush"),
    "sturnus vulgaris": ("starling", "starling"),
    "columba palumbus": ("woodpigeon", "woodpigeon"),
    "troglodytes troglodytes": ("wren", "wren"),
    "turdus iliacus": ("redwing", "redwing"),
    "corvus frugilegus": ("rook", "rook"),
    "phylloscopus collybita": ("chiffchaff", "chiffchaff"),
    "psittacula krameri": ("ring-necked parakeet", "ring-necked-parakeet"),
    "branta leucopsis": ("barnacle goose", "barnacle-goose"),
    "ardea cinerea": ("grey heron", "grey-heron"),
    "fulica atra": ("coot", "eurasian-coot"),
    "pyrrhocorax pyrrhocorax": ("chough", "chough"),
    "branta canadensis": ("canada goose", "canada-goose"),
    "puffinus puffinus": ("manx shearwater", "manx-shearwater"),
    "motacilla alba": ("pied wagtail", "pied-wagtail"),
    "motacilla cinerea": ("grey wagtail", "grey-wagtail"),
    "haematopus ostralegus": ("oystercatcher", "oystercatcher"),
    "anthus pratensis": ("meadow pipit", "meadow-pipit"),
    "anas platyrhynchos": ("mallard", "mallard"),
    "passer montanus": ("tree sparrow", "tree-sparrow"),
    "turdus pilaris": ("fieldfare", "fieldfare"),
}
_BY_SCIENTIFIC = {scientific: slug for scientific, (_name, slug) in _SPECIES.items()}
_BY_NAME = {name: slug for name, slug in _SPECIES.values()}
_BY_NAME["eurasian coot"] = "eurasian-coot"
_BY_NAME["wood pigeon"] = "woodpigeon"
_BY_NAME["ring necked parakeet"] = "ring-necked-parakeet"


def rspb_species_url(name: str, scientific_name: str = "") -> str | None:
    """Return a direct verified RSPB profile, or None for unmatched species."""
    scientific = str(scientific_name or "").strip().casefold()
    slug = _BY_SCIENTIFIC.get(scientific)
    if not slug:
        common = str(name or "").strip().casefold()
        slug = _BY_NAME.get(common)
        if not slug:
            for prefix in ("eurasian ", "european ", "common "):
                if common.startswith(prefix):
                    slug = _BY_NAME.get(common[len(prefix):])
                    if slug:
                        break
    return RSPB_BASE + slug if slug else None
