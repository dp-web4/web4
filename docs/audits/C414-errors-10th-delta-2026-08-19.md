# C414 — `errors.md` 10th delta audit

**Target**: `web4-standard/core-spec/errors.md`
**Date**: 2026-08-19
**Slot**: C414 (= C374 + 40, standing rotation arithmetic)
**Prior pass**: `docs/audits/C374-errors-9th-delta-2026-08-13.md` (PR #704)
**Lineage** (inclusive rule — every C-numbered delta plus the non-C-numbered
`…-internal-consistency-…` member, **of which this lineage has none** — re-verified this pass:
`ls docs/audits/ web4-standard/docs/audits/ | grep -i error` returns 10 files, all C-numbered):
C30, C66, C106, C138, C178, C216, C254, C294, C334, C374 → **C414 is the 10th delta, 11th pass**.
**Mutation by this pass**: **ZERO.** One new file (this document).

---

## §0. Headline

**The headline was killed. It is recorded here rather than deleted (v67), because the kill is the most
useful thing this pass produced.**

I drafted this: *ledger row **I2** states its predicate as a **class** — "a custom `type` URI … a
divergent practice" — but every pass re-measured it with a matcher pinned to one string,
`web4\.io/errors`; `C374 §D` published that matcher's output as **"sole locus in the repo"**; and the
class has a second member (`w4:err:witness`) the matcher structurally cannot return. Ten passes missed
it.*

**That is false, and the falsifier is in the lineage's own row titles.** Policy review read `C30:141`
verbatim and then read how the row was *carried*:

| pass | I2 as titled |
|---|---|
| C66:54, C106:50, C138:52, C178:55, C216:55, C254:55, C294:84 | "**`QUICK_REFERENCE.md` custom `type` URI**" — **7 of 7 instance-scoped** |
| C334:122 | matrix cell, bare `I2` (no title) |

The grammatical subject of C30's *"a divergent practice"* is QUICK_REFERENCE.md's shown URI, and its
remedy clause names one file. **I2 was born instance-scoped and was carried instance-scoped by every
pass that titled it.** So `C374:302`'s cell is **true of I2 as written**, not merely true of its
matcher. There is no instrument defect, no lost carry, no ten-pass miss. My class-reading was a
**retrofit onto a settled row** — which is precisely the drift this lineage's v65 carry names, arriving
from the other direction: I re-resolved a carry by a predicate *I* supplied instead of the one its
originating pass wrote down.

**21st consecutive killed headline.**

**What survives, at much lower severity and at a different locus than I proposed:**

**`C414-N1` (INFO–LOW, net-new).** `web4-standard/WEB4_WITNESSING_SPECIFICATION.md:89` declares a
Problem Details `type` value — `w4:err:witness` — in a **URI scheme the standard never defines**, while
`errors.md:9` names *witnessing* among the six domains it declares itself SSOT for and the witnessing
document cites `errors.md` **0 times**. It is invisible to every instrument: `grep -rn "w4:err"` over
**both** audit trees returns **0** across the entire corpus. Severity is capped by **modality** — 0
RFC2119 keywords on either side — so this is a **coherence** defect, not a conformance violation.

**`C414-N2` (ROUTE, not a charge).** The `protocols/` copy of the same file is inside the **D0** gate,
and C75 — D0's own evidence packet — scoped itself to the 8 files in `protocols/` and therefore never
saw that `protocols/web4-witnessing.md` is **byte-identical** to a root-level file the README calls
*"Canonical witness formats"* and which is **one day older**. That is a correction to route into the D0
memo, not a row for this lineage to take (v71).

---

## §A. Freeze check — **PASSED** (re-frozen)

```
$ git log --oneline -- web4-standard/core-spec/errors.md
afd04623 2026-08-10  docs(standard): fold hackathon findings into canonical Web4 text (#678)
6189432d 2026-06-17  spec(C67): remediate 3 autonomous C66 findings on errors.md (#347)
aaa2bd86 2026-06-04  fix(spec): resolve 5 autonomous-actionable C30 findings in errors.md (#269)
$ git hash-object web4-standard/core-spec/errors.md
9cf077bad906f2396e9006d214a89b9fce241193      # identical to C374's recorded baseline
$ wc -l web4-standard/core-spec/errors.md
157
```

The target moved **once** in its history-to-date at C374 and has not moved since: **re-frozen 9 days**
at `afd04623`. Baseline re-derived with `git hash-object`, never transcribed (C374 §H row 2).

---

## §B. The measurements

### B.1 — Standing carries, re-measured (never transcribed)

Matcher published with every count (v40): `W4_ERR_[A-Z_]+` **not ending in `_`**. The unfiltered regex
returns **31** for `errors.md` because it also matches the six §2.x heading prefixes
(`W4_ERR_BINDING_*` …). My first run published 31 and was wrong; the filtered form is the instrument.

| Carry | C374 | This pass | Verdict |
|---|---|---|---|
| **§2 concrete codes** | 25 | **25** | ✔ unchanged |
| **§2 ⊆ SDK containment** | 24 of 25 | **24 of 25**, sole missing member `W4_ERR_PROTO_FORMAT` | ✔ **`C374-N1` still OPEN, exact** |
| **SDK enum** `len(ErrorCode)` | 30 | **30** | ✔ **neither fork taken** |
| **B-2** registry-only codes | 6 | **6** | ✔ unchanged |
| **B-9** vector coverage | 5 of 25; 0 cross-society | **5 of 25; 0 cross-society** | ✔ unchanged |
| **B-H1** numeric registry orphan | 0 shared; 12 `0x000*` vs 25 | **0**; **12** vs **25** | ✔ orphan still total |
| **B-D1** relation | `25 ⊊ 31` | **`25 ⊊ 31`** | ✔ **no second firing** |
| suite (`tests/test_errors.py`) | 50 passed | **50 passed** | ✔ |
| suite (full SDK) | — | **2750 passed, 5 xfailed** | ✔ |

### B.2 — The `type` member, executed

`errors.md:30` defines `type` as `(OPTIONAL)`, defaulting to `about:blank`, and adds: *"use a specific
URI only for well-known, **dereferenceable** error types."* Three vocabularies exist in the corpus for
that member. Only one of them has an implementer.

| vocab | locus | tree | count |
|---|---|---|---|
| `about:blank` | `errors.md:17,104,117,130`; `protocols/web4-handshake.md:248`; `sdk/README.md:186`; all 5 test vectors | core-spec + SDK | **11** in `web4-standard/` |
| `https://web4.io/errors/invalid-lct` | `web4-standard/QUICK_REFERENCE.md:193` | quick-reference guide | **1** — this is **I2**, and it is I2's *whole* extent |
| `w4:err:witness` | `WEB4_WITNESSING_SPECIFICATION.md:89` + `protocols/web4-witnessing.md:89` + `forum/nova/web4-witnessing.md:89` | root + protocols + forum | **12** repo-wide over **6** files (3 `.md`, 2 archived `.py`, 1 STATUS doc) |

**Base rate, not a count (v69/v71).** The three `.md` copies are **byte-identical** —
`git rev-parse` returns blob `7984a8e5a0880218915bba6f85943017b58f261c` for all three. **Three files,
ONE authoring decision.** Reporting them as three loci would inflate exactly the way this lineage's own
carry forbids. My draft said "two loci" and was wrong in both directions: it missed the forum copy and
it counted copies as independent members.

**Is `w4:` defined?** No.

```
$ grep -rnE '`w4:`|"w4"|prefix\s+w4:' --include=*.md --include=*.json --include=*.jsonld --include=*.ttl web4-standard/
(0 hits)
```

Nearest hit is `architecture/grammar_and_notation.md:44`, a `w4-authority` **grammar production** which
explicitly disclaims itself: *"its canonical surface form is subject to an open repo-wide
identifier-scheme decision and is **not settled by this document**."* It is not a scheme registration.
`w4` is also **not** a JSON-LD prefix anywhere — the CURIE reading was tested and fails.

**Backed control (v43/v50) — the corpus knows how to define a scheme, and does:**

```
$ grep -n "single source of truth" web4-standard/core-spec/data-formats.md
147:The `web4://` URI scheme provides a way to identify … This section is the **single source of truth**
    for the scheme's structure; other documents … defer to this definition.
```

`web4://` is defined at `data-formats.md §6` (`:145` heading, `:147` SSOT sentence). So the absence of a
`w4:` definition is a **gap against the corpus's own demonstrated practice**, not a corpus idiom.

### B.3 — Executed: can anything see the divergence?

```
$ cd web4-standard/implementation/sdk && python3 -c "…Web4Error.from_problem_json…"
  errors.md default    accepted, roundtrip='about:blank'
  witnessing spec      accepted, roundtrip='w4:err:witness'
  NEG-CONTROL          accepted, roundtrip='w4:err:banana'     # v59: plausible-wrong, not a sentinel
  non-URI int          accepted, roundtrip=12345
  type OMITTED         accepted, roundtrip='about:blank'
```

`w4:err:witness` is accepted **identically to the negative control and to a non-URI integer**.

> **CORRECTED 2026-08-19 (rev1, in response to the #738 block).** The cell that stood here asserted an
> unqualified negative — *"there is no JSON Schema for the Problem Details envelope anywhere in the
> repo"* — sourced to `git ls-files | grep 'schema.*\.json$' | xargs grep -l 'problem\|W4_ERR'` → 1 file,
> *"a T3/V3 JSON-LD validation fixture."* **The count was wrong and the identification was wrong.** The
> replacement is below; it makes N1 stronger, because a measured non-discrimination beats an absence.

**B.3a — The instrument, corrected: three Problem Details schemas, and none of them can see it**

The pipeline as published returns one file, and it is not a T3/V3 fixture — it is the error-envelope
schema the sentence declared absent:

```
$ git ls-files | grep 'schema.*\.json$' | xargs grep -l 'problem\|W4_ERR'
forum/nova/web4-core-handshake-and-metering/schemas/problem-details.schema.json     # "Web4 Problem Details"
```

**The filter was defective in two stages, and the second is why the count read 1.** (i) `grep 'schema.*\.json$'`
is an *unanchored path* heuristic: it admits `web4-standard/test-vectors/schema-validation/*` on the
**directory** name — so the T3/V3 fixture does match the filename filter, contrary to the block comment;
it is excluded by the *content* grep — while excluding `web4-standard/test-vectors/errors/error-taxonomy.json`,
the normative tree's own error artifact. (ii) `grep 'problem'` is **case-sensitive** and the titles read
`"Web4 Problem Details"`. Three tracked schemas carry that title; the pipeline sees one of them, and that
one matched only through the lowercase path fragment in its `$id`:

```
$ git ls-files | grep '\.json$' | xargs grep -l '"title": *"Web4 Problem Details"'
archive/implementation-sprawl/tests/problem_details_schema.json                     # grep -c problem = 0, no $id
forum/nova/…/implementation/tests/problem_details_schema.json                       # grep -c problem = 0, no $id
forum/nova/…/schemas/problem-details.schema.json                                    # grep -c problem = 1, via $id
```

Executed against all three (`jsonschema` Draft 2020-12, `FormatChecker` **on**):

| schema | `type.format` | `type` required? | `w4:err:witness` | NEG `w4:err:banana` | `about:blank` | int `12345` |
|---|---|---|---|---|---|---|
| `forum/nova/…/schemas/problem-details.schema.json` | `uri-reference` | no | ACCEPT | ACCEPT | ACCEPT | REJECT |
| `forum/nova/…/tests/problem_details_schema.json` | `uri` | **yes** | ACCEPT | ACCEPT | ACCEPT | REJECT |
| `archive/…/tests/problem_details_schema.json` | `uri` | **yes** | ACCEPT | ACCEPT | ACCEPT | REJECT |

**3 of 3 accept the spec value and the negative control identically** — across both `format` values, and
regardless of whether the schema *requires* `type` at all. Two of the three demand the field be present
and still cannot tell `w4:err:witness` from `w4:err:banana`.

**The non-discrimination is SCHEME-level, and the two instruments differ (name them separately).** The
SDK parser (`Web4Error.from_problem_json`, §B.3) accepted the integer `12345`; all three schemas **reject**
it — `12345 is not of type 'string'`. So the corpus *does* discriminate on JSON type; what nothing
discriminates on is the **URI scheme**, which is precisely N1's axis. The original blanket "nothing in the
corpus can distinguish them" over-reached in the other direction and is withdrawn.

**Denominator, qualified (v40).** Under `web4-standard/` — the normative tree — there are **0 Problem
Details envelope schemas among 86 tracked `.json` files**. Stated without the qualifier this would be a
*third* false absence claim: the normative tree does contain a genuine error envelope,
`web4-standard/schemas/presence-protocol/v0/common/error_envelope.schema.json` (*"Presence Protocol —
Error Envelope (Mechanism A)"*, `required: ["_hestia_error"]`, sole property `_hestia_error`). It is
structurally **not** Problem Details — no `type`/`title`/`status`/`code` — so it is outside this finding's
class, and it is named here so the next pass does not rediscover it and conclude the 10th missed it.

**Corpus scope — routed, not re-adjudicated (v71).** Whether a `forum/nova/` schema counts as "the corpus"
already has a ruling from **this lineage's own 7th pass**: `C294:262` examined this exact file (blob
`18209449`, 2025-09-11) and ruled it *"a `forum/nova/` contributed artifact, not a promoted standard
artifact, so it is a mirror and not a peer."* That ruling stands and this pass applies it rather than
re-opening it: the schemas are mirrors, which is why the normative-tree denominator is reported separately
above. It is consistent with §B.1, where this pass already counted the `forum/nova/` witnessing copy as one
of the three byte-identical loci.

**v52 — the predecessor held the falsifier.** `C294:262` cited this file, with blob and date, **20 days
before** this pass declared it absent. The 10th pass did not need a new instrument to catch this; it needed
to read its own lineage. That is the same carry this pass published about its own killed headline (v72),
arriving a second time from the opposite direction.

**Correction addressed to the #738 block comment.** That comment is right that the returned file is the
Problem Details schema and not a T3/V3 fixture — the load-bearing half, and it is what unblocked this. Two
of its supporting cells do not survive re-running, both inherited from the same defective filter: (a) *"One
file, as you say"* endorses the count, which the case-sensitivity defect above shows is **3**, not 1; and
(b) *"The T3/V3 fixture … does not even match the filename filter"* — it **does** match
(`git ls-files | grep 'schema.*\.json$'` returns `…/schema-validation/t3v3-jsonld-validation.json`, on the
directory name); it is excluded by the content grep. Recorded per v52, and noted as the mirror image of
this pass's own error rather than as a deduction from the review.

**The omitted-`type` row is the strongest cell here and it came from the reviewer, not from me.** The
SDK *actively implements* `errors.md`'s `about:blank` default. So the shipped implementation and the
witnessing document disagree about the same field, and the implementation is on the spec's side.

### B.4 — Modality (v71 — check before calling a locus normative)

| locus | RFC2119 keywords | command |
|---|---|---|
| `web4-witnessing.md` §4 Error Handling (`:87–:90`) | **0** | `awk 'NR>=87&&NR<=90' … \| grep -cE '\bMUST\b\|\bSHOULD\b\|…'` |
| same file, whole document | 9 | `grep -cE … protocols/web4-witnessing.md` |
| `errors.md:30` `type` bullet | `(OPTIONAL)`, **0** on the *"dereferenceable"* clause | `grep -n 'OPTIONAL.*URI identifying'` |
| `errors.md` §1 Fields block (`:26–:36`) | 8 total: 4 `OPTIONAL`, 3 `REQUIRED`, 1 `SHOULD` | |

**Neither side is normative on this point.** That caps N1 at a coherence note. Calling it a violation
would have been the second error in the same headline.

---

## §C. Findings

### C.1 — `C414-N1` (INFO–LOW, net-new) — the standard declares a Problem Details `type` in a URI scheme it never defines

**Locus charged: `web4-standard/WEB4_WITNESSING_SPECIFICATION.md:89`** — and *only* that one. The
`protocols/` copy is inside the D0 gate (§C.2); the `forum/nova/` copy is inbound correspondence.

**Statement.** `errors.md:9` declares itself *"the single source of truth for core protocol error codes
(binding, pairing, **witnessing**, authorization, cryptography, and protocol errors)"* and §2.3 defines
the four `W4_ERR_WITNESS_*` codes. §1 lists the subsystem specs permitted to *extend* the taxonomy —
SAL §9, ACP §10, metering §6, MCP §7.6 — and **witnessing is not among them**, because witnessing is
core, already owned. Yet the witnessing specification declares its own Problem Details `type` value,
`w4:err:witness`, in a scheme the standard never defines, and **cites `errors.md` 0 times**
(`grep -c "errors\.md"` = 0 in both the root and `protocols/` copies; `errors.md → witnessing` = 1, the
SSOT sentence itself).

**Why the root copy and not the `protocols/` one.** `README.md:71` NAV-lists
`WEB4_WITNESSING_SPECIFICATION.md` as *"Canonical witness formats"*. C75's triage table never counted
it (`grep -n "WEB4_WITNESSING_SPECIFICATION"` on C75 = **0 hits**; C75's stated scope is *"All 8
documents in `web4-standard/protocols/`"*). So the root copy is **outside D0's gate** and is chargeable;
the `protocols/` copy is not.

**Severity: INFO–LOW, and here is why it is not higher.**
- Modality 0/0 (§B.4) — coherence, not conformance.
- **One authoring decision, not three** (§B.2) — the base rate is 1.
- The frozen date is `c963853b` **2025-09-13**; nothing has consumed it in the live tree since.
- Its only executable consumers are **archived**: `archive/reference-implementations/witnessing_spec.py:592,599`
  and `witnessing_attestation_spec.py:544` assert `doc["type"] == "w4:err:witness"` as conformance
  checks T6.1/T6.4, and `docs/history/STATUS-2026-02.md:1488` records it as shipped. So the value is
  **not inert** — it was implemented and asserted against. It is *stranded*, which is a different and
  milder thing. (Found by policy review; I had drafted "inert", which would have been false.)

**Novelty, matcher published (v44).** `grep -rn "w4:err" docs/audits/ web4-standard/docs/audits/` = **0
hits, both trees, entire corpus.** **9** audit docs name `web4-witnessing` — C27, C29, C30, C74, C86,
C114, C146, C302, C75 — and **none** touches its §4 Error Handling.

**"Invisible to the instrument" is NOT available as a defense, and this is the honest part.**
`C30:132` — this lineage's own founding pass — cites `web4-witnessing §1` by name, for the `w4idp:`
colon form of the pairwise identifier. The document was open on the desk at pass 1. §1 was read; §4 was
not. That is **v56 (novelty is per-LOCUS, not per-artifact)** costing this lineage eleven passes on its
own founding citation.

**Routing**: standard editor. Two mutually exclusive remedies — (a) align the value to `about:blank`
per `errors.md:30`'s stated convention, or (b) define a `w4:` scheme in `data-formats.md` alongside
`web4://` and register it. **Author ruling, not a measurement; do not self-apply.** Note (b) collides
with the open repo-wide identifier-scheme decision that `grammar_and_notation.md:44` defers to.

### C.2 — `C414-N2` (ROUTE to the **D0** memo — not a charge, not re-adjudicated)

C75 (`web4-standard/docs/audits/C75-protocols-cluster-lifecycle-triage.md`) is D0's evidence packet. Its
whole purpose, stated at `C75:113`, is that *"the operator now sees that the choice is **the same choice
four times**, with the evidence to make it once."* Its Group D row reads:

```
C75:42  | web4-witnessing.md | 2025-09-14 | ✗ (orphan) | 0 (1 STATUS) | none (scattered) | — |
C75:103 "BOTH frozen 2025-09, BOTH 0 NAV, BOTH 0 external NORM … maintaining BOTH is the defect"
```

**The measurement C75 could not make, because of its own scope rule:** `protocols/web4-witnessing.md`
is **byte-identical** (blob `7984a8e5`) to `WEB4_WITNESSING_SPECIFICATION.md`, which sits at the
standard's root, is NAV-listed by `README.md:71` as *"Canonical witness formats"*, and was committed
`c963853b` **2025-09-13 — one day earlier**. The root copy is the original; the `protocols/` one is the
derivative. C75 scoped itself to the 8 files in `protocols/` and so counted the derivative as a
`✗ (orphan)` with `0 NAV`, when the identical bytes at the root carry a README NAV entry calling them
canonical.

This does not change D0's answer and this pass does not attempt to. It changes D0's **evidence**: the
Group D choice is not "witness vs witnessing", it is "witness vs witnessing **vs the root copy of
witnessing**", and the `0 NAV` cell in the Group D row is an artifact of where the scope line was drawn.

**Per v71: a falsifier for a routed row is a correction to route, not a row to take.** The grammatical
subject of that sentence is C75/D0, not `errors.md`. **Written into the D0 memo's ledger; the errors
lineage claims no credit for it and takes no row.** Standing carry reaffirmed: *D0 unanswered ⇒ idle,
do NOT re-audit or self-decide the `protocols/` cluster.*

---

## §D. Policy review — verdict, and the reviewer's own corrections verified

Scope **APPROVED**; premise **DEFLATED** to §0/§C.1. Every reviewer cell was independently re-run
before adoption (v52 corollary — *verify the reviewer's corrections too*).

| # | Reviewer's correction | My re-run | Adopted? |
|---|---|---|---|
| 1 | I2 is instance-scoped; C30:141's subject is QUICK_REFERENCE.md; downstream passes title it so | **CONFIRMED**, with one adjustment: **7 of 8**, not 8 of 8 — `C334:122` is a bare matrix cell carrying no title | ✅ **kills the headline** |
| 2 | `w4:err` repo-wide is **12** hits over 3 spec files, not 2 loci | **CONFIRMED**: 12 hits / **6** files (3 `.md`, 2 archived `.py`, 1 STATUS) | ✅ |
| 3 | **Three** byte-identical blobs, not two — one decision, not three loci | **CONFIRMED**, `7984a8e5` ×3 | ✅ |
| 4 | `w4` is not a JSON-LD prefix/CURIE either | **CONFIRMED**, 0 hits | ✅ |
| 5 | The `protocols/` copy is inside the **D0/C75** gate ⇒ charging it contradicts my own out-of-bounds clause | **CONFIRMED** — decisive, and I had missed it | ✅ |
| 6 | `w4:err:witness` has live conformance consumers ⇒ "inert" would be false | **CONFIRMED**, `witnessing_spec.py:592,599`, `witnessing_attestation_spec.py:544` (archived, so *stranded* not *inert*) | ✅ |
| 7 | `C30:132` had the file open ⇒ "invisible to the instrument" unavailable | **CONFIRMED**, verbatim | ✅ |
| 8 | Duplicate is **not** disclosed anywhere ⇒ v45 does not deflate | **CONFIRMED**, 0 disclosure in all 3 headers | ✅ |
| 9 | Reviewer's added cell: **`type` omitted → SDK emits `about:blank`** | **CONFIRMED** — and it is the best cell in §B.3 | ✅ |
| 10 | *"`web4-standard/docs/audits/` is a second audit directory **the errors lineage has never swept**"* | ❌ **FALSE.** `C334:48` publishes *"`docs/audits/` = 211 docs; `web4-standard/docs/audits/` = 2 docs, **neither an errors doc**"*, and `C334:57` names both trees as the searched set. The lineage swept it **one pass ago** | ❌ **rejected** |
| 11 | Reviewer's repro *"does not run as written; `code` validates first"* | ❌ **FALSE.** My posted snippet used the valid code `W4_ERR_WITNESS_REJECTED` and ran; the transcript is in the session log. The reviewer evidently retyped it with an invalid code | ❌ **rejected** |

Rows 10 and 11 are recorded because the lineage's rule cuts both ways: a reviewer's correction is a
claim, and two of eleven did not survive being run. Neither affects the verdict — the kill rests on
row 1, which is the one I checked hardest.

---

## §E. C374's deferral ledger for C414 — all 7 rows answered

| # | C374 §H row | Disposition |
|---|---|---|
| 1 | `len(ErrorCode)` — **30 is the baseline, any change is the answer**; if 31, which fork? | **30. Neither fork taken.** `C374-N1` open, unchanged; containment **24 of 25**, sole missing member `W4_ERR_PROTO_FORMAT` (exact). The silent-fork-a hazard did **not** materialise |
| 2 | Is the target still moving? Re-derive with `git hash-object` | **No.** `9cf077ba`, 157 L, **re-frozen 9 d**. Derived, not transcribed |
| 3 | `W4_ERR_FORMAT` / `web4-metering.md:110` — author ruling, do **not** re-charge | Locus **still exists**, `protocols/web4-metering.md:110`, **1** live-tree occurrence. **Unanswered.** Not re-charged. §2's `:96` gloss was **not** narrowed, so C298's withdrawal is **not** restored and B-C3 does not retire |
| 4 | N2 rides N3 | **Held.** `initial-registries.md:52` not touched |
| 5 | Did C394 receive N4? | **NO** — `grep -n "afd04623" docs/audits/C394-*.md` = **0**. This is **already known**: MEMORY records `C374-N4` (with `C390-N2`) as **re-routed to acp `C434`**, now 4 passes old. Reported, **not re-charged** — the routing failure C374 pre-registered did occur, and its remedy is already in flight |
| 6 | B-D1: re-measure `25 ⊊ 31`; a second firing must be flagged | **`25 ⊊ 31`, both numbers unchanged. NO second firing.** B-D1 remains operator-**UNANSWERED** and is **not** self-resolved |
| 7 | `mcp.py` relocation, sequenced behind N1's fork | **Still open**, still sequenced behind a fork that has not been chosen |

---

## §F. Window, denominators, negatives

| Item | Value |
|---|---|
| Window | `C374` (2026-08-13) → HEAD (2026-08-19), **pre-registered before §A** |
| Commits in window | **47** |
| Audit docs added in window | **16** (`git log --diff-filter=A --name-only --since=2026-08-13 -- docs/audits/`) |
| Commits touching the target | **0** |
| Mutation by this pass | **ZERO**; 1 new file |
| Probe hygiene | read-only probes only; `git status --porcelain` empty apart from this document |

**v36 set difference — and the negative is what makes it interpretable (v43).** Domain-word sweep
(pre-registered token set `W4_ERR|problem details|9457|error taxonomy|errors\.md`) over the 16 in-window
audit docs returns **C378, C384, C386, C394**. The filename sweep (`errors\.md`) returns **the identical
4**. **Residue empty.** No inbound routing to this lineage; `C378:431` explicitly *"credits, not
claims"* C374's trigger report and rules `C374-N2` theirs-to-leave-alone.

**Negatives recorded**: 0 commits touched the target; B-D1 did not fire a second time; B-2/B-5/B-9/B-H1
all unchanged; `w4:err` = 0 across **both** audit trees; `w4` is not a URI scheme **and** not a JSON-LD
prefix; **all 3 Problem Details schemas in the repo accept `w4:err:witness` and the negative control
identically** (scheme-level non-discrimination — they *do* reject a non-string; §B.3a), and the normative
tree holds **0 of them**; the v36 residue is empty; the
`type`-omitted SDK path agrees with the spec.

**A denominator that moved and why**: `W4_ERR_*`-bearing files under `web4-standard/` reads **9** with
`--include=*.md` and **14** in `C378:123`, which counted `.py`/`.json` too. Neither is wrong; the
matcher travels with the number (v64).

---

## §G. Deferral ledger for **C454** (next errors delta, = C414 + 40)

1. **`len(ErrorCode)` is still 30 and `W4_ERR_PROTO_FORMAT` is still the sole gap.** Two consecutive
   passes with neither fork taken. **If it reads 31, check WHICH FORK** — literals bumped (fork a) or
   derived from `errors.md` (fork b). Fork a taken silently is itself the finding. This row is now
   **twice-deferred**; a third would be worth escalating as a stall, not re-asking.
2. **Freeze**: baseline `9cf077ba`, 157 L, `afd04623`. Re-derive with `git hash-object`.
3. **`C414-N1`**: did anyone rule? Check `WEB4_WITNESSING_SPECIFICATION.md:89` and whether `w4:` gained
   a definition in `data-formats.md §6`. **Do not re-charge if unruled — it is an author call.**
4. **`C414-N2` is ROUTED, not held.** Check the D0 memo received the root-copy correction. If D0 is
   still unanswered: **idle, do not re-audit the `protocols/` cluster.**
5. **B-D1 `25 ⊊ 31`** — third measurement. Two consecutive non-firings; a firing now is a *second*
   firing overall and the memo must say so.
6. **`C374-N4`/`C390-N2` at acp `C434`** — 5 passes old by then. If `C434` did not serve them, the
   re-route failed too, and *that* is the finding rather than the misattribution.
7. **v56 is this lineage's live hazard.** `C30:132` cited `web4-witnessing §1`; §4 went unread for 11
   passes. **Before claiming novelty, re-read the sections of already-cited files that no pass quoted.**
   Concrete next target: `errors.md §4`'s `application/problem+cbor` **SHOULD support** — this pass
   found **0** CBOR serializers in the live tree (`problem+cbor` appears only in prose) and did **not**
   charge it, because absence is not prohibition (v16) and the enforcement denominator was not measured.
   **Measure that denominator first** (row `I3`, content-type over transports, has been INFO since C178).
8. **Instrument note**: `web4-standard/docs/audits/` (2 docs, C33 + C75) is a real second audit tree.
   `C334:48/:57` swept it; **this pass found live evidence in it** (`C75`). Sweep it every pass, not
   once — a tree with 2 documents is cheap and one of them gates a cluster.

---

## §H. Ledger row set

**Carry-in is `C374`'s carried-out table ∪ `C374`'s own §C findings (v62 — a pass's findings are born
in §C and never enter its own carry table): 17 + 4 = 21 rows.**

`B-1, B-2, B-4, B-5, B-8, B-9, B-H1, B-M1, B-M2, B-M3, I2, I3, C16-H1(refuted, held), B-D1(fired once,
unanswered), C178-N1, C294-N1(+N4′), C294-N2, C374-N1, C374-N2, C374-N3, C374-N4(re-routed→C434)`

**21 carried in, 21 carried out, 0 dropped. + new**: `C414-N1`. **Routed out**: `C414-N2` → D0 memo.
**Retired**: none. **Row edited**: `I2` — *no change of substance*, but its scope is now **pinned in
writing as instance-scoped** (`QUICK_REFERENCE.md:193`) so that no future pass re-derives the class
reading this pass got wrong.

---

## §I. Method note — what this pass got wrong, and the carry

**v72: a retrofit reads a settled row's predicate off your own finding.**

Every element of my headline was individually true. `w4:err:witness` is real, undefined, uncited,
unvalidated, and unmentioned in 200+ audit documents. C374 did publish "sole locus in the repo." The
matcher `web4\.io/errors` genuinely cannot return `w4:err:witness`. I assembled true cells into a false
claim by supplying I2's predicate **from the finding I had just made** — reading "a custom `type` URI"
as a class because my new locus was a member of that class — instead of from `C30:141`, where the
sentence's grammatical subject is one file and the remedy clause names one file.

This is **v65 arriving from the opposite direction**. v65 says *re-resolve a carry by its PREDICATE, not
by its id*. The unstated half is that the predicate must be **read off the originating pass's own
words** — otherwise "re-resolving by predicate" becomes a licence to widen any old row until it covers
whatever you just found, and then charge the widening as a ten-pass instrument failure. The tell was
available and cheap and I skipped it: **the row's TITLE, as carried**. Seven passes titled I2
`QUICK_REFERENCE.md custom type URI`. One `grep` over the eight downstream row titles would have killed
the headline in ten seconds, before it was drafted.

**A retrofit is seductive in a way an ordinary error is not, because it makes your finding bigger.**
The class-reading upgraded a stranded 2025 line in a duplicated document into a ten-pass ledger failure
in the lineage's own instrument — from INFO-LOW to the flagship slot. That gradient is exactly why the
check has to be mechanical rather than judgmental.

**Corollaries earned this pass:**

- **The scope line of a routed gate is a fact about YOUR finding's locus, not just theirs.** I declared
  D0 out of bounds in §3 of the session log and then sited the headline inside the cluster D0 gates.
  Before charging a locus, grep the gating triage for the *path* — `grep -n "<basename>"
  web4-standard/docs/audits/C75-*.md` — not for the topic.
- **Three byte-identical files are one authoring decision.** Check `git rev-parse` on every copy before
  counting loci. I both under-counted the copies (missed `forum/nova/`) and over-counted the decisions.
- **An evidence packet's scope rule can invert its own cells.** C75 published `0 NAV` for a file whose
  identical bytes are NAV-listed as canonical one directory up, because its scope was "the 8 files in
  `protocols/`". Route that; do not re-adjudicate a gated decision.
- **"Invisible to the instrument" must be checked against your own lineage's founding pass.** C30 cited
  the file. Novelty was per-LOCUS (v56), not per-artifact, and saying so honestly is what keeps the
  finding at its true size.
- **Verify the reviewer's corrections too** — 9 of 11 confirmed, **2 falsified** (§D rows 10, 11).
  Adopting all eleven on authority would have put two false cells in this document.

