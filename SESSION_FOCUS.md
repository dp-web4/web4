# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-03-23*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 5 Summary: Core Type JSON-LD Phase 2

| Task | Status | Notes |
|------|--------|-------|
| A1: ATP/ADP JSON-LD | DONE | 28 tests, PR #60 merged |
| A2: ACP JSON-LD | DONE | 54 tests, PR #62 merged |
| A3: Entity + Capability JSON-LD | IN REVIEW | 37 tests, PR #63 awaiting review |
| A4: Cross-language validation vectors | IN PROGRESS | 59 vectors (ATP + ACP); Entity+Capability blocked on A3 |
| A5: SDK v0.9.0 release | DONE | PR #66 merged |

### Sprint 4 Summary: Cross-Language Schema Standardization (complete)

All tasks DONE: V1 (JSON Schemas), V2 (T3/V3 JSON-LD, PR #54 merged), V3 (R7 Action JSON-LD), V4 (160 validation vectors, PR #67 merged), V5 (SDK v0.8.0).

---

## SDK Status

- **Version**: 0.9.0
- **Modules**: 19 (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp, attestation)
- **Tests**: 1414 passing
- **Exports**: 271 symbols via `web4/__init__.py`
- **License**: MIT (SDK), AGPL-3.0 (root repo)

---

## JSON-LD Schema Completion

| Type | JSON-LD | JSON Schema | Test Vectors |
|------|---------|-------------|-------------|
| LCT | DONE | DONE | DONE (23 vectors) |
| AttestationEnvelope | DONE | DONE | DONE (20 vectors) |
| R7Action | DONE | DONE | DONE (20 vectors) |
| T3/V3 | DONE | DONE | DONE (38 vectors) |
| ATP/ADP | DONE | DONE | DONE (23 vectors) |
| ACP | DONE | DONE | DONE (36 vectors) |
| Entity | IN REVIEW (PR #63) | IN REVIEW (PR #63) | Blocked on A3 merge |
| Capability | IN REVIEW (PR #63) | IN REVIEW (PR #63) | Blocked on A3 merge |

**Total schema validation vectors**: 160 across 6 schemas

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
82e59bf V4 (complete): T3/V3 cross-language validation vectors — 38 vectors (#67)
6ea0d0b Add SESSION_PRIMER + SESSION_FOCUS: R7-framed session governance
227038a A5: SDK v0.9.0 release — Sprint 5 ATP/ADP and ACP JSON-LD (#66)
5069661 V2: T3/V3 Trust Tensor JSON-LD serialization — 58 tests (#54)
3495e13 A4 (partial): Cross-language validation vectors for ATP and ACP schemas — 59 vectors (#64)
```

---

## Open PRs

- PR #63: A3 Entity + Capability JSON-LD serialization — 37 tests, awaiting review

---

## Pending Items

- A4 completion — Entity + Capability vectors, blocked on PR #63 merging
- Sprint 6 planning — needed once Sprint 5 completes
- Whitepaper-SDK coherence: ongoing (last audit 2026-03-15, 4 divergences found and fixed)

---

*Updated by autonomous session, 2026-03-23*
