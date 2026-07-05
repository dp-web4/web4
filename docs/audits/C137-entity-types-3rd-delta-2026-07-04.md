# C137 Audit: `entity-types.md` — 3rd-Delta Re-Audit (4th Pass)

**Date**: 2026-07-04
**Auditor**: Autonomous session (Legion, web4 track) — firing `180036`, LEAD voice
**Document**: `web4-standard/core-spec/entity-types.md` (741 lines)
**Lineage**: C8 first-pass (2026-05-22, 10 findings, 9 remediated) → C26 first delta (2026-06-02, 5 new + 1 INFO, 4 autonomous remediated #260) → C64 second delta (2026-06-16, 26 raw → 11 distinct, 7 autonomous routed) → C65 remediation (2026-06-16, 7 applied, #344 `5baa160f`) → C104 (2nd-delta re-audit, 0 net-new) → **C137 (this audit, 3rd-delta re-audit / 4th pass)**
**Rotation note**: this fire is the **C137 ISP remediation slot**. C136 (`2ff31a20`, #451) found ISP 0 net-new, so the remediation slot is a **no-op** and the round-robin advances to the next-oldest file, `entity-types.md` (last audited C104, 2026-06-26). This is the **8th** no-op→advance of the frozen-wrap era.
**Methodology**: C-series **3rd-delta re-audit** of a **byte-frozen** target — same class as C131–C136 (the recent 3rd-delta wraps). The target is **byte-identical to its C65 remediation** (`git diff 5baa160f..HEAD -- entity-types.md` = empty; **18 days frozen**, unchanged since the C104 snapshot). Per the **C56 method**, §A audits the C65 remediation's *claims* against canonical, not merely "is the edit present." Per the **C62 lesson**, §A re-verifies every standing carry **bidirectionally**. §B is the **corpus-delta surface**: diff the cited siblings that MOVED since the C104 snapshot at **cited-hunk granularity** ([[feedback_snapshot_presence_guard]]), and read the moved sibling's own interval-audit routing for carries routed back here ([[feedback_cross_doc_carry_inbound]]). §C is a single proportional fresh-internal refute-by-default pass. §D routes findings for C138.
**Cross-spec authority re-read** (passage, not recalled): `atp-adp-cycle.md` §4.2 (`track_value_flow`, L380–383 `aggregate_value`), §7.1 MUST #6 + scope note (L619–636), §2.4 (Slashing) — all read at the current HEAD (post-C119 `e99b419e`); the C119 commit body (#420); the prior C104 audit doc.

---

## §A. Verification of C65 Remediation (frozen target — 8th consecutive)

entity-types.md is **byte-identical** since the C65 remediation (#344 `5baa160f`, 2026-06-16). All 7 autonomous C65 remediations **HELD** by byte-freeze, 0 regressed, **0 `&#`/HTML-entity artifacts**:

| C65 item | Origin | Site | Current state | Verdict |
|----------|--------|------|---------------|---------|
| A.1 (flagship) | C26-H1 value | §3.1 L153 | `"rights": ["presence", "interact", "accumulate_reputation"]` | **HELD** |
| A.1 prose | C26-H1 value | §6.2 L495 | "Provides base rights: Presence, interact, accumulate reputation" | **HELD** |
| B1 | witness format | §3.1 L151 | `["lct:web4:witness:1", "lct:web4:witness:2"]` (colon form) | **HELD** |
| B3 | Hybrid mode | §2.1 L33 | `Agentic/Responsive/Delegative` (was undefined "Mixed") | **HELD** |
| B4 | Infra mode slip | §2.1 L35 | Mode column = `None` (was "Passive", an energy not a mode) | **HELD** |
| B6 | slashing vocab | §2.3 L102 | "ADP consumed ... distinct from the punitive, authority-executed *slashing* of `atp-adp-cycle.md` §2.4 (evidence-gated destruction of ATP for law violations)" | **HELD** |
| A.2 + B5 | role-list home + six-vs-seven | §4 preamble L281 | "six SAL-specific roles ... canonical home is `society-roles.md` §2" | **HELD** |

Together A.1+B1 keep the §3.1 provenance note ("the fields `entity` through `obligations` match canonical `Web4BirthCertificate` §2.2") true at value AND format level — the key-only gap the C56 method caught at C64 remains fully closed.

### A.1 Standing carries — all STAND, re-verified bidirectionally

| Carry | Class | Re-verification at C137 | Verdict |
|-------|-------|--------------------------|---------|
| **C8-L3** | deferred content-merge | §12↔§3.1 citizen-example redundancy; non-contradictory | **STANDS** (deferred) |
| **C23-H1** | OPEN design-q | birth-cert field-set (`ledgerProof`/`parentEntity` superset vs SAL §2.2); untouched by any interval commit | **STANDS** |
| **C24-H1** | OPEN design-q (cross-track) | LCT-ID divergence `lct:web4:*` vs `policy:*` (§13.2) vs `did:web4:key:*` (LCT-spec subject); do NOT self-resolve | **STANDS** |
| **B2** | cross-track (SDK) | SDK `entity.py` Device hardcodes `ACTIVE` — cannot model Passive Device per §2.1/§2.3 | **STANDS** |
| **B7** | cross-track → **3-doc** | §10.2 `trust_requirements` vs dictionary-entities §2.2 `dictionary_trust_config` (3-doc B26 bundle, operator-gated); dictionary-entities UNMOVED since C53 | **STANDS** |
| **B9** | design-q | Task energy "Active (when R6-capable)" vs SDK fixed ACTIVE; §2.3 omits Task from R6-capable list | **STANDS** |
| **B10** | design-q / editorial | §13 Policy lacks an LCT-structure JSON example (asymmetry vs §10.2/§11.2) | **STANDS** |
| **B11** | design-q | §13.1 frames SAGE/IRP integration as if Web4-normative | **STANDS** |
| **B12** | cross-track (nicety) | §2.3 passive-rep lacks explicit cross-ref to atp-adp §4.2; **see §B** | **STANDS** |

No carry RESOLVED or HARDENED into a new defect this interval.

---

## §B. Corpus-Delta + Inbound Cross-Doc Carry

**Moved-sibling surface.** Of the siblings cited by C64/C104 (SAL/`web4-society-authority-law.md`, `society-roles.md`, `dictionary-entities.md`, `atp-adp-cycle.md`, LCT-spec, SDK `entity.py`), **only `atp-adp-cycle.md` moved since the C104 snapshot (2026-06-26).** The single interval commit is **atp-adp-C119** (#420 `e99b419e`, 2026-06-30). This is the **same SSOT sibling** that was the corpus-delta surface at C104 (then C79), and at the sibling wraps C135 (LCT) and C136 (ISP). All other cited siblings are at-or-before C104 (dictionary-entities C53 `95d20919` 2026-06-13; society-roles C39 `8401c6a9` 2026-06-08; LCT C61 `9d1933f8` 2026-06-15; protocols/web4-dictionary-entities 2025-09-11). So the entire corpus-delta surface is atp-adp-C119.

### What C119 actually changed (read at HEAD, not recalled)

C119 resolved the C118-N1 internal contradiction in atp-adp by **scoping §7.1 MUST #6**:
- **§7.1 MUST #6** (L619): `Value MUST be tracked through T3/V3 tensors` → **"Entity-level value MUST be tracked through T3/V3 tensors; society-level aggregates MAY use non-tensor rollup accounting (§4.2)"**, plus a new scope note (L621–636) modeled on the C79 §3.3 demurrage carve-out.
- **§4.2** (L382–383): the `aggregate_value` tertiary comment gained a back-reference — "…not a T3/V3 dimension — rollup accounting, outside §7.1 MUST #6 per its scope note".

Both edits sit in atp-adp **§7.1** and **§4.2** (the `aggregate_value` society-level leg).

### B-delta.1 — atp-adp-C119 → entity-types B6 cross-ref (§2.4 slashing): DISJOINT, STABLE

entity-types §2.3 L102 (the C65-B6 remediation) cross-cites `atp-adp-cycle.md` **§2.4** slashing. C119 touched **§7.1 and §4.2 only — not §2.4**. The B6 cross-ref hunk is therefore **untouched at cited-hunk granularity**; the §2.4 slashing primitive it names is unchanged. **B6 remains true; no delta.** (This mirrors C104, where atp-adp-C79 had *reinforced* the same §2.4 cross-ref by adding the slashing carve-out note; C119 leaves §2.4 stable.)

### B-delta.2 — atp-adp-C119 → entity-types §7.1/MUST#6/aggregate: DISJOINT (grep-confirmed 0)

entity-types has **zero** citation of atp-adp §7.1, "MUST #6", "value proof", `aggregate_value`, "society-level aggregate", or "rollup" (`grep -ni` = 0; the only "7.1" token in entity-types is its **own** `### 7.1 Entity Type Validation` heading, not an atp-adp citation). So the C119 MUST#6-scoping edit is **disjoint at cited-hunk granularity** — nothing in entity-types depends on the unconditional-vs-scoped form of atp-adp §7.1 MUST #6.

### B-delta.3 — CORROBORATION: C119 entity-vs-society scoping REINFORCES entity-types' T3/V3 usage

Every T3/V3 mention in entity-types is at the **entity-role** level, never the society-aggregate level:
- §4.4 L327 — Authority role "Validates and adjusts **T3/V3 tensors of direct citizens**" (entity-role legs)
- §4.6 L354 — agent/executor "Accrues **own T3/V3** for execution quality" (entity-role leg)
- §11 L462 — "Reputation Development: **T3/V3 tensors evolve** through interactions" (entity-role leg)

C119's scope note says precisely that MUST #6 "**governs entity-role tensor accounting, not the society-aggregate rollup**." entity-types tracks value exactly where C119 now says T3/V3 applies (entity-role legs) and never claims T3/V3 for a society-level aggregate. So the C119 scoping is **consistent with — and corroborates —** entity-types' usage; there is nothing to staleify. (Same corroboration shape recorded at C135/C136 for the same C119 edit against LCT and ISP.)

### B-delta.4 — atp-adp-C119 → entity-types B12 nicety (§2.3 passive-resource): STANDS, orthogonal

B12 references atp-adp **§4.2 value-flow tracking** relative to the passive-resource omission in entity-types §2.3 (L102: passive resources earn "Utilization frequency × effectiveness," "no reputation updates"). C119's §4.2 change was a one-line **comment** on the `aggregate_value` society-level tertiary leg — orthogonal to how §4.2 treats (omits) passive resources. entity-types §2.3 remains consistent with atp-adp §4.2. **B12 stays a nicety (an explicit cross-ref would help a reader), not a defect.**

**Interval-audit routing.** The C118 atp-adp delta-audit and the C119 #420 commit body route only atp-adp-internal findings (C118-N1 applied, C118-N2 t3-v3-owned deferred); **0 carries routed back to entity-types** from the atp-adp side.

### B-inbound.1 — C64-B7 3-doc Dictionary-LCT bundle: unchanged, STANDS

The C104 elevation of C64-B7 (entity-types §10.2 `trust_requirements` as a 3rd normative Dictionary-LCT structure alongside dictionary-entities §2.2 and protocols/web4-dictionary-entities) is **unchanged** — dictionary-entities has not moved since C53 (`95d20919`, 2026-06-13) and the protocols/ sibling since 2025-09-11. The fix belongs on the entity-types §10.2 side but is **gated on the operator's B26 sibling-canonicity decision** → cross-track/operator, NOT autonomous.

**Net from corpus-delta: 0 net-new.**

---

## §C. Fresh-Internal Refute-by-Default Pass

A single Explore pass (proportional to an 8th-consecutive byte-frozen target whose full 8-lens 26-raw sweep ran at C64 and whose refute pass ran clean at C104), fed the C64/C104 prior-finding + DEMOTED context and instructed to refute by default. **Result: 0 net-new internal contradictions.**

Checked and clean (line-traced): §1–§14 numbering fully sequential, no duplicate/skipped headings; §2.1 entity table (15 types) ↔ §2.2 behavioral modes ↔ §2.3 energy classes — every row's mode/energy consistent with the prose, incl. the C65-fixed Hybrid (L33 Agentic/Responsive/Delegative) and Infrastructure (L35 None) cells; Citizen-role immutability consistent across §3.1 L137 / §3.4 L244 / §6.2 L494; all internal `see §X` cross-refs resolve (L261→§3.2, L275→§3.4, L290→§4.2, L423→§3.1); §3.1 JSON-LD ↔ §5.1 birth-cert pseudocode divergence is the §5.1-declared "illustrative and abbreviated" subset (L418–423), stated-by-design, not a contradiction; rights values match §6.2 prose. Confirms the near-certain-empty expectation for a thrice-audited frozen file.

---

## §D. Disposition Summary & C138 Routing

| Finding | Class | Disposition |
|---------|-------|-------------|
| 7/7 C65 remediations | §A | **HELD** by byte-freeze; 0 regressed, 0 artifacts |
| All 9 standing carries | §A | **STAND**; none resolved/hardened into a defect |
| atp-adp-C119 → B6 (§2.4 slashing) | §B corpus-delta | **DISJOINT/STABLE** (C119 touched §7.1+§4.2, not §2.4) |
| atp-adp-C119 → §7.1/MUST#6 | §B corpus-delta | **DISJOINT** (entity-types cites §7.1/MUST#6 nowhere; grep=0) |
| atp-adp-C119 entity-vs-society scoping | §B corpus-delta | **CORROBORATES** entity-types' entity-role-only T3/V3 usage (L327/354/462) |
| atp-adp-C119 → B12 (§4.2) | §B corpus-delta | **STANDS** (aggregate_value comment orthogonal to passive-resource omission) |
| C64-B7 3-doc bundle | §B inbound | **STANDS**, unchanged (dictionary siblings unmoved); operator-gated B26 |
| Fresh-internal pass | §C | **0 net-new internal contradictions** |

**C137 distinct new findings: 0.** This is entity-types' **2nd CONSECUTIVE fully-clean delta** (C104 + C137). → **C138 entity-types remediation slot = NO-OP** (matches the C131–C136 pattern: a 0-defect 3rd-delta pairs with a no-op remediation turn and the rotation advances).

**Routed off-target (all standing, none gate a normal AUDIT turn — surface as ONE operator memo)**:
- **C64-B7** (3-doc Dictionary-LCT-structure canonicity) → folds into dictionary **B26** sibling-canonicity bundle; operator picks the canonical form, then the fix lands on the entity-types §10.2 side.
- **C23-H1** (birth-cert field-set superset) + **C24-H1** (LCT-ID 4-way divergence) → open design-Qs, do NOT self-resolve.
- **B2** (SDK Device per-instance energy) → SDK-track.
- **B9** (Task non-R6 metabolism), **B10** (Policy LCT JSON example), **B11** (SAGE optionality framing) → design-q, operator.
- **B12** (passive-rep cross-ref to atp-adp §4.2) → cross-track nicety.

**Rotation**: next-oldest after entity-types (C64/C65, 2026-06-16) is **`errors.md`** (last audited C106, lineage C30→C66→C67→C106→C138/C139) for its 3rd-delta.

---

## §E. Lessons (for memory)

1. **8th consecutive frozen-wrap, same shape.** entity-types byte-frozen 18 days; §A = pure verification (7/7 held by byte-freeze, 9 carries stand); §B yield is **entirely** on the corpus-delta surface. Files churn slower than the +2-per-file cadence → wraps keep hitting frozen targets. Locked across C92/C94/C96/C98/C100/C102/C104/**C137**.
2. **The moved sibling was atp-adp-cycle.md AGAIN** — C119, the same commit that was the corpus-delta surface at C135 (LCT) and C136 (ISP). A single recently-churned SSOT sibling is the delta surface for *multiple* downstream frozen targets across a wrap window. Confirms the C104 observation (then C79) as a recurring structural fact of the round-robin.
3. **The C119 MUST#6-scoping edit is a THREE-shape disjointness case, and the third shape is CORROBORATION.** Against entity-types: (a) DISJOINT-by-uncited-section — the §2.4 slashing cross-ref (B6) sits in a section C119 never touched; (b) DISJOINT-by-zero-citation — entity-types cites atp-adp §7.1/MUST#6/aggregate nowhere (grep=0); (c) **CORROBORATION** — C119's "entity-role tensor accounting, not society-aggregate rollup" scoping *reinforces* entity-types' T3/V3 usage, which is entity-role-level at every occurrence (L327/354/462). Corroboration is a first-class delta outcome (a sibling can reinforce the target, not only stale it) — same lesson C136 drew for ISP.
4. **Proportional §C earned its keep without a fleet.** One refute-by-default Explore pass confirmed 0 net-new internal on a thrice-audited frozen file — the right instrument, avoiding a re-run of the C64 8-lens 26-raw workflow on identical bytes.

---

## Cross-Reference to Prior Audits

| Audit | Spec | Result |
|-------|------|--------|
| C8 | entity-types.md (first pass) | 10 (3H/4M/3L); 9 remediated, L3 deferred |
| C26 | entity-types.md (1st delta) | 5 new + 1 INFO; 4 autonomous remediated (#260) |
| C64 | entity-types.md (2nd delta) | 26 raw → 11 distinct (0 HIGH/4 MED/5 LOW/2 INFO); 7 autonomous routed |
| C65 | entity-types.md (remediation) | 7 autonomous applied (#344 `5baa160f`) |
| C104 | entity-types.md (2nd-delta re-audit, 3rd pass) | §A 7/7 HELD, 9 carries STAND; §B atp-adp-C79 REINFORCED B6, 0 net-new; §C 0 net-new. → C105 NO-OP |
| **C137** | **entity-types.md (3rd-delta re-audit, 4th pass)** | **§A: 7/7 C65 HELD by byte-freeze (18d), 0 regressed, 0 artifacts; 9 carries STAND. §B: only atp-adp-C119 moved → §7.1 MUST#6 + §4.2 aggregate_value comment BOTH DISJOINT from entity-types' cited §2.4 slashing hunk (grep §7.1/MUST#6/aggregate = 0); entity-vs-society scoping CORROBORATES entity-types' entity-role-only T3/V3 usage; B6/B12 STABLE; C64-B7 3-doc bundle unchanged, operator-gated. §C: 0 net-new internal. → 2nd consecutive fully-clean delta (C104+C137); C138 = NO-OP.** |
