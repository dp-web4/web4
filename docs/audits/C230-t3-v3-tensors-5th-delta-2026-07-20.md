# C230 Audit: `t3-v3-tensors.md` 5th Delta Re-Audit

**Date**: 2026-07-20
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn, slot `web4-20260720-000036`
**Document**: `web4-standard/core-spec/t3-v3-tensors.md` (690 lines at HEAD; was byte-frozen since C122 `b2a98f7c` — **now moved** to blob `32d3368e`)
**Prior passes**: C13 (internal-consistency) → C42 (1st delta) → **C43 remediation** (#299) → C82 (2nd delta) → **C83 remediation** (#374) → C118-N2 applied at **C122** (#427) → C154 → **C192** (4th delta, first Rust-mirror gate, N1–N4). This is the **5th delta** (rotation +2 from C228/atp-adp; multi-device empirically skipped).
**Methodology**: Standard delta re-audit. §A = whole-file diff since the C122 freeze + regression sweep + C42/C13/C82/C83 carry re-verification. §B = corpus-delta + **SDK-mirror re-derivation at live HEAD**, whose flagship is the remediation-verification of C192-N1 (did #517 close it, and did the fix regress anything?). §C = bidirectional re-verify of standing DESIGN-Qs D1/D2/D3 + C192-N2/N3/N4. Refute-by-default; every load-bearing claim hand-verified against source and the pre-change blob.
**Reference materials** (blobs at HEAD `02ef374b`): spec `t3-v3-tensors.md` (`32d3368e`); Python SDK `trust.py` (`93dd41c4`); Rust `web4-core/src/t3.rs` (`98bb8c58`) + `v3.rs` (`bdbeacc6`); `web4-trust-core/src/tensor/mod.rs` (`38547600`) + `entity/trust.rs` (`ee27e47f`); LCT spec `LCT-linked-context-token.md` §1.2; ontology `t3v3-ontology.ttl`; test vectors `test-vectors/t3v3/tensor-operations.json`.

---

## Summary

| | Count / Verdict |
|---|---|
| **§A** spec delta since C122 freeze | **1 net-new** (#531 §1.1 cross-ref) — accurate, CONSISTENT, accountability-strengthening |
| **§A** frozen-body regression sweep | 0 regression (whole-file diff = the one insert; all C42/C13/C82/C83/C122 carries HELD; anchors shifted uniformly +2 below L16) |
| **§B** spec-side substantive findings | **0** (spec CORRECT throughout) |
| **§B** flagship — C192-N1 (MEDIUM live SDK divergence) | **CLOSED + VERIFIED** by #517 (both Rust layers fixed; no regression) |
| **§B** SDK-mirror net-new findings | **0** (only #517 touched the mirror set since C192; C192-N2/N3/N4 STAND unchanged) |
| **§C** DESIGN-Q re-verification | D1 STILL-OPEN · D2 STILL-OPEN · **D3 STILL-OPEN** (hardening from C192-N2 stands; not re-hardened) |

**Health verdict**: `t3-v3-tensors.md` is **spec-side substantive-CLEAN** at this 5th delta. The two motions since C192 are both **healthy**: (1) the spec gained one accurate cross-ref paragraph (#531) tying T3/V3 to the newly-canonized *Inspectable Evidence, Not Prescribed Trust* principle (LCT §1.2) — a **strengthening** of the file's own role-contextual, evidence-not-verdict framing, not a defect; and (2) the SDK gained #517, which **correctly and completely closes the prior delta's flagship finding C192-N1** (the Talent-no-decay protocol-invariant violation), with no regression. This is the first t3-v3 delta whose net-new value is a **remediation-closure witness** rather than a new finding — the C13→…→C192 cycle now has zero open spec-side items and its one live SDK divergence resolved.

---

## §A — Spec Delta + Regression Sweep

**The C122 byte-freeze ended.** `t3-v3-tensors.md` moved `b2a98f7c`→`32d3368e` via **#531** (`d89595e8`, "docs(spec): canonize 'Inspectable Evidence, Not Prescribed Trust' principle"). The whole-file diff `b2a98f7c → HEAD` is **exactly one inserted paragraph** (plus its blank line) at §1.1 L16:

> Tensors are **evidence, not verdicts**: a T3/V3 score is inspectable input a relying party weighs, scaled to the stakes of the act — the standard never prescribes a trust threshold. See the LCT spec §1.2, *Inspectable Evidence, Not Prescribed Trust*.

Nothing else in the file changed. Consequences:

1. **All prior carries HELD by construction.** Because the body below L16 is byte-identical, every C42/C13/C82/C83/C122 finding verified HELD at C82/C192 is untouched. Spot-re-verified the load-bearing anchors (all shifted uniformly **+2** from the insert):

   | Value | C192 line | HEAD line | Status |
   |-------|-----------|-----------|--------|
   | §2.3 "Talent Stability: No decay" | L123 | **L125** | HELD |
   | t3v3-012 "Talent MUST NOT decay" | L633 | **L635** | HELD |
   | §10.2 ATP-conservation anchor (C83-F2/C118-N2) | L640 | **L642** | HELD, still accurate |
   | §10.4 anti-example "0.995 per period" | L673 | **L675** | HELD |
   | t3v3-001/002 composite weights `0.4/0.3/0.3`, `0.3/0.35/0.35` | L629/630 | **L631/632** | HELD |
   | C83-F3 §3.3 "distinct weights" | L336 | **L339** | HELD |

   **Provenance note for the next delta** ([[feedback_prior_finding_path_provenance]]): every previously-cited t3-v3 line number **at or below §1.1 shifts +2**. Re-grep at live HEAD; do not carry stale numerics.

2. **Cross-ref accuracy — VERIFIED.** The target exists and is cited correctly: `LCT-linked-context-token.md:26` is `### 1.2 Design Principle: Inspectable Evidence, Not Prescribed Trust` — title byte-matches the citation. LCT §1.2 explicitly enumerates "**a T3/V3 tensor**" among "evidence a relying party weighs, contextually and scaled to the stakes of the specific act. It is never a verdict the protocol renders." The new §1.1 paragraph is a **faithful, bidirectional** summary — LCT §1.2 names T3/V3; t3-v3 §1.1 points back. No over-claim, no mis-citation.

3. **Accountability lens (RWOA+S+V).** The addition is **docs-only, no surface** — it creates no path to a consequential act; it *describes a constraint on* surfaces (a conforming surface MUST NOT encode a universal trust threshold). It therefore has no S/R/W/O/A/V obligation of its own, and it **hardens** the corpus-wide accountability norm rather than relaxing it. No conflict with t3-v3's composite weighting (aggregation ≠ a threshold/verdict) or TrustLevel bucketing (a convenience mapping, not a protocol-enforced exclusion).

**§A verdict: 1 accurate net-new cross-ref, 0 regression, all carries HELD.**

---

## §B — SDK-Mirror Re-Derivation + C192-N1 Closure (flagship)

Re-derived the mirror set at live HEAD (`git log fce49107..HEAD` over `t3.rs`, `v3.rs`, `tensor/mod.rs`, `entity/trust.rs`, `trust.py`). **Exactly one commit** touched it since C192: **#517** (`5cb536bf`, "fix(t3): Talent no-decay invariant … — audit C192-N1"). No new implementers appeared; `v3.rs` and `trust.py` were untouched.

### C192-N1 — CLOSED + VERIFIED (no regression)

C192-N1 (MEDIUM, live) held that **both** Rust decay layers violated the doubly-stated protocol invariant "Talent MUST NOT decay through inactivity" (§2.3 L125, t3v3-012 L635), with `web4-trust-core` using the **literal `0.995`** §10.4 pre-emptively names as spec-violating. #517 fixes **both** flagged sites; verified against the pre-#517 blob (`659e2f64` t3.rs, `c5b60...` diffed):

- **web4-core `T3::decay`** (`t3.rs:350`) — new guard `if i == TrustDimension::Talent as usize { continue; }` skips **both score and weight** for Talent (the `continue` precedes both the score-toward-neutral and the `weights[i] *= decay_factor` in the same loop body). Sub-dimensions gained `if sub.parent == TrustDimension::Talent { continue; }` so Talent-parented sub-dims (which roll up to the no-decay root) are also exempt. Two new tests assert exact stability: `test_decay_moves_toward_neutral_except_talent` (`assert_eq!(score(Talent),0.9)` + `assert_eq!(weight(Talent), before)`) and `test_decay_exempts_talent_sub_dimensions`.
- **web4-trust-core `t3_apply_decay`** (`tensor/mod.rs:189`) — the `decay_value(old_talent, 0.995)` triple (read/decay/apply) is **removed entirely**; Training/Temperament decay unchanged; return value still keyed on Training movement (`(old_training-new_training).abs()>0.001`) — semantics preserved.
- **Oracle fixture** (`entity/trust.rs:667`, an independent re-implementation of *intended* semantics used as a cross-check) updated: `self.talent = dv(self.talent, 0.995)` deleted, Talent now passes through — so the test oracle models the spec, not the old defect (avoids masking the fix).

**Correctness**: the fix matches the Python SDK reference (`trust.py::decay`, which was already correct and left Talent untouched), matches spec §2.3/t3v3-012, and neutralizes the exact §10.4 anti-value. Commit reports "179 web4-core + 49 trust-core + 187 hestia lockstep green."

**Remediation-regression check** ([[feedback_remediation_introduced_regression]]): the fix is *subtractive* (skip/remove decay for one dimension) — it cannot decay Talent that previously decayed, and leaves Training/Temperament paths byte-identical. The one judgment call — freezing Talent's **weight** as well as its score — is defensible and deliberate: t3v3-012 states the invariant flatly ("Talent MUST NOT decay"), the PR explicitly chose "score AND weight," and a stable-aptitude assessment retaining its observation-confidence under inactivity is coherent (an inactive entity's Talent confidence does not erode). No spec text distinguishes weight from score decay, so the conservative reading conforms. **No regression introduced.**

**Verdict**: C192-N1 **CLOSED**. Route (SDK-track) discharged by #517. Nothing owed.

### C192-N2 / N3 / N4 — STAND unchanged (untouched by #517)

- **C192-N2 → D3** (web4-core `v3.rs` clamps V3 Valuation, hardening the clamp-resolution DESIGN-Q): `v3.rs` was **not** touched by #517. STANDS. The 3-way divergence (spec+ontology unbounded vs. Python+Rust clamped) is unchanged — still 2-vs-1 toward clamping. Operator DESIGN-Q.
- **C192-N3** (INFO — protocol-invariant composite + §2.3 update magnitudes are Python-only; web4-core `aggregate()` is confidence-weighted, not protocol-weighted): unchanged. Wire-layer forward-awareness; joins the C180–C190 SDK wire-readiness synthesis. STANDS.
- **C192-N4** (INFO — Rust tensors carry no entity-role binding; §6.3 role-segregation MUST is a higher-layer concern): unchanged. STANDS; feeds D2.

**§B verdict: 0 spec defect; 0 net-new SDK finding; flagship C192-N1 CLOSED+VERIFIED; N2/N3/N4 STAND.**

---

## §C — Standing Operator DESIGN-Q (bidirectional re-verification)

- **D1 — ontology-vocabulary divergence — STILL-OPEN.** `web4:matchesTask` (§9.2) still appears once corpus-wide with no defining triple; role IRIs (`web4:Surgeon` etc.) remain undeclared as classes/individuals. #531 does not touch §9. Fold into the standing C40 ontology-vocab bundle.
- **D2 — X4 (mrh §5 duplication) + N4 role-binding + multi-device attach — STILL-OPEN.** mrh §5 still duplicates this file's role-contextual principle + Surgeon Turtle; the **Surgeon `training` 0.92 (t3-v3) vs 0.90 (mrh)** cross-doc contradiction stands (mrh-side fix). C192-N4 (SDK tensor primitive also lacks role binding) unchanged corroborating datapoint. The attach-strategy operator decision still gates the multi-device rewrite.
- **D3 — M4 Valuation range 3-way divergence — STILL-OPEN (C192 hardening stands).** spec+ontology (unbounded) vs. Python-SDK + Rust web4-core (both clamped). Not re-hardened this delta (`v3.rs` unchanged); the 2-vs-1-toward-clamping posture holds. Operator semantic decision still required. Couples C42 F1/F25.

---

## §D — Lessons

1. **A delta's net-new value can be a remediation-closure witness, not a new finding.** C230 opened no new item — its yield is *confirming* that #517 fully and correctly closed C192-N1 across both Rust layers with no regression. The standing method's "delta re-audits must check whether prior remediation introduced NEW defects" ([[feedback_remediation_introduced_regression]]) here returns a clean bill: the fix is subtractive and the Oracle fixture was correctly updated to model the spec rather than mask the change. Closing the loop on a prior finding is itself audit output.
2. **When a byte-freeze ends, diff against the freeze SHA — not the last audit HEAD — to bound the delta exactly.** Diffing `b2a98f7c → HEAD` proved the spec motion is a single paragraph, collapsing the §A regression sweep to a line-number-shift check. The freeze SHA is the tightest baseline.
3. **A docs cross-ref that points *at* a newly-canonized principle can strengthen a file's accountability posture without adding a surface.** #531's §1.1 insert makes explicit what t3-v3 already implied (tensors are role-contextual evidence, not verdicts) — the RWOA lens correctly returns "no surface, hardens the norm," distinguishing description-of-a-constraint from a consequential path.

---

## Disposition

- **Spec-side (this file)**: substantive-CLEAN. **No C231 remediation item owed on `t3-v3-tensors.md`.** The #531 §1.1 cross-ref is accurate and stays.
- **Closed this delta**: **C192-N1** (MEDIUM, live) — Talent-no-decay violation in web4-core `T3::decay` + web4-trust-core `t3_apply_decay` — **CLOSED + VERIFIED by #517** (`5cb536bf`), no regression. Remove from the SDK-track live-carry set.
- **Still routed off-spec (SDK-track, unchanged)**: **C192-N3** (composite/update-formula Python-only), **C192-N4** (Rust tensors carry no role binding). Both INFO, join the wire-layer-readiness synthesis / feed D2.
- **Operator DESIGN-Q (unchanged)**: **C192-N2 → D3** (2nd SDK clamps V3 Valuation), **D1** (ontology-vocab), **D2** (mrh §5 dup + Surgeon 0.92-vs-0.90 + multi-device attach). Route to the single operator memo; do NOT self-apply.

The C13→C42→C43→C82→C83→C122→C192→C230 cycle for `t3-v3-tensors.md` remains in **excellent health**: five deltas, zero spec-side regressions, all remediation accurate, and — as of this delta — its one live SDK-invariant violation resolved. **Next fire = C232 = reputation-computation** (next file in the rotation). The **next t3-v3 delta is a full rotation later** (~C268); when it comes, re-baseline the spec from `32d3368e` (no longer `b2a98f7c`) and re-grep every cited line number (+2 shift below §1.1).
