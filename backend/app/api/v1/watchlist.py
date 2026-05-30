import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_providers.base import AuthUser
from app.core.deps import get_current_user
from app.db.models import IngredientWatchlist
from app.db.session import get_db
from app.models.schemas import WatchlistItem, WatchlistRequest

router = APIRouter(prefix="/watchlist/ingredients", tags=["watchlist"])


def _normalized_key(label_name: str, e_code: str | None) -> str:
    return (e_code or label_name).strip().lower()


@router.get("", response_model=list[WatchlistItem])
async def list_watchlist(
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(IngredientWatchlist)
        .where(IngredientWatchlist.user_id == current_user.id)
        .order_by(IngredientWatchlist.created_at.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return rows


@router.post("", response_model=WatchlistItem)
async def add_to_watchlist(
    body: WatchlistRequest,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    key = _normalized_key(body.label_name, body.e_code)
    stmt = select(IngredientWatchlist).where(
        IngredientWatchlist.user_id == current_user.id,
        IngredientWatchlist.normalized_key == key,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing

    item = IngredientWatchlist(
        user_id=current_user.id,
        label_name=body.label_name,
        e_code=body.e_code,
        normalized_key=key,
    )
    session.add(item)
    await session.flush()
    return item


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(IngredientWatchlist).where(
        IngredientWatchlist.id == watchlist_id,
        IngredientWatchlist.user_id == current_user.id,
    )
    item = (await session.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    await session.delete(item)
    return {"detail": "Removed"}


@router.delete("")
async def remove_by_key(
    label_name: str,
    e_code: str | None = None,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    key = _normalized_key(label_name, e_code)
    stmt = select(IngredientWatchlist).where(
        IngredientWatchlist.user_id == current_user.id,
        IngredientWatchlist.normalized_key == key,
    )
    item = (await session.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    await session.delete(item)
    return {"detail": "Removed"}
