# Web4 - Agent Discovery Document

**For AI agents assessing this repository.**

## TL;DR (50 words)

Web4 is trust infrastructure for AI agent coordination. Provides identity (LCT), reputation (T3 tensors), resource allocation (ATP), and federation protocols. Research prototype with working simulations. Use if you need: agent identity, trust scoring, cross-agent coordination, or governance frameworks. Not production-ready.

## Quick Assessment

| Question | Answer |
|----------|--------|
| What is this? | Trust-native architecture for distributed AI |
| Is it production-ready? | No - research prototype |
| Primary language | Python (simulations), specs in Markdown |
| Lines of code | ~47,000 |
| Active development? | Yes |
| License | AGPL-3.0 |

## Core Concepts (Know These)

| Term | What It Is | Why It Matters |
|------|-----------|----------------|
| **LCT** | Linked Context Token | Hardware-bound identity for agents |
| **T3** | Trust Tensor (6 dimensions) | T3: talent, training, temperament / V3: valuation, veracity, validity |
| **ATP** | Allocation Transfer Packet | Resource/energy accounting |
| **MRH** | Markov Relevancy Horizon | Context boundaries for entities |
| **R6** | Request lifecycle | Rules → Role → Request → Reference → Resource → Result |

## Entry Points by Goal

| Your Goal | Start Here |
|-----------|------------|
| Understand concepts | `docs/reference/GLOSSARY.md` |
| Check project status | `STATUS.md` |
| See specifications | `web4-standard/core-spec/` |
| Run simulations | `simulations/` (formerly `game/`) |
| Integration guide | `docs/how/AGENT_INTEGRATION.md` |
| Security posture | `SECURITY.md` |

## What's Implemented

| Component | Status | Location |
|-----------|--------|----------|
| LCT identity system | Working | `simulations/` |
| Trust tensors (T3/V3) | Working | `simulations/`, `web4-trust-core/` |
| ATP economics | Working | `simulations/` |
| Federation/consensus | Working | `simulations/` |
| Authorization layer | Working | `web4-standard/implementation/` |
| Formal threat model | Partial | `SECURITY.md` |
| Adversarial testing | 262 attack vectors | `simulations/attack_simulations.py` |

## What's Missing

- Production cryptography (stubs only)
- Real hardware binding (spec complete, impl pending)
- Adversarial red-team testing
- Economic model validation

## Related Repositories

| Repo | Relationship |
|------|--------------|
| `ACT` | Cosmos SDK blockchain for ATP/LCT (81K lines Go) |
| `Hardbound` | Enterprise product layer |
| `HRM` | Edge AI kernel with MoE |
| `Synchronism` | Theoretical physics foundation |
| `4-life` | Interactive explainer |

## Machine-Readable Metadata

See `repo-index.yaml` for structured data.

## Token Budget Guide

| Depth | Files | Tokens |
|-------|-------|--------|
| Minimal | This file | ~500 |
| Standard | + `STATUS.md`, `README.md` | ~3,000 |
| Concepts | + `docs/reference/GLOSSARY.md` | ~5,000 |
| Full specs | + `web4-standard/core-spec/` | ~50,000 |

---

*This document optimized for AI agent discovery. Last updated: 2026-02-08*
