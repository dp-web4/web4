#!/usr/bin/env python3
"""
Trust API
Session #56: Python API for trust score management with batching

Provides high-level Python API for trust score updates, using the TrustUpdateBatcher
for performance optimization.

Architecture:
- TrustAPI: Main API class, wraps batcher and provides convenience methods
- Integrates with existing SQL functions (update_reputation_from_action, etc.)
- Automatic batching reduces database load by 10-60x
- Thread-safe for multi-agent environments
"""

import psycopg2
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum

from trust_update_batcher import TrustUpdateBatcher


class ActionType(Enum):
    """Action types for reputation updates"""
    CODE_COMMIT = "code_commit"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    GENERIC = "generic"


class TrustAPI:
    """
    Python API for trust score management.

    Features:
    - Automatic batching for performance (10-60x improvement)
    - T3 and V3 score updates
    - Integration with existing SQL functions
    - Thread-safe operations
    - Statistics and monitoring
    """

    def __init__(self,
                 db_config: dict,
                 flush_interval_seconds: int = 60,
                 max_batch_size: int = 100,
                 auto_start: bool = True):
        """
        Initialize trust API.

        Args:
            db_config: PostgreSQL connection config
            flush_interval_seconds: Seconds between automatic flushes (default: 60)
            max_batch_size: Maximum updates before forcing flush (default: 100)
            auto_start: Start background flush thread automatically
        """
        self.db_config = db_config
        self.batcher = TrustUpdateBatcher(
            db_config=db_config,
            flush_interval_seconds=flush_interval_seconds,
            max_batch_size=max_batch_size,
            auto_start=auto_start
        )

    def start(self):
        """Start background flush thread"""
        self.batcher.start()

    def stop(self):
        """Stop background flush thread and flush pending updates"""
        self.batcher.stop()

    def record_action(self,
                     lct_id: str,
                     org_id: str,
                     action_type: str,
                     success: bool,
                     custom_deltas: Optional[Dict[str, Decimal]] = None):
        """
        Record an action and update T3 reputation scores.

        Args:
            lct_id: LCT identity of the agent
            org_id: Organization ID
            action_type: Type of action (code_commit, code_review, etc.)
            success: Whether the action succeeded
            custom_deltas: Custom T3 deltas (overrides defaults)

        Default deltas for successful actions:
            - talent_delta: +0.001
            - training_delta: +0.002
            - temperament_delta: +0.001

        Failed actions: -0.5x the success deltas
        """
        if custom_deltas:
            talent_delta = custom_deltas.get('talent', Decimal('0.0'))
            training_delta = custom_deltas.get('training', Decimal('0.0'))
            temperament_delta = custom_deltas.get('temperament', Decimal('0.0'))
        else:
            # Default deltas based on action type and success
            if success:
                talent_delta = Decimal('0.001')
                training_delta = Decimal('0.002')
                temperament_delta = Decimal('0.001')
            else:
                # Penalize failed actions
                talent_delta = Decimal('-0.0005')
                training_delta = Decimal('-0.001')
                temperament_delta = Decimal('-0.0005')

        self.batcher.record_t3_update(
            lct_id=lct_id,
            org_id=org_id,
            talent_delta=talent_delta,
            training_delta=training_delta,
            temperament_delta=temperament_delta
        )

    def record_transaction(self,
                          lct_id: str,
                          org_id: str,
                          transaction_type: str,
                          value: Decimal,
                          verified: bool,
                          custom_deltas: Optional[Dict[str, Decimal]] = None):
        """
        Record a transaction and update V3 trust scores.

        Args:
            lct_id: LCT identity of the agent
            org_id: Organization ID
            transaction_type: Type of transaction
            value: Transaction value (ATP or other currency)
            verified: Whether the transaction was verified
            custom_deltas: Custom V3 deltas (overrides defaults)

        Default deltas:
            - veracity_delta: +0.01 if verified, -0.005 if not
            - validity_delta: +0.01 for valid transactions
            - valuation_delta: Based on transaction value (normalized)
        """
        if custom_deltas:
            veracity_delta = custom_deltas.get('veracity', Decimal('0.0'))
            validity_delta = custom_deltas.get('validity', Decimal('0.0'))
            valuation_delta = custom_deltas.get('valuation', Decimal('0.0'))
        else:
            # Default deltas
            if verified:
                veracity_delta = Decimal('0.01')
            else:
                veracity_delta = Decimal('-0.005')

            validity_delta = Decimal('0.01')

            # Valuation delta based on transaction value
            # Normalize to reasonable range (assuming ATP value 0-1000)
            normalized_value = min(float(value) / 1000.0, 1.0)
            valuation_delta = Decimal(str(normalized_value * 0.01))

        self.batcher.record_v3_update(
            lct_id=lct_id,
            org_id=org_id,
            veracity_delta=veracity_delta,
            validity_delta=validity_delta,
            valuation_delta=valuation_delta
        )

    def flush(self):
        """
        Manually flush all pending updates to database.

        Useful for testing or when immediate persistence is required.
        """
        self.batcher.flush()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get batcher statistics.

        Returns:
            Dictionary with:
                - total_updates_recorded: Total updates recorded
                - total_flushes: Total number of flushes
                - total_entities_flushed: Total entities flushed
                - pending_updates: Current pending update count
                - last_flush_time: Timestamp of last flush
                - flush_errors: Number of flush errors
        """
        return self.batcher.get_stats()

    def get_pending_count(self) -> int:
        """Get count of pending updates"""
        return self.batcher.get_pending_count()

    def get_t3_scores(self, lct_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Get T3 reputation scores for an entity.

        Args:
            lct_id: LCT identity
            org_id: Organization ID

        Returns:
            Dictionary with:
                - talent_score: Talent score (0-1)
                - training_score: Training score (0-1)
                - temperament_score: Temperament score (0-1)
                - t3_score: Overall T3 score (0-1)
                - total_actions: Total actions recorded
                - last_updated: Last update timestamp
        """
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT talent_score, training_score, temperament_score,
                       t3_score, total_actions, last_updated
                FROM reputation_scores
                WHERE lct_id = %s AND organization_id = %s
            """, (lct_id, org_id))

            row = cursor.fetchone()

            if not row:
                return None

            return {
                'talent_score': row[0],
                'training_score': row[1],
                'temperament_score': row[2],
                't3_score': row[3],
                'total_actions': row[4],
                'last_updated': row[5]
            }

        finally:
            cursor.close()
            conn.close()

    def get_v3_scores(self, lct_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Get V3 trust scores for an entity.

        Args:
            lct_id: LCT identity
            org_id: Organization ID

        Returns:
            Dictionary with:
                - veracity_score: Veracity score (0-1)
                - validity_score: Validity score (0-1)
                - valuation_score: Valuation score (0-1)
                - v3_score: Overall V3 score (0-1)
                - total_transactions: Total transactions recorded
                - last_updated: Last update timestamp
        """
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT veracity_score, validity_score, valuation_score,
                       v3_score, total_transactions, last_updated
                FROM v3_scores
                WHERE lct_id = %s AND organization_id = %s
            """, (lct_id, org_id))

            row = cursor.fetchone()

            if not row:
                return None

            return {
                'veracity_score': row[0],
                'validity_score': row[1],
                'valuation_score': row[2],
                'v3_score': row[3],
                'total_transactions': row[4],
                'last_updated': row[5]
            }

        finally:
            cursor.close()
            conn.close()


# Example usage
if __name__ == "__main__":
    # Database configuration
    db_config = {
        'dbname': 'web4',
        'user': 'postgres',
        'host': 'localhost'
    }

    # Create API
    api = TrustAPI(
        db_config=db_config,
        flush_interval_seconds=60,
        max_batch_size=100
    )

    print("Trust API initialized")
    print(f"Flush interval: 60 seconds")
    print(f"Max batch size: 100 updates")

    # Record some actions
    print("\nRecording 10 successful actions...")
    for i in range(10):
        api.record_action(
            lct_id=f"lct:ai:example:00{i}",
            org_id="org:example:001",
            action_type="code_commit",
            success=True
        )

    # Record some transactions
    print("Recording 5 transactions...")
    for i in range(5):
        api.record_transaction(
            lct_id=f"lct:ai:example:00{i}",
            org_id="org:example:001",
            transaction_type="atp_transfer",
            value=Decimal('100.0'),
            verified=True
        )

    # Check stats
    stats = api.get_stats()
    print(f"\nAPI Statistics:")
    print(f"  Total updates recorded: {stats['total_updates_recorded']}")
    print(f"  Pending updates: {stats['pending_updates']}")
    print(f"  Total flushes: {stats['total_flushes']}")

    # Manual flush
    print("\nManually flushing...")
    api.flush()

    stats = api.get_stats()
    print(f"After flush:")
    print(f"  Pending updates: {stats['pending_updates']}")
    print(f"  Total entities flushed: {stats['total_entities_flushed']}")

    # Stop API
    api.stop()
    print("\nAPI stopped")
