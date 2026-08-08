from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageOps

from paths import OUTPUT_DIR


FRAME_SIZE = (1080, 1920)
FRAME_DIR = OUTPUT_DIR / "frame"
FRAME_JPG = FRAME_DIR / "frame-ready.jpg"


def _env_enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def frame_enabled() -> bool:
    return _env_enabled("BIRDCANVAS_FRAME_ENABLED", False)


def _samsungtv_binary() -> str:
    override = os.getenv(
        "BIRDCANVAS_FRAME_SAMSUNGTV",
        "",
    ).strip()

    if override:
        candidate = Path(override).expanduser()

        if not candidate.is_file():
            raise FileNotFoundError(
                f"Configured samsungtv command not found: {candidate}"
            )

        return str(candidate)

    # If samsungtvws was installed into the same virtual environment
    # as BirdCanvas, its CLI should sit alongside the current Python.
    alongside_python = Path(sys.executable).with_name("samsungtv")

    if alongside_python.is_file():
        return str(alongside_python)

    found = shutil.which("samsungtv")

    if found:
        return found

    raise FileNotFoundError(
        "Samsung TV CLI not found. "
        'Install it with: pip install "samsungtvws[cli]"'
    )


def prepare_frame_jpg(source_image: Path) -> Path:
    source_image = Path(source_image)

    if not source_image.is_file():
        raise FileNotFoundError(
            f"BirdCanvas artwork not found: {source_image}"
        )

    FRAME_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with Image.open(source_image) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")

        # BirdCanvas should already supply 1080 x 1920.
        # ImageOps.fit keeps this function safe for custom artwork too.
        ready = ImageOps.fit(
            source,
            FRAME_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

        ready.save(
            FRAME_JPG,
            "JPEG",
            quality=95,
            subsampling=0,
            optimize=True,
        )

    return FRAME_JPG


def _run_samsungtv(*arguments: str) -> str:
    host = os.getenv(
        "BIRDCANVAS_FRAME_HOST",
        "",
    ).strip()

    if not host:
        raise RuntimeError(
            "BIRDCANVAS_FRAME_HOST has not been configured."
        )

    token_file = Path(
        os.getenv(
            "BIRDCANVAS_FRAME_TOKEN_FILE",
            "~/.birdcanvas-frame-token",
        )
    ).expanduser()

    client_name = os.getenv(
        "BIRDCANVAS_FRAME_NAME",
        "BirdCanvas",
    ).strip() or "BirdCanvas"

    command = [
        _samsungtv_binary(),
        "--host",
        host,
        "--token-file",
        str(token_file),
        "--name",
        client_name,
        "--timeout",
        "30",
        *arguments,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=90,
    )

    if result.returncode != 0:
        details = (
            result.stderr.strip()
            or result.stdout.strip()
            or f"exit status {result.returncode}"
        )

        raise RuntimeError(
            f"Samsung Frame command failed: {details}"
        )

    return result.stdout.strip()


def upload_to_frame(source_image: Path) -> dict | None:
    """
    Upload one BirdCanvas artwork to the Samsung Frame and display it.

    Returns None when Frame integration is disabled.
    """

    if not frame_enabled():
        return None

    ready_image = prepare_frame_jpg(source_image)

    print(
        f"Preparing Samsung Frame artwork: "
        f"{ready_image} ({FRAME_SIZE[0]}x{FRAME_SIZE[1]})"
    )

    upload_output = _run_samsungtv(
        "art-upload",
        "--matte",
        "none",
        "--portrait-matte",
        "none",
        str(ready_image),
    )

    match = re.search(
        r"\b(MY_[A-Za-z0-9_]+)\b",
        upload_output,
    )

    if not match:
        raise RuntimeError(
            "Samsung upload completed but no content ID "
            f"was returned. Output: {upload_output}"
        )

    content_id = match.group(1)

    print(
        f"Samsung Frame upload complete: {content_id}"
    )

    _run_samsungtv(
        "art-display",
        content_id,
    )

    print(
        f"Samsung Frame now displaying: {content_id}"
    )

    return {
        "content_id": content_id,
        "image": str(ready_image),
        "host": os.getenv(
            "BIRDCANVAS_FRAME_HOST",
            "",
        ).strip(),
    }
