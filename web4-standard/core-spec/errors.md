# Web4 Error Taxonomy

**Version**: 1
**Status**: Draft — core protocol error taxonomy (RFC 9457 Problem Details); subsystem specs extend it (see §1).
**Last-Updated**: 2026-06-17

---

This document defines the standardized **core protocol** error taxonomy for Web4, based on RFC 9457 Problem Details. It is the single source of truth for core protocol error codes (binding, pairing, witnessing, authorization, cryptography, and protocol errors). Subsystem specifications **extend** this taxonomy with additional domain-specific codes and SHOULD reuse the codes defined here where applicable rather than introducing parallel names: Society/Authority Law (`web4-society-authority-law.md` §9), ACP (`acp-framework.md` §10), and metering (`web4-metering.md` §6) add codes following the `W4_ERR_*` convention defined here; MCP cross-society (`mcp-protocol.md` §7.6) currently uses lowercase `web4_*` identifiers for its cross-society failure modes. A consistent error format is essential for debugging, interoperability, and providing a good developer experience.

## 1. Error Format

Web4 uses RFC 9457 Problem Details for all protocol errors. Errors MUST be represented as JSON objects with `application/problem+json` content type (or `application/problem+cbor` for CBOR):

```json
{
  "type": "about:blank",
  "title": "Binding Already Exists",
  "status": 409,
  "code": "W4_ERR_BINDING_EXISTS",
  "detail": "Entity already has an active binding for device-12345",
  "instance": "web4://w4idp-ABCD/bindings/12345"
}
```

### Fields

Web4 Problem Details build on the RFC 9457 member set. Per RFC 9457 §3.1 the standard members (`type`, `title`, `status`, `detail`, `instance`) are all OPTIONAL; Web4 additionally **mandates `status` and `title`** for every error and defines `code` as a Web4 **extension member** (RFC 9457 §3.2):

-   **`type`** (OPTIONAL): URI identifying the error type. Defaults to `"about:blank"` (RFC 9457 §3.1); use a specific URI only for well-known, dereferenceable error types
-   **`title`** (REQUIRED in Web4): Short, human-readable summary of the error type
-   **`status`** (REQUIRED in Web4): Status code in the range 100–599. Modelled on HTTP status codes for familiarity but **transport-agnostic** — over HTTP it SHOULD equal the response status code; over non-HTTP transports (e.g. CBOR over TLS/QUIC, BLE GATT, or CAN Bus per `core-protocol.md` §5.1) it carries the analogous semantic class per §2/§5
-   **`code`** (REQUIRED in Web4): Web4 **extension member** (RFC 9457 §3.2) carrying the error code from the §2 taxonomy
-   **`detail`** (OPTIONAL): Human-readable explanation specific to this occurrence
-   **`instance`** (OPTIONAL): URI identifying the specific occurrence of the error. The path segments shown in examples (e.g. `/bindings/12345`, `/messages/123`) are **illustrative**; Web4 defines no normative `instance` path registry

## 2. Error Code Taxonomy

Web4 defines a hierarchical error code taxonomy with the following categories:

### 2.1 Binding Errors (W4_ERR_BINDING_*)

| Code | Title | Status | Description |
|------|-------|--------|-------------|
| W4_ERR_BINDING_EXISTS | Binding Already Exists | 409 | Entity already has an active binding |
| W4_ERR_BINDING_INVALID | Invalid Binding | 400 | Binding parameters are malformed |
| W4_ERR_BINDING_REVOKED | Binding Revoked | 410 | Referenced binding has been revoked |
| W4_ERR_BINDING_PROOF_FAIL | Binding Proof Failed | 401 | Binding proof signature verification failed |

### 2.2 Pairing Errors (W4_ERR_PAIRING_*)

| Code | Title | Status | Description |
|------|-------|--------|-------------|
| W4_ERR_PAIRING_DENIED | Pairing Denied | 403 | Entity denied pairing request |
| W4_ERR_PAIRING_TIMEOUT | Pairing Timeout | 408 | Pairing handshake timed out |
| W4_ERR_PAIRING_INVALID | Invalid Pairing | 400 | Pairing parameters are malformed |
| W4_ERR_PAIRING_EXPIRED | Pairing Expired | 410 | Pairing session has expired |

### 2.3 Witness Errors (W4_ERR_WITNESS_*)

| Code | Title | Status | Description |
|------|-------|--------|-------------|
| W4_ERR_WITNESS_UNAVAIL | Witness Unavailable | 503 | Required witness is not available |
| W4_ERR_WITNESS_REJECTED | Witness Rejected | 403 | Witness rejected attestation request |
| W4_ERR_WITNESS_INVALID | Invalid Witness | 400 | Witness signature or format invalid |
| W4_ERR_WITNESS_QUORUM | Quorum Not Met | 409 | Insufficient witnesses for quorum |

### 2.4 Authorization Errors (W4_ERR_AUTHZ_*)

| Code | Title | Status | Description |
|------|-------|--------|-------------|
| W4_ERR_AUTHZ_DENIED | Authorization Denied | 401 | Credential lacks required capability |
| W4_ERR_AUTHZ_EXPIRED | Authorization Expired | 401 | Authorization token has expired |
| W4_ERR_AUTHZ_SCOPE | Insufficient Scope | 403 | Operation requires additional scopes |
| W4_ERR_AUTHZ_RATE | Rate Limit Exceeded | 429 | Metering rate limit exceeded |

### 2.5 Cryptographic Errors (W4_ERR_CRYPTO_*)

| Code | Title | Status | Description |
|------|-------|--------|-------------|
| W4_ERR_CRYPTO_SUITE | Unsupported Suite | 400 | Cryptographic suite not supported |
| W4_ERR_CRYPTO_VERIFY | Verification Failed | 401 | Signature verification failed |
| W4_ERR_CRYPTO_DECRYPT | Decryption Failed | 400 | Failed to decrypt message |
| W4_ERR_CRYPTO_KEY | Invalid Key | 400 | Public key format or encoding invalid |

### 2.6 Protocol Errors (W4_ERR_PROTO_*)

| Code | Title | Status | Description |
|------|-------|--------|-------------|
| W4_ERR_PROTO_VERSION | Version Mismatch | 400 | Protocol version not supported |
| W4_ERR_PROTO_SEQUENCE | Sequence Error | 400 | Message sequence out of order |
| W4_ERR_PROTO_REPLAY | Replay Detected | 409 | Message replay attack detected |
| W4_ERR_PROTO_DOWNGRADE | Downgrade Detected | 400 | Protocol downgrade attack detected |

## 3. Error Examples

### 3.1 Authorization Error

```json
{
  "type": "about:blank",
  "title": "Authorization Denied",
  "status": 401,
  "code": "W4_ERR_AUTHZ_DENIED",
  "detail": "Credential lacks the required capability for this operation",
  "instance": "web4://w4idp-ABCD/messages/123"
}
```

### 3.2 Witness Quorum Error

```json
{
  "type": "about:blank",
  "title": "Quorum Not Met",
  "status": 409,
  "code": "W4_ERR_WITNESS_QUORUM",
  "detail": "Only 2 of 3 required witnesses responded",
  "instance": "web4://w4idp-EFGH/attestations/456"
}
```

### 3.3 Rate Limit Error

```json
{
  "type": "about:blank",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "code": "W4_ERR_AUTHZ_RATE",
  "detail": "Request rate 5001/min exceeds limit 5000/min",
  "instance": "web4://w4idp-IJKL/api/v1/query"
}
```

## 4. Content Types

- **JSON**: `application/problem+json` (MUST support)
- **CBOR**: `application/problem+cbor` (SHOULD support)

## 5. Status Code Semantics

Per §1, the `status` member is **transport-agnostic** — the reason phrases below are HTTP status codes used as the canonical *illustrative labels* for each semantic class, and the same semantic class applies over non-HTTP transports (e.g. CBOR over TLS/QUIC, BLE GATT, CAN Bus). Each entry names the semantic class the status conveys:

- **400 Bad Request**: Malformed requests, invalid parameters
- **401 Unauthorized**: Authentication failure, or a credential that lacks the required capability (e.g. `W4_ERR_AUTHZ_DENIED`)
- **403 Forbidden**: An authenticated entity lacking the additional scope or authorization required for the operation (e.g. `W4_ERR_AUTHZ_SCOPE`)
- **408 Request Timeout**: Operation timed out
- **409 Conflict**: Resource state conflicts
- **410 Gone**: Resource no longer available
- **429 Too Many Requests**: Rate limiting
- **503 Service Unavailable**: Temporary unavailability


