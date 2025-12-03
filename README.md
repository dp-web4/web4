# Web4: Trust-Native Distributed Intelligence Architecture

> **Research prototype exploring trust, identity, and authorization for AI agents**

---

## ⚠️ Project Status: Research Prototype

**This is exploratory research, not production software.**

Web4 is investigating trust-native architectures for AI coordination. We have interesting ideas, working prototypes, and significant gaps. See [STATUS.md](STATUS.md) for honest assessment.

---

## 🏗️ Two Development Tracks

Web4 contains **two distinct subsystems** at different maturity levels:

### Track 1: `/game/` - 4-Life Society Simulation (Research Stage)

**What it is**: A fractal sandbox for simulating Web4 societies - agents form societies, societies join societies, trust emerges through interaction. Named "4-Life" for the emergent, self-organizing nature of the simulation (like Conway's Game of Life, but with trust dynamics).

**Goal**: Validate Web4 primitives under complex emergent behavior, reveal gaps in specs, and provide interactive demonstration for humans and AI agents.

**Status**: Active research prototype (~40 engine modules, ~60 demo scripts)
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

---

## 📊 Key Documentation

| Document | What It Covers |
|----------|----------------|
| **[STATUS.md](STATUS.md)** | Honest assessment - what exists, what works, what's missing |
| **[SECURITY.md](SECURITY.md)** | Security research status and gaps |
| **[THREAT_MODEL.md](THREAT_MODEL.md)** | Formal threat model for the overall system |
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
│   ├── engine/                        # ~40 modules (LCT, federation, consensus, ATP, etc.)
│   ├── run_*.py                       # ~60 demo/test scripts
│   ├── README.md                      # Game overview and design
│   ├── THREAT_MODEL_GAME.md          # Security assumptions
│   └── WEB4_HRM_ALIGNMENT.md         # SAGE integration spec
│
├── web4-standard/implementation/      # Track 2: DB-backed authorization
│   └── authorization/                 # PostgreSQL schemas & tests
│       ├── schema*.sql               # Security mitigations
│       ├── *_engine.py               # Authorization logic
│       └── test_*.py                 # Attack resistance tests
│
├── demo/                              # Track 3: Commerce demo
│   ├── store/                        # Demo e-commerce
│   └── delegation-ui/                # User management UI
│
├── whitepaper/                        # Conceptual foundation
├── STATUS.md                          # Honest project status
├── SECURITY.md                        # Security research status
└── THREAT_MODEL.md                    # System threat model
```

---

## 🤝 Related Projects

- **[HRM/SAGE](https://github.com/dp-web4/HRM)** - Edge AI consciousness kernel with federation
- **[Synchronism](https://github.com/dp-web4/Synchronism)** - Theoretical physics framework (MRH, coherence)
- **[Memory](https://github.com/dp-web4/memory)** - Distributed memory and witnessing

---

## 📖 Whitepaper

The Web4 whitepaper provides the conceptual foundation:

- **[Web Version](https://dp-web4.github.io/web4/whitepaper-web/)**
- **[PDF Version](https://dp-web4.github.io/web4/whitepaper-web/WEB4_Whitepaper.pdf)**

Key concepts: LCTs, MRH, Trust Tensors, ATP, Federation, Dictionaries

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

**Research prototype. Interesting ideas. Significant gaps. Honest about both.**
