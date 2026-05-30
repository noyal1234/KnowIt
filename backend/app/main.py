from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.api.v1 import auth, dashboard, products, profile, scan, scans, watchlist
from app.config import get_settings
from app.core.rate_limit import limiter
from app.db.models import Base
from app.db.session import engine
from app.services.cache import get_redis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(dashboard.router)
api_router.include_router(products.router)
api_router.include_router(scans.router)
api_router.include_router(scan.router)
api_router.include_router(watchlist.router)
app.include_router(api_router)


@app.get("/health")
async def health():
    checks = {"api": "ok", "postgres": "unknown", "redis": "unknown"}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {exc}"

    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    status_code = 200 if checks["postgres"] == "ok" else 503
    from fastapi.responses import JSONResponse

    return JSONResponse(content=checks, status_code=status_code)
