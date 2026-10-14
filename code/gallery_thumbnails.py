"""Serve compact cached artwork previews without modifying originals."""
from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

from PIL import Image, ImageOps
from gallery_library import artwork_image_path
from paths import OUTPUT_DIR

CACHE_DIR = OUTPUT_DIR / 'gallery' / 'thumbs'
SIZE = (420, 560)


def thumbnail_path(artwork_id: str) -> Path:
    source = artwork_image_path(artwork_id)
    stat = source.stat()
    digest = hashlib.sha256(f'{artwork_id}:{source}:{stat.st_mtime_ns}:{stat.st_size}'.encode()).hexdigest()
    dest = CACHE_DIR / f'{digest}.jpg'
    if dest.is_file():
        return dest
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temp = dest.with_name(f'.{digest}-{uuid.uuid4().hex}.tmp')
    try:
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original)
            image.thumbnail(SIZE, Image.Resampling.LANCZOS)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(temp, format='JPEG', quality=78, optimize=True)
        os.replace(temp, dest)
    finally:
        temp.unlink(missing_ok=True)
    return dest
