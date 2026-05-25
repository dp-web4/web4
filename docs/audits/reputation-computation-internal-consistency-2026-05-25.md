# C15: reputation-computation.md Internal Consistency Audit

**Date**: 2026-05-25
**Auditor**: Autonomous session (legion-web4-20260525-120044)
**Document**: `web4-standard/core-spec/reputation-computation.md` (760 lines)
**Cross-references verified** (each re-read against the live file at the cited line):
- `web4-standard/implementation/sdk/web4/reputation.py` — the SDK's full rule-engine reputation path: `ReputationEngine`, `ReputationStore`, `analyze_factors`, `process_action_outcome` (the module docstring names this file as the implementation of *this* spec).
- `web4-standard/implementation/sdk/web4/r6.py` — `ReputationDelta`, `TensorDelta`, `R7Action`, `Role`, `_generate_id`.
- `web4-standard/implementation/sdk/web4/trust.py` — `T3`, `V3`, `_clamp` (V3 dimension fields).
- `web4-standard/ontology/t3v3-ontology.ttl` — canonical V3 dimension names (RDF backbone).
- `web4-standard/core-spec/t3-v3-tensors.md` §3.1, §3.3 — canonical V3 dimension definitions (the C13 audit target, remediation merged #232).
- `web4-standard/core-spec/r7-framework.md` §1.7 — the parent R7 Reputation component (the C14 audit target, remediation merged #234).

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| HIGH | 1 | §7 `compute_current_reputation` aggregates deltas as a recency-weighted **average**, contradicting its own example outputs and the SDK (which the SDK explicitly documents as a spec bug) |
| MEDIUM | 4 | Third V3 dimension named `value` not canonical `valuation`; §6 `roleType` vs the doc's own `role_lct`; `action_id` sourced from ledger txHash vs SDK's pre-execution id; §5 V3 `from` is role-agnostic while T3 `from` is role-contextualized |
| LOW | 3 | §5 algorithm omits Required schema fields; §7 "30-day half-life" label vs 30-day time-constant math; §5 worked example cites an undefined rule with an inverted modifier→dimension mapping |

**Cross-audit calibration note**: This audit follows C12 (r6, #229/#231), C13 (t3-v3, #230/#232), and C14 (r7, #233/#234). Two candidate issues were deliberately **demoted to non-defects** to avoid the recurring C-series cross-document overcall (C7/C9/C10/C11):
- **Leading `+` on JSON numbers** (e.g. §1 `"change": +0.01`, `"net_trust_change": +0.035`) is invalid per RFC 8259, but it is a **corpus-wide readability convention** — r7 §1.7 (just remediated in C14) uses the identical `+0.01` form and C14 did not flag it. Treating it as a reputation-computation-specific defect would be inconsistent; recorded as an informational note (below), not a finding.
- **L2 "30-day half-life"** label/math imprecision is **shared with the SDK** (`reputation.py` uses `DEFAULT_HALF_LIFE_DAYS = 30.0` + `exp(-age / half_life_days)` identically), so it is a shared naming convention, not a spec-vs-SDK divergence. Kept as LOW (the in-file label is still mathematically loose) but explicitly scoped as non-divergent.

Severities for the V3-misnaming (M1) and `roleType` (M2) classes are calibrated against C14, which rated the same classes MEDIUM and HIGH respectively in r7 — see each finding for why this file's instances land where they do.

Every cross-reference below was re-read against the live file at the cited line.

---

## HIGH Findings

### H1: §7 `compute_current_reputation` averages deltas — contradicts its own example AND the SDK (SDK-documented spec bug)

**Location**: §7 lines 596–639 (esp. line 635); contradicted by the example at lines 643–658 (outputs 0.90 / 0.20)
**Severity**: HIGH

The aggregation function builds a recency-weighted sum of delta **changes** and divides by the weight sum:

```python
for delta in deltas:
    age_days = (now() - delta.timestamp).days
    recency_weight = math.exp(-age_days / 30.0)
    weighted_sum += delta.change * recency_weight   # delta.change is a CHANGE (~0.01)
    weight_sum   += recency_weight

current_value = weighted_sum / weight_sum if weight_sum > 0 else 0.5   # line 635
return max(0.0, min(1.0, current_value))
```

`weighted_sum / weight_sum` is the recency-weighted **average of the delta magnitudes**, not an accumulated reputation level. With deltas on the order of ±0.01 (as every example in the doc shows), this returns ~0.01 — and worse, a brand-new pairing returns `0.5` (line 622), so the *first* positive +0.01 action would **drop** the entity's reputation from 0.5 to ~0.01. The doc's own example claims this same function returns **0.90** ("highly trained financial analyst", line 650) and **0.20** ("no medical training", line 655) — absolute levels the algorithm as written cannot produce.

**SDK confirmation**: `web4-standard/implementation/sdk/web4/reputation.py` `ReputationStore.current()` computes the identical `weighted_sum / weight_sum` (lines 438–453) and then **explicitly documents that the spec is wrong**:

```python
# lines 450-454
# The spec computes: weighted_sum / weight_sum as current value.
# But deltas are CHANGES, not absolute values. We apply them to
# the neutral baseline of 0.5.
aggregated = weighted_sum / weight_sum
return _clamp(0.5 + aggregated)
```

The SDK returns `_clamp(0.5 + aggregated)`; the spec returns the bare average. The SDK is the authority (its module docstring names this file as the implementation of `reputation-computation.md`).

**Impact**: An implementer following §7 literally produces reputation scores collapsed toward the delta magnitude (~0.01) instead of accumulating from the neutral baseline, and the function regresses reputation on the first positive action. This is a correctness defect, not a wording nit.

**Remediation**: Change line 635 to apply the aggregate to the neutral baseline, mirroring the SDK: `current_value = 0.5 + (weighted_sum / weight_sum)` (with the existing `[0.0, 1.0]` clamp). Update the prose ("time-weighted aggregation of deltas") to state that deltas accumulate onto the 0.5 baseline. (Note: even baseline+average is a modeling choice — the example's 0.90/0.20 imply *summation* of many deltas, which neither the spec nor SDK does; at minimum make the algorithm and its example self-consistent and match the SDK.)

---

## MEDIUM Findings

### M1: Third V3 dimension named `value` / `Value` — canonical name is `valuation`

**Location**: §1 schema line 46–47 (`"value": {...}`); §3.3 heading line 200 ("### 3.3 Value") + body lines 200–215; §4 exceptional-performance rule line 305 (`value: +0.03`); §5 algorithm line 370 (`['veracity', 'validity', 'value']`); §V3 Interpretation lines 217–235; Summary line 746 ("V3 (value)")
**Severity**: MEDIUM

The document names the third V3 dimension **`value`** (lowercase in schema/algorithm, "Value" as the §3.3 dimension definition heading). The canonical name is **`valuation`**:

- **Ontology (RDF backbone)** `web4-standard/ontology/t3v3-ontology.ttl`: line 29 `"... 3 root dimensions (Valuation/Veracity/Validity) ..."`; line 47 `web4:Valuation a web4:Dimension`; line 125 `web4:valuation a rdf:Property`. There is **no** `web4:value` dimension/property.
- **t3-v3-tensors.md** (C13 target): §3.1 line 185 `#### Valuation (Subjective Worth)`; §3.3 line 257 `1. **Valuation** = ...`; parameter table line 532 `valuation=0.3`.
- **SDK** `web4-standard/implementation/sdk/web4/reputation.py` line 286: `for dim in ("veracity", "validity", "valuation")`; line 596 `"valuation": current_v3.valuation`. `trust.py` `V3` exposes `valuation` (read by `reputation.py` line 286/300).
- **CLAUDE.md** canonical equation table: V3 = "Valuation/Veracity/Validity".

Note the precise distinction: **"Value tensor" / "V3" as the tensor's full name is correct** (§3 heading "Value Tensor (V3)" is fine). It is only the **third dimension** that must be `valuation`, not `value`. T3/V3 dimension names are Terminology-Protected (CLAUDE.md).

**Calibration**: C14 rated the identical class ("V3 dimension misnamed") **MEDIUM** in r7, where it was a single example occurrence. Here it is more pervasive — the §3.3 definitional section, the §1 schema, a §4 rule, and the §5 algorithm all use `value`. Kept at MEDIUM for cross-audit consistency, but flagged as definitional/pervasive so the remediation is understood as a mechanical-but-broad rename (`value` → `valuation` everywhere it denotes the third V3 dimension, leaving "Value tensor" intact).

**Remediation**: Rename the third V3 dimension `value`→`valuation` in §1 schema, §3.3 heading + body, §4 rule, §5 algorithm, §V3 interpretation, and Summary. Do **not** touch "Value tensor"/"V3" tensor-name usages.

### M2: §6 `action.role.roleType` — inconsistent with the doc's own `role_lct` and the SDK/r7 `roleLCT`

**Location**: §6 line 540 (`role_validators = get_validators_for_role(action.role.roleType)`)
**Severity**: MEDIUM

The witness-selection pseudocode reads the role via `action.role.roleType`. But this document's own §1 schema and field table use **`role_lct`** (line 24 `"role_lct"`, line 72 field `role_lct | LCT | Yes`), and §7 is built entirely around `role_lct`. So §6 is **internally inconsistent** with the rest of the doc.

**SDK confirmation**: `web4-standard/implementation/sdk/web4/r6.py` `Role` (line 234) has only `role_lct` (serialized as `roleLCT`, line 243) — **no `roleType` field**. `R7Action` validation (lines 766–767) requires `role.role_lct`. The C14 r7 remediation (#234) renamed `roleType`→`roleLCT` in r7; r7 now uses `roleLCT` (9 occurrences).

**Why MEDIUM, not HIGH** (C14 rated `roleType` HIGH in r7): in r7 the offending `roleType` appeared in **wire-JSON examples** an implementer would copy into objects the SDK cannot consume. Here it is in **§6 witness-selection pseudocode** (a field access in illustrative code), with lower blast radius. It is still both internally inconsistent and SDK-divergent.

**Out-of-scope context for the remediation lead**: `roleType` also persists in `mcp-protocol.md` line 306 and `dictionary-entities.md` line 418 (separate, un-audited files — not part of this audit; noted so the eventual corpus-wide cleanup is on the radar).

**Remediation**: Change §6 line 540 to `get_validators_for_role(action.role.role_lct)` (or `roleLCT` if matching wire casing), consistent with §1/§7 and the SDK.

### M3: §5 `action_id = result.ledgerProof.txHash` — diverges from the SDK's pre-execution action id

**Location**: §5 algorithm line 387 (`reputation.action_id = result.ledgerProof.txHash`); §1 field table line 76 ("Transaction that caused the change")
**Severity**: MEDIUM

The algorithm sources `action_id` from the **ledger transaction hash** produced *after* settlement (`result.ledgerProof.txHash`).

**SDK confirmation**: `web4-standard/implementation/sdk/web4/reputation.py` line 319 sets `action_id=action.action_id`. In `web4-standard/implementation/sdk/web4/r6.py`, `R7Action.action_id` is generated in `__post_init__` (lines 744–745) via `_generate_id()` (lines 747–748) = `sha256` over `f"{self.role.actor}:{self.request.action}:{self.request.nonce}:{self.timestamp}"` — a **pre-execution**, nonce-derived id, available before any ledger write. The spec's `result.ledgerProof.txHash` is a *different* value computed at a *different* time (post-settlement).

**Scoped honestly**: the JSON representation is *not* in conflict — both `reputation-computation.md` §1 (line 34) and r7 §1.7 use `"action_id": "txn:0x..."`. The divergence is at the **source/timing level**: the spec algorithm derives `action_id` from a post-execution ledger artifact, while the SDK uses the action's own pre-execution generated id. (This also matters for H1/L1: in the SDK the id exists before reputation is computed; in the spec algorithm it cannot, since it depends on the ledger write.)

**Remediation**: Source `action_id` from the action's own identifier (set at request time), e.g. `reputation.action_id = action.action_id`, matching the SDK. If the intent is genuinely the ledger txHash, reconcile with the SDK and r7 and document the timing.

### M4: §5 V3 `from` is role-agnostic while T3 `from` is role-contextualized — contradicts the doc's CRITICAL principle

**Location**: §5 algorithm — T3 `from` at line 364 (`action.role.t3InRole[dimension]`) vs V3 `from` at line 381 (`get_current_v3(action.role.actor, dimension)`)
**Severity**: MEDIUM

When assembling deltas, the T3 path reads the prior value from the **role pairing** (`action.role.t3InRole[dimension]`), but the V3 path reads it via `get_current_v3(action.role.actor, dimension)` — keyed on the **actor**, with no role argument. This contradicts the document's own emphasised principle:

> **CRITICAL**: Reputation is **role-contextualized**. The `t3_delta` and `v3_delta` apply to the specific MRH role pairing link, NOT globally to the entity. (§1 line 87)

A V3 lookup keyed only on the actor is exactly the "global to the entity" reading the spec forbids.

**SDK confirmation**: `web4-standard/implementation/sdk/web4/reputation.py` reads **both** tensors from the role: T3 from `action.role.t3_in_role` (line 273) and V3 from `action.role.v3_in_role` (line 300). The SDK is symmetric and role-contextualized for both.

**Remediation**: Make the V3 `from` read from the role pairing, mirroring T3 — e.g. `action.role.v3InRole[dimension]` (and rename the helper or drop it) so both tensors are role-contextualized as §1 requires.

---

## LOW Findings

### L1: §5 algorithm omits Required schema fields (`role_lct`, `action_type`, `action_target`, `timestamp`)

**Location**: §5 algorithm assembly lines 386–394; vs §1 field table lines 72–85
**Severity**: LOW

`compute_reputation_delta()` sets `subject_lct`, `action_id`, `rule_triggered`, `reason`, `t3_delta`, `v3_delta`, `contributing_factors`, `net_trust_change`, `net_value_change` — but never sets `role_lct`, `action_type`, `action_target`, or `timestamp`, all marked **Required: Yes** in the §1 field table (lines 72–76, 85). `role_lct` is the load-bearing role-contextualization key the doc calls CRITICAL (§1 line 87), yet the canonical algorithm never populates it.

**SDK confirmation**: `web4-standard/implementation/sdk/web4/reputation.py` `ReputationEngine.evaluate()` (lines 314–326) sets all four: `role_lct=action.role.role_lct`, `action_type=action.request.action`, `action_target=action.request.target`, `timestamp=ts`. (`net_trust_change`/`net_value_change` are computed `@property`s on `ReputationDelta` — `r6.py` lines 602–608 — so the SDK does not set them explicitly; the spec setting them by hand is consistent in value.)

**Remediation**: Add `role_lct`, `action_type`, `action_target`, and `timestamp` assignments to the §5 algorithm, matching the SDK, so the canonical algorithm produces a delta that satisfies its own Required-field contract.

### L2: §7 "30-day half-life" comment is a 30-day time constant, not a half-life

**Location**: §7 line 630 (`recency_weight = math.exp(-age_days / 30.0)  # 30-day half-life`)
**Severity**: LOW

`exp(-age/30)` decays to `1/e` (~0.368) at 30 days; the true **half-life** (decay to 0.5) is `30·ln 2 ≈ 20.8` days. So "30-day half-life" mislabels a 30-day **time constant**.

**Non-divergence note**: the SDK shares this exact naming — `web4-standard/implementation/sdk/web4/reputation.py` line 360 `DEFAULT_HALF_LIFE_DAYS = 30.0` and line 443 `recency_weight = math.exp(-age_days / half_life_days)`. So this is a **shared label/math imprecision**, not a spec-vs-SDK divergence; the in-file comment is still loose.

**Remediation** (cosmetic): rename to "30-day time constant" in the comment, OR make it a true half-life via `math.exp(-age_days * math.log(2) / 30.0)` (equivalently `0.5 ** (age_days / 30.0)`). If the formula is changed, change the SDK in lockstep to keep them aligned (separate session, out of this audit's scope).

### L3: §5 "Example Computation" cites an undefined rule with an inverted modifier→dimension mapping

**Location**: §5 "Example Computation" lines 488–515 (esp. lines 493, 506–507)
**Severity**: LOW

The worked example is attributed to rule `successful_model_training` (line 493), which is **never defined** in the document — so its base deltas and modifiers cannot be traced. Worse, its modifier→dimension assignments **invert** the only rule the doc does define (§4 `successful_analysis_completion`, lines 245–278):

- §5 example applies **`exceed_quality` 1.2 and `early_completion` 1.3 to `training`** and **`deadline_met` 1.5 to `temperament`** (lines 506–507).
- §4's defined rule applies **`deadline_met` 1.5 and `exceed_quality` 1.2 to `training`**, and **`early_completion` 1.3 to `temperament`** (lines 254–265).

So the example silently swaps which dimension `deadline_met` vs `early_completion` modifies, relative to the doc's only concrete rule. A reader cannot reconcile the numbers with any defined rule.

**Remediation**: Either define `successful_model_training` explicitly (with its base deltas/modifiers) so the arithmetic is traceable, or rebuild the example on the existing §4 `successful_analysis_completion` rule using its actual modifier→dimension mapping.

---

## Informational (not a finding)

**Leading `+` on JSON numbers.** §1 (`"change": +0.01`, `"net_trust_change": +0.035`, etc.) and §4 use leading-`+` numbers, which are invalid per RFC 8259 (a JSON number's integer part may not begin with `+`). This is intentionally **not** scored: it is a corpus-wide readability convention to signal "positive delta", and r7 §1.7 — just remediated in C14 — uses the identical `+0.01` form without C14 flagging it. Scoring it here alone would be inconsistent cross-audit treatment. If the project later decides to enforce strict JSON validity, it should be a single corpus-wide pass (r7, reputation-computation, and any other affected spec), not a reputation-computation-specific fix.

---

## Remediation Summary (for the next session)

| ID | Severity | One-line fix |
|----|----------|--------------|
| H1 | HIGH | §7 line 635: `0.5 + (weighted_sum/weight_sum)` baseline (match SDK `reputation.py` L454); fix prose + example self-consistency |
| M1 | MEDIUM | Rename third V3 dimension `value`→`valuation` (§1, §3.3, §4, §5, §V3-interp, Summary); leave "Value tensor" intact |
| M2 | MEDIUM | §6 line 540: `roleType`→`role_lct` (match §1/§7 + SDK) |
| M3 | MEDIUM | §5 line 387: `action_id` from `action.action_id`, not `result.ledgerProof.txHash` (match SDK) |
| M4 | MEDIUM | §5 line 381: V3 `from` read role-contextualized `v3InRole`, mirroring T3 (match SDK symmetry) |
| L1 | LOW | §5: also set `role_lct`/`action_type`/`action_target`/`timestamp` (match SDK `evaluate()`) |
| L2 | LOW | §7 line 630: relabel "time constant" or make a true half-life (keep SDK in lockstep) |
| L3 | LOW | §5: define `successful_model_training` or rebuild example on §4's defined rule |

**Suggested grouping**: H1 + M4 + L1 all touch the §5/§7 algorithm and are best done together (algorithm-correctness cluster). M1 is a standalone mechanical rename. M2/M3/L2/L3 are independent one-liners. The remediation should treat the SDK (`reputation.py`/`r6.py`) as authority throughout — every fix above converges the spec toward the SDK, not vice versa.
