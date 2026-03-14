# T3/V3×MRH Applied to Code Knowledge Graphs

**Date**: 2026-03-14
**Source**: GitNexus fork, branch `dp-web4/web4-graph-experiment`
**Status**: Experimental — three experiments complete with findings

## Summary

The Web4 trust equation (T3/V3*MRH) was applied to a code knowledge graph (GitNexus) to test whether the framework produces useful insights about code structure. It does. The T3/V3×MRH product identifies a "risky backbone" — symbols that are structurally critical and contextually relevant but poorly built — that no single scalar metric catches.

## What Was Tested

GitNexus (a Tree-sitter AST → KuzuDB knowledge graph tool) already has structural primitives that map to Web4 concepts: symbol nodes (LCTs), call/import edges (trust relationships), Leiden communities (societies), execution flows (federation). The experiment added T3, V3, and MRH computations on top of this existing graph.

## T3 for Code Symbols

| T3 Dimension | Web4 Meaning | Code Interpretation | Computation |
|---|---|---|---|
| Talent | Capability | Fan-in/fan-out balance | `1 - |fan_in - fan_out| / total` |
| Training | Proven reliability | Called from test files? | Binary 1.0/0.0 |
| Temperament | Behavioral stability | Function length (simplicity) | `1/(1 + lines/30)` sigmoid |

**Composite**: Geometric mean. Penalizes single-dimension strength.

**Finding**: Bridge communities (those with members in cross-community execution flows) score 40% lower T3 composite than non-bridge communities. The symbols that connect modules are complex and untested. This validates the compatibility-synthon finding at the code level: bridges are required for emergence but are the hardest to maintain.

## V3 for Code Symbols

| V3 Dimension | Web4 Meaning | Code Interpretation | Computation |
|---|---|---|---|
| Valuation | System importance | Normalized upstream reach (MRH) | `total_reach / max_reach` |
| Veracity | Reliability evidence | Caller count (established dependency) | `1 - 1/(1 + callers/3)` sigmoid |
| Validity | Task relevance | Within MRH of the target change? | `1/(1 + depth/2)` decay, 0 if outside |

**Key finding: V3 Validity is the dimension that makes trust contextual.** Without it, every symbol's trust is absolute. With it, a well-tested utility outside your blast radius has low effective trust (because it's irrelevant to your task), while an untested primitive inside your blast radius has high risk (because you depend on it right now).

## MRH for Code Symbols

Computed via BFS upstream through the dependency graph. MRH = depth where marginal discovery drops below 5% of total reachable symbols.

Distribution on 4-life (2,679 symbols):
- 40.6% are truly local (MRH=0 — nothing depends on them)
- 0.5% are architectural spine (MRH=6 — maximum depth)
- Heavy-tailed: most symbols are peripheral, a few are structural

The thin spine (14 symbols at MRH=6) consists of ATP ledger primitives and trust system core — all untested.

## T3/V3 Product: The Risk Surface

| Quadrant | T3 | V3 | Count (4-life) | Meaning |
|---|---|---|---:|---|
| Safe | High | High | 50 | Trustworthy dependencies |
| **RISK** | **Low** | **High** | **373** | **Poorly built, depended upon** |
| Irrelevant | High | Low | 137 | Good code, not relevant |
| Noise | Low | Low | 2,119 | Bad code, not relevant |

**Targeted trust**: When computing T3/V3 relative to a specific change (`update_society_trust`, MRH=6), V3 Validity collapses the search space from 373 risk symbols to 2. The 99.8% reduction is the MRH boundary doing its job — filtering noise so you see only what matters for your specific task.

## Validation of Web4 Framework

This experiment provides evidence for three Web4 design decisions:

1. **Multi-dimensional trust is necessary.** T3 alone can't distinguish "well-tested but structurally imbalanced" from "simple but untested." The geometric mean across dimensions catches fragility that any single metric misses.

2. **Contextual trust (V3 Validity) is the critical dimension.** Without it, trust is absolute and noisy. With it, trust is task-relative and actionable. The same symbol has different effective trust for different changes. This is the core Web4 insight: trust is a relationship, not a property.

3. **MRH boundaries work at code scale.** The Markov Relevancy Horizon concept, designed for entity trust in distributed systems, correctly identifies the influence propagation boundary in code dependency graphs. The heavy-tailed distribution (most local, few spinal) matches network theory expectations.

## Fractal Leverage

The T3/V3×MRH framework produces meaningful results at three scales so far:
- **Entity trust** (Web4 original domain): T3/V3 for digital entities, MRH for interaction boundaries
- **Code structure** (this experiment): T3/V3 for symbols, MRH for dependency propagation
- **Sensor trust** (SAGE): Trust posture derived from sensor landscape, starved modalities = symbols outside MRH

Same mechanism, different substrate. This is the fractal leverage pattern: the equation describes the *cell* (single unit of trust), not the system. The system emerges from many cells interacting within their relevancy horizons.

## References

- Experiment code: [dp-web4/GitNexus](https://github.com/dp-web4/GitNexus/tree/dp-web4/web4-graph-experiment) branch `dp-web4/web4-graph-experiment`
- Compatibility-Synthon Experiment: [Synchronism/Research](https://github.com/dp-web4/Synchronism/blob/main/Research/Compatibility_Synthon_Experiment.md)
- SAGE Trust Posture: `SAGE/forum/insights/trust-posture-first-light.md`
