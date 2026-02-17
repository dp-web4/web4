# Roamer Candidate: T3/V3 Fractal RDF Code Alignment

**Created**: 2026-02-13
**Priority**: High
**Depends on**: Ontology and spec alignment (completed 2026-02-13)

## Context

The T3/V3 ontology (`web4-standard/ontology/t3v3-ontology.ttl`) and all specification documents have been updated to make the fractal RDF sub-dimension model normative. The specs now declare:

- 3 root dimensions per tensor (T3: Talent/Training/Temperament, V3: Valuation/Veracity/Validity)
- Each root is a node in an open-ended RDF sub-graph via `web4:subDimensionOf`
- Both shorthand (`web4:talent 0.95`) and full (`web4:hasDimensionScore`) forms are valid
- JSON schemas allow `sub_dimensions` objects

**The code implementations still use hardcoded 6D flat arrays with non-canonical dimension names.**

## Scope

### Rust Crates (2 competing, incompatible)

#### `web4-trust-core/src/tensor/t3.rs` (311 lines)
- 6D: competence, reliability, consistency, witnesses, lineage, alignment
- `pub struct T3Tensor` with 6 `pub f64` fields
- PyO3 bindings in `t3.rs` with hardcoded field names
- WASM bindings in `wasm.rs` with hardcoded field names
- Consumers: `tensor/mod.rs`, `tensor/v3.rs`, `lib.rs`

#### `web4-core/src/t3.rs` (285 lines)
- 6D: Competence, Integrity, Benevolence, Predictability, Transparency, Accountability
- `pub const T3_DIMENSIONS: usize = 6;` with `[f64; T3_DIMENSIONS]`
- More sophisticated: observation model with EMA, weighted geometric mean
- Has `TrustRelation` struct (from_id, to_id, T3) — closest to RDF edge
- Consumers: `lib.rs`, `v3.rs`, `reputation.rs`

### Python Reference Implementation

#### `web4-standard/implementation/reference/trust_tensor.py` (638 lines)
- Uses web4-trust-core's 6D names
- Line 9-10 already notes: "A reconciliation is needed in the spec documentation"
- `EntityTensorStore` with role-contextual nesting (closest to target model)

#### `web4-standard/implementation/reference/mrh_graph.py`
- Already uses 3D: talent/training/temperament stored as RDF triples
- **Closest to target** — mostly just needs `subDimensionOf` edge support

### Other Python Files Using Old 6D Names

Found via `grep -rl "technical_competence\|social_reliability"`:
- `web4_full_stack_demo.py`
- `web4_ep_performance_benchmark.py`
- `test_relationship_coherence_ep.py`
- `relationship_coherence_ep.py`
- `lct_capability_levels.py`
- `law_oracle.py`
- `attack_demonstrations.py`
- `ATTACK_VECTOR_ANALYSIS.md`
- `schema_action_sequences.sql`

## Recommended Approach

### Phase 1: Python (lower risk, highest payoff)

1. **`mrh_graph.py`** — Already nearly correct. Add `subDimensionOf` edge support and aggregation method.

2. **`trust_tensor.py`** — Map existing 6D to root + sub-dimension hierarchy. The `EntityTensorStore` with role-contextual nesting is already close. Change field names, add `sub_dimensions` dict.

3. **Other Python files** — Search-and-replace dimension names, update test data.

### Phase 2: Rust Consolidation (higher risk)

**Critical decision first**: Which crate survives?

| Aspect | web4-trust-core | web4-core |
|--------|----------------|-----------|
| Sophistication | Basic (simple average) | Advanced (EMA, geometric mean) |
| Bindings | PyO3 + WASM | None |
| Edge model | No relation struct | `TrustRelation` (closest to RDF) |
| Consumers | Less | More |

**Recommended**: Keep `web4-core` math, add `web4-trust-core` bindings. But this needs careful analysis of all consumers.

Refactor approach:
1. Define canonical `T3Tensor` with 3 root `f64` + `HashMap<String, f64>` for sub-dimensions
2. Implement `From<[f64; 6]>` for backward compatibility during migration
3. Update PyO3/WASM bindings
4. Migrate consumers one at a time with tests

### Phase 3: Serialized Data

Check for any persisted data on disk using old field names. Will need migration script.

## Risk Assessment

- **Python**: Low risk. Mostly renames and restructuring. Good test coverage exists.
- **Rust**: Medium-high risk. Two incompatible crates, binding layers, and no test suite visible.
- **Data migration**: Unknown risk. Need to check if any JSON/CBOR data is persisted.

## Acceptance Criteria

1. All Python implementations use canonical 3D root + sub_dimensions pattern
2. `mrh_graph.py` supports `web4:subDimensionOf` edges
3. Rust crates consolidated or clearly separated with shared types
4. All dimension names match canonical: talent/training/temperament, valuation/veracity/validity
5. No references to old 6D names (competence, reliability, consistency, etc.) in active code
6. `grep "technical_competence\|social_reliability" web4-standard/implementation/` returns 0
