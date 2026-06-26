# C104 Audit: `entity-types.md` — 2nd-Delta Re-Audit (3rd Pass)

**Date**: 2026-06-26
**Auditor**: Autonomous session (Legion, web4 track) — firing `000010`, LEAD voice
**Document**: `web4-standard/core-spec/entity-types.md` (741 lines)
**Lineage**: C8 first-pass (2026-05-22, 10 findings, 9 remediated) → C26 first delta (2026-06-02, 5 new + 1 INFO, 4 autonomous remediated #260) → C64 second delta (2026-06-16, 26 raw → 11 distinct, 7 autonomous routed) → C65 remediation (2026-06-16, 7 applied, #344 `5baa160f`) → **C104 (this audit, 2nd-delta re-audit)**
**Methodology**: C-series **2nd-delta re-audit** of a **byte-frozen** target — same class as C92/C94/C96/C98/C100/C102 (the six prior frozen-wrap audits). The target is **byte-identical to its C65 remediation** (`git log 5baa160f..HEAD -- entity-types.md` = empty; 10 days frozen). Per the **C56 method**, §A audits the C65 remediation's *claims* against canonical token-by-token, not merely "is the edit present." Per the **C62 lesson**, §A re-verifies every standing carry **bidirectionally**. §B is the **corpus-delta surface**: diff the cited siblings that MOVED since C65 (apply the [[feedback_snapshot_presence_guard]]), and read the moved siblings' own interval-audit docs for carries routed back here ([[feedback_cross_doc_carry_inbound]]). §C is a single fresh-internal refute-by-default pass (proportional — full 8-lens sweep ran at C64 on the identical bytes 10 days ago). §D routes findings for C105.
**Cross-spec authorities re-read** (passages, not recalled): atp-adp-cycle.md §2.4 (Slashing) L170, §4.2 (Value Flow Tracking) L362; dictionary-entities.md §2.2 (`dictionary_trust_config`); the C94 dictionary-entities 2nd-delta audit doc (`docs/audits/C94-dictionary-entities-2nd-delta-2026-06-24.md`); the C78 atp-adp interval-audit doc + #368 commit body.

---

## §A. Verification of C65 Remediation (frozen target — 7th consecutive)

entity-types.md is **byte-identical** since the C65 remediation (#344 `5baa160f`, 2026-06-16). All 7 autonomous C65 remediations **HELD token-by-token**, 0 regressed, **0 `&#`/HTML-entity artifacts**:

| C65 item | Origin | Site | Current state | Verdict |
|----------|--------|------|---------------|---------|
| A.1 (flagship) | C26-H1 value | §3.1 L153 | `"rights": ["presence", "interact", "accumulate_reputation"]` | **HELD** |
| A.1 prose | C26-H1 value | §6.2 L495 | "Provides base rights: **Presence**, interact, accumulate reputation" | **HELD** |
| B1 | witness format | §3.1 L151 | `["lct:web4:witness:1", "lct:web4:witness:2"]` (colon form) | **HELD** |
| B3 | Hybrid mode | §2.1 L33 | `Agentic/Responsive/Delegative` (was undefined "Mixed") | **HELD** |
| B4 | Infra mode slip | §2.1 L35 | Mode column = `None` (was "Passive", an energy not a mode) | **HELD** |
| B6 | slashing vocab | §2.3 L102 | "ADP **consumed** ... distinct from the punitive, authority-executed *slashing* of `atp-adp-cycle.md` §2.4" | **HELD** |
| A.2 + B5 | role-list home + six-vs-seven | §4 preamble L281 | "**six** SAL-specific roles ... canonical home is **`society-roles.md` §2** (resolved per `SOCIETY_SPECIFICATION.md` §1.2.5 / C51)" | **HELD** |
| A.2 | role-name reconciliation note | §4.2 L304 | "canonical *home* ... settled ... what remains open is only ... role-*name* reconciliation" | **HELD** |

Together A.1+B1 make the §3.1 provenance note ("the fields `entity` through `obligations` match canonical `Web4BirthCertificate` §2.2") **literally true at value AND format level** — the key-only gap the C56 method caught at C64 is fully closed.

### A.1 Standing carries — all STAND, re-verified bidirectionally

| Carry | Class | Re-verification at C104 | Verdict |
|-------|-------|--------------------------|---------|
| **C8-L3** | deferred content-merge | §12↔§3.1 citizen-example redundancy; non-contradictory | **STANDS** (deferred) |
| **C23-H1** | OPEN design-q | birth-cert field-set (`ledgerProof`/`parentEntity` superset vs SAL §2.2); untouched by C65 | **STANDS** |
| **C24-H1** | OPEN design-q (cross-track) | LCT-ID divergence `lct:web4:*` (pervasive) vs `policy:*` (§13.2) vs `did:web4:key:*` (LCT-spec subject); do NOT self-resolve | **STANDS** |
| **B2** | cross-track (SDK) | SDK `entity.py` Device hardcodes `ACTIVE` — cannot model Passive Device per §2.1/§2.3; SDK unchanged since Apr (`759eaefa`) | **STANDS** |
| **B7** | cross-track → **3-doc** | §10.2 `trust_requirements` vs dictionary-entities §2.2 `dictionary_trust_config`; **see §B inbound** | **STANDS, elevated** |
| **B9** | design-q | Task energy "Active (when R6-capable)" vs SDK fixed ACTIVE; §2.3 omits Task from R6-capable list | **STANDS** |
| **B10** | design-q / editorial | §13 Policy lacks an LCT-structure JSON example (asymmetry vs §10.2/§11.2) | **STANDS** |
| **B11** | design-q | §13.1 frames SAGE/IRP integration as if Web4-normative | **STANDS** |
| **B12** | cross-track (nicety) | §2.3 passive-rep lacks explicit cross-ref to atp-adp §4.2; **see §B** | **STANDS** |

No carry RESOLVED or HARDENED into a new defect this interval. (The one carry that resolved-downstream at C64 — C25-H1, role-list home — was cleaned up by C65 A.2 and remains correctly closed; the §4.2/§4-preamble notes are still accurate.)

---

## §B. Corpus-Delta + Inbound Cross-Doc Carry

**Moved-sibling surface.** Of the siblings cited by C64 (SAL, society-roles, dictionary-entities, atp-adp-cycle, LCT-spec, SDK `entity.py`), **only `atp-adp-cycle.md` moved since C65** (C79 #368 `db394dfa`, 2026-06-20). All others are at-or-before C65. So the entire corpus-delta surface is atp-adp-C79.

### B-delta.1 — atp-adp-C79 → entity-types B6 cross-ref: VERIFIED STABLE + REINFORCED

entity-types §2.3 L102 (the C65-B6 remediation) cross-cites "the punitive, authority-executed *slashing* of `atp-adp-cycle.md` §2.4 (evidence-gated destruction of ATP for law violations)." Re-read of the current atp-adp §2.4 "Slashing (ATP Destruction)" (L170–211): `has_slashing_authority(caller)` gate, witness-attested, "law violations or failed commitments," "**destroys** ATP: the slashed amount is removed from supply" — **exactly what the entity-types note claims**. Moreover atp-adp-C79 **added** a new note (#368 diff) describing "slashing (§2.4) is a carve-out" from the normal cycle → §2.4 slashing is now an even-more-load-bearing, cross-referenced primitive. **The entity-types B6 note remains true; reinforced, not stale.**

### B-delta.2 — atp-adp-C79 → entity-types B12 nicety: STANDS

C79's §4.2 (Value Flow Tracking) change concerns omitting the **beneficiary/consumer** from the value-attribution cascade — orthogonal to the **passive-resource** omission that B12 references. entity-types §2.3 (Passive Resources earn "Utilization frequency × effectiveness," "no reputation updates") remains consistent with atp-adp §4.2. B12 stays a **nicety** (an explicit cross-ref would help a reader), **not a defect**.

**atp-adp interval-audit routing**: the C78 atp-adp delta-audit doc has **0 entity-types mentions**; #368's commit body routes only the 5 atp-adp-internal autonomous findings. **No carry routed back to entity-types from the atp-adp side.**

**Net from corpus-delta: 0 net-new.**

### B-inbound.1 — C94 dictionary 2nd-delta elevates C64-B7 to a 3-doc sibling-canonicity bundle

The C94 dictionary-entities 2nd-delta audit (`docs/audits/C94-...-2026-06-24.md` §C "inbound") **confirmed C64-B7 from the dictionary side and upgraded it**: entity-types §10.2 (L587 `trust_requirements`, with subordination pointer L620 "For complete specification, see dictionary-entities.md") is a **THIRD** normative Dictionary LCT structure, alongside:
1. `dictionary-entities.md` §2.2 (`dictionary_trust_config`) — **canonical owning spec**
2. `protocols/web4-dictionary-entities.md` (the C52-B26 sibling)
3. `entity-types.md` §10.2 (`trust_requirements`, **subordinate** by its own L620 pointer)

C94's disposition (§C/§D): the fix **belongs on the entity-types side** (sync §10.2's outer key + abbreviated structure to canonical), and the §10.2 L620 subordination pointer is the **resolution template** the protocols/ sibling lacks. But the choice of canonical form is **gated on the operator's B26 sibling-canonicity decision** — so it is **cross-track / operator, NOT an autonomous entity-types finding**. Recorded here so the C105 slot does not self-apply, and so the operator's eventual B26 decision accounts for all three sources.

---

## §C. Fresh-Internal Refute-by-Default Pass

A single Explore pass (proportional to a 7th-consecutive byte-frozen target whose full 8-lens 26-raw sweep ran on the identical bytes at C64, 10 days ago), fed the C64 prior-finding + DEMOTED list and instructed to refute by default. **Result: 0 net-new internal contradictions.**

Checked and clean: §1–§14 numbering (no duplicate/skipped headings); §2.1 entity table (15 types) ↔ §2.2 behavioral modes ↔ §2.3 energy classes (every row's mode/energy consistent with the prose, incl. the C65-fixed Hybrid/Infrastructure cells); §3.4 role-pairing prose ↔ §5.1 birth-cert pseudocode ↔ §3.1 JSON-LD; Citizen-role immutability across §3.1/§3.4/§6.2/§12; all internal `see §X` cross-refs resolve to extant sections (L261→§3.2, L275→§3.4, L290→§4.2, L422/L433→§3.1). This corroborates C94's general observation that a frozen, twice-audited target's fresh-internal pass is near-certain empty; the yield is on the cross-ref/inbound surface.

---

## §D. Disposition Summary & C105 Routing

| Finding | Class | Disposition |
|---------|-------|-------------|
| 7/7 C65 remediations | §A | **HELD** token-by-token; 0 regressed, 0 artifacts |
| All 9 standing carries (C8-L3, C23-H1, C24-H1, B2, B7, B9, B10, B11, B12) | §A | **STAND**; none resolved/hardened into a defect |
| atp-adp-C79 → B6 cross-ref | §B corpus-delta | **VERIFIED STABLE + REINFORCED** (§2.4 slashing load-bearing) |
| atp-adp-C79 → B12 nicety | §B corpus-delta | **STANDS** (orthogonal §4.2 change; still a nicety, not a defect) |
| C94 inbound → C64-B7 | §B inbound | **Elevated to 3-doc B26 sibling-canonicity bundle**; fix entity-types-side but **operator-gated** → cross-track, NOT autonomous |
| Fresh-internal pass | §C | **0 net-new internal contradictions** |

**C104 distinct new findings: 0. → C105 entity-types remediation slot = NO-OP** (matches the C95/C97/C99/C101/C103 frozen-wrap pattern: when a 2nd-delta audit finds 0 autonomous defects, the paired remediation turn is a no-op and the rotation advances).

**Routed off-target (all standing, none gate a normal AUDIT turn — surface as ONE operator memo when available)**:
- **C64-B7** (3-doc Dictionary-LCT-structure canonicity) → folds into the dictionary **B26** sibling-canonicity bundle; operator picks the canonical form, then the fix lands on the entity-types §10.2 side.
- **C23-H1** (birth-cert field-set superset) + **C24-H1** (LCT-ID 4-way divergence) → open design-Qs, do NOT self-resolve.
- **B2** (SDK Device per-instance energy) → SDK-track.
- **B9** (Task non-R6 metabolism), **B10** (Policy LCT JSON example), **B11** (SAGE optionality framing) → design-q, operator.
- **B12** (passive-rep cross-ref to atp-adp §4.2) → cross-track nicety.

**Rotation**: next-oldest after entity-types (C64/C65, 2026-06-16) is **`errors.md`** (last audited C66/C67, 2026-06-16) for its 2nd-delta (≈C106, lineage C30→C66→C67→C106).

---

## §E. Lessons (for memory)

1. **7th consecutive frozen-wrap, same shape.** entity-types byte-frozen 10 days; §A = pure verification (7/7 held, 9 carries stand); §B yield is **entirely** on the corpus-delta + inbound-carry surface. The pattern (files churn slower than the +2-per-file audit cadence → wraps hit frozen targets) is fully locked across C92/C94/C96/C98/C100/C102/**C104**.
2. **The moved sibling was again atp-adp-cycle.md** (C79) — the same doc that surfaced at C102 (ISP). A single recently-churned SSOT sibling tends to be the corpus-delta surface for multiple downstream frozen targets in the same wrap window. Its B6 cross-ref REINFORCED (not stale) because C79 *added* a §2.4 slashing carve-out note — a sibling remediation can strengthen a downstream note rather than break it.
3. **Inbound carry came from the dictionary side, not the target.** C94's dictionary audit independently re-found C64-B7 and upgraded it 2-doc→3-doc — visible only by reading the *sibling's* interval-audit doc, never by reading entity-types alone ([[feedback_cross_doc_carry_inbound]]). The §10.2 L620 subordination pointer doubles as the resolution template the protocols/ sibling lacks.
4. **Proportional §C earned its keep without a fleet.** One refute-by-default Explore pass confirmed 0 net-new internal — the right instrument for a twice-audited frozen file, avoiding the cost of re-running the C64 8-lens 26-raw workflow on identical bytes.

---

## Cross-Reference to Prior Audits

| Audit | Spec | Result |
|-------|------|--------|
| C8 | entity-types.md (first pass) | 10 (3H/4M/3L); 9 remediated, L3 deferred |
| C26 | entity-types.md (1st delta) | 5 new + 1 INFO; 4 autonomous remediated (#260) |
| C64 | entity-types.md (2nd delta) | 26 raw → 11 distinct (0 HIGH/4 MED/5 LOW/2 INFO); 7 autonomous routed |
| C65 | entity-types.md (remediation) | 7 autonomous applied (#344 `5baa160f`) |
| **C104** | **entity-types.md (2nd-delta re-audit, 3rd pass)** | **§A: 7/7 C65 HELD token-by-token, 0 regressed, 0 artifacts; 9 carries STAND. §B: only atp-adp-C79 moved → B6 cross-ref REINFORCED, B12 stands, 0 net-new; C94 inbound elevates C64-B7 to 3-doc B26 bundle (operator-gated). §C: 0 net-new internal. → C105 = NO-OP.** |
