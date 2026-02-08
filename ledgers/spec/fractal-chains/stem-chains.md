# Stem Chains

**Time Scale**: Minutes to Hours
**Purpose**: Medium-term consolidated memory with pattern extraction
**ATP Cost**: 10-100 units
**Verification**: Regional (multi-party witnesses)

## Overview

Stem chains consolidate learnings from multiple leaf chains, extracting patterns and building organizational memory. Like plant stems that transport nutrients and provide structure, these chains bridge ephemeral activity and permanent record.

## Characteristics

- **Cross-validation**: Multiple sources confirm patterns
- **Pattern mining**: Aggregate insights from leaf chains
- **Witness aggregation**: Multi-party verification required
- **Value-based retention**: High-value patterns kept longer

## Use Cases

| Domain | Example |
|--------|---------|
| Fleet | Performance patterns across vehicles |
| ML | Model training checkpoints |
| Organization | Team memory, institutional knowledge |
| Trust | Relationship evolution over time |

## Implementation Details

### Entry Format

```json
{
  "entry_id": "stem-team-eng-4521",
  "timestamp": "2026-02-08T14:00:00Z",
  "prev_hash": "sha256:def456...",
  "content": {
    "type": "pattern_consolidation",
    "source_entries": ["leaf-42-1337", "leaf-43-1338", "leaf-44-1339"],
    "pattern": {
      "type": "code_review_efficiency",
      "metrics": {"avg_time": 45, "approval_rate": 0.92}
    },
    "actor_lct": "lct:web4:team:eng"
  },
  "witnesses": [
    {"lct": "lct:web4:alice", "signature": "sig1..."},
    {"lct": "lct:web4:bob", "signature": "sig2..."}
  ],
  "content_hash": "sha256:ghi789..."
}
```

### Storage Architecture

```python
class StemChain:
    """Team-level ledger with pattern consolidation."""

    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self._init_schema()

    def consolidate(self, leaf_entries: List[dict], pattern: dict) -> dict:
        """Create consolidated entry from leaf sources."""
        entry = {
            'entry_id': self.generate_id(),
            'timestamp': datetime.now().isoformat(),
            'prev_hash': self.get_latest_hash(),
            'content': {
                'type': 'pattern_consolidation',
                'source_entries': [e['entry_id'] for e in leaf_entries],
                'pattern': pattern
            },
            'witnesses': []
        }

        # Require witnesses before committing
        return entry  # Pending witness collection

    def add_witness(self, entry_id: str, witness_lct: str, signature: str):
        """Add witness to pending entry."""
        # ...commit when threshold reached
```

### Witness Requirements

Stem chains require multi-party verification:

```python
WITNESS_REQUIREMENTS = {
    'pattern_consolidation': 2,  # 2 witnesses minimum
    'trust_update': 3,           # 3 for trust changes
    'policy_change': 5,          # 5 for governance
    'checkpoint': 2              # 2 for ML checkpoints
}

def can_commit(entry):
    """Check if entry has sufficient witnesses."""
    required = WITNESS_REQUIREMENTS.get(entry['content']['type'], 2)
    return len(entry['witnesses']) >= required
```

### Pattern Extraction

Stem chains mine patterns from leaf chains:

```python
def extract_patterns(leaf_entries: List[dict]) -> List[dict]:
    """Mine patterns from session data."""
    patterns = []

    # Time-based patterns
    if detect_periodicity(leaf_entries):
        patterns.append({'type': 'periodic', ...})

    # Behavioral patterns
    if detect_workflow(leaf_entries):
        patterns.append({'type': 'workflow', ...})

    # Anomaly patterns
    if detect_recurring_anomaly(leaf_entries):
        patterns.append({'type': 'anomaly', ...})

    return patterns
```

### Merkle Tree Aggregation

For efficient verification of large datasets:

```python
def build_merkle_root(entries: List[dict]) -> str:
    """Build Merkle tree from entry hashes."""
    hashes = [e['content_hash'] for e in entries]

    while len(hashes) > 1:
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])  # Duplicate last
        hashes = [
            sha256(hashes[i] + hashes[i+1])
            for i in range(0, len(hashes), 2)
        ]

    return hashes[0]
```

## Retention Policy

- **Default lifetime**: Days to months
- **Value scoring**: High-value patterns retained longer
- **Pruning criteria**: Low access + low value = removal
- **Promotion threshold**: Critical patterns → Root chain

### Value Scoring

```python
def value_score(entry):
    """Calculate retention value."""
    base = entry['content'].get('value_score', 0)

    # Access frequency bonus
    access_count = get_access_count(entry['entry_id'])
    access_bonus = min(access_count * 0.1, 2.0)

    # Trust impact bonus
    if entry['content']['type'] == 'trust_update':
        base += 1.5

    # Age decay
    age_days = (now() - entry['timestamp']).days
    age_factor = 1.0 / (1 + age_days * 0.1)

    return (base + access_bonus) * age_factor
```

## Energy Considerations

| Operation | ATP Cost |
|-----------|----------|
| Create entry | 10-20 |
| Add witness | 5 |
| Merkle aggregation | 15 |
| Pattern extraction | 20-50 |
| Root promotion | 50 |

## Relationship to Other Chains

```
Root Chain (permanent)
    ↑
    │ [witness marks for critical patterns]
    │
Stem Chain (this level)
    ↑
    │ [consolidated from multiple sources]
    │
Leaf Chains (seconds-minutes)
```

## Synchronization

Stem chains sync across team boundaries:

```python
async def federated_sync(self, peer_teams: List[str]):
    """Sync patterns with related teams."""
    for team in peer_teams:
        peer = await connect_team(team)

        # Share pattern summaries (not full data)
        my_summaries = self.get_pattern_summaries()
        peer_summaries = await peer.get_pattern_summaries()

        # Request relevant full patterns
        relevant = filter_relevant(peer_summaries, self.mrh)
        for pattern_id in relevant:
            full = await peer.get_pattern(pattern_id)
            self.merge_pattern(full)
```

## Best Practices

1. **Consolidate aggressively**: Don't keep raw leaf data
2. **Witness everything**: Multi-party for accountability
3. **Extract patterns**: Raw data → insights
4. **Prune by value**: Keep what's accessed

## See Also

- [README.md](README.md) - Fractal chain overview
- [leaf-chains.md](leaf-chains.md) - Previous level
- [root-chains.md](root-chains.md) - Next level up
- [../witness-protocol/](../witness-protocol/) - Multi-party witnessing
