# C100: LCT-linked-context-token.md 2nd-Delta Re-Audit (3rd delta overall)

**Date**: 2026-06-25
**Auditor**: Autonomous session (legion-web4-20260625-120010)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (697 lines, HEAD — byte-identical to C61 `9d1933f8`)
**Prior audits**: C9 (`lct-internal-consistency-2026-05-22.md`, 8 → PR #225 clean 8/8) → C24 (`C24-...-2026-05-31.md`, 12 NEW → PR #256: 6 autonomous / 4 DQ + 2 SDK) → **C60** (`C60-...-2026-06-15.md`, 21 distinct → PR #338) → **C61 remediation** (`9d1933f8` #338: 9 autonomous applied).
**Spec mutations since C60**: 1 — PR #338 (the C61 remediation itself). File **byte-identical since #338** (`git diff 9d1933f8 HEAD` empty).

**Framing**: Fifth consecutive **frozen target** (after C92 SOCIETY_SPEC, C94 dictionary, C96 metabolic, C98 SAL — all 0 autonomous). The LCT spec has not moved since its own C61 remediation (10 days). Per the locked frozen-target pattern, **§A = verification** (did the 9 C61 remediations hold, did anything regress, do all carries stand) and **§B yield is entirely on the corpus-delta surface** — the sibling docs that MOVED since the C60 snapshot. No finder pass was run over unchanged LCT prose (anti-padding BC-C23-5: a clean frozen §A stands on its own).

**Policy conditions honored**:
1. §A verifies the 9 C61 remediations by the **C56 completeness method** (each claim checked token-by-token against canonical, not merely "edit present"). "FROZEN" is treated as frozen-relative-to-its-own-remediation, since the LCT itself moved at C61.
2. The C61 ≥3 birth-witness reword was re-checked against the **2-vs-3 contradiction** C58 refuted as subsumed under C23-H1 — confirmed NOT re-opened (see §A.2).

**Counts**:
- **§A**: 9/9 C61 autonomous remediations **HELD** token-by-token, 0 regressed, 0 HTML-entity/`&#` artifacts; witness floor uniformly ≥3 (no 2-vs-3 re-opening); all carried-OPEN C24 + SDK + C60 design-Q items re-confirmed STANDING.
- **§B**: 3 moved siblings diffed against the C60 snapshot → **0 net-new autonomous defects**; all 5 LCT cross-track carries the moved siblings could have resolved/regressed (A1, B9, B10, B12, B19) instead **STAND** (1 mild hardening, 1 off-target convergence observation).
- **C100 distinct new findings**: **0** (positive frozen-target result).

---

## §A. Verification (C56 completeness + mirror method)

### A.0 — Frozen-state + artifact confirmation
- `git diff 9d1933f8 HEAD -- LCT-linked-context-token.md` → **empty** (byte-identical to the C61 remediation).
- HTML-entity / `&#` / `&amp;` / `&lt;` sweep → **0 hits**. Clean.

### A.1 — The 9 C61 autonomous remediations (9/9 HELD, token-by-token)

| C61 ID | Site | Live verification @ HEAD | Verdict |
|--------|------|--------------------------|---------|
| **A1** | §6.1 L385 / §6.2 L422 | Both "Canonical weights" blocks cite `t3-v3-tensors.md §10.2` as protocol-invariant SSOT verbatim; no residual standalone "(normative)" self-declaration. | HELD |
| **A2** | §6.2 L410 | `"composite_score": 0.0+,  // CAN exceed 1.0 when valuation does (see note)`. | HELD |
| **B3** | §4.2 L301 | "Witnesses MUST be members of issuing society (enforcement is implementation-defined; the §11.2 reference validator … does not currently verify society membership)". | HELD |
| **B4** | §11.2 L653 + L658-660 | `assert witness_attested(lct, witness)   # implementation-defined` + the full "Implementation-defined helper" semantics paragraph (COSE_Sign1 / present-only-minimum / `attestations` array). | HELD |
| **B5** | §7.3 L477 | `Both LCTs valid (new LCT status = "active"; parent stays "active" until retired)`. | HELD |
| **B14** | §8.1 L508 | "Witness quorum: Birth requires a quorum (≥3) … (witness distinctness / anti-collusion is not asserted by this property alone …)" — "independent" removed. | HELD |
| **B16** | §8.3 L524 | "Selective attestation: Non-birth attestations may share only relevant witnesses (birth certificates require the full `birth_witnesses` set …)". | HELD |
| **B18** | §8.1 L509 | "Blockchain anchor: … temporal proof (when present; `genesis_block_hash` is RECOMMENDED, not required …)". | HELD |
| **B19** | §9.3 L548 | "Never attest to future timestamps (verification is implementation-defined — the protocol mandates no reference clock, skew tolerance, or error path; treat as an advisory honesty constraint …)". | HELD |

0 regressed. No remediation introduced a new `&#`/markdown artifact or shifted a sibling's expected value.

### A.2 — Binding-condition re-checks

- **Witness-count uniformity (2-vs-3 guard)**: the ≥3 birth-witness floor is uniform across L206 ("minimum 3"), L283 ("Array of ≥3"), L300 ("Minimum quorum: 3"), L311 ("Required (≥3)"), L508 (B14 reword "quorum (≥3)"), L604 (`assert … >= 3`). **No "2 witness" / "two witness" / "minimum 2" floor exists** anywhere (grep hits on "2" resolve to "§11.2" references, not counts). The C61 B14 reword did **NOT** re-open the 2-vs-3 contradiction C58 refuted as subsumed under C23-H1. Condition satisfied.
- **C23-H1 firewall**: the birth-certificate 3-way shape remains cite-only per the BC-C23-1 firewall; not re-litigated here.

### A.3 — Carried items re-confirmed OPEN (all STAND)

| ID | Class | Re-verification @ HEAD | Status |
|----|-------|------------------------|--------|
| C24-H1 | DESIGN-Q | LCT L260 `lct:web4:<hash>` (2-seg) vs SDK `lct.py:289` `lct:web4:{entity_type}:{h}` (3-seg). Divergent. | OPEN |
| C24-M2 | SDK cross-track | `LCT.create()` still does not populate `mrh.witnessing` (SDK frozen since 2026-04-17). | OPEN |
| C24-M3 | SDK cross-track | `LCT.create()` still does not build `attestations` from witnesses. | OPEN |
| C24-M4 | DESIGN-Q | SDK `RevocationStatus.SUSPENDED`; spec still does not enumerate `revocation.status`. | OPEN |
| C24-M6 | DESIGN-Q | §7.3 "superseded" status vs §7.4 reason-list; SDK has neither. | OPEN |
| C24-L3 | DESIGN-Q | §6.2 valuation 0.0+ vs composite annotation (A2 resolved annotation; design-Q on bound semantics stands). | OPEN |
| C60-B2 | DESIGN-Q | `mrh.paired[].context` unmodeled (SDK + vector frozen). | OPEN |
| C60-B6/B7/B8 | SDK | V3-clamp / no-bootstrap-path / no-quorum-guard at genesis factory (SDK frozen). | OPEN |
| C60-B12 | DESIGN-Q | entity_type closed-15 vs lct-capability-levels extended types (see §B). | OPEN |
| C60-B14-req/B15/B17 | DESIGN-Q | anti-collusion requirement / selective-disclosure layer / per-attestation revocation mechanism. | OPEN |
| C60-B1 | vector | `valid-birth-certificate.json` still missing `issuing_society` (grep=0), `t3_tensor`/`v3_tensor`, ≥3 witnesses (vector corpus frozen since Sprint 30). | OPEN |
| C60-B9/B10/B11/B13 | sister-doc | tensor cardinality / `dimensions`-wrapper / birth_timestamp gating / web4-lct enum staleness (see §B). | OPEN |

---

## §B. Corpus-Delta Surface (moved siblings only)

Three sibling docs moved since the C60 snapshot (`7b49a08a`, 2026-06-15). Each was diffed against the snapshot to determine whether its movement **RESOLVED**, **HARDENED**, or **REGRESSED** an LCT cross-track carry. The **snapshot-presence guard** ([[feedback_snapshot_presence_guard]]) was applied to every candidate: a moved-sibling divergence is only net-new if it was absent at the C60 snapshot — reword ≠ new normative content.

| Sibling | Moved at | LCT carries touched | Result |
|---------|----------|---------------------|--------|
| **t3-v3-tensors.md** | C83 #374 (2026-06-21) | A1, B9, B10 | A1 target intact; B9 hardened; B10 verbatim |
| **entity-types.md** | C65 #344 (2026-06-16) | B12 | verbatim (off-target convergence note) |
| **errors.md** | C67 #347 (2026-06-17) | B19 | verbatim |

### B.1 — t3-v3-tensors.md (C83)

- **A1 (SSOT citation)**: A1 makes LCT §6.1/§6.2 cite t3-v3 **§10.2** as the protocol-invariant SSOT. The §10.2 self-declaration — `**This table is the normative source** for all protocol-invariant formulas, weights, and constants` — is present and **unchanged** at both the C60 snapshot (L558) and live (L620). C83 did not touch it. **A1 citation target intact → A1 STANDS valid (HELD).**
- **B9 (single-embedded-composite vs §6.3 per-role cardinality)**: §6.3's rule is unchanged at HEAD — L468 "Implementations MUST NOT compute global (role-agnostic) trust scores — only role-specific tensors"; L469 "Each role MUST maintain separate T3/V3 tensors". C83 **added** a "flat, role-agnostic schema" bridge section for protocol extensions that explicitly states such extensions are "collapsed into the 3 roots, rather than introducing a parallel role-agnostic composite **(which §6.3 forbids)**". This **sharpens** B9 — the LCT §6.x mandate ("Every LCT MUST contain a `t3_tensor`/`v3_tensor`" with a single embedded `composite_score`) is now contrasted against an even more prominent §6.3 prohibition. **Per the snapshot-presence guard, this is NOT a net-new finding**: the §6.3 prohibition itself is unchanged; B9 already captured the tension. Recorded as a **mild hardening** of standing carry C60-B9, not a new defect. (The C83 bridge is, usefully, the canonical pattern that an LCT-embedded-composite reconciliation should follow.)
- **B10 (`dimensions`-wrapper vs flat roots)**: C83 did not change t3-v3 JSON nesting; the wrapper contradiction is anchored on `lct-capability-levels.md` (FROZEN since C57, pre-snapshot). **B10 STANDS verbatim.**

### B.2 — entity-types.md (C65)

- **B12 (entity_type closed-15 vs extended types)**: C65 edited the behavioral-mode columns (Hybrid → "Agentic/Responsive/Delegative"; Infrastructure → "None"), the ADP-slashed→consumed wording, and a witness-LCT format. It did **not** change the entity-type count or the closed-vs-extended framing. The LCT enum (L68) remains the canonical **15** (`human|ai|society|organization|role|task|resource|device|service|oracle|accumulator|dictionary|hybrid|policy|infrastructure`). **B12 STANDS verbatim.**
- **Off-target convergence note (no LCT action)**: C65's "ADP slashed → ADP consumed (permanently destroyed via maintenance) … distinct from the punitive, authority-executed *slashing* of `atp-adp-cycle.md` §2.4" is the **same maintenance-discharge-vs-slashing distinction** the C79 atp-adp delta introduced and that C94/C96 already noted converging corpus-wide. It touches no LCT carry; recorded only as evidence the slashing-terminology convergence is now in entity-types too.

### B.3 — errors.md (C67)

- **B19 (no timestamp-validation error path)**: C67 added 3 error-code remediations but **no** timestamp/clock/skew code; no timestamp-validation error code exists in errors.md at all (grep=0). B19's observation that the spec "mandates no … error path" **STANDS** — and is already scoped advisory/impl-defined on the LCT side by the C61 B19 reword. No action.

**§B net**: 0 net-new autonomous defects. Every carry the moving corpus could have resolved or regressed instead STANDS. The single substantive movement (C83's §6.3 bridge) sharpens B9 without changing its status.

---

## §C. Routing for C101

**C101 LCT remediation slot = NO-OP.** C100 found 0 autonomous-actionable defects (target frozen; §B yielded 0 net-new). There is nothing to apply — same outcome as C95 (dictionary), C97 (metabolic), C99 (SAL). Rotation advances to **next-oldest = `isp-identity-system-protocol`-family / `ISP` (last audited C62/C63, 2026-06-16)** for its 2nd-delta (≈C102), per the fixed round-robin.

**Standing carries (all STAND — none gate a normal AUDIT turn; surface as ONE operator memo):**
- **DESIGN-Q (operator)**: C24-H1 (lct_id 2-seg vs SDK 3-seg), C24-M4 (revocation.status enum), C24-M6 (superseded status-vs-reason), C24-L3 (valuation bound), C60-B2 (paired.context), C60-B5-uniqueness (active-count invariant + disambiguation), C60-B12 (entity_type extended-types), C60-B14-req (anti-collusion requirement), C60-B15 (selective-disclosure layer), C60-B17 (per-attestation revocation).
- **SDK cross-track** (SDK frozen since 2026-04-17): C24-M2/M3 (witnessing/attestations population), C60-B6 (V3 clamp ↔ L3), C60-B7 (bootstrap factory), C60-B8 (genesis quorum guard).
- **Vector corpus**: C60-B1 (regenerate `valid-birth-certificate.json` to current normative shape — still 3-way broken).
- **Sister-doc reconciliation**: C60-B9 (tensor cardinality vs t3-v3 §6.3 — **sharpened by C83's bridge**; the C83 flat-schema collapse pattern is the recommended reconciliation model), C60-B10 (`dimensions`-wrapper vs flat across capability-levels/t3-v3/LCT), C60-B11 (birth_timestamp gating vs capability-levels + capability.py), C60-B13 (`web4-lct.md` 7-role + 15-type staleness).
- **Firewall / DEMOTED**: C23-H1 (birth-cert 3-way shape, cite-only), C24-D1 (ontology L219 cluster), C24-D2 (AI/ai).

---

## §D. Lessons

1. **Bold markdown can hide a citation target from an exact grep.** A1's cited SSOT phrase is `**This table is the normative source** for all protocol-invariant formulas` — the `**…**` split broke a verbatim `grep "normative source for all protocol-invariant"`, falsely suggesting the citation target had vanished at C83. A loose grep (`normative source`) plus a snapshot diff confirmed it present and unchanged. **When a cross-ref appears to have gone stale, diff the target against the prior snapshot before reporting it — markdown emphasis fragments string matches.** (Extends the snapshot-presence guard to citation-target verification.)
2. **A sibling remediation can SHARPEN a standing cross-doc carry without creating a net-new finding.** C83 added a §6.3 bridge that makes the B9 cardinality tension more prominent, but the underlying §6.3 prohibition is unchanged — so B9 is hardened, not net-new. The snapshot-presence guard ([[feedback_snapshot_presence_guard]]) is what distinguishes "the corpus moved toward my carry" from "I found a new defect." Report the former as a hardening note in §C routing, not a §B finding.
3. **Fifth consecutive frozen target confirms the steady-state model.** Across C92/C94/C96/C98/C100 the files churn slower than the audit cadence; every wrap hits a frozen target, §A is pure verification, and §B yield lives entirely on the moved-sibling / inbound-carry surface. The instrument that earns its keep on a frozen target is the **corpus-delta diff**, not a fresh finder sweep.

---

## Cross-Reference to Prior Audits

| Audit | Spec | Findings | Remediated |
|-------|------|----------|------------|
| C9 | LCT (1st) | 8 | PR #225 (8/8 clean) |
| C24 | LCT (re-audit) | 12 NEW | PR #256 (6 autonomous; 4 DQ + 2 SDK) |
| C60 | LCT (2nd delta) | 21 distinct | PR #338 / C61 (9 autonomous applied) |
| **C100** | **LCT (3rd delta)** | **0 new** (9/9 C61 HELD; all carries STAND; §B 0 net-new on moved siblings) | **N/A — C101 remediation slot = NO-OP** |

*"An LCT is not an identity. It is a presence — witnessed, contextualized, and witness-hardened."* — and across four audits (C9 → C24 → C60 → C100), the witnessing, tensors, and security claims have stabilized: the third delta moves nothing because the second delta's remediation held and the corpus around it converged.
