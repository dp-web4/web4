#!/usr/bin/env python3
"""Agent-Based Attack Simulation for Web4 ATP Economics

Simulates attackers and defenders to empirically validate:
1. Attack profitability (ROI)
2. Detection times
3. Nash equilibrium (honest vs malicious strategies)
4. Optimal stake amounts

This addresses the critical research gap identified in Session #40:
"Current stakes ARE deterrent IF detection < 5 days, but we have
no empirical data on actual detection times."

Author: Legion (autonomous research session #41)
Date: 2025-11-30
Priority: #1 from Session #40 ATP Economic Analysis
"""

import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum


class AgentStrategy(Enum):
    """Agent behavioral strategy."""
    HONEST = "honest"
    QUALITY_INFLATION = "quality_inflation"
    CARTEL_MEMBER = "cartel_member"


class DetectionStatus(Enum):
    """Detection status for malicious behavior."""
    UNDETECTED = "undetected"
    SUSPICIOUS = "suspicious"
    DETECTED = "detected"
    SLASHED = "slashed"


@dataclass
class AgentState:
    """State of a simulated agent/platform."""
    agent_id: str
    strategy: AgentStrategy

    # Economic state
    atp_balance: float = 100_000.0
    atp_staked: float = 0.0

    # Reputation
    reputation_score: float = 0.5
    total_tasks: int = 0
    successful_tasks: int = 0

    # Malicious behavior tracking
    detection_status: DetectionStatus = DetectionStatus.UNDETECTED
    suspicious_events: int = 0
    inflation_amount: float = 0.0  # For quality inflation

    # Profitability tracking
    revenue: float = 0.0
    costs: float = 0.0
    net_profit: float = 0.0


@dataclass
class ChallengeSystem:
    """Simulates challenge-response detection system."""
    base_challenge_rate: float = 0.10  # 10% of tasks challenged
    detection_threshold: int = 3  # Mismatches before detection

    # Adaptive challenge rate based on reputation
    reputation_penalty_factor: float = 0.5  # Low rep → more challenges

    def get_challenge_rate(self, reputation: float) -> float:
        """Calculate challenge rate based on reputation.

        Low reputation → higher challenge rate
        High reputation → lower challenge rate
        """
        penalty = max(0.0, (0.7 - reputation)) * self.reputation_penalty_factor
        return min(0.50, self.base_challenge_rate * (1 + penalty))

    def challenge_task(self, agent: AgentState, claimed_quality: float,
                      actual_quality: float) -> bool:
        """Challenge a task and return whether mismatch detected."""
        challenge_rate = self.get_challenge_rate(agent.reputation_score)

        if random.random() < challenge_rate:
            # Task challenged - compare claimed vs actual
            quality_error = abs(claimed_quality - actual_quality) / actual_quality
            if quality_error > 0.15:  # >15% error is suspicious
                agent.suspicious_events += 1

                if agent.suspicious_events >= self.detection_threshold:
                    agent.detection_status = DetectionStatus.DETECTED
                    return True  # Detected!
                else:
                    agent.detection_status = DetectionStatus.SUSPICIOUS

        return False  # Not detected (yet)


@dataclass
class EconomicParameters:
    """ATP pricing and economic parameters."""
    # Task ATP costs (from atp_pricing_calibrated.json)
    low_complexity_cost: float = 10.8
    medium_complexity_cost: float = 34.0
    high_complexity_cost: float = 56.1
    critical_complexity_cost: float = 200.0

    # Identity stakes (from atp_aware_identity_stakes.py)
    global_lct_stake: float = 75_000.0

    # Daily operating costs
    platform_daily_cost: float = 1_000.0

    # Quality inflation markup (malicious strategy)
    quality_inflation_markup_pct: float = 0.30  # 30% markup


@dataclass
class SimulationResults:
    """Results from attack simulation run."""
    scenario_name: str

    # Agent outcomes
    honest_agents: List[AgentState] = field(default_factory=list)
    malicious_agents: List[AgentState] = field(default_factory=list)

    # Detection metrics
    avg_detection_time_days: float = 0.0
    detection_rate: float = 0.0  # % of malicious agents detected

    # Economic metrics
    honest_avg_roi: float = 0.0
    malicious_avg_roi: float = 0.0
    malicious_avg_profit: float = 0.0

    # Attack success metrics
    profitable_attacks_pct: float = 0.0

    def calculate_metrics(self):
        """Calculate aggregate metrics from agent states."""
        # Detection metrics
        detected_count = sum(1 for a in self.malicious_agents
                           if a.detection_status == DetectionStatus.DETECTED)
        self.detection_rate = detected_count / len(self.malicious_agents) if self.malicious_agents else 0.0

        # Economic metrics for honest agents
        if self.honest_agents:
            honest_profits = [a.net_profit for a in self.honest_agents]
            honest_stakes = [a.atp_staked for a in self.honest_agents]
            self.honest_avg_roi = (sum(honest_profits) / sum(honest_stakes)) if sum(honest_stakes) > 0 else 0.0

        # Economic metrics for malicious agents
        if self.malicious_agents:
            malicious_profits = [a.net_profit for a in self.malicious_agents]
            malicious_stakes = [a.atp_staked for a in self.malicious_agents]
            self.malicious_avg_roi = (sum(malicious_profits) / sum(malicious_stakes)) if sum(malicious_stakes) > 0 else 0.0
            self.malicious_avg_profit = sum(malicious_profits) / len(malicious_profits)

            # Profitable attacks
            profitable = sum(1 for a in self.malicious_agents if a.net_profit > 0)
            self.profitable_attacks_pct = profitable / len(self.malicious_agents)


class AttackSimulation:
    """Simulates attacks on Web4 ATP economy."""

    def __init__(self, params: EconomicParameters):
        self.params = params
        self.challenge_system = ChallengeSystem()

    def simulate_quality_inflation_attack(
        self,
        num_honest: int = 10,
        num_malicious: int = 5,
        simulation_days: int = 30,
        tasks_per_day: int = 100
    ) -> SimulationResults:
        """Simulate quality score inflation attack.

        Malicious agents:
        - Stake 75k ATP for GLOBAL LCT
        - Execute tasks but inflate quality scores
        - Receive higher payment for claimed quality
        - Risk detection via challenge-response

        Honest agents:
        - Stake 75k ATP for GLOBAL LCT
        - Execute tasks honestly
        - Receive fair payment
        """
        results = SimulationResults(scenario_name="Quality Inflation Attack")

        # Create honest agents
        for i in range(num_honest):
            agent = AgentState(
                agent_id=f"honest_{i}",
                strategy=AgentStrategy.HONEST,
                atp_staked=self.params.global_lct_stake
            )
            results.honest_agents.append(agent)

        # Create malicious agents
        for i in range(num_malicious):
            agent = AgentState(
                agent_id=f"malicious_{i}",
                strategy=AgentStrategy.QUALITY_INFLATION,
                atp_staked=self.params.global_lct_stake
            )
            results.malicious_agents.append(agent)

        # Simulate each day
        detection_days = []

        for day in range(simulation_days):
            # Process tasks for each agent
            for agent in results.honest_agents + results.malicious_agents:
                if agent.detection_status == DetectionStatus.DETECTED:
                    continue  # Detected agents can't continue

                daily_revenue = 0.0
                daily_cost = self.params.platform_daily_cost

                for _ in range(tasks_per_day):
                    if agent.strategy == AgentStrategy.HONEST:
                        # Honest execution
                        actual_quality = self.params.medium_complexity_cost
                        claimed_quality = actual_quality
                        payment = claimed_quality
                        cost = actual_quality
                    else:
                        # Malicious: deliver medium quality, claim high quality
                        actual_quality = self.params.medium_complexity_cost
                        claimed_quality = self.params.high_complexity_cost
                        payment = claimed_quality
                        cost = actual_quality
                        agent.inflation_amount += (claimed_quality - actual_quality)

                    daily_revenue += payment
                    daily_cost += cost
                    agent.total_tasks += 1

                    # Challenge system
                    if agent.strategy != AgentStrategy.HONEST:
                        detected = self.challenge_system.challenge_task(
                            agent, claimed_quality, actual_quality
                        )
                        if detected and agent.agent_id not in [d[0] for d in detection_days]:
                            detection_days.append((agent.agent_id, day))

                agent.revenue += daily_revenue
                agent.costs += daily_cost

                # Update reputation (simplified)
                if agent.detection_status == DetectionStatus.DETECTED:
                    agent.reputation_score = 0.0
                elif agent.detection_status == DetectionStatus.SUSPICIOUS:
                    agent.reputation_score = max(0.3, agent.reputation_score - 0.05)
                else:
                    agent.reputation_score = min(1.0, agent.reputation_score + 0.01)

        # Calculate final profits (including stake loss if detected)
        for agent in results.honest_agents + results.malicious_agents:
            if agent.detection_status == DetectionStatus.DETECTED:
                # Lose stake
                agent.net_profit = agent.revenue - agent.costs - agent.atp_staked
            else:
                # Keep stake
                agent.net_profit = agent.revenue - agent.costs

        # Calculate detection time
        if detection_days:
            avg_detection_day = sum(d[1] for d in detection_days) / len(detection_days)
            results.avg_detection_time_days = avg_detection_day

        results.calculate_metrics()
        return results

    def print_results(self, results: SimulationResults):
        """Print simulation results."""
        print("=" * 80)
        print(f"Simulation Results: {results.scenario_name}")
        print("=" * 80)
        print()

        print(f"Agents:")
        print(f"  Honest: {len(results.honest_agents)}")
        print(f"  Malicious: {len(results.malicious_agents)}")
        print()

        print(f"Detection Metrics:")
        print(f"  Detection rate: {results.detection_rate * 100:.1f}%")
        print(f"  Avg detection time: {results.avg_detection_time_days:.1f} days")
        print()

        print(f"Economic Outcomes:")
        print(f"  Honest avg ROI: {results.honest_avg_roi * 100:+.1f}%")
        print(f"  Malicious avg ROI: {results.malicious_avg_roi * 100:+.1f}%")
        print(f"  Malicious avg profit: {results.malicious_avg_profit:+,.0f} ATP")
        print(f"  Profitable attacks: {results.profitable_attacks_pct * 100:.1f}%")
        print()

        # Nash equilibrium analysis
        if results.honest_avg_roi > results.malicious_avg_roi:
            print("Nash Equilibrium: ✓ HONEST STRATEGY DOMINATES")
            advantage = results.honest_avg_roi - results.malicious_avg_roi
            print(f"  Honest advantage: {advantage * 100:+.1f} percentage points")
        else:
            print("Nash Equilibrium: ✗ MALICIOUS STRATEGY PROFITABLE")
            advantage = results.malicious_avg_roi - results.honest_avg_roi
            print(f"  Malicious advantage: {advantage * 100:+.1f} percentage points")
        print()

        # Deterrence assessment
        if results.malicious_avg_roi < -0.20:
            print("Deterrence Level: ✅ STRONG (>20% expected loss)")
        elif results.malicious_avg_roi < 0.0:
            print("Deterrence Level: ⚠️ MARGINAL (0-20% expected loss)")
        else:
            print("Deterrence Level: ❌ WEAK (profitable attack)")
        print()


def main():
    """Run attack simulations."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "Agent-Based Attack Simulation" + " " * 31 + "║")
    print("║" + " " * 22 + "Web4 ATP Economics" + " " * 36 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Empirically validating ATP stake deterrence via agent-based simulation.")
    print("Priority #1 from Session #40 ATP Economic Analysis.")
    print()

    params = EconomicParameters()
    sim = AttackSimulation(params)

    print("Parameters:")
    print(f"  GLOBAL LCT stake: {params.global_lct_stake:,.0f} ATP")
    print(f"  Challenge rate: 10% base (adaptive based on reputation)")
    print(f"  Detection threshold: 3 quality mismatches")
    print(f"  Tasks per day: 100")
    print(f"  Simulation duration: 30 days")
    print()

    # Scenario 1: Quality Inflation Attack
    print("Running Scenario 1: Quality Inflation Attack...")
    print("  Malicious strategy: Deliver medium quality, claim high quality")
    print("  Expected markup: 30% (56 ATP claimed vs 34 ATP actual)")
    print()

    results = sim.simulate_quality_inflation_attack(
        num_honest=10,
        num_malicious=5,
        simulation_days=30,
        tasks_per_day=100
    )

    sim.print_results(results)

    print("=" * 80)
    print("Key Findings")
    print("=" * 80)
    print()

    if results.avg_detection_time_days < 5:
        print(f"✓ Detection is FAST ({results.avg_detection_time_days:.1f} days)")
        print("  Current 75k ATP stake is EFFECTIVE deterrent")
    elif results.avg_detection_time_days < 10:
        print(f"⚠ Detection is MODERATE ({results.avg_detection_time_days:.1f} days)")
        print("  Marginal deterrence - consider increasing challenge rate")
    else:
        print(f"✗ Detection is SLOW ({results.avg_detection_time_days:.1f} days)")
        print("  WEAK deterrence - increase stakes or detection rate")
    print()

    if results.malicious_avg_roi < 0:
        print(f"✓ Attacks are UNPROFITABLE ({results.malicious_avg_roi * 100:.1f}% ROI)")
        print("  Economic deterrence working as designed")
    else:
        print(f"✗ Attacks are PROFITABLE ({results.malicious_avg_roi * 100:.1f}% ROI)")
        print("  Need to increase stakes or improve detection")
    print()

    print("Validation Status:")
    print(f"  Session #40 hypothesis: 'Stakes ARE deterrent IF detection < 5 days'")
    print(f"  Empirical result: Detection = {results.avg_detection_time_days:.1f} days, ROI = {results.malicious_avg_roi * 100:.1f}%")

    if results.avg_detection_time_days < 5 and results.malicious_avg_roi < 0:
        print(f"  ✅ HYPOTHESIS CONFIRMED")
    else:
        print(f"  ⚠️ HYPOTHESIS NEEDS REFINEMENT")
    print()


if __name__ == "__main__":
    main()
