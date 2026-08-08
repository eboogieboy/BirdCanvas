import base64
import json
import os
from datetime import date
from pathlib import Path

from openai import OpenAI

from storage import get_birds, get_yesterday_birds
from artwork_store import publish_artwork
from paths import OUTPUT_DIR, DATA_DIR
OUTPUT = OUTPUT_DIR / "final_scene.png"
CANDIDATE_DIR = OUTPUT_DIR / "candidates"
MAX_ATTEMPTS = 2
IMAGE_SIZE = "1024x1536"

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)


def load_birds_for_source(source):
    if source == "yesterday":
        return get_yesterday_birds()

    return get_birds()


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
    response = client.responses.create(
        model="gpt-5.5",
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


def save_creative_history(movement, brief, critique):

    HISTORY_FILE.parent.mkdir(exist_ok=True)
    history = load_creative_history(limit=100)

    dna = extract_creative_dna(brief)

    history.append({
        "date": str(date.today()),
        "movement": movement.get("name",""),
        "materials": brief.get("materials",""),
        "palette": brief.get("palette",""),
        "composition": brief.get("composition",""),
        "originality": critique.get("originality",0),
        "creative_dna": dna
    })

    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def create_movement_options(birds, season, edition="daily"):
    bird_list = "\n".join(f"- {b}" for b in birds)

    history = load_creative_history()

    response = client.responses.create(
        model="gpt-5.5",
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
    response = client.responses.create(
        model="gpt-5.5",
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


def create_creative_brief(birds, movement=None, edition="daily", observation_window=""):

    bird_list = "\n".join(f"- {bird}" for bird in birds)
    season = current_season()

    response = client.responses.create(
        model="gpt-5.5",
        input=f"""
You are the Creative Director for BirdCanvas.

BirdCanvas creates changing portrait-format contemporary artworks for a Samsung Frame television mounted in portrait orientation, inspired by birds observed during a defined time window.

Edition: {edition}
Observation window: {observation_window or "current bird list"}

BirdCanvas values:
- beauty over realism
- calm over drama
- simplicity over clutter
- originality over obviousness
- premium contemporary home aesthetics
- recognisable birds, but not wildlife-calendar art

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

Allow the season to influence:
- colour palette
- lighting
- textures
- atmosphere
- materials
- compositional feeling

Do not make the season obvious.
Avoid clichés.
Subtle seasonal influence is preferred over literal seasonal imagery.

BirdCanvas celebrates delight rather than frequency.

Unless there is a compelling artistic reason, common urban or plain species such as gulls, pigeons, crows, rooks, jackdaws and similar birds should normally be supporting.

Reserve hero status for birds that people typically find beautiful, colourful, delicate, charming or memorable.

If the bird list is mostly common urban birds, do not hide them all. Celebrate the character of that day honestly.

Birds observed:
{bird_list}

Selected exhibition movement (chosen by the Art Director):

Name: {movement.get("name","") if movement else ""}

Creative direction: {movement.get("creative_direction","") if movement else ""}

Materials: {movement.get("materials","") if movement else ""}

Composition: {movement.get("composition","") if movement else ""}

Develop THIS movement further.

Do not invent a different movement.

Create a curator's brief for today's exhibition.

The artwork must be conceived as an artwork first.

The birds are integrated into that artwork.

The birds are the primary subject of the artwork.

They must remain clearly recognisable as birds, even when highly stylised.

At least one bird should be immediately identifiable at normal viewing distance.

The selected movement influences HOW the birds are portrayed, not WHETHER they are visible.

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
  "bird_integration": "",
"materials": "",
"visual_focus": "",
  "avoid": []
}}

Rules:
- Every bird must be represented in the final artwork.
- Describe how the birds should be integrated into the artistic language using the bird_integration field.
- Suggest materials using the materials field.
- Describe what should attract the viewer first using the visual_focus field.
- The brief should encourage a distinctive artwork, not a predictable bird illustration.
- Invent an original exhibition style.
- Include style, style_guidance and curator_notes in the JSON.
- The style should feel suitable for a premium gallery.
- Do not imitate a living artist.
- visual_focus must describe the artwork itself (light, material, texture, geometry or composition), never a bird.
"""
    )

    try:
        text = clean_json_text(response.output_text)
        return json.loads(text)

    except Exception as error:
        print(f"Creative brief failed, using fallback: {error}")

        return {
            "collection": "Quiet Northern Forms",
            "style": "Contemporary botanical gallery print",
            "style_guidance": "Elegant contemporary wall art with restrained composition.",
            "curator_notes": "Fallback creative direction.",
            "mood": "calm",
            "visual_language": "minimal contemporary portrait-format wall art with restrained abstract forms",
            "palette": "warm neutrals, sea glass, soft greens, charcoal, sandstone and linen",
            "composition": "9:16 portrait composition with strong vertical balance and generous negative space",
            "bird_integration": "Integrate every bird naturally into the artwork so they are discovered rather than presented.",
"materials": "Layered paper, limewashed wood, mineral pigments and subtle textured surfaces.",
"visual_focus": "The composition and materials should attract attention before the birds are noticed.",
            "avoid": [
                "wildlife calendar art",
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

Today's birds are the subject of the artwork.

The selected exhibition movement determines the artistic language, materials and composition.

The birds must remain recognisable and important within that artistic language.

The viewer should first see a beautiful contemporary artwork.

The birds should be immediately noticeable as the subject of the piece.

The artistic movement should enhance the birds, not hide them.

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
    response = client.responses.create(
        model="gpt-5.5",
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
    """
    Build a species-by-species visual accuracy plan before image generation.

    The text model is much better than the image model at reasoning about
    diagnostic field marks. We therefore decide what each bird MUST look like
    before asking the image model to render the artwork.
    """

    exact_count = len(birds)

    numbered_birds = "\n".join(
        f"{index}. {bird}"
        for index, bird in enumerate(birds, start=1)
    )

    response = client.responses.create(
        model="gpt-5.5",
        input=f"""
You are the BirdCanvas Ornithology Director.

Create a strict visual identification plan for the bird species below.

These birds are being rendered in contemporary artwork, but each species
must remain visually identifiable.

The artwork is viewed in Britain, so use normal British/European field
identification characteristics where relevant.

Bird list:

{numbered_birds}

Return ONLY valid JSON in exactly this structure:

{{
  "birds": [
    {{
      "index": 1,
      "species": "",
      "position": "",
      "required_features": [
        "",
        "",
        ""
      ],
      "avoid_confusions": [
        ""
      ]
    }}
  ]
}}

STRICT RULES:

- Return exactly {exact_count} bird entries.
- Preserve the exact species names and exact order supplied above.
- Do not add or remove species.
- Give each bird a different visible position within a portrait composition.
- Keep all positions inside the central 80% of the canvas width.
- Do not overlap birds.
- Each bird must have 3 to 5 concise REQUIRED VISIBLE FEATURES.
- Choose features that are genuinely useful for identifying that species:
  body shape, bill shape, head pattern, wing markings, breast colour,
  rump colour, tail shape or other diagnostic field marks.
- Prefer features that remain visible in stylised artwork.
- Do not rely on tiny details that cannot be seen across a room.
- Avoid unnecessarily sex-specific or age-specific plumage.
- If males and females differ significantly, favour the most recognisable
  conventional adult appearance unless that would be misleading.
- avoid_confusions should name visual mistakes that could make the bird look
  like another likely species.
- Keep the wording visual and concise.
- This is an ornithological specification, not an artistic description.
"""
    )

    try:
        result = json.loads(
            clean_json_text(response.output_text)
        )

        planned = result.get("birds", [])

        if len(planned) != exact_count:
            raise ValueError(
                "Bird plan returned the wrong number of species."
            )

        cleaned = []

        for index, expected_species in enumerate(
            birds,
            start=1,
        ):
            item = planned[index - 1]

            actual_species = str(
                item.get("species", "")
            ).strip()

            if actual_species != expected_species:
                raise ValueError(
                    "Bird plan changed species order: "
                    f"expected {expected_species!r}, "
                    f"received {actual_species!r}"
                )

            features = [
                str(value).strip()
                for value in item.get(
                    "required_features",
                    [],
                )
                if str(value).strip()
            ]

            confusions = [
                str(value).strip()
                for value in item.get(
                    "avoid_confusions",
                    [],
                )
                if str(value).strip()
            ]

            if len(features) < 2:
                raise ValueError(
                    f"Too few identifying features for "
                    f"{expected_species}."
                )

            position = str(
                item.get("position", "")
            ).strip()

            if not position:
                position = _fallback_bird_position(
                    index,
                    exact_count,
                )

            cleaned.append(
                {
                    "index": index,
                    "species": expected_species,
                    "position": position,
                    "required_features": features[:5],
                    "avoid_confusions": confusions[:3],
                }
            )

        return cleaned

    except Exception as error:
        print(
            "Bird accuracy planning failed; "
            f"using safe fallback plan: {error}"
        )

        return [
            {
                "index": index,
                "species": species,
                "position": _fallback_bird_position(
                    index,
                    exact_count,
                ),
                "required_features": [
                    "correct species-specific body shape and proportions",
                    "correct species-specific plumage colours",
                    "clearly visible diagnostic field markings",
                ],
                "avoid_confusions": [
                    "do not substitute or visually merge with another species"
                ],
            }
            for index, species in enumerate(
                birds,
                start=1,
            )
        ]


def format_bird_plan_for_prompt(bird_plan):
    sections = []

    for bird in bird_plan:
        features = "; ".join(
            bird["required_features"]
        )

        confusions = "; ".join(
            bird.get("avoid_confusions", [])
        )

        section = (
            f'BIRD {bird["index"]}: '
            f'{bird["species"]}\n'
            f'RESERVED POSITION: {bird["position"]}\n'
            f'REQUIRED VISIBLE FEATURES: {features}'
        )

        if confusions:
            section += (
                "\nAVOID THESE IDENTIFICATION ERRORS: "
                f"{confusions}"
            )

        sections.append(section)

    return "\n\n".join(sections)


def create_image_prompt(
    birds,
    brief,
    bird_plan,
    correction=None,
):
    exact_bird_count = len(birds)

    plan_text = format_bird_plan_for_prompt(
        bird_plan
    )

    correction_text = ""

    if correction:
        correction_text = f"""

THIS IS A CORRECTIVE RETRY.

The previous generated artwork failed verification for these reasons:

{correction}

Correct every failure above.

Do not compensate for a missing or incorrect species by adding another copy
of a bird that was already correct.

Every species in the Bird Accuracy Plan below remains mandatory.
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=f"""
You are the Image Prompt Writer for BirdCanvas.

Write the artistic portion of ONE image-generation prompt.

The final image will be generated by gpt-image-1.

The artwork is premium contemporary gallery art for a vertically mounted
32-inch Samsung Frame.

The source canvas is 1024 × 1536 portrait and is subsequently centre-cropped
to exactly 1080 × 1920.

The artistic composition must therefore:

- be portrait
- be full bleed
- have no border, mount or mat
- keep every bird safely within the central 80% of the width
- leave the extreme side edges for background/material only
- remain visually successful after the 9:16 crop

There are exactly {exact_bird_count} individual birds.

Creative brief:

{json.dumps(brief, indent=2)}

Bird Accuracy Plan:

{plan_text}

{correction_text}

IMPORTANT:

Do NOT rewrite, reinterpret or simplify the Bird Accuracy Plan.

Do NOT change the species.

Do NOT exchange identifying features between birds.

Do NOT invent extra birds.

Your job is to describe HOW the specified birds and artistic movement form
one beautiful contemporary artwork.

Keep the artistic prompt concise and visually precise.

Do not explain your work.
"""
    )

    try:
        artistic_prompt = (
            response.output_text.strip()
        )
    except Exception:
        artistic_prompt = (
            brief.get(
                "style_guidance",
                "Create premium contemporary gallery art.",
            )
        )

    # The ornithology block below is assembled directly by Python rather than
    # rewritten by another model. This prevents species names or identifying
    # features being lost during prompt composition.
    final_prompt = f"""
{artistic_prompt}

NON-NEGOTIABLE BIRD ACCURACY PLAN

The finished image contains EXACTLY {exact_bird_count} birds in total.

{plan_text}

BIRD EXECUTION RULES

- Every numbered bird above must appear exactly once.
- No other birds may appear.
- Every bird gets its own reserved position.
- Birds must remain physically separate and fully visible.
- Do not overlap, merge, obscure or crop any bird.
- The identifying features listed for one species belong ONLY to that bird.
- Never transfer colours, markings, bill shape, head pattern or wing pattern
  from one species to another.
- Preserve realistic bird anatomy and proportions.
- Artistic stylisation applies to material, texture and rendering language;
  it must not erase diagnostic species features.
- When artistic composition conflicts with species accuracy, species accuracy
  wins.
- Before rendering, internally account for birds 1 through
  {exact_bird_count}, one by one.
- Final bird count: exactly {exact_bird_count}.

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
- Keep all birds and important features within the central 80% of the width.
- Allow only background/material/texture to occupy the extreme side edges.
- Artwork must be full bleed.
- No border, mount, mat, blank margin or landscape layout.

MANDATORY BIRD ACCURACY CHECKLIST:

- Show exactly the number of birds specified in the prompt.
- Include every listed bird species exactly once.
- Do not omit, duplicate or invent any bird.
- Place each bird in a separate, clearly readable position.
- Keep every bird fully visible; do not crop, merge, overlap or conceal them.
- Preserve correct anatomy, proportions, posture and identifying plumage.
- Each species must be recognisable from its distinctive field markings.
- Artistic materials and stylisation may affect the surrounding artwork, but
  must not obscure or distort the birds.
- Do not replace birds with silhouettes, symbols, fragments or vague motifs.
- Make all birds large enough to identify when viewed across a room.

Before rendering, internally count the birds and confirm that every listed
species appears once and only once.
"""

    result = client.images.generate(
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

    response = client.responses.create(
        model="gpt-5.5",
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

    plan_text = json.dumps(
        {
            "birds": bird_plan,
        },
        indent=2,
    )

    response = client.responses.create(
        model="gpt-5.5",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"""
You are the BirdCanvas Ornithology Verifier.

Inspect the generated artwork carefully.

Expected Bird Accuracy Plan:

{plan_text}

There must be exactly {len(expected_birds)} birds.

Evaluate EACH expected species independently.

Return ONLY valid JSON in exactly this structure:

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

SEVERITY RULES:

Use "major" only when:
- an expected species is missing
- an obvious extra bird is present
- one expected species has clearly been substituted by another
- a bird is so wrong that it clearly resembles a different species
- the total bird list has materially failed

Use "minor" when:
- the species is still reasonably identifiable
- a plumage shade is slightly wrong
- a leg, bill or small marking colour is imperfect
- a fine wing, neck or tail marking is missing or unclear
- the bird position differs from the plan
- stylisation has softened a diagnostic feature without changing the species

Use "none" for a correct bird.

VERIFICATION RULES:

- Include one bird_results entry for EVERY expected species.
- Preserve the supplied species order.
- Compare each bird against its required visible features.
- Mark "correct" when the bird is reasonably identifiable.
- Mark "missing" if that expected species is absent.
- Mark "incorrect" when a bird occupies its place but has materially wrong
  identifying features or clearly resembles another species.
- Mark "uncertain" only when there genuinely is not enough visual evidence.
- Do not fail because artistic rendering is stylised.
- Do not demand photographic realism.
- Do fail when diagnostic plumage, shape or markings make the bird the wrong
  species.
- Report duplicate/substitute birds when one expected species appears to have
  been replaced by another expected species.
- extra_birds should contain only clearly additional real birds, not decorative
  motifs or abstract marks.
- issues should contain concise actionable corrections.
- passed may be true ONLY if every expected bird is correct and there are no
  obvious extra birds.
- Be conservative about severity. BirdCanvas is artwork, not a field-guide
  plate. A recognisable species with a small detail wrong is MINOR, not MAJOR.
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

    result = json.loads(
        clean_json_text(response.output_text)
    )

    bird_results = result.get(
        "bird_results",
        [],
    )

    # Do not trust a malformed "passed": true response.
    if len(bird_results) != len(expected_birds):
        result["passed"] = False
        result.setdefault(
            "issues",
            [],
        ).append(
            "Verifier did not return one result "
            "for every expected species."
        )
        return result

    for expected, bird_result in zip(
        expected_birds,
        bird_results,
    ):
        if (
            str(
                bird_result.get(
                    "species",
                    "",
                )
            ).strip()
            != expected
        ):
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
    """
    Build a focused retry instruction.

    A paid second generation should concentrate ONLY on major bird-list
    failures. Minor field-mark imperfections are deliberately ignored.
    """

    corrections = []
    preserve = []

    for result in verification.get(
        "bird_results",
        [],
    ):
        species = str(
            result.get("species", "")
        ).strip()

        status = str(
            result.get("status", "")
        ).strip().lower()

        severity = str(
            result.get("severity", "minor")
        ).strip().lower()

        problems = [
            str(problem).strip()
            for problem in result.get(
                "problems",
                [],
            )
            if str(problem).strip()
        ]

        if status == "correct" and severity != "major":
            if species:
                preserve.append(species)
            continue

        if status == "missing" or severity == "major":
            detail = (
                "; ".join(problems)
                if problems
                else "major species error"
            )

            corrections.append(
                f"{species}: {status}. {detail}"
            )

    for extra in verification.get(
        "extra_birds",
        [],
    ):
        extra_text = str(extra).strip()

        if extra_text:
            corrections.append(
                f"Remove this extra bird: {extra_text}"
            )

    if preserve:
        corrections.append(
            "PRESERVE these already acceptable species and do not "
            "replace, duplicate or redesign them: "
            + ", ".join(preserve)
            + "."
        )

    if not corrections:
        corrections.append(
            "Re-check the bird list and correct only major "
            "missing, substituted or extra birds."
        )

    corrections.append(
        "Do not spend the retry improving minor plumage details. "
        "The priority is the exact species list and exact bird count."
    )

    return "\n".join(
        f"- {item}"
        for item in corrections
    )



def compose(source="today", birds=None, edition="daily", observation_window=""):

    print("compose() started")
    print("Loading birds...")
    birds = list(birds) if birds is not None else load_birds_for_source(source)
    print(f"Loaded {len(birds)} birds")

    if not birds:
        print(f"No birds recorded in {source}.")
        return None

    print("Creating movement options...")
    movements = create_movement_options(birds, current_season(), edition)
    print(f"Created {len(movements)} movement options")

    print("Movement options:")
    for i, m in enumerate(movements, 1):
        print(f"{i}. {m.get('name','Untitled')}")

    # print()
    # selected_movement, selection_reason = select_movement(movements, birds)

    # print(f"Selected movement: {selected_movement.get('name','Untitled')}")
    # print(f"Reason: {selection_reason}")
    # print()


    selected_movement, selection_reason = select_movement(movements, birds)
    brief = create_creative_brief(
    birds,
    movement=selected_movement,
    edition=edition,
    observation_window=observation_window
)

    print(f"BirdCanvas source: {source}")
    print(f"Image size: {IMAGE_SIZE}")
    print("Creative brief:")
    print(json.dumps(brief, indent=2))
    print()

    print("Creating Bird Accuracy Plan...")
    bird_plan = create_bird_plan(birds)

    print("Bird Accuracy Plan:")
    print(
        json.dumps(
            {"birds": bird_plan},
            indent=2,
        )
    )
    print()

    correction = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"Generating artwork attempt {attempt}/{MAX_ATTEMPTS}...")

        prompt = create_image_prompt(
            birds=birds,
            brief=brief,
            bird_plan=bird_plan,
            correction=correction,
        )

        print("Final image prompt:")
        print(prompt)
        print()

        image_bytes = generate_image(prompt)
        save_image(image_bytes)

        print("Verifying artwork...")

        try:
            verification = verify_image(
                birds,
                bird_plan,
            )
        except Exception as error:
            print(f"Verification failed, keeping generated artwork: {error}")
            return {"birds": birds, "brief": brief, "output": str(OUTPUT)}

        print("Verification results:")
        print(
            json.dumps(
                verification,
                indent=2,
            )
        )

        major_failure = verification_has_major_failure(
            verification
        )

        if not major_failure:
            if verification.get("passed") is True:
                print("✓ Bird verification passed.")
            else:
                print(
                    "✓ Only minor bird inaccuracies detected. "
                    "Accepting artwork without another paid generation."
                )

            critique = critique_artwork(
                birds,
                brief,
                OUTPUT,
            )

            print()
            print("Art Director critique")
            print("---------------------")
            for key, value in critique.items():
                print(f"{key}: {value}")

            save_creative_history(
                selected_movement,
                brief,
                critique,
            )

            publish_artwork(
                source_image=OUTPUT,
                observation_date=str(date.today()),
                birds=birds,
                brief=brief,
                edition=edition,
                generation={
                    "movement_options": movements,
                    "selected_movement": selected_movement,
                    "selection_reason": selection_reason,
                    "bird_plan": bird_plan,
                    "image_prompt": prompt,
                    "verification": verification,
                    "accepted_with_minor_issues": (
                        verification.get("passed") is not True
                    ),
                    "attempts_used": attempt,
                    "critique": critique,
                },
            )

            return {
                "birds": birds,
                "brief": brief,
                "critique": critique,
                "verification": verification,
                "output": str(OUTPUT),
            }

        correction = build_verification_correction(
            verification
        )

        print()
        print(
            "⚠ Major bird-list problem detected. "
            "A corrective generation is justified."
        )

        print()
        print("Correction instructions for retry:")
        print(correction)

    print("⚠ Maximum attempts reached. Publishing latest artwork.")

    publish_artwork(
        source_image=OUTPUT,
        observation_date=str(date.today()),
        birds=birds,
        brief=brief,
        edition=edition,
        generation={
            "movement_options": movements,
            "selected_movement": selected_movement,
            "selection_reason": selection_reason,
            
            "bird_plan": bird_plan,
            "image_prompt": prompt,
            "verification": verification,
            "verification_failed": True,
            "attempts_used": MAX_ATTEMPTS,
        },
    )

    print(f"✓ Artwork published to {OUTPUT}")

    return {
        "birds": birds,
        "brief": brief,
        "output": str(OUTPUT)
    }


if __name__ == "__main__":
    compose()