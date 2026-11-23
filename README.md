# HAMSA AVIATOR AI — Phase 05

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
  - Upload a local CSV/JSON export, save it to the configured database, view aggregate statistics, chart recent multipliers, and browse paginated history. The dashboard refreshes saved summary/history every five seconds while the tab is visible.
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



## Phase 06 — Signed Live Data Webhook

- `POST /api/v1/aviator/feed/webhook` accepts normalized batches from an explicitly authorized sender.
- HMAC-SHA256 signs the exact request bytes and Unix timestamp using `X-HAMSA-Timestamp` and `X-HAMSA-Signature` headers.
- Timestamp tolerance defaults to 300 seconds; request bodies are capped at 256 KB while streaming; duplicate round IDs are skipped.
- Configure `LIVE_FEED_WEBHOOK_SECRET` in the deployment environment. HMAC confirms message integrity and shared-secret possession, not the truth or authorization of the upstream data.
- This is a receiver only; no live 1xBet/SPRIBE connector is configured.

## Source Catalog — Sportsbook

- Read-only metadata endpoint: `GET /api/v1/catalog/sportsbook/sources/1xbet-php`.
- Catalog entry for [LanceSpezzate/1xbet-api-php](https://github.com/LanceSpezzate/1xbet-api-php), covering sports, leagues, matches, odds, search, and video metadata.
- The source is catalogued but not connected; it depends on `HTTP_SGET` and `need/ok_odds.json`, and its license is unconfirmed.
- It is not an Aviator/Crash feed and is kept separate from Aviator ingestion.

## Railway deployment
Deploy using the included Dockerfile and `railway.json`. Configure `APP_ENV=production`, `DATABASE_URL`, `DASHBOARD_ACCESS_TOKEN`, and `LOG_LEVEL=INFO`. Use Railway PostgreSQL or another persistent PostgreSQL service for retained history.

The API and Telegram bot may run as separate Railway services. Set `TELEGRAM_BOT_TOKEN` only on the bot service.
\n\n## Phase 04 — Authorized live feed\nSee [Phase 04 implementation and request contract](docs/PHASE_04_LIVE_FEED.md). This is an authenticated ingestion adapter, not a 1xBet scraper. The operator is responsible for ensuring that the upstream source and collection method are authorized. No browser-session extraction, protected WebSocket interception, anti-bot bypass, or prediction logic is included.\n

## Phase 05 — Source health & data quality
See [Phase 05 monitor documentation](docs/PHASE_05_SOURCE_MONITOR.md). Monitoring is based only on records already stored by HAMSA; no upstream service is probed. A real external adapter requires official API documentation or documented authorization and an approved schema/authentication method.


## Phase 07 — Sportsbook Data Foundation

- `POST /api/v1/catalog/sportsbook/events/import` accepts up to 250 normalized event records from an explicitly authorized source.
- `GET /api/v1/catalog/sportsbook/events` lists saved fixtures; `GET /api/v1/catalog/sportsbook/summary` reports event counts and statuses.
- Stores event identity, sport/league, home/away teams, scheduled start, status, and latest supplied 1X2 odds. Existing event IDs are updated rather than duplicated.
- Import and read endpoints use the existing dashboard access token. The catalog metadata endpoint remains read-only.
- This is an ingestion contract, not a live 1xBet connector. The supplied PHP wrapper has not been executed; its undocumented endpoint usage and license remain unconfirmed. Only authorized normalized data should be submitted.
- Historical odds movement, settlement, and betting recommendations are outside this phase. Data remains source-supplied and unverified.


## External Crash Monitoring Reference Audit

The repository [Zakaria-laktati/crash-1xbet-monitoring](https://github.com/Zakaria-laktati/crash-1xbet-monitoring) has been reviewed and catalogued at GET /api/v1/catalog/sportsbook/sources/crash-monitoring. It implements a WebSocket scraper and Streamlit/PostgreSQL monitor; no documented REST API was identified (REST API is listed as future work). Its dashboard/statistical concepts overlap with HAMSA's existing analytics. Session-token capture, account registration, and scraping code are not imported. See docs/CRASH_MONITORING_SOURCE_AUDIT.md.
