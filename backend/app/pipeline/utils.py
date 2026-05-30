import hashlib
import json
import re
from typing import Any

from app.models.pipeline import RiskTier


def sha256_key(*parts: str) -> str:
    payload = "|".join(p.strip().lower() for p in parts if p)
    return hashlib.sha256(payload.encode()).hexdigest()


def enrich_cache_key(label: str, e_code: str | None) -> str:
    return f"enrich:{sha256_key(label, e_code or '')}"


def report_cache_key(full_ingredient_str: str) -> str:
    return f"report:{sha256_key(full_ingredient_str)}"


def normalize_ingredient_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def chunk_list(items: list[Any], size: int) -> list[list[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def parse_json_from_llm(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(text[start : end + 1])


def score_to_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def compute_base_score(risk_counts: dict[RiskTier, int]) -> int:
    score = 100
    score -= risk_counts.get(RiskTier.CONCERN, 0) * 12
    score -= risk_counts.get(RiskTier.CAUTION, 0) * 5
    score -= risk_counts.get(RiskTier.UNKNOWN, 0) * 3
    return max(0, min(100, score))
