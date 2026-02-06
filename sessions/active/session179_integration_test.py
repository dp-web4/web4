"""
Session #179: Integration Test

Comprehensive test of the integrated ATP/ADP economics + coherence network
+ phase transition detection framework.

This simulates a complete market cycle:
1. Healthy stable market
2. Crisis emerges (herding starts)
3. Crash (coordinated panic, ATP crisis)
4. Recovery (diversification, ATP restored)
5. Stability restored

Author: Web4 Research Session 16
Date: January 2026
"""

import sys
sys.path.append('.')

from session179_atp_economics_coherence import (
    AgentEconomicState,
    GammaMarketAnalyzer,
    EconomicCoherenceCalculator
)
from session179_coherence_network import (
    CoherenceNetworkBuilder
)
from session179_phase_transition_detector import (
    PhaseTransitionDetector
)

import random


def create_agent(agent_id: str, initial_atp: float = 100.0) -> AgentEconomicState:
    """Create an agent with random initial spending pattern"""
    return AgentEconomicState(
        agent_id=agent_id,
        atp=initial_atp,
        adp=initial_atp * 0.5,
        atp_velocity=0.0,
        spending_pattern=[random.uniform(10, 20) for _ in range(5)],
        earning_pattern=[random.uniform(12, 18) for _ in range(5)],
        economic_coherence=0.7
    )


def simulate_healthy_market(agents: list) -> None:
    """Simulate healthy market with independent agents"""
    for i, agent in enumerate(agents):
        # Each agent has unique pattern
        agent.spending_pattern = [10.0 + i*2 + random.uniform(-1, 1) for _ in range(5)]
        agent.atp = 100.0
        agent.atp_velocity = random.uniform(-1, 1)
        agent.economic_coherence = 0.7


def simulate_herding_starts(agents: list) -> None:
    """Simulate start of herding - some agents coordinate"""
    herd_pattern = [15.0, 17.0, 16.0, 18.0, 16.5]

    # Half the agents start herding
    for i in range(len(agents) // 2):
        agents[i].spending_pattern = [p + random.uniform(-0.5, 0.5) for p in herd_pattern]
        agents[i].atp_velocity = -2.0  # Starting to deplete


def simulate_crash(agents: list) -> None:
    """Simulate full market crash - coordinated panic"""
    panic_pattern = [50.0, 52.0, 51.0, 53.0, 51.5]

    # All agents panic
    for agent in agents:
        agent.spending_pattern = panic_pattern.copy()
        agent.atp = random.uniform(10, 20)  # ATP crisis
        agent.atp_velocity = -5.0
        agent.economic_coherence = 0.3


def simulate_recovery_start(agents: list) -> None:
    """Simulate start of recovery - diversification begins"""
    # Create diverse patterns again
    for i, agent in enumerate(agents):
        if i % 2 == 0:
            agent.spending_pattern = [10.0 + i, 12.0 + i, 11.0 + i, 13.0 + i, 12.0 + i]
        else:
            agent.spending_pattern = [20.0 - i, 18.0 - i, 19.0 - i, 17.0 - i, 18.5 - i]

        agent.atp = 50.0  # Partially recovered
        agent.atp_velocity = 2.0  # Starting to grow
        agent.economic_coherence = 0.5


def simulate_stability(agents: list) -> None:
    """Simulate return to stability - fully diversified"""
    patterns = [
        [10.0, 12.0, 11.0, 13.0, 12.0],
        [25.0, 15.0, 20.0, 10.0, 18.0],
        [5.0, 30.0, 8.0, 35.0, 10.0],
        [40.0, 35.0, 42.0, 30.0, 45.0],
        [15.0, 15.0, 15.0, 15.0, 15.0],
        [8.0, 18.0, 13.0, 22.0, 16.0],
        [30.0, 25.0, 28.0, 23.0, 27.0],
        [12.0, 14.0, 13.0, 15.0, 13.5],
        [45.0, 38.0, 42.0, 35.0, 40.0],
        [20.0, 22.0, 21.0, 23.0, 21.5]
    ]

    for i, agent in enumerate(agents):
        agent.spending_pattern = patterns[i % len(patterns)]
        agent.atp = 100.0  # Fully recovered
        agent.atp_velocity = 1.0  # Stable growth
        agent.economic_coherence = 0.7


def run_full_cycle_simulation():
    """Run complete market cycle simulation"""
    print("=" * 80)
    print("SESSION #179: Full Market Cycle Simulation")
    print("=" * 80)
    print()

    # Create detector
    detector = PhaseTransitionDetector()

    # Create 10 agents
    agents = [create_agent(f"agent_{i}") for i in range(10)]

    # Phase 1: Healthy Market
    print("PHASE 1: Healthy Stable Market")
    print("-" * 80)
    simulate_healthy_market(agents)
    state1 = detector.analyze_state(agents, timestamp=0)
    print(f"  γ: {state1.market_state.gamma:.3f}")
    print(f"  Market phase: {state1.market_state.phase.value}")
    print(f"  Efficiency: {state1.market_state.efficiency:.3f}")
    print(f"  Crisis risk: {state1.market_state.crisis_risk:.3f}")
    print(f"  Network coherence: {state1.network_metrics.network_coherence:.3f}")
    print(f"  Avg ATP: {sum(a.atp for a in agents) / len(agents):.1f}")
    print()

    # Phase 2: Herding Starts
    print("PHASE 2: Herding Behavior Emerges")
    print("-" * 80)
    simulate_herding_starts(agents)
    state2 = detector.analyze_state(agents, timestamp=1)
    print(f"  γ: {state2.market_state.gamma:.3f} (Δ: {state2.market_state.gamma - state1.market_state.gamma:.3f})")
    print(f"  Market phase: {state2.market_state.phase.value}")
    print(f"  Efficiency: {state2.market_state.efficiency:.3f}")
    print(f"  Crisis risk: {state2.market_state.crisis_risk:.3f}")
    print(f"  Network coherence: {state2.network_metrics.network_coherence:.3f}")
    print(f"  Avg ATP: {sum(a.atp for a in agents) / len(agents):.1f}")
    print()

    # Phase 3: Market Crash
    print("PHASE 3: Market Crash (Coordinated Panic)")
    print("-" * 80)
    simulate_crash(agents)
    state3 = detector.analyze_state(agents, timestamp=2)
    print(f"  γ: {state3.market_state.gamma:.3f} (Δ: {state3.market_state.gamma - state2.market_state.gamma:.3f})")
    print(f"  Market phase: {state3.market_state.phase.value}")
    print(f"  Efficiency: {state3.market_state.efficiency:.3f}")
    print(f"  Crisis risk: {state3.market_state.crisis_risk:.3f}")
    print(f"  Network coherence: {state3.network_metrics.network_coherence:.3f}")
    print(f"  Avg ATP: {sum(a.atp for a in agents) / len(agents):.1f}")
    print()

    # Phase 4: Recovery Starts
    print("PHASE 4: Recovery Begins (Diversification)")
    print("-" * 80)
    simulate_recovery_start(agents)
    state4 = detector.analyze_state(agents, timestamp=3)
    print(f"  γ: {state4.market_state.gamma:.3f} (Δ: {state4.market_state.gamma - state3.market_state.gamma:.3f})")
    print(f"  Market phase: {state4.market_state.phase.value}")
    print(f"  Efficiency: {state4.market_state.efficiency:.3f}")
    print(f"  Crisis risk: {state4.market_state.crisis_risk:.3f}")
    print(f"  Network coherence: {state4.network_metrics.network_coherence:.3f}")
    print(f"  Avg ATP: {sum(a.atp for a in agents) / len(agents):.1f}")
    print()

    # Phase 5: Stability Restored
    print("PHASE 5: Stability Restored")
    print("-" * 80)
    simulate_stability(agents)
    state5 = detector.analyze_state(agents, timestamp=4)
    print(f"  γ: {state5.market_state.gamma:.3f} (Δ: {state5.market_state.gamma - state4.market_state.gamma:.3f})")
    print(f"  Market phase: {state5.market_state.phase.value}")
    print(f"  Efficiency: {state5.market_state.efficiency:.3f}")
    print(f"  Crisis risk: {state5.market_state.crisis_risk:.3f}")
    print(f"  Network coherence: {state5.network_metrics.network_coherence:.3f}")
    print(f"  Avg ATP: {sum(a.atp for a in agents) / len(agents):.1f}")
    print()

    # Transition Summary
    print("=" * 80)
    print("DETECTED TRANSITIONS")
    print("=" * 80)
    summary = detector.get_transition_summary()

    print(f"Total transitions detected: {summary['total_transitions']}")
    print()

    print("By type:")
    for ttype, count in summary['by_type'].items():
        print(f"  {ttype}: {count}")
    print()

    print("By severity:")
    for severity, count in summary['by_severity'].items():
        print(f"  {severity}: {count}")
    print()

    print("Timeline:")
    for transition in summary['transitions']:
        print(f"  t={transition['timestamp']}: {transition['type']} ({transition['severity']})")
        print(f"    {transition['description']}")
        print(f"    γ change: {transition['gamma_change']:.3f}")
        print(f"    Affected agents: {transition['affected_agents']}")
        print()

    print("=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80)
    print()
    print("Key Observations:")
    print("  1. γ drops during herding and crashes (coordination increases)")
    print("  2. Network coherence reflects overall system health")
    print("  3. Phase transitions detected automatically")
    print("  4. Crisis risk tracks ATP levels and coordination")
    print("  5. Recovery involves both ATP restoration AND diversification")
    print()


if __name__ == "__main__":
    run_full_cycle_simulation()
