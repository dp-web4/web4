# W3C Decentralized Identifiers (DIDs) Standard

## Specification Details
- **Title**: Decentralized Identifiers (DIDs) v1.0 - Core architecture, data model, and representations
- **Status**: W3C Recommendation (Final Standard)
- **Date**: July 19, 2022
- **Editors**: Manu Sporny (Digital Bazaar), Amy Guy (Digital Bazaar), Markus Sabadello (Danube Tech), Drummond Reed (Evernym/Avast)
- **Working Group**: W3C Decentralized Identifier Working Group
- **Implementation Status**: 103 experimental DID Method specifications, 32 DID Method driver implementations, 46 conformant implementations

## Core Concept

DIDs are a new type of globally unique identifier that enables verifiable, decentralized digital identity. Unlike federated identifiers, DIDs are designed to be decoupled from centralized registries, identity providers, and certificate authorities.

### Key Characteristics
1. **Controller-owned**: Entities generate their own identifiers using systems they trust
2. **Verifiable**: Controllers prove control through cryptographic proofs (digital signatures)
3. **Decentralized**: No dependence on central authority for identifier existence
4. **Context-scoped**: Entities can have multiple DIDs for different contexts/personas
5. **Technology-agnostic**: Can work with distributed ledgers, decentralized file systems, distributed databases, peer-to-peer networks

## Architecture Components

### 1. DID (Decentralized Identifier)
- URI format that identifies a DID subject
- Can refer to person, organization, thing, data model, abstract entity
- Example syntax: `did:method:identifier`

### 2. DID Document
- Contains information about the DID subject
- Includes cryptographic material and verification methods
- Describes services for trusted interactions
- Enables DID controller to prove control

### 3. DID Subject
- The entity identified by the DID
- Determined by the controller of the DID

### 4. DID Controller
- Entity with capability to make changes to DID document
- Can prove control through cryptographic verification

### 5. Verification Methods
- Cryptographic public keys or other mechanisms
- Used to authenticate or authorize interactions
- Types include: Authentication, Assertion, Key Agreement, Capability Invocation, Capability Delegation

### 6. Services
- Endpoints for trusted interactions with DID subject
- Enable discovery of service endpoints

## Design Goals (from specification)
1. **Decentralization**: Remove requirement for centralized authorities
2. **Control**: Give entities direct control over their identifiers
3. **Privacy**: Enable privacy protection through selective disclosure
4. **Security**: Enable cryptographic verification
5. **Proof-based**: Enable entities to prove control through cryptographic proofs
6. **Discoverability**: Make it possible to discover DID documents
7. **Interoperability**: Use standard formats and protocols
8. **Portability**: Enable identifiers to be used across systems
9. **Simplicity**: Favor simple solutions
10. **Extensibility**: Enable extension when possible

## Relationship to Web4

### Similarities
Both Web4 (LCT) and W3C DIDs address decentralized identity, but with different approaches and scope.

**Common Ground**:
- Cryptographic identity verification
- Decentralized architecture (no central authority)
- Controller-owned identifiers
- Support for multiple contexts/personas
- Verification through cryptographic proofs

### Key Differences

**W3C DIDs**:
- **Scope**: Identity layer only (identifier + verification)
- **Maturity**: W3C Recommendation (ratified standard since 2022)
- **Adoption**: 103 method specifications, 46 conformant implementations
- **Ecosystem**: Broad industry support (Digital Bazaar, Evernym, Transmute, Blockchain Commons)
- **Focus**: Interoperability across identity systems
- **Technology**: Method-agnostic (works with any underlying tech)
- **Use Cases**: Digital identity, verifiable credentials, authentication

**Web4 LCT (Linked Context Token)**:
- **Scope**: Complete trust-native internet architecture (identity + witnessing + economic model + authorization)
- **Maturity**: In development, working implementation but not yet standardized
- **Focus**: Trust through witnessed interactions, not just identity
- **Additional Features**: 
  - ATP/ADP economic metering
  - Witnessed presence (MRH tensors)
  - Hardware binding for IoT devices
  - Fine-grained authorization and delegation
  - Real-time budget tracking and enforcement
- **Use Cases**: AI agent authorization, IoT trust networks, energy markets, agent-to-agent commerce

### Potential Relationship
1. **Complementary**: Web4 could potentially build on or integrate with DID standard for identity layer
2. **Competitive**: Web4 LCT could be seen as alternative identity system with additional features
3. **Layered**: DIDs could serve as identity foundation with Web4 adding trust/witnessing layer on top

### Questions for Further Investigation
1. Does Web4 implement DID methods or is LCT a separate identity system?
2. Could Web4's LCT be registered as a DID method?
3. Are there technical incompatibilities between DID architecture and Web4's approach?
4. What does Web4 gain/lose by not using standard DIDs?

## Related W3C Standards
- **Verifiable Credentials**: Standard for expressing credentials on the web
- **DID Use Cases and Requirements**: Document describing use cases
- **DID Specification Registries**: Registry of DID methods and extensions

## Key Organizations in DID Ecosystem
- Digital Bazaar
- Danube Tech
- Evernym/Avast
- Transmute
- Blockchain Commons
- W3C Decentralized Identifier Working Group

## Academic Citations
The DID specification has significant academic backing and has been cited in research on:
- Self-sovereign identity (SSI) systems
- Verifiable credentials
- Blockchain-based identity management
- Privacy-preserving authentication
- Decentralized trust frameworks
