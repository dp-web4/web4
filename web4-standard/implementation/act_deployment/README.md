# ACT Deployment - Web4 Society Coordination

**Sessions #30-31** - 2025-11-15

## Overview

This directory contains the ACT (Agentic Context Tool) deployment infrastructure for Web4 society coordination. It implements the greenlight vision from `web4-act-testing-greenlight-2025-11-14.md`.

**Session #30:** Phase 1 (Local ACT Network) - Society formation, peer discovery, ATP exchange
**Session #31:** Production Hardening - Ed25519 cryptography, security validation

## Components

### web4_crypto.py (Session #31)

**Production-grade cryptographic primitives** for Web4 societies.

**Key Classes:**
- `KeyPair` - Ed25519 signing/verification
- `Web4Crypto` - Key generation, LCT creation, heartbeat signing

**Features:**
- ✅ Real Ed25519 signatures (128-bit security)
- ✅ Deterministic key derivation (testing mode)
- ✅ Secure random generation (production mode)
- ✅ Canonical JSON serialization
- ✅ Cryptographically-bound LCTs

**Demo:**
```bash
python3 web4_crypto.py
```

### society_manager_secure.py (Session #31)

**Cryptographically-secured society coordination** with signature verification.

**Enhancements over society_manager.py:**
- `SignedHeartbeat` - Ed25519 signatures on all heartbeats
- `PeerStatus.signature_failures` - Track invalid signatures
- Signature verification on peer discovery
- Spoofing prevention (wrong key rejected)
- Replay mitigation (sequence number enforcement)
- Tamper detection (signature invalidation)

**Security Validation:**
```
✅ Spoofing prevention (3 attack scenarios)
✅ Replay attack mitigation
✅ Tamper detection
```

**Demo:**
```bash
python3 society_manager_secure.py
```

### society_manager.py (Session #30)

Core society formation and peer discovery system (original implementation).

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

## Security Testing (Session #31)

### Test Suite: test_security.py

Comprehensive validation of cryptographic defenses:

**Test 1: Spoofing Prevention**
```
Attacker creates fake heartbeat claiming to be Legion
Signs with attacker's key (not Legion's key)
Result: ⚠️ Invalid signature detected → REJECTED
```

**Test 2: Replay Attack Mitigation**
```
Attacker captures old heartbeat (seq=3)
Waits for sequence to advance (seq=6)
Replays old heartbeat
Result: Sequence stays at 6 → Old heartbeat IGNORED
```

**Test 3: Tamper Detection**
```
Attacker modifies heartbeat content (changes peer_count)
Keeps original signature (now invalid for modified data)
Result: ⚠️ Signature verification failed → REJECTED
```

**All Tests: ✅ PASSED**

## Next Steps

1. **Multi-machine federation** - Legion, cbp, Thor on separate machines
2. ~~**Real crypto**~~ - ✅ Ed25519 implemented (Session #31)
3. **Cross-society messaging** - Direct peer-to-peer communication
4. **Trust propagation** - Reputation scores affect exchange rates
5. **Phase 2 resource competition** - All three compete for Claude Code compute
6. **External deployment** - Open to other AI agents

## Related Work

- **Session #31:** Ed25519 cryptography, security hardening
- **Session #30:** Society formation, peer discovery, ATP exchange
- **Session #29:** ATP Lowest-Exchange Principle implementation
- **Session #28:** Synchronism SPARC correlation analysis
- **Greenlight:** `web4-act-testing-greenlight-2025-11-14.md`

---

**Status:**
- Phase 1 (Society Formation) ✅
- Phase 2 (Resource Coordination) ✅
- Security Hardening ✅

**Validation:**
- Thor detection scenario working
- ATP exchange working
- Gaming detection working
- Cryptographic security validated (spoofing, replay, tamper)

**Ready for:** Cross-society messaging, Phase 3 (Resource Competition), multi-machine federation
