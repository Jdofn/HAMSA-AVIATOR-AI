# HAMSA AVIATOR AI — Phase 01

Foundation scaffold for a Telegram-based research system.

## Current scope
- FastAPI backend with root, health, database-health and system-status endpoints.
- SQLAlchemy database setup and `round_results` table.
- Telegram bot with `/start` and `/status`.
- Railway Docker deployment configuration.
- Basic automated API tests.

## Important data-source limitation
No official 1xBet/Spribe results API has been configured or verified. This project does not scrape protected sessions, bypass access controls, or treat sample data as official. Phase 02 must establish a permitted source and document its terms, authentication, schema, and provenance.

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

Run the API and bot as separate Railway services. Add a PostgreSQL service and set `DATABASE_URL` to Railway's PostgreSQL connection variable for production.

## Railway deployment
Deploy this repository as an API service using the included Dockerfile and `railway.json`. Configure:
- `DATABASE_URL` = Railway PostgreSQL connection string
- `APP_ENV` = `production`
- `LOG_LEVEL` = `INFO`

For the bot, create a second service from the same repository with a custom start command:
`python -m bot.main`
and set `TELEGRAM_BOT_TOKEN`.

Do not commit `.env` or secrets.

## Phase 01 acceptance criteria
- API starts.
- `/health` returns `{"status":"ok","service":"api"}`.
- `/health/database` can reach the configured database.
- `/api/v1/status` reports official data source as not configured until verified.
- Telegram `/start` and `/status` respond after a valid bot token is configured.
