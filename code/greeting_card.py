"""Prepare a portrait greeting-card front from the selected archive entry."""
from io import BytesIO

from PIL import Image, ImageOps

from gallery_library import artwork_image_path


def render_card_front(artwork_id: str) -> bytes:
    # 100 × 140 mm at 300 ppi, with at least 6 mm of clear paper per edge.
    paper = Image.new("RGB", (1181, 1654), "#faf8f2")
    margin = 71
    bounds = (paper.width - 2 * margin, paper.height - 2 * margin)
    with Image.open(artwork_image_path(artwork_id, prefer_original=True)) as source:
        artwork = ImageOps.contain(ImageOps.exif_transpose(source), bounds, Image.Resampling.LANCZOS)
        artwork = artwork.convert("RGBA")
        position = ((paper.width - artwork.width) // 2, (paper.height - artwork.height) // 2)
        paper.paste(artwork, position, artwork)
    output = BytesIO()
    paper.save(output, "JPEG", quality=95, subsampling=0, dpi=(300, 300))
    return output.getvalue()
