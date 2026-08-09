# C342 — 8th-Delta Re-Audit of `protocols/web4-lct.md`: discharging C302's §D.7 deferral

**Date**: 2026-08-08
**Auditor**: Legion autonomous web4 track (slot `web4-20260808-180000`)
**Target**: `web4-standard/protocols/web4-lct.md` (278 lines, blob `5f68a5c7` — **byte-frozen since `27b85624`, 2026-02-17, 5.7 months**)
**Base**: `55c0ed7b` · **Window**: C302's baseline `a6959a8c` → HEAD = **58 commits**
**Type**: delta re-audit. **Read-only — zero file mutations outside `docs/audits/`.** The target is D0-gated.
**Lineage (8 documents)**: C60-B13 → **C74** (#363, 28 findings B1–B28) → C75 (#364) → C114 → C146 → C186 → C224 → C262 → **C302** (#625) → **C342**.

**Scope, as approved by policy review (and revised once).** The first proposal ran the full §A/§B/§B′
apparatus. The reviewer struck three of its four sections as **zero-yield by construction** and ruled
that the pass is **C302's §D.7 deferral** plus **one bounded no-motion attestation**. That ruling is
correct and this document is built to it: §A is short by design, §B is the session.

---

## Headline

C302 closed with a sentence it meant as a limit and which turned out to be the whole pass:

> *"The actual mirror comparison against the four newly admitted trees is NOT run in this pass … it is
> routed to the 8th delta by §D.7."* — `C302:263`, and again at `C302:542`: *"the largest known
> unmeasured surface on this lineage … should be the 8th delta's first work."*

**Four trees compared, four dispositions published, none exits as "admitted."** But the pass's largest
result did not come from any of them. It came from the one instrument the reviewer told me to re-run
rather than inherit.

- **N1 (MED, net-new, process/instrument → operator + rotation-wide).** **`C316-N1` was routed to this
  slot by number** — `C316:105` names *"the LCT lineage (`LCT-linked-context-token.md` **C328** /
  `web4-lct.md` **C342**)"* — and **C328, the first named addressee, received none of it**: `C316`,
  `E-M1`, `lct://`, `RECONCILIATION`, `transport` all measure **0** in C328. This is the **fourth**
  sighting of the non-reception mechanism and the **sharpest**: prior cases were routed by owner name;
  this one named the destination *slot number* and the *target file path*, pre-registered three
  regression greps, and still did not arrive.
- **N2 (LOW, mirror-set, → this lineage's own ledger).** C302 admitted `ledgers/` on the strength of
  **one** artifact, `reference/typescript/lct-document.ts` (`a29e1052`, 2026-02-19). The tree holds a
  **second, larger, one-day-newer independent implementation** — `ledgers/reference/go/lct/`, **2,007
  lines** across 6 files (`b3a5256c`, 2026-02-20) — named in **no** document of this lineage. It is
  the artifact `C316-N1`'s transport-grammar arm is measured against.
- **§D.7 discharged, 4/4**, incl. a NEGATIVE (`ontology/`) and a re-priced M-DECLINE (`demos/`).
- **Received and re-verified, not re-filed:** `C33 E-M1` + `C316-N1`. All **three** of C316's
  pre-registered regression greps re-run by the addressee — **all three unchanged**.
- **ZERO mutation. Nothing here edits any spec file. D0 remains operator-unanswered.**

**Own instrument error, published:** the reviewer handed me a window measurement (*"3 LCT-naming files,
all audit docs"*). Per v9 I re-ran it rather than adopt it. **It does not reproduce: 44, not 3** (§A.3).
The reviewer's matcher read **filenames only**; mine reads filenames *and* content. That number was
load-bearing for striking §B′ from the scope — the deletion still stands on other grounds, but **it was
argued from a number that was wrong by 14×**, and I would have shipped it unexamined had condition (a)
not been ruled in bounds.

---

## §A — No-motion attestation (bounded; replaces the struck §A + §B + §B′)

### A.1 — The four event triggers C302 pre-registered

C302 §D recommended C342 be **event-triggered**, *"recorded for the operator; not self-applied — the
rotation stands until the operator rules."* The rotation stands, so this pass runs. The triggers are
measured anyway, because C302 asked for them:

| Trigger | C302 baseline | HEAD | Motion |
|---|---|---|---|
| target `protocols/web4-lct.md` | blob `5f68a5c7` | blob `5f68a5c7` | **none** |
| canonical `core-spec/LCT-linked-context-token.md` | `d89595e8` | `d89595e8` | **none** |
| `web4-standard/schemas/lct.schema.json` | `9bcfe598` | `9bcfe598` | **none** |
| `web4-core/` | 0 commits | **1** — `d43964e2` `src/role.rs` | **fires** |

**Instrument:** `git rev-parse HEAD:<path>` for blobs; `git log --oneline a6959a8c..HEAD -- <tree>`
for motion. **This pass makes no cadence ruling.** It is **CADENCE datapoint 15**, routed to the
operator with the C324 memo. Deciding it here is on this pass's out-of-bounds list.

### A.2 — `d43964e2` (`role.rs`) — gated on subject matter, not on the fact that it moved

`d43964e2` *"a role's trust must accumulate per occupant, and rotation recorded nothing"* is the sole
`web4-core/` commit in the window. **Gate: NEGATIVE for this target, and already consumed by the
sibling.** `role.rs` carries `role_lct_id`/`filling_entity_lct_id` typed `Uuid`, which **C328 §D.2
already read and filed** as the third shipped face of `C288-N2` — and `d43964e2` (2026-08-05) is an
**ancestor of C328's base `b21da071`** (verified: `git merge-base --is-ancestor` → true), so C328 read
`role.rs` at or after this commit. It is `web4-core`'s **role-occupant** surface, not the §1 LCT
object; C336 independently M1-FAILed the same file for the security lineage. **No finding. Not
annexed.** The trigger fired; the artifact behind it was already owned.

### A.3 — Window artifact sweep — and the reviewer's number does not reproduce

**Instrument, published in full** (v21/v26 — matcher, root, filetypes, range, and the row count beside
the output count):

```
root:      repository top (/home/dp/.session-worktrees/web4-worker-web4-20260808-180000)
range:     a6959a8c..HEAD          filetypes: none (all)      tree: whole repo
matcher:   git diff --name-only a6959a8c..HEAD          -> 57 unique paths
           then, per path: PATH matches /\blcts?\b/i  OR  CONTENT matches /\blcts?\b/i
```

| measurement | value |
|---|---|
| unique paths in window | **57** |
| paths whose **filename** names LCT | **3** — `C302-…`, `C308-multi-device-lct-binding-…`, `C328-…` (all audit docs) |
| paths whose **filename or content** names LCT | **44** |
| output lines / table rows | 44 / 44 — **no line dropped** (v21) |

**The reviewer's figure was 3 and its stated basis was *"3 matching LCT, all three audit docs."* Mine
is 44.** The disagreement resolves exactly: **3 is the filename-only count** — reproducible to the
digit under `git diff --name-only … | grep -iE '\blcts?\b'`. It is not a wrong measurement; it is a
correct measurement of a different question, published as an answer to the question *"did the window
produce an LCT-naming artifact?"* Among the 41 it cannot see are **`web4-standard/rfcs/RFC-COMPOSITE-
ENTITY-IDENTITY.md`** (25 word-bound LCT hits), **`web4-standard/docs/FRACTAL_ROLE_IDENTITY.md`** (35),
and **`web4-core/src/role.rs`**.

**What this does and does not change.** It does **not** resurrect §B′: I read all three `web4-standard/`
movers and the sole edit to them in the window is `e4a62d7a`, the **C319 remediation** repointing five
stale `mrh-tensors.md:246` citations to `§5.1` — citation anchors only, no LCT subject matter. The
reviewer's *conclusion* survives. Its *premise* did not, and per its own ruling — *"if yours returns
anything other than 3, publish the disagreement as the finding and do not silently adopt either
number"* — the disagreement is published here rather than reconciled away.

**Second reviewer-number correction, same pass.** The §D.7 sizing was handed to me as **86 of 94
files** naming LCT, then self-corrected to **85** before I ran it. My independent re-derivation
(`git grep -liwE 'lcts?' -- <resolved path>`) returns **85 of 94**, and the single loose-only member is
`web4-standard/ontology/r7-action.jsonld` — the reviewer's correction reproduces exactly.
**Two published counts, from two different sources, each one high, in two consecutive fires** (cf.
C340's derivation sweep, C338's v17 re-run) — recorded for the method carries, not as a finding.

### A.4 — What holds by construction, and is therefore NOT re-run

Per the reviewer's change 2, these are stated, not performed, and **not billed as evidence**:

- **C74 B1–B28** — target byte-identical to the C74 snapshot ⇒ all target-internal rows hold by
  construction (**28/28**, 8th consecutive).
- **The four canonical line-anchors** (3.2 `:718`, B8 `:393`, B12 `:190-201`, B26 `:571`) — the anchored
  blob has not moved since 2026-07-16 and C302 re-resolved all four **against that same blob** on
  07-31, under a D0-gated ledger that cannot have re-typed them. Same input, same output.
  **v22's cheap test agrees**: `git log a6959a8c..HEAD -- <canonical> | wc -l` = **0** ⇒ no re-resolve
  owed. Re-running them and reporting agreement would be the apparatus padding the review struck.
- **C75 3.1 / 3.2, C114-N1, C172-N1** — all HELD; sources frozen; D0-blocked.

---

## §B — SPINE: C302 §D.7, the four-tree mirror comparison

### B.0 — Resolved paths, published BEFORE comparing (binding condition 1)

C302 §D.7 names its four trees informally. **Two of the four names do not resolve from the repository
root**, and a sweep rooted there would have returned zero for both and certified a false clean — the
v9 gate-scoped-to-the-wrong-tree failure, inside the section discharging it.

| C302's name | resolves at root? | **resolved path used here** | files | word-bound LCT |
|---|---|---|---|---|
| `implementation/sdk/tests/` | **NO** | `web4-standard/implementation/sdk/tests/` | 47 | 43 |
| `ontology/` | **NO** | `web4-standard/ontology/` | 7 | **5** |
| `ledgers/` | yes | `ledgers/` | 34 | 31 |
| `web4-standard/demos/` | yes | `web4-standard/demos/` | 6 | 6 |
| | | **total** | **94** | **85** |

**Matcher, one, stated once:** `git grep -liwE 'lcts?' -- <resolved path>`; file counts from
`git ls-files <resolved path>`. Loose (`-lie 'lct'`) differs on exactly one file, named in §A.3.

**Freshness caveat, per the reviewer's added condition.** `ledgers/` last moved **2026-02-20** and
`web4-standard/demos/` **2025-09-14** — both **older than the target's own freeze** (`27b85624`,
2026-02-17) in the `demos/` case. Where a tree exits "compared", the comparison is stated **against the
target at blob `5f68a5c7`**, which is the revision in force for all four trees' entire lifetimes.

### B.1 — `web4-standard/implementation/sdk/tests/` → **COMPARED. Divergence CONFIRMED BY EXECUTION.**

The target's §2.2/§2.3 and the canonical spec disagree on three rows this lineage has carried since
C74 — **B7** (entity_type: target enumerates **12**, canonical **15**), **B8** (`t3_tensor`/`v3_tensor`
absent from the whole target), **B9** (birth certificate lacks `issuing_society`). C302-N2 escalated
these on the ground that `lct.schema.json` *"already adjudicates B7, B8 and B9 in canonical's favour,
from inside `web4-standard/`."* That was a **declaration**. This tree makes it an **execution**.

```
cd web4-standard/implementation/sdk
python3 -m pytest tests/test_lct_jsonld_vectors.py tests/test_lct_jsonld.py -q
  → 175 passed in 0.18s
```

| target says | this tree asserts, green | site |
|---|---|---|
| §2.2 enumerates **12** entity types (no `society`, `policy`, `infrastructure`) | all **15** exercised, incl. `EntityType.SOCIETY` / `.POLICY` / `.INFRASTRUCTURE` (22 assertion sites) | `git grep -ohE 'EntityType\.[A-Z_]+' -- <tree> \| sort -u` = 15 |
| **no** `t3_tensor` / `v3_tensor` anywhere in 278 lines | *"Every JSON-LD document **must** have … `t3_tensor`, `v3_tensor`"* — asserted per-vector | `test_lct_jsonld_vectors.py:94-97` |
| §2.3 birth certificate has no `issuing_society` | `issuing_society` asserted on the birth certificate in **7** test files | `test_federation.py:63`, `test_integration.py:84`, `test_lct_jsonld.py:218`, … |

**Disposition: COMPARED — B7/B8/B9 are adjudicated in canonical's favour by a green, executed
conformance suite inside the standard.** A conforming implementation of the target's §2.2/§2.3 **as
written** fails these 175 tests. **This is a strength-escalation on C302-N2, not net-new** — same
rows, same direction, same operator bundle (adjudicate with D0/B-D1). What changes is that the
evidence moved from *a schema declares* to *a test suite executes*, which is what §D.7 was for.
**Not re-filed. Not self-applied.**

### B.2 — `web4-standard/ontology/` → **COMPARED. NEGATIVE — published as such (v7 rider 7, v24).**

C302 M-ADMITTED this tree on authority (a promoted `ontology/` artifact is a **spec peer** per C292),
noting it scores 0 on all three snake_case tokens and is nonzero only on `birthCertificate`.

**Comparison run; the tree defines no LCT object.** `git grep -ncE 'lct_id|birth_certificate|birthCertificate|LinkedContextToken|web4:LCT\b'` over all 7 files returns non-zero for exactly **three**, at **one or two lines each**:

- `web4-core-ontology.ttl:217` — `web4:birthCertificate a rdf:Property ;` (one property declaration; `:235` is a comment tallying it)
- `role-extension-schema.md`, `role-extension.ttl` — one hit each, both `EntityType::Role` in the **role-orchestration** lane

**No `lct_id`, no birth-certificate field set, no entity-type enumeration, no witnessing-role
enumeration.** The tree is a peer *of the standard*, but its subject matter is T3/V3, hub-law and role
extension — **not the §1 LCT object**. **Disposition: COMPARED → NEGATIVE. No divergence exists to
find.** C302's admission was correct on authority and is simply not load-bearing: a peer with nothing
to say about the subject cannot contradict it. **Guard for C382: re-check only if `ontology/` gains an
LCT class, an entity-type enumeration, or a birth-certificate shape.**

### B.3 — `ledgers/` → **COMPARED. → N2. C302 admitted the tree on one implementation; there are two.**

C302's admission, verbatim (`C302:252`): *"`ledgers/reference/typescript/lct-document.ts`
(`a29e1052`, 2026-02-19) is a full LCT document model that names `web4-standard/schemas/lct.schema.json`
as its source of truth … an independent implementation surface, not a consumer."* True, and it is the
**only** artifact the admission names — in the table row, in N2's evidence fold, and in §D.7.

**Measured: the tree holds a second independent implementation, in Go, that no document of this
lineage names.**

```
ledgers/reference/go/lct/     b3a5256c  2026-02-20  "Go LCT builder: fluent document construction with validation"
  document.go 511 · document_test.go 409 · uri.go 350 · uri_test.go 339 · builder.go 194 · builder_test.go 204
  = 2,007 lines, 952 of them tests
```

It is **larger than the TypeScript model, one day newer, and carries its own test suite.** Both
implementations agree with **canonical** and against the target on B7:

| implementation | entity types | site |
|---|---|---|
| TypeScript | **15** | `lct-document.ts:363-367` `VALID_ENTITY_TYPES` |
| **Go** | **15**, with the comment *"enumerates the 15 canonical entity types per entity-types.md (Feb 2026)"* | `document.go:13-31`, validated at `:339`/`:381` |
| **target §2.2** | **12** | `protocols/web4-lct.md:63` |

**And the Go tree is the load-bearing artifact for an inbound carry** (§C.1): `uri.go` is a 350-line
parser for the `lct://{component}:{instance}:{role}@{network}` **transport** scheme, and
`document.go:495` emits `fmt.Sprintf("lct://%s:%s:%s@%s", …)`. `C316-N1` measures its transport-grammar
arm against **`ledgers/reference/go/lct/uri.go:71`** specifically. So the artifact C302 did not name is
the artifact the carry routed *to this slot* depends on.

**Disposition: COMPARED → divergence is B7, already carried, direction canonical (see §B.1); the
mirror-set gap is N2.** Severity **LOW**: no verdict of C302 changes, the tree is frozen since
2026-02-20, and the B7 direction it confirms was already confirmed by three other artifacts. It is a
row because an admission that names one of two implementations reads as a swept tree — **v31**, and
this is its first application outside the lineage that bore it.

### B.4 — `web4-standard/demos/` → **COMPARED. M-DECLINE upheld on normativity; a third `lct_id` formula found.**

**v31 applies squarely here.** C302's disposition was *"M-DECLINED (non-normative example code), but
not silently."* That answers the predicate **"is it normative?"** It does **not** answer **"does it
agree with the target?"** — which is the question §D.7 asked. The decline is re-affirmed **and** the
comparison is run.

`hello_web4.py:33-36` derives an LCT id as:

```python
def generate_lct_id(entity_type: str, pubkey: bytes) -> str:
    h = hashlib.sha256(entity_type.encode() + pubkey).digest()
    return f"lct:web4:{b64(h[:16])}"           # base64url, TRUNCATED to 16 bytes
```

Set against the two forms already carried:

| source | preimage | encoding | width |
|---|---|---|---|
| **target §3 step 5** (`:147`) | `binding_proof` (the **signature**) | MB32 | full SHA-256 |
| `web4-core/src/lct.rs:361-364` `derive_lct_id` | `public_key` | `mb32:b` + base32 | full SHA-256 — **this divergence is C172-N1** |
| **`demos/hello_web4.py:35`** | **`entity_type ‖ public_key`** | **base64url** | **truncated to 128 bits** |

A **third** preimage, a **third** encoding, and a width no other artifact in the corpus uses. Emitted
into committed fixtures: `demo_alice.json` `"lct_id": "lct:web4:MFU-oSh_b217a7xYByUfTQ"`.

**Refutation run, and it succeeded in part — published (v4).** The obvious charge is that these ids
violate the standard's own schema. **They do not.** `lct.schema.json`'s pattern is
`^lct:web4:[A-Za-z0-9_:-]+$`; both demo ids **MATCH**, as does the canonical `lct:web4:mb32:b…` control.
The permissiveness C316-N1 charges elsewhere is exactly what absorbs this. **No schema violation.**

**Disposition: COMPARED → reach-escalation of C172-N1 (third derivation formula), LOW; M-DECLINE
upheld.** LOW and not higher because the tree self-labels *"Hello-Web4 (5-minute demo)"*, has **0**
product referrers (`git grep -rln 'hello-web4\|hello_web4'` outside the tree = 4 files, **all four are
audit docs or `forum/`**), and the ids validate. It is a row because it is the first artifact in the
corpus to truncate an LCT identifier, and because C172-N1's ledger records two formulas where three
exist.

### B.5 — §D.7 completeness: the deferral was real, and it was not the whole surface

C302 called these four *"the largest known unmeasured surface on this lineage."* Discharging it, I
re-derived the gate's own coverage. **The 16-row C302 gate has no row for six `web4-standard/` trees
that name LCT, nor for two root-level LCT fixtures:**

| never in the gate | files naming LCT (`git grep -lwiE 'lcts?'`) |
|---|---|
| `web4-standard/rfcs/` | **8** of 9 |
| `web4-standard/testing/` | **7** of 22 |
| `web4-standard/docs/` | 3 of 7 |
| `web4-standard/proposals/` | 3 of 5 (C302 ruled the *tier* — no authority over canon) |
| `web4-standard/submission/` | 2 of 4 — **the v29 outward tree** |
| `web4-standard/profiles/` | 1 of 4 |
| root fixtures | `web4-standard/test_lcts_rdf.json`, `web4-standard/test_lcts_simple.json` |

**This is recorded as a §E guard, not a §C finding.** It changes no verdict here, and charging it
would be re-running the gate — the work the review struck. But C302's *"largest known unmeasured
surface"* was a claim about a surface it had enumerated, and the enumeration was not complete.
**C382's first work is this table, not a re-read of it.**

---

## §C — Findings

### C.1 — N1 (MED, net-new, process/instrument → operator + rotation-wide). A carry routed to this slot by number did not reach its first addressee

**What was routed.** `C316` (presence 8th delta, 2026-08-05) filed **N1** as an explicit
reach-escalation of `C33 E-M1`, and routed it **out of its own lineage, by slot number**:

> `C316:105` — *"DECLINED here as a presence finding and its subject matter **routed to the LCT
> lineage** (`LCT-linked-context-token.md` **C328** / `web4-lct.md` **C342**)"*
> `C316:184` — *"Adjudicate WITH C33 E-M1; **routed to C328/C342** + the attestation-envelope owner"*
> `C316:202` — *"If C356 finds it still open, that is a **routing failure to report**"*

It named both target files **by path**, both destination slots **by number**, pre-registered **three**
regression greps, and published a refuted-guard list so the addressee would not re-charge the killed
version. It is the most carefully routed inbound item this rotation has produced.

**Reception at C328, the first addressee** (ran 2026-08-07, **two days later**, on the co-named target):

| token | occurrences in `C328-lct-linked-context-token-8th-delta-2026-08-07.md` |
|---|---|
| `C316` | **0** |
| `E-M1` | **0** |
| `lct://` | **0** |
| `RECONCILIATION` | **0** |
| `transport` | **0** |

**0 of 5.** Instrument: `grep -cF <token> <file>`. And in this lineage, `C302` scores `C316`=0,
`E-M1`=0, `lct://`=0 — though C302 predates C316 and is not charged.

**Why it did not arrive, and the honest exculpation.** Per the C336-N3 / C334-N2 rule, an inbound item
is received when written under an id the **owner's** ledger already types, and lost when written under
the **sibling's** id — *regardless of how explicitly the owner is named*. C316 wrote it as `C316-N1`;
the LCT ledger types `C24-*`, `C60-*`, `C172-*`, `C288-*`, `B1–B28`. **The one instrument that finds it
is the v28 third-direction sweep** — and it does, decisively:

```
git grep -nE "web4-lct\.md" -- docs/audits web4-standard/docs/audits | grep -viE "C[0-9]+-web4-lct"
  → docs/audits/C316-…:105  "routed to the LCT lineage (LCT-linked-context-token.md C328 / web4-lct.md C342)"
```

**v28 was born at C334 and C328 landed first** (C328 = PR #653, C334 = PR #663, same date 2026-08-07).
**C328 could not have run an instrument that did not yet exist**, and it is not charged with a method
failure. That is precisely what makes this a finding about the *routing mechanism* rather than about a
pass: everything a router can do was done, and it still took a method carry born **two days after the
route** for the item to land.

**What the addressee owes, discharged here.** C316 pre-registered three regression greps *"for C356"*.
As the co-addressee I ran all three at HEAD:

| C316's pre-registered check | was | at HEAD `55c0ed7b` | state |
|---|---|---|---|
| `grep -rlF "E-M1" .` (excl. `.git`) | **1** (C33 itself) | **2** — `C33` + `C316` | still **0** citations from any owning lineage; **64 days** |
| `attestation-envelope-jsonld.schema.json` `entity_id` has a `pattern`? | **no** | **no** — keys are `['description','minLength','type']` | unchanged |
| `LCT-SPEC-RECONCILIATION-2026-02.md` still claims the regex is *"intentionally permissive to accommodate both"*? | **yes, and false** | **yes** — `:116`, status ACTIVE | unchanged |

**Classification (v16 discipline, stated before the severity).** The `lct://` divergence itself is
**NOT net-new and is not re-filed here**: it is **`C33 E-M1`** (MEDIUM, cross-track, 2026-06-05),
reach-escalated by **`C316-N1`**. Both are **received into this ledger by name** (§F) and
**re-verified binary, not re-argued** (v10 rule 5). What is net-new is the **reception failure**.

**Severity MED.** Not LOW: the item is a live MEDIUM whose own escalation says a later pass finding it
open is *"a routing failure to report"* — and that report is due now, one addressee early. Not HIGH:
nothing is mis-stated in the standard as a result, no consequential act depends on it, and the item is
latent (the `entity_id` schema has no `pattern`, so nothing currently rejects).

**Route: operator, plus the rotation as a whole.** The corrective act is **not** a spec edit and **not**
a re-audit. It is that **routing by slot number is not a delivery mechanism**, and after four sightings
the rotation should stop treating it as one. Concretely, and **proposed, not applied**: an item routed
to slot N must be written into slot N's **carry ledger under an id that ledger already types**, by the
routing pass — the addressee cannot be relied on to discover a name it does not carry. §F does that
here for `E-M1`/`C316-N1` as the worked example.

### C.2 — N2 (LOW, mirror-set → this lineage's ledger). `ledgers/` was admitted on one implementation of two

Full measurement in §B.3. C302's admission names `reference/typescript/lct-document.ts` in the gate
row, in N2's evidence fold and in §D.7; `ledgers/reference/go/lct/` (**2,007 lines, 6 files, 952 lines
of tests**, `b3a5256c` 2026-02-20 — **one day newer** than the TypeScript model) appears in **no**
document of this lineage. Both implementations enumerate **15** entity types against the target's 12.

**Why it is a row and not a note.** C302's own §D.1 warns that *"inheriting even this corrected 12-tree
list reproduces the exact mechanism N2 records."* The mechanism turns out to operate **inside** an
admitted tree as well as across trees: a tree can be admitted, named, folded into a finding's evidence,
and still have half its subject-matter surface unnamed. **v8 says a mirror set can contract; this says
an admitted member can be a stand-in for its tree.**

**Severity LOW** — no verdict changes, the tree is frozen 5.5 months, and the B7 direction is already
established four ways. **Route: this lineage's ledger** (§F), not the operator.

---

## §D — Killed candidates (published, per *refute your BEST finding*)

1. **KILLED — "the demo's LCT ids violate the standard's schema."** The strongest-looking version of
   §B.4. `lct.schema.json`'s `^lct:web4:[A-Za-z0-9_:-]+$` **matches both** demo ids and the canonical
   control. Tested directly, not reasoned about. The charge survives only in the narrower
   derivation-formula form, at LOW.
2. **KILLED — "the corpus carries two colliding LCT identifier schemes."** This is C316's own R-1,
   **already refuted** by `LCT-SPEC-RECONCILIATION-2026-02.md:114-115` (status ACTIVE, 2026-02-19),
   which ratified the transport-vs-identity split. **Do not resurrect without first overturning that
   decision.** Inherited as a refuted-guard, re-verified present at HEAD, not re-opened.
3. **KILLED — `E-M1` / the `lct://` scheme as net-new.** Owned by `C33` (`web4-standard/docs/audits/`),
   escalated by `C316-N1`. Received and re-verified (§C.1, §F); **not re-filed, not co-claimed.**
   This is the C302 §E.1 discipline applied to an inbound rather than a sibling-parallel finding.
4. **KILLED — `d43964e2`/`role.rs` as an LCT finding.** Fires the event trigger; already owned by
   `C288-N2` via C328 §D.2, and M1-FAILed for security by C336. §A.2.
5. **KILLED — a §B′ resurrection off the 44-vs-3 disagreement.** The reviewer's premise was wrong; its
   conclusion was not. The three `web4-standard/` movers the filename matcher missed were touched by
   exactly one commit, `e4a62d7a`, the C319 citation-anchor remediation — no LCT subject matter.
   **Reported as an instrument correction (§A.3), not used to reopen struck scope.**
6. **NOT re-derived, per standing guards:** C302's 16-tree gate (re-derivation is C382's, §E) ·
   §E.1's vector-vs-schema failures (= `C288-N1`, sibling-owned) · Rust `EntityType`=9 (= `C176-N1`) ·
   `§1 rotate`/context-3-vs-5/revocation-2-vs-3 (= B3/B2/B4) · the `peer` 8th witnessing role
   (= `C302-N3`, witness-registry track).

---

## §E — Self-corrections and post-write re-runs at a different scope (v17, amended)

Every number above was re-run after its section was written, at a different **root** and with a
different **tool** than it was drafted with — **including this pass's own gate cells**, which is the
C338 amendment.

1. **CAUGHT (reviewer's cell, not mine — but I ran it): 3 vs 44.** §A.3. Would have shipped as an
   inherited premise. The re-run was in bounds only because I asked first; the lesson is that
   **the question a number answers must be published beside it**, since 3 and 44 are both correct
   measurements of different questions.
2. **CAUGHT (reviewer's cell): 86 → 85.** Self-corrected by the reviewer before I ran it; my
   independent derivation reproduces **85** and the same loose-only member. Two reviewer counts, both
   one high, in one review.
3. **CAUGHT, mine — and I made the defect myself, by measuring.** The §B.0 tree sizes were drafted
   with `git ls-files` (**94** files). Re-run with `find <tree> -type f` they are **96**. The two
   extra are
   `web4-standard/implementation/sdk/tests/__pycache__/test_lct_jsonld{,_vectors}.cpython-312-pytest-7.4.4.pyc`
   — **bytecode that did not exist until §B.1 ran pytest against that tree.** They are gitignored
   (`.gitignore:11`), so **94 is the correct figure** for an audit of the repository and the table
   stands; but the honest statement is that **the act of measuring changed the thing measured**, and
   only a second tool at a second root could see it. This is C340's mechanism — *the audit doc entered
   the corpus it measures* — recurring one fire later via an **execution** rather than a document.
   **Method note for the carries: when a pass runs code against a tree it also counts, take the count
   before the run, or take it from the index rather than the filesystem.**
4. **CAUGHT, mine: the Go test-line total.** Drafted **948**; `wc -l` gives 204 + 409 + 339 = **952**.
   A plain arithmetic slip in the finding that is *about* an under-named artifact. Corrected in §B.3
   and §C.2. Neither the finding nor its severity depends on the cell.
5. **Re-run, held:** the four trigger blobs, under `git rev-parse HEAD:<path>` (drafted) and
   `git log --oneline -1 -- <path>` (re-run) — agree.
6. **Re-run, held:** the per-tree **LCT** counts, drafted with `git grep -liwE` and re-run with
   `grep -rliwE` over the filesystem — **85** both ways, and unchanged by the `__pycache__`
   contamination (`.pyc` files do not match the word-bound matcher), which is why the LCT column
   survived an error the file column did not.
7. **Re-run, held:** the C328 reception zeros, drafted with `grep -cF` and re-run with `grep -oF |
   wc -l` over five distinct tokens rather than one — **0 for all five**, so the zero is not an
   artifact of a single spelling or of `grep -c`'s line-vs-occurrence ambiguity (v13 rider 8).
8. **Re-run, held:** the window sweep, drafted with `git diff --name-only` + `git grep` and re-run
   with `find`/`LC_ALL=C grep` — **57 paths / 3 filename-only / 44 filename-or-content**, identical.
   The two numbers that disagree with the reviewer disagree by the same amount under both tools.
9. **v21 line-count check:** the window sweep emitted **44** matching paths; the table reports **44**.
   The §B.0 resolution table has **4** rows for **4** trees. No line dropped between stdout and table.
10. **Ambiguity published, not resolved in my favour:** C328 and C334 share the date 2026-08-07, so
   "was v28 available to C328" is decided by PR number (**#653 < #663**, verified in the merge log),
   not by date. Stated as such in §C.1 rather than asserted.

---

## §F — Carry ledger after C342 (every id named individually — v19/v23/v24)

**Row count: 14.** Ids received from other lineages are written **under this ledger's own typing**, per
N1's proposed corrective.

| ID | Class | State after C342 |
|---|---|---|
| **B1–B28** | C74 | **28/28 HELD, 0 regression** (8th consecutive; holds by construction, §A.4). Anchors as corrected by C302-N1: 3.2 `:718`, B8 `:393`, B12 `:190-201`, B26 `:571` |
| **B7 / B8 / B9** | C74, cross-doc | HELD — **now adjudicated in canonical's favour BY EXECUTION** (§B.1, 175 green tests) and by **two** `ledgers/` implementations (§B.3). Direction unchanged; evidence strengthened. Operator bundle with D0/B-D1 |
| **C75 3.1 / 3.2** | structural | HELD-REAL; `README.md:64`, canonical `:718`; sources frozen |
| **C114-N1** | internal `claims` contradiction | HELD; D0-blocked |
| **C172-N1** | `derive_lct_id` key-derived | HELD — **reach: a THIRD formula** (`demos/hello_web4.py:35`, entity_type‖pubkey, base64url, 128-bit). §B.4 |
| **C302-N2** | reach-escalation on B7/B8/B9 | **→ OPERATOR**, unchanged in routing; **strengthened** by §B.1 |
| **C302-N3** | 8th witnessing role `peer` | **→ witness-registry track**; not re-opened |
| **C342-N1** | **NEW — MED, process/instrument** | Routing-by-slot-number failed at its first addressee; 4th non-reception sighting, sharpest form. **→ operator + rotation-wide.** §C.1 |
| **C342-N2** | **NEW — LOW, mirror-set** | `ledgers/` admitted on 1 of 2 implementations; `reference/go/lct/` (2,007 L) unnamed in 8 passes. **→ this ledger.** §C.2 |
| **E-M1** | **RECEIVED (C33, MED, cross-track)** | `lct://` scheme defined in no spec. **OPEN, 64 days, 0 citations from any owning lineage.** Re-verified binary at HEAD, not re-argued. Adjudicate **with** C316-N1 |
| **C316-N1** | **RECEIVED (MED, reach-escalation on E-M1)** | `LCT-SPEC-RECONCILIATION-2026-02.md:116` (ACTIVE) declines the divergence on a premise that is false; **all 3 pre-registered regression greps re-run, all unchanged** (§C.1). Adjudicate **with** E-M1 + the attestation-envelope owner |
| **D0** | DESIGN-Q | **operator-unanswered; gates all `protocols/` remediation.** Read-as-evidence split upheld (C296/C336 posture): this pass read the target and laid **no finding against it** |
| **B-D1** | flagship SSOT inversion | unanswered |
| **CADENCE** | DESIGN-Q | **datapoint 15**, routed with the C324 memo. **Not decided here** |

---

## §G — Guards for the next delta (C382)

1. **FIRST WORK: §B.5's table, not a re-read of it.** Six `web4-standard/` trees and two root-level
   LCT fixtures have never had a gate row. Run the subject-matter predicate over each, publish a
   per-member disposition including NEGATIVEs. `submission/` is the v29 outward tree and should be
   taken first — C336 found a pre-remediation crypto suite living there for four passes.
2. **Re-derive the 16-tree gate, do not re-read it** (C302 §D.1, still live). **And check inside each
   admitted tree** — C342-N2 shows an admission can name one artifact and stand in for a whole tree.
3. **Check `E-M1` / `C316-N1` first.** If either is still open and still uncited at C382, that is the
   *routing* failure escalating, not a new LCT finding. Pre-registered, unchanged: `grep -rlF "E-M1" .`
   = **2**; `entity_id` `pattern` = **absent**; `LCT-SPEC-RECONCILIATION-2026-02.md:116` = **present
   and false**. **Do not re-charge the ratified transport/identity split** (§D.2).
4. **Run v28 before §A, every pass.** It is the only instrument that found this pass's largest result,
   and the sweep command is in §C.1 verbatim with this target substituted.
5. **Anchors: apply v22's cheap test, don't perform the re-resolution.** `git log <lastpass>..HEAD --
   <canonical> | wc -l`; non-zero ⇒ re-resolve all four by content; zero ⇒ state that it holds by
   construction and move on. Re-running it and reporting agreement is padding.
6. **`web4-core/` has fired the trigger once on a file that was not this lineage's** — re-gate on a
   §1/§2/§3 LCT primitive or an own signing preimage, phrased as a **behaviour**, not as `role.rs`.
7. **Publish the QUESTION a count answers, not just its matcher** (§A.3's lesson). 3 and 44 were both
   right. v26 fixes the window; this fixes the predicate.
8. **Cadence:** datapoint 15. Target frozen 5.7 months; 3 of 4 triggers negative; and the pass still
   yielded a MED — **from the inbound sweep, not from the target.** That is itself evidence for the
   operator's cadence question: what pays here is no longer the file.

---

## Accountability self-audit

```
surface: C342 audit document   act: publish audit findings that route an operator decision
S: low/reversible [construct: read-only; sole write is this new file under docs/audits/; zero spec, schema, vector or code mutation]
R: n/a [construct: no caller-driven path created]
W: n/a [construct: no identity or authority asserted; every finding routes, none decides]
O: pass [construct: §D refutations and the §B.0 path resolution precede §C authorship; the demo-vs-schema charge was killed pre-write, and the four §D.7 dispositions were measured before any was written]
A: pass [construct: every count carries its matcher, root, filetypes and range; every zero names its token; §E publishes the post-write re-runs and both inherited-number corrections, including the one that was load-bearing for my own approved scope]
V: present [construct: §D kill-list — the pass killed its own strongest candidate and declined to reopen scope the review had struck, on a premise the review got wrong]
verdict: PASS
```

*No file outside `docs/audits/` was created or modified. `protocols/web4-lct.md` is untouched; D0 is
unanswered and stands. `C342-N1` and `C342-N2` are routed, not applied.*
