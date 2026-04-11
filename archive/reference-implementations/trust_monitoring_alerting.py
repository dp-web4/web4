"""
Trust Monitoring & Alerting for Web4
Session 32, Track 6

Real-time trust health monitoring and anomaly detection:
- Moving average trust tracking
- EWMA (exponentially weighted moving average) for trend detection
- CUSUM (cumulative sum) for change detection
- Trust threshold alerting with hysteresis
- Multi-dimensional trust dashboard (T3 dimensions)
- Alert aggregation and deduplication
- SLO (service level objective) for trust quality
- Trust incident lifecycle (detect → alert → investigate → resolve)
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Set
from collections import deque


# ─── Alert Types ──────────────────────────────────────────────────

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class Alert:
    alert_id: str
    entity: str
    dimension: str
    severity: AlertSeverity
    state: AlertState
    message: str
    timestamp: int
    value: float
    threshold: float


# ─── Moving Average Tracker ──────────────────────────────────────

@dataclass
class MovingAverageTracker:
    """Track trust using simple moving average over a window."""
    window_size: int = 20
    _values: deque = field(default_factory=lambda: deque())

    def update(self, value: float):
        self._values.append(value)
        while len(self._values) > self.window_size:
            self._values.popleft()

    @property
    def average(self) -> float:
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)

    @property
    def std_dev(self) -> float:
        if len(self._values) < 2:
            return 0.0
        avg = self.average
        variance = sum((v - avg) ** 2 for v in self._values) / (len(self._values) - 1)
        return math.sqrt(variance)

    @property
    def trend(self) -> float:
        """Estimate trend as slope of linear fit."""
        if len(self._values) < 3:
            return 0.0
        n = len(self._values)
        x_mean = (n - 1) / 2
        y_mean = self.average
        numerator = sum((i - x_mean) * (v - y_mean)
                        for i, v in enumerate(self._values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        return numerator / denominator if denominator > 0 else 0.0


# ─── EWMA Tracker ────────────────────────────────────────────────

@dataclass
class EWMATracker:
    """Exponentially Weighted Moving Average for trend detection."""
    alpha: float = 0.1  # smoothing factor
    value: float = 0.0
    variance: float = 0.0
    initialized: bool = False

    def update(self, observation: float):
        if not self.initialized:
            self.value = observation
            self.variance = 0.0
            self.initialized = True
            return

        # EWMA update
        diff = observation - self.value
        self.value = self.alpha * observation + (1 - self.alpha) * self.value
        self.variance = (1 - self.alpha) * (self.variance + self.alpha * diff ** 2)

    @property
    def std_dev(self) -> float:
        return math.sqrt(max(0, self.variance))

    def upper_band(self, n_sigma: float = 2.0) -> float:
        return self.value + n_sigma * self.std_dev

    def lower_band(self, n_sigma: float = 2.0) -> float:
        return self.value - n_sigma * self.std_dev


# ─── CUSUM Change Detection ──────────────────────────────────────

@dataclass
class CUSUMDetector:
    """
    Cumulative Sum for detecting trust regime changes.
    Detects both upward and downward shifts.
    """
    target: float = 0.5    # expected trust level
    threshold: float = 5.0  # detection threshold
    drift: float = 0.5      # allowable drift
    s_pos: float = 0.0      # positive CUSUM
    s_neg: float = 0.0      # negative CUSUM

    def update(self, value: float) -> Optional[str]:
        """Returns 'increase', 'decrease', or None."""
        diff = value - self.target

        self.s_pos = max(0, self.s_pos + diff - self.drift)
        self.s_neg = max(0, self.s_neg - diff - self.drift)

        if self.s_pos > self.threshold:
            self.s_pos = 0  # reset
            return "increase"
        if self.s_neg > self.threshold:
            self.s_neg = 0  # reset
            return "decrease"

        return None


# ─── Threshold Alert with Hysteresis ─────────────────────────────

@dataclass
class HysteresisAlert:
    """
    Alert with hysteresis to prevent flapping.
    Fires at fire_threshold, resolves at resolve_threshold.
    """
    fire_threshold: float     # trust below this → alert
    resolve_threshold: float  # trust above this → resolve
    is_firing: bool = False
    consecutive_fire: int = 0
    consecutive_ok: int = 0
    min_fire_count: int = 3   # need N consecutive violations to fire
    min_ok_count: int = 5     # need N consecutive OK to resolve

    def check(self, value: float) -> Optional[str]:
        """Returns 'fire', 'resolve', or None."""
        if value < self.fire_threshold:
            self.consecutive_fire += 1
            self.consecutive_ok = 0
        elif value > self.resolve_threshold:
            self.consecutive_ok += 1
            self.consecutive_fire = 0
        else:
            # In dead zone
            self.consecutive_fire = 0
            self.consecutive_ok = 0

        if not self.is_firing and self.consecutive_fire >= self.min_fire_count:
            self.is_firing = True
            return "fire"

        if self.is_firing and self.consecutive_ok >= self.min_ok_count:
            self.is_firing = False
            return "resolve"

        return None


# ─── Trust SLO ────────────────────────────────────────────────────

@dataclass
class TrustSLO:
    """
    Service Level Objective for trust quality.
    e.g., "99% of trust evaluations should be >= 0.7"
    """
    name: str
    target_percentile: float = 0.99
    min_trust: float = 0.7
    window_size: int = 100
    _values: deque = field(default_factory=lambda: deque())

    def record(self, value: float):
        self._values.append(value)
        while len(self._values) > self.window_size:
            self._values.popleft()

    @property
    def compliance(self) -> float:
        """Fraction of values meeting the SLO."""
        if not self._values:
            return 1.0
        meeting = sum(1 for v in self._values if v >= self.min_trust)
        return meeting / len(self._values)

    @property
    def is_met(self) -> bool:
        return self.compliance >= self.target_percentile

    @property
    def error_budget_remaining(self) -> float:
        """How much of the error budget is left."""
        allowed_failures = (1 - self.target_percentile) * len(self._values)
        actual_failures = sum(1 for v in self._values if v < self.min_trust)
        if allowed_failures <= 0:
            return 0.0 if actual_failures > 0 else 1.0
        return max(0, 1 - actual_failures / allowed_failures)


# ─── Alert Aggregator ─────────────────────────────────────────────

@dataclass
class AlertAggregator:
    """Aggregate and deduplicate alerts."""
    active_alerts: Dict[str, Alert] = field(default_factory=dict)
    history: List[Alert] = field(default_factory=list)
    dedup_window: int = 10  # suppress duplicate alerts within window

    def _alert_key(self, entity: str, dimension: str) -> str:
        return f"{entity}:{dimension}"

    def fire(self, entity: str, dimension: str,
             severity: AlertSeverity, message: str,
             timestamp: int, value: float, threshold: float) -> Optional[Alert]:
        """Create alert if not already firing for this entity/dimension."""
        key = self._alert_key(entity, dimension)

        # Check for existing active alert
        if key in self.active_alerts:
            existing = self.active_alerts[key]
            if existing.state == AlertState.FIRING:
                # Suppress duplicate within dedup window
                if timestamp - existing.timestamp < self.dedup_window:
                    return None
                # Update existing
                existing.timestamp = timestamp
                existing.value = value
                return existing

        alert = Alert(
            alert_id=f"alert_{len(self.history)}",
            entity=entity,
            dimension=dimension,
            severity=severity,
            state=AlertState.FIRING,
            message=message,
            timestamp=timestamp,
            value=value,
            threshold=threshold,
        )
        self.active_alerts[key] = alert
        self.history.append(alert)
        return alert

    def resolve(self, entity: str, dimension: str,
                timestamp: int) -> Optional[Alert]:
        """Resolve an active alert."""
        key = self._alert_key(entity, dimension)
        if key in self.active_alerts:
            alert = self.active_alerts[key]
            alert.state = AlertState.RESOLVED
            del self.active_alerts[key]
            return alert
        return None

    @property
    def firing_count(self) -> int:
        return sum(1 for a in self.active_alerts.values()
                   if a.state == AlertState.FIRING)


# ─── Trust Monitor ────────────────────────────────────────────────

@dataclass
class TrustMonitor:
    """Complete trust monitoring system."""
    ewma_trackers: Dict[str, EWMATracker] = field(default_factory=dict)
    cusum_detectors: Dict[str, CUSUMDetector] = field(default_factory=dict)
    hysteresis_alerts: Dict[str, HysteresisAlert] = field(default_factory=dict)
    aggregator: AlertAggregator = field(default_factory=AlertAggregator)
    slos: Dict[str, TrustSLO] = field(default_factory=dict)

    def register_entity(self, entity: str, dimension: str = "overall",
                         fire_threshold: float = 0.3,
                         resolve_threshold: float = 0.5):
        key = f"{entity}:{dimension}"
        self.ewma_trackers[key] = EWMATracker(alpha=0.1)
        self.cusum_detectors[key] = CUSUMDetector(target=0.5)
        self.hysteresis_alerts[key] = HysteresisAlert(
            fire_threshold=fire_threshold,
            resolve_threshold=resolve_threshold)

    def observe(self, entity: str, dimension: str, value: float,
                timestamp: int) -> List[Alert]:
        """Process a trust observation. Returns new alerts."""
        key = f"{entity}:{dimension}"
        alerts = []

        # Update trackers
        if key in self.ewma_trackers:
            self.ewma_trackers[key].update(value)

        if key in self.cusum_detectors:
            change = self.cusum_detectors[key].update(value)
            if change == "decrease":
                alert = self.aggregator.fire(
                    entity, dimension, AlertSeverity.WARNING,
                    f"Trust decrease detected for {entity}",
                    timestamp, value, 0.5)
                if alert:
                    alerts.append(alert)

        if key in self.hysteresis_alerts:
            action = self.hysteresis_alerts[key].check(value)
            if action == "fire":
                alert = self.aggregator.fire(
                    entity, dimension, AlertSeverity.CRITICAL,
                    f"Trust below threshold for {entity}",
                    timestamp, value, self.hysteresis_alerts[key].fire_threshold)
                if alert:
                    alerts.append(alert)
            elif action == "resolve":
                self.aggregator.resolve(entity, dimension, timestamp)

        # Record in SLOs
        for slo in self.slos.values():
            slo.record(value)

        return alerts


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    print("=" * 70)
    print("Trust Monitoring & Alerting for Web4")
    print("Session 32, Track 6")
    print("=" * 70)

    # ── §1 Moving Average ───────────────────────────────────────
    print("\n§1 Moving Average Tracking\n")

    ma = MovingAverageTracker(window_size=5)
    for v in [0.5, 0.6, 0.7, 0.8, 0.9]:
        ma.update(v)

    check("ma_average", abs(ma.average - 0.7) < 0.01,
          f"avg={ma.average:.4f}")
    check("ma_std_dev", ma.std_dev > 0,
          f"std={ma.std_dev:.4f}")
    check("ma_trend_positive", ma.trend > 0,
          f"trend={ma.trend:.6f}")

    # Decreasing values
    ma_dec = MovingAverageTracker(window_size=5)
    for v in [0.9, 0.8, 0.7, 0.6, 0.5]:
        ma_dec.update(v)
    check("ma_trend_negative", ma_dec.trend < 0,
          f"trend={ma_dec.trend:.6f}")

    # ── §2 EWMA Tracker ────────────────────────────────────────
    print("\n§2 EWMA Tracking\n")

    ewma = EWMATracker(alpha=0.2)
    for v in [0.5, 0.5, 0.5, 0.5, 0.5]:
        ewma.update(v)

    check("ewma_stable", abs(ewma.value - 0.5) < 0.05,
          f"ewma={ewma.value:.4f}")
    check("ewma_low_variance", ewma.std_dev < 0.1,
          f"std={ewma.std_dev:.4f}")

    # Bands contain value
    check("ewma_bands", ewma.lower_band() <= 0.5 <= ewma.upper_band(),
          f"lower={ewma.lower_band():.4f} upper={ewma.upper_band():.4f}")

    # Sharp change detected
    ewma.update(0.1)
    check("ewma_detects_change", ewma.value < 0.45,
          f"ewma={ewma.value:.4f}")

    # ── §3 CUSUM Change Detection ──────────────────────────────
    print("\n§3 CUSUM Change Detection\n")

    cusum = CUSUMDetector(target=0.5, threshold=3.0, drift=0.2)

    # Stable period
    results = []
    for _ in range(10):
        results.append(cusum.update(0.5))
    check("cusum_stable", all(r is None for r in results))

    # Sharp decrease
    cusum2 = CUSUMDetector(target=0.5, threshold=2.0, drift=0.1)
    decrease_detected = False
    for _ in range(20):
        r = cusum2.update(0.1)
        if r == "decrease":
            decrease_detected = True
            break
    check("cusum_detects_decrease", decrease_detected)

    # Sharp increase
    cusum3 = CUSUMDetector(target=0.5, threshold=2.0, drift=0.1)
    increase_detected = False
    for _ in range(20):
        r = cusum3.update(0.9)
        if r == "increase":
            increase_detected = True
            break
    check("cusum_detects_increase", increase_detected)

    # ── §4 Hysteresis Alert ─────────────────────────────────────
    print("\n§4 Hysteresis Alert\n")

    hyst = HysteresisAlert(
        fire_threshold=0.3,
        resolve_threshold=0.6,
        min_fire_count=3,
        min_ok_count=3
    )

    # Below threshold but not enough consecutive
    check("hyst_no_immediate_fire", hyst.check(0.2) is None)
    check("hyst_still_no_fire", hyst.check(0.2) is None)

    # Third consecutive → fires
    check("hyst_fires_on_third", hyst.check(0.2) == "fire")
    check("hyst_is_firing", hyst.is_firing)

    # Above resolve but not enough consecutive
    hyst.check(0.7)
    hyst.check(0.7)
    check("hyst_no_immediate_resolve", hyst.is_firing)

    # Third consecutive → resolves
    check("hyst_resolves", hyst.check(0.7) == "resolve")
    check("hyst_not_firing", not hyst.is_firing)

    # ── §5 Trust SLO ───────────────────────────────────────────
    print("\n§5 Trust SLO\n")

    slo = TrustSLO(name="basic_trust", target_percentile=0.95, min_trust=0.5)

    # All good values
    for _ in range(100):
        slo.record(0.8)

    check("slo_met", slo.is_met)
    check("slo_full_budget", slo.error_budget_remaining > 0.9)

    # Add some bad values
    for _ in range(10):
        slo.record(0.2)

    check("slo_compliance_drops", slo.compliance < 1.0,
          f"compliance={slo.compliance:.4f}")

    # ── §6 Alert Aggregator ────────────────────────────────────
    print("\n§6 Alert Aggregation\n")

    agg = AlertAggregator(dedup_window=5)

    a1 = agg.fire("alice", "overall", AlertSeverity.CRITICAL,
                    "Low trust", 10, 0.2, 0.3)
    check("first_alert_fires", a1 is not None)
    check("firing_count_1", agg.firing_count == 1)

    # Duplicate within window → suppressed
    a2 = agg.fire("alice", "overall", AlertSeverity.CRITICAL,
                    "Low trust", 12, 0.2, 0.3)
    check("duplicate_suppressed", a2 is None)

    # Different entity → new alert
    a3 = agg.fire("bob", "overall", AlertSeverity.WARNING,
                    "Trust declining", 13, 0.4, 0.5)
    check("different_entity_fires", a3 is not None)
    check("firing_count_2", agg.firing_count == 2)

    # Resolve
    agg.resolve("alice", "overall", 20)
    check("resolved_count", agg.firing_count == 1)

    # ── §7 Full Monitor ────────────────────────────────────────
    print("\n§7 Full Trust Monitor\n")

    monitor = TrustMonitor()
    monitor.register_entity("server_1", "overall",
                              fire_threshold=0.3, resolve_threshold=0.6)
    monitor.slos["quality"] = TrustSLO("quality", 0.95, 0.5)

    random.seed(42)

    # Normal operation
    alerts_normal = []
    for t in range(50):
        value = 0.7 + random.gauss(0, 0.05)
        alerts_normal.extend(monitor.observe("server_1", "overall", value, t))
    check("normal_few_alerts", len(alerts_normal) == 0,
          f"alerts={len(alerts_normal)}")

    # Trust degradation
    alerts_degrade = []
    for t in range(50, 70):
        value = 0.7 - (t - 50) * 0.03  # gradual decrease
        alerts_degrade.extend(monitor.observe("server_1", "overall", value, t))

    check("degradation_alerts", len(alerts_degrade) > 0,
          f"alerts={len(alerts_degrade)}")

    # SLO check
    check("slo_after_degradation", monitor.slos["quality"].compliance < 1.0,
          f"compliance={monitor.slos['quality'].compliance:.4f}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
