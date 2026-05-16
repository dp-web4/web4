# Web4 Conformance Test Vectors

Machine-readable test vectors for cross-language conformance testing.
Any Web4 implementation (Rust, Python, TypeScript, WASM) MUST produce
identical results for these inputs.

## Test Suites

| File | Coverage | Vectors |
|------|----------|---------|
| `tensor-operations.json` | T3/V3 tensors: construction, update, decay, levels, sub-dimensions | 8 |
| `atp-operations.json` | ATP/ADP: accounts, lock/commit/rollback, transfers, conservation, sliding scale | 11 |
| `r6-r7-actions.json` | R6/R7: validation, reputation deltas, role contextualization, chain determinism | 8 |
| `society-roles.json` | Society: bootstrap, lifecycle, roles, rotation, federation, minimum viable | 8 |

## How to Use

### From Rust (web4-core)
```rust
let vectors: serde_json::Value = serde_json::from_str(
    include_str!("testing/conformance/tensor-operations.json")
)?;
// Assert your implementation matches expected outputs
```

### From Python (web4-core)
```python
import json
vectors = json.load(open("testing/conformance/tensor-operations.json"))
for v in vectors["t3_vectors"]:
    # Assert your implementation matches v["expected"]
```

### From TypeScript (Hardbound / web4-trust-core WASM)
```typescript
import vectors from './conformance/tensor-operations.json';
// Assert your implementation matches expected outputs
```

## Key Invariants

1. **ATP Conservation**: `sender_deducted == actual_credit + fee + overflow`
2. **Role-LCT Stability**: Role rotation MUST NOT change the role's LCT ID
3. **Reputation Context**: All T3/V3 deltas bind to `role_lct`, never global
4. **Hash Determinism**: Same action inputs → identical canonical hash
5. **Level Thresholds**: ≥0.8=high, ≥0.5=medium, ≥0.2=low, <0.2=untrusted

## Contributing Vectors

When adding new vectors:
- Use the `$schema` field for machine-parseable format
- Include `invariant` fields for properties that MUST hold
- Mark tolerance for floating-point comparisons (`tolerance: 1e-10`)
- Every vector needs an `id` and `description`

## Vector Freshness

Vectors are authored against a snapshot of an SDK data-structure shape. When
that shape later changes (new/renamed/re-defaulted field), a pre-change vector
can keep passing while silently testing outdated semantics — the adapter's
forward-compatible `.get(key, default)` masks the drift. Before merging a PR
that changes a vector file **or** an SDK dataclass a conformance adapter
constructs, follow the pre-merge checklist in
[`VECTOR-FRESHNESS.md`](VECTOR-FRESHNESS.md).
