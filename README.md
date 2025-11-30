# Web4: Trust-Native Distributed Intelligence Architecture

> **Research prototype exploring trust, identity, and authorization for AI agents**

---

## ⚠️ Project Status: Research Prototype

**This is exploratory research, not production software.**

Web4 is investigating trust-native architectures for AI coordination. We have interesting ideas, working prototypes, and significant gaps. See [STATUS.md](STATUS.md) for honest assessment.

---

## 🏗️ Two Development Tracks

Web4 contains **two distinct subsystems** at different maturity levels:

### Track 1: `/game/` - In-Memory Simulation Engine (Research Stage)

**What it is**: A sandbox for exploring trust dynamics, federation, and multi-society coordination.

**Status**: Research prototype with stub cryptography
- In-memory only (no persistence)
- Stub signatures (not real crypto verification)
- MRH-aware policies (v0 heuristics)
- Hardware binding MVP (fingerprint tracking, not TPM/HSM)
- Tested at research scale (100 societies, 1000 agents)

**Documentation**:
- [`game/THREAT_MODEL_GAME.md`](game/THREAT_MODEL_GAME.md) - What's modeled, what's not
- [`game/WEB4_HRM_ALIGNMENT.md`](game/WEB4_HRM_ALIGNMENT.md) - Integration with SAGE federation
- [`SECURITY.md`](SECURITY.md) - Security research status

**Use for**: Exploring ideas, testing trust dynamics, developing intuition

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

### Run the Game Engine

```bash
cd game
python run_two_societies_demo.py      # Federation demo
python run_greedy_treasurer_demo.py   # Policy enforcement demo
python run_hardware_bound_demo.py     # Hardware binding MVP demo
```

---

## 📊 Repository Structure

```
web4/
├── game/                              # Track 1: In-memory simulation
│   ├── engine/                        # Core simulation engine
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
