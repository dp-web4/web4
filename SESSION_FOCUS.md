# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-05-13 (Sprint 47)*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 47 Summary: Cross-Language T3/V3 Alignment Audit (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Cross-language T3/V3 semantic alignment audit | DONE | Triggered by operator WASM rebuild (`55b1a3d8`). Documented 8 divergences between Rust/WASM and spec/Python SDK: 1 CRITICAL (Talent decay violates normative invariant), 4 HIGH (composites, update formula, decay model), 2 MEDIUM (ActionOutcome, legacy bridge), 1 LOW (missing operations). Audit at `docs/audits/cross-language-t3v3-alignment-2026-05-13.md`. 1 new file. |

### Sprint 46 Summary: Clarify CI Canonicity (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Normative clarification of constellation_coherence vs "CI" | DONE | Resolves audit item #10 from Sprint 43. Added §4.4 to `multi-device-lct-binding.md`: `constellation_coherence` is canonical metric (T3 tensor extension); "CI" and numeric multipliers (e.g., 1.4×) are simulation parameters, not protocol primitives. 0 new files, 1 spec file modified. |

### Sprint 45 Summary: Archive Stale Implementation Artifacts (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Archive 3 stale non-code files from implementation/ | DONE | Completes cleanup chain from PRs #174-178. Archived `implementation_guide.md` (drift-era crypto guide), `handshake_exchange.json` (non-canonical protocol), `metering_flow.json` (non-canonical terminology) to `archive/implementation-sprawl/`. `implementation/` now contains only `sdk/` and `reference/` (3 REVIEW .py files pending operator). 0 new files, 3 files moved. |

### Sprint 44 Summary: Resolve MEDIUM-Priority Spec Gaps (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: ATP transfer-fee semantics + T3 Talent-decay clarification | DONE | Resolves SPEC GAP #2 and #5 from Sprint 43 audit. Added §6.3 Transfer Fees to `atp-adp-cycle.md` (society-configurable, not protocol-prescribed). Strengthened Talent no-decay language in `t3-v3-tensors.md` (normative invariant, not tunable). 0 new files, 2 spec files modified. |

### Sprint 43 Summary: Spec-to-Explainer Alignment Memo (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Spec-to-explainer alignment memo | DONE | Categorized 14 friction items from 4-life visitor log: 4 SPEC GAP, 8 EXPLAINER GAP, 2 BOTH. Produced `docs/audits/spec-vs-explainer-alignment-2026-04-19.md`. |

### Sprint 42 Summary: CI Quickstart Smoke (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: Wire `examples/quickstart.py` into CI wheel smoke job | DONE | Added one step to the `wheel` job in `.github/workflows/sdk-test.yml`, running `examples/quickstart.py` against the installed wheel's isolated venv. Closes Sprint 36 T1 follow-up. 0 new files, no product code changes, no version bump. Originally proposed as Sprint 40 (PR #164); renumbered to Sprint 42 to reflect merge order — Sprint 41 landed on main first. |

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
- **License**: AGPL-3.0-or-later throughout (a brief MIT relicense was attempted Feb 2026 for ARIA grant compatibility; reverted 2026-04-27 — AGPL-bounded patent grant in PATENTS.md was incompatible with MIT)

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

## ARIA-era Work (historical context, 2026-02 → 2026-04)

Work undertaken in early 2026 toward what was at the time a planned ARIA grant submission. The grant was ultimately not submitted; the technical work landed and is canonical:
- **Witnessed tier work**: LCT JSON-LD with attestation chain, cross-language validation vectors — landed
- **Hardware binding**: AttestationEnvelope integrated into SDK with TPM2/FIDO2/SE anchor types — landed
- **Cross-language interoperability**: JSON Schemas enable Go/TypeScript/Rust validators — landed
- **License**: SDK was briefly relicensed AGPL→MIT for ARIA compatibility, reverted to AGPL-3.0-or-later 2026-04-27 after ARIA decision was no-submit (the AGPL-bounded patent grant in PATENTS.md created a license trap with MIT)

---

## Recent Commits

```
55b1a3d Rebuild web4-trust-core WASM: canonical 3D tensors
8e6d1ee Sprint 46 T1: Clarify CI canonicity (audit item #10) (#181)
8e07fb0 [Publisher] No-change check: Sprint 44 T1 spec gaps resolved, no whitepaper integration
7c228fd Sprint 45 T1: Archive stale implementation artifacts (#180)
d530060 Sprint 44 T1: Resolve MEDIUM-priority spec gaps from Sprint 43 audit (#179)
```

---

## Open PRs

None (Sprint 47 T1 PR pending).

### Closed PRs (recent)

- PR #181 MERGED — Sprint 46 T1: Clarify CI canonicity (audit item #10)
- PR #180 MERGED — Sprint 45 T1: Archive stale implementation artifacts
- PR #179 MERGED — Sprint 44 T1: Resolve MEDIUM-priority spec gaps from Sprint 43 audit
- PR #178 MERGED — Strategic review follow-up audit + archive 3 stray implementation/ markdowns
- PR #176 MERGED — Web4 session 20260512-060024 (auto-branched safety net)
- PR #175 MERGED — Archive 15 reference files + triage 9 sprawl directories

---

## Completeness Summary

- All 47 sprints COMPLETE (Sprints 1-47, all merged or PR pending)
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
- `examples/quickstart.py` runs in the CI `wheel` job against the installed wheel — API breakage in the quickstart fails CI on every PR

---

- **web4-trust-core alignment**: Cross-language T3/V3 audit identified 8 divergences (1 CRITICAL, 4 HIGH) between Rust/WASM and spec/Python SDK — see `docs/audits/cross-language-t3v3-alignment-2026-05-13.md`

---

*Updated by autonomous session, 2026-05-13 (Sprint 47 — cross-language T3/V3 alignment audit)*
