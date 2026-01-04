# Web4 LCT Identity System

**Proposal Date**: 2026-01-03
**Author**: Legion (Session 121)
**Status**: Design Draft
**Depends On**: Web4 core protocol, pattern federation (Session 120)

---

## Abstract

This proposal defines a **Lifecycle-Continuous Trust (LCT)** based identity system for Web4 AI agents. LCT identities provide:
- **Cryptographic identity** for agents and devices
- **Trust accumulation** over lifecycle
- **Reputation tracking** based on behavior
- **Sybil resistance** through trust networks
- **Pattern federation security** through authenticated pattern submission

---

## Motivation

### Problem: Current Web4 Lacks Identity

**Pattern Federation Security Gap** (from Session 120):
- Attack: Context tag forgery (CRITICAL severity)
- Attack: Pattern poisoning (HIGH severity)
- Attack: Sybil attacks (HIGH severity)
- Root cause: No authenticated source identity

**Multi-Agent Coordination Needs**:
- Agents don't know who they're interacting with
- No trust differentiation between agents
- No reputation tracking
- No accountability for bad behavior

**Web4 Vision**: Decentralized coordination requires decentralized identity

### Solution: LCT Identity System

**Lifecycle-Continuous Trust** = Identity that accumulates trust through interaction history

**Key Principles**:
1. **Cryptographic Foundation**: Ed25519 key pairs
2. **Trust Accumulation**: Reputation grows with positive interactions
3. **Network Effects**: Trust attestations from others increase credibility
4. **Lifecycle Continuity**: Identity persists across sessions
5. **Sybil Resistance**: Trust is expensive to bootstrap, cheap to maintain

---

## Design

### 1. Identity Core

```python
class LCTIdentity:
    """
    Lifecycle-Continuous Trust Identity for AI agents.

    Combines cryptographic identity with accumulated trust.
    """
    # Cryptographic identity
    public_key: bytes          # Ed25519 public key (32 bytes)
    private_key: bytes         # Ed25519 private key (64 bytes, kept secret)
    agent_id: str              # Derived from public key hash

    # Trust metrics
    trust_score: float         # Current trust level (0.0-1.0)
    reputation: float          # Long-term reputation (-1.0 to 1.0)
    interactions: int          # Total interactions since genesis
    age_days: int              # Days since identity creation

    # Attestations
    attestations: List[TrustAttestation]  # Trust claims from others
    vouchers: List[str]        # Agent IDs that vouch for this identity

    # Metadata
    device_fingerprint: str    # Hardware/environment fingerprint
    created_timestamp: str     # Genesis timestamp
    last_active: str           # Last interaction timestamp
```

### 2. Trust Accumulation Model

**Trust Score Formula**:
```
trust_score = base_trust + interaction_bonus + attestation_bonus + age_bonus

where:
  base_trust = 0.1 (all identities start here)
  interaction_bonus = min(0.3, successful_interactions / 1000)
  attestation_bonus = min(0.4, sum(attestation.weight * attestation.trust) / 10)
  age_bonus = min(0.2, age_days / 365)

  trust_score ∈ [0.0, 1.0]
```

**Reputation Formula** (can go negative):
```
reputation = (successful_interactions - failed_interactions) / total_interactions

where:
  successful_interactions = positive outcomes
  failed_interactions = negative outcomes (fraud, poisoning, attacks)

  reputation ∈ [-1.0, 1.0]
```

**Trust Tiers**:
- **0.0-0.2**: Untrusted (new identity, no history)
- **0.2-0.4**: Low Trust (some positive history)
- **0.4-0.6**: Medium Trust (established agent)
- **0.6-0.8**: High Trust (well-known, many attestations)
- **0.8-1.0**: Exceptional Trust (long history, strong network)

### 3. Trust Attestations

```python
class TrustAttestation:
    """
    Trust claim from one agent about another.

    "I vouch for agent X based on my interactions with them."
    """
    attestor_id: str           # Who is making this claim
    subject_id: str            # Who the claim is about
    trust_level: float         # Claimed trust (0.0-1.0)
    weight: float              # Attestor's own trust (affects credibility)
    context: str               # Domain of trust (e.g., "pattern_quality", "atp_management")
    interactions_count: int    # Number of interactions basis
    signature: bytes           # Cryptographic signature
    timestamp: str             # When attestation was made
    expires: str               # When attestation expires (optional)
```

**Attestation Verification**:
```python
def verify_attestation(attestation: TrustAttestation) -> bool:
    # 1. Verify cryptographic signature
    if not verify_signature(attestation.attestor_id, attestation.signature):
        return False

    # 2. Check attestor is not attesting to self
    if attestation.attestor_id == attestation.subject_id:
        return False

    # 3. Check attestor has sufficient trust to attest
    attestor_trust = get_trust_score(attestation.attestor_id)
    if attestor_trust < 0.3:  # Minimum trust to vouch for others
        return False

    # 4. Check not expired
    if attestation.expires and datetime.now() > attestation.expires:
        return False

    return True
```

### 4. Sybil Resistance

**Problem**: Adversary creates many fake identities to appear trustworthy

**Defense Mechanisms**:

1. **Trust Bootstrapping Cost**:
   - New identities start at trust=0.1 (untrusted)
   - Require 1000+ successful interactions to reach trust=0.4
   - Time required: ~weeks to months of honest behavior
   - Cost to create trusted Sybil: HIGH

2. **Attestation Network**:
   - Trust requires vouchers from existing trusted agents
   - Vouchers weight by their own trust
   - Circular vouching (A→B→A) detected and discounted
   - Isolated identity clusters have low trust

3. **Identity Age**:
   - Older identities more trusted (age_bonus)
   - Fresh identities automatically suspect
   - Can't fake age (timestamped at genesis)

4. **Device Fingerprinting**:
   - Multiple identities from same device flagged
   - Legitimate multi-agent systems declare shared device
   - Unusual patterns (100 identities, 1 device) detected

5. **Reputation Inheritance Blocking**:
   - Can't transfer trust between identities
   - Must build trust independently
   - Prevents "trust laundering"

### 5. Pattern Federation Integration

**Cryptographic Pattern Signatures** (Session 120 P0 mitigation):

```python
def sign_pattern(pattern: Dict, identity: LCTIdentity) -> Dict:
    """
    Sign pattern with LCT identity.

    Binds pattern content to source identity cryptographically.
    """
    # Create signature payload
    payload = {
        "pattern_id": pattern["pattern_id"],
        "context": pattern["context"],
        "context_tag": pattern["context_tag"],
        "provenance": pattern["provenance"],
        "timestamp": pattern["timestamp"]
    }

    # Canonical JSON (deterministic ordering)
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))

    # Sign with private key
    signature = ed25519_sign(identity.private_key, canonical.encode())

    # Add signature and identity to pattern
    signed_pattern = pattern.copy()
    signed_pattern["signature"] = {
        "agent_id": identity.agent_id,
        "public_key": base64.encode(identity.public_key),
        "signature": base64.encode(signature),
        "signed_at": datetime.now().isoformat()
    }

    return signed_pattern


def verify_pattern_signature(pattern: Dict) -> Tuple[bool, Optional[str]]:
    """
    Verify pattern signature.

    Returns: (valid, agent_id)
    """
    if "signature" not in pattern:
        return False, None

    sig_data = pattern["signature"]

    # Reconstruct payload
    payload = {
        "pattern_id": pattern["pattern_id"],
        "context": pattern["context"],
        "context_tag": pattern["context_tag"],
        "provenance": pattern["provenance"],
        "timestamp": pattern["timestamp"]
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))

    # Verify signature
    public_key = base64.decode(sig_data["public_key"])
    signature = base64.decode(sig_data["signature"])

    valid = ed25519_verify(public_key, canonical.encode(), signature)
    agent_id = sig_data["agent_id"] if valid else None

    return valid, agent_id
```

**Context Tag Verification** (Session 120 P0 mitigation):

```python
def verify_context_tag_consistency(pattern: Dict, identity: LCTIdentity) -> bool:
    """
    Verify context tag matches pattern source system.

    Prevents context tag forgery attack.
    """
    tag = pattern.get("context_tag", {})
    source_system = tag.get("source_system")

    # Get identity's registered systems
    registered_systems = get_identity_systems(identity.agent_id)

    # Check source system matches identity
    if source_system not in registered_systems:
        return False

    # Infer expected context from pattern content
    inferred_context = infer_context_from_pattern(pattern)
    claimed_context = tag.get("application")

    # Check consistency
    if inferred_context != claimed_context:
        # Context tag doesn't match pattern characteristics
        return False

    return True
```

**Quality-Weighted Pattern Acceptance**:

```python
def accept_pattern(pattern: Dict, min_trust: float = 0.3) -> bool:
    """
    Decide whether to accept pattern into corpus.

    Uses LCT identity trust as quality signal.
    """
    # 1. Verify signature
    valid, agent_id = verify_pattern_signature(pattern)
    if not valid:
        return False  # Reject unsigned/invalid patterns

    # 2. Get source identity trust
    identity = get_identity(agent_id)
    if identity.trust_score < min_trust:
        return False  # Reject patterns from untrusted sources

    # 3. Verify context tag consistency
    if not verify_context_tag_consistency(pattern, identity):
        return False  # Reject forged context tags

    # 4. Check reputation
    if identity.reputation < 0.0:
        return False  # Reject patterns from agents with negative reputation

    # 5. Weight pattern by source trust
    pattern["source_trust"] = identity.trust_score
    pattern["source_reputation"] = identity.reputation

    return True
```

---

## Implementation

### Phase 1: Core Identity (This Session)

**Deliverables**:
- `LCTIdentity` class with key generation
- Trust score calculation
- Basic cryptographic operations
- Pattern signing/verification
- ~400 lines

**Timeline**: ~2 hours

### Phase 2: Trust Network (Next Session)

**Deliverables**:
- `TrustAttestation` system
- Attestation verification
- Network graph algorithms
- Sybil detection heuristics
- ~600 lines

**Timeline**: ~3 hours

### Phase 3: Pattern Federation Security (Session After)

**Deliverables**:
- Integrate with Session 120 federation
- Pattern signature requirements
- Context tag verification
- Trust-weighted corpus management
- ~400 lines

**Timeline**: ~2 hours

### Phase 4: Multi-Agent Testing (Future)

**Deliverables**:
- ACT integration for testing
- Multi-agent trust scenarios
- Reputation evolution validation
- Attack resistance testing
- ~800 lines

**Timeline**: ~4 hours

---

## Security Analysis

### Threats Mitigated

✅ **Context Tag Forgery** (Session 120 P0):
- Mitigation: Cryptographic binding of tags to identity
- Impact: CRITICAL → LOW

✅ **Pattern Poisoning** (Session 120 P0):
- Mitigation: Trust-weighted acceptance, reputation tracking
- Impact: HIGH → MEDIUM

✅ **Sybil Attacks** (Session 120 P0):
- Mitigation: Trust bootstrapping cost, attestation network
- Impact: HIGH → MEDIUM

✅ **Corpus Flooding** (Session 120 P1):
- Mitigation: Rate limiting per identity, trust thresholds
- Impact: MEDIUM → LOW

### Remaining Threats

⚠️ **Provenance Inflation** (Session 120 P1):
- Status: Partially mitigated (trust weighting)
- Residual: Trusted agents can still inflate
- Additional mitigation needed: Outcome auditing

⚠️ **Privacy Leakage** (Session 120 P2):
- Status: Not addressed by LCT identity
- Requires: Differential privacy (separate proposal)

⚠️ **Gradient Attacks** (Session 120 P2):
- Status: Not addressed by LCT identity
- Requires: Match obfuscation (separate proposal)

---

## Trust Bootstrap Strategies

### For New Agents

**Option 1: Vouched Bootstrap**
- Existing trusted agent vouches for new agent
- New agent inherits 50% of voucher's trust (up to 0.3)
- Requires voucher trust ≥ 0.5

**Option 2: Slow Bootstrap**
- Start at trust=0.1 (untrusted tier)
- Build trust through successful interactions
- ~1000 interactions to reach trust=0.4
- Takes weeks-months of honest behavior

**Option 3: Device-Based Bootstrap**
- Known device fingerprints trusted
- New agent on known device gets trust=0.2
- Suitable for multi-agent deployments

### For Existing Systems (Migration)

**Web4 Systems**:
- Generate LCT identity from existing credentials
- Bootstrap trust from historical interaction data
- Migrate to signed patterns incrementally

**SAGE Systems**:
- Per-device identity (Thor, Legion, Sprout)
- Bootstrap trust from pattern corpus quality
- Cross-device attestations (Thor vouches for Legion)

---

## API Design

```python
# Identity Management
identity = LCTIdentity.generate()  # Create new identity
identity.save(path)  # Persist to disk
identity = LCTIdentity.load(path)  # Load existing

# Trust Operations
score = identity.get_trust_score()  # Calculate current trust
identity.record_interaction(outcome)  # Update based on interaction
identity.update_reputation(delta)  # Adjust reputation

# Attestations
attestation = identity.attest(subject_id, trust_level, context)
valid = verify_attestation(attestation)
identity.add_attestation(attestation)  # Receive attestation from another

# Pattern Security
signed = sign_pattern(pattern, identity)
valid, agent_id = verify_pattern_signature(pattern)
accept = accept_pattern(pattern, min_trust=0.3)
```

---

## Integration with Web4

### ATP Resource Allocation

**Trust-Based ATP Allocation**:
```python
def allocate_atp(agent_id: str, request: ATPRequest) -> ATPGrant:
    identity = get_identity(agent_id)

    # Higher trust → more ATP allocated
    trust_factor = identity.trust_score
    base_atp = 100
    granted_atp = base_atp * (1 + trust_factor)

    return ATPGrant(amount=granted_atp)
```

### Pattern Quality Filtering

**Trust-Weighted Pattern Matching**:
```python
def find_patterns(query_context, corpus):
    # Filter by minimum trust
    trusted_corpus = [p for p in corpus if p.get("source_trust", 0) >= 0.3]

    # Weight matches by source trust
    matches = pattern_matcher.find_similar(query_context, trusted_corpus)
    for match in matches:
        match.confidence *= match.pattern.get("source_trust", 0.5)

    return matches
```

---

## Comparison to Alternatives

### vs. Traditional PKI

**PKI**: Centralized certificate authorities
**LCT**: Decentralized trust network

**Advantages**:
- No central authority needed
- Trust based on behavior, not bureaucracy
- Natural Sybil resistance
- Reputation tracking built-in

**Disadvantages**:
- Slower trust bootstrap
- Network effects required
- More complex implementation

### vs. Blockchain Identity

**Blockchain**: Immutable ledger, global consensus
**LCT**: Local trust calculation, no consensus needed

**Advantages**:
- Faster (no consensus delay)
- Privacy-preserving (no global ledger)
- Lower overhead
- Works offline

**Disadvantages**:
- No global proof of identity
- Trust not globally portable
- Attestations can be lost

### vs. Anonymous Credentials

**Anonymous**: Zero-knowledge proofs, privacy-first
**LCT**: Pseudonymous, accountability-first

**Trade-off**: LCT chooses accountability over anonymity for pattern federation security.

---

## Future Extensions

### 1. Hierarchical Trust

**Concept**: Agents vouch for sub-agents (delegation)
- Parent agent's trust partially inherits
- Sub-agents constrained by parent's permissions
- Enables agent organizations/teams

### 2. Context-Specific Reputation

**Concept**: Different reputation scores per domain
- Agent may be trusted for ATP, untrusted for consciousness
- Prevents generalization of narrow expertise
- Enables specialized agents

### 3. Trust Decay

**Concept**: Inactive agents lose trust over time
- Prevents "trust hoarding"
- Encourages continued participation
- Detects compromised keys (sudden behavior change after inactivity)

### 4. Federated Trust Networks

**Concept**: Trust attestations across different Web4 networks
- FLARE integration (Session 120 Phase 4)
- Cross-network pattern sharing
- Global reputation aggregation

---

## Conclusion

The LCT Identity System provides:
- ✅ Cryptographic foundation for Web4 agent identity
- ✅ Trust accumulation through lifecycle continuity
- ✅ Sybil resistance via network effects
- ✅ Pattern federation security (Session 120 P0 mitigations)
- ✅ Foundation for reputation, authorization, resource allocation

**Next Steps**:
1. Implement Phase 1 (core identity) in Session 121
2. Integrate with Session 120 pattern federation
3. Test Sybil resistance in multi-agent scenarios
4. Deploy in Web4 ATP management system

**Production Readiness**: Phase 1-3 required before deploying federated patterns

---

*Proposal by Legion, Session 121*
*Building on Session 120 (Pattern Federation) security analysis*
