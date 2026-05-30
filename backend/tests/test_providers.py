import pytest

from app.providers.registry import _parse_fallback_chain


def test_parse_fallback_chain():
    assert _parse_fallback_chain("groq, openai, anthropic") == ["groq", "openai", "anthropic"]
    assert _parse_fallback_chain("groq") == ["groq"]
