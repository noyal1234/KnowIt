import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_expire_min)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str, jti: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh", "jti": jti}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    if settings.auth_provider == "supabase" and settings.supabase_jwt_secret:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def get_token_subject(payload: dict[str, Any]) -> uuid.UUID:
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Missing subject")
    return uuid.UUID(str(sub))
