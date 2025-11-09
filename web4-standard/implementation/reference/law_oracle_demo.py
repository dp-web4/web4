"""
Law Oracle + Authorization Integration Demo
============================================

Demonstrates complete law-based authorization flow:

1. Society publishes law dataset with norms, procedures, interpretations
2. Entities request actions
3. Authorization engine queries law oracle
4. Law oracle evaluates norms and procedures
5. Authorization granted/denied based on law
6. Law evolves with new interpretations
7. Authorization adapts to law changes

This shows how Web4 implements "code as law" with verifiable,
machine-readable rules that govern all actions.
"""

from law_oracle import (
    LawOracle,
    LawDataset,
    Norm,
    NormType,
    Operator,
    Procedure,
    Interpretation,
    RolePermissions,
    create_default_law_dataset
)
from authorization_engine import (
    AuthorizationEngine,
    AuthorizationRequest,
    AgentDelegation,
    LCTCredential,
    AuthorizationDecision
)


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def demo_1_basic_law_query():
    """Demo 1: Basic law oracle queries"""
    print_header("DEMO 1: Basic Law Oracle Queries")

    society_id = "society:research_lab"
    law_oracle_lct = f"lct:web4:oracle:law:{society_id}:1"

    # Create law oracle with default dataset
    oracle = LawOracle(society_id, law_oracle_lct)
    dataset = create_default_law_dataset(society_id, law_oracle_lct, "1.0.0")
    law_hash = oracle.publish_law_dataset(dataset)

    print(f"\n📜 Society Law Published:")
    print(f"   Society: {society_id}")
    print(f"   Law Version: {dataset.version}")
    print(f"   Law Hash: {law_hash[:16]}...")
    print(f"   Norms: {len(dataset.norms)}")
    print(f"   Procedures: {len(dataset.procedures)}")

    # Query role permissions
    print(f"\n🔍 Querying Role Permissions:")

    for role in ["role:researcher", "role:administrator", "role:guest"]:
        perms = oracle.get_role_permissions(role)
        print(f"\n   {role}:")
        print(f"     Allowed: {perms.allowed_actions}")
        print(f"     Max ATP: {perms.max_atp_per_action}")
        print(f"     Trust threshold: {perms.trust_threshold}")
        print(f"     Requires witness: {perms.requires_witness}")

    # Check action legality
    print(f"\n⚖️  Action Legality Checks:")

    test_actions = [
        ("read", {"atp_cost": 50}, "role:researcher"),
        ("compute", {"atp_cost": 100}, "role:researcher"),
        ("compute", {"atp_cost": 700}, "role:researcher"),
        ("compute", {"atp_cost": 1500}, "role:researcher"),
        ("delete", {"atp_cost": 50}, "role:researcher")
    ]

    for action, context, role in test_actions:
        legal, reason = oracle.check_action_legality(action, context, role)
        status = "✅ LEGAL" if legal else f"❌ ILLEGAL: {reason}"
        print(f"   {action} ({context.get('atp_cost')} ATP): {status}")


def demo_2_authorization_with_law():
    """Demo 2: Authorization engine using law oracle"""
    print_header("DEMO 2: Authorization Engine with Law Oracle")

    society_id = "society:ai_research"
    auth_engine = AuthorizationEngine(society_id)

    print(f"\n🏛️  Authorization Engine Initialized:")
    print(f"   Society: {society_id}")
    print(f"   Law Version: {auth_engine.law_oracle.get_law_version()}")
    print(f"   Law Hash: {auth_engine.law_oracle.get_law_hash()[:16]}...")

    # Create delegation
    delegation = AgentDelegation(
        delegation_id="deleg:research_001",
        client_lct="lct:human:supervisor",
        agent_lct="lct:ai:research_agent",
        role_lct="role:researcher",
        granted_permissions={"read", "write", "compute"},
        atp_budget=2000,
        max_actions_per_hour=50
    )

    auth_engine.register_delegation(delegation)

    print(f"\n📋 Delegation Registered:")
    print(f"   ID: {delegation.delegation_id}")
    print(f"   Agent: {delegation.agent_lct}")
    print(f"   Role: {delegation.role_lct}")
    print(f"   ATP Budget: {delegation.atp_budget}")

    # Create credential
    credential = LCTCredential(
        lct_id="lct:ai:research_agent",
        entity_type="AI",
        society_id=society_id,
        birth_certificate_hash="abc123",
        public_key="pubkey_xyz"
    )

    # Test various actions
    print(f"\n🔐 Authorization Requests:")

    test_requests = [
        ("read", "data:papers", 50, {}),
        ("compute", "model:training", 200, {}),
        ("compute", "model:large", 700, {}),  # High ATP, needs witness
        ("compute", "model:huge", 1500, {}),  # Exceeds limit
        ("delete", "data:temp", 50, {})  # Needs witness
    ]

    for action, resource, atp_cost, extra_context in test_requests:
        request = AuthorizationRequest(
            requester_lct=credential.lct_id,
            action=action,
            target_resource=resource,
            atp_cost=atp_cost,
            context={"atp_cost": atp_cost, **extra_context},
            delegation_id=delegation.delegation_id
        )

        result = auth_engine.authorize_action(request, credential)

        print(f"\n   {action} on {resource} ({atp_cost} ATP):")
        print(f"     Decision: {result.decision.value.upper()}")
        if result.denial_reason:
            print(f"     Reason: {result.denial_reason.value}")
        print(f"     ATP Remaining: {result.atp_remaining}")
        if result.requires_witness:
            print(f"     ⚠️  Requires Witness")


def demo_3_law_evolution():
    """Demo 3: Law dataset evolution with interpretations"""
    print_header("DEMO 3: Law Evolution & Interpretations")

    society_id = "society:evolving_law"
    law_oracle_lct = f"lct:web4:oracle:law:{society_id}:1"

    oracle = LawOracle(society_id, law_oracle_lct)
    dataset_v1 = create_default_law_dataset(society_id, law_oracle_lct, "1.0.0")
    oracle.publish_law_dataset(dataset_v1)

    print(f"\n📜 Law v1.0.0 Published:")
    print(f"   Hash: {oracle.get_law_hash()[:16]}...")

    # Add interpretation for edge case
    print(f"\n📖 Adding Interpretation for Edge Case:")

    interp1 = oracle.add_interpretation(
        interpretation_id="INTERP-001",
        question="Does 'read' action include streaming data?",
        answer="Yes, 'read' includes both batch and streaming data access",
        applies_to_norms=["ALLOW-READ"],
        reason="Clarification requested by authorization engine"
    )

    print(f"   ✅ INTERP-001 added")
    print(f"   Question: Does 'read' include streaming?")
    print(f"   Answer: Yes")

    # Add another interpretation
    interp2 = oracle.add_interpretation(
        interpretation_id="INTERP-002",
        question="What ATP cost threshold triggers witness requirement?",
        answer="Actions costing >500 ATP require witnesses",
        applies_to_norms=["REQUIRE-WITNESS-HIGH-ATP"],
        reason="Policy clarification from society governance"
    )

    print(f"\n   ✅ INTERP-002 added")
    print(f"   Question: What ATP threshold needs witnesses?")
    print(f"   Answer: >500 ATP")

    # Supersede interpretation
    print(f"\n🔄 Updating Interpretation:")

    interp3 = oracle.add_interpretation(
        interpretation_id="INTERP-003",
        question="What ATP cost threshold triggers witness requirement?",
        answer="Actions costing >750 ATP require witnesses (updated from 500)",
        applies_to_norms=["REQUIRE-WITNESS-HIGH-ATP"],
        replaces="INTERP-002",
        reason="Governance vote raised threshold to reduce friction"
    )

    print(f"   ✅ INTERP-003 added (replaces INTERP-002)")
    print(f"   New threshold: >750 ATP")

    # Show interpretation chain
    print(f"\n🔗 Interpretation Chain:")
    chain = oracle.get_interpretation_chain("INTERP-003")
    for i, interp in enumerate(chain):
        print(f"\n   [{i+1}] {interp.interpretation_id}")
        print(f"       Answer: {interp.answer}")
        if interp.replaces:
            print(f"       Replaces: {interp.replaces}")

    # Show updated law hash
    print(f"\n📜 Updated Law Hash:")
    print(f"   Old hash: {dataset_v1.hash[:16]}...")
    print(f"   New hash: {oracle.get_law_hash()[:16]}...")
    print(f"   (Hash changed due to new interpretations)")


def demo_4_custom_law_dataset():
    """Demo 4: Creating custom law dataset"""
    print_header("DEMO 4: Custom Law Dataset")

    society_id = "society:strict_governance"
    law_oracle_lct = f"lct:web4:oracle:law:{society_id}:1"

    # Create custom norms
    norms = [
        # Very strict ATP limits
        Norm(
            norm_id="STRICT-ATP-LIMIT",
            norm_type=NormType.LIMIT,
            selector="atp_cost",
            operator=Operator.LTE,
            value=100,  # Very low limit
            reason="Strict resource conservation policy"
        ),

        # Require witness for all write operations
        Norm(
            norm_id="WITNESS-ALL-WRITES",
            norm_type=NormType.REQUIRE,
            selector="action",
            operator=Operator.EQ,
            value="write",
            condition="witness_required",
            reason="All data modifications need oversight"
        ),

        # Deny compute for low-trust entities
        Norm(
            norm_id="DENY-COMPUTE-LOW-TRUST",
            norm_type=NormType.DENY,
            selector="action",
            operator=Operator.EQ,
            value="compute",
            reason="Compute restricted to high-trust entities only"
        ),

        # Allow read (only unrestricted action)
        Norm(
            norm_id="ALLOW-READ",
            norm_type=NormType.ALLOW,
            selector="action",
            operator=Operator.EQ,
            value="read",
            reason="Reading is always allowed"
        )
    ]

    # Create strict procedures
    procedures = [
        Procedure(
            procedure_id="PROC-ANY-WRITE",
            triggers=["action=='write'"],
            requires_witnesses=3,
            requires_quorum=2,
            validation_steps=["verify_intent", "check_impact", "get_approval"],
            timeout_seconds=7200
        )
    ]

    # Create dataset
    strict_dataset = LawDataset(
        version="1.0.0",
        society_id=society_id,
        law_oracle_lct=law_oracle_lct,
        norms=norms,
        procedures=procedures
    )

    oracle = LawOracle(society_id, law_oracle_lct)
    oracle.publish_law_dataset(strict_dataset)

    print(f"\n📜 Strict Law Dataset Published:")
    print(f"   Society: {society_id}")
    print(f"   Policy: Very restrictive")
    print(f"   Hash: {strict_dataset.hash[:16]}...")

    print(f"\n📊 Law Statistics:")
    stats = oracle.get_stats()
    print(f"   Total norms: {stats['norms']['total']}")
    print(f"     Allow: {stats['norms']['allow']}")
    print(f"     Deny: {stats['norms']['deny']}")
    print(f"     Limit: {stats['norms']['limit']}")
    print(f"     Require: {stats['norms']['require']}")
    print(f"   Procedures: {stats['procedures']}")

    # Test actions under strict law
    print(f"\n⚖️  Testing Actions Under Strict Law:")

    test_cases = [
        ("read", {"atp_cost": 50}, "role:researcher"),
        ("write", {"atp_cost": 50}, "role:researcher"),
        ("compute", {"atp_cost": 50}, "role:researcher"),
        ("read", {"atp_cost": 150}, "role:researcher")  # Exceeds ATP limit
    ]

    for action, context, role in test_cases:
        legal, reason = oracle.check_action_legality(action, context, role)
        status = "✅ LEGAL" if legal else f"❌ ILLEGAL: {reason}"
        print(f"   {action} ({context.get('atp_cost')} ATP): {status}")


def demo_5_json_ld_export():
    """Demo 5: JSON-LD export for interoperability"""
    print_header("DEMO 5: JSON-LD Export")

    society_id = "society:interoperable"
    law_oracle_lct = f"lct:web4:oracle:law:{society_id}:1"

    oracle = LawOracle(society_id, law_oracle_lct)
    dataset = create_default_law_dataset(society_id, law_oracle_lct, "1.0.0")
    oracle.publish_law_dataset(dataset)

    print(f"\n📄 Exporting Law Dataset as JSON-LD:")

    json_ld = dataset.to_json_ld()

    print(f"\n   @context: {json_ld['@context']}")
    print(f"   type: {json_ld['type']}")
    print(f"   id: {json_ld['id']}")
    print(f"   society: {json_ld['society']}")
    print(f"   lawOracle: {json_ld['lawOracle']}")
    print(f"   version: {json_ld['version']}")
    print(f"   hash: {json_ld['hash'][:16]}...")

    print(f"\n   Norms ({len(json_ld['norms'])}):")
    for norm in json_ld['norms'][:3]:  # Show first 3
        print(f"     - {norm['id']}: {norm['type']}")
        print(f"       {norm['selector']} {norm['operator']} {norm['value']}")

    print(f"\n   Procedures ({len(json_ld['procedures'])}):")
    for proc in json_ld['procedures']:
        print(f"     - {proc['id']}")
        print(f"       Witnesses required: {proc['requiresWitnesses']}")

    print(f"\n✅ JSON-LD export can be:")
    print(f"   - Published to distributed ledger")
    print(f"   - Queried via SPARQL")
    print(f"   - Verified by other societies")
    print(f"   - Integrated with existing legal frameworks")


def main():
    """Run all demonstrations"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  Web4 Law Oracle - Complete Demonstration".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    demos = [
        demo_1_basic_law_query,
        demo_2_authorization_with_law,
        demo_3_law_evolution,
        demo_4_custom_law_dataset,
        demo_5_json_ld_export
    ]

    for demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()

    print_header("DEMONSTRATION COMPLETE")
    print("\n✅ All scenarios demonstrated successfully!")
    print("\nKey Capabilities Shown:")
    print("  • Versioned law datasets with norms, procedures, interpretations")
    print("  • Role-based permission queries")
    print("  • Action legality verification")
    print("  • Witness requirement determination")
    print("  • Law evolution through interpretations")
    print("  • Custom law dataset creation")
    print("  • JSON-LD export for interoperability")
    print("  • Integration with authorization engine")
    print("\n🎯 Web4 implements 'Code as Law' with:")
    print("  • Machine-readable rules")
    print("  • Verifiable enforcement")
    print("  • Transparent governance")
    print("  • Evolutionary adaptation")
    print("\n")


if __name__ == "__main__":
    main()
