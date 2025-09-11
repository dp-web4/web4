# Cloud Service Conformance Profile

This profile defines the requirements for Web4 implementations on cloud services, such as web servers, APIs, and other backend systems. These services are typically not resource-constrained and can support a wider range of protocols and cryptographic algorithms.

## 1. Protocol Stack

-   **Network Protocol:** HTTPS
-   **Transport Protocol:** TCP
-   **Authentication:** OAuth 2.0

## 2. Data Format

-   **Primary Format:** JSON
-   **Canonicalization:** JSON Canonicalization Scheme (JCS)

## 3. Cryptographic Suite

-   **Suite ID:** `W4-FIPS-1`
-   **KEM:** P-256ECDH
-   **Signature:** ECDSA-P256
-   **AEAD:** AES-128-GCM
-   **Hash:** SHA-256
-   **KDF:** HKDF



