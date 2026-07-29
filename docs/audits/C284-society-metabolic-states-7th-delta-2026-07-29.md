# C284 — SOCIETY_METABOLIC_STATES.md 7th-Delta Re-Audit (C21→C54/C55→C96→C133→C168→C206→C244→C284)

**Audit ID**: C284
**Date**: 2026-07-29
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (444 lines, v1.0.0, "Proposed Standard")
**Lineage**: C21 first-pass (2026-05-29) → C54 first-delta → C55 remediation (PR #326, `a504ea41`) → C96 → C133 → C168 (C168-N1 ledger promotion, #500) → C206 (PR #535) → C244 (PR #562-era, 6th delta) → **C284 (this, 7th delta)**
**Rotation provenance**: C282 (dictionary 7th delta) SERVED as PR #589 and advanced the fixed-order round-robin +2 to the next file = SOCIETY_METABOLIC (last audited C244, 2026-07-21). Step-0 queue check run first: `private-context/SESSION_FOCUS.md` §"In motion" 0a–0d holds **no actionable Legion item** (0a hestia-owned; 0b SERVED; 0c WIRED and awaiting a vault-authorized human actor — hestia's PolicyGate correctly denied the `autonomous-timer` role the passphrase and that denial is **not** to be circumvented; 0d's Phase-2 code half is the HUB track's PR and no such PR is open). Rotation therefore proceeds unpre-empted.
**Auditor session**: legion-web4-20260729-120003 (slot 120003)
**Mutation**: **ZERO.** No spec, SDK, crate, ontology, test-vector or sister-doc byte was changed. Findings route; they are not self-applied.
**Out of scope**: the C168-N1 `society.rs` rename (operator/publish-track gated — and see N1, whose whole point is that the rename got *more* expensive); self-answering any DESIGN-Q; the pre-C-series decision-section sweep (C168 §D, operator-gated); mining `simulations/` for spec divergences (policy-review-flagged drift risk, declined by construction — see §3.1).

---

## 1. Methodology, and the shape this audit was forced into

Policy review returned **REVISE** and was right on all four counts. The proposed scope named `hub/`, `web4-policy/` and `docs/specs/` as the Gate-1 candidate set; two of those three are provably empty of metabolic content and the directory that actually holds a third independent implementation was **not in the list**. Had the scope been executed as proposed, Gate 1 would have returned a **false NEGATIVE**. The four amendments — corpus-wide sweep instead of a hand-picked list, §C collapsed like §A, Gate 3 demoted to a pre-check, and Gate 2's expectation recalibrated so the strongest candidate was not pre-loaded as a defect — are executed below verbatim.

**§A is deliberately collapsed to a freeze proof.** Six prior deltas returned 0 net-new against the target. Re-narrating prior-finding verification on a byte-frozen file is the padding the C282 reviewer ruled against; that ruling is honored here up-front rather than after the fact.

**Freeze — proven by blob identity at live HEAD `8bc3ef39` vs the C244 cutoff `2293f83b`:**

| Artifact | HEAD blob | C244 blob | State |
|---|---|---|---|
| `SOCIETY_METABOLIC_STATES.md` | `5e3f7203` | `5e3f7203` | **FROZEN** — byte-identical since C55 `a504ea41` (~2 months), **7th consecutive frozen window** |
| SDK `web4/metabolic.py` | `d3d31446` | `d3d31446` | FROZEN |
| `test-vectors/metabolic/society-metabolic-states.json` | `855eedb5` | `855eedb5` | FROZEN |
| `SOCIETY_SPECIFICATION.md` (B14 anchor) | `2ad453ba` | `2ad453ba` | FROZEN |
| `web4-society-authority-law.md` (B15 / C58-B10 anchor) | `0849ebbe` | `0849ebbe` | FROZEN |
| `web4-core/src/society.rs` (C168-N1 mirror) | `17112f05` | `17112f05` | FROZEN |
| `atp-adp-cycle.md` (C96-E1 anchor) | `2d060579` | `2d060579` | FROZEN |
| `web4-core-ontology.ttl` (M7 sweep) | `fc4b4c36` | `fc4b4c36` | FROZEN |

**Window**: 46 commits, `2293f83b..HEAD`.

**Window lexicon diff — the whole-corpus regression sweep.** `git diff 2293f83b..HEAD` restricted to non-audit-doc paths and filtered on `metabolic|hibernat|torpor|estivat|molting|MetabolicState` yields **exactly one matching line in the entire window**, and it is prose in `whitepaper/log/CHANGELOG.md` quoting the C244 audit's own title. **Zero** spec, SDK, crate, ontology or test lines. The window is regression-free by construction.

**Verifier baseline** ([[feedback_enumeration_and_grep_hypotheses]] — a grep is a silent-failing hypothesis, and so is a *classifier*): the lexicon pattern was baselined **positive** on the two known-positive frozen artifacts (target, `metabolic.py`) and **red** on the six window authority-claimers' diffs (all 0, §3.2) before being used as evidence. One near-finding this pass was killed by baselining the instrument rather than the target — see **R2**.

Severity: HIGH / MEDIUM / LOW / INFO. Disposition: AUTONOMOUS-ACTIONABLE / DESIGN-Q / CROSS-TRACK.

---

## 2. §A — Freeze proof (collapsed)

- **C55 remediations (5, PR #326): 5/5 HELD by construction.** B2 §2.4 wake bullet · B10 §7.2 Wake-Trigger Flooding · B12 §7.1 sentinel row · B13 §10 conformance precision · B16 §3.1 cross-ref symmetry. Blob unmoved since `a504ea41`; C206 re-read all five at line level and found 0 REGRESSED; the blob has not moved since, so that read stands verbatim.
- **Regression sweep**: 0 lines, whole window (§1).
- §10 conformance (C56 claim-vs-canonical) unchanged by freeze.

---

## 3. §B — the three pre-registered gates

### 3.1 Gate 1 — genuine-mirror set re-derived from SUBJECT MATTER ([[feedback_mirror_set_underderived]], born C280)

**Mirror criterion, pre-registered before any grep ran.** An artifact is a *genuine mirror* of this spec iff all three hold:

- **M1 — it implements or enforces society-level metabolic state**: it holds a state set, a transition rule, an ATP-cost-by-state rule, or a trust-adjustment-by-state rule keyed to the spec's subject matter. Mentioning the word is not enough.
- **M2 — it is normative or product-bearing in the corpus's own taxonomy**: standard text, SDK/crate code shipped as a library, or a running daemon. `CLAUDE.md` classifies `simulations/` as *Python research*, and the primer classifies standalone research scripts as non-integrating; **research/reference code is a consumer of the ideas, not a mirror** — a divergence there is a research observation at most, never a spec defect.
- **M3 — a divergence in it would misinform a relying party acting on the spec**: it is reachable by someone implementing Web4.

The criterion is stated first precisely so the verdict on `simulations/` could not be reverse-engineered from what was found there. **The gate was not widened by analogy to C280's positive result on the society spec.**

**Corpus-wide sweep** (`grep -rlEi 'metabolic|hibernat|torpor|estivat|molting|MetabolicState'`, whole repo, audit docs excluded). Verdicts on everything not already in the tracked set:

| Candidate | M1 | M2 | M3 | Verdict |
|---|---|---|---|---|
| `web4-policy/` | — | — | — | **0 files.** Empty of the subject matter. |
| `docs/specs/` | — | — | — | **0 files.** |
| `hub/hub-daemon/src/admin.rs:282` | ✗ (renders, does not implement) | ✓ (running daemon) | ✓ | **CONSUMER**, not a mirror → feeds **N1** |
| `web4-trust-core/src/bindings/wasm.rs:670` | ✗ | ✓ (published WASM/JS API) | ✓ | **CONSUMER**, not a mirror → feeds **N1** |
| `simulations/` (12 files) | ✓ (`attack_track_fr.py:20`, `policy_entity.py:139`, `heartbeat_ledger.py`) | ✗ **research** | — | **NOT a mirror.** No spec defect can be raised from it. 126 attack sims × 8 states is an unbounded finding surface; declining it is the reason the criterion was written down first. |
| `ledgers/reference/python/heartbeat_ledger.py` | ✓ **fully** | ✗ reference code | ✓ | **NOT a mirror — but admissible as evidence.** See below. |
| `archive/**` (~50 files) | varies | ✗ archived | ✗ | Out by construction. |

**Gate 1 verdict: POSITIVE-but-qualified — and this lineage's blind spot is real.** No metabolic audit in seven passes (C21, C54/C55, C96, C133, C168, C206, C244) has ever read `ledgers/`. Only two audit documents in the entire corpus mention `ledgers/` at all, and neither is a metabolic pass.

`ledgers/reference/python/heartbeat_ledger.py` (979 lines, added `7fb0284f`, 2026-02-08) is a **complete, independent implementation of this spec**: all 8 states with the spec's own names (`:36-45`), `STATE_ENERGY_MULTIPLIER` annotated *"(from spec section 4.1)"* (`:48-59`), `STATE_TRUST_DECAY_RATE` annotated *"(from spec section 5.1)"* (`:73-83`), `VALID_TRANSITIONS` (`:91`), `AUTO_TRANSITIONS` (`:120`). It is byte-identical to `simulations/heartbeat_ledger.py`; `ledgers/reference/python/README.md:131` records the provenance and calls these files "**canonical copies**" — the word is used to mean *verbatim copy*, but it is doing unhelpful work in a repo whose entire thesis is canonicity, and the M2 verdict below is rendered *against* that label, not in ignorance of it.

**It fails M2, so it produces no spec-vs-mirror defect.** What it does produce is a **third independent reading of §5.1**, and that is admissible as evidence about the spec's own ambiguity — which is precisely what standing carry **C21-H3** alleges. Verified against the spec line by line:

| Surface | Result |
|---|---|
| 8 state names (§2.1–2.8) | **identical** |
| `STATE_ENERGY_MULTIPLIER` vs §4.1 `energy.state_multipliers` | **identical, all 8 values** |
| `VALID_TRANSITIONS` vs §3.1 transition matrix | **identical, all 17 edges** — including the two easy-to-miss ones (Torpor→Hibernation "grace period expired", Estivation→Hibernation "extended duration") |
| `AUTO_TRANSITIONS` thresholds vs §3.1/§4.1 | **identical** (1h→Rest, 6h→Sleep, 30d→Hibernation, ATP<10%→Torpor) |
| `STATE_TRUST_DECAY_RATE` vs §5.1 | **2 of 8 rows silently wrong** |

The two wrong rows are **exactly** the two rows the spec states on a non-decay axis:

| State | Spec §5.1 "Trust Tensor Effect" | SDK `metabolic.py` | `heartbeat_ledger.py` |
|---|---|---|---|
| Active | Normal updates | update 1.0 / decay 1.0 | decay 1.0 ✓ |
| **Rest** | **"90% update rate"** | update **0.9** / decay 1.0 | decay **0.9** ✗ — read the 90% as *decay* |
| Sleep | "10% decay rate" | update 0.0 / decay 0.1 | decay 0.1 ✓ |
| Hibernation / Torpor / Estivation / Dreaming | Frozen / Frozen / Internal only / Recalibration | 0.0 / 0.0 | 0.0 ✓ |
| **Molting** | **"-20% temporary"** | update 1.0 / decay 1.0, `temporary_penalty=-0.20` | decay **1.2** ✗ — read a *level penalty* as 20% *accelerated decay* |

C21-H3 ("§5.1's single column mixes incommensurable semantic categories") and C21-H1 ("§2.3/§5.1 silent on update_rate") have been open **61 days**, argued from prose. They now have a measured victim: a third implementer read the column, had only one axis to put it in, and mis-resolved precisely the rows H3 predicted — 6 of 8 rows agree because 6 of 8 rows are unambiguous. **This is evidence upgrading an existing carry, not a new defect.** It is not booked as net-new (stop rule), and it is not a spec-vs-implementer split (M2). It is recorded as **N3** so that whoever adjudicates H1/H3 has the demonstration.

### 3.2 Gate 2 — what landed in the window claiming authority over metabolic subject matter ([[feedback_canonized_principle_rescopes_frozen_file]])

All six candidates carry **zero** metabolic lexicon in their diffs, so each was adjudicated against the **behaviour** the spec prescribes, not its vocabulary ([[feedback_frozen_mirror_not_read_mirror]] — the vocabulary grep is not the test).

| Window artifact | Claim over this subject matter | Verdict |
|---|---|---|
| **#580** `954ee391` — *resilience to incomplete/malformed/contradicting information* (parent principle, dp-directed) | "Absence NEVER grants. Missing evidence → *less* trust, never assumed trust." Directly addresses §5.2's scoring and §5.1's dormancy freeze. | **Two adjudications: N2 (positive precedent) + R1 (refuted).** |
| **#579** `4665a430` — Dictionary as context-mandatory role | Names no metabolic surface; its "materiality" machinery is generic. | DISJOINT |
| **AAEP PRD** `752eadde` | Action-evidence portability; no state-lifecycle claim. | DISJOINT |
| `5df662a5` — "the RELYING party must compute trust" (README) | Touches §5.1's *consumer*, not its content — §5.1 states an effect on the tensor, it does not compute a verdict for a relying party. | DISJOINT; consistent with C244's ruling that metabolic §5 is **rate modulation**, which is not re-litigated here. |
| `780af6ef` — hub position review | Names admission-law theater, CI-dark Rust workspace, AAEP; no metabolic claim. | DISJOINT |
| `206dd004` — first-ever Rust CI | Arms `cargo test --locked` over `web4-core` (193+4 green). No metabolic assertion, but see the INFO under N1. | DISJOINT (informational) |

### 3.3 Gate 3 — ontology/schema edit vs EMITTED EXAMPLES ([[feedback_schema_edit_falsifies_sibling_examples]]) — **NEGATIVE, one line**

`01f410db` (`web4:Tensor` superclass + `web4:observationCount`, closes #581) **cannot reach** this target: the spec contains **0** `web4:` tokens across its **14** fenced blocks, and the frozen test vector contains 0 occurrences of `web4:`, `Tensor`, or `observationCount`. Machine-checked, recorded, no section built around it.

---

## 4. Net-New

**0 net-new defects against the target.** The spec is substantively clean for the 7th consecutive delta. Three items route; two candidates were refuted.

### N1 — MEDIUM — C168-N1's mis-citation has two *shipped* consumer faces nobody has recorded → operator + SDK/crate track, adjudicate **with** C168-N1

**Not net-new as a fact; net-new as REACH.** Standing carry **C168-N1** says `web4-core/src/society.rs:33-48` defines `pub enum MetabolicState { Genesis, Bootstrap, Operational, Dormant, Sunset }` under the doc-comment `Reference: SOCIETY_METABOLIC_STATES.md` — a 5-phase *lifecycle* model citing an 8-state *metabolic* spec that shares **zero** state names with it. Prior passes treated it as a crate-internal doc defect and left it operator-gated.

Re-deriving consumers at live HEAD (Gate 1) shows it is no longer crate-internal:

- **`web4-trust-core/src/bindings/wasm.rs:670`** — `WasmSociety::state()` getter, `inner: RustSociety = web4_core::society::Society`, doc-comment *"Current metabolic state as string"*, returning `"Genesis"|"Bootstrap"|"Operational"|"Dormant"|"Sunset"` to JavaScript. **A published API surface** whose documented name is the spec's, and whose values are not.
- **`hub/hub-daemon/src/admin.rs:282`** — the operator page renders `<dt>Metabolic state</dt><dd>{society.state}</dd>`. A human reading a running hub sees the spec's term over the wrong vocabulary.

**Severity argued down, then up.** Down: `admin.rs:282` is the hub's *only* read of `society.state` (verified by grep) — display-only, **no code keys authority, law, or ATP off it**, so there is no live authorization consequence today. Up to MEDIUM anyway on two grounds: (1) the composition hazard — SAL §3.6 defines "dormant states" as a *class of four metabolic states* (Sleep, Hibernation, Torpor, Estivation) and attaches an authority consequence ("dormant states SHOULD defer"), so "Metabolic state: **Dormant**" on an operator page is a term collision on a word that carries governance weight, with the two carried items (C168-N1 and B15/C58-B10) meeting for the first time; (2) the fix is monotonically getting more expensive — the rename is now a **breaking change on a published WASM getter**, not a comment edit.

One genuinely helpful window fact: `206dd004` armed the repo's first Rust CI (`web4-core` 193+4 tests green, matrix over four crate roots). The rename now has a machine-checkable blast gate it did not have at C168 — though the commit's own scope note is explicit that **CI green is not CI gating** (branch protection is steward-side). Auditor **MUST NOT** self-apply: the enum name is public API and the choice between renaming the Rust enum, re-labelling the two consumer surfaces, and amending the spec is an operator call.

### N2 — INFO — §5.2 is the corpus's first *positive* precedent for #580 → CBP, with #580

#580 asserts its principle is "already canon in two places" and cites `r6-framework.md` (corrective actions) and `data-formats.md` (unknown ≠ malformed). The C-series has so far handed that survey only adverse signals: **C280-N2** found a ratified counter-precedent (SOCIETY_SPEC §2.3), **C282-N1** found the canonical SDK imputing absence to the *maximum* (`dictionary.py:750-773`, "assume perfect"). This pass supplies the first confirming instance.

`SOCIETY_METABOLIC_STATES.md §5.2` `calculate_metabolic_reliability()` (`:308-329`) is four independent `+=` on *positive* evidence over a `score = 0.0` floor. A society with nothing measured scores **0.0**, the minimum — the exact inverse of `select_best_dictionary`'s ceiling default. This is #580's "Missing evidence → *less* trust, never assumed trust" already implemented in ratified spec text, 60 days before the proposal was written. It belongs in #580's precedent survey and materially strengthens it: the principle is not novel, it is *inconsistently applied*, which is a stronger case for canonization than novelty.

**Honest caveat, recorded with it:** §5.2 cannot distinguish *never hibernated* from *hibernated and failed every time* — both contribute 0.0. Under #580's sharp edge ("absence NEVER grants") that is **conformant**. Under #580's clause 3 ("materially incomplete → recursive correction, not termination") it is **silent**: no corrective act is spawned to obtain the missing observation. That is a question for #580's author about the proposal's own completeness, not a defect in a spec that predates it.

### N3 — INFO — Gate 1's blind-spot answer, and a demonstrated upgrade to C21-H1/H3 → method ledger + whoever adjudicates H1/H3

Recorded so the next pass inherits it: (a) **the metabolic lineage's mirror set was under-derived for seven passes** — `ledgers/` was never read, and it holds a spec-faithful 979-line implementation; (b) that implementation reproduces **all 8 states, all 8 energy multipliers, all 17 transition edges and all 4 auto-transition thresholds exactly**, and diverges on **exactly the 2 of 8 §5.1 rows that are stated on a non-decay axis** (§3.1 table). C21-H3 is no longer a stylistic complaint about a table; it is a defect with three implementers, two readings, and a demonstrated mis-resolution. Its severity in the carry ledger should be re-set accordingly by whoever adjudicates it. **Not booked as net-new** (stop rule: existing carries are not elevated to justify a fire).

### R1 — REFUTED — "#580 vs §5.1's dormancy freeze: frozen trust imputes a stale favourable value from absence"

The strongest available charge, and it fails. §5.1 freezes trust decay for Hibernation/Torpor/Estivation; a relying party could read a 90-day-old T3 of 0.9 with no current measurement behind it, which looks like absence being read favourably. **Refuted**: §3.2 requires every transition to be (1) recorded on the ledger and (5) written to society LCT metadata. The state is therefore *published alongside the frozen value* — a relying party sees "Hibernation" and can discount the tensor itself. That is not an imputation from absence; it is a value published with the fact of its own staleness, which is exactly LCT §1.2's "inspectable evidence, not prescribed trust". The refutation also re-confirms C244's ruling from a different direction and does not re-open it.

### R2 — REFUTED — "the 2026-05-11 triage classified `heartbeat_ledger.py` ARCHIVE and the decision was never executed on the two live copies"

An attractive finding, killed by baselining the instrument instead of trusting the filename. `docs/audits/reference-implementation-triage-2026-05-11.md:45` does classify a `heartbeat_ledger.py` (813 lines) as ARCHIVE, superseded by `web4-core`'s `LocalLedger`, and `cbc951a6` (2026-05-12, #175) did archive it — so on names alone, two live 979-line copies look like an unexecuted triage decision. **They are different files sharing a basename.** The archived 813-line file is *"Heartbeat-Driven Ledger Timing — Phase 5 of MRH Grounding Implementation"* and contains **zero** occurrences of the metabolic lexicon. The 979-line metabolic implementation has **never been triaged at all** — which is a smaller and truer statement than the one that was nearly filed. ([[feedback_enumeration_and_grep_hypotheses]] — the near-miss is the lesson: the classifier was the hypothesis, not the target.)

---

## 5. §C — Carries reconciliation (collapsed to one table, per policy review)

All eight tracked artifacts are byte-identical to the C244 snapshot (§1), and C244 re-anchored every carry by blob identity. Carry-by-carry re-narration would be the same padding §A avoids.

| Carry | Anchor | Anchor blob | State |
|---|---|---|---|
| **B1** SDK hibernation-wake omits `new_citizen`/90-day | `metabolic.py:147` | `d3d31446` | STILL STALE (by freeze) |
| **B3** SDK "Daily ATP Cost" vs spec §6.1 "Hourly" (`:341`) | `metabolic.py:207` | `d3d31446` | STILL STALE |
| **B4** SDK Torpor `"Frozen + alert bonus"` vs spec `"Frozen"` (`:299`) | `metabolic.py:110` | `d3d31446` | STILL STALE |
| **B11** SDK comment "Rest: queued" vs `return state == ACTIVE` | `metabolic.py:412-413` | `d3d31446` | STILL STALE |
| **B14** SOCIETY_SPEC §1.4 MUST-conform vs target "Proposed Standard" + §10 SHOULD | `SOCIETY_SPECIFICATION.md:89` | `2ad453ba` | OPEN, HELD |
| **B15 / C58-B10** SAL §3.6 dormant list omits Rest; "dormant states SHOULD defer" | `web4-society-authority-law.md:138-141` | `0849ebbe` | OPEN, HELD — **now composes with N1** |
| **C168-N1** `society.rs` 5-phase enum mis-cites the 8-state spec | `web4-core/src/society.rs:33-48` | `17112f05` | OPEN — **reach escalated, see N1** |
| **C21-H1** §2.3/§5.1 silent on Sleep `update_rate` | spec §2.3 / §5.1 `:297` | `5e3f7203` | OPEN — **demonstrated, see N3** |
| **C21-H3** §5.1 single column mixes incommensurable axes | spec §5.1 `:293-302` | `5e3f7203` | OPEN — **demonstrated, see N3** |
| **M3** emergency-state entry only from Active · **M5** define "dormant" · **M7** ontology absence · **L4** Estivation 10% < Sleep 15% · **L5** Rest queued-vs-refuse · **L7** wake-penalty state coverage | spec + `web4-core-ontology.ttl` | `5e3f7203` / `fc4b4c36` | ALL OPEN, HELD by freeze. M7 re-swept: 0 metabolic terms in the ontology at HEAD. |
| **C96-E1** ATP conservation cross-ref | `atp-adp-cycle.md` | `2d060579` | HELD |
| **C244** LCT §1.2-vs-§5 charge (metabolic §5 = rate modulation) | — | — | **CONSUMED — do NOT re-open.** R1 re-confirms it from a different principle. |

---

## 6. §D — Method notes and the next-delta guard

- **Stop rule (adopted from policy review, made binding before execution) was satisfied on all three clauses**: (a) eight artifacts byte-identical by blob hash; (b) whole-window lexicon diff = 1 line of whitepaper CHANGELOG prose, zero spec/SDK/crate lines; (c) all three gates returned a result with its criterion recorded *before* the grep ran. A 7th consecutive 0-net-new verdict on the target is the correct output, and no carry was elevated to manufacture one.
- **The C280 blind-spot lesson replicates, and its shape is now clearer.** C280 found `hub/` un-gated in the society lineage; C282 asked whether that was corpus-wide and answered **negative** for dictionary; C284 finds a *different* un-gated directory (`ledgers/`) in a *third* lineage. The generalization is therefore **not** "gate `hub/` everywhere" — it is that each lineage's mirror set was derived once, early, from whatever the auditor happened to know, and has been re-run rather than re-derived ever since. **Pre-registering the mirror criterion before sweeping is what makes the negative publishable**, and it is what stopped `simulations/` from becoming 126 attack sims' worth of manufactured findings this pass.
- **For the operator memo** (do NOT self-execute): the cadence question stands and gains a datapoint — a file byte-frozen two months, whose 7th pass yielded nothing about the file and three things about its *consumers*, is arguing for consumer-set re-derivation on a different clock than spec re-reading. Also note that `docs/SPRINT.md` **does exist** (last updated 2026-05-19, Sprint 55) and its §"Remaining from audit" lines still name the MetabolicState operator decision — i.e. the C168 §D item is recorded in two places and executed in neither.

**Guard for the next metabolic delta (~C322) — do NOT re-open as net-new:**
1. Target byte-frozen `5e3f7203` since `a504ea41`; 7 consecutive clean passes. Re-baseline from `8bc3ef39`.
2. **`ledgers/` is now IN this lineage's derived set as a non-mirror evidence source** (M2-fail, recorded). Do not re-file its §5.1 divergence as a defect; check only whether it *changed*, and whether anything promoted it to product-bearing.
3. **N1 is reach, not a new defect** — if C168-N1 is still open, check first whether the WASM getter and the hub admin label are still there, and whether anything began keying authority off `society.state` (today: nothing does).
4. N2 belongs to #580's survey; if #580 ratifies, §5.2 becomes precedent-bearing and C282-N1's `dictionary.py` charge and this one must be read together.
5. C21-H1/H3 carry a demonstration now (§3.1 table). Do not re-derive it; cite it.

---

## 7. Conclusion

Seventh consecutive frozen window, seventh consecutive clean verdict **on the spec** — and the third consecutive pass in which the yield came from re-deriving the gate rather than re-reading the file. The spec's transition matrix, energy model and trigger thresholds are strong enough that an independent 979-line implementation nobody knew about reproduces them exactly; the one place that implementation goes wrong is the one place the spec has been known to be ambiguous for 61 days, which is as clean an experimental confirmation of a standing finding as this series has produced. Meanwhile the defect that *is* live has been quietly getting more expensive: a mis-citation that was a crate comment at C168 is now the documented name of a published WASM getter and the label on an operator's screen.

Zero mutation. 0 net-new against the target, 1 MEDIUM reach-escalation and 2 INFO routed, 2 candidates refuted — one of them the pass's most attractive finding, killed by checking the instrument.
