# V3 Specification: Operational Validity Framework
**Version:** 0.1  
**Date:** 2026-02-25  
**Status:** Draft  

---

# 1. Purpose

V3 defines **Validity** as a first-class, operational property of systems.

Where:
- **Valuation** is subjective.
- **Veracity** is observational.
- **Validity (V3)** is structured, contestable, and computationally bounded verification of meaningful claims.

V3 is concerned with making validity:

1. Computationally feasible  
2. Socially legible  
3. Semantically meaningful  

---

# 2. Core Definition

> Validity = The fraction of meaningful claims that survive contest under bounded verification cost.

### Terms

- **Meaningful Claim**: A claim tied to a state transition, action, or measurable outcome.
- **Contest**: Independent replay and probe validation.
- **Bounded Cost**: Verification must operate on small artifact bundles and cheap probe suites.

---

# 3. Validity Stack (Normative Layers)

## Layer 0 — Identity
Every entity must provide:
- Stable identifier
- Versioned manifest
- Lineage references

Required artifact: `manifest.json`

## Layer 1 — Events
Append-only log of:
- Inputs
- Outputs
- Actions
- Failures

Required artifact: `events.jsonl`

## Layer 2 — Claims
Explicit separation of:
- Observations
- Interpretations
- Decisions

Required artifact: `claims.jsonl`

## Layer 3 — Invariants
Explicit constraints that must always hold.

Examples:
- Budget never negative
- Schema validity maintained
- Promotion requires probe pass

Required artifact:
- `invariants.md`
- `invariant_checks.py`

## Layer 4 — Probes
Small, curated behavioral tests representing system promises.

Required artifact:
- `probe_suite/`
- `probe_results.json`

## Layer 5 — Promotion Gates
State transitions require:
- Passing probes
- Recorded decision

Required artifact:
- `promotion_policy.json`
- `promotion_decision.json`

## Layer 6 — Contestability
Every claim must provide:
- Evidence pointers
- Replay instructions
- Minimal reproducibility bundle

---

# 4. Operational Rules

1. No state transition without artifact bundle.
2. No promotion without probe validation.
3. No trust elevation without replayable evidence.
4. All verification units must be small and self-contained.

---

# 5. Anti-Patterns (Explicitly Rejected)

- Narrative-only validation
- Repo-size trust assumptions
- Implicit policy behavior
- Silent regressions
- Non-reproducible claims

---

# 6. Minimal Compliance Criteria

A system is V3-compliant if:

1. It emits structured manifests.
2. It maintains append-only event logs.
3. It defines explicit invariants.
4. It runs bounded probe suites.
5. It gates promotions via probe results.
6. It supports contestable replay.

---

# 7. Design Philosophy

V3 does not attempt perfect truth.
It enforces:

- Continuous provability
- Cheap contest
- Bounded verification cost
- Meaningful semantic guarantees

Validity becomes a system property, not a documentation claim.
