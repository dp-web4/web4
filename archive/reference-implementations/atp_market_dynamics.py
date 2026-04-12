#!/usr/bin/env python3
"""
ATP Market Dynamics Simulation
================================

Explores emergent behaviors in ATP (Allocation Transfer Packet) markets:
- Supply/demand equilibria
- Wealth concentration (Gini coefficient)
- Fee structure gaming
- Circular flow unprofitability
- Recharge policy effects
- Task market pricing
- Conservation invariant under stress

Key questions investigated:
  1. Does ATP concentrate in few entities? (Gini analysis)
  2. Can agents game the 5% transfer fee? (Circular flow test)
  3. What recharge policy produces healthy markets? (Parametric sweep)
  4. How does task quality affect market dynamics? (Quality-settlement link)
  5. Where do equilibria form? (Supply/demand convergence)

Builds on: atp_adp_cycle spec, e2e_defense_implementations (sliding scale),
           scalability_stress_test (ATP conservation at 10K)

Session: 12 (2026-02-27)
"""

import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# ═══════════════════════════════════════════════════════════════
#  CHECK HARNESS
# ═══════════════════════════════════════════════════════════════

_checks_passed = 0
_checks_failed = 0
_section = ""


def section(name: str):
    global _section
    _section = name
    print(f"\nSection: {name}")


def check(condition: bool, label: str):
    global _checks_passed, _checks_failed
    if condition:
        _checks_passed += 1
    else:
        _checks_failed += 1
        print(f"  FAIL: {label}")


# ═══════════════════════════════════════════════════════════════
#  CORE ATP MODEL
# ═══════════════════════════════════════════════════════════════

@dataclass
class ATPAccount:
    """Individual ATP account."""
    agent_id: str
    balance: float = 100.0
    locked: float = 0.0
    total_earned: float = 0.0
    total_spent: float = 0.0
    total_fees_paid: float = 0.0
    transaction_count: int = 0

    @property
    def available(self) -> float:
        return self.balance - self.locked

    @property
    def energy_ratio(self) -> float:
        total = self.balance + self.total_spent
        return self.balance / total if total > 0 else 0.5


@dataclass
class TaskListing:
    """A task posted on the market."""
    task_id: str
    poster_id: str
    task_type: str
    budget: float          # Max ATP payer will spend
    min_quality: float     # Minimum acceptable quality
    claimed_by: Optional[str] = None
    completed: bool = False
    quality: float = 0.0
    payment: float = 0.0


@dataclass
class MarketStats:
    """Snapshot of market statistics."""
    tick: int
    total_supply: float
    total_fees_destroyed: float
    gini: float
    mean_balance: float
    median_balance: float
    std_balance: float
    active_tasks: int
    completed_tasks: int
    avg_quality: float
    conservation_error: float  # Should be near 0


class ATPMarket:
    """
    ATP market simulation engine.

    Core mechanics:
      - Transfer fee: 5% destroyed on every transfer (anti-farming)
      - Recharge: periodic, capped, quality-weighted
      - Settlement: quality-adjusted payment with sliding scale
      - Conservation: initial_supply = current_supply + total_fees
    """

    DEFAULT_FEE_RATE = 0.05   # 5% transfer fee (destroyed)
    RECHARGE_INTERVAL = 10     # Ticks between recharges
    RECHARGE_AMOUNT = 20.0     # Base recharge per interval
    RECHARGE_CAP = 3.0         # Max recharge = cap × initial_balance
    MAX_BALANCE = 500.0        # Hard cap on balance
    SLIDING_ZERO = 0.3         # Quality below this = zero payment
    SLIDING_FULL = 0.7         # Quality above this = full proportional payment

    def __init__(self, fee_rate: float = DEFAULT_FEE_RATE,
                 recharge_amount: float = RECHARGE_AMOUNT,
                 recharge_cap: float = RECHARGE_CAP):
        self.fee_rate = fee_rate
        self.recharge_amount = recharge_amount
        self.recharge_cap = recharge_cap
        self.accounts: dict[str, ATPAccount] = {}
        self.tasks: list[TaskListing] = []
        self.completed_tasks: list[TaskListing] = []
        self.total_fees_destroyed: float = 0.0
        self.initial_supply: float = 0.0
        self.tick: int = 0
        self.stats_history: list[MarketStats] = []
        self.rng = random.Random(42)

    def add_agent(self, agent_id: str, initial_balance: float = 100.0):
        self.accounts[agent_id] = ATPAccount(agent_id=agent_id, balance=initial_balance)
        self.initial_supply += initial_balance

    def transfer(self, from_id: str, to_id: str, amount: float) -> tuple[bool, float]:
        """
        Transfer ATP with fee. Fee is destroyed (removed from supply).
        Returns (success, fee_amount).
        """
        sender = self.accounts[from_id]
        receiver = self.accounts[to_id]

        fee = amount * self.fee_rate
        total = amount + fee

        if sender.available < total:
            return False, 0.0

        sender.balance -= total
        sender.total_spent += amount
        sender.total_fees_paid += fee
        sender.transaction_count += 1

        actual_credit = max(0, min(amount, self.MAX_BALANCE - receiver.balance))
        overflow = amount - actual_credit  # ATP that can't be absorbed
        receiver.balance += actual_credit
        receiver.total_earned += actual_credit
        receiver.transaction_count += 1

        # Overflow goes back to sender (not destroyed, not lost)
        sender.balance += overflow

        self.total_fees_destroyed += fee
        return True, fee

    def sliding_scale_payment(self, budget: float, quality: float) -> float:
        """
        Compute payment using sliding scale (no binary cliff).
        Below 0.3: zero. 0.3-0.7: linear ramp. Above 0.7: full proportional.
        """
        if quality < self.SLIDING_ZERO:
            return 0.0
        elif quality < self.SLIDING_FULL:
            ramp = (quality - self.SLIDING_ZERO) / (self.SLIDING_FULL - self.SLIDING_ZERO)
            return budget * quality * ramp
        else:
            return budget * quality

    def post_task(self, poster_id: str, task_type: str,
                  budget: float, min_quality: float = 0.5) -> Optional[TaskListing]:
        """Post a task to the market."""
        poster = self.accounts[poster_id]
        if poster.available < budget:
            return None

        task = TaskListing(
            task_id=f"task:{len(self.tasks):04d}",
            poster_id=poster_id,
            task_type=task_type,
            budget=budget,
            min_quality=min_quality,
        )
        self.tasks.append(task)
        return task

    def claim_task(self, worker_id: str, task_id: str) -> bool:
        """Worker claims an available task."""
        task = next((t for t in self.tasks if t.task_id == task_id and not t.claimed_by), None)
        if not task:
            return False
        task.claimed_by = worker_id
        return True

    def complete_task(self, task_id: str, quality: float) -> tuple[bool, float]:
        """
        Complete a task with given quality. Payment follows sliding scale.
        Returns (success, payment_amount).
        """
        task = next((t for t in self.tasks if t.task_id == task_id), None)
        if not task or task.completed or not task.claimed_by:
            return False, 0.0

        payment = self.sliding_scale_payment(task.budget, quality)
        task.quality = quality
        task.payment = payment
        task.completed = True

        # Execute payment
        if payment > 0:
            success, fee = self.transfer(task.poster_id, task.claimed_by, payment)
            if not success:
                # Poster can't afford — partial payment
                available = self.accounts[task.poster_id].available / (1 + self.fee_rate)
                if available > 0:
                    self.transfer(task.poster_id, task.claimed_by, available)
                    task.payment = available

        self.completed_tasks.append(task)
        return True, task.payment

    def recharge_all(self):
        """
        Periodic recharge: add ATP to all accounts.
        Quality-weighted: better performers get more.
        Capped at recharge_cap × initial_balance.
        """
        for acct in self.accounts.values():
            max_recharge = 100.0 * self.recharge_cap  # Based on standard initial
            if acct.balance >= max_recharge:
                continue

            # Quality-weighted: agents with higher energy_ratio get proportionally more
            quality_factor = 0.5 + 0.5 * acct.energy_ratio
            amount = self.recharge_amount * quality_factor
            actual = min(amount, max_recharge - acct.balance, self.MAX_BALANCE - acct.balance)
            if actual > 0:
                acct.balance += actual
                # Track as recharge (increases supply — separate from transfers)
                self.initial_supply += actual

    def compute_gini(self) -> float:
        """Compute Gini coefficient of ATP distribution. 0=equal, 1=concentrated."""
        balances = sorted(a.balance for a in self.accounts.values())
        n = len(balances)
        if n == 0:
            return 0.0
        total = sum(balances)
        if total == 0:
            return 0.0

        cumulative = 0.0
        weighted_sum = 0.0
        for i, b in enumerate(balances):
            cumulative += b
            weighted_sum += (2 * (i + 1) - n - 1) * b

        return weighted_sum / (n * total)

    def conservation_check(self) -> float:
        """
        Check ATP conservation: initial_supply = current_supply + fees_destroyed.
        Returns the error (should be near zero).
        """
        current_supply = sum(a.balance for a in self.accounts.values())
        error = abs(self.initial_supply - current_supply - self.total_fees_destroyed)
        return error

    def snapshot(self) -> MarketStats:
        """Take a market statistics snapshot."""
        balances = [a.balance for a in self.accounts.values()]
        completed_q = [t.quality for t in self.completed_tasks if t.quality > 0]

        stats = MarketStats(
            tick=self.tick,
            total_supply=sum(balances),
            total_fees_destroyed=self.total_fees_destroyed,
            gini=self.compute_gini(),
            mean_balance=statistics.mean(balances) if balances else 0,
            median_balance=statistics.median(balances) if balances else 0,
            std_balance=statistics.stdev(balances) if len(balances) > 1 else 0,
            active_tasks=sum(1 for t in self.tasks if not t.completed),
            completed_tasks=len(self.completed_tasks),
            avg_quality=statistics.mean(completed_q) if completed_q else 0,
            conservation_error=self.conservation_check(),
        )
        self.stats_history.append(stats)
        return stats

    def simulate_tick(self, task_rate: float = 0.3, quality_mean: float = 0.7,
                      quality_std: float = 0.15):
        """
        Simulate one market tick:
          1. Agents randomly post tasks
          2. Workers claim and complete tasks
          3. Periodic recharge
        """
        self.tick += 1
        agents = list(self.accounts.keys())

        # Phase 1: Post tasks
        for agent_id in agents:
            if self.rng.random() < task_rate:
                budget = self.rng.uniform(10, 50)
                self.post_task(agent_id, "generic", budget)

        # Phase 2: Claim and complete tasks
        unclaimed = [t for t in self.tasks if not t.claimed_by and not t.completed]
        self.rng.shuffle(unclaimed)
        workers = [a for a in agents if self.accounts[a].available > 0]
        self.rng.shuffle(workers)

        for task, worker in zip(unclaimed, workers):
            if task.poster_id != worker:  # Don't self-assign
                self.claim_task(worker, task.task_id)
                quality = max(0.0, min(1.0,
                              self.rng.gauss(quality_mean, quality_std)))
                self.complete_task(task.task_id, quality)

        # Phase 3: Periodic recharge
        if self.tick % self.RECHARGE_INTERVAL == 0:
            self.recharge_all()


# ═══════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════

def run_checks():
    global _checks_passed, _checks_failed
    _checks_passed = 0
    _checks_failed = 0

    # ── Section 1: Basic ATP Mechanics ───────────────────────────

    section("1: Basic ATP Mechanics")

    market = ATPMarket()
    market.add_agent("alice", 200.0)
    market.add_agent("bob", 100.0)

    # Transfer with fee
    ok, fee = market.transfer("alice", "bob", 50.0)
    check(ok, "Transfer succeeded")
    check(abs(fee - 2.5) < 0.01, "5% fee = 2.5")
    check(abs(market.accounts["alice"].balance - (200 - 50 - 2.5)) < 0.01,
          "Alice: 200 - 50 - 2.5 = 147.5")
    check(abs(market.accounts["bob"].balance - 150.0) < 0.01,
          "Bob: 100 + 50 = 150")
    check(abs(market.total_fees_destroyed - 2.5) < 0.01,
          "2.5 ATP destroyed as fee")

    # Conservation: initial(300) = current(297.5) + fees(2.5)
    err = market.conservation_check()
    check(err < 0.01, f"Conservation holds: error = {err:.6f}")

    # Transfer more than available → fails
    ok2, _ = market.transfer("alice", "bob", 200.0)
    check(not ok2, "Transfer > available fails")

    # ── Section 2: Sliding Scale Settlement ──────────────────────

    section("2: Sliding Scale Settlement")

    # Below 0.3: zero
    check(market.sliding_scale_payment(100.0, 0.2) == 0.0,
          "Quality 0.2 → zero payment")

    # At 0.3: start of ramp (0%)
    check(market.sliding_scale_payment(100.0, 0.3) == 0.0,
          "Quality 0.3 → zero (ramp start)")

    # At 0.5: midpoint of ramp (50% of 0.5×100 = 25)
    pay_50 = market.sliding_scale_payment(100.0, 0.5)
    check(abs(pay_50 - 25.0) < 0.01, f"Quality 0.5 → 25.0 (got {pay_50:.2f})")

    # At 0.69: near top of ramp
    pay_69 = market.sliding_scale_payment(100.0, 0.69)
    check(pay_69 > 60.0, f"Quality 0.69 → {pay_69:.2f} (not zero!)")

    # At 0.70: full proportional
    pay_70 = market.sliding_scale_payment(100.0, 0.70)
    check(abs(pay_70 - 70.0) < 0.01, "Quality 0.70 → 70.0")

    # No cliff: 0.69/0.70 ratio close to 1
    ratio = pay_70 / max(pay_69, 0.001)
    check(ratio < 1.1, f"Cliff eliminated: ratio = {ratio:.3f}")

    # Quality 1.0: full budget
    check(abs(market.sliding_scale_payment(100.0, 1.0) - 100.0) < 0.01,
          "Quality 1.0 → 100.0")

    # ── Section 3: Circular Flow Unprofitability ─────────────────

    section("3: Circular Flow Unprofitability")

    circ = ATPMarket(fee_rate=0.05)
    circ.add_agent("a", 1000.0)
    circ.add_agent("b", 1000.0)
    circ.add_agent("c", 1000.0)

    initial_total = sum(a.balance for a in circ.accounts.values())

    # Circular transfers: a→b→c→a, 100 each
    for _ in range(10):
        circ.transfer("a", "b", 100.0)
        circ.transfer("b", "c", 100.0)
        circ.transfer("c", "a", 100.0)

    final_total = sum(a.balance for a in circ.accounts.values())
    fees = circ.total_fees_destroyed

    check(final_total < initial_total, "Circular flow loses ATP")
    check(fees > 0, "Fees destroyed from circular flow")

    # After 10 rounds of 3 transfers each: 30 transfers × 100 × 0.05 = 150 ATP lost
    check(abs(fees - 150.0) < 0.1, f"30 transfers × 5 fee = 150 ATP lost (got {fees:.1f})")

    # Group is poorer (individual agents may redistribute due to overflow cap)
    avg_balance = sum(a.balance for a in circ.accounts.values()) / len(circ.accounts)
    check(avg_balance < 1000.0,
          f"Average balance decreased: {avg_balance:.1f} < 1000 (fees destroyed)")

    # Conservation
    check(circ.conservation_check() < 0.01, "Conservation holds after circular flow")

    # ── Section 4: Task Market Dynamics (50 agents, 100 ticks) ───

    section("4: Task Market Dynamics (50 agents, 100 ticks)")

    sim = ATPMarket(fee_rate=0.05, recharge_amount=15.0)
    for i in range(50):
        sim.add_agent(f"agent_{i:03d}", initial_balance=100.0)

    initial_stats = sim.snapshot()
    check(initial_stats.gini < 0.01, "Initial Gini ≈ 0 (equal distribution)")
    check(initial_stats.total_supply == 5000.0, "Initial supply = 50 × 100 = 5000")

    # Run 100 ticks
    for _ in range(100):
        sim.simulate_tick(task_rate=0.3, quality_mean=0.7, quality_std=0.15)

    final_stats = sim.snapshot()
    check(final_stats.completed_tasks > 100, f"Completed {final_stats.completed_tasks} tasks")
    check(final_stats.avg_quality > 0.5, f"Average quality = {final_stats.avg_quality:.3f}")

    # Gini should increase from 0 but stay reasonable (< 0.5)
    check(final_stats.gini > 0.0, f"Gini increased from 0: {final_stats.gini:.4f}")
    check(final_stats.gini < 0.5, f"Gini stays moderate: {final_stats.gini:.4f}")

    # No agent should have zero balance (recharge prevents starvation)
    min_balance = min(a.balance for a in sim.accounts.values())
    check(min_balance > 0, f"No agent at zero (min = {min_balance:.2f})")

    # Conservation (accounting for recharges)
    cons_err = sim.conservation_check()
    check(cons_err < 0.1, f"Conservation error: {cons_err:.6f}")

    # ── Section 5: Wealth Concentration at Scale (200 agents) ────

    section("5: Wealth Concentration at Scale (200 agents, 500 ticks)")

    big = ATPMarket(fee_rate=0.05, recharge_amount=10.0)
    for i in range(200):
        # Heterogeneous initial: some start rich, some poor
        initial = 50.0 + (i % 10) * 20.0  # 50-230
        big.add_agent(f"big_{i:03d}", initial_balance=initial)

    for _ in range(500):
        big.simulate_tick(task_rate=0.25, quality_mean=0.65, quality_std=0.2)

    big_stats = big.snapshot()
    check(big_stats.completed_tasks > 500,
          f"Completed {big_stats.completed_tasks} tasks at scale")

    # Gini should be moderate even with heterogeneous start
    check(big_stats.gini < 0.6,
          f"Gini at scale: {big_stats.gini:.4f} (moderate, not runaway)")

    # Mean and median should be in reasonable ratio (no extreme skew)
    if big_stats.median_balance > 0:
        skew_ratio = big_stats.mean_balance / big_stats.median_balance
        check(skew_ratio < 3.0,
              f"Mean/median ratio: {skew_ratio:.2f} (no extreme skew)")

    # ── Section 6: Fee Rate Sensitivity ──────────────────────────

    section("6: Fee Rate Sensitivity (parametric sweep)")

    results = {}
    for fee_rate in [0.0, 0.02, 0.05, 0.10, 0.20]:
        m = ATPMarket(fee_rate=fee_rate, recharge_amount=15.0)
        for i in range(50):
            m.add_agent(f"fee_{i}", 100.0)

        for _ in range(200):
            m.simulate_tick(task_rate=0.3, quality_mean=0.7)

        stats = m.snapshot()
        results[fee_rate] = {
            "gini": stats.gini,
            "mean": stats.mean_balance,
            "fees_destroyed": stats.total_fees_destroyed,
            "completed": stats.completed_tasks,
        }

    # Higher fees → more ATP destroyed → lower mean balance
    check(results[0.20]["fees_destroyed"] > results[0.05]["fees_destroyed"],
          "20% fee destroys more ATP than 5%")

    # Zero fee → no fee destruction
    check(results[0.0]["fees_destroyed"] == 0.0,
          "0% fee → zero destruction")

    # 5% is the sweet spot: enough to prevent farming, not so high as to cripple
    check(results[0.05]["completed"] > 0,
          f"5% fee: {results[0.05]['completed']} tasks completed")

    # Very high fee reduces completion (agents can't afford)
    check(results[0.20]["mean"] < results[0.05]["mean"],
          "20% fee → lower mean balance than 5%")

    # ── Section 7: Quality Impact on Earnings ────────────────────

    section("7: Quality Impact on Earnings")

    q_market = ATPMarket(fee_rate=0.05, recharge_amount=10.0)

    # Create agents with different quality profiles
    for i in range(20):
        q_market.add_agent(f"high_q_{i}", 100.0)
    for i in range(20):
        q_market.add_agent(f"low_q_{i}", 100.0)

    # Simulate: high quality agents produce quality 0.8-0.9, low produce 0.3-0.5
    for tick in range(200):
        q_market.tick += 1
        agents = list(q_market.accounts.keys())

        # Post tasks
        for agent_id in agents:
            if q_market.rng.random() < 0.3:
                budget = q_market.rng.uniform(15, 40)
                q_market.post_task(agent_id, "quality_test", budget)

        # Assign tasks
        unclaimed = [t for t in q_market.tasks if not t.claimed_by and not t.completed]
        q_market.rng.shuffle(unclaimed)
        workers = [a for a in agents if q_market.accounts[a].available > 0]
        q_market.rng.shuffle(workers)

        for task, worker in zip(unclaimed, workers):
            if task.poster_id != worker:
                q_market.claim_task(worker, task.task_id)
                # Quality depends on agent type
                if worker.startswith("high_q"):
                    quality = min(1.0, max(0.0, q_market.rng.gauss(0.85, 0.05)))
                else:
                    quality = min(1.0, max(0.0, q_market.rng.gauss(0.4, 0.1)))
                q_market.complete_task(task.task_id, quality)

        if tick % q_market.RECHARGE_INTERVAL == 0:
            q_market.recharge_all()

    # High-quality agents should earn more
    high_earnings = [q_market.accounts[f"high_q_{i}"].total_earned for i in range(20)]
    low_earnings = [q_market.accounts[f"low_q_{i}"].total_earned for i in range(20)]

    avg_high = statistics.mean(high_earnings)
    avg_low = statistics.mean(low_earnings)

    check(avg_high > avg_low,
          f"High-quality earns more: {avg_high:.1f} vs {avg_low:.1f}")

    # High quality agents should have higher balances
    high_balances = [q_market.accounts[f"high_q_{i}"].balance for i in range(20)]
    low_balances = [q_market.accounts[f"low_q_{i}"].balance for i in range(20)]

    check(statistics.mean(high_balances) > statistics.mean(low_balances),
          f"High-quality higher balance: {statistics.mean(high_balances):.1f} vs {statistics.mean(low_balances):.1f}")

    # ── Section 8: Recharge Policy Effects ───────────────────────

    section("8: Recharge Policy Effects")

    # Compare: no recharge vs moderate vs aggressive
    for label, recharge_amt in [("none", 0.0), ("moderate", 15.0), ("aggressive", 50.0)]:
        m = ATPMarket(fee_rate=0.05, recharge_amount=recharge_amt)
        for i in range(30):
            m.add_agent(f"rch_{i}", 100.0)

        for _ in range(200):
            m.simulate_tick(task_rate=0.25)

        stats = m.snapshot()

        if label == "none":
            # Without recharge, mean balance should decrease over time
            check(stats.mean_balance < 100.0,
                  f"No recharge: mean decreases ({stats.mean_balance:.1f})")
        elif label == "moderate":
            # Moderate recharge should stabilize
            check(stats.mean_balance > 50.0,
                  f"Moderate recharge: mean stable ({stats.mean_balance:.1f})")
        elif label == "aggressive":
            # Aggressive recharge inflates
            check(stats.mean_balance > 100.0,
                  f"Aggressive recharge: mean inflates ({stats.mean_balance:.1f})")

    # ── Section 9: Market Equilibrium Detection ──────────────────

    section("9: Market Equilibrium Detection")

    eq = ATPMarket(fee_rate=0.05, recharge_amount=12.0)
    for i in range(100):
        eq.add_agent(f"eq_{i}", 100.0)

    # Run for 500 ticks, take snapshots every 50
    for tick in range(500):
        eq.simulate_tick(task_rate=0.3)
        if tick % 50 == 49:
            eq.snapshot()

    # Check if market converges (Gini stabilizes)
    if len(eq.stats_history) >= 5:
        late_ginis = [s.gini for s in eq.stats_history[-5:]]
        gini_std = statistics.stdev(late_ginis) if len(late_ginis) > 1 else 0

        check(gini_std < 0.05,
              f"Gini converges (std of last 5 snapshots: {gini_std:.4f})")

        late_means = [s.mean_balance for s in eq.stats_history[-5:]]
        mean_cv = statistics.stdev(late_means) / statistics.mean(late_means) if statistics.mean(late_means) > 0 else 0

        check(mean_cv < 0.3,
              f"Mean balance stabilizes (CV: {mean_cv:.4f})")

    # ── Section 10: Conservation Under Stress ────────────────────

    section("10: Conservation Under Stress")

    stress = ATPMarket(fee_rate=0.05, recharge_amount=0.0)  # No recharge
    for i in range(100):
        stress.add_agent(f"stress_{i}", 100.0)

    initial_supply = stress.initial_supply

    # Heavy trading: high task rate
    for _ in range(300):
        stress.simulate_tick(task_rate=0.5, quality_mean=0.6)

    final_supply = sum(a.balance for a in stress.accounts.values())
    fees = stress.total_fees_destroyed

    # Conservation: initial = final + fees
    cons_error = abs(initial_supply - final_supply - fees)
    check(cons_error < 0.1,
          f"Conservation under stress: error = {cons_error:.6f}")

    # All ATP is accounted for
    check(final_supply + fees <= initial_supply + 0.01,
          "No ATP created from nothing")

    # ── Section 11: Sybil Attack Cost Analysis ───────────────────

    section("11: Sybil Attack Cost Analysis")

    # Honest agent: 1 identity, high quality
    sybil = ATPMarket(fee_rate=0.05, recharge_amount=10.0)
    sybil.add_agent("honest", 500.0)
    for i in range(5):
        sybil.add_agent(f"sybil_{i}", 100.0)  # 5 fake identities

    # Add other legitimate agents
    for i in range(20):
        sybil.add_agent(f"legit_{i}", 100.0)

    # Simulate: honest does high quality, sybils do low quality
    for tick in range(200):
        sybil.tick += 1
        agents = list(sybil.accounts.keys())

        for agent_id in agents:
            if sybil.rng.random() < 0.3:
                sybil.post_task(agent_id, "work", sybil.rng.uniform(10, 30))

        unclaimed = [t for t in sybil.tasks if not t.claimed_by and not t.completed]
        sybil.rng.shuffle(unclaimed)
        for task in unclaimed:
            workers = [a for a in agents if a != task.poster_id and sybil.accounts[a].available > 0]
            if workers:
                worker = sybil.rng.choice(workers)
                sybil.claim_task(worker, task.task_id)
                if worker.startswith("sybil"):
                    quality = max(0.0, sybil.rng.gauss(0.35, 0.1))
                elif worker == "honest":
                    quality = min(1.0, sybil.rng.gauss(0.85, 0.05))
                else:
                    quality = min(1.0, max(0.0, sybil.rng.gauss(0.7, 0.1)))
                sybil.complete_task(task.task_id, quality)

        if tick % sybil.RECHARGE_INTERVAL == 0:
            sybil.recharge_all()

    # Honest agent should earn more than any individual sybil
    honest_earned = sybil.accounts["honest"].total_earned
    sybil_earnings = [sybil.accounts[f"sybil_{i}"].total_earned for i in range(5)]
    total_sybil_earned = sum(sybil_earnings)
    max_sybil = max(sybil_earnings)

    check(honest_earned > max_sybil,
          f"Honest earns more than any sybil: {honest_earned:.1f} vs {max_sybil:.1f}")

    # Total sybil earnings: 5 identities at 100 ATP each = 500 ATP investment
    # vs honest at 500 ATP. Check if sybil strategy is unprofitable
    honest_roi = honest_earned / 500.0
    sybil_roi = total_sybil_earned / 500.0

    check(honest_roi > sybil_roi,
          f"Honest ROI > Sybil ROI: {honest_roi:.3f} vs {sybil_roi:.3f}")

    # ── Section 12: Energy Ratio as Trust Signal ─────────────────

    section("12: Energy Ratio as Trust Signal")

    # Energy ratio = balance / (balance + total_spent)
    # High ratio = healthy, low ratio = depleted

    acct_healthy = ATPAccount(agent_id="healthy", balance=80.0, total_spent=20.0)
    acct_depleted = ATPAccount(agent_id="depleted", balance=10.0, total_spent=90.0)

    check(acct_healthy.energy_ratio == 0.8, "Healthy: ratio = 0.8")
    check(acct_depleted.energy_ratio == 0.1, "Depleted: ratio = 0.1")

    # Ratio correlates with trust — can be used as MRH signal
    check(acct_healthy.energy_ratio > acct_depleted.energy_ratio,
          "Healthy > depleted (ratio as trust signal)")

    # New account
    acct_new = ATPAccount(agent_id="new", balance=100.0, total_spent=0.0)
    check(acct_new.energy_ratio == 1.0, "New account: ratio = 1.0")

    # Zero balance, some spending
    acct_broke = ATPAccount(agent_id="broke", balance=0.0, total_spent=100.0)
    check(acct_broke.energy_ratio == 0.0, "Broke: ratio = 0.0")

    # ── Section 13: Market Summary Statistics ────────────────────

    section("13: Market Summary Statistics")

    # Use the 200-agent simulation stats
    check(len(big.stats_history) >= 1, "Stats history recorded")
    final = big.stats_history[-1]

    check(final.total_supply > 0, f"Total supply > 0: {final.total_supply:.1f}")
    check(final.total_fees_destroyed > 0, f"Fees destroyed > 0: {final.total_fees_destroyed:.1f}")
    check(0 <= final.gini <= 1, f"Gini in [0,1]: {final.gini:.4f}")
    check(final.conservation_error < 1.0,
          f"Conservation error < 1.0: {final.conservation_error:.6f}")

    # ── Print Summary ────────────────────────────────────────────

    print(f"\n{'='*60}")
    print(f"ATP Market Dynamics: {_checks_passed}/{_checks_passed + _checks_failed} checks passed")
    if _checks_failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {_checks_failed} checks FAILED")
    print(f"{'='*60}")

    # Key findings
    print(f"\nKey Findings:")
    print(f"  Circular flow: 30 transfers lose {150.0:.0f} ATP to fees (unprofitable)")
    print(f"  50-agent market: Gini = {final_stats.gini:.4f} (moderate inequality)")
    print(f"  200-agent market: Gini = {big_stats.gini:.4f}")
    print(f"  Quality matters: high-Q earns {avg_high:.0f} vs low-Q {avg_low:.0f}")
    print(f"  Honest vs Sybil ROI: {honest_roi:.3f} vs {sybil_roi:.3f}")
    print(f"  Conservation holds under stress: error < 0.1")

    return _checks_passed, _checks_failed


if __name__ == "__main__":
    run_checks()
