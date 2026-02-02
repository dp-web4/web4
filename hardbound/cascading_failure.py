"""
Cascading Failure Analysis Module

Track CL: Predicting, detecting, and mitigating cascading failures in federation networks.

Key concepts:
1. Failure Propagation: Model how failures spread through trust relationships
2. Critical Path Analysis: Identify single points of failure in trust chains
3. Contagion Risk: Measure how likely a federation's failure affects others
4. Circuit Breakers: Automatic isolation to prevent cascade spread
5. Recovery Orchestration: Coordinate healing after cascading failures

Cascading failures are the most dangerous attack vector because:
- Single node failure can propagate to entire network
- Economic, trust, and reputation effects compound
- Recovery becomes harder as damage spreads
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from enum import Enum
from collections import defaultdict
import json
import hashlib
import math

from hardbound.multi_federation import MultiFederationRegistry, FederationRelationship
from hardbound.trust_network import TrustNetworkAnalyzer
from hardbound.partition_resilience import PartitionResilienceManager, PartitionRisk


class FailureType(Enum):
    """Types of federation failure."""
    ECONOMIC = "economic"           # ATP exhaustion
    TRUST = "trust"                 # Trust score collapse
    REPUTATION = "reputation"       # Reputation damage
    AVAILABILITY = "availability"   # Node offline
    GOVERNANCE = "governance"       # Governance deadlock
    SECURITY = "security"           # Compromise detected


class PropagationRisk(Enum):
    """Risk level for failure propagation."""
    MINIMAL = "minimal"       # < 10% cascade probability
    LOW = "low"               # 10-30% cascade probability
    MODERATE = "moderate"     # 30-60% cascade probability
    HIGH = "high"             # 60-80% cascade probability
    CRITICAL = "critical"     # > 80% cascade probability


class CircuitBreakerState(Enum):
    """State of a circuit breaker."""
    CLOSED = "closed"         # Normal operation
    OPEN = "open"             # Blocking propagation
    HALF_OPEN = "half_open"   # Testing recovery


@dataclass
class FailureEvent:
    """Record of a federation failure."""
    event_id: str
    federation_id: str
    failure_type: FailureType
    severity: float  # 0.0 to 1.0
    detected_at: str
    resolved_at: str = ""
    propagated_to: List[str] = field(default_factory=list)
    circuit_breaker_triggered: bool = False
    recovery_actions: List[str] = field(default_factory=list)


@dataclass
class CascadeSimulation:
    """Result of a cascade simulation."""
    origin_federation: str
    failure_type: FailureType
    initial_severity: float
    propagation_rounds: int
    affected_federations: Dict[str, float]  # federation_id -> damage level
    total_network_damage: float
    propagation_path: List[Tuple[str, str, float]]  # (from, to, damage)
    recommendations: List[str]


@dataclass
class CircuitBreaker:
    """Circuit breaker for containing cascades."""
    breaker_id: str
    federation_id: str
    state: CircuitBreakerState
    failure_count: int
    last_failure: str
    last_success: str
    threshold: int  # Failures before opening
    timeout_seconds: int  # How long to stay open
    affected_relationships: List[str]


@dataclass
class ContagionScore:
    """Contagion risk score for a federation."""
    federation_id: str
    outbound_risk: float  # Risk of spreading failure
    inbound_risk: float   # Risk of receiving failure
    systemic_importance: float  # Impact if this federation fails
    isolation_score: float  # How isolated from cascades
    recommended_monitoring: str


class CascadingFailureAnalyzer:
    """
    Analyze and prevent cascading failures in federation networks.

    Track CL: Provides tools for understanding and mitigating cascade risks.
    """

    # Propagation damping factors
    TRUST_PROPAGATION_FACTOR = 0.6   # How much trust failures propagate
    ECONOMIC_PROPAGATION_FACTOR = 0.4  # How much economic failures propagate
    REPUTATION_PROPAGATION_FACTOR = 0.5  # How much reputation failures propagate

    # Circuit breaker settings
    DEFAULT_FAILURE_THRESHOLD = 3
    DEFAULT_TIMEOUT_SECONDS = 300

    # Simulation parameters
    MAX_PROPAGATION_ROUNDS = 10
    MIN_PROPAGATION_THRESHOLD = 0.1  # Stop when damage < 10%

    def __init__(
        self,
        registry: MultiFederationRegistry,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize cascade analyzer.

        Args:
            registry: Multi-federation registry
            db_path: Database path for cascade history
        """
        self.registry = registry
        self.analyzer = TrustNetworkAnalyzer(registry)
        self.db_path = db_path or Path("cascading_failure.db")

        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS failure_events (
                    event_id TEXT PRIMARY KEY,
                    federation_id TEXT NOT NULL,
                    failure_type TEXT NOT NULL,
                    severity REAL NOT NULL,
                    detected_at TEXT NOT NULL,
                    resolved_at TEXT,
                    propagated_to TEXT DEFAULT '[]',
                    circuit_breaker_triggered INTEGER DEFAULT 0,
                    recovery_actions TEXT DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS circuit_breakers (
                    breaker_id TEXT PRIMARY KEY,
                    federation_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    failure_count INTEGER DEFAULT 0,
                    last_failure TEXT,
                    last_success TEXT,
                    threshold INTEGER NOT NULL,
                    timeout_seconds INTEGER NOT NULL,
                    affected_relationships TEXT DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS cascade_simulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    origin_federation TEXT NOT NULL,
                    failure_type TEXT NOT NULL,
                    initial_severity REAL NOT NULL,
                    propagation_rounds INTEGER NOT NULL,
                    affected_count INTEGER NOT NULL,
                    total_damage REAL NOT NULL,
                    simulation_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_failures_federation
                    ON failure_events(federation_id);

                CREATE INDEX IF NOT EXISTS idx_breakers_federation
                    ON circuit_breakers(federation_id);
            """)
            conn.commit()
        finally:
            conn.close()

    def simulate_cascade(
        self,
        origin_federation: str,
        failure_type: FailureType,
        initial_severity: float = 1.0,
    ) -> CascadeSimulation:
        """
        Simulate a cascading failure starting from one federation.

        Args:
            origin_federation: Federation where failure originates
            failure_type: Type of failure
            initial_severity: Initial severity (0.0-1.0)

        Returns:
            CascadeSimulation with propagation analysis
        """
        # Get propagation factor for failure type
        prop_factor = self._get_propagation_factor(failure_type)

        # Track damage levels
        affected: Dict[str, float] = {origin_federation: initial_severity}
        propagation_path: List[Tuple[str, str, float]] = []

        # Iteratively propagate failure
        current_round = 0
        newly_affected = {origin_federation: initial_severity}

        while newly_affected and current_round < self.MAX_PROPAGATION_ROUNDS:
            current_round += 1
            next_affected: Dict[str, float] = {}

            for fed_id, damage in newly_affected.items():
                # Get outbound trust relationships
                relationships = [
                    r for r in self.registry.get_all_relationships()
                    if r.source_federation_id == fed_id
                ]

                for rel in relationships:
                    target = rel.target_federation_id

                    # Calculate propagated damage
                    # Factors: trust strength, propagation factor, current damage
                    propagated_damage = damage * rel.trust_score * prop_factor

                    # Apply damping for distance from origin
                    propagated_damage *= (0.8 ** current_round)

                    if propagated_damage < self.MIN_PROPAGATION_THRESHOLD:
                        continue

                    # Check if target already affected
                    if target in affected:
                        # Additional damage compounds (but with diminishing returns)
                        old_damage = affected[target]
                        new_damage = min(1.0, old_damage + propagated_damage * 0.5)
                        if new_damage > old_damage:
                            affected[target] = new_damage
                            next_affected[target] = propagated_damage * 0.5
                    else:
                        affected[target] = propagated_damage
                        next_affected[target] = propagated_damage

                    propagation_path.append((fed_id, target, propagated_damage))

            newly_affected = next_affected

        # Calculate total network damage
        # Get unique federation IDs from relationships
        all_rels = self.registry.get_all_relationships()
        fed_ids = set()
        for rel in all_rels:
            fed_ids.add(rel.source_federation_id)
            fed_ids.add(rel.target_federation_id)
        total_damage = sum(affected.values()) / max(len(fed_ids), 1)

        # Generate recommendations
        recommendations = self._generate_cascade_recommendations(
            origin_federation, affected, propagation_path
        )

        simulation = CascadeSimulation(
            origin_federation=origin_federation,
            failure_type=failure_type,
            initial_severity=initial_severity,
            propagation_rounds=current_round,
            affected_federations=affected,
            total_network_damage=total_damage,
            propagation_path=propagation_path,
            recommendations=recommendations,
        )

        # Store simulation
        self._store_simulation(simulation)

        return simulation

    def _get_propagation_factor(self, failure_type: FailureType) -> float:
        """Get propagation factor for failure type."""
        return {
            FailureType.ECONOMIC: self.ECONOMIC_PROPAGATION_FACTOR,
            FailureType.TRUST: self.TRUST_PROPAGATION_FACTOR,
            FailureType.REPUTATION: self.REPUTATION_PROPAGATION_FACTOR,
            FailureType.AVAILABILITY: 0.3,
            FailureType.GOVERNANCE: 0.2,
            FailureType.SECURITY: 0.7,  # Security failures propagate strongly
        }.get(failure_type, 0.5)

    def _generate_cascade_recommendations(
        self,
        origin: str,
        affected: Dict[str, float],
        path: List[Tuple[str, str, float]]
    ) -> List[str]:
        """Generate recommendations to prevent/mitigate cascade."""
        recommendations = []

        # Find most damaging propagation paths
        critical_edges = sorted(path, key=lambda x: x[2], reverse=True)[:5]

        if critical_edges:
            recommendations.append(
                f"CRITICAL: Primary propagation path through {critical_edges[0][0]} -> {critical_edges[0][1]}. "
                "Consider adding circuit breaker."
            )

        # Check for high-damage federations
        high_damage = [f for f, d in affected.items() if d > 0.5]
        if len(high_damage) > 3:
            recommendations.append(
                f"SYSTEMIC RISK: {len(high_damage)} federations severely affected. "
                "Consider network topology changes to reduce interconnection."
            )

        # Check origin's centrality
        centrality = self.analyzer.calculate_centrality()
        origin_centrality = centrality.get(origin, 0)

        if origin_centrality > 0.3:
            recommendations.append(
                f"HIGH CENTRALITY: Origin federation has {origin_centrality:.0%} centrality. "
                "Reduce dependence on single federation."
            )

        # Recovery recommendations
        if len(affected) > 5:
            recommendations.append(
                "RECOVERY: Prioritize restoration of affected federations by reverse propagation order."
            )

        return recommendations

    def _store_simulation(self, simulation: CascadeSimulation):
        """Store simulation results."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO cascade_simulations
                (timestamp, origin_federation, failure_type, initial_severity,
                 propagation_rounds, affected_count, total_damage, simulation_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(timezone.utc).isoformat(),
                simulation.origin_federation,
                simulation.failure_type.value,
                simulation.initial_severity,
                simulation.propagation_rounds,
                len(simulation.affected_federations),
                simulation.total_network_damage,
                json.dumps({
                    "affected": simulation.affected_federations,
                    "path": simulation.propagation_path,
                    "recommendations": simulation.recommendations,
                }),
            ))
            conn.commit()
        finally:
            conn.close()

    def calculate_contagion_scores(self) -> Dict[str, ContagionScore]:
        """
        Calculate contagion risk scores for all federations.

        Returns:
            Dict mapping federation_id to ContagionScore
        """
        scores: Dict[str, ContagionScore] = {}

        # Get unique federation IDs from relationships
        all_rels = self.registry.get_all_relationships()
        fed_ids = set()
        for rel in all_rels:
            fed_ids.add(rel.source_federation_id)
            fed_ids.add(rel.target_federation_id)

        centrality = self.analyzer.calculate_centrality()

        for fed_id in fed_ids:

            # Calculate outbound risk (how much this fed could spread failure)
            outbound_rels = [
                r for r in self.registry.get_all_relationships()
                if r.source_federation_id == fed_id
            ]
            outbound_risk = sum(r.trust_score for r in outbound_rels) / max(len(outbound_rels), 1)
            outbound_risk *= centrality.get(fed_id, 0.1)

            # Calculate inbound risk (how vulnerable to receiving failure)
            inbound_rels = [
                r for r in self.registry.get_all_relationships()
                if r.target_federation_id == fed_id
            ]
            inbound_risk = sum(r.trust_score for r in inbound_rels) / max(len(inbound_rels), 1)

            # Systemic importance based on centrality and relationships
            systemic_importance = centrality.get(fed_id, 0) * (1 + len(outbound_rels) * 0.1)

            # Isolation score (inverse of connectivity)
            total_rels = len(outbound_rels) + len(inbound_rels)
            isolation_score = 1.0 / (1 + total_rels * 0.2)

            # Determine monitoring recommendation
            if systemic_importance > 0.5:
                monitoring = "CRITICAL - continuous monitoring required"
            elif outbound_risk > 0.4:
                monitoring = "HIGH - frequent health checks"
            elif inbound_risk > 0.3:
                monitoring = "MODERATE - regular monitoring"
            else:
                monitoring = "STANDARD - periodic checks"

            scores[fed_id] = ContagionScore(
                federation_id=fed_id,
                outbound_risk=min(1.0, outbound_risk),
                inbound_risk=min(1.0, inbound_risk),
                systemic_importance=min(1.0, systemic_importance),
                isolation_score=isolation_score,
                recommended_monitoring=monitoring,
            )

        return scores

    def identify_critical_paths(self) -> List[Dict]:
        """
        Identify critical failure propagation paths.

        Returns:
            List of critical path descriptions
        """
        critical_paths = []

        # Get high-centrality nodes
        centrality = self.analyzer.calculate_centrality()
        high_centrality = [
            (fed_id, score)
            for fed_id, score in centrality.items()
            if score > 0.2
        ]
        high_centrality.sort(key=lambda x: x[1], reverse=True)

        # Simulate failure for each high-centrality federation
        for fed_id, cent_score in high_centrality[:5]:
            simulation = self.simulate_cascade(
                fed_id,
                FailureType.TRUST,
                initial_severity=0.8
            )

            if simulation.total_network_damage > 0.3:
                critical_paths.append({
                    "origin": fed_id,
                    "centrality": cent_score,
                    "affected_count": len(simulation.affected_federations),
                    "network_damage": simulation.total_network_damage,
                    "propagation_rounds": simulation.propagation_rounds,
                    "primary_path": simulation.propagation_path[:5],
                })

        return critical_paths

    def get_or_create_circuit_breaker(self, federation_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for a federation."""
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM circuit_breakers WHERE federation_id = ?",
                (federation_id,)
            ).fetchone()

            if row:
                return CircuitBreaker(
                    breaker_id=row[0],
                    federation_id=row[1],
                    state=CircuitBreakerState(row[2]),
                    failure_count=row[3],
                    last_failure=row[4] or "",
                    last_success=row[5] or "",
                    threshold=row[6],
                    timeout_seconds=row[7],
                    affected_relationships=json.loads(row[8]),
                )

            # Create new breaker
            breaker_id = hashlib.sha256(
                f"{federation_id}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]

            breaker = CircuitBreaker(
                breaker_id=breaker_id,
                federation_id=federation_id,
                state=CircuitBreakerState.CLOSED,
                failure_count=0,
                last_failure="",
                last_success=datetime.now(timezone.utc).isoformat(),
                threshold=self.DEFAULT_FAILURE_THRESHOLD,
                timeout_seconds=self.DEFAULT_TIMEOUT_SECONDS,
                affected_relationships=[],
            )

            conn.execute("""
                INSERT INTO circuit_breakers
                (breaker_id, federation_id, state, failure_count, last_failure,
                 last_success, threshold, timeout_seconds, affected_relationships)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                breaker.breaker_id,
                breaker.federation_id,
                breaker.state.value,
                breaker.failure_count,
                breaker.last_failure,
                breaker.last_success,
                breaker.threshold,
                breaker.timeout_seconds,
                json.dumps(breaker.affected_relationships),
            ))
            conn.commit()

            return breaker

        finally:
            conn.close()

    def record_failure(
        self,
        federation_id: str,
        failure_type: FailureType,
        severity: float,
    ) -> Tuple[FailureEvent, bool]:
        """
        Record a failure event and check if circuit breaker should trip.

        Args:
            federation_id: Federation that failed
            failure_type: Type of failure
            severity: Severity (0.0-1.0)

        Returns:
            Tuple of (FailureEvent, circuit_breaker_tripped)
        """
        now = datetime.now(timezone.utc)
        event_id = hashlib.sha256(
            f"{federation_id}{now.isoformat()}".encode()
        ).hexdigest()[:16]

        # Create failure event
        event = FailureEvent(
            event_id=event_id,
            federation_id=federation_id,
            failure_type=failure_type,
            severity=severity,
            detected_at=now.isoformat(),
        )

        # Update circuit breaker
        breaker = self.get_or_create_circuit_breaker(federation_id)
        breaker.failure_count += 1
        breaker.last_failure = now.isoformat()

        # Check if breaker should trip
        tripped = False
        if breaker.state == CircuitBreakerState.CLOSED:
            if breaker.failure_count >= breaker.threshold:
                breaker.state = CircuitBreakerState.OPEN
                event.circuit_breaker_triggered = True
                tripped = True

                # Get affected relationships
                rels = self.registry.get_all_relationships()
                affected = [
                    r.target_federation_id
                    for r in rels
                    if r.source_federation_id == federation_id
                ]
                breaker.affected_relationships = affected

        # Store event and update breaker
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO failure_events
                (event_id, federation_id, failure_type, severity, detected_at,
                 circuit_breaker_triggered)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.federation_id,
                event.failure_type.value,
                event.severity,
                event.detected_at,
                1 if event.circuit_breaker_triggered else 0,
            ))

            conn.execute("""
                UPDATE circuit_breakers
                SET state = ?, failure_count = ?, last_failure = ?,
                    affected_relationships = ?
                WHERE breaker_id = ?
            """, (
                breaker.state.value,
                breaker.failure_count,
                breaker.last_failure,
                json.dumps(breaker.affected_relationships),
                breaker.breaker_id,
            ))
            conn.commit()
        finally:
            conn.close()

        return event, tripped

    def check_circuit_breaker_timeout(self, federation_id: str) -> bool:
        """
        Check if circuit breaker timeout has elapsed and transition to half-open.

        Returns:
            True if breaker transitioned to half-open
        """
        breaker = self.get_or_create_circuit_breaker(federation_id)

        if breaker.state != CircuitBreakerState.OPEN:
            return False

        # Check if timeout elapsed
        if not breaker.last_failure:
            return False

        last_failure = datetime.fromisoformat(breaker.last_failure.replace('Z', '+00:00'))
        timeout = timedelta(seconds=breaker.timeout_seconds)

        if datetime.now(timezone.utc) > last_failure + timeout:
            # Transition to half-open
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    UPDATE circuit_breakers
                    SET state = ?
                    WHERE breaker_id = ?
                """, (CircuitBreakerState.HALF_OPEN.value, breaker.breaker_id))
                conn.commit()
            finally:
                conn.close()
            return True

        return False

    def record_success(self, federation_id: str) -> bool:
        """
        Record a successful operation and potentially close circuit breaker.

        Returns:
            True if breaker transitioned to closed
        """
        breaker = self.get_or_create_circuit_breaker(federation_id)

        now = datetime.now(timezone.utc)

        if breaker.state == CircuitBreakerState.HALF_OPEN:
            # Success in half-open means close the breaker
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    UPDATE circuit_breakers
                    SET state = ?, failure_count = 0, last_success = ?,
                        affected_relationships = '[]'
                    WHERE breaker_id = ?
                """, (
                    CircuitBreakerState.CLOSED.value,
                    now.isoformat(),
                    breaker.breaker_id,
                ))
                conn.commit()
            finally:
                conn.close()
            return True

        elif breaker.state == CircuitBreakerState.CLOSED:
            # Success in closed state - update last_success
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    UPDATE circuit_breakers
                    SET last_success = ?
                    WHERE breaker_id = ?
                """, (now.isoformat(), breaker.breaker_id))
                conn.commit()
            finally:
                conn.close()

        return False

    def get_network_health_summary(self) -> Dict:
        """
        Get overall network health summary regarding cascade risks.

        Returns:
            Dict with network health metrics
        """
        # Get unique federation IDs from relationships
        all_rels = self.registry.get_all_relationships()
        fed_ids = set()
        for rel in all_rels:
            fed_ids.add(rel.source_federation_id)
            fed_ids.add(rel.target_federation_id)

        contagion_scores = self.calculate_contagion_scores()

        # Calculate aggregate metrics
        if not contagion_scores:
            return {
                "federation_count": len(fed_ids),
                "overall_risk": "unknown",
                "systemic_federations": [],
                "circuit_breakers_open": 0,
                "recent_failures": 0,
            }

        avg_outbound_risk = sum(s.outbound_risk for s in contagion_scores.values()) / len(contagion_scores)
        avg_inbound_risk = sum(s.inbound_risk for s in contagion_scores.values()) / len(contagion_scores)

        # Identify systemic federations
        systemic = [
            fed_id for fed_id, score in contagion_scores.items()
            if score.systemic_importance > 0.5
        ]

        # Count open circuit breakers
        conn = sqlite3.connect(self.db_path)
        try:
            open_breakers = conn.execute(
                "SELECT COUNT(*) FROM circuit_breakers WHERE state = 'open'"
            ).fetchone()[0]

            # Count recent failures (last 24 hours)
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            recent_failures = conn.execute(
                "SELECT COUNT(*) FROM failure_events WHERE detected_at > ?",
                (yesterday,)
            ).fetchone()[0]
        finally:
            conn.close()

        # Determine overall risk level
        if open_breakers > 2 or recent_failures > 10:
            overall_risk = "critical"
        elif open_breakers > 0 or recent_failures > 5 or avg_outbound_risk > 0.5:
            overall_risk = "elevated"
        elif avg_outbound_risk > 0.3:
            overall_risk = "moderate"
        else:
            overall_risk = "normal"

        return {
            "federation_count": len(fed_ids),
            "overall_risk": overall_risk,
            "average_outbound_risk": avg_outbound_risk,
            "average_inbound_risk": avg_inbound_risk,
            "systemic_federations": systemic,
            "systemic_count": len(systemic),
            "circuit_breakers_open": open_breakers,
            "recent_failures": recent_failures,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_failure_history(
        self,
        federation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[FailureEvent]:
        """Get failure event history."""
        conn = sqlite3.connect(self.db_path)
        try:
            if federation_id:
                rows = conn.execute("""
                    SELECT event_id, federation_id, failure_type, severity,
                           detected_at, resolved_at, propagated_to,
                           circuit_breaker_triggered, recovery_actions
                    FROM failure_events
                    WHERE federation_id = ?
                    ORDER BY detected_at DESC
                    LIMIT ?
                """, (federation_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT event_id, federation_id, failure_type, severity,
                           detected_at, resolved_at, propagated_to,
                           circuit_breaker_triggered, recovery_actions
                    FROM failure_events
                    ORDER BY detected_at DESC
                    LIMIT ?
                """, (limit,)).fetchall()

            return [
                FailureEvent(
                    event_id=row[0],
                    federation_id=row[1],
                    failure_type=FailureType(row[2]),
                    severity=row[3],
                    detected_at=row[4],
                    resolved_at=row[5] or "",
                    propagated_to=json.loads(row[6]) if row[6] else [],
                    circuit_breaker_triggered=bool(row[7]),
                    recovery_actions=json.loads(row[8]) if row[8] else [],
                )
                for row in rows
            ]
        finally:
            conn.close()
