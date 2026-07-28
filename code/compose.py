import base64
import json
import os
from datetime import date
from pathlib import Path

from openai import OpenAI

from storage import get_birds, get_yesterday_birds
from artwork_store import publish_artwork

OUTPUT = Path("output/final_scene.png")
CANDIDATE_DIR = Path("output/candidates")
MAX_ATTEMPTS = 1
IMAGE_SIZE = "1536x1024"

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

HISTORY_FILE = _Path("data/creative_history.json")


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

Generate TEN radically different exhibition movements for today's birds.

Imagine these are proposals from ten different world-class galleries competing to exhibit today's birds.

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

Across the ten movements, maximise diversity in:

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

Someone viewing the ten movement titles should immediately imagine ten completely different exhibitions.
Before returning your final list, critically review it.

If two movements feel similar, replace the weaker one.

Do not stop until all TEN movements feel like they belong in completely different exhibitions.

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
                "composition":"Open landscape.",
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

BirdCanvas creates changing landscape-format contemporary artworks for a Samsung Frame television, inspired by birds observed during a defined time window.

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
            "visual_language": "minimal contemporary landscape-format wall art with restrained abstract forms",
            "palette": "warm neutrals, sea glass, soft greens, charcoal, sandstone and linen",
            "composition": "16:9 landscape composition with full-width balance and generous negative space",
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

{correction}

Create a new artwork that corrects these issues while remaining artistically excellent.
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

Landscape format.

Designed for a Samsung Frame television.

Fill the entire 16:9 canvas.

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

The birds are simply one layer within the artwork.

The image should feel collectible.

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


def create_image_prompt(birds, brief):
    bird_list = ", ".join(birds)

    response = client.responses.create(
        model="gpt-5.5",
        input=f"""
You are the Image Prompt Writer for BirdCanvas.

Convert the curator's brief into a concise, highly effective prompt for gpt-image-1.

Today's birds:
{bird_list}

Creative brief:
{json.dumps(brief, indent=2)}

Write ONE image-generation prompt.

Do not explain.
Do not use headings.
Do not repeat the JSON.
Focus on visual execution.
"""
    )

    try:
        return response.output_text.strip()
    except Exception:
        return build_prompt(birds, brief)


def generate_image(prompt):
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=IMAGE_SIZE,
        quality="high"
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


def verify_image(expected_birds):
    expected_text = "\n".join(f"- {bird}" for bird in expected_birds)
    image_url = image_to_data_url(OUTPUT)

    response = client.responses.create(
        model="gpt-5.5",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"""
You are checking a generated BirdCanvas artwork.

Expected bird species:
{expected_text}

Return ONLY valid JSON:

{{
  "passed": true,
  "issues": []
}}

or

{{
  "passed": false,
  "issues": [
    "Specific issue here"
  ]
}}

Check for:
- birds are reasonably recognisable
- missing expected species
- obvious extra bird species not listed

Only flag duplication when:
- the same bird is clearly repeated as a replacement for a missing expected species
- the artwork has obviously failed the bird list

Do not fail because of:
- decorative repeated motifs
- similar background shapes
- abstract artistic elements
- minor ambiguity in small birds

Be practical. If a bird is stylised or abstract but reasonably identifiable, accept it.
"""
                    },
                    {
                        "type": "input_image",
                        "image_url": image_url
                    }
                ]
            }
        ]
    )

    text = clean_json_text(response.output_text)

    return json.loads(text)


def compose(source="today", birds=None, edition="daily", observation_window=""):
    birds = list(birds) if birds is not None else load_birds_for_source(source)

    if not birds:
        print(f"No birds recorded in {source}.")
        return None

    movements = create_movement_options(birds, current_season(), edition)

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

    correction = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"Generating artwork attempt {attempt}/{MAX_ATTEMPTS}...")

        curator_prompt = build_prompt(
            birds=birds,
            brief=brief,
            correction=correction,
            edition=edition,
            observation_window=observation_window
        )

        structured = compose_structured_image_prompt(birds, brief)

        print("Structured prompt:")
        print(json.dumps(structured, indent=2))
        print()

        prompt = create_image_prompt(
            birds,
            {
                **brief,
                "structured_prompt": structured
            }
        )

        print("Final image prompt:")
        print(prompt)
        print()

        image_bytes = generate_image(prompt)
        save_image(image_bytes)

        print("Verifying artwork...")

        try:
            verification = verify_image(birds)
        except Exception as error:
            print(f"Verification failed, keeping generated artwork: {error}")
            return {"birds": birds, "brief": brief, "output": str(OUTPUT)}

        if verification.get("passed") is True:
            critique = critique_artwork(birds, brief, OUTPUT)

            print()
            print("Art Director critique")
            print("---------------------")
            for key, value in critique.items():
                print(f"{key}: {value}")

            save_creative_history(selected_movement, brief, critique)

            publish_artwork(
                source_image=OUTPUT,
                observation_date=str(date.today()),
                birds=birds,
                brief=brief,
                edition=edition,
            )

            return {
                "birds": birds,
                "brief": brief,
                "critique": critique,
                "output": str(OUTPUT)
            }

        issues = verification.get("issues", [])
        correction = "\n".join(f"- {issue}" for issue in issues)

        print("Verification issues:")
        print(correction)

    print("⚠ Maximum attempts reached. Publishing latest artwork.")

    publish_artwork(
    source_image=OUTPUT,
    observation_date=str(date.today()),
    birds=birds,
    brief=brief,
    edition=edition,
    )

    print(f"✓ Artwork published to {OUTPUT}")

    return {
        "birds": birds,
        "brief": brief,
        "output": str(OUTPUT)
    }


if __name__ == "__main__":
    compose()