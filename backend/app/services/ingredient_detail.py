"""Build full ingredient detail for IngredientIQ detail screen."""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IngredientWatchlist, Scan, ScanReport
from app.models.pipeline import (
    EnrichedIngredient,
    ExposureEstimate,
    IngredientAction,
    IngredientStudy,
    IngredientType,
    RiskTier,
)
from app.services.ingredient_utils import RISK_LABELS, infer_ingredient_type
from app.services.regulatory import lookup_additive_full


def _parse_ingredient(raw: dict[str, Any]) -> EnrichedIngredient:
    tier = raw.get("risk_tier", "unknown")
    if isinstance(tier, str):
        tier = RiskTier(tier)
    ing_type = raw.get("ingredient_type", "unknown")
    if isinstance(ing_type, str):
        ing_type = IngredientType(ing_type)
    return EnrichedIngredient.model_validate({**raw, "risk_tier": tier, "ingredient_type": ing_type})


def _find_ingredient(ingredients: list[dict], ingredient_id: int) -> dict | None:
    for ing in ingredients:
        if ing.get("id") == ingredient_id:
            return ing
    return None


def _filter_citations_for_ingredient(citations: list[dict], label: str, e_code: str | None) -> list[IngredientStudy]:
    terms = [label.lower()]
    if e_code:
        terms.append(e_code.lower())
    studies: list[IngredientStudy] = []
    for i, cite in enumerate(citations):
        hay = f"{cite.get('title', '')} {cite.get('snippet', '')}".lower()
        if not any(t in hay for t in terms):
            continue
        severity = "inconclusive"
        snippet = cite.get("snippet", "")
        if any(w in snippet.lower() for w in ("adverse", "risk", "concern", "harm")):
            severity = "adverse"
        elif any(w in snippet.lower() for w in ("safe", "no adverse", "gras")):
            severity = "safe"
        year_match = re.search(r"(20\d{2}|19\d{2})", cite.get("title", "") + snippet)
        studies.append(
            IngredientStudy(
                title=cite.get("title") or f"Study {i + 1}",
                authors="See source",
                journal="PubMed / Regulatory source",
                year=int(year_match.group(1)) if year_match else None,
                finding=snippet[:280] if snippet else cite.get("title", ""),
                severity=severity,
                url=cite.get("url"),
            )
        )
    return studies[:5]


def _build_actions(ingredient: EnrichedIngredient, risk_reason: str | None) -> list[IngredientAction]:
    actions: list[IngredientAction] = []
    if ingredient.risk_tier in (RiskTier.CONCERN, RiskTier.CAUTION):
        desc = risk_reason or f"Monitor intake of {ingredient.label_name}."
        if ingredient.e_code:
            desc += f" Check labels for {ingredient.e_code}."
        actions.append(IngredientAction(type="limit", title="Limit intake", description=desc))
    if ingredient.risk_tier == RiskTier.SAFE and ingredient.function:
        actions.append(
            IngredientAction(
                type="alternative",
                title="Generally recognised",
                description=f"{ingredient.label_name} is commonly used as a {ingredient.function.lower()}.",
            )
        )
    elif ingredient.risk_tier in (RiskTier.CONCERN, RiskTier.CAUTION):
        actions.append(
            IngredientAction(
                type="alternative",
                title="Safe alternatives",
                description="Choose products with fewer artificial additives or look for clean-label alternatives.",
            )
        )
    return actions


def _build_exposure(adi: float | None, tier: RiskTier) -> ExposureEstimate | None:
    if adi is None:
        return None
    exceeds = 30 if tier == RiskTier.CONCERN else 15 if tier == RiskTier.CAUTION else 5
    return ExposureEstimate(
        adi_mg_per_kg=adi,
        product_contribution_pct=35,
        typical_diet_contribution_pct=max(20, 70 - exceeds),
        exceeds_adi_pct=exceeds,
    )


def _default_at_risk_groups(tier: RiskTier, e_code: str | None) -> list[str]:
    groups: list[str] = []
    if tier in (RiskTier.CONCERN, RiskTier.CAUTION):
        groups.extend(["Children under 12", "Pregnant women"])
    if e_code:
        groups.append("Multiple additive sensitivity")
    return groups


async def build_ingredient_detail(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    scan_id: uuid.UUID,
    ingredient_id: int,
) -> dict[str, Any]:
    stmt = (
        select(Scan, ScanReport)
        .join(ScanReport, ScanReport.scan_id == Scan.id)
        .where(Scan.id == scan_id, Scan.user_id == user_id)
    )
    row = (await session.execute(stmt)).one_or_none()
    if not row:
        return None  # type: ignore[return-value]

    scan, report = row
    raw = _find_ingredient(report.ingredients or [], ingredient_id)
    if not raw:
        return None  # type: ignore[return-value]

    ingredient = _parse_ingredient(raw)

    # Enrich from regulatory DB if sparse
    if not ingredient.regulatory_by_region:
        db_hit = await lookup_additive_full(
            session,
            label_name=ingredient.label_name,
            e_code=ingredient.e_code,
            region="US",
            ingredient_id=ingredient.id,
        )
        if db_hit:
            ingredient = ingredient.model_copy(
                update={
                    "chemical_name": ingredient.chemical_name or db_hit.chemical_name,
                    "iupac_name": ingredient.iupac_name or db_hit.iupac_name,
                    "function": ingredient.function or db_hit.function,
                    "regulatory_by_region": db_hit.regulatory_by_region,
                    "banned_in": db_hit.banned_in or ingredient.banned_in,
                    "adi_mg_per_kg": ingredient.adi_mg_per_kg or db_hit.adi_mg_per_kg,
                    "at_risk_groups": ingredient.at_risk_groups or db_hit.at_risk_groups,
                    "function_descriptions": ingredient.function_descriptions or db_hit.function_descriptions,
                }
            )

    if not ingredient.function:
        ingredient = ingredient.model_copy(
            update={"ingredient_type": infer_ingredient_type(ingredient.label_name, ingredient.e_code)}
        )

    risk_reason = None
    for risk in report.risks or []:
        if risk.get("ingredient", "").lower() == ingredient.label_name.lower():
            risk_reason = risk.get("reason")
            break

    studies = ingredient.studies or _filter_citations_for_ingredient(
        report.citations or [], ingredient.label_name, ingredient.e_code
    )
    actions = ingredient.actions or _build_actions(ingredient, risk_reason)
    at_risk = ingredient.at_risk_groups or _default_at_risk_groups(ingredient.risk_tier, ingredient.e_code)
    exposure = ingredient.exposure or _build_exposure(ingredient.adi_mg_per_kg, ingredient.risk_tier)

    if not ingredient.risk_label:
        ingredient = ingredient.model_copy(
            update={"risk_label": RISK_LABELS.get(ingredient.risk_tier, "Unknown")}
        )

    # Navigation prev/next within scan ingredient list (ordered by id)
    sorted_ids = sorted(i.get("id", 0) for i in (report.ingredients or []))
    idx = sorted_ids.index(ingredient_id) if ingredient_id in sorted_ids else 0
    prev_id = sorted_ids[idx - 1] if idx > 0 else None
    next_id = sorted_ids[idx + 1] if idx < len(sorted_ids) - 1 else None

    def _nav_item(iid: int | None) -> dict | None:
        if iid is None:
            return None
        ing = _find_ingredient(report.ingredients or [], iid)
        return {"id": iid, "label_name": ing.get("label_name") if ing else None}

    watch_stmt = select(IngredientWatchlist).where(
        IngredientWatchlist.user_id == user_id,
        IngredientWatchlist.normalized_key == _watch_key(ingredient.label_name, ingredient.e_code),
    )
    is_bookmarked = (await session.execute(watch_stmt)).scalar_one_or_none() is not None

    detail = ingredient.model_copy(
        update={
            "studies": studies,
            "actions": actions,
            "at_risk_groups": at_risk,
            "exposure": exposure,
        }
    )

    return {
        "scan_id": scan_id,
        "ingredient": detail.model_dump(),
        "navigation": {"prev": _nav_item(prev_id), "next": _nav_item(next_id)},
        "is_bookmarked": is_bookmarked,
        "studies_total": len(studies),
        "studies_more_count": max(0, len(report.citations or []) - len(studies)),
    }


def _watch_key(label_name: str, e_code: str | None) -> str:
    return (e_code or label_name).strip().lower()
