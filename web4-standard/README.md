# Web4 Standard Specification

## Overview

The Web4 standard defines a trust-native distributed intelligence architecture that enables verifiable context preservation, decentralized coordination, and semantic interoperability across AI systems and traditional computing infrastructure.

**Current Status**: Alpha-ready for independent implementations, Beta-ready for submission (IETF/ISO)

## The Web4 Equation (Extended)

```
Web4 = LCTs + MRH + Trust + MCP + SAL + AGY
```

- **LCTs** (Linked Context Tokens): Provide unforgeable identity and context preservation
- **MRH** (Markov Relevancy Horizon): Maintain relevance across fractal scales  
- **Trust**: Enable decentralized coordination without central authority
- **MCP** (Model Context Protocol): Bridge AI models to external resources
- **SAL** (Society-Authority-Law): Governance framework with birth certificates, law oracles, and authority delegation
- **AGY** (Agency Delegation): Formal mechanism for Client entities to delegate authority to Agent entities

## Quick Navigation

### 📚 Core Documentation
- [**QUICK_REFERENCE.md**](QUICK_REFERENCE.md) - Essential concepts and quick start guide
- [**GLOSSARY.md**](GLOSSARY.md) - Complete terminology reference
- [**INTEGRATION_STATUS.md**](INTEGRATION_STATUS.md) - Development phases and current status
- [**NOVA_REVIEW_SUMMARY.md**](NOVA_REVIEW_SUMMARY.md) - Technical review and assessment
- [**SAL_INTEGRATION_SUMMARY.md**](SAL_INTEGRATION_SUMMARY.md) - Society-Authority-Law governance layer
- [**AGY_INTEGRATION_SUMMARY.md**](AGY_INTEGRATION_SUMMARY.md) - Agency Delegation framework

### 🔧 Core Specifications

#### Identity & Context
- [**protocols/web4-lct.md**](protocols/web4-lct.md) - Linked Context Token specification
- [**MRH_RDF_SPECIFICATION.md**](MRH_RDF_SPECIFICATION.md) - Markov Relevancy Horizon as RDF graphs
- [**MRH_THEORETICAL_FOUNDATION.md**](MRH_THEORETICAL_FOUNDATION.md) - Theory extending Markov blankets

#### Entity Relationships
- [**protocols/web4-entity-relationships.md**](protocols/web4-entity-relationships.md) - Binding, pairing, witnessing, broadcast
- [**core-spec/web4-society-authority-law.md**](core-spec/web4-society-authority-law.md) - SAL governance framework
- [**MCP_ENTITY_SPECIFICATION.md**](MCP_ENTITY_SPECIFICATION.md) - MCP servers as Web4 entities
- [**WEB4_WITNESSING_SPECIFICATION.md**](WEB4_WITNESSING_SPECIFICATION.md) - Canonical witness formats

#### Trust & Tensors
- [**core-spec/mrh-tensors.md**](core-spec/mrh-tensors.md) - MRH tensor specification
- [**core-spec/t3-v3-tensors.md**](core-spec/t3-v3-tensors.md) - Trust and value tensors
- [**R6_TENSOR_GUIDE.md**](R6_TENSOR_GUIDE.md) - Role, Rights, Responsibilities, Risks, Rewards, Results
- [**core-spec/r6-framework.md**](core-spec/r6-framework.md) - R6 Action Framework specification

#### Protocols
- [**core-spec/mcp-protocol.md**](core-spec/mcp-protocol.md) - Model Context Protocol as inter-entity communication layer
- [**protocols/web4-handshake.md**](protocols/web4-handshake.md) - HPKE-based handshake protocol
- [**protocols/web4-metering.md**](protocols/web4-metering.md) - ATP/ADP resource exchange
- [**core-spec/errors.md**](core-spec/errors.md) - Error taxonomy and handling

### 🛠️ Implementation

#### Reference Implementations
- [**mrh_rdf_implementation.py**](mrh_rdf_implementation.py) - MRH as RDF graphs
- [**mrh_sparql_queries.py**](mrh_sparql_queries.py) - SPARQL query examples
- [**mrh_trust_propagation.py**](mrh_trust_propagation.py) - Trust flow algorithms
- [**mrh_migration_tool.py**](mrh_migration_tool.py) - Migration from simple to RDF format
- [**mrh_visualizer.py**](mrh_visualizer.py) - Interactive graph visualization

#### Testing & Validation
- [**testing/witness-vectors/**](testing/witness-vectors/) - Witness interop test vectors
- [**testing/validator/**](testing/validator/) - Vector validation tools
- [**validate_vectors.py**](validate_vectors.py) - Standalone validator script
- [**implementation/tests/**](implementation/tests/) - Test suites and examples

### 📋 Profiles & Registries

#### Conformance Profiles
- [**profiles/edge-device-profile.md**](profiles/edge-device-profile.md) - Edge device profile
- [**profiles/peer-to-peer-profile.md**](profiles/peer-to-peer-profile.md) - Peer-to-peer profile
- [**profiles/cloud-service-profile.md**](profiles/cloud-service-profile.md) - Cloud service profile
- [**profiles/blockchain-bridge-profile.md**](profiles/blockchain-bridge-profile.md) - Blockchain integration

#### Registries
- [**registries/README.md**](registries/README.md) - IANA registry templates
- [**registries/cipher-suites.md**](registries/cipher-suites.md) - Cryptographic suites
- [**registries/error-codes.md**](registries/error-codes.md) - Error code registry
- [**registries/extensions.md**](registries/extensions.md) - Protocol extensions

### 🏗️ Architecture

- [**architecture/document_structure.md**](architecture/document_structure.md) - Standard organization
- [**architecture/extensibility_framework.md**](architecture/extensibility_framework.md) - Extension mechanisms
- [**architecture/grammar_and_notation.md**](architecture/grammar_and_notation.md) - Notation conventions
- [**core-spec/security-framework.md**](core-spec/security-framework.md) - Security architecture

### 📖 Additional Resources

- [**RELATIONSHIP_GUIDE.md**](RELATIONSHIP_GUIDE.md) - Entity relationship patterns
- [**core-spec/data-formats.md**](core-spec/data-formats.md) - Data format specifications
- [**CONSISTENCY_REPORT.md**](CONSISTENCY_REPORT.md) - Standard consistency analysis

## Key Innovations

### 1. Markov Relevancy Horizon (MRH)
Created by Dennis Palatov, MRH extends the information-theoretic concept of Markov blankets to explicitly encompass fractal scales, enabling systems to maintain context across multiple levels of organization.

### 2. Unified Witnessing
Nova's witness specification provides canonical COSE/JOSE formats for verifiable observation without centralized authorities, with three core roles: time, audit-minimal, and oracle.

### 3. MCP Entity Integration  
MCP servers are defined as both responsive (return results) and delegative (front-end for resources), completing the Web4 equation by bridging AI to the external world.

### 4. Trust Propagation
Sophisticated algorithms for trust flow through MRH graphs, supporting multiple models (multiplicative, probabilistic, maximal) with temporal decay.

### 5. Agency Delegation (AGY)
Formal delegation mechanism where Client entities authorize Agent entities to act on their behalf with scoped constraints, resource caps, and proof-of-agency requirements.

## Development Status

### ✅ Complete
- Core protocol specifications
- Entity relationship mechanisms  
- Witness specification and vectors
- MRH as RDF implementation
- MCP entity definition
- Trust propagation algorithms
- Reference implementations
- Test vectors and validators
- SAL governance framework (Society-Authority-Law)
- Law Oracle specification
- Enhanced birth certificates
- Auditor role with adjustment powers
- R6 Action Framework documentation
- AGY (Agency Delegation) framework with proof-of-agency

### 🚧 In Progress
- Transport & discovery matrix
- Expanded interop vectors
- IANA considerations
- Submission preparation

## Getting Started

1. **Read the Concepts**: Start with [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. **Understand the Terms**: Review [GLOSSARY.md](GLOSSARY.md)
3. **Explore Examples**: Check implementation examples in [implementation/](implementation/)
4. **Run Tests**: Use test vectors in [testing/](testing/)
5. **Choose a Profile**: Select appropriate [profile](profiles/) for your use case

## Contributing

See [community/CONTRIBUTING.md](community/CONTRIBUTING.md) for contribution guidelines.

## Governance

See [community/governance.md](community/governance.md) for standard maintenance and evolution procedures.

## Assessment

Per Nova's comprehensive review (2025-09-13):
> "This draft is now **substantively complete and technically coherent**. With the unified Witness specification and additional interop vectors, it is alpha-ready for independent implementations and beta-ready for submission (IETF/ISO)."

## License

See [LICENSE](../LICENSE) for licensing information.

## Contact

- GitHub: [github.com/dp-web4/web4](https://github.com/dp-web4/web4)
- Author: Dennis Palatov

---

*"In Web4, you don't just have an account. You have presence. You don't just perform roles. You inhabit them. You don't just interact. You leave footprints in the fabric of digital reality itself."*