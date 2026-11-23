# Phase 02 — Authorized Protocol & Cryptography Lab

## Implemented
- Structured HTTP request/response and WebSocket metadata inspection from user-supplied exports.
- Strict event-shape validation and a 1,000-event request limit.
- Allowlist-only response headers; unapproved headers (including cookies, authorization, tokens, and arbitrary custom headers) are omitted.
- Route templates only; no query strings or raw packet bodies.
- Requester-supplied source and authorization-basis declarations, clearly marked unverified.
- In-memory HMAC-SHA256 and HMAC-SHA512 verification with constant-time digest comparison.
- No raw capture ingestion, network calls, persistence of supplied keys, or remote target scanning.

## Deferred
- PCAP parsing: deferred until dedicated resource limits, privacy review, and parser hardening are added.
- Asymmetric public-key signatures: deferred until dependency and key-format decisions are reviewed.
- Live HTTP/WebSocket collection and TLS probing: not implemented; no third-party traffic is intercepted or scanned.

## Authorization boundary
Use only synthetic data, systems owned by the operator, or environments covered by explicit written authorization. Do not submit third-party credentials, cookies, session identifiers, private keys, or personal data. The API cannot independently verify the requester's authorization declaration.


## Offline compatibility adapter
HAMSA includes a clean-room importer for local CSV/JSON exports in the reference capture format (`L`, `F`, `TS`). It ignores player/bet/prize totals, normalizes timestamps, and marks every multiplier unverified. It performs no browser automation, WebSocket interception, network collection, or persistence. The reference repository's active capture and stealth components are intentionally not copied or integrated.
