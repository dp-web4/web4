"""
Federation Health Monitoring

Track CE: Real-time federation health metrics and alerts.

Key concepts:
1. Health Score: Composite metric combining multiple health factors
2. Health Components:
   - Trust health: Quality and diversity of trust relationships
   - Activity health: Recent activity patterns
   - Reputation health: Reputation stability and trends
   - Economic health: ATP balance and flow
   - Governance health: Proposal activity and voting participation
3. Alert Thresholds: Configurable triggers for health warnings
4. Health History: Track health over time for trend analysis

This provides the monitoring layer needed for federation operators
to maintain healthy federation networks.
"""

import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from enum import Enum
import json
import hashlib

from hardbound.multi_federation import MultiFederationRegistry, FederationRelationship
from hardbound.reputation_aggregation import ReputationAggregator, ReputationScore


class HealthLevel(Enum):
    """Federation health levels."""
    CRITICAL = "critical"      # Immediate attention needed
    WARNING = "warning"        # Issues detected
    HEALTHY = "healthy"        # Normal operation
    EXCELLENT = "excellent"    # Above average health


class AlertType(Enum):
    """Types of health alerts."""
    # Trust alerts
    LOW_TRUST_DIVERSITY = "low_trust_diversity"
    TRUST_CONCENTRATION = "trust_concentration"
    RAPID_TRUST_LOSS = "rapid_trust_loss"

    # Activity alerts
    LOW_ACTIVITY = "low_activity"
    ACTIVITY_SPIKE = "activity_spike"

    # Reputation alerts
    REPUTATION_DECLINE = "reputation_decline"
    REPUTATION_VOLATILITY = "reputation_volatility"

    # Economic alerts
    LOW_ATP_BALANCE = "low_atp_balance"
    ATP_DRAIN = "atp_drain"

    # Governance alerts
    LOW_VOTING_PARTICIPATION = "low_voting_participation"
    STALE_PROPOSALS = "stale_proposals"


@dataclass
class HealthComponent:
    """A component of overall health."""
    name: str
    score: float  # 0.0 to 1.0
    weight: float  # Contribution to overall health
    details: Dict = field(default_factory=dict)


@dataclass
class HealthAlert:
    """A health alert for a federation."""
    alert_id: str
    federation_id: str
    alert_type: AlertType
    level: HealthLevel
    message: str
    timestamp: str
    details: Dict = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class FederationHealthReport:
    """Comprehensive health report for a federation."""
    federation_id: str
    timestamp: str
    overall_health: float  # 0.0 to 1.0
    health_level: HealthLevel

    # Component scores
    trust_health: HealthComponent
    activity_health: HealthComponent
    reputation_health: HealthComponent
    economic_health: HealthComponent
    governance_health: HealthComponent

    # Active alerts
    alerts: List[HealthAlert] = field(default_factory=list)

    # Recommendations
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "federation_id": self.federation_id,
            "timestamp": self.timestamp,
            "overall_health": self.overall_health,
            "health_level": self.health_level.value,
            "trust_health": asdict(self.trust_health),
            "activity_health": asdict(self.activity_health),
            "reputation_health": asdict(self.reputation_health),
            "economic_health": asdict(self.economic_health),
            "governance_health": asdict(self.governance_health),
            "alerts": [
                {**asdict(a), "alert_type": a.alert_type.value, "level": a.level.value}
                for a in self.alerts
            ],
            "recommendations": self.recommendations,
        }


class FederationHealthMonitor:
    """
    Monitor and report federation health.

    Track CE: Provides real-time health monitoring for federations.
    """

    # Default health thresholds
    CRITICAL_THRESHOLD = 0.3
    WARNING_THRESHOLD = 0.5
    HEALTHY_THRESHOLD = 0.7

    def __init__(
        self,
        registry: MultiFederationRegistry,
        reputation_aggregator: Optional[ReputationAggregator] = None,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize health monitor.

        Args:
            registry: Multi-federation registry
            reputation_aggregator: Optional reputation aggregator
            db_path: Database path for health history
        """
        self.registry = registry
        self.reputation = reputation_aggregator or ReputationAggregator(registry)
        self.db_path = db_path or Path("federation_health.db")

        self._init_db()

    def _init_db(self):
        """Initialize health database."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    federation_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    overall_health REAL NOT NULL,
                    health_level TEXT NOT NULL,
                    trust_health REAL,
                    activity_health REAL,
                    reputation_health REAL,
                    economic_health REAL,
                    governance_health REAL,
                    report_json TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_health_fed_time
                    ON health_history(federation_id, timestamp);

                CREATE TABLE IF NOT EXISTS health_alerts (
                    alert_id TEXT PRIMARY KEY,
                    federation_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT,
                    timestamp TEXT NOT NULL,
                    details_json TEXT,
                    acknowledged INTEGER DEFAULT 0,
                    resolved INTEGER DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_alerts_fed
                    ON health_alerts(federation_id);
            """)
            conn.commit()
        finally:
            conn.close()

    def check_health(
        self,
        federation_id: str,
        record_history: bool = True,
    ) -> FederationHealthReport:
        """
        Check the health of a federation.

        Args:
            federation_id: The federation to check
            record_history: Whether to record in history

        Returns:
            FederationHealthReport with all health components
        """
        now = datetime.now(timezone.utc).isoformat()

        # Calculate component health scores
        trust_health = self._check_trust_health(federation_id)
        activity_health = self._check_activity_health(federation_id)
        reputation_health = self._check_reputation_health(federation_id)
        economic_health = self._check_economic_health(federation_id)
        governance_health = self._check_governance_health(federation_id)

        # Calculate overall health (weighted average)
        components = [trust_health, activity_health, reputation_health,
                     economic_health, governance_health]
        total_weight = sum(c.weight for c in components)
        overall_health = sum(c.score * c.weight for c in components) / total_weight

        # Determine health level
        health_level = self._determine_level(overall_health)

        # Check for alerts
        alerts = self._check_alerts(
            federation_id,
            trust_health, activity_health, reputation_health,
            economic_health, governance_health
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_health, trust_health, activity_health,
            reputation_health, economic_health, governance_health
        )

        report = FederationHealthReport(
            federation_id=federation_id,
            timestamp=now,
            overall_health=overall_health,
            health_level=health_level,
            trust_health=trust_health,
            activity_health=activity_health,
            reputation_health=reputation_health,
            economic_health=economic_health,
            governance_health=governance_health,
            alerts=alerts,
            recommendations=recommendations,
        )

        if record_history:
            self._record_health(report)

        return report

    def _check_trust_health(self, federation_id: str) -> HealthComponent:
        """Check trust relationship health."""
        relationships = self.registry.get_all_relationships()

        # Incoming trust
        incoming = [r for r in relationships if r.target_federation_id == federation_id]
        outgoing = [r for r in relationships if r.source_federation_id == federation_id]

        # Trust diversity (number of unique trust sources)
        trust_sources = len(incoming)
        diversity_score = min(1.0, trust_sources / 5)  # 5+ sources = full score

        # Trust quality (average trust level)
        if incoming:
            avg_trust = sum(r.trust_score for r in incoming) / len(incoming)
        else:
            avg_trust = 0.0

        # Bidirectional relationships (both sides trust each other)
        incoming_ids = {r.source_federation_id for r in incoming}
        outgoing_ids = {r.target_federation_id for r in outgoing}
        bidirectional = len(incoming_ids & outgoing_ids)
        bidirectional_ratio = bidirectional / max(1, len(incoming_ids))

        # Combined trust health
        health_score = (
            0.4 * diversity_score +
            0.4 * avg_trust +
            0.2 * bidirectional_ratio
        )

        return HealthComponent(
            name="Trust Health",
            score=health_score,
            weight=1.0,
            details={
                "incoming_trust_count": len(incoming),
                "outgoing_trust_count": len(outgoing),
                "avg_incoming_trust": avg_trust,
                "bidirectional_ratio": bidirectional_ratio,
                "trust_sources": trust_sources,
            }
        )

    def _check_activity_health(self, federation_id: str) -> HealthComponent:
        """Check activity level health."""
        # For now, return baseline activity (would need activity tracker)
        # This would integrate with ReputationHistory or separate activity log

        return HealthComponent(
            name="Activity Health",
            score=0.5,  # Default moderate activity
            weight=0.8,
            details={
                "activity_level": "moderate",
                "note": "Activity tracking not fully integrated",
            }
        )

    def _check_reputation_health(self, federation_id: str) -> HealthComponent:
        """Check reputation health."""
        try:
            rep = self.reputation.calculate_reputation(federation_id, force_refresh=True)

            # Reputation score directly
            rep_score = rep.global_reputation

            # Confidence factor
            confidence = rep.confidence

            # Combined reputation health
            health_score = 0.7 * rep_score + 0.3 * confidence

            return HealthComponent(
                name="Reputation Health",
                score=health_score,
                weight=1.0,
                details={
                    "global_reputation": rep.global_reputation,
                    "tier": rep.tier.value,
                    "confidence": rep.confidence,
                    "incoming_trust_count": rep.incoming_trust_count,
                }
            )
        except Exception:
            return HealthComponent(
                name="Reputation Health",
                score=0.0,
                weight=1.0,
                details={"error": "Could not calculate reputation"}
            )

    def _check_economic_health(self, federation_id: str) -> HealthComponent:
        """Check economic health (ATP balance and flow)."""
        # Would integrate with ATP/economic systems
        # For now, return baseline

        return HealthComponent(
            name="Economic Health",
            score=0.6,  # Default moderate economic health
            weight=0.7,
            details={
                "note": "Economic tracking not fully integrated",
            }
        )

    def _check_governance_health(self, federation_id: str) -> HealthComponent:
        """Check governance health (voting, proposals)."""
        # Would integrate with governance systems
        # For now, return baseline

        return HealthComponent(
            name="Governance Health",
            score=0.5,  # Default moderate governance health
            weight=0.6,
            details={
                "note": "Governance tracking not fully integrated",
            }
        )

    def _determine_level(self, overall_health: float) -> HealthLevel:
        """Determine health level from overall score."""
        if overall_health >= self.HEALTHY_THRESHOLD:
            return HealthLevel.EXCELLENT if overall_health >= 0.85 else HealthLevel.HEALTHY
        elif overall_health >= self.WARNING_THRESHOLD:
            return HealthLevel.WARNING
        else:
            return HealthLevel.CRITICAL

    def _check_alerts(
        self,
        federation_id: str,
        trust_health: HealthComponent,
        activity_health: HealthComponent,
        reputation_health: HealthComponent,
        economic_health: HealthComponent,
        governance_health: HealthComponent,
    ) -> List[HealthAlert]:
        """Generate alerts based on health components."""
        alerts = []
        now = datetime.now(timezone.utc).isoformat()

        # Trust alerts
        if trust_health.details.get("incoming_trust_count", 0) < 2:
            alerts.append(HealthAlert(
                alert_id=self._generate_alert_id(federation_id, AlertType.LOW_TRUST_DIVERSITY),
                federation_id=federation_id,
                alert_type=AlertType.LOW_TRUST_DIVERSITY,
                level=HealthLevel.WARNING,
                message="Federation has few trust sources",
                timestamp=now,
                details={"trust_sources": trust_health.details.get("incoming_trust_count", 0)}
            ))

        # Reputation alerts
        rep_score = reputation_health.details.get("global_reputation", 0)
        if rep_score < 0.3:
            alerts.append(HealthAlert(
                alert_id=self._generate_alert_id(federation_id, AlertType.REPUTATION_DECLINE),
                federation_id=federation_id,
                alert_type=AlertType.REPUTATION_DECLINE,
                level=HealthLevel.WARNING if rep_score > 0.1 else HealthLevel.CRITICAL,
                message="Federation has low reputation",
                timestamp=now,
                details={"reputation": rep_score}
            ))

        # Store alerts
        for alert in alerts:
            self._store_alert(alert)

        return alerts

    def _generate_recommendations(
        self,
        overall_health: float,
        trust_health: HealthComponent,
        activity_health: HealthComponent,
        reputation_health: HealthComponent,
        economic_health: HealthComponent,
        governance_health: HealthComponent,
    ) -> List[str]:
        """Generate recommendations based on health analysis."""
        recommendations = []

        if trust_health.score < 0.5:
            recommendations.append(
                "Consider establishing trust relationships with more federations"
            )

        if trust_health.details.get("bidirectional_ratio", 0) < 0.5:
            recommendations.append(
                "Many trust relationships are one-way; consider reciprocating trust"
            )

        if reputation_health.score < 0.5:
            recommendations.append(
                "Reputation is low; focus on building trust with established federations"
            )

        if overall_health < 0.5:
            recommendations.append(
                "Overall health is below optimal; review all health components for improvement"
            )

        return recommendations

    def _generate_alert_id(self, federation_id: str, alert_type: AlertType) -> str:
        """Generate unique alert ID."""
        now = datetime.now(timezone.utc).isoformat()
        hash_input = f"{federation_id}:{alert_type.value}:{now}"
        return f"alert:{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def _store_alert(self, alert: HealthAlert):
        """Store alert in database."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO health_alerts
                (alert_id, federation_id, alert_type, level, message, timestamp,
                 details_json, acknowledged, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.federation_id,
                alert.alert_type.value,
                alert.level.value,
                alert.message,
                alert.timestamp,
                json.dumps(alert.details),
                int(alert.acknowledged),
                int(alert.resolved),
            ))
            conn.commit()
        finally:
            conn.close()

    def _record_health(self, report: FederationHealthReport):
        """Record health report in history."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO health_history
                (federation_id, timestamp, overall_health, health_level,
                 trust_health, activity_health, reputation_health,
                 economic_health, governance_health, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.federation_id,
                report.timestamp,
                report.overall_health,
                report.health_level.value,
                report.trust_health.score,
                report.activity_health.score,
                report.reputation_health.score,
                report.economic_health.score,
                report.governance_health.score,
                json.dumps(report.to_dict()),
            ))
            conn.commit()
        finally:
            conn.close()

    def get_health_history(
        self,
        federation_id: str,
        limit: int = 100,
    ) -> List[Dict]:
        """Get health history for a federation."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM health_history
                WHERE federation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (federation_id, limit)).fetchall()

            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_active_alerts(
        self,
        federation_id: Optional[str] = None,
    ) -> List[HealthAlert]:
        """Get active (unresolved) alerts."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            if federation_id:
                rows = conn.execute("""
                    SELECT * FROM health_alerts
                    WHERE federation_id = ? AND resolved = 0
                    ORDER BY timestamp DESC
                """, (federation_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM health_alerts
                    WHERE resolved = 0
                    ORDER BY timestamp DESC
                """).fetchall()

            alerts = []
            for row in rows:
                alerts.append(HealthAlert(
                    alert_id=row["alert_id"],
                    federation_id=row["federation_id"],
                    alert_type=AlertType(row["alert_type"]),
                    level=HealthLevel(row["level"]),
                    message=row["message"],
                    timestamp=row["timestamp"],
                    details=json.loads(row["details_json"] or "{}"),
                    acknowledged=bool(row["acknowledged"]),
                    resolved=bool(row["resolved"]),
                ))

            return alerts
        finally:
            conn.close()

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                UPDATE health_alerts SET acknowledged = 1
                WHERE alert_id = ?
            """, (alert_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                UPDATE health_alerts SET resolved = 1
                WHERE alert_id = ?
            """, (alert_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_federation_summary(self, federation_id: str) -> Dict:
        """Get a quick health summary for a federation."""
        report = self.check_health(federation_id, record_history=False)

        return {
            "federation_id": federation_id,
            "overall_health": report.overall_health,
            "health_level": report.health_level.value,
            "active_alerts": len(report.alerts),
            "top_recommendation": report.recommendations[0] if report.recommendations else None,
        }

    def get_network_health(self) -> Dict:
        """Get overall network health summary."""
        # Get all federations
        relationships = self.registry.get_all_relationships()
        federation_ids = set()
        for r in relationships:
            federation_ids.add(r.source_federation_id)
            federation_ids.add(r.target_federation_id)

        if not federation_ids:
            return {
                "total_federations": 0,
                "avg_health": 0.0,
                "health_distribution": {},
                "total_active_alerts": 0,
            }

        # Check health for each
        health_scores = []
        health_levels = {level: 0 for level in HealthLevel}

        for fed_id in federation_ids:
            report = self.check_health(fed_id, record_history=False)
            health_scores.append(report.overall_health)
            health_levels[report.health_level] += 1

        # Get all active alerts
        alerts = self.get_active_alerts()

        return {
            "total_federations": len(federation_ids),
            "avg_health": sum(health_scores) / len(health_scores),
            "health_distribution": {k.value: v for k, v in health_levels.items()},
            "total_active_alerts": len(alerts),
        }


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Federation Health Monitor - Self Test")
    print("=" * 60)

    import tempfile

    tmp_dir = Path(tempfile.mkdtemp())

    # Create registry and monitor
    registry = MultiFederationRegistry(db_path=tmp_dir / "registry.db")
    monitor = FederationHealthMonitor(
        registry,
        db_path=tmp_dir / "health.db"
    )

    # Create test federations
    registry.register_federation("fed:alpha", "Alpha Federation")
    registry.register_federation("fed:beta", "Beta Federation")
    registry.register_federation("fed:gamma", "Gamma Federation")

    # Establish trust relationships
    registry.establish_trust("fed:alpha", "fed:beta", FederationRelationship.PEER, 0.7)
    registry.establish_trust("fed:beta", "fed:alpha", FederationRelationship.PEER, 0.6)
    registry.establish_trust("fed:gamma", "fed:alpha", FederationRelationship.TRUSTED, 0.8)

    print("\n1. Check health for fed:alpha:")
    report = monitor.check_health("fed:alpha")
    print(f"   Overall Health: {report.overall_health:.2f}")
    print(f"   Health Level: {report.health_level.value}")
    print(f"   Trust Health: {report.trust_health.score:.2f}")
    print(f"   Reputation Health: {report.reputation_health.score:.2f}")
    print(f"   Alerts: {len(report.alerts)}")

    print("\n2. Check health for fed:gamma (new, less trusted):")
    report2 = monitor.check_health("fed:gamma")
    print(f"   Overall Health: {report2.overall_health:.2f}")
    print(f"   Health Level: {report2.health_level.value}")
    print(f"   Alerts: {len(report2.alerts)}")
    for alert in report2.alerts:
        print(f"     - {alert.alert_type.value}: {alert.message}")

    print("\n3. Get network health:")
    network = monitor.get_network_health()
    print(f"   Total Federations: {network['total_federations']}")
    print(f"   Average Health: {network['avg_health']:.2f}")
    print(f"   Health Distribution: {network['health_distribution']}")
    print(f"   Active Alerts: {network['total_active_alerts']}")

    print("\n4. Get health history for fed:alpha:")
    history = monitor.get_health_history("fed:alpha")
    print(f"   History records: {len(history)}")

    print("\n✓ Self-test complete!")
