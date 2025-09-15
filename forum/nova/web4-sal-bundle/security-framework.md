# Web4 Security Framework

This document defines the security framework for the Web4 standard. It covers the cryptographic primitives, key management, authentication and authorization, and a comprehensive analysis of security considerations.




## 1. Cryptographic Suites

Web4 defines standardized cryptographic suites to ensure interoperability and security. All implementations MUST support the mandatory suite.

### 1.1. Suite Definitions

| Suite ID          | KEM     | Sig       | AEAD                | Hash    | Profile | Status |
|-------------------|---------|-----------|---------------------|---------|---------|--------|
| W4-BASE-1         | X25519  | Ed25519   | ChaCha20-Poly1305   | SHA-256 | COSE    | MUST   |
| W4-FIPS-1         | P-256   | ECDSA-P256| AES-128-GCM         | SHA-256 | JOSE    | SHOULD |

**Implementation Requirements:**
- Implementations MUST support W4-BASE-1
- FIPS-bound environments SHOULD support W4-FIPS-1
- Other suites MAY be offered but MUST NOT be negotiated as MTI

### 1.2. Algorithm Specifications

#### W4-BASE-1 (Mandatory to Implement)
- **Key Exchange**: X25519 (RFC 7748)
- **Signatures**: Ed25519 (RFC 8032)
- **AEAD**: ChaCha20-Poly1305 (RFC 8439)
- **Hash**: SHA-256 (FIPS 180-4)
- **KDF**: HKDF-SHA256 (RFC 5869)
- **Encoding**: COSE (RFC 8152)

#### W4-FIPS-1 (FIPS Compliance)
- **Key Exchange**: ECDH with P-256 (FIPS 186-4)
- **Signatures**: ECDSA with P-256 (FIPS 186-4)
- **AEAD**: AES-128-GCM (NIST SP 800-38D)
- **Hash**: SHA-256 (FIPS 180-4)
- **KDF**: HKDF-SHA256 (RFC 5869)
- **Encoding**: JOSE (RFC 7515/7516)

### 1.3. Canonicalization and Signatures

All Web4 signed payloads **MUST** implement COSE/CBOR (Ed25519/EdDSA) as mandatory-to-implement (MTI). JOSE/JSON (ES256) is OPTIONAL/SHOULD for bridge scenarios.

#### COSE/CBOR (MUST)
- Deterministic CBOR encoding per CTAP2
- Ed25519 with `crv: Ed25519` and `alg: EdDSA` 
- Payload is the canonical CBOR map
- See web4-handshake.md Section 6.0.3 for complete profile

#### JOSE/JSON (SHOULD)
- JCS canonical JSON (RFC 8785)
- ES256 with compact serialization or JWS JSON serialization
- See web4-handshake.md Section 6.0.4 for complete profile




## 2. Key Management

Proper key management is crucial for the security of the Web4 protocol. This section provides guidelines for key generation, storage, and rotation.

### 2.1. Key Generation

Web4 entities MUST generate their own key pairs. The key generation process MUST use a secure random number generator.

### 2.2. Key Storage

Private keys MUST be stored securely to prevent unauthorized access. Recommended storage methods include:

-   **Hardware Security Modules (HSMs):** For the highest level of security, private keys should be stored in an HSM.
-   **Secure Enclaves:** On devices that support it, private keys can be stored in a secure enclave, such as the Secure Enclave on Apple devices or the Trusted Execution Environment (TEE) on Android devices.
-   **Encrypted Storage:** If an HSM or secure enclave is not available, private keys should be stored in an encrypted format, with the encryption key protected by a strong password or other authentication mechanism.

### 2.3. Key Rotation

To mitigate the risk of key compromise, Web4 entities SHOULD rotate their keys periodically. The key rotation process involves generating a new key pair and updating the entity's Web4 Identifier to use the new public key.




## 3. Authentication and Authorization

Authentication and authorization are essential for controlling access to Web4 resources and services. This section describes the mechanisms for verifying the identity of entities and determining their access rights.

### 3.1. Authentication

Authentication in Web4 is based on digital signatures. An entity authenticates itself by signing a challenge with its private key. The signature can then be verified by the other party using the entity's public key.

### 3.2. Authorization

Authorization in Web4 is based on Verifiable Credentials (VCs). A VC is a digitally signed credential that contains a set of claims about an entity. These claims can be used to determine the entity's access rights to a particular resource or service.

For example, a VC could be used to grant an entity access to a specific API, or to prove that the entity is over a certain age.
---
**See also:** Web4 Society–Authority–Law (SAL) — normative requirements for genesis **Citizen** role, **Authority**, **Law Oracle**, **Witness/Auditor**, immutable record, MRH edges, and R6 bindings. ([sal.md](web4-society-authority-law.md), [sal.jsonld](sal.jsonld))
