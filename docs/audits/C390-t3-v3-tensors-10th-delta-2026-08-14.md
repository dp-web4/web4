# C390 — `core-spec/t3-v3-tensors.md`, 10th delta (this lineage printed the defect in its own baseline evidence, charged the row beside it, and built a gate whose domain cannot reach the one it left)

**Slot**: C390 (rotation: C350 + 40) · **Target**: `web4-standard/core-spec/t3-v3-tensors.md`
**HEAD**: `a68adb93` · **Prior pass HEAD**: `03b61ac2` (C350, 9th delta, 2026-08-10)
**Window**: 32 commits · **Target motion**: 0 · **Mirror-layer motion**: 0

**Lineage membership rule (inclusive, per `C346 rev1`, re-affirmed `C348 rev1` §F.5 and `C350` §F.1):**
a document is in this lineage if its path under `docs/audits` or `web4-standard/docs/audits` matches
`t3-v3|t3v3`, case-insensitive. **13 at HEAD** (C350 published 12 at `03b61ac2`; this document's own
predecessor entered the tree since). This pass is the **10th delta** and the **14th document** — both
are true, of different questions. The rule admits the non-C-numbered members
`t3-v3-tensors-internal-consistency-2026-05-24.md`, `cross-language-t3v3-alignment-2026-05-13.md` and
`2026-04-27-canonical-t3v3.md` (the standing enumeration rule: every lineage has a non-C-numbered
`…-internal-consistency-…` member; this one has it).

**Ordinal chain**: C42(1) C82(2) C121(3) C154(4) C192(5) C230(6) C270(7) C310(8) C350(9) **C390(10)**.
*(`C192`'s filename says "4th delta" and `C154`'s says the same; the chain above is the authority.)*

---

## Scope — declared, and approved after one revision

Proposed as the five guards `C350` §G left for this slot. The policy reviewer returned **REVISE** with
three narrowing changes, all applied before any measurement was charged:

1. **Item 4 was reworded from an adjudication to a reception check.** As proposed it read *"answer the
   C310-N1 A/B fork"* while the same proposal's out-of-bounds clause read *"do not answer C310-N1's
   fork."* `C310:20` classifies N1 as *operator + spec author (**fork**, do not self-apply)*. The
   corrected item asks only **whether the operator has answered**, read off `v3-valid-003` rather than
   the spec note, and the correct output of a *no* is a **routing-failure report, not a decision**.
2. **`C366:426` is decomposed before adjudication.** The row reads *"`ontology#` + camelCase vs `ns/` +
   snake_case"*. The **namespace** half is ratified design
   (`docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md`) and sits on C310's do-not-raise
   list; only the **case-convention** half is live. Adjudicating the row wholesale would re-open a
   ratified decision under cover of an inbound routing. See **N4**.
3. **The null was pre-registered as publishable for guards 1, 2 and 5**, before they were run, so that
   an unchanged result could not be retro-fitted into manufactured yield. This is discharged
   structurally: the session log published §A's freeze and the 0-commit mirror result *before* the
   reviewer was spawned.

On the question put to the reviewer directly — **`C372:383` d4 is the `C120→C121` hazard's prescribed
remedy, not a violation of it.** The hazard forbids *batching* a corpus-wide sweep; `C372:383`
decomposes d4 into seven per-lineage members, *"each to its own lineage slot, one per pass"*, and taking
the `t3v3` member in the `t3v3` slot **is** the anti-batch form. Boundary condition accepted and
honoured: confined to C350 §E's baseline artifact set; the other six members are **not** charged here.

---

## Verdict

Target byte-frozen for the **10th** consecutive pass, and the mirror layer moved **zero** commits in a
32-commit window. The corpus delta is empty in both trees. Nothing in this pass came from a diff.

| # | Severity | Class | Owner |
|---|---|---|---|
| **N1** | **MEDIUM** | **net-new as a disposition failure, NOT as a fact** — `trust-query.jsonld` was printed by **this lineage's own C310 baseline**, named there as one of *two* misses *in this lineage*, charged as neither a finding nor a carry; the gate built two days later in response to its sibling has a domain that structurally cannot reach it | SDK/build track + this ledger (**do not self-apply**) |
| **N2** | **LOW** | **`C372` d4 discharged for the `t3v3` member**, executed. Class re-derived: **4 of 9** JSON-LD pairs, **40** unmappable properties; `t3v3` is the **smallest** member at **2**. **NOT net-new** — `C314:188-203` published this class 9 days ago | recorded; one instrument divergence routed to the acp lineage |
| **N3** | **INFO** | **the pre-registered null**, published as the answer — the `DimensionScore` class is immobile across 10 passes; `C310-N1`'s fork is **unanswered at the 5th pass** ⇒ routing-failure report | operator (fork), this ledger |
| **N4** | **INFO** | `C366:426` **received and decomposed** — namespace half fenced as ratified, case half subsumed into N2's table. `r7-action`'s own d4 member **not** charged (another lineage's slot) | recorded; r7 lineage |

**ZERO mutation.** No file under `web4-standard/` was edited by this pass.

---

## §A — Freeze

```
git rev-parse --short a68adb93:web4-standard/core-spec/t3-v3-tensors.md         →  32d3368e
git log --oneline 03b61ac2..a68adb93 -- web4-standard/core-spec/t3-v3-tensors.md →  0 commits
git rev-list --count 03b61ac2..a68adb93                                          →  32
git log --oneline 03b61ac2..a68adb93 -- web4-standard/schemas/ web4-standard/ontology/ \
    web4-standard/test-vectors/ web4-standard/implementation/sdk/                →  0 commits
```

`32d3368e` is byte-identical to C350's and C310's blob. Last content commit `d89595e8` (#531,
2026-07-16) — **29 days**. **The mirror layer returned 0, where C350 returned 1.** Both halves of the
corpus delta are therefore empty, which is why §B is the whole of this pass's yield — the fifth
consecutive fire on this track for which that is true (C344, C346, C348, C350, C390).

**v39 fires on this file's own name**: `git ls-tree -r --name-only a68adb93 | grep -c
"/t3-v3-tensors.md$"` → **2**. Every path in this document is repo-relative for that reason.

---

## §B — The inbound set difference, run FIRST

**Verb set PRE-REGISTERED before the run** (v26):
`owner|route|routed|carry|carried|owed|addressee|cross-track|next pass|lineage|slot|hand-off|discharge`.

**Slot-number channel, and the negative is recorded** (v55 — a positive on one channel is only
interpretable against the other's negative):

```
git grep -n "C390" a68adb93 -- docs/audits web4-standard/docs/audits
  →  3 hits, ALL THREE inside C350 itself (:513, :515, :531)  ⇒  0 sibling routings by number
```

**Subject-matter channel, by the domain's words not the filename** (v40/v48 — `C314` and `#637` never
write the target's filename at all, which is C350 §F.4's carry):

```
git grep -l -E "t3v3|T3/V3|t3-v3|DimensionScore|t3v3-ontology" a68adb93 \
    -- docs/audits web4-standard/docs/audits
  minus the 13 lineage documents, restricted to filenames dated ≥ 2026-08-10   →  9 documents
```

**Residue — rows this ledger does not hold:**

| row | source | date | → |
|---|---|---|---|
| `trust-query.jsonld` unbacked (2 sites) → **"t3-v3 / trust lineage … Ride the next trust slot."** | `C366:424`, `C366:219` | 2026-08-12 | **N1** |
| `ontology/r7-action.jsonld` vs `schemas/contexts/r7-action.jsonld` disagree → **"t3-v3 / build track"**, recorded not charged | `C366:426` | 2026-08-12 | **N4** |
| d4 corpus-wide schema/vector sweep, remaining list names **`t3v3`**, *"each to its own lineage slot, one per pass"* | `C372:383` | 2026-08-12 | **N2** |
| the `atp` member of the same d4 list, discharged | `C386:511` | 2026-08-14 | context for N2 |

**This slot is the addressee named in `C366:424` by role rather than by number.** The by-number
channel measured **0** again, for the second consecutive pass on this file — the by-name channel
carried everything.

---

## §C — Findings

### N1 (MEDIUM) — the SDK emits a context URI that has no backing file, and the miss was printed in this lineage's own baseline eight days before the gate that cannot see it was written

**The fact, executed.** The SDK declares eleven `https://web4.io/contexts/*.jsonld` constants. Ten
resolve to a file under `web4-standard/schemas/contexts/`; one does not.

```
for n in lct atp capability attestation-envelope dictionary t3 v3 trust-query entity acp r7-action; do
  test -f web4-standard/schemas/contexts/$n.jsonld && echo "BACKED $n" || echo "MISSING $n"; done
  →  BACKED ×10,  MISSING trust-query.jsonld
```

**It is a live emission path, not a dead constant.**
`web4-standard/implementation/sdk/web4/trust.py:713` — `doc["@context"] = [TRUST_QUERY_JSONLD_CONTEXT]`
inside `TrustQuery.to_jsonld()`, with the constant at `:108` and re-exported at
`web4-standard/implementation/sdk/web4/__init__.py:76`, `:554`. Any caller of `TrustQuery.to_jsonld()`
receives a document whose sole `@context` entry does not resolve.

**Why no instrument in the repository can see it — and this is the finding.**

| instrument | what it asks | why it misses |
|---|---|---|
| `web4-standard/test-vectors/validate_context_refs.py` | does every `@context` URI **under `test-vectors/`** have a backing file? | its reference domain is `VECTORS_DIR.rglob("*.json")` (`:83`). The two trust-query vectors carry **no `@context` at all** (top-level keys: `description, input, expected_output, should_succeed, notes`) — they are SDK fixtures, not JSON-LD documents. The emission happens at SDK **runtime**, in a tree the gate does not scan. Executed: the gate reports **9** distinct names and `ALL REFERENCED CONTEXTS BACKED (except 1 carried: t3v3.jsonld)`, **exit 0**. `trust-query.jsonld` is not among the 9 |
| `web4-standard/implementation/sdk/tests/test_trust.py:941` | `assert "https://web4.io/contexts/trust-query.jsonld" in doc["@context"]` | asserts the **string is present**, never that it resolves. A green test about a literal, not about a system (v45). Executed: `175 passed` |
| the JSON-LD schemas | — | type `@context` as an array of URI strings and never dereference it (the gate's own docstring `:10-12` records this) |

**The disposition failure, which is what makes this net-new.** `C310:315` — this lineage's own 8th
delta — printed, inside the baseline it built to prove that `t3v3.jsonld` was *not* an idiom:

> ```
> trust-query.jsonld            → ** MISSING **   (emitted by trust.py:108)
> t3v3.jsonld                   → ** MISSING **   (cited by 36/38 vectors)
> ```
> **Nine of eleven hold the convention; both misses are in the T3/V3 lineage.** Not an idiom.

C310 **named both misses as this lineage's own**, charged `t3v3.jsonld` as N3 — and entered
`trust-query.jsonld` in neither the findings table nor the carry table. `C350` §D then
disposition-checked C310's **eight carries** and could not see it, because it was never a carry: it
was *evidence for* a carry. Two passes and 12 days later a **different** lineage (`C366:219`) re-found
it from its own denominator work and routed it back here by role.

**And the gate inherited the same blind spot.** `web4-standard/test-vectors/validate_context_refs.py`
was created by `8d3808db` (#637) on **2026-08-04**, two days after C310, and its docstring cites
`audit C310-N3` by name. It was built to watch this exact class — and it was scoped to the **charged**
instance's tree (`test-vectors/`) rather than to the **measured** class (every `web4.io/contexts/*`
reference in the repo). `C366-N1` had already reached the same conclusion from the SAL side and asked
for exactly this widening as its item (3): *"widen the gate's domain from `test-vectors/` to the class
— every `web4.io/contexts/*.jsonld` reference under `git ls-files web4-standard/`."* **This pass
supplies the instance that proves the ask, and it is in this lineage's own module.**

**DIRECTION TESTED, and it separates this from C310-N3.**

```
git log -S 'TRUST_QUERY_JSONLD_CONTEXT = "https://web4.io/contexts/trust-query.jsonld"' \
    -- web4-standard/implementation/sdk/web4/trust.py
  →  2d7d3e3d  2026-04-05  Sprint 19 T1: TrustQuery data classes + JSON-LD dispatcher (#130)
git log --diff-filter=A -- web4-standard/schemas/contexts/t3.jsonld   →  936c2d92  2026-03-24
git log --diff-filter=A -- web4-standard/schemas/contexts/acp.jsonld  →  6300d34a  2026-03-21
```

`t3v3.jsonld` was **retired by** the 2026-03-24 reconciliation. `trust-query.jsonld` was **never
created** — the constant was added **12 days after** the `schemas/contexts/` convention already
existed and had been populated. The story that covers C310-N3 (*"the reconciliation replaced the shared
context"*, quoted verbatim in `KNOWN_MISSING` at `validate_context_refs.py:52-54`) **does not apply
here**, so a fix that repoints the t3v3 vectors leaves this one untouched. Distinct mechanism, and the
`KNOWN_MISSING` disposition text would be false if copied across.

**Severity MEDIUM, and bounded honestly.** Re-run of C314's consumption matcher at HEAD:

```
grep -rnE "pyld|jsonld\.expand|from rdflib|import rdflib" --include=*.py .   (excl. target/, .git/)
  →  web4-standard/mrh_rdf_implementation.py:13-15,314 ; web4-standard/mrh_sparql_queries.py:12-13
grep -rnE "json-ld|jsonld" --include=*.rs --include=*.ts --include=*.js .    →  0
```

**Nothing in the repository dereferences a context**, so this is **latent, not a live failure** — the
same posture C314-N1 established and this pass re-verifies rather than inherits. It is MEDIUM rather
than LOW on two counts C310-N3 does not share: it sits in the SDK's **live emission path** (a published
API method) rather than in inert vector data, and it is **unwatched** where C310-N3 is watched — the
`KNOWN_MISSING` mechanism means a reader of the gate's green output is told about one miss and not the
other.

**Refutations tested and failed.**

1. *"`trust-query` is deliberately a non-JSON-LD schema."* `C378:290` records
   `# Non-JSON-LD schemas (lct-raw, t3v3-raw, trust-query)` in the registry docstring, and
   `test_jsonld_lifecycle.py:1029` excludes `trust-query` from its JSON-LD schema list. **This
   refutes a schema-side charge and is why none is made** — but it does not reach the finding: the
   SDK nonetheless ships `TrustQuery.to_jsonld()` at `:705-717`, whose docstring says the wrapper
   exists *"so the document can be dispatched by the generic `from_jsonld()` deserializer."* The
   method's own justification is that the document is JSON-LD. If the type is deliberately
   non-JSON-LD, the emission is the defect; if it is JSON-LD, the missing context is. **The
   disjunction is the finding, and either arm lands on the SDK/build track.**
2. *"The gate's `schemas/contexts/` resolution is too narrow — `ontology/t3v3.jsonld` exists on
   disk."* **Refuted.** The gate resolves at `CONTEXTS_DIR / name` (`:40`, `:107`) and its docstring
   `:5-8` states the convention explicitly, citing the SDK test that asserts it with
   `os.path.exists()`. `ontology/t3v3.jsonld` is the **retired** file. Charging this would resurrect
   the ratified namespace reconciliation. **Not charged** — recorded here so the next pass does not
   re-derive it.
3. *"A lone miss is an idiom, not a defect."* This is C310's own baseline test, and C310 already ran
   it: **9 of 11 hold the convention.** Re-executed at HEAD, **10 of 11** — `t3v3.jsonld` is not an
   SDK constant, so the SDK-side denominator is 11 constants with 1 miss. Not an idiom, by the
   lineage's own standard.

**Routed, not applied.** Three legitimate shapes with different blast radii — create
`web4-standard/schemas/contexts/trust-query.jsonld`; or drop `to_jsonld()`/`from_jsonld()` from
`TrustQuery` and ratify it as non-JSON-LD per `C378:290`; or add it to `KNOWN_MISSING` **with its own
disposition text** (not C310-N3's, which is false for it) as the honest interim disclosure. That is an
author decision. **Nothing here is self-applied.**

---

### N2 (LOW) — `C372` d4 discharged for the `t3v3` member; the class is real, was already published, and `t3v3` is its smallest instance

**Executed**, confined to C350 §E's baseline artifact set plus the nine JSON-LD schema/context pairings
needed to give the count a denominator (v46 — an absence is a finding only against a denominator).

Method: for each pairing, the set of property names declared anywhere in the schema's `properties`
blocks, minus the terms defined in **every** context of the pairing, minus JSON-LD keywords and
keyword aliases. `t3v3` is the one pairing where a single schema faces **two** contexts, so a name
counts only if unmapped under **both**.

| pairing | schema props | unmappable | names |
|---|--:|--:|---|
| `acp` | 54 | **23** | `args, audience, authorized, autoThreshold, dependsOn, expiresAt, expr, fallback, humanApproval, id, kind, maxAtp, maxExecutions, mcp, mode, nonce, output, rateLimit, requiresApproval, resourceCaps, status, timeout, witnessLevel` |
| `r7-action` | 83 | **8** | `amount, atp, atp_balance, composite_score, hard, message, release_condition, threshold` |
| `lct` | 55 | **7** | `binding_context, computation_witnesses, last_attestation, last_computed, role, sub_dimensions, witness_count` |
| **`t3v3`** | 16 | **2** | **`observed_at`, `witnessed_by`** |
| `atp` · `attestation-envelope` · `capability` · `dictionary` · `entity` | 13/32/14/34/8 | **0** | — |
| | | **40** | **4 of 9 pairings affected** |

**Two refutations tested first, both falsified**, which is what makes the column mean anything:
**no context in `web4-standard/schemas/contexts/` defines a scoped `@context` on any term** (all 10
checked, `none`), and **no context aliases `id`/`type` to `@id`/`@type`** (all 10, `none`). And the
pincer holds everywhere: `additionalProperties: false` on **11 of 11** acp property-blocks, **3 of 3**
t3v3, **13 of 13** lct, **21 of 22** r7-action. So a schema-conformant document must spell the key the
schema's way, and a conformant JSON-LD processor then drops it.

**This is NOT net-new, and the novelty check is what established that.** `C314:188-203` (acp 8th
delta, 2026-08-05) published this same table nine days ago — `acp` 22, `lct` 6, `r7-action` 2, `t3v3`
2 — and stated the corpus-shaped conclusion explicitly: *"the fix … is corpus-shaped — `lct.jsonld`
(6) and `r7-action.jsonld` (2) have the same class of gap."* **The headline this pass first drafted —
"the casing split is a class" — was killed by that check before filing.** See §F.2.

**The `t3v3` residue is exactly `observed_at` and `witnessed_by`** — C350-N1's pair, re-derived
independently here, and the d4 member is discharged on that basis. Two controls make the cell honest:
the intersection over both contexts removes `validity/valuation/veracity` and `talent/temperament/
training` (expected structure, not defect — a shared schema against split contexts), and only **2 of
38** published t3v3 vector cases carry either key, which is why 38 vectors pass and always will.

**One instrument divergence, routed and NOT charged:** this pass reads `r7-action` at **8** where
`C314:195` reads **2**, and `acp` at 23 where C314 reads 22. The gap is a counting-convention
difference — C314 scored top-level plus one nested level under a stated convention; this pass walks
`properties` blocks recursively at any depth. **Neither is wrong; they answer different questions**,
and `C314:258` guard 3 already instructs the acp lineage to re-derive this baseline at its own slot
rather than inherit it. Recorded for that slot (**acp ≈ C394**), by name, not by number.

---

### N3 (INFO) — the pre-registered null, published as the answer

All three guards returned unchanged. This was pre-registered as publishable before the runs (§Scope.3),
and it is the substantive result: **the `DimensionScore` evidence-serialization class has not moved in
10 passes.**

| guard | probe | result |
|---|---|---|
| **G1** — the five-row table | `rdfs:domain web4:DimensionScore` in `web4-standard/ontology/t3v3-ontology.ttl`; `$defs.DimensionScore` in `web4-standard/schemas/t3v3-jsonld.schema.json`; `@context` of both context files | **identical to C350.** 5 ttl properties (decl `:87 :92 :97 :102 :107`); schema keys `dimension, score, observed_at, witnessed_by`, `additionalProperties: false`; contexts define `observedAt`/`witnessedBy`, not the snake_case spellings; **no `@vocab`** in either. **3 of 5 rows still ❌.** No row became ✅, so C350 guard 1's follow-up ("check the other two moved with it") does not arm |
| **G2** — `KNOWN_MISSING` | `web4-standard/test-vectors/validate_context_refs.py:49-56`; gate executed | **unchanged** — one entry, `t3v3.jsonld`, same citation and disposition text. Neither gone nor grown. Gate: 283 refs, 9 names, 8 `OK`, 1 `KNOWN`, **exit 0** |
| **G5** — `C310-N1`'s A/B fork | `grep -rn "v3-valid-003" web4-standard/` per C310 method note 5 — read the **vector**, not the note | `test-vectors/schema-validation/t3v3-jsonld-validation.json:167`, **still present** ⇒ **option B not executed**; the note at `:429-435` is verbatim ⇒ option A not executed |

**G5 is a routing-failure report, not a decision** (the reviewer's required change 1). The operator has
now not answered this fork across **C278 → C310 → C350 → C390 — the 4th pass, 12 days since C310
raised it as the adjudication of the routed C278-N1 carry** — and C310's own
instruction was that its severity be argued both ways until answered. **This ledger does not decide
it.** What it records is that the by-number channel and the fork channel have both now measured zero
twice running on this file, while the by-role channel (`C366:424`) delivered N1 — a fourth datapoint
for the standing observation that **delivery is an act of the receiver** (v36).

---

### N4 (INFO) — `C366:426` received, and decomposed rather than adjudicated

The row routed here reads: *`ontology/r7-action.jsonld` vs `schemas/contexts/r7-action.jsonld`
**disagree** (`ontology#` + camelCase vs `ns/` + snake_case)*, owner **"t3-v3 / build track"**,
*"Surfaced by this pass's denominator work; outside SAL's subject matter. Recorded, not charged."*

**Decomposed into its two halves before any disposition** (the reviewer's required change 2):

- **Namespace half (`ns/` vs `ontology#`) — FENCED, not adjudicated.** This is ratified design per
  `docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md` and sits verbatim on C310's
  do-not-raise list (*"charging it resurrects a decision"*). Adjudicating `C366:426` wholesale would
  have re-opened a ratified decision under cover of an inbound routing. **Recorded as fenced.**
- **Case-convention half — live, and it is C350-N1's own mechanism one artifact over.** It is
  **subsumed into N2's table** rather than charged separately: `r7-action` appears there at 8
  unmappable properties. Per v37, a subsumption is a disposition — the row is answered, not dropped.

**`r7-action`'s own d4 member is NOT charged here.** `C372:383` assigns it to its own lineage slot,
one per pass, and taking it in the t3v3 slot is precisely the batching the `C120→C121` hazard forbids.
The finding is recorded for the r7 lineage by name.

---

## §D — Carry disposition at HEAD `a68adb93`

**Method: disposition, not re-derivation** — sound because §A shows the target byte-frozen and the
mirror layer at 0 commits, so no carry anchors into changed text. **C350's 4 findings + C310's 8 rows.**

| carry | probe | status |
|---|---|---|
| **C350-N1** (all 3 evidence properties of `DimensionScore` fail the round trip) | G1 re-executed above | **STILL-OPEN, unchanged.** Re-derived independently by N2's intersection |
| **C350-N2** (C314 measured it, scored it, routed nothing here) | `C314:188-203` read in full this pass | **CORRECTED-AND-CLOSED.** C314 *did* route it — to the *author/SDK track* (`C314:242`), explicitly as corpus-shaped. What it did not do is route to **this lineage**, which is the narrower true claim. See §F.3 |
| **C350-N3** (`C318-I-1` received) | closed at C350 | **CLOSED.** Not re-opened |
| **C350-N4** (`C310-N3` consumed by the standard, gate cites it by id+path) | gate executed, exit 0, `KNOWN (36 refs, 1 files)` | **STILL OPEN-AND-GATED**, unchanged — and **N1 shows the gate it produced is scoped to the charged instance, not the measured class** |
| **C310-N1** (`:429-435` V3 entity-role note, operator fork) | G5 | **STILL-OPEN, 4th pass** — the chain runs C278 → C310 → C350 → C390, and C350's guard 5 pre-registered this pass as the fourth. Routing-failure report, **no self-decision** |
| **C310-N2** (`observationCount` in `.ttl`, schema forbids) | `web4-standard/ontology/t3v3-ontology.ttl:107`; **0** hits in the schema | **STILL-OPEN**, subsumed in the five-row class. Adjudicate with C350-N1 |
| **C310-N3** (36 refs to a context that does not exist) | G2 | **OPEN-AND-GATED**, unchanged |
| **C310-N4** (header `:4` names the retired context) | target frozen ⇒ verbatim | **STILL-OPEN, UNCHANGED** |
| **C270-N1** (successor gate anchored to the crate) | no window commit touches `web4-trust-core/` | **STILL-OPEN**, disposition-checked |
| **C270-N2** (Rust cross-language vectors unbacked) | `grep -rn tensor-operations --include=*.rs . \| grep -v target` → **0** | **STILL-OPEN**, conclusion untouched |
| **C270-N3** (pre-C-series alignment audit never entered the ledger) | inclusive rule admits it; lineage = 13 | **STILL-OPEN as a status row** |
| **C192-N3** (layer-split composite aggregation is INFO) | C270/C310/C350 do-not list | **STANDS. Not re-raised** |

**C310's and C350's do-not-raise lists honoured verbatim**: composite-weights #2/#3, decay-model #5
Training/Temperament, C238-N1/D2 NUMERIC facet, the vectors-as-authority form, the C230 "+2 shift",
the `ns/`-vs-`ontology#` split, C278-N2, `C318-I-1`. **None re-opened.**

---

## §E — Instrument index

**Built by capture.** All paths repo-relative. **Basenames checked with
`git ls-tree -r --name-only a68adb93 | grep -c "/<basename>$"`; ⚠ = collides, always written rooted:**
`t3-v3-tensors.md` **2** ⚠ (`web4-standard/core-spec/` and `forum/nova/web4-sal-bundle/`) ·
`validate_vectors.py` **5** ⚠ · **`acp.jsonld` 2 ⚠** — new this pass:
`web4-standard/schemas/contexts/acp.jsonld` and `forum/nova/ACP-bundle/acp.jsonld`. **N2's row is the
former**; the `forum/nova/` copy is inside the tree `C314:243` **DECLINED** as a frozen 2025-09-15
inbound proposal, and this pass does not read it.
`validate_context_refs.py` 1 · `trust.py` 1 · `test_trust.py` 1 · `t3v3-jsonld.schema.json` 1 ·
`t3.jsonld` 1 · `v3.jsonld` 1.

| claim | instrument | scope | result |
|---|---|---|---|
| target frozen | `git rev-parse --short a68adb93:web4-standard/core-spec/t3-v3-tensors.md` ⚠ | 1 file | `32d3368e` = C350's = C310's |
| target motion | `git log --oneline 03b61ac2..a68adb93 -- web4-standard/core-spec/t3-v3-tensors.md` ⚠ (pathspec confirmed to match a tracked file before the 0 was published, v39b) | 1 file | **0** |
| window | `git rev-list --count 03b61ac2..a68adb93` | repo | **32** |
| mirror motion | `git log --oneline 03b61ac2..a68adb93 -- web4-standard/schemas/ web4-standard/ontology/ web4-standard/test-vectors/ web4-standard/implementation/sdk/` | 4 trees | **0** |
| lineage (inclusive rule) | `git ls-tree -r --name-only a68adb93 -- docs/audits web4-standard/docs/audits \| grep -icE 't3-v3\|t3v3'` — pinned to `a68adb93`, which predates this document, so the working tree cannot enter its own scope (v33) | both trees | **13** |
| slot-number channel | `git grep -n "C390" a68adb93 -- docs/audits web4-standard/docs/audits` | both audit trees | **3** hits, all inside C350 ⇒ **0** sibling routings |
| subject-matter channel | `git grep -l -E "t3v3\|T3/V3\|t3-v3\|DimensionScore\|t3v3-ontology" a68adb93 -- docs/audits web4-standard/docs/audits`, minus lineage, filenames ≥ 2026-08-10 | both audit trees | **9** docs |
| **N1 backing-file census** | `test -f web4-standard/schemas/contexts/<n>.jsonld` over the 11 SDK constants | 11 files | **10 BACKED, 1 MISSING** (`trust-query.jsonld`) |
| **N1 emission path** | `grep -n TRUST_QUERY_JSONLD_CONTEXT -r web4-standard/implementation/sdk/` | SDK tree | `web4/trust.py:53,:108,:713` · `web4/__init__.py:76,:554` |
| **N1 gate blindness (EXECUTED)** | `python3 web4-standard/test-vectors/validate_context_refs.py` | 1 gate | 283 refs, **9** names, 8 `OK`, 1 `KNOWN`, **exit 0**; `trust-query.jsonld` **absent from the 9** |
| **N1 why blind** | `json.load` of both `web4-standard/test-vectors/trust-query/*.json`; gate domain at `:83` | 2 vectors | top-level keys `description, input, expected_output, should_succeed, notes`; **no `@context` at any depth** |
| **N1 green test** | `web4-standard/implementation/sdk/tests/test_trust.py:941`; `python3 -m pytest tests/test_trust.py tests/test_t3v3_jsonld.py -q` | 2 suites | asserts the **string**; **175 passed** |
| **N1 prior print** | `docs/audits/C310-t3-v3-tensors-8th-delta-2026-08-02.md:315` | 1 file | `trust-query.jsonld → ** MISSING ** (emitted by trust.py:108)` |
| **N1 gate provenance** | `git log --diff-filter=A -- web4-standard/test-vectors/validate_context_refs.py` | 1 file | `8d3808db` **2026-08-04**, 2 d after C310; docstring `:13` cites `audit C310-N3` |
| **N1 direction** | `git log -S 'TRUST_QUERY_JSONLD_CONTEXT = "…"' -- web4-standard/implementation/sdk/web4/trust.py`; `git log --diff-filter=A` **per file** on two contexts | 3 files | constant `2d7d3e3d` **2026-04-05**; contexts `936c2d92` **2026-03-24**, `6300d34a` **2026-03-21** ⇒ born unbacked **12 d after** the convention |
| **N1 consumption (severity bound)** | `grep -rnE "pyld\|jsonld\.expand\|from rdflib\|import rdflib" --include=*.py .` (excl. `target/`, `.git/`); same for `*.rs`/`*.ts`/`*.js` | repo | 2 MRH scripts only; **0** non-Python ⇒ **latent** |
| **N1 refutation 1** | `C378:290`; `web4-standard/implementation/sdk/tests/test_jsonld_lifecycle.py:1029`; `web4-standard/implementation/sdk/web4/trust.py:705-717` | 3 files | non-JSON-LD registry note **confirmed**; `to_jsonld()` ships anyway ⇒ disjunction |
| **N1 refutation 2** | `validate_context_refs.py:5-8, :40, :107` | 1 file | `schemas/contexts/` resolution is the **stated ratified convention** ⇒ not charged |
| **N2 class table** | per-pairing set difference: schema `properties` names (recursive) − context terms − aliases − JSON-LD keywords; `t3v3` = intersection over **both** contexts | 9 pairings | **4 affected, 40 unmappable**; `acp` 23 · `r7-action` 8 · `lct` 7 · **`t3v3` 2** |
| **N2 refutation A** | scoped-`@context` scan of all `web4-standard/schemas/contexts/*.jsonld` | 10 files | **none** — falsified |
| **N2 refutation B** | `@id`/`@type`/`@graph` alias scan, same 10 | 10 files | **none** — falsified |
| **N2 pincer** | `additionalProperties: false` count per property-block | 9 schemas | acp 11/11 · t3v3 3/3 · lct 13/13 · r7-action 21/22 |
| **N2 t3v3 control** | intersection vs per-context difference; evidence-key census over the published vectors | 1 vector file | `t3-only` = `validity/valuation/veracity` (expected structure); **2 of 38** cases carry either key |
| **N2 not-net-new** | `docs/audits/C314-acp-framework-8th-delta-2026-08-05.md:188-203`, `:242`, `:258` | 1 file | class table published 2026-08-05; `acp` 22 · `lct` 6 · `r7-action` 2 · `t3v3` 2 |
| **G1** | `grep -n "rdfs:domain web4:DimensionScore" web4-standard/ontology/t3v3-ontology.ttl`; `$defs.DimensionScore` of `web4-standard/schemas/t3v3-jsonld.schema.json`; `@`-level keys of both contexts | 4 files | 5 props (`:87 :92 :97 :102 :107`); 4 schema keys + `additionalProperties: false`; **no `@vocab`** ⇒ **3 of 5 ❌, unchanged** |
| **G5** | `grep -rn "v3-valid-003" web4-standard/` | tree | `test-vectors/schema-validation/t3v3-jsonld-validation.json:167` — **present** ⇒ option B not executed |

**Not mechanically reproducible: none.** The one row C350 had to label hand-derived (JSON-LD
*expansion*, `rdflib`/`pyld` absent on this host — re-confirmed absent) **is not relied on by any
finding in this pass**: N1 rests on file existence and an executed gate, N2 on set differences over
parsed JSON with both structural refutations executed.

---

## §F — Own errors

1. **The first per-pairing table published `t3v3` at 5 unmappable properties. The correct figure is
   2.** `validity/valuation/veracity` are absent from `t3.jsonld` and `talent/temperament/training`
   from `v3.jsonld` because one shared schema faces two split contexts — expected structure, not
   defect. Caught by running the intersection as a control. **The sharp part: `C314:201` had already
   made and documented this exact correction nine days earlier**, in the same words (*"that penalises
   T3Tensor for not being defined in V3's context and vice versa, which is not a real defect"*). I
   re-made an error the corpus had already fixed and published, because I built the measurement before
   reading the document that measured it. **Read the prior art before building the instrument, not
   after** — the novelty check and the method check are the same check run in different orders.
2. **The pass's drafted headline was "the snake_case/camelCase split is a corpus-wide class", and it
   is not net-new.** `C314:188-203` published the class table, the corpus-shaped conclusion, and the
   per-pairing counts on 2026-08-05. The draft survived until the two-pass novelty enumeration (v44,
   v57) was run against the *subject matter* rather than the target filename. Had it shipped, this
   pass would have re-charged a sibling lineage's nine-day-old finding as its own headline. **What
   survives is N2 as a discharge with a corrected denominator — a much smaller claim, correctly
   sized.**
3. **C350-N2's characterisation was too strong and is corrected in §D.** C350 filed it as *"C314
   measured this defect … and routed nothing to the owner."* Reading `C314:242` in full this pass:
   C314 **did** route it — *"Routed to author/SDK track; not applied"* — and stated the corpus-shaped
   scope. The true, narrower claim is that it did not route to **this lineage**, which is what left
   `t3v3` unowned. My own predecessor's row was the one that needed correcting (v52), and it took
   reading the cited document rather than the citing one.
4. **A candidate finding was killed after being drafted**: that the gate's `schemas/contexts/`
   resolution is too narrow because `ontology/t3v3.jsonld` exists on disk. Refuted by the gate's own
   docstring `:5-8`, which states the convention and cites the SDK test that asserts it. Recorded as
   §C N1 refutation 2 rather than dropped, so the next pass does not re-derive it — a rejected
   candidate written up with its baseline hands the next pass a **closed** question (v55).
5. **`acp.jsonld` collides as a basename (2 tracked files) and the first draft of §E did not check
   it**, having inherited C350's collision list (`t3-v3-tensors.md`, `validate_vectors.py`) rather
   than re-running the check over *this* pass's artifact set. Caught before publication. **A
   collision list is per-pass, not per-lineage.**

---

## §G — Disposition

**N1 MEDIUM · N2 LOW · N3 INFO · N4 INFO. 1 net-new, 1 d4 member discharged, 1 reception decomposed,
1 predecessor row corrected. ZERO mutation.**

- **C391 = declared NO-OP.** N1 routes to the **SDK / build track** with three named shapes, none
  chosen here — do **not** create `web4-standard/schemas/contexts/trust-query.jsonld`, edit
  `web4-standard/implementation/sdk/web4/trust.py`, or add a `KNOWN_MISSING` entry autonomously.
- **N1 and `C366-N1` item (3) are the same remedy seen from two lineages** and should be adjudicated
  together: widen `validate_context_refs.py`'s domain from `test-vectors/` to every
  `web4.io/contexts/*.jsonld` reference under `git ls-files web4-standard/`. **N1 is the instance that
  proves the ask**, and it is the one the current gate cannot reach. If the widening lands, it
  subsumes N1 by making the miss visible — but **visibility is not a fix**, and the `KNOWN_MISSING`
  disposition text for `t3v3.jsonld` is **false for `trust-query.jsonld`** (different mechanism,
  proved by direction) and must not be copied.
- **Delivered outward this fire, by ROLE not by number** (the channel that worked): N1 → SDK/build
  track, joining `C366-N1`; N2's instrument divergence → the **acp lineage at ≈ C394**, by name, under
  `C314:258`'s own guard 3; N4's `r7-action` member → the r7 lineage. The by-number channel measured
  **0** for the second consecutive pass on this file.
- **Rotation**: next t3-v3 delta ≈ **C430**.

**Baseline for C430** (blobs at `a68adb93`; basename hits re-checked *this pass*, ⚠ = write rooted):

| artifact | note | basename hits |
|---|---|--:|
| `web4-standard/core-spec/t3-v3-tensors.md` | `32d3368e`, 689 L, frozen 10 passes | **2** ⚠ |
| `web4-standard/ontology/t3v3-ontology.ttl` | `rdfs:domain web4:DimensionScore` block `:87-110` | 1 |
| `web4-standard/schemas/t3v3-jsonld.schema.json` | `$defs.DimensionScore` `:11-37`, `additionalProperties` `:36` | 1 |
| `web4-standard/schemas/contexts/t3.jsonld` · `…/v3.jsonld` | camelCase evidence terms | 1 · 1 |
| `web4-standard/schemas/contexts/acp.jsonld` | N2's 23-property row | **2** ⚠ |
| `web4-standard/test-vectors/schema-validation/t3v3-jsonld-validation.json` | `v3-valid-003` `:167` | 1 |
| `web4-standard/test-vectors/validate_context_refs.py` | `KNOWN_MISSING` `:49-56`, domain `:83`, resolution `:107` | 1 |
| `web4-standard/implementation/sdk/web4/trust.py` | `:108` constant, `:705-717` `to_jsonld`, `:713` emission | 1 |
| `web4-standard/implementation/sdk/tests/test_trust.py` | `:941` string assertion | 1 |
| `web4-standard/test-vectors/validate_vectors.py` | `validate_t3v3` `:106` | **5** ⚠ |

**Guards for C430.**
1. **Re-run N1's backing-file census first** (11 SDK constants → `web4-standard/schemas/contexts/`).
   **Identify WHICH of the three shapes landed** — a created context file, a removed `to_jsonld()`, or
   a `KNOWN_MISSING` entry are three different worlds. If a `KNOWN_MISSING` entry appeared, **read its
   disposition text**: if it reuses C310-N3's reconciliation wording, the direction finding was lost in
   the fix and the entry is false as written.
2. **Check whether `validate_context_refs.py`'s domain was widened.** If it now scans beyond
   `test-vectors/`, re-derive the census against the new domain and check what *else* the widening
   surfaced — `C366:219`'s table names `sal.jsonld` (2 sites) and `law.jsonld` (2 sites) as the other
   members, and they are not this lineage's.
3. **Re-run the five-row `DimensionScore` table** (G1). Unchanged for 10 passes; if any row became ✅,
   check the other two moved with it — `additionalProperties: false` means a half-applied fix breaks
   published vectors rather than degrading quietly.
4. **`C310-N1`'s A/B fork: 5th pass** (chain C278 → C310 → C350 → C390 → C430). Read `v3-valid-003`,
   **not** the note. Do not self-decide. If it is still unanswered at a fifth check, the unanswered
   **fork itself** — not the note — is the row worth escalating, and this ledger should say so rather
   than re-probing a sixth time.
5. **Run the inbound sweep BEFORE §A, on subject matter as well as the filename token, and read the
   cited document before building any instrument** (§F.1, §F.2 — both of this pass's substantive own
   errors were prior art discovered late). Measure the by-number channel and **record the negative**.
6. Do **not** re-open: everything on C310's and C350's do-not-raise lists; N1 refutation 2 (the gate's
   `schemas/contexts/` resolution — closed with its baseline); `r7-action`'s d4 member (r7's slot);
   `C318-I-1` (closed at C350).

---

## Pattern (C390)

**C350 found a defect four instruments had touched without asking the question that convicts it. This
pass found one that *this lineage's own instrument had already printed* — and then watched the gate it
spawned inherit the same blind spot.**

`C310` built a baseline for one reason: to prove `t3v3.jsonld`'s missing context was not an idiom. The
baseline worked. It returned **two** misses out of eleven, and C310 wrote the correct sentence about
its own output — *"both misses are in the T3/V3 lineage"* — charged one, and carried neither the other.
`C350` then disposition-checked C310's **carries**, which is the right method and could not possibly
have found it: `trust-query.jsonld` was never a carry, it was *evidence for* a carry. Twelve days
later a different lineage re-derived it from scratch and routed it back by role.

And the gate is the same shape one level up. `validate_context_refs.py` was written two days after
C310, cites `C310-N3` in its docstring, and exists specifically to stop this class of error from
staying invisible. Its domain is `test-vectors/` — **the tree the charged instance lived in**, not the
class the baseline measured. Three lines above the miss it was built for sat a miss it structurally
cannot see, in a live SDK emission path, and it exits **0** while `175` tests pass.

**v60 (new): a fact printed in a finding's own baseline evidence is not carried by that finding's
disposition row.** Baselines exist to prove a defect is not an idiom, so they systematically surface
siblings — that is their function. But the next pass enumerates the **carry table**, and the carry
table is populated from *findings*, not from *evidence*. The gap is structural, not careless: C310 did
everything right except promote its own measurement into a row. **When a baseline shows N misses and
you charge one, charge or explicitly carry the other N−1 — and when you build a guard from a finding,
scope it to the baseline's denominator, not to the charged instance's tree.** The instrument you write
in response to a finding inherits that finding's domain unless you widen it on purpose.

The corollary is the one this track keeps re-learning from the other side: **the by-number routing
channel measured 0 again, and the by-role channel delivered the entire pass.** `C366` did not know
this slot's number. It knew whose subject matter it was, said so in a table, and wrote *"ride the next
trust slot."* That arrived.

→ [[feedback_evidence_is_not_a_carry]] / [[feedback_guard_domain_is_not_its_class]] /
[[feedback_delivery_is_an_act_of_the_receiver]] / [[feedback_novelty_is_an_absence_claim]] /
[[feedback_metric_denominator_is_a_domain]] / [[feedback_unit_green_is_not_system_green]]

---

*C390 verdict: `t3-v3-tensors.md` byte-frozen for the 10th consecutive pass, mirror layer at zero
commits — **zero autonomous mutation**. One MEDIUM net-new in this lineage's own SDK module, received
by role from a sibling lineage and traced back to a print in this lineage's own eight-pass-old
baseline; one d4 member discharged with an executed denominator that shrank the pass's own drafted
headline to a footnote; one operator fork unanswered at a third pass and reported as a routing failure
rather than decided.*
