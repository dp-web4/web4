# C123: reputation-computation.md — Third Delta Re-Audit

**Date**: 2026-07-01
**Auditor**: Autonomous session (legion-web4-20260701-060036), LEAD
**Document**: `web4-standard/core-spec/reputation-computation.md` (809 lines)
**Lineage**: C13/C15 (internal-consistency, `reputation-computation-internal-consistency-2026-05-25.md`) → **C44** (1st delta, PR #304 `b98f690c`) → **C45** remediation (PR #305 `00803b03`, 13 findings) → **C84** (2nd delta, `docs/audits/C84-reputation-computation-2nd-delta-2026-06-22.md`) → **C85** remediation (PR #376 `15be0743`, all 9 autonomous C84 findings applied) → **C123** (this 3rd delta). File **byte-frozen since C85** (HEAD blob == C85 blob; last commit `15be0743`, 2026-06-22).
**Instrument**: refute-by-default multi-agent finder pass — 1 §A regression verifier (8 C15 + 13 C45 + 9 C85, extended to every edited site's SDK/vector/sister-doc mirror per the C54/C56/C82 remediation-introduced-regression lesson) + 3 §B dimension finders (internal-consistency+schema, SDK-fidelity, canonical-cross-doc+inbound-carry) → hand-verified each headline candidate with a loose grep at the cited line (C64) + git-provenance check → consolidation/dedup.

**Cross-references re-read against the live files at the cited lines**:
- `web4-standard/implementation/sdk/web4/reputation.py` — `ReputationRule.matches` (L90–115), `analyze_factors` (L170–205), `ReputationEngine.evaluate` (L237–330), `ReputationStore.current`/`inactivity_decay`/`effective_reputation` (L410–511). **Unchanged since Apr 2026 (Sprint 38 `759eaefa`)** — same code C84 audited.
- `web4-standard/implementation/sdk/web4/r6.py` — `ReputationDelta` (~L589–610), `Role`, `TensorDelta`. Unchanged since May.
- `web4-standard/test-vectors/reputation/reputation-operations.json` — rep-001..rep-005. Unchanged since Mar.
- `web4-standard/core-spec/t3-v3-tensors.md` §3 (V3 dim defs + ranges), §7.1 (diminishing returns), §10.2 — **C122 (`b2a98f7c`) touched only §10.2 ATP-conservation cell L640; §3/§7.1 byte-unchanged.**
- `web4-standard/core-spec/mcp-protocol.md` §7.3/§7.5 (cross-society reputation envelope) — **C117 (`afab0c43`) touched only §12 MUST #6; §7.3/§7.5 byte-frozen.**
- `web4-standard/core-spec/atp-adp-cycle.md` §7.1/§4.2 — **C119 (`e99b419e`) narrowed §7.1 MUST #6 to entity-level tensor tracking; ATP discharge/cost model (reputation §9 dependency) unaffected.**
- `web4-standard/core-spec/r7-framework.md` §1.7 — parent ReputationDelta record (X-1 intra-society leg). Unchanged since C84.

---

## Summary

| | Count | Notes |
|---|---|---|
| **§A regression** | 8/8 C15 **HELD** + 13/13 C45 **HELD** + 9/9 C85 **HELD**, **0 REGRESSED** | Fifth consecutive clean delta in this lineage (C40 mrh, C42 t3-v3, C44 reputation, C84 reputation, now C123). Every one of the 30 tracked findings holds against the live file, SDK, and vectors. |
| **§B confirmed** | 3 (1 M / 1 L / 1 record) | 0 HIGH. **NEW-1** (MED), **N1** (LOW), **N2** (record). |
| **§B refuted** | 12 | cross-doc/schema overcall discipline held (see §C); includes 3 refuted sibling-churn overcalls. |
| **Autonomous-actionable (→ C124)** | 2 | NEW-1 (spec-only prose alignment), N1 (spec-only clamp parity). |
| **DESIGN-Q / cross-track (route only)** | 3 | X-1 (reputation-schema reshape bundle), X-2 (§10 stale vs mcp §7.5), NEW-1-SDK-face (fail-open-vs-fail-closed is also an SDK-design question), r7-§1.7-stale-factor (sibling-side). |
| **Record-only** | 2 | SDK-6/B-I5 (§6 unimplemented in SDK), N2 (SDK write-back side-effect). |

**Headline**: The C15+C45+C85 layers are fully durable — **fifth clean delta**, 30/30 held, zero regression. The one substantive new finding, **NEW-1**, is a **remediation-introduced spec-vs-SDK conformance defect from C85's own edit** (a [[feedback_remediation_introduced_regression]] catch, the pattern's 8th confirmation in the C-series): C85 added a new "Trigger Condition Semantics" subsection (§4 L283–296) to document SDK-4/SDK-5, and its closing clause makes an unrecognized trigger condition **SHOULD cause the rule not to match (fail-closed)** — the exact opposite of the reference SDK `ReputationRule.matches()`, which silently **ignores** unrecognized keys and still matches (**fail-open**). No prior audit tested this clause: it did not exist pre-C85, and C84's SDK-5 asked only to "add `min_atp_stake` … or note the set open-ended," never to specify fail-closed conformance. The §B own-pass otherwise reaches only trivia (N1 negative-age clamp parity; N2 SDK write-back side-effect), and the inbound-carry surface is **clean** — all three siblings that moved since C84 (mcp/t3-v3/atp-adp) edited sections outside reputation's cross-ref surface, so 6/6 cross-refs re-verify as reinforcing. X-1/X-2 remain open + cross-track (route-only), unchanged since C84.

---

## §A — Regression Check

Three layers re-verified against the live file + SDK + vectors + canonical sister-docs. **Unanimous: 8/8 C15 HELD, 13/13 C45 HELD, 9/9 C85 HELD, 0 REGRESSED, 0 PARTIAL.**

### Layer 1 — the 8 C15 findings

| C15 ID | Sev | Finding (abbrev.) | Status | Live evidence |
|---|---|---|---|---|
| H1 | HIGH | §7 aggregate onto 0.5 baseline | **HELD** | L660 `current_value = 0.5 + (weighted_sum / weight_sum) if weight_sum > 0 else 0.5`; SDK `reputation.py:454` `_clamp(0.5 + aggregated)`. |
| M1 | MED | third V3 dim `valuation` everywhere | **HELD** | §3.3 L202; §1 v3_delta L46; grep `"value"` V3-key = 0 hits. |
| M2 | MED | §6 witness reads `role_lct` | **HELD** | L562 `get_validators_for_role(action.role.role_lct)`. |
| M3 | MED | §5 `action_id` pre-exec | **HELD** | L397 `action.action_id  # pre-execution id, set at request time`. |
| M4 | MED | §5 V3 `from` role-contextualized | **HELD** | L382 `from_value = action.role.v3InRole[dimension]`. |
| L1 | LOW | §5 sets role_lct/type/target/timestamp | **HELD** | L394–408 all present. |
| L2 | LOW | §7 "30-day time constant (≈20.8-day half-life)" | **HELD** | L653. |
| L3 | LOW | §5 example uses a defined §4 rule | **HELD** | §4 L247 defines `successful_analysis_completion`; §5 L509 references it. |

### Layer 2 — the 13 C45 remediations

All HELD with live cites: **B-M1** (§5 L423/L426 `getattr(rule, impacts_attr)`), **B-M2** (§7 decay keyed `(entity_lct, role_lct)` L693/L698–701), **B-L3** (clamp+recompute L369/L383), **B-L4** (`analyze_factors` quality>0.5 L460 — distinct from §4's `quality_threshold` 0.95 trigger L252/L292), **B-L5** (dead normalization removed), **B-L1** (factor `high_accuracy` §4 L260/L273, §5 L463), **B-L2** (§5 example self-consistent), **B-L7** (§1 zero-change validity dropped — v3_delta L44–47 has veracity+valuation only), **B-M3** (§3.2 `### 3.2 Validity (Confirmed Transfer)` L187), **B-I3** (Veracity/Valuation prose canonical L170/L202), **B-L6** (grep `on-chain` = 0), **B-I1** (diminishing-returns cross-ref to t3-v3 §7.1 / vector t3v3-007 L762), **B-I6** (fractional-day age L652/L703).

### Layer 3 — the 9 C85 remediations (verified applied AND accurate)

| C85 ID | Status | Live evidence |
|---|---|---|
| INT-1 | **HELD** | §1 L50 `{"factor": "high_accuracy", "weight": 0.4}` — no `accuracy_threshold_exceeded`. |
| SDK-2 | **HELD** | §5 L473/L480 read boolean `constraints.get('deadline_met'/'early_completion')`; L467–472 documents caller-upstream pre-resolution. |
| SDK-1 | **HELD** | §5 L401 `", ".join(r.rule_id for r in triggered_rules)`; §1 L76 "rule(s) … joined (comma-separated)". |
| INT-2 | **HELD** | §1 L72 `role_pairing_in_mrh … Required: No`. |
| SDK-3 | **HELD** | §5 L490–491 `required_atp`/`atp_consumed`, L493 `required > 0` guard, L497 `round(efficiency * 0.2, 4)`. |
| SDK-4 | **HELD** | §4 L292 "Matches **iff** `output.quality >= threshold`. A missing quality value is treated as `0.0`". |
| SDK-5 | **HELD** | §4 L293 `min_atp_stake` row (**but see NEW-1** — the surrounding subsection's fail-closed clause is the remediation-introduced defect). |
| INT-3 | **HELD** | §7 L725–729 `effective_reputation()` = current + decay, clamped; L731 SDK parity note. |
| B-L2-residual | **HELD** | §5 L531–537 Note block names `rep-001`, temperament +0.0065 vs +0.005. |

### SDK / vector claim re-verification (SDK unchanged since April — all still hold)
`analyze_factors` (quality>0.5→`high_accuracy`/0.4 L182–183; `deadline_met` L186–187; `early_completion` L189–191; resource `required>0` guard + `round(...,4)` L196–202); `ReputationRule.matches` (quality_threshold L104–107 default 0.0; min_atp_stake L110–112); `evaluate()` rule_ids join L312 + reason L321 "rule(s)"; `current()` 0.5 baseline L436/L454; `effective_reputation` L489–510 = `current()+inactivity_decay()`; vector rep-001 factors `[high_accuracy, deadline_met]` (no `early_completion`), v3 `validity:1.0`. All ✓.

### Remediation-introduced-defect sweep — ONE catch (→ §B NEW-1)
The 30 tracked findings introduced no regression at their own edited sites. **But** the C85 *vehicle* for SDK-4/SDK-5 — the newly-added "Trigger Condition Semantics" subsection (§4 L283–296) — carries a normative clause (fail-closed SHOULD) that no prior audit tested and that contradicts the SDK. Recorded as **NEW-1** below. This is the [[feedback_remediation_introduced_regression]] pattern: the fix itself was correct (min_atp_stake documented, quality comparator stated), but its surrounding prose over-reached into a conformance claim the reference impl does not honor.

**Streak**: C40 → C42 → C44 → C84 → C123 all 0-regressed on their tracked findings. The C15 (#237), C45 (#305), and C85 (#376) remediations are durable.

---

## §B — New Findings

### MEDIUM

#### NEW-1 (MED, autonomous spec-only + cross-track SDK-face — C85 remediation-introduced): §4 fail-closed SHOULD contradicts the SDK's fail-OPEN `ReputationRule.matches()`
**Location**: `reputation-computation.md` §4 L295–296: *"Implementations MAY define additional conditions; an unrecognized condition SHOULD cause the rule not to match (fail-closed) rather than be ignored."* vs SDK `implementation/sdk/web4/reputation.py` `ReputationRule.matches()` L90–115.
**Contradiction**: `matches()` inspects exactly four recognized keys (`action_type` L95, `result_status` L99, `quality_threshold` L105, `min_atp_stake` L111) and falls through to `return True` (L115) whenever all recognized checks pass. Any **unrecognized** key in `trigger_conditions` is never inspected and never causes `return False` — it is **silently ignored, and the rule still matches** (fail-OPEN). The spec's new normative SHOULD says implementations SHOULD do the opposite ("cause the rule not to match … rather than be ignored"). A conformant implementation following the spec would reject rules the reference SDK accepts.
**Provenance (net-new, remediation-introduced)**: git-verified — none of the strings `fail-closed` / `unrecognized condition` / `open-ended` / `Trigger Condition Semantics` exist in `15be0743^` (the pre-C85 file); the entire §4 L283–296 subsection is a C85 addition. C84's SDK-5 asked only to "add `min_atp_stake` to `trigger_conditions` (or note the set is open-ended). Direction SDK→spec." — it never specified fail-open/fail-closed conformance. The fail-closed SHOULD is the C85 remediator's own elaboration, untested against `matches()`.
**Severity**: MED — a normative SHOULD directly at odds with the reference implementation's dispatch logic. (Non-cosmetic because fail-open vs fail-closed rule matching is also a mild security property: under fail-open, a rule carrying a typo'd or unknown condition still fires.)
**Fix (C124)**:
- **Autonomous, spec-only (recommended)**: align §4 L295–296 to describe the SDK's actual behavior — e.g. *"Implementations MAY define additional conditions. The reference SDK ignores unrecognized conditions (fail-open): a rule matches when all recognized conditions pass. Implementations MAY instead treat an unrecognized condition as fail-closed; this is not currently required."* This converges the spec to the SDK (the established SDK→spec direction) and removes the false conformance claim without silently changing SDK behavior behind a spec edit.
- **Cross-track sub-question (route-only)**: whether the SDK *should* be tightened to fail-closed (the more defensible design against malformed/adversarial rules) is an SDK-behavioral/security decision for the operator, not an autonomous spec turn. Route alongside the fix; do NOT self-apply an SDK change.

### LOW

#### N1 (LOW, autonomous spec-only): §7 age computations lack the SDK's `max(0.0, …)` negative-age clamp
**Location**: §7 L652 (`age_days = (now() - delta.timestamp).total_seconds() / 86400.0`) and L703 (`days_inactive = (now() - last_action_timestamp).total_seconds() / 86400.0`); vs SDK `reputation.py` `current()` L442 (`age_days = max(0.0, …)`) and `inactivity_decay()` L476 (`days_inactive = max(0.0, …)`).
The SDK guards against future-dated timestamps (clock skew) by flooring age at 0.0; the spec pseudocode does not. Behavior converges anyway (a negative `days_inactive` still passes the `< 30` grace gate L705 → returns 0.0; a negative `age_days` only mildly over-weights a future delta). C84's B-I6 recorded the fractional-day `/86400.0` treatment but not this clamp.
**Fix (C124)**: add `max(0.0, …)` to §7 L652 and L703 for exact SDK parity. LOW.

### INFORMATIONAL / record-only

| ID | Item | Disposition |
|---|---|---|
| **SDK-6 (=C44 B-I5)** | §6 `select_reputation_witnesses` (L546–588) has no SDK implementation; `r6.py` `ReputationDelta.witnesses` exists (L599) but `evaluate()` L314–326 never populates it (defaults empty). | **cross-track / record** — §6 → SDK coverage gap; carry HOLDS unchanged. |
| **N2** | SDK `evaluate()` writes the delta back onto the action (`action.reputation = delta`, L327); spec `compute_reputation_delta` pseudocode only `return`s it. | **record** — illustrative pseudocode; harmless side-effect omission. |

---

## §B — Cross-Track / DESIGN-Q (route only; do NOT self-resolve in C124)

#### X-1 (MED, cross-track — STILL OPEN, unchanged since C84): three un-reconciled reputation shapes in the corpus
**Location**: this doc `ReputationDelta` (§1 L22–84 — `subject_lct`/`role_lct`/`role_pairing_in_mrh`/`t3_delta`+`v3_delta` split/`net_*`/`rule_triggered`/`contributing_factors`); r7-framework.md §1.7 L268–304 (**structurally byte-identical** intra-society ledger record — the same 15 fields, same t3/v3 split — reinforcing, not divergent); **vs** mcp-protocol.md §7.3 L394–421 (the **cross-society wire envelope**: `outcome_class`/`outcome_quality`/**flat** `trust_dimension_updates`/`propagation_scope`/`responding_society_signature` — no `subject_lct`/`role_lct`/`net_*`, a **single flat** trust-delta map rather than the t3/v3 split).
This is precisely the standing **mcp B2/B6 "reputation reshape — coordinate mcp+r7+SDK"** bundle; reputation-computation.md is a **third** doc in it. **Verified unchanged since C84**: mcp §7.3/§7.5 byte-frozen (C117 touched only §12); r7 §1.7 unchanged. No doc carries the envelope↔record mapping.
**Route**: operator/cross-track. Recommend the operator's reputation bundle adds this doc; the resolution defines one shared schema (or an explicit envelope↔record mapping table) spanning mcp §7.3 + r7 §1.7 + reputation §1 + the SDK. **NOT acted on this fire.**

#### X-2 (LOW, cross-track — STILL OPEN): §10 frames cross-society reputation as "Future Evolution"; mcp §7.5 already makes it normative
**Location**: §10 L781–782 ("### Cross-Society Reputation / Allow reputation … to partially transfer", under "## 10. Future Evolution"); vs mcp-protocol.md §7.5 (L490+, normative `propagation_scope` enum + society↔society T3/V3 tensor). Mild staleness (partial-transfer *weighting* could still be future), not a hard contradiction. C117 did not touch §7.5.
**Route**: cross-track; rides X-1 — when X-1's schema is reconciled, update §10 to point at mcp §7.5.

#### NEW-1 SDK-face (cross-track): whether the SDK `ReputationRule.matches()` should be tightened from fail-open to fail-closed. **Route**: SDK-behavioral/security operator decision; only the spec-prose alignment (describe fail-open) is in C124 autonomous scope. See NEW-1 above.

#### r7-§1.7-stale-factor (LOW, cross-track — sibling-side, NEW observation): r7-framework.md §1.7 example still carries the pre-INT-1 factor string
**Location**: r7-framework.md §1.7 example (~L294) `contributing_factors` shows `accuracy_threshold_exceeded`/0.4 — the exact pre-C85 vocabulary that reputation-computation's **INT-1** (C85) corrected to `high_accuracy`/0.4 in this doc. r7's ReputationDelta *shape* is byte-identical to reputation §1 (X-1 reinforcing), but its worked-example *factor value* was not swept when INT-1 fixed the reputation-computation copy.
**Route**: cross-track — belongs to a future r7-framework audit turn (r7 is separately in the rotation), NOT a reputation-computation defect. Recorded here so the r7 auditor inherits it (a [[feedback_cross_doc_carry_inbound]] routed *outbound*).

---

## §C — Refuted Candidates (overcall-discipline)

Twelve candidates refuted on adversarial re-read / hand-grep / git-provenance (cross-doc + sibling-churn overcall discipline C7/C9/C10/C11 held):

1. **"C122 changed t3-v3 §3/§7.1 that reputation §3/§9 cite"** — REFUTED: C122's hunk is confined to t3-v3 §10.2 L640 (ATP-conservation cell); §3 dim defs + §7.1 diminishing-returns are byte-unchanged. All 4 reputation→t3-v3 cross-refs re-verify correct.
2. **"C117 changed mcp §7.3/§7.5 → X-1/X-2 net-new"** — REFUTED: C117 relocated a phrase in mcp §12 MUST #6 only; §7.3/§7.5 byte-frozen. X-1/X-2 states unchanged, not net-new (snapshot-presence guard).
3. **"C119 changed atp-adp that reputation §9 ATP-cost depends on"** — REFUTED: C119 narrowed §7.1 MUST #6 to entity-level tensor tracking; it does not alter the ATP discharge cost grounding reputation's Sybil-resistance barrier.
4. **"§1 schema `v3_delta` 2-dims vs '6 dimensions' summary"** — REFUTED: `v3_delta` Required:Yes but "may be empty" (L79); §5 emits only `change != 0` dims; "6 dimensions" = 3 T3 + 3 V3. Already adjudicated REFUTED at C84.
5. **"§5 `compute_reputation_delta` omits a Required:Yes field"** — REFUTED: all 11 Required:Yes fields assembled (L393–408); `rule_triggered` (Required:No) set L401; SDK parity (net_* computed `@property` r6.py L602–610).
6. **"§4 Rule Categories name a phantom dimension"** — REFUTED: every axis in Success/Failure/Exceptional/Ethical examples is a valid T3 (talent/training/temperament) or V3 (veracity/validity/valuation) dim.
7. **"§7 code blocks + decay + checklist §8 incoherent"** — REFUTED: `compute_current_reputation`/`apply_reputation_decay`/`effective_reputation` compose coherently; checklist references only §5-defined functions; undefined helpers are illustrative (INT-4 non-defect, C84).
8. **"§5 worked-example numbers don't reproduce"** — REFUTED: 0.018/0.0065/0.022 + nets 0.0245/0.022 all reproduce exactly from §4's rule.
9. **"§5 dimension-delta clamp diverges from SDK"** — REFUTED: spec L442 `max(-1.0, min(1.0, total_delta))` == SDK L297–298; loop order + `getattr` access match.
10. **"reputation aggregation horizon window diverges (spec filters, SDK doesn't)"** — REFUTED: BOTH filter by horizon (spec L637–642 `since=`; SDK L432–433 `cutoff`), default 90 both; recency `exp(-age/30)` matches.
11. **"r7 §1.7 ReputationDelta contradicts reputation §1"** — REFUTED: byte-identical intra-society shape (the real divergence is mcp §7.3, captured as X-1). Only cosmetic example-value differences (+ the r7-side stale factor, routed separately).
12. **"min_atp_stake `atp_stake` field undefined in doc"** — REFUTED/DROPPED: within already-closed SDK-5 scope; SDK field is `action.request.atp_stake` (reputation.py L112, r6.py L608); prose reference is not a contradiction.

---

## Remediation Summary (for the C124 turn)

**2 autonomous-actionable** (one file: `reputation-computation.md`; both converge the spec toward the SDK, never vice versa):

| ID | Sev | One-line fix | Cluster |
|---|---|---|---|
| NEW-1 | M | §4 L295–296: replace the fail-closed SHOULD with a description of the SDK's actual fail-OPEN behavior (unrecognized conditions ignored; a rule matches when all recognized conditions pass; fail-closed MAY be adopted, not required) | algorithm/conformance |
| N1 | L | §7 L652 + L703: add `max(0.0, …)` negative-age clamp for SDK parity | algorithm |

**3 DESIGN-Q / cross-track (do NOT self-resolve in C124)**:
- **X-1** reputation-schema reshape — mcp §7.3 flat `trust_dimension_updates` ⊥ r7 §1.7 / this doc's `t3_delta`+`v3_delta` split. The HELD mcp **B2/B6** bundle; route this doc into it. **Route only.**
- **X-2** §10 "Future Evolution" stale vs mcp §7.5 normative — rides X-1.
- **NEW-1 SDK-face** — whether SDK `matches()` should be tightened to fail-closed (SDK-behavioral/security operator decision; the spec-prose alignment is the C124 autonomous path).
- **r7-§1.7-stale-factor** — r7-framework §1.7 example carries the pre-INT-1 factor string; belongs to a future r7 audit turn (routed outbound).

**Record-only**: SDK-6/B-I5 (§6 `select_reputation_witnesses` unimplemented in SDK; carry HOLDS), N2 (SDK write-back side-effect).

**Carry re-verification (C84's four deferred items, re-checked against the current corpus)**:
- **X-1** → **STILL OPEN** (mcp §7.3/§7.5 + r7 §1.7 byte-frozen since C84; no reconciliation).
- **X-2** → **STILL OPEN** (mcp §7.5 still normative; §10 still frames it as future).
- **INT-2 SDK face / B-I7** (`role_pairing_in_mrh` Required-but-absent-from-SDK) → **CLOSED (spec side)**: r6.py `ReputationDelta` L589–600 has no such field; spec L72 now Required:**No** → SDK conformant.
- **SDK-6 / B-I5** (§6 witness SDK gap) → **HOLDS** (record-only).

---

*C13→C15→C44→C45→C84→C85→C123 lineage: C13/C15 fixed the §5/§7 algorithm + V3-naming wire layer; C44/C45 fixed the structural (rule-schema access, role-scoped decay) and cross-doc-semantic (Validity "Confirmed Transfer") layers; C84 reached the §5-normative-algorithm SDK-fidelity layer; C85 remediated all 9. C123 finds the C15+C45+C85 layers fully durable (30/30 held, fifth clean delta) and reaches one **remediation-introduced** conformance defect in C85's own added prose (NEW-1: §4 fail-closed SHOULD ⊥ SDK fail-open `matches()`) plus one trivial clamp-parity gap (N1). The inbound-carry surface is clean — all three siblings that moved since C84 edited outside reputation's cross-ref surface. X-1/X-2 remain the standing cross-track reputation-reshape carries, unchanged.*
