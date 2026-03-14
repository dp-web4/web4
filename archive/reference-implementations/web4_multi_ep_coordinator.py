"""
Web4 Multi-EP Security Coordinator

Coordinates multiple Epistemic Proprioception systems for Web4 security:
- Grounding EP: Validates identity coherence
- Relationship EP: Predicts relationship degradation
- Authorization EP: Prevents permission abuse

Based on Thor's Multi-EP Coordinator pattern (sage/experiments/multi_ep_coordinator.py)
Applied to Web4 security domain.

The Security EP Trilogy:
1. **Grounding EP**: "Will grounding fail?" → Identity security
2. **Relationship EP**: "Will relationship degrade?" → Trust security
3. **Authorization EP**: "Will permission be abused?" → Access security

Together they enable proactive, coordinated security decisions.

Created: 2025-12-30
Session: 109 (Legion autonomous research)
Foundation: Thor's Multi-EP Coordinator + Sessions 107-108
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class SecurityEPDomain(Enum):
    """Web4 security EP domains."""
    GROUNDING = "grounding"        # Identity coherence
    RELATIONSHIP = "relationship"  # Trust dynamics
    AUTHORIZATION = "authorization"  # Permission safety


class ConflictResolution(Enum):
    """Strategies for resolving multi-EP conflicts."""
    PRIORITY = "priority"    # Use priority ordering
    CONSENSUS = "consensus"  # Require agreement
    SEVERITY = "severity"    # Worst-case takes precedence
    COMBINED = "combined"    # Combine compatible security measures


@dataclass
class SecurityEPPrediction:
    """Prediction from a single security EP domain."""
    domain: SecurityEPDomain

    # Prediction
    risk_probability: float  # 0.0-1.0 (probability of security issue)
    confidence: float  # 0.0-1.0
    severity: float  # 0.0-1.0 (how severe if issue occurs?)

    # Recommendation
    recommendation: str  # "proceed", "adjust", "defer", "reject"
    reasoning: str
    security_measure: Optional[str] = None  # Recommended security adjustment

    # Context
    risk_patterns: List[str] = field(default_factory=list)
    similar_pattern_count: int = 0


@dataclass
class Web4SecurityDecision:
    """
    Coordinated security decision from multiple EP systems.

    Integrates predictions across security domains for coherent decision.
    """

    # Coordinated decision (required fields first)
    final_decision: str  # "proceed", "adjust", "defer", "reject"
    decision_confidence: float  # 0.0-1.0
    reasoning: str

    # Individual predictions (optional fields)
    grounding_prediction: Optional[SecurityEPPrediction] = None
    relationship_prediction: Optional[SecurityEPPrediction] = None
    authorization_prediction: Optional[SecurityEPPrediction] = None

    # Security measures
    security_measures: List[str] = field(default_factory=list)
    verification_requirements: Dict = field(default_factory=dict)

    # Conflict information
    has_conflict: bool = False
    conflict_type: Optional[str] = None
    resolution_strategy: Optional[ConflictResolution] = None

    # Multi-domain risk detection
    cascade_predicted: bool = False  # Multiple severe risks detected
    cascade_domains: List[SecurityEPDomain] = field(default_factory=list)
    combined_risk_score: float = 0.0  # 0.0-1.0

    # Audit trail
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    decision_id: Optional[str] = None


class Web4MultiEPCoordinator:
    """
    Coordinates multiple EP systems for coherent Web4 security decisions.

    Based on Thor's Multi-EP Coordinator pattern, applied to Web4 security.

    Handles:
    - Conflicting predictions (different security domains disagree)
    - Cascading security risks (one domain's issue affects others)
    - Priority resolution (which domain takes precedence)
    - Combined security measures (integrate compatible protections)
    """

    def __init__(
        self,
        priority_order: Optional[List[SecurityEPDomain]] = None,
        cascade_threshold: float = 0.7,
        reject_threshold: float = 0.85
    ):
        """
        Initialize Web4 Multi-EP Security Coordinator.

        Args:
            priority_order: Domain priority (default: Grounding > Relationship > Authorization)
            cascade_threshold: Severity threshold for cascade detection
            reject_threshold: Risk threshold for outright rejection
        """
        if priority_order is None:
            # Default: Verify identity first, then trust, then permissions
            priority_order = [
                SecurityEPDomain.GROUNDING,      # Identity must be verified
                SecurityEPDomain.RELATIONSHIP,   # Then check trust
                SecurityEPDomain.AUTHORIZATION   # Then evaluate permissions
            ]

        self.priority_order = priority_order
        self.cascade_threshold = cascade_threshold
        self.reject_threshold = reject_threshold

        # Statistics
        self.decisions_made = 0
        self.conflicts_resolved = 0
        self.cascades_detected = 0
        self.interactions_rejected = 0
        self.security_measures_applied = 0

    def coordinate(
        self,
        grounding_pred: Optional[SecurityEPPrediction] = None,
        relationship_pred: Optional[SecurityEPPrediction] = None,
        authorization_pred: Optional[SecurityEPPrediction] = None,
        decision_id: Optional[str] = None
    ) -> Web4SecurityDecision:
        """
        Coordinate predictions from multiple security EP domains.

        Args:
            grounding_pred: Prediction from Grounding EP
            relationship_pred: Prediction from Relationship EP
            authorization_pred: Prediction from Authorization EP
            decision_id: Optional identifier for audit trail

        Returns:
            Web4SecurityDecision with coordinated security outcome
        """
        self.decisions_made += 1

        # Collect available predictions
        predictions = self._collect_predictions(
            grounding_pred,
            relationship_pred,
            authorization_pred
        )

        if not predictions:
            # No EP predictions available - default to cautious
            return Web4SecurityDecision(
                final_decision="defer",
                decision_confidence=0.3,
                reasoning="No EP predictions available - defer for manual review",
                decision_id=decision_id
            )

        # Check for cascade (multiple severe risks)
        cascade_detected, cascade_domains, combined_risk = self._detect_cascade(predictions)

        if cascade_detected:
            self.cascades_detected += 1
            return self._handle_cascade(
                predictions,
                cascade_domains,
                combined_risk,
                decision_id
            )

        # Check for critical single-domain rejection
        rejection = self._check_rejection(predictions)
        if rejection:
            self.interactions_rejected += 1
            return rejection

        # Check for conflicts
        has_conflict, conflict_type = self._detect_conflict(predictions)

        if has_conflict:
            self.conflicts_resolved += 1
            return self._resolve_conflict(
                predictions,
                grounding_pred,
                relationship_pred,
                authorization_pred,
                conflict_type,
                decision_id
            )

        # No conflict - proceed with consensus or combination
        return self._consensus_decision(
            predictions,
            grounding_pred,
            relationship_pred,
            authorization_pred,
            decision_id
        )

    def _collect_predictions(
        self,
        grounding_pred: Optional[SecurityEPPrediction],
        relationship_pred: Optional[SecurityEPPrediction],
        authorization_pred: Optional[SecurityEPPrediction]
    ) -> List[SecurityEPPrediction]:
        """Collect available predictions."""
        predictions = []
        if grounding_pred:
            predictions.append(grounding_pred)
        if relationship_pred:
            predictions.append(relationship_pred)
        if authorization_pred:
            predictions.append(authorization_pred)
        return predictions

    def _detect_cascade(
        self,
        predictions: List[SecurityEPPrediction]
    ) -> Tuple[bool, List[SecurityEPDomain], float]:
        """
        Detect security cascade - multiple domains predicting severe risks.

        Returns: (cascade_detected, affected_domains, combined_risk_score)
        """
        severe_predictions = [
            p for p in predictions
            if p.severity >= self.cascade_threshold
        ]

        if len(severe_predictions) >= 2:
            # Multiple severe risks = cascade
            domains = [p.domain for p in severe_predictions]

            # Combined risk score (amplified by multiple domains)
            individual_risks = [p.risk_probability * p.severity for p in severe_predictions]
            combined_risk = min(1.0, sum(individual_risks) * 1.2)  # Amplify

            return True, domains, combined_risk

        return False, [], 0.0

    def _handle_cascade(
        self,
        predictions: List[SecurityEPPrediction],
        cascade_domains: List[SecurityEPDomain],
        combined_risk: float,
        decision_id: Optional[str]
    ) -> Web4SecurityDecision:
        """Handle detected security cascade."""

        # Cascade reasoning
        domain_names = [d.value for d in cascade_domains]
        reasoning = (
            f"SECURITY CASCADE DETECTED across {len(cascade_domains)} domains: "
            f"{', '.join(domain_names)}. "
            f"Combined risk score: {combined_risk:.2f}. "
            "Multiple severe security risks indicate systemic threat. REJECTING interaction."
        )

        # Collect all risk patterns
        all_risk_patterns = []
        for pred in predictions:
            all_risk_patterns.extend(pred.risk_patterns)

        return Web4SecurityDecision(
            grounding_prediction=next((p for p in predictions if p.domain == SecurityEPDomain.GROUNDING), None),
            relationship_prediction=next((p for p in predictions if p.domain == SecurityEPDomain.RELATIONSHIP), None),
            authorization_prediction=next((p for p in predictions if p.domain == SecurityEPDomain.AUTHORIZATION), None),
            final_decision="reject",
            decision_confidence=0.95,  # High confidence in cascade detection
            reasoning=reasoning,
            security_measures=["cascade_rejection", "audit_log", "potential_threat_flag"],
            has_conflict=False,
            cascade_predicted=True,
            cascade_domains=cascade_domains,
            combined_risk_score=combined_risk,
            decision_id=decision_id
        )

    def _check_rejection(
        self,
        predictions: List[SecurityEPPrediction]
    ) -> Optional[Web4SecurityDecision]:
        """Check if any single domain requires outright rejection."""

        for pred in predictions:
            # Critical risk threshold
            if pred.risk_probability * pred.severity >= self.reject_threshold:
                return Web4SecurityDecision(
                    grounding_prediction=pred if pred.domain == SecurityEPDomain.GROUNDING else None,
                    relationship_prediction=pred if pred.domain == SecurityEPDomain.RELATIONSHIP else None,
                    authorization_prediction=pred if pred.domain == SecurityEPDomain.AUTHORIZATION else None,
                    final_decision="reject",
                    decision_confidence=pred.confidence,
                    reasoning=(
                        f"CRITICAL RISK in {pred.domain.value} domain. "
                        f"Risk: {pred.risk_probability:.2f}, Severity: {pred.severity:.2f}. "
                        f"{pred.reasoning}"
                    ),
                    security_measures=["critical_rejection", "audit_log"],
                    combined_risk_score=pred.risk_probability * pred.severity
                )

        return None

    def _detect_conflict(
        self,
        predictions: List[SecurityEPPrediction]
    ) -> Tuple[bool, Optional[str]]:
        """Detect if predictions conflict."""

        recommendations = [p.recommendation for p in predictions]
        unique_recommendations = set(recommendations)

        if len(unique_recommendations) > 1:
            # Conflict exists
            if "reject" in recommendations and "proceed" in recommendations:
                return True, "proceed_reject_conflict"
            elif "defer" in recommendations and "proceed" in recommendations:
                return True, "proceed_defer_conflict"
            else:
                return True, "recommendation_mismatch"

        return False, None

    def _resolve_conflict(
        self,
        predictions: List[SecurityEPPrediction],
        grounding_pred: Optional[SecurityEPPrediction],
        relationship_pred: Optional[SecurityEPPrediction],
        authorization_pred: Optional[SecurityEPPrediction],
        conflict_type: str,
        decision_id: Optional[str]
    ) -> Web4SecurityDecision:
        """Resolve conflicts using priority ordering."""

        # Use priority ordering to resolve
        for domain in self.priority_order:
            pred = None
            if domain == SecurityEPDomain.GROUNDING and grounding_pred:
                pred = grounding_pred
            elif domain == SecurityEPDomain.RELATIONSHIP and relationship_pred:
                pred = relationship_pred
            elif domain == SecurityEPDomain.AUTHORIZATION and authorization_pred:
                pred = authorization_pred

            if pred:
                # Highest priority domain decides
                reasoning = (
                    f"CONFLICT RESOLVED via priority: {domain.value} domain takes precedence. "
                    f"Conflict type: {conflict_type}. "
                    f"{pred.reasoning}"
                )

                # Collect all security measures
                all_measures = [
                    p.security_measure for p in predictions
                    if p.security_measure
                ]

                return Web4SecurityDecision(
                    grounding_prediction=grounding_pred,
                    relationship_prediction=relationship_pred,
                    authorization_prediction=authorization_pred,
                    final_decision=pred.recommendation,
                    decision_confidence=pred.confidence * 0.9,  # Slightly reduced for conflict
                    reasoning=reasoning,
                    security_measures=all_measures,
                    has_conflict=True,
                    conflict_type=conflict_type,
                    resolution_strategy=ConflictResolution.PRIORITY,
                    combined_risk_score=max(p.risk_probability * p.severity for p in predictions),
                    decision_id=decision_id
                )

        # Should not reach here
        return Web4SecurityDecision(
            final_decision="defer",
            decision_confidence=0.5,
            reasoning="Conflict resolution failed - defer for manual review",
            has_conflict=True,
            conflict_type=conflict_type,
            decision_id=decision_id
        )

    def _consensus_decision(
        self,
        predictions: List[SecurityEPPrediction],
        grounding_pred: Optional[SecurityEPPrediction],
        relationship_pred: Optional[SecurityEPPrediction],
        authorization_pred: Optional[SecurityEPPrediction],
        decision_id: Optional[str]
    ) -> Web4SecurityDecision:
        """Create consensus decision when no conflicts."""

        # All predictions agree - combine their insights
        decision = predictions[0].recommendation

        # Average confidence (weighted by confidence)
        total_confidence = sum(p.confidence for p in predictions)
        avg_confidence = total_confidence / len(predictions)

        # Combine reasoning
        reasonings = [f"{p.domain.value}: {p.reasoning}" for p in predictions]
        combined_reasoning = "CONSENSUS decision. " + " | ".join(reasonings)

        # Collect all security measures
        all_measures = [
            p.security_measure for p in predictions
            if p.security_measure
        ]

        # Combined risk score
        combined_risk = max(p.risk_probability * p.severity for p in predictions)

        if all_measures:
            self.security_measures_applied += len(all_measures)

        return Web4SecurityDecision(
            grounding_prediction=grounding_pred,
            relationship_prediction=relationship_pred,
            authorization_prediction=authorization_pred,
            final_decision=decision,
            decision_confidence=avg_confidence,
            reasoning=combined_reasoning,
            security_measures=all_measures,
            has_conflict=False,
            combined_risk_score=combined_risk,
            decision_id=decision_id
        )

    def get_stats(self) -> Dict:
        """Get coordinator statistics."""
        return {
            "decisions_made": self.decisions_made,
            "conflicts_resolved": self.conflicts_resolved,
            "cascades_detected": self.cascades_detected,
            "interactions_rejected": self.interactions_rejected,
            "security_measures_applied": self.security_measures_applied,
            "conflict_rate": (
                self.conflicts_resolved / self.decisions_made
                if self.decisions_made > 0 else 0.0
            ),
            "cascade_rate": (
                self.cascades_detected / self.decisions_made
                if self.decisions_made > 0 else 0.0
            ),
            "rejection_rate": (
                self.interactions_rejected / self.decisions_made
                if self.decisions_made > 0 else 0.0
            )
        }


# Example usage and demonstration
if __name__ == "__main__":
    print("=== Web4 Multi-EP Security Coordinator Demonstration ===\n")

    coordinator = Web4MultiEPCoordinator()

    # Scenario 1: All systems agree - proceed
    print("Scenario 1: Consensus - All Security Checks Pass")
    print("-" * 70)

    grounding_ok = SecurityEPPrediction(
        domain=SecurityEPDomain.GROUNDING,
        risk_probability=0.1,
        confidence=0.85,
        severity=0.2,
        recommendation="proceed",
        reasoning="High grounding CI (0.92), stable identity",
        security_measure=None
    )

    relationship_ok = SecurityEPPrediction(
        domain=SecurityEPDomain.RELATIONSHIP,
        risk_probability=0.15,
        confidence=0.80,
        severity=0.3,
        recommendation="proceed",
        reasoning="Stable collaborative relationship, trust 0.85",
        security_measure=None
    )

    decision1 = coordinator.coordinate(
        grounding_pred=grounding_ok,
        relationship_pred=relationship_ok,
        decision_id="scenario_1"
    )

    print(f"Final Decision: {decision1.final_decision}")
    print(f"Confidence: {decision1.decision_confidence:.2f}")
    print(f"Has Conflict: {decision1.has_conflict}")
    print(f"Combined Risk: {decision1.combined_risk_score:.2f}")
    print(f"Reasoning: {decision1.reasoning[:150]}...")
    print()

    # Scenario 2: Conflict - grounding warns, relationship ok
    print("\nScenario 2: Conflict - Grounding Concern, Relationship OK")
    print("-" * 70)

    grounding_warn = SecurityEPPrediction(
        domain=SecurityEPDomain.GROUNDING,
        risk_probability=0.55,
        confidence=0.70,
        severity=0.65,
        recommendation="adjust",
        reasoning="Low grounding CI (0.48), identity coherence questionable",
        security_measure="increase_grounding_checks"
    )

    relationship_ok2 = SecurityEPPrediction(
        domain=SecurityEPDomain.RELATIONSHIP,
        risk_probability=0.2,
        confidence=0.75,
        severity=0.3,
        recommendation="proceed",
        reasoning="Stable relationship, minor reciprocity imbalance",
        security_measure=None
    )

    decision2 = coordinator.coordinate(
        grounding_pred=grounding_warn,
        relationship_pred=relationship_ok2,
        decision_id="scenario_2"
    )

    print(f"Final Decision: {decision2.final_decision}")
    print(f"Confidence: {decision2.decision_confidence:.2f}")
    print(f"Has Conflict: {decision2.has_conflict}")
    print(f"Conflict Type: {decision2.conflict_type}")
    print(f"Resolution: {decision2.resolution_strategy.value if decision2.resolution_strategy else 'N/A'}")
    print(f"Security Measures: {decision2.security_measures}")
    print(f"Reasoning: {decision2.reasoning[:150]}...")
    print()

    # Scenario 3: Security Cascade - multiple severe risks
    print("\nScenario 3: Security Cascade - Multiple Severe Risks")
    print("-" * 70)

    grounding_fail = SecurityEPPrediction(
        domain=SecurityEPDomain.GROUNDING,
        risk_probability=0.85,
        confidence=0.90,
        severity=0.9,
        recommendation="reject",
        reasoning="Grounding failure, impossible travel detected",
        risk_patterns=["impossible_travel", "grounding_failure"],
        security_measure="reject_interaction"
    )

    relationship_adversarial = SecurityEPPrediction(
        domain=SecurityEPDomain.RELATIONSHIP,
        risk_probability=0.80,
        confidence=0.85,
        severity=0.85,
        recommendation="reject",
        reasoning="Relationship CI collapsed (0.25), adversarial stance 0.65",
        risk_patterns=["stance_inversion", "ci_degradation", "trust_violation"],
        security_measure="terminate_relationship"
    )

    decision3 = coordinator.coordinate(
        grounding_pred=grounding_fail,
        relationship_pred=relationship_adversarial,
        decision_id="scenario_3"
    )

    print(f"Final Decision: {decision3.final_decision}")
    print(f"Confidence: {decision3.decision_confidence:.2f}")
    print(f"Cascade Detected: {decision3.cascade_predicted}")
    print(f"Cascade Domains: {[d.value for d in decision3.cascade_domains]}")
    print(f"Combined Risk Score: {decision3.combined_risk_score:.2f}")
    print(f"Security Measures: {decision3.security_measures}")
    print(f"Reasoning: {decision3.reasoning}")
    print()

    # Statistics
    print("\n" + "=" * 70)
    print("Coordinator Statistics:")
    print("=" * 70)
    stats = coordinator.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")

    print("\n=== Demonstration Complete ===")
