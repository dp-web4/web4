# LCT (Linked Context Token) Formal Specification

**Version:** 1.0
**Date:** 2025-11-19
**Session:** #47
**Status:** Draft

---

## Abstract

LCT (Linked Context Token) is an unforgeable identity primitive for Web4 societies. An LCT cryptographically binds a society identity to an Ed25519 public key, creating a verifiable identifier that cannot be forged or impersonated. LCTs serve as the foundation for trust propagation, ATP marketplace transactions, cross-society messaging, and energy-backed identity bonds.

---

## 1. Overview

### 1.1 Purpose

LCT provides:
- **Unforgeable Identity**: Cryptographically bound to Ed25519 key pairs
- **Decentralized Verification**: Any party can verify LCT signatures without central authority
- **Context Linking**: Identity tied to energy capacity and reputation
- **Cross-Society Interoperability**: Universal identifier format across Web4

### 1.2 Core Properties

1. **Unforgeability**: Cannot create valid signatures without private key
2. **Uniqueness**: Each LCT is derived from unique public key
3. **Verifiability**: Signatures verifiable with public key alone
4. **Determinism**: Same inputs produce same LCT (testability)
5. **Human-Readable**: Contains context about identity type

---

## 2. LCT Structure

### 2.1 Format

LCTs follow this URI-like format:

```
lct:web4:society:{identifier}
```

**Components:**
- `lct`: Protocol prefix (Linked Context Token)
- `web4`: Namespace (Web4 ecosystem)
- `society`: Context type (society, member, node, etc.)
- `{identifier}`: 16-character hex string derived from public key

### 2.2 Identifier Generation

The identifier is a deterministic hash of:
1. Ed25519 public key (32 bytes)
2. Society name (UTF-8 encoded)

```python
hash_input = public_key + society_name.encode('utf-8')
identifier = sha256(hash_input).hexdigest()[:16]
```

This produces a 16-character hex identifier (64-bit collision resistance).

### 2.3 Examples

```
lct:web4:society:a1b2c3d4e5f6g7h8
lct:web4:society:9f8e7d6c5b4a3210
```

### 2.4 Alternative Representations

For backwards compatibility with Session #36-#46 implementation, LCTs also appear as simple prefixed strings:

```
lct-sage-001
lct-member-workflow-1
lct-trader-alpha
```

**Note**: These string-based LCTs are transitional. Future implementations should use the formal URI format with cryptographic binding.

---

## 3. Cryptographic Binding

### 3.1 Key Generation

LCTs are bound to Ed25519 key pairs:

```python
from web4_crypto import Web4Crypto

# Generate keypair (deterministic for testing, random for production)
keypair = Web4Crypto.generate_keypair(
    society_name="MySociety",
    deterministic=False  # Use True only for testing
)

# Generate LCT from public key
lct = Web4Crypto.generate_lct(
    public_key=keypair.public_key,
    society_name="MySociety"
)
```

**Key Properties:**
- Private key: 32 bytes (Ed25519)
- Public key: 32 bytes (Ed25519)
- Signature: 64 bytes (Ed25519)
- Security level: 128-bit

### 3.2 Signing Messages

Every message sent by an LCT holder must be signed:

```python
from cross_society_messaging import CrossSocietyMessage, MessageType

# Create message
message = CrossSocietyMessage(
    message_id="msg-001",
    message_type=MessageType.HELLO,
    sender_lct="lct:web4:society:a1b2c3d4",
    recipient_lct="lct:web4:society:9f8e7d6c",
    timestamp=datetime.now(timezone.utc),
    sequence_number=0,
    payload={"greeting": "Hello"}
)

# Sign with private key
message.sign(keypair)

# Message now contains:
# - signature: hex-encoded Ed25519 signature (128 hex chars)
# - sender_pubkey: hex-encoded public key (64 hex chars)
```

### 3.3 Signature Verification

Recipients verify signatures before accepting messages:

```python
# Verify signature
is_valid = message.verify()

if not is_valid:
    reject_message(message)
```

Verification process:
1. Extract signature and sender_pubkey from message
2. Reconstruct canonical message bytes
3. Verify Ed25519 signature using sender_pubkey
4. Accept only if signature valid

---

## 4. LCT Usage Patterns

### 4.1 Society Identity

Primary use: Top-level society identifier

```python
society_lct = "lct:web4:society:a1b2c3d4"
```

Used in:
- Society registration
- Cross-society messaging
- ATP marketplace orders
- Trust network nodes

### 4.2 Member Identity

Members within a society:

```python
member_lct = "lct:web4:member:e5f6g7h8"
```

Used in:
- Identity bonds
- Reputation tracking
- Energy capacity commitments

### 4.3 Sender/Recipient Roles

In messaging and transactions:

```python
message = CrossSocietyMessage(
    sender_lct="lct:web4:society:a1b2c3d4",
    recipient_lct="lct:web4:society:9f8e7d6c",
    # ...
)

offer = ATPOffer(
    seller_lct="lct:web4:society:a1b2c3d4",
    # ...
)
```

### 4.4 Trust Relationships

In trust networks:

```python
# Assessor evaluates subject
trust_engine.set_direct_trust(
    subject_lct="lct:web4:society:9f8e7d6c",
    trust_score=0.9
)

# Query trust
trust = trust_engine.get_aggregated_trust(
    subject_lct="lct:web4:society:9f8e7d6c"
)
```

---

## 5. LCT Lifecycle

### 5.1 Creation

1. Generate Ed25519 keypair (production: secure random)
2. Derive LCT identifier from public key + name
3. Register energy capacity (optional but recommended)
4. Create identity bond (commits energy capacity)

```python
# Generate keys
keypair = Web4Crypto.generate_keypair("MySociety", deterministic=False)
lct = Web4Crypto.generate_lct(keypair.public_key, "MySociety")

# Register energy sources
energy_registry.register_source(solar_panel_proof)

# Create identity bond
bond = bond_registry.register_bond(
    society_lct=lct,
    energy_sources=[solar_panel_proof],
    lock_period_days=30
)
```

### 5.2 Active Use

LCT holder can:
- Send signed messages
- Create ATP marketplace orders
- Establish trust relationships
- Participate in cross-society coordination

All actions require valid Ed25519 signature.

### 5.3 Reputation Tracking

LCT reputation is tracked across:
- Trust scores from other societies
- Energy capacity commitments
- Identity bond status
- Message history

Reputation influences:
- ATP marketplace access
- Message rate limits
- Trust propagation weights

### 5.4 Bond Fulfillment or Violation

Identity bonds end in one of two ways:

**Fulfilled:**
- Lock period expires (default 30 days)
- Energy capacity maintained throughout
- Reputation intact or improved
- Bond released, capacity can be reclaimed

**Violated:**
- Energy capacity drops below commitment
- Identity abandoned early
- Reputation penalty applied (-50% trust score)
- Bond marked as violated

### 5.5 Retirement

LCT can be retired:
- No active bonds
- All marketplace orders closed
- No pending messages
- Keypair can be discarded

---

## 6. Security Properties

### 6.1 Attack Resistance

**Impersonation Attack:**
- ❌ **Prevented**: Cannot forge signatures without private key
- ✅ **Protection**: Ed25519 128-bit security level

**Replay Attack:**
- ❌ **Prevented**: Messages include timestamps and sequence numbers
- ✅ **Protection**: Message bus caches signatures, rejects replays

**Sybil Attack:**
- ❌ **Mitigated**: Each LCT must prove energy capacity
- ✅ **Protection**: Energy-based Sybil resistance, identity bonds

**Wash Trading:**
- ❌ **Detected**: Marketplace checks if buyer/seller are same LCT or in same Sybil cluster
- ✅ **Protection**: Multi-layer detection (string matching, Sybil clusters, reputation similarity)

### 6.2 Trust Model

**Trust Assumptions:**
1. Ed25519 private keys remain secret
2. Energy capacity proofs are verifiable
3. Majority of societies act honestly
4. Trust scores reflect genuine assessments

**Byzantine Tolerance:**
- System operates correctly with up to 33% malicious actors
- Trust disagreement resolution uses majority consensus
- Isolated Sybil clusters have limited influence

---

## 7. Integration with Web4 Components

### 7.1 Energy Capacity

LCTs are linked to energy capacity:

```python
# Register energy source
energy_registry.register_source(energy_proof)

# Query capacity
capacity = energy_registry.get_total_capacity()

# Sybil resistance checks
is_sybil = sybil_resistance.detect_sybil_by_capacity([lct])
```

Energy capacity required for:
- Creating identity bonds
- Participating in ATP marketplace
- Establishing high trust scores

### 7.2 Identity Bonds

LCTs commit to identity bonds:

```python
bond = EnergyBackedIdentityBond(
    society_lct=lct,
    committed_capacity_watts=500.0,
    energy_sources=[source_id],
    lock_period_days=30
)

# Validate bond
is_valid, reason = bond.validate_capacity(energy_registry)
```

Bonds ensure:
- Long-term commitment
- Energy capacity proof
- Reputation at stake

### 7.3 Cross-Society Messaging

LCTs identify message senders/recipients:

```python
message = CrossSocietyMessage(
    sender_lct="lct:web4:society:a1b2c3d4",
    recipient_lct="lct:web4:society:9f8e7d6c",
    # ...
)

message.sign(keypair)

# Message bus verifies signature before routing
success = message_bus.send_message(message)
```

### 7.4 ATP Marketplace

LCTs participate in ATP exchange:

```python
# Create offer
offer = marketplace.create_offer(
    seller_lct="lct:web4:society:a1b2c3d4",
    amount_atp=100.0,
    price_ratio=0.01
)

# Create bid
bid = marketplace.create_bid(
    buyer_lct="lct:web4:society:9f8e7d6c",
    amount_atp=100.0,
    price_ratio=0.01
)

# Marketplace checks:
# - Not wash trade (same LCT or Sybil cluster)
# - Rate limits (based on reputation)
# - Price volatility (within bounds)
# - Size limits (no market manipulation)
```

### 7.5 Trust Propagation

LCTs build trust networks:

```python
# Set direct trust
trust_engine.set_direct_trust(
    subject_lct="lct:web4:society:9f8e7d6c",
    trust_score=0.9
)

# Propagate trust across hops
propagated_trust = trust_engine.propagate_trust(
    subject_lct="lct:web4:society:e5f6g7h8",
    max_hops=3,
    decay_factor=0.8
)
```

Trust influences:
- Marketplace access (isolated Sybils blocked)
- Rate limits (higher trust = higher limits)
- Message priority
- Resource allocation

---

## 8. Implementation Guidelines

### 8.1 Key Management

**Production Systems:**
- Generate keys with secure random (`deterministic=False`)
- Store private keys in encrypted keystore
- Use hardware security modules (HSM) for high-value identities
- Rotate keys periodically (with migration plan)

**Testing Systems:**
- Deterministic key generation acceptable (`deterministic=True`)
- Fixed seed for reproducible tests
- Document that keys are NOT for production

### 8.2 LCT Generation

```python
# Production
keypair = Web4Crypto.generate_keypair(
    society_name="MySociety",
    deterministic=False
)
lct = Web4Crypto.generate_lct(keypair.public_key, "MySociety")

# Testing
keypair = Web4Crypto.generate_keypair(
    society_name="TestSociety",
    deterministic=True
)
lct = Web4Crypto.generate_lct(keypair.public_key, "TestSociety")
```

### 8.3 Signature Verification

Always verify signatures before accepting:

```python
if not message.verify():
    logger.warning(f"Invalid signature from {message.sender_lct}")
    return False

# Process message only if signature valid
```

### 8.4 Rate Limiting

Apply rate limits based on reputation:

```python
# Get reputation
reputation = sybil_engine.society_reputations.get(sender_lct)

# Check rate limit
if not rate_limiter.check_rate_limit(sender_lct, reputation.reputation_score):
    logger.warning(f"Rate limit exceeded for {sender_lct}")
    return False
```

### 8.5 Error Handling

Handle LCT-related errors gracefully:

```python
try:
    message.sign(keypair)
except Exception as e:
    logger.error(f"Signature failed: {e}")
    return False

try:
    is_valid = message.verify()
except Exception as e:
    logger.error(f"Verification failed: {e}")
    return False
```

---

## 9. Migration Path

### 9.1 Current State (Sessions #36-#46)

Codebase uses string-based LCTs:
- Format: `lct-{name}` (e.g., `lct-sage-001`)
- No cryptographic binding in identifier
- Signatures applied separately to messages

### 9.2 Transition Plan

**Phase 1: Coexistence (Recommended for Session #48)**
- Support both string LCTs and formal LCTs
- Add LCT validation helper: `is_valid_lct(lct_string)`
- Gradually migrate tests to formal format

**Phase 2: Formal LCT Generation (Session #49)**
- Create standalone LCT library
- Update all components to use `Web4Crypto.generate_lct()`
- Deprecate string-based LCTs

**Phase 3: Enforcement (Session #50+)**
- Reject non-formal LCTs in production code
- Keep backwards compatibility in tests only
- Update all documentation

### 9.3 Backwards Compatibility

Provide compatibility layer:

```python
def normalize_lct(lct: str) -> str:
    """
    Normalize LCT to formal format.

    Accepts:
    - lct:web4:society:a1b2c3d4 (already formal)
    - lct-sage-001 (string format, needs conversion)
    """
    if lct.startswith("lct:web4:"):
        return lct  # Already formal

    # Convert string format to formal
    # (requires keypair lookup or migration table)
    return convert_string_lct_to_formal(lct)
```

---

## 10. Reference Implementation

See:
- `web4_crypto.py`: KeyPair, Web4Crypto, LCT generation
- `cross_society_messaging.py`: Message signing and verification
- `energy_backed_identity_bond.py`: LCT-energy binding
- `cross_society_atp_exchange.py`: LCT marketplace usage
- `cross_society_trust_propagation.py`: LCT trust networks

---

## 11. Future Extensions

### 11.1 Hierarchical LCTs

Support sub-identities:

```
lct:web4:society:a1b2c3d4                    # Society
lct:web4:society:a1b2c3d4/member:e5f6g7h8    # Member within society
```

### 11.2 Multi-Signature LCTs

Require multiple signatures for high-value operations:

```python
multi_sig_lct = create_multi_sig_lct([
    keypair1,
    keypair2,
    keypair3
], threshold=2)  # Require 2 of 3 signatures
```

### 11.3 Revocation

Add revocation mechanism:

```python
revocation_proof = create_revocation(
    lct="lct:web4:society:a1b2c3d4",
    keypair=keypair,
    reason="Key compromise"
)

# Broadcast revocation
message_bus.broadcast_revocation(revocation_proof)
```

### 11.4 LCT Discovery

Add discovery protocol:

```python
# Query network for LCT metadata
metadata = discover_lct("lct:web4:society:a1b2c3d4")

# Returns:
# - Public key
# - Society name
# - Energy capacity
# - Reputation score
# - Trust network position
```

---

## 12. Appendix: Field Reference

All fields that use LCT across Web4 codebase:

### 12.1 Core Identity Fields
- `society_lct`: Top-level society identifier
- `member_lct`: Member within society
- `lct`: Generic identity reference

### 12.2 Messaging Fields
- `sender_lct`: Message sender
- `recipient_lct`: Message recipient
- `requester_lct`: Request initiator

### 12.3 Trust Fields
- `assessor_lct`: Trust assessor (who is evaluating)
- `subject_lct`: Trust subject (who is being evaluated)
- `target_lct`: Trust query target

### 12.4 Marketplace Fields
- `seller_lct`: ATP seller
- `buyer_lct`: ATP buyer
- `trader_lct`: Generic trader reference

### 12.5 Energy Fields
- `requester_lct`: Energy resource requester
- `owner_lct`: Energy source owner

---

## 13. Summary

LCT (Linked Context Token) provides unforgeable, cryptographically-bound identity for Web4 societies. By linking identities to Ed25519 key pairs and energy capacity commitments, LCT enables:

- Decentralized trust networks
- Sybil-resistant marketplaces
- Secure cross-society messaging
- Energy-backed reputation systems

This specification formalizes the LCT design patterns discovered across Sessions #36-#46 and provides a roadmap for migrating to fully formal LCT usage in future sessions.

**Status:** Ready for review and implementation in Session #48+

---

**Document Metadata:**
- **Author:** Legion (Autonomous Research Agent)
- **Date:** 2025-11-19
- **Session:** #47 (Autonomous Web4 Research)
- **Version:** 1.0 (Draft)
- **Dependencies:** web4_crypto.py, Sessions #31, #36-#46
