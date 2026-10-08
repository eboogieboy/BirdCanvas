import base64
import json
import os
from datetime import date
from pathlib import Path

from functools import lru_cache

from storage import get_birds, get_yesterday_birds
from generation_settings import excluded_birds
from paths import OUTPUT_DIR, DATA_DIR
import generation_ai
OUTPUT = OUTPUT_DIR / "final_scene.png"
CANDIDATE_DIR = OUTPUT_DIR / "candidates"
MAX_ATTEMPTS = 2
IMAGE_SIZE = "1024x1536"
MIN_FEATURED_BIRDS = 2
MAX_FEATURED_BIRDS = 4

@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def filter_birds(birds, terms=None):
    kept = []
    excluded = []
    terms = excluded_birds() if terms is None else terms

    for bird in birds:
        name = str(bird).strip()
        lowered = name.casefold()

        if any(term in lowered for term in terms):
            excluded.append(name)
        else:
            kept.append(name)

    if excluded:
        print("Excluded from artwork:", ", ".join(excluded))

    return kept


def load_birds_for_source(source):
    if source == "yesterday":
        birds = get_yesterday_birds()
    else:
        birds = get_birds()

    return filter_birds(birds)


def clean_json_text(text):
    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()

    if text.startswith("```"):
        text = text.replace("```", "").strip()

    return text


def current_season():
    month = date.today().month

    if month in [12, 1, 2]:
        return "winter"

    if month in [3, 4, 5]:
        return "spring"

    if month in [6, 7, 8]:
        return "summer"

    return "autumn"






from pathlib import Path as _Path

HISTORY_FILE = DATA_DIR / "creative_history.json"


def load_creative_history(limit=10):
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text())
        return data[-limit:]
    except Exception:
        return []




def extract_creative_dna(brief):
    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=f"""
You are the BirdCanvas Curator.

Analyse this creative brief and extract its Creative DNA.

Brief:
{json.dumps(brief, indent=2)}

Return ONLY JSON:

{{
  "dominant_family":"",
  "materials":[],
  "palette_type":"",
  "energy":"",
  "complexity":"",
  "surface":"",
  "geometry":"",
  "overall_character":""
}}
"""
    )
    try:
        return json.loads(clean_json_text(response.output_text))
    except Exception:
        return {
            "dominant_family":"unknown",
            "materials":[],
            "palette_type":"unknown",
            "energy":"unknown",
            "complexity":"unknown",
            "surface":"unknown",
            "geometry":"unknown",
            "overall_character":"unknown"
        }


def save_creative_history(
    movement,
    brief,
    critique,
    featured_birds=None,
    creative_dna=None,
):
    """Persist creative memory without making another paid API call."""
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    history = load_creative_history(limit=100)

    if isinstance(creative_dna, dict) and creative_dna:
        dna = creative_dna
    else:
        material_value = brief.get("materials", "")
        if isinstance(material_value, list):
            materials = material_value[:6]
        else:
            materials = [
                part.strip()
                for part in str(material_value).split(",")
                if part.strip()
            ][:6]

        dna = {
            "dominant_family": movement.get("name", "") or brief.get("style", ""),
            "materials": materials,
            "palette_type": brief.get("palette", ""),
            "energy": brief.get("mood", ""),
            "complexity": "",
            "surface": brief.get("visual_language", ""),
            "geometry": brief.get("composition", ""),
            "overall_character": brief.get("style_guidance", ""),
        }

    history.append({
        "date": str(date.today()),
        "movement": movement.get("name", ""),
        "materials": brief.get("materials", ""),
        "palette": brief.get("palette", ""),
        "composition": brief.get("composition", ""),
        "subject_balance": brief.get("subject_balance", ""),
        "originality": critique.get("originality", 0),
        "featured_birds": list(featured_birds or []),
        "creative_dna": dna,
    })

    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def select_featured_birds(birds):
    """Curate a small species set so the artwork is not an illustrated checklist."""
    available = list(dict.fromkeys(str(bird).strip() for bird in birds if str(bird).strip()))

    if len(available) <= MIN_FEATURED_BIRDS:
        return available, "All eligible species are featured because the collection is already small."

    minimum = MIN_FEATURED_BIRDS
    maximum = min(MAX_FEATURED_BIRDS, len(available))
    history = load_creative_history(limit=8)
    recent_featured = [
        str(bird).strip()
        for item in history
        for bird in item.get("featured_birds", [])
        if str(bird).strip()
    ]

    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=f"""
You are the BirdCanvas Curator.

BirdCanvas now uses its Magic Mirror as the factual bird list. The Samsung
Frame artwork does NOT need to illustrate every species heard.

Choose between {minimum} and {maximum} species from the eligible list below
to FEATURE in one beautiful contemporary artwork.

Eligible species:
{json.dumps(available, indent=2)}

Recently featured species:
{json.dumps(recent_featured, indent=2)}

Curation principles:
- artwork first; birds are source material, not a checklist
- choose the number of species that gives the strongest composition
- 2 or 3 species is often stronger than 4; use 4 only when it genuinely helps
- favour interesting contrasts of silhouette, scale, movement and colour
- give memorable or visually distinctive visitors a chance
- avoid repeating the same recent featured species when good alternatives exist
- common species may still be selected when they suit the artistic idea
- do not infer detection frequency or rarity from this list
- preserve the exact supplied species names
- do not invent a species

Return ONLY valid JSON:
{{
  "birds": ["exact species name"],
  "reason": "one concise curatorial reason"
}}
"""
    )

    try:
        result = json.loads(clean_json_text(response.output_text))
        selected = [
            str(bird).strip()
            for bird in result.get("birds", [])
            if str(bird).strip()
        ]

        if len(selected) != len(set(selected)):
            raise ValueError("Featured-bird selection contains duplicates.")
        if not minimum <= len(selected) <= maximum:
            raise ValueError("Featured-bird selection returned the wrong number of species.")
        if any(bird not in available for bird in selected):
            raise ValueError("Featured-bird selection invented or renamed a species.")

        return selected, str(result.get("reason", "")).strip()
    except Exception as error:
        appearances = {}
        for bird in recent_featured:
            key = bird.casefold()
            appearances[key] = appearances.get(key, 0) + 1

        indexed = list(enumerate(available))
        indexed.sort(key=lambda item: (appearances.get(item[1].casefold(), 0), item[0]))
        selected = [bird for _, bird in indexed[:min(3, len(indexed))]]
        return selected, f"Fallback curation after selector error: {error}"


def create_movement_options(birds, season, edition="daily"):
    bird_list = "\n".join(f"- {b}" for b in birds)

    history = load_creative_history()

    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=f"""
You are the Exhibition Programme Director for BirdCanvas.

Generate FIVE radically different exhibition movements for today's birds.

Imagine these are proposals from FIVE different world-class galleries competing to exhibit today's birds.

Each movement must come from a distinctly different artistic tradition, material language, compositional philosophy and emotional atmosphere.

Reusing similar materials, palettes, geometry, visual language or artistic traditions across movements is considered a failure.

Aim for maximum diversity while maintaining museum-quality contemporary art.

Recent creative history:
{json.dumps(history, indent=2)}

Treat the Creative DNA as the exhibition memory.

Avoid repeating the same dominant family, energy, palette type, geometry, surface language and material combinations across consecutive days.

Actively seek creative contrast while maintaining premium gallery quality.

Birds:
{bird_list}

Season: {season}
Edition: {edition}

Each movement must be unmistakably different from every other movement.

Across the FIVE movements, maximise diversity in:

- artistic tradition
- medium
- materials
- colour philosophy
- composition
- texture
- geometry
- cultural influences
- historical inspiration
- level of abstraction

Avoid repeating words, concepts or materials unless absolutely necessary.

Someone viewing the FIVE movement titles should immediately imagine FIVE completely different exhibitions.
Before returning your final list, critically review it.

If two movements feel similar, replace the weaker one.

Do not stop until all FIVE movements feel like they belong in completely different exhibitions.

The final list should maximise creative diversity rather than consistency.
Return ONLY valid JSON:

[
  {{
    "name":"",
    "creative_direction":"",
    "materials":"",
    "composition":"",
    "why_it_is_distinct":""
  }}
]
"""
    )

    try:
        return json.loads(clean_json_text(response.output_text))
    except Exception:
        return [
            {
                "name":"Quiet Mineral Abstraction",
                "concept":"Layered contemporary abstraction.",
                "materials":"Plaster, pigment, wood.",
                "composition":"Open vertical composition.",
                "why_it_is_distinct":"Fallback."
            }
        ]




def select_movement(movements, birds):
    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=f"""
You are the Art Director for BirdCanvas.

Birds:
{", ".join(birds)}

Here are candidate exhibition movements:

{json.dumps(movements, indent=2)}

Choose the SINGLE strongest movement.

Judge on:
- originality
- suitability for a premium home
- compatibility with today's birds
- distinction from familiar BirdCanvas styles

Return ONLY JSON:

{{
  "index": 1,
  "reason": ""
}}
"""
    )

    try:
        result=json.loads(clean_json_text(response.output_text))
        idx=max(1,min(len(movements),int(result["index"])))-1
        return movements[idx], result.get("reason","")
    except Exception:
        return movements[0],"Fallback selection."



SUBJECT_BALANCE_MODES = (
    "environment-led",
    "subtle-wildlife",
    "shared",
    "bird-led",
)

# Long-term mix: 70% art/setting-led, 20% shared, 10% bird-led.
# Keep both art-first modes in rotation for distinct visual approaches.
SUBJECT_BALANCE_WEIGHTS = {
    "environment-led": 0.4,
    "subtle-wildlife": 0.3,
    "shared": 0.2,
    "bird-led": 0.1,
}


def select_subject_balance():
    """Choose the most underrepresented weighted mode in recent history."""
    history = load_creative_history(limit=10)
    recent = [
        str(item.get("subject_balance", "")).strip()
        for item in history
        if str(item.get("subject_balance", "")).strip() in SUBJECT_BALANCE_MODES
    ]
    counts = {mode: recent.count(mode) for mode in SUBJECT_BALANCE_MODES}
    last = recent[-1] if recent else None

    # Weighted deficit balances the collection without a random generator
    # or any additional API call. Avoid repeating the previous mode on ties.
    return max(
        SUBJECT_BALANCE_MODES,
        key=lambda mode: (
            SUBJECT_BALANCE_WEIGHTS[mode] * (len(recent) + 1) - counts[mode],
            mode != last,
            -SUBJECT_BALANCE_MODES.index(mode),
        ),
    )


def create_creative_brief(birds, movement=None, edition="daily", observation_window=""):

    bird_list = "\n".join(f"- {bird}" for bird in birds)
    season = current_season()
    subject_balance = select_subject_balance()

    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=f"""
You are the Creative Director for BirdCanvas.

BirdCanvas creates changing portrait-format contemporary artworks for a Samsung Frame television mounted in portrait orientation, inspired by birds genuinely heard during a defined time window.

Edition: {edition}
Observation window: {observation_window or "current bird list"}

BirdCanvas values:
- beautiful artwork before bird inventory
- beauty over realism
- calm over drama
- simplicity over clutter
- originality over obviousness
- premium contemporary home aesthetics
- selected birds remain recognisable, but this is not wildlife-calendar art

Subject balance for THIS artwork: {subject_balance}

Interpret that balance as follows:
- bird-led: birds may be the principal visual feature, but the work must still contain a convincing wider world
- shared: birds and environment/objects/architecture share visual importance
- environment-led: the setting, architecture, objects, furniture, landscape, material or light is the main visual subject; birds live naturally within it
- subtle-wildlife: the artwork works first as a complete scene or composition and the birds are smaller discoveries noticed on closer viewing

Do not override this selected balance just because birds supplied the source data.

The wider scene may include, when artistically appropriate, buildings, windows,
walls, rooftops, sheds, greenhouses, furniture, chairs, tables, fences, paths,
garden structures, domestic objects, vessels, textiles, plants, trees, water,
weather, reflections, landscape, interiors or views through windows.

These are genuine compositional subjects, not merely background decoration.

The Magic Mirror carries the factual record of all birds heard. This Frame
artwork is a CURATED artistic response, using only a small selected set.

Sense of place:
BirdCanvas lives in North Shields on the north-east coast of England.

Do not create literal coastal scenes unless the birds naturally suggest them.

Instead allow the location to quietly influence the artwork in subtle ways such as:
- cool North Sea light
- sea glass colours
- sandstone
- weathered wood
- harbour textures
- wind
- coastal skies
- muted maritime colours
- salt-worn surfaces
- open horizons

These should influence mood, colour, texture and composition rather than become the subject.

The viewer should rarely think "this is a seaside picture".

Instead they should feel a quiet northern coastal atmosphere.

Season:
The current season is {season}.

Allow the season to influence colour, lighting, texture, atmosphere, materials
and compositional feeling without using obvious seasonal clichés.

Selected birds for this artwork:
{bird_list}

Selected exhibition movement:

Name: {movement.get("name","") if movement else ""}

Creative direction: {movement.get("creative_direction","") if movement else ""}

Materials: {movement.get("materials","") if movement else ""}

Composition: {movement.get("composition","") if movement else ""}

Develop THIS movement further. Do not invent a different movement.

Create a curator's brief for today's exhibition.

The artwork must be conceived as an artwork first.

The selected birds are source material and visual motifs, not a checklist.
The image may be abstract, architectural, textural, landscape-adjacent,
object-based, painterly, sculptural or otherwise led by the movement.

Do not give every bird equal visual weight.
One bird may be the hero; the others may be supporting, quiet or partially
embedded in material, pattern, light, shadow or negative space.

Every selected species should retain a light visual identity, but the brief must
not turn into an ornithology specification. Use one or two restrained identity
hints per species at most; do not enumerate field marks, anatomy or plumage.

The artistic medium must transform the birds. A conventionally rendered bird
placed inside an abstract or sculptural composition is a failure of integration.

Do not force birds into separate compartments or reserved positions.
Do not make the composition look like a field-guide plate.

Invent a completely new exhibition style for this artwork.

The style may draw inspiration from ANY historical or contemporary visual tradition including painting,
printmaking, sculpture, ceramics, textiles, architecture, photography processes, glass, illustration,
industrial design, indigenous traditions, folk art, mixed media or combinations of these.

Do NOT imitate any living artist.
Avoid clichés and repetitive choices.
Feel free to invent sophisticated hybrid styles.

Return ONLY valid JSON in this exact format:

{{
  "collection": "",
  "style": "",
  "style_guidance": "",
  "curator_notes": "",
  "mood": "",
  "visual_language": "",
  "palette": "",
  "composition": "",
  "subject_balance": "",
  "bird_integration": "",
  "materials": "",
  "visual_focus": "",
  "hero_birds": [],
  "supporting_birds": [],
  "avoid": []
}}

Rules:
- subject_balance must be exactly "{subject_balance}".
- Every selected species must be represented, but the artwork does not need to be about birds at first glance.
- In environment-led and subtle-wildlife modes, do not enlarge or centre birds merely to make them more obvious.
- Buildings, furniture, objects, structures, landscape, plants, weather, light and interior/exterior space may carry the composition.
- bird_integration should describe how the artistic medium transforms the birds, not their detailed anatomy, plumage or field marks.
- bird_integration must not ask for a normal naturalistic bird simply placed inside an abstract composition.
- hero_birds may contain zero or one selected species.
- supporting_birds should contain the remaining selected species when useful.
- visual_focus must describe the artwork itself: light, material, texture, geometry, colour or composition, never a bird.
- The brief should encourage a distinctive artwork, not a predictable bird illustration.
- The style should feel suitable for a premium gallery.
- Do not imitate a living artist.
"""
    )

    try:
        text = clean_json_text(response.output_text)
        brief = json.loads(text)
        valid = set(birds)
        hero = [
            str(item).strip()
            for item in brief.get("hero_birds", [])
            if str(item).strip() in valid
        ][:1]
        supporting = [
            str(item).strip()
            for item in brief.get("supporting_birds", [])
            if str(item).strip() in valid and str(item).strip() not in hero
        ]
        for bird in birds:
            if bird not in hero and bird not in supporting:
                supporting.append(bird)
        brief["subject_balance"] = subject_balance
        brief["hero_birds"] = hero
        brief["supporting_birds"] = supporting
        return brief

    except Exception as error:
        print(f"Creative brief failed, using fallback: {error}")

        return {
            "collection": "Quiet Northern Forms",
            "style": "Contemporary material abstraction",
            "style_guidance": "Create elegant contemporary wall art led by composition, material and atmosphere.",
            "curator_notes": "The birds are selected visual cues inside a broader artwork.",
            "mood": "calm",
            "visual_language": "minimal contemporary portrait-format wall art with restrained abstract forms",
            "palette": "warm neutrals, sea glass, soft greens, charcoal, sandstone and linen",
            "composition": "9:16 portrait composition with strong vertical balance and generous negative space",
            "subject_balance": subject_balance,
            "bird_integration": "Integrate the selected birds subtly into the artistic language while keeping each species recognisable.",
            "materials": "Layered paper, limewashed wood, mineral pigments and subtle textured surfaces.",
            "visual_focus": "The composition and materials should attract attention before the birds are noticed.",
            "hero_birds": [],
            "supporting_birds": list(birds),
            "avoid": [
                "wildlife calendar art",
                "field-guide plate composition",
                "clip art",
                "busy garden scenes",
                "cute cartoon style"
            ]
        }


def format_list(title, items):
    if not items:
        return ""

    lines = [title]

    for item in items:
        lines.append(f"• {item}")

    return "\n".join(lines)


def build_prompt(birds, brief, correction=None, edition="daily", observation_window=""):

    bird_list = "\n".join(f"• {bird}" for bird in birds)
    avoid_text = "\n".join(f"• {item}" for item in brief.get("avoid", []))

    correction_text = ""

    if correction:
        correction_text = f"""

QUALITY REVIEW

The previous artwork failed validation.

Verifier findings:

{correction}

This retry MUST correct every issue above.

The artistic style, movement, materials, colour palette and composition were
successful and should be preserved wherever possible.
Treat the previous artwork as Revision 1.

Create Revision 2 of the same artwork.

Do not produce a different interpretation.

The goal is to correct the verifier findings while making the smallest possible changes to the successful artwork.
Do NOT redesign the artwork from scratch.

Instead:

- Reserve a separate visible position for every missing species before composing.
- Every missing species becomes a mandatory primary subject.
- Do not remove species that were already present.
- Do not duplicate any species.
- Preserve correct anatomy and identifying plumage.
- Before rendering, internally confirm that every expected species appears exactly once.

Only when every verification issue has been corrected should the artwork be rendered.
"""

    return f"""
# BIRDCANVAS

You are creating a museum-quality work of contemporary wall art.

This is NOT wildlife illustration.

This is NOT a bird painting.

This is NOT a greetings card.

This is NOT a nature scene.

Imagine this artwork hanging in the Design Museum, Tate Modern, MoMA or Louisiana Museum of Modern Art.

This is contemporary bird artwork.

The artwork must feel like premium contemporary art, not a wildlife illustration.

Today's birds are the creative trigger for the artwork, not necessarily its dominant visual subject.

The selected exhibition movement and subject balance determine the artistic language, materials and composition.

The birds must remain recognisable within that artistic language, but their prominence may range from leading subjects to quiet discoveries within a larger scene.

The viewer should first see a beautiful contemporary artwork.

Architecture, furniture, objects, landscape, plants, weather, water, interiors, structures, light and material may be as important as—or more important than—the birds.

The artistic movement should integrate the birds naturally rather than forcing them to dominate.

A person viewing the Samsung Frame from across the room should understand that this is artwork inspired by today's birds.

Portrait format.

Designed specifically for a 32-inch Samsung Frame television mounted vertically.

The final displayed artwork will be 9:16 portrait at exactly 1080 × 1920 pixels.

The image generator produces a slightly wider 2:3 portrait source which will be centre-cropped to 9:16.

Compose specifically for that final 9:16 crop.

Keep every bird, face, body and important visual element safely inside the central 80% of the canvas width.

Do not place important birds or identifying features close to the extreme left or right edges.

Background textures, colour and abstract material may extend fully beyond that safe area.

The finished artwork must fill the entire portrait screen with no border, mount, mat or blank margin.

{bird_list}

## Creative brief

Collection:
{brief["collection"]}

Mood:
{brief["mood"]}

Visual language:
{brief["visual_language"]}

Palette:
{brief["palette"]}

Composition:
{brief["composition"]}

Bird integration:
{brief.get("bird_integration", "")}

Suggested materials:
{brief.get("materials", "")}

Visual focus:
{brief.get("visual_focus", "")}
## Bird integration

Every listed bird must appear exactly once.

Do not duplicate birds.

Do not invent species.

The birds should emerge naturally from the artistic language.

They may appear as:

• silhouettes

• relief carving

• stitched forms

• ceramic decoration

• woven shapes

• paper collage

• etched marks

• sculptural fragments

• stained glass

• architectural ornament

• abstract motifs

Recognition matters.

Every listed bird must be identifiable.

Stylisation is encouraged, but do not reduce birds to vague marks or hidden symbols.

The viewer should be able to recognise the species through shape, colour, posture or distinctive features.

Birds should not dominate the entire canvas, but they must remain clearly visible.

## Bird rules

Every listed species must appear somewhere within the artwork.

Do not invent additional bird species.

Do not duplicate species.

The birds should be integrated into the artistic language rather than presented as individual wildlife subjects.

A viewer should be able to discover each bird over time.

Recognition is important.

Prominence is not.

The artwork must remain successful even if the viewer never consciously notices every bird.

## BirdCanvas philosophy

## Artistic priorities

The image should be judged in this order:

1. Is it extraordinary contemporary art?

2. Would someone choose to hang it in their home?

3. Does it have an original visual language?

4. Does it reward repeated viewing?

5. Are today's birds embedded within it?

Never sacrifice recognisability of the birds. Contemporary interpretation is encouraged, but a casual viewer should immediately recognise that this is artwork about birds.

Simplicity comes before detail.

Wonder comes before accuracy.

Silence is part of the composition.

Negative space is as important as paint.

Avoid obvious solutions.

Take creative risks.

Create something memorable.

## Artistic style

Today's exhibition style

{brief.get("style","Contemporary gallery art")}

Creative guidance

{brief.get("style_guidance","Create an original museum-quality artwork.")}

Curator notes

{brief.get("curator_notes","")}

## Avoid

{avoid_text}

Also avoid:
• wildlife calendar art
• greetings cards
• clip art
• stock illustration
• children's illustration
• AI cliché imagery
• overly busy scenes
• text
• labels
• borders
• signatures
• watermarks
• humans

## Final instruction

Forget everything you know about bird illustration.

Create a piece of contemporary art.

Every listed bird is an essential primary subject within the artwork.

Each bird must remain clearly visible, individually readable and recognisable, while the complete image still feels collectible.
It should look expensive.

It should reward repeated viewing.

It should surprise professional designers.

Someone seeing the artwork without context should never assume it was generated from a list of birds.

{correction_text}
"""






def compose_structured_image_prompt(birds, brief):
    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=f"""
You are BirdCanvas Prompt Composer.

Convert the creative brief into a structured specification for gpt-image-1.

Birds:
{", ".join(birds)}

Brief:
{json.dumps(brief, indent=2)}

Return ONLY JSON:

{{
  "title":"",
  "subject":"",
  "composition":"",
  "materials":"",
  "lighting":"",
  "colour":"",
  "bird_strategy":"",
  "mood":"",
  "rendering_priorities":[
    "...","..."
  ],
  "avoid":[]
}}
"""
    )
    try:
        return json.loads(clean_json_text(response.output_text))
    except Exception:
        return {
            "title":"BirdCanvas",
            "subject":"Contemporary artwork",
            "composition":brief.get("composition",""),
            "materials":brief.get("materials",""),
            "lighting":"Soft natural light",
            "colour":brief.get("palette",""),
            "bird_strategy":brief.get("bird_integration",""),
            "mood":brief.get("mood",""),
            "rendering_priorities":["Museum quality"],
            "avoid":brief.get("avoid",[])
        }


def _fallback_bird_position(index, total):
    return (
        f"reserved visual position {index} of {total}, "
        "inside the central 80% of the portrait canvas"
    )



def create_bird_plan(birds):
    """Create a lightweight recognition guide without dictating composition."""
    exact_count = len(birds)
    numbered_birds = "\n".join(
        f"{index}. {bird}"
        for index, bird in enumerate(birds, start=1)
    )

    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=f"""
You are the BirdCanvas Ornithology Adviser.

For each selected species below, provide only the broad visual cues needed to
keep it recognisable inside contemporary artwork.

The artwork is viewed in Britain, so use normal British/European field
identification characteristics where relevant.

Selected species:
{numbered_birds}

Return ONLY valid JSON:
{{
  "birds": [
    {{
      "index": 1,
      "species": "",
      "art_cue": "",
      "recognition_cues": ["", ""],
      "avoid_confusions": [""]
    }}
  ]
}}

Rules:
- Return exactly {exact_count} entries in the supplied order.
- Preserve exact species names.
- Give each species one art_cue: a short, evocative 6-14 word identity hint suitable for an artist.
- art_cue should use only one or two broad signals such as silhouette, movement or a signature colour accent.
- Give each species 2 or 3 broader recognition_cues for the verifier only.
- Prefer silhouette, bill shape, overall colour blocking, head pattern,
  tail shape or characteristic posture in recognition_cues.
- Do not specify a position, bounding box, exact scale or composition.
- Do not demand every small field mark.
- Stylisation and deep integration into the artwork are allowed.
- avoid_confusions should mention only the most important likely visual mix-up.
- The image generator will receive art_cue, NOT the detailed recognition_cues.
- The detailed guide protects recognisability during verification; it must not dictate the artwork.
"""
    )

    try:
        result = json.loads(clean_json_text(response.output_text))
        planned = result.get("birds", [])

        if len(planned) != exact_count:
            raise ValueError("Bird plan returned the wrong number of species.")

        cleaned = []
        for index, expected_species in enumerate(birds, start=1):
            item = planned[index - 1]
            actual_species = str(item.get("species", "")).strip()
            if actual_species != expected_species:
                raise ValueError(
                    f"Bird plan changed species order: expected {expected_species!r}, received {actual_species!r}"
                )

            art_cue = str(item.get("art_cue", "")).strip()
            cues = [
                str(value).strip()
                for value in item.get("recognition_cues", [])
                if str(value).strip()
            ]
            confusions = [
                str(value).strip()
                for value in item.get("avoid_confusions", [])
                if str(value).strip()
            ]
            if not art_cue:
                raise ValueError(f"No art cue for {expected_species}.")
            if not cues:
                raise ValueError(f"No recognition cues for {expected_species}.")

            cleaned.append({
                "index": index,
                "species": expected_species,
                "art_cue": art_cue,
                "recognition_cues": cues[:3],
                "avoid_confusions": confusions[:2],
            })

        return cleaned

    except Exception as error:
        print(f"Bird recognition planning failed; using fallback: {error}")
        return [
            {
                "index": index,
                "species": species,
                "art_cue": f"{species}: recognisable silhouette with one restrained signature colour or shape cue",
                "recognition_cues": [
                    "recognisable species-specific silhouette",
                    "characteristic broad colour or marking pattern",
                ],
                "avoid_confusions": [
                    "do not make it clearly resemble another species"
                ],
            }
            for index, species in enumerate(birds, start=1)
        ]



def format_art_cues_for_prompt(bird_plan):
    sections = []

    for bird in bird_plan:
        cue = str(bird.get("art_cue", "")).strip()
        if not cue:
            cue = f'{bird["species"]}: recognisable identity through one restrained visual cue'
        sections.append(
            f'FEATURED SPECIES {bird["index"]}: {bird["species"]}\n'
            f'ART IDENTITY CUE: {cue}'
        )

    return "\n\n".join(sections)


def format_bird_plan_for_prompt(bird_plan):
    sections = []

    for bird in bird_plan:
        cues = "; ".join(bird["recognition_cues"])
        confusions = "; ".join(bird.get("avoid_confusions", []))
        section = (
            f'FEATURED SPECIES {bird["index"]}: {bird["species"]}\n'
            f'RECOGNITION CUES: {cues}'
        )
        if confusions:
            section += f"\nAVOID CLEAR CONFUSION WITH: {confusions}"
        sections.append(section)

    return "\n\n".join(sections)



def create_image_prompt(
    birds,
    brief,
    bird_plan,
    correction=None,
):
    featured_count = len(birds)
    art_cues_text = format_art_cues_for_prompt(bird_plan)
    correction_text = ""

    if correction:
        correction_text = f"""

THIS IS A CORRECTIVE RETRY.

The previous generated artwork had a major species-level failure:

{correction}

Correct the major failure while preserving the successful artistic idea,
materials, atmosphere and composition as much as possible.
"""

    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=f"""
You are the Image Prompt Writer for BirdCanvas.

Write the artistic portion of ONE image-generation prompt for gpt-image-1.

BirdCanvas is premium contemporary gallery art for a vertically mounted
32-inch Samsung Frame. The source canvas is 1024 × 1536 portrait and is
centre-cropped to exactly 1080 × 1920.

There are {featured_count} FEATURED SPECIES. They were curated from a larger
factual list of birds heard in the garden.

Creative brief:
{json.dumps(brief, indent=2)}

Art identity cues:
{art_cues_text}

The detailed ornithological recognition guide is intentionally withheld from
the image generator. A separate verifier will check species identity afterwards.

{correction_text}

Priorities:
- make a beautiful, original artwork first
- obey the creative brief's subject_balance; it controls how visually prominent the birds should be
- let the selected movement control composition, atmosphere and material
- architecture, buildings, furniture, objects, garden structures, plants, landscape, weather, water, windows, interiors and light may be major or dominant features
- environmental features should feel intentionally composed, not like generic background scenery
- the birds do not need equal prominence or separate positions
- the birds do not need to be the main subject; in environment-led or subtle-wildlife work they may be small, distant, partially obscured or discovered later
- one bird may be a hero only when the selected subject_balance supports it; otherwise keep all birds subordinate to the wider artwork
- each featured species should remain recognisable through only the light art identity cue supplied
- transform the birds into the movement's own material language rather than drawing ordinary birds and decorating around them
- a conventionally rendered naturalistic bird placed inside an abstract, sculptural or graphic scene is a failure
- stylisation, abstraction and integration into pattern/material/light are strongly preferred
- do not turn the image into a wildlife plate or a grid of bird portraits
- do not add obvious unlisted real bird species
- important recognisable bird forms should survive the final 9:16 crop
- background, texture and abstract material may fill the entire canvas

Do not explain your work. Return only the finished image prompt.
"""
    )

    try:
        artistic_prompt = response.output_text.strip()
    except Exception:
        artistic_prompt = brief.get(
            "style_guidance",
            "Create premium contemporary gallery art.",
        )

    final_prompt = f"""
{artistic_prompt}

FEATURED SPECIES ART IDENTITY CUES

{art_cues_text}

BIRDCANVAS EXECUTION RULES

- Include every featured species in an identifiable but transformed way.
- Do not force separate compartments, reserved coordinates or equal scale.
- Use only the supplied lightweight identity cues; do not elaborate them into field-guide anatomy.
- The birds should inherit the artwork's material, geometry, texture and visual logic.
- A normally rendered naturalistic bird inserted into an otherwise abstract, sculptural or graphic artwork is a failure.
- Birds may emerge from material, pattern, shadow, reflection, negative space,
  abstraction or landscape structure if they remain recognisable.
- Birds may perch on, move through or quietly inhabit architecture, furniture,
  garden structures, domestic objects, plants, water, landscape or interior space.
- Do not automatically centre, enlarge or foreground a bird.
- One species may dominate only when the creative brief's subject_balance supports it.
- In environment-led and subtle-wildlife modes, let non-bird elements clearly carry the visual hierarchy.
- Do not add an obvious real bird species that was not selected.
- The artwork must remain compelling even before the viewer consciously notices
  every bird.
- When minor ornithological detail conflicts with a stronger composition,
  the stronger composition wins.
- This must not look like a field-guide plate, wildlife calendar or checklist.

{correction_text}
""".strip()

    return final_prompt



def generate_image(prompt):
    final_prompt = f"""
{prompt}

MANDATORY DISPLAY FORMAT:

- Portrait orientation only.
- Source canvas: 1024 × 1536.
- Final display crop: 1080 × 1920, exact 9:16 portrait.
- Keep important recognisable forms crop-safe.
- Artwork must be full bleed.
- No border, mount, mat, blank margin or landscape layout.

ART-FIRST BIRD GUIDANCE:

- This is a contemporary artwork inspired by selected bird species, not an
  identification plate.
- Every selected species should be recognisable somewhere in the finished work.
- Bird prominence must follow the supplied creative brief: birds may be principal,
  shared, subordinate or deliberately subtle within the larger artwork.
- Buildings, furniture, structures, domestic objects, plants, landscape, water,
  weather, windows, interiors, reflections and light are allowed to become the
  dominant visual features.
- Small, distant, partially obscured or quietly perched birds are valid when the
  selected subject balance calls for them.
- Do not automatically make a bird the focal point just because birds triggered
  the artwork.
- Use only a few broad identity signals; do not construct a complete field-guide rendering.
- The selected birds should be transformed by the chosen medium, not painted conventionally and placed on top of it.
- If the surrounding work is abstract, sculptural, textile, ceramic, architectural or graphic, the birds must visibly belong to that same material language.
- Do not add obvious unlisted real bird species.
- Do not arrange the birds as equal isolated specimens.
- Composition, atmosphere, material, light and beauty are the primary visual
  priorities.

Before rendering, ensure the selected species are present without sacrificing
the integrity of the artwork.
"""

    result = _client().images.generate(
        model="gpt-image-1",
        prompt=final_prompt,
        size=IMAGE_SIZE,
        quality="medium"
    )

    return base64.b64decode(result.data[0].b64_json)


def save_image(image_bytes, output_path=OUTPUT):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(image_bytes)


def image_to_data_url(path):
    image_bytes = Path(path).read_bytes()
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    return f"data:image/png;base64,{encoded}"




def critique_artwork(expected_birds, brief, image_path):
    image_url = image_to_data_url(image_path)

    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=[
            {
                "role":"user",
                "content":[
                    {
                        "type":"input_text",
                        "text":f"""
You are the BirdCanvas Art Critic.

Creative brief:
{json.dumps(brief, indent=2)}

Score this artwork from 1-10 for:
- originality
- adherence to the movement
- contemporary art quality
- bird integration

For bird integration, score highly only when the birds genuinely inherit the
movement's material and visual language. If ordinary or naturalistic birds are
simply placed into an otherwise abstract/sculptural/graphic composition, bird
integration should score 3 or below.

Return ONLY JSON:

{{
  "originality":0,
  "movement":0,
  "art_quality":0,
  "bird_integration":0,
  "summary":""
}}
"""
                    },
                    {
                        "type":"input_image",
                        "image_url":image_url
                    }
                ]
            }
        ]
    )

    try:
        return json.loads(clean_json_text(response.output_text))
    except Exception:
        return {
            "originality":0,
            "movement":0,
            "art_quality":0,
            "bird_integration":0,
            "summary":"Critique unavailable."
        }



def verify_image(expected_birds, bird_plan):
    image_url = image_to_data_url(OUTPUT)
    plan_text = json.dumps({"birds": bird_plan}, indent=2)

    response = _client().responses.create(
        model="gpt-5.6-sol",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"""
You are the BirdCanvas Ornithology Verifier.

This is contemporary artwork, not a field-guide illustration. Verify only
whether the CURATED featured species remain reasonably recognisable.

Featured species recognition guide:
{plan_text}

Evaluate EACH featured species independently.

Return ONLY valid JSON:
{{
  "passed": true,
  "bird_results": [
    {{
      "species": "",
      "status": "correct",
      "severity": "none",
      "problems": []
    }}
  ],
  "extra_birds": [],
  "issues": []
}}

Allowed status values:
- "correct"
- "missing"
- "incorrect"
- "uncertain"

Allowed severity values:
- "none"
- "minor"
- "major"

Use "major" only when:
- a featured species is genuinely missing
- a featured species clearly looks like a different species
- an obvious, visually prominent unlisted real bird species changes the curated set

Use "minor" when:
- the species is still reasonably identifiable
- one recognition cue is softened or omitted
- anatomy is stylised but still readable
- the bird is small, partially embedded, partly obscured or compositionally unusual
- colour or a fine marking is imperfect

Verification rules:
- Include one bird_results entry for every featured species in supplied order.
- Preserve exact species names.
- Do not demand photographic realism.
- Do not assess position, equal prominence, exact scale or full-body visibility.
- Do not fail artistic abstraction when the species remains recognisable.
- extra_birds should list only clearly identifiable, prominent additional real
  bird species, never decorative motifs, shadows or ambiguous abstract forms.
- passed may be true when every featured species is reasonably identifiable and
  there is no prominent unlisted species.
- Be conservative: composition and artistry intentionally take priority over
  minor ornithological precision.
"""
                    },
                    {
                        "type": "input_image",
                        "image_url": image_url,
                    },
                ],
            }
        ],
    )

    result = json.loads(clean_json_text(response.output_text))
    bird_results = result.get("bird_results", [])

    if len(bird_results) != len(expected_birds):
        result["passed"] = False
        result.setdefault("issues", []).append(
            "Verifier did not return one result for every featured species."
        )
        return result

    for expected, bird_result in zip(expected_birds, bird_results):
        if str(bird_result.get("species", "")).strip() != expected:
            result["passed"] = False
        if bird_result.get("status") != "correct":
            result["passed"] = False

    if result.get("extra_birds"):
        result["passed"] = False

    return result


def verification_has_major_failure(verification):
    """
    Return True only when another paid image-generation attempt is justified.

    Minor ornithological imperfections are deliberately accepted so
    BirdCanvas can keep generation costs low while still producing fresh
    artwork every day.
    """

    if verification.get("extra_birds"):
        return True

    for result in verification.get(
        "bird_results",
        [],
    ):
        severity = str(
            result.get("severity", "")
        ).strip().lower()

        status = str(
            result.get("status", "")
        ).strip().lower()

        # Missing birds are always worth correcting.
        if status == "missing":
            return True

        if severity == "major":
            return True

    return False



def build_verification_correction(
    verification,
):
    """Build a retry focused only on genuine species-level failures."""
    corrections = []
    preserve = []

    for result in verification.get("bird_results", []):
        species = str(result.get("species", "")).strip()
        status = str(result.get("status", "")).strip().lower()
        severity = str(result.get("severity", "minor")).strip().lower()
        problems = [
            str(problem).strip()
            for problem in result.get("problems", [])
            if str(problem).strip()
        ]

        if status == "correct" and severity != "major":
            if species:
                preserve.append(species)
            continue

        if status == "missing" or severity == "major":
            detail = "; ".join(problems) if problems else "major species error"
            corrections.append(f"{species}: {status}. {detail}")

    for extra in verification.get("extra_birds", []):
        extra_text = str(extra).strip()
        if extra_text:
            corrections.append(f"Remove this prominent unlisted bird: {extra_text}")

    if preserve:
        corrections.append(
            "Preserve these already recognisable species without making them more "
            "literal or prominent: " + ", ".join(preserve) + "."
        )

    if not corrections:
        corrections.append(
            "Correct only genuine missing, substituted or prominent unlisted species."
        )

    corrections.append(
        "Do not spend the retry improving minor field marks, positions or anatomy. "
        "Preserve the artwork-first composition."
    )

    return "\n".join(f"- {item}" for item in corrections)



def compose(source="today", birds=None, edition="daily", observation_window="", excluded_terms=None):

    generation_ai.reset_usage()

    print("compose() started")
    print("Loading birds...")
    eligible_birds = list(birds) if birds is not None else load_birds_for_source(source)
    eligible_birds = filter_birds(eligible_birds, excluded_terms)
    print(f"Loaded {len(eligible_birds)} eligible birds after filtering")

    if not eligible_birds:
        print(f"No birds recorded in {source}.")
        return None

    history = load_creative_history(limit=10)

    birds, curation_reason = generation_ai.select_featured_birds(
        eligible_birds,
        history=history,
        minimum=MIN_FEATURED_BIRDS,
        maximum=MAX_FEATURED_BIRDS,
    )
    print(f"Curated {len(birds)} featured birds from {len(eligible_birds)} eligible species")
    print("Featured birds:", ", ".join(birds))
    if curation_reason:
        print("Curation reason:", curation_reason)

    print("Loading Bird Recognition Guide...")
    bird_plan = generation_ai.create_bird_plan(birds)

    subject_balance = select_subject_balance()
    print("Subject balance:", subject_balance)

    print("Creating consolidated creative direction...")
    direction = generation_ai.create_art_direction(
        birds,
        bird_plan,
        history=history,
        season=current_season(),
        edition=edition,
        observation_window=observation_window,
        subject_balance=subject_balance,
    )

    movements = direction["movement_options"]
    selected_movement = direction["selected_movement"]
    selection_reason = direction.get("selection_reason", "")
    brief = direction["brief"]
    creative_dna = direction.get("creative_dna", {})
    base_prompt = direction["image_prompt"]

    print(f"BirdCanvas source: {source}")
    print(f"Image size: {IMAGE_SIZE}")
    print("Selected movement:", selected_movement.get("name", "Untitled"))
    print("Creative brief:")
    print(json.dumps(brief, indent=2))
    print()

    correction = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"Generating artwork attempt {attempt}/{MAX_ATTEMPTS}...")

        if correction:
            prompt = generation_ai.build_retry_prompt(base_prompt, correction)
        else:
            prompt = base_prompt

        print("Final image prompt:")
        print(prompt)
        print()

        image_bytes = generation_ai.generate_image(
            prompt,
            size=IMAGE_SIZE,
            quality="medium",
        )
        save_image(image_bytes)

        print("Reviewing artwork and featured species...")
        try:
            review = generation_ai.review_artwork(
                birds,
                brief,
                OUTPUT,
                bird_plan,
            )
            verification = review["verification"]
            critique = review["critique"]
        except Exception as error:
            print(f"Artwork review failed, keeping generated artwork: {error}")
            return {
                "birds": birds,
                "brief": brief,
                "output": str(OUTPUT),
                "generation": {
                    "eligible_birds": eligible_birds,
                    "featured_birds": birds,
                    "curation_reason": curation_reason,
                    "movement_options": movements,
                    "selected_movement": selected_movement,
                    "selection_reason": selection_reason,
                    "bird_plan": bird_plan,
                    "image_prompt": prompt,
                    "review_error": str(error),
                    "attempts_used": attempt,
                    "api_profile": generation_ai.model_profile(),
                    "api_usage": generation_ai.usage_snapshot(),
                },
            }

        print("Verification results:")
        print(json.dumps(verification, indent=2))

        print()
        print("Art Director critique")
        print("---------------------")
        for key, value in critique.items():
            print(f"{key}: {value}")

        major_failure = verification_has_major_failure(verification)

        if not major_failure:
            if verification.get("passed") is True:
                print("✓ Featured-species verification passed.")
            else:
                print(
                    "✓ Only minor species inaccuracies detected. "
                    "Accepting artwork without another paid generation."
                )

            save_creative_history(
                selected_movement,
                brief,
                critique,
                featured_birds=birds,
                creative_dna=creative_dna,
            )

            return {
                "birds": birds,
                "brief": brief,
                "critique": critique,
                "verification": verification,
                "output": str(OUTPUT),
                "generation": {
                    "eligible_birds": eligible_birds,
                    "featured_birds": birds,
                    "curation_reason": curation_reason,
                    "movement_options": movements,
                    "selected_movement": selected_movement,
                    "selection_reason": selection_reason,
                    "bird_plan": bird_plan,
                    "image_prompt": prompt,
                    "verification": verification,
                    "accepted_with_minor_issues": verification.get("passed") is not True,
                    "attempts_used": attempt,
                    "critique": critique,
                    "creative_dna": creative_dna,
                    "api_profile": generation_ai.model_profile(),
                    "api_usage": generation_ai.usage_snapshot(),
                },
            }

        correction = build_verification_correction(verification)

        print()
        print(
            "⚠ Major featured-species problem detected. "
            "A corrective generation is justified."
        )
        print()
        print("Correction instructions for retry:")
        print(correction)

    print("⚠ Maximum attempts reached. Publishing latest artwork.")
    print(f"✓ Artwork prepared at {OUTPUT}")

    return {
        "birds": birds,
        "brief": brief,
        "critique": critique,
        "verification": verification,
        "output": str(OUTPUT),
        "generation": {
            "eligible_birds": eligible_birds,
            "featured_birds": birds,
            "curation_reason": curation_reason,
            "movement_options": movements,
            "selected_movement": selected_movement,
            "selection_reason": selection_reason,
            "bird_plan": bird_plan,
            "image_prompt": prompt,
            "verification": verification,
            "verification_failed": True,
            "attempts_used": MAX_ATTEMPTS,
            "critique": critique,
            "creative_dna": creative_dna,
            "api_profile": generation_ai.model_profile(),
            "api_usage": generation_ai.usage_snapshot(),
        },
    }


if __name__ == "__main__":
    from artwork_store import publish_artwork
    result = compose()
    if result:
        publish_artwork(
            source_image=Path(result["output"]),
            observation_date=date.today().isoformat(),
            birds=result["birds"],
            brief=result["brief"],
            generation=result.get("generation"),
        )
