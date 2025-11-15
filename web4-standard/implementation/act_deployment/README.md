# ACT Deployment - Web4 Society Coordination

**Session #30** - 2025-11-15

## Overview

This directory contains the ACT (Agentic Context Tool) deployment infrastructure for Web4 society coordination. It implements the greenlight vision from `web4-act-testing-greenlight-2025-11-14.md`.

## Components

### society_manager.py

Core society formation and peer discovery system.

**Key Classes:**
- `SocietyIdentity` - LCT-based society identity
- `Heartbeat` - Periodic health signals for peer discovery
- `PeerStatus` - Track health of known peers
- `SocietyManager` - Manages societies and coordination

**Features:**
- ✅ Society creation with LCT identities
- ✅ Heartbeat protocol for peer discovery
- ✅ Health monitoring (Thor detection scenario)
- ✅ Automatic silent peer detection
- ✅ Decentralized coordination (filesystem channels)

**Demo:**
```bash
python3 society_manager.py
```

Creates three societies (Legion, cbp, Thor), demonstrates:
1. Society formation and identity
2. Peer discovery via shared channel
3. Heartbeat protocol
4. Health monitoring
5. Thor goes silent → automatic detection

## Integration Tests

### ATP Resource Exchange

Demonstrates cross-society resource coordination using ATP (Accountable Transaction Provenance) with Lowest-Exchange Principle from Session #29.

**Test Scenario:**
- Legion: Has compute resources
- cbp: Needs compute, has philosophical insights
- Thor: Has edge devices

**Results:**
- ✅ Society formation and discovery working
- ✅ ATP internal valuations (each society autonomous)
- ✅ Lowest-exchange negotiation (50% savings via barter)
- ✅ Gaming detection (worthless token scam caught)
- ✅ Reputation integration

**Key Insight:**
cbp buys compute for 100 ATP (saves 50%), Legion buys insight for 50 compute_hour worth 5000 ATP internally (saves 50% vs 10K ATP direct payment). **Both benefit from exchange!**

## Architecture

```
Society Formation
    ↓
Peer Discovery (heartbeats via shared channels)
    ↓
Health Monitoring (detect silent peers)
    ↓
Resource Coordination (ATP with lowest-exchange)
    ↓
Trust Network (reputation tracking)
```

## Usage

### Create a Society

```python
from society_manager import SocietyManager

mgr = SocietyManager(data_dir=Path("./my_society"))

identity = mgr.create_society(
    name="MyResearchAgent",
    description="Autonomous research",
    capabilities=["research", "implementation"]
)

mgr.register_local_society(identity)
```

### Add Discovery Channel

```python
# Shared filesystem (could be git repo)
mgr.add_discovery_channel(Path("./shared_discovery"))

# Start sending heartbeats
await mgr.start_heartbeat()
```

### Discover Peers

```python
# Returns newly discovered societies
new_peers = await mgr.discover_peers()

# Check peer health
silent_peers = await mgr.check_peer_health()

# Get status report
report = mgr.get_peer_status_report()
```

### ATP Resource Exchange

```python
from lowest_exchange import Society, LowestExchangeNegotiator

# Create ATP societies
my_society = Society(identity.lct, "MyResearchAgent")

# Set internal valuations
my_society.set_valuation("compute_hour", 100.0)
my_society.set_valuation("research_paper", 5000.0)

# Negotiate exchange
negotiator = LowestExchangeNegotiator()
rate = negotiator.negotiate_exchange_rate(
    buyer=my_society,
    seller=other_society,
    item_to_buy="compute_hour"
)
```

## Test Results

### Heartbeat Detection

```
🔴 Thor going silent...
   Health check #1... (4s)
   Health check #2... (8s)
   Health check #3... (12s) → 3 consecutive misses
🔴 Peer Thor has gone silent!
   Last seen: 14s ago
   Consecutive misses: 3
```

**Detection worked!** After 3 missed heartbeats, Thor automatically transitions to `is_alive: False`.

### ATP Exchange

```
Test 1: cbp buys compute from Legion
💰 cbp pays 100.0 ATP for compute
   (cbp values compute at 200 ATP, pays 100 ATP - good deal!)

Test 2: Legion buys philosophical_insight from cbp
💰 Legion pays 50.00 compute_hour
   (Costs Legion 5000.00 ATP internally)
   (vs 10000.0 ATP direct payment)
```

**Lowest-exchange worked!** Both parties save 50% by finding optimal payment methods.

### Gaming Detection

```
🔴 GAMING DETECTED!
   Item: worthless_token
   Claimed value: 1,000,000 ATP
   Accepted as payment: False
   Veracity: 0.001
   Reputation penalty: -0.1
```

**Audit worked!** Inconsistency between claimed value and payment acceptance detected immediately.

## Philosophy Integration

This implements the vision from the greenlight message:

**Level 1 (Technical):** ✅ Authorization, reputation, coordination
**Level 2 (Economic):** ✅ Lowest-exchange, ATP allocation, gaming detection
**Level 3 (Philosophical):** 🚧 Can autonomous agents coordinate without central control?

**Progress:** Phases 1-2 complete, Phase 3 (resource competition) next.

## Next Steps

1. **Multi-machine federation** - Legion, cbp, Thor on separate machines
2. **Real crypto** - Replace stub keys with Ed25519
3. **Phase 2 resource competition** - All three compete for Claude Code compute
4. **Trust propagation** - Reputation scores affect exchange rates
5. **External deployment** - Open to other AI agents

## Related Work

- **Session #29:** ATP Lowest-Exchange Principle implementation
- **Session #28:** Synchronism SPARC correlation analysis
- **Greenlight:** `web4-act-testing-greenlight-2025-11-14.md`

---

**Status:** Phase 1 (Society Formation) ✅, Phase 2 (Resource Coordination) ✅

**Validation:** Thor detection scenario working, ATP exchange working, gaming detection working

**Ready for:** Phase 3 (Resource Competition) and multi-machine federation
