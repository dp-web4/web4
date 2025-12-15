#!/usr/bin/env python3
"""
Web4 Phase 2c: Circadian-Aware Integrated Coordinator
=====================================================

Extends Phase 2b with temporal awareness from SAGE (Thor Session 49).

Adds:
- Circadian clock for temporal context (5th dimension)
- Phase-dependent intervention strategies
- Temporal pattern learning (success varies by time)
- Scheduled consolidation (learning during NIGHT phases)
- Resource optimization by circadian phase

Created: December 14, 2025
Session: Autonomous Web4 Research Session 51
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import deque
import time
import sys

sys.path.insert(0, '/home/dp/ai-workspace/HRM')

from web4_phase2b_integrated_coordinator import (
    Web4IntegratedCoordinator,
    InterventionLevel,
    EpistemicTelemetry,
    IntegratedMetrics,
    CoordinationParameters
)

from sage.core.circadian_clock import CircadianClock, CircadianPhase, CircadianContext


@dataclass
class CircadianTelemetry(EpistemicTelemetry):
    """Extended telemetry with circadian context."""
    circadian_phase: str = ""
    phase_progression: float = 0.0
    day_strength: float = 0.0
    night_strength: float = 0.0
    circadian_bias_applied: float = 0.0


@dataclass
class CircadianMetrics(IntegratedMetrics):
    """Extended metrics with circadian tracking."""
    # Phase distribution
    cycles_by_phase: Dict[str, int] = field(default_factory=dict)
    coordinations_by_phase: Dict[str, int] = field(default_factory=dict)
    success_by_phase: Dict[str, int] = field(default_factory=dict)
    avg_quality_by_phase: Dict[str, List[float]] = field(default_factory=dict)

    # Consolidation tracking
    consolidations_scheduled: int = 0
    consolidations_executed: int = 0
    patterns_learned_during_night: int = 0


class Web4CircadianCoordinator(Web4IntegratedCoordinator):
    """
    Phase 2c: Circadian-aware coordination with temporal optimization.

    Extends Phase 2b with:
    - Temporal awareness (circadian clock)
    - Phase-dependent decision-making
    - Scheduled consolidation
    - Resource optimization by time
    """

    def __init__(
        self,
        params: Optional[CoordinationParameters] = None,
        enable_epistemic: bool = True,
        enable_learning: bool = True,
        enable_interventions: bool = False,
        enable_circadian: bool = True,
        intervention_threshold: float = 0.7,
        learning_frequency: int = 100,
        circadian_period: int = 100,  # Cycles per "day"
        consolidate_during_night: bool = True
    ):
        """
        Initialize circadian-aware coordinator.

        Args:
            enable_circadian: Enable circadian temporal awareness
            circadian_period: Length of circadian cycle in coordination cycles
            consolidate_during_night: Run consolidation during NIGHT phases
        """
        super().__init__(
            params=params,
            enable_epistemic=enable_epistemic,
            enable_learning=enable_learning,
            enable_interventions=enable_interventions,
            intervention_threshold=intervention_threshold,
            learning_frequency=learning_frequency
        )

        # Circadian clock
        self.enable_circadian = enable_circadian
        self.circadian_clock = CircadianClock(period_cycles=circadian_period) if enable_circadian else None
        self.consolidate_during_night = consolidate_during_night

        # Circadian metrics
        self.circadian_metrics = CircadianMetrics()

        # Raw quality tracking (separate from metrics to avoid list->float conversion)
        self._raw_quality_by_phase: Dict[str, List[float]] = {}

        # Initialize phase tracking
        if enable_circadian:
            for phase in CircadianPhase:
                self.circadian_metrics.cycles_by_phase[phase.value] = 0
                self.circadian_metrics.coordinations_by_phase[phase.value] = 0
                self.circadian_metrics.success_by_phase[phase.value] = 0
                self.circadian_metrics.avg_quality_by_phase[phase.value] = []
                self._raw_quality_by_phase[phase.value] = []

    def _get_circadian_context(self) -> Optional[CircadianContext]:
        """Get current circadian context."""
        if not self.enable_circadian or not self.circadian_clock:
            return None

        return self.circadian_clock.get_context()

    def _apply_circadian_bias(
        self,
        base_decision: bool,
        base_confidence: float,
        circadian_context: Optional[CircadianContext]
    ) -> Tuple[bool, float, float]:
        """
        Apply circadian bias to coordination decision.

        Returns:
            (modified_decision, modified_confidence, bias_applied)
        """
        if not circadian_context:
            return base_decision, base_confidence, 0.0

        # Phase-dependent biasing
        if circadian_context.phase == CircadianPhase.DAY:
            # Encourage coordination during day
            bias = +0.10 * circadian_context.day_strength
        elif circadian_context.phase == CircadianPhase.DAWN:
            # Moderate encouragement during dawn
            bias = +0.05
        elif circadian_context.phase == CircadianPhase.DUSK:
            # Slight encouragement during dusk
            bias = +0.03
        elif circadian_context.phase == CircadianPhase.NIGHT:
            # Discourage coordination during night (consolidation time)
            bias = -0.08 * circadian_context.night_strength
        else:  # DEEP_NIGHT
            # Strong discouragement during deep night
            bias = -0.12 * circadian_context.night_strength

        # Apply bias to confidence
        modified_confidence = max(0.0, min(1.0, base_confidence + bias))

        # Decision may flip if bias crosses threshold (use satisfaction threshold)
        threshold = self.coordinator.params.satisfaction_threshold
        modified_decision = modified_confidence >= threshold

        return modified_decision, modified_confidence, bias

    def _should_consolidate(self, circadian_context: Optional[CircadianContext]) -> bool:
        """Check if we should consolidate learnings (during NIGHT phases)."""
        if not self.consolidate_during_night or not circadian_context:
            return False

        # Consolidate during NIGHT and DEEP_NIGHT
        return circadian_context.phase in [CircadianPhase.NIGHT, CircadianPhase.DEEP_NIGHT]

    def _get_phase_intervention_level(
        self,
        base_intervention: InterventionLevel,
        circadian_context: Optional[CircadianContext]
    ) -> InterventionLevel:
        """Adjust intervention level based on circadian phase."""
        if not circadian_context:
            return base_intervention

        # During NIGHT phases, be more conservative (reduce activity)
        if circadian_context.phase in [CircadianPhase.NIGHT, CircadianPhase.DEEP_NIGHT]:
            if base_intervention == InterventionLevel.MONITOR:
                return InterventionLevel.REDUCE_LOAD

        # During DAY phase, be more tolerant (peak activity time)
        if circadian_context.phase == CircadianPhase.DAY:
            if base_intervention == InterventionLevel.REDUCE_LOAD:
                return InterventionLevel.MONITOR

        return base_intervention

    def coordinate_interaction(
        self,
        priority: float,
        trust_score: float,
        network_density: float,
        quality_score: Optional[float] = None,
        context: Optional[Dict] = None
    ) -> Tuple[bool, CircadianTelemetry]:
        """
        Coordinate interaction with circadian temporal awareness.

        Extends Phase 2b with:
        - Circadian phase tracking
        - Phase-dependent biasing
        - Scheduled consolidation
        """
        # Get circadian context
        circadian_context = self._get_circadian_context()

        # Advance clock
        if self.circadian_clock:
            circadian_context = self.circadian_clock.tick()

        # Call parent (Phase 2b) coordination
        base_decision, base_telemetry = super().coordinate_interaction(
            priority=priority,
            trust_score=trust_score,
            network_density=network_density,
            quality_score=quality_score,
            context=context
        )

        # Apply circadian bias
        modified_decision, modified_confidence, bias = self._apply_circadian_bias(
            base_decision,
            base_telemetry.decision_confidence,
            circadian_context
        )

        # Adjust intervention level based on phase
        modified_intervention = self._get_phase_intervention_level(
            base_telemetry.intervention_level,
            circadian_context
        )

        # Check for scheduled consolidation
        if self._should_consolidate(circadian_context):
            if self.cycle_count % 20 == 0:  # Consolidate every 20 cycles during night
                self._execute_consolidation()

        # Create circadian telemetry
        telemetry = CircadianTelemetry(
            timestamp=base_telemetry.timestamp,
            cycle_number=base_telemetry.cycle_number,
            epistemic_state=base_telemetry.epistemic_state,
            epistemic_metrics=base_telemetry.epistemic_metrics,
            intervention_level=modified_intervention,
            intervention_reason=base_telemetry.intervention_reason,
            coordination_decision=modified_decision,
            decision_confidence=modified_confidence,
            learned_patterns_used=base_telemetry.learned_patterns_used,
            learning_recommendation=base_telemetry.learning_recommendation,
            circadian_phase=circadian_context.phase.value if circadian_context else "",
            phase_progression=circadian_context.phase_progression if circadian_context else 0.0,
            day_strength=circadian_context.day_strength if circadian_context else 0.0,
            night_strength=circadian_context.night_strength if circadian_context else 0.0,
            circadian_bias_applied=bias
        )

        # Track circadian metrics
        if circadian_context:
            phase = circadian_context.phase.value
            self.circadian_metrics.cycles_by_phase[phase] += 1

            if modified_decision:
                self.circadian_metrics.coordinations_by_phase[phase] += 1

            if quality_score:
                self._raw_quality_by_phase[phase].append(quality_score)

                if quality_score > 0.65:  # Success threshold
                    self.circadian_metrics.success_by_phase[phase] += 1

        # Update cycle count
        self.cycle_count += 1

        return modified_decision, telemetry

    def _execute_consolidation(self):
        """Execute pattern consolidation during NIGHT phase."""
        if not self.enable_learning or not self.learner or len(self.epistemic_history) < 10:
            return

        # Update learnings from recent history
        self.learnings = self.learner.extract_patterns(self.epistemic_history)
        self.last_learning_update = self.cycle_count

        # Track consolidation
        self.circadian_metrics.consolidations_executed += 1
        self.circadian_metrics.patterns_learned_during_night = len(self.learnings.patterns)

    def get_circadian_metrics(self) -> CircadianMetrics:
        """Get comprehensive circadian metrics."""
        # Copy base metrics
        self.circadian_metrics.total_cycles = self.metrics.total_cycles
        self.circadian_metrics.coordinations = self.metrics.coordinations
        self.circadian_metrics.coordination_rate = self.metrics.coordination_rate
        self.circadian_metrics.state_distribution = self.metrics.state_distribution
        self.circadian_metrics.avg_coherence = self.metrics.avg_coherence
        self.circadian_metrics.avg_confidence = self.metrics.avg_confidence
        self.circadian_metrics.avg_stability = self.metrics.avg_stability
        self.circadian_metrics.patterns_extracted = self.metrics.patterns_extracted
        self.circadian_metrics.success_factors_discovered = self.metrics.success_factors_discovered
        self.circadian_metrics.network_insights_discovered = self.metrics.network_insights_discovered
        self.circadian_metrics.learning_accuracy = self.metrics.learning_accuracy
        self.circadian_metrics.interventions_triggered = self.metrics.interventions_triggered
        self.circadian_metrics.interventions_by_type = self.metrics.interventions_by_type

        # Calculate averages for quality by phase (from raw tracking)
        for phase, qualities in self._raw_quality_by_phase.items():
            if qualities:
                avg = sum(qualities) / len(qualities)
                self.circadian_metrics.avg_quality_by_phase[phase] = avg
            else:
                self.circadian_metrics.avg_quality_by_phase[phase] = 0.0

        return self.circadian_metrics

    def get_phase_summary(self) -> Dict:
        """Get summary statistics by circadian phase."""
        metrics = self.get_circadian_metrics()

        summary = {}
        for phase in CircadianPhase:
            phase_name = phase.value
            cycles = metrics.cycles_by_phase.get(phase_name, 0)
            coords = metrics.coordinations_by_phase.get(phase_name, 0)
            successes = metrics.success_by_phase.get(phase_name, 0)

            avg_quality = metrics.avg_quality_by_phase.get(phase_name, 0.0)
            if isinstance(avg_quality, list) and avg_quality:
                avg_quality = sum(avg_quality) / len(avg_quality)

            summary[phase_name] = {
                'cycles': cycles,
                'coordinations': coords,
                'coordination_rate': coords / cycles if cycles > 0 else 0.0,
                'successes': successes,
                'success_rate': successes / coords if coords > 0 else 0.0,
                'avg_quality': avg_quality
            }

        return summary


if __name__ == "__main__":
    print("Web4 Phase 2c: Circadian-Aware Coordinator")
    print("=" * 80)
    print()

    print("Features:")
    print("  • Temporal awareness via circadian clock (Thor Session 49)")
    print("  • Phase-dependent coordination biasing")
    print("  • Scheduled consolidation during NIGHT phases")
    print("  • Resource optimization by circadian phase")
    print("  • Temporal pattern learning")
    print()

    print("Circadian Phases:")
    print("  DAWN       (0-10%):  Transition to day, moderate activity")
    print("  DAY        (10-50%): Peak coordination activity")
    print("  DUSK       (50-60%): Transition to night, winding down")
    print("  NIGHT      (60-90%): Low activity, consolidation")
    print("  DEEP_NIGHT (90-100%): Minimal activity, deep consolidation")
    print()

    print("Usage:")
    print()
    print("  coordinator = Web4CircadianCoordinator(")
    print("      enable_circadian=True,")
    print("      circadian_period=100,  # 100 cycles = 1 'day'")
    print("      consolidate_during_night=True")
    print("  )")
    print()
    print("  should_coord, telemetry = coordinator.coordinate_interaction(...)")
    print("  phase_summary = coordinator.get_phase_summary()")
    print()
