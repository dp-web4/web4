# C44: reputation-computation.md Delta Re-Audit

**Date**: 2026-06-10
**Auditor**: Autonomous session (legion-web4-20260610-000050), LEAD
**Document**: `web4-standard/core-spec/reputation-computation.md` (768 lines)
**Prior audit**: C15 (`docs/audits/reputation-computation-internal-consistency-2026-05-25.md`), 8 findings (H1, M1–M4, L1–L3); remediation merged **PR #237** (`51d628ad`). File untouched since (16 days).
**Instrument**: refute-by-default multi-agent WORKFLOW — 2 §A regression checkers + 5 §B dimension finders → adversarial verify each candidate (refute-by-default) → consolidation. 36 agents; §B 29 raw candidates → 5 refuted / 24 surviving (deduped to 18 distinct items below).

**Cross-references re-read against the live files at the cited lines**:
- `web4-standard/implementation/sdk/web4/reputation.py` — `ReputationEngine.evaluate`, `analyze_factors`, `ReputationStore.current` / `inactivity_decay`, `DimensionImpact`, `t3_impacts`/`v3_impacts` (the SDK module names this file as the implementation of *this* spec).
- `web4-standard/implementation/sdk/web4/r6.py` — `ReputationDelta`, `Role` (`role_lct`, `t3_in_role`, `v3_in_role`), `R7Action` (`action_id`).
- `web4-standard/implementation/sdk/web4/trust.py` — `V3` (`valuation`/`veracity`/`validity`), `V3_WEIGHTS`.
- `web4-standard/core-spec/t3-v3-tensors.md` §3.1/§3.3/§7.1/§10.2 — canonical V3 dimension definitions + ranges + diminishing-returns (the C42/C43 target; remediation merged #299, `15a2a41a`).
- `web4-standard/ontology/t3v3-ontology.ttl` — canonical V3 dimension IRIs/comments.
- `web4-standard/core-spec/r7-framework.md` §1.7 — parent R7 Reputation component.
- `web4-standard/core-spec/atp-adp-cycle.md` — ledger-medium-agnostic "Packet" terminology note.
- `web4-standard/implementation/sdk/web4/tests/vectors/reputation-operations.json` — conformance vectors (`t3_impacts`/`v3_impacts`, `high_accuracy`).

---

## Summary

| | Count | Notes |
|---|---|---|
| **§A regression** | 8/8 **HELD**, **0 REGRESSED** | Third consecutive clean delta re-audit (after C40 mrh, C42 t3-v3) |
| **§B confirmed** | 18 (3 M / 7 L / 8 INFO) | from 29 raw → 5 refuted → dedup |
| **§B refuted** | 5 | overcall-discipline working (see §C) |
| **Autonomous-actionable** | 13 | B-M1, B-M2, B-M3, B-L1–B-L7, B-I1, B-I4, B-I6 |
| **DESIGN-Q / cross-track** | 3 | B-I2 (Valuation range → carry-C42 D3), B-I3 (couples B-M3), B-I7 (SDK `role_pairing_in_mrh` gap, shared w/ r7) |

**Headline**: All 8 C15 findings held — the §5/§7 algorithm-correctness cluster (H1 baseline, M2 `role_lct`, M3 pre-exec `action_id`, M4 role-contextualized V3 `from`, L1 required-field assembly, L3 worked-example rule) and the M1 `value`→`valuation` rename are all intact and SDK-aligned. The new §B work surfaces a **deeper layer the C15 wire-level pass did not reach**: (1) the §5 algorithm cannot actually read §4's own rule schema (**B-M1**, structural), (2) reputation decay is role-agnostic despite the doc's CRITICAL role-contextualization mandate (**B-M2**, the same defect-class M4 fixed for V3 `from`, missed in the decay path), and (3) the §3.2 **Validity** definition is a pre-canonical "logical soundness" reading that contradicts the canonical "Confirmed Transfer / value delivery" definition (**B-M3**, cross-doc drift vs the C42/C43-current t3-v3 spec — exactly the coupling this target was chosen to probe).

---

## §A — Regression Check (C15 findings)

Both regression agents independently re-read the live file + SDK. Unanimous: **8/8 HELD, 0 REGRESSED, 0 PARTIAL**.

| C15 ID | Sev | Finding (abbrev.) | Status | Live evidence |
|---|---|---|---|---|
| H1 | HIGH | §7 aggregate must apply onto 0.5 baseline | **HELD** | L640 `current_value = 0.5 + (weighted_sum / weight_sum) …`; prose L638–639 + docstring L603; example self-consistent (analyst `> 0.5` L655, unacted role `0.50` L661); modeling note L666 cites SDK `ReputationStore.current()`. SDK `reputation.py` L453–454 `return _clamp(0.5 + aggregated)`. |
| M1 | MED | third V3 dim `value`→`valuation` everywhere | **HELD** | Every third-V3-dim usage is `valuation` (§1 L47, §3.3 heading L200, §4 L305, §5 list L370). Grep of `\bvalue\b` returns only correct usages (tensor-name "Value tensor", `net_value_change`, factor-dict `'value'` key, prose). Matches ontology `web4:valuation` + `trust.py` `V3.valuation`. |
| M2 | MED | §6 witness reads `role_lct` not `roleType` | **HELD** | L542 `get_validators_for_role(action.role.role_lct)`; no `roleType` in file. `r6.py` `Role` has only `role_lct` (L234). |
| M3 | MED | §5 `action_id = action.action_id` (pre-exec) | **HELD** | L390 `reputation.action_id = action.action_id  # pre-execution id, set at request time`; no `ledgerProof`/`txHash`. SDK `evaluate()` L319 `action_id=action.action_id`. |
| M4 | MED | §5 V3 `from` role-contextualized (`v3InRole`) | **HELD** | L381–382 V3 reads `action.role.v3InRole[dimension]`, mirroring T3 L364–365 `t3InRole`. SDK reads both from role (`reputation.py` L273/L300). |
| L1 | LOW | §5 sets `role_lct`/`action_type`/`action_target`/`timestamp` | **HELD** | §5 assembly L387–398 sets all four. SDK `evaluate()` L314–326 parity. |
| L2 | LOW | §7 "30-day half-life" relabeled | **HELD** | L633 comment now "30-day time constant (1/e; ≈20.8-day half-life)" — accurate. |
| L3 | LOW | §5 example uses a *defined* §4 rule, correct mapping | **HELD** | L497 references `successful_analysis_completion` (defined §4 L245); L508–513 mapping matches §4 (deadline_met×exceed_quality→training, early_completion→temperament). No undefined `successful_model_training`. |

**Streak**: C40 (mrh) 0-regressed, C42 (t3-v3) 0-regressed, C44 (reputation) 0-regressed — three consecutive clean delta re-audits. The C15 remediation (#237) was durable; nothing in the 16-day interval disturbed it.

---

## §B — New Findings

### MEDIUM

#### B-M1 (MEDIUM, autonomous): §5 `compute_dimension_delta` cannot read §4's own rule schema — `reputation_impact[dimension]` is flat, but §4 nests under `t3_changes`/`v3_changes`

**Location**: §5 `compute_dimension_delta` L409–413; contradicts §4 Rule Structure L251–275.
**Found independently by both the `internal` and `sdk-fidelity` finders.**

§5 accesses the impact by *bare dimension name*:
```python
for rule in rules:
    if dimension not in rule.reputation_impact:   # L410
        continue
    impact = rule.reputation_impact[dimension]    # L413
```
But §4's rule JSON nests dimensions two levels deep:
```json
"reputation_impact": {
  "t3_changes": { "training": {...}, "temperament": {...} },
  "v3_changes": { "veracity": {...} }
}
```
So `rule.reputation_impact["training"]` is a miss (it lives under `t3_changes`). As written, **§5 finds no dimension and every delta is zero** — the algorithm is incompatible with the doc's only concrete rule schema.

**SDK + vector authority**: `reputation.py` splits the impacts into two flat per-tensor maps — `t3_impacts: Dict[str, DimensionImpact]` / `v3_impacts` (L85–86) — and reads `rule.t3_impacts.get(dim)` (L262) / `rule.v3_impacts.get(dim)` (L289). The conformance vector `reputation-operations.json` uses `"t3_impacts"`/`"v3_impacts"` (L29/L42). So the SDK and vectors agree the structure is a **T3/V3-split flat map**, not §4's `t3_changes`/`v3_changes` nesting *nor* §5's flat `reputation_impact[dim]`.

**Recommendation**: Reconcile §4 + §5 on one structure that matches the SDK/vectors. Cleanest: change §4's rule JSON keys to `t3_impacts`/`v3_impacts` and have §5 read `rule.t3_impacts[dimension]` for T3 dims and `rule.v3_impacts[dimension]` for V3 dims. Keep the T3/V3 split (the SDK + vectors enforce it).

#### B-M2 (MEDIUM, autonomous): §7 `apply_reputation_decay` is entity-global (no `role_lct`) — contradicts the doc's CRITICAL role-contextualization mandate and the SDK

**Location**: §7 Reputation Decay, signature L673; contradicts §1 L87, §7 `compute_current_reputation` L599/L605–606/L619.

`compute_current_reputation` is role-scoped and its docstring is emphatic:
```python
def compute_current_reputation(entity_lct, role_lct, dimension, time_horizon_days=90):  # L599
    # CRITICAL: Reputation is role-contextualized. This function computes
    # reputation for a specific entity+role pairing, not globally.        # L605–606
```
…and §1 L87 reiterates "the `t3_delta` and `v3_delta` apply to the specific MRH role pairing link, **NOT globally to the entity**." But the decay function drops the role entirely:
```python
def apply_reputation_decay(entity_lct, dimension, last_action_timestamp):   # L673 — no role_lct
```
An entity active in role A but idle in role B would have its role-B reputation decayed (or not) based on entity-global activity — exactly the "global to the entity" reading the doc forbids. This is the **same defect-class as C15's M4** (which fixed the V3 `from` role-agnosticism but did not touch the decay path).

**SDK authority**: `reputation.py` `inactivity_decay(self, entity_lct, role_lct, *, now=…)` (L456) keys decay state by `(entity_lct, role_lct)` (L470). Role-scoped.

**Sub-note (was a separate LOW candidate)**: the `dimension` parameter of `apply_reputation_decay` is never referenced in the body — decay is dimension-uniform. Either drop the param or document that decay is applied per-dimension by the caller.

**Recommendation**: Add `role_lct` to the signature and key decay by `(entity_lct, role_lct)`, matching `compute_current_reputation` + SDK `inactivity_decay`. Drop or justify the unused `dimension` param in the same edit.

#### B-M3 (MEDIUM, autonomous — couples B-I3): §3.2 **Validity** defined as "logical soundness / methodological correctness" — contradicts the canonical "Confirmed Transfer / value delivery" definition

**Location**: §3.2 L183–198 (definition L184; "Increases/Decreases When" L186–196; typical-range L198).

reputation-computation.md §3.2:
> **Definition**: Logical soundness and methodological correctness.
> **Typical Range**: 0.0 (invalid reasoning) to 1.0 (formally valid)

The "Increases When" / "Decreases When" bullets are entirely about *reasoning/method* ("Arguments are logically sound", "Logical fallacies", "Methodological flaws") — **zero** mention of value delivery.

**Canonical authority** — `t3-v3-tensors.md` §3.1 (verified live, L220–224):
> #### Validity (Confirmed Transfer)
> - **Measures**: Actual value delivery and receipt
> - **Updates**: Binary per transaction, averaged over time
> - **Context**: Completion of value transfer cycle

and §3.3 L273: `Validity = 1.0 if value_transferred else 0.0`. The ontology `t3v3-ontology.ttl` L53–54 comments Validity as "soundness of reasoning **and confirmed value delivery**" — i.e. reputation-computation captures only the first half and drops the ATP-linked "confirmed value delivery" core that the canonical tensor spec makes the *operative* (binary-per-transaction) meaning.

This is **pre-canonical drift**: reputation-computation predates the t3-v3 reframing of Validity to "Confirmed Transfer" and was not updated. Validity is a Terminology-Protected V3 dimension (CLAUDE.md), so the divergence is a genuine contradiction, not a permitted reputation-lens elaboration.

**Recommendation**: Realign §3.2 to the canonical "Confirmed Transfer" definition (actual value delivery and receipt; binary per transaction, averaged over time), copying the t3-v3 §3.1 wording. Do this as **one V3-prose-realignment cluster with B-I3** (§3.1 Veracity and §3.3 Valuation prose also drift, more mildly). Add a pointer to `t3-v3-tensors.md §3` as the canonical source for V3 dimension semantics.

---

### LOW

#### B-L1 (LOW, autonomous): factor-name vocabulary incoherence — §4 `high_confidence` modifier is unreachable; §5 emits `exceed_quality` where SDK/vectors use `high_accuracy`

**Location**: §4 veracity modifier L271 (`high_confidence`); §5 `analyze_factors` L435–489; §5 example L502–509.

§5 `analyze_factors` produces only `exceed_quality`, `deadline_met`, `early_completion`, `resource_efficiency`, `high_accuracy`. The §4 rule's veracity modifier keys on `high_confidence` — a factor **nothing in the doc ever emits**, so that modifier can never fire (dead modifier; the §5 example even notes "high_confidence modifier not triggered" L513). Separately, §5 emits `exceed_quality`, but the SDK `analyze_factors` (L170–205) and vector `rep-001` use `high_accuracy` for the quality factor — `exceed_quality` has no SDK/vector counterpart.

**Recommendation**: Pick one quality-factor name (`high_accuracy`, the SDK/vector name) and use it consistently in §4's modifier, §5's `analyze_factors`, and the §5 example; drop or rename `high_confidence`. (If `exceed_quality`/`high_confidence` are genuinely wanted, they must be added to the SDK + vectors — cross-track — so prefer converging on `high_accuracy`.)

#### B-L2 (LOW, autonomous): §5 worked-example `exceed_quality` weight 0.5 contradicts the section's own `analyze_factors` (computes ≈0.021)

**Location**: §5 example contributing-factors L499–506; vs §5 `analyze_factors` L440–443.

`analyze_factors` sets `weight = exceed_ratio = (actual_quality − threshold) / threshold` (L440). With the example's 97% accuracy (L495) and §4's `quality_threshold` 0.95 (L249): `(0.97 − 0.95)/0.95 = 0.021`. But the worked example lists `exceed_quality` weight **0.5** (L502). (The deltas are unaffected — weights gate modifier *presence*, not magnitude — but the listed weight is unreproducible from the stated algorithm.)

**Recommendation**: Either set the example weight to ≈0.021 (recompute normalized_weights across {0.021, 0.3, 0.2}), or add a one-line note that the example's round 0.5/0.3/0.2 weights are illustrative, not `analyze_factors` outputs.

#### B-L3 (LOW, autonomous): §5 computes delta `to` without clamping to [0,1]; SDK clamps and recomputes `change`

**Location**: §5 L362–366 (T3) and L379–383 (V3).

§5 writes `'to': from + delta` directly. The SDK clamps the new value to `[0,1]` and recomputes the effective `change` from the clamp, so a delta that would push a dimension past 1.0 is truncated and the recorded `change` reflects the truncation. The spec can record a `to` > 1.0.

**Recommendation**: Clamp `to` to `[0,1]` and recompute `change = to − from`, matching the SDK, so the per-delta record cannot exceed the dimension range.

#### B-L4 (LOW, autonomous): §5 `high_accuracy` threshold is 0.95 in the spec but 0.5 in the SDK

**Location**: §5 `analyze_factors` L480–487.

§5 appends `high_accuracy` only when `accuracy > 0.95` (L482); the SDK uses a 0.5 threshold. Divergent gate.

**Recommendation**: Reconcile the threshold with the SDK (treat the SDK as authority unless there is a documented reason; if the spec's 0.95 is intended, change the SDK in lockstep — cross-track).

#### B-L5 (LOW, autonomous): §5 step-3 factor-weight normalization is dead code

**Location**: §5 `compute_reputation_delta` step 3, L347–349.

Step 3 computes `factor.normalized_weight = factor.weight / total_weight`, but `compute_dimension_delta` (L403–425) derives the delta purely from rule `base_delta × modifier multipliers` — it never consults `normalized_weight`. The normalization is computed and discarded; it has no SDK counterpart.

**Recommendation**: Either remove the dead normalization step, or wire `normalized_weight` into `compute_dimension_delta` if multi-factor weighting is intended (and reflect that in the SDK — cross-track if so).

#### B-L6 (LOW, autonomous): §9/Summary "on-chain" over-commits to blockchain; the canonical economic layer is ledger-medium-agnostic (also internally inconsistent with §8)

**Location**: §9 Privacy L726 ("All reputation changes on-chain"); Summary L759 ("All changes on-chain and auditable"); vs §8 checklist L702 ("Store ReputationDelta in **ledger**").

`atp-adp-cycle.md` L7 terminology note: value packets "can be implemented as blockchain tokens, **local ledger entries, or other locally appropriate means**." reputation-computation's own §8 uses medium-agnostic "ledger", so §9/Summary "on-chain" is both a canonical over-commit and internally inconsistent.

**Recommendation**: Soften "on-chain" → "recorded in the society ledger" in §9 L726 and Summary L759, matching §8 and atp-adp. (Check whether r7 §4.6 shares the same "on-chain" absolute before a corpus sweep — cross-track note.)

#### B-L7 (LOW, autonomous): §1 schema example carries a zero-change `v3_delta` entry that §5's algorithm would omit

**Location**: §1 Complete Schema L46 (`"validity": {"change": 0.0, …}`); vs §5 L361/L378 (`if delta != 0:`).

The §1 example includes a `validity` entry with `change: 0.0`, but §5 only adds a dimension to the delta map when `delta != 0` (L361 for T3, L378 for V3). So the canonical algorithm would never emit the zero-change entry the schema example shows.

**Recommendation**: Either drop the zero-change `validity` entry from the §1 example, or relax §5 to include zero deltas (the former is simpler and matches the algorithm).

---

### INFORMATIONAL (record-only / cross-track)

| ID | Item | Disposition |
|---|---|---|
| **B-I1** | §9 "Diminishing returns: repeated identical actions yield less reputation" (L720) is asserted but **not implemented anywhere in this doc**; the mechanism lives in `t3-v3-tensors.md §7.1` (`max(0.8^(n−1), 0.1)`, vector t3v3-007) + SDK `diminishing_returns()`. | **autonomous** — add a cross-reference to t3-v3 §7.1; optionally note the per-action delta path here does not itself apply it. |
| **B-I2** | §3.3 Valuation "Typical Range 0.0 to 1.0" (L215) hard-bounds a dimension the canonical spec flags as an **open question** (t3-v3 §3.1 L205–214, §10.2 L580–582: Valuation range omitted pending operator decision; may exceed 1.0). | **DESIGN-Q / cross-track** — couples **carry-C42 D3** (M4 Valuation range). Do NOT clamp here while the canonical question is open; at most soften "Typical Range" wording. |
| **B-I3** | §3.1 Veracity / §3.3 Valuation prose definitions are narrower/differently-emphasised than canonical t3-v3 §3.1 — coherence drift, not contradiction. | **autonomous** — fold into the **B-M3** V3-prose-realignment cluster. |
| **B-I4** | §5 pseudocode `t3InRole`/`v3InRole` are camelCase wire form vs SDK `t3_in_role`/`v3_in_role`. | **autonomous (dialect)** — optional; the doc consistently uses camelCase wire form. Cosmetic. |
| **B-I5** | §6 `select_reputation_witnesses` has no SDK implementation. | **record** — unimplemented spec, not a divergence. Track for §6 → SDK coverage. |
| **B-I6** | §7 `compute_current_reputation` truncates age via `.days` (integer) where SDK uses fractional days. | **autonomous (optional)** — same 30-day constant; minor numeric drift. |
| **B-I7** | `role_pairing_in_mrh` is `Required: Yes` in §1 (L73) but absent from the SDK `ReputationDelta` dataclass. | **cross-track** — shared with r7 (not reputation-specific); track for a ReputationDelta schema reconciliation. |
| **B-I8** | Leading-`+` on JSON numbers (§1/§4/§5). | **NOT scored** — known corpus-wide readability convention (per C15 informational note + C-series calibration). |

---

## §C — Refuted Candidates (overcall-discipline)

Five candidates were **refuted** on adversarial re-read — the cross-doc overcall pattern (C7/C9/C10/C11) held in check:

1. **"ReputationDelta schema contradicts r7 §1.7"** — REFUTED: re-read r7 §1.7; the schemas match.
2. **"§1 `role_pairing_in_mrh` / `link:mrh:` is undefined RDF vocab (C40 carry applies)"** — REFUTED: these are **JSON illustration**, not RDF/SPARQL; the C40 ontology-vocab concern (undefined RDF predicates in Turtle/SPARQL) does not apply to a JSON example field.
3. **"§9 'Each action costs ATP' contradicts atp-adp-cycle.md"** — REFUTED: re-read atp-adp; the claim is consistent.
4. **"Identifier forms inconsistent / new id-scheme finding"** — REFUTED: the `lct:web4:{entity|role|witness|oracle}:`, `link:mrh:`, `txn:0x`, `sha256:` forms are internally consistent; the global id-scheme choice is the known **C33 carry**, not a new finding.
5. **"Inactivity-decay numeric model wrong"** — REFUTED: recomputed (-0.01/month, ×1.5 after 6 months, −0.5 cap, 30-day grace); correct and SDK-aligned (`inactivity_decay`).

---

## Remediation Summary (for the C45 remediation turn)

**13 autonomous-actionable** (suggested grouping):

| ID | Sev | One-line fix | Cluster |
|---|---|---|---|
| B-M1 | M | §4+§5: reconcile rule structure to SDK `t3_impacts`/`v3_impacts`; §5 read `rule.t3_impacts[dim]`/`v3_impacts[dim]` | algorithm |
| B-M2 | M | §7: add `role_lct` to `apply_reputation_decay`, key by (entity, role); drop unused `dimension` param | algorithm |
| B-L3 | L | §5: clamp `to` to [0,1], recompute `change` (SDK parity) | algorithm |
| B-L4 | L | §5: reconcile `high_accuracy` threshold 0.95→SDK 0.5 | algorithm |
| B-L5 | L | §5: remove dead factor-weight normalization (step 3) | algorithm |
| B-L1 | L | §4/§5: converge quality-factor name on `high_accuracy`; drop unreachable `high_confidence` | factor-vocab |
| B-L2 | L | §5 example: fix `exceed_quality` weight 0.5→≈0.021 or annotate as illustrative | factor-vocab |
| B-L7 | L | §1: drop zero-change `validity` entry (or relax §5) | schema |
| B-M3 | M | §3.2: realign **Validity** to canonical "Confirmed Transfer" (t3-v3 §3.1/§3.3) | V3-prose |
| B-I3 | INFO | §3.1/§3.3: align Veracity/Valuation prose to canonical (with B-M3) | V3-prose |
| B-L6 | L | §9/Summary: "on-chain"→"society ledger" (match §8 + atp-adp) | wording |
| B-I1 | INFO | §9: cross-reference diminishing-returns to t3-v3 §7.1 / vector t3v3-007 | wording |
| B-I6 | INFO | §7: fractional-day age (optional, SDK parity) | optional |

**3 DESIGN-Q / cross-track (do NOT self-resolve in C45)**:
- **B-I2** Valuation range [0,1] hard-bound → couples **carry-C42 D3** (M4 Valuation 3-way range, operator-blocked). At most soften "Typical Range"; do not clamp while the canonical question is open.
- **B-I7** `role_pairing_in_mrh` Required-but-absent-from-SDK-`ReputationDelta` → shared with r7; track for a ReputationDelta schema reconciliation (cross-track).
- **B-I5** §6 witness-selection unimplemented in SDK → §6 SDK-coverage gap (record).

**Authority note**: every B-M*/B-L* fix converges the spec toward the SDK (`reputation.py`/`r6.py` + `reputation-operations.json` vectors) and the canonical `t3-v3-tensors.md` — not vice versa. No SDK/.ttl/vector edits are part of the C45 remediation (those are cross-track).

---

*C13→C15→C44 lineage: C13/C15 established the §5/§7 algorithm + V3-naming wire-correctness; C44 reaches the structural layer (rule-schema access, role-scoped decay) and the cross-doc semantic layer (Validity definition vs the now-canonical t3-v3 "Confirmed Transfer"). The C15 remediation (#237) is fully durable.*
