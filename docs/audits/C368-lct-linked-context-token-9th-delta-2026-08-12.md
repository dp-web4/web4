# C368: LCT-linked-context-token.md 9th-Delta Re-Audit (11th pass)

**Date**: 2026-08-12
**Auditor**: Autonomous session (legion-web4-20260812-060000)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (726 lines, blob `231d70b5` — **byte-frozen since C210**)
**Base**: C328 merge `89251abc` (#653)
**Lineage (11 documents, inclusive rule — the non-C-numbered `…-internal-consistency-…` member counts)**: **C9** (`docs/audits/lct-internal-consistency-2026-05-22.md`, pre-convention filename, self-identifying `# C9 Audit:` on line 1) → C24 (#256) → C60 (#338) → **C61 remediation** (`9d1933f8`) → C100 → C135 → C172 → C210 (#531 mover) → C248 → C288 (#596) → C328 (#653) → **C368**.
**Spec mutations since C210**: **0**. `git diff d89595e8..HEAD -- <target>` = empty. **Fourth consecutive byte-frozen delta** (27 days).
**Window**: 48 commits since `89251abc`.

---

## Framing — the lineage has been reading the wrong schema

The standard publishes **two** LCT schemas. One of them is wired into the SDK's validator, the standard's own schema harness, the round-trip suite and the schema-validation vector runner. The other is reachable only under the name `"lct-raw"`, and **no CI-reachable or pytest-collected code ever validates anything against it**.

For three passes across two lineages, the conformance rulings have been taken from the second one:

- **`C302:283`/`:333`** read `lct.schema.json`'s `binding.entity_type.enum` = 15 and adjudicated the sibling carry **B7** *"in canonical's favour by three independent implementations"* (`C302:351`).
- **`C328 §C`** read `lct.schema.json`'s `revocation.status` enum = `["active","revoked"]` and re-classified the operator design questions **`C24-M4`** and **`C24-M6`**, writing *"False of the standard"* and *"the schema **FORBIDS** the `suspended` the SDK vector emits."*
- The standing carry **`C60-B12`** is premised on a closed **15**.

The enforced schema disagrees with all three. Its `entity_type` enum has **16** values — the 16th is **`agent`**, which appears as an entity type in **no other artifact in the corpus** (§C). Its `revocation.status` enum **permits `suspended`** (§D). The lineage's own C288 had already established, one pass before C328, that the schema C328 then used to adjudicate *"is registered but never validated against"* (`C288:128`).

**§C is net-new (MEDIUM). §D is a correction of this lineage's immediately preceding pass (MEDIUM).** They are one root cause with two faces, which is why they are filed together and routed to the same open question.

**Counts**: §A 0 spec motion, all mirrors frozen but `hub/`. §B — first schema-vs-schema diff in 11 passes: **13 disagreements**, enumerated; C288-N1's "4" sharpened to 13 (**not a row**); the totals **failed reproduction and are withheld** (§B.3). §C — **1 MED net-new** (`C368-N1`). §D — **1 MED correction** (`C368-N2`), C24-M4's answer inverts. §E — corpus-delta **CLEAN against the spec prose, 5th consecutive**. **Zero mutation.**

**The spec prose is CORRECT in every finding below.** Nothing routes a change to `LCT-linked-context-token.md`.

---

## §A. Freeze + window at live HEAD

### A.0 — Freeze
`git diff d89595e8..HEAD -- web4-standard/core-spec/LCT-linked-context-token.md` → **empty**. Blob `231d70b5`, 726 lines. Last touch `d89595e8` (#531, 2026-07-16). **4th consecutive frozen delta.**

### A.1 — Mirror motion (command published per cell: `git log --oneline 89251abc..HEAD -- <path> | wc -l`)

| Mirror | Commits | Verdict |
|---|---|---|
| `web4-core/src/lct.rs` · `attestation.rs` · `ratchet.rs` · `role.rs` | 0 · 0 · 0 · 0 | frozen |
| `implementation/sdk/web4/lct.py` | 0 | frozen |
| `schemas/lct.schema.json` | 0 | frozen (`9bcfe598`, 2026-02-22) |
| `schemas/lct-jsonld.schema.json` | 0 | frozen (`af621844`, 2026-04-10) |
| `test-vectors/lct/` · `ledgers/reference/` | 0 · 0 | frozen |
| `web4-trust-core/` · `web4-policy/` · `core/lct_binding/` | 0 · 0 · 0 | frozen |
| **`hub/`** | **19** | moved — §E |

**Window instrument, both forms published (they disagree and both are right):**
per-commit TOUCHES / unique PATHS — `hub` 32/13 · `docs` 20/20 · `whitepaper` 4/1 · `web4-standard` 3/3 · `STATUS.md` 1/1 · `scripts` 1/1 · `CHANGELOG.md` 1/1.

### A.2 — Deferral row
C328 §F: *"DEFERRAL ROW FOR C368 — none carried; C328 discharged all 5 of C288's."* **Nothing inherited.** This pass's scope was therefore earned by the opening sequence's machine checks, run before any re-reading, not by a pre-registered list.

### A.3 — Pre-committed routing (recorded in this session's policy review **before** §C/§D were written)

> A disagreement between the two schemas on a field already in C288-N1's five-row table is **C288-N1 reach, not net-new**. Only a disagreement on a field **outside** that table, where the *enforced* schema is the one carrying the unregistered value, is candidate net-new. A correction to C328 is publishable **only** if the enforced schema's behaviour is executed, not read.

Both conditions are met below. The routing is published here so neither finding can be sold as a discovery after the fact.

---

## §B. The two published schemas, diffed against each other for the first time

Eleven passes have read these files separately. C328 §D.4 validated the ten vectors against **both** — but never compared the two schemas **to each other**. That is the gap this section closes.

### B.1 — Which schema is enforced (v45: caller count, not registration)

| | `lct-jsonld.schema.json` | `lct.schema.json` |
|---|---|---|
| SDK validator name | **`"lct"`** (`validation.py:57`) | `"lct-raw"` (`validation.py:67`) |
| Standard's own harness | **`validate_schemas.py:81`** | — |
| Round-trip suite | **`test_jsonld_schema_roundtrip.py:67`, `:834`** | — |
| Schema-validation vectors | **`validate_schema_vectors.py:42`** | — |
| Only other `"lct-raw"` reference | — | `test_validation.py:101` — `assert "lct-raw" in schemas` |
| Bundled in the wheel | yes (`schema_registry.json`) | yes (`schema_registry.json`) |

`test_validation.py:101` asserts the schema is **listed**, never that anything **validates** against it — `[[feedback_does_the_impl_agree_with_itself]]`'s test shape exactly. This is **C288's finding, not mine** (`C288:128` states it verbatim, including the same two-hit grep); it is restated here only because §C and §D turn on it.

**Scoping the inertness claim honestly (required correction from this session's policy review).** "Never validated against" is true of every automated gate and false repo-wide. Three consumers **do** load it: `archive/reference-implementations/lct_schema_validator.py:40` and `lct_document.py:402` actually validate against it, and `ledgers/reference/typescript/lct-document.ts:9,226` names it source of truth (the last was already disclosed at C288 facet (c)). None is reachable from a gate: `sdk/pyproject.toml:84` sets `testpaths = ["tests"]`, `archive/` is never collected, and `grep -rn lct_schema_validator` returns **zero invokers** (one hit, `docs/history/STATUS-2026-02.md`, pointing at a path that no longer exists). **The correct claim is "inert to every automated gate," not "unreferenced."**

### B.2 — The 13 disagreements, enumerated

Instrument: recursive collector over `{enum, required, pattern, type, additionalProperties}`, keyed by JSON pointer; a row appears only where **both** schemas define the same pointer and the values differ.

| # | Pointer | Constraint | jsonld-only / value | raw-only / value |
|---|---|---|---|---|
| 1 | `<root>` | required | `@context`, `revocation`, `t3_tensor`, `v3_tensor` | `birth_certificate` |
| 2 | `/attestations[]` | required | — | `sig`, `ts` |
| 3 | `/binding` | required | — | `binding_proof` |
| **4** | **`/binding/entity_type`** | **enum** | **`agent`** | — |
| 5 | `/birth_certificate` | required | — | `birth_witnesses`, `context` |
| 6 | `/lct_id` | pattern | `^lct:` | `^lct:web4:[A-Za-z0-9_:-]+$` |
| 7 | `/lineage[]` | required | `parent` | `ts` |
| 8 | `/lineage[]/reason` | enum | `derived_from` | — |
| 9 | `/mrh` | required | `witnessing` | `last_updated` |
| 10 | `/mrh/paired[]` | required | `pairing_type` | `ts` |
| 11 | `/revocation/reason` | type | `["string","null"]` | `"string"` |
| **12** | **`/revocation/status`** | **enum** | **`suspended`** | — |
| 13 | `/revocation/ts` | type | `["string","null"]` | `"string"` |

**C288-N1 states the two schemas "disagree on 4 components" (`C288:113`). Measured: 13.** That is a **sharpening of C288-N1, not a new row** — C288's table (`:105-111`) is explicitly a *required*-list comparison over five components, and it is correct on its own terms. Rows **4** and **12** are the two this pass turns on, and **neither field appears in C288's table at all**.

### B.3 — A negative published: the totals did not reproduce

The first collector reported jsonld **99** / raw **109** constraints. This session's policy review independently re-implemented the same stated method and got jsonld **117** / raw **111** — **the direction inverts** (the raw schema carries more constraints under one implementation and fewer under the other; the likely cause is differing treatment of `$defs`/`$ref`, which the JSON-LD schema uses for the tensors and the raw schema inlines).

**A total whose sign flips under a re-implementation of its own stated method is an instrument artifact, not a measurement. The totals are withheld.** The **13** reproduced exactly under both implementations, and it is self-verifying because every row above is a named JSON pointer that a reader can check by hand. Recorded because the withheld number is the one that would have read as a result.

---

## §C. `C368-N1` (MEDIUM, net-new) — the enforced schema admits a 16th entity type that exists nowhere else

### C.1 — The measurement

`lct-jsonld.schema.json` `binding.entity_type.enum` has **16** values. Fifteen are the canonical set. The sixteenth is **`agent`**.

| Artifact | Count | `agent` present? |
|---|---|---|
| **`schemas/lct-jsonld.schema.json`** (**enforced**) | **16** | **YES** |
| `schemas/lct.schema.json` (inert to gates) | 15 | no |
| `schemas/entity-jsonld.schema.json` | 15 | no |
| SDK `implementation/sdk/web4/lct.py` `EntityType` | 15 | no |
| Register `core-spec/entity-types.md §2.1` | 15 | no |

**Denominator: 1 of 5.** Per v46, a 1-of-5 ratio is a defect, not a corpus idiom.

### C.2 — Executed, with a backed control and a negative control

Instrument: real vector `lct-jsonld-001` from `test-vectors/lct/lct-jsonld-vectors.json` (one of the 10 that pass the enforced schema), **one field changed**, jsonschema 4.26.0 `Draft202012Validator`.

| | `binding.entity_type` | ENFORCED `lct-jsonld` | inert `lct.schema` | SDK `EntityType(...)` |
|---|---|---|---|---|
| **CONTROL (backed)** | `"ai"` | **PASS** | FAIL | **OK** |
| **MUTANT** | `"agent"` | **PASS** | FAIL | **`ValueError: 'agent' is not a valid EntityType`** |
| **NEGATIVE CONTROL** | `"not_real"` | **FAIL** | FAIL | `ValueError` |

The negative control is what makes the instrument admissible: the enum is **not vacuous** — it rejects an arbitrary string and accepts `agent` specifically.

⇒ **The standard's only gate-enforced LCT schema accepts a document that the standard's own reference SDK cannot represent.** A conforming producer and a conforming consumer disagree, and the conformance surface sides with the producer.

### C.3 — The belief in "16" is systemic, not a one-file typo

Two further in-standard sites assert sixteen entity types while shipping fifteen:

- **`test-vectors/schema-validation/lct-jsonld-validation.json:254`** — `"description": "LCT with all 16 entity types (one per type, testing 'policy')"`. `grep -c agent` on that file = **0**. The conformance vector's author believed there were 16 and enumerated 15.
- **`implementation/sdk/CHANGELOG.md:662`** — *"validation for all 16 entity types. 48 tests, 5 vectors."* The SDK's own published changelog, against an `EntityType` enum of 15.

Neither was found by any prior pass. Together with the enum they are three independent assertions of 16 in the standard's own artifacts.

**It also ships.** `schema_registry.json:1632` carries `"agent"` — the drift is inside the installable wheel, not only the repo.

### C.4 — Refutation attempts (all three fail; each is pre-answered because a reviewer will raise it)

1. **"It's a legitimate raw-vs-JSON-LD profile difference"** — the concession C288 itself made at `:132`. **Fails on the lineage's own reasoning at `C288:134`**: *"A profile cannot explain the T3/V3 direction: one published schema makes them mandatory and the other optional, for the same object."* A profile explains a serialization envelope (`@context`/`@type`), not **value-domain membership**. A new arm routed onto C288-N1 on exactly this basis has precedent at `C328:267`.
2. **"`agent` IS registered."** It is — as a **role**, not an entity type. `entity-types.md:257-258` lists Agent among the roles Human and AI can fill, and **§4.6 `:349` is "Agent Role (AGY)"**. This does not save the enum; it **sharpens** the finding into a **category collision**: the taxonomy already carries `role` as an entity type, so an *entity type* named `agent` conflates the two axes the register keeps apart. Stated explicitly here because `§4.6` is otherwise the sentence that kills the finding.
3. **"The register is open, so `agent` is a permitted extension."** `entity-types.md §2.1` has **no** "MAY define additional" or open-set clause, and **§14 Future Extensions `:798-805`** — the document's own extension surface — lists Contract, Content, Workflow, Community, Citizen Subtypes as *"under consideration."* **`agent` is not among them.** "Unregistered" holds.

### C.5 — Provenance and direction (v: date the defect against the change you would blame)

`git log -S '"agent"' -- web4-standard/schemas/lct-jsonld.schema.json` returns exactly one commit: **`c787452e` (#53, 2026-03-20)** — the file's birth. The file has **2 commits total**; the field has never been touched since. **Age: 145 days.** This is an original-authoring artifact that has survived every pass, not a regression.

**No emitter exists.** Nothing in the corpus produces `"entity_type": "agent"` except `archive/reference-implementations/protocol_refinement_verification.py:522`, which is archived sprawl. The defect is a *permission* nothing currently exercises — which is precisely why 145 days of green gates never surfaced it.

### C.6 — What it falsifies, and what it must not annex

- **`C60-B12`'s premise is falsified.** That carry is stated as *"entity_type closed-15 vs extended types"*. The enforced schema is not closed at 15. B12 remains open and operator-routed; its **premise line needs correcting**, not its disposition.
- **Cross-track note only — do NOT annex.** `C302-N2`/**B7** (`C302:333`, `:351`) adjudicated `entity_type` "in canonical's favour by three independent implementations" — all three at 15, none of them the enforced schema. That is the **web4-lct** lineage (next slot **C382**), not this one. Recorded as a note for that ledger; this pass takes no disposition on it.

### C.7 — Severity and route

**MEDIUM.** Normative divergence on a terminology-protected register, inside the artifact that gates conformance and ships in the wheel; not exploitable; fully reversible. **Filed as a new arm on `C288-N1`'s open operator DESIGN-Q — *"which published schema is normative?"*** — because that question decides this one too.

**The remedy is an operator decision between two options, and the auditor must take neither**: **register** `agent` (amend `entity-types.md §2.1`, `entity-jsonld.schema.json`, `lct.schema.json`, SDK `EntityType`) or **retract** it (amend the enum, `lct-jsonld-validation.json:254`, `CHANGELOG.md:662`). Deleting the enum value is *not* obviously the fix — same shape as C366's authorship-not-canonicalization ruling. **Do NOT self-apply: normative artifact + conformance vector.**

---

## §D. `C368-N2` (MEDIUM) — C328 adjudicated two operator carries from the schema its own lineage had ruled inert, and the answer inverts

### D.1 — What C328 published

`C328 §C` (`:159-169`) re-classified `C24-M4` and `C24-M6` on the authority of `lct.schema.json`:

> **C24-M4** — *"True of the **prose** … **False of the standard.** `lct.schema.json` publishes a **closed 2-value enum**, and the SDK-generated vector emits `suspended`, which the schema **rejects** … The carry's premise moves from *unspecified* to *specified and violated*."*

and propagated it to the ledger at `C328:315`:

> *"**`C24-M4`** (revocation.status — re-classified §C: prose omits, `lct.schema.json` **forbids** `suspended`)"*

### D.2 — Executed against the enforced schema

`lct-jsonld.schema.json` `revocation.status.enum` = **`["active","revoked","suspended"]`**. Same control vector, same instrument:

| `revocation.status` | ENFORCED `lct-jsonld` | inert `lct.schema` |
|---|---|---|
| `active` | **PASS** | FAIL |
| `revoked` | **PASS** | FAIL |
| **`suspended`** | **PASS** | FAIL |

**`suspended` is permitted by the standard as enforced.** The SDK's `RevocationStatus.SUSPENDED` (`lct.py:74`) is not "spec-unspecified and violating" — it is **backed by the enforced schema and contradicted only by the inert one. C24-M4's answer inverts.**

### D.3 — The document refutes itself, and that is the finding

This is not hindsight. **C328 contains both dispositions of the same measurement:**

- `C328:247` — *"The pre-committed routing fires exactly as written … **a 0/10 against the raw schema is C288-N1 reach, not net-new**; only a failure against `lct-jsonld.schema.json` would be candidate net-new. The JSON-LD schema passed. **No net-new finding from this artifact.**"*
- `C328 §C` — then promotes **one arm of that same 0/10 run** (the `n=1` `revocation/status` row in its own §D.4 census, `C328:260`) into an adjudication of two operator design questions.

**Same run, two dispositions, one document.** The pre-committed routing was correct; §C stepped outside it.

**Fairness — C328 did hedge, and the hedge is why this is MEDIUM and not HIGH.** `C328:169` routes the question conditionally: *"if `lct.schema.json` is normative the remedy is to align §7.3, and if it is not, the schema's enums are unbacked."* That sentence is sound and it names the exact disjunction this pass resolves. **The chargeable defect is that the unhedged form is what propagated**: `"False of the standard"`, `"the schema **adjudicates**"`, and the ledger line at `:315` that says `forbids` flatly. **An operator reads the ledger line, not the conditional three paragraphs up.** That is `[[feedback_prose_is_not_ledger]]`.

**The method irony, recorded as method and not as snark:** `C328:157` invokes v16 explicitly — *"which is what v16 exists to distinguish: *omits* ≠ *forbids* ≠ *requires*"* — and then determines "forbids" from the file that forbids nothing anyone runs. **v16 tells you to check the modality; it does not tell you to check which artifact has standing to assert it.**

### D.4 — Disposition

`C24-M4` and `C24-M6` **remain OPEN and operator-routed**, with their C328 re-classification **WITHDRAWN** and replaced by:

- **`C24-M4`** — the prose omits an enumeration (true, 0 in 726 lines). The **enforced** schema **permits** `active|revoked|suspended`; the **inert** schema publishes a closed 2-value enum. The SDK conforms to the enforced one. **Premise: `unspecified in prose, specified permissively by the enforced schema, specified restrictively by an inert one`** — *not* "specified and violated."
- **`C24-M6`** — C328 concluded the schema *"adjudicates in favour of §7.4"* and makes §7.3 L509 *"Mark as `superseded`"* **unrepresentable**. That conclusion is drawn from the inert schema's `status` enum. Under the enforced schema, `status` has three values and `superseded` is not among them either, so **the §7.3-vs-§7.4 conflict is genuine and survives** — but it is **not** settled "by the standard's own schema," and **`superseded`-as-status is unrepresentable under both**. The conflict stands as an unresolved DESIGN-Q; the claim that a schema resolved it does not.

**Severity MEDIUM**: no code or spec is wrong because of it, but a corrected basis reaches a human decision-maker on two 73-day-old carries. **Route: same operator bundle as §C, folded into `C288-N1`.** Auditor MUST NOT self-apply.

---

## §E. Corpus delta — CLEAN against the spec prose (5th consecutive)

Of the 48 window commits: **19 in `hub/`** (governance/receipt/test hardening; grepped for the **behaviour** not the vocabulary — `lct_id` derivation, `birth_certificate` shape, `authority_ratchet`, T3/V3 embedding — **no commit claims authority over LCT subject matter**), 20 in `docs/` (audit docs C350–C366 + whitepaper log), 3 in `web4-standard/`, 4 whitepaper touches, and one each to `STATUS.md`, `scripts/`, `CHANGELOG.md`.

**v36 inbound set-difference, window and matcher pre-registered.** Domain-word sweep `git grep -li "linked context token"` **minus** the filename sweep `git grep -li "LCT-linked-context-token"`, `comm -23`, bounded to `docs/audits/` + `web4-standard/docs/audits/`.

- domain sweep: **7** files · filename sweep: **81** files · **residue: EMPTY** (the domain-word set is a strict subset).

**Recorded as a negative** — this is the outcome v48 predicts is *possible* but not guaranteed, and saying so is what makes the other fires' positives interpretable. **The residue being empty does NOT mean nothing cites the target**: **8** audit docs postdating C328 do, via the filename sweep. Read:

- **`C348:289/291/339/347`** re-measures this target for **its own** carries (`C36-N11`, `C19-M4`, `B-10` reach) — all dispositioned in the multi-device lineage, none raising anything against this target.
- **`C332:84/93`** names it only as a *referrer* to `entity-types.md`.
- The remaining six cite it in passing with no measurement against it.

**Cross-lineage hand-off found in the sweep (note only, do NOT annex).** `C332:451` — the **entity-types** lineage's own pre-registered deferral **d4** — asks: *"The other 11 top-level schemas in `web4-standard/schemas/` — do any ship MUST-PASS vectors that contradict their own spec?"*, scoped explicitly to `entity-types.md`'s slot. **`C368-N1` partially answers d4 from the other side**: `lct-jsonld.schema.json` contradicts the `entity-types.md` register directly, and `lct-jsonld-validation.json:254` is the MUST-PASS vector that asserts the wrong count. Routed to **C372** (`entity-types`, next in rotation) as evidence for d4; this pass takes no disposition on d4.

**0 net-new against the spec. Zero mutation.**

---

## §F. Carry Ledger for the next LCT delta (~C408)

**Row count: 26.** **Every id named individually — C328-N1's corrective act is upheld here and this ledger must not become the next pass's exhibit.**

### F.1 — Net-new this pass

| id | sev | status | summary |
|---|---|---|---|
| **C368-N1** | **MED** | OPEN → operator (arm on C288-N1) | `lct-jsonld.schema.json` — the **gate-enforced** LCT schema — publishes a **16-value** `binding.entity_type` enum whose 16th, **`agent`**, is in **no** other corpus artifact (4 siblings at 15; denominator 1 of 5). Executed: mutant `agent` **PASSES** the enforced schema and raises `ValueError` in the SDK; backed control `ai` passes both; negative control `not_real` fails. Category collision with the **role** register (`entity-types.md:257-258`, §4.6 `:349`). Two further "16" assertions: `lct-jsonld-validation.json:254` (`grep -c agent` = 0) and `CHANGELOG.md:662`. Ships in the wheel (`schema_registry.json:1632`). Age **145 d** (`c787452e`, #53, 2026-03-20; field never touched). **Falsifies `C60-B12`'s "closed 15" premise.** Remedy = operator choice **register or retract**; do NOT self-apply. |
| **C368-N2** | **MED** | OPEN → operator (arm on C288-N1) | `C328 §C` adjudicated `C24-M4`/`C24-M6` from `lct.schema.json`, which `C288:128` had ruled — one pass earlier, same lineage — inert to every gate. Executed: `revocation.status="suspended"` **PASSES** the enforced schema. **C24-M4's answer inverts.** `C328:247` pre-committed the opposite routing for the same run; `C328:169` hedged correctly but the **unhedged ledger line `:315` is what propagated**. C328's re-classification **WITHDRAWN**, corrected basis in §D.4. |

### F.2 — Ledger, all 20 restored names carried forward (re-verified TRUE at HEAD; all mirrors 0 commits in window)

**DESIGN-Q (operator)** — `C24-H1` · **`C24-M4`** (**basis CORRECTED, §D.4** — C328's re-classification withdrawn) · **`C24-M6`** (**basis CORRECTED, §D.4**) · `C24-L3` · `C60-B2` · `C60-B5-uniqueness` · **`C60-B12`** (**premise FALSIFIED by C368-N1** — "closed 15" is false of the enforced schema; disposition unchanged, premise line needs correcting) · `C60-B14-req` · `C60-B15` · `C60-B17`.

**SDK cross-track** (`lct.py` frozen) — `C24-M2` · `C24-M3` · `C60-B6` · `C60-B7` · `C60-B8`.

**Vector corpus** (frozen) — `C60-B1`.

**Sister-doc** (all four sister files 0 commits in window) — `C60-B9` · `C60-B10` · `C60-B11` · `C60-B13`.

**Firewall / DEMOTED** — `C23-H1` (open HIGH, now **3 dependents** rotation-wide) · `C24-D1` (folded into live `C16-M8`, pointer VERIFIED at C328) · `C24-D2` (**correctly demoted, no defect — do not resurrect**).

### F.3 — Standing findings

- **C288-N1 (MED)** — HELD, **two new arms** (`C368-N1`, `C368-N2`) and **sharpened**: its "disagree on **4** components" is **13** when measured pointer-wise (§B.2); its own 5-row table is correct on its own terms and **contains neither** `entity_type` **nor** `revocation.status`. Its open DESIGN-Q *"which published schema is normative?"* now decides **five** carries: its own field set, `C24-M4`, `C24-M6`, `C60-B12`, and `C368-N1`. **Spec CORRECT — do not weaken §2.1/§2.2.**
- **C288-N2 (MED, HUB track)** — HELD. `hub/` moved 19 commits this window; C328's re-resolved anchors were **not** re-verified this pass (out of approved scope) — **flagged for C408**, since C328 established the anchors drift with `hub/` motion.
- **C328-N1 (LOW)** — HELD and **discharged in practice**: this ledger names every member.
- **C210-N1 · C172-N1/N2/N3 · C248-N1 · C248-N2** — HELD (all mirrors frozen).

### F.4 — Swept clean previously; check only whether they CHANGED, do not re-derive
`lct-jsonld.schema.json` + `lct-jsonld-vectors.json` (**10/10 PASS**, re-confirmed this pass as the §C control's basis) · `web4-policy/` (NEGATIVE gate, 0 commits) · `core/lct_binding/` (M2 evidence-only) · the `hub/` `*_lct_id: Uuid` population (**160 sites, internally consistent, not a widening**).

### F.5 — DEFERRAL ROW FOR C408 (this row is what makes this pass's scope a bounded choice, not truncation)

1. **`hub/`'s 19 window commits vs C288-N2's anchors** — not re-resolved here. `git log 89251abc..HEAD -- hub/hub-daemon/src/constellation.rs hub/hub-daemon/src/rest.rs`, re-resolve by content.
2. **The other 11 rows of §B.2** — only rows 4 and 12 were pursued. Rows 1/5 are C288-N1's own; rows 6–11 and 13 are **unexamined**, in particular **row 6** (`lct_id` pattern `^lct:` vs `^lct:web4:…`, which bears on `C24-H1`) and **row 8** (`lineage[].reason` mints `derived_from`, the same shape as `agent` one field over — **check whether it is registered anywhere**).
3. **`entity-jsonld.schema.json` vs `entity-types.md`** — this pass read only its `entity_type` enum. Never diffed as a pair.

---

## §G. Post-write re-runs at a different scope (v17), and what they caught

1. **CAUGHT — the §B totals** (jsonld 99 / raw 109). This session's policy review re-implemented the same stated method and got **117 / 111** — direction inverted. **Withheld rather than published** (§B.3). The 13 reproduced under both.
2. **CAUGHT — the inertness claim.** Drafted as "`lct.schema.json`'s only non-definition reference is `test_validation.py:101`." Repo-wide that is **false**: two `archive/` modules actually validate against it and `ledgers/reference/typescript/lct-document.ts` names it source of truth. Rescoped to **"inert to every automated gate"**, with the gate evidence (`pyproject.toml:84`, zero invokers) published. Caught by the policy review.
3. **CAUGHT — a missing corroborator.** `CHANGELOG.md:662`'s "all 16 entity types" was found on the post-write re-run, after the review had already supplied `lct-jsonld-validation.json:254`. Two independent "16" assertions became three; the finding moved from "a schema typo" to "a systemic belief."
4. **Re-run, held** — the controlled mutation, re-run with a **negative control** added (`not_real` → FAIL) to prove the enum is not vacuous. The first run omitted it and would have been inadmissible.
5. **Re-run, held** — every reviewer-supplied path token was resolved as written before adoption (`entity-types.md:257-258`, `§4.6:349`, `lct-jsonld-validation.json:254`, `schema_registry.json:1632`, `pyproject.toml:84`, `C288:113`/`:128`/`:132`/`:134`, `C328:169`/`:247`/`:315`, `c787452e` = 2026-03-20). **All 13 resolved.** Run because two of the previous fire's reviewer cites were fence lines.
6. **Re-run, held** — `git log -S '"agent"'` scoped to the schema file returns exactly the birth commit; the emitter sweep returns exactly one archived hit.
7. **CAUGHT — §E's own prose, and it is the worst error in this pass.** §E was drafted asserting *"Residue: empty. **No audit doc written since C328 cites this target or its subject matter.**"* The residue **is** empty and that half reproduced. The second sentence was **written before the sweep was run** and is **false**: **8** post-C328 audit docs cite the target by filename. Running it corrected the prose **and** surfaced the `C332:451` d4 hand-off, which is now the only cross-lineage route this pass emits. **An empty residue is a statement about a set difference, not about citation.** Publishing the inference instead of the measurement is the exact failure this section exists to catch, and it was mine, caught by re-running rather than re-reading — the C362 rule.

**Not re-derived, per the standing guards**: C328's §F.4 swept-clean set (checked only for change: unmoved) · the `hub/` `*_lct_id` population (**known population, not a finding**) · the six untracked `web4-standard/` trees (**C382's first work per `C342 §B.5`, not this slot's**).

---

## §H. Lessons

1. **Ask which artifact has standing before asking what it says.** v16 (*omits ≠ forbids ≠ requires*) tells you to check the **modality** of a constraint. It does not tell you to check whether the artifact asserting it **binds anything**. C328 applied v16 correctly and still got the wrong answer, because it read the modality off the file that no gate runs. **v45's caller-count question is a precondition for v16, not an alternative to it.** ⇒ *a constraint's modality is only as strong as its enforcer's caller count.*
2. **A schema pair is an artifact in its own right.** Eleven passes read these two files — separately. C328 even validated the same ten vectors against **both** and still never compared them **to each other**, because the vectors were the object of interest and the schemas were the instruments. **When two instruments are published as co-equal, the diff between them is data.** Both flagship fields sat in that diff for 145 days.
3. **A defect nothing exercises is invisible to every green gate, and that is exactly why it survives.** Nothing in the corpus emits `entity_type: "agent"`. The enum is a *permission*, and permissions are not exercised by conformance suites, which test that valid things pass and invalid things fail — never that the *set of valid things* is the right set. **A vector suite cannot audit an enum's membership; only a cross-artifact diff can.**
4. **The hedge does not propagate; the ledger line does.** C328 wrote the correct conditional at `:169` and the flat claim at `:315`. Three weeks later the flat claim is what an operator would act on. **Where a finding is conditional, the condition belongs in the ledger row, not only in the prose above it.**
5. **A review that falsifies your headline number is worth more than one that approves it.** The policy review killed the constraint totals by re-implementing the method rather than re-reading the output, rescoped the inertness claim from "unreferenced" to "inert to gates," and supplied two corroborating sites. Four of this pass's six §G entries are its work. **This is the fifth consecutive fire in which submitting a *measured* premise — not a plan — falsified something load-bearing before it shipped.**

---

**Verdict: 9th delta SERVED. Target byte-frozen (4th consecutive, 27 days), corpus-delta CLEAN against the spec prose (5th consecutive), ZERO mutation, 0 net-new against the spec prose.** Two MEDIUMs — `C368-N1` (the enforced schema's unregistered 16th entity type, executed with backed + negative controls, 145 days old, shipping in the wheel) and `C368-N2` (C328's adjudication of two operator carries from the gate-inert schema; `C24-M4`'s answer inverts) — both filed as arms on `C288-N1`'s open DESIGN-Q, none self-applied. C288-N1 sharpened 4 → 13 with the pointer table published; the constraint **totals withheld as method-unstable**; `C60-B12`'s premise falsified; the **v36 residue published as an empty negative** with a cross-lineage hand-off to `C332`'s deferral **d4** routed to C372; a 3-item deferral row pre-registered for C408; **7 corrections made before shipping — 4 mine (incl. §E's own prose), 3 from the policy review — all published rather than quietly fixed.** Rotation advances to **ISP (`inter-society-protocol.md`) = C370**.

---

## Review-gate block

```
surface: C368 audit pass (docs/audits/, read-only over the standard)   act: publish an audit record; route findings to the operator DESIGN-Q bundle
S: low/reversible [construct: no mutation of any spec, schema, vector, or code artifact; sole write is one new file under docs/audits/]
R: n/a [construct: no reachability-gated act]   W: n/a [construct: no consequential act performed on behalf of an identity]
O: pass [construct: §A.0 freeze verification and §A.3 pre-committed routing precede every claim in §C and §D]   A: pass [construct: this document + the PR commit record the act, its evidence, its instruments, and its withheld/failed measurements together]
V: n/a [construct: no irreversible act; every finding routed, none self-applied — the guardrail forbids the auditor amending the enum, the register, or the conformance vector]
verdict: PASS
```
