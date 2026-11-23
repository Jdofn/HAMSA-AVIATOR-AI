# Phase 06 — Signed Live Data Integration

## Delivered integration contract
HAMSA now exposes `POST /api/v1/aviator/feed/webhook` for an upstream provider that the operator is authorized to use. The provider must transform its documented response into the normalized `LiveFeedBatch` JSON schema already used by Phase 04.

Required headers:
- `X-HAMSA-Timestamp`: Unix timestamp in seconds.
- `X-HAMSA-Signature`: `sha256=<hex>`.

Signature is HMAC-SHA256 over the exact bytes `timestamp + "." + raw_request_body`, using `LIVE_FEED_WEBHOOK_SECRET`. Requests outside a five-minute clock-skew window are rejected. The endpoint caps the body at 256 KB, validates the normalized schema, and reuses Phase 04 persistence/idempotency behavior. It does not require the dashboard token because the webhook HMAC is its independent authentication mechanism.

## Provider adapter contract
An authorized provider adapter must:
1. Follow the provider's official API documentation and terms.
2. Authenticate to that provider using its documented mechanism, with credentials stored only in deployment environment variables.
3. Map each completed round into `round_id`, `multiplier`, and optional timezone-aware `occurred_at`, `time_of_day`, `players`, `bets`, and `prize`.
4. POST the JSON batch to the HAMSA webhook and sign the exact serialized request body.
5. Retry transient failures with bounded exponential backoff and a stable round ID; database idempotency prevents duplicate storage.

No upstream client, polling schedule, provider credentials, or 1xBet endpoint is configured in this phase. No undocumented API, browser session, protected WebSocket, stealth automation, or anti-bot bypass is used. A real provider-specific connector remains blocked until official API documentation or written authorization and its schema/authentication details are supplied.

## Deployment
Set `LIVE_FEED_WEBHOOK_SECRET` to a long random secret in Railway and in the authorized provider adapter's secret store. Never commit it or send it in chat. Keep `APP_ENV=production` and a persistent PostgreSQL `DATABASE_URL` configured. Rotate the secret if exposed.

## Validation and limitations
Automated tests cover missing configuration, valid signature, duplicate delivery, tampered payload, and stale timestamp. Events remain `unverified`; a valid webhook signature authenticates the sender/payload integrity, not the truth of game outcomes or authorization claims. Historical analytics are descriptive and do not predict future rounds.
