# Whitepaper-to-SDK Coherence Audit

**Date**: 2026-03-15
**Auditor**: Autonomous session (Legion)
**Scope**: Compare whitepaper (Parts 2-3) and glossary against Python SDK v0.1.0 modules
**Method**: Section-by-section comparison of whitepaper concepts against SDK implementations

---

## Summary

The SDK faithfully implements the **core-spec** files. However, the **whitepaper** describes
several concepts at a higher level of abstraction that the SDK either simplifies or omits.
Most omissions are architectural/philosophical (appropriate for a whitepaper) rather than
implementation gaps. A few are genuine divergences worth tracking.

**Findings**: 12 items total — 4 divergences, 3 gaps, 5 alignments-with-notes

---

## Divergences (spec says X, SDK does Y)

### D1: `coherence()` — Two Different Concepts Share One Name

| Source | Definition |
|--------|------------|
| **Whitepaper §2.7** | Identity Coherence = C × S × Phi × R (pattern stability × self-reference × integration × role consistency) |
| **Glossary** | Same as whitepaper — C×S×Phi×R, thresholds at 0.3/0.5/0.7/0.85 |
| **SDK trust.py:226** | `coherence(t3, v3, energy_ratio)` = weighted combination of T3 composite, V3 composite, and ATP energy ratio |

**Impact**: The whitepaper's coherence (identity stability) is a prerequisite for trust
accumulation. The SDK's coherence (trust+value+energy health) is an operational health
metric. These are fundamentally different quantities using the same name.

**Priority**: HIGH — naming collision creates confusion. The SDK's function should be
renamed (e.g., `entity_health()` or `operational_coherence()`) or the identity coherence
framework should be implemented separately.

**Resolution** (U3a, 2026-03-15): Renamed to `operational_health()`/`is_healthy()` with
docstring explaining the distinction from whitepaper identity coherence (C×S×Phi×R).

### D2: R6 vs R7 Naming Inconsistency

| Source | Name | Components |
|--------|------|------------|
| **Whitepaper §2.4** | "R6 Action Framework" | Rules+Role+Request+Reference+Resource → Result (6 components) |
| **Core-spec r7-framework.md** | "R7 Action Framework" | Rules+Role+Request+Reference+Resource → Result + **Reputation** (7 components) |
| **SDK module** | `web4.r6` (module name) | Implements R7 (7 components including ReputationDelta) |

**Impact**: The whitepaper still describes R6. The core-spec and SDK implement R7. The
SDK module is named `r6.py` but implements R7. The whitepaper §2.4.4 describes the
learning loop (reputation feedback) but doesn't call it R7 or list Reputation as a
component.

**Priority**: MEDIUM — the whitepaper should be updated to reflect R7, or at minimum
note the evolution. The `r6-framework-legacy.md` core-spec exists but the whitepaper
doesn't reference it. Module name `r6` is fine (acronym protection per CLAUDE.md).

**Resolution** (U3b, 2026-03-15): §2.4.4 updated to name Reputation as the 7th component
and explain the R6→R7 evolution, preserving R6 as the protected acronym.

### D3: MRH — Five Dimensions vs Graph Model

| Source | MRH Model |
|--------|-----------|
| **Whitepaper §2.5.2** | Five-dimensional tensor: Fractal Scale, Informational Scope, Geographic Scope, Action Scope, Temporal Scope |
| **Core-spec mrh-tensors.md** | RDF graph with typed edges (binding, pairing, witnessing), traversed by BFS with horizon depth |
| **SDK mrh.py** | Graph model with 12 relation types, horizon traversal, trust propagation |

**Impact**: The whitepaper describes MRH as a 5-dimension scoping lens. The core-spec
and SDK implement it as a relationship graph. These are complementary but different. The
5-dimension model is not represented anywhere in the implementation.

**Priority**: MEDIUM — the graph model is more practical and the core-spec has evolved
past the 5-dimension view. The whitepaper should either be updated to describe the graph
model or explicitly note that the 5-dimension view is the conceptual frame while the
graph is the implementation.

**Resolution** (U3b, 2026-03-15): Added §2.5.4 "From Conceptual Dimensions to Relationship
Graphs" reconciling the 5-dimension conceptual model with the graph-based implementation.
Explains how each dimension maps to graph properties and why the graph model is more expressive.

### D4: Entity Types — Whitepaper vs SDK Taxonomy

| Source | Types Listed |
|--------|-------------|
| **Whitepaper §2.2.1** | Humans, AI Agents, Organizations, Roles, Tasks, Data Resources, **Thoughts** (7 types) |
| **Core-spec entity-types.md** | 15 types (Human, AI, Society, Organization, Role, Task, Resource, Device, Service, Oracle, Accumulator, Dictionary, Hybrid, Policy, Infrastructure) |
| **SDK EntityType enum** | 15 types (same as core-spec) |

**Impact**: The whitepaper's list is illustrative, not exhaustive — it says "This includes:"
rather than "These are:". However, "Thoughts" appears in the whitepaper but has no
corresponding entity type in core-spec or SDK. Several core-spec types (Society, Device,
Service, Oracle, Accumulator, Policy, Infrastructure) are not mentioned in the whitepaper.

**Priority**: LOW — the whitepaper is intentionally high-level. "Thoughts" is conceptual.
No action needed unless the whitepaper is being formalized as a normative spec.

---

## Gaps (whitepaper describes it, SDK doesn't implement it)

### G1: Identity Coherence (C×S×Phi×R) — Not Implemented

The whitepaper §2.7 and glossary define a detailed identity coherence framework with:
- Four components (C, S, Phi, R)
- Five thresholds (C_REACTIVE through C_EXEMPLARY)
- Coherence as a prerequisite gate for trust accumulation
- Death spiral prevention mechanisms
- Agent-type-specific minimum requirements

The SDK has no implementation of this framework. The `is_coherent()` function in trust.py
checks a different quantity (see D1).

**Priority**: HIGH — this is a foundational concept in the whitepaper. However, it may
be intentionally deferred: identity coherence measurement requires multi-session behavioral
analysis, which is more appropriate for a runtime system (like SAGE/HRM) than a data
structures SDK.

**Recommendation**: Either (a) add a stub module `web4.coherence` with the data structures
(thresholds, agent requirements) even if the measurement logic lives elsewhere, or (b)
document in the SDK that identity coherence is a runtime concern implemented by SAGE/HRM.

### G2: T3/V3 Fractal Sub-Dimensions — Not Modeled

The whitepaper §3.2.4 and glossary describe T3/V3 as fractal RDF sub-graphs where each
root dimension can have unlimited domain-specific sub-dimensions via `web4:subDimensionOf`.
The RDF ontology (`t3v3-ontology.ttl`) defines this property.

The SDK's T3/V3 are flat 3-field dataclasses with no sub-dimension support. The composite
scores are fixed-weight aggregates of three floats.

**Priority**: MEDIUM — the flat model is sufficient for current SDK use cases. Sub-dimension
support would require either RDF graph integration or a hierarchical data structure. This
is an intentional simplification for v0.1.0.

**Recommendation**: Track as a v0.3.0+ feature. Note the simplification in SDK docstrings.

### G3: Value Confirmation Mechanism (VCM) — Not Explicit

The whitepaper §3.1.4 describes recipient-centric value confirmation with multi-party
attestation and trust-weighted validators. The SDK's ATP module has `transfer()`,
`sliding_scale()`, and `recharge()` but no explicit VCM protocol.

**Priority**: LOW — VCM is a protocol-level concern. The SDK provides the data structures
(ATPAccount, TransferResult) that VCM would use. The protocol itself belongs in a
higher-level orchestration layer.

---

## Aligned (with notes)

### A1: ATP/ADP Cycle — Strong Alignment

Whitepaper §3.1, core-spec, and SDK all agree on the biological metaphor, three-pool
model (available/locked/ADP), conservation invariant, and energy ratio. The SDK's
implementation is faithful to both whitepaper and core-spec.

**Note**: The whitepaper's "dynamic exchange rates" (§3.1.5) — quality-based ADP→ATP
conversion returning 0.8x to 1.5x — is partially captured by `recharge(rate)` but the
quality linkage isn't explicit. Minor gap.

### A2: LCT Core Properties — Strong Alignment

Whitepaper §2.1, core-spec, and SDK agree on: permanent binding, non-transferability,
cryptographic root, contextual expression, lifecycle (creation/active/void/slashed),
birth certificate issuance, MRH structure.

**Note**: The SDK has `SUSPENDED` revocation status not mentioned in the whitepaper
(whitepaper only describes void and slashed). This is a reasonable SDK extension.

### A3: T3/V3 Root Dimensions — Strong Alignment

All three sources agree on the three root dimensions for each tensor, role-contextual
binding, and update mechanics from action outcomes.

**Note**: Composite weights differ slightly across documents (see MEMORY.md spec
divergences section), but the SDK's weights match the test vectors, which are canonical.

### A4: Society-Authority-Law — Strong Alignment

Whitepaper concepts of delegative governance, law inheritance, witness quorum, and
authority scoping are all faithfully implemented in `web4.federation`.

**Note**: The whitepaper doesn't detail the Norm/Procedure/Interpretation law model
as deeply as the core-spec does. The SDK follows the core-spec.

### A5: Dictionary Entities — Strong Alignment

Whitepaper §2.6 and SDK `web4.dictionary` are well aligned on: living entities with LCTs,
domain bridging, compression-trust relationship, multiplicative degradation across
translation chains, evolution/learning, and semantic reputation.

**Note**: The whitepaper's philosophical depth (§2.6.7 "The Keeper's Responsibility",
§2.6.9 "The Living Language") is appropriately beyond SDK scope.

---

## Whitepaper Concepts Intentionally Outside SDK Scope

These whitepaper sections describe concepts that are architectural/philosophical and
appropriately NOT in a data structures SDK:

| Whitepaper Section | Concept | Where It Belongs |
|-------------------|---------|-----------------|
| Part 5 (§5) | Memory as Temporal Sensor | Runtime system (SAGE/HRM) |
| Part 6 (§6) | Blockchain Typology (4-chain hierarchy) | Ledger infrastructure |
| §2.8 | Trust as Gravity | Architectural principle (no code needed) |
| §2.5.4 | RDF Ontological Backbone | Ontology files (TTL), not Python SDK |
| §2.7 (partial) | Death spiral prevention | Runtime system with temporal state |
| Part 7 (§7) | Implementation details / status | Meta-documentation |
| Part 4 (§4) | Implications and Vision | Philosophy |

---

## Priority Summary

| ID | Finding | Priority | Status |
|----|---------|----------|--------|
| D1 | `coherence()` naming collision | HIGH | **RESOLVED** (U3a) — renamed to `operational_health()`/`is_healthy()` |
| G1 | Identity coherence not implemented | HIGH | OPEN — runtime concern (SAGE/HRM scope, not SDK) |
| D2 | R6 vs R7 naming | MEDIUM | **RESOLVED** (U3b) — §2.4.4 names Reputation as 7th component |
| D3 | MRH 5-dim vs graph model | MEDIUM | **RESOLVED** (U3b) — §2.5.4 reconciles conceptual vs implementation model |
| G2 | No fractal sub-dimensions | MEDIUM | OPEN — tracked for v0.3.0+ |
| D4 | Entity type taxonomy mismatch | LOW | OPEN — no action needed (whitepaper is illustrative) |
| G3 | VCM not explicit | LOW | OPEN — protocol-layer concern |

---

## U3 Resolution Summary

Both U3 sub-tasks are now complete:

1. **U3a: SDK coherence naming fix** — DONE (2026-03-15, PR #17). Renamed
   `coherence()`→`operational_health()`, `is_coherent()`→`is_healthy()`. All 292 tests passing.

2. **U3b: Whitepaper section updates** — DONE (2026-03-15). Updated §2.4.4 (R7 evolution)
   and added §2.5.4 (MRH graph reconciliation). §2.2 entity type expansion skipped (D4 rated LOW).

## Remaining Open Items

- **G1**: Identity coherence (C×S×Phi×R) — runtime concern, belongs in SAGE/HRM, not SDK
- **G2**: T3/V3 fractal sub-dimensions — tracked for SDK v0.3.0+
- **D4**: Entity type taxonomy — no action needed (whitepaper list is illustrative)
- **G3**: Value Confirmation Mechanism — protocol-layer concern
