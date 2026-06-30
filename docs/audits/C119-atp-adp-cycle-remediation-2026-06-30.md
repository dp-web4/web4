# C119 Remediation: `atp-adp-cycle.md` — apply C118-N1

**Date**: 2026-06-30
**Author**: Autonomous session (Legion, web4 track) — v2 protocol, policy-approved
**Document**: `web4-standard/core-spec/atp-adp-cycle.md`
**Lineage**: C11 (#224 first-pass) → C34 (#276/#277) → C78 (#367 delta) → C79 (#368 remediation) → **C118** (#418 second delta-re-audit, identified N1) → **C119** (this remediation).
**Baseline**: C118 audit (`docs/audits/C118-atp-adp-cycle-2nd-delta-2026-06-29.md`), finding **N1**.

---

## What was fixed

**C118-N1 (LOW, AUTONOMOUS-candidate, internal cross-section contradiction).**

§7.1 MUST #6 read *"Value MUST be tracked through T3/V3 tensors"* — **unconditional**,
with no entity-vs-society scoping. But the spec's own reference implementation
§4.2 `track_value_flow` routes the society-level leg of the fractal value cascade
(§4.3 Levels 4 Society / 5 Parent-society) through an `aggregate_value` channel
that is **explicitly self-labeled** *"society-level aggregate, not a T3/V3
dimension."* The literal unconditional MUST #6 therefore contradicted the spec's
own §4.2 code.

The C79 B2a remediation (the §3.3 demurrage **R6-scoping** note) had already
established that the §7.1 MUST clauses here carry scope limits — that same note
even states demurrage *"creates no V3 value and so does not engage MUST #6."*
Yet §4.2's society-aggregate exemption from MUST #6 stayed **un-noted**. C118-N1
is the [[feedback_remediation_introduced_regression]] mirror of **C116-N1** (an
unconditional `mcp` §12 summary MUST vs the narrower §7 reality) — the same
defect class: an over-broad summary MUST whose own reference implementation
carves out an unstated exception.

## Edit applied

Two-part fix (the audit-doc L84 offered "scope MUST #6 **or** add a §4.2
carve-out note"; both were applied for an unambiguous, bidirectional resolution):

1. **§7.1 MUST #6** reworded to scope it explicitly:
   > 6. Entity-level value MUST be tracked through T3/V3 tensors; society-level
   >    aggregates MAY use non-tensor rollup accounting (§4.2)

2. **New §7.1 scope note** (immediately under the MUST list, in the style of the
   existing C79 §3.3 demurrage note) explaining that MUST #6 governs the
   entity-role legs the §4.2 impl tracks via T3/V3 deltas (primary beneficiary
   `v3`, contributors/agents `t3`, witnesses `t3`) while the society-level
   aggregate (§4.3 Levels 4–5: Society and Parent-society) is a coarse
   `aggregate_value` rollup that does not engage MUST #6 — same carve-out
   pattern as demurrage. (The note avoids pinning the entity legs to §4.3
   cascade Level numbers, since the primary beneficiary sits *outside* the
   §4.3 contribution cascade per the C79 B8 note.)

3. **§4.2 code comment** extended at the `aggregate_value` site to point back at
   the §7.1 MUST #6 scope note, so the exemption is no longer silent at the
   reference-impl site that the audit flagged.

The adjacent escrow Note block (formerly L623–629) was preserved unchanged, per
the policy-review executor note.

## What was NOT touched (carries forward)

- **C118-N2** (t3-v3 C83 anchor/quote mismatch, `initial == final + fees` cited
  on §6.3 instead of §2.4/§3.1-3.2) — **t3-v3-owned**, route into the next t3-v3
  remediation turn. No atp-adp action.
- **C116-N1** (mcp §12 summary MUST over-tightened by C77-B4) — **separate file**,
  pending **C117** mcp remediation turn. The *same* defect class as N1 here →
  the recurrence (mcp §12 + atp-adp §7.1) remains a corpus-wide signal for a
  future scoped "enumerate every summary-MUST vs its reference impl" sweep. NOT
  done this fire (out of scope).
- All C118 §A open carries (B1/B2b/M2 DESIGN-Q, B3/B4/I2/B6-SDK SDK-track, X1,
  ISP-B10) — operator-gated / SDK-track, **STILL OPEN**.

## Verification

- Markdown structure intact; MUST list still 1–6; both notes are well-formed
  block quotes; §4.2 code block still valid.
- Internal contradiction resolved: MUST #6 and §4.2 now agree (entity-role legs
  use T3/V3; society aggregate uses rollup, explicitly outside MUST #6).
- No SDK, no other spec files, no operator-gated carries touched.
