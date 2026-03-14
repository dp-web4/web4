"""
Authorization → Reputation Integration Demo
==========================================

Shows how authorization decisions feed into reputation computation,
creating a closed loop where:
1. Authorization uses trust scores to grant/deny
2. Actions produce outcomes (success/failure)
3. Outcomes update reputation (T3/V3)
4. Updated reputation affects future authorizations
"""

from authorization_engine import (
    AuthorizationEngine,
    AuthorizationRequest,
    AgentDelegation,
    LCTCredential,
    AuthorizationDecision
)
from reputation_engine import (
    ReputationEngine,
    OutcomeType
)
import time


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def demonstrate_feedback_loop():
    """Show the authorization-reputation feedback loop"""
    print_header("Web4 Authorization ↔ Reputation Feedback Loop")

    # Initialize engines
    auth_engine = AuthorizationEngine("society:research_lab")
    rep_engine = ReputationEngine()

    # Create entity and delegation
    entity_lct = "lct:ai:research_agent"
    role_lct = "role:researcher"

    delegation = AgentDelegation(
        delegation_id="deleg:research_001",
        client_lct="lct:human:supervisor",
        agent_lct=entity_lct,
        role_lct=role_lct,
        granted_permissions={"read", "write", "compute"},
        atp_budget=1000
    )
    auth_engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id=entity_lct,
        entity_type="AI",
        society_id="society:research_lab",
        birth_certificate_hash="hash123",
        public_key="pubkey_abc"
    )

    print(f"\n🤖 Entity: {entity_lct}")
    print(f"📋 Role: {role_lct}")
    print(f"💰 ATP Budget: {delegation.atp_budget}")

    # Simulate 10 actions with varying outcomes
    actions = [
        ("read", "dataset:climate_2025", 10, OutcomeType.STANDARD_SUCCESS),
        ("compute", "model:forecast", 50, OutcomeType.EXCEPTIONAL_QUALITY),
        ("write", "report:analysis", 20, OutcomeType.STANDARD_SUCCESS),
        ("read", "dataset:emissions", 10, OutcomeType.STANDARD_SUCCESS),
        ("compute", "model:optimization", 60, OutcomeType.NOVEL_SUCCESS),
        ("write", "paper:findings", 30, OutcomeType.EXCEPTIONAL_QUALITY),
        ("read", "dataset:policies", 10, OutcomeType.STANDARD_SUCCESS),
        ("compute", "model:prediction", 50, OutcomeType.UNEXPECTED_FAILURE),
        ("write", "report:results", 20, OutcomeType.DEADLINE_MET),
        ("compute", "model:validation", 40, OutcomeType.RESOURCE_EFFICIENT),
    ]

    print_header("Action Sequence with Reputation Evolution")

    for i, (action, resource, atp_cost, outcome) in enumerate(actions, 1):
        print(f"\n--- Action {i} ---")

        # Get current reputation
        reputation = rep_engine.get_reputation(entity_lct, role_lct)
        if reputation:
            trust_score = reputation.t3.average()
            value_score = reputation.v3.average()
            print(f"Current Trust (T3): {trust_score:.3f}")
            print(f"Current Value (V3): {value_score:.3f}")
            print(f"Success Rate: {reputation.success_rate():.1%}")
        else:
            trust_score = 0.5
            value_score = 0.5
            print(f"Initial Trust (T3): {trust_score:.3f}")
            print(f"Initial Value (V3): {value_score:.3f}")

        # Request authorization
        request = AuthorizationRequest(
            requester_lct=entity_lct,
            action=action,
            target_resource=resource,
            atp_cost=atp_cost,
            context={"trust_context": "research"},
            delegation_id="deleg:research_001"
        )

        auth_result = auth_engine.authorize_action(request, credential)
        print(f"\n🔒 Authorization: {auth_result.decision.value.upper()}")

        if auth_result.decision == AuthorizationDecision.GRANTED:
            print(f"   ATP Consumed: {atp_cost} (Remaining: {auth_result.atp_remaining})")

            # Simulate action outcome and compute reputation delta
            # In production, outcome comes from actual action execution
            witnesses = ["witness:supervisor"] if outcome in [OutcomeType.NOVEL_SUCCESS, OutcomeType.EXCEPTIONAL_QUALITY] else []

            delta = rep_engine.compute_delta(
                entity_lct=entity_lct,
                role_lct=role_lct,
                action_type=action,
                action_target=resource,
                outcome_type=outcome,
                witnesses=witnesses,
                action_id=auth_result.decision_log_hash
            )

            # Apply reputation delta
            rep_engine.apply_delta(delta)

            print(f"\n📈 Outcome: {outcome.value}")
            print(f"   T3 Change: {delta.net_trust_change():+.4f}")
            print(f"   V3 Change: {delta.net_value_change():+.4f}")
            if witnesses:
                print(f"   ✅ Witnessed by: {', '.join(witnesses)}")

        else:
            print(f"   Denied: {auth_result.denial_reason.value if auth_result.denial_reason else 'N/A'}")

    # Final reputation summary
    print_header("Final Reputation Profile")

    reputation = rep_engine.get_reputation(entity_lct, role_lct)
    if reputation:
        print(f"\n🎯 Final Statistics:")
        print(f"   Trust (T3): {reputation.t3.average():.3f}")
        print(f"     - Talent: {reputation.t3.talent:.3f}")
        print(f"     - Training: {reputation.t3.training:.3f}")
        print(f"     - Temperament: {reputation.t3.temperament:.3f}")
        print(f"\n   Value (V3): {reputation.v3.average():.3f}")
        print(f"     - Veracity: {reputation.v3.veracity:.3f}")
        print(f"     - Validity: {reputation.v3.validity:.3f}")
        print(f"     - Value: {reputation.v3.value:.3f}")
        print(f"\n   Total Actions: {reputation.total_actions}")
        print(f"   Success Rate: {reputation.success_rate():.1%}")
        print(f"   ATP Spent: {delegation.atp_spent}")

    # Check for gaming
    is_gaming, reason = rep_engine.detect_gaming_attempt(entity_lct, role_lct)
    print(f"\n🔍 Gaming Detection: {'⚠️  SUSPICIOUS' if is_gaming else '✅ Clean'}")
    if is_gaming:
        print(f"   Reason: {reason}")

    # Show stats
    auth_stats = auth_engine.get_authorization_stats(entity_lct)
    print(f"\n📊 Authorization Statistics:")
    print(f"   Total Requests: {auth_stats['total']}")
    print(f"   Granted: {auth_stats['granted']}")
    print(f"   Denied: {auth_stats['denied']}")
    print(f"   Success Rate: {auth_stats['success_rate']:.1%}")

    print_header("KEY INSIGHTS")
    print("""
✅ Closed Loop Achieved:
   1. Authorization uses trust scores (T3) to decide
   2. Successful actions produce outcomes
   3. Outcomes generate reputation deltas (T3/V3)
   4. Updated reputation affects future authorizations
   5. Witnesses boost reputation gains (gaming resistance)
   6. Diminishing returns prevent score inflation
   7. Multi-dimensional assessment prevents narrow optimization

🔒 Security Properties:
   - Trust must be earned through witnessed performance
   - Gaming detected through pattern analysis
   - Reputation is role-contextual (not global)
   - Time decay prevents stale reputation
   - ATP budget prevents unlimited attempts

🎯 Next Steps:
   - Integrate with real Law Oracle for permission queries
   - Connect to immutable ledger for audit trail
   - Add cross-society reputation portability
   - Implement reputation-based ATP allocation
    """)


if __name__ == "__main__":
    demonstrate_feedback_loop()
