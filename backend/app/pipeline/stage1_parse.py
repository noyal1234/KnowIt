import json
import logging

from app.config import get_settings
from app.models.pipeline import ParsedIngredient, Stage1Output
from app.pipeline.prompts import STAGE1_RETRY, STAGE1_SYSTEM, STAGE1_USER
from app.providers.registry import llm_complete_json_with_fallback

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_stage1_parse(raw_text: str) -> tuple[Stage1Output, str]:
    user = STAGE1_USER.format(raw_ingredient_text=raw_text)
    model = settings.model_stage1 if settings.pipeline_phase == "local" else settings.model_stage1

    data, provider_name = await llm_complete_json_with_fallback(
        primary=settings.provider_llm,
        fallback_chain=settings.provider_llm_fallback,
        system=STAGE1_SYSTEM,
        user=user,
        temperature=0.0,
        max_tokens=800,
        model=model,
    )

    try:
        output = Stage1Output.model_validate(data)
    except Exception:
        data, provider_name = await llm_complete_json_with_fallback(
            primary=settings.provider_llm,
            fallback_chain=settings.provider_llm_fallback,
            system=STAGE1_SYSTEM,
            user=user + "\n\n" + STAGE1_RETRY,
            temperature=0.0,
            max_tokens=800,
            model=model,
        )
        output = Stage1Output.model_validate(data)

    return output, provider_name
