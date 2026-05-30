import uuid

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_providers.base import AuthProvider, AuthUser
from app.core.security import decode_token, get_token_subject
from app.db.models import Profile, User


class SupabaseAuthProvider(AuthProvider):
    """Verify Supabase-issued JWTs; registration/login handled by Supabase client on iOS."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(self, email: str, password: str, display_name: str) -> AuthUser:
        raise NotImplementedError("Use Supabase client for registration")

    async def login(self, email: str, password: str) -> AuthUser:
        raise NotImplementedError("Use Supabase client for login")

    async def verify_access_token(self, token: str) -> AuthUser:
        try:
            payload = decode_token(token)
            user_id = get_token_subject(payload)
            email = payload.get("email", f"{user_id}@supabase.local")
        except JWTError as exc:
            raise ValueError("Invalid Supabase token") from exc

        stmt = select(User).where(User.id == user_id)
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if not user:
            user = User(id=user_id, email=email, hashed_password=None)
            self._session.add(user)
            profile = Profile(user_id=user_id, display_name=email.split("@")[0])
            self._session.add(profile)
            await self._session.flush()
        return AuthUser(id=user.id, email=user.email)
