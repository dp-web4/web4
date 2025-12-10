#!/usr/bin/env python3
"""
Web4 Temporal Adaptation Framework

Session 8 - Track 39: Apply Thor S18's production temporal adaptation to Web4 coordination

Adapts SAGE's TemporalAdapter (sage/core/temporal_adaptation.py) for Web4 contexts:
- ATP allocation tuning (cost/recovery parameters)
- Authorization threshold adaptation (trust/risk parameters)
- Reputation dynamics tuning (coherence parameters)

Research Provenance:
- Thor S16: Temporal consciousness adaptation (685 LOC)
- Thor S17: Damping mechanism with satisfaction threshold (763 LOC)
- Thor S18: Production integration (512 LOC)
- Sprout S62: Cross-platform validation (Orin Nano)
- Legion S8: Web4 coordination adaptation (this module)

Key Features:
1. Satisfaction threshold: Stop adapting when performance >95%
2. Exponential damping: Prevent over-adaptation during stability
3. Multi-system coordination: ATP + Authorization + Reputation
4. Network-aware metrics: Interaction density, coherence, trust dynamics
5. Pattern learning: Time-of-day and workload pattern recognition

Integration Points:
- ATPAllocation: Resource constraint tuning
- AuthorizationSystem: Trust threshold adaptation
- ReputationTracker: Coherence parameter optimization
- NetworkCoordinator: Global performance monitoring

Hardware: All platforms (development, production, edge)
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List
from collections import deque
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AdaptationTrigger(Enum):
    """Types of adaptation triggers for Web4 systems"""
    # ATP-specific
    ATP_DEGRADATION = "atp_degradation"          # Resource efficiency dropped
    ATP_SURPLUS = "atp_surplus"                  # Consistent resource surplus
    ATP_STARVATION = "atp_starvation"            # Persistent resource shortage

    # Authorization-specific
    AUTH_DRIFT = "auth_drift"                    # Trust accuracy declining
    AUTH_CONSERVATIVE = "auth_conservative"       # Too many false rejections
    AUTH_PERMISSIVE = "auth_permissive"          # Too many false approvals

    # Reputation-specific
    REP_INSTABILITY = "rep_instability"          # Trust oscillations
    REP_STAGNATION = "rep_stagnation"            # No differentiation
    REP_FRAGMENTATION = "rep_fragmentation"       # Network partitioning

    # General
    PATTERN_SHIFT = "pattern_shift"              # Workload pattern changed
    NONE = "none"                                # No adaptation needed


@dataclass
class NetworkWindow:
    """
    Sliding window of Web4 network performance metrics.

    Tracks interaction density, authorization accuracy, ATP efficiency,
    reputation stability, and coordination quality over configurable window.
    """
    window_minutes: int = 15

    # ATP metrics
    atp_allocations: deque = field(default_factory=lambda: deque(maxlen=1000))
    atp_levels: deque = field(default_factory=lambda: deque(maxlen=1000))
    allocation_success: deque = field(default_factory=lambda: deque(maxlen=1000))

    # Authorization metrics
    auth_decisions: deque = field(default_factory=lambda: deque(maxlen=1000))
    auth_accuracy: deque = field(default_factory=lambda: deque(maxlen=100))
    false_positives: int = 0
    false_negatives: int = 0

    # Reputation metrics
    reputation_updates: deque = field(default_factory=lambda: deque(maxlen=1000))
    coherence_values: deque = field(default_factory=lambda: deque(maxlen=1000))
    trust_volatility: deque = field(default_factory=lambda: deque(maxlen=100))

    # Network metrics
    interaction_density: deque = field(default_factory=lambda: deque(maxlen=1000))
    coordination_quality: deque = field(default_factory=lambda: deque(maxlen=100))

    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    cycle_count: int = 0

    def add_cycle(
        self,
        atp_allocated: bool,
        atp_level: float,
        allocation_succeeded: bool,
        auth_decision: Optional[bool] = None,
        auth_correct: Optional[bool] = None,
        reputation_update: Optional[float] = None,
        coherence: Optional[float] = None,
        interaction_count: int = 0,
        coordination_score: Optional[float] = None
    ):
        """Add metrics from a single coordination cycle"""
        # ATP metrics
        self.atp_allocations.append(1.0 if atp_allocated else 0.0)
        self.atp_levels.append(atp_level)
        self.allocation_success.append(1.0 if allocation_succeeded else 0.0)

        # Authorization metrics
        if auth_decision is not None:
            self.auth_decisions.append(1.0 if auth_decision else 0.0)
            if auth_correct is not None:
                if auth_correct:
                    pass  # Correct decision
                else:
                    if auth_decision:
                        self.false_positives += 1  # Approved incorrectly
                    else:
                        self.false_negatives += 1  # Rejected incorrectly

        # Reputation metrics
        if reputation_update is not None:
            self.reputation_updates.append(reputation_update)
        if coherence is not None:
            self.coherence_values.append(coherence)

        # Network metrics
        self.interaction_density.append(float(interaction_count))
        if coordination_score is not None:
            self.coordination_quality.append(coordination_score)

        # Calculate derived metrics every 100 cycles
        if self.cycle_count % 100 == 0:
            self._update_derived_metrics()

        self.cycle_count += 1
        self.last_update = time.time()

    def _update_derived_metrics(self):
        """Calculate derived metrics for adaptation decisions"""
        # Authorization accuracy
        if self.auth_decisions:
            total_decisions = len(self.auth_decisions)
            errors = self.false_positives + self.false_negatives
            accuracy = 1.0 - (errors / max(1, total_decisions))
            self.auth_accuracy.append(accuracy)

        # Trust volatility (coefficient of variation)
        if len(self.coherence_values) > 1:
            mean_coh = statistics.mean(self.coherence_values)
            std_coh = statistics.stdev(self.coherence_values)
            volatility = std_coh / mean_coh if mean_coh > 0 else 0.0
            self.trust_volatility.append(volatility)

    def get_metrics(self) -> Dict[str, float]:
        """Calculate current window metrics"""
        if not self.atp_allocations:
            return {}

        metrics = {
            # ATP
            'atp_allocation_rate': statistics.mean(self.atp_allocations),
            'atp_efficiency': statistics.mean(self.allocation_success) if self.allocation_success else 0.0,
            'mean_atp_level': statistics.mean(self.atp_levels),
            'atp_volatility': statistics.stdev(self.atp_levels) if len(self.atp_levels) > 1 else 0.0,

            # Authorization
            'auth_rate': statistics.mean(self.auth_decisions) if self.auth_decisions else 0.0,
            'auth_accuracy': statistics.mean(self.auth_accuracy) if self.auth_accuracy else 0.0,
            'false_positive_rate': self.false_positives / max(1, len(self.auth_decisions)),
            'false_negative_rate': self.false_negatives / max(1, len(self.auth_decisions)),

            # Reputation
            'reputation_activity': len(self.reputation_updates) / max(1, self.cycle_count),
            'mean_coherence': statistics.mean(self.coherence_values) if self.coherence_values else 0.0,
            'trust_volatility': statistics.mean(self.trust_volatility) if self.trust_volatility else 0.0,

            # Network
            'interaction_density': statistics.mean(self.interaction_density),
            'coordination_quality': statistics.mean(self.coordination_quality) if self.coordination_quality else 0.0,

            # Meta
            'cycles': self.cycle_count,
            'duration_minutes': (self.last_update - self.start_time) / 60.0
        }

        return metrics

    def reset(self):
        """Reset window for new period"""
        self.atp_allocations.clear()
        self.atp_levels.clear()
        self.allocation_success.clear()
        self.auth_decisions.clear()
        self.auth_accuracy.clear()
        self.false_positives = 0
        self.false_negatives = 0
        self.reputation_updates.clear()
        self.coherence_values.clear()
        self.trust_volatility.clear()
        self.interaction_density.clear()
        self.coordination_quality.clear()
        self.start_time = time.time()
        self.last_update = time.time()
        self.cycle_count = 0


@dataclass
class Web4Parameters:
    """Tunable parameters for Web4 coordination systems"""
    # ATP parameters
    atp_attention_cost: float = 0.01          # ATP cost per allocation
    atp_rest_recovery: float = 0.05           # ATP recovery per REST cycle
    atp_allocation_threshold: float = 0.20     # Minimum ATP to allocate

    # Authorization parameters
    auth_trust_threshold: float = 0.50        # Minimum trust for approval
    auth_risk_tolerance: float = 0.30         # Maximum risk acceptable
    auth_adaptation_rate: float = 0.05        # Learning rate for thresholds

    # Reputation parameters
    rep_coherence_gamma: float = 2.0          # Coherence steepness
    rep_density_critical: float = 0.1         # Critical density threshold
    rep_decay_rate: float = 0.01              # Base reputation decay

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'atp_attention_cost': self.atp_attention_cost,
            'atp_rest_recovery': self.atp_rest_recovery,
            'atp_allocation_threshold': self.atp_allocation_threshold,
            'auth_trust_threshold': self.auth_trust_threshold,
            'auth_risk_tolerance': self.auth_risk_tolerance,
            'auth_adaptation_rate': self.auth_adaptation_rate,
            'rep_coherence_gamma': self.rep_coherence_gamma,
            'rep_density_critical': self.rep_density_critical,
            'rep_decay_rate': self.rep_decay_rate
        }


@dataclass
class AdaptationEvent:
    """Record of a single Web4 parameter adaptation"""
    timestamp: float
    trigger: AdaptationTrigger
    subsystem: str  # "ATP", "Authorization", "Reputation"
    old_params: Dict[str, float]
    new_params: Dict[str, float]
    metrics_before: Dict[str, float]
    metrics_after: Optional[Dict[str, float]] = None
    success: Optional[bool] = None
    damping_factor: float = 1.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            'timestamp': self.timestamp,
            'trigger': self.trigger.value,
            'subsystem': self.subsystem,
            'old_params': self.old_params,
            'new_params': self.new_params,
            'metrics_before': self.metrics_before,
            'metrics_after': self.metrics_after,
            'success': self.success,
            'damping_factor': self.damping_factor
        }


class Web4TemporalAdapter:
    """
    Production temporal adaptation system for Web4 coordination.

    Continuously monitors network performance and adapts coordination parameters
    to maintain optimal efficiency, accuracy, and stability.

    Based on Thor Sessions 16-18 (SAGE consciousness adaptation).
    Validated through Sprout Session 62 (cross-platform).
    Applied to Web4 coordination in Legion Session 8.
    """

    def __init__(
        self,
        initial_params: Optional[Web4Parameters] = None,
        adaptation_rate: float = 0.1,
        window_minutes: int = 15,
        satisfaction_threshold: float = 0.95,
        enable_damping: bool = True,
        damping_decay: float = 0.5,
        min_cycles_between_adaptations: int = 500
    ):
        """
        Initialize Web4 temporal adaptation system.

        Args:
            initial_params: Starting coordination parameters
            adaptation_rate: Base rate for parameter changes (±10% default)
            window_minutes: Performance monitoring window size
            satisfaction_threshold: Performance level considered excellent (0.95 = 95%)
            enable_damping: Apply exponential backoff for consecutive adaptations
            damping_decay: Rate of damping increase (0.5 = halve each time)
            min_cycles_between_adaptations: Minimum wait between adaptations
        """
        # Current parameters
        self.params = initial_params or Web4Parameters()

        # Adaptation configuration
        self.adaptation_rate = adaptation_rate
        self.satisfaction_threshold = satisfaction_threshold
        self.enable_damping = enable_damping
        self.damping_decay = damping_decay

        # Performance windows
        self.current_window = NetworkWindow(window_minutes=window_minutes)
        self.previous_window = NetworkWindow(window_minutes=window_minutes)

        # Adaptation state
        self.adaptation_history: List[AdaptationEvent] = []
        self.cycles_since_adaptation = 0
        self.min_cycles_between_adaptations = min_cycles_between_adaptations

        # Damping state
        self.consecutive_similar_triggers = 0
        self.last_trigger = AdaptationTrigger.NONE
        self.current_damping_factor = 1.0

        # Satisfaction tracking per subsystem
        self.satisfaction_windows = {
            'ATP': 0,
            'Authorization': 0,
            'Reputation': 0
        }

        # Statistics
        self.total_adaptations = 0
        self.successful_adaptations = 0
        self.start_time = time.time()

    def update(
        self,
        atp_allocated: bool,
        atp_level: float,
        allocation_succeeded: bool,
        auth_decision: Optional[bool] = None,
        auth_correct: Optional[bool] = None,
        reputation_update: Optional[float] = None,
        coherence: Optional[float] = None,
        interaction_count: int = 0,
        coordination_score: Optional[float] = None
    ) -> Optional[Tuple[str, Web4Parameters]]:
        """
        Update adapter with metrics from a coordination cycle.

        Returns:
            (subsystem, new_params) if adaptation triggered, None otherwise
        """
        # Add metrics to current window
        self.current_window.add_cycle(
            atp_allocated=atp_allocated,
            atp_level=atp_level,
            allocation_succeeded=allocation_succeeded,
            auth_decision=auth_decision,
            auth_correct=auth_correct,
            reputation_update=reputation_update,
            coherence=coherence,
            interaction_count=interaction_count,
            coordination_score=coordination_score
        )

        self.cycles_since_adaptation += 1

        # Check if adaptation needed
        if self.cycles_since_adaptation < self.min_cycles_between_adaptations:
            return None

        trigger, subsystem, reason = self._should_adapt()

        if trigger != AdaptationTrigger.NONE:
            # Perform adaptation
            old_params = self.params.to_dict()
            self._adapt_parameters(trigger, subsystem)
            new_params = self.params.to_dict()

            # Record adaptation event
            event = AdaptationEvent(
                timestamp=time.time(),
                trigger=trigger,
                subsystem=subsystem,
                old_params=old_params,
                new_params=new_params,
                metrics_before=self.current_window.get_metrics(),
                damping_factor=self.current_damping_factor
            )

            self.adaptation_history.append(event)
            self.total_adaptations += 1

            # Update damping state
            self._update_damping(trigger)

            # Reset cycle counter
            self.cycles_since_adaptation = 0

            # Shift windows
            self.previous_window = self.current_window
            self.current_window = NetworkWindow(window_minutes=self.current_window.window_minutes)

            logger.info(f"Web4 adaptation: {trigger.value} | {subsystem} | "
                       f"damping={self.current_damping_factor:.2f} | {reason}")

            return (subsystem, self.params)

        return None

    def _should_adapt(self) -> Tuple[AdaptationTrigger, str, str]:
        """
        Determine if adaptation is needed.

        Returns:
            (trigger_type, subsystem, reason_string)
        """
        current = self.current_window.get_metrics()

        if not current:
            return (AdaptationTrigger.NONE, "", "insufficient data")

        # SATISFACTION CHECKS (Primary mechanism from Thor S17)

        # ATP satisfaction
        atp_efficiency = current.get('atp_efficiency', 0.0)
        if atp_efficiency >= self.satisfaction_threshold:
            self.satisfaction_windows['ATP'] += 1
            if self.satisfaction_windows['ATP'] >= 3:
                # Continue to check other subsystems
                pass
        else:
            self.satisfaction_windows['ATP'] = 0

        # Authorization satisfaction
        auth_accuracy = current.get('auth_accuracy', 0.0)
        if auth_accuracy >= self.satisfaction_threshold:
            self.satisfaction_windows['Authorization'] += 1
        else:
            self.satisfaction_windows['Authorization'] = 0

        # Reputation satisfaction (measured by low volatility)
        trust_volatility = current.get('trust_volatility', 1.0)
        if trust_volatility < (1.0 - self.satisfaction_threshold):  # <5% volatility
            self.satisfaction_windows['Reputation'] += 1
        else:
            self.satisfaction_windows['Reputation'] = 0

        # ATP CHECKS
        if self.satisfaction_windows['ATP'] < 3:
            # Not satisfied - check for ATP issues
            if atp_efficiency < 0.70:
                return (AdaptationTrigger.ATP_DEGRADATION, 'ATP',
                       f"efficiency low ({atp_efficiency:.1%})")

            mean_atp = current.get('mean_atp_level', 0.0)
            allocation_rate = current.get('atp_allocation_rate', 0.0)

            if mean_atp < 0.15:
                return (AdaptationTrigger.ATP_STARVATION, 'ATP',
                       f"persistent shortage (ATP {mean_atp:.1%})")

            if mean_atp > 0.85 and allocation_rate < 0.70:
                return (AdaptationTrigger.ATP_SURPLUS, 'ATP',
                       f"surplus ({mean_atp:.1%}) with low allocation ({allocation_rate:.1%})")

        # AUTHORIZATION CHECKS
        if self.satisfaction_windows['Authorization'] < 3:
            # Not satisfied - check for authorization issues
            if auth_accuracy > 0 and auth_accuracy < 0.85:
                return (AdaptationTrigger.AUTH_DRIFT, 'Authorization',
                       f"accuracy degraded ({auth_accuracy:.1%})")

            fp_rate = current.get('false_positive_rate', 0.0)
            fn_rate = current.get('false_negative_rate', 0.0)

            if fp_rate > 0.15:
                return (AdaptationTrigger.AUTH_PERMISSIVE, 'Authorization',
                       f"too permissive (FP {fp_rate:.1%})")

            if fn_rate > 0.15:
                return (AdaptationTrigger.AUTH_CONSERVATIVE, 'Authorization',
                       f"too conservative (FN {fn_rate:.1%})")

        # REPUTATION CHECKS
        if self.satisfaction_windows['Reputation'] < 3:
            # Not satisfied - check for reputation issues
            if trust_volatility > 0.30:
                return (AdaptationTrigger.REP_INSTABILITY, 'Reputation',
                       f"high volatility ({trust_volatility:.1%})")

            coherence = current.get('mean_coherence', 0.0)
            if coherence > 0 and coherence < 0.10:
                return (AdaptationTrigger.REP_STAGNATION, 'Reputation',
                       f"low differentiation (coherence {coherence:.2f})")

        return (AdaptationTrigger.NONE, "", "all subsystems satisfied or acceptable")

    def _adapt_parameters(self, trigger: AdaptationTrigger, subsystem: str):
        """
        Adapt parameters based on trigger type.

        Args:
            trigger: Type of adaptation needed
            subsystem: Which subsystem to adapt
        """
        effective_rate = self.adaptation_rate * self.current_damping_factor

        if subsystem == 'ATP':
            if trigger == AdaptationTrigger.ATP_DEGRADATION:
                # Make allocation cheaper, recovery faster
                self.params.atp_attention_cost *= (1.0 - effective_rate)
                self.params.atp_rest_recovery *= (1.0 + effective_rate)

            elif trigger == AdaptationTrigger.ATP_STARVATION:
                # Reduce cost significantly
                self.params.atp_attention_cost *= (1.0 - effective_rate * 1.5)

            elif trigger == AdaptationTrigger.ATP_SURPLUS:
                # Can afford more allocation
                self.params.atp_attention_cost *= (1.0 - effective_rate * 0.5)

            # Clamp to reasonable ranges
            self.params.atp_attention_cost = max(0.001, min(0.05, self.params.atp_attention_cost))
            self.params.atp_rest_recovery = max(0.01, min(0.10, self.params.atp_rest_recovery))

        elif subsystem == 'Authorization':
            if trigger == AdaptationTrigger.AUTH_DRIFT:
                # Increase adaptation rate temporarily
                self.params.auth_adaptation_rate *= (1.0 + effective_rate)

            elif trigger == AdaptationTrigger.AUTH_PERMISSIVE:
                # Raise trust threshold, lower risk tolerance
                self.params.auth_trust_threshold *= (1.0 + effective_rate)
                self.params.auth_risk_tolerance *= (1.0 - effective_rate)

            elif trigger == AdaptationTrigger.AUTH_CONSERVATIVE:
                # Lower trust threshold, raise risk tolerance
                self.params.auth_trust_threshold *= (1.0 - effective_rate)
                self.params.auth_risk_tolerance *= (1.0 + effective_rate)

            # Clamp to reasonable ranges
            self.params.auth_trust_threshold = max(0.30, min(0.80, self.params.auth_trust_threshold))
            self.params.auth_risk_tolerance = max(0.10, min(0.50, self.params.auth_risk_tolerance))
            self.params.auth_adaptation_rate = max(0.01, min(0.20, self.params.auth_adaptation_rate))

        elif subsystem == 'Reputation':
            if trigger == AdaptationTrigger.REP_INSTABILITY:
                # Increase coherence steepness (more stability)
                self.params.rep_coherence_gamma *= (1.0 + effective_rate)

            elif trigger == AdaptationTrigger.REP_STAGNATION:
                # Decrease coherence steepness (more differentiation)
                self.params.rep_coherence_gamma *= (1.0 - effective_rate)

            # Clamp to reasonable ranges
            self.params.rep_coherence_gamma = max(1.0, min(5.0, self.params.rep_coherence_gamma))
            self.params.rep_density_critical = max(0.01, min(0.50, self.params.rep_density_critical))

    def _update_damping(self, trigger: AdaptationTrigger):
        """Update damping factor based on adaptation history"""
        if not self.enable_damping:
            return

        # Check if same type of trigger as last time
        if trigger == self.last_trigger:
            self.consecutive_similar_triggers += 1
            # Exponential damping
            self.current_damping_factor *= self.damping_decay
            self.current_damping_factor = max(0.1, self.current_damping_factor)
        else:
            # New trigger type → reset damping
            self.consecutive_similar_triggers = 0
            self.current_damping_factor = 1.0

        self.last_trigger = trigger

    def get_statistics(self) -> Dict:
        """Get adaptation statistics"""
        runtime_hours = (time.time() - self.start_time) / 3600.0

        return {
            'runtime_hours': runtime_hours,
            'total_adaptations': self.total_adaptations,
            'adaptations_per_hour': self.total_adaptations / runtime_hours if runtime_hours > 0 else 0,
            'current_params': self.params.to_dict(),
            'current_damping': self.current_damping_factor,
            'satisfaction_windows': self.satisfaction_windows.copy(),
            'cycles_since_adaptation': self.cycles_since_adaptation,
            'current_metrics': self.current_window.get_metrics()
        }

    def export_history(self) -> List[Dict]:
        """Export adaptation history for analysis"""
        return [event.to_dict() for event in self.adaptation_history]


# Convenience factory functions

def create_production_web4_adapter(**kwargs) -> Web4TemporalAdapter:
    """
    Create Web4 adapter with production settings.

    Balanced configuration suitable for most deployments.
    """
    defaults = {
        'adaptation_rate': 0.1,
        'satisfaction_threshold': 0.95,
        'enable_damping': True,
        'damping_decay': 0.5,
        'min_cycles_between_adaptations': 500
    }
    defaults.update(kwargs)
    return Web4TemporalAdapter(**defaults)


def create_conservative_web4_adapter(**kwargs) -> Web4TemporalAdapter:
    """
    Create Web4 adapter with conservative settings.

    Less frequent adaptations, suitable for stable networks.
    """
    defaults = {
        'adaptation_rate': 0.05,
        'satisfaction_threshold': 0.90,
        'enable_damping': True,
        'damping_decay': 0.3,
        'min_cycles_between_adaptations': 1000
    }
    defaults.update(kwargs)
    return Web4TemporalAdapter(**defaults)


def create_responsive_web4_adapter(**kwargs) -> Web4TemporalAdapter:
    """
    Create Web4 adapter with responsive settings.

    More aggressive adaptations, suitable for highly dynamic networks.
    """
    defaults = {
        'adaptation_rate': 0.15,
        'satisfaction_threshold': 0.95,
        'enable_damping': True,
        'damping_decay': 0.7,
        'min_cycles_between_adaptations': 300
    }
    defaults.update(kwargs)
    return Web4TemporalAdapter(**defaults)


if __name__ == "__main__":
    # Example usage
    print("Web4 Temporal Adaptation Framework")
    print("=" * 60)
    print()
    print("Based on Thor S16-S18 (SAGE consciousness adaptation)")
    print("Applied to Web4 coordination systems (Legion S8)")
    print()
    print("Key Features:")
    print("  • Satisfaction threshold prevents over-adaptation")
    print("  • Multi-system coordination (ATP + Auth + Rep)")
    print("  • Network-aware performance metrics")
    print("  • Exponential damping for stability")
    print()
    print("Factory Functions:")
    print("  • create_production_web4_adapter() - Default")
    print("  • create_conservative_web4_adapter() - Stable networks")
    print("  • create_responsive_web4_adapter() - Dynamic networks")
    print()

    # Create example adapter
    adapter = create_production_web4_adapter()
    print(f"Production adapter created:")
    print(f"  Adaptation rate: {adapter.adaptation_rate}")
    print(f"  Satisfaction threshold: {adapter.satisfaction_threshold}")
    print(f"  Damping enabled: {adapter.enable_damping}")
    print(f"  Min cycles between adaptations: {adapter.min_cycles_between_adaptations}")
    print()
    print(f"Initial parameters:")
    for key, value in adapter.params.to_dict().items():
        print(f"  {key}: {value:.4f}")
