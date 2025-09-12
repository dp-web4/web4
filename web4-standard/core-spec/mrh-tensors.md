


# MRH (Markov Relevancy Horizon) Specification

This document provides the formal specification for the Markov Relevancy Horizon (MRH), a core concept in Web4 that defines the dynamic context of relationships surrounding each entity. The MRH emerges from the actual relationships an LCT maintains - it is not computed but rather observed from the entity's interaction patterns.

## Core Concept: Context Through Relationships

The MRH is fundamentally different from traditional trust models. Rather than calculating trust scores or maintaining global reputation, each entity's MRH is simply the list of other entities it has relationships with. This creates emergent context - an entity's relevance and trustworthiness emerge from WHO it interacts with, not from abstract metrics.

### Key Principles

1. **MRH is a List, Not a Calculation**: The MRH is literally the arrays of bound, paired, and witnessing LCTs stored in each LCT
2. **Context Emerges from Connections**: An entity's context is defined by its relationships
3. **Dynamic and Self-Updating**: Every binding, pairing, or witness interaction automatically updates the MRH
4. **Horizon Limits Scope**: Relationships beyond a certain depth become irrelevant (Markov property)

## 1. MRH Implementation in LCT

The MRH is implemented directly within each LCT as dynamic arrays:

```json
{
  "lct_id": "lct:web4:...",
  "mrh": {
    "bound": [
      {"lct_id": "lct:web4:...", "type": "parent|child|sibling", "ts": "..."}
    ],
    "paired": [
      {"lct_id": "lct:web4:...", "context": "energy-mgmt", "session_id": "...", "ts": "..."}
    ],
    "witnessing": [
      {"lct_id": "lct:web4:...", "role": "time|audit|oracle", "last_attestation": "..."}
    ],
    "horizon_depth": 3,
    "last_updated": "2025-09-11T15:00:00Z"
  }
}
```

## 2. How MRH Creates Context

### 2.1 Relationship Types Define Context

Each relationship type creates different contextual meaning:

- **Bound Relationships**: Create hierarchical context (parent/child/sibling)
  - Parent binding: Entity inherits trust context from parent
  - Child binding: Entity extends parent's capabilities
  - Sibling binding: Entities share common parent context

- **Paired Relationships**: Create operational context
  - Energy management pairing: Entities can exchange energy credits
  - Data exchange pairing: Entities can share information
  - Service pairing: One entity provides services to another

- **Witness Relationships**: Create validation context
  - Time witnesses: Provide temporal ordering
  - Audit witnesses: Validate compliance
  - Oracle witnesses: Provide external data

### 2.2 Context Propagation

Context flows through the MRH via relationship chains:

1. **Direct Context** (Depth 1): Immediate relationships define primary context
2. **Inherited Context** (Depth 2): Context from relationships' relationships
3. **Network Context** (Depth 3+): Broader network effects, limited by horizon_depth

### 2.3 The Markov Property

The "Markov" in MRH means that beyond a certain depth (horizon_depth), relationships become irrelevant:
- Default horizon_depth = 3 (you, your connections, their connections)
- Beyond this depth, entities are outside your relevancy horizon
- This limits computational complexity and maintains local context focus

## 3. MRH Dynamics and Updates

### 3.1 Automatic Updates

The MRH updates automatically through entity interactions:

| Action | MRH Update | Context Change |
|--------|------------|----------------|
| Binding established | Add to `bound` array | Hierarchical context created |
| Pairing initiated | Add to `paired` array | Operational context created |
| Witness attestation | Add/update `witnessing` array | Validation context strengthened |
| Relationship revoked | Remove from array | Context removed |

### 3.2 Trust Emergence

Trust emerges from MRH patterns rather than calculations:
- Entities with many witness attestations → Higher perceived reliability
- Entities with stable long-term pairings → Established operational trust
- Entities with strong binding hierarchies → Institutional trust

## 4. Future: T3/V3 Trust and Value Tensors

While not yet fully specified, the MRH will eventually support trust and value tensors:

- **T3 (Trust Tensor)**: Multi-dimensional trust metrics derived from MRH patterns
- **V3 (Value Tensor)**: Value exchange metrics tracked through relationships

These will emerge from MRH data rather than being externally imposed.


