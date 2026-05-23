# C11 Audit: `atp-adp-cycle.md` Internal Consistency

**Date**: 2026-05-23
**Auditor**: Autonomous session (Legion, web4 track)
**Document**: `web4-standard/core-spec/atp-adp-cycle.md` (689 lines)
**Methodology**: C-series internal consistency audit (same as C2, C5, C6, C7, C8, C9, C10)
**SDK alignment**: Checked against `web4-standard/implementation/sdk/web4/atp.py` (382 lines)

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 1 | H1 |
| MEDIUM | 6 | M1, M2, M3, M4, M5, M6 |
| LOW | 2 | L1, L2 |
| **Total** | **9** | |

**Section numbering is clean** — no duplicates, no collisions, no heading-level
inconsistencies. This is a notable improvement over C7 (society-roles.md) and C8
(entity-types.md), which both had significant numbering corruption. The document
is structurally well-organized with 12 numbered sections, consistent h2/h3/h4
hierarchy, and a single sub-subsection (§2.2.1).

The primary issues are: one pseudocode defect (undefined variable), a cross-spec
terminology conflict with `r6-framework.md`, a quantitative data mismatch in a
pool metrics example, and several spec-SDK alignment gaps.

---

## HIGH Findings

### H1: §2.4 Pseudocode References Undefined Variable `caller`

**Line**: 164
**Issue**: The function `slash_atp(violator, amount, evidence)` (line 159)
references `caller` on line 164:

```python
def slash_atp(violator, amount, evidence):
    # 1. Validate slashing authority
    if not has_slashing_authority(caller):  # ← 'caller' not in parameters
        raise UnauthorizedSlashing()
```

The parameters are `violator`, `amount`, `evidence` — but `caller` is used
without being defined. The slashing authority check should apply to the entity
*initiating* the slash (the caller/authority), not the violator, so this is
a missing parameter rather than a naming error.

**Impact**: Implementers following this pseudocode will encounter a NameError
or need to guess the intent. The distinction between "who initiates the slash"
and "who gets slashed" is semantically important for authorization logic.

**Remediation**: Add `caller` (or `authority`) to the function signature:
`def slash_atp(caller, violator, amount, evidence):`

---

## MEDIUM Findings

### M1: §3.1 Pool Metrics — `charge_rate` Doesn't Match Example Data

**Lines**: 202–216
**Issue**: The pool JSON example shows:

```json
"state_distribution": {
    "ATP": 15000000,
    "ADP": 85000000
},
"metrics": {
    "charge_rate": 0.73  // "ATP/ADP ratio"
}
```

The comment says "ATP/ADP ratio," but:
- ATP/ADP = 15M/85M = **0.176**
- ATP/(ATP+ADP) = 15M/100M = **0.15** (energy ratio)
- Neither equals **0.73**

**Impact**: An implementer computing `charge_rate` from pool state will get 0.176
or 0.15, not 0.73. Either the metric definition is wrong (it measures something
other than ATP/ADP ratio) or the example value is wrong.

**Remediation**: Either:
(a) Change the value to match: `"charge_rate": 0.176` with comment `// ATP/ADP ratio`,
or (b) Change the comment to describe what 0.73 actually measures (e.g., charging
efficiency, throughput rate), or (c) Change it to energy ratio: `"charge_rate": 0.15`
with comment `// ATP/(ATP+ADP)`.

---

### M2: R6 vs R7 Terminology — Spec Uses "R6" for Reputation-Tracking Actions

**Lines**: 17, 119, 123, 545
**Issue**: The spec consistently refers to ATP discharge as involving "R6" actions:
- Line 17: `Web4: ADP + Value → ATP → R6 Action + ADP`
- Line 119: "ATP discharges through R6 transactions"
- Line 123: `"type": "R6Transaction"`
- Line 545: "Discharging MUST occur through R6 transactions"

However, the §2.3 JSON example (lines 146–150) shows T3/V3 tensor updates as
part of the discharge:
```json
"t3v3_updates": [
    {"entity": "client", "v3": {"value": +0.03}},
    {"entity": "agent", "t3": {"talent": +0.01}}
]
```

The `r6-framework.md` spec (line 5) explicitly defines R6 as the mode for
"**routine, low-consequence tasks** that don't merit reputation tracking — the
cheap default mode." T3/V3 updates *are* reputation tracking, which is R7's
domain (R6 + Reputation feedback).

**Impact**: The ATP spec labels discharge flows as R6 but demonstrates R7
behavior (reputation updates). An implementer might omit reputation tracking
from ATP discharge because the spec says "R6," or might be confused when
cross-referencing with `r6-framework.md`.

**Remediation**: Either:
(a) Change "R6" to "R7" in the discharge context (lines 17, 119, 123, 545),
since discharge with T3/V3 tracking is definitionally R7, or
(b) Separate the discharge into R6 (the transfer) and a subsequent reputation
update step, making the R6 label accurate, or
(c) Add a note clarifying that ATP discharge is R6 at the action level but
triggers R7-level reputation updates as a post-action effect.

---

### M3: §6.3 "MUST NOT Hard-Code Fee Rates" vs SDK Default `fee_rate=0.05`

**Lines**: 533–535 (spec), atp.py line 238 (SDK)
**Issue**: §6.3 states:

> "Implementations MUST NOT hard-code fee rates; they MUST read them from the
> governing society's published laws."

The SDK's `transfer()` function signature is:
```python
def transfer(sender, receiver, amount, fee_rate: float = 0.05, ...)
```

The default `fee_rate=0.05` means callers who don't explicitly pass a fee rate
get a 5% fee — a de facto hard-coded protocol-level fee. While the parameter
*can* be overridden, the default contradicts §6.3's principle that the protocol
is fee-free and fees come from society law.

**Impact**: The SDK's default behavior (5% fee on every transfer) contradicts
the spec's explicit MUST NOT. Code using `transfer(sender, receiver, 100)` will
silently apply a 5% fee that no society law authorized.

**Remediation**: Change the SDK default to `fee_rate: float = 0.0` (fee-free
by default, consistent with protocol-level behavior). Callers implementing
society-level fees would pass the society's configured rate explicitly.
Alternatively, add a `society_law` parameter and read fees from it.

---

### M4: No Cross-References to Dependent Spec Files

**Lines**: Throughout
**Issue**: The spec references several core Web4 concepts without linking to
their canonical specifications:
- **R6/R7**: Referenced 6+ times, no link to `r6-framework.md`
- **T3/V3**: Referenced 5+ times, no link to `t3-v3-tensors.md` or
  `web4-standard/ontology/t3v3-ontology.ttl`
- **LCT**: Used in URI format (`lct:web4:society:...`), no link to
  `LCT-linked-context-token.md`
- **Society**: Referenced throughout, no link to `society-roles.md` or
  `SOCIETY_SPECIFICATION.md`

Other spec files (e.g., `inter-society-protocol.md`, `society-roles.md`)
include explicit cross-references like `(see entity-types.md §3)`.

**Impact**: Readers cannot navigate from ATP/ADP concepts to their dependent
specifications. The spec assumes familiarity with R6, T3/V3, LCT, and society
concepts without pointing to where they're defined.

**Remediation**: Add a "References" section (or inline cross-references) linking
to the canonical specs for each referenced concept. Suggested placement: after
§12 (Summary) or as a new §13.

---

### M5: §4.3 Attribution Percentages Hardcoded Without Qualification

**Lines**: 360–365
**Issue**: §4.3 presents fixed attribution percentages:

```
Level 1: Direct executor (100% attribution)
Level 2: Agent/delegator (10% attribution)
Level 3: Witnesses (1% attribution)
Level 4: Society (0.1% attribution)
Level 5: Parent society (0.01% attribution)
```

§6.3 established the precedent that specific numeric values in the spec are
"**simulation parameters**, not protocol constants" and that "Implementations
MUST NOT hard-code" them. The attribution percentages should follow the same
pattern — they appear to be illustrative defaults, not protocol constants — but
no qualification is given.

**Impact**: Implementers may treat 100/10/1/0.1/0.01 as mandatory protocol
constants rather than society-configurable parameters. This contradicts the
principle of society sovereignty (§12: "Each society manages its own currency").

**Remediation**: Add a qualification note: "The percentages shown are
illustrative defaults. Societies SHOULD define attribution rates in their
economic laws. Implementations MUST NOT hard-code these values."

---

### M6: SDK Three-Pool Model Not Reflected in Spec's Two-State Model

**Lines**: Spec throughout; SDK atp.py lines 44–128
**Issue**: The spec describes tokens as existing in two states:
- §1.2: "Semifungible: Can exist in two states (charged/discharged)"
- §7.1: "Tokens MUST exist in only ATP or ADP state"

The SDK introduces a three-pool model:
- `available`: ATP ready for use
- `locked`: ATP reserved for pending operations
- `adp`: discharged tokens

With operations `lock()`, `commit()`, `rollback()` that manage the intermediate
locked state. This is a useful implementation pattern (two-phase commit for ATP
operations), but the spec doesn't mention it.

**Impact**: The SDK's `locked` state is an implementation detail that could be
normatively useful — e.g., for preventing double-spending during in-flight
transactions. Another implementation following the spec alone would have no
locked state and might encounter race conditions in concurrent operations.

**Remediation**: Either:
(a) Add a subsection to §2 or §7 describing the optional locked state as a
SHOULD/MAY implementation pattern for two-phase commit, or
(b) Document in the SDK that `locked` is an implementation optimization beyond
the normative spec's two-state requirement.

---

## LOW Findings

### L1: Unnumbered "Overview" Section Before §1

**Line**: 3
**Issue**: The document begins with `## Overview` (unnumbered) before
`## 1. Core Concepts`. This means the overview content (lines 5–8) has no
section number and cannot be referenced as "§X." While common across the spec
corpus, it creates an addressability gap.

**Impact**: Minor — the overview content is introductory and unlikely to be
cross-referenced. Consistent with other spec files that also have unnumbered
overviews.

**Remediation**: No action needed unless a cross-reference campaign standardizes
overview numbering across all spec files.

---

### L2: JSON Examples Use `"type"` Instead of `"@type"` (JSON-LD Convention)

**Lines**: 43, 122, 375, 457
**Issue**: JSON examples throughout use plain `"type"` keys:
- Line 43: `"type": "TokenMinting"`
- Line 122: `"type": "R6Transaction"`
- Line 375: `"membership_event": { ... }`
- Line 457: (monetary authority JSON)

The SDK's `to_jsonld()` methods use `"@type"` and include `"@context"` headers,
following JSON-LD conventions. Other spec files vary in their use of `@type` vs
`type` in examples.

**Impact**: Minor — examples are illustrative pseudocode, not normative JSON-LD
schemas. The actual schemas in `web4-standard/implementation/sdk/schemas/` use
proper JSON-LD conventions. However, the inconsistency between spec examples and
SDK output could confuse implementers comparing the two.

**Remediation**: Low priority. If a cross-spec normalization pass is done, update
JSON examples to use `@type` and include `@context` headers.

---

## Positive Observations

1. **Clean section numbering**: All 12 top-level sections and their subsections
   have correct, non-duplicate, non-colliding numbers. Heading levels are
   consistent (h2 for top-level, h3 for subsections, h4 for the single
   sub-subsection §2.2.1). This is notably better than C7 and C8.

2. **Consistent terminology**: ATP/ADP nomenclature matches the glossary
   definition exactly. The biological metaphor is used consistently throughout.

3. **Well-structured governance section**: §6 (Governance and Regulation) is
   thorough, with §6.3 (Transfer Fees) providing an exemplary clarification
   that distinguishes protocol-level from society-level concerns.

4. **Good pool math**: The §3.1 pool example has internally consistent totals
   (ATP+ADP=100M, allocations sum to 100M). The only issue is the `charge_rate`
   metric value (M1).

5. **SDK alignment is generally strong**: The SDK implements the core concepts
   faithfully — accounts, transfers, energy ratios, conservation invariants.
   The gaps (M3, M6) are about spec-SDK boundary clarity, not contradictions.
