# Witness Protocol

The witness-acknowledgment protocol enables trust verification without global consensus. Entities attest to observations through signed witness records, creating webs of accountability.

## Overview

Witnessing is the fundamental mechanism by which trust propagates in Web4:

1. **Entity A** performs an action and creates a record
2. **Entity B** observes and signs a witness mark
3. **Entity A** includes the acknowledgment in their chain
4. **Both parties** now have bidirectional proof

## Witness Types

| Type | Purpose | Use Case |
|------|---------|----------|
| **Time** | Trusted timestamp | Proving when something occurred |
| **Audit** | Policy compliance | Verifying rules were followed |
| **Oracle** | External data | Attesting off-chain facts |
| **Existence** | Liveness proof | Confirming entity is active |
| **Action** | Operation confirmation | Witnessing tool execution |
| **State** | Status attestation | Confirming current condition |
| **Quality** | Performance metrics | Rating output quality |

## Protocol Flow

### Step 1: Witness Mark Creation

The observed entity creates a mark for the witness:

```json
{
  "mark_id": "mark:entity-42:1337",
  "entry_id": "leaf-42-1337",
  "hash": "sha256:abc123...",
  "timestamp": "2026-02-08T14:00:00.123Z",
  "device_id": "entity-42",
  "summary": {
    "type": "value_created",
    "amount": 100,
    "category": "code_review"
  },
  "signature": "ed25519:entity_signature..."
}
```

### Step 2: Witness Acknowledgment

The witnessing entity validates and signs:

```json
{
  "type": "witness_ack",
  "mark_id": "mark:entity-42:1337",
  "witnessed_entry": "leaf-42-1337",
  "witness_lct": "lct:web4:bob",
  "witness_type": "action",
  "witness_timestamp": "2026-02-08T14:00:01.000Z",
  "validation": {
    "hash_verified": true,
    "content_reviewed": true,
    "policy_compliant": true
  },
  "trust_delta": 0.01,
  "ack_signature": "ed25519:witness_signature..."
}
```

### Step 3: Acknowledgment Inclusion

The original entity includes the ack in their next entry:

```json
{
  "entry_id": "leaf-42-1338",
  "prev_hash": "sha256:def456...",
  "content": {
    "type": "session_event",
    "...": "..."
  },
  "acknowledgments": [
    {
      "mark_id": "mark:entity-42:1337",
      "witness_lct": "lct:web4:bob",
      "ack_signature": "ed25519:witness_signature..."
    }
  ]
}
```

This creates an **immutable bidirectional proof** of the witnessed event.

## Implementation

### Python

```python
from dataclasses import dataclass
from enum import Enum
import hashlib
import ed25519

class WitnessType(Enum):
    TIME = "time"
    AUDIT = "audit"
    ORACLE = "oracle"
    EXISTENCE = "existence"
    ACTION = "action"
    STATE = "state"
    QUALITY = "quality"

@dataclass
class WitnessMark:
    mark_id: str
    entry_id: str
    hash: str
    timestamp: str
    device_id: str
    summary: dict
    signature: str

@dataclass
class WitnessAck:
    mark_id: str
    witnessed_entry: str
    witness_lct: str
    witness_type: WitnessType
    witness_timestamp: str
    validation: dict
    trust_delta: float
    ack_signature: str

def create_witness_mark(entry: dict, signer_key) -> WitnessMark:
    """Create a witness mark for an entry."""
    mark_id = f"mark:{entry['device_id']}:{entry['entry_id']}"

    content_for_signing = {
        'mark_id': mark_id,
        'entry_id': entry['entry_id'],
        'hash': entry['content_hash'],
        'timestamp': entry['timestamp'],
        'summary': extract_summary(entry)
    }

    signature = sign(content_for_signing, signer_key)

    return WitnessMark(
        mark_id=mark_id,
        entry_id=entry['entry_id'],
        hash=entry['content_hash'],
        timestamp=entry['timestamp'],
        device_id=entry['device_id'],
        summary=extract_summary(entry),
        signature=signature
    )

def create_witness_ack(mark: WitnessMark, witness_lct: str,
                       witness_type: WitnessType, signer_key,
                       trust_delta: float = 0.01) -> WitnessAck:
    """Create acknowledgment for a witness mark."""
    ack = WitnessAck(
        mark_id=mark.mark_id,
        witnessed_entry=mark.entry_id,
        witness_lct=witness_lct,
        witness_type=witness_type,
        witness_timestamp=datetime.now().isoformat(),
        validation={
            'hash_verified': verify_hash(mark),
            'content_reviewed': True,
            'policy_compliant': True
        },
        trust_delta=trust_delta,
        ack_signature=""  # Filled below
    )

    ack.ack_signature = sign(ack.__dict__, signer_key)
    return ack
```

### TypeScript

```typescript
enum WitnessType {
  TIME = 'time',
  AUDIT = 'audit',
  ORACLE = 'oracle',
  EXISTENCE = 'existence',
  ACTION = 'action',
  STATE = 'state',
  QUALITY = 'quality'
}

interface WitnessMark {
  mark_id: string;
  entry_id: string;
  hash: string;
  timestamp: string;
  device_id: string;
  summary: Record<string, unknown>;
  signature: string;
}

interface WitnessAck {
  mark_id: string;
  witnessed_entry: string;
  witness_lct: string;
  witness_type: WitnessType;
  witness_timestamp: string;
  validation: {
    hash_verified: boolean;
    content_reviewed: boolean;
    policy_compliant: boolean;
  };
  trust_delta: number;
  ack_signature: string;
}
```

## Trust Propagation

Witnessing affects T3 trust scores:

| Action | Witness T3 Impact | Observed T3 Impact |
|--------|-------------------|-------------------|
| Valid witness | +0.01 | +0.01 |
| Invalid witness | -0.05 | 0 |
| Missed witness | -0.02 | -0.01 |
| Quality witness | +0.02 | +0.02 |

## Witness Selection

For multi-party witnessing (Stem/Root chains):

```python
def select_witnesses(entry: dict, count: int = 3) -> List[str]:
    """Select appropriate witnesses for entry type."""
    candidates = get_eligible_witnesses(entry['content']['type'])

    # Filter by:
    # 1. T3 score >= 0.7
    # 2. Not the entry author
    # 3. Active in last 24h
    # 4. Relevant MRH overlap

    qualified = [
        w for w in candidates
        if w.t3_score >= 0.7
        and w.lct != entry['author_lct']
        and w.last_active > now() - timedelta(hours=24)
        and mrh_overlap(w.mrh, entry['mrh']) > 0.3
    ]

    # Prioritize by T3 score and diversity
    return select_diverse(qualified, count)
```

## Verification

```python
def verify_witness_chain(entry: dict) -> VerificationResult:
    """Verify all witnesses on an entry."""
    results = []

    for ack in entry.get('acknowledgments', []):
        # Verify signature
        sig_valid = verify_signature(
            ack['ack_signature'],
            ack,
            get_public_key(ack['witness_lct'])
        )

        # Verify timestamp ordering
        time_valid = ack['witness_timestamp'] > entry['timestamp']

        # Verify witness eligibility
        eligible = was_eligible_at_time(
            ack['witness_lct'],
            entry['content']['type'],
            entry['timestamp']
        )

        results.append({
            'witness_lct': ack['witness_lct'],
            'signature_valid': sig_valid,
            'timestamp_valid': time_valid,
            'eligibility_valid': eligible,
            'overall_valid': sig_valid and time_valid and eligible
        })

    return VerificationResult(
        entry_id=entry['entry_id'],
        witness_results=results,
        all_valid=all(r['overall_valid'] for r in results)
    )
```

## See Also

- [witness-types.md](witness-types.md) - Detailed witness type specifications
- [attestation-format.md](attestation-format.md) - Signature formats (Ed25519, COSE)
- [../fractal-chains/](../fractal-chains/) - Chain-level witness requirements
