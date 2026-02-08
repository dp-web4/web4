# Fractal Chain Architecture

Web4 implements a temporal chain hierarchy that matches persistence requirements to verification needs, creating a fractal structure from ephemeral to permanent.

## The Four-Chain Temporal Hierarchy

```
                    Root Chain (Permanent)
                           ↑
                    [witness marks]
                           ↑
                      Stem Chains (m-h)
                           ↑
                    [witness marks]
                           ↑
                      Leaf Chains (s-m)
                           ↑
                    [witness marks]
                           ↑
                     Compost Chains (ms-s)
```

Each level maintains autonomy while contributing to the whole:

- **Local Entry Creation**: Each level creates entries at its own pace
- **Asynchronous Propagation**: No synchronous coordination required
- **Selective Verification**: Full data retrieved only when needed
- **Privacy Preservation**: Details stay local until requested

## Overview

| Chain | Time Scale | Purpose | ATP Cost | Verification |
|-------|------------|---------|----------|--------------|
| [Compost](compost-chains.md) | ms-seconds | Working memory | 0 | None |
| [Leaf](leaf-chains.md) | seconds-minutes | Session records | 1-10 | Local |
| [Stem](stem-chains.md) | minutes-hours | Team memory | 10-100 | Regional |
| [Root](root-chains.md) | Permanent | Global truth | 100+ | Global |

## Advantages Over Traditional Approaches

### Scalability
- Each device handles only its own data
- No global state synchronization
- Witness marks are tiny (200-500 bytes)
- Network traffic proportional to hierarchy depth, not node count

### Flexibility
- Different entry rates per level (cells: ms, modules: min, packs: hr)
- Multiple data formats (binary, JSON, protobuf)
- Varied storage strategies (memory, disk, distributed)
- Adaptive retention policies per level

### Resilience
- No single point of failure
- Graceful degradation under partition
- Missing witnesses don't break the chain
- Parent can reconstruct from witness marks

### Privacy
- Data stays local by default
- Only hashes propagate upward
- Selective disclosure mechanisms
- Encrypted private channels supported

## Decision Tree for Chain Selection

```
What is the data's lifetime?
├─ < 1 minute → Compost Chain
├─ < 1 hour → Leaf Chain
├─ < 1 month → Stem Chain
└─ Permanent → Root Chain

What is the verification need?
├─ None → Compost Chain
├─ Local → Leaf Chain
├─ Regional → Stem Chain
└─ Global → Root Chain

What is the ATP budget?
├─ < 1 ATP → Compost Chain
├─ 1-10 ATP → Leaf Chain
├─ 10-100 ATP → Stem Chain
└─ 100+ ATP → Root Chain
```

## Integration with Web4 Components

### LCT Integration
Each chain level can anchor LCTs:
- Compost: Temporary session LCTs
- Leaf: Task and role LCTs
- Stem: Project and team LCTs
- Root: Permanent entity LCTs

### ATP/ADP Energy Flows
Memory operations consume and generate value:
- **Storage Cost**: Creating entries costs ATP (varies by level)
- **Access Returns**: Frequently accessed entries earn ATP
- **Witness Value**: Acknowledgments generate trust and ATP
- **Pruning Recovery**: Forgetting obsolete data recovers ATP

### T3/V3 Trust Metrics
Chain operations affect trust scores:
- Reliable witnessing increases T3 scores
- Valuable entries increase V3 scores
- Failed verifications decrease trust
- Consistent participation builds reputation

## See Also

- [compost-chains.md](compost-chains.md) - Working memory details
- [leaf-chains.md](leaf-chains.md) - Session records
- [stem-chains.md](stem-chains.md) - Team memory
- [root-chains.md](root-chains.md) - Permanent records
- [../witness-protocol/](../witness-protocol/) - Witness-acknowledgment protocol
