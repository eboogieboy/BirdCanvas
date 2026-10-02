"""Render a complete Magic Mirror bird grid on the BirdCanvas Pi."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from bird_images import mirror_tile_path
from mirror_birds import DEFAULT_TILE_LIMIT, selected_birds
from paths import OUTPUT_DIR

PANEL_DIR = OUTPUT_DIR / "mirror"
PANEL_JPG = PANEL_DIR / "panel.jpg"
PANEL_META = PANEL_DIR / "panel.json"
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 900
DEFAULT_COLUMNS = 4

BACKGROUND = (10, 10, 10)
LABEL = (242, 242, 242)
MUTED = (175, 175, 175)
TILE_BACKGROUND = (246, 244, 237)


def _bounded(value, *, default: int, low: int, high: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default
    return min(max(value, low), high)


def _font(size: int, bold: bool = False):
    names = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ) if bold else (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int):
    size = max(16, start_size)
    while size > 16:
        font = _font(size, bold=True)
        bounds = draw.textbbox((0, 0), text, font=font)
        if bounds[2] - bounds[0] <= max_width:
            return font
        size -= 2
    return _font(16, bold=True)


def _signature(
    *,
    birds: list[dict],
    tile_paths: list[Path],
    width: int,
    height: int,
    columns: int,
    slots: int,
) -> str:
    payload = {
        "width": width,
        "height": height,
        "columns": columns,
        "slots": slots,
        "birds": [
            {
                "name": str(bird.get("name", "")),
                "scientific_name": str(bird.get("scientific_name", "")),
                "tile": str(path.name),
                "tile_mtime_ns": path.stat().st_mtime_ns,
                "tile_size": path.stat().st_size,
            }
            for bird, path in zip(birds, tile_paths)
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_meta(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _draw_empty(panel: Image.Image) -> None:
    draw = ImageDraw.Draw(panel)
    title = "Listening for birds…"
    font = _font(max(26, panel.width // 30), bold=True)
    bounds = draw.textbbox((0, 0), title, font=font)
    x = (panel.width - (bounds[2] - bounds[0])) / 2
    y = (panel.height - (bounds[3] - bounds[1])) / 2
    draw.text((x, y), title, fill=LABEL, font=font)


def _render(
    birds: list[dict],
    tile_paths: list[Path],
    *,
    width: int,
    height: int,
    columns: int,
    slots: int,
) -> Image.Image:
    panel = Image.new("RGB", (width, height), BACKGROUND)
    if not birds:
        _draw_empty(panel)
        return panel

    draw = ImageDraw.Draw(panel)
    rows = max(1, math.ceil(slots / columns))
    cell_width = width / columns
    cell_height = height / rows

    for index, (bird, tile_path) in enumerate(zip(birds, tile_paths)):
        row, column = divmod(index, columns)
        left = int(column * cell_width)
        top = int(row * cell_height)
        right = int((column + 1) * cell_width)
        bottom = int((row + 1) * cell_height)

        pad = max(10, int(min(cell_width, cell_height) * 0.045))
        label_height = max(38, int(cell_height * 0.18))
        image_space_width = max(1, right - left - pad * 2)
        image_space_height = max(1, bottom - top - label_height - pad * 2)
        image_side = max(1, min(image_space_width, image_space_height))

        with Image.open(tile_path) as opened:
            tile = ImageOps.fit(
                ImageOps.exif_transpose(opened).convert("RGB"),
                (image_side, image_side),
                method=Image.Resampling.LANCZOS,
            )

        image_left = left + (right - left - image_side) // 2
        image_top = top + pad
        draw.rounded_rectangle(
            (
                image_left - 2,
                image_top - 2,
                image_left + image_side + 2,
                image_top + image_side + 2,
            ),
            radius=max(8, image_side // 28),
            fill=TILE_BACKGROUND,
        )
        panel.paste(tile, (image_left, image_top))

        name = str(bird.get("name", "")).strip()
        text_top = image_top + image_side + max(8, pad // 2)
        font = _fit_font(draw, name, max_width=right - left - pad * 2, start_size=max(22, int(cell_width * 0.085)))
        bounds = draw.textbbox((0, 0), name, font=font)
        text_width = bounds[2] - bounds[0]
        draw.text(
            (left + (right - left - text_width) / 2, text_top),
            name,
            fill=LABEL,
            font=font,
        )

    return panel


def build_mirror_panel(
    *,
    now: datetime | None = None,
    limit: int = DEFAULT_TILE_LIMIT,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    columns: int = DEFAULT_COLUMNS,
    output_dir: Path | None = None,
) -> Path:
    """Build or reuse the current complete bird-grid JPEG."""
    width = _bounded(width, default=DEFAULT_WIDTH, low=600, high=2400)
    height = _bounded(height, default=DEFAULT_HEIGHT, low=450, high=1800)
    columns = _bounded(columns, default=DEFAULT_COLUMNS, low=2, high=6)
    limit = _bounded(limit, default=DEFAULT_TILE_LIMIT, low=1, high=24)

    _, _, birds = selected_birds(now=now, limit=limit)
    birds = [bird for bird in birds if str(bird.get("name", "")).strip()]
    tile_paths = [
        mirror_tile_path(
            str(bird.get("name", "")),
            str(bird.get("scientific_name", "")),
        )
        for bird in birds
    ]

    panel_dir = Path(output_dir) if output_dir is not None else PANEL_DIR
    panel_path = panel_dir / "panel.jpg"
    meta_path = panel_dir / "panel.json"
    panel_dir.mkdir(parents=True, exist_ok=True)

    signature = _signature(
        birds=birds,
        tile_paths=tile_paths,
        width=width,
        height=height,
        columns=columns,
        slots=limit,
    )
    previous = _read_meta(meta_path)
    if panel_path.is_file() and previous.get("signature") == signature:
        return panel_path

    panel = _render(
        birds,
        tile_paths,
        width=width,
        height=height,
        columns=columns,
        slots=limit,
    )
    panel.save(panel_path, "JPEG", quality=92, subsampling=0, optimize=True)

    meta_path.write_text(
        json.dumps(
            {
                "signature": signature,
                "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "width": width,
                "height": height,
                "columns": columns,
                "slots": limit,
                "birds": [str(bird.get("name", "")) for bird in birds],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return panel_path
