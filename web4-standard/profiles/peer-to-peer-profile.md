# Peer-to-Peer Conformance Profile

This profile defines the requirements for Web4 implementations that communicate directly with each other without the need for a central server. This is common in applications such as secure messaging, file sharing, and collaborative editing.

## 1. Protocol Stack

-   **Network Protocol:** WebRTC
-   **Transport Protocol:** SCTP

## 2. Data Format

-   **Primary Format:** CBOR
-   **Canonicalization:** CBOR Deterministic Encoding

## 3. Cryptographic Suite

-   **Suite ID:** `W4-BASE-1`
-   **KEM:** X25519
-   **Signature:** Ed25519
-   **AEAD:** ChaCha20-Poly1305
-   **Hash:** SHA-256
-   **KDF:** HKDF



