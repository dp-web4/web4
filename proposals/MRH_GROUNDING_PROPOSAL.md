# MRH Grounding: Presence Coherence Layer

**Proposal Version:** 1.0  
**Date:** December 27, 2025  
**Status:** Draft for Implementation  
**Applies to:** Web4, HRM/SAGE  

---

## Executive Summary

This proposal introduces **Grounding** as a fifth MRH relationship type that captures ephemeral operational presence. Grounding edges enable coherence-based trust modulation by tracking where entities ARE and what they CAN do in their current context, distinct from what they're authorized or trusted to do.

Presence coherence acts as a real-time multiplier on trust application—not replacing T3/V3 tensors but gating how they're applied at transaction time.

---

## 1. Problem Statement

Web4 currently has strong primitives for:

| Primitive | What It Captures | Persistence |
|-----------|------------------|-------------|
| LCT | Identity (who you ARE) | Permanent |
| T3/V3 | Trust (what you're TRUSTED to do) | Long-lived, slow decay |
| ATP | Resources (what you can SPEND) | Transaction-scoped |
| AGY/ACP | Authorization (what you're ALLOWED to do) | Policy-defined |

**Missing:** Ephemeral operational context—where an entity currently IS and what it CAN do right now.

This gap creates vulnerabilities:

1. **Impossible travel attacks** - Entity with valid LCT and high T3 appears in implausible locations
2. **Capability spoofing** - Node advertises capabilities inconsistent with its hardware history
3. **Context discontinuity** - No mechanism to detect sudden behavioral/contextual shifts
4. **Routing ambiguity** - Unclear how to reach an entity across multiple surfaces

---

## 2. Grounding: The Fifth MRH Relationship Type

### 2.1 Existing MRH Relationship Types

| Type | Semantics | TTL | Example |
|------|-----------|-----|---------|
| **Binding** | Permanent identity anchoring | Indefinite | LCT ↔ Hardware root |
| **Pairing** | Operational authorization | Session/revocable | Agent ↔ Delegator |
| **Witnessing** | Trust-building observation | Long (months) | Transaction ↔ Witness set |
| **Broadcast** | Public announcement | Variable | Entity → Network |

### 2.2 New: Grounding

| Property | Value |
|----------|-------|
| **Semantics** | Current operational context and capability state |
| **TTL** | Short (minutes to hours) |
| **Update Frequency** | High (heartbeat-driven) |
| **Persistence** | Ephemeral with windowed history |
| **Primary Use** | Coherence calculation at transaction time |

---

## 3. Grounding Edge Specification

### 3.1 Edge Structure

```
grounding_edge {
  source: LCT                    # Entity being grounded
  target: GroundingContext       # Current operational context
  timestamp: ISO8601             # When this grounding was announced
  ttl: Duration                  # How long this grounding remains valid
  signature: Signature           # Signed by source LCT
  witness_set: [LCT]             # Optional witnesses to this grounding
}
```

### 3.2 GroundingContext Object

```
GroundingContext {
  # Spatial grounding
  location: {
    type: "physical" | "network" | "logical"
    value: LocationValue         # GPS, IP range, society ID, etc.
    precision: PrecisionLevel    # How specific the claim is
    verifiable: boolean          # Can this be independently verified?
  }
  
  # Capability grounding
  capabilities: {
    advertised: [CapabilityID]   # What the entity claims it can do now
    hardware_class: HardwareClass # Device category (edge, server, mobile)
    resource_state: {
      compute: ResourceLevel
      memory: ResourceLevel
      network: ResourceLevel
      sensors: [SensorType]
    }
  }
  
  # Temporal grounding
  session: {
    started: ISO8601
    activity_pattern: PatternHash # Hash of recent activity timing
    continuity_token: Token       # Links to previous grounding
  }
  
  # Relational grounding
  active_contexts: [LCT]         # Societies/entities currently engaged with
  surface: SurfaceID             # Current interaction surface (if applicable)
}
```

### 3.3 RDF Representation

```turtle
@prefix mrh: <https://web4.io/mrh#> .
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

---

## 4. Coherence Calculation

### 4.1 Coherence Index (CI)

The Coherence Index is a derived property computed from grounding edge history, not stored directly. It represents how plausible the current grounding is given historical patterns.

```
CI = f(spatial_coherence, capability_coherence, temporal_coherence, relational_coherence)
```

Where each component ∈ [0.0, 1.0] and the combination function is configurable per-society.

### 4.2 Spatial Coherence

```python
def spatial_coherence(current: Location, history: [GroundingEdge], window: Duration) -> float:
    """
    Measures whether current location is plausible given movement history.
    
    Factors:
    - Distance from last known location
    - Time elapsed since last grounding
    - Maximum plausible velocity for entity type
    - Pre-announced travel (reduces penalty)
    - Witness corroboration at new location
    """
    recent = filter_by_window(history, window)
    if not recent:
        return 0.5  # No history, neutral coherence
    
    last = recent[-1]
    distance = geo_distance(current, last.location)
    elapsed = current.timestamp - last.timestamp
    max_velocity = entity_max_velocity(current.hardware_class)
    
    if distance / elapsed > max_velocity:
        # Impossible travel detected
        base_coherence = 0.1
        # Check for travel announcement
        if has_travel_announcement(history, current.location):
            base_coherence += 0.4
        # Check for witness at destination
        if has_destination_witness(current):
            base_coherence += 0.3
        return base_coherence
    
    return 1.0 - (distance / (max_velocity * elapsed))  # Gradual reduction
```

### 4.3 Capability Coherence

```python
def capability_coherence(current: Capabilities, history: [GroundingEdge]) -> float:
    """
    Measures whether advertised capabilities are plausible.
    
    Factors:
    - Consistency with hardware class
    - Gradual vs sudden capability changes
    - Known upgrade/downgrade events
    """
    expected = capabilities_for_hardware_class(current.hardware_class)
    advertised = set(current.advertised)
    
    # Capabilities beyond hardware class are suspicious
    unexpected = advertised - expected
    if unexpected:
        penalty = len(unexpected) * 0.15
        return max(0.0, 1.0 - penalty)
    
    # Sudden new capabilities without upgrade event
    if history:
        last_caps = set(history[-1].capabilities.advertised)
        new_caps = advertised - last_caps
        if new_caps and not has_upgrade_event(history, new_caps):
            return 0.7  # Mild suspicion
    
    return 1.0
```

### 4.4 Temporal Coherence

```python
def temporal_coherence(current: Session, history: [GroundingEdge]) -> float:
    """
    Measures whether activity timing is consistent with patterns.
    
    Factors:
    - Time of day vs historical active hours
    - Day of week patterns
    - Session continuity (gaps in continuity_token chain)
    """
    if not history:
        return 0.5
    
    pattern = extract_activity_pattern(history)
    current_time = current.timestamp
    
    # How unusual is this time for this entity?
    unusualness = pattern.score_time(current_time)  # 0 = typical, 1 = very unusual
    
    # Check continuity chain
    if current.continuity_token:
        if not validates_continuity(current.continuity_token, history):
            return 0.3  # Broken chain is suspicious
    
    return 1.0 - (unusualness * 0.5)  # Unusual timing reduces but doesn't eliminate
```

### 4.5 Relational Coherence

```python
def relational_coherence(current: [LCT], history: [GroundingEdge], mrh: Graph) -> float:
    """
    Measures whether current interactions fit relationship patterns.
    
    Factors:
    - Are active contexts within usual MRH neighborhood?
    - Sudden engagement with distant graph regions
    - Society membership vs interaction targets
    """
    usual_neighborhood = mrh.neighborhood(entity, depth=2)
    current_contexts = set(current.active_contexts)
    
    familiar = current_contexts & usual_neighborhood
    novel = current_contexts - usual_neighborhood
    
    if not current_contexts:
        return 1.0  # No active contexts, nothing to check
    
    familiarity_ratio = len(familiar) / len(current_contexts)
    
    # Novel contexts aren't bad, but reduce coherence slightly
    return 0.5 + (familiarity_ratio * 0.5)
```

### 4.6 Combined Coherence Index

```python
def coherence_index(
    current: GroundingContext,
    history: [GroundingEdge],
    mrh: Graph,
    weights: CoherenceWeights  # Society-configurable
) -> float:
    """
    Compute overall coherence index.
    Default weights emphasize spatial and capability coherence.
    """
    spatial = spatial_coherence(current.location, history, weights.spatial_window)
    capability = capability_coherence(current.capabilities, history)
    temporal = temporal_coherence(current.session, history)
    relational = relational_coherence(current.active_contexts, history, mrh)
    
    # Weighted geometric mean (multiplicative, not additive)
    ci = (
        spatial ** weights.spatial *
        capability ** weights.capability *
        temporal ** weights.temporal *
        relational ** weights.relational
    ) ** (1 / sum(weights))
    
    return ci
```

---

## 5. Trust Modulation

### 5.1 Relationship Between CI and T3

Coherence Index modulates how T3 is applied, not T3 itself.

```python
def effective_trust(t3: TrustTensor, ci: float, context: TransactionContext) -> TrustTensor:
    """
    T3 represents earned trust.
    CI gates how much of that trust is currently accessible.
    """
    # CI acts as a ceiling on effective trust
    # High CI = full T3 available
    # Low CI = only fraction of T3 accessible
    
    modulated = t3.clone()
    for dimension in modulated.dimensions:
        modulated[dimension] = t3[dimension] * ci_modulation_curve(ci, dimension)
    
    return modulated

def ci_modulation_curve(ci: float, dimension: TrustDimension) -> float:
    """
    Different trust dimensions may respond differently to coherence.
    Financial trust might be more sensitive than read-access trust.
    """
    sensitivity = dimension.coherence_sensitivity  # 0.0 to 1.0
    
    # At CI=1.0, full trust. At CI=0.0, trust reduced by sensitivity factor.
    return 1.0 - (sensitivity * (1.0 - ci))
```

### 5.2 ATP Cost Modulation

Low coherence increases ATP costs for transactions:

```python
def adjusted_atp_cost(base_cost: ATP, ci: float) -> ATP:
    """
    Lower coherence = higher ATP cost.
    This creates natural friction for suspicious contexts.
    """
    if ci >= 0.9:
        return base_cost  # No penalty
    
    # Exponential increase as coherence drops
    multiplier = 1.0 / (ci ** 2)
    return base_cost * min(multiplier, 10.0)  # Cap at 10x
```

### 5.3 Witness Requirements

Low coherence triggers additional witness requirements:

```python
def required_witnesses(base_requirement: int, ci: float) -> int:
    """
    Lower coherence = more witnesses needed.
    """
    if ci >= 0.8:
        return base_requirement
    
    additional = ceil((0.8 - ci) * 10)  # Up to 8 additional witnesses
    return base_requirement + additional
```

### 5.4 Consequence Index (CX) Gating

Beyond modulating trust and costs, CI should gate *which actions are permitted*. We introduce **Consequence Index (CX)** as a complement to CI:

| Index | Measures | Range |
|-------|----------|-------|
| **CI** | How present/coherent the entity is | 0.0 - 1.0 |
| **CX** | How consequential the action is | 0.0 - 1.0 |

**Gating Rule**: An entity should not perform high-consequence actions when not fully coherent.

```python
def ci_threshold_for_cx(cx: float) -> float:
    """Higher consequence → higher coherence required."""
    return 0.3 + (cx * 0.6)  # Range: 0.3 (trivial) to 0.9 (critical)

def can_execute_action(entity: LCT, action: Action, ci: float) -> bool:
    """Gate actions by coherence × consequence."""
    required_ci = ci_threshold_for_cx(action.cx)
    if ci < required_ci:
        return False  # Not just expensive - BLOCKED
    return True
```

**CX Classification Examples:**

| CX Level | Example Actions | Required CI |
|----------|-----------------|-------------|
| 0.0 - 0.2 | Read-only queries, logging | 0.3+ |
| 0.2 - 0.5 | State modifications, API calls | 0.5+ |
| 0.5 - 0.7 | Financial transactions, deployments | 0.6+ |
| 0.7 - 0.9 | Irreversible actions, deletions | 0.75+ |
| 0.9 - 1.0 | Critical infrastructure, safety-relevant | 0.9+ |

**Human Parallel**: "Don't operate machinery while impaired."

**Natural Escalation Paths** when CI < required threshold:
1. **Delegate**: Find higher-CI entity to perform action
2. **Wait**: Let coherence improve (grounding refreshes)
3. **Reduce scope**: Break high-CX action into lower-CX steps
4. **Co-sign**: Multiple entities jointly meet threshold

### 5.5 R6 Integration

CX integrates with the R6 action framework:

```python
class R6Request:
    intent: str
    cx: float  # Consequence level
    urgency: float
    estimated_cost: ATP

class R6Role:
    capabilities: Set[Capability]
    cx_ceiling: float  # Max consequence this role permits

class R6Result:
    outcome: Any
    ci_at_execution: float  # For audit trail
    cx_actual: float  # Realized consequence (for learning)
```

Recording `ci_at_execution` enables post-hoc accountability and dispute resolution.

---

## 6. Grounding Lifecycle

### 6.1 Announcement

Entities announce grounding via MRH broadcast:

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
```

### 6.2 Heartbeat

Grounding edges require periodic refresh:

```python
def grounding_heartbeat(entity: LCT):
    """
    Called periodically to maintain grounding freshness.
    Frequency depends on hardware class and current coherence.
    """
    current = sense_current_context()  # Hardware-specific
    
    if context_changed_significantly(current, last_announced):
        announce_grounding(entity, current)
    else:
        refresh_grounding(entity)  # Extend TTL without full re-announce
```

### 6.3 Expiration

Expired grounding edges affect coherence:

```python
def on_grounding_expired(entity: LCT, edge: GroundingEdge):
    """
    When grounding expires without refresh, coherence degrades.
    """
    # Don't delete immediately - keep for history
    edge.status = "expired"
    
    # Entity's effective CI drops until new grounding announced
    # This creates pressure to maintain active grounding
```

### 6.4 Verification

Optional verification by witnesses:

```python
def verify_grounding(witness: LCT, edge: GroundingEdge) -> WitnessAttestation:
    """
    Witnesses can attest to grounding claims they can verify.
    E.g., a society node can confirm an entity is active in that society.
    """
    if can_verify(witness, edge):
        attestation = WitnessAttestation(
            witness=witness,
            edge=edge,
            timestamp=now(),
            verification_method=how_verified(witness, edge)
        )
        edge.witness_set.append(witness)
        return attestation
    return None
```

---

## 7. SAGE/HRM Integration

### 7.1 Edge Device Grounding

SAGE instances on edge devices (Sprout, etc.) have specific grounding patterns:

```python
class SAGEGroundingContext(GroundingContext):
    """
    Extended grounding for SAGE edge instances.
    """
    hardware_attestation: HardwareAttestation  # TPM/secure enclave proof
    model_state: {
        active_model: ModelID
        quantization: QuantizationLevel
        memory_pressure: float
    }
    federation_state: {
        connected_peers: [LCT]
        consensus_role: "leader" | "follower" | "observer"
        last_sync: ISO8601
    }
```

### 7.2 Cross-Machine Coherence

For distributed SAGE instances (Legion ↔ Thor ↔ Sprout):

```python
def federation_coherence(instances: [LCT], mrh: Graph) -> float:
    """
    Coherence across federated SAGE instances.
    Are they behaving as a coherent federation or fragmenting?
    """
    groundings = [mrh.current_grounding(i) for i in instances]
    
    # Check sync timestamps are aligned
    sync_spread = max(g.federation_state.last_sync for g in groundings) - \
                  min(g.federation_state.last_sync for g in groundings)
    
    if sync_spread > acceptable_sync_drift:
        return 0.7  # Federation may be partitioned
    
    # Check consensus role distribution
    leaders = [g for g in groundings if g.federation_state.consensus_role == "leader"]
    if len(leaders) != 1:
        return 0.5  # Multiple leaders or no leader is concerning
    
    return 1.0
```

### 7.3 Cognition Kernel Considerations

For SAGE cognition/coherence work:

- Grounding provides the "where am I" component of self-model
- Coherence history contributes to identity continuity
- Federated grounding enables distributed self-awareness

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)

- [ ] Add `grounding` edge type to MRH schema
- [ ] Implement `GroundingContext` data structure
- [ ] Add grounding edges to RDF store
- [ ] Basic SPARQL queries for grounding retrieval

### Phase 2: Coherence Calculation (Week 2-3)

- [ ] Implement spatial coherence function
- [ ] Implement capability coherence function
- [ ] Implement temporal coherence function
- [ ] Implement relational coherence function
- [ ] Implement combined CI calculation
- [ ] Add society-configurable weights

### Phase 3: Trust Integration (Week 3-4)

- [ ] Integrate CI into effective trust calculation
- [ ] Implement ATP cost modulation
- [ ] Implement witness requirement modulation
- [ ] Add coherence checks to transaction validation

### Phase 4: Lifecycle Management (Week 4-5)

- [ ] Implement grounding announcement protocol
- [ ] Implement heartbeat mechanism
- [ ] Implement expiration handling
- [ ] Add witness verification flow

### Phase 5: SAGE Integration (Week 5-6)

- [ ] Extend GroundingContext for SAGE
- [ ] Implement hardware attestation hooks
- [ ] Implement federation coherence
- [ ] Cross-machine grounding coordination

### Phase 6: Testing & Hardening (Week 6-8)

- [ ] Unit tests for all coherence functions
- [ ] Integration tests with game engine
- [ ] Impossible travel attack scenarios
- [ ] Capability spoofing scenarios
- [ ] Federation partition scenarios
- [ ] Performance benchmarking

---

## 9. Security Considerations

### 9.1 Grounding Spoofing

**Threat:** Entity announces false grounding (claims to be somewhere it isn't).

**Mitigations:**
- Hardware attestation where available (SAGE edge devices)
- Witness verification requirements for high-stakes contexts
- Coherence penalties for unverifiable claims
- Network-level verification (IP geolocation as soft signal)

### 9.2 Coherence Gaming

**Threat:** Entity maintains artificially high coherence through minimal activity.

**Mitigations:**
- Coherence doesn't grant trust, only gates existing trust
- Activity thresholds for coherence credit
- Decay for inactive-but-grounded states

### 9.3 History Poisoning

**Threat:** Entity builds false history to establish cover for future attack.

**Mitigations:**
- Long windows for pattern establishment
- Witness requirements for pattern changes
- Anomaly detection on pattern shifts

---

## 10. Open Questions

1. **Grounding TTL defaults:** What are sensible defaults for different hardware classes?

2. **Cross-society coherence:** When an entity operates in multiple societies with different coherence norms, how do we reconcile?

3. **Privacy tradeoffs:** Grounding inherently exposes location/capability. How much can be disclosed via zero-knowledge proofs?

4. **Historical window size:** How far back should coherence calculations look? Too short = easy to game. Too long = legitimate changes penalized.

5. **Federation grounding authority:** In SAGE federation, which instance is authoritative for federation-level grounding?

---

## 11. References

- Web4 MRH Specification: `web4-standard/core-spec/mrh-framework.md`
- T3/V3 Trust Tensor Spec: `web4-standard/core-spec/trust-tensors.md`
- SAGE Federation Design: `MULTI_MACHINE_SAGE_FEDERATION_DESIGN.md`
- Game Engine MRH Implementation: `game/engine/mrh.py`

---

## Appendix A: Example Scenarios

### A.1 Normal Operation

```
Entity: sage-sprout-001
Grounding History: Portland, OR for 6 months, consistent capability set
Current Grounding: Portland, OR, same capabilities
Coherence Index: 0.98
Effect: Full T3 access, normal ATP costs
```

### A.2 Announced Travel

```
Entity: user-alice
Grounding History: Portland, OR for 2 years
Travel Announcement: "Traveling to Berlin Dec 20-30" (witnessed)
Current Grounding: Berlin, DE
Coherence Index: 0.85 (reduced but not suspicious)
Effect: Slightly elevated ATP costs, normal witness requirements
```

### A.3 Suspicious Context Shift

```
Entity: agent-bob
Grounding History: Portland, OR, basic compute capabilities
Current Grounding: Singapore, claims GPU cluster access
Coherence Index: 0.25
Effect: Effective trust capped at 25% of T3, 4x ATP cost, +3 witnesses required
```

### A.4 Federation Partition

```
Federation: sage-legion, sage-thor, sage-sprout
Normal State: All synchronized, single leader (legion)
Current State: Thor claims leader, Sprout shows 2-hour sync drift
Federation Coherence: 0.5
Effect: Federation-level operations require manual intervention
```

---

*This document is a living proposal. Implementation discoveries should flow back to update the specification.*
