# Changelog

All notable changes to the Web4 Python SDK.

## [0.5.0] - 2026-03-18

Three new protocol-layer modules, completing the 18-module SDK.

### Added
- **web4.security** (U13) — Security primitives: `CryptoSuiteId`, `CryptoSuite`
  definitions (W4-BASE-1, W4-FIPS-1), `EncodingProfile`, suite negotiation,
  `W4ID` (DID:web4) parsing/validation/pairwise derivation, `KeyStorageLevel`,
  `KeyPolicy`, `SignatureEnvelope`, `VerifiableCredential`. Types and validation
  only — no crypto operations. 339 lines, 51 tests, 12 vectors.
- **web4.protocol** (U14) — Core protocol types: `HandshakePhase` (4-phase HPKE),
  `ClientHello`/`ServerHello`/`ClientFinished`/`ServerFinished` message types,
  `PairingMethod` (Direct/Mediated/QR), `Transport` with compliance levels and
  profiles, `DiscoveryMethod` with privacy levels, `Web4URI` parser/validator
  (RFC 3986 subset). Types only — no networking. 517 lines, 55 tests, 12 vectors.
- **web4.mcp** (U15) — MCP protocol types: `CommunicationPattern` (4 modes),
  `Web4Context` headers (trust context, agency proofs, MRH scope),
  `MCPToolResource`/`MCPPromptResource`, `TrustRequirements`, `MCPSession` with
  ATP tracking, `SessionHandoff`, `calculate_mcp_cost` (trust discounts, demand
  modifiers), `WitnessAttestation`, `MCPCapabilities`/`CapabilityBroadcast`,
  `MCPAuthority`, `MCPErrorContext`. Types only — no networking or JSON-RPC.
  584 lines, 43 tests, 12 vectors.
- `web4_sdk.py` re-exports for all 18 modules (17 security + 22 protocol +
  19 MCP symbols added).

### Changed
- Version bumped from 0.4.0 to 0.5.0 in `web4/__init__.py`.

## [0.4.0] - 2026-03-18

Major release: six new modules, two enhanced modules, 15 modules total.

### Added
- **web4.entity** (U5) — Entity type taxonomy: `BehavioralMode`, `EnergyPattern`,
  `InteractionType`, `EntityTypeInfo`, behavioral classification and interaction
  validation for all 16 entity types. 48 tests, 5 vectors.
- **web4.capability** (U6) — LCT capability levels: `CapabilityLevel` (6 levels
  from Stub to Hardware), `TrustTier`, `LevelRequirement`, level assessment,
  validation, upgrade eligibility, and entity-level range mapping. 42 tests, vectors.
- **web4.errors** (U7) — RFC 9457 error taxonomy: `ErrorCode` (24 codes),
  `ErrorCategory` (6 categories), `Web4Error` exception hierarchy with
  `BindingError`, `PairingError`, `WitnessError`, `AuthzError`, `CryptoError`,
  `ProtoError`. Problem Details serialization/deserialization. 42 tests, 5 vectors.
- **web4.metabolic** (U9) — Society metabolic states: `MetabolicState` (8 states),
  `Transition` (17 valid transitions), `TrustEffect`, `MetabolicProfile`,
  `ReliabilityFactors`. Energy cost calculation, wake penalty, witness requirements,
  dormancy classification. 71 tests, 12 vectors.
- **web4.binding** (U2) — Multi-device LCT binding: `AnchorType` (4 types),
  `DeviceStatus`, `HardwareAnchor`, `DeviceRecord`, `DeviceConstellation`.
  Constellation management (enroll/remove), trust computation (witness freshness,
  coherence bonus, cross-witness density, ceiling), recovery quorum. 68 tests, 6 vectors.
- **web4.society** (U11) — Society composition: `SocietyPhase`, `SocietyState`,
  `Treasury`, `SocietyLedger`, `LedgerEntry`. Composes federation, metabolic, atp,
  trust, lct, entity modules. Citizenship CRUD, metabolic gating, treasury ops,
  law recording, fractal hierarchy, aggregate trust. 86 tests, 6 vectors.
- `web4_sdk.py` re-exports for all 15 modules (metabolic added in v0.4.0 — was
  missing in prior releases). 22 new metabolic symbols, 21 society symbols.

### Changed
- **web4.trust** (U10) — T3/V3 tensor enhancements: `ActionOutcome` enum,
  outcome-based T3 evolution, decay/refresh, `RoleRequirement`, `V3.calculate()`,
  `compute_team_t3()`. 51 new tests, 5 vectors.
- **web4.federation** (U8) — SAL governance extensions: `CitizenshipStatus`
  (5 lifecycle states), `CitizenshipRecord`, `QuorumPolicy` (3 modes),
  `LedgerType`, `AuditRequest`, `AuditAdjustment`, `Norm`, `Procedure`,
  `Interpretation`, `merge_law()`. 29 new tests, 6 vectors.
- Version bumped from 0.3.0 to 0.4.0 in `web4/__init__.py`.

### Fixed
- `web4_sdk.py` was missing metabolic module re-exports (MetabolicState,
  energy_cost, etc.) despite the module being available since PR #23.

## [0.3.0] - 2026-03-16

### Added
- **web4.reputation** — Rule-based reputation computation engine:
  `ReputationRule`, `ReputationEngine`, `ReputationStore`, `Modifier`,
  `DimensionImpact`, `analyze_factors`. Implements rule-triggered reputation
  changes with conditional modifiers, time-weighted aggregation with
  exponential recency weighting, and inactivity decay with grace period
  and acceleration. Validated against `test-vectors/reputation/reputation-operations.json`.
- `web4_sdk.py` re-exports reputation module types (9 modules total).
- 5 cross-language test vectors for reputation computation.

## [0.2.0] - 2026-03-15

Added three new SDK modules and completed re-exports in `web4_sdk.py`.

### Added
- **web4.mrh** — Markov Relevancy Horizon graph: `MRHGraph`, `MRHNode`,
  `MRHEdge`, `RelationType`, trust decay and propagation functions.
  Validated against `test-vectors/mrh/graph-operations.json`.
- **web4.acp** — Agentic Context Protocol: `ACPStateMachine`, `AgentPlan`,
  `Intent`, `Decision`, `ExecutionRecord`, `ProofOfAgency`, approval modes,
  resource caps, guards, and plan validation.
  Validated against `test-vectors/acp/plan-operations.json`.
- **web4.dictionary** — Dictionary Entities: `DictionaryEntity`,
  `DictionarySpec`, `CompressionProfile`, `TranslationRequest`/`Result`/`Chain`,
  versioned evolution, and dictionary selection scoring.
  Validated against `test-vectors/dictionary/dictionary-operations.json`.
- `web4_sdk.py` now re-exports canonical types from all 8 modules
  (trust, lct, atp, federation, r6, mrh, acp, dictionary).
- Cross-module integration tests covering trust+lct+atp+federation workflows.
- Cross-language test vectors: 40 vectors across all modules.

### Changed
- Version bumped from 0.1.0 to 0.2.0 in `web4/__init__.py`.
- **web4.trust**: Renamed `coherence()`→`operational_health()` and
  `is_coherent()`→`is_healthy()` to avoid naming collision with the
  whitepaper's identity coherence framework (C×S×Phi×R). Constants
  `COHERENCE_WEIGHTS`/`COHERENCE_THRESHOLD` renamed to
  `HEALTH_WEIGHTS`/`HEALTH_THRESHOLD`. Behavior unchanged.
- **web4_sdk.py**: `ReputationScore.coherence_score` renamed to
  `ReputationScore.health_score`.

## [0.1.0] - 2026-03-13

Initial SDK release with four core modules.

### Added
- **web4.trust** — T3/V3 trust and value tensors, operational health scoring,
  trust profiles, composite calculations.
- **web4.lct** — Linked Context Tokens: `LCT`, `EntityType` (16 canonical
  types with alias map), `BirthCertificate`, `RevocationStatus`.
- **web4.atp** — ATP/ADP lifecycle: `ATPAccount`, energy ratio, transfer,
  discharge, and conservation verification.
- **web4.federation** — Federation governance (SAL): `Society`, `LawDataset`,
  `Delegation`, `RoleType`.
- **web4.r6** — R7 action framework: `R7Action`, `ActionChain`, `Rules`,
  `Role`, `Request`, `ResourceRequirements`, `Result`, `ReputationDelta`.
- `web4_sdk.py` REST client with re-exports for trust, lct, atp, federation,
  and r6 modules.
- 5 Turtle ontologies (T3V3, ACP, AGY, SAL, Core) defining 25 classes and
  60 properties.
