# C374 — `errors.md` 9th delta audit

**Target**: `web4-standard/core-spec/errors.md`
**Date**: 2026-08-13
**Slot**: C374 (= C334 + 40, standing rotation arithmetic)
**Prior pass**: `docs/audits/C334-errors-8th-delta-2026-08-07.md` (PR #663)
**Lineage** (inclusive rule — every C-numbered delta plus the non-C-numbered
`…-internal-consistency-…` member, of which this lineage has none): C30, C66, C106, C138, C178,
C216, C254, C294, C334 → **C374 is the 9th delta, 10th pass**.
**Mutation by this pass**: **ZERO.** One new file (this document).

---

## §0. Headline

**The target moved.** For the first time in eight passes `errors.md` is not byte-frozen. C334 froze it
at `6189432d` (blob `acda930e`, 154 L, 51 d, 7th consecutive zero-mutation pass). At this HEAD it is
blob `9cf077ba`, **157 L**, last written **2026-08-10** by `afd04623` (#678, *"fold hackathon findings
into canonical Web4 text"*).

That commit is a **direct remediation of `C334-N1`**, delivered by another track — the errors lineage's
carry was discharged by someone else while the rotation was elsewhere (opening-sequence step 4).

**But it discharged one limb of a three-limb finding.** `W4_ERR_PROTO_FORMAT` now exists in the spec.
It does **not** exist in the SDK enum that declares the spec as its authority, and the registry row
that predates it asserts a **different scope** for the same code. The suite is **50 passed**, because
nothing in it reads `errors.md`; and the correct fix, applied and executed in place this session, turns
**2 of the suite's 4 cardinality pins red**.

| Limb | Locus | C334 / C340 status | Status at this HEAD |
|---|---|---|---|
| **Spec** | `core-spec/errors.md` §2.6 | absent | ✅ **DISCHARGED** `afd04623`, 2026-08-10 |
| **SDK** | `implementation/sdk/web4/errors.py` `ErrorCode` | absent | ❌ **OPEN** — containment now 24 of 25 |
| **Registry** | `registries/initial-registries.md:52` | present, unreconciled | ❌ **OPEN** — sole description break, 1 of 25 |

---

## §A. Freeze check — FAILED (by design; the target mutated)

```
$ git log --oneline -- web4-standard/core-spec/errors.md
afd04623 2026-08-10  docs(standard): fold hackathon findings into canonical Web4 text (#678)
6189432d 2026-06-17  spec(C67): remediate 3 autonomous C66 findings on errors.md (#347)
$ git hash-object web4-standard/core-spec/errors.md
9cf077bad906f2396e9006d214a89b9fce241193      # C334 recorded acda930e
```

`afd04623` touches `errors.md` in exactly **three hunks**:

| Hunk | Change |
|---|---|
| `@@ -2,7` | `Last-Updated` 2026-06-17 → **2026-08-09** |
| `@@ -91,6` | **+** `\| W4_ERR_PROTO_FORMAT \| Protocol Format Error \| 400 \| Message encoding, canonical form, or required protocol structure is malformed or unsupported \|` at `:94`, **+** a SHOULD gloss at `:96` |
| `@@ -142,7` | §5's `400 Bad Request` line gains *", invalid protocol format"* |

**This is exactly what `C334-N1` specified.** C334's ledger (`C334:513`) asked for *"one row in §2.6 at
the next remediation turn (status `400`)"*. The row is in §2.6 and the status is 400. **DISCHARGED,
exact.**

**§1 was NOT edited.** C354's disposition row claims otherwise — see **N4**.

---

## §B. The measurements

Every cell carries the command that produced it (v45).

### B.1 — Code sets

```
$ # concrete codes in errors.md §2 (table rows; the 6 W4_ERR_<CATEGORY>_ tokens are
$ # §2.1–§2.6 heading prefixes, not codes — a table-row regex returns the identical set,
$ # so the count does not depend on the stub filter)
errors.md concrete codes .................. 25
$ cd web4-standard/implementation/sdk && python3 -c "from web4.errors import ErrorCode; print(len(ErrorCode))"
ErrorCode members .......................... 30   (30 distinct values)
$ comm on the two sorted sets
in errors.md, NOT in ErrorCode ............. W4_ERR_PROTO_FORMAT          (1)
in ErrorCode, NOT in errors.md ............. W4_ERR_CROSS_SOCIETY_EXCHANGE_INVALID
                                             W4_ERR_CROSS_SOCIETY_LAW_CONFLICT
                                             W4_ERR_CROSS_SOCIETY_UNRECOGNIZED_LCT
                                             W4_ERR_CROSS_SOCIETY_WITNESS_REQUIRED
                                             W4_ERR_PROPAGATION_SCOPE_UNSUPPORTED
                                             W4_ERR_R7_REPUTATION_INVALID  (6)
intersection ............................... 24
```

**The relation is CONTAINMENT, not bijection — and it is the SDK's own declared contract, not an
invariant this lineage invented.** Publishing the superset is a correction to how I first framed this
pass; the 6 enum-only codes are *declared* at their source:

```
web4/errors.py:4   "Canonical implementation per web4-standard/core-spec/errors.md."
web4/errors.py:63  """All 30 Web4 error codes from the error taxonomy spec + mcp-protocol.md §7.6."""
```

The enum states its own composition as **errors.md §2 ⊕ mcp §7.6**. So `errors.md §2 ⊆ ErrorCode` is
the contract `errors.py` writes down for itself. C334 measured that containment at **24 of 24**. It is
now **24 of 25**, and has been since 2026-08-10 — **3 days**.

### B.2 — The guard asymmetry

```
$ pytest tests/test_errors.py -q
50 passed in 0.06s

$ grep -rn "errors\.md" tests/ web4/
web4/errors.py:4:    Canonical implementation per web4-standard/core-spec/errors.md.
```

**One hit, and it is a docstring.** No test opens any `.md`. Nothing in the suite can observe a spec
addition. The suite's only external read is `test-vectors/errors/error-taxonomy.json` — **5 codes of
25** (B-9, re-measured, unchanged; 0 cross-society).

The suite carries **four** hardcoded numeric pins, all on the *implementation* side:

| Pin | Locus | Value |
|---|---|---|
| `test_exactly_30_codes` | `tests/test_errors.py:47-48` | `len(ErrorCode) == 30` |
| `test_exactly_7_categories` | `tests/test_errors.py:50-51` | `len(ErrorCategory) == 7` |
| `test_codes_per_category` | `tests/test_errors.py:53-65` | dict, incl. `ErrorCategory.PROTO: 4` |
| `test_vector_count` | `TestVectors` | `5` |

**Executed probe** — the complete fix (enum member **+** its `ERROR_META` entry) applied in place, suite
run, then reverted; `git status --porcelain` empty afterward and `50 passed` restored:

```
FAILED tests/test_errors.py::TestRegistryCompleteness::test_exactly_30_codes
FAILED tests/test_errors.py::TestRegistryCompleteness::test_codes_per_category
E   AssertionError: ErrorCategory.PROTO has 5 codes, expected 4
2 failed, 48 passed in 0.07s
```

Two pins, in two test classes. Plus three prose "30" claims (`errors.py:7`, `errors.py:63`,
`test_errors.py:5`). *(An enum-only patch, without the `ERROR_META` entry, fails 4 — three of those are
merely an unfinished fix, and are not evidence about the pins. The complete-fix number is the honest
one.)*

**The counter-reading, stated before it is rejected**: a hardcoded cardinality pin is a legitimate
change-detector, and going red when the enum changes is precisely its job. That defence holds *if the
enum is primary*. By `errors.py:4` it is not — the module names the spec as its authority. **The defect
is the asymmetry, not the pin.** It is a **one-sided change-detector**: it fires on implementation
drift and is structurally incapable of firing on spec drift, in a module that declares the spec
upstream. It does not *cause* the divergence and does not *block* the repair — it prices the repair at
two extra edits, silently, in a suite that reports green while the divergence is live.

### B.3 — Registry vs spec, with its denominator

Descriptions compared for all codes shared by `errors.md` §2 and `registries/initial-registries.md`:

```
shared: 25    AGREE (verbatim, case-insensitive): 24    DISAGREE: 1

  W4_ERR_PROTO_FORMAT
     errors.md:94  Message encoding, canonical form, or required protocol structure is
                   malformed or unsupported
     registry:52   Message format doesn't match negotiated profile
```

**24 of 25 agree verbatim. `PROTO_FORMAT` is the only break.** Description agreement between these two
files is a maintained property of this corpus at 24/25, so this is **not idiom** (v46 — the sibling
ratio decides finding-vs-idiom).

And the two texts do not merely differ in wording, they differ in **scope**: the registry row
(entered at `be353fe0`, long predating the fix) is narrow and handshake-specific — *"doesn't match
negotiated profile"*, matching `web4-handshake.md:164`'s single use — while #678 wrote a **general**
structural-format meaning into §2 and glossed it as the *core* code for the class. The spec generalised
the code; the registry still carries the narrow meaning.

### B.4 — Re-measured standing carries (re-measure, don't transcribe)

| Carry | C334 | This pass | Verdict |
|---|---|---|---|
| **B-H1** numeric registry orphan | 0 shared; 11 vs 24 | `grep -c W4_ERR registries/error-codes.md` = **0**; 12 `0x000*` lines vs **25** §2 codes | ✔ orphan still **total** |
| **B-2** `initial-registries.md` §2-absent codes | **7** | **6** | ⚠️ **MOVED — see §C.1** |
| **B-9** vector coverage | 5 of 24; 0 cross-society | **5 of 25**; **0** cross-society | ✔ (denominator moved with §2) |
| **B-5** SDK ↔ mcp §7.6 statuses | 3 of 6 diverge | **3 of 6 diverge** (`403/404`, `409/400`, `412/403`; `409/409`, `400/400` agree) | ✔ exact |
| **§2 ↔ SDK** | 24/24 | **24 of 25** | ⚠️ **BROKEN — N1** |

---

## §C. Findings

### C.1 — `C374-N1` (MED) — #678 discharged the spec limb and left the SDK limb open; the module's own declared authority is the thing it now disagrees with

**Not net-new. Filed as the Nth member of a named family** (v51):
`C70 B-C1` ≡ `C334-N1` ≡ `C340 HS-X4` (`docs/audits/C340-web4-handshake-8th-delta-2026-08-08.md:65`,
2026-08-08: *"`W4_ERR_PROTO_FORMAT` MUST-abort at `:164`; present in exactly 2 files, 0 in `errors.md`,
0 in the SDK tree. ≡ C70 B-C1"*). C340's SDK clause is **still true at this HEAD**: repo-wide the code
lives in 5 files, **zero** under `implementation/`.

What is new is **dated and structural**:

1. `errors.py:4` / `:63` declare the enum's authority to be `errors.md` §2 **+** mcp §7.6. Containment
   went **24/24 → 24/25** on 2026-08-10 and no gate can see it.
2. The break is invisible to every green signal: `50 passed`, and the only mention of `errors.md` in
   `tests/` or `web4/` is a docstring.
3. The correct fix is **test-breaking in two pins** (executed above), so the divergence is not merely
   unnoticed — closing it has a cost that no one has been shown.
4. **`B-2` moved 7 → 6, and the missing member is exactly this code.** C334 measured 7 §2-absent
   registry codes and identified the 7th itself (`C334:461`: *"a 6th is metering's `W4_ERR_FORMAT`
   renamed to `W4_ERR_PROTO_FORMAT`"*). Today the set is 6. A standing carry's count moved, and #678 is
   the reason.

**Remedy FORKS ⇒ routed as DESIGN-Q, not self-applied:**
(a) add the member + `ERROR_META` entry and **bump both pins to 31 / PROTO: 5** — restores containment,
keeps the pins hardcoded and one-sided; or
(b) **derive** the pin from `errors.md` §2 instead of a literal — closes the asymmetry permanently but
makes the SDK suite read the spec, which it has never done.
(b) is the only option that would have caught this. Both are test-affecting. **Not an autonomous edit.**

### C.2 — `C374-N2` (MED) — the registry and the spec now assert different scopes for the same code

Per §B.3: **1 of 25**, against a 24/25 verbatim-agreement baseline. The registry's narrow
handshake-specific gloss predates #678's general one. One-line fix on its face (align `:52` to `:94`),
**but it interacts with N3** — if `W4_ERR_PROTO_FORMAT` is to absorb metering's format case, the
registry's narrow text is the wrong one to keep and the *broad* text is the right one; if it is not,
the narrow text may be correct and §2's gloss is over-broad. **Route with N3; do not fix in isolation.**

### C.3 — `C374-N3` (DESIGN-Q — **REOPENED, not re-charged**) — #678 removed the mechanism that a prior pass relied on to withdraw `B-C3`

`B-C3` (*"three competing 'format' names"*, filed C70, **0 of 9 received** — C334 left it behind on
purpose, deferral row 2). Its surviving member:

```
$ grep -rn "W4_ERR_FORMAT" (excluding docs/audits, PROTO_FORMAT)
web4-standard/protocols/web4-metering.md:110:- `W4_ERR_FORMAT`
```

**Exactly one occurrence in the entire repository.** No description, no status, absent from `errors.md`,
absent from `initial-registries.md`, absent from the SDK. Metering §6 lists **6** codes; **5** are in
the registry. Denominator: **1 of 6**.

**My predecessor holds the falsifier (v52), and I checked it before charging.**
`C298-registries-7th-delta-2026-07-31.md:149` **withdrew** the charge: *"Twelve of the eighteen are
sanctioned (8 ACP + 3 SAL + `W4_ERR_FORMAT`/metering). The charge of 'rogue minting' is withdrawn."*
That withdrawal was **correct on the artifacts as they stood**. §1 has two clauses — extenders may
*add* domain-specific codes (clause 1, which C298 applied), and they *"SHOULD reuse the codes defined
here where applicable rather than introducing parallel names"* (clause 2). On 2026-07-31, §2 contained
**no format code**, so clause 2's antecedent was false for this case. There was nothing to reuse.

The lineage named that mechanism explicitly. `C294:365`: *"the collision … is the predictable output of
**§2 having no code to reuse for that class**."*

**#678 removed that mechanism for the format class on 2026-08-10** — §2 now has a format code, and
`:96` glosses it as *"the core error for structural/canonical-format failures … Specifications …
SHOULD use this code unless a more specific subsystem error applies."* Clause 2 became applicable.

**A deflation is scoped to the artifacts it was measured on (v51/v42).** C298's withdrawal does not
automatically survive an input change — and it does not automatically fall either. The residual
question is a scoping judgment I cannot settle from the artifacts: **is metering's format error "a more
specific subsystem error", or is `W4_ERR_FORMAT` a parallel name that §2 now supersedes?** `:110`
carries no description, so there is nothing to compare. C334 itself read the two as one code renamed
(`C334:461`).

**Disposition: REOPENED as a dated question for the author. NOT re-charged, and C298's withdrawal is
NOT overturned** — its premise simply expired three days ago. Whoever answers it also answers N2.

### C.4 — `C374-N4` (LOW, cross-lineage) — `C354`'s disposition misattributes `afd04623`

`docs/audits/C354-acp-framework-9th-delta-2026-08-10.md:65-67` records:

> `afd04623` (#678) … `W4_ERR_PROTO_FORMAT` added to §2.6; **§1's delegation sentence** and
> Last-Updated revised … **§1's edit is what makes N1 citable at HEAD**

**§1 was not edited.** `afd04623`'s three hunks are `@@ -2,7`, `@@ -91,6`, `@@ -142,7`; §1's body is
line 9, outside all three:

```
$ git show afd04623:…/errors.md  | sed -n 9p | md5sum   →  94ff58120a57a33db05ba850de636e53
$ git show afd04623^:…/errors.md | sed -n 9p | md5sum   →  94ff58120a57a33db05ba850de636e53
```

The delegation sentence entered at `6189432d` (2026-06-17), 57 days ago. **C354-N1 survives** — §1 has
said it the whole time, so it was citable before #678 as well — but its *dated basis* is wrong. Same
shape as C338/C336-N4: the finding survives, the disposition does not. The `Last-Updated` half of
C354's cell is correct.

**Routing**: → the **acp** lineage (next slot **C394**), one-line correction to a disposition cell.
**Do not self-apply** — this pass does not edit another lineage's ledger.

---

## §D. Routed carry received — `C338-N1` **DISCHARGED**

`C338-registries-8th-delta-2026-08-08.md:114` routed a one-line fix into this lineage: *"restore the
locus as `web4-standard/QUICK_REFERENCE.md:193` and drop the `docs/what/specifications/
WEB4_QUICK_REFERENCE.md` row."*

**Locus verified to resolve exactly as written** (path tokens are their own class — every one gets
checked, including ones handed over by a reviewer):

```
$ grep -rn "web4\.io/errors" --include=*.md .        # excluding docs/audits
web4-standard/QUICK_REFERENCE.md:193:  "type": "https://web4.io/errors/invalid-lct",
```

**Ledger row `I2` — corrected locus, effective this pass:**

| Row | Field | Value |
|---|---|---|
| **I2** | Locus | **`web4-standard/QUICK_REFERENCE.md:193`** (sole locus in the repo) |
| | Superseded locus | ~~`docs/what/specifications/WEB4_QUICK_REFERENCE.md`~~ — has never contained the string |
| | Superseded anchor | ~~`c651c823`~~ — changed two lines about archiving a Python demo directory |

C338's own forward-check (`C338:201`) is satisfied by this row.

---

## §E. C334's deferral ledger — all 5 rows discharged

| # | C334's row | Disposition |
|---|---|---|
| 1 | Re-run the v28 inbound sweep **first** | ✅ **DONE, and it carried the pass.** Domain-word sweep bounded to the **24** audit docs *added* in the window (`git log --diff-filter=A`, not a filename glob — an unbounded `C3*.md` glob leaks June docs and I caught mine doing exactly that) returned **9** with hits; the two that mattered are `C340:65` (the family's other limb, §C.1) and `C354:65-67` (the misattribution, §C.4). |
| 2 | **B-C2 / B-C3 still 0-of-9 — left behind on purpose** | ✅ **B-C2 DEFLATED, retired** (v42): the corpus **discloses it at the point of use** — `initial-registries.md:56` reads *"`W4_ERR_RATE_LIMIT` - Rate limit exceeded **(same as `W4_ERR_AUTHZ_RATE`)**"*. A self-annotated alias is disclosed, not a defect. **B-C3 → N3**, reopened as a dated DESIGN-Q. |
| 3 | The `mcp.py` relocation (move the 6 cross-society codes to the empty `web4/mcp.py`) | ⏸️ **STILL OPEN, unchanged.** Per-module `W4_ERR_` counts re-measured: `acp.py` 9, `errors.py` 30, all others 0. **Now entangled with N1** — a relocation changes `len(ErrorCode)` and therefore collides with the same two pins. Sequence it *after* the N1 fork is chosen. |
| 4 | N4 is settled (`C16-H1-remainder` REFUTED) | ✅ **HELD, not re-raised.** Independently corroborated this window by `C366:427` (*"Retired. Do not re-route to `errors.md`; the answer is `C334-N4`"*). |
| 5 | Re-run the hub trigger | ✅ **NEGATIVE, both limbs, and the negative is recorded** (v43). 23 commits touched `hub/` in the window; `W4_ERR`, `error_code`, `problem_details`, `RFC 9457`, `about:blank` → **0 files each** over `hub/**/*.rs` (excl. `target/`). Do not re-litigate. |

---

## §F. Pre-registered trigger — **FIRED**

The standing note on **B-D1** (SSOT inversion, flagship, operator-**UNANSWERED**) carried a
pre-registered condition: *"now has a set relation, **24 ⊊ 31** — if either number moves without a B-D1
answer, that is the finding."*

```
errors.md §2 concrete codes ............... 25   (was 24)
initial-registries.md codes ............... 31   (unchanged)
```

**The relation is now `25 ⊊ 31`.** The left number moved, on 2026-08-10, and **B-D1 is still
unanswered.** The trigger fired exactly as written — recorded here, **not self-resolved**; B-D1 is
operator-gated and remains so. This is the pre-registration discipline paying its rent: the number was
committed to in advance, so the movement is a datum rather than a rediscovery.

---

## §G. Window, denominators, negatives

| Item | Value |
|---|---|
| Window | `C334` (2026-08-07) → HEAD (2026-08-13), pre-registered before §A |
| Commits in window | **58**, touching **47** files |
| Commits touching the target | **1** (`afd04623`) |
| Audit docs added in window | **24** (the inbound sweep's denominator) |
| Inbound residue with domain-word hits | **9 of 24** (excluding `C334` itself, the prior pass, which hits 33/42) |
| Mutation by this pass | **ZERO**; 1 new file |
| Probe hygiene | Complete fix applied in place, executed, reverted; `git status --porcelain` empty; `50 passed` restored |

**Negatives recorded** (a negative is what makes the positives interpretable): hub trigger 5 tokens ×
0 files despite 23 hub commits; `test_exactly_7_categories` and `test_vector_count` do **not** fire on
the fix (only 2 of 4 pins do); `W4_ERR_FORMAT` has **no** second occurrence anywhere; §2↔registry
description agreement is 24/25, i.e. the disagreement is **not** idiom; B-5 and B-H1 re-measured and
**unchanged**.

---

## §H. Deferral ledger for **C414** (next errors delta, = C374 + 40)

1. **Is N1 closed?** `python3 -c "from web4.errors import ErrorCode; print(len(ErrorCode))"` — **30 is
   the baseline; any change is the answer.** If it reads 31, check *which fork* was taken: are the pins
   still literals (fork a) or derived from `errors.md` (fork b)? Fork b is the only one that closes the
   asymmetry, and taking fork a silently is itself the next finding.
2. **Is the target still moving?** It was frozen 51 d and then moved. Re-derive the freeze from
   `git hash-object`, never transcribe. Baseline: `9cf077ba`, 157 L, `afd04623`.
3. **N3 is an author ruling, not a measurement.** Do **not** re-charge `W4_ERR_FORMAT`; check whether
   `web4-metering.md:110` still exists and whether anyone answered the scoping question. If §2's `:96`
   gloss was narrowed instead, C298's withdrawal is restored and B-C3 retires for good.
4. **N2 rides N3.** Do not fix `initial-registries.md:52` in isolation.
5. **Did C394 receive N4?** `grep -n "afd04623" docs/audits/C394-*.md` — the acp lineage owes a
   one-line disposition correction. If it is unreceived at C394, that is a routing failure to report
   (this lineage has now been on both ends of one).
6. **The B-D1 trigger has fired once.** Re-measure `25 ⊊ 31`. If either number moves again while B-D1
   is still unanswered, that is a *second* firing and the memo should say so.
7. **`mcp.py` relocation** — still open, now sequenced behind N1's fork.

---

## §I. Ledger row set

**17 rows carried in, 17 carried out, 0 dropped.**

`B-1, B-2*, B-4, B-5, B-8, B-9, B-H1, B-M1, B-M2, B-M3, I2*, I3, C16-H1(refuted, held), B-D1(fired),
C178-N1, C294-N1(+N4′), C294-N2`
**+ new**: `C374-N1`, `C374-N2`, `C374-N3`, `C374-N4`
**Retired**: `B-C1` (→ spec limb discharged; SDK limb continues as `C374-N1`), `B-C2` (deflated,
disclosed at point of use)
`*` = row edited this pass (B-2 count 7→6; I2 locus restored per C338-N1)

---

## §J. Method note — what this pass got wrong first

Recorded because the lineage's own rule is to publish the falsifier.

My opening premise called the SDK↔spec relation a **"1:1 invariant this lineage has published for 8
passes."** That is **false**, and policy review refuted it: the enum has always been a strict superset
(6 enum-only codes). The correct relation is **containment**, and — the part I had backwards — it is
not a lineage invention at all. `errors.py:4` and `:63` declare it. The finding got *stronger* when
corrected, which is the tell that the original was asserted rather than measured.

I also called `test_exactly_30_codes` **"the lineage's only numeric guard"** (there are four, and
**two** fire) and said it **"enforces the divergence"** (it does not — it prices the repair). Both were
overstatements reached by reasoning about the guard instead of running it. The executed
`2 failed, 48 passed` probe is the best evidence in this document and it exists only because the
overstatement was challenged.

**Carry (v53): an overstatement and a measurement can point the same direction — which is exactly why
the overstatement survives review unless someone runs it.** All three corrections above pointed at the
same conclusion I had already reached, so nothing *felt* wrong. The strengthened version came from
executing the claim, not from re-reading it. Where a finding is about a guard, the finding is not
made until the guard has been **run against the fix it is supposed to permit**.

Corollary, twice-earned this pass: **verify the reviewer's corrections too.** All five were confirmed
by independent command (docstring text, the second pin, the §1 md5 pair, the registry denominator, the
family row). And the reviewer's own probe number (`2 failed`) differed from my first attempt (`4
failed`) — the discrepancy was not an error in either, but the difference between a *complete* fix and
an *unfinished* one. A number that disagrees is a question, not a verdict.
