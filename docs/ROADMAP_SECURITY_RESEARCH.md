# Advanced Research & Cybersecurity Roadmap

## Phase 01A — Defensive foundation
- Scope policy and explicit third-party restrictions.
- Offline encoding/hash inspection endpoint.
- Static API hardening recommendations.
- Automated tests for scope and payload validation.

## Phase 01B — Offline data intelligence (merged to main)
- JSON/CSV dataset inspection in memory.
- Requester-supplied source and authorization-basis metadata.
- SHA-256 integrity fingerprint.
- Sensitive-key redaction before preview.
- Bounded input, filename validation, and automated tests.
- No persistence of submitted raw content.

## Phase 02 — Authorized protocol and cryptography lab (implemented core)
- Structured HTTP/WebSocket metadata validation and allowlist-only header summaries.
- In-memory HMAC-SHA256/HMAC-SHA512 verification with constant-time comparison.
- Requester-supplied provenance claims explicitly marked unverified.
- Automated tests for protocol shape, header filtering, provenance, and HMAC.
- PCAP parsing, asymmetric signatures, live collection, and remote TLS probing deferred pending separate safeguards.
- No credential extraction, third-party interception, or access-control bypass.

## Phase 03 — HAMSA security testing
- Dependency and secret scanning in CI.
- API authorization and input-validation tests.
- Database least-privilege and backup checks.
- Railway deployment configuration review.
- Isolated intentionally vulnerable lab exercises.

## Phase 04 — Aviator research intelligence
- Permitted historical-data ingestion with provenance.
- Distribution, volatility, streak, and independence analysis.
- Backtesting with train/test separation and leakage controls.
- Model calibration and transparent uncertainty reporting.
- No guaranteed next-round prediction claims.
