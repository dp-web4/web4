# C151 — atp-adp-cycle.md Remediation (applies C150-N1)

**Date**: 2026-07-07
**Turn type**: REMEDIATION (odd-C# turn following the C150 3rd-delta audit, PR #475, merged `0bb9a20b`)
**Target**: `web4-standard/core-spec/atp-adp-cycle.md`
**Lineage**: C11 (#224) → C34 (#276/#277) → C78 (#367) / C79 (#368) → C118 (#418) → C119 (#420 `e99b419e`) → C150 (#475 audit) → **C151** (this, applies C150-N1)

---

## Scope

Exactly the C150 autonomous remediation set: **N1 only** (one-phrase spec edit).
All other C150 routings untouched: B1/B2b/M2/ISP-B10 (DESIGN-Q, operator-gated),
B3/B4/I2/B6-SDK (SDK-track; `atp.py` not modified), X1 (cross-track C33).

## The Change

**§2.4 supply-accounting note, L214** — the transfer-conservation invariant's
scope phrase.

| | Text |
|---|---|
| **Before** | "…which scopes only **ATP→ADP transfers** — a destruction event…" |
| **After** | "…which scopes only **ATP transfers between entities (§6.3)** — a destruction event…" |

**Why (C150-N1, adversarially confirmed 3 ways)**: "ATP→ADP" is this doc's
*discharge* arrow (§2.3 heading; §3.3 "performs the ATP→ADP discharge of
§2.3"), while entity→entity *transfers* are written arrow-free (§6.3; §7.3 #6).
The invariant `initial == final + fees` is transfer-scoped per the SDK
canonical (`atp.py` `check_conservation`, tied to `transfer()` with
`fee = amount * fee_rate`) and does not coherently apply to a discharge, which
reduces the ATP total feelessly by design. The defective phrase was L214's
sole arrow+transfer hybrid and the corpus's only occurrence (grep-verified
pre-edit). Latent since C34 `f854e0e`; became load-bearing when t3-v3 C122
`b2a98f7c` anchored its §10.2 ATP-conservation row on this exact note.

No semantic change: the slashing exception, destruction semantics, and supply
accounting are untouched — only the invariant's scope label is corrected to
match what the invariant already meant.

## Verification

1. **Pre-edit grep**: `ATP→ADP transfers` occurred exactly once in the corpus
   (atp-adp-cycle.md:214; other hits are audit docs quoting it). Post-edit
   count in the spec: 0.
2. **§6.3 read-check** (policy-review condition): §6.3 "Transfer Fees" is the
   entity-to-entity ATP transfer + fee locus ("Peer-to-peer ATP transfers
   within a society…", fee recycling preserving total supply) — the new
   cross-reference is supported.
3. **t3-v3 L640 anchor re-read** (C150 follow-through): the §10.2 ATP
   conservation row cites "§2.4 (per-transfer invariant
   `initial == final + fees`; Slashing is the deliberate exception)". Post-edit
   §2.4 now states the invariant scopes ATP transfers between entities with
   slashing outside it — the sibling's citation and the cited text now agree;
   the C150-identified disagreement (sibling read transfer-scoped, literal
   wording said discharge-scoped) is resolved.
4. **Line-anchor preservation**: single-line diff; the note's line span
   (L210–215) is unchanged, so sibling/audit line citations remain valid.
   (The edited line is 105 chars in a mostly-80-wrapped doc; the file already
   contains 12 lines >95 chars, so no re-wrap — minimal diff wins.)
5. **Doc-convention sweep**: remaining `ATP→ADP` occurrences in the doc are
   all discharge contexts (§2.3, §3.3) — the arrow convention is now
   internally consistent.

## Routing State After C151

| Item | State |
|------|-------|
| C150-N1 | **APPLIED** (this turn) |
| C118-N2 | CLOSED at C150 (applied by t3-v3 C122, verified) |
| B1 / B2b / M2 / ISP-B10 | DESIGN-Q — operator-gated, STAND |
| B3 / B4 / I2 / B6-SDK | SDK-track — STAND (`atp.py` frozen) |
| X1 | CROSS-TRACK (C33 identifier decision) — STAND |

**Rotation**: next atp-adp turn returns to AUDIT on the next wrap; next fire
advances +2 to `multi-device` (last C120, clean; thin-§7 known
clean-except-owned).

---

*Remediation complete: 1 phrase edited, 0 semantic changes, all gated carries untouched.*
