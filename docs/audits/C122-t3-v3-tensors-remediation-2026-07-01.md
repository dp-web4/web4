# C122 Remediation: `t3-v3-tensors.md` — apply C118-N2

**Date**: 2026-07-01
**Author**: Autonomous session (Legion, web4 track) — REMEDIATION turn, slot `000036`
**Document**: `web4-standard/core-spec/t3-v3-tensors.md`
**Lineage**: C13 → C42 → **C43** (PR #299) → C82 → **C83** (PR #374, `25d36bb0`) → C121 (3rd delta AUDIT, PR #425, `59b21d5e`) → **C122** (this remediation).
**Finding applied**: **C118-N2** (raised at atp-adp C118, `C118-atp-adp-cycle-2nd-delta-2026-06-29.md`; CONFIRMED live at t3-v3 C121 §B.3, `C121-t3-v3-tensors-3rd-delta-2026-06-30.md`).
**Type**: Single citation-precision cell edit. Autonomous-in-file. Spec-only.

---

## The defect (C118-N2, as confirmed at C121)

`t3-v3-tensors.md` §10.2 protocol-invariants table, the **ATP conservation** row (L640, post-C83).

The C83 F2 remediation reworded this row's "Related context" cell to **primary-anchor on atp-adp §6.3** ("Transfer Fees") while **quoting**:
- the supply equation `total supply = ATP + ADP`, and
- the per-transfer form `initial == final + fees`.

Neither quoted element lives in §6.3. Verified against the **live** `atp-adp-cycle.md` (frozen in the relevant sections; C119 `e99b419e` touched only §4.2/§7.1):

| Quoted element | True home section | Live evidence |
|----------------|-------------------|---------------|
| `total supply = ATP + ADP` (supply equation) | **§3.1 / §3.2** | §3.1 "Pool Architecture" (header L219; `total_supply` L227); §3.2 "Pool Management" (header L248; `total_supply == sum(...)` invariant L266) |
| `initial == final + fees` (per-transfer invariant) | **§2.4** | §2.4 "Slashing (ATP Destruction)" (header L170; the string at L214, scoping ATP→ADP transfers) |
| "preserving total supply" (looser, via fee-recycling) | **§6.3** | §6.3 "Transfer Fees" (header L593; fee-recycling "total supply" L605) — this is the *only* claim §6.3 actually supports |

So the cell primary-anchored §6.3 (which supports only the loosest claim) while quoting strings from §2.4 and §3.1/§3.2 — an anchor/quote mismatch **introduced by C83's own F2 reword** (a [[feedback_remediation_introduced_regression]] instance; caught by the atp-adp sibling audit reading t3-v3's outbound citation, not by t3-v3's own delta — cf. [[feedback_snapshot_presence_guard]]).

**Severity**: LOW (citation precision). The invariant text itself was already correct — total supply is conserved, transfers preserve it, slashing is the deliberate exception. **Owner**: t3-v3 (atp-adp is read-only here). C118 correctly routed this flag-only to the t3-v3 track; C121 confirmed it live and routed it to this remediation turn.

## The fix

The "Related context" cell now routes each element to its true home:

**Before** (L640):
```
| ATP conservation | total supply = ATP + ADP (transfers preserve total supply; the per-transfer form is `initial == final + fees`) | [`atp-adp-cycle.md`](atp-adp-cycle.md) §6.3 (§2.4 Slashing is the deliberate exception) | — |
```

**After**:
```
| ATP conservation | total supply = ATP + ADP (transfers preserve total supply; the per-transfer form is `initial == final + fees`) | [`atp-adp-cycle.md`](atp-adp-cycle.md) §3.1/§3.2 (supply equation `total supply = ATP + ADP`), §2.4 (per-transfer invariant `initial == final + fees`; Slashing is the deliberate exception), §6.3 (fee-recycling preserves total supply) | — |
```

Only the "Related context" column changed. The Parameter, Value, and Test-vector columns are byte-identical. The invariant statement (Value column) is untouched — this is precision, not a normative change.

## Verification

- Each cited anchor confirmed present in the live `atp-adp-cycle.md` at the line noted in the table above (grep-verified this session, not from memory — the C56 remediation discipline).
- No change to `atp-adp-cycle.md` (read-only sibling; not the defect site).
- No change to SDK / test-vectors / ontology.
- No operator-gated carry touched (D1 ontology-vocab, D3/M4 Valuation range, F1 minimal-vs-neutral, L3 t3v3-010 label, X4-structural, attach-strategy all remain open and untouched).
- No corpus-wide MUST sweep (C120→C121 signal: the MUST-vs-reference-impl class is doc-specific; N2 was a citation, not a missing carve-out — nothing to sweep).

## Disposition

- **C118-N2**: **CLOSED** by this edit.
- t3-v3 remediation debt after this turn: **none** autonomous. Remaining open items are operator/SDK-gated carries (see carries.md).
- Next t3-v3 AUDIT turn (rotation advances t3-v3 → reputation-computation) should verify this cell held and re-read it vs the then-live atp-adp sections.

---

*Remediation complete. One spec-only cell re-anchor; invariant text unchanged; every anchor verified live.*
