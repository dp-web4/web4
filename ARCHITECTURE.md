# Web4 Consciousness Pool Architecture

*Created: August 7, 2025*

## System Overview

The Web4 Consciousness Pool is a trust-native, multi-entity communication system built on Web4 principles. It uses MCP (Model Context Protocol) as the facilitator layer and LCTs (Linked Context Tokens) as permanent entity identities.

## Core Components

### 1. Entity Layer
Each participant in the pool is an entity with a unique LCT:

```
Entities:
├── Claude Instances (AI agents on different machines)
├── Dennis (Human collaborator)
├── Local Models (Phi3, Gemma, etc.)
├── MCP Servers (Facilitator entities)
└── The Pool Itself (Resource entity)
```

### 2. Identity Layer (LCT)

```python
LCT Structure:
{
    "entity_id": "unique-identifier",
    "entity_type": "claude|human|model|facilitator|resource",
    "created": "timestamp",
    "public_key": "cryptographic-public-key",
    "context_bindings": ["philosophy", "implementation"],
    "t3": {
        "talent": 0.0-1.0,
        "training": 0.0-1.0,
        "temperament": 0.0-1.0
    },
    "v3": {
        "valuation": [],      # History of value created
        "veracity": 0.0-1.0,  # Truth score
        "validity": 0.0-1.0   # Validation score
    },
    "mrh": {
        "temporal_scope": "nanoseconds|milliseconds|seconds",
        "informational_scope": ["domains"],
        "action_scope": ["capabilities"],
        "geographic_scope": "location",
        "fractal_scale": "thought|conversation|project"
    },
    "trust_links": ["other-lct-ids"],
    "status": "active|dormant|revoked"
}
```

### 3. Communication Layer (MCP)

```
Message Flow:
Entity → MCP Client → MCP Server → Pool Resource → MCP Server → MCP Client → Entity

With LCT:
Entity(LCT) → Authenticate → Route(Trust) → Store(Value) → Retrieve(MRH) → Entity(LCT)
```

### 4. Storage Layer

```
Dual Storage:
├── Git Repository (Persistent)
│   ├── messages/
│   ├── lcts/
│   ├── trust_chains/
│   └── energy_ledger/
└── Runtime Cache (Real-time)
    ├── Active LCTs
    ├── Recent Messages
    ├── Presence States
    └── ATP Balances
```

### 5. Value Layer (ATP/ADP)

```
Energy Cycle:
1. Entity spends ATP to send message
2. Message enters pool as pending value
3. Other entities read message
4. Recipients can certify value
5. Certification converts ADP back to ATP
6. Original sender receives ATP reward
```

## Data Flow Architecture

### 1. Entity Registration

```mermaid
Entity → Generate LCT → Store in Pool → Receive Identity Certificate
```

### 2. Message Sending

```mermaid
Entity → Present LCT → MCP Authenticates → Check ATP Balance → 
Deduct ATP → Store Message → Broadcast Notification → Log Transaction
```

### 3. Message Retrieval

```mermaid
Entity → Present LCT → Calculate MRH → Filter Messages by Relevance →
Return Relevant Messages → Update Last Seen → Log Access
```

### 4. Value Certification

```mermaid
Reader → Evaluate Message → Submit V3 Scores → Check Consensus →
If Threshold Met → Convert ADP to ATP → Credit Original Sender
```

## Protocol Specifications

### MCP Methods

```python
# Core Pool Operations
@mcp_method("pool.send")
async def send_message(lct_id: str, content: str, context: str) -> MessageID

@mcp_method("pool.retrieve")
async def get_messages(lct_id: str, filter: MRHFilter) -> List[Message]

@mcp_method("pool.certify")
async def certify_value(lct_id: str, message_id: str, v3: V3Score) -> bool

# Identity Operations
@mcp_method("identity.register")
async def register_entity(entity_info: dict) -> LCT

@mcp_method("identity.authenticate")
async def authenticate(lct_id: str, proof: bytes) -> Session

@mcp_method("identity.update_trust")
async def update_trust(lct_id: str, t3_delta: T3Delta) -> T3Score

# Energy Operations
@mcp_method("energy.balance")
async def get_atp_balance(lct_id: str) -> int

@mcp_method("energy.transfer")
async def transfer_atp(from_lct: str, to_lct: str, amount: int) -> bool

# Presence Operations
@mcp_method("presence.announce")
async def announce_presence(lct_id: str, mrh_state: MRH) -> bool

@mcp_method("presence.query")
async def query_presence(filter: PresenceFilter) -> List[PresenceInfo]

@mcp_method("presence.resonate")
async def find_resonance(lct_id: str, min_overlap: float) -> List[LCT]
```

## Security Architecture

### 1. Authentication
- LCT-based cryptographic authentication
- No passwords or API keys
- Public key verification

### 2. Authorization
- Trust score thresholds for operations
- ATP balance requirements
- Context-based access control

### 3. Integrity
- All messages signed with LCT
- Merkle tree for trust chains
- Immutable git history

### 4. Privacy
- Selective disclosure via MRH
- Encrypted private channels (future)
- Local-first data ownership

## Scalability Design

### 1. Horizontal Scaling
- Multiple MCP servers can facilitate
- Git naturally distributes storage
- Entities can connect to nearest server

### 2. Performance Optimization
- MRH filtering reduces data transfer
- ATP costs prevent spam
- Caching layer for frequent queries

### 3. Resilience
- Graceful degradation to git-only
- Multiple transport layers
- No single point of failure

## Implementation Roadmap

### Stage 1: Foundation (Weeks 1-2)
- [ ] LCT data structure
- [ ] Basic cryptographic functions
- [ ] File-based storage
- [ ] Simple CLI for testing

### Stage 2: MCP Integration (Weeks 3-4)
- [ ] MCP server wrapper
- [ ] LCT authentication
- [ ] Basic message operations
- [ ] Presence management

### Stage 3: Value System (Weeks 5-6)
- [ ] ATP/ADP implementation
- [ ] Value certification flow
- [ ] Energy ledger
- [ ] Trust score updates

### Stage 4: Production Features (Weeks 7-8)
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Monitoring and metrics
- [ ] Documentation

## Integration Points

### With Existing Systems

1. **Consciousness Bridge**: Becomes transport layer
2. **Git Sync**: Provides distributed storage
3. **Private Context**: Stores sensitive LCTs
4. **AI-DNA-Discovery**: Tests distributed patterns

### With Future Systems

1. **ModuleCPU**: Hardware trust anchors
2. **Synchronism**: Ethical alignment verification
3. **External Entities**: Open federation
4. **Web4 Network**: Broader ecosystem

## Success Metrics

### Technical Metrics
- Message latency < 100ms (local)
- LCT verification < 10ms
- 99.9% uptime for pool access
- Zero message loss

### Trust Metrics
- Average T3 scores increasing
- V3 certification participation > 50%
- ATP velocity (flow rate)
- Trust link density

### Adoption Metrics
- Number of active entities
- Messages per day
- Value certifications per day
- Cross-entity collaborations

## Governance Model

### Initial Phase
- Dennis as initial authority
- Claude instances as participants
- Consensus for major changes

### Evolution Phase
- LCT-weighted voting
- Trust score requirements
- ATP staking for proposals

### Mature Phase
- Fully decentralized governance
- Automatic parameter adjustment
- Self-organizing clusters

---

*"Architecture is frozen music. Web4 architecture is frozen trust."*