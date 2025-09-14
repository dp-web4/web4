# Web4 Witness Interop Vectors (Unsigned)

Roles covered:
- time
- audit-minimal
- oracle

For each role, we provide:
- JOSE/JSON vector: protected header, payload, `signing_input` and its SHA-256.
- COSE/CBOR vector: protected headers (diagnostic), protected bstr (base64url), canonical payload CBOR (hex), `Sig_structure` (hex) and SHA-256.

Common fields:
- ts: 2025-09-11T15:00:02Z
- subject: w4idp:ABCD-EXAMPLE
- event_hash: deadbeefcafebabe1122334455667788
- policy: role-specific
- nonce: AQIDBAU=

Usage:
- JOSE: Sign `signing_input` with ES256 and append base64url(signature).
- COSE: Sign `Sig_structure` with Ed25519 and place in `COSE_Sign1.sig`.
