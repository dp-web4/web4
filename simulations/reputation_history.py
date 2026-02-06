"""
Federation Reputation History

Track CB: Tracking reputation changes over time.

Key concepts:
1. Reputation snapshots: Record reputation at regular intervals
2. Change detection: Identify significant reputation shifts
3. Trend analysis: Is reputation growing, stable, or declining?
4. Anomaly detection: Flag sudden changes that may indicate manipulation

This creates a time-series view of reputation that enables:
- Historical analysis
- Trust-based predictions
- Manipulation detection
- Accountability through reputation audit trail
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum

from .reputation_aggregation import ReputationAggregator, ReputationScore


class ReputationTrend(Enum):
    """Trend direction for reputation changes."""
    RISING = "rising"           # Consistent improvement
    STABLE = "stable"           # No significant change
    DECLINING = "declining"     # Consistent decrease
    VOLATILE = "volatile"       # Frequent up/down swings
    UNKNOWN = "unknown"         # Insufficient data


@dataclass
class ReputationSnapshot:
    """A point-in-time capture of federation reputation."""
    snapshot_id: str
    federation_id: str
    timestamp: str

    # Core metrics
    global_reputation: float
    confidence: float
    incoming_trust_count: int
    tier: str  # ReputationTier.value

    # Supporting metrics
    incoming_trust_sum: float  # Total incoming trust
    presence_weighted_trust: float  # Trust weighted by source presence

    # Change tracking
    previous_snapshot_id: str = ""
    change_from_previous: float = 0.0  # Delta from last snapshot

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ReputationSnapshot':
        return cls(**data)


@dataclass
class ReputationChange:
    """Record of a significant reputation change."""
    change_id: str
    federation_id: str
    timestamp: str

    # Change details
    old_reputation: float
    new_reputation: float
    delta: float
    percent_change: float

    # Cause analysis
    cause: str = ""  # trust_added, trust_removed, decay, endorsement_change
    related_federations: List[str] = None

    # Risk assessment
    anomaly_score: float = 0.0  # 0-1, higher = more suspicious

    def __post_init__(self):
        if self.related_federations is None:
            self.related_federations = []

    def to_dict(self) -> dict:
        return asdict(self)


class ReputationHistory:
    """
    Track and analyze federation reputation over time.

    Track CB: Federation Reputation History

    Features:
    - Periodic reputation snapshots
    - Change detection and logging
    - Trend analysis (rising/stable/declining)
    - Anomaly detection for manipulation
    """

    def __init__(
        self,
        aggregator: ReputationAggregator,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize reputation history tracking.

        Args:
            aggregator: ReputationAggregator for calculating current reputation
            db_path: Path to SQLite database (None for in-memory)
        """
        self.aggregator = aggregator

        if db_path:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = ":memory:"

        self._init_db()

        # Configuration
        self.significant_change_threshold = 0.05  # 5% change is significant
        self.anomaly_threshold = 0.2  # 20% change in short time is anomalous

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Snapshots table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reputation_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    federation_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    global_reputation REAL NOT NULL,
                    confidence REAL NOT NULL,
                    incoming_trust_count INTEGER NOT NULL,
                    tier TEXT NOT NULL,
                    incoming_trust_sum REAL NOT NULL,
                    presence_weighted_trust REAL NOT NULL,
                    previous_snapshot_id TEXT DEFAULT '',
                    change_from_previous REAL DEFAULT 0.0
                )
            """)

            # Changes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reputation_changes (
                    change_id TEXT PRIMARY KEY,
                    federation_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    old_reputation REAL NOT NULL,
                    new_reputation REAL NOT NULL,
                    delta REAL NOT NULL,
                    percent_change REAL NOT NULL,
                    cause TEXT DEFAULT '',
                    related_federations TEXT DEFAULT '[]',
                    anomaly_score REAL DEFAULT 0.0
                )
            """)

            # Indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snap_fed_time
                ON reputation_snapshots(federation_id, timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_change_fed
                ON reputation_changes(federation_id)
            """)

            conn.commit()
        finally:
            conn.close()

    def take_snapshot(self, federation_id: str) -> ReputationSnapshot:
        """
        Take a snapshot of a federation's current reputation.

        Args:
            federation_id: Federation to snapshot

        Returns:
            ReputationSnapshot with current values
        """
        import uuid

        # Calculate current reputation
        score = self.aggregator.calculate_reputation(federation_id, force_refresh=True)

        now = datetime.now(timezone.utc).isoformat()

        # Get previous snapshot for change tracking
        previous = self._get_latest_snapshot(federation_id)

        snapshot = ReputationSnapshot(
            snapshot_id=f"snap:{uuid.uuid4().hex[:12]}",
            federation_id=federation_id,
            timestamp=now,
            global_reputation=score.global_reputation,
            confidence=score.confidence,
            incoming_trust_count=score.incoming_trust_count,
            tier=score.tier.value,
            incoming_trust_sum=score.incoming_trust_sum,
            presence_weighted_trust=score.presence_weighted_trust,
            previous_snapshot_id=previous.snapshot_id if previous else "",
            change_from_previous=score.global_reputation - previous.global_reputation if previous else 0.0,
        )

        # Store snapshot
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO reputation_snapshots
                (snapshot_id, federation_id, timestamp, global_reputation, confidence,
                 incoming_trust_count, tier, incoming_trust_sum, presence_weighted_trust,
                 previous_snapshot_id, change_from_previous)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.snapshot_id,
                snapshot.federation_id,
                snapshot.timestamp,
                snapshot.global_reputation,
                snapshot.confidence,
                snapshot.incoming_trust_count,
                snapshot.tier,
                snapshot.incoming_trust_sum,
                snapshot.presence_weighted_trust,
                snapshot.previous_snapshot_id,
                snapshot.change_from_previous,
            ))
            conn.commit()
        finally:
            conn.close()

        # Detect and record significant changes
        if previous and abs(snapshot.change_from_previous) >= self.significant_change_threshold:
            self._record_change(previous, snapshot)

        return snapshot

    def _get_latest_snapshot(self, federation_id: str) -> Optional[ReputationSnapshot]:
        """Get the most recent snapshot for a federation."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM reputation_snapshots
                WHERE federation_id = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (federation_id,)).fetchone()

            if row:
                return self._row_to_snapshot(row)
            return None
        finally:
            conn.close()

    def _row_to_snapshot(self, row) -> ReputationSnapshot:
        """Convert database row to ReputationSnapshot."""
        return ReputationSnapshot(
            snapshot_id=row["snapshot_id"],
            federation_id=row["federation_id"],
            timestamp=row["timestamp"],
            global_reputation=row["global_reputation"],
            confidence=row["confidence"],
            incoming_trust_count=row["incoming_trust_count"],
            tier=row["tier"],
            incoming_trust_sum=row["incoming_trust_sum"],
            presence_weighted_trust=row["presence_weighted_trust"],
            previous_snapshot_id=row["previous_snapshot_id"],
            change_from_previous=row["change_from_previous"],
        )

    def _record_change(
        self,
        old_snapshot: ReputationSnapshot,
        new_snapshot: ReputationSnapshot,
        cause: str = "",
        related_federations: Optional[List[str]] = None,
    ):
        """Record a significant reputation change."""
        import uuid

        delta = new_snapshot.global_reputation - old_snapshot.global_reputation
        percent_change = delta / old_snapshot.global_reputation if old_snapshot.global_reputation > 0 else 0

        # Calculate anomaly score based on magnitude and speed of change
        anomaly_score = self._calculate_anomaly_score(
            old_snapshot, new_snapshot, percent_change
        )

        change = ReputationChange(
            change_id=f"change:{uuid.uuid4().hex[:12]}",
            federation_id=new_snapshot.federation_id,
            timestamp=new_snapshot.timestamp,
            old_reputation=old_snapshot.global_reputation,
            new_reputation=new_snapshot.global_reputation,
            delta=delta,
            percent_change=percent_change,
            cause=cause or self._infer_cause(old_snapshot, new_snapshot),
            related_federations=related_federations or [],
            anomaly_score=anomaly_score,
        )

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO reputation_changes
                (change_id, federation_id, timestamp, old_reputation, new_reputation,
                 delta, percent_change, cause, related_federations, anomaly_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                change.change_id,
                change.federation_id,
                change.timestamp,
                change.old_reputation,
                change.new_reputation,
                change.delta,
                change.percent_change,
                change.cause,
                json.dumps(change.related_federations),
                change.anomaly_score,
            ))
            conn.commit()
        finally:
            conn.close()

        return change

    def _calculate_anomaly_score(
        self,
        old: ReputationSnapshot,
        new: ReputationSnapshot,
        percent_change: float,
    ) -> float:
        """Calculate anomaly score for a reputation change."""
        score = 0.0

        # Large percentage change is suspicious
        if abs(percent_change) > self.anomaly_threshold:
            score += 0.3

        # Large absolute change is suspicious
        if abs(new.global_reputation - old.global_reputation) > 0.3:
            score += 0.3

        # Sudden trust count change is suspicious
        trust_count_change = abs(new.incoming_trust_count - old.incoming_trust_count)
        if trust_count_change > 5:
            score += 0.2

        # Low confidence with high reputation is suspicious
        if new.global_reputation > 0.7 and new.confidence < 0.3:
            score += 0.2

        return min(score, 1.0)

    def _infer_cause(
        self,
        old: ReputationSnapshot,
        new: ReputationSnapshot,
    ) -> str:
        """Infer the cause of a reputation change."""
        if new.incoming_trust_count > old.incoming_trust_count:
            return "trust_added"
        elif new.incoming_trust_count < old.incoming_trust_count:
            return "trust_removed"
        elif new.incoming_trust_sum != old.incoming_trust_sum:
            return "trust_value_changed"
        else:
            return "unknown"

    def get_reputation_timeline(
        self,
        federation_id: str,
        limit: int = 100,
    ) -> List[ReputationSnapshot]:
        """
        Get reputation history for a federation.

        Args:
            federation_id: Federation to query
            limit: Maximum snapshots to return

        Returns:
            List of snapshots, most recent first
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM reputation_snapshots
                WHERE federation_id = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (federation_id, limit)).fetchall()

            return [self._row_to_snapshot(row) for row in rows]
        finally:
            conn.close()

    def get_reputation_changes(
        self,
        federation_id: str,
        min_anomaly_score: float = 0.0,
        limit: int = 50,
    ) -> List[ReputationChange]:
        """
        Get significant reputation changes for a federation.

        Args:
            federation_id: Federation to query
            min_anomaly_score: Minimum anomaly score to include
            limit: Maximum changes to return

        Returns:
            List of changes, most recent first
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM reputation_changes
                WHERE federation_id = ?
                  AND anomaly_score >= ?
                ORDER BY timestamp DESC LIMIT ?
            """, (federation_id, min_anomaly_score, limit)).fetchall()

            return [self._row_to_change(row) for row in rows]
        finally:
            conn.close()

    def _row_to_change(self, row) -> ReputationChange:
        """Convert database row to ReputationChange."""
        return ReputationChange(
            change_id=row["change_id"],
            federation_id=row["federation_id"],
            timestamp=row["timestamp"],
            old_reputation=row["old_reputation"],
            new_reputation=row["new_reputation"],
            delta=row["delta"],
            percent_change=row["percent_change"],
            cause=row["cause"],
            related_federations=json.loads(row["related_federations"]),
            anomaly_score=row["anomaly_score"],
        )

    def analyze_trend(
        self,
        federation_id: str,
        lookback_days: int = 30,
    ) -> Dict:
        """
        Analyze reputation trend for a federation.

        Args:
            federation_id: Federation to analyze
            lookback_days: Days to look back

        Returns:
            Dict with trend analysis
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM reputation_snapshots
                WHERE federation_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (federation_id, cutoff)).fetchall()

            if len(rows) < 2:
                return {
                    "trend": ReputationTrend.UNKNOWN.value,
                    "snapshot_count": len(rows),
                    "insufficient_data": True,
                }

            snapshots = [self._row_to_snapshot(row) for row in rows]

            # Calculate deltas
            deltas = [s.change_from_previous for s in snapshots[1:]]

            # Determine trend
            positive_changes = sum(1 for d in deltas if d > 0.01)
            negative_changes = sum(1 for d in deltas if d < -0.01)
            total_changes = len(deltas)

            if positive_changes > total_changes * 0.6:
                trend = ReputationTrend.RISING
            elif negative_changes > total_changes * 0.6:
                trend = ReputationTrend.DECLINING
            elif positive_changes > total_changes * 0.3 and negative_changes > total_changes * 0.3:
                trend = ReputationTrend.VOLATILE
            else:
                trend = ReputationTrend.STABLE

            # Calculate statistics
            start_rep = snapshots[0].global_reputation
            end_rep = snapshots[-1].global_reputation
            avg_rep = sum(s.global_reputation for s in snapshots) / len(snapshots)

            return {
                "trend": trend.value,
                "snapshot_count": len(snapshots),
                "start_reputation": round(start_rep, 3),
                "end_reputation": round(end_rep, 3),
                "average_reputation": round(avg_rep, 3),
                "total_change": round(end_rep - start_rep, 3),
                "positive_changes": positive_changes,
                "negative_changes": negative_changes,
                "lookback_days": lookback_days,
            }
        finally:
            conn.close()

    def detect_anomalies(
        self,
        federation_id: Optional[str] = None,
        threshold: float = 0.5,
    ) -> List[ReputationChange]:
        """
        Detect anomalous reputation changes.

        Args:
            federation_id: Optional federation to check (None = all)
            threshold: Minimum anomaly score

        Returns:
            List of anomalous changes
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            if federation_id:
                rows = conn.execute("""
                    SELECT * FROM reputation_changes
                    WHERE federation_id = ? AND anomaly_score >= ?
                    ORDER BY anomaly_score DESC, timestamp DESC
                """, (federation_id, threshold)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM reputation_changes
                    WHERE anomaly_score >= ?
                    ORDER BY anomaly_score DESC, timestamp DESC
                """, (threshold,)).fetchall()

            return [self._row_to_change(row) for row in rows]
        finally:
            conn.close()

    def get_statistics(self) -> Dict:
        """Get overall reputation history statistics."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            snapshot_count = conn.execute("""
                SELECT COUNT(*) as count FROM reputation_snapshots
            """).fetchone()["count"]

            change_count = conn.execute("""
                SELECT COUNT(*) as count FROM reputation_changes
            """).fetchone()["count"]

            fed_count = conn.execute("""
                SELECT COUNT(DISTINCT federation_id) as count FROM reputation_snapshots
            """).fetchone()["count"]

            anomaly_count = conn.execute("""
                SELECT COUNT(*) as count FROM reputation_changes WHERE anomaly_score >= 0.5
            """).fetchone()["count"]

            return {
                "total_snapshots": snapshot_count,
                "total_changes": change_count,
                "federations_tracked": fed_count,
                "anomalies_detected": anomaly_count,
            }
        finally:
            conn.close()


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Reputation History - Self Test")
    print("=" * 60)

    import tempfile
    from .multi_federation import MultiFederationRegistry, FederationRelationship

    tmp_dir = Path(tempfile.mkdtemp())
    registry = MultiFederationRegistry(db_path=tmp_dir / "federation.db")
    aggregator = ReputationAggregator(registry)
    history = ReputationHistory(aggregator, db_path=tmp_dir / "history.db")

    # Create federations
    print("\n1. Create federations:")
    registry.register_federation("fed:target", "Target")
    registry.register_federation("fed:endorser1", "Endorser1")
    registry.register_federation("fed:endorser2", "Endorser2")
    print("   Created: fed:target, fed:endorser1, fed:endorser2")

    # Take initial snapshot
    print("\n2. Take initial snapshot:")
    snap1 = history.take_snapshot("fed:target")
    print(f"   Snapshot: rep={snap1.global_reputation:.2f}, trust_count={snap1.incoming_trust_count}")

    # Add endorsement and take another snapshot
    print("\n3. Add endorsement and snapshot:")
    registry.establish_trust("fed:endorser1", "fed:target", FederationRelationship.PEER, 0.7)
    snap2 = history.take_snapshot("fed:target")
    print(f"   Snapshot: rep={snap2.global_reputation:.2f}, change={snap2.change_from_previous:+.2f}")

    # Add more endorsements
    print("\n4. Add more endorsements:")
    registry.establish_trust("fed:endorser2", "fed:target", FederationRelationship.PEER, 0.8)
    registry.register_federation("fed:endorser3", "Endorser3")
    registry.establish_trust("fed:endorser3", "fed:target", FederationRelationship.PEER, 0.6)
    snap3 = history.take_snapshot("fed:target")
    print(f"   Snapshot: rep={snap3.global_reputation:.2f}, trust_count={snap3.incoming_trust_count}")

    # View timeline
    print("\n5. Reputation timeline:")
    timeline = history.get_reputation_timeline("fed:target")
    for snap in timeline:
        print(f"   {snap.timestamp[:19]}: rep={snap.global_reputation:.2f}, change={snap.change_from_previous:+.2f}")

    # View changes
    print("\n6. Reputation changes:")
    changes = history.get_reputation_changes("fed:target")
    for change in changes:
        print(f"   {change.cause}: {change.old_reputation:.2f} -> {change.new_reputation:.2f} (anomaly: {change.anomaly_score:.1f})")

    # Trend analysis
    print("\n7. Trend analysis:")
    trend = history.analyze_trend("fed:target")
    print(f"   Trend: {trend['trend']}")
    print(f"   Start: {trend['start_reputation']}, End: {trend['end_reputation']}")

    # Statistics
    print("\n8. Statistics:")
    stats = history.get_statistics()
    print(f"   Snapshots: {stats['total_snapshots']}")
    print(f"   Changes: {stats['total_changes']}")
    print(f"   Anomalies: {stats['anomalies_detected']}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
