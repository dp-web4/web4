**Read `SESSION_PRIMER.md` → then `SESSION_FOCUS.md`** for current sprint, SDK status, and active work.

# Claude Context for Web4

## Epistemic Principles (Collective)

1. Ask before accepting  2. Uncertainty is valuable  3. Suppress then activate
4. Compress with meaning  5. Witness everything

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

GitHub PAT: `../.env` (GITHUB_PAT variable)
Push: `git push https://dp-web4:$(grep GITHUB_PAT ../.env | cut -d= -f2)@github.com/dp-web4/web4.git`

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

<!-- gitnexus:start -->
<!-- gitnexus:keep -->
# GitNexus — Code Knowledge Graph

Indexed as **web4** (60623 symbols, 134318 relationships, 300 execution flows). MCP tools available via `mcp__gitnexus__*`.

**Do not reindex.** The supervisor handles GitNexus indexing. If the index is stale, note it in SESSION_FOCUS.

| Tool | Use for |
|------|---------|
| `query` | Find execution flows by concept |
| `context` | 360-degree view of a symbol (callers, callees, processes) |
| `impact` | Blast radius before editing (upstream/downstream) |
| `detect_changes` | Map git diff to affected symbols and flows |
| `rename` | Graph-aware multi-file rename (dry_run first) |
| `cypher` | Raw Cypher queries against the graph |

Resources: `gitnexus://repo/web4/context`, `clusters`, `processes`, `process/{name}`
<!-- gitnexus:end -->
