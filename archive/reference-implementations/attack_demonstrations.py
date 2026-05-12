"""
Web4 Attack Demonstrations
==========================

Practical demonstrations of attack vectors against Web4 systems.
Each attack shows the exploit, impact measurement, and mitigation validation.

**WARNING**: This code is for security research and testing only.
Do not use against production systems without authorization.
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
    ResourceQuota
)
from collections import Counter


def print_attack_header(attack_name: str):
    print(f"\n{'='*70}")
    print(f"  ATTACK: {attack_name}")
    print('='*70)


def attack_1_permission_escalation():
    """
    Demonstrate permission escalation attempt

    Attacker tries to perform action beyond granted permissions
    """
    print_attack_header("Permission Escalation")

    engine = AuthorizationEngine("society:test")

    # Create read-only delegation
    delegation = AgentDelegation(
        delegation_id="deleg:readonly",
        client_lct="lct:human:user",
        agent_lct="lct:ai:attacker",
        role_lct="role:reader",
        granted_permissions={"read"},  # Only read!
        atp_budget=1000
    )
    engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id="lct:ai:attacker",
        entity_type="AI",
        society_id="society:test",
        birth_certificate_hash="test",
        public_key="test"
    )

    print("\n📋 Delegation created with permissions: read")
    print("🎯 Attacker attempts to escalate to write...")

    # Attempt write (not granted)
    request = AuthorizationRequest(
        requester_lct="lct:ai:attacker",
        action="write",  # Not in granted_permissions
        target_resource="data:sensitive",
        atp_cost=10,
        context={},
        delegation_id="deleg:readonly"
    )

    result = engine.authorize_action(request, credential)

    print(f"\n✅ Authorization Result: {result.decision.value.upper()}")
    if result.decision == AuthorizationDecision.DENIED:
        print(f"   Denial Reason: {result.denial_reason.value}")
        print(f"   ✅ MITIGATION EFFECTIVE: Permission escalation blocked!")
    else:
        print(f"   ❌ VULNERABILITY: Permission escalation succeeded!")

    return result.decision == AuthorizationDecision.DENIED


def attack_2_self_promotion():
    """
    Demonstrate reputation gaming through self-promotion

    Attacker claims success without witnesses to inflate reputation
    """
    print_attack_header("Self-Promotion (Reputation Gaming)")

    engine = ReputationEngine()

    entity_lct = "lct:ai:self_promoter"
    role_lct = "role:expert"

    print("\n🎯 Attacker submits 20 'successful' actions without witnesses...")

    for i in range(20):
        delta = engine.compute_delta(
            entity_lct=entity_lct,
            role_lct=role_lct,
            action_type="analyze",
            action_target=f"fake_work_{i}",
            outcome_type=OutcomeType.NOVEL_SUCCESS,  # Claim exceptional work
            witnesses=[],  # No witnesses!
            action_id=f"action_{i}"
        )
        engine.apply_delta(delta)

    reputation = engine.get_reputation(entity_lct, role_lct)

    print(f"\n📊 Final Reputation:")
    print(f"   Trust (T3): {reputation.t3.average():.3f}")
    print(f"   Value (V3): {reputation.v3.average():.3f}")
    print(f"   Success Rate: {reputation.success_rate():.1%}")

    # Check gaming detection
    is_gaming, reason = engine.detect_gaming_attempt(entity_lct, role_lct)

    print(f"\n🔍 Gaming Detection: {'⚠️  FLAGGED' if is_gaming else '✅ Clean'}")
    if is_gaming:
        print(f"   Reason: {reason}")
        print(f"   ✅ MITIGATION EFFECTIVE: Gaming detected!")
    else:
        print(f"   ❌ VULNERABILITY: Gaming went undetected!")

    return is_gaming


def attack_3_collusion_network():
    """
    Demonstrate collusion through mutual witnessing

    Group of attackers witness each other's fake successes
    """
    print_attack_header("Collusion Network (Mutual Witnessing)")

    engine = ReputationEngine()

    colluders = [
        "lct:ai:colluder_1",
        "lct:ai:colluder_2",
        "lct:ai:colluder_3"
    ]

    role_lct = "role:expert"

    print(f"\n🎯 Creating collusion network with {len(colluders)} participants...")
    print("   Each participant claims success, others witness...")

    for actor in colluders:
        witnesses = [c for c in colluders if c != actor]

        for i in range(10):
            delta = engine.compute_delta(
                entity_lct=actor,
                role_lct=role_lct,
                action_type="analyze",
                action_target=f"work_{i}",
                outcome_type=OutcomeType.EXCEPTIONAL_QUALITY,
                witnesses=witnesses  # Other colluders witness
            )
            engine.apply_delta(delta)

    # Analyze witness patterns
    print(f"\n📊 Collusion Analysis:")

    for actor in colluders:
        reputation = engine.get_reputation(actor, role_lct)

        # Count witness frequency
        witness_counts = Counter()
        for delta in reputation.history:
            for witness in delta.witnesses:
                witness_counts[witness] += 1

        total_witnesses = sum(witness_counts.values())
        max_witness = witness_counts.most_common(1)[0] if witness_counts else (None, 0)

        concentration = (max_witness[1] / total_witnesses * 100) if total_witnesses > 0 else 0

        print(f"\n   {actor}:")
        print(f"      Trust (T3): {reputation.t3.average():.3f}")
        print(f"      Witness Concentration: {concentration:.1f}% (max: {max_witness[0]})")

        # Check for reciprocal witnessing
        reciprocal_found = False
        for witness in witness_counts:
            witness_rep = engine.get_reputation(witness, role_lct)
            if witness_rep:
                for delta in witness_rep.history:
                    if actor in delta.witnesses:
                        reciprocal_found = True
                        print(f"      ⚠️  Reciprocal witnessing with {witness}")
                        break

        if concentration > 40 or reciprocal_found:
            print(f"      ✅ SUSPICIOUS: Collusion indicators detected")
        else:
            print(f"      ❌ VULNERABILITY: Collusion not detected")

    return concentration > 40 or reciprocal_found


def attack_4_resource_exhaustion():
    """
    Demonstrate resource pool exhaustion attack

    Attacker allocates maximum resources to block legitimate users
    """
    print_attack_header("Resource Pool Exhaustion")

    allocator = ResourceAllocator("society:test")

    # Create limited pool
    pool_quota = ResourceQuota(
        cpu_cycles=1_000_000_000,  # 1B cycles
        memory_bytes=1_000_000_000,  # 1GB
        storage_bytes=10_000_000_000,  # 10GB
        network_bytes=1_000_000_000,  # 1GB
        gpu_seconds=10
    )

    allocator.create_pool("limited_pool", pool_quota)

    print(f"\n🏊 Pool created with limited resources")
    print(f"   CPU: 1B cycles")
    print(f"   Memory: 1GB")
    print(f"   GPU: 10 seconds")

    print(f"\n🎯 Attacker requests maximum allocation...")

    # Attacker takes large allocation
    attacker_allocation, error = allocator.create_allocation(
        entity_lct="lct:ai:attacker",
        atp_budget=500,  # Converts to large quota
        pool_id="limited_pool"
    )

    if attacker_allocation:
        print(f"   ✅ Attacker got allocation: {attacker_allocation.allocation_id}")
        print(f"   Allocated CPU: {attacker_allocation.quota_limit.cpu_cycles:,}")
        print(f"   Allocated Memory: {attacker_allocation.quota_limit.memory_bytes:,}")

        # Check pool state
        pool_stats = allocator.get_stats()['pools']['limited_pool']
        print(f"\n📊 Pool Utilization After Attack:")
        for resource, util_pct in pool_stats['utilization'].items():
            print(f"   {resource.upper()}: {util_pct:.1f}%")

        # Try legitimate allocation
        print(f"\n👤 Legitimate user tries to allocate...")
        legit_allocation, legit_error = allocator.create_allocation(
            entity_lct="lct:human:legitimate_user",
            atp_budget=100,
            pool_id="limited_pool"
        )

        if legit_allocation:
            print(f"   ✅ Legitimate user got resources")
            print(f"   ❌ VULNERABILITY: Pool not properly protected")
            return False
        else:
            print(f"   ❌ Legitimate user BLOCKED: {legit_error}")
            print(f"   ✅ ATTACK SUCCESSFUL: Pool exhausted!")
            print(f"\n   ⚠️  MITIGATION NEEDED:")
            print(f"      - Reputation-based allocation priority")
            print(f"      - Per-entity allocation limits")
            print(f"      - Idle resource reclamation")
            return True
    else:
        print(f"   ❌ Attacker allocation failed: {error}")
        return False


def attack_5_atp_race_condition():
    """
    Demonstrate ATP budget race condition

    Two threads try to consume same budget simultaneously
    """
    print_attack_header("ATP Budget Race Condition")

    engine = AuthorizationEngine("society:test")

    delegation = AgentDelegation(
        delegation_id="deleg:race",
        client_lct="lct:human:user",
        agent_lct="lct:ai:agent",
        role_lct="role:worker",
        granted_permissions={"compute"},
        atp_budget=150  # Just enough for one request
    )
    engine.register_delegation(delegation)

    credential = LCTCredential(
        lct_id="lct:ai:agent",
        entity_type="AI",
        society_id="society:test",
        birth_certificate_hash="test",
        public_key="test"
    )

    print(f"\n💰 Delegation has ATP budget: {delegation.atp_budget}")
    print(f"   Two actions each cost: 100 ATP")
    print(f"   Budget sufficient for: 1 action only")

    print(f"\n🎯 Simulating race condition...")

    # First request
    request1 = AuthorizationRequest(
        requester_lct="lct:ai:agent",
        action="compute",
        target_resource="task:1",
        atp_cost=100,
        context={},
        delegation_id="deleg:race"
    )

    result1 = engine.authorize_action(request1, credential)

    print(f"\n   Request 1: {result1.decision.value.upper()}")
    print(f"   ATP Remaining: {result1.atp_remaining}")

    # Second request (should be denied - insufficient budget)
    request2 = AuthorizationRequest(
        requester_lct="lct:ai:agent",
        action="compute",
        target_resource="task:2",
        atp_cost=100,
        context={},
        delegation_id="deleg:race"
    )

    result2 = engine.authorize_action(request2, credential)

    print(f"\n   Request 2: {result2.decision.value.upper()}")
    if result2.decision == AuthorizationDecision.DENIED:
        print(f"   Denial Reason: {result2.denial_reason.value}")
        print(f"\n   ✅ MITIGATION EFFECTIVE: Second request blocked")
        print(f"   Budget properly enforced (sequential)")
    else:
        print(f"   ❌ VULNERABILITY: Both requests granted!")
        print(f"   Budget exceeded: {delegation.atp_spent} > {delegation.atp_budget}")

    # NOTE: True race condition requires threading, which we haven't implemented
    print(f"\n   ⚠️  NOTE: True race condition requires concurrent threads")
    print(f"      Current implementation is sequential (safe)")
    print(f"      Production needs atomic operations for thread-safety")

    return result2.decision == AuthorizationDecision.DENIED


def run_all_attacks():
    """Run all attack demonstrations"""

    print("\n" + "="*70)
    print("  WEB4 SECURITY AUDIT - ATTACK DEMONSTRATIONS")
    print("="*70)
    print("\nTesting authorization, reputation, and resource systems")
    print("against known attack vectors...")

    results = {
        "Permission Escalation": attack_1_permission_escalation(),
        "Self-Promotion Gaming": attack_2_self_promotion(),
        "Collusion Network": attack_3_collusion_network(),
        "Resource Exhaustion": attack_4_resource_exhaustion(),
        "ATP Race Condition": attack_5_atp_race_condition()
    }

    print("\n" + "="*70)
    print("  ATTACK SUMMARY")
    print("="*70)

    successful_attacks = 0
    mitigated_attacks = 0

    for attack_name, detected_or_mitigated in results.items():
        if detected_or_mitigated:
            print(f"   ✅ {attack_name}: Detected/Mitigated")
            mitigated_attacks += 1
        else:
            print(f"   ⚠️  {attack_name}: Successful/Undetected")
            successful_attacks += 1

    print(f"\n📊 Results:")
    print(f"   Mitigated: {mitigated_attacks}/{len(results)}")
    print(f"   Successful: {successful_attacks}/{len(results)}")
    print(f"   Mitigation Rate: {mitigated_attacks/len(results)*100:.1f}%")

    if successful_attacks > 0:
        print(f"\n⚠️  SECURITY GAPS IDENTIFIED:")
        print(f"   - Some attacks succeeded or went undetected")
        print(f"   - Review ATTACK_VECTOR_ANALYSIS.md for mitigations")
        print(f"   - Implement P0/P1 defenses before production")
    else:
        print(f"\n✅ ALL ATTACKS MITIGATED:")
        print(f"   Current defenses effective against tested vectors")
        print(f"   Continue monitoring for new attack patterns")

    print(f"\n" + "="*70)


if __name__ == "__main__":
    run_all_attacks()
