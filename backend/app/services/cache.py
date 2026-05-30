import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def cache_get(key: str) -> dict[str, Any] | None:
    try:
        r = await get_redis()
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception as exc:
        logger.warning("Redis get failed: %s", exc)
        return None


async def cache_set(key: str, value: dict[str, Any], ttl_seconds: int) -> None:
    try:
        r = await get_redis()
        await r.setex(key, ttl_seconds, json.dumps(value))
    except Exception as exc:
        logger.warning("Redis set failed: %s", exc)


async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception as exc:
        logger.warning("Redis delete failed: %s", exc)


async def refresh_token_blocklist_add(token_jti: str, ttl_seconds: int) -> None:
    try:
        r = await get_redis()
        await r.setex(f"blocklist:{token_jti}", ttl_seconds, "1")
    except Exception as exc:
        logger.warning("Redis blocklist failed: %s", exc)


async def refresh_token_is_blocklisted(token_jti: str) -> bool:
    try:
        r = await get_redis()
        return bool(await r.get(f"blocklist:{token_jti}"))
    except Exception:
        return False
