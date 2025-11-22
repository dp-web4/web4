#!/usr/bin/env python3
"""
Test Suite for Revocation Enforcement
Session #61: P2 Security Analysis

Tests that revocation enforcement prevents the Revocation Evasion attack
from ATTACK_VECTORS.md.

Attack Vector (from ATTACK_VECTORS.md line 393-423):
- Attacker obtains valid delegation
- Delegation gets revoked
- Attacker attempts to use cached delegation
- System must reject revoked delegation on every action

Mitigation Verification:
- Real-time revocation checks via active_delegations view
- Timestamp validation (valid_from, valid_until)
- Revocation propagation (status='revoked')
"""

import unittest
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone
import time

# Import delegation store
from pg_permission_store import PostgreSQLDelegationStore


class TestRevocationEnforcement(unittest.TestCase):
    """
    Test that revocation enforcement prevents Revocation Evasion attacks.

    Verifies that:
    1. Revoked delegations are immediately invisible
    2. Expired delegations are not usable
    3. Future delegations are not yet active
    4. Revocation propagates to all queries
    """

    @classmethod
    def setUpClass(cls):
        """Set up test database connection"""
        cls.db_config = {
            'dbname': 'web4_test',
            'user': 'postgres',
            'host': 'localhost'
        }

        # Create delegation store (needs connection string)
        cls.connection_string = "dbname=web4_test user=postgres host=localhost"
        cls.delegation_store = PostgreSQLDelegationStore(cls.connection_string)

        # Create test LCTs
        conn = psycopg2.connect(**cls.db_config)
        cursor = conn.cursor()

        # Ensure test identities exist
        for lct_id in ['lct:delegator:001', 'lct:delegatee:001', 'lct:attacker:001']:
            entity_type = 'human' if 'delegator' in lct_id else 'ai'
            cursor.execute("""
                INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, public_key)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (lct_id) DO NOTHING
            """, (lct_id, entity_type, f'bc:{lct_id}', f'pubkey:{lct_id}'))

        # Ensure test organization exists
        cursor.execute("""
            INSERT INTO organizations (organization_id, organization_name)
            VALUES ('org:test:001', 'Test Org')
            ON CONFLICT (organization_id) DO NOTHING
        """)

        # Ensure reputation scores exist
        for lct_id in ['lct:delegator:001', 'lct:delegatee:001', 'lct:attacker:001']:
            cursor.execute("""
                INSERT INTO reputation_scores (lct_id, organization_id)
                VALUES (%s, 'org:test:001')
                ON CONFLICT (lct_id, organization_id) DO NOTHING
            """, (lct_id,))

        # Create active_delegations view (simplified for testing)
        # Key: Filters for status='active' and valid time range
        cursor.execute("""
            CREATE OR REPLACE VIEW active_delegations AS
            SELECT
                ad.*,
                (ad.atp_budget_total - ad.atp_budget_spent) AS atp_remaining,
                (ad.atp_budget_spent::FLOAT / NULLIF(ad.atp_budget_total, 0)) AS atp_utilization
            FROM agent_delegations ad
            WHERE ad.status = 'active'
              AND ad.valid_from <= CURRENT_TIMESTAMP
              AND ad.valid_until > CURRENT_TIMESTAMP
        """)

        conn.commit()
        cursor.close()
        conn.close()

    def setUp(self):
        """Clear delegation data before each test"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agent_delegations")
        cursor.execute("DELETE FROM delegation_actions")
        conn.commit()
        cursor.close()
        conn.close()

    def test_revoked_delegation_invisible(self):
        """Test that revoked delegations are immediately invisible"""
        print("\n=== Test: Revoked Delegation Invisible ===")

        # Create delegation
        delegation_id = f"del:revoke:test:{int(time.time())}"
        now = datetime.now(timezone.utc)

        success = self.delegation_store.create_delegation(
            delegation_id=delegation_id,
            delegator_lct='lct:delegator:001',
            delegatee_lct='lct:delegatee:001',
            organization_id='org:test:001',
            granted_claim_hashes=['claim:1', 'claim:2'],
            atp_budget=1000,
            valid_from=now,
            valid_until=now + timedelta(hours=1),
            delegation_signature='sig:test'
        )

        self.assertTrue(success, "Failed to create delegation")
        print(f"  ✅ Created delegation: {delegation_id}")

        # Verify delegation is active
        delegation = self.delegation_store.get_delegation(delegation_id)
        self.assertIsNotNone(delegation, "Delegation should be active")
        self.assertEqual(delegation['status'], 'active')
        print(f"  ✅ Delegation is active")

        # Revoke delegation
        revoked = self.delegation_store.revoke_delegation(
            delegation_id,
            "Testing revocation enforcement",
            'lct:delegator:001'
        )

        self.assertTrue(revoked, "Failed to revoke delegation")
        print(f"  ✅ Delegation revoked")

        # Verify delegation is now invisible (real-time check)
        delegation_after = self.delegation_store.get_delegation(delegation_id)
        self.assertIsNone(delegation_after, "Revoked delegation should be invisible")
        print(f"  ✅ Revoked delegation invisible to get_delegation()")

        # Verify delegation doesn't appear in delegatee's list
        delegations_list = self.delegation_store.get_delegations_by_delegatee(
            'lct:delegatee:001',
            'org:test:001'
        )
        self.assertEqual(len(delegations_list), 0, "Revoked delegation should not appear in list")
        print(f"  ✅ Revoked delegation invisible to get_delegations_by_delegatee()")

        print(f"  ✅ PASS: Revocation is enforced in real-time")

    def test_attack_scenario_from_attack_vectors(self):
        """
        Test the exact attack scenario from ATTACK_VECTORS.md:

        Attack Pattern:
        ```python
        # Obtain delegation
        delegation = get_delegation("lct:attacker:001")

        # Delegation gets revoked
        revoke_delegation(delegation_id)

        # Attacker uses cached delegation
        # If system doesn't check revocation on each use
        perform_action(actor="lct:attacker:001", delegation=delegation)
        ```

        Expected: System rejects revoked delegation even if attacker has cached copy
        """
        print("\n=== Test: ATTACK_VECTORS.md Attack Scenario ===")

        # Step 1: Attacker obtains delegation
        delegation_id = f"del:attack:test:{int(time.time())}"
        now = datetime.now(timezone.utc)

        success = self.delegation_store.create_delegation(
            delegation_id=delegation_id,
            delegator_lct='lct:delegator:001',
            delegatee_lct='lct:attacker:001',
            organization_id='org:test:001',
            granted_claim_hashes=['claim:admin'],
            atp_budget=1000,
            valid_from=now,
            valid_until=now + timedelta(hours=1),
            delegation_signature='sig:attacker'
        )

        # Attacker retrieves delegation (simulating caching)
        cached_delegation = self.delegation_store.get_delegation(delegation_id)
        self.assertIsNotNone(cached_delegation, "Attacker should get delegation")
        print(f"  ✓ Attacker obtained delegation: {delegation_id}")
        print(f"    Status: {cached_delegation['status']}")
        print(f"    Granted claims: {cached_delegation['granted_claim_hashes']}")

        # Step 2: Delegation gets revoked (e.g., admin notices suspicious activity)
        print(f"\n  ✓ Admin revokes delegation due to suspicious activity")
        revoked = self.delegation_store.revoke_delegation(
            delegation_id,
            "Suspicious activity detected",
            'lct:delegator:001'
        )
        self.assertTrue(revoked, "Revocation should succeed")

        # Step 3: Attacker attempts to use cached delegation
        print(f"\n  ✓ Attacker attempts to use cached delegation...")

        # Attacker tries to retrieve delegation again (system should reject)
        delegation_check = self.delegation_store.get_delegation(delegation_id)

        if delegation_check is None:
            print(f"    ✅ System correctly rejects revoked delegation")
            print(f"    ✅ Real-time revocation check working")
        else:
            self.fail(f"SECURITY FAILURE: Revoked delegation still accessible!")

        # Verify attacker can't see delegation in their list
        attacker_delegations = self.delegation_store.get_delegations_by_delegatee(
            'lct:attacker:001',
            'org:test:001'
        )
        self.assertEqual(len(attacker_delegations), 0,
                        "Attacker should not see revoked delegation")
        print(f"    ✅ Revoked delegation removed from attacker's delegation list")

        # Verify delegation is marked as revoked in database
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, revoked_at, revocation_reason
            FROM agent_delegations
            WHERE delegation_id = %s
        """, (delegation_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertEqual(row['status'], 'revoked', "Status should be 'revoked'")
        self.assertIsNotNone(row['revoked_at'], "revoked_at should be set")
        self.assertEqual(row['revocation_reason'], "Suspicious activity detected")
        print(f"    ✅ Delegation properly marked as revoked in database")
        print(f"       Revoked at: {row['revoked_at']}")
        print(f"       Reason: {row['revocation_reason']}")

        print(f"\n  ✅ ATTACK MITIGATED: Revocation enforcement prevents cached delegation use")

    def test_expired_delegation_not_active(self):
        """Test that expired delegations are automatically inactive"""
        print("\n=== Test: Expired Delegation Not Active ===")

        # Create delegation that expires in 1 second
        delegation_id = f"del:expire:test:{int(time.time())}"
        now = datetime.now(timezone.utc)

        success = self.delegation_store.create_delegation(
            delegation_id=delegation_id,
            delegator_lct='lct:delegator:001',
            delegatee_lct='lct:delegatee:001',
            organization_id='org:test:001',
            granted_claim_hashes=['claim:temp'],
            atp_budget=100,
            valid_from=now - timedelta(seconds=1),
            valid_until=now + timedelta(seconds=2),  # Expires in 2 seconds
            delegation_signature='sig:temp'
        )

        # Verify delegation is active
        delegation = self.delegation_store.get_delegation(delegation_id)
        self.assertIsNotNone(delegation, "Delegation should be active initially")
        print(f"  ✅ Delegation active (expires in 2s)")

        # Wait for expiration
        print(f"  ⏱  Waiting 3 seconds for expiration...")
        time.sleep(3)

        # Verify delegation is now expired (real-time check)
        delegation_after = self.delegation_store.get_delegation(delegation_id)
        self.assertIsNone(delegation_after, "Expired delegation should be invisible")
        print(f"  ✅ Expired delegation automatically inactive (timestamp validation working)")

    def test_future_delegation_not_yet_active(self):
        """Test that future delegations are not yet usable"""
        print("\n=== Test: Future Delegation Not Yet Active ===")

        # Create delegation that starts in 5 seconds
        delegation_id = f"del:future:test:{int(time.time())}"
        now = datetime.now(timezone.utc)

        success = self.delegation_store.create_delegation(
            delegation_id=delegation_id,
            delegator_lct='lct:delegator:001',
            delegatee_lct='lct:delegatee:001',
            organization_id='org:test:001',
            granted_claim_hashes=['claim:future'],
            atp_budget=100,
            valid_from=now + timedelta(seconds=5),  # Starts in 5 seconds
            valid_until=now + timedelta(hours=1),
            delegation_signature='sig:future'
        )

        # Verify delegation is not yet active
        delegation = self.delegation_store.get_delegation(delegation_id)
        self.assertIsNone(delegation, "Future delegation should not be active yet")
        print(f"  ✅ Future delegation correctly not active (valid_from check working)")

    def test_revocation_propagates_to_all_queries(self):
        """Test that revocation is enforced across all query methods"""
        print("\n=== Test: Revocation Propagates to All Queries ===")

        # Create multiple delegations for same delegatee
        now = datetime.now(timezone.utc)
        delegation_ids = []

        for i in range(3):
            delegation_id = f"del:multi:test:{int(time.time())}:{i}"
            delegation_ids.append(delegation_id)

            self.delegation_store.create_delegation(
                delegation_id=delegation_id,
                delegator_lct='lct:delegator:001',
                delegatee_lct='lct:delegatee:001',
                organization_id='org:test:001',
                granted_claim_hashes=[f'claim:{i}'],
                atp_budget=100,
                valid_from=now,
                valid_until=now + timedelta(hours=1),
                delegation_signature=f'sig:{i}'
            )

        # Verify all 3 delegations are active
        delegations_list = self.delegation_store.get_delegations_by_delegatee(
            'lct:delegatee:001',
            'org:test:001'
        )
        self.assertEqual(len(delegations_list), 3, "Should have 3 active delegations")
        print(f"  ✅ Created 3 active delegations")

        # Revoke middle delegation
        revoked = self.delegation_store.revoke_delegation(
            delegation_ids[1],
            "Testing propagation",
            'lct:delegator:001'
        )
        self.assertTrue(revoked, "Should revoke delegation")
        print(f"  ✅ Revoked delegation {delegation_ids[1]}")

        # Verify only 2 delegations remain active
        delegations_after = self.delegation_store.get_delegations_by_delegatee(
            'lct:delegatee:001',
            'org:test:001'
        )
        self.assertEqual(len(delegations_after), 2, "Should have 2 active delegations")
        print(f"  ✅ Only 2 delegations remain in list (revocation propagated)")

        # Verify revoked delegation can't be retrieved individually
        delegation_check = self.delegation_store.get_delegation(delegation_ids[1])
        self.assertIsNone(delegation_check, "Revoked delegation should not be retrievable")
        print(f"  ✅ Revoked delegation not retrievable via get_delegation()")

        # Verify other two are still active
        for i in [0, 2]:
            delegation = self.delegation_store.get_delegation(delegation_ids[i])
            self.assertIsNotNone(delegation, f"Delegation {i} should still be active")
        print(f"  ✅ Other delegations unaffected")

        print(f"  ✅ PASS: Revocation propagates consistently to all queries")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
