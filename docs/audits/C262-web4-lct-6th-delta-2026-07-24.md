# C262 — 6th-Delta Re-Audit of `protocols/web4-lct.md` (the frozen LCT sister-doc)

**Date**: 2026-07-24
**Auditor**: Legion autonomous web4 track (slot `web4-20260724-000036`, LEAD)
**Target**: `web4-standard/protocols/web4-lct.md` (278 lines)
**Type**: **6th-delta re-audit**. Read-only — produces this audit doc, makes **no file edits** (the target is D0-gated).
**Lineage**: C60-B13 → **C74** first audit (#363, 28 findings B1–B28) → **C75** `protocols/` cluster triage (#364) → **C114** 2nd-delta (+N1) → **C146** 3rd-delta (3.1 path correction) → **C186** 4th-delta (C172-N1 scope-widening) → **C224** 5th-delta (3.2 locus 689→718; C114-N1 SDK-vote witness) → **C262**.
**Snapshot baseline**: target blob `5f68a5c7bda9b1dbcfd81f0324df61243efbaab7` — **byte-frozen since `27b85624` (2026-02-17); unchanged since C74/C114/C146/C186/C224** (re-verified this delta: `git rev-parse HEAD:web4-standard/protocols/web4-lct.md` = `5f68a5c7`). C224 corpus baseline was 2026-07-19.
**Method**: §A prior-finding persistence (C74 B1–B28, C75 3.1/3.2, C114-N1) with the frozen-target re-read disciplines (C56 claim-vs-canonical; C108/C112 cross-section blindspot) + **live-HEAD locus re-confirmation** (C146 / [[feedback_prior_finding_path_provenance]]). §B corpus-delta scan since the C224 baseline. **§B′ SDK-mirror gate** (the C178–C222 verdict ladder) re-run on `web4-core/src/lct.rs` + `attestation.rs`. Refute-by-default on any candidate. The 49-agent C74 finder workflow was deliberately **not** re-run (proportionality: byte-frozen target with an EMPTY corpus-delta — same call as C186/C224).

---

## Headline (read this first)

`protocols/web4-lct.md` is **byte-identical to its C74/C114/C146/C186/C224 snapshot** (blob `5f68a5c7`). §A confirms **28/28 C74 findings HELD, 0 regression**, C114-N1 HELD, and both C75 structural defects re-verified at **live HEAD**. **0 net-new internal findings** — web4-lct's substantive-clean **6th consecutive** delta.

**This cycle the corpus did not move at all.** Every web4-lct-scoped referent is frozen since the C224 snapshot (2026-07-19): the target, canonical `LCT-linked-context-token.md` (`d89595e8`), `web4-standard/README.md` (last touched `d89595e8`), the SDK mirror `web4-core/src/lct.rs` (`2ec6ae09`), the on-subject module `attestation.rs` (`0e997079`), and `ratchet.rs` (`7b048a78`). This is the **first EMPTY corpus-delta on web4-lct** — a clean contrast to C224, which absorbed the largest SDK motion yet (+746 lines). With nothing moving, §A holds by construction, §B is empty, and §B′ re-confirms the C224 verdict without new evidence.

- **§A prior findings:** all HELD; 3.1 locus `README.md:64` verbatim; 3.2 locus canonical `:718` verbatim — **no renumber this cycle** (canonical did not move), so the C146 path-provenance discipline fired but found no shift.
- **§B corpus-delta:** **EMPTY** — no web4-lct-scoped file moved since C224.
- **§B′ SDK-mirror gate:** re-confirmed. `lct.rs`/`attestation.rs` remain a GENUINE on-subject canonical-descendant mirror (`derive_lct_id` key-derived, `citizenships: Vec<BirthCertificateRef>`, `authority_ratchet`, payload-free `AttestationType`) — the **4th D0=SUPERSEDE witness from C224 stands unchanged; no 5th witness accrued** because the code did not move.

**D0 remains operator-unanswered and gates all remediation. Nothing here edits any file or re-decides D0 or the flagship B-D1.**

**One audit-metadata provenance calibration (not a finding):** C224 §A.2 recorded `web4-standard/README.md` as frozen at `27b85624`; its actual last-touching commit is `d89595e8` (#531, 2026-07-16 — *before* C224 ran). The 3.1 defect content at `README.md:64` is byte-present and **HELD-REAL** (the line was introduced at `73353b34` and carried forward untouched by #531); only C224's recorded README freeze-commit was stale. Corrected here per the path-provenance discipline. Not a regression, not net-new.

---

## §A — Prior-finding verification

### A.1 — C74 findings (B1–B28): 28/28 HELD, 0 regression
The target blob is byte-identical to the C74/C114/C146/C186/C224 snapshot (`5f68a5c7`), so all line-anchored findings hold by construction. Spot-re-verified the load-bearing ones at HEAD:
- **B1** (§1 JSON still does not close — the object opened at L10 has no closing `}` before L52) — HELD.
- **B7** (`entity_type` = 12 vs canonical 15) — HELD (§2.2 L63 enumerates 12; canonical `entity-types.md` frozen C65 `5baa160f` at 15).
- **B8** (`t3_tensor`/`v3_tensor` absent) — HELD; `lct.rs` still omits tensor fields (canonical-lag, C172/C180 scope), so this remains a sister+SDK gap, not sister-only.
- **B9** (birth-cert shape divergence) — HELD; §B′ re-confirms the SDK's concrete plural-reference birth-cert model (a SUPERSEDE witness, not a new sister defect).
- **B13/B14/B15** (identifier model — signature-hash `lct_id` at `:147`) — HELD; §B′ (`derive_lct_id` is key-derived → C172-N1 carry).
- **B16** (SAL `Web4BirthCertificate`; SAL frozen) — HELD.
- **B25** (§1 "COSE Sig" `:18` vs §3 signing scope) — HELD.
No remediation has landed (D0-gated) → §A is pure persistence verification. The 5 C74-refuted items remain correctly refuted.

### A.2 — C75 structural defects — both HELD at live HEAD; no locus shift this cycle
Per C146's path-provenance lesson, both defects were re-verified against **live HEAD bytes**. This cycle canonical did not move, so neither locus shifted.

| C75 defect | C224 recorded locus | C262 verification at HEAD | Disposition |
|------------|---------------------|---------------------------|-------------|
| **3.1 README SSOT inversion** | `web4-standard/README.md:64` | `grep -n "protocols/web4-lct.md" README.md` → `64:- [**protocols/web4-lct.md**](protocols/web4-lct.md) - Linked Context Token specification`. Verbatim. | **HELD — REAL**. *Metadata calibration:* the line's introducing commit is `73353b34`; its last-touching commit is `d89595e8` (#531, 2026-07-16), **not** the `27b85624` C224 recorded — but #531 did not alter line 64. Content HELD, freeze-commit corrected. |
| **3.2 Canonical-defers-to-frozen** | `LCT-linked-context-token.md:718` | `grep -n "protocols/web4-lct.md"` → **`:718`** `- **LCT Protocol Details**: \`protocols/web4-lct.md\``. **Unchanged** (canonical frozen `d89595e8` since 2026-07-16; no insert this cycle). | **HELD — REAL**, locus stable at `:718`. |

### A.3 — C114-N1 (internal `claims` cross-section contradiction): HELD
Byte-frozen → holds by construction. §2.6 "Attestation Fields" (L107–114) enumerates four fields (`witness`/`type`/`sig`/`ts`) with **no** `claims`; §6.1 (L221) carries a "Required Claims" column and §6.2 (L237) shows a `claims:{}` object. The two normative halves remain inconsistent. The C224 live SDK witness (attestation.rs, 4 fields / no claims) **stands unchanged** (`0e997079` did not move). N1 stays **blocked-on-D0 / queued-for-the-maintain-path** (not self-applied).

### A.4 — C56 claim-vs-canonical re-read
Every cited canonical source is frozen at or before the C224 baseline: entity-types C65 (`5baa160f`), SAL, witnessing, and canonical `LCT-linked-context-token.md` (`d89595e8`, 2026-07-16 — the #531 motion C210 audited and C224 consumed). Nothing moved this cycle → **no B-line cross-doc claim went stale**. The frozen sister still carries zero `prescrib|threshold|inspectable` tokens, so #531's "Inspectable Evidence, Not Prescribed Trust" principle remains DISJOINT with no sister surface to contradict (inbound-consumed by C210).

---

## §B — Corpus-delta scan (net-new from moving mirrors)

### B.1 — Corpus-delta surface since C224 (2026-07-19): **EMPTY**

| Referent / sibling | last commit | moved since C224 baseline? |
|--------------------|-------------|----------------------------|
| `protocols/web4-lct.md` (target) | `27b85624` 2026-02-17 | **no** (byte-frozen, blob `5f68a5c7`) |
| `web4-standard/README.md` (3.1 locus) | `d89595e8` 2026-07-16 | no (predates C224 baseline) |
| `core-spec/entity-types.md` (B7) | `5baa160f` 2026-06-16 | no |
| `core-spec/LCT-linked-context-token.md` (3.2 locus host) | `d89595e8` 2026-07-16 | no (predates C224 baseline; #531 consumed at C210/C224) |
| `web4-core/src/lct.rs` (SDK mirror) | `2ec6ae09` 2026-07-18 | no (C224 baseline value) |
| `web4-core/src/attestation.rs` (on-subject module) | `0e997079` 2026-07-17 | no (C224 baseline value) |
| `web4-core/src/ratchet.rs` | `7b048a78` 2026-07-16 | no |

**Every web4-lct-scoped referent is frozen since the C224 snapshot.** No new suite/module/canonical motion. This is the **first EMPTY corpus-delta on web4-lct** — the SDK-GROWS surface the delta method exists to catch produced nothing because the crate did not grow this interval (consistent with C258/C260's fleet-wide observation that `web4-core/src` and `web4-standard/` have had 0 commits since ~2026-07-18/19).

### B.2 — Cross-section blindspot sweep: no new internal contradiction
Re-ran the §6-vs-§2.6/§1 cross-section comparison that produced C114-N1, extended to §2.7/§2.8 vs §1 inline examples. All internal contradictions reduce to already-recorded B2–B5 / N1. **0 net-new internal findings.**

---

## §B′ — SDK-mirror gate (C178–C222 ladder), re-run on `lct.rs` + `attestation.rs`

**Gate step 1 — is the mirror genuine and on-subject?** **GENUINE and ON-SUBJECT** (unchanged from C224). `lct.rs` implements the LCT primitive; `attestation.rs` implements the §2.6/§2.3 attestation + birth-certificate surface. Both cite canon §2.3.

**Gate step 2 — does the mirror track the frozen sister or canonical?** **Canonical.** Re-verified the C224 invariants at HEAD — all unchanged:
- `derive_lct_id(public_key)` at `lct.rs:361` = `sha256(public_key)` — **key-derived**, not the sister's `MB32(SHA256(binding_proof))` signature model (§C172-N1 carry, covers sister `:147`).
- `citizenships: Vec<crate::attestation::BirthCertificateRef>` at `lct.rs:164` (#538) — concrete plural-reference birth certificates; frozen sister has singular prose `birth_certificate` (§B9).
- `authority_ratchet: Option<crate::ratchet::RatchetRequirement>` at `lct.rs:180` (#544) — LCT carries a society-ratchet reference; frozen sister has no counterpart.
- `AttestationType` at `attestation.rs:37` = **payload-free 7-class enum** (`Time`/`Audit`/`Oracle`/`Existence`/`Action`/`State`/`Quality`), no `claims` — the C114-N1 §2.6-side vote.

**Verdict ladder placement:** GENUINE on-subject mirror, **tracking canonical away from the frozen sister** → the **4th D0=SUPERSEDE witness established at C224 STANDS**. **No 5th witness accrued** — the code did not move this cycle, so the SUPERSEDE trend meter did not advance; it simply held. The `authority_ratchet` field remains the LCT carrying a *reference* to the society/governance ratchet (`ratchet.rs` #529, C202/C222 = governance scope), orthogonal to the LCT-identity subject, not a sister defect.

---

## §C — Routing

### D0 — FLAGSHIP DESIGN-Q (operator; UNCHANGED, still gates everything)
**Is `protocols/web4-lct.md` a maintained sister-doc, or superseded by canonical `core-spec/LCT-linked-context-token.md`?** Operator-unanswered. Auditor recommendation remains **SUPERSEDE**, supported by the four independent witnesses established through C224 (canonical structural divergence B7/B8/B9; the README/back-pointer inversion 3.1/3.2; the key-derived-id SDK direction C172-N1; the ratified concrete birth-cert-refs + `authority_ratchet` + op-key surfaces). This cycle adds **no new witness** (empty delta) but also **no counter-evidence** — the gap between shipped code and the frozen sister neither widened nor closed this interval. **No remediation may touch this file until D0 resolves.**
- If D0 = **SUPERSEDE**: deprecation/SSOT banner on `web4-lct.md` + fix `web4-standard/README.md:64` → link canonical + delete canonical `LCT-linked-context-token.md:718` deferral. N1 and all B-line items become moot.
- If D0 = **MAINTAIN**: the C74 autonomous list + N1 (with the C224 shipped-SDK direction vote) + B25 COSE_Sign1 sharpening + the C172-N1 key-derived-id update (covering `web4-lct.md:147`) define the remediation.

### This delta's deliverables — routed, NOT self-applied
1. **README freeze-commit metadata correction:** C224 §A.2 recorded `README.md` frozen at `27b85624`; the accurate last-touching commit is `d89595e8` (#531). The 3.1 defect content at `:64` is HELD-REAL and unaltered by #531. Audit-record corrected; under D0=SUPERSEDE this is the line to fix.
2. **3.2 locus stable** at canonical `LCT-linked-context-token.md:718` (no renumber this cycle). Under D0=SUPERSEDE this is the line to delete.
No file is edited by this audit.

### Carries — UNCHANGED (re-confirmed open at live HEAD)
D0 (flagship); C114-N1 (blocked-on-D0, SDK direction-witness held); C172-N1 (MED, covering sister `:147`); identifier-model design-Q (B13/B14/B15, couples C60-H1 / C24-H1); revocation propagation / future-timestamp (B26/B27); REQUIRED-vs-OPTIONAL presence (B10); cross-track to SAL (B16/B18), witnessing registry (B17), registries-canonicity (B19). The 6 other `protocols/` sisters remain triaged-not-audited per C75 while D0 pends.

---

## §D — Method notes (for the next AUDIT turn = C264, web4-lct's rotation successor is `mcp`; web4-lct returns at its next slot ~C296)

1. **First EMPTY corpus-delta on web4-lct — and it is a clean PASS, not a prompt to manufacture.** C224 absorbed the largest SDK motion yet (+746 lines); C262 absorbed nothing. The honest, correct outcome for a byte-frozen target with all mirrors frozen is "0 net-new, HELD by construction, D0 still gates" — reported as such. Resisting the urge to mint a finding to look productive is the discipline ([[feedback_prose_is_not_ledger]]).
2. **Path-provenance discipline fired but found no shift.** Canonical did not move this cycle, so the 3.2 back-pointer stayed at `:718`. The discipline is cheap insurance regardless of outcome — a frozen target does not guarantee a frozen inbound locus, but this interval both were frozen ([[feedback_prior_finding_path_provenance]]).
3. **A metadata-provenance calibration surfaced independently of any locus shift.** C224's recorded README freeze-commit (`27b85624`) was stale — README's true last-touching commit is `d89595e8` (#531), which predates C224. The 3.1 content was unaffected, so the defect held; only the recorded freeze-commit was wrong. Lesson: re-derive a sibling's freeze-commit at live HEAD, not just the finding's line content — audit metadata drifts too.
4. **The SUPERSEDE trend meter is a ratchet, not a decay.** No 5th witness accrued (empty delta), but the 4 prior witnesses stand and no counter-evidence emerged. A quiet interval neither strengthens nor weakens the D0=SUPERSEDE recommendation; it holds.
5. **Frozen ≠ clean, confirmed a sixth consecutive time on this file** (C114/C146/C186/C224, now C262). This cycle it is *also* Frozen = frozen-corpus = genuinely nothing-to-do — the rare case where the byte-freeze and the corpus-freeze coincide and the audit is pure re-confirmation.
6. **Snapshot baseline recorded** (target blob `5f68a5c7`; `lct.rs` `2ec6ae09`; `attestation.rs` `0e997079`; canonical LCT `d89595e8`; README last-touch `d89595e8`) so the next delta detects motion in one `git rev-parse`. Whichever pass next reaches **canonical LCT** owns C172-N1's remediation; this file only inherits it under D0 = MAINTAIN.
