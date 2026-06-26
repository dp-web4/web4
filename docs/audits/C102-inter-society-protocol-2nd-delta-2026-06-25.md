# C102: `inter-society-protocol.md` (ISP) 2nd-delta RE-Audit

**Date**: 2026-06-25
**Track**: web4 (Legion autonomous session, slot `180010`)
**Instrument**: C-series delta RE-audit; **2nd delta** on `inter-society-protocol.md` (lineage C6 → C25 → **C62** → remediation **C63** (#341) → **C102**)
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2 DRAFT, 384 lines, last edited `0405f331` PR #341, 2026-06-16 — **FROZEN 9 days**)
**Method**: §A prior-finding token-by-token verification + #341 regression sweep (incl. `&#` artifact sweep) + bidirectional carry re-verification; §B **frozen-target corpus-delta surface** — ISP byte-identical to C63, so §B yield is the cited siblings that MOVED since C62 (mcp-protocol.md C77 #366; atp-adp-cycle.md C79 #368), checked against ISP cross-refs with the **snapshot-presence guard** (was it present/this-shape at the C62 snapshot?).

**Cross-referenced (read live at audit-write)**:
- `web4-standard/core-spec/mcp-protocol.md` (post-C77 #366 `f3d2613d`) — bears on B1, B2, B3
- `web4-standard/core-spec/atp-adp-cycle.md` (post-C79 #368 `db394dfa`) — bears on B5, B10, B11
- `web4-standard/core-spec/web4-society-authority-law.md` (SAL, frozen since C59) — bears on B13
- `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (frozen) — bears on B9
- `web4-standard/core-spec/society-roles.md` (frozen) — bears on B12, B16
- `web4-standard/implementation/sdk/web4/role.py` (frozen since C62) — bears on B12

**Prior audits**: C6 (`inter-society-protocol-internal-consistency-2026-05-21.md`, 13 findings → #215), C25 (`C25-...-2026-05-31.md`, 6 NEW → #258), **C62** (`C62-...-2026-06-16.md`, 16 distinct → remediation #341 applied 9 autonomous + B2-interim).

---

## Summary

| Severity | NEW (C102) |
|----------|-----------:|
| HIGH     | 0 |
| MEDIUM   | 0 |
| LOW      | 0 |
| INFO     | 0 |
| **Total NEW distinct** | **0** |

**Result**: **POSITIVE FROZEN-TARGET.** ISP is byte-identical to its C63 remediation (`0405f331`, 9 days). All 10 C63 remediations HELD token-by-token; 0 regressions; 0 `&#` artifacts. §B over the two moved siblings (mcp-C77, atp-adp-C79) yields **0 net-new autonomous ISP defects** — the deltas REINFORCE two resolved findings and ELEVATE one standing design-Q to two-sided. **C103 ISP remediation slot = NO-OP** (sixth consecutive frozen target after C92/C94/C96/C98/C100, all 0 autonomous).

**Headline enrichment**: **C62-B10 is now a TWO-SIDED design-Q.** The atp-adp-cycle C78→C79 cycle independently surfaced and routed "ISP-B10" to the operator from the atp-adp side (#368 commit body: *"DESIGN-Q (... ISP-B10) left for the operator"*). The charge-on-pledged-commitment-vs-value-proof tension is now recognized from BOTH the ISP side (C62-B10) and the atp-adp SSOT side, both docs frozen, both routing to the operator. Mirrors the C96 `C58-B10` double-anchor pattern ([[feedback_cross_doc_carry_inbound]]).

---

## §A: Prior-Finding Verification Block

### A.1 — C63 remediations (the 9 autonomous + B2-interim + header), verified token-by-token

ISP `git diff 0405f331 HEAD` = empty (byte-identical). Each remediation re-read against the canonical C62 fix text per the C56 completeness method:

| C62 ID | Sev | C63 fix | Current line | Status |
|--------|-----|---------|--------------|--------|
| **B4** | MED | §2.2 step 4 `SHALL`→`MAY` | L108 "A, B, [C, ...] **MAY** update their own LCTs to record citizenship in D" | **HELD** |
| **B5** | MED | §4.5 "mint ATP"→"mint ADP and charge it to ATP" + cite §2.1–§2.2; quoted-question verb "mint"→"issue" | L237 "...over-reporting compute capacity to **issue** excessive ATP?"; L239 "MAY **mint any quantity of its own ADP and charge it to ATP** under its own policy (minting creates tokens in the discharged ADP state; charging is the ADP→ATP transition — see `atp-adp-cycle.md` §2.1–§2.2)" | **HELD** |
| **B3** | LOW | §8/§9 "§7.7 (WIP)"→"architecture Normative per §7.7.1/§7.7.4; wire format WIP" | L368 (§8 mcp row) + L377 (§9) both carry the refined phrasing | **HELD** |
| **B6** | LOW | §2.1 re-place `MAY` so ≥3 reads mandatory | L75 "Birth witnesses — **≥3 required** per `LCT-linked-context-token.md`; these MAY be entities under the founder's control" | **HELD** |
| **B7** | LOW | §4.6 schema path fix | L252 "`schemas/attestation-envelope-jsonld.schema.json`" | **HELD** |
| **B8** | LOW | §8 `web4:memberOf` cite §3.1→§3.3/§3.5 (remediation-introduced) | L362 "fractal Society Topology (SAL §3.1) and `web4:memberOf` edges (SAL §3.3, chained per §3.5)" | **HELD** |
| **B9** | LOW | §2.2 add SOCIETY_SPEC §4.2.1 formation-event cross-ref | L115 "**Note on formation events**: ... `incorporate_child` / `incorporated_by` formation events per `SOCIETY_SPECIFICATION.md` §4.2.1 (symmetric to ... §5.1 ... SAL §3.4)" | **HELD** |
| **B14** | LOW | §1.3 demote Eurozone (weakest exit analogy) to last | L42-45 NATO/UN/standards-bodies first, Eurozone last with "the weakest of these analogies on the exit axis, listed last for that reason" | **HELD** |
| **B16** | LOW | §8 society-roles row make bidirectional explicit | L369 "...this spec's §6.2 semantic-viability criteria constrain how those roles must compose. **The dependency runs both ways.**" | **HELD** |
| **B2-interim** | (½ of B2) | §3.2 Option 1 forward-pointer to mcp §7.7.1 | L150 "**Note on rate substance**: the *substance* of any rate ... is referent-grounded per `mcp-protocol.md` §7.7.1 (Normative) ... The Fixed / Market-derived / Pegged enumeration above governs rate *stability over time*, not the basis of valuation." | **HELD** |
| header | — | Date 2026-06-01→2026-06-16 | L4 "**Date**: 2026-06-16" | **HELD** |

**10/10 HELD, 0 regressed.** `&#` artifact sweep on ISP: **CLEAN (0 hits)**.

### A.2 — #341 regression sweep (per-file, via git)

`git show 0405f331` touched **only** `inter-society-protocol.md` (+18/−14). No sister-file edits introduced by the remediation (per-file provenance re-checked per the standing lesson). No remediation-introduced defect this cycle — and the prior cycle's remediation-introduced mis-cite (C62-B8, born in #258) was itself fixed by #341 and HELD here.

### A.3 — C25 / C6 carry re-verification (bidirectional)

| ID | Status at C102 | Evidence |
|----|----------------|----------|
| C25-H1 (7-role drift) | **RESOLVED downstream (C51) — re-confirmed** | No ISP-side residue; the §8 SAL/society-roles rows attribute roles correctly. |
| C6-L2 (Gesellian framing) | **deferred-carry persists (expected)** | ISP L197 "...not a Gesellian economic experiment." Informational, technically accurate. |

---

## §B: Corpus-Delta Surface (frozen target → moved siblings)

ISP is frozen, so per policy §B is held to the surface that actually moved: the two cited siblings remediated since C62. Each ISP cross-ref / standing finding that touches them is re-verified with the snapshot-presence guard.

### B.1 — mcp-protocol.md moved (C77 #366): bears on C62-B1, B2, B3

C77 applied 8 autonomous C76 findings (entity_type `mcp_server`→`service` / `mcp_client`→`ai`; `witness_signatures`→`witnesses`; outcome_class definitions; added `responding_role_expected`; §9.1 `t3`→`t3_in_role`; SPARQL `web4:MCPServer`→`web4:Service`; MUST-list summary). Impact on ISP:

- **C62-B3 (RESOLVED) — cross-ref VERIFIED STABLE.** C77 explicitly **held** the §7.7-promotion design-Q cluster (commit body: *"Holds ... the §7.7-promotion design-Q cluster ... for the operator"*). The §7.7 per-subsection banner (§7.7.1/§7.7.4 Normative) that ISP §8 L368 / §9 L377 cite as "architecture Normative" is unchanged. **Snapshot guard**: the banner was present at the C62 snapshot (C62 cited §7.7.1 Normative L514, §7.7.4 Normative L517); C77 did not touch it. ISP's B3 phrasing remains accurate. *Reinforced*: C77 added an interim note at mcp §7.4 (N14) explicitly calling §7.7.1 "the stable normative design-invariant" — strengthening, not contradicting, ISP's B3/B2-interim language.
- **C62-B1 (design-Q) — STANDS.** mcp §7.4 enum L436 `first_contact | established | federated`, L462 "established and federated proceed normally", and the load-bearing normative default at §7.3 L416 (propagation_scope branches on the three values) are all **unchanged** by C77. ISP §3 still defines no `established`/`federated` relationship state. The carry is not resolved; it remains load-bearing (mcp §7.3 L416 normative SHOULD default keys on labels ISP §3 doesn't define). Route to the standing operator/cross-track memo.
- **C62-B2-full (design-Q) — STANDS.** mcp §7.7.1 ("NOT the Web4 model" / referent-grounded invariant) unchanged by C77; ISP §3.2/§4.4 abstract-rate language still un-reframed (B2-interim forward-pointer applied at C63 is the only ISP-side movement). Full reframe remains operator-owned.

**mcp-C77 → 0 net-new ISP defects.** No ISP cross-ref to mcp went stale; one (B3) re-verified accurate and lightly reinforced.

### B.2 — atp-adp-cycle.md moved (C79 #368): bears on C62-B5, B10, B11

C79 applied 5 autonomous C78 findings (§3.3 demurrage R6-scoping carve-out note; §3.1 `mint_adp` harmonized to nested-pool form; metric `charge_rate`→`charged_fraction`; §4.3 cascade role-vocabulary note; **§5 + References: added inter-society-protocol.md + mcp-protocol.md inbound pointers**). Impact on ISP:

- **C62-B5 (RESOLVED) — cross-ref REINFORCED.** C79's B5 fix harmonized `mint_adp` so minting writes `state_distribution['ADP']` (the discharged state) — operationally confirming the exact primitive ISP §4.5 now cross-cites ("minting creates tokens in the discharged ADP state; charging is the ADP→ATP transition — see §2.1–§2.2"). §2.1 "Minting (ADP Creation)" / §2.2 charging text untouched by C79. ISP's B5 cross-ref is stable and corroborated by the corpus.
- **C62-B10 (design-Q) — ELEVATED to TWO-SIDED. [enrichment headline]** The atp-adp C78→C79 cycle independently surfaced this same tension and routed it back: #368 commit body lists *"DESIGN-Q (... **ISP-B10**) left for the operator."* The anchor is live (atp-adp §4 L619 "**Charging MUST require value proof**" present and unchanged; ISP §4.3 ATP-as-Commitment "forward-looking pledge / future capacity" present). It is now recognized from BOTH sides — ISP-side (C62-B10) and the atp-adp SSOT side (C78) — both docs frozen, both routing to operator. This is the [[feedback_cross_doc_carry_inbound]] / C96-`C58-B10`-double-anchor pattern: a one-sided design-Q hardened into a two-sided one by the sibling's own interval audit. Surface as ONE operator decision (does Web4 permit charging ATP on a forward commitment, or only on proven value?).
- **C62-B11 (design-Q / cross-track) — PARTIALLY ACKNOWLEDGED, framing tension persists.** C79's B7 added a §5 "Inter-society homes" note stating cross-society rate-grounding "is being reconciled" with ISP/mcp. This is a step toward the reconciliation B11 calls for, but the rhetorical contradiction itself is untouched: atp-adp §1 L5 still calls ATP the society's "**native currency**" and §5's title is still "Inter-Society **Currency** Exchange", while ISP §4.1 still argues ATP "is a unit of account, not a medium of exchange." Cross-track owner = atp-adp + operator; no ISP-side action. **Snapshot guard**: both anchors present at C62; C79 added an acknowledgment note, did not resolve.
- **New inbound cross-ref verified accurate.** C79-B7 added to atp-adp §5/References: "`inter-society-protocol.md` (declares `Extends: atp-adp-cycle.md` for the ATP form; §4 covers unit-of-account semantics and ADP minting)." Verified: ISP header L6 declares `Extends: ... atp-adp-cycle.md (ATP form)`; ISP §4 covers unit-of-account and (post-B5) ADP minting. Accurate — no new defect.

**atp-adp-C79 → 0 net-new ISP defects.** B5 reinforced; B10 elevated (enrichment); B11 partially acknowledged; new inbound cross-ref accurate.

### B.3 — Frozen siblings (no movement → carries verbatim)

- **C62-B13 (SAL cross-track) — STANDS, live.** SAL §2.2 birth-certificate example (SAL L55) still shows exactly 2 witnesses (`["lct:web4:witness:1", "lct:web4:witness:2"]`) — below the ≥3 quorum ISP §2.1/§6.1 require, and in tension with SAL's own L64 "MUST carry witness co-signatures meeting the society's quorum policy." Defect is SAL-side; ISP's pointer is correct. Folds into the standing C58-B1 SAL birthcert operator bundle. No ISP-side action.
- **C62-B12 (SDK cross-track) — STANDS verbatim.** `role.py` `validate_minimum_viable` unchanged since C62; structural approximation of §6.2 items 1-2 (mitigated by §6.3 GUIDANCE framing) unchanged. Route to SDK track.
- **C62-B9 target stable.** SOCIETY_SPECIFICATION.md §4.2.1 (`incorporate_child`/`incorporated_by`) unchanged; ISP's new B9 cross-ref remains valid.
- **C62-B16 / B6 targets stable.** society-roles.md and LCT-linked-context-token.md unchanged since C62; the §8 bidirectional-dependency phrasing and the §2.1 ≥3-witness cross-ref remain accurate.

---

## §C: Standing Carries (status after C102)

| ID | Class | Status |
|----|-------|--------|
| C62-B1 | design-Q (mcp `established`/`federated` undefined in ISP §3) | **OPEN, load-bearing** — operator/cross-track memo |
| C62-B2-full | design-Q (§3.2/§4.4 abstract-rate reframe) | **OPEN** — operator (B2-interim applied C63) |
| C62-B10 | design-Q (charge-on-pledge vs value-proof) | **OPEN, now TWO-SIDED** — operator (both ISP & atp-adp route it) |
| C62-B11 | design-Q / cross-track (currency vs unit-of-account) | **OPEN, partially acknowledged** — atp-adp owner + operator |
| C62-B15 | design-Q (D's settlement policy could block exit, §5.1 vs §1.3) | **OPEN** — operator (no sibling movement) |
| C62-B12 | cross-track SDK (`validate_minimum_viable`) | **OPEN, verbatim** — SDK track |
| C62-B13 | cross-track SAL (§2.2 example <3 witnesses) | **OPEN, live** — folds to C58-B1 SAL bundle |
| C6-L2 | deferred-carry (Gesellian framing) | persists, informational |

None gate a normal AUDIT turn. Surface as ONE decision memo when the operator is available.

---

## Cross-Cutting Observations

1. **Sixth consecutive frozen target (C92/C94/C96/C98/C100/C102), all 0 autonomous.** The pattern is fully locked: files churn slower than audit cadence, so 2nd-delta wraps hit frozen targets. §A is verification (10/10 held, all carries stand); §B yield is **entirely** on the corpus-delta / inbound-carry surface — diff what MOVED, apply the snapshot-presence guard.
2. **The richest delta signal this cycle came from a sibling's own audit routing a carry back.** atp-adp-C79 routed "ISP-B10" to the operator, elevating C62-B10 from one-sided to two-sided. Reading the sibling's interval-audit *commit body* (not just diffing its text) is what surfaced this — exactly the [[feedback_cross_doc_carry_inbound]] discipline. The C79 text-diff alone (a §5 reconciliation note) would have read as B11-adjacent; the commit body is where the B10 double-anchor lives.
3. **Both moved siblings REINFORCED resolved ISP findings rather than re-opening any.** mcp-C77's §7.4 note hardened §7.7.1's normative status (corroborating B3/B2-interim); atp-adp-C79's `mint_adp` harmonization operationally confirmed B5's "minting creates ADP" cross-cite. A delta audit must check whether sibling movement *corroborates* a prior fix, not only whether it staled one.

---

## §D: Lessons → Memory

1. **A frozen target's §B value can live in a sibling's commit body, not its diff.** atp-adp-C79's text-diff (§5 note) maps to B11; its *commit body* ("ISP-B10 left for the operator") is what elevated B10 to two-sided. When a cited sibling has its own interval audit, read that audit's routing/commit message for carries pointed back at this file. (Reinforces [[feedback_cross_doc_carry_inbound]].)
2. **Sibling deltas corroborate as often as they stale.** Both C77 and C79 reinforced resolved ISP findings (B3, B5). The bidirectional carry re-check must look for corroboration, not only regression/hardening. (Extends the C62 bidirectional-carry lesson.)

---

## Remediation Routing (for C103)

**C103 ISP remediation slot = NO-OP.** 0 autonomous-actionable findings (sixth consecutive frozen target). All non-autonomous outcomes route off-target:

- **Operator design-Q memo**: B1 (`established`/`federated` home), B2-full (rate reframe), **B10 (now two-sided — charge-on-pledge vs value-proof)**, B11 (currency framing, atp-adp owner), B15 (settlement-policy exit protection).
- **SDK track**: B12 (`validate_minimum_viable` structural approximation note).
- **SAL bundle (C58-B1)**: B13 (§2.2 birthcert example <3 witnesses) — SAL-side fix.
- **Carried, no action**: C6-L2 (Gesellian framing).

---

**Audit date**: 2026-06-25
**Source spec date**: 2026-06-16 (header L4; frozen 9 days)
**Auditor**: Legion autonomous session, slot `180010`, LEAD voice
**Method note**: frozen-target 2nd-delta; §A token-by-token + `&#` sweep; §B corpus-delta over 2 moved siblings (mcp-C77, atp-adp-C79) with snapshot-presence guard; clean frozen result — not padded.
