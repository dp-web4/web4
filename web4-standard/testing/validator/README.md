# Web4 Interop Vector Validator

This utility validates **canonicalization and encoding** for Web4 interop vectors.

It covers:
- **JOSE/JSON**: recompute JCS-canonical header & payload, rebuild `signing_input`, and compare its SHA-256.
- **COSE/CBOR**: rebuild `Sig_structure` bytes from the protected header bstr and payload CBOR; compare its SHA-256.

> Note: This tool does **not** perform cryptographic signature verification. Use your crypto library to verify Ed25519 (COSE) or ES256 (JOSE) signatures. This script ensures the bytes you signed are canonical and match the vectors.

## Quick start

```bash
# Validate a folder of vectors (e.g., the ZIPs I provided earlier)
python validate_vectors.py --vectors-dir ./test-vectors
python validate_vectors.py --vectors-dir ./witness-vectors
```

## Compare your outputs against a vector

### JOSE token
```bash
python validate_vectors.py   --check-jose-token eyJhbGciOiJFUzI1NiIsImtpZCI6ImtpZC13aXRuZXNzLTEifQ.eyJyb2xlIjoidGltZSIsInRzIjoiMjAyNS0wOS0xMVQxNTowMDowMloiLCJzdWJqZWN0IjoidzRpZHA6QUJDRC1FWEFNUExFIiwiZXZlbnRfaGFzaCI6ImRlYWRiZWVmY2FmZWJhYmUxMTIyMzM0NDU1NjY3Nzg4IiwicG9saWN5IjoicG9saWN5Oi8vYmFzZWxpbmUtdjEiLCJub25jZSI6IkFRSURCQVU9In0   --against test-vectors/witness_time_jose.json
```

### COSE parts
Extract your `COSE_Sign1`'s protected header bstr (base64url) and payload CBOR hex:

```bash
python validate_vectors.py   --check-cose   --protected-b64 pGNvbnRlbnQtdHlwZWSZYW...   --payload-hex 5a6b7c...   --against test-vectors/handshakeauth_cose.json
```

## Exit codes
- `0` = all checks passed
- `1` = at least one check failed

## Why this matters
Interop hinges on **canonicalization**. If two teams canonicalize differently, signatures won’t verify even with correct keys. This validator catches those differences early.
