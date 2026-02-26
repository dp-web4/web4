#!/usr/bin/env python3
"""
Web4 Aliveness Verification Protocol (AVP) — Core Protocol Reference Implementation
Spec: docs/history/design_decisions/ALIVENESS-VERIFICATION-PROTOCOL.md (1365 lines, 10 sections)

Covers:
  §1  Motivation (identity vs aliveness, design goals)
  §2  Protocol Specification (challenge, proof, verification flow)
  §3  Trust Degradation Policy (7 trust actions, 3 example policies)
  §4  Relationship LCTs with Aliveness (lifecycle, restoration)
  §5  Provider Interface (abstract binding provider, error hierarchy)
  §6  Security Considerations (replay, timing, PCR drift, DoS)
  §7  Integration (T3 adjustment, ATP transfer, R6 actions)
  §8  Example Flows (normal, hardware lost, timeout)
  §9  Future Extensions (heartbeat, delegation, quorum)
  §10 Enhanced Aliveness (key access vs embodiment, PCR drift)

Complements existing avp_transport.py (HTTP/JSON transport layer).
"""

from __future__ import annotations
import hashlib
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ============================================================
# Test harness
# ============================================================
_pass = _fail = 0


def check(label: str, condition: bool):
    global _pass, _fail
    if condition:
        _pass += 1
    else:
        _fail += 1
        print(f"  FAIL: {label}")


# ============================================================
# §2.2 Data Structures
# ============================================================

@dataclass
class AlivenessChallenge:
    """Challenge sent by verifier per §2.1-2.2."""
    nonce: bytes                  # 32 random bytes
    timestamp: float              # Unix epoch
    challenge_id: str             # UUID for correlation
    expires_at: float             # Expiration (epoch)
    verifier_lct_id: str = ""     # Who is asking
    purpose: str = ""             # Why verification is requested

    @staticmethod
    def create(verifier_lct_id: str = "", purpose: str = "",
               ttl_seconds: float = 60.0) -> AlivenessChallenge:
        """Create a new challenge with random nonce."""
        now = time.time()
        return AlivenessChallenge(
            nonce=os.urandom(32),
            timestamp=now,
            challenge_id=str(uuid.uuid4()),
            expires_at=now + ttl_seconds,
            verifier_lct_id=verifier_lct_id,
            purpose=purpose,
        )

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def get_signing_payload(self) -> bytes:
        """Canonical payload for signing per §2.3."""
        # Include expires_at for replay protection
        return self.nonce + str(self.expires_at).encode()


class HardwareType(Enum):
    """Hardware types per §2.2."""
    TPM2 = "tpm2"
    TRUSTZONE = "trustzone"
    SOFTWARE = "software"


@dataclass
class AlivenessProof:
    """Proof returned by prover per §2.2."""
    challenge_id: str
    signature: bytes
    hardware_type: str  # tpm2, trustzone, software
    timestamp: float

    # DEPRECATED per spec — for debugging only, MUST be ignored by verifiers
    _public_key_debug: Optional[str] = None

    # Optional TPM attestation
    attestation_quote: str = ""
    pcr_values: dict[int, str] = field(default_factory=dict)


class AlivenessFailureType(Enum):
    """Failure classification per §2.3."""
    NONE = "none"
    CHALLENGE_EXPIRED = "challenge_expired"
    SIGNATURE_INVALID = "signature_invalid"
    HARDWARE_ACCESS_ERROR = "hardware_access_error"
    KEY_NOT_FOUND = "key_not_found"
    PCR_DRIFT_EXPECTED = "pcr_drift_expected"
    PCR_DRIFT_UNEXPECTED = "pcr_drift_unexpected"
    TIMEOUT = "timeout"


@dataclass
class AlivenessVerificationResult:
    """Result of verifying an aliveness proof per §2.3."""
    valid: bool
    hardware_type: str = ""
    challenge_fresh: bool = True
    failure_type: AlivenessFailureType = AlivenessFailureType.NONE

    # Dual-axis trust signals (NOT recommendations)
    continuity_score: float = 0.0    # Hardware binding verified
    content_score: float = 0.0       # Data provenance verified

    # PCR status for embodiment verification
    pcr_status: Optional[str] = None  # match, drift_expected, drift_unexpected
    attestation_verified: bool = False

    error: Optional[str] = None


# ============================================================
# §2.3 Verification Flow
# ============================================================

def verify_aliveness(
    challenge: AlivenessChallenge,
    proof: AlivenessProof,
    expected_public_key: str,  # From LCT, NOT from proof
) -> AlivenessVerificationResult:
    """Verify an aliveness proof per §2.3.

    CRITICAL: Use expected_public_key from the LCT, never from the proof itself.
    """
    # 1. Freshness check
    if challenge.is_expired:
        return AlivenessVerificationResult(
            valid=False,
            challenge_fresh=False,
            failure_type=AlivenessFailureType.CHALLENGE_EXPIRED,
            error="challenge_expired",
        )

    # 2. Compute canonical payload
    canonical = challenge.get_signing_payload()

    # 3. Verify signature (mock — hash-based)
    expected_sig = _mock_sign(canonical, expected_public_key)
    signature_valid = (proof.signature == expected_sig)

    if not signature_valid:
        return AlivenessVerificationResult(
            valid=False,
            failure_type=AlivenessFailureType.SIGNATURE_INVALID,
            continuity_score=0.0,
            content_score=0.5,  # Data may still be valid
            error="signature_invalid",
        )

    # 4. Success — score based on hardware type
    if proof.hardware_type == HardwareType.SOFTWARE.value:
        return AlivenessVerificationResult(
            valid=True,
            hardware_type=proof.hardware_type,
            challenge_fresh=True,
            continuity_score=0.0,   # Software cannot prove continuity
            content_score=0.85,     # Content authenticity verified
        )
    else:
        return AlivenessVerificationResult(
            valid=True,
            hardware_type=proof.hardware_type,
            challenge_fresh=True,
            continuity_score=1.0,
            content_score=1.0,
        )


# ============================================================
# §3 Trust Degradation Policy
# ============================================================

class TrustAction(Enum):
    """Actions per §3.1."""
    FULL_TRUST = "full_trust"
    REDUCED_TRUST = "reduced_trust"
    REQUIRE_REAUTH = "require_reauth"
    SUSPEND = "suspend"
    TERMINATE = "terminate"
    REJECT = "reject"
    LEGACY_TRUST = "legacy_trust"


@dataclass
class TrustDegradationPolicy:
    """How an entity handles aliveness verification per §3.1."""
    on_success: TrustAction = TrustAction.FULL_TRUST
    on_failure: TrustAction = TrustAction.REJECT
    on_timeout: TrustAction = TrustAction.REDUCED_TRUST
    on_unsupported: TrustAction = TrustAction.LEGACY_TRUST

    failure_trust_ceiling: float = 0.0
    timeout_trust_ceiling: float = 0.3
    software_trust_ceiling: float = 0.85

    require_aliveness_for: list[str] = field(default_factory=list)
    aliveness_cache_seconds: float = 300.0  # 5 minutes default
    max_consecutive_failures: int = 3

    def determine_action(self, result: AlivenessVerificationResult) -> TrustAction:
        """Determine action based on verification result."""
        if result.valid:
            return self.on_success
        if result.failure_type == AlivenessFailureType.TIMEOUT:
            return self.on_timeout
        return self.on_failure

    def trust_ceiling(self, result: AlivenessVerificationResult) -> float:
        """Calculate trust ceiling based on result."""
        if result.valid:
            if result.hardware_type == HardwareType.SOFTWARE.value:
                return self.software_trust_ceiling
            return 1.0
        if result.failure_type == AlivenessFailureType.TIMEOUT:
            return self.timeout_trust_ceiling
        return self.failure_trust_ceiling


# §3.2 Example policies
HIGH_SECURITY_POLICY = TrustDegradationPolicy(
    on_success=TrustAction.FULL_TRUST,
    on_failure=TrustAction.REJECT,
    on_timeout=TrustAction.REJECT,
    on_unsupported=TrustAction.REJECT,
    failure_trust_ceiling=0.0,
    require_aliveness_for=["*"],
    aliveness_cache_seconds=30.0,
    max_consecutive_failures=1,
)

SOCIAL_POLICY = TrustDegradationPolicy(
    on_success=TrustAction.FULL_TRUST,
    on_failure=TrustAction.REDUCED_TRUST,
    on_timeout=TrustAction.REDUCED_TRUST,
    on_unsupported=TrustAction.LEGACY_TRUST,
    failure_trust_ceiling=0.2,
    timeout_trust_ceiling=0.5,
    require_aliveness_for=["relationship_changes", "high_value"],
    aliveness_cache_seconds=3600.0,
    max_consecutive_failures=10,
)

TRANSACTIONAL_POLICY = TrustDegradationPolicy(
    on_success=TrustAction.FULL_TRUST,
    on_failure=TrustAction.REQUIRE_REAUTH,
    on_timeout=TrustAction.REDUCED_TRUST,
    on_unsupported=TrustAction.LEGACY_TRUST,
    failure_trust_ceiling=0.0,
    timeout_trust_ceiling=0.4,
    require_aliveness_for=["transactions_over_100_atp"],
    aliveness_cache_seconds=900.0,
    max_consecutive_failures=3,
)


# ============================================================
# §4 Relationship LCTs with Aliveness
# ============================================================

class RelationshipAction(Enum):
    """Actions on relationship per §4.1."""
    CONTINUE = "continue"
    SUSPEND = "suspend"
    TERMINATE = "terminate"
    DOWNGRADE = "downgrade"


class RelationshipState(Enum):
    """Relationship states per §4.1."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    DORMANT = "dormant"


@dataclass
class RelationshipAlivenessPolicy:
    """How aliveness affects a relationship per §4.1."""
    require_mutual_aliveness: bool = True
    verification_interval_seconds: float = 86400.0  # 24h
    on_party_a_failure: RelationshipAction = RelationshipAction.SUSPEND
    on_party_b_failure: RelationshipAction = RelationshipAction.SUSPEND
    on_both_failure: RelationshipAction = RelationshipAction.SUSPEND
    grace_period_seconds: float = 3600.0  # 1h
    allow_restoration: bool = True
    restoration_trust_penalty: float = 0.5  # Start at 50% of previous


@dataclass
class RelationshipLCT:
    """LCT representing a relationship per §4.1."""
    relationship_id: str
    party_a: str  # LCT ID
    party_b: str  # LCT ID
    aliveness_policy: RelationshipAlivenessPolicy
    state: RelationshipState = RelationshipState.PENDING
    mutual_trust: float = 0.0
    last_verified: float = 0.0
    consecutive_failures: int = 0
    created_at: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

    def verify_and_update(self, result_a: AlivenessVerificationResult,
                          result_b: Optional[AlivenessVerificationResult] = None):
        """Update state based on aliveness results per §4.2."""
        if result_a.valid and (result_b is None or result_b.valid):
            self.state = RelationshipState.ACTIVE
            self.consecutive_failures = 0
            self.last_verified = time.time()
        elif not result_a.valid and (result_b is not None and not result_b.valid):
            action = self.aliveness_policy.on_both_failure
            self._apply_action(action)
        elif not result_a.valid:
            action = self.aliveness_policy.on_party_a_failure
            self._apply_action(action)
        elif result_b is not None and not result_b.valid:
            action = self.aliveness_policy.on_party_b_failure
            self._apply_action(action)

    def _apply_action(self, action: RelationshipAction):
        self.consecutive_failures += 1
        if action == RelationshipAction.SUSPEND:
            self.state = RelationshipState.SUSPENDED
        elif action == RelationshipAction.TERMINATE:
            self.state = RelationshipState.TERMINATED
        elif action == RelationshipAction.DOWNGRADE:
            self.mutual_trust *= 0.5
        # CONTINUE leaves state unchanged

    def needs_verification(self) -> bool:
        """Check if verification is due per §4.1."""
        elapsed = time.time() - self.last_verified
        return elapsed > self.aliveness_policy.verification_interval_seconds


# §4.3 Trust Inheritance on Restoration
def calculate_restored_trust(
    previous_trust: float,
    penalty: float,
    other_party_remembers: bool,
    grants_inheritance: bool,
) -> float:
    """Calculate trust for restored relationship per §4.3."""
    if not other_party_remembers or not grants_inheritance:
        return 0.0
    return round(previous_trust * penalty, 4)


# ============================================================
# §5 Error Hierarchy
# ============================================================

class AlivenessError(Exception):
    """Base exception per §5.2."""
    pass

class HardwareAccessError(AlivenessError):
    pass

class HardwareCompromisedError(AlivenessError):
    pass

class ChallengeExpiredError(AlivenessError):
    pass

class KeyNotFoundError(AlivenessError):
    pass


# ============================================================
# §6 Security — Replay protection and rate limiting
# ============================================================

class ChallengeTracker:
    """Track used challenges to prevent replay per §6.1."""

    def __init__(self):
        self.used_ids: set[str] = set()

    def is_new(self, challenge_id: str) -> bool:
        if challenge_id in self.used_ids:
            return False
        self.used_ids.add(challenge_id)
        return True


class RateLimiter:
    """Rate limit challenge requests per §6.4."""

    def __init__(self, max_per_minute: int = 10):
        self.max_per_minute = max_per_minute
        self.requests: list[float] = []

    def allow(self) -> bool:
        now = time.time()
        # Clean old entries
        self.requests = [t for t in self.requests if now - t < 60]
        if len(self.requests) >= self.max_per_minute:
            return False
        self.requests.append(now)
        return True


# ============================================================
# §7 Integration — T3 adjustment
# ============================================================

@dataclass
class T3Tensor:
    """Simplified T3 for aliveness integration per §7.1."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return round((self.talent + self.training + self.temperament) / 3, 4)


def apply_aliveness_to_t3(
    base_t3: T3Tensor,
    result: AlivenessVerificationResult,
    policy: TrustDegradationPolicy,
) -> T3Tensor:
    """Adjust T3 based on aliveness per §7.1."""
    if result.valid:
        return base_t3

    ceiling = policy.trust_ceiling(result)
    return T3Tensor(
        talent=min(base_t3.talent, ceiling),
        training=min(base_t3.training, ceiling),
        temperament=base_t3.temperament,  # Intent unchanged per spec
    )


# §7.2 ATP transfer with aliveness
ATP_ALIVENESS_THRESHOLD = 100.0


def requires_aliveness_for_transfer(amount: float,
                                    policy: TrustDegradationPolicy) -> bool:
    """Check if ATP transfer requires aliveness per §7.2."""
    if amount > ATP_ALIVENESS_THRESHOLD:
        return True
    if "*" in policy.require_aliveness_for:
        return True
    if "transactions_over_100_atp" in policy.require_aliveness_for and amount > 100:
        return True
    return False


# ============================================================
# §9 Future Extensions
# ============================================================

@dataclass
class ContinuousAlivenessStream:
    """Periodic aliveness proofs per §9.1."""
    interval_seconds: float = 60.0
    proofs: list[AlivenessProof] = field(default_factory=list)
    last_proof_time: float = 0.0

    def add_proof(self, proof: AlivenessProof):
        self.proofs.append(proof)
        self.last_proof_time = proof.timestamp

    @property
    def is_current(self) -> bool:
        return (time.time() - self.last_proof_time) < self.interval_seconds * 2


@dataclass
class DelegatedAlivenessProof:
    """Delegated proof per §9.2."""
    vouching_lct: str
    target_lct: str
    voucher_signature: bytes = b""


@dataclass
class QuorumAlivenessPolicy:
    """M-of-N hardware anchors per §9.3."""
    required_anchors: int = 2
    total_anchors: int = 3

    def is_alive(self, verified_count: int) -> bool:
        return verified_count >= self.required_anchors


# ============================================================
# §10 Enhanced Aliveness — Key Access vs Embodiment
# ============================================================

class AlivenessLevel(Enum):
    """Two levels of aliveness per §10.1."""
    KEY_ACCESS = "key_access"         # "I possess the private key"
    EMBODIMENT_STATE = "embodiment"   # "I'm in an acceptable measured state"


@dataclass
class PCRReference:
    """PCR reference values for embodiment verification per §10."""
    pcr_index: int
    expected_value: str
    tolerance: str = "exact"  # exact, drift_window

    def matches(self, actual_value: str) -> str:
        """Returns: 'match', 'drift_expected', 'drift_unexpected'."""
        if actual_value == self.expected_value:
            return "match"
        if self.tolerance == "drift_window":
            return "drift_expected"
        return "drift_unexpected"


# ============================================================
# Helpers
# ============================================================

def _mock_sign(data: bytes, key: str) -> bytes:
    return hashlib.sha256(data + key.encode()).digest()


def _mock_prove(challenge: AlivenessChallenge, key: str,
                hw_type: str = "tpm2") -> AlivenessProof:
    """Mock prover: signs challenge with given key."""
    payload = challenge.get_signing_payload()
    sig = _mock_sign(payload, key)
    return AlivenessProof(
        challenge_id=challenge.challenge_id,
        signature=sig,
        hardware_type=hw_type,
        timestamp=time.time(),
    )


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":

    # ── T1: Challenge Creation (§2.1) ────────────────────────
    print("T1: Challenge Creation (§2.1)")

    ch = AlivenessChallenge.create(
        verifier_lct_id="lct:web4:verifier:1",
        purpose="delegation",
        ttl_seconds=60.0,
    )
    check("T1.1 Nonce is 32 bytes", len(ch.nonce) == 32)
    check("T1.2 Challenge ID is UUID", len(ch.challenge_id) == 36)
    check("T1.3 Not expired yet", not ch.is_expired)
    check("T1.4 Expires in future", ch.expires_at > ch.timestamp)
    check("T1.5 Verifier set", ch.verifier_lct_id == "lct:web4:verifier:1")
    check("T1.6 Purpose set", ch.purpose == "delegation")
    check("T1.7 Signing payload includes nonce",
          ch.nonce in ch.get_signing_payload())

    # Expired challenge
    expired_ch = AlivenessChallenge(
        nonce=os.urandom(32),
        timestamp=time.time() - 120,
        challenge_id=str(uuid.uuid4()),
        expires_at=time.time() - 60,
    )
    check("T1.8 Expired challenge detected", expired_ch.is_expired)

    # ── T2: Proof and Verification (§2.2-2.3) ────────────────
    print("T2: Proof and Verification (§2.2-2.3)")

    key = "lct_public_key_alice"
    proof = _mock_prove(ch, key, "tpm2")

    check("T2.1 Proof has challenge ID", proof.challenge_id == ch.challenge_id)
    check("T2.2 Proof has signature", len(proof.signature) > 0)
    check("T2.3 Hardware type is tpm2", proof.hardware_type == "tpm2")

    result = verify_aliveness(ch, proof, key)
    check("T2.4 Verification succeeds", result.valid)
    check("T2.5 Challenge is fresh", result.challenge_fresh)
    check("T2.6 No failure type", result.failure_type == AlivenessFailureType.NONE)
    check("T2.7 Continuity score = 1.0 for TPM", result.continuity_score == 1.0)
    check("T2.8 Content score = 1.0 for TPM", result.content_score == 1.0)

    # Software binding
    sw_proof = _mock_prove(ch, key, "software")
    sw_result = verify_aliveness(ch, sw_proof, key)
    check("T2.9 Software binding valid", sw_result.valid)
    check("T2.10 Software continuity = 0.0", sw_result.continuity_score == 0.0)
    check("T2.11 Software content = 0.85", sw_result.content_score == 0.85)

    # Wrong key fails
    wrong_proof = _mock_prove(ch, "wrong_key", "tpm2")
    wrong_result = verify_aliveness(ch, wrong_proof, key)
    check("T2.12 Wrong key fails", not wrong_result.valid)
    check("T2.13 Failure type is SIGNATURE_INVALID",
          wrong_result.failure_type == AlivenessFailureType.SIGNATURE_INVALID)

    # Expired challenge fails
    exp_result = verify_aliveness(expired_ch, proof, key)
    check("T2.14 Expired challenge fails", not exp_result.valid)
    check("T2.15 Failure type is CHALLENGE_EXPIRED",
          exp_result.failure_type == AlivenessFailureType.CHALLENGE_EXPIRED)

    # ── T3: Trust Degradation Policy (§3) ────────────────────
    print("T3: Trust Degradation Policy (§3)")

    check("T3.1 7 trust actions", len(TrustAction) == 7)

    # High security policy
    check("T3.2 High security rejects failure",
          HIGH_SECURITY_POLICY.on_failure == TrustAction.REJECT)
    check("T3.3 High security rejects timeout",
          HIGH_SECURITY_POLICY.on_timeout == TrustAction.REJECT)
    check("T3.4 High security max 1 failure",
          HIGH_SECURITY_POLICY.max_consecutive_failures == 1)

    # Social policy
    check("T3.5 Social reduces on failure",
          SOCIAL_POLICY.on_failure == TrustAction.REDUCED_TRUST)
    check("T3.6 Social failure ceiling 0.2",
          SOCIAL_POLICY.failure_trust_ceiling == 0.2)
    check("T3.7 Social allows 10 failures",
          SOCIAL_POLICY.max_consecutive_failures == 10)

    # Transactional policy
    check("T3.8 Transactional requires reauth",
          TRANSACTIONAL_POLICY.on_failure == TrustAction.REQUIRE_REAUTH)
    check("T3.9 Transactional timeout ceiling 0.4",
          TRANSACTIONAL_POLICY.timeout_trust_ceiling == 0.4)

    # Action determination
    check("T3.10 Success → FULL_TRUST",
          HIGH_SECURITY_POLICY.determine_action(result) == TrustAction.FULL_TRUST)
    check("T3.11 Failure → REJECT for high security",
          HIGH_SECURITY_POLICY.determine_action(wrong_result) == TrustAction.REJECT)

    timeout_result = AlivenessVerificationResult(
        valid=False, failure_type=AlivenessFailureType.TIMEOUT)
    check("T3.12 Timeout → REDUCED_TRUST for social",
          SOCIAL_POLICY.determine_action(timeout_result) == TrustAction.REDUCED_TRUST)

    # Trust ceiling
    check("T3.13 TPM success ceiling = 1.0",
          HIGH_SECURITY_POLICY.trust_ceiling(result) == 1.0)
    check("T3.14 Software ceiling = 0.85",
          HIGH_SECURITY_POLICY.trust_ceiling(sw_result) == 0.85)
    check("T3.15 Failure ceiling = 0.0",
          HIGH_SECURITY_POLICY.trust_ceiling(wrong_result) == 0.0)
    check("T3.16 Timeout ceiling = 0.5 for social",
          SOCIAL_POLICY.trust_ceiling(timeout_result) == 0.5)

    # ── T4: Relationship LCTs (§4) ──────────────────────────
    print("T4: Relationship LCTs (§4)")

    check("T4.1 5 relationship states", len(RelationshipState) == 5)
    check("T4.2 4 relationship actions", len(RelationshipAction) == 4)

    rel = RelationshipLCT(
        relationship_id="rel:alice-bob",
        party_a="lct:alice",
        party_b="lct:bob",
        aliveness_policy=RelationshipAlivenessPolicy(),
    )
    check("T4.3 Starts PENDING", rel.state == RelationshipState.PENDING)

    # Both parties verified
    good_a = AlivenessVerificationResult(valid=True, hardware_type="tpm2")
    good_b = AlivenessVerificationResult(valid=True, hardware_type="tpm2")
    rel.verify_and_update(good_a, good_b)
    check("T4.4 Both verified → ACTIVE", rel.state == RelationshipState.ACTIVE)
    check("T4.5 No failures", rel.consecutive_failures == 0)

    # Party A fails
    bad_a = AlivenessVerificationResult(
        valid=False, failure_type=AlivenessFailureType.SIGNATURE_INVALID)
    rel.verify_and_update(bad_a, good_b)
    check("T4.6 Party A failure → SUSPENDED", rel.state == RelationshipState.SUSPENDED)
    check("T4.7 1 consecutive failure", rel.consecutive_failures == 1)

    # Both parties fail
    rel.verify_and_update(bad_a, bad_a)
    check("T4.8 Both fail → still SUSPENDED", rel.state == RelationshipState.SUSPENDED)
    check("T4.9 2 consecutive failures", rel.consecutive_failures == 2)

    # Recovery
    rel.verify_and_update(good_a, good_b)
    check("T4.10 Recovery → ACTIVE", rel.state == RelationshipState.ACTIVE)
    check("T4.11 Failures reset", rel.consecutive_failures == 0)

    # §4.3 Trust restoration
    restored = calculate_restored_trust(
        previous_trust=0.8,
        penalty=0.5,
        other_party_remembers=True,
        grants_inheritance=True,
    )
    check("T4.12 Restored trust = 0.8 × 0.5 = 0.4", restored == 0.4)

    no_memory = calculate_restored_trust(0.8, 0.5, False, True)
    check("T4.13 No memory → 0.0 trust", no_memory == 0.0)

    no_grant = calculate_restored_trust(0.8, 0.5, True, False)
    check("T4.14 No inheritance grant → 0.0", no_grant == 0.0)

    # ── T5: Error Hierarchy (§5.2) ──────────────────────────
    print("T5: Error Hierarchy (§5.2)")

    check("T5.1 HardwareAccessError is AlivenessError",
          issubclass(HardwareAccessError, AlivenessError))
    check("T5.2 HardwareCompromisedError is AlivenessError",
          issubclass(HardwareCompromisedError, AlivenessError))
    check("T5.3 ChallengeExpiredError is AlivenessError",
          issubclass(ChallengeExpiredError, AlivenessError))
    check("T5.4 KeyNotFoundError is AlivenessError",
          issubclass(KeyNotFoundError, AlivenessError))

    try:
        raise HardwareAccessError("TPM not accessible")
    except AlivenessError as e:
        check("T5.5 Hierarchy catches correctly", "TPM" in str(e))

    # ── T6: Security (§6) ───────────────────────────────────
    print("T6: Security (§6)")

    # Replay protection
    tracker = ChallengeTracker()
    check("T6.1 First challenge accepted", tracker.is_new("ch-001"))
    check("T6.2 Replay rejected", not tracker.is_new("ch-001"))
    check("T6.3 Different challenge accepted", tracker.is_new("ch-002"))

    # Rate limiting
    limiter = RateLimiter(max_per_minute=3)
    check("T6.4 First request allowed", limiter.allow())
    check("T6.5 Second request allowed", limiter.allow())
    check("T6.6 Third request allowed", limiter.allow())
    check("T6.7 Fourth request rate limited", not limiter.allow())

    # ── T7: T3 Integration (§7) ─────────────────────────────
    print("T7: T3 Integration (§7)")

    base_t3 = T3Tensor(talent=0.9, training=0.85, temperament=0.88)

    # Valid result — no change
    adj = apply_aliveness_to_t3(base_t3, result, HIGH_SECURITY_POLICY)
    check("T7.1 Valid → no T3 change", adj.talent == 0.9)

    # Failed result — apply ceiling
    adj_fail = apply_aliveness_to_t3(base_t3, wrong_result, HIGH_SECURITY_POLICY)
    check("T7.2 Failed → talent capped to 0.0", adj_fail.talent == 0.0)
    check("T7.3 Failed → temperament preserved",
          adj_fail.temperament == base_t3.temperament)

    # Timeout with social policy
    adj_timeout = apply_aliveness_to_t3(base_t3, timeout_result, SOCIAL_POLICY)
    check("T7.4 Timeout → talent capped to 0.5", adj_timeout.talent == 0.5)

    # ATP transfer threshold
    check("T7.5 Small transfer no aliveness",
          not requires_aliveness_for_transfer(50, TRANSACTIONAL_POLICY))
    check("T7.6 Large transfer needs aliveness",
          requires_aliveness_for_transfer(150, TRANSACTIONAL_POLICY))
    check("T7.7 Any amount for high security",
          requires_aliveness_for_transfer(1, HIGH_SECURITY_POLICY))

    # ── T8: Future Extensions (§9) ──────────────────────────
    print("T8: Future Extensions (§9)")

    # Continuous aliveness stream
    stream = ContinuousAlivenessStream(interval_seconds=60.0)
    check("T8.1 Stream not current (no proofs)", not stream.is_current)
    stream.add_proof(AlivenessProof(
        challenge_id="stream-1",
        signature=b"sig",
        hardware_type="tpm2",
        timestamp=time.time(),
    ))
    check("T8.2 Stream current after proof", stream.is_current)

    # Delegated proof
    dp = DelegatedAlivenessProof(
        vouching_lct="lct:web4:trusted_node",
        target_lct="lct:web4:unreachable_node",
    )
    check("T8.3 Delegated proof has voucher", dp.vouching_lct != "")
    check("T8.4 Delegated proof has target", dp.target_lct != "")

    # Quorum
    qp = QuorumAlivenessPolicy(required_anchors=2, total_anchors=3)
    check("T8.5 1-of-3 not alive", not qp.is_alive(1))
    check("T8.6 2-of-3 is alive", qp.is_alive(2))
    check("T8.7 3-of-3 is alive", qp.is_alive(3))

    # ── T9: Enhanced Aliveness (§10) ────────────────────────
    print("T9: Enhanced Aliveness (§10)")

    check("T9.1 2 aliveness levels", len(AlivenessLevel) == 2)
    check("T9.2 Key access level",
          AlivenessLevel.KEY_ACCESS.value == "key_access")
    check("T9.3 Embodiment level",
          AlivenessLevel.EMBODIMENT_STATE.value == "embodiment")

    # PCR reference
    pcr = PCRReference(pcr_index=7, expected_value="abc123", tolerance="exact")
    check("T9.4 PCR exact match", pcr.matches("abc123") == "match")
    check("T9.5 PCR unexpected drift", pcr.matches("xyz789") == "drift_unexpected")

    pcr_window = PCRReference(pcr_index=7, expected_value="abc123",
                              tolerance="drift_window")
    check("T9.6 PCR drift window → expected",
          pcr_window.matches("xyz789") == "drift_expected")

    # ── T10: 8 Failure Types (§2.3) ─────────────────────────
    print("T10: Failure Types")

    check("T10.1 8 failure types", len(AlivenessFailureType) == 8)
    check("T10.2 NONE for success",
          AlivenessFailureType.NONE.value == "none")
    check("T10.3 PCR_DRIFT_EXPECTED",
          AlivenessFailureType.PCR_DRIFT_EXPECTED.value == "pcr_drift_expected")
    check("T10.4 PCR_DRIFT_UNEXPECTED",
          AlivenessFailureType.PCR_DRIFT_UNEXPECTED.value == "pcr_drift_unexpected")

    # ── T11: End-to-End Flow (§8) ───────────────────────────
    print("T11: End-to-End Flow (§8)")

    # §8.1 Normal operation
    prover_key = "lct:web4:thor_sage:pub_key"
    e2e_challenge = AlivenessChallenge.create(
        verifier_lct_id="lct:web4:dp_human",
        purpose="delegation",
        ttl_seconds=60.0,
    )
    e2e_proof = _mock_prove(e2e_challenge, prover_key, "tpm2")
    e2e_result = verify_aliveness(e2e_challenge, e2e_proof, prover_key)
    check("T11.1 Normal flow succeeds", e2e_result.valid)
    check("T11.2 Full trust action",
          HIGH_SECURITY_POLICY.determine_action(e2e_result) == TrustAction.FULL_TRUST)

    # §8.2 Hardware lost — restored with new key
    new_key = "lct:web4:thor_sage:new_pub_key"
    lost_proof = _mock_prove(e2e_challenge, new_key, "tpm2")
    lost_result = verify_aliveness(e2e_challenge, lost_proof, prover_key)
    check("T11.3 New key fails verification", not lost_result.valid)
    check("T11.4 Social policy → REDUCED_TRUST",
          SOCIAL_POLICY.determine_action(lost_result) == TrustAction.REDUCED_TRUST)

    # §8.3 Timeout
    timeout_r = AlivenessVerificationResult(
        valid=False, failure_type=AlivenessFailureType.TIMEOUT)
    check("T11.5 Timeout → REDUCED_TRUST for transactional",
          TRANSACTIONAL_POLICY.determine_action(timeout_r) == TrustAction.REDUCED_TRUST)
    check("T11.6 Timeout ceiling = 0.4",
          TRANSACTIONAL_POLICY.trust_ceiling(timeout_r) == 0.4)

    # ── T12: Relationship Lifecycle (§4.2) ──────────────────
    print("T12: Relationship Lifecycle (§4.2)")

    life = RelationshipLCT(
        relationship_id="rel:lifecycle",
        party_a="lct:a",
        party_b="lct:b",
        aliveness_policy=RelationshipAlivenessPolicy(
            on_party_a_failure=RelationshipAction.SUSPEND,
            on_both_failure=RelationshipAction.TERMINATE,
            allow_restoration=True,
        ),
    )

    # PENDING → ACTIVE
    life.verify_and_update(good_a, good_b)
    check("T12.1 PENDING → ACTIVE", life.state == RelationshipState.ACTIVE)

    # ACTIVE → SUSPENDED (party A fails)
    life.verify_and_update(bad_a, good_b)
    check("T12.2 ACTIVE → SUSPENDED", life.state == RelationshipState.SUSPENDED)

    # SUSPENDED → ACTIVE (recovery)
    life.verify_and_update(good_a, good_b)
    check("T12.3 SUSPENDED → ACTIVE", life.state == RelationshipState.ACTIVE)

    # ACTIVE → TERMINATED (both fail)
    life.verify_and_update(bad_a, bad_a)
    check("T12.4 Both fail → TERMINATED", life.state == RelationshipState.TERMINATED)

    # Restoration
    check("T12.5 Restoration allowed", life.aliveness_policy.allow_restoration)
    restored_trust = calculate_restored_trust(0.8, 0.5, True, True)
    check("T12.6 Restored at 50% of 0.8 = 0.4", restored_trust == 0.4)

    # ════════════════════════════════════════════════════════
    print()
    print("=" * 60)
    total = _pass + _fail
    print(f"AVP Core Protocol: {_pass}/{total} checks passed")
    if _fail:
        print(f"  ({_fail} FAILED)")
    else:
        print("  All checks passed!")
    print("=" * 60)
