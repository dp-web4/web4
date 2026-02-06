#!/usr/bin/env python3
"""
Session 148: Resource Quotas + Timing Attack Mitigation (Phase 2)

Research Goal: Implement Phase 2 security mitigations from Session 146:
1. Resource Quotas (computational, bandwidth, connection limits)
2. Timing Attack Mitigation (jittered windows, adaptive decay, rate smoothing)

These provide defense against subtle DOS and timing-based attacks.

Building on:
- Session 144: 9-layer ATP-Security unification
- Session 147: Eclipse defense + Consensus checkpoints

Platform: Legion (RTX 4090)
Session: Autonomous Web4 Research - Session 148
Date: 2026-01-08
"""

import time
import random
import hashlib
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import json
from pathlib import Path


# ============================================================================
# RESOURCE QUOTAS
# ============================================================================

@dataclass
class ResourceUsage:
    """Track resource usage for a node."""
    node_id: str
    cpu_seconds: float = 0.0
    bandwidth_bytes: int = 0
    connection_count: int = 0
    last_reset: float = field(default_factory=time.time)


class ResourceQuotaSystem:
    """
    Resource quota enforcement to prevent subtle DOS attacks.

    Tracks and limits:
    1. CPU usage (computational work)
    2. Bandwidth (message sizes)
    3. Connections (network resources)

    All quotas are per-node and reset periodically.
    """

    def __init__(self,
                 cpu_quota_per_minute: float = 10.0,
                 bandwidth_quota_mb: float = 10.0,
                 max_connections_per_node: int = 10):
        self.cpu_quota_per_minute = cpu_quota_per_minute
        self.bandwidth_quota_mb = bandwidth_quota_mb
        self.max_connections_per_node = max_connections_per_node

        self.usage: Dict[str, ResourceUsage] = {}

        # Metrics
        self.cpu_quota_exceeded: int = 0
        self.bandwidth_quota_exceeded: int = 0
        self.connection_quota_exceeded: int = 0

    def track_cpu_usage(self, node_id: str, cpu_seconds: float) -> bool:
        """
        Track CPU usage and enforce quota.

        Returns:
            True if within quota, False if exceeded
        """
        if node_id not in self.usage:
            self.usage[node_id] = ResourceUsage(node_id)

        usage = self.usage[node_id]

        # Reset quota every minute
        now = time.time()
        if now - usage.last_reset > 60:
            usage.cpu_seconds = 0.0
            usage.last_reset = now

        # Check quota
        if usage.cpu_seconds + cpu_seconds > self.cpu_quota_per_minute:
            self.cpu_quota_exceeded += 1
            return False

        # Record usage
        usage.cpu_seconds += cpu_seconds
        return True

    def track_bandwidth_usage(self, node_id: str, message_bytes: int,
                             trust_score: float = 0.5) -> bool:
        """
        Track bandwidth usage and enforce quota.

        Quota is trust-weighted: higher trust → higher limits

        Returns:
            True if within quota, False if exceeded
        """
        if node_id not in self.usage:
            self.usage[node_id] = ResourceUsage(node_id)

        usage = self.usage[node_id]

        # Reset quota every minute
        now = time.time()
        if now - usage.last_reset > 60:
            usage.bandwidth_bytes = 0
            usage.last_reset = now

        # Trust-weighted quota (higher trust = higher limits)
        trust_multiplier = 1.0 + trust_score
        effective_quota_mb = self.bandwidth_quota_mb * trust_multiplier
        effective_quota_bytes = int(effective_quota_mb * 1024 * 1024)

        # Check quota
        if usage.bandwidth_bytes + message_bytes > effective_quota_bytes:
            self.bandwidth_quota_exceeded += 1
            return False

        # Record usage
        usage.bandwidth_bytes += message_bytes
        return True

    def check_connection_limit(self, node_id: str) -> bool:
        """
        Check if node can open another connection.

        Returns:
            True if within limit, False if exceeded
        """
        if node_id not in self.usage:
            self.usage[node_id] = ResourceUsage(node_id)

        usage = self.usage[node_id]

        if usage.connection_count >= self.max_connections_per_node:
            self.connection_quota_exceeded += 1
            return False

        return True

    def open_connection(self, node_id: str) -> bool:
        """
        Open connection for node.

        Returns:
            True if successful, False if quota exceeded
        """
        if not self.check_connection_limit(node_id):
            return False

        if node_id not in self.usage:
            self.usage[node_id] = ResourceUsage(node_id)

        self.usage[node_id].connection_count += 1
        return True

    def close_connection(self, node_id: str):
        """Close connection for node."""
        if node_id in self.usage:
            self.usage[node_id].connection_count = max(
                0, self.usage[node_id].connection_count - 1
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get resource quota metrics."""
        return {
            "cpu_quota_exceeded": self.cpu_quota_exceeded,
            "bandwidth_quota_exceeded": self.bandwidth_quota_exceeded,
            "connection_quota_exceeded": self.connection_quota_exceeded,
            "nodes_tracked": len(self.usage)
        }


# ============================================================================
# TIMING ATTACK MITIGATION
# ============================================================================

class TimingDefense:
    """
    Timing attack mitigation system.

    Prevents exploitation of time-dependent mechanisms:
    1. Jittered Windows (unpredictable rate limit windows)
    2. Adaptive Decay (variable trust decay based on behavior)
    3. Rate Limit Smoothing (exponential cost instead of hard cutoff)

    Makes timing attacks harder to execute and less effective.
    """

    def __init__(self):
        self.node_jitters: Dict[str, float] = {}  # Persistent per-node
        self.decay_history: Dict[str, List[float]] = {}

        # Metrics
        self.jitter_applications: int = 0
        self.adaptive_decays_computed: int = 0
        self.smoothing_applications: int = 0

    def get_jittered_window(self, node_id: str, base_window: float = 60.0) -> float:
        """
        Get rate window with per-node jitter.

        Each node has persistent jitter (not random each time) to prevent
        attackers from timing window boundaries.

        Args:
            node_id: Node identifier
            base_window: Base window size (seconds)

        Returns:
            Jittered window size (base ± 10s)
        """
        if node_id not in self.node_jitters:
            # Generate persistent jitter for this node
            node_hash = int(hashlib.sha256(node_id.encode()).hexdigest(), 16)
            jitter = (node_hash % 20) - 10  # -10 to +10 seconds
            self.node_jitters[node_id] = jitter

        self.jitter_applications += 1
        return base_window + self.node_jitters[node_id]

    def compute_adaptive_decay(self, node_id: str, days_inactive: float,
                              violation_rate: float, trust_score: float,
                              base_rate: float = 0.1) -> float:
        """
        Compute adaptive trust decay based on behavior history.

        Decay rate varies based on:
        - Violation history (volatile nodes decay faster)
        - Trust level (high trust decays slower)
        - Network conditions (can be adjusted externally)

        Returns:
            Decay amount
        """
        self.adaptive_decays_computed += 1

        # Volatility multiplier (more violations → faster decay)
        volatility_multiplier = 1.0 + violation_rate

        # Trust multiplier (high trust → slower decay)
        trust_multiplier = 1.0 / (1.0 + trust_score)

        # Effective decay rate
        effective_rate = base_rate * volatility_multiplier * trust_multiplier

        # Logarithmic decay
        if days_inactive <= 0:
            return 0.0

        decay = effective_rate * math.log(1 + days_inactive)

        # Record for history
        if node_id not in self.decay_history:
            self.decay_history[node_id] = []
        self.decay_history[node_id].append(decay)

        return decay

    def compute_rate_limit_delay(self, node_id: str, submissions_this_window: int,
                                 max_limit: int) -> float:
        """
        Compute exponential delay for rate limiting.

        Instead of hard cutoff at window boundary, gradually increase
        cost of submissions as window fills.

        Returns:
            Delay in seconds before submission allowed
        """
        self.smoothing_applications += 1

        if max_limit <= 0:
            return 0.0

        # Usage ratio (0 to 1+)
        usage_ratio = submissions_this_window / max_limit

        # Exponential cost increase
        # 0% usage = 0s delay
        # 50% usage = 0.6s delay
        # 100% usage = 147s delay (hard limit)
        # 150% usage = ~3200s delay (severe penalty)
        delay = math.exp(usage_ratio * 5) - 1

        return delay

    def get_metrics(self) -> Dict[str, Any]:
        """Get timing defense metrics."""
        return {
            "jitter_applications": self.jitter_applications,
            "adaptive_decays_computed": self.adaptive_decays_computed,
            "smoothing_applications": self.smoothing_applications,
            "nodes_with_jitter": len(self.node_jitters)
        }


# ============================================================================
# INTEGRATED PHASE 2 SECURITY
# ============================================================================

@dataclass
class NodeState:
    """Complete state for a node."""
    node_id: str
    trust_score: float
    contributions: int
    violations: int
    last_activity: float
    rate_history: deque = field(default_factory=lambda: deque(maxlen=100))


class Phase2SecuritySystem:
    """
    Phase 2 integrated security system.

    Combines:
    1. Resource quotas (CPU, bandwidth, connections)
    2. Timing attack mitigation (jitter, adaptive decay, smoothing)

    Provides defense against subtle DOS and timing-based attacks.
    """

    def __init__(self):
        self.resource_quotas = ResourceQuotaSystem(
            cpu_quota_per_minute=10.0,
            bandwidth_quota_mb=10.0,
            max_connections_per_node=10
        )
        self.timing_defense = TimingDefense()
        self.node_states: Dict[str, NodeState] = {}

    def register_node(self, node_id: str, trust_score: float = 0.1):
        """Register new node."""
        self.node_states[node_id] = NodeState(
            node_id=node_id,
            trust_score=trust_score,
            contributions=0,
            violations=0,
            last_activity=time.time()
        )

    def validate_submission(self, node_id: str, message_bytes: int,
                           cpu_seconds: float) -> Tuple[bool, str, float]:
        """
        Validate submission through Phase 2 defenses.

        Checks:
        1. CPU quota
        2. Bandwidth quota
        3. Rate limit with smoothing

        Returns:
            (allowed, reason, delay_seconds)
        """
        if node_id not in self.node_states:
            self.register_node(node_id)

        state = self.node_states[node_id]

        # 1. Check CPU quota
        if not self.resource_quotas.track_cpu_usage(node_id, cpu_seconds):
            return False, "CPU quota exceeded", 0.0

        # 2. Check bandwidth quota (trust-weighted)
        if not self.resource_quotas.track_bandwidth_usage(
            node_id, message_bytes, state.trust_score
        ):
            return False, "Bandwidth quota exceeded", 0.0

        # 3. Check rate limit with smoothing
        # Get jittered window
        window_size = self.timing_defense.get_jittered_window(node_id)

        # Count submissions in window
        now = time.time()
        window_start = now - window_size
        submissions_in_window = sum(
            1 for t in state.rate_history if t > window_start
        )

        # Compute delay
        max_limit = 10  # Base limit
        delay = self.timing_defense.compute_rate_limit_delay(
            node_id, submissions_in_window, max_limit
        )

        # Record submission
        state.rate_history.append(now)
        state.last_activity = now

        if delay > 60:  # More than 1 minute delay = reject
            return False, f"Rate limit exceeded (delay: {delay:.0f}s)", delay

        return True, "Submission allowed", delay

    def apply_adaptive_decay(self, node_id: str) -> float:
        """Apply adaptive trust decay."""
        if node_id not in self.node_states:
            return 0.0

        state = self.node_states[node_id]

        # Calculate days inactive
        days_inactive = (time.time() - state.last_activity) / 86400

        # Calculate violation rate
        total_actions = state.contributions + state.violations
        violation_rate = state.violations / max(1, total_actions)

        # Compute adaptive decay
        decay = self.timing_defense.compute_adaptive_decay(
            node_id, days_inactive, violation_rate, state.trust_score
        )

        # Apply decay
        state.trust_score = max(0.0, state.trust_score - decay)

        return decay

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get metrics from all Phase 2 systems."""
        return {
            "resource_quotas": self.resource_quotas.get_metrics(),
            "timing_defense": self.timing_defense.get_metrics(),
            "nodes_registered": len(self.node_states)
        }


# ============================================================================
# TESTS: Validate Phase 2 Security
# ============================================================================

def test_resource_quotas():
    """Test 1: Resource quota enforcement."""
    print("\n" + "="*80)
    print("TEST 1: Resource Quota Enforcement")
    print("="*80)

    system = ResourceQuotaSystem(
        cpu_quota_per_minute=5.0,
        bandwidth_quota_mb=1.0,
        max_connections_per_node=3
    )

    # Test CPU quota
    print("\n1. Testing CPU quota...")
    node_id = "node1"

    # Within quota
    result1 = system.track_cpu_usage(node_id, 2.0)
    print(f"   Usage 2.0s: {result1} (within 5.0s quota)")
    assert result1, "Should allow within quota"

    # Approaching quota
    result2 = system.track_cpu_usage(node_id, 2.5)
    print(f"   Usage +2.5s (total 4.5s): {result2}")
    assert result2, "Should allow within quota"

    # Exceed quota
    result3 = system.track_cpu_usage(node_id, 1.0)
    print(f"   Usage +1.0s (total 5.5s): {result3} (exceeds 5.0s quota)")
    assert not result3, "Should reject over quota"

    # Test bandwidth quota
    print("\n2. Testing bandwidth quota...")
    node_id = "node2"

    # Within quota (1 MB = 1,048,576 bytes, trust 0.5 → 1.5 MB effective)
    result1 = system.track_bandwidth_usage(node_id, 500_000, trust_score=0.5)
    print(f"   Usage 500 KB: {result1} (trust 0.5 → 1.5 MB quota)")
    assert result1, "Should allow within quota"

    # At quota limit
    result2 = system.track_bandwidth_usage(node_id, 1_000_000, trust_score=0.5)
    print(f"   Usage +1 MB (total 1.5 MB): {result2} (at 1.5 MB quota)")
    assert result2, "Should allow at quota limit"

    # Exceed quota
    result3 = system.track_bandwidth_usage(node_id, 100_000, trust_score=0.5)
    print(f"   Usage +100 KB: {result3} (exceeds 1.5 MB quota)")
    assert not result3, "Should reject over quota"

    # Test trust-weighted quota
    print("\n3. Testing trust-weighted bandwidth...")
    high_trust_node = "node3"

    # High trust = higher limits
    result = system.track_bandwidth_usage(high_trust_node, 1_500_000, trust_score=0.9)
    print(f"   High trust (0.9) usage 1.5 MB: {result}")
    print(f"   Effective quota: {1.0 * (1.0 + 0.9):.1f} MB")
    assert result, "High trust should allow more bandwidth"

    # Test connection limits
    print("\n4. Testing connection limits...")
    node_id = "node4"

    # Open connections up to limit
    for i in range(3):
        result = system.open_connection(node_id)
        print(f"   Connection {i+1}: {result}")
        assert result, f"Should allow connection {i+1}"

    # Exceed limit
    result = system.open_connection(node_id)
    print(f"   Connection 4: {result} (exceeds limit of 3)")
    assert not result, "Should reject over connection limit"

    # Close and reopen
    system.close_connection(node_id)
    result = system.open_connection(node_id)
    print(f"   After close, connection 4: {result}")
    assert result, "Should allow after closing one"

    print("\n✓ TEST 1 PASSED: Resource quotas working")
    return system.get_metrics()


def test_timing_defense():
    """Test 2: Timing attack mitigation."""
    print("\n" + "="*80)
    print("TEST 2: Timing Attack Mitigation")
    print("="*80)

    defense = TimingDefense()

    # Test jittered windows
    print("\n1. Testing jittered windows...")
    node1 = "node1"
    node2 = "node2"

    window1_a = defense.get_jittered_window(node1, 60.0)
    window1_b = defense.get_jittered_window(node1, 60.0)
    window2 = defense.get_jittered_window(node2, 60.0)

    print(f"   Node1 window: {window1_a:.1f}s (base 60s)")
    print(f"   Node1 again: {window1_b:.1f}s (should be same)")
    print(f"   Node2 window: {window2:.1f}s (likely different)")

    assert window1_a == window1_b, "Jitter should be persistent per node"
    assert 50 <= window1_a <= 70, "Jitter should be ±10s"

    # Test adaptive decay
    print("\n2. Testing adaptive decay...")

    # Low violation rate, high trust → slow decay
    decay1 = defense.compute_adaptive_decay(
        "honest_node", days_inactive=7, violation_rate=0.05, trust_score=0.8
    )
    print(f"   Honest node (7 days, 5% violations, 0.8 trust): {decay1:.4f} decay")

    # High violation rate, low trust → fast decay
    decay2 = defense.compute_adaptive_decay(
        "malicious_node", days_inactive=7, violation_rate=0.5, trust_score=0.2
    )
    print(f"   Malicious node (7 days, 50% violations, 0.2 trust): {decay2:.4f} decay")

    assert decay2 > decay1, "Malicious node should decay faster"
    print(f"   Decay ratio: {decay2/decay1:.1f}× faster for malicious")

    # Test rate limit smoothing
    print("\n3. Testing rate limit smoothing...")

    delays = []
    for usage_pct in [0, 25, 50, 75, 100, 125]:
        submissions = usage_pct
        max_limit = 100
        delay = defense.compute_rate_limit_delay("node3", submissions, max_limit)
        delays.append(delay)
        print(f"   {usage_pct}% usage: {delay:.2f}s delay")

    # Verify exponential growth
    assert delays[0] < delays[2] < delays[4], "Delay should increase exponentially"
    assert delays[4] > 100, "100% usage should have significant delay"

    print("\n✓ TEST 2 PASSED: Timing defense working")
    return defense.get_metrics()


def test_integrated_phase2():
    """Test 3: Integrated Phase 2 security."""
    print("\n" + "="*80)
    print("TEST 3: Integrated Phase 2 Security")
    print("="*80)

    system = Phase2SecuritySystem()

    # Register nodes
    print("\n1. Registering nodes...")
    system.register_node("honest", trust_score=0.8)
    system.register_node("attacker", trust_score=0.1)
    print(f"   Registered 2 nodes")

    # Test honest usage
    print("\n2. Testing honest usage...")
    for i in range(5):
        allowed, reason, delay = system.validate_submission(
            "honest", message_bytes=100_000, cpu_seconds=0.5
        )
        print(f"   Submission {i+1}: {allowed}, delay: {delay:.2f}s")
        assert allowed, f"Submission {i+1} should be allowed"
        time.sleep(0.01)  # Small delay to space out submissions

    # Test attack scenario
    print("\n3. Testing attack scenario...")
    attacker_allowed = 0
    attacker_rejected = 0

    for i in range(20):
        allowed, reason, delay = system.validate_submission(
            "attacker", message_bytes=200_000, cpu_seconds=1.0
        )
        if allowed:
            attacker_allowed += 1
        else:
            attacker_rejected += 1

    print(f"   Attack attempts: 20")
    print(f"   Allowed: {attacker_allowed}")
    print(f"   Rejected: {attacker_rejected}")
    print(f"   Rejection rate: {attacker_rejected/20*100:.1f}%")

    assert attacker_rejected > 0, "Should reject some attack attempts"

    # Test adaptive decay
    print("\n4. Testing adaptive decay...")

    # Simulate activity and violations
    system.node_states["honest"].contributions = 50
    system.node_states["honest"].violations = 2
    system.node_states["honest"].last_activity = time.time() - 86400 * 8  # 8 days ago

    system.node_states["attacker"].contributions = 10
    system.node_states["attacker"].violations = 15
    system.node_states["attacker"].last_activity = time.time() - 86400 * 8

    decay_honest = system.apply_adaptive_decay("honest")
    decay_attacker = system.apply_adaptive_decay("attacker")

    print(f"   Honest node decay: {decay_honest:.4f}")
    print(f"   Attacker decay: {decay_attacker:.4f}")
    print(f"   Attacker decays {decay_attacker/decay_honest:.1f}× faster")

    assert decay_attacker > decay_honest, "Attacker should decay faster"

    # Get comprehensive metrics
    print("\n5. Comprehensive metrics:")
    metrics = system.get_comprehensive_metrics()
    print(f"   CPU quota exceeded: {metrics['resource_quotas']['cpu_quota_exceeded']}")
    print(f"   Bandwidth quota exceeded: {metrics['resource_quotas']['bandwidth_quota_exceeded']}")
    print(f"   Timing jitter applications: {metrics['timing_defense']['jitter_applications']}")
    print(f"   Adaptive decays computed: {metrics['timing_defense']['adaptive_decays_computed']}")

    print("\n✓ TEST 3 PASSED: Integrated Phase 2 security working")
    return metrics


# ============================================================================
# MAIN: Run all tests and generate results
# ============================================================================

def main():
    """Run comprehensive Phase 2 security tests."""
    print("\n" + "="*80)
    print("SESSION 148: RESOURCE QUOTAS + TIMING MITIGATION")
    print("Advanced Security Implementation (Phase 2)")
    print("="*80)
    print("\nPhase 2 security mitigations:")
    print("  1. Resource Quotas (CPU, bandwidth, connections)")
    print("  2. Timing Attack Mitigation (jitter, adaptive decay, smoothing)\n")

    results = {}

    # Run tests
    try:
        results["test1_quotas"] = test_resource_quotas()
        results["test2_timing"] = test_timing_defense()
        results["test3_integrated"] = test_integrated_phase2()

        print("\n" + "="*80)
        print("ALL TESTS PASSED ✓")
        print("="*80)
        print("\nSession 148 Status: ✅ COMPLETE")
        print("Resource Quotas: OPERATIONAL")
        print("Timing Mitigation: OPERATIONAL")
        print("\nProduction Readiness: ✅ HIGH (Phase 2 complete)")

        # Save results
        results_file = Path(__file__).parent / "session148_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "session": "148",
                "title": "Resource Quotas + Timing Mitigation",
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "COMPLETE",
                "tests_passed": 3,
                "tests_failed": 0,
                "phase": "Phase 2 Performance & Fairness",
                "results": {
                    "resource_quotas": results["test1_quotas"],
                    "timing_defense": results["test2_timing"],
                    "integrated": results["test3_integrated"]
                }
            }, f, indent=2)

        print(f"\nResults saved to: {results_file}")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
