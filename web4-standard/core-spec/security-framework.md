# Web4 Security Framework

This document defines the security framework for the Web4 standard. It covers the cryptographic primitives, key management, and authentication and authorization.




## 1. Cryptographic Suites

Web4 defines standardized cryptographic suites to ensure interoperability and security. All implementations MUST support the mandatory suite.

### 1.1. Suite Definitions

| Suite ID          | KEM       | Sig        | AEAD                | Hash    | KDF         | Encoding | Status |
|-------------------|-----------|------------|---------------------|---------|-------------|----------|--------|
| W4-BASE-1         | X25519    | Ed25519    | ChaCha20-Poly1305   | SHA-256 | HKDF-SHA256 | COSE     | MUST   |
| W4-FIPS-1         | ECDH-P256 | ECDSA-P256 | AES-128-GCM         | SHA-256 | HKDF-SHA256 | JOSE     | SHOULD |

**Implementation Requirements:**
- Implementations MUST support W4-BASE-1
- FIPS-bound environments SHOULD support W4-FIPS-1
- Other suites MAY be offered but MUST NOT be required in place of the mandatory W4-BASE-1 baseline

### 1.2. Algorithm Specifications

#### W4-BASE-1 (Mandatory to Implement)
- **Key Exchange**: X25519 (RFC 7748)
- **Signatures**: Ed25519 (RFC 8032)
- **AEAD**: ChaCha20-Poly1305 (RFC 8439)
- **Hash**: SHA-256 (FIPS 180-4)
- **KDF**: HKDF-SHA256 (RFC 5869)
- **Encoding**: COSE (RFC 9052/9053, obsoletes RFC 8152)

#### W4-FIPS-1 (FIPS Compliance)
- **Key Exchange**: ECDH-P256 (ECDH with P-256, FIPS 186-4)
- **Signatures**: ECDSA with P-256 (FIPS 186-4)
- **AEAD**: AES-128-GCM (NIST SP 800-38D)
- **Hash**: SHA-256 (FIPS 180-4)
- **KDF**: HKDF-SHA256 (RFC 5869)
- **Encoding**: JOSE (RFC 7515/7516)

### 1.3. Canonicalization and Signatures

All Web4 signed payloads **MUST** implement COSE/CBOR (Ed25519/EdDSA) as mandatory-to-implement (MTI). JOSE/JSON (ES256) is SHOULD for bridge scenarios.

#### COSE/CBOR (MUST)
- Deterministic CBOR encoding per CTAP2
- Ed25519 with `crv = 6` (COSE curve label) and `alg = -8` (EdDSA)
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

For multi-device identities, implementations MUST distinguish **replicated identity state** from **device-local custody**:

- Root-LCT public state, constellation membership, enrollment/revocation state, recovery policy, and public Device-LCT material MAY be replicated across authorized devices.
- Hardware-anchor private keys, device-unlock secrets, and private attestation material MUST remain device-local and MUST NOT be synchronized as part of an opaque identity-vault copy.
- A replicated backup format MUST identify each secret's custody class. Importing a backup MUST NOT silently convert a hardware-bound credential into an exportable software credential at the same assurance level.
- Revocation state SHOULD propagate aggressively; stale replicas MUST NOT restore authority to a revoked device merely because they predate the revocation.

### 2.3. Key Rotation

To mitigate the risk of key compromise, Web4 entities SHOULD rotate their keys periodically. The key rotation process involves generating a new key pair and issuing a new LCT bound to the new public key. See `LCT-linked-context-token.md` Section 7.3 for the normative rotation lifecycle (new LCT issuance, `lineage` to the parent, and the dual-validity overlap window before the parent is retired as `superseded`).




## 3. Authentication and Authorization

Authentication and authorization are essential for controlling access to Web4 resources and services. This section describes the mechanisms for verifying the identity of entities and determining their access rights.

### 3.1. Authentication

Authentication in Web4 is based on digital signatures. An entity authenticates itself by signing a challenge with its private key. The signature can then be verified by the other party using the entity's public key. See `web4-handshake.md` §6.0.5 (Binding to Session) for the normative session-binding requirement, and §9 (Anti-Replay & Clocks) for the freshness, nonce-uniqueness, and replay-protection requirements that a conformant challenge-response MUST satisfy; the `HandshakeAuth` `nonce`/`ts` fields these rules operate on are defined in §6.1.

#### 3.1.1 Composed Actor Provenance

A valid principal signature proves control of the principal credential; it does **not** by itself prove which harness, device, role, or delegated authority caused an act.

When software or another member acts on behalf of a principal, a consequential session or act MUST preserve the identities as distinct fields rather than collapsing them into one signer. The authenticated envelope SHOULD bind, as applicable:

- `principal` — the human, AI, organization, or other root identity whose intent/benefit is represented;
- `actor` — the harness, application instance, agent, or member that actually performs the act;
- `via_device` — the Device LCT or hardware anchor used for the session;
- `office` — the role/office being occupied, when authority derives from a role rather than merely from identity; and
- `authority` — the occupancy, delegation, capability, or session reference that authorizes the actor to act for the principal in that office.

The canonical transcript or act digest MUST cover every field whose alteration would change attribution or authority. If separate actor/device credentials exist, their proofs SHOULD cover the same transcript so that replacing `actor`, `via_device`, `office`, or `authority` invalidates the proof.

**Authority does not transfer through prose or authenticated instruction alone.** A request from one entity to another is evidence of instruction, not an implicit grant of the requester's or deputy's authority. Cross-entity delegation MUST be explicit, attributable, scoped, and independently verifiable.

#### 3.1.2 Multi-Device and Quorum Assurance

A multi-device policy such as `m-of-n` is an **assurance claim**. Implementations MUST distinguish cryptographic quorum from a policy wrapper around a single credential key:

- If a credential is described as cryptographic `m-of-n`, no single participating device may be sufficient to complete the protected credential operation when `m > 1`.
- A design in which one device holds the relying-party credential key and peer devices merely approve its use MAY be useful, but it MUST be identified as policy quorum rather than cryptographic quorum unless the key operation itself cannot complete without the required peers.
- If fewer than `m` required devices are available, implementations MUST NOT silently reduce the threshold while presenting the result as the same credential or assurance level.
- Recovery, emergency access, and intentionally lower-assurance credentials MAY exist, but each MUST be a separately defined path whose reduced assurance is visible to the relying party or policy evaluator.

> **Availability may degrade service; it may not silently degrade identity assurance.**

A Web4-backed WebAuthn/passkey credential MAY claim assurance parity with an ordinary platform passkey only when its key custody, relying-party binding, user verification, and anti-export properties meet the same bar. Additional independent anchors MAY then increase assurance; they do not retroactively make weak single-device custody equivalent to hardware-bound custody.

### 3.2. Authorization

Authorization in Web4 is based on Verifiable Credentials (VCs). A VC is a digitally signed credential that contains a set of claims about an entity. These claims can be used to determine the entity's access rights to a particular resource or service.

For example, a VC could be used to grant an entity access to a specific API, or to prove that the entity is over a certain age.


