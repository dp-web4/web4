# C382 — `web4-lct` 9th delta audit

**Target**: `web4-standard/protocols/web4-lct.md` (blob `5f68a5c7`, 278 L)
**Date**: 2026-08-13 · **Slot**: C382 (= C342 + 40) · **Prior pass**: C342, PR #675 (`4da4e9a2`)
**Window**: `4da4e9a2..HEAD` = **35 commits** · **Mutation**: ZERO
**Lineage enumeration rule (inclusive, stated per standing rule)**: all `docs/audits/*web4-lct*`
members, C-numbered or not. Members: C74, C302, C342, C382. No non-C-numbered
`…-internal-consistency-…` member exists for this lineage.

**Verdict**: 1 MED net-new, 1 MED reach-escalation, 1 LOW, 1 instrument finding.
C342's §B.5 hand-off **DISCHARGED** (8 artifacts / 51 files, first gate row in 9 passes).

---

## Conventions

Every gate cell carries the command that produced it (v45). Every count publishes its
denominator (v40). Path names are **`web4-standard/`-prefixed** — C342's PATH TRAP binding
condition: 2 of C302's 4 tree names do not resolve from the repo root.

---

## §A — Freeze verification

```
git rev-parse --short HEAD:web4-standard/protocols/web4-lct.md   → 5f68a5c7
git log -1 --format='%h %ad' --date=short -- <target>            → 27b85624 2026-02-17
```

Target **byte-frozen 178 days** (5.9 months), blob unchanged since C74. **9th consecutive
frozen pass.** Blob identity is strictly stronger than an anchor table (C344 §A policy
collapse), so no anchor re-walk is performed; the four inherited canonical anchors
(3.2 `:718`, B8 `:393`, B12 `:190-201`, B26 `:571`) are re-resolved only on canonical motion,
and canonical did not move (below).

---

## §B — Event-trigger cadence, datapoint 16

C302 recommended, and C342 ran, an **event-triggered** cadence: motion in (1) target,
(2) canonical `LCT-linked-context-token.md`, (3) `web4-core/`, (4) `schemas/lct.schema.json`.

| # | trigger operand | result | command |
|---|---|---|---|
| 1 | target | **NEGATIVE** — blob `5f68a5c7` | `git rev-parse HEAD:<target>` |
| 2 | canonical | **NEGATIVE** — mover `d89595e8`, blob `231d70b5` (= C342 baseline) | `git log -1 -- <canonical>` |
| 3 | `schemas/lct.schema.json` | **NEGATIVE** — mover `9bcfe598`, blob `e46d5a09` | `git log -1 -- <schema>` |
| 4 | `web4-core/` | **FIRES** | `git log --oneline 4da4e9a2..HEAD -- web4-core/` → `91c1c333` |

### B.1 — The firing is a FALSE POSITIVE, and that is the finding (v55)

`git diff --stat 4da4e9a2..HEAD -- web4-core/` = **1 file, `src/r6.rs`, +38 L, 0 deletions**
(#703). The addition is `DeltaClass {Conduct, Infra, Unclassified}` plus a `class` field on
`ReputationDelta` — reputation-delta classification, no LCT structural content.

```
git show 91c1c333 -- web4-core/src/r6.rs | grep -E "^[+-].*lct"   → (empty)
```

**Zero added or removed lines contain `lct`.** The 3 `lct` tokens the naive
`git show … | grep -ci lct` reports are **context lines**, not changed lines — the exact
shape v55 warns about.

Meanwhile the trigger's actual **subject** — the three baselined LCT files — is unmoved:

| file | C302/C342 baseline mover | mover at HEAD | moved? |
|---|---|---|---|
| `web4-core/src/lct.rs` | `2ec6ae09` | `2ec6ae09` | no |
| `web4-core/src/attestation.rs` | `0e997079` | `0e997079` | no |
| `web4-core/src/ratchet.rs` | `7b048a78` | `7b048a78` | no |

**INSTRUMENT FINDING (MED, process → this ledger).** Trigger 4's **operand is a directory**
while its **subject is three files**. It has now fired twice, in two consecutive passes, and
both firings were false positives on subject matter:

- **C342**: fired on `web4-core/` `d43964e2` `role.rs` → gated NEGATIVE (C288-N2's 3rd face).
- **C382**: fires on `web4-core/` `91c1c333` `r6.rs` → gated NEGATIVE (above).

**2 of 2 firings false-positive.** This is v55 in its cleanest form: *a trip-wire reports a
difference between its operands, never a fact about its subject.* Each firing has cost a pass
a subject-matter gate that a correctly-scoped operand would not have demanded.

**Corrected trigger pre-registered for C422** — watch the movers of
`web4-core/src/{lct,attestation,ratchet}.rs`, **not** the directory:

```
git log -1 --format=%h -- web4-core/src/lct.rs          # baseline 2ec6ae09
git log -1 --format=%h -- web4-core/src/attestation.rs  # baseline 0e997079
git log -1 --format=%h -- web4-core/src/ratchet.rs      # baseline 7b048a78
```

Coverage disclosure (v55): the corrected operand covers the 3 files C302 baselined. It does
**not** cover `web4-core/src/lib.rs` or `web4-core/python/`, which name LCT but were never
baselined. That is a **stated** gap, not a silent one — C422 may widen it, but must say so.

---

## §B.5 — C342's hand-off, DISCHARGED

C342 §B.5 assigned this slot its first work by name: six `web4-standard/` trees and two root
fixtures that *"have never had a gate row"*, `submission/` first (v29, outward tree).
All six of C342's published counts **reproduce exactly at HEAD**.

**Gate matcher (published, v44/v45)** — a file is a *structural claimant* iff it asserts an
LCT object field:

```
git grep -lE '"(lct_id|entity_type|birth_certificate|binding_proof)"' -- web4-standard/<tree>
```

| tree | files | names LCT | **structural claimants** | disposition |
|---|---|---|---|---|
| `web4-standard/rfcs/` | 9 | 8 | **0** | M-DECLINE — names only |
| `web4-standard/testing/` | 22 | 7 | **1** → `testing/test-vectors/modbatt-can-vectors.json` | **ADMITTED** → §E |
| `web4-standard/docs/` | 7 | 3 | **0** | M-DECLINE — names only |
| `web4-standard/proposals/` | 5 | 3 | **0** | M-DECLINE — proposals tier, no authority over canon (C302 tier rule) |
| `web4-standard/submission/` | 4 | 2 | **1** → `submission/draft-palatov-web4-core-00.txt` | **ADMITTED** → §C |
| `web4-standard/profiles/` | 4 | 1 | **0** | M-DECLINE — names only |
| `test_lcts_{rdf,simple}.json` | 2 | 2 | **0** | **M-DECLINED (closed)** → §F |

**Denominator: 51 files across 6 trees + 2 fixtures = 53 artifacts. Exactly 2 make an LCT
structural claim.** Both were previously ungated by any lineage; both are dispositioned below.
The 49 that merely *name* LCT exit M-DECLINE on the stated rule — **naming is not claiming**.

C422 inherits this as a **closed** table: re-run the one matcher above, compare to `0/1/0/0/1/0`,
and only re-derive a tree whose count changed.

---

## §C — N1 (MED, net-new): the outward IETF submission publishes an LCT object structure that disagrees with the target spec, the enforced schema, and the live draft

**Locus**: `web4-standard/submission/draft-palatov-web4-core-00.txt:236-250` (§3.1,
"Linked Context Tokens (LCTs)", under `Structure:` at `:236`).

The outward draft publishes this LCT object:

```json
{ "lct_id": "...", "entity_type": "human",
  "binding": { "public_key": "...", "created_at": "...", "binding_proof": "..." },
  "mrh": { "bound": [], "paired": [], "witnessing": [] } }
```

Measured against the **target** (`protocols/web4-lct.md:9-49`, whose §1 says the object
**MUST** be represented as shown) and the **enforced schema**
(`schemas/lct.schema.json`, `required = [lct_id, subject, binding, birth_certificate, mrh, policy]`,
`binding.required = [entity_type, public_key, created_at, binding_proof]`):

| divergence | outward draft | target `web4-lct.md` | schema |
|---|---|---|---|
| `entity_type` placement | **top level** `:239` | `binding.entity_type` `:14` | `binding.entity_type` |
| `binding.entity_type` | **absent** | present `:14` | **required** |
| `subject` | **absent** | present `:12` | **required** |
| `birth_certificate` | **absent** | present `:20` | **required** |
| `policy` | **absent** | present `:41` | **required** |

**3 of 6 schema-required top-level fields are absent, and the one field the draft does place
at top level is the one field the standard places inside `binding`.**

### C.1 — Direction test (v55; `git log -S`, per file)

This is *not* an artifact that predates the shape it violates:

```
git log -S'"entity_type": "human|ai|organization' -- web4-standard/protocols/web4-lct.md
  → 4e5c13c8  2025-09-11   (target settles on binding.entity_type)
git log -S'"entity_type": "human",' -- web4-standard/submission/draft-palatov-web4-core-00.txt
  → deaa108f  2025-09-15   (outward draft publishes the top-level shape)
```

The outward draft was written **4 days after** the canonical shape existed, and diverged from
it. The direction is *downstream-and-wrong*, not *upstream-and-once-right*. The draft's own
prose knows the missing field: `:260` lists *"Birth Certificate: Paired with citizen role in a
society"* as lifecycle step 2 — the structure omits the field its own lifecycle requires.

### C.2 — The live draft publishes nothing to correct it

```
grep -cE "lct_id|birth_certificate|binding_proof|\"entity_type\"" submission/draft-web4-core-00.xml → 0
```

`draft-web4-core-00.xml` — the draft `SUBMISSION_GUIDE.md:9` declares current, and the one
`:36` names as the upload — carries **only a one-sentence prose gloss** (`:111`, *"A permanent,
non-transferable digital identity token bound to an entity"*) and **no LCT object structure at
all**. So across the entire outward surface, an external reader or IETF reviewer meets either
**nothing** or **the wrong shape**. There is no outward artifact that publishes the correct one.

### C.3 — Novelty (v44 — absence claim, matcher published)

```
git grep -ohE "draft-palatov-web4-core-00\.txt:[0-9]+" -- docs/audits/ | sort -u
  → :350  :567  :617  :618  :798
```

Eight audit docs cite this file; **not one cites the `:231-260` structure block.** The five
cited loci belong to other lineages (`:617-619` = C336-N1/C376 crypto table; `:567`/`:868` =
C344 `actor`/`roleType`; `:798` = C366 `mrh.jsonld`; `:350` = C344 `web4:Developer`). This
lineage's own three prior docs cite the file **once**, at C74 `:36`, purely as an *inbound
referrer count* — never as an examined structure.

⇒ **In 9 passes, no one has read the LCT object structure in the outward submission**, though
LCT object shape is precisely this lineage's subject matter.

### C.4 — Refutation of my own best finding (standing rule)

1. **"This is C288-N1 re-filed."** **Fails on the reviewer's rule** (a re-file shares *normative
   locus* **and** *defect mechanism*). C288-N1's locus is `lct.schema.json` and its mechanism is
   required-list staleness. This locus is an outward `.txt`; the mechanism is a publication
   artifact disagreeing with the standard it submits. Neither matches.
2. **"It's C302-N2 / B7 (the 12-vs-15 `entity_type` enum)."** **Fails.** B7 is about the enum's
   *cardinality*; this is about the field's *placement* and three *absent* siblings. Note the
   target's `:14` enum lists **12** values vs the schema's **15** — that **is** B7, it is
   **not re-filed here**, and it is deliberately excluded from the table above.
3. **"Illustrative artwork, not normative."** **Survives partially; sets severity.** The block
   is prefixed `Structure:` and is the document's only LCT object. Against HIGH: it is
   elision-styled and the draft is expired. Net: **MED**, matching C336-N1/C340-N1 — the same
   file, comparable mechanism, deliberately kept comparable.
4. **"The draft is expired, so it doesn't count."** **Fails, and is already adjudicated.**
   C300 §B′.4 **ADMITTED** this file as a spec peer with expiry as *severity-down, not
   exclusion*; C340 `:272` ruled the XML live and palatov retired. I adopt both rulings
   unchanged — and neither examined the structure block.

**Severity: MED. Routing: outward-artifact maintainer / operator. NOT self-applied**
(ZERO-mutation discipline; and per C340's reasoning, a patch would close the symptom while
leaving the regeneration channel unwired — an operator decision, not the auditor's).

---

## §D — N2 (MED, reach-escalation on C300 §B′.4 / C340 `:272`): the corpus publishes **two** submission-process instruments naming **two different** outward drafts, and the admission rulings saw one of them

C300 and C340 both grounded the live-vs-retired ruling on a single instrument:

> C340 `:272` — *"`SUBMISSION_GUIDE.md:9` names `draft-web4-core-00` as the draft and `:36`
> names the `.xml` as the upload. The XML is the live one; palatov is the retired one."*

That instrument is `web4-standard/submission/SUBMISSION_GUIDE.md` (214 L, mover `27b85624`).
There is a **second**: `web4-standard/SUBMISSION_PROCESS.md` (331 L, mover `deaa108f`), at the
standard's root, which under `#### Prepare Internet-Draft` declares:

```
SUBMISSION_PROCESS.md:18   Filename format: draft-palatov-web4-core-00.txt
```

| instrument | lines | declares current | mover |
|---|---|---|---|
| `submission/SUBMISSION_GUIDE.md` `:9` | 214 | `draft-web4-core-00` | `27b85624` 2026-02-17 |
| `SUBMISSION_PROCESS.md` `:18` | 331 | `draft-palatov-web4-core-00.txt` | `deaa108f` 2025-09-15 |

**It is an orphan** (v47/v48 — a citation query cannot see an orphan; the domain-word sweep can):

```
git grep -lF "SUBMISSION_PROCESS" -- docs/audits/ web4-standard/docs/audits/   → 0
```

**Zero mentions in any audit document, ever** — across every lineage, in ~190 audit docs. It
surfaced only in this pass's v36 domain-word residue, and only because it is one of exactly two
non-audit referrers to the draft (`git grep -l "draft-palatov" -- . ':!docs/audits'` → the file
itself + `SUBMISSION_PROCESS.md`).

**This does not overturn C340's ruling — it measures its denominator.** C340's conclusion
(XML live, palatov retired) is independently supported by expiry `:7` and by
`SUBMISSION_GUIDE.md:36`. What is new is that the corpus contains a **co-equal, larger,
never-examined instrument that says the opposite**, and every admission ruling to date had a
denominator of **1 of 2** without declaring it. Per v50, when a corpus publishes two co-equal
instruments, *the diff between them is data*.

This is **filed as a reach-escalation, not as net-new** (v51 — the SUPERSEDED/ADMITTED verdicts
of C300 and C340 are scoped to the loci they were measured on). **Routed to the
outward-artifact owner together with N1** — they are the same decision: whether `submission/`
is regenerated, pinned, or retired. Do not adjudicate separately.

---

## §E — N3 (LOW): `modbatt-can-vectors.json` — the other structural claimant

`web4-standard/testing/test-vectors/modbatt-can-vectors.json` (mover `18209449`, 2025-09-11;
**0 audit-doc mentions ever**) is the only structural claimant in `testing/`:

- `test_vectors[0].inputs.entity_type = "DEVICE"` — **uppercase**; the schema enum
  (`binding.entity_type`) is lowercase, `device`.
- `outputs.lct_id = "..."` and `outputs.binding_proof = "..."` — both **elided**.

**LOW, and deliberately not escalated.** The elision self-discloses at the point of use: with
both cryptographic outputs as `"..."` nothing can execute this vector, so the casing cannot
propagate into an implementation. Recorded as a gate row so C422 inherits it measured rather
than unexamined. Not routed.

---

## §F — Fixtures: M-DECLINED, closed (policy-review condition C1)

This pass proposed charging `web4-standard/test_lcts_{rdf,simple}.json` for failing
`lct.schema.json` on 6 of 6 required fields. **Policy review struck it before it was written**,
on three grounds I independently re-verified. Recording the executed baseline so C422 inherits
a **closed** question (C378's discipline):

1. **Different JSON path.** The registered enum is at `binding.entity_type`
   (`schemas/lct.schema.json:21-24`, 15 values). The fixtures carry a **top-level**
   `entity_type`. `python3 -c "…'entity_type' in s['properties']"` → **False**: the schema has
   no top-level `entity_type` to violate. Comparing them compares two fields sharing a name.
2. **They predate the schema** (`--diff-filter=A`, per file): fixtures `c963853b` **2025-09-13**;
   `lct.schema.json` `c66792fd` **2025-09-14**.
3. **They conform to their own declared spec.** `MRH_RDF_SPECIFICATION.md:43-73` (fenced block
   `:42-74`) publishes exactly their shape — `lct_version` `:44`, `entity_id` `:45`, `mrh` `:46`
   — and `awk 'NR>=43&&NR<=73' … | grep -c entity_type` → **0**: the declared object carries no
   `entity_type` at all, so the third fixture object's missing `entity_type` is the spec's
   shape, not an omission.
   `git grep -ln lct_version` → **11 files, all MRH/MCP-entity family**, none LCT-schema.
4. **Both are generated artifacts, and both regenerate.** `mrh_migration_tool.py:416-420`
   *writes* `test_lcts_simple.json` from an in-memory literal and emits `test_lcts_rdf.json`
   from it — the pair is **output/output**, not input/output. Re-run in a clean tmpdir (v33 —
   never in the counted tree): `test_lcts_simple.json` **byte-identical**;
   `test_lcts_rdf.json` **normalized-equal** (generation timestamps only).
   Consumers: **0**. This is `C338:147`'s build-artifact precedent plus C378's
   `schema_registry.json` shape.

⇒ **M-DECLINED. Do not resurrect.** The gate matcher in §B.5 independently returns **0**
structural claimants for both files, corroborating the decline from a second direction.

---

## §G — Kills and do-not-re-file (carried forward)

Inherited from C302 §E and C342 §E, all re-affirmed:

- LCT vectors failing `lct.schema.json` = **C288-N1** (sibling canonical lineage). *Kill owned
  by **C302 §E.1** (`C302:23`, `:433`) — **not** C342 §E, as this pass's own proposal
  mis-stated; corrected per policy-review condition C3.*
- C342 §E's five kills: demo ids vs schema pattern · the two-scheme collision · `E-M1` as
  net-new · `role.rs` as an LCT finding · the §B′ resurrection.
- Rust `EntityType`=9 = C176-N1/C292. §1 `rotate` / context-3-vs-5 / revocation-2-vs-3 =
  B3/B2/B4. `C302-N2` (B7/B8/B9), `C302-N3` (`peer` witnessing role).
- **New this pass**: the fixtures (§F) · "the two drafts have different names / the `.txt` is
  expired" — **C300 §B′.4 and C340 `:272` own this**; N2 escalates its *denominator*, and does
  not re-charge it.

**Still open, operator-gated, NOT self-adjudicated**: flagship **B-D1** (SSOT inversion) ·
**D0** (protocols/ cluster remediation) · `C33 E-M1` + `C316-N1`, held in this ledger by name
since C342, all three pre-registered greps re-run **unchanged**.

---

## §H — Policy review record, and this pass's own errors

**Policy review returned APPROVED with 5 binding conditions**, and — for the **seventh
consecutive pass** — falsified a premise the session submitted:

| condition | effect | status |
|---|---|---|
| C1 | strike the fixture charge; publish as closed disposition | §F |
| C2 | the fixture pair is **output/output**, not input/output | §F.4 |
| C3 | the C288-N1 kill is **C302 §E.1**'s, not C342 §E's | §G |
| C4 | measure the trigger's **coverage**, not just its firing; pre-register the corrected trigger | §B.1 |
| C5 | publish the matcher for any surviving absence claim | §B.5, §C.3, §D |

**Own errors, stated plainly:**

1. **The proposal's headline was wrong.** I opened by charging the two root fixtures and
   proposed the trigger firing as a routine gate. Review inverted both: the fixtures are a
   category error, and the *false* firing was the finding. All three of the review's grounds in
   §F were re-verified by me independently before adoption (v52 — verify the reviewer's
   corrections too); all three hold exactly.
2. **I mis-attributed the C288-N1 kill** to C342 §E when it is C302 §E.1's — the `C374-N4`
   shape, corrected in §G.
3. **I mis-described the fixture pair as input/output** from `mrh_migration_tool.py:416-417`,
   reading two lines where `:419-420` shows the tool *writes* the "input" as well.
4. **The `web4-core` trigger nearly passed on a naive matcher.** `git show … | grep -ci lct`
   returns **3** and would have justified a subject-matter investigation; `grep -E "^[+-].*lct"`
   returns **0**. The naive count reads *context lines*. Same failure family as v55's
   `git log -1` on a directory: plausible enough to survive review.

5. **I inherited a reviewer-supplied line range without verifying its extent.** Policy review
   cited `MRH_RDF_SPECIFICATION.md:43-52`; the fenced block is `:42-74` and `:43-52` stops
   mid-`@context`, so the range does not contain the object it was cited for. I verified the
   *content* of the correction and not its *anchor* — a partial application of v52. Corrected
   to `:43-73` in §F.3 with a per-field anchor and an executable zero. Caught by this pass's
   own anchor self-check, not by a reviewer. **This is the C366/C372/C378 path-token class
   recurring from a new direction: an anchor handed to you by a reviewer is still your cell.**

No reviewer correction was rejected this pass; one was adopted with its anchor corrected (5).

---

## §I — Carry to C422 (next `web4-lct` delta, = C382 + 40)

1. **Corrected event trigger** (§B.1) — watch `web4-core/src/{lct,attestation,ratchet}.rs`
   movers, **not** `web4-core/`. Baselines: `2ec6ae09` / `0e997079` / `7b048a78`. Stated
   coverage gap: `lib.rs`, `python/`.
2. **§B.5 is CLOSED** (§B.5) — re-run the one published matcher, compare to `0/1/0/0/1/0`.
   Re-derive only a tree whose count changed. **Do not re-derive the table.**
3. **N1 + N2 are ONE routing** to the outward-artifact owner. If still open at C422, that is
   two passes; report it as a routing failure, not as a re-finding (v32/v36 — routing by slot
   is not delivery; probe the **receiver's ledger**, not its spec files).
4. **Cadence: datapoint 16.** Target frozen 5.9 months; 3 of 4 triggers negative and the 4th
   false-positive for the 2nd consecutive pass — yet the pass yielded 2 MED, both **from the
   outward tree, not from the target**. Same signature as C342 (yield from the inbound sweep,
   not the target). This is now a **two-pass pattern**: for this lineage the target is inert
   and the *periphery* is where defects live. Recommend C422 spend its budget accordingly —
   operator's call, not self-applied.
5. **Baseline unchanged**: target `5f68a5c7`, canonical `d89595e8`, README `d89595e8`,
   `lct.rs` `2ec6ae09`, `attestation.rs` `0e997079`, `ratchet.rs` `7b048a78`,
   `lct.schema.json` `9bcfe598`.

---

## Review-gate block (accountability self-audit)

```
surface: C382 audit document   act: publish audit findings + route to operator (no state mutation)
S: low/reversible [construct: doc-only, ZERO mutation; git-revertible]
R: n/a [construct: no caller-reachable surface created]   W: pass [construct: signed commit, worker branch, PR review by separate track]
O: pass [construct: policy review (Step 4) precedes all findings; §F charge struck BEFORE it was written]   A: pass [construct: this doc commits findings + evidence-basis + own-errors together]
V: present [construct: §C.4 self-refutation; §F struck charge; operator-gated items B-D1/D0 NOT self-adjudicated]
verdict: PASS
```
