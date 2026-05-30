import pytest

from app.providers.barcode.open_food_facts import OpenFoodFactsProvider
from app.providers.errors import ProviderRetryableError
from app.providers.registry import _parse_fallback_chain


def test_parse_fallback_chain():
    assert _parse_fallback_chain("groq, openai, anthropic") == ["groq", "openai", "anthropic"]
    assert _parse_fallback_chain("groq") == ["groq"]


@pytest.mark.asyncio
async def test_open_food_facts_maps_server_error(monkeypatch):
    class FakeResponse:
        status_code = 503

        def json(self):
            return {}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url):
            return FakeResponse()

    monkeypatch.setattr(
        "app.providers.barcode.open_food_facts.httpx.AsyncClient",
        lambda **kwargs: FakeClient(),
    )
    provider = OpenFoodFactsProvider()
    with pytest.raises(ProviderRetryableError):
        await provider.lookup("3017620422003")
