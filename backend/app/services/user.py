import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile, User
from app.models.schemas import UserOut


async def build_user_out(session: AsyncSession, user_id: uuid.UUID) -> UserOut:
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one()
    profile = (await session.execute(select(Profile).where(Profile.user_id == user_id))).scalar_one_or_none()
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
