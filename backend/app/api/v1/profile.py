import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_providers.base import AuthUser
from app.core.deps import get_current_user
from app.db.models import Profile, User
from app.db.session import get_db
from app.models.schemas import MessageResponse, ProfileUpdate, UserOut
from app.services.user import build_user_out

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserOut)
async def get_profile(
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await build_user_out(session, current_user.id)


@router.patch("", response_model=UserOut)
async def update_profile(
    body: ProfileUpdate,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    profile = (await session.execute(select(Profile).where(Profile.user_id == current_user.id))).scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=current_user.id)
        session.add(profile)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await session.flush()
    logger.info("event=ProfileUpdated user_id=%s", current_user.id)
    return await build_user_out(session, current_user.id)


@router.delete("", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def delete_profile(
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()
    profile = (await session.execute(select(Profile).where(Profile.user_id == current_user.id))).scalar_one_or_none()
    user.is_active = False
    if profile:
        profile.deleted_at = datetime.now(UTC)
    logger.info("event=ProfileDeactivated user_id=%s", current_user.id)
    return MessageResponse(detail="Account deactivated")
