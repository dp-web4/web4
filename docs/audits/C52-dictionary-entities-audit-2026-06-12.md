# C52 — Delta Re-Audit: dictionary-entities.md

**Date**: 2026-06-12
**Auditor**: Legion autonomous web4 track (slot 120047, v2 protocol)
**Target**: `web4-standard/core-spec/dictionary-entities.md` (603 lines, head `958a5625`)
**Prior audit**: C17 (`docs/audits/dictionary-entities-internal-consistency-2026-05-27.md`, PR #241)
**Prior remediation**: PR #242 (`991a0092`, 2026-05-28, +28/−13) — 7 autonomous-actionable findings applied (H1, H2-rename, M2, M3, M5, L1, L2); 4 design-Q deferred (M1 ontology, M4 error taxonomy, M6 threshold semantics, H2 role-value); 1 cross-track (INFO1 SDK dataclass)
**Staleness at audit**: 15 days since #242; no commits have touched the target since (`git log 991a0092..958a5625 -- <target>` empty). **Oldest never-delta-re-audited file in the corpus** at selection time.
**Sister-spec drift exposure**: the corpus-wide `value`→`valuation` V3 renames (#277/#279/#305/#309/#311), attestation `witness`→`lct` key fixes (C46/C48), C33 id-scheme consolidation, mcp-protocol §7.3–7.6 amendments, and the creation of `web4-standard/implementation/sdk/web4/dictionary.py` (C17-INFO1 recorded it as absent) ALL post-date #242 — this spec has never been audited against any of them.
**Method**: §A LEAD-direct re-verification of all 7 applied findings + cross-referential #242 regression sweep (C50 §D lesson: hunk-local sweeps miss cross-referential defects); §B multi-agent finder sweep with refute-by-default adversarial verification + primitive-clustered third pass; §C carries record-only. Per policy execution note 1, SDK-comparison findings default to cross-track/design-Q (no autonomous side-taking on spec-vs-SDK canon — the C22-M5/C50-B7 lesson).

---

## §A — Prior-Finding Verification (held / regressed)

Verdict summary: **7 of 7 HELD, 0 REGRESSED.** The §A clean property recovers after breaking at C50 (streak before the break: C40/C42/C44/C46/C48).

All line cites below are against today's checkout (head `958a5625`).

### C52-A1 — C17-H1 (SPARQL predicate typo): HELD

- L366: `web4:sourceDomain "medical" ;` — the one-character typo (`sourceDomai`) is fixed; predicate now matches the correctly-spelled `web4:targetDomain` on L367.
- Sweep: `sourceDomai\b` has zero hits in the spec corpus today.
- (The predicates themselves remain absent from the canonical ontology — that is deferred C17-M1, tracked in §C, not a regression of H1.)

### C52-A2 — C17-H2, rename half (`roleType` → `roleLCT`): HELD

- L418: `"roleLCT": "lct:web4:role:dictionary-translator:..."` with the inline non-normativity disclaimer (L419–420) referencing the deferred H2 role-value DESIGN-Q, exactly as #242 shipped it.
- `roleType` has zero hits in the target today. The known cross-doc residual (C17-INFO3: `mcp-protocol.md:306` stale `"roleType": "web4:Developer"`) is tracked in §C — re-verified still present today (`mcp-protocol.md` L306), unchanged by the C35 cycle.
- The role-VALUE question (whether `dictionary-translator` enters the SocietyRole enum, and its hyphen-vs-underscore form) remains an open DESIGN-Q (§C); the disclaimer comment keeps the spec honest meanwhile.

### C52-A3 — C17-M2 (`witness_attestation` → `witnesses`): HELD

- L274: `"witnesses": ["lct:web4:witness:domain-expert"]` — plural array-of-LCT-refs, corpus-canonical convention.
- `witness_attestation` has zero hits in the target today; the object-shaped `witness_attestation` record remains reserved by mcp-protocol/schema_registry as intended.

### C52-A4 — C17-M3 (`trust_requirements` outer-key disambiguation): HELD

- L67: §2.2 outer key is `dictionary_trust_config` ({minimum_t3, stake_required} — LCT-default-config scope).
- L189: §4.1 per-request override shape retains `trust_requirements` ({minimum_fidelity, require_witness, atp_stake}).
- The two-scope split #242 established is intact. **Cross-referential residue routed to §B**: §4.2 pseudocode (L206) reads `request.trust_requirements.minimum` and compares it against `dictionary.t3` — a field the disambiguated §4.1 shape does not define (its keys are `minimum_fidelity`/`require_witness`/`atp_stake`, none of them a T3 floor; the T3 floor lives in §2.2's `minimum_t3`). This incoherence is **pre-existing** (L206 is unchanged by #242 — verified in the diff), so it is NOT a remediation-introduced regression; but the M3 disambiguation made it *visible* that the pseudocode references a field from the wrong scope. Adversarially verified in §B (see C52-B2) rather than asserted here.

### C52-A5 — C17-M5 (`:v2` suffix drop): HELD

- L48: `"lct_id": "lct:web4:dictionary:medical-legal"` — no version suffix; the dedicated `"version": "2.3.1"` field (L54) is the sole version carrier.
- Sweep: `lct:web4:dictionary:*:v2`-shaped ids have zero hits in the target today. (Pre-existing `lct:web4:dict:` short-form ids elsewhere in the file are a separate fresh-finding candidate — §B, C52-B3 — not an M5 regression: M5's scope was the `:v2` suffix only.)

### C52-A6 — C17-L1 (bare thresholds → named constants): HELD

- L220: `if target_concepts.ambiguity > AMBIGUITY_GATE:` and L317: `if dictionary.changes > VERSION_BUMP_DELTA:` — both #242 constants present, UPPER_SNAKE_CASE per pseudocode convention.
- Bare `> threshold` has zero hits in the target today. (L246's literal `confidence < 0.95` was not in L1's scope — it is M6-adjacent threshold-semantics material, tracked in §C; a third-bare-threshold observation is evaluated fresh in §B.)

### C52-A7 — C17-L2 (§10.1 chain reshape to §4.3 mirror): HELD

- §10.1 (L499–521): `translation_chain[]` with `{step, from, to, dictionary, output, confidence, degradation}`, top-level `cumulative_degradation: 0.12` with arithmetic comment, full-LCT-form `witnesses` — exactly the #242 shape.
- Arithmetic re-verified: 1 − (0.94 × 0.94) = 0.1164 ≈ 0.12 ✓; §4.3's 1 − (0.95 × 0.92) = 0.126 ✓.
- Known deliberate asymmetries (no regression): §10.1 adds `output` (absent in §4.3 by design — §4.3 is the tracking record, §10.1 the worked example) and omits §4.3's `trust_acceptable`. Id-token consistency *between* the two mirrored examples (`lct:web4:dictionary:medical-insurance` vs `lct:web4:dict:med-legal`) is a fresh-finding candidate — §B (C52-B3).

### #242 regression sweep (cross-referential, all 7 hunks)

Each hunk was re-read in place and its inserted tokens traced to their cross-references:

1. **H1 hunk** (L366): inserted predicate matches L367's existing spelling; no new claims introduced. Clean.
2. **H2 hunk** (L418–420): inserted role-LCT value is explicitly disclaimed as illustrative; the disclaimer's pointer ("C17 audit H2 role-value DESIGN-Q") cites a real, still-open deferral. Clean.
3. **M2 hunk** (L274): inserted key matches the 7-file corpus convention; array shape preserved. Clean.
4. **M3 hunk** (L67): rename only; inner shape untouched. The §4.2 L206 incoherence it exposes is pre-existing (see C52-A4). Clean as a hunk.
5. **M5 hunk** (L48): id now matches the `lct:web4:dictionary:<pair>` long form used at L82–84/L163–165. Clean.
6. **L1 hunks** (L220, L317): constants introduced but (like the pre-existing `lossy_threshold`/`proposal_threshold` pattern they cite) given no defined values — consistent with pseudocode convention; no semantic claim added. Clean.
7. **L2 hunk** (§10.1): arithmetic verified above; inserted dictionary ids use the canonical long form; inserted witness LCTs match §4.3's form. Clean.

**No remediation-introduced defects found in #242.** Contrast with C50 (nine #252-introduced defects): #242 was a small (+28/−13), mechanically-scoped remediation whose inserted text makes almost no cross-referential claims — consistent with the C50 §D size-threshold lesson (+58-line remediations are where cross-referential risk concentrates).

---
