# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Trust Decay (Temporal Coherence)
# https://github.com/dp-web4/web4

"""
Trust Decay: Temporal coherence for trust tensors.

Trust should not be static - it naturally decays without continued
positive interaction. This implements:

1. **Time-based decay**: Trust decreases toward baseline over time
2. **Activity-weighted decay**: Recent interactions slow decay
3. **Dimension-specific decay**: Different dimensions decay differently
4. **Minimum trust floor**: Decay cannot go below baseline

Key insight: Trust decay is not punishment - it's acknowledging that
information about an entity becomes less reliable over time. Old
successes don't guarantee future performance.

Mathematical model:
    trust(t) = baseline + (trust(t0) - baseline) * e^(-λ * Δt)

Where:
    - baseline: Default trust level (0.5)
    - trust(t0): Trust at last update
    - λ (lambda): Decay rate constant
    - Δt: Time since last update (in decay periods)
"""

import math
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List
import json


@dataclass
class DecayConfig:
    """Configuration for trust decay."""

    # Baseline trust (decay target)
    baseline: float = 0.5

    # Decay rate constants per dimension (higher = faster decay)
    # Default: ~50% decay toward baseline per month of inactivity
    decay_rates: Dict[str, float] = field(default_factory=lambda: {
        'competence': 0.02,   # Skills decay slowly
        'reliability': 0.05,  # Recent reliability matters more
        'consistency': 0.03,  # Pattern recognition is stable
        'witnesses': 0.10,    # Witness attestations age quickly
        'lineage': 0.01,      # Historical record is stable
        'alignment': 0.04     # Alignment can shift
    })

    # Period for decay calculation (seconds)
    decay_period: int = 86400  # 1 day

    # Activity factor: how much recent activity slows decay
    # 1.0 = no effect, 0.0 = activity stops decay completely
    activity_decay_factor: float = 0.3

    # Minimum activity window (seconds) to consider "recent"
    activity_window: int = 604800  # 1 week

    # Bonus for sustained high trust
    sustained_bonus_threshold: float = 0.8
    sustained_bonus_factor: float = 0.5  # Decay at 50% rate if trust > threshold


@dataclass
class TrustSnapshot:
    """Trust state at a point in time."""
    timestamp: str  # ISO8601
    values: Dict[str, float]  # Dimension -> value
    action_count: int = 0  # Actions since last snapshot


class TrustDecayCalculator:
    """
    Calculates trust decay over time.

    Usage:
        calc = TrustDecayCalculator()
        decayed = calc.apply_decay(current_trust, last_update, now, action_count)
    """

    def __init__(self, config: Optional[DecayConfig] = None):
        self.config = config or DecayConfig()

    def apply_decay(
        self,
        trust: Dict[str, float],
        last_update: datetime,
        now: Optional[datetime] = None,
        actions_since_update: int = 0
    ) -> Dict[str, float]:
        """
        Apply time-based decay to trust values.

        Args:
            trust: Current trust values by dimension
            last_update: When trust was last updated
            now: Current time (uses utcnow if None)
            actions_since_update: Number of actions since last update

        Returns:
            Decayed trust values
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Calculate time delta in decay periods
        if isinstance(last_update, str):
            if last_update.endswith('Z'):
                last_update = last_update[:-1] + '+00:00'
            last_update = datetime.fromisoformat(last_update)

        delta = (now - last_update).total_seconds()
        periods = delta / self.config.decay_period

        if periods <= 0:
            return trust  # No decay

        # Calculate activity factor
        activity_factor = self._calculate_activity_factor(
            actions_since_update,
            delta
        )

        # Apply decay to each dimension
        decayed = {}
        for dim, value in trust.items():
            decayed[dim] = self._decay_dimension(
                dim, value, periods, activity_factor
            )

        return decayed

    def _decay_dimension(
        self,
        dimension: str,
        value: float,
        periods: float,
        activity_factor: float
    ) -> float:
        """Apply decay to a single dimension."""
        base_rate = self.config.decay_rates.get(dimension, 0.03)

        # Adjust rate based on activity
        effective_rate = base_rate * activity_factor

        # Bonus for sustained high trust
        if value > self.config.sustained_bonus_threshold:
            effective_rate *= self.config.sustained_bonus_factor

        # Exponential decay toward baseline
        baseline = self.config.baseline
        diff = value - baseline
        decayed_diff = diff * math.exp(-effective_rate * periods)

        return baseline + decayed_diff

    def _calculate_activity_factor(
        self,
        action_count: int,
        delta_seconds: float
    ) -> float:
        """
        Calculate how much activity slows decay.

        More recent activity = slower decay.
        """
        if action_count == 0:
            return 1.0  # Full decay

        # Normalize by activity window
        window = self.config.activity_window
        activity_rate = action_count / max(delta_seconds, 1) * window

        # Map to decay factor (more activity = lower factor = slower decay)
        # Asymptotic approach to activity_decay_factor as activity increases
        base = self.config.activity_decay_factor
        factor = base + (1 - base) * math.exp(-activity_rate)

        return factor

    def time_to_baseline(
        self,
        dimension: str,
        current_value: float,
        threshold: float = 0.01
    ) -> timedelta:
        """
        Calculate time for dimension to decay to near-baseline.

        Args:
            dimension: Trust dimension
            current_value: Current trust value
            threshold: Distance from baseline to consider "at baseline"

        Returns:
            Time until trust reaches baseline ± threshold
        """
        rate = self.config.decay_rates.get(dimension, 0.03)
        baseline = self.config.baseline

        diff = abs(current_value - baseline)
        if diff <= threshold:
            return timedelta(0)

        # Solve: threshold = diff * e^(-rate * periods)
        # periods = -ln(threshold / diff) / rate
        periods = -math.log(threshold / diff) / rate

        return timedelta(seconds=periods * self.config.decay_period)

    def project_decay(
        self,
        trust: Dict[str, float],
        days: int = 30,
        actions_per_day: float = 0
    ) -> List[Dict[str, float]]:
        """
        Project trust decay over time.

        Returns list of trust snapshots at daily intervals.
        """
        snapshots = [trust.copy()]
        current = trust.copy()
        now = datetime.now(timezone.utc)

        for day in range(1, days + 1):
            future = now + timedelta(days=day)
            current = self.apply_decay(
                current,
                now + timedelta(days=day-1),
                future,
                int(actions_per_day)
            )
            snapshots.append(current.copy())

        return snapshots


class TrustHistoryManager:
    """
    Manages trust history and decay for an entity.

    Tracks trust updates over time and applies decay on read.
    """

    def __init__(self, entity_id: str, config: Optional[DecayConfig] = None):
        self.entity_id = entity_id
        self.calculator = TrustDecayCalculator(config)
        self.history: List[TrustSnapshot] = []
        self._current_trust: Dict[str, float] = {
            'competence': 0.5,
            'reliability': 0.5,
            'consistency': 0.5,
            'witnesses': 0.5,
            'lineage': 0.5,
            'alignment': 0.5
        }
        self._last_update: Optional[datetime] = None
        self._action_count: int = 0

    def update_trust(
        self,
        dimension: str,
        delta: float,
        record_snapshot: bool = True
    ):
        """
        Update a trust dimension.

        Args:
            dimension: Dimension to update
            delta: Change in value (can be negative)
            record_snapshot: Whether to save to history
        """
        now = datetime.now(timezone.utc)

        # First apply any pending decay
        if self._last_update:
            self._current_trust = self.calculator.apply_decay(
                self._current_trust,
                self._last_update,
                now,
                self._action_count
            )

        # Apply update
        old_value = self._current_trust.get(dimension, 0.5)
        new_value = max(0.0, min(1.0, old_value + delta))
        self._current_trust[dimension] = new_value

        # Update state
        self._last_update = now
        self._action_count += 1

        # Record snapshot
        if record_snapshot:
            self.history.append(TrustSnapshot(
                timestamp=now.isoformat(),
                values=self._current_trust.copy(),
                action_count=self._action_count
            ))

    def get_trust(self, apply_decay: bool = True) -> Dict[str, float]:
        """
        Get current trust values.

        Args:
            apply_decay: Whether to apply time-based decay

        Returns:
            Current trust values (possibly decayed)
        """
        if not apply_decay or self._last_update is None:
            return self._current_trust.copy()

        return self.calculator.apply_decay(
            self._current_trust,
            self._last_update,
            datetime.now(timezone.utc),
            self._action_count
        )

    def get_trust_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Get weighted trust score with decay applied."""
        trust = self.get_trust(apply_decay=True)

        if weights is None:
            weights = {
                'competence': 0.25,
                'reliability': 0.20,
                'consistency': 0.15,
                'witnesses': 0.15,
                'lineage': 0.15,
                'alignment': 0.10
            }

        return sum(trust.get(dim, 0.5) * w for dim, w in weights.items())

    def record_action(self):
        """Record an action (affects decay rate)."""
        self._action_count += 1

    def to_dict(self) -> dict:
        """Serialize for storage."""
        return {
            'entity_id': self.entity_id,
            'current_trust': self._current_trust,
            'last_update': self._last_update.isoformat() if self._last_update else None,
            'action_count': self._action_count,
            'history_length': len(self.history)
        }


def demo_decay():
    """Demonstrate trust decay behavior."""
    print("Trust Decay Demo")
    print("=" * 50)

    calc = TrustDecayCalculator()

    # Start with high trust
    trust = {
        'competence': 0.9,
        'reliability': 0.85,
        'consistency': 0.8,
        'witnesses': 0.7,
        'lineage': 0.9,
        'alignment': 0.75
    }

    print(f"\nInitial trust: {trust}")

    # Project over 60 days with no activity
    projections = calc.project_decay(trust, days=60, actions_per_day=0)

    print("\nDecay over time (no activity):")
    for day in [0, 7, 14, 30, 60]:
        p = projections[day]
        avg = sum(p.values()) / len(p)
        print(f"  Day {day:2d}: avg={avg:.3f} | " +
              " ".join(f"{k[:4]}={v:.2f}" for k, v in p.items()))

    # With daily activity
    projections_active = calc.project_decay(trust, days=60, actions_per_day=5)

    print("\nDecay over time (5 actions/day):")
    for day in [0, 7, 14, 30, 60]:
        p = projections_active[day]
        avg = sum(p.values()) / len(p)
        print(f"  Day {day:2d}: avg={avg:.3f} | " +
              " ".join(f"{k[:4]}={v:.2f}" for k, v in p.items()))


if __name__ == "__main__":
    demo_decay()
