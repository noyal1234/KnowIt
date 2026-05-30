"""Finalize enriched ingredient fields for iOS list/detail UI."""

from app.models.pipeline import EnrichedIngredient, IngredientType, RiskTier
from app.services.ingredient_utils import RISK_LABELS, infer_ingredient_type


def finalize_ingredient(ing: EnrichedIngredient) -> EnrichedIngredient:
    tier = ing.risk_tier if isinstance(ing.risk_tier, RiskTier) else RiskTier(str(ing.risk_tier))
    ing_type = ing.ingredient_type
    if ing_type == IngredientType.UNKNOWN or not ing.function:
        ing_type = infer_ingredient_type(ing.label_name, ing.e_code)

    function = ing.function
    descriptions = list(ing.function_descriptions)
    if function and not descriptions:
        descriptions = [f"Functions as a {function.lower()} in processed foods."]

    return ing.model_copy(
        update={
            "risk_tier": tier,
            "risk_label": RISK_LABELS.get(tier, "Unknown"),
            "ingredient_type": ing_type,
            "function_descriptions": descriptions,
        }
    )


def merge_llm_ingredient(base: EnrichedIngredient, llm_data: dict) -> EnrichedIngredient:
    tier_raw = llm_data.get("risk_tier", base.risk_tier)
    tier = RiskTier(tier_raw) if isinstance(tier_raw, str) else tier_raw
    ing_type_raw = llm_data.get("ingredient_type")
    ing_type = IngredientType(ing_type_raw) if ing_type_raw else base.ingredient_type

    merged = base.model_copy(
        update={
            "chemical_name": llm_data.get("chemical_name") or base.chemical_name,
            "iupac_name": llm_data.get("iupac_name") or base.iupac_name,
            "function": llm_data.get("function") or base.function,
            "ingredient_type": ing_type,
            "regulatory_status": llm_data.get("regulatory_status") or base.regulatory_status,
            "adi_mg_per_kg": llm_data.get("adi_mg_per_kg") if llm_data.get("adi_mg_per_kg") is not None else base.adi_mg_per_kg,
            "risk_tier": tier,
            "sources": llm_data.get("sources") or base.sources,
            "at_risk_groups": llm_data.get("at_risk_groups") or base.at_risk_groups,
            "banned_in": llm_data.get("banned_in") or base.banned_in,
        }
    )
    return finalize_ingredient(merged)
