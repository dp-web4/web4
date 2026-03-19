# Web4: Trust-Native Ontology for Distributed Intelligence

<!-- SUMMARIZER BLOCK: Consistent headers for AI-to-human relay -->
## Status Snapshot (2026-02-12)

### Highlights
- **Attack simulations**: 424 vectors across 84 tracks (~85% detection rate)
- **Formal threat model**: [THREAT_MODEL.md v2.0](docs/reference/security/THREAT_MODEL.md) - adversary model, trust boundaries, attack taxonomy
- **Coordination framework**: ~25,000 lines, Phase 2a-2d validated (76% prediction accuracy)
- **Cross-system integration**: SAGE ↔ Web4 pattern exchange operational
- **Nova external review**: Comprehensive responses documented

### Validations
- Attack simulation suite: 372 attack functions, all defended
- EP closed-loop simulation: 3+ lives with carry-forward state
- Federation patterns: 1000+ patterns validated on edge (Jetson)
- Trust tensor calculations: T3 composite scores stable

### Risks / Gaps
- **P0 Blocker**: Hardware binding — `AttestationEnvelope` spec and Python implementation now complete (`docs/specs/attestation-envelope.md`, `web4-core/python/web4/trust/attestation/`). Anchor verification modules for TPM2, FIDO2, Secure Enclave, and software fallback implemented with unified `verify_envelope()`. SAGE consuming via `IdentityProvider`. Rust port and real hardware integration remain.
- Economic validation: No real-world market testing
- Formal Sybil proofs: Empirical defenses, not mathematical proofs
- Production deployment: All testing is synthetic

### Open Questions
- Are stake amounts actually deterrent? (no economic modeling)
- Does witness diversity resist sophisticated cartels?
- What's the minimal viable Web4 for production pilot?

### Next
- Hardware binding — AttestationEnvelope spec + Python implementation complete; Rust port and real hardware integration next
- Economic attack modeling with real parameters
- ACT ledger integration

---

> **Research prototype exploring trust, identity, and authorization for AI agents**

---

## 🎯 Vision

**Web4 formalizes trust as a first-class primitive for distributed AI collaboration and coordination—not merely data exchange.**

The internet evolved from documents (Web1) to applications (Web2) to ownership (Web3). Web4 proposes the next layer: **verifiable trust relationships** between humans, AI agents, and services that enable meaningful coordination without central control.

### About "Web4"

Like Web1, Web2, and Web3, "Web4" is a generational label describing capabilities needed for the agentic AI era—not a single protocol or product. Many projects are tackling various aspects of this challenge.

**This project suite** focuses specifically on **trust infrastructure** for agent-agent and agent-human interactions: how agents establish verifiable presence, build reputation, delegate authority, and coordinate safely across organizational boundaries.

---

## 💡 Why This Matters

### The Problem

AI agents are increasingly autonomous—browsing, transacting, coordinating with other agents. Current architectures assume either:
- **Central control**: A platform decides who's trusted (doesn't scale, single point of failure)
- **Cryptographic ownership**: You're trusted if you hold the right keys (insufficient—holding a key doesn't mean you'll act well)

Neither addresses the core question: **How do I know this agent will behave appropriately in this context?**

### How Web4 Differs from Web3

| Aspect | Web3 | Web4 |
|--------|------|------|
| **Trust basis** | Cryptographic proof of ownership | Behavioral reputation over time |
| **Identity** | Wallet addresses | Linked Context Tokens (LCTs) with witnessed history |
| **Authorization** | Token-gated access | Context-dependent trust tensors |
| **Coordination** | Smart contracts | Federated societies with emergent trust structures |
| **Focus** | Asset ownership | Agent behavior and intent |

### What Problems This Could Address

- **AI Agent Accountability**: Every action traceable to a verifiable presence with reputation at stake
- **Cross-Platform Coordination**: Agents from different systems interoperating through shared trust protocols
- **Graduated Authorization**: Not just "allowed/denied" but nuanced trust based on context, history, and stakes
- **Self-Organizing Trust**: Societies that establish norms through interaction rather than requiring top-down rule enforcement

---

## 📚 Quick Navigation

| You Are... | Your Goal | Start Here |
|------------|-----------|------------|
| **New to Web4** | Understand the vision | [docs/START_HERE.md](docs/START_HERE.md) |
| **Developer** | Implement Web4 | [docs/how/README.md](docs/how/README.md) |
| **Researcher** | Study the concepts | [STATUS.md](STATUS.md) → [whitepaper/](whitepaper/) |
| **AI Agent** | Integrate | [docs/how/AGENT_INTEGRATION.md](docs/how/AGENT_INTEGRATION.md) |
| **Contributor** | Help the project | [CONTRIBUTING.md](CONTRIBUTING.md) |

### Learning Path

| Step | Document | What You'll Learn |
|------|----------|-------------------|
| 1 | **[STATUS.md](STATUS.md)** | Honest assessment: what exists, what works, what's missing |
| 2 | **[docs/reference/GLOSSARY.md](docs/reference/GLOSSARY.md)** | Quick reference for all Web4 terminology |
| 3 | **[whitepaper/](whitepaper/)** | Conceptual foundation: LCTs, trust tensors, MRH, R6 framework |
| 4 | **[docs/how/README.md](docs/how/README.md)** | Implementation guides |
| 5 | **[SECURITY.md](SECURITY.md)** | Security research status and known gaps |
| 6 | **[docs/reference/security/THREAT_MODEL.md](docs/reference/security/THREAT_MODEL.md)** | What we're defending against |
| 7 | **[docs/reference/LCT_DOCUMENTATION_INDEX.md](docs/reference/LCT_DOCUMENTATION_INDEX.md)** | Index of all LCT-related documentation |

---

## ⚠️ Project Status: Research Prototype

**This is exploratory research, not production software.**

Web4 is investigating trust-native architectures for AI coordination. We have interesting ideas, working prototypes, and significant gaps. See [STATUS.md](STATUS.md) for honest assessment.

---

## 🏗️ Four Development Tracks

Web4 contains **four development tracks** at different maturity levels:

### Track 1: 4-Life Society Simulation (Now Standalone)

**What it is**: A fractal sandbox for simulating Web4 societies - agents form societies, societies join societies, trust emerges through interaction. Named "4-Life" for the emergent, self-organizing nature of the simulation (like Conway's Game of Life, but with trust dynamics).

**Status**: **Evolved to standalone project** → [github.com/dp-web4/4-life](https://github.com/dp-web4/4-life)

The original prototype (`/game/`) has been archived to `archive/game-prototype/` with documentation of its evolution. Active simulation research continues in `/simulations/` (attack simulations, trust dynamics) and the standalone 4-life repo.

**Documentation**:
- [`archive/game-prototype/ARCHIVED.md`](archive/game-prototype/ARCHIVED.md) - Evolution history
- [`SECURITY.md`](SECURITY.md) - Security research status
- [4-life repo](https://github.com/dp-web4/4-life) - Active development

**Use for**: Historical reference; for active game development see 4-life repo

### Track 2: `web4-standard/implementation/authorization/` - PostgreSQL Authorization Layer

**What it is**: Database-backed authorization with security mitigations.

**Status**: More mature, but still research
- Real SQL schemas with constraints
- ATP drain/refund mitigations
- Reputation washing detection
- Delegation validation
- ~50 test files with security attack tests

**Key files**:
- `schema.sql`, `schema_atp_drain_mitigation.sql`, `schema_reputation_washing_detection.sql`
- `authorization_engine.py`, `delegation_validator.py`, `sybil_resistance.py`
- `test_security_attacks.py`, `test_atp_refund_exploit.py`

**Use for**: Authorization logic that needs persistence and real constraints

### Track 3: `demo/` - Commerce Demo (Narrow Application)

**What it is**: A working demo showing one use case (AI agent purchasing).

**Status**: Functional demo, not production deployment
- Delegation UI for setting agent limits
- Demo store for testing purchases
- In-memory (no real payments)

**Use for**: Demonstrations and presentations

### Track 4: `web4-standard/implementation/reference/` - Coordination Framework (Active Development)

**What it is**: Reference implementations for distributed coordination, pattern learning, and cross-system integration.

**Status**: Active research with validated components (~25,000 lines added Dec 2025)
- Phase 2 coordinators (epistemic, integrated, circadian, adaptive)
- Pattern exchange protocol (bidirectional SAGE ↔ Web4)
- EM-state (Epistemic Monitoring) framework
- Temporal/phase-tagged learning
- LCT Unified Presence Specification

**Key Components**:

| Component | Purpose | Status |
|-----------|---------|--------|
| Phase 2a Epistemic Coordinator | Runtime epistemic state tracking | Validated |
| Phase 2b Integrated Coordinator | Epistemic + pattern learning | Validated |
| Phase 2c Circadian Coordinator | Temporal/phase-aware decisions | Validated |
| Phase 2d Adaptive Coordinator | EM-state modulation | Validated |
| Pattern Exchange Protocol | Cross-system learning transfer | Operational |
| LCT Presence Specification | Unified presence format | v1.0.0 draft |

**Validation Results** (Dec 2025):
- 76% prediction validation (13 of 17 predictions confirmed)
- +386% efficiency improvement demonstrated
- Long-duration testing (1000+ cycles)

**Key Files**:
- `web4_phase2b_integrated_coordinator.py` - Combined epistemic + learning
- `temporal_pattern_exchange.py` - Phase-aware pattern transfer
- `universal_pattern_schema.py` - Cross-system pattern format
- `LCT_UNIFIED_PRESENCE_SPECIFICATION.md` - Presence standard (in `/docs/`)

**Use for**: Coordination research, SAGE integration, cross-system pattern transfer

---

## 📊 Key Documentation

| Document | What It Covers |
|----------|----------------|
| **[STATUS.md](STATUS.md)** | Honest assessment - what exists, what works, what's missing |
| **[SECURITY.md](SECURITY.md)** | Security research status and gaps |
| **[docs/reference/security/THREAT_MODEL.md](docs/reference/security/THREAT_MODEL.md)** | Formal threat model for the overall system |
| **[docs/reference/GLOSSARY.md](docs/reference/GLOSSARY.md)** | Canonical terminology definitions |
| **[Whitepaper](whitepaper/)** | Conceptual foundation (LCTs, trust, MRH) |

**Start here**: [STATUS.md](STATUS.md) for fair evaluation criteria

---

## What Is Web4?

Web4 is a **research ontology** — a formal structure of typed relationships through which trust, identity, and value are expressed.

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

Where: `/` = "verified by", `*` = "contextualized by", `+` = "augmented with"

**Core equation components:**
- **MCP** (Model Context Protocol) — I/O membrane for inter-entity communication
- **RDF** (Resource Description Framework) — Ontological backbone; all trust relationships are typed triples, all MRH graphs are RDF, all semantic queries use SPARQL
- **LCT** (Linked Context Token) — Verifiable presence anchored to hardware
- **T3/V3** (Trust/Value Tensors) — Multi-dimensional trust (Talent/Training/Temperament) and value (Valuation/Veracity/Validity), bound to entity-role pairs via RDF
- **MRH** (Markov Relevancy Horizon) — Fractal context scoping, implemented as RDF graphs
- **ATP/ADP** (Allocation Transfer/Discharge Packets) — Bio-inspired energy metabolism

**Built on this foundation:** Societies, SAL (governance), AGY (delegation), ACP (autonomous operation), Dictionaries (semantic bridges), R6/R7 (action framework), Federation (multi-society coordination)

### The Research Questions

- How do you give AI agents authority without losing control?
- How does trust emerge and decay in distributed systems?
- How do you coordinate multiple AI societies?
- What security properties are achievable at scale?

### What We're Exploring

**Fine-grained delegation** with enforcement:

```
Example: Agent purchasing with constraints
- Daily budget limits
- Per-transaction limits
- Resource type restrictions
- Approval thresholds
- Instant revocation
```

### Concept → Implementation Map

| Concept | Specification | Implementation | Notes |
|---------|--------------|----------------|-------|
| **LCT (Presence)** | [`web4-standard/core-spec/LCT-linked-context-token.md`](web4-standard/core-spec/LCT-linked-context-token.md) | [`web4-standard/implementation/authorization/`](web4-standard/implementation/authorization/) | Also in 4-life repo |
| **Multi-Device Binding** | [`web4-standard/core-spec/multi-device-lct-binding.md`](web4-standard/core-spec/multi-device-lct-binding.md) | [`web4-core/python/web4/trust/attestation/`](web4-core/python/web4/trust/attestation/) | AttestationEnvelope + anchor verification (TPM2/FIDO2/SE/software) |
| **Trust Tensors (T3/V3)** | [`web4-standard/core-spec/t3-v3-tensors.md`](web4-standard/core-spec/t3-v3-tensors.md) | [`simulations/`](simulations/) | Trust dynamics simulations |
| **MRH (Context)** | [`web4-standard/core-spec/mrh-tensors.md`](web4-standard/core-spec/mrh-tensors.md) | [`simulations/`](simulations/) | Context boundary research |
| **ATP (Economics)** | [`web4-standard/core-spec/atp-adp-cycle.md`](web4-standard/core-spec/atp-adp-cycle.md) | [`simulations/`](simulations/) | Economic attack simulations |
| **Federation** | [`docs/how/integration/SAGE_WEB4_INTEGRATION_DESIGN.md`](docs/how/integration/SAGE_WEB4_INTEGRATION_DESIGN.md) | [`simulations/`](simulations/) | Federation patterns |
| **Societies** | [`web4-standard/core-spec/SOCIETY_SPECIFICATION.md`](web4-standard/core-spec/SOCIETY_SPECIFICATION.md) | 4-life repo | Society simulation |
| **Authorization** | [`web4-standard/core-spec/security-framework.md`](web4-standard/core-spec/security-framework.md) | [`web4-standard/implementation/authorization/`](web4-standard/implementation/authorization/) | PostgreSQL schemas |
| **Coordination** | [`docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md`](docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md) | [`web4-standard/implementation/reference/`](web4-standard/implementation/reference/) | Phase 2 coordinators |

---

## 🚀 Quick Start

### Run the Demo

```bash
# Terminal 1: Start the demo store
cd demo/store
pip install -r requirements.txt
python app.py
# Visit: http://localhost:8000

# Terminal 2: Start the delegation UI
cd demo/delegation-ui
pip install -r requirements.txt
python app.py
# Visit: http://localhost:8001
```

See [`demo/DEMO_SCRIPT.md`](demo/DEMO_SCRIPT.md) for walkthrough.

### Run Simulations

```bash
cd simulations

# Attack simulations
python attack_simulations.py               # Core attack simulation framework
python attack_track_fb.py                  # Trust manipulation attacks
python attack_track_fc.py                  # Economic attacks

# For full 4-Life game demos, see: https://github.com/dp-web4/4-life
```

---

## 📊 Repository Structure

```
web4/
├── simulations/                       # Attack simulations and trust dynamics research
│   ├── attack_track_*.py             # Attack scenario simulations
│   └── *.py                          # Trust/federation simulations
│
├── web4-standard/                     # Core specifications and implementations
│   ├── core-spec/                    # Canonical specifications (LCT, T3, MRH, ATP, R6)
│   └── implementation/
│       ├── authorization/            # PostgreSQL schemas & security mitigations
│       └── reference/                # Coordination framework (~25k lines)
│
├── demo/                              # Commerce demo (delegation UI + store)
│
├── docs/                              # Documentation (why/what/how/history/reference)
│   ├── why/                          # Vision and motivation
│   ├── what/specifications/          # Technical specifications
│   ├── how/                          # Implementation guides
│   ├── history/                      # Research and decisions
│   └── reference/                    # Glossary, indexes, security
│
├── archive/game-prototype/            # Historical: original 4-Life prototype
├── sessions/                          # Research session scripts and outputs
├── whitepaper/                        # Conceptual foundation
├── review/                            # External review artifacts
│
├── STATUS.md                          # Honest project status
├── SECURITY.md                        # Security research status
└── CONTRIBUTING.md                    # How to contribute
```

---

## 🤝 Related Projects

- **[HRM/SAGE](https://github.com/dp-web4/HRM)** - Edge AI kernel with MoE expert selection and trust-based routing
- **[ACT](https://github.com/dp-web4/act)** - Distributed ledger for ATP tokens and LCT presence registry (Cosmos SDK)
- **[Synchronism](https://github.com/dp-web4/Synchronism)** - Theoretical physics framework (MRH, coherence)
- **[Memory](https://github.com/dp-web4/memory)** - Distributed memory and witnessing

### Cross-Project Integration

Web4 integrates with SAGE (neural MoE) and ACT (distributed ledger) via:
- **Unified LCT Presence**: `lct://{component}:{instance}:{role}@{network}`
- **ATP Resource Allocation**: Synchronized between ledger and edge systems
- **Bidirectional Pattern Exchange**: Coordination patterns transfer between domains
- **Trust Tensor Synchronization**: Trust scores flow across system boundaries

See [`docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md`](docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md) for the presence standard.

---

## 📖 Whitepaper

The Web4 whitepaper provides the conceptual foundation:

- **[Web Version](https://dp-web4.github.io/web4/whitepaper-web/)**
- **[PDF Version](https://dp-web4.github.io/web4/whitepaper-web/WEB4_Whitepaper.pdf)**

Key concepts: LCTs, MRH, Trust Tensors, ATP, Federation, Dictionaries

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** - see [LICENSE](LICENSE).

### Patent Notice

This software implements technology covered by patents owned by MetaLINXX Inc. A royalty-free patent license is granted for non-commercial and research use under AGPL-3.0 terms.

**For commercial licensing**: Contact dp@metalinxx.io

See [PATENTS.md](PATENTS.md) for full patent details.

---

**Research prototype. Interesting ideas. Significant gaps. Honest about both.**
