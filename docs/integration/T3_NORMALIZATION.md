# T3/V3 Normalization — Cross-System Mapping

**Status**: Canonical reference for Phase 0 alignment
**Date**: 2026-03-06

## Web4 Canonical Definitions

### T3 (Trust Tensor)

| Dimension | Canonical Name | Semantics |
|-----------|---------------|-----------|
| T3.1 | **Talent** | Innate or role-specific capability |
| T3.2 | **Training** | Learned skills and demonstrated growth |
| T3.3 | **Temperament** | Consistency, ethics, behavioral stability |

Source: `web4-standard/ontology/t3v3-ontology.ttl`, `web4-standard/core-spec/t3-v3-tensors.md`

### V3 (Value Tensor)

| Dimension | Canonical Name | Semantics |
|-----------|---------------|-----------|
| V3.1 | **Valuation** | Economic or utility value |
| V3.2 | **Veracity** | Truthfulness and accuracy |
| V3.3 | **Validity** | Logical soundness and applicability |

Source: `web4-standard/ontology/t3v3-ontology.ttl`

## System Alignment Status (March 2026)

| System | T3 Names | V3 Names | Status |
|--------|----------|----------|--------|
| **Web4 spec** | Talent/Training/Temperament | Valuation/Veracity/Validity | Canonical |
| **ACT (racecarweb/)** | talent_score/training_score/temperament_score | — | Aligned |
| **ACT (act/ proto)** | talent/training/temperament | valuation/veracity/validity | Aligned (fixed 2026-03-06) |
| **ACT (trust_types.go)** | Talent/Training/Temperament | Valuation/Veracity/Validity | Aligned (fixed 2026-03-06) |
| **Hardbound (runtime)** | talent/training/temperament | — | Aligned |
| **Hardbound (docs)** | competence/reliability/integrity | — | Docs stale, runtime correct |
| **SAGE** | (abstracted — no hardcoded names) | — | Compatible |

### Historical Names (Do Not Use)

These names appeared in earlier implementations. They are superseded by the canonical names above.

| Old Name | Canonical Replacement | Where It Appeared |
|----------|----------------------|-------------------|
| Competence | Talent | ACT act/ proto, Hardbound MVP docs |
| Reliability | Training | ACT act/ proto, Hardbound MVP docs |
| Transparency | Temperament | ACT act/ proto |
| Integrity | Temperament | Hardbound MVP docs, SAGE (retired) |
| Benevolence | (dropped) | SAGE 4-dim model (retired) |
| Economic | Valuation | ACT act/ proto |
| Social | Veracity | ACT act/ proto |
| Knowledge | Validity | ACT act/ proto |
| Value | Valuation | ACT trust_types.go |

### SAGE Compatibility Note

SAGE uses an abstracted `TrustTensor` dataclass with generic `trust_score` and `confidence` fields rather than hardcoding dimension names. This makes it inherently compatible with any naming scheme. When SAGE syncs trust to ACT chain, the bridge layer maps to canonical T3 names.

SAGE's internal 4-dimension model (Competence/Reliability/Benevolence/Integrity) in `identity.json` predates this normalization. A migration path is documented in the ecosystem integration plan but is not required for Phase 0 — SAGE works through the abstraction layer.

## For Implementers

When building cross-system integrations:

1. **Always use canonical names** at system boundaries (APIs, protos, chain state)
2. **Internal names are fine** as long as boundary translation exists
3. **T3 is always 3 dimensions** — no 4th dimension. Systems with 4 dimensions should map to 3.
4. **V3 is always 3 dimensions** — Valuation/Veracity/Validity
5. **Trust is a relationship** (source → target in role/context), not a property of an entity
