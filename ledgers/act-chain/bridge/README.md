# ACT Chain Python Bridge

Python integration layer for interacting with the ACT distributed ledger.

## Files

| File | Lines | Purpose |
|------|-------|---------|
| `genesis_blockchain.py` | ~600 | Cosmos SDK RPC integration |
| `genesis_witness.py` | ~400 | Witness attestation system |
| `genesis_atp_adp_manager.py` | ~550 | ATP/ADP energy management |
| `genesis_crypto.py` | ~400 | Ed25519 cryptographic operations |

## Provenance

These files are copied from:
- `ACT/implementation/ledger/genesis_*.py`

The ACT repository remains the source for Go blockchain code, but these Python bridge files are now canonically maintained here.

## Quick Start

### Blockchain Integration

```python
from genesis_blockchain import GenesisBlockchainIntegration

# Initialize
blockchain = GenesisBlockchainIntegration()

# Check if chain is running
status = blockchain.check_blockchain_status()
if status['connected']:
    print(f"Block height: {status['latest_block']}")

# Submit witnessed transaction
result = blockchain.submit_transaction(
    transaction={
        'type': 'atp_discharge',
        'from_lct': 'lct:web4:alice',
        'amount': 100,
        'reason': 'code_review'
    },
    signer_lct='lct:web4:alice'
)
```

### Energy Management

```python
from genesis_atp_adp_manager import GenesisATPManager

# Initialize
atp = GenesisATPManager()

# Check balance
balance = atp.get_balance('lct:web4:alice')
print(f"ATP: {balance['atp']}, ADP: {balance['adp']}")

# Discharge ATP (spend)
atp.discharge(
    lct_id='lct:web4:alice',
    amount=50,
    reason='tool_execution'
)

# Recharge ADP (earn)
atp.recharge(
    lct_id='lct:web4:alice',
    amount=30,
    value_proof={'work': 'completed', 'quality': 0.9}
)
```

### Witness System

```python
from genesis_witness import GenesisWitnessSystem

# Initialize
witness = GenesisWitnessSystem()

# Witness a transaction
witnessed_tx = witness.witness_transaction(
    transaction={'type': 'action', 'data': '...'},
    witness_count=2
)

# Verify witnessed transaction
valid, invalid_witnesses = witness.verify_witnessed_transaction(witnessed_tx)
```

### Cryptography

```python
from genesis_crypto import GenesisCrypto, TransactionSigner

# Initialize
crypto = GenesisCrypto()
signer = TransactionSigner(crypto)

# Generate key pair
keypair = crypto.generate_keypair('lct:web4:bob')

# Sign transaction
signed = signer.sign_transaction(
    transaction={'type': 'test', 'data': 'hello'},
    signer_lct='lct:web4:bob'
)

# Verify signature
valid = signer.verify_transaction(signed)
```

## Configuration

### Endpoints

```python
# Default configuration
BLOCKCHAIN_RPC = "http://localhost:26657"  # Tendermint RPC
BLOCKCHAIN_API = "http://localhost:1317"   # REST API
CHAIN_ID = "act-web4"
```

### File Paths

```python
# State files (in ~/.genesis_*)
~/.genesis_keys/keypairs.json     # Key storage
~/.genesis_atp/pool_state.json    # ATP/ADP state
~/.genesis_atp/transactions.log   # Transaction log
~/.genesis_witness/attestations.json  # Witness records
~/.genesis_blockchain/transactions.log  # Chain transactions
```

## Dependencies

```
Python >= 3.10
requests >= 2.28
cryptography >= 40.0
PyNaCl >= 1.5 (optional, fallback crypto)
```

## Error Handling

```python
from genesis_blockchain import GenesisBlockchainIntegration, BlockchainError

blockchain = GenesisBlockchainIntegration()

try:
    result = blockchain.submit_transaction(tx, signer)
except BlockchainError as e:
    if 'insufficient ATP' in str(e):
        print("Need to recharge ATP first")
    elif 'invalid signature' in str(e):
        print("Check signer key")
    else:
        raise
```

## See Also

- [../README.md](../README.md) - ACT chain overview
- [../ARCHITECTURE.md](../ARCHITECTURE.md) - Module documentation
- [../../spec/witness-protocol/](../../spec/witness-protocol/) - Witness protocol spec
