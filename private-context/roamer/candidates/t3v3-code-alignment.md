# Roamer Candidate: T3/V3 Fractal RDF Code Alignment

**Created**: 2026-02-13
**Updated**: 2026-02-17
**Priority**: High (Rust consolidation remains)
**Depends on**: Ontology and spec alignment (completed 2026-02-13)

## Status

### COMPLETED: Specs + Python (Phase 1-3)

All specification documents, schemas, and documentation updated and pushed (2026-02-13):
- `web4-standard/ontology/t3v3-ontology.ttl` — NEW, formal fractal ontology
- `web4-standard/ontology/t3v3.jsonld` — NEW, JSON-LD context
- All core specs (t3-v3-tensors.md, mrh-tensors.md, LCT spec) — canonical 3D + `subDimensionOf`
- JSON schemas (t3v3.schema.json, lct.schema.json) — `sub_dimensions` property added
- Docs (CANONICAL_TERMS, SOURCE_OF_TRUTH, EXECUTIVE_SUMMARY, QUICK_REFERENCE, CLAUDE.md)

### COMPLETED: Python Reference Implementations (Phase 4a)

- **`mrh_graph.py`** — Added `DimensionScore` dataclass, `SUB_DIMENSION_OF`/`HAS_DIMENSION_SCORE` relation types, `register_sub_dimension()`, `get_sub_dimensions(recursive=True)`, aggregation via `aggregate_root()`. Tested successfully.
- **`trust_tensor.py`** — Full rewrite. 6D flat → canonical 3D (talent/training/temperament, valuation/veracity/validity) + `sub_dimensions` dict. Added `aggregate_from_sub_dimensions()`, `recompute_roots()`, `from_legacy_6d()` classmethods for backward compat. Tested successfully.
- **Other Python files** — Background agent scanning remaining files (web4_full_stack_demo.py, lct_capability_levels.py, law_oracle.py, attack_demonstrations.py, etc.) for old 6D names.

### REMAINING: Rust Consolidation (Phase 4b)

This is the open work item. See detailed analysis below.

---

## Rust Crate Deep Analysis (February 2026)

### Crate 1: `web4-trust-core` (Jan 24, 2026)

**Location**: `web4-trust-core/`
**License**: MIT
**Files**: 20 `.rs` files

```
src/lib.rs
src/tensor/mod.rs, t3.rs, v3.rs
src/entity/mod.rs, trust.rs, types.rs
src/witnessing/mod.rs, event.rs, chain.rs
src/decay/mod.rs, temporal.rs
src/storage/mod.rs, traits.rs, memory.rs, file.rs
src/bindings/mod.rs, python.rs, wasm.rs
benches/trust_benchmarks.rs
```

**T3 Dimensions**: competence, reliability, consistency, witnesses, lineage, alignment
**V3 Dimensions**: energy, contribution, stewardship, network, reputation, temporal

**Math**: Simple arithmetic mean (`sum / 6.0`). Asymmetric deltas with fixed multipliers. Exponential decay toward floor 0.3.

**Unique features**: WitnessEvent/WitnessingChain (transitive trust), EntityTrust composite, DecayConfig (grace period/floor/rate), TrustStore trait + InMemoryStore + FileStore (JSON on disk), PyO3 0.20 bindings, WASM bindings, criterion benchmarks, Python compat tests.

**Persistence**: JSON files at `~/.web4/governance/entities/{sha256_hash[0:16]}.json`. Flattened T3/V3 fields as siblings via `#[serde(flatten)]`.

### Crate 2: `web4-core` (Jan 22, 2026)

**Location**: `web4-core/`
**License**: AGPL-3.0 (MetaLINXX Inc., patent-protected)
**Files**: 8 `.rs` files

```
src/lib.rs, t3.rs, v3.rs, coherence.rs, crypto.rs, error.rs, lct.rs
python/src/lib.rs
```

**T3 Dimensions**: Competence, Integrity, Benevolence, Predictability, Transparency, Accountability
**V3 Dimensions**: Utility, Novelty, Quality, Timeliness, Relevance, Leverage

**Math**: Weighted **geometric mean** for T3 (zero in any dimension zeros total), weighted **arithmetic mean** for V3 (allows specialization). **EMA** with decaying alpha (`0.5 / (1 + count/10)`). Per-dimension confidence weights via log growth. Per-dimension observation counts. Tensor merge weighted by observations. Euclidean distance. Specialized V3 aggregate for subsets.

**Unique features**: TrustDimension/ValueDimension enums (type-safe), LCT (full Ed25519, status, hardware binding, parent chain), Coherence (C*S*Phi*R), TrustRelation, TrustObservation. PyO3 0.22 (separate subcrate).

**No persistence layer.**

### Test Coverage

- **web4-trust-core**: ~50 tests across 9 modules (tensor, entity, witnessing, storage, decay)
- **web4-core**: ~30 tests across 6 modules (lib, t3, v3, coherence, lct, crypto)

### Dependency Differences

| | web4-trust-core | web4-core |
|--|-----------------|-----------|
| PyO3 | 0.20 | 0.22 |
| Crypto | None | ed25519-dalek 2.1, sha2 |
| Storage | sled (optional), serde_json | serde_json only |
| WASM | wasm-bindgen, js-sys | None |

---

## Consolidation Recommendation

### Math: web4-core wins

1. Weighted geometric mean for T3 prevents "all-but-one" attack
2. Per-dimension confidence weights prevent gaming
3. EMA with decaying alpha is the correct update model
4. Observation counting provides audit trail
5. Merge capability enables federation
6. T3=geometric, V3=arithmetic is philosophically sound (trust requires all dimensions, value allows specialization)

### Infrastructure: web4-trust-core wins

1. Only working WASM bindings
2. More complete Python surface (TrustStore, witnessing, dict export)
3. WitnessEvent/WitnessingChain (only implementation)
4. DecayConfig (more configurable)
5. Storage trait + FileStore (only implementation)
6. Criterion benchmarks (only implementation)
7. Python compat tests (only implementation)

### Recommended Architecture

| Component | Source | Rationale |
|-----------|--------|-----------|
| T3/V3 tensor math | web4-core | Superior EMA, weights, geometric mean |
| TrustDimension/ValueDimension enums | web4-core | Type-safe dimension access |
| LCT | web4-core | Only implementation |
| Coherence (C*S*Phi*R) | web4-core | Only implementation |
| Crypto (Ed25519) | web4-core | Only implementation |
| EntityTrust composite | web4-trust-core | Richer witnessing, action counts |
| WitnessEvent/WitnessingChain | web4-trust-core | Only implementation |
| DecayConfig | web4-trust-core | More configurable |
| TrustStore + InMemoryStore | web4-trust-core | Only implementation |
| FileStore (JSON) | web4-trust-core | Only implementation |
| PyO3 bindings | web4-trust-core (rewired) | More complete surface |
| WASM bindings | web4-trust-core (rewired) | Only implementation |
| Benchmarks | web4-trust-core | Only implementation |

### Dimension Name Mapping (6D → 3D roots)

The old 6D dimensions are flattened instantiations of the canonical 3-root ontology:

```
Talent → { Competence } (web4-core) or { competence } (web4-trust-core)
Training → { Transparency, Accountability } or { witnesses, lineage }
Temperament → { Integrity, Benevolence, Predictability } or { reliability, consistency, alignment }

Valuation → { Utility, Leverage } or { energy, network }
Veracity → { Quality, Relevance } or { contribution, reputation }
Validity → { Novelty, Timeliness } or { stewardship, temporal }
```

This mapping should be documented. The refactored crate uses 3 root `f64` + `HashMap<String, f64>` for sub-dimensions, matching the Python implementations.

---

## Migration Path

### Phase 1: Make web4-trust-core depend on web4-core
- Add `web4-core = { path = "../web4-core" }` to Cargo.toml
- Replace `T3Tensor` (6 named fields) with wrapper around `web4_core::T3`
- Replace `V3Tensor` with wrapper around `web4_core::V3`
- Adapt EntityTrust to use `T3::observe()` instead of `T3Tensor::update_from_outcome()`

### Phase 2: Serialization migration
Current persisted format (flattened named fields):
```json
{
  "entity_id": "mcp:filesystem",
  "competence": 0.5,
  "reliability": 0.5
}
```
web4-core serializes as:
```json
{
  "dimensions": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
  "weights": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
  "observation_counts": [0, 0, 0, 0, 0, 0]
}
```
Write custom serde layer that reads old flat format AND new array format. Always write new format.

### Phase 3: Update bindings
- PyO3: Expose TrustDimension/ValueDimension enums, upgrade to 0.22
- WASM: Same adaptation
- `to_dict()`/`toJSON()` output dimension names from enums

### Phase 4: Update consumers
- `simulations/trust_integration.py` — updated field names
- Claude-code-plugin bridge module — updated imports
- Python compat test — rewrite for new API

## What Breaks

1. **JSON persistence**: Files in `~/.web4/governance/entities/` become incompatible. Needs migration script or backward-compat serde.
2. **Python API surface**: `trust.competence` → `trust.score(TrustDimension.Competence)`. `update_from_outcome(success, magnitude)` → `observe(dimension, score)`.
3. **WASM API surface**: Same field name changes.
4. **trust_integration.py**: Hardbound metric mappings need updating.
5. **Dimension semantics**: "witnesses" and "lineage" from web4-trust-core are metadata, not tensor dimensions. Semantic loss unless mapping designed carefully.
6. **PyO3 version**: 0.20 → 0.22 is a breaking API change (`&PyModule` → `&Bound<'_, PyModule>`).
7. **License**: web4-trust-core=MIT, web4-core=AGPL-3.0. Combined work = AGPL-3.0. **Needs explicit decision.**

## Risk Assessment

- **Python**: COMPLETED. Low risk, mostly renames.
- **Rust consolidation**: Medium-high. Two incompatible crates, 80+ tests, binding layers.
- **Data migration**: Medium. Known JSON persistence on disk with old field names.
- **License conflict**: **Decision required** — MIT vs AGPL-3.0 affects all downstream.

## Acceptance Criteria

1. ~~All Python implementations use canonical 3D root + sub_dimensions pattern~~ DONE
2. ~~`mrh_graph.py` supports `web4:subDimensionOf` edges~~ DONE
3. Rust crates consolidated or clearly separated with shared types
4. All dimension names match canonical: talent/training/temperament, valuation/veracity/validity
5. No references to old 6D names in active code
6. ~~`grep "technical_competence\|social_reliability" web4-standard/implementation/` returns 0~~ DONE
