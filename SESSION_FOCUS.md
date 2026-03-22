# Web4 Session Focus

*Current sprint, SDK status, and active work. Updated by operator and autonomous sessions.*

*Last updated: 2026-03-22*

---

## Current Sprint

**See `docs/SPRINT.md` for full sprint plan and task details.** Do not duplicate sprint content here — SPRINT.md is the source of truth for task scope, status, and dependencies.

### Sprint 5 Summary: Core Type JSON-LD Phase 2

| Task | Status | Notes |
|------|--------|-------|
| A1: ATP/ADP JSON-LD | IN REVIEW | 28 tests, PR merged |
| A2: ACP JSON-LD | IN REVIEW | 54 tests, PR merged |
| A3: Entity + Capability JSON-LD | NOT STARTED | |
| A4: Cross-language validation vectors | IN PROGRESS | 59 vectors (ATP + ACP partial) |
| A5: SDK v0.9.0 release | NOT STARTED | Depends on A1+ |

---

## SDK Status

- **Version**: 0.8.0
- **Modules**: 18 (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, reputation, security, protocol, mcp)
- **Tests**: 1356+ passing (as of Sprint 5 A2 completion)
- **Exports**: 266+ symbols via `web4/__init__.py`
- **License**: MIT (SDK), AGPL-3.0 (root repo)

---

## JSON-LD Schema Completion

| Type | JSON-LD | JSON Schema | Test Vectors |
|------|---------|-------------|-------------|
| LCT | DONE | DONE | DONE (10 vectors) |
| AttestationEnvelope | DONE | DONE | DONE |
| R7Action | DONE | DONE | DONE (21+42 vectors) |
| T3/V3 | IN REVIEW (PR #54) | IN REVIEW | Deferred until PR merges |
| ATP/ADP | IN REVIEW | IN REVIEW | 23 vectors |
| ACP | IN REVIEW | IN REVIEW | 36 vectors |
| Entity | NOT STARTED | NOT STARTED | — |
| Capability | NOT STARTED | NOT STARTED | — |

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
3495e13 A4 (partial): Cross-language validation vectors for ATP and ACP schemas — 59 vectors (#64)
6300d34 A2: ACP JSON-LD serialization — 54 tests (#62)
639cdeb A1: ATP/ADP JSON-LD serialization — 28 tests (#60)
66b68d3 V5: SDK v0.8.0 release — Sprint 4 schema standardization (#58)
1b70c10 Autonomous web4 session 20260321-000045 (safety net) (#56)
```

---

## Open PRs

- PR #54: T3/V3 Trust Tensor JSON-LD serialization (V2) — awaiting review

---

## Pending Items

- A3 (Entity + Capability JSON-LD) — next unstarted sprint task
- A4 completion — needs A3 vectors after PR #63 merges
- A5 (SDK v0.9.0) — release housekeeping after Sprint 5 tasks complete
- V4 completion — T3/V3 vectors deferred until PR #54 merges
- Whitepaper-SDK coherence: ongoing (last audit 2026-03-15, 4 divergences found and fixed)

---

*Updated by operator, 2026-03-22*
