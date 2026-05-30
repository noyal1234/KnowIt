from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RegulatoryAdditive
from app.models.pipeline import EnrichedIngredient, IngredientType, RegionalStatus, RiskTier
from app.services.ingredient_utils import RISK_LABELS, infer_ingredient_type


def _normalize(s: str) -> str:
    return s.strip().lower()


def _status_badge(status: str | None) -> str:
    if not status:
        return "unknown"
    lower = status.lower()
    if any(w in lower for w in ("ban", "prohibit", "restricted")):
        return "banned"
    if any(w in lower for w in ("review", "warning", "adi set", "caution", "limit")):
        return "caution"
    if any(w in lower for w in ("approv", "gras", "permit", "safe")):
        return "approved"
    return "unknown"


def _build_regional_statuses(row: RegulatoryAdditive) -> list[RegionalStatus]:
    return [
        RegionalStatus(
            region="EU",
            region_label="European Union",
            status=row.eu_status or "Unknown",
            badge=_status_badge(row.eu_status),
        ),
        RegionalStatus(
            region="US",
            region_label="United States FDA",
            status=row.fda_status or "Unknown",
            badge=_status_badge(row.fda_status),
        ),
        RegionalStatus(
            region="IN",
            region_label="FSSAI (India)",
            status=row.fssai_status or "Unknown",
            badge=_status_badge(row.fssai_status),
        ),
        RegionalStatus(
            region="WHO",
            region_label="WHO / JECFA",
            status=row.who_jecfa_status or "Unknown",
            badge=_status_badge(row.who_jecfa_status),
        ),
    ]


def _row_to_enriched(
    row: RegulatoryAdditive,
    *,
    label_name: str,
    e_code: str | None,
    ingredient_id: int,
    region: str,
) -> EnrichedIngredient:
    if region == "EU":
        status = row.eu_status
    elif region == "IN":
        status = row.fssai_status
    else:
        status = row.fda_status

    tier = RiskTier(row.default_risk_tier)
    ing_type = infer_ingredient_type(label_name, row.e_code or e_code)
    function = row.function
    descriptions = []
    if function:
        descriptions.append(f"Functions as a {function.lower()} in processed foods.")

    return EnrichedIngredient(
        id=ingredient_id,
        label_name=label_name,
        e_code=row.e_code or e_code,
        chemical_name=row.canonical_name,
        iupac_name=row.iupac_name,
        function=row.function,
        ingredient_type=ing_type,
        regulatory_status=status,
        regulatory_by_region=_build_regional_statuses(row),
        banned_in=list(row.banned_in or []),
        adi_mg_per_kg=row.adi_mg_per_kg,
        risk_tier=tier,
        risk_label=RISK_LABELS.get(tier, "Unknown"),
        sources=[row.source_url] if row.source_url else [],
        at_risk_groups=list(row.at_risk_groups or []),
        function_descriptions=descriptions,
    )


async def _fetch_row(
    session: AsyncSession,
    *,
    label_name: str,
    e_code: str | None,
) -> RegulatoryAdditive | None:
    label_norm = _normalize(label_name)
    e_norm = _normalize(e_code) if e_code else None
    conditions = [func.lower(RegulatoryAdditive.canonical_name) == label_norm]
    if e_norm:
        conditions.append(func.lower(RegulatoryAdditive.e_code) == e_norm)
    stmt = select(RegulatoryAdditive).where(or_(*conditions)).limit(1)
    return (await session.execute(stmt)).scalar_one_or_none()


async def lookup_additive(
    session: AsyncSession,
    *,
    label_name: str,
    e_code: str | None,
    region: str,
    ingredient_id: int = 0,
) -> EnrichedIngredient | None:
    row = await _fetch_row(session, label_name=label_name, e_code=e_code)
    if not row:
        return None
    return _row_to_enriched(
        row, label_name=label_name, e_code=e_code, ingredient_id=ingredient_id, region=region
    )


async def lookup_additive_full(
    session: AsyncSession,
    *,
    label_name: str,
    e_code: str | None,
    region: str,
    ingredient_id: int = 0,
) -> EnrichedIngredient | None:
    return await lookup_additive(
        session,
        label_name=label_name,
        e_code=e_code,
        region=region,
        ingredient_id=ingredient_id,
    )
