# Web4 Error Taxonomy

This document defines a standardized error taxonomy for the Web4 protocol based on RFC 9457 Problem Details. A consistent error format is essential for debugging, interoperability, and providing a good developer experience.

## 1. Error Format

Web4 uses RFC 9457 Problem Details for all protocol errors. Errors MUST be represented as JSON objects with `application/problem+json` content type (or `application/problem+cbor` for CBOR):

```json
{
  "type": "about:blank",
  "title": "Binding Failed",
  "status": 409,
  "code": "W4_ERR_BINDING_EXISTS",
  "detail": "Entity already has an active binding for device-12345",
  "instance": "web4://w4idp-ABCD/bindings/12345"
}
```

### Required Fields

-   **`type`** (REQUIRED): URI identifying the error type. Use `"about:blank"` for generic errors or specific URIs for well-known error types
-   **`title`** (REQUIRED): Short, human-readable summary of the error type
-   **`status`** (REQUIRED): HTTP status code (100-599)
-   **`code`** (REQUIRED): Web4-specific error code from the defined taxonomy
-   **`detail`** (OPTIONAL): Human-readable explanation specific to this occurrence
-   **`instance`** (OPTIONAL): URI identifying the specific occurrence of the error

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
  "title": "Unauthorized",
  "status": 401,
  "code": "W4_ERR_AUTHZ_DENIED",
  "detail": "Credential lacks scope write:lct",
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

## 5. HTTP Status Code Mapping

- **400 Bad Request**: Malformed requests, invalid parameters
- **401 Unauthorized**: Authentication or authorization failures
- **403 Forbidden**: Operation not allowed for authenticated entity
- **408 Request Timeout**: Operation timed out
- **409 Conflict**: Resource state conflicts
- **410 Gone**: Resource no longer available
- **429 Too Many Requests**: Rate limiting
- **503 Service Unavailable**: Temporary unavailability
---
**See also:** Web4 Society–Authority–Law (SAL) — normative requirements for genesis **Citizen** role, **Authority**, **Law Oracle**, **Witness/Auditor**, immutable record, MRH edges, and R6 bindings. ([sal.md](web4-society-authority-law.md), [sal.jsonld](sal.jsonld))
