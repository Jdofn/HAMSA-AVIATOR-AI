# HAMSA AVIATOR AI — Phase 02

Foundation for a Telegram-based Aviator research system with defensive cybersecurity, offline capture imports, and historical analytics.

## Current scope
- FastAPI backend with health, database-health, and system-status endpoints.
- SQLAlchemy database setup and `round_results` table.
- Telegram bot with `/start` and `/status`.
- Railway Docker deployment configuration.
- Defensive security endpoints:
  - `GET /api/v1/security/scope` — permitted and prohibited research boundaries.
  - `POST /api/v1/security/crypto/inspect` — offline Base64/hex decoding and SHA-256 fingerprinting; decoding is not decryption.
  - `GET /api/v1/security/headers/check` — static API hardening recommendations.
- Offline data intelligence:
  - `POST /api/v1/data/datasets/inspect` — inspect requester-provided JSON/CSV in memory, calculate SHA-256, redact sensitive-key values, and return a sanitized preview.
  - `POST /api/v1/data/aviator/import` — normalize local Aviator capture CSV/JSON exports with round reference, multiplier, and timestamp.
- Historical Aviator analytics:
  - `POST /api/v1/aviator/analyze` — calculate mean, median, standard deviation, percentiles, threshold hit rates, multiplier distribution, streak summaries, recent-sample mean, and optional aggregate player/bet/prize metrics.
  - Analytics are descriptive only; no next-round predictions or betting signals are generated.
- Authorized protocol/cryptography lab:
  - `POST /api/v1/lab/protocol/inspect` — offline metadata validation and summary.
  - `POST /api/v1/lab/crypto/hmac/verify` — HMAC-SHA256/SHA512 verification with constant-time comparison.

## Capture compatibility
The offline importer supports JSON exports and the source project's six-column headerless CSV shape:
`Time, totalPlayers, totalBets, F, totalPrize, L`.
It also accepts headered CSV and JSON fields `F`, `L`, and `TS`. Numeric `TS` values are interpreted as Unix epoch milliseconds. Time-only values such as `HH:mm` are retained without inventing a calendar date.

The analytics endpoint accepts normalized multiplier records and optional aggregate metrics. It does not expose individual player identities or betting-account details. Imports and analytics are in-memory; they do not persist uploaded content.

Reference format: [an0nlk/1XBET_Crash_CF_Capture](https://github.com/an0nlk/1XBET_Crash_CF_Capture).

## Security and authorization boundary
Testing is limited to HAMSA-owned systems, isolated labs, or systems covered by explicit authorization. This project does not access third-party accounts or protected sessions, steal credentials/tokens, bypass authentication or anti-bot controls, intercept other users' traffic, or decrypt data without the required key and permission.

The reference repository's Puppeteer stealth/anti-detection automation and live third-party WebSocket capture are not included. The compatible workflow is user-provided exports or a source/API explicitly authorized for collection. No official or otherwise authorized 1xBet/Spribe results feed has been configured or verified.

Source and authorization declarations are supplied by the requester and are not independently verified. All imported records are marked unverified. Historical frequencies and Provably Fair checks do not predict future rounds or guarantee outcomes.

See:
- [Security research policy](docs/SECURITY_RESEARCH_POLICY.md)
- [Security roadmap](docs/ROADMAP_SECURITY_RESEARCH.md)
- [Phase 02 lab scope](docs/PHASE_02_LAB.md)

## Local setup
1. Install Python 3.12.
2. Create a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env`.
5. Run tests: `pytest -q`.
6. Start API: `uvicorn app.main:app --reload`.
7. Initialize DB: `python -m app.init_db`.

API docs: `http://127.0.0.1:8000/docs`.

## Telegram bot
Set `TELEGRAM_BOT_TOKEN` in `.env`, then run `python -m bot.main`. Run API and bot as separate Railway services.

## Railway deployment
Deploy this repository as an API service using the included Dockerfile and `railway.json`. Configure `DATABASE_URL`, `APP_ENV=production`, and `LOG_LEVEL=INFO`. For the bot, create a second service from the same repository with start command `python -m bot.main` and set `TELEGRAM_BOT_TOKEN`.

Do not commit `.env` or secrets.
