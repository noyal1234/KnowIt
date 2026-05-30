from typing import Any

from app.providers.llm.anthropic import AnthropicLLMProvider
from app.providers.llm.groq import GroqLLMProvider


class TogetherLLMProvider(GroqLLMProvider):
    """Together AI uses OpenAI-compatible API — reuse Groq pattern with different base URL."""

    name = "together"

    async def complete_text(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        model: str | None = None,
    ) -> str:
        import httpx

        from app.config import get_settings
        from app.providers.errors import ProviderRetryableError

        settings = get_settings()
        if not settings.together_api_key:
            raise ProviderRetryableError("TOGETHER_API_KEY not configured")
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.together_api_key}"},
                json={
                    "model": model or "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            if resp.status_code >= 500:
                raise ProviderRetryableError(f"Together error: {resp.status_code}")
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        model: str | None = None,
    ) -> dict[str, Any]:
        return await super().complete_json(
            system=system, user=user, temperature=temperature, max_tokens=max_tokens, model=model
        )
