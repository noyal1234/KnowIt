import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_providers.base import AuthUser
from app.core.deps import get_current_user
from app.db.models import Product, Scan, ScanReport, UserProduct
from app.db.session import get_db
from app.models.schemas import ProductDetail, ProductListItem, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductListItem])
async def list_products(
    favorite: bool | None = None,
    search: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Product, UserProduct, ScanReport, Scan.scanned_at)
        .join(UserProduct, UserProduct.product_id == Product.id)
        .join(Scan, Scan.product_id == Product.id)
        .join(ScanReport, ScanReport.scan_id == Scan.id)
        .where(UserProduct.user_id == current_user.id)
        .order_by(Scan.scanned_at.desc())
    )
    if favorite is not None:
        stmt = stmt.where(UserProduct.is_favorite.is_(favorite))
    if search:
        stmt = stmt.where(Product.name.ilike(f"%{search}%"))

    rows = (await session.execute(stmt.offset(offset).limit(limit))).all()
    seen: set[uuid.UUID] = set()
    items: list[ProductListItem] = []
    for product, up, report, scanned_at in rows:
        if product.id in seen:
            continue
        seen.add(product.id)
        items.append(
            ProductListItem(
                id=product.id,
                name=product.name,
                brand=product.brand,
                barcode=product.barcode,
                latest_score=report.health_score,
                latest_grade=report.grade,
                is_favorite=up.is_favorite,
                last_scanned_at=scanned_at,
            )
        )
    return items


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(
    product_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    product = (await session.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    up = (
        await session.execute(
            select(UserProduct).where(
                UserProduct.user_id == current_user.id, UserProduct.product_id == product_id
            )
        )
    ).scalar_one_or_none()

    scans_stmt = (
        select(Scan, ScanReport)
        .join(ScanReport, ScanReport.scan_id == Scan.id)
        .where(Scan.user_id == current_user.id, Scan.product_id == product_id)
        .order_by(Scan.scanned_at.desc())
    )
    scan_rows = (await session.execute(scans_stmt)).all()
    latest_report = None
    history = []
    for scan, report in scan_rows:
        entry = {
            "scan_id": str(scan.id),
            "scanned_at": scan.scanned_at.isoformat(),
            "health_score": report.health_score,
            "grade": report.grade,
        }
        history.append(entry)
        if latest_report is None:
            latest_report = {
                "health_score": report.health_score,
                "grade": report.grade,
                "summary": report.summary,
                "ingredients": report.ingredients,
                "risks": report.risks,
            }

    return ProductDetail(
        id=product.id,
        name=product.name,
        brand=product.brand,
        barcode=product.barcode,
        image_url=product.image_url,
        is_favorite=up.is_favorite if up else False,
        notes=up.notes if up else None,
        tags=up.tags if up else [],
        latest_report=latest_report,
        scan_history=history,
    )


@router.post("/{product_id}/favorite")
async def toggle_favorite(
    product_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    up = (
        await session.execute(
            select(UserProduct).where(
                UserProduct.user_id == current_user.id, UserProduct.product_id == product_id
            )
        )
    ).scalar_one_or_none()
    if not up:
        up = UserProduct(user_id=current_user.id, product_id=product_id, is_favorite=True)
        session.add(up)
    else:
        up.is_favorite = not up.is_favorite
    await session.flush()
    return {"is_favorite": up.is_favorite}


@router.patch("/{product_id}")
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    up = (
        await session.execute(
            select(UserProduct).where(
                UserProduct.user_id == current_user.id, UserProduct.product_id == product_id
            )
        )
    ).scalar_one_or_none()
    if not up:
        up = UserProduct(user_id=current_user.id, product_id=product_id)
        session.add(up)
    if body.notes is not None:
        up.notes = body.notes
    if body.tags is not None:
        up.tags = body.tags
    await session.flush()
    return {"detail": "Updated"}
