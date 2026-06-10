# C46: r7-framework.md Delta Re-Audit

**Date**: 2026-06-10
**Auditor**: Autonomous session (legion-web4-20260610-120050), v2 protocol
**Document**: `web4-standard/core-spec/r7-framework.md` (958 lines)
**Prior audit**: `docs/audits/r7-framework-internal-consistency-2026-05-24.md` (labeled C14; 925 lines; 1 HIGH / 5 MEDIUM / 4 LOW). All 10 findings remediated in commit `6d40cc4b` (#234); follow-up `1e2b9727` (#238) renamed undefined `OutputViolation` → `ResultInvalid`. **Never delta-re-audited until now.**
**Method**: refute-by-default multi-agent WORKFLOW — 1 delta-verifier + 6 dimension finders (spec↔SDK structural, spec↔canonical, internal pseudocode, examples/JSON, cross-spec, normative/RFC-2119) → adversarial verification of every raw finding (default REFUTED; CONFIRM only on re-read of live text). 49 agents.
**Authorities**: SDK `web4-standard/implementation/sdk/web4/r6.py` (declared authority — spec converges to SDK); canonical `web4-standard/core-spec/t3-v3-tensors.md` §3.1; sibling `r6-framework.md`; error SSOT `errors.md`.

---

## Summary

| | Count |
|---|---|
| §A C14 findings re-verified | **10/10 HELD, 0 REGRESSED** |
| §B raw findings | 42 |
| §B → CONFIRMED | 17 (incl. positive conformance attestations) |
| §B → DEFLATED | 21 |
| §B → REFUTED | 4 |
| **Distinct actionable defects** | **11** (3 MEDIUM / 7 LOW / 1 INFO) |
| Autonomous-actionable (next remediation) | 9 (+1 partial) |
| DESIGN-Q / cross-track (NOT self-resolve) | 2 |

**Headline**: §A is the **4th consecutive clean delta streak** (after C40/C42/C44) — all 10 C14 findings held with zero structural regression. The single remediation-introduced item (C46-M1) is the established [[feedback_remediation_introduced_regression]] pattern: C14-M3's fix (sourcing `action_id` from the request nonce instead of the not-yet-written ledger txHash) **fixed the real bug but introduced a fresh spec↔SDK provenance divergence** — the SDK sources `action_id` from the R7Action's own composite id (`r7:<hash>`), not the bare nonce. The overcall-discipline deflated 25/42 raw findings, including refuting a finder's claim that C45's `t3_impacts` rename left r7 drifted (a conflation of two distinct identifiers — see Refuted §R4).

---

## §A — C14 Findings Re-Verified (delta)

| C14 | Description | Status | Evidence (current file) |
|-----|-------------|--------|--------------------------|
| **H1** | §5 examples used `roleType` instead of `roleLCT` | **HELD** | §5.1 L599 / §5.2 L624 / §5.3 L666 / §5.4 L732 / §5.5 L775 all use `roleLCT`; grep `roleType` → 0 hits. |
| **M1** | §5 reputation examples omitted `role_lct` | **HELD** | §5.1 L608 / §5.2 L641 / §5.3 L696 / §5.4 L747 / §5.5 L806 all carry `role_lct`. (§7 error block still omits it → new finding C46-M3, an extension beyond C14-M1's §5-only scope.) |
| **M2** | `v3InRole` named `value` not canonical `valuation` | **HELD** | §1.2 L80 / §5.3 L677 use `valuation`; grep confirms no `value` v3 dim (remaining `value` keys are Rules constraints). SDK `valuation` (r6.py L993). |
| **M3** | `action_id` read from `result.ledgerProof.txHash` pre-ledger-write | **HELD** (intent) | §2.3 L423-428 now sources from request nonce; pre-write read gone. **But the chosen source diverges from SDK → C46-M1.** |
| **M4** | status values inconsistent, enum undefined | **HELD** | §1.6 L228-239 normative status table = SDK `ActionStatus` (7 values) exactly; all §2.2/§5/§7 values appear in table. |
| **M5** | determinism asserted unscoped | **HELD** | §4.1 L574, §6 MUST#3 L834, §9 L950, §1.6 L193 all scope to "same inputs **and the same Result**". |
| **L1** | §2.4 used reserved `from=` | **HELD** | §2.4 L511-514 uses `sender=`/`to=`; grep `from=` → 0 hits. |
| **L2** | §1.7 Components list ≠ structure | **HELD** | §1.7 L249-260 components reconcile with L263-298 structure; no orphan. |
| **L3** | SAL "Auditor can adjust Result" tension | **HELD** | §3 L568 reworded: corrections are a *new* corrective R7 action, original Result immutable per §4.2. |
| **L4** | §4.5 atomic vs non-transactional flow | **HELD** | §4.5 L585-586 reconciles: logical sequence shown, atomic boundary stated. |

**Regression sweep (#234/#238)**: grep over the whole file (incl. all JSON examples + §7) for residual `OutputViolation`, `roleType`, `from=`, and `value`-as-v3-dim → all clean. One semantic regression surfaced (C46-M1, below); two INFO non-defects recorded (cross-doc vocab drift, Rules-constraint key — both pre-existing, not introduced by the remediation).

---

## §B — Confirmed Defects (actionable)

### C46-M1 (MEDIUM, autonomous) — `action_id` source diverges from the SDK authority *(remediation-introduced regression)*
**Location**: §2.3 L423-428 vs SDK `r6.py` L853 (`compute_reputation`) + L747-750 (`_generate_id`).
C14-M3's remediation set `action_id=r7_action.request.nonce` (L427) with a comment that the ledger txHash is written only later. The SDK sets `action_id=self.action_id` (L853), where `self.action_id` is **not** the bare nonce — it is the R7Action's own composite id `r7:{sha256(actor:action:nonce:timestamp)[:16]}` (L747-750). These are structurally different values; an implementer following §2.3 would populate a value that does not match the SDK-authoritative action↔reputation linkage id. (The `txn:0x...` form in the §1.7/§5/§7 JSON examples is a third placeholder, a weaker coupled inconsistency.)
**Fix**: change §2.3 L427 to `action_id=r7_action.action_id` and update the L423-426 comment to refer to the R7Action's pre-assigned composite id (not "the request nonce"). Optional coupled cleanup: reconcile the `txn:0x...` example placeholders toward the `r7:...` form. *Spec converges to SDK — no operator decision needed.*

### C46-M2 (MEDIUM, autonomous) — §1.6 Result attestation keyed `witness`, everywhere else `lct`
**Location**: §1.6 L217 vs §1.4 L149, §1.7 L292, SDK `WitnessAttestation.to_dict` L380 / `from_dict` L390.
§1.6 shows `{"witness": "lct:web4:...", ...}`. Both sibling spec attestation blocks (§1.4, §1.7) and the SDK `WitnessAttestation` use `lct` (the SDK's `Result.attestations` round-trips through exactly this key; a literal §1.6 doc would KeyError on strict `from_dict` or deserialize an empty `lct`). §1.6 is the lone outlier.
**Fix**: §1.6 L217 `"witness"` → `"lct"` (single-token edit).

### C46-M3 (MEDIUM, autonomous) — §7 error reputation block omits `role_lct` *(extends C14-M1 beyond §5)*
**Location**: §7 reputation block L904-916 (no `role_lct` between L905 `subject_lct` and L906 `action_id`).
Every other reputation example (§5.1/5.2/5.3/5.4/5.5) and the §1.7 structure (L267) include `role_lct`. §1.7 L251 bolds **Role LCT** as a required component and L247 states "There is no global reputation—only reputation within specific role contexts." A role-less reputation delta is precisely the global reputation the spec forbids. SDK `ReputationDelta.role_lct` is a non-default required field (r6.py L590), always serialized — the §7 example could not be produced by the SDK. (C14-M1 scoped only §5.1/5.2/5.4/5.5, so §7 was out of its blast radius — this is the residual.)
**Fix**: add one line `"role_lct": "lct:web4:role:...",` after L905.

### C46-M4 (MEDIUM, **DESIGN-Q — do NOT self-resolve**) — `role_pairing_in_mrh` is a first-class spec component absent from SDK `ReputationDelta` *(= carry-C44 B-I7)*
**Location**: §1.7 L268-273 (structure) + §2.3 L420 (constructor kwarg) + §2.4 L529 (`reputation.role_pairing_in_mrh.mrh_link`) + §5.3 L697-702; SDK `ReputationDelta` L589-600 (no such field; `to_dict`/`to_jsonld`/`from_jsonld` neither emit nor read it; grep → 0).
**Confirmed real** (this is the carry-C44 B-I7 item explicitly deferred to the r7 audit). Verifiers split on severity/actionability precisely because it is a genuine design question, **not** a mechanical convergence: the field is woven into the Critical Design Principle (L247) and the §2.4 pseudocode functionally consumes `.mrh_link` to locate the MRH role pairing for tensor updates. Two resolutions:
- **(a) Strip spec → SDK** (spec-converges-to-SDK rule): drop the `role_pairing_in_mrh` object from §1.7/§5.3, rewrite §2.3/§2.4 to use scalar `role_lct` + resolve `mrh_link` via the existing `get_mrh_role_pairing` helper (L413). `role_lct` already carries the role context.
- **(b) Enrich SDK**: add `role_pairing_in_mrh` to the SDK `ReputationDelta` (SDK change).
**Operator decides which side is authoritative for role-pairing representation.** Mitigant: the design intent is **not lost** under (a) — `subject_lct`/`role_lct` duplicate the object's entity/role sub-fields and the SDK docstring (L585-586) already states reputation is role-pairing-contextualized. Recommend **(a)** as the lower-risk default consistent with the C-series convergence rule, but flag for operator since it changes a documented mechanism.

### C46-L1 (LOW, autonomous) — `Resource.pricing` shown in §1.5 + dereferenced in §2.4, absent from SDK
**Location**: §1.5 L180-183, §2.4 L506 (`r7_action.resource.pricing`); SDK `ResourceRequirements` L437-481 (no `pricing`; grep → 0).
**Fix**: remove the `pricing` block from §1.5 and the `pricing` arg from §2.4, or annotate `pricing` as a deferred extension not modeled by SDK `ResourceRequirements`.

### C46-L2 (LOW, autonomous) — §1.4 Reference `interpretations` + `trustPaths` have no SDK counterpart
**Location**: §1.4 L143 (`trustPaths` in `mrhContext`), L145-147 (`interpretations`); SDK `Reference` L398-431 (only precedents/mrh_depth/relevant_entities/witnesses; grep → 0).
`interpretations` has thematic support (L130 "Law Oracle interpretations" source bullet; L566 "Oracle rulings cached"), so it reads as intended-but-unimplemented. **Fix**: align §1.4 example to the SDK Reference shape — drop `trustPaths`, and either remove `interpretations` or annotate it deferred.

### C46-L3 (LOW, autonomous) — `Result.ledgerProof` shown in §1.6/§5.4, absent from SDK Result
**Location**: §1.6 L200 + L219-223, §5.4 L743; SDK `Result` L487-538 (no `ledgerProof`; grep → 0).
The spec's own §2.3 comment (L423-426) already states the resolution: the ledger entry is written only later in settlement and the txHash recorded separately on write. The defect is that §1.6/§5.4 present `ledgerProof` as a Result component without that qualification. **Fix**: annotate §1.6/§5.4 that `ledgerProof` is settlement-recorded-separately (not part of the SDK Result serialization, consistent with the §2.3 note), or remove it from the Result component list.

### C46-L4 (LOW, autonomous) — §2.3/§2.4 pseudocode uses attribute `.roleLCT` (SDK attribute is `.role_lct`)
**Location**: §2.3 L410 (`role_lct = r7_action.role.roleLCT`), §2.4 L528, L543; SDK `Role` L234 (attribute `role_lct`; `roleLCT` is only the to_dict serialization KEY, L243).
Internally inconsistent: the adjacent L409 correctly uses `r7_action.role.actor` (SDK snake_case attribute), proving this is attribute access — so `.roleLCT` would AttributeError. **Fix**: change the three `.roleLCT` accesses to `.role_lct`.

### C46-L5 (LOW, autonomous) — role-id `_2025` segment inconsistency within the running analyst example
**Location**: §1.2 L70 (`lct:web4:role:analyst_financial_q4:abc123`) vs §1.7 L267/L270 (`...analyst_financial_q4_2025:abc123`).
Same actor (`lct:web4:entity:alice`), same `abc123` suffix, same `pairedAt` timestamp → same pairing, but the role-id strings differ by the inserted `_2025`. Free-form ids are valid (L63), so this is a pure within-file harmonization slip. **Fix**: pick one rendering and align the three occurrences.

### C46-L6 (LOW; 3 autonomous renames + 2 DESIGN-Q) — §2.1 raises 5 exception names absent from the §7 catalog
**Location**: §2.1 L319/324/326/334/338 vs §7 L861-880; SDK `r6.py` L90-119.
`InvalidRole`/`InvalidReference`/`InsufficientResources` are word-transposed deviations of the canonical §7+SDK `RoleUnauthorized`/`ReferenceInvalid`/`ResourceInsufficient` (`RuleViolation` is the only exact match). **Autonomous fix**: rename those three to catalog spelling.
- **DESIGN-Q sub-item**: `InvalidAgency` and `AgencyScopeViolation` have **no** §7 catalog entry and **no** SDK error class. Folding them under an existing entry, or adding new R7Error subclasses, is an operator/SDK taxonomy decision (adding to spec would diverge from the SDK, which deliberately has no agency error). **Same gap exists verbatim in sibling `r6-framework.md` L235/L237** — resolve as a paired r6+r7 decision.

### C46-I1 (INFO, autonomous) — §7 error handling has no cross-link to the `errors.md` SSOT
**Location**: §7 L856-918; cross-ref `errors.md` §1 L9.
Not a contradiction: R7 result-level errors are SDK/framework exceptions, categorically distinct from the RFC-9457 `W4_ERR_*` core-protocol taxonomy (so `errors.md`'s anti-parallel-naming rule is not violated). Pure documentation hygiene. **Fix**: add one clarifying sentence in §7, e.g. "R7 result-level errors are SDK exceptions distinct from the RFC-9457 protocol error taxonomy in `errors.md`."

### C46-I2 (INFO, no action) — positive conformance attestations (recorded clean)
Re-verified clean, nothing to remediate: (a) all T3/V3 tensor dimension names canonical across §1.2/§1.7/§5/§7; (b) terminology protection holds (R6/R7/T3/V3/MRH/ATP not redefined; `web4:Surgeon` IRI matches t3-v3 convention); (c) ATP/ADP claims (L7, L16) consistent with `atp-adp-cycle.md` §2.3; (d) "in R6 tensor updates were buried in the Result" (L245) accurate against current `r6-framework.md` §1.6 (`tensorUpdates`); (e) §1.6 status table ↔ §2.2 failure/error branches ↔ SDK `ActionStatus` mutually consistent; (f) all example `net_trust_change`/`net_value_change` sums arithmetically match their shown deltas (every block checked); (g) mixed snake_case (reputation) / camelCase (role) is deliberate SDK-parity.

---

## §B — Notable Deflations & Refutations (overcall-discipline)

- **DEFLATED — leading-`+` JSON numbers** (e.g. `"change": +0.01`): not RFC-8259-well-formed, but an accepted corpus-wide illustrative shorthand (mirrored in `reputation-computation.md`, survived C45) denoting delta direction. Cosmetic; optional one-line "illustrative" note.
- **DEFLATED — MUST#6 "reputation MUST be computed"** alleged stricter than SDK's `Optional[ReputationDelta]`: REFUTED on merits — MUST#6 is the *defining* R6/R7 distinction; the SDK `Optional`/`if self.reputation` is a pre-computation lifecycle artifact (`compute_reputation()` sets it), not evidence a completed R7 action may omit reputation. No change warranted.
- **DEFLATED — RFC-2119 lowercase "must" in §1.2/§4.x**: a deliberate two-tier convention (descriptive §1/§4 narrative vs formal §6 MUST/SHOULD/MAY), **byte-identical in sibling r6-framework.md** — fixing r7 alone would *create* cross-doc divergence. Convention decision spanning both specs, not an r7 defect.
- **DEFLATED — MUST#2 "all seven components present" vs §7 Error-Result example** (only `result`+`reputation`): §7 is explicitly the *output* side (L240); MUST#2's wording is unconditional but the example is coherent with its own framing. Minor clarity nit, not HIGH.
- **REFUTED (R4) — "C45 `t3_impacts` rename left r7 drifted"**: finder conflation. `reputation-computation.md` **still** uses `t3_changes`/`v3_changes` local accumulators (L347/L364) identical to r7 §2.3; C45 renamed a *different* identifier — the rule-structure impact fields `rule.t3_impacts`/`rule.v3_impacts`. No drift exists.
- **REFUTED — three "no defect" clean-check records** (net-sum arithmetic, status-value coverage, var-binding consistency): all verified clean.

---

## §C — Cross-spec record-only (out of r7 scope; for sibling specs' own cycles)

1. **`r6-framework.md` uses non-canonical `value` in `v3InRole`** (L70) — r7 is the *correct* side (`valuation`). Flag for r6's next audit/remediation. *(This is r6's residual of the same class as C14-M2.)*
2. **`r6-framework.md` §2.2 routes unhandled exception → `failure`; r7 §2.2 → `error`** — genuine cross-spec routing divergence; r7 self-documents its split (L240) and is the more granular SDK-aligned model. Fix belongs in r6 (or operator decision on canonical routing).
3. **`r6-framework.md` shares the §2.1 exception-name drift + agency-exception gap** (C46-L6) — resolve as paired r6+r7.
4. **Rules constraint `{"type","value"}` vs SDK `Constraint` `{"type","threshold","hard"}`** — pre-existing (traces to commit `41f190f0`, predates #234/#238), corpus-wide (identical in r6). SDK `from_dict` accepts `value` as documented legacy alias, so it round-trips. The `rate_limit: "100/hour"` string value vs SDK float `threshold` is an SDK-shape question (string vs numeric threshold), not a clean prose fix. Paired r6+r7 INFO when the SDK threshold-type question is resolved.

---

## Disposition for the next remediation turn (C47)

**Autonomous-actionable (9 + 1 partial)** — apply in r7-framework.md prose alone, spec-converges-to-SDK:
C46-M1 (action_id → `.action_id`), C46-M2 (`witness`→`lct`), C46-M3 (add `role_lct` to §7), C46-L1 (pricing), C46-L2 (interpretations/trustPaths), C46-L3 (ledgerProof annotate), C46-L4 (`.roleLCT`→`.role_lct` ×3), C46-L5 (`_2025` harmonize), C46-L6-partial (rename 3 exceptions to catalog spelling), C46-I1 (errors.md cross-link note).

**DESIGN-Q / cross-track — do NOT self-resolve:**
- **C46-M4** = carry-C44 **B-I7** `role_pairing_in_mrh` (operator: strip-spec [recommended] vs enrich-SDK).
- **C46-L6 agency** (`InvalidAgency`/`AgencyScopeViolation`) — no §7/SDK error class; paired r6+r7 + SDK taxonomy decision.

**Cross-spec carries** (§C above) → surface at r6-framework.md's next cycle.
