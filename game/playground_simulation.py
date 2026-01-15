#!/usr/bin/env python3
"""Playground Simulation - Fast, Configurable Web4 Agent Simulation

Designed specifically for interactive parameter exploration in 4-life playground.
Optimized for speed and simplicity while demonstrating core Web4 mechanics.

Key features:
- Runs in <1 second for quick feedback
- Configurable parameters (ATP costs, trust thresholds, initial conditions)
- Minimal dependencies (no HRM/SAGE required)
- Returns structured JSON for visualization
- Demonstrates core mechanics: ATP economics, trust evolution, death/rebirth

Session #12: Interactive Parameter Playground
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import random


@dataclass
class PlaygroundConfig:
    """User-configurable simulation parameters"""

    # Agent initial conditions
    initial_atp: float = 100.0
    initial_trust: float = 0.5

    # Action costs/rewards
    action_cost_low: float = 5.0      # Low-cost actions (observe, wait)
    action_cost_medium: float = 15.0  # Medium-cost actions (collaborate, message)
    action_cost_high: float = 30.0    # High-cost actions (broadcast, challenge)

    action_reward_low: float = 8.0
    action_reward_medium: float = 20.0
    action_reward_high: float = 45.0

    # Trust dynamics
    trust_gain_good: float = 0.05     # Trust gained from successful action
    trust_loss_bad: float = 0.08      # Trust lost from failed action
    trust_threshold_death: float = 0.2  # Die if trust drops below this

    # Rebirth karma
    karma_atp_bonus: float = 40.0     # ATP bonus/penalty based on previous trust
    karma_trust_boost: float = 0.1    # Trust boost for high-trust rebirth

    # Simulation parameters
    num_lives: int = 3
    ticks_per_life: int = 15

    # Behavioral tendency (0.0 = risk-averse, 1.0 = risk-seeking)
    risk_appetite: float = 0.5


@dataclass
class ActionOutcome:
    """Result of a single agent action"""
    tick: int
    action_type: str
    atp_cost: float
    atp_reward: float
    trust_change: float
    success: bool
    atp_after: float
    trust_after: float


@dataclass
class LifeSummary:
    """Summary of one life cycle"""
    life_id: str
    start_tick: int
    end_tick: int
    initial_atp: float
    initial_trust: float
    final_atp: float
    final_trust: float
    termination_reason: str  # "completed", "atp_exhausted", "trust_lost"
    actions: List[ActionOutcome]
    atp_history: List[float]
    trust_history: List[float]


@dataclass
class PlaygroundResult:
    """Complete simulation result"""
    config: PlaygroundConfig
    lives: List[LifeSummary]
    total_ticks: int
    insights: List[str]


class PlaygroundAgent:
    """Simplified agent for playground simulations"""

    def __init__(self, config: PlaygroundConfig):
        self.config = config
        self.atp = config.initial_atp
        self.trust = config.initial_trust
        self.tick = 0

    def choose_action(self) -> tuple[str, float, float]:
        """
        Choose an action based on current state and risk appetite.

        Returns: (action_type, cost, potential_reward)
        """
        # Risk-averse when ATP is low or trust is low
        desperation = 1.0 - (self.atp / 100.0)
        trust_confidence = self.trust
        effective_risk_appetite = self.config.risk_appetite * trust_confidence - desperation * 0.3

        # Choose action tier based on risk appetite
        if effective_risk_appetite < 0.3:
            # Low-risk action
            return ("observe", self.config.action_cost_low, self.config.action_reward_low)
        elif effective_risk_appetite < 0.7:
            # Medium-risk action
            return ("collaborate", self.config.action_cost_medium, self.config.action_reward_medium)
        else:
            # High-risk action
            return ("broadcast", self.config.action_cost_high, self.config.action_reward_high)

    def execute_action(self, action_type: str, cost: float, potential_reward: float) -> ActionOutcome:
        """
        Execute an action and update agent state.

        Success probability based on trust (high trust = more likely to succeed)
        """
        self.tick += 1

        # Spend ATP
        self.atp -= cost

        # Determine success (higher trust = higher success chance)
        # Base success rate: 60% + trust bonus (up to 30% more)
        success_chance = 0.6 + (self.trust * 0.3)
        success = random.random() < success_chance

        # Calculate outcomes
        reward = potential_reward if success else 0.0
        self.atp += reward

        # Trust evolution
        if success:
            trust_change = self.config.trust_gain_good
        else:
            trust_change = -self.config.trust_loss_bad

        self.trust += trust_change
        self.trust = max(0.0, min(1.0, self.trust))  # Clamp to [0, 1]

        return ActionOutcome(
            tick=self.tick,
            action_type=action_type,
            atp_cost=cost,
            atp_reward=reward,
            trust_change=trust_change,
            success=success,
            atp_after=self.atp,
            trust_after=self.trust
        )

    def is_alive(self) -> tuple[bool, str]:
        """Check if agent is still alive"""
        if self.atp <= 0:
            return False, "atp_exhausted"
        if self.trust < self.config.trust_threshold_death:
            return False, "trust_lost"
        return True, ""

    def apply_karma(self, previous_trust: float) -> None:
        """Apply karma from previous life to current life's initial conditions"""
        # Trust-based ATP bonus/penalty
        trust_delta = previous_trust - 0.5  # How far from neutral
        atp_adjustment = trust_delta * self.config.karma_atp_bonus
        self.atp += atp_adjustment

        # Trust boost for high performers
        if previous_trust > 0.7:
            self.trust += self.config.karma_trust_boost
        elif previous_trust < 0.3:
            self.trust -= self.config.karma_trust_boost * 0.5

        self.trust = max(0.0, min(1.0, self.trust))


def run_playground_simulation(config: PlaygroundConfig) -> PlaygroundResult:
    """
    Run a complete multi-life simulation with the given configuration.

    Returns structured result for visualization.
    """
    lives: List[LifeSummary] = []
    total_ticks = 0
    insights: List[str] = []

    previous_life_trust: Optional[float] = None

    for life_num in range(1, config.num_lives + 1):
        life_id = f"life_{life_num}"

        # Create agent
        agent = PlaygroundAgent(config)

        # Apply karma from previous life
        if previous_life_trust is not None:
            agent.apply_karma(previous_life_trust)
            if previous_life_trust > 0.7:
                insights.append(f"Life {life_num}: High karma rebirth (+{config.karma_atp_bonus * (previous_life_trust - 0.5):.1f} ATP)")
            elif previous_life_trust < 0.3:
                insights.append(f"Life {life_num}: Low karma rebirth ({config.karma_atp_bonus * (previous_life_trust - 0.5):.1f} ATP)")

        start_tick = total_ticks
        initial_atp = agent.atp
        initial_trust = agent.trust

        actions: List[ActionOutcome] = []
        atp_history: List[float] = [agent.atp]
        trust_history: List[float] = [agent.trust]

        # Run life
        for _ in range(config.ticks_per_life):
            action_type, cost, reward = agent.choose_action()
            outcome = agent.execute_action(action_type, cost, reward)

            actions.append(outcome)
            atp_history.append(agent.atp)
            trust_history.append(agent.trust)

            # Check if still alive
            alive, termination_reason = agent.is_alive()
            if not alive:
                break

        total_ticks += agent.tick
        end_tick = total_ticks

        # Determine termination reason
        alive, termination_reason = agent.is_alive()
        if alive:
            termination_reason = "completed"

        # Record life summary
        life = LifeSummary(
            life_id=life_id,
            start_tick=start_tick,
            end_tick=end_tick,
            initial_atp=initial_atp,
            initial_trust=initial_trust,
            final_atp=agent.atp,
            final_trust=agent.trust,
            termination_reason=termination_reason,
            actions=actions,
            atp_history=atp_history,
            trust_history=trust_history
        )
        lives.append(life)

        # Generate insights
        if termination_reason == "atp_exhausted":
            insights.append(f"Life {life_num}: Died from ATP exhaustion (too many expensive actions?)")
        elif termination_reason == "trust_lost":
            insights.append(f"Life {life_num}: Died from trust loss (too many failures?)")
        elif agent.trust > 0.7:
            insights.append(f"Life {life_num}: Thrived with {agent.trust:.2f} trust!")

        # Store for next life
        previous_life_trust = agent.trust

    # Generate cross-life insights
    survived_all = all(life.termination_reason == "completed" for life in lives)
    if survived_all:
        insights.append(f"🎯 Survived all {config.num_lives} lives! Parameters well-tuned.")

    avg_final_trust = sum(life.final_trust for life in lives) / len(lives)
    if avg_final_trust > 0.6:
        insights.append(f"📈 Strong trust trajectory (avg: {avg_final_trust:.2f})")
    elif avg_final_trust < 0.4:
        insights.append(f"📉 Weak trust trajectory (avg: {avg_final_trust:.2f})")

    return PlaygroundResult(
        config=config,
        lives=lives,
        total_ticks=total_ticks,
        insights=insights
    )


def main():
    """Run demo simulation with default config"""
    config = PlaygroundConfig()
    result = run_playground_simulation(config)

    # Print summary
    print("=== Playground Simulation Results ===\n")
    for life in result.lives:
        print(f"{life.life_id}:")
        print(f"  Ticks: {life.start_tick}-{life.end_tick}")
        print(f"  ATP: {life.initial_atp:.1f} → {life.final_atp:.1f}")
        print(f"  Trust: {life.initial_trust:.2f} → {life.final_trust:.2f}")
        print(f"  Termination: {life.termination_reason}")
        print()

    print("Insights:")
    for insight in result.insights:
        print(f"  • {insight}")


if __name__ == "__main__":
    main()
