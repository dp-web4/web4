# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-04-11 (Sprint 33)*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

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

- **Version**: 0.24.0
- **Modules**: 22 library modules + MCP server entry point (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp, attestation, validation, deserialize, generate, mcp_server)
- **Tests**: 2614 passing (97.8% coverage)
- **Exports**: 364 symbols via `web4/__init__.py`
- **from_dict()**: 58 classmethods across 10 modules — all classes with to_dict()/as_dict() have matching from_dict()
- **Dispatcher**: 23 types via `web4.from_jsonld()` (19 class-based + 3 function-based + TrustQuery)
- **Generator**: 23 types via `web4.generate()` — minimal valid JSON-LD documents
- **Behavioral**: 3 functions — `evaluate_trust_query()` (direct trust resolution), `resolve_trust()` (indirect trust through MRH graph), `process_action_outcome()` (action consequences)
- **MCP Server**: `web4-mcp` / `python -m web4.mcp_server` — 8 tools (info, validate, generate, roundtrip, list_types, evaluate_trust, resolve_trust, process_action)
- **CLI**: `web4 info/validate/list-schemas/roundtrip/generate/selftest` (console script + `python -m web4`)
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
fbc847e Sprint 32 T1: web4 selftest — deployment verification CLI command (#152)
39d4e9e Sprint 31 T1: SDK v0.23.0 release housekeeping (#150)
af62184 Sprint 30 T1: Distribution verification — fix roundtrip fidelity + packaging (#148)
37cddbc Sprint 29 T1: Refactor CLI tests to in-process for coverage accuracy (#146)
b80db02 Sprint 28: web4_process_action MCP tool + SDK v0.22.0 (#145)
```

---

## Open PRs

- PR #151: "Sprint 32 T1: Archive reference implementation sprawl" — REVIEW_REQUIRED
- PR #147: "Sprint 30 T1: web4 trust CLI subcommand" — REVIEW_REQUIRED

---

## Completeness Summary

- All 33 sprints COMPLETE (Sprints 1-33)
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
- CLI via `web4 info/validate/list-schemas/roundtrip/generate/selftest` (6 subcommands)
- Wheel distribution verified: imports, CLI, schema validation, roundtrip all pass from installed wheel
- All 23 generate() types pass roundtrip fidelity (generate → from_jsonld → to_jsonld = identical)

---

*Updated by autonomous session, 2026-04-11 (Sprint 33 — SDK v0.24.0 release housekeeping)*
