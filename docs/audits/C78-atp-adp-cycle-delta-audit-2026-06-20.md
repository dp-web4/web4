# C78 Audit: `atp-adp-cycle.md` First Delta Re-Audit (prior C34)

**Date**: 2026-06-20
**Auditor**: Autonomous session (Legion, web4 track) — multi-agent finder workflow (4 dimensions × refute-by-default) + auditor synthesis/verification.
**Document**: `web4-standard/core-spec/atp-adp-cycle.md` (752 lines)
**Baseline**: C34 delta re-audit (`docs/audits/C34-atp-adp-cycle-audit-2026-06-06.md`, 12 actionable: 1H/2M/6L/3I + X1), remediated PR #277 (`57690128`, 9 AUTONOMOUS findings, +42/−18).
**SDK alignment**: `web4-standard/implementation/sdk/web4/atp.py` (394 lines).
**Method**: C-series delta re-audit. §A re-verifies every C34 finding against the LIVE spec **token-by-token against the #277 diff** and **extended to the SDK mirror** (C56/C64 lesson), plus **bidirectional carry re-verification** of the deferred items (M2 DESIGN-Q, X1 C33 cross-track, I2 SDK-track). §B surfaces NEW findings; finders were fed the DEMOTED/refuted C34 list to avoid re-derivation. Design questions are ROUTED, not self-resolved. This is an AUDIT turn — **no spec or SDK edits were made**.

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 0 | — |
| MEDIUM | 4 | B1, B2, B3, B4 |
| LOW | 4 | B5, B6, B7, B8 |
| INFO | (in §E) | — |
| **NEW actionable** | **8** | |

**Delta result (§A)**: All **9 C34 AUTONOMOUS findings HELD** (verified against the #277 diff, no regression). The 3 deferred C34 items re-verified as **still open**: M2 (slashing-authority DESIGN-Q), X1 (`lct:web4:` identifier → C33), I2 (SDK "three sub-pools" docstring). No remediation-introduced regressions (cf. [[feedback_remediation_introduced_regression]]).

**Headline (FLAGSHIP — B1)**: Since C34, the corpus added `mcp-protocol.md` §7.7 (the burst-2 inter-society amendment), whose §7.7.1 is **explicitly tagged Normative** — "rates are referent-grounded, not abstract … *This is NOT the Web4 model*" (rejecting floating bilateral FX). `atp-adp-cycle.md` §5.2/§5.3 still present exactly that rejected abstract-FX model ("Floating | Market-determined rate", a single uniform `get_exchange_rate`). This is a **new normative contradiction** introduced by corpus evolution that a single-file read cannot see — the canonical delta-re-audit dividend.

**Classification split**: 5 AUTONOMOUS · 3 DESIGN-Q (B1, B2b, + carried M2 / ISP-B10) · 3 CROSS-TRACK (B1, B4, B6-SDK) · 2 SDK-track (B3, carried I2). (Items appear under multiple buckets where they have multiple legs.)

**Anti-padding**: 4 finder agents returned ~20 raw candidates; refuted/deflated at synthesis: "non-accumulative absolute vs stake-limits" (→INFO), demurrage-rationale, conservation-vs-minting, §7.4 single-rate (folded into B1 as wire echo), errors.md taxonomy (C34 ruling holds). 0 HIGH — the file's numeric/normative core is internally sound; the live defects are scoping-gaps and cross-spec drift, not arithmetic.

---

## §A — C34 Baseline Delta-Persistence

Each C34 AUTONOMOUS finding re-verified against the live spec **and** the exact #277 hunk that remediated it (not just "is the edit present").

| C34 ID | Title | Status | Live evidence |
|--------|-------|--------|---------------|
| **H1** | `slash_atp` undefined `witnesses` | **HELD** | L175 `def slash_atp(caller, violator, amount, evidence, witnesses):` + docstring L181. |
| **M1** | V3 dim `value`→`valuation` | **HELD** | L104, L154, L359 all `valuation`; T3 dims `training`/`talent`/`temperament` correct throughout. (Corpus note: #277 recorded the *same* drift at `mcp-protocol.md` as a cross-track carry — see B-track note below.) |
| **L1** | `regulate_flow` undefined `target_velocity` + `apply_demurrage` collision | **HELD** | L275/277 `self.law.target_velocity`; free fn renamed `apply_demurrage_decay` (L297) with disambiguation docstring. |
| **L2** | §5.1↔§5.3 exchange-rate direction/units | **HELD** | L427 inline direction note (CITY-per-NATION; inverse 0.001); L462-463/470 `get_exchange_rate` target-per-source convention stated. |
| **L3** | tensor-delta notation inconsistent | **HELD (substantially)** | §4.2 dotted form → nested `{"t3"/"v3":{dim:delta}}` (L359-361). Residual: §2.2 uses flat **function-kwargs** `t3_delta=/v3_delta=` — legitimately a call signature, not a data dict; not a defect. |
| **L4** | §4.3 `cf. §6.3` misdirect | **HELD** | L401 now "(see §6.2 on economic laws)". |
| **L5** | slashing destruction/conservation unstated | **HELD** | L211-215 supply-accounting note: slashed ATP removed from `total_supply`, outside the transfer-conservation invariant. |
| **L6** | JSON `"type"` vs `"@type"` | **HELD** | L41-46 "illustrative plain JSON vs JSON-LD wire" note added. |
| **I1** | §2.1 `poolAllocation` vs §3.1 `allocations` vocab | **HELD (partial)** | §2.1 `available`→`circulating` (L64), now a subset of §3.1's vocabulary. §2.1 still carries `total` where §3.1 says `total_supply` — minor residue, folded into B5 pool-model finding. |

**Deferred C34 items — bidirectional re-verification:**
- **M2** (slashing authority — DESIGN-Q): **STILL OPEN.** §2.4 gates on generic `has_slashing_authority(caller)` (L184); §6.1 lists `slash_violations` as a *monetary-authority* power capped `max_slash_per_event: 10000` (L511); §7.3 MAY-list adds "Societies MAY delegate monetary authority" (L609). The §2.4 path caps only at `get_entity_stake(violator)` and **never references** the §6.1 cap — so the cap is structurally unenforced by the only executable path. Re-confirmed underspecified; remains operator DESIGN-Q.
- **X1** (`lct:web4:` identifier → C33 B-H1): **STILL OPEN.** Uniform `lct:web4:<class>:<id>` use throughout. Rides the corpus-wide C33 identifier decision (also C74-B13/14/15, C76-N15). Carry only.
- **I2** (SDK "three sub-pools" docstring): **STILL PRESENT.** `atp.py:49-52` "ATP tokens exist in three sub-pools: available, locked, adp" still reads against §7.1's two-state model (the line-54 invariant `total = available + locked` is itself correct). SDK-track carry — see B3.
- **I3** (illustrative tensor-delta magnitudes): no action, by-design illustration. No change.

**Verdict**: Exemplary remediation; zero regression of any C34 finding's substance. The NEW findings below are (a) cross-spec drift that only became visible after the post-C34 mcp §7.7 amendment, and (b) a clustered-read scoping gap in the §7.1 MUST list that the C34 section-by-section pass did not surface.

---

## §B — NEW Findings

### B1 — *(FLAGSHIP)* §5 abstract-FX exchange model contradicts mcp §7.7.1 **normative** referent-grounding — MEDIUM, CROSS-TRACK / DESIGN-Q

**atp-adp**: §5.2 exchange-models menu (L444-449) = Fixed Peg / **Floating ("Market-determined rate", "Independent economies")** / Basket / **Algorithmic ("Formula-based")**; §5.1 (L426-435) instantiates `mechanism:"floating"`, `adjustment:"daily"`, a standing `initial_rate`; §5.3 (L464-471) applies a **single uniform** `get_exchange_rate(source,target)` (`target_atp = amount * rate`).

**mcp-protocol.md §7.7.1** (L524-528), scope-tagged **"Normative — the referent-grounded model IS the Web4 model; this is a design invariant, not WIP"** (L514): *"two societies maintain a floating bilateral rate `ATP_A : ATP_B` independent of any particular transaction, periodically renegotiated, applied uniformly to all cross-society activity. **This is NOT the Web4 model.**"* Web4 rates are **grounded in the substance of the R6/R7 action** via a **common referent**, with **per-transaction scoping ideal** (L540).

**Why real (refute-survived)**: The WIP caveat on §7.7 covers *wire schemas/error codes* (§7.7.3/§7.7.7), explicitly **not** §7.7.1 (tagged Normative) — so "atp-adp needn't track a draft" fails. atp-adp §5.2/§5.3 present precisely the abstract-bilateral model §7.7.1 names and rejects, **with zero cross-reference** to mcp or referents. Reinforced on two sides: (i) **ISP §4.1** (L191) "ATP is a **unit of account, not a medium of exchange** with intrinsic value" — a "market-determined floating rate" is the definition of a tradable medium of exchange; (ii) atp-adp's **own §9.2** (L648) lists "Speculation (**no secondary markets**)" as a prevented anti-pattern, in tension with §5.2's "Market-determined rate". Not caught by C34 (mcp §7.7 postdates it; C34-L2 only fixed §5.1↔§5.3 unit direction). The §7.4 `atp_settlement` two-valuations-of-a-referent structure (mcp L446) is the wire echo of the same root — folded here, not a separate finding.

**Routing — CROSS-TRACK / DESIGN-Q (do NOT self-resolve)**: atp-adp §5 should be **reframed as referent-grounded** (or explicitly scoped as a society-*internal* currency-pair convenience that does not describe inter-society settlement), in coordination with mcp §7.7 + ISP §4. atp-adp cannot unilaterally pick the model — this is the canonical inter-society axis the other two specs now own. **Operator question**: Is atp-adp §5 meant to describe inter-society settlement at all (in which case it must adopt referent-grounding and drop the floating/algorithmic FX menu), or only intra-society multi-currency bookkeeping (in which case it must say so and defer cross-society exchange to mcp §7.7 / ISP)? *Subsumes carried ISP-B11.*

### B2 — §7.1 MUST-list is scoped as if the work-cycle is the only ATP-state path; 3 non-work-cycle paths exist and only slashing was reconciled — MEDIUM, AUTONOMOUS (a) + DESIGN-Q (b)

§7.1 MUSTs: #4 "Charging MUST require value proof" (L584), #5 "Discharging MUST occur through R6 transactions" (L585), #6 "Value MUST be tracked through T3/V3 tensors" (L586). These read as if §2.2 (charge) / §2.3 (discharge) are the *only* ATP↔ADP transitions. But the spec defines **four** state-changing paths, and only **slashing** (§2.4) received a reconciling carve-out (the L211-215 supply-accounting note). The other two are unreconciled:

- **(b) demurrage** §3.3 (L309-310 `# Convert ATP to ADP` / `convert_to_adp`) performs the §2.3-defined ATP→ADP discharge, **time-triggered, outside any R6 transaction** → conflicts with MUST #5. → **AUTONOMOUS**: add a carve-out note (parallel to the §2.4 note) stating demurrage decay is a non-R6, time-triggered discharge.
- **(a) cross-society exchange** §5.3 (L475-476) `pool.discharge(source_atp)` / `pool.charge(target_atp)` charges the target pool with **no `value_proof`**, discharges the source **outside R6**, and performs **no tensor update** — bypassing MUSTs #4/#5/#6. → **DESIGN-Q**: is exchange a value-*move* exempt from the value-*create* MUSTs, or must it satisfy them? (Couples to B1; if B1 reframes §5 the exemption should be stated there.)

**Why real (refute-survived)**: The escrow note (L588-594) disclaims only MUST #1 (two-state); the illustrative-JSON note (L41-46) is scoped to `TokenMinting`/`R6Transaction` event objects, not §3.3/§5.3. The authors demonstrably knew non-work-cycle transitions need reconciling (they did it for slashing) — the asymmetry is the defect. This is the central clustered-read finding (two independent finders converged).

### B3 — SDK `atp.py` "canonical implementation" overclaims; it omits the entire §2 lifecycle — MEDIUM, SDK-track

`atp.py:4` asserts "Canonical implementation per … atp-adp-cycle.md", but `__all__` (L20-33) exposes only `ATPAccount`, `transfer`, `sliding_scale`, `check_conservation`, `sybil_cost`, `fee_sensitivity`, `energy_ratio`. **None** of the spec's normative lifecycle operations exist: no `mint_adp`, no value-proof-gated `charge_atp`, no R6-gated discharge, no `slash_atp`; **every §7.1 MUST is unimplemented**. The module is, in substance, a transfer-arithmetic + test-vector library (tagged `atp-001..015`), not an implementation of the spec's defining operations. **Routing — SDK-track**: scope the docstring to "ATP value-arithmetic / test-vector layer" (or add the lifecycle). NEW: C34's SDK-alignment dimension used `atp.py` as the alignment target without flagging that it omits the lifecycle entirely.

### B4 — SDK `recharge()` does rate-based ADP→ATP with no value proof, contradicting §7.1 MUST #4 — MEDIUM→LOW, CROSS-TRACK

`atp.py:117-128` `recharge(rate=0.1, max_multiplier=3.0)`: `raw_recharge = initial_balance * rate`, credited straight to `available` (charged ATP) — no authority check, no `validate_value_proof`, no T3/V3 delta. This is the inverse of every gate §2.2 / §7.1 #4 places on ADP→ATP charging, and against §1.3/§9 "value flows through work". Same family as B2 (non-work-cycle ATP creation), on the SDK side. The spec defines **no** passive-recovery ADP→ATP path. **Routing — CROSS-TRACK**: either the SDK gates `recharge` (or renames it to a non-charging primitive), or the spec acknowledges a passive-recovery model and scopes MUST #4 to the value-creation path. (Spec L7 names "recharge" only as the point where ADP metadata "is cleared" — it does not authorize free ATP regeneration.)

### B5 — Pool data model: §3.1 nested (`state_distribution.ADP`) vs §3.2 flat (`self.pools['ADP']`) — LOW, AUTONOMOUS

§3.1 (L226-237) nests states under `state_distribution:{ATP,ADP}` and allocations under `allocations:{…}`; §3.2 `mint_adp` (L264-265) mutates `self.pools['ADP']` and `self.pools['total_supply']` as **flat** keys. `total_supply` is consistent across both; `ADP` is not (nested in §3.1, flat in §3.2 — it would be `self.pools['state_distribution']['ADP']`). The code half-agrees with §3.1's shape, the signature of an inconsistency rather than a deliberate alternate model; and `mint_adp` never touches `allocations.circulating`, silently breaking §3.1's "allocations sum == total_supply" after a mint. Convergent (2 finders). Neither path is covered by the illustrative-JSON disclaimer. **Remediation**: harmonize §3.2 to the §3.1 nested form (the documented pool architecture). *Absorbs I1's `total`/`total_supply` residue.*

### B6 — `charge_rate` denotes ≥2 distinct quantities; SDK adds a third name `energy_ratio` for one of them — LOW, AUTONOMOUS (+ CROSS-TRACK SDK leg)

§3.1 metric `"charge_rate": 0.15 // ATP/(ATP+ADP): fraction of supply charged` (L240) is a dimensionless **state ratio**; §2.2 `charge_rate = get_society_charge_rate(...)` with `atp_amount = adp_amount * charge_rate` (L87-88) is a **conversion multiplier**; §6.1 power `set_charge_rates` (L502) and §6.2 `charging_rules` (L534-538) refer to the latter. A reader cannot tell whether `set_charge_rates` sets the 0.15-style ratio or the per-value-type multipliers. The SDK compounds this: `energy_ratio` (`atp.py:72-84,329-338`) computes exactly the §3.1 `ATP/(ATP+ADP)` quantity under a **third** name, with no alias note either way. Convergent (all 3 finders). **Remediation — AUTONOMOUS**: rename the §3.1 metric (e.g. `charged_fraction`) to free `charge_rate` for the conversion meaning. **CROSS-TRACK (SDK)**: add an alias note that SDK `energy_ratio` == spec `charged_fraction`.

### B7 — §5 / References omit the inter-society homes (ISP, mcp) despite ISP `Extends: atp-adp-cycle.md` — LOW, AUTONOMOUS

The References block (L737-752) lists r6/r7, t3-v3, LCT, society-roles, SOCIETY_SPECIFICATION — but **not** `inter-society-protocol.md` (which declares `**Extends**: … atp-adp-cycle.md (ATP form)`, ISP L6) nor `mcp-protocol.md` (now the inter-society protocol). atp-adp §5 thus describes inter-society exchange in isolation from the two specs that now own it — the inter-society residue C34-M4/L4 did not close. **Remediation**: add §5 inline pointers + two References entries (pairs naturally with the B1 reframe).

### B8 — "executor" role taxonomy collides between §2.3 and §4.3; §4.3 cascade has no slot for the primary beneficiary — LOW, AUTONOMOUS

§2.3 `valueTracking` (L150-152) labels the agent entity `"executor": "lct:web4:entity:agent"` (with `primary_beneficiary` = client). §4.3 fractal cascade (L393-397) makes them **separate levels**: "Level 1: Direct executor (100%)" vs "Level 2: Agent/delegator (10%)" — so the §2.3 example cannot be mapped onto §4.3 consistently. Worse, the §4.3 cascade has **no slot for the client / primary_beneficiary**, yet §2.3 (L154) and §4.2 (L359) give the client the **largest** tensor delta (`valuation +0.05`). Internal role-vocabulary inconsistency. **Remediation**: align the role terms (executor/agent/delegator/beneficiary) between §2.3 and §4.3, and seat the primary beneficiary in the §4.3 cascade.

---

## §C — Routing Summary

| ID | Severity | Classification | Owner / next step |
|----|----------|----------------|-------------------|
| B1 | MEDIUM | CROSS-TRACK / DESIGN-Q | **Operator**: §5 referent-grounded reframe vs intra-society scoping — coordinate atp-adp §5 + mcp §7.7 + ISP §4. Subsumes ISP-B11. |
| B2a (demurrage) | MEDIUM | AUTONOMOUS | Remediation turn: §7.1#5 / §3.3 carve-out note. |
| B2b (exchange) | MEDIUM | DESIGN-Q | **Operator**: is cross-society exchange exempt from value-create MUSTs? Couples to B1. |
| B3 | MEDIUM | SDK-track | SDK: scope `atp.py:4` docstring. |
| B4 | MEDIUM→LOW | CROSS-TRACK | SDK gate `recharge`, or spec scopes MUST #4. |
| B5 | LOW | AUTONOMOUS | Remediation: harmonize §3.2 pool keys to §3.1 nested form. |
| B6 | LOW | AUTONOMOUS (+SDK) | Remediation: rename §3.1 `charge_rate`→`charged_fraction`; SDK alias note. |
| B7 | LOW | AUTONOMOUS | Remediation: add ISP + mcp to §5 / References. |
| B8 | LOW | AUTONOMOUS | Remediation: align §2.3↔§4.3 role taxonomy. |
| M2 (carried) | — | DESIGN-Q | **Operator**: slashing authority exclusive vs delegable; does §6.1 cap bind §2.4? |
| X1 (carried) | — | CROSS-TRACK | C33 B-H1 corpus identifier decision. |
| I2 (carried) | — | SDK-track | `atp.py:49-52` "three sub-pools" → two-state wording. |
| ISP-B10 (carried) | — | DESIGN-Q | Commitment-ATP charged-vs-allocated (ISP §4.3 vs atp-adp §7.1#4). |

**Autonomous remediation set (next remediation turn, C79-candidate)**: B2a, B5, B6 (spec leg), B7, B8 — 5 spec-only AUTONOMOUS edits. B1/B2b/M2/ISP-B10 await operator; B3/B4/I2/B6-SDK ride the SDK track.

> **REMEDIATED in C79** (PR pending, `worker/web4-20260620-180009`): all 5 autonomous findings applied to `atp-adp-cycle.md` (+42/−2). **B2a** — §3.3 R6-scoping note (demurrage is a time-triggered, non-R6 carve-out from MUST #5). **B5** — `mint_adp` harmonized to §3.1 nested form (`state_distribution.ADP` + `allocations.circulating`), preserving both pool invariants. **B6-spec** — §3.1 metric `charge_rate`→`charged_fraction` (full-file sweep; §2.2/§6 conversion-multiplier sites deliberately left). **B7** — ISP + mcp added to §5 inline pointer + References. **B8** — §4.3 role-vocabulary note aligning cascade levels to §2.3 and seating the primary_beneficiary outside the contribution cascade (no % / tensor-delta changes). atp-adp C34→#277→C78→C79 cycle COMPLETE for the autonomous set.

---

## §D — Lessons / Method Notes

- **Delta-re-audit dividend confirmed (B1)**: a file untouched since C34 became *wrong-by-corpus-evolution* when mcp §7.7 landed the normative referent-grounding amendment. A single-file re-read would not catch it; the cross-spec finder feeding on the *current* sibling corpus did. Reinforces the standing method: at delta time, re-check the subject against specs that were **added or amended since the prior audit**, not only against its own prior findings.
- **Clustered-read caught the §7.1 scoping gap (B2)** that the C34 section-by-section pass missed: enumerate *every* state-changing path for a primitive and check each against the normative MUST list, not just the two "happy-path" sections the MUSTs were written around.
- **SDK "canonical implementation" claims deserve a coverage check, not just a field-by-field diff (B3)**: C34 aligned spec fields against `atp.py` without noticing `atp.py` implements a *different layer* than the spec's normative core. (Echoes C64-B2/B9 — first-pass "SDK aligned" claims need a fresh mirror sweep at delta time.)
- Carried-item bidirectional re-check (C62/C64 lesson) applied: ISP-B5 confirmed **RESOLVED** downstream (ISP §4.5 L239 now mints ADP per atp-adp §2.1); M2/X1/I2/ISP-B10/B11 confirmed still open and routed.

---

## §E — INFO / Deflated (anti-overcall record)

- *"Non-accumulative … cannot be hoarded" (§1.2 L24) is absolute, while §3.3/§7.1#2 permit holding up to stake limits* — **INFO/deflated**: §1.2 qualifies "by entities" (entity-level) and §9.2 endorses society-level minting; reconcilable wording mismatch, not a normative conflict.
- *Demurrage penalizes held ATP though you need ATP to act* — **REFUTED**: §1.3 (L31-33) gives the explicit Gesell-style rationale; decay triggers only past `idle_threshold` (L305/542); the escrow note (L588-594) exempts reserved/locked in-flight ATP. Just-in-time charging is coherent.
- *Conservation vs minting* — **REFUTED**: entity-level non-accumulation vs society-level supply growth are distinguished (§9.2).
- *§7.4 `atp_settlement` single-rate vs spec* — folded into **B1** as the wire echo (§7.4 stabilizes with WIP §7.7); not an independent finding.
- *errors.md taxonomy gap for ATP/mint/slash exceptions* — **N/A**: C34 ruling holds (illustrative pseudocode, not wire `W4_ERR_*`); errors.md still defines no such codes.

---

## §F — Methodology Note

Produced by a deterministic 4-agent finder workflow (internal-consistency, SDK-alignment, cross-spec-drift, primitive-clustered blindspot), each prompted refute-by-default and fed the C34 DEMOTED/closed list to suppress re-derivation. The auditor then independently verified every survivor — including hand-confirming the flagship's load-bearing claim (`grep` of `mcp-protocol.md` confirmed §7.7.1's **Normative** scope tag at L514 and the "This is NOT the Web4 model" text at L526) and the ISP §4.1 unit-of-account / §4.5 ADP-mint / §4.3 commitment claims — deduped convergent findings (pool-model and `charge_rate` each surfaced by ≥2 finders), and applied severity deflation. 0 HIGH; the spec's core is sound, the live defects are scoping-gaps and cross-spec drift.

*Audit complete. Recommended next step: a remediation turn applying the 5 spec-only AUTONOMOUS findings (B2a, B5, B6-spec, B7, B8). B1 + B2b (+ carried M2, ISP-B10) await the operator; B3/B4/I2/B6-SDK ride the SDK track.*
