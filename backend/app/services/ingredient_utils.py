"""Helpers for ingredient list/detail API responses."""

from app.models.pipeline import EnrichedIngredient, IngredientType, RiskTier, TierCounts


def infer_ingredient_type(label_name: str, e_code: str | None) -> IngredientType:
    if e_code:
        return IngredientType.E_NUMBER
    natural_keywords = {
        "oat",
        "wheat",
        "flour",
        "grain",
        "milk",
        "water",
        "salt",
        "sugar",
        "oil",
        "honey",
        "fruit",
        "vegetable",
        "whole",
        "natural",
        "rice",
        "corn",
        "butter",
        "egg",
        "cream",
        "cocoa",
        "vanilla",
        "spice",
        "herb",
        "seed",
        "nut",
    }
    label = label_name.lower()
    if any(kw in label for kw in natural_keywords):
        return IngredientType.NATURAL
    if any(kw in label for kw in ("extract", "flavour", "flavor", "colour", "color", "acid")):
        return IngredientType.ADDITIVE
    return IngredientType.UNKNOWN


def compute_tier_counts(ingredients: list[EnrichedIngredient | dict]) -> TierCounts:
    counts = {"concern": 0, "caution": 0, "safe": 0, "unknown": 0}
    for ing in ingredients:
        tier = ing.risk_tier if isinstance(ing, EnrichedIngredient) else ing.get("risk_tier", "unknown")
        if isinstance(tier, RiskTier):
            tier = tier.value
        tier = str(tier).lower()
        if tier in counts:
            counts[tier] += 1
        else:
            counts["unknown"] += 1
    total = sum(counts.values())
    return TierCounts(
        total=total,
        concern=counts["concern"],
        caution=counts["caution"],
        safe=counts["safe"],
        unknown=counts["unknown"],
    )


RISK_LABELS = {
    RiskTier.CONCERN: "High Risk",
    RiskTier.CAUTION: "Caution",
    RiskTier.SAFE: "Safe",
    RiskTier.UNKNOWN: "Unknown",
}
