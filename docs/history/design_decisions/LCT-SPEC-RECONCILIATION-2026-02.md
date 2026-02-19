# LCT Spec Reconciliation — February 2026

**Date**: 2026-02-19
**Status**: ACTIVE — divergences documented, partial fixes applied
**Purpose**: Track and resolve inconsistencies across LCT implementations

---

## 1. Summary

A comprehensive survey of all LCT-related implementations reveals 6 categories of divergence
across Python, TypeScript, Rust/WASM, JSON Schema, and specification documents. This document
captures findings and tracks fixes.

---

## 2. Divergence Matrix

### 2.1 T3/V3 Tensor Dimensions

| Implementation | T3 Dimensions | V3 Dimensions | Status |
|---------------|---------------|---------------|--------|
| `core/lct_capability_levels.py` | 6-dim (legacy) | 6-dim (legacy) | LEGACY — migrate or remove |
| `web4-standard/implementation/reference/lct_capability_levels.py` | 3-dim canonical | 3-dim canonical | CANONICAL |
| `web4-standard/schemas/lct.schema.json` | 3-dim canonical | 3-dim canonical | CANONICAL |
| `web4-standard/ontology/t3v3-ontology.ttl` | 3-dim canonical | 3-dim canonical | CANONICAL |
| `web4-standard/core-spec/LCT-linked-context-token.md` | 3-dim canonical | 3-dim canonical | CANONICAL |
| `web4-trust-core/src/tensor/t3.rs` | 3-dim canonical | 3-dim canonical | CANONICAL (has migration fn) |
| `web4-core/src/lct.rs` | No tensors | No tensors | Identity-only |
| `implementation/reference/web4_entity.py` | 3-dim canonical | 3-dim canonical | CANONICAL (new, Feb 2026) |

**Legacy 6-dim T3**: `technical_competence, social_reliability, temporal_consistency, witness_count, lineage_depth, context_alignment`

**Canonical 3-dim T3**: `talent, training, temperament`

**Migration path** (from `web4-trust-core/src/tensor/t3.rs`):
```
talent = competence
training = avg(reliability, consistency, lineage)
temperament = avg(witnesses, alignment)
```

**Resolution**: The `core/lct_capability_levels.py` 6-dim version is legacy. All new code
uses canonical 3-dim. The legacy file should be updated with a deprecation notice and
re-export from the canonical version, or removed entirely if nothing depends on it.

### 2.2 Entity Type Count

| Source | Count | Types |
|--------|-------|-------|
| `entity-types.md` (spec) | **15** | Core 12 + Society + Policy + Infrastructure |
| `lct.schema.json` | **14** | Core 12 + Policy + Infrastructure (FIXED 2026-02-19) |
| Python `EntityType` enum (both) | **19** | Core 12 + plugin, session, relationship, pattern, society, witness, pending |
| `web4-core/src/lct.rs` | **8** | Human, AiSoftware, AiEmbodied, Org, Role, Task, Resource, Hybrid |
| `web4-trust-core/src/entity/types.rs` | **6** | Mcp, Role, Session, Reference, Lct, Other (operational) |
| `web4_entity.py` (fractal DNA) | **15** | Matches spec exactly |

**Resolution**: The `entity-types.md` spec (15 types) is authoritative. Schema updated to 14
(Policy + Infrastructure added; Society should be added separately since it's in the spec).
Python enums have 4 extra extended types (plugin, session, relationship, pattern) that may
be valid operational types but are NOT in the core spec. Rust crates need updating.

**Note**: The Python `EntityType` includes `society` but the core spec treats Society as one of
the 15. The Rust `web4-core` uniquely splits AI into `AiSoftware`/`AiEmbodied` — this is a
useful distinction not captured in the spec.

### 2.3 MRH Witnessing Roles

| Source | Roles |
|--------|-------|
| LCT spec (markdown) | `time, audit, oracle, existence, action, state, quality` (7) |
| JSON Schema (before fix) | `time, audit, oracle, peer` (4) |
| JSON Schema (after fix) | `time, audit, oracle, peer, existence, action, state, quality` (8) |

**Resolution**: Schema updated 2026-02-19 to include all roles from spec plus `peer`.

### 2.4 Birth Certificate Requirements

| Field | Core Spec | JSON Schema (before) | JSON Schema (after) | Python |
|-------|-----------|---------------------|--------------------|----|
| `issuing_society` | Required | Not required | **Required** (FIXED) | Required |
| `citizen_role` | Required | Required | Required | Required |
| `birth_witnesses` | Min 3 | Min 1 | Min 1 | Min 3 |
| `context` | Not explicit | Required | Required | Not used |

**Resolution**: `issuing_society` added to required fields in schema (2026-02-19).
`birth_witnesses` minimum should be 3 per spec but schema says 1 — left as-is for now
since bootstrap scenarios may need 1 witness.

### 2.5 TypeScript Coverage

`ledgers/reference/typescript/lct-parser.ts` — URI parser only.

**Missing in TypeScript**:
- Full LCT document model (T3/V3/MRH/binding/birth_certificate)
- Entity type registry
- Capability levels
- Tensor operations
- LCT validation

**Gap**: The TypeScript ecosystem has no way to work with full LCT documents.
The URI parser handles `lct://component:instance:role@network` wire format
but none of the document structure.

### 2.6 LCT ID Format

| Implementation | Format | Example |
|---------------|--------|---------|
| Python | `lct:web4:{entity_type}:{hash16}` | `lct:web4:ai:abc123def456` |
| Core Spec | `lct:web4:mb32:{hash}` | `lct:web4:mb32:bafk...` |
| JSON Schema | `^lct:web4:[A-Za-z0-9_-]+$` | Permissive regex |
| TypeScript | `lct://{component}:{instance}:{role}@{network}` | Different scheme entirely |

**Resolution**: The URI format (`lct://...`) is a transport/addressing format.
The document format (`lct:web4:...`) is the identity format. Both are valid
in different contexts. The JSON schema regex is intentionally permissive to
accommodate both. This is not actually a conflict — it's two views of the same identity.

---

## 3. Fixes Applied (2026-02-19)

| Fix | File | Description |
|-----|------|-------------|
| Entity types | `lct.schema.json` | Added `policy`, `infrastructure`, `society` to binding.entity_type enum |
| Witness roles | `lct.schema.json` | Added `existence, action, state, quality` to mrh.witnessing.role enum |
| Birth cert | `lct.schema.json` | Added `issuing_society` to required fields and properties |
| Deprecation | `core/lct_capability_levels.py` | Added deprecation notice for legacy 6-dim T3/V3 |

---

## 4. Remaining Actions

### Priority 1 (High Impact)

- [x] **Deprecate `core/lct_capability_levels.py`**: Deprecation notice added (2026-02-19)
  pointing to `web4-standard/implementation/reference/lct_capability_levels.py`.
  15+ session/test files import EntityType from it — retained for compatibility.
- [x] **Add `society` to JSON schema entity_type enum**: Added 2026-02-19.

### Priority 2 (Medium Impact)

- [ ] **TypeScript LCT document model**: Build full document type definitions matching
  `lct.schema.json`. This blocks TypeScript-based trust applications.
- [ ] **Update `web4-core` Rust entity types**: Align with 15-type spec. Decide whether
  `AiSoftware`/`AiEmbodied` split should propagate to spec or be removed.
- [ ] **Add T3/V3 tensors to `web4-core/src/lct.rs`**: Currently identity-only. Tensors
  are in separate `web4-trust-core` crate with no formal attachment.

### Priority 3 (Low Impact)

- [ ] **birth_witnesses minimum**: Schema says minItems=1, spec says 3. Consider updating
  schema to minItems=3 or documenting the bootstrap exception.
- [ ] **Extended entity types in Python**: Document whether `plugin, session, relationship,
  pattern, pending` are intentional extensions or should be removed from the enum.
- [ ] **Unify attestation chain format**: TPM quote and PSA token normalization for
  cross-machine verification (addressed in CMTVP spec).

---

## 5. Architectural Observation

The divergence pattern reveals a natural layering:

```
Spec Layer (authoritative):
  entity-types.md → 15 types (canonical)
  LCT-linked-context-token.md → 3-dim T3/V3 (canonical)
  t3v3-ontology.ttl → formal RDF model

Schema Layer (wire format):
  lct.schema.json → JSON validation (NOW aligned with spec)

Implementation Layer (operational):
  Python (core/ and web4-standard/) → divergent, being reconciled
  Rust (web4-core, web4-trust-core) → split across crates
  TypeScript (ledgers/) → URI only, no document model

Simulation Layer (research):
  web4_entity.py → canonical 3-dim, matches spec
```

The spec and schema layers are now aligned. Implementation layers lag behind.
This is expected in a research project — spec leads, implementation follows.

---

*"Divergence is data. It tells you where the system grew faster than its documentation."*
