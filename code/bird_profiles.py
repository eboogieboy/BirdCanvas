"""Small, reviewable UK species profiles for the GalleryOS field guide.

Data is keyed by scientific name to avoid BirdNET common-name differences.
This is intentionally a curated local subset, not a bulk sticker/art import.
Only verified BoCC5 labels are populated; missing values remain 'Not recorded'
rather than being guessed. See the linked RSPB guides for full descriptions.
No external API calls or generated image costs.
"""
from __future__ import annotations

from bird_rarity import COMMON_TO_SCIENTIFIC

# Scientific name: family, identifying features, habitat, diet, UK season,
# length in cm, UK Birds of Conservation Concern 5 colour (where verified).
FACTS = {
    "erithacus rubecula": ("Chats and flycatchers", "Orange-red face and breast, brown upperparts, and a fine bill.", "Gardens, woodland and hedges", "Insects, worms and berries", "Resident; winter visitors also occur", 14, ""),
    "turdus merula": ("Thrushes", "Male all-black with a yellow bill; female brown with a streaked throat.", "Gardens, parks and woodland", "Earthworms, insects, fruit", "Resident; numbers increase in winter", 25, ""),
    "cyanistes caeruleus": ("Tits", "Blue cap, yellow breast, white cheeks and a dark eye stripe.", "Gardens, hedgerows and woodland", "Caterpillars, insects, seeds", "Resident", 12, "Green"),
    "parus major": ("Tits", "Black head and broad black stripe down a yellow breast.", "Woodland, parks and gardens", "Insects, seeds and nuts", "Resident", 14, ""),
    "periparus ater": ("Tits", "Small tit with black head, white nape patch and pale wing bars.", "Conifer woodland and gardens", "Insects and conifer seeds", "Resident", 11, ""),
    "aegithalos caudatus": ("Tits", "Tiny, round-bodied bird with a remarkably long tail.", "Hedgerows, woodland and gardens", "Small insects and spiders", "Resident", 14, ""),
    "troglodytes troglodytes": ("Wrens", "Tiny brown bird with fine barring and an often cocked tail.", "Dense shrubs, gardens and undergrowth", "Small insects and spiders", "Resident", 10, ""),
    "prunella modularis": ("Accentors", "Grey head and breast, brown streaked back, fine pointed bill.", "Hedgerows and gardens", "Insects and small seeds", "Resident", 14, ""),
    "fringilla coelebs": ("Finches", "Male has pink breast and blue-grey head; both sexes show white wing bars.", "Woodland, parks and gardens", "Seeds and insects", "Resident; winter visitors", 15, ""),
    "chloris chloris": ("Finches", "Stocky greenish finch with conspicuous yellow wing and tail flashes.", "Gardens, farmland and woodland edges", "Seeds and buds", "Resident", 15, "Red"),
    "carduelis carduelis": ("Finches", "Red face, black-and-white head and vivid yellow wing stripe.", "Gardens, rough grassland and farmland", "Thistle and other seeds", "Resident; some winter movements", 12, ""),
    "passer domesticus": ("Sparrows", "Chunky brown sparrow; male has a grey crown and black bib.", "Buildings, gardens and farmland", "Seeds, grains and insects", "Resident", 15, "Red"),
    "sturnus vulgaris": ("Starlings", "Iridescent dark plumage and pointed bill; white spots in winter.", "Gardens, towns and open farmland", "Invertebrates, berries and fruit", "Resident; large winter influx", 21, "Red"),
    "turdus philomelos": ("Thrushes", "Warm brown upperparts and boldly spotted pale underparts.", "Gardens, woodland and hedges", "Worms, snails and berries", "Resident; additional winter birds", 23, ""),
    "larus argentatus": ("Gulls", "Large pale-grey-backed gull with pink legs and a heavy yellow bill.", "Coast, estuaries and urban areas", "Fish, invertebrates and scavenged food", "Resident; winter movements", 60, "Red"),
    "corvus corone": ("Crows", "Entirely black crow with broad wings and a heavy bill.", "Farmland, coast, parks and towns", "Omnivorous; carrion, insects and seeds", "Resident", 47, ""),
    "coloeus monedula": ("Crows", "Compact crow with a grey nape and pale eyes.", "Towns, cliffs and farmland", "Insects, seeds and scraps", "Resident", 34, ""),
    "pica pica": ("Crows", "Bold black-and-white plumage and very long iridescent tail.", "Parks, farmland and gardens", "Omnivorous", "Resident", 45, ""),
    "streptopelia decaocto": ("Pigeons and doves", "Pale grey-beige dove with a narrow black neck collar.", "Towns, gardens and farmland", "Seeds and grain", "Resident", 32, ""),
    "columba palumbus": ("Pigeons and doves", "Large grey pigeon with white neck and wing patches.", "Woodland, farmland and gardens", "Seeds, buds and leaves", "Resident; winter visitors", 41, ""),
    "turdus iliacus": ("Thrushes", "Small thrush with pale eyebrow and rusty-red flank patches.", "Woodland edges, parks and berry bushes", "Worms, insects and berries", "Mainly autumn and winter visitor", 21, ""),
    "phylloscopus collybita": ("Warblers", "Small olive-brown warbler with dark legs and a short pale eyebrow.", "Woodland, scrub and gardens", "Small insects", "Mostly spring to autumn; some overwinter", 11, ""),
    "psittacula krameri": ("Parrots", "Bright green, long-tailed parakeet with a red bill.", "Urban parks, gardens and woodland", "Seeds, fruit and buds", "Localised resident", 40, ""),
    "ardea cinerea": ("Herons", "Tall grey-and-white heron with long neck, legs and dagger-like bill.", "Ponds, wetlands, rivers and coast", "Fish and amphibians", "Resident", 94, ""),
    "branta leucopsis": ("Geese", "Small goose with a white face, black neck and barred grey back.", "Coasts, fields and wetlands", "Grasses and coastal plants", "Winter and passage visitor", 62, ""),
}

CONSERVATION_SOURCE = "UK Birds of Conservation Concern 5 (2021)"
CONSERVATION_URL = "https://www.bto.org/our-work/science/publications/reports/birds-conservation-concern"


def profile_for(name: str, scientific_name: str = "") -> dict:
    scientific = str(scientific_name or "").strip().casefold()
    common = str(name or "").strip().casefold()
    if common.startswith("eurasian "):
        common = common[8:]
    if common.startswith("european "):
        common = common[9:]
    key = scientific if scientific in FACTS else COMMON_TO_SCIENTIFIC.get(common, scientific)
    facts = FACTS.get(key)
    if not facts:
        return {
            "group": "Other / not yet profiled", "identification": "",
            "habitat": "", "diet": "", "season": "",
            "length_cm": None, "conservation": None,
            "conservation_source": CONSERVATION_SOURCE,
            "conservation_url": CONSERVATION_URL, "reviewed": False,
        }
    group, identification, habitat, diet, season, length_cm, conservation = facts
    return {
        "group": group, "identification": identification,
        "habitat": habitat, "diet": diet, "season": season,
        "length_cm": length_cm, "conservation": conservation or None,
        "conservation_source": CONSERVATION_SOURCE,
        "conservation_url": CONSERVATION_URL, "reviewed": True,
    }
