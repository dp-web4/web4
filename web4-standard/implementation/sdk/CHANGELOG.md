# Changelog

All notable changes to the Web4 Python SDK.

## [0.19.0] - 2026-04-05

Sprints 18-20: CLI conformance tooling, trust query data types, and document generation.

### Added
- **Document generation** (Sprint 20 T1) — new `web4/generate.py` module (22nd SDK module).
  `generate(type_name)` produces minimal valid JSON-LD documents for any of 23 supported
  types. Also provides `generate_string()`, `available_types()`, and `UnsupportedTypeError`.
  CLI subcommand `web4 generate <type>` with `--compact` and `--list` flags. 102 tests.
- **Trust query data types** (Sprint 19 T1) — `TrustQuery`, `TrustQueryResponse`, and
  `DisclosureLevel` in `web4/trust.py`. ATP-staked trust information requests with
  validation (minimum stake, validity period bounds). `to_dict()`/`from_dict()` round-trips,
  `to_jsonld()`/`from_jsonld()` for JSON-LD dispatch. Registered in deserialize dispatcher
  (23 types, up from 22). 7 new exports, 35 tests.
- **CLI `web4 roundtrip` command** (Sprint 18 T1) — reads a JSON-LD document, deserializes
  via `from_jsonld()`, re-serializes via `to_jsonld()`, outputs normalized result. `--check`
  flag for semantic comparison with diff output. Supports stdin via `-`. 10 tests.
- **JSON-LD lifecycle integration tests** (Sprint 18 T2) — 67 integration tests exercising
  the full SDK pipeline: create → `to_jsonld()` → `validate()` → `from_jsonld()` → verify
  round-trip fidelity. Covers all 21 dispatcher types and 19 schema-validated types.

### Changed
- Version bumped from 0.18.0 to 0.19.0.
- 2459 tests passing (up from 2245 in v0.18.0). 22 SDK modules, 359 exports.
- CLI now has 5 subcommands: `info`, `validate`, `list-schemas`, `roundtrip`, `generate`.
- Deserialize dispatcher covers 23 types (up from 22).

## [0.18.0] - 2026-04-04

Sprint 16: mypy strict zero-error and generic JSON-LD deserialization.

### Added
- **Generic JSON-LD deserialization** (T2) — new `web4/deserialize.py` module (21st SDK
  module). Top-level `from_jsonld(doc)` dispatches any JSON-LD document to the correct
  class by `@type` field. Covers 22 types across 10 modules (19 class-based + 3
  function-based). Also provides `from_jsonld_string(s)`, `supported_types()`, and
  `UnknownTypeError`. 62 parametrized tests.
- **mypy strict zero-error** (T1) — `mypy --strict web4/` now reports 0 errors across
  23 source files. Added `[tool.mypy]` config with `strict = true` and override for
  `jsonschema.*` (ignore_missing_imports) in `pyproject.toml`.
- **Test coverage baseline** (T1) — 96.2% overall (4491 statements, 169 missed). 4
  modules at 100%, 16 at 95%+.

### Changed
- Version bumped from 0.17.0 to 0.18.0.
- 2245 tests passing (up from 2183 in v0.17.0). 21 SDK modules, 348 exports.

## [0.17.0] - 2026-04-04

from_dict() round-trip completeness and schema validation vector integration.

### Added
- **from_dict() round-trip completeness** (N1-R1, S1) — 35 new `from_dict()` classmethods
  across 8 modules. Every class with `to_dict()` or `as_dict()` now has a matching
  `from_dict()` for lossless round-trip serialization:
  - security.py (N1): W4ID, KeyPolicy, SignatureEnvelope, VerifiableCredential (4 methods, 16 tests)
  - r6.py (O1): Constraint, Rules, Role, ProofOfAgency, Request, Precedent,
    WitnessAttestation, Reference, ResourceRequirements, Result, TensorDelta,
    ContributingFactor (12 methods, 32 tests)
  - reputation.py + protocol.py (P1): ReputationRule, HandshakeMessage (2 methods, 8 tests)
  - acp.py (Q1): PlanStep, AgentPlan, Intent, Decision, ExecutionRecord (5 methods, 18 tests)
  - lct.py (R1): Binding, MRHPairing, MRH, BirthCertificate, Attestation, LineageEntry,
    Policy, LCT (8 methods, 27 tests)
  - trust.py (S1): T3, V3 (2 methods, 16 tests)
  - mrh.py (S1): MRHNode, MRHEdge (2 methods, 11 tests)
- **Schema validation vectors in pytest** (M1) — 278 cross-language validation vectors
  (92 valid + 186 invalid across 9 schemas) integrated into the pytest suite. Vectors
  run as parametrized tests, replacing the standalone validation runner script.

### Changed
- Version bumped from 0.16.0 to 0.17.0.
- 2183 tests passing (up from 1770 in v0.16.0). 20 SDK modules, 344 exports.

## [0.16.0] - 2026-03-29

Sprints 13 and 14: CLI module and distribution polish.

### Added
- **CLI module** (J1) — `web4/__main__.py` with 3 subcommands: `info`, `validate`,
  `list-schemas`. Schema auto-detection from `@type` field (30+ type mappings).
  Stdin support. Console script entry point (`web4` command). 22 tests.
- **`validation` optional extra** (K1) — `pip install web4[validation]` installs
  just `jsonschema` without the full dev toolchain. Error messages in both
  `validation.py` and CLI now suggest `web4[validation]` instead of `web4[dev]`.

### Changed
- README.md updated to reflect v0.16.0 status: 20 modules, 344 exports, 1770 tests,
  CLI documentation, validation extra installation instructions.
- Version bumped from 0.15.0 to 0.16.0.

## [0.15.0] - 2026-03-29

Sprints 11 and 12: Code Quality Gates and Schema Validation Integration.

### Added
- **Schema validation module** (H1) — `web4/validation.py`: 20th SDK module
  providing runtime validation of JSON-LD documents against the project's JSON
  Schemas. Public API: `validate()`, `list_schemas()`, `get_schema()`,
  `get_schema_dir()`, `ValidationResult`, `ValidationError`,
  `SchemaValidationUnavailable`, `SchemaNotFound`.
  Schema directory auto-detected via repo-relative walk (with
  `WEB4_SCHEMA_DIR` env override). 12 named schemas (9 JSON-LD + 3 standalone).
  33 tests covering all schema types, error handling, caching, and directory
  resolution. `jsonschema` as optional dependency with graceful degradation.

### Changed
- **SDK README coherence update** (G4) — README.md rewritten to accurately
  document the `web4` package (19→20 modules, 336→344 exports, v0.14.0→0.15.0)
  instead of the legacy `web4_sdk.py` async HTTP client.
- **Mypy strict compliance** (G3) — 65 type fixes across 13 SDK modules.
  `mypy --strict web4/` passes with 0 errors.
- Version bumped from 0.14.0 to 0.15.0.
- 1748 tests passing. 20 SDK modules, 344 exports.

## [0.14.0] - 2026-03-28

Sprint 10 completion: CI/CD & Packaging Quality — automated test verification,
packaging metadata improvements, and single-source version management.

### Added
- **GitHub Actions CI workflow** (F1) — `.github/workflows/sdk-test.yml` runs
  full pytest suite across Python 3.10-3.13 matrix on push/PR to SDK paths.
  Zero external dependencies beyond pytest.
- **Packaging metadata improvements** (F2) — `[project.urls]` with Homepage,
  Repository, Issues, Changelog links. 10 PyPI keywords. `MANIFEST.in` for
  sdist inclusion of LICENSE, README.md, CHANGELOG.md, py.typed. MIT LICENSE
  file added to SDK directory.
- **Single-source version management** (F3) — `pyproject.toml` is now the
  single source of truth for version. `__init__.py` reads version via
  `importlib.metadata.version("web4")` with fallback. Redundant `setup.py`
  removed — `pyproject.toml` with setuptools ≥64 is sufficient.

### Fixed
- **CI test dependency** — Added `jsonschema>=4.0` to `[project.optional-dependencies]`
  dev extras so `test_jsonld_schema_roundtrip.py` runs in CI (was failing with
  `ModuleNotFoundError: No module named 'jsonschema'` across all Python versions).

### Changed
- Version bumped from 0.13.0 to 0.14.0.
- Sprint 10 complete (4/4 tasks: F1-F4 all DONE). 1715 tests passing.

## [0.13.0] - 2026-03-27

Sprint 9 completion: SDK Documentation Completeness — docstring coverage for all
public methods and return type annotations across the entire SDK.

### Added
- **Docstring coverage for r6, mrh, security** (E1) — 32 docstrings across 3
  modules: r6.py (19 methods, 69% → 95%), mrh.py (8 methods, 72% → 94%),
  security.py (5 methods, 77% → 82%). All `to_dict()`, property accessors,
  and public methods now documented.
- **Docstring coverage for reputation, protocol, acp** (E2) — 17 docstrings
  across 3 modules: reputation.py (3), protocol.py (5), acp.py (9). All 6
  documentation-gap modules now above 80% coverage on public API.
- **Return type annotations** (E3) — 33 `-> None` annotations added across 5
  modules: acp.py (15), federation.py (8), dictionary.py (4), trust.py (4),
  lct.py (2). All public methods, `__init__`, and `__post_init__` now have
  return type annotations for mypy/IDE support.

### Changed
- Version bumped from 0.12.0 to 0.13.0.
- Sprint 9 complete (4/4 tasks: E1-E4 all DONE). 1715 tests passing.

## [0.12.0] - 2026-03-26

Sprint 8 completion: SDK Developer Experience — export completeness, submodule
`__all__` declarations, and docstring coverage.

### Added
- **Export completeness** (D1) — 52 public symbols across 10 modules added to
  `web4/__init__.py` that were previously accessible only via direct submodule
  import: ATP core operations (5 functions), R7 exceptions + component classes
  (13 symbols), ACP exceptions + guard (9 symbols), Federation serialization
  helpers (12 functions), Dictionary types (4 classes), Trust utilities (3
  symbols), LCT sub-types (4 aliases), Entity lookup (1 function), MRH helper
  (1 function). 336 total exports, up from 284.
- **Submodule `__all__` declarations** (D2) — All 19 SDK submodules now have
  `__all__` lists (375 total symbols across submodules), enabling correct
  `from web4.trust import *` behavior and IDE autocomplete for submodule
  imports. 21 new consistency tests verify all entries resolve, no duplicates,
  and root imports are covered.
- **Docstring coverage for mcp.py** (D3) — All 32 previously undocumented
  `to_dict()` and `from_dict()` methods in `web4.mcp` now have docstrings
  describing serialized format and key behaviors. Module documentation
  coverage: 13.5% → 100% (56/56 public symbols).

### Changed
- Version bumped from 0.11.0 to 0.12.0.
- Sprint 8 complete (4/4 tasks: D1-D4 all DONE). 1715 tests passing.

## [0.11.0] - 2026-03-26

Sprint 7 completion: SDK API completeness — missing `from_jsonld()` inverses,
ATP core unit tests, and BirthCertificate field harmonization.

### Added
- **Missing `from_jsonld()` inverse functions** (C1) — 3 module-level
  serialization functions that previously only had `to_jsonld()` now have
  full round-trip support: `entity_registry_from_jsonld()` /
  `entity_registry_from_jsonld_string()` in `web4.entity`,
  `capability_assessment_from_jsonld()` /
  `capability_assessment_from_jsonld_string()` in `web4.capability`,
  `capability_framework_from_jsonld()` /
  `capability_framework_from_jsonld_string()` in `web4.capability`.
  New `CapabilityAssessment` dataclass. 7 new exports (284 total).
  14 new tests with roundtrip validation.
- **ATP core unit tests** (C2) — 74 tests in `test_atp.py` covering all 8
  ATP public functions/classes: `ATPAccount` construction, `energy_ratio`,
  `transfer`, `sliding_scale`, `recharge`, conservation invariants, edge
  cases, and all 15 cross-language ATP test vectors. Previously only
  JSON-LD serialization tests existed.
- **Dictionary JSON-LD validation vectors** — 50 vectors (17 valid + 33
  invalid) for the Dictionary JSON-LD schema, completing cross-language
  coverage for all 9 schemas (278 total vectors).

### Changed
- **BirthCertificate field rename** (C3) — `BirthCertificate.context` renamed
  to `BirthCertificate.birth_context` to align with LCT spec §2.3 and JSON-LD
  output field naming. Breaking change for direct `.context` access; backward
  compatible in `from_jsonld()` (accepts both field names). 9 files modified.
- Version bumped from 0.10.1 to 0.11.0.
- Sprint 7 complete (4/4 tasks: C1-C4 all DONE). 1659 tests passing.

## [0.10.1] - 2026-03-24

Sprint 6 completion: JSON-LD context consolidation, namespace reconciliation,
and schema-validated round-trip tests across all 19 serializable types.

### Added
- **Missing JSON-LD context files** (B2) — `lct.jsonld` (30+ term mappings)
  and `attestation-envelope.jsonld` (25+ term mappings) in `schemas/contexts/`.
  These were the last 2 types without external `.jsonld` context files. 26
  consistency tests verifying all `to_jsonld()` keys have context mappings.
- **Schema-validated JSON-LD round-trip tests** (B4) —
  `test_jsonld_schema_roundtrip.py` with 48 integration tests covering all 9
  JSON-LD schemas and 19 distinct `@type` values. Pattern: construct object →
  `to_jsonld()` → validate against JSON Schema → `from_jsonld()` → assert
  field equality. Types covered: LCT, AttestationEnvelope, T3Tensor, V3Tensor,
  R7Action, ATPAccount, TransferResult, AgentPlan, Intent, Decision,
  ExecutionRecord, EntityTypeInfo, EntityTypeRegistry, LevelRequirement,
  CapabilityAssessment, CapabilityFramework, DictionarySpec, TranslationResult,
  TranslationChain.

### Changed
- **JSON-LD namespace reconciliation** (B3) — All 10 JSON-LD context files now
  use `https://web4.io/ns/` as canonical namespace. Created 3 new context files
  (`t3.jsonld`, `v3.jsonld`, `r7-action.jsonld`) in `schemas/contexts/` using
  `ns/` namespace. T3/V3 constants updated; `ontology#` reserved for OWL/RDF
  class definitions only. Decision documented in
  `docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md`. 32
  consistency tests.
- Version bumped from 0.10.0 to 0.10.1.
- Sprint 6 complete (6/6 tasks: B1-B6 all DONE). 1571 tests passing.

## [0.10.0] - 2026-03-23

Sprint 5 completion and Sprint 6 start: Entity + Capability JSON-LD, full
cross-language validation vectors, Dictionary JSON-LD, and Sprint 6 planning.

### Added
- **Entity + Capability JSON-LD serialization** (A3) — `EntityTypeInfo.to_jsonld()`
  and `from_jsonld()`, `entity_registry_to_jsonld()` for full registry serialization.
  `LevelRequirement.to_jsonld()` and `from_jsonld()`, `capability_assessment_to_jsonld()`,
  `capability_framework_to_jsonld()`. JSON Schemas (`entity-jsonld.schema.json`,
  `capability-jsonld.schema.json`). JSON-LD contexts (`entity.jsonld`, `capability.jsonld`).
  37 new tests.
- **Cross-language validation vectors completed** (A4, complete) — 68 additional
  vectors for Entity (32: 12 valid + 20 invalid for EntityTypeInfo and
  EntityTypeRegistry) and Capability (36: 12 valid + 24 invalid for
  LevelRequirement, CapabilityAssessment, CapabilityFramework). Total: 127 Phase 2
  vectors across 4 schemas (ATP 23 + ACP 36 + Entity 32 + Capability 36). Grand
  total: 228 cross-language validation vectors across all 8 JSON-LD schemas.
- **Dictionary JSON-LD serialization** (B6) — `DictionarySpec.to_jsonld()` and
  `from_jsonld()`, `TranslationResult.to_jsonld()` and `from_jsonld()`,
  `TranslationChain.to_jsonld()` and `from_jsonld()`, `DictionaryEntity.to_jsonld()`
  and `from_jsonld()`. JSON Schema (`dictionary-jsonld.schema.json`). JSON-LD context
  (`contexts/dictionary.jsonld`). 14 new tests.
- 6 new exports from `web4` package: `ENTITY_JSONLD_CONTEXT`,
  `entity_registry_to_jsonld`, `CAPABILITY_JSONLD_CONTEXT`,
  `capability_assessment_to_jsonld`, `capability_framework_to_jsonld`,
  `DICTIONARY_JSONLD_CONTEXT`.

### Changed
- Version bumped from 0.9.0 to 0.10.0.
- 277 public API symbols in `__all__` (up from 269). All 8 core types plus Dictionary
  now have JSON-LD serialization with JSON Schemas. Sprint 6 planned for JSON-LD
  context consolidation and namespace reconciliation.

## [0.9.0] - 2026-03-22

Sprint 5: Core Type JSON-LD Phase 2 — ATP/ADP and ACP JSON-LD serialization
with cross-language validation vectors.

### Added
- **ATP/ADP JSON-LD serialization** (A1) — `ATPAccount.to_jsonld()` and
  `from_jsonld()`, `TransferResult.to_jsonld()` and `from_jsonld()`. JSON
  Schema (`atp-jsonld.schema.json`) and JSON-LD context (`contexts/atp.jsonld`).
  28 new tests.
- **ACP JSON-LD serialization** (A2) — `AgentPlan.to_jsonld()` /
  `from_jsonld()`, `Intent.to_jsonld()` / `from_jsonld()`, `Decision.to_jsonld()`
  / `from_jsonld()`, `ExecutionRecord.to_jsonld()` / `from_jsonld()`. JSON Schema
  (`acp-jsonld.schema.json`) with 4 type definitions and 6 reusable sub-schemas.
  JSON-LD context (`contexts/acp.jsonld`). 54 new tests.
- **Cross-language validation vectors** (A4, partial) — 59 vectors across 2
  schemas: ATP (23 vectors: 8 valid + 15 invalid for ATPAccount and
  TransferResult) and ACP (36 vectors: 12 valid + 24 invalid for AgentPlan,
  Intent, Decision, ExecutionRecord). Covers missing required fields, invalid
  enums, out-of-range values, type errors, additionalProperties violations,
  and boundary values.
- `TransferResult`, `ATP_JSONLD_CONTEXT`, and `ACP_JSONLD_CONTEXT` exported
  from `web4` package.

### Changed
- Version bumped from 0.8.0 to 0.9.0 in `web4/__init__.py`, `pyproject.toml`,
  and `setup.py`.
- 269 public API symbols in `__all__` (up from 266).

## [0.8.0] - 2026-03-21

Sprint 4: Cross-Language Schema Standardization — JSON Schemas, R7 Action
JSON-LD serialization, and cross-language validation test vectors.

### Added
- **JSON Schema for LCT JSON-LD** (V1) — `lct-jsonld.schema.json` (JSON Schema
  draft 2020-12) validating LCT `to_jsonld()` output against spec §2.3. 10
  validation checks. Schema covers `@context`, `@type`, birth certificate,
  MRH entries, attestations, lineage, and revocation structure.
- **JSON Schema for AttestationEnvelope JSON-LD** (V1) — `attestation-envelope-jsonld.schema.json`
  validating AttestationEnvelope `to_jsonld()` output. 9 validation checks.
  Covers anchor info, proof, platform state, trust ceiling, and freshness model.
- **R7 Action JSON-LD serialization** (V3) — `R7Action.to_jsonld()` and
  `from_jsonld()` for all 7 R7 components (Rules/Role/Request/Reference/
  Resource/Result/Reputation). `ReputationDelta.to_jsonld()` / `from_jsonld()`,
  `ActionChain.to_jsonld()` / `from_jsonld()`. JSON-LD context document
  (`r7-action.jsonld`) and JSON Schema (`r7-action-jsonld.schema.json`).
  26 new tests.
- **Cross-language schema validation test vectors** (V4, partial) — 63 vectors
  across 3 schemas: LCT (23), AttestationEnvelope (20), R7 Action (20). Each
  set includes valid documents and invalid documents exercising missing required
  fields, enum violations, range violations, pattern mismatches, type errors,
  and boundary values. Language-agnostic validation runner script. T3/V3
  vectors deferred pending PR #54.
- `R7_JSONLD_CONTEXT` and `ATTESTATION_JSONLD_CONTEXT` constants exported from
  `web4` package.
- `Society` re-exported directly (was only available as `FederationSociety` alias).

### Changed
- Version bumped from 0.7.0 to 0.8.0 in `web4/__init__.py`, `pyproject.toml`,
  and `setup.py`.
- 266 public API symbols in `__all__` (up from 263).

## [0.7.0] - 2026-03-20

Sprint 3: SDK Interoperability — JSON-LD serialization for spec-compliant
cross-language data exchange.

### Added
- **LCT JSON-LD serialization** (I1) — `LCT.to_jsonld()` and `LCT.from_jsonld()`
  producing documents matching spec §2.3 canonical structure. Includes `@context`
  header, spec-compliant field naming (`birth_context` not `context`), structured
  MRH entries (bound/witnessing as objects), optional sections (attestations,
  lineage) included only when populated, full revocation structure. New types:
  `Attestation`, `LineageEntry`, `LCT_JSONLD_CONTEXT`. `BirthCertificate` gains
  optional `genesis_block_hash`. `LCT.revoke()` gains optional `reason` parameter.
  Backward compatible: `to_dict()` unchanged, `from_jsonld()` accepts both formats.
  51 new tests. Closes known gap "NO Python impl produces schema-compliant LCT
  document."
- **Cross-language LCT JSON-LD test vectors** (I2) — 10 vectors covering minimal,
  full, revoked, suspended, attestations, lineage, complex MRH, boundary T3/V3,
  genesis block hash, and no-birth-certificate scenarios. 110 validation tests
  verify roundtrip fidelity, structural compliance, and spec §2.3 adherence.
- **AttestationEnvelope JSON-LD serialization** (I3) — `AttestationEnvelope.to_jsonld()`
  and `from_jsonld()` matching the attestation-envelope spec format. 41 tests.

### Changed
- Version bumped from 0.5.0 to 0.7.0 in `web4/__init__.py`, `pyproject.toml`,
  and `setup.py`.
- 263 public API symbols in `__all__` (up from 250).

## [0.6.0] - 2026-03-19

Hardware trust attestation module, completing Sprint 2 (Hardware Trust Validation).

### Added
- **web4.attestation** (H4) — AttestationEnvelope: unified hardware trust
  primitive binding TPM attestation + LCT presence + T3/V3 trust into a single
  verifiable structure. `AttestationEnvelope` (construction, auto-computed
  fingerprint, trust ceiling per anchor type, freshness model with configurable
  max age), `AnchorInfo` (anchor type + metadata), `Proof` (nonce, challenge,
  signature, PCR values), `PlatformState` (firmware, secure boot, integrity),
  `VerificationResult` (verified flag + details + timestamp), `verify_envelope()`
  dispatcher with 4 anchor verifiers (software, TPM2, FIDO2, secure enclave),
  `TRUST_CEILINGS` (per-anchor-type maximums: software 0.7, TPM2 0.95, FIDO2
  0.85, secure enclave 0.9), `FRESHNESS_MAX_AGE` (24h default). 370 lines,
  41 tests.
- 8 new symbols in `web4/__init__.py` (255 total exports): `AttestationEnvelope`,
  `AnchorInfo`, `Proof`, `PlatformState`, `VerificationResult`, `TRUST_CEILINGS`,
  `FRESHNESS_MAX_AGE`, `verify_envelope`.

### Changed
- Version bumped from 0.5.0 to 0.6.0 in `web4/__init__.py`, `pyproject.toml`,
  `setup.py`.

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
