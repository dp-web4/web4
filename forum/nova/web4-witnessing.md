# Web4 Witnessing Specification

## 1. Introduction
Witnessing is a core mechanism in Web4 that provides verifiable context for actions
without requiring centralized authorities. This section defines the canonical
formats and required fields for witness attestations, ensuring consistency across
protocols (Handshake, LCT, Metering).

## 2. Roles
A witness is any entity that observes and attests to an event or state. Web4 defines
the following roles:

- **time**: Attests to freshness by providing a trusted timestamp.
- **audit-minimal**: Attests that a transaction occurred and met minimal policy requirements.
- **oracle**: Provides contextual external information (e.g., price, state).

Roles are extensible; new roles MUST be registered in the Web4 Witness Role Registry.

## 3. Envelope Format

Witness attestations MUST use COSE_Sign1 (EdDSA/Ed25519) as the canonical format.
A JOSE/JWS JSON serialization MAY be provided for JSON-centric ecosystems.

### 3.1 COSE Attestation Structure
Protected headers (CBOR map):
```
{
  1: -8,                # alg = EdDSA
  4: h'6b69642d64656d6f2d31',  # kid = "kid-demo-1"
  3: "application/web4+witness+cbor"
}
```

Payload (CBOR map):
```
{
  "role": "time",
  "ts": "2025-09-11T15:00:02Z",
  "subject": "w4idp:abcd...",
  "event_hash": h'deadbeefcafebabe',
  "policy": "policy://baseline-v1",
  "nonce": h'01020304'
}
```

The `Sig_structure` is built per COSE Sign1:
```
["Signature1", protected, external_aad="", payload]
```

### 3.2 JOSE Attestation Structure
Protected header:
```json
{
  "alg": "ES256",
  "kid": "kid-demo-1",
  "typ": "JWT"
}
```

Payload (JCS canonical JSON):
```json
{
  "role": "audit-minimal",
  "ts": "2025-09-11T15:00:02Z",
  "subject": "w4idp:abcd...",
  "event_hash": "deadbeefcafebabe",
  "policy": "policy://baseline-v1",
  "nonce": "AQIDBA=="
}
```

### 3.3 Required Fields
- `role`: MUST be one of the registered roles.
- `ts`: ISO 8601 timestamp of attestation.
- `subject`: W4IDp of the attested entity.
- `event_hash`: SHA-256 hash of the event or transcript being witnessed.
- `policy`: Identifier of the applied policy (MAY be omitted if not applicable).
- `nonce`: Random value to provide uniqueness and replay protection.

### 3.4 Verification
1. Verify signature (Ed25519 or ES256) against the witness public key.
2. Confirm `ts` within freshness window defined by profile (default ±300s).
3. Confirm `event_hash` matches the transcript/event digest.
4. Confirm `role` is recognized and policy constraints satisfied.

## 4. Error Handling
Witness errors use the Web4 Problem Details format (`application/problem+json` or
`application/problem+cbor`), with type `w4:err:witness`.

## 5. Interoperability Vectors
Unsigned test vectors MUST be provided for:
- time role attestation
- audit-minimal role attestation
- oracle role attestation

These vectors include canonical encodings and SHA-256 of `Sig_structure` or
JWS signing input, allowing independent implementers to cross-check.

## 6. IANA Considerations (Draft)
Establish a "Web4 Witness Role Registry" for `role` values. Initial entries:
- time
- audit-minimal
- oracle

## 7. Security Considerations
- Witnessing does not imply surveillance. Attestations are scoped and pairwise.
- Witnesses MUST NOT reuse nonces across attestations.
- Expired attestations MUST be rejected.
- Implementations SHOULD support multiple witnesses for redundancy.
