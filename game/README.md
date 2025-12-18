# Web4 Game: 4-Life Society Simulation

**Last Updated**: December 17, 2025
**Status**: Active research prototype
**Scale**: ~61 engine modules, ~46 demo/test scripts

---

## Overview

The `/game/` directory contains an experimental **society simulation engine** implementing Web4 trust primitives. Named "4-Life" for the emergent, self-organizing nature of the simulation (like Conway's Game of Life, but with trust dynamics).

**What This Is:**
- A fractal sandbox for simulating Web4 societies
- Agents form societies, societies join societies, trust emerges through interaction
- Research testbed for validating Web4 primitives under complex emergent behavior

**What This Isn't:**
- Production infrastructure (no persistence, stub crypto)
- A finished game (no web UI yet)
- A blockchain (all in-memory simulation)

---

## Current Capabilities

### LCT Identity System (4 Phases Complete)

| Phase | Component | Status |
|-------|-----------|--------|
| Phase 1 | Core identity (`lct.py`, `lct_identity.py`) | Complete |
| Phase 2 | Registry (`identity_registry.py`, `identity_consensus.py`) | Complete |
| Phase 3 | Permissions (`lct_permissions.py`, `lct_unified_permissions.py`) | Complete |
| Phase 4 | ATP Integration (`atp_permissions.py`, `identity_stake_system.py`) | Complete |

### Federation & Consensus

- **PBFT Consensus** (`consensus.py`) - Byzantine fault tolerant agreement
- **View Changes** (`view_change.py`) - Leader rotation under failures
- **Signed Gossip** (`signed_epidemic_gossip.py`) - Ed25519 authenticated reputation propagation
- **Federation Delegation** (`signed_federation_delegation.py`) - Cross-society task routing

### Trust & Reputation

- **MRH-Aware Trust** (`mrh_aware_trust.py`) - Context-bounded trust policies
- **Trust Tensors** (`society_trust.py`, `multidimensional_v3.py`) - T3/V3 multi-dimensional scoring
- **Witness Diversity** (`witness_diversity_system.py`) - Anti-collusion attestation requirements
- **Challenge Protocol** (`reputation_challenge_protocol.py`) - Accountability enforcement

### ATP Economics

- **Unified Pricing** (`unified_atp_pricing.py`) - 3D pricing model (modality × location × context)
- **Real Edge Pricing** (`real_edge_atp_pricing.py`) - Calibrated from 200 SAGE task executions
- **Identity Stakes** (`identity_stake_system.py`) - Economic Sybil resistance (1,200-75,000 ATP)
- **Dynamic Premiums** (`dynamic_atp_premiums.py`) - Risk-adjusted costs

### SAGE Integration

- **LCT Integration** (`sage_lct_integration.py`) - Edge device identity patterns
- **Web4 Bridge** (`sage_web4_bridge.py`) - Cross-system coordination

---

## Engine Modules (~61 files)

```
engine/
├── Identity & LCT
│   ├── lct.py, lct_identity.py
│   ├── lct_permissions.py, lct_unified_permissions.py
│   ├── identity_registry.py, identity_consensus.py
│   └── identity_stake_system.py
│
├── Federation & Consensus
│   ├── consensus.py, view_change.py
│   ├── federation_*.py (permissions, reputation, witness)
│   ├── signed_epidemic_gossip.py
│   └── signed_federation_delegation.py
│
├── Trust & Reputation
│   ├── society_trust.py, trust_client.py
│   ├── mrh_aware_trust.py, mrh_profiles.py
│   ├── witness_diversity_system.py
│   └── reputation_challenge_protocol.py
│
├── ATP Economics
│   ├── atp_*.py (ledger, metering, transactions, permissions)
│   ├── unified_atp_pricing.py, real_edge_atp_pricing.py
│   └── dynamic_atp_premiums.py
│
├── Core Simulation
│   ├── models.py, sim_loop.py
│   ├── membership.py, treasury.py
│   ├── policy.py, roles.py
│   └── scenarios.py
│
├── Security Research
│   ├── challenge_evasion_defense.py
│   ├── federation_attack_analysis.py
│   └── integrated_security_test.py
│
└── SAGE Integration
    ├── sage_lct_integration.py
    └── sage_web4_bridge.py
```

---

## Demo Scripts (~46 files)

### Core Demos
```bash
python run_two_societies_demo.py           # Basic federation demo
python run_greedy_treasurer_demo.py        # Policy enforcement demo
python run_lct_e2e_integration_test.py     # Full LCT identity system
```

### Federation & Consensus
```bash
python run_federation_consensus_integration_test.py  # PBFT consensus
python run_multi_society_federation_demo.py          # Multi-society gossip
python run_signed_federation_demo.py                 # Ed25519 signatures
```

### SAGE Integration
```bash
python run_sage_lct_integration_test.py    # Edge device patterns
python run_sage_web4_bridge_demo.py        # Cross-system coordination
```

### Security Testing
```bash
python run_signed_gossip_security_test.py      # Signature verification
python run_witness_diversity_test.py           # Anti-collusion
python run_challenge_protocol_test.py          # Accountability
python run_production_scale_test.py            # 100 societies, 1000 agents
```

---

## Test Results (Research Scale)

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Signature Verification | >50k/s | 88k/s | Passed |
| Gossip Propagation (100 societies) | <10s | <5s | Passed |
| Witness Selection (500 LCTs) | <200ms | <100ms | Passed |
| Memory (1000 agents) | <4GB | <2GB | Passed |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Web4 Game Engine                     │
├─────────────────────────────────────────────────────────┤
│  Agents (LCTs)          Societies (LCTs)                │
│  ├─ Trust Tensors       ├─ Treasury (ATP)               │
│  ├─ Capabilities        ├─ Membership                   │
│  ├─ ATP Budget          ├─ Policies                     │
│  └─ MRH Profile         └─ Roles                        │
├─────────────────────────────────────────────────────────┤
│  Federation Layer                                        │
│  ├─ Signed Gossip (Ed25519)                             │
│  ├─ PBFT Consensus                                      │
│  ├─ Witness Diversity (≥3 societies)                    │
│  └─ Challenge-Response Protocol                         │
├─────────────────────────────────────────────────────────┤
│  Economics Layer                                         │
│  ├─ ATP Metering & Pricing                              │
│  ├─ Identity Stakes (Sybil resistance)                  │
│  └─ Cross-Society Reputation                            │
└─────────────────────────────────────────────────────────┘
```

---

## What's Missing

- **Persistence**: All state is in-memory (no database yet)
- **Real Crypto**: Uses stub signatures in some places (not production crypto)
- **Web UI**: Planned but not built
- **Real Adversaries**: All testing is synthetic

---

## Related Documentation

- [THREAT_MODEL_GAME.md](THREAT_MODEL_GAME.md) - Security assumptions and gaps
- [WEB4_HRM_ALIGNMENT.md](WEB4_HRM_ALIGNMENT.md) - SAGE federation integration spec
- [../SECURITY.md](../SECURITY.md) - Overall security research status
- [../THREAT_MODEL.md](../THREAT_MODEL.md) - Formal threat model

---

## Research Context

This simulation was developed through autonomous AI research sessions with human oversight:

- **Sessions #80-85**: Federation security patterns (~12,600 lines)
- **LCT Phases 1-4**: Identity system implementation
- **Scale Testing**: 100 societies, 1000 agents

**Goal**: Validate Web4 primitives under complex emergent behavior, reveal gaps in specs, provide interactive demonstration.

---

## Quick Start

```bash
cd game

# Run basic demo
python run_two_societies_demo.py

# Run full LCT integration test
python run_lct_e2e_integration_test.py

# Run federation consensus test
python run_federation_consensus_integration_test.py

# Run scale test (100 societies)
python run_production_scale_test.py
```

---

**Status**: Active research prototype - substantial implementation, in-memory only, no production deployment.
