# Web4 Interop Test Vectors (Unsigned)

This folder contains canonical encodings and signing inputs for two message types in both JOSE/JSON and COSE/CBOR:
- HandshakeAuth
- UsageReport

## Files
- handshakeauth_jose.json
- usagereport_jose.json
- handshakeauth_cose.json
- usagereport_cose.json

## How to use

### JOSE/JSON (ES256)
1. Take `protected_header` and `payload`.
2. JCS-canonicalize both (already embedded as base64url segments).
3. Build `signing_input` = `base64url(protected)` + "." + `base64url(payload)`.
4. Sign with **ES256**; append base64url(signature) as the third segment.
5. Verify your `signing_input` SHA-256 matches: 
   - HandshakeAuth: 38d83cfd7dcf3f5335374c5bdaf89bda2dd3b4f211468d9fca830d859ac2681d
   - UsageReport:   e6c50781bc6c5f1a553841995c322e2345fbee63d3d39b3ab63d2b26b9cdca0e

### COSE/CBOR (Ed25519/EdDSA)
1. Protected headers (diagnostic): {"alg": -8, "kid": "kid-demo-1", "content-type": "application/web4+cbor"}
2. Protected headers CBOR bstr (base64url): see `protected_bstr_b64` in each JSON.
3. Deterministically CBOR-encode the payload (hex provided as `payload_cbor_hex`).
4. Build COSE `Sig_structure` = ["Signature1", protected, external_aad="", payload] — the hex and SHA-256 are provided:
   - HandshakeAuth: SHA-256 f6573935f9c5c29c296c83b23e3e167c1392ef5643d9f533651fc409bee8ff2c
   - UsageReport:   SHA-256 34d1e77da4307688d27db1732b306b9e8626685775a5e10a1791cfad079f6bc8
5. Sign `Sig_structure` bytes using Ed25519; place the result in `COSE_Sign1.sig`.

Note: These vectors are **unsigned** to let different teams produce their own signatures while sharing the exact canonical encodings.
