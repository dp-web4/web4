"""
Trust Degradation Policy and Relationship LCT
==============================================

Structures for external entities to configure how they handle
aliveness verification outcomes, and for modeling relationships
between LCTs that require mutual aliveness.

Part of the Aliveness Verification Protocol (AVP).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum


# =============================================================================
# Trust Actions and States
# =============================================================================

class TrustAction(Enum):
    """Actions an external entity can take based on verification result."""
    FULL_TRUST = "full_trust"           # Accept at full T3 ceiling
    REDUCED_TRUST = "reduced_trust"     # Accept at reduced ceiling
    REQUIRE_REAUTH = "require_reauth"   # Demand re-authentication
    SUSPEND = "suspend"                 # Temporarily suspend relationship
    TERMINATE = "terminate"             # End relationship
    REJECT = "reject"                   # Reject this interaction only
    LEGACY_TRUST = "legacy_trust"       # Fall back to non-AVP trust model


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


class RelationshipType(Enum):
    """Types of relationships between LCTs."""
    PEER = "peer"                # Equal standing
    HIERARCHICAL = "hierarchical"  # Parent-child authority
    SERVICE = "service"          # Service provider/consumer
    DELEGATION = "delegation"    # Delegated authority
    FEDERATION = "federation"    # Cross-society federation
    WITNESS = "witness"          # Observation relationship


# =============================================================================
# Trust Degradation Policy
# =============================================================================

@dataclass
class TrustDegradationPolicy:
    """
    Policy for how an external entity handles aliveness verification.

    Each entity configures this based on their risk tolerance
    and relationship with the target LCT.

    External entities are autonomous - they decide their own policies.
    This structure just provides a standard way to express those policies.
    """

    # What to do on successful verification
    on_success: TrustAction = TrustAction.FULL_TRUST

    # What to do on failed verification (signature invalid, key mismatch)
    on_failure: TrustAction = TrustAction.REJECT

    # What to do when verification times out
    on_timeout: TrustAction = TrustAction.REDUCED_TRUST

    # What to do when target doesn't support AVP
    on_unsupported: TrustAction = TrustAction.LEGACY_TRUST

    # Trust multipliers for different failure modes
    failure_trust_ceiling: float = 0.0     # Max trust on signature failure
    timeout_trust_ceiling: float = 0.3     # Max trust on timeout
    software_trust_ceiling: float = 0.85   # Max trust for software binding

    # Which operations require aliveness verification
    # Empty list = never require, ["*"] = always require
    require_aliveness_for: List[str] = field(default_factory=list)

    # How long to cache successful verification
    aliveness_cache_duration: timedelta = timedelta(minutes=5)

    # How many failed verifications before relationship action
    max_consecutive_failures: int = 3

    # Grace period before acting on failures
    grace_period: timedelta = timedelta(minutes=1)

    def should_require_aliveness(self, operation: str) -> bool:
        """Check if an operation requires aliveness verification."""
        if not self.require_aliveness_for:
            return False
        if "*" in self.require_aliveness_for:
            return True
        return operation in self.require_aliveness_for

    def get_trust_ceiling_for_result(
        self,
        success: bool,
        hardware_type: str,
        timed_out: bool = False
    ) -> float:
        """Get trust ceiling based on verification outcome."""
        if success:
            if hardware_type == "software":
                return self.software_trust_ceiling
            return 1.0

        if timed_out:
            return self.timeout_trust_ceiling

        return self.failure_trust_ceiling

    def to_dict(self) -> Dict[str, Any]:
        return {
            "on_success": self.on_success.value,
            "on_failure": self.on_failure.value,
            "on_timeout": self.on_timeout.value,
            "on_unsupported": self.on_unsupported.value,
            "failure_trust_ceiling": self.failure_trust_ceiling,
            "timeout_trust_ceiling": self.timeout_trust_ceiling,
            "software_trust_ceiling": self.software_trust_ceiling,
            "require_aliveness_for": self.require_aliveness_for,
            "aliveness_cache_duration_seconds": self.aliveness_cache_duration.total_seconds(),
            "max_consecutive_failures": self.max_consecutive_failures,
            "grace_period_seconds": self.grace_period.total_seconds()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustDegradationPolicy":
        return cls(
            on_success=TrustAction(data.get("on_success", "full_trust")),
            on_failure=TrustAction(data.get("on_failure", "reject")),
            on_timeout=TrustAction(data.get("on_timeout", "reduced_trust")),
            on_unsupported=TrustAction(data.get("on_unsupported", "legacy_trust")),
            failure_trust_ceiling=data.get("failure_trust_ceiling", 0.0),
            timeout_trust_ceiling=data.get("timeout_trust_ceiling", 0.3),
            software_trust_ceiling=data.get("software_trust_ceiling", 0.85),
            require_aliveness_for=data.get("require_aliveness_for", []),
            aliveness_cache_duration=timedelta(
                seconds=data.get("aliveness_cache_duration_seconds", 300)
            ),
            max_consecutive_failures=data.get("max_consecutive_failures", 3),
            grace_period=timedelta(
                seconds=data.get("grace_period_seconds", 60)
            )
        )


# =============================================================================
# Pre-built Policy Templates
# =============================================================================

class PolicyTemplates:
    """Standard policy templates for common use cases."""

    @staticmethod
    def high_security() -> TrustDegradationPolicy:
        """
        High-security policy (bank, healthcare, critical infrastructure).

        - Requires aliveness for all operations
        - Rejects on any failure
        - Short cache duration
        - No tolerance for failures
        """
        return TrustDegradationPolicy(
            on_success=TrustAction.FULL_TRUST,
            on_failure=TrustAction.REJECT,
            on_timeout=TrustAction.REJECT,
            on_unsupported=TrustAction.REJECT,
            failure_trust_ceiling=0.0,
            timeout_trust_ceiling=0.0,
            require_aliveness_for=["*"],
            aliveness_cache_duration=timedelta(seconds=30),
            max_consecutive_failures=1,
            grace_period=timedelta(seconds=0)
        )

    @staticmethod
    def relationship_preserving() -> TrustDegradationPolicy:
        """
        Relationship-preserving policy (social, collaborative).

        - Tolerates temporary failures
        - Reduces trust rather than rejecting
        - Longer cache duration
        - Patient with failures
        """
        return TrustDegradationPolicy(
            on_success=TrustAction.FULL_TRUST,
            on_failure=TrustAction.REDUCED_TRUST,
            on_timeout=TrustAction.REDUCED_TRUST,
            on_unsupported=TrustAction.LEGACY_TRUST,
            failure_trust_ceiling=0.2,
            timeout_trust_ceiling=0.5,
            require_aliveness_for=["relationship_changes", "high_value"],
            aliveness_cache_duration=timedelta(hours=1),
            max_consecutive_failures=10,
            grace_period=timedelta(hours=1)
        )

    @staticmethod
    def transactional() -> TrustDegradationPolicy:
        """
        Transactional policy (commerce, API).

        - Requires aliveness for high-value operations
        - Moderate tolerance
        - Standard cache duration
        """
        return TrustDegradationPolicy(
            on_success=TrustAction.FULL_TRUST,
            on_failure=TrustAction.REQUIRE_REAUTH,
            on_timeout=TrustAction.REDUCED_TRUST,
            on_unsupported=TrustAction.LEGACY_TRUST,
            failure_trust_ceiling=0.0,
            timeout_trust_ceiling=0.4,
            require_aliveness_for=["transactions_over_100_atp", "authorization_changes"],
            aliveness_cache_duration=timedelta(minutes=15),
            max_consecutive_failures=3,
            grace_period=timedelta(minutes=5)
        )

    @staticmethod
    def permissive() -> TrustDegradationPolicy:
        """
        Permissive policy (public services, low-risk).

        - Rarely requires aliveness
        - Falls back to legacy trust
        - Very tolerant
        """
        return TrustDegradationPolicy(
            on_success=TrustAction.FULL_TRUST,
            on_failure=TrustAction.LEGACY_TRUST,
            on_timeout=TrustAction.LEGACY_TRUST,
            on_unsupported=TrustAction.LEGACY_TRUST,
            failure_trust_ceiling=0.5,
            timeout_trust_ceiling=0.7,
            require_aliveness_for=[],  # Never require
            aliveness_cache_duration=timedelta(hours=24),
            max_consecutive_failures=100,
            grace_period=timedelta(days=1)
        )


# =============================================================================
# Relationship Aliveness Policy
# =============================================================================

@dataclass
class RelationshipAlivenessPolicy:
    """How aliveness affects a specific relationship."""

    # Verification requirements
    require_mutual_aliveness: bool = True    # Both parties must verify
    verification_interval: timedelta = timedelta(hours=24)

    # What happens on aliveness failure for each party
    on_party_a_failure: RelationshipAction = RelationshipAction.SUSPEND
    on_party_b_failure: RelationshipAction = RelationshipAction.SUSPEND
    on_both_failure: RelationshipAction = RelationshipAction.SUSPEND

    # Grace period before relationship state changes
    grace_period: timedelta = timedelta(hours=1)

    # Can relationship be restored after termination?
    allow_restoration: bool = True

    # Trust penalty on restoration (start at X% of previous trust)
    restoration_trust_penalty: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "require_mutual_aliveness": self.require_mutual_aliveness,
            "verification_interval_seconds": self.verification_interval.total_seconds(),
            "on_party_a_failure": self.on_party_a_failure.value,
            "on_party_b_failure": self.on_party_b_failure.value,
            "on_both_failure": self.on_both_failure.value,
            "grace_period_seconds": self.grace_period.total_seconds(),
            "allow_restoration": self.allow_restoration,
            "restoration_trust_penalty": self.restoration_trust_penalty
        }


# =============================================================================
# Mutual Trust Record
# =============================================================================

@dataclass
class MutualTrustRecord:
    """Trust accumulated between two parties in a relationship."""

    # Trust scores
    party_a_trusts_b: float = 0.0
    party_b_trusts_a: float = 0.0

    # Interaction history
    successful_interactions: int = 0
    failed_interactions: int = 0

    # Last verification times
    party_a_last_verified: Optional[datetime] = None
    party_b_last_verified: Optional[datetime] = None

    # Consecutive failures
    party_a_consecutive_failures: int = 0
    party_b_consecutive_failures: int = 0

    @property
    def mutual_trust(self) -> float:
        """Symmetric trust score (geometric mean)."""
        if self.party_a_trusts_b <= 0 or self.party_b_trusts_a <= 0:
            return 0.0
        return (self.party_a_trusts_b * self.party_b_trusts_a) ** 0.5

    @property
    def trust_asymmetry(self) -> float:
        """How asymmetric the trust is (0 = symmetric, 1 = one-sided)."""
        total = self.party_a_trusts_b + self.party_b_trusts_a
        if total == 0:
            return 0.0
        diff = abs(self.party_a_trusts_b - self.party_b_trusts_a)
        return diff / total

    def record_verification(self, party: str, success: bool):
        """Record a verification attempt."""
        now = datetime.now(timezone.utc)

        if party == "a":
            self.party_a_last_verified = now
            if success:
                self.party_a_consecutive_failures = 0
            else:
                self.party_a_consecutive_failures += 1
        elif party == "b":
            self.party_b_last_verified = now
            if success:
                self.party_b_consecutive_failures = 0
            else:
                self.party_b_consecutive_failures += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "party_a_trusts_b": self.party_a_trusts_b,
            "party_b_trusts_a": self.party_b_trusts_a,
            "successful_interactions": self.successful_interactions,
            "failed_interactions": self.failed_interactions,
            "party_a_last_verified": self.party_a_last_verified.isoformat() if self.party_a_last_verified else None,
            "party_b_last_verified": self.party_b_last_verified.isoformat() if self.party_b_last_verified else None,
            "party_a_consecutive_failures": self.party_a_consecutive_failures,
            "party_b_consecutive_failures": self.party_b_consecutive_failures,
            "mutual_trust": self.mutual_trust,
            "trust_asymmetry": self.trust_asymmetry
        }


# =============================================================================
# LCT Reference (for relationships)
# =============================================================================

@dataclass
class LCTReference:
    """Reference to an LCT for use in relationships."""
    lct_id: str
    public_key: str                    # For aliveness verification
    hardware_type: str                 # Expected hardware type
    entity_type: str                   # agent, society, role, etc.

    # Snapshot of trust at relationship formation
    initial_trust_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lct_id": self.lct_id,
            "public_key": self.public_key,
            "hardware_type": self.hardware_type,
            "entity_type": self.entity_type,
            "initial_trust_score": self.initial_trust_score
        }


# =============================================================================
# Relationship LCT
# =============================================================================

@dataclass
class RelationshipLCT:
    """
    An LCT representing a relationship between two entities.

    Relationships are bidirectional and can require both parties
    to maintain aliveness for the relationship to remain active.

    Key insight: When hardware binding is lost, the relationship
    is affected - but the decision of how to handle it belongs
    to the other party (external entity autonomy).
    """

    # Relationship identity
    relationship_id: str              # lct:web4:relationship:{hash}
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Parties
    party_a: Optional[LCTReference] = None
    party_b: Optional[LCTReference] = None

    # Relationship type
    relationship_type: RelationshipType = RelationshipType.PEER

    # Aliveness requirements
    aliveness_policy: RelationshipAlivenessPolicy = field(
        default_factory=RelationshipAlivenessPolicy
    )

    # Current state
    state: RelationshipState = RelationshipState.PENDING

    # Trust accumulated in this relationship
    mutual_trust: MutualTrustRecord = field(default_factory=MutualTrustRecord)

    # State change history
    state_history: List[Dict[str, Any]] = field(default_factory=list)

    def transition_state(self, new_state: RelationshipState, reason: str):
        """Record state transition."""
        old_state = self.state
        self.state = new_state
        self.state_history.append({
            "from_state": old_state.value,
            "to_state": new_state.value,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def check_aliveness_requirements(self) -> Dict[str, Any]:
        """
        Check if aliveness requirements are met.

        Returns status for each party and recommended action.
        """
        now = datetime.now(timezone.utc)
        policy = self.aliveness_policy

        result = {
            "party_a_status": "unknown",
            "party_b_status": "unknown",
            "recommended_action": RelationshipAction.CONTINUE,
            "needs_verification": []
        }

        # Check party A
        if self.mutual_trust.party_a_last_verified:
            time_since = now - self.mutual_trust.party_a_last_verified
            if time_since > policy.verification_interval:
                result["party_a_status"] = "verification_needed"
                result["needs_verification"].append("a")
            elif self.mutual_trust.party_a_consecutive_failures > 0:
                result["party_a_status"] = "failed"
            else:
                result["party_a_status"] = "verified"
        else:
            result["party_a_status"] = "never_verified"
            result["needs_verification"].append("a")

        # Check party B
        if self.mutual_trust.party_b_last_verified:
            time_since = now - self.mutual_trust.party_b_last_verified
            if time_since > policy.verification_interval:
                result["party_b_status"] = "verification_needed"
                result["needs_verification"].append("b")
            elif self.mutual_trust.party_b_consecutive_failures > 0:
                result["party_b_status"] = "failed"
            else:
                result["party_b_status"] = "verified"
        else:
            result["party_b_status"] = "never_verified"
            result["needs_verification"].append("b")

        # Determine recommended action
        a_failed = result["party_a_status"] == "failed"
        b_failed = result["party_b_status"] == "failed"

        if a_failed and b_failed:
            result["recommended_action"] = policy.on_both_failure
        elif a_failed:
            result["recommended_action"] = policy.on_party_a_failure
        elif b_failed:
            result["recommended_action"] = policy.on_party_b_failure

        return result

    def calculate_restored_trust(
        self,
        restoring_party: str,
        other_party_grants_inheritance: bool = False
    ) -> float:
        """
        Calculate initial trust for restored relationship.

        When hardware binding is lost and restored, the entity
        carries experience (DNA) but must re-earn the relationship.
        The other party may choose to give a "head start" based
        on previous positive history.
        """
        # Base: start from zero (true perishability)
        base_trust = 0.0

        if not other_party_grants_inheritance:
            return base_trust

        # Get previous trust
        if restoring_party == "a":
            previous_trust = self.mutual_trust.party_b_trusts_a
        else:
            previous_trust = self.mutual_trust.party_a_trusts_b

        # Apply restoration penalty
        inheritance_factor = self.aliveness_policy.restoration_trust_penalty
        inherited = previous_trust * inheritance_factor

        return inherited

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "created_at": self.created_at.isoformat(),
            "party_a": self.party_a.to_dict() if self.party_a else None,
            "party_b": self.party_b.to_dict() if self.party_b else None,
            "relationship_type": self.relationship_type.value,
            "aliveness_policy": self.aliveness_policy.to_dict(),
            "state": self.state.value,
            "mutual_trust": self.mutual_trust.to_dict(),
            "state_history": self.state_history
        }


# =============================================================================
# Restoration Context
# =============================================================================

@dataclass
class RestorationContext:
    """Context for relationship restoration after hardware loss."""

    # The party being restored
    restoring_party_lct_id: str

    # New hardware binding details
    new_public_key: str
    new_hardware_type: str

    # Whether the other party remembers and grants inheritance
    other_party_remembers: bool = True
    other_party_grants_inheritance: bool = False

    # Reason for restoration
    restoration_reason: str = "hardware_replacement"

    # Timestamp
    restoration_requested_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
