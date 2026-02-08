# Compost Chains

**Time Scale**: Milliseconds to Seconds
**Purpose**: Ephemeral working memory for immediate processing
**ATP Cost**: 0 (no cost)
**Verification**: None required

## Overview

Compost chains handle the fastest, most ephemeral data in the Web4 hierarchy. Like biological compost that breaks down rapidly to nourish new growth, these chains process immediate information that has value only in the moment.

## Characteristics

- **Fast turnover**: Entries created and discarded within seconds
- **Minimal verification**: No cryptographic signatures required
- **Local-only**: Never propagate beyond the originating device
- **Auto-pruning**: Ring buffer architecture with automatic cleanup

## Use Cases

| Domain | Example |
|--------|---------|
| IoT/Sensors | Real-time battery cell voltage readings |
| Processing | Immediate sensor fusion calculations |
| UI | Transient interface state |
| Performance | Cache layers, temporary buffers |

## Implementation Details

### Storage Architecture

```python
class CompostChain:
    """Ring buffer for ephemeral entries."""

    def __init__(self, max_entries=1000):
        self.buffer = collections.deque(maxlen=max_entries)
        self.created_at = time.time()

    def append(self, data):
        """Add entry - old entries automatically removed."""
        entry = {
            'timestamp': time.time_ns(),
            'data': data
        }
        self.buffer.append(entry)
        return entry
```

### Entry Format

```json
{
  "timestamp": 1708300000123456789,
  "data": {
    "sensor_id": "cell-42",
    "voltage": 3.7,
    "temperature": 25.3
  }
}
```

**Note**: No `prev_hash`, no signatures - pure speed.

### Retention Policy

- **Default lifetime**: 60 seconds
- **Max entries**: 1,000-10,000 (configurable)
- **Pruning**: Automatic via ring buffer
- **Promotion**: Significant events create witness marks for Leaf chain

## Promotion to Leaf Chain

When an event warrants longer retention:

```python
def maybe_promote(self, entry):
    """Check if entry should create witness mark."""
    if entry['data'].get('anomaly'):
        # Create witness mark for Leaf chain
        return create_witness_mark(entry)
    return None
```

**Promotion Triggers**:
- Anomaly detection
- Threshold crossing
- Explicit user marking
- Pattern completion

## Network Behavior

- **Zero network overhead**: Compost chains never transmit
- **Local only**: Data never leaves the device
- **No synchronization**: Each device is independent

## Energy Considerations

- **ATP Cost**: 0 (free)
- **Memory only**: No disk I/O
- **No crypto**: No signature computation

## Best Practices

1. **Size appropriately**: Ring buffer sized for expected throughput
2. **Don't over-retain**: Let natural pruning work
3. **Promote selectively**: Only significant events warrant witness marks
4. **Monitor overflow**: Track if buffer fills faster than expected

## Relationship to Higher Chains

```
Compost Chain (this level)
    │
    │ [selective witness marks]
    ▼
Leaf Chain (seconds-minutes)
```

Only ~1% of compost entries typically generate witness marks. The rest decompose naturally, their value captured in aggregate patterns rather than individual records.

## See Also

- [README.md](README.md) - Fractal chain overview
- [leaf-chains.md](leaf-chains.md) - Next level up
- [../witness-protocol/](../witness-protocol/) - Witness mark creation
