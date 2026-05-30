import uuid

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_providers.base import AuthProvider, AuthUser
from app.core.security import decode_token, get_token_subject, hash_password, verify_password
from app.db.models import Profile, User


class LocalAuthProvider(AuthProvider):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(self, email: str, password: str, display_name: str) -> AuthUser:
        stmt = select(User).where(User.email == email.lower())
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ValueError("Email already registered")

        user = User(email=email.lower(), hashed_password=hash_password(password))
        self._session.add(user)
        await self._session.flush()

        profile = Profile(user_id=user.id, display_name=display_name or email.split("@")[0])
        self._session.add(profile)
        await self._session.flush()
        return AuthUser(id=user.id, email=user.email)

    async def login(self, email: str, password: str) -> AuthUser:
        stmt = select(User).where(User.email == email.lower(), User.is_active.is_(True))
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        return AuthUser(id=user.id, email=user.email)

    async def verify_access_token(self, token: str) -> AuthUser:
        try:
            payload = decode_token(token)
            if payload.get("type") == "refresh":
                raise JWTError("Refresh token not accepted")
            user_id = get_token_subject(payload)
        except JWTError as exc:
            raise ValueError("Invalid token") from exc

        stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        return AuthUser(id=user.id, email=user.email)
