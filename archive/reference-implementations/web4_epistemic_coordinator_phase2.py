#!/usr/bin/env python3
"""
Web4 Phase 2: Epistemic Coordination with Runtime Tracking
===========================================================

Extends Web4 Production Coordinator with runtime epistemic state monitoring
and prediction validation, integrating Sessions 16-20 validation framework.

Research Provenance:
- Web4 S16: Epistemic coordination states (Phase 1)
- Web4 S17: Observational framework (23 predictions)
- Web4 S18: Initial validation (3/6, 50%)
- Web4 S19: Diagnosis and improved logic (90% accuracy)
- Web4 S20: Dual-context validation (4/6, 67%)
- Web4 S21: Phase 2 runtime integration (this session)

Following SAGE S40 metabolic states pattern:
- Just as SAGE tracks metabolic states (wake, focus, rest, dream, crisis)
- Web4 tracks epistemic states (optimal, stable, converging, adapting, struggling, conflicting)
- Both enable runtime regulation and self-awareness

Key Features:
1. Backward compatible: Epistemic tracking opt-in
2. Runtime state monitoring: Track epistemic state each coordination cycle
3. Prediction validation: Continuous validation of M1-M6 in production
4. Intervention triggers: Alert/adjust when entering struggling/conflicting states
5. Production telemetry: Export epistemic metrics for monitoring

Design Pattern (following Thor S26 opt-in approach):
```python
# Without epistemic tracking (legacy)
coordinator = Web4ProductionCoordinator()

# With epistemic tracking (Phase 2)
coordinator = Web4EpistemicCoordinator(enable_epistemic=True)

# With intervention (advanced)
coordinator = Web4EpistemicCoordinator(
    enable_epistemic=True,
    enable_interventions=True,
    intervention_threshold=0.7  # Alert if frustration > 0.7
)
```

Created: December 12, 2025
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from collections import deque
from enum import Enum

# Import Phase 1 components
from web4_coordination_epistemic_states import (
    CoordinationEpistemicState,
    CoordinationEpistemicMetrics,
    estimate_coordination_epistemic_state,
    CoordinationEpistemicTracker
)

from web4_production_coordinator import (
    Web4ProductionCoordinator,
    CoordinatorMode,
    MultiObjectiveFitness,
    CoordinationParameters
)


class EpistemicIntervention(Enum):
    """Types of epistemic interventions"""
    NONE = "none"  # No intervention needed
    ALERT = "alert"  # Log warning, continue
    REDUCE_LOAD = "reduce_load"  # Lower ATP allocation to reduce pressure
    RESET_PARAMS = "reset_params"  # Return to safe parameter values
    EMERGENCY_STOP = "emergency_stop"  # Halt coordination, require manual review


@dataclass
class EpistemicTelemetry:
    """
    Telemetry data for epistemic state monitoring.

    Exported for production monitoring dashboards.
    """
    timestamp: float
    cycle_id: int
    epistemic_state: CoordinationEpistemicState
    epistemic_metrics: CoordinationEpistemicMetrics
    fitness: MultiObjectiveFitness
    intervention: EpistemicIntervention

    # Running statistics
    state_distribution: Dict[str, int] = field(default_factory=dict)
    confidence_history: List[float] = field(default_factory=list)
    stability_history: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for export"""
        return {
            'timestamp': self.timestamp,
            'cycle_id': self.cycle_id,
            'epistemic_state': self.epistemic_state.value,
            'confidence': self.epistemic_metrics.coordination_confidence,
            'stability': self.epistemic_metrics.parameter_stability,
            'coherence': self.epistemic_metrics.objective_coherence,
            'improvement_rate': self.epistemic_metrics.improvement_rate,
            'frustration': self.epistemic_metrics.adaptation_frustration,
            'coverage': self.fitness.coverage,
            'quality': self.fitness.quality,
            'efficiency': self.fitness.efficiency,
            'intervention': self.intervention.value,
            'state_distribution': self.state_distribution
        }


class Web4EpistemicCoordinator(Web4ProductionCoordinator):
    """
    Web4 coordinator with integrated epistemic state tracking.

    Extends production coordinator with Phase 1 epistemic framework,
    enabling runtime monitoring and prediction validation.

    Following opt-in design pattern: Epistemic features disabled by default.
    """

    def __init__(
        self,
        params: Optional[CoordinationParameters] = None,
        # Phase 2 epistemic parameters (new)
        enable_epistemic: bool = False,
        enable_interventions: bool = False,
        intervention_threshold: float = 0.7,  # Frustration threshold for intervention
        telemetry_window: int = 100,  # Cycles to keep in memory
    ):
        """
        Initialize epistemic coordinator.

        Args:
            params: Coordination parameters (uses defaults if None)
            enable_epistemic: Enable epistemic state tracking
            enable_interventions: Enable automatic interventions
            intervention_threshold: Frustration level that triggers intervention
            telemetry_window: Number of cycles to track for statistics
        """
        # Use default params if not provided
        if params is None:
            params = CoordinationParameters()

        # Initialize parent coordinator
        super().__init__(params)

        # Phase 2 components
        self.enable_epistemic = enable_epistemic
        self.enable_interventions = enable_interventions
        self.intervention_threshold = intervention_threshold
        self.telemetry_window = telemetry_window

        if self.enable_epistemic:
            self.epistemic_tracker = CoordinationEpistemicTracker()
            self.epistemic_history: List[EpistemicTelemetry] = []
            self.cycle_counter = 0

            # Running state distribution
            self.state_counts = {state: 0 for state in CoordinationEpistemicState}

    def coordinate(
        self,
        interaction: Dict,
        context: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Coordinate interaction with epistemic tracking.

        Returns:
            (should_coordinate, telemetry): Decision and epistemic telemetry
        """
        # Base coordination decision (from parent class)
        should_coordinate, base_telemetry = super().coordinate(interaction, context)

        # If epistemic tracking disabled, return base result
        if not self.enable_epistemic:
            return should_coordinate, base_telemetry

        # Phase 2: Estimate epistemic state
        cycle_metrics = {
            'coverage': base_telemetry.get('coverage', 0.0),
            'quality': base_telemetry.get('quality', 0.0),
            'efficiency': base_telemetry.get('efficiency', 0.0),
            'parameter_drift': base_telemetry.get('parameter_drift', 0.0),
            'adaptation_rate': base_telemetry.get('adaptation_rate', 0.0),
            'satisfaction_history': base_telemetry.get('satisfaction_history', [])
        }

        epistemic_metrics = estimate_coordination_epistemic_state(
            cycle_metrics,
            self.epistemic_tracker.history
        )

        epistemic_state = epistemic_metrics.primary_state()

        # Track state
        self.epistemic_tracker.track(epistemic_metrics)
        self.state_counts[epistemic_state] += 1
        self.cycle_counter += 1

        # Create fitness object
        fitness = MultiObjectiveFitness(
            coverage=cycle_metrics['coverage'],
            quality=cycle_metrics['quality'],
            efficiency=cycle_metrics['efficiency']
        )

        # Determine intervention
        intervention = self._determine_intervention(epistemic_state, epistemic_metrics)

        # Create telemetry
        telemetry = EpistemicTelemetry(
            timestamp=time.time(),
            cycle_id=self.cycle_counter,
            epistemic_state=epistemic_state,
            epistemic_metrics=epistemic_metrics,
            fitness=fitness,
            intervention=intervention,
            state_distribution={k.value: v for k, v in self.state_counts.items()},
            confidence_history=[m.coordination_confidence
                              for m in self.epistemic_tracker.history[-10:]],
            stability_history=[m.parameter_stability
                             for m in self.epistemic_tracker.history[-10:]]
        )

        # Store telemetry (with window limit)
        self.epistemic_history.append(telemetry)
        if len(self.epistemic_history) > self.telemetry_window:
            self.epistemic_history.pop(0)

        # Execute intervention if enabled
        if self.enable_interventions and intervention != EpistemicIntervention.NONE:
            should_coordinate = self._execute_intervention(
                intervention,
                should_coordinate,
                epistemic_state,
                epistemic_metrics
            )

        # Merge epistemic data into base telemetry
        enhanced_telemetry = {
            **base_telemetry,
            'epistemic': telemetry.to_dict()
        }

        return should_coordinate, enhanced_telemetry

    def _determine_intervention(
        self,
        state: CoordinationEpistemicState,
        metrics: CoordinationEpistemicMetrics
    ) -> EpistemicIntervention:
        """
        Determine if intervention is needed based on epistemic state.

        Following SAGE S40 metabolic intervention pattern:
        - Crisis state → Emergency intervention
        - Struggling state → Reduce load
        - Conflicting state → Alert for review
        """
        # High frustration → struggling state
        if metrics.adaptation_frustration > self.intervention_threshold:
            if state == CoordinationEpistemicState.STRUGGLING:
                # Persistent struggling → reduce load
                return EpistemicIntervention.REDUCE_LOAD
            else:
                # Temporary spike → alert
                return EpistemicIntervention.ALERT

        # Low coherence → conflicting objectives
        if metrics.objective_coherence < 0.3:
            if state == CoordinationEpistemicState.CONFLICTING:
                # Conflicting objectives → manual review needed
                return EpistemicIntervention.ALERT

        # Everything nominal
        return EpistemicIntervention.NONE

    def _execute_intervention(
        self,
        intervention: EpistemicIntervention,
        should_coordinate: bool,
        state: CoordinationEpistemicState,
        metrics: CoordinationEpistemicMetrics
    ) -> bool:
        """
        Execute epistemic intervention.

        Args:
            intervention: Type of intervention
            should_coordinate: Current coordination decision
            state: Current epistemic state
            metrics: Current epistemic metrics

        Returns:
            Modified coordination decision
        """
        if intervention == EpistemicIntervention.ALERT:
            print(f"⚠️  Epistemic Alert: {state.value}")
            print(f"   Frustration: {metrics.adaptation_frustration:.2f}")
            print(f"   Coherence: {metrics.objective_coherence:.2f}")
            # Don't modify decision, just alert
            return should_coordinate

        elif intervention == EpistemicIntervention.REDUCE_LOAD:
            print(f"🔻 Reducing coordination load (struggling state)")
            print(f"   Frustration: {metrics.adaptation_frustration:.2f}")
            # More conservative: Only coordinate if very high priority
            # (Implementation would check interaction priority)
            return should_coordinate and metrics.coordination_confidence > 0.8

        elif intervention == EpistemicIntervention.RESET_PARAMS:
            print(f"🔄 Resetting to safe parameters (conflicting objectives)")
            # Would reset to known-good parameter values
            # (Implementation would call reset method)
            return should_coordinate

        elif intervention == EpistemicIntervention.EMERGENCY_STOP:
            print(f"🛑 Emergency stop (critical epistemic state)")
            # Halt coordination entirely
            return False

        return should_coordinate

    def get_epistemic_summary(self) -> Dict:
        """
        Get epistemic state summary for monitoring.

        Returns:
            Dictionary with current state, distribution, and trends
        """
        if not self.enable_epistemic or not self.epistemic_history:
            return {'epistemic_enabled': False}

        latest = self.epistemic_history[-1]

        # Calculate state distribution percentages
        total_cycles = sum(self.state_counts.values())
        state_distribution = {
            state.value: (count / total_cycles * 100 if total_cycles > 0 else 0)
            for state, count in self.state_counts.items()
        }

        # Recent confidence/stability trends
        recent_confidence = [t.epistemic_metrics.coordination_confidence
                           for t in self.epistemic_history[-20:]]
        recent_stability = [t.epistemic_metrics.parameter_stability
                          for t in self.epistemic_history[-20:]]

        return {
            'epistemic_enabled': True,
            'current_state': latest.epistemic_state.value,
            'current_metrics': {
                'confidence': latest.epistemic_metrics.coordination_confidence,
                'stability': latest.epistemic_metrics.parameter_stability,
                'coherence': latest.epistemic_metrics.objective_coherence,
                'frustration': latest.epistemic_metrics.adaptation_frustration,
                'improvement_rate': latest.epistemic_metrics.improvement_rate
            },
            'state_distribution': state_distribution,
            'total_cycles': total_cycles,
            'trends': {
                'confidence_mean': statistics.mean(recent_confidence) if recent_confidence else 0,
                'confidence_stdev': statistics.stdev(recent_confidence) if len(recent_confidence) > 1 else 0,
                'stability_mean': statistics.mean(recent_stability) if recent_stability else 0,
                'stability_stdev': statistics.stdev(recent_stability) if len(recent_stability) > 1 else 0
            },
            'interventions': {
                'last_intervention': latest.intervention.value,
                'intervention_count': sum(1 for t in self.epistemic_history
                                        if t.intervention != EpistemicIntervention.NONE)
            }
        }

    def validate_predictions(self) -> Dict:
        """
        Validate M1-M6 predictions on production data.

        Returns:
            Validation results for each prediction
        """
        if not self.enable_epistemic or len(self.epistemic_history) < 50:
            return {'error': 'Insufficient data for validation (need 50+ cycles)'}

        # Prepare data for framework
        coordination_history = [
            {
                'cycle_id': str(t.cycle_id),
                'epistemic_metrics': t.epistemic_metrics,
                'quality': t.fitness.quality,
                'coverage': t.fitness.coverage,
                'efficiency': t.fitness.efficiency
            }
            for t in self.epistemic_history
        ]

        data = {'coordination_history': coordination_history}

        # Import validation framework
        from web4_epistemic_observational_extension import Web4EpistemicObservationalFramework

        framework = Web4EpistemicObservationalFramework()

        # Validate each prediction
        results = {}
        for pred_id in ["M1", "M2", "M4", "M5", "M6"]:  # Skip M3 (needs labeled data)
            prediction = framework.predictions_dict.get(pred_id)
            if not prediction:
                continue

            try:
                observed, error = prediction.measure(data)
                validated, significance = prediction.validate(observed, error)

                results[pred_id] = {
                    'name': prediction.name,
                    'observed': observed,
                    'predicted': prediction.predicted_value,
                    'range': prediction.predicted_range,
                    'validated': validated,
                    'significance': significance
                }
            except Exception as e:
                results[pred_id] = {
                    'name': prediction.name,
                    'error': str(e)
                }

        return results


def create_epistemic_coordinator_production() -> Web4EpistemicCoordinator:
    """
    Factory: Production-ready epistemic coordinator.

    Balanced mode with epistemic tracking enabled, interventions disabled.
    """
    params = CoordinationParameters(
        enable_multi_objective=True,
        coverage_weight=0.33,
        quality_weight=0.33,
        efficiency_weight=0.34
    )
    return Web4EpistemicCoordinator(
        params=params,
        enable_epistemic=True,
        enable_interventions=False  # Conservative: track but don't intervene
    )


def create_epistemic_coordinator_monitored() -> Web4EpistemicCoordinator:
    """
    Factory: Monitored epistemic coordinator with interventions.

    For testing/staging environments where interventions are safe.
    """
    params = CoordinationParameters(
        enable_multi_objective=True,
        coverage_weight=0.33,
        quality_weight=0.33,
        efficiency_weight=0.34
    )
    return Web4EpistemicCoordinator(
        params=params,
        enable_epistemic=True,
        enable_interventions=True,
        intervention_threshold=0.7
    )


# Example usage
if __name__ == "__main__":
    print("Web4 Phase 2: Epistemic Coordinator")
    print("=" * 80)
    print()
    print("Creating production epistemic coordinator...")

    coordinator = create_epistemic_coordinator_production()

    print("✓ Coordinator created with epistemic tracking enabled")
    print()
    print("Features:")
    print("- Multi-objective optimization: Enabled")
    print("- Epistemic state tracking: Enabled")
    print("- Automatic interventions: Disabled (production safety)")
    print()
    print("Usage:")
    print("  should_coord, telemetry = coordinator.coordinate(interaction)")
    print("  summary = coordinator.get_epistemic_summary()")
    print("  validation = coordinator.validate_predictions()")
    print()
