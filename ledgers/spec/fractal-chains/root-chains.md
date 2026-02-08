# Root Chains

**Time Scale**: Permanent
**Purpose**: Long-term crystallized wisdom and immutable truth
**ATP Cost**: 100+ units
**Verification**: Global consensus

## Overview

Root chains are the permanent record layer - the immutable foundation of the Web4 trust hierarchy. Like tree roots that anchor and sustain the entire organism, these chains hold identity anchors, constitutional rules, and critical agreements that must never be forgotten.

## Characteristics

- **Global consensus**: Full distributed agreement required
- **Immutable record**: No modification or deletion possible
- **Maximum verification**: Multiple witness requirements
- **Cross-chain anchoring**: Verification across multiple root chains

## Use Cases

| Domain | Example |
|--------|---------|
| Identity | LCT registrations, permanent identifiers |
| Governance | Organizational charters, constitutional rules |
| Credentials | Verified professional certifications |
| Audit | Historical compliance records |

## Implementation Details

### Entry Format

```json
{
  "entry_id": "root:lct:registration:alice-2026",
  "timestamp": "2026-02-08T14:00:00Z",
  "prev_hash": "sha256:mno012...",
  "content": {
    "type": "lct_registration",
    "lct_id": "lct:web4:alice",
    "public_key": "ed25519:pub123...",
    "binding": {
      "type": "hardware",
      "device_attestation": "tpm:att456..."
    },
    "metadata": {
      "name": "Alice",
      "created": "2026-02-08T14:00:00Z"
    }
  },
  "witnesses": [
    {"lct": "lct:web4:genesis:council", "signature": "sig1...", "timestamp": "..."},
    {"lct": "lct:web4:genesis:trust_validator", "signature": "sig2...", "timestamp": "..."},
    {"lct": "lct:web4:genesis:federation_bridge", "signature": "sig3...", "timestamp": "..."}
  ],
  "content_hash": "sha256:pqr345...",
  "merkle_proof": {
    "root": "sha256:global_root...",
    "path": ["sha256:a...", "sha256:b...", "sha256:c..."]
  }
}
```

### Storage Architecture

Root chains use distributed consensus:

```python
class RootChain:
    """Permanent distributed ledger."""

    def __init__(self, consensus_nodes: List[str]):
        self.nodes = consensus_nodes
        self.local_db = self._init_local_store()

    async def propose(self, content: dict) -> str:
        """Propose entry for global consensus."""
        proposal = {
            'entry_id': self.generate_id(),
            'content': content,
            'proposer': self.local_lct,
            'timestamp': datetime.now().isoformat()
        }

        # Collect signatures from consensus nodes
        signatures = await self._collect_signatures(proposal)

        if len(signatures) >= self.consensus_threshold:
            return await self._commit(proposal, signatures)
        else:
            raise InsufficientConsensus(signatures)
```

### Consensus Requirements

```python
ENTRY_TYPE_REQUIREMENTS = {
    'lct_registration': {
        'min_witnesses': 3,
        'required_roles': ['genesis:council'],
        'atp_cost': 100
    },
    'charter_amendment': {
        'min_witnesses': 5,
        'required_roles': ['genesis:council', 'genesis:trust_validator'],
        'atp_cost': 500,
        'voting_period': timedelta(days=7)
    },
    'credential_issuance': {
        'min_witnesses': 2,
        'required_roles': ['credential:issuer'],
        'atp_cost': 150
    },
    'audit_seal': {
        'min_witnesses': 3,
        'required_roles': ['audit:authority'],
        'atp_cost': 200
    }
}
```

### Cross-Chain Anchoring

Root chains can anchor to external systems:

```python
def create_anchor(self, external_chain: str, external_tx: str):
    """Create cross-chain anchor for verification."""
    return {
        'type': 'cross_chain_anchor',
        'external_chain': external_chain,  # e.g., 'solana', 'ethereum'
        'external_tx': external_tx,
        'web4_entry': self.latest_entry_id,
        'timestamp': datetime.now().isoformat(),
        'merkle_root': self.compute_merkle_root()
    }
```

**Supported External Chains**:
- Solana (low-cost, fast finality)
- Ethereum (high security, wide recognition)
- Bitcoin (maximum immutability)

Note: We refer to these as "ledgers" in user-facing documentation, not "blockchains".

## Retention Policy

- **Lifetime**: Permanent (no expiration)
- **Deletion**: Impossible by design
- **Amendment**: New entries supersede, old remain
- **Archival**: Replicated across multiple nodes

### Immutability Guarantees

```python
def verify_immutability(entry_id: str) -> ImmutabilityProof:
    """Generate proof that entry hasn't been modified."""
    return {
        'entry_id': entry_id,
        'original_hash': entry['content_hash'],
        'merkle_proof': get_merkle_proof(entry_id),
        'witness_signatures': entry['witnesses'],
        'cross_chain_anchors': get_anchors(entry_id),
        'verification_timestamp': datetime.now().isoformat()
    }
```

## Energy Considerations

| Operation | ATP Cost |
|-----------|----------|
| LCT registration | 100 |
| Charter amendment | 500 |
| Credential issuance | 150 |
| Audit seal | 200 |
| Cross-chain anchor | 50 |
| Merkle proof | 10 |

## Node Requirements

Root chain nodes must meet requirements:

```yaml
node_requirements:
  hardware:
    storage: 1TB+ SSD
    memory: 16GB+ RAM
    uptime: 99.9%

  trust:
    t3_minimum: 0.8
    witness_history: 1000+ validations
    no_violations: true

  governance:
    stake: 10000 ATP minimum
    slashing: enabled
    voting_power: proportional to stake * t3
```

## Federation

Root chains federate across organizations:

```python
async def federate(self, peer_federation: str):
    """Establish federation with peer root chain."""
    # Exchange genesis information
    peer_genesis = await peer.get_genesis()
    my_genesis = self.get_genesis()

    # Create mutual witness relationship
    federation_entry = {
        'type': 'federation_establishment',
        'local_genesis': my_genesis['entry_id'],
        'peer_genesis': peer_genesis['entry_id'],
        'terms': {
            'witness_reciprocity': True,
            'anchor_sharing': True,
            'dispute_resolution': 'council_arbitration'
        }
    }

    return await self.propose(federation_entry)
```

## Relationship to Other Chains

```
Root Chain (this level - PERMANENT)
    ↑
    │ [critical patterns only]
    │
Stem Chains (minutes-hours)
    ↑
    │ [consolidated patterns]
    │
Leaf Chains (seconds-minutes)
    ↑
    │ [selective events]
    │
Compost Chains (ms-seconds)
```

## Query Interface

```python
# Query by LCT
entries = root.query(lct="lct:web4:alice")

# Query by type
registrations = root.query(type="lct_registration", since="2026-01-01")

# Verify entry
proof = root.verify(entry_id="root:lct:registration:alice-2026")

# Get Merkle proof
merkle = root.merkle_proof(entry_id, depth=10)
```

## Best Practices

1. **Be selective**: Only truly permanent data
2. **Verify thoroughly**: Multiple witnesses required
3. **Anchor externally**: Cross-chain for maximum assurance
4. **Federate**: Connect to peer organizations

## See Also

- [README.md](README.md) - Fractal chain overview
- [stem-chains.md](stem-chains.md) - Previous level
- [../witness-protocol/](../witness-protocol/) - Consensus witnessing
- [../../act-chain/](../../act-chain/) - ACT distributed ledger implementation
