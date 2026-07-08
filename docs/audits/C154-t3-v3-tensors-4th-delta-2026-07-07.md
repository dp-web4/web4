# C154 Audit: `t3-v3-tensors.md` Fourth Delta Re-Audit

**Date**: 2026-07-07
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn, slot `180036`
**Document**: `web4-standard/core-spec/t3-v3-tensors.md` (687 lines)
**Prior passes**: C13 → C42/**C43** (#299) → C82/**C83** (#374, `25d36bb0`) → C121 (#425) / **C122** (#427, `b2a98f7c`) → **C154** (this).
**Methodology**: Fourth delta re-audit, single-auditor refute-by-default with an adversarial verifier subagent (4 items, all primary-source re-read). §A = C122 fix persistence + claim-vs-canonical token-by-token re-read against the LIVE sibling (load-bearing this cycle: C151 reworded the exact atp-adp line the C122 cell anchors) + remediation-introduced-regression check + bidirectional carry re-verification with live grep evidence. §B = corpus-delta at cited-hunk granularity (5 movers), non-spec T3/V3-consumer sweep (3 Rust commits), inbound-carry read of all 14 sibling audit docs since C122 that mention t3-v3.

---

## C153 — multi-device REMEDIATION slot: genuine NO-OP (declared, evidentiary basis)

Per the rotation, C153 was the `multi-device-lct-binding.md` remediation slot following the C152 audit (PR #478, merged `ab44384d` 2026-07-07T23:04Z). **Zero commits landed between the C152 merge and this session's base** (`git log ab44384d..origin/main` empty — the merge commit IS HEAD), so nothing could have introduced an autonomous multi-device item; and C152 itself routed both of its findings cross-track (C152-1 B-10 adjudication → operator with the security cluster; C152-2 PAIRED-CHANNELS.md:420 → hub track). **16th no-op→advance** (precedents C93→C94 … C149→C150). Rotation advances (+2) to `t3-v3-tensors.md` = **C154**.

---

## Summary

| | Count |
|---|---|
| **§A** C122 fix (§10.2 L640 re-anchor) | HELD — all 3 anchors verify token-by-token at live HEAD; **C151 REINFORCES** |
| **§A** C83 F2–F6 + C43 fixes | HELD by byte-identity (target frozen since C122; only C122's one-cell diff since C83) |
| **§A** open carries re-verified live | D1 / D3 / F1 / L3 / X4-structural / D2-attach-strategy — **all STILL OPEN**, evidence re-grepped at HEAD |
| **§B** movers since C122 | 5 — 1 REINFORCING (atp-adp C151), 4 DISJOINT at cited-hunk granularity |
| **§B** T3/V3 consumers (Rust) | 3/3 REINFORCING (P3b #445, identity-p1 #457, hub §5.3 #430) |
| **§B** NET-NEW surviving adversarial verification | **1** — **N1 (LOW, cross-track, mcp-owned)**: mcp L415 citation mis-anchor, sharpened from C148's INFO |
| Autonomous-in-file items for C155 | **0** |

**Health verdict**: `t3-v3-tensors.md` remains in **excellent health** — byte-frozen since C122 (HEAD blob `25203eb8` == C122 blob), zero regression across the C13→C43→C83→C122 remediation stack, and the one §A hazard this cycle (C151 rewording atp-adp §2.4 L214, the line the C122 cell quotes) resolves as **reinforcing**: the sharpened scope phrase ("ATP transfers between entities (§6.3)") makes the cell's "transfers preserve total supply" *more* precisely grounded, not less. The corpus is actively converging ON this file: all three Rust T3/V3 consumers that landed since C122 adopt the canonical 3-root, role-contextual model. The single yield is an **outbound** cross-track item (N1) surfaced by the inbound-carry read, not by this file's own bytes.

---

## §A — C122 Persistence + Claim-vs-Canonical + Carry Re-Verification

### A.1 — C122 fix (the §10.2 L640 ATP-conservation re-anchor): HELD + REINFORCED

C122's single edit expanded the Related-context cell to route each element to its true home. All three anchors re-verified token-by-token against the **live** `atp-adp-cycle.md` (adversarial verifier Item 1, CONFIRMED):

| Anchor claim (t3-v3 L640) | Live atp-adp evidence | Verdict |
|---|---|---|
| §3.1/§3.2 supply equation `total supply = ATP + ADP` | `state_distribution` contains ONLY `ATP` (15M) + `ADP` (85M) keys summing to `total_supply` (100M) at L225–245; §3.2 explicit invariant `total_supply == sum(allocations) and == sum(state_distribution)` at L266 | **HOLDS** |
| §2.4 per-transfer invariant `initial == final + fees`; Slashing the deliberate exception | Exact form verbatim at L214; slashing "sits **outside** the transfer-conservation invariant" L213–215 | **HOLDS** |
| §6.3 fee-recycling preserves total supply | "Fees SHOULD be recycled into the society's pool (not destroyed), preserving total supply" L604–605 | **HOLDS** |

**The C151 interaction (this cycle's load-bearing check)**: C151 (`256ab51d`, applying C150-N1) reworded §2.4 L214's scope phrase "scopes only ATP→ADP transfers" → "scopes only ATP transfers between entities (§6.3)". Verified: C151's spec diff is confined to that single line (§3.1/§3.2/§6.3 byte-unchanged since C122); the cell quotes the invariant *form* and the slashing-exception framing, both of which survive; and the sharpened scope makes the cell's summary "transfers preserve total supply" cleaner (discharge — now explicitly outside the invariant's scope — still preserves total supply as a state change, so the sentence is true under both wordings). The other in-file use of the invariant (L328 demurrage carve-out analogy) is also consistent. **REINFORCING.** C151's own commit-body claim ("t3-v3 L640 anchor re-verified post-edit") independently corroborated.

**Remediation-introduced-regression check** (the C121/C123 pattern, 8 prior instances): C122's net-new prose vs `b2a98f7c^` = the expanded cell only; every claim it added is verified above against live canonicals. **CLEAN** — second consecutive clean remediation in this lineage (C122 quoted canonicals verbatim, same discipline as C119).

### A.2 — C83/C43 persistence

Target byte-frozen since C122; the only diff since C83 is C122's one cell. C83 F2–F6 (verified individually at C121) and the C43 stack therefore HOLD by byte-identity. Mirror freshness: SDK `trust.py` (last `759eaefa`, Sprint 38), ontology `t3v3-ontology.ttl` (`bedd3bf8`), vectors `tensor-operations.json` (`226e7948`) — **all unchanged since before C83** → every numeric claim (bridge 0.6/0.4-per-3, t3v3-008, V3 0.3/0.35/0.35 vs T3 0.4/0.3/0.3, clamps) persists by construction.

### A.3 — Open carries (bidirectional, live-grepped at HEAD)

| Carry | C154 state | Live evidence |
|-------|-----------|---------------|
| **D1** ontology-vocab (`web4:matchesTask` undefined) | **STILL OPEN** | `matchesTask` has exactly ONE corpus occurrence — the §9.2 L549 *usage*; 0 defining triples; ontology frozen |
| **D3/M4** Valuation 3-way range | **STILL OPEN** | §3.1 L260–267 open-question note intact; SDK `V3.__post_init__` still clamps; ontology L90 still "may exceed" |
| **F1** "minimal" vs SDK neutral-0.5 (cross-track) | **STILL OPEN** | §6.3 L470 "minimal trust" intact; `trust.py` L151–153 defaults 0.5 |
| **L3** t3v3-010 "coherence" label (cross-doc) | **STILL OPEN** | vector L184/L191 still `"coherence"`; §10.2 L639 spec-side note intact |
| **X4-structural** (mrh §5 shrink-to-pointer, operator DESIGN-Q) | **STILL OPEN** | `mrh-tensors.md` frozen since C91 `f0c82118` |
| **D2 attach-strategy** (multi-device flat-6D ↔ §2.5 bridge; ontology sub-dim declaration) | **STILL OPEN**, context hardened | multi-device frozen since C81; ontology still 3-roots-only; **P3b #445 deleted the last parallel Rust T3Tensor** (per C152) — the implementation world has converged on the canonical form, strengthening the case for the operator to ratify the bridge/sub-dim path |

---

## §B — Corpus Delta, Consumer Sweep, Inbound-Carry Read

### B.1 — The 5 movers since C122 (cited-hunk granularity; verifier Item 3, CONFIRMED)

| Mover | Hunks | Verdict |
|-------|-------|---------|
| **atp-adp C151** `256ab51d` | §2.4 L214 scope phrase only | **REINFORCING** (see A.1) |
| **reputation C124** `4d1594ea` | @292 fail-open conditions note, @654/@705 clock-skew floors | **DISJOINT** — all outside reputation's 4 t3-v3 citation sites (L166/L188/L217/L767); fail-open prose is rule-*matching* semantics, zero t3-v3 counterpart surface |
| **acp C126** `aabe4457` | 2 hunks, `resourceCaps` casing only | **DISJOINT** — acp's `t3v3Delta` (L160–165) / `trustTrend` (L383–386) untouched |
| **FRACTAL_ROLE_IDENTITY C130** `4e3feb26` | 1 line, mrh anchor `:143`→`:174` | **DISJOINT** — no t3-v3 content in hunk |
| **presence README C128** `cf0d6cc5` | schema-gap ledger | **DISJOINT** by zero-of-concept (0 t3/v3 occurrences, diff and live) |

### B.2 — Non-spec T3/V3 consumers (read-only; verifier Item 4, CONFIRMED)

All three Rust commits since C122 that consume T3/V3 **adopt the canonical model** — none redefines dimensions, adds a 4th root, or computes global trust:

- **P3b `20ef29f5`** (#445): deletes the parallel `T3Tensor`/`V3Tensor` (−513 lines), converges `EntityTrust` onto `web4_core::t3::T3`/`v3::V3`; serde keys = canonical root names; [0,1] clamps via `apply_delta`. (Observation-count arrays are confidence metadata, not dimensions. EntityTrust's entity-keying is pre-existing shape, noted at C121 via referenced-acts — unchanged.)
- **identity-p1 `c21442bd`** (#457): `t3_delta`/`v3_delta` keyed by root-dimension names; the new `SovereignStrength` is attestation-provenance metadata, not a trust dimension; fold stays per role-pairing.
- **hub §5.3 `386ef044`** (#430): reputation keyed `(subject_lct, role_lct)`, "Reputation is NEVER global" (twice), folds via `T3/V3::apply_delta`, scoring weights deferred to society law — direct conformance with §1.1 role-contextual + §6.3 L468 "MUST NOT compute global (role-agnostic) trust scores".

### B.3 — Inbound-carry read → **N1** (LOW, cross-track, mcp-owned; verifier Item 2, CONFIRMED)

14 sibling audit docs since C122 mention t3-v3; 13 use it as canonical reference / disjointness evidence with nothing routed here (C150 verified the L640 anchors AGREE; C152 anchors §2.5). The 14th — **C148 (mcp)** — recorded an "inspected & bounded" INFO: *t3-v3 §10.2 classes the T3-update formula protocol-invariant while mcp says the society sets bounds; defensible because bounds ≠ formula; not routed.* This audit owns the t3-v3 side of that citation, so it was adjudicated fresh with a dereference test — **can a reader following mcp's citation actually find the cited governance?**

**Finding N1**: `mcp-protocol.md:415` — "deltas MUST be within bounds set by the responding society's **Law Oracle** for the role context (**per `t3-v3-tensors.md` parameter governance**)" — is a citation mis-anchor:

- t3-v3 contains **zero** mentions of "Law Oracle" (whole file);
- §10.2/§10.3 contain **no row** for trust-delta bounds (§10.3's only trust row, "Role requirement thresholds" §5.1, is a minimum-T3 *qualification gate*, not an update-magnitude bound — this also invalidates C148's specific dereference, which pointed at exactly that row);
- §10's own preamble (L600–604) scopes its synthesis to t3-v3 §2.3/§3.3 + atp-adp §6.3/§7 + multi-device §4.4 — R7 reputation deltas are outside it;
- the actual normative home is **`reputation-computation.md:241`**: "Law Oracles define reputation rules that map outcomes to T3/V3 deltas."

**Adversarial adjudication vs C148's deflation**: C148's core deflation (no vector/SDK contradiction → not MED/HIGH) **stands**; and a weak reading survives in which mcp cites the §10.1/§10.5 governance-tier *framework* ("when a society sets a rate, it MUST publish the value in its governance laws"). So this is **LOW** (citation precision), sharpened from C148's INFO by the missing-dereference evidence. **Owner: mcp** (the citation lives there; t3-v3 is read-only here — the same ownership logic as C118-N2 in reverse). **Fix (for a future mcp turn)**: re-anchor L415's parenthetical to `reputation-computation.md` (Law-Oracle reputation rules) with t3-v3 §10.5 optionally cited for the publish-in-law principle. **Route-only; NOT applied this turn** (audit turn + not this file).

### B.4 — Internal blindspot re-sweep

Byte-frozen target; the normative-summary loci (§6, §10) were swept at C121 with exactly one instance (N2, fixed by C122 and re-verified here). No new normative-summary content exists to sweep. The C148-noted formula-vs-bounds *tension* is adjudicated above as N1 (mcp-owned). **CLEAN.**

---

## §C — Disposition

**AUDIT turn — no spec mutation this session.** Routing:

- **N1** (LOW, mcp-owned) → **carries ledger, outbound cross-doc carry**; apply at the next mcp rotation turn. Not autonomous here.
- All standing carries (D1, D3/M4, F1, L3, X4-structural, D2 attach-strategy) → **STAND**, operator/SDK-gated, re-verified live.
- **0 autonomous-in-file items for C155** → per the no-op→advance precedent, C155 (t3-v3 remediation slot) is expected NO-OP; rotation advances to `reputation-computation.md` 4th delta (last audited C123/C124).

## §D — Lessons

1. **A sibling's "inspected & bounded, not routed" INFO is inbound surface for the file it cites.** C148 deflated the formula-vs-bounds tension from the *mcp* side; the *t3-v3*-side dereference test (zero Law-Oracle mentions, no delta-bounds row, §10's explicit scope statement) sharpened it into a routable LOW — and exposed that C148's own dereference (role-requirement thresholds) was wrong. Delta audits should re-adjudicate a sibling's deflated INFOs when the deflation's evidence lives in *this* file.
2. **A sibling's remediation can REINFORCE an anchor your own prior remediation created — but only verification proves it.** C151 reworded the exact line C122's cell quotes; the outcome (reinforcing) was not knowable from the commit subject. Same discipline as C140's remediated-mover lesson, now on the *anchored* side.
3. **Consumer convergence is corpus-health evidence for a frozen target.** Three independent Rust commits all adopting the canonical 3-root role-contextual model (and one deleting a parallel tensor) is the strongest kind of "the spec is being read and followed" signal — worth recording in the audit even though it yields no defect.

---

*Audit complete. C153 declared no-op (evidence above); C154 yield = 1 outbound cross-track LOW (N1 → mcp) + 0 autonomous-in-file. Recommended next: C155 expected no-op → advance to `reputation-computation.md` 4th delta.*
