from app.providers.base import SearchResult
from app.providers.llm.openai import OpenAILLMProvider


class OpenAIWebSearchProvider:
    name = "openai_web"

    def __init__(self) -> None:
        self._llm = OpenAILLMProvider()

    async def search(
        self, query: str, *, domains: list[str], max_results: int
    ) -> list[SearchResult]:
        domain_hint = ", ".join(domains)
        text = await self._llm.complete_text(
            system="Search authoritative sources and summarize findings as JSON array.",
            user=f"Search for: {query}. Prefer domains: {domain_hint}. Max {max_results} results.",
            temperature=0.0,
            max_tokens=1500,
            model="gpt-4o",
        )
        return [SearchResult(title=query, url="", snippet=text[:500])]
