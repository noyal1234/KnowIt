import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_providers.base import AuthUser
from app.core.deps import get_current_user
from app.db.models import Product, Scan, ScanReport
from app.db.session import get_db
from app.models.schemas import (
    IngredientDetailResponse,
    IngredientNavigation,
    IngredientNavItem,
    ScanDetail,
    ScanListItem,
)
from app.services.ingredient_detail import build_ingredient_detail
from app.services.ingredient_utils import compute_tier_counts

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("", response_model=list[ScanListItem])
async def list_scans(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Scan, ScanReport, Product.name)
        .join(ScanReport, ScanReport.scan_id == Scan.id)
        .join(Product, Product.id == Scan.product_id)
        .where(Scan.user_id == current_user.id)
        .order_by(Scan.scanned_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        ScanListItem(
            id=scan.id,
            product_id=scan.product_id,
            product_name=name,
            health_score=report.health_score,
            grade=report.grade,
            scanned_at=scan.scanned_at,
        )
        for scan, report, name in rows
    ]


@router.get("/{scan_id}", response_model=ScanDetail)
async def get_scan(
    scan_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Scan, ScanReport, Product)
        .join(ScanReport, ScanReport.scan_id == Scan.id)
        .join(Product, Product.id == Scan.product_id)
        .where(Scan.id == scan_id, Scan.user_id == current_user.id)
    )
    row = (await session.execute(stmt)).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan, report, product = row
    tier_counts = compute_tier_counts(report.ingredients or [])
    return ScanDetail(
        id=scan.id,
        product={"id": product.id, "name": product.name, "barcode": product.barcode},
        health_score=report.health_score,
        grade=report.grade,
        tier_counts=tier_counts.model_dump(),
        ingredients=report.ingredients,
        risks=report.risks,
        profile_alerts=report.profile_alerts,
        citations=report.citations,
        summary=report.summary,
        recommendations=report.recommendations,
        scanned_at=scan.scanned_at,
        provider_meta=scan.provider_meta,
    )


@router.get("/{scan_id}/ingredients/{ingredient_id}", response_model=IngredientDetailResponse)
async def get_ingredient_detail(
    scan_id: uuid.UUID,
    ingredient_id: int,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await build_ingredient_detail(
        session,
        user_id=current_user.id,
        scan_id=scan_id,
        ingredient_id=ingredient_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Scan or ingredient not found")
    nav = result["navigation"]
    return IngredientDetailResponse(
        scan_id=result["scan_id"],
        ingredient=result["ingredient"],
        navigation=IngredientNavigation(
            prev=IngredientNavItem(**nav["prev"]) if nav.get("prev") else None,
            next=IngredientNavItem(**nav["next"]) if nav.get("next") else None,
        ),
        is_bookmarked=result["is_bookmarked"],
        studies_total=result["studies_total"],
        studies_more_count=result["studies_more_count"],
    )


@router.delete("/{scan_id}")
async def delete_scan(
    scan_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Scan).where(Scan.id == scan_id, Scan.user_id == current_user.id)
    scan = (await session.execute(stmt)).scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    await session.delete(scan)
    return {"detail": "Deleted"}
