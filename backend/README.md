# Product Review Backend

FastAPI backend for the Product Review iOS app: ingredient scanning, regulatory enrichment (FDA/EU/FSSAI), health scoring, user profiles, and dashboard APIs.

## Virtual environment (required)

Dependencies **must** be installed into the project venv at the workspace root:

```
Product Review/
├── .venv/          ← Python virtual environment lives here
└── backend/        ← FastAPI app
```

Do **not** use system `pip` or `python` — on macOS they often point outside the project and cause dependency errors.

### Recommended setup

```bash
# From workspace root (Product Review/)
cd backend
bash scripts/setup_dev.sh
source ../.venv/bin/activate
cp .env.example .env
```

Or manually:

```bash
# From workspace root
source .venv/bin/activate
cd backend
python -m pip install -e ".[dev]"
```

Verify you are using the venv:

```bash
which python   # should end in .../Product Review/.venv/bin/python
pip check      # should report: No broken requirements found
```

### Python version

- **Recommended:** Python 3.12 (matches Docker image)
- **Supported:** 3.11+ (your `.venv` uses 3.14 — that is fine if `pip install` succeeds)
- For fewer wheel issues, prefer 3.12 (matches Docker)

## Quick start

```bash
source ../.venv/bin/activate   # from backend/
docker compose up -d postgres redis
python scripts/seed_regulatory.py   # run from backend/ with venv activated
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Docker (full stack)

Docker uses its own Python 3.12 environment — no local venv needed:

```bash
docker compose up --build
docker compose --profile dev up -d ollama  # optional local models
```

## Environment

See `.env.example`. Key settings:

| Variable | Description |
|---|---|
| `AUTH_PROVIDER` | `local` or `supabase` |
| `PIPELINE_PHASE` | `build` (Groq all stages) or `local` (specialized models) |
| `GROQ_API_KEY` | Required for Phase A pipeline |
| `TAVILY_API_KEY` | Stage 3 regulatory search |

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/v1/auth/register` | Sign up (local mode) |
| POST | `/v1/auth/login` | Login (local mode) |
| GET | `/v1/auth/me` | Current user |
| GET/PATCH | `/v1/profile` | User profile |
| GET | `/v1/dashboard/summary` | Health overview |
| POST | `/v1/scan` | Analyze product |
| GET | `/v1/scans/{id}` | Scan + ingredient list + `tier_counts` |
| GET | `/v1/scans/{id}/ingredients/{ingredient_id}` | IngredientIQ detail sheet + prev/next nav |
| GET/POST/DELETE | `/v1/watchlist/ingredients` | Bookmark ingredients |
| GET | `/v1/scans` | Scan history |

## Tests

```bash
source ../.venv/bin/activate
pytest
```

## Troubleshooting dependency errors

| Problem | Fix |
|---|---|
| `command not found: pip` | Activate venv: `source ../.venv/bin/activate` |
| Packages installed but import fails | Confirm `which python` points to `.venv/bin/python` |
| `passlib` / `bcrypt` errors | Reinstall in venv: `pip install "bcrypt>=4.0.0,<4.1.0" passlib[bcrypt]` |
| Python 3.14 wheel errors | Recreate venv with 3.12: `python3.12 -m venv ../.venv` then re-run `setup_dev.sh` |
| Locked reproducible install | `pip install -r requirements-lock.txt` (inside activated venv) |
