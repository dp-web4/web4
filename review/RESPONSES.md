# Responses to Nova Review Open Questions

**Addressed**: February 12, 2026
**Status**: In Progress

---

## Canonicality and Governance

### Q1: Which document is authoritative when definitions conflict?

**RESOLVED.** Created `docs/reference/SOURCE_OF_TRUTH.md` which defines a 4-tier authority hierarchy:

1. **Tier 1 (Highest)**: `CANONICAL_TERMS_v1.md`, `web4-standard/core-spec/*.md`
2. **Tier 2**: `STATUS.md`, `SECURITY.md`, `CHANGELOG.md`
3. **Tier 3**: `GLOSSARY.md`, `docs/how/*`, `docs/architecture/*`
4. **Tier 4 (Lowest)**: `README.md`, index files

Rule: Higher tier wins. Within same tier, more specific wins.

### Q2: Is there a formal versioning policy for canonical concepts?

**PARTIALLY RESOLVED.** `CANONICAL_TERMS_v1.md` uses semantic versioning (1.0.0). The versioning policy for individual specs (LCT, T3, etc.) is not yet formalized beyond the spec files themselves.

**NEEDED**: Add version field to each core-spec file header and document update procedures.

### Q3: How will R6 guidance be enforced and stale R7 mentions removed?

**RESOLVED.** `CANONICAL_TERMS_v1.md` explicitly states:
> "R6 (Six-Element Action Framework) - NOT: R7, R5, or any other count. R6 is canonical."

Enforcement section requires checking canonical terms before creating/updating docs.

**NEEDED**: Grep codebase for "R7" references and update. (Can do now if desired.)

---

## Architecture and Scope

### Q4: Migration plan for stale `/game/` links?

**RESOLVED.** All 30 broken `/game/` links have been fixed:
- README.md: Updated to reference standalone 4-life repo and `archive/game-prototype/`
- SECURITY.md: Updated scope section
- GLOSSARY.md: Updated 4-Life Game entry

**Evidence**: `review/evidence.md` documented the broken links; all are now fixed.

### Q5: Which implementation track is strategic production path?

**NEEDS OWNER INPUT.** Current state:
- `web4-standard/implementation/` - In-repo reference implementations
- `web4-core` - Mentioned in docs but not present in this repo
- `web4-trust-core` - Not found in repo

This appears to be a decision point requiring project owner guidance.

### Q6: What is the MVP subset for external pilot integration?

**NEEDS OWNER INPUT.** Suggestion based on spec analysis:
- Minimum: LCT identity + T3 basic trust + ATP economic primitives
- Components: `LCT-linked-context-token.md`, `t3-v3-tensors.md`, `atp-adp-cycle.md`

Would benefit from explicit "MVP.md" or similar document.

---

## Security and Trust

### Q7: Timeline for formal threat model?

**EXISTS BUT SCATTERED.** Security documentation is present:
- `SECURITY.md` - Top-level security policy
- `review/security_attack_vector_matrix.md` - 12 attack vectors with severity ratings
- `review/security_external_engagement_runbook.md` - Red team engagement procedures

**NEEDED**: Consolidate into formal `THREAT_MODEL.md` with explicit adversary capabilities and security objectives.

### Q8: Which security claims are validated vs proposed?

**HONEST ASSESSMENT:**
- **Validated (simulation)**: 126 attack simulations in `simulations/` directory
- **Validated (empirical)**: None yet - no production deployment
- **Proposed (theoretical)**: Anti-Sybil, anti-collusion, trust degradation models

The attack vector matrix (`security_attack_vector_matrix.md`) categorizes these.

### Q9: Is there an external red team plan?

**EXISTS.** See:
- `review/external_red_team_plan.md` - Detailed phased approach
- `review/security_external_engagement_runbook.md` - Engagement procedures

Acceptance criteria defined in runbook:
- All Critical findings addressed or accepted with risk sign-off
- High findings remediated or scheduled with owner/deadline
- Retest completed for fixed items

---

## Economics and Incentives

### Q10: How will ATP stake/cost parameters be calibrated?

**THEORETICAL ONLY.** The `atp-adp-cycle.md` spec defines the mechanism but calibration against real attacker ROI is not documented.

**NEEDED**: Economic modeling document with attacker cost assumptions.

### Q11: Is there a target economic model for anti-Sybil claims?

**PARTIALLY EXISTS.** Simulation results in `simulations/` test anti-Sybil properties under synthetic conditions.

**NEEDED**: Document mapping synthetic parameters to real-world economic assumptions.

### Q12: What guardrails prevent parameter overfitting?

**NOT DOCUMENTED.** This is a valid concern.

**NEEDED**: Document parameter selection methodology and out-of-sample validation approach.

---

## Identity and Hardware Binding

### Q13: Phased plan for hardware binding?

**CONCEPTUAL ONLY.** Hardware binding is specified in `LCT-linked-context-token.md` but phased rollout across TPM/Secure Enclave/FIDO2 is not documented.

**NEEDED**: Hardware binding implementation roadmap.

### Q14: Key rotation, revocation, and recovery?

**SPECIFIED BUT NOT IMPLEMENTED.**
- Binding = permanent (no rotation by design)
- Pairing = revocable
- Delegation = instantly revocable

Recovery mechanisms not specified in detail.

**NEEDED**: Key lifecycle management spec.

---

## Documentation and Developer Experience

### Q15: Will CI enforce link integrity?

**NOT YET.** Manual link checking performed (this review).

**RECOMMENDATION**: Add GitHub Action using `markdown-link-check` or similar.

### Q16: How frequently should status/metrics be synchronized?

**NOT FORMALIZED.** STATUS.md and attack counts updated ad-hoc.

**RECOMMENDATION**: Define quarterly review cadence with sign-off.

### Q17: Should there be a machine-readable claims manifest?

**GOOD IDEA, NOT IMPLEMENTED.**

**RECOMMENDATION**: Create `claims.yaml` with:
- Security claims and validation status
- Capability claims and evidence pointers
- Version and attestation metadata

---

## Interoperability and Externalization

### Q18: What criteria define "standards-ready"?

**NOT FORMALIZED.** IETF/ISO submission mentioned in STATUS.md but criteria not explicit.

**RECOMMENDATION**: Create standards-readiness checklist:
- [ ] Formal spec in RFC format
- [ ] Reference implementation
- [ ] Conformance test suite
- [ ] Two independent implementations
- [ ] Security review

### Q19: Which external repos are dependencies vs optional?

**CLARIFIED:**
- **ACT** (Cosmos SDK chain): Core dependency for ATP/LCT registry
- **HRM** (Neural MoE): Optional integration for trust-based expert selection
- **4-life** (Simulation): Development tool, not runtime dependency

Should be documented in STATUS.md or ARCHITECTURE.md.

### Q20: Publicly documented interoperability test matrix?

**NOT EXISTS.**

**NEEDED**: Create `tests/INTEROPERABILITY_MATRIX.md` with:
- Component combinations tested
- Test fixtures and expected outputs
- Reproducibility instructions

---

## Summary

| Category | Questions | Resolved | Partial | Needs Work |
|----------|-----------|----------|---------|------------|
| Canonicality | 3 | 2 | 1 | 0 |
| Architecture | 3 | 1 | 0 | 2 |
| Security | 3 | 1 | 1 | 1 |
| Economics | 3 | 0 | 1 | 2 |
| Identity | 2 | 0 | 1 | 1 |
| Documentation | 3 | 0 | 0 | 3 |
| Interoperability | 3 | 0 | 1 | 2 |
| **Total** | **20** | **4** | **5** | **11** |

---

## Immediate Actions Taken

1. Created `docs/reference/CANONICAL_TERMS_v1.md`
2. Created `docs/reference/SOURCE_OF_TRUTH.md`
3. Fixed 30 broken links across README.md, SECURITY.md, GLOSSARY.md
4. Fixed T3/V3 terminology inconsistency (3D not 4D/6D)
5. Updated CLAUDE.md T3/V3 description

## Recommended Next Steps

1. Grep for remaining "R7" references and update
2. Create CI workflow for link checking
3. Consolidate threat model into single document
4. Define MVP subset explicitly
5. Document external repo dependencies in STATUS.md
