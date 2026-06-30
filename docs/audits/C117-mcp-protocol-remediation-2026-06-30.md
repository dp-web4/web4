# C117 — `mcp-protocol.md` Remediation (applies C116-N1)

**Date**: 2026-06-30
**Author**: autonomous web4 session (legion, LEAD `000036`, C-series)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` §12 "MUST Requirements" item #6
**Type**: REMEDIATION (alternation turn following C120 AUDIT)
**Applies**: finding **C116-N1** from `docs/audits/C116-mcp-protocol-2nd-delta-2026-06-29.md` §B.2 / §C
**Lineage**: C35 (#279) → C76 (#365) → C77 (#366, `f3d2613d`) → **C116** (#406, audit) → **C117** (this remediation)

---

## What was wrong (C116-N1, LOW, remediation-introduced regression)

§12 MUST #6 read:

> 6. R7 actions MUST be witnessed: an R7 transaction MUST NOT proceed without witnessing (§7.5), and **for high-consequence actions** the `reputation.witnesses` array MUST contain at least one Witness-role entry (§7.3)

The qualifier "for high-consequence actions" attached grammatically **only to clause (b)** (the `reputation.witnesses` array). Clause (a) — "an R7 transaction MUST NOT proceed without witnessing" — and the lead-in "R7 actions MUST be witnessed:" were **unconditional**, applying to ALL R7 regardless of consequence.

But both cited sections scope mandatory witnessing to **high-consequence** actions only:

- **§7.5 item 4**: *"low-consequence R6 calls MAY proceed without witnessing; for high-consequence actions, R7 MUST NOT proceed without witnessing (consistent with the §7.3 normative requirement…)"*
- **§7.3**: *"For high-consequence actions (per the responding society's classification), `reputation.witnesses` MUST contain at least one entry from a Witness role…"*

Because cross-society actions are **R7-by-default** (§7.3) independent of consequence, a **low-consequence cross-society R7** is reachable — conformant under §7.5/§7.3 but falsely **non-conformant under §12 MUST #6** as written. This was a [[feedback_remediation_introduced_regression]]: C77's fix for C76-B4 (which correctly added the high-consequence witnessing MUST and a non-exhaustive preamble) over-tightened clause (a) from the requested "high-consequence" scope to unconditional. Adversarially verified REAL in C116; severity deflated MED→LOW because the §12 preamble subordinates the summary to §7.3/§7.5 and the error is over-strict (rejects valid traffic), not a safety gap.

## The fix

Relocate the scope qualifier to govern the whole item, so both clauses inherit the high-consequence scope that §7.5 (clause a) and §7.3 (clause b) each independently require.

**Before** (`f3d2613d` … HEAD):
```
6. R7 actions MUST be witnessed: an R7 transaction MUST NOT proceed without witnessing (§7.5), and for high-consequence actions the `reputation.witnesses` array MUST contain at least one Witness-role entry (§7.3)
```

**After** (this remediation):
```
6. R7 actions MUST be witnessed: for high-consequence actions, an R7 transaction MUST NOT proceed without witnessing (§7.5), and the `reputation.witnesses` array MUST contain at least one Witness-role entry (§7.3)
```

This is the wording recommended verbatim in C116 §B.2 (L111) and routed as autonomous-actionable in C116 §C (L126).

## Post-edit verification (C56 remediation-completeness)

Re-read §7.3 and §7.5 after the edit to confirm no NEW asymmetry was introduced:

- Clause (a) "an R7 transaction MUST NOT proceed without witnessing (§7.5)" — §7.5 item 4 scopes this to high-consequence. ✓ Faithful.
- Clause (b) "the `reputation.witnesses` array MUST contain at least one Witness-role entry (§7.3)" — §7.3 *already* scoped its array requirement to "For high-consequence actions" before this edit. Placing it under the shared qualifier restates the existing scope; it does **not** newly gate a previously-unconditional requirement. ✓ No asymmetry.
- The §12 preamble (L893-895, "not exhaustive … §7.3/§7.5 govern in full") is unchanged and still correctly subordinates the summary to the sections. ✓
- §7.6 error `412 web4_cross_society_witness_required` is the high-consequence enforcement path (C116 §B.2 "Inspected and bounded") — now consistent with §12 #6 as well as §7.3/§7.5. ✓

The summary MUST #6 now matches the sections it cites. The over-strict rejection of conformant low-consequence cross-society R7 is closed.

## Scope discipline

- **One line modified**; no other §12 item, no §7.x section text touched (§7.3/§7.5 are the canonical source and were already correct — only the summary was out of sync).
- **No corpus-wide MUST sweep.** Per the C120 signal (`docs/audits/C120-multi-device-lct-binding-3rd-delta-2026-06-30.md`), the MUST-vs-section defect class is doc-specific to normative-summary sections (mcp §12, atp-adp §7.1), **not** corpus-wide — it was remediated FILE-BY-FILE as rotation reached this doc, not batched speculatively.
- No SDK or test changes — this is a doc-summary precision correction with no behavioral delta (the SDK and §7.3/§7.5 already implement the high-consequence scope).
- Cross-track / design-Q carries from C116 (B2/B6 r7-reputation shape, B5/B12 registry-home, N5/N9/N13 §7.7 promotion, N12 error model, N15 `lct:web4:` id, F5 interaction_type home, F9 PolicyEntity form, B1-family `entity_subtype`) remain **untouched and open** — operator/cross-track gated, not part of this autonomous remediation.

## Status

- C116-N1: **REMEDIATED**.
- mcp remediation debt from the C116 audit: **cleared** (N1 was the only autonomous-actionable finding).
- Open mcp carries: all cross-track/design-Q (see C116 §C and `carries.md`) — unchanged.

---

*Remediation turn. One line of spec text modified, one record file created. No SDK or test code touched. Applies the single adversarially-verified AUTONOMOUS finding from C116; corpus-wide-sweep explicitly declined per the C120 doc-specific signal. See [[feedback_remediation_introduced_regression]], [[feedback_audit_workflow_adversarial_verify]].*
