# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-03-24*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 6 Summary: JSON-LD Context Consolidation & SDK Quality

| Task | Status | Notes |
|------|--------|-------|
| B1: SDK v0.10.0 release housekeeping | DONE | CHANGELOG + version bump for A3/A4 complete |
| B2: Missing JSON-LD context files (LCT, AttestationEnvelope) | DONE | 2 .jsonld files, 26 consistency tests |
| B3: Namespace and context URI reconciliation | DONE | All 10 context files now use ns/, decision documented |
| B4: Schema-validated JSON-LD round-trip tests | DONE | 48 tests, 9 schemas, 19 @type values |
| B5: SDK v0.10.1 release housekeeping | PENDING | Depends on B2-B4, B6 |
| B6: Dictionary JSON-LD serialization | DONE | 4 types, 14 tests, schema + context |

### Sprint 5 Summary: Core Type JSON-LD Phase 2 (COMPLETE)

All tasks DONE: A1 (ATP/ADP JSON-LD), A2 (ACP JSON-LD), A3 (Entity+Capability JSON-LD), A4 (127 validation vectors), A5 (SDK v0.9.0).

### Sprint 4 Summary: Cross-Language Schema Standardization (COMPLETE)

All tasks DONE: V1 (JSON Schemas), V2 (T3/V3 JSON-LD), V3 (R7 Action JSON-LD), V4 (160 validation vectors), V5 (SDK v0.8.0).

---

## SDK Status

- **Version**: 0.10.0
- **Modules**: 19 (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp, attestation)
- **Tests**: 1571 passing
- **Exports**: 277 symbols via `web4/__init__.py`
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
| Dictionary | DONE | DONE | schemas/contexts/ | PENDING |

**Total schema validation vectors**: 228 across 8 schemas (Dictionary vectors pending)

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
2fb27d1 B2: Missing JSON-LD context files for LCT and AttestationEnvelope — 26 tests (#74)
dfc7151 B1+B6: SDK v0.10.0 — Dictionary JSON-LD + Sprint 6 planning (#72)
705e90e A4 (complete): Entity + Capability cross-language validation vectors — 68 vectors (#71)
9dd8f06 A3: Entity + Capability JSON-LD serialization — 37 tests (#63)
cf887fb Maintenance: Update SESSION_FOCUS.md to reflect current state (#69)
```

---

## Open PRs

None — B4 PR pending.

---

## Pending Items

- Sprint 6 B5: SDK v0.10.1 version bump (B4 complete, B5 now unblocked)
- Whitepaper-SDK coherence: ongoing (last audit 2026-03-15, 4 divergences found and fixed)

---

*Updated by autonomous session, 2026-03-24*
