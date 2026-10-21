"""Rotating BirdCanvas gallery art across ten distinct artistic families.

The selector is entirely local; it adds no AI calls or generation cost.
Historical artwork and old style names remain untouched.
"""
from __future__ import annotations

STYLE_FAMILIES = {
    "modern_graphic": [
        ("Pop art", "Luminous saturated screenprint colour, bold comic-style contours, flat graphic shapes and striking contrast."),
        ("Constructivist modernism", "Asymmetric modernist diagonal blocks, dynamic geometry, strong colours and radical poster composition; no lettering."),
        ("Mid-century modern", "Confident retro modernist illustration, crisp flat shapes and wonderfully considered vintage graphic colour."),
        ("Bauhaus geometric design", "Primary-colour planes, circles, bars, functional Bauhaus geometry and lively negative space."),
        ("Swiss graphic modernism", "Crisp asymmetrical grid, precise graphic elements, colour-field design and purposeful spatial rhythm; no typography."),
    ],
    "abstract_experimental": [
        ("Abstract expressionism", "An energetic non-representational painting with expressive gestures, layered pigment, bold movement and subtle bird identity."),
        ("Geometric abstraction", "Non-literal intersecting geometric shapes, bold colour planes and balanced spatial tension."),
        ("Cubism", "Fragmented prismatic planes, shifting simultaneous perspectives and transformed bird shapes."),
        ("Minimalism", "Reduced sculptural geometry, exceptionally purposeful negative space and tiny recognisable bird accents."),
        ("Surrealism", "Intentional dream logic, impossible relationships and poetic visual surprises rather than literal fantasy postcard scenery."),
        ("Colour-field abstraction", "Broad luminous regions of colour, softly contrasting edges and minimal integrated bird forms."),
    ],
    "illustration_print": [
        ("Japanese woodblock", "Ukiyo-e-inspired woodblock shapes, hand-carved linework and exquisite flat printed colour."),
        ("Folk art", "Handmade decorative motifs, flattened stylised birds and lively considered folkloric colour."),
        ("Graphic novel", "Sophisticated graphic-novel inks, cinematic negative space and expressive illustrated shapes without comic panels."),
        ("Editorial illustration", "Sophisticated conceptual magazine illustration, playful metaphor and graphic visual clarity, never children's-book art."),
        ("Screenprint", "Silkscreen spot-colour layers, bold silhouettes, deliberate overprinting and tactile ink imperfections."),
        ("Risograph", "Distinctive two-to-four spot-ink riso printing, grain, colour overprint and misregistration."),
        ("Linocut", "Expressive carved gouges, black-and-colour relief ink, bold positive/negative forms and tactile print edges."),
    ],
    "material_sculptural": [
        ("Paper collage", "Torn and cut paper planes, visible handmade fibres, layered edges and sophisticated graphic juxtaposition."),
        ("Cut-paper relief", "Dimensional hand-cut stacked paper, real cast shadows, sculptural layering and elegantly formed bird silhouettes."),
        ("Ceramic mural", "Contemporary ceramic tile relief, individual glazed tiles, geometric joints and integrated stylised bird forms."),
        ("Mosaic mural", "Modern mosaic tesserae, visible individual pieces, confident blocks of ceramic/stone colour and rhythmic shapes."),
    ],
    "textile_fibre": [
        ("Textile tapestry", "Woven tapestry with conspicuous yarn texture, large graphic textile fields and birds worked into the weave."),
        ("Contemporary embroidery", "Fine and coarse expressive embroidery stitches, linen ground, stitched bird contours and abstract thread gestures."),
        ("Modern art quilt", "Contemporary pieced and appliqued textile composition with confident fabric blocks and tactile stitching."),
        ("Batik fabric artwork", "Wax-resist batik with characteristic crackled dyes, saturated cloth colour and integrated bird shapes."),
        ("Woven fibre abstraction", "Sculptural fibre-art relief with visible warp and weft, asymmetric weaving and textural bird suggestions."),
    ],
    "photographic_process": [
        ("Cyanotype", "Deep Prussian-blue photographic contact print with white bird silhouettes, organic exposure marks and tonal chemical variation."),
        ("Photogram", "Darkroom camera-less photogram: luminous object and bird-shaped impressions on dramatic tonal photographic paper."),
        ("Solarised darkroom print", "Experimental solarised photographic art with reversed contour tones, surprising tonal fields and graphic bird forms."),
        ("Lumen print", "Organic sun-exposed photographic paper, shifting pink/rust/ochre tones and ghostly bird and plant silhouettes."),
        ("Gum bichromate print", "Handmade multi-layer gum-bichromate photographic process with visible pigment grains, painterly registration and silhouettes."),
    ],
    "kinetic_optical": [
        ("Op art", "Mesmerising optical black-and-colour linework, geometric repetition and subtle bird silhouettes embedded in pattern."),
        ("Moiré optical print", "Overlapping high-contrast line grids that create moiré rhythm, with stylised bird-shaped negative spaces."),
        ("Kinetic sculpture study", "Museum-quality visual rendering of hanging moving abstract shapes, dynamic balance and delicate bird-inspired structures."),
        ("Optical stripe abstraction", "Confident stripe oscillations, warped colour bands and hypnotic rhythmic geometry incorporating discreet bird contours."),
    ],
    "digital_new_media": [
        ("Generative algorithmic art", "Collectible computational artwork with intricate procedural lines, point systems, colourful networks and bird-motif emergence."),
        ("Pixel mosaic art", "Sophisticated large-pixel digital mosaic, limited intentional palette, crisp square geometry and recognisable bird shapes; not video-game clip art."),
        ("Glitch collage", "Considered contemporary glitch-based composition: fractured signals, strong digital colour and deliberately integrated bird silhouettes."),
        ("Low-poly digital sculpture", "Faceted three-dimensional geometric sculptures, bold architectural lighting and bird-inspired angular forms."),
        ("Vector isometric design", "Crisp isometric vector geometry, clean colour fields, inventive spatial construction and small readable bird motifs."),
    ],
    "decorative_heritage": [
        ("Art Deco", "Genuine Art Deco ornamental geometry, streamlined curved forms, decorative metallic rhythm and strongly stylised birds."),
        ("Art Nouveau", "Whiplash botanical curves, elegant organic ornament, flowing lines and decorative stylised bird forms."),
        ("Arts and Crafts print", "Handcrafted ornamental botanical pattern, carved repeat motifs and detailed integrated bird decoration."),
        ("Cloisonné enamel", "Jewelled enamel colour cells, fine metallic outlines, ornamental symmetry and richly worked abstract bird imagery."),
    ],
    "atmospheric": [
        ("Oil painting", "Expressive authentic oil brushwork, richly nuanced colour and original contemporary painted composition."),
        ("Impressionism", "Luminous broken-colour brushwork, painterly sunlight and loose energetic mark-making."),
        ("Watercolour", "Transparent flowing pigments, granulation, atmospheric washes and lively unpainted space."),
        ("Pastel", "Powdery soft pastel marks, rich chalked layers and bold but gentle colour relationships."),
        ("Atmospheric mixed media", "Premium restrained mixed media with layered tactile surfaces and original subject matter; avoid generic moody seaside architecture."),
    ],
}

# Compatibility with existing imports and saved history.
STYLES = [entry for entries in STYLE_FAMILIES.values() for entry in entries]
STYLE_LOOKUP = {
    name: {"name": name, "guidance": guidance, "family": family}
    for family, entries in STYLE_FAMILIES.items()
    for name, guidance in entries
}

BOLD_FAMILIES = tuple(f for f in STYLE_FAMILIES if f != "atmospheric")
FAMILY_COOLDOWN = 3
# One atmospheric contrast in every ~10 automatic editions, rather than the
# overly frequent painterly return of earlier releases.
BOLD_BEFORE_ATMOSPHERIC = 9


def get_style(name: str) -> dict[str, str]:
    """Return a validated active style; removed Storybook cannot be selected."""
    try:
        return dict(STYLE_LOOKUP[str(name).strip()])
    except KeyError as error:
        raise ValueError(f"Unsupported artistic style: {name}") from error


def choose_style(history, preferred_style=None):
    """Rotate across ten families, keeping the last three families different.

    Explicit manual style tests do not influence automatic family selection.
    Sliding-window logic works even when old creative history is pruned.
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
    blocked = set(families[-FAMILY_COOLDOWN:])
    recent = families[-BOLD_BEFORE_ATMOSPHERIC:]

    atmospheric_due = (
        len(recent) == BOLD_BEFORE_ATMOSPHERIC
        and "atmospheric" not in recent
    )
    if atmospheric_due:
        family = "atmospheric"
    else:
        choices = [f for f in BOLD_FAMILIES if f not in blocked]
        family = min(
            choices,
            key=lambda f: (
                recent.count(f),
                BOLD_FAMILIES.index(f),
            ),
        )

    recently_used_styles = set(used[-5:])
    candidates = [
        entry for entry in STYLE_FAMILIES[family]
        if entry[0] not in recently_used_styles
    ]
    if not candidates:
        candidates = STYLE_FAMILIES[family]
    name, guidance = min(
        candidates,
        key=lambda entry: (
            used.count(entry[0]),
            STYLE_FAMILIES[family].index(entry),
        ),
    )
    return {"name": name, "guidance": guidance, "family": family}
