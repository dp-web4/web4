# C346 — `atp-adp-cycle.md` Eighth Delta Re-Audit (a carry this lineage *absorbed* was never reported back, and the row that absorbed it then narrowed to exclude what it absorbed)

**Date**: 2026-08-09
**Target**: `web4-standard/core-spec/atp-adp-cycle.md` (804 L, blob `2d060579`)
**Prior pass**: C306 (7th delta, 2026-08-01, PR #629), base `0fb9d952`
**This pass's HEAD**: `5fddf603`
**Lineage** (10 docs): C34 → C78 → C118 → C119 → C150 → C151 → C190 → C228 → C266 → C306 → **C346**
**Mutation**: **ZERO.** No spec, schema, SDK, vector, config or sibling file is edited by this pass.

---

## Headline

Target byte-frozen **33 days** (`256ab51d`, 2026-07-07). Window = **2** `web4-standard/` commits,
neither adding a single ATP token. Every C306 guard discharges. On the numbers this is the fourth
consecutive frozen delta and it should be empty.

It is not, and the reason is that **this lineage has been on the receiving end of the same failure it
charged one lineage over at C344 — with the sign reversed.**

At C344 a carry was routed to the mcp lineage six times over 74 days and never received. Here the
carry *was* received. On 2026-06-20 **C78 absorbed the ISP lineage's `C62-B11`** — the canonical
framing of ATP as *currency* vs *unit-of-account* — into its own **B1**, writing *"Subsumes carried
ISP-B11"* in a routing paragraph. Three things then happened, none of them noticed by eight
subsequent passes:

1. **The subsumption was never delivered back.** The token `ISP-B11` appears in **exactly one file in
   the repository** — C78 itself. The ISP lineage calls the row `C62-B11`. Sender and receiver used
   different names for the same row, so even a grep could not join them. **0 of 10** ISP-lineage
   documents contain the word *"subsum"*.
2. **The ISP lineage has published it as live and atp-owned in seven passes since, most recently two
   days ago.** C102 (06-25), C136 (07-04), C174 (07-11), C212 (07-17) and C250 (07-22) print it as
   `C62-B11`, with its subject matter; C290 (07-30) and C330 (**2026-08-07**) still carry it as a
   bare `B11` in an aggregate STAND row with no description at all.
3. **The absorbing row then shed the half it absorbed.** C78's B1 reads *"in coordination with
   **mcp §7.7 + ISP §4**."* From **C118 onward** — six consecutive passes, verbatim — B1 reads
   *"§5 abstract-FX vs **mcp §7.7** referent-grounding"*, and the evidence each pass publishes for
   *STILL OPEN* is **"mcp §7.7 unmoved."** That is a check which cannot see the ISP half at all.

C306 measured carry-row survival across nine labels and concluded **"No emptied ledger — unlike
C300's finding, this lineage's rows survive."** That conclusion is correct for the nine labels it
holds. It cannot see the tenth, because a census of the labels you hold is structurally blind to a
row whose label you dropped. → **N1.**

Two smaller net-new items follow from actually executing the artifacts rather than reading them
(**N2**, **N3**), and §E executes all three vector gates against this target and asks what each green
answers.

---

## Severity legend

| level | meaning |
|---|---|
| HIGH | a conformant implementation reading the spec is led into a wire-incompatible or unsafe result |
| MEDIUM | a normative statement is unsatisfiable, self-contradictory, or contradicted by the standard's own machine-readable artifacts, with no executable path today; **or** a ledger row's live status rests on evidence that cannot reach it |
| LOW | a defect in an in-standard artifact that does not change what a conformant implementation emits |
| INFO | a re-verification, an exclusion re-held, or an instrument note |

---

## §A — Freeze, collapsed to blob identity (the policy review struck the anchor table)

Per the C344 precedent, blob identity is strictly stronger than re-resolving anchors one at a time.
The whole atp mirror set, measured at `5fddf603`:

| artifact | blob at HEAD | last mover | date |
|---|---|---|---|
| `core-spec/atp-adp-cycle.md` | `2d060579` | `256ab51d` | 2026-07-07 |
| `schemas/atp-jsonld.schema.json` | `a8e07c0f` | `639cdebd` | 2026-03-21 |
| `schemas/contexts/atp.jsonld` | `a78531a0` | `639cdebd` | 2026-03-21 |
| `test-vectors/atp/transfer-operations.json` | `3b89dffc` | `a3b93713` | 2026-02-27 |
| `test-vectors/schema-validation/atp-jsonld-validation.json` | `11485cec` | `3495e135` | 2026-03-22 |
| `testing/conformance/atp-operations.json` | `31cbd900` | `92454d65` | 2026-05-14 |
| `deployment/config/demurrage.example.json` | `699ad842` | `0e547127` | 2025-12-05 |
| `web4-core/src/atp.rs` | `f5b0efe0` | `8857ab09` | 2026-05-13 |
| `implementation/sdk/web4/atp.py` | `efa5de3c` | `62524cf8` | 2026-05-24 |
| `test-vectors/validate_vectors.py` | `5259d473` | `a3b93713` | 2026-02-27 |

All ten frozen. Target blobs recorded at C266 and C306 both equal HEAD's. **Every C306/C266 anchor
row holds by byte-identity; no per-anchor re-resolution is published, because on an unchanged blob it
cannot return a finding.**

**Window.** `git log 0fb9d952..HEAD -- web4-standard/` = **2** commits — `8d3808db` (#637, the new
context-ref gate, §E) and `e4a62d7a` (#644, C320; its `web4-standard/` diff is citation tokens in
`FRACTAL_ROLE_IDENTITY.md` + 2 RFCs, all mrh). `git log -p 0fb9d952..HEAD -- web4-standard/ | grep
-icE '^\+.*\b(atp|adp|demurrage|slash_atp|mint_adp)\b'` → **0**. `web4-core/` = 1 commit
(`d43964e2`, `role.rs` only; `atp.rs` untouched). `hub/` = 25, repo-wide 58.

**Sibling drift.** The nine siblings `atp-adp-cycle.md` cites were last moved `d89595e8`
(2026-07-16), *before* C306 re-resolved them on 2026-08-01. Drift since C306 is provably zero; the
row is published as a measured negative rather than skipped.

---

## §B — Mirror set re-derived, and the directions swept

### B.1 — v36 inbound, both trees

`grep -rl "atp-adp-cycle" web4-standard/docs/audits/` → **0** (that tree holds exactly 2 files, C33
and C75). The second half of v36 discharges in one line, negative.

`grep -rl "atp-adp-cycle" docs/audits/` → **86** files, of which **10** are this lineage ⇒ **76
non-lineage documents name the target.** As literally specified, v36 would have me read all 76 — a
token sink, and the policy review said so. The reviewer's sharpening is what produced N1: **generalize
C306's own I-5 instrument** (which found that C158 named "atp-adp 2" among affected files and 0 of 9
atp docs ever mentioned it) into a **set difference** — rows in non-lineage documents that name
atp-adp *as an addressee* (owner / route / carry / owed), minus the rows this ledger holds.

Filtered to lines carrying both the target and routing language: **53 documents**. Hand-triaged, the
great majority are *disjointness* notes in the other direction (*"atp-adp is the correct side"*,
*"DISJOINT from the edit"*) — those are senders reporting that they need nothing. **The residue that
names atp-adp as the OWNER of an open row is `C62-B11`, carried in seven documents — the most recent
two days old — and it is not in this ledger.** → N1.

### B.2 — Third direction (v28): what cites the target

`git grep -l "atp-adp-cycle" -- . ':!docs/audits' ':!web4-standard/docs/audits'` → **42 files.**
Cross-referenced against the 10 lineage documents by basename:

| | count |
|---|--:|
| tracked files citing `atp-adp-cycle` (outside both audit trees) | **42** |
| ever named by any of the 10 lineage documents | **14** |
| **never named by any lineage document** | **28** |

Among the 28 unread: **`web4-standard/ATP_INTEGRATION_SUMMARY.md`** — an in-standard, ATP-subject
summary document, never read by any of ten passes over 64 days. It is where N3 lives. Also unread:
four `core-spec/` siblings (`LCT-…`, `SOCIETY_SPECIFICATION`, `acp-framework`, `r6-framework`),
`whitepaper/sections/09-atp-adp/index.md`, `docs/reference/CANONICAL_TERMS_v1.md` and
`docs/reference/GLOSSARY.md`. This is not a call to read all 28; it is the measured statement that the
lineage's frame has been the artifacts that *implement* the target.

### B.3 — Outward trees (v29), funded because they have real cardinality

C306's scope covered schemas, contexts, vectors, conformance, `deployment/`, `hub/`, SDK, `ontology/`
and core-spec fences — and **none** of `rfcs/ submission/ proposals/ profiles/ testing/ docs/`.
Measured over `web4-standard/`:

| tree | files mentioning `atp` | files citing `atp-adp-cycle` |
|---|--:|--:|
| `rfcs/` | 7 | **0** |
| `testing/` | 6 | **0** |
| `proposals/` | 5 | **0** |
| `docs/` | 4 | **0** |
| `submission/` | 3 | **0** |
| `profiles/` | 0 | 0 |
| **total** | **25** | **0** |

**Twenty-five outward files discuss ATP and not one cites the normative spec.** Published as a
measured negative, not charged: no individual citation is required, and charging a corpus-wide
citation idiom is the exact overcall C306's own §F warns against. It does sharpen C306-N1, though —
`testing/conformance/atp-operations.json`, the suite that minted the colliding identifier block, does
not cite the specification it claims to conform to.

### B.4 — SDK / code mirrors, and the standing false-mirror guard

`atp.py` blob `efa5de3c` and `atp.rs` blob `f5b0efe0` are byte-identical to C266/C306 ⇒ B3/B4/I2/
B6-SDK stand by construction. **I-2's false-mirror exclusion is HELD and was NOT re-counted**
(`lct.rs:585 slash()` = `LctStatus::Slashed`, LCT-lifecycle; `ledger.rs mint()`/`MintReceipt` =
LCT-genesis anchoring), per the standing per-file guard. `hub/`'s 25 in-window commits carry zero ATP
primitive — DISJOINT, C228 adjudication unchanged.

---

## §C — Findings

### N1 (MEDIUM, net-new, process/ledger) — a carry this lineage absorbed was never reported back, and the absorbing row then narrowed to exclude it

**The absorption.** `C78-atp-adp-cycle-delta-audit-2026-06-20.md:68` routes B1 as CROSS-TRACK/
DESIGN-Q and closes: *"atp-adp §5 should be reframed as referent-grounded … in coordination with
**mcp §7.7 + ISP §4**. … **Subsumes carried ISP-B11.**"* Repeated in its routing table at `:109`
(*"Subsumes ISP-B11"*) and its method note at `:134`.

**The subsumption was substantively defensible.** `C62:221` defines B11 as *"canonical framing of ATP
as 'currency' vs 'unit-of-account' (ISP §4.1 vs `atp-adp-cycle.md`). [cross-track owner =
atp-adp-cycle]"*, and C78's operator question — *"Is atp-adp §5 meant to describe inter-society
settlement at all … or only intra-society multi-currency bookkeeping?"* — would largely settle it.
**This finding does not dispute the merge.** It charges what happened to the record afterwards.

**Measurement 1 — the label exists in exactly one file.**

```
grep -rl "ISP-B11" docs/audits/            →  C78-atp-adp-cycle-delta-audit-2026-06-20.md   (1 of 196)
grep -ci "subsum" <10 ISP-lineage docs>    →  0, every one
```

The absorbing lineage wrote `ISP-B11`; the originating lineage writes `C62-B11`. **The two ledgers
never shared a token for the row**, so no grep either side could run would have joined them. This is
sharper than C344-N2, where at least the routed name was stable.

**Measurement 2 — the originating lineage has published it as live and atp-owned seven times since,
and the row degraded as it went.**

| document | date | the row, verbatim | form |
|---|---|---|---|
| `C62-…:221` | 2026-06-16 | *"**B11**: canonical framing of ATP as 'currency' vs 'unit-of-account' (ISP §4.1 vs `atp-adp-cycle.md`). [cross-track owner = atp-adp-cycle]"* | origin |
| `C102-…` | 2026-06-25 | `C62-B11` ×2 | described |
| `C136-…:115` (+ prose `:96`) | 2026-07-04 | *"C62-B11 … **OPEN, partially acknowledged** — atp-adp owner + operator"* | described |
| `C174-…:148` | 2026-07-11 | *"C62-B11 … **OPEN** — atp-adp owner + operator"* | described |
| `C212-…:142` | 2026-07-17 | *"C62-B11 … **OPEN** — atp-adp owner + operator; atp-adp frozen → unchanged"* | described |
| `C250-…:142` | 2026-07-22 | *"C62-B11 … **OPEN** — atp-adp owner + operator; atp-adp frozen → unchanged"* | described |
| `C290-…:283` | 2026-07-30 | *"B1, B2-full, B10, **B11**, B15 \| **STAND** (operator DESIGN-Q)"* | **bare label, no description** |
| `C330-…:95` | **2026-08-07** | *"B1, B2-full, B10, **B11**, B15 \| **STAND** (operator DESIGN-Q)"* | **bare label, no description** |

Seven passes across 43 days, each re-affirming an owner who had merged the row and did not know it
was still being carried. C136/C174/C212/C250 additionally list it in an **operator design-Q memo**
(`:143`, `:182`, `:180`, `:181`), so the divergence has been reaching the operator's queue as a
separate item. **The two most recent ISP passes carry it as a bare label in an aggregate row with no
subject matter at all** — C324's v23 shape (*collapse the narration, not the row count*) in its
failure direction: the label survived, the description that would let anyone notice the duplication
did not.

**And the ISP side's own re-check could not have seen it either.** `C290:75` records
`atp-adp-cycle | 256ab51d 2026-07-07 | DISJOINT — B5/B10/B11 stand`. The predicate is *did the spec
blob move?* The disposition lived in an **audit document**, which a spec-freeze check cannot reach.
v31 fires symmetrically: both ledgers re-verified the row correctly, against evidence that was
structurally incapable of containing the answer.

**Measurement 3 — the absorbing row narrowed, and this is the load-bearing half.**

| pass | date | B1 as published | evidence published for *STILL OPEN* |
|---|---|---|---|
| C78 | 06-20 | §5 reframe *"in coordination with **mcp §7.7 + ISP §4**"* — *subsumes ISP-B11* | — |
| C118 | 06-29 | *"§5 abstract-FX vs **mcp §7.7.1** normative referent-grounding"* | mcp §7.7.1 unchanged |
| C150 | 07-07 | same, mcp-only | *"mcp §7.7 unmoved"* |
| C190 | 07-13 | same, mcp-only | *"mcp §7.7 unmoved by C188"* |
| C228 | 07-19 | same, mcp-only | *"mcp §7.7 unmoved"* |
| C266 | 07-24 | same, mcp-only | *"mcp §7.7 unmoved"* |
| C306 | 08-01 | same, mcp-only | *"Neither side moved; mcp byte-frozen since C226"* |

`grep -c "unit-of-account"` over the ten lineage docs: **C78 = 1, C118 = 3** (both inside the *B7
References* row, a different item), **every other pass = 0.** `grep -c "\bC62\b"`: **C78 = 1, all
others = 0.**

So for six consecutive passes the row certified *STILL OPEN, direction unchanged* on a predicate —
**"did mcp §7.7 move?"** — that is structurally incapable of reaching the ISP §4.1 half it had
absorbed. This is **v31** applied to the lineage's own ledger: *an OPEN row licenses only the
predicate its evidence answered.* C306's §A.2 is explicit that it "re-derived direction, no
inversions" for B1; the direction it re-derived was atp-vs-mcp, because that is the only direction
the row's text still names.

**Measurement 4 — why the existing instrument could not catch it.** C306's §A.3 carry-row survival
census counts **B1, B2b, M2, ISP-B10, B3, B4, B6, X1, B8** — the nine labels the ledger holds — and
concludes *"No emptied ledger … this lineage's rows survive."* True, and blind by construction: a
census over the labels you hold cannot detect a row whose label you dropped. It is the same relation
as C344's between §A (re-resolve the anchors you have) and the inbound grep (find the rows addressed
to you).

**Four refutations attempted.**

1. *"B11 and B1 are the same question, so nothing is lost."* — **Fails on the record, not the
   merits.** Even granting full substantive equivalence (which this pass grants), the ISP lineage is
   carrying an OPEN row and routing it to an owner who has closed it into another row, and the
   operator memo lists it separately. Two ledgers disagree about how many open rows exist. That is a
   defect in the record whether or not the merge was right.
2. *"The ISP docs are simply stale — ISP's problem."* — **Fails on direction.** The document that
   created the divergence is `C78`, and it is this lineage's. The subsumption note lives in atp-adp
   prose and nowhere else. **v36 cuts both ways: this pass is the only one that has read both
   ledgers, so it is the one that can deliver.**
3. *"The narrowing is cosmetic; the operator will read C78."* — **Fails.** Nothing in C118→C306's B1
   row cites C78's subsumption clause, and C306 is the document an operator reads first. A row whose
   own description omits half its scope will be answered for the half it describes.
4. *"C306's census would have caught a genuinely lost row."* — **Fails, and this is measurement 4.**
   The census is over held labels. It is the instrument that certified *"no emptied ledger"* while
   the tenth row sat outside it.

**Severity: MEDIUM.** No spec byte is wrong and nothing a conformant implementation emits changes —
which caps it below HIGH. Above LOW because a design-Q the operator is being asked to answer is
mis-scoped in the ledger that will be used to answer it, and has been for six passes.
**Route: operator + ISP lineage.** Not auditor-applicable: whether to (i) re-widen B1's description
to name ISP §4.1 and mark `C62-B11` CLOSED-BY-SUBSUMPTION in the ISP ledger, (ii) split them back
apart, or (iii) leave the merge and simply reconcile the two ledgers' bookkeeping, is an owner's call.
**The corrective this pass can name is structural: a subsumption is a disposition, and a disposition
must be written into the ledger of the row being disposed of, not only into the ledger doing the
absorbing.**

### N2 (LOW, net-new, instrument → this ledger + operator) — C306-N1's "self-enforcing" routing option names a script that nothing executes

C306's §E routes N1 (the `atp-001`–`atp-005` namespace collision) with four options and this closer:
*"A duplicate-ID check in `test-vectors/validate_vectors.py` would make any choice self-enforcing."*

Measured at `5fddf603`, the file is executed by **nothing**:

```
grep -rn "validate_vectors" --include='*.yml' --include='*.yaml' --include='*.toml' \
   --include='*.cfg' --include='*.ini' --include='*.sh' --include='Makefile' --include='*.mk' \
   --include='*.py' .   [excluding the five copies themselves and docs/audits/]      →  0 hits
```

- `.github/workflows/` holds exactly four files (`build_whitepaper`, `ci`, `sdk-test`,
  `vector-context-refs`). None invokes it.
- No `Makefile`, `justfile`, `noxfile.py` or `tox.ini` exists at repo root.
- `implementation/sdk/pyproject.toml` `[project.scripts]` declares `web4` and `web4-mcp` only.
- `test-vectors/README.md` never mentions running a validator.
- The SDK's pytest suite reads the **vector JSON directly** (`test_atp.py:35`/`:490`
  `load_vectors("transfer-operations.json")`) and never touches the runner.

So a duplicate-ID check added there would fire only when a human ran the script by hand. **The word
that fails is "self-enforcing."** The routing option is not wrong about the fix; it is wrong that the
fix would enforce itself — and an operator picking option (i) on that basis would get a check nobody
runs.

**Two corroborating measurements, published because they are what makes it more than a word-choice
nit.**

- **The README points at a different validator that cannot see ATP.** `web4-standard/README.md:106`
  links `validate_vectors.py` — the **root** copy, blob `c5c9e5bf`, 180 L, last touched 2025-09-14 —
  as *"Standalone validator script."* It is a JOSE/COSE canonicalization checker:
  `grep -ci 'atp\|transfer\|demurrage'` → **0**. The ATP-aware 423-line runner lives at
  `test-vectors/validate_vectors.py` and is linked from nowhere. `grep -c "test-vectors"
  web4-standard/README.md` → **0**: the standard's index never names the tree holding all 35 of its
  published vector suites.
- **That 180-line file exists four times, byte-identical** (blob `c5c9e5bf`): `web4-standard/`,
  `testing/validator/`, `tools/`, and `forum/nova/validator/`. Two of the copies ship READMEs
  documenting `python validate_vectors.py --vectors-dir ./test-vectors`.

**Severity: LOW.** It changes nothing a conformant implementation emits, and the two ATP suites do
pass every gate that reads them. It is recorded as LOW rather than MEDIUM deliberately: the legend's
MEDIUM is about normative statements, and this is a defect in an audit ledger's routing text. It is
nonetheless **decision-affecting** — that is why it is a finding and not an INFO.
**Route: this ledger (amend C306-N1's option (i)) + operator/SDK track (wire a runner, or retire the
four stale copies and the README link).**

### N3 (LOW, net-new) — two in-standard pointers to an archived ATP document, from the same 2026-05-12 cleanup wave as C306-N2, one of them on the README's Getting-Started path

C306-N2 found `deployment/README.md` installing two files from a path they were deleted from by
`12ee197c` (2026-05-12). Applying **v35** — sweep the class, not the cell — every relative markdown
link in `web4-standard/` was resolved:

```
173 relative links checked.  5 broken.
  README.md:83                     -> core-spec/r6-framework-legacy.md      (deleted 4e195bdf, 2026-04-27)
  README.md:107                    -> implementation/tests/                 (dir never created; implementation/ holds reference/ + sdk/)
  README.md:229                    -> implementation/ATP_ADP_IMPLEMENTATION_INSIGHTS.md   <-- ATP
  README.md:230                    -> implementation/LCT_MINTING_PATTERNS.md
  ATP_INTEGRATION_SUMMARY.md:7     -> implementation/ATP_ADP_IMPLEMENTATION_INSIGHTS.md   <-- ATP
```

**Two of the five name the same ATP target** — the only doubly-cited broken link in the tree. It was
moved to `archive/implementation-sprawl/ATP_ADP_IMPLEMENTATION_INSIGHTS.md` by **`372b06aa`**
(2026-05-12, #178, *"archive 3 stray implementation/ markdowns"*) — the **same-day companion** of the
`12ee197c` sweep that produced C306-N2. So the 2026-05-12 cleanup broke in-standard pointers in at
least two files, in two syntactic forms (a shell `cp` path and a markdown link), and C306 found the
first pair only because it happened to read `deployment/`.

`web4-standard/README.md:228-229` is **step 3 of "Getting Started"**:

> 3. **Explore Examples**: Check implementation examples in [implementation/](implementation/)
>    - **NEW**: [ATP/ADP Energy Economy](implementation/ATP_ADP_IMPLEMENTATION_INSIGHTS.md) — Validated patterns from ACT blockchain (Jan 2025)

A first-time reader following the standard's own onboarding path to its ATP material gets a 404, from
a link labelled **NEW**. 89 days.

**Baseline, published so the charge is not an overcall.** 5 of 173 links (2.9%) are broken — this is
*not* a corpus-wide idiom, it is a small enumerable set, which is what makes it fixable rather than a
DESIGN-Q. ATP owns 2 of the 5, and with C306-N2 owns 3 of the ~6 known 2026-05-12 pointer breakages.
The target document still exists under `archive/`, so nothing is lost — only mis-pointed. **LOW.**
**Route: operator/author** (repoint or restore — the same open direction as C306-N2, and it should be
decided once for both).

---

## §D — C306's guards and the carry ledger

Every cell is a measurement taken this pass, at `5fddf603`.

| # | C306 guard | measured at HEAD | verdict |
|--:|---|---|---|
| 1 | is the `atp-001`–`atp-005` collision still live; renumbered or qualified? | id-collect over both suites: conformance ids ∩ vector ids = **`atp-001…atp-005`**, still 5 | **UNCHANGED** — C306-N1 stands, not remediated |
| 2 | were `deployment/README.md`'s two paths repointed, or the files restored? | both paths **MISSING**; both files still at `archive/reference-implementations/`; README last touched `0e547127` **2025-12-05** | **UNCHANGED** — C306-N2 stands; **and see N3** |
| 3 | target + `atp.rs`/`atp.py` blobs unchanged? | `2d060579` / `f5b0efe0` / `efa5de3c` — all three | **FROZEN** |
| 4 | I-2 false-mirror guard held, not re-counted? | `lct.rs:585` / `ledger.rs mint()` **not re-counted** as ATP mirrors | **HELD** |
| 5 | do NOT re-open: ontology term non-resolution · unparseable `json` fences · schema-validation vectors (23/23) · SDK `to_jsonld()`↔schema (3/3) | none re-opened; §E confirms the 23/23 and 3/3 by execution only, with the predicate named | **RESPECTED** |

| Carry | loci at C306 | loci at C346 | Status | Route |
|---|--:|--:|---|---|
| **B1** (§5 abstract-FX vs mcp §7.7) | 1 | **1 + 1 recovered** (ISP §4.1 half, absorbed at C78, absent C118→C306) | **OPEN — and MIS-SCOPED**, see N1 | operator + ISP lineage |
| **C62-B11** (ATP currency vs unit-of-account) | — | **1** (`C62:221`; absorbed into B1 at `C78:68`) | **RECEIVED this pass** as a ledger row; disposition is N1's routing question | operator + ISP lineage |
| **B2b** §5.3 exchange bypasses MUST #4/#5/#6 | 1 | **1** | HELD (DESIGN-Q; both sides in one frozen blob) | operator |
| **M2** §2.4 cap never references §6.1 `max_slash_per_event` | 3 (`:184`/`:194`/`:547`) | **3** | HELD by byte-freeze | operator |
| **ISP-B10** commitment-ATP charged-vs-allocated | 1 | **1** | HELD; ISP frozen since C63 | operator |
| **B3 / B4 / I2 / B6-SDK** | 4 | **4** | HELD; `atp.py` byte-frozen, schema-clean (C306 §B″.1) | SDK track |
| **X1** `lct:web4:` identifier | 1 | **1** | HELD (C33 corpus decision) | cross-track |
| **B8** (inbound, acp-owned) | 1 (`:621`) | **1** | STANDS; atp-adp §7.1 #5 is the correct-side referent | acp lineage |
| **C306-N1** vector-ID namespace collision | 1 | **1**, and see **N2** | HELD, **unchanged**; option (i) amended by N2 | operator/author |
| **C306-N2** deployment README install paths | 2 | **2**, and see **N3** | HELD, **unchanged**; class now has 3 known ATP members | operator/author |
| **I-1 / I-2 / I-3 / I-4 / I-5** | — | — | HELD as recorded at C306 | unchanged |

**No row lost a locus this pass. One row gained the ledger (`C62-B11`, 50 days late) and one row
(`B1`) recovered a locus it had shed six passes ago.**

---

## §E — The three vector gates, executed, scoped, and asked what their green answers

C304/C344 established that a green gate can be the defect. This target has **three** gates over its
vectors. All three were run; none of them is a lie, and none of them asserts what a reader would
assume.

| gate | wired to CI? | opens (atp) | reports | what the green actually answers |
|---|---|---|---|---|
| `test-vectors/validate_context_refs.py` | **yes** — `vector-context-refs.yml`, on `test-vectors/**` | 1 of 2 atp vector files | `atp.jsonld  OK  (21 refs, 1 files)` | every `web4.io` context URI **that is cited** resolves to a backing file |
| `test-vectors/schema-validation/validate_schema_vectors.py` | **no** | the schema-validation suite | `atp: 23/23 passed` (`ALL 278 VECTORS PASSED`) | two dataclass shapes match their schema |
| `test-vectors/validate_vectors.py` | **no** | `atp/transfer-operations.json` | `Results: 87 passed, 0 failed` | the transfer arithmetic reproduces |

Three observations, in ascending order of interest.

1. **The atp green is split, and the report does not say so.** All **21** of the context refs the
   first gate counts live in `test-vectors/schema-validation/atp-jsonld-validation.json`.
   `grep -c '@context' web4-standard/test-vectors/atp/transfer-operations.json` → **0**. The
   behavioural suite — the one 15 SDK citations point at, the one C306-N1 is about — contributes
   nothing to the green and is indistinguishable in the output from a suite that was verified. This
   is C344's §E result **inverted**: for mcp the gate was vacuous by total absence; here it is
   non-vacuous overall and vacuous for the file that matters.
2. **`validate_vectors.py` opens 2 of the 35 JSON files under `test-vectors/`** — hardcoded at `:109`
   (`t3v3/tensor-operations.json`) and `:245` (`atp/transfer-operations.json`) — and prints
   `87 passed, 0 failed` with no indication that 33 files were never opened. For once this is not an
   ATP blind spot but its opposite: **ATP is one of only two suites this runner covers, and the
   runner is executed by nothing** (N2).
3. **The schema gate cites this spec and covers none of its requirements.** `atp-jsonld.schema.json`
   `$defs` = `ATPAccount`, `TransferResult`; its own `description` names
   `web4-standard/core-spec/atp-adp-cycle.md` by path. §7.1 publishes **6 MUSTs** at `:617-622` (two-state, stake
   limits, society pools, charge-requires-value-proof, discharge-through-R6, T3/V3 tracking). The
   23/23 green covers **0 of 6**. This is the doc-specific, file-by-file form the C121 KEY SIGNAL
   demands — **no corpus-wide MUST sweep was run.**

**A candidate finding that died here, published because the corpse is the point.** `sdk-test.yml` —
the workflow that actually exercises the ATP vectors through pytest — is path-filtered to
`web4-standard/implementation/sdk/**`, so a commit editing `test-vectors/atp/transfer-operations.json`
alone does **not** trigger it, and the one workflow it does trigger is vacuous for that file (obs. 1).
That looked like a MEDIUM. It is not, and the refutation is a count: **since `sdk-test.yml` was added
(`270a5715`, 2026-03-27) there have been only **3** commits touching `test-vectors/` at all, and
**1 of the 3** failed to also touch `implementation/sdk/`** — and that one is `8d3808db`, the gate commit itself. The gap is latent, not
demonstrated. Recorded as **INFO**, routed to nobody, so that a future pass does not re-derive it as
new. (See §F.2 for how this number was got wrong the first time.)

---

## §F — Own errors

Published because a pass that reports only its findings is reporting half its instrument.

1. **The v36 inbound grep, run as literally specified, was a token sink — and the policy review
   caught it before any budget was spent.** `grep -rln "atp-adp-cycle" docs/audits/` returns **86**
   files where C344's equivalent returned a handful. Reading 76 non-lineage documents would have
   consumed the pass and returned the disjointness notes that make up most of them. The instrument
   that worked is a **set difference** (rows naming atp-adp as *addressee*, minus rows this ledger
   holds), and it is a generalization of C306's own **I-5**. **v36 names the direction to look; it
   does not name the filter, and on a heavily-cited target the filter is the whole cost.**
2. **A co-change count that was true and answered the wrong question (v31, on my own instrument).**
   §E's refutation was first computed over all history: **10 of 32** commits touching `test-vectors/`
   did not touch `implementation/sdk/` — 31%, which reads as a live gap. Nine of those ten predate
   `sdk-test.yml` (added 2026-03-27), so they cannot evidence anything about a workflow that did not
   exist. Re-scoped to the period the workflow has existed: **1 of 3**, and that one is the gate
   commit itself. The first number was not miscomputed; it answered *"how often do these trees move
   independently?"* when the question was *"how often would this workflow have failed to fire?"*
   **Both numbers are published, with their windows, rather than the convenient one.**
   *A second slip inside the same correction, caught only by the post-write re-run: the re-scoped
   figure was first written as "1 of 6" because the loop that produced it printed only its
   **numerator** — the three non-triggering commits — and the denominator was supplied from memory
   of the all-history run. It is **1 of 3**. An instrument that prints only the hits invites you to
   guess the total; print both or publish neither.*
3. **A cross-tool re-run that did not type its object (v34).** While clearing #680 earlier this fire,
   C306's role-block census was re-implemented with a different window and returned **69** blocks
   where the published figure was 53. The load-bearing sub-count (`entity`+`roleType` = 5, same five
   sites) reproduced exactly; the totals are **not comparable** and are not presented as agreeing.
   Recorded here as well as there because it is the third firing of v34 in this track and the lesson
   is not doc-specific: *a re-implementation is immune to derivation error, not to a different
   question.*
4. **Three of this document's own line cites were wrong on the first write, and the same sweep that
   cleared #680 four hours earlier is what caught them.** This fire opened by clearing a standing
   block on PR #680 whose entire content was three bad line cites, and whose lesson — the reviewer's
   words — is *a pass charging another lineage for an anchor it did not re-derive has to have
   re-derived its own*. That sweep was then run over this file before publication:
   - §7.1's MUSTs were first cited `:615-620`. `:615` is the **heading** and `:620` is MUST **#4**;
     the six MUSTs are `:617-622`. Off at both ends — the identical shape to #680's `:301` and
     `:340-347`, in the document written by the pass that had just been sent back for them.
   - The escrow note was first cited `:637-644`. `:637` is mid-note and `:644` is blank; the note is
     `:635-641`.
   - `C136-…:114` was published as one of the `C62-B11` rows. `:114` is **C62-B10**. C136's B11 table
     row is **`:115`**, and it does not read *"OPEN"* like the other three — it reads *"OPEN,
     **partially acknowledged**"*. Correcting the cite corrected the quotation.
   **Only re-derivation catches this class; re-reading does not.** All three cells looked right.
5. **The ISP-side measurement was materially wrong until the enumeration was widened (v24/v35).**
   N1's first draft said *"four ISP-lineage passes"* and *"0 of 5 documents"*, from a hand-listed set.
   Enumerating `docs/audits/*inter-society*` mechanically returns **10** documents, and the true
   figures are **seven** passes carrying the row and *"subsum"* absent from **all ten**. Two of the
   seven — C290 and C330, the most recent, one of them **two days old** — were missed entirely
   because they carry it as a bare `B11` inside an aggregate row and do not contain the string
   `C62-B11` the first search keyed on. **A disposition must name its members from an enumeration,
   not from a list you assembled while reading**, and a search keyed to a row's *described* form will
   not find the row after it has been collapsed to a label.
6. **Measurement instants.** Every count in this document was re-run against the tree **after** the
   findings were written; see §G. Two counts move if this file is included in their scope and are
   therefore scoped in words: §B.1's **86** and **76** are measured **excluding this document**
   (which now names the target), and §B.2's **42/14/28** excludes both audit trees by construction
   and does not move.

---

## §G — Disposition and instrument index

**Findings: N1 MEDIUM · N2 LOW · N3 LOW · 1 INFO (§E). 3 net-new. ZERO mutation.**

- **C347 = declared NO-OP.** N1 is operator + ISP-lineage owned (reconciling two ledgers is not an
  auditor's edit); N2 amends another pass's routing text and touches CI wiring; N3 is the same open
  direction as C306-N2 and must be decided with it. Do **not** self-fix `atp-adp-cycle.md`,
  `web4-standard/README.md`, `ATP_INTEGRATION_SUMMARY.md`, any C306 text, or any workflow.
- **Decide N3 together with C306-N2.** Both are "a 2026-05-12 cleanup moved a file and left a pointer
  behind"; answering them separately will produce two different conventions.
- **Delivered outward this fire, not merely routed** (v36 applied to this pass's own output):
  the two mechanical asks standing on PR **#678** were posted to that PR as a GitHub
  **suggestion block** plus a derived count, with receiver `dp-web4` and a re-check date named,
  rather than routed a third time through a session log. Re-check at the next fire touching
  `submission/` (security ≈ C376) or at atp **C386**, whichever is first.
- **Rotation** advances +2 → `multi-device-lct-binding.md` = **C348** (last audited C308).
  Next atp delta ≈ **C386**.

**Baseline for C386** (commits unless marked *blob*): target `256ab51d` (*blob* `2d060579`, 804 L;
§7.1 heading `:615`, its **6 MUSTs** `:617-622`, MUST-#6-scope note `:624-633`, escrow note
`:635-641`, §2.4 `:184`/`:194`, §6.1 `:547`, §5.3 `:511-512`, MUST #5 referent `:621`);
`atp-jsonld.schema.json` `639cdebd`; `contexts/atp.jsonld` `639cdebd`;
`test-vectors/atp/transfer-operations.json` `a3b93713`; `schema-validation/atp-jsonld-validation.json`
`3495e135`; `testing/conformance/atp-operations.json` `92454d65`; `deployment/config/demurrage.example.json`
`0e547127`; `web4-core/src/atp.rs` `8857ab09`; `sdk/web4/atp.py` `62524cf8` (*blob* `efa5de3c`);
`test-vectors/validate_vectors.py` `a3b93713` (*blob* `5259d473`).

**Guards for C386.**
1. **Check whether N1 was reconciled** — specifically whether `C62-B11` carries a disposition in the
   **ISP** ledger (not only here) and whether B1's description names ISP §4.1 again. A fix that
   widens B1 without closing the ISP row leaves the divergence intact in the other direction.
2. **Do NOT re-run a census over held labels and call it a ledger check.** Run the set difference:
   rows in non-lineage docs naming atp-adp as addressee, minus rows held. That is what found N1.
3. Check whether C306-N1's option (i) was amended (N2) and whether any runner became wired. If a
   duplicate-ID check appears in `test-vectors/validate_vectors.py`, **verify it is invoked** before
   recording it as enforcement.
4. Check the five broken links (N3) and `deployment/README.md` (C306-N2) **as one class**.
5. Do **not** re-open: I-2's false mirrors; ontology term non-resolution; unparseable `json` fences
   (C158-owned); the 23/23 schema-validation suite; the 3/3 `to_jsonld()`↔schema result; the §E
   path-filter candidate (refuted, 1 of 3); the 25 outward files' non-citation of the spec (measured
   negative, not a defect).

**Instrument index — every count re-run after the findings were written, at `5fddf603`.**

| claim | instrument | scope | result |
|---|---|---|---|
| target frozen 33 d | `git log -1 --format=%h -- core-spec/atp-adp-cycle.md` | 1 file | `256ab51d`, 2026-07-07 |
| mirror set frozen | `git rev-parse HEAD:<path>` × 10 | 10 files | table §A |
| window | `git log 0fb9d952..HEAD -- web4-standard/` | tree | **2** commits |
| window ATP tokens | `git log -p … \| grep -icE '^\+.*\b(atp\|adp\|demurrage\|slash_atp\|mint_adp)\b'` | window diff | **0** |
| second audit tree | `grep -rl "atp-adp-cycle" web4-standard/docs/audits/` | 2 files | **0** |
| inbound corpus | `grep -rl "atp-adp-cycle" docs/audits/` | 196 docs | **86** (10 lineage, 76 not) — *excludes this file* |
| addressee residue | routing-verb ∩ target regex, hand-triaged | 76 docs | 53 with routing language; **1 addressee row not held** (`C62-B11`) |
| `ISP-B11` label reach | `grep -rl "ISP-B11" docs/audits/` | 196 docs | **1** (C78) |
| `subsum` in ISP lineage | `grep -c subsum` × 5 docs | 5 docs | **0** |
| B1 narrowing | `grep -c "unit-of-account"` / `grep -c "\bC62\b"` × 10 lineage docs | 10 docs | C78 1/1; C118 3/0; others **0/0** |
| citation direction | `git grep -l "atp-adp-cycle" -- . ':!docs/audits' ':!web4-standard/docs/audits'` | tree | **42**; 14 named, **28** never |
| outward trees | `grep -rli atp` vs `grep -rl atp-adp-cycle` × 6 trees | `web4-standard/{rfcs,submission,proposals,profiles,testing,docs}` | **25** mention, **0** cite |
| validator invocation | `grep -rn validate_vectors --include={yml,yaml,toml,cfg,ini,sh,mk,py,Makefile}` | repo, minus the copies + `docs/audits/` | **0** |
| validator copies | `git rev-parse HEAD:<path>` × 5 | 5 files | 4 × `c5c9e5bf` (180 L) + 1 × `5259d473` (423 L) |
| README validator is ATP-blind | `grep -ci 'atp\|transfer\|demurrage' web4-standard/validate_vectors.py` | 1 file | **0** |
| README names the vector tree | `grep -c "test-vectors" web4-standard/README.md` | 1 file | **0** |
| broken links | resolve every relative md link | `web4-standard/**/*.md` | **5 of 173**; 2 are the same ATP target |
| gate 1 | `python3 test-vectors/validate_context_refs.py` | `test-vectors/**` | `atp.jsonld OK (21 refs, 1 files)` |
| gate 1 reach | `grep -c '@context' test-vectors/atp/transfer-operations.json` | 1 file | **0** |
| gate 2 | `python3 schema-validation/validate_schema_vectors.py` | 278 vectors | `atp 23/23`, all pass |
| gate 3 | `python3 test-vectors/validate_vectors.py` | 2 of 35 files | `87 passed, 0 failed` |
| §7.1 MUST coverage | count MUSTs `:617-622` vs schema `$defs` | 1 spec + 1 schema | **6 MUSTs, 0 covered** |
| ISP-lineage reach | `grep -c 'C62-B11'` / bare `B11` / `subsum` × 10 ISP docs | `docs/audits/*inter-society*` | **7 carry it** (5 described, 2 bare); `subsum` **0/10** |
| §E refutation | co-change of `test-vectors/` and `implementation/sdk/` | since `270a5715` (2026-03-27) | **1 of 3** (all history: **10 of 32** — §F.2) |
| C306 guard 1 | id-collect ∩ over both atp suites | 2 files | **5** ids still colliding |
| C306 guard 2 | file-existence on the 2 cited paths | 2 paths | both MISSING; README last touched 2025-12-05 |

---

## Pattern (C346)

**A carry can fail by being received.** C344's lesson was that routing is not delivery, because
delivery is an act of the receiver. This pass is the same relation one turn further on: **the receiver
acted, and the act was never reported back.** C78 did the *harder* and more correct thing — it read
another lineage's row, judged it to be its own question in different words, and merged it. Then it
wrote the disposition into a routing paragraph in its own document, under a label the sending lineage
had never used, and eight passes later the sender is still publishing the row as open and still
naming this lineage as its owner.

The second half is what makes it structural rather than clerical. A merged row's content has to live
somewhere, and it lived in B1 — until B1's own description drifted back to the half that had a live
counterparty. Six passes then re-certified B1 *STILL OPEN, direction unchanged*, and every one of
them was right about the predicate it checked. **`mcp §7.7 unmoved` is a true sentence that cannot
be evidence about ISP §4.1.** The row was never abandoned; it was answered narrowly, six times, by
passes doing exactly what the ledger asked.

**v37 (new): a subsumption is a disposition, and a disposition must be written into the ledger of
the row being disposed of.** Absorbing a carry creates two obligations the absorbing pass alone can
discharge — record the disposition where the *sender* will read it, and widen the absorbing row's own
description to cover what it took on. C306's carry census, which certified *"no emptied ledger,"*
was structurally blind to both, because a census over the labels you hold cannot see a row whose
label you dropped. → [[feedback_delivery_is_an_act_of_the_receiver]] /
[[feedback_ledger_emptied_not_closed]] / [[feedback_admission_row_is_not_examination]] /
[[feedback_class_not_cell]].
