# C238 Audit: `mrh-tensors.md` Sixth Delta Re-Audit

**Date**: 2026-07-21
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn, slot `web4-20260721-000036`
**Document**: `web4-standard/core-spec/mrh-tensors.md` (422 lines; **byte-frozen since C163 `b8740803`**, 2026-07-09 — `git diff b8740803 HEAD` empty across the file; prior freeze was C91 `f0c82118`, broken only by C163's single §4.2 edit)
**Lineage**: C10 → C40 → C41 (remed, #290) → C90 (2nd delta) → C91 (remed, #382 `f0c82118`) → C129 (3rd delta) → C130 (remed of C129-O1) → C162 (4th delta, #490) → C163 (remed, #491 `b8740803`) → C200 (5th delta, #532 `3a1b459c`) → **C238** (this 6th delta)
**Method**: §A prior-finding + carry verification re-run **at live HEAD** (not trusting prior line numbers) + the mandated remediation-regression check on the C163-applied §4.2 hunk (re-derive the three propagation signatures from `mrh.py` ground truth) + byte-freeze confirmation. §B refute-by-default across three lenses: corpus-delta over the 31 post-C200 commits / **inbound cross-doc carry** / the **SDK-mirror gate over both `mrh.py`/`trust.py` and `web4-core::Mrh`**. Each surviving candidate handed to an adversarial refuter; own flagship attacked first.
**Reference materials**: SDK `web4-standard/implementation/sdk/web4/{mrh.py,trust.py}`; `web4-core/src/lct.rs` (`Mrh`/`MrhEdge`); `web4-standard/ontology/role-extension.ttl`; `t3-v3-tensors.md`; `LCT-linked-context-token.md` §5; sibling audit docs C200, **C230 (t3-v3 5th delta, 2026-07-16)**, C232/C234/C236; Python 3.

---

## Summary

| | Result |
|---|---|
| **§A** C163 §4.2 hunk (the mandated guard) | **HELD** — re-derived from `mrh.py`; exactly 3 `propagate_*` fns, all `List[float]`, no 4th, no restored `MRHEdge` param; enumeration correct & complete; **0 regression** |
| **§A** byte-freeze | **CONFIRMED** — `mrh-tensors.md` + `mrh.py` unchanged since C163 (`git diff b8740803 HEAD` empty for both); working tree clean |
| **§A** C91/C130 numeric + anchor carries | **HELD** — L264/L325 = `0.92`; C130 FRACTAL anchor lands; 0 regressed |
| **§A** standing DESIGN-Qs (D1/D4/X4/N4) | STILL-OPEN, correctly escalated; D4 anchor `MRH_MAX_HOPS = 4` present at `trust.py:91` |
| **§B** new autonomous mrh (class-a) defects | **0** |
| **§B** corpus delta (31 post-C200 commits) | **CLEAN** — 0 touch mrh spec/py; pickaxe of horizon/propagation/edge tokens = 0 non-audit hits; no new mrh mirror/consumer file |
| **§B** SDK/`web4-core` mirror gate | **STABLE** — `web4-core::Mrh` shape unchanged; one datapoint refresh (N2, INFO, routed): free-string `edge_type` gained `"birth_certificate"` (#538) |
| **§B** inbound cross-doc carry (N1) | **STALE & UN-CONSUMED** — the D2 numeric facet is dead (mrh already `0.92`), yet t3-v3 **C230** restates it as open; re-routed with provenance |
| **§B** flagship (C162 MRH-redefinition guard vs `4f76f110`) | **REFUTED** — oracle-scope commit added no MRH token; C162 refutation holds |

**Verdict: `mrh-tensors.md` remains byte-stable and healthy — 6th consecutive clean delta.** The C163 remediation (its own newest net-new prose) is verified **clean with zero regression**, re-tested against `mrh.py` ground truth. **Zero autonomous net-new mrh defects.** As at C200, the entire yield is in the *neighbourhood*, not the 422 frozen lines: (i) a sibling carry that is still stale **and still un-consumed** one delta later, and (ii) a datapoint refresh on the untracked Rust mirror. Both are routed; no mrh edit.

The session's most valuable output is **N1 (persistence)**: the t3-v3 lineage's **C230** delta (2026-07-16 — the *same day* C200 first flagged this) **still carries the "Surgeon `training` 0.92 vs 0.90 (mrh-side fix)" numeric contradiction as open**, though the mrh-side value has been `0.92` since C91 closed it on 2026-06-24. C200 routed the correction; C230 did not consume it. See §B-N1 and §D.

---

## §A — Carry, Fix, and Prior-Finding Verification

### The mandated guard — C163's §4.2 hunk re-tested against `mrh.py` (HELD, 0 regression)

C163's forward guard requires every pass that reaches mrh to **re-test** (not re-read) the §4.2 SDK-divergence note against `mrh.py` — if `mrh.py` gained a 4th propagation function or restored an edge-typed parameter, the "Three API differences" note becomes the defect. Ground truth re-derived at live HEAD:

- `grep -c "^def propagate" mrh.py` → **3**. Exactly three module functions: `propagate_multiplicative(path_weights, decay_factor=0.7)`, `propagate_probabilistic(path_trusts)`, `propagate_maximal(path_trusts)`. **No 4th.**
- All three consume `List[float]`; **no `MRHEdge`-typed parameter restored** (`MRHEdge` remains a *graph*-layer type, not a propagation-fn parameter).
- The §4.2 note's three-part enumeration (all consume `List[float]` not `MRHEdge`; prob/max take per-**path** scalars; those two drop `decay_factor`) matches ground truth. **Correct and complete. HELD, 0 regression.** (Per the standing memory guard, this is a re-verify, **not** a re-flag of the C162/C163 §4.2 item.)

### Byte-freeze

- `git diff b8740803 HEAD -- web4-standard/core-spec/mrh-tensors.md` → **empty**. Frozen since the C163 remediation.
- `git diff b8740803 HEAD -- web4-standard/implementation/sdk/web4/mrh.py` → **empty** (last content change 2026-04, `759eaefa` ruff format). Working tree clean for both.
- 31 commits landed on main since C200 (`3a1b459c`); **zero** touched either file.

### C91 / C130 numeric + anchor carries — re-verified against frozen bytes

- **C91-N1(b)** Surgeon aggregate: mrh **L264** `web4:training 0.92`, **L325** `web4:t3Score 0.92`. `grep -n "0\.90" mrh-tensors.md` → **no match**. **HELD** — and this is the crux of §B-N1.
- **C130** FRACTAL re-anchor (`Default horizon_depth = 3`) lands at **L174**. **HELD.**
- Composite arithmetic `0.95×0.4 + 0.92×0.3 + 0.88×0.3 = 0.920` = L325 `t3Score 0.92`. Internally consistent.

### Standing DESIGN-Qs — status (unchanged, correctly escalated)

- **D1** (ontology-vocabulary divergence) — STILL-OPEN. §B-N2 adds a datapoint (`"birth_certificate"` edge string).
- **D4** (`horizon_depth = 3` default vs `MRH_MAX_HOPS = 4` cap vs per-LCT `u32` datum — three distinct *roles*, not conflicting values, per C200-N2(a)) — anchors re-baselined: `MRH_MAX_HOPS = 4  # 5+ hops = BEYOND = zero trust` present at `trust.py:91`; zone checks `:558`/`:571`. Operator-gated.
- **X4 / N1(a)** (structural §5-shrink, L240-369 duplicating t3-v3 §5) — STILL-OPEN. Its *numeric* facet is the dead half corrected by §B-N1.
- **N4** (`t3Score` vs `trustScore`, folds into D1) — unchanged; both tokens present (grep = 4 occurrences of the pair).

---

## §B — New Findings (0 autonomous; 2 routed cross-track)

### N1 (INFO, class-b, RE-ROUTED to the t3-v3 / multi-device lineage) — the D2 numeric facet is STALE **and was NOT consumed** by t3-v3 C230

C200-N1 (2026-07-16) established that the D2 carry's numeric facet — *"Surgeon `training` 0.92 (t3-v3) vs 0.90 (mrh), mrh-side fix"* — is **dead**: C91 (`f0c82118`, 2026-06-24) already reconciled mrh `0.90 → 0.92`; there is no `0.90` in the file. C200 routed the correction to the t3-v3 / multi-device lineage (the owner of standing carry **D2**), asking the next t3-v3 or multi-device delta to drop the numeric half and carry only the X4 structural-duplication facet.

**Re-verified at live HEAD (C238):** `grep -n "0\.90" mrh-tensors.md` → still **no match**; L264/L325 both `0.92`. The refutation **holds**.

**But the correction was not consumed.** The next t3-v3 delta after C200 was **C230** (`docs/audits/C230-t3-v3-tensors-5th-delta-2026-07-16.md`, #554 — merged the *same day* as C200's #532). C230 **still restates the numeric contradiction as open**:

> C230 L87: *"the **Surgeon `training` 0.92 (t3-v3) vs 0.90 (mrh)** cross-doc contradiction stands (**mrh-side fix**)."*
> C230 L105: *"**D2** (mrh §5 dup + Surgeon 0.92-vs-0.90 + multi-device attach). Route to the single operator memo."*

C230 and C200 ran on the same day; C230 evidently did not have C200's routing in view. The stale ground truth (a pre-C91 value) has now been carried forward across **C42 → C82 → C192 → C230**, and C200's correction has sat un-consumed for one full t3-v3 delta.

**Disposition**: the D2 **numeric-contradiction facet remains dead** — mrh is `0.92`, matching t3-v3. **Do NOT edit mrh to "fix" a non-existent `0.90`.** Only D2's **structural-duplication (X4) facet** survives (mrh §5 L240-369 still duplicates t3-v3 §5's role-contextual principle + Surgeon Turtle — the standing operator DESIGN-Q). **Re-routed to the t3-v3 / multi-device audit lineage with explicit provenance** (C91 closed the numeric half 2026-06-24; C200 first flagged the stale carry; C230 did not consume it). The **next t3-v3 delta (~C268)** MUST drop the numeric half from the D2 carry. Not an mrh defect; no mrh mutation.

### N2 (INFO, class-b, SDK-mirror gate — ROUTED to D1/D4 + web4-core owners) — `web4-core::Mrh` stable; free-string `edge_type` vocabulary grew `"birth_certificate"`

`web4-core/src/lct.rs` `struct Mrh` (introduced #499, adjudicated a genuine §2.1-family mirror with a trust-propagation layer-split at C200-N2) is **unchanged in shape** at HEAD: `bound / paired / witnessing: Vec<MrhEdge>` + `horizon_depth: u32` (doc-comment `canon §5` / `§5.4; 0 = unset`). Three post-C200 commits touched `lct.rs` (#538 citizenship, #540 operational-key vouching, #544 authority_ratchet) but added structs *around* `Mrh`, not to it. Pickaxe of `horizon_depth`/`MrhEdge`/`RelationType`/`boundTo`/`pairedWith`/`witnessedBy` = **0 non-audit commits** changed the model.

**One datapoint refresh (D1):** `MrhEdge.edge_type` is a free `String`. Its doc-comment example set — `"parent"`/`"occupant"`/`"existence"` at C200 — now also lists `"birth_certificate"` (lct.rs L208), and #538 uses that value as a live filter key (`e.edge_type == "birth_certificate"`, L467) and test fixture (L988). This is the citizenship reshaping (#538) surfacing on the MRH edge layer. It **strengthens** C200-N2(b): the Rust open-string edge vocabulary (`"parent"`, `"birth_certificate"`, `"occupant"`, `"existence"`, …) continues to diverge from the spec §2.1 **closed 12-member** `rdfs:subPropertyOf` vocabulary and Python's closed `RelationType` enum. A D1-sibling representation split, not a contradiction — `"birth_certificate"` is an LCT-layer citizenship edge, and `mrh-tensors.md` (byte-frozen) asserts nothing it violates.

**Disposition**: **routed** to the D1/D4 operator DESIGN-Q bundle and the web4-core / LCT-spec owners as concord/vocabulary context. Not an mrh defect; no mrh mutation.

---

## §C — The flagship candidate, and why it was REFUTED

The most promising candidate was a **regression of the C162 flagship**. C162 raised (then refuted) the charge that `role-extension.ttl` *redefines MRH*. Since C200, that file was touched by **`4f76f110`** ("oracle consult/write sets on Scope — Piece B for oracle-scope gating"), and `role-extension.ttl` §Scope carries `rdfs:label "Scope / MRH"` and `rdfs:comment "The Markov Relevancy Horizon of the grant …"`. If `4f76f110` had bound a *new* MRH semantic onto the oracle-scope machinery, the C162 refutation could have inverted.

**Refuted.** `git show 4f76f110 -- '*role-extension.ttl'` adds **no** MRH/Markov/relevancy/horizon token — the added content is `oracle_consult` / `write_set` scope affordances (the same oracle-scope construct guarded in the C234 acp and C236 presence deltas). The pre-existing "Scope / MRH" references (L49-50, L136) are untouched and remain the C162-adjudicated usage: MRH as the *scope-dimension bundle* (repos/machines/channels/data/ATP-budget the role ranges over), consistent with the canonical glossary's scope-dimension definition — **not** a redefinition of the mrh-tensors trust-graph. C162's refutation **holds**. No finding.

*(Method note: the C162/C200 §C pattern recurring — point the refuter at the strongest candidate, open the actually-cited target, and the charge dies. [[feedback_refute_your_best_finding]].)*

---

## §B — Refuted / carry-not-new (default-to-refute upheld)

| Candidate | Disposition |
|-----------|-------------|
| `4f76f110` re-introduces an MRH redefinition into `role-extension.ttl` | **REFUTED** — commit adds only oracle scope affordances; 0 MRH tokens; "Scope/MRH" refs untouched. C162 holds. See §C. |
| D2 "Surgeon training 0.92 vs 0.90 (mrh-side fix)" is a live mrh defect | **REFUTED / STALE** — mrh L264 = 0.92 (C91-closed 2026-06-24); no 0.90. Numeric facet dead; only X4 survives. Re-routed **N1** (still un-consumed by C230). |
| `web4-core::Mrh` changed since C200 → new mirror delta | **REFUTED** — struct shape unchanged; 0 non-audit commits touch the model. Only a free-string `edge_type` example grew (N2). |
| `"birth_certificate"` edge string contradicts the 12-member §2.1 vocabulary | **REFUTED** — open-string-vs-closed-enum is the standing D1 split; LCT-layer citizenship edge; frozen spec asserts nothing it violates. Routed N2. |
| §4.2 note under-enumerates API differences (the C162 finding class) | **REFUTED** — C163 fixed to "Three"; re-derived from `mrh.py`, correct & complete. |
| corpus delta since C200 contradicts an mrh claim | **REFUTED** — 31 commits, 0 touch mrh spec/py; pickaxe of propagation/horizon/edge tokens = 0 non-audit hits. |
| C91/C130 fixes regressed | **REFUTED** — L264/L325 = 0.92, C130 anchor lands; 0 regressed. |
| `horizon_depth = 3` vs `MRH_MAX_HOPS = 4` | **KNOWN CARRY D4** — `MRH_MAX_HOPS = 4` present at `trust.py:91`; three distinct roles per C200-N2(a). Not re-reported. |
| C10-L2 unnumbered preamble | **STILL-OPEN INFO by design** — C41 declined the demotion. |

---

## Disposition for C239 (paired remediation slot)

- **Apply autonomous: NONE.** Zero net-new autonomous mrh defects; `mrh-tensors.md` is byte-frozen and correct. **C239 is a genuine no-op** (to be declared in the next audit doc per the C155/C161/C199/C201 precedent), unless a cross-track owner routes something back.
- **Route cross-track (do NOT self-apply):**
  - **N1** → the **t3-v3 / multi-device audit lineage** (owner of carry **D2**): the numeric facet is **STALE and still un-consumed** — C230 restates "0.92 vs 0.90" as open though mrh has been 0.92 since C91. The next t3-v3 delta (~C268) MUST drop the numeric half and carry only the X4 structural facet. Correction to a *sibling audit record*, not to the standard.
  - **N2** → the **D1/D4 operator DESIGN-Q bundle** + web4-core / LCT-spec owners: `web4-core::Mrh` is stable; its free-string `edge_type` grew `"birth_certificate"` (#538), refreshing the open-string-vs-closed-12-enum D1 datapoint.
- **Defer — operator DESIGN-Q (unchanged bundle)**: **X4/N1(a)** structural §5-shrink; **D1** ontology-vocabulary (N4 + N2 fold in); **D4** horizon-depth model (three roles per C200-N2(a)).
- **No date bump**: `mrh-tensors.md` carries no date/version banner; audit-only turn.

---

## §D — Method Notes

1. **A routed cross-doc correction is not closed until the receiving lineage consumes it — verify consumption, don't assume it.** C200 correctly identified the D2 numeric facet as stale and routed the fix to t3-v3. But the next t3-v3 delta (C230, same day) re-carried it anyway. A routing is a *request*, not a *guarantee*; the sending lineage should re-check, on its next delta, whether the receiver acted. C238's job here was not to re-derive the refutation (that was C200's) but to observe that the neighbour **still hasn't consumed it** and re-route with sharpened provenance. This is [[feedback_prior_finding_path_provenance]] applied to the *lifecycle* of a routed carry, and [[feedback_cross_doc_carry_inbound]] read in the outbound direction.

2. **The SDK-mirror gate is where a byte-frozen file's net-new lives — and it keeps producing INFO even when the mirror's *shape* is frozen.** `web4-core::Mrh` didn't change structurally, yet #538's citizenship reshaping leaked a new free-string `edge_type` value (`"birth_certificate"`) onto the MRH edge layer — a live refresh of the D1 open-string-vs-closed-enum datapoint. Re-derive implementers/consumers in *both* the Python SDK and `web4-core` every delta, and diff their *values*, not just their type signatures.

3. **A frozen file's health is a claim about a moving neighbourhood.** mrh is now byte-stable across six deltas. C238's entire yield — as at C196/C198/C200 — came from outside the 422 frozen lines: a sibling carry still stale one delta later, and a citizenship edge-string on the Rust mirror. Nothing in the spec needed a touch, which is the correct and honest outcome; the value is in the routing.

---

*C238 verdict: `mrh-tensors.md` byte-stable and healthy — 6th consecutive clean delta. The C163 §4.2 remediation re-tested against `mrh.py` ground truth and verified CLEAN with zero regression (exactly 3 propagation functions, correct enumeration, no 4th fn, no restored MRHEdge param). **Zero autonomous net-new mrh defects.** Two routed cross-track INFO items: N1 — the sibling D2 numeric facet ("0.92 vs 0.90") is STALE (mrh has been 0.92 since C91, 2026-06-24) **and was NOT consumed by t3-v3 C230**, re-routed with provenance so the next t3-v3 delta (~C268) drops it; N2 — `web4-core::Mrh` (#499) is shape-stable, but its free-string `edge_type` gained `"birth_certificate"` via #538 citizenship, refreshing the D1 open-string-vs-closed-12-enum datapoint. Flagship C162-MRH-redefinition-regression candidate (vs `4f76f110` oracle-scope) raised, pressed, and REFUTED. Standing D1/D4/X4/N4 correctly still escalated; C239 is a no-op unless a cross-track owner routes something back.*
