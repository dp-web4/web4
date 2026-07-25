# C270 Audit: `t3-v3-tensors.md` 7th Delta Re-Audit

**Date**: 2026-07-24
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn, slot `web4-20260724-180011`
**Document**: `web4-standard/core-spec/t3-v3-tensors.md` (689 lines at HEAD; **byte-frozen** since C230 — blob `32d3368e`, last mover `d89595e8` / #531)
**Prior passes**: C13 (internal-consistency, 11 findings) → **C42 (1st delta)** → C43 remediation (#299) → **C82 (2nd delta)** → C83 remediation (#374) → **C121 (3rd delta)** → C122 remediation (#427, applied C118-N2) → **C154 (4th delta)** → **C192 (5th delta**, first Rust-mirror gate, N1–N4**)** → **C230 (6th delta**, C192-N1 closure witness**)**. This is the **7th delta**.

> **Ordinal correction (condition 3 of the policy review; [[feedback_enumeration_and_grep_hypotheses]] applied to this doc's own filename).** The delta counter for this file has been **off by one since C192**. `C192-t3-v3-tensors-4th-delta` self-labels "4th delta" and its *Prior passes* chain **omits C121 and C154 entirely** — but `C121-t3-v3-tensors-3rd-delta` self-labels "Third Delta Re-Audit" and `C154-t3-v3-tensors-4th-delta` self-labels "Fourth Delta Re-Audit". Re-derived from ground truth (the audit files themselves, not the inherited counter), the delta chain on this file is **C42(1) → C82(2) → C121(3) → C154(4) → C192(5) → C230(6) → C270(7)**. C192 and C230 are therefore each mislabeled by one; their **content** is unaffected and no finding changes. Filenames are historical artifacts and are **not** being renamed. Carry this corrected ordinal forward.

**Methodology**: Standard delta re-audit, single-auditor, refute-by-default, **zero mutation** of spec or SDK. §A = byte-identity regression argument against the C230 baseline blob + live re-anchor of every cited line number. §B = corpus-delta gate (34 commits) + **SDK/consumer mirror re-derivation at live HEAD**, whose flagship is the **2026-07-24 dp ruling** (`22d5a8f6`) landing in this file's mirror surface. §C = bidirectional re-verify of D1/D2/D3 + C192-N2/N3/N4, and **consumption of the inbound C238-N1** carry. Every load-bearing claim hand-verified against source at HEAD; the flagship was refuted three ways before being reported, and two of my own candidate findings were **downgraded by my own refutation** (recorded below).

**Reference materials** (at HEAD `22d5a8f6`): spec `t3-v3-tensors.md` (`32d3368e`, unchanged); `web4-trust-core/README.md` (`b9ba95ca`, **moved this window**); `web4-trust-core/src/tensor/mod.rs`; `web4-trust-core/src/entity/trust.rs`; `web4-core/src/t3.rs`, `v3.rs`; Python SDK `web4/trust.py`; vectors `web4-standard/test-vectors/t3v3/tensor-operations.json`; SDK tests `test_vectors.py` / `test_conformance.py` / `test_trust.py`; prior audit `docs/audits/cross-language-t3v3-alignment-2026-05-13.md`.

---

## Summary

| | Count / Verdict |
|---|---|
| **§A** spec delta since C230 | **0** — blob `32d3368e` **byte-identical**; all C230 anchors HELD at their recorded lines |
| **§A** frozen-body regression sweep | 0 regression (byte-identity is the proof; 6/6 anchors re-grepped at live HEAD) |
| **§B** spec-side substantive findings | **0** (spec CORRECT throughout — again) |
| **§B** net-new routed findings | **2** (**N1 MEDIUM**, **N2 MEDIUM**) + **1 INFO** (N3) |
| **§B** self-refuted candidates | **2 downgraded by my own refutation** (see §B.4) |
| **§C** carry re-verification | D1 STILL-OPEN · D2 **numeric facet RETIRED** (C238-N1 consumed) · D3 STILL-OPEN · C192-N3/N4 STAND · C192-N1 stays CLOSED |

**Health verdict**: the **spec is clean for the 7th consecutive-in-substance pass**; nothing in `t3-v3-tensors.md` needs correction. All yield this delta came from a **window event**, exactly as at C268: a **dp ruling committed ~3 hours before this fire** (`22d5a8f6`, 2026-07-24 15:12 PDT) landed inside this file's mirror surface and created a **gate-anchoring collision** with §10.2. The C268 METHOD CARRY fired on the very next fire, in a variant form: not a canonized *principle* re-scoping a frozen spec, but an operator *ruling on an implementation* whose merge gate points at the implementation rather than at the spec's normative vector file.

---

## §A — Spec Delta + Regression Sweep

`git diff --name-only 02ef374b..HEAD` (C230's HEAD → this HEAD, 34 commits) touches **zero** paths under `web4-standard/` and **zero** under `web4-core/`. `git rev-parse HEAD:web4-standard/core-spec/t3-v3-tensors.md` = **`32d3368e`** — byte-identical to the C230 baseline. The file has not moved since #531 (`d89595e8`, 2026-07-16).

**Byte-identity is the regression proof.** Re-grepped the six load-bearing anchors at live HEAD (per [[feedback_prior_finding_path_provenance]] — never trust a carried line number):

| Value | C230 line | HEAD line | Status |
|-------|-----------|-----------|--------|
| §2.3 "Talent Stability: No decay" | L125 | **L125** | HELD |
| t3v3-012 "Talent MUST NOT decay through inactivity" | L635 | **L635** | HELD |
| §10.2 ATP-conservation anchor (C83-F2/C118-N2) | L642 | **L642** | HELD, still accurate |
| §10.4 anti-example "0.995 per period" | L675 | **L675** | HELD |
| t3v3-001/002 composite weights `0.4/0.3/0.3`, `0.3/0.35/0.35` | L631/632 | **L631/632** | HELD |
| §3.3 "distinct weights" (C83-F3) | L339 | **L335** (`weights valuation=0.3, veracity=0.35…`) | HELD — the C230 table's L339 was the section body; the authoritative-values sentence sits at L335. Same clause, no motion. |

The C230 "+2 shift below §1.1" provenance note is now **consumed** — that shift was absorbed at C230 and the numbers above are the post-shift live values. Do not re-apply it.

**§A verdict: 0 delta, 0 regression, all carries HELD by byte-identity.**

---

## §B — Mirror Re-Derivation at Live HEAD

Per the standing METHOD GUARD, the mirror set was **re-derived, not assumed**. Window movers by area: `docs/audits` (20 of 34 commits), `docs/specs`, `hub/*`, `web4-trust-core/README.md`, `whitepaper/PUBLISHER_CONTEXT.md`.

### B.0 — Corpus-delta gate (NEGATIVE candidates, one line each)

- **`hub/` + `docs/specs/` window diff** — `git diff 02ef374b..HEAD -- hub/ docs/specs/ | grep '^+' | grep -iE '\bt3\b|\bv3\b|tensor|talent|temperament|veracity'` returns **zero added lines**. `docs/specs/constellation-enrollment-registry.md:64` ("derive an assurance tier a relying party scales trust to") is assurance-tier vocabulary, **not** a T3/V3 surface. **Gate NEGATIVE.** (Pre-tested by the policy reviewer; confirmed independently. Manufacturing a mirror finding here would have been the drift.)
- **`forum/nova/web4-sal-bundle/t3-v3-tensors.md`** (374 L vs the live 689 L) — a **static inbound Nova proposal snapshot**, already known to the corpus via the SAL audits (`sal-internal-consistency-2026-05-27`, C23, C134). Not a mirror, not a consumer, unmoved this window. **Gate NEGATIVE, pre-existing.**
- **`whitepaper/PUBLISHER_CONTEXT.md`** — no-change verification log (`950eb251`). **DISJOINT.**

### B.1 — The window event: `22d5a8f6`, a dp ruling inside the mirror surface

`web4-trust-core/README.md` gained a nine-line **"Successor research track"** section (`22d5a8f6`, "trust-core: pointer to the derivation successor track (dp ruling 2026-07-24)", authored by Dennis Palatov):

> A derivation-as-law successor for this crate's update/decay arithmetic is being developed at [`dp-web4/web4-trust-core`](https://github.com/dp-web4/web4-trust-core) (a *repo*, distinct from this crate; nothing there is published to crates.io). When its merge gate passes — **a DerivationSpec reproducing this crate's normative t3v3 vectors** — that work ships as a new release **of this crate, under this name**. Until then, **this crate is the enforced semantics**.

`web4-trust-core` is squarely inside this file's mirror set: C192 and C230 both gated `src/tensor/mod.rs` and `src/entity/trust.rs`, and **C192-N1 was about this exact crate**.

### B.2 — C270-N1 (MEDIUM) — the successor merge gate is anchored to the crate, not to the §10.2 vector file

**Finding.** The gate condition is *"a DerivationSpec reproducing **this crate's** normative t3v3 vectors."* Three facts, each verified at HEAD:

1. **The crate ships no vectors.** `find web4-trust-core -name '*vector*'` → nothing; the only JSON in the crate tree is `pkg/package.json`. The single normative t3v3 vector set in the repo is `web4-standard/test-vectors/t3v3/tensor-operations.json`, which spec §10.2 (L622) designates: *"**This table is the normative source** … enforced by cross-language test vectors in `web4-standard/test-vectors/t3v3/tensor-operations.json`."*
2. **No Rust code references it.** `grep -rl 'tensor-operations\|test-vectors'` across the repo returns only Python SDK tests, `web4-standard/test-vectors/validate_vectors.py`, and `whitepaper/make-web.sh`. Both Rust crates: **zero hits**.
3. **The crate's sole T3-update path diverges from a §10.2 protocol-invariant row.** `web4-trust-core/src/tensor/mod.rs:129-141`:

   ```rust
   pub fn t3_update_from_outcome(t3: &mut T3, success: bool, magnitude: f64) {
       let training = t3.score(TrustDimension::Training);
       let delta = if success { magnitude * 0.05 * (1.0 - training) }
                   else       { -magnitude * 0.10 * training };
       t3.apply_delta(TrustDimension::Training,   delta);
       t3.apply_delta(TrustDimension::Temperament, delta * 0.5);
       t3.apply_delta(TrustDimension::Talent,      delta * 0.3);
   }
   ```

   §10.2 L633-634 fixes **T3 update formula = `0.02 × (quality − 0.5)`** (vector t3v3-003) and **T3 dimension update factors = talent 1.0 / training 0.8 / temperament 0.6** (t3v3-003). The crate **inverts the dimension ordering** — Talent, which the spec makes the *most*-updated dimension (1.0), is the crate's *least*-updated (0.3×) — and replaces the symmetric quality-centred delta with an asymmetric success/magnitude one. Python `trust.py:77-84` holds the spec values exactly (`T3_UPDATE_RATE = 0.02`, `T3_UPDATE_FACTORS = {talent 1.0, training 0.8, temperament 0.6}`).

**Therefore**: a gate read literally — *reproduce this crate's vectors* — would have the derivation-as-law successor **canonize the divergence** rather than converge on §10.2. There is no artifact in the crate for a DerivationSpec to reproduce except the crate's current behaviour, and on t3v3-003/004 that behaviour is not §10.2's.

**This finding does NOT adjudicate the SSOT question.** dp issued the ruling; whether crate or spec is authoritative for update/decay arithmetic is dp's call and the successor track exists precisely to settle it. The finding is narrower and answerable without settling it: **the gate does not name which artifact it means.** Suggested author fix (not applied, not an auditor edit): anchor the gate to the vector file **by path**, e.g. *"a DerivationSpec reproducing the t3v3 conformance vectors at `web4-standard/test-vectors/t3v3/tensor-operations.json`"* — or, if the crate's current arithmetic is deliberately the target, say so explicitly and record the §10.2 rows it supersedes.

**Route**: **author + operator**. `22d5a8f6` is an operator-attested commit; an auditor MUST NOT edit it. Severity **MEDIUM** (a research-track gate condition, not a live consequential surface — but it is the gate that decides what the *next* release of a **published** crate (`pip install web4-trust`) enforces).

**Refutations attempted (3), all survived:**

- **R1 — "the contrast set is {this crate, the successor repo}, not {crate, spec}."** The paragraph disambiguates two *implementations*; "until then" means "until the successor's gate passes," so "enforced semantics" plausibly means "depend on this crate, not that repo." **Assessment: correct about intent, and it is why this is MEDIUM rather than HIGH — but it does not touch the finding.** The finding is about the *gate condition's referent*, which is a separate clause ("reproducing this crate's normative t3v3 vectors") and is under-determined regardless of what "enforced semantics" means.
- **R2 — "'this crate's normative t3v3 vectors' is a loose possessive for 'the standard's vectors, as implemented here'."** Plausible reading. But under it the gate is satisfied by reproducing `tensor-operations.json` — which the crate's own `t3_update_from_outcome` **does not** satisfy today. So the charitable reading makes the gate *stricter than the crate*, and the uncharitable reading makes it *canonize the crate*. The two readings give **opposite** outcomes for the successor. That ambiguity **is** the defect. **Not refuted — strengthened.**
- **R3 — "dp already knows; a track exists for exactly this arithmetic."** The strongest refutation: this is a known-and-tracked open question, not an undetected defect. **Assessment: accepted, and it caps severity at MEDIUM and forbids any framing as news.** It does not dissolve the finding, because knowing the arithmetic is open is compatible with the gate accidentally pointing at the wrong artifact — that is a drafting fact about `README.md:102-104`, independent of what dp intends to decide.

**Adjudicate jointly with the standing flagship B-D1 / C-M1** (SSOT inversion) — same defect *class* (implementation designated normative over a spec-designated normative source), different file. **N1 is a new instance, not a duplicate**: B-D1 is the `registries/` directory's README/orphan-file inversion.

### B.3 — C270-N2 (MEDIUM, cross-track) — §10.2's "cross-language test vectors enforce them" is unbacked in fact

§10.1 (L612) and §10.2 (L619-621) both stake conformance on the vectors:

> **Protocol-invariant** | MUST / MUST NOT | Fixed by the specification. Implementations MUST use exactly these values. **Cross-language test vectors enforce them.**
> These values are fixed by the specification. All conforming implementations MUST produce identical results (**enforced by cross-language test vectors** in `web4-standard/test-vectors/t3v3/tensor-operations.json`).

At live HEAD the file is loaded by **exactly one language**. Consumers (`grep -rl 'tensor-operations\|t3v3/'`): `web4-standard/implementation/sdk/web4/trust.py`, `sdk/tests/test_conformance.py`, `sdk/tests/test_vectors.py` (`:56` `load_vectors("t3v3/tensor-operations.json")`), `sdk/tests/test_trust.py`, plus `test-vectors/validate_vectors.py` (a JOSE/COSE canonicalization checker — not a tensor harness) and `whitepaper/make-web.sh`. **Zero Rust tests load it.** The only t3v3 tokens in either Rust crate are four *prose comments* citing `t3v3-012` (`web4-trust-core/src/tensor/mod.rs:192`, `entity/trust.rs:668`, `web4-core/src/t3.rs:352` and `:534`) — a hand-written citation, not an executed assertion.

**Empirical proof of consequence, not a hypothetical**: `web4-trust-core` carried `decay_value(old_talent, 0.995)` — the *literal* value §10.4 L675 pre-emptively names as spec-violating — from crate birth until #517 on **2026-07-13**. It was documented on **2026-05-13** (`cross-language-t3v3-alignment-2026-05-13.md`, divergence #1, CRITICAL) and still took ~2 further months to fix. It was caught by **audits, twice** (the 2026-05-13 pass and then C192-N1), never by the vectors. A mechanism the spec calls "enforcing" did not enforce, on the invariant the spec states twice, in the crate the 2026-07-24 ruling now calls "the enforced semantics."

**Direction: the SPEC IS CORRECT.** The vectors *should* be the cross-language enforcement; that is the right design. What is missing is a **Rust harness that loads `tensor-operations.json`** — the same shape as `sdk/tests/test_vectors.py`, in `web4-core/tests/` and/or `web4-trust-core/tests/`. **Do not weaken §10.2's language to match reality; build the harness.** Note that such a harness would, on the day it lands, fail on t3v3-003/004 for `web4-trust-core` — which is the point, and is why it couples to N1.

**Route**: SDK/build-track, joins the C180–C192 wire-layer-readiness synthesis. **No spec mutation. Not self-applied** — writing a Rust conformance harness is implementation work outside an audit turn's scope, and it would pre-empt the very question N1 routes to the operator (reproduce *which* artifact?).

### B.4 — Self-refuted candidates (2 downgraded by my own refutation)

Per [[feedback_refute_your_best_finding]], I pointed the refuter at my own strongest material. Two candidates I initially rated HIGH did **not** survive:

- **Candidate: "T3/V3 composite weights divergence persists in `web4-trust-core` (2026-05-13 divergences #2/#3, HIGH)."** Live code: `tensor/mod.rs:109-114 t3_average()` = flat `/3.0`, `:212-217 v3_average()` = flat `/3.0`; neither applies the §10.2 weights. **REFUTED down to INFO.** The functions are now named `t3_average` / `v3_average` (not `composite`), and `:104-108` explicitly documents *"deliberately **not** `T3::aggregate()` … the categorical trust level is defined over the flat average."* The crate does not compute the protocol composite **at all** — this is **absence / layer-split, not divergence**, and it is the identical shape the C-series already ruled INFO for `web4-core` at **C192-N3**. The 2026-05-13 HIGH rating described code that called this "the composite"; the corpus partially self-corrected by *renaming*. Do **not** carry these as HIGH.
- **Candidate: "T3 decay model still wrong (2026-05-13 divergence #5)."** Live `tensor/mod.rs:174-198` decays Training (factor 1.0) and Temperament (0.98) via `(1−rate)^days` toward a floor of 0.3 — not §2.3's "−0.001 per month". **REFUTED to NOT-A-DEFECT.** §10.3 classifies "Training decay rate" and "Temperament recovery rate" as **society-configurable** with the spec values as *reference defaults* ("Societies **MAY** configure custom decay policies"). Only the **Talent** half of divergence #5 was protocol-invariant, and it is CLOSED by #517 (the `continue`/removal verified HELD at `tensor/mod.rs:192-197` and `web4-core/src/t3.rs:352`). Same reasoning clears `v3_apply_decay` and `v3_update_veracity`: no §10.2 row governs them.

That leaves **exactly one** genuine §10.2-invariant divergence in `web4-trust-core` — the update formula (t3v3-003/004) — which is folded into N1 as its factual load. Reporting "three HIGH divergences persist" would have been wrong.

### B.5 — C270-N3 (INFO) — pre-C-series ledger blind spot, first worked example

`docs/audits/cross-language-t3v3-alignment-2026-05-13.md` (Sprint 47 T1, operator-triggered) enumerated **8 divergences** of `web4-trust-core` from the vectors: 1 CRITICAL, 4 HIGH, 2 MEDIUM, 1 LOW. **None was ever promoted into the C-series carry ledger.** C192 rediscovered divergence #1 independently as C192-N1; C192-N3 booked a *different* crate's composite absence as INFO. Divergences #2–#8 have never appeared in a C-series `§C`. This is exactly the blind spot the standing **C168 operator-memo ask** names (*"one-time sweep of pre-C-series 'Operator Decision Required' sections"*) and exactly the [[feedback_prose_is_not_ledger]] failure mode: an item recorded in prose but never promoted into a carry ledger vanishes.

**Live re-adjudication of the 2026-05-13 set** (bounded to what this pass verified; paths re-derived — the audit cites `src/tensor/t3.rs`/`v3.rs`, which **no longer exist**; the crate was restructured to `src/tensor/mod.rs` over `web4_core::{t3,v3}` types):

| # | 2026-05-13 claim | Severity then | Live verdict at C270 |
|--:|------------------|---------------|----------------------|
| 1 | Talent decay applied | CRITICAL | **CLOSED** by #517 (=C192-N1); re-verified HELD |
| 2 | T3 composite unweighted | HIGH | **INFO — absence/layer-split** (§B.4); do not carry as HIGH |
| 3 | V3 composite unweighted | HIGH | **INFO — absence/layer-split** (§B.4) |
| 4 | T3 update wrong formula | HIGH | **STILL LIVE, genuine** → folded into **C270-N1** |
| 5 | T3 decay wrong model | HIGH | **Talent half CLOSED**; Training/Temperament half = §10.3 **society-configurable, NOT a defect** (§B.4) |
| 6 | No ActionOutcome evolution (t3v3-011) | MEDIUM | **NOT re-verified this pass** — bounded scope, carried |
| 7 | Legacy 6D bridge formula (t3v3-008) | MEDIUM | **NOT re-verified this pass** — carried |
| 8 | Missing vector operations (t3v3-007, 009-015) | LOW | **NOT re-verified this pass** — carried; substantially subsumed by **N2** (no Rust harness exists to run any of them) |

**No silent cap**: #6/#7/#8 were **not** examined. They are recorded as unverified rather than dropped, and they are the natural first output of the N2 harness.

---

## §C — Standing Carries (bidirectional re-verification at live HEAD)

- **D1 — ontology-vocabulary divergence — STILL-OPEN.** `grep -rn matchesTask` corpus-wide → exactly 2 hits: `web4-standard/core-spec/t3-v3-tensors.md:551` and the static forum bundle copy `:359`. **Zero defining triple** in `web4-standard/ontology/`. Role IRIs (`web4:Surgeon` et al., L365/402/407/593/595) remain undeclared as classes/individuals. Unchanged. Folds into the standing C40 ontology-vocab bundle.
- **D2 — RE-SCOPED. The numeric facet is RETIRED; only the structural facet survives.** **Consuming inbound C238-N1** as instructed: the claimed cross-doc contradiction "Surgeon `training` 0.92 (t3-v3) vs 0.90 (mrh)" is **STALE and now verified dead at HEAD** — `mrh-tensors.md:264` reads `web4:training 0.92 ; # Extensive medical training (aggregate — shorthand)`, matching t3-v3. There is **no 0.90**. It was refuted at C200 and again at C238, and **C230 re-carried it in error**. **Do not re-carry it.** What remains of D2 is the **X4 structural facet only**: mrh §5 duplicates this file's role-contextual principle and the Surgeon Turtle example, and the operator attach-strategy decision still gates the multi-device rewrite. **Status-only inbound from C268**: multi-device N1/N2 (flat-8 `t3_tensor`, no entity-role binding) are the **t3-v3-side face of D2's attach-strategy DESIGN-Q**. Recorded, **not** decided here.
- **D3 — V3 Valuation range 3-way divergence — STILL-OPEN, unchanged.** `web4-core/src/v3.rs` was not touched this window; the clamps persist at `:137` (`scores[i].clamp(0.0, 1.0)`) and `:191` (`(before + delta).clamp(0.0, 1.0)`). spec + ontology (unbounded, per the §10.2 caveat note L646-648) vs Python SDK + Rust `web4-core` (both clamped) — the 2-vs-1-toward-clamping posture from C192-N2 holds, not re-hardened. Operator semantic decision still required. Couples C42 F1/F25.
- **C192-N1 — stays CLOSED.** Re-verified HELD by direct read: `web4-trust-core/src/tensor/mod.rs:192-197` (the `0.995` triple is gone, replaced by the invariant comment) and `web4-core/src/t3.rs:352`/`:534`. No regression, no reintroduction.
- **C192-N3 (INFO) — STANDS**, and is now **precedent-bearing**: it is the ruling this pass applied to downgrade the `web4-trust-core` composite candidates in §B.4.
- **C192-N4 (INFO) — STANDS.** Rust tensors still carry no entity-role binding; feeds D2's structural facet, now joined by the C268 multi-device status note.

---

## §D — Lessons

1. **The C268 METHOD CARRY fired on the very next fire, in a second variant — and the variant matters.** C268: a canonized *principle* retroactively re-scoped a byte-frozen spec. C270: an operator *ruling on an implementation* created a gate whose referent the frozen spec already owns. Same shape (the window, not the target, holds the yield; a freeze protects a file from churn **and** from being kept current), different vector. Generalize the carry: **on each delta, ask what landed in the window that CLAIMS AUTHORITY over the target's subject matter** — principle, ruling, README, or release note — not merely which sibling spec changed. Two consecutive fires now say the frozen target is the least informative thing in its own audit.
2. **Downgrading your own candidates is the finding.** Three prior-audit HIGHs went in; one genuine divergence came out. Two were killed by reading the *doc comments* on the code (`"deliberately not T3::aggregate()"`) and by reading the spec's own **governance tier** (§10.3 society-configurable) rather than only its body text. An auditor who had simply re-asserted the 2026-05-13 severities would have reported three HIGH divergences, two of them wrong — and, worse, would have made the one real finding harder to see. §10's three-tier table is the instrument: **check the tier before calling a mismatch a defect.**
3. **An enforcement claim is a testable claim, and this corpus had never tested it.** §10.2 says the vectors "enforce" cross-language identity. One `grep -rl` settled it: one language. The proof that it matters was already in the ledger — a literal spec-violating constant survived from crate birth to #517 while the "enforcing" mechanism sat unwired. **When a spec names its own enforcement mechanism, grep for the mechanism's consumers.** That is a five-second check that no prior t3-v3 delta ran across seven passes.
4. **The delta counter was wrong for three passes because each audit inherited the previous one's ordinal instead of re-deriving it.** C192 dropped C121 and C154 from its provenance chain and self-labelled "4th"; C230 accepted "4th" and wrote "5th". [[feedback_enumeration_and_grep_hypotheses]] applies to an audit's own metadata: *re-derive the count from ground truth (the files), not from the last claim*. The policy reviewer caught this before the doc was named — a reviewer reading the artifact list beats an auditor reading its own memory.

---

## Disposition

- **Spec-side (this file)**: **substantive-CLEAN**. **No C271 remediation item owed on `t3-v3-tensors.md`.** Byte-frozen since #531; nothing to fix.
- **Net-new, routed (do NOT self-apply):**
  - **C270-N1 (MEDIUM) → author + operator.** `web4-trust-core/README.md:102-104` — the successor merge gate ("a DerivationSpec reproducing **this crate's** normative t3v3 vectors") names no reproducible artifact: the crate ships no vectors, no Rust test loads the spec's, and the crate's sole T3-update path (`tensor/mod.rs:129-141`) diverges from §10.2's protocol-invariant update-formula and dimension-factor rows (t3v3-003/004, Talent factor 0.3× vs the spec's 1.0×). Read literally the gate would canonize the divergence. Ask: anchor the gate to `web4-standard/test-vectors/t3v3/tensor-operations.json` by path, or state explicitly which §10.2 rows the crate's arithmetic supersedes. **Operator-attested commit — auditor MUST NOT edit.** Adjudicate alongside **B-D1 / C-M1** (same class, new instance, not a duplicate).
  - **C270-N2 (MEDIUM) → SDK/build-track.** §10.2/§10.1's "cross-language test vectors enforce them" is unbacked: `tensor-operations.json` has Python consumers only; both Rust crates hold hand-written `t3v3-012` *comments*, not executed assertions. **Spec CORRECT — build the harness, do not weaken the spec.** Joins the C180–C192 wire-layer-readiness synthesis. Couples to N1 (the harness would fail on t3v3-003/004 the day it lands — by design).
  - **C270-N3 (INFO) → operator memo (C168 item).** The 2026-05-13 pre-C-series cross-language audit's 8 divergences never entered the C-series ledger. Re-adjudicated live: #1 CLOSED, #2/#3 INFO (absence, per the C192-N3 precedent), #4 live (→N1), #5 Talent-half CLOSED / rest society-configurable and not a defect, **#6/#7/#8 explicitly NOT re-verified** this pass. First worked example for the standing "sweep pre-C-series audits into the ledger" ask.
- **Carry ledger changes**: **D2's numeric facet is RETIRED** (C238-N1 consumed; the mrh `0.92`-vs-`0.90` contradiction is verified dead at `mrh-tensors.md:264` — do **not** re-carry). D1, D2-structural, D3, C192-N3, C192-N4 STAND. C192-N1 stays CLOSED.
- **Ordinal**: this file's delta chain is **C42(1) C82(2) C121(3) C154(4) C192(5) C230(6) C270(7)**. C192 and C230 filenames are off by one; **not** renamed.
- **Cadence observation (one line, §D-adjacent, routed not self-executed)**: 20 of this window's 34 commits are audit docs and four of the last five fires were zero-net-new, while both C268 and C270 found their yield in a **window event** rather than in the frozen target. Whether the rotation should shift from fixed-order round-robin to **event-triggered** (fire on corpus-delta or on a normative claim landing in the target's subject matter; skip otherwise) is an **operator** question. Recorded here; **not** self-decided.

**Next fire = C272 = `reputation-computation.md`** (rotation +2). The next `t3-v3-tensors.md` delta is a full rotation later (**~C310**); when it comes, re-baseline from blob `32d3368e` unless it has moved, re-derive the mirror set at live HEAD **including whatever the successor track has shipped by then**, and check first whether N1's gate was re-anchored and whether an N2 Rust vector harness exists.
