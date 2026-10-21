"""Curated BirdCanvas styles across five genuinely different visual languages.

Style choice is local and free: no additional model calls. Old creative-history
records stay valid, including entries from retired or reclassified styles.
"""
from __future__ import annotations

STYLE_FAMILIES = {
    "modern_graphic": [
        ("Pop art", "Unmistakable pop art: punchy screenprinted colour, halftone texture, bold flat shapes and graphic outlines."),
        ("Art Deco", "Stylised 1920s–30s geometry, ornamental rhythm, elegant angular forms and confident colour; avoid a photoreal interior."),
        ("Mid-century modern", "Vintage modernist editorial design with inventive flat shapes, retro palette and graphic negative space."),
        ("Constructivist modernism", "Radical diagonals, asymmetric modernist blocks, strong poster-like geometry and assertive colour; no typography."),
        ("Bauhaus geometric design", "Functional Bauhaus visual composition: primary-colour planes, circles, bars, clean geometric rhythm and reduced forms."),
        ("Swiss graphic modernism", "Crisp international-style graphic composition, asymmetric grid, purposeful negative space and bright colour fields; no lettering."),
    ],
    "abstract_experimental": [
        ("Abstract expressionism", "Non-representational energy: sweeping gestural marks, layered pigment, bold contrast and expressive movement."),
        ("Geometric abstraction", "Large non-literal colour planes, sharp intersecting geometry and carefully balanced spatial tension."),
        ("Cubism", "Fragmented planes and multiple perspectives; bird motifs reconstructed as angular interlocking shapes."),
        ("Minimalism", "Extremely reduced, intentional forms, spare colour and generous negative space with subtle recognisable bird motifs."),
        ("Surrealism", "Poetic visual impossibility and surprising spatial relationships; coherent as an artwork rather than picturesque fantasy."),
        ("Colour-field abstraction", "Broad luminous colour fields and soft-edged boundaries with a few subtle bird silhouettes or forms."),
        ("Op art", "High-contrast optical geometry, repetition and rhythmic shifts, with recognisable bird forms woven into the pattern."),
    ],
    "illustration_print": [
        ("Japanese woodblock", "Ukiyo-e-inspired carved shapes, disciplined flat colour, precise ink contours and striking printmaking composition."),
        ("Folk art", "Distinctive handmade decorative motifs, flattened symbolic bird forms and joyful considered colour."),
        ("Graphic novel", "Cinematic ink illustration, graphic colour areas and powerful storytelling composition without comic panels or lettering."),
        ("Editorial illustration", "Sophisticated contemporary editorial illustration: stylised storytelling, inventive metaphor and graphic restraint, never childish."),
        ("Screenprint", "Layered silkscreen inks with slight registration shifts, bold cut-out silhouettes and limited high-impact palette."),
        ("Risograph", "Risograph print aesthetic: vibrant spot inks, grain, imperfect overprint and daring colour interaction."),
        ("Linocut", "Hand-carved high-contrast relief-print gouges, expressive negative space and tactile blocks of ink."),
    ],
    "material_sculptural": [
        ("Stained glass", "A complete designed stained-glass artwork: leaded geometry and luminous translucent colour, not a photographed window."),
        ("Paper collage", "Layered torn and cut paper, visible fibres, expressive shape overlaps and intentional negative space."),
        ("Cut-paper relief", "Dimensional stacked paper relief with crisp cut edges, subtle physical shadows and sculptural bird silhouettes."),
        ("Textile tapestry", "Contemporary woven tapestry: tactile threads, embroidered or woven bird motifs and large abstract textile fields."),
        ("Mosaic mural", "Modern mosaic artwork with visibly distinct tesserae, confident colour blocks and integrated bird motifs."),
        ("Ceramic mural", "Handmade ceramic-tile mural with glaze variation, geometric joints and stylised bird ornament integrated into the surface."),
    ],
    "atmospheric": [
        ("Oil painting", "Expressive oil painting, visible painterly strokes and confident pigment rather than photographic realism."),
        ("Impressionism", "Broken-colour impressionist brushwork with light-filled colour and unmistakable painted marks."),
        ("Watercolour", "Transparent washes, fluid pigment edges, expressive white space and unmistakable watercolour handling."),
        ("Pastel", "Dry chalk and layered soft pastel, lively colour blending and beautifully tactile strokes."),
        ("Atmospheric mixed media", "Sophisticated layered materials, original surface texture and surprising spatial storytelling; avoid stock moody coastal imagery."),
    ],
}

# Public compatibility for tests and callers which consume the existing flat list.
STYLES = [style for styles in STYLE_FAMILIES.values() for style in styles]
STYLE_LOOKUP = {
    name: {"name": name, "guidance": guidance, "family": family}
    for family, styles in STYLE_FAMILIES.items()
    for name, guidance in styles
}

BOLD_FAMILIES = (
    "modern_graphic",
    "abstract_experimental",
    "illustration_print",
    "material_sculptural",
)
# Eight bold daily editions, then one atmospheric change of pace (~11%).
BOLD_BEFORE_ATMOSPHERIC = 8


def get_style(name: str) -> dict[str, str]:
    """Resolve only active styles; never revive retired Storybook illustration."""
    try:
        return dict(STYLE_LOOKUP[str(name).strip()])
    except KeyError as error:
        raise ValueError(f"Unsupported artistic style: {name}") from error


def choose_style(history, preferred_style=None):
    """Choose contrasting families using recent *automatic* editions only.

    Never repeat a family seen in the previous three normal editions. Four
    bold families rotate while atmospheric work appears after eight consecutive
    non-atmospheric editions. The algorithm uses only a sliding window, so it
    does not break once creative history reaches its retention limit.
    """
    if preferred_style and preferred_style != "surprise":
        return get_style(preferred_style)

    normal = [
        (STYLE_LOOKUP[item["art_style"]]["family"], item["art_style"])
        for item in history
        if isinstance(item, dict)
        and item.get("art_style") in STYLE_LOOKUP
        and item.get("edition") != "style_test"
    ]
    families = [family for family, _ in normal]
    used = [name for _, name in normal]
    blocked = set(families[-3:])
    last_eight = families[-BOLD_BEFORE_ATMOSPHERIC:]

    atmospheric_due = (
        len(last_eight) == BOLD_BEFORE_ATMOSPHERIC
        and "atmospheric" not in last_eight
    )
    if atmospheric_due:
        family = "atmospheric"
    else:
        # With four bold families and a three-family cooldown, at least one
        # eligible family always remains. Prefer underrepresented categories.
        candidates = [f for f in BOLD_FAMILIES if f not in blocked]
        family = min(
            candidates,
            key=lambda f: (
                last_eight.count(f),
                BOLD_FAMILIES.index(f),
            ),
        )

    recent_styles = set(used[-5:])
    options = [entry for entry in STYLE_FAMILIES[family] if entry[0] not in recent_styles]
    if not options:
        options = STYLE_FAMILIES[family]
    name, guidance = min(
        options,
        key=lambda entry: (
            used.count(entry[0]),
            STYLE_FAMILIES[family].index(entry),
        ),
    )
    return {"name": name, "guidance": guidance, "family": family}
