# C402 — `dictionary-entities.md`, 10th delta

**Date**: 2026-08-18 · **Slot**: `web4-20260818-000000` · **Target**:
`web4-standard/core-spec/dictionary-entities.md` · **Lineage**: `dictionary-entities-internal-consistency-2026-05-27`
(non-C-numbered member, per the standing enumeration rule) → C52 → C94 → C132 → C166 → C204 → C242 →
C282 → C322 → C362 → **C402**.

**Output shape**: doc-only. **Zero mutation of any audited artifact.** Every mutation in this document
was applied to a working copy and reverted; `git status --porcelain` is empty except for this file.

---

## §A — Freeze proof (collapsed, fourth application)

Per `C362 §E` and `C322 §E`: the target's blob is unmoved, so the **9 C53 remediations hold by
construction and are not re-derived**.

| artifact | blob at HEAD |
|---|---|
| `core-spec/dictionary-entities.md` | `8e06a23c` |
| `implementation/sdk/web4/dictionary.py` | `edd97183` |
| `implementation/sdk/tests/test_dictionary.py` | `d8f71420` |
| `protocols/web4-dictionary-entities.md` | `b28d8f9e` |
| `schemas/dictionary-jsonld.schema.json` | `f32292dd` |
| `schemas/contexts/dictionary.jsonld` | `5f803c97` |
| `test-vectors/dictionary/dictionary-operations.json` | `55d58bf6` |
| `test-vectors/schema-validation/dictionary-jsonld-validation.json` | `f5d95664` |
| `implementation/sdk/web4/schema_registry.json` | `ee9d5f40` |

All nine paths are prefixed `web4-standard/`. Command (run from the repo root; **the root is part of
the cell**, v65):

```
git rev-parse HEAD:web4-standard/<path>
```

Every hash is **identical to the value C362 published**, with one carried instrument correction
already applied: `dictionary-jsonld-validation.json` is blob **`f5d95664`**, not `f39252d4` — that
figure in C322's table is the **commit** (#80). Do not re-raise it as a change.

**Target**: `8e06a23c`, 603 L, last moved `95d20919` (2026-06-13) ⇒ **66 days, 10 passes byte-frozen**.

### Window

Base = the **MERGED** C362 commit, obtained from the PR rather than from a branch tip:

```
gh pr view 691 --repo dp-web4/web4 --json mergeCommit   # -> c23ce054
git merge-base --is-ancestor c23ce054 HEAD              # -> exit 0
git rev-list --count c23ce054..HEAD                     # -> 27
git rev-list --count c23ce054..HEAD -- web4-standard/   # -> 0
git log --oneline c23ce054..HEAD -- '*dictionary*'      # -> 0
```

**27 commits / 0 in `web4-standard/` / 0 dictionary.** This is the **9th consecutive fire** on this
track with an empty `web4-standard/` window (C400 recorded the 8th). Both delta halves are empty; the
entire yield below comes from machine checks run **before** §A, per the opening sequence.

### §A.1 — Correction to a C362 evidence cell (net-new, process)

`C362:180`, the `C282-N1` row, reads:

> `.get(…, 1.0)` × 3 unchanged; **and** #580 still reads `Status: proposal, for fleet review`
> (**`4665a430`**, unmoved since 2026-07-27).

`4665a430` is **not** #580's commit:

```
git log -1 --format='%h %ci %s' 4665a430
  4665a430 2026-07-27 17:43:10 -0700 proposal: Dictionary becomes a context-mandatory society role (#579)
git log -1 --format='%h %ci %s' 954ee391
  954ee391 2026-07-27 17:43:40 -0700 proposal: Web4 must be resilient to incomplete, malformed and contradicting information (#580)
git log -1 --format=%h -- web4-standard/proposals/resilience-to-incomplete-information.md
  954ee391
```

The two commits are **30 seconds apart** and `C282 §E` listed the #580 (N1) and #579 (N2) probes
adjacently. The row picked up **its sibling's evidence**. The row's *conclusion* is unaffected — the
Status field is independently re-measured below and still reads `proposal` — but the cell has been
wrong for one pass.

This is the **`C400-N2` defect class** (a carry row holding its sibling's evidence) recurring in this
lineage one pass after that class was named. It is filed here rather than charged: the disposition it
supports is correct, and correcting it costs one line.

---

## §B — The three §9.1 MUST arms nobody executed

### B.1 — The row, re-resolved by its PREDICATE (v65)

The predicate originates at `dictionary-entities-internal-consistency-2026-05-27:474`:

> All §9.1 MUST requirements (every Dictionary MUST have a valid LCT; MUST track confidence and
> degradation; MUST be witnessable; evolution MUST be versioned; critical translations MUST require
> ATP stake) are **spec-only — no SDK enforcement exists**.

`C52:225-227` flipped `C17-INFO1` to **CLOSED-INVALID** on **instrument** grounds — its evidence was
`grep -l -i "class.*Dictionary\b"`, which cannot match `DictionaryEntity`. That correction is right.
But `C52:244` then wrote that the predicate is *"now actually answered"*, citing:

> MUST-3 witnessability is SDK-enforced (better than spec pseudocode), MUST-5 stake is not enforced on
> either side (B11).

**Two arms of five.** A row was dispositioned from a proper subset of its arms — `v65b` exactly, and
`v60` (*charge or explicitly carry the other N−1*) one level up.

**Per-arm state, corrected against the record rather than asserted** (policy review falsified two
cells of my first draft here):

| arm | predicate | executed before C402? | where |
|---|---|---|---|
| MUST-1 | every Dictionary has a valid LCT | **spec-internal arm only** | `C94:53-54` (C94-B1) raised §3.2–3.4's illustrative snippets as HIGH and adversarially demoted them. That is a *spec-internal* conformance predicate. The **SDK arm was never run.** |
| MUST-2 | tracks confidence and degradation | **never** | — |
| MUST-3 | translations are witnessable | yes | `C52-B1` — SDK ahead of the spec |
| MUST-4 | evolution is versioned | **constant-absence limb only** | `C52-B25 [INFO]` (`AMBIGUITY_GATE`/`VERSION_BUMP_DELTA` undefined), **STANDS** at `C362:184`. The **behavioural** limb was never run. |
| MUST-5 | critical translations require ATP stake | yes | `C52-B11` — "critical" undefined, OPEN |

Executing MUST-2's SDK arm produced **N1**. Executing MUST-1's SDK arm produced **N3**. MUST-4's
behavioural limb is filed under the standing `C52-B25` row in §C, not as a fresh finding.

### B.2 — N1 [LOW] · `ChainStep.degradation`'s only guard is transformation-invariant

`TranslationChain` carries **four** derived quantities. Three of them —`cumulative_confidence`,
`cumulative_degradation`, `length` — are `@property` in `dictionary.py`, so `from_jsonld` **discards
whatever the wire declared** and recomputes. The fourth, per-step `degradation`, is a **stored field**
taken verbatim from the document.

Executed (`TranslationChain.from_jsonld` on a document declaring `cumulative_confidence: 0.99`,
`cumulative_degradation: 0.01` over steps that multiply to 0.874):

```
schema says valid   : True
declared cum_conf   : 0.99   -> SDK reports 0.874
declared cum_degr   : 0.01   -> SDK reports 0.126
re-emitted doc      : {'cumulative_confidence': 0.874, 'cumulative_degradation': 0.126, 'length': 2}
```

**3 of 4 recomputed, 1 trusted.** That asymmetry is dictionary's own, and it is the severity basis —
*not* "a required field nothing constrains", which is a corpus idiom and dies to one control (see
§B.5).

The relation `degradation = 1 − confidence` is asserted on **three normative surfaces**:

- spec `§4.2` step 7: `degradation = 1.0 - confidence`, and `§4.3`'s wire object shows `0.05`/`0.08`
  against `0.95`/`0.92`;
- `schemas/dictionary-jsonld.schema.json`, `$defs/ChainStep.degradation.description`: *"Semantic loss
  in this step (1 - confidence)."* — and the field is in `required`, under `additionalProperties: false`;
- `dictionary.py` `TranslationResult` docstring: *"degradation: 1 - confidence"*.

**The field is read.** `to_jsonld` emits it and `from_jsonld` ingests it, and mutating the ingest site
*is* caught — by `tests/test_cli.py::TestSelftest` ×3, i.e. `__main__.py`'s
generate → `to_jsonld` → `from_jsonld` → compare loop. That guard is a **round-trip identity check**,
which is invariant under any transformation applied consistently on both sides. **Nothing anywhere
asserts the field's semantics.**

#### Mutation map — 8 sites, each mutated to a plausible in-range wrong value (v59), full suite each time

Baseline: `python3 -m pytest tests/ -q` (from `web4-standard/implementation/sdk`) → **2750 passed,
5 xfailed**.

| # | site | mutation | full suite |
|---|---|---|---|
| A | `add_step` — the value **stored** on a ChainStep | `_clamp(1.0 - confidence)` → `_clamp(confidence)` | **2750 passed — SILENT** |
| B | chain `to_jsonld` — the per-step value **emitted** | `s.degradation` → `0.42` | **2750 passed — SILENT** |
| C | `TranslationResult.from_jsonld` | `doc["degradation"]` → `0.42` | 3 failed (`test_cli.py::TestSelftest` ×3) |
| D | chain `from_jsonld` step ingest | `s["degradation"]` → `0.42` | 3 failed (same) |
| E | `record_translation` generation | `1.0 - confidence` → `confidence` | 1 failed (`test_record_translation`) |
| F | `TranslationResult.to_jsonld` | constant | 1 failed (`test_basic_result_roundtrip`) |
| G | `cumulative_degradation` | constant | 3 failed |
| H | `cumulative_confidence` | `*= step.confidence` → `*= 1.0` | 6 failed |

**A and B are the write and emit sites of the one quantity that has no semantic reader.** They are the
only two silent sites of eight.

#### Vector coverage — matcher published with the number (v64)

Matcher: recursive walk of each vector's `document`, collecting every object that carries **both**
`confidence` and `degradation` as numbers (a top-level-only matcher returns 10 and is the wrong
denominator — policy review caught this).

```
total vectors in dictionary-jsonld-validation.json : 50
vectors with >=1 co-located conf/deg pair          : 17
pairs breaking sum == 1                            : 3  (dict-invalid-013, -014, -022)
   ...of those, BOTH values in [0,1]               : 0
```

All three sum-breakers are caught by `minimum`/`maximum`, i.e. by **range**, never by the relation.
**Zero of 50 vectors present an in-range violating pair.**

### B.3 — N1 corollary: C362-N1's routed fix would not close this

`C362-N1` routed to the SDK track: `dictionary.py:20` claims *"Validated against:
test-vectors/dictionary/dictionary-operations.json"* and nothing loads that file. **Regression
re-run:** `grep -c "dictionary-operations.json" tests/*.py` ⇒ **0** in every file; repo-wide, excluding
`archive/` and the docstring itself, **0**. Still unremediated.

Measured here for the first time: **wiring it up would still be silent under mutations A and B.**

```
dict-001 input steps : [{"source","target","confidence"}, …]   # no `degradation` key at all
dict-001 expected    : {cumulative_confidence, cumulative_degradation, length}
dict-003 expected    : {cumulative_confidence, cumulative_degradation, length, is_acceptable}
```

The operations vectors' step shape is **narrower than spec §4.3's own wire object** and narrower than
the schema's `ChainStep`. A loader would exercise `add_step` and the two `@property`s and assert only
aggregates. The routed fix is **necessary but not sufficient** — that is worth attaching to the
routing before someone implements it and reports the gap closed (v53: run the guard against the fix).

### B.4 — N2 [LOW] · the self-declared drift-catcher is 48/48 green under all four mutations

`implementation/sdk/tests/test_jsonld_schema_roundtrip.py:11-19`:

> Covers all 9 JSON-LD schemas and **19 distinct @type values**: … *(20 names listed)* …
> This is the programmatic schema validation layer that was missing from per-module tests.
> **It catches schema/code drift.**

Proved rather than argued — `pytest tests/test_jsonld_schema_roundtrip.py -q`:

| run | result |
|---|---|
| baseline | **48 passed** |
| mutation A (silent in the full suite) | **48 passed** |
| mutation B (silent in the full suite) | **48 passed** |
| mutation C (**3 failures** in the full suite) | **48 passed** |
| mutation E (**1 failure** in the full suite) | **48 passed** |

**Zero of four**, including the two the rest of the suite does catch. The mechanism is visible in the
two dictionary round-trip tests:

- `test_translation_result_roundtrip` asserts `restored.content` and `restored.confidence` and
  **omits `degradation`** — the field the object's own docstring is about.
- `test_translation_chain_roundtrip` asserts
  `restored.cumulative_confidence == pytest.approx(chain.cumulative_confidence)`. Both sides are the
  same `@property` recomputed from the same steps: the comparison is `f(x) == f(x)` and cannot fail
  for any value of the wire document.

**The claim is published at three sites, and two of them state the stronger form.** `docs/SPRINT.md:1561`
(*"→ `from_jsonld()` → assert equality"*) and `implementation/sdk/CHANGELOG.md:457-461` (*"→
`from_jsonld()` → **assert field equality**"*). Field equality is exactly what the two dictionary
round-trips do not perform. A shipped CHANGELOG entry is a live consumer, which is a materiality
multiplier (v64: a coverage gap is not chargeable — **the document claiming the coverage is**).

The three sites also disagree with each other and with the corpus on their own denominator:

| site | count published | names listed | |
|---|---|---|---|
| `test_jsonld_schema_roundtrip.py:11` | 19 | **20** | |
| `docs/SPRINT.md:1562-1563` | 19 | **20** | |
| `CHANGELOG.md:459` | 19 | **19** — omits `DictionaryEntity`, which the file does cover | |
| corpus (`web4-standard/schemas/*.json`) | — | **20** distinct `@type` consts | measured |

The true figure is 20. Note the sets are not quite the lists' either: the corpus const is
`web4:LinkedContextToken` where all three sites write `LCT`. **"Covers all 9 JSON-LD schemas" is TRUE**
(9 of the 12 schema files match `*jsonld*.schema.json`) — do not charge that half.

**Scoping the novelty honestly (v44).** `test_jsonld_schema_roundtrip.py` has exactly **one** citation
in the whole audit corpus — `C368:74` (LCT lineage), where it appears as a *consumer* row in a coverage
table — and **zero in this lineage's ten passes**. Its own assertions have never been audited.
Matcher: `grep -rliE "test_jsonld_schema_roundtrip|schema_roundtrip" docs/audits/ web4-standard/docs/audits/`.

### B.5 — Controls, run before charging

- **Repo-wide reader check for the per-step field.** `hub/`, `web4-core/`, `ledgers/`, and the
  standalone runner `test-vectors/schema-validation/validate_schema_vectors.py`: **zero** per-step
  `degradation` readers. The only non-`dictionary.py` hits are tests and unrelated
  `degradation_factor` in `archive/`.
- **Idiom control (v46), and its limit.** The chain **aggregates**' silent discard of the wire's
  declared values is a **2-of-2 corpus idiom**: `r6.py`'s `net_trust_change`/`net_value_change` are
  `@property` with the same behaviour, and `test_r6.py:832` round-trips them with consistent data —
  the same blind spot. That control kills any finding about the *aggregates* and it is why N1 is not
  about them. **It does not reach the per-step stored field**, which is N1.
- **Schema-level denominator.** Across the 12 top-level schemas, exactly **6** properties are defined
  by their own `description` as a function of a sibling; **4 of the 6 are dictionary's**
  (`ChainStep.degradation`, `TranslationResult.degradation`, `cumulative_confidence`,
  `cumulative_degradation`); the other 2 are r7-action's, and both are `@property` in the SDK.
- **Vector-runner denominator (v47), executed and CLEAN.** `test_schema_validation_vectors.py` asserts
  92 / 186 / 278 and `test_all_schemas_covered`, and `schema-validation/` holds exactly 9 vector files
  against 9 map entries. The C364 fails-open shape is **not** present here. Recorded as a negative.
- **Registry backwards sweep, CLEAN.** `schema_registry.json` has 12 entries; `schemas/*.json` has
  exactly 12 top-level files; the sets match. (`schemas/presence-protocol/**` is a separate domain, 12
  files, deliberately unregistered.)
- **`@type` const census** used for the N2 table: 20 distinct `(schema, const)` pairs, collected by a
  recursive walk for `properties["@type"]["const"]` over `schemas/*.json`.

### B.6 — N3 [INFO] · MUST-1's SDK arm: the disclosure is unreachable from the generic entry point

`DictionaryEntity.from_jsonld`'s docstring **does** disclose the shortcut (v45's defense, which is why
this is INFO and not higher):

> Since the full LCT is not embedded (it's a separate document), a minimal LCT is created from the
> `lct_id` and spec. **The `public_key` parameter allows callers to supply the actual key.**

The remedy it names is unavailable to the SDK's own generic surface. `deserialize.from_jsonld(doc)`
dispatches on `@type` and **has no parameter through which a key could be passed**; it is the path used
by CLI `deserialize` (`__main__.py:172-175`), CLI `selftest` (`:315-323`) and MCP `web4_roundtrip`
(`mcp_server.py:216-219`). Executed:

```
generic from_jsonld -> DictionaryEntity
binding.public_key  -> restored
subject             -> did:web4:key:restored
```

Control: `grep -rn '"restored"' web4/*.py` ⇒ **exactly 2 hits, both `dictionary.py` (`:607`, `:636`)**.
No other SDK module substitutes a placeholder key on deserialization.

**Bounded honestly, and two limbs dropped:** `lct.py:287` mixes a timestamp into the id hash, so "the
id is not derivable from its own binding" is trivially true of *every* LCT and is not evidence;
`DictionaryEntity.to_jsonld` does not serialize the binding, so the placeholder stays in-memory and
cannot escape onto the wire. What remains is narrow and real: the one SDK module that hands
deserialization a fabricated key is dictionary's, and its stated escape hatch cannot be reached from
the generic, CLI or MCP callers.

---

## §C — Carry ledger (per-row table; **do not convert to prose** — that conversion is `C322-N1`)

| id | type | locus | status at C402 | evidence (command / measurement) |
|---|---|---|---|---|
| **C362-N1** | INFO, SDK track | `dictionary.py:20` claim | **HOLDS — unremediated** | `grep -c "dictionary-operations.json" tests/*.py` ⇒ 0 in every file; repo-wide (excl. `archive/`, the docstring) ⇒ 0. **Widened by §B.3: the routed fix is necessary but not sufficient.** |
| **C322-I2** | INFO, SDK track | `TestBundledRegistry` | **HOLDS** | 4 tests (`test_registry_loads`, `test_registry_contains_all_schemas`, `test_registry_schemas_have_schema_key`, `test_get_schema_uses_registry`); still **no content-equality assertion** against `schemas/`. |
| **C322-N3** | LOW, SDK track | `validation.py:219-224` | **HOLDS — inversion unchanged** | `# Try bundled registry first` still precedes the directory branch; `:8-12` still documents `WEB4_SCHEMA_DIR` as priority 1. |
| **C322-N2** | INFO, test-vector owner | `validate_schema_vectors.py:120-123` | **HOLDS** | `error_kinds = {e.validator for e in errors}` still computed for the `--verbose` message only. |
| **C282-N1** | MED, CBP + SDK-conditional | `dictionary.py:771-773` | **DOES NOT ESCALATE** | limb A: `.get(…, 1.0)` × 3 unchanged at `:771`, `:772`, `:773`. limb B **fails**: `proposals/resilience-to-incomplete-information.md` still reads `**Status:** proposal, for fleet review`; last-mover **`954ee391`** (not `4665a430` — see §A.1), unmoved since 2026-07-27. Escalation requires both ⇒ `C36-N5` is **not** re-adjudicated. |
| **C282-N2** | INFO, CBP | #579 / §6 discovery | **HOLDS** | `proposals/dictionary-as-context-mandatory-role.md` last-mover `4665a430`, blob `534d48b1`, unmoved. Carries inbound `C280-N3`. |
| **C52-B25** | INFO, SDK bundle | `AMBIGUITY_GATE` / `VERSION_BUMP_DELTA` | **STANDS — widened with behavioural evidence** | `grep -rn VERSION_BUMP` in the SDK ⇒ **0**. **New:** 25 `apply_feedback(correction)` calls move T3 composite **0.500 → 0.418** while `versions` stays `['1.0.0']`; `create_new_version` exists with **2 callers, both tests** (`test_dictionary.py:310`, `test_integration.py:1117`). Spec §5.1 step 5 is the only definer of the trigger. **Disclosure asymmetry:** `record_translation` explicitly disclaims the application layer's job (*"This does NOT process content — … provided by the application layer"*); `apply_feedback` does not. Filed as evidence under this row, **not** as a fresh finding. |
| **C52-B15/B16/B17** | MED ×3, SDK bundle | §4.1/§4.3/§2.2 vs SDK | **STAND** | target + SDK both frozen ⇒ hold by construction |
| **C52-B24** | LOW, SDK bundle | §6.2 vs `dictionary_selection_score` | **STANDS** | frozen |
| **C52-B18** | MED, SDK bundle | V3 never updated (§5.1 step 4) | **STANDS** | `apply_feedback` touches `self.lct.t3` only; `v3` untouched |
| **C52-B1/B10/B11** | MED ×3 | §4.2 flag, `fidelity`, "critical" | **STAND / OPEN** | frozen |
| **C52-B9, C17-M1/H2/M4/M6, B26, C64-B7** | operator DESIGN-Q | — | **OPEN, unchanged** | target frozen ⇒ hold by construction |
| **C322-N1** | LOW, ledger | this table | **DISCHARGED by construction** | §C is a per-row table with a disposition column |
| **C17-INFO1** | INFO, closed | §9.1 MUST enforcement | **RE-OPENED PER ARM in §B.1** | closed CLOSED-INVALID at `C52:227`; predicate answered for 2 of 5 arms. MUST-1 and MUST-2 SDK arms executed here; MUST-4's behavioural limb filed under C52-B25. |
| **B-D1** | flagship | SSOT inversion | **UNANSWERED** | operator-owned; not re-derived |

**On the C282-N1 escalation condition, an argument this lineage has not used.** PR #580 is **MERGED**
(`2026-07-28T00:43:41Z`) while its document still reads `Status: proposal, for fleet review`. That
looks like a conflict until you date the carry: `C282`'s audit doc last moved **2026-07-30**, *two days
after* #580 merged. Its author, writing *"did #580 ratify?"*, demonstrably did not mean *"did the PR
merge?"* — the merge had already happened. **The document's own Status field is the test**, and it
still reads `proposal`.

---

## §D — Routing (routes, never applies)

### D.1 — `C402-N1` [LOW] → the **SDK track**, jointly with `C362-N1`

`ChainStep.degradation` is `required` on the wire and semantically unguarded: its write site
(`dictionary.py` `add_step`) and its emit site (chain `to_jsonld`) each survive a plausible in-range
mutation with the full 2750-test suite green, while the other six degradation sites are each caught.
Root cause is structural — `cumulative_degradation` is a `@property` over `confidence`, so the stored
per-step value has no semantic reader anywhere in the repo. **Fix shape:** either derive
`ChainStep.degradation` (make it a `@property`, matching the three sibling quantities in the same
class) or add the one assertion — `abs(step.degradation - (1 - step.confidence)) < tol` — at
construction and on ingest. **Do not close this by wiring up `dictionary-operations.json`**: §B.3
measures that the vectors carry no per-step `degradation` and would remain silent.

### D.2 — `C402-N2` [LOW] → the **SDK track** (test owner) + whoever maintains `docs/SPRINT.md`

`test_jsonld_schema_roundtrip.py` publishes a coverage claim it does not meet on this field, and the
claim is restated at two further sites in its stronger *"assert field equality"* form. **Fix shape:**
assert `degradation` in `test_translation_result_roundtrip`; replace the `f(x) == f(x)` comparison in
`test_translation_chain_roundtrip` with an assertion against the **document's declared** aggregates (or
state explicitly that they are recomputed, which is the honest behaviour); correct 19 → 20 at all three
sites and add `DictionaryEntity` to the CHANGELOG list.

### D.3 — `C402-N3` [INFO] → the **SDK track**

`deserialize.from_jsonld` has no parameter through which `DictionaryEntity.from_jsonld`'s documented
`public_key` escape hatch can be supplied, and that generic path is what CLI `deserialize`, CLI
`selftest` and MCP `web4_roundtrip` all use. **Fix shape:** either thread an optional key through the
generic dispatcher, or narrow the docstring's disclosure to say that the parameter is reachable only
from the class method.

### D.4 — Routed as an observation, not a finding

The `@property`-recomputes-and-discards-the-wire behaviour of `cumulative_confidence` /
`cumulative_degradation` / `length` is a **2-of-2 corpus idiom** with `r6.py`'s
`net_trust_change`/`net_value_change`. It is not dictionary's defect. Recorded so the next pass does not
re-derive it as one.

### D.5 — Killed before charging (v44)

- *"Nothing enforces `degradation = 1 − confidence`"* — **false**: 6 of 8 sites are guarded. Killed by
  the mutation map, which is why the finding is scoped to the two silent sites and to the
  transformation-invariance of the one guard that exists.
- *"`ChainStep.degradation` has no reader"* — **false as phrased**: `to_jsonld` reads it and
  `from_jsonld` ingests it. Corrected to "no **semantic** reader".
- *"MUST-1 and MUST-4 were never executed"* — **overstated**: `C94:53-54` ran MUST-1's spec-internal
  arm, `C52-B25` ran MUST-4's constant-absence limb. Corrected in §B.1's per-arm table.
- *"10 of 50 vectors carry a confidence/degradation pair"* — **wrong denominator** (top-level-only
  matcher). Corrected to **17 of 50** by a recursive matcher, published with the finding. The
  load-bearing figure — **0 in-range violating pairs** — survives at every nesting depth.
- *"`test_jsonld_schema_roundtrip.py` is a corpus orphan"* — **false**: one citation exists at
  `C368:74`, in another lineage. Corrected to "0 of 10 passes in **this** lineage".
- *"Covers all 9 JSON-LD schemas is false"* — **true**, do not charge.
- Do **not** re-open: `C282`-R1 / R2, the `hub/` subject-matter gate, the
  `web4-core/…/trust/attestation/` false mirror, Effector/W4IP, LCT §1.2, `C362-NEG1`
  (spec examples vs JSON-LD schema — 0 of 48 corpus-wide, not dictionary's).
- `protocols/` cluster remains gated by **D0** (operator-unanswered). Not re-audited.

---

## §E — Guard for the next dictionary delta (**C442**, or on event trigger)

- Target frozen at `8e06a23c` since `95d20919`; the **9** artifacts are listed with hashes in §A and
  **may not contract** (v8). If unchanged, §A is a freeze proof — do **not** re-derive the 9 C53
  remediations an eleventh time.
- **§C stays a per-row table.** Converting it to prose *is* `C322-N1`.
- **Two carried instrument corrections**, do not re-raise either as a change: `dictionary-jsonld-validation.json`
  is blob **`f5d95664`** (`f39252d4` in C322's table is the commit); and the last-mover of
  `resilience-to-incomplete-information.md` is **`954ee391`**, not `4665a430` (§A.1).
- **The window base is the MERGED commit.** `c23ce054` this pass; verify with
  `git merge-base --is-ancestor <base> HEAD` before publishing any count.
- **`C402-N1` regression, one command:**
  `grep -n "degradation" web4-standard/implementation/sdk/web4/dictionary.py`. If `ChainStep.degradation`
  has become a `@property`, or if an `abs(deg - (1-conf))` assertion has appeared, **re-run the
  mutation map** — mutations A and B should then fail. At C402 both are silent at 2750 passed.
- **`C402-N2` regression, one command — and note which command:**
  `grep -c "assert.*degradation" web4-standard/implementation/sdk/tests/test_jsonld_schema_roundtrip.py`
  ⇒ at C402 **0**. The bare-token form is the wrong instrument and returns **3** (`:728`, `:739`,
  `:912` — all constructor kwargs, none an assertion). My own §G re-run caught me publishing the bare
  form; it is recorded here rather than silently swapped, because it is the same shape as everything
  §F is about.
- **`C402-N3` regression:** does `deserialize.from_jsonld` take a key parameter? At C402: no.
- **`C52-B25`:** re-run the behavioural probe (25 `apply_feedback` corrections; does `versions` move?).
  At C402 it does not.
- **`C362-N1`, `C322-I2`, `C322-N3`, `C322-N2`, `C282-N1`/`N2`:** all HOLD; re-run the six probes in §C.
  `C282-N1` still needs **both** limbs, and limb B is the document's **Status field**, not the PR state.
- **Do not batch** the `Validated against:` claims corpus-wide (C120/C121). `federation.py:26` is the
  federation lineage's row.

---

## §F — Method lesson

**A round-trip identity check is invariant under any transformation applied consistently on both sides.**

The guard on `ChainStep.degradation` is real — mutating the ingest site turns `web4 selftest` red. It is
also structurally incapable of noticing that the value is *wrong*, because it compares the object to
itself after a lap through JSON. Ten passes have measured whether dictionary's artifacts are *correct*
and whether they are *consumed*; none had asked what **shape** the consuming guard has. A guard's shape
is a property you can only see by mutating on **one** side of it.

Three things this pass got wrong before measuring them, all in the same direction — assuming an absence
where there was a weak presence:

1. *"No enforcement"* — there were six enforcers of eight sites. The finding is the **two** that are
   silent, and it is stronger for being bounded.
2. *"No reader"* — there were two readers. The finding is that neither is **semantic**.
3. *"Corpus orphan"* — there was one citation, in another lineage. The finding is that its **assertions**
   have never been audited, which is a different and narrower claim.

Each correction narrowed the claim and made it survivable. **v42 deflates a row; this pass shows the
same move applied to a claim's *phrasing* is what makes it publishable at all.**

And the pass's own §A carries the fourth instance: `C362:180` filed #579's commit as #580's evidence,
30 seconds apart in the log, adjacent in the predecessor's §E. That is `C400-N2`'s class recurring in
this lineage **one pass after it was named** — which is the strongest available argument that
[[re-resolve by predicate, not by id]] is not yet an operating habit anywhere in the rotation.

---

## §G — Post-write re-run (v17)

Re-executed after writing, against HEAD, in a clean shell, from the repo root unless noted:

- 9 artifact blobs ⇒ all match §A's table ✓ · target `8e06a23c`, 603 L ✓
- `git merge-base --is-ancestor c23ce054 HEAD` ⇒ 0 ✓ · `git rev-list --count c23ce054..HEAD` ⇒ **27** ✓ ·
  `-- web4-standard/` ⇒ **0** ✓
- `git log -1 --format=%h -- web4-standard/proposals/resilience-to-incomplete-information.md` ⇒ `954ee391` ✓
- baseline `pytest tests/ -q` (from `implementation/sdk`) ⇒ **2750 passed, 5 xfailed** ✓
- mutation map re-run ⇒ A **2750 passed**, B **2750 passed**, C 3 failed, D 3 failed, E 1 failed,
  F 1 failed, G 3 failed, H 6 failed ✓
- `pytest tests/test_jsonld_schema_roundtrip.py -q` ⇒ **48 passed** at baseline and under A, B, C, E ✓
- vector census (recursive matcher) ⇒ 50 / **17** with a pair / **3** sum-breakers / **0** in-range
  violations ✓
- `grep -c "dictionary-operations.json" tests/*.py` ⇒ 0 everywhere ✓
- `grep -rn '"restored"' web4/*.py` ⇒ 2 hits, both `dictionary.py` ✓
- `grep -c "assert.*degradation" tests/test_jsonld_schema_roundtrip.py` ⇒ **0** ✓ — **and this cell is
  a correction**: the re-run's first form, `grep -c "degradation" …`, returns **3** (constructor
  kwargs at `:728`, `:739`, `:912`). The §E guard published the bare form and has been fixed. A guard
  cell inherits the finding's predicate, not its vocabulary.
- `git status --porcelain` ⇒ **empty except this file**; every mutation reverted from
  `/tmp/dictionary.py.orig` ✓

No verdict moved after the re-run. **Zero files mutated outside this document.**
