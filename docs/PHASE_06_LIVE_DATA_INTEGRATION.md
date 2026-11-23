# Phase 06 — Signed live-data webhook

## Scope
Phase 06 adds a source-neutral, authenticated webhook boundary. It accepts normalized round batches from a sender the operator is authorized to use. It does **not** connect to 1xBet, scrape a browser, capture sessions, inspect third-party WebSocket traffic, or bypass access controls.

## Endpoint
`POST /api/v1/aviator/feed/webhook`

The request body uses the existing `LiveFeedBatch` JSON schema from Phase 04:
```json
{
  "source": "your-authorized-provider",
  "authorization_basis": "documented permission or official API agreement",
  "records": [
    {"round_id": "provider-round-123", "multiplier": 2.15, "occurred_at": "2026-11-23T20:00:00Z"}
  ]
}
```

## Authentication
Configure `LIVE_FEED_WEBHOOK_SECRET` as a long random secret in the deployment environment. The sender must include:
- `X-HAMSA-Timestamp`: Unix timestamp in seconds.
- `X-HAMSA-Signature`: `sha256=<lowercase hex HMAC>`.

Signature input is the exact byte sequence `timestamp + "." + raw_request_body`, encoded as UTF-8 for the timestamp and concatenated with the unmodified body. HMAC algorithm: SHA-256. Example sender pseudocode:

```python
import hashlib, hmac, time
timestamp = str(int(time.time()))
signed = timestamp.encode() + b"." + raw_body
digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
headers = {
    "X-HAMSA-Timestamp": timestamp,
    "X-HAMSA-Signature": "sha256=" + digest,
}
```

The server rejects missing configuration (503), malformed/missing headers (401), invalid signatures (401), timestamps outside the configured tolerance (default 300 seconds; minimum effective tolerance 30 seconds) (401), and bodies larger than 256 KB (413). Comparison is constant-time. Round IDs are deduplicated by the existing database uniqueness constraint and ingestion logic. The timestamp window limits stale replays; round-level idempotency prevents duplicate round insertion.

## Deployment
Set `LIVE_FEED_WEBHOOK_SECRET` and optionally `LIVE_FEED_WEBHOOK_TOLERANCE_SECONDS=300` in Railway or the hosting environment. Keep the secret out of Git, source code, URLs, and chat. Rotate it if exposed. Existing dashboard token protection remains separate and unchanged.

## Provider integration contract
The upstream connector must be implemented on the sender side or as a separately reviewed provider adapter using official documentation and approved credentials. It must normalize only fields supported by the endpoint: `round_id`, positive finite `multiplier`, timezone-aware `occurred_at` (optional), and optional aggregate metrics. Never send account credentials, cookies, session tokens, player identifiers, or unrelated personal data.

## Limitations
A successful webhook response means HAMSA accepted and stored a structurally valid signed payload. It does not independently prove the source's authenticity, authorization, completeness, or game-result verification. Records remain `unverified`. Historical analytics are descriptive and are not next-round predictions or betting signals.


## Assessment of the supplied `LanceSpezzate/1xbet-api-php` file

The supplied `_1xbet.php` was reviewed as a candidate source. It is a PHP wrapper for sportsbook data, not an Aviator/Crash feed:
- It calls `LiveFeed` / `LineFeed` methods such as `GetSportsShortZip`, `GetChampsZip`, `Get1x2_Zip`, `BestGamesExtZip`, `GetChampZip`, `GetGameZip`, and `Web_SearchZip`.
- Its exposed methods cover sports, leagues, matches, odds, search, and video metadata; no Aviator round/multiplier endpoint or Crash-specific method is present.
- It depends on an external `HTTP_SGET` helper and `need/ok_odds.json`; the supplied PHP file alone is not self-contained.
- The repository README only describes the project as a 1xbet.com API PHP project. No LICENSE file was found at the repository root, so copying the source wholesale into HAMSA is not assumed to be licensed.

**Decision:** do not wire this wrapper into the Aviator ingestion pipeline. It would provide the wrong data domain and could not produce valid round multipliers. Keep it as a reviewed reference only. Reconsider it only if HAMSA's scope expands to sportsbook data and the endpoint usage, terms, and code license are confirmed. For Aviator, a separate authorized Crash/Aviator data source or official interface is still required.
