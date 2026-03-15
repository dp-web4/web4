# Web4 Sprint Plan

**Created**: 2026-03-14
**Updated**: 2026-03-15
**Phase**: Development
**Track**: web4 (Legion)

---

## Active Tasks

### S6: Post-merge integration tests (all 8 modules)

**Status**: PLANNED (now unblocked)
**Depends on**: S1, S2
**Description**: Extend integration tests to cover cross-module workflows
using all 8 SDK modules (trust, lct, atp, federation, r6, mrh, acp,
dictionary). E.g., create entity → build agent plan → execute action →
record in MRH graph → translate via dictionary → check federation compliance.

**Acceptance**: Integration tests cover at least 2 workflows spanning 5+ modules.

---

## Unscoped Tasks

These are known needs without implementation details. Each requires its own
scoping session before work begins.

### U2: Multi-device binding
Hardware binding hierarchy (API-Bridge → App → Pack Controller → Battery Module).
Patent-covered (305 family). Requires TPM2 integration design.

### U3: Whitepaper-SDK coherence fixes

**Status**: SCOPED (audit complete 2026-03-15)
**Depends on**: None (can proceed independently of S1)
**Audit**: `docs/audits/whitepaper-sdk-coherence-2026-03-15.md`
**Description**: Audit found 4 divergences and 3 gaps between whitepaper and SDK.
Two sub-tasks:

**U3a: SDK coherence naming fix** — DONE (2026-03-15). Renamed `coherence()`→`operational_health()`,
`is_coherent()`→`is_healthy()`, constants `COHERENCE_WEIGHTS`→`HEALTH_WEIGHTS`,
`COHERENCE_THRESHOLD`→`HEALTH_THRESHOLD`, `ReputationScore.coherence_score`→`health_score`.
All 70 tests passing. Docstring explains distinction from whitepaper identity coherence.

**U3b: Whitepaper section updates** — Update whitepaper §2.4 to reference R7 evolution
(Reputation as 7th component), §2.5 to reconcile 5-dimension conceptual model vs
graph implementation model, and §2.2 to expand entity type examples. ~2-3 files modified.

**Acceptance**: (a) No naming collision between SDK coherence function and whitepaper
identity coherence concept. (b) Whitepaper §2.4 references R7. (c) Whitepaper §2.5
acknowledges graph-based MRH implementation.

---

## Completed Tasks

### S1: Merge SDK module PRs
**Completed**: 2026-03-15 (all 3 PRs merged)
**Result**: PRs #5 (R6), #6 (MRH), #7 (ACP) merged to main. All tests passing.

### S2: Cross-module integration tests
**Completed**: 2026-03-14 (PR #8, merged as commit 099e524)
**Result**: 19 integration tests covering trust+lct+atp+federation cross-module workflows.

### S3: Update web4_sdk.py re-exports
**Completed**: 2026-03-15
**Result**: web4_sdk.py imports and re-exports canonical types from all 8 modules
(trust, lct, atp, federation, r6, mrh, acp, dictionary). 51 re-exported symbols.

### S4: Archive reference implementation sprawl
**Completed**: 2026-03-14 (PR #9, merged as commit 0a514e6)
**Result**: 149 files archived to `archive/reference-implementations/`, 39 kept.
MANIFEST.md documents triage rationale.

### S5: Close stale PR #4
**Completed**: 2026-03-14
**Result**: PR #4 closed (duplicate of #5, superseded).

### S7: SDK version bump and changelog
**Completed**: 2026-03-15
**Result**: Version 0.2.0 (set during module PR merges). CHANGELOG.md covers
v0.1.0 (4 core modules) and v0.2.0 (3 new modules + full re-exports).

### U1: Dictionary entities module
**Completed**: 2026-03-15 (PR #10, merged as commit df1fca7)
**Result**: `web4.dictionary` module — 320 lines, 33 tests, 5 test vectors.

### U3a: SDK coherence naming fix
**Completed**: 2026-03-15
**Result**: Renamed `coherence()`→`operational_health()`, `is_coherent()`→`is_healthy()`,
plus constants and `ReputationScore.coherence_score`→`health_score`. Resolves naming
collision with whitepaper identity coherence (C×S×Phi×R). 70 tests passing.

---

## Task ID Reference

| ID | Summary | Status |
|----|---------|--------|
| S1 | Merge SDK module PRs (#5, #6, #7) | DONE |
| S2 | Cross-module integration tests (main) | DONE |
| S3 | Update web4_sdk.py re-exports | DONE |
| S4 | Archive reference sprawl | DONE |
| S5 | Close stale PR #4 | DONE |
| S6 | Post-merge integration tests (all 8) | PLANNED |
| S7 | SDK version bump + changelog | DONE |
| U1 | Dictionary entities module | DONE |
| U2 | Multi-device binding | UNSCOPED |
| U3 | Whitepaper-SDK coherence fixes | U3a DONE, U3b TODO |
