#!/usr/bin/env python3
"""
Web4 Session 54: Phase 2d Emotional Coordinator
===============================================

Extends Phase 2c with emotional intelligence for adaptive coordination.

Research Provenance:
- Web4 S22: Coordination learning (DREAM integration)
- Web4 S51: Phase 2c circadian integration
- Web4 S52: Quality-selectivity tradeoffs, emotional mapping
- Web4 S53: Emotional tracking (Phase 1+2)
- Web4 S54: Emotional modulation (Phase 3) - this session

SAGE Emotional Intelligence → Web4 Adaptive Coordination:
1. Frustration → Consolidation trigger (like SAGE REST)
2. Progress → Dynamic threshold adjustment
3. Curiosity → Diversity tolerance modulation
4. Engagement → Priority-based filtering

Evolution:
- Phase 2a: Basic coordinator
- Phase 2b: + Epistemic tracking + Learning
- Phase 2c: + Circadian temporal awareness
- Phase 2d: + Emotional adaptive behavior (this)

Usage:
```python
coordinator = Web4EmotionalCoordinator(
    enable_circadian=True,
    enable_emotional=True,
    enable_learning=True
)

# Coordinator adapts based on emotional state
should_coord, telemetry = coordinator.coordinate_interaction(...)

# Check emotional state
emotions = coordinator.get_emotional_state()
if emotions.frustration > 0.7:
    print("High frustration - consolidation triggered")
```

Created: December 15, 2025
Session: Autonomous Web4 Research Session 54
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from web4_phase2c_circadian_coordinator import Web4CircadianCoordinator
from web4_emotional_tracking import (
    EmotionalCoordinationTracker,
    EmotionalCoordinationMetrics
)
from web4_production_coordinator import CoordinationParameters
from sage.core.circadian_clock import CircadianPhase


@dataclass
class EmotionalTelemetry:
    """Extended telemetry with emotional state"""
    # Base telemetry fields
    timestamp: float
    cycle_number: int
    coordination_decision: bool
    decision_confidence: float

    # Circadian fields (from Phase 2c)
    circadian_phase: Optional[str] = None
    circadian_bias_applied: Optional[float] = None

    # Emotional fields (Phase 2d)
    emotional_state: Optional[EmotionalCoordinationMetrics] = None
    emotional_adjustment: Optional[float] = None
    threshold_adjustment: Optional[float] = None
    consolidation_triggered: bool = False

    # Learning fields
    learned_patterns_used: int = 0
    learning_recommendation: Optional[str] = None


class Web4EmotionalCoordinator(Web4CircadianCoordinator):
    """
    Phase 2d: Emotional adaptive coordinator.

    Extends Phase 2c circadian coordinator with emotional intelligence.
    Uses emotional state to adapt coordination behavior dynamically.

    Emotional Adaptations:
    1. Frustration → Trigger consolidation (like SAGE REST)
    2. Progress → Adjust satisfaction threshold
    3. Curiosity → Modulate diversity tolerance
    4. Engagement → Filter by priority
    """

    def __init__(
        self,
        params: Optional[CoordinationParameters] = None,
        enable_circadian: bool = True,
        enable_emotional: bool = True,
        enable_epistemic: bool = True,
        enable_learning: bool = True,
        enable_interventions: bool = False,
        circadian_period: int = 100,
        consolidate_during_night: bool = True,
        # Emotional parameters
        frustration_consolidation_threshold: float = 0.7,
        progress_threshold_adjustment_range: Tuple[float, float] = (-0.10, +0.10),
        curiosity_diversity_bonus: float = 0.05,
        engagement_priority_threshold: float = 0.7,
        learning_frequency: int = 100
    ):
        """
        Initialize emotional adaptive coordinator.

        Args:
            params: Base coordination parameters
            enable_circadian: Enable circadian temporal awareness
            enable_emotional: Enable emotional adaptive behavior
            enable_epistemic: Enable epistemic tracking
            enable_learning: Enable pattern learning
            enable_interventions: Enable automatic interventions
            circadian_period: Circadian cycle period
            consolidate_during_night: Consolidate during night phases
            frustration_consolidation_threshold: Frustration level that triggers consolidation
            progress_threshold_adjustment_range: Min/max threshold adjustment based on progress
            curiosity_diversity_bonus: Confidence bonus for diverse coordination when curious
            engagement_priority_threshold: Minimum engagement for priority filtering
            learning_frequency: Cycles between learning updates
        """
        super().__init__(
            params=params,
            enable_circadian=enable_circadian,
            enable_epistemic=enable_epistemic,
            enable_learning=enable_learning,
            enable_interventions=enable_interventions,
            circadian_period=circadian_period,
            consolidate_during_night=consolidate_during_night,
            learning_frequency=learning_frequency
        )

        # Emotional features
        self.enable_emotional = enable_emotional
        self.emotional_tracker = EmotionalCoordinationTracker() if enable_emotional else None

        # Emotional parameters
        self.frustration_consolidation_threshold = frustration_consolidation_threshold
        self.progress_threshold_range = progress_threshold_adjustment_range
        self.curiosity_diversity_bonus = curiosity_diversity_bonus
        self.engagement_priority_threshold = engagement_priority_threshold

        # Emotional state
        self.current_emotions: Optional[EmotionalCoordinationMetrics] = None
        self.consolidation_count: int = 0
        self.last_consolidation_cycle: int = 0

    def coordinate_interaction(
        self,
        priority: float,
        trust_score: float,
        network_density: float,
        quality_score: Optional[float] = None,
        context: Optional[Dict] = None
    ) -> Tuple[bool, EmotionalTelemetry]:
        """
        Coordinate with emotional adaptive behavior.

        Process:
        1. Get base coordination decision (from Phase 2c)
        2. Update emotional state
        3. Apply emotional modulation
        4. Check for consolidation trigger
        5. Return adapted decision + emotional telemetry

        Args:
            priority: Coordination priority [0-1]
            trust_score: Trust in partner [0-1]
            network_density: Network connectivity [0-1]
            quality_score: Optional expected quality [0-1]
            context: Optional additional context

        Returns:
            (should_coordinate, emotional_telemetry)
        """
        context = context or {}

        # 1. Get base coordination decision from Phase 2c
        should_coord_base, base_telemetry = super().coordinate_interaction(
            priority, trust_score, network_density, quality_score, context
        )

        # 2. Update emotional state
        emotional_adjustment = 0.0
        threshold_adjustment = 0.0
        consolidation_triggered = False

        if self.enable_emotional and self.emotional_tracker:
            # Update emotional tracker
            emotional_data = {
                'network_density': network_density,
                'diversity_score': context.get('diversity_score', 0.5),
                'quality': quality_score if quality_score else 0.5,
                'priority': priority,
                'timestamp': time.time()
            }

            self.current_emotions = self.emotional_tracker.update(emotional_data)

            # 3. Apply emotional modulation
            emotional_adjustment, threshold_adjustment = self._apply_emotional_modulation(
                priority,
                trust_score,
                network_density,
                context,
                base_telemetry.decision_confidence
            )

            # 4. Check consolidation trigger
            consolidation_triggered = self._check_consolidation_trigger()

        # Apply adjustments to decision
        final_confidence = base_telemetry.decision_confidence + emotional_adjustment
        final_confidence = max(0.0, min(1.0, final_confidence))

        # Adjust threshold dynamically
        adjusted_threshold = self.coordinator.params.satisfaction_threshold + threshold_adjustment

        # Final decision with emotional adaptation
        should_coordinate = final_confidence >= adjusted_threshold

        # Create emotional telemetry
        telemetry = EmotionalTelemetry(
            timestamp=base_telemetry.timestamp,
            cycle_number=base_telemetry.cycle_number,
            coordination_decision=should_coordinate,
            decision_confidence=final_confidence,
            circadian_phase=base_telemetry.circadian_phase,
            circadian_bias_applied=base_telemetry.circadian_bias_applied,
            emotional_state=self.current_emotions,
            emotional_adjustment=emotional_adjustment,
            threshold_adjustment=threshold_adjustment,
            consolidation_triggered=consolidation_triggered,
            learned_patterns_used=base_telemetry.learned_patterns_used,
            learning_recommendation=base_telemetry.learning_recommendation
        )

        return should_coordinate, telemetry

    def _apply_emotional_modulation(
        self,
        priority: float,
        trust_score: float,
        network_density: float,
        context: Dict,
        base_confidence: float
    ) -> Tuple[float, float]:
        """
        Apply emotional state modulation to coordination decision.

        Returns:
            (confidence_adjustment, threshold_adjustment)
        """
        if not self.current_emotions:
            return 0.0, 0.0

        confidence_adjustment = 0.0
        threshold_adjustment = 0.0

        # 1. Curiosity → Diversity tolerance
        if self.current_emotions.curiosity > 0.7:
            # High curiosity: Bonus for diverse coordination
            diversity = context.get('diversity_score', 0.5)
            if diversity > 0.6:
                confidence_adjustment += self.curiosity_diversity_bonus

        elif self.current_emotions.curiosity < 0.3:
            # Low curiosity: Bonus for familiar patterns
            diversity = context.get('diversity_score', 0.5)
            if diversity < 0.4:
                confidence_adjustment += self.curiosity_diversity_bonus

        # 2. Frustration → Conservative behavior
        if self.current_emotions.frustration > 0.6:
            # High frustration: Be more selective (reduce confidence)
            frustration_penalty = (self.current_emotions.frustration - 0.6) * 0.25
            confidence_adjustment -= frustration_penalty

        # 3. Progress → Dynamic threshold adjustment
        # High progress → lower threshold (coordinate more, learning is working)
        # Low progress → higher threshold (be more selective, need adjustment)
        progress = self.current_emotions.progress

        if progress > 0.7:
            # High progress: Lower threshold to explore more
            threshold_adjustment = self.progress_threshold_range[0] * (progress - 0.5) / 0.5
        elif progress < 0.3:
            # Low progress: Raise threshold to be more selective
            threshold_adjustment = self.progress_threshold_range[1] * (0.5 - progress) / 0.5

        # 4. Engagement → Priority filtering
        if self.current_emotions.engagement > self.engagement_priority_threshold:
            # High engagement: Only accept high-priority coordination
            if priority < 0.7:
                confidence_adjustment -= 0.10  # Penalty for low priority

        elif self.current_emotions.engagement < (1.0 - self.engagement_priority_threshold):
            # Low engagement: Accept broader priorities
            if priority > 0.3:
                confidence_adjustment += 0.05  # Small bonus

        return confidence_adjustment, threshold_adjustment

    def _check_consolidation_trigger(self) -> bool:
        """
        Check if emotional state triggers consolidation.

        Like SAGE REST state triggered by high frustration.

        Returns:
            True if consolidation should be triggered
        """
        if not self.current_emotions:
            return False

        # High frustration triggers consolidation
        if self.current_emotions.frustration > self.frustration_consolidation_threshold:
            # Don't consolidate too frequently
            cycles_since_last = self.cycle_count - self.last_consolidation_cycle

            if cycles_since_last >= 50:  # At least 50 cycles between consolidations
                self._trigger_consolidation()
                return True

        return False

    def _trigger_consolidation(self):
        """
        Trigger learning consolidation due to emotional state.

        Similar to SAGE REST state consolidation.
        """
        if self.enable_learning and len(self.epistemic_history) >= 20:
            # Consolidate learnings
            self._update_learnings()

            # Update tracking
            self.consolidation_count += 1
            self.last_consolidation_cycle = self.cycle_count

    def get_emotional_state(self) -> Optional[EmotionalCoordinationMetrics]:
        """Get current emotional state"""
        return self.current_emotions

    def get_emotional_summary(self) -> Dict:
        """
        Get detailed emotional summary with interpretations.

        Returns:
            Dict with emotional state and interpretations
        """
        if not self.emotional_tracker:
            return {'emotional_tracking_disabled': True}

        return self.emotional_tracker.get_emotional_summary()

    def get_adaptation_metrics(self) -> Dict:
        """
        Get metrics about emotional adaptation.

        Returns:
            Dict with adaptation statistics
        """
        return {
            'consolidations_triggered': self.consolidation_count,
            'last_consolidation_cycle': self.last_consolidation_cycle,
            'current_emotions': self.current_emotions.to_dict() if self.current_emotions else None,
            'emotional_tracking_enabled': self.enable_emotional
        }


# Backward compatibility
__all__ = [
    'Web4EmotionalCoordinator',
    'EmotionalTelemetry'
]
