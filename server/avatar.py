"""Profile pictures. Every upload is decoded and re-encoded as a 256x256 WebP, which drops EXIF
(GPS and camera data), embedded scripts and anything that is not really pixels."""
from __future__ import annotations

import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PIXELS = 16_000_000
SIZE = 256
ALLOWED = {"JPEG", "PNG", "WEBP", "GIF"}
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class AvatarError(ValueError):
    pass


def process_avatar(raw: bytes) -> bytes:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(io.BytesIO(raw))
            if img.format not in ALLOWED:
                raise AvatarError("Use a JPG, PNG, WebP or GIF image.")
            if img.width * img.height > MAX_PIXELS:
                raise AvatarError("That image is too large. Use one under 16 megapixels.")
            img.load()
    except AvatarError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, OSError, ValueError, SyntaxError):
        raise AvatarError("That file is not a readable image.")
    img = ImageOps.exif_transpose(img)
    rgba = img.convert("RGBA")
    flat = Image.new("RGB", rgba.size, (20, 22, 25))
    flat.paste(rgba, mask=rgba.getchannel("A"))
    square = ImageOps.fit(flat, (SIZE, SIZE), Image.LANCZOS, centering=(0.5, 0.5))
    out = io.BytesIO()
    square.save(out, "WEBP", quality=85, method=4)
    return out.getvalue()
