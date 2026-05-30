import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)
    scans: Mapped[list["Scan"]] = relationship(back_populates="user")
    user_products: Mapped[list["UserProduct"]] = relationship(back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(255), default="")
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    region: Mapped[str] = mapped_column(String(8), default="US")
    dietary_preferences: Mapped[list] = mapped_column(JSONB, default=list)
    allergens: Mapped[list] = mapped_column(JSONB, default=list)
    avoid_additives: Mapped[list] = mapped_column(JSONB, default=list)
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    health_goal: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    barcode: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(512), default="Unknown Product")
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scans: Mapped[list["Scan"]] = relationship(back_populates="product")
    user_products: Mapped[list["UserProduct"]] = relationship(back_populates="product")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    image_storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    ingredient_text_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_meta: Mapped[dict] = mapped_column(JSONB, default=dict)

    user: Mapped["User"] = relationship(back_populates="scans")
    product: Mapped["Product"] = relationship(back_populates="scans")
    report: Mapped["ScanReport"] = relationship(back_populates="scan", uselist=False)


class ScanReport(Base):
    __tablename__ = "scan_reports"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), primary_key=True
    )
    health_score: Mapped[int] = mapped_column(Integer, nullable=False)
    grade: Mapped[str] = mapped_column(String(2), nullable=False)
    ingredients: Mapped[list] = mapped_column(JSONB, default=list)
    risks: Mapped[list] = mapped_column(JSONB, default=list)
    profile_alerts: Mapped[list] = mapped_column(JSONB, default=list)
    citations: Mapped[list] = mapped_column(JSONB, default=list)
    summary: Mapped[str] = mapped_column(Text, default="")
    recommendations: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scan: Mapped["Scan"] = relationship(back_populates="report")


class UserProduct(Base):
    __tablename__ = "user_products"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_user_product"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="user_products")
    product: Mapped["Product"] = relationship(back_populates="user_products")


class RegulatoryAdditive(Base):
    __tablename__ = "regulatory_additives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    e_code: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    cas_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fda_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    eu_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fssai_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    adi_mg_per_kg: Mapped[float | None] = mapped_column(nullable=True)
    default_risk_tier: Mapped[str] = mapped_column(String(16), default="unknown")
    function: Mapped[str | None] = mapped_column(String(128), nullable=True)
    iupac_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    who_jecfa_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    banned_in: Mapped[list] = mapped_column(JSONB, default=list)
    at_risk_groups: Mapped[list] = mapped_column(JSONB, default=list)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)


class IngredientWatchlist(Base):
    __tablename__ = "ingredient_watchlist"
    __table_args__ = (UniqueConstraint("user_id", "normalized_key", name="uq_user_watch_ingredient"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    label_name: Mapped[str] = mapped_column(String(255), nullable=False)
    e_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    normalized_key: Mapped[str] = mapped_column(String(270), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
