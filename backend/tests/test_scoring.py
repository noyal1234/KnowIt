import pytest

from app.models.pipeline import EnrichedIngredient, RiskTier
from app.pipeline.utils import compute_base_score, parse_json_from_llm, score_to_grade, sha256_key
from app.services.scoring import apply_profile_scoring


def test_compute_base_score():
    counts = {RiskTier.CONCERN: 1, RiskTier.CAUTION: 2, RiskTier.UNKNOWN: 1, RiskTier.SAFE: 5}
    assert compute_base_score(counts) == 100 - 12 - 10 - 3


def test_score_to_grade():
    assert score_to_grade(95) == "A"
    assert score_to_grade(85) == "B"
    assert score_to_grade(55) == "F"


def test_parse_json_from_llm_with_fence():
    raw = '```json\n{"ingredients": [{"id": 1, "label_name": "water", "e_code": null, "parent_id": null}]}\n```'
    data = parse_json_from_llm(raw)
    assert data["ingredients"][0]["label_name"] == "water"


def test_sha256_key_deterministic():
    assert sha256_key("Salt", "E500") == sha256_key("salt", "e500")


def test_profile_allergen_caps_score():
    ingredients = [
        EnrichedIngredient(id=1, label_name="peanut oil", risk_tier=RiskTier.SAFE),
    ]
    score, grade, alerts, _ = apply_profile_scoring(
        ingredients,
        allergens=["peanut"],
        avoid_additives=[],
        dietary_preferences=[],
    )
    assert score <= 40
    assert any(a.severity == "critical" for a in alerts)


def test_avoid_additive_penalty():
    ingredients = [
        EnrichedIngredient(id=1, label_name="Tartrazine", e_code="E102", risk_tier=RiskTier.CAUTION),
    ]
    score, _, alerts, _ = apply_profile_scoring(
        ingredients,
        allergens=[],
        avoid_additives=["E102"],
        dietary_preferences=[],
        base_score=80,
    )
    assert score == 65
    assert len(alerts) == 1
