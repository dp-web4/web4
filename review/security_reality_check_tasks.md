# Security Reality Check v1 - Task Checklist

## Phase 0: Alignment
- [ ] Confirm invariant IDs and definitions with maintainers.
- [ ] Confirm P0 scenario ordering and ownership.
- [ ] Confirm output schema fields required for security reviews.

## Phase 1: Framework
- [x] Add `simulations/security_reality_check/invariants.yaml`.
- [x] Add `simulations/security_reality_check/runner.py`.
- [x] Add report writer (JSON + markdown summary).

## Phase 2: P0 Scenarios
- [x] Implement RT-01 replay lane (baseline stub).
- [x] Implement RT-02 replay lane (baseline stub).
- [x] Implement RT-04 replay lane (baseline stub).
- [x] Implement RT-05 replay lane (baseline stub).

## Phase 3: Validation + Reporting
- [ ] Run baseline pass and capture outputs.
- [ ] Confirm invariant checks fire correctly on seeded failures.
- [ ] Produce first scorecard and unresolved-risk list.

## Phase 4: Continuous Use
- [ ] Add optional CI/scheduled run target.
- [ ] Add contributor docs for adding new scenario lanes.
- [ ] Define retest policy for mitigated findings.
