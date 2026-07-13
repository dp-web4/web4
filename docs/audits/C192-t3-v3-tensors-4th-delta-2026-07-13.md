# C192 Audit: `t3-v3-tensors.md` 4th Delta Re-Audit

**Date**: 2026-07-13
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn, slot `web4-20260713-060036`
**Document**: `web4-standard/core-spec/t3-v3-tensors.md` (688 lines; byte-frozen since C122 `b2a98f7c`)
**Prior passes**: C13 (internal-consistency, 11 findings) → C42 (1st delta, 20 actionable) → **C43 remediation** (PR #299, 13 edits) → C82 (2nd delta, 6 findings F1–F6) → **C83 remediation** (PR #374, 5 autonomous edits) → C118-N2 applied at **C122** (PR #427). This is the **4th delta** (rotation +2 from C190/atp-adp).
**Methodology**: Standard delta re-audit. §A = C82/C83 remediation-completeness + C42/C13 carry re-verification + frozen-since-C122 regression argument. §B = corpus-delta + inbound-carry scan + **the first Rust SDK-mirror gate for this file** (C82 cross-checked only Python `trust.py`). §C = bidirectional re-verification of the 3 standing operator DESIGN-Qs. Refute-by-default; every load-bearing claim hand-verified against source.
**Reference materials** (frozen SHAs at HEAD `fce49107`): Python SDK `web4-standard/implementation/sdk/web4/trust.py` (`759eaefa`), Rust `web4-core/src/t3.rs` + `v3.rs` (`20ef29f5`), Rust `web4-trust-core/src/tensor/mod.rs` + `entity/trust.rs` (`20ef29f5`), ontology `t3v3-ontology.ttl`, test vectors `test-vectors/t3v3/tensor-operations.json`.

---

## Summary

| | Count |
|---|---|
| **§A** C82/C83 remediation edits re-verified | 5/5 PRESENT + HELD (0 regressed) |
| **§A** C42/C13 carries | all HELD (file byte-frozen since C122; spot-verified load-bearing values) |
| **§B** spec-side substantive findings | **0** (spec CORRECT throughout) |
| **§B** SDK-mirror gate net-new findings | **4** (1 MEDIUM live divergence / 1 DESIGN-Q datapoint / 2 INFO layer-observations) — all route off-spec |
| **§C** DESIGN-Q re-verification | D1 STILL-OPEN · D2 STILL-OPEN · **D3 HARDENED** (2nd SDK clamps Valuation) |

**Health verdict**: `t3-v3-tensors.md` is **spec-side substantive-CLEAN** at this delta — all 5 C83 edits hold, no regression, and the SDK-mirror gate found **no spec defect**. The gate result is a **GENUINE mirror with LAYER-SPLIT** (parallel to C190/`atp.rs`): the Rust `web4-core` tensors genuinely mirror the §2.1 root-dimension model, the §2.4 fractal sub-dimension graph, and the `[0,1]` clamp as a **data-structure / observation primitive** — but the **protocol-invariant composite** (fixed weights, t3v3-001/002), the **§2.3 update formula**, and the **Talent-no-decay invariant** are either Python-SDK-only or *divergent in the Rust layer*. One divergence is a **live, spec-named violation** (N1). The spec itself is correct on every point — indeed §10.4 pre-emptively documents the exact violation N1 exhibits.

---

## §A — Remediation Completeness + Carry Verification

The file is **byte-frozen since C122 `b2a98f7c`** (verified: `git log` shows no commit to `t3-v3-tensors.md` after C122). All C42/C13 carries verified HELD at C82 therefore cannot have regressed. Load-bearing values spot-re-verified against Python SDK constants at HEAD:

| Spec value | Location | SDK constant | Verdict |
|-----------|----------|--------------|---------|
| T3 composite weights `0.4/0.3/0.3` | §9.2 L556, §10.2 L629 | `T3_WEIGHTS` (`trust.py:77`) | ✓ match + t3v3-001 |
| V3 composite weights `0.3/0.35/0.35` | §3.3 L333, §10.2 L630 | `V3_WEIGHTS` (`trust.py:78`) | ✓ match + t3v3-002 |
| T3 update formula `0.02×(quality−0.5)` + factors `1.0/0.8/0.6` | §2.3 L110–111, §10.2 L631–632 | `T3_UPDATE_FACTORS` (`trust.py:179–181`) | ✓ match |
| Diminishing returns `0.8^(n−1)`, floor `0.1` | §7.1 L477–480, §10.2 L636 | `trust.py` DIMINISHING_* | ✓ match + t3v3-007 |
| ATP-conservation anchor (C83-F2/C118-N2) | §10.2 L640 | — | ✓ accurate (re-confirmed at C190; **not** re-flagged) |

**C83 remediation edits (5/5 PRESENT + HELD):**
- **F2** — §10.2 L640 ATP-conservation row re-anchored off the §2.4 "Slashing" section to §3.1/§3.2 supply-equation + §6.3 fee-recycling, with §2.4 annotated as the deliberate exception and the per-transfer form `initial == final + fees` noted. ✓ (Re-verified ACCURATE at C190 — do NOT re-flag per standing guard.)
- **F3** — §3.3 L336–337 "**parallels** the T3 composite *structure* … but uses its own weights (V3 `0.3/0.35/0.35`, distinct from T3's `0.4/0.3/0.3`)". ✓ False numeric-equivalence removed.
- **F4** — §10.2 L635 V3 Veracity/Validity range row notes clamping is "SDK-enforced in `V3.__post_init__`; no dedicated V3 boundary vector — t3v3-002/t3v3-014 exercise interior values only". ✓
- **F5** — SPARQL `PREFIX` declarations present in §9.2 (L544) and both §9.3 queries (L570–571, L585–586). ✓
- **F6-partial** — the **entire §2.5 "Bridging Flat (6-Dimensional) Trust Schemas"** section (L204–246, bridge body prose + 6-input weighting table + multi-device key mapping) plus the §2.4 protocol-extension paragraph (L193–202) naming `hardware_binding_strength` / `constellation_coherence` as candidate sub-dimensions. ✓ The C82 "owner-side documentation gap" (opaque one-row bridge, no body prose) is substantially closed.

**§A verdict: 5/5 C83 edits HELD, all carries HELD, 0 regression.**

---

## §B — SDK-Mirror Gate (first Rust pass for t3-v3)

C82 cross-checked **only** Python `trust.py`. This delta re-derives the mirror at live HEAD against the untracked Rust twins — the frontier where net-new lives ([[feedback_prose_is_not_ledger]]: verified none of these was parked in C82's prose; C82's reference list explicitly excluded `t3.rs`/`v3.rs`).

### The three-layer picture

| Concern (spec) | `web4-core` t3.rs/v3.rs | `web4-trust-core` tensor/mod.rs | Python `trust.py` |
|----------------|------------------------|----------------------------------|-------------------|
| 3 root dims + names (§2.1/§3.1) | ✓ genuine | (uses web4-core types) | ✓ |
| Fractal sub-dimensions `subDimensionOf` (§2.4) | ✓ genuine (`sub_dimensions` HashMap + `parent`) | — | — |
| `[0,1]` clamp for T3 + V3 Veracity/Validity (§2.1/§3.1) | ✓ genuine | — | ✓ |
| **Protocol-invariant composite** `0.4/0.3/0.3` & `0.3/0.35/0.35` (t3v3-001/002) | ✗ ABSENT (`aggregate()` = confidence-weighted geo/arith mean) | ✗ (only flat `t3_average`/`v3_average` for `TrustLevel` bucketing) | ✓ `composite()` (`:161`,`:294`) |
| **§2.3 update formula** `0.02×(q−0.5)`, factors `1.0/0.8/0.6` | ✗ (raw `apply_delta`; magnitude computed elsewhere) | ✗ DIVERGENT bespoke law (`t3_update_from_outcome`: `mag×0.05×(1−training)` …) | ✓ `from_action` |
| **Talent no-decay** (§2.3 L123, §10.2 t3v3-012) | ✗ **VIOLATED** (`decay()` moves all 3 toward 0.5) | ✗ **VIOLATED** (`t3_apply_decay` decays talent, factor `0.995`) | ✓ correct (`decay()` leaves `talent` untouched, `:200`) |
| V3 Valuation range (§3.1, D3) | clamps `[0,1]` | (via web4-core) | clamps `[0,1]` |
| Entity-**role** binding (§1.1/§6.3 MUST) | ✗ bare tensor; `TrustRelation` is entity→entity | ✗ `EntityTrust` holds tensors directly | (role-keyed at a higher layer) |

**Gate verdict: GENUINE mirror + LAYER-SPLIT.** web4-core built the tensor **data-structure / observation / confidence / merge / decay / persistence** layer; the **protocol-invariant composite + §2.3 update magnitudes + Talent-no-decay** layer is Python-only or divergent. Same shape as C184/C188/C190 (primitives shipped, protocol/wire layer lags). The spec is CORRECT on every point tested.

### Findings (all route off-spec; NONE is autonomous spec mutation)

#### N1 — MEDIUM (live SDK divergence) — Rust decay violates the Talent-no-decay protocol invariant, using the exact value §10.4 names as spec-violating
The protocol invariant is unambiguous and doubly stated:
- §2.3 L123–125: "**Talent Stability**: No decay … This is a normative protocol property, not a tunable parameter."
- §10.2 L633 (t3v3-012): "**Talent no-decay** | Talent MUST NOT decay through inactivity".
- §10.4 L673 (simulation-only anti-example): "Talent decay/half-life | **'0.995 per period'** | Talent no-decay is a protocol invariant (§2.3); **any decay value violates the spec**".

Both Rust layers decay Talent through inactivity:
- `web4-core::t3::T3::decay(factor)` (`t3.rs:350–358`) moves **all three** `dimensions[i]` (Talent is index 0) toward neutral 0.5.
- `web4-trust-core::tensor::t3_apply_decay(days_inactive, decay_rate)` (`tensor/mod.rs:174–197`) decays Talent at line 193: `decay_value(old_talent, 0.995)` — the **literal `0.995`** §10.4 flags by name.

This is **live**, not hypothetical: the public `EntityTrust::apply_decay(days_inactive, decay_rate)` (`entity/trust.rs:420–424`) calls `t3_apply_decay` on the at-rest trust store's inactivity path. Worked example: `talent=0.9`, 30 days at `decay_rate=0.01` → `decay_factor=(0.99)^30≈0.74` → `new_talent = 0.3 + 0.6×0.74×0.995 ≈ 0.742` (a 0.16 drop). Python `trust.py` `decay()` correctly leaves Talent untouched.
**Adversarial refutation attempted & failed**: `t3_apply_decay` is parameterized by `days_inactive` — unambiguously the protocol inactivity-decay path, not a generic utility; the floor-0.3 model still moves Talent for any `talent>0.3`. Finding holds.
**Direction**: spec CORRECT (and pre-emptively documents this exact violation). **Route: web4-core + web4-trust-core SDK-track.** Fix = exempt Talent from decay in both Rust decay functions (or, if these are deliberately non-protocol utilities, gate them so `EntityTrust::apply_decay` cannot reduce Talent). NOT autonomous (SDK code, not spec).

#### N2 — DESIGN-Q datapoint (feeds standing D3 / C13-M4) — Rust web4-core is a 2nd SDK clamping V3 Valuation
`web4-core::v3::V3` clamps Valuation to `[0,1]` (`with_scores` rejects `>1.0` `v3.rs:108–115`; `apply_delta`/`observe` clamp `:191`,`:210`), exactly as Python `trust.py` `V3.__post_init__` does (`:289`). The standing C13/M4/D3 divergence — spec §3.1 "Range: Variable (can exceed 1.0)" + ontology `t3v3-ontology.ttl:90` "may exceed for value" vs. SDK-clamped — is now **spec+ontology (unbounded) vs. TWO SDK implementations (Python + Rust, both clamped)**. This **hardens** D3 and strengthens the "clamp the spec/ontology" resolution option. Operator DESIGN-Q; **NOT autonomous**. Record under §C-D3.

#### N3 — INFO (layer-observation, wire-layer forward-awareness) — protocol-invariant composite absent from Rust
web4-core `T3::aggregate()` is a **confidence-weighted geometric mean** (`t3.rs:270–288`) and `V3::aggregate()` a **confidence-weighted arithmetic mean** (`v3.rs:256–270`) — weights derived from observation counts, **not** the protocol constants `0.4/0.3/0.3` / `0.3/0.35/0.35`. web4-trust-core exposes only flat `t3_average`/`v3_average` (for `TrustLevel` bucketing, explicitly *not* the composite — `tensor/mod.rs:104–114`). The **fixed-weight protocol composite (t3v3-001/002) lives ONLY in Python `trust.py` `composite()`**. Likewise the §2.3 update magnitudes are Python-only; web4-trust-core's `t3_update_from_outcome` uses a *different* bespoke update law. **Forward-awareness**: a wire/protocol layer needing t3v3-001/002 conformance MUST NOT use web4-core `aggregate()`. Spec CORRECT.

#### N4 — INFO (layer-observation) — Rust tensors carry no entity-role binding
web4-core `T3`/`V3` are bare tensors; `TrustRelation` keys by entity→entity (`from_id`/`to_id`, `t3.rs:426–441`), and `EntityTrust` holds tensors directly — neither carries a `role`. The §1.1/§6.3 role-contextual MUST ("MUST NOT compute global role-agnostic trust; each role MUST maintain separate tensors") is therefore a **higher-layer responsibility not enforced by the tensor primitive** — the same architectural shape as the `atp.rs` account primitive (C190) and the multi-device flat-8 (C82 N1/N2). Whichever layer keys tensors by role owes the §6.3 enforcement. Spec CORRECT (this is an SDK-composition constraint, feeds §C-D2).

### Checked and REFUTED / clean-bill
- Rust `T3::with_scores`/`observe` **reject** out-of-range vs §2.1 "clamped" — NOT a defect: the *update* path (`apply_delta`, the R7-delta fold) clamps as §2.1 requires; input constructors validating stricter is a superset, not a contradiction.
- Rust geometric-for-trust / arithmetic-for-value aggregate SHAPES correctly reflect the spec's conceptual distinction (§8.2 "cannot average trust across roles"; value allows specialization) — the divergence is in the WEIGHTS (confidence vs protocol), captured in N3, not the shape.
- Sub-dimension `parent`-linked model + EMA math — faithful to §2.4 fractal graph. Genuine.

---

## §C — Standing Operator DESIGN-Q (bidirectional re-verification)

- **D1 — ontology-vocabulary divergence — STILL-OPEN.** `web4:matchesTask` (§9.2) still appears once corpus-wide with no defining triple; role IRIs (`web4:Surgeon` etc.) remain undeclared as classes/individuals. File frozen; no movement. Fold into the standing C40 ontology-vocab bundle.
- **D2 — X4 (mrh §5 duplication) + N1/N2 multi-device attach — STILL-OPEN.** mrh §5 still duplicates this file's role-contextual principle + Surgeon Turtle; the **Surgeon `training` 0.92 (t3-v3) vs 0.90 (mrh)** cross-doc contradiction stands (mrh-side fix). **New corroborating datapoint**: this delta's N4 shows the SDK tensor primitive *also* lacks entity-role binding — the same "flat/role-agnostic tensor" shape as the multi-device consumer defect, now observed a third time. The attach-strategy operator decision (formalize-bridge / declare-sub-dims / both) still gates the multi-device rewrite.
- **D3 — M4 Valuation range 3-way divergence — HARDENED.** Was spec+ontology (unbounded) vs. Python-SDK (clamped). Now **2 SDKs clamp** (Python + Rust web4-core, per N2). The 3-way is now lopsided 2-vs-1 toward clamping. Operator semantic decision still required (clamp spec/ontology, or unbound both SDKs); the added Rust datapoint argues for the clamp resolution. Couples C42 F1/F25.

---

## §D — Lessons

1. **The SDK-mirror gate's yield is real and file-specific — a "very-good-health" spec can be spec-side-CLEAN yet sit atop a live SDK invariant violation.** t3-v3 is among the most-remediated core-spec docs (C13→C42→C82, 0 regressions), and C82 gave it a clean bill against Python `trust.py`. The *Rust* mirror — never before checked for this file — carries a **live protocol-invariant violation** (N1). Confirms the standing method guard: re-derive target-primitive implementers at live HEAD across **both** Python SDK **and** `web4-core`/`web4-trust-core` before declaring §B clean.
2. **When a spec pre-emptively names an anti-value, grep the SDK for that literal.** §10.4 names "`0.995 per period`" Talent decay as spec-violating; `web4-trust-core` hard-codes `decay_value(old_talent, 0.995)`. The spec's own simulation-only table is a ready-made test oracle for SDK divergence — the anti-examples are exactly what to search the implementation for.
3. **Layer-split is now the dominant t3-v3-class gate outcome, but with a divergence rather than clean (unlike C190).** web4-core ships the tensor *data-structure/observation* layer (genuine); the *protocol-invariant composite + update-formula + Talent-no-decay* layer is Python-only or divergent. This is C190's layer-split shape (`atp.rs` account-primitive genuine, pool/governance absent) — except here the SDK layer that *does* exist actively contradicts an invariant (N1), so the verdict is GENUINE-mirror-with-divergence, not GENUINE-and-CLEAN.

---

## Disposition

- **Spec-side (this file)**: substantive-CLEAN. **No C193 remediation item owed on `t3-v3-tensors.md`.**
- **Routed off-spec (SDK-track)**:
  - **C192-N1** (MEDIUM, live) — web4-core `T3::decay` + web4-trust-core `t3_apply_decay` decay Talent, violating §2.3/§10.2 t3v3-012 (using the §10.4-named `0.995`). Route: web4-core + web4-trust-core owners. Fix = exempt Talent from decay.
  - **C192-N3** (INFO) — protocol-invariant composite + §2.3 update magnitudes are Python-only; web4-core `aggregate()` is confidence-weighted, not protocol-weighted. Wire-layer forward-awareness (joins the C180/C182/C184/C188/C190 SDK wire-layer-readiness synthesis).
  - **C192-N4** (INFO) — Rust tensors carry no entity-role binding; §6.3 role-segregation MUST is a higher-layer concern. Feeds D2.
- **Operator DESIGN-Q**:
  - **C192-N2 → D3** — 2nd SDK (Rust web4-core) clamps V3 Valuation; hardens the C13/M4/D3 range divergence toward the clamp resolution.
  - **D1** (ontology-vocab), **D2** (X4 mrh §5 shrink + Surgeon 0.92-vs-0.90 + multi-device attach) — unchanged, still operator/sibling-gated.

The C13→C42→C43→C82→C83→C122→C192 cycle for `t3-v3-tensors.md` remains in **excellent health**: zero regressions across four deltas, all remediation accurate, and the spec is correct even where its Rust SDK is not. The net-new value this delta added was **the first Rust-mirror pass**, which surfaced a live invariant violation the spec had already anticipated.
