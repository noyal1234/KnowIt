import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.auth_providers.base import AuthUser
from app.core.auth_providers.local import LocalAuthProvider
from app.core.auth_providers.supabase import SupabaseAuthProvider
from app.db.session import get_db

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_provider(session: AsyncSession = Depends(get_db)) -> LocalAuthProvider | SupabaseAuthProvider:
    if settings.auth_provider == "supabase":
        return SupabaseAuthProvider(session)
    return LocalAuthProvider(session)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth: Annotated[LocalAuthProvider | SupabaseAuthProvider, Depends(get_auth_provider)],
) -> AuthUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        return await auth.verify_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
