# C366 — `web4-society-authority-law.md` (SAL), 9th delta

**Date**: 2026-08-12
**Target**: `web4-standard/core-spec/web4-society-authority-law.md` — blob `0849ebbe`, 419 lines
**Prior pass**: `docs/audits/C326-society-authority-law-8th-delta-2026-08-06.md` (PR #652, `b21da071`)
**Window**: `b21da071..HEAD` (`472d877a`, 2026-08-11 22:05 −0700) = **48 commits**
**Spec mutation**: **ZERO.** This pass produces one document under `docs/audits/` and touches nothing else.

**Lineage enumeration rule (inclusive, stated per the standing rule).** The SAL lineage is **10
documents**, not 9: the origin pass is `docs/audits/sal-internal-consistency-2026-05-27.md`
(`# C16:` on line 1), which a `C*-society-authority-law*` glob does not return. Members: C16, C23,
C58, C98, C134, C170, C208, C246, C286, C326 — and this document, C366.

| | |
|---|---|
| Target freeze | `0849ebbe` since `1354e4c2` (2026-07-14, #523) — **29 days**, 9 passes |
| Commits on target in window | **0** |
| Commits in `web4-standard/` in window | **1** — `afd04623` (#678), touching `errors.md`, `security-framework.md`, `submission/draft-web4-core-00.xml`; disjoint from SAL |
| Commits in `hub/` in window | 19 |
| Commits in `web4-standard/implementation/sdk/` in window | 0 |
| Result | **8th consecutive fully-clean delta on the target text.** One net-new finding, against the standard's *enforcement* surface rather than its prose. |

---

## §A — Pre-registered checks from C326, answered

C326 pre-registered three forward checks by name. All three are answered here **before** any new
work, and two of them retire or re-affirm a row rather than producing a finding.

### A.1 — `C16-H1-remainder`: did C334 consume it? **YES. Retired here.**

C326's guard: *"AT C366 CHECK: did C334 consume it? If not, the routing failed twice ⇒ escalable."*

`docs/audits/C334-errors-8th-delta-2026-08-07.md` answers it by name at `:403` — **`C334-N4`**,
*"`C16-H1-remainder`, routed to this slot by C326, is REFUTED as a defect against `errors.md`"* —
with the measurement published at `C334:409-413`:

| Code | `errors.md` | `errors.py` | SAL §9 | `initial-registries.md` |
|---|---|---|---|---|
| `W4_ERR_LEDGER_WRITE` | 0 | 0 | 1 (`:331`) | 0 |
| `W4_ERR_AUDIT_EVIDENCE` | 0 | 0 | 1 (`:332`) | 0 |
| `W4_ERR_LAW_CONFLICT` | 0 | 0 | 1 (`:333`) | 0 |

The refutation is on the merits and it is correct: `errors.md` §1 grants extenders the right *"to
extend this taxonomy with additional domain-specific codes"* and **names SAL §9 as extender 1 of 4**.
Three SAL-domain codes living in SAL §9 and not in `errors.md` §2 is the mechanism working, not
failing. `C334:560` forward-guard 4: *"Do not re-raise it as an errors.md defect. If a future SAL
delta re-routes it here, answer with N4 rather than re-deriving."*

**Disposition: the row is RETIRED at the SAL seat** (v42 — a deflation retires the row). Its
surviving half is an `errors.py` inconsistency and rides `C334-N3`, which is the errors lineage's.
Re-verified independently at HEAD: all three codes still present at SAL `:331-333`; still 0 in
`errors.md` and 0 in `errors.py`.

**The routing succeeded.** C326 routed it, C334 received it the next day and answered it on the
merits. Recorded as a positive datapoint for the v36 delivery discipline, which is what produced
the routing in the first place.

### A.2 — I-1: did `sal-governance.json` or `federation.py` change? **Neither.**

| artifact | state |
|---|---|
| `web4-standard/test-vectors/federation/sal-governance.json` | blob `dab43af1`; sole commit in all history `f00c35f1` (2026-03-16, #22) |
| `web4-standard/implementation/sdk/web4/federation.py` | `sdk/` = **0** commits in window |

C326's first-in-corpus-history execution of these vectors (6/6 PASS) stands and is **not re-run** —
its inputs are byte-identical. The `federation.py:26` *"Validated against"* claim remains TRUE and
guarded by nothing; that is C326's I-1 and C362's v46 row, not a new one.

### A.3 — C286-N1: did `KNOWN_ROLES` change? Did a fidelity test appear? **No and no — 3rd pass.**

`hub/hub-lib/src/law.rs:39-47` still lists exactly 7 entries in the same order (`sovereign`,
`administrator`, `treasurer`, `archivist`, `witness`, `citizen`, `applicant`). The only test that
reads `KNOWN_ROLES` is still the **non-overlap** assertion — now
`constellation_roles_are_a_separate_namespace_from_society_roles` at `law.rs:521` (drifted from
C326's `:452` on 3 in-window `law.rs` commits) — which asserts the two vocabularies are **disjoint**,
never that `KNOWN_ROLES` **matches** `society-roles.md`.

**C286-N1 STANDS, undischarged, third consecutive pass. HUB track. Not re-scored here.**

**Sharpened, and this is worth routing:** the ratified fix shape now exists **in the same file**.
`68c2ba9c` (#670, in-window) added `law.rs` `is_known_law_action` — *refuse a law norm that names an
action the gate never emits*. That is precisely the "is this value one the gate can ever actually
see" guard C286-N1 asks for, built for the **action** vocabulary and not applied to the **role**
vocabulary 350 lines above it, in the same window, by the same track. The remedy is no longer
hypothetical; it is a local idiom the file already uses.

### A.4 — Anchor re-resolution (v22, 4th fire)

| anchor (C326-published) | in-window commits to file | live | result |
|---|---|---|---|
| `law.rs:39` `KNOWN_ROLES` | 3 | `:39` | **HELD** |
| `law.rs:452` non-overlap test | 3 | **`:521`** | **DRIFTED** (+69) |
| SAL `:331-333` error codes | 0 | `:331-333` | HELD |

Consistent with the standing v22 reading: commit count screens for drift; magnitude predicts
nothing. Within a hot tree, *which* construct moves stays unpredictable — so anchors are re-resolved,
never trusted.

### A.5 — Inbound sweep (v36), bounded and published as measured

Filename-token sweep over both audit trees: `git grep -lF "society-authority-law" -- docs/audits/
web4-standard/docs/audits/` = **77 documents**. That is a token sink on a target this heavily cited,
so the sweep is bounded by a rule stated before it ran: **audit documents postdating C326
(2026-08-06)**, which is where prior fires found their entire yield.

| doc | hits | row addressed to SAL? |
|---|---|---|
| C330 ISP 8th | 1 | No — `:560` notes `test-vectors/federation/` is read by the SAL lineage, never from the ISP side. Observation, not a route. |
| C332 entity-types 8th | 2 | No |
| C334 errors 8th | 2 | **Yes — `C334-N4`, answered in §A.1.** |
| C348 multi-device 7th | 3 | No |
| C352 reputation 9th | 1 | No |
| C358 mrh-tensors 9th | 6 | No — C358 **cites SAL's own C58-B5(b) as the precedent for its flagship** (`C358:194`), and types `forum/nova/web4-sal-bundle/web4-society-authority-law.md` as a *"frozen inbound bundle, pre-C59 source"* (`:282`). Credit flowing outward, not a row inward. **Load-bearing for §B′.4 below.** |
| C360 SOCIETY_SPEC 9th | 6 | No — `:342` and `:664` reference SAL's ledger history, not a route. |
| C364 metabolic 9th | 2 | No |

**One inbound row in the bounded window, and it was already answered.** Recorded as a negative,
because a negative here is what makes the other lineages' positives interpretable.

### A.6 — Carried rows, re-verified at HEAD

C326's §C is a 19-row ledger. Nothing in this window touches the target, `ontology/`,
`society-roles.md`, or the SDK, so no row's referent moved. Re-verified binary, no merits re-argued:

- **`C16-M8`/`B6`** — SAL §7.1/§7.1.1 triple family still 100% absent from canonical
  `web4-standard/ontology/`; still no `sal-ontology.ttl` there. **STANDS.** (§B′ is a *sibling* of
  this row, not a re-file — see §B′.4.)
- **`C23-H1`** — birth-certificate N-way shape drift. **STANDS.** Now has a second dependent (§B′.6).
- **`B7`**, **`C50-B15`**, **`C58-B10`**, **`C286-N1`** — STAND (N1 per §A.3).
- Rows 1-13 of C326's table: row 1 (`C16-H1-remainder`) **retired here** per §A.1; rows 2-13
  unchanged, referents frozen, dispositions as published.
- **Ledger size: 19 → 19** (one retired, one added). The two name collisions C326 made visible —
  **`C16-H1` ≠ `C23-H1`** and **`C58-B15` ≠ `C50-B15`** — are carried forward verbatim in §C.
- **CADENCE design-Q: 11th consecutive datapoint.**

---

## §B — Corpus delta and mirror set

The mirror set was derived at C286 and is not re-derived from scratch. Re-checked at live HEAD:

| member | window commits | bearing on SAL |
|---|---|---|
| `hub/hub-lib/src/law.rs` | 3 | §A.3 — `KNOWN_ROLES` unchanged; `is_known_law_action` added |
| `hub/hub-daemon/src/{main,rest,admin}.rs` | (within 19) | no society-law surface change found |
| `hub/hub-lib/src/init.rs` | 0 | `:585` role-report anchor HELD |
| `web4-standard/implementation/sdk/` | 0 | frozen |
| `web4-standard/core-spec/` | 0 on target; 1 commit elsewhere (`afd04623`) | disjoint |

The single in-window `web4-standard/` commit `afd04623` (#678, *"fold hackathon findings into
canonical Web4 text"*) touches `errors.md`, `security-framework.md` and
`submission/draft-web4-core-00.xml`. Checked for authority over SAL's subject matter (v2 — grep the
behaviour, not the vocabulary): it adds no society/law/citizenship normative surface and does not
reach SAL's §9 rows. **Disjoint.**

**Frozen target + frozen mirrors is the "0 net-new" trap, not a clean bill** (v7/C288). The
remaining surface is the standard's own **published non-prose artifacts** — and this pass's opening
move was to execute those artifacts against each other rather than re-read the prose. That is where
§B′ came from.

---

## §B′ — C366-N1 (MED) — the standard has a ratified gate for dangling `@context` references, and its domain is a **directory**; SAL's two live instances sit outside it, in the only two blocks the spec calls canonical and MUST-publishable

### B′.1 The class is ratified, and so is the way to disclose an instance of it

`#637` (`8d3808db`, **2026-08-04**) added `.github/workflows/vector-context-refs.yml` and
`web4-standard/test-vectors/validate_context_refs.py` in response to audit **C310-N3**, which found
36 of 38 published t3v3 vectors citing a context retired by the 2026-03-24 namespace reconciliation.
The script's own docstring states the hazard precisely:

> the schemas type `@context` as an array of URI strings and never dereference it, so a vector can
> pass schema validation forever while citing a context that does not exist

and the workflow header states the discipline:

> Armed GREEN per the ci.yml discipline … the one currently-missing context, `t3v3.jsonld`, is
> carried explicitly as `KNOWN_MISSING` inside the script, with its audit citation and fix routing.
> … the debt is enumerable, not silent.

Run at HEAD: **283 references, 9 distinct names, green, 1 carried debt.**

This is a well-built gate. **`KNOWN_MISSING` (`validate_context_refs.py:49-56`) is also the corpus's
established disclosure convention for this exact class**: name + audit citation + fix routing. That
convention is what makes the rest of this finding chargeable rather than a charge against the
corpus's own deliberate phasing (v45 corollary 2).

### B′.2 The gate's domain is a directory, and the denominator is a class

`validate_context_refs.py:39` sets `VECTORS_DIR = Path(__file__).parent`; `:83` iterates
`VECTORS_DIR.rglob("*.json")`. The workflow is path-filtered to `web4-standard/test-vectors/**`,
`web4-standard/schemas/contexts/**`, and itself. **Nothing outside `test-vectors/` can affect the
result, and nothing outside it is examined.**

Measured over the class instead — every `https://web4\.io/contexts/([A-Za-z0-9_.-]+\.jsonld)` in
every file returned by `git ls-files web4-standard/`:

| | count |
|---|---|
| distinct context names referenced | **15** |
| backed by a file in `web4-standard/schemas/contexts/` | **10** |
| **unbacked** | **5** |
| unbacked names the gate can see | **1** (`t3v3.jsonld`) |
| **unbacked names the gate cannot see** | **4** |

The denominator **10** is not this pass's construct — it is the corpus's own:
`web4-standard/implementation/sdk/CHANGELOG.md:468` records the 2026-03-24 reconciliation as
covering *"All 10 JSON-LD context files."*

The four invisible ones, each with its site:

| name | site | tree | disclosed anywhere? |
|---|---|---|---|
| **`sal.jsonld`** | `core-spec/web4-society-authority-law.md:47` | `core-spec/` | **No** |
| **`sal.jsonld`** | `core-spec/entity-types.md:143` | `core-spec/` | **No** |
| **`law.jsonld`** | `core-spec/web4-society-authority-law.md:161` | `core-spec/` | **No** |
| **`law.jsonld`** | `rfcs/RFC_LAW_ORACLE_PROCEDURES.md:481` | `rfcs/` | **No** |
| `trust-query.jsonld` | `sdk/web4/trust.py:108`, `sdk/tests/test_trust.py:941` | `implementation/` | No — **routed, not charged here** |
| `mrh.jsonld` | `submission/draft-palatov-web4-core-00.txt:798` | `submission/` | No — **routed, not charged here** |

**Second enforcement surface, same shape.** The SDK asserts context-file *existence* with
`os.path.exists()` for exactly **3 of 15** names — `r7-action` (`test_r6.py:1450`), `t3`
(`test_t3v3_jsonld.py:469`), `v3` (`:521`) — all three already backed. So it catches nothing that
is broken. And `test_trust.py:941` asserts that the `trust-query.jsonld` **string** appears in the
document, never that it resolves: a green test about a literal, not about a system (v45).

**Both guards are green. Neither can reach four of the five real instances.**

### B′.3 SAL's two are in the only blocks it calls canonical, and they fail *executed*, not argued

SAL carries six fenced `json` blocks. **Four are hedged and carry no `@context` at all** (heading
locus → block locus):

- `:205` → `:206` §5.5 — *"Auditor Invocation (canonical **extract**)"*
- `:113` → `:114` §3.4 — *"Ledger Interface (**minimum**)"*
- `:388` → `:389` §14.1 — *"Citizen Role LCT (**extract**)"*, under §14 *"Schema **Stubs**"*
- `:398` → `:399` §14.2 — *"Society Record (**extract**)"*

**The two that do carry an `@context` are exactly the two the spec does not hedge**:

- `:44` → `:45-59`, IRI at **`:47`** — §2.2 *"Birth Certificate (**Canonical JSON-LD**)"* →
  `contexts/sal.jsonld`
- `:152` *"A Law Oracle **MUST** publish a versioned Law Dataset containing:"* → `:159-169`, IRI at
  **`:161`** — §4.1 → `contexts/law.jsonld`

So SAL demonstrably knows how to mark a block illustrative, applies that marking four times in the
same file, and withholds it from precisely the two blocks whose contexts do not exist. The sibling
sites are unhedged too: `entity-types.md:140` *"Birth Certificate Structure (SAL-aligned
superset)"* (IRI at `:143`), and `RFC_LAW_ORACLE_PROCEDURES.md:477` *"Extended procedures remain
valid `Web4LawDataset`:"* (IRI at `:481`).

**Executed** (`pyld`, offline document loader resolving `https://web4.io/contexts/<name>.jsonld`
against `web4-standard/schemas/contexts/` — the standard's own tree, no network):

| block | result |
|---|---|
| SAL §2.2 birth certificate | **`JsonLdError` — expansion fails outright.** No backing file. |
| SAL §4.1 `Web4LawDataset` | **`JsonLdError` — expansion fails outright.** |
| *control:* `{"@context":["https://web4.io/contexts/lct.jsonld"], "lct_id":"lct:web4:x"}` | expands cleanly → `https://web4.io/ns/lctId` |

The control is what makes the instrument admissible: the same loader, the same call, a backed
context, a clean expansion. The failure is specific to the two names, not to the method.

### B′.4 The obvious fix is a trap — and this is the part a copy-paste remediation would get wrong

`forum/nova/web4-sal-bundle/sal.jsonld` **exists** and looks like the missing file. It is not.
Substituting it (the only `sal.jsonld` anywhere in the repo) and expanding:

| block | input properties | survive expansion | **dropped** |
|---|---|---|---|
| §2.2 birth certificate | 11 | 2 — `@type`, `lawVersion` | **9**: `entity`, `citizenRole`, `society`, `lawOracle`, `birthTimestamp`, `witnesses`, `genesisBlock`, `rights`, `obligations` |
| §4.1 `Web4LawDataset` | 7 | 2 — `@type`, `hash` | **5**: `law_id`, `norms`, `procedures`, `interpretations`, `r6Bindings` |

*(Counting rule: `type` counted as an input property; it survives as `@type` via the bundle's
`"type": "@type"` alias.)*

The bundle defines 29 terms, and they are the **class names and §7 RDF predicates** —
`Web4BirthCertificate`, `Web4LawDataset`, `LawOracle`, `hasWitness`, `hasAuditor`, `memberOf`. It
was never a serialization context for these objects' **properties**. Dropping it into
`schemas/contexts/sal.jsonld` would turn both CI surfaces green while leaving 9 of 11 properties of
the standard's own **canonical** birth certificate — every field it exists to carry — undefined on
expansion. That is the C350 shape: evidence that survives validation and vanishes in the round trip.

**Consistent with C358's independent typing of the same directory** (`C358:282`): the SAL bundle is
a *"frozen inbound bundle, pre-C59 source."* It is a pre-remediation artifact, not a canonical one.

**Therefore the remedy is authorship, not canonicalization** — 9 term definitions for §2.2 and 5 for
§4.1, plus a namespace decision (`ontology#` in the bundle vs `ns/` in all 10 published contexts per
`CHANGELOG.md:468`).

### B′.5 Novelty — the matcher, published beside the claim (v44)

Over **both** audit trees:

| matcher | docs |
|---|---|
| `law.jsonld` | **0** |
| `sal.jsonld` | **1** — `C23-society-authority-law-audit-2026-05-30.md` |
| `context IRI` | 0 |
| `unpublished context` | 0 |
| `term expansion` | 0 |
| `JSON-LD expansion` | 0 |

C23's single hit is at `:109-125`, and it is **`C23-H1`** (birth-certificate three-way shape drift),
which quotes the §2.2 block *including* its `@context` line while charging the **field set**. It
never charges the IRI. (Note for the record: `C23-M1` is a different row — `initialRights`/
`initialResponsibilities` against **`entity-types.md` L153-154**, not SAL.)

**Honest framing.** The *class* is **not** net-new: `C310-N3` owns it, with the denominator scoped
to **SDK constants** (9 of 11). What is new is (i) extending the denominator to the **whole
standard** and (ii) this lineage's two instances. And the **fact** is old: `git log -S
"contexts/sal.jsonld" -- web4-standard/` first hits `5a916edd`, **2025-09-15** — the dangling
reference has been in the standard for **331 days**, since SAL was introduced. Net-new as a
*finding*; 331 days old as a *fact*; the *gate* that should have caught it is 8 days old.

### B′.6 What C338 got right, and where its conclusion was scoped

`docs/audits/C338-registries-8th-delta-2026-08-08.md:145` already measured the gate's shape,
four days ago, and published it as **a negative with a guard**:

> `validate_context_refs.py` sets `VECTORS_DIR = Path(__file__).parent`, so it recurses only from
> `web4-standard/test-vectors/` (35 JSON files) and is structurally blind to
> `web4-standard/testing/test-vectors/` (16 JSON files) … Measured before charging: … **0**. The
> blind tree carries no context references at all, so the blindness is currently harmless.
> Published as a NEGATIVE with its number, and as a guard: the gate's scope is a latent defect that
> becomes real the moment a `@context` lands under `testing/`.

**C338's measurement was right and its conclusion was scoped to the wrong region.** It looked for
another *test-vector-shaped directory* and found an empty one. The populated blind region was
`core-spec/`, `rfcs/`, `implementation/`, `submission/` — and on the day C338 called the blindness
harmless, **four live dangling references were already sitting in it**, two of them SAL's, in a
block the spec labels canonical.

This pass therefore **discharges C338's guard** rather than claiming its ground: the latent defect
C338 correctly identified was not latent, and the reason it read as latent is that the search was
keyed to the gate's own shape. A directory-shaped guard invites a directory-shaped audit of it.
C338 is credited, not superseded.

### B′.7 Severity, and why it is not independently fixable

**MED.** Not HIGH: nothing in the deployed system dereferences these IRIs today — SAL §2.3's
canonicalization MUST is **JCS over the JSON**, not over the expanded RDF, so signatures and
`lawHash` pinning (§8) are unaffected. Not LOW: §4.1 sits under a **MUST publish**, §2.2 is labelled
**Canonical**, the defect has propagated to two sibling documents, and a conformant implementer
following the spec literally cannot expand either object.

**And it is blocked, which is the finding's most useful consequence.** A context defines the terms
of a field set. `C23-H1` — **STANDS**, four passes open (`C326:349`) — is precisely the row saying
that this block's field set is in unresolved three-way drift across SAL §2.2,
`LCT-linked-context-token.md`, and `lct.py::BirthCertificate`. **You cannot author a context for a
block whose field set is under an open HIGH.** So C366-N1 is not an isolated MED to be scheduled;
it is a **second dependent on C23-H1's deferral**, and it is a materially stronger argument for
escalating H1 than four passes of shape-drift prose have managed.

### B′.8 Refuting my own flagship (standing rule)

Four attempts, recorded:

1. **"The examples are illustrative; specs do that."** Refuted in B′.3 — SAL hedges four blocks and
   marks these two canonical/MUST.
2. **"The corpus phases mechanisms in deliberately and says so"** (v45 corollary 2 — the check that
   killed a C360 draft). Searched `web4-standard/` for `does not resolve|placeholder|not
   dereferenc|illustrative|not yet published|reserved namespace` → **0**. And the corpus's disclosure
   convention for *this exact class* exists and is applied to `t3v3.jsonld`; these two are not in it.
   The defect is the sites that opted out of a convention the corpus built.
3. **"This is `C16-M8`/`B6` re-filed."** Refuted in §B′.4/§C: `M8` is a **TTL vocabulary row about
   `ontology/`**; this is a **dangling IRI in a normative example plus an enforcement asymmetry** —
   different artifact, different consumer, different owner. They share a root (SAL's vocabulary was
   never canonicalized), and this document says so rather than presenting an independent discovery.
4. **"Just copy the bundle file."** Refuted by execution in §B′.4 — that greens the gate and drops
   9 of 11 properties. This is the refutation that most improved the finding.

---

## §C — Ledger

**19 rows in, 19 rows out** (one retired, one added). Count published per v23.

| # | id | disposition at C366 |
|---|---|---|
| 1 | `C16-H1-remainder` | **RETIRED** — consumed and refuted by `C334-N4` (§A.1); `errors.py` half rides `C334-N3` |
| 2 | `C16-M1` | DESIGN-Q — TRUE, re-derived as `C286-N1` |
| 3 | `C16-M3` | DESIGN-Q — TRUE |
| 4 | `C16-M4` | DESIGN-Q / cross-track — TRUE |
| 5 | `C16-M5` | DESIGN-Q / cross-track — TRUE |
| 6 | `C16-M6` | cross-track — TRUE |
| 7 | `C23-M3` | DESIGN-Q — TRUE |
| 8 | `C23-L2` | DESIGN-Q (overlaps `C16-M5`) — TRUE |
| 9 | `B1` | FOLDED — facet of `C23-H1` |
| 10 | `B8` | DESIGN-Q — TRUE (frozen) |
| 11 | `B9` | DESIGN-Q / cross-track — TRUE |
| 12 | `B11` | cross-track → `r6-framework.md` — TRUE |
| 13 | `L1-residual` | SPEC-side — TRUE (frozen) |
| 14 | `C16-M8` / `B6` | **STANDS** — SAL §7.1/§7.1.1 triple family absent from canonical `ontology/`; no `sal-ontology.ttl` there. **Sibling of `C366-N1`, not the same row**: `M8` is TTL/`ontology/`, N1 is JSON-LD `@context`/`schemas/contexts/`. Same root, different artifact. Adjudicate together. |
| 15 | `C23-H1` | **STANDS** — birth-certificate N-way shape drift (**≠ `C16-H1`**). **Now has a second dependent: `C366-N1` cannot be fixed until H1 is decided (§B′.7).** |
| 16 | `B7` | STANDS — SAL conformance-MUSTs vs `society-roles.md` Optional tier; adjudicate **with** `C16-M1` and #579 |
| 17 | `C50-B15` | STANDS — law-composition, 3 models (**≠ `C58-B15`**) |
| 18 | `C58-B10` | STANDS — dormant-defer vs `new_citizen` wake, two-sided |
| 19 | `C286-N1` | **STANDS, 3rd pass, undischarged** — HUB track. Sharpened: the fix shape now exists in the same file (`is_known_law_action`, `68c2ba9c`/#670). |
| 20 | **`C366-N1`** | **NEW (MED)** — see §D routing |

**Two name collisions this ledger must keep visible** (carried verbatim from C326; both would
otherwise read as renames):

- **`C16-H1` ≠ `C23-H1`.** `C16-H1` is the §9 error-code finding, carried as `C16-H1-remainder`,
  **retired this pass**. `C23-H1` is filed at `C23:44` as `HIGH (new)` — birth-certificate three-way
  shape drift. `C23-H1` surviving does **not** rescue `C16-H1`, and `C16-H1`'s retirement does
  **not** touch `C23-H1`.
- **`C58-B15` ≠ `C50-B15`.** The former (§9 expired-delegation) has never been typed as an id
  anywhere, both trees; the latter (law-composition) is healthy.

**Still with the operator, unchanged, not re-argued:** `C50-B13`/`B14`/`B15`, `C16-M8`/`B6`,
`C58-B10`, `C33`. → the standing operator memo. **CADENCE design-Q: 11th consecutive datapoint.**

---

## §D — Routing

| item | owner | action asked |
|---|---|---|
| **`C366-N1`** (MED) | **standard-editor + SDK/build track**, gated on `C23-H1` | (1) Do **not** copy `forum/nova/web4-sal-bundle/sal.jsonld` — §B′.4 shows it drops 9 of 11 properties. (2) Until `C23-H1` decides the birth-certificate field set, the honest interim act is **disclosure**, using the convention the corpus already built: add `sal.jsonld` and `law.jsonld` to a `KNOWN_MISSING`-equivalent with this citation and this routing. (3) The durable fix is to widen the gate's domain from `test-vectors/` to the class — every `web4.io/contexts/*.jsonld` reference under `git ls-files web4-standard/`. |
| **`C286-N1`** | HUB track | Unchanged, 3rd pass. Note the in-window precedent `is_known_law_action` (`68c2ba9c`/#670) — the same guard, one vocabulary over. |
| `trust-query.jsonld` unbacked (2 sites) | **t3-v3 / trust lineage** | Not charged here. `test_trust.py:941` asserts the string, never the file. Ride the next trust slot. |
| `mrh.jsonld` unbacked (1 site, `submission/draft-palatov-web4-core-00.txt:798`) | **mrh-tensors lineage (C358's)** | Not charged here — `submission/` is C336-N1's charged tree and re-charging an adjacent cell re-litigates another ledger. Recorded as a baseline. |
| `ontology/r7-action.jsonld` vs `schemas/contexts/r7-action.jsonld` **disagree** (`ontology#` + camelCase vs `ns/` + snake_case) | **t3-v3 / build track** | Surfaced by this pass's denominator work; outside SAL's subject matter. Recorded, not charged. |
| `C16-H1-remainder` | — | **Retired.** Do not re-route to `errors.md`; the answer is `C334-N4`. |

**Nothing in this document is self-applied.** SAL, `entity-types.md`, `law.rs`,
`validate_context_refs.py`, the workflow, and the SDK are untouched.

---

## §E — Forward guards for C406 (next SAL slot)

Phrased as behaviours, not paths:

1. **Check whether `C366-N1` was disclosed or fixed — and if "fixed", expand the block before
   believing it.** A `schemas/contexts/sal.jsonld` that exists is not the same as one that defines
   the birth certificate's properties. Run the expansion; count surviving properties against the 11
   in §2.2. A green gate is compatible with 9 dropped fields.
2. **Check whether `C23-H1` was decided.** `C366-N1` unblocks only when it is. If H1 is still open
   at C406, that is **three** dependents and five passes, and the escalation argument is no longer
   about shape drift.
3. **Check whether the gate's domain widened.** If `validate_context_refs.py` still sets
   `VECTORS_DIR = Path(__file__).parent`, the four out-of-domain references are still invisible —
   re-run the class-wide denominator (command in §G) and report the count, not the impression.
4. **`C286-N1`, 4th pass.** Ask only two things: did `KNOWN_ROLES` change, and does any test assert
   it **matches** `society-roles.md`. A disjointness test is not a fidelity test.
5. **When a guard is built in-window, audit its *domain* before trusting its colour.** This pass's
   entire yield came from asking what a green check is green *about*. C338 asked the same question
   of the same gate four days earlier and scoped the answer to a directory.

---

## §F — Accountability self-audit

```
surface: none — this pass produces one audit document under docs/audits/
act: none — no consequential act; zero mutation of web4-standard/**, hub/**, .github/**, or any SDK file
S: low/reversible [construct: docs/audits/C366-society-authority-law-9th-delta-2026-08-12.md, additive]
R: n/a   W: n/a
O: n/a   A: n/a   V: n/a
verdict: PASS (no caller-drivable surface; a record, not an enactment)
```

The one execution performed (JSON-LD expansion) ran in a throwaway virtualenv against a read-only
checkout with an **offline** document loader; no network fetch, no repo file written, no dependency
added to the project.

---

## §G — Own-error re-run

Six cells failed a post-write re-run or a review challenge. All corrections are published; three
of them made the finding stronger, which is the standing signal that the original was guessed.

1. **"The fix is a canonicalization, not an authorship" — FALSE, and it was the draft's headline
   framing.** I sampled the forum bundle's terms, saw `Web4BirthCertificate`, `Web4LawDataset`,
   `LawOracle`, `hasWitness`, and generalized from the hits. **Executing it** shows it defines 2 of
   11 §2.2 properties and 2 of 7 §4.1 properties. Caught by policy review; converted the finding's
   weakest paragraph into §B′.4, its strongest. **A term list read is not a term list run.**
2. **`C338-registries-8th-delta:145` already owned the gate-blind-tree observation, and the draft
   did not cite it at all** — a near-miss on the exact failure this track has a standing rule
   against (re-filing another lineage's row as net-new). Caught by policy review. The corrected
   framing (§B′.6) is better than "net-new" would have been: it *discharges* C338's own guard.
3. **The C23 citation was misattributed.** The draft said C23 charges the field names
   `initialRights`/`initialResponsibilities` on this block. Those are **`C23-M1`**, filed against
   **`entity-types.md` L153-154**. The row that quotes SAL §2.2 with its `@context` is **`C23-H1`**,
   a HIGH that **STANDS** (`C326:349`). Novelty is unaffected — H1 charges shape, never the IRI —
   but the pass is landing a second row on a block under an open HIGH, and that turned out to be
   §B′.7's whole point.
4. **A first sweep reported the target as absent from its own error-code grep.** `git grep -l` over
   three alternated tokens returned a 20-line list piped through `head -20` — the target sorts after
   `forum/` and was cut. The number was real, the list was truncated, and I nearly read the
   truncation as a finding. **Publish the count, not the head.**
5. **Two sibling cites were adopted from policy review without being resolved** — the hedging prose
   was cited at `entity-types.md:141` and `RFC_LAW_ORACLE_PROCEDURES.md:479`, which are both the
   fence line ` ```json `. The prose is at `:140` and `:477`. Corrected in §B′.3, along with the
   §14 heading-vs-block loci. **A cite handed to you by a reviewer is still a cite you did not
   run** — the standing rule about not taking another agent's result at face value applies to the
   ones that agree with you.
6. **`sdk/web4/federation.py` does not exist**; the real path is
   `web4-standard/implementation/sdk/web4/federation.py`. Carried from memory, not resolved, and it
   would have produced a false "file deleted" signal on a pre-registered check. Anchors are
   re-resolved; so are paths.

**Post-write re-runs that AGREED** (an agreeing verifier confirms nothing until you confirm it ran —
these were re-run at a different scope and the scopes disagreed on nothing): the 15/10/5 denominator
(re-run with an independent instrument by policy review, same result); `KNOWN_ROLES` = 7 entries
(re-run against `git show HEAD:hub/hub-lib/src/law.rs`); window = 48 (re-run as `git rev-list
--count`); `b21da071` confirmed an ancestor of HEAD (`git merge-base --is-ancestor`) — the C362
non-ancestor-base error, checked for and not repeated.

**Reproducible instruments.**

```bash
# The class-wide denominator (guard 3 above). Root-independent: git ls-files, not grep -r.
python3 - <<'PY'
import re, subprocess, collections, os
pat = re.compile(r'https://web4\.io/contexts/([A-Za-z0-9_.-]+\.jsonld)')
refs = collections.defaultdict(lambda: collections.defaultdict(int))
for f in subprocess.check_output(['git','ls-files','web4-standard/'],text=True).split():
    for m in pat.finditer(open(f,encoding='utf-8',errors='replace').read()):
        refs[m.group(1)][f] += 1
backed = {os.path.basename(p) for p in
          subprocess.check_output(['git','ls-files','web4-standard/schemas/contexts/'],text=True).split()}
for n in sorted(refs):
    print(f"{n:32s} {'BACKED' if n in backed else 'UNBACKED':9s} "
          f"{sum(refs[n].values()):3d} refs  {sorted(refs[n])}")
PY

# The ratified gate, for comparison (domain = test-vectors/ only)
cd web4-standard/test-vectors && python3 validate_context_refs.py
```
