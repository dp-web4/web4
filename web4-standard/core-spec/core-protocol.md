# Web4 Core Protocol Specification

This document provides the detailed specification for the Web4 core protocol, including the handshake and pairing process, messaging protocol, data formats, and URI scheme.




## 1. Handshake and Pairing Protocol

The Web4 handshake and pairing protocol is the process by which two Web4 entities establish a secure communication channel and create a persistent, trusted relationship. This protocol is designed to be secure, efficient, and flexible, allowing for a variety of pairing methods.

### 1.1. Protocol Overview

The pairing process consists of the following phases:

1.  **Discovery:** One entity discovers the other, either through a direct connection, a discovery service, or by scanning a QR code.
2.  **Handshake:** The two entities perform a cryptographic handshake to establish a secure channel and exchange their public keys.
3.  **Pairing:** The entities exchange and store their respective Web4 identifiers and public keys, creating a persistent pairing.
4.  **Witnessing (Optional):** A third-party witness may be involved to notarize the pairing, adding an extra layer of trust.

### 1.2. Handshake Messages

The handshake process involves the exchange of the following messages:

-   **ClientHello:** The initiating entity (client) sends a `ClientHello` message to the responding entity (server). This message includes the client's public key and a list of supported cryptographic algorithms.
-   **ServerHello:** The server responds with a `ServerHello` message, which includes its public key and the selected cryptographic algorithm.
-   **ClientFinished:** The client sends a `ClientFinished` message, which is encrypted with the server's public key and contains a signature of the handshake messages.
-   **ServerFinished:** The server responds with a `ServerFinished` message, which is encrypted with the client's public key and contains a signature of the handshake messages.

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




## 4. URI Scheme

The Web4 URI scheme provides a way to identify and locate Web4 resources. The scheme is based on the standard URI syntax defined in RFC 3986 and is designed to be flexible and extensible.

### 4.1. Syntax

The Web4 URI scheme has the following syntax:

`web4://<w4id>/<path-abempty>[?query][#fragment]`

-   **`web4://`:** The scheme identifier.
-   **`<w4id>`:** The Web4 Identifier of the entity that owns the resource.
-   **`<path-abempty>`:** An optional path to the resource.
-   **`[?query]`:** An optional query string.
-   **`[#fragment]`:** An optional fragment identifier.

### 4.2. Resolution

To resolve a Web4 URI, the client first resolves the W4ID to obtain the entity's service endpoint. The client then sends a request to the service endpoint, including the path, query, and fragment from the URI.


