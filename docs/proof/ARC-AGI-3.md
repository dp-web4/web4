# ARC-AGI-3 historical research artifact — spring 2026

> **Status, September 2026:** preserved for provenance. This page documents a real spring-2026 SAGE/ARC result, but **it is not a current competition claim, current Web4 proof point, or evidence that this lab is near the top of the ARC-AGI-3 leaderboard today.** Current competition-legal local-model work is well behind the leaders.

## The result

A Phase-1 SAGE/ARC harness around Claude Opus 4.6 produced a published **94.85%** scorecard on the public ARC-AGI-3 environments.

**Public scorecard:** https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4

The number is genuine and publicly verifiable. It should also be read with the affordances that produced it:

- the model was a frontier Claude Opus 4.6 instance;
- the harness analyzed the public game-engine source;
- per-game solver/world-model cartridges were built from that engine-level information;
- the run therefore used affordances outside strict from-observation competition play.

So the result shows what that **model + harness + engine-level context** could do. It does not show blind generalization from observation, and it does not show that structure can substitute for model capability.

## Why it was useful

At the time, the experiment supplied an important methodological result: changing the machinery around an unchanged model can materially change behavior.

The Phase-1 workflow made several useful ideas concrete:

- structured world models rather than free-form narration;
- persistent knowledge between sessions;
- explicit skill invocation;
- prediction and verification around actions;
- multi-agent accumulation of research context.

Those ideas influenced later SAGE work. The current research program has moved beyond the scorecard itself toward a harder target: persistent agents that can form hypotheses, run their own experiments, learn from outcomes, retain reusable procedures, and act under explicit governance.

## What changed since spring 2026

The field moved quickly. Stronger models and stronger competition harnesses now outperform this lab's competition-legal local-model work by a wide margin.

That changes the correct use of this artifact:

- **then:** an externally verifiable milestone and useful demonstration of harness leverage;
- **now:** a historical research record and provenance trail;
- **not now:** investor-facing competitive positioning or Web4's primary evidence of maturity.

The current Web4 proof is increasingly operational: published core packages, a running Hub society runtime, Hestia governing multiple agent vendors under one local law, witnessed action records, escalation paths, and an explicit A1 assurance boundary. See [STATUS.md](../../STATUS.md) and the root [README](../../README.md).

## Reproduction / source

The frozen Phase-1 research snapshot is preserved in [ARC-SAGE](https://github.com/dp-web4/ARC-SAGE). The public [SAGE](https://github.com/dp-web4/SAGE) repository preserves the broader architecture and historical experiment record.

The artifact remains public precisely so later framing can change **without rewriting what actually happened**.
