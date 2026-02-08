# Leaf Chains

**Time Scale**: Seconds to Minutes
**Purpose**: Short-term episodic memory with selective retention
**ATP Cost**: 1-10 units
**Verification**: Local (SNARC-gated)

## Overview

Leaf chains capture session-level activity - individual interactions, transactions, and events that may warrant longer retention. Like leaves that capture energy before seasonal shedding, these chains retain value temporarily while feeding patterns to higher levels.

## Characteristics

- **SNARC-gated retention**: Significant events promoted, others pruned
- **Local verification**: Lightweight cryptographic signatures
- **Selective sync**: Peer synchronization for important events
- **Parent witnessing**: Key events generate witness marks for Stem chain

## Use Cases

| Domain | Example |
|--------|---------|
| Vehicles | Trip segments, driving events |
| Users | Interaction sessions, conversations |
| Collaboration | Temporary workspaces |
| Detection | Short-term pattern recognition |

## Implementation Details

### Entry Format

```json
{
  "entry_id": "leaf-42-1337",
  "timestamp": "2026-02-08T14:00:00.123Z",
  "prev_hash": "sha256:abc123...",
  "content": {
    "type": "session_event",
    "actor_lct": "lct:web4:alice",
    "action": "tool_call",
    "target": "file:///src/main.py"
  },
  "signature": "ed25519:xyz789..."
}
```

### Storage Architecture

```python
class LeafChain:
    """Session-level ledger with selective retention."""

    def __init__(self, storage_path: str):
        self.entries = []
        self.storage = Path(storage_path)

    def append(self, content: dict, signer_key) -> dict:
        """Add signed entry to chain."""
        prev_hash = self.get_latest_hash()

        entry = {
            'entry_id': self.generate_id(),
            'timestamp': datetime.now().isoformat(),
            'prev_hash': prev_hash,
            'content': content,
            'content_hash': self.hash_content(content),
            'signature': self.sign(content, signer_key)
        }

        self.entries.append(entry)
        self.persist(entry)
        return entry
```

### SNARC Gating

SNARC (Significant Novel Anomalous Relevant Consequential) determines retention:

```python
def snarc_score(entry):
    """Calculate retention priority."""
    score = 0

    # Significant: High ATP cost or trust change
    if entry['content'].get('atp_cost', 0) > 10:
        score += 2

    # Novel: First occurrence of pattern
    if is_novel_pattern(entry):
        score += 3

    # Anomalous: Deviation from baseline
    if entry['content'].get('anomaly_score', 0) > 0.7:
        score += 2

    # Relevant: Within active MRH
    if within_active_mrh(entry):
        score += 1

    # Consequential: Has downstream effects
    if entry['content'].get('spawns'):
        score += 2

    return score

def should_retain(entry):
    """Entries with SNARC score >= 3 are retained."""
    return snarc_score(entry) >= 3
```

### Retention Policy

- **Default lifetime**: 1-24 hours
- **SNARC retention**: High-scoring entries kept longer
- **Promotion threshold**: Score >= 5 creates witness mark
- **Pruning**: Low-score entries removed after session end

## Witnessing Protocol

### Creating Witness Marks

```python
def create_witness_mark(entry):
    """Create mark for Stem chain."""
    return {
        'entry_id': entry['entry_id'],
        'hash': entry['content_hash'],
        'timestamp': entry['timestamp'],
        'device_id': get_device_id(),
        'summary': extract_summary(entry),
        'signature': sign_mark(entry)
    }
```

### Parent Acknowledgment

```json
{
  "type": "witness_ack",
  "witnessed_entry": "leaf-42-1337",
  "witness_device": "stem-node",
  "witness_timestamp": "2026-02-08T14:00:01.000Z",
  "trust_delta": 0.01,
  "ack_signature": "parent_signature"
}
```

## Peer Synchronization

Leaf chains can sync with peers for redundancy:

```python
async def sync_with_peer(self, peer_url: str):
    """Selective sync of significant entries."""
    my_marks = [e for e in self.entries if should_sync(e)]
    peer_marks = await peer.get_marks()

    # Exchange missing entries
    missing = set(peer_marks) - set(my_marks)
    for mark in missing:
        entry = await peer.get_entry(mark)
        self.merge_entry(entry)
```

## Energy Considerations

| Operation | ATP Cost |
|-----------|----------|
| Create entry | 1-2 |
| Sign entry | 1 |
| Sync entry | 2-3 |
| Create witness mark | 5 |

## Relationship to Other Chains

```
Stem Chain (minutes-hours)
    ↑
    │ [witness marks]
    │
Leaf Chain (this level)
    ↑
    │ [selective witness marks]
    │
Compost Chain (ms-seconds)
```

## Best Practices

1. **Session scoping**: One chain per session/task
2. **Sign everything**: Lightweight Ed25519 for all entries
3. **SNARC ruthlessly**: Don't over-retain
4. **Witness selectively**: Only significant events go up

## See Also

- [README.md](README.md) - Fractal chain overview
- [compost-chains.md](compost-chains.md) - Previous level
- [stem-chains.md](stem-chains.md) - Next level up
- [../witness-protocol/](../witness-protocol/) - Witnessing details
