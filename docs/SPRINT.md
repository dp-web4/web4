# Web4 Sprint Plan

**Created**: 2026-03-14
**Updated**: 2026-03-17
**Phase**: Development
**Track**: web4 (Legion)

---

## Active Tasks

### U5: Entity type taxonomy module
**Status**: DONE
**Completed**: 2026-03-16
**Result**: `web4.entity` module — 284 lines, 48 tests, 5 vectors. PR #20, merged.

### U9: Society metabolic states module
**Status**: DONE
**Completed**: 2026-03-17
**Result**: `web4.metabolic` module — 300 lines, 71 tests, 12 vectors. PR #23, merged.

### U10: T3/V3 tensor enhancements
**Status**: DONE
**Completed**: 2026-03-17
**Result**: ActionOutcome enum, outcome-based T3 evolution, decay/refresh, RoleRequirement, V3.calculate(), compute_team_t3(). 51 new tests, 5 vectors. Extended trust.py.

### U6: Capability levels module
**Status**: DONE
**Completed**: 2026-03-17
**Result**: `web4.capability` module — 6-level LCT capability framework (Stub → Hardware) per lct-capability-levels.md spec. 42 tests, cross-language vectors. PR #26, merged.

### U7: Error taxonomy module
**Status**: DONE
**Completed**: 2026-03-17
**Result**: `web4.errors` module — 353 lines, 42 tests, 5 vectors. 24 error codes across 6 categories with RFC 9457 Problem Details serialization. PR #27, merged.

### U11: Society core module
**Status**: DONE
**Completed**: 2026-03-17
**Spec**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md`
**Result**: `web4.society` module — 766 lines, 86 tests, 6 vectors. Composes federation, metabolic, atp, trust, lct, entity modules into society orchestration layer. PR #31, merged.

### U12: SDK v0.4.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-18
**Result**: Fixed missing metabolic module re-exports in web4_sdk.py (22 symbols), bumped version to 0.4.0, CHANGELOG.md documents 6 new + 2 enhanced modules since v0.3.0. SPRINT.md updated (U7/U11 → DONE).

### U14: Core protocol types module
**Status**: DONE
**Spec**: `web4-standard/core-spec/core-protocol.md`
**Description**: Implement `web4.protocol` module with handshake message types (ClientHello, ServerHello, ClientFinished, ServerFinished), PairingMethod enum, Transport enum with profiles, DiscoveryMethod enum with privacy levels, Web4URI parser/validator, and transport negotiation. Types only — no networking.

### U15: MCP protocol types module
**Status**: DONE
**Spec**: `web4-standard/core-spec/mcp-protocol.md`
**Description**: Implement `web4.mcp` module with Web4Context headers, CommunicationPattern enum, MCP resource types (tool/prompt/context), TrustRequirements, MCPSession with ATP tracking, SessionHandoff, ATP metering (calculate_mcp_cost), WitnessAttestation, MCPCapabilities/CapabilityBroadcast, MCPAuthority, MCPErrorContext. Types only — no networking or JSON-RPC.

### U16: Full-stack integration tests (all 18 modules)
**Status**: IN REVIEW
**Result**: 3 cross-module integration test workflows covering all 18 SDK modules. PR #38.

### U17: SDK v0.5.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-18
**Result**: CHANGELOG.md updated with v0.5.0 entries for U13 (security), U14 (protocol),
U15 (mcp). Version bumped 0.4.0 → 0.5.0. SPRINT.md U13 status corrected, U16/U17 added.

---

## Unscoped Tasks

These are known needs without implementation details. Each requires its own
scoping session before work begins.

### U2: Multi-device binding
**Status**: DONE
**Completed**: 2026-03-17
**Design**: `docs/designs/u2-multi-device-binding.md`
**Spec**: `web4-standard/core-spec/multi-device-lct-binding.md`
**Result**: `web4.binding` module — AnchorType (4 types), DeviceStatus, HardwareAnchor,
DeviceRecord, DeviceConstellation, constellation management (enroll/remove), trust
computation (witness freshness, coherence bonus, cross-witness density, ceiling),
cross-device witnessing, recovery quorum. 68 tests, 6 vectors. Patent-covered (305 family).

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

### U13: Security primitives module
**Status**: DONE
**Completed**: 2026-03-18
**Spec**: `web4-standard/core-spec/security-framework.md`, `web4-standard/core-spec/data-formats.md`
**Result**: `web4.security` module — 339 lines, 51 tests, 12 vectors. CryptoSuite definitions
(W4-BASE-1, W4-FIPS-1), W4ID (DID:web4) parsing/validation/pairwise derivation, KeyPolicy types,
SignatureEnvelope, VerifiableCredential. Types-only — no crypto implementations. PR #34, merged.

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
| U2 | Multi-device binding | DONE |
| U3 | Whitepaper-SDK coherence fixes | DONE (U3a + U3b) |
| U4 | Reputation computation module | DONE |
| U5 | Entity type taxonomy module | DONE |
| U6 | Capability levels module | DONE |
| U7 | Error taxonomy module | DONE |
| U8 | SAL governance extensions | DONE |
| U9 | Society metabolic states module | DONE |
| U10 | T3/V3 tensor enhancements | DONE |
| U11 | Society core module | DONE |
| U12 | SDK v0.4.0 release housekeeping | DONE |
| U13 | Security primitives module | DONE |
| U14 | Core protocol types module | DONE |
| U15 | MCP protocol types module | DONE |
| U16 | Full-stack integration tests (18 modules) | PR #38 |
| U17 | SDK v0.5.0 release housekeeping | DONE |
