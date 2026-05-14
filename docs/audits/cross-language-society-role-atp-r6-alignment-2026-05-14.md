# Cross-Language Alignment Audit: Society, Role, ATP, R6/R7

**Date**: 2026-05-14
**Scope**: 4 new Rust SDK modules (`web4-core/src/{society,role,atp,r6}.rs`) vs Python SDK counterparts (`web4-standard/implementation/sdk/web4/{society,r6,atp}.py`) vs canonical specs
**Triggered by**: Operator commits `82438958` (Society+Role) and `8857ab09` (ATP+R6/R7) -- 4 new Rust modules added to web4-core
**Pattern**: Same methodology as Sprint 47 T1 (cross-language T3/V3 alignment audit)
**Author**: Autonomous session (Legion web4 track)

---

## Executive Summary

The operator added 4 new Rust modules to `web4-core` implementing Society, Role, ATP, and R6/R7 concepts. These were built against the NEW specs (`society-roles.md`, `inter-society-protocol.md`) committed the same day. The Python SDK's corresponding modules were built against OLDER specs and lack several concepts from the new specifications.

**Key finding**: The Python SDK has **no concept of Society Roles** -- the entire 7-role taxonomy from `society-roles.md` (Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen) is absent. This is the largest cross-language gap.

| Severity | Count | Summary |
|----------|-------|---------|
| **CRITICAL** | 1 | Python SDK missing SocietyRole/RoleAssignment entirely |
| **HIGH** | 3 | Genesis protocol mismatch, MetabolicState divergence, no role-LCT binding |
| **MEDIUM** | 3 | Constraint structure, ActionStatus mismatch, composite architecture |
| **LOW** | 4 | Naming differences, missing utility functions, JSON-LD asymmetry |

---

## Methodology

For each module pair:
1. Read the canonical spec (normative reference)
2. Read the Rust implementation
3. Read the Python implementation
4. Compare (a) Python vs spec, (b) Rust vs spec, (c) Python vs Rust
5. Classify divergences by severity and category

**Severity levels** (same as Sprint 47 audit):
- **CRITICAL**: Fundamental concept missing; implementations cannot interoperate
- **HIGH**: Significant semantic mismatch; same operation produces different results or meaning
- **MEDIUM**: Structural differences that complicate but don't block interop
- **LOW**: Naming, API style, or utility-level differences

---

## Module 1: Society + Role

### Reference specs
- `web4-standard/core-spec/society-roles.md` (v0.1.0, 2026-05-13)
- `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2, 2026-05-13)
- `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (existing)

### Rust implementation
- `web4-core/src/society.rs` (408 lines, 4 tests)
- `web4-core/src/role.rs` (272 lines, 3 tests)

### Python implementation
- `web4-standard/implementation/sdk/web4/society.py` (826 lines)
- `web4-standard/implementation/sdk/web4/federation.py` (dependency)
- `web4-standard/implementation/sdk/web4/metabolic.py` (dependency)

### Finding #1: Python SDK missing SocietyRole entirely -- CRITICAL

**Spec requirement** (`society-roles.md` section 2): Every Web4-compliant society MUST have 7 base-mandatory roles: Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen.

**Rust**: `SocietyRole` enum with 10 variants (7 base-mandatory + Witness + Auditor + Custom). `is_base_mandatory()`, `base_mandatory()`, `description()` methods. `RoleAssignment` struct with role-LCT binding, T3/V3 per role, multi-holder support, rotation.

**Python**: No `SocietyRole` type exists anywhere in the SDK. No role enum, no role assignment, no role-LCT pairing. The `society.py` module manages citizens but has no concept of differentiated roles within a society.

**Impact**: The Python SDK cannot represent the fundamental governance structure defined in the spec. Any cross-language interaction involving role-based authorization, role-contextualized reputation (R7), or minimum viable society validation would fail.

**Fix scope**: Add `SocietyRole` enum + `RoleAssignment` dataclass to Python SDK. Integrate with `society.py`'s `SocietyState`. This is a significant addition (~150-200 lines of new types + integration).

### Finding #2: Genesis protocol mismatch -- HIGH

**Spec requirement** (`inter-society-protocol.md` section 2.1): Self-bootstrapped genesis -- a single entity MAY found a society. "Solo founder wears many hats."

**Rust**: `Society::bootstrap(name, charter_hash, founder_lct_id)` implements solo-founder genesis. Creates all 7 base-mandatory role assignments with the founder filling every role. Returns `(Society, Vec<(SocietyRole, Uuid)>)` -- the society plus the role-LCT pairs.

**Python**: `create_society()` requires `len(founders) >= 2` -- raises `ValueError("Society requires at least 2 founders")`. This contradicts the spec's solo-founder genesis protocol.

**Impact**: The Python SDK cannot create a solo-founder society, which the spec explicitly permits and the Rust SDK implements. The 2-founder minimum was carried forward from an older version of `SOCIETY_SPECIFICATION.md` that predates the `inter-society-protocol.md` genesis protocols.

**Fix scope**: Add `bootstrap()` class method or standalone function supporting solo-founder genesis. Optionally retain `create_society()` for the multi-founder case.

### Finding #3: MetabolicState divergence -- HIGH

**Spec reference**: `SOCIETY_SPECIFICATION.md` metabolic states, referenced by `inter-society-protocol.md` section 5 (secession/dissolution).

**Rust**: `MetabolicState` enum with 5 variants: Genesis, Bootstrap, Operational, Dormant, Sunset.

**Python**: `MetabolicState` (in `metabolic.py`) has: ACTIVE, GROWING, STABLE, DECLINING, DORMANT, CRITICAL, DISSOLVING (7 variants).

**Mismatch detail**:

| Concept | Rust | Python |
|---------|------|--------|
| Initial creation | Genesis | (no equivalent -- jumps to ACTIVE) |
| Setting up roles/ATP | Bootstrap | (no equivalent) |
| Fully running | Operational | ACTIVE / GROWING / STABLE |
| Low activity | Dormant | DORMANT |
| Winding down | Sunset | DECLINING / DISSOLVING |
| Emergency | (not modeled) | CRITICAL |

**Impact**: The two SDKs have fundamentally different lifecycle models. The Rust model follows the new spec (Genesis to Bootstrap to Operational lifecycle from `inter-society-protocol.md`). The Python model follows an older, more granular biologically-inspired model. Interop on lifecycle state would require a mapping layer.

**Fix scope**: Decide whether to align Python to Rust's spec-matching 5-state model or define a canonical mapping. The Python `SocietyPhase` enum (Genesis/Bootstrap/Operational) partially covers the Rust states but is separate from `MetabolicState`.

### Finding #4: No role-LCT binding in Python -- HIGH

**Spec requirement** (`society-roles.md` section 5): "Role authority binds to the role LCT, not to the filling entity's LCT. When the filling entity changes, the role's history and authority continue uninterrupted."

**Rust**: `RoleAssignment` has `role_lct_id: Uuid` (the role's own LCT), `filling_entity_lct_id: Uuid` (who currently fills it), `assigned_by`, `assigned_at`, `role_trust: T3`, `role_value: V3`, `multi_holder: bool`, `additional_holders: Vec<Uuid>`. Supports `rotate()` (change filler, keep role-LCT) and `add_holder()` (committee pattern).

**Python**: No equivalent concept. Citizens are tracked as sets of LCT IDs in `federation.Society.citizens`. There is no role-LCT, no role rotation, no multi-holder committee pattern.

**Impact**: Role-based accountability chains, role rotation, and the "authority binds to role, not person" principle cannot be expressed in the Python SDK.

**Fix scope**: Part of the broader SocietyRole addition (Finding #1). The `RoleAssignment` dataclass with role-LCT binding is the core type to add.

### Finding #5: Composite architecture difference -- MEDIUM

**Python**: Uses a layered composite pattern -- `SocietyState` wraps `federation.Society` + `SocietyPhase` + `MetabolicState` + `Treasury` + `SocietyLedger` + citizen trust profiles. The `federation.Society` holds citizens, laws, quorum policy, parent/children. Operations are free functions (`create_society()`, `admit_citizen()`, etc.) that mutate `SocietyState`.

**Rust**: Uses a self-contained `Society` struct with roles, citizens, federation parent/children, charter, and metabolic state all in one type. Operations are methods on `Society` (`bootstrap()`, `assign_role()`, `go_operational()`, etc.).

**Impact**: Not a semantic mismatch per se -- both represent the same concepts -- but the Python SDK's layered approach means that adding roles requires threading through multiple types (SocietyState, federation.Society, and a new role component). The Rust approach is simpler to extend.

### Finding #6: Minimum viable society validation -- MEDIUM

**Spec requirement** (`inter-society-protocol.md` section 6.2): A society is semantically viable when it has (1) internal differentiation, (2) witnessing capacity, (3) externally-grounded ATP reification.

**Rust**: `Society::validate_minimum_viable()` checks all three requirements. Returns `Result<(), Vec<String>>` with specific error messages.

**Python**: No equivalent validation. A society can be created and operated without any structural validation of viability.

**Fix scope**: Add validation function once SocietyRole is available (depends on Finding #1).

---

## Module 2: ATP

### Reference spec
- `web4-standard/core-spec/atp-adp-cycle.md`

### Rust implementation
- `web4-core/src/atp.rs` (289 lines, 7 tests)

### Python implementation
- `web4-standard/implementation/sdk/web4/atp.py` (382 lines)

### Finding #7: Core semantics are aligned -- INFO (positive)

Both implementations share identical semantics for:

| Operation | Python | Rust | Aligned? |
|-----------|--------|------|----------|
| Account structure | `ATPAccount(available, locked, adp, initial_balance)` | `ATPAccount { available, locked, adp, initial_balance }` | YES |
| Total calculation | `available + locked` | `available + locked` | YES |
| Energy ratio | `total / (total + adp)`, 0 maps to 0.5 | `total / (total + adp)`, 0 maps to 0.5 | YES |
| Lock | `lock(amount) -> bool` | `lock(amount) -> Result<()>` | YES (idiomatic) |
| Commit | `commit(amount) -> float` | `commit(amount) -> Result<f64>` | YES |
| Rollback | `rollback(amount) -> float` | `rollback(amount) -> Result<f64>` | YES |
| Recharge | `recharge(rate, max_multiplier) -> float` | `recharge(rate, max_multiplier) -> f64` | YES |
| Transfer | `transfer(sender, receiver, amount, fee_rate, max_balance)` | `transfer(sender, receiver, amount, fee_rate, max_balance)` | YES |
| Sliding scale | `sliding_scale(quality, base, zero_thresh, full_thresh)` | `sliding_scale(quality, base, zero_thresh, full_thresh)` | YES |

This is the **best-aligned module pair** in the audit. Both implementations follow the `atp-adp-cycle.md` spec faithfully.

### Finding #8: Python has additional analytical functions -- LOW

**Python only**: `check_conservation()`, `sybil_cost()`, `fee_sensitivity()`, `energy_ratio()` (standalone function).

**Rust**: None of these utility functions.

**Impact**: These are analysis/test-support utilities, not core primitives. The Rust SDK covers the core protocol operations; the Python SDK additionally provides economic analysis tools. Not a divergence -- a maturity difference.

### Finding #9: JSON-LD serialization asymmetry -- LOW

**Python**: `ATPAccount` and `TransferResult` have `to_jsonld()`, `from_jsonld()`, `to_jsonld_string()`, `from_jsonld_string()`.

**Rust**: Has `serde::Serialize`/`Deserialize` derives (JSON via serde_json) but no JSON-LD-specific serialization.

**Impact**: Cross-language document exchange would use JSON (both support it) but the JSON-LD `@context` and `@type` fields are Python-only. The Rust SDK will need JSON-LD support when interop matters.

---

## Module 3: R6/R7

### Reference specs
- `web4-standard/core-spec/r6-framework.md`
- `web4-standard/core-spec/r7-framework.md`

### Rust implementation
- `web4-core/src/r6.rs` (561 lines, 8 tests)

### Python implementation
- `web4-standard/implementation/sdk/web4/r6.py` (~700 lines)

### Finding #10: Constraint structure mismatch -- MEDIUM

**Python**: `Constraint(constraint_type: str, value: Any)` -- generic value, no hard/soft distinction.

**Rust**: `Constraint { constraint_type: String, threshold: f64, hard: bool }` -- typed threshold, explicit hard/soft flag.

**Impact**: The Rust version is more specific and better aligned with the spec's concept of hard constraints (that block execution) vs soft constraints (that warn). The Python version loses this distinction. A hard constraint in Rust would need to be encoded differently in Python (e.g., as a convention in `constraint_type` naming).

**Fix scope**: Add `hard: bool = True` and rename `value` to `threshold` in the Python `Constraint` dataclass. Breaking change for existing test vectors.

### Finding #11: ActionStatus enum mismatch -- MEDIUM

**Python**: 7 variants: PENDING, VALIDATED, IN_PROGRESS, SUCCESS, FAILURE, ERROR, CANCELLED.

**Rust**: 6 variants: Pending, Validated, InProgress, Success, Failure, Error. **Missing: CANCELLED**.

**Impact**: An action cancelled in Python cannot be represented in Rust. Minor -- CANCELLED is a convenience state not referenced in the spec's core lifecycle. But cross-language serialization of cancelled actions would fail.

### Finding #12: Python has ActionChain; Rust does not -- LOW

**Python**: `ActionChain` class for chaining R7 actions (linked list via `prev_action_hash`), with `build_action()` convenience function.

**Rust**: No `ActionChain`. `R7Action` has `prev_action_hash` field for manual linking.

**Impact**: Python SDK is more feature-complete for action sequencing. Rust provides the primitive (`prev_action_hash`) but not the convenience wrapper.

### Finding #13: Error hierarchy difference -- LOW

**Python**: 7 dedicated error types inheriting from `R7Error`: `RuleViolation`, `RoleUnauthorized`, `RequestMalformed`, `ReferenceInvalid`, `ResourceInsufficient`, `ResultInvalid`, `ReputationComputationError`.

**Rust**: Uses generic `Web4Error` with `InvalidInput`, `InvalidState`, `Unauthorized` variants.

**Impact**: Language-idiomatic. Python's finer-grained errors map to R7's 7 components; Rust uses broader error categories. Not a semantic mismatch.

### Finding #14: Naming differences -- LOW

| Concept | Python | Rust |
|---------|--------|------|
| Role in action context | `Role` | `ActionRole` |
| Action result | `Result` | `ActionResult` |
| Constraint threshold | `value: Any` | `threshold: f64` |

**Impact**: Cosmetic. Cross-language documentation should use the spec terms (Rules, Role, Request, Reference, Resource, Result, Reputation) rather than implementation-specific names.

---

## Prioritized Fix Queue

Ordered by impact and dependency chain:

| Priority | Finding | Severity | Module | Action | Dependency |
|----------|---------|----------|--------|--------|------------|
| **P1** | #1 | CRITICAL | Society | Add `SocietyRole` enum + `RoleAssignment` to Python SDK | None |
| **P2** | #4 | HIGH | Society | Add role-LCT binding to `RoleAssignment` (with T3/V3 per role, rotation, multi-holder) | P1 |
| **P3** | #2 | HIGH | Society | Add solo-founder bootstrap function to Python SDK | P1, P2 |
| **P4** | #3 | HIGH | Society | Reconcile MetabolicState models (5-state vs 7-state) | Operator decision |
| **P5** | #6 | MEDIUM | Society | Add `validate_minimum_viable()` to Python SDK | P1, P2 |
| **P6** | #10 | MEDIUM | R6 | Add `hard` flag + type `threshold` to Python `Constraint` | None |
| **P7** | #5 | MEDIUM | Society | Consider SocietyState integration approach for roles | P1 |

### Items NOT requiring immediate action

| Finding | Severity | Reason |
|---------|----------|--------|
| #7 | INFO | ATP core semantics are aligned -- no fix needed |
| #8 | LOW | Python's extra analytical functions are additive, not divergent |
| #9 | LOW | JSON-LD support in Rust is a later concern (no cross-language doc exchange yet) |
| #11 | MEDIUM | CANCELLED status is a convenience; can wait for next R6/R7 spec revision |
| #12 | LOW | ActionChain is a convenience wrapper; Rust has the primitives |
| #13 | LOW | Error hierarchy is language-idiomatic |
| #14 | LOW | Naming differences are cosmetic |

---

## Operator Decision Required

### Decision #1: MetabolicState model (Finding #3)

The Python SDK has 7 metabolic states (ACTIVE, GROWING, STABLE, DECLINING, DORMANT, CRITICAL, DISSOLVING). The Rust SDK has 5 (Genesis, Bootstrap, Operational, Dormant, Sunset). The spec references both patterns. Options:

- **A**: Align Python to Rust's 5-state model (matches new specs, breaking change)
- **B**: Keep both models; define canonical mapping (complexity, potential confusion)
- **C**: Python's `SocietyPhase` (Genesis/Bootstrap/Operational) already covers the Rust lifecycle; treat `MetabolicState` as an orthogonal health metric

### Decision #2: Role integration architecture (Finding #5, #7)

The Python SDK uses a layered composite (`SocietyState` wrapping `federation.Society`). Adding roles requires choosing:

- **A**: Add roles to `federation.Society` (deep change, affects all society operations)
- **B**: Add roles as a new field on `SocietyState` (shallow change, roles are a parallel structure)
- **C**: Create a new `GovernedSociety` type that composes `SocietyState` + roles (cleanest but adds another layer)

---

## Cross-Reference to Sprint 47 Audit

The Sprint 47 T1 audit (`docs/audits/cross-language-t3v3-alignment-2026-05-13.md`) found 8 divergences in T3/V3 between Rust and Python. This audit finds 14 items across Society/Role/ATP/R6 -- but the pattern is different:

| Sprint 47 (T3/V3) | Sprint 49 (Society/Role/ATP/R6) |
|---|---|
| Both SDKs had the same concepts implemented differently | Python SDK is MISSING entire concepts |
| Fix = correct Rust formulas | Fix = add new types to Python SDK |
| 1 CRITICAL (wrong behavior) | 1 CRITICAL (missing concept) |
| Fixes require Rust toolchain | Fixes require Python SDK changes (this repo) |

The Society/Role gap (Findings #1-#6) is **autonomous-actionable from this repo** -- unlike the Sprint 47 T3/V3 fixes which required the `web4-trust-core` Rust toolchain. P1-P3, P5-P7 can be executed by autonomous sessions working in `web4-standard/implementation/sdk/`.

P4 (MetabolicState reconciliation) requires operator design input.

---

## Files Examined

### Rust SDK (read-only, no toolchain on Legion)
- `web4-core/src/lib.rs` -- module structure, re-exports
- `web4-core/src/society.rs` -- Society struct, bootstrap, lifecycle, federation
- `web4-core/src/role.rs` -- SocietyRole enum, RoleAssignment
- `web4-core/src/atp.rs` -- ATPAccount, transfer, sliding_scale
- `web4-core/src/r6.rs` -- R6/R7 types, validation, reputation
- `web4-core/Cargo.toml` -- dependencies

### Python SDK
- `web4-standard/implementation/sdk/web4/society.py` -- SocietyState, create_society, citizen lifecycle
- `web4-standard/implementation/sdk/web4/atp.py` -- ATPAccount, transfer, analytical functions
- `web4-standard/implementation/sdk/web4/r6.py` -- R7Action, R6/R7 types, ActionChain

### Canonical Specs
- `web4-standard/core-spec/society-roles.md` -- 7 base-mandatory roles, 3-tier taxonomy
- `web4-standard/core-spec/inter-society-protocol.md` -- genesis, first-contact, federation, secession
- `web4-standard/core-spec/atp-adp-cycle.md` -- ATP form, transfer, conservation
