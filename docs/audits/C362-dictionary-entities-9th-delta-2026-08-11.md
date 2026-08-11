# C362 — `dictionary-entities.md`, 9th delta audit

**Date**: 2026-08-11 · **Slot**: `web4-20260811-120000` · **Rotation**: C322 + 40
**Target**: `web4-standard/core-spec/dictionary-entities.md` (603 L, blob `8e06a23c`)
**Mutation**: ZERO. This pass routes; it does not apply.

**Headline** — the SDK module that implements this spec publishes a conformance claim naming a
test-vector file, and **nothing in the repository loads that file**. Executed by hand, all **5**
vectors PASS, so the claim is *true* — and unguarded. The measurement that makes it a finding
rather than an anecdote is the denominator: of the SDK's **17** `Validated against:` claims,
**15 are backed** by a loader and **2 are not** — this one and `federation.py`'s.

---

## §A — Freeze proof (collapsed, third application)

Licensed explicitly by the C322 §E guard. The 9 C53 remediations are **not** re-derived a ninth
time; they hold by construction because the blob has not moved.

| artifact | blob @HEAD | expected (C322) | last commit |
|---|---|---|---|
| `core-spec/dictionary-entities.md` | `8e06a23c` | `8e06a23c` | 2026-06-13 `95d20919` |
| `protocols/web4-dictionary-entities.md` (sister) | `b28d8f9e` | `b28d8f9e` | 2025-09-11 `80f53a63` |
| `implementation/sdk/web4/dictionary.py` | `edd97183` | `edd97183` | 2026-04-17 `759eaefa` |
| `implementation/sdk/tests/test_dictionary.py` | `d8f71420` | `d8f71420` | 2026-04-17 `759eaefa` |
| `schemas/dictionary-jsonld.schema.json` | `f32292dd` | `f32292dd` | 2026-03-23 `dfc71516` |
| `schemas/contexts/dictionary.jsonld` | `5f803c97` | `5f803c97` | 2026-03-23 `dfc71516` |
| `test-vectors/dictionary/dictionary-operations.json` | `55d58bf6` | `55d58bf6` | 2026-03-14 `df1fca78` |
| `test-vectors/schema-validation/dictionary-jsonld-validation.json` | `f5d95664` | *see note* | 2026-03-25 `f39252d4` |
| `implementation/sdk/web4/schema_registry.json` | `ee9d5f40` | `ee9d5f40` | — |

Target byte-frozen **59 days across 9 passes**. All nine artifacts unchanged.

**Instrument correction against my own lineage.** C322 records the schema-validation vectors as
`f39252d4`. That is the **commit** hash (#80); the blob is `f5d95664`. Comparing the guard's value
against `git rev-parse HEAD:<path>` reads as a CHANGE on first pass. Only one commit has ever
touched the file, so it is genuinely frozen. One cell of C322's blob table is a commit hash in a
blob column — recorded here so C402 does not re-raise the false alarm.

### Window

```
git log --oneline 36602276..HEAD                                    -> 51
git log --oneline 36602276..HEAD -- web4-standard/                  ->  1   (afd04623, #678)
git log --oneline 36602276..HEAD -- <9 dictionary artifacts>        ->  0
```

**Base correction (mine).** I first measured the window from `5b206d52` (the C322 *rev1* commit)
and published **55**. `5b206d52` is **not an ancestor of HEAD** — it is a pre-merge commit on the
PR branch, so `5b206d52..HEAD` counts four commits that are not in the window at all. The correct
base is the merged `36602276`, and the window is **51**. The load-bearing cells (1 and 0) were
unaffected, which is exactly why the wrong total survived a first reading. Every cell above now
carries the command that produced it.

---

## §B — The one measurement no pass in this lineage has taken

Eight passes asked whether dictionary's artifacts are **correct**. C322 swept the five
machine-readable ones CLEAN and recorded the operations vector as *"5 vectors (`dict-001`…`dict-005`),
`spec_ref` resolves, suite/version well-formed."* That is a well-formedness predicate. **No pass has
asked whether anything consumes them** (v45: a green unit is evidence about a function, never a
system; where an artifact is named as a conformance basis, the caller count *is* the conformance
measurement).

### B.1 — The claim

`implementation/sdk/web4/dictionary.py:20`, closing the module docstring that also enumerates the
five §9.1 MUSTs:

```
Validated against: web4-standard/test-vectors/dictionary/dictionary-operations.json
```

### B.2 — The consumer sweep

```
grep -rnF "dictionary-operations.json" --include=*.py .        # excl. archive/, target/, sdk/web4/
```
⇒ **0**. The only two non-audit mentions anywhere in the repo are *prose restatements of the same
claim*: `dictionary.py:20` itself and `implementation/sdk/CHANGELOG.md:726`
(*"Validated against `test-vectors/dictionary/dictionary-operations.json`"*).

`test_dictionary.py` — one of this lineage's four tracked mirrors, byte-frozen since 2026-04-17 —
is **629 lines / 128 assertions**, all green, and contains **no** occurrence of `load_vectors`,
`test-vectors`, or `VECTORS`. The module's own test file does not touch the artifact the module
names as its conformance basis.

### B.3 — The denominator (v40), corrected upward on review

The SDK carries **17** `Validated against:` claims. My first instrument split them into 9
"file-form" (naming a `.json`) and 8 "directory-form" (naming a directory), and measured only the
9 — because a bare directory basename (`entity/`, `lct/`, `security/`) is a non-distinctive matcher
that forked onto unrelated files (v39: *a bare basename is a fork*). That exclusion was **convenient,
not necessary**: each directory-form claim resolves to a small enumerable file set, and matching on
the *contained filenames* is distinctive. Re-derived over all 17:

| claim form | modules | backed by a loader |
|---|---|---|
| file-form (names a `.json`) | 9 | **7** |
| directory-form (names a dir) | 8 | **7** (+ `lct/` partial, 1 of its 5 files) |
| **total** | **17** | **15** |

**Unbacked: exactly 2 — `dictionary.py:20` and `federation.py:26`** (`test-vectors/federation/sal-governance.json`,
likewise 0 refs). Correcting the denominator *strengthened* the finding (2-of-17 is a sharper outlier
than 2-of-9), which per **v41** means the original was guessed rather than derived. Stated plainly
rather than quietly improved.

Backing sites, for audit: `test_acp.py:783`, `test_vectors.py:172` (atp) and `:56` (t3v3),
`test_binding.py:646`, `test_metabolic.py:442`, `test_mrh.py:301`, `test_society.py:808`,
`test_capability.py:454`, `test_mcp.py:31`, `test_protocol.py:43`.

### B.4 — The loader class the matcher structurally cannot see

A filename grep cannot detect a loader that enumerates a directory. Five `validate_vectors.py`
copies exist; three are byte-identical (`c5c9e5bf`, 180 L — `web4-standard/`,
`web4-standard/tools/`, `web4-standard/testing/validator/`) and **do** take `--vectors-dir` and
`os.walk` recursively. They would reach `dictionary-operations.json` without ever naming it.

The finding survives, but by **execution, not by my matcher** — the walk dispatches
`if is_jose_vector(p) … elif is_cose_vector(p) … else: continue`, and a dictionary vector falls
through the `continue`. Run rather than read:

```
python3 tools/validate_vectors.py --vectors-dir test-vectors/dictionary   -> no output, exit 0
python3 tools/validate_vectors.py --vectors-dir test-vectors             -> no output
```

It processes **zero** vectors over the entire tree, so this loader class backs **none** of the 17
claims. The fourth copy (`test-vectors/validate_vectors.py`, `5259d473`, 423 L) is a different
program whose suite list is hardcoded: `suites = sys.argv[1:] if len(sys.argv) > 1 else ["t3v3", "atp"]`
— it knows two suites, neither of them dictionary.

### B.5 — The deflation (v42), executed

The claim being unguarded does not make it false. All five vectors were executed by hand against
the SDK at HEAD:

| vector | §  | result |
|---|---|---|
| `dict-001` | §4.3 | `cumulative_confidence` 0.874, `degradation` 0.126, `length` 2 — **PASS** (tol 0.001) |
| `dict-002` | §6.2 | `selection_score` 0.86 — **PASS** |
| `dict-003` | §4.3 | 0.7866 / 0.2134 / 3 / `is_acceptable` false — **PASS** |
| `dict-004` | §2.1–2.2 | `binding.entity_type` `dictionary`, `mrh.bound` both domains, `policy.capabilities` all three, version `2.3.1` — **PASS** |
| `dict-005` | §5.1 | 0.5 → 0.49672 → 0.5; decreases then increases — **PASS** |

**5/5 PASS.** The conformance claim is **TRUE but UNGUARDED**. This retires the stronger reading —
this is *not* C52-B16's shape (*"one side's claim of conformance is false today"*). It is a missing
guard, and is typed accordingly in §D.

Three of my five first-run "FAILURES" were my harness guessing constructor signatures
(`ChainStep` positional args; `FeedbackRecord(quality=…)`, which does not exist; omitting
`version=` from `create()`). Reading the real API turned all three into passes. A harness error
published as a spec defect would have been the whole finding, inverted.

### B.6 — The v45 disclosure check, executed rather than argued

v45 warns that the corpus phases mechanisms in deliberately and says so at the point of use;
charging disclosed inertness is charging its discipline. So the disclosure is **measured**:

```
grep -cniE "TODO|planned|not yet|future|phase|deferred|placeholder|aspiration|will be" \
  web4/dictionary.py  test-vectors/dictionary/dictionary-operations.json
```
⇒ `dictionary.py` **1**, vector file **0**. The single hit is **`from __future__ import annotations`**
at `:23` — a false positive of my own matcher. True disclosure count: **0 / 0**.

`Validated against:` is unqualified present-tense indicative. It is the opposite of the corpus's
disclosed-phasing idiom (`starter-law.yaml:120-121`, `hub-law-schema.md:44`): it *asserts* the thing
a disclosure would qualify. **No v45 defense is available.**

---

## §C — Carry ledger (per-row table; **do not convert to prose** — that conversion is C322-N1)

| id | type | locus | status at C362 | evidence |
|---|---|---|---|---|
| **C322-I2** | INFO, SDK track | `TestBundledRegistry` | **HOLDS — no regression, no fix** | 4 tests: `test_registry_loads`, `test_registry_contains_all_schemas`, `test_registry_schemas_have_schema_key`, `test_get_schema_uses_registry`. Still **no content-equality assertion** against `schemas/`. |
| **C322-N3** | LOW, SDK track | `validation.py:219-224` | **HOLDS — inversion unchanged** | `# Try bundled registry first` still precedes the directory branch; `:8-12` still documents `WEB4_SCHEMA_DIR` as priority **1**. Docs and code still contradict at HEAD. |
| **C282-N1** | MED, CBP + SDK-conditional | `dictionary.py:771-773` | **DOES NOT ESCALATE** (same as C322) | `.get(…, 1.0)` × 3 unchanged; **and** #580 still reads `Status: proposal, for fleet review` (`4665a430`, unmoved since 2026-07-27). Escalation requires **both**; the second remains false. |
| **C322-N2** | INFO, test-vector owner | `validate_schema_vectors.py:120-123` | **HOLDS** | `error_kinds = {e.validator for e in errors}` still computed for the `--verbose` message only; no comparison against the declared `error_kind`. |
| **C52-B15/B16/B17** | MED ×3, SDK bundle | §4.1/§4.3/§2.2 vs SDK | **STAND** | see §D.2 |
| **C52-B24** | LOW, SDK bundle | §6.2 vs `dictionary_selection_score` | **STANDS** | see §D.2 |
| **C52-B25** | INFO | `AMBIGUITY_GATE`/`VERSION_BUMP_DELTA` | **STANDS** | unmoved (target frozen) |
| **C52-B9, C17-M1/H2/M4/M6, B26, C64-B7** | operator DESIGN-Q | — | **OPEN, unchanged** | target frozen ⇒ hold by construction |
| **C322-N1** | LOW, ledger | this table | **DISCHARGED by construction** | §C is a per-row table with a disposition column, as C322 §E requires |
| **B-D1** | flagship | SSOT inversion | **UNANSWERED** | operator-owned; not re-derived here |

---

## §D — Routing (routes, never applies)

### D.1 — C362-N1 [INFO] · routed to the **SDK track** · sibling of C322-I2 and C322-N3

> `web4/dictionary.py:20` publishes `Validated against: <path>` for a vector file that no code in
> the repository loads. The five vectors pass when executed by hand (§B.5), so no fault is present
> today; what is absent is any mechanism that would notice if one appeared. 2 of the SDK's 17
> `Validated against:` claims are in this state.

**Typed INFO, not LOW, on this lineage's own precedent.** C322-I2 — five days old, same lineage,
ratified — is the identical evidentiary posture: guard absent, objects verified equal today
(12/12 identical), no harmed consumer, routed. "5/5 PASS" is "12/12 identical." Grading this LOW
would be inflation against my own precedent, and would make a thin delta look thicker than it is.

**Received as a set, per v37.** The SDK track now holds **three** rows of one shape, all from this
lineage, all unapplied: a bundled registry with no content gate (I2), a documented resolution order
the code inverts (N3), and a published conformance claim with no runner (N1). The pattern is
*the SDK's assertions about its own artifacts are unguarded*; delivering it as a three-row pattern
is worth more than a third isolated INFO.

**Sibling named, deliberately NOT charged.** `federation.py:26` / `sal-governance.json` is in the
identical state. Per the **C120/C121 key signal** the MUST-vs-reference-impl class is DOC-SPECIFIC
and must be cleared file-by-file — batching a corpus-wide sweep is the failure mode. It is named
here so the federation lineage can pick it up at its own slot; it is **not** counted in this pass's
yield.

### D.2 — Killed candidates (v44: novelty is an absence claim)

| candidate | killed by | matcher that found the precedent |
|---|---|---|
| §6.2 scores **five** inputs incl. `latency`; SDK's `dictionary_selection_score` takes **four** and hardcodes 0.4/0.3/0.2/0.1 | **C52-B24** (2026-06-12), verbatim, still standing | `grep -rn "latency" docs/audits/` — the **domain's** word, not my paraphrase ("arity", "signature", "five-factor" all returned nothing) |
| spec `dictionary_spec`/`compression_profile`/`entity_type` vs schema+SDK `spec`/`compression`/`@type` | **C52-B15/B16/B17** | `sed -n '/C52-B16/,/^####/p'` on the C52 doc |
| 4 of 8 ```json fences do not parse | **C158** corpus-wide INFO (51/148 corpus) — all 4 failures are `//` comments | all 8 recovered after a JSONC strip (v43: never discard the blocks your parser cannot read) |

Both C52 rows were found only because the search used the domain expert's vocabulary. Publishing
them as *killed* is the point: a false novelty would have stolen C52's credit and discarded the
ratified routing that already exists for them.

### D.3 — C362-NEG1 [negative] · routed **corpus-wide** as a standing do-not-re-raise row

Candidate, tested and **refuted before charging**: *"the spec's own JSON examples do not validate
against its own JSON-LD schema."*

True of dictionary in isolation — **8 of 8** examples INVALID. §2.2 *"Dictionary LCT Structure"*,
the canonical example, shares exactly **one** property (`lct_id`) with `$defs/DictionaryEntity`,
omits 7 of its 8 `required`, and trips `additionalProperties: false` with 6 unexpected keys.

**But the corpus baseline refutes the dictionary-specific typing.** One uniform instrument
(fence-extract → JSONC-strip → `Draft202012Validator` against the paired `*-jsonld.schema.json`)
over the **8** core-spec docs that have a paired JSON-LD schema:

| pair | json fences | parsed | declare `@context`/`@type` | valid |
|---|---|---|---|---|
| acp / acp-framework | 7 | 7 | 0 | 0 |
| atp / atp-adp-cycle | 6 | 5 | 0 | 0 |
| capability / lct-capability-levels | 12 | 12 | 0 | 0 |
| **dictionary / dictionary-entities** | 8 | 7 | 0 | **0** |
| entity / entity-types | 7 | 5 | 1 | 0 |
| lct / LCT-linked-context-token | 4 | 2 | 1 | 0 |
| r7-action / r7-framework | 13 | 7 | 0 | 0 |
| t3v3 / t3-v3-tensors | 3 | 3 | 0 | 0 |
| **total** | 60 | **48** | **2** | **0** |

**0 of 48**, and only **2 of 48** examples even declare the `@context`/`@type` that every one of
these schemas makes `required`. Dictionary is indistinguishable from the corpus. This is the same
shape as the already-refuted **C282-R1** (ontology predicates, 74% corpus-wide) — a corpus-level
fact about the relationship between the prose-spec layer and the JSON-LD layer, owned by neither
this file nor this lineage.

**NOT charged.** Routed corpus-wide rather than buried here, because the next presence, atp, or
r7 pass will otherwise re-discover it and be tempted to charge it as *their* file's defect. If the
standard's owner wants the two layers reconciled that is a standards-level decision, not an audit
finding.

---

## §E — Guard for the next dictionary delta (C402, or on event trigger)

- Target frozen at `8e06a23c` since `95d20919`; nine artifacts as listed in §A. If unchanged, §A is
  a freeze proof — **do not re-derive the 9 C53 remediations a tenth time.**
- **§C stays a per-row table.** Converting it to prose *is* C322-N1.
- **The C322 blob table has a commit hash (`f39252d4`) in the blob cell for
  `dictionary-jsonld-validation.json`.** True blob `f5d95664`. Do not re-raise as a change.
- **The window base is the MERGED commit.** `36602276`, not the PR-branch commit `5b206d52` —
  verify with `git merge-base --is-ancestor <base> HEAD` before publishing a window count.
- **The five machine-readable artifacts remain in the swept set and may not contract** (v8).
  They were swept clean at C322 and **unchanged** here — check only whether they *changed*.
- **C362-N1 regression:** did `test_dictionary.py` gain a loader for
  `test-vectors/dictionary/dictionary-operations.json`? One grep:
  `grep -c "dictionary-operations.json" web4-standard/implementation/sdk/tests/*.py`. At C362: **0**.
  If a runner lands, re-execute all 5 (they PASS at C362 — a new failure would be a real regression).
- **C322-I2 / C322-N3 / C322-N2 / C282-N1 regressions:** all four **HOLD unchanged** at C362, with
  the probes recorded in §C. Re-run the same four; C282-N1 still needs **both** limbs.
- **Do not re-open:** C282's R-1 and R-2; the `hub/` gate (NEGATIVE on subject matter);
  the `web4-core/.../trust/attestation/` false mirror; Effector/W4IP; LCT §1.2; **and now
  C362-NEG1** (spec examples vs JSON-LD schema — 0 of 48 corpus-wide, not dictionary's).
- **Do not batch** the 15 backed / 2 unbacked `Validated against:` claims into a corpus sweep
  (C120/C121). `federation.py:26` is the federation lineage's row.
- `protocols/` cluster remains gated by **D0** (operator-unanswered). Do not re-audit.

---

## §F — Method lesson

**A conformance claim is an absence claim about its own enforcement.**

Eight passes verified that dictionary's artifacts are *correct*. Correctness was never the exposed
surface. The module docstring asserts validation against a named file; the assertion is true; and
the mechanism that would keep it true does not exist. Nothing in a green test suite can report
this, because the suite's 128 assertions are evidence about functions and the claim is about a
system (**v45**).

Three of this pass's four candidate findings died to precedent or to a baseline, and the survivor
deflated from "the claim is false" to "the claim is unenforced" the moment I stopped reading and
ran it (**v42**, **v43**). What made the survivor publishable was not its severity but its
**denominator** — and I had to be told that my first denominator (2 of 9) was gerrymandered by an
exclusion I had justified as necessary when it was merely convenient. The corrected figure, 2 of
17, is *sharper*. **When correcting your own cite strengthens your argument, the original was
guessed** (**v41**) — that rule caught me twice this pass, here and on the window base.

**Corollary for the next auditor: run your own instrument against your own output before
publishing it.** My disclosure grep returned 1 hit and the hit was `from __future__ import
annotations`. My first vector run returned 3 failures and all 3 were my harness. My first window
count was 55 against a base that is not an ancestor of HEAD. Every one of those would have been a
published falsehood, and each was caught by the same cheap move: execute it again, and look at
what came back.

---

## §G — Post-write re-run (v17)

Re-executed after writing, against HEAD, in a clean shell:

- `git rev-parse HEAD:web4-standard/core-spec/dictionary-entities.md` → `8e06a23c…` ✓
- `git log --oneline 36602276..HEAD | wc -l` → **51** ✓ (and `git merge-base --is-ancestor 36602276 HEAD` → 0) ✓
- `grep -rnF "dictionary-operations.json" --include=*.py .` (excl. `archive/`, `target/`, `sdk/web4/`) → **0** ✓
- 17 `Validated against:` claims; **15** backed, **2** unbacked (`dictionary.py`, `federation.py`) ✓
- 5 vectors re-executed → **5/5 PASS** ✓
- corpus example-vs-schema baseline → **0 of 48 valid, 2 of 48 declaring `@context`** ✓
- four carried regressions (C322-I2, C322-N3, C322-N2, C282-N1) → all **HOLD**, none escalates ✓

No cell moved. Zero files mutated outside this document.
