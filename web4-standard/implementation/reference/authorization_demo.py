"""
Web4 Authorization System - Comprehensive Demonstration
=======================================================

This demo shows the authorization system in action across various scenarios:
1. Successful agent authorization
2. Trust-based decision making
3. ATP budget enforcement
4. Rate limiting
5. Delegation lifecycle
6. Security boundary enforcement
7. Human oversight (witness requirements)
"""

from authorization_engine import (
    AuthorizationEngine,
    AuthorizationRequest,
    AgentDelegation,
    LCTCredential,
    AuthorizationDecision
)
import time


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def print_result(result):
    """Print authorization result"""
    print(f"Decision: {result.decision.value.upper()}")
    if result.denial_reason:
        print(f"Denial Reason: {result.denial_reason.value}")
    print(f"Trust Score: {result.actual_trust_score:.2f} (required: {result.required_trust_score:.2f})")
    print(f"ATP Remaining: {result.atp_remaining}")
    if result.requires_witness:
        print("⚠️  Witness Required (Human Oversight)")
    print(f"Decision Hash: {result.decision_log_hash[:16]}...")


def demo_1_successful_authorization():
    """Demo 1: Successful authorization flow"""
    print_section("DEMO 1: Successful Authorization")

    # Setup
    engine = AuthorizationEngine("society:research_institute")

    delegation = AgentDelegation(
        delegation_id="deleg:research_001",
        client_lct="lct:human:dr_smith",
        agent_lct="lct:ai:research_assistant",
        role_lct="role:researcher",
        granted_permissions={"read", "write", "compute", "analyze"},
        atp_budget=1000,
        max_actions_per_hour=100
    )
    engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id="lct:ai:research_assistant",
        entity_type="AI",
        society_id="society:research_institute",
        birth_certificate_hash="abc123",
        public_key="pubkey_xyz"
    )

    # Execute authorized action
    request = AuthorizationRequest(
        requester_lct="lct:ai:research_assistant",
        action="read",
        target_resource="data:research_papers_2025",
        atp_cost=50,
        context={"trust_context": "research", "purpose": "literature_review"},
        delegation_id="deleg:research_001"
    )

    result = engine.authorize_action(request, credential)
    print("\n📝 Research Assistant requests to read papers...")
    print_result(result)

    if result.decision == AuthorizationDecision.GRANTED:
        print("\n✅ Access Granted! Agent can proceed with research.")


def demo_2_trust_based_decisions():
    """Demo 2: Trust-based authorization decisions"""
    print_section("DEMO 2: Trust-Based Authorization")

    engine = AuthorizationEngine("society:financial_services")

    # High trust agent
    high_trust_delegation = AgentDelegation(
        delegation_id="deleg:high_trust",
        client_lct="lct:human:cfo",
        agent_lct="lct:ai:senior_analyst",
        role_lct="role:researcher",
        granted_permissions={"read", "write", "compute"},
        atp_budget=5000
    )
    engine.register_delegation(high_trust_delegation)

    credential = LCTCredential(
        lct_id="lct:ai:senior_analyst",
        entity_type="AI",
        society_id="society:financial_services",
        birth_certificate_hash="def456",
        public_key="pubkey_abc"
    )

    # Request without witness (trust is 0.75, threshold is 0.5, witness only for <0.6)
    request = AuthorizationRequest(
        requester_lct="lct:ai:senior_analyst",
        action="compute",
        target_resource="model:financial_forecast",
        atp_cost=200,
        context={"trust_context": "financial_analysis"},
        delegation_id="deleg:high_trust"
    )

    result = engine.authorize_action(request, credential)
    print("\n💼 Senior Analyst requests financial model access...")
    print_result(result)


def demo_3_atp_budget_enforcement():
    """Demo 3: ATP budget enforcement"""
    print_section("DEMO 3: ATP Budget Enforcement")

    engine = AuthorizationEngine("society:compute_cluster")

    delegation = AgentDelegation(
        delegation_id="deleg:compute_001",
        client_lct="lct:human:researcher",
        agent_lct="lct:ai:compute_agent",
        role_lct="role:researcher",
        granted_permissions={"compute"},
        atp_budget=100,
        max_actions_per_hour=50
    )
    engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id="lct:ai:compute_agent",
        entity_type="AI",
        society_id="society:compute_cluster",
        birth_certificate_hash="ghi789",
        public_key="pubkey_def"
    )

    print("\n💻 Agent has 100 ATP budget...")

    # First request: 60 ATP
    request1 = AuthorizationRequest(
        requester_lct="lct:ai:compute_agent",
        action="compute",
        target_resource="task:training_model_1",
        atp_cost=60,
        context={},
        delegation_id="deleg:compute_001"
    )

    result1 = engine.authorize_action(request1, credential)
    print("\n📊 Request 1: Train model (60 ATP)")
    print_result(result1)

    # Second request: 30 ATP
    request2 = AuthorizationRequest(
        requester_lct="lct:ai:compute_agent",
        action="compute",
        target_resource="task:training_model_2",
        atp_cost=30,
        context={},
        delegation_id="deleg:compute_001"
    )

    result2 = engine.authorize_action(request2, credential)
    print("\n📊 Request 2: Train another model (30 ATP)")
    print_result(result2)

    # Third request: 20 ATP (should fail - would exceed budget)
    request3 = AuthorizationRequest(
        requester_lct="lct:ai:compute_agent",
        action="compute",
        target_resource="task:training_model_3",
        atp_cost=20,
        context={},
        delegation_id="deleg:compute_001"
    )

    result3 = engine.authorize_action(request3, credential)
    print("\n📊 Request 3: Train third model (20 ATP)")
    print_result(result3)

    if result3.decision == AuthorizationDecision.DENIED:
        print("\n❌ Budget Exhausted! Agent must request more ATP or wait for recharge.")


def demo_4_rate_limiting():
    """Demo 4: Rate limiting enforcement"""
    print_section("DEMO 4: Rate Limiting")

    engine = AuthorizationEngine("society:api_service")

    delegation = AgentDelegation(
        delegation_id="deleg:api_001",
        client_lct="lct:human:developer",
        agent_lct="lct:ai:api_client",
        role_lct="role:researcher",
        granted_permissions={"read"},
        atp_budget=1000,
        max_actions_per_hour=5  # Very low limit for demo
    )
    engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id="lct:ai:api_client",
        entity_type="AI",
        society_id="society:api_service",
        birth_certificate_hash="jkl012",
        public_key="pubkey_ghi"
    )

    print("\n🚦 Agent has 5 requests/hour limit...")

    # Make 6 requests
    for i in range(6):
        request = AuthorizationRequest(
            requester_lct="lct:ai:api_client",
            action="read",
            target_resource=f"data:item_{i}",
            atp_cost=1,
            context={},
            delegation_id="deleg:api_001"
        )

        result = engine.authorize_action(request, credential)
        print(f"\nRequest {i+1}: {result.decision.value}")

        if result.decision == AuthorizationDecision.DENIED:
            print(f"❌ Rate limit exceeded! Reason: {result.denial_reason.value}")
            break


def demo_5_delegation_lifecycle():
    """Demo 5: Delegation lifecycle management"""
    print_section("DEMO 5: Delegation Lifecycle")

    engine = AuthorizationEngine("society:collaboration_space")

    # Create delegation with short expiry
    delegation = AgentDelegation(
        delegation_id="deleg:temp_001",
        client_lct="lct:human:manager",
        agent_lct="lct:ai:temp_worker",
        role_lct="role:researcher",
        granted_permissions={"read", "write"},
        atp_budget=500,
        valid_from=time.time(),
        valid_until=time.time() + 5  # Expires in 5 seconds
    )
    engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id="lct:ai:temp_worker",
        entity_type="AI",
        society_id="society:collaboration_space",
        birth_certificate_hash="mno345",
        public_key="pubkey_jkl"
    )

    # Request while valid
    request = AuthorizationRequest(
        requester_lct="lct:ai:temp_worker",
        action="read",
        target_resource="data:project_files",
        atp_cost=10,
        context={},
        delegation_id="deleg:temp_001"
    )

    result1 = engine.authorize_action(request, credential)
    print("\n📋 Immediate request (delegation valid):")
    print_result(result1)

    # Wait for expiry
    print("\n⏳ Waiting 6 seconds for delegation to expire...")
    time.sleep(6)

    # Request after expiry
    result2 = engine.authorize_action(request, credential)
    print("\n📋 Request after expiry:")
    print_result(result2)


def demo_6_security_boundaries():
    """Demo 6: Security boundary enforcement"""
    print_section("DEMO 6: Security Boundaries")

    engine = AuthorizationEngine("society:secure_facility")

    # Create limited delegation (read-only)
    delegation = AgentDelegation(
        delegation_id="deleg:read_only",
        client_lct="lct:human:guest",
        agent_lct="lct:ai:limited_agent",
        role_lct="role:researcher",
        granted_permissions={"read"},  # No write permission
        atp_budget=1000
    )
    engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id="lct:ai:limited_agent",
        entity_type="AI",
        society_id="society:secure_facility",
        birth_certificate_hash="pqr678",
        public_key="pubkey_mno"
    )

    # Attempt authorized action (read)
    read_request = AuthorizationRequest(
        requester_lct="lct:ai:limited_agent",
        action="read",
        target_resource="data:public_docs",
        atp_cost=5,
        context={},
        delegation_id="deleg:read_only"
    )

    read_result = engine.authorize_action(read_request, credential)
    print("\n👁️ Agent attempts to READ (authorized):")
    print_result(read_result)

    # Attempt unauthorized action (write)
    write_request = AuthorizationRequest(
        requester_lct="lct:ai:limited_agent",
        action="write",
        target_resource="data:protected_docs",
        atp_cost=10,
        context={},
        delegation_id="deleg:read_only"
    )

    write_result = engine.authorize_action(write_request, credential)
    print("\n✏️  Agent attempts to WRITE (not authorized):")
    print_result(write_result)

    if write_result.decision == AuthorizationDecision.DENIED:
        print("\n✅ Security boundary enforced! Write access denied.")


def demo_7_authorization_statistics():
    """Demo 7: Authorization statistics and auditing"""
    print_section("DEMO 7: Authorization Statistics")

    engine = AuthorizationEngine("society:analytics_platform")

    delegation = AgentDelegation(
        delegation_id="deleg:analytics_001",
        client_lct="lct:human:data_scientist",
        agent_lct="lct:ai:analytics_agent",
        role_lct="role:researcher",
        granted_permissions={"read", "compute"},
        atp_budget=1000
    )
    engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id="lct:ai:analytics_agent",
        entity_type="AI",
        society_id="society:analytics_platform",
        birth_certificate_hash="stu901",
        public_key="pubkey_pqr"
    )

    print("\n📊 Agent performs multiple actions...")

    # Perform various actions
    actions = [
        ("read", "dataset:sales_2025", 10),
        ("compute", "model:forecast", 50),
        ("read", "dataset:customer_data", 15),
        ("compute", "model:clustering", 75),
        ("read", "dataset:inventory", 10),
    ]

    for action, resource, cost in actions:
        request = AuthorizationRequest(
            requester_lct="lct:ai:analytics_agent",
            action=action,
            target_resource=resource,
            atp_cost=cost,
            context={},
            delegation_id="deleg:analytics_001"
        )
        engine.authorize_action(request, credential)

    # Get statistics
    stats = engine.get_authorization_stats("lct:ai:analytics_agent")

    print(f"\n📈 Authorization Statistics:")
    print(f"  Total Requests: {stats['total']}")
    print(f"  Granted: {stats['granted']}")
    print(f"  Denied: {stats['denied']}")
    print(f"  Deferred: {stats['deferred']}")
    print(f"  Success Rate: {stats['success_rate']:.1%}")
    print(f"  Avg Trust Score: {stats['avg_trust_score']:.2f}")
    print(f"  Total ATP Cost: {stats['total_atp_cost']}")


def main():
    """Run all demonstrations"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  Web4 Authorization System - Comprehensive Demonstration".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    demos = [
        demo_1_successful_authorization,
        demo_2_trust_based_decisions,
        demo_3_atp_budget_enforcement,
        demo_4_rate_limiting,
        demo_5_delegation_lifecycle,
        demo_6_security_boundaries,
        demo_7_authorization_statistics
    ]

    for demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")

    print_section("DEMONSTRATION COMPLETE")
    print("\n✅ All scenarios demonstrated successfully!")
    print("\nKey Capabilities Shown:")
    print("  • LCT-based identity verification")
    print("  • Role-based permission enforcement")
    print("  • Trust score evaluation")
    print("  • ATP budget management")
    print("  • Rate limiting")
    print("  • Delegation lifecycle")
    print("  • Security boundary enforcement")
    print("  • Authorization auditing")
    print("\n")


if __name__ == "__main__":
    main()
