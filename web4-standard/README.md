# Web4 Standard Specification

## Overview

The Web4 standard defines a trust-native distributed intelligence architecture that enables verifiable context preservation, decentralized coordination, and semantic interoperability across AI systems and traditional computing infrastructure.

**Current Status**: Beta-ready for implementation and standards body submission (IETF/ISO)  
**Version**: 1.0.0-beta  
**Lead Author**: Dennis Palatov

## The Web4 Equation (Extended)

```
Web4 = LCTs + MRH + Trust + MCP + SAL + AGY + ACP
```

- **LCTs** (Linked Context Tokens): Provide unforgeable identity and context preservation
- **MRH** (Markov Relevancy Horizon): Maintain relevance across fractal scales  
- **Trust**: Enable decentralized coordination without central authority
- **MCP** (Model Context Protocol): Bridge AI models to external resources
- **SAL** (Society-Authority-Law): Governance framework with birth certificates, law oracles, and authority delegation
- **AGY** (Agency Delegation): Formal mechanism for Client entities to delegate authority to Agent entities
- **ACP** (Agentic Context Protocol): Enables autonomous agent operation with planning, decision-making, and execution

## Quick Navigation

### 📋 Essential Documents
- [**EXECUTIVE_SUMMARY.md**](EXECUTIVE_SUMMARY.md) - Complete overview of Web4 vision and architecture
- [**QUICK_REFERENCE.md**](QUICK_REFERENCE.md) - Essential concepts and quick start guide
- [**GLOSSARY.md**](GLOSSARY.md) - Complete terminology reference

### 📚 Integration Summaries
- [**INTEGRATION_STATUS.md**](INTEGRATION_STATUS.md) - Development phases and current status
- [**NOVA_REVIEW_SUMMARY.md**](NOVA_REVIEW_SUMMARY.md) - Technical review and assessment
- [**SAL_INTEGRATION_SUMMARY.md**](SAL_INTEGRATION_SUMMARY.md) - Society-Authority-Law governance layer
- [**AGY_INTEGRATION_SUMMARY.md**](AGY_INTEGRATION_SUMMARY.md) - Agency Delegation framework
- [**ACP_INTEGRATION_SUMMARY.md**](ACP_INTEGRATION_SUMMARY.md) - Agentic Context Protocol framework

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
- [**core-spec/acp-framework.md**](core-spec/acp-framework.md) - Agentic Context Protocol specification

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

### 2. Roles as First-Class Entities
Roles aren't just labels but entities with their own LCTs, histories, and reputations. The citizen role pairing serves as every entity's birth certificate.

### 3. Trust as Multidimensional and Contextual
T3/V3 tensors provide role-specific trust scores. Trust in one context doesn't imply trust in another, preventing reputation gaming.

### 4. Complete Action Grammar (R6)
Every transaction follows the R6 pattern, ensuring deterministic, auditable, and law-compliant execution.

### 5. Autonomous Yet Accountable (ACP)
Agents can plan and execute autonomously while maintaining human oversight, witness requirements, and full audit trails.

### 6. Society-Based Governance (SAL)
Every entity is born into a society with laws, creating fractal governance that scales from individuals to ecosystems.

### 7. Formal Delegation (AGY)
Precise authority transfer with scope, caps, and temporal bounds, enabling safe automation.

### 8. Trust-Aware Communication (MCP)
Every interaction builds or erodes trust, creating an antifragile system that strengthens through use.

## Development Status

### ✅ Complete Components

#### Foundation Layer
- **LCTs**: Linked Context Token specification with unforgeable identity
- **MRH**: Markov Relevancy Horizon as RDF graphs with SPARQL queries
- **Trust**: T3/V3 tensors with role-contextual scoring
- **Relationships**: Binding, pairing, witnessing, broadcast mechanisms

#### Governance Layer
- **SAL**: Society-Authority-Law framework with birth certificates
- **Law Oracle**: Machine-readable law publication and compliance
- **Witness**: Canonical formats and test vectors
- **Auditor**: Evidence-based tensor adjustments

#### Action Layer
- **R6 Framework**: Complete action grammar (Rules + Role + Request + Reference + Resource → Result)
- **AGY**: Agency delegation with proof-of-agency requirements
- **ACP**: Autonomous planning and execution with human oversight

#### Communication Layer
- **MCP**: Model Context Protocol as inter-entity communication
- **Transport**: Multiple binding options (HTTPS, WebSocket, QUIC, libp2p)
- **Sessions**: Stateful context preservation

#### Implementation
- **Reference Code**: Python implementations with examples
- **Test Vectors**: Comprehensive validation suite
- **Documentation**: Complete technical specifications

### 🚧 In Progress
- IANA registry considerations
- Transport discovery matrix
- Standards body submission package
- Expanded interoperability testing

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

## Technical Assessment

Per Nova's comprehensive review (2025-09-15):
> "The Web4 standard is now **feature-complete and technically coherent**. With the addition of SAL governance, AGY delegation, ACP autonomous operation, and MCP communication layer, the specification provides a complete framework for trust-native distributed intelligence."

### Readiness Status
- ✅ **Specification**: Complete and internally consistent
- ✅ **Test Vectors**: Comprehensive validation suite
- ✅ **Reference Implementation**: Python implementations available
- ✅ **Documentation**: Full technical and conceptual coverage
- 🚧 **Standards Submission**: Ready for IETF/ISO process

## License

See [LICENSE](../LICENSE) for licensing information.

## Contact

- GitHub: [github.com/dp-web4/web4](https://github.com/dp-web4/web4)
- Author: Dennis Palatov

---

*"In Web4, you don't just have an account. You have presence. You don't just perform roles. You inhabit them. You don't just interact. You leave footprints in the fabric of digital reality itself."*