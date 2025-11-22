# Claude Context for Web4

## Machine Information
**Current Machine**: Legion Pro 7 (Native Linux)
- **Model**: Legion Pro 7 16IRX8H
- **OS**: Ubuntu 22.04 LTS (Linux 6.8.0-86-generic)
- **Hardware**: Intel Core i9-13900HX, NVIDIA RTX 4080 (12GB), 32GB RAM
- **Platform**: /home/dp/ai-workspace/web4
- **Working Directory**: /home/dp/ai-workspace/web4

## Authentication
**GitHub PAT Location**: `../.env` (GITHUB_PAT variable)
- Use for pushing: `git push https://dp-web4:$(grep GITHUB_PAT ../.env | cut -d= -f2)@github.com/dp-web4/web4.git`

## Project Overview

Web4 is a trust-native distributed intelligence architecture that implements:
- **Linked Context Tokens (LCTs)**: Unforgeable digital presence
- **Trust Tensors (T3)**: Multi-dimensional trust calculations
- **Dictionary Entities**: Living keepers of meaning across domains
- **Markov Relevancy Horizons (MRH)**: Context boundaries for entities
- **R6 Action Framework**: Intent to reality transformation

## Whitepaper Status

The Web4 whitepaper is actively evolving with:
- **Current Version**: Full technical document (~100+ pages)
- **Planned Split**: Manifesto (10-15 pages) + Technical expansions
- **Key Concepts Documented**:
  - Foundational concepts (LCTs, Entities, Roles, R6, MRH, Dictionaries, Trust as Gravity)
  - Value and trust mechanics (ATP/ADP tokens, T3 tensors)
  - Implementation details and examples
  - Governance and blockchain integration

## Recent Developments

### Entity Relationship Mechanisms (January 2025)
- **Binding**: Permanent identity attachment (hardware to LCT)
- **Pairing**: Authorized operational relationships with symmetric keys
- **Witnessing**: Trust building through observation with bidirectional MRH links
- **Broadcast**: Unidirectional public announcement for discovery
- Documented with concrete implementation examples from modbatt-CAN project

### Web4 Internet Standard Development (January 2025)
- Created comprehensive instructions for formal standard development
- 21-day structured plan for IETF RFC and W3C specification
- Includes reference implementations, conformance tests, and governance framework
- Target: Transform Web4 from concept to legitimate internet standard

### Entity Binding Hierarchy Implementation (January 2025)
- Documented multi-level binding from API-Bridge → App → Pack Controller → Battery Module
- Each level witnesses the level below, creating unforgeable presence chain
- Public key exchange creates bidirectional MRH tensor links
- Physical hardware achieves digital presence through hierarchical witnessing

### Dictionary Entities (August 20, 2024)
- Elevated from implementation detail to foundational concept
- Section 2.6 in Foundational Concepts
- Living entities with their own LCTs
- Manage trust degradation in translation
- Embody compression-trust relationship

### Trust as Gravity (August 20, 2024)
- Added Section 2.7 to Foundational Concepts
- Trust operates as fundamental force
- High-trust entities attract attention, resources, opportunities
- T3 tensor scores create actual force fields

### Navigation Architecture
- Expandable navigation with proper header IDs
- All seven foundational concepts accessible
- Web-first presentation optimized

## Build System

### Whitepaper Generation
```bash
cd whitepaper
./make-pdf.sh    # Generate PDF version
./make-web.sh    # Generate web version with navigation
./make.sh        # Build all formats
```

### Safety Features
- Pre-build conflict checking
- Automatic pull if safe
- Clear conflict resolution instructions
- Complete asset copying

## Key Insights

### LCT Unforgeability Through Witnessed Presence
- **Presence exists only through witnessing** - An entity's presence is real to the extent it is observed and recorded
- **Hierarchical witness chains** - LCTs link to other LCTs, creating trees of contextual witnessing
- **Cross-domain validation** - LCT trees span blockchains, domains, and fractal boundaries
- **Presence accumulation** - The more an entity is witnessed, the more present it becomes
- **Historical immutability** - Accumulated witnessing makes falsifying presence history exponentially harder
- **Reification through observation** - LCTs transform abstract presence into concrete, verifiable reality

### Compression-Trust Unity
- Compression requires trust in shared decompression artifacts
- What appears "lossy" is missing context in receiver
- Dictionaries manage decompression/recompression across domains

### Trust Networks
- High trust = Maximum compression
- Medium trust = Moderate compression
- Low trust = Minimal compression
- Zero trust = Raw data transmission

## Related Projects

### Modbatt-CAN
- Concrete implementation of Web4 entity binding hierarchy
- Demonstrates binding, pairing, witnessing, and broadcast in real hardware
- CAN bus protocol integration with blockchain identity
- Reference implementation for IoT Web4 adoption

### Portal
- Entity connection protocols
- MCP and beyond exploration
- Practical implementation of Web4 concepts

### Memory
- Distributed memory paradigms
- Integration with LCTs
- Temporal sensor patterns

### HRM
- GPU mailbox architecture
- English-First implementation
- Compression-trust insights applied

## Development Philosophy

Web4 isn't just infrastructure—it's the nervous system for a new kind of internet where trust emerges from the interplay of presence, capability, intent, and context.

---

*"In Web4, you don't just have an account. You have presence. You don't just perform roles. You inhabit them. You don't just interact. You leave footprints in the fabric of digital reality itself."*