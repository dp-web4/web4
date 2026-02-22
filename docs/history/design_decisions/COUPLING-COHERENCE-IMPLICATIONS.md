# Design Decision: Coupling-Coherence Experiment Implications for Web4

**Date**: 2026-02-22
**Source**: Synchronism coupling-coherence experiment (900 simulation runs)
**Full analysis**: `github.com/dp-web4/HRM/forum/insights/coupling-coherence-web4-sage.md`

## Context

The coupling-coherence experiment tested 5 Bayesian agents discovering a random knowledge graph with controllable coupling (sharing probability p). It found a clear sigmoid transition from incoherent (C=0.34) to coherent (C=0.94), with the critical threshold at p ≈ 0.002.

## Key Findings Relevant to Web4

### 1. Sparse witnessing is sufficient

Even p = 0.01 (1% chance of sharing per pair per round) produces a 35% coherence gain. Full transparency (p=1.0) only adds another 100% on top of that. The majority of coherence gain comes from the first tiny bit of coupling.

**Implication**: Web4's Broadcast mechanism (ephemeral, public, cheap) is where most of the trust coherence value lives. Frequent Pairing and constant Witnessing are less critical than having any signal flow at all.

### 2. Hill function > tanh for coherence emergence

The Hill function (cooperative binding kinetics) fits the data better than the Synchronism tanh form (ΔAIC=4). This is thematically consistent with Web4's metabolic framing (ATP/ADP).

**Implication**: When modeling expected coherence returns from trust infrastructure investment, use cooperative binding math (Hill sigmoid), not logarithmic saturation.

### 3. Trust convergence alone is not enough

The geometric mean C = √(convergence × correctness) catches "trust bubbles" — situations where entities agree on trust scores that turn out to be wrong.

**Implication**: Web4 should track trust convergence AND outcome validation separately. A metric that combines both would detect degenerate consensus early.

### 4. Derived critical thresholds fail

The attempt to derive p_crit from system properties (noise, world entropy, agent count) failed catastrophically (400× error). Critical thresholds are empirical, not derivable.

**Implication**: Web4 cannot predict optimal federation parameters from first principles. Trust thresholds, ATP budgets, and witnessing frequencies must be learned from observed outcomes.

## No Code Changes Required

This is a theoretical back-annotation, not an implementation change. The experiment validates existing Web4 design decisions (sparse trust signals, metabolic metaphor, empirical tuning) and suggests future instrumentation (convergence × correctness metrics, Hill-curve resource modeling).

## References

- Experiment: `github.com/dp-web4/Synchronism/Research/Coupling_Coherence_Experiment.md`
- Results: `synchronism-site.vercel.app/coupling-experiment`
- Full cross-reference: `github.com/dp-web4/HRM/forum/insights/coupling-coherence-web4-sage.md`
