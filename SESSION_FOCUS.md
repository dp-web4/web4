# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-04-04 (Sprint 17 T1)*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 17 Summary: Release Housekeeping (IN PROGRESS)

| Task | Status | Notes |
|------|--------|-------|
| T1: SDK v0.18.0 release housekeeping | DONE | Version bump, CHANGELOG, README, docstring updates for Sprint 16 work |

### Sprint 16 Summary: Quality Gates + Generic Deserialization (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| T1: mypy strict zero-error + coverage baseline | DONE | `mypy --strict` 0 errors (22 files), coverage 96.2% (4491 stmts) |
| T2: Generic JSON-LD deserialization dispatcher | DONE | `web4.from_jsonld(doc)` dispatches 22 types, 62 tests, 2245 total |

### Sprint 15 Summary: from_dict() Completeness + Schema Vectors (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| N1: Security from_dict() | DONE | W4ID, KeyPolicy, SignatureEnvelope, VerifiableCredential — 4 methods, 16 tests, PR #119 |
| O1: R6 from_dict() | DONE | 12 component from_dict() methods, 32 tests, PR #120 |
| P1: Reputation + protocol from_dict() | DONE | ReputationRule, HandshakeMessage — 2 methods, 8 tests, PR #121 |
| Q1: ACP from_dict() | DONE | PlanStep, AgentPlan, Intent, Decision, ExecutionRecord — 5 methods, 18 tests, PR #123 |
| R1: LCT from_dict() | DONE | Binding, MRHPairing, MRH, BirthCertificate, Attestation, LineageEntry, Policy, LCT — 8 methods, 27 tests, PR #124 |
| M1: Schema validation vectors in pytest | DONE | 278 vectors as parametrized tests, PR #117 |
| S1: Trust/MRH from_dict() + v0.17.0 | DONE | T3, V3, MRHNode, MRHEdge from_dict() — 4 methods, 27 tests. Version bump, CHANGELOG |

### Sprint 14 Summary: Optional Extras and Release Polish (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| K1: Validation extra + README + v0.16.0 | DONE | `pip install web4[validation]`, README coherence, version bump |

### Sprints 4-13: All COMPLETE

See `docs/SPRINT.md` for full history. Highlights: JSON-LD serialization for all 10 types (Sprints 4-6), API completeness (Sprint 7), developer experience (Sprint 8), documentation (Sprint 9), CI/CD (Sprint 10), quality gates (Sprint 11), schema validation (Sprint 12), CLI + distribution (Sprint 13).

---

## SDK Status

- **Version**: 0.18.0
- **Modules**: 21 (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp, attestation, validation, deserialize)
- **Tests**: 2245 passing
- **Exports**: 348 symbols via `web4/__init__.py`
- **from_dict()**: 56 classmethods across 10 modules — all classes with to_dict()/as_dict() have matching from_dict()
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
7677335 K1: Validation optional extra + README coherence + SDK v0.16.0 (#113)
e7f1b97 R1: LCT module from_dict() round-trip completeness (#124)
f05c3f8 M1: Integrate 278 schema validation vectors into pytest suite (#117)
9417027 Q1: ACP module from_dict() round-trip completeness (#123)
8184181 P1: Reputation + protocol from_dict() round-trip completeness (#121)
e7ddf1a O1: R6 module from_dict() round-trip completeness (#120)
b6449c7 N1: Security module from_dict() round-trip completeness (#119)
```

---

## Open PRs

- PR #112: L1: Strict warnings + CI quality gates — Sprint 15 (REVIEW_REQUIRED)

---

## Completeness Summary

- All 16 sprints COMPLETE (Sprints 1-16), Sprint 17 in progress
- All 9 JSON-LD schemas with cross-language validation vectors (278 total, in pytest)
- All `to_jsonld()` functions have `from_jsonld()` inverses (API symmetry complete)
- All `to_dict()`/`as_dict()` methods have `from_dict()` inverses (56 round-trip methods total)
- Generic `from_jsonld(doc)` dispatches 22 types by `@type` field (web4.deserialize)
- All 21 submodules have `__all__` declarations, 348 root exports
- All public methods have docstrings and return type annotations
- `mypy --strict` passes with 0 errors across 23 source files
- Test coverage: 96.2% overall (4 modules at 100%, 16 at 95%+)
- Schema validation via `web4.validation.validate()` with `pip install web4[validation]`
- CLI via `web4 info/validate/list-schemas`

---

*Updated by autonomous session, 2026-04-04 (Sprint 17 T1)*
