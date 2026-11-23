# Phase 04 — Authorized Live Feed Adapter

## Scope
Phase 04 adds a bounded, authenticated ingestion contract for normalized round events supplied by an adapter that the operator is authorized to use. It is intentionally source-agnostic and does not connect to 1xBet or SPRIBE.

## Endpoint
- `POST /api/v1/aviator/feed/batch`
- Header: `X-Dashboard-Token: <DASHBOARD_ACCESS_TOKEN>`
- Maximum 250 records per request.
- Required batch provenance: `source` and `authorization_basis` (operator-supplied, not independently verified).
- Each record requires a stable `round_id` and positive finite `multiplier`; optional event timestamp must include a timezone.
- Optional `time_of_day`, `players`, `bets`, and `prize` fields are validated.
- Duplicate event IDs are skipped within the `authorized_live_feed` provider namespace.
- Events are persisted transactionally and appear in the existing rounds and summary APIs.

## Example request
```json
{
  "source": "operator-authorized-adapter",
  "authorization_basis": "Documented permission for this data source",
  "records": [
    {
      "round_id": "round-2026-0001",
      "multiplier": 2.35,
      "occurred_at": "2026-11-23T18:30:00Z",
      "players": 12,
      "bets": 18,
      "prize": 42
    }
  ]
}
```

## Dashboard refresh
The dashboard polls the authenticated summary and latest-history endpoints every five seconds while its browser tab is visible. The token remains in the in-memory password field and is not persisted to browser storage. Polling pauses while the tab is hidden.

## Security and limitations
- This is an ingestion interface, not a scraper or a prediction engine.
- No stealth browser automation, session-cookie extraction, third-party WebSocket interception, credential capture, anti-bot bypass, or decryption of protected traffic is implemented.
- The caller must ensure its source and collection method are authorized.
- Records remain marked `unverified`; this does not verify Provably Fair results.
- Historical statistics do not predict upcoming multipliers or provide guaranteed betting signals.
- Production must set `APP_ENV=production`, persistent PostgreSQL `DATABASE_URL`, and a strong `DASHBOARD_ACCESS_TOKEN`.
