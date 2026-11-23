# HAMSA AVIATOR AI — Phase 08

Personal Aviator research platform for authorized data ingestion, persisted round history, descriptive analytics, and defensive security research.

## Phase 08 — Advanced Distribution & Volatility Analytics

- `POST /api/v1/aviator/advanced-analyze` analyzes a caller-supplied historical sample.
- Distribution metrics: P05/P10/P25/P50/P75/P90/P95/P99, IQR, outlier flags, threshold rates, coefficient of variation.
- Rolling volatility: configurable window size (2–500), rolling mean, population standard deviation, and coefficient of variation.
- Time-of-day grouping: timestamped rounds are normalized to UTC and summarized by hour.
- Requires at least two rounds; maximum 10,000; timestamps must include an explicit timezone.
- Descriptive research only. No next-round prediction, betting signal, or guaranteed outcome.

## Current data connectivity status

- No official, publicly documented 1xBet/SPRIBE Aviator historical-round read API has been verified or configured in this repository.
- The reviewed Aviator Studio integration documentation describes casino/operator integration: provider-issued public key and provider ID, partner-generated launch token, and provider-to-partner callbacks for account/balance/round events. It is not a public endpoint for arbitrary third parties to read all Aviator multipliers.
- HAMSA therefore keeps the signed webhook receiver and normalized authorized-feed ingestion contract. A real upstream connection requires written authorization, partner credentials, an approved event schema, and a provider endpoint/feed specification.
- Do not place 1xBet account passwords, browser cookies, session tokens, or private keys in source control or logs.

## Existing capabilities retained

- FastAPI backend, SQLAlchemy persistence, additive database migration, health/status endpoints.
- Offline JSON/CSV import: `POST /api/v1/data/aviator/import`.
- Historical descriptive analytics: `POST /api/v1/aviator/analyze`.
- Persisted history: `GET /api/v1/aviator/rounds` and `GET /api/v1/aviator/summary`.
- Dashboard: `GET /dashboard`; signed live-feed receiver: `POST /api/v1/aviator/feed/webhook`.
- Source health monitor: `GET /api/v1/aviator/monitor/quality`.
- Sportsbook event foundation remains separate from Aviator round data.

## Security and provenance

The supported ingestion workflow is user-provided local exports or a source/API explicitly authorized for this use. HMAC confirms integrity and shared-secret possession, not upstream authenticity. Source and authorization declarations are requester-supplied and are not independently verified. Imported data remains unverified unless a separate verification mechanism establishes otherwise.

## Setup

1. Python 3.12.
2. `pip install -r requirements.txt`.
3. Configure `.env` from `.env.example`.
4. Run `PYTHONPATH=. pytest -q`.
5. Start with `uvicorn app.main:app --reload`.
6. API docs at `/docs`.

For production, configure `APP_ENV=production`, persistent PostgreSQL `DATABASE_URL`, and a long random `DASHBOARD_ACCESS_TOKEN`. Never commit secrets.

## Deployment on Railway

Deploy from this repository using the included `Dockerfile` and `railway.json`. The configured health-check path is `/health`.

Required production configuration:
- `APP_ENV=production`
- `DATABASE_URL`: persistent PostgreSQL connection string. Do not use ephemeral SQLite storage for production history.
- `DASHBOARD_ACCESS_TOKEN`: long, randomly generated secret used to protect dashboard data operations.
- `LOG_LEVEL=INFO`

Optional configuration:
- `LIVE_FEED_WEBHOOK_SECRET`: set only when an authorized sender will post signed feed batches.
- `LIVE_FEED_WEBHOOK_TOLERANCE_SECONDS=300`
- `FEED_STALE_AFTER_SECONDS=300`

Never commit secrets, cookies, account passwords, or provider credentials. Configure secrets in Railway's service variables. The API service starts by running `python -m app.init_db` and then Uvicorn. A Telegram bot, if enabled, should be deployed as a separate service with `TELEGRAM_BOT_TOKEN` configured only there.

## Earlier implementation phases

- Phase 01–03: API foundation, defensive research utilities, offline data import, persisted round history, and dashboard.
- Phase 04: authorized normalized live-feed ingestion — see [Phase 04 documentation](docs/PHASE_04_LIVE_FEED.md).
- Phase 05: stored-source freshness and data-quality monitoring — see [Phase 05 documentation](docs/PHASE_05_SOURCE_MONITOR.md).
- Phase 06: signed HMAC live-feed webhook receiver — see [Phase 06 documentation](docs/PHASE_06_LIVE_DATA_INTEGRATION.md).
- Phase 07: separate sportsbook event data foundation — see [Phase 07 documentation](docs/PHASE_07_SPORTSBOOK_DATA.md).

## External source audits

- [1xBet / Aviator connectivity assessment](docs/1XBET_AVIATOR_CONNECTIVITY_ASSESSMENT.md): no public third-party Aviator historical-round read API has been verified; a production connector requires authorized provider access and a documented schema.
- [Crash monitoring repository audit](docs/CRASH_MONITORING_SOURCE_AUDIT.md): the reviewed project is a WebSocket collector and dashboard, not a ready-made REST API. Session-token harvesting and credential scraping are not included in HAMSA.
