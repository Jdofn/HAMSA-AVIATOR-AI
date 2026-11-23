# HAMSA Security Research Policy

## Scope
HAMSA is a defensive research and analytics project. Security testing is limited to systems the operator owns or has explicit, documented authorization to assess. Third-party data may be analyzed only when it is lawfully obtained and its use is permitted.

## Allowed research
- Offline inspection of user-supplied captures, logs, JSON, binary files, and protocol samples.
- Parsing HTTP/WebSocket metadata from an authorized test environment.
- Base64/hex decoding, hashing, signature verification, and cryptographic experiments with owned data and authorized keys.
- Security review and testing of HAMSA, its APIs, database, Railway configuration, and isolated lab targets.
- Malware and exploit-behavior analysis in an isolated defensive lab, without deploying it against real third-party systems.
- Statistical analysis and verification of completed Aviator rounds from reliable, permitted sources.

## Prohibited operations
- Accessing 1xBet/Spribe accounts, infrastructure, private APIs, or protected sessions without authorization.
- Credential/session/token theft, phishing, interception of other users' traffic, or bypassing TLS, authentication, authorization, rate limits, or anti-bot controls.
- Exploiting vulnerabilities on third-party systems without written authorization.
- Decrypting data without the required key and permission, or attempting to recover another party's secrets.
- Treating historical multipliers or hash verification as a guaranteed prediction of future rounds.

## Data handling
- Do not commit tokens, passwords, private keys, cookies, or personal data.
- Redact secrets before uploading logs or packet captures.
- Record source, collection method, authorization basis, timestamp, and integrity hash for each research dataset.
- Keep test data separate from production data.

## 1xBet data-source status
No official or otherwise authorized 1xBet/Spribe results feed is configured or verified in this repository. Do not enable collection until a permitted source and its terms, authentication method, and schema have been documented.
