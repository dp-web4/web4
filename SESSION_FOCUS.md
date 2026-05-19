# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-05-19 (Sprint 55)*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 55 Summary: SDK v0.28.0 Release Housekeeping (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: v0.28.0 release housekeeping | DONE | Version bump 0.27.0->0.28.0. CHANGELOG for PRs #195, #199, #210. Updated counters (369->376 exports, 2709->2749 tests, 8->5 xfails, 6->7 error categories). Updated README, quickstart, test assertions. 0 new files. |

### Sprint 54 Summary: Spec Audit & Remediation Series (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| C-series audits + remediation | DONE | Informal series (PRs #195-#211). C1: MCP-SDK alignment audit. C2: mcp-protocol.md internal consistency (13 findings) → PRs #200/#201/#203. C3: §7.7 promotion tracking → PR #202. C4: vector-freshness process → PR #197. C5: presence-protocol.md consistency (13 findings) → PRs #206/#207/#208/#209. SDK: cross-society types (PR #195), tests (PR #199), 3 xfails resolved (PR #210). CHANGELOG staleness resolved (PR #211). |

### Sprint 53 Summary: SDK v0.27.0 Release Housekeeping (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: v0.27.0 release housekeeping | DONE | Version bump 0.26.0->0.27.0. CHANGELOG for Sprints 41-42, 50-52. Added missing `validate_minimum_viable` export + `role` module to CLI info/selftest (was 22, now 23 modules). Updated README, quickstart, test assertions. 0 new files. 369 exports. 2709 tests. |

### Sprints 43-52: All COMPLETE

See `docs/SPRINT.md` for details. Highlights: Spec-to-explainer alignment (43), MEDIUM spec gaps (44), archive stale artifacts (45), CI canonicity (46), cross-language T3/V3 audit (47), parameter governance (48), cross-language Society/Role/ATP/R6 audit (49), SocietyRole + RoleAssignment (50), validate_minimum_viable + Constraint alignment (51), conformance test runner (52).

### Sprints 4-42: All COMPLETE

See `docs/SPRINT.md` for full history.

---

## SDK Status

- **Version**: 0.28.0
- **Modules**: 23 library modules + MCP server entry point (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, role, reputation, security, protocol, mcp, attestation, validation, deserialize, generate, mcp_server)
- **Tests**: 2749 total (2744 passing, 5 xfailed conformance gaps)
- **CLI**: `web4 info/validate/list-schemas/roundtrip/generate/selftest/trust` (7 subcommands)
- **Exports**: 376 symbols via `web4/__init__.py`
- **from_dict()**: 58 classmethods across 10 modules — all classes with to_dict()/as_dict() have matching from_dict()
- **Dispatcher**: 23 types via `web4.from_jsonld()` (19 class-based + 3 function-based + TrustQuery)
- **Generator**: 23 types via `web4.generate()` — minimal valid JSON-LD documents
- **Behavioral**: 3 functions — `evaluate_trust_query()` (direct trust resolution), `resolve_trust()` (indirect trust through MRH graph), `process_action_outcome()` (action consequences)
- **MCP Server**: `web4-mcp` / `python -m web4.mcp_server` — 8 tools (info, validate, generate, roundtrip, list_types, evaluate_trust, resolve_trust, process_action)
- **CLI entry points**: console script `web4` + `python -m web4`
- **Optional extras**: `web4[validation]` (jsonschema), `web4[mcp]` (mcp), `web4[dev]` (full toolchain)
- **Error taxonomy**: 7 categories (Binding, Pairing, Witness, Authorization, Crypto, Protocol, Cross-Society), 30 error codes
- **License**: AGPL-3.0-or-later throughout

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

## Conformance Status

- **35 conformance vectors** across 4 suites (tensor ops, ATP, R6/R7, society/roles)
- **34 passing, 5 xfailed** (was 31/8 at Sprint 52; PR #210 resolved 3)
- **5 remaining xfails** — all require operator/architect decisions:
  1. `t3-004`: T3 update direction (quality-only vs success flag) — Tier B
  2. `r6-val-004`: Constraint enforcement in validate() vs PolicyGate — Tier B
  3. `role-004`: Assigner authorization predicate (data vs governance layer) — Tier B
  4. `fed-001`: Federation join/secede (child-initiated vs parent-initiated) — Tier B
  5. `sub-001`: T3 sub-dimension rollup (runtime vs ontology-metadata) — Tier C
- See `docs/audits/sprint-52-conformance-gap-consolidation-2026-05-15.md` for full analysis

---

## Open Audit Items (Operator-Blocked)

| Item | Source | Decision Needed |
|------|--------|-----------------|
| P4: MetabolicState reconciliation | Sprint 49 audit | 5-state (Rust/spec) vs 7-state (Python) |
| P7: Role integration architecture | Sprint 49 audit | Where do roles live in SocietyState? |
| B1-B5: Conformance xfails | Sprint 52 consolidation | See conformance status above |

---

## Recent Commits

```
40e6228f docs(changelog): resolve stale "Upcoming (planned)" v1 section in presence-protocol CHANGELOG (#211)
b5c9e87b docs(conformance): add shapeMatchesSchema to P1-003 connect step (corpus consistency) (#209)
3f124627 fix(conformance): reconcile 3 vectors with normative spec — resolve 3 of 8 xfails (#210)
ac9de279 docs(conformance): resolve C5 audit G4 — fix P1-003 + add P1-004 (P12/P13) (#208)
9ace6d76 docs(whitepaper): no-change check 2026-05-18 — audit-driven spec discipline; §7.7 promotion gate formalized
```

---

## Open PRs

None. All PRs through #211 merged.

### Closed PRs (recent)

- PR #211 MERGED — CHANGELOG post-v1 staleness resolved
- PR #210 MERGED — Reconcile 3 conformance vectors with normative spec
- PR #209 MERGED — shapeMatchesSchema corpus consistency
- PR #208 MERGED — C5 audit G4: fix P1-003 + add P1-004
- PR #207 MERGED — C5 audit G2: discipline honesty
- PR #206 MERGED — C5 audit G1+G3: casing authority + localized staleness
- PR #204 MERGED — C5: presence-protocol.md internal consistency audit
- PR #203 MERGED — C2 audit: resolve LOW F14/F16
- PR #202 MERGED — C3: §7.7 promotion tracking stub
- PR #201 MERGED — C2 audit: resolve MEDIUM F1/F5/F15
- PR #200 MERGED — C2 audit: resolve HIGH §7.4↔§7.7 F2/F3/F4/F12
- PR #199 MERGED — Cross-society type tests + wiring
- PR #197 MERGED — C4: vector-freshness check process
- PR #195 MERGED — Cross-society MCP types

---

## Completeness Summary

- All 55 sprints COMPLETE (Sprints 1-55, all merged)
- All 9 JSON-LD schemas with cross-language validation vectors (278 total, in pytest)
- All `to_jsonld()` functions have `from_jsonld()` inverses (API symmetry complete)
- All `to_dict()`/`as_dict()` methods have `from_dict()` inverses (58 round-trip methods total)
- Generic `from_jsonld(doc)` dispatches 23 types by `@type` field (web4.deserialize)
- `web4.generate(type_name)` produces minimal valid JSON-LD for any of 23 types
- `evaluate_trust_query()` — direct trust resolution composing TrustQuery + TrustProfile + ATPAccount
- `resolve_trust()` — indirect trust resolution composing MRHGraph + TrustProfile T3 tensors
- `process_action_outcome()` — action consequence pipeline composing R7Action + ReputationEngine + TrustProfile + ATPAccount
- MCP server: 8 tools exposing SDK data operations + behavioral trust/reputation resolution to MCP clients
- Cross-society types: `CrossSocietyContext`, `ReputationEnvelope`, `MCPContextResource` (§7.3–7.6)
- All 23 submodules have `__all__` declarations, 376 root exports
- All public methods have docstrings and return type annotations
- `mypy --strict` passes with 0 errors across 26 source files
- Test coverage: 97.8% overall (4 modules at 100%, 16 at 95%+, __main__.py at 90.6%)
- Schema validation via `web4.validation.validate()` with `pip install web4-sdk[validation]`
- CLI via `web4 info/validate/list-schemas/roundtrip/generate/selftest/trust` (7 subcommands)
- Wheel distribution verified: imports, CLI, schema validation, roundtrip all pass from installed wheel
- All 23 generate() types pass roundtrip fidelity (generate → from_jsonld → to_jsonld = identical)
- `ruff check web4/ tests/` passes with 0 errors — CI enforces lint on source + tests
- `ruff format --check web4/ tests/test_*.py` passes with 0 changes — CI enforces formatting
- `examples/quickstart.py` runs in the CI `wheel` job against the installed wheel
- Conformance: 34/39 vectors pass, 5 xfailed (operator-blocked architectural decisions)
- Spec audits: mcp-protocol.md (C2) and presence-protocol.md (C5) audited for internal consistency; findings resolved via PRs #200-#211

---

*Updated by autonomous session, 2026-05-19 (Sprint 55 — SDK v0.28.0 release housekeeping)*
