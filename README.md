# HAMSA AVIATOR AI — Phase 01A

Foundation for a Telegram-based Aviator research system with a defensive security research API.

## Current scope
- FastAPI backend with health, database-health, and system-status endpoints.
- SQLAlchemy database setup and `round_results` table.
- Telegram bot with `/start` and `/status`.
- Railway Docker deployment configuration.
- Defensive security research endpoints:
  - `GET /api/v1/security/scope` — documents permitted and prohibited research boundaries.
  - `POST /api/v1/security/crypto/inspect` — offline Base64/hex decoding, SHA-256 fingerprinting, and bounded previews. Decoding is not decryption.
  - `GET /api/v1/security/headers/check` — static API hardening recommendations; it does not scan remote hosts.
- Automated API and security tests.

## Security and authorization boundary
Testing is limited to HAMSA-owned systems, isolated labs, or systems covered by explicit authorization. The project does not access third-party accounts or protected sessions, steal credentials/tokens, bypass authentication or anti-bot controls, intercept other users' traffic, or decrypt data without the required key and permission.

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

## Phase 01A acceptance criteria
- Existing API health and system endpoints remain available.
- Security scope endpoint clearly reports research boundaries.
- Crypto inspection accepts bounded Base64/hex/UTF-8 input and returns a SHA-256 fingerprint.
- Invalid or oversized input is rejected.
- Static header guidance does not perform remote scanning.
- Official 1xBet/Spribe source remains marked unconfigured until independently verified.
