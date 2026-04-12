"""
Adaptive Attestation Scheduling for Web4
Session 31, Track 2

Dynamic scheduling of attestation events:
- Exponential backoff for stable entities
- Urgency-based scheduling (trust near thresholds)
- Load-aware scheduling (federation capacity)
- Priority queues with aging
- Batch optimization (group related attestations)
- Deadline-aware scheduling (time-critical contexts)
- Feedback-driven rate adaptation
"""

import math
import random
import heapq
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional


# ─── Scheduling Primitives ────────────────────────────────────────

class Priority(Enum):
    CRITICAL = 0    # trust below safety threshold
    HIGH = 1        # trust near threshold
    NORMAL = 2      # routine re-attestation
    LOW = 3         # stable entity, low urgency
    BACKGROUND = 4  # periodic maintenance


@dataclass(order=True)
class AttestationTask:
    priority: int = field(compare=True)
    deadline: int = field(compare=True)
    entity_id: str = field(compare=False)
    current_trust: float = field(compare=False)
    context: str = field(compare=False, default="routine")
    created_at: int = field(compare=False, default=0)
    age_bonus: float = field(compare=False, default=0.0)

    @property
    def effective_priority(self) -> float:
        """Priority with aging: older tasks get boosted."""
        return self.priority - self.age_bonus


# ─── Adaptive Scheduler ───────────────────────────────────────────

class AdaptiveScheduler:
    """
    Priority queue scheduler with adaptive intervals.
    """

    def __init__(self, capacity: int = 10, current_time: int = 0):
        self.queue: List[AttestationTask] = []
        self.capacity = capacity  # max concurrent attestations
        self.current_time = current_time
        self.completed: List[AttestationTask] = []
        self.entity_intervals: Dict[str, float] = {}  # entity → current interval
        self.entity_history: Dict[str, List[float]] = {}  # entity → trust history

    def schedule(self, task: AttestationTask):
        """Add task to priority queue."""
        task.created_at = self.current_time
        heapq.heappush(self.queue, task)

    def next_batch(self, batch_size: int = None) -> List[AttestationTask]:
        """Get next batch of tasks to execute."""
        if batch_size is None:
            batch_size = self.capacity

        batch = []
        while self.queue and len(batch) < batch_size:
            task = heapq.heappop(self.queue)
            # Apply aging
            age = self.current_time - task.created_at
            task.age_bonus = min(2.0, age * 0.01)  # cap at 2 priority levels
            batch.append(task)

        return batch

    def complete(self, task: AttestationTask, new_trust: float):
        """Record completion and update scheduling."""
        self.completed.append(task)

        # Update history
        if task.entity_id not in self.entity_history:
            self.entity_history[task.entity_id] = []
        self.entity_history[task.entity_id].append(new_trust)

        # Adapt interval based on trust stability
        interval = self.compute_interval(task.entity_id, new_trust)
        self.entity_intervals[task.entity_id] = interval

    def compute_interval(self, entity_id: str, current_trust: float) -> float:
        """
        Compute next attestation interval based on trust dynamics.

        Stable high trust → long interval (exponential backoff)
        Volatile or low trust → short interval
        Near threshold → very short interval
        """
        history = self.entity_history.get(entity_id, [])

        # Base interval
        base = 100.0

        # Trust level factor: lower trust → shorter interval
        trust_factor = max(0.1, current_trust)

        # Volatility factor
        if len(history) >= 3:
            recent = history[-3:]
            volatility = max(recent) - min(recent)
            vol_factor = max(0.2, 1.0 - volatility * 5)
        else:
            vol_factor = 0.5  # uncertain → moderate interval

        # Threshold proximity: shorter interval near 0.3 (minimum viable)
        threshold = 0.3
        proximity = abs(current_trust - threshold)
        if proximity < 0.1:
            proximity_factor = 0.2  # very close to threshold
        elif proximity < 0.2:
            proximity_factor = 0.5
        else:
            proximity_factor = 1.0

        interval = base * trust_factor * vol_factor * proximity_factor
        return max(5.0, min(1000.0, interval))

    def advance_time(self, ticks: int = 1):
        self.current_time += ticks

    def queue_size(self) -> int:
        return len(self.queue)


# ─── Urgency Classification ───────────────────────────────────────

def classify_urgency(trust: float, decay_rate: float,
                      threshold: float = 0.3) -> Priority:
    """
    Classify attestation urgency based on trust dynamics.
    """
    if trust < threshold:
        return Priority.CRITICAL

    # Time until threshold
    if decay_rate > 0:
        time_to_threshold = -math.log(threshold / trust) / decay_rate
    else:
        time_to_threshold = float('inf')

    if time_to_threshold < 10:
        return Priority.HIGH
    elif time_to_threshold < 50:
        return Priority.NORMAL
    elif time_to_threshold < 200:
        return Priority.LOW
    return Priority.BACKGROUND


# ─── Exponential Backoff ──────────────────────────────────────────

def exponential_backoff_interval(base: float, consecutive_successes: int,
                                  max_interval: float = 1000.0,
                                  multiplier: float = 1.5) -> float:
    """
    Interval grows exponentially with consecutive successful attestations.
    Resets on failure.
    """
    interval = base * (multiplier ** consecutive_successes)
    return min(interval, max_interval)


def jittered_interval(interval: float, jitter_fraction: float = 0.2,
                       rng: random.Random = None) -> float:
    """Add random jitter to prevent thundering herd."""
    if rng is None:
        rng = random.Random()
    jitter = interval * jitter_fraction * (rng.random() * 2 - 1)
    return max(1.0, interval + jitter)


# ─── Load-Aware Scheduling ────────────────────────────────────────

@dataclass
class FederationLoad:
    """Current federation attestation load."""
    active_attestations: int = 0
    max_capacity: int = 50
    avg_latency: float = 10.0  # ticks per attestation
    queue_depth: int = 0

    @property
    def utilization(self) -> float:
        return self.active_attestations / max(1, self.max_capacity)

    @property
    def congested(self) -> bool:
        return self.utilization > 0.8


def load_adjusted_interval(base_interval: float,
                            load: FederationLoad) -> float:
    """
    Adjust interval based on federation load.
    High load → longer intervals (back off).
    Low load → can schedule sooner.
    """
    if load.congested:
        # Back off proportionally to congestion
        factor = 1.0 + (load.utilization - 0.8) * 5  # 1.0 to 2.0
        return base_interval * factor
    else:
        # Can be more aggressive when load is low
        factor = 0.8 + load.utilization * 0.2  # 0.8 to 1.0
        return base_interval * factor


# ─── Batch Optimization ───────────────────────────────────────────

def batch_related_attestations(tasks: List[AttestationTask],
                                max_batch: int = 5) -> List[List[AttestationTask]]:
    """
    Group related attestation tasks for efficiency.
    Related = same context or similar priority.
    """
    # Group by context
    by_context: Dict[str, List[AttestationTask]] = {}
    for task in tasks:
        if task.context not in by_context:
            by_context[task.context] = []
        by_context[task.context].append(task)

    batches = []
    for context, group in by_context.items():
        # Sort by priority within group
        group.sort(key=lambda t: t.priority)
        # Split into batches of max_batch
        for i in range(0, len(group), max_batch):
            batches.append(group[i:i + max_batch])

    return batches


# ─── Deadline-Aware Scheduling ────────────────────────────────────

def earliest_deadline_first(tasks: List[AttestationTask]) -> List[AttestationTask]:
    """Sort tasks by deadline (EDF scheduling)."""
    return sorted(tasks, key=lambda t: t.deadline)


def check_deadline_feasibility(tasks: List[AttestationTask],
                                processing_time: float,
                                current_time: int) -> Dict:
    """
    Check if all tasks can meet their deadlines.
    """
    sorted_tasks = earliest_deadline_first(tasks)
    feasible = []
    missed = []
    time = current_time

    for task in sorted_tasks:
        time += processing_time
        if time <= task.deadline:
            feasible.append(task)
        else:
            missed.append(task)

    return {
        "feasible": len(feasible),
        "missed": len(missed),
        "all_feasible": len(missed) == 0,
        "utilization": len(tasks) * processing_time / max(1, max(t.deadline for t in tasks) - current_time) if tasks else 0,
    }


# ─── Rate Adaptation ──────────────────────────────────────────────

class RateAdapter:
    """
    AIMD (Additive Increase, Multiplicative Decrease) rate control
    for attestation scheduling. Like TCP congestion control.
    """

    def __init__(self, initial_rate: float = 5.0, min_rate: float = 1.0,
                 max_rate: float = 50.0):
        self.rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.history: List[Tuple[float, bool]] = []  # (rate, success)

    def on_success(self):
        """Additive increase on success."""
        self.rate = min(self.max_rate, self.rate + 1.0)
        self.history.append((self.rate, True))

    def on_failure(self):
        """Multiplicative decrease on failure."""
        self.rate = max(self.min_rate, self.rate * 0.5)
        self.history.append((self.rate, False))

    def current_interval(self) -> float:
        """Convert rate to interval."""
        return 1.0 / self.rate if self.rate > 0 else float('inf')

    @property
    def success_rate(self) -> float:
        if not self.history:
            return 0.0
        successes = sum(1 for _, s in self.history if s)
        return successes / len(self.history)


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
    print("Adaptive Attestation Scheduling for Web4")
    print("Session 31, Track 2")
    print("=" * 70)

    # ── §1 Priority Classification ────────────────────────────────
    print("\n§1 Urgency Classification\n")

    p_crit = classify_urgency(0.2, 0.05)
    check("critical_below_threshold", p_crit == Priority.CRITICAL)

    p_high = classify_urgency(0.35, 0.05)
    check("high_near_threshold", p_high in (Priority.HIGH, Priority.CRITICAL),
          f"priority={p_high}")

    p_bg = classify_urgency(0.9, 0.001)
    check("background_stable", p_bg == Priority.BACKGROUND,
          f"priority={p_bg}")

    # Higher decay → higher urgency
    p_fast = classify_urgency(0.5, 0.1)
    p_slow = classify_urgency(0.5, 0.001)
    check("faster_decay_higher_urgency", p_fast.value <= p_slow.value,
          f"fast={p_fast} slow={p_slow}")

    # ── §2 Adaptive Scheduler ─────────────────────────────────────
    print("\n§2 Adaptive Scheduler\n")

    sched = AdaptiveScheduler(capacity=5)

    # Schedule tasks with different priorities
    sched.schedule(AttestationTask(Priority.NORMAL.value, 100, "entity_1", 0.6))
    sched.schedule(AttestationTask(Priority.CRITICAL.value, 50, "entity_2", 0.2))
    sched.schedule(AttestationTask(Priority.LOW.value, 200, "entity_3", 0.8))

    check("queue_size", sched.queue_size() == 3)

    # Next batch should return highest priority first
    batch = sched.next_batch(2)
    check("batch_size", len(batch) == 2)
    check("highest_priority_first", batch[0].entity_id == "entity_2",
          f"first={batch[0].entity_id}")

    # Complete and check interval adaptation
    sched.complete(batch[0], 0.4)
    interval = sched.entity_intervals.get("entity_2", 0)
    check("interval_computed", interval > 0, f"interval={interval:.1f}")

    # ── §3 Exponential Backoff ────────────────────────────────────
    print("\n§3 Exponential Backoff\n")

    i0 = exponential_backoff_interval(10, 0)
    i3 = exponential_backoff_interval(10, 3)
    i10 = exponential_backoff_interval(10, 10)

    check("backoff_grows", i3 > i0, f"i0={i0:.1f} i3={i3:.1f}")
    check("backoff_monotone", i10 > i3, f"i3={i3:.1f} i10={i10:.1f}")
    check("backoff_capped", i10 <= 1000, f"i10={i10:.1f}")

    # Jittered interval
    rng = random.Random(42)
    jittered = [jittered_interval(100, 0.2, rng) for _ in range(100)]
    check("jitter_varies", len(set(jittered)) > 50)
    check("jitter_centered", abs(sum(jittered)/len(jittered) - 100) < 10,
          f"mean={sum(jittered)/len(jittered):.1f}")

    # ── §4 Interval Adaptation ────────────────────────────────────
    print("\n§4 Trust-Based Interval Adaptation\n")

    sched2 = AdaptiveScheduler()

    # High trust, stable → long interval
    sched2.entity_history["stable"] = [0.8, 0.81, 0.79]
    int_stable = sched2.compute_interval("stable", 0.8)

    # Low trust, volatile → short interval
    sched2.entity_history["volatile"] = [0.4, 0.6, 0.3]
    int_volatile = sched2.compute_interval("volatile", 0.4)

    check("stable_longer_interval", int_stable > int_volatile,
          f"stable={int_stable:.1f} volatile={int_volatile:.1f}")

    # Near threshold → very short (both volatile and threshold are urgent)
    sched2.entity_history["threshold"] = [0.32, 0.31, 0.29]
    int_threshold = sched2.compute_interval("threshold", 0.31)
    check("threshold_very_short", int_threshold < int_stable,
          f"threshold={int_threshold:.1f} stable={int_stable:.1f}")

    # ── §5 Load-Aware Scheduling ──────────────────────────────────
    print("\n§5 Load-Aware Scheduling\n")

    low_load = FederationLoad(active_attestations=10, max_capacity=50)
    high_load = FederationLoad(active_attestations=45, max_capacity=50)

    check("low_load_not_congested", not low_load.congested)
    check("high_load_congested", high_load.congested)

    int_low = load_adjusted_interval(100, low_load)
    int_high = load_adjusted_interval(100, high_load)
    check("high_load_backs_off", int_high > int_low,
          f"low={int_low:.1f} high={int_high:.1f}")

    # ── §6 Batch Optimization ─────────────────────────────────────
    print("\n§6 Batch Optimization\n")

    tasks = [
        AttestationTask(2, 100, f"e_{i}", 0.5, context="financial")
        for i in range(7)
    ] + [
        AttestationTask(1, 50, f"e_{i+7}", 0.3, context="identity")
        for i in range(3)
    ]

    batches = batch_related_attestations(tasks, max_batch=4)
    check("batches_created", len(batches) > 0)

    # All tasks accounted for
    total_in_batches = sum(len(b) for b in batches)
    check("all_tasks_batched", total_in_batches == 10,
          f"total={total_in_batches}")

    # No batch exceeds max size
    check("batch_size_limit", all(len(b) <= 4 for b in batches))

    # ── §7 Deadline-Aware Scheduling ──────────────────────────────
    print("\n§7 Deadline-Aware (EDF)\n")

    deadline_tasks = [
        AttestationTask(2, 30, "e_1", 0.5),
        AttestationTask(2, 10, "e_2", 0.5),
        AttestationTask(2, 20, "e_3", 0.5),
    ]

    sorted_tasks = earliest_deadline_first(deadline_tasks)
    check("edf_order", sorted_tasks[0].entity_id == "e_2",
          f"first={sorted_tasks[0].entity_id}")

    # Feasibility check
    feasibility = check_deadline_feasibility(deadline_tasks, 5.0, 0)
    check("all_feasible", feasibility["all_feasible"],
          f"feasible={feasibility['feasible']} missed={feasibility['missed']}")

    # Infeasible case
    tight_tasks = [
        AttestationTask(2, 5, f"e_{i}", 0.5) for i in range(5)
    ]
    infeasible = check_deadline_feasibility(tight_tasks, 3.0, 0)
    check("some_infeasible", not infeasible["all_feasible"],
          f"missed={infeasible['missed']}")

    # ── §8 AIMD Rate Adaptation ───────────────────────────────────
    print("\n§8 AIMD Rate Control\n")

    adapter = RateAdapter(initial_rate=10.0)

    # Successes increase rate
    for _ in range(5):
        adapter.on_success()
    check("rate_increases_on_success", adapter.rate > 10.0,
          f"rate={adapter.rate:.1f}")

    # Failure halves rate
    rate_before = adapter.rate
    adapter.on_failure()
    check("rate_halves_on_failure", abs(adapter.rate - rate_before * 0.5) < 0.1,
          f"before={rate_before:.1f} after={adapter.rate:.1f}")

    # Rate bounded
    for _ in range(100):
        adapter.on_success()
    check("rate_capped", adapter.rate <= 50.0, f"rate={adapter.rate:.1f}")

    for _ in range(100):
        adapter.on_failure()
    check("rate_floored", adapter.rate >= 1.0, f"rate={adapter.rate:.1f}")

    # Success rate tracked
    check("success_rate_computed", 0 <= adapter.success_rate <= 1,
          f"sr={adapter.success_rate:.3f}")

    # ── §9 End-to-End Simulation ──────────────────────────────────
    print("\n§9 End-to-End Scheduling Simulation\n")

    rng = random.Random(42)
    sched3 = AdaptiveScheduler(capacity=5)

    # Simulate 100 ticks with 10 entities
    entities = {f"e_{i}": rng.uniform(0.3, 0.9) for i in range(10)}
    completed_count = 0

    for tick in range(100):
        sched3.current_time = tick

        # Some entities need attestation
        for eid, trust in entities.items():
            if rng.random() < 0.05:  # 5% chance per tick
                urgency = classify_urgency(trust, 0.02)
                sched3.schedule(AttestationTask(
                    urgency.value, tick + 20, eid, trust, "routine"
                ))

        # Process batch
        if sched3.queue_size() > 0 and tick % 5 == 0:
            batch = sched3.next_batch(3)
            for task in batch:
                # Simulate attestation result
                new_trust = max(0, min(1, task.current_trust + rng.gauss(0, 0.05)))
                sched3.complete(task, new_trust)
                entities[task.entity_id] = new_trust
                completed_count += 1

    check("simulation_completed", completed_count > 0,
          f"completed={completed_count}")
    check("intervals_adapted", len(sched3.entity_intervals) > 0,
          f"entities_with_intervals={len(sched3.entity_intervals)}")

    # Entities with stable trust should have longer intervals
    intervals = list(sched3.entity_intervals.values())
    if intervals:
        check("intervals_positive", all(i > 0 for i in intervals))

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
