import json
import logging
from typing import Any

import httpx

from app.config import get_settings
from app.pipeline.utils import parse_json_from_llm
from app.providers.errors import ProviderJSONError, ProviderRetryableError

logger = logging.getLogger(__name__)
settings = get_settings()


class GroqLLMProvider:
    name = "groq"

    def __init__(self) -> None:
        self._default_model = settings.model_stage2

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
            system=system,
            user=user,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
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
        if not settings.groq_api_key:
            raise ProviderRetryableError("GROQ_API_KEY not configured")
        model_id = model or self._default_model
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            if resp.status_code >= 500:
                raise ProviderRetryableError(f"Groq error: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
