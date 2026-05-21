# C6: `inter-society-protocol.md` Internal Consistency Audit

**Date**: 2026-05-21
**Track**: web4 (Legion autonomous session)
**Instrument**: Same as C2 (mcp-protocol.md, 2026-05-15) and C5 (presence-protocol.md, 2026-05-17)
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2, 372 lines, stable since 2026-05-14)
**Cross-referenced**: `SOCIETY_SPECIFICATION.md`, `atp-adp-cycle.md`, `LCT-linked-context-token.md`, `r6-framework.md`, `r7-framework.md`, `mcp-protocol.md`, `society-roles.md`

---

## Purpose

Read `inter-society-protocol.md` end-to-end and surface internal inconsistencies, cross-reference failures, and structural gaps. This is the third core-spec internal consistency audit using the C-series instrument (C2 covered `mcp-protocol.md`, C5 covered `presence-protocol.md`). The document has been stable at v0.1.2 for 7 days (no commits since 2f4454f5, 2026-05-13).

## Summary

| Severity | Count |
|----------|------:|
| HIGH | 3 |
| MEDIUM | 5 |
| LOW | 5 |
| **Total** | **13** |

Finding count matches both C2 and C5 (13 each) — likely coincidental, but the consistency of the instrument is notable.

---

## HIGH Findings

### H1: Duplicate section numbering in §4

**Lines affected**: 194, 211, 222, 228

§4 "ATP Reification Sovereignty" has duplicate subsection numbers:

| Position | Current Number | Title |
|----------|---------------|-------|
| Line 183 | §4.1 | What ATP Is (and What It Is Not) |
| Line 194 | **§4.2** | Form vs. Substance |
| Line 211 | **§4.3** | Commitment vs. Record |
| Line 222 | **§4.2** ← duplicate | Implication for Cross-Society Exchange |
| Line 228 | **§4.3** ← duplicate | "First ATP" Resolution |
| Line 236 | §4.4 | Resource Measurement and Attestation |
| Line 249 | §4.5 | ATP/ADP Policy Examples |

The second §4.2 and §4.3 shadow the first. Correct numbering should be §4.1 through §4.7. This breaks all internal and external cross-references to §4.x subsections — notably, `society-roles.md` line 206 references "§4.4 for inter-society witnessing," which currently points to "Resource Measurement and Attestation" but would point to a different section after renumbering.

**Remediation**: Renumber §4 subsections sequentially (§4.1–§4.7). Audit all external references to `inter-society-protocol.md` §4.x (at minimum: `society-roles.md` line 206, `mcp-protocol.md` lines 523 and 646).

### H2: Header version stale (v0.1.0 vs actual v0.1.2)

**Line affected**: 3

The header reads:
```
**Status**: Core Specification v0.1.0 (DRAFT)
**Date**: 2026-05-13
```

Git history shows two post-v0.1.0 amendments:
- v0.1.1 (f4803dde, 2026-05-13): incorporated Kimi round-3 sharpenings
- v0.1.2 (2f4454f5, 2026-05-13): fixed R6-only to R6/R7 throughout

The document's content reflects v0.1.2 changes (R7 references present throughout §8) but the header was never updated. This makes the document's self-reported version unreliable.

**Remediation**: Update header to `v0.1.2 (DRAFT)` and date to `2026-05-13` (same day, but version is the actionable field). Consider adding a version history section or CHANGELOG entry.

### H3: §8 Relationship table omits `mcp-protocol.md`

**Line affected**: 348–357

The §8 "Relationship to Other Specs" table lists 7 companion specs but omits `mcp-protocol.md`, despite:
- §9 citing `mcp-protocol.md` §7.3, §7.4, §7.5, §7.6, §7.7 as the resolution mechanism for three former future-work items
- `mcp-protocol.md` referencing `inter-society-protocol.md` at 7 locations (lines 36, 443, 446, 495, 501, 523, 646)
- `mcp-protocol.md` §1.1 explicitly stating "MCP IS the inter-society protocol" per the canonical equation

This is the document's most important cross-reference and it's missing from the summary table.

**Remediation**: Add `mcp-protocol.md` row to §8 table. Suggested description: "MCP is the inter-society action protocol per the canonical Web4 equation. This spec defines genesis/first-contact/secession; mcp-protocol.md §7.3–§7.6 specifies R6/R7 actions between societies via MCP. §7.7 (WIP) specifies referent-grounded exchange rate negotiation."

---

## MEDIUM Findings

### M1: §2.1 contains two wrong internal cross-references

**Lines affected**: 72, 75

The §2.1 "Self-Bootstrapped Genesis" protocol contains two cross-reference errors in the genesis steps:

| Line | Current Reference | Correct Reference | Reason |
|------|------------------|-------------------|--------|
| 72 | "per §6" | "per §7" | §6 is "Minimum Viable Society"; §7 is "Ledger Anchoring (Cross-Reference)" which discusses ledger choice |
| 75 | "see §4 on minimum viable society" | "see §6 on minimum viable society" | §4 is "ATP Reification Sovereignty"; §6 is "Minimum Viable Society" |

Both errors are in the foundational genesis protocol — the document's most operationally important section. The pattern (off-by-one and off-by-two in the same code block) suggests section renumbering occurred without a cross-reference audit.

**Remediation**: Fix both references. Then audit all other internal `§N` references (there are 20+ throughout the document) for similar drift.

### M2: §9 RESOLVED items cite mcp-protocol.md versions without explicit disambiguation

**Lines affected**: 363–365

Three §9 "Future Work" items are struck through as RESOLVED, citing version numbers:
- "RESOLVED v0.1.3 (2026-05-14)"
- "RESOLVED v0.1.3 (2026-05-14)"
- "RESOLVED v0.1.4 (2026-05-14, WIP)"

These are `mcp-protocol.md` version numbers, but a reader seeing "v0.1.3" in a document whose header says "v0.1.0" (or should say v0.1.2 per H2) will reasonably wonder whether these are inter-society-protocol.md versions. The text body does say "See `mcp-protocol.md` §7.x" but the version number lacks explicit qualification.

**Remediation**: Change each occurrence to include the document name in the version reference, e.g., "RESOLVED — `mcp-protocol.md` v0.1.3 (2026-05-14)".

### M3: §8 Relationship table omits `society-roles.md`

**Line affected**: 348–357

`society-roles.md` lists `inter-society-protocol.md` as a companion document (line 7) and references specific sections:
- Line 206: "See `inter-society-protocol.md` §4.4 for inter-society witnessing"
- Line 363: "Inter-society interactions reference the Diplomat role; cross-society R7 actions reference the Witness role"

`inter-society-protocol.md` §6.2 discusses role differentiation as a semantic viability requirement. Yet `society-roles.md` is not in the §8 relationship table.

**Remediation**: Add `society-roles.md` row to §8 table. Note the bidirectional dependency: society-roles.md defines roles (including Diplomat) that inter-society interactions require; inter-society-protocol.md defines the semantic viability criteria that constrain role composition.

### M4: "The existing spec requires ≥3 birth witnesses" — vague source attribution

**Line affected**: 83

The note reads: "The existing spec requires ≥3 birth witnesses." This requirement comes from `LCT-linked-context-token.md` line 200 ("Records birth_witnesses (minimum 3)"), not from `SOCIETY_SPECIFICATION.md`. The vague "existing spec" phrasing is ambiguous in a document that extends multiple specs.

**Remediation**: Change to "per `LCT-linked-context-token.md` (minimum 3 birth witnesses)" or cite the specific section.

### M5: `AttestationEnvelope` reference is a dangling cross-reference

**Line affected**: 245

The text reads: "The `AttestationEnvelope` primitive (see related work) provides one cross-platform interface." The phrase "(see related work)" implies there is a document to follow, but:
- There is no `attestation-envelope.md` in `web4-standard/core-spec/`
- `AttestationEnvelope` is defined in the Python SDK (`web4/attestation.py`) and has a JSON Schema (`schemas/attestation-envelope.schema.json`), but no core-spec document
- No other core-spec document in the directory defines or specifies AttestationEnvelope

**Remediation**: Either create a stub core-spec document for AttestationEnvelope (out of scope for this audit), or change the reference to cite the specific implementation location: "The `AttestationEnvelope` primitive (see `schemas/attestation-envelope.schema.json` and the SDK's `web4/attestation.py`)".

---

## LOW Findings

### L1: §1.3 Eurozone exit analogy is misleading

**Line affected**: 43

"Eurozone (members chose to join EUR; can theoretically exit, see Greek debt crisis 2015, Brexit 2020)"

Two issues:
1. **Greece did not exit the Eurozone.** The 2015 crisis ended with Greece remaining in the Eurozone under a third bailout program. Using it as an example of exit capability is misleading.
2. **Brexit was an EU exit, not a Eurozone exit.** The UK was never in the Eurozone (it retained GBP). The parenthetical conflates EU membership with Eurozone membership.

The underlying point (consent-based membership with exit rights) is valid and well-argued in the surrounding text.

**Remediation**: Either remove the parenthetical examples or replace with more precise ones. For Eurozone specifically, no member state has ever actually exited — the theoretical exit right exists but is untested. For EU exit, "Brexit 2020" is correct.

### L2: §4.1 "Gesellian economic experiment" is niche terminology

**Line affected**: 191

"Demurrage in the Web4 context is 'expiration of resource allocations,' not a Gesellian economic experiment."

While technically accurate (Silvio Gesell proposed demurrage currencies in 1916), this reference may be opaque to most technical readers without economic-theory background. Not an internal consistency issue; flagged as a readability note.

### L3: Cross-spec gap — `society-roles.md` expects Diplomat role reference in this document

**Line affected**: N/A (absence)

`society-roles.md` line 363 asserts: "Inter-society interactions reference the Diplomat role; cross-society R7 actions reference the Witness role." However, `inter-society-protocol.md` never mentions the "Diplomat" role. The Diplomat / Federation-Representative role is defined in `society-roles.md` §Diplomat (line 230) as the role that fills inter-society representation, but the inter-society protocol itself does not reference it.

This finding belongs primarily to a `society-roles.md` audit (the assertion is there), but is surfaced here because the audit's cross-referencing scope includes bidirectional consistency.

**Remediation**: Either add a reference to the Diplomat role in `inter-society-protocol.md` §3 (first-contact) or §2.2 (federation genesis, where "delegated representatives" is the equivalent concept), or correct `society-roles.md` line 363's assertion.

### L4: §2.2 "birth certificates" is undefined terminology

**Line affected**: 104

"D SHALL issue birth certificates to A, B, [C, ...] as constituent societies"

The term "birth certificates" is not defined in the glossary (`whitepaper/sections/02-glossary/`), not used in `LCT-linked-context-token.md`, and not used in §2.1 for the equivalent step in solo genesis. Solo genesis (§2.1) describes "minting the society LCT" (step 5); federation genesis (§2.2) uses "birth certificates" — different terminology for what appears to be the same operation.

**Remediation**: Either define "birth certificate" as a term (perhaps an LCT minting event recorded on a federation ledger), or align with §2.1's "mint" terminology for consistency.

### L5: §3.2 Option 1 — ANCHORED capitalization implies normative force without RFC 2119 framing

**Line affected**: 141

"Exchange transactions are witnessed by both societies and ANCHORED in both ledgers."

The capitalization of "ANCHORED" follows the RFC 2119 convention (like MUST, SHALL, MAY) but is not an RFC 2119 keyword. The surrounding text uses standard RFC 2119 terms (SHALL, MAY, SHOULD) correctly. Mixed use of capitalization — RFC 2119 keywords alongside non-standard capitalized emphasis — weakens the normative precision of the document.

**Remediation**: If the dual-ledger anchoring is a normative requirement, rephrase as "Exchange transactions SHALL be witnessed by both societies and anchored in both ledgers." If emphasis only, lowercase "anchored."

---

## Cross-Cutting Observations

### Observation 1: Section §4 is the structural weak point

Three of 13 findings (H1, M1-line-75, and the duplicate numbering's cascading effects on external references) center on §4 "ATP Reification Sovereignty." This section is the document's longest (lines 178–261, 83 lines) and most conceptually dense. The duplicate numbering suggests it was assembled from two separately-drafted subsection sequences that were merged without renumbering. The cross-reference errors in §2.1 (which point to wrong sections in §4 and §6's vicinity) support the hypothesis of a late structural reorganization.

### Observation 2: §9 Future Work is doing double duty as a cross-spec resolution log

Three of the six §9 items are struck-through RESOLVED entries that function as a changelog linking this document's evolution to `mcp-protocol.md`'s evolution. This is useful metadata but places resolution records (which age) alongside open future-work items (which are forward-looking). As the spec matures, §9 will accumulate resolved items that provide historical context but dilute the future-work signal. Consider splitting into §9 "Resolved Dependencies" and §10 "Future Work" in a future revision.

### Observation 3: The document is architecturally sound

Despite 13 findings, none challenge the document's conceptual architecture. The anti-hierarchical-by-design property (§1.3), the form/substance distinction (§4), the three sovereign options for first-contact (§3.2), and the semantic minimum viable society (§6) are internally coherent and well-argued. The findings are structural/editorial (numbering, cross-references, missing table entries) rather than conceptual. This contrasts with C2 (mcp-protocol.md) where 4 of 13 findings were HIGH conceptual gaps in §7.4↔§7.7.

### Observation 4: Instrument comparison across C2/C5/C6

| Property | C2 (mcp-protocol) | C5 (presence-protocol) | C6 (inter-society) |
|----------|-------------------|----------------------|-------------------|
| Findings | 13 | 13 | 13 |
| HIGH | 4 | 2 | 3 |
| MEDIUM | 5 | 6 | 5 |
| LOW | 4 | 5 | 5 |
| Document age at audit | ~6 months | ~1 day | 7 days |
| Lines | ~670 | ~400 | 372 |
| Conceptual HIGHs | 4 (§7.4↔§7.7) | 1 (§3.1 contradicts schemas) | 0 |
| Structural HIGHs | 0 | 1 (casing authority) | 3 (numbering, version, table) |

The inter-society-protocol.md is conceptually clean but structurally rough — the inverse of the C2 finding pattern. This suggests different authoring modes: `mcp-protocol.md` was structurally careful but had conceptual gaps from evolving requirements, while `inter-society-protocol.md` was conceptually thorough but structurally hasty (authored in a single day across 3 versions).

---

## Remediation Priority

### Group 1 — Structural numbering (H1 + M1): Fix first

Renumber §4 subsections and fix the two wrong cross-references in §2.1. These affect all downstream cross-reference work.

### Group 2 — Table completeness (H3 + M3): Fix second

Add `mcp-protocol.md` and `society-roles.md` to §8 relationship table. These are factual additions with no design decisions needed.

### Group 3 — Version and attribution (H2 + M2 + M4): Fix third

Update header version, disambiguate §9 version references, and make the ≥3 witness source explicit. Pure editorial.

### Group 4 — Dangling references and terminology (M5 + L3 + L4 + L5): Fix last or defer

These require minor decisions (where to point the AttestationEnvelope reference, whether to add Diplomat role mention, whether to define "birth certificate" or align terminology). Low urgency.

### Group 5 — Informational (L1 + L2): Low priority

Analogy precision and readability notes. Fix when convenient.

---

*Audit classifies; it does not remediate. Downstream PRs consume this classification.*
