# C133 — SOCIETY_METABOLIC_STATES.md 3rd-Delta Re-Audit (C21→C54→C55→C96→C133)

**Audit ID**: C133
**Date**: 2026-07-03
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (444 lines, v1.0.0, "Proposed Standard")
**Lineage**: C21 first-pass (2026-05-29, 16 findings) → C54 first-delta (2026-06-14, 16 distinct) → C55 remediation (PR #326, `a504ea41`, applied 5 autonomous) → C96 2nd-delta (2026-06-25, 0 net-new) → **C133 (this, 3rd delta)**
**Cadence**: C-series fixed-order round-robin delta re-audit. Rotation reached SOCIETY_METABOLIC because the **C133 dictionary REMEDIATION slot was a no-op** — C132 (dictionary 3rd-delta, PR #444) found 0 net-new and the dictionary has no autonomous fix; step-(a) confirmed no DESIGN-Q answered / no dictionary SDK auth since C132 (only intervening commit `20ef29f5` #445 is an unrelated Rust trust-tensor migration). Per the **C93→C94** and **C131→C132** precedents, a no-op remediation slot advances the round-robin to the next-oldest file = SOCIETY_METABOLIC_STATES (last audited C96, 2026-06-25).
**Auditor session**: legion-web4-20260703-180036 (LEAD, slot 000036)
**Out of scope**: spec source edits, SDK edits, sister-doc edits (this is an AUDIT turn; remediation is the next alternation). Sister-doc/SDK finding-generation is cross-reference reads only. No M7 ontology drafting; no self-applied operator DESIGN-Q.

---

## 1. Methodology

Standard C-series 3rd-delta re-audit on a **byte-frozen target**. The file has not changed since the C55 remediation (`a504ea41`): `git diff a504ea41 HEAD -- web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` is **empty** — frozen across the entire C55→C96→C133 window (19 days). The SDK canonical `metabolic.py` is likewise unchanged since C96. This is a frozen 3rd-delta, so the method (per the locked frozen-target pattern established C92/C94/C96/C98/C100/C106 and reaffirmed C121/C123/C131/C132) leans on:

- **§A — Prior-finding verification**: all C96 dispositions HELD by construction on a frozen target, re-confirmed by first-hand re-read of the live text; every standing carry re-verified STANDS (not merely asserted). #-regression check on the frozen window.
- **§B — Corpus-delta + inbound-carry sweep**: the yield on a frozen target is entirely on **what moved**. Exactly **two** siblings moved since the C96 cutoff (2026-06-25): atp-adp-cycle.md (C119 `e99b419e`) and web4-trust-core (#445 `20ef29f5`). Each is tested for disjointness from the metabolic carry surface **by citing the moved hunk** (C120/C123/C132 discipline — prove disjointness, don't assert it), refute-by-default.
- **§C — Carries reconciliation** against the standing ledger.
- **§D — Method notes.**

Severity: HIGH / MEDIUM / LOW / INFO. Disposition: AUTONOMOUS-ACTIONABLE / DESIGN-Q / CROSS-TRACK.

### Anchor authorities consulted
| Anchor | Path |
|---|---|
| Spec target | `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (frozen `a504ea41`) |
| SDK canonical | `web4-standard/implementation/sdk/web4/metabolic.py` (frozen since C96) |
| Test vector | `web4-standard/test-vectors/metabolic/society-metabolic-states.json` |
| Corpus delta (moved) | `atp-adp-cycle.md` (C119 `e99b419e`, §7.1 MUST #6), `web4-trust-core` EntityTrust tensor (#445 `20ef29f5`) |
| Sister specs (unmoved) | `SOCIETY_SPECIFICATION.md` §1.4, `web4-society-authority-law.md` §3.6 |
| Sibling interval audits | `docs/audits/C98-society-authority-law-audit-2026-06-25.md` (SAL 2nd-delta), `C131/C132` (this fire's predecessors) |

---

## 2. §A — Prior-Finding Verification

### A.1 C55 remediations (5 autonomous, PR #326) — held/regressed?
Target byte-frozen since `a504ea41` → all five HELD **by construction**; re-confirmed present by first-hand re-read:
| C54 ID | C55 fix locus | C133 disposition |
|---|---|---|
| **B2** (LOW) | §2.4 wake bullet (`L91`) | **HELD** — present; agrees with §3.1 `L184` + §4.1 `L229`. |
| **B10** (LOW) | §7.2 #1 "Wake-Trigger Flooding" (`L382`) | **HELD** — present verbatim (`L382` re-read: rate-limit/ATP-bond all cheap wake triggers incl. hibernation `new_citizen`). |
| **B12** (INFO) | §7.1 "Sentinel heartbeat + timeout wake" | **HELD**. |
| **B13** (INFO) | §10 conformance precision | **HELD** — §10 claims re-tested against §6.1/§6.2/§5.2 ground truth (see A.4). |
| **B16** (INFO) | §3.1 transition cross-ref symmetry | **HELD**. |

**5/5 HELD, 0 REGRESSED.** No post-C55 commit touched the target; the C96 finding that #326 introduced 0 defects (like C51) is unchanged.

### A.2 #-Regression sweep (C96→C133 window)
No commit in the window touched the target or `metabolic.py`. The frozen window is regression-free by construction. The two moved siblings are handled in §B (both off-target).

### A.3 Standing carries — re-verified STAND (frozen ⇒ verbatim, re-read live)

**SDK cross-track (4) — ALL STILL STALE** (`metabolic.py` frozen; line-anchors re-read live this fire):
| ID | Site | State |
|---|---|---|
| **B1** | `metabolic.py:147` `Transition(HIBERNATION, ACTIVE, "external witness or timeout")` | **STILL STALE** — re-read confirms exact string; omits `new_citizen` + 90-day that spec §3.1 `L184` now carries. |
| **B3** | `metabolic.py:207` `Formula (§6.1): Daily ATP Cost = …` | **STILL STALE** — re-read confirms "Daily"; spec §6.1 `L341` says "Hourly". |
| **B4** | `metabolic.py:110` `description="Frozen + alert bonus"` (TORPOR) | **STILL STALE** — re-read confirms phantom "+ alert bonus"; spec §5.1 `L299` is "Frozen". |
| **B11** | `metabolic.py:412` comment "Rest: queued" vs `return state == ACTIVE` | **STILL STALE**. |

**Sister-doc cross-track (2) — ALL STILL OPEN, snapshot-stable**:
| ID | Site | State |
|---|---|---|
| **B14** | `SOCIETY_SPECIFICATION.md` §1.4 "MUST also conform" vs metabolic "Proposed Standard" + §10 SHOULD | **STILL OPEN** — SOCIETY_SPEC unmoved since C96 (`git log` since cutoff empty); C131 (SOCIETY_SPEC 3rd-delta) did not touch §1.4. Snapshot-stable. |
| **B15** | `web4-society-authority-law.md` §3.6 `L141` dormant list omits Rest (SDK `DORMANT_STATES` ⊇ REST) | **STILL OPEN** — SAL unmoved since C96; **dual-anchored** by SAL audit C98-B9 (re-confirmed this fire). Snapshot-stable. |

**C21 design-Q (8) — ALL STILL OPEN**: H1, H3, M3, M5, M7, L4, L5, L7. **C54 design-Q (6) — ALL STILL OPEN**: B5, B6, B7, B8, B9, B14-normative-strength. None self-resolved (frozen). **M7 ontology absence**: no `web4:MetabolicState` class was drafted (operator-engagement-flagged); the 2 pre-existing `web4-core-ontology.ttl` adjective-"metabolic" hits (ATP/ADP-cycle `rdfs:comment`) are unchanged — M7 absence HOLDS.

### A.4 §10 conformance re-test (fresh-eyes, frozen text)
All 8 state multipliers agree across §2.x / §4.1 `state_multipliers` / §10. §6.1 (1000/2400/40), §6.2 (5.0/90.0/50.0), §5.2 (1.0/0.0/reliability) recompute correctly; §10 category breakdown, named states, 6-of-8-driven and `molt_success_rate` nuance all exact. 0 discrepancies — consistent with C96.

---

## 3. §B — Corpus-Delta + Inbound-Carry Sweep

**Result: 0 NET-NEW AUTONOMOUS DEFECTS on the frozen target** — the honest frozen-target outcome, **2nd consecutive fully-clean metabolic delta** (after C96). Both moved siblings are proven DISJOINT from the metabolic carry surface by citing the moved hunk.

### B.1 atp-adp C119 (`e99b419e`, PR #420) — DISJOINT (moved hunk cited)
C119 applied C118-N1 to `atp-adp-cycle.md`. Live `git show e99b419e` of the target hunk:
- **§7.1 MUST #6** changed from "Value MUST be tracked through T3/V3 tensors" → "**Entity-level value** MUST be tracked through T3/V3 tensors; **society-level aggregates MAY use non-tensor rollup accounting** (§4.2)", plus an added scope Note carving the §4.3 Levels 4–5 `aggregate_value` channel out of MUST #6 ("**not a T3/V3 dimension**").

**Disjointness — proven two ways:**
1. **By absence of surface.** `grep -niE "\bvalue\b|V3|aggregate" SOCIETY_METABOLIC_STATES.md` returns **zero hits**. The metabolic target has **no society-level value / V3 / aggregate concept at all**, so C119's MUST #6 *value*-tracking carve-out has literally no metabolic surface to touch.
2. **By carve-out family.** C119's own Note states the MUST #6 society-aggregate carve-out is "**the same carve-out pattern as the §3.3 demurrage note**." Metabolic's only atp-adp coupling is §6.1's **hourly presence cost = a time-triggered maintenance _discharge_** (C96-E1), which sits on the **§3.3 / MUST #5 (discharge)** carve-out, a *different* carve-out than MUST #6 (value tracking). The live §3.3 demurrage anchor is confirmed still present (`atp-adp-cycle.md:329` re-read this fire) → **C96-E1's anchor is intact and unmoved**; C119 neither strengthened nor weakened it. C96-E1 stands verbatim as a route-only atp-adp-side INFO enrichment.

**No MUST-vs-impl (C116-N1/C118-N1) exposure.** Per the policy-review caution: metabolic §6.1 is a discharge-cost locus, but because the target restates **no** entity-level value MUST (zero value surface, per B.1.1) it cannot conflict with the moved MUST #6; and §6.1's discharge is *compliant-by-§3.3-carve-out*, not an unconditional restatement. The DOC-SPECIFIC MUST-vs-impl class does not fire here.

### B.2 trust-tensor #445 (`20ef29f5`, EntityTrust → web4_core T3/V3) — DISJOINT
`git show 20ef29f5 --stat | grep -i metabol` = **no metabolic files**. #445 converges the Rust `web4-trust-core` `EntityTrust` onto `web4_core::t3::T3`/`v3::V3` (one tensor in the crate; sealed-file serde compat preserved; bit-identical update semantics). This is the Rust trust crate — the metabolic spec's only trust surface is the Python SDK `TrustEffect(update_rate, decay_rate)` dataclass (`metabolic.py`) and the §5.1 single-column trust-effect (C21-H3 design-Q). Neither is the `EntityTrust` T3/V3 structure #445 touched; #445 does not alter `TrustEffect` (Python SDK frozen since C96) nor the §5.1 redesign question. DISJOINT.

### B.3 Inbound sibling-audit carries (C98 SAL 2nd-delta)
The only sibling audit since C96 that anchors metabolic is **C98** (SAL 2nd-delta, 2026-06-25). Re-read this fire:
- **C58-B10 / C96-C58-link (defer-vs-wake DESIGN-Q)** — re-verified two-sided and OPEN. SAL §3.6 `L141` "dormant states SHOULD **defer**" citizenship (re-read live) vs metabolic §3.1 `L184` / §4.1 `L229` `wake_on: ["new_citizen", …]` making `new_citizen` an explicit Hibernation→Active **wake** trigger (re-read live). **Both files frozen since their respective remediations → the two-sided contradiction stands unchanged.** Routes to the operator bundle (couples M5 "define dormant" + C54-B9 / C58-B9 Rest-membership). Not self-applied.
- **C58-B9 / C54-B15 (Rest dormant-membership)** — dual-anchored, both anchors frozen, STANDS.
- C100/C106 mention metabolic only in the frozen-target-pattern narrative (rotation bookkeeping) — no metabolic carry routed back.

---

## 4. §C — Carries Reconciliation

### Standing carries — all STAND (frozen target → verbatim, re-read live this fire)
- **C21 design-Q (8)**: H1, H3, M3, M5, M7, L4, L5, L7 — OPEN.
- **C54 design-Q (6)**: B5, B6, B7, B8, B9, B14-normative-strength — OPEN.
- **C54 SDK cross-track (4)**: B1, B3, B4, B11 — STILL STALE in `metabolic.py` (bundle for a future SDK-track pass; line-anchors re-read valid).
- **C54 sister-doc cross-track (2)**: B14 (SOCIETY_SPEC §1.4 MUST-vs-SHOULD), B15 (SAL §3.6 dormant omits Rest, dual-anchored C98-B9) — OPEN, snapshot-stable.
- **C96-E1 (INFO, cross-track → atp-adp §3.3)**: metabolic §6.1 hourly maintenance cost = unnamed third member of the atp-adp §3.3 demurrage/slashing maintenance-discharge carve-out; compliant-by-carve-out. **Anchor (§3.3, atp-adp:329) confirmed present and unmoved by C119.** Fix (if any) is a one-line atp-adp-side enumeration — not the frozen target.
- **C58-B10 / C96-C58-link (DESIGN-Q double-anchor)**: new-citizen defer-vs-wake — two-sided, both anchors frozen, STANDS. Route to operator bundle.
- **Subordinate-ontology cluster / M7**: absent, operator-flagged; no autonomous TTL drafting.

### New at C133
**None.** 0 net-new autonomous defects; 0 new INFO/DESIGN-Q. Both moved siblings proven disjoint. No carry elevated or resolved this fire.

**None of the standing carries gate a normal AUDIT turn.** All route to the standing operator DESIGN-Q bundle / SDK-track / atp-adp-track. Surface as part of the one-decision memo when the operator is available.

---

## 5. §D — Method Notes

1. **2nd consecutive fully-clean metabolic delta; frozen-target steady-state holds.** C96 and C133 both hit a target unchanged since its C55 remediation, both returned 0 autonomous defects. The round-robin remains in steady state — files churn slower than the audit cadence, so §A is verification and §B's yield is entirely on the moved-sibling surface.
2. **Disjointness proven, not asserted (C120/C123/C132 discipline).** Both moved siblings were cleared by citing the specific moved hunk: C119's §7.1 MUST #6 is a **value**-tracking carve-out (parallel to §3.3, per C119's own text), while metabolic couples only to the §3.3 **discharge** carve-out (C96-E1) — a different carve-out — and the target has **zero value/V3/aggregate surface** (grep-verified) so the MUST #6 change cannot reach it. #445 touches no metabolic files and the Rust `EntityTrust` tensor is not the Python `TrustEffect`.
3. **MUST-vs-impl class (C116-N1/C118-N1) checked and did not fire** — the policy-review load-bearing condition. Metabolic §6.1 is a discharge locus but restates no entity-level value MUST (no value surface), so the moved atp-adp MUST #6 creates no MUST-vs-impl contradiction. This confirms the C120→C121 KEY SIGNAL that the class is DOC-SPECIFIC and confined to docs whose normative-summary unconditionally restates entity MUSTs (mcp §12, atp-adp §7.1) — metabolic is not such a doc for the *value* axis.
4. **C96-E1 anchor still-present verified live** (`atp-adp-cycle.md:329`), distinguishing "carry open + anchor unmoved" from "silently resolved downstream" (C106/C120 snapshot-presence guard). C119 added a *parallel* MUST #6 carve-out that references §3.3 but did not move §3.3 itself.
5. **Severity discipline held.** 0 HIGH / 0 net-new is the honest result for a mature twice-remediated frozen spec; no finding manufactured to fill the turn (anti-padding, per C94/C96/C132 precedent + policy-review non-blocking guidance).

---

## 6. Conclusion

C133 is the **3rd delta re-audit** of `SOCIETY_METABOLIC_STATES.md` (lineage C21→C54→C55→C96→C133). The target is **byte-frozen since the C55 remediation** (19 days); SDK `metabolic.py` frozen since C96.
- **§A**: 5/5 C55 remediations HELD (0 regressed); frozen window regression-free; all standing carries STAND (8 C21 design-Q + 6 C54 design-Q + 4 SDK cross-track B1/B3/B4/B11 still-stale, line-anchors re-read + 2 sister-doc B14/B15 open/snapshot-stable); M7 ontology absence HOLDS; §10 conformance re-tested exact.
- **§B**: corpus-delta + inbound-carry sweep → **0 net-new autonomous defects (2nd consecutive fully-clean metabolic delta)**. Both moved siblings proven DISJOINT by cited hunk — atp-adp C119 moved the MUST #6 *value*-tracking carve-out (metabolic has zero value surface + couples only to the distinct §3.3 discharge carve-out, C96-E1 anchor intact); trust-tensor #445 touches no metabolic files. C58-B10 defer-vs-wake DESIGN-Q re-verified two-sided/open (both anchors frozen).
- **§C**: all carries reconciled; **0 new, 0 elevated, 0 resolved** this fire; none gate a normal turn.
- **NO spec mutation. 0 autonomous items for the next remediation slot.**
- Next: the **C134 metabolic REMEDIATION slot = NO-OP** (0 autonomous to apply, like C97). Rotation advances to next-oldest = **SAL** (`web4-society-authority-law.md`, last audited C98/C99, 2026-06-25) for its **3rd-delta** (≈C134). [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, **SAL**, LCT, ISP, entity-types, errors, security, registries, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.]

---

*Audit produced under Autonomous Session Protocol v2 by legion-web4-20260703-180036 (LEAD, slot 000036). Read-only: zero edits to web4-standard/ or SDK source; this audit document is the only web4-repo write. Policy-review APPROVED first-pass with 2 binding conditions (worktree-cwd write; live-hunk disjointness check) — both satisfied.*
