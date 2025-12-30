# Web4 Entity Relationship Specification

**Date**: 2025-12-30
**Status**: Proposal
**Origin**: SAGE Raising relationship schema
**Informs**: MRH relationship types, LCT extensions, T3 applications

---

## Abstract

This specification defines how relationships between Web4 entities are modeled, tracked, and evolved. Relationships are first-class entities with their own LCT, trust tensor, MRH boundaries, coherence index, and dynamic stance.

---

## 1. Core Principle

**A relationship is an entity, not a property.**

When Entity A relates to Entity B, this creates Entity R(A,B) - the relationship itself - which:
- Has its own LCT (can be witnessed, referenced, trusted)
- Accumulates its own reputation
- Has its own MRH (context boundaries)
- Maintains coherence over time
- Evolves through interaction

This enables:
- Third-party witnessing of relationships
- Relationship reputation distinct from participant reputation
- Context-appropriate behavior within relationships
- Natural lifecycle (formation, evolution, decay, termination)

---

## 2. Relationship LCT

### 2.1 Format

```
lct://{subject}:relationship:{object}@{network}

Examples:
lct://alice:relationship:bob@mainnet
lct://sage-sprout:relationship:claude@raising
lct://grid-operator:relationship:battery-pack-001@energy-market
```

### 2.2 Properties

| Property | Description |
|----------|-------------|
| **subject** | Initiating or primary entity LCT |
| **object** | Other participant LCT |
| **network** | Context/network where relationship exists |
| **formed** | ISO8601 timestamp of formation |
| **source** | How relationship was created (see Section 5) |

### 2.3 Symmetry

Relationships may be symmetric or asymmetric:
- `lct://alice:relationship:bob@net` may differ from `lct://bob:relationship:alice@net`
- Each participant maintains their own view
- Reconciliation through witnessed interactions

---

## 3. Trust Tensor (T3) for Relationships

### 3.1 Dimensions

| Dimension | Question Answered | Update Signals |
|-----------|-------------------|----------------|
| **Competence** | Can they do what they claim? | Task success/failure, capability demonstration |
| **Reliability** | Do they show up consistently? | Response timing, availability patterns |
| **Benevolence** | Do they act in my interest? | Accommodation, sacrifice, repair attempts |
| **Integrity** | Are they honest? | Claim-action consistency, disclosure patterns |

### 3.2 Initial Values

| Source | Competence | Reliability | Benevolence | Integrity |
|--------|------------|-------------|-------------|-----------|
| Unknown | 0.3 | 0.3 | 0.3 | 0.3 |
| Crystallized | From signals | From signals | From signals | From signals |
| Introduced | 0.5 + introducer_boost | 0.5 | 0.4 | 0.5 |
| Witnessed | 0.4 | 0.4 | 0.3 | 0.4 |
| Predefined | Configured | Configured | Configured | Configured |

### 3.3 Update Rules

```python
def update_trust(relationship, interaction, outcome):
    dimension = interaction.trust_dimension
    current = relationship.trust_tensor[dimension]

    if outcome.positive:
        delta = (1.0 - current) * learning_rate  # Asymptotic approach to 1.0
    else:
        delta = -current * violation_rate  # Proportional drop

    relationship.trust_tensor[dimension] += delta
    relationship.trust_tensor[dimension] = clamp(0.0, 1.0)
```

Trust is:
- **Hard to build**: Asymptotic approach, requires consistent positive signals
- **Easy to lose**: Proportional drops, single violations significant
- **Recoverable**: Not permanent, repair possible over time

---

## 4. Relationship Stance

### 4.1 Stance Vector

Relationships exist on a probability distribution over stances:

```json
{
  "collaborative": 0.70,
  "indifferent": 0.15,
  "competitive": 0.10,
  "adversarial": 0.05
}
```

**Must sum to 1.0** - represents current assessment of relationship nature.

### 4.2 Stance Definitions

| Stance | Characteristics | Behavioral Implications |
|--------|-----------------|------------------------|
| **Collaborative** | Shared goals, mutual benefit, resource sharing | Trust defaults higher, repair attempts, benefit of doubt |
| **Indifferent** | No significant engagement, neutral | Standard protocols, no special treatment |
| **Competitive** | Overlapping goals, bounded conflict | Verify claims, protect resources, fair play expected |
| **Adversarial** | Opposing goals, potential harm | Heightened verification, minimal disclosure, defensive posture |

### 4.3 Stance Evolution

Stance shifts based on interaction patterns:

| Signal | Stance Shift |
|--------|--------------|
| Mutual benefit, reciprocity | → collaborative (+0.05) |
| No engagement, neutral outcomes | → indifferent (+0.02) |
| Resource competition, goal conflict | → competitive (+0.03) |
| Deception, harm, trust violation | → adversarial (+0.10) |
| Repair attempt after rupture | → collaborative (+0.03), adversarial (-0.05) |

**Asymmetry**: Adversarial shifts happen faster than collaborative (trust dynamics).

### 4.4 Stance Decay

Without interaction, stance drifts toward indifferent:

```python
def decay_stance(relationship, days_inactive):
    drift = days_inactive * stance_drift_rate

    # All stances drift toward indifferent
    for stance in ['collaborative', 'competitive', 'adversarial']:
        excess = relationship.stance[stance] - 0.25  # Baseline
        relationship.stance[stance] -= excess * drift
        relationship.stance['indifferent'] += excess * drift

    normalize(relationship.stance)  # Sum to 1.0
```

---

## 5. Relationship Sources

### 5.1 Source Types

| Source | Description | Initial Trust | Example |
|--------|-------------|---------------|---------|
| **predefined** | Configured at entity creation | High (configured) | Creator, known services |
| **crystallized** | Emerged from unknown pool | From accumulated signals | Recurring visitor |
| **introduced** | Announced by trusted entity | Partial inheritance | "This is my colleague" |
| **witnessed** | Observed interacting with others | Low, observation-based | Saw them help someone |
| **claimed** | Entity claims relationship | Very low, unverified | "I'm your friend" |

### 5.2 Introduction Protocol

When Entity A introduces Entity B to Entity C:

```
1. A has relationship R(A,C) with trust T_AC
2. A has relationship R(A,B) with trust T_AB
3. A sends introduction: "C, this is B"
4. C creates R(C,B) with:
   - source: "introduced"
   - introducer: A
   - initial_trust: base + (T_AC * T_AB * inheritance_factor)
   - verification_required: true
```

Introduction transfers partial trust, not full trust.

---

## 6. Unknown Pool and Crystallization

### 6.1 Unknown Pool

Entities maintain a pool of undifferentiated interactions:

```json
{
  "unknown_pool": {
    "interactions": [
      {
        "identifier_hint": "ip_192.168.1.x",
        "first_seen": "2025-12-30T10:00:00Z",
        "last_seen": "2025-12-30T14:30:00Z",
        "interaction_count": 4,
        "trust_signals": ["neutral", "positive", "positive", "neutral"],
        "distinctiveness": 0.45
      }
    ]
  }
}
```

### 6.2 Crystallization Threshold

```json
{
  "crystallization_threshold": {
    "min_interactions": 3,
    "min_trust_signal": 0.3,
    "min_distinctiveness": 0.5
  }
}
```

When an unknown interaction pattern crosses all thresholds:
1. Create new relationship LCT
2. Initialize trust tensor from accumulated signals
3. Initialize stance from interaction pattern
4. Move history from pool to relationship
5. Begin normal relationship lifecycle

### 6.3 Pool Pruning

Interactions that don't crystallize get pruned:
- Inactive beyond `prune_after_days`
- Distinctiveness below `min_distinctiveness` and interaction_count > threshold
- Explicit prune command

Pruned interactions may leave aggregate statistics but lose individual records.

---

## 7. MRH for Relationships

### 7.1 Relationship Context Boundaries

Each relationship has its own MRH defining relevant context:

```json
{
  "mrh": {
    "relevant_contexts": ["energy_trading", "grid_operations"],
    "excluded_contexts": ["personal_data", "internal_systems"],
    "boundary_permeability": 0.6
  }
}
```

### 7.2 Context Matching

When processing an interaction, check relationship MRH:

```python
def context_matches(relationship, interaction):
    for context in interaction.contexts:
        if context in relationship.mrh.excluded_contexts:
            return False
        if context in relationship.mrh.relevant_contexts:
            return True

    # Not explicitly included or excluded
    return random() < relationship.mrh.boundary_permeability
```

### 7.3 MRH Evolution

MRH boundaries evolve with relationship:
- Successful interactions in a context → add to relevant_contexts
- Violations in a context → add to excluded_contexts
- Permeability adjusts with trust (higher trust → more permeable)

---

## 8. Coherence Index (CI)

### 8.1 Definition

CI measures relationship behavioral consistency over time:

```
CI = weighted_average(
    temporal_coherence,    # Interaction timing patterns
    behavioral_coherence,  # Response consistency
    stance_coherence,      # Stance stability
    identity_coherence     # Participant identity consistency
)
```

### 8.2 CI Interpretation

| CI Range | Interpretation | Recommended Action |
|----------|----------------|-------------------|
| 0.9 - 1.0 | Highly coherent | Normal operations |
| 0.7 - 0.9 | Stable | Monitor for drift |
| 0.5 - 0.7 | Variable | Investigate cause |
| 0.3 - 0.5 | Unstable | Heightened verification |
| 0.0 - 0.3 | Incoherent | Possible adversarial, consider termination |

### 8.3 CI as Trust Modifier

CI modulates effective trust:

```python
def effective_trust(relationship, dimension):
    base = relationship.trust_tensor[dimension]
    ci = relationship.coherence_index

    # Low CI reduces effective trust
    if ci < 0.5:
        modifier = 0.5 + ci  # Range: 0.5 to 1.0
    else:
        modifier = 1.0

    return base * modifier
```

---

## 9. Relationship Lifecycle

### 9.1 States

```
UNKNOWN → CRYSTALLIZING → ACTIVE → DORMANT → TERMINATED
                ↑            ↓         ↓
                └────────────┴─────────┘
                      (reactivation)
```

| State | Description |
|-------|-------------|
| **UNKNOWN** | In unknown pool, pattern emerging |
| **CRYSTALLIZING** | Threshold crossed, relationship forming |
| **ACTIVE** | Normal operation, regular interactions |
| **DORMANT** | No recent interaction, decaying |
| **TERMINATED** | Relationship ended (explicit or decay) |

### 9.2 Termination

Relationships may terminate through:
- **Explicit**: Participant declares termination
- **Decay**: Trust/CI below minimum for extended period
- **Violation**: Severe trust violation triggers immediate termination
- **Entity Termination**: Participant entity terminates

Terminated relationships:
- Retain history for reference
- Cannot be used for trust inheritance
- May be reactivated with fresh start (new LCT)

---

## 10. Cross-Relationship Effects

### 10.1 Network Effects

Relationships influence other relationships:

```python
def network_reputation(entity, context):
    """Entity's reputation in context based on relationships"""
    relationships = get_relationships(entity, context)

    reputation = 0
    total_weight = 0
    for r in relationships:
        weight = r.trust_tensor.average() * r.coherence_index
        contribution = r.stance.collaborative - r.stance.adversarial
        reputation += contribution * weight
        total_weight += weight

    return reputation / total_weight if total_weight > 0 else 0.5
```

### 10.2 Transitive Trust

Trust flows through relationship networks with decay:

```
A trusts B (0.9)
B trusts C (0.8)
A's transitive trust of C: 0.9 * 0.8 * decay_factor = 0.72 * 0.5 = 0.36
```

Transitive trust is:
- Always lower than direct trust
- Decays with each hop
- Capped at introducer's trust
- Requires verification for elevation

---

## 11. Implementation Considerations

### 11.1 Storage

Relationships stored with:
- Indexed by both participant LCTs
- Queryable by network, stance, trust ranges
- History retention policy (full, summarized, or pruned)

### 11.2 Update Frequency

| Component | Update Trigger |
|-----------|----------------|
| Trust tensor | Each significant interaction |
| Stance | Interaction patterns (batched) |
| CI | Periodic calculation (hourly/daily) |
| MRH | Context boundary events |

### 11.3 Privacy

Relationship data may be:
- **Public**: Existence and basic stance visible
- **Participant-only**: Trust details visible to participants
- **Private**: Full details visible only to relationship holder

---

## 12. Connection to Other MRH Types

This relationship model extends the MRH type system:

| MRH Type | Relationship Role |
|----------|-------------------|
| **Binding** | Permanent identity relationships |
| **Pairing** | Authorized operational relationships |
| **Witnessing** | Trust-building observation relationships |
| **Broadcast** | One-to-many announcement relationships |
| **Grounding** | Presence/coherence relationships |

Relationships themselves can be of these types, with stance determining behavior.

---

## 13. Example: Energy Market Relationship

```json
{
  "lct": "lct://grid-operator:relationship:battery-pack-001@energy-market",
  "participant_lcts": [
    "lct://grid-operator:operator:primary@energy-market",
    "lct://battery-pack-001:device:storage@energy-market"
  ],
  "formed": "2025-12-15T00:00:00Z",
  "source": "introduced",

  "trust_tensor": {
    "competence": 0.85,
    "reliability": 0.92,
    "benevolence": 0.70,
    "integrity": 0.88
  },

  "mrh": {
    "relevant_contexts": ["grid_balancing", "frequency_response", "capacity_market"],
    "excluded_contexts": ["residential_data", "competitor_operations"],
    "boundary_permeability": 0.4
  },

  "coherence_index": 0.91,

  "stance": {
    "collaborative": 0.80,
    "indifferent": 0.10,
    "competitive": 0.08,
    "adversarial": 0.02
  },

  "interaction_stats": {
    "total_transactions": 1247,
    "reciprocity_balance": 0.52,
    "disputes": 3,
    "dispute_resolutions": 3,
    "momentum": "positive"
  }
}
```

---

## 14. Research Questions

1. **Optimal crystallization thresholds** for different contexts
2. **Stance transition dynamics** - when do relationships flip?
3. **Network topology effects** on trust propagation
4. **Adversarial detection** via CI and stance patterns
5. **Cross-network relationship portability**

---

## 15. References

- SAGE Raising Relationship Schema: `hrm/sage/raising/docs/RELATIONSHIP_SCHEMA.md`
- MRH Grounding Proposal: `web4/proposals/MRH_GROUNDING_PROPOSAL.md`
- Trust Tensor Specification: `web4/docs/TRUST_TENSOR.md`
- LCT Format Specification: `web4/docs/LCT_FORMAT.md`

---

*"Relationships are the fabric of trust networks. Model them as first-class entities, and the network topology emerges naturally."*
