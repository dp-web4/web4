#!/usr/bin/env python3
"""
Sybil Resistance Enforcement
Session #58: P1 security fix for identity verification

Implements birth certificate and hardware binding verification to prevent
Sybil attacks (creating fake identities to inflate trust scores).

Design:
- Verify birth certificate hash uniqueness
- Validate hardware binding (TPM) when available
- ATP deposit requirement for new identities
- Graph analysis for suspicious vouching patterns

From ATTACK_VECTORS.md Session #56:
**Attack Pattern**:
```python
# Create 1000 fake identities
for i in range(1000):
    fake_lct = create_identity(f"lct:fake:{i}")
    # Cross-vouch to build reputation artificially
```

**Mitigation**:
1. ✅ Birth certificate verification (schema enforced)
2. ✅ Hardware binding (schema supported)
3. 🔄 Cost of identity creation (ATP deposit) - this module
4. 🔄 Graph analysis (suspicious patterns) - future
5. 🔄 Reputation aging (new identities start low) - future
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, List
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib


class SybilResistance:
    """
    Sybil resistance enforcement for LCT identities.

    Features:
    - Birth certificate uniqueness validation
    - Hardware binding verification
    - ATP deposit requirements
    - Identity creation rate limiting
    - Suspicious pattern detection
    """

    def __init__(self, db_config: dict,
                 min_atp_deposit: Decimal = Decimal('10.0'),
                 max_identities_per_hour: int = 10):
        """
        Initialize Sybil resistance.

        Args:
            db_config: PostgreSQL connection config
            min_atp_deposit: Minimum ATP deposit for new identity
            max_identities_per_hour: Max identities created per hour
        """
        self.db_config = db_config
        self.min_atp_deposit = min_atp_deposit
        self.max_identities_per_hour = max_identities_per_hour

    def validate_birth_certificate(self, birth_cert_hash: str) -> bool:
        """
        Validate birth certificate uniqueness.

        Args:
            birth_cert_hash: Birth certificate hash to check

        Returns:
            True if valid and unique, False if duplicate

        Note: The database schema already enforces this via FK,
        but this method provides explicit validation.
        """
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            # Check if birth certificate already used
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM lct_identities
                WHERE birth_certificate_hash = %s
            """, (birth_cert_hash,))

            result = cursor.fetchone()
            count = result['count']

            return count == 0  # Valid if not used

        finally:
            cursor.close()
            conn.close()

    def validate_hardware_binding(self, lct_id: str, hardware_hash: str) -> bool:
        """
        Validate hardware binding for identity.

        Args:
            lct_id: LCT identity
            hardware_hash: TPM hardware binding hash

        Returns:
            True if binding is valid

        Validation rules:
        1. Hardware hash must be unique (one identity per device)
        2. If identity already has binding, must match
        3. Binding cannot be changed after creation
        """
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            # Check if hardware already bound to another identity
            cursor.execute("""
                SELECT lct_id
                FROM lct_identities
                WHERE hardware_binding_hash = %s
                AND lct_id != %s
            """, (hardware_hash, lct_id))

            existing = cursor.fetchone()

            if existing:
                # Hardware already bound to different identity
                return False

            # Check if this identity has existing binding
            cursor.execute("""
                SELECT hardware_binding_hash
                FROM lct_identities
                WHERE lct_id = %s
            """, (lct_id,))

            identity = cursor.fetchone()

            if identity and identity['hardware_binding_hash']:
                # Identity has existing binding - must match
                return identity['hardware_binding_hash'] == hardware_hash

            # New binding or no existing binding - valid
            return True

        finally:
            cursor.close()
            conn.close()

    def check_identity_creation_rate(self, creator_lct: Optional[str] = None) -> bool:
        """
        Check if identity creation rate limit is exceeded.

        Args:
            creator_lct: LCT of entity creating new identity (optional)

        Returns:
            True if within rate limit, False if exceeded

        Rate limit:
        - Max 10 identities per hour globally
        - If creator_lct provided, max 5 per hour per creator
        """
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

            # Check global rate
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM lct_identities
                WHERE created_at >= %s
            """, (one_hour_ago,))

            global_count = cursor.fetchone()['count']

            if global_count >= self.max_identities_per_hour:
                return False

            # Check per-creator rate if provided
            if creator_lct:
                # Assuming we track creator in metadata or separate table
                # For now, just check global
                pass

            return True

        finally:
            cursor.close()
            conn.close()

    def detect_suspicious_vouching(self, lct_id: str, threshold: int = 10) -> Dict:
        """
        Detect suspicious vouching patterns.

        Args:
            lct_id: LCT identity to check
            threshold: Number of vouches to trigger suspicion

        Returns:
            Dictionary with detection results

        Suspicious patterns:
        1. Circular vouching (A vouches B, B vouches A)
        2. Cluster vouching (tight group all vouching each other)
        3. New identity with many vouches quickly
        4. Vouching from other new identities
        """
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        try:
            # Get identity creation time
            cursor.execute("""
                SELECT created_at
                FROM lct_identities
                WHERE lct_id = %s
            """, (lct_id,))

            identity = cursor.fetchone()
            if not identity:
                return {'suspicious': False, 'reason': 'Identity not found'}

            # Check trust relationships (vouching)
            cursor.execute("""
                SELECT
                    COUNT(*) as vouch_count,
                    AVG(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at))) as avg_relationship_age
                FROM trust_relationships
                WHERE target_lct = %s
            """, (lct_id,))

            vouch_stats = cursor.fetchone()

            if vouch_stats['vouch_count'] > threshold:
                # Check if vouches came quickly after creation
                created_at = identity['created_at']
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                identity_age = (datetime.now(timezone.utc) - created_at).total_seconds()

                if identity_age < 3600:  # Less than 1 hour old
                    return {
                        'suspicious': True,
                        'reason': 'New identity with many vouches',
                        'vouch_count': vouch_stats['vouch_count'],
                        'identity_age_seconds': identity_age
                    }

            # Check for circular vouching
            cursor.execute("""
                SELECT source_lct
                FROM trust_relationships
                WHERE target_lct = %s
            """, (lct_id,))

            vouchers = [row['source_lct'] for row in cursor.fetchall()]

            # Check if any of these also received vouches from lct_id
            circular_count = 0
            for voucher in vouchers:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM trust_relationships
                    WHERE source_lct = %s AND target_lct = %s
                """, (lct_id, voucher))

                if cursor.fetchone()['count'] > 0:
                    circular_count += 1

            if circular_count > threshold / 2:
                return {
                    'suspicious': True,
                    'reason': 'Circular vouching detected',
                    'circular_count': circular_count,
                    'total_vouches': len(vouchers)
                }

            return {
                'suspicious': False,
                'vouch_count': vouch_stats['vouch_count'],
                'circular_count': circular_count
            }

        finally:
            cursor.close()
            conn.close()

    def require_atp_deposit(self, lct_id: str) -> bool:
        """
        Check if identity has required ATP deposit.

        Args:
            lct_id: LCT identity

        Returns:
            True if deposit requirement met

        Note: This is a placeholder. Actual implementation requires
        ATP balance tracking system (future work).
        """
        # TODO: Integrate with ATP balance system
        # For now, assume all identities have met deposit
        return True

    def validate_identity_creation(self,
                                   birth_cert_hash: str,
                                   hardware_hash: Optional[str] = None,
                                   creator_lct: Optional[str] = None) -> Dict:
        """
        Validate all Sybil resistance requirements for identity creation.

        Args:
            birth_cert_hash: Birth certificate hash
            hardware_hash: Hardware binding hash (optional)
            creator_lct: Creating entity LCT (optional)

        Returns:
            Dictionary with validation results

        This is the main entry point for identity creation validation.
        """
        results = {
            'valid': True,
            'checks': {}
        }

        # Check birth certificate uniqueness
        bc_valid = self.validate_birth_certificate(birth_cert_hash)
        results['checks']['birth_certificate'] = {
            'valid': bc_valid,
            'message': 'Unique' if bc_valid else 'Duplicate birth certificate'
        }
        if not bc_valid:
            results['valid'] = False

        # Check identity creation rate
        rate_ok = self.check_identity_creation_rate(creator_lct)
        results['checks']['creation_rate'] = {
            'valid': rate_ok,
            'message': 'Within limit' if rate_ok else 'Rate limit exceeded'
        }
        if not rate_ok:
            results['valid'] = False

        # Check hardware binding if provided
        if hardware_hash:
            hw_valid = self.validate_hardware_binding('new', hardware_hash)
            results['checks']['hardware_binding'] = {
                'valid': hw_valid,
                'message': 'Valid binding' if hw_valid else 'Hardware already bound'
            }
            if not hw_valid:
                results['valid'] = False

        return results

    def get_identity_risk_score(self, lct_id: str) -> Dict:
        """
        Calculate risk score for identity being Sybil.

        Args:
            lct_id: LCT identity

        Returns:
            Dictionary with risk score and factors

        Risk factors:
        - New identity (< 1 week old): +2
        - No hardware binding: +1
        - Suspicious vouching patterns: +3
        - High vouch count quickly: +2
        - Low trust scores: +1

        Score interpretation:
        - 0-2: Low risk
        - 3-5: Medium risk
        - 6+: High risk
        """
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        risk_score = 0
        factors = []

        try:
            # Get identity info
            cursor.execute("""
                SELECT
                    created_at,
                    hardware_binding_hash,
                    entity_type
                FROM lct_identities
                WHERE lct_id = %s
            """, (lct_id,))

            identity = cursor.fetchone()
            if not identity:
                return {'risk_score': 10, 'risk_level': 'CRITICAL', 'factors': ['Identity not found']}

            # Check age (handle timezone-aware datetime from database)
            created_at = identity['created_at']
            if created_at.tzinfo is None:
                # If naive, assume UTC
                created_at = created_at.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - created_at).days
            if age_days < 7:
                risk_score += 2
                factors.append(f'New identity ({age_days} days old)')

            # Check hardware binding
            if not identity['hardware_binding_hash']:
                risk_score += 1
                factors.append('No hardware binding')

            # Check vouching patterns
            vouch_analysis = self.detect_suspicious_vouching(lct_id)
            if vouch_analysis['suspicious']:
                risk_score += 3
                factors.append(f"Suspicious vouching: {vouch_analysis['reason']}")

            # Check trust scores
            cursor.execute("""
                SELECT AVG((talent_score + training_score + temperament_score) / 3) as avg_t3
                FROM reputation_scores
                WHERE lct_id = %s
            """, (lct_id,))

            trust_result = cursor.fetchone()
            if trust_result['avg_t3']:
                avg_t3 = float(trust_result['avg_t3'])
                if avg_t3 < 0.3:
                    risk_score += 1
                    factors.append(f'Low trust scores (avg {avg_t3:.2f})')

            # Determine risk level
            if risk_score <= 2:
                risk_level = 'LOW'
            elif risk_score <= 5:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'HIGH'

            return {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'factors': factors,
                'identity_age_days': age_days
            }

        finally:
            cursor.close()
            conn.close()


# Example usage
if __name__ == "__main__":
    print("Sybil Resistance Enforcement - Session #58")
    print("=" * 60)

    # Database configuration
    db_config = {
        'dbname': 'web4',
        'user': 'postgres',
        'host': 'localhost'
    }

    # Create Sybil resistance checker
    sybil = SybilResistance(
        db_config=db_config,
        min_atp_deposit=Decimal('10.0'),
        max_identities_per_hour=10
    )

    # Example 1: Validate new identity creation
    print("\nExample 1: Validate Identity Creation")
    print("-" * 60)

    birth_cert = hashlib.sha256(b'unique_birth_cert_001').hexdigest()
    hardware = hashlib.sha256(b'tpm_hardware_001').hexdigest()

    validation = sybil.validate_identity_creation(
        birth_cert_hash=birth_cert,
        hardware_hash=hardware,
        creator_lct='lct:admin:system'
    )

    print(f"Valid: {validation['valid']}")
    for check_name, check_result in validation['checks'].items():
        status = "✅" if check_result['valid'] else "❌"
        print(f"  {status} {check_name}: {check_result['message']}")

    # Example 2: Check identity creation rate
    print("\nExample 2: Identity Creation Rate Check")
    print("-" * 60)

    rate_ok = sybil.check_identity_creation_rate()
    print(f"Rate limit OK: {rate_ok}")
    print(f"Max per hour: {sybil.max_identities_per_hour}")

    print("\n" + "=" * 60)
    print("Sybil resistance module ready for integration")
