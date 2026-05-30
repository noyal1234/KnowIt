from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IngredientType(str, Enum):
    ADDITIVE = "additive"
    NATURAL = "natural"
    E_NUMBER = "e_number"
    UNKNOWN = "unknown"


class RiskTier(str, Enum):
    SAFE = "safe"
    CAUTION = "caution"
    CONCERN = "concern"
    UNKNOWN = "unknown"


class ParsedIngredient(BaseModel):
    id: int
    label_name: str
    e_code: str | None = None
    parent_id: int | None = None


class Stage1Output(BaseModel):
    ingredients: list[ParsedIngredient]


class RegionalStatus(BaseModel):
    region: str
    region_label: str
    status: str
    badge: str  # approved | caution | banned | unknown


class IngredientStudy(BaseModel):
    title: str
    authors: str | None = None
    journal: str | None = None
    year: int | None = None
    finding: str
    severity: str  # adverse | inconclusive | safe
    url: str | None = None


class IngredientAction(BaseModel):
    type: str  # limit | alternative
    title: str
    description: str


class ExposureEstimate(BaseModel):
    adi_mg_per_kg: float | None = None
    product_contribution_pct: int = 35
    typical_diet_contribution_pct: int = 35
    exceeds_adi_pct: int = 30
    footnote: str = "Based on 50kg adult consuming 2 servings/day"


class EnrichedIngredient(BaseModel):
    id: int
    label_name: str
    e_code: str | None = None
    chemical_name: str | None = None
    iupac_name: str | None = None
    function: str | None = None
    ingredient_type: IngredientType = IngredientType.UNKNOWN
    regulatory_status: str | None = None
    regulatory_by_region: list[RegionalStatus] = Field(default_factory=list)
    banned_in: list[str] = Field(default_factory=list)
    adi_mg_per_kg: float | None = None
    risk_tier: RiskTier = RiskTier.UNKNOWN
    risk_label: str = "Unknown"
    sources: list[str] = Field(default_factory=list)
    at_risk_groups: list[str] = Field(default_factory=list)
    function_descriptions: list[str] = Field(default_factory=list)
    studies: list[IngredientStudy] = Field(default_factory=list)
    actions: list[IngredientAction] = Field(default_factory=list)
    exposure: ExposureEstimate | None = None


class Stage2Output(BaseModel):
    ingredients: list[EnrichedIngredient]


class Citation(BaseModel):
    title: str
    url: str
    snippet: str


class RiskItem(BaseModel):
    ingredient: str
    tier: RiskTier
    reason: str


class ProfileAlert(BaseModel):
    type: str
    ingredient: str
    severity: str
    message: str


class TierCounts(BaseModel):
    total: int
    concern: int
    caution: int
    safe: int
    unknown: int


class Stage3Output(BaseModel):
    health_score: int
    grade: str
    citations: list[Citation] = Field(default_factory=list)
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
    profile_alerts: list[ProfileAlert] = Field(default_factory=list)


class ProviderMeta(BaseModel):
    ocr_cleanup: str | None = None
    ocr: str | None = None
    llm_s1: str | None = None
    llm_s2: str | None = None
    llm_s2_assist: str | None = None
    llm_s3: str | None = None
    search: str | None = None
    barcode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.model_dump().items() if v is not None}
