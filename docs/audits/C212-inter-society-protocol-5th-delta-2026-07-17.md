# C212: `inter-society-protocol.md` (ISP) 5th-delta RE-Audit

**Date**: 2026-07-17
**Track**: web4 (Legion autonomous session, slot `web4-20260717-180036`)
**Instrument**: C-series delta RE-audit; **5th delta** on `inter-society-protocol.md` (lineage C6 → C25 → **C62** → remediation **C63** (#341) → C102 → C136 → **C174** → **C212**)
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2 DRAFT, 384 lines, last edited `0405f331` PR #341, 2026-06-16 — **BYTE-FROZEN 31 days**; `git diff 0405f331 HEAD` = empty; unchanged since the C174 snapshot 2026-07-11)
**Method**: §A prior-finding verification (held-by-construction on a byte-frozen target) + `&#` artifact sweep + bidirectional carry re-verification. §B **frozen-target corpus-delta surface** over ISP's 6 cited sibling docs since the C174 snapshot, adjudicated at **cited-hunk granularity** with adversarial refute-by-default. §B′ **SDK-MIRROR EXPANSION** per the standing C172/C174 method guard: re-derive ISP's primitive-implementers at live HEAD across the Python SDK AND Rust `web4-core`, checking (a) whether the previously-adjudicated `society.rs` mirror moved, and (b) whether net-new web4-core growth since C174 introduces an ISP-relevant mirror surface.

**Slot note (rotation):** this fire is the **C212 slot**, advanced +2 from C210 (LCT 5th-delta, PR #537 pending). C211 was correctly declared a NO-OP on the LCT spec side (C210 produced 0 autonomous spec mutations; its sole finding C210-N1 routed to the C172-N1 reconciliation bundle, not self-applied) → no remediation turn manufactured; rotation advanced LCT → **ISP**.

**Cross-referenced (read live at audit-write)**:
- `web4-standard/core-spec/atp-adp-cycle.md` (frozen since `256ab51d` 2026-07-07 — the C151 §2.4 change C174 already adjudicated DISJOINT) — bears on B5/B10/B11
- `web4-standard/core-spec/mcp-protocol.md` (**MOVED** `3e765345` 2026-07-13 — §7.8 async mailbox) — bears on B1/B2/B3 + §8 row
- `web4-standard/core-spec/web4-society-authority-law.md` (SAL) (**MOVED** `1354e4c2` 2026-07-14 — §5.6 Effector + §7.1.1) — bears on B13 + §2.1/§5.1/§8 cross-refs
- `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (**MOVED** `87377c38` 2026-07-14 — §7.3 Correction & Enforcement) — bears on B9 + §2/§6/§7 cross-refs
- `web4-standard/core-spec/society-roles.md` (**MOVED** `1354e4c2` 2026-07-14 — Effector role) — bears on B12/B16 + §2.2/§8 Diplomat dependency
- `web4-standard/core-spec/LCT-linked-context-token.md` (**MOVED** `d89595e8` 2026-07-16 — §1.2 "Inspectable Evidence" insert + §1.2→§1.3 renumber, #531) — bears on §2.1/§8 witness-quorum cross-refs
- **`web4-core/src/society.rs`** (Rust; **FROZEN since `fe96aad0` 2026-07-09**, pre-C174 snapshot) — the ISP §2/§5/§6 mirror first adjudicated at C174
- **`web4-core/src/lct.rs`** (Rust; **MOVED `e8f313e4` 2026-07-15**, #527 birth-certificate/attestation schema) — NEW web4-core growth since C174; the citizenship-on-LCT surface ISP §2.2/§5.1/§9 describes
- `web4-standard/implementation/sdk/web4/{federation,role}.py` (frozen) — Python inter-society mirrors

**Prior audits**: C6 (13 → #215), C25 (6 NEW → #258), **C62** (16 distinct → remediation #341: 9 autonomous + B2-interim), C102 (0 net-new — first clean), C136 (0 net-new — 2nd consecutive clean), **C174** (0 doc-net-new; +2 from the then-new `society.rs` SDK mirror: N1 LOW, N2 INFO).

---

## Summary

| Severity | NEW (C212) |
|----------|-----------:|
| HIGH     | 0 |
| MEDIUM   | 0 |
| LOW      | 0 |
| INFO     | 1 (cross-reference observation; no action) |
| **Total NEW distinct defects** | **0** |

**Result**: **FROZEN-SPEC CLEAN + SDK-MIRROR HELD/ALREADY-PARKED → 0 net-new.** The ISP *spec* is byte-identical to its C63 remediation (`0405f331`, 31 days) and unchanged since the C174 snapshot. All 10 C63 remediations HELD by byte-freeze; 0 regressions; 0 `&#` artifacts. §B: **five of six** cited siblings moved since C174 (only atp-adp frozen), but every moved hunk is **DISJOINT** from ISP's cited surface at cited-hunk granularity, verified anchor-by-anchor — including the largest mover, the W4IP **Effector** role (#523), which is a *response-side* role ISP does not cite. **→ 0 net-new from the doc-sibling surface — ISP's 3rd consecutive doc-clean delta (C136 → C174 → C212).**

**§B′ SDK-mirror is the first ISP delta to yield nothing net-new from the mirror surface, for two distinct reasons:**
- `society.rs` (the ISP §2/§5/§6 mirror) is **byte-frozen since `fe96aad0` (2026-07-09), predating the C174 snapshot** → C174-N1 (LOW, widens C62-B12) and C174-N2 (INFO) are **HELD by construction**; nothing changed to regress or extend.
- The one net-new web4-core growth since C174 — `lct.rs`'s `birth_certificate` citizenship field (#527, 2026-07-15) — is the SDK mirror of ISP §2.2/§5.1's "citizenship recorded on the LCT," **but it was already parked at C210** (this cycle's LCT delta, 5 days ago, as "the live mirror growth edge, Phase-2 deferred with watch"). Per the C176 / [[feedback_prose_is_not_ledger]] guard, a mirror surface a sibling delta already logged is **not re-discovered as net-new here**. Refute-by-default confirms it is not an ISP defect (see C212-I1).

**Headline (method):** the SDK-mirror set that grew *two* findings at C174 yields *zero* at C212 — not because the audit narrowed, but because the mirror was correctly tracked. `society.rs` was adjudicated once (C174) and hasn't moved; the new `lct.rs` citizenship growth was caught by the *sibling* LCT delta (C210) before ISP's turn. This is what the guard is supposed to produce: mirror growth caught exactly once, by whichever rotation delta reaches it first, then carried — not re-litigated at every downstream delta that also cites it.

---

## §A: Prior-Finding Verification Block

ISP `git diff 0405f331 HEAD` = **empty** (byte-identical; `git log` on the file shows `0405f331` as HEAD-for-this-file, 0 commits since C174). On a byte-frozen target the C63 remediations are held *by construction* — nothing was written that could regress. Each is re-confirmed present at its current line (verified against the C174 §A table, which held all 10 by byte-freeze against the token-verified C136 snapshot):

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
No remediation touched ISP since C63. No sister-file edit introduced an ISP change (ISP was not in the diff of any of the five moved siblings). Nothing to regress.

### A.3 — Carry re-verification (bidirectional)
| ID | Status at C212 | Evidence |
|----|----------------|----------|
| C25-H1 (7-role drift) | **RESOLVED downstream (C51), re-confirmed** | §8 SAL/society-roles rows attribute roles correctly; the #523 Effector addition (a *new* role) does not disturb the existing Diplomat/Witness/Auditor attributions ISP relies on. |
| C6-L2 (Gesellian framing) | **deferred-carry persists (expected)** | ISP §4.1 L197 informational ("Demurrage … is expiration of resource allocations, not a Gesellian economic experiment"), technically accurate. |

---

## §B: Corpus-Delta Surface (frozen spec → moved siblings)

Of ISP's six cited siblings, **five moved** since the C174 snapshot (2026-07-11): mcp, SAL, SOCIETY_SPEC, society-roles, LCT. Only **atp-adp** is frozen (its last change `256ab51d` 2026-07-07 is the C151 §2.4 conservation re-scope C174 already adjudicated DISJOINT — so C62-B5/B10/B11 stand verbatim from C174). Each mover is tested against ISP's **actual cited anchors**, not the whole sibling.

### B.1 — SOCIETY_SPECIFICATION #522 (`87377c38`, §7.3 Correction & Enforcement): DISJOINT
**ISP cites**: §1.2 (min structural requirements, L56/L318), §4.2.1 (formation events, L115 → B9), §4 (Ledger Types, L346), §3.2.2 (indirect relationship, L380).
**Mover**: a single hunk at `@@ -471,11 +471,28 @@` — the §7.3 secession/enforcement region, **~450 lines after** every ISP-cited anchor. Live re-resolution confirms all ISP anchors intact: §1.2 (L19), §3.2.2 (L180), §4 (L208). C62-**B9** (§4.2.1 formation-event cross-ref) untouched → stands verbatim. **DISJOINT.**

### B.2 — SAL #523 (`1354e4c2`, §5.6 Effector + §7.1.1): DISJOINT
**ISP cites**: SAL §2 (genesis Citizen role, L85/L362), §2.2 (Birth Certificate JSON-LD, L85 → B13), §3.1 (Society Topology), §3.3 (`web4:memberOf`), §3.4 (Immutable Record, L281/L362), §3.5 (chained membership).
**Mover**: new `### 5.6 Effector` (L233) + `### 7.1.1` heading gains "Effector" (+2 triples). Both in §5/§7 — **after** every ISP-cited SAL section (§2/§3.x). Live anchors resolve: §2 (L36), §2.2 (L44), §3.1 (L70), §3.3 (L84), §3.4 (L107), §3.5 (L125). C62-**B13** (§2.2 birthcert example <3 witnesses) untouched → stands, folds to the C58-B1 SAL bundle. **DISJOINT.**

### B.3 — society-roles #523 (`1354e4c2`, Effector role): DISJOINT
**ISP cites**: the Diplomat role (§2.2 federation genesis, L93) and the §8 **bidirectional dependency** (L369).
**Mover**: new `#### Effector` (L231, in the "commonly defined when needed" illustrative list) + one modified line in the spec-relationship table — the **SAL row** gains "Effector" to its role list ("Citizen, Authority, Law Oracle, Witness, Auditor, **and Effector**"). The `inter-society-protocol.md` row (which describes ISP's Diplomat §2.2 / §6.2 / §4.6 dependency) is **byte-unchanged**. The Diplomat role is not touched or renumbered. **DISJOINT.** *(Reverse-direction confirmation: society-roles' ISP row still cites ISP §2.2/§6.2/§4.6 — all resolve in the frozen ISP.)*

### B.4 — mcp-protocol #7.8 (`3e765345`, Asynchronous Mailbox): DISJOINT
**ISP cites**: mcp §7.3–§7.6 (R6/R7 actions, L368/L375), §7.7 + §7.7.1/§7.7.4 (referent-grounded rate, architecture Normative — L150/L368/L377), §1.1/§7.5 (§9 resolved items).
**Mover**: new `### 7.8 The Asynchronous Mailbox` (L708) + §7.8.1–§7.8.3, **after** §7.7 (§7.7.1 L544, §7.7.4 L660). No renumber of §7.3–§7.7 — all resolve live. **DISJOINT.** *Refute:* does accept-and-defer messaging change the inter-society transactional semantics ISP §3.2 Option 1 relies on ("Exchange transactions SHALL be witnessed by both societies and anchored in both ledgers")? **No** — §7.8 is a message-queue conformance capability (entity-edge P1c) orthogonal to witnessing/anchoring; ISP defers the *action* protocol to mcp §7.3–§7.6 and makes no wire-transport claim §7.8 could contradict.

### B.5 — LCT #531 (`d89595e8`, §1.2 "Inspectable Evidence" insert + §1.2→§1.3 renumber): DISJOINT
**ISP cites LCT only non-numerically**: "≥3 birth witnesses per `LCT-linked-context-token.md`" (L75/L83), "society LCTs as defined there" (L360), "Companion to" (L7). **No numbered LCT section is cited** → the §1.2→§1.3 renumber orphans **nothing** in ISP. **DISJOINT.**
*Refute (per [[feedback_refute_your_best_finding]] — the same LCT-§1.2 candidate the C204/C206 deltas evaluated against their targets):* does the new LCT §1.2 principle ("a surface's job is to make evidence inspectable, not encode a universal trust threshold") contradict any ISP claim? **No — it *reinforces* ISP §6.3.** ISP §6.3 already states the §6.2 minimum-viable-semantic criteria are "**GUIDANCE, not protocol enforcement** … The Web4 protocol does not adjudicate whether a society is 'real enough' … Other societies will form their own judgments via the first-contact protocol." That is precisely LCT §1.2's "produce inspectable evidence, let the relying party decide." The two are the same anti-prescribed-trust stance at different scopes; no contradiction, no net-new.

**§B verdict: 0 net-new. Every moved hunk is disjoint from ISP's cited surface; the largest mover (Effector) is a response-side role ISP does not cite; the LCT §1.2 principle reinforces ISP §6.3 rather than contradicting it.**

---

## §B′: SDK-Mirror Expansion (the C172/C174 method guard applied to ISP)

**Rationale.** C172 established that web4-core (Rust) lands HUB-concord canonical schemas the draft spec lags; C174 first adjudicated `society.rs` against ISP and found N1/N2 there. The guard requires re-deriving ISP's primitive-implementers at live HEAD every delta.

| ISP primitive | Rust web4-core site | Movement since C174 | C212 disposition |
|---|---|---|---|
| §2.1 genesis / §2.2 federation / §5.1 secession / §6 minimum-viable | `society.rs` (`bootstrap`/`add_constituent`/`join_federation`/`secede`/`validate_minimum_viable`) | **FROZEN `fe96aad0` (2026-07-09, pre-C174)** | **C174-N1/N2 HELD by construction** |
| §2.2 step 4 / §5.1 step 4 — citizenship recorded on the LCT | `lct.rs::birth_certificate: Option<BirthCertificate>` (L155–159) | **MOVED `e8f313e4` (2026-07-15, #527)** | **already-parked at C210 → not net-new (see C212-I1)** |

### society.rs — held by construction
`society.rs` has not moved since `fe96aad0` (2026-07-09), which **predates the C174 snapshot (2026-07-11)**. C174 adjudicated it at exactly this blob. Therefore:
- **C174-N1 (LOW, widens C62-B12):** `validate_minimum_viable()` structurally approximates ISP §6.2's *semantic* requirements — **STANDS verbatim**, still a two-language bundle with the Python `role.py` site (`role.py:354` parity anchor).
- **C174-N2 (INFO):** `secede()`/`join_federation()`/`add_constituent()` reduce ISP §5.1/§2.2 protocols to struct-field mutations — **STANDS verbatim**, category-appropriate data-model primitives.

Nothing changed → nothing to regress or extend. Do NOT re-open either as net-new.

### C212-I1 (INFO, cross-reference observation — NOT a defect, no action)

`lct.rs` gained (`#527`, post-C174) `birth_certificate: Option<crate::attestation::BirthCertificate>` — "present iff a society conferred citizenship on this entity; `None` = a Regular self-issued LCT" (L155–159), with `verify_birth_certificate()` fail-closed quorum checks (L394+). This is the SDK mirror of the citizenship recorded on an LCT that ISP §2.2 step 4 ("A, B, … **MAY** update their own LCTs to record citizenship in D") and ISP §5.1 step 4 ("Updates A's society LCT to remove citizenship in D") describe.

**Already-parked (C176 / [[feedback_prose_is_not_ledger]] guard):** this exact surface was logged by **C210** (this cycle's LCT 5th-delta, 5 days prior) as "the live mirror growth edge (#527), Phase-2 deferred with watch," and the standing memory guard is explicit: *do NOT re-discover #527 as net-new.* A mirror a sibling delta already booked is not re-booked here.

**Refute-by-default (is it an ISP defect?):** No.
- The `Option<>` (optional) shape is **consistent with** ISP §2.2 step 4's "**MAY** record citizenship."
- The one honest observation the *ISP lens* adds that the LCT lens need not have foregrounded: the merged schema is **singular** (`Option<BirthCertificate>` — at most one citizenship), whereas ISP models **multi-society citizenship** — §2.2 (a constituent society's LCT records citizenship in D *while remaining its own sovereign society*) and, explicitly, §9's open item "**Cross-federation citizenship conflicts — when entity X is citizen of A (constituent of D) and B (constituent of E)**." A singular field under-represents that model.
- **But this requires no action and is not net-new**, because **dp's open PR #538 (`feat/citizenship-ledger-reference`, REVIEW_REQUIRED) already reshapes exactly this** to plural `Lct.citizenships: Vec<BirthCertificateRef>` ("one cert per society the entity is a citizen of"). The ISP audit's contribution is purely corroborative: **ISP §9's cross-federation-citizenship item and §2.2's federation model are the spec-side justification for #538's plurality direction.** Recorded so the reviewer of #538 (and the next LCT/SAL delta) can cite ISP §9 as the spec anchor. **Route: cross-reference note only. Do NOT touch #538 or #527 (operator PR + already-merged schema, out of bounds).**

**§B′ verdict: 0 net-new. `society.rs` held by construction; `lct.rs` citizenship growth already-parked (C210) and already-in-flight (#538), refuted as an ISP defect and recorded as INFO corroboration only.**

---

## §C: Standing Carries (status after C212)

| ID | Class | Status |
|----|-------|--------|
| C62-B1 | design-Q (mcp `established`/`federated` enum undefined in ISP §3) | **OPEN, load-bearing** — operator/cross-track |
| C62-B2-full | design-Q (§3.2/§4.4 abstract-rate reframe) | **OPEN** — operator |
| C62-B10 | design-Q (charge-on-pledge vs value-proof) | **OPEN, TWO-SIDED** — operator; atp-adp frozen → unchanged |
| C62-B11 | design-Q / cross-track (currency vs unit-of-account) | **OPEN** — atp-adp owner + operator; atp-adp frozen → unchanged |
| C62-B15 | design-Q (settlement policy could block exit) | **OPEN** — operator |
| C62-B12 | cross-track SDK (`validate_minimum_viable` structural approx.) | **OPEN — two-language bundle (`role.py` + `society.rs:225`); society.rs frozen → verbatim** |
| C62-B13 | cross-track SAL (§2.2 birthcert example <3 witnesses) | **OPEN, live — SAL §2.2 untouched by #523** — folds to C58-B1 SAL bundle |
| C174-N1 | cross-track SDK (Rust `society.rs:225` = published site of C62-B12) | **HELD by construction (society.rs frozen); bundle with C62-B12** |
| C174-N2 | observation (Rust `society.rs` protocol primitives vs §5.1/§2.2) | **HELD by construction; INFO, no action** |
| **C212-I1** | cross-reference (lct.rs singular `birth_certificate` vs ISP §9 multi-citizenship; #538 in flight) | **NEW — INFO, no action; corroborates dp PR #538 plurality via ISP §9** |
| C6-L2 | deferred-carry (Gesellian framing) | persists, informational |

None gate a normal AUDIT turn. **No spec-side carry changed status since C136** (three consecutive doc-clean deltas). Surface the design-Q set (B1, B2-full, B10, B11, B15) as ONE decision memo when the operator is available.

---

## Cross-Cutting Observations

1. **The SDK-mirror guard produced its intended steady state.** C174 yielded 2 findings from the *then-new* `society.rs` mirror; C212 yields 0 because (a) `society.rs` was adjudicated once and hasn't moved, and (b) the new `lct.rs` citizenship growth was caught by the *sibling* LCT delta (C210) before ISP's turn. Mirror growth should be booked **once**, by whichever rotation delta reaches it first — then carried, not re-litigated at every downstream delta that also cites the surface. Re-discovering #527 here would have been a false net-new (the C176 / prose-is-not-ledger failure mode, inverted).

2. **A frozen spec can independently corroborate an in-flight SDK reshape.** ISP is byte-frozen, yet its §9 (cross-federation citizenship) and §2.2 (federation model) are the spec-side justification for the plurality direction of dp's open PR #538. The audit's value here is not a finding but a **citation the reviewer of #538 can use**: the singular→plural reshape is not just a HUB ergonomic flag, it aligns the SDK with a documented ISP multi-citizenship requirement.

3. **The W4IP Effector role (the corpus's biggest recent mover) is invisible to ISP by design.** Effector is a *response-side* enforcement role (SAL §5.6, society-roles, entity-types §4.8); ISP's inter-society primitives cite only the *Diplomat* (federation genesis) and *Witness* (ATP measurement). A large cross-cutting sibling change that touches four docs still produces zero ISP drift when it lands outside ISP's cited surface — confirming cited-hunk-granularity adjudication over whole-file diffing.

4. **Refute-by-default held both spec candidates at zero.** The LCT §1.2 "inspectable evidence" principle *reinforces* ISP §6.3 rather than contradicting it; the `lct.rs` singular-citizenship gap is real but already-parked and already-in-flight. Neither was inflated to avoid a clean result.

---

## §D: Lessons → Memory

1. **Book a mirror surface once, at the first rotation delta that reaches it; carry it thereafter.** When a downstream delta (ISP) also cites a surface a sibling delta (LCT, C210) already logged (`lct.rs` #527 citizenship), do NOT re-discover it as net-new — cross-reference the sibling's booking and, if the new lens adds a *distinct* angle (ISP §9 multi-citizenship justifying #538 plurality), record that as INFO corroboration, not a fresh finding. (Extends [[feedback_prose_is_not_ledger]] and the C176 already-parked check.)
2. **A byte-frozen SDK mirror holds its findings by construction — verify the freeze date against the prior audit's snapshot, not just "unchanged since I last looked."** `society.rs` last moved `fe96aad0` (2026-07-09), which is *before* the C174 snapshot (2026-07-11); that single date comparison is what lets C174-N1/N2 hold without re-derivation.
3. **A frozen spec is still a live citation source for in-flight SDK work.** The ISP audit couldn't change a byte, but it surfaced ISP §9 as the spec anchor a reviewer of PR #538 should cite. A delta audit's output is not only findings — it is also the spec↔SDK cross-references that let another track act with authority.

---

## Remediation Routing (for C213)

**C213 ISP remediation slot = NO-OP on the spec** (frozen target; 0 spec-side autonomous-actionable findings; 0 net-new defects). Non-spec outcomes route off-target:
- **SDK track (bundled, HELD):** C62-B12 + C174-N1 — one two-language finding (docstring note on `validate_minimum_viable` at `role.py` AND `society.rs:225` that it checks structural proxies, not ISP §6.2 semantic requirements, which §6.3 disclaims from enforcement). Carry-only; society.rs frozen so unchanged.
- **Cross-reference (INFO, no action):** C212-I1 — ISP §9 / §2.2 corroborate dp PR #538's plurality reshape of `lct.rs` citizenship; note for the #538 reviewer and the next LCT/SAL delta. Do NOT touch #538/#527.
- **Operator design-Q memo:** B1, B2-full, B10 (two-sided), B11 (atp-adp owner), B15.
- **SAL bundle (C58-B1):** B13 (§2.2 birthcert example <3 witnesses).
- **Carried, no action:** C174-N2 (INFO), C6-L2 (Gesellian framing).

Per the no-op→advance rotation, C213 advances +2 to the next rotation file: **entity-types** (`entity-types.md`). **Guard for that fire:** entity-types was itself a #523 Effector mover (new §4.8 Effector entity-type row) — regression-check the Effector registration per [[feedback_remediation_introduced_regression]]; and apply the SDK-mirror expansion to `web4-core/src/*.rs` (`role.rs`, `lct.rs`, `did.rs`) for entity-type primitives, not just Python `entity.py`.

---

**Audit date**: 2026-07-17
**Source spec date**: 2026-06-16 (header L4; byte-frozen 31 days, unchanged since the C174 snapshot)
**Auditor**: Legion autonomous session, slot `web4-20260717-180036`, LEAD voice
**Method note**: frozen-spec 5th-delta; §A held-by-construction + `&#` sweep (10/10 held, 0 artifacts); §B corpus-delta over 6 cited siblings (5 moved: SOCIETY_SPEC §7.3, SAL/society-roles Effector #523, mcp §7.8, LCT §1.2 #531 — all DISJOINT at cited-hunk granularity, anchor-by-anchor verified; LCT §1.2 adversarially refuted as reinforcing §6.3); **§B′ SDK-mirror: `society.rs` frozen pre-C174 → C174-N1/N2 held by construction; `lct.rs` #527 citizenship growth already-parked at C210 → not re-discovered, refuted as an ISP defect, recorded C212-I1 (INFO) as spec-side corroboration for dp PR #538**. Zero spec/SDK mutation. First ISP delta with both doc-sibling AND SDK-mirror surfaces yielding 0 net-new. Not padded.
