# Web4 Sprint Plan

**Created**: 2026-03-14
**Updated**: 2026-03-17
**Phase**: Development
**Track**: web4 (Legion)

---

## Active Tasks

### U9: Society metabolic states module
**Status**: IN PROGRESS (PR #23)
**Description**: Implement `web4.metabolic` module per `core-spec/SOCIETY_METABOLIC_STATES.md`.
8 biological-inspired metabolic states (Active→Torpor), transition validation,
energy cost calculation, wake penalty, metabolic reliability score, witness requirements.
**Deliverables**: `metabolic.py`, `test_metabolic.py`, `test-vectors/metabolic/society-metabolic-states.json`

### U10: T3/V3 tensor enhancements
**Status**: IN PROGRESS
**Description**: Extend `web4.trust` module with spec features from `core-spec/t3-v3-tensors.md`:
outcome-based evolution (§2.3), decay/refresh mechanics (§2.3), role requirements matching (§5.1),
V3 calculation from action components (§3.3), team tensor composition (§8.2).
**Deliverables**: Extended `trust.py`, new `test_trust.py`, 5 new test vectors

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

**U3b: Whitepaper section updates** — DONE (2026-03-15). Updated §2.4.4 to name Reputation
as the 7th component (R7 evolution). Added §2.5.4 reconciling 5-dimension conceptual model
vs graph implementation model. §2.2 entity type expansion skipped (audit rated LOW).

**Acceptance**: (a) No naming collision between SDK coherence function and whitepaper
identity coherence concept. (b) Whitepaper §2.4 references R7. (c) Whitepaper §2.5
acknowledges graph-based MRH implementation.

---

## Completed Tasks

### U8: SAL governance extensions (federation module)
**Completed**: 2026-03-16 (PR #22, merged as commit f00c35f)
**Result**: Extended `web4.federation` with SAL governance primitives — CitizenshipStatus
(5 lifecycle states), CitizenshipRecord, QuorumPolicy (3 modes), LedgerType, AuditRequest,
AuditAdjustment, Norm, Procedure, Interpretation, merge_law(). 29 new tests, 6 vectors.

### U5: Entity type taxonomy module
**Completed**: 2026-03-16 (PR #20, merged as commit 0b7d3a9)
**Result**: `web4.entity` module — 284 lines, 48 tests, 5 vectors.

### S6: Post-merge integration tests (all 8 modules)
**Completed**: 2026-03-15 (PR #14, merged as commit 8453df6)
**Result**: Extended integration tests covering cross-module workflows using all 8 SDK modules.
Workflows span trust→lct→atp→federation→r6→mrh→acp→dictionary. 298 total tests passing.

### U4: Reputation computation module
**Completed**: 2026-03-16
**Result**: `web4.reputation` module — 451 lines, 41 tests, 5 test vectors.
ReputationRule (trigger matching with modifiers), ReputationEngine (multi-rule evaluation),
ReputationStore (time-weighted aggregation + inactivity decay). SDK bumped to v0.3.0.

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

### U3b: Whitepaper section updates
**Completed**: 2026-03-15
**Result**: Updated §2.4.4 to name Reputation as the 7th component (R7 evolution).
Added §2.5.4 reconciling 5-dimension conceptual model vs graph implementation model.
Addresses audit findings D2 (MEDIUM) and D3 (MEDIUM).

---

## Task ID Reference

| ID | Summary | Status |
|----|---------|--------|
| S1 | Merge SDK module PRs (#5, #6, #7) | DONE |
| S2 | Cross-module integration tests (main) | DONE |
| S3 | Update web4_sdk.py re-exports | DONE |
| S4 | Archive reference sprawl | DONE |
| S5 | Close stale PR #4 | DONE |
| S6 | Post-merge integration tests (all 8) | DONE |
| S7 | SDK version bump + changelog | DONE |
| U1 | Dictionary entities module | DONE |
| U2 | Multi-device binding | UNSCOPED |
| U3 | Whitepaper-SDK coherence fixes | DONE (U3a + U3b) |
| U4 | Reputation computation module | DONE |
| U5 | Entity type taxonomy module | DONE |
| U6+U7 | Capability levels + error taxonomy | IN PROGRESS (PR #21) |
| U8 | SAL governance extensions | DONE |
| U9 | Society metabolic states module | IN PROGRESS (PR #23) |
| U10 | T3/V3 tensor enhancements | IN PROGRESS |
