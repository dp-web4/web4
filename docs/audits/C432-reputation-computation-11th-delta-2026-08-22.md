# C432 — `reputation-computation.md`, 11th delta

**Date**: 2026-08-22 · **Slot**: `web4-20260822-000000` · **Target**:
`web4-standard/core-spec/reputation-computation.md` · **Prior pass**: C392 (`a695ff8b`, 2026-08-15,
PR #718) · **Next slot**: C472.

**Enumeration rule (stated, per the standing rule)**: the lineage is every audit document whose
subject is this target, **including** the non-C-numbered member
`docs/audits/reputation-computation-internal-consistency-2026-05-25.md`. Re-derived at HEAD, never
inherited: **14** (10 delta/base passes + 3 remediations + 1 internal-consistency member). C392
predicted 14. `ls docs/audits/ web4-standard/docs/audits/ | grep -ci reput` → 14.

**Headline**: canon grew a normative MUST about reputation while this target was frozen, and the
MUST names a field the standard's own published schema **forbids**. `interface-planes.md:109`
(created in-window, three days old) requires every reputation-bearing signal to carry a
conduct-vs-infrastructure classification. The target's §1 heading is **"Complete Schema"** and
carries no such field; `$defs.reputation_delta` is `additionalProperties:false`, so adding it breaks
the corpus's own CI-run vectors. The only implementer is `web4-core` + `hub`, and it landed
**six days before** the MUST that ratified it.

**ZERO mutation.** Nothing outside `docs/audits/` is touched by this pass. Every finding whose
remedy forks is routed.

---

## §A — Carry re-resolution at HEAD

Re-resolved **by predicate, not by id** (v65).

| carry | predicate re-run | verdict |
|---|---|---|
| **C392-N1** (MED, routed to 3 owners jointly) — a normative trigger is defined over an `output` key no schema defines | `sed -n '292p'` → `quality_threshold … output.quality`; `sed -n '524p'` → `result.output.get('quality', result.output.get('accuracy'))`; schema `$defs` still names neither | **UNANSWERED, 2nd window.** No arm taken. Target byte-frozen; schema byte-frozen. |
| **C392-N2** (LOW, routes with N1) — neither executed vector set distinguishes the reads | re-run; **extended**, see §D.2 | **UNANSWERED**, and now a *second* executed vector set corroborates it. |
| **C392-N3** (INFO, instrument) — the `$defs.witness_attestation` fork, 3 consecutive passes | per guard (3): **reported against the receiver's ledger, not re-charged.** The block is byte-frozen (`b266a19b`); the fork is now at **4 consecutive passes** with no motion from either referent. | **REPORTED, not re-charged** (v38). |
| **C392-N4** (INFO) — §7 pre-registered NULL, clean on all 4 claims | per guard (4): **discharged null. NOT re-run.** `ReputationStore` unmoved (`reputation.py` `bb73c7c2`). | **DISCHARGED — do not re-run.** |
| **C194-N1** (HIGH, SDK) — Rust `ReputationDelta` wire shape unbacked by the standard | `git grep -n 'sovereign_strength' -- web4-standard` → **0** (re-run) | **STANDS**, and gains a second field — see §D.1 arm D and §E.2. |
| **C312-N1** (MED, fork) — `role_pairing_in_mrh` absent from `$defs.reputation_delta` | schema props re-enumerated at HEAD: 14, `additionalProperties:false`, no `role_pairing_in_mrh`; target `:69` still lists it Required:No | **STANDS, unanswered through two full rotation cycles.** |
| **C352-N1/-N2** (MED/LOW, fork) — the §6 witness-element shape | block byte-frozen; subsumed by the C392-N3 report line above | **STANDS.** |
| **B-D1** (flagship, operator-unanswered) | second datapoint recorded — §C.3 | **STANDS; do not self-resolve.** |

**No carry was discharged by anyone else this window** (opening-sequence step 4): probed the
receivers' ledgers, not their spec files — `web4-standard/` moved **once** in-window and that commit
adds a file rather than answering anything.

---

## §B — The window, pre-registered

**Pre-registration (v26).** Span `a695ff8b..HEAD`. Root: repo. Filetypes: all. Path-bound
(standing rule): `-- . ':!docs/audits' ':!web4-standard/docs/audits'`.

| measurement | command | result |
|---|---|---|
| total commits | `git log --oneline a695ff8b..HEAD` | **46** |
| non-audit commits | `git log --oneline a695ff8b..HEAD -- . ':!docs/audits' ':!web4-standard/docs/audits'` | **28** |
| commits touching `web4-standard/` | `… -- web4-standard/ ':!web4-standard/docs/audits'` | **1** |

The one is `2462881f` — *"canon: specify interface planes (fact planes x exposure classes)"* (#727,
2026-08-19). It modifies `GLOSSARY.md` and `README.md` and **adds**
`web4-standard/core-spec/interface-planes.md` (196 L).

### B.1 — Target and mirrors are byte-frozen

| artifact | blob at HEAD | last mover | moved this window? |
|---|---|---|---|
| **target** `core-spec/reputation-computation.md` | `bfdac3ba` (870 L) | `2bc3bafb` (2026-07-18) | no — **35 d, 6th consecutive frozen pass** |
| `schemas/r7-action-jsonld.schema.json` | `b266a19b` | 2026-05-14 | no |
| `schemas/contexts/r7-action.jsonld` | `015b6e68` | 2026-03-24 | no |
| `implementation/sdk/web4/reputation.py` | `bb73c7c2` | 2026-04-17 | no |
| `implementation/sdk/web4/r6.py` | `013af40c` | 2026-05-14 | no |
| `test-vectors/reputation/reputation-operations.json` | `11234034` | 2026-03-16 | no |
| `implementation/sdk/tests/test_reputation.py` | `eb091265` | 2026-04-17 | no |

All seven of C392's delta-shape mirrors are frozen at C392's own blobs.

### B.2 — And the window is *not* empty, because the mirror set is wrong

`web4-core/src/r6.rs` moved in-window (`91c1c333`, 2026-08-13). It is **not in the mirror set** —
see **§C.4**, which is why this pass has findings at all.

---

## §C — Findings

### C.1 — **C432-N1 (MED, ROUTED — remedy forks 3 ways, do NOT self-apply)**

**Canon requires a field the standard's published schema forbids.**

`web4-standard/core-spec/interface-planes.md:109-110`:

> Every reputation-bearing signal **MUST** carry a classification distinguishing conduct from
> infrastructure, and an unclassified signal **MUST** default to the non-conduct class.

Against the corpus at HEAD:

| site | what it carries | command |
|---|---|---|
| target §1 `### Complete Schema` (`:19-64`) | no classification field | read |
| target §1 `### Field Definitions` (`:66-87`), **15 rows** | no classification row | read |
| target, whole file | 3 hits for `conduct`, **all ordinary English** — `:137` *"Unprofessional conduct"* (a T3 decrease bullet), `:348` *"conduct toward others"*, `:379` *"coercive conduct"*. Zero in the classification sense. | `grep -niE 'conduct\|infrastructur\|unclassified'` = 3 |
| `schemas/r7-action-jsonld.schema.json` `$defs.reputation_delta` | **14 props, `additionalProperties:false`** — the field is *forbidden*, not merely absent | parsed |
| `web4-standard/implementation/sdk/web4/r6.py:580` `ReputationDelta` | 12 fields, no class | read |
| `implementation/sdk/web4/reputation.py` | 0 hits | `grep -niE 'class_\|delta_class\|conduct\|infra'` |
| `implementation/sdk/web4/schema_registry.json` (embedded copy) | **byte-identical** for this `$def` — the copy does not diverge | parsed both, compared |

#### The exhibit — the corpus's own CI-run vectors, not a hand-built document

`web4-standard/test-vectors/schema-validation/r7-action-jsonld-validation.json` is mapped to the
`r7-action` schema by `implementation/sdk/tests/test_schema_validation_vectors.py:41`, so these run
in CI. Two of its `valid` entries carry a `reputation` member. Validator: `jsonschema` 4.26.0,
`Draft202012Validator`, whole-document (not the `$def` in isolation).

| arm | document | errors |
|---|---|---|
| **CONTROL** | `/valid/1` as published | **0** |
| **CONTROL** | `/valid/5` as published | **0** |
| **B** | `/valid/1` + `reputation.class = "conduct"` | **1** — `Additional properties are not allowed ('class' was unexpected)` |
| **C** | `/valid/5` + `reputation.class = "conduct"` | **1** — same |
| **D** | `/valid/1` + `reputation.sovereign_strength` | **1** — same shape, **C194-N1's field** (comparator, see §E.2) |

Denominator: **2 of 2** CI-run valid R7Action vectors that carry a `reputation` member break the
moment the MUST is honoured.

#### Reachability qualifier (v54) — state what is *not* enforced

The prohibition bites **only on the R7Action-embedded form**. The tree discloses this itself:

> `implementation/sdk/tests/test_jsonld_lifecycle.py:436-437` —
> *"ReputationDelta @type != R7Action, so r7-action schema doesn't validate it directly."*

A standalone `rep_delta.to_jsonld()` is never validated against this schema, and the
`web4-core`/`hub` path — the only implementer of the field — never touches this schema at all. So
the *enforced* consequence is confined to embedded deltas in CI; the *unenforced* consequence is
that the standard publishes a delta shape its own reference stack cannot express.

#### The only implementer, and the direction

| site | construct |
|---|---|
| `web4-core/src/r6.rs:252-277` | `DeltaClass { Conduct, Infra, Unclassified }` + `impl Default` → `Unclassified` |
| `web4-core/src/r6.rs:294-299` | `#[serde(default)] pub class: DeltaClass` on `ReputationDelta`. **No `skip_serializing_if`** — every serialized delta carries it. |
| `hub/hub-lib/src/state.rs:885-912` | the class gate: folds only `applied && class == Conduct`; counts the rest by class |
| `hub/hub-daemon/src/rest.rs:3944`, `:4146`, `:4490` | emit + `applied = mode == Apply && class == Conduct` |

Repo-wide, `DeltaClass`/`delta_class` resolves in **those two trees only**: `web4-trust-core/` has
reputation code and no delta class; there is no TS/JS `ReputationDelta`; `simulations/` returns
nothing; the `archive/` `conduct` hits are `misconduct` and a temperament string.

**DIRECTION PROVED, and it runs implementation → canon:**

```
git log -S 'DeltaClass' --diff-filter=A            → 91c1c333  2026-08-13  hub F0.1 (R7a) … conduct-vs-infra delta classification (#703)
git log -S 'reputation-bearing signal' -- web4-standard/ → 2462881f  2026-08-19  canon: specify interface planes (#727)
git log --diff-filter=A -- …/interface-planes.md   → 2462881f  2026-08-19
```

The hub invented the classification on 08-13; canon ratified it on 08-19, **six days later** — which
is exactly the story `interface-planes.md`'s own abstract tells (*"Two independent Web4
implementations each invented a plane vocabulary… evidence that the concept is real, load-bearing,
and missing from canon"*). The defect is not the invention. **The defect is that the ratification
did not propagate**: the reputation spec, its published schema and its reference SDK were left where
they were, and the schema was left actively hostile to the thing canon now mandates.

#### Severity: **MED**, capped — and the cap is *not* the word `proposed`

`interface-planes.md` is the only core-spec file whose status line reads `proposed`. That fact does
**not** carry the cap: of **31** files in `web4-standard/core-spec/`, **21 carry no status line at
all** — including this target — and of the 10 that do, 4 read `Draft` and 3 more read
`… (DRAFT)`/`(Draft)`. `proposed` therefore does not distinguish `interface-planes.md` from
`reputation-computation.md` on ratification, and it is **operatively canon**: two normative-
vocabulary entries in `GLOSSARY.md:12-16` cite it (one by section number), and `README.md:89` lists
it under **Protocols**, marked **NEW**.

The real cap is **age and adoption**: the file is 3 days old and has **zero** adopters among the
artifacts it governs. It is a live inconsistency, not a shipped harm — hence MED, not HIGH.

#### Remedy FORKS three ways — routed, not self-applied

| arm | change | cost |
|---|---|---|
| **A** | Amend `$defs.reputation_delta` (add `class`, keep `additionalProperties:false`) and add the row to the target's Field Definitions + Complete Schema | amends a **published** schema and a frozen core-spec; must also reach the embedded copy in `schema_registry.json` and the reference SDK, or arm A creates C350-N1's mechanism |
| **B** | Narrow `interface-planes.md:109` — scope the MUST to plane-E-adjacent records rather than "every reputation-bearing signal" | narrows a 3-day-old clause whose author chose the wide phrasing deliberately (*"fail-closed in the direction that matters"*, `:112-114`) |
| **C** | Declare the classification an out-of-band property (a ledger-event field, not a delta field) — which is what the hub actually does with `applied` | contradicts `r6.rs`'s own stated design (*"The class rides the delta so the scoring side can never conflate the two"*, `:257-258`) |

**Owners (jointly, as with C392-N1):** the standard editor (target + `interface-planes.md`), the
`r7-action` schema owner, and the `web4-core`/hub owner. **Do not self-resolve.**

---

### C.2 — **C432-N2 (LOW-MED, routes with N1)** — the spec's fail-closed default collides with its own preceding bullet

`interface-planes.md:110` says an unclassified signal **MUST** default to *"the non-conduct class"*.

**The key is undefined.** `git grep -n 'non-conduct' -- . ':!docs/audits' ':!web4-standard/docs/audits'`
returns **1** hit: its own definition site. No section enumerates the classification's value set.

Two readings, and they are not equivalent:

- **Binary reading** (the definite article, and §4's own phrasing *"conduct from infrastructure"*):
  there are two classes, so *the* non-conduct class is **infrastructure**.
- **Complement reading**: any class that is not conduct qualifies. The only implementer's default —
  `DeltaClass::Unclassified`, documented at `r6.rs:258-261` as *"held — recorded, surfaced for
  review, never applied to tensors"* — trivially satisfies this.

**This pass does not assert an implementer violation.** Which reading governs is undecidable from
the artifacts, and under the complement reading `web4-core` conforms. The charge is **spec-internal**
and holds under the binary reading alone:

> `:107` — *"Plane E records **MUST NOT** enter the witness chain (D)…"*
> `:110` — an unclassified signal **MUST** default to the infrastructure class.

Under the binary reading, `:110` manufactures plane-E-classed records out of every under-specified
signal, and `:107` then bars exactly those records from the chain. The two clauses are three lines
apart and pull in opposite directions.

That collision is **live in the only implementation**, and not as a defect it chose: every delta is
witnessed to the chain regardless of class —

```
hub/hub-daemon/src/rest.rs:4149   witness_event(s, HubEvent::ReputationRecorded { delta, applied })
hub/hub-lib/src/events.rs:520-531 ReputationRecorded { delta, applied }
hub/hub-lib/src/state.rs:885-912  folds only Conduct; Infra and Unclassified are counted, held, and chained
```

An `Infra`-classed `ReputationDelta` therefore enters the hash-chained record with `applied = false`.
It produces no reputation *effect* (so `:107`'s second half holds) but it does *enter the chain* (so
`:107`'s first half does not) — **if** an Infra-classed reputation delta is a "Plane E record".
`interface-planes.md` gives no test for that, which is the same undefined-key defect one rung up.

**Severity capped at LOW-MED**: latent on the tensor side under both readings — nothing scores. The
divergence is about what the **witness record asserts**, which is precisely the fact plane
`interface-planes.md` §4 exists to protect: recording *"an infrastructure condition occurred"* when
all that is known is *"nobody classified this"* is a different falsehood from recording nothing, and
plane D is where it becomes permanent.

**Routes with N1**, same three owners.

---

### C.3 — **C432-N3 (LOW, instrument — routed to the `interface-planes.md` owner)** — the conformance list is a denominator, and two normative sections fall outside it

§8 opens *"An implementation conforms to this specification when:"* followed by six items. That is a
sufficient-condition claim, so it is checkable arithmetic (v80).

**Denominator, recounted independently by two parties and agreed at 26** (all-caps bolded
MUST/MUST NOT/REQUIRED, Notation section excluded):

| section | count | lines |
|---|---|---|
| §2 The two axes | 3 | `:51`, `:52`, `:64` |
| §3 Non-substitution | 9 | `:79`, `:82`–`:87`, `:90`×2 |
| §4 Telemetry as a plane | 5 | `:105`, `:107`×2, `:109`, `:110` |
| §5 Exposure is evidence | 4 | `:119`, `:124`, `:126`, `:128` |
| §6 Describing a surface | 3 | `:150`, `:157`, `:160` |
| §7 Relationship to the membrane | 2 | `:167`, `:170` |
| **total** | **26** | — |

**Disclosure:** `:150` is a descriptive back-reference to §3's rule (*"Those are the two planes §3
puts a MUST NOT between"*), not a fresh clause. Publish as **25 fresh + 1 reference**. No unbolded
normative keywords exist in the file.

**Item → section mapping:**

| §8 item | cites | reaches |
|---|---|---|
| 1 | *(no section citation)* | §6 `:133-134` — which is a **SHOULD** (*"specifications and implementations **SHOULD** state the pair explicitly"*), upgraded here to a conformance requirement |
| 2 | §2.1 | `:51`, `:52` |
| 3 | §3 | `:79`–`:90` |
| 4 | §4 | reproduces bullets 1–2 (`:105`, `:107`×2) |
| 5 | §5 | `:119`, `:126` |
| 6 | §6 | `:160` |

**Two gaps:**

1. **§7 is named by no item.** Its two MUSTs (`:167` *"MUST NOT infer a plane from the transport"*,
   `:170` *"MUST be determined by the surface it addresses"*) are outside every conformance
   criterion.
2. **§2.2 is named by no item.** `:64` — *"Every surface **MUST** declare exactly one exposure
   class"* — is reached by item 1 only if item 1's undocumented *"documented with its (plane,
   exposure) pair"* is read as implying it.

And **within §4, item 4's text omits bullet 3** — `:109` and `:110`, the two clauses this pass's N1
and N2 are about. An implementation can satisfy all six items while carrying no classification at
all. **The strongest normative clause `interface-planes.md` aims at reputation is the one its own
conformance section cannot see.**

---

### C.4 — **C432-N4 (INFO, instrument — this ledger)** — a mirror set that contracts loses the file where the motion happens

`web4-core/src/r6.rs` and `web4-trust-core/src/bindings/wasm.rs` were **both** rows in C312's mirror
table (`docs/audits/C312-reputation-computation-8th-delta-2026-08-04.md:90-91`, with a recorded path
correction for `wasm.rs`). Then:

| pass | `r6.rs` in the swept set? | `wasm.rs`? |
|---|---|---|
| C312 (8th) | **yes**, mirror row | **yes**, mirror row |
| C352 (9th) | no | survives only as a citation-rooting note (`:269`), not a mirror row |
| C392 (10th) | no | **no** — `grep -c wasm` = **0** |
| C432 (this pass) | **restored** | **restored** |

The consequence is measurable, not hypothetical. `91c1c333` landed in `web4-core/src/r6.rs` on
**2026-08-13**. C392 ran on **2026-08-15**, two days later, with the file outside its swept set, and
recorded *"0 of the 28 window commits touch any of them"* — true of the seven artifacts it had, and
blind to the eighth it used to have. `web4-core` appears in C392 exactly once, as the *third tree of
a grep* for a different token (`C392:120`).

The pointer was even published on the same day, by a **different lineage**:
`docs/audits/C382-web4-lct-9th-delta-2026-08-13.md:53-54` inspected `91c1c333`, correctly ruled it
out of *its own* subject matter, and named it in plain words — *"the addition is `DeltaClass
{Conduct, Infra, Unclassified}` plus a `class` field on `ReputationDelta` — reputation-delta
classification, no LCT structural content."* That sentence is this pass's N1, written nine days
early, in a document with no route to this lineage.

**Two distinct instrument failures, and they compound:**
1. **Contraction** (v-carry `mirror_set_contracted`): a mirror dropped without a stated reason
   silently narrows every subsequent window.
2. **A per-lineage window has no inbox.** A finding correctly dispositioned as out-of-scope by
   lineage X is not thereby routed to lineage Y. C382 did everything right and the information still
   sat for nine days.

**Not routed outward** — recorded in this ledger and in the per-file guards, where the next pass
reads it.

### C.5 — B-D1's second datapoint (INFO, **do not self-resolve**)

`interface-planes.md` §9 *"Relationship to other specifications"* names six sibling specs;
`grep -n 'reputation-computation' web4-standard/core-spec/interface-planes.md` → **empty**, although
§4 and §8-item-4 both constrain reputation. So the MUST has **no inbound path** to the artifact it
governs, in either direction.

This shape is **not novel and is not re-derived here**:
`docs/audits/C424-mcp-protocol-10th-delta-2026-08-21.md:34-46` charged exactly it — one day earlier,
for `mcp-protocol.md`, on the same file — and filed it as corroboration of the standing **B-D1**
SSOT-inversion carry, leaving a forward guard at `:384-387`: *"Report either way; do not
self-resolve (B-D1 is operator-unanswered)."*

**Recorded here as B-D1's second datapoint on `interface-planes.md`, and honoured as instructed.**

---

## §D — Guard discharge

| guard (from C392 §K) | discharge |
|---|---|
| **(1)** if C392-N1 was answered, check WHICH ARM | **not answered.** Target and schema both byte-frozen; no arm taken; §5's `:572` accuracy-vocabulary gloss unswept because there is nothing to sweep it against. |
| **(2)** `quality_score` is a tracked token — still unread at C432 ⇒ the *instrument* is the finding (v55) | **discharged, see D.1** |
| **(3)** C392-N3 will be at 4 consecutive passes — report against the receiver's LEDGER, stop re-charging | **honoured** — reported in §A, not re-charged. |
| **(4)** §7 is a discharged null | **not re-run.** `ReputationStore` unmoved. |
| **(5)** the 13 orphans are the residue's live edge — open one, but not the same one | **discharged, see D.2** |
| **(6)** re-derive the lineage count (expect 14) | **14**, re-derived. |

### D.1 — Guard 2: `quality_score` still has zero readers, and there is a **fifth** placement

Bounded to C392's own denominator (`web4-standard/`, `hub/`, `web4-core/`):

```
git grep -n 'quality_score' -- web4-standard hub web4-core     → 7 hits
```

Of those, **3 are the ATP-domain plural `quality_scores`** (`test_atp.py:690`,
`test_vectors.py:356`, `validate_vectors.py:385`, all reading
`test-vectors/atp/transfer-operations.json:290`) — a different concept, and the reason a naive count
of this token overstates. The R7-sense singular resolves at **3 publishing sites, 0 readers**:

| site | placement |
|---|---|
| `test-vectors/schema-validation/r7-action-jsonld-validation.json:121` | `result.output.quality_score` (C392's arm D) |
| `R6_TENSOR_GUIDE.md:138` | `result.metrics.quality_score` (C392's fourth placement) |
| **`protocols/web4-r6-framework.md:130`** | **`result.performance.quality_score`** — a **fifth** placement, not previously named |

**Guard 2 fires as C392 predicted**: the token is still read by nothing, and the placement count
grew by one while the readership stayed at zero. Corroborates C392-N1's class without being
separately charged (v60: the evidence is recorded, the row is not re-filed).

### D.2 — Guard 5: one orphan opened, and it is a second executed vector set

Opened `web4-standard/test-vectors/r6/action-operations.json` (109 L) — an orphan from C392-N4's
enumeration of 13, and **not** the one C392 opened.

It is **executed**: `implementation/sdk/tests/test_r6.py:665-670` loads it, and `r6-002`/`r6-003`
drive `compute_reputation`. Its quality signal sits at a bare top-level `input.quality` (`:34`,
`:57`) — the scalar convention C392 identified for `r7-rep-001`, in which `result.output` is never
consulted at all.

So the corpus now has **two** executed vector sets bearing on C392-N1, and **neither can
distinguish its two reads** — for the same structural reason: both bypass `result.output`. That
strengthens C392-N2 without re-charging it, and it is stated here rather than folded into a fresh
finding.

---

## §E — Own errors

**Seven own errors this pass. Three substantive.** All nine cells the policy reviewer challenged were
independently re-verified by me before adoption (v52 — verify the reviewer's corrections too);
where the reviewer was right, the correction is folded above rather than footnoted.

| # | error | how caught | substantive? |
|---|---|---|---|
| 1 | Cited the field table as *"the §3 field table"*. **§3 is "Value Tensor (V3) Dimensions" (`:161`)**; the field table is `### Field Definitions` at `:66-87`, inside §1. Copied loosely from C312's phrasing instead of resolving it. | policy review; verified by `grep -n '^## \|^### '` | **yes** — a wrong section number in a spec charge |
| 2 | Cited `r6.rs:252-278` for enum *and* field. The field is at `:294-299`; `:252-277` is comment + enum + `impl Default`. | policy review; verified by `sed` | **yes** — an unreadable cite |
| 3 | Built a synthetic `reputation_delta` for the exhibit when the corpus ships **CI-run** vectors that carry the member. The synthetic control also failed first pass on a guessed `TensorDelta` shape (`from_value`/`to_value` vs the schema's `from`/`to`) — a guessed shape I would have published as a control. | policy review supplied `/valid/1`+`/valid/5`; verified both | **yes** — a weaker instrument and a near-published guess |
| 4 | Based N1's severity cap on the word `proposed`. **21 of 31 core-spec files carry no status line at all**, including the target — the word does not distinguish it. | policy review; verified by 31-file census | no (conclusion unchanged, basis replaced) |
| 5 | Drafted N2 asserting an implementer violation. Undecidable — *"**the** non-conduct class"* admits a complement reading under which `Unclassified` conforms. | policy review | no (charge re-based on the spec-internal collision, which is stronger) |
| 6 | Drafted the §9 omission as a novel sub-cell of N1. `C424:34-46` charged the shape **one day earlier** and left an explicit forward guard. | policy review; verified by reading C424 | no (routed to B-D1 as its second datapoint) |
| 7 | Cited §8 item 1's referent as `interface-planes.md:145` — that is a table row. The SHOULD is at `:133-134`. | **caught only by re-executing §E's own rooting pass**, after the reviewer had signed off | no (a line cite, corrected in place) |

**Policy review = 13th consecutive falsification of load-bearing cells.** It also *strengthened* two
findings rather than only trimming them: it supplied the CI-run control (N1) and it found the second
dropped mirror (N4).

### E.1 — Citation rooting

Every path token in this document was resolved as written before it was cited (standing rule).
`r6.py` resolves twice in-tree (`web4-standard/implementation/sdk/web4/r6.py`, `simulations/r6.py`)
and `archive/game-prototype/engine/r6.py` a third time — every cite here is tree-prefixed.
`r7-action-jsonld.schema.json` resolves twice (`web4-standard/schemas/`, and the embedded copy in
`implementation/sdk/web4/schema_registry.json`); **both were parsed, and for `$defs.reputation_delta`
they are byte-identical** — the embedded copy does not diverge, so no second charge exists.
`wasm.rs` is `web4-trust-core/src/bindings/wasm.rs`, **not** `web4-core/src/wasm.rs` (C312's path
correction, honoured).

### E.2 — v60: the evidence names two fields, and only one was charged

N1's charge is `class`. **`sovereign_strength` is forbidden by the same
`additionalProperties:false`, present on the same Rust struct, and worse off**: it has **no canon
MUST anywhere**, and `git grep -ln 'sovereign_strength\|SovereignStrength' -- ':!docs/audits'`
returns **5 files with zero under `web4-standard/`** (`CHANGELOG.md`, one forum post,
`hub/hub-daemon/src/rest.rs`, `hub/hub-lib/src/state.rs`, `web4-core/src/r6.rs`).

That is **C194-N1**, still open and still pointing the way it was filed. It is not re-filed here; it
is recorded that the divergence N1 charges is **two fields wide**, so an arm-A remedy that adds only
`class` leaves the schema still unable to express a serialized `web4-core` delta. Arm A must be
scoped to both fields or it is a partial application — C312-N1's exact warning, one field over.

---

## §F — Deferral row (the instrument for C472) — v25

Pre-registered, so the next pass measures rather than re-derives.

1. **C432-N1's fork**: check **which arm** was taken before anything else. Arm A must reach **four**
   sites — the target's Complete Schema *and* Field Definitions, `schemas/r7-action-jsonld.schema.json`,
   the embedded copy in `implementation/sdk/web4/schema_registry.json`, and the Python SDK — **and**
   both fields (`class` *and* `sovereign_strength`, §E.2). A schema fix that skips the embedded copy
   or the context is C350-N1's mechanism. Arm B is a one-line narrowing of `interface-planes.md:109`
   and will look like a no-op in a `--stat`; grep the clause text, not the file.
2. **Do NOT re-run**: §7 (discharged null, C392-N4 — unless `ReputationStore` moves); C392-N3's
   `$defs.witness_attestation` fork as a *charge* (report against the receiver's ledger only — it
   will be at 5 consecutive passes); the `proposed`-status severity argument (retired at §C.1, the
   31-file census is the standing denominator); the synthetic `reputation_delta` control (retired —
   use `/valid/1` and `/valid/5`).
3. **`quality_score` is now a 3-site, 0-reader token** (D.1). If a reader appears, C392-N1's arm D
   changes shape. If a **sixth** placement appears, the instrument finding hardens: five placements
   and no reader is no longer an oversight.
4. **The mirror set for C472 is NINE**: the seven C392 artifacts **plus** `web4-core/src/r6.rs`
   **plus** `web4-trust-core/src/bindings/wasm.rs`. Do not contract it again; if a mirror is dropped,
   **state the reason in the table** (§C.4).
5. **`interface-planes.md` is now in this file's swept set** — it is 3 days old, it carries two MUSTs
   about reputation, and it is the only in-window artifact that bears on the target. Check whether it
   gained a `reputation-computation` citation (closes §C.5) or an adopter (closes N1's zero-adopter
   cap).
6. **Orphans**: 11 of C392's 13 remain unopened (`R6_TENSOR_GUIDE.md` by C392,
   `test-vectors/r6/action-operations.json` by this pass; `T3V3_PRIVACY_GOVERNANCE.md` was opened by
   C430 in another lineage — treat it as spent). Open one, not the same one.
7. **Standing and unanswered**: C392-N1 (2 windows), C312-N1 (two full rotation cycles), C352-N1/-N2,
   C194-N1, B-D1. None was answered this window. If C392-N1 is still unanswered at C472 that is a
   **third** window and the routing itself is the finding.

---

## §G — Numbers

lineage **14** · target frozen **35 d**, blob `bfdac3ba`, 870 L · window **46 / 28 non-audit / 1
`web4-standard/`** · mirrors frozen **7 of 7**, mirror set corrected to **9** · schema `$defs.reputation_delta`
**14 props, `additionalProperties:false`** · exhibit **2 controls at 0 errors, 3 arms at 1 error each** ·
`interface-planes.md` **196 L, 26 normative clauses (25 fresh + 1 reference), 6 conformance items,
2 sections uncovered** · core-spec status census **31 files, 10 with a status line, 21 without** ·
`non-conduct` **1 corpus hit** · `DeltaClass` **2 trees, 5 files** · `sovereign_strength` **5 files,
0 under `web4-standard/`** · `quality_score` (R7 sense) **3 sites, 0 readers** · orphans **11 of 13
unopened** · own errors **7, 3 substantive** · ZERO mutation.

---

## §H — Accountability self-audit

```
surface: docs/audits/C432-reputation-computation-11th-delta-2026-08-22.md   act: none (audit record only)
S: low/reversible [construct: doc-only, ZERO mutation outside docs/audits/]
R: n/a [construct: no caller-authorized path created]   W: n/a [construct: no identity-bearing act]
O: n/a [construct: no side effect to order]   A: pass [construct: findings carry the commands that produced them; §E records own errors]
V: n/a [construct: no irreversible act; all forking remedies ROUTED, not applied]
verdict: PASS
```
