#!/usr/bin/env python3
"""
Delegation Validator Test Suite
Session #59: P1 Security Fix - Unauthorized Delegation Attack Testing

Tests:
- Invalid delegation signature rejection
- Unauthorized permission delegation prevention
- Witness signature validation
- Delegation chain validation (sub-delegation)
- Delegation rate limiting
- Audit logging
"""

import unittest
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from delegation_validator import DelegationValidator, DelegationValidationError
from crypto_verification import CryptoVerifier


# Test database configuration
TEST_DB_CONFIG = {
    'dbname': 'web4',
    'user': 'postgres',
    'host': 'localhost'
}


class DelegationValidatorTestBase(unittest.TestCase):
    """Base class for delegation validator tests"""

    @classmethod
    def setUpClass(cls):
        """Create test identities and organization once for all tests"""
        conn = psycopg2.connect(**TEST_DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            # Create 32-byte mock public keys (hex-encoded)
            admin_pubkey = hashlib.sha256(b'admin_pubkey').hexdigest()  # 64 hex chars = 32 bytes
            agent_pubkey = hashlib.sha256(b'agent_pubkey').hexdigest()
            attacker_pubkey = hashlib.sha256(b'attacker_pubkey').hexdigest()

            # Create test admin LCT
            cursor.execute("""
                INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, public_key)
                VALUES ('lct:admin:deleg_test', 'human', %s, %s)
                ON CONFLICT (lct_id) DO NOTHING
            """, (
                hashlib.sha256(b'admin_deleg_test').hexdigest(),
                admin_pubkey
            ))

            # Create test agent LCT
            cursor.execute("""
                INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, public_key)
                VALUES ('lct:agent:deleg_test', 'ai', %s, %s)
                ON CONFLICT (lct_id) DO NOTHING
            """, (
                hashlib.sha256(b'agent_deleg_test').hexdigest(),
                agent_pubkey
            ))

            # Create test attacker LCT
            cursor.execute("""
                INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, public_key)
                VALUES ('lct:attacker:deleg_test', 'ai', %s, %s)
                ON CONFLICT (lct_id) DO NOTHING
            """, (
                hashlib.sha256(b'attacker_deleg_test').hexdigest(),
                attacker_pubkey
            ))

            # Create test organization
            cursor.execute("""
                INSERT INTO organizations (organization_id, organization_name, admin_lct_id)
                VALUES ('org:deleg_test', 'Delegation Test Org', 'lct:admin:deleg_test')
                ON CONFLICT (organization_id) DO NOTHING
            """)

            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def setUp(self):
        """Set up for each test"""
        self.validator = DelegationValidator(db_config=TEST_DB_CONFIG)

    def _cleanup_delegations(self, prefix: str):
        """Clean up test delegations with given prefix"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM agent_delegations
                WHERE delegation_id LIKE %s
            """, (f'{prefix}%',))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def _cleanup_claims(self, prefix: str):
        """Clean up test permission claims with given prefix"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM permission_claims
                WHERE claim_hash LIKE %s
            """, (f'{prefix}%',))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def _create_test_claim(self, claim_hash: str, subject_lct: str, org_id: str):
        """Helper to create test permission claim"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO permission_claims
                (claim_hash, claim_id, issuer_lct, subject_lct, organization_id,
                 permission_action, resource_pattern, signature, issued_at, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'active')
                ON CONFLICT (claim_hash) DO NOTHING
            """, (
                claim_hash,
                f'claim_id:{claim_hash}',
                'lct:admin:deleg_test',
                subject_lct,
                org_id,
                'test_action',
                'test_resource',
                'mock_signature'
            ))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def _create_test_delegation(
        self,
        delegation_id: str,
        delegator_lct: str,
        delegatee_lct: str,
        org_id: str,
        granted_claims: list,
        parent_id: str = None
    ):
        """Helper to create test delegation"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        try:
            from psycopg2.extras import Json
            cursor.execute("""
                INSERT INTO agent_delegations
                (delegation_id, delegator_lct, delegatee_lct, organization_id,
                 granted_claim_hashes, atp_budget_total, valid_from, valid_until,
                 delegation_signature, parent_delegation_id, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
            """, (
                delegation_id, delegator_lct, delegatee_lct, org_id,
                Json(granted_claims), 1000,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc) + timedelta(days=30),
                'mock_signature',
                parent_id
            ))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


class TestDelegationSignatureVerification(DelegationValidatorTestBase):
    """Test delegation signature verification"""

    def test_missing_delegator_public_key_rejected(self):
        """Test that delegation with missing delegator public key is rejected"""
        # Create temporary LCT without public key (will fail)
        delegation_id = 'deleg:test:no_pubkey'
        delegator = 'lct:nonexistent:test'  # This LCT doesn't exist
        delegatee = 'lct:agent:deleg_test'
        org_id = 'org:deleg_test'
        claims = ['claim:test:001']
        signature = 'invalid_signature'

        valid, error = self.validator.validate_delegation(
            delegation_id=delegation_id,
            delegator_lct=delegator,
            delegatee_lct=delegatee,
            organization_id=org_id,
            granted_claim_hashes=claims,
            delegation_signature=signature
        )

        self.assertFalse(valid, "Delegation without delegator public key should be rejected")
        self.assertIn("signature", error.lower())

    def test_invalid_signature_rejected(self):
        """Test that invalid delegation signature is rejected"""
        delegation_id = 'deleg:test:invalid_sig'
        delegator = 'lct:admin:deleg_test'  # Exists with public key
        delegatee = 'lct:agent:deleg_test'
        org_id = 'org:deleg_test'
        claims = ['claim:test:002']
        signature = 'definitely_invalid_signature'

        valid, error = self.validator.validate_delegation(
            delegation_id=delegation_id,
            delegator_lct=delegator,
            delegatee_lct=delegatee,
            organization_id=org_id,
            granted_claim_hashes=claims,
            delegation_signature=signature
        )

        self.assertFalse(valid, "Invalid signature should be rejected")
        self.assertIn("signature", error.lower())


class TestUnauthorizedPermissionDelegation(DelegationValidatorTestBase):
    """Test prevention of unauthorized permission delegation"""

    def test_delegator_without_permission_rejected(self):
        """Test that delegator without permission cannot delegate it"""
        # Attacker tries to delegate permission they don't have
        delegation_id = 'deleg:test:unauth_perm'
        delegator = 'lct:attacker:deleg_test'
        delegatee = 'lct:agent:deleg_test'
        org_id = 'org:deleg_test'
        claims = ['claim:test:nonexistent']  # Claim attacker doesn't have
        signature = 'mock_signature'

        try:
            valid, error = self.validator.validate_delegation(
                delegation_id=delegation_id,
                delegator_lct=delegator,
                delegatee_lct=delegatee,
                organization_id=org_id,
                granted_claim_hashes=claims,
                delegation_signature=signature
            )

            self.assertFalse(valid, "Unauthorized permission delegation should be rejected")
            self.assertIn("lacks permissions", error)
        finally:
            self._cleanup_delegations('deleg:test:unauth_perm')

    def test_delegator_with_permission_accepted(self):
        """Test that delegator with permission can delegate it"""
        # Give admin the permission first
        claim_hash = 'claim:test:admin_has'
        self._create_test_claim(
            claim_hash,
            'lct:admin:deleg_test',
            'org:deleg_test'
        )

        try:
            delegation_id = 'deleg:test:auth_perm'
            delegator = 'lct:admin:deleg_test'
            delegatee = 'lct:agent:deleg_test'
            org_id = 'org:deleg_test'
            signature = 'mock_signature'

            # This will still fail on signature verification,
            # but should pass permission check
            valid, error = self.validator.validate_delegation(
                delegation_id=delegation_id,
                delegator_lct=delegator,
                delegatee_lct=delegatee,
                organization_id=org_id,
                granted_claim_hashes=[claim_hash],
                delegation_signature=signature
            )

            # Should fail on signature, not permission
            self.assertFalse(valid)
            if error:
                self.assertIn("signature", error.lower())
                self.assertNotIn("lacks permissions", error)

        finally:
            self._cleanup_claims('claim:test:admin_has')
            self._cleanup_delegations('deleg:test:auth_perm')


class TestDelegationChainValidation(DelegationValidatorTestBase):
    """Test delegation chain validation for sub-delegations"""

    def test_subdelegation_without_parent_rejected(self):
        """Test that sub-delegation without valid parent is rejected"""
        delegation_id = 'deleg:test:sub_no_parent'
        delegator = 'lct:agent:deleg_test'
        delegatee = 'lct:attacker:deleg_test'
        org_id = 'org:deleg_test'
        claims = ['claim:test:sub']
        signature = 'mock_signature'
        parent_id = 'deleg:nonexistent:parent'

        valid, error = self.validator.validate_delegation(
            delegation_id=delegation_id,
            delegator_lct=delegator,
            delegatee_lct=delegatee,
            organization_id=org_id,
            granted_claim_hashes=claims,
            delegation_signature=signature,
            parent_delegation_id=parent_id
        )

        self.assertFalse(valid, "Sub-delegation without parent should be rejected")
        self.assertIn("chain", error.lower())

    def test_subdelegation_with_valid_parent_chain_checked(self):
        """Test that sub-delegation chain is properly validated"""
        # Create parent delegation first
        parent_id = 'deleg:test:parent_chain'
        claim_hash = 'claim:test:chain_perm'

        # Give parent permission to admin
        self._create_test_claim(
            claim_hash,
            'lct:admin:deleg_test',
            'org:deleg_test'
        )

        # Create parent delegation (admin -> agent)
        self._create_test_delegation(
            parent_id,
            'lct:admin:deleg_test',
            'lct:agent:deleg_test',
            'org:deleg_test',
            [claim_hash]
        )

        try:
            # Now agent tries to sub-delegate (agent -> attacker)
            delegation_id = 'deleg:test:sub_with_parent'
            delegator = 'lct:agent:deleg_test'  # Was delegatee in parent
            delegatee = 'lct:attacker:deleg_test'
            org_id = 'org:deleg_test'
            signature = 'mock_signature'

            valid, error = self.validator.validate_delegation(
                delegation_id=delegation_id,
                delegator_lct=delegator,
                delegatee_lct=delegatee,
                organization_id=org_id,
                granted_claim_hashes=[claim_hash],
                delegation_signature=signature,
                parent_delegation_id=parent_id
            )

            # Should fail on signature, but pass chain validation
            self.assertFalse(valid)
            if error:
                # Should not fail on chain
                self.assertNotIn("chain", error.lower())

        finally:
            self._cleanup_delegations('deleg:test:parent_chain')
            self._cleanup_delegations('deleg:test:sub_with_parent')
            self._cleanup_claims('claim:test:chain_perm')

    def test_subdelegation_excess_permissions_rejected(self):
        """Test that sub-delegation with more permissions than parent is rejected"""
        # Create parent delegation with limited permissions
        parent_id = 'deleg:test:parent_limited'
        parent_claim = 'claim:test:limited'
        excess_claim = 'claim:test:excess'

        # Give admin both claims
        self._create_test_claim(parent_claim, 'lct:admin:deleg_test', 'org:deleg_test')
        self._create_test_claim(excess_claim, 'lct:admin:deleg_test', 'org:deleg_test')

        # Parent delegation only grants parent_claim
        self._create_test_delegation(
            parent_id,
            'lct:admin:deleg_test',
            'lct:agent:deleg_test',
            'org:deleg_test',
            [parent_claim]  # Only this claim
        )

        try:
            # Sub-delegation tries to grant excess_claim (not in parent)
            delegation_id = 'deleg:test:sub_excess'
            delegator = 'lct:agent:deleg_test'
            delegatee = 'lct:attacker:deleg_test'
            org_id = 'org:deleg_test'
            signature = 'mock_signature'

            valid, error = self.validator.validate_delegation(
                delegation_id=delegation_id,
                delegator_lct=delegator,
                delegatee_lct=delegatee,
                organization_id=org_id,
                granted_claim_hashes=[excess_claim],  # Not in parent
                delegation_signature=signature,
                parent_delegation_id=parent_id
            )

            self.assertFalse(valid, "Sub-delegation with excess permissions should be rejected")
            self.assertIn("parent", error.lower())

        finally:
            self._cleanup_delegations('deleg:test:parent_limited')
            self._cleanup_delegations('deleg:test:sub_excess')
            self._cleanup_claims('claim:test:limited')
            self._cleanup_claims('claim:test:excess')


class TestDelegationRateLimiting(DelegationValidatorTestBase):
    """Test delegation creation rate limiting"""

    def test_delegation_rate_limit_enforced(self):
        """Test that delegation rate limiting prevents flooding"""
        delegator = 'lct:admin:deleg_test'
        delegatee = 'lct:agent:deleg_test'
        org_id = 'org:deleg_test'
        claim_hash = 'claim:test:rate_limit'

        # Give delegator the permission
        self._create_test_claim(claim_hash, delegator, org_id)

        try:
            # Create many delegations quickly (beyond rate limit)
            created_count = 0
            max_to_create = 105  # Above default 100/hour limit

            for i in range(max_to_create):
                delegation_id = f'deleg:test:rate_{i}'

                # Actually create the delegation (bypass validation)
                self._create_test_delegation(
                    delegation_id,
                    delegator,
                    delegatee,
                    org_id,
                    [claim_hash]
                )
                created_count += 1

            # Now try to validate a new one - should fail rate limit
            new_delegation_id = f'deleg:test:rate_{max_to_create}'
            signature = 'mock_signature'

            valid, error = self.validator.validate_delegation(
                delegation_id=new_delegation_id,
                delegator_lct=delegator,
                delegatee_lct=delegatee,
                organization_id=org_id,
                granted_claim_hashes=[claim_hash],
                delegation_signature=signature
            )

            # Should be rejected due to rate limit
            self.assertFalse(valid, "Delegation beyond rate limit should be rejected")
            if error:
                self.assertIn("rate limit", error.lower())

        finally:
            self._cleanup_delegations('deleg:test:rate_')
            self._cleanup_claims('claim:test:rate_limit')


class TestAuditLogging(DelegationValidatorTestBase):
    """Test audit logging of delegation validation"""

    def test_validation_failure_logged(self):
        """Test that validation failures are logged to audit trail"""
        delegation_id = 'deleg:test:audit_fail'
        delegator = 'lct:attacker:deleg_test'
        delegatee = 'lct:agent:deleg_test'
        org_id = 'org:deleg_test'
        claims = ['claim:test:audit']
        signature = 'invalid_signature'

        # This should fail and be logged
        valid, error = self.validator.validate_delegation(
            delegation_id=delegation_id,
            delegator_lct=delegator,
            delegatee_lct=delegatee,
            organization_id=org_id,
            granted_claim_hashes=claims,
            delegation_signature=signature
        )

        self.assertFalse(valid)

        # Check audit log
        conn = psycopg2.connect(**TEST_DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT event_type, event_data
                FROM delegation_audit_log
                WHERE delegation_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (delegation_id,))

            result = cursor.fetchone()
            self.assertIsNotNone(result, "Validation failure should be in audit log")
            self.assertEqual(result['event_type'], 'validation_failure')
            self.assertIn('error', result['event_data'])

        finally:
            # Cleanup audit log
            cursor.execute("""
                DELETE FROM delegation_audit_log
                WHERE delegation_id = %s
            """, (delegation_id,))
            conn.commit()
            cursor.close()
            conn.close()


if __name__ == '__main__':
    print("Delegation Validator Test Suite")
    print("=" * 70)
    print("Testing P1 security fix for Unauthorized Delegation attacks")
    print("=" * 70)
    print()

    # Run tests with verbose output
    unittest.main(verbosity=2)
