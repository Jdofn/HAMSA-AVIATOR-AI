# 1xBet / Aviator connectivity assessment

## Finding

No official, publicly documented 1xBet/SPRIBE endpoint for arbitrary third-party retrieval of all Aviator round multipliers was verified during this review.

The publicly accessible Aviator Studio integration documentation describes the casino/operator integration contract. It requires provider-issued integration values such as a public key and provider ID, and documents partner-side launch authentication plus provider callbacks for account, balance, and round lifecycle events. This is not a public historical-round data API for an unaffiliated research client.

## HAMSA implementation decision

- Keep the signed HMAC webhook receiver as the supported integration boundary.
- Do not harvest browser cookies, user access tokens, private WebSocket sessions, or account credentials.
- Do not attempt authentication bypass, anti-bot evasion, or decryption of protected traffic.
- Enable a production adapter only after the operator/provider supplies written authorization, endpoint details, credentials, and a documented payload schema.
- Treat every ingested round as unverified until the source authenticity and integrity can be independently established.

## Public documentation reviewed

- Aviator Studio game launch integration: https://docs.crash.aviator.studio/game-integration/launch-game/
- Aviator Studio integration endpoints: https://docs.crash.aviator.studio/game-integration/integration-endpoints/
- Aviator Studio provider configuration API: https://docs.crash.aviator.studio/provider-configs/

No external service was called with user credentials and no live 1xBet account was accessed.