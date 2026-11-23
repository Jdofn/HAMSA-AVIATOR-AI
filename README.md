# HAMSA AVIATOR AI — Phase 06

Personal Aviator research platform for offline capture imports, authorized signed live-data ingestion, persisted round history, historical analytics, and defensive security research.

## Current capabilities
- FastAPI backend, SQLAlchemy persistence, Telegram bot foundation, health and system status.
- Offline CSV/JSON import: `POST /api/v1/data/aviator/import`.
- Historical descriptive analytics: `POST /api/v1/aviator/analyze`.
- Authenticated normalized batch ingestion: `POST /api/v1/aviator/feed/batch` (dashboard token).
- **Phase 06 signed webhook ingestion:** `POST /api/v1/aviator/feed/webhook`.
  - HMAC-SHA256 signature over `timestamp + "." + exact raw request body`.
  - Headers: `X-HAMSA-Timestamp` (Unix seconds), `X-HAMSA-Signature` (`sha256=<hex>`).
  - Configurable timestamp tolerance (default five minutes; minimum 30 seconds), strict SHA-256 signature format, constant-time comparison, 256 KB body limit.
  - Uses the Phase 04 normalized event schema and existing idempotent database persistence.
- Quality monitor: `GET /api/v1/aviator/monitor/quality`.
- Dashboard: `GET /dashboard`.

## Source catalog categories

### Sportsbook — reviewed 1xBet PHP reference
- Catalog endpoint: `GET /api/v1/catalog/sportsbook/sources/1xbet-php`.
- Source: [LanceSpezzate/1xbet-api-php](https://github.com/LanceSpezzate/1xbet-api-php).
- Category covers sportsbook sports, leagues, matches, odds, event search, and video metadata.
- Review status: catalogued only; no live connection or remote requests are implemented.
- The PHP wrapper depends on `HTTP_SGET` and `need/ok_odds.json`; its license was not confirmed.
- **Not compatible with Aviator/Crash round analytics:** no Aviator round or multiplier methods were identified. Keep this category isolated from Aviator ingestion.

## Signed webhook configuration
Set `LIVE_FEED_WEBHOOK_SECRET` to a long random secret in the Railway service and in the authorized provider adapter's secret store. Never commit it or send it in chat. The webhook returns 503 until configured. Unlike dashboard APIs, the webhook authenticates using its HMAC signature and does not require `X-Dashboard-Token`.

The provider adapter must use official documentation and authorized access, normalize completed events into the Phase 04 `LiveFeedBatch` JSON schema, sign the exact serialized body, and send it to the webhook. Use stable round IDs and bounded retries; duplicate deliveries are safely skipped.

## Deployment and access protection
Set `APP_ENV=production`, a persistent PostgreSQL `DATABASE_URL`, and a strong `DASHBOARD_ACCESS_TOKEN`. Set `LIVE_FEED_WEBHOOK_SECRET` only if receiving signed webhooks. Do not put secrets in Git or chat.

## Scope and limitations
No 1xBet API endpoint, upstream connector, polling worker, or provider credentials are configured: no official 1xBet API documentation or authorized endpoint was supplied. This phase delivers the secure receiving contract, not a live connection to 1xBet. A provider-specific adapter requires official API documentation or written authorization plus its schema and authentication requirements. No stealth browser automation, protected-session extraction, third-party WebSocket interception, anti-bot bypass, or unauthorized decryption is included.

All received events remain `unverified`. HMAC proves message integrity and possession of the shared secret; it does not prove the underlying game result is authentic or that a source is authorized. Historical statistics do not predict future rounds.

## Local setup
1. Install Python 3.12.
2. Create and activate a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env`.
5. Run tests: `PYTHONPATH=. pytest -q`.
6. Start API: `uvicorn app.main:app --reload`.
7. Open `http://127.0.0.1:8000/dashboard`.

API docs: `http://127.0.0.1:8000/docs`.
