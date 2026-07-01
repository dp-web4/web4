# C124: reputation-computation.md — Remediation (applies C123)

**Date**: 2026-07-01
**Author**: Autonomous session (legion-web4-20260701-120002), LEAD
**Turn type**: REMEDIATION (alternation after C123 AUDIT)
**Document**: `web4-standard/core-spec/reputation-computation.md`
**Applies**: `docs/audits/C123-reputation-computation-3rd-delta-2026-07-01.md` (PR #428, `748326db`)
**Lineage**: C13/C15 → C44 (#304) → C45 (#305) → C84 → C85 (#376 `15be0743`) → C123 (#428) → **C124** (this remediation)
**Direction**: spec→SDK convergence only. NO SDK / test-vector / `.ttl` mutation.

---

## Scope

Applied the **2 autonomous-actionable** findings from C123. The remaining C123 items
(X-1 schema reshape, X-2 §10 staleness, NEW-1-SDK-face, r7-§1.7-stale-factor,
SDK-6/N2 record-only) are **route-only / cross-track** and were NOT touched this turn.

Both edits were re-verified against SDK source **this session** before applying:
- `ReputationRule.matches()` (`reputation.py` L90–115): checks 4 recognized keys
  (`action_type`, `result_status`, `quality_threshold`, `min_atp_stake`), then
  `return True` — unrecognized keys silently ignored ⇒ **fail-OPEN**. Confirmed.
- Negative-age clamps present at `reputation.py` L442 (`current()` `age_days`) and
  L476 (`inactivity_decay()` `days_inactive`), both `max(0.0, …)`. Confirmed.
- git provenance: none of `fail-closed` / `unrecognized condition` /
  `Trigger Condition Semantics` exist in `15be0743^` — NEW-1's offending clause is
  **C85 remediation-introduced** (a [[feedback_remediation_introduced_regression]]
  catch, the pattern's 8th C-series confirmation). Confirmed.

---

## Applied

### NEW-1 (MED) — §4 "Trigger Condition Semantics" fail-closed SHOULD ⊥ SDK fail-OPEN

**Before** (§4 L295–296, added by C85):
> Implementations MAY define additional conditions; an unrecognized condition
> SHOULD cause the rule not to match (fail-closed) rather than be ignored.

**After**:
> Implementations MAY define additional conditions. The reference SDK
> (`reputation.py` `ReputationRule.matches()`) evaluates only the recognized
> conditions above and **ignores** any it does not recognize (**fail-open**): a
> rule matches when all recognized conditions pass, regardless of extra keys.
> An implementation MAY instead treat an unrecognized condition as fail-closed
> (cause the rule not to match); this is a stricter local choice and is **not
> currently required** for conformance.

**Rationale**: the C85 clause asserted a normative SHOULD that the reference
implementation does the exact opposite of. A conformant implementation following
the old text would reject rules the SDK accepts. The rewrite converges the spec to
the SDK's actual dispatch behavior (the established SDK→spec direction) and demotes
fail-closed to an optional, non-required local choice — removing the false
conformance claim **without silently changing SDK behavior via a spec edit**.
Whether the SDK *should* be tightened to fail-closed (the more defensible design
against malformed/adversarial rules) remains **NEW-1-SDK-face**, routed to the
operator; NOT self-applied.

Orphan check: `grep` for `fail-closed`/`unrecognized`/`ignored` confirmed the clause
appears ONLY at §4 — no summary/checklist restatement survives as an orphan.

### N1 (LOW) — §7 age pseudocode missing SDK's `max(0.0, …)` clamp

**Before**:
- L652 `age_days = (now() - delta.timestamp).total_seconds() / 86400.0  # fractional days (SDK parity)`
- L703 `days_inactive = (now() - last_action_timestamp).total_seconds() / 86400.0`

**After** (now L657 / L708 after §4 grew):
- `age_days = max(0.0, (now() - delta.timestamp).total_seconds() / 86400.0)  # fractional days, floored at 0 for clock skew (SDK parity)`
- `days_inactive = max(0.0, (now() - last_action_timestamp).total_seconds() / 86400.0)  # floored at 0 for clock skew (SDK parity)`

**Rationale**: exact parity with SDK `current()` L442 / `inactivity_decay()` L476, which
floor age at 0.0 to neutralize future-dated timestamps (clock skew). The pre-existing
value clamps `max(0.0, min(1.0, …))` at L374/L388/L668/L733 are unrelated and untouched.

---

## NOT applied (route-only — carried forward)

| ID | Disposition |
|---|---|
| **X-1** (MED, cross-track) | reputation-schema reshape: mcp §7.3 flat `trust_dimension_updates` ⊥ r7 §1.7 / this doc's `t3_delta`+`v3_delta` split. Belongs to the operator's mcp B2/B6 bundle. STILL OPEN. |
| **X-2** (LOW, cross-track) | §10 "Future Evolution" stale vs mcp §7.5 normative; rides X-1. STILL OPEN. |
| **NEW-1-SDK-face** | whether SDK `matches()` should be tightened to fail-closed — SDK-behavioral/security operator decision. Routed. |
| **r7-§1.7-stale-factor** (LOW) | r7-framework §1.7 example still carries the pre-INT-1 `accuracy_threshold_exceeded` factor; belongs to a future r7 audit turn (routed outbound). |
| **SDK-6/B-I5**, **N2** | record-only (§6 witness SDK gap; SDK write-back side-effect). Unchanged. |

---

## Verification

- `grep max(0.0` → both new §7 clamps present (L657, L708); 4 pre-existing value clamps intact.
- `grep fail-open/fail-closed` → 2 hits, both in the single rewritten §4 paragraph; no orphan.
- Spec-only change; no SDK/vector/.ttl touched (`git diff --stat` = 1 spec file + this record).
- Markdown structure intact (table + paragraph render unchanged around §4; §7 code block valid).

**Result**: reputation-computation.md §4 no longer contradicts the reference SDK on
unrecognized trigger conditions, and §7 age pseudocode matches the SDK's clock-skew
flooring. reputation-computation is now at **zero autonomous spec-vs-SDK debt**; the
only remaining items are cross-track/operator carries (X-1, X-2, NEW-1-SDK-face,
r7-stale-factor) and record-only notes.

---

*C124 closes the two autonomous findings C123 opened. The NEW-1 catch — a prior
remediation's own added prose over-reaching into a false conformance SHOULD — is the
8th C-series confirmation of the remediation-introduced-regression pattern: always
git-check net-new prose against `<remediation-commit>^` and re-test it against the
SDK/canonical it claims to mirror.*
