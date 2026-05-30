from app.models.pipeline import EnrichedIngredient, ProfileAlert


def match_profile_alerts_from_report(
    ingredients: list[EnrichedIngredient],
    profile_alerts: list[ProfileAlert],
) -> list[dict]:
    return [a.model_dump() for a in profile_alerts]


def count_active_alerts(reports: list[dict]) -> int:
    total = 0
    for report in reports:
        total += len(report.get("profile_alerts") or [])
    return total
