# Web4 Grounding Implementation Roadmap (Legion)

**Date**: 2025-12-27
**Machine**: Legion Pro 7
**Proposal**: [MRH_GROUNDING_PROPOSAL.md](../proposals/MRH_GROUNDING_PROPOSAL.md)
**Integration Notes**: [GROUNDING_INTEGRATION_NOTES.md](./GROUNDING_INTEGRATION_NOTES.md)

---

## Executive Summary

The MRH Grounding proposal introduces **Grounding** as a fifth MRH relationship type that captures ephemeral operational presence. This document maps what needs to be implemented in Web4 core on Legion specifically.

**Web4-Specific Work**: Phases 1-4 (8-10 weeks)
**HRM/SAGE Integration**: Phases 5-6 (cross-project, Thor/Sprout involvement)

---

## 1. What Grounding Is

### The Missing Primitive

Web4 currently has:
- **LCT**: Identity (who you ARE) - Permanent
- **T3/V3**: Trust (what you're TRUSTED to do) - Long-lived
- **ATP**: Resources (what you can SPEND) - Transaction-scoped
- **AGY/ACP**: Authorization (what you're ALLOWED to do) - Policy-defined

**Missing**: Ephemeral operational context—where an entity currently IS and what it CAN do right now.

### What Grounding Adds

```python
grounding_edge {
  source: LCT                    # Entity being grounded
  target: GroundingContext       # Current operational context
  timestamp: ISO8601
  ttl: Duration                  # Minutes to hours
  signature: Signature
  witness_set: [LCT]
}

GroundingContext {
  location: {...}           # Spatial grounding (physical/network/logical)
  capabilities: {...}       # Capability grounding (hardware, resources)
  session: {...}            # Temporal grounding (activity patterns)
  active_contexts: [LCT]    # Relational grounding (current interactions)
}
```

### Coherence Index (CI)

Grounding enables coherence calculation—how plausible is the current grounding given history?

```python
CI = f(spatial_coherence, capability_coherence, temporal_coherence, relational_coherence)
```

**CI modulates trust application** (not trust itself):
- High CI (0.9+): Full T3 access, normal ATP costs
- Low CI (<0.5): Reduced effective trust, increased ATP costs, more witnesses required

---

## 2. Web4 Core Implementation (Legion Scope)

### Phase 1: Core Infrastructure (Week 1-2)

**Files to Modify**:
- `web4-standard/mrh_rdf_implementation.py` - Add grounding edge type
- `web4-standard/core-spec/mrh-framework.md` - Update specification
- `game/engine/mrh_profiles.py` - Add grounding support

**Tasks**:
- [ ] Add `grounding` to MRHRelation enum (alongside binding, pairing, witnessing, broadcast)
- [ ] Implement `GroundingContext` dataclass with four components
- [ ] Add grounding edges to RDF store with proper namespaces
- [ ] Create SPARQL queries for grounding retrieval
- [ ] Update MRH graph traversal to handle grounding edges

**RDF Representation**:
```turtle
@prefix ground: <https://web4.io/mrh/grounding#> .

<lct:entity-123> mrh:grounding [
    a ground:GroundingEdge ;
    ground:timestamp "2025-12-27T14:30:00Z"^^xsd:dateTime ;
    ground:ttl "PT1H"^^xsd:duration ;
    ground:location [
        ground:type "physical" ;
        ground:value "geo:45.5231,-122.6765" ;
        ground:precision "city" ;
    ] ;
    ground:capabilities [
        ground:advertised ( "canvas" "voice" "compute" ) ;
        ground:hardwareClass "edge-device" ;
    ] ;
    ground:continuityToken "prev-grounding-hash" ;
    ground:signature "sig:..." ;
] .
```

### Phase 2: Coherence Calculation (Week 2-3)

**New Files**:
- `web4-standard/implementation/reference/coherence.py` - Core coherence functions
- `web4-standard/implementation/reference/grounding.py` - Grounding lifecycle

**Tasks**:
- [ ] Implement `spatial_coherence()` - Impossible travel detection
- [ ] Implement `capability_coherence()` - Capability spoofing prevention
- [ ] Implement `temporal_coherence()` - Activity pattern analysis
- [ ] Implement `relational_coherence()` - MRH neighborhood consistency
- [ ] Implement `coherence_index()` - Weighted geometric mean combiner
- [ ] Add society-configurable weights (CoherenceWeights dataclass)
- [ ] Implement grounding history storage and windowing

**Key Algorithms**:

```python
# Spatial coherence - detect impossible travel
def spatial_coherence(current: Location, history: [GroundingEdge], window: Duration) -> float:
    last = history[-1]
    distance = geo_distance(current, last.location)
    elapsed = current.timestamp - last.timestamp
    max_velocity = entity_max_velocity(current.hardware_class)

    if distance / elapsed > max_velocity:
        # Impossible travel - check mitigations
        base = 0.1
        if has_travel_announcement(history, current.location):
            base += 0.4
        if has_destination_witness(current):
            base += 0.3
        return base

    return 1.0 - (distance / (max_velocity * elapsed))

# Combined coherence - multiplicative, not additive
def coherence_index(current, history, mrh, weights) -> float:
    spatial = spatial_coherence(current.location, history, weights.spatial_window)
    capability = capability_coherence(current.capabilities, history)
    temporal = temporal_coherence(current.session, history)
    relational = relational_coherence(current.active_contexts, history, mrh)

    # Weighted geometric mean (one low score tanks the whole CI)
    ci = (
        spatial ** weights.spatial *
        capability ** weights.capability *
        temporal ** weights.temporal *
        relational ** weights.relational
    ) ** (1 / sum(weights))

    return ci
```

### Phase 3: Trust Integration (Week 3-4)

**Files to Modify**:
- `web4-standard/implementation/reference/trust_tensors.py` - CI modulation
- `game/engine/mrh_aware_trust.py` - Game engine integration
- `web4-standard/core-spec/trust-tensors.md` - Update specification

**Tasks**:
- [ ] Implement `effective_trust()` - CI-modulated T3 calculation
- [ ] Implement `adjusted_atp_cost()` - ATP cost modulation (up to 10x for low CI)
- [ ] Implement `required_witnesses()` - Witness count modulation
- [ ] Add coherence checks to transaction validation
- [ ] Integrate CI into game engine trust decisions
- [ ] Add CI to LCT presentation layer

**Trust Modulation**:
```python
def effective_trust(t3: TrustTensor, ci: float, context: TransactionContext) -> TrustTensor:
    """
    CI acts as a ceiling on effective trust.
    High CI = full T3 available. Low CI = only fraction accessible.
    """
    modulated = t3.clone()
    for dimension in modulated.dimensions:
        modulated[dimension] = t3[dimension] * ci_modulation_curve(ci, dimension)
    return modulated

def adjusted_atp_cost(base_cost: ATP, ci: float) -> ATP:
    """Lower coherence = higher ATP cost."""
    if ci >= 0.9:
        return base_cost
    multiplier = 1.0 / (ci ** 2)
    return base_cost * min(multiplier, 10.0)  # Cap at 10x

def required_witnesses(base_requirement: int, ci: float) -> int:
    """Lower coherence = more witnesses needed."""
    if ci >= 0.8:
        return base_requirement
    additional = ceil((0.8 - ci) * 10)  # Up to 8 additional witnesses
    return base_requirement + additional
```

### Phase 4: Lifecycle Management (Week 4-5)

**New Files**:
- `web4-standard/implementation/reference/grounding_lifecycle.py` - Announcement, heartbeat, expiration

**Tasks**:
- [ ] Implement `announce_grounding()` - MRH broadcast protocol
- [ ] Implement `grounding_heartbeat()` - Periodic refresh mechanism
- [ ] Implement `on_grounding_expired()` - Expiration handling
- [ ] Implement `verify_grounding()` - Witness verification flow
- [ ] Add grounding TTL defaults per hardware class
- [ ] Implement continuity token chain validation
- [ ] Add grounding gossip protocol

**Lifecycle Functions**:
```python
def announce_grounding(entity: LCT, context: GroundingContext) -> GroundingEdge:
    edge = GroundingEdge(
        source=entity,
        target=context,
        timestamp=now(),
        ttl=default_grounding_ttl(context.hardware_class),
        signature=entity.sign(context),
        continuity_token=hash(last_grounding(entity))
    )
    mrh.add_edge(edge)
    gossip.broadcast(edge)
    return edge

def grounding_heartbeat(entity: LCT):
    current = sense_current_context()
    if context_changed_significantly(current, last_announced):
        announce_grounding(entity, current)
    else:
        refresh_grounding(entity)  # Extend TTL without full re-announce
```

---

## 3. Ruvector Relevance

**Repository**: `/home/dp/ai-workspace/ruvector/`

Ruvector is a distributed vector database with features highly relevant to Web4:

### Direct Applicability

| Ruvector Feature | Web4 Use Case |
|------------------|---------------|
| **RDF/SPARQL support** | Web4's MRH already uses RDF - ruvector could be a performance backend |
| **Cypher queries** | Alternative query language for MRH graph traversal |
| **Hyperedges** | Complex MRH relationships (beyond binary edges) |
| **Raft consensus** | Distributed MRH synchronization across federation |
| **GNN learning** | Trust propagation and coherence pattern learning |
| **Vector embeddings** | Context similarity for grounding coherence |
| **Multi-master replication** | Federated SAGE instances (Legion ↔ Thor ↔ Sprout) |

### Potential Integration Points

1. **MRH Backend**: Replace or augment `mrh_rdf_implementation.py` with ruvector for:
   - Faster SPARQL queries (61µs p50 latency)
   - Native graph neural network support for trust propagation
   - Distributed consensus for multi-machine MRH

2. **Coherence Calculation**: Use ruvector's GNN layers for:
   - Learning optimal coherence weights per society
   - Pattern recognition in grounding history
   - Anomaly detection for security (impossible travel, capability spoofing)

3. **Federation Coherence**: Use ruvector's Raft consensus for:
   - Distributed grounding across SAGE federation
   - Conflict resolution for multi-master scenarios
   - Consistent snapshots for auditing

4. **Context Embeddings**: Use ruvector's vector search for:
   - Semantic similarity between GroundingContext instances
   - Context clustering for pattern analysis
   - Relational coherence via embedding distance

### Recommended Exploration

**After Phase 2 completion** (coherence functions implemented), evaluate:
- [ ] Ruvector as alternative MRH backend (performance benchmarks)
- [ ] GNN layers for coherence weight learning
- [ ] Raft consensus for federation grounding
- [ ] Context embedding similarity metrics

---

## 4. SAGE/HRM Integration (Not Legion-Specific)

### Phase 5: SAGE Integration (Week 5-6)

**Cross-Project Work** (HRM repository, Thor/Sprout coordination):
- [ ] Extend `GroundingContext` with SAGE-specific fields (hardware attestation, model state, federation state)
- [ ] Implement hardware attestation hooks (TPM/secure enclave integration)
- [ ] Implement federation coherence calculation (`federation_coherence()`)
- [ ] Cross-machine grounding coordination protocol

**Relevant to**:
- Thor Session (multi-machine SAGE)
- Sprout Session (edge device SAGE)
- SAGE unified identity (Session 131 work)

### Phase 6: Testing & Hardening (Week 6-8)

**Test Scenarios**:
- [ ] Unit tests for all four coherence functions
- [ ] Integration tests with game engine
- [ ] Impossible travel attack scenarios
- [ ] Capability spoofing scenarios
- [ ] Federation partition scenarios
- [ ] Performance benchmarking (coherence calculation overhead)

---

## 5. Security Considerations

### Attack Vectors

1. **Grounding Spoofing**: Entity claims false location/capabilities
   - **Mitigation**: Hardware attestation (SAGE), witness requirements, coherence penalties

2. **Coherence Gaming**: Entity maintains artificially high CI through minimal activity
   - **Mitigation**: Activity thresholds, decay for inactive states

3. **History Poisoning**: Entity builds false history for future attack
   - **Mitigation**: Long windows, witness requirements for pattern changes, anomaly detection

### Trust Implications

- Grounding **does not grant trust**, only **gates existing trust**
- CI modulation is **multiplicative** (one low dimension tanks the whole score)
- Low coherence increases **friction** (ATP costs, witness requirements), not hard blocks

---

## 6. Open Questions

1. **Grounding TTL defaults**: What are sensible defaults for edge/server/mobile hardware classes?
   - Edge device (Sprout): 15 minutes?
   - Server (Legion/Thor): 1 hour?
   - Mobile: 5 minutes?

2. **Cross-society coherence**: When an entity operates in multiple societies with different norms, how reconcile?
   - Use minimum CI across societies?
   - Society-specific CI with separate witness requirements?

3. **Privacy tradeoffs**: Grounding exposes location/capability. Zero-knowledge proofs?
   - Range proofs for location (in Portland metro, don't need exact GPS)?
   - Capability class commitment without revealing specifics?

4. **Historical window size**: How far back for coherence calculations?
   - Spatial: 7 days for pattern establishment?
   - Capability: 30 days for upgrade detection?
   - Temporal: 90 days for activity pattern learning?

5. **Ruvector integration timeline**: Before or after Phase 2?
   - Option A: Implement Phase 2 in pure Python, then evaluate ruvector
   - Option B: Prototype with ruvector from start (faster, but dependency risk)

---

## 7. Next Steps (Immediate)

### Decision Point: Implementation Approach

**Option 1: Pure Python (Lower Risk)**
- Implement Phases 1-2 in pure Python using existing `mrh_rdf_implementation.py`
- Evaluate ruvector after coherence functions are working
- Gradual migration if performance justifies

**Option 2: Ruvector-First (Higher Performance)**
- Evaluate ruvector integration in Phase 1
- Use ruvector's RDF/SPARQL backend for MRH from start
- Leverage GNN layers for coherence learning

### Recommended: **Option 1** (Pragmatic)

**Rationale**:
1. Grounding proposal is brand new (Dec 27, 2025) - needs experimentation
2. Pure Python allows rapid iteration without external dependency complexity
3. Ruvector integration is a natural Phase 7 optimization after core works
4. Autonomous sessions can evaluate ruvector in parallel while Legion implements core

### Immediate Actions

1. **Read existing MRH implementation** (`mrh_rdf_implementation.py`) fully
2. **Create Phase 1 implementation plan** (grounding edge type, RDF schema)
3. **Set up test infrastructure** (grounding edge creation, SPARQL queries)
4. **Document design decisions** (TTL defaults, weight initialization)
5. **Coordinate with autonomous sessions** (Thor/Sprout SAGE integration timeline)

---

## 8. Timeline Summary

| Phase | Duration | Web4 Work | HRM/SAGE Work | Ruvector |
|-------|----------|-----------|---------------|----------|
| **1: Core Infrastructure** | 2 weeks | ✅ Legion | - | Evaluation |
| **2: Coherence Calculation** | 1 week | ✅ Legion | - | Evaluation |
| **3: Trust Integration** | 1 week | ✅ Legion | - | - |
| **4: Lifecycle Management** | 1 week | ✅ Legion | - | - |
| **5: SAGE Integration** | 1 week | Coordination | ✅ Thor/Sprout | - |
| **6: Testing** | 2 weeks | ✅ Legion | ✅ All machines | Benchmarks |
| **7: Ruvector Migration** | 2 weeks | ✅ Legion | - | ✅ Integration |

**Total**: 10 weeks for full implementation, 5 weeks for Web4 core (Phases 1-4)

---

## References

- **Proposal**: [MRH_GROUNDING_PROPOSAL.md](../proposals/MRH_GROUNDING_PROPOSAL.md)
- **Integration Notes**: [GROUNDING_INTEGRATION_NOTES.md](./GROUNDING_INTEGRATION_NOTES.md)
- **HRM Brief**: `/home/dp/ai-workspace/HRM/sage/docs/AUTO_SESSION_BRIEF_MRH_GROUNDING.md`
- **Ruvector**: `/home/dp/ai-workspace/ruvector/`
- **Web4 MRH Spec**: `web4-standard/core-spec/mrh-framework.md`
- **T3/V3 Trust Tensors**: `web4-standard/core-spec/trust-tensors.md`

---

*This roadmap is a living document. Implementation discoveries should flow back to update both this roadmap and the core proposal.*
