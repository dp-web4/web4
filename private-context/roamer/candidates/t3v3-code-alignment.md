# Roamer Candidate: T3/V3 Fractal RDF Code Alignment

**Created**: 2026-02-13
**Updated**: 2026-02-17
**Priority**: Low (all phases complete, only Rust toolchain testing remains)
**Status**: ALL CODE ALIGNMENT COMPLETE

## Status Summary

### COMPLETED: Specs + Python (Phase 1-3) — 2026-02-13

All specification documents, schemas, and documentation updated and pushed:
- `web4-standard/ontology/t3v3-ontology.ttl` — NEW, formal fractal ontology
- `web4-standard/ontology/t3v3.jsonld` — NEW, JSON-LD context
- All core specs (t3-v3-tensors.md, mrh-tensors.md, LCT spec) — canonical 3D + `subDimensionOf`
- JSON schemas (t3v3.schema.json, lct.schema.json) — `sub_dimensions` property added
- Docs (CANONICAL_TERMS, SOURCE_OF_TRUTH, EXECUTIVE_SUMMARY, QUICK_REFERENCE, CLAUDE.md)

### COMPLETED: Python Reference Implementations (Phase 4a) — 2026-02-17

- **`mrh_graph.py`** — DimensionScore, subDimensionOf, register_sub_dimension, aggregate_root
- **`trust_tensor.py`** — Full rewrite 6D→3D + sub_dimensions dict
- **`lct_capability_levels.py`** — Updated with canonical 3D names

### COMPLETED: web4-core Rust Refactor (Phase 4b-1) — 2026-02-17

- License: AGPL-3.0 → MIT (all source headers + LICENSE file)
- `src/t3.rs` — 6D→3D (Talent/Training/Temperament) + SubDimensionScore + HashMap
- `src/v3.rs` — 6D→3D (Valuation/Veracity/Validity) + SubDimensionScore + HashMap
- `src/lib.rs` — Updated tests and docs
- `python/src/lib.rs` — PyO3 0.22 bindings with canonical 3D

### COMPLETED: web4-trust-core Rust Refactor (Phase 4b-2) — 2026-02-17

- `src/tensor/t3.rs` — 6D→3D (talent/training/temperament) + `from_legacy_6d()` migration
- `src/tensor/v3.rs` — 6D→3D (valuation/veracity/validity) + `from_legacy_6d()` migration
- `src/tensor/mod.rs` — Updated docs
- `src/entity/trust.rs` — Backward-compatible serde (reads old 6D JSON, writes canonical 3D)
- `src/bindings/python.rs` — PyO3 with canonical 3D getters/setters
- `src/bindings/wasm.rs` — wasm-bindgen with canonical 3D getters/setters
- `src/storage/file.rs` — Test assertions updated
- `src/witnessing/mod.rs` — Doc comments updated
- `src/lib.rs` — Updated docs

## Backward Compatibility

### JSON Persistence Migration
The serde layer in `entity/trust.rs` supports both formats:
- **Write**: Always outputs canonical 3D names (talent, training, temperament, valuation, veracity, validity)
- **Read**: Accepts both canonical 3D AND legacy 6D (competence, reliability, etc.)
- **Migration**: Automatic on first read-then-save cycle

### Legacy 6D → Canonical 3D Mapping
```
T3:
  talent = competence
  training = avg(reliability, consistency, lineage)
  temperament = avg(witnesses, alignment)

V3:
  valuation = avg(energy, contribution)
  veracity = reputation
  validity = avg(stewardship, network, temporal)
```

## Remaining: Testing (when Rust toolchain available)

No Rust toolchain on current WSL2 machine. When cargo is available:
1. `cd web4-core && cargo test`
2. `cd web4-trust-core && cargo test`
3. `cd web4-core/python && maturin develop && python -c "import web4; print(web4.version())"`

## Acceptance Criteria

1. ~~All Python implementations use canonical 3D root + sub_dimensions pattern~~ DONE
2. ~~`mrh_graph.py` supports `web4:subDimensionOf` edges~~ DONE
3. ~~Rust crates use canonical dimension names~~ DONE
4. ~~All dimension names match canonical: talent/training/temperament, valuation/veracity/validity~~ DONE
5. ~~No references to old 6D names in active code (only in legacy compat paths)~~ DONE
6. ~~Backward-compatible JSON deserialization~~ DONE
7. Rust tests pass (BLOCKED: no cargo on this machine)
