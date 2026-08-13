# C372 Audit: `entity-types.md` — 9th-Delta Re-Audit (11th Pass)

**Date**: 2026-08-12
**Auditor**: Autonomous session (Legion, web4 track) — firing `20260812-180000`
**Document**: `web4-standard/core-spec/entity-types.md` (804 lines, blob `a2dda417`)
**Lineage** (11 docs, inclusive rule — the origin `docs/audits/entity-types-internal-consistency-2026-05-22.md`
self-identifies as `# C8 Audit` and is glob-invisible under `C*`, but is cited by name in all successors;
C332 verified this and ruled the C326 glob trap does **not** bite here — not re-litigated):
C8 → C26 → C64 → C65 (remediation, 7 applied) → C104 → C137 → C176 → C214 (#523 Effector §4.8) →
C252 → C292 → C332 → **C372 (this audit)**
**Window**: `38d0bd89..HEAD` — 50 commits / 41 files, 2026-08-07 → 2026-08-12. **Rotation**: `C332 + 40`.

## Headline: the standard's entity-type register cannot be applied to an entity, and the one document shape it *can* validate certifies an empty registry as complete

Three findings, **zero mutation of the standard**, all executed rather than read.

The through-line: `entity-types.md` §2.1 is the register of 15 canonical entity types. Its faithful
machine transcription — `schemas/entity-jsonld.schema.json` `$defs/EntityType` — is **structurally
unreachable for any real entity**, because that schema's top-level `oneOf` admits only
`EntityTypeInfo` and `EntityTypeRegistry`: documents *about* the taxonomy. Executed against a real
LCT from the standard's own vector file, the register schema returns `FAIL(shape)` even for a
perfectly valid `human` LCT. And the one shape it *does* accept — `EntityTypeRegistry`, described in
its own text as *"Full registry of all **15** canonical entity types"* — carries no cardinality
constraint at all: an empty registry validates, and the corpus's own invalid-vector set already
contains one.

**The proposed headline of this pass was falsified in policy review and is recorded as own-error §E.1.**

---

## §0. Gates

**Step 0 (queue).** Canonical `/home/dp/ai-workspace/private-context/SESSION_FOCUS.md` read (not the
worktree copy). `[Legion]` items: 0a hestia-owned; 0b SERVED; 0c WIRED, awaits a vault-authorized
actor (PolicyGate W-deny — not circumvented); 0d IN MOTION (HUB track's PR); 0e SERVED; 0f owned by
the CBP Publisher track. **No greenlit item pre-empts the rotation.**

**Step 0.5 (own standing blocks).** `gh pr list --repo dp-web4/web4 --state open --json number,title,headRefName`
returns **`[]`** — zero open PRs corpus-wide. There is no branch to attribute and no PR for
`pr_standing_blocks.py` to read, so **0.5 is CLEAR on the strongest available evidence** (an empty
set, not a filtered one). Recorded explicitly because the C330/C332 instrument note stands: a
`reviewDecision` field is not evidence, and the appended-head staleness bug in
`pr_standing_blocks.py` is still unfixed. Neither mattered this pass — there was nothing to read.

---

## §0.5. Pre-registration (v26) — fixed before any measurement

**Prior, stated as prediction.** C332 left a **6-row deferral ledger naming its own blind spots**
(d1–d6) and two sibling lineages routed carries here (C364-N3, C368-N1). Predictions:

1. The target is frozen; **§A holds by construction and will not be narrated as a discovery.**
2. d1/d2 substrates are frozen ⇒ **NEGATIVE is the predicted outcome for both.**
3. d3 (`schemas/contexts/entity.jsonld`, never opened in 10 passes) was deferred on the hypothesis
   that it is a **4th published description of the register** and would escalate C332-N1.
   **Pre-registered:** if it carries no type enumeration, that hypothesis is **refuted**, and the
   refutation gets published as prominently as a confirmation would have been.
4. **Pre-registered matcher set** for the novelty claims, fixed before searching: site identifiers
   (`EntityTypeInfo`, `EntityTypeRegistry`, `entity-jsonld.schema`) **and** domain vocabulary
   (`minItems`, `uniqueItems`, `cardinality`, `completeness`, `all 15`, `full registry`).

**Denominators published up front (v40), because the inherited counter is ambiguous.**
Two different freeze counters have been conflated in this lineage's guards, so both are published:

| counter | value at C372 | denominator |
|---|---|---|
| passes over blob `a2dda417` | **5th** (C214, C252, C292, C332, C372) | since `1354e4c2` (#523, 2026-07-14) — a **non-audit** mutation |
| lineage's "consecutive zero-mutation pass" | **7th** (C332 self-published as 6th at `C332:416`) | audits that mutated nothing |
| byte-freeze age | **29 days** | `1354e4c2` → today |

Policy review proposed a third reading ("8th consecutive zero-mutation, counting from the C65
remediation `5baa160f`"). **Not adopted** — `C332:416` pairs "6th consecutive zero-mutation pass"
with the byte-freeze narrative, so the successor value is 7. The disagreement is itself the point:
**the inherited counter is under-specified, which is why all three denominators appear above.**

**In-window movement** (`38d0bd89..HEAD`, 50 commits / 41 files): `web4-standard/` **1**,
`web4-core/` **0**, `sdk/` **0**, `hub/` **19**, `docs/` **22**. **Target: 0.**
Every artifact this pass executes is also unmoved since C332 — `entity-jsonld.schema.json`,
`entity-taxonomy.json`, `entity-jsonld-validation.json`, `contexts/entity.jsonld` = **0 commits each**.

---

## §A. Held by construction

Target blob unchanged since C332's own audit commit (`git diff --stat c32a83c0..HEAD -- <target>`
= empty). Therefore, **without re-narration**: the 7 C65 remediations, the §4-preamble count at
`:281`, and the 9 standing carries (C8-L3, C23-H1, C24-H1, B2/B9, B7, B10/B11, B12) all **HOLD**.
Design-questions C23-H1 / C24-H1 / B7 / B2 / B9 / B10 / B11 and **C292-N1** remain
operator-unanswered → **one** operator memo, not self-applied.

---

## §B. The deferral ledger — 6 of 6 discharged, 4 negative

C332 closed with an explicit instruction: *"Do NOT inherit that list as a mirror set — it is what
this pass did NOT measure."* Each row was executed independently.

| row | subject | disposition |
|---|---|---|
| **d1** | C292-N1 author ruling | `git log` on `ontology/role-extension.{ttl,schema.md}` since C332 = **0 commits**. **NEGATIVE — C292-N1 STANDS**, unanswered, 3rd pass. |
| **d2** | C332-N2's 3 SDK `slashed` sites | `entity.py:74`, `entity.py:306`, `test_integration.py:1531` — **3→3**. **NEGATIVE — C332-N2 STANDS**, now 57 days live. |
| **d3** | `schemas/contexts/entity.jsonld`, never opened | **Opened for the first time in 11 passes.** 35 lines, `9dd8f06e` (2026-03-23). Defines **term mappings only** — `entity_type → web4:entityType` typed `xsd:string`, **no enum, no value constraint**. **The escalation hypothesis is REFUTED**: it is not a 4th published description of the register, and it places no constraint on entity type. (See §E.3 — it is *cited* as the `@context` by every document in §C.) |
| **d4** | the other 11 top-level schemas — do any ship MUST-PASS vectors contradicting their spec? | **ROUTED, not executed.** This is a corpus-wide sweep, not an `entity-types.md` question; executing it here would repeat the standing `KEY SIGNAL C120→C121` hazard (never batch a corpus-wide MUST sweep). A **bounded** slice was run instead — see §C.3 — which is in-slot because it bounds N1's own defect class. Receiving slots named in §F. |
| **d5** | `FRACTAL_ROLE_IDENTITY.md` + `RFC-COMPOSITE-ENTITY-IDENTITY.md` — anchors were gated, **claims** never read | Both assert *"Roles are first-class LCT entities (`entity-types.md:518`, MUST)"*. **The claim is substantively CORRECT**: `:579` = `Implementations MUST:` and `:581` = `- Support role LCTs as first-class entities`. Only the **anchor** is stale. **NEGATIVE on new substance — and it independently CONFIRMS C332-N3's arithmetic** (`518 + 63 = 581`, exact). C332-N3's remedy has **not** landed (`git grep -c "entity-types.md:518"` = C332 4, FRACTAL 2, RFC 1). |
| **d6** | `DICTIONARY_INTEGRATION_SUMMARY.md` vs §10 | No contradiction: the summary's *"first-class Web4 entities … living semantic bridges"* matches §2.1's Dictionary row and §10.1. **And the summary IS indexed** (`web4-standard/README.md`) ⇒ it is one of C364's 6 indexed siblings. **NEGATIVE — and it confirms C364's scoping** of its own unindexed-summary finding to `METABOLIC_STATES_INTEGRATION_SUMMARY.md` alone. |

**v36 inbound set-difference, pre-registered bound.** `git grep -li "entity type\|entity_type\|entityType"`
over both audit trees = **57 files**; filename sweep `git grep -li "entity-types"` = **102 files**;
`comm -23` residue = **8 files**. Bounded to audit docs **postdating C332** (2026-08-07): **0 of 8**.
**NEGATIVE — recorded as such.** The instrument has yielded for five consecutive fires; this pass it
did not, and that is reported rather than quietly dropped.

---

## §C. Net-new findings

### C372-N1 (MED) — the register schema cannot count, and the corpus's own invalid set proves it
*Filed as a **sharpening of C332-N1**, not clean net-new — see the novelty qualification below.*

`schemas/entity-jsonld.schema.json` `$defs/EntityTypeRegistry` describes itself:

> `"description": "Full registry of all 15 canonical entity types."`

Its only payload property is:

```json
"entity_types": { "type": "array", "items": { "$ref": "#/$defs/EntityTypeInfo" },
                  "description": "All entity type metadata entries." }
```

**No `minItems`, no `maxItems`, no `uniqueItems`, no `contains`.** (`additionalProperties: false` is
present, but constrains the *key set*, not the array.) The completeness assertion lives in prose in
the parent object; nothing in the construct can enforce it.

**Executed** via the SDK's real validator (`validate(doc, "entity").valid`), controls first:

| case | result |
|---|---|
| registry with all 15 real types (**control**) | PASS |
| `entity_types: []` — an empty *"full registry of all 15"* | **PASS** |
| `"human"` × 15 (duplicates) | **PASS** |
| registry with 1 entry | **PASS** |
| **neg control** — type `"banana"` | FAIL |
| **neg control** — type `"agent"` | FAIL |

The negative controls fire, so the enum is not vacuous and the instrument is admissible.

**The sharpest evidence is the corpus's own, and it is already shipped.** Denominator: the vector
file holds **5 registry-shaped documents — 2 MUST-PASS (`entity-valid-009`, `-010`) and 3 MUST-FAIL
(`entity-invalid-016`, `-017`, `-018`).** `entity-invalid-018` ships:

```json
{ "@context": [...], "@type": "EntityTypeRegistry", "entity_types": [], "version": "1.0" }
```

— an **empty** "full registry of all 15", charged solely for `"error_kind": "additionalProperties"`
(the stray `version` key). **Removing `version` and re-validating: the empty registry PASSES.** The
standard's own conformance suite therefore contains a document that is empty-and-complete, and
objects only to an unrelated extra field. Meanwhile the two MUST-PASS registries are described by
their own authors as *"minimal with one entity type"* and *"two entity types"* — so the **vector
author and the schema author disagree about what `EntityTypeRegistry` is**, and both are green.

**Class bounded (v40), 2 of 12.** An instrument over all 12 top-level schemas — parent object whose
title/description asserts completeness (`all N`, `full`, `complete`), carrying an array property with
no cardinality guard — returns exactly **2**:

| schema | construct | claim | guards |
|---|---|---|---|
| `entity-jsonld.schema.json` | `EntityTypeRegistry.entity_types` | *"Full registry of all 15 canonical entity types"* | **NONE** |
| `capability-jsonld.schema.json` | `CapabilityFramework.levels` | *"Complete capability level framework with all 6 levels"* | **NONE** |

The sibling was **executed too**: a `CapabilityFramework` with `levels: []` **PASSES**. It is *not*
charged here — it routes to the `lct-capability-levels` lineage (§F).

**Deflating precedent engaged and partially sustained.** `C160:88` ratified a deflation for exactly
this shape: *"`constraints` `minItems` unenforced by v1 schema … Schema is permissive (doesn't forbid
&lt;3); **under-enforcement, not contradiction**."* That precedent is real and it is why **this is MED,
not HIGH**. It does not fully apply: C160's case was *spec says N, schema is silent* — two artifacts.
Here the **schema's own description** asserts the cardinality, and the **standard's own MUST-PASS
vectors** certify instances that violate it. That is self-contradiction inside one artifact plus its
conformance suite. **Severity is capped at MED** because no shipping artifact is wrong today: the
SDK's producer `entity.py:353 entity_registry_to_jsonld()` does emit all 15 and validates.

**Remedy is an author ruling, not an auditor edit** — the two readings are mutually exclusive:
either add `minItems: 15` / `uniqueItems: true` (if `EntityTypeRegistry` means *the* register), or
correct the description to *"A registry of entity type metadata entries"* (if it means *a* registry,
which is what the vector authors evidently assumed). **Not self-applied.**

**Novelty, qualified (v44).** Site-identifier matchers over both audit trees: `EntityTypeRegistry`
**0 of 212**, `"full registry"` **0**, `EntityTypeInfo` **4** (C64/C176/C252/C332, all this lineage),
`entity-jsonld.schema` **3**. But the claim must be qualified twice, and both qualifications were
found by searching the **domain's** vocabulary rather than the site's identifier:

1. **The identifier is overloaded.** `archive/reference-implementations/conformance_test_suite.py:435`
   has an `EntityTypeRegistry` that is a registry *of entities* (`lct_id → type`), a different object.
   A zero-hit grep on an overloaded identifier is weak evidence and is not relied on alone.
2. **C332 was one hop away.** `C332:218` reads: *"All 20 invalid cases in the file assert shape errors
   only (missing field, wrong enum member, wrong JSON type, `additionalProperties`, `minItems`,
   `uniqueItems`) — not one asserts a taxonomy-content error."* Same file, same instrument. C332
   charged *field-content* divergence of `EntityTypeInfo`; N1 charges *registry cardinality*. It is a
   genuine increment, but it is **a sharpening of C332-N1 and is filed as one.** Claiming clean
   net-new here would violate this session's own v44 rule against its own lineage.
   `"all 15"` hits (7 files) were each read: all concern the **Rust/Python enum membership**
   (C176-N1) — none the schema's completeness constraint.

### C372-N2 (MED) — §13.4's accountability frame keys on a vocabulary that is not the metabolic register
*Adjudicating **C364-N3**, which routed this locus here and is **credited**, not superseded.*

`entity-types.md:779-783` publishes, under §13.4 *Accountability Frames*:

| Frame | Metabolic States | Meaning |
|---|---|---|
| Normal | WAKE, FOCUS | Standard accountability — agent chose this outcome |
| Degraded | REST, DREAM | Reduced capabilities acknowledged |
| Duress | CRISIS | Fight-or-flight — consequences beyond agent's control |

**C364-N3 measured the forward direction** and stated it correctly: *"Five names. One — REST — is a
state of this specification."* It routed adjudication here and explicitly declined to adjudicate.
**C372 adds the operational complement — the reverse direction — executed, not read.** An
implementation does not hold a frame and look for states; it **holds a state and looks up the frame**.
Running the canonical register (`SDK web4/metabolic.py` `MetabolicState`, = `SOCIETY_METABOLIC_STATES.md`
§2.1–§2.8, two independent witnesses at 8) through the table verbatim:

```
ACTIVE       -> NO FRAME      REST         -> Degraded
SLEEP        -> NO FRAME      HIBERNATION  -> NO FRAME
TORPOR       -> NO FRAME      ESTIVATION   -> NO FRAME
DREAMING     -> NO FRAME      MOLTING      -> NO FRAME

states with an accountability frame: 1 of 8
frame keys that are not register states: ['WAKE', 'FOCUS', 'DREAM', 'CRISIS']
```

**1 of 8.** And the three non-states are not near-misses; each was checked in the canonical document:

- **`WAKE`** — appears 23× but never as a state. It is a **transition trigger**
  (`SOCIETY_METABOLIC_STATES.md:181` *"Sleep → Active: Wake trigger fired"*). Its target state is `ACTIVE`.
- **`FOCUS`** — **1** occurrence, the English noun inside a prose description of Hibernation
  (`:83` *"preservation focus"*). SDK **0**, vectors **0**. It is not a state and never was.
- **`CRISIS`** — 3 occurrences, all prose. SDK **0**, vectors **0**. Decisively,
  **`:99` is the description of `TORPOR`: *"Crisis mode when resources critically low."***
- **`DREAM`** — one character from `DREAMING`, and is not it.

**The consequence is the accountability equation itself**, which the spec states in the very next
sentence (`:785`): *"CRISIS mode changes the **accountability equation**, not policy strictness."*
`TORPOR` is the state whose own definition **is** crisis mode — and it resolves to **no frame**, while
the key `CRISIS` matches nothing any implementation can emit. A society in emergency conservation
therefore falls through to whatever the implementer's default is, on the one table that decides
whether an agent is held fully accountable for an outcome.

**Severity MED, not HIGH**, on modality: §13.4 is a descriptive table. `entity-types.md` carries **6**
`MUST`s in total and none is in §13.4, so no conformance clause is being violated — this is a
vocabulary that cannot bind, not a broken requirement. **Remedy is an author ruling** (map the frames
onto `ACTIVE/REST/DREAMING/TORPOR/…`, or state that §13.4's vocabulary is a distinct agent-level
register and cross-reference it) — **not self-applied**, and it touches a byte-frozen document.

**Anchor verified.** C364-N3's citation `:779-783` is **exact** (header `:779`, separator `:780`, three
rows `:781-783`). Policy review asserted the table body *"runs to `:785`"*; `:785` is the following
prose sentence. **C364-N3's anchor stands; the review's correction is not adopted** — see §E.2.

### C372-N3 (MED) — the §2.1 register is structurally unreachable for any real entity
*This is what survived the falsification of this pass's proposed headline. See §E.1.*

`schemas/entity-jsonld.schema.json` is the only faithful 15-value transcription of §2.1 in the schema
layer. Its top level is:

```json
"oneOf": [ { "$ref": "#/$defs/EntityTypeInfo" }, { "$ref": "#/$defs/EntityTypeRegistry" } ]
```

Both branches are **taxonomy-metadata** documents. `EntityTypeInfo.required` =
`entity_type, modes, energy, can_r6, description` — that is the description of a *type*, not an
*instance*. **The schema therefore never sees an entity.**

**Executed** on a real LCT taken verbatim from the standard's own `lct-jsonld-validation.json`
(`valid[0]`), varying only `binding.entity_type`:

| `entity_type` | enforced schema (`"lct"`) | Python SDK `LCT.from_jsonld` | register schema (`"entity"`) |
|---|---|---|---|
| `human` (**control**) | PASS | OK | **FAIL (shape)** |
| `agent` | **PASS** | **`ValueError: 'agent' is not a valid EntityType`** | **FAIL (shape)** |
| `banana` (**neg control**) | FAIL | `ValueError` | FAIL (shape) |

The control carries the finding: the register schema returns `FAIL(shape)` for a **perfectly valid
`human` LCT**. The unreachability is structural, not a property of the type value.

**Consequence.** A document that PASSES the standard's own default LCT validation path **crashes the
Python SDK**, and the declarative layer that knows the correct answer cannot be pointed at it. Three
implementations *do* enforce the 15 on real bindings — and each is an independent witness that §2.1
is canonical:

- Python — `sdk/web4/lct.py:51-68` (15 members), enforced at `lct.py:94` (`Binding.from_dict`) and
  `:655` (`LCT.from_jsonld`) by enum coercion. Executed: `agent` → `ValueError`.
- Go — `ledgers/reference/go/lct/document.go:34-39` (`ValidEntityTypes`, 15), enforced at `:381`.
- TypeScript — `ledgers/reference/typescript/lct-document.ts:363-367` (15), enforced at `:397`.

So the disagreement is **cross-layer**: the schema layer cannot reject `agent` on an entity, and the
code layer cannot accept it. This is the *mechanism* — it explains why the C368-N1 defect survived
145 days of green gates, which C368 established but did not account for.

**Novelty.** `C368:123` publishes the row `| schemas/entity-jsonld.schema.json | 15 | no |` — C368
recorded that this schema holds 15 and does not gate LCTs. It did **not** state the reachability
argument (that the schema is structurally inapplicable to *any* entity document, control included),
which is what N3 charges. Severity **MED**, not HIGH: no shipping artifact emits `agent` today.

### C368-N1 — CONFIRMED, zero increment
The `agent` cross-schema contradiction is **already recorded at `C368:123`**. This pass re-executed it
(above) and confirms it, and adds two dates: `agent` entered the enforced enum at `c787452e`
(2026-03-20, #53) = **145 days** — matching C368's number exactly and independently; the 15-value
register schema was authored at `9dd8f06e` (2026-03-23), **three days later**, so the two have
contradicted each other for **142 days**. **Filed as confirmation with zero increment** — not as a
"second family member," which would imply an increment that does not exist. Route: C368's operator
ruling (`C368:175`), unchanged.

---

## §D. Measurement hazards named for successors

1. **`validate()` does not raise.** `sdk/web4/validation.py` `validate(document, schema_name, *, raise_on_error=False)`
   **returns** a `ValidationResult`; it does not throw by default. **Any harness measuring this SDK via
   `try/except` reports 100% PASS on every input, including negative controls.** This pass's instrument
   read `.valid` (which is why its neg controls fired), but the policy reviewer's first independent
   run hit exactly this trap and reported all seven cases PASS. Named here because it manufactures
   precisely the false green that C332-N1 was charging.
2. **A completeness claim sits on the parent, the enforcement gap on the child.** This pass's first
   class-bounding instrument scanned array constructs' *own* descriptions and returned **0 rows** —
   missing the very case that motivated it. Corrected instrument (parent's title/description → child
   array's guards) returns 2 of 12. Recorded in §E.4.

---

## §E. Own-error log

**E.1 — the proposed headline was falsified in policy review, and the falsifier was already in the
lineage.** This pass drafted as its headline: *"the only faithful machine transcription of §2.1 can
never be applied to an actual entity — §2.1 has zero enforcement over the objects it governs."* The
second clause is **false**. Three implementations enforce the 15 on real bindings (Python `lct.py:94`,
Go `document.go:381`, TS `lct-document.ts:397`), all verified and executed here. Worse: **`C332:240`
already recorded it verbatim** — *"No shipping implementation is wrong today: the Python SDK is 15/15"* —
with `C332:419` publishing the measurement as a gate row and `C332:182` calling it *"load-bearing …
it makes the Python SDK an independent witness for §2.1."* The immediately prior pass of this same
lineage contained the falsifier three separate times, and this pass did not check its own predecessor
before drafting. (Policy review cited this as `C332:243`; the correct loci are `:182`, `:240`, `:419` —
verified line by line, per §E.2's rule, including on the correction that exposed this error.)
The true, narrower claim (unreachability **within the schema layer**) survives as N3. The scope claim
"zero enforcement" was reached by measuring the schema layer and generalising to the corpus — the same
undeclared-denominator error v51 was written to prevent, committed one fire after writing it.

**E.2 — two policy-review corrections were themselves wrong, and were not adopted.** (a) The review
gave the §13.4 table as `:779-785`; `:785` is the following prose sentence — C364-N3's `:779-783` is
exact. (b) The review corrected the pass counter to "8th consecutive zero-mutation"; `C332:416`
self-publishes "6th", making the successor 7. Both were checked against the files before rejection,
per the C366 rule that a reviewer's path tokens are verified like any other. The review's **substantive**
corrections — E.1, the `entity-invalid-018` evidence, the 5-document denominator, the C332:218
novelty qualification, the C368:123 zero-increment ruling, routing d4 — were all verified and **adopted**.

**E.3 — d3's finding was nearly published as a pure negative.** `contexts/entity.jsonld` carries no
enum, which refutes the escalation hypothesis. But it is the `@context` of every document in §C, and
its `entity_type → web4:entityType` mapping is typed `xsd:string` — i.e. the semantic layer also
places no constraint. That is corroboration for N3 and was almost dropped as "nothing found."

**E.4 — the class-bounding instrument returned 0 and was believed for one step.** See §D.2. The
denominator 2-of-12 exists only because the null result was distrusted enough to re-run against a
known-positive case.

**E.5 — "the corpus's own invalid set proves it" was not this pass's discovery.** N1's strongest
evidence (`entity-invalid-018`) was surfaced by the policy reviewer, not by the audit. This pass had
measured the schema and the two MUST-PASS vectors and stopped there, having never enumerated the
MUST-FAIL set — the same "denominator decides whether an absence is a finding" error as v46.

---

## §F. Routing — nothing self-applied

| item | routes to |
|---|---|
| **C372-N1** author ruling (`minItems: 15`+`uniqueItems` **or** correct the description) | operator / standard-editor |
| **C372-N1** sibling: `capability-jsonld.schema.json` `CapabilityFramework.levels`, *"all 6 levels"*, empty PASSES (executed) | **`lct-capability-levels` lineage** |
| **C372-N2** §13.4 frame vocabulary vs the 8-state register | operator / standard-editor; cross-ref **C364-N3** (credited) |
| **C372-N3** schema-layer unreachability | operator + SDK track; joins **C368-N1**'s operator ruling (`C368:175`) |
| **C368-N1** | CONFIRMED, zero increment — no new routing |
| **C292-N1** (3rd pass), **C332-N2** (57 d), **C332-N3** (remedy not landed) | STAND — existing routes |
| **d4** corpus-wide schema/vector sweep | **NOT executed** (C120→C121 hazard). Prior art: C328 did `lct-jsonld-vectors.json`, C322 the dictionary artifacts, C332 + C372 the entity artifacts. Remaining: `acp`, `atp`, `attestation-envelope`, `capability`, `dictionary`, `r7-action`, `t3v3` → **each to its own lineage slot**, one per pass. |

**Out-of-slot observations, routed and deliberately NOT charged here** (surfaced while mapping N3's
enforcement surface; each belongs to another lineage and none was verified to audit depth):
`sdk-test.yml` is path-filtered to `implementation/sdk/**`, so edits to `web4-standard/schemas/**`
and `web4-standard/test-vectors/**` trigger no CI → **SDK/CI track**; the wheel-shipped
`sdk/web4/schema_registry.json` carries its own copy of all 12 schemas (including the 16-enum) with
no content-equality test against `web4-standard/schemas/` → **SDK track**;
`sdk/tests/test_lct_jsonld_vectors.py:285-301` hard-codes a **15**-value `valid_types` set and would
fail an `agent` vector, contradicting the schema it validates against → **LCT lineage, joins C368-N1**;
`web4-core/src/lct.rs` 9-variant enum → **already booked C176-N1, not re-raised.**

---

## §G. Deferral ledger for the next pass (**C412**) — row count 5, members named

**Do NOT inherit this as a mirror set — it is what C372 did *not* measure.**

- **g1** — C372-N1/N2/N3 are all author rulings; check whether any landed, and whether
  `entity-jsonld.schema.json` gained `minItems`/`uniqueItems` (one `git log`, one `grep`).
- **g2** — the two Specialized-Entity sections carry **9** sub-sections between them (§10.1–10.4,
  §13.1–13.5). Only **one** — §13.4 — had its vocabulary checked against the sibling spec that owns it.
  **Do the other eight name vocabularies owned by other specs?** Specifically: §10.2's
  `dictionary_spec` / `compression_profile` / `trust_requirements` / `evolution` blocks were read this
  pass but **not** cross-checked against `dictionary-entities.md`, and §13.3 (`PolicyGate: IRP-Backed
  Evaluation`) names an IRP contract owned elsewhere entirely.
- **g3** — `entity-taxonomy.json` covers **5 of 15** types (`human, society, device, infrastructure,
  oracle`); `entity-jsonld-validation.json` valid docs cover **10 of 15**. The union omits
  `organization`, `role`, `task`, `service`, `hybrid` — **5 types with no vector anywhere.** Not charged
  this pass (coverage ≠ defect, per v43), but it is the natural companion to N1's completeness question.
- **g4** — the §2.1 table's **Mode** and **Energy** columns were verified 15/15 against the SDK by
  C332; they have **never** been verified against `entity-taxonomy.json`'s `expected` blocks, which is a
  third witness. C332 found the two vector files agree on **0** of 5 shared types — that comparison was
  never extended to §2.1 itself.
- **g5** — d5 is answered for the two RFC documents' *role* claim only. Their **composite-identity**
  claims (P1/P2, `RFC-COMPOSITE-ENTITY-IDENTITY.md:66-95`) cite `LCT §2.1` and `t3-v3 §8.2`, not
  entity-types, and were **not** read against §3/§7.2.

**Next entity-types delta ≈ C412.**
