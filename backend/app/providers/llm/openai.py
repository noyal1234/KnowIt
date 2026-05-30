import json
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings
from app.pipeline.utils import parse_json_from_llm
from app.providers.errors import ProviderJSONError

settings = get_settings()


class OpenAILLMProvider:
    name = "openai"

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key or "missing")

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
        response = await self._client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
