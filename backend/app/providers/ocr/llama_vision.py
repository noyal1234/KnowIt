import asyncio
import base64
import logging

import httpx

from app.config import get_settings
from app.providers.errors import ProviderError, ProviderRetryableError
from app.providers.llm.ollama import OllamaLLMProvider
from app.services.image_preprocess import preprocess_image

logger = logging.getLogger(__name__)
settings = get_settings()


class LlamaVisionOCRProvider:
    name = "llama_vision"

    def __init__(self) -> None:
        self._llm = OllamaLLMProvider()

    async def extract_text(self, image_bytes: bytes) -> str:
        processed = await asyncio.to_thread(preprocess_image, image_bytes)
        b64 = base64.b64encode(processed).decode()
        prompt = (
            "Extract the full ingredient list text from this food label image. "
            "Return only the ingredient list as plain text."
        )
        model = settings.model_ocr_llama_vision
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt, "images": [b64]}],
                        "stream": False,
                    },
                )
        except httpx.TimeoutException as exc:
            raise ProviderRetryableError("Llama vision OCR timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Llama vision OCR failed: {exc}") from exc

        if resp.status_code >= 500:
            raise ProviderRetryableError(f"Llama vision OCR error: {resp.status_code}")
        if resp.status_code >= 400:
            raise ProviderError(f"Llama vision OCR error: {resp.status_code}")
        return resp.json()["message"]["content"]
