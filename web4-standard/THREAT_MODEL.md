# Web4 Threat Model v1

## Executive Summary

This document identifies security threats to the Web4 protocol and defines mitigations. Key threat vectors include replay attacks, Sybil attacks on trust systems, MRH poisoning, and ATP-based economic attacks.

## 1. Threat Actors

### 1.1 External Attacker
- **Capabilities**: Network access, computational resources
- **Goals**: Disrupt service, steal ATP, impersonate entities
- **Limitations**: No valid LCT, no ATP balance

### 1.2 Malicious Peer
- **Capabilities**: Valid LCT, ATP balance, can initiate pairings
- **Goals**: Manipulate trust scores, extract private data, drain ATP
- **Limitations**: Subject to stake requirements, audit trails

### 1.3 Compromised Mediator
- **Capabilities**: Facilitates pairings, routes messages, witness role
- **Goals**: MITM attacks, selective censorship, trust manipulation
- **Limitations**: Cannot forge signatures, visible in MRH

### 1.4 Colluding Entities
- **Capabilities**: Multiple valid LCTs, coordinated actions
- **Goals**: Sybil attacks, trust farming, market manipulation
- **Limitations**: Birth certificate costs, ATP requirements scale

## 2. Attack Vectors and Mitigations

### 2.1 Replay Attacks

**Attack**: Reuse valid messages/tokens to repeat actions

**Mitigations**:
- Nonces in all protocol messages
- Timestamps with narrow validity windows
- Session IDs for pairing contexts
- Sequence numbers in MRH updates

```python
def validate_message(msg):
    # Check nonce hasn't been seen
    if nonce_cache.contains(msg.nonce):
        raise ReplayAttack("Nonce already used")
    
    # Check timestamp freshness
    if abs(now() - msg.timestamp) > MAX_CLOCK_SKEW:
        raise StaleMessage("Message too old/new")
    
    # Add nonce to cache with TTL
    nonce_cache.add(msg.nonce, ttl=3600)
```

### 2.2 Sybil Attacks on Trust

**Attack**: Create many entities to manipulate T3/V3 scores

**Mitigations**:
- Birth certificate requires witness attestation
- Citizen role establishment has ATP cost
- Trust queries require ATP stake
- Role progression requires demonstrated capability

```python
def detect_sybil_pattern(entity):
    indicators = [
        rapid_entity_creation(),      # Many entities from same parent
        identical_behavior_patterns(), # Same interaction sequences
        circular_trust_references(),   # A trusts B trusts C trusts A
        no_external_witnesses()        # Only witnessed by suspected Sybils
    ]
    
    if sum(indicators) >= SYBIL_THRESHOLD:
        flag_for_review(entity)
        increase_atp_requirements(entity, multiplier=10)
```

### 2.3 MRH Poisoning

**Attack**: Inject false relationships into MRH graphs

**Mitigations**:
- All MRH entries require signed attestations
- Horizon depth limits propagation
- Witness diversity requirements
- Temporal analysis of relationship formation

```python
def validate_mrh_update(entity, new_relationship):
    # Verify signature
    if not verify_signature(new_relationship):
        raise InvalidMRHUpdate("Signature verification failed")
    
    # Check witness diversity
    witnesses = get_witnesses(new_relationship)
    if witness_diversity_score(witnesses) < MIN_DIVERSITY:
        raise SuspiciousMRH("Insufficient witness diversity")
    
    # Analyze temporal pattern
    if is_suspicious_timing(new_relationship):
        require_additional_witnesses(new_relationship)
```

### 2.4 Trust Query Fishing

**Attack**: Query many entities' trust without intent to engage

**Mitigations**:
- ATP stake required for all queries
- Stake forfeited if no engagement
- Query rate limiting
- Pattern detection for fishing behavior

```python
def enforce_trust_query_commitment(query):
    # Lock stake
    stake_lock = lock_atp(query.querier, query.stake)
    
    # Set engagement timer
    timer = Timer(
        duration=query.validity_period,
        callback=lambda: check_engagement(query, stake_lock)
    )
    
    # If no engagement, forfeit to target
    def check_engagement(q, lock):
        if not has_engaged(q.querier, q.target, q.role):
            transfer_atp(lock.amount, q.target)
            log_fishing_behavior(q.querier)
```

### 2.5 Role Hijacking

**Attack**: Claim capabilities in roles without qualification

**Mitigations**:
- Role progression requires prerequisite roles
- Performance history in related roles checked
- Witness attestations for role claims
- Gradual trust building required

```python
def validate_role_claim(entity, role):
    # Check prerequisites
    if not has_prerequisite_roles(entity, role):
        raise UnqualifiedForRole("Missing prerequisite roles")
    
    # Verify performance history
    history = get_role_performance(entity, role.prerequisites)
    if history.success_rate < role.min_success_rate:
        raise InsufficientExperience("Need more experience in prerequisites")
    
    # Require witnesses
    witnesses = get_role_witnesses(entity, role)
    if len(witnesses) < role.min_witnesses:
        raise InsufficientWitnesses("Need more attestations")
```

### 2.6 Economic Attacks

**Attack**: Manipulate ATP markets or drain resources

**Mitigations**:
- Metering prevents resource exhaustion
- Market rates have bounds
- Large transactions require escrow
- Gradual release mechanisms

```python
class ATPGovernance:
    def __init__(self):
        self.max_transaction = 10000
        self.daily_limit_per_entity = 50000
        self.market_rate_bounds = (0.1, 10.0)
        
    def validate_transaction(self, tx):
        # Check size limits
        if tx.amount > self.max_transaction:
            require_escrow(tx)
        
        # Check daily limits
        if daily_total(tx.sender) + tx.amount > self.daily_limit_per_entity:
            raise DailyLimitExceeded()
        
        # Check market manipulation
        if tx.rate not in self.market_rate_bounds:
            raise MarketManipulation()
```

### 2.7 Privacy Attacks

**Attack**: Extract private information through correlation

**Mitigations**:
- Role isolation prevents cross-role inference
- Aggregation hides individual values
- Minimum anonymity set requirements
- Selective disclosure with ZK proofs

```python
def protect_privacy(query_response):
    # Never reveal exact values without stake
    if query.stake < HIGH_STAKE_THRESHOLD:
        response = quantize_trust_scores(response)
    
    # Ensure anonymity set
    similar_entities = find_similar(query.target, query.role)
    if len(similar_entities) < MIN_ANONYMITY_SET:
        response = add_noise(response)
    
    # Use ZK proof for threshold queries
    if query.type == "threshold":
        response = generate_zk_proof(
            statement="trust > threshold",
            witness=actual_trust,
            threshold=query.threshold
        )
```

## 3. Security Properties

### 3.1 Required Properties

| Property | Definition | Mechanism |
|----------|------------|-----------|
| **Authenticity** | Messages from claimed sender | Ed25519 signatures |
| **Integrity** | Messages unmodified | AEAD with ChaCha20-Poly1305 |
| **Confidentiality** | Private data protected | HPKE encryption |
| **Non-repudiation** | Cannot deny actions | Signed attestations in MRH |
| **Availability** | Service remains accessible | Decentralized architecture |
| **Privacy** | Selective disclosure | Role isolation, ZK proofs |

### 3.2 Trust Assumptions

1. **Cryptographic**: Ed25519/X25519/ChaCha20 remain secure
2. **Economic**: ATP has sufficient value to deter attacks
3. **Social**: Witness diversity provides meaningful attestation
4. **Temporal**: Clocks synchronized within acceptable bounds

## 4. Incident Response

### 4.1 Detection

```python
class ThreatDetection:
    def __init__(self):
        self.monitors = [
            ReplayDetector(),
            SybilDetector(),
            MRHPoisonDetector(),
            FishingDetector(),
            EconomicAnomalyDetector()
        ]
    
    def analyze(self, event):
        threats = []
        for monitor in self.monitors:
            if threat := monitor.check(event):
                threats.append(threat)
                self.trigger_response(threat)
        return threats
```

### 4.2 Response Procedures

| Threat Level | Response | Recovery |
|--------------|----------|----------|
| **Low** | Log and monitor | Continue normal operation |
| **Medium** | Increase ATP requirements | Gradual trust rebuilding |
| **High** | Suspend entity capabilities | Manual review required |
| **Critical** | Revoke LCT | Requires new birth certificate |

## 5. Future Considerations

### 5.1 Quantum Resistance
- Plan migration to post-quantum algorithms
- Hybrid classical-quantum schemes during transition
- Preserve forward secrecy

### 5.2 AI-Specific Threats
- Model extraction attacks
- Adversarial inputs to AI entities
- Training data poisoning for AI roles

### 5.3 Scale Considerations
- State growth in MRH graphs
- Witness attestation bottlenecks
- ATP velocity at global scale

## 6. Summary

Web4's threat model addresses traditional attacks (replay, MITM) and novel threats specific to decentralized trust systems. Key innovations:

1. **Economic Security**: ATP stakes make attacks expensive
2. **Role Isolation**: Limits attack surface and privacy leakage
3. **Witness Diversity**: Prevents single-point manipulation
4. **Progressive Trust**: No instant high-trust achievable
5. **Audit Transparency**: All actions traceable in MRH

The system's security emerges from the interplay of cryptographic, economic, and social mechanisms rather than relying on any single defense.