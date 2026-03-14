# Web4 Sprint Plan

**Created**: 2026-03-14
**Phase**: Development
**Track**: web4 (Legion)

---

## Active Tasks

### S1: Merge SDK module PRs

**Status**: READY
**Depends on**: None
**PRs**: #5 (R6), #6 (MRH), #7 (ACP)
**Description**: Review and merge the three SDK module PRs. Each adds a
canonical equation component to the Python SDK. PR #4 is a stale duplicate
of #5 and should be closed.

Merge order: #5 (R6) → #6 (MRH) → #7 (ACP) — each may need rebase on
the previous.

**Acceptance**: All 3 PRs merged to main, #4 closed, tests passing.

---

### S2: Cross-module integration tests

**Status**: IN PROGRESS (this session)
**Depends on**: None (tests main-branch modules)
**Description**: Integration tests proving trust+lct+atp+federation compose
correctly. Workflow scenarios, not unit tests.

**Acceptance**: test_integration.py passing, covers at least 3 cross-module
workflows.

---

### S3: Update web4_sdk.py re-exports

**Status**: BLOCKED (waiting on S1)
**Depends on**: S1
**Description**: web4_sdk.py currently imports from web4.trust, web4.lct,
web4.atp, web4.federation. After S1, add re-exports for web4.r6, web4.mrh,
web4.acp types.

**Acceptance**: web4_sdk.py imports and re-exports all 7 module types.

---

### S4: Archive reference implementation sprawl

**Status**: READY
**Depends on**: None
**Description**: 189 files in `implementation/reference/` — many are standalone
scripts reimplementing generic CS concepts with a "trust_" prefix. Move
academic sprawl to `archive/reference-implementations/` and document what
was kept vs archived and why.

**Acceptance**: reference/ contains only files that import from or are imported
by the SDK. Archived files are in archive/ with a manifest.

---

### S5: Close stale PR #4

**Status**: READY (can be done immediately)
**Depends on**: None
**Description**: PR #4 is a duplicate of PR #5 (both R6 module). Close #4
with a comment explaining it was superseded by #5.

**Acceptance**: PR #4 closed.

---

## Planned Tasks (Scoped)

### S6: Post-merge integration tests (all 7 modules)

**Status**: PLANNED
**Depends on**: S1, S2
**Description**: After all PRs merge, extend integration tests to cover
cross-module workflows using all 7 SDK modules (trust, lct, atp, federation,
r6, mrh, acp). E.g., create entity → build agent plan → execute action →
record in MRH graph → check federation compliance.

**Acceptance**: Integration tests cover at least 2 workflows spanning 5+ modules.

---

### S7: SDK version bump and changelog

**Status**: PLANNED
**Depends on**: S1
**Description**: After merging all module PRs, update __init__.py to v0.2.0,
write a CHANGELOG.md documenting what each version added.

**Acceptance**: Version 0.2.0, changelog covers v0.1.0 and v0.2.0.

---

## Unscoped Tasks

These are known needs without implementation details. Each requires its own
scoping session before work begins.

### U1: Dictionary entities module
Web4 dictionaries are elevated to foundational entities (§2.6 in whitepaper).
No SDK module exists yet. Requires spec review to determine data structures.

### U2: Multi-device binding
Hardware binding hierarchy (API-Bridge → App → Pack Controller → Battery Module).
Patent-covered (305 family). Requires TPM2 integration design.

### U3: Whitepaper sync
Whitepaper sections may have drifted from SDK implementation. Requires
cross-reference audit between spec docs and SDK modules.

---

## Completed Tasks

(None yet — this sprint plan is new.)

---

## Task ID Reference

| ID | Summary | Status |
|----|---------|--------|
| S1 | Merge SDK module PRs (#5, #6, #7) | READY |
| S2 | Cross-module integration tests (main) | IN PROGRESS |
| S3 | Update web4_sdk.py re-exports | BLOCKED on S1 |
| S4 | Archive reference sprawl | READY |
| S5 | Close stale PR #4 | READY |
| S6 | Post-merge integration tests (all 7) | PLANNED |
| S7 | SDK version bump + changelog | PLANNED |
| U1 | Dictionary entities module | UNSCOPED |
| U2 | Multi-device binding | UNSCOPED |
| U3 | Whitepaper sync audit | UNSCOPED |
