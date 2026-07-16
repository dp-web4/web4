# C200 Audit: `mrh-tensors.md` Fifth Delta Re-Audit (+ C199 presence no-op declaration)

**Date**: 2026-07-16
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn, slot `web4-20260716-060036`
**Document**: `web4-standard/core-spec/mrh-tensors.md` (420 lines; **byte-frozen since C163 `b8740803`**, 2026-07-09 — `git diff b8740803 HEAD` empty across the file; prior freeze was C91 `f0c82118`, broken only by C163's single §4.2 edit)
**Lineage**: C10 → C40 → C41 (remed, #290) → C90 (2nd delta) → C91 (remed, #382 `f0c82118`) → C129 (3rd delta, `a10affc0`) → C130 (remed of C129-O1, `4e3feb26`, #442) → C162 (4th delta, #490 `1f3b63be`) → C163 (remed, #491 `b8740803`) → **C200** (this 5th delta)
**Method**: §A prior-finding + carry verification re-run **at live HEAD** (not trusting prior line numbers) + **mandated remediation-regression check on the C163-applied §4.2 hunk** (re-derive the three propagation signatures from `mrh.py` ground truth, per C163's own forward guard) + byte-freeze confirmation + behavioural re-baseline of the propagation instrument. §B refute-by-default across three lenses: corpus-delta / **inbound cross-doc carry** / the **SDK-mirror gate — extended for the first time on mrh to `web4-core/src/*.rs`, not only the Python SDK** (prior mrh passes never examined the Rust mirror). Each surviving candidate handed to an adversarial refuter.
**Reference materials**: SDK `web4-standard/implementation/sdk/web4/{mrh.py,trust.py}`; **`web4-core/src/{lct.rs,r6.rs,role_extension.rs}`**; `t3-v3-tensors.md`; `LCT-linked-context-token.md` §5; sibling audit docs C162/C163, C192 (t3-v3 4th delta), C194 (reputation 5th delta), C196/C198; `whitepaper/sections/02-glossary/index.md`; Python 3 + rdflib.

---

## C199 — presence-protocol REMEDIATION slot: genuine no-op (declared)

Per the C155→C156 / C161→C163 precedent (a no-op remediation turn is declared inside the next audit doc, not given its own session/PR):

C198 (`docs/audits/C198-presence-protocol-5th-delta-2026-07-16.md`, PR #530, merged `487ecee3`) recorded **zero net-new autonomous findings**. Its only outputs were (i) one **routed** forward-compat INFO (B.2 — presence↔PolicyEntity `escalate` mapping for a hypothetical future v1.x LLM-backed engine, explicitly NOT self-applied) and (ii) the standing **C127-1** cross-track carry (author `Session`/`VaultEntry` schemas + 2 read vectors), operator-gated. The presence `decision` enum was adjudicated **CLEAN-BY-LAYER** and the SDK/Rust-mirror gate **NEGATIVE**.

**C199 therefore has nothing to apply. No presence file is touched.** This closes the presence C198/C199 pair.

---

## Summary

| | Result |
|---|---|
| **§A** C163 §4.2 hunk (the mandated guard) | **HELD** — re-derived from `mrh.py` ground truth; note's "Three API differences" enumeration is correct and complete; **0 regression** |
| **§A** byte-freeze | **CONFIRMED** — `mrh-tensors.md` unchanged since `b8740803`; `mrh.py` unchanged since 2026-04 (`759eaefa`) |
| **§A** propagation instrument re-baseline | **GREEN** — exactly 3 `propagate_*` fns; behaviour matches spec/pseudocode |
| **§A** C10/C40/C91/C130 carries | spot-re-verified against frozen bytes; **0 regressed** |
| **§A** standing DESIGN-Qs (D1/D4/X4/N4) | STILL-OPEN, correctly escalated; **D4 sharpened** by the Rust mirror (see N2) |
| **§B** new autonomous mrh (class-a) defects | **0** |
| **§B** inbound cross-doc carry re-adjudicated | **1 (N1, INFO, routed)** — the sibling **D2** carry's numeric facet is **STALE / refuted at live HEAD** |
| **§B** SDK-mirror gate (Rust, first time on mrh) | **1 (N2, INFO, routed)** — `web4-core::Mrh` is a GENUINE §2.1-family mirror with a trust-propagation LAYER-SPLIT; feeds D4 a third `horizon_depth` representation |
| **§B** flagship candidate | **REFUTED** — the Rust `Mrh`'s `canon §5/§5.4` citation resolves correctly to LCT §5; not a broken-citation defect |

**Verdict: `mrh-tensors.md` remains in good health and byte-stable.** The C163 remediation (its own newest net-new prose) is verified **clean with zero regression** — re-tested against ground truth, not re-read. **Zero autonomous net-new mrh defects.** Both §B items are **routed cross-track** and require no mrh edit. This is the C196/C198 frozen-target pattern: the file is stable and the yield comes from its *neighbourhood* — an inbound carry that went stale, and the untracked Rust mirror.

The session's most valuable output is **N1**: a sibling audit lineage (t3-v3/multi-device) has been carrying a cross-doc numeric contradiction ("Surgeon `training` 0.92 vs 0.90, mrh-side fix") **that C91 already closed three weeks ago** — the carry perpetuates a pre-C91 ground truth. See §B-N1 and §D.

---

## §A — Carry, Fix, and Prior-Finding Verification

### The mandated guard — C163's §4.2 hunk re-tested against `mrh.py` (HELD, 0 regression)

C163 (`b8740803`) rewrote the §4.2 SDK-divergence note from "Two API differences" to "Three," making the per-**edge** vs per-**path** scalar distinction explicit. C163's own forward guard: *"C164 (or whichever pass next reaches mrh) MUST re-test this exact hunk against `mrh.py` — not re-read it. If `mrh.py` gains a fourth propagation function or restores an edge-typed parameter, this note becomes the defect."* This is the first pass to reach it.

**Ground truth re-derived at live HEAD** (`web4-standard/implementation/sdk/web4/mrh.py`):

| SDK function | Signature (line) | `decay_factor`? |
|---|---|---|
| `propagate_multiplicative` | `(path_weights: List[float], decay_factor: float = 0.7) -> float` (L198) | **yes** |
| `propagate_probabilistic` | `(path_trusts: List[float]) -> float` (L214) | dropped |
| `propagate_maximal` | `(path_trusts: List[float]) -> float` (L228) | dropped |

- **Exactly three** `propagate_*` module functions (`grep -c "^def propagate" == 3`; `dir(mrh)` filter confirms `['propagate_maximal','propagate_multiplicative','propagate_probabilistic']`). **No 4th function.**
- **No `MRHEdge`-typed parameter restored** on any of the three — all consume `List[float]`. (`MRHEdge` still exists and is used by the *graph* layer — `MRHGraph.add_edge`, `find_paths -> List[List[MRHEdge]]` — but not by the propagation functions.)
- The §4.2 note (spec L201-208) enumerates: (1) all three consume `List[float]` not `MRHEdge`, multiplicative per-**edge** weights; (2) prob/max take per-**path** scalars not `List[List[MRHEdge]]`; (3) those two drop `decay_factor`. **All three claims match ground truth.** Enumeration is correct and complete.

**Behavioural re-baseline of the instrument** (guard against a green-on-broken-checker per [[feedback_enumeration_and_grep_hypotheses]]): `propagate_multiplicative([]) == 1.0`, `propagate_probabilistic([]) == 0.0`, `propagate_maximal([]) == 0.0`, `propagate_probabilistic([0.5,0.5]) == 0.75`, `propagate_maximal([0.3,0.9,0.6]) == 0.9`. Consistent with the pseudocode's noisy-OR (identity 0.0) and empty-guard semantics. **HELD, 0 regression.**

### Byte-freeze

- `git diff b8740803 HEAD -- web4-standard/core-spec/mrh-tensors.md` → **empty**. Frozen since the C163 remediation.
- `git diff b8740803 HEAD -- web4-standard/implementation/sdk/web4/mrh.py` → **empty**. `mrh.py` last touched 2026-04-17 (`759eaefa`, ruff format), unchanged in content since.

### C10 (9) / C40 (12) / C91 (3) / C130 (1) — spot-re-verified against frozen bytes

- **C91-N1(b)** §5.2 `web4:training 0.92` → mrh **L264** = `web4:training 0.92`. **HELD** (and this is the crux of §B-N1 below). **C91-N2** honest `ASK` (L384-386) HELD. **C91-N3** `maximal()` empty-input `default=0.0` (L230-233) HELD, behaviourally re-verified.
- **C130** FRACTAL `:143`→`:174` re-anchor — mrh **L174** = `- Default horizon_depth = 3 …`; lands exactly. HELD.
- **C40** F1 (`combined = 0.0`, L222) / F5 (§3.3 depth-bound note) / F8 (`MRHEdge` clamp note) / F10 (§4.2 divergence note) — unchanged. **C10-L2** unnumbered preamble STILL-OPEN INFO by design (C41 declined the demotion). **0 regressions.**
- **Composite arithmetic**: `0.95×0.4 + 0.92×0.3 + 0.88×0.3 = 0.920` = the `web4:t3Score 0.92` at L325. Internally consistent.

### Standing DESIGN-Qs — status

- **D1** (ontology-vocabulary divergence) — unchanged, still escalated. §B-N2(b) is a fresh sibling datapoint.
- **D4** (`horizon_depth = 3` at L174 vs `MRH_MAX_HOPS = 4` at `trust.py:91` + code-only zone taxonomy) — anchors re-baselined: `trust.py:91` `MRH_MAX_HOPS = 4  # 5+ hops = BEYOND = zero trust` still present; zone check at `:558`/`:571`. **Sharpened by §B-N2**: the LCT canon §5.4 and mrh L174 *agree* on "Depth 3: Default"; the Rust `Mrh` models depth as per-LCT `u32` data (0=unset). "Default 3" (both specs), "MAX_HOPS 4 cap" (Python), and "per-LCT data" (Rust) are **three different quantities**, not three conflicting values — see N2. Still operator-gated.
- **X4 / N1(a)** (structural shrink of §5, L240-369) — STILL-OPEN. Its inbound-anchor census (O2 + C162 A1/A2) unchanged. §B-N1 corrects a *sibling's* framing of the X4-coupled numeric facet.
- **N4** (`web4:t3Score` vs `web4:trustScore`, folds into D1) — unchanged.

---

## §B — New Findings (0 autonomous; 2 routed cross-track)

### N1 (INFO, class-b, ROUTED to the t3-v3 / multi-device lineage) — the sibling **D2** carry's numeric-contradiction facet is **STALE**: it perpetuates a pre-C91 ground truth

Reading sibling audit docs for carries routed back here ([[feedback_cross_doc_carry_inbound]]) surfaced the standing **D2** carry, most recently restated in **C192** (`docs/audits/C192-t3-v3-tensors-4th-delta-2026-07-13.md:103,125`):

> *"D2 — X4 (mrh §5 duplication) … the **Surgeon `training` 0.92 (t3-v3) vs 0.90 (mrh)** cross-doc contradiction stands (**mrh-side fix**)."*

This numeric facet is **refuted at live HEAD.** Ground truth in `mrh-tensors.md`:

- **L264**: `web4:training 0.92 ;` (Surgeon aggregate shorthand)
- **L325**: `web4:t3Score 0.92 .`
- `grep -n "0\.90" mrh-tensors.md` → **no match.** There is **no `0.90`** anywhere in the file.

The provenance: **C42** (t3-v3 audit, 2026-06-09) filed F18 recording "training 0.92 (t3-v3 §5.2) vs 0.90 (mrh §5.2)" and correctly said *"the mrh-side 0.90 is the outlier to reconcile … Fix lands in `mrh-tensors.md`."* **C91** (mrh remediation, 2026-06-24, `f0c82118`) then applied exactly that reconciliation — its N1(b) changed mrh `web4:training 0.90 → 0.92`. **C129** and **C162** both verified: *"contradiction closed on BOTH sides."* But the **t3-v3 lineage** (C82, C192) kept carrying the "0.92-vs-0.90" divergence forward from C42 **without re-deriving the mrh value after C91 closed it** — a textbook [[feedback_prior_finding_path_provenance]] slip (a carried finding's stated ground truth is wrong at live HEAD).

**Disposition**: the D2 **numeric-contradiction facet is dead** — mrh is already `0.92`, matching t3-v3. **Do NOT edit mrh to "fix" a non-existent `0.90`.** Only D2's **structural-duplication (X4) facet** survives: mrh §5 (L240-369) still duplicates t3-v3 §5's role-contextual principle + Surgeon Turtle, and that structural shrink remains the standing operator DESIGN-Q. **Routed to the t3-v3 / multi-device audit lineage** so the next t3-v3 or multi-device delta consumes the correction and stops carrying the stale numeric half. Not an mrh defect; no mrh mutation.

### N2 (INFO, class-b, SDK-mirror gate — ROUTED, promoted from C192 prose) — `web4-core::Mrh` is a GENUINE §2.1-family mirror with a trust-propagation LAYER-SPLIT

Prior mrh passes (C40–C163) examined only the **Python** SDK (`mrh.py`/`trust.py`). Extending the SDK-mirror gate to `web4-core/src/*.rs` at live HEAD (the method's standing instruction — re-derive target-primitive implementers in *both* the Python SDK and `web4-core`):

`web4-core/src/lct.rs:167-181` defines `struct Mrh` (introduced **`7db29a5c`, PR #499**, *after* C163's `b8740803` — genuinely new corpus content since the last mrh audit):

```rust
pub struct Mrh {
    pub bound:      Vec<MrhEdge>,   // permanent structural (parent/child/sibling)
    pub paired:     Vec<MrhEdge>,   // operational (roles, occupants, sessions)
    pub witnessing: Vec<MrhEdge>,   // who attests existence/actions
    pub horizon_depth: u32,         // canon §5.4; 0 = unset
}
pub struct MrhEdge { pub lct_id: String, pub edge_type: String, pub ts: DateTime<Utc> }
```

**This was already surfaced in C192 prose** (`C192-…:` "the new `Mrh` struct … carries exactly `{bound, paired, witnessing}` (+ `horizon_depth`) — byte-matching SAL §14.1's schema stub") as a *positive convergence*, but was **never adjudicated for mrh**. Per [[feedback_prose_is_not_ledger]], it is **promoted into this ledger** rather than re-discovered.

**Adjudication (mrh lens):**

- **GENUINE mirror at the family level.** The three buckets `bound/paired/witnessing` map 1:1 onto mrh §2.1's three `rdfs:subPropertyOf` families (binding / pairing / witness). Concordant; also byte-matches SAL §14.1's `{bound,paired,witnessing}` stub. No contradiction.
- **LAYER-SPLIT.** `web4-core` reifies the MRH-**edge** layer (the relationships carried *on* an LCT, for registry/hub traversal) but carries **no trust-propagation mirror** — there is no Rust twin of §4.2's `propagate_multiplicative/probabilistic/maximal`. That algorithm layer lives only in Python `mrh.py`. This is the same genuine-mirror-with-layer-split shape as C188 (mcp types vs wire) and C190 (atp account-primitive). Expected, not a defect.
- **(a) `horizon_depth` — a THIRD representation, feeds D4.** Rust models depth as per-LCT `u32` (0=unset), *deferring to data*; it hardcodes neither `3` nor `4`. The LCT canon §5.4 (`LCT-linked-context-token.md:380`) and mrh L174 **agree** "Depth 3: Default"; Python's `MRH_MAX_HOPS = 4` is a **hard cap** ("5+ = BEYOND = zero"), a different quantity. So D4 is not three conflicting *values* but three distinct *roles* — default (3), cap (4), per-entity datum (Rust). This **clarifies** D4's resolution space; routed into D4, not self-decided.
- **(b) `MrhEdge.edge_type: String` (free) vs Python `RelationType` (closed 12-enum) vs spec §2.1 (12 `rdfs:subPropertyOf`).** A representation split — Rust uses open strings ("parent"/"occupant"/"existence"), Python/spec use a closed 12-member vocabulary. Not a contradiction (the three families align); a D1-sibling ontology-vocabulary datapoint. Routed.

**Disposition**: **routed** to the D4 / D1 operator DESIGN-Q bundle and to the web4-core / LCT-spec owners as concord context. Not an mrh defect; mrh-tensors.md is byte-frozen and asserts nothing web4-core contradicts. No mrh mutation.

---

## §C — The flagship candidate, and why it was REFUTED

The most promising candidate was that the new `web4-core::Mrh` doc-comment cites **`canon §5` / `canon §5.4`** for `bound/paired/witnessing` and `horizon_depth` — but in `mrh-tensors.md`, §5 is "Role-Contextual T3/V3 Tensors" and §5.4 is "Role Pairing in MRH," which contain **neither** the edge families nor `horizon_depth`. If "canon" pointed at `mrh-tensors.md`, the Rust citation would be **broken**, and a broken cross-reference in freshly-merged canonical code (#499) is a legitimately reportable (routed) defect.

**Refuted.** "canon" resolves to the **LCT** canonical spec, not mrh-tensors: `LCT-linked-context-token.md:343` `## 5. Markov Relevancy Horizon (MRH)`, with `### 5.4 Horizon Depth` at L380 ("Depth 3: Default …") and §5.2 "Relationship Types" enumerating bound/paired/witnessing. The Rust citation **lands exactly** on the section that governs the MRH-on-LCT reification. This also confirms the corpus's **two-treatment** structure is deliberate: `mrh-tensors.md` = MRH as an RDF trust-graph with 12 typed edges + propagation algorithms; LCT §5 = MRH as the edges carried on an LCT (what web4-core mirrors). Not a redefinition, not a broken citation — a division of labor. **REFUTED; no finding.**

*(Method note: this is the C162 §C pattern recurring — a strong cross-doc/cross-repo candidate with a real policy hook, killed by opening the actual cited target. Point the refuter at your best finding, not the leftovers — [[feedback_refute_your_best_finding]].)*

---

## §B — Refuted / acknowledged / carry-not-new (default-to-refute upheld)

| Candidate | Disposition |
|-----------|-------------|
| Rust `Mrh` `canon §5/§5.4` citation is broken (points at mrh §5 = T3/V3) | **REFUTED** — "canon" = LCT spec; `LCT…md:343` §5 MRH, §5.4 Horizon Depth. Lands exactly. See §C. |
| D2 "Surgeon training 0.92 vs 0.90 (mrh-side fix)" is a live mrh defect | **REFUTED / STALE** — mrh L264 = 0.92 (C91-closed 2026-06-24); no 0.90 in the file. Numeric facet dead; only X4 duplication survives. Routed as **N1**. |
| Rust `Mrh` contradicts mrh's edge model | **REFUTED** — bound/paired/witnessing map 1:1 to §2.1 families; SAL §14.1 concord. Genuine mirror. |
| Rust drops the trust-propagation layer → mirror incomplete → defect | **LAYER-SPLIT, expected** — §4.2 algorithms are Python-only; web4-core reifies the edge layer only (C188/C190 shape). Not a defect. |
| `horizon_depth: u32` (Rust) contradicts "default 3" / `MRH_MAX_HOPS 4` | **REFUTED** — per-LCT datum vs default vs cap = three distinct quantities; feeds D4, not a contradiction. |
| §4.2 note under-enumerates API differences (the C162 finding class) | **REFUTED** — C163 fixed it to "Three"; re-derived from `mrh.py`, correct and complete. |
| §4.2 propagation math diverges from SDK | **REFUTED** — behaviourally re-verified (pp([])=0.0, pp([0.5,0.5])=0.75, px([])=0.0). |
| corpus delta since C163 contradicts mrh | **REFUTED** — `git log b8740803..HEAD -p` grep for `hasRelationship\|pairedWith\|boundTo\|witnessedBy\|propagate_\|horizon_depth\|0.92` returns only (i) audit-doc quotations, (ii) whitepaper *equation-gloss* prose ("MRH … contextualized by horizon" — descriptive, concordant), (iii) the web4-core `Mrh` struct (N2). No delta hunk asserts anything against an mrh claim. |
| C91/C130 fixes regressed | **REFUTED** — 3/3 + 1/1 held; behaviourally re-verified. |
| `horizon_depth=3` vs `MRH_MAX_HOPS=4` | **KNOWN CARRY D4** — confirmed present (`trust.py:91`), sharpened by N2, not re-reported as new. |
| C10-L2 unnumbered preamble | **STILL-OPEN INFO by design** — C41 declined. |

---

## Disposition for C201 (paired remediation slot)

- **Apply autonomous: NONE.** Zero net-new autonomous mrh defects; `mrh-tensors.md` is byte-frozen and correct. **C201 is a genuine no-op** (to be declared in the next audit doc per the C155/C161/C199 precedent), unless a cross-track owner routes something back.
- **Route cross-track (do NOT self-apply):**
  - **N1** → the **t3-v3 / multi-device audit lineage** (owner of standing carry **D2**): the D2 *numeric* facet ("Surgeon training 0.92 vs 0.90") is **STALE** — mrh is already 0.92 (C91-closed). Drop the numeric half; carry only the X4 structural-duplication facet. Correction to a *sibling audit record*, not to the standard.
  - **N2** → the **D4 / D1 operator DESIGN-Q bundle** and the **web4-core / LCT-spec owners**: `web4-core::Mrh` (#499) is a genuine §2.1-family mirror with a trust-propagation layer-split; `horizon_depth` as per-LCT data is a third D4 representation (default 3 / cap 4 / per-entity datum are distinct roles); `MrhEdge.edge_type` free-string vs the 12-member closed vocabulary is a D1-sibling.
- **Defer — operator DESIGN-Q (unchanged bundle)**: **X4/N1(a)** structural §5-shrink (cost context O2 + C162 A1/A2); **D1** ontology-vocabulary (N4 + C162-N2 + N2(b) fold in); **D4** horizon-depth model (now clarified by N2(a): three roles, not three conflicting values).
- **No date bump**: `mrh-tensors.md` carries no date/version banner; audit-only turn.

---

## §D — Method Notes

1. **A carried cross-doc contradiction must be re-derived at live HEAD on BOTH sides, every time it is restated.** The D2 numeric facet ("0.92 vs 0.90") was correct when C42 filed it (2026-06-09), reconciled by C91 (2026-06-24), verified closed by C129 and C162 — and *still* restated as open by C192 (2026-07-13), because the t3-v3 lineage re-copied C42's framing without re-reading the mrh value. A cross-doc carry is a claim about *two* files; when either moves, the carry's ground truth can silently invert. This is [[feedback_prior_finding_path_provenance]] applied to a *sibling's* ledger: reading the neighbours' audit docs for inbound carries ([[feedback_cross_doc_carry_inbound]]) is not enough — you must re-verify the carry's asserted values, not just note that the carry exists.

2. **The SDK-mirror gate is not a fixed set — and a frozen file's first exposure to a *second* implementation is where net-new lives.** Four prior mrh passes read only Python. `web4-core::Mrh` (#499) landed after C163 and mirrors mrh's edge layer canonically — yet the mrh lineage would never have seen it, because it lives in a repo the file-scoped audit doesn't open by default. The Rust mirror both **confirmed** the spec (family-level concord, SAL §14.1 byte-match) and **sharpened** a standing DESIGN-Q (D4's three roles). Re-derive implementers in *both* the Python SDK and `web4-core` before declaring §B clean.

3. **Promote from prose to ledger.** N2's artifact (`Mrh` struct) was already in C192's prose as a "positive convergence," parked and unadjudicated for mrh — exactly the [[feedback_prose_is_not_ledger]] surface. The fix is not to re-discover it but to promote it into *this* file's carry ledger with an mrh-lens adjudication. C176 did the same with the Rust `EntityType` gap that sat in C172's LCT prose.

4. **A frozen file's health is a claim about its neighbourhood, and the neighbourhood keeps moving.** mrh has now been byte-stable across five deltas. C200's entire yield came from outside the file: a sibling carry that went stale, and a new canonical Rust struct. Nothing in the 420 frozen lines needed a touch — which is the correct, honest outcome, and the reason the audit's value is in the routing, not in an edit.

---

*C200 verdict: `mrh-tensors.md` byte-stable and healthy; the C163 §4.2 remediation (its own newest prose) re-tested against `mrh.py` ground truth and verified CLEAN with zero regression — exactly 3 propagation functions, correct enumeration, no 4th fn, no restored MRHEdge param. **Zero autonomous net-new mrh defects.** Two routed cross-track INFO items: N1 — the sibling D2 carry's numeric facet ("0.92 vs 0.90") is STALE, closed by C91 three weeks ago, only its X4 structural facet survives (routed to t3-v3/multi-device); N2 — the new `web4-core::Mrh` (#499) is a genuine §2.1-family mirror with a trust-propagation layer-split, promoted from C192 prose and feeding D4 a third horizon_depth representation (routed to D4/D1 + web4-core owners). Flagship broken-canon-citation candidate raised, pressed, and REFUTED (canon = LCT §5, resolves exactly). C199 presence remediation declared a genuine no-op. Standing D1/D4/X4/N4 correctly still escalated; C201 is a no-op unless a cross-track owner routes something back.*
