# C195 — reputation-computation.md Remediation (applies C194-N2 + C194-N6)

**Date**: 2026-07-15
**Slot**: worker/web4-20260715-060036
**Authorizing audit**: C194 (PR #524, MERGED 2026-07-15T11:05Z with operator APPROVED comment: "N2/N6 owed as C195 autonomous"). Audit doc marks exactly these two findings "AUTONOMOUS, C195".
**Scope**: exactly the two autonomous-class items, both in `web4-standard/core-spec/reputation-computation.md` §5. Zero design content; both are SDK+vector-concord pseudocode alignments. Precedent: C157 (applied C156-2 after #483 merged).
**Policy review**: v2-protocol subagent APPROVED (session log `legion-web4-20260715-060036-session.md`).

## Applied

**C194-N2 (MEDIUM)** — §5 no-match branch returned an undefined helper, contradicting SDK `None` + vector rep-002 `"delta": null`.

- **Before** (:416): `return empty_reputation_delta()`
- **After** (:416): `return None  # no delta emitted`
- The preceding "No rules triggered = no reputation change" comment kept, per the C194 prescription (verbatim fix shape).
- **Basis (re-verified at apply time)**: `empty_reputation_delta` was defined nowhere — its only corpus occurrence was this call site (post-edit corpus grep: 0 hits). SDK `reputation.py evaluate()` docstring + body return `None` when no rules match; conformance vector rep-002 expects `"delta": null`. SDK+vector concord ⇒ spec pseudocode was the stale surface.

**C194-N6 (LOW)** — §5 `analyze_factors` emitted a `'value'` key in contributing factors that no other surface carries, self-contradicting :572.

- **Edit**: dropped the `'value'` line from all four appends (pre-edit :525 `quality`, :538 `True`, :545 `True`, :559 `efficiency`); trailing commas on the preceding `'weight'` lines removed accordingly. Line numbers re-verified at edit time per policy-reviewer caution.
- **Drop-vs-annotate**: C194 allowed either; **DROP chosen** because it is the option that makes :572's pre-existing claim ("exactly as `analyze_factors` emits them") TRUE against the worked example at :575-578, and matches every other surface — §1 example :49-53, SDK `ContributingFactor` (r6.py:563-576), SDK `analyze_factors` (reputation.py:170-192), vector rep-001 — all `{factor, weight}` only. Annotating would have preserved a spec-only field no implementation emits.
- **Safety (verified pre-edit)**: `factor_applies(modifier.condition, factors)` matches condition NAMES (`deadline_met`, `high_accuracy` — §4 modifier examples :258/:259/:265/:273); nothing in the spec pseudocode or SDK reads a factor `value` field. The `quality` / `efficiency` locals remain used (guard condition / weight computation respectively).

## Explicitly NOT applied (route-only, per C194)

| Finding | Owner / gate |
|---|---|
| C194-N1 (HIGH, Rust `ReputationDelta` wire shape) + N8 (wasm `vec![]` factors) + INFO-4 | SDK track (web4-core), semver-sensitive |
| C194-N3 (tensor-vs-aggregate layer split, A/B remediation shape) + N4 (10× rate divergence, folds into N3) | **operator DESIGN-Q memo bundle — do NOT self-apply** |
| C194-N5 (bad-faith-emergency disclaimer line) | W4IP-N5 owner's §4 note-refresh bundle; :387-394 region untouched |
| C194-N7 (`r6.py to_jsonld()` truthiness-drops) | ReputationDelta shape-reconcile bundle (C84 X-1 / SDK track) |
| C194 INFO-2 (W4IP-DRAFT ratification annotations) | HUB/CBP |

Zero SDK mutation. Zero vector mutation. Zero edits outside `reputation-computation.md` §5.

## Verification

- Baselined instrument ([[feedback_enumeration_and_grep_hypotheses]]): pre-edit greps = 4 × `'value'`, 1 × `empty_reputation_delta`; post-edit = 0 and 0. `return None  # no delta emitted` present at :416.
- `git diff --stat` = exactly 1 file, 5 hunks, +5/−9 — one line swapped (N2) + four 2-line→1-line append shrinks (N6).
- Intra-file consistency restored: :572's "exactly as `analyze_factors` emits them" now literally matches the pseudocode's emission shape.
- Next audit of this file (6th delta) inherits per [[feedback_remediation_introduced_regression]]: this edit is deletion-shaped (no new claims introduced); the one assertion to re-check is that `return None` still matches SDK `evaluate()` and rep-002 if either moves.

## Rotation

C195 complete → rotation advances (+2, wraps) to **C196 = acp-framework.md next delta** (`web4-standard/core-spec/acp-framework.md`; inbound: C156-5 CLOSED at C159 — verify HELD; check C158-N2/-N4 still parked).
