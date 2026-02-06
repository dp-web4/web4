"""
Network Partition Resilience

Track CI: Defending against network partition attacks.

Key concepts:
1. Bridge Detection: Identify single points of failure in trust network
2. Partition Warning: Alert when network is at risk of partition
3. Graceful Degradation: Maintain operations during partitions
4. Healing Verification: Safe state reconciliation after partition heals
5. Redundancy Scoring: Measure network resilience to partition

This provides the defensive layer needed to protect federations
from network partition attacks identified in Attack 24.
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from enum import Enum
import json
import hashlib
from collections import defaultdict

from hardbound.multi_federation import MultiFederationRegistry, FederationRelationship
from hardbound.trust_network import TrustNetworkAnalyzer, NetworkAnomaly


class PartitionRisk(Enum):
    """Level of partition risk."""
    NONE = "none"              # Fully redundant network
    LOW = "low"                # Minor single points of failure
    MEDIUM = "medium"          # Significant partition risk
    HIGH = "high"              # Critical - partition likely
    PARTITIONED = "partitioned"  # Network is currently partitioned


class BridgeType(Enum):
    """Type of bridge node."""
    NONE = "none"              # Not a bridge
    MINOR = "minor"            # Bridges small clusters
    MAJOR = "major"            # Critical bridge node
    CRITICAL = "critical"      # Single point of failure


@dataclass
class BridgeNode:
    """A node that bridges network partitions."""
    federation_id: str
    bridge_type: BridgeType
    centrality_score: float
    connected_clusters: List[str]  # Clusters this node connects
    redundancy_score: float  # 0 = no redundancy, 1 = fully redundant
    alternate_paths: int  # Number of paths that don't use this bridge

    def to_dict(self) -> Dict:
        return {
            "federation_id": self.federation_id,
            "bridge_type": self.bridge_type.value,
            "centrality_score": self.centrality_score,
            "connected_clusters": self.connected_clusters,
            "redundancy_score": self.redundancy_score,
            "alternate_paths": self.alternate_paths,
        }


@dataclass
class PartitionAlert:
    """Alert about potential or actual partition."""
    alert_id: str
    risk_level: PartitionRisk
    affected_federations: List[str]
    bridge_nodes: List[str]
    message: str
    timestamp: str
    recommendations: List[str] = field(default_factory=list)
    resolved: bool = False


@dataclass
class PartitionEvent:
    """Record of a partition event."""
    event_id: str
    detected_at: str
    healed_at: str = ""
    partition_a: List[str] = field(default_factory=list)  # Federation IDs
    partition_b: List[str] = field(default_factory=list)
    bridge_failures: List[str] = field(default_factory=list)
    healing_verified: bool = False
    state_conflicts: List[Dict] = field(default_factory=list)


class PartitionResilienceManager:
    """
    Manage network partition resilience.

    Track CI: Defense against network partition attacks.
    """

    # Centrality threshold for bridge classification
    CRITICAL_CENTRALITY_THRESHOLD = 0.4
    MAJOR_CENTRALITY_THRESHOLD = 0.2
    MINOR_CENTRALITY_THRESHOLD = 0.1

    # Minimum redundancy for healthy network
    MIN_HEALTHY_REDUNDANCY = 0.3

    # Minimum cluster connectivity
    MIN_CLUSTER_CONNECTIONS = 2

    def __init__(
        self,
        registry: MultiFederationRegistry,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize partition resilience manager.

        Args:
            registry: Multi-federation registry
            db_path: Database path for event history
        """
        self.registry = registry
        self.analyzer = TrustNetworkAnalyzer(registry)
        self.db_path = db_path or Path("partition_resilience.db")

        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS partition_alerts (
                    alert_id TEXT PRIMARY KEY,
                    risk_level TEXT NOT NULL,
                    affected_federations TEXT NOT NULL,
                    bridge_nodes TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    resolved INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS partition_events (
                    event_id TEXT PRIMARY KEY,
                    detected_at TEXT NOT NULL,
                    healed_at TEXT,
                    partition_a TEXT NOT NULL,
                    partition_b TEXT NOT NULL,
                    bridge_failures TEXT NOT NULL,
                    healing_verified INTEGER DEFAULT 0,
                    state_conflicts TEXT DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS resilience_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    overall_risk TEXT NOT NULL,
                    bridge_count INTEGER NOT NULL,
                    avg_redundancy REAL NOT NULL,
                    details TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
                ON partition_alerts(timestamp);

                CREATE INDEX IF NOT EXISTS idx_events_detected
                ON partition_events(detected_at);
            """)
            conn.commit()
        finally:
            conn.close()

    def analyze_network_resilience(self) -> Dict:
        """
        Analyze overall network resilience to partitions.

        Returns:
            Dict with resilience analysis
        """
        # Build network and identify bridges
        nodes, edges = self.analyzer.build_network()
        centrality = self.analyzer.calculate_centrality()

        # Identify bridge nodes
        bridges = self._identify_bridges(centrality)

        # Detect clusters
        clusters = self.analyzer.detect_clusters()

        # Calculate redundancy scores
        redundancy = self._calculate_redundancy(bridges, clusters)

        # Determine overall risk
        risk_level = self._calculate_risk_level(bridges, redundancy)

        # Generate recommendations
        recommendations = self._generate_recommendations(bridges, redundancy, clusters)

        # Store snapshot
        self._store_resilience_snapshot(risk_level, bridges, redundancy)

        return {
            "risk_level": risk_level.value,
            "bridge_nodes": [b.to_dict() for b in bridges],
            "cluster_count": len(clusters),
            "average_redundancy": redundancy.get("average", 0.0),
            "critical_bridges": [b.federation_id for b in bridges if b.bridge_type == BridgeType.CRITICAL],
            "recommendations": recommendations,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _identify_bridges(self, centrality: Dict[str, float]) -> List[BridgeNode]:
        """Identify bridge nodes in the network."""
        bridges = []

        for fed_id, score in centrality.items():
            if score < self.MINOR_CENTRALITY_THRESHOLD:
                continue

            # Determine bridge type
            if score >= self.CRITICAL_CENTRALITY_THRESHOLD:
                bridge_type = BridgeType.CRITICAL
            elif score >= self.MAJOR_CENTRALITY_THRESHOLD:
                bridge_type = BridgeType.MAJOR
            else:
                bridge_type = BridgeType.MINOR

            # Find connected clusters
            connected_clusters = self._find_connected_clusters(fed_id)

            # Calculate redundancy for this bridge
            redundancy = self._calculate_bridge_redundancy(fed_id, connected_clusters)

            bridges.append(BridgeNode(
                federation_id=fed_id,
                bridge_type=bridge_type,
                centrality_score=score,
                connected_clusters=connected_clusters,
                redundancy_score=redundancy["score"],
                alternate_paths=redundancy["alternate_paths"],
            ))

        # Sort by criticality
        bridges.sort(key=lambda b: b.centrality_score, reverse=True)
        return bridges

    def _find_connected_clusters(self, bridge_id: str) -> List[str]:
        """Find clusters connected through a bridge node."""
        clusters = self.analyzer.detect_clusters()
        connected = []

        for cluster in clusters:
            if bridge_id in cluster.members:
                # Bridge is in this cluster
                connected.append(cluster.cluster_id)
            else:
                # Check if any cluster member connects to bridge
                relationships = self.registry.get_all_relationships()
                for rel in relationships:
                    if rel.source_federation_id == bridge_id and rel.target_federation_id in cluster.members:
                        connected.append(cluster.cluster_id)
                        break
                    if rel.target_federation_id == bridge_id and rel.source_federation_id in cluster.members:
                        connected.append(cluster.cluster_id)
                        break

        return list(set(connected))

    def _calculate_bridge_redundancy(
        self,
        bridge_id: str,
        connected_clusters: List[str]
    ) -> Dict:
        """Calculate redundancy for a specific bridge."""
        if len(connected_clusters) < 2:
            return {"score": 1.0, "alternate_paths": 0}  # Not a true bridge

        # Get federation IDs from clusters
        clusters = {c.cluster_id: c.members for c in self.analyzer.detect_clusters()}

        cluster_a = clusters.get(connected_clusters[0], [])
        cluster_b = clusters.get(connected_clusters[1], []) if len(connected_clusters) > 1 else []

        if not cluster_a or not cluster_b:
            return {"score": 1.0, "alternate_paths": 0}

        # Find paths between clusters not using bridge
        alternate_paths = 0

        for fed_a in cluster_a[:3]:  # Sample for performance
            for fed_b in cluster_b[:3]:
                if fed_a == bridge_id or fed_b == bridge_id:
                    continue
                paths = self.analyzer.find_all_paths(fed_a, fed_b, max_hops=4)
                paths_without_bridge = [p for p in paths if bridge_id not in p]
                alternate_paths += len(paths_without_bridge)

        # Score based on alternate paths
        score = min(1.0, alternate_paths / 10.0)  # Normalize

        return {"score": score, "alternate_paths": alternate_paths}

    def _calculate_redundancy(
        self,
        bridges: List[BridgeNode],
        clusters: List
    ) -> Dict:
        """Calculate overall network redundancy."""
        if not bridges:
            return {"average": 1.0, "min": 1.0, "details": {}}

        scores = [b.redundancy_score for b in bridges]

        return {
            "average": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
            "details": {
                b.federation_id: b.redundancy_score for b in bridges
            }
        }

    def _calculate_risk_level(
        self,
        bridges: List[BridgeNode],
        redundancy: Dict
    ) -> PartitionRisk:
        """Calculate overall partition risk level."""
        critical_bridges = [b for b in bridges if b.bridge_type == BridgeType.CRITICAL]
        major_bridges = [b for b in bridges if b.bridge_type == BridgeType.MAJOR]

        avg_redundancy = redundancy.get("average", 1.0)
        min_redundancy = redundancy.get("min", 1.0)

        # Check for critical single points of failure
        if critical_bridges and min_redundancy < 0.1:
            return PartitionRisk.HIGH

        if critical_bridges and min_redundancy < 0.3:
            return PartitionRisk.MEDIUM

        if major_bridges and avg_redundancy < 0.3:
            return PartitionRisk.MEDIUM

        if bridges and avg_redundancy < 0.5:
            return PartitionRisk.LOW

        return PartitionRisk.NONE

    def _generate_recommendations(
        self,
        bridges: List[BridgeNode],
        redundancy: Dict,
        clusters: List
    ) -> List[str]:
        """Generate recommendations for improving resilience."""
        recommendations = []

        critical_bridges = [b for b in bridges if b.bridge_type == BridgeType.CRITICAL]

        for bridge in critical_bridges:
            if bridge.redundancy_score < 0.2:
                recommendations.append(
                    f"CRITICAL: Federation '{bridge.federation_id}' is a single point of failure. "
                    f"Establish redundant trust paths between its connected clusters."
                )

        if redundancy.get("average", 1.0) < self.MIN_HEALTHY_REDUNDANCY:
            recommendations.append(
                "Network redundancy is below healthy threshold. "
                "Consider establishing additional cross-cluster trust relationships."
            )

        if len(clusters) > 1:
            isolated = [c for c in clusters if len(c.members) == 1]
            for cluster in isolated:
                recommendations.append(
                    f"Federation '{cluster.members[0]}' is isolated. "
                    "Establish trust relationships to integrate into the network."
                )

        return recommendations

    def _store_resilience_snapshot(
        self,
        risk_level: PartitionRisk,
        bridges: List[BridgeNode],
        redundancy: Dict
    ):
        """Store a resilience snapshot for historical analysis."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO resilience_snapshots
                (timestamp, overall_risk, bridge_count, avg_redundancy, details)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now(timezone.utc).isoformat(),
                risk_level.value,
                len(bridges),
                redundancy.get("average", 1.0),
                json.dumps({
                    "bridges": [b.to_dict() for b in bridges],
                    "redundancy": redundancy,
                }),
            ))
            conn.commit()
        finally:
            conn.close()

    def check_partition_status(self) -> Dict:
        """
        Check if network is currently partitioned.

        Returns:
            Dict with partition status
        """
        clusters = self.analyzer.detect_clusters()

        if len(clusters) <= 1:
            return {
                "partitioned": False,
                "partition_count": 1,
                "message": "Network is connected",
            }

        # Multiple disconnected clusters indicate partition
        return {
            "partitioned": True,
            "partition_count": len(clusters),
            "partitions": [
                {
                    "cluster_id": c.cluster_id,
                    "members": c.members,
                    "size": len(c.members),
                }
                for c in clusters
            ],
            "message": f"Network is partitioned into {len(clusters)} disconnected clusters",
        }

    def create_partition_alert(
        self,
        risk_level: PartitionRisk,
        affected_federations: List[str],
        bridge_nodes: List[str],
        message: str,
    ) -> PartitionAlert:
        """Create and store a partition alert."""
        now = datetime.now(timezone.utc)
        alert_id = hashlib.sha256(
            f"{now.isoformat()}{message}".encode()
        ).hexdigest()[:16]

        recommendations = self._generate_recommendations(
            [BridgeNode(
                federation_id=b,
                bridge_type=BridgeType.CRITICAL,
                centrality_score=0.5,
                connected_clusters=[],
                redundancy_score=0.0,
                alternate_paths=0,
            ) for b in bridge_nodes],
            {"average": 0.0},
            [],
        )

        alert = PartitionAlert(
            alert_id=alert_id,
            risk_level=risk_level,
            affected_federations=affected_federations,
            bridge_nodes=bridge_nodes,
            message=message,
            timestamp=now.isoformat(),
            recommendations=recommendations,
        )

        # Store alert
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO partition_alerts
                (alert_id, risk_level, affected_federations, bridge_nodes,
                 message, timestamp, recommendations, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.risk_level.value,
                json.dumps(alert.affected_federations),
                json.dumps(alert.bridge_nodes),
                alert.message,
                alert.timestamp,
                json.dumps(alert.recommendations),
                0,
            ))
            conn.commit()
        finally:
            conn.close()

        return alert

    def record_partition_event(
        self,
        partition_a: List[str],
        partition_b: List[str],
        bridge_failures: List[str],
    ) -> PartitionEvent:
        """Record a partition event."""
        now = datetime.now(timezone.utc)
        event_id = hashlib.sha256(
            f"{now.isoformat()}{partition_a}{partition_b}".encode()
        ).hexdigest()[:16]

        event = PartitionEvent(
            event_id=event_id,
            detected_at=now.isoformat(),
            partition_a=partition_a,
            partition_b=partition_b,
            bridge_failures=bridge_failures,
        )

        # Store event
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO partition_events
                (event_id, detected_at, partition_a, partition_b, bridge_failures)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.detected_at,
                json.dumps(event.partition_a),
                json.dumps(event.partition_b),
                json.dumps(event.bridge_failures),
            ))
            conn.commit()
        finally:
            conn.close()

        return event

    def verify_partition_healing(self, event_id: str) -> Dict:
        """
        Verify that a partition has healed safely.

        Returns:
            Dict with healing verification results
        """
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM partition_events WHERE event_id = ?",
                (event_id,)
            ).fetchone()

            if not row:
                return {"error": "Event not found"}

            partition_a = json.loads(row[3])
            partition_b = json.loads(row[4])

            # Check if all federations are now connected
            status = self.check_partition_status()

            if status["partitioned"]:
                return {
                    "healed": False,
                    "message": "Network is still partitioned",
                    "remaining_partitions": status["partition_count"],
                }

            # Verify all federations are reachable
            all_feds = partition_a + partition_b
            for fed in all_feds:
                fed_data = self.registry.get_federation(fed)
                if not fed_data:
                    return {
                        "healed": False,
                        "message": f"Federation {fed} not found in registry",
                    }

            # Update event as healed
            now = datetime.now(timezone.utc)
            conn.execute("""
                UPDATE partition_events
                SET healed_at = ?, healing_verified = 1
                WHERE event_id = ?
            """, (now.isoformat(), event_id))
            conn.commit()

            return {
                "healed": True,
                "healed_at": now.isoformat(),
                "federations_verified": len(all_feds),
                "message": "Partition has healed successfully",
            }

        finally:
            conn.close()

    def get_resilience_history(self, limit: int = 100) -> List[Dict]:
        """Get historical resilience snapshots."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT timestamp, overall_risk, bridge_count, avg_redundancy, details
                FROM resilience_snapshots
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [
                {
                    "timestamp": row[0],
                    "overall_risk": row[1],
                    "bridge_count": row[2],
                    "avg_redundancy": row[3],
                    "details": json.loads(row[4]),
                }
                for row in rows
            ]
        finally:
            conn.close()

    def get_active_alerts(self) -> List[PartitionAlert]:
        """Get all unresolved partition alerts."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT alert_id, risk_level, affected_federations, bridge_nodes,
                       message, timestamp, recommendations, resolved
                FROM partition_alerts
                WHERE resolved = 0
                ORDER BY timestamp DESC
            """).fetchall()

            return [
                PartitionAlert(
                    alert_id=row[0],
                    risk_level=PartitionRisk(row[1]),
                    affected_federations=json.loads(row[2]),
                    bridge_nodes=json.loads(row[3]),
                    message=row[4],
                    timestamp=row[5],
                    recommendations=json.loads(row[6]),
                    resolved=bool(row[7]),
                )
                for row in rows
            ]
        finally:
            conn.close()

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE partition_alerts SET resolved = 1 WHERE alert_id = ?",
                (alert_id,)
            )
            conn.commit()
            return True
        finally:
            conn.close()
