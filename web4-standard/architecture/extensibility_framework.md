# Web4 Extensibility Framework

This document defines the framework for extending the Web4 protocol. A robust extensibility model is crucial for the long-term success and evolution of the standard, allowing for the introduction of new features and capabilities without breaking backward compatibility.

## 1. Extension Mechanism

Web4 extensions are defined as optional additions to the core protocol. Implementations are not required to support any extensions, but they MUST be able to parse and ignore any unknown extensions gracefully.

### 1.1. Extension Negotiation

Extensions are negotiated during the handshake and pairing process. A client MAY include a list of supported extensions in its initial handshake message. The server then responds with a list of extensions that it supports and wishes to use for the current session.

### 1.2. Extension Structure

Each extension is defined by a unique identifier and a set of parameters. The identifier is a short, human-readable string, and the parameters are defined in a key-value format.

## 2. Subprotocol Negotiation

Web4 supports the concept of subprotocols, which are application-level protocols layered on top of the core Web4 protocol. Subprotocols allow for the creation of specialized protocols for specific use cases.

### 2.1. Subprotocol Negotiation

Subprotocols are negotiated during the handshake and pairing process, similar to extensions. A client MAY include a list of supported subprotocols in its initial handshake message. The server then selects one of the proposed subprotocols to use for the session.

## 3. IANA Considerations

To ensure interoperability and prevent collisions, all Web4 extensions and subprotocols MUST be registered with the Internet Assigned Numbers Authority (IANA).

### 3.1. Extension Registry

A new IANA registry will be created for Web4 extensions. The registry will include the extension identifier, a brief description, and a reference to the relevant specification.

### 3.2. Subprotocol Registry

A new IANA registry will be created for Web4 subprotocols. The registry will include the subprotocol identifier, a brief description, and a reference to the relevant specification.


