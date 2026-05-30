import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.auth_providers.base import AuthUser
from app.core.auth_providers.local import LocalAuthProvider
from app.core.deps import get_auth_provider, get_current_user
from app.core.rate_limit import limiter
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.models.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services.cache import refresh_token_blocklist_add, refresh_token_is_blocklisted
from app.services.user import build_user_out

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

_AUTH_LIMIT = "20/minute"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(_AUTH_LIMIT, key_func=get_remote_address)
async def register(
    request: Request,
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
    logger.info("event=UserRegistered user_id=%s", user.id)
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id), jti),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(_AUTH_LIMIT, key_func=get_remote_address)
async def login(
    request: Request,
    body: LoginRequest,
    auth: LocalAuthProvider = Depends(get_auth_provider),
):
    if settings.auth_provider != "local":
        raise HTTPException(status_code=400, detail="Login via API disabled in Supabase mode")
    try:
        user = await auth.login(body.email, body.password)
    except ValueError as exc:
        logger.warning("event=LoginFailed")
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    jti = str(uuid.uuid4())
    logger.info("event=LoginSucceeded user_id=%s", user.id)
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id), jti),
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(_AUTH_LIMIT, key_func=get_remote_address)
async def refresh(request: Request, body: RefreshRequest):
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
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    new_jti = str(uuid.uuid4())
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id, new_jti),
    )


@router.post("/logout", response_model=MessageResponse)
@limiter.limit(_AUTH_LIMIT, key_func=get_remote_address)
async def logout(request: Request, body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
        jti = payload.get("jti")
        if jti:
            ttl = settings.jwt_refresh_expire_days * 86400
            await refresh_token_blocklist_add(jti, ttl)
    except JWTError:
        pass
    return MessageResponse(detail="Logged out")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("10/minute", key_func=get_remote_address)
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    if settings.auth_provider == "supabase":
        return MessageResponse(detail="Use Supabase password reset flow")
    return MessageResponse(detail="If the email exists, a reset link will be sent")


@router.get("/me", response_model=UserOut)
async def me(
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await build_user_out(session, current_user.id)
