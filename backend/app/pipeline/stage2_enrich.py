import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.pipeline import EnrichedIngredient, ParsedIngredient, RiskTier, Stage2Output
from app.pipeline.prompts import FOODYLLM_NER_USER, STAGE2_SYSTEM, STAGE2_USER
from app.pipeline.utils import chunk_list, enrich_cache_key
from app.providers.registry import get_llm_provider, llm_complete_json_with_fallback
from app.services.cache import cache_get, cache_set
from app.services.ingredient_enrich import finalize_ingredient, merge_llm_ingredient
from app.services.regulatory import lookup_additive

logger = logging.getLogger(__name__)
settings = get_settings()

ENRICH_TTL = 30 * 24 * 3600  # 30 days
CHUNK_SIZE = 15


async def _foodyllm_assist(ingredient_names: list[str]) -> dict[str, str]:
    if not settings.model_stage2_assist or settings.pipeline_phase == "build":
        return {}
    try:
        provider = get_llm_provider(settings.provider_llm_stage2_assist)
        text = await provider.complete_text(
            system="Extract and normalize food entity names.",
            user=FOODYLLM_NER_USER.format(ingredients=", ".join(ingredient_names)),
            temperature=0.1,
            max_tokens=500,
            model=settings.model_stage2_assist,
        )
        logger.debug("FoodyLLM assist output: %s", text[:200])
        return {}
    except Exception as exc:
        logger.warning("FoodyLLM assist failed: %s", exc)
        return {}


async def run_stage2_enrich(
    session: AsyncSession,
    parsed: list[ParsedIngredient],
    *,
    region: str,
) -> tuple[Stage2Output, str, str | None]:
    enriched: list[EnrichedIngredient] = []
    llm_provider_used = "regulatory_db"
    assist_provider: str | None = None
    unknown_for_llm: list[ParsedIngredient] = []

    for item in parsed:
        cache_key = enrich_cache_key(item.label_name, item.e_code)
        cached = await cache_get(cache_key)
        if cached:
            ing = finalize_ingredient(EnrichedIngredient.model_validate({**cached, "id": item.id}))
            enriched.append(ing)
            continue

        db_hit = await lookup_additive(
            session,
            label_name=item.label_name,
            e_code=item.e_code,
            region=region,
            ingredient_id=item.id,
        )
        if db_hit:
            enriched.append(finalize_ingredient(db_hit))
            await cache_set(cache_key, db_hit.model_dump(), ENRICH_TTL)
            continue

        unknown_for_llm.append(item)

    if unknown_for_llm:
        await _foodyllm_assist([i.label_name for i in unknown_for_llm])
        assist_provider = settings.provider_llm_stage2_assist if settings.pipeline_phase == "local" else None

        for chunk in chunk_list(unknown_for_llm, CHUNK_SIZE):
            chunk_json = json.dumps([c.model_dump() for c in chunk])
            data, provider_name = await llm_complete_json_with_fallback(
                primary=settings.provider_llm,
                fallback_chain=settings.provider_llm_fallback,
                system=STAGE2_SYSTEM,
                user=STAGE2_USER.format(region=region, stage1_ingredients_json=chunk_json),
                temperature=0.1,
                max_tokens=2500,
                model=settings.model_stage2,
            )
            llm_provider_used = provider_name
            llm_ings = data.get("ingredients", [])
            for i, item in enumerate(chunk):
                llm_row = llm_ings[i] if i < len(llm_ings) else {}
                base = EnrichedIngredient(id=item.id, label_name=item.label_name, e_code=item.e_code)
                ing = merge_llm_ingredient(base, llm_row)
                enriched.append(ing)
                cache_key = enrich_cache_key(ing.label_name, ing.e_code)
                await cache_set(cache_key, ing.model_dump(), ENRICH_TTL)

    enriched.sort(key=lambda x: x.id)
    return Stage2Output(ingredients=enriched), llm_provider_used, assist_provider
