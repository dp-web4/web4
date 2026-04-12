#!/usr/bin/env python3
"""
Temporal Trust Dynamics

How trust evolves through TIME in Web4 — not just "trust goes up or down"
but the rich temporal structure: memory effects, forgetting curves, seasonal
patterns, regime changes, information shocks, and trust inertia.

The Problem:
  Current Web4 trust models treat time as a simple counter.
  Real trust has temporal STRUCTURE:
    - Recent events matter more (exponential decay of memory)
    - Some events create permanent shifts (regime changes)
    - Trust has inertia (doesn't change instantly)
    - Seasonal patterns exist (activity cycles)
    - Information shocks propagate with delay
    - Old trust evidence should decay but not vanish entirely

This implementation models trust as a temporal process, not just a score.

Sections:
  §1  Exponential Forgetting — Ebbinghaus curve applied to trust evidence
  §2  Weighted Memory — Recent events matter more, with configurable decay
  §3  Trust Inertia — Resistance to change proportional to trust age
  §4  Seasonal Trust Patterns — Cyclical activity and trust fluctuations
  §5  Regime Change Detection — Identify structural breaks in trust history
  §6  Information Shock Propagation — How sudden events ripple through networks
  §7  Trust Half-Life — Different dimensions decay at different rates
  §8  Temporal Aggregation — Combining evidence across time windows
  §9  Prediction & Forecasting — Extrapolate future trust from history
  §10 Staleness Detection — Identify entities with outdated trust evidence
  §11 Temporal Attack Vectors — Time-based manipulation strategies
  §12 Full Temporal Simulation — Integration of all temporal effects
"""

import math
import random
import statistics
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  §1. EXPONENTIAL FORGETTING
# ═══════════════════════════════════════════════════════════════

@dataclass
class TrustEvidence:
    """A single piece of trust evidence with timestamp."""
    timestamp: float  # Time of observation
    dimension: str    # 'talent', 'training', 'temperament'
    value: float      # Observed trust quality [0, 1]
    weight: float = 1.0  # Base importance
    source_trust: float = 0.5  # Trust in the source of this evidence

    def decayed_weight(self, current_time: float, half_life: float) -> float:
        """Weight after exponential decay."""
        age = current_time - self.timestamp
        if age < 0:
            return 0.0
        decay = math.exp(-math.log(2) * age / half_life)
        return self.weight * self.source_trust * decay


class EbbinghausForgetting:
    """
    Ebbinghaus forgetting curve applied to trust evidence.

    R(t) = e^(-t/S) where:
      R = retention (how much trust evidence is remembered)
      t = time since observation
      S = stability (how well-established the evidence is)

    Key insight: REPEATED observations increase S (stability).
    An entity witnessed 10 times has higher S than one witnessed once.
    """

    def __init__(self, base_stability: float = 10.0,
                 repetition_boost: float = 1.5):
        self.base_stability = base_stability
        self.repetition_boost = repetition_boost

    def retention(self, time_elapsed: float, n_observations: int) -> float:
        """How much of the trust evidence is retained."""
        stability = self.base_stability * (self.repetition_boost ** (n_observations - 1))
        return math.exp(-time_elapsed / stability)

    def effective_trust(self, observations: List[Tuple[float, float]],
                       current_time: float) -> float:
        """
        Compute effective trust from a series of observations.

        observations: [(timestamp, trust_value), ...]
        current_time: current time

        Each observation's contribution is weighted by its retention.
        """
        if not observations:
            return 0.1  # Default trust

        n_obs = len(observations)
        weighted_sum = 0.0
        weight_sum = 0.0

        for timestamp, value in observations:
            elapsed = current_time - timestamp
            if elapsed < 0:
                continue
            r = self.retention(elapsed, n_obs)
            weighted_sum += value * r
            weight_sum += r

        if weight_sum < 1e-10:
            return 0.1  # All evidence forgotten

        return weighted_sum / weight_sum


# ═══════════════════════════════════════════════════════════════
#  §2. WEIGHTED MEMORY
# ═══════════════════════════════════════════════════════════════

class WeightedMemory:
    """
    Trust memory with configurable recency weighting.

    Different weighting schemes:
      - Exponential: w(t) = λ^(T-t)  — classic exponential decay
      - Linear: w(t) = max(0, 1 - (T-t)/W)  — linear window
      - Sliding: fixed window of last N observations
      - Adaptive: window size adapts to trust volatility
    """

    @staticmethod
    def exponential_weights(timestamps: List[float], current_time: float,
                          decay_rate: float = 0.1) -> List[float]:
        """Exponential recency weights."""
        weights = []
        for t in timestamps:
            age = current_time - t
            weights.append(math.exp(-decay_rate * age))
        return weights

    @staticmethod
    def linear_weights(timestamps: List[float], current_time: float,
                      window: float = 100.0) -> List[float]:
        """Linear recency weights (zero outside window)."""
        weights = []
        for t in timestamps:
            age = current_time - t
            w = max(0.0, 1.0 - age / window)
            weights.append(w)
        return weights

    @staticmethod
    def sliding_window(values: List[float], window_size: int) -> List[float]:
        """Simple sliding window: only last N values."""
        return values[-window_size:] if len(values) > window_size else values

    @staticmethod
    def adaptive_window(values: List[float], timestamps: List[float],
                       current_time: float,
                       volatility_threshold: float = 0.1) -> Tuple[List[float], int]:
        """
        Adaptive window: shrinks when trust is volatile, expands when stable.

        Returns (weighted_values, effective_window_size).
        """
        if len(values) < 3:
            return values, len(values)

        # Compute recent volatility
        recent = values[-min(20, len(values)):]
        if len(recent) < 2:
            return values, len(values)

        volatility = statistics.stdev(recent)

        # High volatility → small window (recent changes matter more)
        # Low volatility → large window (history is informative)
        if volatility > volatility_threshold:
            window = max(5, int(10 / (1 + volatility * 10)))
        else:
            window = min(len(values), int(50 / (1 + volatility)))

        windowed = values[-window:]
        return windowed, window

    @staticmethod
    def weighted_average(values: List[float], weights: List[float]) -> float:
        """Compute weighted average."""
        if not values or not weights:
            return 0.0
        total_weight = sum(weights[:len(values)])
        if total_weight < 1e-10:
            return 0.0
        return sum(v * w for v, w in zip(values, weights)) / total_weight


# ═══════════════════════════════════════════════════════════════
#  §3. TRUST INERTIA
# ═══════════════════════════════════════════════════════════════

class TrustInertia:
    """
    Trust resists change proportional to its age and strength.

    Physical analogy: trust has mass (accumulated evidence).
    Changing trust requires force (new evidence) proportional to mass.

    Inertia formula:
      ΔT_effective = ΔT_raw / (1 + α * mass)
      where mass = n_observations * current_trust * age_factor

    This means:
      - New entities (low mass) change trust quickly
      - Established entities (high mass) change trust slowly
      - High-trust entities are harder to destabilize
      - Low-trust entities are harder to rehabilitate (but less so)
    """

    def __init__(self, alpha: float = 0.1, age_weight: float = 0.01):
        self.alpha = alpha
        self.age_weight = age_weight

    def compute_mass(self, n_observations: int, current_trust: float,
                    age: float) -> float:
        """Compute trust inertia mass."""
        age_factor = 1 + self.age_weight * age
        return n_observations * current_trust * age_factor

    def apply_inertia(self, current_trust: float, raw_delta: float,
                     n_observations: int, age: float) -> float:
        """Apply inertia to a trust change."""
        mass = self.compute_mass(n_observations, current_trust, age)
        effective_delta = raw_delta / (1 + self.alpha * mass)
        new_trust = current_trust + effective_delta
        return max(0.0, min(1.0, new_trust))

    def required_evidence(self, current_trust: float, target_trust: float,
                         n_observations: int, age: float) -> int:
        """How many observations needed to shift trust by a given amount."""
        mass = self.compute_mass(n_observations, current_trust, age)
        raw_delta = target_trust - current_trust
        if abs(raw_delta) < 0.001:
            return 0

        # Each observation contributes ~0.02 raw delta
        per_obs_delta = 0.02
        effective_per_obs = per_obs_delta / (1 + self.alpha * mass)

        if abs(effective_per_obs) < 1e-10:
            return 999999

        return max(1, int(abs(raw_delta) / abs(effective_per_obs)))


# ═══════════════════════════════════════════════════════════════
#  §4. SEASONAL TRUST PATTERNS
# ═══════════════════════════════════════════════════════════════

class SeasonalTrust:
    """
    Model cyclical trust patterns.

    Real-world trust has seasonal components:
      - Daily cycles: activity peaks/troughs
      - Weekly cycles: weekday vs weekend behavior
      - Project cycles: sprint beginnings vs endings
      - Annual cycles: quarterly reviews, budget periods

    We model this as: T(t) = T_base + A * sin(2πt/P + φ) + ε
    where A = amplitude, P = period, φ = phase, ε = noise
    """

    @staticmethod
    def generate_seasonal(n_steps: int = 365,
                        base_trust: float = 0.6,
                        amplitude: float = 0.1,
                        period: float = 30.0,  # Monthly cycle
                        noise: float = 0.02) -> List[float]:
        """Generate trust time series with seasonal component."""
        values = []
        for t in range(n_steps):
            seasonal = amplitude * math.sin(2 * math.pi * t / period)
            noise_val = random.gauss(0, noise)
            trust = base_trust + seasonal + noise_val
            trust = max(0.0, min(1.0, trust))
            values.append(trust)
        return values

    @staticmethod
    def detect_seasonality(values: List[float], max_period: int = 100) -> Dict:
        """
        Detect seasonal patterns using autocorrelation.

        Returns detected period and strength.
        """
        n = len(values)
        if n < max_period * 2:
            max_period = n // 2

        mean = statistics.mean(values)
        var = sum((v - mean) ** 2 for v in values) / n
        if var < 1e-10:
            return {'seasonal': False, 'period': 0, 'strength': 0}

        # Compute autocorrelation for each lag
        autocorr = []
        for lag in range(1, max_period + 1):
            corr = sum((values[t] - mean) * (values[t + lag] - mean)
                      for t in range(n - lag)) / ((n - lag) * var)
            autocorr.append((lag, corr))

        # Find peak autocorrelation (excluding lag 0)
        if not autocorr:
            return {'seasonal': False, 'period': 0, 'strength': 0}

        best_lag, best_corr = max(autocorr, key=lambda x: x[1])

        return {
            'seasonal': best_corr > 0.3,  # Significant seasonality
            'period': best_lag,
            'strength': best_corr,
            'top_3': sorted(autocorr, key=lambda x: -x[1])[:3],
        }

    @staticmethod
    def deseasonalize(values: List[float], period: int) -> List[float]:
        """Remove seasonal component to reveal trend.

        Uses classical decomposition: compute per-position seasonal average
        and subtract it from each value.
        """
        if period <= 0 or period >= len(values):
            return values

        # Compute seasonal component: average for each position in the period
        seasonal = [0.0] * period
        counts = [0] * period
        for i, v in enumerate(values):
            pos = i % period
            seasonal[pos] += v
            counts[pos] += 1
        for pos in range(period):
            if counts[pos] > 0:
                seasonal[pos] /= counts[pos]

        # Center the seasonal component (so it sums to zero)
        seasonal_mean = statistics.mean(seasonal)
        seasonal = [s - seasonal_mean for s in seasonal]

        # Subtract seasonal component
        overall_mean = statistics.mean(values)
        deseasonalized = []
        for i, v in enumerate(values):
            pos = i % period
            deseasonalized.append(v - seasonal[pos])
        return deseasonalized


# ═══════════════════════════════════════════════════════════════
#  §5. REGIME CHANGE DETECTION
# ═══════════════════════════════════════════════════════════════

class RegimeChangeDetector:
    """
    Detect structural breaks in trust history.

    A regime change is a fundamental shift in trust behavior:
      - Entity gets compromised → trust should drop permanently
      - Entity gets certified → trust should jump permanently
      - Federation policy change → all members affected

    Detection methods:
      1. CUSUM (Cumulative Sum) — detects mean shifts
      2. Change-point detection — finds breakpoints
      3. Sliding window comparison — compares before/after distributions
    """

    @staticmethod
    def cusum_detect(values: List[float], threshold: float = 3.0,
                    drift: float = 0.5) -> List[int]:
        """
        CUSUM (Cumulative Sum) change detection.

        Detects upward and downward shifts from the running mean.
        Returns list of change-point indices.
        """
        if len(values) < 10:
            return []

        mean = statistics.mean(values[:min(20, len(values))])
        std = statistics.stdev(values[:min(20, len(values))]) if len(values) > 1 else 1.0
        if std < 1e-10:
            std = 0.01

        s_pos = 0.0
        s_neg = 0.0
        change_points = []

        for i, v in enumerate(values):
            z = (v - mean) / std
            s_pos = max(0, s_pos + z - drift)
            s_neg = max(0, s_neg - z - drift)

            if s_pos > threshold or s_neg > threshold:
                change_points.append(i)
                s_pos = 0.0
                s_neg = 0.0
                # Update running mean after change
                if i + 1 < len(values):
                    remaining = values[i + 1:min(i + 21, len(values))]
                    if remaining:
                        mean = statistics.mean(remaining)

        return change_points

    @staticmethod
    def sliding_window_detect(values: List[float],
                             window_size: int = 20,
                             significance: float = 0.1) -> List[Dict]:
        """
        Detect regime changes by comparing adjacent windows.

        Returns list of {index, before_mean, after_mean, shift_magnitude}.
        """
        if len(values) < 2 * window_size:
            return []

        changes = []
        for i in range(window_size, len(values) - window_size):
            before = values[i - window_size:i]
            after = values[i:i + window_size]

            before_mean = statistics.mean(before)
            after_mean = statistics.mean(after)
            shift = abs(after_mean - before_mean)

            # Pooled standard deviation
            before_std = statistics.stdev(before) if len(before) > 1 else 0.01
            after_std = statistics.stdev(after) if len(after) > 1 else 0.01
            pooled_std = math.sqrt((before_std ** 2 + after_std ** 2) / 2)

            if pooled_std > 0 and shift / pooled_std > 2.0:  # 2 sigma shift
                # Only add if not too close to previous change
                if not changes or i - changes[-1]['index'] > window_size:
                    changes.append({
                        'index': i,
                        'before_mean': before_mean,
                        'after_mean': after_mean,
                        'shift_magnitude': shift,
                        'direction': 'up' if after_mean > before_mean else 'down',
                    })

        return changes


# ═══════════════════════════════════════════════════════════════
#  §6. INFORMATION SHOCK PROPAGATION
# ═══════════════════════════════════════════════════════════════

class InformationShock:
    """
    Model how sudden trust events propagate through a network.

    When entity E has a trust event (compromise, certification, etc.),
    the information propagates to connected entities with delay:
      - Direct witnesses: learn immediately
      - 2-hop neighbors: learn after ~1 time step
      - n-hop neighbors: learn after ~n time steps

    The propagation follows an SIR-like model:
      - Susceptible: hasn't heard the news
      - Informed: knows the news, updating trust
      - Resolved: has fully adjusted trust
    """

    @dataclass
    class Node:
        trust: float
        state: str = 'susceptible'  # susceptible, informed, resolved
        inform_time: int = -1
        neighbors: List[int] = field(default_factory=list)

    @staticmethod
    def simulate_shock(n_nodes: int = 100,
                      avg_degree: int = 6,
                      shock_magnitude: float = -0.3,
                      propagation_speed: float = 0.5) -> Dict:
        """
        Simulate an information shock and measure propagation.

        shock_magnitude: how much trust changes (-0.3 = drop by 0.3)
        """
        # Build small-world network
        nodes = []
        for i in range(n_nodes):
            n = InformationShock.Node(trust=0.6 + random.gauss(0, 0.1))
            n.trust = max(0.1, min(1.0, n.trust))
            nodes.append(n)

        # Create connections (ring + random shortcuts)
        for i in range(n_nodes):
            for j in range(1, avg_degree // 2 + 1):
                neighbor = (i + j) % n_nodes
                nodes[i].neighbors.append(neighbor)
                nodes[neighbor].neighbors.append(i)
            # Random shortcut
            if random.random() < 0.1:
                shortcut = random.randint(0, n_nodes - 1)
                if shortcut != i:
                    nodes[i].neighbors.append(shortcut)
                    nodes[shortcut].neighbors.append(i)

        # Deduplicate neighbors
        for n in nodes:
            n.neighbors = list(set(n.neighbors))

        # Apply shock to node 0
        nodes[0].trust = max(0.0, nodes[0].trust + shock_magnitude)
        nodes[0].state = 'informed'
        nodes[0].inform_time = 0

        # Propagate
        informed_trajectory = [1]
        trust_trajectory = [statistics.mean(n.trust for n in nodes)]

        for step in range(1, 50):
            newly_informed = []

            for i, node in enumerate(nodes):
                if node.state == 'informed':
                    # Inform neighbors
                    for j in node.neighbors:
                        if nodes[j].state == 'susceptible':
                            if random.random() < propagation_speed:
                                newly_informed.append(j)

                    # Transition to resolved after 3 steps
                    if step - node.inform_time >= 3:
                        node.state = 'resolved'

            # Apply informed state
            for j in newly_informed:
                if nodes[j].state == 'susceptible':
                    nodes[j].state = 'informed'
                    nodes[j].inform_time = step
                    # Trust adjustment (dampened by distance)
                    dampening = 0.5  # Each hop halves the impact
                    nodes[j].trust = max(0.0, nodes[j].trust + shock_magnitude * dampening)

            informed_count = sum(1 for n in nodes if n.state in ('informed', 'resolved'))
            informed_trajectory.append(informed_count)
            trust_trajectory.append(statistics.mean(n.trust for n in nodes))

        # Measure propagation metrics
        final_informed = sum(1 for n in nodes if n.state in ('informed', 'resolved'))
        trust_drop = trust_trajectory[0] - min(trust_trajectory)

        return {
            'informed_trajectory': informed_trajectory,
            'trust_trajectory': trust_trajectory,
            'final_informed_fraction': final_informed / n_nodes,
            'peak_trust_drop': trust_drop,
            'propagation_speed': next(
                (t for t, c in enumerate(informed_trajectory) if c > n_nodes * 0.5), 50
            ),
            'recovery': trust_trajectory[-1] > trust_trajectory[0] - 0.05,
        }


# ═══════════════════════════════════════════════════════════════
#  §7. TRUST HALF-LIFE
# ═══════════════════════════════════════════════════════════════

class TrustHalfLife:
    """
    Different trust dimensions decay at different rates.

    Web4 T3 dimensions:
      - Talent: decays slowly (skills persist) — half-life ~365 time units
      - Training: decays moderately (knowledge fades) — half-life ~180 time units
      - Temperament: decays quickly (behavior is recent) — half-life ~30 time units

    V3 dimensions:
      - Valuation: decays quickly (market conditions change) — half-life ~14
      - Veracity: decays slowly (truth record persists) — half-life ~365
      - Validity: decays moderately (certifications expire) — half-life ~90
    """

    HALF_LIVES = {
        'talent': 365.0,
        'training': 180.0,
        'temperament': 30.0,
        'valuation': 14.0,
        'veracity': 365.0,
        'validity': 90.0,
    }

    @staticmethod
    def decay(initial_trust: float, elapsed: float, dimension: str) -> float:
        """Apply dimension-specific decay."""
        half_life = TrustHalfLife.HALF_LIVES.get(dimension, 90.0)
        decay_factor = math.exp(-math.log(2) * elapsed / half_life)
        # Trust decays toward base level (0.1), not zero
        base = 0.1
        return base + (initial_trust - base) * decay_factor

    @staticmethod
    def composite_decay(t3: Dict[str, float], elapsed: float,
                       weights: Dict[str, float] = None) -> float:
        """Compute composite trust after dimension-specific decay."""
        if weights is None:
            weights = {'talent': 0.4, 'training': 0.35, 'temperament': 0.25}

        composite = 0.0
        for dim, weight in weights.items():
            if dim in t3:
                decayed = TrustHalfLife.decay(t3[dim], elapsed, dim)
                composite += weight * decayed

        return composite

    @staticmethod
    def time_to_threshold(initial_trust: float, threshold: float,
                         dimension: str) -> float:
        """How long until trust drops below threshold."""
        half_life = TrustHalfLife.HALF_LIVES.get(dimension, 90.0)
        base = 0.1

        if initial_trust <= threshold:
            return 0.0

        if threshold <= base:
            return float('inf')  # Never reaches below base

        # Solve: base + (initial - base) * exp(-ln2 * t / hl) = threshold
        # exp(-ln2 * t / hl) = (threshold - base) / (initial - base)
        ratio = (threshold - base) / (initial_trust - base)
        if ratio <= 0:
            return float('inf')

        return -half_life * math.log(ratio) / math.log(2)


# ═══════════════════════════════════════════════════════════════
#  §8. TEMPORAL AGGREGATION
# ═══════════════════════════════════════════════════════════════

class TemporalAggregation:
    """
    Combine trust evidence across different time windows.

    Challenge: How to combine a strong evidence from 100 days ago
    with weak evidence from today?

    Methods:
      - Simple average (ignores time)
      - Recency-weighted average
      - Bayesian update (each observation updates prior)
      - Maximum likelihood over sliding windows
    """

    @staticmethod
    def bayesian_update(prior: float, observations: List[Tuple[float, float]],
                       current_time: float, half_life: float = 50.0) -> float:
        """
        Bayesian trust update with temporal decay.

        prior: initial trust estimate
        observations: [(timestamp, quality), ...]
        current_time: current time
        half_life: how quickly old observations lose weight

        Uses beta-distribution model:
          trust ~ Beta(α, β)
          observation of quality q → α += q * weight, β += (1-q) * weight
        """
        alpha = prior * 10  # Prior strength
        beta = (1 - prior) * 10

        for timestamp, quality in observations:
            elapsed = current_time - timestamp
            weight = math.exp(-math.log(2) * elapsed / half_life)
            alpha += quality * weight
            beta += (1 - quality) * weight

        return alpha / (alpha + beta)

    @staticmethod
    def sliding_window_aggregate(observations: List[Tuple[float, float]],
                                current_time: float,
                                windows: List[float] = None) -> Dict:
        """
        Multi-scale temporal aggregation.

        Compute trust in multiple time windows and combine.
        Short-term trust is weighted higher for volatile dimensions.
        Long-term trust is weighted higher for stable dimensions.
        """
        if windows is None:
            windows = [7.0, 30.0, 90.0, 365.0]  # 1w, 1m, 3m, 1y

        window_trusts = {}
        for w in windows:
            relevant = [(t, q) for t, q in observations
                       if current_time - t <= w]
            if relevant:
                window_trusts[w] = statistics.mean(q for _, q in relevant)
            else:
                window_trusts[w] = None

        # Combine: weighted by 1/window_size (shorter windows weight more)
        valid = [(w, t) for w, t in window_trusts.items() if t is not None]
        if not valid:
            return {'aggregate': 0.1, 'windows': window_trusts}

        weight_sum = sum(1.0 / w for w, _ in valid)
        aggregate = sum(t / w for w, t in valid) / weight_sum

        return {
            'aggregate': aggregate,
            'windows': window_trusts,
            'n_valid_windows': len(valid),
        }


# ═══════════════════════════════════════════════════════════════
#  §9. PREDICTION & FORECASTING
# ═══════════════════════════════════════════════════════════════

class TrustForecast:
    """
    Extrapolate future trust from historical patterns.

    Methods:
      - Linear extrapolation (trend continuation)
      - Exponential smoothing (Holt-Winters)
      - Mean reversion (trust gravitates toward equilibrium)
    """

    @staticmethod
    def linear_extrapolation(history: List[float],
                            forecast_steps: int = 30) -> List[float]:
        """Simple linear trend extrapolation."""
        if len(history) < 2:
            return [history[-1] if history else 0.5] * forecast_steps

        # Fit linear trend using last 30 points
        recent = history[-min(30, len(history)):]
        n = len(recent)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(recent)

        num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(recent))
        den = sum((i - x_mean) ** 2 for i in range(n))

        slope = num / den if den > 0 else 0
        intercept = y_mean - slope * x_mean

        forecast = []
        for t in range(forecast_steps):
            val = intercept + slope * (n + t)
            val = max(0.0, min(1.0, val))  # Clip to [0, 1]
            forecast.append(val)

        return forecast

    @staticmethod
    def exponential_smoothing(history: List[float],
                             alpha: float = 0.3,
                             forecast_steps: int = 30) -> List[float]:
        """Simple exponential smoothing forecast."""
        if not history:
            return [0.5] * forecast_steps

        # Compute smoothed value
        smoothed = history[0]
        for v in history[1:]:
            smoothed = alpha * v + (1 - alpha) * smoothed

        # Forecast: constant at smoothed level
        return [max(0.0, min(1.0, smoothed))] * forecast_steps

    @staticmethod
    def mean_reversion(history: List[float],
                      equilibrium: float = 0.5,
                      reversion_speed: float = 0.05,
                      forecast_steps: int = 30) -> List[float]:
        """Forecast trust reverting toward equilibrium."""
        current = history[-1] if history else 0.5
        forecast = []

        for _ in range(forecast_steps):
            delta = reversion_speed * (equilibrium - current)
            current = current + delta
            current = max(0.0, min(1.0, current))
            forecast.append(current)

        return forecast


# ═══════════════════════════════════════════════════════════════
#  §10. STALENESS DETECTION
# ═══════════════════════════════════════════════════════════════

class StalenessDetector:
    """
    Identify entities with outdated trust evidence.

    Trust is only as good as its evidence. An entity observed 365 days ago
    has stale trust that should be flagged.

    Staleness levels:
      - FRESH: last observation within 1 half-life
      - AGING: 1-2 half-lives since last observation
      - STALE: 2-3 half-lives
      - EXPIRED: > 3 half-lives
    """

    class Staleness(Enum):
        FRESH = "fresh"
        AGING = "aging"
        STALE = "stale"
        EXPIRED = "expired"

    @staticmethod
    def classify(last_observation_time: float, current_time: float,
                half_life: float = 90.0) -> 'StalenessDetector.Staleness':
        """Classify staleness of trust evidence."""
        age = current_time - last_observation_time
        half_lives = age / half_life

        if half_lives <= 1:
            return StalenessDetector.Staleness.FRESH
        elif half_lives <= 2:
            return StalenessDetector.Staleness.AGING
        elif half_lives <= 3:
            return StalenessDetector.Staleness.STALE
        else:
            return StalenessDetector.Staleness.EXPIRED

    @staticmethod
    def confidence_discount(staleness: 'StalenessDetector.Staleness') -> float:
        """How much to discount trust based on staleness."""
        discounts = {
            StalenessDetector.Staleness.FRESH: 1.0,
            StalenessDetector.Staleness.AGING: 0.8,
            StalenessDetector.Staleness.STALE: 0.5,
            StalenessDetector.Staleness.EXPIRED: 0.2,
        }
        return discounts[staleness]

    @staticmethod
    def audit_entities(entities: List[Dict], current_time: float,
                      half_life: float = 90.0) -> Dict:
        """
        Audit a set of entities for staleness.

        entities: [{'id': str, 'last_observed': float, 'trust': float}, ...]
        """
        results = {s.value: [] for s in StalenessDetector.Staleness}

        for entity in entities:
            staleness = StalenessDetector.classify(
                entity['last_observed'], current_time, half_life
            )
            results[staleness.value].append(entity['id'])

        return {
            'classifications': results,
            'fresh_count': len(results['fresh']),
            'stale_count': len(results['stale']) + len(results['expired']),
            'staleness_ratio': (len(results['stale']) + len(results['expired'])) / len(entities) if entities else 0,
        }


# ═══════════════════════════════════════════════════════════════
#  §11. TEMPORAL ATTACK VECTORS
# ═══════════════════════════════════════════════════════════════

class TemporalAttacks:
    """
    Time-based manipulation strategies against trust systems.

    Attack vectors:
      1. Slow poisoning: gradually shift trust over many steps
      2. Trust bombing: sudden burst of positive evidence
      3. Time-warp: exploit staleness by waiting then acting
      4. Seasonal exploitation: attack during low-activity periods
      5. Evidence flooding: overwhelm recent memory with new data
    """

    @staticmethod
    def slow_poisoning(n_steps: int = 200,
                      poison_rate: float = 0.005) -> Dict:
        """
        Gradually shift trust with barely-detectable changes.

        Each step: trust += small positive delta (below detection threshold)
        Over time: trust inflated significantly.
        """
        trust = 0.3  # Start low
        trajectory = [trust]
        detector = RegimeChangeDetector()

        for _ in range(n_steps):
            # Small positive bias each step
            trust += poison_rate + random.gauss(0, 0.01)
            trust = max(0.0, min(1.0, trust))
            trajectory.append(trust)

        # Check if CUSUM detects the poisoning
        changes = detector.cusum_detect(trajectory, threshold=3.0)

        return {
            'initial_trust': trajectory[0],
            'final_trust': trajectory[-1],
            'trust_inflation': trajectory[-1] - trajectory[0],
            'changes_detected': len(changes),
            'detected': len(changes) > 0,
            'first_detection': changes[0] if changes else n_steps,
        }

    @staticmethod
    def trust_bombing(base_trust: float = 0.3,
                     bomb_size: int = 50,
                     bomb_quality: float = 0.95) -> Dict:
        """
        Sudden burst of high-quality evidence to inflate trust.

        Attack: create many positive observations in a short time.
        Defense: inertia should limit effectiveness.
        """
        memory = EbbinghausForgetting(base_stability=10.0)
        inertia = TrustInertia(alpha=0.1)

        # Normal history: 100 moderate observations
        normal_observations = [(t, 0.5 + random.gauss(0, 0.1))
                              for t in range(100)]

        trust_before = memory.effective_trust(normal_observations, 100)

        # Bomb: 50 high-quality observations at time 100-105
        bomb_observations = normal_observations + [
            (100 + i * 0.1, bomb_quality) for i in range(bomb_size)
        ]

        trust_after_bomb = memory.effective_trust(bomb_observations, 105)

        # With inertia
        trust_with_inertia = inertia.apply_inertia(
            trust_before,
            trust_after_bomb - trust_before,
            len(normal_observations),
            age=100
        )

        return {
            'trust_before': trust_before,
            'trust_after_bomb_no_inertia': trust_after_bomb,
            'trust_after_bomb_with_inertia': trust_with_inertia,
            'bomb_effectiveness_no_inertia': trust_after_bomb - trust_before,
            'bomb_effectiveness_with_inertia': trust_with_inertia - trust_before,
            'inertia_dampening': 1 - (trust_with_inertia - trust_before) / max(0.001, trust_after_bomb - trust_before),
        }

    @staticmethod
    def staleness_exploit(trust: float = 0.8,
                         wait_time: float = 300.0,
                         half_life: float = 90.0) -> Dict:
        """
        Wait until trust evidence is stale, then act with outdated reputation.

        Attack: entity builds trust, goes dormant, then acts maliciously
        while still showing high trust to those who haven't updated.
        """
        # Trust decays during waiting period
        decayed_trust = TrustHalfLife.decay(trust, wait_time, 'temperament')

        # Staleness classification
        staleness = StalenessDetector.classify(0, wait_time, half_life)
        discount = StalenessDetector.confidence_discount(staleness)

        # What observers see
        naive_trust = trust  # Observer hasn't applied decay
        informed_trust = decayed_trust  # Observer applies decay
        cautious_trust = trust * discount  # Observer applies staleness discount

        return {
            'original_trust': trust,
            'wait_time': wait_time,
            'decayed_trust': decayed_trust,
            'staleness': staleness.value,
            'naive_trust': naive_trust,
            'informed_trust': informed_trust,
            'cautious_trust': cautious_trust,
            'exploit_gap': naive_trust - cautious_trust,
            'defense_effective': cautious_trust < 0.5,
        }


# ═══════════════════════════════════════════════════════════════
#  §12. FULL TEMPORAL SIMULATION
# ═══════════════════════════════════════════════════════════════

class TemporalSimulation:
    """
    Full integration of all temporal effects on trust.

    Combines: forgetting, inertia, seasonality, shocks, and decay
    to model realistic trust evolution.
    """

    @staticmethod
    def full_simulation(n_entities: int = 50,
                       n_steps: int = 365,
                       shock_step: int = 180,
                       seasonal_period: float = 30.0) -> Dict:
        """Run full temporal simulation with all effects."""
        random.seed(42)

        # Initialize entities
        entities = []
        for i in range(n_entities):
            entities.append({
                'trust': 0.4 + random.gauss(0, 0.15),
                'observations': 5 + random.randint(0, 20),
                'age': random.randint(10, 100),
                'last_observed': 0,
            })
            entities[-1]['trust'] = max(0.1, min(0.9, entities[-1]['trust']))

        trust_trajectories = [[] for _ in range(n_entities)]
        avg_trust_trajectory = []
        gini_trajectory = []

        memory = EbbinghausForgetting()
        inertia_model = TrustInertia(alpha=0.05)

        for step in range(n_steps):
            trusts = []

            for i, entity in enumerate(entities):
                # Seasonal component
                seasonal = 0.05 * math.sin(2 * math.pi * step / seasonal_period)

                # Random action quality
                quality = 0.6 + seasonal + random.gauss(0, 0.1)
                quality = max(0.0, min(1.0, quality))

                # Information shock at shock_step
                if shock_step <= step < shock_step + 10 and i < 25:
                    quality = 0.0  # Compromised entities — sustained shock
                    if step == shock_step:
                        entity['trust'] = max(0.0, entity['trust'] - 0.3)  # Immediate drop

                # Raw trust change
                raw_delta = 0.02 * (quality - 0.5)

                # Apply inertia
                new_trust = inertia_model.apply_inertia(
                    entity['trust'], raw_delta,
                    entity['observations'], entity['age']
                )

                # Apply dimension-specific decay (using temperament half-life for simplicity)
                decay_factor = math.exp(-math.log(2) / 30.0)  # ~30 step half-life for temp
                new_trust = 0.1 + (new_trust - 0.1) * decay_factor

                # Regrowth from quality actions
                new_trust = new_trust + 0.01 * quality

                entity['trust'] = max(0.0, min(1.0, new_trust))
                entity['observations'] += 1
                entity['age'] += 1
                entity['last_observed'] = step

                trust_trajectories[i].append(entity['trust'])
                trusts.append(entity['trust'])

            avg_trust_trajectory.append(statistics.mean(trusts))
            gini_trajectory.append(
                sum(abs(ti - tj) for ti in trusts for tj in trusts) /
                (2 * len(trusts) * len(trusts) * statistics.mean(trusts))
                if statistics.mean(trusts) > 0 else 0
            )

        # Detect regime changes in average trust
        changes = RegimeChangeDetector.cusum_detect(avg_trust_trajectory)

        # Detect seasonality
        seasonality = SeasonalTrust.detect_seasonality(avg_trust_trajectory)

        return {
            'avg_trust_trajectory': avg_trust_trajectory,
            'gini_trajectory': gini_trajectory,
            'final_avg_trust': avg_trust_trajectory[-1],
            'final_gini': gini_trajectory[-1],
            'regime_changes_detected': len(changes),
            'regime_change_steps': changes,
            'seasonality_detected': seasonality['seasonal'],
            'seasonal_period': seasonality['period'],
            'shock_visible': any(
                avg_trust_trajectory[shock_step + d] < avg_trust_trajectory[shock_step - 1] - 0.01
                for d in range(1, 10) if shock_step + d < n_steps
            ),
            'trust_recovered': avg_trust_trajectory[-1] > avg_trust_trajectory[shock_step + 15] if shock_step + 15 < n_steps else False,
        }


# ═══════════════════════════════════════════════════════════════
#  TEST RUNNER
# ═══════════════════════════════════════════════════════════════

def run_all_checks():
    """Run all temporal trust dynamics checks."""
    checks_passed = 0
    checks_failed = 0
    total_sections = 12

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal checks_passed, checks_failed
        if condition:
            checks_passed += 1
            print(f"  ✓ {name}")
        else:
            checks_failed += 1
            print(f"  ✗ {name}: {detail}")
        return condition

    random.seed(42)

    # ── §1 Exponential Forgetting ──
    print("\n§1 Exponential Forgetting")
    print("─" * 40)

    eb = EbbinghausForgetting(base_stability=10.0)

    # Single observation retention
    check("Full retention at t=0", abs(eb.retention(0, 1) - 1.0) < 0.01)
    check("Retention decays at t=10", eb.retention(10, 1) < 1.0)
    check("Retention positive at t=100", eb.retention(100, 1) > 0)

    # More observations = higher retention
    r1 = eb.retention(20, 1)
    r5 = eb.retention(20, 5)
    check("More observations → higher retention", r5 > r1,
          f"r1={r1:.4f}, r5={r5:.4f}")

    # Effective trust computation
    observations = [(0, 0.8), (5, 0.7), (10, 0.9)]
    t = eb.effective_trust(observations, 10)
    check("Effective trust in [0, 1]", 0 <= t <= 1)
    check("Effective trust weighted toward recent", abs(t - 0.85) < 0.15,
          f"trust={t:.4f}")

    # Empty observations
    t_empty = eb.effective_trust([], 10)
    check("Empty observations → default trust", abs(t_empty - 0.1) < 0.01)

    # Very old observations
    old_obs = [(0, 0.9)]
    t_old = eb.effective_trust(old_obs, 1000)
    check("Very old evidence → low trust", t_old < 0.5,
          f"trust={t_old:.4f}")

    # ── §2 Weighted Memory ──
    print("\n§2 Weighted Memory")
    print("─" * 40)

    timestamps = [0.0, 10.0, 20.0, 30.0, 40.0]
    current = 50.0

    exp_w = WeightedMemory.exponential_weights(timestamps, current, 0.1)
    check("Exponential weights increase with recency",
          all(exp_w[i] <= exp_w[i + 1] for i in range(len(exp_w) - 1)))
    check("Most recent has highest weight", exp_w[-1] == max(exp_w))

    lin_w = WeightedMemory.linear_weights(timestamps, current, 100.0)
    check("Linear weights all positive (within window)",
          all(w > 0 for w in lin_w))
    check("Linear weights decrease with age",
          all(lin_w[i] <= lin_w[i + 1] for i in range(len(lin_w) - 1)))

    # Sliding window
    values = list(range(100))
    windowed = WeightedMemory.sliding_window(values, 10)
    check("Sliding window returns last N", windowed == list(range(90, 100)))

    # Adaptive window
    stable_values = [0.5 + random.gauss(0, 0.01) for _ in range(100)]
    volatile_values = [0.5 + random.gauss(0, 0.2) for _ in range(100)]

    _, stable_window = WeightedMemory.adaptive_window(
        stable_values, list(range(100)), 100)
    _, volatile_window = WeightedMemory.adaptive_window(
        volatile_values, list(range(100)), 100)
    check("Stable → larger window, volatile → smaller",
          stable_window >= volatile_window,
          f"stable={stable_window}, volatile={volatile_window}")

    # ── §3 Trust Inertia ──
    print("\n§3 Trust Inertia")
    print("─" * 40)

    inertia = TrustInertia(alpha=0.1)

    # New entity: low inertia
    new_trust = inertia.apply_inertia(0.3, 0.1, n_observations=5, age=10)
    # Old entity: high inertia
    old_trust = inertia.apply_inertia(0.3, 0.1, n_observations=100, age=500)

    check("New entity changes more than old",
          abs(new_trust - 0.3) > abs(old_trust - 0.3),
          f"new_delta={abs(new_trust-0.3):.4f}, old_delta={abs(old_trust-0.3):.4f}")
    check("Both move in right direction", new_trust > 0.3 and old_trust > 0.3)
    check("Neither exceeds bounds", 0 <= new_trust <= 1 and 0 <= old_trust <= 1)

    # Mass computation
    mass_new = inertia.compute_mass(5, 0.3, 10)
    mass_old = inertia.compute_mass(100, 0.8, 500)
    check("Old established entity has higher mass", mass_old > mass_new)

    # Required evidence
    req = inertia.required_evidence(0.3, 0.7, 5, 10)
    check("Required evidence is finite", 0 < req < 10000,
          f"required={req}")

    # ── §4 Seasonal Trust ──
    print("\n§4 Seasonal Trust Patterns")
    print("─" * 40)

    random.seed(42)
    seasonal = SeasonalTrust.generate_seasonal(365, base_trust=0.6,
                                               amplitude=0.1, period=30)

    check("Seasonal series length correct", len(seasonal) == 365)
    check("All values in [0, 1]", all(0 <= v <= 1 for v in seasonal))

    detected = SeasonalTrust.detect_seasonality(seasonal, max_period=45)
    check("Seasonality detected", detected['seasonal'],
          f"strength={detected['strength']:.4f}")
    check("Period approximately correct", abs(detected['period'] - 30) < 10,
          f"detected_period={detected['period']}")

    # Deseasonalize
    deseasonalized = SeasonalTrust.deseasonalize(seasonal, 30)
    # Check that seasonal autocorrelation drops (not variance — moving avg amplifies boundary noise)
    deseas_check = SeasonalTrust.detect_seasonality(deseasonalized, max_period=45)
    check("Deseasonalized reduces seasonal autocorrelation",
          deseas_check['strength'] < detected['strength'],
          f"original={detected['strength']:.4f}, deseasonalized={deseas_check['strength']:.4f}")

    # ── §5 Regime Change Detection ──
    print("\n§5 Regime Change Detection")
    print("─" * 40)

    # Create signal with regime change at step 100
    regime_signal = [0.5 + random.gauss(0, 0.02) for _ in range(100)]
    regime_signal += [0.8 + random.gauss(0, 0.02) for _ in range(100)]

    cusum_changes = RegimeChangeDetector.cusum_detect(regime_signal)
    check("CUSUM detects regime change", len(cusum_changes) > 0,
          f"detected={len(cusum_changes)} changes")
    if cusum_changes:
        check("Change detected near step 100",
              any(80 <= c <= 120 for c in cusum_changes),
              f"change_points={cusum_changes}")

    # Sliding window detection
    sw_changes = RegimeChangeDetector.sliding_window_detect(regime_signal, window_size=20)
    check("Sliding window detects change", len(sw_changes) > 0)
    if sw_changes:
        check("Sliding window: upward shift detected",
              sw_changes[0]['direction'] == 'up')

    # No regime change in stable signal
    stable_signal = [0.5 + random.gauss(0, 0.02) for _ in range(200)]
    stable_changes = RegimeChangeDetector.cusum_detect(stable_signal, threshold=5.0)
    check("Stable signal: no false positives",
          len(stable_changes) == 0,
          f"false_positives={len(stable_changes)}")

    # ── §6 Information Shock Propagation ──
    print("\n§6 Information Shock Propagation")
    print("─" * 40)

    random.seed(42)
    shock = InformationShock.simulate_shock(n_nodes=100, shock_magnitude=-0.3)

    check("Shock propagates to majority",
          shock['final_informed_fraction'] > 0.5,
          f"informed={shock['final_informed_fraction']:.2%}")
    check("Trust drops after shock", shock['peak_trust_drop'] > 0.01,
          f"drop={shock['peak_trust_drop']:.4f}")
    check("Propagation speed < 20 steps",
          shock['propagation_speed'] < 20,
          f"speed={shock['propagation_speed']}")

    # ── §7 Trust Half-Life ──
    print("\n§7 Trust Half-Life")
    print("─" * 40)

    # Talent decays slowly
    talent_100 = TrustHalfLife.decay(0.9, 100, 'talent')
    # Temperament decays fast
    temp_100 = TrustHalfLife.decay(0.9, 100, 'temperament')

    check("Talent retains more than temperament at t=100",
          talent_100 > temp_100,
          f"talent={talent_100:.4f}, temp={temp_100:.4f}")

    # After 1 half-life, trust should be ~midpoint to base
    talent_hl = TrustHalfLife.decay(0.9, 365, 'talent')
    expected = 0.1 + (0.9 - 0.1) * 0.5  # Midpoint between 0.9 and 0.1
    check("Talent at half-life ≈ 50% retained",
          abs(talent_hl - expected) < 0.1,
          f"actual={talent_hl:.4f}, expected={expected:.4f}")

    # Composite decay
    t3 = {'talent': 0.8, 'training': 0.7, 'temperament': 0.9}
    composite_0 = TrustHalfLife.composite_decay(t3, 0)
    composite_100 = TrustHalfLife.composite_decay(t3, 100)
    check("Composite decays over time", composite_100 < composite_0,
          f"t=0: {composite_0:.4f}, t=100: {composite_100:.4f}")

    # Time to threshold
    time_talent = TrustHalfLife.time_to_threshold(0.8, 0.5, 'talent')
    time_temp = TrustHalfLife.time_to_threshold(0.8, 0.5, 'temperament')
    check("Talent takes longer to reach threshold than temperament",
          time_talent > time_temp,
          f"talent={time_talent:.1f}, temp={time_temp:.1f}")

    # ── §8 Temporal Aggregation ──
    print("\n§8 Temporal Aggregation")
    print("─" * 40)

    # Bayesian update
    observations = [(t, 0.5 + 0.3 * (t / 100)) for t in range(100)]
    bayes_trust = TemporalAggregation.bayesian_update(0.3, observations, 100)
    check("Bayesian update: trust increases with positive evidence",
          bayes_trust > 0.3, f"trust={bayes_trust:.4f}")
    check("Bayesian trust in bounds", 0 <= bayes_trust <= 1)

    # Multi-window aggregation
    agg = TemporalAggregation.sliding_window_aggregate(observations, 100)
    check("Multi-window aggregation computed", agg['aggregate'] > 0)
    check("Multiple windows valid", agg['n_valid_windows'] >= 2,
          f"n_valid={agg['n_valid_windows']}")

    # ── §9 Prediction & Forecasting ──
    print("\n§9 Prediction & Forecasting")
    print("─" * 40)

    # Upward trend
    upward = [0.3 + 0.002 * t + random.gauss(0, 0.01) for t in range(100)]
    upward = [max(0, min(1, v)) for v in upward]

    linear_fc = TrustForecast.linear_extrapolation(upward, 30)
    check("Linear forecast continues upward trend",
          linear_fc[-1] > upward[-1] - 0.05,
          f"last_history={upward[-1]:.4f}, forecast_end={linear_fc[-1]:.4f}")

    exp_fc = TrustForecast.exponential_smoothing(upward, alpha=0.3, forecast_steps=30)
    check("Exponential smoothing stays near end of history",
          abs(exp_fc[0] - upward[-1]) < 0.1)

    mean_rev = TrustForecast.mean_reversion(upward, equilibrium=0.5, forecast_steps=30)
    # If current > 0.5, mean reversion should pull toward 0.5
    if upward[-1] > 0.5:
        check("Mean reversion moves toward equilibrium",
              mean_rev[-1] < upward[-1])
    else:
        check("Mean reversion moves toward equilibrium",
              mean_rev[-1] > upward[-1])

    # ── §10 Staleness Detection ──
    print("\n§10 Staleness Detection")
    print("─" * 40)

    staleness = StalenessDetector()

    check("Fresh classification",
          staleness.classify(90, 100, 90).value == 'fresh')
    check("Aging classification",
          staleness.classify(0, 100, 90).value == 'aging')
    check("Stale classification",
          staleness.classify(0, 200, 90).value == 'stale')
    check("Expired classification",
          staleness.classify(0, 300, 90).value == 'expired')

    # Confidence discount
    check("Fresh: full confidence",
          staleness.confidence_discount(StalenessDetector.Staleness.FRESH) == 1.0)
    check("Expired: low confidence",
          staleness.confidence_discount(StalenessDetector.Staleness.EXPIRED) == 0.2)

    # Audit
    entities = [
        {'id': 'A', 'last_observed': 95, 'trust': 0.8},
        {'id': 'B', 'last_observed': 50, 'trust': 0.7},
        {'id': 'C', 'last_observed': 0, 'trust': 0.9},
        {'id': 'D', 'last_observed': -200, 'trust': 0.6},
    ]
    audit = staleness.audit_entities(entities, 100, 90)
    check("Audit counts fresh entities", audit['fresh_count'] >= 1)
    check("Audit finds stale entities", audit['stale_count'] >= 1)

    # ── §11 Temporal Attack Vectors ──
    print("\n§11 Temporal Attack Vectors")
    print("─" * 40)

    random.seed(42)

    # Slow poisoning
    poison = TemporalAttacks.slow_poisoning(n_steps=200, poison_rate=0.005)
    check("Slow poisoning inflates trust",
          poison['trust_inflation'] > 0.3,
          f"inflation={poison['trust_inflation']:.4f}")
    check("CUSUM detects slow poisoning", poison['detected'],
          f"first_detection={poison['first_detection']}")

    # Trust bombing
    bomb = TemporalAttacks.trust_bombing(base_trust=0.3, bomb_size=50)
    check("Trust bombing has effect without inertia",
          bomb['bomb_effectiveness_no_inertia'] > 0.1)
    check("Inertia dampens trust bomb",
          bomb['inertia_dampening'] > 0.3,
          f"dampening={bomb['inertia_dampening']:.4f}")

    # Staleness exploit
    exploit = TemporalAttacks.staleness_exploit(trust=0.8, wait_time=300)
    check("Staleness exploit gap exists",
          exploit['exploit_gap'] > 0.2,
          f"gap={exploit['exploit_gap']:.4f}")
    check("Cautious observer defends",
          exploit['defense_effective'])

    # ── §12 Full Temporal Simulation ──
    print("\n§12 Full Temporal Simulation")
    print("─" * 40)

    random.seed(42)
    sim = TemporalSimulation.full_simulation(
        n_entities=50, n_steps=365, shock_step=180
    )

    check("Final average trust reasonable",
          0.2 < sim['final_avg_trust'] < 0.8,
          f"avg={sim['final_avg_trust']:.4f}")
    check("Gini bounded", sim['final_gini'] < 0.5,
          f"gini={sim['final_gini']:.4f}")
    check("Shock visible in trajectory", sim['shock_visible'])
    check("Trust recovers after shock", sim['trust_recovered'])
    check("Seasonality detected in simulation", sim['seasonality_detected'])
    check("Regime changes detected at shock",
          sim['regime_changes_detected'] > 0,
          f"n_changes={sim['regime_changes_detected']}")

    # ── Summary ──
    total = checks_passed + checks_failed
    print(f"\n{'═' * 50}")
    print(f"Temporal Trust Dynamics: {checks_passed}/{total} checks passed")
    print(f"Sections: {total_sections}/{total_sections}")

    if checks_failed > 0:
        print(f"\n⚠ {checks_failed} checks failed")
    else:
        print(f"\n✓ All {total} checks passed across {total_sections} sections")

    return checks_passed, checks_failed


if __name__ == "__main__":
    passed, failed = run_all_checks()
    exit(0 if failed == 0 else 1)
