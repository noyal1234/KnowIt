from app.models.pipeline import EnrichedIngredient, ProfileAlert, RiskTier
from app.pipeline.utils import compute_base_score, score_to_grade


NON_VEGAN_KEYWORDS = {
    "gelatin",
    "lard",
    "beef",
    "pork",
    "chicken",
    "fish",
    "shellfish",
    "milk",
    "whey",
    "casein",
    "egg",
    "honey",
}


def apply_profile_scoring(
    ingredients: list[EnrichedIngredient],
    *,
    allergens: list[str],
    avoid_additives: list[str],
    dietary_preferences: list[str],
    base_score: int | None = None,
) -> tuple[int, str, list[ProfileAlert], list[str]]:
    risk_counts = {tier: 0 for tier in RiskTier}
    for ing in ingredients:
        risk_counts[ing.risk_tier] = risk_counts.get(ing.risk_tier, 0) + 1

    score = base_score if base_score is not None else compute_base_score(risk_counts)
    alerts: list[ProfileAlert] = []
    recommendations: list[str] = []

    allergen_set = {a.lower() for a in allergens}
    avoid_set = {a.lower() for a in avoid_additives}
    prefs = {p.lower() for p in dietary_preferences}

    for ing in ingredients:
        label = ing.label_name.lower()
        e_code = (ing.e_code or "").lower()

        for allergen in allergen_set:
            if allergen in label or allergen in (ing.chemical_name or "").lower():
                alerts.append(
                    ProfileAlert(
                        type="allergen",
                        ingredient=ing.label_name,
                        severity="critical",
                        message=f"Contains allergen: {allergen}",
                    )
                )

        for blocked in avoid_set:
            if blocked in label or blocked == e_code:
                score -= 15
                alerts.append(
                    ProfileAlert(
                        type="avoid_additive",
                        ingredient=ing.label_name,
                        severity="high",
                        message=f"Contains blocked additive: {blocked}",
                    )
                )

        if "vegan" in prefs:
            if any(kw in label for kw in NON_VEGAN_KEYWORDS):
                alerts.append(
                    ProfileAlert(
                        type="dietary",
                        ingredient=ing.label_name,
                        severity="caution",
                        message="May not be compatible with vegan diet",
                    )
                )
                recommendations.append(
                    f"Review {ing.label_name} — may conflict with vegan preference"
                )

    if any(a.severity == "critical" for a in alerts):
        score = min(score, 40)

    score = max(0, min(100, score))
    grade = score_to_grade(score)
    return score, grade, alerts, recommendations
