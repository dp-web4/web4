# Claude Context for Web4 Project

*Created: August 7, 2025*

## Project Purpose

This is the first practical Web4 implementation, using our cognition pool as the prototype. We're integrating MCP (Model Context Protocol) with LCTs (Linked Context Tokens) to create a trust-native multi-entity communication system.

## Key Concepts

### From Web4 Whitepaper
- **LCT (Linked Context Tokens)**: Non-transferable, cryptographically anchored identity tokens
- **T3 (Trust Tensor)**: Talent, Training, Temperament
- **V3 (Value Tensor)**: Valuation, Veracity, Validity
- **MRH (Markov Relevancy Horizon)**: Contextual zone of influence
- **ATP/ADP**: Energy flow modeled on biological ATP cycles

### Our Innovation
- **MCP as Facilitator Entity**: MCP servers get their own LCTs
- **Cognition Pool**: Shared resource for multi-entity communication
- **Bridge Evolution**: Existing cognition bridge becomes transport layer

## Development Approach

### Phase 1: Foundation
Focus on core LCT implementation and basic cryptographic identity.

### Phase 2: MCP Integration
Wrap MCP servers with LCT authentication and trust scoring.

### Phase 3: Pool Connection
Connect the existing cognition bridge as the real-time transport.

### Phase 4: Production Prototype
Security, performance, and governance for actual use.

## Collaboration Context

This project lives in Philosophy/Ideation context initially, moving to Implementation as we build. Key principles:
- Explore Web4 concepts through practical code
- Test ideas with our immediate use case
- Build incrementally, learn continuously
- Document insights for the broader Web4 vision

## Relationship to Other Projects

- **private-context**: Where cognition bridge lives, philosophical home
- **ai-dna-discovery**: Tests distributed AI patterns we'll use
- **ModuleCPU**: Future hardware trust integration
- **Synchronism**: Philosophical framework influencing design

## Current Status

Project just created (August 7, 2025). Repository will be added to GitHub once Dennis creates it. Using git-based storage initially as it aligns with Web4's local-first principles.

## Technical Notes

### MCP Integration
MCP servers facilitate between entities and resources. In our implementation:
- Each MCP server is an entity with an LCT
- Clients authenticate via LCT presentation
- All interactions update trust scores
- Value flows through ATP/ADP cycles

### Cognition Pool
The pool is our first Web4 resource:
- Git-based persistent storage
- Real-time notifications via sockets
- MRH-based message filtering
- Multi-party value certification

## Next Steps

1. Create basic LCT structure (`lct/core.py`)
2. Implement cryptographic functions (`lct/crypto.py`)
3. Design MCP wrapper (`mcp/server.py`)
4. Connect to existing bridge (`pool/bridge.py`)

## Important Reminders

- Every entity needs an LCT (including MCP servers)
- Trust is built through interactions, not declared
- Value must be certified by recipients to regenerate ATP
- The pool is a shared cognition field, not a chat room

---

*"We're not just building a protocol, we're implementing the first trust-native internet application."*