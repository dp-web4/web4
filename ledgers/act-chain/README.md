# ACT Chain

> **Migration Notice**: The ACT distributed ledger implementation has been consolidated into the Web4 repository. The original Go implementation remains in the `ACT` repository for historical reference, but this is now the canonical documentation location.

## Overview

ACT (Artificial Communication Transport) is a Cosmos SDK-based distributed ledger implementing the Web4 protocol. It provides:

- **LCT Management**: Linked Context Token identity system
- **Energy Economy**: ATP/ADP allocation and discharge mechanics
- **Trust Tensors**: T3/V3 multi-dimensional trust calculations
- **Context Boundaries**: Markov Relevancy Horizon (MRH) scoping

## Architecture

Built on:
- **Cosmos SDK v0.53.x** - Modular blockchain framework
- **CometBFT** (formerly Tendermint) - Byzantine fault-tolerant consensus
- **Chain ID**: `act-web4`

### Module Structure

```
x/
├── lctmanager/       # Linked Context Token management
├── energycycle/      # ATP/ADP energy economy
├── trusttensor/      # T3/V3 trust calculations
├── mrh/              # Markov Relevancy Horizon
├── pairing/          # Device pairing authentication
├── pairingqueue/     # Pairing queue management
├── componentregistry/ # Component tracking
└── societytodo/      # Society task delegation
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed module documentation.

## Python Bridge

The `bridge/` directory contains Python integration code for interacting with the ACT chain:

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
print(f"Connected: {status['connected']}")
print(f"Block: {status['latest_block']}")

# Submit transaction
result = blockchain.submit_transaction(
    transaction={
        'type': 'atp_discharge',
        'amount': 100,
        'reason': 'work_completed'
    },
    signer_lct='lct:web4:alice'
)
```

## Endpoints

When running, ACT exposes:

| Service | URL | Purpose |
|---------|-----|---------|
| Tendermint RPC | `http://localhost:26657` | Transaction submission |
| REST API | `http://localhost:1317` | Query interface |
| gRPC | `http://localhost:9090` | High-performance queries |

## Relationship to Web4

ACT implements the **Root Chain** layer of Web4's fractal chain architecture:

```
ACT Chain (Root - Permanent)
    ↑
    │ [witness marks from Stem chains]
    │
Stem Chains (Team Memory)
    ↑
    │ [consolidated patterns]
    │
Leaf Chains (Session Records)
```

ACT is used for:
- Permanent LCT registrations
- Organizational charters
- Cross-federation agreements
- Audit seals

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

## Development

### Building (Go)

```bash
cd /path/to/ACT/implementation/ledger
ignite chain build --skip-proto
```

### Running

```bash
racecar-webd init mynode --chain-id act-web4
racecar-webd start --api.enable --grpc.enable
```

### Testing (Python Bridge)

```bash
cd bridge/
python -m pytest tests/
```

## Migration Notes

The ACT Go implementation remains in the `ACT` repository. This consolidation:

1. **Documents** the architecture in Web4's canonical location
2. **Preserves** Python bridge code for integration
3. **Clarifies** ACT's role as Web4's root chain implementation

For Go module development, continue using the `ACT` repository.

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed module documentation
- [spec/](spec/) - Module specifications
- [bridge/](bridge/) - Python integration code
- [../spec/fractal-chains/root-chains.md](../spec/fractal-chains/root-chains.md) - Root chain specification
