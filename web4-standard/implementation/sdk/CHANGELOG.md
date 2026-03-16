# Changelog

All notable changes to the Web4 Python SDK.

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
