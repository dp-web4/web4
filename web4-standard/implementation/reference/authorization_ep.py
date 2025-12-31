"""
Authorization Epistemic Proprioception

Predicts authorization abuse/regret BEFORE permissions are granted,
enabling proactive access control and permission management.

The Third Web4 Security EP Domain:
1. Grounding EP (Session 107): "Will grounding fail?" → Identity security
2. Relationship EP (Session 108): "Will relationship degrade?" → Trust security
3. Authorization EP (Session 109): "Will permission be abused?" → Access security

The EP Question:
"Given identity state, relationship context, and permission characteristics,
will granting this authorization be regrettable?"

Pattern Structure:
- AuthorizationContext: Who, what permissions, relationship state
- PermissionCharacteristics: Scope, duration, sensitivity
- AuthorizationOutcome: Abuse, legitimate use, over-privileged

Stages:
1. Immature: Grant → Monitor → Revoke if abused (reactive)
2. Learning: Predict abuse before granting (pattern-based)
3. Mature: Adjust permissions proactively (high-confidence)

Created: 2025-12-30
Session: 109 (Legion autonomous research)
Foundation: Sessions 107 (Grounding EP), 108 (Relationship EP)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import math


class AuthorizationRiskPattern(Enum):
    """Risk patterns that predict authorization abuse."""

    # Identity/Grounding risks
    LOW_IDENTITY_COHERENCE = "low_identity_coherence"
    GROUNDING_UNSTABLE = "grounding_unstable"
    NEW_IDENTITY = "new_identity"

    # Relationship risks
    LOW_TRUST = "low_trust"
    ADVERSARIAL_STANCE = "adversarial_stance"
    RELATIONSHIP_DECLINING = "relationship_declining"
    RECENT_VIOLATION = "recent_violation"

    # Permission characteristics
    OVERLY_BROAD_SCOPE = "overly_broad_scope"
    SENSITIVE_RESOURCES = "sensitive_resources"
    PERMANENT_DURATION = "permanent_duration"
    CASCADING_PERMISSIONS = "cascading_permissions"  # Can grant to others

    # Historical patterns
    PERMISSION_ESCALATION = "permission_escalation"  # Requesting more over time
    FREQUENT_REVOCATIONS = "frequent_revocations"  # History of abuse
    UNUSUAL_REQUEST = "unusual_request"  # Doesn't match typical pattern


class PermissionScope(Enum):
    """Scope of permission."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    GRANT = "grant"  # Can grant to others
    ADMIN = "admin"  # Full control


@dataclass
class Permission:
    """Permission being requested."""
    resource_type: str  # "storage", "compute", "network", "data"
    resource_id: str
    scope: Set[PermissionScope]
    duration: Optional[timedelta]  # None = permanent
    sensitivity_level: float  # 0.0-1.0 (1.0 = highly sensitive)
    can_delegate: bool = False  # Can grant to others?

    description: str = ""

    def is_high_risk(self) -> bool:
        """Is this a high-risk permission?"""
        return (
            self.sensitivity_level > 0.7 or
            PermissionScope.ADMIN in self.scope or
            PermissionScope.GRANT in self.scope or
            (PermissionScope.DELETE in self.scope and self.sensitivity_level > 0.5)
        )


@dataclass
class AuthorizationContext:
    """Context for authorization decision."""
    # Requester identity
    requester_lct: str
    grounding_ci: float  # From grounding EP
    identity_age: timedelta  # How long has this identity existed?

    # Relationship context
    relationship_lct: Optional[str]
    relationship_trust_avg: float  # Average of trust tensor
    relationship_ci: float  # From relationship EP
    relationship_stance_collaborative: float  # 0.0-1.0

    # Permission history
    current_permissions: List[str]  # Permissions already held
    permission_count: int
    revocations: int  # Times permissions were revoked
    violations: int  # Times permissions were abused

    # Request characteristics
    permission_requested: Permission
    justification_provided: bool
    urgency_claimed: str  # "low", "medium", "high", "critical"

    # Context
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AuthorizationOutcome:
    """Outcome of granting authorization."""
    granted: bool

    # If granted, what happened?
    abused: bool  # Was permission misused?
    legitimate_use: bool  # Used appropriately?
    over_privileged: bool  # Granted more than needed?
    delegated_inappropriately: bool  # Granted to others when shouldn't?

    # Metrics
    usage_frequency: float  # How often was permission used?
    violation_count: int  # Specific violations
    revocation_required: bool
    time_to_revocation: Optional[timedelta]

    # If not granted, was it correct?
    grant_would_have_been_safe: Optional[bool] = None


@dataclass
class AuthorizationPattern:
    """Complete pattern for learning."""
    pattern_id: str
    timestamp: str

    # The core relationship
    context: AuthorizationContext
    outcome: AuthorizationOutcome

    # Learning metadata
    prediction_error: Optional[float] = None


@dataclass
class AuthorizationPrediction:
    """Predicted authorization outcome."""
    predicted_abuse_probability: float  # 0.0-1.0
    predicted_legitimate_use: float  # 0.0-1.0
    confidence: float  # 0.0-1.0

    risk_patterns: List[AuthorizationRiskPattern]
    risk_score: float  # 0.0-1.0

    reasoning: str
    similar_pattern_count: int

    def should_deny(self, abuse_threshold: float = 0.6) -> bool:
        """Should we deny this authorization request?"""
        return (
            self.predicted_abuse_probability >= abuse_threshold and
            self.confidence >= 0.5
        )

    def should_restrict(self, restriction_threshold: float = 0.4) -> bool:
        """Should we grant with restrictions?"""
        return (
            self.predicted_abuse_probability >= restriction_threshold and
            self.predicted_abuse_probability < 0.6 and
            self.confidence >= 0.5
        )


class RestrictionStrategy(Enum):
    """Permission restriction strategies."""
    TIME_LIMIT = "time_limit"  # Grant for limited time
    SCOPE_REDUCTION = "scope_reduction"  # Reduce permission scope
    REQUIRE_APPROVAL = "require_approval"  # Require approval for each use
    AUDIT_ALL_USE = "audit_all_use"  # Log all uses
    REVOKE_ON_VIOLATION = "revoke_on_violation"  # Auto-revoke if misused
    PROBATION_PERIOD = "probation_period"  # Grant tentatively, monitor closely
    DENY_GRANT = "deny_grant"  # Don't allow delegation
    FULL_GRANT = "full_grant"  # No restrictions
    DENY = "deny"  # Reject completely


@dataclass
class AdjustedAuthorization:
    """Adjusted authorization based on prediction."""
    strategy: RestrictionStrategy
    granted: bool
    restricted_permission: Optional[Permission]  # Adjusted permission if granted
    requirements: Dict
    expected_abuse_reduction: float  # How much abuse prevented
    reasoning: str


class AuthorizationEPPredictor:
    """Predicts authorization abuse before granting permissions."""

    def __init__(self, pattern_library: Optional[List[AuthorizationPattern]] = None):
        self.patterns = pattern_library or []
        self.min_patterns_for_prediction = 3

    def predict_authorization(
        self,
        context: AuthorizationContext
    ) -> AuthorizationPrediction:
        """Predict authorization outcome before granting."""

        # 1. Detect risk patterns
        risk_patterns = self._detect_risk_patterns(context)

        # 2. Find similar historical patterns
        similar_patterns = self._find_similar_patterns(context)

        # 3. Calculate prediction
        if len(similar_patterns) >= self.min_patterns_for_prediction:
            abuse_prob, legit_prob, confidence = self._predict_from_patterns(similar_patterns)
        else:
            abuse_prob, legit_prob, confidence = self._predict_from_risks(context, risk_patterns)

        # 4. Calculate risk score
        risk_score = self._calculate_risk_score(context, risk_patterns)

        # 5. Generate reasoning
        reasoning = self._generate_reasoning(context, risk_patterns, similar_patterns, abuse_prob)

        return AuthorizationPrediction(
            predicted_abuse_probability=abuse_prob,
            predicted_legitimate_use=legit_prob,
            confidence=confidence,
            risk_patterns=risk_patterns,
            risk_score=risk_score,
            reasoning=reasoning,
            similar_pattern_count=len(similar_patterns)
        )

    def _detect_risk_patterns(
        self,
        context: AuthorizationContext
    ) -> List[AuthorizationRiskPattern]:
        """Detect risk patterns from context."""
        risks = []

        # Identity/Grounding risks
        if context.grounding_ci < 0.6:
            risks.append(AuthorizationRiskPattern.GROUNDING_UNSTABLE)

        if context.grounding_ci < 0.4:
            risks.append(AuthorizationRiskPattern.LOW_IDENTITY_COHERENCE)

        if context.identity_age < timedelta(days=7):
            risks.append(AuthorizationRiskPattern.NEW_IDENTITY)

        # Relationship risks
        if context.relationship_trust_avg < 0.5:
            risks.append(AuthorizationRiskPattern.LOW_TRUST)

        if context.relationship_ci < 0.5:
            risks.append(AuthorizationRiskPattern.RELATIONSHIP_DECLINING)

        if context.relationship_stance_collaborative < 0.5:
            risks.append(AuthorizationRiskPattern.ADVERSARIAL_STANCE)

        if context.violations > 0:
            risks.append(AuthorizationRiskPattern.RECENT_VIOLATION)

        # Permission characteristics
        perm = context.permission_requested

        if perm.sensitivity_level > 0.7:
            risks.append(AuthorizationRiskPattern.SENSITIVE_RESOURCES)

        if perm.duration is None:  # Permanent
            risks.append(AuthorizationRiskPattern.PERMANENT_DURATION)

        if perm.can_delegate or PermissionScope.GRANT in perm.scope:
            risks.append(AuthorizationRiskPattern.CASCADING_PERMISSIONS)

        if len(perm.scope) > 3:  # Broad scope
            risks.append(AuthorizationRiskPattern.OVERLY_BROAD_SCOPE)

        # Historical patterns
        if context.permission_count > context.identity_age.days:
            # Requesting permissions faster than 1/day
            risks.append(AuthorizationRiskPattern.PERMISSION_ESCALATION)

        if context.revocations > 2:
            risks.append(AuthorizationRiskPattern.FREQUENT_REVOCATIONS)

        return risks

    def _find_similar_patterns(
        self,
        context: AuthorizationContext
    ) -> List[AuthorizationPattern]:
        """Find similar authorization patterns from history."""
        similar = []

        for pattern in self.patterns:
            similarity = self._calculate_similarity(context, pattern.context)
            if similarity > 0.6:
                similar.append(pattern)

        return similar

    def _calculate_similarity(
        self,
        current: AuthorizationContext,
        pattern: AuthorizationContext
    ) -> float:
        """Calculate similarity between contexts."""
        similarities = []

        # Trust similarity
        trust_sim = 1.0 - abs(current.relationship_trust_avg - pattern.relationship_trust_avg)
        similarities.append(trust_sim)

        # CI similarity
        ci_sim = 1.0 - abs(current.relationship_ci - pattern.relationship_ci)
        similarities.append(ci_sim)

        # Permission sensitivity similarity
        sens_sim = 1.0 - abs(
            current.permission_requested.sensitivity_level -
            pattern.permission_requested.sensitivity_level
        )
        similarities.append(sens_sim)

        # Violation history similarity
        if current.violations > 0 and pattern.violations > 0:
            similarities.append(0.8)
        elif current.violations == 0 and pattern.violations == 0:
            similarities.append(1.0)
        else:
            similarities.append(0.4)

        return sum(similarities) / len(similarities)

    def _predict_from_patterns(
        self,
        similar_patterns: List[AuthorizationPattern]
    ) -> Tuple[float, float, float]:
        """Predict from similar patterns."""
        abuse_cases = sum(1 for p in similar_patterns if p.outcome.abused)
        legit_cases = sum(1 for p in similar_patterns if p.outcome.legitimate_use)

        abuse_prob = abuse_cases / len(similar_patterns)
        legit_prob = legit_cases / len(similar_patterns)

        # Confidence based on pattern count
        confidence = min(1.0, len(similar_patterns) / 10.0)

        return abuse_prob, legit_prob, confidence

    def _predict_from_risks(
        self,
        context: AuthorizationContext,
        risks: List[AuthorizationRiskPattern]
    ) -> Tuple[float, float, float]:
        """Predict from risk patterns when insufficient historical data."""
        if not risks:
            return 0.1, 0.8, 0.4  # Low risk, high legitimacy, moderate confidence

        # High-severity risks
        severe_risks = {
            AuthorizationRiskPattern.FREQUENT_REVOCATIONS,
            AuthorizationRiskPattern.RECENT_VIOLATION,
            AuthorizationRiskPattern.ADVERSARIAL_STANCE,
            AuthorizationRiskPattern.LOW_IDENTITY_COHERENCE
        }

        severe_count = sum(1 for r in risks if r in severe_risks)
        moderate_count = len(risks) - severe_count

        # Calculate abuse probability
        abuse_prob = min(1.0, severe_count * 0.25 + moderate_count * 0.10)

        # Legitimate use inversely related to abuse
        legit_prob = 1.0 - abuse_prob

        # Moderate confidence in risk-based prediction
        confidence = 0.5

        return abuse_prob, legit_prob, confidence

    def _calculate_risk_score(
        self,
        context: AuthorizationContext,
        risks: List[AuthorizationRiskPattern]
    ) -> float:
        """Calculate overall risk score."""
        if not risks:
            return 0.0

        # Base risk from pattern count
        risk = min(1.0, len(risks) * 0.12)

        # Amplify based on permission sensitivity
        if context.permission_requested.sensitivity_level > 0.7:
            risk = min(1.0, risk * 1.4)

        # Amplify based on relationship state
        if context.relationship_trust_avg < 0.4:
            risk = min(1.0, risk * 1.3)

        # Amplify based on violation history
        if context.violations > 0:
            risk = min(1.0, risk * 1.5)

        return risk

    def _generate_reasoning(
        self,
        context: AuthorizationContext,
        risks: List[AuthorizationRiskPattern],
        similar_patterns: List[AuthorizationPattern],
        abuse_prob: float
    ) -> str:
        """Generate human-readable reasoning."""
        parts = []

        # Pattern-based reasoning
        if similar_patterns:
            abuse_count = sum(1 for p in similar_patterns if p.outcome.abused)
            parts.append(
                f"Found {len(similar_patterns)} similar cases: "
                f"{abuse_count} resulted in abuse ({abuse_prob:.0%})."
            )

        # Risk-based reasoning
        if risks:
            parts.append(f"Detected {len(risks)} risk patterns: {', '.join(r.value for r in risks[:3])}.")

        # Context-based reasoning
        if context.violations > 0:
            parts.append(f"History of {context.violations} violations.")

        if context.relationship_trust_avg < 0.5:
            parts.append(f"Low trust ({context.relationship_trust_avg:.2f}).")

        if context.permission_requested.is_high_risk():
            parts.append("High-risk permission requested (sensitive/admin/grant).")

        return " ".join(parts) if parts else "Insufficient data for detailed reasoning."

    def add_pattern(self, pattern: AuthorizationPattern):
        """Add pattern to library."""
        self.patterns.append(pattern)


class AuthorizationAdjuster:
    """Adjusts authorization based on prediction."""

    def __init__(self,
                 abuse_threshold: float = 0.6,
                 restriction_threshold: float = 0.4):
        self.abuse_threshold = abuse_threshold
        self.restriction_threshold = restriction_threshold

    def adjust_authorization(
        self,
        prediction: AuthorizationPrediction,
        context: AuthorizationContext
    ) -> AdjustedAuthorization:
        """Adjust authorization based on prediction."""

        # Check for deny
        if prediction.should_deny(self.abuse_threshold):
            return self._deny(prediction, context)

        # Check for restrictions
        if prediction.should_restrict(self.restriction_threshold):
            return self._apply_restrictions(prediction, context)

        # Grant fully
        return self._full_grant(prediction, context)

    def _deny(
        self,
        prediction: AuthorizationPrediction,
        context: AuthorizationContext
    ) -> AdjustedAuthorization:
        """Deny authorization."""
        return AdjustedAuthorization(
            strategy=RestrictionStrategy.DENY,
            granted=False,
            restricted_permission=None,
            requirements={"denied": True, "reason": prediction.reasoning},
            expected_abuse_reduction=prediction.predicted_abuse_probability,
            reasoning=(
                f"DENIED: Abuse probability {prediction.predicted_abuse_probability:.0%}. "
                f"{prediction.reasoning}"
            )
        )

    def _apply_restrictions(
        self,
        prediction: AuthorizationPrediction,
        context: AuthorizationContext
    ) -> AdjustedAuthorization:
        """Grant with restrictions."""
        perm = context.permission_requested

        # Select restriction strategy
        strategy = self._select_restriction_strategy(prediction, context)

        # Apply restrictions
        restricted_perm = self._create_restricted_permission(perm, strategy)

        requirements = self._create_requirements(strategy, context)

        return AdjustedAuthorization(
            strategy=strategy,
            granted=True,
            restricted_permission=restricted_perm,
            requirements=requirements,
            expected_abuse_reduction=prediction.predicted_abuse_probability * 0.6,
            reasoning=(
                f"GRANTED WITH RESTRICTIONS ({strategy.value}): "
                f"Abuse probability {prediction.predicted_abuse_probability:.0%}. "
                f"{prediction.reasoning}"
            )
        )

    def _select_restriction_strategy(
        self,
        prediction: AuthorizationPrediction,
        context: AuthorizationContext
    ) -> RestrictionStrategy:
        """Select appropriate restriction strategy."""

        # Check for specific risk patterns
        if AuthorizationRiskPattern.CASCADING_PERMISSIONS in prediction.risk_patterns:
            return RestrictionStrategy.DENY_GRANT

        if AuthorizationRiskPattern.PERMANENT_DURATION in prediction.risk_patterns:
            return RestrictionStrategy.TIME_LIMIT

        if AuthorizationRiskPattern.OVERLY_BROAD_SCOPE in prediction.risk_patterns:
            return RestrictionStrategy.SCOPE_REDUCTION

        if AuthorizationRiskPattern.RECENT_VIOLATION in prediction.risk_patterns:
            return RestrictionStrategy.PROBATION_PERIOD

        # Default: audit all use
        return RestrictionStrategy.AUDIT_ALL_USE

    def _create_restricted_permission(
        self,
        perm: Permission,
        strategy: RestrictionStrategy
    ) -> Permission:
        """Create restricted version of permission."""
        if strategy == RestrictionStrategy.TIME_LIMIT:
            return Permission(
                resource_type=perm.resource_type,
                resource_id=perm.resource_id,
                scope=perm.scope,
                duration=timedelta(days=7),  # 7-day limit
                sensitivity_level=perm.sensitivity_level,
                can_delegate=False,
                description=f"{perm.description} [TIME LIMITED: 7 days]"
            )

        elif strategy == RestrictionStrategy.SCOPE_REDUCTION:
            # Remove dangerous scopes
            reduced_scope = {s for s in perm.scope if s not in {
                PermissionScope.DELETE,
                PermissionScope.ADMIN,
                PermissionScope.GRANT
            }}
            return Permission(
                resource_type=perm.resource_type,
                resource_id=perm.resource_id,
                scope=reduced_scope or {PermissionScope.READ},
                duration=perm.duration,
                sensitivity_level=perm.sensitivity_level,
                can_delegate=False,
                description=f"{perm.description} [SCOPE REDUCED]"
            )

        elif strategy == RestrictionStrategy.DENY_GRANT:
            return Permission(
                resource_type=perm.resource_type,
                resource_id=perm.resource_id,
                scope=perm.scope - {PermissionScope.GRANT},
                duration=perm.duration,
                sensitivity_level=perm.sensitivity_level,
                can_delegate=False,
                description=f"{perm.description} [NO DELEGATION]"
            )

        else:
            # Keep permission as-is, restriction is in monitoring
            return perm

    def _create_requirements(
        self,
        strategy: RestrictionStrategy,
        context: AuthorizationContext
    ) -> Dict:
        """Create requirements dict for strategy."""
        if strategy == RestrictionStrategy.TIME_LIMIT:
            return {"time_limit_days": 7, "auto_revoke": True}

        elif strategy == RestrictionStrategy.AUDIT_ALL_USE:
            return {"audit_all_uses": True, "notify_on_use": True}

        elif strategy == RestrictionStrategy.PROBATION_PERIOD:
            return {
                "probation_days": 30,
                "max_uses_per_day": 10,
                "auto_revoke_on_violation": True
            }

        elif strategy == RestrictionStrategy.REQUIRE_APPROVAL:
            return {"require_approval_for_each_use": True}

        else:
            return {}

    def _full_grant(
        self,
        prediction: AuthorizationPrediction,
        context: AuthorizationContext
    ) -> AdjustedAuthorization:
        """Grant authorization fully."""
        return AdjustedAuthorization(
            strategy=RestrictionStrategy.FULL_GRANT,
            granted=True,
            restricted_permission=context.permission_requested,
            requirements={},
            expected_abuse_reduction=0.0,
            reasoning=(
                f"FULLY GRANTED: Low abuse probability ({prediction.predicted_abuse_probability:.0%}). "
                f"{prediction.reasoning}"
            )
        )


# Example usage
if __name__ == "__main__":
    print("=== Authorization EP Demonstration ===\n")

    predictor = AuthorizationEPPredictor()
    adjuster = AuthorizationAdjuster()

    # Example 1: Low-risk request from trusted identity
    print("Example 1: Low-Risk Request from Trusted Identity")
    print("-" * 70)

    low_risk_context = AuthorizationContext(
        requester_lct="lct://alice@mainnet",
        grounding_ci=0.92,
        identity_age=timedelta(days=180),
        relationship_lct="lct://alice:relationship:bob@mainnet",
        relationship_trust_avg=0.85,
        relationship_ci=0.90,
        relationship_stance_collaborative=0.85,
        current_permissions=["storage:read"],
        permission_count=2,
        revocations=0,
        violations=0,
        permission_requested=Permission(
            resource_type="storage",
            resource_id="project-data",
            scope={PermissionScope.READ, PermissionScope.WRITE},
            duration=timedelta(days=30),
            sensitivity_level=0.3,
            can_delegate=False,
            description="Access project storage"
        ),
        justification_provided=True,
        urgency_claimed="low"
    )

    pred1 = predictor.predict_authorization(low_risk_context)
    adj1 = adjuster.adjust_authorization(pred1, low_risk_context)

    print(f"Abuse Probability: {pred1.predicted_abuse_probability:.0%}")
    print(f"Legitimate Use: {pred1.predicted_legitimate_use:.0%}")
    print(f"Risk Score: {pred1.risk_score:.2f}")
    print(f"Risk Patterns: {[r.value for r in pred1.risk_patterns]}")
    print(f"\nDecision: {adj1.strategy.value}")
    print(f"Granted: {adj1.granted}")
    print(f"Reasoning: {adj1.reasoning[:120]}...")
    print()

    # Example 2: High-risk request from new, untrusted identity
    print("\nExample 2: High-Risk Request from New, Untrusted Identity")
    print("-" * 70)

    high_risk_context = AuthorizationContext(
        requester_lct="lct://mallory@mainnet",
        grounding_ci=0.45,
        identity_age=timedelta(days=3),
        relationship_lct="lct://system:relationship:mallory@mainnet",
        relationship_trust_avg=0.35,
        relationship_ci=0.40,
        relationship_stance_collaborative=0.30,
        current_permissions=[],
        permission_count=5,  # Many requests quickly
        revocations=1,
        violations=2,
        permission_requested=Permission(
            resource_type="compute",
            resource_id="production-cluster",
            scope={PermissionScope.ADMIN, PermissionScope.GRANT},
            duration=None,  # Permanent
            sensitivity_level=0.95,
            can_delegate=True,
            description="Admin access to production"
        ),
        justification_provided=False,
        urgency_claimed="critical"
    )

    pred2 = predictor.predict_authorization(high_risk_context)
    adj2 = adjuster.adjust_authorization(pred2, high_risk_context)

    print(f"Abuse Probability: {pred2.predicted_abuse_probability:.0%}")
    print(f"Legitimate Use: {pred2.predicted_legitimate_use:.0%}")
    print(f"Risk Score: {pred2.risk_score:.2f}")
    print(f"Risk Patterns ({len(pred2.risk_patterns)}):")
    for risk in pred2.risk_patterns:
        print(f"  - {risk.value}")
    print(f"\nDecision: {adj2.strategy.value}")
    print(f"Granted: {adj2.granted}")
    print(f"Expected Abuse Reduction: {adj2.expected_abuse_reduction:.0%}")
    print(f"Reasoning: {adj2.reasoning}")

    print("\n=== Demonstration Complete ===")
