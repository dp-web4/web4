# C318 Audit: `mrh-tensors.md` Eighth Delta Re-Audit

**Date**: 2026-08-05
**Target**: `web4-standard/core-spec/mrh-tensors.md` (422 lines, blob `581e9b48`)
**Prior pass**: C278 (2026-07-28, `d2fb326b`) — 7th delta, 0 net-new, zero mutation
**HEAD at audit**: `2ec8e9b3`
**Window**: `d2fb326b..2ec8e9b3` = **60 commits**, of which **1** touches `web4-standard/`
**Mutation**: **ZERO**

---

## What a complete pass looks like here (stated before §A, not after)

The target has been byte-frozen since `b8740803` (2026-07-09, 27 days), and the 60-commit window
contains exactly one `web4-standard/` file — `test-vectors/validate_context_refs.py`, which belongs
to another lineage's subject matter. That configuration is method-carry **v13**'s "false clean most
likely," and it puts a pass under pressure to produce.

So, fixed in advance: **zero net-new findings is a complete and successful pass for this
configuration.** This pass is sized by *the artifact set swept and the carries re-measured*, not by
findings returned. As it happens this pass returns **zero net-new findings** — its one substantive
result is a **status change on a standing carry**, and its own flagship candidate was killed. Both
outcomes are recorded as successes.

Every number below is published with its instrument, its scope, and the commit it ran at, and every
count was re-run **after** the finding was written, at a **different scope** than it was drafted with
(v17). Three published cells did not survive that re-run and one whole finding did not survive
adversarial verification; the corrections are in §D, not buried.

### Pre-registered admission criterion (written before the sweep, unchanged after)

- **M1** — inside the standard's published surface (`web4-standard/`) or a shipped implementation of
  it (`implementation/sdk/`, `web4-core/`, `web4-trust-core/`, `hub/`).
- **M2** — specifies or implements **mrh's subject matter**: relevance scoping, horizon bounds, edge
  typing between LCTs, fractal context nesting, or the RDF graph shape MRH is defined as. Classified
  by **role**, not path (`M2c` = in-standard normative sibling even when the path says
  `test-vectors/`).
- **M3 — reach.** The artifact must be *consumed*: loaded by a harness or validator, run by a
  documented step, or cited as normative by a spec. M3 tests reach; it does not restate M2. An
  artifact nothing reads is evidence, not a mirror.

Token list, fixed in advance, swept in both casings (`grep -F` where a token carries `.` or `-`):
`mrh` · `MRH` · `markov` · `relevanc` · `horizon` · `edge_type` · `edgeType` · `edge-type` ·
`fractal` · `mrh_link` · `mrhLink` · `propagate` · `context_depth` · `contextDepth`.

Both audit trees searched by absolute path on every coverage grep: `docs/audits/` **and**
`web4-standard/docs/audits/` (v17).

---

## Summary

| Item | Disposition |
|---|---|
| Target byte-freeze | **HELD** — blob `581e9b48`, 422L, unmoved since `b8740803` (2026-07-09) |
| C163 §4.2 guard (`mrh.py` propagation enumeration) | **HELD, 0 regression** — exactly 3 `propagate_*`; `mrh.py` blob `dea3fb4a`, last moved 2026-04-17 |
| C91-N1(b) / C130 numeric carries | **HELD** — `0.92` at `:264` and `:325`; zero `0.90` in the file |
| C129-O1 (`FRACTAL_ROLE_IDENTITY` anchor) | **CLOSED** — repointed to `:174` by C130 (`4e3feb26`, #442); `:174` verified correct at HEAD |
| **C129-O2 / X4 (inbound raw-line anchors)** | **MATERIALIZED — the event O2 predicted has occurred.** See N1 |
| C238-N2 (`edge_type` free `String`) | **OPEN, unchanged** — `lct.rs:211` still `pub edge_type: String`; `lct.rs` untouched this window |
| C278-N1 (`01f410db` vs the C42-M3 note) | **CONSUMED** — adjudicated by **C310** (t3-v3 8th, 2026-08-02) as its N1; routing closed, remedy is an open operator fork |
| C278-N2 (issue #581 general ask) | **OPEN, unchanged** — #581 still CLOSED (2026-07-28T17:24:03Z), general ask still unanswered |
| D1 / D4 / N4 | **OPEN, unchanged** — D4 gains a reach correction (N2) |
| **N1 (LOW — materialization of C129-O2/X4, NOT net-new)** | mrh's own C163 remediation broke **5 of 7** live inbound anchors, by exactly the mechanism O2 named 7 days earlier → **C319** |
| **N2 (LOW — reach-escalation on C129-D4, NOT net-new)** | the zone taxonomy D4 calls "code-only" is published in the standard's test vectors, and D4's enumeration over-counts by one at HEAD |
| **N3 (INFO, net-new, narrow)** | `test-vectors/validate_vectors.py` exits **0** on an unknown suite; its sibling in the same directory exits **1** with an `Available:` list |
| **I-1 (instrument correction → t3-v3 lineage)** | C270 attributed the wrong file identity to `test-vectors/validate_vectors.py`; five files share that basename, four byte-identical |
| **I-2 (coverage)** | `test-vectors/mrh/graph-operations.json` — **0 of 8** mrh passes, and **0** mentions in either audit tree under 5 matchers prior to this document |
| **I-3 (anchor drift in the ledger)** | the C42-M3 note is at `t3-v3-tensors.md:430-435`; C278 cited `:428-434`, C310 cited `:429-435`, against a blob unmoved since 2026-07-16 |
| **REFUTED (2)** | the `mrh-002` "declared strategy contradicts its own expected value" charge, and — after adversarial verification — this pass's **flagship**, "the cross-language validator certifies 2 of 22 suites" |

**Verdict: `mrh-tensors.md` remains byte-stable and correct — 8th consecutive delta, zero mutation,
zero net-new defects.** The substantive result is that a standing carry has **changed state**: C129-O2
warned in July that *"any line insertion above L246 silently breaks all six `:246` citations,"* routed
that to the X4 DESIGN-Q as a precondition, and then this lineage's own C163 remediation performed
exactly that insertion seven days later. Five inbound anchors are stale, and three subsequent passes
certified "byte-frozen ⇒ clean" over them.

---

## §A — Carries re-measured at live HEAD

Every row was re-derived by running its instrument at `2ec8e9b3`, not read off C278.

### The mandated guard — C163 §4.2 re-tested against `mrh.py`

```
$ grep -cE "def propagate" web4-standard/implementation/sdk/web4/mrh.py
3
$ grep -n "def propagate" …/mrh.py
198:def propagate_multiplicative(   214:def propagate_probabilistic(   228:def propagate_maximal(
```
`mrh.py` blob `dea3fb4a`, last moved 2026-04-17. The §4.2 note's enumeration is correct and complete.
**HELD, 0 regression** — do not re-flag.

### C91 / C130 numeric carries

`grep -n "0\.92\|0\.90" mrh-tensors.md` → `:264` (`web4:training 0.92`), `:325` (`web4:t3Score 0.92`);
**zero** `0.90`. **HELD.**

### C129-O1 — **CLOSED**

C129 routed a repoint of `FRACTAL_ROLE_IDENTITY.md:53` from `mrh-tensors.md:143` to `:174`. At HEAD
that line reads ``(`mrh-tensors.md:174`, default depth 3)``, and `mrh-tensors.md:174` is exactly
`- Default horizon_depth = 3 …`. Applied by `4e3feb26` (#442, 2026-07-03). **CLOSED, verified.**

### C238-N2 — **OPEN, unchanged**

`web4-core/src/lct.rs:211` is still `pub edge_type: String`, with `"birth_certificate"` compared at
`:467` and constructed at `:988`. `lct.rs` blob `2e9d4586`, last moved 2026-07-18 — **before** C278,
so untouched this window. Carried forward verbatim to the D1/D4 + web4-core owners.

### C278-N1 — **CONSUMED by C310** (routing closed)

`grep -rlF "C278-N1" docs/audits/ web4-standard/docs/audits/` → exactly one file,
`C310-t3-v3-tensors-8th-delta-2026-08-02.md`, which files it as *"an adjudication of C278-N1, not as
a net-new C310 finding"* and escalates it to an operator **fork**. The mrh→t3-v3 routing is
**closed**; the remedy is open on the operator's side. **Do not re-file, do not re-argue the merits.**

### C278-N2 — **OPEN, unchanged**

`gh issue view 581` → `state: CLOSED, closedAt 2026-07-28T17:24:03Z`. Unmoved since C278 recorded it;
the general ask (state the property-extension rule) is still unanswered. Carried.

### Carry-row survival census (v10)

| Row | C40 | C90 | C129 | C162 | C200 | C238 | C278 | C318 |
|---|---|---|---|---|---|---|---|---|
| D1 / X1 (undefined `web4:` vocabulary) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (refresh) | ✓ (unchanged) |
| D4 (`horizon_depth` 3 vs SDK; zone taxonomy) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (**N2: reach**) |
| X4 / N1(a) (§5 structural shrink) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **0** | ✓ (**N1**) |
| **O2** (inbound raw-line anchors, folded into X4) | — | — | ✓ | ✓ | ✓ | **0** | **0** | ✓ (**materialized**) |
| O1 (`FRACTAL_ROLE_IDENTITY` anchor) | — | — | ✓ | ✓ | 0 | 0 | 0 | ✓ (**CLOSED**) |
| `RFC-SHARED-POLICY-SUBSTRATE.md` named | — | — | ✓ | ✓ | 0 | 0 | 0 | ✓ |

**The zero column is the finding, and it is mine as much as the corpus's.** O2 last appears at C200
(2026-07-16, *"Its inbound-anchor census (O2 + C162 A1/A2) unchanged"* — asserted **7 days after** the
break it was watching for). C238 and C278 drop it, and **this pass's first draft dropped it too**: §A
was written claiming every carry had been re-derived, while X4 and O2 appeared nowhere in it. They
were recovered only under adversarial verification (§D 1). Per v11, these zero-rows are **cross-doc**,
not target-internal, so byte-freeze of the target does not warrant them.

---

## §B — Findings

### N1 (LOW) — **materialization of standing carry C129-O2 / X4.** Not net-new: the predicted event has occurred, and this lineage caused it

**What O2 said, on 2026-07-02** (`C129-…md:69`, folded into the X4 operator DESIGN-Q at `:99`):

> Three new downstream docs now cite mrh by **raw line number**: `:246` ×6 … all for the "T3/V3 not
> absolute / only within role context" axiom … Consequently the deferred **X4/N1(a) §5-shrink — or any
> line insertion above L246 — silently breaks all six `:246` citations.** … before any §5 shrink,
> migrate the 8 inbound anchors to section references.

**What happened, seven days later.** `b8740803` — *"remed(C163): mrh-tensors — apply C162's single
autonomous item"*, 2026-07-09 — has one hunk, `@@ -198,12 +198,14 @@`: **+2 lines** at §4.2. That is
a line insertion above L246. Everything below shifted by two:

```
$ git show b8740803^:web4-standard/core-spec/mrh-tensors.md | grep -n "not absolute properties"
246:**T3/V3 tensors are not absolute properties of entities …**
$ grep -n "not absolute properties" web4-standard/core-spec/mrh-tensors.md
248:**T3/V3 tensors are not absolute properties of entities …**
$ sed -n '246p' web4-standard/core-spec/mrh-tensors.md
### 5.1 Critical Principle: Trust is Role-Specific
```

**The inbound census at HEAD — 7 anchors / 3 documents, 5 broken:**

| citing site | anchor | state |
|---|---|---|
| `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md:37` | `mrh-tensors.md:246` | **BROKEN** — quotes the sentence verbatim; `:246` is now the heading |
| `web4-standard/rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md:54` | `mrh-tensors.md:246` | **BROKEN** |
| `…RFC-COMPOSITE…:82` | `mrh-tensors.md:246` | **BROKEN** — carries a normative MUST NOT on cross-role aggregation |
| `…RFC-COMPOSITE…:117` | `mrh-tensors.md:246` | **BROKEN** — alignment-table row |
| `web4-standard/rfcs/RFC-SHARED-POLICY-SUBSTRATE.md:165` | `` `mrh §246` `` | **BROKEN** — the loose spelling C162-A2 warned about |
| `…RFC-COMPOSITE…:97` | `mrh-tensors.md:143` | correct — **above** the hunk |
| `FRACTAL_ROLE_IDENTITY.md:53` | `mrh-tensors.md:174` | correct — above the hunk, and it is C130's repoint |

7 total / 3 documents reproduces **C162-A1's corrected census exactly** (C129's 8 → 7; `RFC-COMPOSITE
:246` ×4 → ×3), with `:143` ×2 having become `:143` ×1 + `:174` ×1 when C130 applied O1. The hunk
position is the whole explanation: **every inbound anchor below line 209 broke; every one above it
held.**

All three citing documents were correct when written (`b447f33e` #402 and `9921e9c4` #403, both
2026-06-28; `43c90d3e`, 2026-06-30) and all three are below canon tier — `RFC-COMPOSITE`
`**Status**: Proposed`, `RFC-SHARED-POLICY-SUBSTRATE` `**Status**: Proposed`,
`FRACTAL_ROLE_IDENTITY` *"Draft / design. Plan, not yet built."* (v3 tier check).

**Why LOW.** The stale anchors land on the heading of the *correct* section, two lines above the
sentence; `FRACTAL:37` quotes the sentence verbatim, so no reader can be misled about *what* is being
cited; and all three citing documents are pre-canon tier. This is citation integrity for a human
implementer, not a semantic defect.

**Why it is not net-new.** By the same rule this pass applies to N2, a carry whose predicted event
occurs is a **status change on that carry**, not a new finding — C129-O2 identified the fragility,
enumerated the blast radius, and named the trigger class. Filing it as net-new would claim credit for
a prediction the corpus made in July and would detach the remedy from the X4 decision it was
deliberately folded into.

**What *is* new, and it is the uncomfortable part:** O2 was written to protect against a *deliberate*
§5 shrink. The insertion that fired it was a **two-line correction to a note about the SDK API**,
authored by this audit lineage, in a remediation slot, seven days after the warning — and then
certified clean three times (C200, C238, C278) by passes that read "byte-frozen" as "nothing to
check." O2's precondition (*migrate the anchors to section references first*) was never executed
because nobody expected the trigger to come from inside.

**Route**: **C319** (the paired remediation slot, now not a no-op) — repoint the five `:246`/`§246`
sites to the section anchor `#51-critical-principle-trust-is-role-specific`, which is what O2 and
C129-O1 both recommended and what would have survived `b8740803`. Doc-only, three files, no spec text.
**Not applied here.** The X4 DESIGN-Q remains open and its cost picture is *reduced* by executing the
migration: after C319 the §5-shrink has no raw-line anchors left to coordinate.

### N2 (LOW — reach-escalation on C129-D4, **NOT net-new**, do not re-file)

C129-D4 records the horizon-zone taxonomy as `SELF/DIRECT/INDIRECT/PERIPHERAL/BEYOND` *"living only
in code."* Both halves are stale at HEAD:

1. **Not only in code.** `test-vectors/mrh/graph-operations.json` `mrh-001.expected.zones` publishes
   `SELF` / `DIRECT` / `INDIRECT` inside `web4-standard/`, and that expectation is executed
   (`sdk/tests/test_mrh.py::TestMRHVectors`, in CI via `.github/workflows/sdk-test.yml`). The taxonomy
   is in the standard's published surface.
2. **The enumeration over-counts by one.** `mrh.py:388` documents *"keys: SELF, DIRECT, INDIRECT,
   PERIPHERAL"* and `:392-395` builds exactly those four. `grep -n "BEYOND" …/mrh.py` → **0 hits.**
   There is no `BEYOND` zone at HEAD.

Per v16 this is a **reach escalation with a factual correction** on an existing carry: it changes what
D4 is about (a spec-vs-code gap → a spec-vs-standard-artifact gap) without changing that D4 is open.
Routed **with** D4, to be adjudicated together.

### N3 (INFO, net-new, narrow) — the vector validator exits 0 on an unknown suite, against its own directory's convention

`web4-standard/test-vectors/validate_vectors.py` (blob `5259d473`, 423L) takes suite names positionally
(`suites = sys.argv[1:] if len(sys.argv) > 1 else ["t3v3","atp"]`, `:400`) and has no unknown-name
path. Measured at `2ec8e9b3`, exit codes captured without a pipe:

| invocation | output | exit |
|---|---|---|
| `validate_vectors.py` | `Results: 87 passed, 0 failed` | 0 |
| `validate_vectors.py mrh` (a suite that exists on disk) | `Results: 0 passed, 0 failed` | **0** |
| `validate_vectors.py zzzz` | `Results: 0 passed, 0 failed` | **0** |
| `schema-validation/validate_schema_vectors.py zzzz` | `Unknown target(s): ['zzzz']. Available: [...]` | **1** |

The sibling validator **in the same tree** rejects an unknown target with a non-zero exit and an
`Available:` list. So exit-0-on-unknown is not house style; it is one file out of step with its own
directory. A user who mistypes a suite name, or who reasonably tries `mrh` because
`test-vectors/mrh/` exists, gets a green result having validated nothing.

**INFO, not MEDIUM** — see §D 2 for the flagship this replaced and why the larger charge died. Not in
CI (`grep -rn validate_vectors .github/` → 0). Never previously reported: `grep -rliF` over both audit
trees for `"Run all vector suites"` and `"cross-language test vector validator"` → 0 files; the three
docs naming the file (C182 — a *different* file; C270 — see I-1; C306 — duplicate-ID note) say
something else. **Route**: test-vector owner, as a one-line nit — raise `SystemExit(1)` with the
supported-suite list, matching the sibling.

---

## §B′ — Negatives, with their instruments

Published as negatives so silence does not imply the check was skipped (v13 §7).

1. **Mirror set, derived from subject matter in both citation directions (v14), then coverage-measured
   across all 8 passes.** Instrument:
   `grep -rl -iE "mrh|markov|relevanc|horizon|edge_type|edgeType|fractal" web4-standard/{schemas,test-vectors,testing,ontology,deployment}/`
   → **26 artifacts**. Coverage (`grep -lF <basename>` over the 8 mrh pass docs):

   | coverage | artifacts |
   |---|---|
   | 6/8 | `ontology/t3v3-ontology.ttl` |
   | 5/8 | `ontology/web4-core-ontology.ttl` |
   | 3/8 | `ontology/role-extension.ttl` |
   | 1/8 | `ontology/role-extension-schema.md`, `test-vectors/t3v3/tensor-operations.json` |
   | **0/8** | **21 artifacts**, including `test-vectors/mrh/graph-operations.json` |

   The lineage has read the **ontology** tree consistently and the **schemas / test-vectors /
   conformance** trees essentially never — the same shape C306 found for atp-adp and C312 for
   reputation. `deployment/` returns **0 files** for every token: a measured zero, not an unswept tree.

   **Caveat published with the number (v13 §5):** 0-of-8 *audit* coverage is not "unenforced."
   Measured by JSON basename over `implementation/sdk/` plus the four `test-vectors/**/*.py`
   validators: **30 of 35** vector files have a consumer, and **21 of 22** directories have at least
   one — `graph-operations.json` among them (`sdk/tests/test_mrh.py`, run in CI by
   `.github/workflows/sdk-test.yml`). The **5 file-level orphans** are `keys/test-keypairs.json`
   (fixture keypairs, not a suite) and four `lct/` files — `interop-human-full.json`,
   `interop-minimal-interop.json`, `interop-revoked-agent.json`, `valid-birth-certificate.json` —
   which are **not** mrh's to raise; noted here so the next lineage to sweep this tree inherits the
   measurement rather than re-deriving it. Coverage in the table above means *this lineage has never
   looked*, nothing more.

2. **`edge_type` / `edgeType` / `edge-type` in the standard's artifact tree: 0 files.** The vocabulary
   C238-N2 is about exists only in `web4-core/src/lct.rs` and in prose. The carry's scope is unchanged.

3. **Inbound anchor sweep — run twice, with a tight and a loose pattern.**
   `grep -rnoE "mrh-tensors\.md[:#]L?[0-9]+"` (all files; `.git`/`node_modules`/`target` excluded) →
   **26 occurrences: 20 inside the two audit trees** (9 of them this document's own) **and 6 live.**
   That tight pattern **undercounts**, exactly as C162-A2 predicted: adding
   `grep -rn "mrh §[0-9]"` recovers `RFC-SHARED-POLICY-SUBSTRATE.md:165`, giving the true live census
   of **7 anchors / 3 documents**. Both numbers are published because the gap between them *is* the
   A2 lesson.

4. **#637's `validate_context_refs.py` gate — vacuous for mrh.** The window's single `web4-standard/`
   commit (`8d3808db`, 2026-08-04, #637) gates that every `@context` URI in `test-vectors/` has a
   backing file. `graph-operations.json` declares no `@context`, so the gate asserts nothing about the
   mrh suite. Consistent with **C316-I-3**, which found the same gate vacuous for presence on two
   grounds — cited, not re-filed.

5. **SDK mirror gate.** `mrh.py` blob `dea3fb4a` (2026-04-17) and `lct.rs` blob `2e9d4586`
   (2026-07-18) are both older than C278; neither moved this window. Recorded **empty**, per C266 — no
   datapoint manufactured.

---

## §C — Candidates raised and killed

### C-1 — "`mrh-002` declares a strategy its own expected value contradicts" — **REFUTED**

The charge: `mrh-002` sets `"strategy": "probabilistic"` with `"decayFactor": 0.7`, but its
`description` says *"multiplicative decay along path"* and its `explanation` computes
`0.9*0.7 → 0.63; 0.63*0.7*0.49 = 0.21609` — exactly `propagate_multiplicative`'s
`trust *= w * (decay ** (i+1))`. `propagate_probabilistic` (`mrh.py:214`) computes `1 - ∏(1 - p_i)`,
takes path trusts rather than edge weights, accepts no decay factor, and on `[0.9, 0.7]` returns
**0.97** — 4.5× the published expectation. The vector is executed with the declared strategy passed
through (`test_mrh.py:322-329`).

**Killed by reading `trust_between` (`mrh.py:457-493`).** The two names operate at different levels:
every path is decayed with `propagate_multiplicative` first (`:485`), and `strategy` selects the
**cross-path combiner** (`:488-493`). `mrh-002` has a single path, so
`propagate_probabilistic([0.21609]) = 0.21609` — the published value, exactly. The vector is
internally consistent. No finding.

One true observation survives and is deliberately **not** filed: `strategy == "multiplicative"` and
`strategy == "maximal"` both `return propagate_maximal(path_trusts)`. With all paths already
multiplicatively decayed those *are* the same quantity, so this is correct-but-redundant SDK-internal
code, not a spec divergence.

### C-2 — the flagship: "the cross-language validator certifies 2 of 22 suites and exits 0 for the other 20" — **REFUTED under adversarial verification**

This pass drafted, and very nearly shipped, a MEDIUM: `test-vectors/validate_vectors.py` promises
*"Any language implementation that passes these vectors is interoperable"* and documents
`python validate_vectors.py  # Run all vector suites`, yet validates 2 of 22 suite directories and
exits 0 for the rest. The exit codes and the counts were all correctly measured. The **framing** was
wrong, in three independent ways, each sufficient on its own:

1. **It is not "the standard's conformance harness."** `find web4-standard/test-vectors -name '*.py'`
   returns **four** validators: this one, `validate_context_refs.py`, and per-suite validators
   `attestation/validate_attestation_vectors.py` and `schema-validation/validate_schema_vectors.py`.
   The quoted "interoperable" sentence is **house boilerplate** — the attestation validator carries the
   same sentence for a single suite. And the sibling's usage block reads
   `validate_schema_vectors.py  # Run all` / `… lct  # LCT only`: in this tree, *"run all"*
   idiomatically means *all suites this validator owns.* The docstring was over-read.
2. **The claim was true when written.** `git log --follow` → the file has exactly one commit,
   `a3b93713` (2026-02-27), *"Add cross-language T3V3 and ATP test vectors with validator (87/87)"* —
   it shipped in the same commit as `t3v3/` and `atp/`, the only two suites that then existed. `mrh/`,
   `acp/`, `dictionary/` arrived 2026-03-14; `schema-validation/` 2026-03-21. This is an **accretion
   artifact**, not a false claim.
3. **The denominator was incommensurable.** The tool dispatches on a `vectors[].operation`
   discriminator; only **2 of the 35** JSON files carry that field at all. Nine are
   `{valid, invalid}` JSON-Schema sets with their own runner; eight have no top-level `vectors[]`. The
   other suites are not "unimplemented in this tool" — they are a different artifact class with a
   different mechanism, and **21 of 22 directories have an executing consumer in CI**.

What survives is the one cell that all three attacks left standing: the unknown-suite exit code, which
its own directory's sibling handles differently. That is **N3, INFO**.

**Recorded as a method result, not an embarrassment.** The refuter was pointed at the flagship first,
by rule, and the flagship is what it killed. The counts were right and the conclusion was wrong — the
failure was in *what the artifact is*, which no amount of re-running the same greps would have found.

---

## §D — Method notes

1. **The carry census must be built from the lineage's own earliest ledgers, not from the previous
   pass's summary.** This pass's §A was drafted with D1/D4/N4 and the C238/C278 findings — and
   silently omitted **X4** and **O2**, the two rows that turned out to hold the entire result. They
   were inherited through a compressed pointer that said *"D1/D4/X4/N4 = operator DESIGN-Qs"* and
   never expanded, so O2 — a sub-item folded **into** X4 at C129 and last mentioned at C200 — was
   invisible. v10 says a column of zeros is the finding; the sharper form is: **a carry that was
   folded into another carry loses its own row, and then loses its own zeros.** Grep the earliest full
   ledger in the lineage (here `C129-…md:69,99` and `C162-…md:86,107,218-219`), not the last summary.

2. **My tight anchor grep committed the exact defect C162-A2 recorded 27 days earlier.** A2's rule:
   *"any §5-shrink enumerating its blast radius by grepping `mrh-tensors\.md:[0-9]` will undercount"* —
   because `RFC-SHARED:165` writes `` `mrh §246` ``. This pass enumerated the blast radius by grepping
   `mrh-tensors\.md[:#]L?[0-9]+`, and undercounted by precisely that anchor (4 instead of 5). The rule
   was in the lineage's own record, in the audit doc *for the very commit that caused the break*. A
   method carry that is not re-read is not a method carry.

3. **Three published cells did not survive the post-write re-run** (v17 working as designed):
   - §B′3 was drafted as *"13 anchors: 9 in `docs/audits/`, 4 live."* Occurrence-counting instead of
     `sort -u` over `file → anchor` pairs gives **26 / 20 / 6**. `sort -u` is a claim about identity,
     not quantity, and reporting a deduplicated pair-count using the word *anchors* is the same defect
     class this corpus keeps charging others with.
   - N3 was drafted asserting `web4-standard/README.md:106` links the harness, raising its reach.
     Resolving the link relative to its own file shows it points at `web4-standard/validate_vectors.py`
     — the *quadruplicated JOSE/COSE copy*. Cut.
   - The I-2 phrase-matcher re-run returned **1** file rather than 0 — this document, which by then
     existed. Stated so the number reproduces: 0 among the 8 prior passes, 1 including C318.
   - The consumer-coverage cell in §B′1 was first measured with `grep -rl "<dir>/"` and reported
     **13** directories with no SDK consumer. That instrument is broken: `test_mrh.py:301` builds its
     path as `os.path.join(…, "test-vectors", "mrh", "graph-operations.json")`, so the string `mrh/`
     never appears. Re-measured by **JSON basename**: 30 of 35 files and 21 of 22 directories are
     consumed. A verifier that *disagrees* is as much a hypothesis as one that agrees (v13 §6) — 13
     identically-shaped "orphans" was the tell.
   - And a labelling error corrected throughout: three "blob" citations were not blobs.
     `mrh.py` blob = `dea3fb4a` (`759eaefa` is the *commit*); `lct.rs` blob = `2e9d4586` (`2ec6ae09` is
     the commit); `validate_vectors.py` blob = `5259d473` (`472a7331` was an **md5**). Three object
     kinds under one word, in a document whose method is *publish the instrument*.

4. **Five files, one basename, and a past pass got the identity wrong.** `find . -name
   validate_vectors.py` → **5**: four byte-identical copies of the JOSE/COSE interop checker (md5
   `e2068118`, 7708 B / 180 L) at `web4-standard/`, `web4-standard/tools/`,
   `web4-standard/testing/validator/`, `forum/nova/validator/`; plus one different file (blob
   `5259d473`, 18188 B / 423 L) at `web4-standard/test-vectors/`, the t3v3/atp harness.
   → **I-1**, routed to the t3-v3 lineage: C270 §2 characterises
   `web4-standard/test-vectors/validate_vectors.py` as *"a JOSE/COSE canonicalization checker — not a
   tensor harness."* It **is** a tensor harness; it defines `validate_t3v3()` and running it prints 87
   passing t3v3+atp assertions. **C270's conclusion survives untouched** (the vectors are still loaded
   by exactly one language; there is still no Rust harness) — one supporting cell is wrong, and the
   cause is a basename that collides five ways. Correction published here; C270 is not rewritten (v11).

5. **Three passes, three anchors, one unmoved blob → I-3.** The C42-M3 note lives at
   `t3-v3-tensors.md:430-435` at HEAD (`grep -n "Note on V3 entity-role binding"` → 430;
   `grep -n "role-contextual"` → 435). C278 cited `:428-434`; C310 cited `:429-435`. The blob is
   `32d3368e` in all three passes — unmoved since `d89595e8` (2026-07-16), before either audit. At most
   one could have been right; neither was, and C278's range additionally truncates the note's final
   clause, which is the design rule C278-N1 says was negated. The corpus's live cross-lineage MEDIUM
   has never had a correct anchor. An instrument defect, published so the next pass resolves it by
   content.

6. **Proposed method carry v18 — a census is not a resolution.** The narrow, true form, after the
   adversarial pass cut the wider claim: C129, C162 and C200 all *did* run the inbound-anchor census,
   so the blind spot was never "nobody looked inbound." What none of them did was **re-resolve the
   anchors by content after the target moved** — a census counts citations, a resolution checks that
   each one still lands on what it quotes. So: *when the target's blob changes, every inbound anchor
   must be re-resolved by content in the same commit, with a loose pattern (`file:N`, `file#LN`,
   `§N`).* A remediation slot is the highest-risk place for this, because it is the one actor that
   edits a file the lineage has certified frozen.

7. **Cadence datapoint** (a measurement for the standing operator DESIGN-Q; **not** a proposal, and not
   this track's to decide):

   | pass | ordinal | days frozen | `web4-standard/` commits in window | artifacts newly swept | findings |
   |---|---|---|---|---|---|
   | C318 | 8th delta | 27 | 1 (another lineage's) | 21 (0/8 before this pass) | **0 net-new defects**; 1 carry materialization, 1 reach escalation, 1 INFO, 3 instrument corrections, 2 candidates refuted |

   Set beside C306 (atp-adp, same configuration → 2 MEDIUMs in an unread artifact tree) and C316
   (presence, 43 days frozen / 0 subject-matter commits → 4 artifacts at 0/7 and the two-audit-trees
   discovery). Three data points now say the same thing: **the frozen-target configuration is where the
   artifact sweep pays, and pass ordinal does not predict yield.** C318 adds a fourth reading the
   others do not: its yield came from *the lineage's own oldest ledger*, not from the neighbourhood at
   all.

---

## Disposition for C319 (paired remediation slot)

- **N1 — APPLY.** Repoint the five stale sites — `FRACTAL_ROLE_IDENTITY.md:37`;
  `RFC-COMPOSITE-ENTITY-IDENTITY.md:54`, `:82`, `:117`; `RFC-SHARED-POLICY-SUBSTRATE.md:165` (loose
  `` `mrh §246` `` spelling) — to the section anchor
  `#51-critical-principle-trust-is-role-specific`. Doc-only, three files, no spec text. This executes
  the precondition C129-O2 attached to X4, and **reduces** X4's cost. The C130 pattern exactly.
- **N2 — route with C129-D4**, do not adjudicate separately.
- **N3 — route to the test-vector owner** as a one-line nit (non-zero exit + supported-suite list,
  matching `validate_schema_vectors.py`). Do not touch the suite coverage.
- **I-1 — route to the t3-v3 lineage** as a correction to one supporting cell of C270; C270's
  conclusion is untouched and must not be re-litigated.
- **C238-N2, C278-N2, D1, D4, N4, X4 — carried forward.** X4 stays open; after N1 is applied its
  anchor-migration precondition is discharged.

---

*C318 verdict: `mrh-tensors.md` byte-stable and correct — 8th consecutive delta, zero mutation, zero
net-new defects. The C163 §4.2 guard re-tested against `mrh.py` ground truth (exactly 3 propagation
functions, 0 regression); C129-O1 verified CLOSED; C278-N1 verified CONSUMED by C310; C238-N2 and
C278-N2 carried unchanged. The result is a **state change on a standing carry**: C129-O2 warned on
2026-07-02 that any line insertion above L246 would silently break the inbound `:246` citations and
made anchor migration a precondition of the X4 §5-shrink; `b8740803` — this lineage's own C163
remediation, seven days later — inserted two lines at §4.2, and **5 of the 7 live inbound anchors have
been stale ever since**, through three passes that certified "byte-frozen ⇒ clean." The first §B
artifact sweep this lineage has run found 21 of 26 subject-matter artifacts at 0-of-8 coverage,
including the standard's only MRH-named test-vector suite; following its reach produced one INFO after
adversarial verification killed the MEDIUM it was drafted as. Both of this pass's own flagship
candidates were **REFUTED** — the mrh-002 strategy contradiction by reading `trust_between`, and the
"2 of 22 suites" charge by discovering the file is one of four per-suite validators whose claim was
true the day it shipped. C319 applies N1 only.*
