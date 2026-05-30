from app.providers.base import SearchResult
from app.providers.llm.anthropic import AnthropicLLMProvider


class AnthropicWebSearchProvider:
    name = "anthropic_web"

    def __init__(self) -> None:
        self._llm = AnthropicLLMProvider()

    async def search(
        self, query: str, *, domains: list[str], max_results: int
    ) -> list[SearchResult]:
        domain_hint = ", ".join(domains)
        text = await self._llm.complete_text(
            system="Summarize authoritative regulatory/clinical findings.",
            user=f"Research: {query}. Domains: {domain_hint}. Limit {max_results}.",
            temperature=0.0,
            max_tokens=1500,
            model="claude-3-5-sonnet-20241022",
        )
        return [SearchResult(title=query, url="", snippet=text[:500])]
