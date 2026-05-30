import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product, Scan, ScanReport, UserProduct
from app.models.schemas import DashboardSummary, DashboardTrends, RecentProduct, TrendPoint, TopConcernIngredient

logger = logging.getLogger(__name__)


async def get_dashboard_summary(session: AsyncSession, user_id: UUID) -> DashboardSummary:
    total_stmt = select(func.count(Scan.id)).where(Scan.user_id == user_id)
    total_scans = (await session.execute(total_stmt)).scalar() or 0

    avg_stmt = (
        select(func.avg(ScanReport.health_score))
        .join(Scan, Scan.id == ScanReport.scan_id)
        .where(Scan.user_id == user_id)
    )
    avg_score = (await session.execute(avg_stmt)).scalar() or 0.0

    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    avg_7d_stmt = (
        select(func.avg(ScanReport.health_score))
        .join(Scan, Scan.id == ScanReport.scan_id)
        .where(Scan.user_id == user_id, Scan.scanned_at >= week_ago)
    )
    avg_7d = (await session.execute(avg_7d_stmt)).scalar()

    prev_7d_stmt = (
        select(func.avg(ScanReport.health_score))
        .join(Scan, Scan.id == ScanReport.scan_id)
        .where(
            Scan.user_id == user_id,
            Scan.scanned_at >= two_weeks_ago,
            Scan.scanned_at < week_ago,
        )
    )
    prev_7d = (await session.execute(prev_7d_stmt)).scalar()

    score_change = None
    if avg_7d is not None and prev_7d is not None:
        score_change = round(float(avg_7d) - float(prev_7d), 1)

    grade_stmt = (
        select(ScanReport.grade, func.count())
        .join(Scan, Scan.id == ScanReport.scan_id)
        .where(Scan.user_id == user_id)
        .group_by(ScanReport.grade)
    )
    grade_rows = (await session.execute(grade_stmt)).all()
    grade_distribution = {g: c for g, c in grade_rows}

    fav_stmt = select(func.count()).where(UserProduct.user_id == user_id, UserProduct.is_favorite.is_(True))
    favorites_count = (await session.execute(fav_stmt)).scalar() or 0

    last_scan_stmt = (
        select(Scan.scanned_at).where(Scan.user_id == user_id).order_by(Scan.scanned_at.desc()).limit(1)
    )
    last_scan_at = (await session.execute(last_scan_stmt)).scalar_one_or_none()

    recent_stmt = (
        select(Product.id, Product.name, ScanReport.health_score, ScanReport.grade)
        .join(Scan, Scan.product_id == Product.id)
        .join(ScanReport, ScanReport.scan_id == Scan.id)
        .where(Scan.user_id == user_id)
        .order_by(Scan.scanned_at.desc())
        .limit(5)
    )
    recent_rows = (await session.execute(recent_stmt)).all()
    recent_products = [
        RecentProduct(id=r[0], name=r[1], score=r[2], grade=r[3]) for r in recent_rows
    ]

    alerts_stmt = (
        select(ScanReport.profile_alerts)
        .join(Scan, Scan.id == ScanReport.scan_id)
        .where(Scan.user_id == user_id, Scan.scanned_at >= week_ago)
    )
    alert_rows = (await session.execute(alerts_stmt)).scalars().all()
    active_alerts_count = sum(len(a or []) for a in alert_rows)

    return DashboardSummary(
        total_scans=total_scans,
        avg_health_score=round(float(avg_score), 1),
        avg_score_last_7d=round(float(avg_7d), 1) if avg_7d is not None else None,
        score_change_vs_prev_7d=score_change,
        grade_distribution=grade_distribution,
        active_alerts_count=active_alerts_count,
        favorites_count=favorites_count,
        last_scan_at=last_scan_at,
        recent_products=recent_products,
    )


async def get_dashboard_trends(session: AsyncSession, user_id: UUID, period: str) -> DashboardTrends:
    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
    since = datetime.now(UTC) - timedelta(days=days)

    stmt = (
        select(
            func.date(Scan.scanned_at).label("day"),
            func.avg(ScanReport.health_score),
            func.count(Scan.id),
        )
        .join(ScanReport, ScanReport.scan_id == Scan.id)
        .where(Scan.user_id == user_id, Scan.scanned_at >= since)
        .group_by(func.date(Scan.scanned_at))
        .order_by(func.date(Scan.scanned_at))
    )
    rows = (await session.execute(stmt)).all()
    data_points = [
        TrendPoint(date=str(r[0]), avg_score=round(float(r[1]), 1), scan_count=r[2]) for r in rows
    ]
    return DashboardTrends(period=period, data_points=data_points)


async def get_top_concerns(session: AsyncSession, user_id: UUID, limit: int = 10) -> list[TopConcernIngredient]:
    stmt = (
        select(ScanReport.ingredients, ScanReport.risks)
        .join(Scan, Scan.id == ScanReport.scan_id)
        .where(Scan.user_id == user_id)
        .order_by(Scan.scanned_at.desc())
        .limit(100)
    )
    rows = (await session.execute(stmt)).all()
    counts: dict[str, dict] = {}
    for ingredients, risks in rows:
        for risk in risks or []:
            if risk.get("tier") in ("concern", "caution"):
                name = risk.get("ingredient", "unknown")
                if name not in counts:
                    counts[name] = {"count": 0, "tier": risk.get("tier", "concern")}
                counts[name]["count"] += 1

    sorted_items = sorted(counts.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]
    return [
        TopConcernIngredient(ingredient=k, count=v["count"], tier=v["tier"])
        for k, v in sorted_items
    ]
