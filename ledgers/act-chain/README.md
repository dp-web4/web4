# ACT Chain

## Fully Operational Implementation

ACT (Artificial Communication Transport) is a **production-ready distributed ledger** implementing the Web4 protocol. This is not theoretical - the complete implementation is available and has been tested in federation scenarios.

**Source Code**: [github.com/dp-web4/ACT](https://github.com/dp-web4/ACT/tree/main/implementation/ledger)

### Implementation Stats

| Metric | Value |
|--------|-------|
| Go source files | 273 |
| Lines of code | ~81,000 |
| Cosmos SDK modules | 8 |
| Status | Operational |

## Overview

ACT provides the **Root Chain** layer of Web4's fractal chain architecture - the permanent, globally-consensus layer for immutable records:

- **LCT Management**: Linked Context Token identity system
- **Energy Economy**: ATP/ADP allocation and discharge mechanics
- **Trust Tensors**: T3/V3 multi-dimensional trust calculations
- **Context Boundaries**: Markov Relevancy Horizon (MRH) scoping

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Cosmos SDK | v0.53.x | Modular blockchain framework |
| CometBFT | v0.38.x | Byzantine fault-tolerant consensus |
| Go | 1.24+ | Implementation language |
| Ignite CLI | v29.4+ | Build tooling |

**Chain ID**: `act-web4`

## Module Structure

The implementation includes 8 specialized modules:

```
x/
├── lctmanager/        # Linked Context Token management
├── energycycle/       # ATP/ADP energy economy
├── trusttensor/       # T3/V3 trust calculations
├── mrh/               # Markov Relevancy Horizon
├── pairing/           # Device pairing authentication
├── pairingqueue/      # Pairing queue management
├── componentregistry/ # Component tracking
└── societytodo/       # Society task delegation
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed module documentation.

## Running ACT

### Prerequisites

```bash
# Install Go 1.24+
# Install Ignite CLI
curl https://get.ignite.com/cli! | bash
```

### Build and Run

```bash
# Clone the repository
git clone https://github.com/dp-web4/ACT.git
cd ACT/implementation/ledger

# Build
ignite chain build --skip-proto

# Initialize
racecar-webd init mynode --chain-id act-web4

# Add test accounts
racecar-webd keys add alice --keyring-backend test
racecar-webd genesis add-genesis-account alice 1000000000stake --keyring-backend test

# Start
racecar-webd start --api.enable --grpc.enable
```

### Endpoints

When running, ACT exposes:

| Service | URL | Purpose |
|---------|-----|---------|
| Tendermint RPC | `http://localhost:26657` | Transaction submission |
| REST API | `http://localhost:1317` | Query interface |
| gRPC | `http://localhost:9090` | High-performance queries |
| Token Faucet | `http://localhost:4500` | Test tokens |

## Python Bridge

The `bridge/` directory contains Python integration code:

| File | Purpose |
|------|---------|
| `genesis_blockchain.py` | Cosmos SDK RPC integration |
| `genesis_witness.py` | Witness attestation system |
| `genesis_atp_adp_manager.py` | Energy cycle management |
| `genesis_crypto.py` | Ed25519 transaction signing |

### Quick Start

```python
from bridge.genesis_blockchain import GenesisBlockchainIntegration

# Initialize
blockchain = GenesisBlockchainIntegration()

# Check status
status = blockchain.check_blockchain_status()
if status['connected']:
    print(f"Block height: {status['latest_block']}")

# Submit witnessed transaction
result = blockchain.submit_transaction(
    transaction={
        'type': 'atp_discharge',
        'amount': 100,
        'reason': 'work_completed'
    },
    signer_lct='lct:web4:alice'
)
```

## Relationship to Web4

ACT implements the **Root Chain** layer of Web4's fractal chain architecture:

```
ACT Chain (Root - Permanent)     ← YOU ARE HERE
    ↑
    │ [witness marks from Stem chains]
    │
Stem Chains (Team Memory)
    ↑
    │ [consolidated patterns]
    │
Leaf Chains (Session Records)
    ↑
    │ [selective events]
    │
Compost Chains (Ephemeral)
```

**Root chain responsibilities**:
- Permanent LCT registrations
- Organizational charters
- Cross-federation agreements
- Audit seals
- Constitutional rules

## Genesis Entities

Initial allocation (100,000 ATP federation pool):

| Entity | Initial ATP | Daily Recharge | Role |
|--------|-------------|----------------|------|
| Genesis Queen | 30,000 | 3,000 | Federation lead |
| Genesis Council | 20,000 | 2,000 | Governance |
| Coherence Guru | 15,000 | 1,500 | Quality assurance |
| Federation Bridge | 10,000 | 1,000 | Cross-federation |
| Synchronism Oracle | 10,000 | 1,000 | Timing authority |
| Emergency Response | 5,000 | 500 | Crisis handling |

## Federation Testing

ACT has been tested in multi-node federation scenarios:

- **Multi-machine deployment** (Legion, Thor, Sprout nodes)
- **Cross-platform witnessing** between nodes
- **Proposal and voting** mechanisms
- **ATP transfer** between entities
- **Trust tensor propagation**

See the [ACT repository](https://github.com/dp-web4/ACT/tree/main/implementation/ledger) for federation documentation.

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed module documentation
- [bridge/](bridge/) - Python integration code
- [../spec/fractal-chains/root-chains.md](../spec/fractal-chains/root-chains.md) - Root chain specification
- [ACT Repository](https://github.com/dp-web4/ACT) - Full source code
