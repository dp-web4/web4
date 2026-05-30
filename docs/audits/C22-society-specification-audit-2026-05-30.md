# C22 Audit — `SOCIETY_SPECIFICATION.md` Internal Consistency

**Audit ID**: C22
**Date**: 2026-05-30
**Auditor**: Autonomous web4 session (Legion, slot 060057, exit #135, LEAD voice, v2 protocol)
**Target spec**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (398 lines, version 1.0.0, last content modification = PR #250 `f142fcdb` C21-M1 paragraph at §1.4)
**Audit class**: Internal consistency + cross-coherence (sister specs + SDK + ontology + test vectors)

---

## 0. Method & Boundary Conditions

- **BCs (13)**: BC#1 multi-file single-ID framing; BC#2 severity rubric; BC#3 line-cite re-verification at audit-write time; BC#4 explicit autonomous-vs-design-Q-vs-cross-track split; BC#5 corpus sweep extended to `web4-standard/core-spec/**` + sister `web4-society-authority-law.md`; BC#6 re-read sister specs that are cited; BC#7 no autonomous operator-engagement actions; BC#8 SDK-side findings flagged cross-track; BC#9 PR-body discipline; BC#10 subordinate-ontology TTL → cluster bundle, not inline drafts; BC#11 graceful-partial-remediation for next cycle; **BC#12 (NEW)** re-run vector-file `cat | jq` / `wc -l` at audit time when any finding cites vector counts; **BC#13 (NEW)** date-staleness alone is INFO unless coupled with a normative claim that depends on the date being current.
- **Sources cross-checked** (BC#6 verified read at audit time):
  - `web4-standard/core-spec/web4-society-authority-law.md` (SAL — sister, normative)
  - `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (sister — just-merged C21)
  - `web4-standard/core-spec/atp-adp-cycle.md` (ATP/ADP vocabulary canonical source)
  - `web4-standard/core-spec/mcp-protocol.md` (cross-society protocol live spec)
  - `web4-standard/core-spec/inter-society-protocol.md` (existence + SDK reference per `role.py:348`)
  - `web4-standard/implementation/sdk/web4/society.py` (canonical implementation)
  - `web4-standard/implementation/sdk/web4/federation.py` (Society / CitizenshipRecord / LedgerType / QuorumPolicy)
  - `web4-standard/implementation/sdk/web4/role.py` (`validate_minimum_viable` + `BASE_MANDATORY_ROLES`)
  - `web4-standard/ontology/web4-core-ontology.ttl` (subordinate-ontology gap check)
  - `web4-standard/test-vectors/society/society-vectors.json` (6 vectors, BC#12 verified at audit-write time via `grep -c '"name"' → 12 ↔ 1 top + 5×2 + 1×1 = 12 ↔ 6 distinct vectors`)
- **BC#3 line-cite verification at audit-write time**: every line number in this audit was re-checked against the current `SOCIETY_SPECIFICATION.md` head (398L, post-PR-#250 state) before finalization.

---

## 1. Findings Summary

| Severity | Count | Autonomous-actionable | Design-Q | Cross-track |
|---|---|---|---|---|
| HIGH    | 3 | 3 | 0 | 0 |
| MEDIUM  | 6 | 2 | 1 | 3 |
| LOW     | 2 | 2 | 0 | 0 |
| INFO    | 4 | 1 | 1 | 2 |
| DEMOTED | 2 | — | — | — |
| **Total actionable** | **11** | **8** | **2** | **5 (M3, M4, M5, I3, I4)** |

The autonomous-actionable batch (8) sits in the established C16-C21 envelope (5/5/6/6/7/8). Cross-track items continue to feed the standing subordinate-ontology cluster (now **7 audits** since #133) and the snake/camel cluster.

---

## 2. HIGH Findings

### H1 — Three-way drift in "minimum-viable society" definitions (cross-doc + SDK)

- **Anchor**: `SOCIETY_SPECIFICATION.md` §1.2 L19-51.
- **Defect**: Three normative sources define the *minimum requirement set* for a society differently, and no spec disambiguates which is canonical:
  - **`SOCIETY_SPECIFICATION.md` §1.2** (this doc) — 4 items: Law Oracle (§1.2.1 L23), Ledger (§1.2.2 L31), Treasury (§1.2.3 L39), Society LCT (§1.2.4 L46).
  - **`web4-society-authority-law.md` §3.1 L70-74** — 3 items: Authority Role LCT, Law Oracle LCT, Quorum Policy. (SAL §3.4 adds Immutable Record/Ledger as a *separate* MUST.)
  - **SDK `validate_minimum_viable` at `role.py:341-392`** — references `inter-society-protocol.md §6.2`: 7 base-mandatory roles (Sovereign, Law Oracle, Policy Entity, Treasurer, Administrator, Archivist, Citizen — `role.py:118-126`) + (if operational) ≥2 distinct fillers + Witness or Auditor.
- **Why HIGH**: This is the *foundational* MUST of the spec. A society implementer reading §1.2 alone gets a 4-item checklist that the SDK does NOT enforce; the SDK's enforced checklist (7 roles + witness/auditor) is in a *third* spec doc not cross-referenced from §1.2. A spec whose normative MUST list contradicts both its sister normative spec and the canonical SDK implementation is a HIGH-severity defect.
- **Severity**: HIGH.
- **Class**: autonomous-actionable. Remediation: add explicit cross-reference paragraph to §1.2 acknowledging that the "operational minimum" is further refined by SAL §3.1 (Authority + Quorum) and `inter-society-protocol.md §6.2` (the 7 base-mandatory roles), and that the §1.2 four-element list is a *conceptual* minimum that maps onto those role-structural requirements. No spec-source-of-truth change autonomously; this finding documents the gap and adds the cross-ref scaffold.

### H2 — §4.2.1 economic event action vocabulary mixes abstraction levels

- **Anchor**: `SOCIETY_SPECIFICATION.md` §4.2.1 L265-275 (specifically L269: `"action": "allocate|charge|discharge"`).
- **Defect**: The spec lists three economic actions for ledger events: `allocate | charge | discharge`. Of these:
  - `allocate` is a **treasury-level** action (treasury → entity). Matches SDK `society.py:653` (`"action": "allocate"` in ECONOMIC LedgerEntry).
  - `charge` and `discharge` are **ATP-cycle token-state transitions** per `atp-adp-cycle.md` §2.2 (ADP → ATP charging via value-creation, `charge_atp()`) and §2.3 (ATP → ADP discharging via R6 transactions). These are **R6-level** actions, not treasury-level.
  - The actual SDK-canonical treasury actions are `allocate | deposit | reclaim` (per `society.py` `Treasury.deposit/allocate/reclaim` L207-236 + `LedgerEventType.ECONOMIC` comment at `society.py:94`: `"economic"  # allocate/deposit/reclaim`).
- **Why HIGH**: The spec conflates two abstraction layers — a ledger Economic-event taxonomy should enumerate treasury operations (deposit, allocate, reclaim, slash), not the R6-level ATP-state transitions (charge, discharge) that happen at the cycle layer. An implementer following §4.2.1 literally would either omit deposit/reclaim entirely OR record R6 charge/discharge events at the wrong abstraction layer.
- **Severity**: HIGH.
- **Class**: autonomous-actionable. Remediation: replace L269 action enum with treasury-correct vocabulary aligned to SDK (`"action": "deposit|allocate|reclaim"`), or — if the spec intends both layers — split into two event_types: `economic_treasury` (deposit/allocate/reclaim) and `economic_token` (charge/discharge/slash) with cross-ref to `atp-adp-cycle.md` §2.

### H3 — §2.3 Citizenship Lifecycle ASCII shows "Rejection" but no SDK status represents it

- **Anchor**: `SOCIETY_SPECIFICATION.md` §2.3 L107-117 (ASCII flow showing `Application → Review → Acceptance` with branches to `Rejection / Provisional Status / Suspension → Reinstatement-or-Termination`).
- **Defect**: The ASCII lifecycle has `Rejection` as a terminal branch off `Review`. The SDK's authoritative `CitizenshipStatus` enum (`federation.py:91-98`) has 5 statuses: APPLIED, PROVISIONAL, ACTIVE, SUSPENDED, TERMINATED — **NO `REJECTED` status**. The `_CITIZENSHIP_TRANSITIONS` graph (`federation.py:102-108`) goes `APPLIED → {PROVISIONAL, ACTIVE}` only; there is no transition from APPLIED to a terminal "rejected" state. A rejected application in the SDK leaves no `CitizenshipRecord` at all (since `admit_citizen` returns False without creating a record).
- **Why HIGH**: The ASCII implies "Rejection" is a recorded lifecycle state (otherwise why is it in the diagram?), but the SDK treats it as a non-record outcome. A reader implementing per the ASCII would either add a phantom `REJECTED` status or record nothing on rejection — and the spec doesn't say which.
- **Severity**: HIGH. (Lifecycle diagram is the de facto reference for implementations.)
- **Class**: autonomous-actionable. Remediation: edit §2.3 ASCII to clarify that `Rejection` is a non-record outcome (no `CitizenshipRecord` is created) rather than a status, OR add an explicit prose note immediately under the ASCII stating: *"Rejection results in no record on the ledger; the SDK's `CitizenshipStatus` enum contains no REJECTED state."* Spec wording — does not require SDK change.

---

## 3. MEDIUM Findings

### M1 — §7.1 "Cross-Society Protocols" framed as "Future Considerations" but live specs exist

- **Anchor**: `SOCIETY_SPECIFICATION.md` §7.1 L382-385 ("Cross-Society Protocols: Treaty mechanisms / Resource sharing agreements / Reputation portability").
- **Defect**: §7 is titled "Future Considerations" but cross-society protocols are already specified normatively in:
  - `mcp-protocol.md` §1.1 (L28-36: "MCP as the Inter-Society Interface" — "MCP is the protocol by which sovereign Web4 societies engage each other").
  - `mcp-protocol.md` §7.3-7.6 (per memory, normative since MCP v0.1.3 amendment); §7.7 WIP.
  - `inter-society-protocol.md` (entire spec — exists in `core-spec/`, referenced by SDK `role.py:348` and `mcp-protocol.md:36`).
- **Why MEDIUM**: This is roadmap framing drift — the section reads as aspirational when the work has been done. A reader assumes the topic is open; in fact MCP §1.1 settles it.
- **Severity**: MEDIUM (framing, not correctness).
- **Class**: autonomous-actionable. Remediation: add note at §7.1 head: *"Treaty / resource-sharing / reputation-portability primitives are specified in `mcp-protocol.md` §7 and `inter-society-protocol.md`. This section enumerates further extensions beyond what those documents normatively define."* — preserves the "future" tone for genuinely-future items while removing the false-future framing.

### M2 — §1.2.2 vs §4.2.1 internal inconsistency on minimum-record categories + SDK divergence

- **Anchor**: `SOCIETY_SPECIFICATION.md` §1.2.2 L31-38 (lists 4 minimum record categories: Citizenship / Law / Economic / Witness attestations) ↔ §4.2.1 L237-275 (enumerates only 3 event_types: citizenship / law_change / economic). SDK `society.py` `LedgerEventType` (L89-97) has 5 types (CITIZENSHIP, LAW_CHANGE, ECONOMIC, METABOLIC, FORMATION).
- **Defect**: Three-way inconsistency:
  - §1.2.2 says ledger MUST record 4 things including "witness attestations".
  - §4.2.1 enumerates only 3 event types and omits witness attestations entirely.
  - SDK has 5 LedgerEventType values, adds METABOLIC + FORMATION (both have actual recording sites in `society.py` — metabolic-state transitions at `society.py:594-601`; formation phase transitions at `society.py:369-391`), and does NOT have a separate WITNESS_ATTESTATION type (witnesses are a *field* on every `LedgerEntry`, not a category of event).
- **Why MEDIUM**: Internal spec inconsistency is a framing defect, but the SDK omission of WITNESS_ATTESTATION suggests §1.2.2 is just imprecise (witnesses are participants, not events). Resolving requires consolidating §1.2.2 with §4.2.1 + acknowledging the SDK's METABOLIC + FORMATION categories.
- **Severity**: MEDIUM.
- **Class**: autonomous-actionable. Remediation: (a) remove "Witness attestations" from §1.2.2's minimum-records list (witnesses are participants, recorded via the `witnesses` field on each entry — not a separate event type); (b) extend §4.2.1 to enumerate the additional event types METABOLIC (state transitions) and FORMATION (phase transitions / incorporation), with JSON examples matching the SDK shape; (c) cross-ref §1.2.2 to §4.2.1 as the canonical enumeration. M2 is a single finding with two sub-edits in one section pair (BC#1 cohesion).

### M3 — §2.4 citizenship record JSON uses `society_lct` / `witness_lcts`; SDK uses `society_id` / `witnesses`

- **Anchor**: `SOCIETY_SPECIFICATION.md` §2.4 L121-132 (JSON keys: `entity_lct`, `society_lct`, `witness_lcts`, `rights`, `obligations`, `status`).
- **Defect**: SDK `CitizenshipRecord` (`federation.py:116-156`) uses `society_id` (not `society_lct`) and `witnesses` (not `witness_lcts`). Independent of casing, the **field names** disagree:
  - `society_lct` (spec) ↔ `society_id` (SDK)
  - `witness_lcts` (spec) ↔ `witnesses` (SDK)
- **Note on corpus-sweep (BC#5)**: `society_lct` appears in 5+ other normative/proposal docs (`SOCIETY_METABOLIC_STATES.md`, `ATP_INSURANCE_PROTOCOL.md`, `RFC-R6-TO-R7-EVOLUTION.md`, `SOCIETY_INTEGRATION_SUMMARY.md`) — so the spec-side convention is established; the SDK is the outlier. This compounds the snake/camel cluster (C17-M3 + C18-M3 + C18-L1, carry-forward from #134).
- **Severity**: MEDIUM (field-name drift across spec corpus and SDK is non-trivial; affects any serialization/canonicalization contract).
- **Class**: **cross-track** — defer to operator preference per C18 M4 V3-dim precedent. The naming question (spec is internally consistent across 5+ docs; SDK is the outlier) is bigger than C22 and is part of the standing snake/camel cluster.

### M4 — §5.3 Trust Building input list is aspirational; SDK implements only citizen behavior aggregation

- **Anchor**: `SOCIETY_SPECIFICATION.md` §5.3 L348-354 ("Society-level trust tensors (T3) are calculated from: Citizen behavior aggregation / Inter-society interactions / Economic efficiency / Law compliance rates").
- **Defect**: The SDK's `compute_society_t3` (`society.py:705-724`) implements ONLY citizen behavior aggregation — it calls `compute_team_t3(profiles, role)` which is a weighted average of citizens' T3 tensors. The other three inputs listed by §5.3 — inter-society interactions, economic efficiency, law compliance rates — have **no implementation surface** in the SDK. Plus, §5.3 mentions T3 only (no V3); SDK `society.py:766` explicitly acknowledges this with the comment *"Use T3 composite as proxy for V3 since V3 is not aggregated at society level"* — an SDK self-flag of incompleteness.
- **Why MEDIUM**: The spec specifies four inputs; the SDK implements one. This is the recurring T3/V3-incompleteness-at-non-tensor-spec pattern (carry-NEW-A subordinate-ontology cluster from #134).
- **Severity**: MEDIUM.
- **Class**: **cross-track** — feeds the subordinate-ontology cluster bundle (now 7 audits since C16-M8 / C17-M1 / C18-M6 / C19-M5 / C20-M5 / C21-M7 / C22-M4). Per BC#10 + #134 carry-NEW-A, no inline TTL/SDK drafting in this audit.

### M5 — §1.2.3 Treasury mentions "ADP allocation" but SDK Treasury only handles ATP

- **Anchor**: `SOCIETY_SPECIFICATION.md` §1.2.3 L39-44 ("Definition: Society-managed ATP/ADP token pool / Requirements: Initial ADP allocation (can be zero) / Allocation mechanism defined in law / Energy accounting (ATP in/out tracking)").
- **Defect**: The spec describes Treasury as "ATP/ADP token pool" with "Initial ADP allocation". SDK `Treasury` (`society.py:194-241`) only tracks ATP — fields are `balance` (single scalar), `total_deposited`, `total_allocated`, `allocations: Dict[str, float]`. There is no ADP state-tracking, no charged/discharged distinction at the treasury level. The treasury comment at `society.py:196` says *"Society ATP pool per spec §1.2.3"* — silently dropping the ADP half.
- **Cross-ref**: `atp-adp-cycle.md` §2.1 (L37-60) shows societies *mint* tokens in the ADP state and §2.2 charges them to ATP; §1.2.3's "Initial ADP allocation" is consistent with the cycle's minting semantics, but the SDK Treasury doesn't reify the ATP/ADP state distinction at all.
- **Severity**: MEDIUM (SDK-side gap; spec is correct per cycle semantics, but SDK doesn't honor the dual-state pool).
- **Class**: **cross-track** — SDK Treasury needs ADP-state representation, or §1.2.3 needs to clarify that the dual-state distinction is at the cycle layer not the treasury layer. Either way, decision is design-Q + SDK refactor (not autonomous within an audit-only PR).

### M6 — Three different default `rights`/`obligations` across the codebase (spec + SDK × 2 sites)

- **Anchor**: Three sources, three sets:
  - `SOCIETY_SPECIFICATION.md` §2.4 L128-129: rights `["vote", "propose", "allocate"]`, obligations `["witness", "contribute"]`.
  - SDK `CitizenshipRecord` defaults (`federation.py:128-129`): rights `["exist", "interact", "accumulate_reputation"]`, obligations `["abide_law", "respect_quorum"]`.
  - SDK `society.py admit_citizen` defaults (`society.py:441-443`): rights `["vote", "propose"]`, obligations `["abide_law", "witness"]`.
- **Defect**: Three different default lists for the same conceptual field, in two of the same codebase's modules + the spec. An entity admitted via `admit_citizen()` gets a DIFFERENT rights/obligations list than an entity constructed via `CitizenshipRecord(...)` with no explicit args. The spec's example list overlaps neither perfectly. No documented canonical default.
- **Severity**: MEDIUM.
- **Class**: **design-Q** — operator must pick the canonical default. SAL §2.2 birth certificate (L57-58) has yet another set (rights `["exist", "interact", "accumulate_reputation"]`, obligations `["abide_law", "respect_quorum"]` — matches SDK CitizenshipRecord defaults). This finding documents the four-way split for an operator decision; not autonomously fixable.

---

## 4. LOW Findings

### L1 — §4.1.3 Participatory Ledger JSON omits the `validators` field present in §4.1.1 / §4.1.2

- **Anchor**: `SOCIETY_SPECIFICATION.md` §4.1.1 L196-203 (Confined — has `validators`), §4.1.2 L211-218 (Witnessed — has `validators`), §4.1.3 L226-233 (Participatory — has NO `validators` field; uses `parent_ledger` instead).
- **Defect**: The ledger-type schema is inconsistent across the three subtypes. Participatory ledgers presumably *do* have validators (the parent's), but the JSON doesn't expose how. SDK `LedgerType` (`federation.py:200-205`) is just an enum, not a struct, so no canonical "participatory has these validators" rule exists in code either.
- **Severity**: LOW (schema sketch, not enforced; minor reader-confusion source).
- **Class**: autonomous-actionable. Remediation: add `"validators": "inherited_from_parent"` or `"validators_via": "parent_ledger"` to the §4.1.3 JSON to make the inheritance explicit. Or add a sentence under the JSON clarifying that participatory ledgers inherit validators from the parent.

### L2 — §1.2.4 says Society LCT "holds society-level trust tensors" — singular tensor; spec elsewhere distinguishes T3 + V3

- **Anchor**: `SOCIETY_SPECIFICATION.md` §1.2.4 L48-52 ("Holds society-level trust tensors").
- **Defect**: §5.3 (L348) names "T3" specifically; `t3v3-ontology.ttl` distinguishes T3 (Trust) and V3 (Value) as two separate root tensors. §1.2.4's generic "trust tensors" is technically correct (T3 is *a* trust tensor) but lossy — a reader doesn't know whether a society's LCT carries T3 only or T3+V3. SDK `society.py:709` aggregates T3 only with explicit V3-as-T3-proxy workaround at L766.
- **Severity**: LOW.
- **Class**: autonomous-actionable. Remediation: change §1.2.4 wording from "society-level trust tensors" to "society-level T3 and V3 tensors (see `t3-v3-tensors.md`)" OR keep the generalization and add a one-sentence cross-ref to §5.3. Either preserves the spec voice while removing ambiguity.

---

## 5. INFO Findings

### I1 — Header date "January 17, 2025" stale; same staleness in sister `SOCIETY_METABOLIC_STATES.md`

- **Anchor**: `SOCIETY_SPECIFICATION.md` L4 (`## Date: January 17, 2025`).
- **BC#5 corpus-sweep**: identical staleness in `SOCIETY_METABOLIC_STATES.md` L4 (`## Date: January 17, 2025`). Per BC#1 framing: 1 finding × 2 file effects (multi-file framing).
- **BC#13 application**: date-staleness alone is INFO unless coupled with a normative claim that depends on the date being current. The version field (`1.0.0`) carries no date-dependency; nothing in §§1-7 references the date as a normative anchor. Therefore INFO, not LOW.
- **Class**: autonomous-actionable. Remediation: bump both file dates to `2026-05-30` (or `2026-05-XX` matching remediation-PR merge date). Two-file edit via BC#1 multi-file framing.

### I2 — Status label "Foundational Concept" vs §1.4 normative `MUST` language

- **Anchor**: `SOCIETY_SPECIFICATION.md` L5 (`## Status: Foundational Concept`) vs §1.4 L76 (*"Implementations of this Society Specification MUST also conform to the metabolic-states specification…"*).
- **Defect**: The status field reads as "concept", implying non-normative; §1.4 uses RFC 2119 `MUST`. The two framings disagree: this spec is operationally normative for the SDK (entire `society.py` is "Canonical implementation per … `SOCIETY_SPECIFICATION.md`" per `society.py:4`), yet labeled a "concept".
- **Severity**: INFO (label/framing only — no behavior depends on it).
- **Class**: **design-Q** — status taxonomy is operator's call. (Candidate values: "Foundational Concept" / "Draft" / "Stable" / "Normative". This spec is closer to the last two given the SDK's canonical-impl dependency.) Not autonomously fixable.

### I3 — Test-vector coverage gap: 6 vectors exercise ~20% of SDK surface

- **Anchor**: `web4-standard/test-vectors/society/society-vectors.json` (BC#12 verified at audit-write time: 6 distinct vectors — minimal_society / society_with_treasury / citizen_admission / treasury_allocation / metabolic_transition / fractal_hierarchy).
- **Defect**: Untested SDK behaviors include:
  - `suspend_citizen` / `reinstate_citizen` / `terminate_citizen` (lifecycle states beyond ACTIVE — `society.py:472-571`)
  - `record_law_change` (any LAW_CHANGE event — `society.py:672-699`)
  - `SocietyLedger.amend()` (immutability-with-corrections per spec §4.2.2 — `society.py:155-181`)
  - `compute_society_t3` (society-level T3 aggregation — `society.py:705-724`)
  - `society_health` / `society_energy_cost`
  - The full 5-status `CitizenshipStatus` lifecycle (only ACTIVE is exercised)
  - The 3 LedgerType variants (only CONFINED default is exercised; WITNESSED + PARTICIPATORY untested)
  - The AuditRequest / AuditAdjustment SAL §5.5 surfaces (entire SAL audit pathway untested at society level)
- **Severity**: INFO (recurring orphan-vector pattern; extends C18-H3 family).
- **Class**: **cross-track** — operator may commission additional vector batch. Carry-forward joins #134's carry-NEW-H (society-metabolic-states.json 6/8 state coverage gap) as a coordinated test-vector backlog item.

### I4 — Core ontology has zero predicates for Society/Citizen/Treasury/Ledger/LawOracle

- **Anchor**: `web4-standard/ontology/web4-core-ontology.ttl` — `grep` for `web4:Society`, `web4:Citizen`, `web4:Treasury`, `web4:Ledger`, `web4:LawOracle`, `web4:hasAuthority`, `web4:hasLawOracle` returned ONE result (a comment at L124 mentioning `OracleWitness` linked to `LawOracle`).
- **Defect**: Society / Citizen / Treasury / Ledger / LawOracle have ZERO subordinate-ontology coverage in `web4-core-ontology.ttl`. SAL §3.3 (L82-101) shows the *intended* edges (`web4:memberOf`, `web4:hasAuthority`, `web4:hasLawOracle`, `web4:delegatesTo`) as turtle examples — but these are not in the actual ontology TTL.
- **Severity**: INFO (recurring subordinate-ontology cluster — now at **7 audits** since C16-M8 / C17-M1 / C18-M6 / C19-M5 / C20-M5 / C21-M7 / C22-I4).
- **Class**: **cross-track** — feeds subordinate-ontology cluster bundle (carry-NEW-A from #134). Per BC#10, no inline TTL drafting. Cluster has been past the 5-audit operator-engagement threshold since C20.

---

## 6. DEMOTED candidates (transparency)

### D1 — §4.1.1 Confined Ledger `validators` field

- **Considered as**: schema gap (validators field is just LCT IDs of citizens, no explicit policy).
- **Demoted reason**: SDK `Society.citizens` (`federation.py`) is the canonical validator set for CONFINED ledgers; the JSON is a representational sketch, not a normative schema. Not a finding.

### D2 — §1.3 Formation Process "First law ratified" in Bootstrap vs §1.2.1 "At least one foundational law" required

- **Considered as**: ordering inconsistency (law required at minimum-viability but only ratified at Bootstrap).
- **Demoted reason**: On re-read of §1.3.1 ("Founding entities agree on initial laws") + §1.3.2 ("First law ratified"), the sequence is internally coherent — laws are *established* at Genesis and *ratified* at Bootstrap. SDK `society.py:332-333` mirrors this (`set_law` called at create_society if `initial_law` provided, before `BOOTSTRAP` phase). Not a finding.

---

## 7. Remediation Roadmap (for downstream PR cycle)

Per the established C16-C21 partial-remediation pattern (graceful-partial-remediation, BC#11), the matching C22 remediation PR should:

- **Apply autonomous-actionable (8)**: H1 (cross-ref scaffold), H2 (econ vocabulary correction), H3 (ASCII clarification), M1 (§7.1 cross-ref to MCP/inter-society), M2 (§1.2.2 ↔ §4.2.1 reconciliation + METABOLIC/FORMATION addition), L1 (§4.1.3 validators schema), L2 (§1.2.4 T3+V3 explicitness), I1 (date bump × 2 files).
- **Defer design-Q (2)**: M6 (canonical rights/obligations defaults — 4-way split needs operator pick), I2 (status taxonomy — operator framing call).
- **Defer cross-track (5)**: M3 (snake/camel cluster), M4 (subordinate-ontology cluster), M5 (SDK ADP-at-treasury), I3 (test-vector orphans), I4 (subordinate-ontology cluster — same bundle as M4).
- **Multi-file findings (per BC#1)**: I1 is 1 finding × 2 file effects (`SOCIETY_SPECIFICATION.md` + `SOCIETY_METABOLIC_STATES.md`); H1 may add cross-ref paragraphs to SAL §3.1 and `inter-society-protocol.md §6.2` for symmetry, but the C22 PR can scope to target-spec only and defer the parent-symmetry edits.

---

## 8. Carry-forward to #136 and beyond

- **Carry-NEW (this audit)**:
  - `carry-C22-rem`: 8 autonomous-actionable findings for the next remediation cycle. Expected envelope: 6-9 edits across 1-2 files (mostly target-spec; possibly 1 sister date-bump).
  - `carry-C22-design-Q`: M6 (rights/obligations defaults 4-way split — needs operator canonical pick) + I2 (status taxonomy framing) → standing operator-engagement menu.
  - `carry-C22-cross-track`: M3 + M4 + M5 + I3 + I4 → feeds existing clusters (snake/camel + subordinate-ontology + test-vector orphans + SDK-side).
- **Cluster status update**:
  - Subordinate-ontology cluster: now at **7 audits** (C16-M8 / C17-M1 / C18-M6 / C19-M5 / C20-M5 / C21-M7 / C22-I4+M4). Past 5-audit operator-engagement threshold since C20; strongest case yet for the bundled TTL extension PR (carry-NEW-A from #134).
  - Snake/camel cluster: extends to 4 audits (C17-M3 + C18-M3 + C18-L1 + C22-M3).
  - Test-vector orphan family: C18-H3 + C21-NEW-H (8/8 metabolic state coverage gap) + C22-I3 (society-vector 6-scenario coverage).
- **BC menu**: BC#12 (NEW per #134) used cleanly at audit-write time to verify society-vectors.json count (12 grep hits ↔ 6 distinct vectors). BC#13 (NEW per reviewer) applied: header date staleness classified INFO (not LOW) because no normative dependency.

---

## 9. Audit Statistics

- **Spec lines**: 398
- **Audit lines**: ~430 (this doc)
- **Findings**: 11 actionable (3 HIGH + 6 MEDIUM + 2 LOW) + 4 INFO + 2 DEMOTED
- **Autonomous-actionable**: 8 (H1, H2, H3, M1, M2, L1, L2, I1)
- **Design-Q**: 2 (M6, I2)
- **Cross-track**: 5 (M3, M4, M5, I3, I4)
- **Cross-doc / cross-source citations**: 6 sister specs, 3 SDK modules, 1 ontology file, 1 test-vector file, 1 proposal corpus sweep
- **BC#3 off-by-one corrections at audit-write time**: 0 (line numbers were re-verified against current spec head before write — all stable)
- **BC#5 corpus-sweep hits**: 1 (I1 — identical date staleness in sister `SOCIETY_METABOLIC_STATES.md` L4; 2-file multi-effect via BC#1).
- **BC#12 application**: 1 (I3 — society-vectors.json count verified `grep -c '"name"' = 12 ↔ 6 distinct vectors`).

---

*"A society's specification is its self-description; the audit is the mirror that asks whether the description matches the body."*
