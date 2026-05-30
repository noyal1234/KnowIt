import json
import logging

from app.config import get_settings
from app.models.pipeline import (
    Citation,
    EnrichedIngredient,
    RiskItem,
    RiskTier,
    Stage3Output,
)
from app.pipeline.prompts import STAGE3_SYSTEM, STAGE3_USER
from app.pipeline.utils import compute_base_score, normalize_ingredient_text, report_cache_key, score_to_grade
from app.providers.registry import get_llm_provider, llm_complete_json_with_fallback, search_with_fallback
from app.services.cache import cache_get, cache_set
from app.services.scoring import apply_profile_scoring

logger = logging.getLogger(__name__)
settings = get_settings()

REPORT_TTL = 7 * 24 * 3600  # 7 days


def _flagged(ingredients: list[EnrichedIngredient]) -> list[EnrichedIngredient]:
    return [
        i
        for i in ingredients
        if i.risk_tier in (RiskTier.CAUTION, RiskTier.CONCERN, RiskTier.UNKNOWN)
    ]


async def run_stage3_report(
    enriched: list[EnrichedIngredient],
    *,
    product_hint: str,
    region: str,
    profile: dict,
) -> tuple[Stage3Output, str, str | None]:
    full_str = normalize_ingredient_text(
        ",".join(i.label_name for i in enriched)
    )
    cache_key = report_cache_key(full_str)
    cached = await cache_get(cache_key)
    if cached:
        return Stage3Output.model_validate(cached), "cache", None

    flagged = _flagged(enriched)
    if not flagged:
        risk_counts = {tier: 0 for tier in RiskTier}
        for ing in enriched:
            risk_counts[ing.risk_tier] = risk_counts.get(ing.risk_tier, 0) + 1
        base_score = compute_base_score(risk_counts)
        score, grade, profile_alerts, recs = apply_profile_scoring(
            enriched,
            allergens=profile.get("allergens", []),
            avoid_additives=profile.get("avoid_additives", []),
            dietary_preferences=profile.get("dietary_preferences", []),
            base_score=base_score,
        )
        output = Stage3Output(
            health_score=score,
            grade=grade,
            summary="All identified ingredients are within acceptable regulatory tiers.",
            recommendations=recs or ["No significant concerns identified."],
            profile_alerts=profile_alerts,
        )
        await cache_set(cache_key, output.model_dump(), REPORT_TTL)
        return output, "short_circuit", None

    risk_counts = {tier: 0 for tier in RiskTier}
    for ing in enriched:
        risk_counts[ing.risk_tier] = risk_counts.get(ing.risk_tier, 0) + 1
    base_score = compute_base_score(risk_counts)
    grade = score_to_grade(base_score)

    search_results = []
    search_provider = None
    max_searches = len(flagged) * 2
    for ing in flagged[:max_searches]:
        query = f"{ing.label_name} {ing.e_code or ''} food additive safety {region} FDA EFSA"
        results, search_provider = await search_with_fallback(
            query, domains=settings.search_domains, max_results=2
        )
        search_results.extend(results)

    search_text = "\n\n".join(
        f"Title: {r.title}\nURL: {r.url}\n{r.snippet}" for r in search_results
    )

    enriched_json = json.dumps([i.model_dump() for i in enriched], default=str)
    user = STAGE3_USER.format(
        stage2_enriched_json=enriched_json,
        product_hint=product_hint or "Unknown product",
        health_score=base_score,
        grade=grade,
        search_results=search_text or "No search results available.",
    )

    model = settings.model_stage3
    if settings.pipeline_phase == "local":
        try:
            provider = get_llm_provider("ollama")
            data = await provider.complete_json(
                system=STAGE3_SYSTEM,
                user=user,
                temperature=0.2,
                max_tokens=2000,
                model="meditron:8b",
            )
            llm_provider = "meditron:8b"
        except Exception:
            data, llm_provider = await llm_complete_json_with_fallback(
                primary=settings.provider_llm,
                fallback_chain=settings.provider_llm_fallback,
                system=STAGE3_SYSTEM,
                user=user,
                temperature=0.2,
                max_tokens=2000,
                model=model,
            )
    else:
        data, llm_provider = await llm_complete_json_with_fallback(
            primary=settings.provider_llm,
            fallback_chain=settings.provider_llm_fallback,
            system=STAGE3_SYSTEM,
            user=user,
            temperature=0.2,
            max_tokens=2000,
            model=model,
        )

    citations = [Citation.model_validate(c) for c in data.get("citations", [])]
    if not citations and search_results:
        citations = [
            Citation(title=r.title, url=r.url, snippet=r.snippet) for r in search_results[:5]
        ]

    risks = [RiskItem.model_validate(r) for r in data.get("risks", [])]
    if not risks:
        risks = [
            RiskItem(
                ingredient=i.label_name,
                tier=i.risk_tier,
                reason=i.regulatory_status or f"Classified as {i.risk_tier.value}",
            )
            for i in flagged
        ]

    score, grade, profile_alerts, profile_recs = apply_profile_scoring(
        enriched,
        allergens=profile.get("allergens", []),
        avoid_additives=profile.get("avoid_additives", []),
        dietary_preferences=profile.get("dietary_preferences", []),
        base_score=base_score,
    )

    recommendations = list(data.get("recommendations", [])) + profile_recs

    output = Stage3Output(
        health_score=score,
        grade=grade,
        citations=citations,
        summary=data.get("summary", ""),
        recommendations=recommendations,
        risks=risks,
        profile_alerts=profile_alerts,
    )
    await cache_set(cache_key, output.model_dump(), REPORT_TTL)
    return output, llm_provider, search_provider
