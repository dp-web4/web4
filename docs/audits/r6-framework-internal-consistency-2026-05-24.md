# C12 Internal Consistency Audit: r6-framework.md

**Date**: 2026-05-24
**Auditor**: Autonomous session (legion-web4-20260524-000005)
**File**: `web4-standard/core-spec/r6-framework.md` (583 lines)
**Cross-references checked**: `r7-framework.md`, `atp-adp-cycle.md`, `t3-v3-tensors.md`, `society-roles.md`, SDK `web4/r6.py`
**Series**: C12 (continues C1-C11 internal consistency audit pipeline)

## Summary

11 findings: 1 HIGH, 6 MEDIUM, 4 LOW.

The R6 spec is structurally sound (section numbering clean, flow logical), but
carries several fields and characterizations that diverge from the R7 spec and SDK,
suggesting the R6 spec was written before the R7 evolution and not fully reconciled.
The most significant issue is the Role structure containing legacy fields (`roleType`,
`scopeContext`) absent from R7 and SDK, and missing `v3InRole` which both R7 and SDK
include.

The previously flagged r6/r7 tension ("R6 Result includes tensor updates" vs "R7 says
R6 has no reputation feedback") is investigated and found to be **consistent but
imprecisely worded** — R6 does update tensors in the Result, but not as first-class
tracked reputation (which is R7's addition). The Overview's "don't merit reputation
tracking" characterization should be qualified.

## Findings

### H1 (HIGH) — §1.2 Role: `roleType` field absent from R7 spec and SDK

**Location**: Lines 60-61

**Issue**: R6 §1.2 Role structure includes both `roleType` ("web4:DataAnalyst") and
`roleLCT` ("lct:web4:role:analyst:..."). R7 §1.2 only has `roleLCT`. SDK `Role` class
only has `role_lct`.

**Analysis**: The two fields appear to serve overlapping purposes — `roleType` is a
semantic type URI, `roleLCT` is an instance LCT identifier. R7 and SDK dropped
`roleType`, consolidating to `roleLCT` alone. The R6 spec carrying both creates
ambiguity: are they both required? What is the relationship between them?

**Proposed fix**: Either (a) remove `roleType` from R6 Role structure to match R7 and
SDK, or (b) if the distinction is intentional (type vs instance), add a note explaining
the relationship and why R7 dropped it. Option (a) is recommended — R7's consolidation
to `roleLCT` is the current canonical design, and R6 should match.

**Also affected**: `scopeContext` field (line 62) is present in R6 §1.2 but absent
from R7 §1.2 and SDK. Same recommendation applies — remove or explain.

---

### M1 (MEDIUM) — §1.2 Role: missing `v3InRole`

**Location**: Lines 63-68

**Issue**: R6 §1.2 Role structure includes `t3InRole` but not `v3InRole`. R7 §1.2
includes both `t3InRole` and `v3InRole`. SDK `Role` class has both `t3_in_role` and
`v3_in_role`.

**Cross-document check**: R6 §1.6 Result includes V3 tensor updates
(`"v3": {"veracity": +0.02, "validity": 1.0}` at line 204). If R6 Result updates V3
tensors, the Role context carrying the action should include the V3 baseline —
otherwise the V3 deltas in the Result have no documented starting point.

**Proposed fix**: Add `v3InRole` to R6 §1.2 Role structure, matching R7 §1.2 format:
```json
"v3InRole": {
  "veracity": 0.92,
  "validity": 0.88,
  "value": 0.85
}
```

---

### M2 (MEDIUM) — §5.5 tensorUpdates: ad-hoc multi-party key format

**Location**: Lines 477-480

**Issue**: R6 §5.5 (Agency-Delegated Action) uses `"agent_t3"` and `"client_v3"` as
`tensorUpdates` keys for multi-party tensor attribution:
```json
"tensorUpdates": {
    "agent_t3": {"temperament": +0.01},
    "client_v3": {"validity": +0.005}
}
```

This is inconsistent with §1.6 Result which uses `"t3": {...}, "v3": {...}` as keys.
The ad-hoc `agent_t3`/`client_v3` keying creates an unbounded namespace — any
`{party}_{tensor}` combination could appear, with no schema to validate.

**Cross-document check**: R7 §5.5 handles multi-party attribution properly by having a
separate `reputation` object for the agent, with a note "Client reputation also affected
(separate ReputationDelta)." This is the cleaner pattern.

**Proposed fix**: Either (a) restructure to use an array of per-party tensor updates
with explicit party identification:
```json
"tensorUpdates": [
  {"entity": "lct:web4:agent:...", "t3": {"temperament": +0.01}},
  {"entity": "lct:web4:client:...", "v3": {"validity": +0.005}}
]
```
Or (b) add a note that multi-party tensor attribution in R6 is illustrative and that
R7's ReputationDelta per-party model is the preferred pattern for consequential agency
actions.

---

### M3 (MEDIUM) — Overview: "don't merit reputation tracking" vs §1.6 tensorUpdates

**Location**: Line 5 (Overview) vs lines 184, 202-205 (§1.6), lines 316-321 (§2.3)

**Issue**: R6 Overview states R6 is for "routine, low-consequence tasks that **don't
merit reputation tracking**." But R6 §1.6 Result includes `tensorUpdates` (T3/V3
changes), and R6 §2.3 settlement explicitly calls `update_t3_v3_tensors()`. These
are reputation-affecting operations.

**Cross-document check**: R7 §1.7 clarifies: "In R6, tensor updates were buried in the
Result." This acknowledges R6 does update tensors — just not as first-class tracked
reputation. The distinction is:
- R6: tensor deltas applied directly during settlement (simple, untracked)
- R7: tensor deltas computed as a ReputationDelta (first-class, role-contextualized,
  witnessed, attributed, ledger-recorded)

**Resolution**: The tension is **consistent but imprecisely worded**. R6 does update
tensors; it just doesn't produce the full reputation machinery that R7 adds. "Don't
merit reputation tracking" should be qualified.

**Proposed fix**: Change Overview line 5 from:
> "routine, low-consequence tasks that don't merit reputation tracking"

To:
> "routine, low-consequence tasks that don't merit explicit, first-class reputation
> tracking"

Or:
> "routine, low-consequence tasks where implicit tensor updates in the Result suffice
> (see §1.6) — without the full reputation attribution that R7 provides"

---

### M4 (MEDIUM) — Missing `## References` section

**Location**: End of file (absent)

**Issue**: R6 spec has no `## References` section cross-linking to sibling specs. The
only cross-reference is an inline link to `r7-framework.md` on line 7.

C-series audits established a pattern of adding References sections:
- C10 (M3): added cross-reference to `t3-v3-tensors.md` in mrh-tensors.md §5
- C11 (M4): added `## References` section to atp-adp-cycle.md

R6 references concepts from multiple sibling specs without linking:
- ATP/ADP tokens (atp-adp-cycle.md) — §1.5 Resource, §2.3 Settlement
- T3/V3 tensors (t3-v3-tensors.md) — §1.6 Result, §2.3 Settlement
- MRH graph (mrh-tensors.md) — §1.2 Role, §1.4 Reference
- Law Oracle / SAL (SOCIETY_SPECIFICATION.md) — §1.1 Rules, §3
- Society roles (society-roles.md) — §1.2 Role

**Proposed fix**: Add a `## References` section before or after §9 Summary, listing:
- `r7-framework.md` — R7 superset with reputation tracking
- `atp-adp-cycle.md` — ATP/ADP token lifecycle and value mechanics
- `t3-v3-tensors.md` — T3 (Trust) and V3 (Value) tensor definitions
- `mrh-tensors.md` — Markov Relevancy Horizon graph structure
- `society-roles.md` — Role definitions and tier structure
- `SOCIETY_SPECIFICATION.md` — Society-Authority-Law (SAL) governance

---

### M5 (MEDIUM) — §4.1 / §6 MUST-3: overstrong "determinism" claim

**Location**: Line 354 (§4.1), line 491 (§6 MUST-3)

**Issue**: R6 §4.1 asserts: "Given the same R6 inputs, the result must be identical
across all valid implementations." §6 MUST-3 repeats: "Results MUST be deterministic
given inputs."

For R6 actions involving external systems — compute tasks (§5.3: GPU training),
network calls, external service quotas (§1.5) — the raw execution result depends on
external factors (hardware differences, network state, nondeterministic algorithms).
True determinism of the *Result* is not achievable for these action types.

**Cross-document check**: The R7 spec copies the same claim verbatim at §4.1. This
is a shared issue across R6/R7.

**What IS deterministic**: The R6 framework's *processing* of results — validation
logic, settlement calculation, tensor update application, escrow release — is
deterministic. Given the same action definition and the same raw execution output,
the settlement and tensor updates will be identical.

**Proposed fix**: Qualify §4.1:
> "Given the same R6 inputs **and execution outcome**, the settlement (resource
> accounting, tensor updates, ledger entry) must be identical across all valid
> implementations. The determinism guarantee applies to the R6 framework's processing,
> not to the underlying action execution which may depend on external factors."

Update §6 MUST-3 similarly.

---

### M6 (MEDIUM) — §7 error hierarchy: `R6Error` base class (spec-only)

**Location**: Lines 511-531

**Issue**: R6 §7 defines error classes inheriting from `R6Error`:
```python
class R6Error(Exception): pass
class RuleViolation(R6Error): ...
```

SDK only has `R7Error` as the base class (since it implements R7 exclusively). There
is no `R6Error` class in the SDK.

**Cross-document check**: R7 §7 defines the same hierarchy with `R7Error` base, plus
`ReputationComputationError(R7Error)`. SDK matches R7 exactly.

**Analysis**: Since R7 is a strict superset of R6, implementing only `R7Error` is
correct — all R6 errors are valid R7 errors. A pure R6 implementation would need
`R6Error`, but no such implementation exists.

**Proposed fix**: Add a note to §7: "In implementations that support both R6 and R7,
the error hierarchy may use a shared base class. The SDK uses `R7Error` as the common
base, since R7 is a superset of R6. A pure R6 implementation would define `R6Error`
as shown."

---

### L1 (LOW) — §5.2 Result: undeclared `commitment` field

**Location**: Line 399

**Issue**: R6 §5.2 Trust Query Result includes `"commitment": "must_engage_or_forfeit"`.
This field does not appear in the §1.6 Result structure definition. It is an ad-hoc
field in one transaction example without formal specification.

**Proposed fix**: Either (a) add `commitment` as an optional field in §1.6 Result
(for staked queries that require follow-through), or (b) move it into the `output`
object where application-specific data belongs: `"output": {"commitment": "must_engage_or_forfeit", ...}`.

---

### L2 (LOW) — §2.3 pseudocode: `from` is a Python keyword

**Location**: Lines 306-307

**Issue**: `transfer_atp(from=r6_action.role.actor, to=resource_providers, amount=final_cost)` — `from` is a Python reserved keyword. This pseudocode would not parse.

**Cross-document check**: R7 §2.4 has the same issue at line 483.

**Proposed fix**: Rename to `sender` or `source`:
```python
transfer_atp(sender=r6_action.role.actor, to=resource_providers, amount=final_cost)
```

---

### L3 (LOW) — §2.2 / §7: "error" vs "failure" status distinction undocumented

**Location**: Lines 285-289 (§2.2), line 539 (§7)

**Issue**: R6 uses two distinct Result status values — `"failure"` (§2.2 catch block,
action attempted but failed) and `"error"` (§7, pre-execution error like
ResourceInsufficient) — but never formally defines the distinction between them. SDK
`ActionStatus` has both `FAILURE` and `ERROR` as enum values.

**Analysis**: The implicit distinction is:
- `"failure"`: action was attempted, execution failed (runtime error, output violation)
- `"error"`: pre-execution validation failed (insufficient resources, invalid role)

**Proposed fix**: Add a brief note to §7 or §1.6 Result:
> "R6 distinguishes two non-success statuses: `error` for pre-execution validation
> failures (the action was never attempted), and `failure` for execution-time errors
> (the action was attempted but did not succeed)."

---

### L4 (LOW) — §1.2 Role: `scopeContext` field absent from R7 and SDK

**Location**: Line 62

**Issue**: R6 §1.2 Role includes `"scopeContext": "financial_analysis"` — a free-text
field describing the domain context. R7 §1.2 Role does not include `scopeContext`.
SDK `Role` class does not have a `scope_context` field.

**Analysis**: Same category as the H1 `roleType` issue — R6 Role carries fields that
were dropped in the R7 evolution. `scopeContext` is effectively superseded by the
`roleLCT` which encodes domain-specific context in the LCT identifier itself (R7 §1.2
example: `"roleLCT": "lct:web4:role:analyst_financial_q4:abc123"`).

**Proposed fix**: Remove `scopeContext` from R6 §1.2 to match R7/SDK, or add a note
explaining it was absorbed into the LCT-based role system.

---

## Cross-Document Tension Resolution

### Previously flagged: "R6 Result includes T3/V3 updates" vs "R7 says R6 has no reputation feedback"

**Source**: C11 verification session (120044) flagged: "r6 §1.6 says R6 Result
'includes Tensor updates (T3/V3)' vs r7's 'R6 without reputation feedback' framing."

**Investigation**: Confirmed both statements are accurate and **compatible**:

| Aspect | R6 | R7 |
|--------|----|----|
| Tensor updates | Included in Result (§1.6 line 184) | Extracted to ReputationDelta (§1.7) |
| Settlement | `update_t3_v3_tensors()` (§2.3 line 317) | `apply_t3_v3_updates_to_role_pairing()` (§2.4 line 496) |
| Attribution | None — deltas applied silently | Full: role-contextualized, witnessed, reason, factors |
| Tracking | Not tracked as reputation | First-class output, ledger-recorded |

R7's characterization of R6 as "without reputation feedback" (r7-framework.md line 7)
means "without *explicit, first-class, tracked* reputation" — not "without any tensor
updates." R6 does modify tensors; it just doesn't produce the full reputation machinery.

**Verdict**: Not an inconsistency, but the R6 Overview wording ("don't merit reputation
tracking") is imprecise. Addressed by finding M3 above.

## Severity Summary

| Severity | Count | Findings |
|----------|-------|----------|
| HIGH | 1 | H1 (legacy `roleType` field) |
| MEDIUM | 6 | M1-M6 |
| LOW | 4 | L1-L4 |
| **Total** | **11** | |

## SDK Alignment Note

The SDK `web4/r6.py` implements **R7** (the superset), not pure R6. The module is named
`r6.py` per CLAUDE.md terminology protection (R6 is the protected acronym), but its
primary class is `R7Action`. This means:

1. The R6 spec describes a design (Result with tensorUpdates, R6Error hierarchy) that
   has no direct SDK counterpart — the SDK skips R6 and implements R7 directly.
2. The R6 spec remains valid as the "base grammar" specification — R7 extends it, and
   the R6 spec documents what R7 inherits and what it changes.
3. Any future R6-only implementation would need to implement the R6 spec as written,
   including the R6Error hierarchy and Result-embedded tensorUpdates.

## Deferred Items

- **R7 §4.1 determinism claim**: Same overstrong wording exists in R7 spec. Remediation
  of R6 M5 should be coordinated with the eventual C13 R7 audit to apply consistent
  language.
- **R7 §2.4 `from=` keyword**: Same pseudocode issue as R6 L2. Coordinate fix.
