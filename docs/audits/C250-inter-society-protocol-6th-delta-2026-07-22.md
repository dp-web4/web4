# C250: `inter-society-protocol.md` (ISP) 6th-delta RE-Audit

**Date**: 2026-07-22
**Track**: web4 (Legion autonomous session, slot `web4-20260722-120002`)
**Instrument**: C-series delta RE-audit; **6th delta** on `inter-society-protocol.md` (lineage C6 → C25 → **C62** → remediation **C63** (#341) → C102 → C136 → **C174** → **C212** → **C250**)
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2 DRAFT, 384 lines, last edited `0405f331` PR #341, 2026-06-16 — **BYTE-FROZEN 36 days**; `git diff 0405f331 HEAD` = empty; blob `22bf6c1d`; unchanged since the C212 snapshot 2026-07-17)
**Method**: §A prior-finding verification (held-by-construction on a byte-frozen target) + `&#` artifact sweep + bidirectional carry re-verification. §B **frozen-target corpus-delta surface** over ISP's 6 cited sibling docs since the C212 snapshot, adjudicated at **cited-hunk granularity** with adversarial refute-by-default. §B′ **SDK-MIRROR EXPANSION** per the standing C172/C174 method guard: re-derive ISP's primitive-implementers at live HEAD across Rust `web4-core` (`society.rs`, `role.rs`, `lct.rs`, `attestation.rs`) and the Python SDK, adjudicating the two Rust movers since C212 against ISP's cited surface, applying the **book-once** guard ([[feedback_prose_is_not_ledger]] / C176).

**Slot note (rotation):** this fire is the **C250 slot**, advanced +2 from C248 (LCT 6th-delta, PR #565 merged `2e8f2ce4`). C249 was correctly a NO-OP on the LCT spec side (LCT byte-frozen since C210; C248 produced 0 spec mutations, only 2 routed LOW mirror findings) → no remediation turn manufactured; rotation advanced LCT → **ISP**.

**Cross-referenced (read live at audit-write)**:
- `web4-standard/core-spec/atp-adp-cycle.md` (frozen `256ab51d` 2026-07-07) — bears on B5/B10/B11
- `web4-standard/core-spec/mcp-protocol.md` (frozen `3e765345` 2026-07-13, §7.8 async mailbox — C212-adjudicated DISJOINT) — bears on B1/B2/B3 + §8 row
- `web4-standard/core-spec/web4-society-authority-law.md` (SAL) (frozen `1354e4c2` 2026-07-14, §5.6 Effector — C212-adjudicated DISJOINT) — bears on B13 + §2.1/§5.1/§8
- `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (frozen `87377c38` 2026-07-14, §7.3 — C212-adjudicated DISJOINT) — bears on B9
- `web4-standard/core-spec/society-roles.md` (frozen `1354e4c2` 2026-07-14, Effector — C212-adjudicated DISJOINT) — bears on B12/B16 + §2.2 Diplomat
- `web4-standard/core-spec/LCT-linked-context-token.md` (frozen `d89595e8` 2026-07-16, §1.2 insert #531 — C212-adjudicated DISJOINT) — bears on §2.1/§8 witness-quorum cross-refs
- **`web4-core/src/society.rs`** (Rust; **FROZEN `fe96aad0` 2026-07-09**, pre-C174) — the ISP §2/§5/§6 mirror
- **`web4-core/src/role.rs`** (Rust; **FROZEN `fe96aad0` 2026-07-09**) — role primitives
- **`web4-core/src/attestation.rs`** (Rust; **MOVED `0e997079` 2026-07-17, #538**) — the plural `citizenships` reshape C212-I1 flagged in-flight
- **`web4-core/src/lct.rs`** (Rust; **MOVED `2ec6ae09` 2026-07-18, #544**) — new `authority_ratchet` field
- `web4-standard/implementation/sdk/web4/{federation,role}.py` (frozen) — Python inter-society mirrors

**Prior audits**: C6 (13 → #215), C25 (6 NEW → #258), **C62** (16 distinct → remediation #341: 9 autonomous + B2-interim), C102 (0 net-new — first clean), C136 (0 net-new — 2nd clean), **C174** (0 doc-net-new; +2 from the then-new `society.rs` SDK mirror: N1 LOW, N2 INFO), **C212** (0 net-new; C212-I1 INFO corroborating in-flight #538).

---

## Summary

| Severity | NEW (C250) |
|----------|-----------:|
| HIGH     | 0 |
| MEDIUM   | 0 |
| LOW      | 0 |
| INFO     | 0 net-new (one standing INFO carry **RESOLVED** — C212-I1) |
| **Total NEW distinct defects** | **0** |

**Result**: **FROZEN-SPEC CLEAN + ALL DOC SIBLINGS FROZEN + SDK-MIRROR BOOK-ONCE → 0 net-new; one standing carry RESOLVED.** The ISP *spec* is byte-identical to its C63 remediation (`0405f331`, 36 days) and unchanged since the C174/C212 snapshots. All 10 C63 remediations HELD by byte-freeze; 0 regressions; 0 `&#` artifacts. **§B is the first ISP delta where NO cited doc-sibling moved** — all six are byte-frozen since the C212 snapshot (last commits ≤ 2026-07-16 < 2026-07-17), so every prior DISJOINT adjudication (mcp §7.8, SAL/society-roles Effector #523, SOCIETY_SPEC §7.3, LCT §1.2 #531) stands verbatim, nothing re-litigated. **§B′ yields 0 net-new for two reasons and one substantive resolution:**

- `society.rs` / `role.rs` (the ISP §2/§5/§6 mirror) are **byte-frozen since `fe96aad0` (2026-07-09), pre-C174** → **C174-N1 (LOW) and C174-N2 (INFO) HELD by construction.**
- The two Rust movers since C212 — `attestation.rs` #538 (plural `citizenships`) and `lct.rs` #544 (`authority_ratchet`) — were **both already booked by the C248 LCT delta 4 days ago** (C248-N1 / C248-N2). Per the book-once guard, a mirror surface a sibling delta already logged is **not re-discovered as net-new here**.
- **C212-I1 RESOLVED.** #538 landed the exact singular→plural citizenship reshape C212-I1 had recorded as in-flight. The SDK now carries `Lct.citizenships: Vec<BirthCertificateRef>` ("one per society the entity is a citizen of"), which **realizes** ISP §2.2/§5.1's multi-society citizenship model and ISP §9's open cross-federation-citizenship item. The under-representation C212-I1 flagged is gone. #544's `authority_ratchet` is **DISJOINT** from ISP (ISP cites no ratchet/authority-level anywhere — grep = 0); it belongs to the LCT-structure and SAL faces (C248-N2 / C246-N1), not ISP.

**Headline (method):** C250 is the ISP delta where *both* prose surfaces (spec + all six siblings) are fully frozen and the *only* live surface is the Rust mirror — and every mirror move was already caught by whichever rotation delta reached it first (`society.rs` at C174; #538/#544 at C248/C246). The audit's substantive output is not a finding but a **carry resolution**: C212-I1's in-flight predicate (#538) merged, aligning the SDK with a documented ISP requirement. This is exactly the steady state the book-once guard is designed to produce — mirror growth booked once, then carried, and here *closed* when it lands.

---

## §A: Prior-Finding Verification Block

ISP `git diff 0405f331 HEAD` = **empty** (byte-identical; `git log` on the file shows `0405f331` as HEAD-for-this-file, 0 commits since C63). On a byte-frozen target the C63 remediations are held *by construction* — nothing was written that could regress. Each is re-confirmed present at its current line (verified against the C212 §A table, itself byte-verified against the token-verified C136 snapshot):

| C62 ID | Sev | C63 fix | Current line | Status |
|--------|-----|---------|--------------|--------|
| **B4** | MED | §2.2 step 4 `SHALL`→`MAY` | L108 | **HELD (byte-freeze)** |
| **B5** | MED | §4.5 "mint ADP and charge it to ATP" + cite §2.1–§2.2 | L239 | **HELD** |
| **B3** | LOW | §8/§9 §7.7 architecture-Normative phrasing | L368/377 | **HELD** |
| **B6** | LOW | §2.1 ≥3-witness placement | L75 | **HELD** |
| **B7** | LOW | §4.6 schema path fix | L252 | **HELD** |
| **B8** | LOW | §8 `web4:memberOf` cite §3.3/§3.5 | L362 | **HELD** |
| **B9** | LOW | §2.2 SOCIETY_SPEC §4.2.1 formation-event cross-ref | L115 | **HELD** |
| **B14** | LOW | §1.3 demote Eurozone analogy to last | L45 | **HELD** |
| **B16** | LOW | §8 society-roles bidirectional dependency | L369 | **HELD** |
| **B2-interim** | (½ B2) | §3.2 forward-pointer to mcp §7.7.1 | L150 | **HELD** |

**10/10 HELD, 0 regressed. `&#` artifact sweep on ISP: CLEAN (0 hits: `&#|&amp;|&lt;|&gt;`).**

### A.2 — Regression / provenance sweep
No remediation touched ISP since C63. No sister-file edit introduced an ISP change (ISP was not in the diff of any sibling since C212 — indeed no sibling moved since C212). Nothing to regress.

### A.3 — Carry re-verification (bidirectional)
| ID | Status at C250 | Evidence |
|----|----------------|----------|
| C25-H1 (7-role drift) | **RESOLVED downstream (C51), re-confirmed** | §8 SAL/society-roles rows attribute roles correctly; the #523 Effector addition (frozen since C212) does not disturb the Diplomat/Witness/Auditor attributions ISP relies on. |
| C6-L2 (Gesellian framing) | **deferred-carry persists (expected)** | ISP §4.1 L197 informational; technically accurate. |

---

## §B: Corpus-Delta Surface (frozen spec → siblings) — FIRST ISP DELTA WITH ZERO MOVERS

Of ISP's six cited siblings, **none moved** since the C212 snapshot (2026-07-17). Last-commit dates (all before the C212 snapshot, hence already adjudicated there):

| Sibling | Last commit | vs C212 snapshot | C212 verdict (stands verbatim) |
|---------|-------------|------------------|-------------------------------|
| atp-adp-cycle | `256ab51d` 2026-07-07 | frozen | DISJOINT (C151 §2.4 re-scope, C174-adjudicated) — B5/B10/B11 stand |
| mcp-protocol | `3e765345` 2026-07-13 | frozen | DISJOINT (§7.8 async mailbox after §7.7) |
| SAL | `1354e4c2` 2026-07-14 | frozen | DISJOINT (§5.6 Effector after ISP-cited §2/§3.x) — B13 stands |
| SOCIETY_SPEC | `87377c38` 2026-07-14 | frozen | DISJOINT (§7.3 ~450 lines after ISP anchors) — B9 stands |
| society-roles | `1354e4c2` 2026-07-14 | frozen | DISJOINT (Effector row; ISP/Diplomat row byte-unchanged) — B16 stands |
| LCT | `d89595e8` 2026-07-16 | frozen | DISJOINT (§1.2 insert; ISP cites LCT non-numerically; §1.2 *reinforces* ISP §6.3) |

**§B verdict: 0 net-new.** No cited surface moved; every prior cited-hunk adjudication holds by freeze. Nothing to re-litigate; nothing to refute (no new candidate arose). This is the first ISP delta since the rotation began where the entire doc-sibling surface is quiescent — the corpus around ISP has stabilized (the last mover, LCT §1.2, was 6 days before C212 and is already the fourth-consecutive doc-clean input).

---

## §B′: SDK-Mirror Expansion (the C172/C174 guard applied to ISP)

**Rationale.** web4-core (Rust) lands HUB-concord canonical schemas the draft spec lags; the guard requires re-deriving ISP's primitive-implementers at live HEAD every delta and deciding direction per-finding.

| ISP primitive | Rust web4-core site | Movement since C212 | C250 disposition |
|---|---|---|---|
| §2.1 genesis / §2.2 federation / §5.1 secession / §6 minimum-viable | `society.rs` (`bootstrap`/`add_constituent`/`join_federation`/`secede`/`validate_minimum_viable`); `role.rs` | **FROZEN `fe96aad0` (2026-07-09, pre-C174)** | **C174-N1/N2 HELD by construction** |
| §2.2 step 4 / §5.1 step 4 — citizenship recorded on the LCT | `Lct.citizenships: Vec<attestation::BirthCertificateRef>` (`lct.rs:164`); `attestation::BirthCertificateRef` (`attestation.rs:218`) | **MOVED `0e997079` #538 (2026-07-17)** | **already booked C248-N1; RESOLVES C212-I1 (see B′.2)** |
| (none — ISP cites no ratchet/authority-level) | `Lct.authority_ratchet: Option<ratchet::RatchetRequirement>` (`lct.rs:180`) | **MOVED `2ec6ae09` #544 (2026-07-18)** | **DISJOINT from ISP; booked C248-N2 / C246-N1 (see B′.3)** |

### B′.1 — society.rs / role.rs: held by construction
Neither has moved since `fe96aad0` (2026-07-09), which **predates the C174 snapshot (2026-07-11)**. C174 adjudicated them at exactly this blob. Therefore:
- **C174-N1 (LOW, widens C62-B12):** `validate_minimum_viable()` structurally approximates ISP §6.2's *semantic* requirements — **STANDS verbatim**, two-language bundle with `role.py:354`.
- **C174-N2 (INFO):** `secede()`/`join_federation()`/`add_constituent()` reduce ISP §5.1/§2.2 protocols to struct-field mutations — **STANDS verbatim**, category-appropriate primitives.

Nothing changed → do NOT re-open either as net-new.

### B′.2 — #538 plural `citizenships`: RESOLVES C212-I1 (in-flight → landed & aligned)

C212-I1 (INFO) recorded that the then-singular `lct.rs::birth_certificate: Option<BirthCertificate>` (#527) **under-represented** ISP's multi-society citizenship model — ISP §2.2 (a constituent society records citizenship in D *while remaining its own sovereign society*) and ISP §9's open item ("**Cross-federation citizenship conflicts** — when entity X is citizen of A (constituent of D) and B (constituent of E)"). C212-I1 noted dp's then-open PR #538 would reshape this to plural and recorded ISP §9/§2.2 as the *spec-side justification* for that plurality, explicitly deferring: *"Do NOT touch #538 or #527."*

**#538 has landed** (`0e997079`, 2026-07-17). Live HEAD confirms:
- `Lct.citizenships: Vec<crate::attestation::BirthCertificateRef>` (`lct.rs:164`), doc-commented "canon §2.3 `birth_certificate`, reshaped per dp 2026-07-16."
- `attestation::BirthCertificateRef` (`attestation.rs:218`) — "one … per society it is a citizen of (**plurality** — see `crate::Lct::citizenships`)"; a tamper-evident **ledger reference** (society id + ledger entry), not an embedded certificate.
- `verify_citizenship()` / `add_citizenship` operate on the vector; "A Regular LCT (no citizenships)" is the empty-vector case (`lct.rs:444/456`).

**Adjudication (ISP lens, refute-by-default):** the plural vector **realizes** the exact model ISP §2.2/§5.1/§9 describes — an entity holding citizenship in *multiple* societies simultaneously, each recorded as a distinct reference. The under-representation C212-I1 flagged is **gone**; the SDK and ISP now agree. There is **no ISP defect** here and **no net-new** (the reshape itself was booked by C248-N1 as the LCT §2.3-side spec-lag; the ISP-side interest was solely the multi-citizenship correspondence, which is now satisfied). **C212-I1 status → RESOLVED.** The residual is a pure cross-reference for the record: ISP §9 remains the spec anchor for *why* citizenship is plural, and ISP §9's cross-federation-*conflict* question (which society's law governs when A and B oppose) is a policy/governance item the data-model plurality **enables** but does not itself answer — that half stays an ISP §9 open design item, unchanged.

### B′.3 — #544 `authority_ratchet`: DISJOINT from ISP's cited surface

`lct.rs:180` gained `authority_ratchet: Option<crate::ratchet::RatchetRequirement>` (#544, "the sovereign-authority requirement … provable on the LCT"). **Refute-by-default (is this an ISP surface?):**
- ISP references **no** ratchet, authority-level, or assurance-level construct anywhere — verified `grep -ni "ratchet|authority.level|assurance.level"` over the full ISP = **0 hits**. ISP's inter-society primitives are federation genesis/secession, exchange transactions, and the Diplomat/Witness role dependencies; the sovereign-authority *ratchet level* of an individual LCT is orthogonal to those.
- The ratchet is the **LCT-structure** primitive (should LCT §2.2 enumerate the field?) and the **SAL** primitive (should SAL §5.2/§4.2 NAME the society-ratchet mechanism?). Both faces are already booked: **C248-N2** (LCT-structure face) and **C246-N1** (SAL face). Per book-once, ISP does not re-discover it.

**Verdict: DISJOINT; not an ISP finding; already booked on its two owning faces.** ISP is not a third face of the ratchet question.

**§B′ verdict: 0 net-new.** `society.rs`/`role.rs` held by construction; #538 already-booked (C248-N1) and **resolves C212-I1** on the ISP side; #544 DISJOINT and already-booked (C248-N2 / C246-N1).

---

## §C: Standing Carries (status after C250)

| ID | Class | Status |
|----|-------|--------|
| C62-B1 | design-Q (mcp `established`/`federated` enum undefined in ISP §3) | **OPEN, load-bearing** — operator/cross-track |
| C62-B2-full | design-Q (§3.2/§4.4 abstract-rate reframe) | **OPEN** — operator |
| C62-B10 | design-Q (charge-on-pledge vs value-proof) | **OPEN, TWO-SIDED** — operator; atp-adp frozen → unchanged |
| C62-B11 | design-Q / cross-track (currency vs unit-of-account) | **OPEN** — atp-adp owner + operator; atp-adp frozen → unchanged |
| C62-B15 | design-Q (settlement policy could block exit) | **OPEN** — operator |
| C62-B12 | cross-track SDK (`validate_minimum_viable` structural approx.) | **OPEN — two-language bundle (`role.py:354` + `society.rs`); society.rs frozen → verbatim** |
| C62-B13 | cross-track SAL (§2.2 birthcert example <3 witnesses) | **OPEN, live — SAL §2.2 frozen since C212** — folds to C58-B1 SAL bundle |
| C174-N1 | cross-track SDK (Rust `society.rs` = published site of C62-B12) | **HELD by construction (society.rs frozen); bundle with C62-B12** |
| C174-N2 | observation (Rust `society.rs` protocol primitives vs §5.1/§2.2) | **HELD by construction; INFO, no action** |
| **C212-I1** | cross-reference (lct.rs singular `birth_certificate` vs ISP §9 multi-citizenship; #538 in flight) | **RESOLVED — #538 landed (`0e997079`); SDK plural `citizenships` realizes ISP §2.2/§5.1/§9 multi-citizenship; ISP-side interest satisfied. The cross-federation-*conflict* half of ISP §9 remains an open policy design-item (unchanged).** |
| C6-L2 | deferred-carry (Gesellian framing) | persists, informational |

None gate a normal AUDIT turn. **No spec-side carry changed status since C136** (four consecutive doc-clean deltas: C136 → C174 → C212 → C250). The only carry motion this delta is C212-I1 **closing** (SDK-mirror side). Surface the design-Q set (B1, B2-full, B10, B11, B15) as ONE decision memo when the operator is available.

---

## Cross-Cutting Observations

1. **Book-once reached its terminal state: a carry *closing* when its predicate lands.** C174 opened two findings from the then-new `society.rs` mirror; C212 opened C212-I1 as INFO corroborating in-flight #538; C250 *closes* C212-I1 because #538 merged. Mirror growth is booked once by the first rotation delta that reaches it, carried across downstream deltas that also cite the surface, and closed when the in-flight predicate lands — without any downstream delta re-discovering it as net-new. C250 re-discovering #538 or #544 here would have been the prose-is-not-ledger failure mode, inverted.

2. **A frozen spec resolved a cross-track carry without changing a byte.** ISP is byte-frozen 36 days, yet the ISP-side of C212-I1 resolved this fire — not by an ISP edit but by the SDK landing the reshape ISP §9 justified. A delta audit's output is not only findings; it is the spec↔SDK correspondence bookkeeping that lets a carry close cleanly on the correct side.

3. **The full doc-sibling surface is quiescent for the first time.** No cited sibling moved since C212. The W4IP Effector burst (#523, four docs) and the LCT §1.2 insert (#531) have both settled; ISP was invisible to both by design (Effector is a response-side role ISP does not cite; ISP cites LCT non-numerically). The corpus around ISP has stabilized — the only remaining live edge is the Rust mirror, and that is caught by the rotation's book-once discipline.

4. **`authority_ratchet` is correctly a two-face primitive, not three.** #544 has an LCT-structure face (C248-N2) and a SAL face (C246-N1); ISP is not a third face because ISP cites no ratchet/authority-level construct (grep = 0). Resisting the pull to manufacture an ISP angle for a corpus-wide new field is the same discipline as cited-hunk-granularity §B adjudication.

---

## §D: Lessons → Memory

1. **A book-once carry has a terminal state: it *closes* when its in-flight predicate lands.** C212-I1 tracked in-flight #538; C250 closes it because #538 merged — on the SDK-mirror side, with no spec edit. When a downstream delta reaches a surface a prior delta parked as "in-flight," check whether the predicate landed and *close the carry* rather than re-opening the surface as net-new. (Extends [[feedback_prose_is_not_ledger]] and the C176 already-parked check with a *resolution* arm.)
2. **A corpus-wide new field is not automatically a finding on every doc that could plausibly relate.** `authority_ratchet` (#544) touches LCT-structure and SAL; ISP is not a third face because ISP cites no ratchet (grep = 0). Test "does the target actually cite this construct?" before manufacturing an angle — the same cited-hunk discipline that keeps §B honest.
3. **When both prose surfaces (spec + all siblings) are frozen, the audit's whole live surface is the SDK mirror — and its value may be a carry *closure*, not a finding.** A 6th-delta on a 36-day-frozen spec is not padding when a standing cross-track carry resolves on it; the honest output is "0 net-new, one carry closed," not a manufactured finding to justify the fire.

---

## Remediation Routing (for C251)

**C251 ISP remediation slot = NO-OP on the spec** (frozen target; 0 spec-side autonomous-actionable findings; 0 net-new defects). Non-spec outcomes route off-target:
- **Carry RESOLVED (no action):** C212-I1 — #538 landed; SDK plural `citizenships` realizes ISP §2.2/§5.1/§9. Record as closed. The cross-federation-*conflict* half of ISP §9 stays an open policy design-item.
- **SDK track (bundled, HELD):** C62-B12 + C174-N1 — docstring note on `validate_minimum_viable` at `role.py:354` AND `society.rs` that it checks structural proxies, not ISP §6.2 semantic requirements (which §6.3 disclaims from enforcement). Carry-only; society.rs frozen so unchanged.
- **Not an ISP surface (booked elsewhere):** #544 `authority_ratchet` → LCT-structure face **C248-N2**, SAL face **C246-N1**. Do NOT open an ISP face. Do NOT touch #538/#544/#527 (operator/merged Rust).
- **Operator design-Q memo:** B1, B2-full, B10 (two-sided), B11 (atp-adp owner), B15.
- **SAL bundle (C58-B1):** B13 (§2.2 birthcert example <3 witnesses).
- **Carried, no action:** C174-N2 (INFO), C6-L2 (Gesellian framing).

Per the no-op→advance rotation, C251 advances +2 to the next rotation file: **entity-types** (`entity-types.md`; last audited C214). **Guard for that fire:** entity-types was a #523 Effector mover (§4.8 Effector entity-type row) — regression-check the Effector registration per [[feedback_remediation_introduced_regression]]; apply the SDK-mirror expansion to `web4-core/src/*.rs` (`role.rs`, `lct.rs`, `did.rs`) for entity-type primitives, not just Python `entity.py`; and note #544's `authority_ratchet` / `ratchet::RatchetRequirement` is a NEW web4-core type — check whether entity-types should register a ratchet-bearing entity face (likely DISJOINT, but re-derive at live HEAD).

---

**Audit date**: 2026-07-22
**Source spec date**: 2026-06-16 (header L4; byte-frozen 36 days, unchanged since the C174/C212 snapshots)
**Auditor**: Legion autonomous session, slot `web4-20260722-120002`, LEAD voice
**Method note**: frozen-spec 6th-delta; §A held-by-construction + `&#` sweep (10/10 held, 0 artifacts); §B corpus-delta over 6 cited siblings — **first ISP delta with ZERO movers** (all frozen since C212 → prior DISJOINT adjudications stand verbatim); **§B′ SDK-mirror: `society.rs`/`role.rs` frozen pre-C174 → C174-N1/N2 held by construction; two Rust movers since C212 (#538 plural citizenships, #544 authority_ratchet) both already booked by C248 → book-once; #538 landing RESOLVES C212-I1 on the ISP side (SDK now realizes ISP §2.2/§5.1/§9 multi-citizenship); #544 ratchet DISJOINT (ISP cites no ratchet, grep=0), booked on its LCT/SAL faces (C248-N2/C246-N1)**. Zero spec/SDK mutation. First ISP delta whose entire prose surface is frozen and whose sole substantive output is a cross-track carry *resolution*. Not padded.
