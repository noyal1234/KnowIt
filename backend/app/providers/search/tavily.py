import logging
from typing import Any

import httpx

from app.providers.base import SearchResult
from app.providers.errors import ProviderRetryableError

logger = logging.getLogger(__name__)


class TavilySearchProvider:
    name = "tavily"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def search(
        self, query: str, *, domains: list[str], max_results: int
    ) -> list[SearchResult]:
        if not self._api_key:
            logger.warning("TAVILY_API_KEY not set — returning empty search results")
            return []
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self._api_key,
                    "query": query,
                    "include_domains": domains,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
            )
            if resp.status_code >= 500:
                raise ProviderRetryableError(f"Tavily error: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("content", ""),
                )
                for r in data.get("results", [])
            ]
