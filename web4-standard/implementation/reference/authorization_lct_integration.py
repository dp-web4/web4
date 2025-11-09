"""
Authorization + LCT Integration
===============================

Complete integration showing how LCT Registry provides real identity
verification for the Authorization Engine.

Flow:
1. Society mints LCTs for entities (humans, AIs)
2. Entities use their LCT credentials to sign requests
3. Authorization engine verifies LCT validity
4. If valid, proceeds with permission/budget/trust checks
5. Actions are attributed to verified identities
"""

from lct_registry import (
    LCTRegistry,
    EntityType,
    LCTCredential
)
from authorization_engine import (
    AuthorizationEngine,
    AuthorizationRequest,
    AgentDelegation,
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


def demonstrate_complete_identity_flow():
    """
    Demonstrate complete flow from identity creation to authorization
    """

    print_header("Web4 Complete Identity Flow: LCT → Authorization")

    # Step 1: Create society and LCT registry
    print("\n🏛️  Step 1: Creating Society and LCT Registry")

    society_id = "society:ai_research_lab"
    lct_registry = LCTRegistry(society_id)
    auth_engine = AuthorizationEngine(society_id)
    rep_engine = ReputationEngine()

    print(f"   Society: {society_id}")
    print(f"   LCT Registry: Ready")
    print(f"   Authorization Engine: Ready")
    print(f"   Reputation Engine: Ready")

    # Step 2: Mint LCT for human supervisor
    print("\n👤 Step 2: Minting LCT for Human Supervisor")

    supervisor_lct, error = lct_registry.mint_lct(
        entity_type=EntityType.HUMAN,
        entity_identifier="dr.smith@research.ai",
        witnesses=["witness:hr_dept", "witness:security_officer"],
        genesis_block="block:genesis_001"
    )

    if not supervisor_lct:
        print(f"   ❌ Failed: {error}")
        return

    print(f"   ✅ Supervisor LCT: {supervisor_lct.lct_id}")
    print(f"   Birth Certificate: {supervisor_lct.birth_certificate.certificate_hash[:16]}...")
    print(f"   Witnesses: {supervisor_lct.birth_certificate.witnesses}")

    # Step 3: Mint LCT for AI agent
    print("\n🤖 Step 3: Minting LCT for AI Research Agent")

    agent_lct, error = lct_registry.mint_lct(
        entity_type=EntityType.AI,
        entity_identifier="research_agent_v2_gpu_server_001",
        witnesses=["witness:supervisor", "witness:tech_lead"],
        genesis_block="block:genesis_002"
    )

    if not agent_lct:
        print(f"   ❌ Failed: {error}")
        return

    print(f"   ✅ Agent LCT: {agent_lct.lct_id}")
    print(f"   Birth Certificate: {agent_lct.birth_certificate.certificate_hash[:16]}...")
    print(f"   Witnesses: {agent_lct.birth_certificate.witnesses}")

    # Step 4: Supervisor delegates to AI agent
    print("\n📋 Step 4: Supervisor Delegates Authority to Agent")

    delegation = AgentDelegation(
        delegation_id="deleg:research_project_alpha",
        client_lct=supervisor_lct.lct_id,
        agent_lct=agent_lct.lct_id,
        role_lct="role:researcher",
        granted_permissions={"read", "compute", "write"},
        atp_budget=1000,
        max_actions_per_hour=50
    )

    auth_engine.register_delegation(delegation)

    print(f"   Delegation: {delegation.delegation_id}")
    print(f"   From: {supervisor_lct.lct_id}")
    print(f"   To: {agent_lct.lct_id}")
    print(f"   Permissions: {delegation.granted_permissions}")
    print(f"   ATP Budget: {delegation.atp_budget}")

    # Step 5: Agent attempts action with signed request
    print("\n🔐 Step 5: Agent Requests Authorization (Cryptographically Signed)")

    # Agent creates request message
    request_data = {
        "action": "compute",
        "target": "model:climate_forecast",
        "atp_cost": 100
    }

    request_message = f"{agent_lct.lct_id}:compute:model:climate_forecast:100".encode()

    # Agent signs with private key
    signature = agent_lct.sign(request_message)

    print(f"   Request: {request_data}")
    print(f"   Message: {request_message}")
    print(f"   Signature: {signature.hex()[:32]}...")

    # Verify signature using LCT registry
    lct_valid, lct_msg = lct_registry.verify_lct(
        agent_lct.lct_id,
        request_message,
        signature
    )

    print(f"\n   LCT Verification: {'✅ VALID' if lct_valid else f'❌ INVALID: {lct_msg}'}")

    if not lct_valid:
        print(f"   Authorization DENIED: Invalid LCT")
        return

    # Create authorization request
    auth_request = AuthorizationRequest(
        requester_lct=agent_lct.lct_id,
        action="compute",
        target_resource="model:climate_forecast",
        atp_cost=100,
        context={"trust_context": "research"},
        delegation_id=delegation.delegation_id
    )

    # Use the verified LCT credential for authorization
    # (In production, auth engine would query LCT registry directly)
    from authorization_engine import LCTCredential as AuthLCTCred

    auth_credential = AuthLCTCred(
        lct_id=agent_lct.lct_id,
        entity_type=agent_lct.entity_type.value,
        society_id=agent_lct.society_id,
        birth_certificate_hash=agent_lct.birth_certificate.certificate_hash,
        public_key=agent_lct.public_key_bytes.hex()
    )

    # Step 6: Authorization engine checks everything
    print(f"\n✅ Step 6: Authorization Engine Verification")

    auth_result = auth_engine.authorize_action(auth_request, auth_credential, signature)

    print(f"   Authorization Decision: {auth_result.decision.value.upper()}")

    if auth_result.decision == AuthorizationDecision.GRANTED:
        print(f"   ✅ GRANTED")
        print(f"   ATP Remaining: {auth_result.atp_remaining}")
        print(f"   Trust Score: {auth_result.actual_trust_score:.2f}")
        print(f"   Decision Hash: {auth_result.decision_log_hash[:16]}...")

        # Step 7: Action executes, outcome updates reputation
        print(f"\n📊 Step 7: Action Outcome Updates Reputation")

        outcome = OutcomeType.EXCEPTIONAL_QUALITY

        rep_delta = rep_engine.compute_delta(
            entity_lct=agent_lct.lct_id,
            role_lct="role:researcher",
            action_type="compute",
            action_target="model:climate_forecast",
            outcome_type=outcome,
            witnesses=["witness:supervisor"],  # Supervisor witnessed quality
            action_id=auth_result.decision_log_hash
        )

        rep_engine.apply_delta(rep_delta)

        print(f"   Outcome: {outcome.value}")
        print(f"   T3 Delta: {rep_delta.net_trust_change():+.4f}")
        print(f"   V3 Delta: {rep_delta.net_value_change():+.4f}")
        print(f"   Witnessed: ✅")

        reputation = rep_engine.get_reputation(agent_lct.lct_id, "role:researcher")

        print(f"\n   Updated Reputation:")
        print(f"   Trust (T3): {reputation.t3.average():.3f}")
        print(f"   Value (V3): {reputation.v3.average():.3f}")

    else:
        print(f"   ❌ DENIED: {auth_result.denial_reason.value if auth_result.denial_reason else 'Unknown'}")

    # Step 8: Demonstrate full traceability
    print_header("Full Identity Traceability")

    print(f"\n🔍 Complete Audit Trail:")
    print(f"\n   Entity Identifier: research_agent_v2_gpu_server_001")
    print(f"   ↓")
    print(f"   LCT: {agent_lct.lct_id}")
    print(f"   ↓")
    print(f"   Birth Certificate: {agent_lct.birth_certificate.certificate_hash[:16]}...")
    print(f"   ├─ Society: {agent_lct.birth_certificate.society_id}")
    print(f"   ├─ Witnesses: {agent_lct.birth_certificate.witnesses}")
    print(f"   ├─ Genesis Block: {agent_lct.birth_certificate.genesis_block}")
    print(f"   └─ Birth Time: {time.ctime(agent_lct.birth_certificate.birth_timestamp)}")
    print(f"   ↓")
    print(f"   Delegation: {delegation.delegation_id}")
    print(f"   ├─ Client: {supervisor_lct.lct_id}")
    print(f"   ├─ Role: {delegation.role_lct}")
    print(f"   └─ Permissions: {delegation.granted_permissions}")
    print(f"   ↓")
    print(f"   Authorization: {auth_result.decision_log_hash[:16]}...")
    print(f"   ├─ Decision: {auth_result.decision.value}")
    print(f"   ├─ Trust: {auth_result.actual_trust_score:.2f}")
    print(f"   └─ ATP Cost: {auth_request.atp_cost}")
    print(f"   ↓")
    print(f"   Reputation Update: T3={reputation.t3.average():.3f}, V3={reputation.v3.average():.3f}")

    print(f"\n✅ Every action traced back to verified identity")
    print(f"✅ Cryptographic proof at every step")
    print(f"✅ Society-witnessed birth certificate")
    print(f"✅ Immutable audit trail (ledger integration pending)")

    # Step 9: Demonstrate identity lifecycle
    print_header("Identity Lifecycle Management")

    # Create another agent
    print(f"\n🤖 Creating second agent...")

    agent2_lct, _ = lct_registry.mint_lct(
        entity_type=EntityType.AI,
        entity_identifier="research_agent_v3_gpu_server_002",
        witnesses=["witness:supervisor"],
        genesis_block="block:genesis_003"
    )

    print(f"   ✅ Agent 2 LCT: {agent2_lct.lct_id}")

    # Suspend agent 2 (security issue discovered)
    print(f"\n🚫 Security issue discovered - suspending agent 2...")

    lct_registry.suspend_lct(agent2_lct.lct_id, "Under security review")

    # Try to use suspended LCT
    message = b"test"
    sig = agent2_lct.sign(message)

    suspended_valid, suspended_msg = lct_registry.verify_lct(
        agent2_lct.lct_id,
        message,
        sig
    )

    print(f"   Suspended LCT verification: {'❌ BLOCKED' if not suspended_valid else '✅'}")
    print(f"   Reason: {suspended_msg}")

    # Registry stats
    print(f"\n📊 Registry Statistics:")

    stats = lct_registry.get_stats()
    print(f"   Total LCTs: {stats['total_lcts']}")
    print(f"   Active: {stats['active']}")
    print(f"   Suspended: {stats['suspended']}")
    print(f"   Humans: {stats['entity_types']['HUMAN']}")
    print(f"   AIs: {stats['entity_types']['AI']}")

    print_header("KEY ACHIEVEMENTS")

    print("""
✅ Complete Identity System:
   1. Real cryptography (Ed25519 signatures)
   2. Birth certificates (society-witnessed)
   3. Duplicate prevention (one LCT per entity)
   4. Lifecycle management (suspend/revoke/reactivate)
   5. Cryptographic verification at authorization

🔐 Security Properties:
   - Private keys never leave owner
   - Signatures prove identity
   - Birth certificates prevent forgery
   - Society witnesses validate membership
   - Audit trail for all operations

🎯 Integration Complete:
   - LCT Registry ← mints identities
   - Authorization Engine ← verifies identities
   - Reputation Engine ← tracks identities
   - Resource Allocator ← allocates to identities

📝 Next Steps:
   - Ledger integration (immutable birth certificates)
   - Hardware binding (TPM/SE for keys)
   - Cross-society identity portability
   - MRH graph updates from identity lifecycle
    """)


if __name__ == "__main__":
    demonstrate_complete_identity_flow()
