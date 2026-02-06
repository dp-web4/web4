#!/usr/bin/env python3
"""
ATP-Aware Agent Implementation

Implements Level 1 meta-cognition: Agents that observe their own ATP
resource state and adapt cooperation behavior accordingly.

This addresses the fundamental issue discovered in Sessions #28-29:
Coherence pricing failed because agents couldn't respond to ATP costs.
Their cooperation decisions were based on FIXED behavioral profiles,
with ATP costs applied AFTER the decision (too late to influence it).

Solution: Meta-cognitive resource awareness
- Agent observes own ATP state BEFORE deciding
- Cooperation rate adjusted based on resource availability
- Creates feedback loop: ATP costs → Resource state → Cooperation decision

Meta-Cognition Level: 1 (State Feedback)
- Level 0: No feedback (original agents)
- Level 1: State feedback (this implementation)
- Level 2: Epistemic feedback (uncertainty-aware)

Session #31 Autonomous Research
Date: 2026-01-17
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import random


@dataclass
class ResourceState:
    """Agent's observable resource state."""
    atp_current: float
    atp_max: float
    atp_regen_rate: float
    last_observation_tick: int

    @property
    def atp_ratio(self) -> float:
        """ATP as ratio of maximum [0.0, 1.0]."""
        return self.atp_current / self.atp_max if self.atp_max > 0 else 0.0

    @property
    def is_depleted(self) -> bool:
        """Check if ATP is critically low."""
        return self.atp_ratio < 0.20  # Less than 20% remaining

    @property
    def is_abundant(self) -> bool:
        """Check if ATP is plentiful."""
        return self.atp_ratio > 0.80  # More than 80% remaining

    @property
    def is_normal(self) -> bool:
        """Check if ATP is in normal range."""
        return 0.20 <= self.atp_ratio <= 0.80


@dataclass
class BehavioralProfile:
    """Agent's behavioral characteristics."""
    name: str
    base_cooperation_rate: float  # Base cooperation probability [0.0, 1.0]
    reliability: float  # Reliability when cooperating [0.0, 1.0]
    description: str

    # ATP-awareness parameters (NEW)
    atp_awareness_enabled: bool = True  # Enable meta-cognitive resource awareness
    depletion_penalty: float = 0.5     # Cooperation reduction when depleted
    abundance_bonus: float = 0.2        # Cooperation increase when abundant


class ATPAwareAgent:
    """
    Agent with Level 1 meta-cognition: Resource state awareness.

    Implements feedback loop:
    ATP state → Cooperation decision → ATP consumption → ATP state

    This closes the loop that was missing in original trust network agents.
    """

    def __init__(self, agent_id: str, profile: BehavioralProfile,
                 initial_atp: float = 100.0, max_atp: float = 150.0,
                 atp_regen_rate: float = 5.0):
        """
        Initialize ATP-aware agent.

        Args:
            agent_id: Unique agent identifier
            profile: Behavioral profile with cooperation parameters
            initial_atp: Starting ATP
            max_atp: Maximum ATP capacity
            atp_regen_rate: ATP regeneration per tick
        """
        self.agent_id = agent_id
        self.profile = profile
        self.resource_state = ResourceState(
            atp_current=initial_atp,
            atp_max=max_atp,
            atp_regen_rate=atp_regen_rate,
            last_observation_tick=0
        )

        # Statistics
        self.total_cooperations = 0
        self.total_defections = 0
        self.atp_spent = 0.0
        self.decisions_by_state = {
            "depleted": {"cooperate": 0, "defect": 0},
            "normal": {"cooperate": 0, "defect": 0},
            "abundant": {"cooperate": 0, "defect": 0}
        }

    def observe_resource_state(self, current_tick: int) -> ResourceState:
        """
        Meta-cognitive introspection: Observe own ATP state.

        This is the core Level 1 meta-cognition capability:
        Agent can observe its own internal resource state.

        Args:
            current_tick: Current simulation tick

        Returns:
            Current resource state observation
        """
        self.resource_state.last_observation_tick = current_tick
        return self.resource_state

    def estimate_action_cost(self, action: str, target: Optional[str] = None) -> float:
        """
        Estimate ATP cost of an action before performing it.

        This enables proactive decision-making based on anticipated costs.

        Args:
            action: Action type ("cooperate", "defect", etc.)
            target: Target agent (for relationship-based costs)

        Returns:
            Estimated ATP cost
        """
        # Simple cost model (would integrate with coherence pricing in full implementation)
        base_costs = {
            "cooperate": 10.0,  # Helping costs ATP
            "defect": 2.0,      # Defecting is cheap
            "neutral": 1.0      # Neutral action minimal cost
        }
        return base_costs.get(action, 5.0)

    def calculate_effective_cooperation_rate(self, current_tick: int,
                                            estimated_cost: float) -> float:
        """
        Calculate cooperation rate adjusted for ATP state.

        This is where meta-cognition affects behavior:
        - Observe ATP state
        - Consider action cost
        - Adjust cooperation probability accordingly

        Args:
            current_tick: Current simulation tick
            estimated_cost: Estimated ATP cost of cooperation

        Returns:
            Effective cooperation rate [0.0, 1.0]
        """
        # Meta-cognitive observation
        state = self.observe_resource_state(current_tick)

        # Base cooperation rate from profile
        base_rate = self.profile.base_cooperation_rate

        # If ATP awareness disabled, return base rate (Level 0 behavior)
        if not self.profile.atp_awareness_enabled:
            return base_rate

        # ATP-aware adjustment (Level 1 behavior)
        if state.is_depleted:
            # Low ATP → Reduce cooperation
            # Can't afford to help others when own resources critical
            adjustment_factor = 1.0 - self.profile.depletion_penalty
            effective_rate = base_rate * adjustment_factor

        elif state.is_abundant:
            # High ATP → Increase cooperation
            # Can afford to be generous when resources plentiful
            adjustment_factor = 1.0 + self.profile.abundance_bonus
            effective_rate = min(1.0, base_rate * adjustment_factor)

        else:
            # Normal ATP → Use base rate
            effective_rate = base_rate

        # Further adjustment if cost exceeds current ATP
        if estimated_cost > state.atp_current:
            # Literally cannot afford this action
            effective_rate *= 0.1  # Drastically reduce (not zero, might get lucky)

        return max(0.0, min(1.0, effective_rate))

    def decide_cooperation(self, target_agent: str, current_tick: int) -> bool:
        """
        Decide whether to cooperate with target agent.

        Implements meta-cognitive decision process:
        1. Estimate cost of cooperation
        2. Observe own ATP state
        3. Calculate effective cooperation rate based on state
        4. Make probabilistic decision
        5. Record decision statistics

        Args:
            target_agent: Target agent ID
            current_tick: Current simulation tick

        Returns:
            True if cooperating, False if defecting
        """
        # Estimate cost BEFORE deciding (unlike original agents)
        estimated_cost = self.estimate_action_cost("cooperate", target_agent)

        # Calculate ATP-aware cooperation rate
        effective_rate = self.calculate_effective_cooperation_rate(
            current_tick, estimated_cost
        )

        # Make probabilistic decision
        cooperates = random.random() < effective_rate

        # Record statistics by resource state
        state = self.resource_state
        if state.is_depleted:
            state_key = "depleted"
        elif state.is_abundant:
            state_key = "abundant"
        else:
            state_key = "normal"

        if cooperates:
            self.total_cooperations += 1
            self.decisions_by_state[state_key]["cooperate"] += 1
        else:
            self.total_defections += 1
            self.decisions_by_state[state_key]["defect"] += 1

        return cooperates

    def consume_atp(self, amount: float, reason: str = "action"):
        """
        Consume ATP for an action.

        Called AFTER decision is made but BEFORE next decision.
        This updates the state that will be observed in next decision.

        Args:
            amount: ATP to consume
            reason: Reason for consumption (for logging)
        """
        self.resource_state.atp_current -= amount
        self.resource_state.atp_current = max(0.0, self.resource_state.atp_current)
        self.atp_spent += amount

    def regenerate_atp(self, current_tick: int):
        """
        Regenerate ATP at the start of a tick.

        Args:
            current_tick: Current simulation tick
        """
        regen = self.resource_state.atp_regen_rate
        self.resource_state.atp_current = min(
            self.resource_state.atp_max,
            self.resource_state.atp_current + regen
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get agent statistics for analysis.

        Returns:
            Dictionary of statistics
        """
        total_decisions = self.total_cooperations + self.total_defections
        cooperation_rate = (self.total_cooperations / total_decisions
                          if total_decisions > 0 else 0.0)

        # Calculate cooperation rate by resource state
        state_cooperation_rates = {}
        for state_name, decisions in self.decisions_by_state.items():
            total = decisions["cooperate"] + decisions["defect"]
            rate = decisions["cooperate"] / total if total > 0 else 0.0
            state_cooperation_rates[state_name] = rate

        return {
            "agent_id": self.agent_id,
            "profile": self.profile.name,
            "total_cooperations": self.total_cooperations,
            "total_defections": self.total_defections,
            "overall_cooperation_rate": cooperation_rate,
            "cooperation_rate_by_state": state_cooperation_rates,
            "atp_current": self.resource_state.atp_current,
            "atp_ratio": self.resource_state.atp_ratio,
            "atp_spent": self.atp_spent,
            "decisions_by_state": self.decisions_by_state
        }


# Example usage and comparison
if __name__ == "__main__":
    print("=" * 80)
    print("  ATP-AWARE AGENT DEMONSTRATION")
    print("  Level 1 Meta-Cognition: Resource State Awareness")
    print("=" * 80)

    # Create behavioral profile
    profile = BehavioralProfile(
        name="Cooperative",
        base_cooperation_rate=0.70,
        reliability=0.85,
        description="Tends to cooperate",
        atp_awareness_enabled=True,
        depletion_penalty=0.5,  # 50% reduction when depleted
        abundance_bonus=0.2     # 20% increase when abundant
    )

    # Create agent
    agent = ATPAwareAgent(
        agent_id="agent_001",
        profile=profile,
        initial_atp=100.0,
        max_atp=150.0,
        atp_regen_rate=5.0
    )

    print("\n" + "=" * 80)
    print("Test 1: Normal ATP State")
    print("=" * 80)
    print(f"\nInitial ATP: {agent.resource_state.atp_current:.1f}")
    print(f"ATP Ratio: {agent.resource_state.atp_ratio:.2f}")
    print(f"Base cooperation rate: {profile.base_cooperation_rate:.2f}")

    effective_rate = agent.calculate_effective_cooperation_rate(
        current_tick=0,
        estimated_cost=10.0
    )
    print(f"Effective cooperation rate: {effective_rate:.2f}")
    print(f"State: {'Normal' if agent.resource_state.is_normal else 'Other'}")

    print("\n" + "=" * 80)
    print("Test 2: Depleted ATP State")
    print("=" * 80)
    # Deplete ATP
    agent.resource_state.atp_current = 25.0  # 16.7% of max
    print(f"\nDepleted ATP: {agent.resource_state.atp_current:.1f}")
    print(f"ATP Ratio: {agent.resource_state.atp_ratio:.2f}")

    effective_rate = agent.calculate_effective_cooperation_rate(
        current_tick=1,
        estimated_cost=10.0
    )
    print(f"Effective cooperation rate: {effective_rate:.2f}")
    print(f"State: {'Depleted' if agent.resource_state.is_depleted else 'Other'}")
    print(f"Reduction: {profile.base_cooperation_rate - effective_rate:.2f} "
          f"({(1 - effective_rate/profile.base_cooperation_rate)*100:.0f}%)")

    print("\n" + "=" * 80)
    print("Test 3: Abundant ATP State")
    print("=" * 80)
    # Restore to abundant
    agent.resource_state.atp_current = 140.0  # 93% of max
    print(f"\nAbundant ATP: {agent.resource_state.atp_current:.1f}")
    print(f"ATP Ratio: {agent.resource_state.atp_ratio:.2f}")

    effective_rate = agent.calculate_effective_cooperation_rate(
        current_tick=2,
        estimated_cost=10.0
    )
    print(f"Effective cooperation rate: {effective_rate:.2f}")
    print(f"State: {'Abundant' if agent.resource_state.is_abundant else 'Other'}")
    print(f"Increase: {effective_rate - profile.base_cooperation_rate:.2f} "
          f"({(effective_rate/profile.base_cooperation_rate - 1)*100:.0f}%)")

    print("\n" + "=" * 80)
    print("Test 4: Simulation Over Time")
    print("=" * 80)

    # Reset agent
    agent = ATPAwareAgent(
        agent_id="agent_002",
        profile=profile,
        initial_atp=100.0,
        max_atp=150.0,
        atp_regen_rate=5.0
    )

    print("\nSimulating 20 ticks with cooperation decisions...\n")
    print("| Tick | ATP  | State     | Eff Rate | Decision | ATP After |")
    print("|------|------|-----------|----------|----------|-----------|")

    for tick in range(20):
        # Regenerate ATP at start of tick
        agent.regenerate_atp(tick)

        # Make decision
        cooperates = agent.decide_cooperation("target", tick)

        # Record state before consumption
        atp_before = agent.resource_state.atp_current
        state = ("Depleted" if agent.resource_state.is_depleted
                else "Abundant" if agent.resource_state.is_abundant
                else "Normal")
        eff_rate = agent.calculate_effective_cooperation_rate(tick, 10.0)

        # Consume ATP based on decision
        cost = 10.0 if cooperates else 2.0
        agent.consume_atp(cost, "cooperation" if cooperates else "defection")

        # Display
        decision = "Cooperate" if cooperates else "Defect   "
        print(f"| {tick:4d} | {atp_before:4.0f} | {state:9s} | {eff_rate:8.2f} | "
              f"{decision} | {agent.resource_state.atp_current:9.1f} |")

    print("\n" + "=" * 80)
    print("Final Statistics")
    print("=" * 80)

    stats = agent.get_statistics()
    print(f"\nOverall cooperation rate: {stats['overall_cooperation_rate']:.2%}")
    print("\nCooperation rate by ATP state:")
    for state_name, rate in stats['cooperation_rate_by_state'].items():
        print(f"  {state_name.capitalize():9s}: {rate:.2%}")

    print(f"\nDecisions by state:")
    for state_name, decisions in stats['decisions_by_state'].items():
        total = decisions['cooperate'] + decisions['defect']
        if total > 0:
            print(f"  {state_name.capitalize():9s}: "
                  f"{decisions['cooperate']} cooperate, "
                  f"{decisions['defect']} defect "
                  f"(n={total})")

    print(f"\nFinal ATP: {stats['atp_current']:.1f} / {agent.resource_state.atp_max}")
    print(f"Total ATP spent: {stats['atp_spent']:.1f}")

    print("\n" + "=" * 80)
    print("  KEY INSIGHT: META-COGNITIVE FEEDBACK LOOP")
    print("=" * 80)
    print()
    print("BEFORE (Level 0 - No Feedback):")
    print("  cooperates = random.random() < base_cooperation_rate")
    print("  agent.atp -= cost  # Too late to affect decision!")
    print()
    print("AFTER (Level 1 - State Feedback):")
    print("  state = agent.observe_resource_state()  # Introspection")
    print("  effective_rate = adjust_for_state(base_rate, state)")
    print("  cooperates = random.random() < effective_rate")
    print("  agent.atp -= cost  # Updates state for next decision")
    print()
    print("RESULT: Coherence pricing now affects behavior!")
    print("  - Low ATP (depleted) → Reduced cooperation")
    print("  - High ATP (abundant) → Increased cooperation")
    print("  - Feedback loop closed: Cost → State → Decision → Cost")
    print()
    print("=" * 80)
