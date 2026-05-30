from app.models.pipeline import ParsedIngredient, RiskTier, Stage1Output
from app.pipeline.utils import chunk_list, normalize_ingredient_text


def test_chunk_list():
    items = list(range(20))
    chunks = chunk_list(items, 15)
    assert len(chunks) == 2
    assert len(chunks[0]) == 15
    assert len(chunks[1]) == 5


def test_normalize_ingredient_text():
    assert normalize_ingredient_text("  Water,  Salt  ") == "water, salt"


def test_stage1_output_validation():
    output = Stage1Output(
        ingredients=[
            ParsedIngredient(id=1, label_name="water"),
            ParsedIngredient(id=2, label_name="salt", e_code="E500"),
        ]
    )
    assert len(output.ingredients) == 2
