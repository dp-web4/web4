# C118 Audit: `atp-adp-cycle.md` Second Delta Re-Audit (prior C78/C79)

**Date**: 2026-06-29
**Auditor**: Autonomous session (Legion, web4 track) — single-auditor refute-by-default + targeted adversarial verification (proportional to a byte-frozen target with a bounded corpus delta; **not** the C78 4-agent fan-out).
**Document**: `web4-standard/core-spec/atp-adp-cycle.md` (793 lines)
**Lineage**: C11 (#224 first-pass) → C34 (#276 delta, #277 remediation) → **C78** (#367 first delta-re-audit, 8 findings) → **C79** (#368 remediation, 5 autonomous) → **C118** (this, second delta-re-audit).
**Baseline**: C78 audit (`docs/audits/C78-atp-adp-cycle-delta-audit-2026-06-20.md`); C79 remediation commit `db394dfa` (PR #368, +42/−2).
**Method**: §A re-verifies every C79 remediation and every open carry against the **live** spec. The target is **byte-FROZEN since C79** (HEAD blob `ea57769f` == the `db394dfa` blob), so §A is **persistence verification by byte-identity** (the fixes cannot have regressed because no edit landed) — *not* fix-held-under-churn verification. §B sweeps the **corpus delta** — siblings changed since C79 (2026-06-20) — for inbound cross-ref drift, plus a **cross-section internal blindspot sweep** (the discipline that has yielded the net-new finding on every frozen target since C108). Design questions are **ROUTED, not self-resolved**. **Read-only AUDIT turn — no spec or SDK edits.**

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 0 | — |
| MEDIUM | 0 | — |
| LOW | 2 | N1 (internal, AUTONOMOUS-candidate), N2 (inbound, flag-only) |
| **NEW actionable** | **1** | N1 (N2 is routed to the t3-v3 owner, not an atp-adp edit) |

**Delta result (§A)**: All **5 C79 autonomous remediations HELD** by byte-identity (B2a §3.3 demurrage R6 carve-out, B5 `mint_adp` nested-pool form, B6 `charged_fraction` rename, B7 ISP+mcp References, B8 §4.3 role-vocabulary note); **0 regression** (no remediation landed since C79 → §A is pure persistence verification). All open carries (B1/B2b DESIGN-Q, B3/I2/B6-SDK SDK-track, B4 CROSS-TRACK, M2, X1, ISP-B10) **STILL OPEN** — siblings frozen, operator unanswered.

**§B corpus delta**: 4 siblings touched atp-adp cross-refs since C79 — t3-v3 (C83), acp (C87), multi-device (C81), reputation (C85). Classification (against the C78/C79 **snapshot**, per the snapshot-presence guard, not memory): **2 REINFORCING, 1 flag-only multi-device-owned carry, 1 NET-NEW inbound drift (N2)**. Plus **1 NET-NEW internal cross-section finding (N1)** from the blindspot sweep.

**"Frozen ≠ clean," 5th confirmation (C108/C112/C114/C116/C118)**: a byte-frozen target with a bounded corpus delta still yielded N1 (internal blindspot) + N2 (inbound drift). N1 is itself a **[[feedback_remediation_introduced_regression]] mirror of C116-N1** — an unconditional §7 summary MUST whose own reference implementation carves out an unstated exception.

---

## §A — C79 Baseline Delta-Persistence

Target byte-FROZEN since C79 (`db394dfa`, 2026-06-20); HEAD blob `ea57769f` is identical. Each C79 fix re-verified present at the live line.

| C78 ID (C79 fix) | Remediation | Status | Live evidence |
|------------------|-------------|--------|---------------|
| **B2a** | §3.3 demurrage R6 carve-out note | **HELD** | L323–331: "time-triggered and not an R6 transaction … carve-out from §7.1 MUST #5 … demurrage is a *maintenance* discharge". |
| **B5** | `mint_adp` harmonized to §3.1 nested pool form | **HELD** | L264–269: mutates `state_distribution['ADP']` + `allocations['circulating']` + `total_supply`, with the invariant note. |
| **B6 (spec leg)** | §3.1 metric `charge_rate`→`charged_fraction` | **HELD** | L240: `charged_fraction` with the "distinct from the §2.2/§6 conversion-multiplier `charge_rate`" disambiguation. |
| **B7** | ISP + mcp added to §5 inline note + References | **HELD** | §5 note L433–439; References L787–791 (ISP "§4 … unit-of-account semantics and ADP minting"; mcp "§7.7 … referent-grounded cross-society exchange-rate negotiation"). |
| **B8** | §4.3 role-vocabulary note (seats primary_beneficiary outside the cascade) | **HELD** | L418–429: executor/agent/delegator/beneficiary roles aligned to §2.3; beneficiary "sits **outside** this contribution-attribution cascade". |

**Open carries — bidirectional re-verification (all STILL OPEN):**
- **B1** (§5 abstract-FX vs mcp §7.7.1 **normative** referent-grounding — CROSS-TRACK / DESIGN-Q): **STILL OPEN.** §5.2 menu still lists "Floating | Market-determined rate" (L482) and §5.3 still applies a single uniform `get_exchange_rate` (L499–507). The C79 B7 note (L433–439) correctly *flags* that rate-grounding "is owned by those specs and is being reconciled," but does **not** resolve the model contradiction — by design (B1 is operator-gated). mcp §7.7.1 unchanged (mcp frozen since C77 `f3d2613d`); **C116 independently re-confirmed atp-adp §5/References cite mcp §7.7 as the exchange-rate-negotiation owner — REINFORCING.**
- **B2b** (cross-society exchange §5.3 discharge bypasses MUST #4/#5/#6 — DESIGN-Q): **STILL OPEN.** L510 `source_society.pool.discharge(source_atp)` is still a non-R6 discharge with no value_proof/tensor update. Note the **carve-out asymmetry is now sharper**: C79 added the demurrage carve-out note (B2a) and slashing already had one (§2.4 note), so §5.3 exchange is the **lone** non-R6 discharge path **without** a carve-out note — reinforcing the B1/B2b routing, not net-new.
- **M2** (slashing-authority cap: §2.4 path caps at `get_entity_stake` and never references §6.1 `max_slash_per_event: 10000` — DESIGN-Q): **STILL OPEN.** L194 / L546 unchanged.
- **B3** (`atp.py` "canonical implementation" omits the §2 lifecycle — SDK-track): **STILL OPEN** (SDK untouched).
- **B4** (SDK `recharge()` rate-based ADP→ATP with no value proof — CROSS-TRACK): **STILL OPEN** (SDK untouched).
- **I2** (`atp.py:49-52` "three sub-pools" docstring — SDK-track): **STILL OPEN.**
- **B6-SDK leg** (`energy_ratio` alias note for spec `charged_fraction`): **STILL OPEN** (SDK untouched).
- **X1** (`lct:web4:` identifier → C33 corpus decision): **STILL OPEN** (corpus-wide carry).
- **ISP-B10** (commitment-ATP charged-vs-allocated, ISP §4.3 vs atp-adp §7.1#4 — DESIGN-Q): **STILL OPEN** (ISP frozen since C63, pre-C78).

**C56 claim-vs-canonical re-read** (verify the remediation's *claims*, not just edit-presence): B7's References claim that mcp §7.7 "covers referent-grounded cross-society exchange-rate negotiation" and ISP §4 "covers unit-of-account semantics and ADP minting" — both **re-confirmed accurate** (C116 verified mcp §7.7.1 normative referent-grounding; C78 verified ISP §4.1 unit-of-account / §4.5 ADP mint, both still live since ISP/mcp are frozen). No stale claim.

**Verdict**: Exemplary remediation persistence; zero regression. Analytic weight shifts (as on every no-remediation-landed delta) to §B.

---

## §B — Corpus Delta & Cross-Section Blindspot Sweep

### Inbound sibling cross-refs (snapshot-presence guard applied — classified against the C78/C79 snapshot, not memory)

| Sibling (C#) | Change to atp-adp cross-ref | Snapshot guard | Verdict |
|--------------|------------------------------|----------------|---------|
| **t3-v3 (C83, `25d36bb0`)** | ATP-conservation row reworded (see **N2**) | Pre-C83 co-cited "§2.4 + §6.3"; C83 demoted §2.4 + added a §2.4-only quote → **net-new** | **N2 (drift, flag-only)** |
| **acp (C87, `31cea0b0`)** | Adds "consumed … in the sense of `atp-adp-cycle.md` §2.3" (L172) | Citation absent pre-C87 → net-new, but **accurate** (§2.3 = ATP discharged/consumed by R6 execution) | **REINFORCING** |
| **multi-device (C81, `a6cbde92`)** | Adds carry "C19-M7 (§7.3 ATP costs vs `atp-adp-cycle.md`) | Deferred | … no atp-adp counterpart exists" | net-new deferral, **multi-device-owned** | **Flag-only** (no atp-adp action; multi-device tracks it) |
| **reputation (C85, `15be0743`)** | Adds rule field `min_atp_stake` + R6 fields `required_atp` / `atp_consumed` | references "staked ATP" / R6 consumption — concepts atp-adp owns (§3.3 stake limits, §2.3 `atpConsumed`) | **REINFORCING** (no doc-citation to atp-adp; field-casing difference is illustrative-representation, deflated) |

### N1 — §7.1 MUST #6 is unconditional, but §4.2 tracks society-level value **outside** T3/V3 via `aggregate_value` — LOW, AUTONOMOUS-candidate, INTERNAL (cross-section)

**§7.1 MUST #6** (L621): *"Value MUST be tracked through T3/V3 tensors."* — unconditional, no entity-vs-society scoping.

**§4.2 `track_value_flow`** (L383–386): the society-level leg of the fractal cascade is tracked with `(r6_transaction.society, {"aggregate_value": +0.0001})`, **explicitly self-labeled** *"society-level aggregate, **not a T3/V3 dimension**"*. So the spec's own reference implementation routes society-level value (the §4.3 cascade Levels 4 Society / 5 Parent-society) through a **non-T3/V3** channel — contradicting the literal, unconditional MUST #6.

**Why real (refute-survived)**:
- *Refute attempt 1 — "MUST #6 is about entities, societies are tracked differently by design."* Fails on the text: MUST #6 carries no entity-only scoping, and §4.2's **entity** legs (client `v3`, agent `t3`, witnesses `t3`) **do** use T3/V3 — only the society leg does not. The spec internally treats society-aggregate value as exempt from MUST #6 without saying so.
- *Refute attempt 2 — "`aggregate_value` is just a derived rollup of the entity T3/V3, so MUST #6 still holds."* Fails on the in-line comment, which calls it *"not a T3/V3 dimension"* — i.e. a distinct accounting channel, not a derivation.
- **Parallel to the C79 carve-out the authors already wrote**: C79 added a note (B2a) that demurrage *"creates no V3 value and so does not engage MUST #6."* That establishes MUST #6 **does** have scope limits — yet §4.2's society-aggregate exemption from MUST #6 stayed **un-noted**. Same carve-out-asymmetry pattern C78-B2 found for MUST #5 (slashing/demurrage noted, exchange not).

**Why not caught earlier**: C34 was section-by-section (never compared §7.1↔§4.2); C78-B2's clustered read enumerated *state-change* paths (charge/discharge/slash/demurrage/exchange) against the MUST list, but did not examine the **value-tracking** reference impl (§4.2) against MUST #6. This is the cross-section the blindspot sweep is built to reach.

**Severity — LOW**: the gap is at the society-aggregate attribution level (0.1% / 0.01% in §4.3), the authors are demonstrably aware (the explicit comment), and the defect is *over-broad MUST wording*, not a safety/economic hole. Directly mirrors **C116-N1** (unconditional §12 summary MUST vs the narrower §7 reality).

**Routing — AUTONOMOUS (next atp-adp remediation, C119-candidate), NOT self-applied (read-only audit)**: one-clause fix — scope MUST #6 (e.g. *"Entity-level value MUST be tracked through T3/V3 tensors; society-level aggregates MAY use non-tensor rollup accounting (§4.2)"*), **or** add a §4.2 carve-out note parallel to the C79 demurrage note. Recorded here so it is not re-surfaced as "net-new" at C120.

### N2 — t3-v3 (C83) ATP-conservation cross-ref now quotes a §2.4-only invariant form while anchoring primary on §6.3 — LOW, flag-only (t3-v3-owned)

**t3-v3 L640** (post-C83): `| ATP conservation | total supply = ATP + ADP (transfers preserve total supply; the per-transfer form is `initial == final + fees`) | atp-adp-cycle.md §6.3 (§2.4 Slashing is the deliberate exception) | — |`

**Issue**: the quoted invariant form `initial == final + fees` appears in atp-adp at **§2.4** (L214, the supply-accounting note) — **not** §6.3. atp-adp **§6.3** ("Transfer Fees") supports only the looser *"preserving total supply"* (fee recycling, L604); the *equation* `total supply = ATP + ADP` lives in **§3.1/§3.2** (`state_distribution` + the `mint_adp` invariant note). So the C83 reword anchors primary on §6.3 while quoting a §2.4 string and an §3.1/§3.2 equation.

**Snapshot-presence guard (net-new, not pre-existing)**: pre-C83, t3-v3 co-cited *"§2.4 + §6.3"* (both co-primary) with no quote. C83 **demoted §2.4** to a parenthetical "the exception" **and added the `initial == final + fees` quote** — so C83 *introduced* the anchor/quote mismatch; it was not present at the C78/C79 snapshot.

**Routing — flag-only to the t3-v3 owner** (this is a **t3-v3 edit**; atp-adp is read-only here and is **not** the defect site). Tightest fix in t3-v3: cite *"§2.4 (per-transfer invariant) + §3.1/§3.2 (supply equation); §6.3 fee-recycling preserves supply; §2.4 Slashing is the deliberate exception."* Route into the next t3-v3 remediation turn (t3-v3 last C82/C83). No atp-adp action.

---

## §C — Routing Summary

| ID | Severity | Classification | Owner / next step |
|----|----------|----------------|-------------------|
| **N1** | LOW | AUTONOMOUS (internal) | Next atp-adp remediation (C119-candidate): scope §7.1 MUST #6 to entity-level, or add a §4.2 society-aggregate carve-out note. NOT self-applied (read-only). |
| **N2** | LOW | flag-only (t3-v3-owned) | t3-v3 owner / next t3-v3 remediation: tighten the L640 ATP-conservation anchor (§2.4 + §3.1/§3.2 for the quoted invariant; §6.3 for fee-recycling). No atp-adp action. |
| B1 | — | CROSS-TRACK / DESIGN-Q | **Operator** (open): §5 referent-grounded reframe vs intra-society scoping. C116-REINFORCED. |
| B2b | — | DESIGN-Q | **Operator** (open): is §5.3 exchange exempt from value-create MUSTs? Now the lone un-noted non-R6 discharge. |
| M2 | — | DESIGN-Q | **Operator** (open): does §6.1 `max_slash_per_event` bind the §2.4 path? |
| B3 / B4 / I2 / B6-SDK | — | SDK-track | SDK (open): scope `atp.py` docstring; gate/rename `recharge`; "two-state" wording; `energy_ratio`↔`charged_fraction` alias. |
| X1 | — | CROSS-TRACK | C33 corpus identifier decision (open). |
| ISP-B10 | — | DESIGN-Q | **Operator** (open): commitment-ATP charged-vs-allocated. |

**Autonomous remediation set (next atp-adp remediation turn, C119-candidate)**: **N1 only** (1 spec-only edit). N2 rides the t3-v3 track; everything else awaits the operator or the SDK track.

---

## §D — Lessons / Method Notes

- **"Frozen ≠ clean," 5th confirmation (C108/C112/C114/C116/C118)**: a byte-frozen target + bounded corpus delta still yielded N1 (internal cross-section) + N2 (inbound drift). On a no-remediation-landed delta, §A is light (persistence by byte-identity) and the analytic weight is **entirely** on §B — exactly where the policy-review guardrail said to put it.
- **N1 is a C116-N1 mirror** ([[feedback_remediation_introduced_regression]] class once-removed): an unconditional **summary MUST** (§7.1 #6 here, §12 #6 in mcp) whose own detailed reference behaviour carves out an **unstated** exception. The recurrence across two consecutive files suggests a corpus-wide pattern worth a **primitive-clustered MUST-vs-reference-impl sweep** — enumerate every "X MUST …" summary requirement and check it against the section that actually implements X.
- **Snapshot-presence guard earned its keep (N2)**: the t3-v3 cross-ref *looks* like a long-standing §6.3 citation, but the git snapshot shows C83 **demoted §2.4 and added a §2.4-only quote** — the drift is net-new and correctly attributed to the C83 edit, not mis-flagged as pre-existing. (Cf. [[feedback_snapshot_presence_guard]].)
- **Inbound cross-ref dividend (C90 lesson)**: reading what siblings *changed* about their atp-adp citations (not just atp-adp's own text) surfaced both a REINFORCING confirmation (acp §2.3) and a drift (t3-v3 §6.3 anchor). Two of four siblings reinforced, one drifted, one is an other-owned deferral — the healthy signature of a frozen-but-cited primitive.
- **Proportionality vindicated**: single auditor, refute-by-default, targeted git-snapshot verification — **not** the C78 4-agent fan-out. Right cost for a frozen target with a 4-sibling delta surface.

---

## §E — INFO / Deflated (anti-overcall record)

- *reputation C85 `required_atp` (snake_case) vs atp-adp R6 example `atpRequired` (camelCase)* — **deflated**: atp-adp L41–46 declares its JSON examples illustrative (camelCase readability); reputation's are Python pseudocode (snake_case). Different representations of the same field, not a normative conflict.
- *§4.2 society leg `aggregate_value` magnitude (+0.0001) vs §2.3/§4.2 entity deltas* — **N/A**: illustrative magnitudes, C78-I3 ruling holds (by-design illustration).
- *§8.2 lowercase "must" bullets (value proofs signed, pool states merkle-rooted, exchange rates witnessed, slashing evidence-trailed) not mirrored in the §7.1 MUST list* — **deflated to INFO**: §8 is "Security Considerations" prose, not the normative requirements list; lowercase "must" in a considerations section is descriptive. Noted as a *potential* §7-list-non-exhaustiveness echo of N1's family, but below the actionable bar (no contradiction, only non-mirroring).
- *§2.3 vs §4.2 differing tensor-delta magnitudes (client +0.03 vs +0.05; agent +0.01 vs +0.02)* — **REFUTED**: C78-I3 by-design illustrative magnitudes; the C79 B8 note explicitly references §4.2's own numbers.

---

## §F — Methodology Note

Single-auditor delta-re-audit, refute-by-default, proportioned to a byte-frozen target (HEAD blob == C79 blob, verified) with a bounded corpus delta (4 siblings touched atp-adp cross-refs since C79, each individually diffed). §A is persistence verification by byte-identity plus a C56 claim-vs-canonical re-read of the B7 References claims (re-confirmed against the still-live mcp §7.7 / ISP §4). §B applied the snapshot-presence guard to every inbound cross-ref (git-diffed each sibling's pre/post text) and a cross-section internal blindspot sweep (§7.1 MUST list × the reference implementations in §2–§5). Both net-new candidates were adversarially refute-tested (N1 survived two refutations; N2 survived the snapshot guard). 0 HIGH / 0 MEDIUM — the spec's numeric/normative core remains sound; the live defects are an over-broad summary-MUST (N1) and an inbound citation imprecision introduced by a sibling's own remediation (N2).

*Audit complete. Recommended next step: a C119 atp-adp remediation turn applying **N1** (1 spec-only edit); flag **N2** to the t3-v3 track; B1/B2b/M2/ISP-B10 + the SDK-track carries (B3/B4/I2/B6-SDK) + X1 remain operator/SDK-gated.*
