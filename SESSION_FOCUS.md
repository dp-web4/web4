# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-03-26*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 8 Summary: SDK Developer Experience (IN PROGRESS)

| Task | Status | Notes |
|------|--------|-------|
| D1: Export completeness | DONE | 52 new exports (284 → 336), 35 new tests |
| D2: Submodule `__all__` declarations | DONE | All 19 submodules, 375 symbols, 21 new tests |
| D3: Docstring coverage for mcp.py | DONE | 32 methods documented, 100% coverage |
| D4: SDK v0.12.0 release housekeeping | NOT STARTED | Version bump, CHANGELOG |

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

- **Version**: 0.11.0
- **Modules**: 19 (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp, attestation)
- **Tests**: 1715 passing
- **Exports**: 336 symbols via `web4/__init__.py`
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
0ab1cd2 C2: ATP core unit tests — 74 tests (#82)
650518d C3: BirthCertificate field rename context → birth_context (#83)
a8c7dd8 C1: Add missing from_jsonld() inverse functions — 14 tests (#81)
f39252d Dictionary JSON-LD cross-language validation vectors — 50 vectors (#80)
40190f1 B5: SDK v0.10.1 — Sprint 6 complete (6/6 tasks) (#79)
```

---

## Open PRs

None.

---

## Pending Items

- Sprint 8 IN PROGRESS (D1-D3 done, D4 remaining)
- D1 export audit: 52 missing symbols now exported (336 total), 6 aliased to avoid collisions
- D2 submodule __all__: all 19 submodules have __all__ (375 total symbols)
- D3 mcp.py docstrings: 32 methods documented, 100% coverage (56/56 symbols)
- All 9 JSON-LD schemas have cross-language validation vectors (278 total)
- Whitepaper-SDK coherence: ongoing (last audit 2026-03-15, 4 divergences found and fixed)
- All `to_jsonld()` functions now have `from_jsonld()` inverses (API symmetry complete)

---

*Updated by autonomous session, 2026-03-26*
