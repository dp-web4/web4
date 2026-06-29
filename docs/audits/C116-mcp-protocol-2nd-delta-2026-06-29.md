# C116 — `mcp-protocol.md` Second Delta Re-Audit

**Date**: 2026-06-29
**Auditor**: autonomous web4 session (legion, LEAD `120001`, C-series)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` (964 lines, 16 sections) + `web4-standard/MCP_ENTITY_SPECIFICATION.md` (408 lines, second B1 site)
**Instrument**: proportioned single-file re-read + corpus-delta diff + cross-section blindspot sweep → 1 adversarial verifier (refute-by-default) on the lone candidate. Not the C76 9-agent fan-out — the target is byte-frozen and the corpus delta is a single moved sibling (see Proportionality).
**Scope**: §A delta re-verification of **C76** (`docs/audits/C76-mcp-protocol-delta-audit-2026-06-19.md`) and its remediation **C77** (`f3d2613d`, PR #366, 8 autonomous findings). §B new findings since 2026-06-19.
**This audit recommends; it does not patch.** No spec text modified. One new file.

**Lineage**: C35 (first audit, 2026-06-06) → #279 (12 findings) → **C76** (first delta, #365, 2026-06-19) → **C77** (#366, `f3d2613d`, 2026-06-20, remediated 8 autonomous C76 findings) → **C116** (this audit).

---

## Headline

1. **C77 was a clean remediation by persistence.** Both target files are **byte-FROZEN since C77** (`f3d2613d`, 2026-06-20 — zero commits since). All 8 C77-applied C76 findings (B1+B11, B3, B4, B7, B8, B9, B10, N14) are present and un-regressed. Because no remediation has *landed* since C77, §A here is **persistence-by-byte-identity**, not a fresh fix-verification.

2. **One NET-NEW finding — N1 (LOW) — and it is a remediation-introduced regression.** The C77 fix for C76-**B4** (which correctly added the high-consequence witnessing MUST to §12 and a non-exhaustive preamble) **over-tightened clause (a)** of the new §12 MUST #6: it states witnessing as an *unconditional* MUST for all R7, where the body it cites (§7.5 item 4, §7.3) scopes mandatory witnessing to **high-consequence** actions only. The C76-B4 remediation request literally read "add the *high-consequence* witnessing MUST"; clause (a) dropped the qualifier. Adversarially verified REAL (severity deflated MED→LOW: the §12 preamble explicitly subordinates the summary to the sections, and the error is over-strict, not a safety gap). A textbook [[feedback_remediation_introduced_regression]] case — the exact class the prior fix's own cross-section reconciliation pass should have caught. → autonomous-actionable one-line fix, routed to the next mcp remediation turn (C117). NOT self-applied (read-only audit).

3. **The one moved sibling REINFORCES, it does not break.** Of every doc C76 cross-referenced, only `atp-adp-cycle.md` moved since C77 (C79, #368). Its C79-B7 edit added an **inbound** cross-reference pointing AT mcp §7.7 as the owner of referent-grounded cross-society exchange-rate negotiation. Verified bidirectionally consistent (atp-adp owns the ATP *form*; mcp §7.7 owns the *negotiation*), and the C76 "ATP-minting CONSISTENT" ruling HOLDS (C79-B5 still mints ADP, not ATP). INFO, no defect.

This is the **third confirmation** (after C108, C112, C114) that a byte-frozen 2nd-delta target is *not* presumed clean: the lone net-new finding came entirely from the cross-section blindspot sweep — the one discipline that section-anchored finders structurally cannot reproduce.

---

## Severity legend

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR a normative value/structure is rejected by the canonical taxonomy/SSOT. |
| **MEDIUM** | Normative guidance self-contradicts/ambiguous enough that two good-faith implementations diverge. |
| **LOW** | Maintainability / summary-precision / terminology hazard; recoverable by a careful reader; not a blocking contradiction. |
| **INFO** | Observation; recorded for completeness or to confirm a seam was inspected and found bounded. |

---

## §A — Delta re-verification of C76 (+ C77 remediation)

### A.1 — The 8 C77-applied findings (persistence by byte-identity)

Target byte-frozen since C77 → each edit verified present at its current line; no edit reverted, none introduced a stale mirror.

| C76 ID | Sev | Verdict | Current site | Evidence |
|--------|-----|---------|--------------|----------|
| **B1+B11** | HIGH | **HELD** | §3.1 L76 / §3.2 L100 / §8.2 L737 / note L113-119 | `entity_type` = `service` (server) / `ai` (client); SPARQL `?server a web4:Service`; added normative entity-type-grounding note ("`mcp_server`/`mcp_client` … MUST NOT be used"). **2nd site** `MCP_ENTITY_SPECIFICATION.md` L64/131/160/189 → `service`. |
| **B3** | MED | **HELD** | §7.3 L404-406 / L417 | reputation array renamed `witness_signatures`→`witnesses` with r7 canonical `{lct, signature, timestamp}` element shape; §7.3 bullet L417 cross-refs `r7-framework.md` §1.7. |
| **B4** | MED | **HELD** (but see §B/N1) | §12 L893-895 / L902 | §12 gained the non-exhaustive preamble + MUST #6 "R7 actions MUST be witnessed". *The fix landed — but clause (a) over-tightened; see N1.* |
| **B7** | LOW | **HELD** | §7.3 L414 | All four `outcome_class` values defined inline (`success`/`partial`/`failure`/`violation`); `partial` now has semantics. |
| **B8** | LOW | **HELD** | §9.1 L764-769 | `context.t3`→`t3_in_role`; "implementation-assembled aggregate" note added; `.average()` scoped to dimensions present. |
| **B9** | LOW | **HELD** | §7.4 L461 | orphan `responding_role_expected` now defined OPTIONAL/advisory with role-mismatch handling. |
| **B10** | LOW | **HELD** | §7.1 L339-346 | role-id field-name note harmonizing `sender_role`/`role_required`/`roleType` (+ `roleLCT` for concrete binding). |
| **N14** | LOW(opt) | **HELD** | §7.4 L470 | interim conformance note now cross-refs §7.7.1's stable design-invariant. |

**A.1 tally**: 8 HELD · 0 REVERTED · 0 regression from the edits themselves (the N1 over-statement is a *content* defect in the B4 edit, tracked in §B, not a reversion).

**Sub-observation (persisting, not net-new)**: `MCP_ENTITY_SPECIFICATION.md` L65 retains `entity_subtype: "database"` (and `subtype=` constructor args L131/160/189). C76-B1 flagged this parenthetically ("also adds a non-canonical `entity_subtype`"); C77 fixed the `entity_type` *values* but did not address the `subtype` field. Rides the B1 family — whether `subtype` is a sanctioned refinement of a taxonomy type is the open question. Minor; recorded for the B1 cross-track turn.

### A.2 — Deferred / cross-track clusters (siblings frozen → dispositions unchanged)

| C76 ID | Cluster | Verdict | Note |
|--------|---------|---------|------|
| **B2 + B6** | r7-reputation shape (V3-delta, `{change,from,to}`, `action_id`) | **STILL OPEN** | `r7-framework.md` frozen since C77 → no movement. Cross-track (r7 + mcp + SDK must agree on ONE reputation shape). B2's V3-omission remains load-bearing. |
| **B5 + B12** | registry-home for §7.6 `web4_cross_society_*` + §7.7.7 `web4_rate_*` | **STILL OPEN** | `registries/initial-registries.md` + `error-codes.md` frozen since C77. N4's resolution sanctions the *form*; only the *home* remains. |
| **N5 / N9 / N13** | §7.7 v0.1.0-final promotion wire-shape | **STILL OPEN (WIP-fenced)** | §7.7 byte-identical; resolve as ONE unit at promotion. *Newly reinforced*: atp-adp C79-B7 now names mcp §7.7 as the negotiation owner (§B). |
| **N12** | carry-C30 §10 JSON-RPC vs RFC-9457 error model | **STILL OPEN** | `errors.md` frozen; operator-scoped error-model decision. |
| **N15** | carry-C33 `lct:web4:` entity-vs-instance identifier | **STILL OPEN** | `data-formats.md` frozen; mcp remains a high-volume consumer awaiting canonical entity-id form. |
| **F5 / C62-B1** | `established`/`federated` interaction_type definition-site | **STILL OPEN** | `inter-society-protocol.md` frozen; relationship-state home unresolved. Surfaces at §7.3 L416 + §7.4 L436. |
| **F9-inverted** | corpus-wide `PolicyEntity`/`Policy-Entity`/`Policy` | **STILL OPEN** | mcp still uses `Policy-Entity` (§7.3 L413, §7.6 L524, §7.7.2 L574) — consistent with `society-roles.md`; do NOT single-file rename. Corpus-wide decision. |

---

## §B — New findings since 2026-06-19

Corpus-delta surface: **all** C76-referenced siblings frozen since C77 **except `atp-adp-cycle.md`** (C79, #368, `db394dfa`, 2026-06-20).

### B.1 — atp-adp inbound carry (C79-B7) — verified REINFORCING (INFO)

C79-B7 added to `atp-adp-cycle.md`:
- §5 inline note: *"Cross-society settlement is also governed by … `mcp-protocol.md` (the inter-society protocol; §7.7 covers cross-society exchange-rate negotiation)."*
- References block: *"`mcp-protocol.md` … §7.7 covers referent-grounded cross-society exchange-rate negotiation."*

Verdict: **bidirectionally consistent, reinforcing, no defect.** atp-adp now explicitly delegates *exchange-rate negotiation* to mcp §7.7 while retaining ownership of the ATP *form*; mcp §7.7.1 owns the referent-grounded negotiation model. The division is clean — no contradiction, no stale claim. Two minor INFO observations (recorded, not findings):
- atp-adp's inbound pointer lands a reader on mcp §7.7, which is **WIP v0.1.0-draft**. This is a known-deferred state (§7.7 self-labels WIP), not a net-new defect; it slightly raises the stakes on the N5/N9/N13 promotion cluster (an external doc now cites the WIP section as authoritative).
- mcp §7.7 does **not** carry a reciprocal back-citation to `atp-adp-cycle.md` (it cites `inter-society-protocol.md` §4 for sovereignty). Not a defect — the form/negotiation split is unambiguous — but a future §7.7 promotion editor MAY add the back-link for symmetry.

**C76 "ATP-minting CONSISTENT" ruling re-verified HELD**: C79-B5 harmonized `mint_adp` to the §3.1 nested-pool form but still mints **ADP** (not ATP); C79 touched no §7.1 MUST #5 / §2.1 minting-authority text that mcp's settlement-not-minting posture depends on. mcp §7.3/§7.7.2 "updates both societies' ATP accounts" remains settlement against pre-existing balances.

### B.2 — N1 (LOW, NET-NEW, remediation-introduced) — §12 MUST #6 clause (a) overstates the body's witnessing scope

| Field | Value |
|-------|-------|
| **Severity** | **LOW** (verifier-deflated from a MED ceiling) |
| **Actionability** | **autonomous** (single-file, one-line scope insertion; no design decision) |
| **Where** | §12 MUST #6 (L902) vs §7.5 item 4 (L499) + §7.3 (L417) |
| **Class** | remediation-introduced regression ([[feedback_remediation_introduced_regression]]); cross-section blindspot ([[feedback_auditor_blindspot_pattern]]) |

**Finding.** §12 MUST #6 reads:
> "6. R7 actions MUST be witnessed: an R7 transaction MUST NOT proceed without witnessing (§7.5), and for high-consequence actions the `reputation.witnesses` array MUST contain at least one Witness-role entry (§7.3)"

The qualifier "for high-consequence actions" attaches grammatically **only to clause (b)** (the `reputation.witnesses` array). Clause (a) — "an R7 transaction MUST NOT proceed without witnessing" — and the lead-in "R7 actions MUST be witnessed:" are **unconditional**, applying to ALL R7. But the two sections clause (a) cites both scope mandatory witnessing to **high-consequence** only:
- §7.5 item 4 (L499): *"low-consequence R6 calls MAY proceed without witnessing; **for high-consequence actions**, R7 MUST NOT proceed without witnessing"*
- §7.3 (L417): *"**For high-consequence actions** …, `reputation.witnesses` MUST contain at least one entry from a Witness role"*

A full sweep of §7 finds **no** statement that all R7 (regardless of consequence) must be witnessed. Because cross-society actions are **R7-by-default** (§7.3 L376) independent of consequence, the affected case — a low-consequence cross-society R7 — is reachable, not hypothetical. Such an action is conformant under §7.5/§7.3 but **non-conformant under §12 MUST #6**.

**Why this is a remediation-introduced regression.** C76-B4 found §12 *under-stated* witnessing (reduced it to a SHOULD) and its remediation request was explicitly "add the **high-consequence** witnessing MUST to §12." C77 added MUST #6 — clause (b) and the preamble correctly kept the high-consequence scope, but clause (a) over-corrected to unconditional. The fix swung from under- to over-statement on the same axis.

**Mitigation (why LOW, not MED).** The C77-added §12 preamble (L893-895) — *"not exhaustive — section-level requirements (notably the R7 normative requirements in §7.3/§7.5) govern in full"* — is a precedence clause naming the exact governing sections, so a reader who follows the pointer recovers the correct rule. But the preamble disclaims *omissions*, not *affirmative over-statements*; a MUST-list (whose purpose is a quick conformance checklist) that contradicts the section it summarizes is still a reader hazard. The error direction is **over-strict** (rejects valid low-consequence R7 traffic), not a safety/security gap.

**Recommended fix (routed, NOT applied).** Insert the scope qualifier into clause (a):
> "6. R7 actions MUST be witnessed: **for high-consequence actions,** an R7 transaction MUST NOT proceed without witnessing (§7.5), and the `reputation.witnesses` array MUST contain at least one Witness-role entry (§7.3)"

or otherwise word clause (a) to match §7.5's high-consequence scope. → next mcp remediation turn (C117).

**Inspected and bounded (refuted / consistent — recorded):**
- §7.6 `412 web4_cross_society_witness_required` ("Witness signature required but absent") — CONSISTENT and *corroborating*: this is the high-consequence enforcement path, not an all-R7 rule, matching §7.3/§7.5 (and against §12 clause (a)).
- §7.3 `violation` outcome (L419) vs §7.6 transport/protocol failure — CONSISTENT (§7.3 L419 explicitly distinguishes them).
- §7.3 L413 / §7.6 L524 Policy-Entity-signs-reputation — CONSISTENT (re-sign recovery matches signer).
- §9.1 metering `context` aggregate (B8 fix) — CONSISTENT; `t3_in_role.average()` scoped to present dimensions.

---

## §C — Routing for the remediation turn

### Autonomous-actionable (single-file, no design decision)
- **N1** — insert the high-consequence scope qualifier into §12 MUST #6 clause (a) so it matches §7.5/§7.3. One-line edit. Sequence at the next mcp remediation turn (C117). *(Verify against §7.5 item 4 + §7.3 L417 before applying.)*

### Cross-track / design-Q / WIP (do NOT self-resolve — all carried unchanged from C76)
- **B2 + B6** (r7-reputation shape) · **B5 + B12** (registry-home) · **N5/N9/N13** (§7.7 promotion — now reinforced by atp-adp C79-B7) · **N12** (§10 error model) · **N15** (`lct:web4:` identifier) · **F5/C62-B1** (interaction_type home) · **F9-inverted** (corpus-wide PolicyEntity form). See `carries.md`.
- **B1-family sub-item**: `MCP_ENTITY_SPECIFICATION.md` `entity_subtype`/`subtype` canonicity (taxonomy refinement question).

### Confirmed-bounded (no action)
- atp-adp C79-B7 inbound carry — reinforcing; C76 ATP-minting-CONSISTENT ruling HELD.

---

## Out of scope (handed off, not closed here)

- SDK-vs-spec conformance of §7 behavior (separate SDK-alignment track).
- §7.7 promotion to v0.1.0-final (operator/fleet-review gated); N5/N9/N13 + the new atp-adp inbound citation are inputs.
- Corpus-wide PolicyEntity-form decision (F9-inverted) and the C62-B1 relationship-state-home decision.
- `inter-society-protocol.md`, `r7-framework.md`, `errors.md`, `entity-types.md`, `atp-adp-cycle.md`, registries — cited as mirror references only; not re-audited (atp-adp inspected solely for its inbound carry to mcp §7.7).

---

*Second delta re-audit. No spec text modified. No SDK or test code touched. One new file. Frozen target (both files byte-stable since C77 `f3d2613d`) + single moved sibling → proportioned to a re-read + blindspot sweep + 1 adversarial verifier, not the C76 9-agent fan-out. Third confirmation (C108/C112/C114) that frozen ≠ clean: the lone net-new finding (N1) came entirely from the cross-section blindspot sweep, and is itself a [[feedback_remediation_introduced_regression]] mirror — the C77 fix for B4 over-tightened clause (a). See [[feedback_audit_workflow_adversarial_verify]], [[feedback_cross_doc_carry_inbound]].*
