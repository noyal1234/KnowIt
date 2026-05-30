from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_providers.base import AuthUser
from app.core.deps import get_current_user
from app.db.models import Profile, User
from app.db.session import get_db
from app.models.schemas import ProfileUpdate, UserOut

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserOut)
async def get_profile(
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()
    profile = (await session.execute(select(Profile).where(Profile.user_id == current_user.id))).scalar_one_or_none()
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=profile.display_name if profile else "",
        region=profile.region if profile else "US",
        dietary_preferences=profile.dietary_preferences if profile else [],
        allergens=profile.allergens if profile else [],
        avoid_additives=profile.avoid_additives if profile else [],
        notification_enabled=profile.notification_enabled if profile else True,
        health_goal=profile.health_goal if profile else None,
        avatar_url=profile.avatar_url if profile else None,
    )


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
    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=profile.display_name,
        region=profile.region,
        dietary_preferences=profile.dietary_preferences,
        allergens=profile.allergens,
        avoid_additives=profile.avoid_additives,
        notification_enabled=profile.notification_enabled,
        health_goal=profile.health_goal,
        avatar_url=profile.avatar_url,
    )


@router.delete("")
async def delete_profile(
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()
    profile = (await session.execute(select(Profile).where(Profile.user_id == current_user.id))).scalar_one_or_none()
    user.is_active = False
    if profile:
        profile.deleted_at = datetime.now(UTC)
    return {"detail": "Account deactivated"}
