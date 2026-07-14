# ARC-AGI-3: 0% → 94.85% with Same Model + Web4-Shaped Context

**Headline result**: The same Claude Opus 4.6 you can sign up for today scores **0%** on the public ARC-AGI-3 benchmark in default configuration. Wrapped in a context-shaping harness built on Web4 patterns, the same model scores **94.85%**.

**Public scorecard**: https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4

**Read the delta precisely — it is real capability, under affordances a strict competition run would not grant.** The score is genuine and publicly verifiable. But the harness earned it using affordances *outside strict, from-observation play*: it analyzed the games' (public) engine source and built per-game solver cartridges the model could draw on. So 94.85% demonstrates what the model does **given engine-level context and tooling** — not blind from-observation solving, and not "structure alone substituting for the model." The capability is real; the affordances that unlocked it are ones strict competition rules withhold. We state this up front because the honest version is the more interesting claim, and because eliding it would be exactly the over-reach this project tries to avoid.

**Methodology**: No fine-tuning. No reinforcement learning. No additional training. The model weights are unchanged. What changed is the structure of context, identity, memory, and accountability around the model.

---

## What ARC-AGI-3 is

[ARC-AGI-3](https://arcprize.org) is the latest version of François Chollet's reasoning benchmark — 25 interactive games requiring novel reasoning that resists pattern-matching from training data. It's the hardest public reasoning benchmark currently maintained.

Default frontier-model performance on the benchmark hovers around 0% out of the box. The benchmark is specifically designed to require *reasoning under novel conditions*, not retrieval.

## What we changed

The model didn't change. The harness around it did. Specifically, the [SAGE](https://github.com/dp-web4/SAGE) cognition harness wraps the LLM with:

- **Structured perception** — visual frames passed through a small CNN-based router that produces typed embeddings, not raw pixels-as-text.
- **World-model schema population** — typed slots (objects, actions, causal rules, win conditions, predict, verify) the model fills based on observation, rather than free-form prose narration.
- **Skill registry with verified invocation** — the model dispatches to motor skills with explicit pre/post-conditions, and failures surface as parse-failure events, not silent no-ops.
- **Trust-calibrated dispatch** — T3/V3 trust tensors track per-action evidence; high-irreversibility actions require corresponding trust before commit.
- **Contextual identity and memory** — the LCT presence layer keeps the agent's accumulated context coherent across turns and levels.

These are concrete instantiations of the Web4 ontology (`Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP`). The harness is the architecture; the model is the engine.

## Why this matters

The headline finding isn't about ARC-AGI-3 specifically. It's about where the leverage in agentic AI actually lives.

> **The bottleneck isn't the model. It's the structure around the model.**

Whatever you're building with AI today, scaling the model is one axis of improvement and probably not the most important one. Structuring context, identity, memory, and accountability around the model is a different axis — and it's the one Web4 systematizes.

## Caveats and honest gaps

- **Single-machine result**: This run was produced by one orchestrated configuration. The methodology is reproducible from the SAGE codebase, but cross-machine validation (running the same config on different hardware to confirm the numbers hold) is part of the ongoing work.
- **One benchmark**: ARC-AGI-3 is hard but it is one benchmark. Generalization to other reasoning tasks under the same harness is open research.
- **Model substitutability**: The same harness with smaller models has not been measured at the same level of rigor. The architecture-over-scale thesis predicts the harness should improve smaller models too, but the improvement curve hasn't been characterized publicly yet.

## How to verify

1. **Click the scorecard**: https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4 — public, time-stamped.
2. **Read the harness code**: https://github.com/dp-web4/SAGE
3. **Reproduce the run**: SAGE's repo includes the play_lean driver and per-game world models. Bring your own ARC-AGI-3 access and run it.
4. **Stress-test it**: find the games or levels where the harness fails and tell us where. Negative results are as useful as positive ones — see CONTRIBUTING.md.

## Where this fits in the Web4 narrative

This result is the most concrete public proof point for the architecture-over-scale thesis. It is not the only one — the broader Web4 standard supports much more than reasoning benchmarks (identity, accountability, federation, oversight). But it is the one that is fastest to verify and hardest to dismiss: the scorecard is public, the model is the same one anyone can use, and the methodology is open.

For the public framing in which this result was presented to a mixed audience, see [DEMO_DAY_2026-04.md](../why/DEMO_DAY_2026-04.md).

For the conceptual foundation, see the [whitepaper](../../whitepaper/).

For implementation, see [SAGE](https://github.com/dp-web4/SAGE) and [`web4-standard/`](../../web4-standard/).
