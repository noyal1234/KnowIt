import json
from typing import Any

import httpx

from app.config import get_settings
from app.pipeline.utils import parse_json_from_llm
from app.providers.errors import ProviderJSONError, ProviderRetryableError

settings = get_settings()


class OllamaLLMProvider:
    name = "ollama"

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        model: str | None = None,
    ) -> dict[str, Any]:
        text = await self.complete_text(
            system=system, user=user, temperature=temperature, max_tokens=max_tokens, model=model
        )
        try:
            return parse_json_from_llm(text)
        except (ValueError, json.JSONDecodeError) as exc:
            raise ProviderJSONError(str(exc)) from exc

    async def complete_text(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        model: str | None = None,
    ) -> str:
        model_id = model or "mistral:7b"
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            )
            if resp.status_code >= 500:
                raise ProviderRetryableError(f"Ollama error: {resp.status_code}")
            resp.raise_for_status()
            return resp.json()["message"]["content"]
