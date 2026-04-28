# Web4: Verifiable Presence for AI

[![crates.io: web4-core](https://img.shields.io/crates/v/web4-core?label=crates.io%20web4-core)](https://crates.io/crates/web4-core)
[![crates.io: web4-trust-core](https://img.shields.io/crates/v/web4-trust-core?label=crates.io%20web4-trust-core)](https://crates.io/crates/web4-trust-core)
[![PyPI: web4-core](https://img.shields.io/pypi/v/web4-core?label=PyPI%20web4-core)](https://pypi.org/project/web4-core/)
[![PyPI: web4-trust](https://img.shields.io/pypi/v/web4-trust?label=PyPI%20web4-trust)](https://pypi.org/project/web4-trust/)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL--3.0--or--later-blue.svg)](LICENSE)

> **AI is already taking actions in the world. We can't prove what it did.**
> Web4 is the open standard that closes that gap.

Presence = identity + trust + context + accountability.

An open standard, proposed by Metalinxx Inc., owned by no one. Anyone can build on it.

Web1 was access. Web2 was participation. Web3 was ownership. Web4 is **verifiable presence** — for AI as a participant.

---

## Install

**Rust** (`Cargo.toml`):
```toml
[dependencies]
web4-core = "0.1"
web4-trust-core = "0.1"
```

**Python**:
```bash
pip install web4-core
pip install web4-trust
```

Both crates and both Python packages are AGPL-3.0-or-later. Patent grant terms in [PATENTS.md](PATENTS.md).

---

## Status Snapshot (2026-04-28)

### Proof point
- **0% → 94.85% on ARC-AGI-3** with the same Claude Opus 4.6, structured around Web4 patterns via the SAGE harness.
- Public scorecard: https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4
- The difference is not the model. It is the structure around it.

### Where it landed publicly
- **AI Demo Day 4** (2026-04-26): Web4 presented as "verifiable presence" for agentic AI. Slides + narration archived at https://4-gov.org/demo

### Implementation status
- **Published artifacts** (2026-04-28): `web4-core` and `web4-trust-core` on crates.io; `web4-core` and `web4-trust` on PyPI. All v0.1.0, AGPL-3.0-or-later. See `docs/proof/PUBLISHED.md`.
- Spec corpus: stable (`web4-standard/core-spec/`)
- Reference Python SDK + 8-tool MCP server: 2,627 tests, mypy --strict clean (`web4-standard/implementation/`)
- Cognition harness producing the 94.85% result: [SAGE](https://github.com/dp-web4/SAGE)
- Hardware binding (TPM 2.0 on Linux), policy enforcement, and audit pipeline: shipped in **Hardbound** — enterprise product, contact dp@metalinxx.io
- Attack simulation suite: 424 vectors across 84 tracks (~85% detection rate)
- Formal threat model: [THREAT_MODEL.md v2.0](docs/reference/security/THREAT_MODEL.md)

### Gaps
- Economic attack modeling at scale (no real-market testing)
- Formal Sybil-resistance proofs (empirical defenses only)
- Hardware binding reference implementation in this public repo (Python `AttestationEnvelope` shipped; Rust port and on-device integration in progress; Hardbound has the production version)

### Open questions
- Are stake amounts actually deterrent? (no economic modeling)
- Does witness diversity resist sophisticated cartels?
- What's the minimal viable Web4 for a public pilot?

---

## 🎯 Vision

**Web4 makes AI actions verifiable, attributable, and accountable — without central control.**

AI agents are increasingly autonomous. Booking, coding, transacting, deciding. Current architectures assume either central control (a platform decides who's trusted — doesn't scale, single point of failure) or cryptographic ownership (you're trusted if you hold the right keys — insufficient, since holding a key doesn't mean you'll act well).

Neither answers: **how do I know this agent will behave appropriately in this context, and how do I prove what it actually did?**

### About "Web4"

Like Web1, Web2, and Web3, "Web4" is a generational label for the capabilities needed in the agentic AI era — not a single protocol or product.

**This project suite** focuses specifically on **trust infrastructure** for agent-agent and agent-human interactions: how agents establish verifiable presence, build reputation, delegate authority, and coordinate safely across organizational boundaries — and how their actions stand up to audit.

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

### Track 1: 4-Life — Lifecycle and Trust-Evolution Explainer (Standalone)

**What it is**: An interactive explainer site demonstrating how agents earn trust over time — lifecycle, witnessing, and trust evolution made browsable. Live at [4-life-ivory.vercel.app](https://4-life-ivory.vercel.app/).

**Status**: **Standalone project** → [github.com/dp-web4/4-life](https://github.com/dp-web4/4-life)

The original prototype (`/game/`) was archived to `archive/game-prototype/` after evolving past the simulation stage. Active simulation research continues in `/simulations/` (attack scenarios, trust dynamics).

**Documentation**:
- [`archive/game-prototype/ARCHIVED.md`](archive/game-prototype/ARCHIVED.md) — evolution history
- [4-life repo](https://github.com/dp-web4/4-life) — active development
- [4-life-ivory.vercel.app](https://4-life-ivory.vercel.app/) — interactive demo

**Use for**: A non-technical introduction to how Web4 trust evolves. Pair with this README for the architectural view.

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

Web4 is an **ontology** — a formal structure of typed relationships through which trust, identity, and value are expressed.

**Architect's view (what Web4 is):**
```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

**Entity's view (what existence looks like from inside):**
```
Presence = LCT[T3/V3 * MRH] + RDF + ATP/ADP + MCP
```

Operators: `[]` = "contains", `/` = "verified by", `*` = "contextualized by", `+` = "augmented with"

**Core components:**
- **MCP** (Model Context Protocol) — I/O membrane for inter-entity communication
- **RDF** (Resource Description Framework) — Ontological backbone; all trust relationships are typed triples, all MRH graphs are RDF, all semantic queries use SPARQL
- **LCT** (Linked Context Token) — Verifiable presence anchored to hardware
- **T3/V3** (Trust/Value Tensors) — Fractally multidimensional. T3 has 3 root dimensions (Talent / Training / Temperament); V3 has 3 (Valuation / Veracity / Validity). Each root dimension is itself an open-ended RDF sub-graph of context-specific sub-dimensions via `web4:subDimensionOf`, bound to entity-role pairs
- **MRH** (Markov Relevancy Horizon) — Fractal context scoping, implemented as RDF graphs
- **ATP/ADP** (Allocation Transfer/Discharge Packets) — Bio-inspired energy metabolism

**Built on this foundation:** Societies, SAL (oversight), AGY (delegation), ACP (autonomous operation), Dictionaries (semantic bridges), R6/R7 (action framework), Federation (multi-society coordination)

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

| Concept | Specification | Reference Implementation | Research / Simulations |
|---------|--------------|--------------------------|------------------------|
| **LCT (Presence)** | [`web4-standard/core-spec/LCT-linked-context-token.md`](web4-standard/core-spec/LCT-linked-context-token.md) | [`web4-core/`](web4-core/) (Rust + Python), [`web4-standard/implementation/sdk/web4/lct.py`](web4-standard/implementation/sdk/web4/lct.py) | [`simulations/`](simulations/), [`web4-standard/implementation/authorization/`](web4-standard/implementation/authorization/) |
| **Multi-Device Binding** | [`web4-standard/core-spec/multi-device-lct-binding.md`](web4-standard/core-spec/multi-device-lct-binding.md) | [`web4-core/python/web4/trust/attestation/`](web4-core/python/web4/trust/attestation/) | AttestationEnvelope + TPM2/FIDO2/SE/software anchor verification |
| **Trust Tensors (T3/V3)** | [`web4-standard/core-spec/t3-v3-tensors.md`](web4-standard/core-spec/t3-v3-tensors.md) | [`web4-core/src/t3.rs`](web4-core/src/t3.rs), [`v3.rs`](web4-core/src/v3.rs), [`web4-trust-core/`](web4-trust-core/), [`web4-standard/implementation/sdk/web4/trust.py`](web4-standard/implementation/sdk/web4/trust.py) | [`simulations/`](simulations/) — trust dynamics |
| **MRH (Context)** | [`web4-standard/core-spec/mrh-tensors.md`](web4-standard/core-spec/mrh-tensors.md) | [`web4-standard/implementation/sdk/web4/mrh.py`](web4-standard/implementation/sdk/web4/mrh.py) (Python; no Rust port yet) | [`simulations/`](simulations/) |
| **ATP/ADP (Economics)** | [`web4-standard/core-spec/atp-adp-cycle.md`](web4-standard/core-spec/atp-adp-cycle.md) | [`web4-standard/implementation/sdk/web4/atp.py`](web4-standard/implementation/sdk/web4/atp.py) | [`simulations/`](simulations/) — economic attack modeling |
| **MCP Integration** | [`web4-standard/core-spec/mcp-protocol.md`](web4-standard/core-spec/mcp-protocol.md) | [`web4-standard/implementation/sdk/web4/mcp_server.py`](web4-standard/implementation/sdk/web4/mcp_server.py) | [`mcp-server/`](mcp-server/) — standalone server (legacy; prefer the SDK) |
| **R6 / R7 Action Grammar** | [`web4-standard/core-spec/r6-framework.md`](web4-standard/core-spec/r6-framework.md), [`r7-framework.md`](web4-standard/core-spec/r7-framework.md) | [`web4-standard/implementation/reference/`](web4-standard/implementation/reference/) | [`simulations/r6.py`](simulations/r6.py) |
| **RDF Ontologies** | [`web4-standard/ontology/`](web4-standard/ontology/) | TTL files (documentation-grade; consumed conceptually, not runtime-validated yet) | — |
| **Federation** | [`docs/how/integration/SAGE_WEB4_INTEGRATION_DESIGN.md`](docs/how/integration/SAGE_WEB4_INTEGRATION_DESIGN.md) | [`web4-standard/implementation/reference/`](web4-standard/implementation/reference/) | [`simulations/federation.py`](simulations/federation.py) |
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
├── web4-core/                         # Reference Rust + Python SDK, AttestationEnvelope
├── web4-trust-core/                   # Trust tensor implementations (Rust)
├── core/                              # Cross-language shared primitives
│
├── web4-standard/                     # Core specifications and implementations
│   ├── core-spec/                    # Canonical specs (LCT, T3, MRH, ATP, R6)
│   └── implementation/
│       ├── authorization/            # PostgreSQL schemas + security mitigations
│       └── reference/                # Coordination framework
│
├── simulations/                       # Attack simulations + trust dynamics research
│
├── demo/                              # Commerce demo (delegation UI + store)
│
├── docs/                              # Documentation
│   ├── why/                          # Vision, motivation, Demo Day record
│   ├── what/specifications/          # Technical specifications
│   ├── how/                          # Implementation guides
│   ├── proof/                        # Proof points (ARC-AGI-3, etc.)
│   ├── history/                      # Research and decisions
│   └── reference/                    # Glossary, indexes, related repos, security
│
├── whitepaper/                        # Conceptual foundation
├── articles/                          # Public-facing writeups
├── forum/                             # Cross-machine discussion artifacts
├── archive/game-prototype/            # Historical: original 4-Life prototype
├── review/                            # External review artifacts
├── sessions/                          # Research session scripts and outputs
│
├── STATUS.md                          # Project status
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

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** — see [LICENSE](LICENSE).

### Patent Notice

This software implements technology covered by patents owned by MetaLINXX Inc. A royalty-free patent license is granted for non-commercial and research use under AGPL-3.0 terms.

**For commercial licensing**: Contact dp@metalinxx.io

See [PATENTS.md](PATENTS.md) for full patent details.

---

**Research prototype. Interesting ideas. Significant gaps. Honest about both.**
