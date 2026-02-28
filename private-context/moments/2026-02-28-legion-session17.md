# Session 17 — Feb 28, 2026 (Legion)

## Summary
Session 17: 5 tracks, 477/477 checks, 13 bugs found and fixed. All tracks committed and pushed.

## Tracks

### Track 1: Adaptive Consensus Protocol (102/102)
- 4 consensus algorithms: fast-path (2-phase), PBFT (3-phase), raft-like, hardened BFT (4-phase)
- Automatic switching based on NetworkCondition health assessment
- Hysteresis (3 consecutive samples), cooldown (10s), immediate override for HARDENED_BFT
- **Bugs**: 2
  - Cooldown blocked first switch (`last_switch_time=0.0` → `-1000.0`)
  - PBFT message count: n messages instead of n² (broadcast = all-to-all)

### Track 2: Economic Attack Resistance (90/90)
- 8 attack vectors: treasury drain, inflation, fee manipulation, flash loans, front-running, wash trading, staking, sybil economics
- **Bugs**: 4
  - Rewards from nowhere (added reward_pool account)
  - Account creation order vs supply measurement
  - NaN bypasses debit guard (IEEE 754: `nan <= 0` is False)
  - Wash volume threshold diluted by inclusion in mean (lowered from 2.0 to 1.5)

### Track 3: Cross-Module Formal Composition (91/91)
- Sequential, parallel, advanced DP composition
- ZK AND/OR/threshold composition
- Trust-weighted governance, interference detection
- **Bugs**: 3
  - `sum([0.1]*100) ≠ 10.0` (floating point)
  - Zero-trust entity: `0 >= 0*2` is True (skip zero-weight)
  - Advanced composition NOT tighter for 20 medium ε (changed to 100 × 0.05)

### Track 4: WASM Trust Validator (105/105)
- Conformance validation: T3/V3 tensors, ATP transactions, LCT structure, MRH zones
- 16 entity types validated, trust chain continuity, batch processing, performance benchmarks
- **Bugs**: 0 — CLEAN first run!

### Track 5: End-to-End Integration Pipeline (89/89)
- 12 sections: entity lifecycle, trust accumulation, ATP earning, governance, privacy, consensus, cross-federation, audit trail, full simulation (20×50), stress test, error recovery, complete E2E
- **Bugs**: 4
  - Carol's trust 0.15 ≥ min_vote 0.1 (lowered to 0.05)
  - 1 high-trust vs 2 lower-trust voters (fixed voter ratio)
  - Proposal stake vanished from system (added `ledger.stake()` tracking)
  - Federation had its own empty ledger (accept shared ledger + track cross-fed fees)

## Key Insights

### New Technical Discoveries
- Cooldown initialization trap: `last_switch_time=0.0` prevents first event if cooldown > event_time
- PBFT broadcast is O(n²), not O(n) — each node broadcasts to ALL others
- Reward pool pattern: tasks pay into pool, rewards come from pool (conservation safe)
- Stake tracking: `total_staked` must be in conservation formula alongside `total_fees`
- Cross-federation fee tracking: fees from cross-fed transfers must be tracked like regular fees
- Shared vs isolated ledgers: E2E tests need shared ledger; unit tests can use isolated

### Recurring Patterns
- IEEE 754 NaN behavior (3rd session in a row)
- Conservation invariants break when any operation bypasses the ledger's tracking
- Zero-value edge cases create false positives in ratio comparisons
- Floating point accumulation errors for repeated decimal addition

## Cumulative Stats
- 175 reference implementations
- Session 17: 477 checks, 13 bugs
- Estimated cumulative: ~11,121+ checks across all sessions
