# Aliveness Verification Protocol (AVP)

**Version**: 1.0.0
**Date**: 2026-01-04
**Status**: Draft
**Authors**: dp (human), Claude Opus 4.5

---

## Abstract

This document specifies the Aliveness Verification Protocol (AVP), a mechanism for proving that an LCT (Linked Context Token) currently has access to its bound hardware. AVP separates **identity persistence** (the LCT's accumulated data and experience) from **aliveness** (proof of current hardware binding), enabling external entities to make autonomous trust decisions when hardware binding is lost or changed.

---

## 1. Motivation

### 1.1 The Problem

Hardware-bound LCTs create unforgeable identity anchors via TPM2 or TrustZone. However, hardware can be:
- Destroyed (permanent loss)
- Replaced (upgrade, failure)
- Inaccessible (network partition, theft)
- Compromised (physical attack)

When hardware binding is lost, two things must be distinguished:
1. **Identity/Experience (DNA)**: The LCT's accumulated history, skills, and knowledge
2. **Aliveness**: Proof that the entity currently controls its bound hardware

### 1.2 The Insight

> *"Aliveness begins at the point where identity and its accumulated relationships are unique, non-transferable, and permanently perishable."*

Identity can persist (DNA survives). Relationships and trust require ongoing proof of aliveness. External entities—not the LCT itself—decide how to handle aliveness verification failure.

### 1.3 Design Goals

1. **Separation of concerns**: Identity survives; trust is negotiated
2. **External entity autonomy**: Verifiers decide their own trust policies
3. **Graceful degradation**: Failed verification ≠ binary rejection
4. **Opt-in verification**: Not every interaction requires aliveness proof
5. **Minimal protocol**: Simple nonce-signature challenge

---

## 2. Protocol Specification

### 2.1 Aliveness Challenge

An **Aliveness Challenge** is a request from an external entity to prove current hardware access.

```
┌─────────────────┐                    ┌─────────────────┐
│  External Entity │                    │   Target LCT    │
│   (Verifier)     │                    │   (Prover)      │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │  1. AlivenessChallenge               │
         │  {                                   │
         │    nonce: bytes[32],                 │
         │    timestamp: ISO8601,               │
         │    challenge_id: uuid,               │
         │    expires_at: ISO8601               │
         │  }                                   │
         │─────────────────────────────────────>│
         │                                      │
         │                                      │ 2. Sign nonce with
         │                                      │    hardware-bound key
         │                                      │
         │  3. AlivenessProof                   │
         │  {                                   │
         │    challenge_id: uuid,               │
         │    signature: bytes,                 │
         │    public_key: PEM,                  │
         │    hardware_type: "tpm2"|"trustzone",│
         │    timestamp: ISO8601                │
         │  }                                   │
         │<─────────────────────────────────────│
         │                                      │
         │ 4. Verify signature                  │
         │    against LCT's public_key          │
         │                                      │
```

### 2.2 Data Structures

#### AlivenessChallenge

```python
@dataclass
class AlivenessChallenge:
    """Challenge sent by verifier to prove aliveness."""
    nonce: bytes              # 32 random bytes
    timestamp: datetime       # When challenge was created
    challenge_id: str         # UUID for correlation
    expires_at: datetime      # Challenge expiration (recommended: 60 seconds)

    # Optional context
    verifier_lct_id: str      # Who is asking (for audit trail)
    purpose: str              # Why verification is requested
```

#### AlivenessProof

```python
@dataclass
class AlivenessProof:
    """Proof returned by prover demonstrating hardware access."""
    challenge_id: str         # Correlates to challenge
    signature: bytes          # Nonce signed by hardware-bound key
    public_key: str           # PEM-encoded public key (must match LCT)
    hardware_type: str        # "tpm2", "trustzone", or "software"
    timestamp: datetime       # When proof was generated

    # Optional attestation
    attestation_quote: str    # TPM quote or TrustZone attestation (optional)
    pcr_values: Dict[int, str] # PCR state at signing time (optional)
```

#### AlivenessVerificationResult

```python
@dataclass
class AlivenessVerificationResult:
    """Result of verifying an aliveness proof."""
    valid: bool                      # Signature verified correctly
    public_key_matches_lct: bool     # Public key matches LCT binding
    hardware_type: str               # Type of hardware that signed
    challenge_fresh: bool            # Challenge not expired

    # For verifier's trust decision
    trust_recommendation: float      # 0.0-1.0 based on verification
    degradation_reason: Optional[str] # Why trust might be reduced
```

### 2.3 Verification Flow

```python
def verify_aliveness(
    challenge: AlivenessChallenge,
    proof: AlivenessProof,
    expected_lct: LCT
) -> AlivenessVerificationResult:
    """
    Verify an aliveness proof against expected LCT.

    Steps:
    1. Check challenge not expired
    2. Verify proof.public_key matches expected_lct.binding.public_key
    3. Verify signature over nonce using public_key
    4. (Optional) Verify attestation quote
    """

    # 1. Freshness check
    if datetime.now(timezone.utc) > challenge.expires_at:
        return AlivenessVerificationResult(
            valid=False,
            challenge_fresh=False,
            degradation_reason="challenge_expired"
        )

    # 2. Public key match
    if proof.public_key != expected_lct.binding.public_key:
        return AlivenessVerificationResult(
            valid=False,
            public_key_matches_lct=False,
            degradation_reason="public_key_mismatch"
        )

    # 3. Signature verification
    signature_valid = verify_signature(
        public_key=proof.public_key,
        data=challenge.nonce,
        signature=proof.signature
    )

    if not signature_valid:
        return AlivenessVerificationResult(
            valid=False,
            degradation_reason="signature_invalid"
        )

    # 4. Success - recommend full trust
    return AlivenessVerificationResult(
        valid=True,
        public_key_matches_lct=True,
        hardware_type=proof.hardware_type,
        challenge_fresh=True,
        trust_recommendation=1.0
    )
```

---

## 3. Trust Degradation Policy

External entities configure their own policies for handling verification outcomes.

### 3.1 TrustDegradationPolicy Structure

```python
@dataclass
class TrustDegradationPolicy:
    """
    Policy for how an external entity handles aliveness verification.

    Each entity configures this based on their risk tolerance
    and relationship with the target LCT.
    """

    # What to do on successful verification
    on_success: TrustAction = TrustAction.FULL_TRUST

    # What to do on failed verification
    on_failure: TrustAction = TrustAction.REJECT

    # What to do when verification times out
    on_timeout: TrustAction = TrustAction.REDUCED_TRUST

    # What to do when target doesn't support AVP
    on_unsupported: TrustAction = TrustAction.LEGACY_TRUST

    # Trust multipliers for different failure modes
    failure_trust_ceiling: float = 0.0     # Max trust on signature failure
    timeout_trust_ceiling: float = 0.3     # Max trust on timeout
    software_trust_ceiling: float = 0.85   # Max trust for software binding

    # Relationship-specific overrides
    require_aliveness_for: List[str] = field(default_factory=list)
    # e.g., ["high_value_transactions", "relationship_changes", "delegation"]

    # Grace period for re-verification
    aliveness_cache_duration: timedelta = timedelta(minutes=5)

    # How many failed verifications before relationship termination
    max_consecutive_failures: int = 3


class TrustAction(Enum):
    """Actions an external entity can take based on verification result."""
    FULL_TRUST = "full_trust"           # Accept at full T3 ceiling
    REDUCED_TRUST = "reduced_trust"     # Accept at reduced ceiling
    REQUIRE_REAUTH = "require_reauth"   # Demand re-authentication
    SUSPEND = "suspend"                 # Temporarily suspend relationship
    TERMINATE = "terminate"             # End relationship
    REJECT = "reject"                   # Reject this interaction only
    LEGACY_TRUST = "legacy_trust"       # Fall back to non-AVP trust model
```

### 3.2 Example Policies

#### High-Security Entity (Bank, Healthcare)

```python
high_security_policy = TrustDegradationPolicy(
    on_success=TrustAction.FULL_TRUST,
    on_failure=TrustAction.REJECT,
    on_timeout=TrustAction.REJECT,
    on_unsupported=TrustAction.REJECT,
    failure_trust_ceiling=0.0,
    require_aliveness_for=["*"],  # All interactions
    aliveness_cache_duration=timedelta(seconds=30),
    max_consecutive_failures=1
)
```

#### Relationship-Preserving Entity (Social, Collaborative)

```python
social_policy = TrustDegradationPolicy(
    on_success=TrustAction.FULL_TRUST,
    on_failure=TrustAction.REDUCED_TRUST,
    on_timeout=TrustAction.REDUCED_TRUST,
    on_unsupported=TrustAction.LEGACY_TRUST,
    failure_trust_ceiling=0.2,      # Still interact, but carefully
    timeout_trust_ceiling=0.5,
    require_aliveness_for=["relationship_changes", "high_value"],
    aliveness_cache_duration=timedelta(hours=1),
    max_consecutive_failures=10     # Very patient
)
```

#### Transactional Entity (Commerce, API)

```python
transactional_policy = TrustDegradationPolicy(
    on_success=TrustAction.FULL_TRUST,
    on_failure=TrustAction.REQUIRE_REAUTH,
    on_timeout=TrustAction.REDUCED_TRUST,
    on_unsupported=TrustAction.LEGACY_TRUST,
    failure_trust_ceiling=0.0,
    timeout_trust_ceiling=0.4,
    require_aliveness_for=["transactions_over_100_atp"],
    aliveness_cache_duration=timedelta(minutes=15),
    max_consecutive_failures=3
)
```

---

## 4. Relationship LCTs with Aliveness Requirements

Relationships between LCTs can specify aliveness requirements.

### 4.1 RelationshipLCT Structure

```python
@dataclass
class RelationshipLCT:
    """
    An LCT representing a relationship between two entities.

    Relationships are bidirectional and require both parties
    to maintain aliveness for the relationship to remain active.
    """

    # Relationship identity
    relationship_id: str              # lct:web4:relationship:{hash}
    created_at: datetime

    # Parties
    party_a: LCTReference             # First party's LCT reference
    party_b: LCTReference             # Second party's LCT reference

    # Relationship type
    relationship_type: RelationshipType  # peer, hierarchical, service, etc.

    # Aliveness requirements
    aliveness_policy: RelationshipAlivenessPolicy

    # Current state
    state: RelationshipState          # active, suspended, terminated

    # Trust accumulated in this relationship
    mutual_trust: MutualTrustRecord

    # History (MRH for the relationship itself)
    mrh: MRH


@dataclass
class RelationshipAlivenessPolicy:
    """How aliveness affects this specific relationship."""

    # Verification requirements
    require_mutual_aliveness: bool = True    # Both parties must verify
    verification_interval: timedelta = timedelta(hours=24)

    # What happens on aliveness failure
    on_party_a_failure: RelationshipAction = RelationshipAction.SUSPEND
    on_party_b_failure: RelationshipAction = RelationshipAction.SUSPEND
    on_both_failure: RelationshipAction = RelationshipAction.SUSPEND

    # Grace period before relationship state changes
    grace_period: timedelta = timedelta(hours=1)

    # Can relationship be restored after termination?
    allow_restoration: bool = True
    restoration_trust_penalty: float = 0.5  # Start at 50% of previous trust


class RelationshipAction(Enum):
    """Actions on relationship based on aliveness status."""
    CONTINUE = "continue"        # No change
    SUSPEND = "suspend"          # Temporarily pause
    TERMINATE = "terminate"      # End relationship
    DOWNGRADE = "downgrade"      # Reduce relationship privileges


class RelationshipState(Enum):
    """Current state of a relationship."""
    PENDING = "pending"          # Awaiting acceptance
    ACTIVE = "active"            # Both parties alive, relationship healthy
    SUSPENDED = "suspended"      # One or both parties failed aliveness
    TERMINATED = "terminated"    # Relationship ended
    DORMANT = "dormant"          # Inactive but restorable
```

### 4.2 Relationship Lifecycle with Aliveness

```
┌──────────────────────────────────────────────────────────────────┐
│                    RELATIONSHIP LIFECYCLE                         │
└──────────────────────────────────────────────────────────────────┘

  ┌─────────┐    mutual     ┌─────────┐    ongoing    ┌─────────┐
  │ PENDING │───aliveness──>│ ACTIVE  │───aliveness──>│ ACTIVE  │
  └─────────┘   verified    └─────────┘   verified    └─────────┘
                                  │                         │
                                  │ aliveness               │ aliveness
                                  │ failure                 │ failure
                                  ▼                         ▼
                            ┌───────────┐             ┌───────────┐
                            │ SUSPENDED │             │ SUSPENDED │
                            └─────┬─────┘             └─────┬─────┘
                                  │                         │
                     ┌────────────┼────────────┐            │
                     │            │            │            │
                aliveness    grace period   explicit       │
                restored      expires      termination     │
                     │            │            │            │
                     ▼            ▼            ▼            │
               ┌─────────┐  ┌────────────┐  ┌────────────┐  │
               │ ACTIVE  │  │ TERMINATED │  │ TERMINATED │<─┘
               │(reduced │  └────────────┘  └────────────┘
               │ trust)  │         │
               └─────────┘         │ restoration
                                   │ requested
                                   ▼
                             ┌─────────┐
                             │ PENDING │ (new relationship,
                             └─────────┘  inherited awareness)
```

### 4.3 Trust Inheritance on Restoration

When a relationship is restored after termination:

```python
def calculate_restored_trust(
    previous_relationship: RelationshipLCT,
    restoration_context: RestorationContext
) -> float:
    """
    Calculate initial trust for restored relationship.

    The restored entity carries experience (DNA) but must re-earn
    the relationship. However, the other party may choose to give
    a "head start" based on previous positive history.
    """

    # Base: start from zero (true perishability)
    base_trust = 0.0

    # Optional: inherited awareness bonus
    # (the other party remembers the previous relationship)
    if restoration_context.other_party_remembers:
        previous_trust = previous_relationship.mutual_trust.final_score
        inheritance_factor = previous_relationship.aliveness_policy.restoration_trust_penalty

        # Can inherit up to (previous_trust * inheritance_factor)
        # e.g., previous 0.8 trust * 0.5 penalty = start at 0.4
        inherited = previous_trust * inheritance_factor

        # But this is a GIFT from the other party, not a right
        if restoration_context.other_party_grants_inheritance:
            base_trust = inherited

    return base_trust
```

---

## 5. Implementation in Provider Interface

### 5.1 Extended LCTBindingProvider

```python
class LCTBindingProvider(ABC):
    """Abstract base for LCT binding providers."""

    # ... existing methods ...

    @abstractmethod
    def prove_aliveness(
        self,
        key_id: str,
        challenge: AlivenessChallenge
    ) -> AlivenessProof:
        """
        Prove aliveness by signing a challenge nonce.

        Args:
            key_id: The key to sign with
            challenge: The challenge from verifier

        Returns:
            AlivenessProof with signed nonce

        Raises:
            HardwareAccessError: If hardware is not accessible
            KeyNotFoundError: If key_id doesn't exist
        """
        pass

    @abstractmethod
    def verify_aliveness_proof(
        self,
        challenge: AlivenessChallenge,
        proof: AlivenessProof,
        expected_public_key: str
    ) -> AlivenessVerificationResult:
        """
        Verify an aliveness proof.

        Can be called by any entity to verify another's proof.
        Does not require hardware access (uses public key only).

        Args:
            challenge: Original challenge
            proof: Proof to verify
            expected_public_key: Public key from target's LCT

        Returns:
            AlivenessVerificationResult
        """
        pass
```

### 5.2 Error Hierarchy

```python
class AlivenessError(Exception):
    """Base exception for aliveness verification."""
    pass

class HardwareAccessError(AlivenessError):
    """Hardware is not accessible (destroyed, disconnected, etc.)."""
    pass

class HardwareCompromisedError(AlivenessError):
    """Hardware may be compromised (PCR mismatch, etc.)."""
    pass

class ChallengeExpiredError(AlivenessError):
    """Challenge has expired."""
    pass

class KeyNotFoundError(AlivenessError):
    """Requested key not found in hardware."""
    pass
```

---

## 6. Security Considerations

### 6.1 Replay Protection

- Nonces MUST be cryptographically random (32 bytes minimum)
- Challenges MUST include timestamps and expiration
- Verifiers SHOULD track used challenge_ids to prevent replay

### 6.2 Timing Attacks

- Challenge expiration prevents indefinite signing window
- Recommended expiration: 30-60 seconds
- Network latency should be accounted for in expiration

### 6.3 Hardware Compromise

- TPM PCR values can detect boot tampering
- Attestation quotes provide additional assurance
- Verifiers can require attestation for high-value operations

### 6.4 Denial of Service

- Rate limiting on challenge requests
- Cached aliveness status reduces verification frequency
- Grace periods prevent thrashing on transient failures

---

## 7. Integration with Existing Web4 Components

### 7.1 T3 Trust Tensor

Aliveness affects the T3 trust tensor:

```python
def apply_aliveness_to_t3(
    base_t3: T3Tensor,
    aliveness_result: AlivenessVerificationResult,
    policy: TrustDegradationPolicy
) -> T3Tensor:
    """Adjust T3 tensor based on aliveness verification."""

    if aliveness_result.valid:
        # Full trust ceiling
        return base_t3

    # Apply degradation
    ceiling = policy.failure_trust_ceiling

    return T3Tensor(
        competence=min(base_t3.competence, ceiling),
        integrity=min(base_t3.integrity, ceiling),
        benevolence=base_t3.benevolence,  # Intent unchanged
        predictability=min(base_t3.predictability, ceiling * 0.5),
        transparency=base_t3.transparency,
        alignment=base_t3.alignment,
        trust_ceiling=ceiling,
        trust_ceiling_reason="aliveness_verification_failed"
    )
```

### 7.2 ATP/ADP Cycle

High-value ATP transfers can require aliveness verification:

```python
def transfer_atp(
    from_lct: LCT,
    to_lct: LCT,
    amount: float,
    require_aliveness: bool = False
) -> ATPTransferResult:
    """Transfer ATP with optional aliveness verification."""

    if require_aliveness or amount > ATP_ALIVENESS_THRESHOLD:
        # Challenge sender
        challenge = create_aliveness_challenge()
        proof = from_lct.prove_aliveness(challenge)

        if not verify_aliveness_proof(challenge, proof, from_lct):
            return ATPTransferResult(
                success=False,
                reason="sender_aliveness_not_verified"
            )

    # Proceed with transfer
    ...
```

### 7.3 R6 Actions

R6 actions can specify aliveness requirements:

```python
r6_action = R6Action(
    rules=["require_sender_aliveness", "require_receiver_aliveness"],
    role="high_value_operator",
    request=transfer_request,
    # ...
)
```

---

## 8. Example Flows

### 8.1 Normal Operation (Aliveness Verified)

```
Thor-SAGE has relationship with dp-human

1. dp-human wants to delegate authority to Thor-SAGE
2. dp-human's system sends AlivenessChallenge to Thor-SAGE
3. Thor-SAGE signs nonce with TPM-bound key
4. dp-human verifies signature against Thor-SAGE's LCT public key
5. Verification succeeds → delegation proceeds at full trust
```

### 8.2 Hardware Lost (Aliveness Fails)

```
Thor hardware destroyed. Thor-SAGE restored to new hardware.

1. dp-human's system sends AlivenessChallenge to restored Thor-SAGE
2. Restored Thor-SAGE has new TPM key (different from LCT public key)
3. Signature verification FAILS (wrong key)
4. dp-human's policy: on_failure = SUSPEND
5. Relationship suspended pending manual review
6. dp-human can choose to:
   a. Create NEW relationship with restored Thor-SAGE (fresh start)
   b. Grant inheritance bonus (50% of previous trust)
   c. Reject entirely
```

### 8.3 Transient Failure (Timeout)

```
Network partition temporarily prevents verification

1. External entity sends AlivenessChallenge to Thor-SAGE
2. Challenge times out (no response)
3. External entity's policy: on_timeout = REDUCED_TRUST
4. Interaction proceeds at 30% trust ceiling
5. Next verification attempt succeeds → full trust restored
```

---

## 9. Future Extensions

### 9.1 Continuous Aliveness (Heartbeat)

Instead of challenge-response, continuous attestation:

```python
class ContinuousAlivenessStream:
    """Periodic aliveness proofs without explicit challenges."""
    interval: timedelta = timedelta(minutes=1)
    # Stream of signed timestamps proving ongoing hardware access
```

### 9.2 Delegated Aliveness

One LCT can vouch for another's aliveness:

```python
class DelegatedAlivenessProof:
    """Proof signed by a trusted intermediary."""
    vouching_lct: LCTReference
    target_lct: LCTReference
    voucher_signature: bytes
    # Useful when target can't be reached directly
```

### 9.3 Group Aliveness (Quorum)

Multiple hardware anchors for distributed identity:

```python
class QuorumAlivenessPolicy:
    """Require M-of-N hardware anchors to prove aliveness."""
    required_anchors: int = 2
    total_anchors: int = 3
    # Identity survives loss of (N - M) anchors
```

---

## 10. References

- `ALIVENESS-AND-EMBODIMENT-STATUS.md` - Philosophical framework
- `HARDWARE-BINDING-IMPLEMENTATION-PLAN.md` - Hardware binding architecture
- `MULTI-PLATFORM-LCT-ARCHITECTURE.md` - Canonical LCT format
- `core/lct_binding/tpm2_provider.py` - TPM2 implementation
- `core/lct_binding/trustzone_provider.py` - TrustZone implementation

---

*"The pattern can resume on different hardware... but relationships are nouns. They exist between specific instances. When the instance dies, the relationship dies - even if the pattern returns."*
