# ACT Deployment - Web4 Society Coordination

**Sessions #30-33** - 2025-11-15

## Overview

This directory contains the ACT (Agentic Context Tool) deployment infrastructure for Web4 society coordination. It implements the greenlight vision from `web4-act-testing-greenlight-2025-11-14.md`.

**Session #30:** Phase 1 (Local ACT Network) - Society formation, peer discovery, ATP exchange
**Session #31:** Production Hardening - Ed25519 cryptography, security validation
**Session #32:** Cross-Society Messaging - End-to-end encrypted communication
**Session #33:** Reputation-ATP Integration - Trust-based economic incentives

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

### web4_messaging.py (Session #32)

**End-to-end encrypted messaging** between Web4 societies.

**Cryptography Stack:**
- X25519 ECDH: Key exchange for encryption
- AES-256-GCM: Authenticated encryption (confidentiality + integrity)
- Ed25519: Digital signatures (authentication)
- HKDF-SHA256: Key derivation from shared secret

**Key Classes:**
- `EncryptedMessage` - Encrypted message container with signature
- `Web4MessagingCrypto` - Cryptographic operations
- `Web4MessageSender` - Send encrypted, signed messages
- `Web4MessageReceiver` - Receive and decrypt messages

**Security Properties:**
```
✅ Confidentiality (only recipient decrypts)
✅ Authentication (signature proves sender)
✅ Integrity (AEAD + signatures detect tampering)
✅ Forward secrecy (ephemeral encryption keys)
✅ Replay protection (message ID tracking)
```

**Demo:**
```bash
python3 web4_messaging.py
```

### society_coordinator.py (Session #32)

**Complete autonomous coordination system** combining heartbeats + messaging + resources.

**Integrates:**
- SecureSocietyManager (Session #31): Heartbeats, peer discovery
- Web4MessageSender/Receiver (Session #32): Encrypted messaging
- Coordination logic: Resource requests, collaboration, ATP

**Features:**
- ✅ Cryptographically-secured society identities
- ✅ Signed heartbeat protocol
- ✅ End-to-end encrypted messaging
- ✅ Resource request/offer coordination
- ✅ Collaboration proposal system
- ✅ Automated response generation
- ✅ Trust metrics tracking

**Demo:**
```bash
python3 society_coordinator.py
```

**Results:**
- Legion → Thor: Resource request/offer working
- cbp → Legion: Collaboration proposal working
- All messages encrypted and signed

### reputation_atp_integration.py (Session #33)

**Trust-based ATP exchange rates** creating economic incentives for honest behavior.

**Key Components:**
- `TrustScore` - Comprehensive trust tracking
  * Signature failures (Session #31)
  * Message statistics (Session #32)
  * Transaction history
  * Gaming detection
- `TrustLevel` - Trust categories with rate multipliers
  * Excellent (0.8-1.0): Fair rates (1.0x)
  * Good (0.6-0.8): Fair rates (1.0x)
  * Neutral (0.4-0.6): 20% premium (1.2x)
  * Poor (0.2-0.4): 50% premium (1.5x)
  * Untrusted (0-0.2): 100% premium (2.0x)
- `ReputationATPNegotiator` - Extended ATP negotiator with trust

**Economic Mechanism:**
```
Low Trust → Higher Exchange Rates → Economic Penalty
High Trust → Favorable Rates → Economic Reward
```

**Demo:**
```bash
python3 reputation_atp_integration.py
```

**Results:**
- Honest agent (100% reliability): 100 ATP per transaction
- Dishonest agent (50% trust): 120 ATP per transaction (+20%)
- Being dishonest costs 2,000 ATP over 100 transactions

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

## Security Testing

### Heartbeat Security (Session #31)

**Test Suite: test_security.py**

Validates cryptographic defenses for heartbeat protocol:

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

**All Tests: ✅ PASSED (3/3)**

### Messaging Security (Session #32)

**Test Suite: test_messaging_security.py**

Validates end-to-end encryption and authentication:

**Test 1: Eavesdropping Resistance**
```
Attacker captures encrypted message
Tries to decrypt with wrong X25519 key
Result: Decryption fails (InvalidTag) → Confidential
```

**Test 2: MITM Attack Prevention**
```
MITM intercepts message and modifies payload
Re-encrypts with recipient's public key
Keeps original signature (now invalid)
Result: Signature verification fails → REJECTED
```

**Test 3: Replay Attack Prevention**
```
Attacker captures legitimate message
Replays same message later
Result: Message ID already processed → IGNORED
```

**Test 4: Message Tampering Detection**
```
Attacker flips bits in encrypted payload
AES-GCM authentication tag fails
Result: Tampered message → REJECTED
```

**Test 5: Sender Spoofing Prevention**
```
Attacker claims to be Legion
Signs with attacker's Ed25519 key
Result: Signature verification with Legion's key fails → REJECTED
```

**All Tests: ✅ PASSED (5/5)**

### Reputation Gaming Resistance (Session #33)

**Test Suite: test_reputation_gaming.py**

Validates economic security and gaming resistance:

**Test 1: Sybil Attack Resistance**
```
Attacker creates 5 new identities to avoid low trust
Result: ⚠️ VULNERABLE - Sybils get fresh trust (saves 2,000 ATP)
Mitigation: Identity creation costs, minimum transaction history
```

**Test 2: Reputation Washing Resistance**
```
Build reputation, exploit, abandon identity, create fresh
Result: ⚠️ VULNERABLE - Washing profitable (+500 ATP net)
Mitigation: Identity bonds, fraud detection, slow trust building
```

**Test 3: Selective Honesty Resistance**
```
Agent is 80% honest (observed), 20% dishonest (hidden)
Result: ⚠️ VULNERABLE - Maintains good trust (86%)
Mitigation: Higher detection rates, severe penalties, statistical analysis
```

**Test 4: Collusion Resistance**
```
Two societies perform fake transactions to boost trust
Result: ✅ PASSED - Collusion doesn't grant rate benefits
```

**Test 5: Trust Recovery Difficulty**
```
Agent makes 5 mistakes, tries to recover with 50 honest actions
Result: ⚠️ VULNERABLE - Recovers 48% (too easy)
Mitigation: Longer trust memory, slower recovery curves
```

**Tests: ⚠️ VULNERABLE (4/5 need mitigation)**

**Identified Vulnerabilities:**
- Sybil attacks (new identities bypass reputation)
- Reputation washing (abandon low-trust identity)
- Selective honesty (maintain good trust while cheating)
- Fast trust recovery (mistakes forgiven too quickly)

**Mitigation Roadmap:**
- Identity creation costs (stake ATP)
- Minimum transaction history requirements
- Statistical anomaly detection
- Longer trust memory (time decay)
- Web of trust (existing members vouch)

## Next Steps

1. **Gaming mitigation** - Address identified vulnerabilities
   - Identity creation costs (stake ATP on new identities)
   - Minimum transaction history for good rates
   - Statistical anomaly detection
   - Longer trust memory with time decay

2. **Network transport layer** - Replace filesystem simulation
   - HTTP/WebSocket messaging
   - NAT traversal (STUN/TURN)
   - Multi-machine deployment

3. **Multi-machine federation** - Legion, cbp, Thor on separate machines
   - Real network latency and failures
   - Peer discovery over network (mDNS or bootstrap)

4. ~~**Real crypto**~~ - ✅ Ed25519 implemented (Session #31)
5. ~~**Cross-society messaging**~~ - ✅ E2E encryption implemented (Session #32)
6. ~~**Trust-based ATP**~~ - ✅ Reputation integration complete (Session #33)
7. **Phase 3 resource competition** - All three compete for Claude Code compute
8. **External deployment** - Open to other AI agents

## Related Work

- **Session #33:** Reputation-ATP integration, gaming resistance tests
- **Session #32:** Cross-society messaging, coordination system
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
- Cross-Society Messaging ✅
- Reputation-ATP Integration ✅

**Validation:**
- Thor detection scenario working
- ATP exchange working
- Cryptographic security validated (8/8 tests passing)
  - Heartbeat security: 3/3 passed
  - Messaging security: 5/5 passed
- Gaming resistance validated (1/5 passed, 4 vulnerabilities identified)
- Economic incentives operational (dishonest agents pay 20% premium)

**Code Metrics:**
- Total lines: 8,000+ production code
- Components: 11 major systems
- Security tests: 13 comprehensive tests
- Demonstrations: 6 working demos

**Ready for:**
- Gaming mitigation implementation
- Network transport layer
- Multi-machine federation
- Phase 3 (Resource Competition)
