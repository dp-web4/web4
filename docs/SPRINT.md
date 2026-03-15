# Web4 Sprint Plan

**Created**: 2026-03-14
**Updated**: 2026-03-14
**Phase**: Development
**Track**: web4 (Legion)

---

## Active Tasks

### S1: Merge SDK module PRs

**Status**: IN PROGRESS (1/3 merged)
**Depends on**: None
**PRs**: ~~#5 (R6)~~ merged, #6 (MRH) awaiting review, #7 (ACP) awaiting review
**Description**: Review and merge the three SDK module PRs. Each adds a
canonical equation component to the Python SDK.

Merge order: ~~#5 (R6)~~ → #6 (MRH) → #7 (ACP) — each may need rebase on
the previous.

**Acceptance**: All 3 PRs merged to main, tests passing.

---

### S3: Update web4_sdk.py re-exports

**Status**: IN PROGRESS (R6 done, MRH/ACP pending S1)
**Depends on**: S1 (for MRH + ACP)
**Description**: web4_sdk.py re-exports canonical types from web4 modules.
R6 re-exports added. After S1 completes, add re-exports for web4.mrh and
web4.acp types.

**Acceptance**: web4_sdk.py imports and re-exports all 7 module types.

---

## Planned Tasks (Scoped)

### S6: Post-merge integration tests (all 8 modules)

**Status**: DONE
**Depends on**: S1, S2
**Description**: Extended integration tests to cover cross-module workflows
using all 8 SDK modules (trust, lct, atp, federation, r6, mrh, acp, dictionary).
Two new test classes: `TestAgentActionWorkflow` (3 tests, 7 modules) and
`TestDictionaryTranslationWorkflow` (3 tests, 7 modules). Total: 25 integration tests.

**Acceptance**: ✅ 6 new tests covering 2 workflows, each spanning 7 modules.

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

**Status**: IN PROGRESS (PR #10 awaiting review)
**Description**: Web4 dictionaries elevated to foundational entities (§2.6 in whitepaper).
SDK module implemented as `web4.dictionary` — 320 lines, 33 tests, 5 test vectors.
Covers DictionarySpec, CompressionProfile, TranslationRequest/Result, TranslationChain,
DictionaryEntity, DictionaryVersion, and dictionary selection scoring.

### U2: Multi-device binding
Hardware binding hierarchy (API-Bridge → App → Pack Controller → Battery Module).
Patent-covered (305 family). Requires TPM2 integration design.

### U3: Whitepaper sync
Whitepaper sections may have drifted from SDK implementation. Requires
cross-reference audit between spec docs and SDK modules.

---

## Completed Tasks

### S2: Cross-module integration tests
**Completed**: 2026-03-14 (PR #8, merged as commit 099e524)
**Result**: 19 integration tests covering trust+lct+atp+federation cross-module workflows.

### S4: Archive reference implementation sprawl
**Completed**: 2026-03-14 (PR #9, merged as commit 0a514e6)
**Result**: 149 files archived to `archive/reference-implementations/`, 39 kept.
MANIFEST.md documents triage rationale.

### S5: Close stale PR #4
**Completed**: 2026-03-14
**Result**: PR #4 closed (duplicate of #5, superseded).

---

## Task ID Reference

| ID | Summary | Status |
|----|---------|--------|
| S1 | Merge SDK module PRs (#5, #6, #7) | IN PROGRESS (1/3) |
| S2 | Cross-module integration tests (main) | DONE |
| S3 | Update web4_sdk.py re-exports | IN PROGRESS (R6 done) |
| S4 | Archive reference sprawl | DONE |
| S5 | Close stale PR #4 | DONE |
| S6 | Post-merge integration tests (all 8) | DONE |
| S7 | SDK version bump + changelog | PLANNED |
| U1 | Dictionary entities module | IN PROGRESS (PR #10) |
| U2 | Multi-device binding | UNSCOPED |
| U3 | Whitepaper sync audit | UNSCOPED |
