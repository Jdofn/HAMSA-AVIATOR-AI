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