import base64
import hashlib
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Product, Profile, Scan, ScanReport, UserProduct
from app.models.pipeline import ProviderMeta
from app.models.schemas import ScanResponse
from app.pipeline.stage0_ocr_cleanup import run_stage0_ocr_cleanup
from app.pipeline.stage1_parse import run_stage1_parse
from app.pipeline.stage2_enrich import run_stage2_enrich
from app.pipeline.stage3_report import run_stage3_report
from app.providers.registry import get_barcode_provider, get_storage_provider, ocr_with_fallback
from app.services.ingredient_utils import compute_tier_counts

logger = logging.getLogger(__name__)
settings = get_settings()


async def _get_or_create_product(
    session: AsyncSession,
    *,
    barcode: str | None,
    name: str,
    brand: str | None,
    image_url: str | None,
    ingredient_text: str,
) -> Product:
    content_hash = hashlib.sha256(ingredient_text.encode()).hexdigest() if ingredient_text else None

    if barcode:
        stmt = select(Product).where(Product.barcode == barcode)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

    if content_hash:
        stmt = select(Product).where(Product.content_hash == content_hash)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

    product = Product(
        barcode=barcode,
        content_hash=content_hash,
        name=name,
        brand=brand,
        image_url=image_url,
    )
    session.add(product)
    await session.flush()
    return product


async def run_scan_pipeline(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    barcode: str | None = None,
    ingredient_text: str | None = None,
    image_base64: str | None = None,
    storage_path: str | None = None,
    product_hint: str | None = None,
    region: str | None = None,
) -> ScanResponse:
    profile_stmt = select(Profile).where(Profile.user_id == user_id)
    profile_row = (await session.execute(profile_stmt)).scalar_one_or_none()
    profile = {
        "allergens": profile_row.allergens if profile_row else [],
        "avoid_additives": profile_row.avoid_additives if profile_row else [],
        "dietary_preferences": profile_row.dietary_preferences if profile_row else [],
    }
    effective_region = region or (profile_row.region if profile_row else "US")

    meta = ProviderMeta()
    product_name = product_hint or "Unknown Product"
    product_brand: str | None = None
    product_image: str | None = None
    raw_text = ingredient_text or ""
    skip_stage0 = bool(barcode and not ingredient_text)

    # Barcode path
    if barcode:
        meta.barcode = "open_food_facts"
        off = get_barcode_provider()
        off_data = await off.lookup(barcode)
        if off_data:
            raw_text = off_data.get("ingredients_text") or raw_text
            product_name = off_data.get("name") or product_name
            product_brand = off_data.get("brand")
            product_image = off_data.get("image_url")
            skip_stage0 = True

    # Image path
    image_bytes: bytes | None = None
    stored_path = storage_path
    if image_base64 and not raw_text:
        image_bytes = base64.b64decode(image_base64)
    elif storage_path and not raw_text:
        storage = get_storage_provider()
        image_bytes = await storage.download(storage_path)

    if image_bytes and not raw_text:
        raw_text, meta.ocr = await ocr_with_fallback(image_bytes)

    if not raw_text.strip():
        raise ValueError("No ingredient text available from barcode, text, or image")

    cleaned_text, meta.ocr_cleanup = await run_stage0_ocr_cleanup(raw_text, skip=skip_stage0)

    stage1, meta.llm_s1 = await run_stage1_parse(cleaned_text)
    stage2, meta.llm_s2, meta.llm_s2_assist = await run_stage2_enrich(
        session, stage1.ingredients, region=effective_region
    )
    stage3, meta.llm_s3, meta.search = await run_stage3_report(
        stage2.ingredients,
        product_hint=product_name,
        region=effective_region,
        profile=profile,
    )

    product = await _get_or_create_product(
        session,
        barcode=barcode,
        name=product_name,
        brand=product_brand,
        image_url=product_image,
        ingredient_text=cleaned_text,
    )

    scan_id = uuid.uuid4()
    if image_bytes and not stored_path:
        storage = get_storage_provider()
        stored_path = await storage.upload(
            user_id=str(user_id),
            scan_id=str(scan_id),
            data=image_bytes,
            content_type="image/jpeg",
        )

    scan = Scan(
        id=scan_id,
        user_id=user_id,
        product_id=product.id,
        image_storage_path=stored_path,
        ingredient_text_raw=cleaned_text,
        provider_meta=meta.to_dict(),
    )
    session.add(scan)

    report = ScanReport(
        scan_id=scan.id,
        health_score=stage3.health_score,
        grade=stage3.grade,
        ingredients=[i.model_dump() for i in stage2.ingredients],
        risks=[r.model_dump() for r in stage3.risks],
        profile_alerts=[a.model_dump() for a in stage3.profile_alerts],
        citations=[c.model_dump() for c in stage3.citations],
        summary=stage3.summary,
        recommendations=stage3.recommendations,
    )
    session.add(report)

    # Ensure user_product link exists
    up_stmt = select(UserProduct).where(
        UserProduct.user_id == user_id, UserProduct.product_id == product.id
    )
    up = (await session.execute(up_stmt)).scalar_one_or_none()
    if not up:
        session.add(UserProduct(user_id=user_id, product_id=product.id))

    await session.flush()

    tier_counts = compute_tier_counts(stage2.ingredients)

    return ScanResponse(
        scan_id=scan.id,
        product={"id": product.id, "name": product.name, "barcode": product.barcode},
        ingredients=[i.model_dump() for i in stage2.ingredients],
        tier_counts=tier_counts.model_dump(),
        health_score=stage3.health_score,
        grade=stage3.grade,
        risks=[r.model_dump() for r in stage3.risks],
        profile_alerts=[a.model_dump() for a in stage3.profile_alerts],
        citations=[c.model_dump() for c in stage3.citations],
        summary=stage3.summary,
        recommendations=stage3.recommendations,
        provider_meta=meta.to_dict(),
        disclaimer=settings.disclaimer,
    )
