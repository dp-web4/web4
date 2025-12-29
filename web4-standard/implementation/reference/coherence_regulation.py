#!/usr/bin/env python3
"""
Coherence Regulation - Cascade Prevention

Implements regulation mechanisms to prevent coherence death spirals where
low CI leads to high ATP costs, preventing coherence maintenance, leading
to lower CI in a positive feedback loop.

Regulation Strategies:
1. Temporal Decay: CI penalties fade over time if no new issues
2. Soft Bounds: Minimum effective CI prevents total lock-out
3. Cascade Detection: Identify and intervene in coherence spirals
4. Recovery Paths: Grace periods and witness vouching for legitimate agents

Motivation:
Inspired by SAGE Session 135 frustration cascade discovery. Both systems
exhibit positive feedback loops that can lock into failure states without
active regulation. See: docs/COHERENCE_CASCADE_ANALYSIS.md
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
import math

# Import existing coherence and trust components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from mrh_rdf_implementation import GroundingEdge, GroundingContext
from coherence import coherence_index, CoherenceWeights
from trust_tensors import CIModulationConfig


# ============================================================================
# Regulation Configuration
# ============================================================================

@dataclass
class CoherenceRegulationConfig:
    """
    Configuration for coherence regulation mechanisms

    Societies can tune these parameters to balance security vs resilience:
    - High-security: Slow decay, low soft floor, strict cascade detection
    - Lenient: Fast decay, high soft floor, generous grace periods
    """
    # Temporal decay parameters
    enable_temporal_decay: bool = True
    decay_half_life_hours: float = 6.0  # Penalties halve every 6 hours

    # Soft bounds parameters
    min_effective_ci: float = 0.2  # Even very low CI can still operate
    max_atp_multiplier: float = 5.0  # Cap at 5x cost, not 10x

    # Cascade detection parameters
    cascade_detection_enabled: bool = True
    cascade_ci_threshold: float = 0.4  # Below this for N consecutive = cascade
    cascade_consecutive_count: int = 5  # How many consecutive low CIs trigger
    cascade_recovery_boost: float = 0.3  # Emergency CI boost amount

    # Grace period parameters
    grace_period_first_drop: bool = True
    grace_period_duration: timedelta = field(default_factory=lambda: timedelta(hours=2))
    grace_period_min_ci: float = 0.5  # CI floor during grace period

    # Witness vouching parameters
    witness_vouching_enabled: bool = False  # Future feature
    vouching_ci_boost: float = 0.2
    min_witnesses_for_vouching: int = 3


# ============================================================================
# Temporal Decay
# ============================================================================

def calculate_decay_factor(time_elapsed: timedelta, half_life_hours: float) -> float:
    """
    Calculate exponential decay factor

    Uses half-life decay: factor = 0.5^(t / half_life)
    - t=0: factor = 1.0 (no decay)
    - t=half_life: factor = 0.5 (half decayed)
    - t=2*half_life: factor = 0.25 (quarter remaining)

    Args:
        time_elapsed: Time since last coherence issue
        half_life_hours: Half-life for penalty decay

    Returns:
        Decay factor [0.0, 1.0]
    """
    hours = time_elapsed.total_seconds() / 3600
    return 0.5 ** (hours / half_life_hours)


def apply_temporal_decay(
    current_ci: float,
    last_issue_time: str,
    config: CoherenceRegulationConfig
) -> float:
    """
    Apply temporal decay to CI penalties

    If CI is low due to past issues but no new issues have occurred,
    the penalty gradually fades. This prevents permanent lock-in from
    temporary coherence drops.

    Args:
        current_ci: Current raw CI value
        last_issue_time: ISO8601 timestamp of last coherence issue
        config: Regulation configuration

    Returns:
        CI with decay applied
    """
    if not config.enable_temporal_decay:
        return current_ci

    if current_ci >= 0.9:
        return current_ci  # Already high, no decay needed

    # Calculate time since last issue
    last_issue = datetime.fromisoformat(last_issue_time)
    now = datetime.now()
    elapsed = now - last_issue

    # Calculate how much penalty should have decayed
    decay_factor = calculate_decay_factor(elapsed, config.decay_half_life_hours)

    # CI recovery: Move toward 1.0 as penalties decay
    penalty = 1.0 - current_ci  # How much below perfect
    decayed_penalty = penalty * decay_factor  # Penalty after decay
    recovered_ci = 1.0 - decayed_penalty

    return min(recovered_ci, 1.0)


# ============================================================================
# Soft Bounds
# ============================================================================

def apply_soft_bounds(ci: float, config: CoherenceRegulationConfig) -> float:
    """
    Apply soft floor to CI to prevent total lock-out

    Even very low coherence should allow some operation (at high cost).
    This prevents cascade where low CI → high cost → no operations → lower CI.

    Args:
        ci: Raw CI value
        config: Regulation configuration

    Returns:
        CI with soft floor applied
    """
    return max(ci, config.min_effective_ci)


def adjusted_atp_cost_regulated(
    base_cost: float,
    ci: float,
    config: CoherenceRegulationConfig
) -> float:
    """
    Calculate ATP cost with regulation (soft floor and max cap)

    Unlike the base adjusted_atp_cost() which can go to 10x, this version:
    - Applies soft floor to CI (min 0.2)
    - Caps multiplier at 5x (not 10x)
    - Prevents total lock-out while still penalizing low coherence

    Args:
        base_cost: Base ATP cost
        ci: Coherence Index
        config: Regulation configuration

    Returns:
        Adjusted ATP cost with regulation
    """
    if ci >= 0.9:
        return base_cost

    # Apply soft floor
    ci_bounded = apply_soft_bounds(ci, config)

    # Calculate multiplier with bounded CI
    multiplier = 1.0 / (ci_bounded ** 2)

    # Apply max cap
    multiplier = min(multiplier, config.max_atp_multiplier)

    return base_cost * multiplier


# ============================================================================
# Cascade Detection
# ============================================================================

@dataclass
class CoherenceCascadeDetection:
    """Results from cascade detection"""
    is_cascade: bool
    consecutive_low_ci: int
    min_ci_in_window: float
    recovery_action_recommended: str


def detect_coherence_cascade(
    entity_lct: str,
    ci_history: List[float],  # Pre-calculated CI values
    config: CoherenceRegulationConfig
) -> CoherenceCascadeDetection:
    """
    Detect if entity is in coherence death spiral

    Cascade indicators:
    - N consecutive CIs below threshold
    - Monotonic CI degradation (each lower than previous)
    - Current CI critically low

    Args:
        entity_lct: Entity LCT URI
        ci_history: List of pre-calculated CI values (chronological)
        config: Regulation configuration

    Returns:
        Cascade detection results
    """
    if not config.cascade_detection_enabled:
        return CoherenceCascadeDetection(False, 0, 1.0, "detection disabled")

    if len(ci_history) < config.cascade_consecutive_count:
        return CoherenceCascadeDetection(False, 0, 1.0, "insufficient history")

    # Get recent CIs
    cis = ci_history[-config.cascade_consecutive_count:]

    # Check for consecutive low CI
    consecutive_low = sum(1 for ci in cis if ci < config.cascade_ci_threshold)

    # Check for monotonic degradation
    is_monotonic = all(cis[i] < cis[i-1] for i in range(1, len(cis)))

    # Get minimum CI
    min_ci = min(cis)
    current_ci = cis[-1]

    # Determine if cascade
    is_cascade = (
        consecutive_low == len(cis) and  # All recent CIs low
        current_ci < config.cascade_ci_threshold and  # Currently critically low
        (is_monotonic or min_ci < 0.3)  # And getting worse or very low
    )

    if is_cascade:
        action = f"URGENT: Apply recovery boost of {config.cascade_recovery_boost}"
    elif consecutive_low >= config.cascade_consecutive_count - 1:
        action = "WARNING: Approaching cascade, monitor closely"
    else:
        action = "OK: No cascade detected"

    return CoherenceCascadeDetection(
        is_cascade=is_cascade,
        consecutive_low_ci=consecutive_low,
        min_ci_in_window=min_ci,
        recovery_action_recommended=action
    )


def apply_cascade_recovery(
    current_ci: float,
    detection: CoherenceCascadeDetection,
    config: CoherenceRegulationConfig
) -> float:
    """
    Apply emergency coherence boost if cascade detected

    Grants temporary coherence credit to prevent lock-out.
    Interpretation: "Benefit of the doubt during recovery period"

    Args:
        current_ci: Current CI value
        detection: Cascade detection results
        config: Regulation configuration

    Returns:
        CI with recovery boost if applicable
    """
    if not detection.is_cascade:
        return current_ci

    # Apply emergency boost
    boosted_ci = current_ci + config.cascade_recovery_boost

    # Ensure at least moderate coherence
    return max(boosted_ci, 0.5)


# ============================================================================
# Grace Periods
# ============================================================================

@dataclass
class GracePeriodStatus:
    """Grace period status for an entity"""
    in_grace_period: bool
    grace_started: Optional[str]  # ISO8601
    grace_expires: Optional[str]  # ISO8601
    first_drop_ci: Optional[float]
    grace_ci_floor: float


def check_grace_period(
    entity_lct: str,
    current_ci: float,
    ci_history: List[Tuple[float, str]],  # List of (ci, timestamp) tuples
    config: CoherenceRegulationConfig
) -> GracePeriodStatus:
    """
    Check if entity is in grace period after first coherence drop

    First time an entity's CI drops below threshold, grant a grace period
    with a higher effective CI floor. This allows recovery from temporary
    issues without immediate harsh penalties.

    Args:
        entity_lct: Entity LCT URI
        current_ci: Current CI value
        ci_history: List of (CI, timestamp) tuples (chronological)
        config: Regulation configuration

    Returns:
        Grace period status
    """
    if not config.grace_period_first_drop:
        return GracePeriodStatus(False, None, None, None, config.min_effective_ci)

    # Find first time CI dropped below threshold
    first_drop_idx = None
    for i, (ci, timestamp) in enumerate(ci_history):
        if ci < 0.8:  # Threshold for "drop"
            first_drop_idx = i
            break

    if first_drop_idx is None:
        # No drop yet, no grace period
        return GracePeriodStatus(False, None, None, None, config.min_effective_ci)

    # Check if still within grace period
    first_drop_ci, grace_started = ci_history[first_drop_idx]
    grace_started_dt = datetime.fromisoformat(grace_started)
    grace_expires_dt = grace_started_dt + config.grace_period_duration
    grace_expires = grace_expires_dt.isoformat()

    now = datetime.now()
    in_grace = now < grace_expires_dt

    if in_grace:
        return GracePeriodStatus(
            in_grace_period=True,
            grace_started=grace_started,
            grace_expires=grace_expires,
            first_drop_ci=first_drop_ci,
            grace_ci_floor=config.grace_period_min_ci
        )
    else:
        # Grace period expired
        return GracePeriodStatus(False, grace_started, grace_expires, None, config.min_effective_ci)


def apply_grace_period_floor(
    current_ci: float,
    grace_status: GracePeriodStatus
) -> float:
    """
    Apply grace period CI floor if applicable

    During grace period, CI is floored at a higher value to allow recovery.

    Args:
        current_ci: Current CI value
        grace_status: Grace period status

    Returns:
        CI with grace period floor if applicable
    """
    if not grace_status.in_grace_period:
        return current_ci

    return max(current_ci, grace_status.grace_ci_floor)


# ============================================================================
# Integrated Regulation Manager
# ============================================================================

class CoherenceRegulationManager:
    """
    Manages all coherence regulation mechanisms

    Integrates:
    - Temporal decay
    - Soft bounds
    - Cascade detection
    - Grace periods
    - (Future: Witness vouching)
    """

    def __init__(
        self,
        config: Optional[CoherenceRegulationConfig] = None
    ):
        self.config = config or CoherenceRegulationConfig()

    def regulate_coherence(
        self,
        entity_lct: str,
        raw_ci: float,
        ci_history: Optional[List[Tuple[float, str]]] = None,  # List of (CI, timestamp) tuples
        last_issue_time: Optional[str] = None
    ) -> Tuple[float, dict]:
        """
        Apply all regulation mechanisms to raw CI

        Args:
            entity_lct: Entity LCT URI
            raw_ci: Raw coherence index from coherence_index()
            ci_history: List of (CI, timestamp) tuples for cascade/grace detection (optional)
            last_issue_time: ISO8601 timestamp of last coherence issue (optional)

        Returns:
            (regulated_ci, metadata)
        """
        metadata = {
            'raw_ci': raw_ci,
            'regulations_applied': []
        }

        regulated_ci = raw_ci

        # 1. Temporal decay
        if last_issue_time and self.config.enable_temporal_decay:
            decayed_ci = apply_temporal_decay(regulated_ci, last_issue_time, self.config)
            if decayed_ci != regulated_ci:
                metadata['regulations_applied'].append('temporal_decay')
                metadata['decay_delta'] = decayed_ci - regulated_ci
                regulated_ci = decayed_ci

        # 2. Grace period (if history provided)
        if ci_history:
            grace_status = check_grace_period(
                entity_lct, regulated_ci, ci_history, self.config
            )
            if grace_status.in_grace_period:
                grace_ci = apply_grace_period_floor(regulated_ci, grace_status)
                if grace_ci != regulated_ci:
                    metadata['regulations_applied'].append('grace_period')
                    metadata['grace_expires'] = grace_status.grace_expires
                    regulated_ci = grace_ci

        # 3. Cascade detection (if history provided)
        if ci_history:
            ci_values = [ci for ci, _ in ci_history]
            cascade_detection = detect_coherence_cascade(
                entity_lct, ci_values, self.config
            )
            metadata['cascade_detection'] = {
                'is_cascade': cascade_detection.is_cascade,
                'consecutive_low': cascade_detection.consecutive_low_ci,
                'action': cascade_detection.recovery_action_recommended
            }

            if cascade_detection.is_cascade:
                recovered_ci = apply_cascade_recovery(regulated_ci, cascade_detection, self.config)
                if recovered_ci != regulated_ci:
                    metadata['regulations_applied'].append('cascade_recovery')
                    metadata['cascade_boost'] = recovered_ci - regulated_ci
                    regulated_ci = recovered_ci

        # 4. Soft bounds (always apply as final step)
        bounded_ci = apply_soft_bounds(regulated_ci, self.config)
        if bounded_ci != regulated_ci:
            metadata['regulations_applied'].append('soft_bounds')
            metadata['soft_floor'] = self.config.min_effective_ci
            regulated_ci = bounded_ci

        metadata['final_ci'] = regulated_ci

        return (regulated_ci, metadata)

    def calculate_regulated_atp_cost(
        self,
        base_cost: float,
        regulated_ci: float
    ) -> float:
        """
        Calculate ATP cost using regulated CI

        Args:
            base_cost: Base ATP cost
            regulated_ci: CI after regulation

        Returns:
            ATP cost with regulation
        """
        return adjusted_atp_cost_regulated(base_cost, regulated_ci, self.config)
