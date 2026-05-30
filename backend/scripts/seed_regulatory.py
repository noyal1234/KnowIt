"""Seed regulatory additive tables from CSV files.

Run from backend/ with venv activated:
  cd backend && source ../.venv/bin/activate && python scripts/seed_regulatory.py

To refresh regulatory data on an existing DB:
  python scripts/seed_regulatory.py --force
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import delete, select

from app.db.models import Base, RegulatoryAdditive
from app.db.session import async_session_factory, engine

DATA_DIR = _BACKEND_ROOT / "data" / "regulatory"
FILES = ["seed_fda.csv", "seed_eu_e_numbers.csv", "seed_fssai.csv"]


def _parse_float(val: str) -> float | None:
    if not val or val.strip() in ("", "-1"):
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _parse_list(val: str | None) -> list[str]:
    if not val or not val.strip():
        return []
    return [p.strip() for p in val.replace("|", ",").split(",") if p.strip()]


async def seed(*, force: bool = False) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        existing = (await session.execute(select(RegulatoryAdditive.id).limit(1))).scalar_one_or_none()
        if existing and not force:
            print("Regulatory data already seeded — skipping (use --force to reload)")
            return

        if force and existing:
            await session.execute(delete(RegulatoryAdditive))
            await session.commit()
            print("Cleared existing regulatory additives")

        seen: set[tuple[str, str | None]] = set()
        for filename in FILES:
            path = DATA_DIR / filename
            if not path.exists():
                continue
            with path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row["canonical_name"].strip()
                    e_code = row.get("e_code") or None
                    key = (name.lower(), (e_code or "").lower())
                    if key in seen:
                        continue
                    seen.add(key)
                    session.add(
                        RegulatoryAdditive(
                            canonical_name=name,
                            e_code=e_code,
                            cas_number=row.get("cas_number") or None,
                            fda_status=row.get("fda_status") or None,
                            eu_status=row.get("eu_status") or None,
                            fssai_status=row.get("fssai_status") or None,
                            who_jecfa_status=row.get("who_jecfa_status") or None,
                            adi_mg_per_kg=_parse_float(row.get("adi_mg_per_kg", "")),
                            default_risk_tier=row.get("default_risk_tier") or "unknown",
                            function=row.get("function") or None,
                            iupac_name=row.get("iupac_name") or None,
                            banned_in=_parse_list(row.get("banned_in")),
                            at_risk_groups=_parse_list(row.get("at_risk_groups")),
                            source_url=row.get("source_url") or None,
                        )
                    )
        await session.commit()
        print(f"Seeded {len(seen)} regulatory additives")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Replace existing regulatory seed data")
    args = parser.parse_args()
    asyncio.run(seed(force=args.force))
