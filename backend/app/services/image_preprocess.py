import io
import logging

from PIL import Image, ImageEnhance, ImageOps

logger = logging.getLogger(__name__)


def preprocess_image(image_bytes: bytes) -> bytes:
    """Resize, enhance contrast, and auto-orient label photos."""
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    max_dim = 2000
    if max(img.size) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
