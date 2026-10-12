"""Curated creative-style rotation for BirdCanvas artwork."""
STYLES = [
    ("Pop art", "Bold, colourful screenprint-inspired pop art with sophisticated graphic composition."),
    ("Oil painting", "Expressive oil painting with visible brushwork and luminous pigment."),
    ("Storybook illustration", "Inventive, polished illustrated worlds with expressive drawing; refined rather than childish."),
    ("Japanese woodblock", "Ukiyo-e-inspired carved shapes, elegant ink outlines, and flat colour."),
    ("Impressionism", "Impressionist broken colour, light-filled brushwork, and atmospheric space."),
    ("Art Deco", "Art Deco geometry, rich colour, architectural ornament, and elegant composition."),
    ("Watercolour", "Transparent watercolour washes, soft bleeding pigments, and luminous paper texture."),
    ("Surrealism", "Dreamlike surrealist worlds with poetic juxtaposition and deliberate visual logic."),
    ("Paper collage", "Tactile cut-paper collage with layered shapes and considered colour."),
    ("Graphic novel", "Cinematic graphic-novel inkwork, deliberate framing, and expressive colour."),
    ("Mid-century modern", "Mid-century editorial illustration with modernist shapes and print textures."),
    ("Linocut", "Hand-carved linocut relief with graphic positive/negative space and bold ink."),
    ("Cubism", "Cubist planes, fractured perspective, and vibrant geometric rhythm."),
    ("Folk art", "Inventive decorative folk art with distinctive hand-crafted motifs and joyful colour."),
    ("Pastel", "Rich chalk pastel with luminous blended pigment and expressive marks."),
    ("Stained glass", "Radiant stained glass with structural lead lines and jewel-like colour."),
    ("Minimalism", "Minimalist gallery artwork with confident negative space and reduced forms."),
    ("Atmospheric mixed media", "Textured atmospheric mixed-media architecture and quiet material storytelling."),
]


def choose_style(history):
    """No extra model call; avoid styles represented among five latest generations."""
    used = [str(item.get("art_style", "")) for item in history if item.get("art_style")]
    recent = set(used[-5:])
    start = len(used) % len(STYLES)
    for step in range(len(STYLES)):
        name, guidance = STYLES[(start + step) % len(STYLES)]
        if name not in recent:
            return {"name": name, "guidance": guidance}
    name, guidance = STYLES[start]
    return {"name": name, "guidance": guidance}
