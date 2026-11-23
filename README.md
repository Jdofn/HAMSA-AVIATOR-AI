# HAMSA AVIATOR AI — Phase 02

Foundation for a Telegram-based Aviator research system with defensive cybersecurity and offline data-intelligence capabilities.

## Current scope
- FastAPI backend with health, database-health, and system-status endpoints.
- SQLAlchemy database setup and `round_results` table.
- Telegram bot with `/start` and `/status`.
- Railway Docker deployment configuration.
- Defensive security endpoints:
  - `GET /api/v1/security/scope` — permitted and prohibited research boundaries.
  - `POST /api/v1/security/crypto/inspect` — offline Base64/hex decoding, SHA-256 fingerprinting, and bounded previews. Decoding is not decryption.
  - `GET /api/v1/security/headers/check` — static API hardening recommendations; no remote scanning.
- Offline dataset intelligence:
  - `POST /api/v1/data/datasets/inspect` — inspect requester-provided JSON/CSV in memory.
  - Calculates SHA-256, reports columns and record count, redacts sensitive-key values, and returns a five-record sanitized preview.
  - Requires source and authorization-basis declarations.
  - Does not persist uploaded content; provenance claims are requester-supplied and are not independently verified.
- Automated API, security, and dataset tests.

## Security and authorization boundary
Testing is limited to HAMSA-owned systems, isolated labs, or systems covered by explicit authorization. The project does not access third-party accounts or protected sessions, steal credentials/tokens, bypass authentication or anti-bot controls, intercept other users' traffic, or decrypt data without the required key and permission.

Only upload data you are authorized to process. Secrets in JSON/CSV are redacted by sensitive field names before the preview is returned, but this is not a substitute for removing secrets before submission. Input is processed in memory and not saved by this endpoint.

See:
- [Security research policy](docs/SECURITY_RESEARCH_POLICY.md)
- [Security roadmap](docs/ROADMAP_SECURITY_RESEARCH.md)

## 1xBet/Spribe data-source status
No official or otherwise authorized 1xBet/Spribe results feed has been configured or verified. Do not enable collection until a permitted source, its terms, authentication method, schema, and provenance requirements have been documented. Historical results and Provably Fair verification do not guarantee prediction of future rounds.

## Local setup
1. Install Python 3.12.
2. Create a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`.
5. Run tests: `pytest -q`
6. Start API: `uvicorn app.main:app --reload`
7. Initialize DB: `python -m app.init_db`

API docs: `http://127.0.0.1:8000/docs`

## Telegram bot
Set `TELEGRAM_BOT_TOKEN` in `.env`, then run:
`python -m bot.main`

Run API and bot as separate Railway services. Add PostgreSQL and set `DATABASE_URL` to Railway's PostgreSQL connection variable.

## Railway deployment
Deploy this repository as an API service using the included Dockerfile and `railway.json`. Configure:
- `DATABASE_URL` = Railway PostgreSQL connection string
- `APP_ENV` = `production`
- `LOG_LEVEL` = `INFO`

For the bot, create a second service from the same repository with custom start command `python -m bot.main` and set `TELEGRAM_BOT_TOKEN`.

Do not commit `.env` or secrets.

## Phase 01B acceptance criteria
- Existing health and system endpoints remain available.
- Security scope and crypto inspection endpoints enforce bounded input.
- JSON/CSV dataset inspection requires provenance declarations, rejects invalid formats, redacts sensitive-key values, and does not persist submitted content.
- Official 1xBet/Spribe source remains unconfigured until independently verified.

## Phase 02 — Authorized protocol and cryptography lab
- `POST /api/v1/lab/protocol/inspect` validates and summarizes structured HTTP/WebSocket metadata exports in memory.
- Only allowlisted metadata headers are returned; cookies, authorization headers, custom headers, raw packet bodies, and query strings are excluded.
- `POST /api/v1/lab/crypto/hmac/verify` verifies HMAC-SHA256 or HMAC-SHA512 with a requester-provided key, using constant-time comparison. The key is not stored or returned.
- Source and authorization declarations are recorded as unverified requester claims.
- PCAP parsing, asymmetric signatures, live collection, and remote TLS probing remain deferred.

See [Phase 02 lab scope](docs/PHASE_02_LAB.md). All operations are offline and limited to data and keys you own or are authorized to use.


## Offline Aviator CF Capture compatibility
- `POST /api/v1/data/aviator/import` accepts user-supplied CSV/JSON exports containing `L`, `F`, and `TS` fields.
- Normalizes round reference, multiplier, and timestamp for research; numeric timestamps are interpreted as Unix milliseconds.
- Ignores player/bet/prize metrics, marks imported values unverified, and does not persist them.
- Does not include the reference repository's Puppeteer/stealth browser collector or WebSocket interception logic.
- Reference format: [an0nlk/1XBET_Crash_CF_Capture](https://github.com/an0nlk/1XBET_Crash_CF_Capture).
