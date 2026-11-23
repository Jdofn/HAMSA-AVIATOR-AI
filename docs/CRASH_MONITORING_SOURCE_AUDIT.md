# External Source Audit — Zakaria-laktati Crash Monitoring

Repository: https://github.com/Zakaria-laktati/crash-1xbet-monitoring

## Finding: no documented REST API
The project describes and implements a persistent WebSocket collector, PostgreSQL storage, Streamlit dashboard, token-monitor service, and Docker Compose deployment. Its README lists a REST API as future TODO work. It is not a documented API client/library that can be plugged into HAMSA as an official API.

## Potentially useful research concepts
- Recent crash history and time-window summaries.
- Average, median, standard deviation, min/max, and percentile statistics.
- Distribution buckets and high-multiplier history.
- CSV export and collector/database health indicators.

HAMSA already has historical round storage, descriptive analytics, a dashboard, and source-quality monitoring. These concepts are largely covered; future UI improvements should reuse HAMSA data models and APIs rather than importing the Streamlit app or duplicating its database.

## Security and integration review
The collector instructions require copying a WebSocket request URL and session-related credentials from browser developer tools. The sample collector constructs a WebSocket URL with an access token and sends an account registration message. The dashboard also provides a workflow to persist a token in local YAML configuration. These session-capture and scraping components are not imported or enabled in HAMSA.

The inspected dashboard code includes a hard-coded database password fallback. This is not adopted. HAMSA must keep its own secrets in environment/deployment secret storage and must not request, log, or persist third-party browser session tokens.

## License
The repository includes MIT license text, but the copyright line still contains a placeholder ([Votre Nom]). This audit records the declared MIT license but does not copy source files. Confirm ownership/attribution before copying substantial code.

## HAMSA catalog endpoint
GET /api/v1/catalog/sportsbook/sources/crash-monitoring

The endpoint returns static audit metadata only. It makes no network requests to 1xBet, opens no WebSocket, and does not collect live data.

## Status
- Catalogued: yes.
- REST API available in source repository: no documented API identified.
- Code copied: no.
- Live connection enabled: no.
- Compatible as a reference for descriptive Aviator analytics: yes.
- Verified official 1xBet integration: no.