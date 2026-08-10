# C350 — `core-spec/t3-v3-tensors.md`, 9th delta (the evidence half of `DimensionScore` cannot be serialized, and the test that guards the serialization is green because it only asks about the half that can)

**Date**: 2026-08-10
**Target**: `web4-standard/core-spec/t3-v3-tensors.md` — blob `32d3368e`, 689 lines
**Prior pass**: [C310](C310-t3-v3-tensors-8th-delta-2026-08-02.md) (8th delta), base `60926fa7`
**This pass's HEAD**: `03b61ac2`
**Window**: `60926fa7..03b61ac2`, **56** commits, 2026-08-01 → 2026-08-09
**Spec mutation this pass**: **ZERO.** No spec, schema, ontology, context, SDK, vector or config file is
edited by this pass — including the three artifacts N1 convicts.

**Lineage — membership rule stated, and applied to this lineage the same way it is applied to any
lineage this pass charges** (`#681` member 4; `C348 rev1` §F.5 item 1). Inclusive rule: every
`docs/audits/` document whose name matches `t3-v3` or `t3v3`, C-numbered or not.

```
git ls-tree -r --name-only 03b61ac2 -- docs/audits web4-standard/docs/audits | grep -icE 't3-v3|t3v3'
  →  12
```

`t3-v3-tensors-internal-consistency-2026-05-24` · `2026-04-27-canonical-t3v3` ·
`cross-language-t3v3-alignment-2026-05-13` · C42 · C82 · C121 · **C122 (remediation)** · C154 · C192 ·
C230 · C270 · C310 → **C350 (13th document, 9th delta)**.

> C310's header enumerates the lineage **exclusively** — *"C42(1) C82(2) C121(3) C154(4) C192(5)
> C230(6) C270(7) → C310 (8th)"* — dropping the remediation `C122` and all three non-C-numbered
> members. Stated, not smoothed: this pass is the **9th delta** by C310's count and the **13th
> document** by the inclusive rule, and both numbers are true of different questions. Note the
> consequence, because it is not cosmetic: **`C270-N3` is the carry *"the pre-C-series
> `cross-language-t3v3-alignment` audit never entered the ledger"*, and the inclusive rule is what
> admits it.** A lineage that enumerates itself exclusively cannot close that carry with a count.

---

## Scope of this pass — declared, because it is deliberately narrower than a full delta

This session's budget was committed first to clearing a standing block on PR #682 (`C348 rev1`). The
policy reviewer returned **REVISE on proportionality**, on an argument worth recording: for **three
fires running** (C344, C346, C348) the *entire yield* came from the v36/v37 inbound set difference,
while the heavy §A mirror-layer freeze sweep and the full per-carry probe re-execution consumed most of
the tokens and returned green — and the own-error count has been climbing (3 → 4) across those fires,
i.e. quality was already under strain at *full* budget.

**Run this pass**: the v36/v37 inbound set difference (§B); a two-command freeze measurement on the
**target file only** (§A); a **carry-disposition** re-check (§D). **Not run**: the mirror-layer blob
sweep, and fresh probe re-derivation of each C310 carry.

The two-command freeze was submitted back for re-review rather than taken silently, and approved with a
guardrail now discharged in §A: *a disposition-only re-check is sound only if the target has not
moved,* because C310 holds its carries **by construction against the target's own text**. Had the
target moved, every §D row would be flagged **provisional**. It did not. §D rows are labelled
**disposition-checked, not re-derived** regardless, so no row here claims more than it measured.

---

## Verdict

Target byte-frozen for the **9th** consecutive pass, and the window contains exactly **one** commit
that can reach any artifact in this lineage's orbit. The pass is not empty, and nothing in it came from
the diff or from re-reading the spec.

| # | Severity | Class | Owner |
|---|---|---|---|
| **N1** | **MEDIUM** | net-new — **all three evidence properties** of `web4:DimensionScore` fail to survive the standard's own JSON-LD serialization; C310-N2 found one of the three and charged it alone | schema + ontology owner (**do not self-apply**) |
| **N2** | **LOW** | net-new, instrument → the C314 / acp lineage — C314 measured this defect, scored it as a coverage percentage in its own baseline, and routed nothing to the owner | C314 lineage + operator |
| **N3** | **INFO** | reception — `C318-I-1` was routed to this lineage by name on 2026-08-05 and is **received and adjudicated here, at the first opportunity**. Delivery worked | this ledger (discharged here) |
| **N4** | **INFO** | discharge — `C310-N3` was consumed **by the standard itself** (`8d3808db`, #637), which cites it by id *and path* inside executable code. Nothing told this ledger | this ledger + SDK/build track |

---

## §A — Freeze (target only; two commands, per the approved scope)

```
git rev-parse --short 03b61ac2:web4-standard/core-spec/t3-v3-tensors.md   →  32d3368e
git log --oneline 60926fa7..03b61ac2 -- web4-standard/core-spec/t3-v3-tensors.md   →  0 commits
```

**`32d3368e` is byte-identical to C310's published blob.** The guardrail attached to this measurement
is therefore **discharged**: no C310 carry anchors into changed text, and §D's disposition-only method
is sound rather than merely cheap. Last content commit `d89595e8` (#531, 2026-07-16) — **25 days**.

**v39 fires on this file's own name, immediately.** `git ls-tree -r --name-only 03b61ac2 | grep -c
"/t3-v3-tensors.md$"` → **2**: `web4-standard/core-spec/t3-v3-tensors.md` (`32d3368e`, 689 L) and
`forum/nova/web4-sal-bundle/t3-v3-tensors.md` (`0e37a65d`, 374 L). Every path in this document is
repo-relative for that reason. (This is the carry written four hours before this pass, clearing the
block on #682; the target of *this* slot is one of the eight basenames that mirror tree shadows.)

**Window motion into the mirror layer — one command, and it returns one commit.**

```
git log --oneline 60926fa7..03b61ac2 -- web4-standard/schemas/ web4-standard/ontology/ \
    web4-standard/test-vectors/ web4-standard/implementation/sdk/
  →  8d3808db  test(standard): gate that every @context URI in test-vectors has a backing file (#637)
```

That commit is **N4**.

---

## §B — The inbound set difference, run FIRST (v36 as a set difference, v37)

```
git grep -l "t3-v3-tensors" 03b61ac2 -- docs/audits web4-standard/docs/audits      →  69
  minus the 12 lineage documents (inclusive rule)                                  →  58 non-lineage
```

**Verb set PRE-REGISTERED before the run** (v26):
`owner|route|routed|carry|carried|owed|addressee|cross-track|next pass|lineage|slot`, applied to lines
already matching the target token.

**Two widenings, both of which paid.**

1. **By slot number (v32's shape).** `git grep -n "C350" -- docs/audits web4-standard/docs/audits`
   returns **2 hits, both inside C310 itself** — this lineage's own forward guards. **No sibling
   lineage routed anything to this slot by number.** Recorded because a *negative* on the v32 channel
   is what makes the positive on the v36 channel interpretable.
2. **By subject matter, not label** (the standing carry: *a row collapsed to a bare label will not
   match its described form*). Re-running the corpus on `t3v3|T3/V3|t3-v3|t3_tensor|v3_tensor` and
   restricting to non-lineage documents **postdating C310** returns **11** documents where the
   filename-token sweep returned **3**. The residue lives entirely in the 8 the broader token found.

**Residue — rows this ledger does not hold, all postdating C310 (2026-08-02):**

| row | source | date | held at C310? | → |
|---|---|---|---|---|
| `validate_vectors.py` mischaracterised by C270; five files share the basename | `C318-I-1` | 2026-08-05 | **no** — postdates C310 by 3 d | **N3** |
| `t3v3-jsonld.schema.json` vs `contexts/t3.jsonld`+`v3.jsonld`: **2 undefined properties**, named | `C314:201` | 2026-08-05 | **no** — never routed here | **N2 / N1** |
| `t3v3.jsonld` `KNOWN_MISSING` entry citing `C310-N3` by id and path | `8d3808db` (#637) | **2026-08-04** | **no** — it *is* the reception | **N4** |
| `C310-N3` re-reported from the gate's output by three sibling lineages | `C322:42`, `C338:81`, `C344:360` | 08-06 → 08-09 | n/a | context for N4 |

**The entire yield of this pass came from the inbound sweep, for the fourth consecutive fire on this
track.** N1 is the residue's second row, followed to its cause.

---

## §C — Findings

### N1 (MEDIUM, net-new) — every evidence-bearing property of `web4:DimensionScore` fails the standard's own JSON-LD round trip, and C310-N2 is one member of that class rather than a lone defect

**The class, measured.** `web4:DimensionScore` carries five properties in the ontology this spec
normatively cites. Here is each one against the two machine-readable artifacts that are supposed to
serialize it — `web4-standard/schemas/t3v3-jsonld.schema.json` and
`web4-standard/schemas/contexts/t3.jsonld` (`v3.jsonld` is identical on every cell below):

| ontology property (`web4-standard/ontology/t3v3-ontology.ttl`) | JSON key in the **schema** | term in the **context** | round trip |
|---|---|---|---|
| `web4:dimension` `:87` | `dimension` | `dimension` | ✅ |
| `web4:score` `:92` | `score` | `score` | ✅ |
| `web4:observedAt` `:97` | **`observed_at`** | **`observedAt`** only | ❌ **mutually exclusive** |
| `web4:witnessedBy` `:102` | **`witnessed_by`** | **`witnessedBy`** only | ❌ **mutually exclusive** |
| `web4:observationCount` `:107` | *absent* | *absent* | ❌ **C310-N2** |

**The two that round-trip are the value. The three that fail are the evidence** — *when* the score was
observed, *who* witnessed it, and *how many* observations back it.

**Why "mutually exclusive" and not "one of them is wrong".** `$defs.DimensionScore` sets
`"additionalProperties": false`. So a document that uses the **context's** spelling is **rejected by the
schema**; and a document that uses the **schema's** spelling carries two terms that neither context
defines, and neither context sets `@vocab` (`t3.jsonld` and `v3.jsonld` declare `@version: 1.1` and
nothing else at the `@`-level), so under JSON-LD 1.1 those two keys are **dropped on expansion**. There
is no document that satisfies both artifacts and retains the evidence.

**Executed, not read** (v27) — the standard's own published vector, against the standard's own schema:

```
web4-standard/test-vectors/schema-validation/t3v3-jsonld-validation.json, valid case [4]
  as published        (observed_at / witnessed_by)  →  VALID   against t3v3-jsonld.schema.json
  same doc, context's (observedAt  / witnessedBy )  →  INVALID: additionalProperties false
```

`jsonschema` 4.26.0. **`rdflib` and `pyld` are not installed on this host** (`ModuleNotFoundError`,
both) — so the *schema* half above is a machine check and the **expansion half is hand-derived from
the two context files' `@`-level keys and labelled as such**, never as a machine check. That labelling
is C310's own method note 3, honoured.

**The guard that should have caught it is green because of what it ranges over.**
`web4-standard/implementation/sdk/tests/test_t3v3_jsonld.py:484` is exactly the right test:

```python
def test_dimension_scores_keys_mapped(self, t3_context):
    doc = T3(0.8, 0.7, 0.6).to_jsonld()
    for ds in doc["dimension_scores"]:
        for key in ds:
            ...
            assert key in t3_context, f"DimensionScore key '{key}' missing from context"
```

It iterates the keys the **SDK emits**. `T3.to_jsonld()` (`web4-standard/implementation/sdk/web4/
trust.py:230-234`) emits `{"dimension": …, "score": …}` and nothing else. So the assertion ranges over
**2** of the 5 properties — precisely the 2 that round-trip — and is silent on the 3 that do not.
`python3 -m pytest tests/test_t3v3_jsonld.py -q` → **77 passed**. **v27, in its purest form: the gate
is not weak, it is correctly written over the wrong domain**, and the domain it was given is the
emitter rather than the schema.

**Direction — the defect is original, not introduced.** The obvious story is that the 2026-03-24
JSON-LD namespace reconciliation split the shared `t3v3.jsonld` into `t3.jsonld` + `v3.jsonld` and
changed the casing in transit. **It did not.** The retired context is still in the tree and can be
read:

```
web4-standard/ontology/t3v3.jsonld  →  terms include observedAt, witnessedBy
                                       observed_at: absent · witnessed_by: absent
```

Every context this spec has ever had uses camelCase for these two; the schema has always used
snake_case. **The reconciliation is exonerated and the split is older than the artifact split.** Note
also that `t3.jsonld` carries **both conventions in the same `@context` object** — `composite_score`
and `dimension_scores` are snake_case, `observedAt` and `witnessedBy` are camelCase — so this is not a
context-wide convention the schema disagrees with; it is a two-term exception **inside** the context,
and those two terms are exactly the two the schema forbids.

**Three refutations attempted.**

1. *"The schema describes a different serialization than the context does."* — **Fails on the
   artifacts' own names and contents.** The file is `t3v3-**jsonld**.schema.json`; the documents that
   validate against it carry `@context`; and the schema's own property descriptions read *"When this
   score was observed (**web4:observedAt**)"* and *"LCT that witnessed this score
   (**web4:witnessedBy**)"* (`:29`, `:33`). The schema author named the RDF property correctly and
   then chose a JSON key no context maps to it. The two artifacts are describing the same documents
   and they know it.
2. *"`@vocab` or a term alias rescues the undefined keys."* — **Checked and false.** Neither context
   has any `@`-level key but `@version`, and neither defines `observed_at` or `witnessed_by` under any
   spelling.
3. *"This is C310-N2 re-raised under a new name."* — **Fails on membership.** C310-N2 is
   `observationCount`: a property the `.ttl` gained in-window that the schema **forbids by absence**.
   N1 is `observedAt`/`witnessedBy`: properties the schema **defines**, under a key no context maps.
   Different mechanism, different artifacts, opposite direction. What is net-new is neither of them
   individually — it is that **they are one class**, and that the class is *"the evidence half of
   `DimensionScore`."* C310 charged the third member without the first two, which is why it read as a
   single schema/ontology desync rather than as a hole in the trust model's serialization.

**Why MEDIUM and why it is worth an operator's attention beyond the numbers.** The `.ttl`'s own comment
on the property C310 already convicted states the principle the whole class violates:

> `web4:observationCount` … *"Load-bearing for sufficiency queries (how many observations, how fresh) —
> **a relying party weighs a score by its evidence, not just its value.**"*

That sentence is the ratified §1.2 discipline, written into the ontology. **The serialization layer
drops exactly what it says is load-bearing** and keeps the bare number. An implementation that emits
T3/V3 through the standard's own schema and consumes it as RDF through the standard's own context
receives scores stripped of when, by whom, and on how much — the shape §1.2 exists to forbid. No byte
of the target moves and no conformant implementation is currently *wrong*, because the SDK emits
neither spelling and the only published documents that carry the properties cite a context that does
not exist (C310-N3). **The defect is latent and it becomes live the moment C310-N3's routed remedy is
applied** — see the disposition.

**Disposition — ROUTED, ZERO mutation. And the routed remedy for C310-N3 is not safe as written.**
`web4-standard/test-vectors/validate_context_refs.py:49-56` routes `t3v3.jsonld` with the disposition
*"add the context file, **or repoint the vectors at t3.jsonld / v3.jsonld**."* Taking the second branch
on the 2 published valid cases that carry these properties converts them from *citing a missing
context* to *silently losing two fields against a present one*. **A pass on that gate would then be
true and the data loss would be complete.** The fix is not the auditor's: three shapes are available to
the owner — add `observed_at`/`witnessed_by` as term aliases in both contexts; rename the schema keys
to camelCase (breaks the 2 published vectors and any consumer of them); or declare snake_case
canonical and regenerate both contexts (touches `composite_score`/`dimension_scores` consistency, and
`observationCount` with it). **Choosing among these is a normative decision about the standard's JSON
naming convention, not an audit fix.** Route: **schema + ontology owner + operator**, and it should be
adjudicated **jointly with C310-N2 and C310-N3**, because all three are the same five-row table.

### N2 (LOW, net-new, instrument → the C314 / acp lineage) — the finding was measured by a sibling lineage, scored as a percentage, and never routed to the owner

`C314-acp-framework-8th-delta-2026-08-05.md:201` builds a schema↔context coverage baseline across all
11 pairings in the standard, and its `t3v3` row says, in full:

> *"**Scored against the union: 2 undefined, 88.9%.** … The residual 2 under every treatment are
> `DimensionScore`'s `observed_at` and `witnessed_by`, undefined in both."*

**C314 named the exact two properties, in the exact two artifacts, and got the measurement right.** It
then recorded them as the residual of a coverage score, in a baseline table owned by the acp lineage,
and routed nothing to the t3-v3 lineage — whose **permanent** mirror set includes
`schemas/t3v3-jsonld.schema.json`, `schemas/contexts/t3.jsonld` and `schemas/contexts/v3.jsonld` by
C310's own method note 2. C314's forward guard (`:258`) asks its *next* pass to re-derive the same
table; nothing in it asks the owner anything.

**This is v37 in the direction C346 established**, one level up from a carry: not a disposition written
into the wrong ledger, but a **measurement** filed as an instrument cell in the measurer's ledger when
its subject belongs to another. The mechanism is worth naming precisely, because it is not
carelessness: **a coverage metric converts a defect into a denominator.** `2 undefined / 88.9%` is a
true statement about instrument quality and a *lossy* statement about the corpus — the number survives,
the two property names survive in prose, and the question *"can this document round-trip?"* is never
asked, because coverage does not ask it. C314 was three lines from N1 and the shape of its instrument
is what stopped it.

**Severity LOW** — it charges an instrument's routing, not a conclusion, and C314's own measurement is
correct. Recorded rather than dropped because C314's baseline is explicitly designed to be *inherited*
by later passes (`:258` *"Re-derive it; do not inherit these cells"*), so the 88.9% cell will be
re-measured for as long as the defect lives, in a ledger that cannot fix it.
**Route: C314 / acp lineage + operator.** Not auditor-applicable.

### N3 (INFO, reception) — `C318-I-1` was routed to this lineage by name and arrived at the first opportunity

`C318-mrh-tensors-8th-delta-2026-08-05.md:416` and `:467`:

> *"**I-1**, routed to the t3-v3 lineage: C270 §2 characterises
> `web4-standard/test-vectors/validate_vectors.py` as *'a JOSE/COSE canonicalization checker — not a
> tensor harness.'* It **is** a tensor harness … **C270's conclusion survives untouched** — one
> supporting cell is wrong, and the cause is a basename that collides five ways."*

**Re-measured here, not accepted:**

```
git ls-tree -r --name-only 03b61ac2 | grep '/validate_vectors.py$'   →  5 files
grep -n 'def validate_t3v3' web4-standard/test-vectors/validate_vectors.py   →  :106
python3 web4-standard/test-vectors/validate_vectors.py   →  87 passed, 0 failed
```

C318 is **correct**, and C270's cell (`C270:112`) is wrong: the file at
`web4-standard/test-vectors/validate_vectors.py` defines `validate_t3v3()` and executes 87 t3v3+atp
assertions. **C270's conclusion is untouched and is not re-litigated** — `grep -rn tensor-operations
--include=*.rs . | grep -v target` → **0**; the Rust-side claim in `C270-N2`, which C310 already
narrowed to *"Rust side only"*, stands. **C270 is not rewritten** (v11). The correction is recorded
here and `C318-I-1` is **CLOSED — RECEIVED**.

**Recorded as INFO because the delivery worked, and this track has spent four fires on deliveries that
did not.** C318 routed by **lineage name** in prose (*"routed to the t3-v3 lineage"*), twice, in a
findings row and again in the disposition list; it reached the first pass this lineage ran. Compare
`C348-N2`, where `C330:262` routed **by slot number** and arrived only because the receiving pass
happened to grep for the number; and `C348-N1`, where a carry took 32 days and came back as
rediscovery. **The variable is not effort — C152 named its owner twice and still failed. It is whether
the routing token is one the receiver's own subject-matter sweep will hit.** A lineage name is; a slot
number is not (§B measured that channel at **0** this pass).

And the subject matter is its own small lesson: C318's correction exists because **five files share the
basename `validate_vectors.py`**, and a past pass resolved it to the wrong one. That is the same class
as `C348 rev1`'s v39, found independently, in a different lineage, four days earlier.

### N4 (INFO, discharge) — `C310-N3` was consumed *by the standard*, in executable code that cites it by id and path, and nothing told this ledger

The window's one relevant commit is `8d3808db`, *"test(standard): gate that every `@context` URI in
test-vectors has a backing file (#637)"*. It adds
`web4-standard/test-vectors/validate_context_refs.py`, whose entire `KNOWN_MISSING` table is:

```python
KNOWN_MISSING = {
    "t3v3.jsonld": (
        "C310-N3 (docs/audits/C310-t3-v3-tensors-8th-delta-2026-08-02.md)",
        "routed to the SDK / build track: add the context file, or repoint "
        "the vectors at t3.jsonld / v3.jsonld — …",
    ),
}
```

**Executed** (v27): `python3 web4-standard/test-vectors/validate_context_refs.py` → 283 references, 9
distinct names, 8 `OK`, 1 `KNOWN` (`t3v3.jsonld`, 36 refs, 1 file), **exit 0**.

This is the exact complement of `C348-N2`, and it is the good case. There, consumption reached the
standard as a **commit** and left no citation, so an orphaned-by-id sweep was structurally blind to it.
Here consumption reached the standard as a commit **and carried the citation with it** — id *and*
repo-relative path — into a file that runs. The docstring even states the discipline (*"KNOWN_MISSING
is the carrying mechanism, not a pass: a name lands there only with a citation to the audit that found
it and the track the fix is routed to … the list can only shrink honestly"*). **This is what a working
carry channel looks like, and the standard built it without being asked.**

**What is nonetheless owed, and why this is a row rather than applause.** Nothing wrote the reception
back. This ledger's C310-N3 row still reads *routed, open*; the finding's live status now lives in a
Python dict, and **three sibling lineages have already begun reporting it from there rather than from
here** — `C322:42`, `C338:81`, `C344:360` each cite `t3v3.jsonld` / `C310-N3` from the gate's stdout.
That is `v38`'s shape with the roles swapped: an adjudication of this lineage's carry does not arrive,
and a ledger-side probe cannot see one that happened in a **tool**. **Status re-typed here: `C310-N3`
is OPEN-AND-GATED** — unfixed (36 references still dangle), but now *watched*, with a named owner and a
check that will go red the day the file appears without the entry being removed.

**And the two rows meet.** N1's disposition depends on this one: the gate's routed remedy offers
*"repoint the vectors at `t3.jsonld` / `v3.jsonld`"*, and N1 shows that branch silently drops
`observed_at` and `witnessed_by` from the 2 published cases that carry them. **The best-instrumented
carry in this lineage points at a fix that is unsafe as written.** Route: this ledger (discharged) +
SDK/build track, jointly with N1.

---

## §D — C310's carries, **disposition-checked** at HEAD `03b61ac2`

**Method declared: disposition, not re-derivation.** Each row asks *has this row's status moved* —
owner ledger, routed track, or the artifact's own presence — not *is the underlying evidence still
true*. Sound here only because §A shows the target byte-frozen; had it moved, every row anchored to
target text would be marked **provisional**. **8 rows; 6 HELD, 1 RE-TYPED (N4), 1 CORRECTED-AND-CLOSED
(N3). 0 lost.**

| Carry | disposition probe at HEAD | status |
|---|---|---|
| **C310-N1** (`:429-435` V3 entity-role note, operator **fork** A/B) | C310's own first question for this slot. `sed -n '429,435p' web4-standard/core-spec/t3-v3-tensors.md` → note verbatim; `grep -rn "v3-valid-003" web4-standard/` → `test-vectors/schema-validation/t3v3-jsonld-validation.json:167`, **still present**. Per C310 method note 5, the vector's survival *is* the answer: **option B was not executed** | **STILL-OPEN, 3rd pass.** Operator picked neither A nor B ⇒ per C310's own instruction its severity is now argued both ways. **Idle — no self-decision** |
| **C310-N2** (`web4:observationCount` in `.ttl`, schema forbids) | `grep -n observationCount` → `ontology/t3v3-ontology.ttl:107`, **0** hits in `schemas/t3v3-jsonld.schema.json` | **STILL-OPEN**, and **subsumed as one member of N1's five-row class.** Adjudicate jointly |
| **C310-N3** (36 refs to a context that does not exist) | `validate_context_refs.py` `KNOWN_MISSING` cites it by id+path; gate executed, exit 0, `KNOWN (36 refs, 1 files)` | **RE-TYPED → OPEN-AND-GATED.** See **N4**. Unfixed but watched; owner named |
| **C310-N4** (header `:4` names the retired `ontology/t3v3.jsonld`) | target frozen ⇒ `sed -n '4p'` → **JSON-LD Context**: `web4-standard/ontology/t3v3.jsonld`, verbatim | **STILL-OPEN, UNCHANGED.** And N1 refutation 3 gives it a second reading: the retired file is now *load-bearing evidence* (it proves the casing split predates the reconciliation) |
| **C270-N1** (successor merge gate anchored to the crate, not the spec) | no window commit touches `web4-trust-core/` | **STILL-OPEN**, disposition-checked |
| **C270-N2** (*"cross-language test vectors enforce them"* unbacked, Rust side) | `grep -rn tensor-operations --include=*.rs . \| grep -v target` → **0**; `t3v3-012` prose comments: `web4-trust-core/src/tensor/mod.rs` 1, `web4-core/src/t3.rs` 2 | **STILL-OPEN**, and its **supporting cell corrected** by `C318-I-1` → **N3**. Conclusion untouched |
| **C270-N3** (pre-C-series `cross-language-t3v3-alignment` never entered the ledger) | the **inclusive** membership rule in this header admits it, with `2026-04-27-canonical-t3v3` and `t3-v3-tensors-internal-consistency` | **STILL-OPEN as a status row**, but note the mechanism: it is *unclosable* under C310's exclusive enumeration and merely *open* under the inclusive one |
| **C192-N3** (layer-split composite aggregation is INFO) | C270 DO-NOT list | **STANDS. Not re-raised** |

**C310's §C do-not-raise list honoured verbatim**: composite-weights #2/#3 (INFO by C192-N3
precedent), decay-model #5 Training/Temperament half, C238-N1/D2 NUMERIC facet, the
vectors-as-authority form already narrowed by C270-N2, the C230 "+2 shift", the `ns/`-vs-`ontology#`
split, C278-N2. **None re-opened.**

---

## §E — Instrument index

**Built by capture** (C346 rev1 guard 6), and **built with v39's four pre-publication checks applied to
this section specifically**, because v39 was written four hours before this pass out of a block against
exactly this table in `C348`: (a) every basename `ls-tree`-checked and rooted; (b) no `git log` green
published without confirming the pathspec matches a tracked file; (c) one membership rule for this
lineage and the lineage charged; (d) every count word checked against the set it names.

**Roots**: all paths repo-relative from the repository root. **Basenames that resolve to more than one
tracked file are marked ⚠ and are always written rooted**: `t3-v3-tensors.md` (**2** — `core-spec/` and
`forum/nova/web4-sal-bundle/`, differing blobs) and `validate_vectors.py` (**5** — and that collision
*is* finding N3).

| claim | instrument (paths repo-relative) | scope | result |
|---|---|---|---|
| target frozen | `git rev-parse --short 03b61ac2:web4-standard/core-spec/t3-v3-tensors.md` ⚠ | 1 file | `32d3368e` = C310's blob |
| target motion | `git log --oneline 60926fa7..03b61ac2 -- web4-standard/core-spec/t3-v3-tensors.md` ⚠ — **pathspec confirmed to match a tracked file before the 0 was published** (v39b) | 1 file | **0** commits |
| target basename collision | `git ls-tree -r --name-only 03b61ac2 \| grep -c "/t3-v3-tensors.md$"` | repo | **2** |
| window | `git rev-list --count 60926fa7..03b61ac2` | repo | **56** commits |
| mirror-layer motion | `git log --oneline 60926fa7..03b61ac2 -- web4-standard/schemas/ web4-standard/ontology/ web4-standard/test-vectors/ web4-standard/implementation/sdk/` | 4 trees | **1** commit (`8d3808db`) |
| inbound corpus | `git grep -l "t3-v3-tensors" 03b61ac2 -- docs/audits web4-standard/docs/audits` | both audit trees | **69** |
| lineage (inclusive rule) | `git ls-tree -r --name-only 03b61ac2 -- docs/audits web4-standard/docs/audits \| grep -icE 't3-v3\|t3v3'` — pinned to `03b61ac2`, which **predates this document**, so the working tree cannot enter its own scope (v33, 4th-fire hazard on this track) | both trees @ `03b61ac2` | **12** ⇒ **58** non-lineage |
| slot-number routing channel | `git grep -n "C350" 03b61ac2 -- docs/audits web4-standard/docs/audits` | both audit trees | **2** hits, **both inside C310** ⇒ **0** sibling routings |
| subject-matter widening | `git grep -l "t3v3\|T3/V3\|t3-v3" 03b61ac2 -- docs/audits web4-standard/docs/audits`, minus lineage, restricted to filenames dated ≥ 2026-08-02 | both audit trees | **11** docs (filename-token sweep alone returned **3**) |
| N1 ontology properties | `grep -n "a rdf:Property" web4-standard/ontology/t3v3-ontology.ttl` + `rdfs:domain web4:DimensionScore` | 1 file | **5** properties with `rdfs:domain web4:DimensionScore` — `:87`, `:92`, `:97`, `:102`, `:107`. (`web4:hasDimensionScore` `:80` is **excluded**: its domain is `web4:Tensor`, not `DimensionScore` — it is the linking property, and a first pass of this cell wrongly counted it as a sixth. §F.5) |
| N1 schema keys | `$defs.DimensionScore.properties` (`:11-37`) of `web4-standard/schemas/t3v3-jsonld.schema.json`; `additionalProperties` (`:36`) | 1 file | `dimension`, `score`, `observed_at`, `witnessed_by`; **`false`** |
| N1 context terms | `@context` of `web4-standard/schemas/contexts/t3.jsonld` and `…/v3.jsonld` | 2 files | `observedAt`, `witnessedBy` present; `observed_at`, `witnessed_by` **absent** in both |
| N1 `@vocab` refutation | `@`-level keys of both context files | 2 files | `{"@version": 1.1}` only — **no `@vocab`** |
| **N1 round trip (MACHINE)** | `jsonschema` 4.26.0 over `web4-standard/test-vectors/schema-validation/t3v3-jsonld-validation.json` `valid[4].document`, as published vs. the two keys re-spelled | 1 vector, 2 runs | published → **VALID**; context spelling → **INVALID** (`additionalProperties`) |
| N1 expansion half | **hand-derived** from the two context files' `@`-level keys — `rdflib` and `pyld` both `ModuleNotFoundError` on this host (C310 method note 3) | — | **labelled non-machine-checked** |
| N1 direction (retired context) | `@context` keys of `web4-standard/ontology/t3v3.jsonld` | 1 file | `observedAt`/`witnessedBy` present, snake_case **absent** ⇒ split **predates** the 2026-03-24 reconciliation |
| N1 green gate | `cd web4-standard/implementation/sdk && python3 -m pytest tests/test_t3v3_jsonld.py -q`; and the keys `T3.to_jsonld()` emits (`web4-standard/implementation/sdk/web4/trust.py:230-234`) | 1 suite | **77 passed**; emitter yields **2** of the 5 properties |
| N2 | `web4-standard/docs/audits`-rooted read of `docs/audits/C314-acp-framework-8th-delta-2026-08-05.md:201`, `:258` | 1 file | *"2 undefined, 88.9% … `observed_at` and `witnessed_by`, undefined in both"* |
| N3 basename collision | `git ls-tree -r --name-only 03b61ac2 \| grep "/validate_vectors.py$"` ⚠ | repo | **5** files |
| N3 harness claim | `grep -n "def validate_t3v3" web4-standard/test-vectors/validate_vectors.py`; then execute it | 1 file | `:106`; **87 passed, 0 failed** |
| N3 C270 conclusion survives | `grep -rn tensor-operations --include=*.rs . \| grep -v target` | Rust trees | **0** |
| N4 | `python3 web4-standard/test-vectors/validate_context_refs.py`; `KNOWN_MISSING` at `:49-56` | 1 gate | 283 refs, 9 names, 8 `OK`, 1 `KNOWN`, **exit 0** |
| C310-N1 disposition | `grep -rn "v3-valid-003" web4-standard/` | tree | `test-vectors/schema-validation/t3v3-jsonld-validation.json:167` — **present** ⇒ option B not executed |
| C310-N2 disposition | `grep -n observationCount` on `web4-standard/ontology/t3v3-ontology.ttl` and `web4-standard/schemas/t3v3-jsonld.schema.json` | 2 files | `:107`; **0** |
| C310-N4 disposition | `sed -n '4p' web4-standard/core-spec/t3-v3-tensors.md` ⚠ | 1 file | names `web4-standard/ontology/t3v3.jsonld`, verbatim |

**Not mechanically reproducible: one row, and it is labelled in place** — N1's *expansion* half
(`rdflib`/`pyld` absent on this host). It is stated as hand-derived from two `@`-level key sets, the
inputs to that derivation are themselves machine-read and published above, and **the finding does not
rest on it**: the schema half alone (`additionalProperties: false` vs. terms absent from every context)
establishes that no document satisfies both artifacts. Every other row is a command, a rooted scope,
and its output.

---

## §F — Own errors

1. **The lineage count depends on the rule, and the rule is load-bearing for a carry.** Written first
   as **8** from C310's header, corrected to **12** by running the inclusive rule this track adopted at
   `C346 rev1` and re-affirmed four hours ago in `C348 rev1` §F.5. The correction is not cosmetic:
   `C270-N3` is *"the pre-C-series alignment audit never entered the ledger"*, and under the exclusive
   rule that carry can never be closed by a count, because the rule that would close it is the rule
   that excludes its subject. **Stated in the header rather than smoothed** — this pass is the 9th
   delta and the 13th document, and both are true of different questions.
2. **N1 was nearly filed as "C310-N2, wider."** The first read had `observedAt`/`witnessedBy` as a
   second instance of the schema/ontology desync C310 already charged. They are the opposite
   mechanism — C310's property is **absent** from the schema, these two are **present under a key no
   context maps** — and collapsing them would have hidden the actual result, which is neither
   defect but the **class** they belong to. Refutation 3 in §C is the place that got caught, and it is
   why the finding is the five-row table rather than a fourth desync.
3. **The direction claim was assumed before it was tested, and the assumption was wrong.** The natural
   story — *the 2026-03-24 reconciliation split the context and changed the casing* — was written into
   a draft of N1 before `web4-standard/ontology/t3v3.jsonld` was opened. The retired context uses
   camelCase too, which **exonerates the reconciliation** and makes the split original. Caught by one
   `json.load`, before filing. **v15(a)'s shape** (*date a remediation against the artifacts it
   describes*) generalises: **date a defect against the change you are about to blame for it.**
4. **The subject-matter widening was almost skipped, and it was the entire yield.** The filename-token
   sweep (`t3-v3-tensors`) returned **3** non-lineage documents postdating C310 and **zero** verb-set
   hits — a clean, defensible, empty result. Re-running on `t3v3|T3/V3|t3-v3` returned **11**, and N1,
   N2 and N4 all live in the 8 that only the second sweep found. **`C314` and `#637` never write the
   target's filename at all**; they write the *artifact* names. The standing carry says *search by
   label and by subject matter*; this pass came within one command of publishing the label sweep's
   emptiness as the answer.
5. **Four line-cite / range errors in §E, caught by re-running §E's own instruments against the
   tree before publishing — which is v39's check (a), applied to this document rather than to the one
   that earned the carry.** `web4:dimension` was cited at `:88` (its `rdfs:domain` line) instead of
   `:87` (its declaration); `$defs.DimensionScore` at `:20-35` instead of `:11-37`; the `.ttl` block at
   `:88-110` instead of `:87-110`; `KNOWN_MISSING` at `:49-57` instead of `:49-56`. **And one that was
   a miscount, not a mis-cite**: the first derivation of the property table returned **6** rows,
   because the regex that selected `rdfs:domain web4:DimensionScore` also caught
   `web4:hasDimensionScore` `:80` — whose domain is `web4:Tensor`. It is the *linking* property, not a
   property *of* `DimensionScore`, and including it would have put a ✅ row in a table whose whole
   claim is about which rows are ❌. Corrected to 5 before filing, with the exclusion stated in §E
   rather than silently dropped. (§E's property-count cell names the exclusion; §F.6 below is the balance note.) Line cites are the class two consecutive review blocks on this track
   have been about; the only reason these four did not ship is that §E was re-executed rather than
   re-read.
6. **A pass whose own §A is two commands must not let §E inherit that thinness.** §E here is longer
   than §A and §D combined. That is deliberate and it is the direct application of **v39**: the section
   that certifies the others is the one that must not be written last and fast. Whether the balance is
   right is for the reviewer, but it was chosen, not defaulted into.

---

## §G — Disposition

**Findings: N1 MEDIUM · N2 LOW · N3 INFO · N4 INFO. 2 net-new, 1 reception closed, 1 carry re-typed.
ZERO mutation.**

- **C351 = declared NO-OP.** N1 routes to the schema + ontology owner and the operator as a **fork**
  (three named shapes, none chosen here) — **do not self-apply**, and do not edit
  `web4-standard/schemas/t3v3-jsonld.schema.json`, either context, the `.ttl`, the published vectors,
  or the SDK. N2 is the C314 lineage's instrument. N3 is closed. N4's fix belongs to the SDK/build
  track.
- **Adjudicate N1, C310-N2 and C310-N3 JOINTLY.** They are three rows of one five-row table, and
  N4 shows the C310-N3 remedy currently on file makes N1 live rather than latent. Fixing either in
  isolation can make the other worse.
- **Delivered outward this fire, not merely routed** (v36, and N3 is this pass's own evidence about
  which routing tokens work): **N2 is addressed to the C314 / acp-framework lineage by NAME**, whose
  next slot is **acp ≈ C354**, and it is stated in this document's §B residue table and §C under
  C314's own citation `C314:201` so that a sweep from either side joins them. **It is deliberately
  *not* routed by slot number** — §B measured that channel at **0 receptions** this pass, and
  `C348-N2` is the record of a by-number routing that arrived only by luck. **Re-check at C354.**
- **Rotation** advances +2 → `reputation-computation.md` = **C352**. Next t3-v3 delta ≈ **C390**.

**Baseline for C390** — all paths repo-relative; **basename uniqueness checked for each**
(`git ls-tree -r --name-only 03b61ac2 | grep -c "/<basename>$"`), ⚠ = collides, always write rooted:

| artifact | blob at `03b61ac2` | basename hits |
|---|--:|--:|
| `web4-standard/core-spec/t3-v3-tensors.md` | `32d3368e` | **2** ⚠ |
| `web4-standard/ontology/t3v3-ontology.ttl` | — (`rdfs:domain web4:DimensionScore` block `:87-110`) | 1 |
| `web4-standard/ontology/t3v3.jsonld` (retired; N1 evidence) | — | 1 |
| `web4-standard/schemas/t3v3-jsonld.schema.json` | — (`$defs.DimensionScore` `:11-37`, `additionalProperties: false` `:36`) | 1 |
| `web4-standard/schemas/contexts/t3.jsonld` · `…/v3.jsonld` | — | 1 · 1 |
| `web4-standard/test-vectors/schema-validation/t3v3-jsonld-validation.json` | — (`v3-valid-003` `:167`) | 1 |
| `web4-standard/test-vectors/validate_context_refs.py` | — (`KNOWN_MISSING` `:49-56`) | 1 |
| `web4-standard/test-vectors/validate_vectors.py` | — (`validate_t3v3` `:106`) | **5** ⚠ |
| `web4-standard/implementation/sdk/web4/trust.py` | — (`to_jsonld` `:209-240`) | 1 |
| `web4-standard/implementation/sdk/tests/test_t3v3_jsonld.py` | — (guard `:484`) | 1 |

**Guards for C390.**
1. **Re-run the five-row `DimensionScore` table first.** If any of the three ❌ rows became ✅, find the
   commit and check the *other two* moved with it — a partial fix to one row of this class is the
   likeliest next defect, and `additionalProperties: false` means a half-applied fix breaks published
   vectors rather than degrading quietly.
2. **Check whether `validate_context_refs.py`'s `KNOWN_MISSING` still holds `t3v3.jsonld`.** If the
   entry is **gone**, verify the backing file actually exists *and* that the two evidence properties
   survived the repoint — a green gate here is exactly what N1 predicts will accompany the data loss.
   If the entry **grew**, this lineage now co-owns whatever landed beside it.
3. **Run the inbound set difference BEFORE §A, on SUBJECT MATTER as well as the filename token.** It
   was the entire yield of this pass and of C344, C346, C348. The filename sweep alone returned an
   empty verb set here; the artifact-name sweep returned three findings (§F.4). Pre-register the verb
   set. Measure the **slot-number channel too, and record the negative** — it is what makes the
   positive interpretable.
4. **Build §E by capture, with v39's four checks, and do not write it last-and-fast.** `ls-tree` every
   basename (`t3-v3-tensors.md` and `validate_vectors.py` both collide); never publish a `git log`
   green without confirming the pathspec matches a tracked file; one membership rule for both
   lineages; every count word against the set it names.
5. **Did the operator answer C310-N1's A/B fork?** Fourth pass. Per C310 method note 5, check
   `v3-valid-003` in the vector file, **not** the note in the spec.
6. Do **not** re-open: C310's §C do-not-raise list (verbatim, re-honoured here); `C318-I-1` (**closed**
   — received and adjudicated at N3); C270-N2's Rust-side conclusion (untouched by that correction);
   C192-N3.

---

## Pattern (C350)

**C348 found a carry that succeeded and could not tell anyone. This pass found the same channel working
— and then found a defect that four instruments had already touched without anyone asking the question
that convicts it.**

`C314` measured the two properties and named them, in the right artifacts, correctly — and recorded
them as the residue of an **88.9% coverage score**. The SDK's context test asserts that every
`DimensionScore` key is mapped in the context and passes — over the **two** keys the emitter happens to
produce. The `#637` gate watches every `@context` URI for a backing file and exits **0** — the context
in question is *missing*, so the terms inside it were never in scope. C310 charged the third property
of the same block as a lone schema/ontology desync. **Four instruments, four greens or partials, one
defect, and not one of them was wrong.** Each asked a question whose domain excluded the answer:
coverage asks *how many terms are defined*, the SDK test asks *are the emitted keys mapped*, the gate
asks *does the file exist*, and C310 asked *what changed in the window*. **Nobody asked whether a
document could carry the evidence and survive the round trip.**

**v40 (new): a metric's denominator is a domain, and a defect that lives outside the domain reads as
quality.** C314's `2 undefined / 88.9%` and the SDK guard's `77 passed` are the same object in
different dress — both are true statements about the *instrument's* reach that a reader converts into a
statement about the *corpus*. The corrective is not better instruments; it is a question the
instruments do not ask, put directly to the artifacts: **take the standard's own published document,
run it through the standard's own schema and the standard's own context, and see what comes out the
other side.** That took two `jsonschema` calls and it is the whole of N1.

And the thing that comes out the other side is the point. The ontology says, in its own comment, *"a
relying party weighs a score by its evidence, not just its value."* The serialization keeps the value
and drops the evidence — the *when*, the *who*, and the *how many*. **The standard's trust primitive
can currently be transmitted only as a number, which is the one form §1.2 exists to forbid.**

→ [[feedback_last_table_to_convert]] / [[feedback_green_gate_is_the_defect]] /
[[feedback_subsumption_is_a_disposition]] / [[feedback_delivery_is_an_act_of_the_receiver]] /
[[feedback_class_not_cell]] / [[feedback_publish_the_instrument]]

---

*C350 verdict: `t3-v3-tensors.md` byte-frozen for the 9th consecutive pass — **zero autonomous
mutation**. One MEDIUM net-new in the artifacts the spec normatively cites, found by asking the
standard's own schema and context about the standard's own vector; one instrument-routing finding
against a sibling lineage; one inbound correction received and closed at the first opportunity; one
carry re-typed after being consumed by the standard itself.*
