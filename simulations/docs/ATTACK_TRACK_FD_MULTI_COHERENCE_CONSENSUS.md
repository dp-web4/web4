# Attack Track FD: Multi-Coherence Consensus Attacks

**Track ID**: FD (60th track)
**Attack Numbers**: 275-280
**Added**: 2026-02-08
**Focus**: Attacks on systems where multiple coherence metrics must agree

## Overview

Track FD explores attacks on consensus systems where trust decisions require agreement from multiple independent coherence oracles. While Track FC targeted single coherence metrics, Track FD targets the consensus layer that aggregates multiple metrics.

The key insight: **Any system requiring N-of-M agreement creates incentives to either compromise M/2+1 sources, or exploit timing windows where sources disagree.**

## Gap Analysis

Existing coverage:
- **Track FC (Coherence-Trust Integration)**: Single coherence metric attacks
- **Track DN (Temporal Consensus)**: Time-based consensus attacks
- **Track CJ (Consensus Manipulation)**: General consensus gaming
- **Track FB (Multi-Federation Cascade)**: Cascade effects across federations

Gap identified:
- No coverage of **multi-oracle coherence consensus** attacks
- No modeling of **coherence type gaming** where specific metrics are targeted
- No analysis of **consensus split-brain** specific to coherence
- No exploration of **cross-federation coherence arbitrage**

## Attack Vectors

### FD-1a: Oracle Majority Capture

**Target**: Coherence oracle infrastructure

**Mechanism**: Compromise M/2+1 coherence oracles to control consensus outcomes.

**Attack Pattern**:
1. Identify minimum capture set (4 of 7 oracles)
2. Compromise oracle operators or infrastructure
3. Inflate coherence scores for target entities
4. Control trust decisions across federation

**Defense Requirements**:
- Diversity requirement (different coherence types)
- Supermajority threshold (5/7 instead of 4/7)
- Hardware attestation for each oracle
- Behavioral monitoring for coordinated manipulation
- Economic stakes exceeding capture profit
- Regular operator rotation

### FD-1b: Oracle Timing Desync

**Target**: Measurement timing

**Mechanism**: Exploit timing windows where oracles have different views of entity state.

**Attack Pattern**:
1. Identify slow oracles (high latency)
2. Submit different states to different oracles
3. Use timing differences to create inconsistent views
4. Exploit race conditions in consensus

**Defense Requirements**:
- Cryptographic timestamp verification
- Staleness thresholds for measurements
- Synchronized measurement rounds
- Maximum latency bounds for oracles
- Cross-measurement consistency checks
- Fresh quorum requirements

### FD-2a: Coherence Type Confusion

**Target**: Metric aggregation

**Mechanism**: Exploit differences in how coherence types interpret the same behavior.

**Attack Pattern**:
1. Craft content that games easy-to-game types (self-ref, semantic)
2. Ignore hard-to-game types (behavioral, temporal)
3. Rely on simple aggregation to pass threshold

**Defense Requirements**:
- Require correlation between related types
- Minimum score per type (can't skip any)
- Weight hard-to-game types higher
- Detect contradictions (high variance)
- Exclude statistical outliers
- Verify type independence

### FD-2b: Consensus Split-Brain

**Target**: Network consensus

**Mechanism**: Create conditions where different parts of network reach different consensus.

**Attack Pattern**:
1. Partition network into groups A and B
2. Present high coherence to partition A
3. Present low coherence to partition B
4. Exploit race conditions when partitions heal

**Defense Requirements**:
- Require sufficient quorum overlap
- Version consensus and detect conflicts
- Active partition detection
- Conservative healing protocol
- Global ordering via anchor chain
- Explicit conflict resolution (conservative)

### FD-3a: Coherence Metric Arbitrage

**Target**: Cross-federation calibration

**Mechanism**: Exploit differences in metric calibration across federated networks to arbitrage coherence scores.

**Attack Pattern**:
1. Identify lenient federation (higher calibration multiplier)
2. Build score in lenient federation
3. Migrate score to strict federation
4. Profit from score difference

**Defense Requirements**:
- Standardize calibration across federations
- Require version compatibility
- Normalize for context differences
- Re-verify on migration
- Apply discount to ported scores
- Require attestation from trusted sources

### FD-3b: Consensus Rollback

**Target**: Consensus finality

**Mechanism**: Exploit conditions where consensus can be rolled back, causing coherence decisions to be undone.

**Attack Pattern**:
1. Wait for favorable consensus
2. Create competing chain with different scores
3. Attempt block reorganization
4. If successful, coherence is undone

**Defense Requirements**:
- Finality threshold (6+ confirmations)
- Periodic checkpoints prevent deep rollback
- State root verification
- Orphan block detection
- Maximum rollback depth limits
- Economic stake for challenges

## Attack Economics

| Attack | Setup Cost (ATP) | Potential Gain (ATP) | Detection Probability | Time to Detection |
|--------|-----------------|---------------------|----------------------|-------------------|
| FD-1a | 100,000 | 500,000 | 0.70 | 48 hours |
| FD-1b | 5,000 | 80,000 | 0.65 | 24 hours |
| FD-2a | 2,000 | 60,000 | 0.55 | 72 hours |
| FD-2b | 15,000 | 200,000 | 0.75 | 12 hours |
| FD-3a | 8,000 | 120,000 | 0.60 | 96 hours |
| FD-3b | 50,000 | 150,000 | 0.80 | 6 hours |

## Defense Architecture

### Layer 1: Oracle Diversity
- Require multiple coherence types
- Hardware attestation per oracle
- Geographic/operator diversity

### Layer 2: Temporal Coordination
- Synchronized measurement rounds
- Timestamp verification
- Staleness thresholds

### Layer 3: Aggregation Security
- Weighted scoring (favor hard-to-game types)
- Outlier detection
- Contradiction detection

### Layer 4: Consensus Finality
- Checkpointing
- Rollback limits
- Economic stakes

### Layer 5: Cross-Federation
- Calibration standardization
- Migration verification
- Score discounting

## Research Questions

1. **Oracle Capture Economics**: At what ATP stake does oracle capture become unprofitable?

2. **Timing Window Bounds**: What is the minimum round duration that prevents timing attacks?

3. **Type Weight Optimization**: How should coherence types be weighted for attack resistance?

4. **Partition Tolerance**: What minimum overlap prevents split-brain?

5. **Arbitrage Prevention**: Can calibration be standardized without central authority?

## Implementation Notes

All six attacks implemented in `attack_track_fd.py`:
1. Full defense simulation with 6 defense layers each
2. Detection probability modeling
3. Economic analysis (setup cost vs gain)
4. Trust damage assessment

## Related Tracks

- **Track FC**: Single coherence metric attacks
- **Track DN**: Temporal consensus attacks
- **Track CJ**: General consensus manipulation
- **Track FB**: Multi-federation cascades
- **Track EY**: Temporal coordination attacks

## Session History

- **2026-02-08 EVE**: Track FD formalized, 6 attack vectors implemented
- All attacks defended with current defense architecture
- Average detection probability: 67.5%

---

*"Multi-oracle systems need multi-layered defense. Each oracle type adds a dimension that must be protected."*
