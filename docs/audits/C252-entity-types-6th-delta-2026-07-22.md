# C252 Audit: `entity-types.md` — 6th-Delta Re-Audit (7th Pass)

**Date**: 2026-07-22
**Auditor**: Autonomous session (Legion, web4 track) — firing `20260722-180036`, LEAD voice
**Document**: `web4-standard/core-spec/entity-types.md` (804 lines, blob `a2dda417`)
**Lineage**: C8 (2026-05-22, 10 findings, 9 remediated) → C26 (1st delta, #260) → C64 (2nd delta, 26 raw → 11 distinct) → C65 (remediation, 7 applied, #344 `5baa160f`) → C104 (0 net-new) → C137 (0 net-new) → C176 (0 spec-side net-new; C176-N1/N2 SDK-track) → C214 (5th delta / 6th pass — FIRST non-frozen delta since C65: #523 Effector §4.8; regression-CLEAN; C214-N1 applied to sibling) → **C252 (this audit, 6th delta / 7th pass)**
**Rotation note**: round-robin advanced from C250 (ISP 6th delta, #567 merged `c76b4944`) → the C251 remediation slot is a **no-op** (C250 found 0 spec-side ISP defects) → the wheel advances to the next file in fixed order, `entity-types.md` (last audited C214, 2026-07-18).

## Headline: RE-FROZEN — entity-types.md byte-frozen since #523; 0 net-new (7th pass)

entity-types.md **moved** at C214 (#523 grew it +63 lines with §4.8 Effector). Since #523 (`1354e4c2`, 2026-07-14 13:03) it has **not moved again**: `git log 1354e4c2..HEAD -- entity-types.md` is **empty** — the exact blob C214 audited and consumed, byte-frozen for 8 days. C252 is therefore a **frozen-target delta**, not a mover-audit. The audit's center of mass is the standard frozen-delta surface:

1. **§A** — all C214 findings + prior carries HELD by construction (spec byte-identical).
2. **§B** — C214-N1 (the sibling `reputation-computation.md` forward-ref note applied at C214) still HELD; all 8 §4.8 outbound citations HELD (every cited sibling frozen since C214).
3. **§B′** — the SDK mirror re-derived at live HEAD across Python (`entity.py`/`role.py`) **and** `web4-core/src/{lct,role,ratchet,attestation,did}.rs`, per the standing method guard. Movers since C214 (#538, #540, #544, ratchet.rs) are adjudicated for an entity-types face.

**Cross-artifact authority re-read at live HEAD (passage, not recalled):** the #523 blob region (§4.8 + L281 preamble); `web4-core/src/lct.rs` `EntityType` (L28–53) + `authority_ratchet` field (L173–180); `web4-core/src/role.rs` `SocietyRole` (L33–79); `web4-core/src/ratchet.rs` header + `RatchetRequirement`/`FactorClass`/`SovereignStructureProof` (L64–180); `web4-core/src/did.rs` (EntityType use-sites only); `web4-standard/implementation/sdk/web4/role.py` `SocietyRole` (L43+); `web4-standard/implementation/sdk/web4/entity.py` `EntityType`/`EntityTypeInfo` taxonomy (full 15-type table); `reputation-computation.md` §"Evidence-basis role" note (L384–396); the §4.8 cited siblings `hub-law-schema.md`, `society-roles.md`, `web4-society-authority-law.md`, `act.rs`; the C214 prior audit doc; C246/C248/C250 memory guards.

---

## §A. Regression Check — spec byte-frozen ⇒ all prior findings HELD by construction

`git log 1354e4c2..HEAD -- web4-standard/core-spec/entity-types.md` = **empty**. Blob at HEAD is `a2dda417` (804 lines), byte-identical to the C214 snapshot. Every C214 conclusion that is a property of the file text therefore **HOLDS by construction** — there is no edit that could have regressed it:

| C214 conclusion | C252 status | Basis |
|---|---|---|
| §4-preamble count edit exact (eight subsections / seven SAL roles incl. Effector) | **HELD** | text unchanged |
| 7 C65 remediations (A.1 §3.1 L153, §6.2; B1/B3/B4 §2.1–3.1; B6 §2.3 L102; A.2+B5 §4 L281) | **all HELD** | all sites byte-unchanged |
| 9 standing carries (C8-L3 §12↔§3.1; C23-H1 §5.1; C24-H1 §13.2; B2/B9 §2.1; B7 §10.2; B10/B11 §13; B12 §2.3) | **all STAND** | all sites byte-unchanged; none resolved/hardened |
| §4.8 Effector insertion is clean-additive, 0 internal contradictions (C214 §C adversarial refute) | **HELD** | insertion text unchanged; refute result stands |

**0 regression possible on a byte-frozen target.** The C215 remediation slot was correctly a NO-OP at C214 (sole net-new landed in a sibling); nothing has since forced an entity-types.md edit.

---

## §B. Cited-Sibling Freshness & the C214-N1 Applied Note

### B.1 — All 8 §4.8 outbound citations HELD (every cited sibling frozen since C214)

C214 §B.1 verified 8 outbound citations from §4.8. Re-derived at live HEAD, **none of the cited siblings has moved since the C214 snapshot (2026-07-18)**:

```
git log --since=2026-07-17 -- hub-law-schema.md society-roles.md \
    web4-society-authority-law.md web4-core/src/act.rs   →  (empty for all four)
```

Since both endpoints (entity-types §4.8 *and* every target) are byte-frozen, all 8 citations — response vocabulary (`hub-law-schema.md`), kinetic class, RWOA+S+V+F gate (F-a/F-b), Coercive/Extractive category (`reputation-computation.md` §4), Auditor recognition-sibling (§4.5), SAL delegation (§3.3/§5.6), `consequenceClass: "reversible"` (`act.rs` `ConsequenceClass` snake_case), and the `QUARANTINE-ON-AGENCY-OVERRIDE` example rule — **HOLD by construction**. The tri-file registration (entity-types §4.8 / society-roles §4.1 / SAL §5.6+§7.1.1) remains mutually consistent (all three frozen).

### B.2 — C214-N1 (reputation-computation.md forward-ref note) HELD

C214 applied C214-N1 to the sibling `reputation-computation.md` (the "Evidence-basis role" note, refreshed to state that response vocabulary [#522] and the Effector role [#523] are now ratified while cross-boundary adjudication [N4] remains proposed). Verified at live HEAD:

- `git log --since=2026-07-17 -- reputation-computation.md` shows only `2bc3bafb` — the **C214 audit commit itself (#541)** that applied the note. No subsequent edit.
- The note text (L384–396) reads the applied version verbatim: *"The response side has since been partially ratified: the **response vocabulary** … in `hub-law-schema.md` … and the **Effector role** … in `entity-types.md` §4.8 / `society-roles.md` §4.1 / `web4-society-authority-law.md` §5.6 (W4IP N2). Cross-boundary adjudication remains proposed … and is not normative until ratified."*
- Independently re-confirmed regression-clean at C232 (reputation-computation 6th delta). **HELD.** Do NOT re-open.

---

## §B′. SDK-Mirror Re-Derivation at Live HEAD (Python + `web4-core/src/*.rs`)

Per the standing method guard, the mirror set is re-derived at live HEAD across **both** SDKs. Four movers touched entity-types-adjacent Rust files since C214; each is adjudicated for an entity-types face.

### B′.1 — Effector role-enum mirror STILL absent → INFO, already-routed (not net-new)

`grep -ri effector web4-core/src/ web4-standard/implementation/sdk/web4/*.py` → **0 hits**. Both role enums still carry Effector's recognition-side sibling **Auditor** but not Effector:
- `web4-core/src/role.rs` `SocietyRole` (L33–79): Sovereign/LawOracle/PolicyEntity/Treasurer/Administrator/Archivist/Citizen/Witness/**Auditor**/Custom — **no `Effector`**. `git log --since=2026-07-17 -- role.rs` = empty (frozen since C214).
- `role.py` `SocietyRole` (L43+): …/WITNESS/**AUDITOR** — **no `EFFECTOR`**. Frozen since C214.

This is the expected SDK-lags-spec shape. **NOT net-new**: `SESSION_FOCUS.md` item 0d routes the Effector **code half** to HUB-track's pending Phase-2 PR ("Legion reviews when it's up"). The HUB Phase-2 enactment PR has **not yet landed** as of this fire (grep still 0). Recording per [[feedback_prose_is_not_ledger]]: already owned in the queue — do NOT create a competing route. **Direction = SDK lags spec (spec CORRECT); owner = HUB-track; Legion action = review the enactment PR when it lands (carry the `unwrap_or_default()` NIT + parse-don't-enact enforcement check).** INFO, carry-only.

### B′.2 — C176-N1 (Rust `EntityType` coverage) STANDS unchanged: 7 types absent

Re-derived at live HEAD, `web4-core/src/lct.rs` `EntityType` (L28–53) = 9 variants covering 8 spec §2.1 types: Human, AiSoftware, AiEmbodied (AI split), Organization, **Society**, Role, Task, Resource, Hybrid. **No variant added since C214** (Society was added by #516 *before* C214; the #538/#540/#544 movers touched the `Lct` **struct fields**, not the `EntityType` enum). Python `entity.py` carries the **full 15-type taxonomy** (Society/Device/Service/Oracle/Accumulator/Dictionary/Policy/Infrastructure all present with `EntityTypeInfo` metadata).

**C176-N1 STANDS unchanged: 7 Rust types still absent** — Device, Service, Oracle, Accumulator, Dictionary, Policy, Infrastructure. Direction = SDK lags spec (spec CORRECT); SDK-track, carry-only, travels with the C172/C174/C176 SDK-mirror bundle. **C176-N2** (AI-split double-models embodiment vs the `HardwareBinding` axis) **STANDS** (INFO).

### B′.3 — `ratchet::RatchetRequirement` (#529/#544) is DISJOINT from the entity-types taxonomy (guard-predicted, CONFIRMED)

The C252 memory guard flagged the NEW web4-core type `ratchet::RatchetRequirement` (ratchet.rs introduced by #529 `7b048a78`, 2026-07-16; wired to `lct.rs authority_ratchet` by #544 `2ec6ae09`, 2026-07-18) and asked whether entity-types should register a ratchet-bearing entity face — **predicting DISJOINT**. Re-derived live, the prediction is **confirmed**:

- `ratchet.rs` header states verbatim: *"The Sovereign is a **role** (SAL §2.1), not a special entity. A society's [authority is proven from structure]."* The type is `RatchetRequirement` + `FactorClass` + `SovereignStructureProof` — an **authority-assurance mechanism** (monotone, provable-from-structure sovereign-authority level), **not a new `EntityType`**.
- `lct.rs` L173–180: `authority_ratchet: Option<crate::ratchet::RatchetRequirement>` is documented as *"a provable part of the LCT … `None` on every non-sovereign LCT"*. It attaches to the **Sovereign role's LCT**, which entity-types already covers via §4.1 Society + §4.2 Authority — it introduces **no new entity type**.
- Grep `ratchet` / `RatchetRequirement` against entity-types.md → **0 hits** (as with ISP at C250 and appropriately so).

The ratchet is already booked as **LCT-structure face C248-N2** + **SAL face C246-N1**. It is **NOT** an entity-types face — manufacturing a 3rd (entity-types) face would double-count. **DISJOINT; book-once, not re-discovered.**

### B′.4 — `attestation.rs` plural `citizenships` (#538) + `lct.rs operational_key`/`authority_ratchet` (#538/#540/#544) are LCT-structure faces → DISJOINT

The remaining movers since C214 — #538 (`attestation.rs` plural `citizenships: Vec<BirthCertificateRef>`, `lct.rs`), #540 (operational-key vouching), #544 (`authority_ratchet`) — all reshape **`Lct` struct fields / attestation containers**, not the entity taxonomy. They are LCT §2.3/§1.2-structure faces already booked at **C248-N1/N2** (and the citizenship-shape premise refresh at SAL C23-H1). None touches entity-types §2.1's enumeration of entity **types**. `did.rs` merely *consumes* `EntityType::{Human,AiSoftware}` in test constructors (L203–279) — no new primitive. **All DISJOINT from entity-types.**

**Net from SDK-mirror: 0 net-new.** Effector-mirror = already-routed HUB INFO; C176-N1 STANDS (7 absent); C176-N2 STANDS; ratchet + citizenship/key movers DISJOINT (booked on LCT/SAL faces, not entity-types).

---

## §C. Fresh-Internal Refute-by-Default Pass

The primary claim to refute this delta is **"entity-types.md is genuinely frozen and 0-net-new — nothing moved that entity-types must answer."** Refutation attempts:
1. *Did entity-types.md move and the empty git-log lie?* — Blob hash `a2dda417` re-derived directly from HEAD; `1354e4c2..HEAD -- entity-types.md` empty; the file's last touching commit is #523. **Frozen confirmed.**
2. *Did a §4.8 citation target move and strand the reference?* — All four cited siblings + `act.rs` show empty `--since=2026-07-17` logs. **No stranded citation.**
3. *Is the ratchet actually a stealth new entity type that §2.1 must enumerate?* — `ratchet.rs` self-declares Sovereign as a role-not-entity; `authority_ratchet` is `None` on non-sovereign LCTs; 0 grep hits in entity-types. **Not an entity type; DISJOINT.**
4. *Did the HUB Effector Phase-2 PR land, making the mirror-gap net-new-resolvable this fire?* — `grep -ri effector` SDK = 0 hits. **Not landed; INFO still parked with HUB-track.**

**No refutation succeeds. The frozen 0-net-new verdict survives adversarial verification.**

---

## §D. Disposition Summary & C253 Routing

| Finding | Class | Disposition |
|---------|-------|-------------|
| entity-types.md byte-frozen since #523 (`1354e4c2`, 8d) | §A | **CONFIRMED** (`1354e4c2..HEAD` empty; blob `a2dda417`) |
| 7 C65 remediations + count edit | §A | **HELD** by construction |
| 9 standing carries | §A | **STAND** by construction |
| 8 §4.8 outbound citations | §B.1 | **HELD** (all cited siblings frozen since C214) |
| C214-N1 reputation-computation.md note | §B.2 | **HELD** (only #541 touched it; note = applied version; re-confirmed C232) |
| Effector SDK role-enum mirror (Rust + Python) | §B′.1 | **INFO, already-routed to HUB-track Phase-2; NOT net-new** (grep still 0) |
| C176-N1 Rust `EntityType` coverage | §B′.2 | **STANDS** — 7 types absent (Device/Service/Oracle/Accumulator/Dictionary/Policy/Infrastructure); Python carries all 15 |
| C176-N2 AI-split embodiment | §B′.2 | **STANDS** (INFO) |
| `ratchet::RatchetRequirement` (#529/#544) | §B′.3 | **DISJOINT** — Sovereign=role-not-entity, no new EntityType; booked LCT C248-N2 + SAL C246-N1 |
| `citizenships`/`operational_key`/`authority_ratchet` (#538/#540/#544) | §B′.4 | **DISJOINT** — LCT-structure faces (C248-N1/N2), not entity-types §2.1 |
| Fresh-internal refute pass | §C | **0 net-new** — frozen 0-net-new verdict survives |

**C252 distinct net-new findings: 0.** entity-types.md is spec-side clean and byte-frozen; every mover since C214 is either already-routed (Effector mirror), a standing carry (C176-N1/N2), or DISJOINT (ratchet + LCT-structure movers, booked on other faces). **→ C253 entity-types remediation slot = NO-OP** (do NOT manufacture an edit). This is the **fourth** 0-net-new entity-types delta (C104/C137/C176-spec-side/C252), consistent with the frozen-wrap pattern.

**Routed / carry-forward (all unchanged, no new routes):**
- Effector SDK role-enum mirror → HUB-track Phase-2 code half (SESSION_FOCUS 0d); Legion reviews the enactment PR when up (carry `unwrap_or_default()` NIT + parse-don't-enact enforcement check).
- C176-N1 (7 Rust `EntityType` absent) + C176-N2 (AI-split) → SDK-track, C172/C174/C176 bundle.
- C214-N1 → HELD in sibling; do not re-open.
- Standing design-Qs (C23-H1, C24-H1, B7, B2/B9, B10/B11) → operator memo, unchanged.

**Rotation**: next file in fixed order after entity-types is **`errors.md`** (lineage C30→C66→C67→C106→C138→C178→C216→**C254**). SDK-mirror guard for C254: re-derive the errors-primitive implementers at live HEAD across Python **and** `web4-core/src/error.rs`; check whether the #538/#544 movers introduced new error variants the spec must enumerate.

---

## §E. Lessons (for memory)

1. **A file that un-froze one delta ago can re-freeze the next.** entity-types moved at C214 (#523 Effector) and has been byte-frozen for the 8 days since. The C214 lesson ("frozen ≠ permanently frozen — check the blob every delta") cuts both ways: a *mover* delta is not permanently a mover. C252 checked the blob hash first (`a2dda417`, `1354e4c2..HEAD` empty) and correctly reverted to the frozen-wrap surface (regression-by-construction + mirror re-derivation) rather than re-litigating the #523 insertion.
2. **A guard's DISJOINT prediction is a hypothesis to test at live HEAD, not to assume.** The C252 memory guard predicted `ratchet::RatchetRequirement` is DISJOINT from entity-types "(likely DISJOINT, re-derive live)". Re-reading `ratchet.rs`'s header ("Sovereign is a *role*, not a special entity") + `authority_ratchet: None` on non-sovereign LCTs + 0 grep hits **confirmed** it — but the confirmation is the audit's product, not the guard's assumption. Book-once (LCT C248-N2 + SAL C246-N1); do NOT manufacture a 3rd entity-types face for the same primitive.
3. **"Is it net-new?" before "is it a finding?" — twice over.** Both the Effector mirror gap (owned by HUB-track queue 0d) and the #538/#544 LCT-structure movers (booked at C248) *look* like fresh §B′ yield on a frozen-target delta but are already-ledgered. Recording them as net-new would double-count owned work. The [[feedback_prose_is_not_ledger]] discipline: promote un-ledgered observations, do NOT re-discover already-ledgered ones. On a frozen target the entire §B′ yield reduces to "confirm the ledger still holds."

---

## Cross-Reference to Prior Audits

| Audit | Result |
|-------|--------|
| C8 | first pass — 10 (3H/4M/3L); 9 remediated |
| C26 | 1st delta — 5 new + 1 INFO; 4 remediated (#260) |
| C64 | 2nd delta — 26 raw → 11 distinct; 7 routed |
| C65 | remediation — 7 applied (#344 `5baa160f`) |
| C104 | 0 net-new → C105 NO-OP |
| C137 | 0 net-new → C138 NO-OP |
| C176 | 0 spec-side net-new; C176-N1 (Rust EntityType) + C176-N2 SDK-track |
| C214 | 5th delta — FIRST non-frozen since C65 (#523 Effector §4.8, +63); count exact, 7 C65 HELD, 9 carries STAND, 8/8 citations resolve, tri-file consistent; C214-N1 (reputation-computation.md:389 stale note) LOW, APPLIED to sibling; C176-N1 NARROWED 7/15→8/15 (Society #516) → C215 NO-OP |
| **C252** | **6th delta (7th pass) — RE-FROZEN: byte-frozen since #523 (`1354e4c2`, 8d, blob `a2dda417`); `1354e4c2..HEAD` empty. §A: 7 C65 + count edit + 9 carries HELD/STAND by construction. §B: 8/8 §4.8 citations HELD (all cited siblings frozen since C214); C214-N1 reputation note HELD (only #541 touched it; re-confirmed C232). §B′ (mirror re-derived live): Effector role-enum STILL absent → HUB-track INFO, not net-new; C176-N1 STANDS (7 Rust types absent, Python carries 15); C176-N2 STANDS; `ratchet::RatchetRequirement` (#529/#544) DISJOINT (Sovereign=role, no new EntityType; booked LCT C248-N2 + SAL C246-N1); #538/#540 citizenship/key movers DISJOINT (LCT-structure faces). §C refute: frozen 0-net-new survives. → C253 NO-OP; ZERO net-new. Rotation → errors.md (C254).** |
