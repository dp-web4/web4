# Web4 Canonical Terms v1.0

**Version**: 1.0.0
**Last Updated**: February 12, 2026
**Status**: Authoritative

This document defines the **canonical meanings** of all Web4 terminology. When conflicts arise between documents, this file governs.

---

## Core Identity Primitives

### LCT (Linked Context Token)

**Definition**: An unforgeable digital identity that accumulates witnessed history and reputation over time.

**NOT**: Lifecycle-Continuous Trust, Linear Context Tracker, or any other expansion.

**Format**: `lct://{component}:{instance}:{role}@{network}`

**Example**: `lct://sage:agent-001:expert@mainnet`

**Specification**: [`web4-standard/core-spec/LCT-linked-context-token.md`](../../web4-standard/core-spec/LCT-linked-context-token.md)

---

## Trust and Value Tensors

### T3 (Trust Tensor)

**Definition**: A 3-dimensional tensor measuring trustworthiness:
- **Talent**: Can this entity perform the task? (capability)
- **Training**: Has it learned how? (knowledge/experience)
- **Temperament**: Will it behave appropriately? (disposition)

Each dimension is a **root node in an open-ended RDF sub-graph**, not a scalar. Implementations MUST support the three base dimensions and MAY define contextualized sub-dimensions linked via `web4:subDimensionOf`. The scalar value at each root is the aggregate of its sub-graph. The graph has no built-in dimensional bound — that is what makes T3 part of an ontology, not a fixed data structure.

**NOT**: A 6-dimensional tensor (that's T3+V3 combined).

**NOT**: Trust-Tracing-Tensor, Trust-Transfer-Token, or similar.

**Specification**: [`web4-standard/core-spec/t3-v3-tensors.md`](../../web4-standard/core-spec/t3-v3-tensors.md)

### V3 (Value Tensor)

**Definition**: A 3-dimensional tensor measuring value contribution:
- **Valuation**: How is value assessed?
- **Veracity**: How truthful are claims?
- **Validity**: How sound is the reasoning?

Each dimension is a **root node in an open-ended RDF sub-graph**, following the same fractal pattern as T3. Sub-dimensions are linked via `web4:subDimensionOf`.

**Relationship to T3**: Complementary, not combined. T3 measures trust, V3 measures value. Together they form a 6-dimensional reputation space at the root level, with unbounded fractal depth.

**Ontology**: [`web4-standard/ontology/t3v3-ontology.ttl`](../../web4-standard/ontology/t3v3-ontology.ttl)

**Specification**: [`web4-standard/core-spec/t3-v3-tensors.md`](../../web4-standard/core-spec/t3-v3-tensors.md)

---

## Context and Boundaries

### MRH (Markov Relevancy Horizon)

**Definition**: The boundary of what an entity can know or affect given its position, history, and context. Determines scope of relevance for decisions. Implemented as an **open-ended RDF graph** of typed associations, fractally composable across scales.

**NOT**: Minimum Response Horizon, Memory Retention Heuristic, or similar.

**Specification**: [`web4-standard/core-spec/mrh-tensors.md`](../../web4-standard/core-spec/mrh-tensors.md)

---

## Resource Economics

### ATP (Allocation Transfer Packet)

**Definition**: Energy-based resource allocation unit. Consumed when performing actions, regenerated through contribution. Creates economic incentives.

**NOT**: Attention Token Pool, Adaptive Trust Points, Alignment Transfer Protocol, or similar.

**Specification**: [`web4-standard/core-spec/atp-adp-cycle.md`](../../web4-standard/core-spec/atp-adp-cycle.md)

### ADP (Allocation Discharge Packet)

**Definition**: The "spent" form of ATP after work is done. Can be recycled back to ATP through validation.

**NOT**: Adaptive Development Points, Allocation Decay Packet, or similar.

**Specification**: [`web4-standard/core-spec/atp-adp-cycle.md`](../../web4-standard/core-spec/atp-adp-cycle.md)

---

## Action Framework

### R6 (Six-Element Action Framework)

**Definition**: The canonical lifecycle for actions:
1. **Rules**: Governance constraints
2. **Role**: Actor identity and permissions
3. **Request**: What is being asked
4. **Reference**: Context and precedent
5. **Resource**: What is consumed/produced
6. **Result**: Outcome and attestation

**NOT**: R7, R5, or any other count. R6 is canonical.

**Specification**: [`web4-standard/core-spec/r6-framework.md`](../../web4-standard/core-spec/r6-framework.md)

---

## Organizational Structures

### Society

**Definition**: A self-governing group of entities with treasury, membership rules, policies, and roles. Societies can contain other societies (fractal structure).

**Specification**: [`web4-standard/core-spec/SOCIETY_SPECIFICATION.md`](../../web4-standard/core-spec/SOCIETY_SPECIFICATION.md)

### Federation

**Definition**: Coordination between multiple societies through signed gossip, consensus, and cross-society witnessing.

---

## Security Mechanisms

### Witnessing

**Definition**: Observing and attesting to an entity's actions. Witnesses stake reputation on attestations.

### Binding

**Definition**: Permanent attachment of identity to hardware or cryptographic proof. Irreversible.

### Pairing

**Definition**: Authorized operational relationship between entities. Revocable.

### Delegation

**Definition**: Granting limited authority with constraints (budget, time, scope). Instantly revocable.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-12 | Initial canonical terms based on Nova review feedback |

---

## Enforcement

All documentation in this repository MUST use these definitions. When updating docs:

1. Check this file first for canonical meaning
2. Do not create new expansions for established acronyms
3. Report conflicts to maintainers
4. Update this file when new terms are added

**Migration**: Documents using non-canonical terms should be updated to match this specification.
