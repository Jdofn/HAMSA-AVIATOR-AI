# Advanced Research & Cybersecurity Roadmap

## Phase 01A — Defensive foundation
- Scope policy and explicit third-party restrictions.
- Offline encoding/hash inspection endpoint.
- Static API hardening recommendations.
- Automated tests for scope and payload validation.

## Phase 01B — Offline data intelligence (implemented in branch)
- JSON/CSV dataset inspection in memory.
- Requester-supplied source and authorization-basis metadata.
- SHA-256 integrity fingerprint.
- Sensitive-key redaction before preview.
- Bounded input, filename validation, and automated tests.
- No persistence of submitted raw content.

## Phase 02 — Authorized protocol and cryptography lab
- Parse sanitized HTTP/WebSocket metadata exports from owned or explicitly authorized test environments.
- Add PCAP metadata parsing only after format, resource, and privacy safeguards are implemented.
- Hash/HMAC/signature verification using user-owned data and authorized keys.
- TLS configuration review for HAMSA-owned deployments.
- Protocol schema registry and synthetic replay fixtures.
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
