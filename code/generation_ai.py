"""Cost-optimised OpenAI pipeline for BirdCanvas artwork generation.

The production path intentionally uses one strong creative-director call and
cheap utility calls for selection/review. Species recognition cues are cached
locally so known birds do not need to be re-described on every artwork.
"""
from __future__ import annotations

import base64
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from paths import DATA_DIR

CREATIVE_MODEL = os.getenv("BIRDCANVAS_CREATIVE_MODEL", "gpt-5.6-sol")
UTILITY_MODEL = os.getenv("BIRDCANVAS_UTILITY_MODEL", "gpt-5.6-luna")
IMAGE_MODEL = os.getenv("BIRDCANVAS_IMAGE_MODEL", "gpt-image-2")
CREATIVE_REASONING = os.getenv("BIRDCANVAS_CREATIVE_REASONING", "low")
UTILITY_REASONING = os.getenv("BIRDCANVAS_UTILITY_REASONING", "none")
BIRD_GUIDE_CACHE = DATA_DIR / "bird_recognition_cache.json"

_USAGE_LOG: list[dict[str, Any]] = []


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI

    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _clean_json_text(text: str) -> str:
    text = str(text or "").strip()
    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def _usage_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump()
            if isinstance(dumped, dict):
                return dumped
        except Exception:
            pass
    try:
        return json.loads(json.dumps(value, default=str))
    except Exception:
        return {"value": str(value)}


def _record_usage(label: str, model: str, response: Any) -> None:
    _USAGE_LOG.append(
        {
            "label": label,
            "model": model,
            "usage": _usage_dict(getattr(response, "usage", None)),
        }
    )


def reset_usage() -> None:
    _USAGE_LOG.clear()


def usage_snapshot() -> list[dict[str, Any]]:
    return json.loads(json.dumps(_USAGE_LOG))


def model_profile() -> dict[str, str]:
    return {
        "creative_model": CREATIVE_MODEL,
        "creative_reasoning": CREATIVE_REASONING,
        "utility_model": UTILITY_MODEL,
        "utility_reasoning": UTILITY_REASONING,
        "image_model": IMAGE_MODEL,
    }


def _responses_create(label: str, *, model: str, effort: str, input: Any) -> Any:
    response = _client().responses.create(
        model=model,
        reasoning={"effort": effort},
        input=input,
    )
    _record_usage(label, model, response)
    return response


def _recent_featured(history: list[dict[str, Any]]) -> list[str]:
    return [
        str(bird).strip()
        for item in history[-8:]
        for bird in item.get("featured_birds", [])
        if str(bird).strip()
    ]


def select_featured_birds(
    birds: list[str],
    *,
    history: list[dict[str, Any]] | None = None,
    minimum: int = 2,
    maximum: int = 4,
) -> tuple[list[str], str]:
    """Choose a compact set of birds using the cheap utility model."""
    available = list(dict.fromkeys(str(b).strip() for b in birds if str(b).strip()))
    if len(available) <= minimum:
        return available, "All eligible species are featured because the collection is already small."

    maximum = min(maximum, len(available))
    recent_featured = _recent_featured(history or [])
    response = _responses_create(
        "featured_bird_selection",
        model=UTILITY_MODEL,
        effort=UTILITY_REASONING,
        input=f"""
You are the BirdCanvas curator. Choose between {minimum} and {maximum} species
from the eligible list for one strong contemporary artwork.

Eligible species:
{json.dumps(available, indent=2)}

Recently featured species:
{json.dumps(recent_featured, indent=2)}

Priorities: composition, visual contrast, variety across recent artworks, and
occasional memorable visitors. Do not infer rarity or detection frequency.
Preserve exact supplied names and never invent a species.

Return ONLY JSON:
{{"birds":["exact species name"],"reason":"one concise reason"}}
""",
    )

    try:
        result = json.loads(_clean_json_text(response.output_text))
        selected = [str(b).strip() for b in result.get("birds", []) if str(b).strip()]
        if len(selected) != len(set(selected)):
            raise ValueError("duplicate selection")
        if not minimum <= len(selected) <= maximum:
            raise ValueError("wrong selection count")
        if any(b not in available for b in selected):
            raise ValueError("invented or renamed species")
        return selected, str(result.get("reason", "")).strip()
    except Exception as error:
        appearances: dict[str, int] = {}
        for bird in recent_featured:
            key = bird.casefold()
            appearances[key] = appearances.get(key, 0) + 1
        indexed = list(enumerate(available))
        indexed.sort(key=lambda item: (appearances.get(item[1].casefold(), 0), item[0]))
        selected = [bird for _, bird in indexed[: min(3, len(indexed))]]
        return selected, f"Fallback curation after selector error: {error}"


def _load_bird_guide_cache(path: Path = BIRD_GUIDE_CACHE) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "birds": {}}
    if not isinstance(value, dict) or not isinstance(value.get("birds"), dict):
        return {"version": 1, "birds": {}}
    return value


def _save_bird_guide_cache(value: dict[str, Any], path: Path = BIRD_GUIDE_CACHE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _normalise_bird_guide_entry(species: str, item: dict[str, Any]) -> dict[str, Any]:
    art_cue = str(item.get("art_cue", "")).strip()
    cues = [str(v).strip() for v in item.get("recognition_cues", []) if str(v).strip()]
    confusions = [str(v).strip() for v in item.get("avoid_confusions", []) if str(v).strip()]
    if not art_cue or not cues:
        raise ValueError(f"Incomplete recognition guide for {species}")
    return {
        "species": species,
        "art_cue": art_cue,
        "recognition_cues": cues[:3],
        "avoid_confusions": confusions[:2],
    }


def create_bird_plan(birds: list[str], *, cache_path: Path = BIRD_GUIDE_CACHE) -> list[dict[str, Any]]:
    """Return recognition cues, calling the API only for species not in cache."""
    cache = _load_bird_guide_cache(cache_path)
    cached_birds = cache["birds"]
    missing = [bird for bird in birds if bird.casefold() not in cached_birds]

    if missing:
        numbered = "\n".join(f"{i}. {bird}" for i, bird in enumerate(missing, 1))
        try:
            response = _responses_create(
                "new_species_recognition_guide",
                model=UTILITY_MODEL,
                effort=UTILITY_REASONING,
                input=f"""
You are the BirdCanvas ornithology adviser. Create a reusable visual-recognition
record for each British/European bird below. This record will be cached, so it
must not contain composition-specific instructions.

Species:
{numbered}

Return ONLY JSON:
{{
  "birds":[
    {{
      "species":"exact supplied name",
      "art_cue":"short 6-14 word identity hint for an artist",
      "recognition_cues":["broad cue","broad cue"],
      "avoid_confusions":["most important likely visual mix-up"]
    }}
  ]
}}

Rules:
- Return exactly one entry per supplied species, in order.
- Preserve exact names.
- art_cue should use only one or two broad signals such as silhouette,
  movement or signature colour.
- recognition_cues should use 2-3 broad field cues suitable for verification.
- Do not specify positions, scale, coordinates or composition.
""",
            )
            result = json.loads(_clean_json_text(response.output_text))
            returned = result.get("birds", [])
            if len(returned) != len(missing):
                raise ValueError("recognition guide returned wrong number of birds")
            for species, item in zip(missing, returned):
                if str(item.get("species", "")).strip() != species:
                    raise ValueError(f"recognition guide renamed {species}")
                cached_birds[species.casefold()] = _normalise_bird_guide_entry(species, item)
            _save_bird_guide_cache(cache, cache_path)
        except Exception as error:
            print(f"Bird recognition cache update failed; using fallback cues: {error}")

    plan: list[dict[str, Any]] = []
    for index, species in enumerate(birds, start=1):
        item = cached_birds.get(species.casefold())
        if isinstance(item, dict):
            try:
                entry = _normalise_bird_guide_entry(species, item)
            except Exception:
                entry = None
        else:
            entry = None
        if entry is None:
            entry = {
                "species": species,
                "art_cue": f"{species}: recognisable silhouette with one restrained signature cue",
                "recognition_cues": [
                    "recognisable species-specific silhouette",
                    "characteristic broad colour or marking pattern",
                ],
                "avoid_confusions": ["do not make it clearly resemble another species"],
            }
        plan.append({"index": index, **entry})
    return plan


def _compact_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact = []
    for item in history[-8:]:
        compact.append(
            {
                "date": item.get("date"),
                "movement": item.get("movement"),
                "materials": item.get("materials"),
                "palette": item.get("palette"),
                "composition": item.get("composition"),
                "featured_birds": item.get("featured_birds", []),
                "creative_dna": item.get("creative_dna", {}),
            }
        )
    return compact


def create_art_direction(
    birds: list[str],
    bird_plan: list[dict[str, Any]],
    *,
    history: list[dict[str, Any]],
    season: str,
    edition: str,
    observation_window: str,
    subject_balance: str,
) -> dict[str, Any]:
    """One strong call replaces movement, selection, brief, DNA and prompt calls."""
    art_cues = [
        {"species": item["species"], "art_cue": item["art_cue"]}
        for item in bird_plan
    ]
    response = _responses_create(
        "creative_direction_and_image_prompt",
        model=CREATIVE_MODEL,
        effort=CREATIVE_REASONING,
        input=f"""
You are the Creative Director and Image Prompt Writer for BirdCanvas.

BirdCanvas creates premium contemporary portrait artwork for a 32-inch Samsung
Frame mounted vertically. The final display is 1080x1920 (9:16), generated from
a 1024x1536 portrait source and centre-cropped. It is inspired by birds genuinely
heard in North Shields on the north-east coast of England.

Edition: {edition}
Observation window: {observation_window or "current collection"}
Season: {season}
Subject balance for THIS artwork: {subject_balance}
Selected species: {json.dumps(birds)}
Light identity cues: {json.dumps(art_cues, indent=2)}
Recent creative history: {json.dumps(_compact_history(history), indent=2)}

Do all creative planning in this ONE response:
1. Consider FIVE radically different exhibition movements. Keep each proposal concise.
2. Select the strongest one for today's birds and recent-history contrast.
3. Develop it into a curator's brief.
4. Extract concise Creative DNA for future anti-repetition memory.
5. Write the finished prompt that will be sent directly to GPT Image.

Creative principles:
- artwork first; birds are source material, not a checklist
- obey the supplied subject balance exactly:
  * bird-led: birds may lead but must inhabit a convincing wider world
  * shared: birds and environment/objects/architecture share importance
  * environment-led: setting, architecture, furniture, objects, landscape, material or light leads
  * subtle-wildlife: the complete scene/composition leads and birds are smaller discoveries
- in environment-led and subtle-wildlife modes, never enlarge or centre birds merely to make them obvious
- beautiful, calm, original, premium contemporary-home aesthetics
- one bird may be the hero; others can be quieter or discovered later
- every selected species should remain recognisable using only its light identity cue
- birds must inherit the chosen medium/material language rather than appear as
  conventional naturalistic birds pasted into an abstract scene
- buildings, furniture, architecture, landscape structure and other non-bird
  elements are welcome when artistically useful; birds need not be the main feature
- North Sea light, sandstone, sea-glass colour, weathered material and coastal
  atmosphere may influence the work subtly; avoid literal seaside clichés
- keep important forms safely inside the central 80% width for the 9:16 crop
- full bleed; no borders, mats, text, labels, signatures, watermarks or humans
- avoid wildlife-calendar art, field-guide plates, greeting cards, stock illustration,
  children's illustration, AI clichés and overly busy scenes
- do not imitate a living artist
- do not add obvious unlisted real bird species

Return ONLY valid JSON in exactly this structure:
{{
  "movement_options":[
    {{"name":"","creative_direction":"","materials":"","composition":"","why_it_is_distinct":""}}
  ],
  "selected_index":1,
  "selection_reason":"",
  "brief":{{
    "collection":"",
    "style":"",
    "style_guidance":"",
    "curator_notes":"",
    "mood":"",
    "visual_language":"",
    "palette":"",
    "composition":"",
    "subject_balance":"",
    "bird_integration":"",
    "materials":"",
    "visual_focus":"",
    "hero_birds":[],
    "supporting_birds":[],
    "avoid":[]
  }},
  "creative_dna":{{
    "dominant_family":"",
    "materials":[],
    "palette_type":"",
    "energy":"",
    "complexity":"",
    "surface":"",
    "geometry":"",
    "overall_character":""
  }},
  "image_prompt":""
}}

The image_prompt must be complete and ready for image generation. It must describe
one collectible contemporary artwork, include all selected species once in an
identifiable but transformed way, explicitly preserve crop safety/full bleed, and
prioritise composition, atmosphere, material, light and beauty over ornithological
micro-detail. Do not turn it into a checklist or repeat the whole brief verbatim.
""",
    )

    try:
        result = json.loads(_clean_json_text(response.output_text))
        movements = result.get("movement_options", [])
        if not isinstance(movements, list) or not movements:
            raise ValueError("no movement options")
        selected_index = max(1, min(len(movements), int(result.get("selected_index", 1))))
        brief = result.get("brief", {})
        image_prompt = str(result.get("image_prompt", "")).strip()
        if not isinstance(brief, dict) or not image_prompt:
            raise ValueError("incomplete creative direction")
        valid = set(birds)
        hero = [str(v).strip() for v in brief.get("hero_birds", []) if str(v).strip() in valid][:1]
        supporting = [
            str(v).strip()
            for v in brief.get("supporting_birds", [])
            if str(v).strip() in valid and str(v).strip() not in hero
        ]
        for bird in birds:
            if bird not in hero and bird not in supporting:
                supporting.append(bird)
        brief["subject_balance"] = subject_balance
        brief["hero_birds"] = hero
        brief["supporting_birds"] = supporting
        return {
            "movement_options": movements,
            "selected_movement": movements[selected_index - 1],
            "selection_reason": str(result.get("selection_reason", "")).strip(),
            "brief": brief,
            "creative_dna": result.get("creative_dna", {}),
            "image_prompt": image_prompt,
        }
    except Exception as error:
        print(f"Creative director response invalid; using safe local fallback: {error}")
        movement = {
            "name": "Quiet Northern Material Study",
            "creative_direction": "Contemporary material abstraction shaped by cool northern light.",
            "materials": "mineral pigment, layered paper and weathered surfaces",
            "composition": "open portrait composition with calm negative space",
            "why_it_is_distinct": "fallback",
        }
        brief = {
            "collection": "Quiet Northern Forms",
            "style": "Contemporary material abstraction",
            "style_guidance": "Create elegant contemporary wall art led by composition, material and atmosphere.",
            "curator_notes": "Birds are selected visual cues inside a broader artwork.",
            "mood": "calm",
            "visual_language": "layered material forms with restrained abstraction",
            "palette": "warm neutrals, sea glass, soft greens, charcoal and sandstone",
            "composition": "portrait composition with strong vertical balance and generous negative space",
            "subject_balance": subject_balance,
            "bird_integration": "Transform each bird into the material language while retaining a recognisable identity cue.",
            "materials": movement["materials"],
            "visual_focus": "material, light and spatial rhythm",
            "hero_birds": birds[:1],
            "supporting_birds": birds[1:],
            "avoid": ["wildlife calendar art", "field-guide plate", "clip art", "busy garden scene"],
        }
        cues = "; ".join(f"{x['species']}: {x['art_cue']}" for x in bird_plan)
        return {
            "movement_options": [movement],
            "selected_movement": movement,
            "selection_reason": "Safe fallback after creative-director parsing failure.",
            "brief": brief,
            "creative_dna": {
                "dominant_family": "material abstraction",
                "materials": ["mineral pigment", "paper"],
                "palette_type": "restrained coastal neutrals",
                "energy": "calm",
                "complexity": "low",
                "surface": "layered",
                "geometry": "open vertical",
                "overall_character": "quiet northern contemporary",
            },
            "image_prompt": (
                "Create a museum-quality contemporary material abstraction in portrait format, full bleed, "
                "using layered mineral pigment, paper and weathered surfaces under cool northern light. "
                f"Integrate these selected birds as transformed but recognisable motifs: {cues}. "
                "One may be prominent and the others subtle; do not use a field-guide layout. Buildings, "
                "architectural forms or objects may share the composition. Keep important forms in the central "
                "80% width for a final 9:16 crop. No text, border, mat, signature, watermark or humans."
            ),
        }


def build_retry_prompt(base_prompt: str, correction: str) -> str:
    return f"""{base_prompt}

CORRECTIVE RETRY
The previous rendering had a genuine species-level failure:
{correction}

Create Revision 2 of the same artwork. Preserve the successful movement,
materials, palette, atmosphere and composition as much as possible. Correct only
the missing/substituted/prominent-unlisted species issue. Do not spend the retry
improving minor field marks, positions or anatomy and do not redesign from scratch.
""".strip()


def generate_image(prompt: str, *, size: str = "1024x1536", quality: str = "medium") -> bytes:
    result = _client().images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=size,
        quality=quality,
    )
    _record_usage("image_generation", IMAGE_MODEL, result)
    return base64.b64decode(result.data[0].b64_json)


def _image_to_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def review_artwork(
    expected_birds: list[str],
    brief: dict[str, Any],
    image_path: Path,
    bird_plan: list[dict[str, Any]],
) -> dict[str, Any]:
    """One cheap vision call performs species verification and art critique."""
    image_url = _image_to_data_url(image_path)
    response = _responses_create(
        "verification_and_art_critique",
        model=UTILITY_MODEL,
        effort=UTILITY_REASONING,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"""
You are BirdCanvas's conservative ornithology verifier and art critic.
This is contemporary artwork, not a field-guide illustration.

Featured species guide:
{json.dumps({"birds": bird_plan}, indent=2)}

Creative brief:
{json.dumps(brief, indent=2)}

Do TWO jobs in this one review.

A) Species verification. Evaluate every featured species independently. Major
means only: genuinely missing, clearly another species, or a prominent unlisted
real bird that changes the curated set. Minor means still reasonably identifiable
but stylised, small, partially embedded, obscured, or imperfect in a field mark.
Do not demand photographic realism, equal prominence, exact scale or full bodies.

B) Art critique. Score 1-10 for originality, adherence to the movement,
contemporary-art quality and bird integration. Bird integration should score low
if ordinary naturalistic birds look pasted into an otherwise abstract/material work.

Return ONLY JSON:
{{
  "verification":{{
    "passed":true,
    "bird_results":[
      {{"species":"","status":"correct","severity":"none","problems":[]}}
    ],
    "extra_birds":[],
    "issues":[]
  }},
  "critique":{{
    "originality":0,
    "movement":0,
    "art_quality":0,
    "bird_integration":0,
    "summary":""
  }}
}}

Allowed status: correct, missing, incorrect, uncertain.
Allowed severity: none, minor, major.
Preserve exact supplied species names and supplied order in bird_results.
""",
                    },
                    {"type": "input_image", "image_url": image_url},
                ],
            }
        ],
    )

    result = json.loads(_clean_json_text(response.output_text))
    verification = result.get("verification", {})
    critique = result.get("critique", {})
    bird_results = verification.get("bird_results", [])

    if len(bird_results) != len(expected_birds):
        verification["passed"] = False
        verification.setdefault("issues", []).append(
            "Verifier did not return one result for every featured species."
        )
    else:
        for expected, bird_result in zip(expected_birds, bird_results):
            if str(bird_result.get("species", "")).strip() != expected:
                verification["passed"] = False
            if str(bird_result.get("status", "")).strip().lower() != "correct":
                verification["passed"] = False
    if verification.get("extra_birds"):
        verification["passed"] = False

    return {"verification": verification, "critique": critique}
