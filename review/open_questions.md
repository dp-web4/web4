# Web4 Review Open Questions

## Canonicality and Governance
1. Which document is authoritative when definitions conflict (`README.md`, `STATUS.md`, `repo-index.yaml`, or `web4-standard/README.md`)?
2. Is there a formal versioning policy for canonical concepts (LCT, T3/V3, MRH, R6)?
3. How will canonical R6 guidance be enforced and stale R7 mentions removed from public docs?

## Architecture and Scope
4. What migration plan and compatibility policy should be used to clean stale `/game/` links now that `/simulations/` is permanent in this repo?
5. Which implementation track is considered the strategic production path: `web4-standard/implementation/`, `web4-core`, or `web4-trust-core`?
6. What minimum subset of Web4 is considered an MVP for external pilot integration?

## Security and Trust
7. What is the timeline for publishing a formal threat model with explicit adversary capabilities and security objectives?
8. Which security claims are empirically validated vs theoretically proposed?
9. Is there an independent adversarial testing plan (external red team), and what are acceptance criteria?

## Economics and Incentives
10. How will ATP stake/cost parameters be calibrated against realistic attacker ROI assumptions?
11. Is there a target economic model (simulation-to-market mapping) for validating anti-Sybil and anti-collusion claims?
12. What guardrails prevent parameter overfitting to synthetic simulations?

## Identity and Hardware Binding
13. What is the phased plan for hardware binding across TPM, Secure Enclave, and FIDO2 in environments lacking uniform hardware support?
14. How are key rotation, revocation, and recovery expected to work in the first production-capable implementation?

## Documentation and Developer Experience
15. Will CI enforce link integrity and stale-reference detection for top-level docs?
16. How frequently should top-level status/metrics (e.g., attack counts) be synchronized and signed off?
17. Should there be a single machine-readable “claims manifest” for automated consistency checks?

## Interoperability and Externalization
18. What criteria define “standards-ready” for IETF/ISO submission claims?
19. Which external repos (ACT, HRM) are dependencies vs optional integrations at this stage?
20. Is there a publicly documented interoperability test matrix with reproducible fixtures?

