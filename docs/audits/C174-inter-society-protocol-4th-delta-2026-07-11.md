# C174: `inter-society-protocol.md` (ISP) 4th-delta RE-Audit

**Date**: 2026-07-11
**Track**: web4 (Legion autonomous session, slot `000036`)
**Instrument**: C-series delta RE-audit; **4th delta** on `inter-society-protocol.md` (lineage C6 → C25 → **C62** → remediation **C63** (#341) → **C102** → **C136** → **C174**)
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2 DRAFT, 384 lines, blob `22bf6c1d`, last edited `0405f331` PR #341, 2026-06-16 — **BYTE-FROZEN 25 days**; unchanged since the C136 snapshot 2026-07-04)
**Method**: §A prior-finding token-by-token verification (held-by-construction on a byte-frozen target) + `&#` artifact sweep + bidirectional carry re-verification. §B **frozen-target corpus-delta surface** over ISP's 6 cited sibling docs since the C136 snapshot. **§B′ — SDK-MIRROR EXPANSION per the C172 standing method guard**: re-derive which files implement ISP's primitives at live HEAD across BOTH the Python SDK AND Rust `web4-core`, since every prior ISP audit (C6/C25/C62/C102/C136) tracked only the spec + Python `role.py` and was blind to the Rust mirror. Adversarial refute-by-default on the flagship.

**Slot note (rotation):** this fire is the nominal **C174 slot**, advanced +2 from C172 (LCT 4th-delta, PR #505 MERGED `f9accbeb`). C173 was correctly declared an operator-gated doc-SDK reconciliation (NOT a unilateral remediation) → no remediation turn was manufactured; rotation advanced LCT → **ISP**. (Memory's stale path `isp-identity-system-protocol` resolves to `inter-society-protocol.md`.)

**Cross-referenced (read live at audit-write)**:
- `web4-standard/core-spec/atp-adp-cycle.md` (post-C151 #477 `256ab51d`) — bears on B5, B10, B11 (only moved sibling)
- `web4-standard/core-spec/mcp-protocol.md` (frozen since C117, no movement since C136) — bears on B1, B2, B3
- `web4-standard/core-spec/{web4-society-authority-law,SOCIETY_SPECIFICATION,society-roles,LCT-linked-context-token}.md` (**all frozen since C136**) — bear on B6/B9/B12/B13/B16
- `web4-standard/implementation/sdk/web4/federation.py` (**frozen** — last touch Sprint-38 ruff format) — Python inter-society mirror
- **`web4-core/src/society.rs`** (Rust, **published in web4-core 0.3.0**, crates.io + PyPI 2026-07-09) — **NEW mirror surface, never before tracked by an ISP audit**; implements ISP §2 genesis, §2.2 federation, §5.1 secession, §6 minimum-viable
- `web4-standard/implementation/sdk/web4/role.py` (frozen; `role.py:354` declares explicit cross-language parity with the Rust `validate_minimum_viable`)

**Prior audits**: C6 (13 findings → #215), C25 (6 NEW → #258), **C62** (16 distinct → remediation #341 applied 9 autonomous + B2-interim), **C102** (2nd-delta, 0 net-new — first ISP clean delta), **C136** (3rd-delta, 0 net-new — 2nd consecutive clean).

---

## Summary

| Severity | NEW (C174) |
|----------|-----------:|
| HIGH     | 0 |
| MEDIUM   | 0 |
| LOW      | 1 |
| INFO     | 1 |
| **Total NEW distinct** | **2** (both SDK-mirror, cross-track, non-blocking) |

**Result**: **FROZEN-SPEC CLEAN + SDK-MIRROR EXPANSION YIELDS 2.** The ISP *spec* is byte-identical to its C63 remediation (`0405f331`, 25 days) and unchanged since the C136 snapshot. All 10 C63 remediations HELD by byte-freeze (nothing written → strongest hold); 0 regressions; 0 `&#` artifacts. §B over the 6 cited siblings: only atp-adp moved (C151 §2.4), and its moved hunk is **DISJOINT** from ISP's cited surface at cited-hunk granularity → **0 net-new from the doc-sibling surface**. This would have been ISP's **3rd consecutive clean delta** on the doc-only method.

**The 2 net-new come entirely from §B′ — the SDK-mirror expansion the C172 guard mandates.** `web4-core/src/society.rs` (published, 0.3.0) is a Rust mirror that implements ISP's genesis/federation/secession/minimum-viable primitives and that **no prior ISP audit ever tracked** (C6→C136 tracked only the spec + Python). Auditing it against ISP surfaces:
- **C174-N1 (LOW, cross-track SDK — WIDENS C62-B12):** Rust `validate_minimum_viable()` is a structural approximation of ISP §6.2's *semantic* minimum-viable requirements, now in a **published** SDK; `role.py:354` declares this Rust method an explicit cross-language parity target of the Python site C62-B12 already tracks.
- **C174-N2 (INFO, observation — NOT asserted as a defect):** Rust `secede()` / `join_federation()` / `add_constituent()` reduce ISP's §5.1 secession and §2.2 federation protocols to bare struct-field mutations; defensible as data-model primitives, recorded so a future SDK inter-society-protocol layer inherits the gap.

**Headline (method):** the C172 lesson reconfirms on a *second, unrelated* target. ISP was clean-and-blind for two prior deltas (C102, C136) because the audit tracked only the spec + Python; the Rust `society.rs` mirror — carrying ISP's §2/§5/§6 primitives and now **shipped** — was invisible. **The SDK-mirror set grows every cycle: web4-core is landing canonical entity schemas (lct.rs at C172, society.rs here) that the draft-era spec pseudocode lags.** Expand the mirror set at each delta or accept a clean-and-blind result.

---

## §A: Prior-Finding Verification Block

ISP `git diff 0405f331 HEAD` = **empty** (byte-identical; `git log --since=2026-07-04` on the file = 0 commits). On a byte-frozen target the C63 remediations are held *by construction* — nothing was written that could regress. Each is re-confirmed present at its current line (verified against the C136 §A table, which token-verified all 10 against the canonical C62 fix text):

| C62 ID | Sev | C63 fix | Current line | Status |
|--------|-----|---------|--------------|--------|
| **B4** | MED | §2.2 step 4 `SHALL`→`MAY` | L108 | **HELD (byte-freeze)** |
| **B5** | MED | §4.5 "mint ADP and charge it to ATP" + cite §2.1–§2.2 | L239 | **HELD** |
| **B3** | LOW | §8/§9 §7.7 architecture-Normative phrasing | L368/377 | **HELD** |
| **B6** | LOW | §2.1 ≥3-witness placement | L75 | **HELD** |
| **B7** | LOW | §4.6 schema path fix | L252 | **HELD** |
| **B8** | LOW | §8 `web4:memberOf` cite §3.3/§3.5 | L362 | **HELD** |
| **B9** | LOW | §2.2 SOCIETY_SPEC §4.2.1 formation-event cross-ref | L115 | **HELD** |
| **B14** | LOW | §1.3 demote Eurozone analogy to last | L42-45 | **HELD** |
| **B16** | LOW | §8 society-roles bidirectional dependency | L369 | **HELD** |
| **B2-interim** | (½ B2) | §3.2 forward-pointer to mcp §7.7.1 | L150 | **HELD** |

**10/10 HELD, 0 regressed. `&#` artifact sweep on ISP: CLEAN (0 hits).**

### A.2 — Regression / provenance sweep
No remediation touched ISP since C63 (`git log` on the file shows `0405f331` as HEAD-for-this-file). No sister-file edit introduced an ISP change. Nothing to regress.

### A.3 — Carry re-verification (bidirectional)
| ID | Status at C174 | Evidence |
|----|----------------|----------|
| C25-H1 (7-role drift) | **RESOLVED downstream (C51), re-confirmed** | §8 SAL/society-roles rows attribute roles correctly; no residue. |
| C6-L2 (Gesellian framing) | **deferred-carry persists (expected)** | ISP L197 informational, technically accurate. |

---

## §B: Corpus-Delta Surface (frozen spec → moved siblings)

Of ISP's six cited siblings, exactly **one** moved since the C136 snapshot (2026-07-04): **atp-adp** (C151 #477). The other five (mcp, SAL, SOCIETY_SPEC, society-roles, LCT) are frozen since C136 → their carries stand verbatim.

### B.1 — atp-adp-cycle.md moved (C151 #477 `256ab51d`): bears on C62-B5, B10, B11

C151 applied C150-N1: re-scoped the **§2.4 conservation invariant** — "conservation applies to ATP *transfers between entities*, not 'ATP→ADP transitions'." The change is confined to §2.4.

**ISP's cited surface into atp-adp** (grep `atp-adp-cycle` on ISP = L6/L30/L187/L239/L363): `Extends: … (ATP form)` (L6); form/substance framing (L30/187/363); minting/charging **§2.1–§2.2** (L239). **ISP does NOT cite atp-adp §2.4 or the conservation invariant** (grep `conservation|§2.4` on ISP = 0 hits).

- **C62-B5 (RESOLVED) — cross-ref STABLE.** atp-adp §2.1/§2.2 minting/charging (which ISP §4.5 L239 cross-cites) untouched by C151. Reinforced.
- **C62-B10 (design-Q, two-sided) — STANDS.** Anchor = atp-adp §7.1 MUST #4 "Charging MUST require value proof" + ISP §4.3 ATP-as-Commitment (frozen). Both intact; routes to operator.
- **C62-B11 (design-Q / cross-track) — STANDS.** Anchors = atp-adp §1/§5 currency framing + ISP §4.1 unit-of-account (frozen). Untouched by C151.

**Adversarial refutation (finder A):** attempted to find an ISP claim that inter-society ATP transfers are subject to the atp-adp §2.4 conservation invariant (which the re-scoping would restate) — **refuted.** ISP frames inter-society ATP as a *unit of account decoupled from* conservation-bounded intra-society flows (L191 "unit of account, not a medium of exchange"); it makes no conservation claim. The §2.4 re-scope (transfers-between-entities) is *consistent with* ISP's exchange-witnessing model (§3.2 Option 1: "Exchange transactions SHALL be witnessed by both societies and anchored in both ledgers") and stales no ISP finding. **atp-adp-C151 → 0 net-new ISP defects; changed hunk disjoint from ISP's cited surface.**

### B.2 — Frozen siblings (no movement → carries verbatim)
- **mcp (frozen since C117):** C62-B1 (`established`/`federated` enum undefined in ISP §3) and C62-B2-full (§3.2/§4.4 abstract-rate reframe) STAND, load-bearing, operator-owned. B3 cross-ref (mcp §7.7.1/§7.7.4 "architecture Normative") VERIFIED STABLE.
- **SAL (frozen):** C62-B13 (§2.2 birthcert example <3 witnesses) STANDS, live; folds to the C58-B1 SAL bundle.
- **SOCIETY_SPEC / society-roles / LCT (frozen):** C62-B9/B16/B6 cross-ref targets stable.
- **C62-B15 (design-Q):** settlement-policy-vs-exit tension; no sibling movement. Operator.

---

## §B′: SDK-Mirror Expansion (the C172 method guard applied to ISP)

**Rationale.** C172 established that a frozen spec can be clean against last cycle's mirror yet blind to a *second* implementation, and that web4-core (Rust) is landing HUB-concord canonical schemas the draft spec lags. Every prior ISP audit (C6/C25/C62/C102/C136) tracked only the spec + Python `role.py`. Re-deriving ISP's primitive-implementers at live HEAD:

| ISP primitive | Python SDK | Rust web4-core | Prior ISP-audit coverage |
|---|---|---|---|
| §2.1 solo-founder genesis | `society.py` bootstrap | `society.rs::bootstrap()` L89 | **spec + Python only** |
| §2.2 federation genesis | `federation.py` (frozen) | `society.rs::add_constituent/join_federation` L265-279 | **spec only** |
| §5.1 secession | — | `society.rs::secede()` L270 | **spec only** |
| §6 minimum-viable | `role.py::validate_minimum_viable` (C62-B12) | `society.rs::validate_minimum_viable()` L225 | **Python only (C62-B12)** |

The Rust `web4-core/src/society.rs` (406 lines, **published in web4-core 0.3.0**, crates.io + PyPI 2026-07-09) is a mirror **never before adjudicated against ISP**. Scope bounded to ISP's four primitives per the policy-review boundary condition (no SOCIETY_SPEC / SOCIETY_METABOLIC surface — e.g. the C168 `MetabolicState` carry is snapshot-guarded, NOT re-raised here).

### C174-N1 (LOW, cross-track SDK — WIDENS C62-B12 to the published Rust mirror)

`web4-core/src/society.rs::validate_minimum_viable()` (L225) is a **structural approximation** of ISP §6.2's *semantic* Minimum-Viable-Semantic-Society requirements — the **same defect class as the standing C62-B12 carry** against Python `role.py::validate_minimum_viable`, now present in a **published** SDK and declared an explicit parity target (`role.py:354`: "Cross-language parity with `web4-core/src/society.rs::validate_minimum_viable()`").

The `society.rs` module docstring (L18-21) lists ISP §6.2's three requirements verbatim as what "Minimum viable society requires":
1. *Internal differentiation (roles with meaningfully different authority)*
2. *Witnessing capacity (at least one role can independently attest)*
3. *Reified resource grounded externally (ATP represents something real)*

The method (L225-262) then checks only **structural proxies**:
- L234: `unique_fillers.len() >= 2` — distinct role-**filling entities**. ISP §6.2.1 is about *meaningfully different authority* ("a founder + three identical worker keypairs does NOT differentiate"), which distinct-entity-count cannot detect.
- L241-242: `Witness` **or** `Auditor` role **exists**. ISP §6.2.2 is *independent judgment* ("Witnessing by an identical-twin keypair does not satisfy this"), which role-presence cannot detect.
- L251: base-mandatory roles filled — a **SOCIETY_SPEC §1.2 structural** check, not an ISP §6.2 semantic one.
- Requirement **#3 (ATP grounded in an external referent)** is **not checked at all**.

**Adversarial refutation of this flagship (refute-by-default, per [[feedback_refute_your_best_finding]]):** Is the structural approach a *logic bug*? **No — and this refutes any "the validation is wrong" framing.** ISP §6.3 states the §6.2 requirements are "**GUIDANCE, not protocol enforcement**. The Web4 protocol does not adjudicate whether a society is 'real enough.'" An SDK function therefore *cannot* and *should not* enforce them. What **survives** refutation is only a **documentation/naming gap**: the docstring presents the §6.2 semantic list as what the society "requires," adjacent to a method named `validate_minimum_viable`, inviting a reader to believe the method validates that list — when it validates structural proxies for #1/#2 and omits #3. This is C62-B12 exactly, in a second (now-shipped) site.

- **Severity: LOW.** Cross-track SDK; not a spec defect (the spec is correct and self-consistent — §6.3 pre-empts enforcement).
- **Direction: SDK is the site; spec is correct.** (Contrast C172's spec-is-stale direction — here ISP §6.3 already says the right thing.)
- **Honest fix (carry-only this session, no SDK edit):** a docstring note on *both* parity sites that `validate_minimum_viable` checks the *structural* proxies for a viable society, and that ISP §6.2's *semantic* requirements are GUIDANCE (§6.3), not machine-validatable. **Route: SDK track — bundle with the existing C62-B12 `role.py` carry (they are one finding across two languages).**

### C174-N2 (INFO, observation — NOT asserted as a defect)

`web4-core/src/society.rs` reduces ISP's multi-step inter-society *protocols* to bare struct-field mutations:
- `secede()` (L270): `self.federation_parent.take()` — vs ISP §5.1's **6-step** protocol (announce intent + record reason in the Immutable Record per SAL §3.4; notice period, default 90 days; ATP settlement in D's currency; withdraw ceded sovereignty; update A's LCT to remove D-citizenship; D updates its ledger; relationships revert to first-contact §3).
- `join_federation()` (L265) / `add_constituent()` (L275): pointer set / vec push — vs ISP §2.2's federation-genesis (Diplomat delegation, charter negotiation, constituent-LCT minting, `incorporate_child`/`incorporated_by` formation events per SOCIETY_SPEC §4.2.1, witness = constituent societies).

**Adjudication (refute-by-default):** the `Society` type is a pure data model — it holds no ledger, ATP-settlement, LCT-minting, or notice-period machinery, so `secede()` *can only* mutate the struct field. Expecting a data-model setter to run the §5.1 protocol is a **category error**; this is **not a defect**. Recorded as an INFO observation because (a) there is no doc note distinguishing these primitives from the ISP protocols they are named after, and (b) no higher-layer inter-society-protocol module exists in web4-core to compose the missing steps. **Route: SDK-track note if/when web4-core grows an inter-society-protocol layer.** Do not action now.

---

## §C: Standing Carries (status after C174)

| ID | Class | Status |
|----|-------|--------|
| C62-B1 | design-Q (mcp `established`/`federated` undefined in ISP §3) | **OPEN, load-bearing** — operator/cross-track |
| C62-B2-full | design-Q (§3.2/§4.4 abstract-rate reframe) | **OPEN** — operator |
| C62-B10 | design-Q (charge-on-pledge vs value-proof) | **OPEN, TWO-SIDED** — operator |
| C62-B11 | design-Q / cross-track (currency vs unit-of-account) | **OPEN** — atp-adp owner + operator |
| C62-B15 | design-Q (settlement policy could block exit) | **OPEN** — operator |
| C62-B12 | cross-track SDK (`validate_minimum_viable` structural approx.) | **OPEN — WIDENED by C174-N1 to the published Rust mirror (`society.rs:225`); now a two-language bundle** |
| C62-B13 | cross-track SAL (§2.2 example <3 witnesses) | **OPEN, live** — folds to C58-B1 SAL bundle |
| **C174-N1** | cross-track SDK (Rust `society.rs:225` = published site of C62-B12) | **NEW — carry-only; bundle with C62-B12** |
| **C174-N2** | observation (Rust `society.rs` protocol primitives vs §5.1/§2.2) | **NEW — INFO, no action; SDK-track if web4-core grows an ISP layer** |
| C6-L2 | deferred-carry (Gesellian framing) | persists, informational |

None gate a normal AUDIT turn. Surface the design-Q set as ONE decision memo when the operator is available. **No spec-side carry changed status since C136.**

---

## Cross-Cutting Observations

1. **The C172 SDK-mirror lesson reconfirms on an unrelated target.** ISP was clean-and-blind for C102 + C136 because the audit tracked only the spec + Python; the *shipped* Rust `society.rs` — carrying ISP §2/§5/§6 primitives — was never adjudicated. Two of the three prior "clean" ISP deltas would have flagged N1 had the Rust mirror been in scope. **Expand the SDK-mirror set at every delta.**
2. **Direction differs from C172.** C172's Rust findings were "spec is stale vs a ratified contract" (key-derived `lct_id`). C174-N1 is the *inverse*: the ISP spec is **correct and self-consistent** (§6.3 explicitly disclaims enforcement of §6.2), and the SDK's docstring over-claims relative to what §6.3 permits it to validate. A delta auditor must decide *direction* per finding, not assume "SDK ratified ⇒ spec stale."
3. **Cross-language parity is a finding multiplier, not a mitigant.** `role.py:354`'s explicit "cross-language parity with `society.rs`" means the C62-B12 structural-approximation carry was *replicated by design* into the published Rust SDK. A parity declaration propagates a known defect class to every mirror — check parity anchors when re-deriving mirror sites.
4. **Refute-by-default down-graded both candidates honestly.** N1 fell from "validation bug" to "LOW docstring gap" once ISP §6.3 was read; N2 fell from "missing protocol" to "INFO, category-appropriate primitive." Neither was inflated to justify a non-clean result.

---

## §D: Lessons → Memory

1. **The SDK-mirror set is not fixed and it GROWS toward web4-core.** C172 found it in `lct.rs`; C174 finds it in `society.rs`. At each delta, re-derive primitive-implementers at live HEAD (Python SDK AND Rust web4-core) *before* declaring the delta clean, and **follow cross-language parity anchors** (`role.py:354`-style comments) — a parity declaration means a Python-side carry likely has a live, possibly-published Rust twin. (Extends [[feedback_prior_finding_path_provenance]].)
2. **Decide finding DIRECTION per finding.** A ratified/published Rust mirror does not imply "spec is stale." When the spec itself disclaims a behavior (ISP §6.3: §6.2 is guidance-not-enforcement), the SDK is the site and the spec is correct — the honest fix is an SDK docstring, not a spec mutation.
3. **A parity comment is a defect-propagation vector.** When an SDK method documents "cross-language parity with X," a known carry against that method's Python site should be presumed live at X until verified otherwise. (Widen the carry to the parity twin, don't re-open it as net-new.)

---

## Remediation Routing (for C175)

**C175 ISP remediation slot = NO-OP on the spec (frozen target; 0 spec-side autonomous-actionable findings).** Non-spec outcomes route off-target:
- **SDK track (bundled):** C174-N1 + C62-B12 = one two-language finding — docstring note on `validate_minimum_viable` at `role.py` AND `society.rs:225` that it checks structural proxies, not ISP §6.2 semantic requirements (which §6.3 disclaims from enforcement). Carry-only; do not self-apply (out-of-bounds this session).
- **SDK track (deferred):** C174-N2 — note distinguishing `secede`/`join_federation`/`add_constituent` struct primitives from ISP §5.1/§2.2 protocols, actioned only if web4-core grows an inter-society-protocol layer.
- **Operator design-Q memo:** B1, B2-full, B10 (two-sided), B11 (atp-adp owner), B15.
- **SAL bundle (C58-B1):** B13 (§2.2 birthcert example <3 witnesses).
- **Carried, no action:** C6-L2 (Gesellian framing).

Per the no-op→advance rotation, C175 advances +2 to the next rotation file: **entity-types** (`entity-types.md`, last audited C137). **Guard for that fire: apply the same SDK-mirror expansion — check `web4-core/src/*.rs` for entity-type primitives (`role.rs`, `role_extension.rs`, `lct.rs`, `did.rs`), not just the Python `entity.py`.**

---

**Audit date**: 2026-07-11
**Source spec date**: 2026-06-16 (header L4; byte-frozen 25 days, unchanged since the C136 snapshot)
**Auditor**: Legion autonomous session, slot `000036`, LEAD voice
**Method note**: frozen-spec 4th-delta; §A held-by-construction + `&#` sweep (10/10 held, 0 artifacts); §B corpus-delta over 6 cited siblings (1 moved: atp-adp-C151 §2.4, DISJOINT at cited-hunk granularity, adversarially verified); **§B′ SDK-mirror expansion (C172 guard) — first ISP audit to adjudicate the published Rust `society.rs` mirror**, yielding C174-N1 (LOW, widens C62-B12) + C174-N2 (INFO). Flagship adversarially refuted down from "validation bug" to "docstring gap" via ISP §6.3. Cross-track/SDK findings only; zero spec mutation; not padded.
