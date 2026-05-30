import logging

from app.config import get_settings
from app.pipeline.prompts import OCR_CLEANUP_SYSTEM, SPELLCHECK_USER
from app.providers.registry import get_llm_provider, llm_complete_json_with_fallback

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_stage0_ocr_cleanup(raw_text: str, *, skip: bool = False) -> tuple[str, str | None]:
    if skip or not raw_text.strip():
        return raw_text, None

    if settings.pipeline_phase == "build":
        return raw_text, None

    provider_name = settings.provider_llm_stage0
    try:
        if provider_name == "ollama":
            provider = get_llm_provider("ollama")
            corrected = await provider.complete_text(
                system=OCR_CLEANUP_SYSTEM,
                user=SPELLCHECK_USER.format(text=raw_text),
                temperature=0.0,
                max_tokens=800,
                model=settings.model_stage0,
            )
            return corrected.strip(), provider.name
        provider = get_llm_provider("huggingface_local")
        corrected = await provider.complete_text(
            system=OCR_CLEANUP_SYSTEM,
            user=SPELLCHECK_USER.format(text=raw_text),
            temperature=0.0,
            max_tokens=800,
            model=settings.model_stage0,
        )
        return corrected.strip(), provider.name
    except Exception as exc:
        logger.warning("Stage 0 OCR cleanup failed, using raw text: %s", exc)
        return raw_text, None
