# C412 — `entity-types.md`, 10th delta audit

**Slot**: `web4-20260819-060000` · **Date**: 2026-08-19 · **Protocol**: Autonomous Session Protocol v2
**Target**: `web4-standard/core-spec/entity-types.md`
**Predecessor**: `docs/audits/C372-entity-types-9th-delta-2026-08-12.md` (PR #697)

**Enumeration rule (inclusive, stated per the standing rule):** the lineage's origin member
`docs/audits/entity-types-internal-consistency-2026-05-22.md` self-identifies as `# C8 Audit` and is
therefore invisible to a `C*`-glob, but it is cited **by name** in all successors. C332 verified this;
it is **not re-litigated here**. Counting it, this is the **12th pass** of the lineage and the
**10th delta**.

**Path-token root rule (published with the count, v39).** This document cites **49** distinct path
tokens. Unqualified tokens resolve under these roots, in this order: `core-spec/`, `protocols/`,
`schemas/`, `test-vectors/`, `rfcs/`, `submission/`, `implementation/sdk/` → **`web4-standard/`**;
`docs/`, `ledgers/`, `web4-core/`, `hub/`, `archive/` → **repo root**. The
`forum/nova/web4-sal-bundle/` mirrors of `entity-types.md`, `mrh-tensors.md` and
`web4-society-authority-law.md` are **excluded by name** and are never the referent. Every token was
resolved as written before shipping; 19 line anchors were additionally re-read at their cited line.

---

## §0. Freeze counters — all three published, none picked

Per C372's standing instruction (three counters exist and disagree):

| Counter | Value | Command |
|---|---|---|
| Passes over blob `a2dda417` | **6th** (C214/C252/C292/C332/C372/C412) | `git rev-parse HEAD:web4-standard/core-spec/entity-types.md` |
| Byte-freeze age | **36 d** (`1354e4c2`, 2026-07-14) | `git log -1 --format=%H%n%ad -- <target>` |
| **Inter-pass delta window** | **7 d** (C372 = 2026-08-12) | — |

`wc -l` = **804**. Zero mutation this pass: no spec, schema, SDK, vector, ledger or implementation
byte is touched. The only artifact created is this file.

*(Correction carried from policy review: the scope proposal said "audit the 36-day interval". 36 d is
the target's **freeze**; the **delta window** since C372 is **7 d**. Both are published above.)*

---

## §A. Carries held by construction

The target is byte-identical to the blob C372 audited (`a2dda417`). Every §A row C372 held —
7 C65 remediations, the §4-preamble count at `:281`, and the 9 standing carries
(C8-L3, C23-H1, C24-H1, B2/B9, B7, B10/B11, B12) — **holds by blob identity**. They are not
re-enumerated; `C372 §A` remains the enumeration of record.

Open cross-doc carries re-confirmed, **not re-charged**: `C292-N1` (role_definition ↔
`role-extension`), `C332-N2` (`slashed` overload, 3 SDK sites), `C332-N3` (3 broken inbound anchors
at `518+63=581`), `C372-N1/N2/N3`, `C176-N1/N2`, `C64-B2`, `C64-B7`.

---

## §B. C372 §G deferral ledger — 5/5 discharged, 4 NEGATIVE

### g1 — did any author ruling land? **NEGATIVE. `C372-N1` STANDS.**

```
$ git log -1 --format='%H %ad' -- web4-standard/schemas/entity-jsonld.schema.json
9dd8f06e5de2f5aa9bdc01d0070a5e8e125b6ea5  Mon Mar 23 04:07:06 2026 -0700     # 149 d
```

`$defs/EntityTypeRegistry.entity_types` (`entity-jsonld.schema.json:105-109`) still carries **no**
`minItems` / `maxItems` / `uniqueItems`.

> **MEASUREMENT HAZARD FOR SUCCESSORS.** A bare `grep -n "minItems\|uniqueItems"` on that file
> returns **3 hits** — `:52` and `:97` (`@context.minItems`) and `:66` (`modes.uniqueItems`) — none
> of them on `entity_types`. Read literally, the naive instrument reports the ruling as **landed**.
> The instrument must be scoped to the property the finding names, not the file.

### g2 — foreign vocabularies in the Specialized-Entity sections. **Its own denominator was wrong.**

C372 g2 reads: *"the **two** Specialized-Entity sections carry **9** sub-sections between them
(§10.1–10.4, §13.1–13.5)."* There are **three**:

```
$ grep -n "^## .*Specialized Entity" web4-standard/core-spec/entity-types.md
621:## 10. Specialized Entity: Dictionary          (§10.1–10.4  = 4)
685:## 11. Specialized Entity: Accumulators        (§11.1–11.3  = 3)   <-- dropped by g2
745:## 13. Specialized Entity: Policy              (§13.1–13.5  = 5)
```

True denominator **3 sections / 12 sub-sections**, not 2 / 9. §11 Accumulators was omitted
entirely. Executed over all 12 (v40 — a denominator is a domain):

| Sub-section | Foreign vocabulary | Owning artifact | Result |
|---|---|---|---|
| §11.2 `:700` | `listen_scope: ["ANNOUNCE","HEARTBEAT","CAPABILITY"]` | `protocols/web4-entity-relationships.md:348` ABNF `message-type = "ANNOUNCE" / "HEARTBEAT" / "CAPABILITY"` | **3/3 resolve — NEGATIVE, recorded** |
| §10.2 `:632-664` | 14 field names | `core-spec/dictionary-entities.md` | **14/14 resolve** |
| §10.2 trust block | `trust_requirements` vs `dictionary_trust_config` | `dictionary-entities.md:67` | **= `C64-B7`**, booked 5× (C94/C104/C132/C137/C176) — **NOT novel, not re-raised** |
| §13.3 `:765-773` | IRP contract | SAGE / `POLICY-ENTITY-REPOSITIONING.md` (external) | out of corpus; no resolvable register |
| §13.4 `:775-785` | metabolic states | `SOCIETY_METABOLIC_STATES.md` / `metabolic.py` | **already `C372-N2`** — not re-measured |
| §10.1/10.3/10.4, §11.1/11.3, §13.1/13.2/13.5 | prose, no foreign register | — | nothing to join |

**§11 has no "For complete specification, see …" pointer** (§10.4 `:683` has one, §13.5 `:796` has
one). Its normative home is in fact `protocols/web4-entity-relationships.md` §4.4 (`accumulator`
×12 there) — recorded as an observation, not charged: an uncited-but-correct delegation is not a
defect and the corpus does this deliberately elsewhere.

**g2 is the same defect class as §C's finding, one section-family over** — *"does a section of this
target name a vocabulary owned by another document?"* — and that is said here rather than letting
§C stand in for the row.

### g3 / g4 — §2.1 vs `entity-taxonomy.json` `expected`. **NEGATIVE.**

Coverage re-confirmed: `entity-taxonomy.json` carries **5 of 15** types
(`human, society, device, infrastructure, oracle`). Not charged — coverage ≠ defect (v43). The
third-witness comparison C372 never ran:

| Type | §2.1 Mode | vector `modes` | §2.1 Energy | vector `energy` |
|---|---|---|---|---|
| human | Agentic | `["agentic"]` | Active | `active` |
| society | Delegative | `["delegative"]` | Active (via citizens) | `active` |
| device | Responsive/Agentic | `["responsive","agentic"]` | **Active or Passive** | `active` |
| infrastructure | None | `[]` | Passive | `passive` |
| oracle | Responsive/Delegative | `["responsive","delegative"]` | Active (delivers results) | `active` |

**Modes 5/5 as sets. Energy 5/5** with one qualification: `device`'s *"Active or Passive"* is a
disjunction the scalar vector collapses — **already booked** as `C64-B2` and re-escalated at
`C332`'s reach-escalation ("the standard publishes three answers"). **Not re-raised.**

### g5 — `RFC-COMPOSITE-ENTITY-IDENTITY.md:62-100` (P1–P4) vs §3 / §7.2. **NEGATIVE.**

P1's composite→component `bound` edge matches §6.1's *Binding | Parent → Child*; the component→
composite `paired` **(role)** edge matches the §3.3/§6.2 role-pairing idiom (*"Can pair with:
Agents … to perform the role"*) rather than §6.1's *Pairing | Peer entities* literal reading. That
is a tension of reading, not a contradiction; §6.1's own examples already include `Agent ↔ Role`,
which is likewise not peer-symmetric. **No finding.** P2–P4 pin `t3-v3 §8.2` and `mrh-tensors`, not
this target.

---

## §C. Net-new — **C412-N1** [LOW-MED → operator / standard-editor; author ruling]

> **§5.3 `:533` is the standard's sole declaration of the LCT termination vocabulary
> `{"void","slashed"}` — a non-normative bullet (0 RFC2119 keywords in all of §5) prescribing a
> mutation to a status field the canonical LCT document defines no slot for; its only normative
> consumer is a MUST in `did-web4-method.md:134`, with 0 cross-citation in either direction.**

*(The drafted headline — "5 of the 6 LCT-status artifacts structurally cannot express it" — was
**killed by policy review** as a NON-JOIN dressed as a contradiction and a v69 base rate. See §F.)*

### C.1 The declaration and its modality

```
$ sed -n '529,536p' web4-standard/core-spec/entity-types.md
### 5.3 Entity Termination
When an entity ceases to exist:
- **LCT Marking**: Status changed to "void" or "slashed"          <-- :533
...
$ awk 'NR>=462 && NR<=537' web4-standard/core-spec/entity-types.md | grep -cE '\bMUST\b|\bSHOULD\b|\bMAY\b|\bSHALL\b'
0            # zero RFC2119 keywords in the whole of §5 (file total = 8)
```

Within `web4-standard/`, `void`/`slashed` as an *LCT status* occur in exactly two places:

| Locus | Text | Modality |
|---|---|---|
| `core-spec/entity-types.md:533` | `Status changed to "void" or "slashed"` | descriptive bullet, **0 RFC2119** |
| `core-spec/did-web4-method.md:134-136` | *"If the LCT status is `Void` or `Slashed`, resolution **MUST** set `didDocumentMetadata.deactivated = true`."* | **MUST** |
| *(weaker, `void` only)* `submission/draft-palatov-web4-core-00.txt:262` | `4. Termination: Marked as void but history preserved` | prose |

```
$ grep -c "did-web4\|did:web4" web4-standard/core-spec/entity-types.md      -> 0
$ grep -c "entity-types"        web4-standard/core-spec/did-web4-method.md  -> 0
```

**Cross-citation 0 in both directions.** The only normative consumer of the target's vocabulary does
not know the target exists, and the target does not know it has a consumer.

### C.2 The canonical document has no slot for it — **this is the defect**

`LCT-linked-context-token.md` is `did-web4-method.md:5`'s declared **Companion** — *"the LCT this
method projects."* It contains **zero** occurrences of `void` or `slashed`
(`git grep -ciE 'void|slash'` → exit 1). Its §2.3 Canonical Structure has 13 top-level keys:

```
['@context','@type','lct_id','subject','binding','birth_certificate','mrh',
 'policy','t3_tensor','v3_tensor','attestations','lineage','revocation']
```

**No `status`.** The only status in the canonical document is `revocation.status`, and §7.4
Revocation (`:513-527`) sets it to `"revoked"`.

Both governing schemas declare `"additionalProperties": false`
(`lct.schema.json` tail; `lct-jsonld.schema.json`), so the field §5.3 prescribes a change to
**cannot appear in a conformant LCT document at all**.

### C.3 Executed — matcher and negative control published

Harness: `jsonschema==4.26.0`, `Draft202012Validator(...).iter_errors(doc)` read directly (**not**
`implementation/sdk/web4/validation.py validate()`, which does not raise — C372's recorded hazard).
Control document: the standard's own MUST-PASS vector `lct-valid-001` from
`test-vectors/schema-validation/lct-jsonld-validation.json` (carries `revocation: {"status":"active"}`,
no top-level `status`).

| Mutation | `lct-jsonld.schema.json` | Message |
|---|---|---|
| *(unmutated control)* | **PASS** | — |
| `revocation.status = "revoked"` | **PASS** | — |
| `revocation.status = "suspended"` | **PASS** | — |
| `revocation.status = "void"` | **FAIL** | `'void' is not one of ['active','revoked','suspended']` |
| `revocation.status = "slashed"` | **FAIL** | `'slashed' is not one of [...]` |
| `revocation.status = "dormant"` | **FAIL** | `'dormant' is not one of [...]` |
| **`revocation.status = "banana"`** *(neg. control, v59)* | **FAIL** | `'banana' is not one of [...]` |
| top-level `status = "void"` | **FAIL** | `Additional properties are not allowed ('status' was unexpected)` |

The standard's own prescribed terminal marking fails its own schema **with the identical message as
a nonsense token**. Same result in the SDK:
`RevocationStatus("void") -> ValueError`, exactly as `RevocationStatus("banana")`.

### C.4 Denominator — 8 artifacts, matcher published, **counted as a base rate not an N-of-N (v69)**

Matcher: every in-corpus artifact (`archive/` excluded, exclusion stated) that defines a **closed**
vocabulary for an LCT's status.

| # | Artifact | Field | Vocabulary |
|---|---|---|---|
| 1 | `web4-standard/protocols/web4-lct.md:128` — **a spec** | `revocation.status` (REQUIRED) | `{active, revoked}` |
| 2 | `web4-standard/schemas/lct.schema.json:229` | `revocation.status` | `{active, revoked}` |
| 3 | `web4-standard/schemas/lct-jsonld.schema.json:265` | `revocation.status` | `{active, revoked, suspended}` |
| 4 | `web4-standard/implementation/sdk/web4/lct.py:71-74` | `RevocationStatus` | `{active, revoked, suspended}` |
| 5 | `web4-standard/implementation/sdk/tests/test_lct_jsonld_vectors.py:305` | `valid_statuses` | `{active, revoked, suspended}` |
| 6 | `ledgers/reference/go/lct/document.go:207,209-212` | `RevocationStatus` | `{active, revoked}` |
| 7 | `ledgers/reference/typescript/lct-document.ts:212` | `RevocationStatus` | `{active, revoked}` |
| 8 | `web4-core/src/lct.rs:58-67` (field `:106`) | **`Lct.status`** | `{active, dormant, void, slashed}` |

**Rows 1–7 are ONE derivation event with two variants** (± `suspended`), all descending from the
canonical `revocation` structure at LCT §2.3 / `web4-lct.md:128`. Reported as a **base rate**:
the `revocation.status` family is 7-strong and uniform; that is not seven independent confirmations
of anything. Row 8 is the only artifact in the other family.

Excluded and disclosed: `archive/reference-implementations/e2e_fullstack_demo.py:102`
(`status: str = "active"  # active, dormant, void, slashed`) — the exact 4-value twin of row 8, and
the **only** place `dormant` is grounded anywhere in the corpus. Also not counted separately:
`implementation/sdk/web4/schema_registry.json` vendors copies of rows 2 and 3 (the vendoring question is already
routed by C372).

### C.5 **The NON-JOIN, disclosed** — and what it means

`revocation.status` (rows 1–7, a nested revocation *record* whose companion `reason` vocabulary is
`{compromise, superseded, expired[, violation]}`) and `Lct.status` (row 8, a top-level *lifecycle*
state) are **different fields modelling different things**. `web4-core::Lct` has no `revocation`
field (`grep -i revocation web4-core/src/lct.rs` → 0); rows 1–7 have no top-level `status`.

So the finding is **not** "seven artifacts disagree with §5.3." It is:

> **The canonical LCT document has no lifecycle-status field at all, and `entity-types.md:533` is
> the only place in the standard that prescribes writing to one.**

That absence, not a vocabulary clash, is the charge.

### C.6 Consequence, and the self-scoping defense — severity capped at **LOW-MED**

`web4-core/src/did.rs:192-196` implements §5.2 exactly, and tests it:

```rust
// did.rs:192-196
/// A voided or slashed LCT resolves as deactivated.
pub fn for_lct(lct: &Lct) -> Self {
    Self { deactivated: matches!(lct.status, LctStatus::Void | LctStatus::Slashed) }
}
// did.rs:277-283  fn test_deactivation_reflects_status()  — lct.void() -> deactivated == true
```

It can do so **only** because `web4-core::Lct` carries a top-level `status` the standard's own LCT
schema forbids. An LCT revoked exactly as `LCT §7.4` prescribes (`revocation.status = "revoked"`)
leaves §5.2's antecedent **false** (v54 — the guard's antecedent is unreachable in that family).

Reach, measured: `git grep -w deactivated` over the corpus excluding `archive/` returns
`web4-core/src/did.rs` (4), `did-web4-method.md:135`, and `docs/designs/did-web4-mapping.md:100`.
The one **deployed** resolver, `hub/hub-daemon/src/rest.rs`, performs `did:web4` resolution
(`:2850`, `:2854`, `:10827`) and implements **no deactivation**: `git grep -w deactivated hub/` = **0**.

**Defense, recorded, and it is why this is LOW-MED and not MED:**
`did-web4-method.md:4` declares **"Status: Draft — Phase 0 implemented in `web4-core::did`
(reference)"**, and its design note `docs/designs/did-web4-mapping.md:99` writes the rule as
`LctStatus::Voided | Slashed` — **naming the Rust type directly**. §5.2 is therefore
*self-consistent against its own declared reference implementation*, which does implement it. The
defect is the standard-internal one in C.2, not a broken DID method.

*(Name drift, INFO: the design note writes `LctStatus::Voided`; the actual variant is `Void`
— `web4-core/src/lct.rs:63`.)*

### C.7 Novelty — per-LOCUS (v56), matcher published

```
$ git grep -ln 'did-web4-method' -- docs/audits/ web4-standard/docs/audits/   ->  11 files
$ git grep -ln 'did-web4-method' -- web4-standard/docs/audits/                ->   0 files
$ git grep -liE 'deactivat'      -- docs/audits/ web4-standard/docs/audits/   ->   0 files
```

Novelty holds **per-locus**: §5.2 / deactivation has never been read by any pass in either tree.
It does **not** hold at file granularity, and saying "merely cited" would be false:
`C294-errors-7th-delta-2026-07-30.md` mentions the file **16** times and admitted its **§5.1** to
the errors mirror set (`C294:273-294`, M1-PASS / M2-GENUINE / M3-ADMITTED).

**Standing constraint disclosed, not stepped over:** `C294:371` instructs *"do **not** convert them
into a defect charge without an operator ruling on N1 first."* Per **v51**, that disposition is
scoped to the predicate it was measured on — §5.1 (`notFound` / enumeration defense) — and §5.2 is a
different predicate. The constraint is therefore cited rather than treated as a bar; and it is one
more reason N1's charge is anchored on **`entity-types.md:533`**, not on `did-web4-method.md`.

**C332's clearance of `:533` does not deflate this (v51/v68).** `C332:273-274` cleared `:533`
explicitly and only for the C36 overload predicate — *"the **punitive** sense … consistent with
atp-adp §2.4"*. Whether the word is used in the punitive sense and whether the vocabulary it
declares is implementable are different questions; C332's control does not share this finding's
predicate.

### C.8 Remedy space (author's choice — **not self-applied**)

Two mutually exclusive shapes, exactly one of which the standard editor must pick:

- **(A) Retract.** §5.3 `:533` becomes `revocation.status` language: *"a revocation record is written
  with `status: "revoked"` and a `reason`"*, aligning with LCT §7.4. Then `did-web4-method.md` §5.2's
  antecedent must be restated over `revocation.status`/`reason`, and `web4-core::LctStatus` becomes
  the outlier (→ C448).
- **(B) Register.** `void`/`slashed` (and `dormant`) are promoted into the canonical LCT structure as
  a real lifecycle field, §5.3 gains RFC2119 modality, and rows 1–7 gain the field. Larger, but it is
  what the published whitepaper already tells readers (`docs/whitepaper-web/WEB4_Whitepaper_Complete.md:142`,
  `:366` — *"created → active → void/slashed"*).

An auditor choosing between these would itself be the W violation. **Routed, not applied.**

---

## §D. Routed, not charged

1. **→ C448 (LCT lineage) — a correction to its own pre-registered row.**
   `C408 §G.3 row 5` (`C408:356-364`, 2026-08-18) pre-registered
   `web4-core/src/lct.rs:58-67` for C448, describing it as *"a four-value vocabulary that intersects
   the spec's `{active, revoked}` in exactly one member"*, and instructing C448 to *"probe
   `web4-core`'s status surface against §7.4's `Effect: status = "revoked"`"*.
   **This pass holds a falsifier for that comparator and routes it rather than taking the row:**
   > `{active, revoked}` is **`revocation.status`** — a *different field* from `Lct.status`, so the
   > "intersects in exactly one member" figure compares across a non-join. **3 of the 4 `LctStatus`
   > members are spec-backed:** `Active` trivially; `Void` and `Slashed` by
   > **`entity-types.md:533`**, consumed by the **MUST** at `did-web4-method.md:134`. Only `Dormant`
   > is ungrounded in the standard — its sole corpus grounding is
   > `archive/reference-implementations/e2e_fullstack_demo.py:102`, which is also the exact 4-value
   > twin of `LctStatus` and suggests descent rather than independent design.
   > **C448 should probe against `entity-types.md` §5.3 *and* `did-web4-method.md` §5.2, not §7.4
   > alone.**

   **No `LctStatus` row is charged here.** C408 §G.3 row 5 named that artifact by exact line range
   one day before this pass; holding a falsifier for a routed row is a reason to route a correction,
   **not a licence to take the row** (v70). Credit: `C228:80` and `C266:27` (which routed it as an
   excluded false-mirror and said where it belonged), and `C408 §G.3` (which received it).

2. **→ operator / standard-editor, with the errors lineage (C414) notified.**
   The `did-web4-method.md` §5.2-vs-Companion tension (C.1/C.2). `did-web4-method.md` is not this
   pass's target; the charge above is anchored on `:533`. `C294:371`'s standing instruction is cited
   in C.7 and honoured — this is a route, not a defect charge against that file.

3. **→ C448 / whitepaper track — observation, downgraded from a proposed finding.**
   `docs/audits/whitepaper-sdk-coherence-2026-03-15.md:163-170` records row **A2 "Strong Alignment"**
   claiming whitepaper + core-spec + SDK *"agree on … lifecycle (creation/active/void/slashed)"*,
   noting only that *"the SDK has `SUSPENDED` revocation status not mentioned in the whitepaper …
   a reasonable SDK extension."* Measured: SDK `RevocationStatus` = `{active, revoked, suspended}`,
   containing **neither** `void` **nor** `slashed`; the intersection with the four-item lifecycle the
   row claims agreement on is `{active}`, **1 of 4**. The note's error is
   **"3 missing + 2 extra" described as "one extra"** — not the "two missing + one extra" this pass
   first drafted (arithmetic corrected by policy review). It is an **audit document**, its subject is
   the SDK↔whitepaper join, and it is not a rotation artifact ⇒ **recorded, routed, not charged.**
   156 days old, and it is the corpus's only standing three-way alignment record for the LCT
   lifecycle — which is a plausible reason the C.2 absence went unread this long.

---

## §E. v36 inbound set difference — **NEGATIVE, recorded**

Window **pre-registered before the sweep** (v26): tree `web4-standard/`, filetype `*.md`, root =
repo root, span = full history.

```
domain word   git grep -li "entity_type\|entity type" -- 'web4-standard/**/*.md'   -> 17
filename      git grep -lF "entity-types.md"          -- 'web4-standard/**/*.md'   -> 14
residue       comm -23 domain filename                                             -> 10
```

Residue (10, newest first by last-touch): `entity-types.md` *(the target appears in its own residue —
a file never writes its own name)*, `mrh-tensors.md` 2026-07-09, `multi-device-lct-binding.md`
2026-06-21, `dictionary-entities.md` 2026-06-13, `C33-identifier-scheme-consolidation-audit` 2026-06-05,
`implementation/sdk/README.md` + `implementation/sdk/CHANGELOG.md` 2026-05-19, `protocols/web4-lct.md` 2026-02-17,
`ALIGNMENT_PHILOSOPHY.md` 2025-12-29, `protocols/web4-dictionary-entities.md` 2025-09-11.

**0 residue files postdate C372 (2026-08-12).** The instrument yielded on five earlier fires; it did
not yield on C372 and does not yield here. Recorded so the positives stay interpretable.

> **Instrument note (v47/v48).** `did-web4-method.md` — the source of this pass's entire yield — is
> in **neither** set. It contains no `entity_type`/`entity type` (invisible to the domain sweep) and
> no `entity-types.md` (invisible to the citation sweep). It was reached by walking the **vocabulary**
> (`void`/`slashed`) out of the target's own §5.3. A citation query cannot return an orphan; neither
> can a domain-word sweep whose word the orphan happens not to use.

---

## §F. Own-error log — all caught pre-ship

1. **Four citations off by one**, all found by policy review re-running them:
   `did-web4-method.md` `:133-135` → **`:134-136`**; `lct-jsonld.schema.json` `:264` → **`:265`**;
   Go `document.go:206-211` → type **`:207`**, consts **`:209-212`**; `did.rs` test `:279-284` →
   **`:277-283`**. Path tokens are their own class and every one must be resolved as written.
2. **Denominator was 6; true value 8.** The two misses were the most damaging kind: **row 1 is a
   *specification*** (`protocols/web4-lct.md:128`, `status (REQUIRED)`), not an implementation — a
   finding about what the standard declares that omitted a declaring artifact.
3. **Called `:533` "normative."** It carries **0 RFC2119 keywords**, and all of §5 does. The whole
   modality claim was wrong in the direction that flattered the finding.
4. **Headline killed — 20th consecutive pass** whose drafted headline or central premise policy
   review falsified. The draft ("5 of 6 artifacts structurally cannot express it") was a **NON-JOIN
   dressed as a contradiction** plus a **v69 base rate**: it counted one derivation event seven
   times, and it compared `revocation.status` against `Lct.status` as though they were one field.
   The surviving finding is smaller, target-anchored, and true.
5. **Missed the self-scoping defense entirely** (`did-web4-method.md:4` Draft/Phase-0-in-`web4-core`;
   `did-web4-mapping.md:99` naming the Rust type). It caps severity, and not reporting it would have
   been a MED charge on a LOW-MED fact — the v45 discipline: check whether the inertness is
   **disclosed at the point of use** before charging it. Here it is disclosed in the document's own
   header.
6. **Second candidate's arithmetic wrong** — drafted "two missing + one extra", true value
   **"3 missing + 2 extra"**; and it was drafted as a charge when its subject is another lineage's.
7. **Interval mis-stated** as 36 d; the delta window is **7 d**.
8. **Novelty cell drafted as "~8 audit docs, all merely cited"** — true value **11**, and "all merely
   cited" is false (`C294` read §5.1 substantively, 16 mentions, and left a standing instruction).
   Novelty holds per-**locus**, not per-file.
9. **Reviewer corrections independently re-verified (v52): all 13 correct, zero reviewer errors this
   pass.** Recorded because the last four passes each found at least one bad reviewer cell, and a
   clean run is data about the reviewer, not an excuse to stop checking.

---

## §G. Deferral ledger for the next pass (**C452**) — row count 5, members named

**Do NOT inherit this as a mirror set — it is what C412 did *not* measure.**

1. **`entity-jsonld.schema.json` vs `entity-types.md` §2.1 as a full field-by-field pair diff.**
   Third lineage now carrying it (`C408 §G.3` row 2 carries it too, from the LCT side). `C372-N3`
   served the *reachability* half; the diff itself is still untaken.
2. **The other 11 top-level schemas** — does any ship MUST-PASS vectors contradicting its own spec?
   `C372` d4 routed this per-slot rather than sweeping (C120→C121 hazard). Remaining:
   `acp`, `atp`, `attestation-envelope`, `capability`, `dictionary`, `r7-action`, `t3v3`.
3. **§4's eight SAL roles (§4.1–4.8) against their implementers, in order.** This pass walked §5, §6,
   §10, §11, §13. §4 is the largest enumerated list in the target (`Society, Authority, Law Oracle,
   Witness, Auditor, Agent, Client, Effector`) and only `Effector` has ever been probed
   (SDK mirror = 0, routed INFO). v69's question — *what does the spec declare that nothing
   implements* — has not been asked of §4.
4. **`§5.1`'s ten-step creation list** (`:468-477`) vs `web4-society-authority-law.md` §2.1–§2.2,
   which §5.1's own note (`:481-486`) names as the normative home. Steps 6/7/10 (witness quorum,
   law-oracle binding, ledger inclusion proof) are the SAL-required elements the note says the
   pseudocode omits — is the **ten-step list** itself complete against SAL, or only the pseudocode?
5. **Did the author ruling land?** One `git log` on `entity-types.md` + one grep for a `status`
   field entering `LCT-linked-context-token.md` §2.3 or either LCT schema. Cheap, and it decides
   whether `C412-N1` stands or retires.

**Next entity-types delta ≈ C452.**

---

## §H. Accountability self-audit

**n/a — no surface.** This pass creates one document under `docs/audits/` and mutates nothing. No
path a caller can drive is created or changed, and no consequential act (sign, admit/join, assign
role, amend law/policy, read/release a secret, spend/transfer, mutate governed state, emit an
outward message) is reachable from anything added here. `C412-N1`'s two remedies are mutually
exclusive normative choices belonging to the standard editor; an auditor taking either would be the
W violation, which is why §C.8 states the space and stops.

---

*Audit produced under Autonomous Session Protocol v2 by `legion-web4-20260819-060000`.
Policy review: **REVISE** → 13 changes required; **all 13 adopted**. The review killed the drafted
headline (NON-JOIN + v69 base rate), corrected 4 citations, corrected the denominator 6→8 including
a **specification** the pass had missed, corrected the modality claim (`:533` is non-normative),
supplied the self-scoping defense that caps severity, corrected the novelty cell 8→11 and
"merely cited"→false, corrected the second candidate's arithmetic, and ruled the ownership **SPLIT**
— charge the `entity-types.md:533` subject, route every `LctStatus` subject to C448.
**20th consecutive pass whose headline or central premise policy review falsified.***
