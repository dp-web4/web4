# Web4 Sprint Plan

**Created**: 2026-03-14
**Updated**: 2026-03-27 (Sprint 10 started)
**Phase**: Development
**Track**: web4 (Legion)

---

## Sprint 10: CI/CD & Packaging Quality (2026-03-27)

Sprints 4-9 built a comprehensive SDK: 19 modules, 336 exports, 1715 tests, 278 cross-language
validation vectors, full docstrings and type annotations. However, none of this is verified in
CI — there are no GitHub Actions workflows. This sprint adds automated test verification and
improves packaging metadata so the SDK is ready for external distribution.

### F1: GitHub Actions CI workflow
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: None
**Scope**: Create `.github/workflows/sdk-test.yml` that runs the full pytest suite across
Python 3.10-3.13 on push/PR to SDK paths. Zero external dependencies — only pytest needed.

### F2: Packaging metadata improvements
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: None
**Scope**: Add project URLs (homepage, repository, issues, changelog) to `pyproject.toml`.
Add keywords for PyPI discoverability. Ensure `MANIFEST.in` includes README, CHANGELOG, and
`py.typed` in sdist. Add LICENSE file to SDK directory.
**Result**: Added `[project.urls]` (Homepage, Repository, Issues, Changelog), 10 keywords,
`MANIFEST.in` (LICENSE, README.md, CHANGELOG.md, py.typed), MIT LICENSE file. 1715 tests
passing, zero regressions.

### F3: Single-source version management
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: None
**Scope**: Version is currently hardcoded in 3 places (`pyproject.toml`, `setup.py`,
`__init__.py`). Use `importlib.metadata` or a shared `_version.py` to eliminate sync risk.
Remove redundant `setup.py` if `pyproject.toml` is sufficient.
**Result**: `pyproject.toml` is now the single source of truth. `__init__.py` reads version
via `importlib.metadata.version("web4")` with fallback. Redundant `setup.py` removed —
`pyproject.toml` with setuptools ≥64 is sufficient. 1715 tests passing, zero regressions.

### F4: SDK v0.14.0 release housekeeping
**Status**: TODO
**Depends on**: F1 (at minimum)
**Scope**: Version bump 0.13.0 → 0.14.0, CHANGELOG.md entry documenting Sprint 10
deliverables.

---

## Sprint 9: SDK Documentation Completeness (2026-03-26)

Sprint 8 completed docstring coverage for mcp.py (the worst module at 13.5% → 100%). An
SDK-wide audit reveals 6 more modules below 90% docstring coverage, totaling ~51 undocumented
public methods. Additionally, 21 public methods across 5 modules lack return type annotations.
This sprint closes remaining documentation gaps so the SDK is fully self-documenting for
external consumers.

### E1: Docstring coverage for r6.py, mrh.py, security.py
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: None
**Scope**: Add docstrings to all undocumented public methods in the three worst-documented
modules: r6.py (19 methods at 69% coverage), mrh.py (7 methods at 72%), security.py
(4 methods at 77%). Total: ~30 methods. Focus on `to_dict()` methods explaining serialization
format, and property accessors explaining what they return.
**Result**: 32 docstrings added across 3 modules. r6.py: 95.4% (62/65), mrh.py: 93.5%
(29/31), security.py: 81.5% (22/27). Remaining undocumented are dunder/private methods
(__init__, __post_init__, __eq__, __hash__, __str__, _generate_id). 1715 tests passing,
zero regressions.

### E2: Docstring coverage for reputation.py, protocol.py, acp.py
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: None
**Scope**: Add docstrings to remaining undocumented public methods in reputation.py
(3 methods at 81%), protocol.py (5 methods at 84%), acp.py (11 methods at 84%).
Total: ~19 methods.
**Result**: 17 docstrings added across 3 modules (reputation.py: 3, protocol.py: 5,
acp.py: 9). 2 of the original 11 acp.py symbols were inner functions (visit, dfs) —
not public API. 1715 tests passing, zero regressions.

### E3: Return type annotations for public methods
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: None
**Scope**: Add return type annotations to all public methods across 5 modules (acp.py,
federation.py, lct.py, dictionary.py, trust.py) that currently lack them.
Improves static analysis, IDE support, and mypy compatibility.
**Result**: 33 `-> None` annotations added across 5 modules: acp.py (15), federation.py (8),
dictionary.py (4), trust.py (4), lct.py (2). Covers public methods, `__init__`, and
`__post_init__`. 1715 tests passing, zero regressions.

### E4: SDK v0.13.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: E1 (at minimum)
**Scope**: Version bump 0.12.0 → 0.13.0, CHANGELOG.md entry documenting Sprint 9
deliverables.
**Result**: Version bumped in __init__.py, pyproject.toml, setup.py. CHANGELOG.md
documents E1-E4 deliverables. Sprint 9 complete (4/4 tasks).

---

## Sprint 8: SDK Developer Experience (2026-03-26)

Sprints 1-7 built the full SDK (19 modules, 284 exports, 1659 tests, 278 cross-language
validation vectors, 10 JSON-LD schemas with bidirectional roundtrip). An internal audit
reveals developer experience gaps: 48 public symbols not exported from the package root,
all 19 submodules missing `__all__` declarations, and several modules with incomplete
docstring coverage. This sprint closes DX gaps to prepare the SDK for external consumers.

### D1: Export completeness — missing public symbols
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: None
**Scope**: Add 52 public symbols across 10 modules to `web4/__init__.py` that were
previously accessible only via direct submodule import:
- ATP core operations: `transfer`, `sliding_scale`, `check_conservation`, `sybil_cost`,
  `fee_sensitivity` (5 functions)
- R7 exceptions + component classes: `R7Error` + 7 subclasses, `Constraint`, `Reference`,
  `Precedent`, `TensorDelta`, `ContributingFactor` (13 symbols)
- ACP exceptions + guard: `NoValidGrant`, `ScopeViolation`, `ApprovalRequired`,
  `WitnessDeficit`, `PlanExpired`, `LedgerWriteFailure`, `InvalidTransition`,
  `ResourceCapExceeded`, `HumanApproval` (9 symbols)
- Federation serialization: 6 `_to_dict` + 6 `_from_dict` functions for Norm, Procedure,
  Interpretation, LawDataset, Delegation, QuorumPolicy (12 functions)
- Dictionary types: `AmbiguityHandling`, `ChainStep`, `EvolutionConfig`, `FeedbackRecord`
  (4 classes)
- Trust utilities: `RoleTensors`, `trust_bridge`, `diminishing_returns` (3 symbols)
- LCT sub-types (aliased): `LCTBinding`, `LCTMRH`, `LCTMRHPairing`, `LCTPolicy` (4 aliases)
- Entity lookup: `get_info` (1 function)
- MRH helper: `relation_category` (1 function)
**Result**: 52 new exports (284 → 336 total). 35 new tests in `test_package_api.py`
with roundtrip validation for federation helpers and functional tests for ATP operations.
1694 tests passing, zero regressions.

### D2: Submodule `__all__` declarations
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: D1
**Scope**: Add `__all__` list to each of the 19 submodules (`trust.py`, `lct.py`, etc.)
so that `from web4.trust import *` works correctly and IDEs can autocomplete submodule
imports. Extract the symbol list from the corresponding `web4/__init__.py` import group
plus any module-internal public symbols.
**Result**: All 19 submodules now have `__all__` declarations (375 total symbols across
submodules). 21 new tests in `test_package_api.py` verify consistency (all entries resolve,
no duplicates, submodule count). 1715 tests passing, zero regressions.

### D3: Docstring coverage for mcp.py
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: None
**Scope**: Add docstrings to the 32 undocumented public functions/methods in `web4/mcp.py`.
This module has the worst documentation coverage (13.5%) in the SDK. Focus on class-level
docstrings, constructor parameters, and return types.
**Result**: All 32 previously undocumented `to_dict()` and `from_dict()` methods now have
docstrings. Coverage went from 13.5% to 100% (56/56 public symbols documented).
1715 tests passing, zero regressions.

### D4: SDK v0.12.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: D1 (at minimum)
**Scope**: Version bump 0.11.0 → 0.12.0, CHANGELOG.md entry documenting Sprint 8
deliverables.
**Result**: Version bumped in `__init__.py`, `pyproject.toml`, `setup.py`. CHANGELOG.md
v0.12.0 section documents D1 (export completeness), D2 (submodule `__all__`), D3
(mcp.py docstrings). Sprint 8 complete (4/4 tasks). 1715 tests passing.

---

## Sprint 7: SDK API Completeness (2026-03-24)

Sprints 3-6 delivered JSON-LD serialization for all 10 core types with schemas, context
files, and 278 cross-language validation vectors. However, an API audit reveals asymmetries:
3 module-level `to_jsonld()` functions lack `from_jsonld()` inverses (write-only export),
the ATP module has no direct unit tests, and `BirthCertificate.context` diverges from the
spec's `birth_context` field name. This sprint closes these API gaps before v0.11.0.

### C1: Missing from_jsonld() inverse functions
**Status**: DONE
**Completed**: 2026-03-24
**Depends on**: None
**Scope**: Add `from_jsonld()` counterparts for the 3 module-level serialization functions
that currently only have `to_jsonld()`:
1. `entity_registry_from_jsonld(doc)` → `Dict[EntityType, EntityTypeInfo]` in `web4/entity.py`
2. `capability_assessment_from_jsonld(doc)` → assessment dict in `web4/capability.py`
3. `capability_framework_from_jsonld(doc)` → framework dict in `web4/capability.py`

Schemas already specify the format (`entity-jsonld.schema.json`, `capability-jsonld.schema.json`).
Export new functions from `web4/__init__.py`. Add roundtrip tests.
**Result**: 3 `from_jsonld()` inverses plus 3 `from_jsonld_string()` convenience wrappers.
New `CapabilityAssessment` dataclass. 7 new exports (284 total). 14 new tests with roundtrip
validation. PR #81, merged.

### C2: ATP core unit tests
**Status**: DONE
**Completed**: 2026-03-25
**Depends on**: None
**Scope**: Create `tests/test_atp.py` with direct unit tests for core ATP operations
(transfer, sliding_scale, recharge, conservation invariants). Currently only JSON-LD
serialization tests exist (`test_atp_jsonld.py`). Follow `test_acp.py` pattern.
**Result**: 74 tests covering all 8 ATP public functions/classes. Validates all 15
cross-language ATP test vectors. PR #82, merged.

### C3: BirthCertificate field naming harmonization
**Status**: DONE
**Completed**: 2026-03-25
**Depends on**: None
**Scope**: Rename `BirthCertificate.context` → `BirthCertificate.birth_context` to align
with LCT spec §2.3 and JSON-LD output. The field currently uses `context` internally but
serializes as `birth_context` — creating asymmetric round-trips. Breaking change requiring
`from_jsonld()` backward compatibility (accept both field names).
**Result**: 9 files modified, 34-line symmetric diff. `from_jsonld()` retains backward
compat (accepts both field names). 1571 tests passing, zero regressions. PR #83, merged.

### C4: SDK v0.11.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: C1 (at minimum)
**Scope**: Version bump 0.10.1 → 0.11.0, CHANGELOG.md entry documenting Sprint 7
deliverables.
**Result**: Version bumped in `__init__.py`, `pyproject.toml`, `setup.py`. CHANGELOG.md
v0.11.0 section documents C1 (from_jsonld inverses), C2 (ATP unit tests), C3
(BirthCertificate rename), Dictionary validation vectors. Sprint 7 complete (4/4 tasks).
1659 tests passing.

---

## Sprint 6: JSON-LD Context Consolidation & SDK Quality (2026-03-23)

Sprints 3-5 delivered JSON-LD serialization for all 8 core types with JSON Schemas
and 228 cross-language test vectors. However, an audit reveals inconsistencies in the
JSON-LD context layer: 2 missing context files, a namespace split (`ontology#` vs `ns/`),
and no programmatic schema validation in the SDK. This sprint consolidates the JSON-LD
foundation before building on it.

### B1: SDK v0.10.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: None
**Scope**: Update CHANGELOG.md to document A3 (Entity+Capability JSON-LD, 5 new exports),
A4 complete (127 total vectors, up from 59 partial documented in v0.9.0), and B6
(Dictionary JSON-LD). Bump SDK version 0.9.0 → 0.10.0.
**Result**: CHANGELOG v0.10.0 entry documents A3, A4 complete, and B6. Version bumped
in `__init__.py`, `pyproject.toml`, `setup.py`. 277 symbols in `__all__` (up from 269).
1465 tests passing.

### B2: Missing JSON-LD context files for LCT and AttestationEnvelope
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: None
**Scope**: Create `lct.jsonld` and `attestation-envelope.jsonld` context files in
`web4-standard/schemas/contexts/`. LCT and AttestationEnvelope Python constants
(`LCT_JSONLD_CONTEXT`, `ATTESTATION_JSONLD_CONTEXT`) reference context URIs that don't
exist as files. All other 6 types have external context files. These 2 are the gap.
Extract term mappings from the Python `to_jsonld()` output and create context files
matching the pattern used by ATP/ACP/Entity/Capability contexts (namespace: `https://web4.io/ns/`).
**Result**: 2 `.jsonld` context files (lct.jsonld: 30+ term mappings, attestation-envelope.jsonld:
25+ term mappings). 26 consistency tests verifying all to_jsonld() keys have context mappings.
Fixed 3 type errors in attestation context (timestamp/TTL as xsd:double, PCR selection as @list).
1477 total tests passing.

### B3: JSON-LD namespace and context URI reconciliation
**Status**: DONE
**Completed**: 2026-03-24
**Depends on**: B2
**Scope**: Audit and reconcile the namespace split across all 8 types. Currently:
- T3/V3 and R7 use `https://web4.io/ontology#` (from TTL ontology files)
- ATP/ACP/Entity/Capability use `https://web4.io/ns/` (from schemas/contexts/)
- LCT and AttestationEnvelope reference `https://web4.io/contexts/` URIs

Determine canonical namespace strategy (likely `https://web4.io/ns/` for all, with
`ontology#` reserved for OWL/RDF class definitions). Document the decision. Update
context files and Python constants for consistency. Preserve backward compatibility
in `from_jsonld()` (accept both old and new namespace URIs).
**Result**: Decision: `https://web4.io/ns/` canonical for all application contexts;
`ontology#` reserved for OWL/RDF. Created 3 new context files (`t3.jsonld`, `v3.jsonld`,
`r7-action.jsonld`) in `schemas/contexts/` using `ns/` namespace. Updated T3/V3 constants
and removed bare `WEB4_ONTOLOGY_NS` from @context arrays. R7 context maps both snake_case
(from to_jsonld) and camelCase (from nested to_dict) field names. 32 consistency tests.
Decision doc: `docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md`.
1523 total tests passing.

### B4: Schema-validated JSON-LD round-trip tests
**Status**: DONE
**Completed**: 2026-03-24
**Depends on**: B2, B3
**Scope**: Add integration tests that validate all 9 `to_jsonld()` schemas (19 @type
values) programmatically using `jsonschema`. Pattern: create object → `to_jsonld()` →
validate against schema → `from_jsonld()` → assert equality.
**Result**: `tests/test_jsonld_schema_roundtrip.py` — 48 tests covering all 9 JSON-LD
schemas and 19 distinct @type values: LCT, AttestationEnvelope, T3Tensor, V3Tensor,
R7Action, ATPAccount, TransferResult, AgentPlan, Intent, Decision, ExecutionRecord,
EntityTypeInfo, EntityTypeRegistry, LevelRequirement, CapabilityAssessment,
CapabilityFramework, DictionarySpec, TranslationResult, TranslationChain, DictionaryEntity.
Includes per-type schema validation, round-trip fidelity, and a parametrized summary test
that validates all types in one pass. 1571 total tests passing.

### B5: SDK v0.10.1 release housekeeping
**Status**: DONE
**Completed**: 2026-03-24
**Depends on**: B2, B3, B4, B6
**Scope**: Version bump and CHANGELOG entry documenting B2-B6 deliverables.
**Result**: CHANGELOG.md v0.10.1 entry documents B2 (missing context files), B3
(namespace reconciliation), B4 (schema-validated round-trip tests). Version bumped
0.10.0 → 0.10.1 in `__init__.py`, `pyproject.toml`, `setup.py`. Sprint 6 complete
(6/6 tasks). 1571 tests passing.

### B6: Dictionary JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: None
**Scope**: Add `to_jsonld()` / `from_jsonld()` to DictionarySpec, TranslationResult,
TranslationChain, and DictionaryEntity in `web4.dictionary`. JSON Schema
(`dictionary-jsonld.schema.json`) and JSON-LD context (`contexts/dictionary.jsonld`).
**Result**: 4 types with JSON-LD serialization (DictionarySpec, TranslationResult,
TranslationChain, DictionaryEntity). JSON Schema with 4 type definitions and 4
reusable sub-schemas (DomainCoverage, CompressionProfile, ChainStep, DictionaryType).
JSON-LD context (`contexts/dictionary.jsonld`). 1 new export (`DICTIONARY_JSONLD_CONTEXT`).
14 new tests, 1463 total SDK tests passing.

---

## Sprint 5: Core Type JSON-LD Phase 2 (2026-03-21)

Sprint 4 delivered JSON-LD for the highest-priority types (LCT, AttestationEnvelope,
R7Action, T3/V3). Sprint 5 extends JSON-LD serialization to the next tier of core
types needed for cross-language interoperability.

### A1: ATP/ADP JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-21
**Scope**: Add `to_jsonld()` / `from_jsonld()` to `ATPAccount` and `TransferResult`
in `web4.atp`, producing RDF-aligned JSON-LD documents. JSON Schema
(`atp-jsonld.schema.json`) and JSON-LD context (`contexts/atp.jsonld`).
**Result**: `ATPAccount.to_jsonld()` / `from_jsonld()`, `TransferResult.to_jsonld()` /
`from_jsonld()`. JSON Schema with ATPAccount and TransferResult definitions.
JSON-LD context mapping snake_case fields to web4 namespace.
2 new exports (`TransferResult`, `ATP_JSONLD_CONTEXT`). 28 new tests, 1302 total
SDK tests passing.

### A2: ACP JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-21
**Depends on**: None
**Scope**: Add `to_jsonld()` / `from_jsonld()` to ACP types (AgentPlan, Intent,
Decision, ExecutionRecord) in `web4.acp`. JSON Schema and JSON-LD context.
**Result**: `AgentPlan.to_jsonld()` / `from_jsonld()`, `Intent.to_jsonld()` /
`from_jsonld()`, `Decision.to_jsonld()` / `from_jsonld()`,
`ExecutionRecord.to_jsonld()` / `from_jsonld()`. JSON Schema
(`acp-jsonld.schema.json`) with 4 type definitions and 6 reusable sub-schemas.
JSON-LD context (`contexts/acp.jsonld`). 1 new export (`ACP_JSONLD_CONTEXT`).
54 new tests, 1356 total SDK tests passing.

### A3: Entity + Capability JSON-LD
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: None
**Scope**: Add `to_jsonld()` / `from_jsonld()` to EntityTypeInfo and LevelRequirement
types, plus registry/framework/assessment serializers. JSON Schema and JSON-LD context.
**Result**: `EntityTypeInfo.to_jsonld()` / `from_jsonld()`, `entity_registry_to_jsonld()`,
`LevelRequirement.to_jsonld()` / `from_jsonld()`, `capability_assessment_to_jsonld()`,
`capability_framework_to_jsonld()`. JSON Schemas (`entity-jsonld.schema.json`,
`capability-jsonld.schema.json`). JSON-LD contexts (`entity.jsonld`, `capability.jsonld`).
5 new exports (`ENTITY_JSONLD_CONTEXT`, `entity_registry_to_jsonld`,
`CAPABILITY_JSONLD_CONTEXT`, `capability_assessment_to_jsonld`,
`capability_framework_to_jsonld`). 37 new tests, 1393 total SDK tests passing.

### A4: Cross-language validation vectors for Phase 2
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: A1, A2, A3
**Scope**: JSON test vectors for ATP, ACP, Entity, Capability schemas.
**Result**: 127 vectors for all 4 Phase 2 schemas.
ATP: 8 valid + 15 invalid = 23 vectors (ATPAccount and TransferResult types).
ACP: 12 valid + 24 invalid = 36 vectors (AgentPlan, Intent, Decision, ExecutionRecord types).
Entity: 12 valid + 20 invalid = 32 vectors (EntityTypeInfo and EntityTypeRegistry types).
Capability: 12 valid + 24 invalid = 36 vectors (LevelRequirement, CapabilityAssessment, CapabilityFramework types).
Validation runner updated to include all 8 schemas. 228 total vectors across all schemas.

### A5: SDK v0.9.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-22
**Depends on**: A1 (at minimum)
**Scope**: Version bump, CHANGELOG.md entry for Sprint 5 deliverables.
**Result**: Version bumped 0.8.0 → 0.9.0 in `__init__.py`, `pyproject.toml`, `setup.py`.
CHANGELOG.md v0.9.0 section documents A1 (ATP JSON-LD), A2 (ACP JSON-LD),
A4 partial (59 validation vectors), and 3 new exports. 269 symbols, 1356 tests passing.

---

## Sprint 4: Cross-Language Schema Standardization (2026-03-20)

Sprint 3 produced spec-compliant JSON-LD serialization for LCT and AttestationEnvelope.
This sprint provides formal JSON Schema files so that Go/TypeScript/Rust implementations
can validate their serialization output against a machine-readable specification. It
also extends JSON-LD coverage to remaining core types.

### V1: JSON Schema for LCT and AttestationEnvelope JSON-LD
**Status**: DONE
**Completed**: 2026-03-20
**Scope**: Create JSON Schema (draft 2020-12) files for the LCT JSON-LD format (spec §2.3)
and AttestationEnvelope JSON-LD format. Include a validation script that confirms current
SDK `to_jsonld()` output passes the schemas. Schemas derived from spec documents,
cross-checked against SDK output.
**Result**: `lct-jsonld.schema.json`, `attestation-envelope-jsonld.schema.json`,
`validate_schemas.py`. 19 validation checks (10 LCT + 9 AttestationEnvelope). PR #53, merged.

### V2: T3/V3 Trust Tensor JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-22
**Depends on**: V1
**Scope**: Add `to_jsonld()` / `from_jsonld()` to `T3` and `V3` classes in `web4.trust`,
producing output matching `t3v3-ontology.ttl`. JSON Schema for the format.
**Result**: `T3.to_jsonld()` / `from_jsonld()`, `V3.to_jsonld()` / `from_jsonld()` with
ontology-aligned dual representation. JSON Schema (`t3v3-jsonld.schema.json`).
58 new tests. PR #54, awaiting review.

### V3: R7 Action JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-21
**Depends on**: V1
**Scope**: Add `to_jsonld()` / `from_jsonld()` to R7 action types in `web4.r6`,
enabling cross-language representation of actions, action chains, and reputation deltas.
JSON Schema for the format.
**Result**: `R7Action.to_jsonld()` / `from_jsonld()`, `ReputationDelta.to_jsonld()` /
`from_jsonld()`, `ActionChain.to_jsonld()` / `from_jsonld()`. JSON-LD context
(`r7-action.jsonld`) and JSON Schema (`r7-action-jsonld.schema.json`). All 7 R7
components serialized (Rules/Role/Request/Reference/Resource/Result/Reputation).
26 new tests, 75 total R6 tests, 1274 total SDK tests passing. PR #55, merged.

### V4: Cross-language validation test vectors
**Status**: DONE
**Completed**: 2026-03-22
**Depends on**: V1, V2, V3
**Scope**: JSON test vectors that exercise schema validation edge cases — malformed
documents, missing required fields, extra fields, boundary values. Vectors usable
by any language's JSON Schema validator.
**Result**: 101 vectors for 4 merged schemas (LCT, AttestationEnvelope, R7 Action, T3/V3).
31 valid documents + 70 invalid documents covering: missing required fields, enum violations,
out-of-range values, pattern mismatches, type errors, additionalProperties, boundary values,
type mismatches (T3 fields with V3 @type and vice versa), DimensionScore sub-schema validation.
T3/V3 vectors: 10 valid + 28 invalid = 38 vectors.
Validation runner script (`validate_schema_vectors.py`) covers all 4 schemas.

### V5: SDK v0.8.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-21
**Depends on**: V1 (at minimum)
**Scope**: Version bump, CHANGELOG.md entry for Sprint 4 deliverables.
**Result**: Version bumped 0.7.0 → 0.8.0 in `__init__.py`, `pyproject.toml`, `setup.py`.
CHANGELOG.md v0.8.0 section documents V1 (JSON Schemas), V3 (R7 Action JSON-LD),
V4 partial (63 validation vectors), and new exports. 266 symbols, 1274 tests passing.

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
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: Add `to_jsonld()` / `from_jsonld()` to `AttestationEnvelope` in
`web4.attestation`, matching the attestation-envelope spec format.
**Result**: `AttestationEnvelope.to_jsonld()` and `from_jsonld()` with full
spec compliance. 41 tests. PR #48.

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
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: JSON test vectors for AttestationEnvelope construction, trust ceilings,
freshness model, serialization, and verification dispatch. Python validator script.
**Result**: 35 vectors in `web4-standard/test-vectors/attestation/attestation-vectors.json`,
validator in `validate_attestation_vectors.py` — all passing.

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
**Status**: DONE
**Completed**: 2026-03-20
**Scope**: Version bump (0.5.0 -> 0.6.0) and changelog for the attestation module
that landed in H4. Sprint 2 status update.
**Result**: CHANGELOG.md v0.6.0 entry. PR #46, merged.

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
**Status**: DONE
**Completed**: 2026-03-18
**Result**: Extended `test_integration.py` with 3 new cross-module test classes exercising
all 10 newer modules (security, protocol, mcp, entity, capability, errors, metabolic,
binding, society, reputation) alongside the original 8. 28 total integration tests,
928 total SDK tests passing. Validates SDK works as a coherent 18-module library.

### U17: SDK v0.5.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-18
**Result**: CHANGELOG.md updated with v0.5.0 entries for U13 (security), U14 (protocol),
U15 (mcp). Version bumped 0.4.0 → 0.5.0. SPRINT.md U13 status corrected, U16/U17 added.

### U18: SDK public API and packaging cleanup
**Status**: DONE
**Completed**: 2026-03-20
**Description**: Consolidate web4 package public API surface. Populate `web4/__init__.py`
with re-exports from all 18 modules (247 symbols, `__all__` defined). Fix `pyproject.toml`
metadata (version 0.5.0, classifiers, description). Add PEP 561 `py.typed` marker.
Fix `setup.py` consistency. `from web4 import T3, LCT, Society, R7Action` now works.
49 new tests, 974 total passing. PR #40, merged.

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
| U16 | Full-stack integration tests (18 modules) | DONE |
| U17 | SDK v0.5.0 release housekeeping | DONE |
| U18 | SDK public API and packaging cleanup | DONE |
| H1 | AttestationEnvelope test coverage | DONE |
| H2 | Verification dispatch test coverage | DONE |
| H3 | Cross-language attestation test vectors | DONE |
| H4 | SDK integration for AttestationEnvelope | DONE |
| H5 | AttestationEnvelope + binding integration | DONE |
| H6 | SDK v0.6.0 release housekeeping | DONE |
| I1 | LCT spec-compliant JSON-LD serialization | DONE |
| I2 | Cross-language LCT test vectors | DONE |
| I3 | AttestationEnvelope JSON-LD serialization | DONE |
| I4 | SDK v0.7.0 release housekeeping | DONE |
| V1 | JSON Schema for LCT + AttestationEnvelope JSON-LD | DONE |
| V2 | T3/V3 Trust Tensor JSON-LD serialization | DONE |
| V3 | R7 Action JSON-LD serialization | DONE |
| V4 | Cross-language validation test vectors | DONE |
| V5 | SDK v0.8.0 release housekeeping | DONE |
| A1 | ATP/ADP JSON-LD serialization | DONE |
| A2 | ACP JSON-LD serialization | DONE |
| A3 | Entity + Capability JSON-LD | DONE |
| A4 | Cross-language validation vectors (Phase 2) | DONE |
| A5 | SDK v0.9.0 release housekeeping | DONE |
