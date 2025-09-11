# Web4 Core Protocol Specification

This document provides the detailed specification for the Web4 core protocol, including the handshake and pairing process, messaging protocol, data formats, and URI scheme.




## 1. Cryptographic Suites

Web4 defines a set of cryptographic suites to ensure interoperability and to provide options for different security and performance requirements. All implementations MUST support the `W4-BASE-1` suite.

| Suite ID          | KEM      | Sig       | AEAD              | Hash    | KDF     | Profile |
|-------------------|----------|-----------|-------------------|---------|---------|---------|
| W4-BASE-1 (MUST)  | X25519   | Ed25519   | ChaCha20-Poly1305 | SHA-256 | HKDF    | COSE    |
| W4-FIPS-1 (SHOULD)| P-256ECDH| ECDSA-P256| AES-128-GCM       | SHA-256 | HKDF    | JOSE    |
| W4-IOT-1 (MAY)    | X25519   | Ed25519   | AES-CCM           | SHA-256 | HKDF    | CBOR    |

## 2. Handshake Protocol (HPKE-based)

The Web4 handshake protocol is based on the Hybrid Public Key Encryption (HPKE) standard [RFC9180]. It is used to establish a secure, authenticated channel between two entities.

```
Client                                                   Server
------                                                   ------
ClientHello
  + supported_suites
  + supported_extensions
  + client_public_key
  + client_w4id_ephemeral
  + nonce[32]
  + GREASE_extensions[]
                           -------->
                                                    ServerHello
                                                      + selected_suite
                                                      + selected_extensions
                                                      + server_public_key
                                                      + server_w4id_ephemeral
                                                      + nonce[32]
                                                      + encrypted_credentials
                           <--------
ClientFinished
  + encrypted{client_credentials}
  + MAC(transcript)
                           -------->
                                                    ServerFinished
                                                      + MAC(transcript)
                                                      + session_id
                           <--------

[Application Data]         <------->         [Application Data]
```

### 1.3. Pairing Methods

Web4 supports multiple pairing methods to accommodate different use cases:

-   **Direct Pairing:** Two entities connect directly and perform the handshake and pairing protocol.
-   **Mediated Pairing:** A trusted third-party mediator facilitates the pairing process between two entities that cannot connect directly.
-   **QR Code Pairing:** One entity displays a QR code containing its Web4 identifier and public key, which the other entity scans to initiate the pairing process.




## 2. Messaging Protocol

Once a secure channel has been established, Web4 entities can exchange messages. The Web4 messaging protocol is designed to be simple, efficient, and extensible, supporting a variety of message types and content formats.

### 2.1. Message Structure

A Web4 message consists of a header and a payload:

-   **Header:** The header contains metadata about the message, such as the message type, content type, and a unique message identifier.
-   **Payload:** The payload contains the actual content of the message, which can be in any format, including plain text, JSON, or binary data.

### 2.2. Message Types

Web4 defines a set of standard message types to support common interactions:

-   **`request`:** A message that requests an action or information from the recipient.
-   **`response`:** A message that responds to a `request` message.
-   **`event`:** A message that notifies the recipient of an event or a change in state.
-   **`credential`:** A message that contains a verifiable credential.

### 2.3. Message Encryption

All Web4 messages MUST be encrypted using the keys established during the handshake and pairing process. This ensures the confidentiality and integrity of the communication.




## 3. Data and Credential Formats

Web4 defines a set of standard data and credential formats to ensure interoperability between different implementations. These formats are based on existing open standards, such as JSON and JSON-LD, and are designed to be extensible and flexible.

### 3.1. Web4 Identifier (W4ID)

A Web4 Identifier (W4ID) is a globally unique identifier for a Web4 entity. It is based on the Decentralized Identifier (DID) specification from the W3C and has the following format:

`w4id:<method-name>:<method-specific-id>`

-   **`w4id`:** The URI scheme for Web4 Identifiers.
-   **`<method-name>`:** The name of the method used to create and manage the identifier (e.g., `key`, `web`).
-   **`<method-specific-id>`:** A method-specific identifier.

### 3.2. Verifiable Credentials

Web4 uses Verifiable Credentials (VCs) as defined by the W3C to represent claims and attestations. VCs are digitally signed credentials that can be verified by any party.

### 3.3. JSON-LD

Web4 uses JSON-LD (JSON for Linked Data) to represent data in a structured and interoperable way. JSON-LD allows for the use of semantic vocabularies, such as Schema.org, to describe the meaning of the data.




## 4. Transport and Discovery

### 4.1 Transport Matrix

Web4 operates over multiple transport protocols with the following requirements:

| Transport | Status | Use Cases | Handshake | Metering |
|-----------|--------|-----------|-----------|----------|
| TLS 1.3 | MUST | Web, Cloud | Standard | Full |
| QUIC | MUST | Low-latency, Mobile | Standard | Full |
| WebTransport | SHOULD | Browser P2P | Standard | Full |
| WebRTC DataChannel | SHOULD | P2P, NAT traversal | Adapted | Full |
| WebSocket | MAY | Legacy browser | Standard | Full |
| BLE GATT | MAY | IoT, Proximity | Compressed | Limited |
| CAN Bus | MAY | Automotive | Compressed | Limited |
| TCP/TLS | MAY | Direct socket | Standard | Full |

**Requirements:**
- All transports MUST support the HPKE handshake (possibly adapted for constrained environments)
- All transports MUST provide confidentiality and integrity
- Constrained transports MAY use compressed message formats

### 4.2 Discovery Mechanisms

Web4 entities discover each other through multiple mechanisms:

| Method | Status | Description | Privacy |
|--------|--------|-------------|---------|
| DNS-SD/mDNS | SHOULD | Local network discovery | Low - broadcasts presence |
| QR Code OOB | SHOULD | Out-of-band pairing | High - requires proximity |
| Witness Relay | MUST | Bootstrap via known witnesses | Medium - witness knows query |
| DNS Bootstrap | MAY | DNS TXT records for services | Low - DNS queries visible |
| DHT Lookup | MAY | Distributed hash table | Low - DHT participation visible |
| Broadcast | MAY | Unidirectional announcement | Low - public broadcast |

**Discovery Protocol:**
1. Entity generates discovery request with:
   - Desired capabilities
   - Acceptable witness list
   - Nonce for replay protection
2. Discovery service returns:
   - List of matching entities
   - Their current witness attestations
   - Connection endpoints
3. Entity validates witness signatures before connecting

### 4.3 Transport Selection

Endpoints negotiate transport during discovery:
- Advertise supported transports in priority order
- Select highest mutual priority
- Fall back to TLS 1.3 as universal baseline

## 5. URI Scheme

The Web4 URI scheme provides a way to identify and locate Web4 resources. The scheme is based on the standard URI syntax defined in RFC 3986 and is designed to be flexible and extensible.

### 5.1. Syntax

The Web4 URI scheme has the following syntax:

`web4://<w4id>/<path-abempty>[?query][#fragment]`

-   **`web4://`:** The scheme identifier.
-   **`<w4id>`:** The Web4 Identifier of the entity that owns the resource.
-   **`<path-abempty>`:** An optional path to the resource.
-   **`[?query]`:** An optional query string.
-   **`[#fragment]`:** An optional fragment identifier.

### 5.2. Resolution

To resolve a Web4 URI, the client first resolves the W4ID to obtain the entity's service endpoint. The client then sends a request to the service endpoint, including the path, query, and fragment from the URI.


