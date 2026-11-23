# Phase 07 — Sportsbook Data Foundation

## Scope
Phase 07 adds a source-neutral storage and ingestion contract for normalized sportsbook fixtures and latest supplied 1X2 odds. It is isolated from Aviator models, analytics, and ingestion. It does not execute the reviewed PHP wrapper or call undocumented 1xBet endpoints.

## API
- `POST /api/v1/catalog/sportsbook/events/import` — authenticated batch upsert, max 250 events.
- `GET /api/v1/catalog/sportsbook/events?limit=50&offset=0` — authenticated fixture list.
- `GET /api/v1/catalog/sportsbook/summary` — authenticated aggregate counts.
- Existing metadata endpoint: `GET /api/v1/catalog/sportsbook/sources/1xbet-php`.

All import/read routes use `X-Dashboard-Token` when configured and fail closed in production if the token is missing.

## Normalized input
Required batch fields: `source`, `authorization_basis`, and `events`. Each event requires a stable `event_id`, `sport`, `home_team`, and `away_team`. Optional fields include `league`, timezone-aware `starts_at`, `event_status` (scheduled/live/finished/cancelled), and positive finite 1X2 odds fields `odds_home`, `odds_draw`, and `odds_away`.

Example:
```json
{
  "source": "authorized-provider-adapter",
  "authorization_basis": "Documented permission or official API agreement",
  "events": [{
    "event_id": "provider-event-123",
    "sport": "Football",
    "league": "Example League",
    "home_team": "Home FC",
    "away_team": "Away FC",
    "starts_at": "2026-11-24T18:00:00Z",
    "event_status": "scheduled",
    "odds_home": 1.85,
    "odds_draw": 3.2,
    "odds_away": 4.1
  }]
}
```

## Persistence and limitations
- New `sportsbook_events` table uses a unique provider/event ID pair.
- Repeated event IDs update the existing fixture and latest odds rather than inserting duplicate fixtures.
- This phase stores only the latest supplied 1X2 odds; historical odds movement and settlement are not retained.
- Source and authorization claims are caller-supplied and not independently verified.
- No provider credentials, polling worker, remote HTTP calls, or betting recommendations are included.
