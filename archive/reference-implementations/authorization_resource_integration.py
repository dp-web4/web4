"""
Authorization + Resource Integration
====================================

Complete flow showing how authorization, reputation, and resource allocation
work together to create a fair, trust-based AI coordination system.

Flow:
1. Entity requests action (with ATP budget)
2. Authorization engine checks credentials, trust, permissions
3. Resource allocator converts ATP to concrete resources
4. Action executes with resource metering
5. Outcome updates reputation
6. Resources consumed/returned based on actual usage
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
from resource_allocator import (
    ResourceAllocator,
    ResourceQuota,
    ConversionRates
)
import time
import json


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def simulate_action_execution(action_type: str, resources: ResourceQuota) -> OutcomeType:
    """
    Simulate action execution with resources

    In production, this would be actual work:
    - "compute" → run ML model on GPU
    - "read" → fetch data from storage
    - "write" → store results
    """
    # Simple simulation based on action type
    if "compute" in action_type.lower():
        # Compute is more likely to have quality variance
        if resources.gpu_seconds > 0:
            return OutcomeType.EXCEPTIONAL_QUALITY
        else:
            return OutcomeType.STANDARD_SUCCESS
    elif "write" in action_type.lower():
        return OutcomeType.STANDARD_SUCCESS
    else:
        return OutcomeType.STANDARD_SUCCESS


def demonstrate_complete_flow():
    """
    Complete demonstration of authorization → resources → reputation flow
    """

    print_header("Web4 Complete Integration: Auth + Resources + Reputation")

    # Initialize all engines
    auth_engine = AuthorizationEngine("society:ai_lab")
    rep_engine = ReputationEngine()
    resource_allocator = ResourceAllocator("society:ai_lab")

    # Create society resource pool
    total_resources = ResourceQuota(
        cpu_cycles=10_000_000_000,  # 10B cycles
        memory_bytes=10_000_000_000,  # 10GB
        storage_bytes=100_000_000_000,  # 100GB
        network_bytes=10_000_000_000,  # 10GB
        gpu_seconds=100  # 100 GPU-seconds
    )

    resource_allocator.create_pool("ai_lab_pool", total_resources)

    print(f"\n🏛️  Society Resource Pool Created:")
    print(f"   CPU: 10B cycles")
    print(f"   Memory: 10GB")
    print(f"   Storage: 100GB")
    print(f"   Network: 10GB")
    print(f"   GPU: 100 seconds")

    # Create AI agent entity
    entity_lct = "lct:ai:ml_researcher"
    role_lct = "role:researcher"

    # Human delegates authority to AI agent
    delegation = AgentDelegation(
        delegation_id="deleg:ml_research_001",
        client_lct="lct:human:supervisor",
        agent_lct=entity_lct,
        role_lct=role_lct,
        granted_permissions={"read", "compute", "write"},
        atp_budget=500,  # 500 ATP tokens
        max_actions_per_hour=20
    )
    auth_engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id=entity_lct,
        entity_type="AI",
        society_id="society:ai_lab",
        birth_certificate_hash="hash_ml_researcher",
        public_key="pubkey_ml"
    )

    # Create resource allocation from ATP budget
    allocation, alloc_error = resource_allocator.create_allocation(
        entity_lct=entity_lct,
        atp_budget=delegation.atp_budget,
        pool_id="ai_lab_pool",
        duration_seconds=3600  # 1 hour
    )

    if not allocation:
        print(f"❌ Resource allocation failed: {alloc_error}")
        return

    print(f"\n✅ Agent Setup Complete:")
    print(f"   Entity: {entity_lct}")
    print(f"   Role: {role_lct}")
    print(f"   ATP Budget: {delegation.atp_budget}")
    print(f"   Resource Allocation: {allocation.allocation_id}")

    # Simulate work sequence
    actions = [
        {
            "action": "read",
            "resource": "dataset:climate_data",
            "atp_cost": 20,
            "resources_needed": ResourceQuota(
                storage_bytes=100_000_000,  # 100MB read
                network_bytes=10_000_000  # 10MB transfer
            )
        },
        {
            "action": "compute",
            "resource": "model:climate_forecast",
            "atp_cost": 100,
            "resources_needed": ResourceQuota(
                cpu_cycles=50_000_000,  # 50M cycles
                memory_bytes=500_000_000,  # 500MB RAM
                gpu_seconds=5  # 5 GPU-seconds
            )
        },
        {
            "action": "write",
            "resource": "results:forecast_2025",
            "atp_cost": 30,
            "resources_needed": ResourceQuota(
                storage_bytes=50_000_000,  # 50MB write
                network_bytes=5_000_000  # 5MB transfer
            )
        },
        {
            "action": "compute",
            "resource": "model:optimization",
            "atp_cost": 150,
            "resources_needed": ResourceQuota(
                cpu_cycles=100_000_000,  # 100M cycles
                memory_bytes=1_000_000_000,  # 1GB RAM
                gpu_seconds=10  # 10 GPU-seconds
            )
        },
    ]

    print_header("Action Execution Sequence")

    for i, action_spec in enumerate(actions, 1):
        print(f"\n--- Action {i}: {action_spec['action'].upper()} ---")

        # Get current state
        reputation = rep_engine.get_reputation(entity_lct, role_lct)
        if reputation:
            print(f"Current Reputation: T3={reputation.t3.average():.3f}, V3={reputation.v3.average():.3f}")

        # Request authorization
        auth_request = AuthorizationRequest(
            requester_lct=entity_lct,
            action=action_spec['action'],
            target_resource=action_spec['resource'],
            atp_cost=action_spec['atp_cost'],
            context={"allocation_id": allocation.allocation_id},
            delegation_id="deleg:ml_research_001"
        )

        auth_result = auth_engine.authorize_action(auth_request, credential)

        print(f"\n🔒 Authorization: {auth_result.decision.value.upper()}")

        if auth_result.decision == AuthorizationDecision.GRANTED:
            print(f"   ATP Remaining (Delegation): {auth_result.atp_remaining}")

            # Check resource availability
            can_allocate, alloc_msg = allocation.can_allocate(
                action_spec['resources_needed'],
                resource_allocator.rates
            )

            if can_allocate:
                # Consume resources
                success, consume_msg = resource_allocator.consume_resources(
                    allocation.allocation_id,
                    action_spec['resources_needed']
                )

                if success:
                    print(f"   ✅ Resources allocated: {consume_msg}")
                    print(f"   Resources consumed:")
                    for rtype, amount in action_spec['resources_needed'].to_dict().items():
                        if amount > 0:
                            print(f"      {rtype}: {amount:,}")

                    # Simulate action execution
                    outcome = simulate_action_execution(
                        action_spec['action'],
                        action_spec['resources_needed']
                    )

                    print(f"\n   📊 Action Outcome: {outcome.value}")

                    # Update reputation
                    witnesses = ["witness:supervisor"] if outcome == OutcomeType.EXCEPTIONAL_QUALITY else []

                    rep_delta = rep_engine.compute_delta(
                        entity_lct=entity_lct,
                        role_lct=role_lct,
                        action_type=action_spec['action'],
                        action_target=action_spec['resource'],
                        outcome_type=outcome,
                        witnesses=witnesses,
                        action_id=auth_result.decision_log_hash
                    )

                    rep_engine.apply_delta(rep_delta)

                    print(f"   📈 Reputation Delta: T3={rep_delta.net_trust_change():+.4f}, V3={rep_delta.net_value_change():+.4f}")
                    if witnesses:
                        print(f"   ✅ Witnessed")

                else:
                    print(f"   ❌ Resource consumption failed: {consume_msg}")
            else:
                print(f"   ❌ Resources unavailable: {alloc_msg}")
        else:
            print(f"   ❌ Denied: {auth_result.denial_reason.value if auth_result.denial_reason else 'N/A'}")

    # Final statistics
    print_header("Final State")

    reputation = rep_engine.get_reputation(entity_lct, role_lct)
    auth_stats = auth_engine.get_authorization_stats(entity_lct)
    allocator_stats = resource_allocator.get_stats()

    print(f"\n🎯 Reputation Profile:")
    if reputation:
        print(f"   Trust (T3): {reputation.t3.average():.3f}")
        print(f"     - Talent: {reputation.t3.talent:.3f}")
        print(f"     - Training: {reputation.t3.training:.3f}")
        print(f"     - Temperament: {reputation.t3.temperament:.3f}")
        print(f"   Value (V3): {reputation.v3.average():.3f}")
        print(f"     - Veracity: {reputation.v3.veracity:.3f}")
        print(f"     - Validity: {reputation.v3.validity:.3f}")
        print(f"     - Value: {reputation.v3.value:.3f}")
        print(f"   Success Rate: {reputation.success_rate():.1%}")
        print(f"   Total Actions: {reputation.total_actions}")

    print(f"\n📊 Authorization Statistics:")
    print(f"   Total Requests: {auth_stats['total']}")
    print(f"   Granted: {auth_stats['granted']}")
    print(f"   Denied: {auth_stats['denied']}")
    print(f"   Success Rate: {auth_stats['success_rate']:.1%}")

    print(f"\n💰 Resource Usage:")
    print(f"   ATP Budget: {delegation.atp_budget}")
    print(f"   ATP Spent (Delegation): {delegation.atp_spent}")
    print(f"   ATP Spent (Resources): {allocation.atp_consumed}")
    print(f"   ATP Remaining: {allocation.remaining_atp()}")

    print(f"\n🏊 Resource Pool Utilization:")
    pool_stats = allocator_stats['pools']['ai_lab_pool']
    for resource_name, utilization_pct in pool_stats['utilization'].items():
        print(f"   {resource_name.upper()}: {utilization_pct:.2f}%")

    # Check for gaming
    is_gaming, reason = rep_engine.detect_gaming_attempt(entity_lct, role_lct)
    print(f"\n🔍 Gaming Detection: {'⚠️  SUSPICIOUS' if is_gaming else '✅ Clean'}")
    if is_gaming:
        print(f"   Reason: {reason}")

    print_header("KEY ACHIEVEMENTS")
    print("""
✅ Complete Integration Demonstrated:
   1. Authorization verifies credentials and permissions
   2. Resource allocator converts ATP to concrete resources
   3. Actual work consumes metered resources
   4. Outcomes update reputation (T3/V3)
   5. Trust affects future authorization decisions
   6. Resources drawn from society pool (not individual)
   7. Fair accounting: charge actual cost, not estimate

🔒 Security Properties:
   - Multi-layer authorization (LCT, role, trust, ATP, resources)
   - Resource pools prevent single-entity exhaustion
   - Metering tracks actual consumption
   - Budget enforcement at multiple levels
   - Reputation earned through witnessed performance

💡 Economic Properties:
   - ATP is universal currency
   - Resources are specific goods with conversion rates
   - Under-budget actions charged fairly
   - Over-budget actions denied early
   - Society owns resources, entities rent them

🎯 Trust Properties:
   - Trust enables resource access
   - Resource use affects reputation
   - Reputation influences future trust
   - Virtuous cycle for good actors
   - Gaming detection prevents manipulation
    """)


if __name__ == "__main__":
    demonstrate_complete_flow()
