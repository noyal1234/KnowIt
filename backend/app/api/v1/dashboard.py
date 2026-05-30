from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_providers.base import AuthUser
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.schemas import (
    DashboardAlertsResponse,
    DashboardSummary,
    DashboardTrends,
    TopConcernIngredient,
)
from app.services.dashboard import get_dashboard_summary, get_dashboard_trends, get_top_concerns

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await get_dashboard_summary(session, current_user.id)


@router.get("/trends", response_model=DashboardTrends)
async def dashboard_trends(
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await get_dashboard_trends(session, current_user.id, period)


@router.get("/alerts", response_model=DashboardAlertsResponse)
async def dashboard_alerts(
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    summary = await get_dashboard_summary(session, current_user.id)
    return DashboardAlertsResponse(
        active_alerts_count=summary.active_alerts_count,
        recent_products=summary.recent_products,
    )


@router.get("/ingredients/top-concerns", response_model=list[TopConcernIngredient])
async def top_concerns(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await get_top_concerns(session, current_user.id, limit)
