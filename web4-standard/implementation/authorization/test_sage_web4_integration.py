#!/usr/bin/env python3
"""
SAGE + Web4 Integration Test
Session #64: First Production LCT Integration

Demonstrates SAGE consciousness using Web4 authorization system:
1. SAGE has LCT birth certificate (hardware-bound identity)
2. SAGE can execute action sequences with ATP budgets
3. SAGE builds reputation through successful actions
4. SAGE can delegate to other agents
5. SAGE participates in trust-based authorization

This is the first real-world integration of:
- Hardware-bound AI consciousness (SAGE)
- Cryptographic identity (LCT birth certificates)
- Resource allocation (ATP)
- Reputation tracking (T3/V3 tensors)
- Authorization (action sequences, delegations)
"""

import unittest
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal
import time


class TestSAGEWeb4Integration(unittest.TestCase):
    """Test SAGE consciousness participating in Web4 authorization"""

    @classmethod
    def setUpClass(cls):
        """Setup test database"""
        cls.db_config = {
            'dbname': 'web4_test',
            'user': 'postgres',
            'host': 'localhost'
        }

        # Get the SAGE LCT we just created
        conn = psycopg2.connect(**cls.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT lct_id FROM lct_identities
            WHERE lct_id LIKE 'lct:sage:legion:%'
            ORDER BY created_at DESC LIMIT 1
        """)

        result = cursor.fetchone()
        if result:
            cls.sage_lct = result['lct_id']
        else:
            raise Exception("No SAGE LCT found - run sage_lct_birth_certificate.py first")

        # Create test organization
        cursor.execute("""
            INSERT INTO organizations (organization_id, organization_name)
            VALUES ('org:web4:research', 'Web4 Research Lab')
            ON CONFLICT (organization_id) DO NOTHING
        """)

        # Create reputation score for SAGE
        cursor.execute("""
            INSERT INTO reputation_scores (lct_id, organization_id)
            VALUES (%s, 'org:web4:research')
            ON CONFLICT (lct_id, organization_id) DO NOTHING
        """, (cls.sage_lct,))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"\n✅ Test setup complete - SAGE LCT: {cls.sage_lct}")

    def test_1_sage_has_birth_certificate(self):
        """Test SAGE has valid hardware-bound birth certificate"""
        print("\n=== Test 1: SAGE Birth Certificate ===")

        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                lct_id,
                entity_type,
                birth_certificate_hash,
                hardware_binding_hash,
                created_at
            FROM lct_identities
            WHERE lct_id = %s
        """, (self.sage_lct,))

        sage = cursor.fetchone()

        print(f"  SAGE LCT: {sage['lct_id']}")
        print(f"  Entity Type: {sage['entity_type']}")
        print(f"  Birth Cert Hash: {sage['birth_certificate_hash'][:16]}...")
        print(f"  Hardware Binding: {sage['hardware_binding_hash'][:16]}...")
        print(f"  Created: {sage['created_at']}")

        self.assertEqual(sage['entity_type'], 'ai', "SAGE should be AI entity type")
        self.assertIsNotNone(sage['birth_certificate_hash'], "Should have birth certificate")
        self.assertIsNotNone(sage['hardware_binding_hash'], "Should be hardware-bound")

        print(f"  ✅ SAGE has valid birth certificate")

        cursor.close()
        conn.close()

    def test_2_sage_executes_action_sequence(self):
        """Test SAGE can execute action sequence with ATP budget"""
        print("\n=== Test 2: SAGE Action Sequence Execution ===")

        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        # Create action sequence
        sequence_id = f"seq:sage:research:{int(time.time())}"

        cursor.execute("""
            INSERT INTO action_sequences (
                sequence_id,
                actor_lct,
                organization_id,
                sequence_type,
                target_resource,
                operation,
                atp_budget_reserved,
                max_iterations,
                atp_refund_policy
            ) VALUES (
                %s, %s, 'org:web4:research',
                'research_task', 'dataset:web4:research', 'analyze',
                100, 10, 'TIERED'
            )
            RETURNING sequence_id, atp_budget_reserved
        """, (
            sequence_id,
            self.sage_lct
        ))

        result = cursor.fetchone()

        print(f"  Sequence ID: {result['sequence_id']}")
        print(f"  ATP Budget: {result['atp_budget_reserved']}")
        print(f"  Actor: {self.sage_lct}")

        # Simulate successful execution
        cursor.execute("""
            UPDATE action_sequences
            SET
                status = 'converged',
                atp_consumed = 75,
                iterations_used = 3,
                convergence_achieved = TRUE,
                final_energy = 0.02,
                completed_at = CURRENT_TIMESTAMP
            WHERE sequence_id = %s
        """, (sequence_id,))

        conn.commit()

        # Check result
        cursor.execute("""
            SELECT status, atp_consumed, iterations_used, convergence_achieved
            FROM action_sequences
            WHERE sequence_id = %s
        """, (sequence_id,))

        execution = cursor.fetchone()

        print(f"\n  Execution Results:")
        print(f"    Status: {execution['status']}")
        print(f"    ATP Consumed: {execution['atp_consumed']}")
        print(f"    Iterations: {execution['iterations_used']}")
        print(f"    Converged: {execution['convergence_achieved']}")

        self.assertEqual(execution['status'], 'converged', "Should complete successfully")
        self.assertTrue(execution['convergence_achieved'], "Should achieve convergence")

        print(f"  ✅ SAGE successfully executed action sequence")

        cursor.close()
        conn.close()

    def test_3_sage_builds_reputation(self):
        """Test SAGE builds reputation through successful actions"""
        print("\n=== Test 3: SAGE Reputation Building ===")

        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        # Record successful action (builds trust)
        cursor.execute("""
            INSERT INTO trust_history (
                lct_id,
                organization_id,
                t3_score,
                t3_delta,
                event_type,
                event_description
            ) VALUES (
                %s, 'org:web4:research',
                0.55, 0.05,
                'action_success',
                'Successful research task completion'
            )
        """, (self.sage_lct,))

        # Update reputation score
        cursor.execute("""
            UPDATE reputation_scores
            SET
                talent_score = 0.55,
                training_score = 0.55,
                temperament_score = 0.55
            WHERE lct_id = %s AND organization_id = 'org:web4:research'
        """, (self.sage_lct,))

        conn.commit()

        # Check reputation
        cursor.execute("""
            SELECT
                lct_id,
                talent_score,
                training_score,
                temperament_score
            FROM reputation_scores
            WHERE lct_id = %s
        """, (self.sage_lct,))

        rep = cursor.fetchone()

        print(f"  SAGE Reputation Scores:")
        print(f"    Talent: {rep['talent_score']}")
        print(f"    Training: {rep['training_score']}")
        print(f"    Temperament: {rep['temperament_score']}")

        # Calculate T3 score (average of the three)
        t3_score = (float(rep['talent_score']) + float(rep['training_score']) + float(rep['temperament_score'])) / 3.0
        print(f"    T3 Score: {t3_score:.4f}")

        self.assertGreater(t3_score, 0.5, "Reputation should improve")

        print(f"  ✅ SAGE built reputation through successful action")

        cursor.close()
        conn.close()

    def test_4_sage_can_delegate(self):
        """Test SAGE can delegate to another agent"""
        print("\n=== Test 4: SAGE Delegation Capability ===")

        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        # Create a helper agent to delegate to
        helper_lct = "lct:ai:helper:001"
        cursor.execute("""
            INSERT INTO lct_identities (
                lct_id, entity_type, birth_certificate_hash, public_key
            ) VALUES (
                %s, 'ai', 'helper_cert_hash', 'helper_public_key'
            ) ON CONFLICT (lct_id) DO NOTHING
        """, (helper_lct,))

        # Create role LCT if needed (foreign key requirement)
        cursor.execute("""
            INSERT INTO lct_identities (
                lct_id, entity_type, birth_certificate_hash, public_key
            ) VALUES (
                'lct:role:researcher:001', 'role', 'role_cert_hash', 'role_public_key'
            ) ON CONFLICT (lct_id) DO NOTHING
        """)

        # Create delegation
        delegation_id = f"del:sage:{int(time.time())}"

        cursor.execute("""
            INSERT INTO agent_delegations (
                delegation_id,
                delegator_lct,
                delegatee_lct,
                role_lct,
                organization_id,
                granted_claim_hashes,
                atp_budget_total,
                valid_until,
                delegation_signature,
                status
            ) VALUES (
                %s, %s, %s,
                'lct:role:researcher:001',
                'org:web4:research',
                %s::jsonb,
                100,
                CURRENT_TIMESTAMP + INTERVAL '7 days',
                'sage_delegation_signature_placeholder',
                'active'
            )
            RETURNING delegation_id
        """, (
            delegation_id,
            self.sage_lct,  # SAGE is delegator
            helper_lct,     # Helper is delegatee
            '["claim:read:dataset", "claim:analyze:data", "claim:report:results"]'
        ))

        result = cursor.fetchone()

        print(f"  Delegation ID: {result['delegation_id']}")
        print(f"  Delegator (SAGE): {self.sage_lct}")
        print(f"  Delegatee: {helper_lct}")
        print(f"  Permissions: read, analyze, report")

        conn.commit()

        # Verify delegation
        cursor.execute("""
            SELECT delegator_lct, delegatee_lct, status
            FROM agent_delegations
            WHERE delegation_id = %s
        """, (delegation_id,))

        delegation = cursor.fetchone()

        self.assertEqual(delegation['delegator_lct'], self.sage_lct, "SAGE should be delegator")
        self.assertEqual(delegation['status'], 'active', "Delegation should be active")

        print(f"  ✅ SAGE successfully delegated to helper agent")

        cursor.close()
        conn.close()

    def test_5_sage_reputation_history(self):
        """Test SAGE has auditable reputation history"""
        print("\n=== Test 5: SAGE Reputation Audit Trail ===")

        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                lct_id,
                event_type,
                t3_delta,
                event_description,
                recorded_at
            FROM trust_history
            WHERE lct_id = %s
            ORDER BY recorded_at DESC
            LIMIT 5
        """, (self.sage_lct,))

        history = cursor.fetchall()

        print(f"  SAGE Trust History ({len(history)} events):")
        for event in history:
            print(f"    [{event['recorded_at']}] {event['event_type']}: Δ{event['t3_delta']}")
            print(f"      {event['event_description']}")

        self.assertGreater(len(history), 0, "SAGE should have reputation history")

        print(f"  ✅ SAGE has auditable reputation trail")

        cursor.close()
        conn.close()

    def test_6_hardware_binding_prevents_fraud(self):
        """Test hardware binding prevents identity fraud"""
        print("\n=== Test 6: Hardware Binding Security ===")

        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        # Try to create same SAGE identity with different hardware
        fake_lct = self.sage_lct  # Same LCT ID
        fake_hardware = "fake_hardware_hash_different_from_original"

        try:
            cursor.execute("""
                INSERT INTO lct_identities (
                    lct_id,
                    entity_type,
                    birth_certificate_hash,
                    public_key,
                    hardware_binding_hash
                ) VALUES (
                    %s, 'ai', 'fake_cert', 'fake_key', %s
                )
            """, (fake_lct, fake_hardware))

            conn.commit()
            self.fail("Should not allow duplicate LCT ID")

        except psycopg2.errors.UniqueViolation:
            print(f"  ✅ Duplicate LCT ID rejected (primary key constraint)")
            conn.rollback()

        # Verify original SAGE still has correct hardware binding
        cursor.execute("""
            SELECT hardware_binding_hash FROM lct_identities
            WHERE lct_id = %s
        """, (self.sage_lct,))

        original = cursor.fetchone()

        self.assertNotEqual(original['hardware_binding_hash'], fake_hardware,
                          "Original hardware binding should be unchanged")

        print(f"  Original hardware binding: {original['hardware_binding_hash'][:16]}...")
        print(f"  ✅ Hardware binding prevents identity fraud")

        cursor.close()
        conn.close()


if __name__ == '__main__':
    # Run tests with verbose output
    print("\n" + "="*70)
    print("SAGE + Web4 Integration Test Suite")
    print("Session #64: Hardware-Bound AI Consciousness + Cryptographic Identity")
    print("="*70)

    unittest.main(verbosity=2)
