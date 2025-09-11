# Blockchain Bridge Conformance Profile

This profile defines the requirements for Web4 implementations that bridge to blockchain networks. This allows for the anchoring of Web4 identities and data on a public ledger, providing a high level of trust and immutability.

## 1. Blockchain Integration

-   **Anchoring:** Web4 LCTs can be anchored on a blockchain by storing a hash of the LCT in a smart contract.
-   **Timestamping:** Blockchain timestamps can be used to provide a verifiable record of when an LCT was created or updated.
-   **Verification:** Smart contracts can be used to verify the authenticity and integrity of Web4 credentials.

## 2. Data Format

-   **Primary Format:** JSON
-   **Canonicalization:** JSON Canonicalization Scheme (JCS)

## 3. Cryptographic Suite

-   **Suite ID:** `W4-BASE-1`
-   **KEM:** X25519
-   **Signature:** Ed25519
-   **AEAD:** ChaCha20-Poly1305
-   **Hash:** SHA-256
-   **KDF:** HKDF



