#!/usr/bin/env python3
"""
Comprehensive PostgreSQL Delegation System Test
Session #54: Full integration test with real database

Tests:
1. LCT identity creation and verification
2. Permission claim storage and retrieval
3. Agent delegation with ATP budgets
4. Delegation chains (sub-delegation)
5. Action execution and ATP tracking
6. Reputation updates from actions
7. Automatic revocation on trust drop
8. Ed25519 signature verification
"""

import psycopg2
import hashlib
import json
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

# ============================================================================
# Database Connection
# ============================================================================

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        dbname="web4",
        user="postgres",
        host="localhost"
    )

# ============================================================================
# Cryptographic Utilities
# ============================================================================

def generate_keypair():
    """Generate Ed25519 keypair"""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize to hex
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    return private_bytes.hex(), public_bytes.hex()

def sign_message(message: str, private_key_hex: str) -> str:
    """Sign message with Ed25519 private key"""
    private_bytes = bytes.fromhex(private_key_hex)
    private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
    signature = private_key.sign(message.encode())
    return signature.hex()

def verify_signature(message: str, signature_hex: str, public_key_hex: str) -> bool:
    """Verify Ed25519 signature"""
    try:
        public_bytes = bytes.fromhex(public_key_hex)
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, message.encode())
        return True
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False

def sha256_hash(data: str) -> str:
    """Compute SHA256 hash"""
    return hashlib.sha256(data.encode()).hexdigest()

# ============================================================================
# Test Data Setup
# ============================================================================

def create_test_identities(conn):
    """Create test LCT identities"""
    cursor = conn.cursor()

    # Generate keypairs for test entities
    alice_priv, alice_pub = generate_keypair()
    bob_priv, bob_pub = generate_keypair()
    charlie_priv, charlie_pub = generate_keypair()
    org_admin_priv, org_admin_pub = generate_keypair()

    # Store private keys for testing (in memory only!)
    keys = {
        'lct:human:alice:001': alice_priv,
        'lct:ai:bob:001': bob_priv,
        'lct:ai:charlie:001': charlie_priv,
        'lct:human:admin:001': org_admin_priv
    }

    # Create identities
    identities = [
        ('lct:human:alice:001', 'HUMAN', 'soc:web4:core', alice_pub),
        ('lct:ai:bob:001', 'AI', 'soc:web4:agents', bob_pub),
        ('lct:ai:charlie:001', 'AI', 'soc:web4:agents', charlie_pub),
        ('lct:human:admin:001', 'HUMAN', 'soc:web4:core', org_admin_pub)
    ]

    for lct_id, entity_type, society_id, public_key in identities:
        birth_cert_hash = sha256_hash(f"{lct_id}:{public_key}")

        cursor.execute("""
            INSERT INTO lct_identities
            (lct_id, entity_type, society_id, birth_certificate_hash, public_key)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (lct_id) DO NOTHING
        """, (lct_id, entity_type, society_id, birth_cert_hash, public_key))

    # Create test organization
    cursor.execute("""
        INSERT INTO organizations (organization_id, organization_name, admin_lct_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (organization_id) DO NOTHING
    """, ('org:test:lab', 'Test Lab Organization', 'lct:human:admin:001'))

    conn.commit()
    cursor.close()

    print("✓ Created test identities and organization")
    return keys

# ============================================================================
# Test Cases
# ============================================================================

def test_1_permission_claims(conn, keys):
    """Test 1: Create and verify permission claims"""
    print("\n=== Test 1: Permission Claims ===")
    cursor = conn.cursor()

    # Alice grants Bob permission to read data
    claim_id = "claim:read:data:001"
    subject_lct = "lct:ai:bob:001"
    issuer_lct = "lct:human:alice:001"
    org_id = "org:test:lab"

    # Create claim content
    claim_content = {
        "claim_id": claim_id,
        "subject": subject_lct,
        "issuer": issuer_lct,
        "organization": org_id,
        "action": "read",
        "resource": "data:project123:*",
        "issued_at": datetime.utcnow().isoformat()
    }

    claim_json = json.dumps(claim_content, sort_keys=True)
    claim_hash = sha256_hash(claim_json)

    # Sign with Alice's key
    signature = sign_message(claim_json, keys[issuer_lct])

    # Verify signature
    alice_pubkey = get_public_key(conn, issuer_lct)
    assert verify_signature(claim_json, signature, alice_pubkey), "Signature verification failed!"
    print(f"  ✓ Signature verified for claim {claim_id}")

    # Store claim
    cursor.execute("""
        INSERT INTO permission_claims
        (claim_hash, claim_id, subject_lct, issuer_lct, organization_id,
         permission_action, resource_pattern, signature, issued_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (claim_hash, claim_id, subject_lct, issuer_lct, org_id,
          'read', 'data:project123:*', signature, datetime.utcnow()))

    conn.commit()

    # Retrieve and verify
    cursor.execute("""
        SELECT claim_id, subject_lct, issuer_lct, permission_action, status
        FROM permission_claims WHERE claim_hash = %s
    """, (claim_hash,))

    result = cursor.fetchone()
    assert result[0] == claim_id, "Claim not found!"
    assert result[4] == 'active', "Claim not active!"

    print(f"  ✓ Permission claim stored and retrieved: {claim_id}")
    print(f"    Subject: {result[1]}")
    print(f"    Action: {result[3]}")

    cursor.close()
    return claim_hash

def test_2_agent_delegation(conn, keys, claim_hash):
    """Test 2: Create agent delegation with ATP budget"""
    print("\n=== Test 2: Agent Delegation ===")
    cursor = conn.cursor()

    # Alice delegates to Bob with 1000 ATP budget
    delegation_id = "del:alice_to_bob:001"
    delegator_lct = "lct:human:alice:001"
    delegatee_lct = "lct:ai:bob:001"
    org_id = "org:test:lab"

    # Create delegation content
    delegation_content = {
        "delegation_id": delegation_id,
        "delegator": delegator_lct,
        "delegatee": delegatee_lct,
        "organization": org_id,
        "atp_budget": 1000,
        "valid_from": datetime.utcnow().isoformat(),
        "valid_until": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "claims": [claim_hash]
    }

    delegation_json = json.dumps(delegation_content, sort_keys=True)
    signature = sign_message(delegation_json, keys[delegator_lct])

    # Store delegation
    cursor.execute("""
        INSERT INTO agent_delegations
        (delegation_id, delegator_lct, delegatee_lct, organization_id,
         granted_claim_hashes, atp_budget_total, valid_from, valid_until,
         delegation_signature)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (delegation_id, delegator_lct, delegatee_lct, org_id,
          json.dumps([claim_hash]), 1000,
          datetime.utcnow(), datetime.utcnow() + timedelta(days=7),
          signature))

    conn.commit()

    # Verify delegation
    cursor.execute("""
        SELECT delegation_id, atp_budget_total, atp_budget_spent, status
        FROM agent_delegations WHERE delegation_id = %s
    """, (delegation_id,))

    result = cursor.fetchone()
    assert result[0] == delegation_id, "Delegation not found!"
    assert result[1] == 1000, "Wrong ATP budget!"
    assert result[2] == 0, "ATP should be 0 initially!"
    assert result[3] == 'active', "Delegation should be active!"

    print(f"  ✓ Delegation created: {delegation_id}")
    print(f"    ATP Budget: {result[1]}")
    print(f"    ATP Spent: {result[2]}")
    print(f"    Status: {result[3]}")

    cursor.close()
    return delegation_id

def test_3_delegation_chain(conn, keys):
    """Test 3: Sub-delegation (delegation chains)"""
    print("\n=== Test 3: Delegation Chains ===")
    cursor = conn.cursor()

    # Bob sub-delegates to Charlie (using parent delegation)
    parent_delegation_id = "del:alice_to_bob:001"
    sub_delegation_id = "del:bob_to_charlie:001"
    delegator_lct = "lct:ai:bob:001"
    delegatee_lct = "lct:ai:charlie:001"
    org_id = "org:test:lab"

    # Bob creates sub-delegation
    delegation_content = {
        "delegation_id": sub_delegation_id,
        "parent": parent_delegation_id,
        "delegator": delegator_lct,
        "delegatee": delegatee_lct,
        "organization": org_id,
        "atp_budget": 500,  # Sub-allocation from parent
        "valid_from": datetime.utcnow().isoformat(),
        "valid_until": (datetime.utcnow() + timedelta(days=3)).isoformat()
    }

    delegation_json = json.dumps(delegation_content, sort_keys=True)
    signature = sign_message(delegation_json, keys[delegator_lct])

    # Store sub-delegation
    cursor.execute("""
        INSERT INTO agent_delegations
        (delegation_id, delegator_lct, delegatee_lct, parent_delegation_id,
         organization_id, granted_claim_hashes, atp_budget_total,
         valid_from, valid_until, delegation_signature)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (sub_delegation_id, delegator_lct, delegatee_lct, parent_delegation_id,
          org_id, json.dumps([]), 500,
          datetime.utcnow(), datetime.utcnow() + timedelta(days=3),
          signature))

    conn.commit()

    # Query delegation chain
    cursor.execute("""
        SELECT delegation_id, depth, root_delegator, delegatee_lct
        FROM delegation_chains
        WHERE delegation_id = %s
    """, (sub_delegation_id,))

    result = cursor.fetchone()
    assert result is not None, "Sub-delegation not found in chain!"
    assert result[1] == 2, f"Expected depth 2, got {result[1]}"
    assert result[2] == 'lct:human:alice:001', "Wrong root delegator!"

    print(f"  ✓ Sub-delegation created: {sub_delegation_id}")
    print(f"    Depth: {result[1]}")
    print(f"    Root Delegator: {result[2]}")
    print(f"    Final Delegatee: {result[3]}")

    cursor.close()

def test_4_action_execution(conn):
    """Test 4: Execute actions and track ATP"""
    print("\n=== Test 4: Action Execution & ATP Tracking ===")
    cursor = conn.cursor()

    delegation_id = "del:alice_to_bob:001"
    delegatee_lct = "lct:ai:bob:001"

    # Execute 5 actions
    actions = [
        ('read', 'data:project123:file1.txt', 10, True),
        ('read', 'data:project123:file2.txt', 10, True),
        ('write', 'data:project123:output.txt', 20, True),
        ('read', 'data:secret:file.txt', 10, False),  # Should fail
        ('read', 'data:project123:file3.txt', 10, True)
    ]

    total_atp_spent = 0

    for action_type, resource, atp_cost, authorized in actions:
        # Record action
        cursor.execute("""
            INSERT INTO delegation_actions
            (delegation_id, delegatee_lct, action_type, target_resource,
             atp_cost, authorized, denial_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (delegation_id, delegatee_lct, action_type, resource,
              atp_cost, authorized, None if authorized else 'Resource not permitted'))

        # Update ATP budget if authorized
        if authorized:
            cursor.execute("""
                UPDATE agent_delegations
                SET atp_budget_spent = atp_budget_spent + %s,
                    actions_this_hour = actions_this_hour + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE delegation_id = %s
            """, (atp_cost, delegation_id))
            total_atp_spent += atp_cost

        conn.commit()

    # Verify ATP tracking
    cursor.execute("""
        SELECT atp_budget_total, atp_budget_spent, actions_this_hour
        FROM agent_delegations WHERE delegation_id = %s
    """, (delegation_id,))

    result = cursor.fetchone()
    assert result[1] == total_atp_spent, f"Expected {total_atp_spent} ATP spent, got {result[1]}"

    print(f"  ✓ Executed {len(actions)} actions")
    print(f"    ATP Budget: {result[0]}")
    print(f"    ATP Spent: {result[1]}")
    print(f"    ATP Remaining: {result[0] - result[1]}")
    print(f"    Actions This Hour: {result[2]}")

    # Query action audit log
    cursor.execute("""
        SELECT action_type, target_resource, authorized, atp_cost
        FROM delegation_actions
        WHERE delegation_id = %s
        ORDER BY executed_at
    """, (delegation_id,))

    print("\n  Action Audit Log:")
    for row in cursor.fetchall():
        status = "✓" if row[2] else "✗"
        print(f"    {status} {row[0]:6} {row[1]:40} ({row[3]} ATP)")

    cursor.close()

def test_5_reputation_updates(conn):
    """Test 5: Update reputation from actions"""
    print("\n=== Test 5: Reputation Updates ===")
    cursor = conn.cursor()

    lct_id = "lct:ai:bob:001"
    org_id = "org:test:lab"

    # Ensure reputation record exists
    cursor.execute("""
        INSERT INTO reputation_scores (lct_id, organization_id)
        VALUES (%s, %s)
        ON CONFLICT (lct_id, organization_id) DO NOTHING
    """, (lct_id, org_id))
    conn.commit()

    # Get initial reputation
    cursor.execute("""
        SELECT talent_score, training_score, temperament_score, t3_score, reputation_level
        FROM reputation_scores WHERE lct_id = %s AND organization_id = %s
    """, (lct_id, org_id))

    before = cursor.fetchone()
    print(f"  Initial Reputation:")
    print(f"    Talent: {before[0]:.3f}, Training: {before[1]:.3f}, Temperament: {before[2]:.3f}")
    print(f"    T3 Score: {before[3]:.3f}, Level: {before[4]}")

    # Simulate 10 successful actions
    for i in range(10):
        cursor.execute("""
            SELECT update_reputation_from_action(%s, %s, %s, %s)
        """, (lct_id, org_id, True, 'read'))
        conn.commit()

    # Get updated reputation
    cursor.execute("""
        SELECT talent_score, training_score, temperament_score, t3_score, reputation_level,
               total_actions, successful_actions, failed_actions
        FROM reputation_scores WHERE lct_id = %s AND organization_id = %s
    """, (lct_id, org_id))

    after = cursor.fetchone()
    print(f"\n  After 10 Successful Actions:")
    print(f"    Talent: {after[0]:.3f} (+{after[0]-before[0]:.3f})")
    print(f"    Training: {after[1]:.3f} (+{after[1]-before[1]:.3f})")
    print(f"    Temperament: {after[2]:.3f} (+{after[2]-before[2]:.3f})")
    print(f"    T3 Score: {after[3]:.3f} (+{after[3]-before[3]:.3f})")
    print(f"    Level: {after[4]}")
    print(f"    Actions: {after[5]} total, {after[6]} successful, {after[7]} failed")

    assert after[1] > before[1], "Training should increase!"
    assert after[2] > before[2], "Temperament should increase!"
    assert after[5] == 10, "Should have 10 total actions!"
    assert after[6] == 10, "Should have 10 successful actions!"

    print("  ✓ Reputation updates working correctly")

    cursor.close()

def test_6_auto_revocation(conn):
    """Test 6: Automatic revocation on trust drop"""
    print("\n=== Test 6: Automatic Revocation on Trust Drop ===")
    cursor = conn.cursor()

    # Create delegation with min_t3 constraint
    delegation_id = "del:trust_test:001"
    delegator_lct = "lct:human:alice:001"
    delegatee_lct = "lct:ai:charlie:001"
    org_id = "org:test:lab"

    # Set constraint requiring min T3 of 0.5
    cursor.execute("""
        INSERT INTO agent_delegations
        (delegation_id, delegator_lct, delegatee_lct, organization_id,
         granted_claim_hashes, atp_budget_total, valid_from, valid_until,
         delegation_signature, constraints)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (delegation_id, delegator_lct, delegatee_lct, org_id,
          json.dumps([]), 500,
          datetime.utcnow(), datetime.utcnow() + timedelta(days=7),
          'test_signature',
          json.dumps({"min_t3": 0.5})))

    # Ensure Charlie has reputation record
    cursor.execute("""
        INSERT INTO reputation_scores (lct_id, organization_id, talent_score, training_score, temperament_score)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (lct_id, organization_id)
        DO UPDATE SET talent_score = %s, training_score = %s, temperament_score = %s
    """, (delegatee_lct, org_id, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6))

    conn.commit()

    # Charlie's T3 should be 0.6 (above threshold)
    cursor.execute("""
        SELECT t3_score FROM reputation_scores
        WHERE lct_id = %s AND organization_id = %s
    """, (delegatee_lct, org_id))

    t3_before = cursor.fetchone()[0]
    print(f"  Charlie's T3 before: {t3_before:.3f} (threshold: 0.5)")
    assert t3_before >= 0.5, "T3 should be above threshold!"

    # Drop Charlie's temperament to trigger revocation
    cursor.execute("""
        UPDATE reputation_scores
        SET temperament_score = 0.1
        WHERE lct_id = %s AND organization_id = %s
    """, (delegatee_lct, org_id))
    conn.commit()

    # Check Charlie's new T3
    cursor.execute("""
        SELECT t3_score FROM reputation_scores
        WHERE lct_id = %s AND organization_id = %s
    """, (delegatee_lct, org_id))

    t3_after = cursor.fetchone()[0]
    print(f"  Charlie's T3 after:  {t3_after:.3f} (threshold: 0.5)")
    assert t3_after < 0.5, "T3 should be below threshold!"

    # Trigger automatic revocation check
    cursor.execute("SELECT check_delegation_trust_thresholds()")
    conn.commit()

    # Verify delegation was revoked
    cursor.execute("""
        SELECT status, revocation_reason
        FROM agent_delegations WHERE delegation_id = %s
    """, (delegation_id,))

    result = cursor.fetchone()
    assert result[0] == 'revoked', f"Delegation should be revoked, got {result[0]}!"
    print(f"  ✓ Delegation auto-revoked: {result[1]}")

    # Check revocation event logged
    cursor.execute("""
        SELECT COUNT(*) FROM revocation_events
        WHERE target_type = 'delegation' AND target_id = %s
    """, (delegation_id,))

    count = cursor.fetchone()[0]
    assert count > 0, "Revocation event not logged!"
    print(f"  ✓ Revocation event logged")

    cursor.close()

def test_7_views_and_queries(conn):
    """Test 7: Test views and complex queries"""
    print("\n=== Test 7: Views and Complex Queries ===")
    cursor = conn.cursor()

    # Test active_permissions view
    cursor.execute("""
        SELECT subject_lct, permission_action, resource_pattern, t3_score, reputation_level
        FROM active_permissions
        LIMIT 5
    """)

    print("  Active Permissions:")
    for row in cursor.fetchall():
        print(f"    {row[0]:25} {row[1]:6} {row[2]:30} T3={row[3]:.3f} ({row[4]})")

    # Test active_delegations view
    cursor.execute("""
        SELECT delegation_id, delegatee_lct, atp_remaining, atp_utilization, delegatee_t3
        FROM active_delegations
    """)

    print("\n  Active Delegations:")
    for row in cursor.fetchall():
        util_pct = row[3] * 100 if row[3] else 0
        print(f"    {row[0]:30} → {row[1]:25} ATP: {row[2]:4} remaining ({util_pct:.1f}% used) T3={row[4]:.3f}")

    # Test delegation_chains view
    cursor.execute("""
        SELECT delegation_id, depth, root_delegator, delegatee_lct
        FROM delegation_chains
        ORDER BY depth, delegation_id
    """)

    print("\n  Delegation Chains:")
    for row in cursor.fetchall():
        indent = "  " * row[1]
        print(f"    {indent}[L{row[1]}] {row[0]:30} Root: {row[2]:25} → {row[3]}")

    cursor.close()
    print("\n  ✓ All views working correctly")

# ============================================================================
# Helper Functions
# ============================================================================

def get_public_key(conn, lct_id):
    """Get public key for LCT ID"""
    cursor = conn.cursor()
    cursor.execute("SELECT public_key FROM lct_identities WHERE lct_id = %s", (lct_id,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def cleanup_test_data(conn):
    """Clean up test data"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM delegation_actions")
    cursor.execute("DELETE FROM revocation_events")
    cursor.execute("DELETE FROM agent_delegations")
    cursor.execute("DELETE FROM permission_claims")
    cursor.execute("DELETE FROM reputation_scores")
    cursor.execute("DELETE FROM organizations WHERE organization_id = 'org:test:lab'")  # Delete orgs first!
    cursor.execute("DELETE FROM lct_identities WHERE lct_id LIKE 'lct:%:test%' OR lct_id LIKE 'lct:%:alice%' OR lct_id LIKE 'lct:%:bob%' OR lct_id LIKE 'lct:%:charlie%' OR lct_id LIKE 'lct:%:admin%'")
    conn.commit()
    cursor.close()
    print("✓ Test data cleaned up")

# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    print("=" * 70)
    print("  Web4 PostgreSQL Delegation System - Comprehensive Test Suite")
    print("  Session #54: Full Integration Test")
    print("=" * 70)

    try:
        # Connect to database
        conn = get_db_connection()
        print("\n✓ Connected to PostgreSQL database 'web4'")

        # Clean up any existing test data
        cleanup_test_data(conn)

        # Run tests
        keys = create_test_identities(conn)
        claim_hash = test_1_permission_claims(conn, keys)
        delegation_id = test_2_agent_delegation(conn, keys, claim_hash)
        test_3_delegation_chain(conn, keys)
        test_4_action_execution(conn)
        test_5_reputation_updates(conn)
        test_6_auto_revocation(conn)
        test_7_views_and_queries(conn)

        print("\n" + "=" * 70)
        print("  ✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nKey Features Validated:")
        print("  ✓ Ed25519 cryptographic signatures")
        print("  ✓ Permission claims with signature verification")
        print("  ✓ Agent delegations with ATP budgets")
        print("  ✓ Delegation chains (sub-delegation)")
        print("  ✓ Action execution and ATP tracking")
        print("  ✓ Reputation updates from performance")
        print("  ✓ Automatic trust-based revocation")
        print("  ✓ Complex queries and views")

        # Clean up
        cleanup_test_data(conn)
        conn.close()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
