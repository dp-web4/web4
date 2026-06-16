# C64 Audit: `entity-types.md` — 2nd Delta Re-Audit

**Date**: 2026-06-16
**Auditor**: Autonomous session (Legion, web4 track) — firing `120047`, LEAD voice
**Document**: `web4-standard/core-spec/entity-types.md` (739 lines)
**Lineage**: C8 first-pass (2026-05-22, 10 findings, 9 remediated) → C26 first delta (2026-06-02, 5 new + 1 INFO, 4 autonomous remediated in #260) → **C64 (this audit)**
**Methodology**: C-series internal-consistency **2nd delta re-audit**, same class as C60 (LCT) and C62 (ISP). The target is **byte-identical to its C26 remediation** (`#260`, `e1aa5ae6`, 2026-06-02 — last commit to touch the file). Per the **C56 method**, §A therefore audits the C26 remediation's own *site-enumeration completeness* (did the fix reach every instance?), not merely "did the fixed site hold." Per the **C62 lesson**, §A also re-verifies every prior design-Q carry against the *current* corpus, **bidirectionally** (some resolve downstream, some harden). §B is a primitive-clustered, refute-by-default multi-agent finder workflow. §C is a primitive-clustered blindspot pass. §D routes findings for the C65 remediation turn.
**Cross-spec authorities re-read this session** (passages re-read, not recalled): SAL `web4-society-authority-law.md` §2.2 (`Web4BirthCertificate`); `society-roles.md` §2 (base-mandatory roles); `LCT-linked-context-token.md` `subject` format; SDK `entity.py` (15-type registry, modes, energy patterns).

---

## §A. Verification of Prior Findings (C8 + C26)

### A.0 Byte-stability + structural integrity

entity-types.md is unchanged since the C26 remediation (#260). All C8 structural renumbering (the bulk of C8's work) remains intact: §1–§14 with clean `### 3.1–3.5`, `### 4.1–4.7`, `### 5.1–5.3`, `### 6.1–6.2`, `### 7.1–7.3`, `### 8.1–8.2`, `### 10.1–10.4`, `### 11.1–11.3`, `### 12.1–12.2`, `### 13.1–13.5` — **zero duplicate section numbers, zero heading-level errors**. The 9 remediated C8 findings (H1–H3, M1–M4, L1, L2) all **HOLD**. C8-L3 (the §12↔§3.1 citizen-example redundancy, content-merge) **carry persists**, still correctly deferred (non-contradictory).

### A.1 — FLAGSHIP: C26-H1 remediation INCOMPLETE — base-right VALUE `exist` ≠ SAL canonical `presence`; provenance note over-claims a full match

**Lines**: §3.1 L153, §6.2 L493; cross-spec SAL §2.2 L57.

The C26 remediation (#260) renamed the §3.1 birth-cert KEYS `initialRights`/`initialResponsibilities` → `rights`/`obligations` to match SAL canonical, and added a provenance note (L160–167) asserting:

> "The fields `entity` through `obligations` **match** the canonical `Web4BirthCertificate` defined in `web4-society-authority-law.md` §2.2 — in particular the rights/obligations keys are `rights`/`obligations` (SAL canonical)…"

But the remediation fixed only the KEYS, not the VALUES. The actual canonical VALUE diverges:

| | entity-types.md | SAL §2.2 canonical |
|---|---|---|
| `rights` (first element) | `"exist"` (§3.1 L153) | `"presence"` (SAL L57) |
| prose echo | "base rights: **Exist**, interact, accumulate reputation" (§6.2 L493) | — |

So an implementer reading the §3.1 note ("the fields match canonical") and populating `rights: ["exist", …]` produces an object whose `rights[0]` differs from SAL's `rights: ["presence", …]`. The note's "match" claim is **technically false at the value level** — the precise failure class the C56 site-enumeration check exists to catch (cf. C56-A1: a remediation that fixed the heading but missed an enumeration site). `"presence"` is also the semantically intended term given Web4's presence-reframing (`§1` of this very doc is titled "Core Concept: Entities with **Presence**"); `"exist"` is the stale value.

**Disposition**: **autonomous-actionable** (C65). Change `"exist"` → `"presence"` at §3.1 L153 and the prose at §6.2 L493 ("Exist" → "Presence"), aligning the VALUE to SAL canonical and making the §3.1 provenance note true. (The FIELD-SET question — `ledgerProof`/`parentEntity` superset — remains the separate OPEN design-Q C23-H1; not touched here.)

### A.2 — C26-M1/L2 remediation notes cite C25-H1 as an "open design question" — but C25-H1 RESOLVED downstream

**Lines**: §4 preamble note L281; §4.2 scope note L305; (§3.5 has no such ref).

C26-M1 (Authority/Sovereign) and C26-L2 (the "two sevens") were both remediated with notes that defer the role-name/role-list canonicalization to **"C25-H1"**, described as **open**:

- L281: "…The canonical home of the base-mandatory role list **is an open design question; see C25-H1**."
- L305: "Reconciling the role *name* across these specs … **is an open design question (see C25-H1)**…"

Per the C62 audit (`docs/audits/C62-…-2026-06-16.md` §A, headline), **C25-H1 is RESOLVED downstream** by the C51 remediation (#318): `SOCIETY_SPECIFICATION.md` §1.2.5 now attributes the seven base-mandatory roles to **`society-roles.md` §2** as their canonical home (society-roles §2.1–§2.7 enumerates them). The three-way 7-role drift is closed. Therefore entity-types.md's two notes are now **stale**: they label as "open" a design question the corpus has already answered. This is the *resolution* direction of the C62 bidirectional-carry lesson (the opposite of C25-M1/L1, which hardened).

**Disposition**: **autonomous-actionable** (C65). Update L281 + L305: replace "is an open design question; see C25-H1" with a statement that `society-roles.md` §2 is the canonical home of the base-mandatory role list (resolved per SOCIETY_SPEC §1.2.5 / C51), keeping the substantive scoped-vs-root and two-sevens clarifications intact. Note this does NOT reopen the role-*name* reconciliation (SAL "Authority Role" vs society-roles "Sovereign") if that remains genuinely unsettled — but it must stop citing the *role-list home* as open.

### A.3 — C26-M2 / INFO1 (LCT-ID format) — PERSISTS, correctly cross-track

**Lines**: §13.2 L697 (`policy:<name>:<version>:<hash>`); pervasive `lct:web4:*`; cross-spec LCT-spec L65/L595 (`subject: "did:web4:key:z6Mk…"`).

Re-verified: LCT-spec still uses `did:web4:key:*` for the LCT `subject`; entity-types still uses `lct:web4:*` pervasively plus the `policy:*` form in §13.2. The three-style divergence is unchanged and remains a facet of the **OPEN** design-Q **C24-H1** (LCT-ID 4-way divergence, confirmed still open per C60 carries). Correctly deferred at #260; **persists, no new autonomous action** — do not self-resolve.

### A.4 — C26-L1 (Society reframe) HOLDS

§4.1 "Society (entity-type capabilities)" reframe (Society is an entity type, not a fillable role; apex role → §4.2) is intact at L283–290. No regression.

### A.5 Prior-finding verdict table

| ID | Origin | Issue | C64 status |
|----|--------|-------|-----------|
| C8 H1/H2/H3 | structural renumbering | §3/§4/§5 number corruption | **HOLD** — clean §1–§14, zero dups |
| C8 M1–M4 | heading level / notation / misfile / xref | — | **HOLD** |
| C8 L1/L2 | blockchain comment / self-ref | — | **HOLD** |
| C8 L3 | §12↔§3.1 redundancy | deferred content-merge | **CARRY PERSISTS** (still deferred) |
| C26 H1 (partial) | birth-cert field-name align | keys fixed | **INCOMPLETE → A.1** (value `exist`≠`presence`; note over-claims) |
| C26 M1 (partial) | Authority scoped-vs-root note | applied | **HOLD**, but **A.2** staleness (cites C25-H1 open) |
| C26 M2 / INFO1 | LCT-ID divergence | cross-track | **PERSISTS** (A.3), C24-H1 open |
| C26 L1 | §4.1 Society reframe | applied | **HOLD** |
| C26 L2 | "two sevens" note | applied | **HOLD**, but **A.2** staleness |

**SDK / entity-type-count check (binding note 3)**: SDK `entity.py` registers exactly **15** `EntityType` entries; names + order match §2.1 exactly (Human, AI, Society, Organization, Role, Task, Resource, Device, Service, Oracle, Accumulator, Dictionary, Hybrid, Policy, Infrastructure). Energy patterns match (Resource/Accumulator/Infrastructure = PASSIVE; rest ACTIVE; Device = ACTIVE in SDK vs spec "Active or Passive" — minor, carried to §B taxonomy lens). **Closed-15 is consistent across spec ↔ SDK.**

---

## §B. NEW Findings (primitive-clustered, refute-by-default workflow)

**Method**: workflow `wf_e49e7afc-fb0` — 8 primitive-clustered finder lenses (birthcert, roles, energy, taxonomy, normative, specialized, internal, xref), each `Explore` + refute-by-default, fed the prior-audit DEMOTED list; then a per-candidate adversarial verifier (refute-by-default). **26 raw → 21 survived verify → 5 refuted at verify**. Synthesis-time dedup collapsed the 21 survivors to **11 distinct** findings + **1 refuted at synthesis** (B8) + **1 folded into §A** (B13→A.3). The exist/presence value (A.1) was independently re-found by **3** lenses — strong corroboration, not triple-counted. Two cross-doc claims (B7 dictionary key, B8 path) were re-verified by hand before assertion (binding note 4 loose-pattern sweep).

| ID | Sev | Type | Title |
|----|-----|------|-------|
| B1 | MED | autonomous | §3.1 birth-cert witness IDs lack the canonical colon |
| B2 | MED | cross-track | SDK cannot represent a Passive Device (§2.1/§2.3 vs entity.py) |
| B3 | MED | autonomous | Hybrid "Mixed" mode is undefined in §2.2 |
| B7 | MED | cross-track | Dictionary trust-config key name diverges from owning spec |
| B4 | LOW | autonomous | Infrastructure row puts "Passive" in the Mode column |
| B5 | LOW | autonomous | §4 preamble's "seven subsections … SAL-specific roles" includes Society (a non-role) |
| B6 | LOW | autonomous | §2.3 overloads "slashed" vs atp-adp-cycle's punitive slashing |
| B9 | LOW | design-q | Task energy "Active (when R6-capable)" vs SDK fixed ACTIVE |
| B10 | LOW | design-q | §13 Policy lacks an LCT-structure JSON example |
| B11 | INFO | design-q | §13 frames SAGE/IRP integration as if Web4-normative |
| B12 | INFO | cross-track | §2.3 Passive-reputation lacks cross-ref to atp-adp §4.2 |

### B1 — §3.1 birth-cert witness IDs lack the canonical colon (`lct:web4:witness1` vs `lct:web4:witness:1`)

**Lines**: §3.1 L151; cross-spec SAL §2.2 L55; internal §4.7 L392.

§3.1 L151 writes witnesses as `["lct:web4:witness1", "lct:web4:witness2"]` (no colon before the discriminator). SAL canonical §2.2 L55 uses `["lct:web4:witness:1", "lct:web4:witness:2"]`, and **entity-types.md's own §4.7 Agency Grant L392** uses the colon form `["lct:web4:witness:A"]`. So §3.1 is the outlier against both SAL and itself. This is the **second VALUE/format site the C26-H1 provenance note misses**: the L160 note claims "the fields `entity` through `obligations` match the canonical … §2.2," but the `witnesses` value format does not. Pairs with A.1 — together they show the C26 "match" claim was key-only.

**Disposition**: **autonomous-actionable** — change §3.1 L151 to the colon form. (Trivial; the colon form is canonical across SAL, LCT-spec, all sister docs, and §4.7.)

### B2 — SDK cannot represent a Passive Device (§2.1 "Active or Passive" + §2.3 passive-device examples vs `entity.py` hardcoded ACTIVE)

**Lines**: §2.1 L28, §2.3 L78/L100–101; SDK `entity.py` Device entry (energy=ACTIVE, can_r6=True).

§2.1 lists Device energy as **"Active or Passive"**, and §2.3 explicitly classes **"Non-autonomous devices (sensors, actuators)" as Passive Resources that "Cannot process R6 transactions."** But the SDK `EntityTypeInfo` for Device hardcodes `energy=EnergyPattern.ACTIVE` with `can_r6=True` — there is no per-instance energy, so a sensor/actuator Device cannot be modeled as Passive per the spec's metabolism. C8 reported "full SDK compliance"; this is a divergence the first-pass missed (it only spot-checked names/modes). The spec is **internally consistent** (table + §2.3 agree); the **SDK** is the simplified mirror.

**Disposition**: **cross-track** (SDK). Either make Device energy per-instance (map AGENTIC→ACTIVE, RESPONSIVE→PASSIVE) or document in the spec that the SDK collapses Device to ACTIVE and passive hardware should be typed `Infrastructure`/`Resource`. Couples B9 (same table-conditional-vs-SDK-fixed pattern for Task).

### B3 — Hybrid "Mixed" mode is undefined in §2.2

**Lines**: §2.1 L33 (Hybrid Mode = "Mixed"); §2.2 L41–57 (defines only Agentic / Responsive / Delegative).

The §2.1 table gives Hybrid the Mode **"Mixed"**, but §2.2 enumerates exactly three behavioral modes and never defines "Mixed." Every other multi-mode row uses slash notation (`Responsive/Agentic`, `Responsive/Delegative`). The SDK interprets Hybrid as the union of all three modes, but that interpretation is nowhere stated in the spec.

**Disposition**: **autonomous-actionable** — either add a one-line "Mixed = exhibits all three modes" to §2.2, or change the table cell to `Agentic/Responsive/Delegative` for consistency with the other rows.

### B7 — Dictionary trust-config key name diverges from the owning spec

**Lines**: §10.2 L585 (`trust_requirements`); cross-spec dictionary-entities.md §2.2 L67 (`dictionary_trust_config`).

§10.2's Dictionary LCT example nests the `{minimum_t3:{talent,training,temperament}, stake_required:100}` block under the key **`trust_requirements`**. The owning spec dictionary-entities.md §2.2 L67 nests the **identical** block under **`dictionary_trust_config`**. (dictionary-entities.md does also use `trust_requirements` at L189 — but that is a *translation-request's* trust gate, `request.trust_requirements.minimum`, a different object.) So the dictionary entity's own trust-config block has two different top-level key names across the two core-spec files — a wire/schema hazard for any consumer round-tripping the structure. Verified by hand (not recalled).

**Disposition**: **cross-track** — align entity-types §10.2 to `dictionary_trust_config` (dictionary-entities.md is the owning spec), or escalate the naming to the dictionary-entities owner. (This is distinct from the demoted §10.2-is-a-subset observation; it is a key-name contradiction, not incompleteness.)

### B4 — Infrastructure row puts "Passive" in the Mode column

**Lines**: §2.1 L35.

The Infrastructure row lists **"Passive"** in the **Mode** column and "Passive" again in the Energy-Pattern column. Per §2.2, Modes are {Agentic, Responsive, Delegative}; "Passive" is an energy pattern, not a mode. The SDK correctly gives Infrastructure an empty mode set. The cell is a terminology slip.

**Disposition**: **autonomous-actionable** — set the Infrastructure Mode cell to empty / "None" (Infrastructure is the only type with no behavioral mode).

### B5 — §4 preamble's "seven subsections … are the SAL-specific roles" counts Society, which §4.1 says is not a role

**Lines**: §4 preamble note L281; §4.1 L283–284.

The L281 note (added by C26 remediation) says "The **seven** subsections below (Society, Authority, Law Oracle, Witness, Auditor, Agent, Client) are the **SAL-specific roles**." But §4.1 (also from the same remediation) states "**Society** is an *entity type* (§2.1), **not a role** an entity fills." So the "seven roles" framing self-contradicts: there are **six** roles (§4.2–§4.7) plus Society-as-hosting-context (§4.1). This is a remediation-introduced internal tension (the L281 note and the §4.1 reframe were added together but not reconciled on the count).

**Disposition**: **autonomous-actionable** — reword L281 to "the **six** role subsections below (Authority, Law Oracle, Witness, Auditor, Agent, Client) are the SAL-specific roles; §4.1 describes Society as the entity-type context that hosts them." (Couples A.2 — both edit the L281 note region; do them together in C65.)

### B6 — §2.3 overloads "slashed" against atp-adp-cycle's punitive-slashing definition

**Lines**: §2.3 L91, L102; cross-spec atp-adp-cycle.md §2.4.

§2.3 describes Passive-Resource maintenance as "ADP **SLASHED** (permanently consumed)." atp-adp-cycle.md §2.4 reserves "slashing" for a **punitive, authority-executed, evidence+witness-gated destruction of ATP for law violations** (removed from `total_supply`). Using "slashed" for routine, automatic passive-maintenance discharge overloads a term that the ATP/ADP SSOT gives a specific governance meaning. No functional break (different token states, different mechanisms), but a terminology collision in the canonical-equation vocabulary.

**Disposition**: **autonomous-actionable** (low priority) — reword §2.3 "slashed" → "consumed"/"destroyed via maintenance," optionally with a one-line note distinguishing it from atp-adp §2.4 punitive slashing.

### B9 — Task energy "Active (when R6-capable)" vs SDK fixed ACTIVE; Task omitted from §2.3 R6-capable list

**Lines**: §2.1 L26; §2.3 L80; SDK Task entry (ACTIVE, can_r6=True).

§2.1 gives Task the conditional energy "Active (when R6-capable)," but §2.3's list of R6-capable Responsive entities names only "Oracle, Dictionary, Service" — Task is absent — while the SDK gives Task an unconditional ACTIVE/can_r6. The canonical metabolism status of a non-R6 Task is left undefined (does it decompose into a Resource?).

**Disposition**: **design-q** — whether a non-executable Task is a distinct passive state or is modeled as a Resource is a genuine design question (couples B2's Device pattern). Defer to operator; the safe interim if desired is to add Task to the §2.3 R6-capable list to match SDK.

### B10 — §13 Policy lacks an LCT-structure JSON example

**Lines**: §13 (L680–731); cf. §10.2 (Dictionary), §11.2 (Accumulator).

Dictionary (§10.2) and Accumulator (§11.2) each carry a full LCT-structure JSON example; Policy (§13) provides only a characteristics table. Not a contradiction — the canonical LCT structure lives in LCT-spec — but an asymmetry among the three "specialized entity" sections.

**Disposition**: **design-q / editorial** — optionally add a §13 Policy LCT JSON example mirroring §10.2/§11.2. Low priority.

### B11 — §13 frames SAGE/IRP integration as if Web4-normative

**Lines**: §13.1 L689 ("Integrate with SAGE's IRP plugin architecture via PolicyGate" listed as a defining characteristic); §13.3 L700–708.

§13.1 lists SAGE-IRP integration among Policy's defining characteristics, and §13.3 details PolicyGate energy functions / convergence / ATP budgeting. Per `POLICY-ENTITY-REPOSITIONING.md`, PolicyGate is an **optional** SAGE plugin — "Web4 PolicyEntity works without SAGE." §13.3's "When integrated" conditional softens this, but §13.1's characteristic bullet reads as mandatory.

**Disposition**: **design-q** — clarify §13.1 that SAGE/PolicyGate is an optional runtime, not a Web4 requirement. Low priority (the conditional in §13.3 mitigates).

### B12 — §2.3 Passive-Resource reputation lacks an explicit cross-ref to atp-adp §4.2

**Lines**: §2.3 L103, L114–117; cross-spec atp-adp-cycle.md §4.2.

§2.3 says Passive Resources earn a "Reputation Metric: Utilization frequency × effectiveness" and "no reputation updates." atp-adp-cycle.md §4.2's fractal T3/V3 value cascade correctly omits Passive Resources (they use utilization metrics, not reputation tensors). The specs are **already consistent**; what's missing is only an explicit cross-ref noting the separation, to prevent a reader inferring Passive Resources feed the tensor cascade.

**Disposition**: **cross-track** (nicety) — add a one-line cross-ref. Lowest priority; not a defect.

### B8 — REFUTED at synthesis (false positive)

A finder flagged the L731 backtick reference `docs/history/design_decisions/POLICY-ENTITY-REPOSITIONING.md` as a "broken relative path" needing `../../`. **Refuted**: web4 core-spec uses **repo-root-relative backtick paths** as a documented convention for `docs/` references (e.g. `did-web4-method.md` L6 `docs/designs/…`, `lct-capability-levels.md` L711 `docs/audits/…`). L731 follows the convention exactly; it is a reference, not a markdown link. No action. (Recorded so a future audit doesn't re-raise it.)

---

## §C. Auditor-Blindspot Pass (primitive-clustered)

Per `auditor-blindspot-pattern`, re-read clustered by primitive (not section order):

- **BirthCertificate primitive** (§3.1 JSON-LD, §5.1 pseudocode+10-step list, §12.2 prose, vs SAL §2.2): the value/format gaps are **A.1** (rights `exist`≠`presence`) and **B1** (witness colon). The §5.1 pseudocode `birth_cert` dict (omits law-oracle digest / genesis / rights) is **correctly self-disclaimed** as illustrative (L416–421, added by C26) — the verifier refuted a re-raise of it. Permanence ("cannot be revoked") is stated consistently in §3.1, §3.4 L244, §5.1, §6.2 — **clean**.
- **Role-taxonomy primitive** (§3.4, §3.5 table, §4, vs society-roles §2): **A.2** (C25-H1 resolved → notes stale) + **B5** (six-vs-seven). The §3.5 example-role names (Mediator, Diplomat, Recovery-Authority, Architect, Validator, Governance-Council, Steward, Membership-Authority) were spot-checked against society-roles.md — they appear in its context-mandatory/optional tiers; no invented orphan surfaced (the `roles` finder raised none). **Clean beyond A.2/B5.**
- **Energy-metabolism primitive** (§2.1 table, §2.3, vs SDK + atp-adp): **B2** (Device), **B9** (Task), **B4** (Infrastructure mode cell), **B6** (slashed), **B12** (passive-rep cross-ref). This is the densest new cluster — all at the table↔SDK↔atp-adp boundary, consistent with the "drift concentrates at shared-primitive boundaries" pattern from C25/C26.
- **LCT-identifier primitive** (`lct:web4:*`, `policy:*` §13.2, `did:web4:*` LCT-spec): **A.3** + folded **B13** (the §13.2 "LCT Format" label may actually name an internal entity_id, a new facet) — all ride **C24-H1** (open). **Clean beyond the known design-Q.**
- **Specialized-entity primitive** (Dictionary §10, Accumulator §11, Policy §13): **B7** (dictionary key), **B10/B11** (Policy). Accumulator §11 surfaced nothing.

No contradiction surfaced beyond the findings above. Consistent with C26's observation that entity-types.md drift is downstream of the primitives its sibling specs co-define.

## §D. Disposition Summary & C65 Routing

| ID | Sev | Disposition | Coupled carry |
|----|-----|-------------|---------------|
| A.1 | (flagship) | **Autonomous** — `exist`→`presence` §3.1 L153 + §6.2 L493; makes provenance note true | C23-H1 (field-set, separate) |
| A.2 | — | **Autonomous** — L281/L305 stop citing C25-H1 "open"; cite society-roles §2 canonical | C25-H1 **RESOLVED** (C51 #318) |
| A.3 | — | **Cross-track** — LCT-ID divergence persists; do not self-resolve | C24-H1 (open) |
| B1 | MED | **Autonomous** — §3.1 L151 witness colon form | (pairs A.1) |
| B2 | MED | **Cross-track** — SDK Device per-instance energy, or spec note | couples B9 |
| B3 | MED | **Autonomous** — define "Mixed" in §2.2 or slash-notate §2.1 L33 | — |
| B7 | MED | **Cross-track** — align §10.2 key to `dictionary_trust_config` | dictionary-entities owner |
| B4 | LOW | **Autonomous** — Infrastructure Mode cell → empty/None | — |
| B5 | LOW | **Autonomous** — L281 "seven"→"six roles + Society context" | couples A.2 |
| B6 | LOW | **Autonomous** — §2.3 "slashed"→"consumed" | atp-adp §2.4 vocab |
| B9 | LOW | **design-q** — Task non-R6 metabolism | couples B2 |
| B10 | LOW | **design-q** — Policy LCT JSON example | — |
| B11 | INFO | **design-q** — SAGE optionality framing in §13.1 | — |
| B12 | INFO | **Cross-track** — passive-rep cross-ref to atp-adp §4.2 | — |
| B8 | — | **REFUTED** — repo-root backtick path convention, not broken | — |

**Autonomous-actionable for the C65 remediation turn (7)**: A.1, A.2, B1, B3, B4, B5, B6. All are entity-types.md-only edits; A.1+B1 jointly repair the C26-H1 provenance "match" claim; A.2+B5 jointly repair the L281 region.

**Cross-track (4, do NOT self-resolve)**: A.3/B13 (LCT-ID → C24-H1), B2 (SDK Device energy), B7 (dictionary key → dictionary-entities owner), B12 (atp-adp cross-ref nicety).

**Design-Q (3, operator)**: B9 (Task metabolism), B10 (Policy LCT example), B11 (SAGE optionality framing).

**No new design-Q opened.** A.1/B1 are the value/format completion of the already-tracked C26-H1; A.3/B13 ride C24-H1; A.2/B5 are the *downstream-resolution* cleanup of C25-H1.

---

## §E. Lessons (for memory)

1. **The C56 site-enumeration method paid out again, twice.** A.1 (rights value) and B1 (witness format) are both cases where the C26-H1 remediation fixed the *keys* and added a note claiming the fields "match" SAL canonical — but left two *values/formats* stale, making the note technically false. A delta audit of a byte-stable file MUST re-read the remediation's own claims against the canonical source token-by-token, not just confirm "the edit is still there." (Extends C56-A1/B8.)
2. **Bidirectional carry re-verification caught a resolution-induced staleness (A.2).** C25-H1 RESOLVED downstream (C51 #318), which turned a correct C26 deferral note into a *stale* one. Same mechanism as C62 (where C25-H1 resolution was the headline) but here it leaves a remediation artifact to clean up. Delta §A must re-check carries in BOTH directions and flag notes that a downstream resolution has falsified.
3. **C8's "full SDK compliance" was over-stated** — B2 (Device) and B9 (Task) are table↔SDK energy divergences the first-pass missed because it spot-checked names/modes, not the conditional energy cells. First-pass "SDK aligned" claims deserve a fresh mirror sweep at delta time.
4. **Refute-by-default earned its keep**: 5 verifier refutations + 1 synthesis refutation (B8, the path-convention false positive) + correct collapse of the 3× exist/presence re-find into one §A item. Cross-doc claims (B7, B8) were hand-verified before assertion per the loose-pattern-sweep rule.

---

## Cross-Reference to Prior Audits

| Audit | Spec | Result |
|-------|------|--------|
| C8 | entity-types.md (first pass) | 10 (3H/4M/3L); 9 remediated, L3 deferred |
| C26 | entity-types.md (1st delta) | 5 new + 1 INFO; 4 autonomous remediated (#260); 9/9 C8 hold |
| **C64** | **entity-types.md (2nd delta)** | **§A: 9/9 C8 + structural HOLD; C26-H1 INCOMPLETE (A.1+B1); A.2 C25-H1-resolved staleness; A.3 LCT-ID persists. §B: 26 raw → 11 distinct (0 HIGH / 4 MED / 5 LOW / 2 INFO) + 1 refuted. C65 split: 7 autonomous / 4 cross-track / 3 design-q.** |
