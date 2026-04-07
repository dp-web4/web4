# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-04-07 (Sprint 23 T1)*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

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

- **Version**: 0.20.0
- **Modules**: 22 library modules + MCP server entry point (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp, attestation, validation, deserialize, generate, mcp_server)
- **Tests**: 2525 passing
- **Exports**: 360 symbols via `web4/__init__.py`
- **from_dict()**: 58 classmethods across 10 modules — all classes with to_dict()/as_dict() have matching from_dict()
- **Dispatcher**: 23 types via `web4.from_jsonld()` (19 class-based + 3 function-based + TrustQuery)
- **Generator**: 23 types via `web4.generate()` — minimal valid JSON-LD documents
- **Behavioral**: `evaluate_trust_query()` — trust resolution pipeline (TrustQuery + TrustProfile + ATPAccount → TrustQueryResponse)
- **MCP Server**: `web4-mcp` / `python -m web4.mcp_server` — 5 tools (info, validate, generate, roundtrip, list_types)
- **CLI**: `web4 info/validate/list-schemas/roundtrip/generate` (console script + `python -m web4`)
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
d997500 Sprint 22 T1: evaluate_trust_query() — trust resolution pipeline (#133)
a0b426a [Publisher] Maintenance: AttestationEnvelope + R6/R7 glossary entries, rebuild artifacts
dc45c22 Sprint 21 T1: SDK v0.19.0 release housekeeping (#132)
c998c37 Sprint 20 T1: `web4 generate <type>` CLI command + generate module (#131)
2d7d3e3 Sprint 19 T1: TrustQuery data classes + JSON-LD dispatcher (#130)
```

---

## Open PRs

- PR #134: Sprint 22 T1: Web4 MCP Server (STALE — changes already on main via PR #133 merge)
- PR #112: L1: Strict warnings + CI quality gates — Sprint 15 (REVIEW_REQUIRED)

---

## Completeness Summary

- All 22 sprints COMPLETE (Sprints 1-22), Sprint 23 in progress
- All 9 JSON-LD schemas with cross-language validation vectors (278 total, in pytest)
- All `to_jsonld()` functions have `from_jsonld()` inverses (API symmetry complete)
- All `to_dict()`/`as_dict()` methods have `from_dict()` inverses (58 round-trip methods total)
- Generic `from_jsonld(doc)` dispatches 23 types by `@type` field (web4.deserialize)
- `web4.generate(type_name)` produces minimal valid JSON-LD for any of 23 types
- `evaluate_trust_query()` — core trust resolution composing TrustQuery + TrustProfile + ATPAccount
- MCP server: 5 tools exposing SDK operations to MCP clients
- TrustQuery: to_jsonld() for dispatcher + to_dict() for schema validation (trust-query.schema.json)
- All 22 submodules have `__all__` declarations, 360 root exports
- All public methods have docstrings and return type annotations
- `mypy --strict` passes with 0 errors across 25 source files
- Test coverage: 96.2% overall (4 modules at 100%, 16 at 95%+)
- Schema validation via `web4.validation.validate()` with `pip install web4[validation]`
- CLI via `web4 info/validate/list-schemas/roundtrip/generate`

---

*Updated by autonomous session, 2026-04-07 (Sprint 23 T1)*
