#!/usr/bin/env python3
"""
Web4 Phase 2b: Integrated Epistemic + Learning Coordinator
===========================================================

Combines:
- Phase 1 epistemic state tracking (Sessions 16-20)
- Phase 2 runtime monitoring (Session 21)
- Coordination learning (Session 22)

Design: Composition over inheritance
- Wraps Web4ProductionCoordinator (composition)
- Adds epistemic state tracking
- Adds coordination pattern learning
- Provides unified telemetry

Created: December 13, 2025
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import deque
import time

from web4_production_coordinator import Web4ProductionCoordinator, CoordinationParameters
from web4_coordination_epistemic_states import CoordinationEpistemicMetrics
from web4_coordination_learning import (
    CoordinationLearner,
    ConsolidatedLearnings,
    PatternType
)


class InterventionLevel(Enum):
    """Intervention levels based on epistemic state."""
    NONE = "none"
    MONITOR = "monitor"          # Just track and log
    ALERT = "alert"               # Notify of concerning state
    REDUCE_LOAD = "reduce_load"   # Lower coordination frequency
    RESET_PARAMS = "reset_params" # Return to safe parameter values
    EMERGENCY_STOP = "emergency_stop"  # Halt coordination


@dataclass
class EpistemicTelemetry:
    """Runtime epistemic state telemetry."""
    timestamp: float
    cycle_number: int
    epistemic_state: str
    epistemic_metrics: CoordinationEpistemicMetrics
    intervention_level: InterventionLevel
    intervention_reason: str
    coordination_decision: bool
    decision_confidence: float
    learned_patterns_used: int = 0
    learning_recommendation: Optional[str] = None


@dataclass
class IntegratedMetrics:
    """Combined metrics from production + epistemic + learning."""
    # Production metrics
    total_cycles: int = 0
    coordinations: int = 0
    coordination_rate: float = 0.0

    # Epistemic metrics
    state_distribution: Dict[str, int] = field(default_factory=dict)
    avg_coherence: float = 0.0
    avg_confidence: float = 0.0
    avg_stability: float = 0.0

    # Learning metrics
    patterns_extracted: int = 0
    success_factors_discovered: int = 0
    network_insights_discovered: int = 0
    learning_accuracy: float = 0.0

    # Intervention metrics
    interventions_triggered: int = 0
    interventions_by_type: Dict[str, int] = field(default_factory=dict)


class Web4IntegratedCoordinator:
    """
    Phase 2b: Integrated epistemic tracking + coordination learning.

    Composition-based design wrapping production coordinator.
    Adds runtime epistemic state tracking and pattern-based learning.
    """

    def __init__(
        self,
        params: Optional[CoordinationParameters] = None,
        enable_epistemic: bool = True,
        enable_learning: bool = True,
        enable_interventions: bool = False,
        intervention_threshold: float = 0.7,
        learning_frequency: int = 100  # Update learnings every N cycles
    ):
        """
        Initialize integrated coordinator.

        Args:
            params: Production coordinator parameters
            enable_epistemic: Enable epistemic state tracking
            enable_learning: Enable coordination pattern learning
            enable_interventions: Enable automatic interventions
            intervention_threshold: Threshold for triggering interventions
            learning_frequency: How often to update learned patterns
        """
        # Core coordinator (composition, not inheritance)
        self.coordinator = Web4ProductionCoordinator(params)

        # Features enabled
        self.enable_epistemic = enable_epistemic
        self.enable_learning = enable_learning
        self.enable_interventions = enable_interventions
        self.intervention_threshold = intervention_threshold
        self.learning_frequency = learning_frequency

        # Epistemic state tracking
        self.epistemic_history: List[Dict] = []
        self.telemetry_history: List[EpistemicTelemetry] = []

        # Learning system
        self.learner = CoordinationLearner() if enable_learning else None
        self.learnings: Optional[ConsolidatedLearnings] = None
        self.last_learning_update: int = 0

        # Metrics
        self.metrics = IntegratedMetrics()
        self.cycle_count: int = 0

    def coordinate_interaction(
        self,
        priority: float,
        trust_score: float,
        network_density: float,
        quality_score: Optional[float] = None,
        context: Optional[Dict] = None
    ) -> Tuple[bool, EpistemicTelemetry]:
        """
        Coordinate interaction with integrated epistemic + learning.

        Args:
            priority: Coordination priority (0-1)
            trust_score: Trust in coordination partner (0-1)
            network_density: Network connectivity (0-1)
            quality_score: Optional expected quality (0-1)
            context: Optional additional context

        Returns:
            (should_coordinate, telemetry)
        """
        self.cycle_count += 1
        context = context or {}

        # 1. Get base coordination decision from production coordinator
        base_result = self.coordinator.coordinate_interaction(
            priority=priority,
            trust_score=trust_score,
            network_density=network_density,
            quality_score=quality_score
        )

        should_coordinate = base_result['coordinated']
        base_quality = base_result['quality']
        # Use quality as confidence proxy
        base_confidence = base_quality

        # 2. Epistemic state estimation (if enabled)
        epistemic_state = "unknown"
        epistemic_metrics = None

        if self.enable_epistemic:
            # Build epistemic metrics from current state
            epistemic_metrics = CoordinationEpistemicMetrics(
                coordination_confidence=base_confidence,
                parameter_stability=self._estimate_parameter_stability(),
                objective_coherence=base_result.get('objective_coherence', 1.0),
                improvement_rate=self._estimate_improvement_rate(),
                adaptation_frustration=self._estimate_adaptation_frustration()
            )

            epistemic_state = epistemic_metrics.primary_state().value

            # Track history for learning
            cycle_data = {
                'cycle_id': self.cycle_count,
                'priority': priority,
                'trust_score': trust_score,
                'network_density': network_density,
                'quality_score': quality_score or 0.5,
                'epistemic_state': epistemic_state,
                'coordination_confidence': epistemic_metrics.coordination_confidence,
                'parameter_stability': epistemic_metrics.parameter_stability,
                'objective_coherence': epistemic_metrics.objective_coherence,
                'network_density': network_density,
                'avg_trust_score': trust_score,
                'diversity_score': context.get('diversity_score', 0.5),
                'coordination_succeeded': should_coordinate,
                'epistemic_metrics': epistemic_metrics,
                'timestamp': time.time()
            }
            self.epistemic_history.append(cycle_data)

        # 3. Learning-based recommendation (if enabled and sufficient history)
        learning_recommendation = None
        learned_confidence = base_confidence
        patterns_used = 0

        if self.enable_learning and self.learnings is not None:
            # Get learning-based recommendation
            interaction = {
                'priority': priority,
                'trust_score': trust_score,
                'network_density': network_density,
                'quality_estimate': quality_score or 0.5
            }

            learning_context = {
                'network_density': network_density,
                'avg_trust_score': trust_score,
                'diversity_score': context.get('diversity_score', 0.5)
            }

            should_coord_learning, learned_confidence, reasoning = self.learner.recommend(
                interaction,
                learning_context,
                self.learnings
            )

            learning_recommendation = reasoning
            patterns_used = len(self.learnings.get_top_patterns(3))

            # Blend base decision with learning (weighted average)
            if learned_confidence > 0.6:  # High confidence in learning
                final_confidence = learned_confidence * 0.7 + base_confidence * 0.3
            else:  # Low confidence in learning, trust base more
                final_confidence = base_confidence * 0.7 + learned_confidence * 0.3

        else:
            final_confidence = base_confidence

        # 4. Determine intervention level (if enabled)
        intervention = InterventionLevel.NONE
        intervention_reason = ""

        if self.enable_interventions and epistemic_metrics is not None:
            intervention, intervention_reason = self._determine_intervention(
                epistemic_state,
                epistemic_metrics
            )

            # Apply intervention
            if intervention != InterventionLevel.NONE:
                should_coordinate, final_confidence = self._apply_intervention(
                    intervention,
                    should_coordinate,
                    final_confidence
                )

        # 5. Create telemetry
        telemetry = EpistemicTelemetry(
            timestamp=time.time(),
            cycle_number=self.cycle_count,
            epistemic_state=epistemic_state,
            epistemic_metrics=epistemic_metrics,
            intervention_level=intervention,
            intervention_reason=intervention_reason,
            coordination_decision=should_coordinate,
            decision_confidence=final_confidence,
            learned_patterns_used=patterns_used,
            learning_recommendation=learning_recommendation
        )

        self.telemetry_history.append(telemetry)

        # 6. Update metrics
        self._update_metrics(telemetry)

        # 7. Periodic learning update (extract new patterns from history)
        if (self.enable_learning and
            self.cycle_count % self.learning_frequency == 0 and
            len(self.epistemic_history) >= 20):

            self._update_learnings()

        return should_coordinate, telemetry

    def _estimate_parameter_stability(self) -> float:
        """Estimate parameter stability from recent coordination consistency."""
        if len(self.epistemic_history) < 5:
            return 0.8  # Assume stable initially

        # Check consistency of recent decisions
        recent = self.epistemic_history[-5:]
        decisions = [c['coordination_succeeded'] for c in recent]
        consistency = sum(1 for i in range(len(decisions)-1)
                         if decisions[i] == decisions[i+1]) / (len(decisions) - 1)

        return consistency

    def _estimate_improvement_rate(self) -> float:
        """Estimate improvement rate from coordination confidence trends."""
        if len(self.epistemic_history) < 10:
            return 0.0

        # Compare recent vs earlier confidence
        earlier = self.epistemic_history[-10:-5]
        recent = self.epistemic_history[-5:]

        earlier_conf = sum(c['coordination_confidence'] for c in earlier) / len(earlier)
        recent_conf = sum(c['coordination_confidence'] for c in recent) / len(recent)

        improvement = recent_conf - earlier_conf
        return max(-0.5, min(0.5, improvement))  # Clamp to [-0.5, 0.5]

    def _estimate_adaptation_frustration(self) -> float:
        """Estimate adaptation frustration from decision instability."""
        if len(self.epistemic_history) < 5:
            return 0.0

        # Count decision changes in recent history
        recent = self.epistemic_history[-10:]
        changes = sum(1 for i in range(len(recent)-1)
                     if recent[i]['coordination_succeeded'] != recent[i+1]['coordination_succeeded'])

        frustration = changes / len(recent)
        return min(1.0, frustration)

    def _determine_intervention(
        self,
        epistemic_state: str,
        metrics: CoordinationEpistemicMetrics
    ) -> Tuple[InterventionLevel, str]:
        """Determine if intervention is needed based on epistemic state."""

        # STRUGGLING state - high adaptation frustration
        if epistemic_state == "struggling":
            if metrics.adaptation_frustration > self.intervention_threshold:
                return (
                    InterventionLevel.REDUCE_LOAD,
                    f"High adaptation frustration: {metrics.adaptation_frustration:.2f}"
                )
            else:
                return (
                    InterventionLevel.ALERT,
                    f"Struggling state detected (frustration: {metrics.adaptation_frustration:.2f})"
                )

        # CONFLICTING state - low objective coherence
        elif epistemic_state == "conflicting":
            return (
                InterventionLevel.ALERT,
                f"Conflicting objectives detected (coherence: {metrics.objective_coherence:.2f})"
            )

        # ADAPTING state with low confidence - monitor closely
        elif epistemic_state == "adapting":
            if metrics.coordination_confidence < 0.4:
                return (
                    InterventionLevel.MONITOR,
                    f"Low confidence during adaptation: {metrics.coordination_confidence:.2f}"
                )

        return (InterventionLevel.NONE, "")

    def _apply_intervention(
        self,
        intervention: InterventionLevel,
        should_coordinate: bool,
        confidence: float
    ) -> Tuple[bool, float]:
        """Apply intervention to coordination decision."""

        if intervention == InterventionLevel.REDUCE_LOAD:
            # Lower coordination rate by being more selective
            if confidence < 0.6:
                should_coordinate = False
                confidence = confidence * 0.5

        elif intervention == InterventionLevel.EMERGENCY_STOP:
            # Stop coordination entirely
            should_coordinate = False
            confidence = 0.0

        # Other interventions just log (ALERT, MONITOR)

        return should_coordinate, confidence

    def _update_metrics(self, telemetry: EpistemicTelemetry):
        """Update integrated metrics from telemetry."""
        self.metrics.total_cycles += 1

        if telemetry.coordination_decision:
            self.metrics.coordinations += 1

        self.metrics.coordination_rate = self.metrics.coordinations / self.metrics.total_cycles

        # Epistemic metrics
        if telemetry.epistemic_state != "unknown":
            state = telemetry.epistemic_state
            self.metrics.state_distribution[state] = self.metrics.state_distribution.get(state, 0) + 1

            if telemetry.epistemic_metrics:
                self.metrics.avg_coherence = (
                    self.metrics.avg_coherence * 0.9 +
                    telemetry.epistemic_metrics.objective_coherence * 0.1
                )
                self.metrics.avg_confidence = (
                    self.metrics.avg_confidence * 0.9 +
                    telemetry.epistemic_metrics.coordination_confidence * 0.1
                )
                self.metrics.avg_stability = (
                    self.metrics.avg_stability * 0.9 +
                    telemetry.epistemic_metrics.parameter_stability * 0.1
                )

        # Learning metrics (updated separately)

        # Intervention metrics
        if telemetry.intervention_level != InterventionLevel.NONE:
            self.metrics.interventions_triggered += 1
            intervention_name = telemetry.intervention_level.value
            self.metrics.interventions_by_type[intervention_name] = (
                self.metrics.interventions_by_type.get(intervention_name, 0) + 1
            )

    def _update_learnings(self):
        """Update learned patterns from accumulated history."""
        if not self.enable_learning or len(self.epistemic_history) < 20:
            return

        print(f"\n[Cycle {self.cycle_count}] Updating learned patterns from {len(self.epistemic_history)} cycles...")

        # Extract patterns using Session 22 learning system
        self.learnings = self.learner.extract_patterns(self.epistemic_history)

        # Update learning metrics
        self.metrics.patterns_extracted = len(self.learnings.patterns)
        self.metrics.success_factors_discovered = len(self.learnings.success_factors)
        self.metrics.network_insights_discovered = len(self.learnings.network_insights)

        # Calculate learning accuracy (how well patterns predict outcomes)
        if len(self.epistemic_history) >= 50:
            recent = self.epistemic_history[-20:]
            correct = 0

            for cycle in recent:
                interaction = {'quality_estimate': cycle['quality_score']}
                context = {
                    'network_density': cycle['network_density'],
                    'avg_trust_score': cycle['avg_trust_score'],
                    'diversity_score': cycle.get('diversity_score', 0.5)
                }

                should_coord, conf, _ = self.learner.recommend(interaction, context, self.learnings)
                if should_coord == cycle['coordination_succeeded']:
                    correct += 1

            self.metrics.learning_accuracy = correct / len(recent)

        print(f"  Patterns: {self.metrics.patterns_extracted}")
        print(f"  Success factors: {self.metrics.success_factors_discovered}")
        print(f"  Network insights: {self.metrics.network_insights_discovered}")
        if self.metrics.learning_accuracy > 0:
            print(f"  Prediction accuracy: {self.metrics.learning_accuracy:.1%}")

        self.last_learning_update = self.cycle_count

    def get_metrics(self) -> IntegratedMetrics:
        """Get current integrated metrics."""
        return self.metrics

    def get_epistemic_summary(self) -> Dict:
        """Get summary of epistemic state distribution."""
        if not self.metrics.state_distribution:
            return {}

        total = sum(self.metrics.state_distribution.values())
        return {
            state: count / total
            for state, count in self.metrics.state_distribution.items()
        }

    def get_learned_patterns_summary(self) -> Dict:
        """Get summary of learned patterns (if learning enabled)."""
        if not self.learnings:
            return {}

        return {
            'patterns': [
                {
                    'type': p.pattern_type.value,
                    'description': p.description,
                    'frequency': p.frequency,
                    'confidence': p.confidence
                }
                for p in self.learnings.get_top_patterns(5)
            ],
            'success_factors': [
                {
                    'name': f.factor_name,
                    'correlation': f.correlation,
                    'confidence': f.confidence
                }
                for f in self.learnings.get_actionable_factors()
            ],
            'quality_trajectory': self.learnings.quality_trajectory,
            'confidence_trajectory': self.learnings.confidence_trajectory
        }


if __name__ == "__main__":
    print("Web4 Phase 2b: Integrated Epistemic + Learning Coordinator")
    print("=" * 80)
    print()
    print("Features:")
    print("- Composition-based design (wraps Web4ProductionCoordinator)")
    print("- Runtime epistemic state tracking (Sessions 16-20)")
    print("- Coordination pattern learning (Session 22)")
    print("- Automatic interventions (optional)")
    print("- Unified telemetry export")
    print()
    print("Usage:")
    print("  coordinator = Web4IntegratedCoordinator(")
    print("      enable_epistemic=True,")
    print("      enable_learning=True,")
    print("      enable_interventions=True")
    print("  )")
    print()
    print("  should_coord, telemetry = coordinator.coordinate_interaction(")
    print("      priority=0.8,")
    print("      trust_score=0.9,")
    print("      network_density=0.7")
    print("  )")
    print()
