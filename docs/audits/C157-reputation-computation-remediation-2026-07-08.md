# C157 — reputation-computation.md Remediation (applies C156-2)

**Date**: 2026-07-08
**Slot**: worker/web4-20260708-060036 (LEAD)
**Authorizing audit**: C156 (PR #483, MERGED 2026-07-08 with operator APPROVED comment; C156-2 spot-verified real by reviewer)
**Scope**: exactly ONE line — the single item C156 routed as autonomous. **NOT a no-op** (pre-declared by C156).

## Applied

**C156-2 (LOW)** — §9 Sybil Resistance item 4 asserted an unbacked mechanism in present tense, contradicting §10.

- **Before** (L762): `4. Historical patterns are analyzed (sudden changes flagged)`
- **After** (L762): `4. Historical patterns SHOULD be analyzed for sudden changes (see §10, Machine Learning Reputation Models; not yet specified)`

Wording is verbatim the fix shape prescribed in the C156 audit doc (B-I1-precedent shape: soften to future/SHOULD + cross-ref §10) and confirmed by both the merging operator comment and this session's policy reviewer. No deviation.

**Basis (from C156, re-verified at apply time)**: no anomaly/pattern-analysis mechanism exists in §4–§7, the SDK (`grep -iE 'anomal|historical|pattern|sudden'` reputation.py = 0), or the corpus; §10 L783–784 classifies exactly this capability ("Machine Learning Reputation Models — Use historical patterns to predict reputation changes and detect anomalies") as Future Evolution. Items 1–3 of the same list are backed (ATP cost §1; role-keying §1/r7 §1.7; witnesses per rule §6) and are untouched.

## Explicitly NOT applied (route-only, per C156)

| Finding | Owner / gate |
|---|---|
| C156-1 (C154-N1 amendment: mcp:415 3-option re-anchor menu) | mcp turn — carries.md has the menu; do not pre-empt |
| C156-3 (`sovereign_strength` Rust-ahead-of-spec) | r7 spec + Python-SDK owners |
| C156-4 (hub temporal fold law-ungated) | hub track |
| C156-5 (acp:418 "reputation stakes" dereference) | acp turn |

Zero SDK mutation. Zero edits outside `reputation-computation.md` L762. The canonical §3.2 Validity sentence (C44 B-M3-installed) untouched.

## Verification

- Post-edit grep: `SHOULD be analyzed for sudden changes` present at L762; old present-tense assertion gone (0 hits).
- File diff = exactly 1 line changed; `git diff --stat` confirms single-file single-hunk.
- Next audit of this file (5th delta) inherits: C124 stack (6 clean deltas) + this L762 edit as newest net-new prose → run the [[feedback_remediation_introduced_regression]] check against it (claim introduced: "not yet specified" — verifiable by §10 remaining future-scoped).

## Rotation

C157 complete → rotation advances to **acp-framework.md 4th delta** (last audited C125 #434 / remediated C126 #437). Note: C156-5 (acp:418) is inbound surface for that turn.
