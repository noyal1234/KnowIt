import base64
import json
import logging

import httpx

from app.config import get_settings
from app.providers.errors import ProviderRetryableError
from app.services.image_preprocess import preprocess_image

logger = logging.getLogger(__name__)
settings = get_settings()


class GoogleVisionOCRProvider:
    name = "google_vision"

    async def extract_text(self, image_bytes: bytes) -> str:
        if not settings.google_vision_credentials:
            raise ProviderRetryableError("GOOGLE_VISION_CREDENTIALS not configured")
        processed = preprocess_image(image_bytes)
        # Expect JSON service account or API key path
        api_key = settings.google_vision_credentials
        encoded = base64.b64encode(processed).decode()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
                json={
                    "requests": [
                        {
                            "image": {"content": encoded},
                            "features": [{"type": "TEXT_DETECTION"}],
                        }
                    ]
                },
            )
            if resp.status_code >= 500:
                raise ProviderRetryableError(f"Google Vision error: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            annotations = data["responses"][0].get("textAnnotations", [])
            return annotations[0]["description"] if annotations else ""
