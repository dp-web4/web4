# C392 — `reputation-computation.md`, 10th delta

**Date**: 2026-08-15
**Target**: `web4-standard/core-spec/reputation-computation.md` — blob `bfdac3ba`, 870 L
**Freeze**: last mover `2bc3bafb` (2026-07-18) ⇒ **byte-frozen 28 days**; same blob C232, C272, C312 **and C352** audited — 5th consecutive frozen pass
**Prior pass**: C352 (PR #685, `927eecad`, 2026-08-10)
**Lineage at HEAD**: **13** documents — 10 passes (`…-internal-consistency-2026-05-25`, C44, C84, C123, C156, C194, C232, C272, C312, C352) + 3 remediations (C124, C157, C195). *(C352 reported 12 under this same inclusive rule and was correct at its own commit — it was not yet in the tree when it counted. The inclusive rule — basename matches `reputation`, both audit trees, remediations and the non-C-numbered internal-consistency member included — is applied here to this lineage **and** to every lineage this document counts.)*
**Result**: **1 MED, 1 LOW, 2 INFO. ZERO mutation of the standard.**

---

## Headline

**§4 defines a normative trigger condition, `quality_threshold`, over an output key that no schema in the corpus defines. 232 lines later the same document adopts a *second* undefined key for the same concept — written in by this lineage's own C45 remediation, twelve days before C85 wrote in the clause it contradicts, and neither swept the other. A third undefined key is published by the corpus's own canonical R7 action-serialization vector, and `git grep` shows nothing reads it. Executed: an action serialized exactly as that vector prescribes triggers no reputation rule and produces no quality factor.**

---

## §0 — Method, and what this pass did NOT do

Both halves of the corpus delta are a **measured zero** (§B). This is the 6th consecutive fire on this track whose whole yield is machine checks plus the inbound sweep, so the pass was run as opening-sequence step 1 — execute the frozen artifacts against **each other** — and not as a delta read.

Scope was **revised by the policy reviewer before execution**, and the revision is recorded here rather than absorbed silently. The reviewer **falsified three premise cells and killed one rescue reading**; every correction was re-verified against the artifacts before acceptance (v52 — *verify the reviewer's corrections too*), and all three held. The headline this document publishes is **not** the one proposed. See §F.

**What this pass did NOT do**: it did not mutate `web4-standard/`, did not edit the SDK, and did not add a test. The remedy **forks three ways** and two of the arms change the conformance behaviour of a **released** SDK in opposite directions; picking an arm is a standard-editor decision. It is routed (§C, N1 routing), not applied.

---

## §A — Prior findings and carries

### A.1 — C352's five forward guards, answered first

| # | C352's guard | Answer at HEAD | Command |
|---|---|---|---|
| 1 | *"check which ARM of N1 was taken — if a `$def` was minted, verify the **context** gained the terms too"* | **Neither arm taken.** `$defs.witness_attestation` still has exactly 4 properties (`attestation, lct, signature, timestamp`), `additionalProperties: false`, 6 `$defs` total, 3 `$ref` sites. Context `r7-action.jsonld:63` still types `attestation` as `xsd:string`. **Fork UNANSWERED.** | `python3 -c "json.load(...)['$defs']['witness_attestation']"` |
| 2 | *"two unanswered forks now stand on the same `$defs` block from two consecutive passes — that is itself the signal"* | Now **three** consecutive passes (C312-N1, C352-N1, and this one re-measuring both). Re-raised in §C-N3, **not** re-charged. | — |
| 3 | *"enumerate schema trees with `git ls-files`, NEVER `schemas/*.json`"* | **Discharged, and the trap reproduced**: `git ls-files 'web4-standard/schemas/**' \| grep -c '\.json$'` = **24**; `ls web4-standard/schemas/*.json \| wc -l` = **12**. C352's own §F.7 error is exactly reproducible. Every schema count in this document uses the recursive form. | both, above |
| 4 | *"extract the line range from every prior **DECLINE**, not just every prior PASS"* | Discharged. The lineage's only DECLINE is C272's INFO-2 witness-side decline citing `:607-633`; C352-N3 already adjudicated it. No further decline exists. This pass's findings are in §4/§5, outside that range. | `grep -rn "DECLINE\|declined" docs/audits/*reputation*.md` |
| 5 | *"re-derive this pass's sweep numbers"* | Discharged — every count in this document was re-derived at HEAD; none is inherited. C352's filtered counts are **not** reused. | §E.4 |

### A.2 — Carries whose locus is INSIDE the frozen blob

Target blob at HEAD = `bfdac3ba` = the blob C352 audited. All in-blob anchors hold **by byte-identity**, declared rather than re-walked — *except* C352-N1, which was **re-executed anyway** because guard 1 turns on it:

> **C352-N1 re-executed.** §6's witness element (`:657-670`) validated against `$defs.witness_attestation` under Draft 2020-12 → **2 errors**, identical to C352's published pair: `Additional properties are not allowed ('type' was unexpected)` and `{...} is not of type 'string'`. The §1 `:56` control element (`{lct, signature, timestamp}`) → **0 errors** on the same validator. Exhibit unchanged, fork live.

### A.3 — Carries whose locus is OUTSIDE the frozen blob (re-executed)

All 7 delta-shape mirrors are byte-frozen; **0** of the 28 window commits touch any of them (§B). C352-N2 (§1 omits `attestation`) and C232-N1 (schema `category` absent) hold unchanged.

### A.4 — Regressions

**None.** Full SDK suite `2750 passed, 5 xfailed`; `tests/test_reputation.py` `45 passed`; `tests/test_conformance.py` `34 passed, 5 xfailed` (39 collected).

---

## §B — The window (two commands, one table)

```
git log --oneline 927eecad..HEAD                     | wc -l   ->  28
git log --oneline 927eecad..HEAD -- web4-standard/   | wc -l   ->   0
```

| artifact | blob | L | last mover | in window? |
|---|---|---|---|---|
| `core-spec/reputation-computation.md` | `bfdac3ba` | 870 | `2bc3bafb` 2026-07-18 | no |
| `schemas/r7-action-jsonld.schema.json` | `b266a19b` | 365 | `766611ef` 2026-05-14 | no |
| `schemas/contexts/r7-action.jsonld` | `015b6e68` | 107 | `936c2d92` 2026-03-24 | no |
| `implementation/sdk/web4/reputation.py` | `bb73c7c2` | 628 | `759eaefa` 2026-04-17 | no |
| `implementation/sdk/web4/r6.py` | `013af40c` | 1264 | `766611ef` 2026-05-14 | no |
| `test-vectors/reputation/reputation-operations.json` | `11234034` | 165 | `740f21de` 2026-03-16 | no |
| `implementation/sdk/tests/test_reputation.py` | `eb091265` | 910 | `759eaefa` 2026-04-17 | no |

**Both halves empty.** The 28 window commits are 12 C-series audit docs, 8 hub/PRD commits, and merges — none reaches `web4-standard/`.

### §B.2 — The inbound sweep (v36 as a set difference, window pre-registered)

**Pre-registered rule** (stated before running): tree = `web4-standard/`, excluding `web4-standard/docs/`; domain word = `reputation`; subtract the filename sweep `reputation-computation`.

```
git grep -li "reputation"             -- 'web4-standard/*' ':!web4-standard/docs/*'  ->  95
git grep -li "reputation-computation" -- 'web4-standard/*' ':!web4-standard/docs/*'  ->  13
residue (comm -23)                                                                   ->  82
```

Of the 82 residue members, **13 have never been cited by any audit in either tree**. One of them is load-bearing for this pass: `web4-standard/R6_TENSOR_GUIDE.md` (0 audits, 10 months) publishes a `quality_threshold` — and following it produced the key enumeration that became N2. **This is the sweep's entire yield, and it is recorded because a filename sweep could not have returned it** (v48: a path-token sweep is a citation-graph query and cannot see an orphan).

**Negative recorded**: the unbounded domain-word sweep over the whole repo returns 410 files / 330-member residue and is useless — the word `reputation` reaches every sprawl tree. The bound is what makes the residue readable.

---

## §C — Findings

### C392-N1 (MEDIUM, routed 3 ways — remedy FORKS, do NOT self-apply) — a normative trigger condition defined over a key no schema defines, and a second key for the same concept written in by this lineage 12 days earlier

**The claim.** §4's trigger-condition table `:292` makes `quality_threshold` normative over `output.quality`:

> `| quality_threshold | Matches **iff** `output.quality >= threshold`. A missing quality value is treated as `0.0`, so the threshold fails. |`

232 lines later, §5's `analyze_factors` `:524` reads the same concept from **either of two keys**:

> `quality = result.output.get('quality', result.output.get('accuracy'))`

The reference SDK implements both, in the same module: `reputation.py:106` (`output.get("quality", 0.0)`) and `reputation.py:181` (`output.get("quality", output.get("accuracy", None))`).

**Neither key is defined by any schema.** `schemas/r7-action-jsonld.schema.json` types `result.output` as `{"type": "object", "additionalProperties": true, "description": "Action output data."}` and contains neither the string `quality` nor `accuracy`. `grep -iE "strict by design|heuristic"` over the target returns **0 hits** — the asymmetry is nowhere disclosed.

**Executed** (§4's rule verbatim `:245-281`, the §5 worked example's own scenario `:568`, arms differing only in the output key):

| arm | `result.output` | `matches()` | engine `evaluate()` | `analyze_factors()` — public export |
|---|---|---|---|---|
| **A** | `{"quality":0.97,"accuracy":0.97}` — `rep-001:15` / fixture `:63` | True | **net trust +0.0245** | `high_accuracy, deadline_met, early_completion` |
| **B** | `{"quality":0.97}` — control, the key `:292` names | True | +0.0245 | same |
| **C** | `{"accuracy":0.97}` — the key `:524` accepts and `:292` does not | **False** | **None — no delta** | `high_accuracy, deadline_met, early_completion` |
| **D** | `{"rows_processed":10000,"quality_score":0.95}` — **verbatim** from `test-vectors/schema-validation/r7-action-jsonld-validation.json:121` | **False** | **None — no delta** | **`deadline_met, early_completion`** — no quality factor at all |

**Arm A is a backed control**: it reproduces the spec's own published Net Trust **+0.0245** at `:589`, so the harness is measuring what the document claims.

**What arm C does and does NOT show.** It does **not** show that the engine simultaneously scores the action high-accuracy and rejects it: `evaluate()` short-circuits at `reputation.py:249-250` (`if not triggered: return None`) **before** `analyze_factors` runs at `:252-253`, and the spec discloses exactly this at `:514-517` ("matched against each **triggered** rule's modifier conditions"). The factors in column 4 come from calling `analyze_factors` **directly**. That is a real surface — `analyze_factors` is in `__all__` (`reputation.py:45`) and `evaluate(action, factors=...)` accepts caller-supplied factors (`:237-240`) — so a conforming implementation that derives factors and then hands them to the engine gets a `high_accuracy` factor for an input the engine will never match. But the claim is scoped to that surface, not to the engine path. *(This correction is the reviewer's; see §F.3.)*

**Arm D is the live one.** `r7-action-jsonld-validation.json` is the corpus's own canonical R7 action serialization. An action shaped exactly as it prescribes carries its quality signal under `quality_score` — a **third** undefined key — and `git grep 'quality_score'` finds **no reader anywhere** in `web4-standard/`, `hub/` or `web4-core/`.

**Denominator.** Across every JSON artifact under `web4-standard/`, exactly **2** publish an action `result.output` carrying a quality signal, and they **disagree on the key name**: `test-vectors/reputation/reputation-operations.json` (`quality` *and* `accuracy`) and `test-vectors/schema-validation/r7-action-jsonld-validation.json` (`quality_score`). The reputation trigger can read exactly one of the three names in use.

**DIRECTION PROVED — and it convicts this lineage.**

| limb | commit | date |
|---|---|---|
| both SDK reads (`:106` and `:181`) + `rep-001`'s dual key | `740f21de` (#19, module genesis) | 2026-03-16 |
| §5's `accuracy` fallback written into the standard | `00803b03` — **C45 remediation** | **2026-06-10** |
| §4's `output.quality` / missing→0.0 clause written into the standard | `15be0743` — **C85 remediation** | **2026-06-22** |

The SDK shipped both reads in one commit, together with the one input that cannot distinguish them. The two *spec* clauses were then written in by **this lineage's own two remediations, twelve days apart**, in that order. C84's finding SDK-4 asked for the clause to be stated "in **§4/§5**"; C85 placed it in §4 only and never swept §5, where C45 had already installed the contradicting read.

**Why ten passes missed it.** `docs/audits/C123-reputation-computation-3rd-delta-2026-07-01.md:71` walks `analyze_factors` L182-183 and `matches()` L104-107 back to back in the SDK and ticks "All ✓"; `:54` cites L292 and L460 **in a single clause** and adjudicates them "distinct" — on the *threshold* axis only, never the key vocabulary. The falsifier was in the predecessor's hands (v52).

**Novelty — the absence claim, with its matcher published.** Matcher: `grep -c 'quality'` / `grep -c 'accuracy'` over all 13 lineage members, plus `grep -rn 'quality_score'` over `docs/audits/` and `web4-standard/docs/`. Prior art found and **off-predicate**: C44 **B-L4** (`:155-159`) charged the *threshold value* (0.95 vs SDK 0.5); C84 **SDK-4** (`:96-98`) charged the *comparator* being unspecified — and is the origin of the very sentence at `:292`; C156 **INFO-2** (`:109`) deflated the `quality_threshold: 0.0` edge. `quality_score` returns **0 hits** across both audit trees. No pass charged the **key vocabulary**.

**Disposition: LATENT ⇒ MEDIUM.** No artifact in `web4-standard/` publishes an `accuracy`-only or `quality_score`-only output *to the reputation engine* today, so nothing is currently mis-scored (same disposition class as C352-N1). It is MED rather than LOW because the failure is **silent**: `evaluate()` returns `None`, which is byte-identical to the legitimate "no rules triggered" outcome the standard blesses at `:420` and vector `rep-002` asserts. A reputation system that drops a delta indistinguishably from declining to emit one has no surface on which the drop can be noticed.

**Rescue readings, pre-killed.**
- *"`quality` is canonical; §5's fallback is merely defensive."* **Dead** — no schema defines either key (evidence above), and `r6-framework.md:198-202`'s `Result.output` example uses `data`/`hash`/`format`.
- *"The gate is strict by design; factors are heuristic and only consumed via triggered rules, disclosed at `:514-517`."* **Defeats arm C's engine-path reading and is conceded above.** It does not reach the key-resolution divergence: `analyze_factors` is a §5 spec-level function and a public SDK export, and it does not touch arm D at all.

**Routing — three addressees, jointly.** The remedy forks: **(a)** widen §4/`matches()` to accept `accuracy`; **(b)** narrow §5/`analyze_factors` to `quality` only — note this also invalidates `:572`'s gloss, which narrates the worked example in *accuracy* vocabulary; **(c)** define a normative output-quality key in `r7-action-jsonld.schema.json` and make all three sites conform. (a) and (b) change a **released** SDK's conformance behaviour in opposite directions. Route to **standard editor** + **SDK owner** + **`r7-action` schema owner** — the third addressee follows from the killed rescue. A spec-only fix that leaves the SDK divergent is C350-N1's mechanism, which C352's guard 1 already named.

### C392-N2 (LOW, routes with N1) — the conformance vector that exercises reputation does not exercise key resolution

The corpus has **two** executed reputation vector sets, and **neither can distinguish the two reads** — for different structural reasons, which is why stating only one of them would be misleading:

1. `test-vectors/reputation/reputation-operations.json` → `rep-001`, run by `tests/test_reputation.py::TestVectors::test_rep001_rule_triggered_positive`. Sets **both** keys to `0.97` (`:15`), so the reads are indistinguishable by construction. It also passes `factors=` explicitly from the vector (`test_reputation.py:713-714`), so `analyze_factors` is **never called** on this path.
2. `testing/conformance/r6-r7-actions.json` → `r7-rep-001`, run by `tests/test_conformance.py::TestR7Conformance::test_positive_reputation` (**passes**, not xfail — `-k positive_reputation` → `1 passed`). It calls `R7Action.compute_reputation(quality=inp["quality"])` at `r6.py:794-796`, which takes quality as an **explicit float parameter and never reads `result.output` at all** — a *third* convention for where output quality lives, and the one the conformance suite actually exercises. The spec documents no such function; §5 names `compute_reputation_delta`, a different signature.

**Measured, not asserted**: mutating `rep-001`'s `result_output` to `{"accuracy": 0.97}` (a plausible value, not a sentinel — it is precisely the shape §5's fallback exists for) **is caught**: `1 failed, 44 passed`, at `test_reputation.py:717` `assert delta is not None`. Mutating the fixture at `:63` the same way is also caught: `4 failed, 41 passed`. Both reverted; tree verified clean.

So the honest claim is **not** "no test can see it." The catching assert is a **reachability** assert — it fires because no delta was produced. **Nothing in the corpus asserts which reading is correct.** The tests pin the SDK's current behaviour under an input that satisfies both readings; they do not adjudicate the contradiction. That is what makes this a finding about the *standard* rather than about test coverage.

### C392-N3 (INFO, instrument — re-raised, NOT re-charged) — three consecutive passes have left forks on the same `$defs` block

C312-N1 and C352-N1 both fork on `$defs.witness_attestation` in `r7-action-jsonld.schema.json`. Re-measured at HEAD (§A.1, §A.2): **neither has been answered, no partial application, exhibits reproduce byte-for-byte.** C352 pre-registered that a second consecutive unanswered fork "is itself the signal"; this is the **third** pass to measure it and the second to report it unanswered. Per v55, the instrument rather than the row is now the finding: **two standing forks on one schema block across three passes is a routing failure, not a backlog.** Not re-charged as new — recorded so the count is on the record, and escalated in §G.

### C392-N4 (INFO, delivery — v36/v40 channel measurement) — pre-registered null on §7, and the orphan census

**Pre-registered null, executed.** §7's worked example (`:729-745`) was run against the SDK rather than read:

| §7 claim | asserted | measured |
|---|---|---|
| role never acted in → neutral baseline (`:742`) | `0.50` | **0.5** |
| analyst with sustained positive training deltas (`:736`) | `> 0.5` | **0.518** (5 × +0.018) |
| cross-role isolation ("same entity, different roles") | implied | **holds** — surgeon still 0.5 after analyst activity |
| decay keying + constants (`:753-778`) | `(entity, role)`, 30 d grace, −0.01/mo, ×1.5 > 6 mo, cap −0.5 | **`ReputationStore.inactivity_decay` matches every constant** |

**§7 is clean.** Recording the negative is what makes the other sections' positives interpretable.

**Orphan census** (from §B.2's residue): 13 of 82 residue members have never been cited by any audit — `EXECUTIVE_SUMMARY.md`, `R6_TENSOR_GUIDE.md`, `RELATIONSHIP_GUIDE.md`, `T3V3_PRIVACY_GOVERNANCE.md`, `SPATIAL_WEB_INTEGRATION.md`, `NOVA_FURTHER_REVIEW_SUMMARY.md`, `research/standards_analysis.md`, `test-vectors/r6/action-operations.json`, and 5 SDK test/impl modules (`test_deserialize.py`, `test_lct_roundtrip.py`, `test_mcp_process_action.py`, `test_process_action_outcome.py`, `web4/deserialize.py`). `R6_TENSOR_GUIDE.md` is the one this pass opened; it publishes a **fourth** placement of the quality signal (`result.metrics.quality_score`, `:138`, distinct from `output`), corroborating N1's class without being separately charged.

---

## §D — Refuted this pass, do NOT resurrect

1. **"The same module simultaneously scores the action high-accuracy and rejects it" (engine path).** Refuted — `evaluate()` short-circuits before `analyze_factors`; disclosed at `:514-517`. Survives only on the public standalone surface, and is stated that way in N1.
2. **`R6_TENSOR_GUIDE.md:31`'s `quality_threshold: 0.85` as a fifth divergent trigger.** Refuted — it sits under `rules.constraints`, which is R6 rules semantics, not reputation `trigger_conditions`. Same token, different concept.
3. **`test_r6.py:807`/`:1044` `factor="accuracy"` and `r7-framework.md:722` `model_accuracy` as factor-vocabulary regressions of C44 B-L1 / C84 INT-1.** Refuted — factor names are free-form strings matched against a rule's own modifier conditions; a different rule instance may legitimately use a different vocabulary. Distinct from the ratified `high_accuracy` convention and from the standing outbound `r7-§1.7-stale-factor` row (`r7-framework.md:294`, a different locus and a different token).
4. **§7 decay discontinuity at exactly 6 months** (−0.06 → −0.09). Refuted as a defect — disclosed at `:773` ("Decay accelerates after 6 months") and SDK-exact.

---

## §E — The instrument (built by capture, not by recall)

### E.1 — Every path token, resolved as written
All **18** line cites in this document were verified by `sed -n "${N}p"` at HEAD and printed alongside their content before drafting: `reputation-computation.md` `:251 :292 :420 :523 :524 :525 :568 :572 :589`, `reputation.py` `:104 :106 :107 :181 :182`, `test_reputation.py` `:63 :717`, `reputation-operations.json` `:15 :27`. All resolve exactly. Subsequently added cites (`:514-517`, `:657-670`, `reputation.py:45 :237-240 :249-253`, `r6.py:794-796`, `r7-action-jsonld-validation.json:121`, `R6_TENSOR_GUIDE.md:31 :138`, `r6-framework.md:198-202`) were each read in place.

### E.2 — Every gate cell carries the command that produced it
Window: `git log --oneline 927eecad..HEAD [-- web4-standard/] | wc -l`. Schemas: `git ls-files 'web4-standard/schemas/**' | grep -c '\.json$'`. Residue: `comm -23` of two `git grep -li` runs with the bound stated **before** running. Denominator for output keys: a JSON walk over `web4-standard/**/*.json` collecting every key under an `output`/`result_output` object — published in N1, not summarized.

### E.3 — Machine checks, reproducible
Exhibit script is self-contained (SDK public API only) and run from `web4-standard/implementation/sdk`. Mutations applied to a copy, run, reverted, and `git status --porcelain` confirmed empty. Baselines captured **before** each mutation, never after.

### E.4 — Counts re-derived, never inherited
window 28 / 0 · schemas 24 (glob trap: 12) · lineage 13 · residue 82 of 95 − 13 · orphans 13 · `quality_threshold` sites in `web4-standard/` = 11 hits across 6 files · quality-bearing `output` objects = 2 of 2 disagreeing · suites 2750+5x / 45 / 34+5x.

---

## §F — This pass's own errors

1. **Wrong SDK API in the first exhibit** — used `ReputationEngine(rules=[...])` and `compute_delta()`; the real API is `add_rule()` / `evaluate()`. Caught by running it, in under a minute. Mechanical.
1b. **One line cite off by two** — `test_reputation.py:715` (blank) for the vector's explicit `factors=`; correct locus `:713-714`. Caught by §E.1's resolve-every-token pass, before publication. This is the standing path-token hazard firing on my own citation, and it is why every cite added *after* the first sweep was re-resolved rather than trusted.
2. **Published headline was wrong and had to be re-based.** The proposal's "two contradictory readings" framing was closable by a skeptic: each function's semantics is *individually* disclosed. The policy reviewer supplied the narrower, sharper claim actually published here (a normative condition over a key no schema defines).
3. **SUBSTANTIVE — arm C's punch line was false as proposed.** I asserted the engine "still emits `high_accuracy`" while rejecting the action. It does not: `evaluate()` short-circuits at `reputation.py:249-250` before `analyze_factors` at `:252-253`, and `:514-517` discloses it. My exhibit had obtained those factors by calling `analyze_factors` **directly** and I read the result as an engine behaviour. Caught by the policy reviewer, re-verified by me, and the claim is now scoped to the public standalone surface. *Reading the call order of the function I was executing would have caught this before the reviewer did.*
4. **SUBSTANTIVE — "the only evaluated corpus input" was false.** A second executed vector set exists (`testing/conformance/r6-r7-actions.json` → `r7-rep-001`) and a third read convention with it (`r6.py:794`). Caught by the policy reviewer. My sweep had looked for consumers of the *reputation* vectors and stopped there; the conformance tree indexes its vectors under a different name.
5. **Nearly claimed the suite was blind.** The draft asserted no test could see the divergence. The mutation runs **falsified my own claim** — both mutations are caught. The surviving claim is narrower and is the one published in N2: the assert is a reachability assert, and nothing adjudicates *which* reading is correct.
6. Reviewer slip noted for the record, not adopted: it reported `test_conformance.py` as "49 passed"; the file is **39 collected → 34 passed, 5 xfailed**. Its substantive claim — that `r7-rep-001` executes and is not xfail — is correct and was verified independently (`-k positive_reputation` → `1 passed`).

**Policy review = 12th consecutive falsification of a central premise or headline** (C354, C356, C364, C366, C372, C378, C390, and now C392, where it took three cells and the headline).

---

## §G — Guards for C432 (next reputation-computation delta)

1. **Check whether N1 was answered, and by WHICH ARM.** If §4 was widened to accept `accuracy`, verify `matches()` moved too and that `rep-001` still passes; if §5 was narrowed, verify `:572`'s accuracy-vocabulary gloss was swept with it — that gloss is the sentence a partial fix leaves stale. If a normative key was minted in `r7-action-jsonld.schema.json`, verify **all three** publishing sites conform, including `r7-action-jsonld-validation.json:121`.
2. **`quality_score` is now a tracked token.** It had 0 hits in both audit trees before this pass. If it is still unread by any code at C432, that is a second measurement of the same routing failure, and the *instrument* becomes the finding (v55).
3. **N3 escalation.** Two standing forks on one `$defs` block will be at **four** consecutive passes. If still unanswered, do not re-measure and re-file — report it as a routing failure against the receiver's ledger and stop re-charging the rows (v38: probe the LEDGER, not the spec files).
4. **§7 is a discharged null** — executed against the SDK this pass, all four claims measured clean. Do not re-run it as if it were open; re-run only if `reputation.py`'s `ReputationStore` moves.
5. **13 orphans are enumerated in N4.** They are the residue's live edge. Opening one is cheap and it is what produced this pass's N2 arm; opening the same one twice is not.
6. **Do NOT re-charge** anything in §D. In particular the `factor="accuracy"` / `model_accuracy` sites: they are free-form rule vocabulary, already adjudicated here.
7. **Re-derive the lineage count** — it will be 14 at C432 under the inclusive rule stated in this header. Never inherit it.

---

## Accountability self-audit

```
surface: C392 audit document   act: publish an audit finding + route a remedy to three owners
S: low/reversible [construct: docs/audits/ document; ZERO mutation of web4-standard/; no code path created]
R: n/a [construct: no caller-driven surface created or changed]
W: pass [construct: authored on worker branch worker/web4-20260815-000000, PR-gated; merge authority is the reviewer track, not this session]
O: pass [construct: policy review (Step 4) completed and its three falsifications applied BEFORE the document was written — no finding was published on the un-reviewed premise]
A: pass [construct: §E instrument + §F own-errors committed in the same document as the findings; every count carries the command that produced it]
V: present [construct: "route, do not self-apply" — the forking remedy is escalated to standard editor + SDK owner + r7-action schema owner rather than applied, because two arms change a RELEASED SDK's conformance behaviour in opposite directions]
verdict: PASS
```
