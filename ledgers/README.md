# Web4 Ledgers

Immutable record systems for trust infrastructure. This module provides append-only data structures that enable verifiable action provenance, audit trails, and distributed agreement without centralized authority.

> **Not Just Theory**: Web4 ledgers have fully operational implementations. The [ACT Chain](act-chain/) provides a production-ready distributed ledger (81,000+ lines of Go, 8 Cosmos SDK modules) that has been tested in multi-node federation scenarios. See [github.com/dp-web4/ACT](https://github.com/dp-web4/ACT).

## Overview

Web4 ledgers serve several critical functions:

1. **Action Provenance** - Every action by humans, AI agents, or systems is recorded with cryptographic integrity
2. **Trust Accumulation** - T3/V3 tensor updates are anchored in verifiable history
3. **Witness Chains** - Bidirectional attestation creates webs of accountability
4. **Compliance Export** - Immutable records satisfy regulatory requirements

## Architecture

Web4 uses a **fractal chain architecture** with four temporal layers:

| Layer | Retention | Purpose | Storage |
|-------|-----------|---------|---------|
| **Compost** | ms-seconds | Working memory, ephemeral operations | Ring buffers |
| **Leaf** | seconds-minutes | Session records, SNARC-gated | SQLite/JSONL |
| **Stem** | minutes-hours | Team memory, pattern consolidation | PostgreSQL |
| **Root** | Permanent | Global consensus, immutable truth | Distributed |

Records flow upward through **witness marks** - selective promotion based on significance, not computation.

## Key Concepts

### Hash Chaining

Every entry links to its predecessor via cryptographic hash:

```
Entry N: { content, prev_hash: SHA256(Entry N-1) }
```

Tampering with any entry breaks the chain, making unauthorized modification detectable.

### Witnessing

Entities attest to observations through signed witness records:

- **Time Witness** - Trusted timestamp authority
- **Audit Witness** - Policy compliance verification
- **Action Witness** - Operation execution confirmation
- **Quality Witness** - Performance metrics attestation

See [spec/witness-protocol/](spec/witness-protocol/) for the full protocol.

### Metabolic Timing

Ledger operations follow biological rhythms:

```python
ACTIVE:      60s   # Normal operation
REST:       300s   # Reduced activity
SLEEP:     1800s   # Maintenance mode
HIBERNATION: 3600s # Minimal activity
```

This creates natural checkpoints and reduces resource consumption during quiet periods.

## Directory Structure

```
ledgers/
├── spec/                    # Specifications (no code)
│   ├── fractal-chains/      # 4-layer temporal hierarchy
│   ├── witness-protocol/    # Attestation formats
│   └── api/                 # REST/OpenAPI specs
│
├── reference/               # Reference implementations
│   ├── python/              # Enterprise, heartbeat, governance (~3,000 lines)
│   └── typescript/          # Team ledger, trace
│
├── act-chain/               # ACT distributed ledger (Root chain)
│   ├── ARCHITECTURE.md      # 8 Cosmos SDK modules documented
│   └── bridge/              # Python integration (~1,400 lines)
│   (Full Go source: github.com/dp-web4/ACT - 81,000+ lines)
│
└── archive/                 # Historical implementations
```

## Implementation Status

| Component | Language | Lines | Status |
|-----------|----------|-------|--------|
| ACT Chain (Root) | Go | 81,000+ | Production-ready |
| Enterprise Ledger | Python | 730 | Production-ready |
| Heartbeat Ledger | Python | 980 | Production-ready |
| Governance Audit | Python | 450 | Production-ready |
| Witness System | Python | 600 | Production-ready |
| Team Ledger | TypeScript | 900 | Production-ready |

## Quick Start

### Python (Enterprise Ledger)

```python
from ledgers.reference.python.enterprise_ledger import Ledger

ledger = Ledger("my_team.db")
ledger.initialize()

# Record an action
entry_id = ledger.record_audit(
    actor_lct="lct:web4:alice",
    action_type="tool_call",
    target="file:///src/main.py",
    result_hash="sha256:abc123..."
)

# Verify integrity
valid, errors = ledger.verify_chain()
```

### TypeScript (Team Ledger)

```typescript
import { Ledger } from './ledgers/reference/typescript/team_ledger';

const ledger = new Ledger({ storagePath: './data', teamLct: 'lct:web4:team:eng' });
await ledger.init();

// Submit R6 request
const entry = await ledger.submitR6Request({
    requester: 'lct:web4:alice',
    request: 'Deploy to staging',
    target: 'k8s://staging/app'
});
```

## Integration with Web4

Ledgers integrate with other Web4 components:

- **LCT Registry** - Identity binding for actors
- **Trust Tensor** - T3/V3 snapshots in entries
- **ATP/ADP Economy** - Energy accounting per operation
- **MRH Context** - Relevancy horizon scoping

## See Also

- [act-chain/](act-chain/) - **Full distributed ledger implementation** (Cosmos SDK)
- [TERMINOLOGY.md](TERMINOLOGY.md) - Translation guide for industry terms
- [spec/fractal-chains/](spec/fractal-chains/) - Detailed chain specifications
- [spec/witness-protocol/](spec/witness-protocol/) - Witnessing protocol
- [ARCHIVIST.md](ARCHIVIST.md) - Long-term storage guide
- [PUBLISHER.md](PUBLISHER.md) - API integration guide
- [ACT Repository](https://github.com/dp-web4/ACT) - Full Go source code
