#!/usr/bin/env python3
"""
Nonlinear Trust Scaling Test Suite
Session #60: P2 Security Fix - Score Clamping Exploitation Prevention

Tests:
- Nonlinear penalty scaling at different trust levels
- Reward behavior (should remain linear)
- Attack mitigation (max trust with repeated failures)
- Comparison with old linear behavior
"""

import unittest
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal
import hashlib

# Test database configuration
TEST_DB_CONFIG = {
    'dbname': 'web4',
    'user': 'postgres',
    'host': 'localhost'
}


class NonlinearTrustScalingTestBase(unittest.TestCase):
    """Base class for nonlinear trust scaling tests"""

    @classmethod
    def setUpClass(cls):
        """Create test LCT and organization"""
        conn = psycopg2.connect(**TEST_DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            # Create test LCT
            cursor.execute("""
                INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, public_key)
                VALUES ('lct:test:scaling', 'human', %s, %s)
                ON CONFLICT (lct_id) DO NOTHING
            """, (
                hashlib.sha256(b'test_scaling').hexdigest(),
                hashlib.sha256(b'scaling_pubkey').hexdigest()
            ))

            # Create test organization
            cursor.execute("""
                INSERT INTO organizations (organization_id, organization_name, admin_lct_id)
                VALUES ('org:test:scaling', 'Scaling Test Org', 'lct:test:scaling')
                ON CONFLICT (organization_id) DO NOTHING
            """)

            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def setUp(self):
        """Set up for each test"""
        self.conn = psycopg2.connect(**TEST_DB_CONFIG, cursor_factory=RealDictCursor)
        self.cursor = self.conn.cursor()

    def tearDown(self):
        """Clean up after each test"""
        self.cursor.close()
        self.conn.close()

    def _create_reputation_score(self, lct_id, org_id, talent=0.5, training=0.5, temperament=0.5):
        """Helper to create/update reputation score"""
        self.cursor.execute("""
            INSERT INTO reputation_scores
            (lct_id, organization_id, talent_score, training_score, temperament_score, total_actions)
            VALUES (%s, %s, %s, %s, %s, 0)
            ON CONFLICT (lct_id, organization_id)
            DO UPDATE SET
                talent_score = EXCLUDED.talent_score,
                training_score = EXCLUDED.training_score,
                temperament_score = EXCLUDED.temperament_score
        """, (lct_id, org_id, talent, training, temperament))
        self.conn.commit()

    def _get_reputation_score(self, lct_id, org_id):
        """Helper to get current reputation score"""
        self.cursor.execute("""
            SELECT talent_score, training_score, temperament_score
            FROM reputation_scores
            WHERE lct_id = %s AND organization_id = %s
        """, (lct_id, org_id))
        return self.cursor.fetchone()

    def _apply_delta(self, lct_id, org_id, talent_delta, training_delta, temperament_delta):
        """Helper to apply delta using the new scaling function"""
        self.cursor.execute("""
            UPDATE reputation_scores
            SET talent_score = apply_scaled_trust_delta(talent_score, %s),
                training_score = apply_scaled_trust_delta(training_score, %s),
                temperament_score = apply_scaled_trust_delta(temperament_score, %s)
            WHERE lct_id = %s AND organization_id = %s
        """, (talent_delta, training_delta, temperament_delta, lct_id, org_id))
        self.conn.commit()


class TestNonlinearPenaltyScaling(NonlinearTrustScalingTestBase):
    """Test nonlinear penalty scaling at different trust levels"""

    def test_penalty_at_max_trust(self):
        """Test that penalty at max trust (1.0) is 10x larger"""
        lct_id = 'lct:test:scaling'
        org_id = 'org:test:scaling'

        # Set score to 1.0 (max trust)
        self._create_reputation_score(lct_id, org_id, talent=1.0, training=1.0, temperament=1.0)

        # Apply small penalty (-0.001)
        self._apply_delta(lct_id, org_id, Decimal('-0.001'), Decimal('-0.001'), Decimal('-0.001'))

        # Get new score
        result = self._get_reputation_score(lct_id, org_id)

        # Expected: -0.001 * 10.0 = -0.01
        # new_score = 1.0 - 0.01 = 0.99
        self.assertAlmostEqual(float(result['talent_score']), 0.99, places=4)
        self.assertAlmostEqual(float(result['training_score']), 0.99, places=4)
        self.assertAlmostEqual(float(result['temperament_score']), 0.99, places=4)

    def test_penalty_at_mid_trust(self):
        """Test that penalty at mid trust (0.5) is ~3.25x larger"""
        lct_id = 'lct:test:scaling'
        org_id = 'org:test:scaling'

        # Set score to 0.5 (mid trust)
        self._create_reputation_score(lct_id, org_id, talent=0.5, training=0.5, temperament=0.5)

        # Apply small penalty (-0.001)
        self._apply_delta(lct_id, org_id, Decimal('-0.001'), Decimal('-0.001'), Decimal('-0.001'))

        # Get new score
        result = self._get_reputation_score(lct_id, org_id)

        # Expected: scaling_factor = 1.0 + (0.5^2) * 9.0 = 1.0 + 0.25 * 9.0 = 3.25
        # scaled_delta = -0.001 * 3.25 = -0.00325
        # new_score = 0.5 - 0.00325 = 0.49675
        # Note: PostgreSQL NUMERIC precision may differ slightly
        self.assertAlmostEqual(float(result['talent_score']), 0.497, places=3)
        self.assertAlmostEqual(float(result['training_score']), 0.497, places=3)
        self.assertAlmostEqual(float(result['temperament_score']), 0.497, places=3)

    def test_penalty_at_low_trust(self):
        """Test that penalty at low trust (0.1) is minimal (~1.09x)"""
        lct_id = 'lct:test:scaling'
        org_id = 'org:test:scaling'

        # Set score to 0.1 (low trust)
        self._create_reputation_score(lct_id, org_id, talent=0.1, training=0.1, temperament=0.1)

        # Apply small penalty (-0.001)
        self._apply_delta(lct_id, org_id, Decimal('-0.001'), Decimal('-0.001'), Decimal('-0.001'))

        # Get new score
        result = self._get_reputation_score(lct_id, org_id)

        # Expected: scaling_factor = 1.0 + (0.1^2) * 9.0 = 1.0 + 0.01 * 9.0 = 1.09
        # scaled_delta = -0.001 * 1.09 = -0.00109
        # new_score = 0.1 - 0.00109 = 0.09891
        # Note: PostgreSQL NUMERIC precision may differ slightly
        self.assertAlmostEqual(float(result['talent_score']), 0.099, places=3)
        self.assertAlmostEqual(float(result['training_score']), 0.099, places=3)
        self.assertAlmostEqual(float(result['temperament_score']), 0.099, places=3)


class TestRewardBehavior(NonlinearTrustScalingTestBase):
    """Test that rewards remain linear (no scaling)"""

    def test_reward_at_max_trust(self):
        """Test that reward at max trust is linear (no amplification)"""
        lct_id = 'lct:test:scaling'
        org_id = 'org:test:scaling'

        # Set score to 1.0 (max trust, at ceiling)
        self._create_reputation_score(lct_id, org_id, talent=1.0, training=1.0, temperament=1.0)

        # Apply reward (+0.001) - should be clamped at 1.0
        self._apply_delta(lct_id, org_id, Decimal('0.001'), Decimal('0.001'), Decimal('0.001'))

        # Get new score
        result = self._get_reputation_score(lct_id, org_id)

        # Expected: 1.0 + 0.001 = 1.001, clamped to 1.0
        self.assertAlmostEqual(float(result['talent_score']), 1.0, places=4)
        self.assertAlmostEqual(float(result['training_score']), 1.0, places=4)
        self.assertAlmostEqual(float(result['temperament_score']), 1.0, places=4)

    def test_reward_at_mid_trust(self):
        """Test that reward at mid trust is linear (1:1)"""
        lct_id = 'lct:test:scaling'
        org_id = 'org:test:scaling'

        # Set score to 0.5 (mid trust)
        self._create_reputation_score(lct_id, org_id, talent=0.5, training=0.5, temperament=0.5)

        # Apply reward (+0.001)
        self._apply_delta(lct_id, org_id, Decimal('0.001'), Decimal('0.001'), Decimal('0.001'))

        # Get new score
        result = self._get_reputation_score(lct_id, org_id)

        # Expected: 0.5 + 0.001 = 0.501 (no scaling for rewards)
        self.assertAlmostEqual(float(result['talent_score']), 0.501, places=4)
        self.assertAlmostEqual(float(result['training_score']), 0.501, places=4)
        self.assertAlmostEqual(float(result['temperament_score']), 0.501, places=4)


class TestAttackMitigation(NonlinearTrustScalingTestBase):
    """Test that attack pattern is mitigated"""

    def test_repeated_failures_from_max_trust(self):
        """Test that repeated failures from max trust decay quickly"""
        lct_id = 'lct:test:scaling'
        org_id = 'org:test:scaling'

        # Set score to 1.0 (max trust)
        self._create_reputation_score(lct_id, org_id, talent=1.0, training=1.0, temperament=1.0)

        # Apply 100 failures (same as attack pattern)
        penalty = Decimal('-0.001')
        for i in range(100):
            self._apply_delta(lct_id, org_id, penalty, penalty, penalty)

        # Get final score
        result = self._get_reputation_score(lct_id, org_id)

        # With nonlinear scaling, 100 failures should significantly reduce trust
        # Compare to linear: 1.0 - (0.001 * 100) = 0.9 (only 10% reduction)
        # With nonlinear: Should be much lower (exponential decay)

        # The scaling factor decreases as score decreases
        # So the effect is not purely 10x for all 100 penalties
        # But the first few penalties are 10x, bringing score down quickly

        # After ~10 failures with 10x penalty, score is at ~0.9
        # Then scaling factor decreases to ~8.1x
        # This continues, creating accelerated decay

        # Expected: significantly below 0.9 (the linear result)
        self.assertLess(float(result['talent_score']), 0.9)
        self.assertLess(float(result['training_score']), 0.9)
        self.assertLess(float(result['temperament_score']), 0.9)

        print(f"\nAfter 100 failures from max trust:")
        print(f"  Talent: {result['talent_score']:.6f}")
        print(f"  Training: {result['training_score']:.6f}")
        print(f"  Temperament: {result['temperament_score']:.6f}")

    def test_attack_comparison_linear_vs_nonlinear(self):
        """Compare linear vs nonlinear behavior for attack pattern"""
        lct_id = 'lct:test:scaling'
        org_id = 'org:test:scaling'

        # Test linear behavior (old method)
        print("\n=== Linear Behavior (Old) ===")
        self._create_reputation_score(lct_id, org_id, talent=1.0, training=1.0, temperament=1.0)

        # Simulate linear updates
        linear_score = 1.0
        for i in range(100):
            linear_score = max(0.0, min(1.0, linear_score + float(Decimal('-0.001'))))

        print(f"After 100 failures: {linear_score:.6f}")
        print(f"Reduction: {(1.0 - linear_score) * 100:.1f}%")

        # Test nonlinear behavior (new method)
        print("\n=== Nonlinear Behavior (New) ===")
        self._create_reputation_score(lct_id, org_id, talent=1.0, training=1.0, temperament=1.0)

        penalty = Decimal('-0.001')
        for i in range(100):
            self._apply_delta(lct_id, org_id, penalty, penalty, penalty)

        result = self._get_reputation_score(lct_id, org_id)
        nonlinear_score = float(result['talent_score'])

        print(f"After 100 failures: {nonlinear_score:.6f}")
        print(f"Reduction: {(1.0 - nonlinear_score) * 100:.1f}%")

        # Nonlinear should have more reduction
        self.assertLess(nonlinear_score, linear_score)
        print(f"\nNonlinear reduces {((linear_score - nonlinear_score) / (1.0 - linear_score)) * 100:.1f}% more than linear")


class TestClampingBehavior(NonlinearTrustScalingTestBase):
    """Test that clamping still works properly"""

    def test_clamping_at_zero(self):
        """Test that scores can't go below 0"""
        lct_id = 'lct:test:scaling'
        org_id = 'org:test:scaling'

        # Set score near zero
        self._create_reputation_score(lct_id, org_id, talent=0.001, training=0.001, temperament=0.001)

        # Apply large penalty
        self._apply_delta(lct_id, org_id, Decimal('-1.0'), Decimal('-1.0'), Decimal('-1.0'))

        # Get new score
        result = self._get_reputation_score(lct_id, org_id)

        # Should be clamped at 0.0
        self.assertEqual(float(result['talent_score']), 0.0)
        self.assertEqual(float(result['training_score']), 0.0)
        self.assertEqual(float(result['temperament_score']), 0.0)

    def test_clamping_at_one(self):
        """Test that scores can't go above 1"""
        lct_id = 'lct:test:scaling'
        org_id = 'org:test:scaling'

        # Set score near max
        self._create_reputation_score(lct_id, org_id, talent=0.999, training=0.999, temperament=0.999)

        # Apply large reward
        self._apply_delta(lct_id, org_id, Decimal('1.0'), Decimal('1.0'), Decimal('1.0'))

        # Get new score
        result = self._get_reputation_score(lct_id, org_id)

        # Should be clamped at 1.0
        self.assertEqual(float(result['talent_score']), 1.0)
        self.assertEqual(float(result['training_score']), 1.0)
        self.assertEqual(float(result['temperament_score']), 1.0)


if __name__ == '__main__':
    print("Nonlinear Trust Scaling Test Suite")
    print("=" * 70)
    print("Testing P2 security fix for Score Clamping Exploitation")
    print("=" * 70)
    print()

    # Run tests with verbose output
    unittest.main(verbosity=2)
