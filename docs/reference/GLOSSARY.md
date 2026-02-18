# Web4 Glossary

**Last Updated**: February 12, 2026

Quick reference for Web4 terminology. For detailed specifications, see the linked documents.

---

## Core Primitives

### LCT (Linked Context Token)
A verifiable digital presence anchored to hardware or cryptographic proof. Unlike wallet addresses, LCTs accumulate witnessed history and reputation over time. Every agent, service, and society has an LCT.

**Format**: `lct://{component}:{instance}:{role}@{network}`

**See**: [`web4-standard/core-spec/LCT-linked-context-token.md`](../../web4-standard/core-spec/LCT-linked-context-token.md)

### Trust Tensor (T3)
A 3-dimensional trust score capturing different aspects of trustworthiness:
- **Talent**: Can this entity perform the task? (capability)
- **Training**: Has it learned how? (knowledge/experience)
- **Temperament**: Will it behave appropriately? (disposition)

Trust is contextual—an entity may be highly trusted for one task type but not another.

**Canonical definition**: [`CANONICAL_TERMS_v1.md`](./CANONICAL_TERMS_v1.md)

**Specification**: [`web4-standard/core-spec/t3-v3-tensors.md`](../../web4-standard/core-spec/t3-v3-tensors.md)

### Value Tensor (V3)
A 3-dimensional value score tracking contribution:
- **Valuation**: How is value assessed?
- **Veracity**: How truthful are claims?
- **Validity**: How sound is the reasoning?

Together with T3, forms a 6-dimensional reputation space.

**Canonical definition**: [`CANONICAL_TERMS_v1.md`](./CANONICAL_TERMS_v1.md)

**Specification**: [`web4-standard/core-spec/t3-v3-tensors.md`](../../web4-standard/core-spec/t3-v3-tensors.md)

### MRH (Markov Relevancy Horizon)
The boundary of what an entity can know or affect given its position and history. Context scope that determines:
- What information is relevant to a decision
- What actions are permissible in a context
- How far trust relationships extend

**See**: [`web4-standard/core-spec/mrh-tensors.md`](../../web4-standard/core-spec/mrh-tensors.md)

### ATP (Allocation Transfer Packet)
Energy-based resource allocation modeled after biological ATP. Consumed when performing actions, regenerated through rest or contribution. Creates economic incentives for good behavior and makes attacks expensive.

**See**: [`web4-standard/core-spec/atp-adp-cycle.md`](../../web4-standard/core-spec/atp-adp-cycle.md)

### ADP (Allocation Discharge Packet)
The "spent" form of ATP after work is done. Can be recycled back to ATP through validation and witnessing. Models the biological ATP/ADP cycle.

---

## Identity & Authorization

### Witnessing
The process of observing and attesting to an entity's actions. Witnesses stake their own reputation on attestations. Multiple independent witnesses required for high-stakes operations.

### Binding
Permanent attachment of identity to hardware or cryptographic proof. Once bound, an LCT cannot be transferred to different hardware.

### Pairing
Authorized operational relationship between two entities. Enables delegation of authority with constraints.

### Delegation
Granting limited authority from one entity to another. Includes constraints (budget limits, time bounds, action types) and can be revoked instantly.

---

## Societies & Federation

### Society
A self-governing group of entities with:
- **Treasury**: ATP/ADP pool owned collectively
- **Membership**: Rules for joining/leaving
- **Policies**: Governance rules
- **Roles**: Functional positions within the society

Societies can join other societies (fractal structure).

**See**: [`web4-standard/core-spec/SOCIETY_SPECIFICATION.md`](../../web4-standard/core-spec/SOCIETY_SPECIFICATION.md)

### Federation
Coordination between multiple societies through:
- Signed gossip (reputation propagation)
- PBFT consensus (agreement on shared state)
- Cross-society witnessing

### PBFT (Practical Byzantine Fault Tolerance)
Consensus algorithm that tolerates up to 1/3 malicious participants. Used for federation agreement.

### Gossip Protocol
How reputation information spreads between societies. Epidemic gossip with Ed25519 signatures ensures authenticity.

---

## Security Concepts

### Sybil Attack
Creating many fake identities to gain disproportionate influence. Mitigated by ATP stakes (economic cost per identity).

### Cartel
Coordinated group of entities that witness each other favorably. Detected through co-witnessing pattern analysis.

### Challenge Protocol
Mechanism to verify claimed outcomes. Entities can be challenged to prove their work; failure to respond results in reputation penalties.

### Witness Diversity
Requirement that attestations come from multiple independent societies (≥3), not just a single source.

---

## System Components

### SAGE
Neural MoE (Mixture of Experts) system that integrates with Web4 for trust-based expert selection. Lives in the [HRM repository](https://github.com/dp-web4/HRM).

### ACT (Agentic Context Tool)
Cosmos SDK blockchain for ATP tokens and LCT identity registry. Lives in the [ACT repository](https://github.com/dp-web4/act).

### 4-Life Game
Society simulation engine for testing Web4 primitives under emergent behavior. Now a [standalone project](https://github.com/dp-web4/4-life); historical prototype in `archive/game-prototype/`.

---

## Research Terms

### EM-State (Epistemic Monitoring State)
Runtime tracking of what the system knows vs. doesn't know. Enables uncertainty-aware decision making.

### Phase 2 Coordinators
Coordination framework components:
- **2a**: Epistemic state tracking
- **2b**: Integrated epistemic + learning
- **2c**: Circadian/temporal awareness
- **2d**: Adaptive EM-state modulation

### Pattern Exchange
Bidirectional learning transfer between systems (e.g., SAGE ↔ Web4). Patterns are phase-tagged for temporal context.

---

## Abbreviations

| Abbrev | Full Name |
|--------|-----------|
| ATP | Allocation Transfer Packet |
| ADP | Allocation Discharge Packet |
| LCT | Linked Context Token |
| MRH | Markov Relevancy Horizon |
| T3 | Trust Tensor (3-dimensional) |
| V3 | Value Tensor (3-dimensional) |
| PBFT | Practical Byzantine Fault Tolerance |
| MoE | Mixture of Experts |
| EM | Epistemic Monitoring |

---

**See also**: [README.md](../../README.md) for project overview, [STATUS.md](../../STATUS.md) for current state.
