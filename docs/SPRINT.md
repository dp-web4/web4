# Web4 Sprint Plan

**Created**: 2026-03-14
**Updated**: 2026-03-19
**Phase**: Development
**Track**: web4 (Legion)

---

## Sprint 3: SDK Interoperability (2026-03-19)

The SDK has 19 modules with 1000+ tests, but a known gap exists: no Python
implementation produces schema-compliant LCT documents. This sprint closes
interoperability gaps between the SDK output and the spec's canonical formats.

### I1: LCT spec-compliant JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: Add `to_jsonld()` / `from_jsonld()` methods to `LCT` class producing
documents matching spec §2.3 canonical structure. Includes: `@context` header,
spec-compliant field naming (`birth_context` not `context`), structured MRH entries
(bound/witnessing as objects), optional sections (attestations, lineage) included
only when populated, full revocation structure (status + ts + reason).
New types: `Attestation`, `LineageEntry`, `LCT_JSONLD_CONTEXT`.
`BirthCertificate` gains optional `genesis_block_hash`.
`LCT.revoke()` gains optional `reason` parameter.
Backward compatible: `to_dict()` unchanged, `from_jsonld()` accepts both formats.
**Result**: 51 new tests, 1093 total passing. Closes known gap "NO Python impl
produces schema-compliant LCT document."

### I2: Cross-language LCT test vectors
**Status**: DONE
**Completed**: 2026-03-20
**Scope**: JSON test vectors for LCT JSON-LD roundtrip that TypeScript/Go/Rust
implementations can validate against. Same pattern as existing 79+ SDK vectors.
**Result**: 10 vectors covering: minimal LCT, full LCT (all optional fields), revoked,
attestations, lineage, complex MRH, boundary T3/V3, suspended status, genesis_block_hash,
no birth certificate. 110 validation tests (roundtrip, structure, values, spec compliance,
backward compat). 1203 total passing.

### I3: AttestationEnvelope JSON-LD serialization
**Status**: PENDING
**Scope**: Add `to_jsonld()` / `from_jsonld()` to `AttestationEnvelope` in
`web4.attestation`, matching the attestation-envelope spec format.

### I4: SDK v0.7.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-20
**Depends on**: I1 (at minimum)
**Scope**: Version bump 0.5.0 → 0.7.0 (0.6.0 covered by H6 PR #46),
CHANGELOG.md entry for Sprint 3 JSON-LD serialization (I1, I2, I3),
updated exports count (263 symbols).
**Result**: Version bumped in `__init__.py`, `pyproject.toml`, `setup.py`.
CHANGELOG.md v0.7.0 section documents LCT JSON-LD, cross-language vectors,
and AttestationEnvelope JSON-LD. 1093 tests passing, zero regressions.

---

## Sprint 2: Hardware Trust Validation (2026-03-19)

The AttestationEnvelope landed on main (3 commits by operator, 2026-03-18) as the P0
hardware binding primitive. It has a spec, implementation, and verification dispatch —
but zero test coverage. This sprint validates the new code and prepares it for
integration with the SDK.

### H1: AttestationEnvelope test coverage
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: Comprehensive tests for `web4-core/python/web4/trust/attestation/envelope.py` —
construction, defaults, auto-computed fields (fingerprint, trust ceiling), serialization
round-trips (to_dict/from_dict, to_json/from_json), freshness model (is_fresh,
freshness_factor, effective_trust), and edge cases.
**Result**: 49 tests in `test_envelope.py` — all passing.

### H2: Verification dispatch test coverage
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: Tests for `verify_envelope()` dispatch and all 4 anchor verifiers —
software (end-to-end), TPM2/FIDO2/SE (stub behavior), challenge mismatch,
unknown anchor type, PCR validation.
**Result**: 42 tests in `test_verify.py` — all passing. Parametrized cross-anchor consistency tests.

### H3: Cross-language test vectors for attestation
**Status**: PENDING
**Scope**: JSON test vectors for AttestationEnvelope construction and verification
that other language implementations can validate against. Same pattern as existing
79+ SDK vectors.

### H4: SDK integration for AttestationEnvelope
**Status**: DONE
**Completed**: 2026-03-19
**Depends on**: H1, H2
**Scope**: Evaluate whether `web4-core/` attestation types should be re-exported from
the `web4` SDK package or remain separate. If integrating, add to `web4/__init__.py`.
**Decision**: Mirror into SDK (not re-export from web4-core). Rationale: namespace collision
between web4-core and web4-standard SDK (both define `web4` package), SDK has zero imports
from web4-core, attestation types are pure Python (stdlib only). Created `web4/attestation.py`
consolidating all types + verify_envelope dispatcher + 4 anchor verifiers.
**Result**: `web4.attestation` module — 8 new symbols in `web4/__init__.py`
(AttestationEnvelope, AnchorInfo, Proof, PlatformState, VerificationResult, TRUST_CEILINGS,
FRESHNESS_MAX_AGE, verify_envelope). 41 tests, 1015 total passing.

### H5: AttestationEnvelope + binding module integration
**Status**: DONE
**Completed**: 2026-03-19
**Depends on**: H4
**Scope**: Wire AttestationEnvelope into the existing `web4.binding` module
(DeviceConstellation, HardwareAnchor). The binding module already has AnchorType
and trust ceiling concepts — these should use AttestationEnvelope as the proof carrier.
**Result**: Bidirectional AnchorType↔attestation mapping (`ANCHOR_TYPE_TO_ATTESTATION`,
`attestation_anchor_type()`, `binding_anchor_type()`), `DeviceRecord.latest_attestation`
optional field, `enroll_device()` validates attestation purpose + anchor type compatibility,
`compute_device_trust()` combines anchor weight × witness freshness × attestation freshness.
`compute_constellation_trust()` now uses attestation-aware per-device trust (backward
compatible). 27 integration tests, 1042 total passing.

### H6: SDK v0.6.0 release housekeeping
**Status**: IN REVIEW
**Scope**: Version bump (0.5.0 -> 0.6.0) and changelog for the attestation module
that landed in H4. Sprint 2 status update.
**Result**: CHANGELOG.md v0.6.0 entry. PR #46.

---

## Sprint 1 (Complete)

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

### U18: SDK public API and packaging cleanup
**Status**: IN REVIEW
**Description**: Consolidate web4 package public API surface. Populate `web4/__init__.py`
with re-exports from all 18 modules (247 symbols, `__all__` defined). Fix `pyproject.toml`
metadata (version 0.5.0, classifiers, description). Add PEP 561 `py.typed` marker.
Fix `setup.py` consistency. `from web4 import T3, LCT, Society, R7Action` now works.
49 new tests, 974 total passing.

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
| U18 | SDK public API and packaging cleanup | PR #40 |
| H1 | AttestationEnvelope test coverage | DONE |
| H2 | Verification dispatch test coverage | DONE |
| H3 | Cross-language attestation test vectors | PR #43 |
| H4 | SDK integration for AttestationEnvelope | DONE |
| H5 | AttestationEnvelope + binding integration | DONE |
| H6 | SDK v0.6.0 release housekeeping | PR #46 |
| I1 | LCT spec-compliant JSON-LD serialization | DONE |
| I2 | Cross-language LCT test vectors | DONE |
| I3 | AttestationEnvelope JSON-LD serialization | PENDING |
| I4 | SDK v0.7.0 release housekeeping | DONE |
