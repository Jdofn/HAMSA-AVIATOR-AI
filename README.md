# HAMSA AVIATOR AI — Phase 03

Personal Aviator research platform for offline capture imports, persisted round history, historical analytics, and defensive security research.

## Current capabilities
- FastAPI backend with health and system-status endpoints.
- SQLAlchemy database and additive startup migration for round metadata.
- Telegram bot foundation with `/start` and `/status`.
- Offline JSON/CSV import compatible with the reference capture file formats:
  - `POST /api/v1/data/aviator/import`
  - Supports `F`, `L`, `TS` and the six-column headerless CSV format `Time,totalPlayers,totalBets,F,totalPrize,L`.
  - Persists normalized rounds in `round_results`, including aggregate players/bets/prize metrics, source label, file name, and import batch SHA-256.
  - Deduplicates by provider + source round reference; when no reference exists, uses a stable batch-hash/row key.
  - Limits uploads to 1 MB and 10,000 rows.
- Historical analytics:
  - `POST /api/v1/aviator/analyze` — mean, median, standard deviation, percentiles, multiplier distribution, threshold hit rates, streaks, and recent-sample mean.
  - Descriptive only; no next-round prediction or betting signals.
- Persisted history API:
  - `GET /api/v1/aviator/rounds?limit=50&offset=0`
  - `GET /api/v1/aviator/summary`
- Responsive dashboard:
  - `GET /dashboard`
  - Upload a local CSV/JSON export, save it to the configured database, view aggregate statistics, chart recent multipliers, and browse paginated history.
- Defensive security endpoints and offline HMAC verification remain available under `/api/v1/security` and `/api/v1/lab`.

## Dashboard setup and access protection
Set these Railway/service variables:
- `APP_ENV=production`
- `DATABASE_URL` — use a persistent PostgreSQL database for production; ephemeral container storage is not suitable for durable SQLite history.
- `DASHBOARD_ACCESS_TOKEN` — a long, random secret. The dashboard sends it as `X-Dashboard-Token` for import and history APIs.

In production, stored-history and import APIs fail closed if `DASHBOARD_ACCESS_TOKEN` is missing. The dashboard page itself can load without the token, but data operations require it. The token is held in the page's password field only; it is not saved to browser storage.

For local development, the token is optional. Do not commit secrets or place the token in the repository.

## Database behavior
- Docker startup runs `python -m app.init_db`, which creates missing tables and adds new columns without dropping existing round data.
- Existing rows are retained. Rows imported from time-only `HH:mm` exports preserve the original time-of-day; the required legacy `occurred_at` field receives an ingestion-time fallback, not an invented event date.
- Imports are committed transactionally. Duplicate rows are skipped; failed batches are rolled back.
- The import endpoint returns a batch hash and inserted/duplicate counts.

## Capture compatibility and limitations
Reference format: [an0nlk/1XBET_Crash_CF_Capture](https://github.com/an0nlk/1XBET_Crash_CF_Capture).

This project does not include stealth/anti-detection automation, protected-session extraction, third-party WebSocket interception, credential collection, or bypasses of authentication and anti-bot controls. The supported workflow is user-provided local exports or a data source/API that is explicitly authorized.

Source and authorization declarations are supplied by the requester and are not independently verified. Imported values remain marked `unverified`. Historical frequencies, streaks, and Provably Fair checks do not predict future rounds or guarantee outcomes.

## Local setup
1. Install Python 3.12.
2. Create and activate a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env`.
5. Run tests: `PYTHONPATH=. pytest -q`.
6. Start API: `uvicorn app.main:app --reload`.
7. Open `http://127.0.0.1:8000/dashboard`.

API docs: `http://127.0.0.1:8000/docs`.

## Railway deployment
Deploy using the included Dockerfile and `railway.json`. Configure `APP_ENV=production`, `DATABASE_URL`, `DASHBOARD_ACCESS_TOKEN`, and `LOG_LEVEL=INFO`. Use Railway PostgreSQL or another persistent PostgreSQL service for retained history.

The API and Telegram bot may run as separate Railway services. Set `TELEGRAM_BOT_TOKEN` only on the bot service.
