# web4-trust-core

Core trust primitives for the Web4 ecosystem, implemented in Rust with Python bindings.

## Features

- **T3 Trust Tensor**: 6-dimensional trust measurement (competence, reliability, consistency, witnesses, lineage, alignment)
- **V3 Value Tensor**: 6-dimensional value measurement (energy, contribution, stewardship, network, reputation, temporal)
- **EntityTrust**: Combines T3+V3 with witnessing relationships
- **TrustStore**: Persistent storage with JSON format compatibility

## Installation

```bash
pip install web4-trust
```

Or build from source:

```bash
pip install maturin
maturin develop
```

## Usage

```python
from web4_trust import TrustStore, EntityTrust

# Open the default store (~/.web4/governance/entities)
store = TrustStore()

# Get or create entity trust
trust = store.get("mcp:filesystem")
print(f"T3 average: {trust.t3_average():.3f}")
print(f"Trust level: {trust.trust_level()}")

# Update from action outcome
store.update("mcp:filesystem", success=True, magnitude=0.1)

# Witness event: session observes MCP server
witness_trust, target_trust = store.witness(
    "session:abc",
    "mcp:filesystem",
    success=True,
    magnitude=0.1
)
print(f"MCP trust after witnessing: {target_trust.t3_average():.3f}")
```

## Architecture

```
┌─────────────────────────────────────────┐
│  web4-trust-core (Rust)                 │
│  - T3/V3 tensor math                    │
│  - EntityTrust with witnessing          │
│  - Decay calculations                   │
│  - Storage backends                     │
└─────────────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │  PyO3 Bindings    │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │  Python Package   │
    │  (web4_trust)     │
    └───────────────────┘
```

## License

MIT
