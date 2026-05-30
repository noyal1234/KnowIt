import logging
from typing import TypeVar

from app.config import get_settings
from app.providers.barcode.open_food_facts import OpenFoodFactsProvider
from app.providers.errors import ProviderError, ProviderJSONError, ProviderRetryableError
from app.providers.llm.anthropic import AnthropicLLMProvider
from app.providers.llm.groq import GroqLLMProvider
from app.providers.llm.huggingface_local import HuggingFaceLocalProvider
from app.providers.llm.ollama import OllamaLLMProvider
from app.providers.llm.openai import OpenAILLMProvider
from app.providers.llm.together import TogetherLLMProvider
from app.providers.ocr.google_vision import GoogleVisionOCRProvider
from app.providers.ocr.llama_vision import LlamaVisionOCRProvider
from app.providers.ocr.tesseract import TesseractOCRProvider
from app.providers.search.anthropic_web import AnthropicWebSearchProvider
from app.providers.search.openai_web import OpenAIWebSearchProvider
from app.providers.search.tavily import TavilySearchProvider
from app.providers.storage.local import LocalStorageProvider
from app.providers.storage.supabase import SupabaseStorageProvider

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar("T")

_LLM_FACTORIES = {
    "groq": GroqLLMProvider,
    "ollama": OllamaLLMProvider,
    "openai": OpenAILLMProvider,
    "anthropic": AnthropicLLMProvider,
    "together": TogetherLLMProvider,
    "huggingface_local": HuggingFaceLocalProvider,
}

_OCR_FACTORIES = {
    "tesseract": TesseractOCRProvider,
    "google_vision": GoogleVisionOCRProvider,
    "llama_vision": LlamaVisionOCRProvider,
}

_SEARCH_FACTORIES = {
    "tavily": lambda: TavilySearchProvider(settings.tavily_api_key),
    "openai_web": OpenAIWebSearchProvider,
    "anthropic_web": AnthropicWebSearchProvider,
}

_STORAGE_FACTORIES = {
    "local": LocalStorageProvider,
    "supabase": SupabaseStorageProvider,
}


def _build(factory_map: dict, name: str):
    factory = factory_map.get(name)
    if not factory:
        raise ValueError(f"Unknown provider: {name}")
    return factory() if callable(factory) and not isinstance(factory, type) else factory()


def get_llm_provider(name: str | None = None):
    return _build(_LLM_FACTORIES, name or settings.provider_llm)


def get_ocr_provider(name: str | None = None):
    return _build(_OCR_FACTORIES, name or settings.provider_ocr)


def get_search_provider(name: str | None = None):
    return _build(_SEARCH_FACTORIES, name or settings.provider_search)


def get_barcode_provider():
    return OpenFoodFactsProvider()


def get_storage_provider():
    return _build(_STORAGE_FACTORIES, settings.provider_storage)


def _parse_fallback_chain(chain: str) -> list[str]:
    return [p.strip() for p in chain.split(",") if p.strip()]


async def llm_complete_json_with_fallback(
    *,
    primary: str | None,
    fallback_chain: str | None,
    system: str,
    user: str,
    temperature: float,
    max_tokens: int,
    model: str | None = None,
) -> tuple[dict, str]:
    names = [primary or settings.provider_llm] + _parse_fallback_chain(
        fallback_chain or settings.provider_llm_fallback
    )
    seen: set[str] = set()
    last_error: Exception | None = None
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        provider = get_llm_provider(name)
        for attempt in range(2):
            try:
                result = await provider.complete_json(
                    system=system,
                    user=user,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model,
                )
                return result, provider.name
            except ProviderJSONError as exc:
                last_error = exc
                if attempt == 0:
                    user = user + "\n\nReturn ONLY valid JSON."
                    continue
            except ProviderRetryableError as exc:
                last_error = exc
                break
            except ProviderError as exc:
                last_error = exc
                break
    raise last_error or RuntimeError("All LLM providers failed")


async def ocr_with_fallback(image_bytes: bytes) -> tuple[str, str]:
    names = [settings.provider_ocr] + _parse_fallback_chain(settings.provider_ocr_fallback)
    last_error: Exception | None = None
    for name in names:
        try:
            provider = get_ocr_provider(name)
            text = await provider.extract_text(image_bytes)
            if text.strip():
                return text, provider.name
        except ProviderError as exc:
            last_error = exc
            logger.warning("event=OCRProviderFailed provider=%s error=%s", name, exc)
        except Exception as exc:
            last_error = ProviderError(str(exc))
            logger.warning("event=OCRProviderFailed provider=%s error=%s", name, exc)
    raise last_error or ProviderError("All OCR providers failed")


async def search_with_fallback(
    query: str, *, domains: list[str], max_results: int
) -> tuple[list, str]:
    names = [settings.provider_search] + _parse_fallback_chain(settings.provider_search_fallback)
    last_error: Exception | None = None
    for name in names:
        try:
            provider = get_search_provider(name)
            results = await provider.search(query, domains=domains, max_results=max_results)
            return results, provider.name
        except ProviderError as exc:
            last_error = exc
            logger.warning("event=SearchProviderFailed provider=%s error=%s", name, exc)
        except Exception as exc:
            last_error = ProviderError(str(exc))
            logger.warning("event=SearchProviderFailed provider=%s error=%s", name, exc)
    raise last_error or ProviderError("All search providers failed")
