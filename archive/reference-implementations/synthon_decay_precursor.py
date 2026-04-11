"""
Synthon Decay Precursor Detection
==================================

Extends synthon_lifecycle_detection.py with predictive capability:
1. PrecursorSignature — Quantitative early warning signs of decay
2. DecayPredictor — Time-series forecasting of synthon health
3. InterventionProtocol — Actions to take at each decay stage
4. RecoveryDynamics — Can a decaying synthon be resurrected?
5. CascadePreventor — Prevent cascading decay in adjacent synthons
6. DecayClassifier — Categorize decay root causes
7. PrecursorAuditTrail — Hash-chained precursor detection log

Key insight: Intervention costs increase exponentially with decay stage.
Early detection at WARNING stage costs ~10% of intervention at CRITICAL.

Based on CLAUDE.md: "Monitor for decay signatures with the same
seriousness as formation signatures."
"""

from __future__ import annotations
import hashlib
import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
from collections import deque


# ─── Enums ────────────────────────────────────────────────────────────────────

class SynthonPhase(Enum):
    NASCENT = auto()
    FORMING = auto()
    STABLE = auto()
    STRESSED = auto()
    DISSOLVING = auto()


class PrecursorType(Enum):
    TRUST_ENTROPY_RISE = auto()       # Increasing disorder in trust distribution
    BOUNDARY_PERMEABILITY = auto()    # Boundary becoming porous
    ATP_STARVATION = auto()           # Running out of energy
    WITNESS_EXODUS = auto()           # Witnesses leaving
    COHERENCE_OSCILLATION = auto()    # Trust scores oscillating rather than converging
    MEMBER_ATTRITION = auto()         # Members leaving
    POLICY_FRAGMENTATION = auto()     # Internal policy disagreements


class InterventionType(Enum):
    ATP_INJECTION = auto()            # Inject ATP to stabilize energy
    TRUST_RECALIBRATION = auto()      # Recalibrate trust scores
    BOUNDARY_REINFORCEMENT = auto()   # Strengthen boundaries
    WITNESS_RECRUITMENT = auto()      # Recruit new witnesses
    MEMBER_RECRUITMENT = auto()       # Recruit new members
    GOVERNANCE_ADJUSTMENT = auto()    # Adjust governance parameters
    MERGE_WITH_HEALTHY = auto()       # Merge into a healthy synthon
    CONTROLLED_DISSOLUTION = auto()   # Dissolve gracefully


class DecayStage(Enum):
    NONE = auto()         # No decay detected
    EARLY = auto()        # Subtle precursors only
    MODERATE = auto()     # Clear signals, still reversible
    ADVANCED = auto()     # Significant damage, expensive to reverse
    TERMINAL = auto()     # Irreversible, dissolution recommended


class RecoveryOutcome(Enum):
    FULL_RECOVERY = auto()
    PARTIAL_RECOVERY = auto()
    STABILIZED = auto()
    CONTINUED_DECLINE = auto()
    DISSOLVED = auto()


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class SynthonSnapshot:
    """Point-in-time snapshot of synthon health metrics."""
    timestamp: float = field(default_factory=time.time)
    member_count: int = 0
    trust_entropy: float = 0.0      # Shannon entropy of trust distribution
    trust_mean: float = 0.5
    trust_variance: float = 0.0
    atp_total: float = 0.0
    atp_flow_balance: float = 0.0   # inflow - outflow
    boundary_permeability: float = 0.0  # [0=sealed, 1=open]
    witness_count: int = 0
    coherence_score: float = 0.5    # [0, 1]
    policy_alignment: float = 1.0   # [0, 1]

    @property
    def health_composite(self) -> float:
        """Weighted composite health score."""
        weights = {
            "trust": 0.25,
            "energy": 0.20,
            "boundary": 0.15,
            "coherence": 0.25,
            "witnesses": 0.15,
        }
        trust_health = max(0, 1.0 - self.trust_entropy)
        energy_health = min(1.0, self.atp_total / max(self.member_count * 50, 1))
        boundary_health = 1.0 - self.boundary_permeability
        witness_health = min(1.0, self.witness_count / max(self.member_count, 1))

        return (weights["trust"] * trust_health +
                weights["energy"] * energy_health +
                weights["boundary"] * boundary_health +
                weights["coherence"] * self.coherence_score +
                weights["witnesses"] * witness_health)


@dataclass
class PrecursorSignal:
    """A detected precursor of decay."""
    precursor_type: PrecursorType
    severity: float  # [0, 1]
    confidence: float  # [0, 1]
    trend: float  # Rate of change (positive = worsening)
    metric_value: float
    threshold: float
    detected_at: float = field(default_factory=time.time)
    description: str = ""

    @property
    def urgency(self) -> float:
        """How urgently this needs attention."""
        return self.severity * self.confidence * (1.0 + max(0, self.trend))


@dataclass
class InterventionAction:
    """A recommended intervention action."""
    intervention_type: InterventionType
    priority: int  # 1=highest
    estimated_cost_atp: float
    estimated_effectiveness: float  # [0, 1]
    description: str
    prerequisites: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)


@dataclass
class RecoveryRecord:
    """Record of a recovery attempt."""
    synthon_id: str
    stage_at_start: DecayStage
    interventions_applied: List[InterventionType]
    total_cost_atp: float
    health_before: float
    health_after: float
    outcome: RecoveryOutcome
    duration: float  # seconds
    timestamp: float = field(default_factory=time.time)


@dataclass
class CascadeRisk:
    """Risk assessment for cascade decay."""
    source_synthon: str
    at_risk_synthons: List[str]
    risk_level: float  # [0, 1]
    propagation_path: List[str]
    estimated_damage: float
    preventive_actions: List[str]


# ─── Decay Predictor ─────────────────────────────────────────────────────────

class DecayPredictor:
    """Time-series based decay prediction using exponential smoothing."""

    def __init__(self, window_size: int = 10, alpha: float = 0.3):
        self.window_size = window_size
        self.alpha = alpha  # Smoothing factor
        self.history: Dict[str, deque] = {}  # synthon_id → snapshots

    def record(self, synthon_id: str, snapshot: SynthonSnapshot):
        """Record a health snapshot."""
        if synthon_id not in self.history:
            self.history[synthon_id] = deque(maxlen=self.window_size)
        self.history[synthon_id].append(snapshot)

    def predict_health(self, synthon_id: str,
                       horizon_steps: int = 3) -> Optional[List[float]]:
        """Predict future health composite values."""
        history = self.history.get(synthon_id)
        if not history or len(history) < 3:
            return None

        # Simple exponential smoothing forecast
        values = [s.health_composite for s in history]

        # Calculate smoothed values
        smoothed = values[0]
        for v in values[1:]:
            smoothed = self.alpha * v + (1 - self.alpha) * smoothed

        # Calculate trend
        if len(values) >= 2:
            recent_trend = values[-1] - values[-2]
            avg_trend = (values[-1] - values[0]) / (len(values) - 1)
            trend = 0.5 * recent_trend + 0.5 * avg_trend
        else:
            trend = 0.0

        # Project forward
        predictions = []
        for step in range(1, horizon_steps + 1):
            projected = smoothed + trend * step
            projected = max(0.0, min(1.0, projected))
            predictions.append(projected)

        return predictions

    def predict_time_to_threshold(self, synthon_id: str,
                                  threshold: float = 0.3) -> Optional[float]:
        """Predict time steps until health drops below threshold."""
        predictions = self.predict_health(synthon_id, horizon_steps=20)
        if not predictions:
            return None

        for i, p in enumerate(predictions):
            if p <= threshold:
                return float(i + 1)

        return None  # Won't reach threshold in horizon

    def detect_trend(self, synthon_id: str) -> Optional[Dict]:
        """Detect the current trend direction and magnitude."""
        history = self.history.get(synthon_id)
        if not history or len(history) < 3:
            return None

        values = [s.health_composite for s in history]

        # Linear regression (simple)
        n = len(values)
        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator > 0 else 0.0

        # Classify trend
        if slope < -0.02:
            direction = "declining"
        elif slope > 0.02:
            direction = "improving"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "slope": slope,
            "current_health": values[-1],
            "min_health": min(values),
            "max_health": max(values),
            "volatility": max(values) - min(values),
        }


# ─── Precursor Detector ──────────────────────────────────────────────────────

class PrecursorDetector:
    """Detects early warning signs of synthon decay."""

    def __init__(self,
                 entropy_threshold: float = 0.6,
                 permeability_threshold: float = 0.5,
                 atp_starvation_threshold: float = 30.0,
                 witness_loss_rate: float = 0.3,
                 oscillation_threshold: float = 0.15,
                 attrition_threshold: float = 0.2,
                 policy_threshold: float = 0.6):
        self.entropy_threshold = entropy_threshold
        self.permeability_threshold = permeability_threshold
        self.atp_starvation_threshold = atp_starvation_threshold
        self.witness_loss_rate = witness_loss_rate
        self.oscillation_threshold = oscillation_threshold
        self.attrition_threshold = attrition_threshold
        self.policy_threshold = policy_threshold

    def detect(self, current: SynthonSnapshot,
               previous: Optional[SynthonSnapshot] = None) -> List[PrecursorSignal]:
        """Detect all active precursor signals."""
        signals = []

        # Trust entropy rising
        if current.trust_entropy > self.entropy_threshold:
            severity = min(1.0, (current.trust_entropy - self.entropy_threshold) /
                           (1.0 - self.entropy_threshold))
            trend = 0.0
            if previous:
                trend = current.trust_entropy - previous.trust_entropy
            signals.append(PrecursorSignal(
                precursor_type=PrecursorType.TRUST_ENTROPY_RISE,
                severity=severity,
                confidence=0.8,
                trend=trend,
                metric_value=current.trust_entropy,
                threshold=self.entropy_threshold,
                description=f"Trust entropy {current.trust_entropy:.3f} > {self.entropy_threshold}",
            ))

        # Boundary permeability
        if current.boundary_permeability > self.permeability_threshold:
            severity = min(1.0, (current.boundary_permeability - self.permeability_threshold) /
                           (1.0 - self.permeability_threshold))
            trend = 0.0
            if previous:
                trend = current.boundary_permeability - previous.boundary_permeability
            signals.append(PrecursorSignal(
                precursor_type=PrecursorType.BOUNDARY_PERMEABILITY,
                severity=severity,
                confidence=0.85,
                trend=trend,
                metric_value=current.boundary_permeability,
                threshold=self.permeability_threshold,
            ))

        # ATP starvation
        atp_per_member = current.atp_total / max(current.member_count, 1)
        if atp_per_member < self.atp_starvation_threshold:
            severity = min(1.0, 1.0 - (atp_per_member / self.atp_starvation_threshold))
            trend = 0.0
            if previous:
                prev_per = previous.atp_total / max(previous.member_count, 1)
                trend = -(atp_per_member - prev_per) / max(prev_per, 1)  # Negative is worsening
            signals.append(PrecursorSignal(
                precursor_type=PrecursorType.ATP_STARVATION,
                severity=severity,
                confidence=0.9,
                trend=max(0, trend),
                metric_value=atp_per_member,
                threshold=self.atp_starvation_threshold,
            ))

        # Witness exodus
        if previous and previous.witness_count > 0:
            loss_rate = 1.0 - (current.witness_count / previous.witness_count)
            if loss_rate > self.witness_loss_rate:
                severity = min(1.0, loss_rate)
                signals.append(PrecursorSignal(
                    precursor_type=PrecursorType.WITNESS_EXODUS,
                    severity=severity,
                    confidence=0.75,
                    trend=loss_rate,
                    metric_value=current.witness_count,
                    threshold=previous.witness_count * (1 - self.witness_loss_rate),
                ))

        # Coherence oscillation (variance of coherence in recent history)
        if current.trust_variance > self.oscillation_threshold:
            severity = min(1.0, current.trust_variance / 0.5)
            signals.append(PrecursorSignal(
                precursor_type=PrecursorType.COHERENCE_OSCILLATION,
                severity=severity,
                confidence=0.7,
                trend=0.0,
                metric_value=current.trust_variance,
                threshold=self.oscillation_threshold,
            ))

        # Member attrition
        if previous and previous.member_count > 0:
            attrition = 1.0 - (current.member_count / previous.member_count)
            if attrition > self.attrition_threshold:
                severity = min(1.0, attrition)
                signals.append(PrecursorSignal(
                    precursor_type=PrecursorType.MEMBER_ATTRITION,
                    severity=severity,
                    confidence=0.85,
                    trend=attrition,
                    metric_value=current.member_count,
                    threshold=previous.member_count * (1 - self.attrition_threshold),
                ))

        # Policy fragmentation
        if current.policy_alignment < self.policy_threshold:
            severity = min(1.0, 1.0 - (current.policy_alignment / self.policy_threshold))
            signals.append(PrecursorSignal(
                precursor_type=PrecursorType.POLICY_FRAGMENTATION,
                severity=severity,
                confidence=0.8,
                trend=0.0,
                metric_value=current.policy_alignment,
                threshold=self.policy_threshold,
            ))

        return signals

    def classify_stage(self, signals: List[PrecursorSignal]) -> DecayStage:
        """Classify the overall decay stage from precursor signals."""
        if not signals:
            return DecayStage.NONE

        max_severity = max(s.severity for s in signals)
        avg_severity = sum(s.severity for s in signals) / len(signals)
        count = len(signals)

        if count >= 4 and avg_severity > 0.6:
            return DecayStage.TERMINAL
        elif count >= 3 and avg_severity > 0.4:
            return DecayStage.ADVANCED
        elif count >= 2 and avg_severity > 0.3:
            return DecayStage.MODERATE
        elif max_severity > 0.2 or count >= 1:
            return DecayStage.EARLY
        else:
            return DecayStage.NONE


# ─── Intervention Protocol ───────────────────────────────────────────────────

class InterventionProtocol:
    """Recommends interventions based on decay stage and precursors."""

    # Cost multipliers by decay stage
    STAGE_COST_MULTIPLIER = {
        DecayStage.NONE: 1.0,
        DecayStage.EARLY: 1.0,
        DecayStage.MODERATE: 2.5,
        DecayStage.ADVANCED: 6.0,
        DecayStage.TERMINAL: 15.0,
    }

    # Effectiveness reduction by stage
    STAGE_EFFECTIVENESS = {
        DecayStage.NONE: 1.0,
        DecayStage.EARLY: 0.95,
        DecayStage.MODERATE: 0.75,
        DecayStage.ADVANCED: 0.45,
        DecayStage.TERMINAL: 0.15,
    }

    PRECURSOR_INTERVENTIONS = {
        PrecursorType.TRUST_ENTROPY_RISE: [
            InterventionAction(InterventionType.TRUST_RECALIBRATION, 1, 50.0, 0.8,
                               "Recalibrate trust scores to reduce entropy"),
            InterventionAction(InterventionType.GOVERNANCE_ADJUSTMENT, 2, 30.0, 0.6,
                               "Adjust governance to incentivize trust convergence"),
        ],
        PrecursorType.BOUNDARY_PERMEABILITY: [
            InterventionAction(InterventionType.BOUNDARY_REINFORCEMENT, 1, 80.0, 0.85,
                               "Reinforce synthon boundaries"),
        ],
        PrecursorType.ATP_STARVATION: [
            InterventionAction(InterventionType.ATP_INJECTION, 1, 200.0, 0.9,
                               "Inject ATP to stabilize energy metabolism"),
        ],
        PrecursorType.WITNESS_EXODUS: [
            InterventionAction(InterventionType.WITNESS_RECRUITMENT, 1, 100.0, 0.7,
                               "Recruit replacement witnesses"),
        ],
        PrecursorType.COHERENCE_OSCILLATION: [
            InterventionAction(InterventionType.GOVERNANCE_ADJUSTMENT, 1, 40.0, 0.65,
                               "Stabilize governance parameters to dampen oscillation"),
        ],
        PrecursorType.MEMBER_ATTRITION: [
            InterventionAction(InterventionType.MEMBER_RECRUITMENT, 1, 150.0, 0.6,
                               "Recruit new members to replace attrition"),
            InterventionAction(InterventionType.ATP_INJECTION, 2, 100.0, 0.4,
                               "Improve incentives to retain members"),
        ],
        PrecursorType.POLICY_FRAGMENTATION: [
            InterventionAction(InterventionType.GOVERNANCE_ADJUSTMENT, 1, 60.0, 0.75,
                               "Resolve policy conflicts through governance"),
        ],
    }

    def recommend(self, signals: List[PrecursorSignal],
                  stage: DecayStage) -> List[InterventionAction]:
        """Recommend interventions based on precursor signals."""
        if stage == DecayStage.NONE:
            return []

        cost_mult = self.STAGE_COST_MULTIPLIER[stage]
        eff_mult = self.STAGE_EFFECTIVENESS[stage]

        recommendations = []
        seen_types = set()

        # Sort signals by urgency
        sorted_signals = sorted(signals, key=lambda s: s.urgency, reverse=True)

        for signal in sorted_signals:
            actions = self.PRECURSOR_INTERVENTIONS.get(signal.precursor_type, [])
            for action in actions:
                if action.intervention_type not in seen_types:
                    # Adjust cost and effectiveness by stage
                    adjusted = InterventionAction(
                        intervention_type=action.intervention_type,
                        priority=action.priority,
                        estimated_cost_atp=action.estimated_cost_atp * cost_mult,
                        estimated_effectiveness=action.estimated_effectiveness * eff_mult,
                        description=action.description,
                    )
                    recommendations.append(adjusted)
                    seen_types.add(action.intervention_type)

        # Terminal stage → add dissolution option
        if stage == DecayStage.TERMINAL:
            recommendations.append(InterventionAction(
                InterventionType.CONTROLLED_DISSOLUTION, 99, 50.0, 1.0,
                "Controlled dissolution to preserve member assets",
            ))

        # Sort by priority
        recommendations.sort(key=lambda a: a.priority)
        return recommendations

    def estimate_total_cost(self, recommendations: List[InterventionAction]) -> float:
        """Estimate total ATP cost of all recommended interventions."""
        return sum(a.estimated_cost_atp for a in recommendations)


# ─── Recovery Dynamics ────────────────────────────────────────────────────────

class RecoveryDynamics:
    """Models recovery dynamics for decaying synthons."""

    def __init__(self):
        self.records: List[RecoveryRecord] = []

    def simulate_recovery(self, synthon_id: str,
                          stage: DecayStage,
                          health_before: float,
                          interventions: List[InterventionType],
                          total_cost: float) -> RecoveryRecord:
        """Simulate recovery outcome based on stage and interventions."""
        effectiveness = InterventionProtocol.STAGE_EFFECTIVENESS[stage]

        # Calculate health improvement
        improvement = 0.0
        for intervention in interventions:
            if intervention == InterventionType.ATP_INJECTION:
                improvement += 0.15 * effectiveness
            elif intervention == InterventionType.TRUST_RECALIBRATION:
                improvement += 0.10 * effectiveness
            elif intervention == InterventionType.BOUNDARY_REINFORCEMENT:
                improvement += 0.08 * effectiveness
            elif intervention == InterventionType.WITNESS_RECRUITMENT:
                improvement += 0.06 * effectiveness
            elif intervention == InterventionType.MEMBER_RECRUITMENT:
                improvement += 0.05 * effectiveness
            elif intervention == InterventionType.GOVERNANCE_ADJUSTMENT:
                improvement += 0.07 * effectiveness
            elif intervention == InterventionType.CONTROLLED_DISSOLUTION:
                improvement = -(health_before)  # Dissolve

        health_after = max(0.0, min(1.0, health_before + improvement))

        # Determine outcome
        if InterventionType.CONTROLLED_DISSOLUTION in interventions:
            outcome = RecoveryOutcome.DISSOLVED
        elif health_after > 0.7:
            outcome = RecoveryOutcome.FULL_RECOVERY
        elif health_after > health_before + 0.05:
            outcome = RecoveryOutcome.PARTIAL_RECOVERY
        elif health_after >= health_before - 0.02:
            outcome = RecoveryOutcome.STABILIZED
        else:
            outcome = RecoveryOutcome.CONTINUED_DECLINE

        record = RecoveryRecord(
            synthon_id=synthon_id,
            stage_at_start=stage,
            interventions_applied=interventions,
            total_cost_atp=total_cost,
            health_before=health_before,
            health_after=health_after,
            outcome=outcome,
            duration=0.0,
        )
        self.records.append(record)
        return record


# ─── Cascade Preventor ───────────────────────────────────────────────────────

class CascadePreventor:
    """Prevents cascade decay across adjacent synthons."""

    def __init__(self):
        self.adjacency: Dict[str, Set[str]] = {}
        self.health_scores: Dict[str, float] = {}

    def register_synthon(self, synthon_id: str, health: float,
                         neighbors: Set[str] = None):
        """Register a synthon with its health and neighbors."""
        self.health_scores[synthon_id] = health
        self.adjacency[synthon_id] = neighbors or set()

    def update_health(self, synthon_id: str, health: float):
        self.health_scores[synthon_id] = health

    def assess_cascade_risk(self, decaying_synthon: str) -> CascadeRisk:
        """Assess the risk of decay cascading from a synthon."""
        at_risk = []
        propagation = [decaying_synthon]
        visited = {decaying_synthon}

        # BFS to find at-risk neighbors
        queue = list(self.adjacency.get(decaying_synthon, set()))
        while queue:
            neighbor = queue.pop(0)
            if neighbor in visited:
                continue
            visited.add(neighbor)

            neighbor_health = self.health_scores.get(neighbor, 0.5)
            # Neighbors with low health are at risk of cascade
            if neighbor_health < 0.6:
                at_risk.append(neighbor)
                propagation.append(neighbor)
                # Check neighbors of at-risk synthon too
                for nn in self.adjacency.get(neighbor, set()):
                    if nn not in visited:
                        queue.append(nn)

        source_health = self.health_scores.get(decaying_synthon, 0.0)
        risk_level = 0.0
        if at_risk:
            avg_at_risk_health = sum(self.health_scores.get(s, 0.5) for s in at_risk) / len(at_risk)
            risk_level = (1.0 - source_health) * (1.0 - avg_at_risk_health)

        estimated_damage = risk_level * len(at_risk) * 100.0  # ATP units

        preventive = []
        if risk_level > 0.5:
            preventive.append("Isolate decaying synthon boundaries")
            preventive.append("ATP injection to at-risk neighbors")
        if risk_level > 0.3:
            preventive.append("Increase witness coverage of at-risk synthons")
        if at_risk:
            preventive.append("Monitor at-risk synthon health metrics")

        return CascadeRisk(
            source_synthon=decaying_synthon,
            at_risk_synthons=at_risk,
            risk_level=risk_level,
            propagation_path=propagation,
            estimated_damage=estimated_damage,
            preventive_actions=preventive,
        )

    def firewall(self, decaying_synthon: str) -> Dict:
        """Create a firewall around a decaying synthon."""
        neighbors = self.adjacency.get(decaying_synthon, set())
        firewalled = []
        for n in neighbors:
            # Conceptually: increase boundary strength
            firewalled.append(n)

        return {
            "source": decaying_synthon,
            "firewalled_boundaries": firewalled,
            "count": len(firewalled),
        }


# ─── Precursor Audit Trail ───────────────────────────────────────────────────

class PrecursorAuditTrail:
    """Hash-chained audit trail for precursor detections."""

    def __init__(self):
        self.entries: List[Dict] = []

    def record(self, synthon_id: str, signals: List[PrecursorSignal],
               stage: DecayStage, interventions: List[InterventionAction]):
        prev_hash = self.entries[-1]["entry_hash"] if self.entries else "genesis"
        content = f"{synthon_id}:{stage.name}:{len(signals)}:{time.time()}:{prev_hash}"
        entry_hash = hashlib.sha256(content.encode()).hexdigest()

        self.entries.append({
            "synthon_id": synthon_id,
            "stage": stage.name,
            "signal_count": len(signals),
            "signal_types": [s.precursor_type.name for s in signals],
            "intervention_count": len(interventions),
            "timestamp": time.time(),
            "prev_hash": prev_hash,
            "entry_hash": entry_hash,
        })

    def verify_chain(self) -> Tuple[bool, List[int]]:
        broken = []
        for i, entry in enumerate(self.entries):
            expected_prev = self.entries[i-1]["entry_hash"] if i > 0 else "genesis"
            if entry["prev_hash"] != expected_prev:
                broken.append(i)
        return len(broken) == 0, broken


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_healthy_snapshot(members: int = 10, **overrides) -> SynthonSnapshot:
    defaults = dict(
        member_count=members,
        trust_entropy=0.3,
        trust_mean=0.7,
        trust_variance=0.05,
        atp_total=members * 100.0,
        atp_flow_balance=10.0,
        boundary_permeability=0.2,
        witness_count=members,
        coherence_score=0.8,
        policy_alignment=0.9,
    )
    defaults.update(overrides)
    return SynthonSnapshot(**defaults)


def _make_declining_snapshot(members: int = 10, step: int = 0) -> SynthonSnapshot:
    """Each step worsens health metrics."""
    decay = step * 0.1
    return SynthonSnapshot(
        member_count=max(3, members - step),
        trust_entropy=0.3 + decay * 0.8,
        trust_mean=0.7 - decay * 0.3,
        trust_variance=0.05 + decay * 0.2,
        atp_total=max(50, members * 100.0 - step * 200),
        atp_flow_balance=10.0 - step * 5,
        boundary_permeability=0.2 + decay * 0.6,
        witness_count=max(1, members - step * 2),
        coherence_score=max(0.1, 0.8 - decay * 0.5),
        policy_alignment=max(0.2, 0.9 - decay * 0.3),
    )


def run_tests():
    results = []

    def check(name, condition, detail=""):
        results.append((name, condition, detail))

    # ─── S1: Snapshot health composite ────────────────────────────────

    healthy = _make_healthy_snapshot()
    check("s1_healthy_score", healthy.health_composite > 0.6,
          f"health={healthy.health_composite:.3f}")

    sick = _make_healthy_snapshot(
        trust_entropy=0.9, atp_total=100, boundary_permeability=0.8,
        coherence_score=0.2, witness_count=2,
    )
    check("s1_sick_score", sick.health_composite < 0.5,
          f"health={sick.health_composite:.3f}")

    check("s1_healthy_gt_sick", healthy.health_composite > sick.health_composite)

    # ─── S2: Precursor detection — trust entropy ──────────────────────

    detector = PrecursorDetector()

    high_entropy = _make_healthy_snapshot(trust_entropy=0.8)
    signals = detector.detect(high_entropy)
    entropy_signals = [s for s in signals if s.precursor_type == PrecursorType.TRUST_ENTROPY_RISE]
    check("s2_entropy_detected", len(entropy_signals) == 1)
    check("s2_entropy_severity", entropy_signals[0].severity > 0.3,
          f"sev={entropy_signals[0].severity:.3f}")

    # No entropy signal when below threshold
    low_entropy = _make_healthy_snapshot(trust_entropy=0.3)
    signals_low = detector.detect(low_entropy)
    check("s2_no_entropy", not any(s.precursor_type == PrecursorType.TRUST_ENTROPY_RISE
                                    for s in signals_low))

    # ─── S3: Precursor detection — boundary permeability ──────────────

    leaky = _make_healthy_snapshot(boundary_permeability=0.7)
    signals_leak = detector.detect(leaky)
    leak_signals = [s for s in signals_leak if s.precursor_type == PrecursorType.BOUNDARY_PERMEABILITY]
    check("s3_leak_detected", len(leak_signals) == 1)
    check("s3_leak_severity", leak_signals[0].severity > 0.2)

    # ─── S4: Precursor detection — ATP starvation ─────────────────────

    starving = _make_healthy_snapshot(atp_total=100, member_count=10)  # 10 per member
    signals_starve = detector.detect(starving)
    starve_signals = [s for s in signals_starve if s.precursor_type == PrecursorType.ATP_STARVATION]
    check("s4_starvation_detected", len(starve_signals) == 1)
    check("s4_starvation_severity", starve_signals[0].severity > 0.5,
          f"sev={starve_signals[0].severity:.3f}")

    # No starvation when well-funded
    funded = _make_healthy_snapshot(atp_total=5000, member_count=10)
    check("s4_no_starvation", not any(
        s.precursor_type == PrecursorType.ATP_STARVATION for s in detector.detect(funded)))

    # ─── S5: Precursor detection — witness exodus ─────────────────────

    prev = _make_healthy_snapshot(witness_count=10)
    curr = _make_healthy_snapshot(witness_count=5)  # 50% loss
    signals_witness = detector.detect(curr, prev)
    witness_signals = [s for s in signals_witness if s.precursor_type == PrecursorType.WITNESS_EXODUS]
    check("s5_witness_exodus", len(witness_signals) == 1)
    check("s5_witness_severity", witness_signals[0].severity >= 0.5,
          f"sev={witness_signals[0].severity:.3f}")

    # No exodus without previous snapshot
    check("s5_no_prev", not any(
        s.precursor_type == PrecursorType.WITNESS_EXODUS for s in detector.detect(curr)))

    # ─── S6: Precursor detection — coherence oscillation ──────────────

    oscillating = _make_healthy_snapshot(trust_variance=0.3)
    signals_osc = detector.detect(oscillating)
    osc_signals = [s for s in signals_osc if s.precursor_type == PrecursorType.COHERENCE_OSCILLATION]
    check("s6_oscillation_detected", len(osc_signals) == 1)

    # ─── S7: Precursor detection — member attrition ───────────────────

    prev_big = _make_healthy_snapshot(member_count=20)
    curr_small = _make_healthy_snapshot(member_count=14)  # 30% loss
    signals_attrition = detector.detect(curr_small, prev_big)
    attrition_signals = [s for s in signals_attrition if s.precursor_type == PrecursorType.MEMBER_ATTRITION]
    check("s7_attrition_detected", len(attrition_signals) == 1)

    # ─── S8: Precursor detection — policy fragmentation ───────────────

    fragmented = _make_healthy_snapshot(policy_alignment=0.3)
    signals_frag = detector.detect(fragmented)
    frag_signals = [s for s in signals_frag if s.precursor_type == PrecursorType.POLICY_FRAGMENTATION]
    check("s8_fragmentation_detected", len(frag_signals) == 1)
    check("s8_frag_severity", frag_signals[0].severity > 0.3)

    # ─── S9: Decay stage classification ───────────────────────────────

    # No signals → NONE
    check("s9_none", detector.classify_stage([]) == DecayStage.NONE)

    # Single low-severity → EARLY
    single = [PrecursorSignal(PrecursorType.TRUST_ENTROPY_RISE, 0.3, 0.8, 0.0, 0.7, 0.6)]
    check("s9_early", detector.classify_stage(single) == DecayStage.EARLY)

    # Two moderate signals → MODERATE
    two_mod = [
        PrecursorSignal(PrecursorType.TRUST_ENTROPY_RISE, 0.5, 0.8, 0.1, 0.8, 0.6),
        PrecursorSignal(PrecursorType.BOUNDARY_PERMEABILITY, 0.5, 0.85, 0.05, 0.7, 0.5),
    ]
    check("s9_moderate", detector.classify_stage(two_mod) == DecayStage.MODERATE)

    # Three high signals → ADVANCED
    three_high = [
        PrecursorSignal(PrecursorType.TRUST_ENTROPY_RISE, 0.6, 0.8, 0.1, 0.9, 0.6),
        PrecursorSignal(PrecursorType.ATP_STARVATION, 0.5, 0.9, 0.2, 10, 30),
        PrecursorSignal(PrecursorType.WITNESS_EXODUS, 0.4, 0.75, 0.3, 3, 7),
    ]
    check("s9_advanced", detector.classify_stage(three_high) == DecayStage.ADVANCED)

    # Four+ high signals → TERMINAL
    terminal = [
        PrecursorSignal(PrecursorType.TRUST_ENTROPY_RISE, 0.8, 0.8, 0.2, 0.95, 0.6),
        PrecursorSignal(PrecursorType.ATP_STARVATION, 0.9, 0.9, 0.3, 5, 30),
        PrecursorSignal(PrecursorType.WITNESS_EXODUS, 0.7, 0.75, 0.4, 1, 7),
        PrecursorSignal(PrecursorType.MEMBER_ATTRITION, 0.6, 0.85, 0.3, 4, 8),
    ]
    check("s9_terminal", detector.classify_stage(terminal) == DecayStage.TERMINAL)

    # ─── S10: Intervention recommendations ────────────────────────────

    protocol = InterventionProtocol()

    # Early stage
    early_signals = [PrecursorSignal(PrecursorType.TRUST_ENTROPY_RISE, 0.4, 0.8, 0.05, 0.7, 0.6)]
    early_recs = protocol.recommend(early_signals, DecayStage.EARLY)
    check("s10_early_has_recs", len(early_recs) > 0)
    check("s10_early_low_cost", protocol.estimate_total_cost(early_recs) < 200)

    # Terminal stage — dissolution offered
    terminal_recs = protocol.recommend(terminal, DecayStage.TERMINAL)
    has_dissolution = any(r.intervention_type == InterventionType.CONTROLLED_DISSOLUTION
                          for r in terminal_recs)
    check("s10_terminal_dissolution", has_dissolution)

    # Cost increases with stage
    moderate_signals = two_mod
    moderate_recs = protocol.recommend(moderate_signals, DecayStage.MODERATE)
    early_cost = protocol.estimate_total_cost(early_recs)
    moderate_cost = protocol.estimate_total_cost(moderate_recs)
    check("s10_cost_increases", moderate_cost > early_cost,
          f"early={early_cost:.0f} moderate={moderate_cost:.0f}")

    # No recommendations for NONE stage
    none_recs = protocol.recommend([], DecayStage.NONE)
    check("s10_none_no_recs", len(none_recs) == 0)

    # Effectiveness decreases with stage
    if early_recs and moderate_recs:
        early_eff = early_recs[0].estimated_effectiveness
        moderate_eff = moderate_recs[0].estimated_effectiveness
        check("s10_eff_decreases", early_eff > moderate_eff,
              f"early={early_eff:.2f} mod={moderate_eff:.2f}")

    # ─── S11: Decay Predictor ─────────────────────────────────────────

    predictor = DecayPredictor(window_size=10)

    # Record declining health
    for step in range(8):
        snapshot = _make_declining_snapshot(members=10, step=step)
        predictor.record("synthon_1", snapshot)

    # Predict future health
    predictions = predictor.predict_health("synthon_1", horizon_steps=5)
    check("s11_has_predictions", predictions is not None)
    check("s11_prediction_count", len(predictions) == 5)

    # Predictions should show decline
    if predictions:
        check("s11_declining", predictions[-1] < predictions[0],
              f"first={predictions[0]:.3f} last={predictions[-1]:.3f}")

    # Time to threshold
    ttl = predictor.predict_time_to_threshold("synthon_1", threshold=0.3)
    check("s11_ttl_finite", ttl is not None and ttl > 0,
          f"ttl={ttl}")

    # Trend detection
    trend = predictor.detect_trend("synthon_1")
    check("s11_trend_detected", trend is not None)
    check("s11_trend_declining", trend["direction"] == "declining",
          f"direction={trend['direction']}")
    check("s11_negative_slope", trend["slope"] < 0,
          f"slope={trend['slope']:.4f}")

    # Not enough data
    predictor.record("synthon_short", _make_healthy_snapshot())
    check("s11_insufficient_data", predictor.predict_health("synthon_short") is None)

    # Stable synthon
    stable_predictor = DecayPredictor()
    for i in range(5):
        stable_predictor.record("stable", _make_healthy_snapshot())

    stable_trend = stable_predictor.detect_trend("stable")
    check("s11_stable_trend", stable_trend["direction"] == "stable",
          f"direction={stable_trend['direction']}")

    # ─── S12: Recovery dynamics ───────────────────────────────────────

    recovery = RecoveryDynamics()

    # Early stage recovery — should succeed
    early_result = recovery.simulate_recovery(
        "synth_A", DecayStage.EARLY, 0.55,
        [InterventionType.ATP_INJECTION, InterventionType.TRUST_RECALIBRATION],
        total_cost=150.0,
    )
    check("s12_early_recovery", early_result.outcome in (
        RecoveryOutcome.FULL_RECOVERY, RecoveryOutcome.PARTIAL_RECOVERY),
          f"outcome={early_result.outcome.name}")
    check("s12_health_improved", early_result.health_after > early_result.health_before,
          f"before={early_result.health_before:.3f} after={early_result.health_after:.3f}")

    # Terminal stage — recovery unlikely
    terminal_result = recovery.simulate_recovery(
        "synth_B", DecayStage.TERMINAL, 0.15,
        [InterventionType.ATP_INJECTION],
        total_cost=500.0,
    )
    check("s12_terminal_low_improvement",
          terminal_result.health_after - terminal_result.health_before < 0.1,
          f"improvement={terminal_result.health_after - terminal_result.health_before:.3f}")

    # Controlled dissolution
    dissolve_result = recovery.simulate_recovery(
        "synth_C", DecayStage.TERMINAL, 0.1,
        [InterventionType.CONTROLLED_DISSOLUTION],
        total_cost=50.0,
    )
    check("s12_dissolved", dissolve_result.outcome == RecoveryOutcome.DISSOLVED)
    check("s12_dissolved_zero", dissolve_result.health_after == 0.0)

    # Records tracked
    check("s12_records", len(recovery.records) == 3)

    # ─── S13: Cascade prevention ──────────────────────────────────────

    cascade = CascadePreventor()

    # Create a network of synthons
    cascade.register_synthon("S1", 0.2, {"S2", "S3"})  # Decaying
    cascade.register_synthon("S2", 0.4, {"S1", "S4"})  # At risk
    cascade.register_synthon("S3", 0.8, {"S1"})         # Healthy
    cascade.register_synthon("S4", 0.3, {"S2", "S5"})  # At risk
    cascade.register_synthon("S5", 0.9, {"S4"})         # Healthy

    risk = cascade.assess_cascade_risk("S1")
    check("s13_at_risk_found", len(risk.at_risk_synthons) > 0,
          f"at_risk={risk.at_risk_synthons}")
    check("s13_risk_level", risk.risk_level > 0.0,
          f"risk={risk.risk_level:.3f}")
    check("s13_has_preventive", len(risk.preventive_actions) > 0)
    check("s13_damage_estimate", risk.estimated_damage > 0)

    # Isolated healthy synthon — no cascade risk
    cascade.register_synthon("isolated", 0.9, set())
    healthy_risk = cascade.assess_cascade_risk("isolated")
    check("s13_healthy_no_risk", len(healthy_risk.at_risk_synthons) == 0)

    # Firewall
    fw = cascade.firewall("S1")
    check("s13_firewall", fw["count"] == 2,
          f"count={fw['count']}")

    # ─── S14: Precursor audit trail ───────────────────────────────────

    audit = PrecursorAuditTrail()

    signals_1 = [PrecursorSignal(PrecursorType.TRUST_ENTROPY_RISE, 0.5, 0.8, 0.1, 0.7, 0.6)]
    recs_1 = protocol.recommend(signals_1, DecayStage.EARLY)
    audit.record("synth_X", signals_1, DecayStage.EARLY, recs_1)

    signals_2 = [
        PrecursorSignal(PrecursorType.ATP_STARVATION, 0.6, 0.9, 0.2, 15, 30),
        PrecursorSignal(PrecursorType.TRUST_ENTROPY_RISE, 0.6, 0.8, 0.15, 0.8, 0.6),
    ]
    recs_2 = protocol.recommend(signals_2, DecayStage.MODERATE)
    audit.record("synth_X", signals_2, DecayStage.MODERATE, recs_2)

    check("s14_audit_count", len(audit.entries) == 2)
    check("s14_chain_valid", audit.verify_chain()[0])
    check("s14_has_types", "TRUST_ENTROPY_RISE" in audit.entries[0]["signal_types"])

    # ─── S15: Full lifecycle E2E ──────────────────────────────────────

    e2e_predictor = DecayPredictor()
    e2e_detector = PrecursorDetector()
    e2e_protocol = InterventionProtocol()
    e2e_recovery = RecoveryDynamics()
    e2e_cascade = CascadePreventor()
    e2e_audit = PrecursorAuditTrail()

    # Register synthon network
    e2e_cascade.register_synthon("main", 0.8, {"neighbor"})
    e2e_cascade.register_synthon("neighbor", 0.5, {"main"})

    # Phase 1: Healthy
    prev_snap = None
    for i in range(3):
        snap = _make_healthy_snapshot()
        e2e_predictor.record("main", snap)
        signals = e2e_detector.detect(snap, prev_snap)
        stage = e2e_detector.classify_stage(signals)
        check(f"s15_healthy_{i}", stage == DecayStage.NONE)
        prev_snap = snap

    # Phase 2: Gradual decline
    for i in range(5):
        snap = _make_declining_snapshot(step=i)
        e2e_predictor.record("main", snap)
        signals = e2e_detector.detect(snap, prev_snap)
        stage = e2e_detector.classify_stage(signals)

        if signals:
            recs = e2e_protocol.recommend(signals, stage)
            e2e_audit.record("main", signals, stage, recs)

        e2e_cascade.update_health("main", snap.health_composite)
        prev_snap = snap

    # Should have detected some precursors during decline
    check("s15_precursors_detected", len(e2e_audit.entries) > 0,
          f"detections={len(e2e_audit.entries)}")

    # Prediction should show decline
    pred = e2e_predictor.predict_health("main", 3)
    check("s15_prediction_available", pred is not None)

    # Trend should be declining
    trend = e2e_predictor.detect_trend("main")
    check("s15_trend_declining", trend is not None and trend["direction"] == "declining",
          f"direction={trend['direction'] if trend else 'none'}")

    # Cascade risk assessment
    risk = e2e_cascade.assess_cascade_risk("main")
    check("s15_cascade_assessed", risk is not None)

    # Recovery attempt
    final_health = prev_snap.health_composite
    rec_result = e2e_recovery.simulate_recovery(
        "main", DecayStage.MODERATE, final_health,
        [InterventionType.ATP_INJECTION, InterventionType.TRUST_RECALIBRATION],
        300.0,
    )
    check("s15_recovery_attempted", rec_result is not None)
    check("s15_recovery_outcome", rec_result.outcome != RecoveryOutcome.DISSOLVED)

    # Audit chain valid throughout
    check("s15_audit_chain", e2e_audit.verify_chain()[0])

    # ─── S16: Intervention cost scaling ───────────────────────────────

    # Verify exponential cost increase
    stages = [DecayStage.EARLY, DecayStage.MODERATE, DecayStage.ADVANCED, DecayStage.TERMINAL]
    test_signals = [PrecursorSignal(PrecursorType.ATP_STARVATION, 0.5, 0.9, 0.1, 10, 30)]
    costs = []
    for stage in stages:
        recs = e2e_protocol.recommend(test_signals, stage)
        cost = e2e_protocol.estimate_total_cost(recs)
        costs.append(cost)

    # Each stage should cost more
    check("s16_early_lt_moderate", costs[0] < costs[1],
          f"early={costs[0]:.0f} mod={costs[1]:.0f}")
    check("s16_moderate_lt_advanced", costs[1] < costs[2],
          f"mod={costs[1]:.0f} adv={costs[2]:.0f}")
    check("s16_advanced_lt_terminal", costs[2] < costs[3],
          f"adv={costs[2]:.0f} term={costs[3]:.0f}")

    # Terminal costs >> early costs
    check("s16_terminal_expensive", costs[3] > costs[0] * 5,
          f"ratio={costs[3]/costs[0]:.1f}")

    # ─── S17: Precursor urgency ranking ───────────────────────────────

    mixed_signals = [
        PrecursorSignal(PrecursorType.TRUST_ENTROPY_RISE, 0.3, 0.8, 0.0, 0.7, 0.6),
        PrecursorSignal(PrecursorType.ATP_STARVATION, 0.8, 0.9, 0.3, 5, 30),
        PrecursorSignal(PrecursorType.WITNESS_EXODUS, 0.5, 0.75, 0.1, 3, 7),
    ]

    # ATP starvation should be most urgent (highest severity * confidence * trend)
    sorted_by_urgency = sorted(mixed_signals, key=lambda s: s.urgency, reverse=True)
    check("s17_highest_urgency",
          sorted_by_urgency[0].precursor_type == PrecursorType.ATP_STARVATION,
          f"most_urgent={sorted_by_urgency[0].precursor_type.name}")

    # Urgency is always positive
    check("s17_all_positive", all(s.urgency >= 0 for s in mixed_signals))

    # ─── S18: Edge cases ──────────────────────────────────────────────

    # Zero member count
    zero_snap = SynthonSnapshot(member_count=0, atp_total=0)
    check("s18_zero_members", zero_snap.health_composite >= 0)

    # Single member
    single_snap = _make_healthy_snapshot(members=1)
    check("s18_single_member", single_snap.health_composite > 0)

    # Empty cascade network
    empty_cascade = CascadePreventor()
    empty_cascade.register_synthon("alone", 0.5)
    alone_risk = empty_cascade.assess_cascade_risk("alone")
    check("s18_no_neighbors", len(alone_risk.at_risk_synthons) == 0)

    # Nonexistent synthon
    check("s18_nonexistent", predictor.predict_health("nonexistent") is None)
    check("s18_nonexistent_trend", predictor.detect_trend("nonexistent") is None)

    # ─── Print Results ────────────────────────────────────────────────

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)

    print(f"\n{'='*70}")
    print(f"Synthon Decay Precursor Detection")
    print(f"{'='*70}")

    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        det = f" [{detail}]" if detail else ""
        if not ok:
            print(f"  {status}: {name}{det}")

    print(f"\n  Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    print(f"{'='*70}")

    if failed > 0:
        print("\nFAILED TESTS:")
        for name, ok, detail in results:
            if not ok:
                print(f"  FAIL: {name} [{detail}]")

    return passed, failed


if __name__ == "__main__":
    run_tests()
