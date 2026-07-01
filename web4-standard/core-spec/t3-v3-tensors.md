# Web4 T3/V3 Tensor Specification

**Formal Ontology**: [`web4-standard/ontology/t3v3-ontology.ttl`](../ontology/t3v3-ontology.ttl)
**JSON-LD Context**: [`web4-standard/ontology/t3v3.jsonld`](../ontology/t3v3.jsonld)

This document defines the Trust (T3) and Value (V3) tensor systems that provide nuanced, multi-dimensional assessment of entity capabilities and value creation in Web4.

## 1. Overview

Traditional reputation systems reduce complex behaviors to simple scores. Web4's tensor approach captures the multi-dimensional nature of trust and value, enabling context-aware assessment that evolves through actual performance.

### 1.1 Critical Design Principle: Role-Contextual Trust

**T3/V3 tensors are not absolute properties - they exist only within role contexts.** An entity trusted as a surgeon has no inherent trust as a mechanic. Trust and value are always qualified by the role being performed. RDF triples in the MRH explicitly bind tensors to entity-role pairs, ensuring trust assessments remain contextually appropriate.

## 2. T3 Tensor: Trust Through Capability

The T3 Tensor measures an entity's trustworthiness through three capability dimensions:

### 2.1 Dimensions

All three T3 dimensions are bounded to `[0.0, 1.0]`. Updates that would carry a
dimension outside this interval are **clamped** to the nearest boundary (see the
protocol-invariant range row in [§10.2](#102-protocol-invariant-parameters), test
vectors t3v3-005/t3v3-006).

#### Talent (Role-Specific Capability)
- **Range**: 0.0 to 1.0
- **Measures**: Natural aptitude for specific role, creativity within domain
- **Updates**: Increases with novel solutions in role, decreases with role-specific failures
- **Context**: Always role-qualified (e.g., talent as analyst, not general talent)

#### Training (Role-Specific Expertise)
- **Range**: 0.0 to 1.0
- **Measures**: Learned skills for role, role-specific knowledge, relevant experience
- **Updates**: Grows with successful role performance, role-relevant training
- **Context**: Qualified by role certifications and demonstrated role competence

#### Temperament (Role-Contextual Reliability)
- **Range**: 0.0 to 1.0
- **Measures**: Consistency in role, role-appropriate behavior, role ethics
- **Updates**: Improves with consistent role performance, degrades with role violations
- **Context**: Role-dependent (surgeon needs steady hands, trader needs risk tolerance)

### 2.2 T3 Tensor Structure with Role Binding

```json
{
  "t3_tensor": {
    "entity": "lct:alice",
    "role_tensors": {
      "web4:DataAnalyst": {
        "talent": 0.85,
        "training": 0.90,
        "temperament": 0.95
      },
      "web4:ProjectManager": {
        "talent": 0.65,
        "training": 0.70,
        "temperament": 0.91
      },
      "web4:Mechanic": {
        "talent": 0.20,
        "training": 0.15,
        "temperament": 0.50
      }
    },
    "evolution": [
      {
        "timestamp": "2025-01-11T15:00:00Z",
        "context": "data_analysis",
        "action": "r6:web4:...",
        "deltas": {
          "talent": 0.02,
          "training": 0.01,
          "temperament": 0.0
        },
        "reason": "Novel approach to complex analysis"
      }
    ]
  }
}
```

> **Note:** The ` ```json ` blocks in this document (§2.2, §3.2, §5.1) are
> illustrative application-level serializations, not JSON-LD bound to
> [`t3v3.jsonld`](../ontology/t3v3.jsonld). The canonical RDF shape is the Turtle
> in §2.4/§5.2; these JSON structures show how an implementation might lay out the
> same data.

### 2.3 T3 Evolution Mechanics

#### Performance-Based Updates

T3 scores evolve based on R6 action outcomes:

| Outcome | Talent Impact | Training Impact | Temperament Impact |
|---------|--------------|-----------------|-------------------|
| Novel Success | +0.02 to +0.05 | +0.01 to +0.02 | +0.01 |
| Standard Success | 0 | +0.005 to +0.01 | +0.005 |
| Expected Failure | -0.01 | 0 | 0 |
| Unexpected Failure | -0.02 | -0.01 | -0.02 |
| Ethics Violation | -0.05 | 0 | -0.10 |

#### Continuous Quality-Formula Updates

In addition to the categorical outcome table above, T3 dimensions support a
continuous update formula for fine-grained quality-based adjustments:

- **Formula**: `delta = 0.02 × (quality − 0.5)` where `quality` is in [0, 1]
- **Dimension factors**: talent=1.0, training=0.8, temperament=0.6 (each dimension's delta is scaled by its factor)

The two mechanisms serve different purposes: the **outcome table** classifies
actions into discrete categories for reporting and policy (e.g., "Novel Success",
"Ethics Violation"), while the **quality formula** provides continuous,
fine-grained trust updates per individual action quality. They are complementary
— implementations MAY use either or both depending on context.

#### Decay and Refresh

- **Training Decay**: -0.001 per month without practice
- **Temperament Recovery**: +0.01 per month of good behavior
- **Talent Stability**: No decay — Talent represents inherent capability and
  does not diminish through inactivity. This is a normative protocol property,
  not a tunable parameter.

Societies **MAY** configure custom decay policies for Training and Temperament
(e.g., different decay rates or recovery curves), but Talent's no-decay
property is invariant at the protocol level. Any half-life or decay values
for Talent appearing in simulations or explainers are simulation parameters,
not canonical specification.

### 2.4 Fractal Sub-Dimensions

T3 dimensions are **root nodes in an open-ended RDF sub-graph**, not fixed scalars. Each root dimension (Talent, Training, Temperament) can be refined with contextualized sub-dimensions linked via `web4:subDimensionOf`. The graph has no built-in dimensional bound — this is what makes T3 part of an ontology, not a fixed data structure.

**Extension mechanism**: Any domain can define sub-dimensions without modifying the core ontology:

```turtle
@prefix web4: <https://web4.io/ontology#> .
@prefix analytics: <https://web4.io/ontology/analytics#> .
@prefix lct: <https://web4.io/lct/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Domain-specific sub-dimensions of Talent
analytics:StatisticalModeling a web4:Dimension ;
    web4:subDimensionOf web4:Talent ;
    rdfs:comment "Ability to build and validate statistical models." .

analytics:DataVisualization a web4:Dimension ;
    web4:subDimensionOf web4:Talent ;
    rdfs:comment "Ability to communicate data insights visually." .

# Sub-sub-dimensions (fractal depth)
analytics:BayesianInference a web4:Dimension ;
    web4:subDimensionOf analytics:StatisticalModeling .

# T3 tensor with sub-dimension scores (full form)
_:tensor1 a web4:T3Tensor ;
    web4:entity lct:alice ;
    web4:role web4:DataAnalyst ;
    web4:talent 0.85 ;  # Aggregate (shorthand)
    web4:hasDimensionScore [
        web4:dimension analytics:StatisticalModeling ;
        web4:score 0.92 ;
        web4:observedAt "2026-02-01T10:00:00Z"^^xsd:dateTime ;
        web4:witnessedBy lct:oracle-trust
    ] ;
    web4:hasDimensionScore [
        web4:dimension analytics:DataVisualization ;
        web4:score 0.78 ;
        web4:observedAt "2026-02-01T10:00:00Z"^^xsd:dateTime ;
        web4:witnessedBy lct:oracle-trust
    ] .
```

**SPARQL traversal** — find all sub-dimensions of Talent at any depth:

```sparql
SELECT ?dim ?score WHERE {
    ?dim web4:subDimensionOf* web4:Talent .
    ?tensor web4:entity lct:alice ;
            web4:role web4:DataAnalyst ;
            web4:hasDimensionScore ?ds .
    ?ds web4:dimension ?dim ;
        web4:score ?score .
}
```

The shorthand properties (`web4:talent 0.85`) and the full `web4:hasDimensionScore` form are both valid. The shorthand carries the aggregate score of the sub-graph rooted at that dimension.

The same mechanism is open to **protocol-level extensions**, not just domain
namespaces. For example, multi-device binding contributes two dimensions that
refine the roots in a hardware context — `hardware_binding_strength` (a candidate
sub-dimension of Temperament, measuring binding stability) and
`constellation_coherence` (owned canonically by
[`multi-device-lct-binding.md`](multi-device-lct-binding.md) §4.4 and treated as a
simulation parameter in [§10.4](#104-simulation-only-parameters)). These are named
here as illustrative candidates for the extension mechanism; whether the protocol
declares them as formal `web4:subDimensionOf` triples in the core ontology is an
open coordination decision (not settled by this section).

### 2.5 Bridging Flat (6-Dimensional) Trust Schemas into the 3 Roots

Some protocol extensions carry trust as a **flat, role-agnostic schema** rather
than as a role-bound 3-root T3 tensor. The canonical mechanism for reconciling
such a schema with the three roots is the **6D→3D trust bridge** (SDK
`trust_bridge()`; test vector `t3v3-008`). It is the documented attach-path:
protocol-level flat trust schemas SHOULD be expressed as bridge *inputs* and
collapsed into the 3 roots, rather than introducing a parallel role-agnostic
composite (which §6.3 forbids).

The bridge takes six source dimensions. Three are **primary** — each maps to one
root and is weighted `0.6`. The other three are **secondary** — they are shared
equally across all three roots, each contributing `(1 − 0.6)/3 = 0.4/3 ≈ 0.1333`:

```
talent      = 0.6 × competence  + (0.4/3) × (alignment + witnesses + lineage)
training    = 0.6 × reliability + (0.4/3) × (alignment + witnesses + lineage)
temperament = 0.6 × consistency + (0.4/3) × (alignment + witnesses + lineage)
```

(All three results are clamped to `[0.0, 1.0]`; see `t3v3-008` for the worked
example.)

The six source dimensions correspond to the flat trust keys a protocol extension
typically carries — for instance the base trust block in
[`multi-device-lct-binding.md`](multi-device-lct-binding.md):

| Bridge input | Role weighting | Example flat key (multi-device) |
|--------------|----------------|----------------------------------|
| competence   | → talent (primary ×0.6)        | `technical_competence` |
| reliability  | → training (primary ×0.6)      | `social_reliability` |
| consistency  | → temperament (primary ×0.6)   | `temporal_consistency` |
| alignment    | secondary, shared ×(0.4/3)     | `context_alignment` |
| witnesses    | secondary, shared ×(0.4/3)     | `witness_count` |
| lineage      | secondary, shared ×(0.4/3)     | `lineage_depth` |

A flat trust object is therefore a set of **pre-bridge 6D source inputs** the
canonical model collapses into the 3 roots — it is *not* itself a set of roots or
sub-dimensions. The bridge does not, on its own, supply the entity-role binding
that §1.1 requires; a consumer that bridges a flat schema MUST still bind the
resulting T3 to an entity-role pair. (How a specific extension such as
multi-device binding should serialize this — bridge-on-read vs. relabel its flat
block — is a cross-document coordination decision tracked outside this section.)

## 3. V3 Tensor: Value Through Verification

The V3 Tensor quantifies value creation through three verification dimensions:

### 3.1 Dimensions

#### Valuation (Subjective Worth)
- **Range**: Variable (can exceed 1.0)
- **Measures**: Perceived value by recipients
- **Updates**: Each transaction adds to history
- **Context**: Recipient-specific and use-case dependent

> **Open question (C13/M4):** The Valuation range is a 3-way divergence
> requiring operator decision. The spec (here) and ontology (`t3v3-ontology.ttl`
> line 90: "may exceed for value") agree that Valuation can exceed 1.0. However,
> the SDK (`trust.py` `V3.__post_init__`) clamps all V3 dimensions to [0.0, 1.0],
> and test vector t3v3-002 assumes normalized [0,1] inputs for meaningful composite
> scores. Resolving this requires deciding: should Valuation be clamped (changing
> the spec and ontology) or unbounded (changing the SDK and potentially the test
> vector)? This is a semantic design decision, not a bug fix.

#### Veracity (Objective Accuracy)
- **Range**: 0.0 to 1.0
- **Measures**: Truthfulness, accuracy, reproducibility
- **Updates**: External validation and witness attestation
- **Context**: Domain-specific verification standards

#### Validity (Confirmed Transfer)
- **Range**: 0.0 to 1.0
- **Measures**: Actual value delivery and receipt
- **Updates**: Binary per transaction, averaged over time
- **Context**: Completion of value transfer cycle

### 3.2 V3 Tensor Structure

```json
{
  "v3_tensor": {
    "aggregate": {
      "total_value_created": 15420,  // In ATP units
      "average_valuation": 0.87,
      "veracity_score": 0.93,
      "validity_rate": 0.98
    },
    "recent": [
      {
        "timestamp": "2025-01-11T14:00:00Z",
        "action": "r6:web4:...",
        "valuation": 0.95,
        "veracity": 0.98,
        "validity": 1.0,
        "atp_generated": 55,
        "recipient": "lct:web4:...",
        "witness_count": 3
      }
    ],
    "by_context": {
      "data_processing": {
        "transactions": 45,
        "average_valuation": 0.91,
        "veracity": 0.95,
        "validity": 0.99
      },
      "content_creation": {
        "transactions": 23,
        "average_valuation": 0.78,
        "veracity": 0.88,
        "validity": 0.96
      }
    }
  }
}
```

### 3.3 V3 Calculation

For each completed R6 action:

1. **Valuation** = (ATP_earned / ATP_expected) * recipient_satisfaction
2. **Veracity** = (verified_claims / total_claims) * witness_confidence
3. **Validity** = 1.0 if value_transferred else 0.0

Aggregate scores use weighted averages based on recency and significance.

The **composite V3 score** combines the three dimensions with the protocol-invariant
weights `valuation=0.3, veracity=0.35, validity=0.35` (the authoritative values are
those in the [§10.2](#102-protocol-invariant-parameters) table; test vector t3v3-002).
This parallels the T3 composite *structure* — a single weighted sum of the three
dimensions — applied in the [§9.2](#92-mrh-graph-integration) SPARQL, but uses its own
weights (V3 `0.3/0.35/0.35`, distinct from T3's `0.4/0.3/0.3`).

## 4. Tensor Interactions

### 4.1 T3 → V3 Influence

Higher T3 scores correlate with better V3 outcomes:
- High **Talent** → Higher **Valuation** (innovative solutions valued more)
- High **Training** → Higher **Veracity** (expertise produces accurate results)
- High **Temperament** → Higher **Validity** (reliability ensures delivery)

### 4.2 V3 → T3 Feedback

V3 outcomes influence T3 evolution:
- Consistent high **Valuation** → Talent recognition
- Verified **Veracity** → Training validation
- Perfect **Validity** → Temperament reinforcement

## 5. Role-Based Tensor Application

### 5.1 Role-Specific Trust Matching

Roles specify required T3 thresholds, and entities are matched based on role-specific tensors:

```json
{
  "role": "web4:Surgeon",
  "role_requirements": {
    "minimum_t3": {
      "talent": 0.7,      // High precision required
      "training": 0.9,    // Extensive medical training
      "temperament": 0.85 // Steady under pressure
    }
  },
  "candidate_evaluation": {
    "lct:alice": {
      "role_tensor": {
        "talent": 0.95,
        "training": 0.92,
        "temperament": 0.88
      },
      "qualified": true,
      "trust_score": 0.92  // Computed for THIS role
    }
  }
}
```

### 5.2 RDF Role-Tensor Binding

> **Vocabulary note:** `web4:hasRole` is defined in
> [`web4-core-ontology.ttl`](../ontology/web4-core-ontology.ttl), not in the two
> ontology files named in this document's header
> ([`t3v3-ontology.ttl`](../ontology/t3v3-ontology.ttl) /
> [`t3v3.jsonld`](../ontology/t3v3.jsonld)). A processor resolving these triples
> must load the core ontology as well.

```turtle
@prefix web4: <https://web4.io/ontology#> .
@prefix lct: <https://web4.io/lct/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# T3 tensors are bound to entity-role pairs
lct:alice web4:hasRole web4:Surgeon .
lct:alice web4:hasRole web4:Researcher .

_:tensor1 a web4:T3Tensor ;
    web4:entity lct:alice ;
    web4:role web4:Surgeon ;
    web4:talent 0.95 ;
    web4:training 0.92 ;
    web4:temperament 0.88 .

_:tensor2 a web4:T3Tensor ;
    web4:entity lct:alice ;
    web4:role web4:Researcher ;
    web4:talent 0.80 ;
    web4:training 0.85 ;
    web4:temperament 0.90 .

# Full form with sub-dimension scores (equivalent to shorthand above)
_:tensor1 web4:hasDimensionScore [
    web4:dimension web4:Talent ;
    web4:score 0.95 ;
    web4:observedAt "2026-01-15T10:00:00Z"^^xsd:dateTime ;
    web4:witnessedBy lct:hospital-oracle
] .
```

Both the shorthand (`web4:talent 0.95`) and full (`web4:hasDimensionScore`) forms are valid. See [Section 2.4](#24-fractal-sub-dimensions) for how sub-dimensions extend these root scores.

> **Note on V3 entity-role binding:** The ontology (`t3v3-ontology.ttl`) declares
> `web4:entity` and `web4:role` with domain `web4:T3Tensor` only. V3 tensors
> derive their entity-role context from the co-located T3Tensor for the same
> entity-role pair, rather than carrying independent `web4:entity`/`web4:role`
> properties. This avoids domain violations in RDF validators while preserving
> the §1.1 principle that both T3 and V3 are role-contextual.

### 5.3 Role-Aware Value Pricing

ATP costs derived from role-specific V3 expectations:

```python
def calculate_atp_price(entity_id, role, task_type):
    # Get role-specific V3 tensor
    v3 = get_v3_for_role(entity_id, role)
    
    # Price depends on role-task alignment
    if not role_matches_task(role, task_type):
        return INVALID_ROLE_PRICE  # Very high or rejection
    
    # Role-appropriate pricing
    base_cost = get_role_base_cost(role)
    role_multiplier = get_role_value_multiplier(role)
    
    return base_cost * (1 + v3.valuation) * v3.veracity * v3.validity * role_multiplier
```

## 6. Implementation Requirements

### 6.1 Calculation Precision
- All tensor values MUST use at least 3 decimal places
- Updates MUST be atomic and consistent
- Historical data MUST be preserved

### 6.2 Update Frequency
- T3 updates SHOULD occur after each R6 action
- V3 updates MUST occur upon value confirmation
- Decay calculations SHOULD run daily

### 6.3 Role-Based Segregation
- Implementations MUST NOT compute global (role-agnostic) trust scores — only role-specific tensors
- Each role MUST maintain separate T3/V3 tensors
- New roles MUST start with minimal trust, not inherited from other roles
- Cross-role trust transfer MUST require explicit bridging

## 7. Privacy and Gaming Prevention

### 7.1 Anti-Gaming Measures
- Exponential decay on repeated similar actions. For the `n`-th repetition of a
  similar action the diminishing-returns factor is
  `factor = max(base_factor^(n−1), floor)` with `base_factor=0.8` and `floor=0.1`
  (the authoritative values are those in the [§10.2](#102-protocol-invariant-parameters)
  table; test vector t3v3-007).
- Witness diversity requirements
- Temporal distribution analysis
- Cross-validation with peer entities

### 7.2 Privacy Protection
- Tensor details MAY be selectively disclosed
- Aggregate scores MAY be public
- Evolution history MAY be truncated
- Context labels MAY be anonymized

## 8. Advanced Features

### 8.1 Tensor Prediction
Based on historical patterns:
- Predict T3 evolution trajectories
- Estimate V3 outcomes for actions
- Recommend improvement strategies

### 8.2 Role-Aware Tensor Composition
For composite entities:
- Team T3 for role = weighted average of members' tensors FOR THAT ROLE
- Organization V3 = sum of role-appropriate contributions
- Cannot average trust across different roles
- Multi-role teams compose role-specific sub-teams

Example:
```python
# Mirrors the SDK helper web4.trust.compute_team_t3(...)
def compute_team_t3(team_members, required_role):
    role_qualified = [m for m in team_members 
                      if has_role(m, required_role)]
    
    if not role_qualified:
        return None  # No member holds the required role

    # Average only among those with the role
    role_tensors = [get_t3_for_role(m, required_role) 
                    for m in role_qualified]
    return weighted_average(role_tensors)
```

### 8.3 Cross-Tensor Analytics
- Identify T3/V3 correlation patterns
- Detect anomalous tensor evolution
- Optimize for specific tensor targets

## 9. Integration with R6 and MRH

### 9.1 R6 Role-Based Updates

The R6 framework updates tensors within role contexts:

1. **Before Action**: Role-specific T3 used for confidence
2. **During Action**: Monitor performance in role context
3. **After Action**: Update tensors for performed role only
4. **As Reference**: Role-specific history informs similar roles

### 9.2 MRH Graph Integration

RDF triples in MRH explicitly track role-tensor relationships:

```sparql
# Query for best entity-role match for task
PREFIX web4: <https://web4.io/ontology#>

SELECT ?entity ?role ?trust WHERE {
    ?tensor web4:entity ?entity ;
            web4:role ?role ;
            web4:matchesTask ?taskType .
    
    # Calculate composite trust for role
    ?tensor web4:talent ?t ;
            web4:training ?tr ;
            web4:temperament ?tm .
    
    BIND((?t * 0.4 + ?tr * 0.3 + ?tm * 0.3) AS ?trust)
}
ORDER BY DESC(?trust)
LIMIT 1
```

This creates a continuous learning loop where every action refines role-specific capabilities, preventing trust leakage across unrelated domains.

### 9.3 Sub-Dimension Traversal in SPARQL

Queries can traverse the fractal sub-dimension graph using `web4:subDimensionOf*` property paths:

```sparql
# Find all Talent sub-dimensions and their scores for an entity-role pair
PREFIX web4: <https://web4.io/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?dim ?dimLabel ?score WHERE {
    ?dim web4:subDimensionOf* web4:Talent .
    ?tensor web4:entity ?entity ;
            web4:role ?role ;
            web4:hasDimensionScore ?ds .
    ?ds web4:dimension ?dim ;
        web4:score ?score .
    OPTIONAL { ?dim rdfs:comment ?dimLabel }
}
ORDER BY DESC(?score)

# Compare sub-dimension profiles across two entities for the same role
PREFIX web4: <https://web4.io/ontology#>
PREFIX lct: <https://web4.io/lct/>

SELECT ?dim ?scoreA ?scoreB WHERE {
    ?dim web4:subDimensionOf* web4:Training .

    ?tensorA web4:entity lct:alice ; web4:role web4:Surgeon ;
             web4:hasDimensionScore [ web4:dimension ?dim ; web4:score ?scoreA ] .
    ?tensorB web4:entity lct:bob ; web4:role web4:Surgeon ;
             web4:hasDimensionScore [ web4:dimension ?dim ; web4:score ?scoreB ] .
}
```

## 10. Parameter Governance

This section classifies all trust, value, and energy parameters by governance
tier: who decides the value, and what latitude implementers have. It
synthesizes normative decisions from §2.3 and §3.3 of this document,
[`atp-adp-cycle.md`](atp-adp-cycle.md) §6.3/§7, and
[`multi-device-lct-binding.md`](multi-device-lct-binding.md) §4.4.

### 10.1 Governance Tiers

| Tier | RFC 2119 keyword | Meaning |
|------|-----------------|---------|
| **Protocol-invariant** | MUST / MUST NOT | Fixed by the specification. Implementations MUST use exactly these values. Cross-language test vectors enforce them. |
| **Society-configurable** | MAY / SHOULD | Societies set these via published economic or governance laws. The protocol provides defaults but does not mandate them; some carry SHOULD recommendations for adoption or transparency (e.g. §10.3 demurrage). |
| **Simulation-only** | N/A | Not protocol parameters. Appear in explainers, demos, or simulations. MUST NOT be cited as canonical values. |

### 10.2 Protocol-Invariant Parameters

These values are fixed by the specification. All conforming implementations
MUST produce identical results (enforced by cross-language test vectors in
`web4-standard/test-vectors/t3v3/tensor-operations.json`).

**This table is the normative source** for all protocol-invariant formulas,
weights, and constants listed below. The "Related context" column identifies
where the parameter is discussed or motivated in the spec body, but the
authoritative values are those stated in this table. Where a parameter has
no related context ("—"), the table row and its corresponding test vector
constitute the complete normative definition.

| Parameter | Value | Related context | Test vector |
|-----------|-------|-----------------|-------------|
| T3 composite weights | talent=0.4, training=0.3, temperament=0.3 | §9.2 | t3v3-001 |
| V3 composite weights | valuation=0.3, veracity=0.35, validity=0.35 | §3.3 | t3v3-002 |
| T3 update formula | `0.02 × (quality − 0.5)` | §2.3 | t3v3-003 |
| T3 dimension update factors | talent=1.0, training=0.8, temperament=0.6 | §2.3 | t3v3-003 |
| Talent no-decay | Talent MUST NOT decay through inactivity | §2.3 | t3v3-012 |
| T3 value range | [0.0, 1.0] — clamped at boundaries | §2.1 | t3v3-005, t3v3-006 |
| V3 Veracity / Validity range | [0.0, 1.0] — clamped at boundaries (SDK-enforced in `V3.__post_init__`; no dedicated V3 boundary vector — t3v3-002/t3v3-014 exercise interior values only) | §3.1 | t3v3-002, t3v3-014 |
| Diminishing returns formula | `base_factor^(n−1)`, base=0.8, floor=0.1 | §7.1 | t3v3-007 |
| 6D-to-3D bridge formula | primary×0.6 + secondary×(0.4/3) | [§2.5](#25-bridging-flat-6-dimensional-trust-schemas-into-the-3-roots) | t3v3-008 |
| V3 calculation | valuation=(earned/expected)×satisfaction; veracity=(verified/total)×confidence; validity=1.0 if transferred else 0.0 | §3.3 | t3v3-014 |
| Operational health formula | t3_composite×0.4 + v3_composite×0.3 + energy_ratio×0.3 (note: test vector t3v3-010 labels this "coherence" — this is **not** identity coherence C×S×Phi×R from the whitepaper; it measures operational health) | — | t3v3-010 |
| ATP conservation | total supply = ATP + ADP (transfers preserve total supply; the per-transfer form is `initial == final + fees`) | [`atp-adp-cycle.md`](atp-adp-cycle.md) §3.1/§3.2 (supply equation `total supply = ATP + ADP`), §2.4 (per-transfer invariant `initial == final + fees`; Slashing is the deliberate exception), §6.3 (fee-recycling preserves total supply) | — |

> **V3 Valuation range** is deliberately omitted from the table above: its
> classification is the unresolved 3-way divergence flagged in the §3.1 open
> question (C13/M4), pending an operator decision. Only Veracity and Validity
> are protocol-invariant at [0.0, 1.0].

### 10.3 Society-Configurable Parameters

Societies MAY set these parameters via their published governance laws.
The protocol provides reference defaults; societies override them by
declaring values in their law structure.

| Parameter | Reference default | Governance | Spec reference |
|-----------|-------------------|------------|----------------|
| Training decay rate | −0.001 per month | Societies MAY configure custom decay policies for Training | §2.3 |
| Temperament recovery rate | +0.01 per month | Societies MAY configure custom recovery curves for Temperament | §2.3 |
| ATP decay rate | Implementation-specific | Societies MAY implement custom decay rates | [`atp-adp-cycle.md`](atp-adp-cycle.md) §7.3 |
| ATP transfer fees | None (fee-free at protocol level) | Societies MAY levy transfer fees; rate, bearer, and destination MUST be declared in published laws | [`atp-adp-cycle.md`](atp-adp-cycle.md) §6.3 |
| Demurrage policy | None prescribed | Societies SHOULD implement demurrage | [`atp-adp-cycle.md`](atp-adp-cycle.md) §7.2 |
| Charging mechanisms | Not prescribed | Societies MAY choose charging mechanisms | [`atp-adp-cycle.md`](atp-adp-cycle.md) §7.3 |
| Exchange rate policy | Not prescribed | Societies MAY create exchange agreements; rates SHOULD be transparent | [`atp-adp-cycle.md`](atp-adp-cycle.md) §7.2–7.3 |
| Role requirement thresholds | Per-role | Societies and role definitions set minimum T3 thresholds for role qualification | §5.1 |

### 10.4 Simulation-Only Parameters

These values appear in explainers, demos, and simulations but are **not**
protocol parameters. Implementations MUST NOT hard-code them as canonical.

| Parameter | Example values | Why not canonical | Spec reference |
|-----------|---------------|-------------------|----------------|
| `constellation_coherence` multiplier | "1.4× CI bonus" | Measures identity strength, not economic scaling; multiplier magnitudes are chosen per simulation | [`multi-device-lct-binding.md`](multi-device-lct-binding.md) §4.4 |
| CI thresholds and labels | "CI > 0.8 = strong" | Derived labels from `constellation_coherence`; not standalone protocol primitives | [`multi-device-lct-binding.md`](multi-device-lct-binding.md) §4.4 |
| Talent decay/half-life | "0.995 per period" | Talent no-decay is a protocol invariant (§2.3); any decay value violates the spec | §2.3 |
| Specific fee rates | "5% transfer fee" | Fee rates are society-configurable, not protocol constants | [`atp-adp-cycle.md`](atp-adp-cycle.md) §6.3 |
| Specific ATP decay rates | "1% per day" | Decay rates are society-configurable, not protocol constants | [`atp-adp-cycle.md`](atp-adp-cycle.md) §7.3 |

### 10.5 Governance Principle

The three-tier classification follows a consistent principle across the spec:

> **The protocol prescribes formulas and invariants. Societies configure
> rates and policies. Simulations choose presentation values.**

When a parameter appears in a simulation or explainer, it SHOULD be labeled
as a simulation parameter (not "the Web4 value"). When a society sets a
rate, it MUST publish the value in its governance laws. When the protocol
prescribes a formula, all implementations MUST produce identical results
regardless of society or context.