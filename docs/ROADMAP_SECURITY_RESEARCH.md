# Advanced Research & Cybersecurity Roadmap

## Phase 01A — Defensive foundation
- Scope policy and explicit third-party restrictions.
- Offline encoding/hash inspection endpoint.
- Static API hardening recommendations.
- Automated tests for scope and payload validation.

## Phase 01B — Authorized data analysis
- Import user-provided JSON/CSV/PCAP files with size limits.
- Normalize HTTP/WebSocket metadata from authorized captures.
- Redaction pipeline for cookies, authorization headers, and personal data.
- Dataset provenance and SHA-256 integrity records.

## Phase 02 — Cryptography and protocol lab
- Hash/HMAC/signature verification using user-owned data and authorized keys.
- TLS configuration review for HAMSA-owned deployments.
- Protocol schema registry and replayable synthetic fixtures.
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
