# C48 — Delta Re-Audit: `r6-framework.md` (prior **C12**)

**Audit ID**: C48
**Target**: `web4-standard/core-spec/r6-framework.md` (605 lines; canonical R6 Action Framework spec)
**Date**: 2026-06-10
**Auditor**: autonomous web4 session (legion, slot `200643`), v2 protocol — **LEAD voice**
**Type**: Delta re-audit (regression pass §A + refute-by-default new-findings pass §B)
**Prior coverage**: **C12** `r6-framework-internal-consistency-2026-05-24.md` (11 findings: 1H/6M/4L), remediated in **PR #231** (`06300ca1`). Two later PRs also touched the file: **#235** (`b480fcf2`, SAL Result row §3 + §4.5 atomic-settlement sync) and **#238** (`1e2b9727`, `OutputViolation`→`ResultInvalid` in §2.2).

**Method**: executed as a multi-agent refute-by-default **workflow** per `feedback_audit_workflow_adversarial_verify.md`. §A = one regression agent (11 C12 verdicts + #235/#238 remediation-introduced-regression check, cross-checked vs SDK `web4/r6.py`). §B = **5 parallel lens-finders** (internal-consistency / cross-spec vs `r7-framework.md` / cross-spec vs SDK `r6.py` + conformance vectors / error-taxonomy + identifier-form / altitude-placement), each candidate finding routed to an **adversarial verifier instructed to refute by default**. **53 agents total. 47 raw candidates → 45 surviving / 2 fully refuted**; the adversarial pass moderated severity downward on ~12 survivors (MEDIUM→LOW, LOW→INFO) and corrected routings. After **cross-lens de-duplication** (all five lenses independently surfaced the `v3InRole.value`, error-name-drift, and constraint-shape items), the **13 distinct findings** are consolidated below.

This is the exact structural parallel of **C46** (the r7 delta re-audit just completed): r6-framework.md and r7-framework.md are sibling specs, and several C48 findings are the **r6-side confirmation of the cross-spec carries C46 explicitly parked for "r6's next audit."**

---

## Headline Result

- **§A: ALL 11 C12 findings HELD. Zero PARTIAL, zero STILL-OPEN, zero REGRESSED.** PR #231's remediation is fully intact and still correct vs the current SDK. **Zero regressions** from #235/#238 — the **5th consecutive clean §A streak** (after C40/C42/C44/C46), and a clean [[feedback_remediation_introduced_regression]] result on two non-C12 PRs that touched the file.
- **§B: zero HIGH, zero normative contradictions, zero conformance-vector violations.** The R6 spec's `{success/failure/error}` status model, R6Error hierarchy, and six-component grammar all match the SDK and vectors. The substantive findings are **cross-spec wire-key/naming drift vs r7+SDK** (most of it the r6-mirror of what #309 just fixed in r7) plus hygiene.
- **Distinct actionable**: **3 MEDIUM + 4 LOW** (7 autonomous-fixable), **3 DESIGN-Q** (operator), **3 CROSS-TRACK** (fix lands in r7/SSOT), plus INFO confirmations.

---

## §A — Regression Pass (C12 + #235/#238)

| C12 ID | Verdict | Evidence (summary) |
|--------|---------|--------------------|
| **H1** | **HELD** | §1.2 Role (L56-73) no longer carries `roleType`/`scopeContext`; only `actor`/`roleLCT`/`pairedAt`/`t3InRole`/`v3InRole` — matches SDK `Role` (`r6.py` actor/role_lct/paired_at/t3_in_role/v3_in_role) and r7. |
| **M1** | **HELD** | `v3InRole` block present (L67-71); §1.6 V3 deltas now have a documented baseline. |
| **M2** | **HELD** | §5.5 `tensorUpdates` restructured to per-entity array w/ standard `t3`/`v3` keys (L481-484) + explanatory note L489. |
| **M3** | **HELD** | Overview L5 qualified to "don't merit *explicit, first-class* reputation tracking" + parenthetical on implicit tensorUpdates. |
| **M4** | **HELD** | §10 References (L597-604) cross-links all six siblings. |
| **M5** | **HELD** | §4.1 (L358-359), §6 MUST-3 (L496), §9 (L589) all qualified with "and execution outcome." Consistent across the three sites. |
| **M6** | **HELD** | §7 retains R6Error hierarchy + SDK note (L543) explaining the R7Error shared-base rationale. |
| **L1** | **HELD** | §5.2 `commitment` moved inside `output` (L403). |
| **L2** | **HELD** | §2.3 `from=`→`sender=` (L311); pseudocode now parses. |
| **L3** | **HELD** | §7 (L515-517) formally distinguishes `error` (pre-exec) vs `failure` (exec-time); aligns SDK `ActionStatus`. |
| **L4** | **HELD** | `scopeContext` absent from §1.2; SDK has no `scope_context`. |

**Remediation-introduced-regression check (the load-bearing §A novelty)** — **NO new defects**:
- **#235**: §3 SAL "Result" row (L354) "corrections are issued as a *new* corrective R6 action — the original Result stays immutable per §4.2" — the §4.2 cross-ref is accurate (§4.2 = Non-repudiation, L361-362). §4.5 atomic-settlement (L370-371) correctly cites **§2.3** (R6's settlement, not r7's §2.4) and lists R6's actual steps, deliberately omitting reputation computation R6 lacks. Both cross-refs and the step list match the §2.3 pseudocode. **Clean.**
- **#238**: §2.2 L276 `OutputViolation`→`ResultInvalid`; `ResultInvalid` is defined in §7 (L539) + SDK (`r6.py:114`), is an `Exception` subclass so the §2.2 `except` still catches it → `status="failure"` (consistent with the L3 exec-time→failure rule). Grep confirms `OutputViolation` fully eliminated; no dangling ref. **Clean.**

---

## §B — Findings Summary

| ID | Sev | Routing | One-line |
|----|-----|---------|----------|
| **C48-M1** | MED | AUTONOMOUS | ⭐ §1.2 `v3InRole.value` (L70) uses non-canonical `value`; r7 + SDK + Terminology-Protection canonical = **`valuation`** (5-lens consensus; = carry-C46 §C #1) |
| **C48-M2** | MED | AUTONOMOUS | §1.6 Result attestation keyed `"witness"` (L212) while r6's own §1.4 (L139), r7 §1.6, and SDK use `"lct"` — exact r6-mirror of **C46-M2** (fixed in r7 #309) |
| **C48-M3** | MED | AUTONOMOUS | §2.1 pseudocode raises `InvalidRole`/`InsufficientResources`/`InvalidReference` (L230/245/249) — §7 catalog + SDK spell these `RoleUnauthorized`/`ResourceInsufficient`/`ReferenceInvalid`; r6-mirror of the r7 §2.1 drift fixed in #309 |
| **C48-L1** | LOW | AUTONOMOUS | §1.6 example `tensorUpdates.v3` has `"validity": 1.0` (L209) — an absolute value masquerading as a delta among `+0.01`/`+0.02` deltas |
| **C48-L2** | LOW | AUTONOMOUS | §4.1 Determinism wording (L358-359) diverges from r7 §4.1 phrasing — harmonize the two siblings' identical guarantee |
| **C48-L3** | LOW | AUTONOMOUS | §1.6 single-party `tensorUpdates` object vs §5.5 multi-party array: add a one-line forward-pointer from §1.6 to the §5.5 multi-party form (the §5.5 L489 note already explains the asymmetry) |
| **C48-L4** | LOW | record | Mixed camelCase (`roleLCT`, `atpStake`) / snake_case (`atp_balance`, `cpu_seconds`) JSON casing across §1.x/§5.x — corpus-wide, partly intentional (mirrors SDK `to_dict`); record, do not churn |
| **C48-DQ-agency** | MED | DESIGN-Q | §2.1 `InvalidAgency`/`AgencyScopeViolation` (L235/237) have **no §7 catalog entry and no SDK error class** — identical verbatim in r7 §2.1 (L324/326). = **carry-C46-agency**; paired r6+r7+SDK taxonomy decision |
| **C48-DQ-errors** | MED | DESIGN-Q | §7's Python-class error model (`R6Error`/…) has no link to the canonical `errors.md` `W4_ERR_*` / RFC-9457 taxonomy — ownership/canonicity gap. Folds into **carry-C30** error-canonicity |
| **C48-DQ-constraint** | LOW | DESIGN-Q | §1.1 Rules constraint `{type, value}` w/ string `"100/hour"` (L37) vs SDK `Constraint{type, threshold:float, hard}`. SDK `from_dict` **accepts `value` as a legacy alias** (so the *key* is not a defect), but `"100/hour"` is non-loadable as `threshold:float`; constraint-type names `atp_minimum`/`witness_required` also differ from SDK docstring `min_atp`/`witness_quorum`. SDK-shape Q (= carry-C46 §C #4) |
| **C48-CT-failure** | LOW | CROSS-TRACK | §2.2 `except → status="failure"` (L288-294) is **correct per r6's own §7** (exec-time = failure); r7's analogous handler routes to `status="error"`. Divergence is real but **r6 is the correct side** — reconciliation lands in r7 (= carry-C46 §C #2, re-pointed) |
| **C48-CT-id** | LOW | CROSS-TRACK | Identifier schemes `resource:web4:<type>:<id>` (L93), `mcp:web4://tool/*` (L108), `agy:` (L106/453) undefined in the `data-formats.md` identifier SSOT — folds into the unified-identifier carry |
| **C48-CT-vectors** | INFO | CROSS-TRACK | Conformance vectors (`r6-r7-actions.json`) use a flat dialect (`actor_lct`, `required_atp`, `constraint_type`) distinct from the spec's nested JSON examples — forward-awareness, known, no contradiction |

**13 distinct** (3M/4L actionable + 3 DESIGN-Q + 3 CROSS-TRACK incl. 1 INFO), **+ INFO confirmations** below. **2 fully refuted** (§D).

---

## §B Detail — Actionable (AUTONOMOUS)

### C48-M1 (MEDIUM, AUTONOMOUS) — ⭐ §1.2 `v3InRole.value` → `valuation`

§1.2 Role `v3InRole` (L67-71) is `{"veracity": 0.92, "validity": 0.88, "value": 0.85}`. The canonical V3 third dimension is **Valuation** (CLAUDE.md Terminology Protection: "V3 | Valuation/Veracity/Validity"). r7-framework.md §1.2 and SDK `Role.v3_in_role` use **`valuation`**, and the C-series already renamed `value`→`valuation` in `reputation-computation.md` (C44/C45), `atp-adp-cycle.md` (C34-M1), and `mcp-protocol.md` (C35-N3). r6 is the last `v3InRole` holdout. **All 5 lenses surfaced this independently.** Fix: `value`→`valuation` at L70 (and verify §5.2 `t3InRole`/any V3 example).
- *Severity*: kept MEDIUM — it is a Terminology-Protected canonical-vocabulary divergence, not mere wording.

### C48-M2 (MEDIUM, AUTONOMOUS) — §1.6 attestation key `witness` → `lct`

§1.6 Result `attestations` (L211-213) is `[{"witness": "lct:web4:...", "signature": ..., "timestamp": ...}]`. But r6's **own** §1.4 Reference `witnesses` (L138-140) keys the same concept `{"lct": "lct:web4:witness:...", "attestation": ..., "timestamp": ...}`, and r7 §1.6 + the SDK use `lct`. This is the **exact r6-mirror of C46-M2**, which #309 just fixed in r7 (attestation `"witness"`→`"lct"`). Fix: rename the §1.6 attestation key `witness`→`lct` (L212).

### C48-M3 (MEDIUM, AUTONOMOUS) — §2.1 error-name drift vs §7 catalog + SDK

§2.1 `validate_r6_action` raises `InvalidRole` (L230), `InsufficientResources` (L245), `InvalidReference` (L249). The §7 Error Categories catalog (L520-541) and the SDK `R7Error` hierarchy (`r6.py` `RuleViolation`/`RoleUnauthorized`/`RequestMalformed`/`ReferenceInvalid`/`ResourceInsufficient`/`ResultInvalid`) spell these **`RoleUnauthorized`/`ResourceInsufficient`/`ReferenceInvalid`**. Only `RuleViolation` (L241) and `ResultInvalid` (§2.2 L276) already match. This is the **r6-mirror of the r7 §2.1 drift** #309 fixed (C46-L6-partial). Fix: rename the three §2.1 raises to the §7/SDK catalog spelling. (The two **agency** raises are separately a DESIGN-Q — see C48-DQ-agency.)

### C48-L1 (LOW, AUTONOMOUS) — §1.6 `validity: 1.0` is an absolute value as a delta

§1.6 example `"tensorUpdates": {"t3": {"training": +0.01}, "v3": {"veracity": +0.02, "validity": 1.0}}` (L207-210). `+0.01`/`+0.02` are clearly deltas; `validity: 1.0` reads as an absolute (a full 1.0 delta is implausible and inconsistent with the others). Fix: make it a delta (e.g. `+0.0` / a small positive) or drop it from the illustrative update.

### C48-L2 (LOW, AUTONOMOUS) — §4.1 Determinism wording diverges from r7

r6 §4.1 (L358-359, the post-C12-M5 qualified form) and r7 §4.1 state the same determinism guarantee with different phrasing on `resourceConsumed` nondeterminism. Harmonize the wording so the two siblings read identically (r6's qualified form is the stronger base; align r7 to it at r7's next pass if they diverge).

### C48-L3 (LOW, AUTONOMOUS) — §1.6 object vs §5.5 array `tensorUpdates`

§1.6 single-party `tensorUpdates` is an object `{"t3":…,"v3":…}` (L207); §5.5 multi-party is an array of per-entity objects (L481-484). This is **intentional** (C12-M2 made §5.5 an array for multi-party attribution; L489 note explains it), so not a defect — but §1.6 gives no forward-pointer. Fix: one line in §1.6 noting multi-party actions use the per-entity array form of §5.5.

### C48-L4 (LOW, record) — mixed JSON casing

Top-level camelCase (`roleLCT` L60, `atpStake` L103) vs nested snake_case (`atp_balance` L168, `atp_per_compute` L170, `cpu_seconds` L205). Corpus-wide and partly mirrors SDK `to_dict` output; **record, do not churn** — a casing normalization is a corpus-wide DESIGN-Q, not an r6-local fix. (DEFLATED from a finder's LOW-defect framing.)

---

## §B Detail — DESIGN-Q (operator; recorded, not resolved)

### C48-DQ-agency (MEDIUM, DESIGN-Q) — `InvalidAgency`/`AgencyScopeViolation` have no home (= carry-C46-agency)

§2.1 raises `InvalidAgency` (L235) and `AgencyScopeViolation` (L237) in the agency-delegation branch. Neither exists in the §7 catalog nor in the SDK `R7Error` hierarchy. **Identical verbatim in r7 §2.1 (L324/326).** Adding them to the spec §7 catalog would **diverge from the SDK** (which has no agency error class); folding agency failures into existing classes loses semantic specificity. This is a **paired r6+r7 + SDK taxonomy decision** — operator must choose: (a) add `AgencyError`/`AgencyScopeError` to both specs **and** the SDK; or (b) map agency failures onto existing classes (e.g. `RoleUnauthorized`). **Not self-resolved.**

### C48-DQ-errors (MEDIUM, DESIGN-Q) — §7 class model unlinked to `errors.md` SSOT (= carry-C30)

§7's exception-class taxonomy (`R6Error`/`RuleViolation`/…) is a pure Python-class model with no mapping to the canonical `errors.md` `W4_ERR_*` codes / RFC-9457 problem types. The wire-error canonicity gap is the standing **carry-C30** item (error-system canonicity + ownership). Record here; resolve corpus-wide, not r6-locally.

### C48-DQ-constraint (LOW, DESIGN-Q) — constraint shape `{type, value}` vs SDK `{type, threshold, hard}` (= carry-C46 §C #4)

§1.1 constraints (L36-40): `{"type": "rate_limit", "value": "100/hour"}`, `{"type": "atp_minimum", "value": 50}`, `{"type": "witness_required", "value": 3}`. SDK `Constraint` is `{constraint_type, threshold:float, hard:bool}` with `from_dict` **accepting `value` as a legacy alias** — so the `value` **key is not a defect** (honoring the refute-by-default discipline + the policy-review note). The genuine residue: (1) `"100/hour"` is a **string**, non-loadable as `threshold:float`; (2) constraint-type names `atp_minimum`/`witness_required` differ from the SDK docstring examples `min_atp`/`witness_quorum` (which are illustrative, not enumerated). This is an **SDK-shape DESIGN-Q**, not a hard contradiction — operator decides whether the spec examples should be SDK-loadable and whether constraint-type names get a registry.

---

## §B Detail — CROSS-TRACK

### C48-CT-failure (LOW, CROSS-TRACK) — §2.2 `failure` vs r7 `error` (r6 is correct)

§2.2 `except Exception → status="failure"` (L288-291). A finder framed this as contradicting r6's own §7; **REFUTED** (§D) — r6 §7 L517 explicitly lists "runtime error" under `failure`, and §2.2 *is* the execution phase, so `failure` is correct. The real observation is the **cross-spec divergence**: r7's analogous handler routes to `status="error"`. Since r6 is self-consistent and arguably correct, **the reconciliation lands in r7** (carry-C46 §C #2, re-pointed: r7-side, not r6-side). No r6 edit.

### C48-CT-id (LOW, CROSS-TRACK) — non-SSOT identifier schemes

`resource:web4:<type>:<id>` (L93), `mcp:web4://tool/*` (L108), `agy:` grant ids (L106/453/459/480) are used but undefined in `data-formats.md` (the identifier SSOT). Do **not** re-litigate the `lct:web4:` form (folds into the standing unified-identifier carry). Record the resource/tool/agy schemes for the SSOT pass.

### C48-CT-vectors (INFO, CROSS-TRACK) — conformance-vector dialect

`r6-r7-actions.json` uses a flat key dialect (`actor_lct`, `required_atp`, `constraint_type`) distinct from the spec's nested JSON. Known, intentional (vectors are a wire dialect), **no contradiction** — forward-awareness only.

---

## INFO — Positive Confirmations (bounding coverage)

- ✅ **§7 R6Error hierarchy matches SDK exactly** (`RuleViolation`/`RoleUnauthorized`/`RequestMalformed`/`ReferenceInvalid`/`ResourceInsufficient`/`ResultInvalid`) — minus `ReputationComputationError` (R7-only, correct).
- ✅ **Overview R6/R7 "both canonical, neither deprecated" framing** is mutually consistent with r7's Overview and with §5/§9.
- ✅ **§3 SAL Result row + §4.5** (post-#235) cross-refs accurate, no regression.
- ✅ **2025 timestamps + `_q4` role-id** are illustrative and mirror r7 — no drift.
- ✅ **hash placeholders** (`sha256:`, `0x…`, `hash:`) conventional and consistent.
- ✅ **§6 MUST/SHOULD/MAY** consistent with prose; MUST-4 (failed actions produce valid results) aligns with §7.
- ℹ️ §5.2 `output.commitment` and §7 error-result `refund` are example-only fields not enumerated in the §1.6 Result definition — minor; could be annotated as optional application/settlement fields (LOW/INFO, AUTONOMOUS if a future pass wants to close it).

---

## §D — Refuted Candidates (recorded to prevent re-litigation)

1. **"§2.2 maps all exceptions to `failure`, contradicting r6's own §7."** **REFUTED** — r6 §7 L517 defines `failure` as "Execution-time errors … (e.g., **runtime error**, output constraint violation)"; §2.2 is the execution phase, so routing its exceptions to `failure` is **correct per r6's own definition**. The only legitimate residue is the *cross-spec* divergence from r7 (where r6 is the correct side) — preserved as **C48-CT-failure**.
2. **"§9 Summary omits R7/reputation while the Overview foregrounds it."** **REFUTED** — §9 is the R6 spec's closing summary; restating only R6 properties is its job. L595 ("Every Web4 transaction is an R6 action") is true because R7 is a superset of R6 (the finder conceded this). The Overview already establishes the both-canonical framing. No contradiction.

---

## Disposition Ledger (for the C49 remediation turn)

**AUTONOMOUS (fixable inside r6-framework.md, no design decision):**
- **C48-M1**: §1.2 L70 `value`→`valuation` (+ verify any other V3 example).
- **C48-M2**: §1.6 L212 attestation key `witness`→`lct`.
- **C48-M3**: §2.1 L230/245/249 `InvalidRole`/`InsufficientResources`/`InvalidReference`→`RoleUnauthorized`/`ResourceInsufficient`/`ReferenceInvalid`.
- **C48-L1**: §1.6 L209 `validity: 1.0`→a delta (or drop).
- **C48-L2**: §4.1 harmonize Determinism wording with r7.
- **C48-L3**: §1.6 add forward-pointer to the §5.5 multi-party array form.
- *(C48-L4 casing + §5.2/§7 example-only fields = optional; record, low value.)*

**DESIGN-Q (operator canonicity, recorded not resolved):**
- **C48-DQ-agency** (= carry-C46-agency): `InvalidAgency`/`AgencyScopeViolation` taxonomy — paired r6+r7+SDK. **Do not self-resolve.**
- **C48-DQ-errors** (= carry-C30): §7 class model ↔ `errors.md` `W4_ERR_*`/RFC-9457 canonicity.
- **C48-DQ-constraint** (= carry-C46 §C #4): constraint shape / `"100/hour"` string / constraint-type names — SDK-shape Q.

**CROSS-TRACK (fix/verify lands elsewhere):**
- **C48-CT-failure**: r7-side — reconcile r7 §2.2 `error` vs r6's (correct) `failure` at r7's next pass.
- **C48-CT-id**: `resource:web4:`/`mcp:web4://tool/*`/`agy:` → data-formats SSOT pass (unified-identifier carry).

---

*Audit produced under Autonomous Session Protocol v2 — slot `200643`, LEAD voice. Read-only: no spec, SDK, or test-vector files modified this turn. §A 11/11 C12 HELD + 0 regressed (5th clean streak C40/C42/C44/C46/C48). Method: 5-lens multi-agent fan-out + adversarial refute-by-default verification (53 agents; 47 raw → 45 surviving → 2 refuted; ~12 severities moderated downward), per `feedback_audit_workflow_adversarial_verify.md`. Remediation of the AUTONOMOUS findings is the next alternation turn (C49). The C12→C48 r6-framework.md delta cycle confirms the r6-side of the C46 cross-spec carries.*
