# C310 — `core-spec/t3-v3-tensors.md`, 8th delta

**Date**: 2026-08-02
**Target**: `web4-standard/core-spec/t3-v3-tensors.md` — blob `32d3368e`, 689 lines
**Prior pass**: [C270](C270-t3-v3-tensors-7th-delta-2026-07-24.md) (PR #577), 2026-07-24
**Window**: `6d118ec6..60926fa7` (2026-07-24 → 2026-08-01), **78 commits**
**Lineage ordinal**: C42(1) C82(2) C121(3) C154(4) C192(5) C230(6) C270(7) → **C310 (8th)**
**Spec mutation this pass**: **ZERO** (by design — every finding below is routed)

---

## Verdict

The target is **byte-frozen** and **substantively clean against itself** for the 8th
consecutive pass. Every finding below lives in the artifacts the spec *cites* or the
artifacts that *implement* it — the mirror layer, not the prose.

| # | Severity | Class | Owner |
|---|---|---|---|
| **N1** | **MEDIUM** | adjudication of the routed **C278-N1** carry — six standard-internal artifacts + one live external emitter contradict the ratified note at `:429-435` | operator + spec author (**fork**, do not self-apply) |
| **N2** | **MEDIUM** | net-new — `01f410db` added `web4:observationCount` to the `.ttl` only; the standard's own JSON Schema **forbids** it | ontology owner + author |
| **N3** | **LOW** | net-new — 36 of 38 published cross-language vectors cite a context artifact that does not exist | SDK / build track |
| **N4** | **INFO** | net-new — the spec header names the JSON-LD context that the 2026-03-24 reconciliation retired for that purpose | spec author |

The window's only commit that can reach this target is **`01f410db`** — `web4-standard/`
took exactly **3** commits in 78 (`01f410db`, `954ee391` #580, `4665a430` #579), and
`git log 6d118ec6..HEAD -- web4-standard/implementation/sdk/ web4-core/ web4-trust-core/src/
web4-policy/src/` is **empty (0 commits)**. With the target frozen and every code mirror
frozen, this is precisely the configuration in which a false clean is most likely
(method carry v13). The findings came from widening the surface, not from the diff.

---

## §A — Carried anchors and findings, re-resolved at live HEAD

**Freeze proof (C282 §A-collapse warrant).** `git rev-parse HEAD:web4-standard/core-spec/t3-v3-tensors.md`
= `32d3368e…`, identical to the C270 snapshot; last content commit `d89595e8` (#531, 2026-07-16),
**17 days**. Findings from C42/C82/C121/C154/C192/C230 are therefore held **by construction**
against the target's own text and are not re-derived here. Budget went to §B and §B′.

### The six tracked anchors — all EXACT, none drifted

| Anchor | Line | Text at HEAD |
|---|---|---|
| §2.3 Talent-no-decay | `:125` | `- **Talent Stability**: No decay — Talent represents inherent capability and` |
| T3 composite weights | `:631` | `\| T3 composite weights \| talent=0.4, training=0.3, temperament=0.3 \| §9.2 \| t3v3-001 \|` |
| V3 composite weights | `:632` | `\| V3 composite weights \| valuation=0.3, veracity=0.35, validity=0.35 \| §3.3 \| t3v3-002 \|` |
| t3v3-012 | `:635` | `\| Talent no-decay \| Talent MUST NOT decay through inactivity \| §2.3 \| t3v3-012 \|` |
| §10.2 ATP conservation | `:642` | `\| ATP conservation \| total supply = ATP + ADP …` |
| §10.4 `0.995` anti-example | `:675` | `\| Talent decay/half-life \| "0.995 per period" \| Talent no-decay is a protocol invariant …` |
| §3.3 authoritative values | `:335` | `weights \`valuation=0.3, veracity=0.35, validity=0.35\` (the authoritative values are` |

### Carry-row survival (v10 — rows, not labels)

| Carry | C270 status | C310 status | Instrument re-run at HEAD |
|---|---|---|---|
| **C270-N1** successor merge gate anchored to the crate, not the spec | routed, MED | **STILL-OPEN, verbatim unchanged** | `web4-trust-core/README.md` still reads *"a DerivationSpec reproducing **this crate's** normative t3v3 vectors"*; `find web4-trust-core -name '*.json' -not -path '*/target/*'` → 1 hit, `pkg/package.json` (wasm-pack output), **zero vectors**; `grep -rn tensor-operations --include=*.rs . \| grep -v target` → **0**. The divergent path is live: `web4-trust-core/src/tensor/mod.rs:129-141` `t3_update_from_outcome` = `magnitude*0.05*(1.0-training)` on Training, `delta*0.5` Temperament, **`delta*0.3` Talent** — the spec's §10.2 t3v3-003/004 form is `0.02*(quality-0.5)` and does not rank Talent last. |
| **C270-N2** "cross-language test vectors enforce them" is unbacked | routed, MED | **STILL-OPEN** | 4 hand-written `t3v3-012` **comments** at `web4-trust-core/src/tensor/mod.rs:192`, `web4-trust-core/src/entity/trust.rs:668`, `web4-core/src/t3.rs:352` and `:534`. Rust files loading a vector file: **0**. No harness appeared in the window. |
| **C270-N3** pre-C-series `cross-language-t3v3-alignment` audit never entered the ledger | routed INFO → C168 memo | **STILL-OPEN** | status only; no new evidence sought this pass (per C270's own self-refutation of its #2/#3/#5 items). |
| **C192-N3** layer-split composite aggregation is INFO | precedent-bearing | **STANDS** | held by freeze; **not** re-raised (C270 DO-NOT list). |
| **C192-N4** | STANDS | **STANDS** | held by freeze. |
| **D1** ontology-vocabulary divergence (`web4:matchesTask`) | STILL-OPEN | **STILL-OPEN, unchanged** | `grep -rn matchesTask` (excl. `/target/`, `.git/`) → **2 live hits**: the target `:551` and the static Nova bundle `forum/nova/web4-sal-bundle/t3-v3-tensors.md:359`. Defining triple in any `.ttl`: **0**. **N2 below is a fresh instance of D1's class inside the window.** |
| **D2** X4 structural-duplication facet | open; NUMERIC facet retired | **unchanged** | the retired NUMERIC facet was **not** re-carried (C270 DO-NOT list honoured). |
| **D3** `web4-core` V3 clamps | STILL-OPEN | **STILL-OPEN, untouched** | `web4-core/src/v3.rs:137` `dimensions[i] = scores[i].clamp(0.0, 1.0)`; `:191` `self.dimensions[idx] = (before + delta).clamp(0.0, 1.0)`. |

**Row survival: 8 of 8 tracked rows re-resolved; 0 emptied, 0 inverted, 0 silently dropped.**
No carry changed direction this pass (contrast C304, where a 3-pass-old carry was inverted).

### Reviewer-flagged basis check (C308 → C19-M5) — re-measured live, not inherited

C308 recorded that `C19-M5` ("multi-device's 8 sub-dimensions are absent from the ontology")
had been held **by byte-identity** against `t3v3-ontology.ttl` — a basis `01f410db` invalidated.
Any t3-v3 carry resting on the same assumption was re-measured live rather than inherited:

`t3v3-ontology.ttl` at HEAD declares **exactly 6** `web4:Dimension` instances — `web4:Talent`
`:41`, `Training` `:44`, `Temperament` `:47`, `Valuation` `:52`, `Veracity` `:55`, `Validity`
`:58`. Every sub-dimension in the file is **commented out** (`# med:SurgicalPrecision …` `:157-172`).
**C19-M5's status holds on a live measurement, not on byte-identity.** `01f410db` added a class
and a property; it added no dimension.

---

## §B — N1: adjudication of the routed **C278-N1** carry

> Filed as an **adjudication of C278-N1, not as a net-new C310 finding.** A carry crossing a
> lineage boundary gains **reach, not truth** ([[feedback_carry_gains_reach_not_truth]]).
> C278 (mrh 7th delta, 2026-07-28 §N1) machine-verified the ontology widening, recorded that
> **mrh owes no edit**, and routed adjudication to *"the t3-v3 audit lineage + the ontology
> owner."* This is the first t3-v3 pass since. C278-**N2** is status-checked only (it is routed
> to the operator DESIGN-Q memo as a D1 refresh) and is **not** re-filed here.

### The note under adjudication

`web4-standard/core-spec/t3-v3-tensors.md:429-435`, §5.2, ratified as the **C42-M3 remediation**
(option (c), adopted 2026-06-09):

> **Note on V3 entity-role binding:** The ontology (`t3v3-ontology.ttl`) declares
> `web4:entity` and `web4:role` with domain `web4:T3Tensor` **only**. V3 tensors derive their
> entity-role context from the co-located T3Tensor for the same entity-role pair, **rather than
> carrying independent `web4:entity`/`web4:role` properties**. This avoids domain violations in
> RDF validators while preserving the §1.1 principle that both T3 and V3 are role-contextual.

Per the review's binding condition 2 the note is adjudicated as **two separable clauses**.

### Clause 1 — the factual premise. **FALSE at HEAD.** Machine-checkable, single-line.

`web4-standard/ontology/t3v3-ontology.ttl` at HEAD:

```
:25  web4:Tensor a rdfs:Class ;
:29    rdfs:subClassOf web4:Tensor ;      # on web4:T3Tensor
:33    rdfs:subClassOf web4:Tensor ;      # on web4:V3Tensor
:68  ### Tensor Binding Properties (shared by T3Tensor and V3Tensor via web4:Tensor)
:71    rdfs:domain web4:Tensor ;          # web4:entity
:76    rdfs:domain web4:Tensor ;          # web4:role
:81    rdfs:domain web4:Tensor ;          # web4:hasDimensionScore
```

The properties are no longer declared on `web4:T3Tensor` at all, let alone "only". Authored by
**dp-web4** in `01f410db` (2026-07-28, closes #581) — **four days after C270**, and only the
**second content commit to that file in the project's history**.

### Clause 2 — the design rule. **Contradicted by five further standard-internal artifacts**, four of which predate the note itself.

This is the emitter measurement the review required (condition 3): not prose against prose.

| # | Artifact | Anchor | Since | What it does |
|---|---|---|---|---|
| 1 | `web4-standard/ontology/t3v3-ontology.ttl` | `:25-33`, `:71-81` | 2026-07-28 `01f410db` | Makes independent `web4:entity`/`web4:role` on a V3Tensor **legal**. The commit's stated rationale is *"a correct projection emits them on V3Tensor nodes too"* — the direct negation of the rule. |
| 2 | `web4-standard/schemas/t3v3-jsonld.schema.json` | `:155-161` | 2026-03-22 `5069661f` (#54) | `$defs.V3Tensor.properties.entity` — description **"LCT entity ID this tensor measures (web4:entity)"**; `.role` — **"Role context for this tensor (web4:role)"**. Names the ontology property explicitly. |
| 3 | `web4-standard/test-vectors/schema-validation/t3v3-jsonld-validation.json` | `:176`, vector **`v3-valid-003`** | 2026-03-22 `82e59bfc` (#67) | *"V3Tensor at maximum with entity and role"*, in the **`valid`** array of a suite whose `meta.description` reads *"Each 'valid' document **MUST** pass validation"* and whose `meta.spec_reference` is **`t3v3-ontology.ttl`**. The standard **requires** cross-language implementers to accept the configuration the note forbids. |
| 4 | `web4-standard/schemas/contexts/v3.jsonld` | `:14-15` | 2026-03-24 `936c2d92` (#76) | A JSON-LD context **specifically for V3 documents** mapping `entity` → `web4:entity`, `role` → `web4:role`. |
| 5 | `web4-standard/implementation/sdk/web4/trust.py` | `:336-364` | 2026-03-24 `936c2d92` (#76) | `V3.to_jsonld(entity=…, role=…)` emits `doc["entity"]`/`doc["role"]`. Docstring: *"Serialize to JSON-LD **per t3v3-ontology.ttl**"*, arg doc: *"Optional LCT entity ID (**web4:entity binding**)"*. |
| 5b | `sdk/tests/test_t3v3_jsonld.py` | `:254-262`, `:413-414` | same | `test_entity_binding` / `test_role_binding` in the **V3** class; `test_v3_with_entity_role_valid` schema-validates it. **77 tests pass at HEAD.** |
| 6 | **`hestia`** (external implementer) | — | pre-`01f410db` | Not in this repo, but it is `01f410db`'s **stated driver**: *"a correct projection emits them on V3Tensor nodes too → RDFS domain entailment inferred every V3Tensor to also be a T3Tensor"*, arising from *"hestia PR #84's trust-RDF projection"*. A **live** emitter of independent `web4:entity`/`web4:role` on V3 nodes, in the **ontology namespace** — the configuration the note says does not occur. |

**Machine check, run at HEAD** (`jsonschema` Draft 2020-12, against the standard's own schema):

```
V3(0.8,0.7,0.6).to_jsonld(entity="lct:web4:carol", role="web4:Auditor")
  → {"@context":["https://web4.io/contexts/v3.jsonld"], "@type":"V3Tensor",
     "valuation":0.8, …, "entity":"lct:web4:carol", "role":"web4:Auditor"}
  → validates against schemas/t3v3-jsonld.schema.json : PASS
```

Six standard-internal artifacts, plus one live external emitter, against one prose note.

**A check the commit could not run, run here.** `01f410db`'s message records: *"pytest unavailable
on box so the python SDK suite wasn't run — change is vocabulary-only + widening."* Run at HEAD on
this host: `pytest tests/test_t3v3_jsonld.py -q` → **77 passed**. The widening claim holds against
the SDK suite; nothing regressed. That is reported here because the commit explicitly left it open.

### §C — adversarial refutation of N1, before filing

**R1 — "Namespace layering defeats it."** The strongest counter, and it **partially succeeds**.
`schemas/contexts/v3.jsonld:4` declares `"web4": "https://web4.io/ns/"`, while
`t3v3-ontology.ttl:1` declares `@prefix web4: <https://web4.io/ontology#>`. So the SDK's V3
`entity` expands to `https://web4.io/ns/entity`, **not** the `https://web4.io/ontology#entity`
the note names. This split is **ratified design**, not drift —
`docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md` (2026-03-24, Status: Decided)
assigns `ontology#` to OWL/RDF and `ns/` to application serialization, and the split is
**systematic**: **10 of 10** files in `schemas/contexts/` use `ns/`; every file in `ontology/`
uses `ontology#`. Charging the namespace split as a defect would be resurrecting a ratified
decision, and is **not** filed.

**N1 survives R1 on three legs that are namespace-free or ontology-layer:**
(a) artifact **1** is *in the ontology layer itself*, operator-authored, same namespace as the note
— by itself it kills clause 1 outright and states the negation of clause 2;
(b) artifact **2** is namespace-free JSON Schema whose own descriptions bind the JSON keys to
`web4:entity`/`web4:role` by name;
(c) artifact **3** declares `t3v3-ontology.ttl` as its `spec_reference` — the vectors nominate the
ontology as their referent and then publish `v3-valid-003` as MUST-pass.
What R1 *does* do is bound severity: at the IRI level nothing currently mis-joins because of the
note, so this is a **consistency defect in a ratified normative note**, not a live failure.

**R2 — "The widening removed the *enforcement*; the rule may still be intact."** This is the
reading the review required be tested, and it **does not survive**: a rule is not intact when the
standard's own conformance suite obliges implementers to accept its violation (`v3-valid-003`)
and the reference implementation ships the violating emitter with tests. Separately, the note's
**sole stated justification** — *"This avoids domain violations in RDF validators"* — is now void:
after the widening there is no domain violation to avoid.

**R3 — "This is a resurrection of C42-M3."** No. C42-M3 was *"ontology domain gap — V3Tensor
binding properties undefined"*, disposed **HELD-REMEDIATED**. This finding does not re-raise the
gap; it reports that the **remedy chosen for it** is falsified. Distinct claim — the
remediation-introduced-regression class at one hop (born C36), as C278 also classed it.

**R4 — snapshot-presence guard.** Was this already present at C270? **Split answer, stated
plainly**: artifacts 2-5 predate the note by ~11 weeks — so the note was born
**already contradicted by four artifacts inside the standard**, and seven t3-v3 passes never
checked it against the standard's own schema, vectors or contexts. Artifact 1 is genuinely
in-window. Therefore **net-new as a FINDING, not as a FACT** (C280-N1 precedent), and the
lineage's own blind spot is part of the finding.

### Disposition — **FORK, routed. No spec edit. No `.ttl` edit.**

Both options are coherent; picking one is a spec decision with a named owner, not maintenance:

- **Option A — amend the note.** Delete or rewrite `:429-435` to state that V3 tensors **may**
  carry independent `web4:entity`/`web4:role` (per `01f410db`), keeping the §1.1
  role-contextuality point. Cheap; matches all six artifacts; reverses a ratified C42-M3 remedy.
- **Option B — re-justify and enforce the rule.** Keep co-located derivation as the normative
  rule on a *new* justification (the old one is void), and then make the standard match: retire
  `v3-valid-003`, drop `entity`/`role` from `$defs.V3Tensor`, remove them from
  `schemas/contexts/v3.jsonld`, and remove the `entity`/`role` kwargs from `V3.to_jsonld()`.
  Coherent, but it is a breaking change to a published conformance vector **and** a shipped SDK
  API — and it would additionally require `01f410db` to be reverted and hestia's shipped
  projection to change, i.e. it re-creates the exact RDFS entailment bug (#581) that the operator
  fixed. The auditor notes the asymmetry without deciding: **Option A is cheap and consistent;
  Option B costs a revert of an operator fix plus an external implementer's migration.**

The auditor states the **direction** — the evidence indicts the **note**, not the ontology — and
**does not choose the remedy**. `01f410db` is an operator-authored commit; an auditor must not
edit its consequences into a ratified sibling spec (BC-C23-3; C278 refused the same edit on the
mrh side).

---

## §B (cont.) — N2 (MEDIUM, net-new): `01f410db` reached the `.ttl` and nothing else, and the standard's own schema *forbids* the property it added

`01f410db` added, at `t3v3-ontology.ttl:107-111`:

```turtle
web4:observationCount a rdf:Property ;
  rdfs:domain web4:DimensionScore ;
  rdfs:range xsd:integer ;
  rdfs:comment "Number of witnessed observations backing this score. Load-bearing for
  sufficiency queries … a relying party weighs a score by its evidence, not just its value." .
```

Issue #581's stated purpose (quoted in C278 §N2) was to stop consumers *"inventing the predicate
[and producing] triples that parse, look plausible, and **join with nothing**."*

**Measured at HEAD — every JSON-LD face of this vocabulary lacks the term:**

| Artifact | Defines `observationCount`? | `observation_count`? |
|---|---|---|
| `web4-standard/ontology/t3v3.jsonld` (**named in the target's header `:4`**) | **No** | No |
| `web4-standard/schemas/contexts/t3.jsonld` | **No** | No |
| `web4-standard/schemas/contexts/v3.jsonld` | **No** | No |
| `web4-standard/schemas/t3v3-jsonld.schema.json` `$defs.DimensionScore` | **No** — and `"additionalProperties": false` | No |

Both casings swept (v11 casing rider); the zero is stated per artifact, not as a single blanket.

**The schema does not merely omit it — it rejects it.** Machine check at HEAD, validated against
the `V3Tensor` `$def` directly so the top-level `oneOf` cannot mask the cause (the C306 lesson
that N identically-shaped failures can be the verifier, not the artifact):

```
PATH ['dimension_scores', 0] | VALIDATOR additionalProperties
  | Additional properties are not allowed ('observationCount' was unexpected)
```
…and identically for `observation_count`.

So a JSON-LD consumer of the standard **still** has to invent the predicate, and if they emit it
in a document their implementation is required to schema-validate, **validation fails**. The
remediation reached the OWL layer and stopped there. This is a fresh, in-window instance of
**D1's** class — vocabulary that one layer of the standard defines and another cannot express.

**In-repo emitters of the RDF predicate: zero.** `grep -rn "observationCount"` over the whole tree
excluding `/target/`, `.git/` and `docs/audits/` returns exactly **2** hits, neither an emitter:
the definition at `t3v3-ontology.ttl:107`, and a prose watch-note at
`whitepaper/PUBLISHER_CONTEXT.md:274`. The `observation_count` hits in `web4-core/src/t3.rs` /
`v3.rs` and `web4-trust-core/src/entity/trust.rs` are **Rust struct fields**, not RDF — they carry
the same *concept* (and derive a confidence weight `ln(1+n)/ln(10)` from it) but never surface as
a triple.

**Severity bounded honestly at MEDIUM, for two reasons.** (i) Nothing is broken today: no in-repo
artifact emits the predicate, so nothing currently hits the schema's rejection. (ii) The commit
message names the intended consumer and its migration path — *"hestia had to emit it under a local
`hestia:` namespace where it joins with nothing … hestia can now migrate `hestia:observationCount`
→ `web4:observationCount` on its own track"* — and hestia is a **Turtle/RDF** emitter, so its
migration is unblocked by the `.ttl` alone. The gap is real but it is **JSON-LD-specific**: it
lands on any consumer using the standard's published contexts and schema, which is the layer the
SDK and every cross-language implementer live in. `01f410db` also self-describes as *"Piece 1 of
projecting the trust ontology to the hub's society MRH"* — a multi-piece track, so the
serialization half may already be planned. This is filed so that it is planned **on the record**
rather than assumed.

**Refutations run.** *"An optional property's absence from a context isn't a defect"* — true in
general, and it is why this is not HIGH; but `additionalProperties: false` converts absence into
prohibition, which is a different fact. *"Maybe the schema's `DimensionScore` isn't the JSON face
of the ontology's `web4:DimensionScore`"* — refuted: its own property descriptions read
"`(web4:observedAt)`" and "`(web4:witnessedBy)`", the same class, the same properties.

**Disposition — routed** to the ontology owner + spec author. The remedy spans a `.ttl`-adjacent
JSON-LD context, a JSON Schema, and possibly the vectors; **no autonomous TTL or schema drafting**
(BC-C23-3), and `01f410db` is operator-authored.

---

## §B (cont.) — N3 (LOW, net-new): 36 of 38 published cross-language vectors cite a context artifact that does not exist

`web4-standard/test-vectors/schema-validation/t3v3-jsonld-validation.json` (38 vectors: 10 valid,
28 invalid, `82e59bfc` 2026-03-22 #67). `@context` values across all 38 documents:

| Count | `@context` |
|---|---|
| **35** | `["https://web4.io/contexts/t3v3.jsonld"]` |
| **1** | `"https://web4.io/contexts/t3v3.jsonld"` (bare string, an intentional negative vector) |
| 1 | `null` (negative vector) |
| 1 | `[]` (negative vector) |

`web4-standard/schemas/contexts/t3v3.jsonld` **does not exist**. The SDK emits
`https://web4.io/contexts/t3.jsonld` and `.../v3.jsonld` (`trust.py:106-107`) — the files created
by the 2026-03-24 reconciliation, which explicitly **replaced** the single shared `t3v3` context.

**Baselined before filing** (a lone miss would be an idiom, not a defect). Mapping every
`https://web4.io/contexts/*.jsonld` constant in the SDK to a backing file in
`web4-standard/schemas/contexts/` — the convention the standard's **own** test asserts
(`test_t3v3_jsonld.py:469`, `:521` call `os.path.exists()` on exactly those paths):

```
acp · atp · attestation-envelope · capability · dictionary · entity · lct · r7-action · t3 · v3   → backing file YES  (9/11 … 10 names, 9 distinct modules)
trust-query.jsonld            → ** MISSING **   (emitted by trust.py:108)
t3v3.jsonld                   → ** MISSING **   (cited by 36/38 vectors)
```

**Nine of eleven hold the convention; both misses are in the T3/V3 lineage.** Not an idiom.

Why it has stayed invisible: the schema types `@context` as `{"type":"array","items":{"type":
"string","format":"uri"}}` and never dereferences it, so all 38 vectors pass and will keep
passing. The harness cannot see this class of error at all.

Related and recorded: `JSONLD-NAMESPACE-RECONCILIATION.md`'s **"Not Changed"** list asserts
*"Test vectors — use property names, not namespace URIs."* That is **false for this suite** — 36 of
38 vector documents carry a `@context` URI, and it is the pre-reconciliation name.

**Disposition — routed** to the SDK / build track. Two candidate fixes (add the missing context
files, or repoint the vectors at `t3.jsonld`/`v3.jsonld`) with different blast radii; not the
auditor's call, and no code was touched.

---

## §B (cont.) — N4 (INFO, net-new): the target's header names the JSON-LD context that the ratified reconciliation retired

`t3-v3-tensors.md:4`:

> **JSON-LD Context**: [`web4-standard/ontology/t3v3.jsonld`](../ontology/t3v3.jsonld)

Unqualified. But `JSONLD-NAMESPACE-RECONCILIATION.md` (2026-03-24, **Decided**) standardised
application-facing serialization on `schemas/contexts/*.jsonld` under `https://web4.io/ns/`, and
lists `ontology/t3v3.jsonld` under **"Not Changed … left in place for OWL tooling."** A reader
following the header serialises with `ontology#` IRIs; the SDK, the contexts and the other nine
core types serialise with `ns/` IRIs. The two graphs do not join — which is fine *by design*, but
the header never tells the reader which layer they are in.

**Measured**: core-spec files citing `schemas/contexts/` → **0 of all files under
`web4-standard/core-spec/`**. Core-spec files carrying a `JSON-LD Context` header line → **1**
(this target, `:4`). So there is no corpus idiom to fall back on; this target is the only
core-spec file that makes the claim at all.

Precedent for the fix shape already exists **in the same section**: §5.2 `:389-395` carries a
*"Vocabulary note"* telling the reader `web4:hasRole` lives in `web4-core-ontology.ttl` and *"a
processor resolving these triples must load the core ontology as well."* The same hygiene has
never been applied to the serialization layer.

**Disposition — routed** to the spec author as an INFO. Filed separately from N1 because it is a
different defect (a stale pointer, not a falsified rule) in a different line.

---

## §B′ — mirror set, derived in **both** citation directions (v14), with instruments

Every count below carries its scope and was **re-run after this document was written**, so that
this document's own text cannot inflate a corpus count (v-publish-the-instrument).
All greps exclude `/target/` and `.git/` unless stated.

### Direction 1 — artifacts the target **cites** (a spec's own citations are a mirror-set input)

| Artifact | In window? | Read by prior t3-v3 passes? | Result |
|---|---|---|---|
| `ontology/t3v3-ontology.ttl` (header `:3`) | **1 commit — `01f410db`** | yes (all 7) | **N1 clause 1, N2** |
| `ontology/t3v3.jsonld` (header `:4`) | 0 | named in C42/C82 reference lists; **never opened** | **N2, N4** |
| `ontology/web4-core-ontology.ttl` (§5.2 note) | 0 | yes | clean |
| `schemas/t3v3-jsonld.schema.json` | 0 | **0 of 7** | **N1 artifact 2, N2** |
| `schemas/t3v3.schema.json` | 0 | **0 of 7** | clean this pass |
| `schemas/contexts/t3.jsonld` | 0 | **0 of 7** | N2 |
| `schemas/contexts/v3.jsonld` | 0 | **0 of 7** | **N1 artifact 4, N2** |
| `test-vectors/t3v3/tensor-operations.json` | 0 | yes (C270-N2) | C270-N2 stands |
| `test-vectors/schema-validation/t3v3-jsonld-validation.json` | 0 | **0 of 7** | **N1 artifact 3, N3** |

**Five of nine artifacts the standard publishes for this spec had been read by zero of seven
prior passes.** Four of this pass's findings live in them. This is the same shape as C306
(6 ATP artifacts, 993 lines, 0/7) and C308 (mirror set under-derived by ~18 artifacts) — the
mirror set had been derived **outward only**, from the spec to its implementers, never inward
from the spec to the artifacts it names.

**One correction to the record C278 left.** C278 §N1 wrote of `01f410db` that *"no one has seen
this — `grep -rl "01f410db\|observationCount\|web4:Tensor" docs/` → empty."* That was true when
written; it is **no longer true**, and the exception is informative rather than a rebuttal.
`whitepaper/PUBLISHER_CONTEXT.md:274` carries a dated watch-note on the commit, correctly rules
that *"the paper … enumerates no RDF properties, so nothing contradicts"*, flags `observationCount`
as *"the evidence-sufficiency primitive behind the paper's 'computable from the record' claim"*,
and names 07-t3v3 / 10-composed-architecture as the surfaces to watch. So the one track scoped to
notice **did** notice, ruled its own surface unaffected — correctly — and had no mandate to check
`t3-v3-tensors.md:429-435`. The t3-v3 consequence stayed unowned for five days not because nobody
looked at the commit, but because **no track owned that particular seam**. That is the routing gap
this pass closes.

### Direction 2 — artifacts that **implement or cite** the target

`git log 6d118ec6..HEAD --` over `web4-standard/implementation/sdk/`, `web4-core/`,
`web4-trust-core/src/`, `web4-policy/src/` → **0 commits**. Every code mirror is byte-frozen for
the window; all C270 code-side carries therefore stand by construction and were additionally
re-measured live above.

`web4-trust-core/` took 2 window commits, both non-semantic: `44dc25db` (#600) un-gitignored
`Cargo.lock` for CI, plus the lockfile itself. **No `src/` change.** C270-N1's divergent arithmetic
is untouched.

### Negative gates — each states the tree searched and the token, per v9

| Gate | Scope searched | Token(s) | Result |
|---|---|---|---|
| `hub/` can reach t3-v3 | `git log 6d118ec6..HEAD -- hub/` = 32 commits | window diff for `t3v3\|T3Tensor\|V3Tensor\|observationCount` | **NEGATIVE** — hub's window work is law/registry/docs; no T3/V3 vocabulary added |
| `docs/specs/` | whole tree | `t3v3-ontology\|V3Tensor` | **NEGATIVE** |
| Operational tree (v13) | `web4-standard/deployment/` — **5 files**: `README.md`, `cron/web4-demurrage.cron`, `config/demurrage.{dev,example}.json`, `systemd/web4-demurrage.service` (there is **no** repo-root `deployment/`; the tree C306 audited lives under `web4-standard/`) | `t3v3\|T3Tensor\|V3Tensor\|observationCount` → **0 files**; `tensor` case-insensitive → **0 files** | **NEGATIVE** — the entire operational tree is ATP-demurrage; it neither installs nor serves a T3/V3 artifact |
| Nova static bundle | `forum/nova/web4-sal-bundle/t3-v3-tensors.md` (374 L) | — | **NOT a mirror** — static inbound proposal snapshot; known via the SAL lineage; carries the *pre*-`01f410db` text, so its 2 `web4:T3Tensor` hits are historical, not divergence |
| `simulations/` | — | — | **DECLINED on M2** by construction (unbounded surface), per C284 precedent |

### Idiom baselines run before filing (so a "novel" usage is not charged as a defect)

| Candidate charge | Baseline | Outcome |
|---|---|---|
| Two `web4:` namespace IRIs (`ns/` vs `ontology#`) is a defect | 10/10 `schemas/contexts/` use `ns/`; all `ontology/` use `ontology#`; **ratified** by `JSONLD-NAMESPACE-RECONCILIATION.md` 2026-03-24 | **NOT FILED** — ratified design |
| A context URL without a repo backing file is a defect | 9 of 11 SDK context URLs have one; the standard's own test asserts the mapping | **FILED as N3** — the 2 misses are both T3/V3 |
| `hub-law.ttl:1` uses a third variant `https://web4.io/ontology/` (trailing slash) | out of this target's subject matter | **NOT FILED** — noted for the hub-law/SAL lineage |

---

## §C — items deliberately **not** raised

Honouring the C270 per-file DO-NOT list verbatim (review condition 6) and the standing guards:

- **Composite-weights #2/#3** (crate names them `t3_average`/`v3_average`) — **INFO** by the
  C192-N3 precedent. Not re-raised, not re-severitised.
- **Decay-model #5, Training/Temperament half** — §10.3 society-configurable. **Not a defect.**
- **C238-N1 / D2 NUMERIC facet** — CONSUMED and verified dead at C270. **Not re-carried.**
- **"The spec names conformance vectors as authority but nothing consumes them"** — refuted at
  C272 for the sibling; C270-N2 already carries the accurate, narrower form (Rust side only).
- **C230 "+2 shift"** — consumed; `:631/:632/:635/:642/:675` above **are** the post-shift numbers.
- **The `ns/`-vs-`ontology#` split** — ratified (see §B′ baselines).
- **C278-N2** — routed to the operator DESIGN-Q memo as a D1 refresh; status-checked only, not
  re-filed here.

---

## Method notes for the next pass (~C350)

1. **Re-baseline from blob `32d3368e`.** If the target is still frozen, the delta again lives
   entirely in the cited-artifact layer — start there, not in the diff.
2. **The mirror set now includes, permanently**: `schemas/t3v3-jsonld.schema.json`,
   `schemas/t3v3.schema.json`, `schemas/contexts/t3.jsonld`, `schemas/contexts/v3.jsonld`,
   `test-vectors/schema-validation/t3v3-jsonld-validation.json`, `ontology/t3v3.jsonld`.
   Five of these had been read by **zero** of seven prior passes. Do not let the set contract (v8).
3. **Machine-validate the standard's published examples every pass.** N1 artifact 3 and N2 were
   both found by *running* the standard's own schema over the standard's own documents, not by
   reading them. `jsonschema` is available; `rdflib`/`pyld` are **not** installed on this host —
   the RDF-layer checks in this document are hand-derived from the cited `.ttl` lines and are
   labelled as such, never as machine checks.
4. **First question at C350**: did the operator pick option A or B on N1? If neither, N1 is a
   3-pass carry and its severity should be argued **both** ways (v-carry-gains-reach).
5. **`v3-valid-003` is now a tracked row.** If it is ever removed, that is option B being executed
   and N1 closes in the other direction — check the vector, not the note.

### Method carry **v15** — proposed, not asserted (operator to ratify)

Two rules, both born from how N1 and N4 were actually found. Neither is covered by v8-v14.

**(a) Date a remediation note against the artifacts it describes.** `:429-435` is not drift — it is
a *ratified remedy*, adopted 2026-06-09, that was **already contradicted by four artifacts inside
the same standard** on the day it was written (schema 03-22, vectors 03-22, context 03-24, SDK
03-24). Seven subsequent passes inherited it as settled precisely *because* it was labelled
remediated. The rule: when a carried finding's status is **HELD-REMEDIATED**, re-read the remedy
once against the artifacts it makes claims about, and compare dates. A remediation is a claim about
the corpus at a moment; it does not survive by being ratified. (Adjacent to but distinct from the
C36 remediation-introduced-regression class: there, a *later* commit reopens a closed finding; here
the remedy was **never true**.)

**(b) A spec's header pointers can be retired by a ratified design decision, and nothing checks
them.** N4 exists because `docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md`
(Status: Decided) retired `ontology/t3v3.jsonld` for application serialization while the target's
`:4` still names it, unqualified, as **the** JSON-LD Context. A freeze protects the header's bytes;
no test dereferences it; no lineage greps the decision record. The rule: for each artifact the
target's header or front-matter names, `grep docs/history/design_decisions/` for it before treating
the pointer as live. This is the header-level analogue of v14's "the spec's own citations are a
mirror-set input" — v14 says *read* what the spec cites; v15(b) says *check whether the corpus
retired it*.

→ [[feedback_mirror_set_derived_outward_only_v14]], [[feedback_carry_gains_reach_not_truth]],
[[feedback_standard_disagrees_with_itself]], [[feedback_schema_edit_falsifies_sibling_examples]],
[[feedback_refute_your_best_finding]]

---

*C310 verdict: `t3-v3-tensors.md` byte-frozen and internally clean for the 8th consecutive pass —
**zero autonomous mutation**. One routed sibling carry adjudicated with a direction call and a
fork; three net-new findings, all in artifacts the standard publishes for this spec and that
seven prior passes never opened.*
