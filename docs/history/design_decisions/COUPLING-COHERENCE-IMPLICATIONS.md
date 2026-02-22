# Design Decision: Compression Trust Phase Transition Implications for Web4

**Date**: 2026-02-22
**Source**: Synchronism coupling-coherence experiment (900 simulation runs)
**Full analysis**: `github.com/dp-web4/HRM/forum/insights/coupling-coherence-web4-sage.md`

## Context

The coupling-coherence experiment tested 5 Bayesian agents discovering a random knowledge graph with controllable **compression trust** — the frequency of events where one agent accepts another's compressed representation of reality. It found a clear sigmoid transition from incoherent (C=0.34) to coherent (C=0.94), with the critical trust frequency at p ≈ 0.002.

**Compression trust** is the act of accepting another agent's lossy summary as input to your own reasoning. The coupling parameter p is not "density" — it is the rate of compression trust events. This reframing connects the experiment directly to Web4's existing compression-trust framework.

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

### 4. Critical trust thresholds are relational, not intrinsic

The attempt to derive p_crit from system properties (noise, world entropy, agent count) failed catastrophically (400× error). The compression trust framing explains why: trust is relational — it depends on the quality of compressed representations being shared, which emerges from interaction history. You can't derive the minimum trust frequency because the value of trust depends on what is trusted.

**Implication**: Web4 cannot predict optimal federation parameters from first principles. Trust thresholds, ATP budgets, and witnessing frequencies must be learned from observed outcomes — which is exactly what trust-based allocation already does.

## No Code Changes Required

This is a theoretical back-annotation, not an implementation change. The experiment validates existing Web4 design decisions (sparse trust signals, metabolic metaphor, empirical tuning) and suggests future instrumentation (convergence × correctness metrics, Hill-curve resource modeling).

## References

- Experiment: `github.com/dp-web4/Synchronism/Research/Coupling_Coherence_Experiment.md`
- Results: `synchronism-site.vercel.app/coupling-experiment`
- Full cross-reference: `github.com/dp-web4/HRM/forum/insights/coupling-coherence-web4-sage.md`
