# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-03-29*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 14 Summary: Optional Extras and Release Polish (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| K1: Validation extra + README + v0.16.0 | DONE | `pip install web4[validation]`, README coherence, version bump |

### Sprint 13 Summary: SDK CLI Module (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| J1: CLI module | DONE | `web4 info/validate/list-schemas`, 22 tests, merged #105 |
| I1: Bundle JSON Schemas as package data | DONE | PR #104, pending review |

### Sprint 12 Summary: Schema Validation Integration (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| H1: Schema validation module | DONE | 20th SDK module, 8 public symbols, 33 tests |
| H2: SDK v0.15.0 release housekeeping | DONE | Version bump, CHANGELOG, sprint closure |

### Sprint 11 Summary: Code Quality Gates (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| G1+G2: Ruff linting + coverage reporting | DONE | PR #98, pending review |
| G3: Mypy strict compliance | DONE | 65 type fixes, mypy --strict passes |
| G4: SDK README coherence update | DONE | README rewritten for actual web4 package |

### Sprint 10 Summary: CI/CD & Packaging Quality (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| F1: GitHub Actions CI workflow | DONE | pytest across Python 3.10-3.13 matrix |
| F2: Packaging metadata improvements | DONE | URLs, keywords, LICENSE, MANIFEST.in |
| F3: Single-source version management | DONE | importlib.metadata, removed setup.py |
| F4: SDK v0.14.0 release housekeeping | DONE | Version bump 0.13.0 → 0.14.0, CHANGELOG |

### Sprint 9 Summary: SDK Documentation Completeness (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| E1: Docstring coverage (r6, mrh, security) | DONE | 32 docstrings across 3 modules, PR #89 |
| E2: Docstring coverage (reputation, protocol, acp) | DONE | 17 docstrings across 3 modules, PR #89 |
| E3: Return type annotations | DONE | 33 annotations across 5 modules |
| E4: SDK v0.13.0 release housekeeping | DONE | Version bump 0.12.0 → 0.13.0, CHANGELOG |

### Sprint 8 Summary: SDK Developer Experience (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| D1: Export completeness | DONE | 52 new exports (284 → 336), 35 new tests |
| D2: Submodule `__all__` declarations | DONE | All 19 submodules, 375 symbols, 21 new tests |
| D3: Docstring coverage for mcp.py | DONE | 32 methods documented, 100% coverage |
| D4: SDK v0.12.0 release housekeeping | DONE | Version bump 0.11.0 → 0.12.0, CHANGELOG |

### Sprint 7 Summary: SDK API Completeness (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| C1: Missing from_jsonld() inverse functions | DONE | 3 inverses + 3 string wrappers, CapabilityAssessment dataclass, 14 tests |
| C2: ATP core unit tests | DONE | 74 tests covering all 8 ATP public functions/classes |
| C3: BirthCertificate field rename | DONE | context → birth_context, backward compat in from_jsonld() |
| C4: SDK v0.11.0 release housekeeping | DONE | Version bump, CHANGELOG, sprint closure |

### Sprint 6 Summary: JSON-LD Context Consolidation & SDK Quality (COMPLETE)

All tasks DONE: B1-B6 (context files, namespace reconciliation, round-trip tests, Dictionary JSON-LD, release housekeeping).

### Sprint 5 Summary: Core Type JSON-LD Phase 2 (COMPLETE)

All tasks DONE: A1 (ATP/ADP JSON-LD), A2 (ACP JSON-LD), A3 (Entity+Capability JSON-LD), A4 (127 validation vectors), A5 (SDK v0.9.0).

### Sprint 4 Summary: Cross-Language Schema Standardization (COMPLETE)

All tasks DONE: V1 (JSON Schemas), V2 (T3/V3 JSON-LD), V3 (R7 Action JSON-LD), V4 (160 validation vectors), V5 (SDK v0.8.0).

---

## SDK Status

- **Version**: 0.16.0
- **Modules**: 20 (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp, attestation, validation)
- **Tests**: 1770 passing
- **Exports**: 344 symbols via `web4/__init__.py`
- **CLI**: `web4 info/validate/list-schemas` (console script + `python -m web4`)
- **Optional extras**: `web4[validation]` (jsonschema), `web4[dev]` (full toolchain)
- **License**: MIT (SDK), AGPL-3.0 (root repo)

---

## JSON-LD Schema Completion

| Type | JSON-LD | JSON Schema | Context File | Test Vectors |
|------|---------|-------------|-------------|-------------|
| LCT | DONE | DONE | schemas/contexts/ | DONE (23 vectors) |
| AttestationEnvelope | DONE | DONE | schemas/contexts/ | DONE (20 vectors) |
| R7Action | DONE | DONE | schemas/contexts/ | DONE (20 vectors) |
| T3 | DONE | DONE | schemas/contexts/ | DONE (38 vectors) |
| V3 | DONE | DONE | schemas/contexts/ | DONE (38 vectors) |
| ATP/ADP | DONE | DONE | schemas/contexts/ | DONE (23 vectors) |
| ACP | DONE | DONE | schemas/contexts/ | DONE (36 vectors) |
| Entity | DONE | DONE | schemas/contexts/ | DONE (32 vectors) |
| Capability | DONE | DONE | schemas/contexts/ | DONE (36 vectors) |
| Dictionary | DONE | DONE | schemas/contexts/ | DONE (50 vectors) |

**Total schema validation vectors**: 278 across 9 schemas (ALL COMPLETE)

**All 10 context files now in `schemas/contexts/` using `https://web4.io/ns/` namespace.**
Namespace decision documented in `docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md`.

---

## ARIA Deliverable Alignment

Web4 SDK development aligns with ARIA grant requirements:
- **Witnessed tier work**: LCT JSON-LD with attestation chain, cross-language validation vectors
- **Hardware binding**: AttestationEnvelope integrated into SDK with TPM2/FIDO2/SE anchor types
- **MIT license**: SDK relicensed from AGPL to MIT per ARIA requirement
- Cross-language interoperability (JSON Schemas enable Go/TypeScript/Rust validators)

---

## Recent Commits

```
bdf3c8d J1: SDK CLI module — python -m web4 validate/info/list-schemas (#105)
0bef0a9 H2: SDK v0.15.0 release housekeeping — Sprint 12 complete (#103)
e6f4fc5 H1: Schema validation module — Sprint 12 (#102)
bf42c0d G4: SDK README coherence update — document actual web4 package (#101)
803b095 G3: Mypy strict compliance — 65 type fixes across 13 SDK modules (#100)
```

---

## Open PRs

- PR #104: I1: Bundle JSON Schemas as package data — Sprint 13 (REVIEW_REQUIRED)
- PR #98: G1+G2: Ruff linting + coverage reporting — Sprint 11 (REVIEW_REQUIRED)

---

## Pending Items

- Sprint 14 COMPLETE (K1 done): Optional Extras and Release Polish, SDK v0.16.0
- Sprint 13 COMPLETE (I1+J1 done): CLI module merged, schema bundling in PR #104
- Sprint 12 COMPLETE (H1-H2 all done): Schema Validation Integration, SDK v0.15.0
- Sprint 11 COMPLETE (G1-G4 all done): Code Quality Gates (G1+G2 in PR #98)
- All 9 JSON-LD schemas have cross-language validation vectors (278 total)
- All `to_jsonld()` functions now have `from_jsonld()` inverses (API symmetry complete)
- All 20 submodules have `__all__` declarations, 344 root exports
- All public methods have docstrings and return type annotations
- Schema validation via `web4.validation.validate()` with `pip install web4[validation]`
- CLI via `web4 info/validate/list-schemas`

---

*Updated by autonomous session, 2026-03-29*
