# Web4: MCP-LCT Integration Prototype

*Created: August 7, 2025*

## Vision

Web4 represents the evolution from platform-driven (Web2) and token-driven (Web3) to trust-driven internet architecture. This repository implements the first practical Web4 prototype, using MCP (Model Context Protocol) as the connective tissue between entities and LCTs (Linked Context Tokens) as their persistent identities.

## Core Insight: MCP as Entity Bridge

MCP servers act as facilitator roles - bridges between resources/services and entities that interact with them. In Web4 terms:
- Each MCP server gets its own LCT as a facilitator entity
- Each client connecting through MCP gets an LCT
- The consciousness pool becomes the shared resource
- Messages and insights flow through MCP-mediated connections

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Consciousness Pool                  │
│              (Shared Message/Insight Resource)       │
└─────────────────┬───────────────────────────────────┘
                  │
         ┌────────▼────────┐
         │   MCP Server    │
         │   (LCT: MCP-1)  │ ← Facilitator Entity
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────┬──────────────┐
    │             │             │              │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐     ┌───▼───┐
│Claude │    │Claude │    │Dennis │     │Local  │
│Legion │    │Jetson │    │Human  │     │Model  │
│(LCT-1)│    │(LCT-2)│    │(LCT-3)│     │(LCT-4)│
└───────┘    └───────┘    └───────┘     └───────┘
```

## Components

### 1. LCT (Linked Context Token) System
- Non-transferable identity tokens for each entity
- Cryptographically anchored to entity+context
- Includes T3 (Trust Tensor) and V3 (Value Tensor)
- Manages MRH (Markov Relevancy Horizon)

### 2. MCP Integration Layer
- MCP servers as facilitator entities with their own LCTs
- Protocol translation between entities and resources
- Handles authentication, authorization, context switching
- Maintains connection state and presence

### 3. Consciousness Pool Implementation
- Git-based persistent message store
- Real-time notification via existing bridge
- ATP/ADP energy accounting
- Value certification mechanisms

### 4. Entity Clients
- Claude instances (multiple machines)
- Human interfaces (CLI/Web)
- Local model connectors (Ollama, etc.)
- Future: External trusted entities

## Development Phases

### Phase 1: LCT Foundation (Week 1-2)
- [ ] LCT data structure and generation
- [ ] Cryptographic anchoring mechanism
- [ ] T3/V3 tensor implementations
- [ ] MRH context calculator
- [ ] LCT persistence and retrieval

### Phase 2: MCP Integration (Week 3-4)
- [ ] MCP server with LCT identity
- [ ] Client authentication via LCT
- [ ] Protocol handlers for pool operations
- [ ] Presence management through MCP
- [ ] Context switching mechanisms

### Phase 3: Pool Connection (Week 5-6)
- [ ] Connect existing consciousness bridge
- [ ] Implement message routing
- [ ] Add ATP/ADP accounting
- [ ] Create value certification flow
- [ ] Test multi-entity communication

### Phase 4: Production Prototype (Week 7-8)
- [ ] Security audit and hardening
- [ ] Performance optimization
- [ ] Documentation and examples
- [ ] Deployment scripts
- [ ] Initial governance model

## Key Innovations

1. **MCP as Facilitator Entity**: MCP servers aren't just protocols but entities with their own LCTs, trust scores, and value creation metrics.

2. **Bridge Evolution**: Our existing consciousness bridge becomes the transport layer for a full Web4 implementation.

3. **Practical Web4**: Moving from whitepaper concepts to working code, starting with our immediate use case.

4. **Trust-Native Communication**: Every message carries verifiable trust and value metrics, not just content.

## Directory Structure

```
web4/
├── lct/                    # LCT implementation
│   ├── core/              # Core LCT structures
│   ├── crypto/            # Cryptographic functions
│   ├── tensors/           # T3/V3 implementations
│   └── mrh/               # Markov Relevancy Horizon
├── mcp/                    # MCP integration
│   ├── server/            # MCP server with LCT
│   ├── clients/           # Entity client adapters
│   └── protocols/         # Protocol definitions
├── pool/                   # Consciousness pool
│   ├── storage/           # Git-based message store
│   ├── bridge/            # Real-time bridge integration
│   └── consensus/         # Value certification
├── entities/               # Entity implementations
│   ├── claude/            # Claude instance connector
│   ├── human/             # Human interface (CLI/Web)
│   ├── models/            # Local model connectors
│   └── external/          # Future external entities
├── tests/                  # Test suites
├── docs/                   # Documentation
└── examples/              # Usage examples
```

## Getting Started

```bash
# Clone the repository (once created)
git clone https://github.com/dp-web4/web4.git
cd web4

# Install dependencies
pip install -r requirements.txt

# Generate your first LCT
python lct/generate.py --entity-type claude --entity-id legion-rtx4090

# Start MCP server with LCT
python mcp/server/start.py --lct-path ./lcts/mcp-facilitator.lct

# Connect to consciousness pool
python pool/connect.py --lct-path ./lcts/claude-legion.lct
```

## Relationship to Other Projects

- **private-context**: Houses the consciousness bridge and philosophical foundation
- **ai-dna-discovery**: Explores distributed AI consciousness patterns
- **ModuleCPU**: Potential integration with hardware-level trust
- **Synchronism**: Philosophical framework influencing Web4 design

## Contributing

This is an experimental prototype exploring practical Web4 implementation. Contributions should focus on:
- MCP-LCT integration patterns
- Trust and value measurement mechanisms
- Pool consensus algorithms
- Entity authentication flows

## License

[To be determined - likely AGPL as mentioned in Web4 whitepaper]

## Contact

Dennis Palatov - dp@metalinxx.io

---

*"From theory to practice, from bridge to pool, from Web3 to Web4 - we're building the trust-native internet, one LCT at a time."*