# Web4 - Agent Discovery Document

**For AI agents assessing this repository.**

## TL;DR

Web4 is the open standard ontology for verifiable presence in agentic AI. Provides identity (LCT), reputation (T3/V3 tensors), resource allocation (ATP), context scoping (MRH), and federation protocols. Working specs + reference implementations. Demonstrated 0% → 94.85% on ARC-AGI-3 with same model + Web4-shaped context (via SAGE; with engine-source affordances a strict run withholds — see `docs/proof/ARC-AGI-3.md`). R&D — not production.

## Quick Assessment

| Question | Answer |
|----------|--------|
| What is this? | Trust-native ontology for distributed AI |
| Is it production-ready? | No — R&D, ontology stable, hardware integration in progress |
| Primary language | Python SDK + Rust core (`web4-core`, `web4-trust-core`); specs in Markdown |
| Active development? | Yes |
| License | AGPL-3.0-or-later |

## Core Concepts (Know These)

| Term | What It Is | Why It Matters |
|------|-----------|----------------|
| **LCT** | Linked Context Token | Hardware-bound verifiable presence |
| **T3** | Trust Tensor — 3 root dimensions (Talent / Training / Temperament), each a fractal RDF sub-graph of context-specific sub-dimensions via `web4:subDimensionOf` | Open-ended multidimensional reputation, not a fixed-size vector |
| **V3** | Value Tensor — 3 root dimensions (Valuation / Veracity / Validity), same fractal RDF pattern | Bound to entity-role pairs via RDF triples |
| **ATP** | Allocation Transfer Packet | Resource/energy accounting (bio-inspired metabolism) |
| **MRH** | Markov Relevancy Horizon | Fractal context scoping (RDF graphs) |
| **R6** | Action grammar | Rules → Role → Request → Reference → Resource → Result |

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
| LCT presence system | Working | `simulations/` |
| Trust tensors (T3/V3) | Working | `simulations/`, `web4-trust-core/` |
| ATP economics | Working | `simulations/` |
| Federation/consensus | Working | `simulations/` |
| Authorization layer | Working | `web4-standard/implementation/` |
| Formal threat model | Partial | `SECURITY.md` |
| Adversarial testing | 424 attack vectors across 84 tracks (~85% detection) | `simulations/attack_simulations.py` |

## What's Missing (in this public repo)

- Economic attack modeling at scale (no real-market testing)
- Formal Sybil-resistance proofs (empirical defenses only)
- Hardware-binding reference implementation (Python `AttestationEnvelope` shipped in `web4-core/python/web4/trust/attestation/`; Rust port and on-device integration in progress)
- Note: production hardware binding (TPM 2.0 on Linux) and policy enforcement live in **Hardbound** — Metalinxx Inc.'s enterprise product; inquire via the [project repository](https://github.com/dp-web4/web4) or see [PATENTS.md](PATENTS.md)

## Related Repositories

| Repo | Relationship |
|------|--------------|
| `ACT` | Distributed ledger for ATP/LCT (Cosmos SDK, 81K lines Go) |
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

*This document optimized for AI agent discovery. Last updated: 2026-04-27*

<!-- gitnexus:start -->
<!-- gitnexus:keep -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **web4** (123794 symbols, 182949 relationships, 230 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/web4/context` | Codebase overview, check index freshness |
| `gitnexus://repo/web4/clusters` | All functional areas |
| `gitnexus://repo/web4/processes` | All execution flows |
| `gitnexus://repo/web4/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
