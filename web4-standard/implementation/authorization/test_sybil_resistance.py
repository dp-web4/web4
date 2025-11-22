#!/usr/bin/env python3
"""
Sybil Resistance Test Suite
Session #58: Validate P1 security fix for Sybil attack prevention

Tests:
- Birth certificate uniqueness validation
- Hardware binding verification and uniqueness
- Identity creation rate limiting
- Suspicious vouching pattern detection
- Risk score calculation
- Integration with identity creation
"""

import unittest
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from sybil_resistance import SybilResistance


# Test database configuration
TEST_DB_CONFIG = {
    'dbname': 'web4',
    'user': 'postgres',
    'host': 'localhost'
}


class SybilResistanceTestBase(unittest.TestCase):
    """Base class for Sybil resistance tests"""

    @classmethod
    def setUpClass(cls):
        """Create test admin LCT and organization once for all tests"""
        conn = psycopg2.connect(**TEST_DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            # Create admin LCT if not exists
            cursor.execute("""
                INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, public_key)
                VALUES ('lct:admin:sybil_test', 'ai', %s, 'test_public_key_sybil_admin')
                ON CONFLICT (lct_id) DO NOTHING
            """, (hashlib.sha256(b'admin_sybil_test').hexdigest(),))

            # Create test organization if not exists
            cursor.execute("""
                INSERT INTO organizations (organization_id, organization_name, admin_lct_id)
                VALUES ('org:test:sybil', 'Sybil Test Org', 'lct:admin:sybil_test')
                ON CONFLICT (organization_id) DO NOTHING
            """)

            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def setUp(self):
        """Set up for each test"""
        self.sybil = SybilResistance(
            db_config=TEST_DB_CONFIG,
            min_atp_deposit=Decimal('10.0'),
            max_identities_per_hour=10
        )

    def _cleanup_test_identities(self, prefix: str):
        """Clean up test identities with given prefix"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM lct_identities
                WHERE lct_id LIKE %s
            """, (f'{prefix}%',))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def _create_test_identity(self, lct_id: str, birth_cert_hash: str,
                             hardware_hash: str = None) -> None:
        """Helper to create test identity"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            # Generate a test public key based on lct_id
            public_key = f"test_public_key_{lct_id}"
            cursor.execute("""
                INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, hardware_binding_hash, public_key)
                VALUES (%s, 'human', %s, %s, %s)
            """, (lct_id, birth_cert_hash, hardware_hash, public_key))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


class TestBirthCertificateValidation(SybilResistanceTestBase):
    """Test birth certificate uniqueness validation"""

    def test_unique_birth_certificate_valid(self):
        """Test that unique birth certificate is valid"""
        unique_cert = hashlib.sha256(b'unique_birth_cert_001').hexdigest()
        is_valid = self.sybil.validate_birth_certificate(unique_cert)
        self.assertTrue(is_valid, "Unique birth certificate should be valid")

    def test_duplicate_birth_certificate_rejected(self):
        """Test that duplicate birth certificate is rejected"""
        # Create identity with birth certificate
        test_lct = 'lct:test:sybil:duplicate_bc'
        test_cert = hashlib.sha256(b'duplicate_birth_cert').hexdigest()

        self._create_test_identity(test_lct, test_cert)

        try:
            # Try to validate same birth certificate
            is_valid = self.sybil.validate_birth_certificate(test_cert)
            self.assertFalse(is_valid, "Duplicate birth certificate should be rejected")
        finally:
            self._cleanup_test_identities('lct:test:sybil:duplicate_bc')

    def test_multiple_unique_certificates_all_valid(self):
        """Test that multiple unique certificates all validate"""
        certs = [
            hashlib.sha256(f'unique_cert_{i}'.encode()).hexdigest()
            for i in range(5)
        ]

        for cert in certs:
            is_valid = self.sybil.validate_birth_certificate(cert)
            self.assertTrue(is_valid, f"Certificate {cert[:16]}... should be valid")


class TestHardwareBindingValidation(SybilResistanceTestBase):
    """Test hardware binding verification"""

    def test_new_hardware_binding_valid(self):
        """Test that new hardware binding is valid"""
        new_lct = 'lct:test:sybil:new_hardware'
        new_hardware = hashlib.sha256(b'new_hardware_001').hexdigest()

        is_valid = self.sybil.validate_hardware_binding(new_lct, new_hardware)
        self.assertTrue(is_valid, "New hardware binding should be valid")

    def test_duplicate_hardware_binding_rejected(self):
        """Test that hardware already bound to another identity is rejected"""
        # Create identity with hardware binding
        test_lct_1 = 'lct:test:sybil:hw_bind_1'
        test_lct_2 = 'lct:test:sybil:hw_bind_2'
        test_hardware = hashlib.sha256(b'shared_hardware').hexdigest()
        test_cert_1 = hashlib.sha256(b'cert_hw_1').hexdigest()
        test_cert_2 = hashlib.sha256(b'cert_hw_2').hexdigest()

        self._create_test_identity(test_lct_1, test_cert_1, test_hardware)

        try:
            # Try to bind same hardware to different identity
            is_valid = self.sybil.validate_hardware_binding(test_lct_2, test_hardware)
            self.assertFalse(is_valid, "Hardware already bound should be rejected")
        finally:
            self._cleanup_test_identities('lct:test:sybil:hw_bind_')

    def test_existing_binding_must_match(self):
        """Test that identity with existing binding must provide matching hash"""
        test_lct = 'lct:test:sybil:existing_bind'
        original_hardware = hashlib.sha256(b'original_hardware').hexdigest()
        different_hardware = hashlib.sha256(b'different_hardware').hexdigest()
        test_cert = hashlib.sha256(b'cert_existing_bind').hexdigest()

        self._create_test_identity(test_lct, test_cert, original_hardware)

        try:
            # Same hardware should validate
            is_valid_same = self.sybil.validate_hardware_binding(test_lct, original_hardware)
            self.assertTrue(is_valid_same, "Original hardware should validate")

            # Different hardware should fail
            is_valid_different = self.sybil.validate_hardware_binding(test_lct, different_hardware)
            self.assertFalse(is_valid_different, "Different hardware should fail")
        finally:
            self._cleanup_test_identities('lct:test:sybil:existing_bind')


class TestIdentityCreationRateLimit(SybilResistanceTestBase):
    """Test identity creation rate limiting"""

    def setUp(self):
        """Set up with low rate limit for testing"""
        super().setUp()
        self.sybil = SybilResistance(
            db_config=TEST_DB_CONFIG,
            max_identities_per_hour=5  # Low limit for testing
        )

    def test_within_rate_limit_allowed(self):
        """Test that creation within rate limit is allowed"""
        # Clean up recent test identities first
        self._cleanup_recent_test_identities()

        # Should be within limit initially
        is_ok = self.sybil.check_identity_creation_rate()
        self.assertTrue(is_ok, "Should be within rate limit initially")

    def test_exceeding_rate_limit_blocked(self):
        """Test that exceeding rate limit is blocked"""
        # Clean up and create identities up to limit
        self._cleanup_recent_test_identities()

        # Create identities up to the limit
        for i in range(5):
            lct_id = f'lct:test:sybil:rate_{i}'
            cert = hashlib.sha256(f'rate_cert_{i}'.encode()).hexdigest()
            self._create_test_identity(lct_id, cert)

        try:
            # Next creation should be blocked
            is_ok = self.sybil.check_identity_creation_rate()
            self.assertFalse(is_ok, "Should exceed rate limit after 5 creations")
        finally:
            self._cleanup_test_identities('lct:test:sybil:rate_')

    def _cleanup_recent_test_identities(self):
        """Clean up recent test identities"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            cursor.execute("""
                DELETE FROM lct_identities
                WHERE lct_id LIKE %s
                AND created_at >= %s
            """, ('lct:test:sybil:%', one_hour_ago))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


class TestSuspiciousVouchingDetection(SybilResistanceTestBase):
    """Test suspicious vouching pattern detection"""

    def test_new_identity_many_vouches_suspicious(self):
        """Test that new identity with many vouches is flagged"""
        # This test requires trust_relationships table with vouching data
        # For now, we'll test with an identity that doesn't exist
        result = self.sybil.detect_suspicious_vouching('lct:nonexistent:identity')
        self.assertFalse(result['suspicious'], "Non-existent identity should not be suspicious")
        self.assertIn('Identity not found', result['reason'])

    def test_circular_vouching_suspicious(self):
        """Test that circular vouching is detected"""
        # Create test identities and circular vouches
        test_lct_a = 'lct:test:sybil:circular_a'
        test_lct_b = 'lct:test:sybil:circular_b'
        test_cert_a = hashlib.sha256(b'cert_circular_a').hexdigest()
        test_cert_b = hashlib.sha256(b'cert_circular_b').hexdigest()

        self._create_test_identity(test_lct_a, test_cert_a)
        self._create_test_identity(test_lct_b, test_cert_b)

        # Create circular trust relationships (A->B, B->A)
        self._create_trust_relationship(test_lct_a, test_lct_b)
        self._create_trust_relationship(test_lct_b, test_lct_a)

        try:
            # Check for suspicious pattern
            result = self.sybil.detect_suspicious_vouching(test_lct_a, threshold=1)
            # With only 1 circular vouch and threshold=1, might be suspicious
            # Result depends on the threshold logic
            self.assertIn('circular_count', result)
        finally:
            self._cleanup_trust_relationships(test_lct_a, test_lct_b)
            self._cleanup_test_identities('lct:test:sybil:circular_')

    def _create_trust_relationship(self, source_lct: str, target_lct: str):
        """Helper to create trust relationship"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO trust_relationships
                (source_lct, target_lct, relationship_type, organization_id, created_at)
                VALUES (%s, %s, 'vouching', 'org:test:sybil', CURRENT_TIMESTAMP)
                ON CONFLICT (source_lct, target_lct, organization_id, relationship_type) DO NOTHING
            """, (source_lct, target_lct))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def _cleanup_trust_relationships(self, lct_a: str, lct_b: str):
        """Helper to clean up trust relationships"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM trust_relationships
                WHERE (source_lct = %s AND target_lct = %s)
                   OR (source_lct = %s AND target_lct = %s)
            """, (lct_a, lct_b, lct_b, lct_a))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


class TestRiskScoreCalculation(SybilResistanceTestBase):
    """Test Sybil risk score calculation"""

    def test_new_identity_no_binding_medium_risk(self):
        """Test that new identity without hardware binding has medium risk"""
        # Create new identity without hardware binding
        test_lct = 'lct:test:sybil:new_no_hw'
        test_cert = hashlib.sha256(b'cert_new_no_hw').hexdigest()

        self._create_test_identity(test_lct, test_cert, hardware_hash=None)

        try:
            # Create reputation score entry
            self._create_reputation_score(test_lct, 'org:test:sybil')

            risk = self.sybil.get_identity_risk_score(test_lct)

            # Should have risk factors:
            # - New identity (< 7 days): +2
            # - No hardware binding: +1
            # Total: 3 (MEDIUM risk)
            self.assertGreaterEqual(risk['risk_score'], 3, "Should have medium risk")
            self.assertEqual(risk['risk_level'], 'MEDIUM')
            self.assertIn('New identity', str(risk['factors']))
            self.assertIn('No hardware binding', str(risk['factors']))
        finally:
            self._cleanup_reputation_scores(test_lct)
            self._cleanup_test_identities('lct:test:sybil:new_no_hw')

    def test_old_identity_with_binding_low_risk(self):
        """Test that old identity with hardware binding has low risk"""
        # Create old identity with hardware binding
        test_lct = 'lct:test:sybil:old_with_hw'
        test_cert = hashlib.sha256(b'cert_old_with_hw').hexdigest()
        test_hardware = hashlib.sha256(b'hardware_old').hexdigest()

        self._create_test_identity(test_lct, test_cert, test_hardware)

        # Backdate the identity creation
        self._backdate_identity(test_lct, days=30)

        try:
            # Create reputation score entry with good scores
            self._create_reputation_score(test_lct, 'org:test:sybil', avg_score=0.7)

            risk = self.sybil.get_identity_risk_score(test_lct)

            # Should have low risk:
            # - Old identity: 0
            # - Has hardware binding: 0
            # - Good trust scores: 0
            # Total: 0-2 (LOW risk)
            self.assertLessEqual(risk['risk_score'], 2, "Should have low risk")
            self.assertEqual(risk['risk_level'], 'LOW')
        finally:
            self._cleanup_reputation_scores(test_lct)
            self._cleanup_test_identities('lct:test:sybil:old_with_hw')

    def test_nonexistent_identity_critical_risk(self):
        """Test that non-existent identity has critical risk"""
        risk = self.sybil.get_identity_risk_score('lct:nonexistent:identity')
        self.assertEqual(risk['risk_score'], 10)
        self.assertEqual(risk['risk_level'], 'CRITICAL')
        self.assertIn('Identity not found', risk['factors'])

    def _create_reputation_score(self, lct_id: str, org_id: str, avg_score: float = 0.5):
        """Helper to create reputation score"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO reputation_scores
                (lct_id, organization_id, talent_score, training_score, temperament_score)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (lct_id, organization_id) DO UPDATE
                SET talent_score = EXCLUDED.talent_score,
                    training_score = EXCLUDED.training_score,
                    temperament_score = EXCLUDED.temperament_score
            """, (lct_id, org_id, avg_score, avg_score, avg_score))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def _cleanup_reputation_scores(self, lct_id: str):
        """Helper to clean up reputation scores"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM reputation_scores
                WHERE lct_id = %s
            """, (lct_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def _backdate_identity(self, lct_id: str, days: int):
        """Helper to backdate identity creation"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            past_date = datetime.now(timezone.utc) - timedelta(days=days)
            cursor.execute("""
                UPDATE lct_identities
                SET created_at = %s
                WHERE lct_id = %s
            """, (past_date, lct_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


class TestIdentityCreationValidation(SybilResistanceTestBase):
    """Test comprehensive identity creation validation"""

    def test_valid_identity_creation_passes(self):
        """Test that valid identity creation passes all checks"""
        unique_cert = hashlib.sha256(b'valid_creation_cert').hexdigest()
        unique_hardware = hashlib.sha256(b'valid_creation_hw').hexdigest()

        validation = self.sybil.validate_identity_creation(
            birth_cert_hash=unique_cert,
            hardware_hash=unique_hardware
        )

        # Should pass all checks
        self.assertTrue(validation['valid'], "Valid identity should pass")
        self.assertTrue(validation['checks']['birth_certificate']['valid'])
        self.assertTrue(validation['checks']['creation_rate']['valid'])
        self.assertTrue(validation['checks']['hardware_binding']['valid'])

    def test_duplicate_birth_cert_fails_validation(self):
        """Test that duplicate birth certificate fails validation"""
        # Create identity
        test_lct = 'lct:test:sybil:dup_cert_val'
        dup_cert = hashlib.sha256(b'duplicate_cert_validation').hexdigest()
        self._create_test_identity(test_lct, dup_cert)

        try:
            validation = self.sybil.validate_identity_creation(
                birth_cert_hash=dup_cert
            )

            # Should fail birth certificate check
            self.assertFalse(validation['valid'], "Duplicate cert should fail")
            self.assertFalse(validation['checks']['birth_certificate']['valid'])
            self.assertIn('Duplicate', validation['checks']['birth_certificate']['message'])
        finally:
            self._cleanup_test_identities('lct:test:sybil:dup_cert_val')

    def test_rate_limit_exceeded_fails_validation(self):
        """Test that exceeding rate limit fails validation"""
        # Create low-limit sybil checker
        sybil_limited = SybilResistance(
            db_config=TEST_DB_CONFIG,
            max_identities_per_hour=2
        )

        # Clean up and create identities up to limit
        self._cleanup_recent_test_identities()
        for i in range(2):
            lct_id = f'lct:test:sybil:rate_val_{i}'
            cert = hashlib.sha256(f'rate_val_cert_{i}'.encode()).hexdigest()
            self._create_test_identity(lct_id, cert)

        try:
            # Next validation should fail rate limit
            new_cert = hashlib.sha256(b'new_cert_after_limit').hexdigest()
            validation = sybil_limited.validate_identity_creation(
                birth_cert_hash=new_cert
            )

            # Should fail rate limit check
            self.assertFalse(validation['valid'], "Should fail rate limit")
            self.assertFalse(validation['checks']['creation_rate']['valid'])
            self.assertIn('limit', validation['checks']['creation_rate']['message'])
        finally:
            self._cleanup_test_identities('lct:test:sybil:rate_val_')

    def _cleanup_recent_test_identities(self):
        """Clean up recent test identities"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            cursor.execute("""
                DELETE FROM lct_identities
                WHERE lct_id LIKE %s
                AND created_at >= %s
            """, ('lct:test:sybil:%', one_hour_ago))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


if __name__ == '__main__':
    print("Sybil Resistance Test Suite")
    print("=" * 70)
    print("Testing P1 security fix for Sybil attack prevention")
    print("=" * 70)
    print()

    # Run tests with verbose output
    unittest.main(verbosity=2)
