import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.auth_providers.base import AuthUser
from app.core.auth_providers.local import LocalAuthProvider
from app.core.deps import get_auth_provider, get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.models import Profile, User
from app.db.session import get_db
from app.models.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services.cache import refresh_token_blocklist_add, refresh_token_is_blocklisted

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


async def _user_out(session: AsyncSession, user_id: uuid.UUID) -> UserOut:
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


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    auth: LocalAuthProvider = Depends(get_auth_provider),
    session: AsyncSession = Depends(get_db),
):
    if settings.auth_provider != "local":
        raise HTTPException(status_code=400, detail="Registration via API disabled in Supabase mode")
    try:
        user = await auth.register(body.email, body.password, body.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    jti = str(uuid.uuid4())
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id), jti),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    auth: LocalAuthProvider = Depends(get_auth_provider),
):
    if settings.auth_provider != "local":
        raise HTTPException(status_code=400, detail="Login via API disabled in Supabase mode")
    try:
        user = await auth.login(body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    jti = str(uuid.uuid4())
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id), jti),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    if settings.auth_provider != "local":
        raise HTTPException(status_code=400, detail="Use Supabase client to refresh tokens")
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        jti = payload.get("jti", "")
        if jti and await refresh_token_is_blocklisted(jti):
            raise HTTPException(status_code=401, detail="Token revoked")
        user_id = payload["sub"]
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    new_jti = str(uuid.uuid4())
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id, new_jti),
    )


@router.post("/logout")
async def logout(body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
        jti = payload.get("jti")
        if jti:
            ttl = settings.jwt_refresh_expire_days * 86400
            await refresh_token_blocklist_add(jti, ttl)
    except Exception:
        pass
    return {"detail": "Logged out"}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    if settings.auth_provider == "supabase":
        return {"detail": "Use Supabase password reset flow"}
    return {"detail": "If the email exists, a reset link will be sent"}


@router.get("/me", response_model=UserOut)
async def me(
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await _user_out(session, current_user.id)
