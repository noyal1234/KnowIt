from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: UUID
    email: str
    display_name: str
    region: str
    dietary_preferences: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    avoid_additives: list[str] = Field(default_factory=list)
    notification_enabled: bool = True
    health_goal: str | None = None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


# --- Profile ---


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    region: Literal["US", "EU", "IN"] | None = None
    dietary_preferences: list[str] | None = None
    allergens: list[str] | None = None
    avoid_additives: list[str] | None = None
    notification_enabled: bool | None = None
    health_goal: Literal["general", "clean_eating", "allergen_safe"] | None = None


# --- Scan ---


class ScanRequest(BaseModel):
    barcode: str | None = None
    ingredient_text: str | None = None
    image_base64: str | None = None
    storage_path: str | None = None
    product_hint: str | None = None
    region: Literal["US", "EU", "IN"] | None = None


class ProductBrief(BaseModel):
    id: UUID
    name: str
    barcode: str | None = None
    brand: str | None = None


class ScanResponse(BaseModel):
    scan_id: UUID
    product: ProductBrief
    ingredients: list[dict[str, Any]]
    tier_counts: dict[str, int]
    health_score: int
    grade: str
    risks: list[dict[str, Any]]
    profile_alerts: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    summary: str
    recommendations: list[str]
    provider_meta: dict[str, Any]
    disclaimer: str


# --- Dashboard ---


class RecentProduct(BaseModel):
    id: UUID
    name: str
    score: int
    grade: str


class DashboardSummary(BaseModel):
    total_scans: int
    avg_health_score: float
    avg_score_last_7d: float | None
    score_change_vs_prev_7d: float | None
    grade_distribution: dict[str, int]
    active_alerts_count: int
    favorites_count: int
    last_scan_at: datetime | None
    recent_products: list[RecentProduct]


class TrendPoint(BaseModel):
    date: str
    avg_score: float
    scan_count: int


class DashboardTrends(BaseModel):
    period: str
    data_points: list[TrendPoint]
    top_improved: list[RecentProduct] = Field(default_factory=list)
    top_declined: list[RecentProduct] = Field(default_factory=list)


class TopConcernIngredient(BaseModel):
    ingredient: str
    count: int
    tier: str


# --- Products ---


class ProductListItem(BaseModel):
    id: UUID
    name: str
    brand: str | None
    barcode: str | None
    latest_score: int | None
    latest_grade: str | None
    is_favorite: bool = False
    last_scanned_at: datetime | None


class ProductDetail(BaseModel):
    id: UUID
    name: str
    brand: str | None
    barcode: str | None
    image_url: str | None
    is_favorite: bool
    notes: str | None
    tags: list[str]
    latest_report: dict[str, Any] | None
    scan_history: list[dict[str, Any]]


class ProductUpdate(BaseModel):
    notes: str | None = None
    tags: list[str] | None = None


class ScanListItem(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    health_score: int
    grade: str
    scanned_at: datetime


class ScanDetail(BaseModel):
    id: UUID
    product: ProductBrief
    health_score: int
    grade: str
    tier_counts: dict[str, int]
    ingredients: list[dict[str, Any]]
    risks: list[dict[str, Any]]
    profile_alerts: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    summary: str
    recommendations: list[str]
    scanned_at: datetime
    provider_meta: dict[str, Any]


# --- Ingredient detail (IngredientIQ) ---


class TierCounts(BaseModel):
    total: int
    concern: int
    caution: int
    safe: int
    unknown: int


class IngredientNavItem(BaseModel):
    id: int
    label_name: str | None


class IngredientNavigation(BaseModel):
    prev: IngredientNavItem | None
    next: IngredientNavItem | None


class IngredientDetailResponse(BaseModel):
    scan_id: UUID
    ingredient: dict[str, Any]
    navigation: IngredientNavigation
    is_bookmarked: bool
    studies_total: int
    studies_more_count: int


class WatchlistRequest(BaseModel):
    label_name: str
    e_code: str | None = None


class WatchlistItem(BaseModel):
    id: UUID
    label_name: str
    e_code: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
