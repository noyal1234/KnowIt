"""Add IngredientIQ columns to existing PostgreSQL tables (safe to re-run)."""

import asyncio
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import text

from app.db.session import engine

ALTERS = [
    "ALTER TABLE regulatory_additives ADD COLUMN IF NOT EXISTS function VARCHAR(128)",
    "ALTER TABLE regulatory_additives ADD COLUMN IF NOT EXISTS iupac_name VARCHAR(512)",
    "ALTER TABLE regulatory_additives ADD COLUMN IF NOT EXISTS who_jecfa_status VARCHAR(128)",
    "ALTER TABLE regulatory_additives ADD COLUMN IF NOT EXISTS banned_in JSONB DEFAULT '[]'",
    "ALTER TABLE regulatory_additives ADD COLUMN IF NOT EXISTS at_risk_groups JSONB DEFAULT '[]'",
]


async def migrate() -> None:
    async with engine.begin() as conn:
        for stmt in ALTERS:
            await conn.execute(text(stmt))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ingredient_watchlist (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id),
                label_name VARCHAR(255) NOT NULL,
                e_code VARCHAR(16),
                normalized_key VARCHAR(270) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT uq_user_watch_ingredient UNIQUE (user_id, normalized_key)
            )
        """))
    print("Migration complete")


if __name__ == "__main__":
    asyncio.run(migrate())
