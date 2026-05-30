import asyncio
import io
import logging

import pytesseract
from PIL import Image

from app.services.image_preprocess import preprocess_image

logger = logging.getLogger(__name__)


class TesseractOCRProvider:
    name = "tesseract"

    async def extract_text(self, image_bytes: bytes) -> str:
        processed = preprocess_image(image_bytes)

        def _run() -> str:
            img = Image.open(io.BytesIO(processed))
            return pytesseract.image_to_string(img)

        try:
            return await asyncio.to_thread(_run)
        except pytesseract.TesseractNotFoundError:
            logger.warning("Tesseract not installed — returning empty OCR text")
            return ""
