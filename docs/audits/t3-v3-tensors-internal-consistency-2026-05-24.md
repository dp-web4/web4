# C13: t3-v3-tensors.md Internal Consistency Audit

**Date**: 2026-05-24
**Auditor**: Autonomous session (legion-web4-20260524-060008)
**Document**: `web4-standard/core-spec/t3-v3-tensors.md` (559 lines)
**Cross-references verified**:
- `web4-standard/ontology/t3v3-ontology.ttl`
- `web4-standard/test-vectors/t3v3/tensor-operations.json`
- `web4-standard/implementation/sdk/web4/trust.py`
- `web4-standard/core-spec/atp-adp-cycle.md` §6.3, §7.1
- `web4-standard/core-spec/multi-device-lct-binding.md` §4.4

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| HIGH | 3 | Weight error in normative SPARQL; protocol-invariant formulas without normative definitions |
| MEDIUM | 4 | §10.2 cross-reference mismatches; ontology domain gap; spec-SDK Valuation range divergence |
| LOW | 4 | Naming tensions; structural redundancy; implied vs explicit invariants |

---

## HIGH Findings

### H1: §9.2 SPARQL — T3 composite weights SWAPPED

**Location**: Lines 440–444
**Severity**: HIGH

The SPARQL query in §9.2 assigns T3 composite weights as:
```sparql
BIND((?t * 0.3 + ?tr * 0.4 + ?tm * 0.3) AS ?trust)
```

Where `?t` = `web4:talent`, `?tr` = `web4:training`, `?tm` = `web4:temperament`.

This gives:
- talent = **0.3** (should be 0.4)
- training = **0.4** (should be 0.3)
- temperament = 0.3 (correct)

The canonical protocol-invariant weights (§10.2, test vector t3v3-001, SDK `T3_WEIGHTS`) are:
- talent = **0.4**, training = **0.3**, temperament = 0.3

**Impact**: §10.2 cites "§9.2" as the spec reference for T3 composite weights. The cited section contains the wrong values.

**Remediation**: Change the SPARQL BIND to `(?t * 0.4 + ?tr * 0.3 + ?tm * 0.3)`.

---

### H2: §10.2 "Diminishing returns formula" cites §7.1 — formula not defined there

**Location**: §10.2 row (line 512) referencing §7.1 (lines 371–374)
**Severity**: HIGH

The parameter governance table lists:
> Diminishing returns formula | `base_factor^(n−1)`, base=0.8, floor=0.1 | **§7.1** | t3v3-007

But §7.1 "Anti-Gaming Measures" contains only a bullet list:
```
- Exponential decay on repeated similar actions
- Witness diversity requirements
- Temporal distribution analysis
- Cross-validation with peer entities
```

The formula, base factor (0.8), and floor (0.1) are **not defined** in §7.1. They exist only in the §10.2 table itself and in test vector t3v3-007.

**Impact**: A protocol-invariant formula has no normative definition in its cited section. Implementers looking at §7.1 would find no formula to implement.

**Remediation**: Either (a) expand §7.1 with a normative sub-section defining the formula, or (b) correct the §10.2 reference to "§10.2" (self-referential, meaning the table IS the normative definition).

---

### H3: §10.2 lists protocol-invariant formulas with no spec section reference

**Location**: §10.2 rows (lines 513, 515)
**Severity**: HIGH

Two protocol-invariant formulas have "—" as their spec reference:

| Formula | Spec reference |
|---------|---------------|
| 6D-to-3D bridge formula: `primary×0.6 + secondary×(0.4/3)` | — |
| Operational health formula: `t3_composite×0.4 + v3_composite×0.3 + energy_ratio×0.3` | — |

Both are marked "Protocol-invariant" (all implementations MUST produce identical results) yet neither is defined in any normative section of the spec body. Their sole authoritative definitions are the §10.2 table row and the corresponding test vector (t3v3-008, t3v3-010).

**Impact**: Ambiguous normative status — are these formulas part of the specification proper, or just test-vector conveniences? If protocol-invariant, they need normative section text.

**Remediation**: Either (a) add normative sub-sections (e.g., §8.3 "Trust Bridge" and §8.4 "Operational Health") defining these formulas, or (b) clearly state in §10.2 preamble that the table itself is normative for formulas without section references.

---

## MEDIUM Findings

### M1: §10.2 cites §2.3 for T3 update formula — §2.3 contains different mechanism

**Location**: §10.2 rows (lines 508–509) citing §2.3 (lines 94–118)
**Severity**: MEDIUM

The §10.2 table says:
> T3 update formula | `0.02 × (quality − 0.5)` | **§2.3** | t3v3-003
> T3 dimension update factors | talent=1.0, training=0.8, temperament=0.6 | **§2.3** | t3v3-003

But §2.3 "T3 Evolution Mechanics" describes an **outcome-based table** with discrete delta ranges ("+0.02 to +0.05" for Novel Success, etc.), not the continuous quality-formula. The formula `0.02 × (quality − 0.5)` does not appear anywhere in §2.3 prose.

The SDK implements both mechanisms: `T3.update()` (quality-based) and `T3.evolve()` (outcome-based), but §2.3 text only describes the outcome-based mechanism.

**Impact**: Implementers reading §2.3 would implement the outcome-based table but miss the quality-formula entirely.

**Remediation**: Either (a) add the quality-formula to §2.3 text as an alternative update path, clearly distinguishing it from the outcome table, or (b) correct the §10.2 reference to "§10.2" if the table is the sole normative source.

---

### M2: §10.2 cites §3.3 for V3 composite weights — §3.3 defines dimension formulas only

**Location**: §10.2 row (line 507) citing §3.3 (lines 244–250)
**Severity**: MEDIUM

The §10.2 table says:
> V3 composite weights | valuation=0.3, veracity=0.35, validity=0.35 | **§3.3** | t3v3-002

But §3.3 "V3 Calculation" defines only individual dimension formulas:
```
1. Valuation = (ATP_earned / ATP_expected) * recipient_satisfaction
2. Veracity = (verified_claims / total_claims) * witness_confidence
3. Validity = 1.0 if value_transferred else 0.0
```

Followed by: "Aggregate scores use weighted averages based on recency and significance."

The specific weights (0.3, 0.35, 0.35) are **never stated** in §3.3. They exist only in §10.2 and test vector t3v3-002.

**Impact**: Implementers cannot derive the V3 composite weights from §3.3 alone.

**Remediation**: Add the weights explicitly to §3.3 text (e.g., "The V3 composite is: `valuation×0.3 + veracity×0.35 + validity×0.35`").

---

### M3: Ontology domain gap — V3Tensor binding properties undefined

**Location**: `t3v3-ontology.ttl` lines 65–73 vs spec §3 (implicit V3 binding)
**Severity**: MEDIUM

The TTL ontology declares `web4:entity` and `web4:role` with domain `web4:T3Tensor` only:
```turtle
web4:entity a rdf:Property ;
  rdfs:domain web4:T3Tensor ; ...

web4:role a rdf:Property ;
  rdfs:domain web4:T3Tensor ; ...
```

V3Tensor instances need entity-role binding too (spec §1.1 states T3/V3 are both role-contextual), but the ontology provides no mechanism for V3Tensor to use these properties without violating the declared domain constraint.

The spec §5.2 RDF examples show T3Tensor bindings but never show V3Tensor RDF. The spec §3.2 JSON example has no entity/role fields on V3.

**Impact**: An RDF validator would flag V3Tensor instances using `web4:entity` or `web4:role` as domain violations. The ontology is incomplete for the full spec's intent.

**Remediation**: Either (a) generalize the domain to a union (e.g., create a `web4:TrustTensor` superclass), or (b) add separate `web4:entity`/`web4:role` property declarations with `web4:V3Tensor` domain, or (c) document that V3 tensors derive their entity-role context from the co-located T3Tensor.

---

### M4: §3.1 Valuation "Range: Variable (can exceed 1.0)" — SDK clamps to [0.0, 1.0]

**Location**: Spec line 185 vs SDK `trust.py:289`
**Severity**: MEDIUM

Spec §3.1 states:
> #### Valuation (Subjective Worth)
> - **Range**: Variable (can exceed 1.0)

But the SDK V3 class clamps all dimensions including valuation:
```python
def __post_init__(self) -> None:
    self.valuation = _clamp(self.valuation)  # clamps to [0.0, 1.0]
```

And the `V3.calculate()` method explicitly clamps: `valuation=_clamp(valuation)`.

**Impact**: The spec allows V3 valuation > 1.0 (reflecting that perceived value can exceed expectations), but the SDK enforces a hard cap at 1.0. Cross-language implementations following the spec text would differ from the SDK.

**Remediation**: Either (a) the spec should state Valuation is clamped to [0.0, 1.0] like other dimensions, or (b) the SDK should remove the Valuation clamp to match the spec's "variable" range. Recommend (a) since test vector t3v3-002 uses V3 weights that assume normalized [0,1] inputs for meaningful composite scores.

---

## LOW Findings

### L1: §2.2 JSON example — redundant `role_tensors` and `contextual` blocks

**Location**: Lines 43–89
**Severity**: LOW

The §2.2 T3 Tensor Structure example contains two parallel objects:
- `role_tensors`: keyed by URI (`"web4:DataAnalyst"`, `"web4:ProjectManager"`, `"web4:Mechanic"`)
- `contextual`: keyed by string (`"data_analysis"`, `"project_management"`) — missing Mechanic

These appear to represent the same data with different key conventions. The `contextual` block is a subset (2 of 3 roles) with different naming. Their relationship is unexplained — neither is marked as deprecated or as an alternative encoding.

**Impact**: Implementers may be confused about which structure to use. The inconsistent subset (missing Mechanic) appears unintentional.

**Remediation**: Either (a) remove the `contextual` block (since `role_tensors` with URIs is the normative form per RDF binding), or (b) add explanatory text distinguishing the two representations, or (c) keep only one and mark the other as legacy/deprecated.

---

### L2: §2.3 conflates two update mechanisms without distinguishing their use cases

**Location**: §2.3 (lines 94–118) vs §10.2 (lines 508–509)
**Severity**: LOW

§2.3 "T3 Evolution Mechanics" describes outcome-based deltas (table with categories like Novel Success, Ethics Violation). §10.2 defines a continuous quality-formula `0.02 × (quality − 0.5)`. The SDK implements both as separate methods (`T3.evolve()` vs `T3.update()`).

The spec never explicitly states:
- When to use outcome-based evolution vs quality-formula
- Whether they're alternatives or complementary
- Whether they can be composed

**Impact**: Implementers must infer the dual-mechanism architecture from test vectors and SDK code rather than spec text.

**Remediation**: Add a brief paragraph to §2.3 explaining the two update paths and their intended use cases (e.g., "The quality-formula provides fine-grained continuous updates; the outcome table provides categorical classification for reporting and policy").

---

### L3: Test vector t3v3-010 naming tension with spec/SDK

**Location**: Test vector `tensor-operations.json` lines 183–198 vs SDK line 577
**Severity**: LOW

The test vector uses:
- `"operation": "coherence"`
- `"expected": { "coherence": 0.71 }`
- `"description": "Coherence calculation (C ≈ 0.7 threshold)"`

The spec §10.2 calls this "Operational health formula". The SDK names it `operational_health()` with an explicit comment:
```python
# NOTE: The whitepaper uses "coherence" for identity coherence (C×S×Phi×R),
# a distinct concept measuring pattern stability and self-reference.
# This SDK metric measures operational health (trust + value + energy).
```

**Impact**: The test vector's "coherence" label conflicts with the whitepaper's identity coherence concept (C×S×Phi×R). New implementers may confuse the two.

**Remediation**: Rename the test vector operation to `"operational_health"` and field to `"health"` (breaking change for test runners), or add a `"note"` field clarifying this is NOT identity coherence.

---

### L4: §10.2 "ATP conservation" cross-reference to atp-adp-cycle.md §7.1 is imprecise

**Location**: §10.2 row (line 516)
**Severity**: LOW

The table says:
> ATP conservation | total supply = ATP + ADP (invariant) | atp-adp-cycle.md §7.1 | —

atp-adp-cycle.md §7.1 states: "Tokens MUST exist in only ATP or ADP state" — a state constraint, not explicitly a conservation formula. The conservation property is *implied* by the two-state requirement combined with §6.3's "not destroyed" recycling guidance, but no single section states "total supply = ATP + ADP" as a formula.

**Impact**: Minor — the invariant is logically derivable from §7.1's two-state requirement, but the explicit formula isn't stated in the cited section.

**Remediation**: Either add a sentence to atp-adp-cycle.md §7.1 explicitly stating the conservation invariant, or update the reference to "§6.3 + §7.1 (implied)".

---

## Structural Observations (Informational)

1. **Section numbering**: Consistent and well-structured (§1–§10, sub-sections numbered correctly). No gaps or duplicates.

2. **§10 Parameter Governance**: This section (added Sprint 48) is the most cross-reference-heavy section and the source of most findings. It consolidates parameters from multiple locations, acting as both an index and a normative definition. The dual role creates ambiguity about whether §10.2 defines values or merely cites them.

3. **Ontology alignment**: The spec's JSON examples (§2.2, §3.2, §5.1) use a flat JSON structure, while the RDF examples (§2.4, §5.2) use Turtle. The two representations are well-reconciled — the ontology's "shorthand properties" (lines 102–138) explicitly bridge the gap.

4. **SDK alignment overall**: The SDK `trust.py` is highly consistent with the spec. Constants match test vectors. Both update mechanisms are implemented. The only material divergence is M4 (Valuation clamping).

5. **Test vector coverage**: The 15 vectors in `tensor-operations.json` cover all protocol-invariant parameters in §10.2 except "ATP conservation" (which has "—" as its test vector). Coverage is thorough.

---

## Cross-Audit Note

The §10.2 "Spec reference" column serves as a traceability index but has systematic accuracy issues (H1, H2, H3, M1, M2). A remediation pass should either:
1. Add normative text to each cited section so the reference is accurate, or
2. Establish that §10.2 itself is the normative source for formulas and weights, with section references serving as "related context" rather than "definition location".

Approach (2) is simpler and prevents future drift, but requires adding a preamble sentence to §10.2 clarifying its normative status.
