# Phase 05 — Source Health & Data Quality Monitor

## What this phase provides
- Protected operational endpoint: `GET /api/v1/aviator/monitor/quality`.
- Feed ingestion status: `no_data`, `receiving`, or `stale`, based on latest database ingestion time.
- Event freshness: `no_data`, `recent`, `old_events`, or `clock_skew`, based on event timestamps.
- Configurable stale threshold via `FEED_STALE_AFTER_SECONDS` (default 300; minimum effective value 30).
- Quality sample (up to 1,000 latest records): valid/invalid multipliers, missing aggregate metrics, future timestamps, missing round IDs, and a descriptive quality score.
- Per-source record counts.
- Explicit disclosure that historical duplicate submissions are not retained as audit events; deduplication remains enforced by batch logic and the database unique constraint.

## Access
Send `X-Dashboard-Token: <DASHBOARD_ACCESS_TOKEN>` in production. The monitor only queries HAMSA's own database; it does not probe any upstream host.

## Upstream adapter boundary
Phase 05 intentionally does not hard-code an upstream URL, credentials, browser automation, or undocumented 1xBet/SPRIBE protocol. A real connector can only be added once the operator supplies the official API documentation or other documented authorization, plus the permitted authentication method and data schema. Until then, the existing authenticated `POST /api/v1/aviator/feed/batch` is the normalized adapter contract.

## Interpretation
- `feed_status=receiving` means HAMSA has ingested a record recently; it does not prove the upstream service is online or the feed is complete.
- `event_freshness=clock_skew` indicates a future-dated event in the database.
- The quality score is the percentage of sampled records with a finite positive multiplier. Missing optional metrics are reported separately and do not reduce the score.
- Stored records remain unverified. No metric predicts future rounds or guarantees a betting outcome.
