# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-03-22 (Session 70)*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 5 Summary: Core Type JSON-LD Phase 2

| Task | Status | Notes |
|------|--------|-------|
| A1: ATP/ADP JSON-LD | DONE | 28 tests, PR #60 merged |
| A2: ACP JSON-LD | DONE | 54 tests, PR #62 merged |
| A3: Entity + Capability JSON-LD | IN REVIEW | 37 tests, PR #63 |
| A4: Cross-language validation vectors | IN PROGRESS | 59 vectors (ATP + ACP), Entity+Cap deferred until A3 merges |
| A5: SDK v0.9.0 release | DONE | PR #66 merged |

### Sprint 4 Residual

| Task | Status | Notes |
|------|--------|-------|
| V4: Cross-language validation vectors | IN PROGRESS | 163 total vectors (T3/V3 done: 41 vectors). Entity+Cap deferred until A3 merges |

---

## SDK Status

- **Version**: 0.9.0
- **Modules**: 19 (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp, attestation)
- **Tests**: 1356+ passing
- **Exports**: 269 symbols via `web4/__init__.py`
- **License**: MIT (SDK), AGPL-3.0 (root repo)

---

## JSON-LD Schema Completion

| Type | JSON-LD | JSON Schema | Test Vectors |
|------|---------|-------------|-------------|
| LCT | DONE | DONE | DONE (23 vectors) |
| AttestationEnvelope | DONE | DONE | DONE (20 vectors) |
| R7Action | DONE | DONE | DONE (20 vectors) |
| T3/V3 | DONE (PR #54 merged) | DONE | DONE (41 vectors) |
| ATP/ADP | DONE (PR #60 merged) | DONE | DONE (23 vectors) |
| ACP | DONE (PR #62 merged) | DONE | DONE (36 vectors) |
| Entity | IN REVIEW (PR #63) | IN REVIEW | Deferred until A3 merges |
| Capability | IN REVIEW (PR #63) | IN REVIEW | Deferred until A3 merges |

**Total validation vectors**: 163 across 6 schemas

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
6ea0d0b Add SESSION_PRIMER + SESSION_FOCUS: R7-framed session governance
227038a A5: SDK v0.9.0 release — Sprint 5 ATP/ADP and ACP JSON-LD (#66)
5069661 V2: T3/V3 Trust Tensor JSON-LD serialization — 58 tests (#54)
3495e13 A4 (partial): Cross-language validation vectors for ATP and ACP schemas — 59 vectors (#64)
6300d34 A2: ACP JSON-LD serialization — 54 tests (#62)
```

---

## Open PRs

- PR #63: A3 Entity + Capability JSON-LD serialization — awaiting review

---

## Pending Items

- A3 review (PR #63) — blocking Entity+Capability validation vectors
- A4 completion — needs Entity+Capability vectors after A3 merges
- V4 completion — needs Entity+Capability vectors after A3 merges
- Sprint 6 planning — once Sprint 5 wraps up
- Whitepaper-SDK coherence: ongoing (last audit 2026-03-15, 4 divergences found and fixed)

---

*Updated by autonomous session, 2026-03-22 18:00*
