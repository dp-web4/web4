# C406 — `web4-society-authority-law.md` (SAL), 10th delta

**Date:** 2026-08-18 · **Slot:** C406 (SAL, 10th delta; predecessor **C366** / PR #693, anchor `9713026e`)
**Target:** `web4-standard/core-spec/web4-society-authority-law.md` — blob `0849ebbe`, **419 L**
**Freeze:** last mover `1354e4c2` (2026-07-14, #523 W4IP Phase 3) ⇒ **35 days, 10 passes, 9th consecutive fully-clean delta on the prose**
**Mutation this pass:** **ZERO.** One new file, this document.

**Headline (N1, MED).** The ratified remediation that closed `C58-B4` and `C58-B5` — `0d756773` / #330,
*"spec(C59): remediate 9 autonomous C58 findings on SAL"* — widened §7.1's requirement list and
repaired §7.2's queries, and **never touched §3.3, the only worked RDF data the spec contains.**
Executed at HEAD: §3.3 exposes **7 of the 15** predicates §7.1 + §7.1.1 now MUST-require, and §7.2's
`SELECT` — the query `C58-B4` was named for — still returns **0 rows** against it. Neither B4 nor B5
has been re-executed in the seven passes since.

---

## §A — Pre-registered checks from C366 §E, answered

C366 phrased five forward guards as behaviours. Each is answered below with the command that produced it.

### A.1 — Guard 1: was `C366-N1` disclosed or fixed? **Neither. Unchanged, byte-for-byte.**

```
ls web4-standard/schemas/contexts/
→ acp atp attestation-envelope capability dictionary entity lct r7-action t3 v3   (10 files)
```

`sal.jsonld` is still absent, so the "expand the block before believing it" trap C366 pre-registered
never had to be sprung. Re-running C366's class-wide denominator over `git ls-files web4-standard/`:

| | C366 (2026-08-12) | C406 (HEAD) |
|---|---|---|
| context names referenced | 15 | **15** |
| backed | 10 | **10** |
| unbacked | 5 | **5** — `law.jsonld`, `mrh.jsonld`, `sal.jsonld`, `t3v3.jsonld`, `trust-query.jsonld` |

**`C366-N1` STANDS, unchanged.** Disclosure grep over `web4-standard/` for
`does not resolve|placeholder|not dereferenc|illustrative|not yet published|reserved namespace` = **0**,
as at C366.

### A.2 — Guard 3: did the gate's domain widen? **No.**

`web4-standard/test-vectors/validate_context_refs.py:39` still reads `VECTORS_DIR = Path(__file__).parent`,
and `:83` still walks `VECTORS_DIR.rglob("*.json")`. The gate sees **1** of the 5 unbacked names; the
other 4 remain outside its domain. `C366-N1`'s severity basis is intact. (This is `v49` — a guard's
domain is not its class — holding for a second pass.)

### A.3 — Guard 2: was `C23-H1` decided? **No.**

`grep -rn "C23-H1" docs/audits/` returns no disposition dated after C366; every hit outside the SAL
lineage (`C60`, `C80`) pre-dates it and is cite-only under the BC-C23-1 firewall. H1 was raised
**2026-05-30** and has now been carried across **ten SAL passes / 80 days**.

**Correction to my own draft, and a narrowing.** C366 §B′.7 filed `C366-N1` as H1's *second* dependent
and pre-registered "if H1 is still open at C406 that is **three** dependents". It is **two**, not three:
this pass's `N1` is independent of H1 (it turns on §3.3-vs-§7.1 edge sets, not on birth-certificate
shape), so no third dependent arrived. The escalation argument is *duration*, not *fan-out* — and
stating it as fan-out would have been an unearned inflation of my own predecessor's row.

### A.4 — Guard 4: `C286-N1`, 4th pass. **`KNOWN_ROLES` unchanged; still no fidelity test.**

`hub/` moved **7** commits in-window, **2** of them touching `hub/hub-lib/src/law.rs`. Both questions
the guard permits, answered:

- `law.rs:40-48` — still **7** entries, same order (`sovereign, administrator, treasurer, archivist, witness, citizen, applicant`).
- The only test over that constant is still the **non-overlap** assertion,
  `constellation_roles_are_a_separate_namespace_from_society_roles` (`:789-800`). It asserts
  `KNOWN_ROLES` and `KNOWN_CONSTELLATION_ROLES` are *disjoint*. **A disjointness test is not a
  fidelity test** — nothing asserts `KNOWN_ROLES` matches `society-roles.md`.

Anchors drifted a third time (`:452` → `:521` → **`:522/:534/:546/:566`**; the test `:452` → `:790`).
The `is_known_law_action` precedent C366 routed to HUB (`68c2ba9c`/#670) is still `:649`, still applied
to the **action** vocabulary only. **`C286-N1` STANDS, 4th pass, undischarged.**

### A.5 — Guard 5: audit a guard's *domain* before trusting its colour. **Applied — and it cost me my drafted headline. See §G.1.**

### A.6 — Inbound sweep (v36), bounded and published as measured

Window `9713026e..HEAD` = **27** commits. Pre-registered rule: domain word `society|authority|law`
over `git grep -li`, minus the filename sweep, bounded to `web4-standard/ **and** hub/`, excluding
`archive/**` and `simulations/**` (the M2 trees).

**0** commits in `web4-standard/`. The 7 `hub/` commits are Sprint F0 (`#699`, `#703`, `#706`, `#708`)
plus 3 PRD docs — response-side/R7 enforcement work. Two touch `law.rs` and are consumed by A.4;
the rest are `hub-daemon` sponsor-evidence and deploy-ratification, **disjoint** from SAL's prose.
**Residue: empty.** Recorded as a negative so the other fires' positives stay interpretable.

### A.7 — Carried rows, re-verified at HEAD

Twenty rows inherited from C366's §C table (v62: table ∪ predecessor's §C-born findings — C366 bore
exactly one, `C366-N1`, already its row 20).

| # | row | disposition at C406 |
|---|---|---|
| 1 | `C16-H1-remainder` | **RETIRED at C366** (consumed by `C334-N4`) — not re-opened |
| 2 | `C16-M1` | DESIGN-Q — TRUE (re-derived as `C286-N1`, see A.4) |
| 3 | `C16-M3` | DESIGN-Q — TRUE (target frozen) |
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
| 14 | `C16-M8` / `B6` | **STANDS — measured, widened, and its remediation measured insufficient. See §C.1.** |
| 15 | `C23-H1` | **STANDS** — 10 passes / 80 d, **two** dependents (see A.3) |
| 16 | `B7` | STANDS — SAL conformance-MUSTs vs `society-roles.md` Optional tier |
| 17 | `C50-B15` | STANDS — law-composition, 3 models (**≠ `C58-B15`**) |
| 18 | `C58-B10` | STANDS — dormant-defer vs `new_citizen` wake, two-sided |
| 19 | `C286-N1` | **STANDS, 4th pass** (A.4) |
| 20 | `C366-N1` | **STANDS, unchanged** (A.1, A.2) |
| — | **`C58-B4` / `C58-B5`** | **RE-OPENED as `C406-N1` — see §B′.** Dispositioned `HELD` at `C98` on a static read; never executed. |

Ledger **20 → 21**.

---

## §B — Corpus delta and mirror set

Target byte-frozen `0849ebbe`. Window empty on the standard for the **11th consecutive** measurement
across this fleet's rotation. Mirror set (`web4-core/src/{role,society,lct,r6}.rs`, SDK
`web4/{role,society,federation}.py`, `web4-policy/src/lib.rs`, `sal-governance.json`): **0** commits
in-window — C208 §B.3 and C326's 6/6 execution stand by construction on byte-identical inputs and were
**not** re-run (v25: a deferral row is an instrument, not a chore).

`web4-standard/ontology/` moved **0** commits in-window; `hub-law.ttl` at HEAD still declares
`@prefix web4: <https://web4.io/ontology/>` (trailing slash) and `law:hash` (`:112-116`) — `C58-B6`
intact, **not re-charged** (see §C.1).

**M2 declines, unchanged:** `archive/**` (incl. `rdf_ontology_consistency.py`), `simulations/**`,
`forum/nova/**`. Where `forum/nova/**` appears below it is **evidence about an in-scope carry's
remediation**, never a charge target — the position `C286:115` itself takes when it uses the same file
as evidence for `C16-M8`.

---

## §B′ — N1 (MED): the fix that closed `C58-B4`/`B5` widened the requirement and repaired the query, and left the data behind

### B′.1 What the two rows said, in their own words

`C58` (2026-06-15) charged both, back-to-back, under *"Self-consistency hygiene (SPARQL examples + cross-refs)"*:

> **B4 (LOW)** — §7.1 "Required Triples" omits `web4:publishes`, `web4:hash`, `web4:scope` that the
> spec's own queries/data depend on. […] **An implementation maintaining exactly the stated required
> set cannot answer the spec's own canonical query.**

> **B5 (LOW)** — §7.2 SPARQL examples are non-executable (2 facets). (a) Neither SPARQL block declares
> `PREFIX web4:` […] (b) the queries reference subjects as full IRIs `<lct:societyRoot>` […] but the
> §3.3 example data writes them as CURIEs […] **so the example ASK/SELECT would never match the
> example triples.**

Both name the same failure — *the spec's own query does not answer against the spec's own data* — and
approach it from opposite ends.

### B′.2 What the ratified fix did, by hunk

One commit closed both: **`0d756773` / #330**, 2026-06-15, *"spec(C59): remediate 9 autonomous C58
findings on SAL"*. Its hunk headers on the target:

```
git show 0d756773 -- web4-standard/core-spec/web4-society-authority-law.md | grep '^@@'
@@ -1,6 +1,6 @@      @@ -38,7 +38,7 @@     @@ -52,16 +52,16 @@
@@ -141,7 +141,7 @@   @@ -257,8 +257,10 @@   @@ -266,22 +268,29 @@   @@ -306,7 +315,7 @@
```

- `@@ -257 @@` — **B4**: `+ web4:publishes` / `+ web4:hash` / `+ web4:scope` appended to §7.1's list.
- `@@ -266 @@`, `@@ -306 @@` — **B5**: `+PREFIX web4: <https://web4.io/ontology#>` / `+PREFIX lct: …`
  added to both blocks, and `- <lct:entity> …` → `+ lct:entity …` (IRI → CURIE).

**No hunk falls in `84–104`** — §3.3, the turtle block and its MUST. The fix moved the requirement list
toward the data and the queries toward the data, and left the data itself untouched.

### B′.3 Executed at HEAD

Instrument: `rdflib 7.6.0`, blocks extracted verbatim by line range from the frozen target.

```
§3.3 turtle (L86–102)  → parses, 7 triples
§7.2 ASK    (L298–306) → askAnswer: True
§7.2 SELECT (L285–295) → 0 rows
```

The `ASK` matches — **B5's arm (b) was genuinely fixed**. The `SELECT`, the query B4's own text names
(*"Find a society's active law hash"*), returns nothing: §3.3 emits no `web4:hash` triple, so
`?law web4:hash ?hash` never binds.

Set-wise, at HEAD:

| | predicates | members |
|---|---|---|
| §3.3 turtle exposes | **7** | `pairedWith`, `memberOf`, `hasAuthority`, `hasLawOracle`, `publishes`, `delegatesTo`, `scope` |
| §7.1 + §7.1.1 MUST-require | **15** | the 8 of §7.1 + the 7 of §7.1.1 |
| §7.1+§7.1.1 \ §3.3 | **8** | `hash` + all seven of §7.1.1 |
| §3.3 \ §7.1+§7.1.1 | **0** | — |

§3.3's own line 104 reads *"Implementations **MUST** expose these edges for SPARQL queries"*. "These
edges" is the 7. §7.1's line 263 reads *"Implementations **MUST** maintain triples for:"* — the 15.
An implementation that satisfies §3.3 exactly fails §7.1; the direction runs one way only.

### B′.4 The control I ran first, and why it was the wrong control

Before charging, I ran the same instrument over the house-style sibling `mrh-tensors.md`: **6 of 6**
of its SPARQL blocks return 0 rows / `False` against its own turtle, and 3 of its 4 turtle blocks do
not parse standalone. On that reading SAL is *above* the corpus norm (1 of 2 matching), and
"query returns nothing against spec data" is a corpus idiom, not a defect. **I deflated the finding on
that basis and the policy reviewer reversed it, correctly.**

The control answers *"do core-spec SPARQL blocks generally agree with core-spec data?"* — and the
answer is no, generally not. But the question this pass is entitled to ask is narrower: **did the fix
ratified specifically to make this query agree with this data complete?** `mrh-tensors.md` has no such
remediation, so it cannot be the comparator. The comparator is `0d756773` against its own two rows.

Per arm (`v65b` — a multi-arm row is dispositioned per arm, not in aggregate):

| row | arm | verdict at HEAD |
|---|---|---|
| B5 | (a) missing `PREFIX` decls | **FIXED** — both blocks declare `web4:` and `lct:` |
| B5 | (b) IRI-vs-CURIE mismatch | **FIXED** — `ASK` returns `True` |
| B4 | the requirement list | **FIXED** — `publishes`/`hash`/`scope` present at `:268-271` |
| B4 | *"cannot answer the spec's own canonical query"* | **OPEN** — `SELECT` returns 0 rows |

Three of four arms fixed; the fourth is the predicate B4 was actually about. `C98` dispositioned
**B5 HELD** on a static read (*"L275/L288 `PREFIX web4:` …; subjects `lct:societyRoot` (CURIE)"*) and
carried B4 as remediated. Both readings are correct about what they checked. Neither ran anything —
and no pass since has (`C134`, `C170`, `C208`, `C246`, `C286`, `C326`, `C366` all carry **B6** and
neither B4 nor B5).

### B′.5 Novelty — matcher published beside the claim (v44)

Denominator: **247** documents — `docs/audits/` = 245, `web4-standard/docs/audits/` = 2.
*(Inherited correction, restated: `C364`'s "all 90 documents in `docs/audits/`" is wrong for its own
anchor; the tree held 227 at `c23ce054`.)*

| matcher | hits | reading |
|---|---|---|
| `grep -rn "B4\|B5" docs/audits/C*society-authority-law*` | B4/B5 appear only in `C58` (charge) and `C98` (HELD) | **no pass has re-executed either** |
| `grep -rniE "rdflib" docs/audits/ web4-standard/docs/audits/` | 13 docs, all mrh / t3-v3 / acp lineages | **no SAL pass has ever run an RDF tool** |
| `grep -rn "0d756773\|#330" docs/audits/` | `C98` only, as the remediation commit | never re-opened |
| `grep -rniE "0 rows\|zero rows\|returns nothing"` | 0 in the SAL lineage | — |

The **class** is precedented and its fix shape ratified elsewhere: `C42-F5` charged undeclared Turtle
prefixes in `t3-v3-tensors.md`'s fences and `C43`/`23d4a395` remediated by adding the `@prefix` lines
(present today at `t3-v3-tensors.md:142-145`, `:397-399`). **That precedent's domain is markdown
fences, not the agreement of a spec's data with its own normative list** (`v49` — a guard's domain is
not its class), so it supplies a fix shape, not a disposition.

### B′.6 Severity, and what would falsify it

**MED.** Not HIGH: both MUSTs are internally coherent, no wire format is at risk, and an implementer
reading §7.1 alone gets the correct 15. Not LOW: §3.3 is the spec's only worked RDF data and carries
its own MUST; §7.2's canonical query is the spec's own demonstration that the vocabulary is queryable;
and the specific arm still open is the one a ratified remediation was named for and marked closed.

**Falsifier, stated in advance:** if §3.3's *"SAL adds/uses these typed edges"* is intended as an
illustrative sample rather than a normative set, `:104`'s "MUST expose **these** edges" would need to
be reworded — and the finding becomes an editorial one at LOW. I did not find that hedge: §3.3 carries
no *"extract"*, *"minimum"* or *"canonical extract"* qualifier, unlike the four blocks C366 measured as
hedged (`:206`, `:114`, `:389`, `:399`). **The two unhedged blocks C366 identified are `:45` and `:159`;
§3.3 at `:85` is a third.** That is the operator's call, not mine — filed as the remediation choice, not
adjudicated here.

### B′.7 Refuting my own flagship (standing rule)

Best case against it: *B4 was LOW, C59 closed it, and re-opening a LOW row seven passes later on a
technicality inflates the ledger.* Answer: the row is not re-opened at LOW — it is re-opened at MED
because the **evidence class changed**. B4 was argued; this is executed, and it reverses a `HELD`
disposition that three subsequent passes relied on. `v53` is exactly this: run the guard against the
fix. Second case: *this is really `C16-M8` wearing a different hat.* Answer: M8 is about the
**ontology** not defining the vocabulary; N1 is about the **spec's own data** not exposing it. M8
survives unchanged if §3.3 gains a `web4:hash` triple tomorrow.

---

## §C — Second finding and re-measured carries

### C.1 — `C16-M8`/`B6`: STANDS, widened by measurement, and its remediation is insufficient

M8 (`sal-internal-consistency-2026-05-27.md:290`) enumerated **9** absent predicates. At HEAD §7.1 +
§7.1.1 name **15** with MUST, and **0 of 15** are defined in any of the four parseable files in
`web4-standard/ontology/` (432 triples, 121 defined subjects, merged with rdflib).

Where the 15 actually live:

| bucket | n | members |
|---|---|---|
| defined **only** in `forum/nova/web4-sal-bundle/sal-ontology.ttl` | **11** | `memberOf`, `hasAuthority`, `hasLawOracle`, `pairedWith`, `delegatesTo`, `publishes`, `hasWitness`, `hasAuditor`, `recordsOn`, `adjustedBy`, `attestedBy` |
| **weak presence** under another IRI, in the standard | **2** | `hash` → `law:hash` (`hub-law.ttl:112-116`, `rdfs:comment "SHA-256 hash of the canonical serialization"`); `scope` → `web4:scope` in `schemas/contexts/r7-action.jsonld:51`, `web4:` = `https://web4.io/ns/` |
| absent from **every** `.ttl` and `.jsonld` repo-wide | **2** | **`hasEffector`**, **`respondedBy`** |

Those 11 are a **bijection** with `sal-ontology.ttl`'s entire property set (11 of 11).

**Not re-charged, attributed by predicate (v65):** the `law:hash`-vs-`web4:hash` divergence and the
trailing-slash-vs-hash namespace split are **`C58-B6`**, charged 2026-06-15 and carried at `C134:108`,
`C170:46`, `C208:40`. The `ns/`-vs-`ontology#` split is **ratified design**
(`docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md`; `C310:426` NOT-FILED, `C312:360`
do-not-re-charge). Both are disclosable context here, not findings.

**⇒ `C16-M8`'s ratified remediation is measurably insufficient.** M8's own remediation text is
*"Promote `forum/nova/web4-sal-bundle/sal-ontology.ttl` (or a revised version) into
`web4-standard/ontology/sal-ontology.ttl`"*. Executed in full it would back **11 of 15**. This is the
`C362-N1` shape — *measure the fix you routed before someone ships it* — landing on this lineage's own
eleven-pass-old row.

**Feasibility fact about that remediation, filed against the row and not against the file:**
`forum/nova/web4-sal-bundle/sal-ontology.ttl` uses `rdf:Property` with no `@prefix rdf:` declaration
and **does not parse as Turtle** (`rdflib`: `Bad syntax (Prefix "rdf:" not bound)` at line 17). Same
defect in its two siblings — **3 of 3** forum bundles fail; **4 of 4** files in
`web4-standard/ontology/` parse clean. Confirmed with a second, independent instrument (regex
prefix-declaration set difference). Ten SAL passes have re-verified M8 with a `grep` over
`web4-standard/ontology/`; **none has ever parsed the file M8 names as the only place the vocabulary
exists** — the `v49` distinction again, a `grep` domain against a parser's class. The ratified one-line
fix shape is `C42-F5`/`C43`'s.

**Disclosure polarity (v57), checked and recorded because it runs the strengthening way.** All three
bundle READMEs describe the `.ttl` as an *"ontology patch"* — `SAL_README.md`: *"This bundle **adds**
the Society–Authority–Law (SAL) layer **to the Web4 standard**"*, `sal-ontology.ttl` — *"Turtle ontology
patch for SAL terms"* — with MUST/REQUIRED language in their Notes. None of the three READMEs contains
*draft*, *non-canonical*, *proposal*, *illustrative*, or *inbound*. (The one `Draft` hit in the bundle
is the `Status: Draft` line of its copy of the SAL spec — a line the canonical SAL carries too.) The
non-canonical status is asserted only inside **this audit tree** (`C286:115`, `C358:282`), never in the
tree that ships the files. The disclosure at the point of use asserts **coverage**, not absence.

### C.2 — N2 (LOW-MED): two MUST-required predicates were created during the carry and exist in no ontology anywhere

`web4:hasEffector` (`:276`) and `web4:respondedBy` (`:279`) were added to §7.1.1 by **`1354e4c2` / #523**
(2026-07-14, *"W4IP Phase 3 (N2): Effector Role — first-class registration"*), the same commit that is
the target's current freeze point. Repo-wide over every `.ttl` and `.jsonld` under version control,
including the M2 trees: **0 hits each.**

```
git grep -n "web4:hasEffector\|web4:respondedBy" -- '*.ttl' '*.jsonld'   →   (empty)
```

So SAL grew two normative RDF requirements **while `C16-M8` sat open**, and the vocabulary gap grew
with it — the two additions are outside even the remediation M8 proposes. Novelty: `grep -rn
"hasEffector\|respondedBy" docs/audits/` returns **4** and **0** docs respectively; the `hasEffector`
hits (`C208`, `C246`, `C286`, `C214`) all cite it as a *§7.1.1 list member*, none as an ontology
absence. **LOW-MED**, and correctly a sub-row of M8 rather than a headline — the class is M8's; only
these two members and their provenance are net-new.

---

## §D — Routing

| item | to | why |
|---|---|---|
| **`web4-core-ontology.ttl` publishes a corpus-completeness total whose denominator is majority outside the standard** — `:236-238` claims `Total classes: 21 + 4 = 25` / `Total properties: 38 + 22 = 60`. Its self-count (4/22) is exact. The `21`/`38` reconstruct **exactly** at its own commit `a37f3011` (2026-02-22) over the four files its header names at `:11-15`: t3v3 (4/14) + sal (9/11) + acp (4/5) + agy (4/8) = **21/38**. At that commit those four plus itself are the *only* `.ttl` files in the repo, so **no competing denominator reconstructs**. **17 classes / 24 properties of the published total live in three files that are not in `web4-standard/` and that no RDF tool can load.** At HEAD the sum is 22/39 (drift = `01f410db`/#581, `web4:Tensor` + `web4:observationCount`). Two further checkable claims in the same file: `:195` *"`web4:delegatesTo` is defined in `sal-ontology.ttl`"*, and `:217-220` `web4:birthCertificate rdfs:range web4:Web4BirthCertificate` — **the only dangling domain/range target in the merged standard ontology, 1 of 1 over 432 triples / 121 subjects**. Cited provenance `rdf_ontology_consistency.py` (`:20`, `:241`) resolves to `archive/reference-implementations/` — the M2 sprawl tree. | **ontology / t3-v3 track** | `web4-core-ontology.ttl` is in `web4-standard/` and the measurement is sound, but it is not SAL's subject matter. This lineage's established habit for exactly this shape is to route with the measurement and not headline it (`C310:428`, `C366:426`). **INFO, carrying the full arithmetic so the receiving track need not re-derive it.** |
| `C286-N1` — society-role vocabulary fidelity; `is_known_law_action` (`law.rs:649`) is the ratified in-file fix shape, applied to actions not roles | **HUB track** | 4th pass undischarged; re-routed, not re-adjudicated (`v51`) |
| `C366-N1` — `sal.jsonld` / `law.jsonld` unbacked; blocked on `C23-H1` | **operator (with `C23-H1`)** | unchanged; 6 passes on the gate-domain half |
| `C23-H1`, `B7`, `C50-B15`, `C58-B10`, `C16-M1/M3/M4/M5/M6`, `C23-M3/L2` | **operator / cross-track** | frozen inputs; carried |

**Standing routings inherited and NOT served by this pass:** `C374-N4` and `C390-N2` remain routed to
acp `C434` (now **4 passes old**). Recorded so the count does not silently reset.

---

## §E — Forward guards for C446 (next SAL slot)

Phrased as behaviours, not paths.

1. **Re-execute before believing any disposition on `C406-N1`.** A `web4:hash` triple appearing in §3.3
   is not the same as the `SELECT` returning rows — the FILTER binds `lct:societyRoot` and the chain
   runs `hasLawOracle → publishes → hash`. Extract the block by line range, parse it, run the query,
   publish the row count. A "fixed §3.3" that still returns 0 rows is the same defect one edit later.
2. **If §3.3 was hedged instead of extended, that is a disposition, not a dodge — but check `:104`.**
   Adding *"extract"* to `:85` while leaving *"MUST expose **these** edges"* at `:104` resolves nothing;
   the two clauses are one unit.
3. **`C16-M8`: ask about the four, not the eleven.** The remediation covers 11 of 15. If a
   `web4-standard/ontology/sal-ontology.ttl` appears, count `hash`, `scope`, `hasEffector`,
   `respondedBy` **first** — a promoted file that greens the obvious check still leaves those, and two
   of them (`C58-B6`) are a *different IRI*, not an absence.
4. **`C286-N1`, 5th pass — the same two questions only.** Did `KNOWN_ROLES` change; does any test
   assert it *matches* `society-roles.md`. Anchors have drifted on three consecutive passes: resolve by
   symbol, never by line.
5. **`C23-H1` is 10 passes / 80 days old with two dependents.** If still open at C446 the duration
   argument is the whole argument — do not manufacture a third dependent to strengthen it.
6. **Method, for whoever holds the next slot: a control answers the question you asked it.** This pass
   ran a good control against the wrong question and deflated its own strongest finding (§G.1). Before
   letting a control kill a finding, write down the finding's actual predicate and check the control
   shares it.

---

## §F — Accountability self-audit

```
surface: none — this pass produces one audit document under docs/audits/
act: none — no consequential act; ZERO mutation of web4-standard/**, hub/**, .github/**, forum/**, or any SDK file
S: low/reversible [construct: docs/audits/C406-society-authority-law-10th-delta-2026-08-18.md — additive, no reader is gated on it]
R: n/a [construct: no caller-drivable path created or changed]
W: n/a [construct: no identity or authority is asserted; findings are routed, not adjudicated]
O: pass [construct: all measurements executed before the document was written; no side effect precedes them]
A: pass [construct: every count in this document carries the command and the root that produced it; the killed control and the corrected fan-out claim are recorded in §B′.4 and §A.3, not deleted]
V: n/a [construct: nothing irreversible; the audit is a proposal to a reviewer who may reject it]
verdict: PASS
```

---

## §G — Own-error re-run

1. **I deflated my own strongest finding with a control that answered a different question.** I ran
   `mrh-tensors.md` (6 of 6 SPARQL blocks return nothing against its own turtle), read SAL's 1-of-2 as
   *above* the corpus norm, and filed §7.2's empty `SELECT` as a corpus idiom. The reviewer reversed it:
   `mrh-tensors.md` has no ratified remediation aimed at query/data agreement, so it is not the
   comparator — `0d756773` is. **The finding I nearly discarded is this pass's headline.** The control
   was well-executed and correctly interpreted for the question it answered; the error was the question.
2. **Arithmetic error in the routed measurement, caught by the reviewer.** I published the
   outside-the-standard split as **16 classes / 23 properties**. It is **17 / 24** (21 − 4, 38 − 14).
   Off by one in both dimensions, on the exact figure the routed item rests on.
3. **A "0 hits everywhere" claim that was two weak presences.** I published `hash`, `scope`,
   `hasEffector`, `respondedBy` as absent from every ontology. `web4:hash` is present as `law:hash` in
   the standard's own `hub-law.ttl` with a matching gloss, and `web4:scope` is bound in
   `schemas/contexts/r7-action.jsonld:51`. **Two of the four, not four** — and the `law:hash` half is
   `C58-B6`, this lineage's own row since 2026-06-15. `v66b` (narrow the absence to a weak presence)
   and `v65` (re-resolve by predicate) both fired, and I had run neither before drafting.
4. **I inherited my predecessor's pre-registered inflation without checking it.** C366 pre-registered
   *"if `C23-H1` is still open at C406 that is three dependents"*. It is two; my `N1` does not depend on
   H1. A pre-registration is a hypothesis, not a result — `v52`, the predecessor holds the falsifier,
   including a falsifier for its own forecast.
5. **A first draft that would have laundered an M2 charge.** My headline candidate H-A made the forum
   bundles' unparseability the *subject* of the charge. `C286:115` declines that tree as a charge target
   while itself using the same file as evidence. The distinction is real and I had stated it correctly
   in the proposal, then violated it in the wording one paragraph later.
6. **Instrument availability was not free.** `rdflib` is not in the system Python; the measurements
   required a venv (`/tmp/salvenv`, rdflib 7.6.0). Ten passes of this lineage reasoning about RDF
   vocabulary without ever installing a parser is not a coincidence — the friction is the reason.
