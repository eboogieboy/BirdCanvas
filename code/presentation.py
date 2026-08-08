from __future__ import annotations

from pathlib import Path
from statistics import fmean, pstdev
from typing import Any

from PIL import Image, ImageEnhance, ImageOps, ImageStat

DEFAULT_STYLE = "auto"
OUTPUT_SIZE = (1080, 1920)

STYLES: dict[str, dict[str, Any]] = {
    "auto": {"name": "Automatic Mount"},
    "white_mount": {
        "name": "White Mount",
        "colour": (244, 243, 238),
        "inner_line": (218, 217, 211),
    },
    "black_mount": {
        "name": "Black Mount",
        "colour": (20, 20, 21),
        "inner_line": (54, 54, 56),
    },
    "no_mount": {"name": "No Mount"},
}


def _luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _analyse_image(image: Image.Image) -> dict[str, float]:
    sample = ImageOps.exif_transpose(image).convert("RGB")
    sample.thumbnail((240, 360), Image.Resampling.LANCZOS)

    width, height = sample.size
    band = max(2, min(width, height) // 16)

    edge_crops = [
        sample.crop((0, 0, width, band)),
        sample.crop((0, height - band, width, height)),
        sample.crop((0, band, band, height - band)),
        sample.crop((width - band, band, width, height - band)),
    ]

    edge_pixels: list[tuple[int, int, int]] = []
    for crop in edge_crops:
        edge_pixels.extend(list(crop.getdata()))

    edge_luminances = [_luminance(pixel) for pixel in edge_pixels]
    edge_mean_rgb = tuple(fmean(pixel[channel] for pixel in edge_pixels) for channel in range(3))
    edge_luminance = fmean(edge_luminances)
    edge_variation = pstdev(edge_luminances) if len(edge_luminances) > 1 else 0.0

    inset_x = max(band * 2, width // 6)
    inset_y = max(band * 2, height // 6)
    if inset_x * 2 >= width or inset_y * 2 >= height:
        centre = sample
    else:
        centre = sample.crop((inset_x, inset_y, width - inset_x, height - inset_y))

    centre_mean_rgb = tuple(ImageStat.Stat(centre).mean[:3])
    centre_luminance = _luminance(centre_mean_rgb)
    edge_centre_difference = abs(edge_luminance - centre_luminance)

    hsv = sample.convert("HSV")
    saturation = ImageStat.Stat(hsv).mean[1]

    return {
        "edge_luminance": round(edge_luminance, 2),
        "centre_luminance": round(centre_luminance, 2),
        "edge_variation": round(edge_variation, 2),
        "edge_centre_difference": round(edge_centre_difference, 2),
        "average_saturation": round(saturation, 2),
        "edge_red": round(edge_mean_rgb[0], 2),
        "edge_green": round(edge_mean_rgb[1], 2),
        "edge_blue": round(edge_mean_rgb[2], 2),
    }


def choose_mount(image: Image.Image) -> tuple[str, str, dict[str, float]]:
    analysis = _analyse_image(image)
    edge_luminance = analysis["edge_luminance"]
    edge_variation = analysis["edge_variation"]
    edge_centre_difference = analysis["edge_centre_difference"]

    # A quiet, consistent edge that is clearly different from the centre usually
    # means the artwork already contains its own visual margin or border.
    has_natural_border = edge_variation < 18 and edge_centre_difference > 42
    if has_natural_border:
        return (
            "no_mount",
            "The artwork already has a calm, contrasting edge that acts as its own border.",
            analysis,
        )

    # Strongly light or dark edges benefit from the opposite mount.
    if edge_luminance >= 174:
        return (
            "black_mount",
            "The artwork has light outer edges, so a black mount gives clean separation.",
            analysis,
        )

    if edge_luminance <= 82:
        return (
            "white_mount",
            "The artwork has dark outer edges, so a white mount gives clean separation.",
            analysis,
        )

    # Mid-tone work is judged by whichever neutral gives the greater luminance contrast.
    contrast_to_white = abs(244 - edge_luminance)
    contrast_to_black = abs(20 - edge_luminance)
    if contrast_to_white >= contrast_to_black:
        return (
            "white_mount",
            "A white mount gives the strongest restrained contrast with the artwork edge.",
            analysis,
        )

    return (
        "black_mount",
        "A black mount gives the strongest restrained contrast with the artwork edge.",
        analysis,
    )


def _fit_inside(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
    return fitted


def _fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(
        image,
        size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def create_gallery_presentation(
    source_image: Path,
    destination: Path,
    *,
    style: str = DEFAULT_STYLE,
    output_size: tuple[int, int] = OUTPUT_SIZE,
) -> dict[str, Any]:
    if style not in STYLES:
        raise ValueError(f"Unknown presentation style: {style}")
    if not source_image.is_file():
        raise FileNotFoundError(f"Artwork image not found: {source_image}")

    with Image.open(source_image) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")

    requested_style = style
    reason = "The mount style was selected manually."
    analysis = _analyse_image(source)

    if style == "auto":
        style = "no_mount"
        reason = "Samsung Frame full-screen mode."

    canvas_w, canvas_h = output_size

    if style == "no_mount":
        result = _fit_cover(source, output_size)
        mount_width = 0
    else:
        config = STYLES[style]
        mount_colour = config["colour"]
        inner_line = config["inner_line"]

        # Approximately 6.5% side mount, with a subtly deeper lower margin.
        side = max(48, round(canvas_w * 0.065))
        top = side
        bottom = round(side * 1.16)
        art_area = (canvas_w - side * 2, canvas_h - top - bottom)

        result = Image.new("RGB", output_size, mount_colour)
        artwork = _fit_inside(source, art_area)

        x = (canvas_w - artwork.width) // 2
        available_height = canvas_h - top - bottom
        y = top + (available_height - artwork.height) // 2

        # A one-pixel neutral key line gives definition without simulating a frame.
        line_width = max(1, round(canvas_w / 1200))
        keyed = ImageOps.expand(artwork, border=line_width, fill=inner_line)
        result.paste(keyed, (x - line_width, y - line_width))
        mount_width = side

    result = ImageEnhance.Sharpness(result).enhance(1.02)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination, "PNG", optimize=True)

    return {
        "mode": requested_style,
        "applied_mount": style.replace("_mount", "").replace("no_", ""),
        "style": style,
        "style_name": STYLES[style]["name"],
        "decision_reason": reason,
        "analysis": analysis,
        "mount_width": mount_width,
        "output_size": list(output_size),
        "source_image": source_image.name,
        "presented_image": destination.name,
    }
