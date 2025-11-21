#!/usr/bin/env python3
"""
Trust Update Batcher
Session #56: Implementation of Session #53 Q11 design
Session #57: Added Merkle tree anchoring

Implements write-behind caching for trust updates to reduce database load by ~60x.

Design from SAGE_INTEGRATION_ANSWERS.md Q11:
- Accumulate trust updates in memory
- Flush periodically (60 seconds) or on batch size (100 updates)
- Single SQL UPDATE per entity (not one per action)
- Atomic batch updates (all or nothing)

Session #57 additions:
- Merkle tree generation for each flush
- Cryptographic audit trail
- Proof-of-inclusion support

Performance improvement:
- Without batching: 1000 actions = 1000 DB writes
- With batching (60s): 1000 actions = ~17 DB writes (one per minute)
- ~60x reduction in database load
"""

import threading
import time
import psycopg2
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal

# Merkle tree for anchoring
from trust_merkle_tree import TrustMerkleTree, TrustUpdateLeaf

@dataclass
class TrustDelta:
    """Accumulated trust deltas for an entity"""
    lct_id: str
    org_id: str

    # T3 deltas
    talent_delta: Decimal = Decimal('0.0')
    training_delta: Decimal = Decimal('0.0')
    temperament_delta: Decimal = Decimal('0.0')

    # V3 deltas
    veracity_delta: Decimal = Decimal('0.0')
    validity_delta: Decimal = Decimal('0.0')
    valuation_delta: Decimal = Decimal('0.0')

    # Statistics
    actions_count: int = 0
    transactions_count: int = 0

    # Tracking
    first_update: datetime = field(default_factory=datetime.utcnow)
    last_update: datetime = field(default_factory=datetime.utcnow)

    def accumulate_t3(self, talent: Decimal, training: Decimal, temperament: Decimal):
        """Accumulate T3 deltas"""
        self.talent_delta += talent
        self.training_delta += training
        self.temperament_delta += temperament
        self.actions_count += 1
        self.last_update = datetime.utcnow()

    def accumulate_v3(self, veracity: Decimal, validity: Decimal, valuation: Decimal):
        """Accumulate V3 deltas"""
        self.veracity_delta += veracity
        self.validity_delta += validity
        self.valuation_delta += valuation
        self.transactions_count += 1
        self.last_update = datetime.utcnow()

    def key(self) -> str:
        """Unique key for this entity+org"""
        return f"{self.lct_id}:{self.org_id}"


class TrustUpdateBatcher:
    """
    Batches trust updates to reduce database load.

    Design:
    - Updates accumulate in memory
    - Flush on timer (60s) or batch size (100)
    - Single UPDATE per entity (not per action)
    - Background thread for automatic flushing
    """

    def __init__(self,
                 db_config: dict,
                 flush_interval_seconds: int = 60,
                 max_batch_size: int = 100,
                 auto_start: bool = True,
                 max_updates_per_minute_per_lct: int = 60,
                 max_pending_total: int = 10000,
                 max_pending_per_lct: int = 100):
        """
        Initialize trust update batcher.

        Args:
            db_config: PostgreSQL connection config
            flush_interval_seconds: Seconds between automatic flushes
            max_batch_size: Maximum updates before forcing flush
            auto_start: Start background flush thread automatically
            max_updates_per_minute_per_lct: Rate limit per LCT (default: 60)
            max_pending_total: Max total pending updates (default: 10000)
            max_pending_per_lct: Max pending per LCT (default: 100)
        """
        self.db_config = db_config
        self.flush_interval = flush_interval_seconds
        self.max_batch_size = max_batch_size
        self.max_updates_per_minute_per_lct = max_updates_per_minute_per_lct
        self.max_pending_total = max_pending_total
        self.max_pending_per_lct = max_pending_per_lct

        # Pending updates (key: "lct_id:org_id" -> TrustDelta)
        self.pending: Dict[str, TrustDelta] = {}
        self.lock = threading.Lock()

        # Rate limiting (lct_id -> (count, window_start))
        self.rate_limits: Dict[str, tuple[int, datetime]] = {}

        # Merkle tree tracking (Session #57)
        self.merkle_roots: List[str] = []  # Historical merkle roots
        self.last_merkle_root: Optional[str] = None
        self.last_merkle_tree: Optional[TrustMerkleTree] = None

        # Background flush thread
        self.flush_thread: Optional[threading.Thread] = None
        self.running = False

        # Statistics
        self.stats = {
            'total_updates_recorded': 0,
            'total_flushes': 0,
            'total_entities_flushed': 0,
            'last_flush_time': None,
            'flush_errors': 0,
            'rate_limit_rejections': 0,
            'pending_limit_rejections': 0,
            'merkle_roots_generated': 0
        }

        if auto_start:
            self.start()

    def start(self):
        """Start background flush thread"""
        if self.running:
            return

        self.running = True
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.flush_thread.start()

    def stop(self):
        """Stop background flush thread and flush pending updates"""
        if not self.running:
            return

        self.running = False
        if self.flush_thread:
            self.flush_thread.join(timeout=5.0)

        # Final flush
        self.flush()

    def _flush_loop(self):
        """Background thread that flushes periodically"""
        while self.running:
            time.sleep(self.flush_interval)
            if self.running:  # Check again after sleep
                try:
                    self.flush()
                except Exception as e:
                    print(f"Error in flush loop: {e}")
                    self.stats['flush_errors'] += 1

    def _check_rate_limit(self, lct_id: str) -> bool:
        """
        Check if LCT is within rate limit.

        Returns:
            True if within limit, False if exceeded
        """
        now = datetime.utcnow()

        if lct_id not in self.rate_limits:
            # First update for this LCT
            self.rate_limits[lct_id] = (1, now)
            return True

        count, window_start = self.rate_limits[lct_id]

        # Check if window has expired (1 minute)
        window_age = (now - window_start).total_seconds()
        if window_age >= 60:
            # Reset window
            self.rate_limits[lct_id] = (1, now)
            return True

        # Within current window
        if count >= self.max_updates_per_minute_per_lct:
            # Rate limit exceeded
            return False

        # Increment count
        self.rate_limits[lct_id] = (count + 1, window_start)
        return True

    def _check_pending_limits(self, key: str) -> bool:
        """
        Check if pending limits would be exceeded.

        Returns:
            True if within limits, False if exceeded
        """
        # Check total pending limit
        if key not in self.pending and len(self.pending) >= self.max_pending_total:
            return False

        # Check per-LCT pending limit
        if key in self.pending:
            if self.pending[key].actions_count + self.pending[key].transactions_count >= self.max_pending_per_lct:
                return False

        return True

    def record_t3_update(self,
                        lct_id: str,
                        org_id: str,
                        talent_delta: Decimal = Decimal('0.0'),
                        training_delta: Decimal = Decimal('0.0'),
                        temperament_delta: Decimal = Decimal('0.0')):
        """
        Record T3 trust update in memory.

        Will be flushed to database on next flush cycle.

        Raises:
            RuntimeError: If rate limit or pending limit exceeded
        """
        should_flush = False

        with self.lock:
            # Check rate limit
            if not self._check_rate_limit(lct_id):
                self.stats['rate_limit_rejections'] += 1
                raise RuntimeError(f"Rate limit exceeded for LCT {lct_id}")

            key = f"{lct_id}:{org_id}"

            # Check pending limits
            if not self._check_pending_limits(key):
                self.stats['pending_limit_rejections'] += 1
                raise RuntimeError(f"Pending limit exceeded for {key}")

            if key not in self.pending:
                self.pending[key] = TrustDelta(lct_id, org_id)

            self.pending[key].accumulate_t3(talent_delta, training_delta, temperament_delta)
            self.stats['total_updates_recorded'] += 1

            # Check if batch is full
            if len(self.pending) >= self.max_batch_size:
                should_flush = True

        # Flush outside the lock to avoid deadlock
        if should_flush:
            self.flush()

    def record_v3_update(self,
                        lct_id: str,
                        org_id: str,
                        veracity_delta: Decimal = Decimal('0.0'),
                        validity_delta: Decimal = Decimal('0.0'),
                        valuation_delta: Decimal = Decimal('0.0')):
        """
        Record V3 trust update in memory.

        Will be flushed to database on next flush cycle.

        Raises:
            RuntimeError: If rate limit or pending limit exceeded
        """
        should_flush = False

        with self.lock:
            # Check rate limit
            if not self._check_rate_limit(lct_id):
                self.stats['rate_limit_rejections'] += 1
                raise RuntimeError(f"Rate limit exceeded for LCT {lct_id}")

            key = f"{lct_id}:{org_id}"

            # Check pending limits
            if not self._check_pending_limits(key):
                self.stats['pending_limit_rejections'] += 1
                raise RuntimeError(f"Pending limit exceeded for {key}")

            if key not in self.pending:
                self.pending[key] = TrustDelta(lct_id, org_id)

            self.pending[key].accumulate_v3(veracity_delta, validity_delta, valuation_delta)
            self.stats['total_updates_recorded'] += 1

            # Check if batch is full
            if len(self.pending) >= self.max_batch_size:
                should_flush = True

        # Flush outside the lock to avoid deadlock
        if should_flush:
            self.flush()

    def flush(self):
        """
        Flush all pending updates to database.

        Uses single UPDATE per entity (not per action).
        All updates are atomic (transaction).

        Session #57: Also generates Merkle tree for cryptographic anchoring.
        """
        # Get pending updates
        with self.lock:
            if not self.pending:
                return  # Nothing to flush

            updates_to_flush = self.pending.copy()
            self.pending.clear()

        # Build Merkle tree from updates (Session #57)
        flush_timestamp = datetime.utcnow()
        merkle_leaves = []

        for key, delta in updates_to_flush.items():
            leaf = TrustUpdateLeaf(
                lct_id=delta.lct_id,
                org_id=delta.org_id,
                talent_delta=delta.talent_delta,
                training_delta=delta.training_delta,
                temperament_delta=delta.temperament_delta,
                veracity_delta=delta.veracity_delta,
                validity_delta=delta.validity_delta,
                valuation_delta=delta.valuation_delta,
                timestamp=flush_timestamp,
                action_count=delta.actions_count,
                transaction_count=delta.transactions_count
            )
            merkle_leaves.append(leaf)

        # Generate Merkle tree
        merkle_tree = TrustMerkleTree(merkle_leaves)
        merkle_root = merkle_tree.get_root_hex()

        # Store Merkle tree for proof generation
        self.last_merkle_tree = merkle_tree
        self.last_merkle_root = merkle_root
        self.merkle_roots.append(merkle_root)
        self.stats['merkle_roots_generated'] += 1

        # Connect to database
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            try:
                # Begin transaction
                entities_flushed = 0

                for key, delta in updates_to_flush.items():
                    # Update T3 scores if any T3 deltas
                    if delta.actions_count > 0:
                        cursor.execute("""
                            UPDATE reputation_scores
                            SET talent_score = LEAST(1.0, GREATEST(0.0, talent_score + %s)),
                                training_score = LEAST(1.0, GREATEST(0.0, training_score + %s)),
                                temperament_score = LEAST(1.0, GREATEST(0.0, temperament_score + %s)),
                                total_actions = total_actions + %s,
                                last_updated = CURRENT_TIMESTAMP
                            WHERE lct_id = %s AND organization_id = %s
                        """, (
                            delta.talent_delta,
                            delta.training_delta,
                            delta.temperament_delta,
                            delta.actions_count,
                            delta.lct_id,
                            delta.org_id
                        ))

                    # Update V3 scores if any V3 deltas
                    if delta.transactions_count > 0:
                        cursor.execute("""
                            UPDATE v3_scores
                            SET veracity_score = LEAST(1.0, GREATEST(0.0, veracity_score + %s)),
                                validity_score = LEAST(1.0, GREATEST(0.0, validity_score + %s)),
                                valuation_score = LEAST(1.0, GREATEST(0.0, valuation_score + %s)),
                                total_transactions = total_transactions + %s,
                                last_updated = CURRENT_TIMESTAMP
                            WHERE lct_id = %s AND organization_id = %s
                        """, (
                            delta.veracity_delta,
                            delta.validity_delta,
                            delta.valuation_delta,
                            delta.transactions_count,
                            delta.lct_id,
                            delta.org_id
                        ))

                    entities_flushed += 1

                # Commit transaction
                conn.commit()

                # Update statistics
                self.stats['total_flushes'] += 1
                self.stats['total_entities_flushed'] += entities_flushed
                self.stats['last_flush_time'] = datetime.utcnow()

            except Exception as e:
                conn.rollback()
                print(f"Error flushing trust updates: {e}")
                self.stats['flush_errors'] += 1

                # Put updates back in pending queue
                with self.lock:
                    for key, delta in updates_to_flush.items():
                        if key in self.pending:
                            # Merge with existing
                            existing = self.pending[key]
                            existing.talent_delta += delta.talent_delta
                            existing.training_delta += delta.training_delta
                            existing.temperament_delta += delta.temperament_delta
                            existing.veracity_delta += delta.veracity_delta
                            existing.validity_delta += delta.validity_delta
                            existing.valuation_delta += delta.valuation_delta
                            existing.actions_count += delta.actions_count
                            existing.transactions_count += delta.transactions_count
                        else:
                            self.pending[key] = delta

                raise

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            print(f"Database connection error: {e}")
            self.stats['flush_errors'] += 1
            raise

    def get_stats(self) -> dict:
        """Get batcher statistics"""
        with self.lock:
            return {
                **self.stats,
                'pending_updates': len(self.pending),
                'pending_entities': list(self.pending.keys())[:10],  # First 10
                'last_merkle_root': self.last_merkle_root,
                'merkle_roots_count': len(self.merkle_roots)
            }

    def get_pending_count(self) -> int:
        """Get count of pending updates"""
        with self.lock:
            return len(self.pending)

    def get_merkle_proof(self, lct_id: str, org_id: str) -> Optional[dict]:
        """
        Get Merkle proof for the last flush containing this entity.

        Args:
            lct_id: LCT identity
            org_id: Organization ID

        Returns:
            Dictionary with proof data, or None if not found

        Note: Only works for the last flush. For historical proofs,
        need to query merkle_proofs table (Phase 1).
        """
        if not self.last_merkle_tree:
            return None

        # Find the entity in last flush
        key = f"{lct_id}:{org_id}"
        for i, leaf in enumerate(self.last_merkle_tree.leaves):
            if leaf.lct_id == lct_id and leaf.org_id == org_id:
                # Found it - generate proof
                proof = self.last_merkle_tree.get_proof_hex(i)
                return {
                    'lct_id': lct_id,
                    'org_id': org_id,
                    'leaf_index': i,
                    'leaf_hash': leaf.hash().hex(),
                    'merkle_root': self.last_merkle_root,
                    'proof': proof,
                    'timestamp': leaf.timestamp.isoformat()
                }

        return None

    def get_all_merkle_roots(self) -> List[str]:
        """Get list of all merkle roots generated"""
        return self.merkle_roots.copy()


# Example usage
if __name__ == "__main__":
    # Database configuration
    db_config = {
        'dbname': 'web4',
        'user': 'postgres',
        'host': 'localhost'
    }

    # Create batcher
    batcher = TrustUpdateBatcher(
        db_config=db_config,
        flush_interval_seconds=60,
        max_batch_size=100
    )

    print("Trust Update Batcher started")
    print(f"Flush interval: {batcher.flush_interval} seconds")
    print(f"Max batch size: {batcher.max_batch_size} updates")

    # Simulate some updates
    from decimal import Decimal

    for i in range(10):
        batcher.record_t3_update(
            lct_id=f"lct:ai:test:00{i}",
            org_id="org:test:batch",
            training_delta=Decimal('0.001'),
            temperament_delta=Decimal('0.0005')
        )

    print(f"\nRecorded 10 updates")
    print(f"Pending: {batcher.get_pending_count()}")

    # Manual flush
    batcher.flush()
    print(f"After flush: {batcher.get_pending_count()} pending")

    # Statistics
    stats = batcher.get_stats()
    print(f"\nStatistics:")
    print(f"  Total updates recorded: {stats['total_updates_recorded']}")
    print(f"  Total flushes: {stats['total_flushes']}")
    print(f"  Total entities flushed: {stats['total_entities_flushed']}")

    # Stop batcher
    batcher.stop()
    print("\nBatcher stopped")
