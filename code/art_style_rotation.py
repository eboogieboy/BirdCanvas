"""Distinct visual traditions for BirdCanvas, with family-level contrast.

No additional AI calls are made for style selection. Historical artwork may
contain removed or unclassified styles; those records remain untouched.
"""
from __future__ import annotations

STYLE_FAMILIES = {
    "atmospheric": [
        ("Oil painting", "Expressive oil paint, energetic brushwork and luminous pigment; avoid photographic illustration."),
        ("Impressionism", "Visible broken-colour brushwork, natural light and varied impressionist marks."),
        ("Watercolour", "Transparent layered washes, fluid edges and expressive pigment blooms."),
        ("Pastel", "Dry chalk marks, luminous blended pigment and rich textured colour."),
        ("Japanese woodblock", "Ukiyo-e-inspired block colours, elegant linework and deliberate flatness."),
        ("Atmospheric mixed media", "Tactile layered pigments and material textures, without reverting to a generic grey coastal scene."),
    ],
    "modern_graphic": [
        ("Pop art", "Unmistakable Pop art: saturated screenprint colour, strong graphic contours, flat shapes and playful contrast."),
        ("Art Deco", "Clear Art Deco geometry, architectural rhythm, ornament and confident stylised colour."),
        ("Graphic novel", "Cinematic ink and graphic storytelling, expressive flat colour and bold frame composition."),
        ("Mid-century modern", "Mid-century editorial illustration with striking modernist shapes and vintage-print colour."),
        ("Linocut", "Hand-carved high-contrast relief marks, strong silhouettes and bold blocks of ink."),
        ("Stained glass", "Radiant translucent jewel-coloured panes and expressive geometric lead-line structure."),
        ("Constructivist modernism", "Modernist poster-like diagonal forms, strong geometry and radical colour blocking; no typography."),
    ],
    "abstract_experimental": [
        ("Abstract expressionism", "Dominant gestural marks, tactile paint, energetic expressive colour and a clearly abstract composition."),
        ("Geometric abstraction", "Large non-representational colour planes, crisp geometry, controlled tension and rhythmic shapes."),
        ("Cubism", "Fragmented cubist planes, multiple viewpoints and dramatic spatial reconstruction."),
        ("Paper collage", "Torn and cut paper, overlapping abstract forms, intentional negative space and tactile layers."),
        ("Minimalism", "Bold reduced forms, precise relationships and meaningful negative space; a genuine minimalist object."),
        ("Surrealism", "A coherent yet impossible visual world with dreamlike spatial relationships and poetic contradictions."),
        ("Folk art", "Joyful flattened symbolic motifs and handmade decorative geometry."),
    ],
}
# Kept for existing callers and tests.
STYLES = [style for group in STYLE_FAMILIES.values() for style in group]
STYLE_LOOKUP = {
    name: {"name": name, "guidance": guidance, "family": family}
    for family, styles in STYLE_FAMILIES.items()
    for name, guidance in styles
}
TARGET_WEIGHTS = {"atmospheric": 0.33, "modern_graphic": 0.37, "abstract_experimental": 0.30}


def get_style(name: str):
    """Return a validated explicit style, rejecting unsupported/retired names."""
    try:
        return dict(STYLE_LOOKUP[str(name).strip()])
    except KeyError as error:
        raise ValueError(f"Unsupported artistic style: {name}") from error


def choose_style(history, preferred_style=None):
    """Choose a contrasting family and avoid styles used in the previous five artworks.

    Priority is avoiding either of the two preceding families. With three
    families this gives a genuine painterly / graphic / abstract rotation.
    Historical counts break ties toward the desired longer-term family mix.
    An explicit style is only used for a user-requested manual style test.
    """
    if preferred_style and preferred_style != "surprise":
        return get_style(preferred_style)

    used = [
        str(item.get("art_style", "")).strip()
        for item in history
        if isinstance(item, dict) and item.get("art_style")
    ]
    families = [STYLE_LOOKUP[name]["family"] for name in used if name in STYLE_LOOKUP]
    recent_families = set(families[-2:])
    recent_styles = set(used[-5:])
    family_counts = {family: families.count(family) for family in STYLE_FAMILIES}
    length = len(families) + 1

    ranked = sorted(
        STYLE_FAMILIES,
        key=lambda family: (
            family in recent_families,
            family == "atmospheric" and families[-6:].count("atmospheric") >= 2,
            -(TARGET_WEIGHTS[family] * length - family_counts[family]),
            list(STYLE_FAMILIES).index(family),
        ),
    )
    for family in ranked:
        choices = [item for item in STYLE_FAMILIES[family] if item[0] not in recent_styles]
        if not choices:
            choices = STYLE_FAMILIES[family]
        # Pick the least-used specific medium for meaningful variety within a family.
        name, guidance = min(
            choices,
            key=lambda item: (used.count(item[0]), STYLE_FAMILIES[family].index(item)),
        )
        return {"name": name, "guidance": guidance, "family": family}
    raise RuntimeError("Artistic-style collection is empty.")
