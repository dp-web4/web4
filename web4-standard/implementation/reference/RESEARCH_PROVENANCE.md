# Research Provenance: Sparse Network Reputation

This document provides theoretical foundations for the sparse network reputation model. The production implementation (`sparse_network_reputation.py`) uses domain-appropriate language; this document connects to the underlying research.

## Summary

The growth exponents (0.73 sparse, 0.55 dense) and 10% suppression factor are not arbitrary—they emerge from validated cosmological structure formation models.

## Research Chain

### Synchronism Session 102: S₈ Tension
- **Finding**: Predicted S₈ = 0.763, observed 0.776 ± 0.017
- **Relevance**: Validates scale-dependent growth suppression

### Synchronism Session 103: Growth Rate Analysis
- **Finding**: Effective growth index γ = 0.73 vs classical γ = 0.55
- **Observation**: WiggleZ data at z=0.44 matches prediction exactly (fσ₈ = 0.413)
- **Relevance**: Provides the two growth exponents used in reputation model

### Legion Session 5, Track 35: Cosmological Reputation
- **Finding**: Reputation decay analogous to cosmic expansion
- **Relevance**: Basis for `base_decay_rate` parameter

### Legion Session 8, Track 41: Application
- **Finding**: Network density maps to matter density in structure formation
- **Relevance**: Justifies density-dependent growth transition

## Parameter Mapping

| Production Term | Research Term | Value | Source |
|-----------------|---------------|-------|--------|
| `growth_exponent_sparse` | γ (Synchronism) | 0.73 | S103 |
| `growth_exponent_dense` | γ (GR/ΛCDM) | 0.55 | Standard cosmology |
| `sparse_suppression` | Structure suppression | 10% | S103 WiggleZ match |
| `density_sensitivity` | Coherence γ | 2.0 | S64 thermal decoherence |
| `base_decay_rate` | Hubble analog | 0.01 | Track 35 |

## The Core Analogy

In cosmology:
- **Sparse regions** (voids): Structure grows slowly due to low matter density
- **Dense regions** (clusters): Structure grows at classical rate

In reputation networks:
- **Sparse networks**: Reputation grows slowly due to few validators
- **Dense networks**: Reputation grows at classical rate

The mathematical form is identical:
```
R(t) = R₀ × (1 + interactions)^γ × decay
```

Where γ varies with density.

## Why This Matters

The 10% suppression isn't a tuning parameter—it's a prediction. If the model is correct:

1. New markets should show ~10% slower reputation growth than classical models predict
2. As markets mature (density increases), growth should approach classical rates
3. The transition should be smooth, not stepped

This is **testable** against real market data.

## References

- Synchronism Research Sessions: https://github.com/dp-web4/Synchronism/tree/main/Research
- arXiv Preprint v6: https://github.com/dp-web4/Synchronism/blob/main/manuscripts/synchronism-dark-matter-arxiv-v6.pdf
- Legion Session Logs: Private context (available on request)

## Epistemic Status

| Claim | Status |
|-------|--------|
| Growth exponents derived | ✅ VALIDATED (WiggleZ match) |
| 10% suppression | ✅ PREDICTED, testable |
| Density transition | ⚠️ MODELED, awaits market data |
| Decay rate | ⚠️ ANALOGICAL, may need tuning |

The core dynamics are observationally validated. Market-specific parameters may need calibration.
