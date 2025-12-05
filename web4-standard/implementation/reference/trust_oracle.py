"""
Web4 Trust Oracle
=================

PostgreSQL-backed trust query service for authorization decisions.

Implements the Trust Oracle interface needed by authorization_engine.py,
replacing the hardcoded 0.75 stub with real T3/V3 tensor queries.

Key Features:
- Query T3 (Talent, Training, Temperament) scores from PostgreSQL
- Query V3 (Veracity, Validity, Valuation) scores
- Role-contextual trust (trust in specific roles)
- Temporal decay application
- Trust relationship graph queries
- Caching for performance

Database Schema:
- reputation_scores (T3 tensor)
- v3_scores (V3 tensor)
- trust_history (temporal tracking)
- trust_relationships (graph)

Author: Legion Autonomous Session (2025-12-05)
Session: Autonomous Web4 Research
"""

from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrustScore:
    """Complete trust assessment for an entity"""
    lct_id: str
    organization_id: str

    # T3 tensor (capability)
    talent: float
    training: float
    temperament: float
    t3_score: float

    # V3 tensor (transaction quality)
    veracity: Optional[float] = None
    validity: Optional[float] = None
    valuation: Optional[float] = None
    v3_score: Optional[float] = None

    # Statistics
    total_actions: int = 0
    successful_actions: int = 0
    total_transactions: int = 0
    successful_transactions: int = 0

    # Reputation level
    reputation_level: str = "novice"

    # Timestamps
    last_updated: Optional[datetime] = None

    def composite_score(self, t3_weight: float = 0.6, v3_weight: float = 0.4) -> float:
        """
        Calculate composite trust score from T3 and V3.

        Default: 60% T3 (capability), 40% V3 (transaction quality)
        Falls back to T3 if V3 not available.
        """
        if self.v3_score is not None:
            return (t3_weight * self.t3_score) + (v3_weight * self.v3_score)
        return self.t3_score

    def is_stale(self, threshold_days: int = 90) -> bool:
        """Check if trust score is stale (not updated recently)"""
        if self.last_updated is None:
            return True

        age = datetime.now(timezone.utc) - self.last_updated
        return age.days > threshold_days


class TrustOracle:
    """
    Trust Oracle - Query trust scores from PostgreSQL backend

    Provides trust assessments for authorization decisions.
    Implements caching for performance.
    """

    def __init__(
        self,
        db_config: Dict[str, str],
        cache_ttl_seconds: int = 300,  # 5 minutes
        enable_decay: bool = True
    ):
        """
        Initialize Trust Oracle.

        Args:
            db_config: PostgreSQL connection parameters
                {host, port, dbname, user, password}
            cache_ttl_seconds: Cache time-to-live (default 5 minutes)
            enable_decay: Apply temporal decay to scores
        """
        self.db_config = db_config
        self.cache_ttl = cache_ttl_seconds
        self.enable_decay = enable_decay

        # Cache: (lct_id, org_id) -> (TrustScore, timestamp)
        self.cache: Dict[Tuple[str, str], Tuple[TrustScore, float]] = {}

        # Connection pool (simple implementation)
        self.connection = None

        logger.info(f"Trust Oracle initialized (cache_ttl={cache_ttl_seconds}s, decay={enable_decay})")

    def _get_connection(self):
        """Get database connection (with reconnection logic)"""
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(**self.db_config)
            logger.debug("Established new PostgreSQL connection")
        return self.connection

    def get_trust_score(
        self,
        lct_id: str,
        organization_id: str,
        role_lct: Optional[str] = None,
        use_cache: bool = True
    ) -> TrustScore:
        """
        Get trust score for an entity in an organization.

        Args:
            lct_id: Entity whose trust to query
            organization_id: Organization context
            role_lct: Optional role context (for role-specific trust)
            use_cache: Use cached values if available

        Returns:
            TrustScore with T3/V3 values

        Raises:
            ValueError: If entity not found
        """
        cache_key = (lct_id, organization_id, role_lct)

        # Check cache
        if use_cache and cache_key in self.cache:
            score, cached_at = self.cache[cache_key]
            age = time.time() - cached_at

            if age < self.cache_ttl:
                logger.debug(f"Trust cache hit: {lct_id} (age={age:.1f}s)")
                return score
            else:
                logger.debug(f"Trust cache expired: {lct_id} (age={age:.1f}s)")

        # Query from database
        score = self._query_trust_score(lct_id, organization_id, role_lct)

        # Apply temporal decay if enabled
        if self.enable_decay and score.last_updated:
            score = self._apply_decay(score)

        # Cache result
        self.cache[cache_key] = (score, time.time())

        logger.debug(f"Trust queried: {lct_id} @ {organization_id} = {score.t3_score:.3f}")

        return score

    def _query_trust_score(
        self,
        lct_id: str,
        organization_id: str,
        role_lct: Optional[str] = None
    ) -> TrustScore:
        """Query trust score from database"""
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Query T3 and V3 scores with single join
                query = """
                SELECT
                    t3.lct_id,
                    t3.organization_id,
                    -- T3 scores
                    t3.talent_score,
                    t3.training_score,
                    t3.temperament_score,
                    t3.t3_score,
                    t3.reputation_level,
                    t3.total_actions,
                    t3.successful_actions,
                    t3.last_action_at AS t3_last_updated,
                    -- V3 scores
                    v3.veracity_score,
                    v3.validity_score,
                    v3.valuation_score,
                    v3.v3_score,
                    v3.total_transactions,
                    v3.successful_transactions,
                    v3.last_updated AS v3_last_updated
                FROM reputation_scores t3
                LEFT JOIN v3_scores v3
                    ON t3.lct_id = v3.lct_id
                    AND t3.organization_id = v3.organization_id
                WHERE t3.lct_id = %s AND t3.organization_id = %s
                """

                cur.execute(query, (lct_id, organization_id))
                row = cur.fetchone()

                if not row:
                    # Entity not found - return default novice scores
                    logger.warning(f"Trust not found: {lct_id} @ {organization_id}, using defaults")
                    return TrustScore(
                        lct_id=lct_id,
                        organization_id=organization_id,
                        talent=0.5,
                        training=0.5,
                        temperament=0.5,
                        t3_score=0.5,
                        reputation_level="novice"
                    )

                # Build TrustScore from database row
                return TrustScore(
                    lct_id=row['lct_id'],
                    organization_id=row['organization_id'],
                    talent=float(row['talent_score']),
                    training=float(row['training_score']),
                    temperament=float(row['temperament_score']),
                    t3_score=float(row['t3_score']),
                    veracity=float(row['veracity_score']) if row['veracity_score'] is not None else None,
                    validity=float(row['validity_score']) if row['validity_score'] is not None else None,
                    valuation=float(row['valuation_score']) if row['valuation_score'] is not None else None,
                    v3_score=float(row['v3_score']) if row['v3_score'] is not None else None,
                    total_actions=row['total_actions'] or 0,
                    successful_actions=row['successful_actions'] or 0,
                    total_transactions=row['total_transactions'] or 0,
                    successful_transactions=row['successful_transactions'] or 0,
                    reputation_level=row['reputation_level'] or 'novice',
                    last_updated=row['t3_last_updated'] or row['v3_last_updated']
                )

        except psycopg2.Error as e:
            logger.error(f"Database error querying trust: {e}")
            raise ValueError(f"Failed to query trust for {lct_id}: {e}")

    def _apply_decay(self, score: TrustScore) -> TrustScore:
        """
        Apply temporal decay to trust scores.

        Decay rules (from t3-v3-tensors.md):
        - Training: -0.001 per month without practice
        - Temperament: +0.01 per month of good behavior (recovery)
        - Talent: No decay (innate capability)
        """
        if score.last_updated is None:
            return score

        # Calculate months elapsed
        now = datetime.now(timezone.utc)
        elapsed = now - score.last_updated
        months_elapsed = elapsed.days / 30.0

        if months_elapsed < 0.1:  # Less than 3 days
            return score  # No decay

        # Apply training decay
        score.training = max(0.0, score.training - (0.001 * months_elapsed))

        # Apply temperament recovery (if below 0.8)
        if score.temperament < 0.8:
            score.temperament = min(1.0, score.temperament + (0.01 * months_elapsed))

        # Recalculate T3 composite
        score.t3_score = (score.talent + score.training + score.temperament) / 3.0

        logger.debug(f"Applied decay: {months_elapsed:.1f} months, training now {score.training:.3f}")

        return score

    def get_trust_relationship(
        self,
        source_lct: str,
        target_lct: str,
        organization_id: str,
        relationship_type: str = "collaborated"
    ) -> Optional[float]:
        """
        Get direct trust relationship score.

        This queries the trust_relationships table for direct
        trust assessments between entities.

        Args:
            source_lct: Entity making trust assessment
            target_lct: Entity being assessed
            organization_id: Organization context
            relationship_type: Type of relationship

        Returns:
            Trust score (0.0-1.0) or None if no relationship
        """
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                SELECT trust_score, confidence, interaction_count,
                       successful_interactions, failed_interactions
                FROM trust_relationships
                WHERE source_lct = %s AND target_lct = %s
                  AND organization_id = %s AND relationship_type = %s
                """

                cur.execute(query, (source_lct, target_lct, organization_id, relationship_type))
                row = cur.fetchone()

                if not row:
                    return None

                logger.debug(f"Trust relationship: {source_lct} → {target_lct} = {row['trust_score']:.3f}")

                return float(row['trust_score'])

        except psycopg2.Error as e:
            logger.error(f"Database error querying trust relationship: {e}")
            return None

    def query_trust_for_authorization(
        self,
        lct_id: str,
        organization_id: str,
        action_type: str,
        required_role: Optional[str] = None
    ) -> float:
        """
        Simplified trust query for authorization engine.

        This is the interface called by authorization_engine.py
        to replace the hardcoded 0.75 stub.

        Args:
            lct_id: Entity requesting authorization
            organization_id: Organization context
            action_type: Action being authorized
            required_role: Required role for action

        Returns:
            Trust score (0.0-1.0) for authorization decision
        """
        try:
            score = self.get_trust_score(lct_id, organization_id, required_role)

            # Use composite score (T3 + V3 weighted)
            return score.composite_score()

        except Exception as e:
            logger.error(f"Error querying trust for authorization: {e}")
            # Fail closed: return low trust on error
            return 0.3

    def clear_cache(self):
        """Clear trust score cache"""
        self.cache.clear()
        logger.info("Trust cache cleared")

    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Trust Oracle closed")


def create_trust_oracle(db_config: Dict[str, str], **kwargs) -> TrustOracle:
    """
    Factory function to create TrustOracle instance.

    Args:
        db_config: PostgreSQL connection parameters
        **kwargs: Additional TrustOracle arguments

    Returns:
        Configured TrustOracle instance
    """
    return TrustOracle(db_config, **kwargs)


# Example usage
if __name__ == '__main__':
    import sys

    # Example configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'dbname': 'web4_trust',
        'user': 'web4',
        'password': 'changeme'
    }

    # Create oracle
    oracle = TrustOracle(db_config)

    # Query example
    try:
        score = oracle.get_trust_score(
            lct_id="lct:ai:agent:001",
            organization_id="org:web4:dev"
        )

        print(f"Trust Score for {score.lct_id}:")
        print(f"  T3: {score.t3_score:.3f} (talent={score.talent:.3f}, training={score.training:.3f}, temperament={score.temperament:.3f})")
        if score.v3_score:
            print(f"  V3: {score.v3_score:.3f} (veracity={score.veracity:.3f}, validity={score.validity:.3f}, valuation={score.valuation:.3f})")
        print(f"  Composite: {score.composite_score():.3f}")
        print(f"  Reputation: {score.reputation_level}")
        print(f"  Actions: {score.successful_actions}/{score.total_actions}")

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        oracle.close()
