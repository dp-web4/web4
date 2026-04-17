# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-04-17 (Sprint 41)*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 41 Summary: Remove Dead web4_sdk.py + Fix v0.26.0 Documentation Gaps (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Remove dead `web4_sdk.py` + fix docs | DONE | Deleted `web4_sdk.py` (dead async HTTP client for nonexistent services, not in wheel) + `test_sdk_integration.py` (14 tests). README: version 0.25.0→0.26.0, removed misleading "Client SDK" section. Quickstart docstring: v0.25.0→v0.26.0. 2613 tests, 0 new files, 2 deleted. |

### Sprint 39 Summary: SDK v0.26.0 Release Housekeeping (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: v0.26.0 release housekeeping | DONE | Version bump, CHANGELOG for Sprints 35/37/38 (CI hardening, ruff lint, ruff format), test assertion updates, 2627 tests, 0 new files |

### Sprint 38 Summary: Ruff Format Codebase-Wide + CI Enforcement (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: `ruff format` codebase-wide + CI `ruff format --check` | DONE | 70 files reformatted (web4/ + tests/test_*.py), new CI format-check step matches existing lint scope, 0 new files, 0 manual source edits, 2627 tests pass, mypy strict clean |

### Sprint 37 Summary: Ruff Lint Cleanup + CI Enforcement (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: `ruff check` lint cleanup + CI enforcement | DONE | 239 issues fixed (source: 10, tests: 229), CI now lints both web4/ and tests/, per-file-ignore for E402 in tests, 0 new files |

### Sprint 36 Summary: Quickstart Example Refresh (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Replace stale `examples/` with v0.25.0 quickstart | DONE | Deleted 2 obsolete examples (imported nonexistent `web4_sdk.Web4Client`); added `examples/quickstart.py` + `examples/README.md`. Offline, lint-clean, mypy --strict clean. |

### Sprint 35 Summary: CI Workflow Hardening (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: CI workflow hardening | DONE | mypy --strict in CI (was --ignore-missing-imports), new wheel build+selftest job, 0 new files |

### Sprint 34 Summary: SDK v0.25.0 Release Housekeeping (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: v0.25.0 release housekeeping | DONE | Version bump, CHANGELOG for PRs #147/#151/#153, README/docstring updates, 2627 tests, 7 CLI subcommands |

### Sprint 33 Summary: SDK v0.24.0 Release Housekeeping (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: v0.24.0 release housekeeping | DONE | Version bump, CHANGELOG for Sprint 32, README/docstring updates, 2614 tests |

### Sprint 32 Summary: Deployment Verification CLI (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: `web4 selftest` command | DONE | Automates deployment verification: module imports, schema registry, 23-type roundtrip. 4 new tests, 2614 total |

### Sprint 31 Summary: SDK v0.23.0 Release Housekeeping (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: v0.23.0 release housekeeping | DONE | Version bump, CHANGELOG for Sprints 29+30, README/docstring updates, 2610 tests |

### Sprint 30 Summary: Distribution Verification + Roundtrip Fidelity (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Wheel verification + roundtrip fixes | DONE | 4 bugs fixed (LCT @type, LCT schema, DictionaryEntity lct_id, license format), 2610 total tests |

### Sprint 29 Summary: CLI Test Coverage Hardening (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Refactor CLI tests to in-process | DONE | `__main__.py` coverage 15.8% → 90.6%, 40 tests in test_cli.py, 2608 total tests |

### Sprint 28 Summary: MCP process_action Tool + v0.22.0 (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: `web4_process_action` MCP tool | DONE | 8th MCP tool, wraps `process_action_outcome()`, 15 new tests |
| T2: SDK v0.22.0 release housekeeping | DONE | Version bump, CHANGELOG, README, docstring updates |

### Sprint 24 Summary: Action Consequence Pipeline (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: `process_action_outcome()` function + `ActionOutcomeResult` dataclass | DONE | R7Action → ReputationEngine → TrustProfile → ATPAccount composition, 2 new exports (364 total), 18 new tests. PR #143 |

### Sprint 27 Summary: MCP Behavioral Tools (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Expose behavioral functions as MCP tools | DONE | `web4_evaluate_trust` + `web4_resolve_trust`, 7 MCP tools total, 20 new tests |

### Sprint 26 Summary: Release Housekeeping v0.21.0 (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: SDK v0.21.0 release housekeeping | DONE | Version bump, CHANGELOG, README, docstring updates for Sprint 25. |

### Sprint 25 Summary: Indirect Trust Resolution (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: `resolve_trust()` function + `TrustResolution` dataclass | DONE | MRH graph + T3 tensor composition: indirect trust through intermediaries, 2 new exports (362 total), 22 new tests |

### Sprint 23 Summary: Release Housekeeping v0.20.0 (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: SDK v0.20.0 release housekeeping | DONE | Version bump, CHANGELOG, README, docstring updates for Sprint 22. PR #136 |

### Sprint 22 Summary: Trust Query Evaluation Pipeline + MCP Server (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: `evaluate_trust_query()` function | DONE | Core trust resolution pipeline, 1 new export (360 total), 23 new tests |
| T1b: Web4 MCP Server module | DONE | 5 MCP tools, FastMCP stdio transport, `web4-mcp` entry point, 43 new tests |

### Sprint 21 Summary: Release Housekeeping v0.19.0 (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: SDK v0.19.0 release housekeeping | DONE | Version bump, CHANGELOG, README, docstring updates for Sprints 18-20 |

### Sprints 4-20: All COMPLETE

See `docs/SPRINT.md` for full history. Highlights: JSON-LD serialization for all 10 types (Sprints 4-6), API completeness (Sprint 7), developer experience (Sprint 8), documentation (Sprint 9), CI/CD (Sprint 10), quality gates (Sprint 11), schema validation (Sprint 12), CLI + distribution (Sprint 13), optional extras (Sprint 14), from_dict completeness (Sprint 15), mypy strict + deserializer (Sprint 16), release housekeeping (Sprint 17), CLI roundtrip + lifecycle tests (Sprint 18), TrustQuery types (Sprint 19), generate module (Sprint 20).

---

## SDK Status

- **Version**: 0.26.0
- **Modules**: 22 library modules + MCP server entry point (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp, attestation, validation, deserialize, generate, mcp_server)
- **Tests**: 2613 passing (97.8% coverage)
- **CLI**: `web4 info/validate/list-schemas/roundtrip/generate/selftest/trust` (7 subcommands)
- **Exports**: 364 symbols via `web4/__init__.py`
- **from_dict()**: 58 classmethods across 10 modules — all classes with to_dict()/as_dict() have matching from_dict()
- **Dispatcher**: 23 types via `web4.from_jsonld()` (19 class-based + 3 function-based + TrustQuery)
- **Generator**: 23 types via `web4.generate()` — minimal valid JSON-LD documents
- **Behavioral**: 3 functions — `evaluate_trust_query()` (direct trust resolution), `resolve_trust()` (indirect trust through MRH graph), `process_action_outcome()` (action consequences)
- **MCP Server**: `web4-mcp` / `python -m web4.mcp_server` — 8 tools (info, validate, generate, roundtrip, list_types, evaluate_trust, resolve_trust, process_action)
- **CLI entry points**: console script `web4` + `python -m web4`
- **Optional extras**: `web4[validation]` (jsonschema), `web4[mcp]` (mcp), `web4[dev]` (full toolchain)
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

**Total schema validation vectors**: 278 across 9 schemas (ALL COMPLETE — integrated into pytest via M1)

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
91ed230 Sprint 36 T1: Replace stale examples with v0.25.0 quickstart (#160)
64add4c Sprint 39 T1: SDK v0.26.0 release housekeeping (#163)
759eaef Sprint 38 T1: ruff format codebase-wide + CI enforcement (#162)
e355a19 Sprint 37 T1: ruff check lint cleanup + CI enforcement (#161)
4a97ff7 Sprint 35 T1: CI workflow hardening — strict mypy + wheel verification (#158)
```

---

## Open PRs

- PR #164: Sprint 40 T1 — Wire examples/quickstart.py into CI wheel smoke job (pending review)

### Closed PRs (recent)

- PR #163 MERGED — Sprint 39 T1: SDK v0.26.0 release housekeeping
- PR #160 MERGED — Sprint 36 T1: Replace stale examples with v0.25.0 quickstart
- PR #159 CLOSED (superseded) — attempted `ruff format` sweep; intent addressed in Sprint 38

---

## Completeness Summary

- All 41 sprints COMPLETE (Sprints 1-41)
- All 9 JSON-LD schemas with cross-language validation vectors (278 total, in pytest)
- All `to_jsonld()` functions have `from_jsonld()` inverses (API symmetry complete)
- All `to_dict()`/`as_dict()` methods have `from_dict()` inverses (58 round-trip methods total)
- Generic `from_jsonld(doc)` dispatches 23 types by `@type` field (web4.deserialize)
- `web4.generate(type_name)` produces minimal valid JSON-LD for any of 23 types
- `evaluate_trust_query()` — direct trust resolution composing TrustQuery + TrustProfile + ATPAccount
- `resolve_trust()` — indirect trust resolution composing MRHGraph + TrustProfile T3 tensors
- MCP server: 8 tools exposing SDK data operations + behavioral trust/reputation resolution to MCP clients
- TrustQuery: to_jsonld() for dispatcher + to_dict() for schema validation (trust-query.schema.json)
- `process_action_outcome()` — action consequence pipeline composing R7Action + ReputationEngine + TrustProfile + ATPAccount
- All 22 submodules have `__all__` declarations, 364 root exports
- All public methods have docstrings and return type annotations
- `mypy --strict` passes with 0 errors across 25 source files
- Test coverage: 97.8% overall (4 modules at 100%, 16 at 95%+, __main__.py at 90.6%)
- Schema validation via `web4.validation.validate()` with `pip install web4[validation]`
- CLI via `web4 info/validate/list-schemas/roundtrip/generate/selftest/trust` (7 subcommands)
- Wheel distribution verified: imports, CLI, schema validation, roundtrip all pass from installed wheel
- All 23 generate() types pass roundtrip fidelity (generate → from_jsonld → to_jsonld = identical)
- `ruff check web4/ tests/` passes with 0 errors — CI enforces lint on source + tests
- `ruff format --check web4/ tests/test_*.py` passes with 0 changes — CI enforces formatting on source + tests
- Dead `web4_sdk.py` removed — async HTTP client for nonexistent services, not distributed in wheel

---

*Updated by autonomous session, 2026-04-17 (Sprint 41 — Remove dead web4_sdk.py + fix v0.26.0 docs)*
