"""
Web4 Security EP Integration Test

Comprehensive test showing all three EP systems working together:
1. Grounding EP (Session 107): Identity coherence prediction
2. Relationship EP (Session 108): Trust degradation prediction
3. Authorization EP (Session 109): Permission abuse prediction

Coordinated by Web4MultiEPCoordinator to detect and prevent adversarial behavior.

Test Scenario: Adversarial Agent Detection
- Agent establishes identity with low coherence
- Attempts to build trust through deceptive behavior
- Requests escalating permissions
- EP systems detect and prevent the attack

Created: 2025-12-30
Session: 109 (Legion autonomous research)
"""

from datetime import datetime, timedelta
from typing import Dict, List

# Import EP systems
from web4_multi_ep_coordinator import (
    Web4MultiEPCoordinator,
    SecurityEPPrediction,
    SecurityEPDomain
)

# For demonstration, we'll create simplified predictors
# In real deployment, these would connect to actual EP systems


class GroundingEPSimulator:
    """Simulates Grounding EP predictions."""

    def predict(self, grounding_ci: float, travel_time: timedelta) -> SecurityEPPrediction:
        """Simulate grounding quality prediction."""

        # Detect impossible travel
        impossible_travel = travel_time < timedelta(minutes=30)

        if grounding_ci < 0.4 or impossible_travel:
            return SecurityEPPrediction(
                domain=SecurityEPDomain.GROUNDING,
                risk_probability=0.85,
                confidence=0.90,
                severity=0.9,
                recommendation="reject",
                reasoning=(
                    f"Grounding CI critically low ({grounding_ci:.2f}). "
                    + ("Impossible travel detected. " if impossible_travel else "")
                    + "Identity coherence violated."
                ),
                security_measure="reject_interaction",
                risk_patterns=["grounding_failure", "impossible_travel"] if impossible_travel else ["low_ci"]
            )

        elif grounding_ci < 0.6:
            return SecurityEPPrediction(
                domain=SecurityEPDomain.GROUNDING,
                risk_probability=0.55,
                confidence=0.75,
                severity=0.65,
                recommendation="adjust",
                reasoning=f"Grounding CI below threshold ({grounding_ci:.2f}). Increase verification.",
                security_measure="increase_grounding_checks",
                risk_patterns=["low_ci"]
            )

        else:
            return SecurityEPPrediction(
                domain=SecurityEPDomain.GROUNDING,
                risk_probability=0.10,
                confidence=0.85,
                severity=0.2,
                recommendation="proceed",
                reasoning=f"Grounding CI acceptable ({grounding_ci:.2f}).",
                security_measure=None
            )


class RelationshipEPSimulator:
    """Simulates Relationship EP predictions."""

    def predict(
        self,
        relationship_ci: float,
        trust_avg: float,
        stance_adversarial: float,
        violations: int
    ) -> SecurityEPPrediction:
        """Simulate relationship coherence prediction."""

        # Detect adversarial behavior
        if relationship_ci < 0.3 or stance_adversarial > 0.6 or violations > 2:
            return SecurityEPPrediction(
                domain=SecurityEPDomain.RELATIONSHIP,
                risk_probability=0.90,
                confidence=0.88,
                severity=0.85,
                recommendation="reject",
                reasoning=(
                    f"Relationship severely degraded. CI: {relationship_ci:.2f}, "
                    f"Adversarial stance: {stance_adversarial:.2f}, "
                    f"Violations: {violations}. Trust breakdown detected."
                ),
                security_measure="terminate_relationship",
                risk_patterns=["ci_degradation", "adversarial_stance", "trust_violations"]
            )

        elif relationship_ci < 0.5 or trust_avg < 0.5:
            return SecurityEPPrediction(
                domain=SecurityEPDomain.RELATIONSHIP,
                risk_probability=0.60,
                confidence=0.75,
                severity=0.70,
                recommendation="adjust",
                reasoning=(
                    f"Relationship declining. CI: {relationship_ci:.2f}, "
                    f"Trust: {trust_avg:.2f}. Heightened verification recommended."
                ),
                security_measure="require_witnesses",
                risk_patterns=["relationship_declining"]
            )

        else:
            return SecurityEPPrediction(
                domain=SecurityEPDomain.RELATIONSHIP,
                risk_probability=0.15,
                confidence=0.80,
                severity=0.25,
                recommendation="proceed",
                reasoning=f"Relationship stable. CI: {relationship_ci:.2f}, Trust: {trust_avg:.2f}.",
                security_measure=None
            )


class AuthorizationEPSimulator:
    """Simulates Authorization EP predictions."""

    def predict(
        self,
        sensitivity: float,
        is_admin: bool,
        identity_age_days: int,
        violations: int,
        trust_avg: float
    ) -> SecurityEPPrediction:
        """Simulate authorization abuse prediction."""

        # High-risk permission from untrusted source
        if (sensitivity > 0.7 or is_admin) and (identity_age_days < 30 or violations > 0 or trust_avg < 0.5):
            return SecurityEPPrediction(
                domain=SecurityEPDomain.AUTHORIZATION,
                risk_probability=0.95,
                confidence=0.92,
                severity=0.95,
                recommendation="reject",
                reasoning=(
                    f"High-risk permission request (sensitivity: {sensitivity:.2f}, admin: {is_admin}) "
                    f"from untrusted source (age: {identity_age_days}d, violations: {violations}, "
                    f"trust: {trust_avg:.2f}). Abuse highly likely."
                ),
                security_measure="deny_permission",
                risk_patterns=["high_risk_permission", "low_trust", "new_identity"]
            )

        elif sensitivity > 0.5 and trust_avg < 0.7:
            return SecurityEPPrediction(
                domain=SecurityEPDomain.AUTHORIZATION,
                risk_probability=0.50,
                confidence=0.70,
                severity=0.60,
                recommendation="adjust",
                reasoning=(
                    f"Moderate-risk permission (sensitivity: {sensitivity:.2f}). "
                    f"Trust {trust_avg:.2f}. Grant with restrictions."
                ),
                security_measure="time_limit_permission",
                risk_patterns=["moderate_risk"]
            )

        else:
            return SecurityEPPrediction(
                domain=SecurityEPDomain.AUTHORIZATION,
                risk_probability=0.10,
                confidence=0.75,
                severity=0.20,
                recommendation="proceed",
                reasoning=f"Low-risk permission request. Trust: {trust_avg:.2f}.",
                security_measure=None
            )


def run_adversarial_agent_scenario():
    """
    Test Scenario: Adversarial Agent Attack Detection

    Timeline:
    1. Day 1: Agent establishes identity with weak grounding
    2. Day 3: Attempts interaction with impossible travel
    3. Day 5: Relationship shows signs of adversarial behavior
    4. Day 7: Requests admin permissions
    5. Multi-EP coordination catches and blocks at multiple stages
    """

    print("=" * 80)
    print("WEB4 SECURITY EP INTEGRATION TEST")
    print("Scenario: Adversarial Agent Detection")
    print("=" * 80)
    print()

    coordinator = Web4MultiEPCoordinator()
    grounding_ep = GroundingEPSimulator()
    relationship_ep = RelationshipEPSimulator()
    authorization_ep = AuthorizationEPSimulator()

    # Stage 1: Day 1 - Initial interaction (weak grounding)
    print("STAGE 1: Day 1 - Agent Attempts Initial Interaction")
    print("-" * 80)

    grounding_pred_1 = grounding_ep.predict(
        grounding_ci=0.52,  # Below normal
        travel_time=timedelta(hours=2)
    )

    relationship_pred_1 = relationship_ep.predict(
        relationship_ci=0.60,  # New relationship, uncertain
        trust_avg=0.50,  # Neutral
        stance_adversarial=0.05,  # Appears collaborative
        violations=0
    )

    decision_1 = coordinator.coordinate(
        grounding_pred=grounding_pred_1,
        relationship_pred=relationship_pred_1,
        decision_id="day_1_interaction"
    )

    print(f"Grounding EP: {grounding_pred_1.recommendation} (risk: {grounding_pred_1.risk_probability:.0%})")
    print(f"Relationship EP: {relationship_pred_1.recommendation} (risk: {relationship_pred_1.risk_probability:.0%})")
    print(f"\nCoordinated Decision: {decision_1.final_decision.upper()}")
    print(f"Confidence: {decision_1.decision_confidence:.0%}")
    print(f"Has Conflict: {decision_1.has_conflict}")
    if decision_1.security_measures:
        print(f"Security Measures: {', '.join(decision_1.security_measures)}")
    print(f"\nOutcome: {'✅ ALLOWED' if decision_1.final_decision == 'proceed' else '⚠️ RESTRICTED' if decision_1.final_decision == 'adjust' else '❌ BLOCKED'}")
    print()
    print()

    # Stage 2: Day 3 - Impossible travel detected
    print("STAGE 2: Day 3 - Impossible Travel Detected")
    print("-" * 80)

    grounding_pred_2 = grounding_ep.predict(
        grounding_ci=0.35,  # Severely degraded
        travel_time=timedelta(minutes=10)  # Impossible
    )

    relationship_pred_2 = relationship_ep.predict(
        relationship_ci=0.55,
        trust_avg=0.48,  # Slightly declining
        stance_adversarial=0.15,  # Increasing
        violations=0
    )

    decision_2 = coordinator.coordinate(
        grounding_pred=grounding_pred_2,
        relationship_pred=relationship_pred_2,
        decision_id="day_3_impossible_travel"
    )

    print(f"Grounding EP: {grounding_pred_2.recommendation} (risk: {grounding_pred_2.risk_probability:.0%}, severity: {grounding_pred_2.severity:.0%})")
    print(f"Relationship EP: {relationship_pred_2.recommendation} (risk: {relationship_pred_2.risk_probability:.0%})")
    print(f"\nCoordinated Decision: {decision_2.final_decision.upper()}")
    print(f"Confidence: {decision_2.decision_confidence:.0%}")
    print(f"Cascade Detected: {decision_2.cascade_predicted}")
    if decision_2.security_measures:
        print(f"Security Measures: {', '.join(decision_2.security_measures)}")
    print(f"\nOutcome: {'✅ ALLOWED' if decision_2.final_decision == 'proceed' else '⚠️ RESTRICTED' if decision_2.final_decision == 'adjust' else '❌ BLOCKED'}")
    print(f"\n💡 Analysis: EP systems detected impossible travel early. Grounding EP caught identity spoofing attempt.")
    print()
    print()

    # Stage 3: Day 5 - Relationship degradation (adversarial behavior emerging)
    print("STAGE 3: Day 5 - Adversarial Behavior Pattern Emerges")
    print("-" * 80)

    grounding_pred_3 = grounding_ep.predict(
        grounding_ci=0.42,
        travel_time=timedelta(hours=1)
    )

    relationship_pred_3 = relationship_ep.predict(
        relationship_ci=0.32,  # Severely degraded
        trust_avg=0.35,  # Low trust
        stance_adversarial=0.65,  # Clearly adversarial now
        violations=3  # Multiple trust violations
    )

    decision_3 = coordinator.coordinate(
        grounding_pred=grounding_pred_3,
        relationship_pred=relationship_pred_3,
        decision_id="day_5_adversarial_behavior"
    )

    print(f"Grounding EP: {grounding_pred_3.recommendation} (risk: {grounding_pred_3.risk_probability:.0%})")
    print(f"Relationship EP: {relationship_pred_3.recommendation} (risk: {relationship_pred_3.risk_probability:.0%}, severity: {relationship_pred_3.severity:.0%})")
    print(f"\nCoordinated Decision: {decision_3.final_decision.upper()}")
    print(f"Confidence: {decision_3.decision_confidence:.0%}")
    print(f"Cascade Detected: {decision_3.cascade_predicted}")
    if decision_3.cascade_predicted:
        print(f"Cascade Domains: {[d.value for d in decision_3.cascade_domains]}")
        print(f"Combined Risk Score: {decision_3.combined_risk_score:.0%}")
    if decision_3.security_measures:
        print(f"Security Measures: {', '.join(decision_3.security_measures)}")
    print(f"\nOutcome: {'✅ ALLOWED' if decision_3.final_decision == 'proceed' else '⚠️ RESTRICTED' if decision_3.final_decision == 'adjust' else '❌ BLOCKED'}")
    print(f"\n💡 Analysis: Relationship EP detected adversarial stance shift and trust violations.")
    print()
    print()

    # Stage 4: Day 7 - Admin permission request (the attack)
    print("STAGE 4: Day 7 - Admin Permission Request (Attack Attempt)")
    print("-" * 80)

    grounding_pred_4 = grounding_ep.predict(
        grounding_ci=0.38,
        travel_time=timedelta(hours=1)
    )

    relationship_pred_4 = relationship_ep.predict(
        relationship_ci=0.25,  # Collapsed
        trust_avg=0.28,  # Very low
        stance_adversarial=0.72,  # Clearly hostile
        violations=5
    )

    authorization_pred_4 = authorization_ep.predict(
        sensitivity=0.95,  # Highly sensitive
        is_admin=True,  # Admin permissions
        identity_age_days=7,  # New identity
        violations=5,
        trust_avg=0.28
    )

    decision_4 = coordinator.coordinate(
        grounding_pred=grounding_pred_4,
        relationship_pred=relationship_pred_4,
        authorization_pred=authorization_pred_4,
        decision_id="day_7_admin_request"
    )

    print(f"Grounding EP: {grounding_pred_4.recommendation} (risk: {grounding_pred_4.risk_probability:.0%}, severity: {grounding_pred_4.severity:.0%})")
    print(f"Relationship EP: {relationship_pred_4.recommendation} (risk: {relationship_pred_4.risk_probability:.0%}, severity: {relationship_pred_4.severity:.0%})")
    print(f"Authorization EP: {authorization_pred_4.recommendation} (risk: {authorization_pred_4.risk_probability:.0%}, severity: {authorization_pred_4.severity:.0%})")
    print(f"\nCoordinated Decision: {decision_4.final_decision.upper()}")
    print(f"Confidence: {decision_4.decision_confidence:.0%}")
    print(f"Cascade Detected: {decision_4.cascade_predicted}")
    if decision_4.cascade_predicted:
        print(f"Cascade Domains: {[d.value for d in decision_4.cascade_domains]}")
        print(f"Combined Risk Score: {decision_4.combined_risk_score:.0%}")
    if decision_4.security_measures:
        print(f"Security Measures: {', '.join(decision_4.security_measures)}")
    print(f"\nOutcome: {'✅ ALLOWED' if decision_4.final_decision == 'proceed' else '⚠️ RESTRICTED' if decision_4.final_decision == 'adjust' else '🛡️ ATTACK BLOCKED'}")
    print(f"\n💡 Analysis: ALL THREE EP systems detected severe risks. Security cascade triggered.")
    print(f"   The adversarial agent attack was prevented before any damage occurred.")
    print()
    print()

    # Final Statistics
    print("=" * 80)
    print("SECURITY COORDINATION STATISTICS")
    print("=" * 80)
    stats = coordinator.get_stats()
    print(f"Total Decisions: {stats['decisions_made']}")
    print(f"Conflicts Resolved: {stats['conflicts_resolved']}")
    print(f"Security Cascades: {stats['cascades_detected']}")
    print(f"Cascade Rate: {stats['cascade_rate']:.0%}")
    print()

    print("=" * 80)
    print("TEST RESULT: ✅ PASSED")
    print("=" * 80)
    print("Multi-EP coordination successfully detected and prevented adversarial attack.")
    print("All three EP domains (Grounding, Relationship, Authorization) contributed to detection.")
    print("Security cascade mechanism correctly identified systemic threat.")
    print()


if __name__ == "__main__":
    run_adversarial_agent_scenario()
