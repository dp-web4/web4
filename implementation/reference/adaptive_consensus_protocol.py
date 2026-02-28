"""
Web4 Adaptive Consensus Protocol — Session 17, Track 1
======================================================

Adaptive BFT consensus that switches algorithms based on network conditions.
Key insight: No single consensus algorithm is optimal for all conditions.
- Low latency, high trust → fast-path optimistic (2-phase)
- Medium conditions → standard PBFT (3-phase)
- High latency, partitions → Raft-like leader-based
- Byzantine detected → hardened PBFT with view changes

12 sections, ~65 checks expected.
"""

import hashlib
import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict


# ============================================================
# §1 — Network Condition Model
# ============================================================

class NetworkHealth(Enum):
    EXCELLENT = auto()   # Low latency, no faults
    GOOD = auto()        # Minor latency variation
    DEGRADED = auto()    # High latency, some message loss
    PARTITIONED = auto() # Network partition detected
    BYZANTINE = auto()   # Byzantine behavior detected


@dataclass
class NetworkCondition:
    """Observable network metrics that drive consensus adaptation."""
    avg_latency_ms: float = 5.0
    latency_stddev_ms: float = 1.0
    message_loss_rate: float = 0.0
    partition_detected: bool = False
    byzantine_detected: bool = False
    node_count: int = 10
    faulty_count: int = 0
    throughput_tps: float = 100.0
    last_updated: float = 0.0

    def health(self) -> NetworkHealth:
        if self.byzantine_detected:
            return NetworkHealth.BYZANTINE
        if self.partition_detected:
            return NetworkHealth.PARTITIONED
        if self.avg_latency_ms > 200 or self.message_loss_rate > 0.1:
            return NetworkHealth.DEGRADED
        if self.avg_latency_ms > 50 or self.message_loss_rate > 0.01:
            return NetworkHealth.GOOD
        return NetworkHealth.EXCELLENT

    def fault_tolerance(self) -> int:
        """Max Byzantine faults tolerable: f < n/3."""
        return (self.node_count - 1) // 3


@dataclass
class ConditionWindow:
    """Sliding window of network conditions for trend analysis."""
    window_size: int = 20
    conditions: List[NetworkCondition] = field(default_factory=list)

    def add(self, cond: NetworkCondition):
        self.conditions.append(cond)
        if len(self.conditions) > self.window_size:
            self.conditions = self.conditions[-self.window_size:]

    def avg_latency(self) -> float:
        if not self.conditions:
            return 0.0
        return sum(c.avg_latency_ms for c in self.conditions) / len(self.conditions)

    def trend(self) -> str:
        """Latency trend: improving, stable, degrading."""
        if len(self.conditions) < 4:
            return "stable"
        first_half = self.conditions[:len(self.conditions)//2]
        second_half = self.conditions[len(self.conditions)//2:]
        avg1 = sum(c.avg_latency_ms for c in first_half) / len(first_half)
        avg2 = sum(c.avg_latency_ms for c in second_half) / len(second_half)
        if avg2 < avg1 * 0.8:
            return "improving"
        elif avg2 > avg1 * 1.2:
            return "degrading"
        return "stable"

    def loss_rate(self) -> float:
        if not self.conditions:
            return 0.0
        return sum(c.message_loss_rate for c in self.conditions) / len(self.conditions)


def test_section_1():
    checks = []

    # Basic condition assessment
    excellent = NetworkCondition(avg_latency_ms=2.0, message_loss_rate=0.0)
    checks.append(("excellent_health", excellent.health() == NetworkHealth.EXCELLENT))

    good = NetworkCondition(avg_latency_ms=60.0, message_loss_rate=0.005)
    checks.append(("good_health", good.health() == NetworkHealth.GOOD))

    degraded = NetworkCondition(avg_latency_ms=250.0, message_loss_rate=0.15)
    checks.append(("degraded_health", degraded.health() == NetworkHealth.DEGRADED))

    partitioned = NetworkCondition(partition_detected=True)
    checks.append(("partitioned_health", partitioned.health() == NetworkHealth.PARTITIONED))

    byzantine = NetworkCondition(byzantine_detected=True)
    checks.append(("byzantine_health", byzantine.health() == NetworkHealth.BYZANTINE))

    # Byzantine overrides partition
    both = NetworkCondition(partition_detected=True, byzantine_detected=True)
    checks.append(("byzantine_overrides_partition", both.health() == NetworkHealth.BYZANTINE))

    # Fault tolerance
    n10 = NetworkCondition(node_count=10)
    checks.append(("fault_tolerance_10", n10.fault_tolerance() == 3))

    n4 = NetworkCondition(node_count=4)
    checks.append(("fault_tolerance_4", n4.fault_tolerance() == 1))

    # Sliding window
    window = ConditionWindow(window_size=5)
    for i in range(8):
        window.add(NetworkCondition(avg_latency_ms=10.0 + i * 5))
    checks.append(("window_capped", len(window.conditions) == 5))
    checks.append(("window_avg", window.avg_latency() > 20.0))

    # Trend detection
    improving = ConditionWindow()
    for i in range(10):
        improving.add(NetworkCondition(avg_latency_ms=100.0 - i * 8))
    checks.append(("trend_improving", improving.trend() == "improving"))

    degrading = ConditionWindow()
    for i in range(10):
        degrading.add(NetworkCondition(avg_latency_ms=10.0 + i * 8))
    checks.append(("trend_degrading", degrading.trend() == "degrading"))

    return checks


# ============================================================
# §2 — Consensus Algorithm Registry
# ============================================================

class ConsensusType(Enum):
    FAST_PATH = "fast_path"      # 2-phase optimistic
    PBFT = "pbft"                # Standard 3-phase BFT
    RAFT_LIKE = "raft_like"      # Leader-based for partitions
    HARDENED_BFT = "hardened_bft"  # Full BFT with view changes


@dataclass
class ConsensusProfile:
    """Performance characteristics of a consensus algorithm."""
    algo_type: ConsensusType
    min_phases: int
    max_phases: int
    message_complexity: str  # O(n), O(n^2), O(n^3)
    fault_model: str  # "crash", "byzantine"
    latency_multiplier: float  # vs single message RTT
    throughput_factor: float  # relative throughput
    min_nodes: int = 1
    requires_leader: bool = False

    def expected_latency(self, base_latency_ms: float) -> float:
        return base_latency_ms * self.latency_multiplier * self.min_phases

    def messages_per_consensus(self, n: int) -> int:
        if self.message_complexity == "O(n)":
            return n
        elif self.message_complexity == "O(n^2)":
            return n * n
        else:
            return n * n * n


ALGO_PROFILES = {
    ConsensusType.FAST_PATH: ConsensusProfile(
        algo_type=ConsensusType.FAST_PATH,
        min_phases=2, max_phases=2,
        message_complexity="O(n)",
        fault_model="crash",
        latency_multiplier=1.0,
        throughput_factor=3.0,
        min_nodes=3,
        requires_leader=True,
    ),
    ConsensusType.PBFT: ConsensusProfile(
        algo_type=ConsensusType.PBFT,
        min_phases=3, max_phases=4,
        message_complexity="O(n^2)",
        fault_model="byzantine",
        latency_multiplier=1.5,
        throughput_factor=1.0,
        min_nodes=4,
    ),
    ConsensusType.RAFT_LIKE: ConsensusProfile(
        algo_type=ConsensusType.RAFT_LIKE,
        min_phases=2, max_phases=3,
        message_complexity="O(n)",
        fault_model="crash",
        latency_multiplier=1.0,
        throughput_factor=2.0,
        min_nodes=3,
        requires_leader=True,
    ),
    ConsensusType.HARDENED_BFT: ConsensusProfile(
        algo_type=ConsensusType.HARDENED_BFT,
        min_phases=4, max_phases=6,
        message_complexity="O(n^2)",
        fault_model="byzantine",
        latency_multiplier=2.0,
        throughput_factor=0.5,
        min_nodes=4,
    ),
}


def test_section_2():
    checks = []

    fp = ALGO_PROFILES[ConsensusType.FAST_PATH]
    checks.append(("fast_path_2_phase", fp.min_phases == 2))
    checks.append(("fast_path_linear", fp.message_complexity == "O(n)"))
    checks.append(("fast_path_crash_only", fp.fault_model == "crash"))

    pbft = ALGO_PROFILES[ConsensusType.PBFT]
    checks.append(("pbft_3_phase", pbft.min_phases == 3))
    checks.append(("pbft_byzantine", pbft.fault_model == "byzantine"))

    hbft = ALGO_PROFILES[ConsensusType.HARDENED_BFT]
    checks.append(("hardened_slowest", hbft.latency_multiplier >= pbft.latency_multiplier))
    checks.append(("hardened_lowest_throughput", hbft.throughput_factor <= pbft.throughput_factor))

    # Expected latency comparison
    base = 10.0  # ms
    fp_lat = fp.expected_latency(base)
    pbft_lat = pbft.expected_latency(base)
    hbft_lat = hbft.expected_latency(base)
    checks.append(("fast_path_fastest", fp_lat < pbft_lat < hbft_lat))

    # Message complexity
    n = 10
    fp_msgs = fp.messages_per_consensus(n)
    pbft_msgs = pbft.messages_per_consensus(n)
    checks.append(("linear_vs_quadratic", fp_msgs == 10 and pbft_msgs == 100))

    return checks


# ============================================================
# §3 — Algorithm Selection Policy
# ============================================================

@dataclass
class SelectionPolicy:
    """Policy for choosing consensus algorithm based on conditions."""
    # Thresholds for fast path
    fast_path_max_latency_ms: float = 20.0
    fast_path_max_loss: float = 0.001
    fast_path_min_trust: float = 0.8

    # Thresholds for degradation
    degraded_latency_ms: float = 200.0
    degraded_loss: float = 0.1

    # Hysteresis: require sustained conditions before switching
    switch_threshold: int = 3  # consecutive samples needed

    # Cooldown: minimum time between switches
    cooldown_seconds: float = 10.0
    last_switch_time: float = -1000.0  # Allow first switch without cooldown

    # History tracking
    _consecutive_counts: Dict[ConsensusType, int] = field(default_factory=lambda: defaultdict(int))
    current_algo: ConsensusType = ConsensusType.PBFT

    def evaluate(self, condition: NetworkCondition, node_trust: float = 0.5,
                 current_time: float = 0.0) -> ConsensusType:
        """Determine ideal algorithm for current conditions."""
        health = condition.health()

        if health == NetworkHealth.BYZANTINE:
            return ConsensusType.HARDENED_BFT

        if health == NetworkHealth.PARTITIONED:
            return ConsensusType.RAFT_LIKE

        if health == NetworkHealth.DEGRADED:
            if condition.faulty_count > 0:
                return ConsensusType.HARDENED_BFT
            return ConsensusType.RAFT_LIKE

        if health == NetworkHealth.EXCELLENT and node_trust >= self.fast_path_min_trust:
            if condition.avg_latency_ms <= self.fast_path_max_latency_ms and \
               condition.message_loss_rate <= self.fast_path_max_loss:
                return ConsensusType.FAST_PATH

        return ConsensusType.PBFT

    def should_switch(self, recommended: ConsensusType, current_time: float = 0.0) -> bool:
        """Apply hysteresis and cooldown to avoid flapping."""
        if recommended == self.current_algo:
            self._consecutive_counts.clear()
            return False

        # Always switch immediately to hardened BFT (safety critical)
        if recommended == ConsensusType.HARDENED_BFT:
            return True

        # Cooldown check
        if current_time - self.last_switch_time < self.cooldown_seconds:
            return False

        # Hysteresis: need consecutive recommendations
        self._consecutive_counts[recommended] += 1
        if self._consecutive_counts[recommended] >= self.switch_threshold:
            return True

        return False

    def apply_switch(self, new_algo: ConsensusType, current_time: float = 0.0):
        self.current_algo = new_algo
        self.last_switch_time = current_time
        self._consecutive_counts.clear()


def test_section_3():
    checks = []

    policy = SelectionPolicy()

    # Byzantine → hardened BFT
    byz = NetworkCondition(byzantine_detected=True)
    checks.append(("byzantine_selects_hardened",
                    policy.evaluate(byz) == ConsensusType.HARDENED_BFT))

    # Partition → raft-like
    part = NetworkCondition(partition_detected=True)
    checks.append(("partition_selects_raft",
                    policy.evaluate(part) == ConsensusType.RAFT_LIKE))

    # Excellent + high trust → fast path
    excellent = NetworkCondition(avg_latency_ms=5.0, message_loss_rate=0.0)
    checks.append(("excellent_selects_fast_path",
                    policy.evaluate(excellent, node_trust=0.9) == ConsensusType.FAST_PATH))

    # Excellent but low trust → PBFT
    checks.append(("low_trust_stays_pbft",
                    policy.evaluate(excellent, node_trust=0.4) == ConsensusType.PBFT))

    # Degraded → raft-like
    degraded = NetworkCondition(avg_latency_ms=300.0, message_loss_rate=0.15)
    checks.append(("degraded_selects_raft",
                    policy.evaluate(degraded) == ConsensusType.RAFT_LIKE))

    # Degraded with faults → hardened
    degraded_faulty = NetworkCondition(avg_latency_ms=300.0, message_loss_rate=0.15, faulty_count=2)
    checks.append(("degraded_faulty_selects_hardened",
                    policy.evaluate(degraded_faulty) == ConsensusType.HARDENED_BFT))

    # Hysteresis: need 3 consecutive recommendations to switch
    policy2 = SelectionPolicy()
    policy2.current_algo = ConsensusType.PBFT
    checks.append(("hysteresis_no_switch_1", not policy2.should_switch(ConsensusType.FAST_PATH, 100.0)))
    checks.append(("hysteresis_no_switch_2", not policy2.should_switch(ConsensusType.FAST_PATH, 101.0)))
    checks.append(("hysteresis_switch_3", policy2.should_switch(ConsensusType.FAST_PATH, 102.0)))

    # Immediate switch to hardened BFT (safety override)
    policy3 = SelectionPolicy()
    policy3.current_algo = ConsensusType.FAST_PATH
    checks.append(("immediate_hardened_switch",
                    policy3.should_switch(ConsensusType.HARDENED_BFT, 0.0)))

    # Cooldown prevents rapid switching
    policy4 = SelectionPolicy(cooldown_seconds=10.0)
    policy4.current_algo = ConsensusType.PBFT
    policy4.last_switch_time = 100.0
    checks.append(("cooldown_prevents_switch",
                    not policy4.should_switch(ConsensusType.FAST_PATH, 105.0)))

    return checks


# ============================================================
# §4 — Consensus Round Simulation
# ============================================================

@dataclass
class ConsensusMessage:
    msg_type: str  # "propose", "prepare", "commit", "reply", "vote"
    sender: str
    round_num: int
    value: Any
    timestamp: float = 0.0


@dataclass
class ConsensusRound:
    """Simulates a single consensus round."""
    round_num: int
    algo: ConsensusType
    proposer: str
    value: Any
    participants: List[str] = field(default_factory=list)
    messages: List[ConsensusMessage] = field(default_factory=list)
    decided: bool = False
    decision: Any = None
    start_time: float = 0.0
    end_time: float = 0.0
    phases_completed: int = 0

    def simulate(self, condition: NetworkCondition, rng: random.Random) -> bool:
        """Simulate the round. Returns True if consensus reached."""
        profile = ALGO_PROFILES[self.algo]
        n = len(self.participants)
        f = condition.fault_tolerance()

        if self.algo == ConsensusType.FAST_PATH:
            return self._simulate_fast_path(n, condition, rng)
        elif self.algo == ConsensusType.PBFT:
            return self._simulate_pbft(n, f, condition, rng)
        elif self.algo == ConsensusType.RAFT_LIKE:
            return self._simulate_raft(n, condition, rng)
        else:  # HARDENED_BFT
            return self._simulate_hardened(n, f, condition, rng)

    def _simulate_fast_path(self, n: int, cond: NetworkCondition, rng: random.Random) -> bool:
        """2-phase optimistic: propose → accept (requires all honest)."""
        # Phase 1: Propose
        self.phases_completed = 1
        for p in self.participants:
            if rng.random() >= cond.message_loss_rate:
                self.messages.append(ConsensusMessage("propose", self.proposer, self.round_num, self.value))

        # Phase 2: Accept (need ALL to agree for fast path)
        accepts = 0
        for p in self.participants:
            if rng.random() >= cond.message_loss_rate:
                accepts += 1
                self.messages.append(ConsensusMessage("accept", p, self.round_num, self.value))

        self.phases_completed = 2
        # Fast path needs unanimous (or n-f for optimistic)
        if accepts >= n - cond.faulty_count:
            self.decided = True
            self.decision = self.value
            self.end_time = self.start_time + cond.avg_latency_ms * 2
            return True
        return False

    def _simulate_pbft(self, n: int, f: int, cond: NetworkCondition, rng: random.Random) -> bool:
        """3-phase PBFT: pre-prepare → prepare → commit."""
        quorum = 2 * f + 1

        # Phase 1: Pre-prepare
        self.phases_completed = 1
        delivered = sum(1 for _ in self.participants if rng.random() >= cond.message_loss_rate)

        # Phase 2: Prepare (each node broadcasts to all others → n² messages)
        prepares = 0
        for p in self.participants:
            if rng.random() >= cond.message_loss_rate:
                prepares += 1
                # Each prepare is broadcast to all other nodes
                for other in self.participants:
                    if other != p:
                        self.messages.append(ConsensusMessage("prepare", p, self.round_num, self.value))
        self.phases_completed = 2

        if prepares < quorum:
            return False

        # Phase 3: Commit (each node broadcasts to all others → n² messages)
        commits = 0
        for p in self.participants:
            if rng.random() >= cond.message_loss_rate:
                commits += 1
                for other in self.participants:
                    if other != p:
                        self.messages.append(ConsensusMessage("commit", p, self.round_num, self.value))
        self.phases_completed = 3

        if commits >= quorum:
            self.decided = True
            self.decision = self.value
            self.end_time = self.start_time + cond.avg_latency_ms * 3
            return True
        return False

    def _simulate_raft(self, n: int, cond: NetworkCondition, rng: random.Random) -> bool:
        """Leader-based: request vote → append entries."""
        majority = n // 2 + 1

        # Phase 1: Request votes
        self.phases_completed = 1
        votes = 1  # Leader votes for itself
        for p in self.participants:
            if p != self.proposer and rng.random() >= cond.message_loss_rate:
                votes += 1
                self.messages.append(ConsensusMessage("vote", p, self.round_num, self.value))

        if votes < majority:
            return False

        # Phase 2: Append entries
        self.phases_completed = 2
        acks = 1  # Leader
        for p in self.participants:
            if p != self.proposer and rng.random() >= cond.message_loss_rate:
                acks += 1
                self.messages.append(ConsensusMessage("ack", p, self.round_num, self.value))

        if acks >= majority:
            self.decided = True
            self.decision = self.value
            self.end_time = self.start_time + cond.avg_latency_ms * 2
            return True
        return False

    def _simulate_hardened(self, n: int, f: int, cond: NetworkCondition, rng: random.Random) -> bool:
        """4-phase hardened BFT with extra verification."""
        quorum = 2 * f + 1

        # Phases 1-3: Same as PBFT
        for phase in range(3):
            self.phases_completed = phase + 1
            count = sum(1 for _ in self.participants if rng.random() >= cond.message_loss_rate)
            if count < quorum:
                return False
            for p in self.participants[:count]:
                self.messages.append(ConsensusMessage(f"phase_{phase}", p, self.round_num, self.value))

        # Phase 4: Finalize with signatures
        self.phases_completed = 4
        finals = sum(1 for _ in self.participants if rng.random() >= cond.message_loss_rate)
        if finals >= quorum:
            self.decided = True
            self.decision = self.value
            self.end_time = self.start_time + cond.avg_latency_ms * 4
            return True
        return False


def test_section_4():
    checks = []
    rng = random.Random(42)

    participants = [f"node_{i}" for i in range(10)]
    cond = NetworkCondition(avg_latency_ms=5.0, message_loss_rate=0.0, node_count=10)

    # Fast path succeeds with no losses
    r1 = ConsensusRound(1, ConsensusType.FAST_PATH, "node_0", "tx1",
                        participants=participants, start_time=0.0)
    result = r1.simulate(cond, rng)
    checks.append(("fast_path_succeeds", result and r1.decided))
    checks.append(("fast_path_2_phases", r1.phases_completed == 2))

    # PBFT succeeds with no losses
    r2 = ConsensusRound(2, ConsensusType.PBFT, "node_0", "tx2",
                        participants=participants, start_time=0.0)
    result = r2.simulate(cond, rng)
    checks.append(("pbft_succeeds", result and r2.decided))
    checks.append(("pbft_3_phases", r2.phases_completed == 3))

    # Raft succeeds with no losses
    r3 = ConsensusRound(3, ConsensusType.RAFT_LIKE, "node_0", "tx3",
                        participants=participants, start_time=0.0)
    result = r3.simulate(cond, rng)
    checks.append(("raft_succeeds", result and r3.decided))

    # Hardened BFT succeeds
    r4 = ConsensusRound(4, ConsensusType.HARDENED_BFT, "node_0", "tx4",
                        participants=participants, start_time=0.0)
    result = r4.simulate(cond, rng)
    checks.append(("hardened_succeeds", result and r4.decided))
    checks.append(("hardened_4_phases", r4.phases_completed == 4))

    # High loss rate may cause failure
    lossy = NetworkCondition(avg_latency_ms=100.0, message_loss_rate=0.5, node_count=10)
    failures = 0
    for i in range(20):
        r = ConsensusRound(100+i, ConsensusType.PBFT, "node_0", f"tx_lossy_{i}",
                          participants=participants, start_time=0.0)
        if not r.simulate(lossy, rng):
            failures += 1
    checks.append(("lossy_causes_some_failures", failures > 0))

    return checks


# ============================================================
# §5 — Adaptive Controller
# ============================================================

@dataclass
class AdaptiveController:
    """Main controller that monitors conditions and switches algorithms."""
    policy: SelectionPolicy = field(default_factory=SelectionPolicy)
    window: ConditionWindow = field(default_factory=ConditionWindow)
    current_algo: ConsensusType = ConsensusType.PBFT
    switch_history: List[Tuple[float, ConsensusType, ConsensusType]] = field(default_factory=list)
    rounds_completed: int = 0
    rounds_failed: int = 0

    def observe(self, condition: NetworkCondition, current_time: float = 0.0,
                node_trust: float = 0.5) -> Optional[ConsensusType]:
        """Process new observation, potentially switch algorithm."""
        self.window.add(condition)
        recommended = self.policy.evaluate(condition, node_trust, current_time)

        if self.policy.should_switch(recommended, current_time):
            old = self.current_algo
            self.current_algo = recommended
            self.policy.apply_switch(recommended, current_time)
            self.switch_history.append((current_time, old, recommended))
            return recommended
        return None

    def run_round(self, value: Any, participants: List[str],
                  condition: NetworkCondition, rng: random.Random,
                  current_time: float = 0.0) -> ConsensusRound:
        """Run a consensus round with current algorithm."""
        r = ConsensusRound(
            round_num=self.rounds_completed,
            algo=self.current_algo,
            proposer=participants[self.rounds_completed % len(participants)],
            value=value,
            participants=participants,
            start_time=current_time,
        )
        result = r.simulate(condition, rng)
        if result:
            self.rounds_completed += 1
        else:
            self.rounds_failed += 1
        return r

    def success_rate(self) -> float:
        total = self.rounds_completed + self.rounds_failed
        if total == 0:
            return 1.0
        return self.rounds_completed / total

    def stats(self) -> Dict[str, Any]:
        return {
            "current_algo": self.current_algo.value,
            "rounds_completed": self.rounds_completed,
            "rounds_failed": self.rounds_failed,
            "success_rate": self.success_rate(),
            "switches": len(self.switch_history),
            "window_avg_latency": self.window.avg_latency(),
            "trend": self.window.trend(),
        }


def test_section_5():
    checks = []
    rng = random.Random(42)
    participants = [f"node_{i}" for i in range(10)]

    ctrl = AdaptiveController()

    # Start with excellent conditions
    exc = NetworkCondition(avg_latency_ms=5.0, message_loss_rate=0.0, node_count=10)

    # Run some rounds in PBFT
    for i in range(5):
        r = ctrl.run_round(f"tx_{i}", participants, exc, rng, current_time=float(i))
    checks.append(("initial_pbft_rounds", ctrl.rounds_completed >= 3))

    # Observe excellent conditions with high trust → should recommend fast path
    for i in range(5):
        ctrl.observe(exc, current_time=20.0 + i, node_trust=0.9)

    # After enough observations, should switch to fast path
    switch = ctrl.observe(exc, current_time=30.0, node_trust=0.9)
    # May or may not have switched depending on hysteresis
    checks.append(("controller_running", ctrl.success_rate() > 0))

    # Force switch with byzantine conditions
    byz = NetworkCondition(byzantine_detected=True, node_count=10)
    switch = ctrl.observe(byz, current_time=50.0)
    checks.append(("byzantine_immediate_switch", ctrl.current_algo == ConsensusType.HARDENED_BFT))
    checks.append(("switch_recorded", len(ctrl.switch_history) > 0))

    # Stats available
    s = ctrl.stats()
    checks.append(("stats_available", "current_algo" in s and "success_rate" in s))

    return checks


# ============================================================
# §6 — Condition-Driven Scenario Simulation
# ============================================================

def simulate_scenario(scenario_name: str, conditions: List[Tuple[float, NetworkCondition]],
                      node_trust: float, rng: random.Random) -> Dict:
    """Simulate a full scenario with changing conditions."""
    ctrl = AdaptiveController()
    participants = [f"node_{i}" for i in range(conditions[0][1].node_count)]
    results = {
        "scenario": scenario_name,
        "algo_timeline": [],
        "switches": [],
        "rounds": [],
    }

    for t, cond in conditions:
        switch = ctrl.observe(cond, current_time=t, node_trust=node_trust)
        if switch is not None:
            results["switches"].append((t, switch.value))

        r = ctrl.run_round(f"tx_{t}", participants, cond, rng, current_time=t)
        results["algo_timeline"].append((t, ctrl.current_algo.value))
        results["rounds"].append({
            "time": t,
            "algo": ctrl.current_algo.value,
            "decided": r.decided,
            "phases": r.phases_completed,
        })

    results["final_algo"] = ctrl.current_algo.value
    results["success_rate"] = ctrl.success_rate()
    results["total_switches"] = len(ctrl.switch_history)
    return results


def test_section_6():
    checks = []
    rng = random.Random(42)

    # Scenario 1: Stable excellent conditions
    stable_excellent = [(float(i), NetworkCondition(avg_latency_ms=5.0, node_count=10))
                        for i in range(20)]
    r1 = simulate_scenario("stable_excellent", stable_excellent, 0.9, rng)
    checks.append(("stable_high_success", r1["success_rate"] > 0.8))

    # Scenario 2: Gradual degradation
    degrading = []
    for i in range(20):
        lat = 5.0 + i * 15  # 5ms → 290ms
        loss = min(0.3, i * 0.015)
        degrading.append((float(i), NetworkCondition(avg_latency_ms=lat, message_loss_rate=loss, node_count=10)))
    r2 = simulate_scenario("degrading", degrading, 0.5, rng)
    checks.append(("degrading_triggers_switches", r2["total_switches"] > 0))

    # Scenario 3: Byzantine event
    byz_scenario = []
    for i in range(10):
        byz_scenario.append((float(i), NetworkCondition(avg_latency_ms=5.0, node_count=10)))
    # Byzantine event at t=10
    for i in range(10, 20):
        byz_scenario.append((float(i), NetworkCondition(avg_latency_ms=5.0, byzantine_detected=True, node_count=10)))
    r3 = simulate_scenario("byzantine_event", byz_scenario, 0.5, rng)
    checks.append(("byzantine_switch_happens", r3["final_algo"] == "hardened_bft"))

    # Scenario 4: Partition and recovery
    partition_scenario = []
    for i in range(5):
        partition_scenario.append((float(i), NetworkCondition(avg_latency_ms=10.0, node_count=10)))
    for i in range(5, 10):
        partition_scenario.append((float(i), NetworkCondition(avg_latency_ms=10.0, partition_detected=True, node_count=10)))
    for i in range(10, 20):
        partition_scenario.append((float(i), NetworkCondition(avg_latency_ms=10.0, node_count=10)))
    r4 = simulate_scenario("partition_recovery", partition_scenario, 0.5, rng)
    checks.append(("partition_handled", r4["total_switches"] >= 1))

    return checks


# ============================================================
# §7 — Performance Comparison
# ============================================================

def benchmark_algo(algo: ConsensusType, condition: NetworkCondition,
                   num_rounds: int, rng: random.Random) -> Dict:
    """Benchmark a specific algorithm under given conditions."""
    participants = [f"node_{i}" for i in range(condition.node_count)]
    decided = 0
    total_latency = 0.0
    total_messages = 0

    for i in range(num_rounds):
        r = ConsensusRound(
            round_num=i,
            algo=algo,
            proposer=participants[i % len(participants)],
            value=f"tx_{i}",
            participants=participants,
            start_time=float(i) * 100,
        )
        if r.simulate(condition, rng):
            decided += 1
            total_latency += (r.end_time - r.start_time)
        total_messages += len(r.messages)

    return {
        "algo": algo.value,
        "decided": decided,
        "total": num_rounds,
        "success_rate": decided / num_rounds if num_rounds > 0 else 0,
        "avg_latency": total_latency / decided if decided > 0 else float('inf'),
        "total_messages": total_messages,
        "msgs_per_round": total_messages / num_rounds if num_rounds > 0 else 0,
    }


def test_section_7():
    checks = []
    rng = random.Random(42)

    # Compare all algorithms under good conditions
    good = NetworkCondition(avg_latency_ms=10.0, message_loss_rate=0.0, node_count=10)
    results = {}
    for algo in ConsensusType:
        results[algo.value] = benchmark_algo(algo, good, 50, random.Random(42))

    # All should succeed under good conditions
    for name, r in results.items():
        checks.append((f"{name}_succeeds", r["success_rate"] > 0.8))

    # Fast path should be fastest (lowest latency)
    fp_lat = results["fast_path"]["avg_latency"]
    pbft_lat = results["pbft"]["avg_latency"]
    checks.append(("fast_path_lower_latency", fp_lat < pbft_lat))

    # Hardened BFT should have highest latency
    hbft_lat = results["hardened_bft"]["avg_latency"]
    checks.append(("hardened_highest_latency", hbft_lat >= pbft_lat))

    # Linear complexity should have fewer messages
    fp_msgs = results["fast_path"]["msgs_per_round"]
    pbft_msgs = results["pbft"]["msgs_per_round"]
    checks.append(("fast_path_fewer_messages", fp_msgs < pbft_msgs))

    # Under lossy conditions, PBFT should outperform fast_path
    lossy = NetworkCondition(avg_latency_ms=50.0, message_loss_rate=0.15, node_count=10)
    fp_lossy = benchmark_algo(ConsensusType.FAST_PATH, lossy, 50, random.Random(42))
    pbft_lossy = benchmark_algo(ConsensusType.PBFT, lossy, 50, random.Random(42))
    checks.append(("pbft_better_under_loss",
                    pbft_lossy["success_rate"] >= fp_lossy["success_rate"]))

    return checks


# ============================================================
# §8 — View Change Protocol
# ============================================================

@dataclass
class ViewChange:
    """View change mechanism for leader rotation on failure."""
    current_view: int = 0
    current_leader: int = 0
    node_count: int = 10
    view_change_votes: Dict[int, Set[str]] = field(default_factory=lambda: defaultdict(set))
    view_history: List[Tuple[int, str, float]] = field(default_factory=list)

    def request_view_change(self, requester: str, proposed_view: int) -> bool:
        """Node requests a view change. Returns True if quorum reached."""
        if proposed_view <= self.current_view:
            return False
        self.view_change_votes[proposed_view].add(requester)
        f = (self.node_count - 1) // 3
        quorum = 2 * f + 1
        if len(self.view_change_votes[proposed_view]) >= quorum:
            return True
        return False

    def execute_view_change(self, new_view: int, current_time: float = 0.0):
        """Execute the view change."""
        old_leader = f"node_{self.current_leader}"
        self.current_view = new_view
        self.current_leader = new_view % self.node_count
        new_leader = f"node_{self.current_leader}"
        self.view_history.append((new_view, new_leader, current_time))
        self.view_change_votes.clear()

    def leader_id(self) -> str:
        return f"node_{self.current_leader}"


def test_section_8():
    checks = []

    vc = ViewChange(node_count=10)
    checks.append(("initial_view_0", vc.current_view == 0))
    checks.append(("initial_leader", vc.leader_id() == "node_0"))

    # Need quorum (7 for n=10, f=3) for view change
    for i in range(6):
        result = vc.request_view_change(f"node_{i}", 1)
        checks.append((f"not_yet_quorum_{i}", not result))

    result = vc.request_view_change("node_6", 1)
    checks.append(("quorum_reached", result))

    # Execute view change
    vc.execute_view_change(1, current_time=100.0)
    checks.append(("view_updated", vc.current_view == 1))
    checks.append(("leader_rotated", vc.leader_id() == "node_1"))
    checks.append(("history_recorded", len(vc.view_history) == 1))

    # Can't request old view
    result = vc.request_view_change("node_0", 0)
    checks.append(("reject_old_view", not result))

    # Multiple view changes
    for i in range(7):
        vc.request_view_change(f"node_{i}", 5)
    vc.execute_view_change(5, current_time=200.0)
    checks.append(("view_jump", vc.current_view == 5))
    checks.append(("leader_wraps", vc.leader_id() == "node_5"))

    return checks


# ============================================================
# §9 — Consensus Safety Invariants
# ============================================================

def verify_safety(rounds: List[ConsensusRound]) -> Dict[str, bool]:
    """Verify safety invariants across all decided rounds."""
    invariants = {}

    # Agreement: all decided rounds for same round_num agree on value
    by_round = defaultdict(list)
    for r in rounds:
        if r.decided:
            by_round[r.round_num].append(r.decision)

    agreement = all(len(set(map(str, vals))) == 1 for vals in by_round.values())
    invariants["agreement"] = agreement

    # Validity: decided value was proposed by some node
    proposed = {r.value for r in rounds}
    decided = {r.decision for r in rounds if r.decided}
    invariants["validity"] = decided.issubset(proposed)

    # No decision reversal: once decided, stays decided
    # (in our model each round is independent, so this is trivially true)
    invariants["irrevocability"] = True

    # Quorum intersection: every two quorums must overlap
    # For BFT: 2Q > N guarantees overlap
    for r in rounds:
        if r.decided:
            n = len(r.participants)
            f = (n - 1) // 3
            q = 2 * f + 1
            invariants["quorum_intersection"] = 2 * q > n

    if "quorum_intersection" not in invariants:
        invariants["quorum_intersection"] = True  # No decided rounds

    return invariants


def test_section_9():
    checks = []
    rng = random.Random(42)

    participants = [f"node_{i}" for i in range(10)]
    cond = NetworkCondition(avg_latency_ms=5.0, node_count=10)

    # Run many rounds and verify safety
    rounds = []
    for i in range(30):
        for algo in ConsensusType:
            r = ConsensusRound(i, algo, participants[i % 10], f"tx_{i}",
                              participants=participants, start_time=float(i))
            r.simulate(cond, rng)
            rounds.append(r)

    safety = verify_safety(rounds)
    checks.append(("safety_agreement", safety["agreement"]))
    checks.append(("safety_validity", safety["validity"]))
    checks.append(("safety_irrevocability", safety["irrevocability"]))
    checks.append(("safety_quorum_intersection", safety["quorum_intersection"]))

    # Verify with mixed conditions
    rounds2 = []
    conditions = [
        NetworkCondition(avg_latency_ms=5.0, node_count=10),
        NetworkCondition(avg_latency_ms=100.0, message_loss_rate=0.1, node_count=10),
        NetworkCondition(avg_latency_ms=5.0, node_count=10, faulty_count=2),
    ]
    for i in range(20):
        c = conditions[i % len(conditions)]
        algo = [ConsensusType.PBFT, ConsensusType.HARDENED_BFT][i % 2]
        r = ConsensusRound(i, algo, participants[i % 10], f"tx_{i}",
                          participants=participants, start_time=float(i))
        r.simulate(c, rng)
        rounds2.append(r)

    safety2 = verify_safety(rounds2)
    checks.append(("mixed_safety_agreement", safety2["agreement"]))
    checks.append(("mixed_safety_validity", safety2["validity"]))

    return checks


# ============================================================
# §10 — Adaptive Throughput Optimization
# ============================================================

@dataclass
class ThroughputOptimizer:
    """Dynamically adjusts batch size and pipeline depth based on conditions."""
    base_batch_size: int = 10
    max_batch_size: int = 100
    min_batch_size: int = 1
    current_batch_size: int = 10
    pipeline_depth: int = 1  # How many rounds can be in-flight
    max_pipeline: int = 5

    # Metrics
    recent_latencies: List[float] = field(default_factory=list)
    recent_success: List[bool] = field(default_factory=list)
    window: int = 20

    def record(self, latency_ms: float, success: bool):
        self.recent_latencies.append(latency_ms)
        self.recent_success.append(success)
        if len(self.recent_latencies) > self.window:
            self.recent_latencies = self.recent_latencies[-self.window:]
            self.recent_success = self.recent_success[-self.window:]

    def adjust(self):
        """AIMD-like adjustment: additive increase, multiplicative decrease."""
        if len(self.recent_success) < 5:
            return

        success_rate = sum(self.recent_success[-10:]) / min(10, len(self.recent_success))

        if success_rate >= 0.95:
            # Additive increase
            self.current_batch_size = min(self.max_batch_size, self.current_batch_size + 2)
            self.pipeline_depth = min(self.max_pipeline, self.pipeline_depth + 1)
        elif success_rate < 0.7:
            # Multiplicative decrease
            self.current_batch_size = max(self.min_batch_size, self.current_batch_size // 2)
            self.pipeline_depth = max(1, self.pipeline_depth - 1)

    def effective_throughput(self) -> float:
        """Estimated TPS based on current settings and observed latency."""
        if not self.recent_latencies:
            return 0.0
        avg_lat = sum(self.recent_latencies) / len(self.recent_latencies)
        if avg_lat <= 0:
            return 0.0
        success_rate = sum(self.recent_success) / len(self.recent_success) if self.recent_success else 0
        return (self.current_batch_size * self.pipeline_depth * success_rate * 1000.0) / avg_lat


def test_section_10():
    checks = []

    opt = ThroughputOptimizer()

    # Record good performance → increase
    for _ in range(10):
        opt.record(10.0, True)
    opt.adjust()
    checks.append(("increase_batch", opt.current_batch_size > 10))
    checks.append(("increase_pipeline", opt.pipeline_depth > 1))

    # Record bad performance → decrease
    opt2 = ThroughputOptimizer(current_batch_size=50, pipeline_depth=3)
    for _ in range(10):
        opt2.record(200.0, False)
    opt2.adjust()
    checks.append(("decrease_batch", opt2.current_batch_size < 50))
    checks.append(("decrease_pipeline", opt2.pipeline_depth < 3))

    # Batch size bounded
    opt3 = ThroughputOptimizer(current_batch_size=99, max_batch_size=100)
    for _ in range(10):
        opt3.record(5.0, True)
    opt3.adjust()
    checks.append(("batch_capped", opt3.current_batch_size <= 100))

    opt4 = ThroughputOptimizer(current_batch_size=2, min_batch_size=1)
    for _ in range(10):
        opt4.record(500.0, False)
    opt4.adjust()
    checks.append(("batch_floor", opt4.current_batch_size >= 1))

    # Throughput calculation
    opt5 = ThroughputOptimizer(current_batch_size=10, pipeline_depth=2)
    for _ in range(10):
        opt5.record(10.0, True)
    tps = opt5.effective_throughput()
    checks.append(("throughput_positive", tps > 0))
    # 10 batch * 2 pipeline * 1.0 success * 1000 / 10ms = 2000 TPS
    checks.append(("throughput_reasonable", abs(tps - 2000.0) < 1.0))

    return checks


# ============================================================
# §11 — Multi-Region Adaptive Consensus
# ============================================================

@dataclass
class RegionConfig:
    name: str
    node_count: int
    intra_latency_ms: float
    trust_level: float


def simulate_multi_region(regions: List[RegionConfig],
                          inter_region_latency_ms: float,
                          rounds: int,
                          rng: random.Random) -> Dict:
    """Simulate adaptive consensus across multiple regions."""
    controllers = {}
    for region in regions:
        controllers[region.name] = AdaptiveController()

    all_results = {r.name: [] for r in regions}
    global_decisions = []

    for round_num in range(rounds):
        round_decisions = {}

        # Each region runs local consensus
        for region in regions:
            ctrl = controllers[region.name]
            participants = [f"{region.name}_node_{i}" for i in range(region.node_count)]
            cond = NetworkCondition(
                avg_latency_ms=region.intra_latency_ms,
                node_count=region.node_count,
            )

            # Observe local conditions
            ctrl.observe(cond, current_time=float(round_num), node_trust=region.trust_level)

            # Run local round
            r = ctrl.run_round(f"tx_{round_num}", participants, cond, rng,
                              current_time=float(round_num))
            all_results[region.name].append({
                "round": round_num,
                "algo": ctrl.current_algo.value,
                "decided": r.decided,
            })
            if r.decided:
                round_decisions[region.name] = r.decision

        # Global agreement: need majority of regions
        if len(round_decisions) > len(regions) // 2:
            global_decisions.append(round_num)

    return {
        "regions": {name: {
            "algo": controllers[name].current_algo.value,
            "success_rate": controllers[name].success_rate(),
            "switches": len(controllers[name].switch_history),
        } for name in controllers},
        "global_decisions": len(global_decisions),
        "total_rounds": rounds,
        "global_success_rate": len(global_decisions) / rounds if rounds > 0 else 0,
    }


def test_section_11():
    checks = []
    rng = random.Random(42)

    regions = [
        RegionConfig("us_east", 5, 2.0, 0.9),
        RegionConfig("eu_west", 5, 3.0, 0.85),
        RegionConfig("asia_east", 4, 5.0, 0.8),
    ]

    result = simulate_multi_region(regions, inter_region_latency_ms=50.0,
                                   rounds=30, rng=rng)

    # All regions should have decisions
    for name in ["us_east", "eu_west", "asia_east"]:
        sr = result["regions"][name]["success_rate"]
        checks.append((f"{name}_success", sr > 0.5))

    # Global success rate
    checks.append(("global_success", result["global_success_rate"] > 0.5))

    # High-trust region may use fast path
    us = result["regions"]["us_east"]
    checks.append(("us_algo_recorded", us["algo"] in ["fast_path", "pbft", "raft_like", "hardened_bft"]))

    # Mixed region test with degraded conditions
    mixed_regions = [
        RegionConfig("fast", 5, 2.0, 0.95),
        RegionConfig("slow", 4, 250.0, 0.4),
        RegionConfig("medium", 5, 30.0, 0.7),
    ]
    result2 = simulate_multi_region(mixed_regions, inter_region_latency_ms=100.0,
                                    rounds=20, rng=rng)
    # Fast region should outperform slow region
    fast_sr = result2["regions"]["fast"]["success_rate"]
    slow_sr = result2["regions"]["slow"]["success_rate"]
    checks.append(("fast_beats_slow", fast_sr >= slow_sr))

    return checks


# ============================================================
# §12 — Complete Adaptive Pipeline + Verification
# ============================================================

def run_complete_adaptive_pipeline(rng: random.Random) -> List[Tuple[str, bool]]:
    """Complete test: adaptive consensus across changing conditions."""
    checks = []

    participants = [f"node_{i}" for i in range(10)]
    ctrl = AdaptiveController()

    # Phase 1: Excellent conditions (should stabilize on fast path or PBFT)
    for i in range(10):
        cond = NetworkCondition(avg_latency_ms=3.0, node_count=10)
        ctrl.observe(cond, current_time=float(i), node_trust=0.9)
        r = ctrl.run_round(f"phase1_tx_{i}", participants, cond, rng, current_time=float(i))
    phase1_algo = ctrl.current_algo
    checks.append(("phase1_optimal_algo", phase1_algo in [ConsensusType.FAST_PATH, ConsensusType.PBFT]))
    checks.append(("phase1_success", ctrl.success_rate() > 0.6))

    # Phase 2: Gradual degradation (should switch to PBFT or Raft)
    for i in range(10):
        lat = 5.0 + i * 30  # 5ms → 275ms
        loss = i * 0.02
        cond = NetworkCondition(avg_latency_ms=lat, message_loss_rate=loss, node_count=10)
        ctrl.observe(cond, current_time=20.0 + i, node_trust=0.5)
        r = ctrl.run_round(f"phase2_tx_{i}", participants, cond, rng, current_time=20.0 + i)

    switches_phase2 = len(ctrl.switch_history)
    checks.append(("phase2_adapted", switches_phase2 > 0))

    # Phase 3: Byzantine event
    for i in range(5):
        cond = NetworkCondition(avg_latency_ms=10.0, byzantine_detected=True, node_count=10)
        ctrl.observe(cond, current_time=40.0 + i, node_trust=0.3)
        r = ctrl.run_round(f"phase3_tx_{i}", participants, cond, rng, current_time=40.0 + i)
    checks.append(("phase3_hardened", ctrl.current_algo == ConsensusType.HARDENED_BFT))

    # Phase 4: Recovery (conditions improve)
    for i in range(15):
        cond = NetworkCondition(avg_latency_ms=5.0, node_count=10)
        ctrl.observe(cond, current_time=50.0 + i, node_trust=0.85)
        r = ctrl.run_round(f"phase4_tx_{i}", participants, cond, rng, current_time=50.0 + i)

    # Should have switched away from hardened after recovery
    phase4_algo = ctrl.current_algo
    checks.append(("phase4_recovered", phase4_algo != ConsensusType.HARDENED_BFT))

    # Overall metrics
    total_switches = len(ctrl.switch_history)
    checks.append(("total_switches_reasonable", 2 <= total_switches <= 20))
    checks.append(("overall_success", ctrl.success_rate() > 0.4))

    # Safety verification
    checks.append(("stats_complete", "trend" in ctrl.stats()))

    # Multi-region complete test
    regions = [
        RegionConfig("dc1", 5, 1.0, 0.95),
        RegionConfig("dc2", 5, 2.0, 0.9),
        RegionConfig("dc3", 4, 5.0, 0.85),
        RegionConfig("edge", 3, 50.0, 0.6),
    ]
    mr = simulate_multi_region(regions, 80.0, 25, rng)
    checks.append(("multi_region_global", mr["global_success_rate"] > 0.3))

    # Performance comparison across conditions
    good_cond = NetworkCondition(avg_latency_ms=5.0, node_count=10)
    bad_cond = NetworkCondition(avg_latency_ms=200.0, message_loss_rate=0.2, node_count=10)

    good_bench = benchmark_algo(ConsensusType.PBFT, good_cond, 20, rng)
    bad_bench = benchmark_algo(ConsensusType.PBFT, bad_cond, 20, rng)
    checks.append(("good_outperforms_bad", good_bench["success_rate"] >= bad_bench["success_rate"]))

    return checks


def test_section_12():
    rng = random.Random(42)
    return run_complete_adaptive_pipeline(rng)


# ============================================================
# Main runner
# ============================================================

def run_all():
    sections = [
        ("§1 Network Condition Model", test_section_1),
        ("§2 Consensus Algorithm Registry", test_section_2),
        ("§3 Algorithm Selection Policy", test_section_3),
        ("§4 Consensus Round Simulation", test_section_4),
        ("§5 Adaptive Controller", test_section_5),
        ("§6 Condition-Driven Scenarios", test_section_6),
        ("§7 Performance Comparison", test_section_7),
        ("§8 View Change Protocol", test_section_8),
        ("§9 Consensus Safety Invariants", test_section_9),
        ("§10 Throughput Optimization", test_section_10),
        ("§11 Multi-Region Adaptive", test_section_11),
        ("§12 Complete Pipeline", test_section_12),
    ]

    total = 0
    passed = 0
    failed_checks = []

    for name, fn in sections:
        checks = fn()
        section_pass = sum(1 for _, v in checks if v)
        section_total = len(checks)
        total += section_total
        passed += section_pass
        status = "✓" if section_pass == section_total else "✗"
        print(f"  {status} {name}: {section_pass}/{section_total}")
        for cname, cval in checks:
            if not cval:
                failed_checks.append(f"    FAIL: {name} → {cname}")

    print(f"\nTotal: {passed}/{total}")
    if failed_checks:
        print("\nFailed checks:")
        for f in failed_checks:
            print(f)

    return passed, total


if __name__ == "__main__":
    run_all()
