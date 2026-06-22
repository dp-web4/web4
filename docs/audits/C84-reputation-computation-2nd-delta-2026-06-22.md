# C84: reputation-computation.md — Second Delta Re-Audit

**Date**: 2026-06-22
**Auditor**: Autonomous session (legion-web4-20260622-000009), LEAD
**Document**: `web4-standard/core-spec/reputation-computation.md` (765 lines)
**Lineage**: C13/C15 (internal-consistency, `reputation-computation-internal-consistency-2026-05-25.md`) → **C44** (1st delta, prior C15; PR #304 `b98f690c`) → **C45** remediation (PR #305 `00803b03`, 13 findings in 5 clusters) → **C84** (this 2nd delta). File **byte-unchanged since C45** (last commit `00803b03`).
**Instrument**: refute-by-default multi-agent finder pass — 1 §A regression verifier (8 C15 + 13 C45, extended to every edited site's SDK/vector/sister-doc mirror per the C54/C56/C82 remediation-introduced-regression lesson) + 4 §B dimension finders (internal-consistency, SDK-fidelity, canonical-cross-doc, schema/wire) → hand-verified each headline candidate with a loose grep at the cited line (C64 lesson) → consolidation/dedup.

**Cross-references re-read against the live files at the cited lines**:
- `web4-standard/implementation/sdk/web4/reputation.py` — `ReputationEngine.evaluate`, `analyze_factors`, `ReputationRule.matches`, `DimensionImpact`/`Modifier`, `ReputationStore.current`/`inactivity_decay`/`effective_reputation`.
- `web4-standard/implementation/sdk/web4/r6.py` — `ReputationDelta` (~L580), `Role` (~L234), `TensorDelta`.
- `web4-standard/implementation/sdk/web4/trust.py` — `T3`/`V3`/`V3_WEIGHTS`.
- `web4-standard/test-vectors/reputation/reputation-operations.json` — rep-001..rep-005 (**note the move**: C44 cited this under `implementation/sdk/web4/tests/vectors/`; it now lives under `test-vectors/reputation/` — a relocation, not a content change).
- `web4-standard/core-spec/t3-v3-tensors.md` §3 (V3 dim defs + ranges), §7.1 (diminishing returns), §10.2 (Valuation open question).
- `web4-standard/ontology/t3v3-ontology.ttl` — V3 dimension comments.
- `web4-standard/core-spec/r7-framework.md` §1.7 — parent Reputation component.
- `web4-standard/core-spec/mcp-protocol.md` §7.3/§7.5 — cross-society reputation envelope (the MCP-as-inter-society amendment).
- `web4-standard/core-spec/atp-adp-cycle.md` — ledger-medium-agnostic note.

---

## Summary

| | Count | Notes |
|---|---|---|
| **§A regression** | 8/8 C15 **HELD** + 13/13 C45 **HELD**, **0 REGRESSED** | Fourth consecutive clean delta in this lineage (C40 mrh, C42 t3-v3, C44 reputation, now C84). No remediation-introduced defect at any C45-edited site or its SDK/vector/sister-doc mirror. |
| **§B confirmed** | 13 distinct (4 M / 6 L / 3 INFO) | 0 HIGH |
| **§B refuted** | 13 | cross-doc overcall discipline held (see §C) |
| **Autonomous-actionable (→ C85)** | 9 | INT-1, SDK-1, SDK-2, INT-2 (recommended path), SDK-3, SDK-4, SDK-5, INT-3, B-L2 (annotation) |
| **DESIGN-Q / cross-track (route only)** | 4 | X-1 (reputation-schema reshape = B2/B6 bundle + this doc), X-2, B-I7-SDK-face, SDK-6/B-I5 |
| **Record-only** | 1 | INT-4 (pseudocode helpers) |

**Headline**: The C15+C45 algorithm/wire layers are fully durable — fourth clean delta in the lineage. The new layer §B reaches is **C45 remediation-incompleteness and a deeper SDK-fidelity gap in §5's normative algorithm**: (1) C45's B-L1 factor-vocabulary convergence (`high_accuracy`) reached §4/§5 but **missed the §1 schema example**, which still carries the pre-C45 `accuracy_threshold_exceeded`/weight-0.5 factor that no code path emits (**INT-1**); (2) §5's normative `analyze_factors` **derives** the timing factors from a `constraints.deadline` datetime + a 1-hour threshold, but the SDK reads **pre-resolved boolean flags** — the spec algorithm cannot run against the SDK's own data model (**SDK-2**); (3) §5 records only the **first** triggered rule's id while accumulating deltas across **all** of them, losing provenance the SDK preserves by joining all ids (**SDK-1**); (4) the **Required** `role_pairing_in_mrh` field is never assembled by the doc's own constructor and is still absent from the SDK `ReputationDelta` (**INT-2**, hardening C44's B-I7). The cross-track headline is **X-1**: this doc's `t3_delta`/`v3_delta`-split reputation record now sits as a **third** un-reconciled shape alongside mcp §7.3's flat `trust_dimension_updates` envelope and r7 §1.7 — exactly the HELD mcp **B2/B6 reputation-reshape** bundle, route-only.

---

## §A — Regression Check

Two layers re-verified against the live file + SDK + vectors + canonical sister-docs. **Unanimous: 8/8 C15 HELD, 13/13 C45 HELD, 0 REGRESSED, 0 PARTIAL.**

### Layer 1 — the 8 C15 findings

| C15 ID | Sev | Finding (abbrev.) | Status | Live evidence |
|---|---|---|---|---|
| H1 | HIGH | §7 aggregate onto 0.5 baseline | **HELD** | L632 `current_value = 0.5 + (weighted_sum / weight_sum) …`; SDK `reputation.py:454` `_clamp(0.5 + aggregated)`; vector rep-003 confirms 0.5+0.076. |
| M1 | MED | third V3 dim `valuation` everywhere | **HELD** | L46/L202/L307/L365; no stray V3 `value`; SDK `trust.py` `V3.valuation`. |
| M2 | MED | §6 witness reads `role_lct` | **HELD** | L534 `get_validators_for_role(action.role.role_lct)`; no `roleType`. |
| M3 | MED | §5 `action_id` pre-exec | **HELD** | L382 `= action.action_id  # pre-execution id`; no ledgerProof/txHash. |
| M4 | MED | §5 V3 `from` role-contextualized | **HELD** | L367 `action.role.v3InRole[dimension]`; SDK `v3_in_role`. |
| L1 | LOW | §5 sets role_lct/type/target/timestamp | **HELD** | L379–390. |
| L2 | LOW | §7 "30-day time constant (≈20.8-day half-life)" | **HELD** | L625. |
| L3 | LOW | §5 example uses a defined §4 rule | **HELD** | §4 L247 defines `successful_analysis_completion`; §5 L489 references it. |

### Layer 2 — the 13 C45 remediations (verified applied AND accurate, not merely present)

All HELD with live cites: **B-M1** (§4/§5 `t3_impacts`/`v3_impacts`, getattr read; SDK+vectors agree), **B-M2** (§7 decay `(entity_lct, role_lct)`, unused `dimension` dropped), **B-L3** (clamp+recompute change), **B-L4** (`analyze_factors` quality>0.5 — correctly distinct from §4's `quality_threshold` 0.95 *trigger*), **B-L5** (dead normalization removed), **B-L1** (factor name `high_accuracy` in §4/§5 — *but see INT-1 for the missed §1 site*), **B-L2** (§5 example self-consistent against §4's rule — *but see B-L2-residual vs vector*), **B-L7** (§1 zero-change `validity` dropped), **B-M3** (§3.2 Validity realigned to canonical "Confirmed Transfer" — token-by-token accurate vs `t3-v3-tensors.md` §3.1 + §3.3 `1.0 if value_transferred else 0.0`), **B-I3** (Veracity/Valuation prose canonical), **B-L6** (no `on-chain` remains; `grep` returns 0; §9/Summary use "society ledger"), **B-I1** (diminishing-returns cross-ref to t3-v3 §7.1 / vector t3v3-007 verified live), **B-I6** (fractional-day age).

**Remediation-introduced-defect sweep**: No HIGH/MED regression at any C45-edited site. The two residuals below are NEW §B findings whose *root* is C45's edits being site-incomplete, not C45 corrupting what it touched:
- **INT-1** — B-L1's factor convergence left the §1 schema example (L50) on the old vocabulary.
- **B-L2-residual** — the §5 example (temperament +0.0065 via `early_completion`×1.3) and conformance vector rep-001 (temperament 0.005, no `early_completion`) compute different deltas for the same narrative; each is internally consistent against its own rule instance.

**Streak**: C40 → C42 → C44 → C84 all 0-regressed. The C15 (#237) and C45 (#305) remediations are durable.

---

## §B — New Findings

### MEDIUM

#### INT-1 (MED, autonomous — C45 B-L1 remediation-incompleteness): §1 schema example `contributing_factors` use a factor name + weight no code path emits
**Location**: §1 Complete Schema L50 (`{"factor": "accuracy_threshold_exceeded", "weight": 0.5}`); contradicts §5 `analyze_factors` L442–447 (emits `{'factor': 'high_accuracy', 'weight': 0.4}`) and §4 modifier keys (L259/L273 `high_accuracy`).
C45's B-L1 converged the quality-factor name on `high_accuracy` across §4 and §5 and the §5 worked example, but the **§1 canonical schema example** was not swept — it still shows `accuracy_threshold_exceeded` at weight `0.5`, a factor name + weight that no `analyze_factors` path produces and no §4 rule keys on. The doc's headline example therefore exhibits the exact pre-C45 vocabulary B-L1 removed everywhere else.
**Fix (C85)**: §1 L50 → `{"factor": "high_accuracy", "weight": 0.4}`. (Optional: L52 `resource_efficiency` weight is `efficiency × 0.2` per §5 L477, not a fixed `0.2` — annotate or leave as illustrative.)

#### SDK-2 (MED, autonomous): §5 `analyze_factors` derives the timing factors from a datetime + 1-hour threshold; the SDK reads pre-resolved boolean flags — the spec algorithm cannot run against the SDK data model
**Location**: §5 `analyze_factors` L450–467; vs SDK `reputation.py` L186–191.
The spec computes `deadline_met` by reading `action.request.constraints.deadline` (a datetime), comparing it to `result.timestamp`, and derives `early_completion` from `time_saved > timedelta(hours=1)`. The SDK reads pre-computed booleans directly: `action.request.constraints.get("deadline_met")` / `.get("early_completion")` — it never sees a `deadline` datetime nor applies a 1-hour rule. So §5's normative `analyze_factors` body is incompatible with the SDK `R7Action` it claims to mirror; the 1-hour `early_completion` threshold lives only in the spec.
**Fix (C85)**: rewrite §5's timing block to read boolean `constraints.get("deadline_met")` / `.get("early_completion")` (SDK parity), and drop the datetime-derivation + 1-hour prose — OR document explicitly that the SDK expects the caller to pre-resolve these flags and the §5 derivation is one illustrative way to compute them upstream.

#### SDK-1 (MED, autonomous): §5 records only the FIRST triggered rule's id; the SDK joins ALL triggered rule ids
**Location**: §5 L383 (`reputation.rule_triggered = triggered_rules[0].rule_id`); vs SDK `reputation.py` L312/L320 (`rule_ids = ", ".join(r.rule_id for r in triggered)` → `rule_triggered=rule_ids`).
§5's own delta loop accumulates `total +=` across **all** triggered rules (mirrored by SDK L261/L288), but the provenance field records only the first rule's id. The SDK preserves full provenance by joining every triggered rule's id. (The §1 field table L76 also describes `rule_triggered` in the singular — "Which reputation rule was triggered" — so the doc is internally first-rule-minded.)
**Fix (C85)**: §5 L383 → `reputation.rule_triggered = ", ".join(r.rule_id for r in triggered_rules)`; reword §1 L76 to "Which reputation rule(s) were triggered" (and note `reason` derives from the full set, as SDK L321 does).

#### INT-2 (MED, autonomous internal face + cross-track SDK face — hardens C44 B-I7): Required field `role_pairing_in_mrh` is never assembled by the doc's own constructor and is absent from the SDK `ReputationDelta`
**Location**: §1 field table L72 (`role_pairing_in_mrh` — **Required: Yes**, "Full MRH role pairing context"); vs §5 assembly L378–390 (sets 12 fields, omits `role_pairing_in_mrh`) and SDK `r6.py` `ReputationDelta` L589–600 (no such field — only `role_lct` L590).
The single constructor the spec defines (`compute_reputation_delta`) produces a ReputationDelta that is missing a field its own schema marks Required. The SDK likewise has no `role_pairing_in_mrh` (this is C44's B-I7, now hardened — the SDK has not gained it in the interval, and the internal §5 omission is a *new* face C44 did not record).
**Fix (C85, recommended spec-only path)**: downgrade §1 L72 to **Required: No** with a note "derivable from `role_lct` via the entity↔role MRH pairing" — matching the SDK, which carries only `role_lct`. (The alternative — keep Required and add the field to §5 assembly + the SDK `ReputationDelta` — pulls in a cross-track SDK edit; see DESIGN-Q below.)

### LOW

#### SDK-3 (LOW, autonomous): §5 resource-efficiency factor reads `resource.required` / `result.resourceConsumed`; SDK reads `resource.required_atp` / `result.atp_consumed` (+ `required > 0` guard + round-4)
**Location**: §5 L470–479; vs SDK `reputation.py` L194–202.
**Fix (C85)**: align field names to `required_atp`/`atp_consumed`, add the `required > 0` guard and `round(efficiency * 0.2, 4)` to the §5 prose.

#### SDK-4 (LOW, autonomous): §4 `quality_threshold` comparator is unspecified; SDK matches iff `quality >= threshold` (missing quality → 0.0 → fail)
**Location**: §4 rule L251 (`quality_threshold: 0.95`, no comparator stated); vs SDK `ReputationRule.matches` L105–108.
**Fix (C85)**: state in §4/§5 that a rule with `quality_threshold` matches iff `output.quality >= threshold`, with missing quality treated as 0.0.

#### SDK-5 (LOW, autonomous): SDK `ReputationRule.matches` supports a `min_atp_stake` trigger condition the spec §4 does not document
**Location**: SDK `reputation.py` L111–113 (`min_atp_stake`); vs §4 trigger_conditions L248–252 (only `action_type`/`result_status`/`quality_threshold`).
**Fix (C85)**: add `min_atp_stake` to the §4 `trigger_conditions` list (or note the set is open-ended). Direction SDK→spec.

#### INT-3 (LOW, autonomous): §7 `apply_reputation_decay` returns a negative delta with no defined application site
**Location**: §7 L688 (returns `decay`); `compute_current_reputation` L591–635 computes value purely from stored deltas + 0.5 baseline and never consumes the decay; checklist L702 implies decay applies. (The SDK composes it in `effective_reputation` = `current + inactivity_decay` — `reputation.py` L489–509 — which the spec does not mirror.)
**Fix (C85)**: add a sentence (or a small `effective_reputation`-style wrapper) stating how the decay delta composes with `compute_current_reputation`, matching SDK `effective_reputation`.

#### B-L2-residual (LOW, autonomous annotation; vector face = cross-track): §5 worked example temperament `+0.0065` vs conformance vector rep-001 `0.005`
**Location**: §5 example L502 (temperament `+0.0065` = base 0.005 × `early_completion` 1.3); vs vector rep-001 (`reputation-operations.json` temperament `change: 0.005`, rule modifiers `[]`, factor list omits `early_completion`).
Each is internally consistent against its own rule instance (§5's §4 rule includes the `early_completion`×1.3 temperament modifier and a "completed 2 hours early" scenario; rep-001's rule omits it). But a reader treating §5's example as the worked instance of `successful_analysis_completion` and rep-001 as its vector sees two temperament deltas.
**Fix (C85)**: annotate the §5 example that it exercises a richer factor set than vector rep-001 (spec-only = autonomous) — OR add the `early_completion`×1.3 modifier + factor to vector rep-001 to make them identical (vector edit = cross-track). Prefer the annotation.

### INFORMATIONAL / record-only

| ID | Item | Disposition |
|---|---|---|
| **SDK-6 (=C44 B-I5)** | §6 `select_reputation_witnesses` (L518–560) has no SDK implementation; `ReputationDelta.witnesses` exists but `evaluate()` never populates it. | **cross-track / record** — §6 → SDK coverage gap; carry HOLDS. |
| **INT-4** | §5/§6/§7 pseudocode helpers called but never defined (`matches_trigger_conditions`, `factor_applies`, `generate_reason`, `get_reputation_deltas`, `get_validators_for_role`, `get_mrh_witnesses`). | **record** — expected in illustrative pseudocode; not a defect. |

---

## §B — Cross-Track / DESIGN-Q (route only; do NOT self-resolve in C85)

#### X-1 (MED, cross-track — the HELD mcp B2/B6 reputation-reshape bundle, now +this doc): three un-reconciled reputation shapes in the corpus
**Location**: this doc `ReputationDelta` (§1 L22–84 — `subject_lct`/`role_lct`/`role_pairing_in_mrh`/`t3_delta`+`v3_delta` split/`net_trust_change`/`net_value_change`/`rule_triggered`/`contributing_factors`); r7-framework.md §1.7 (byte-identical shape — the intra-society ledger record); **vs** mcp-protocol.md §7.3 L394–421 (the **cross-society wire envelope**: `outcome_class`/`outcome_quality`/**flat** `trust_dimension_updates`/`propagation_scope`/`responding_society_signature` — no `subject_lct`/`role_lct`/`net_*`, and a **single flat** trust-delta map rather than the t3/v3 split).
mcp §7.3 cross-references r7 §1.7 only for the **witness** sub-shape (L417), not for the full ReputationDelta. No doc carries a mapping (`outcome_class`→`rule_triggered`? `trust_dimension_updates`→`t3_delta`+`v3_delta`?). This is precisely the standing **mcp B2/B6 "reputation reshape — coordinate mcp+r7+SDK"** item; reputation-computation.md is a **third** doc in that bundle.
**Route**: operator/cross-track. Recommend the operator's reputation bundle adds this doc, and the resolution defines one shared schema (or an explicit envelope↔record mapping table) spanning mcp §7.3 + r7 §1.7 + reputation-computation §1 + the SDK. **Per this session's policy condition, NOT acted on this fire.**

#### X-2 (LOW, cross-track — rides X-1): §10 frames cross-society reputation as "Future Evolution"; mcp §7.5 already makes it normative
**Location**: §10 L737–738 ("### Cross-Society Reputation / Allow reputation … to partially transfer", under "## 10. Future Evolution"); vs mcp-protocol.md §7.5 L501–514 (normative `propagation_scope` enum + society↔society T3/V3 tensor). Mild staleness, not a hard contradiction (partial-transfer *weighting* could still be future).
**Route**: cross-track; when X-1's schema is reconciled, update §10 to point at mcp §7.5 rather than listing cross-society reputation as unbuilt.

#### INT-2 SDK face / B-I7 (cross-track): whether the SDK `ReputationDelta` should gain `role_pairing_in_mrh` or the spec should drop the Required marking — couples the INT-2 autonomous recommendation above. **Route**: cross-track (only the spec-only downgrade is in C85 scope).

---

## §C — Refuted Candidates (overcall-discipline)

Thirteen candidates were refuted on adversarial re-read / hand-grep (the cross-doc overcall pattern C7/C9/C10/C11 held):

1. **"§3.3 Valuation range contradicts t3-v3 (B-I2 carry)"** — REFUTED: C45 softened §3.3 L217 to explicitly defer to the t3-v3 §3.1/§10.2 open question ("may exceed 1.0 … pending an operator decision; do not assume a hard [0,1] clamp"). The doc now **correctly reflects** the open question. The underlying operator decision stays open at the t3-v3/ontology level (carry-C42 D3), but reputation-computation is no longer divergent — **B-I2 CLOSED for this doc**.
2. **"§3.2 Validity definition drift (was B-M3)"** — REFUTED: token-by-token match to canonical "Confirmed Transfer" (verified live).
3. **"§9 'Each action costs ATP' contradicts atp-adp"** — REFUTED: re-verified consistent with the ATP→ADP discharge model (matches C44's prior refutation; re-checked, not blindly re-raised).
4. **"on-chain over-commit (B-L6)"** — REFUTED: `grep` confirms 0 `on-chain`; r7 §1.7 also ledger-medium-agnostic. Softening holds corpus-consistently.
5. **"v3_delta omits validity → contradicts §3's 3 dims / Summary '6 dimensions'"** — REFUTED: §5 L370 records only `change != 0` dims; "6 dimensions" = 3 T3 + 3 V3. Consistent.
6. **"net_trust_change/net_value_change field vs SDK @property"** — REFUTED: both = sum of changes; functionally identical.
7. **"§5 worked-example numbers don't reproduce from §4 rule"** — REFUTED: 0.018/0.0065/0.022 all reproduce exactly.
8. **"role dropped in some algorithm signature"** — REFUTED: every function (§5/§6/§7) preserves role.
9. **"§7 baseline+average vs modeling note vs §10 accumulation incoherent"** — REFUTED: mutually coherent; the note explicitly defers accumulation to §10.
10. **"ReputationDelta contradicts r7 §1.7"** — REFUTED: byte-identical intra-society shape (the divergence is mcp §7.3, captured as X-1).
11. **"DEFAULT_HALF_LIFE_DAYS=30 vs spec 30-day constant is a divergence"** — REFUTED: same number, same formula position; the `≈20.8-day half-life` comment is correct (1/e time constant).
12. **"resource_efficiency missing from §5 example"** — REFUTED: the example's stated inputs give no resource data; omission defensible.
13. **"field-table/example completeness"** — REFUTED: all 12 Required:Yes fields present in the §1 example; no orphan fields (the *factor-vocabulary* mismatch is INT-1, a value not a structural gap).

---

## Remediation Summary (for the C85 turn)

**9 autonomous-actionable** (one file: `reputation-computation.md`; every fix converges the spec toward the SDK + canonical, never vice versa):

| ID | Sev | One-line fix | Cluster |
|---|---|---|---|
| INT-1 | M | §1 L50 example factor `accuracy_threshold_exceeded`/0.5 → `high_accuracy`/0.4 (B-L1's missed site) | factor-vocab |
| SDK-2 | M | §5 `analyze_factors` timing block → read boolean `constraints.get("deadline_met"/"early_completion")` (SDK parity) | algorithm |
| SDK-1 | M | §5 L383 → join ALL triggered rule ids; reword §1 L76 to "rule(s)" | algorithm |
| INT-2 | M | §1 L72 `role_pairing_in_mrh` Required:Yes → **No** ("derivable from `role_lct` via MRH") — SDK parity | schema |
| SDK-3 | L | §5 resource fields → `required_atp`/`atp_consumed` + `required>0` guard + round-4 | algorithm |
| SDK-4 | L | §4/§5: state `quality_threshold` matches iff `quality >= threshold` (missing→0.0) | algorithm |
| SDK-5 | L | §4: add `min_atp_stake` to `trigger_conditions` (or note open-ended) | schema |
| INT-3 | L | §7: state how the decay delta composes with `compute_current_reputation` (SDK `effective_reputation`) | algorithm |
| B-L2-residual | L | §5 example: annotate that it exercises a richer factor set than vector rep-001 (spec-only) | factor-vocab |

**4 DESIGN-Q / cross-track (do NOT self-resolve in C85)**:
- **X-1** reputation-schema reshape — mcp §7.3 flat `trust_dimension_updates` ⊥ r7 §1.7 / this doc's `t3_delta`+`v3_delta` split. The HELD mcp **B2/B6** bundle; route this doc into it. **Route only (policy condition).**
- **X-2** §10 "Future Evolution" stale vs mcp §7.5 normative — rides X-1.
- **INT-2 SDK face / B-I7** — SDK `ReputationDelta` gains `role_pairing_in_mrh` vs spec drops Required (the spec-only downgrade is the C85 autonomous path; the SDK side is cross-track).
- **SDK-6 / B-I5** — §6 `select_reputation_witnesses` unimplemented in SDK (record).

**Carry re-verification (C44's three deferred items, re-checked against the current corpus)**:
- **B-I2** (Valuation range) → **CLOSED for this doc** (C45 softened §3.3 to reflect the open question; the operator-level t3-v3 decision remains carry-C42 D3).
- **B-I7** (`role_pairing_in_mrh` Required-but-absent-from-SDK) → **HARDENED** into INT-2 (now two faces: the doc's own §5 constructor also omits it).
- **B-I5** (§6 witness SDK gap) → **HOLDS** (SDK-6).

**Vector-relocation note**: `reputation-operations.json` moved from `implementation/sdk/web4/tests/vectors/` (C44's cited path) to `test-vectors/reputation/`. Content unchanged; future audits should cite the new path.

---

*C13→C15→C44→C84 lineage: C13/C15 fixed the §5/§7 algorithm + V3-naming wire layer; C44/C45 fixed the structural (rule-schema access, role-scoped decay) and cross-doc-semantic (Validity "Confirmed Transfer") layers; C84 reaches the §5-normative-algorithm SDK-fidelity layer (factor derivation vs flags, rule-id provenance, resource fields, trigger comparator) plus one C45 site-incompleteness (INT-1) and the corpus-level reputation-schema reshape (X-1). Both prior remediations remain fully durable — four clean deltas in a row.*
