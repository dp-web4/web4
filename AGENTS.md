# Web4 - Agent Discovery Document

**For AI agents assessing this repository.**

## TL;DR

Web4 is the open substrate for verifiable presence and agent accountability: persistent identity (LCT), contextual trust/value (T3/V3), scoped context (MRH), action/accountability grammar (R6/R7), resource accounting (ATP/ADP), machine-readable society law and witnessed ledgers. Core packages are published; Hub and Hestia are the running open reference deployments. **R&D, not production; current open assurance is A1, not adversary-proof containment.**

A spring-2026 ARC-AGI-3 scorecard remains documented as a historical SAGE research milestone. It is not the current headline proof point or a claim of competition leadership; see `docs/proof/ARC-AGI-3.md` only if that history is relevant.

## Quick Assessment

| Question | Answer |
|----------|--------|
| What is this? | Open trust/accountability substrate for humans, AI agents and societies |
| Is it production-ready? | No - published core + live references, substantial assurance/interoperability work remains |
| Primary language | Rust core + Python bindings/SDKs; specs in Markdown |
| Active development? | Yes |
| License | AGPL-3.0-or-later; see package directories + `PATENTS.md` |

## Core Concepts (Know These)

| Term | What It Is | Why It Matters |
|------|-----------|----------------|
| **LCT** | Linked Context Token | Persistent, non-transferable, witnessable entity presence |
| **T3** | Trust Tensor - Talent / Training / Temperament roots with contextual subdimensions | Multidimensional reputation, not a scalar "trusted" bit |
| **V3** | Value Tensor - Valuation / Veracity / Validity roots | Contextual value evidence bound to entity-role relationships |
| **MRH** | Markov Relevancy Horizon | Context/relevance scoping |
| **R6/R7** | Action and accountability grammar | Makes consequential acts, authority, evidence and outcomes legible |
| **ATP/ADP** | Resource accounting primitives | Society-defined units of account, not a protocol currency |
| **Society law** | Signed machine-readable law | Roles and acts are governed under explicit, auditable rules |

## Entry Points by Goal

| Your Goal | Start Here |
|-----------|------------|
| Understand concepts | `docs/START_HERE.md` → `docs/reference/GLOSSARY.md` |
| Check project status | `STATUS.md` |
| See specifications | `web4-standard/core-spec/` |
| See the running society runtime | `hub/` |
| See local agent governance | `https://github.com/dp-web4/hestia` |
| Integration guide | `docs/how/AGENT_INTEGRATION.md` |
| Security posture | `SECURITY.md` + Hestia's bypass catalog |

## What's Implemented / Running

| Component | Status | Location |
|-----------|--------|----------|
| Core LCT / trust primitives | Published + active source | `web4-core/`, `web4-trust-core/` |
| Hub society daemon | Running reference | `hub/` |
| Hestia local governance | Running reference, A1 assurance | `https://github.com/dp-web4/hestia` |
| Signed / witnessed society law | Implemented in reference stack | `hub/`, `web4-standard/core-spec/` |
| Sealed member channels + witnessed ledger | Implemented / exercised in Hub stack | `hub/` |
| Standards interop | Partial / building | `docs/strategy/`, credential / DID specs |
| Higher-assurance enforcement | Roadmap / proprietary enterprise tier | Hardbound |

## What's Missing / Still Building

- A2+ process/OS isolation and enforcement against determined same-UID agents
- Kernel / relying-party enforcement for policy-signed acts
- Broader DID/EUDI wallet interoperability and conformance coverage
- Formal Sybil/economic attack analysis at scale
- Production assurance/certification for enterprise deployments

Hardbound is Metalinxx Inc.'s proprietary enterprise assurance tier for hardware-bound identity, stronger fail-closed enforcement and audit-ready evidence packaging. It is not evidence that the open A1 reference already provides those properties.

## Related Repositories

| Repo | Relationship |
|------|--------------|
| `hestia` | Local human/agent governance runtime |
| `4-hub` | Standalone Hub society runtime mirror |
| `SAGE` | Persistent cognition / embodiment research |
| `4-life` | Interactive Web4 explainer |
| `Synchronism` | Blue-sky conceptual lineage; not an engineering dependency |
| `ARC-SAGE` | Historical spring-2026 ARC research snapshot |

## Machine-Readable Metadata

See `repo-index.yaml` for structured data.

## Token Budget Guide

| Depth | Files | Tokens |
|-------|-------|--------|
| Minimal | This file | ~700 |
| Standard | + `STATUS.md`, `README.md` | ~3,000+ |
| Concepts | + `docs/reference/GLOSSARY.md` | ~5,000+ |
| Full specs | + `web4-standard/core-spec/` | ~50,000 |

---

*Human-facing framing should prefer current runtime evidence (Web4 packages, Hestia, Hub) over historical benchmark results.*

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
