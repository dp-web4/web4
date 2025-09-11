# Edge Device Conformance Profile

This profile defines the requirements for Web4 implementations on edge devices, such as IoT sensors, actuators, and gateways. These devices are typically resource-constrained, with limited processing power, memory, and network bandwidth.

## 1. Protocol Stack

-   **Network Protocol:** CoAP (Constrained Application Protocol)
-   **Transport Protocol:** UDP
-   **Physical Layer:** BLE (Bluetooth Low Energy)

## 2. Data Format

-   **Primary Format:** CBOR (Concise Binary Object Representation)
-   **Canonicalization:** CBOR Deterministic Encoding

## 3. Cryptographic Suite

-   **Suite ID:** `W4-IOT-1`
-   **KEM:** X25519
-   **Signature:** Ed25519
-   **AEAD:** AES-CCM
-   **Hash:** SHA-256
-   **KDF:** HKDF



