# Initial Registries
Status: Draft • Last-Updated: 2025-09-11T22:47:56.408268Z

## Suite IDs
- W4-BASE-1 : X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 (COSE)
- W4-FIPS-1 : P-256 ECDH / ECDSA-P256 / AES-128-GCM / SHA-256 (JOSE)

## Extension IDs (provisional)
- w4_ext_sdjwt_vp@1
- w4_ext_noise_xx@1
- w4_ext_93f07f2a@0 (GREASE placeholder)

## Error Codes

### Binding Errors
- W4_ERR_BINDING_EXISTS - Entity already has an active binding
- W4_ERR_BINDING_INVALID - Binding parameters are malformed
- W4_ERR_BINDING_REVOKED - Referenced binding has been revoked
- W4_ERR_BINDING_PROOF_FAIL - Binding proof signature verification failed

### Pairing Errors
- W4_ERR_PAIRING_DENIED - Entity denied pairing request
- W4_ERR_PAIRING_TIMEOUT - Pairing handshake timed out
- W4_ERR_PAIRING_INVALID - Pairing parameters are malformed
- W4_ERR_PAIRING_EXPIRED - Pairing session has expired

### Witness Errors
- W4_ERR_WITNESS_UNAVAIL - Required witness is not available
- W4_ERR_WITNESS_REJECTED - Witness rejected attestation request
- W4_ERR_WITNESS_INVALID - Witness signature or format invalid
- W4_ERR_WITNESS_QUORUM - Insufficient witnesses for quorum
- W4_ERR_WITNESS_REQUIRED - Witness attestation required but missing

### Authorization Errors
- W4_ERR_AUTHZ_DENIED - Credential lacks required capability
- W4_ERR_AUTHZ_EXPIRED - Authorization token has expired
- W4_ERR_AUTHZ_SCOPE - Operation requires additional scopes
- W4_ERR_AUTHZ_RATE - Metering rate limit exceeded

### Cryptographic Errors
- W4_ERR_CRYPTO_SUITE - Cryptographic suite not supported
- W4_ERR_CRYPTO_VERIFY - Signature verification failed
- W4_ERR_CRYPTO_DECRYPT - Failed to decrypt message
- W4_ERR_CRYPTO_KEY - Public key format or encoding invalid

### Protocol Errors
- W4_ERR_PROTO_VERSION - Protocol version not supported
- W4_ERR_PROTO_SEQUENCE - Message sequence out of order
- W4_ERR_PROTO_REPLAY - Message replay attack detected
- W4_ERR_PROTO_DOWNGRADE - Protocol downgrade attack detected
- W4_ERR_PROTO_FORMAT - Message format doesn't match negotiated profile

### Metering Errors
- W4_ERR_GRANT_EXPIRED - Credit grant has expired
- W4_ERR_RATE_LIMIT - Rate limit exceeded (same as W4_ERR_AUTHZ_RATE)
- W4_ERR_SCOPE_DENIED - Requested scope not authorized
- W4_ERR_BAD_SEQUENCE - Sequence number out of order
- W4_ERR_BAD_TIMESTAMP - Timestamp outside acceptable window
