#!/usr/bin/env python3
"""
Authorization Satisfaction Threshold

Session 8 - Track 40: Apply satisfaction threshold to authorization learning

Prevents over-optimization in authorization systems by implementing satisfaction checks.
When accuracy >95% for 3 consecutive evaluation windows, stop adapting parameters.

Research Provenance:
- Thor S17: Damping mechanism with satisfaction threshold (763 LOC)
- Thor S18: Production temporal adaptation (512 LOC)
- Sprout S62: Cross-platform validation (satisfaction threshold works)
- Legion S8 Track 39: Web4 temporal adaptation framework
- Legion S8 Track 40: Authorization-specific satisfaction (this module)

Key Insight from Thor S17:
"Satisfaction threshold > Exponential damping (for this use case)
Stop adapting when performance excellent, even if 'opportunities' exist
Prevents optimization beyond practical benefit"

Application to Authorization:
- Stop tuning trust thresholds when accuracy >95%
- Prevent unnecessary micro-adjustments during stable periods
- Avoid over-fitting to noise in authorization decisions
- Maintain stable, predictable authorization behavior

Integration Points:
- EmpiricaLAuthorizationCollector: Add satisfaction tracking
- AuthorizationEngine: Stop adapting when satisfied
- Web4TemporalAdapter: Use for authorization subsystem
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import deque
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuthAdaptationTrigger(Enum):
    """Types of adaptation triggers for authorization systems"""
    ACCURACY_DEGRADATION = "accuracy_degradation"    # Accuracy dropped
    FALSE_POSITIVE_HIGH = "false_positive_high"      # Too permissive
    FALSE_NEGATIVE_HIGH = "false_negative_high"      # Too conservative
    DRIFT_DETECTED = "drift_detected"                # Decision patterns changing
    NONE = "none"                                    # Satisfied or acceptable


@dataclass
class AuthorizationWindow:
    """
    Sliding window of authorization performance metrics.

    Tracks accuracy, false positive rate, false negative rate,
    and decision consistency over configurable time window.
    """
    window_minutes: int = 15

    # Decision outcomes
    decisions: deque = field(default_factory=lambda: deque(maxlen=1000))
    correct_decisions: deque = field(default_factory=lambda: deque(maxlen=1000))
    false_positives: int = 0
    false_negatives: int = 0
    true_positives: int = 0
    true_negatives: int = 0

    # Accuracy tracking
    accuracy_scores: deque = field(default_factory=lambda: deque(maxlen=100))

    # Trust threshold tracking
    trust_thresholds: deque = field(default_factory=lambda: deque(maxlen=1000))

    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    decision_count: int = 0

    def add_decision(
        self,
        approved: bool,
        should_approve: bool,
        trust_score: float,
        current_threshold: float
    ):
        """Add an authorization decision outcome"""
        self.decisions.append(1.0 if approved else 0.0)
        correct = (approved == should_approve)
        self.correct_decisions.append(1.0 if correct else 0.0)

        # Track confusion matrix
        if approved and should_approve:
            self.true_positives += 1
        elif approved and not should_approve:
            self.false_positives += 1
        elif not approved and should_approve:
            self.false_negatives += 1
        else:  # not approved and not should_approve
            self.true_negatives += 1

        # Track threshold usage
        self.trust_thresholds.append(current_threshold)

        # Calculate accuracy every 100 decisions
        if self.decision_count % 100 == 0 and self.decision_count > 0:
            total = self.decision_count
            errors = self.false_positives + self.false_negatives
            accuracy = 1.0 - (errors / total)
            self.accuracy_scores.append(accuracy)

        self.decision_count += 1
        self.last_update = time.time()

    def get_metrics(self) -> Dict[str, float]:
        """Calculate current window metrics"""
        if self.decision_count == 0:
            return {}

        total = self.decision_count
        errors = self.false_positives + self.false_negatives

        metrics = {
            # Core metrics
            'accuracy': 1.0 - (errors / total) if total > 0 else 0.0,
            'decisions': self.decision_count,

            # Confusion matrix rates
            'false_positive_rate': self.false_positives / max(1, total),
            'false_negative_rate': self.false_negatives / max(1, total),
            'true_positive_rate': self.true_positives / max(1, total),
            'true_negative_rate': self.true_negatives / max(1, total),

            # Precision and recall
            'precision': self.true_positives / max(1, self.true_positives + self.false_positives),
            'recall': self.true_positives / max(1, self.true_positives + self.false_negatives),

            # Threshold stability
            'mean_threshold': statistics.mean(self.trust_thresholds) if self.trust_thresholds else 0.0,
            'threshold_std': statistics.stdev(self.trust_thresholds) if len(self.trust_thresholds) > 1 else 0.0,

            # Recent accuracy trend
            'recent_accuracy': statistics.mean(self.accuracy_scores) if self.accuracy_scores else 0.0,

            # Meta
            'duration_minutes': (self.last_update - self.start_time) / 60.0
        }

        # F1 score
        precision = metrics['precision']
        recall = metrics['recall']
        if precision + recall > 0:
            metrics['f1_score'] = 2 * (precision * recall) / (precision + recall)
        else:
            metrics['f1_score'] = 0.0

        return metrics

    def reset(self):
        """Reset window for new period"""
        self.decisions.clear()
        self.correct_decisions.clear()
        self.false_positives = 0
        self.false_negatives = 0
        self.true_positives = 0
        self.true_negatives = 0
        self.accuracy_scores.clear()
        self.trust_thresholds.clear()
        self.start_time = time.time()
        self.last_update = time.time()
        self.decision_count = 0


@dataclass
class AuthorizationThresholds:
    """Tunable authorization thresholds"""
    trust_threshold: float = 0.50       # Minimum trust to approve
    risk_tolerance: float = 0.30        # Maximum risk acceptable
    criticality_multiplier: float = 1.5 # Raise threshold for critical actions
    learning_rate: float = 0.05         # Rate of threshold adjustment

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'trust_threshold': self.trust_threshold,
            'risk_tolerance': self.risk_tolerance,
            'criticality_multiplier': self.criticality_multiplier,
            'learning_rate': self.learning_rate
        }


@dataclass
class AuthAdaptationEvent:
    """Record of threshold adaptation"""
    timestamp: float
    trigger: AuthAdaptationTrigger
    old_thresholds: Dict[str, float]
    new_thresholds: Dict[str, float]
    metrics_before: Dict[str, float]
    damping_factor: float = 1.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            'timestamp': self.timestamp,
            'trigger': self.trigger.value,
            'old_thresholds': self.old_thresholds,
            'new_thresholds': self.new_thresholds,
            'metrics_before': self.metrics_before,
            'damping_factor': self.damping_factor
        }


class AuthorizationSatisfactionAdapter:
    """
    Authorization threshold adapter with satisfaction threshold.

    Prevents over-optimization by stopping adaptation when performance
    is excellent (>95% accuracy for 3 consecutive windows).

    Based on Thor S17's satisfaction threshold mechanism.
    """

    def __init__(
        self,
        initial_thresholds: Optional[AuthorizationThresholds] = None,
        adaptation_rate: float = 0.05,
        satisfaction_threshold: float = 0.95,
        satisfaction_windows_required: int = 3,
        enable_damping: bool = True,
        damping_decay: float = 0.5,
        min_decisions_between_adaptations: int = 500
    ):
        """
        Initialize authorization satisfaction adapter.

        Args:
            initial_thresholds: Starting authorization thresholds
            adaptation_rate: Base rate for threshold changes (±5% default)
            satisfaction_threshold: Accuracy level considered excellent (0.95 = 95%)
            satisfaction_windows_required: Consecutive windows above threshold to stop (3)
            enable_damping: Apply exponential backoff for consecutive adaptations
            damping_decay: Rate of damping increase (0.5 = halve each time)
            min_decisions_between_adaptations: Minimum decisions between adaptations
        """
        # Current thresholds
        self.thresholds = initial_thresholds or AuthorizationThresholds()

        # Adaptation configuration
        self.adaptation_rate = adaptation_rate
        self.satisfaction_threshold = satisfaction_threshold
        self.satisfaction_windows_required = satisfaction_windows_required
        self.enable_damping = enable_damping
        self.damping_decay = damping_decay

        # Performance windows
        self.current_window = AuthorizationWindow()
        self.previous_window = AuthorizationWindow()

        # Adaptation state
        self.adaptation_history: List[AuthAdaptationEvent] = []
        self.decisions_since_adaptation = 0
        self.min_decisions_between_adaptations = min_decisions_between_adaptations

        # Satisfaction tracking
        self.satisfaction_stable_windows = 0

        # Damping state
        self.consecutive_similar_triggers = 0
        self.last_trigger = AuthAdaptationTrigger.NONE
        self.current_damping_factor = 1.0

        # Statistics
        self.total_adaptations = 0
        self.start_time = time.time()

    def add_decision(
        self,
        approved: bool,
        should_approve: bool,
        trust_score: float
    ) -> Optional[AuthorizationThresholds]:
        """
        Record an authorization decision and check if adaptation needed.

        Args:
            approved: Whether request was approved
            should_approve: Ground truth (whether it should have been approved)
            trust_score: The trust score used for decision

        Returns:
            New thresholds if adaptation triggered, None otherwise
        """
        # Add to current window
        self.current_window.add_decision(
            approved=approved,
            should_approve=should_approve,
            trust_score=trust_score,
            current_threshold=self.thresholds.trust_threshold
        )

        self.decisions_since_adaptation += 1

        # Check if adaptation needed
        if self.decisions_since_adaptation < self.min_decisions_between_adaptations:
            return None

        trigger, reason = self._should_adapt()

        if trigger != AuthAdaptationTrigger.NONE:
            # Perform adaptation
            old_thresholds = self.thresholds.to_dict()
            self._adapt_thresholds(trigger)
            new_thresholds = self.thresholds.to_dict()

            # Record event
            event = AuthAdaptationEvent(
                timestamp=time.time(),
                trigger=trigger,
                old_thresholds=old_thresholds,
                new_thresholds=new_thresholds,
                metrics_before=self.current_window.get_metrics(),
                damping_factor=self.current_damping_factor
            )

            self.adaptation_history.append(event)
            self.total_adaptations += 1

            # Update damping
            self._update_damping(trigger)

            # Reset counter
            self.decisions_since_adaptation = 0

            # Shift windows
            self.previous_window = self.current_window
            self.current_window = AuthorizationWindow()

            logger.info(f"Authorization adaptation: {trigger.value} | "
                       f"threshold {old_thresholds['trust_threshold']:.3f}→"
                       f"{new_thresholds['trust_threshold']:.3f} | "
                       f"damping={self.current_damping_factor:.2f} | {reason}")

            return self.thresholds

        return None

    def _should_adapt(self) -> Tuple[AuthAdaptationTrigger, str]:
        """
        Determine if adaptation is needed.

        Returns:
            (trigger_type, reason_string)
        """
        current = self.current_window.get_metrics()

        if not current or current.get('decisions', 0) < 100:
            return (AuthAdaptationTrigger.NONE, "insufficient decisions")

        accuracy = current.get('accuracy', 0.0)

        # SATISFACTION CHECK (Primary mechanism from Thor S17)
        if accuracy >= self.satisfaction_threshold:
            self.satisfaction_stable_windows += 1

            # Satisfied for required consecutive windows → stop adapting
            if self.satisfaction_stable_windows >= self.satisfaction_windows_required:
                return (AuthAdaptationTrigger.NONE,
                       f"satisfied (accuracy {accuracy:.1%} for "
                       f"{self.satisfaction_stable_windows} windows)")
        else:
            # Reset satisfaction counter if accuracy drops
            self.satisfaction_stable_windows = 0

        # DEGRADATION CHECK
        if self.previous_window.get_metrics():
            prev_accuracy = self.previous_window.get_metrics().get('accuracy', 0.0)
            accuracy_delta = accuracy - prev_accuracy

            if accuracy_delta < -0.05:  # 5% drop
                return (AuthAdaptationTrigger.ACCURACY_DEGRADATION,
                       f"accuracy degraded {accuracy_delta:+.1%} "
                       f"({prev_accuracy:.1%}→{accuracy:.1%})")

        # FALSE POSITIVE CHECK
        fp_rate = current.get('false_positive_rate', 0.0)
        if fp_rate > 0.15:  # >15% false positives
            return (AuthAdaptationTrigger.FALSE_POSITIVE_HIGH,
                   f"too permissive (FP {fp_rate:.1%})")

        # FALSE NEGATIVE CHECK
        fn_rate = current.get('false_negative_rate', 0.0)
        if fn_rate > 0.15:  # >15% false negatives
            return (AuthAdaptationTrigger.FALSE_NEGATIVE_HIGH,
                   f"too conservative (FN {fn_rate:.1%})")

        # DRIFT CHECK
        threshold_std = current.get('threshold_std', 0.0)
        if threshold_std > 0.10:  # High variance in effective threshold
            return (AuthAdaptationTrigger.DRIFT_DETECTED,
                   f"decision patterns unstable (σ {threshold_std:.3f})")

        return (AuthAdaptationTrigger.NONE, "performance acceptable")

    def _adapt_thresholds(self, trigger: AuthAdaptationTrigger):
        """
        Adapt authorization thresholds based on trigger type.

        Args:
            trigger: Type of adaptation needed
        """
        effective_rate = self.adaptation_rate * self.current_damping_factor

        if trigger == AuthAdaptationTrigger.ACCURACY_DEGRADATION:
            # Increase learning rate temporarily to recover faster
            self.thresholds.learning_rate *= (1.0 + effective_rate)

        elif trigger == AuthAdaptationTrigger.FALSE_POSITIVE_HIGH:
            # Raise trust threshold (be more conservative)
            self.thresholds.trust_threshold *= (1.0 + effective_rate)
            # Lower risk tolerance
            self.thresholds.risk_tolerance *= (1.0 - effective_rate)

        elif trigger == AuthAdaptationTrigger.FALSE_NEGATIVE_HIGH:
            # Lower trust threshold (be less conservative)
            self.thresholds.trust_threshold *= (1.0 - effective_rate)
            # Raise risk tolerance
            self.thresholds.risk_tolerance *= (1.0 + effective_rate)

        elif trigger == AuthAdaptationTrigger.DRIFT_DETECTED:
            # Increase criticality multiplier to stabilize
            self.thresholds.criticality_multiplier *= (1.0 + effective_rate * 0.5)

        # Clamp to reasonable ranges
        self.thresholds.trust_threshold = max(0.30, min(0.80, self.thresholds.trust_threshold))
        self.thresholds.risk_tolerance = max(0.10, min(0.50, self.thresholds.risk_tolerance))
        self.thresholds.criticality_multiplier = max(1.0, min(3.0, self.thresholds.criticality_multiplier))
        self.thresholds.learning_rate = max(0.01, min(0.20, self.thresholds.learning_rate))

    def _update_damping(self, trigger: AuthAdaptationTrigger):
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

        current_metrics = self.current_window.get_metrics()

        return {
            'runtime_hours': runtime_hours,
            'total_adaptations': self.total_adaptations,
            'adaptations_per_hour': self.total_adaptations / runtime_hours if runtime_hours > 0 else 0,
            'current_thresholds': self.thresholds.to_dict(),
            'current_damping': self.current_damping_factor,
            'satisfaction_stable_windows': self.satisfaction_stable_windows,
            'decisions_since_adaptation': self.decisions_since_adaptation,
            'current_accuracy': current_metrics.get('accuracy', 0.0),
            'current_f1_score': current_metrics.get('f1_score', 0.0)
        }

    def export_history(self) -> List[Dict]:
        """Export adaptation history for analysis"""
        return [event.to_dict() for event in self.adaptation_history]


# Convenience factory functions

def create_production_auth_adapter(**kwargs) -> AuthorizationSatisfactionAdapter:
    """
    Create authorization adapter with production settings.

    Balanced configuration suitable for most deployments.
    """
    defaults = {
        'adaptation_rate': 0.05,
        'satisfaction_threshold': 0.95,
        'satisfaction_windows_required': 3,
        'enable_damping': True,
        'damping_decay': 0.5,
        'min_decisions_between_adaptations': 500
    }
    defaults.update(kwargs)
    return AuthorizationSatisfactionAdapter(**defaults)


def create_conservative_auth_adapter(**kwargs) -> AuthorizationSatisfactionAdapter:
    """
    Create authorization adapter with conservative settings.

    Less frequent adaptations, suitable for stable authorization patterns.
    """
    defaults = {
        'adaptation_rate': 0.02,
        'satisfaction_threshold': 0.90,
        'satisfaction_windows_required': 5,
        'enable_damping': True,
        'damping_decay': 0.3,
        'min_decisions_between_adaptations': 1000
    }
    defaults.update(kwargs)
    return AuthorizationSatisfactionAdapter(**defaults)


def create_responsive_auth_adapter(**kwargs) -> AuthorizationSatisfactionAdapter:
    """
    Create authorization adapter with responsive settings.

    More aggressive adaptations, suitable for dynamic authorization patterns.
    """
    defaults = {
        'adaptation_rate': 0.10,
        'satisfaction_threshold': 0.95,
        'satisfaction_windows_required': 2,
        'enable_damping': True,
        'damping_decay': 0.7,
        'min_decisions_between_adaptations': 300
    }
    defaults.update(kwargs)
    return AuthorizationSatisfactionAdapter(**defaults)


if __name__ == "__main__":
    # Example usage
    print("Authorization Satisfaction Threshold Framework")
    print("=" * 60)
    print()
    print("Based on Thor S17 (satisfaction threshold prevents over-adaptation)")
    print("Applied to Web4 authorization systems (Legion S8 Track 40)")
    print()
    print("Key Feature:")
    print("  • Stop adapting when accuracy >95% for 3 consecutive windows")
    print("  • Prevents unnecessary micro-tuning during stable periods")
    print("  • Avoids over-fitting to noise in authorization decisions")
    print()
    print("Factory Functions:")
    print("  • create_production_auth_adapter() - Default")
    print("  • create_conservative_auth_adapter() - Stable patterns")
    print("  • create_responsive_auth_adapter() - Dynamic patterns")
    print()

    # Create example adapter
    adapter = create_production_auth_adapter()
    print(f"Production adapter created:")
    print(f"  Adaptation rate: {adapter.adaptation_rate}")
    print(f"  Satisfaction threshold: {adapter.satisfaction_threshold}")
    print(f"  Windows required: {adapter.satisfaction_windows_required}")
    print(f"  Damping enabled: {adapter.enable_damping}")
    print()
    print(f"Initial thresholds:")
    for key, value in adapter.thresholds.to_dict().items():
        print(f"  {key}: {value:.4f}")
