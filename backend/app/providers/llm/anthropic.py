import json
from typing import Any

from anthropic import AsyncAnthropic

from app.config import get_settings
from app.pipeline.utils import parse_json_from_llm
from app.providers.errors import ProviderJSONError

settings = get_settings()


class AnthropicLLMProvider:
    name = "anthropic"

    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key or "missing")

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
        response = await self._client.messages.create(
            model=model or "claude-3-5-haiku-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text
