# C408 — `LCT-linked-context-token.md`, 10th delta

**Target**: `web4-standard/core-spec/LCT-linked-context-token.md`
**Date**: 2026-08-18 · **Slot**: `legion-web4-20260818-180000` · **Predecessor**: C368 (PR #695, `61530057`)
**Protocol**: Autonomous Session Protocol v2 · **Mutation**: ZERO · **New files**: 1 (this one)

---

## §0. Headline

**The spec's §7.4 declares four revocation reasons. Nothing implements the fourth.**

`violation` is named at `:521` with a definition (*"Policy violation"*). Three artifacts declare a
closed revocation-reason vocabulary and **all three carry exactly the other three, in the spec's own
order**; two more decline to declare one at all, one of them re-typing the field as free prose. Not a
single artifact in the corpus can represent an LCT revoked for a policy violation.

Both halves of this were already printed **by this lineage** — `C24:316`/`:322` printed the four and
drew only the *status* conclusion; `C328:162` printed the schema's three — and no pass compared them.
That is **v60** (*evidence is not a carry*) recurring in the lineage that coined it.

**The headline this pass drafted was killed by policy review** (18th consecutive). It was going to be
"the gate-enforced schema mints an unregistered value in 3 of its 3 enums." The measurement is correct
and is published below as §B.1, but the framing is a base rate: the enforced schema is a *uniformly
looser* artifact — a superset on all three shared enums **and** it drops enum constraints on five more
vocabularies. "Mints in 3 of 3" restates "uniformly looser." One increment (`derived_from`), not three.

---

## §A. Window

| | |
|---|---|
| Target blob | `231d70b5`, 726 L |
| Last mover | `d89595e8` (2026-07-16, #531) — **byte-frozen 33 d, 5th consecutive frozen delta** |
| Window | `61530057..HEAD` = **32 commits** |
| `web4-standard/` movers | **0** — `git log --format='%H' 61530057..HEAD -- web4-standard/ \| wc -l` |
| Tree breakdown | `docs/audits` 18 · `hub/hub-lib` 12 · `hub/docs` 9 · `hub/hub-daemon` 6 · `whitepaper` 3 · `web4-core/src` 1 · misc 4 |
| Schemas | `lct.schema.json` blob `e46d5a09` (`9bcfe598`, 2026-02-22) · `lct-jsonld.schema.json` blob `64dd77d6` (`af621844`, 2026-04-10) · `entity-jsonld.schema.json` `9dd8f06e` — **all frozen** |

**Which schema binds** (inherit from C368, do not re-derive): `web4-standard/implementation/sdk/web4/validation.py:57`
maps `"lct"` → **`lct-jsonld.schema.json`**; `lct.schema.json` is `"lct-raw"`, whose sole non-definition
reference is `test_validation.py:101`. Below, **enforced** = `lct-jsonld.schema.json`, **raw** = `lct.schema.json`.

**Scope caveat carried into every table below.** The raw schema is unsatisfiable whole-document
(`C288-N1`, facet (b) — `birth_certificate.context`), so its **whole-document** column is uninformative
and every claim about raw is made at **subschema** scope, stated per table.

---

## §B. Measurements

### B.1 — Enum census, both published schemas (deflated to a measurement, not a finding)

Instrument: walk every `enum` key in each schema by JSON pointer; compare at matching pointers.

```
enforced (lct-jsonld.schema.json) — 3 enums
  /binding/entity_type          16 values   (raw: 15)  mints "agent"
  /lineage[]/reason              5 values   (raw:  4)  mints "derived_from"
  /revocation/status             3 values   (raw:  2)  mints "suspended"
raw (lct.schema.json) — 8 enums
  the three above, plus /birth_certificate/context, /mrh/bound[]/type,
  /mrh/paired[]/pairing_type, /mrh/witnessing[]/role, /revocation/reason
```

The enforced schema is a **strict superset on all three shared enums** and declares **no enum at all**
for the other five vocabularies. `agent` is charged (`C368-N1`), `suspended` is charged (`C368-N2`);
`derived_from` is new and is §C.3. **This is one authorship event, not three independent confirmations
— recorded as a base rate, deflating this pass's drafted headline.**

### B.2 — Runtime enforcement, per vocabulary

Denominator: the four implementations that model an LCT document — Python SDK, Go reference, TS
reference, plus the two schemas. "Runtime enforcer" = a construct that rejects an out-of-vocabulary
value when a document is actually parsed.

| vocabulary | enforced | raw | Python SDK | Go `Validate()` | TS `validate()` | runtime enforcers outside the enforced schema |
|---|---|---|---|---|---|---|
| `binding.entity_type` | 16 | 15 | `EntityType(...)` `lct.py:94`, `:655` | `isValidEntityType` `document.go:381` | `VALID_ENTITY_TYPES` `lct-document.ts:397` | **3** |
| `revocation.status` | 3 | 2 | `RevocationStatus(...)` `lct.py:509`, `:741` | type only, never inspected | type only, never inspected | **1** |
| `revocation.reason` | *none* | 3 | `Optional[str]` `lct.py:258` | consts `document.go:217-221`, never inspected | union `lct-document.ts:213`, never inspected | **0** |
| `lineage[].reason` | 5 | 4 | `str` `lct.py:195` | alias `document.go:189-196`, never inspected | union `lct-document.ts:197`, never inspected | **0** |

**Precision required (policy-review correction, adopted).** Go's `type LineageReason string` + consts
and TS's union are **compile-time or nominal only** — untyped Go string constants convert implicitly,
and TS types erase. So the honest statement is **"0 runtime enforcers, 1 never-evaluated compile-time
union"**, not "0 enforcers". Mitigating and worth publishing: `ledgers/reference/typescript/` contains
**no `package.json` and no `tsconfig.json`**, and no workflow references `ledgers/` — so the union is
never type-checked by anything either.

---

## §C. Findings

### C.1 — **N1 (MEDIUM, net-new → operator + standard editor)** — §7.4 declares four revocation reasons; the corpus implements three

**The claim.** `LCT-linked-context-token.md:518-521`:

```
Reasons:
  - compromise: Keys compromised
  - superseded: Rotated to new LCT
  - expired: Time-bounded LCT ended
  - violation: Policy violation
```

Every artifact that declares a closed vocabulary declares the **first three, in this order**, and stops:

| artifact | locus | vocabulary |
|---|---|---|
| raw schema | `lct.schema.json` `/properties/revocation/properties/reason` | `["compromise","superseded","expired"]` |
| Go reference | `ledgers/reference/go/lct/document.go:217-221` | `RevocationCompromise` / `RevocationSuperseded` / `RevocationExpired` |
| TS reference | `ledgers/reference/typescript/lct-document.ts:213` | `'compromise' \| 'superseded' \| 'expired'` |
| enforced schema | `lct-jsonld.schema.json` `/properties/revocation/properties/reason` | **no enum** — `type: ["string","null"]`, described as *"Human-readable revocation reason"* |
| Python SDK | `web4-standard/implementation/sdk/web4/lct.py:258` | `revocation_reason: Optional[str] = None` |

**Executed** (subschema scope; `Draft202012Validator` on each schema's `revocation.reason` subschema):

```
compromise   enforced=PASS   raw=PASS
superseded   enforced=PASS   raw=PASS
expired      enforced=PASS   raw=PASS
violation    enforced=PASS   raw=FAIL      ← the spec's own fourth value
banana       enforced=PASS   raw=FAIL      ← negative control: raw's enum is not vacuous
```

The enforced schema admits `violation` only in the sense that it admits `banana` — it constrains
nothing. So `violation` is **rejected by the one artifact that enumerates and unrepresentable as a
typed value in both reference implementations**.

**Ordering is the evidence.** Three artifacts, authored independently, each take the spec's first three
in the spec's sequence and drop the fourth. That is a derivation with one truncation, not coincidence.

**The fence objection, disposed head-on.** §7.4's content sits inside an unlabeled fence
(`:515`-`:528`), and `C288:130` excluded fenced pipe-alternation strings — naming
`"genesis|rotation|fork|upgrade"` explicitly — as documentation convention. That exclusion does not
reach here, for a reason internal to the same fence: **`:524` `status = "revoked"` is in it**, and every
implementation honours it (`RevocationRevoked`, `'revoked'`, `RevocationStatus.REVOKED`). Reading the
fence as non-normative voids the three values everyone *did* implement along with the one they didn't.
Whatever normative weight carried `revoked` out of `:524` carried `violation` out of `:521`.

**Novelty, matchers published.** `git grep -n "violation" -- web4-standard/ ledgers/ web4-core/ core/`
returns zero hits of `violation` as a revocation-reason *value* outside `:521`. Audit corpus:
`C24:316` reproduces the four-line block verbatim and `C24:322` writes *"§7.4 enumerates four REASONS
(`compromise|superseded|expired|violation`)"* — then draws only the **status** conclusion (that the spec
implies `{active, revoked}` without declaring it). `C328:162` separately printed the raw schema's three.
`C114-B4` charged a *different* 2-vs-3 divergence on the **sister** doc. **No pass compared the spec's
four against the implementations' three.**

**This is v60 recurring in its own lineage.** *Evidence is not a carry*: a fact printed in a finding's
own baseline is not carried by that finding's disposition row. C24 printed the four-value list as
supporting material for a status finding, and the list went nowhere for nine passes.

**Materiality, routed not annexed.** `violation` is the only one of the four that is a *governance*
act — a society revoking a citizen for policy breach. The corpus's enforcement layer is being built
around exactly that act (W4IP kinetic verbs, `web4-standard/core-spec/hub-law-schema.md`). Stated as materiality for the
operator's severity call; **no disposition taken on any other lineage's rows.**

**Severity MEDIUM** — normative under-implementation of the target's own lifecycle section; not
exploitable; fully reversible. **Remedy is an operator choice, REGISTER or RETRACT** (add `violation`
to the three closed vocabularies, or strike it from `:521` and say the lifecycle has three reasons).
**Do NOT self-apply** — both the spec and the schemas are normative artifacts.

### C.2 — **N2 (MEDIUM, net-new → operator/schema track; arm on `C288-N1`)** — the two MUST-PASS vector families are exactly complementary on `lineage[]`

`/lineage[]` `required` disagrees between the published schemas — enforced `["parent","reason"]`, raw
`["reason","ts"]` — and the corpus ships one MUST-PASS vector family on **each** side of the
disagreement, so each family is invalid under the schema the other satisfies.

**Executed** (subschema scope, `properties.lineage.items` of each schema):

```
valid[7]  {"parent":"lct:web4:ai:v1","reason":"genesis"}      enforced=PASS   raw=FAIL ('ts' required)
interop   {"reason":"genesis","ts":"2026-02-19T00:00:00Z"}    enforced=FAIL ('parent' required)   raw=PASS
```

Left row: `web4-standard/test-vectors/schema-validation/lct-jsonld-validation.json` `valid[7]`.
Right row: `web4-standard/test-vectors/lct/interop-human-full.json:37-41` — `should_succeed: true` —
and `web4-standard/test-vectors/lct/interop-revoked-agent.json` carries the same shape.

**Consequence, executed at whole-document scope** on `lct-jsonld-validation.json` `valid[1]` with
`parent` dropped: enforced **FAIL**, and `LCT.from_jsonld` raises an **uncaught `KeyError: 'parent'`**
(`lct.py:202`, `parent=d["parent"]`) — an untyped exception escaping the SDK's error surface, not a
`ValueError` like the `entity_type` path.

**Which side is right: the spec has no MUST on `lineage.parent`.** §7.3's *"Lineage points to parent
LCT"* (`:504`) is scoped to **rotation**. A `genesis` entry has no parent by construction. So the
parentless shape is semantically correct and the **enforced schema's `required: parent` is the wrong
constraint** — and `valid[7]`'s genesis-*with*-a-parent is the incoherent shape that constraint forces.
(Offered as reading, not as a causal claim about authorship; no `git blame` evidence is presented for
the "price of `required:parent`" story.)

**Two emitters produce the shape the enforced schema rejects**: TS
`lct-document.ts:607` `addLineage(reason: LineageReason, parent?: string)` — parent optional — and Go
`document.go:201` `Parent string \`json:"parent,omitempty"\`` — dropped when empty.

**Severity capped, honestly.** The only consumer of the three `interop-*.json` vectors is
`archive/reference-implementations/cross_language_interop.py:824`, which is gate-inert: the SDK's
`web4-standard/implementation/sdk/pyproject.toml:84` sets `testpaths = ["tests"]` and no workflow
references `archive/`. **Attribution corrected mid-pass:** C368 pinned the archive-tree gate-inertness
to `C288:128`, but `C288:128` is about the *raw schema* being registered-but-never-validated-against,
a different artifact. The inertness *class* is C368's ruling and is not re-filed as net-new; the two
cells above are this pass's own measurement. So this is a shape disagreement with an executed
consequence, **not** a red CI gate. **MEDIUM**, on the same operator
question as `C288-N1` (*which published schema is normative?*), which now decides four carries.

### C.3 — **N3 (LOW, net-new → schema track)** — `derived_from`: the discharge of C368 row 8 is *there is no register*

C368 row 8 asked whether `derived_from` "is registered anywhere." **It is not, and neither are the
other four** — no artifact in `web4-standard/` declares a lineage-reason vocabulary at all.

- Corpus sweep `git grep -n "derived_from"` = 5 hits; **2** are LCT-relevant — `lct-jsonld.schema.json:246`
  and its byte copy vendored into the wheel at `implementation/sdk/web4/schema_registry.json:1888`.
  The other three (`archive/…/mrh_theoretical_foundation.py:480`, `docs/how/GROUNDING_INTEGRATION_NOTES.md:54`,
  `hub/hub-lib/src/constellation.rs:1035`) are unrelated uses of the token.
- The **only** enumeration of lineage reasons in the standard is the pipe-alternation placeholder at
  `LCT-linked-context-token.md:206`, and `C288:130` excluded that string **by name** as a documentation
  convention. **The spec-contradiction route is therefore closed** — unlike `agent`, which contradicts a
  ratified 804-line register (`web4-standard/core-spec/entity-types.md`). `derived_from` has nowhere to be absent *from*.
- Executed (ARM A, whole-document, `valid[1]`): the four spec values and `derived_from` all PASS the
  enforced schema; the negative control `spontaneous_combustion` **FAILS** it (enum not vacuous); and
  the Python SDK **accepts all six**, including the negative control.

**Severity LOW**, per standing carry **v16** (*absence is not prohibition*): lower detectability than
`agent` — nothing anywhere can contradict it (§B.2 row 4) — but with no normative referent, that is
risk without a violated rule. Declared as a **v61 recurrence** (*the undefined vocabulary is the defect,
not the disagreement*), not sold as a novel pattern. Route: schema track, jointly with `C368-N1`'s
operator ruling — the register-or-retract question is the same one, one field over.

### C.4 — **N4 (LOW, net-new → schema track)** — C368 row 6: the enforced `lct_id` constraint contradicts its own description

`lct-jsonld.schema.json` `/properties/lct_id`: `pattern: "^lct:"`, `description: "Unique LCT
identifier. Format: lct:web4:<type>:<hash>"`. Raw: `pattern: "^lct:web4:[A-Za-z0-9_:-]+$"`.

**Executed** (subschema scope):

```
'lct:web4:ai:abc123'   enforced=PASS   raw=PASS
'lct:bogus'            enforced=PASS   raw=FAIL
'lct:'                 enforced=PASS   raw=FAIL
'lct:x'                enforced=PASS   raw=FAIL
'notanlct'             enforced=FAIL   raw=FAIL      ← negative control: the pattern is not vacuous
```

A constraint that admits `lct:` while its own adjacent prose states a four-segment format. **LOW** —
self-contained, one artifact, textual. Bears on `C24-H1` (C368 flagged this), but no disposition is
taken on `C24-H1` here: it is a HIGH held by the operator memo.

### C.5 — Observation, NOT a finding (do not re-derive it as one)

`web4-standard/schemas/contexts/lct.jsonld:189-192` maps the term `reason` → `web4:reason`,
`xsd:string` — **one global IRI serving both `lineage[].reason` and `revocation.reason`**, two disjoint
vocabularies. The same file disambiguates the sibling: `status` → `web4:revocationStatus` (`:198-200`).
Recorded because the file has been opened by 5 audits in 10 passes and no one has read these terms; it
is an observation about JSON-LD term scoping, and charging it would require a consumer that is harmed,
which this pass did not find.

---

## §D. Deferral discharges — and what is **not** discharged

C368 §F.5 pre-registered three items. Naming the residue is required; a bounded choice is fine,
truncation dressed as discharge is not.

| item | status |
|---|---|
| **1. `hub/` window commits vs `C288-N2`'s anchors** | **DISCHARGED, no net-new.** Re-resolved **by content**: `hub/hub-lib/src/constellation.rs` — `pub struct AssuranceReceipt` `:542` (C328 read `:543`), `pair_id` `:545`, `hub_lct_id` `:555`, `hub_signer_lct_id` `:560`. `*_lct_id: Uuid` in `hub/` = **155** (C328: 160). The `hub_signer_lct_id` widening dates to `8b0b133d` (2026-07-29) and **C328 already recorded it** — not re-filed. C288-N2 substance HELD. |
| **2. The other 11 rows of the schema diff** | **PARTIAL.** Rows **6** (§C.4), **7** (§C.2) and **8** (§C.3) taken — the two C368 named "in particular", plus row 7. Rows 1/5 are `C288-N1`'s own. **Rows 9, 10, 11 and 13 NOT examined → re-deferred to C448**: 9 `/mrh`, 10 `/mrh/paired`, 11 `/revocation/reason` **type** (`["string","null"]` vs `"string"` — note §C.1 reached its *enum*, not its type), 13 `/revocation/ts` type. |
| **3. `web4-standard/schemas/entity-jsonld.schema.json` vs `web4-standard/core-spec/entity-types.md` as a pair** | **NOT TAKEN → re-deferred to C448**, with a pointer: `C372-N3` served much of it from the other side (the top-level `oneOf` admits only taxonomy metadata, so the register is structurally unreachable for a real entity; `web4-standard/schemas/contexts/entity.jsonld` types `entity_type` as `xsd:string` with no enum). What remains is the full field-by-field pair diff. |

---

## §E. v36 inbound set-difference — a **different window** from C368's

C368 ran the domain sweep bounded to `docs/audits/` + `web4-standard/docs/audits/` and got **7 / 81,
residue EMPTY**. That is a statement about the audit trees. This pass ran the complement.

**Pre-registered window**: root = repo; all tracked filetypes; exclusion rule = drop
`docs/audits/`, `archive/`, `forum/`, `whitepaper/` (audit + sprawl trees); `comm -23` after `sort`.

- `git grep -li "linked context token"` → **90** after exclusion (unfiltered **165**; the
  **case-sensitive** form returns **1** — the matcher's case flag moves this by 165×, which is why it
  travels with the count). Filename sweep `git grep -li "LCT-linked-context-token"` → **50**.
  **Residue: 66 files** — product trees that discuss the domain without citing the file by name.
- Second sweep, the **finding's** domain word, scoped to the implementation trees:
  `git grep -li "lineage" -- web4-standard/ ledgers/ web4-core/ core/` = 44, minus filename sweep 23 ⇒
  **residue 31**.

**Two residue members carried this pass's yield**, which is what the sweep is for:
`web4-standard/schemas/contexts/lct.jsonld` (→ §C.5) and `ledgers/reference/go/lct/builder.go:160`
(`AddLineage(reason LineageReason, parent string)`, whose `parent` is a required *argument* that is
nonetheless dropped from the wire by `omitempty` — the emitter half of §C.2).

**No divergence is claimed against C368's figure**: 7 and 90 are different windows, not a disagreement.

---

## §F. Own errors this pass (6)

1. **Drafted headline was a base rate.** "Mints in 3 of 3 enums" restates "the enforced schema is
   uniformly looser." Caught by policy review; deflated to §B.1 and published as a measurement.
2. **Over-claimed "0 enforcers"** for `lineage[].reason`. Corrected to *0 runtime, 1 never-evaluated
   compile-time union*, with the no-`tsconfig`/no-CI evidence that makes the correction matter.
3. **Nearly charged `derived_from` at MEDIUM** on the `agent` analogy. The analogy fails: `agent`
   contradicts a ratified register and `derived_from` has no register to contradict. Demoted to LOW.
4. **First run of arms C and D was at whole-document scope**, where the raw column is uninformative
   (C288-N1 unsatisfiability) — every raw cell read FAIL and said nothing. Re-run at subschema scope.
5. **Reviewer correction verified and one reversed** (v52 — verify the reviewer's corrections too):
   the review reported `C74-B3`/`C114-B3` as having "zero hits in `docs/audits/`". They resolve:
   `docs/audits/C74-web4-lct-protocols-audit-2026-06-19.md:50` and
   `docs/audits/C114-web4-lct-2nd-delta-2026-06-29.md:33`. Both are on the **sister** doc
   (`web4-standard/protocols/web4-lct.md`), so they corroborate rather than duplicate §C.1 — and the review's
   substantive corrections (1-4 above) all held.
6. **Propagated a misattribution one step before catching it.** §C.2 first credited the interop
   vectors' gate-inertness to `C288:128`, inheriting C368's pin. `C288:128` is about the **raw schema**
   being registered-but-never-validated-against — a different artifact. Corrected in place, and the
   two inertness cells are now this pass's own measurement (`pyproject.toml:84`, no workflow reference
   to `archive/`). Caught by the standing rule that every line anchor must be *read*, not carried:
   the anchor resolved, and said something else.

---

## §G. Carry ledger for the next LCT delta (**C448**)

### G.1 — Net-new this pass

| id | sev | status | summary |
|---|---|---|---|
| **C408-N1** | **MED** | OPEN → operator + standard editor | §7.4 `:518-521` declares **four** revocation reasons; **`violation` is implemented by nothing**. 3 closed vocabularies (`lct.schema.json` enum, Go `document.go:217-221`, TS `lct-document.ts:213`) each carry the other three in the spec's order; 2 declare none (enforced schema re-types the field as *"Human-readable"*, SDK `lct.py:258` `Optional[str]`). Executed: `violation` FAILS raw, PASSES enforced only because enforced has no enum — so does `banana`. Fence objection disposed via `:524`. **v60 recurrence** — `C24:316`/`:322` printed the four, `C328:162` printed the three, neither compared. Remedy = **REGISTER or RETRACT**, operator's. Do NOT self-apply. |
| **C408-N2** | **MED** | OPEN → operator/schema (arm on `C288-N1`) | The two MUST-PASS vector families are **exactly complementary** on `/lineage[]` `required`: `valid[7]` PASSES enforced / FAILS raw (`ts`); `interop-human-full.json:37` PASSES raw / FAILS enforced (`parent`). SDK raises **uncaught `KeyError: 'parent'`**. Spec has **no MUST on `lineage.parent`** (§7.3 `:504` is rotation-scoped) ⇒ parentless genesis is correct and the enforced `required` is wrong. Emitters: TS `:607`, Go `:201` `omitempty`. Severity capped — interop vectors' sole consumer is gate-inert (`C288:128`, not re-filed). |
| **C408-N3** | **LOW** | OPEN → schema track (with `C368-N1`) | `derived_from` — discharge of C368 row 8 is **there is no register**. 2 real corpus hits (schema `:246` + vendored `schema_registry.json:1888`); the only lineage-reason enumeration in the standard is `:206`, excluded **by name** at `C288:130`. **0 runtime enforcers** (§B.2). v16 + **v61 recurrence**. |
| **C408-N4** | **LOW** | OPEN → schema track | C368 row 6: enforced `lct_id` `pattern: "^lct:"` vs its own `description: "Format: lct:web4:<type>:<hash>"`. `lct:` and `lct:bogus` PASS; `notanlct` FAILS (neg control). Bears on `C24-H1`; **no disposition taken on `C24-H1`**. |

### G.2 — Held, verified unchanged

`C288-N1` (now decides **four** carries: `C24-M4`, `C24-M6`, `C408-N2`, and its own) · `C288-N2`
(anchors re-resolved by content, §D item 1) · `C368-N1` · `C368-N2` · `C372-N3` (received as the
mechanism behind `C368-N1`; corroborated here — the semantic layer constrains nothing, §C.5) ·
`C24-H1` (operator memo) · the 23-row restored ledger from `C328` — **not re-enumerated here; C328 §F
remains the enumeration of record**, and this pass declines to let its own ledger become the next
pass's exhibit.

### G.3 — **DEFERRAL ROW FOR C448 (pre-registered)**

1. **Schema-diff rows 9, 10, 11, 13** — untouched (§D item 2). Row 11 in particular: §C.1 reached
   `revocation.reason`'s **enum**, not its **type** disagreement.
2. **`web4-standard/schemas/entity-jsonld.schema.json` vs `web4-standard/core-spec/entity-types.md` as a full pair diff** — third pass carrying it;
   `C372-N3` served the reachability half, the field-by-field diff is untaken (§D item 3).
3. **Does any *other* spec section enumerate a vocabulary that no artifact implements?** §C.1 found one
   by walking §7.4. The generalization — walk every enumerated list in the 726-line target and diff
   each against the artifacts that implement it — was **not** run. If it yields a second `violation`,
   §C.1 is a class, not an instance.
4. **`web4:reason` term collision** (§C.5) — recorded as an observation. It becomes a finding only if a
   consumer is found that is harmed by the conflation. Do not charge it without one.
5. **`web4-core/src/lct.rs:58-67` `pub enum LctStatus { Active, Dormant, Void, Slashed }`** — the
   released Rust crate models LCT status with a **four-value vocabulary that intersects the spec's
   `{active, revoked}` in exactly one member**, and declares no revocation-reason vocabulary at all.
   **This was routed here and never received**: the atp-adp lineage excluded it as a name-collision
   false-mirror at `C228:80` and said so explicitly — *"this is LCT-lifecycle slashing … the
   web4-lct/LCT-spec entity-status lens"* — re-confirmed at `C266:27`. Two passes handed this lineage a
   pointer and ten passes did not pick it up. **Not measured here** (this pass found it while checking
   whether a fourth artifact declares the §C.1 vocabulary); C448 should probe `web4-core`'s status
   surface against §7.4's `Effect: status = "revoked"` before charging anything. Credit C228/C266.

---

## §H. Accountability self-audit

**n/a — no surface.** This pass creates and changes nothing a caller can drive: one new document under
`docs/audits/`, zero mutation of any spec, schema, SDK, vector, or implementation. No consequential act
(sign, admit, assign role, amend law, release a secret, spend, mutate governed state, emit outward) is
reachable from anything added here. All four findings **route to the operator and are explicitly not
self-applied**, which is the point: the remedy for N1 and N3 is a normative register-or-retract choice,
and an auditor taking it would itself be the W violation.

---

*Audit produced under Autonomous Session Protocol v2 by `legion-web4-20260818-180000`.
Policy review: **REVISE** → six changes required; all six adopted (demote the enum-census headline to a
recorded base rate; charge `derived_from` LOW as a v61 recurrence rather than MED on the `agent`
analogy; restate the enforcer count as 0-runtime/1-never-evaluated; lead N2 with the complementary-vector
result at subschema scope; publish the deferral arithmetic with its residue named; resolve every path
token to its real root). The review also supplied §C.1, this pass's headline, by verification — the
drafted headline was killed. **18th consecutive pass whose headline or central premise policy review
falsified.***
