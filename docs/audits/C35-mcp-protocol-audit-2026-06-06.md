# C35 — `mcp-protocol.md` Delta Re-Audit

**Date**: 2026-06-06
**Auditor**: autonomous web4 session (legion, LEAD `120050`, C-series)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` (current: 922 lines, 16 sections)
**Instrument**: multi-agent refute-by-default workflow — 5 finders (2× §A delta-split, 2× §B internal-consistency lenses, 1× §B cross-spec) → 10 adversarial verifiers (refute-by-default). 22 agents total.
**Scope**: Internal-consistency + cross-spec delta re-audit. Two parts:
- **§A** — delta re-verification of the 2026-05-15 internal-consistency audit's 16 findings (F1–F16, incl. 5 HIGH). That audit explicitly did NOT patch; this re-verifies which findings the subsequent (2026-05-17) editorial pass resolved vs. which still hold.
- **§B** — NEW findings since 2026-05-15 (internal-consistency + cross-spec drift vs the now-mature C21–C34 corpus).

This audit **recommends; it does not patch**. No spec text was modified. One new file.

**Predecessor**: `docs/audits/mcp-protocol-internal-consistency-2026-05-15.md` (16 findings, never remediated as a dedicated PR; the file received an editorial reconciliation pass on 2026-05-17).

---

## Headline

The **2026-05-17 editorial pass silently remediated 9 of the 16 prior findings, including 6 of the 7 HIGH findings** (the entire §7.4↔§7.7 settlement-seam cluster F2/F3/F4 + the §4.1 header-reconciliation F8 + the §7.7-status F12, plus the §7.3 `violation`-handling F15). The `exchange_rate` scalar/denominator shape the prior audit's HIGH cluster targeted **no longer exists** — §7.4 now carries the referent-grounded dual-valuation `atp_settlement` block, an explicit interim-conformance note scoping its MUST to *presence*, a §4.1↔§7.4 field-reconciliation subsection, a §7.6↔§7.7.7 error-precedence paragraph, and a per-subsection conformance-status map for §7.7. This is the most-remediated delta re-audit in the C-series to date.

What **remains live** is concentrated in two clusters:
1. **The §7.4 ↔ §7.7.3 wire-shape seam** — the referent-grounded model is now *consistent in intent* but the two JSON examples that cross-reference each other (`atp_settlement` vs `rate_accept`) use **divergent field names/structure** (`caller_amount` vs `agreed_rate_caller_atp.{amount,per_unit}`; `quantity` vs `reference_standard`; no signer-binding on the inline form). All are explicitly fenced by the §7.7 WIP / Normative-draft tags, so they are **design-Q coupled to §7.7 v0.1.0-final promotion**, not present-state defects against a stable rule.
2. **A spread of mechanical hygiene gaps** newly surfaced — role-identifier form drift (`web4:Name` vs `web4:role:name`), an orphan `exchange_agreement_hash` field, two session-id schemes, two pseudocode field-path errors, and the standing **carry-C34 line-107 V3 `value`→`valuation`** drift (now CONFIRMED).

---

## Severity legend

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR two normative passages specify structurally incompatible wire data. |
| **MEDIUM** | Normative guidance is self-contradicting/ambiguous enough that two good-faith implementations would diverge. |
| **LOW** | Maintainability / terminology / illustrative-example hazard; not a blocking contradiction. |
| **INFO** | Observation, recorded for completeness or to confirm a seam was inspected and found bounded. |

---

## §A — Delta re-verification of the 2026-05-15 findings (F1–F16)

| ID | Prior sev | Verdict | Where | One-line |
|----|-----------|---------|-------|----------|
| F1 | MED | **SUPERSEDED** | Overview L5 | Overview now states inter-society = primary use case, intra-society = special case. |
| F2 | HIGH | **SUPERSEDED** | §7.4 L447–451 | MUST now scoped to block *presence*; interim note reconciles with §7.7 WIP. |
| F3 | HIGH | **SUPERSEDED** | §7.4 L420–432 | Scalar `exchange_rate` gone; now referent-grounded dual valuation (the §7.7.1 model). |
| F4 | HIGH | **SUPERSEDED** | §7.4 L420–432 | `atp_settlement` now has `referent` + per-society `caller_amount`/`responder_amount`. |
| F5 | MED | **SUPERSEDED** | §7.6 L508 | New paragraph states §7.7.7 codes *refine* §7.6's `exchange_invalid`; precedence given. |
| F6 | MED | **PARTIAL** | §7.3 L386 / §7.5 L487 | `propagation_scope` still single-enum; `both` covers the case, residual is prose wording only → LOW. |
| F7 | MED | **HOLD** | §7.3 L397 / §7.5 L489 | Default scope not `interaction_type`-aware: federated defaults to `both` but §7.5 calls `encompassing_society` the federation standard. |
| F8 | HIGH | **SUPERSEDED** | §7.4 L453–469 | New "Relationship to §4.1" block reconciles `sender_society`↔`society` and `agency_chain`↔`proof_of_agency`. |
| F9 | LOW | **HOLD** | L394/400/505 | Hyphenated `Policy-Entity` still diverges from canonical `PolicyEntity`/`PolicyGate`. |
| F10 | LOW | **HOLD** | §7.6 L503 | Law-conflict recovery still presupposes an encompassing society; no-encompassing case unhandled. |
| F11 | MED | **PARTIAL** | §7.4 / §7.7.2/7.7.3 | Settlement values now traceable to a signed §7.7.3 acceptance by reference, but §7.4 block still names no signer for itself (see §B-N13). |
| F12 | HIGH | **SUPERSEDED** | §7.7 L512–521 | New per-subsection conformance-status map resolves the undeterminable RFC2119 force. |
| F13 | LOW | **HOLD** | §7.7.1/7.7.5/7.7.6 | Per-transaction/standing/oracle guidance still triplicated across three subsections. |
| F14 | LOW | **REFUTED** | L495 ↔ ISP §9 | Cross-doc claim verified TRUE: ISP §9 reciprocally strikes "society-society trust tensors → RESOLVED → §7.5". No defect. |
| F15 | MED | **SUPERSEDED** | §7.3 L400 | New paragraph fully specifies `violation` propagation (non-positive deltas, still signed, Archivist-persisted, ≠ §7.6 failure). |
| F16 | LOW | **SUPERSEDED** | §9.2 L744–749 | New prose makes §9.1 the canonical formula; §9.2's `0.8` framed as its max-trust endpoint. |

**§A tally**: 9 SUPERSEDED · 4 HOLD (F7 MED, F9/F10/F13 LOW) · 2 PARTIAL (F6 LOW, F11 MED) · 1 REFUTED. **6 of 7 HIGHs resolved**; the lone non-superseded HIGH (F11) deflates to a PARTIAL/MEDIUM (signer-binding, now §B-N13). No prior finding was found to have *regressed*.

---

## §B — New findings since 2026-05-15

14 unique confirmed findings (after dedupe of the witnessing finding, independently surfaced by two finders). 1 cross-doc verification candidate was correctly refuted (= the §A F14 consistency confirmation). Severity reflects the post-adversarial-verify deflation.

| # | Sev | Actionability | Where | Finding |
|---|-----|---------------|-------|---------|
| N1 | MED | autonomous-actionable * | §7.3 L398 vs §7.5 L480 | High-consequence R7 witnessing is **MUST** in §7.3 but defeasible **SHOULD NOT-proceed-without** in §7.5 — conflicting RFC2119 strength for the same condition. |
| N2 | MED | autonomous-actionable | §4.1 L129 / §6.1 L243 / §7.1 L306 vs §7.4 L413/415 | Role identifiers use two forms: canonical `web4:<Name>` vs §7.4's `web4:role:<name>` infix (the infix appears ONLY at L413/415 in the entire tree). Same `sender_role` field rendered two ways. |
| N3 | MED | autonomous-actionable (cross-spec-confirmed) | L107 | **carry-C34 CONFIRMED**: V3 dimension `value` should be `valuation` (siblings `veracity`/`validity` correct). Identical single-token drift fixed in atp-adp under C34 M1 (PR #277). |
| N4 | MED | cross-spec → operator | §7.6 L499–508 / §7.7.7 L677–685 vs `errors.md` L9 | MCP cross-society error codes use HTTP-prefixed `web4_*` strings, not the `W4_ERR_*` form `errors.md` (the declared SSOT, which names §7.6 by number) requires; no cross-reference. Couples carry-C30 error-canonicity DESIGN-Q. |
| N5 | MED | design-Q (§7.7-coupled) | §7.4 L421–431 / L449 vs §7.7.3 L629–631 | Inline `atp_settlement` field set (`caller_amount` flat) does not match the §7.7.3 `rate_accept` payload it cites (`agreed_rate_caller_atp.{amount,per_unit}`; no per-side currency). No reconciliation table (unlike the §4.1 one). |
| N6 | LOW | autonomous-actionable | §7.7 L519 vs §7.7.5 L667 | §7.7.5 is tagged **Informative ("no conformance requirements")** yet contains a normative `SHOULD`/`MAY` + a "24h default" termination constant. |
| N7 | LOW | autonomous-actionable | §6.3 L274 vs §11 L825/847 | Two session-identifier schemes in one doc: `sess:...` (§6.3) vs `mcp:session:...` (§11). Local to this file (not the C33 LCT/W4ID cluster). |
| N8 | LOW | autonomous-actionable | §7.4 L418 vs L431/448 | Orphan `exchange_agreement_hash` (cross_society level) is never defined by any normative bullet; only `exchange_agreement_ref` (nested) is. Implementer cannot disambiguate. |
| N9 | LOW | design-Q (§7.7-coupled) | §7.4 L425–430 vs §7.7.3 L588–593 | `referent` object has divergent shapes: cross-society envelope bundles `quantity`; §7.7.3 carries `reference_standard` (no `quantity`, amount externalized to `rate.per_unit_of_referent`). |
| N10 | LOW | autonomous-actionable | §4.1 L130–132 vs §4.2 L160 | §4.2 pseudocode reads `web4_context.atp_stake` (top-level) but the header nests it at `trust_context.atp_stake` (and L156 of the same pseudocode accesses `trust_context` correctly). |
| N11 | LOW | autonomous-actionable | §9.1 L739 | Metering pseudocode caps on `context.atp_cap` — a field defined in NO context/header/session schema (§11 uses `atp_remaining`). |
| N12 | LOW | cross-spec → operator | §10.1 L773–791 / §10.2 L795–813 vs `errors.md` §1 | §10 error model is JSON-RPC numeric (`-32001`) + Python exception classes, disjoint from the RFC 9457 `problem+json` / `W4_ERR_*` model; also internally divergent from §7.6's `web4_*` strings. Couples carry-C30. |
| N13 | INFO | design-Q (§7.7-coupled) | §7.4 L420–432 vs §7.7.3 L630–634 | Inline `atp_settlement` carries an agreed amount with no signer/acceptance-binding, unlike the `accepting_treasurer`-signed §7.7.3 acceptance it mirrors. (= deflated §A-F11; non-repudiation gap, but §7.7-WIP-fenced.) |
| N14 | INFO | autonomous-actionable (optional) | §7.4 L447 / L451 / §7.7 L512 | §7.4's MUST elaborates its content "per §7.7's referent-grounded model" (WIP), but §7.7.1 is itself marked Normative design-invariant and L451 scopes the MUST to presence. Seam inspected; bounded. Optional inline cross-ref L451←L447. |
| N15 | INFO | design-Q → carry-C33 | pervasive `lct:web4:...` | mcp uses `lct:web4:` to name **entities** (client/agent/society), but `data-formats.md` §1.3 says `lct:web4:` is the LCT *instance* id and entities take `did:web4:`. Recorded, NOT resolved — folds into the operator-only carry-C33 identifier-scheme decision (mcp is a 635-occ-class high-volume consumer). |

\* **N1 reconciliation direction is a soft design call.** One verifier classed it design-Q (hard-MUST-refusal vs defeasible-SHOULD-NOT is an enforcement-posture choice); the other classed it autonomous-actionable (§7.3 is the canonical "Normative requirements" list and already commits to MUST, so aligning §7.5 L480 to "MUST NOT proceed without" is a one-keyword fix). Lean: **autonomous-actionable toward §7.3's MUST**, since §7.3 owns the normative-requirements block — but a remediator should note the alternative softening path for operator visibility.

---

## Actionability breakdown (for the remediation turn)

**Autonomous-actionable NEW (mechanical, no design decision)** — 8:
- **N3** (L107 `value`→`valuation`) — the carry-C34 fix; identical to C34 M1.
- **N2** (role-id form: rename §7.4 L413/415 `web4:role:` → `web4:<Name>` to match corpus).
- **N6** (§7.7.5: restate `SHOULD`/`MAY`/24h as non-normative so the Informative tag holds).
- **N7** (session-id: standardize on `mcp:session:`, fix §6.3 L274, or add alias note).
- **N8** (delete orphan `exchange_agreement_hash` L418, or define + relate it to `_ref`).
- **N10** (fix §4.2 L160 to `web4_context.trust_context.atp_stake`).
- **N11** (bind §9.1 L739 `atp_cap` to a defined field, e.g. session `atp_remaining`).
- **N1** (lean: align §7.5 L480 to §7.3's MUST) — *flag the softening alternative*.
- **N14** (optional: inline cross-ref §7.4 L451 from L447).

**Autonomous-actionable from §A holds** — 4:
- **F9** (normalize `Policy-Entity` → `PolicyEntity`, 3 occurrences).
- **F10** (split §7.6 law-conflict recovery by whether an encompassing society exists).
- **F13** (make §7.7.5/§7.7.6 reference §7.7.1's per-transaction/standing/oracle statement rather than restate).
- **F6** (reword §7.5 L487 "combined with both" against the single-enum, or note `both` is the combined value).
- **F7** (MED): make §7.3 default `interaction_type`-aware OR soften §7.5's federation "standard" to "recommended, overriding the §7.3 default when `federated`") — borderline; bounded normative reconciliation, no new behavior.

**Design-Q / operator-coupled (do NOT self-resolve)** — couple to two existing operator decisions:
- **§7.7 v0.1.0-final promotion cluster**: N5, N9, N13 (and the residual of F11). All are the same wire-shape reconciliation between the `atp_settlement` envelope and the §7.7.3 `rate_accept` payload; the spec itself fences them as WIP/Normative-draft. Resolve as ONE unit at §7.7 promotion — do not patch piecemeal (re-introduces the inconsistency the 2026-05-17 pass just cleared).
- **carry-C30 error-canonicity DESIGN-Q**: N4 + N12 (numeric-vs-string error canonicity + `W4_ERR_*`/RFC-9457 adoption). `errors.md` already names MCP §7.6 as an extending subsystem; the taxonomy-form question is operator-scoped.
- **carry-C33 identifier-scheme DESIGN-Q**: N15 (`lct:web4:` entity-vs-instance). mcp is a high-volume consumer that will need a sweep once the operator picks the canonical entity-id form.

---

## Recommended sequencing (for a future remediation pass)

1. **N3** alone first — the carry-C34 single-token fix; closes a standing cross-track carry, zero risk.
2. **N2 + N7 + N8 + N10 + N11 + F9** — the mechanical hygiene batch (identifier forms, orphan field, pseudocode paths, terminology). All single-file, no design input.
3. **N6 + F13 + F6** — §7.7 informative/normative tagging + duplication + prose cleanup (still mechanical; touch §7.7 carefully given its WIP status).
4. **N1 + F10 + F7** — the normative-strength/recovery reconciliations (bounded but RFC2119-bearing; remediator states the direction chosen and why).
5. **DEFER as a unit to §7.7 promotion**: N5 + N9 + N13 + F11-residual (operator/design).
6. **DEFER to operator**: N4 + N12 (→ carry-C30) and N15 (→ carry-C33).

---

## Out of scope (handed off, not closed here)

- SDK-vs-spec conformance of any §7 behavior (the separate SDK-alignment track; prior `mcp-protocol-sdk-alignment-2026-05-15.md`).
- §7.7 promotion to v0.1.0-final (operator-blocked); N5/N9/N13/F11 are *inputs* to it.
- The carry-C30 error-canonicity and carry-C33 identifier-scheme operator DESIGN-Qs — recorded here as N4/N12 and N15, NOT resolved.

---

*Delta re-audit only. No spec text modified. No SDK or test code touched. One new file. Instrument: multi-agent refute-by-default workflow (22 agents); see `[[feedback_audit_workflow_adversarial_verify]]`.*
