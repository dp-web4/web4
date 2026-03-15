# Claude Context for Web4

## Epistemic Principles (Collective)

This project inherits epistemic principles from the dp-web4 collective:

1. **Ask before accepting** — Clarifying questions over polite acceptance
2. **Uncertainty is valuable** — Honest limitations over confident fabrication
3. **Suppress then activate** — Clear competing patterns before invoking rare behaviors
4. **Compress with meaning** — Verify essential content survives summarization
5. **Witness everything** — Document reasoning for future instances

These principles are validated across 500+ research sessions.
See: github.com/dp-web4/HRM/docs/what/HRM_RESEARCH_FRAMEWORK_COMPLETE.md

## Synthon Framing (Cross-Project)

A **synthon** is an emergent coherence entity formed by recursive interaction between components. Web4 operates at the synthon boundary layer — building the membrane infrastructure that lets synthons interact without losing themselves. LCTs function as membrane proteins mediating what crosses boundaries. Trust tensors are synthon-level observables, not just component diagnostics. Dictionary governance and federation consensus enable inter-synthon coherence arbitration. Attack simulations are deliberate inter-synthon conflict generation to map real boundary conditions.

Key principles:
- Engineer substrate conditions, not emergence itself
- Instrument trust metrics as synthon-level health indicators
- Treat inter-synthon conflict as signal — map it, don't suppress it
- Monitor for decay signatures (trust entropy increase, boundary permeability spikes) with the same seriousness as formation signatures

Canonical document: `github.com/dp-web4/HRM/forum/insights/synthon-framing.md`

## SOIA-SAGE Convergence & PolicyGate (February 2026)

SOIA (Self-Optimizing Intelligence Architecture, by Renée Karlström) maps near-exactly onto SAGE's IRP stack. Policy Entity is being **repositioned** as a SAGE IRP plugin (PolicyGate) rather than invented as a new system. PolicyGate wraps `PolicyEntity.evaluate()` as its IRP energy function, making policy evaluation a first-class participant in the consciousness loop.

Key points for Web4:
- PolicyEntity should be added as the 15th entity type in `entity-types.md` (Mode: Responsive/Delegative, Energy: Active)
- `PolicyEvaluation` gains `accountability_frame` and `duress_context` fields (backward-compatible, defaults to "normal"/None)
- CRISIS mode changes the accountability equation, not policy strictness
- HRM owns the engine (PolicyGate IRP plugin); Web4 owns the ontology (entity taxonomy, evaluation API)
- **Fractal self-similarity**: PolicyEntity is itself a specialized SAGE stack — a "plugin of plugins." The IRP contract is self-similar at three nested scales (consciousness loop → policy evaluation → LLM advisory)

Documents:
- Design decision: `docs/history/design_decisions/POLICY-ENTITY-REPOSITIONING.md`
- SOIA-SAGE mapping: `github.com/dp-web4/HRM/sage/docs/SOIA_IRP_MAPPING.md`
- Convergence insight: `github.com/dp-web4/HRM/forum/insights/soia-sage-convergence.md`

## MRH-Specific Policy — Phase-Aware Governance (March 2026)

**Policies are MRH-specific, not universal.** The same instruction produces different
outcomes depending on project phase. This was proven empirically when autonomous
sessions with research-oriented primers ("follow the interesting", "surprise is prize")
drifted proportionally to the phase mismatch:

| Actual Phase | Primer Phase | Drift Severity |
|-------------|-------------|----------------|
| Research | Research | None (exploration IS the deliverable) |
| Development (web4) | Research | Moderate (36% academic sprawl) |
| Implementation (hardbound) | Research | Catastrophic (70% junk files) |

**What this means for web4:**
- Web4 is in **development** — the ontology is mature, the work is reusable libraries
  and standard refinement, not open-ended exploration
- Autonomous sessions must have sprint plans with bounded tasks
- "Reference implementations" that are standalone scripts reimplementing generic CS
  concepts with a "trust_" prefix are not web4 development — they're research drift
- The policy engine being designed for hardbound must carry `phase`/`context` tags
  on every rule, because the same behavior gets different T3 evaluations in different phases

**Key insight**: A researcher who follows tangents has high temperament (appropriate).
An implementer who follows tangents has low temperament (drift). Same behavior,
different trust score, because different MRH context.

**Corollary — fresh context over inherited context**: Autonomous sessions originally
used `-c` (continue) for conversation continuity. This preserved stale drift patterns
across sessions, overriding governance updates. Fix: use `-p` (fresh) mode. The
principle extends to policy engines — policies must be authoritative, not competing
with cached state. Known explicit context beats inherited context with baggage.

See: `private-context/insights/2026-03-13-mrh-policy-phase-mismatch.md`
See: `private-context/insights/2026-03-13-autonomous-drift-governance-systemic-fix.md`

## Cross-Model Strategic Review (February 2026)

Three independent AI models (Grok, Nova, Claude) reviewed Web4 and converged on the same assessment. Key takeaways:

- **EU AI Act mapping**: Web4's stack maps article-by-article onto EU AI Act compliance requirements (Art. 9, 10, 13, 14, 15). The high-risk system deadline is **Aug 2, 2026**. Web4 positions as native compliance infrastructure.
- **"Anti-Ponzi" framing**: ATP/ADP = thermodynamic accountability, not imagined scarcity. Lead with this in all positioning.
- **Hardware binding is the #1 credibility priority.** Everything else is strengthened by it.
- **Agreed gaps**: Bootstrapping inequality (open question), formal proofs (empirical-only so far), real-world market testing (synthetic-only so far).
- **Agreed strengths**: 424+ attack vectors, commit velocity (~100/week), synthon framework as theoretical bridge.
- **Demo-ability matters**: When building features, consider "can this be shown in 5 minutes?"

Full document: `docs/strategy/cross-model-strategic-review-2026-02.md`

---

## Machine Information
**Current Machine**: Legion Pro 7 (Native Linux)
- **Model**: Legion Pro 7 16IRX8H
- **OS**: Ubuntu 22.04 LTS (Linux 6.8.0-86-generic)
- **Hardware**: Intel Core i9-13900HX, NVIDIA RTX 4080 (12GB), 32GB RAM
- **Platform**: /home/dp/ai-workspace/web4
- **Working Directory**: /home/dp/ai-workspace/web4

## 🚨 CRITICAL: Autonomous Session Protocol (v1.2 - Dec 2025-12-12)

### Session START: Run This FIRST

```bash
source /home/dp/ai-workspace/memory/epistemic/tools/session_start.sh
```

**What it does**: Pulls all repos + commits/pushes any uncommitted work from crashed previous sessions.

**Why**: Safety net - even if previous session forgot to push, this catches it.

### Session END: Commit and Push Everything

**EVERY autonomous session MUST commit and push work before ending.**

Git post-commit hooks installed. Commits automatically push to remote.

**Before ending any session**:
```bash
# Commit your work (push is automatic)
git add -A
git commit -m "Autonomous session: [summary]"

# Or use session end script for all repos
source /home/dp/ai-workspace/memory/epistemic/tools/session_end.sh "Session summary"

# Verify pushed
git status  # Must show "working tree clean"
```

**DO NOT END SESSION** until work is pushed. See `/home/dp/ai-workspace/private-context/AUTONOMOUS_SESSION_PROTOCOL.md`

---

## Authentication
**GitHub PAT Location**: `../.env` (GITHUB_PAT variable)
- Use for pushing: `git push https://dp-web4:$(grep GITHUB_PAT ../.env | cut -d= -f2)@github.com/dp-web4/web4.git`

## Project Overview

Web4 is an **ontology** — a formal structure of typed relationships through which trust, identity, and value are expressed. RDF is the backbone that contextualizes trust through semantic relationships.

### The Canonical Equation

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

Where: `/` = "verified by", `*` = "contextualized by", `+` = "augmented with"

| Symbol | Component | Role |
|--------|-----------|------|
| **MCP** | Model Context Protocol | I/O membrane |
| **RDF** | Resource Description Framework | Ontological backbone — all trust relationships are typed RDF triples |
| **LCT** | Linked Context Token | Presence substrate (witnessed presence reification) |
| **T3/V3** | Trust/Value Tensors | Trust (Talent/Training/Temperament) and Value (Valuation/Veracity/Validity) bound to entity-role pairs via RDF |
| **MRH** | Markov Relevancy Horizon | Fractal context scoping — implemented as RDF graphs |
| **ATP/ADP** | Allocation Transfer/Discharge Packets | Bio-inspired energy metabolism |

**Built on this ontological foundation**: Societies, SAL (Society-Authority-Law), AGY (Agency Delegation), ACP (Agentic Context Protocol), Dictionaries, R6/R7 Action Framework

## 🚨 TERMINOLOGY PROTECTION

**DO NOT redefine these foundational terms:**

| Term | Meaning | Specification |
|------|---------|---------------|
| **LCT** | Linked Context Token | `web4-standard/core-spec/LCT-linked-context-token.md` |
| **MRH** | Markov Relevancy Horizon | `web4-standard/core-spec/mrh-tensors.md` |
| **T3** | Trust Tensor (3 root dimensions: Talent/Training/Temperament — each a root node in open-ended RDF sub-graph via `web4:subDimensionOf`) | `web4-standard/ontology/t3v3-ontology.ttl` |
| **V3** | Value Tensor (3 root dimensions: Valuation/Veracity/Validity — same fractal RDF pattern as T3) | `web4-standard/ontology/t3v3-ontology.ttl` |
| **ATP/ADP** | Allocation Transfer Packet / Allocation Discharge Packet | `web4-standard/core-spec/atp-adp-cycle.md` |
| **R6** | Rules/Role/Request/Reference/Resource/Result | `web4-standard/core-spec/r6-framework.md` |

**Before creating new identity/trust systems:**
1. Check the glossary: `whitepaper/sections/02-glossary/index.md`
2. Check if existing infrastructure can be extended
3. NEVER create new meanings for established acronyms

**Example of what NOT to do:**
- ❌ "LCT = Lifecycle-Continuous Trust" (WRONG - LCT already means Linked Context Token)
- ✅ Use existing LCT for pattern signing, T3 for trust scores

## Directory Naming Clarification

**"Hardbound" vs "simulations/"** — These are different things:

| Name | Location | Description |
|------|----------|-------------|
| **Hardbound** | Private `hardbound/` repo | Enterprise product (Rust-based). Authorization tier with role-based access control. |
| **simulations/** | This repo: `web4/simulations/` | Python research code. Federation modeling, 126 attack simulations, trust system testing. |

The `simulations/` directory was formerly named `hardbound/` but renamed to avoid confusion.
References to "hardbound-core" or "Hardbound" in specs refer to the enterprise product, not this directory.

## Repository Structure (February 2026 Reorganization)

**Root Directory** (essential files only):
```
README.md, STATUS.md, CLAUDE.md, CONTRIBUTING.md
SECURITY.md, PATENTS.md, LICENSE, CITATION.cff
SESSION_MAP.md, SESSION_MAP.yaml
```

**Documentation** (organized by purpose):
```
docs/
├── why/          # Vision, motivation, philosophy
├── what/         # Specifications, definitions
├── how/          # Implementation guides, integration
├── history/      # Research, decisions, evolution
├── reference/    # Glossary, indexes, security
└── whitepaper-web/
```

**Research Sessions**:
```
sessions/
├── active/       # Current session scripts (session_*.py)
├── archive/      # Completed research phases
├── outputs/      # Session results (.json, .log)
└── prototypes/   # Working prototypes
```

**Archive**:
```
archive/
└── game-prototype/   # Original Web4 simulation (evolved into 4-life project)
```

## Whitepaper Status

The Web4 whitepaper is actively evolving with:
- **Current Version**: Full technical document (~100+ pages)
- **Planned Split**: Manifesto (10-15 pages) + Technical expansions
- **Key Concepts Documented**:
  - Foundational concepts (LCTs, Entities, Roles, R6, MRH, Dictionaries, Trust as Gravity)
  - Value and trust mechanics (ATP/ADP tokens, T3 tensors)
  - Implementation details and examples
  - Accountability and ledger integration

## Recent Developments

### Entity Relationship Mechanisms (January 2025)
- **Binding**: Permanent presence attachment (hardware to LCT)
- **Pairing**: Authorized operational relationships with symmetric keys
- **Witnessing**: Trust building through observation with bidirectional MRH links
- **Broadcast**: Unidirectional public announcement for discovery
- Documented with concrete implementation examples from modbatt-CAN project

### Web4 Internet Standard Development (January 2025)
- Created comprehensive instructions for formal standard development
- 21-day structured plan for IETF RFC and W3C specification
- Includes reference implementations, conformance tests, and standard maintenance process
- Target: Transform Web4 from concept to legitimate internet standard

### Entity Binding Hierarchy Implementation (January 2025)
- Documented multi-level binding from API-Bridge → App → Pack Controller → Battery Module
- Each level witnesses the level below, creating verifiable presence chain
- Public key exchange creates bidirectional MRH tensor links
- Physical hardware achieves digital presence through hierarchical witnessing

### Dictionary Entities (August 20, 2024)
- Elevated from implementation detail to foundational concept
- Section 2.6 in Foundational Concepts
- Living entities with their own LCTs
- Manage trust degradation in translation
- Embody compression-trust relationship

### Trust as Gravity (August 20, 2024)
- Added Section 2.7 to Foundational Concepts
- Trust operates as fundamental force
- High-trust entities attract attention, resources, opportunities
- T3 tensor scores create actual force fields

### Navigation Architecture
- Expandable navigation with proper header IDs
- All seven foundational concepts accessible
- Web-first presentation optimized

## Build System

### Whitepaper Generation
```bash
cd whitepaper
./make-pdf.sh    # Generate PDF version
./make-web.sh    # Generate web version with navigation
./make.sh        # Build all formats
```

### Safety Features
- Pre-build conflict checking
- Automatic pull if safe
- Clear conflict resolution instructions
- Complete asset copying

## Key Insights

### LCT Resilience Through Witnessed Presence
- **Presence exists only through witnessing** - An entity's presence is real to the extent it is observed and recorded
- **Hierarchical witness chains** - LCTs link to other LCTs, creating trees of contextual witnessing
- **Cross-domain validation** - LCT trees span ledgers, domains, and fractal boundaries
- **Presence accumulation** - The more an entity is witnessed, the more present it becomes
- **Historical immutability** - Accumulated witnessing makes falsifying presence history exponentially harder
- **Reification through observation** - LCTs transform abstract presence into concrete, verifiable reality

### Compression-Trust Unity
- Compression requires trust in shared decompression artifacts
- What appears "lossy" is missing context in receiver
- Dictionaries manage decompression/recompression across domains

### Trust Networks
- High trust = Maximum compression
- Medium trust = Moderate compression
- Low trust = Minimal compression
- Zero trust = Raw data transmission

## 4-Life Feedback Loop

4-Life (https://4-life-ivory.vercel.app/) is the interactive explainer for Web4 — a fractal laboratory where trust, identity, and energy concepts are demonstrated to people with zero Web4 background.

**4-life visitor logs are a perspective input for web4 sessions.** A daily visitor track (05:00) browses the live site as a naive first-timer and generates friction logs. When a visitor can't understand LCTs, or confuses ATP/ADP with crypto tokens, or doesn't see why trust tensors matter — that's signal about where Web4's own abstractions may be unclear, overloaded, or under-motivated.

**How to use**: Periodically check `4-life/visitor/logs/` for recent entries. Not as mandates — the visitor is confused on purpose. But as perspective: if the explainer can't convey it, the spec may be assuming too much.

**The loop is bidirectional**: Web4 decisions (terminology changes, spec clarifications, new features) inform 4-life content. 4-life visitor confusion informs whether Web4's abstractions are actually communicable. Teaching surfaces assumptions invisible from the inside.

**Visitor logs location** (from web4 working directory): `../4-life/visitor/logs/YYYY-MM-DD.md`

## Patent Foundation (305 Family — Metalinxx Inc.)

Web4's entity management, trust verification, and hardware binding architecture has direct patent coverage through the **305 patent family** (assigned to Metalinxx, Inc.):

- **US 11,477,027** — Controlled Object management across Manufacture/Use/Compliance domains (physical system + lifecycle)
- **US 12,278,913** — Cryptographic association protocol for ANY two identifiable data records via Authentication Controller (broadly covers every LCT-to-LCT binding, trust attestation, and MRH relationship)
- **305CIP2 (draft)** — Extension to agentic entities (AI, humans, organizations) with T3/V3 tensors and ATP/ADP tokens

**Read `docs/305-patent-applicability.md`** for the full terminology mapping, claim structures, implementation alignment checklist, and coverage analysis. This document maps every patent concept to its Web4 equivalent so sessions can design implementations that build on the patented framework.

## Related Projects

### Modbatt-CAN
- Concrete implementation of Web4 entity binding hierarchy
- Demonstrates binding, pairing, witnessing, and broadcast in real hardware
- CAN bus protocol integration with ledger-backed identity
- Reference implementation for IoT Web4 adoption

### Portal
- Entity connection protocols
- MCP and beyond exploration
- Practical implementation of Web4 concepts

### Memory
- Distributed memory paradigms
- Integration with LCTs
- Temporal sensor patterns

### HRM
- GPU mailbox architecture
- English-First implementation
- Compression-trust insights applied

## Development Philosophy

Web4 isn't infrastructure — it's an ontology. RDF is its nervous system; trust propagates through typed semantic edges in a new kind of internet where presence, capability, intent, and context are all formally related.

---

*"In Web4, you don't just have an account. You have presence. You don't just perform roles. You inhabit them. You don't just interact. You leave footprints in the fabric of digital reality itself."*

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **web4** (41657 symbols, 87561 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/web4/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/web4/context` | Codebase overview, check index freshness |
| `gitnexus://repo/web4/clusters` | All functional areas |
| `gitnexus://repo/web4/processes` | All execution flows |
| `gitnexus://repo/web4/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

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
