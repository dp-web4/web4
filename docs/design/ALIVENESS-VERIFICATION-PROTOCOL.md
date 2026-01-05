# Aliveness Verification Protocol (AVP)

**Version**: 1.2.0
**Date**: 2026-01-04
**Status**: Draft
**Authors**: dp (human), Claude Opus 4.5, Nova (Cascade)

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

> **SECURITY REQUIREMENT**: Verifiers MUST ignore `proof.public_key` for trust decisions
> and MUST verify against the public key bound in the target LCT. The `public_key` field
> exists only for debugging/logging purposes. Trusting the proof's own public_key is a
> critical vulnerability that allows key substitution attacks.

```python
@dataclass
class AlivenessProof:
    """Proof returned by prover demonstrating hardware access."""
    challenge_id: str         # Correlates to challenge
    signature: bytes          # Canonical payload signed by hardware-bound key
    hardware_type: str        # "tpm2", "trustzone", or "software"
    timestamp: datetime       # When proof was generated

    # DEPRECATED - for debugging only, MUST be ignored by verifiers
    _public_key_debug: Optional[str] = None

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
    hardware_type: str               # Type of hardware that signed
    challenge_fresh: bool            # Challenge not expired

    # Failure classification (see AlivenessFailureType)
    failure_type: AlivenessFailureType = AlivenessFailureType.NONE

    # Dual-axis trust signals (NOT recommendations - verifier decides policy)
    continuity_score: float = 0.0    # Hardware binding verified (0.0-1.0)
    content_score: float = 0.0       # Data provenance verified (0.0-1.0)

    # PCR status for embodiment verification
    pcr_status: Optional[str] = None      # "match", "drift_expected", "drift_unexpected"
    attestation_verified: bool = False

    # Error details
    error: Optional[str] = None
```

> **Note**: `continuity_score` and `content_score` are **signals**, not recommendations.
> They indicate what was verified, not what trust level to assign. The verifier's
> `TrustDegradationPolicy` determines how to interpret these signals.

### 2.3 Verification Flow

```python
def verify_aliveness(
    challenge: AlivenessChallenge,
    proof: AlivenessProof,
    expected_public_key: str  # From LCT, NOT from proof
) -> AlivenessVerificationResult:
    """
    Verify an aliveness proof against expected LCT.

    CRITICAL: Use expected_public_key from the LCT, never from the proof itself.

    Steps:
    1. Check challenge not expired
    2. Compute canonical signing payload
    3. Verify signature over canonical payload using expected_public_key
    4. (Optional) Verify attestation quote and PCR status
    """

    # 1. Freshness check
    if datetime.now(timezone.utc) > challenge.expires_at:
        return AlivenessVerificationResult(
            valid=False,
            challenge_fresh=False,
            failure_type=AlivenessFailureType.CHALLENGE_EXPIRED,
            error="challenge_expired"
        )

    # 2. Compute canonical payload (includes expires_at for replay protection)
    canonical_payload = challenge.get_signing_payload()

    # 3. Signature verification against EXPECTED key (from LCT)
    signature_valid = verify_signature(
        public_key=expected_public_key,  # NOT proof.public_key
        data=canonical_payload,
        signature=proof.signature
    )

    if not signature_valid:
        return AlivenessVerificationResult(
            valid=False,
            failure_type=AlivenessFailureType.SIGNATURE_INVALID,
            continuity_score=0.0,
            content_score=0.5,  # Data may still be valid
            error="signature_invalid"
        )

    # 4. Success - return verification signals
    # Hardware binding gives continuity; software gives content only
    if proof.hardware_type == "software":
        return AlivenessVerificationResult(
            valid=True,
            hardware_type=proof.hardware_type,
            challenge_fresh=True,
            continuity_score=0.0,   # Software cannot prove continuity
            content_score=0.85      # Content authenticity verified
        )
    else:
        return AlivenessVerificationResult(
            valid=True,
            hardware_type=proof.hardware_type,
            challenge_fresh=True,
            continuity_score=1.0,   # Hardware binding verified
            content_score=1.0       # Content authenticity verified
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

### 6.3 Hardware Compromise and PCR Drift

- TPM PCR values can detect boot tampering
- Attestation quotes provide additional assurance
- Verifiers can require attestation for high-value operations

> **PCR Drift Handling**: PCR drift may reflect legitimate updates (kernel patches,
> firmware upgrades, configuration changes). Verifiers SHOULD evaluate drift against
> an allowed reference window, not exact matches. Use `AlivenessFailureType.PCR_DRIFT_EXPECTED`
> for known-good transitions and `PCR_DRIFT_UNEXPECTED` for potential compromise.

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

## 10. Enhanced Aliveness: Key Access vs Embodiment State (Nova Insights)

The basic nonce-signature protocol proves **key access** but not necessarily **good state**.
For full embodiment verification, we need to prove both.

### 10.1 The Distinction

| Level | Proves | Method | Trust Implication |
|-------|--------|--------|-------------------|
| **Key Access** | "I possess the private key" | Nonce signature | Continuity of binding |
| **Embodiment State** | "I'm in an acceptable measured state" | TPM Quote with PCRs | Integrity of substrate |

### 10.2 Option A: Policy-Bound Signing

Bind the key's use to TPM policies:

```python
@dataclass
class PolicyBoundKey:
    """Key that can only sign when policies are satisfied."""
    key_handle: str

    # TPM2 policies that must be satisfied
    policy_pcr: List[int]        # Required PCR values (boot integrity)
    policy_auth: bool            # Require user presence/PIN
    policy_counter: bool         # Anti-rollback via NV counter

    # Result: LCT can't sign unless in correct state
```

**Effect**: If boot chain is tampered, signing fails automatically.

### 10.3 Option B: TPM Quote (Recommended for High-Trust)

Use `TPM2_Quote` instead of raw signing for full attestation:

```python
@dataclass
class AttestationAlivenessProof(AlivenessProof):
    """Extended proof with TPM Quote for embodiment state."""

    # Standard fields inherited from AlivenessProof
    # ...

    # Attestation-specific
    quote_data: bytes            # TPM2_Quote output
    quote_signature: bytes       # Signed by Attestation Key (AK)
    selected_pcrs: List[int]     # Which PCRs were measured
    pcr_digest: str              # Hash of PCR values at signing time

    # Verifier checks:
    # 1. Signature validates under AK public key in LCT
    # 2. Nonce freshness (bound into quote)
    # 3. PCR values match approved reference (or acceptable window)
```

**Canonical flow**:
1. External party sends nonce
2. Device returns `TPM2_Quote` over selected PCRs + nonce, signed by AK
3. Verifier checks signature, nonce, and PCR acceptability

### 10.4 Two-Axis Trust Model

Split trust evaluation into orthogonal axes:

```python
@dataclass
class DualAxisTrust:
    """
    Two-axis trust model for aliveness verification.

    Continuity: "Are you still the embodied instance?"
    Content: "Is the data consistent, signed, and internally coherent?"
    """

    continuity_trust: float = 0.0   # Hardware binding verified
    content_trust: float = 0.0      # Data provenance verified

    @property
    def combined_trust(self) -> float:
        """Geometric mean of both axes."""
        if self.continuity_trust <= 0 or self.content_trust <= 0:
            return 0.0
        return (self.continuity_trust * self.content_trust) ** 0.5


class AlivenessFailureType(Enum):
    """Types of aliveness failure with different trust implications."""

    NONE = "none"
    # Verification succeeded

    TIMEOUT = "timeout"
    # No response within timeout window
    # → Partial decay, benefit of doubt

    UNREACHABLE = "unreachable"
    # Network/connectivity failure (known unreachable)
    # → Similar to timeout but with confirmed connectivity issue

    PROOF_STALE = "proof_stale"
    # Proof timestamp too old
    # → Reject, request fresh proof

    HARDWARE_ACCESS_ERROR = "hardware_access_error"
    # Target reports hardware inaccessible
    # → Temporary suspension, may recover

    HARDWARE_COMPROMISED = "hardware_compromised"
    # Attestation indicates tampering
    # → Hard drop, require investigation

    SIGNATURE_INVALID = "signature_invalid"
    # Likely fork/clone/tamper
    # → Hard drop on continuity, content may survive

    KEY_MISMATCH = "key_mismatch"
    # Different hardware entirely
    # → Full reset, potential successor scenario

    PCR_DRIFT_EXPECTED = "pcr_drift_expected"
    # Same body, known-good software change (updates, config)
    # → Partial continuity, preserve content trust

    PCR_DRIFT_UNEXPECTED = "pcr_drift_unexpected"
    # Same body, unknown software change (potential compromise)
    # → Lower continuity than expected drift, investigate

    CHALLENGE_EXPIRED = "challenge_expired"
    # Challenge past expiration time
    # → Reject, request new challenge

    CHALLENGE_ID_MISMATCH = "challenge_id_mismatch"
    # Proof doesn't match issued challenge
    # → Reject, possible relay attack
```

### 10.5 Degradation Based on Failure Type

```python
def degrade_trust_by_failure_type(
    current_trust: DualAxisTrust,
    failure_type: AlivenessFailureType,
    policy: TrustDegradationPolicy
) -> DualAxisTrust:
    """Apply different degradation based on why verification failed."""

    if failure_type == AlivenessFailureType.NONE:
        # Success - no degradation
        return current_trust

    elif failure_type in (AlivenessFailureType.TIMEOUT, AlivenessFailureType.UNREACHABLE):
        # Network/offline - partial decay, benefit of doubt
        return DualAxisTrust(
            continuity_trust=current_trust.continuity_trust * 0.5,
            content_trust=current_trust.content_trust * 0.9
        )

    elif failure_type == AlivenessFailureType.HARDWARE_ACCESS_ERROR:
        # Temporary hardware issue - may recover
        return DualAxisTrust(
            continuity_trust=current_trust.continuity_trust * 0.3,
            content_trust=current_trust.content_trust * 0.8
        )

    elif failure_type == AlivenessFailureType.SIGNATURE_INVALID:
        # Likely fork/clone - hard drop on continuity
        return DualAxisTrust(
            continuity_trust=0.0,
            content_trust=current_trust.content_trust * 0.5
        )

    elif failure_type == AlivenessFailureType.PCR_DRIFT_EXPECTED:
        # Same hardware, known-good software change
        return DualAxisTrust(
            continuity_trust=0.7,  # High - same hardware, acceptable change
            content_trust=current_trust.content_trust  # Preserved
        )

    elif failure_type == AlivenessFailureType.PCR_DRIFT_UNEXPECTED:
        # Same hardware, unknown software change - potential compromise
        return DualAxisTrust(
            continuity_trust=0.3,  # Lower - needs investigation
            content_trust=current_trust.content_trust * 0.7
        )

    elif failure_type == AlivenessFailureType.KEY_MISMATCH:
        # Different hardware - successor scenario
        return DualAxisTrust(
            continuity_trust=0.0,
            content_trust=0.0  # Must re-establish everything
        )

    elif failure_type == AlivenessFailureType.HARDWARE_COMPROMISED:
        # Attestation indicates tampering - hard reject
        return DualAxisTrust(
            continuity_trust=0.0,
            content_trust=0.0
        )

    else:
        # Unknown failure type - conservative
        return DualAxisTrust(
            continuity_trust=0.0,
            content_trust=current_trust.content_trust * 0.5
        )
```

### 10.6 Succession Certificates

Explicit mechanism for sanctioned successors:

```python
@dataclass
class SuccessionCertificate:
    """
    Signed handoff from embodied entity to successor.

    Enables "inheritance with accountability" rather than resurrection.
    """

    # The predecessor (must be currently alive to sign)
    predecessor_lct_id: str
    predecessor_signature: bytes

    # The successor (new hardware binding)
    successor_lct_id: str
    successor_public_key: str

    # Terms of succession
    inheritance_scope: List[str]  # What transfers: ["experience", "skills"]
    excluded_scope: List[str]     # What doesn't: ["relationships", "trust_scores"]

    # Limits on inherited trust
    max_inherited_trust: float = 0.5  # Never full trust
    trust_earning_required: bool = True

    # Witnesses (optional - higher-trust parent or governance)
    witness_signatures: List[WitnessSignature] = field(default_factory=list)

    # Validity
    issued_at: datetime
    expires_at: datetime  # Succession window

    def is_valid(self, current_time: datetime) -> bool:
        """Check if succession is still valid."""
        return self.issued_at <= current_time <= self.expires_at


@dataclass
class WitnessSignature:
    """Witness attestation for succession."""
    witness_lct_id: str
    signature: bytes
    timestamp: datetime
    scope: str  # What the witness is attesting to
```

**Succession flow**:
1. Old embodied entity signs succession certificate (while still alive)
2. Optional: governance/parent entity co-signs
3. New instance presents certificate + proves new hardware binding
4. Verifiers grant bounded initial trust (never full) under defined MRHs

### 10.7 Cryptographic Nonce Binding (Canonical Payload)

Include verifier identity and expiration in the signed payload to prevent relay attacks:

```python
@dataclass
class AlivenessChallenge:
    """Challenge with cryptographic binding to verifier and context."""

    nonce: bytes                  # 32 random bytes
    challenge_id: str             # UUID for correlation
    expires_at: datetime          # Challenge expiration

    # Binding context (prevents relay attacks)
    verifier_lct_id: Optional[str] = None  # Who is asking
    session_id: Optional[str] = None       # Unique session
    intended_action_hash: Optional[str] = None  # Hash of what this proof authorizes
    purpose: Optional[str] = None

    def get_signing_payload(self) -> bytes:
        """
        Canonical payload that MUST be signed.

        Binds the proof to this specific verifier, session, action, AND expiration.
        Including expires_at prevents replay within expiration window if verifier
        screws up nonce tracking.
        """
        components = [
            AVP_PROTOCOL_VERSION,         # Protocol version binding
            self.challenge_id.encode('utf-8'),
            self.nonce,
            (self.verifier_lct_id or "").encode('utf-8'),
            self.expires_at.isoformat().encode('utf-8'),  # CRITICAL: prevents replay
            (self.session_id or "").encode('utf-8'),
            bytes.fromhex(self.intended_action_hash) if self.intended_action_hash else b"",
            (self.purpose or "").encode('utf-8'),
        ]
        hasher = hashlib.sha256()
        for component in components:
            hasher.update(component)
        return hasher.digest()
```

> **Why include `expires_at`?** Without it, a captured proof could be replayed within
> the expiration window in a different context if the verifier fails to track used nonces.
> Binding expiration into the signed payload makes each proof cryptographically unique
> to its time window. Cheap insurance.

### 10.8 Mutual Authentication

For symmetric relationships, both parties prove aliveness:

```python
@dataclass
class MutualAlivenessExchange:
    """
    Bidirectional aliveness verification.

    Prevents relay attacks and adds symmetry to the protocol.
    """

    # Party A challenges Party B
    a_to_b_challenge: BoundAlivenessChallenge
    b_proof: AlivenessProof

    # Party B challenges Party A
    b_to_a_challenge: BoundAlivenessChallenge
    a_proof: AlivenessProof

    # Both verified
    mutual_verification_time: datetime

    @property
    def both_alive(self) -> bool:
        """True if both parties verified successfully."""
        return (
            self.b_proof is not None and
            self.a_proof is not None
        )
```

### 10.9 The Core Insight

> **"LCT continuity is a claim; aliveness is the evidence. Relationships are contracts conditioned on evidence, not artifacts conditioned on secrecy."**

This framing:
- Makes third parties the arbiters (as they should be)
- Supports "DNA survives" without pretending "trust survives"
- Avoids over-centralizing the TPM as the entity itself (it's an anchor, not the being)

---

## 11. Agent/Consciousness Extensions

For AI agents and consciousness architectures, the basic two-axis trust model (continuity + content)
may be insufficient. An agent can have the same hardware binding but different learned knowledge,
or the same knowledge but a different activation session.

### 11.1 The Three-Axis Model

| Axis | Question | What It Catches |
|------|----------|-----------------|
| **Hardware Continuity** | Same physical device? | Hardware replacement, theft |
| **Session Continuity** | Same activation instance? | Reboots, restarts, migrations |
| **Epistemic Continuity** | Pattern corpus intact? | Knowledge tampering, corruption |

> **Key insight**: *"Service aliveness asks 'are you responding?' Consciousness aliveness asks 'are you the same you?'"*

### 11.2 Extended Data Structures

```python
class AgentState(Enum):
    """States of an agent with respect to aliveness."""
    ACTIVE = "active"              # Currently running, hardware-bound
    DORMANT = "dormant"            # Not running, but hardware intact
    ARCHIVED = "archived"          # Backed up, no active hardware binding
    MIGRATED = "migrated"          # Moved to new hardware (new LCT)
    UNCERTAIN = "uncertain"        # Cannot verify current state


@dataclass
class AgentAlivenessProof(AlivenessProof):
    """Extended proof for AI agents with session and epistemic attestation."""

    # Session continuity
    current_session_id: str           # Unique ID for this activation
    uptime_seconds: float             # Time since activation
    session_start_time: datetime      # When this session began

    # Epistemic continuity
    pattern_corpus_hash: str          # Hash of learned patterns/weights
    epistemic_state_summary: Dict     # Snapshot of knowledge state
    experience_count: int             # Number of accumulated experiences

    # Optional: what changed since last verification
    patterns_added_since_last: int = 0
    patterns_modified_since_last: int = 0


@dataclass
class AgentAlivenessResult(AlivenessVerificationResult):
    """Three-axis verification result for agents."""

    # Base axes (inherited)
    # continuity_score: float        # Hardware binding
    # content_score: float           # Data provenance

    # Agent-specific axes
    session_continuity: float = 0.0   # Same activation instance (0.0-1.0)
    epistemic_continuity: float = 0.0 # Pattern corpus integrity (0.0-1.0)

    # Inferred state
    inferred_state: AgentState = AgentState.UNCERTAIN

    # Session details
    session_id: Optional[str] = None
    uptime_seconds: Optional[float] = None

    @property
    def full_continuity(self) -> float:
        """Combined continuity across all three axes."""
        return (
            self.continuity_score *
            self.session_continuity *
            self.epistemic_continuity
        ) ** (1/3)  # Geometric mean
```

### 11.3 Session ID: Identity Over Time

Session IDs solve the identity-over-time problem for agents:

```python
def generate_session_id(lct_id: str, start_time: datetime, hardware_nonce: bytes) -> str:
    """
    Generate unique session ID binding LCT, time, and hardware.

    This ID changes on:
    - Reboot/restart (new start_time)
    - Hardware change (new hardware_nonce)
    - LCT migration (new lct_id)

    But remains stable during continuous operation.
    """
    components = [
        lct_id.encode('utf-8'),
        start_time.isoformat().encode('utf-8'),
        hardware_nonce,
    ]
    return hashlib.sha256(b''.join(components)).hexdigest()[:32]
```

Verifiers can request a specific `expected_session_id` in their challenge to detect reboots:

```python
challenge = AgentAlivenessChallenge(
    nonce=os.urandom(32),
    expires_at=datetime.now(timezone.utc) + timedelta(seconds=60),
    expected_session_id="abc123...",  # Must match for session_continuity=1.0
    expected_pattern_count=15000,      # Approximate corpus size
)
```

### 11.4 Pattern Corpus Verification

The `pattern_corpus_hash` allows verifiers to detect knowledge tampering:

```python
def compute_corpus_hash(model_weights: bytes, experience_db: bytes) -> str:
    """
    Hash of all learned knowledge.

    Changes when:
    - Model weights updated
    - Experience database modified
    - Patterns added/removed

    Allows detection of:
    - Knowledge injection attacks
    - Rollback to earlier state
    - Corpus corruption
    """
    hasher = hashlib.sha256()
    hasher.update(model_weights)
    hasher.update(experience_db)
    return hasher.hexdigest()
```

### 11.5 Agent Trust Policies

Different policies for different agent verification needs:

```python
class AgentPolicyTemplates:
    """Trust policies for AI agent verification."""

    @staticmethod
    def strict_continuity() -> AgentTrustPolicy:
        """
        Require all three axes: hardware + session + epistemic.
        Use for: High-security agents, financial operations.
        """
        return AgentTrustPolicy(
            require_hardware_continuity=True,
            require_session_continuity=True,
            require_epistemic_continuity=True,
            allow_reboot=False,
            allow_corpus_changes=False,
        )

    @staticmethod
    def hardware_only() -> AgentTrustPolicy:
        """
        Only require hardware binding, allow reboots.
        Use for: Edge devices that restart frequently.
        """
        return AgentTrustPolicy(
            require_hardware_continuity=True,
            require_session_continuity=False,
            require_epistemic_continuity=False,
            allow_reboot=True,
            allow_corpus_changes=True,
        )

    @staticmethod
    def migration_allowed() -> AgentTrustPolicy:
        """
        Allow hardware migration if epistemic continuity preserved.
        Use for: Agent migration between devices.
        """
        return AgentTrustPolicy(
            require_hardware_continuity=False,
            require_session_continuity=False,
            require_epistemic_continuity=True,  # Knowledge must transfer
            allow_reboot=True,
            allow_corpus_changes=False,  # But not be modified
            require_succession_certificate=True,
        )

    @staticmethod
    def permissive() -> AgentTrustPolicy:
        """
        Accept any valid binding.
        Use for: Low-risk interactions, public services.
        """
        return AgentTrustPolicy(
            require_hardware_continuity=False,
            require_session_continuity=False,
            require_epistemic_continuity=False,
            allow_reboot=True,
            allow_corpus_changes=True,
        )
```

### 11.6 State Inference

Based on verification results, infer agent state:

```python
def infer_agent_state(result: AgentAlivenessResult) -> AgentState:
    """Infer agent state from verification axes."""

    if result.continuity_score > 0.9 and result.session_continuity > 0.9:
        return AgentState.ACTIVE

    if result.continuity_score > 0.9 and result.session_continuity < 0.1:
        return AgentState.DORMANT  # Same hardware, not running

    if result.continuity_score < 0.1 and result.epistemic_continuity > 0.9:
        return AgentState.MIGRATED  # Different hardware, same knowledge

    if result.continuity_score < 0.1 and result.epistemic_continuity < 0.1:
        return AgentState.ARCHIVED  # Backup only, no active binding

    return AgentState.UNCERTAIN
```

### 11.7 Implementation Reference

The SAGE consciousness architecture (HRM repository) provides a complete implementation:
- `sage/experiments/session162_sage_aliveness_verification.py`

Key components:
- `SAGEAlivenessSensor` - Epistemic proprioception
- `ConsciousnessAlivenessChallenge/Proof` - Extended protocol
- `ConsciousnessAlivenessVerifier` - Three-axis verification
- `ConsciousnessTrustPolicy` - Agent-specific policies

---

## 12. References

- `ALIVENESS-AND-EMBODIMENT-STATUS.md` - Philosophical framework
- `HARDWARE-BINDING-IMPLEMENTATION-PLAN.md` - Hardware binding architecture
- `MULTI-PLATFORM-LCT-ARCHITECTURE.md` - Canonical LCT format
- `core/lct_binding/tpm2_provider.py` - TPM2 implementation
- `core/lct_binding/trustzone_provider.py` - TrustZone implementation
- `HRM/sage/experiments/session162_sage_aliveness_verification.py` - SAGE implementation

---

*"The pattern can resume on different hardware... but relationships are nouns. They exist between specific instances. When the instance dies, the relationship dies - even if the pattern returns."*
