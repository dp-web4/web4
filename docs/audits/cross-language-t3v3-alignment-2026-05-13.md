# Cross-Language T3/V3 Semantic Alignment Audit

**Date**: 2026-05-13
**Track**: web4 (Legion autonomous session, Sprint 47 T1)
**Triggered by**: Operator commit `55b1a3d8` (WASM rebuild for canonical 3D tensors, "Driven by Hardbound alignment audit")
**Scope**: Compare `web4-trust-core` (Rust/WASM) against canonical test vectors and Python SDK

---

## Purpose

The operator rebuilt the web4-trust-core WASM package to fix dimension naming
(legacy 6D → canonical 3D: Talent/Training/Temperament, Valuation/Veracity/Validity).
The naming surface is now correct, but the **behavioral semantics** — how composites
are calculated, how updates work, how decay is applied — remain significantly
divergent from both the canonical test vectors and the Python SDK.

This audit documents every semantic divergence so that the operator (or a
Rust-toolchain-equipped session) can bring the Rust implementation into
conformance before hardbound relies on it in production.

## Authoritative Sources

| Source | Role | Location |
|--------|------|----------|
| **Test vectors** | Normative ("All implementations MUST produce identical results") | `web4-standard/test-vectors/t3v3/tensor-operations.json` |
| **Spec** | Normative (core-spec defines semantics) | `web4-standard/core-spec/t3-v3-tensors.md` |
| **Python SDK** | Reference implementation (validates against test vectors in CI) | `web4-standard/implementation/sdk/web4/trust.py` |
| **Rust** | Subject of audit | `web4-trust-core/src/tensor/t3.rs`, `v3.rs`, `entity/trust.rs` |

---

## Divergence Summary

| # | Divergence | Severity | Test Vector | Rust Location |
|--:|-----------|----------|-------------|---------------|
| 1 | Talent decay applied | **CRITICAL** | t3v3-012 | `t3.rs:157` |
| 2 | T3 composite: unweighted | HIGH | t3v3-001 | `t3.rs:73` |
| 3 | V3 composite: unweighted | HIGH | t3v3-002 | `v3.rs:72` |
| 4 | T3 update: wrong formula | HIGH | t3v3-003, t3v3-004 | `t3.rs:89-105` |
| 5 | T3 decay: wrong model | HIGH | t3v3-012 | `t3.rs:137-161` |
| 6 | No ActionOutcome evolution | MEDIUM | t3v3-011 | N/A (missing) |
| 7 | Legacy 6D bridge: wrong formula | MEDIUM | t3v3-008 | `t3.rs:205-218` |
| 8 | Missing test vector operations | LOW | t3v3-007,009-015 | N/A |

**Critical**: 1 &nbsp; **High**: 4 &nbsp; **Medium**: 2 &nbsp; **Low**: 1

---

## Detailed Divergences

### 1. CRITICAL — Talent Decay Applied (Spec Violation)

**Rust** (`web4-trust-core/src/tensor/t3.rs:156-157`):
```rust
// Talent decays slowest (innate ability doesn't fade as fast)
self.talent = decay_value(self.talent, 0.995);
```

**Spec** (`web4-standard/core-spec/t3-v3-tensors.md:110-118`, strengthened by Sprint 44 T1):
> **Talent Stability**: No decay — Talent represents inherent capability and
> does not diminish through inactivity. This is a normative protocol property,
> not a tunable parameter.
>
> Societies **MAY** configure custom decay policies for Training and Temperament
> (e.g., different decay rates or recovery curves), but Talent's no-decay
> property is invariant at the protocol level.

**Test vector** (t3v3-012):
```json
"talent": 0.8,   // unchanged after 12 months
"formulas": { "talent": "unchanged" }
```

**Python SDK** (`web4-standard/implementation/sdk/web4/trust.py:200`):
```python
return T3(
    talent=self.talent,  # stable — no decay
    ...
)
```

**Impact**: Any entity whose T3 has been processed through the Rust `apply_decay` function
will have a lower Talent score than the spec prescribes. This is not a rounding difference —
it's a semantic violation of a normative invariant. Hardbound MUST NOT rely on Rust Talent
values after decay has been applied.

**Fix**: In `t3.rs:apply_decay()`, remove the Talent decay line entirely. Talent should
remain unchanged regardless of `days_inactive`.

---

### 2. HIGH — T3 Composite: Unweighted Average

**Rust** (`web4-trust-core/src/tensor/t3.rs:72-74`):
```rust
pub fn average(&self) -> f64 {
    (self.talent + self.training + self.temperament) / 3.0
}
```

**Test vector** (t3v3-001):
```json
"formula": "talent*0.4 + training*0.3 + temperament*0.3",
"weights": {"talent": 0.4, "training": 0.3, "temperament": 0.3}
```

**Python SDK** (`web4-standard/implementation/sdk/web4/trust.py:162-167`):
```python
return (
    self.talent * T3_WEIGHTS["talent"]       # 0.4
    + self.training * T3_WEIGHTS["training"]   # 0.3
    + self.temperament * T3_WEIGHTS["temperament"]  # 0.3
)
```

**Numeric example** (test vector t3v3-001 input: talent=0.8, training=0.7, temperament=0.9):
- Spec/Python: 0.8×0.4 + 0.7×0.3 + 0.9×0.3 = **0.80**
- Rust: (0.8 + 0.7 + 0.9) / 3 = **0.80** ← happens to match for this input

**Why it still matters**: For asymmetric inputs, the results diverge. Example:
talent=0.9, training=0.3, temperament=0.3:
- Spec/Python: 0.9×0.4 + 0.3×0.3 + 0.3×0.3 = 0.36 + 0.09 + 0.09 = **0.54**
- Rust: (0.9 + 0.3 + 0.3) / 3 = **0.50**

The spec weights Talent more heavily (0.4 vs 0.33), reflecting that inherent capability
is the strongest signal. The Rust `average()` method is called throughout the codebase
for trust level determination (`TrustLevel::from_score(self.average())`), so this
divergence affects every trust-level decision.

**Fix**: Add a `composite()` method using canonical weights, or change `average()` to use them.
The WASM binding at `bindings/wasm.rs:57-59` and Python binding at `bindings/python.rs:61-63`
both delegate to this method.

---

### 3. HIGH — V3 Composite: Unweighted Average

**Rust** (`web4-trust-core/src/tensor/v3.rs:71-73`):
```rust
pub fn average(&self) -> f64 {
    (self.valuation + self.veracity + self.validity) / 3.0
}
```

**Test vector** (t3v3-002):
```json
"formula": "valuation*0.3 + veracity*0.35 + validity*0.35",
"weights": {"valuation": 0.3, "veracity": 0.35, "validity": 0.35}
```

**Numeric example** (test vector t3v3-002 input: valuation=0.3, veracity=0.85, validity=0.8):
- Spec/Python: 0.3×0.3 + 0.85×0.35 + 0.8×0.35 = **0.6675**
- Rust: (0.3 + 0.85 + 0.8) / 3 = **0.65**

The spec weights Veracity and Validity higher (0.35 each) than Valuation (0.3),
reflecting that truthfulness and legitimacy are stronger value signals than raw
economic contribution. The Rust `average()` underweights veracity and validity.

**Fix**: Same as #2 — add `composite()` with canonical weights or update `average()`.

---

### 4. HIGH — T3 Update: Wrong Formula

**Rust** (`web4-trust-core/src/tensor/t3.rs:89-105`):
```rust
let delta = if success {
    magnitude * 0.05 * (1.0 - self.training)  // diminishing returns
} else {
    -magnitude * 0.10 * self.training          // bigger fall from height
};

self.training = (self.training + delta).clamp(0.0, 1.0);
self.temperament = (self.temperament + delta * 0.5).clamp(0.0, 1.0);
self.talent = (self.talent + delta * 0.3).clamp(0.0, 1.0);
```

**Test vector** (t3v3-003):
```json
"delta_formula": "0.02 * (quality - 0.5)",
"dimension_factors": {"talent": 1.0, "training": 0.8, "temperament": 0.6}
```

**Python SDK** (`web4-standard/implementation/sdk/web4/trust.py:177-182`):
```python
base_delta = T3_UPDATE_RATE * (quality - 0.5)  # 0.02 * (quality - 0.5)
return T3(
    talent=_clamp(self.talent + base_delta * T3_UPDATE_FACTORS["talent"]),
    training=_clamp(self.training + base_delta * T3_UPDATE_FACTORS["training"]),
    temperament=_clamp(self.temperament + base_delta * T3_UPDATE_FACTORS["temperament"]),
)
```

**Divergences in the update formula**:

| Aspect | Spec/Python | Rust |
|--------|-------------|------|
| Input | `quality` (0.0-1.0) | `success` (bool) + `magnitude` (0.0-1.0) |
| Base delta | `0.02 * (quality - 0.5)` | success: `magnitude * 0.05 * (1 - training)` |
| | | failure: `-magnitude * 0.10 * training` |
| Dimension ordering | Talent gets largest factor (1.0) | Training gets largest delta (1.0x) |
| Talent factor | 1.0 (most affected) | 0.3 (least affected) |
| Training factor | 0.8 | 1.0 (most affected) |
| Temperament factor | 0.6 | 0.5 |
| Symmetry | Symmetric (quality below 0.5 = negative) | Asymmetric (failure hits 2x harder) |

**Numeric example** (test vector t3v3-003, neutral tensor, quality=0.8):
- Spec/Python: base_delta=0.006 → talent=0.506, training=0.5048, temperament=0.5036
- Rust (magnitude=0.8, success=true): delta=0.8×0.05×0.5=0.02 → training=0.52, temperament=0.51, talent=0.506

The spec's design gives Talent the highest update factor because inherent capability
is the strongest signal from any single action. The Rust implementation inverts this,
making Training the primary affected dimension.

**Fix**: Replace `update_from_outcome` with spec-conformant formula. The function
signature may need to change from `(success, magnitude)` to `(quality)` to match
the spec's continuous quality input.

---

### 5. HIGH — T3 Decay: Wrong Model

**Rust** (`web4-trust-core/src/tensor/t3.rs:137-161`):
```rust
let decay_factor = (1.0 - decay_rate).powf(days_inactive);
let floor = 0.3;

// Training decays most
self.training = decay_value(self.training, 1.0);
// Temperament decays slightly less
self.temperament = decay_value(self.temperament, 0.98);
// Talent decays slowest (SEE DIVERGENCE #1 — THIS SHOULD NOT HAPPEN)
self.talent = decay_value(self.talent, 0.995);
```

**Test vector** (t3v3-012):
```json
"formulas": {
    "training": "0.8 - 0.001*12 = 0.788",
    "temperament": "0.6 + 0.01*12 = 0.72",
    "talent": "unchanged"
}
```

**Python SDK** (`web4-standard/implementation/sdk/web4/trust.py:193-204`):
```python
return T3(
    talent=self.talent,                                          # no decay
    training=_clamp(self.training - TRAINING_DECAY_PER_MONTH * months),  # -0.001/month
    temperament=_clamp(self.temperament + TEMPERAMENT_RECOVERY_PER_MONTH * months),  # +0.01/month
)
```

| Aspect | Spec/Python | Rust |
|--------|-------------|------|
| Talent | No decay (invariant) | Decays (factor 0.995) |
| Training | Linear: -0.001/month | Exponential: `(1-rate)^days` with floor 0.3 |
| Temperament | **Recovers** +0.01/month | **Decays** (factor 0.98) |
| Time unit | Months | Days |
| Floor | 0.0 (implicit via clamp) | 0.3 (hard floor) |
| Model | Linear (training), linear (temperament) | Exponential (all) |

The Temperament divergence is particularly notable: the spec says Temperament **recovers**
over time (good behavior is the default), while the Rust implementation **decays** it.
These are opposite directions.

**Fix**: Rewrite `apply_decay` to:
1. Leave Talent unchanged (normative invariant)
2. Use linear decay for Training (-0.001 per month)
3. Use linear recovery for Temperament (+0.01 per month)
4. Accept months (not days) or convert internally

---

### 6. MEDIUM — No ActionOutcome-Based Evolution

The spec (§2.3) and Python SDK define five categorized action outcomes with explicit
per-dimension deltas:

| Outcome | Talent | Training | Temperament |
|---------|--------|----------|-------------|
| NOVEL_SUCCESS | +0.035 | +0.015 | +0.01 |
| STANDARD_SUCCESS | 0.0 | +0.0075 | +0.005 |
| EXPECTED_FAILURE | -0.01 | 0.0 | 0.0 |
| UNEXPECTED_FAILURE | -0.02 | -0.01 | -0.02 |
| ETHICS_VIOLATION | -0.05 | 0.0 | -0.10 |

Python SDK: `T3.evolve(outcome: ActionOutcome) -> T3` (`trust.py:184-191`)
Test vector t3v3-011 validates ethics_violation specifically.

Rust has no equivalent. The `update_from_outcome(success, magnitude)` function is the
closest, but it uses a binary success/failure model rather than the five-outcome taxonomy.

**Fix**: Add `ActionOutcome` enum and `evolve` method to `T3Tensor`.

---

### 7. MEDIUM — Legacy 6D Bridge: Wrong Formula

**Rust** (`web4-trust-core/src/tensor/t3.rs:205-218`):
```rust
pub fn from_legacy_6d(competence, reliability, consistency, witnesses, lineage, alignment) -> Self {
    Self::new(
        competence,                                    // talent = competence directly
        (reliability + consistency + lineage) / 3.0,   // training = avg(3 dims)
        (witnesses + alignment) / 2.0,                 // temperament = avg(2 dims)
    )
}
```

**Test vector** (t3v3-008):
```json
"formula": "primary*0.6 + sum(secondary)*0.133",
"primary_mapping": {
    "competence": "talent",
    "reliability": "training",
    "consistency": "temperament"
},
"primary_weight": 0.6,
"secondary_weight": 0.1333
```

**Python SDK** (`web4-standard/implementation/sdk/web4/trust.py`, `trust_bridge` function):
```
talent = 0.6*competence + (0.4/3)*(alignment + witnesses + lineage) = 0.62
training = 0.6*reliability + (0.4/3)*(alignment + witnesses + lineage) = 0.56
temperament = 0.6*consistency + (0.4/3)*(alignment + witnesses + lineage) = 0.50
```

**Numeric comparison** (test vector input):
| Dimension | Spec/Python | Rust |
|-----------|-------------|------|
| talent | 0.62 | 0.70 |
| training | 0.56 | 0.47 |
| temperament | 0.50 | 0.60 |

The spec uses a primary/secondary weighting scheme where each 3D dimension gets
0.6 weight from its primary 6D source and 0.4/3 weight from each secondary.
The Rust implementation assigns the primary dimension directly (1.0 weight)
and averages the remaining dimensions.

**Fix**: Implement the primary/secondary weighting formula from the test vector.
The V3 `from_legacy_6d` (`v3.rs:146-159`) has the same structural issue.

---

### 8. LOW — Missing Test Vector Operations

The following test vector operations have no Rust implementation. These are
module-level functions in the Python SDK that may not all need to be in the
Rust core library, but their absence means hardbound cannot rely on
web4-trust-core for these calculations:

| Test Vector | Operation | Python SDK Function |
|-------------|-----------|---------------------|
| t3v3-007 | Diminishing returns | `diminishing_returns()` |
| t3v3-009 | MRH trust decay per hop | `mrh_trust_decay()` |
| t3v3-010 | Operational health / coherence | `operational_health()` |
| t3v3-013 | Role requirement evaluation | `RoleRequirement` + evaluation |
| t3v3-014 | V3 from action components | Implicit in V3 calculation |
| t3v3-015 | Team T3 composition | `compute_team_t3()` |

These are MEDIUM/LOW priority since hardbound can call the Python SDK for these
operations. They become HIGH priority if hardbound needs them in the WASM path.

---

## What IS Aligned

For completeness, these aspects are correctly aligned after the `55b1a3d8` rebuild:

| Aspect | Status |
|--------|--------|
| Dimension names (T3: talent/training/temperament) | Aligned |
| Dimension names (V3: valuation/veracity/validity) | Aligned |
| Value range (0.0 - 1.0 clamping) | Aligned |
| Neutral tensor (all 0.5) | Aligned |
| `TrustLevel` thresholds (0.8/0.6/0.4/0.2) | Aligned |
| Entity ID parsing (`type:name` format) | Aligned |
| Witnessing relationship tracking | Aligned (structure) |
| JSON serialization of tensor fields | Aligned |

---

## Recommendations

### Immediate (before hardbound relies on T3/V3 from WASM)

1. **Fix Talent decay** (CRITICAL, #1) — remove `self.talent = decay_value(...)` line
2. **Fix composites** (HIGH, #2/#3) — use canonical weighted averages
3. **Fix update formula** (HIGH, #4) — adopt spec's `0.02 * (quality - 0.5)` formula
4. **Fix decay model** (HIGH, #5) — linear, monthly, with Temperament recovery

### Soon (before hardbound uses outcome-based trust evolution)

5. **Add ActionOutcome** (MEDIUM, #6) — five-outcome enum with per-dimension deltas
6. **Fix legacy bridge** (MEDIUM, #7) — adopt primary/secondary weighting

### Eventually (if hardbound needs these in WASM path)

7. **Add missing functions** (LOW, #8) — diminishing returns, MRH decay, etc.

### Process Note

The test vectors at `web4-standard/test-vectors/t3v3/tensor-operations.json` are the
authoritative cross-language conformance suite. Any Rust fix should be validated by
adding a test in `web4-trust-core/tests/` that parses and validates against these
vectors, mirroring the Python SDK's CI integration.

---

## Meta

This audit follows the pattern of `docs/audits/spec-vs-explainer-alignment-2026-04-19.md`
(Sprint 43 T1). It classifies divergences; it does not fix them. The Rust fixes require
a machine with the Rust toolchain installed.
