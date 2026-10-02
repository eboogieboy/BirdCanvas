"""Render a complete Magic Mirror bird grid on the BirdCanvas Pi."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from bird_catalog import record_birds
from bird_images import mirror_tile_path
from mirror_birds import DEFAULT_TILE_LIMIT, selected_birds
from paths import OUTPUT_DIR

PANEL_DIR = OUTPUT_DIR / "mirror"
PANEL_JPG = PANEL_DIR / "panel.jpg"
PANEL_META = PANEL_DIR / "panel.json"
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 900
DEFAULT_COLUMNS = 4
PANEL_RENDER_VERSION = 4

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
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans.ttf",
    ) if bold else (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _label_candidates(text: str) -> list[str]:
    words = str(text).split()
    candidates = [str(text)]
    if len(words) > 1:
        candidates.extend(
            " ".join(words[:index]) + "\n" + " ".join(words[index:])
            for index in range(1, len(words))
        )
    return candidates


def _fit_label(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int):
    """Keep labels large; stay on one line when possible, otherwise use two."""
    size = max(20, start_size)
    candidates = _label_candidates(text)
    while size >= 20:
        font = _font(size, bold=True)

        single = candidates[0]
        bounds = draw.textbbox((0, 0), single, font=font)
        if bounds[2] - bounds[0] <= max_width:
            return single, font

        wrapped = []
        for candidate in candidates[1:]:
            bounds = draw.multiline_textbbox((0, 0), candidate, font=font, spacing=2, align="center")
            width = bounds[2] - bounds[0]
            if width <= max_width:
                wrapped.append((width, candidate))
        if wrapped:
            wrapped.sort(key=lambda item: item[0])
            return wrapped[0][1], font

        size -= 2
    return str(text), _font(20, bold=True)


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
        "render_version": PANEL_RENDER_VERSION,
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

    # Use a compact fixed grid rather than stretching each slot across the
    # whole panel. This keeps neighbouring bird plates visually grouped while
    # preserving the 4 x 3 structure when all 12 slots are occupied.
    row_height = height / rows
    card_width = min(width / columns, max(200, width * 0.19))
    horizontal_gap = max(3, int(width * 0.003))
    grid_width = columns * card_width + (columns - 1) * horizontal_gap
    grid_left = max(0, (width - grid_width) / 2)

    label_gap = max(4, int(row_height * 0.012))
    label_height = max(68, int(row_height * 0.24))
    vertical_pad = max(3, int(row_height * 0.012))
    image_side = int(
        max(
            1,
            min(
                card_width - 8,
                row_height - label_height - label_gap - vertical_pad * 2,
            ),
        )
    )

    for index, (bird, tile_path) in enumerate(zip(birds, tile_paths)):
        row, column = divmod(index, columns)
        left = grid_left + column * (card_width + horizontal_gap)
        top = row * row_height

        with Image.open(tile_path) as opened:
            tile = ImageOps.fit(
                ImageOps.exif_transpose(opened).convert("RGB"),
                (image_side, image_side),
                method=Image.Resampling.LANCZOS,
            )

        image_left = int(left + (card_width - image_side) / 2)
        image_top = int(top + vertical_pad)
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
        text_top = image_top + image_side + label_gap
        label, font = _fit_label(
            draw,
            name,
            max_width=int(card_width - 2),
            start_size=max(38, int(card_width * 0.17)),
        )
        bounds = draw.multiline_textbbox((0, 0), label, font=font, spacing=2, align="center")
        text_width = bounds[2] - bounds[0]
        draw.multiline_text(
            (left + (card_width - text_width) / 2, text_top),
            label,
            fill=LABEL,
            font=font,
            spacing=2,
            align="center",
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
    record_birds(birds)
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
