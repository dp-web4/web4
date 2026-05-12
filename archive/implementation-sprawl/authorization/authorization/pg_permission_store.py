"""
Web4 Authorization System - PostgreSQL Permission Store
========================================================

Persistent storage implementation for permission claims and delegations using PostgreSQL.

Replaces the in-memory PermissionStore with a database-backed implementation
that supports:
- Persistent permission claims
- Agent delegations with ATP tracking
- Delegation chains (sub-delegation)
- Automatic revocation on trust score drops
- Comprehensive audit trails

Session #52: AI Agent Authorization & Delegation System
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import List, Optional, Dict, Set
from datetime import datetime, timezone
import hashlib
import json
from contextlib import contextmanager

# Import from existing authorization system
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from permission_claim import PermissionClaim, PermissionStatus


class PostgreSQLPermissionStore:
    """
    PostgreSQL-backed storage for permission claims.

    Provides persistent storage with:
    - Atomic transactions
    - Foreign key integrity
    - Indexed queries for performance
    - Automatic timestamps
    - Audit trail via triggers
    """

    def __init__(self, connection_string: str):
        """
        Initialize PostgreSQL connection.

        Args:
            connection_string: PostgreSQL connection string
                Example: "host=localhost dbname=web4_auth user=web4 password=***"
        """
        self.connection_string = connection_string
        self._ensure_schema()

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self):
        """Ensure database schema exists (idempotent)"""
        # In production, schema should be created separately via migration
        # This is a convenience for development
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_path.read_text())

    def store_claim(self, claim: PermissionClaim) -> bool:
        """
        Store a permission claim in the database.

        Args:
            claim: PermissionClaim to store

        Returns:
            True if stored successfully, False if duplicate
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Check for duplicate
                cur.execute(
                    "SELECT claim_hash FROM permission_claims WHERE claim_hash = %s",
                    (claim.claim_hash,)
                )
                if cur.fetchone():
                    return False  # Already exists

                # Insert claim
                cur.execute("""
                    INSERT INTO permission_claims (
                        claim_hash, claim_id, subject_lct, issuer_lct, organization_id,
                        permission_action, resource_pattern, resource_scope,
                        signature, witness_signatures,
                        status, issued_at, expires_at,
                        description, conditions, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s, %s
                    )
                """, (
                    claim.claim_hash,
                    claim.claim_id,
                    claim.subject_lct,
                    claim.issuer_lct,
                    claim.organization,
                    claim.permission,
                    claim.resource,
                    claim.scope,
                    claim.signature,
                    Json(claim.witness_signatures) if claim.witness_signatures else Json([]),
                    claim.status.value,
                    claim.issued_at,
                    claim.expires_at,
                    claim.description,
                    Json(claim.conditions) if claim.conditions else Json({}),
                    Json(claim.metadata) if claim.metadata else Json({})
                ))

                return True

    def get_claims(self, subject_lct: str, organization: str) -> List[PermissionClaim]:
        """
        Get all active claims for a subject in an organization.

        Args:
            subject_lct: Subject's LCT identifier
            organization: Organization context

        Returns:
            List of PermissionClaim objects
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT *
                    FROM permission_claims
                    WHERE subject_lct = %s
                      AND organization_id = %s
                      AND status = 'active'
                      AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                    ORDER BY issued_at DESC
                """, (subject_lct, organization))

                rows = cur.fetchall()
                return [self._row_to_claim(row) for row in rows]

    def get_claim(self, claim_hash: str) -> Optional[PermissionClaim]:
        """
        Get a specific claim by hash.

        Args:
            claim_hash: SHA256 hash of claim

        Returns:
            PermissionClaim or None if not found
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM permission_claims WHERE claim_hash = %s",
                    (claim_hash,)
                )
                row = cur.fetchone()
                return self._row_to_claim(row) if row else None

    def update_claim(self, claim: PermissionClaim):
        """
        Update an existing claim.

        Args:
            claim: Updated PermissionClaim
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE permission_claims
                    SET status = %s,
                        expires_at = %s,
                        revoked_at = %s,
                        revocation_reason = %s,
                        witness_signatures = %s,
                        conditions = %s,
                        metadata = %s
                    WHERE claim_hash = %s
                """, (
                    claim.status.value,
                    claim.expires_at,
                    claim.revoked_at,
                    claim.revocation_reason,
                    Json(claim.witness_signatures) if claim.witness_signatures else Json([]),
                    Json(claim.conditions) if claim.conditions else Json({}),
                    Json(claim.metadata) if claim.metadata else Json({}),
                    claim.claim_hash
                ))

    def revoke_claim(self, claim_hash: str, reason: str, revoker_lct: str = "system") -> bool:
        """
        Revoke a permission claim.

        Args:
            claim_hash: Hash of claim to revoke
            reason: Reason for revocation
            revoker_lct: LCT of entity revoking (default: system)

        Returns:
            True if revoked, False if not found
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Check if claim exists and is active
                cur.execute(
                    "SELECT status FROM permission_claims WHERE claim_hash = %s",
                    (claim_hash,)
                )
                row = cur.fetchone()
                if not row:
                    return False

                if row['status'] == 'revoked':
                    return True  # Already revoked

                # Revoke the claim
                cur.execute("""
                    UPDATE permission_claims
                    SET status = 'revoked',
                        revoked_at = CURRENT_TIMESTAMP,
                        revocation_reason = %s
                    WHERE claim_hash = %s
                """, (reason, claim_hash))

                # Trigger will automatically log to revocation_events
                return True

    def _row_to_claim(self, row: Dict) -> PermissionClaim:
        """Convert database row to PermissionClaim object"""
        return PermissionClaim(
            subject_lct=row['subject_lct'],
            permission=row['permission_action'],
            resource=row['resource_pattern'],
            scope=row['resource_scope'],
            issuer_lct=row['issuer_lct'],
            organization=row['organization_id'],
            description=row['description'],
            conditions=row['conditions'] if row['conditions'] else {},
            metadata=row['metadata'] if row['metadata'] else {},
            claim_id=row['claim_id'],
            issued_at=row['issued_at'],
            expires_at=row['expires_at'],
            signature=row['signature'],
            witness_signatures=row['witness_signatures'] if row['witness_signatures'] else [],
            status=PermissionStatus(row['status']),
            revoked_at=row['revoked_at'],
            revocation_reason=row['revocation_reason'],
            claim_hash=row['claim_hash']
        )


class PostgreSQLDelegationStore:
    """
    PostgreSQL-backed storage for agent delegations.

    Manages:
    - Delegation creation and tracking
    - ATP budget management
    - Rate limiting per delegation
    - Delegation chains (sub-delegation)
    - Action audit trail
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_delegation(
        self,
        delegation_id: str,
        delegator_lct: str,
        delegatee_lct: str,
        organization_id: str,
        granted_claim_hashes: List[str],
        atp_budget: int,
        valid_from: datetime,
        valid_until: datetime,
        delegation_signature: str,
        role_lct: Optional[str] = None,
        parent_delegation_id: Optional[str] = None,
        max_actions_per_hour: int = 100,
        description: Optional[str] = None,
        constraints: Optional[Dict] = None,
        witness_signatures: Optional[List[Dict]] = None
    ) -> bool:
        """
        Create a new agent delegation.

        Args:
            delegation_id: Unique delegation identifier
            delegator_lct: Principal delegating authority
            delegatee_lct: Agent receiving authority
            organization_id: Organization context
            granted_claim_hashes: List of permission claim hashes
            atp_budget: Total ATP budget allocated
            valid_from: Start of validity period
            valid_until: End of validity period
            delegation_signature: Delegator's signature
            role_lct: Optional role identity
            parent_delegation_id: For sub-delegations
            max_actions_per_hour: Rate limit
            description: Human-readable description
            constraints: Additional constraints
            witness_signatures: Required witnesses

        Returns:
            True if created successfully
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Check for self-delegation
                if delegator_lct == delegatee_lct:
                    raise ValueError("Cannot delegate to self")

                # Insert delegation
                cur.execute("""
                    INSERT INTO agent_delegations (
                        delegation_id, delegator_lct, delegatee_lct,
                        parent_delegation_id, role_lct, organization_id,
                        granted_claim_hashes, atp_budget_total,
                        max_actions_per_hour, valid_from, valid_until,
                        delegation_signature, witness_signatures,
                        description, constraints
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s
                    )
                """, (
                    delegation_id, delegator_lct, delegatee_lct,
                    parent_delegation_id, role_lct, organization_id,
                    Json(granted_claim_hashes), atp_budget,
                    max_actions_per_hour, valid_from, valid_until,
                    delegation_signature, Json(witness_signatures or []),
                    description, Json(constraints or {})
                ))

                return True

    def get_delegation(self, delegation_id: str) -> Optional[Dict]:
        """Get delegation by ID"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM active_delegations WHERE delegation_id = %s",
                    (delegation_id,)
                )
                return dict(cur.fetchone()) if cur.rowcount > 0 else None

    def get_delegations_by_delegatee(
        self,
        delegatee_lct: str,
        organization_id: Optional[str] = None
    ) -> List[Dict]:
        """Get all active delegations for a delegatee"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if organization_id:
                    cur.execute("""
                        SELECT * FROM active_delegations
                        WHERE delegatee_lct = %s AND organization_id = %s
                        ORDER BY valid_until DESC
                    """, (delegatee_lct, organization_id))
                else:
                    cur.execute("""
                        SELECT * FROM active_delegations
                        WHERE delegatee_lct = %s
                        ORDER BY valid_until DESC
                    """, (delegatee_lct,))

                return [dict(row) for row in cur.fetchall()]

    def consume_atp(self, delegation_id: str, cost: int) -> bool:
        """
        Consume ATP from delegation budget.

        Args:
            delegation_id: Delegation to consume from
            cost: ATP cost to consume

        Returns:
            True if consumed successfully, False if insufficient budget
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Check budget availability
                cur.execute("""
                    SELECT atp_budget_total, atp_budget_spent
                    FROM agent_delegations
                    WHERE delegation_id = %s AND status = 'active'
                """, (delegation_id,))

                row = cur.fetchone()
                if not row:
                    return False

                remaining = row['atp_budget_total'] - row['atp_budget_spent']
                if remaining < cost:
                    return False

                # Consume ATP
                cur.execute("""
                    UPDATE agent_delegations
                    SET atp_budget_spent = atp_budget_spent + %s
                    WHERE delegation_id = %s
                """, (cost, delegation_id))

                return True

    def record_action(
        self,
        delegation_id: str,
        delegatee_lct: str,
        action_type: str,
        target_resource: str,
        atp_cost: int,
        authorized: bool,
        denial_reason: Optional[str] = None,
        request_context: Optional[Dict] = None,
        result_metadata: Optional[Dict] = None
    ):
        """
        Record an action in the audit trail.

        Args:
            delegation_id: Delegation under which action was performed
            delegatee_lct: Agent performing action
            action_type: Type of action (R6 action or custom)
            target_resource: Resource being acted upon
            atp_cost: ATP consumed
            authorized: Whether action was authorized
            denial_reason: If denied, why
            request_context: Additional request context
            result_metadata: Additional result metadata
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO delegation_actions (
                        delegation_id, delegatee_lct,
                        action_type, target_resource, atp_cost,
                        authorized, denial_reason,
                        request_context, result_metadata
                    ) VALUES (
                        %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s
                    )
                """, (
                    delegation_id, delegatee_lct,
                    action_type, target_resource, atp_cost,
                    authorized, denial_reason,
                    Json(request_context or {}), Json(result_metadata or {})
                ))

    def revoke_delegation(self, delegation_id: str, reason: str, revoker_lct: str = "system") -> bool:
        """Revoke a delegation"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE agent_delegations
                    SET status = 'revoked',
                        revoked_at = CURRENT_TIMESTAMP,
                        revocation_reason = %s
                    WHERE delegation_id = %s AND status = 'active'
                """, (reason, delegation_id))

                # Trigger will log to revocation_events
                return cur.rowcount > 0

    def get_delegation_chain(self, delegation_id: str) -> List[Dict]:
        """
        Get full delegation chain for a delegation.

        Returns list from root delegator to final delegatee.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT *
                    FROM delegation_chains
                    WHERE delegation_id = %s
                    ORDER BY depth ASC
                """, (delegation_id,))

                return [dict(row) for row in cur.fetchall()]


class PostgreSQLReputationService:
    """
    PostgreSQL-backed reputation (T3) service.

    Manages trust tensor scores and automatic reputation updates.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_t3(self, lct_id: str, organization: str = "org:web4:default") -> float:
        """Get T3 score for an entity in an organization"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t3_score
                    FROM reputation_scores
                    WHERE lct_id = %s AND organization_id = %s
                """, (lct_id, organization))

                row = cur.fetchone()
                return float(row['t3_score']) if row else 0.0

    def set_t3(
        self,
        lct_id: str,
        talent: float,
        training: float,
        temperament: float,
        organization: str = "org:web4:default"
    ):
        """Set T3 component scores (computed T3 is calculated by database)"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO reputation_scores (
                        lct_id, organization_id,
                        talent_score, training_score, temperament_score
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (lct_id, organization_id)
                    DO UPDATE SET
                        talent_score = EXCLUDED.talent_score,
                        training_score = EXCLUDED.training_score,
                        temperament_score = EXCLUDED.temperament_score,
                        last_updated = CURRENT_TIMESTAMP
                """, (lct_id, organization, talent, training, temperament))

    def update_from_action(
        self,
        lct_id: str,
        organization: str,
        success: bool,
        action_type: str
    ):
        """Update reputation based on action outcome (calls database function)"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT update_reputation_from_action(%s, %s, %s, %s)
                """, (lct_id, organization, success, action_type))
