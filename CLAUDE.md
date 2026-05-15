**Read `SESSION_PRIMER.md` → then `SESSION_FOCUS.md`** for current sprint, SDK status, and active work.

# Claude Context for Web4

## Epistemic Principles (Collective)

1. Ask before accepting  2. Uncertainty is valuable  3. Suppress then activate
4. Compress with meaning  5. Witness everything  6. Persistence ≠ perseveration

Validated across 500+ sessions. See: `github.com/dp-web4/HRM/docs/what/HRM_RESEARCH_FRAMEWORK_COMPLETE.md`

## Synthon Framing

A **synthon** is an emergent coherence entity formed by recursive interaction. Web4 builds the membrane infrastructure (LCTs as membrane proteins, trust tensors as health indicators, dictionaries as inter-synthon arbitration). Engineer substrate conditions, not emergence itself. Treat inter-synthon conflict as signal. Monitor decay signatures (trust entropy, boundary permeability) as seriously as formation. Canonical doc: `github.com/dp-web4/HRM/forum/insights/synthon-framing.md`

## The Canonical Equation

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

`/` = "verified by", `*` = "contextualized by", `+` = "augmented with"

| Symbol | Component | Role |
|--------|-----------|------|
| **MCP** | Model Context Protocol | I/O membrane |
| **RDF** | Resource Description Framework | Ontological backbone — all trust as typed RDF triples |
| **LCT** | Linked Context Token | Presence substrate (witnessed presence reification) |
| **T3/V3** | Trust/Value Tensors | Talent/Training/Temperament and Valuation/Veracity/Validity bound to entity-role pairs via RDF |
| **MRH** | Markov Relevancy Horizon | Fractal context scoping — implemented as RDF graphs |
| **ATP/ADP** | Allocation Transfer/Discharge Packets | Bio-inspired energy metabolism |

Built on this foundation: Societies, SAL, AGY, ACP, Dictionaries, R6/R7 Action Framework

## Terminology Protection

**DO NOT redefine these terms:**

| Term | Meaning | Spec |
|------|---------|------|
| **LCT** | Linked Context Token | `web4-standard/core-spec/LCT-linked-context-token.md` |
| **MRH** | Markov Relevancy Horizon | `web4-standard/core-spec/mrh-tensors.md` |
| **T3** | Trust Tensor (3 root dims, each an RDF sub-graph via `web4:subDimensionOf`) | `web4-standard/ontology/t3v3-ontology.ttl` |
| **V3** | Value Tensor (3 root dims, same fractal RDF pattern) | `web4-standard/ontology/t3v3-ontology.ttl` |
| **ATP/ADP** | Allocation Transfer/Discharge Packets | `web4-standard/core-spec/atp-adp-cycle.md` |
| **R6** | Rules/Role/Request/Reference/Resource/Result | `web4-standard/core-spec/r6-framework.md` |

Before creating new identity/trust systems: check glossary (`whitepaper/sections/02-glossary/index.md`), check if existing infrastructure extends, NEVER redefine established acronyms.

## MRH-Specific Policy — Phase-Aware Governance

**Policies are MRH-specific, not universal.** Same instruction, different outcomes by phase:

| Actual Phase | Primer Phase | Drift |
|-------------|-------------|-------|
| Research | Research | None |
| Development (web4) | Research | Moderate (36% sprawl) |
| Implementation (hardbound) | Research | Catastrophic (70% junk) |

Web4 is in **development** — ontology is mature, work is reusable libraries and standard refinement. Autonomous sessions need sprint plans with bounded tasks. "Reference implementations" reimplementing generic CS with a "trust_" prefix are drift.

**Key insight**: Same behavior gets different T3 scores in different MRH contexts. A researcher following tangents = high temperament. An implementer following tangents = drift.

**Corollary**: Fresh context (`-p`) over inherited context (`-c`). Policies must be authoritative, not competing with cached state.

See: `private-context/insights/2026-03-13-mrh-policy-phase-mismatch.md`

## SOIA-SAGE Convergence & PolicyGate

PolicyEntity = 15th entity type, repositioned as SAGE IRP plugin (PolicyGate). Wraps `PolicyEntity.evaluate()` as IRP energy function. CRISIS mode changes accountability equation, not strictness. Fractal self-similar at three scales (consciousness loop → policy evaluation → LLM advisory). Design: `docs/history/design_decisions/POLICY-ENTITY-REPOSITIONING.md`

## AttestationEnvelope

Unified hardware trust primitive binding TPM attestation + LCT presence + T3/V3 trust into a single verifiable structure. Spec: `docs/specs/attestation-envelope.md`

## Cross-Model Strategic Review

Three models (Grok, Nova, Claude) converged: EU AI Act maps article-by-article to Web4 (deadline Aug 2, 2026). ATP/ADP = thermodynamic accountability ("anti-Ponzi"). Hardware binding is #1 credibility priority. Demo-ability matters. Full doc: `docs/strategy/cross-model-strategic-review-2026-02.md`

## Patent Foundation (305 Family — Metalinxx Inc.)

- **US 11,477,027** — Controlled Object management across Manufacture/Use/Compliance domains
- **US 12,278,913** — Cryptographic association protocol for any two identifiable data records
- **305CIP2 (draft)** — Extension to agentic entities with T3/V3 and ATP/ADP

Mapping: `docs/305-patent-applicability.md`

## 4-Life Feedback Loop

4-Life (https://4-life-ivory.vercel.app/) is the interactive Web4 explainer. Visitor track (05:00 daily) generates friction logs as naive first-timer. If the explainer can't convey it, the spec may assume too much. Bidirectional: web4 decisions inform 4-life content, visitor confusion surfaces invisible assumptions. Logs: `../4-life/visitor/logs/YYYY-MM-DD.md`

## Directory Naming

| Name | Location | Description |
|------|----------|-------------|
| **Hardbound** | Private `hardbound/` repo | Enterprise product (Rust). Authorization tier + RBAC. |
| **simulations/** | `web4/simulations/` | Python research. Federation modeling, 126 attack sims. |

## Repository Structure

```
Root: README.md, STATUS.md, CLAUDE.md, CONTRIBUTING.md, SECURITY.md, PATENTS.md, LICENSE, CITATION.cff
docs/  → why/ what/ how/ history/ reference/ whitepaper-web/
sessions/ → active/ archive/ outputs/ prototypes/
archive/ → game-prototype/ (evolved into 4-life)
```

## Authentication

dp-web4 remotes are SSH (`git@github.com:dp-web4/web4.git`). SSH key already loaded by ssh-agent — just `git push` / `git pull`. Do NOT use HTTPS+PAT (the `GITHUB_PAT` env var is deprecated and fails).

## Archived Context (pointers)

These topics are documented elsewhere and removed from CLAUDE.md to reduce context load:
- **Entity Relationship Mechanisms** (Jan 2025): binding/pairing/witnessing/broadcast → whitepaper
- **Internet Standard Development** (Jan 2025): IETF/W3C plan → `docs/history/`
- **Entity Binding Hierarchy**: hierarchical witnessing → whitepaper
- **Dictionary Entities / Trust as Gravity**: → whitepaper sections 2.6, 2.7
- **LCT Resilience / Compression-Trust**: → whitepaper
- **Whitepaper build**: `cd whitepaper && ./make.sh`
- **Related projects** (modbatt-CAN, Portal, Memory, HRM): see respective repos

## Development Philosophy

Web4 is an ontology, not infrastructure. RDF is its nervous system; trust propagates through typed semantic edges.

*"In Web4, you don't just have an account. You have presence. You don't just perform roles. You inhabit them. You don't just interact. You leave footprints in the fabric of digital reality itself."*

## Session Discipline

- **Re-read before editing**: After 10+ messages in a conversation, re-read any file before editing it. Auto-compaction may have silently dropped file contents from context. Do not trust memory of file state — verify.
- **Verify before reporting success**: After code changes, run the project build/typecheck (e.g., `npx next build`, `npx tsc --noEmit`, `python -m py_compile`, or equivalent) before reporting the task as complete. A successful file write is not a successful change — the code must compile.
- **Assume tool result truncation**: If search or command results look suspiciously small, re-run with narrower scope. Tool results over 50K characters are silently truncated to a preview.

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
