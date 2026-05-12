#!/usr/bin/env python3
"""
Delegation Validation - Session #59 P1 Security Fix
===================================================

Runtime validation for agent delegations to prevent unauthorized
delegation attacks (Attack Vector 3.1 from ATTACK_VECTORS.md).

Security Requirements:
1. Signature verification - Verify delegator signature
2. Permission validation - Check delegator has permission to delegate
3. Witness validation - Verify witness signatures if required
4. Audit logging - Track all delegation attempts
5. Permission chain validation - Verify delegation chain integrity

From ATTACK_VECTORS.md Session #56:
**Attack Pattern**:
```python
# Attacker delegates admin role to themselves
create_delegation(
    delegator="lct:admin:org:001",  # Spoofed
    delegatee="lct:attacker:001",
    role="org:admin",
    permissions=["*"]  # All permissions
)
```

**Mitigation**:
1. ✅ Signature verification (this module)
2. ✅ Permission validation (this module)
3. ✅ Audit logging (this module)
4. ✅ Witness validation (this module)
5. ✅ Permission chain validation (this module)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import hashlib
import json
import logging

# Import existing crypto verification
from crypto_verification import CryptoVerifier, VerificationResult, SignatureVerificationError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DelegationValidationError(Exception):
    """Raised when delegation validation fails"""
    pass


class DelegationValidator:
    """
    Runtime validator for agent delegations.

    Enforces security requirements:
    - Signature verification (cryptographic proof)
    - Permission chain validation (delegator must have permissions)
    - Witness validation (multi-sig if required)
    - Audit logging (full trail of delegation attempts)
    - Rate limiting (prevent delegation flooding)
    """

    def __init__(self, db_config: dict, crypto_verifier: Optional[CryptoVerifier] = None):
        """
        Initialize delegation validator.

        Args:
            db_config: PostgreSQL connection config
            crypto_verifier: Optional CryptoVerifier instance
        """
        self.db_config = db_config
        self.crypto_verifier = crypto_verifier or CryptoVerifier()

    def validate_delegation(
        self,
        delegation_id: str,
        delegator_lct: str,
        delegatee_lct: str,
        organization_id: str,
        granted_claim_hashes: List[str],
        delegation_signature: str,
        witness_signatures: Optional[List[Dict]] = None,
        parent_delegation_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a delegation request.

        Args:
            delegation_id: Unique delegation identifier
            delegator_lct: Principal delegating authority
            delegatee_lct: Agent receiving authority
            organization_id: Organization context
            granted_claim_hashes: List of permission claim hashes
            delegation_signature: Delegator's signature
            witness_signatures: Optional witness signatures
            parent_delegation_id: For sub-delegations

        Returns:
            (valid, error_message) tuple
            - (True, None) if valid
            - (False, error_message) if invalid

        Validation steps:
        1. Verify delegation signature
        2. Check delegator has permissions being delegated
        3. Verify witness signatures if required
        4. Validate delegation chain if sub-delegation
        5. Log validation attempt
        """
        try:
            # Step 1: Verify delegation signature
            if not self._verify_delegation_signature(
                delegation_id, delegator_lct, delegatee_lct,
                organization_id, granted_claim_hashes, delegation_signature
            ):
                error = f"Invalid delegation signature from {delegator_lct}"
                self._log_validation_failure(delegation_id, delegator_lct, delegatee_lct, error)
                return False, error

            # Step 2: Verify delegator has permissions
            if not self._verify_delegator_permissions(
                delegator_lct, organization_id, granted_claim_hashes
            ):
                error = f"Delegator {delegator_lct} lacks permissions being delegated"
                self._log_validation_failure(delegation_id, delegator_lct, delegatee_lct, error)
                return False, error

            # Step 3: Verify witness signatures if required
            if witness_signatures:
                if not self._verify_witness_signatures(
                    delegation_id, witness_signatures
                ):
                    error = f"Invalid witness signatures for delegation {delegation_id}"
                    self._log_validation_failure(delegation_id, delegator_lct, delegatee_lct, error)
                    return False, error

            # Step 4: Validate delegation chain if sub-delegation
            if parent_delegation_id:
                if not self._validate_delegation_chain(
                    delegator_lct, parent_delegation_id, granted_claim_hashes
                ):
                    error = f"Invalid delegation chain: parent {parent_delegation_id}"
                    self._log_validation_failure(delegation_id, delegator_lct, delegatee_lct, error)
                    return False, error

            # Step 5: Check delegation rate limits
            if not self._check_delegation_rate_limit(delegator_lct):
                error = f"Delegation rate limit exceeded for {delegator_lct}"
                self._log_validation_failure(delegation_id, delegator_lct, delegatee_lct, error)
                return False, error

            # All validations passed
            self._log_validation_success(delegation_id, delegator_lct, delegatee_lct)
            return True, None

        except Exception as e:
            error = f"Validation error: {str(e)}"
            logger.error(f"Delegation validation failed: {error}")
            self._log_validation_failure(delegation_id, delegator_lct, delegatee_lct, error)
            return False, error

    def _verify_delegation_signature(
        self,
        delegation_id: str,
        delegator_lct: str,
        delegatee_lct: str,
        organization_id: str,
        granted_claim_hashes: List[str],
        delegation_signature: str
    ) -> bool:
        """
        Verify the delegation signature from delegator.

        Args:
            delegation_id: Delegation identifier
            delegator_lct: Delegator LCT
            delegatee_lct: Delegatee LCT
            organization_id: Organization
            granted_claim_hashes: Granted permissions
            delegation_signature: Signature to verify

        Returns:
            True if signature is valid
        """
        # Construct delegation data for signature verification
        delegation_data = {
            'delegation_id': delegation_id,
            'delegator': delegator_lct,
            'delegatee': delegatee_lct,
            'organization_id': organization_id,
            'granted_claims': sorted(granted_claim_hashes)  # Canonical ordering
        }

        # Get delegator's public key from database
        delegator_pubkey = self._get_lct_public_key(delegator_lct)
        if not delegator_pubkey:
            logger.warning(f"No public key found for delegator {delegator_lct}")
            return False

        # Register public key with crypto verifier
        self.crypto_verifier.register_public_key(delegator_lct, delegator_pubkey)

        # Verify signature
        try:
            result = self.crypto_verifier.verify_delegation_signature(
                delegation_data,
                delegation_signature,
                delegator_lct
            )
            return result.valid
        except SignatureVerificationError as e:
            logger.warning(f"Signature verification failed: {e}")
            return False

    def _verify_delegator_permissions(
        self,
        delegator_lct: str,
        organization_id: str,
        granted_claim_hashes: List[str]
    ) -> bool:
        """
        Verify delegator has the permissions being delegated.

        Args:
            delegator_lct: Delegator LCT
            organization_id: Organization context
            granted_claim_hashes: Claims being delegated

        Returns:
            True if delegator has all granted permissions
        """
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            # Get all permission claims for delegator in this organization
            cursor.execute("""
                SELECT claim_hash, status
                FROM permission_claims
                WHERE subject_lct = %s
                AND organization_id = %s
                AND status = 'active'
            """, (delegator_lct, organization_id))

            delegator_claims = {row['claim_hash'] for row in cursor.fetchall()}

            # Check if delegator has all granted claims
            for claim_hash in granted_claim_hashes:
                if claim_hash not in delegator_claims:
                    logger.warning(
                        f"Delegator {delegator_lct} lacks claim {claim_hash}"
                    )
                    return False

            return True

        finally:
            cursor.close()
            conn.close()

    def _verify_witness_signatures(
        self,
        delegation_id: str,
        witness_signatures: List[Dict]
    ) -> bool:
        """
        Verify witness signatures if required.

        Args:
            delegation_id: Delegation identifier
            witness_signatures: List of witness signature dicts

        Returns:
            True if all witness signatures are valid
        """
        # Each witness signature should have:
        # - witness_lct: LCT of witness
        # - signature: Ed25519 signature
        # - timestamp: When signature was created

        for witness in witness_signatures:
            witness_lct = witness.get('witness_lct')
            signature = witness.get('signature')

            if not witness_lct or not signature:
                logger.warning(f"Invalid witness signature format: {witness}")
                return False

            # Get witness public key
            witness_pubkey = self._get_lct_public_key(witness_lct)
            if not witness_pubkey:
                logger.warning(f"No public key for witness {witness_lct}")
                return False

            # Register and verify
            self.crypto_verifier.register_public_key(witness_lct, witness_pubkey)

            try:
                # Witness signs delegation_id
                witness_data = {'delegation_id': delegation_id}
                result = self.crypto_verifier.verify_delegation_signature(
                    witness_data,
                    signature,
                    witness_lct
                )
                if not result.valid:
                    logger.warning(f"Invalid witness signature from {witness_lct}")
                    return False
            except SignatureVerificationError as e:
                logger.warning(f"Witness signature verification failed: {e}")
                return False

        return True

    def _validate_delegation_chain(
        self,
        delegator_lct: str,
        parent_delegation_id: str,
        granted_claim_hashes: List[str]
    ) -> bool:
        """
        Validate delegation chain for sub-delegations.

        Args:
            delegator_lct: Sub-delegator LCT
            parent_delegation_id: Parent delegation
            granted_claim_hashes: Claims being sub-delegated

        Returns:
            True if chain is valid
        """
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            # Get parent delegation
            cursor.execute("""
                SELECT
                    delegatee_lct,
                    granted_claim_hashes,
                    status,
                    valid_until
                FROM agent_delegations
                WHERE delegation_id = %s
            """, (parent_delegation_id,))

            parent = cursor.fetchone()
            if not parent:
                logger.warning(f"Parent delegation {parent_delegation_id} not found")
                return False

            # Check parent is still active
            if parent['status'] != 'active':
                logger.warning(f"Parent delegation {parent_delegation_id} not active")
                return False

            # Check parent not expired
            if parent['valid_until'] < datetime.now(timezone.utc):
                logger.warning(f"Parent delegation {parent_delegation_id} expired")
                return False

            # Check delegator is the delegatee of parent
            if parent['delegatee_lct'] != delegator_lct:
                logger.warning(
                    f"Delegator {delegator_lct} not delegatee of parent {parent_delegation_id}"
                )
                return False

            # Check granted claims are subset of parent granted claims
            parent_claims = set(parent['granted_claim_hashes'])
            for claim_hash in granted_claim_hashes:
                if claim_hash not in parent_claims:
                    logger.warning(
                        f"Claim {claim_hash} not in parent delegation"
                    )
                    return False

            return True

        finally:
            cursor.close()
            conn.close()

    def _check_delegation_rate_limit(
        self,
        delegator_lct: str,
        max_delegations_per_hour: int = 100
    ) -> bool:
        """
        Check delegation creation rate limit.

        Args:
            delegator_lct: Delegator LCT
            max_delegations_per_hour: Max delegations per hour

        Returns:
            True if within rate limit
        """
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            # Count delegations in last hour
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM agent_delegations
                WHERE delegator_lct = %s
                AND created_at >= NOW() - INTERVAL '1 hour'
            """, (delegator_lct,))

            result = cursor.fetchone()
            count = result['count']

            if count >= max_delegations_per_hour:
                logger.warning(
                    f"Delegation rate limit exceeded: {delegator_lct} created {count} delegations in last hour"
                )
                return False

            return True

        finally:
            cursor.close()
            conn.close()

    def _get_lct_public_key(self, lct_id: str) -> Optional[bytes]:
        """
        Get public key for LCT from database.

        Args:
            lct_id: LCT identifier

        Returns:
            Public key bytes, or None if not found
        """
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT public_key
                FROM lct_identities
                WHERE lct_id = %s
            """, (lct_id,))

            result = cursor.fetchone()
            if not result:
                return None

            # Public key is stored as text in database
            # Convert to bytes for cryptography
            public_key_str = result['public_key']
            if isinstance(public_key_str, str):
                # Assume hex-encoded or base64
                try:
                    return bytes.fromhex(public_key_str)
                except ValueError:
                    # Try base64
                    import base64
                    return base64.b64decode(public_key_str)
            else:
                return public_key_str

        finally:
            cursor.close()
            conn.close()

    def _log_validation_success(
        self,
        delegation_id: str,
        delegator_lct: str,
        delegatee_lct: str
    ):
        """
        Log successful delegation validation.

        Args:
            delegation_id: Delegation identifier
            delegator_lct: Delegator LCT
            delegatee_lct: Delegatee LCT
        """
        logger.info(
            f"Delegation validated: {delegation_id} "
            f"from {delegator_lct} to {delegatee_lct}"
        )

        # Store in audit log
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO delegation_audit_log
                (delegation_id, delegator_lct, delegatee_lct, event_type, event_data, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                delegation_id,
                delegator_lct,
                delegatee_lct,
                'validation_success',
                json.dumps({'status': 'validated'})
            ))
            conn.commit()
        except psycopg2.Error as e:
            # Table might not exist yet, log warning
            logger.warning(f"Could not write to audit log: {e}")
        finally:
            cursor.close()
            conn.close()

    def _log_validation_failure(
        self,
        delegation_id: str,
        delegator_lct: str,
        delegatee_lct: str,
        error: str
    ):
        """
        Log failed delegation validation.

        Args:
            delegation_id: Delegation identifier
            delegator_lct: Delegator LCT
            delegatee_lct: Delegatee LCT
            error: Error message
        """
        logger.warning(
            f"Delegation validation failed: {delegation_id} "
            f"from {delegator_lct} to {delegatee_lct}: {error}"
        )

        # Store in audit log
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO delegation_audit_log
                (delegation_id, delegator_lct, delegatee_lct, event_type, event_data, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                delegation_id,
                delegator_lct,
                delegatee_lct,
                'validation_failure',
                json.dumps({'error': error})
            ))
            conn.commit()
        except psycopg2.Error as e:
            # Table might not exist yet, log warning
            logger.warning(f"Could not write to audit log: {e}")
        finally:
            cursor.close()
            conn.close()


# Example usage
if __name__ == "__main__":
    print("Delegation Validator - Session #59 P1 Security Fix")
    print("=" * 60)

    # Database configuration
    db_config = {
        'dbname': 'web4',
        'user': 'postgres',
        'host': 'localhost'
    }

    # Create validator
    validator = DelegationValidator(db_config=db_config)

    # Example validation
    print("\nExample: Validate delegation")
    print("-" * 60)

    # Test delegation data
    delegation_id = "deleg:test:001"
    delegator = "lct:admin:test"
    delegatee = "lct:agent:test"
    org_id = "org:test:001"
    claims = ["claim:read:data", "claim:write:data"]
    signature = "mock_signature_for_testing"

    valid, error = validator.validate_delegation(
        delegation_id=delegation_id,
        delegator_lct=delegator,
        delegatee_lct=delegatee,
        organization_id=org_id,
        granted_claim_hashes=claims,
        delegation_signature=signature
    )

    print(f"Validation result: {valid}")
    if error:
        print(f"Error: {error}")

    print("\n" + "=" * 60)
    print("Delegation validator ready for integration")
    print("\nSecurity features implemented:")
    print("✅ Signature verification")
    print("✅ Permission chain validation")
    print("✅ Witness signature validation")
    print("✅ Delegation chain validation (sub-delegation)")
    print("✅ Rate limiting")
    print("✅ Audit logging")
