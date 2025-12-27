#!/usr/bin/env python3
"""
Session 92 Track 2: Metabolic State-Dependent Reputation

**Date**: 2025-12-26
**Platform**: Legion (RTX 4090)
**Track**: 2 of 4 - State-Dependent Reputation

## Problem Statement

Current Web4 reputation is static - an agent has one reputation score regardless of context.

**Issue**: Agents perform differently in different metabolic/emotional states:
- FOCUS state: Higher quality work, better reasoning
- WAKE state: Normal baseline performance
- REST state: Reduced capacity, may defer work
- CRISIS state: Emergency mode, minimal functionality
- DREAM state: Background processing only

**Static reputation fails to capture state-dependent capability!**

## Solution: State-Dependent Reputation

Track reputation separately per metabolic state:

```python
reputation = {
    MetabolicState.FOCUS: 0.95,   # High quality in focus
    MetabolicState.WAKE: 0.80,    # Good baseline
    MetabolicState.REST: 0.65,    # Reduced in rest
    MetabolicState.CRISIS: 0.30,  # Low in crisis
    MetabolicState.DREAM: 0.10,   # Background only
}
```

When requesting work from an agent, check their CURRENT state to predict quality.

## Key Innovations

1. **State-Aware Task Assignment**: Route high-priority tasks to agents in FOCUS/WAKE
2. **Predictive Quality Estimation**: Use state-specific reputation for quality prediction
3. **Fair Reputation Tracking**: Don't penalize REST/CRISIS performance against FOCUS baseline
4. **Metabolic State Disclosure**: Agents advertise current state in attestations
5. **Dynamic Trust Adjustment**: Trust level varies with metabolic state

## Integration with SAGE

SAGE (Sessions 120-123) developed 5 metabolic states with resource budgets:
- WAKE: 100 ATP, 2.4/1.2/12.0 recovery (C/M/T)
- FOCUS: 150 ATP, 1.5/0.8/8.0 recovery
- REST: 60 ATP, 4.0/2.0/16.0 recovery
- DREAM: 40 ATP, 3.0/3.5/5.0 recovery (memory-biased)
- CRISIS: 30 ATP, 1.0/0.5/3.0 recovery

Web4 now uses these states to modulate trust/reputation.

## Test Scenarios

1. **State-Dependent Quality**: Same agent, different states, different outcomes
2. **Task Routing**: High-priority task routed to FOCUS agent, not REST agent
3. **Fair Penalization**: REST performance doesn't damage WAKE reputation
4. **State Transitions**: Reputation updates as agent transitions WAKE → FOCUS → REST
5. **Cross-Society Comparison**: Compare agents across societies accounting for states
"""

import json
import time
import secrets
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path

# Import metabolic states from SAGE (conceptual - would need actual SAGE integration)
class MetabolicState(Enum):
    """Metabolic states from SAGE Sessions 120-123."""
    WAKE = "wake"
    FOCUS = "focus"
    REST = "rest"
    DREAM = "dream"
    CRISIS = "crisis"


@dataclass
class StateParameters:
    """Resource parameters for each metabolic state."""
    atp_budget: float
    compute_recovery: float
    memory_recovery: float
    tool_recovery: float
    quality_multiplier: float  # Expected quality in this state (vs WAKE baseline)


# State parameters from SAGE Session 122
STATE_PARAMS = {
    MetabolicState.WAKE: StateParameters(
        atp_budget=100.0,
        compute_recovery=2.4,
        memory_recovery=1.2,
        tool_recovery=12.0,
        quality_multiplier=1.0  # Baseline
    ),
    MetabolicState.FOCUS: StateParameters(
        atp_budget=150.0,
        compute_recovery=1.5,
        memory_recovery=0.8,
        tool_recovery=8.0,
        quality_multiplier=1.3  # 30% better quality
    ),
    MetabolicState.REST: StateParameters(
        atp_budget=60.0,
        compute_recovery=4.0,
        memory_recovery=2.0,
        tool_recovery=16.0,
        quality_multiplier=0.7  # 30% reduced quality
    ),
    MetabolicState.DREAM: StateParameters(
        atp_budget=40.0,
        compute_recovery=3.0,
        memory_recovery=3.5,
        tool_recovery=5.0,
        quality_multiplier=0.2  # Background only
    ),
    MetabolicState.CRISIS: StateParameters(
        atp_budget=30.0,
        compute_recovery=1.0,
        memory_recovery=0.5,
        tool_recovery=3.0,
        quality_multiplier=0.4  # Emergency mode, low quality
    ),
}


@dataclass
class StateDependentReputation:
    """Reputation tracked separately per metabolic state."""

    # Reputation by state (0.0 - 1.0)
    focus_reputation: float = 0.5
    wake_reputation: float = 0.5
    rest_reputation: float = 0.5
    crisis_reputation: float = 0.5
    dream_reputation: float = 0.5

    # Sample counts (for statistical confidence)
    focus_samples: int = 0
    wake_samples: int = 0
    rest_samples: int = 0
    crisis_samples: int = 0
    dream_samples: int = 0

    # Overall reputation (weighted average, WAKE-biased)
    overall_reputation: float = 0.5

    def get_reputation(self, state: MetabolicState) -> float:
        """Get reputation for specific state."""
        mapping = {
            MetabolicState.FOCUS: self.focus_reputation,
            MetabolicState.WAKE: self.wake_reputation,
            MetabolicState.REST: self.rest_reputation,
            MetabolicState.CRISIS: self.crisis_reputation,
            MetabolicState.DREAM: self.dream_reputation,
        }
        return mapping.get(state, 0.5)

    def get_sample_count(self, state: MetabolicState) -> int:
        """Get sample count for specific state."""
        mapping = {
            MetabolicState.FOCUS: self.focus_samples,
            MetabolicState.WAKE: self.wake_samples,
            MetabolicState.REST: self.rest_samples,
            MetabolicState.CRISIS: self.crisis_samples,
            MetabolicState.DREAM: self.dream_samples,
        }
        return mapping.get(state, 0)

    def update_reputation(
        self,
        state: MetabolicState,
        outcome_quality: float,
        learning_rate: float = 0.1
    ):
        """Update reputation for specific state based on outcome.

        Uses exponential moving average:
        new_rep = (1 - lr) * old_rep + lr * outcome
        """
        current_rep = self.get_reputation(state)
        new_rep = (1 - learning_rate) * current_rep + learning_rate * outcome_quality

        # Update state-specific reputation
        if state == MetabolicState.FOCUS:
            self.focus_reputation = new_rep
            self.focus_samples += 1
        elif state == MetabolicState.WAKE:
            self.wake_reputation = new_rep
            self.wake_samples += 1
        elif state == MetabolicState.REST:
            self.rest_reputation = new_rep
            self.rest_samples += 1
        elif state == MetabolicState.CRISIS:
            self.crisis_reputation = new_rep
            self.crisis_samples += 1
        elif state == MetabolicState.DREAM:
            self.dream_reputation = new_rep
            self.dream_samples += 1

        # Recompute overall reputation (WAKE-weighted average)
        total_samples = (
            self.focus_samples + self.wake_samples + self.rest_samples +
            self.crisis_samples + self.dream_samples
        )

        if total_samples > 0:
            # Weight WAKE 2x, others 1x
            wake_weight = 2.0
            weighted_sum = (
                self.focus_reputation * self.focus_samples +
                self.wake_reputation * self.wake_samples * wake_weight +
                self.rest_reputation * self.rest_samples +
                self.crisis_reputation * self.crisis_samples +
                self.dream_reputation * self.dream_samples
            )
            weight_total = (
                self.focus_samples + self.wake_samples * wake_weight +
                self.rest_samples + self.crisis_samples + self.dream_samples
            )
            self.overall_reputation = weighted_sum / weight_total


@dataclass
class AgentProfile:
    """Agent profile with current metabolic state and reputation."""
    agent_id: str
    current_state: MetabolicState
    reputation: StateDependentReputation = field(default_factory=StateDependentReputation)
    state_transition_history: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def predict_quality(self) -> float:
        """Predict quality for current state.

        Combines:
        - State-specific reputation
        - Expected quality multiplier for state
        """
        state_rep = self.reputation.get_reputation(self.current_state)
        state_multiplier = STATE_PARAMS[self.current_state].quality_multiplier

        # Predicted quality is reputation weighted by state capability
        # If agent has 0.8 reputation in FOCUS (1.3x multiplier), predict 0.8 * 1.3 = 1.04 quality
        # If same agent in REST (0.7x multiplier), predict 0.8 * 0.7 = 0.56 quality
        return state_rep * state_multiplier

    def transition_state(self, new_state: MetabolicState):
        """Transition to new metabolic state."""
        old_state = self.current_state
        self.current_state = new_state

        self.state_transition_history.append({
            "timestamp": time.time(),
            "from_state": old_state.value,
            "to_state": new_state.value
        })


class MetabolicReputationTracker:
    """Track reputation across metabolic states for multiple agents."""

    def __init__(self):
        self.agents: Dict[str, AgentProfile] = {}

    def register_agent(
        self,
        agent_id: str,
        initial_state: MetabolicState = MetabolicState.WAKE
    ) -> AgentProfile:
        """Register new agent."""
        profile = AgentProfile(
            agent_id=agent_id,
            current_state=initial_state
        )
        self.agents[agent_id] = profile
        return profile

    def record_outcome(
        self,
        agent_id: str,
        outcome_quality: float,
        task_state: Optional[MetabolicState] = None
    ):
        """Record task outcome for agent.

        Args:
            agent_id: Agent identifier
            outcome_quality: Quality of outcome (0.0 - 1.0)
            task_state: State agent was in when performing task (default: current)
        """
        if agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {agent_id}")

        profile = self.agents[agent_id]
        state = task_state if task_state else profile.current_state

        profile.reputation.update_reputation(state, outcome_quality)

    def select_best_agent(
        self,
        candidates: List[str],
        min_quality: float = 0.7
    ) -> Optional[str]:
        """Select best agent for task based on predicted quality.

        Args:
            candidates: List of agent IDs
            min_quality: Minimum acceptable predicted quality

        Returns:
            Best agent ID or None if no agent meets threshold
        """
        best_agent = None
        best_quality = min_quality

        for agent_id in candidates:
            if agent_id not in self.agents:
                continue

            profile = self.agents[agent_id]
            predicted = profile.predict_quality()

            if predicted > best_quality:
                best_quality = predicted
                best_agent = agent_id

        return best_agent

    def get_state_statistics(self) -> Dict:
        """Get statistics about agent states and reputation."""
        stats = {
            "total_agents": len(self.agents),
            "by_state": {},
            "avg_reputation_by_state": {}
        }

        # Count agents per state
        for state in MetabolicState:
            count = sum(1 for p in self.agents.values() if p.current_state == state)
            stats["by_state"][state.value] = count

        # Average reputation per state (across all agents)
        for state in MetabolicState:
            reps = [p.reputation.get_reputation(state) for p in self.agents.values()]
            stats["avg_reputation_by_state"][state.value] = sum(reps) / len(reps) if reps else 0.0

        return stats


# =============================================================================
# Test Scenarios
# =============================================================================

def test_state_dependent_quality():
    """Test Scenario 1: Same agent, different states, different predicted quality."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 1: State-Dependent Quality Prediction")
    print("=" * 80)

    tracker = MetabolicReputationTracker()

    # Register agent
    agent = tracker.register_agent("alice", MetabolicState.WAKE)

    # Train reputation in different states
    # WAKE: 0.8 quality
    for _ in range(10):
        tracker.record_outcome("alice", 0.8, MetabolicState.WAKE)

    # FOCUS: 0.95 quality (better in focus!)
    agent.transition_state(MetabolicState.FOCUS)
    for _ in range(10):
        tracker.record_outcome("alice", 0.95, MetabolicState.FOCUS)

    # REST: 0.6 quality (reduced in rest)
    agent.transition_state(MetabolicState.REST)
    for _ in range(10):
        tracker.record_outcome("alice", 0.6, MetabolicState.REST)

    # Now predict quality in each state
    print(f"\nAgent: alice")
    print(f"Reputation by state:")
    for state in [MetabolicState.WAKE, MetabolicState.FOCUS, MetabolicState.REST]:
        rep = agent.reputation.get_reputation(state)
        samples = agent.reputation.get_sample_count(state)
        print(f"  {state.value:8s}: {rep:.3f} ({samples} samples)")

    # Predict quality in each state
    print(f"\nPredicted quality by state:")
    for state in [MetabolicState.WAKE, MetabolicState.FOCUS, MetabolicState.REST]:
        agent.transition_state(state)
        predicted = agent.predict_quality()
        multiplier = STATE_PARAMS[state].quality_multiplier
        print(f"  {state.value:8s}: {predicted:.3f} (rep × {multiplier:.1f}x multiplier)")

    # Verify predictions match expectations
    agent.transition_state(MetabolicState.FOCUS)
    focus_pred = agent.predict_quality()

    agent.transition_state(MetabolicState.REST)
    rest_pred = agent.predict_quality()

    assert focus_pred > rest_pred, "FOCUS should predict higher quality than REST"

    return {
        "status": "success",
        "focus_predicted": focus_pred,
        "rest_predicted": rest_pred,
        "quality_ratio": focus_pred / rest_pred
    }


def test_task_routing():
    """Test Scenario 2: Route high-priority task to FOCUS agent."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 2: State-Aware Task Routing")
    print("=" * 80)

    tracker = MetabolicReputationTracker()

    # Register 3 agents in different states
    alice = tracker.register_agent("alice", MetabolicState.FOCUS)
    bob = tracker.register_agent("bob", MetabolicState.WAKE)
    charlie = tracker.register_agent("charlie", MetabolicState.REST)

    # Train similar base reputation (~0.85)
    for agent_id in ["alice", "bob", "charlie"]:
        profile = tracker.agents[agent_id]
        for _ in range(5):
            tracker.record_outcome(agent_id, 0.85, profile.current_state)

    # Select best agent for high-priority task (min_quality=0.7)
    candidates = ["alice", "bob", "charlie"]
    best = tracker.select_best_agent(candidates, min_quality=0.7)

    print(f"\nCandidates:")
    for agent_id in candidates:
        profile = tracker.agents[agent_id]
        predicted = profile.predict_quality()
        print(f"  {agent_id:8s} ({profile.current_state.value:6s}): predicted quality = {predicted:.3f}")

    print(f"\n✅ Selected agent: {best}")
    print(f"   Reason: alice in FOCUS has highest predicted quality")

    assert best == "alice", "Should select FOCUS agent for high-quality task"

    return {
        "status": "success",
        "selected_agent": best,
        "selected_state": alice.current_state.value
    }


def test_fair_penalization():
    """Test Scenario 3: REST performance doesn't damage WAKE reputation."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 3: Fair State-Specific Reputation")
    print("=" * 80)

    tracker = MetabolicReputationTracker()
    agent = tracker.register_agent("alice", MetabolicState.WAKE)

    # Build WAKE reputation (0.9)
    for _ in range(10):
        tracker.record_outcome("alice", 0.9, MetabolicState.WAKE)

    wake_rep_before = agent.reputation.wake_reputation

    # Transition to REST and perform poorly (0.5)
    agent.transition_state(MetabolicState.REST)
    for _ in range(10):
        tracker.record_outcome("alice", 0.5, MetabolicState.REST)

    wake_rep_after = agent.reputation.wake_reputation
    rest_rep = agent.reputation.rest_reputation

    print(f"\nWAKE reputation before REST work: {wake_rep_before:.3f}")
    print(f"WAKE reputation after REST work:  {wake_rep_after:.3f}")
    print(f"REST reputation after REST work:  {rest_rep:.3f}")
    print(f"\n✅ WAKE reputation unchanged: {abs(wake_rep_after - wake_rep_before) < 0.01}")
    print(f"✅ REST reputation reflects actual performance: {abs(rest_rep - 0.5) < 0.1}")

    assert abs(wake_rep_after - wake_rep_before) < 0.01, "WAKE rep should be unchanged"
    assert abs(rest_rep - 0.5) < 0.1, "REST rep should reflect poor performance"

    return {
        "status": "success",
        "wake_before": wake_rep_before,
        "wake_after": wake_rep_after,
        "rest_final": rest_rep
    }


# =============================================================================
# Main Test Execution
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SESSION 92 TRACK 2: METABOLIC STATE-DEPENDENT REPUTATION")
    print("=" * 80)

    results = {}

    # Run test scenarios
    results["scenario_1"] = test_state_dependent_quality()
    results["scenario_2"] = test_task_routing()
    results["scenario_3"] = test_fair_penalization()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_success = all(r["status"] == "success" for r in results.values())

    print(f"\n✅ All scenarios passed: {all_success}")
    print(f"\nScenarios tested:")
    print(f"  1. State-dependent quality prediction")
    print(f"  2. State-aware task routing")
    print(f"  3. Fair state-specific reputation tracking")

    # Save results
    results_file = Path(__file__).parent / "session92_track2_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to: {results_file}")

    print("\n" + "=" * 80)
    print("Key Innovations:")
    print("=" * 80)
    print("1. Reputation tracked separately per metabolic state")
    print("2. Predicted quality = state reputation × state capability multiplier")
    print("3. Task routing uses current state to select best agent")
    print("4. REST/CRISIS performance doesn't penalize WAKE/FOCUS reputation")
    print("5. Fair comparison across agents accounting for metabolic state")
    print("\nState-dependent reputation enables context-aware trust in Web4,")
    print("integrating SAGE's metabolic framework with decentralized coordination.")
    print("=" * 80)
