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
| `presence-protocol-conformance.json` | Presence Protocol v0: 8 tools + 6 resources + error envelope. See spec at [`core-spec/presence-protocol.md`](../../core-spec/presence-protocol.md). | 10 |

## Presence-protocol harness (live daemon)

The `presence-protocol-conformance.json` file is consumed by per-SDK
runners in the [`dp-web4/hestia`](https://github.com/dp-web4/hestia)
repo. Each runner spins up a connection to a running Hestia daemon and
exercises every scenario:

| Language | Path | Command |
|---|---|---|
| TypeScript | `hestia/plugin-sdk/typescript/test/conformance/conformance.test.ts` | `RUN_CONFORMANCE=1 npm test -- test/conformance/` |
| Python    | `hestia/plugin-sdk/python/tests/conformance/test_conformance.py`     | `RUN_CONFORMANCE=1 pytest tests/conformance/` |
| Rust      | `hestia/plugin-sdk/rust/tests/conformance.rs`                        | `RUN_CONFORMANCE=1 cargo test --test conformance` |

All three runners auto-skip if no daemon is reachable at
`$HESTIA_ENDPOINT` (default `http://127.0.0.1:7711/mcp`); set
`RUN_CONFORMANCE=1` to require it. All three resolve this directory
automatically, or accept `$WEB4_STANDARD_CONFORMANCE` as an override.

### Scenario format

Each scenario has tool/resource steps with optional setup, capture, and
expect clauses. Cross-scenario state flows via `{{P0-XXX.fieldName}}`
interpolation against prior captures. See the file header for the full
schema; key supported field-check predicates: `equals`,
`matchesPattern`, `startsWith`, `isInteger`/`isNumber`/`isBoolean`/
`isString`/`isArray`/`isIso8601`/`isNonEmptyString`, `isIn`, `min`,
`max`, `minLength`. The runners also validate ordering via
`{field, monotonic}`.

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
