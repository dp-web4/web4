# Web4: Trust-Native Distributed Intelligence Architecture

<!-- SUMMARIZER BLOCK: Consistent headers for AI-to-human relay -->
## Status Snapshot (2026-01-13)

### Highlights
- **Sessions 176-180**: Causality verification, information theory, consciousness-aware attestation integrated
- **Multi-device LCT binding spec**: Hardware anchor protocol for phone SE, FIDO2, TPM (Session 181)
- **Existence threshold detection**: Session 180 adds C > 0 checks for entity presence
- **ATP economics coherence**: Phase transition detector for trust dynamics
- **Federation reputation DB**: Per-node reputation tracking (Legion, Thor, Peer1, Peer2)

### Validations
- EP closed-loop simulation: 3+ lives with carry-forward state working
- Federation patterns: 1000+ patterns in corpus, validated on edge (Jetson)
- Trust tensor calculations: T3 composite scores stable across simulation runs

### Risks / Gaps
- **P0 Blocker (spec complete)**: Hardware binding spec complete - [`multi-device-lct-binding.md`](web4-standard/core-spec/multi-device-lct-binding.md) - implementation pending
- No formal threat model or adversarial testing
- Consciousness-aware attestation is theoretical (no empirical grounding yet)

### Open Questions
- How to implement hardware-bound keys without TPM on all platforms?
- Can trust dynamics predict cascade failures before they occur?
- What's the minimal viable Web4 for production pilot?

### Next
- Multi-device binding implementation (iOS/Android/WebAuthn reference)
- Integration with HRM nine-domain coherence framework
- Pattern corpus browser from 4-life for EP visualization

---

> **Research prototype exploring trust, identity, and authorization for AI agents**

---

## 🎯 Vision

**Web4 formalizes trust as a first-class primitive for distributed AI collaboration and governance—not merely data exchange.**

The internet evolved from documents (Web1) to applications (Web2) to ownership (Web3). Web4 proposes the next layer: **verifiable trust relationships** between humans, AI agents, and services that enable meaningful coordination without central control.

### About "Web4"

Like Web1, Web2, and Web3, "Web4" is a generational label describing capabilities needed for the agentic AI era—not a single protocol or product. Many projects are tackling various aspects of this challenge.

**This project suite** focuses specifically on **trust infrastructure** for agent-agent and agent-human interactions: how agents establish identity, build reputation, delegate authority, and coordinate safely across organizational boundaries.

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
| **Coordination** | Smart contracts | Federated societies with emergent governance |
| **Focus** | Asset ownership | Agent behavior and intent |

### What Problems This Could Address

- **AI Agent Accountability**: Every action traceable to an identity with reputation at stake
- **Cross-Platform Coordination**: Agents from different systems interoperating through shared trust protocols
- **Graduated Authorization**: Not just "allowed/denied" but nuanced trust based on context, history, and stakes
- **Emergent Governance**: Societies that self-organize rules rather than requiring top-down control

---

## 📚 Start Here (Learning Path)

| Step | Document | What You'll Learn |
|------|----------|-------------------|
| 1 | **[STATUS.md](STATUS.md)** | Honest assessment: what exists, what works, what's missing |
| 2 | **[docs/GLOSSARY.md](docs/GLOSSARY.md)** | Quick reference for all Web4 terminology |
| 3 | **[whitepaper/](whitepaper/)** | Conceptual foundation: LCTs, trust tensors, MRH, R6 framework |
| 4 | **[game/README.md](game/README.md)** | Interactive simulation of Web4 societies |
| 5 | **[SECURITY.md](SECURITY.md)** | Security research status and known gaps |
| 6 | **[THREAT_MODEL.md](docs/security/THREAT_MODEL.md)** | What we're defending against |
| 7 | **[docs/LCT_DOCUMENTATION_INDEX.md](docs/LCT_DOCUMENTATION_INDEX.md)** | Index of all LCT-related documentation |

---

## ⚠️ Project Status: Research Prototype

**This is exploratory research, not production software.**

Web4 is investigating trust-native architectures for AI coordination. We have interesting ideas, working prototypes, and significant gaps. See [STATUS.md](STATUS.md) for honest assessment.

---

## 🏗️ Four Development Tracks

Web4 contains **four development tracks** at different maturity levels:

### Track 1: `/game/` - 4-Life Society Simulation (Research Stage)

**What it is**: A fractal sandbox for simulating Web4 societies - agents form societies, societies join societies, trust emerges through interaction. Named "4-Life" for the emergent, self-organizing nature of the simulation (like Conway's Game of Life, but with trust dynamics).

**Goal**: Validate Web4 primitives under complex emergent behavior, reveal gaps in specs, and provide interactive demonstration for humans and AI agents.

**Status**: Active research prototype (~60 engine modules, ~45 demo scripts)
- In-memory simulation (no persistence yet)
- Stub cryptography (not production crypto)
- LCT identity system (4 phases complete: identity, registry, permissions, ATP integration)
- Federation with PBFT consensus and view changes
- MRH-aware trust policies (v0 heuristics)
- Tested at research scale (100 societies, 1000 agents)

**What Works**:
- Agents with LCTs, trust tensors (T3/V3), capabilities, and ATP budgets
- Societies with treasuries, membership, policies, and roles
- Federation between societies with signed gossip and consensus
- Insurance pools and cross-society reputation
- SAGE edge device integration patterns

**What's Missing**:
- Persistence layer (all in-memory)
- Real cryptographic verification
- Production-grade security hardening
- Web UI (planned, not built)

**Documentation**:
- [`game/README.md`](game/README.md) - Full game overview and design
- [`game/THREAT_MODEL_GAME.md`](game/THREAT_MODEL_GAME.md) - What's modeled, what's not
- [`game/WEB4_HRM_ALIGNMENT.md`](game/WEB4_HRM_ALIGNMENT.md) - Integration with SAGE federation
- [`SECURITY.md`](SECURITY.md) - Security research status

**Use for**: Exploring trust dynamics, testing federation patterns, developing intuition about emergent behavior

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
- LCT Unified Identity Specification

**Key Components**:

| Component | Purpose | Status |
|-----------|---------|--------|
| Phase 2a Epistemic Coordinator | Runtime epistemic state tracking | Validated |
| Phase 2b Integrated Coordinator | Epistemic + pattern learning | Validated |
| Phase 2c Circadian Coordinator | Temporal/phase-aware decisions | Validated |
| Phase 2d Adaptive Coordinator | EM-state modulation | Validated |
| Pattern Exchange Protocol | Cross-system learning transfer | Operational |
| LCT Identity Specification | Unified identity format | v1.0.0 draft |

**Validation Results** (Dec 2025):
- 76% prediction validation (13 of 17 predictions confirmed)
- +386% efficiency improvement demonstrated
- Long-duration testing (1000+ cycles)

**Key Files**:
- `web4_phase2b_integrated_coordinator.py` - Combined epistemic + learning
- `temporal_pattern_exchange.py` - Phase-aware pattern transfer
- `universal_pattern_schema.py` - Cross-system pattern format
- `LCT_UNIFIED_IDENTITY_SPECIFICATION.md` - Identity standard (in `/docs/`)

**Use for**: Coordination research, SAGE integration, cross-system pattern transfer

---

## 📊 Key Documentation

| Document | What It Covers |
|----------|----------------|
| **[STATUS.md](STATUS.md)** | Honest assessment - what exists, what works, what's missing |
| **[SECURITY.md](SECURITY.md)** | Security research status and gaps |
| **[THREAT_MODEL.md](docs/security/THREAT_MODEL.md)** | Formal threat model for the overall system |
| **[game/THREAT_MODEL_GAME.md](game/THREAT_MODEL_GAME.md)** | Threat model specific to `/game/` engine |
| **[Whitepaper](whitepaper/)** | Conceptual foundation (LCTs, trust, MRH) |

**Start here**: [STATUS.md](STATUS.md) for fair evaluation criteria

---

## What Is Web4?

Web4 is a **research architecture** exploring how to safely coordinate AI agents with:

- **Linked Context Tokens (LCTs)** - Unforgeable identity anchored to hardware
- **Trust Tensors (T3)** - Multi-dimensional trust scoring
- **Markov Relevancy Horizons (MRH)** - Context boundaries for entities
- **ATP (Adaptive Trust Points)** - Energy-based resource allocation
- **Federation** - Multi-society coordination with signed gossip

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

| Concept | Specification | Implementation | Demo |
|---------|--------------|----------------|------|
| **LCT (Identity)** | [`web4-standard/core-spec/LCT-linked-context-token.md`](web4-standard/core-spec/LCT-linked-context-token.md) | [`game/engine/lct.py`](game/engine/lct.py), [`lct_identity.py`](game/engine/lct_identity.py) | `run_lct_e2e_integration_test.py` |
| **Multi-Device Binding** | [`web4-standard/core-spec/multi-device-lct-binding.md`](web4-standard/core-spec/multi-device-lct-binding.md) | (spec only - implementation pending) | - |
| **Trust Tensors (T3/V3)** | [`web4-standard/core-spec/t3-v3-tensors.md`](web4-standard/core-spec/t3-v3-tensors.md) | [`game/engine/society_trust.py`](game/engine/society_trust.py) | `run_two_societies_demo.py` |
| **MRH (Context)** | [`web4-standard/core-spec/mrh-tensors.md`](web4-standard/core-spec/mrh-tensors.md) | [`game/engine/mrh_aware_trust.py`](game/engine/mrh_aware_trust.py) | - |
| **ATP (Economics)** | [`web4-standard/core-spec/atp-adp-cycle.md`](web4-standard/core-spec/atp-adp-cycle.md) | [`game/engine/atp_metering.py`](game/engine/atp_metering.py), [`unified_atp_pricing.py`](game/engine/unified_atp_pricing.py) | `run_atp_integration_test.py` |
| **Federation** | [`docs/SAGE_WEB4_INTEGRATION_DESIGN.md`](docs/SAGE_WEB4_INTEGRATION_DESIGN.md) | [`game/engine/signed_epidemic_gossip.py`](game/engine/signed_epidemic_gossip.py) | `run_federation_consensus_integration_test.py` |
| **Societies** | [`web4-standard/core-spec/SOCIETY_SPECIFICATION.md`](web4-standard/core-spec/SOCIETY_SPECIFICATION.md) | [`game/engine/membership.py`](game/engine/membership.py), [`treasury.py`](game/engine/treasury.py) | `run_greedy_treasurer_demo.py` |
| **Authorization** | [`web4-standard/core-spec/security-framework.md`](web4-standard/core-spec/security-framework.md) | [`web4-standard/implementation/authorization/`](web4-standard/implementation/authorization/) | `demo/` |
| **Coordination** | [`docs/LCT_UNIFIED_IDENTITY_SPECIFICATION.md`](docs/LCT_UNIFIED_IDENTITY_SPECIFICATION.md) | [`web4-standard/implementation/reference/web4_phase2b_integrated_coordinator.py`](web4-standard/implementation/reference/web4_phase2b_integrated_coordinator.py) | - |

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

### Run the 4-Life Game Engine

```bash
cd game

# Core demos
python run_two_societies_demo.py           # Basic federation demo
python run_greedy_treasurer_demo.py        # Policy enforcement demo
python run_lct_e2e_integration_test.py     # Full LCT identity system

# Federation & consensus
python run_federation_consensus_integration_test.py  # PBFT consensus
python run_multi_society_federation_demo.py          # Multi-society gossip

# SAGE integration
python run_sage_lct_integration_test.py    # Edge device patterns
```

---

## 📊 Repository Structure

```
web4/
├── game/                              # Track 1: 4-Life Society Simulation
│   ├── engine/                        # ~60 modules (LCT, federation, consensus, ATP, etc.)
│   ├── run_*.py                       # ~45 demo/test scripts
│   ├── README.md                      # Game overview and design
│   ├── THREAT_MODEL_GAME.md          # Security assumptions
│   └── WEB4_HRM_ALIGNMENT.md         # SAGE integration spec
│
├── web4-standard/implementation/      # Tracks 2 & 4
│   ├── authorization/                 # Track 2: PostgreSQL schemas & tests
│   │   ├── schema*.sql               # Security mitigations
│   │   ├── *_engine.py               # Authorization logic
│   │   └── test_*.py                 # Attack resistance tests
│   └── reference/                     # Track 4: Coordination framework (~25k lines)
│       ├── web4_phase2*_coordinator.py  # Phase 2a-2d coordinators
│       ├── pattern_exchange_protocol.py # Cross-system learning
│       ├── universal_pattern_schema.py  # Pattern format standard
│       ├── temporal_pattern_exchange.py # Phase-tagged transfer
│       └── test_*.py                    # Validation tests
│
├── demo/                              # Track 3: Commerce demo
│   ├── store/                        # Demo e-commerce
│   └── delegation-ui/                # User management UI
│
├── docs/                              # Specifications
│   └── LCT_UNIFIED_IDENTITY_SPECIFICATION.md  # Cross-system identity
│
├── whitepaper/                        # Conceptual foundation
├── STATUS.md                          # Honest project status
├── SECURITY.md                        # Security research status
└── docs/security/THREAT_MODEL.md      # System threat model
```

---

## 🤝 Related Projects

- **[HRM/SAGE](https://github.com/dp-web4/HRM)** - Edge AI kernel with MoE expert selection and trust-based routing
- **[ACT](https://github.com/dp-web4/act)** - Cosmos SDK blockchain for ATP tokens and LCT identity registry
- **[Synchronism](https://github.com/dp-web4/Synchronism)** - Theoretical physics framework (MRH, coherence)
- **[Memory](https://github.com/dp-web4/memory)** - Distributed memory and witnessing

### Cross-Project Integration

Web4 integrates with SAGE (neural MoE) and ACT (blockchain) via:
- **Unified LCT Identity**: `lct://{component}:{instance}:{role}@{network}`
- **ATP Resource Allocation**: Synchronized between blockchain and edge systems
- **Bidirectional Pattern Exchange**: Coordination patterns transfer between domains
- **Trust Tensor Synchronization**: Trust scores flow across system boundaries

See [`docs/LCT_UNIFIED_IDENTITY_SPECIFICATION.md`](docs/LCT_UNIFIED_IDENTITY_SPECIFICATION.md) for the identity standard.

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
