from app.models.pipeline import EnrichedIngredient, RiskTier
from app.services.ingredient_utils import compute_tier_counts, infer_ingredient_type


def test_tier_counts():
    ingredients = [
        EnrichedIngredient(id=1, label_name="A", risk_tier=RiskTier.CONCERN),
        EnrichedIngredient(id=2, label_name="B", risk_tier=RiskTier.CAUTION),
        EnrichedIngredient(id=3, label_name="C", risk_tier=RiskTier.SAFE),
        EnrichedIngredient(id=4, label_name="D", risk_tier=RiskTier.SAFE),
    ]
    counts = compute_tier_counts(ingredients)
    assert counts.total == 4
    assert counts.concern == 1
    assert counts.caution == 1
    assert counts.safe == 2


def test_infer_ingredient_type_e_number():
    assert infer_ingredient_type("Tartrazine", "E102").value == "e_number"


def test_infer_ingredient_type_natural():
    assert infer_ingredient_type("Whole Grain Oats", None).value == "natural"
