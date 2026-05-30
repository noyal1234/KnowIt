import base64

from app.config import get_settings
from app.providers.llm.ollama import OllamaLLMProvider
from app.services.image_preprocess import preprocess_image

settings = get_settings()


class LlamaVisionOCRProvider:
    name = "llama_vision"

    def __init__(self) -> None:
        self._llm = OllamaLLMProvider()

    async def extract_text(self, image_bytes: bytes) -> str:
        processed = preprocess_image(image_bytes)
        b64 = base64.b64encode(processed).decode()
        # Ollama vision models accept images in chat — simplified text fallback prompt
        prompt = (
            "Extract the full ingredient list text from this food label image. "
            "Return only the ingredient list as plain text."
        )
        async with __import__("httpx").AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={
                    "model": "llama3.2-vision:11b",
                    "messages": [{"role": "user", "content": prompt, "images": [b64]}],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
