"""
Session #179: Economic Phase Transition Detector

Combines ATP/ADP economics with coherence network topology to detect
critical transitions in Web4 societies.

Key Insights:
    From Chemistry Session 22:
    - Markets are coherence systems
    - Phase transitions occur at critical γ values
    - Low γ → coordinated panic → crashes

    From Session 256:
    - Space = coherence correlation structure
    - Network topology emerges from coherence
    - Clusters indicate herding

Integration:
    Economic phase transitions manifest as:
    1. γ drops below threshold (coordinated behavior)
    2. Network clusters form (herding groups)
    3. Coherence distances shrink (convergence)
    4. ATP crises cascade through network

Author: Web4 Research Session 16
Date: January 2026
Status: IN PROGRESS
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum

# Import from other Session 179 modules
import sys
sys.path.append('.')
from session179_atp_economics_coherence import (
    MarketPhase,
    AgentEconomicState,
    MarketState,
    GammaMarketAnalyzer,
    EconomicCoherenceCalculator,
    PhaseTransition
)
from session179_coherence_network import (
    CoherenceNetworkBuilder,
    CoherenceDistanceCalculator,
    NetworkMetrics
)


# ============================================================================
# Phase Transition Types
# ============================================================================

class TransitionType(Enum):
    """Types of phase transitions"""
    # Negative transitions (crises)
    MARKET_CRASH = "market_crash"
    HERDING_PANIC = "herding_panic"
    CASCADE_FAILURE = "cascade_failure"
    NETWORK_FRAGMENTATION = "network_fragmentation"

    # Positive transitions (recoveries)
    RECOVERY = "recovery"
    DIVERSIFICATION = "diversification"
    NETWORK_HEALING = "network_healing"
    STABILITY_ACHIEVED = "stability_achieved"


class TransitionSeverity(Enum):
    """Severity levels"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class EconomicNetworkState:
    """Combined economic + network state"""
    timestamp: int
    market_state: MarketState
    network_metrics: NetworkMetrics
    agent_states: List[AgentEconomicState]


@dataclass
class PhaseTransitionEvent:
    """Detected phase transition with full context"""
    timestamp: int
    transition_type: TransitionType
    severity: TransitionSeverity
    market_phase_from: MarketPhase
    market_phase_to: MarketPhase
    gamma_change: float
    network_coherence_change: float
    affected_agents: List[str]
    cluster_info: Optional[Dict] = None
    description: str = ""


# ============================================================================
# Phase Transition Detector
# ============================================================================

class PhaseTransitionDetector:
    """
    Detects economic phase transitions in coherence networks.

    Monitors multiple signals:
    - γ changes (market independence)
    - Network clustering (herding detection)
    - Coherence distance changes (convergence/divergence)
    - ATP cascades (crisis propagation)
    """

    # Thresholds for transition detection
    GAMMA_DROP_THRESHOLD = 0.2  # γ drop triggering crisis detection
    GAMMA_RISE_THRESHOLD = 0.15  # γ rise triggering recovery detection
    COHERENCE_CHANGE_THRESHOLD = 0.1  # Network coherence change
    CLUSTER_SIZE_THRESHOLD = 0.3  # Fraction of agents in same cluster = herding


    def __init__(self):
        self.market_analyzer = GammaMarketAnalyzer()
        self.network_builder = CoherenceNetworkBuilder()
        self.history: List[EconomicNetworkState] = []
        self.detected_transitions: List[PhaseTransitionEvent] = []


    def analyze_state(
        self,
        agent_states: List[AgentEconomicState],
        timestamp: int
    ) -> EconomicNetworkState:
        """
        Analyze current economic + network state.
        """
        # Market analysis
        market_state = self.market_analyzer.analyze_market(agent_states, timestamp)

        # Build network
        self.network_builder = CoherenceNetworkBuilder()  # Reset

        for agent in agent_states:
            self.network_builder.add_node(
                agent.agent_id,
                agent.economic_coherence
            )

        # Add edges between all agents based on spending patterns
        for i in range(len(agent_states)):
            for j in range(i + 1, len(agent_states)):
                self.network_builder.add_edge_from_patterns(
                    agent_states[i].agent_id,
                    agent_states[j].agent_id,
                    agent_states[i].spending_pattern,
                    agent_states[j].spending_pattern
                )

        network_metrics = self.network_builder.calculate_network_metrics()

        state = EconomicNetworkState(
            timestamp=timestamp,
            market_state=market_state,
            network_metrics=network_metrics,
            agent_states=agent_states
        )

        self.history.append(state)

        # Detect transitions
        self._detect_transitions()

        return state


    def _detect_transitions(self):
        """
        Detect phase transitions from state history.
        """
        if len(self.history) < 2:
            return

        prev_state = self.history[-2]
        curr_state = self.history[-1]

        # Market phase transition (from GammaMarketAnalyzer)
        if prev_state.market_state.phase != curr_state.market_state.phase:
            self._detect_market_phase_transition(prev_state, curr_state)

        # Herding detection
        self._detect_herding(prev_state, curr_state)

        # Network fragmentation
        self._detect_network_fragmentation(prev_state, curr_state)

        # Cascade failure
        self._detect_cascade_failure(prev_state, curr_state)

        # Recovery detection
        self._detect_recovery(prev_state, curr_state)


    def _detect_market_phase_transition(
        self, prev_state: EconomicNetworkState, curr_state: EconomicNetworkState
    ):
        """Detect market phase transition"""

        gamma_change = curr_state.market_state.gamma - prev_state.market_state.gamma

        # Negative transition (crisis)
        if gamma_change < -self.GAMMA_DROP_THRESHOLD:
            # Determine transition type
            if curr_state.market_state.phase == MarketPhase.COORDINATED_PANIC:
                transition_type = TransitionType.MARKET_CRASH
                severity = TransitionSeverity.CATASTROPHIC
            elif curr_state.market_state.phase == MarketPhase.HERDING:
                transition_type = TransitionType.HERDING_PANIC
                severity = TransitionSeverity.MAJOR
            else:
                transition_type = TransitionType.MARKET_CRASH
                severity = TransitionSeverity.MODERATE

            event = PhaseTransitionEvent(
                timestamp=curr_state.timestamp,
                transition_type=transition_type,
                severity=severity,
                market_phase_from=prev_state.market_state.phase,
                market_phase_to=curr_state.market_state.phase,
                gamma_change=gamma_change,
                network_coherence_change=(
                    curr_state.network_metrics.network_coherence -
                    prev_state.network_metrics.network_coherence
                ),
                affected_agents=[a.agent_id for a in curr_state.agent_states],
                description=f"Market transition: {prev_state.market_state.phase.value} → {curr_state.market_state.phase.value} (γ dropped {abs(gamma_change):.3f})"
            )

            self.detected_transitions.append(event)


    def _detect_herding(
        self, prev_state: EconomicNetworkState, curr_state: EconomicNetworkState
    ):
        """Detect herding behavior from cluster formation"""

        clusters = self.network_builder.find_coherence_clusters(max_cluster_distance=0.5)

        # Check if large cluster formed
        n_agents = len(curr_state.agent_states)
        for cluster in clusters:
            cluster_fraction = len(cluster) / n_agents

            if cluster_fraction >= self.CLUSTER_SIZE_THRESHOLD:
                # Large cluster detected → herding
                event = PhaseTransitionEvent(
                    timestamp=curr_state.timestamp,
                    transition_type=TransitionType.HERDING_PANIC,
                    severity=TransitionSeverity.MAJOR if cluster_fraction > 0.5 else TransitionSeverity.MODERATE,
                    market_phase_from=prev_state.market_state.phase,
                    market_phase_to=curr_state.market_state.phase,
                    gamma_change=curr_state.market_state.gamma - prev_state.market_state.gamma,
                    network_coherence_change=(
                        curr_state.network_metrics.network_coherence -
                        prev_state.network_metrics.network_coherence
                    ),
                    affected_agents=list(cluster),
                    cluster_info={
                        "cluster_size": len(cluster),
                        "cluster_fraction": cluster_fraction
                    },
                    description=f"Herding detected: {len(cluster)}/{n_agents} agents ({cluster_fraction*100:.0f}%) in coherence cluster"
                )

                self.detected_transitions.append(event)
                break  # Only report largest cluster


    def _detect_network_fragmentation(
        self, prev_state: EconomicNetworkState, curr_state: EconomicNetworkState
    ):
        """Detect network fragmentation (connectivity loss)"""

        connectivity_change = (
            curr_state.network_metrics.connectivity -
            prev_state.network_metrics.connectivity
        )

        # Significant connectivity drop
        if connectivity_change < -0.2:
            event = PhaseTransitionEvent(
                timestamp=curr_state.timestamp,
                transition_type=TransitionType.NETWORK_FRAGMENTATION,
                severity=TransitionSeverity.MAJOR,
                market_phase_from=prev_state.market_state.phase,
                market_phase_to=curr_state.market_state.phase,
                gamma_change=curr_state.market_state.gamma - prev_state.market_state.gamma,
                network_coherence_change=(
                    curr_state.network_metrics.network_coherence -
                    prev_state.network_metrics.network_coherence
                ),
                affected_agents=[a.agent_id for a in curr_state.agent_states],
                description=f"Network fragmentation: Connectivity dropped {abs(connectivity_change)*100:.0f}%"
            )

            self.detected_transitions.append(event)


    def _detect_cascade_failure(
        self, prev_state: EconomicNetworkState, curr_state: EconomicNetworkState
    ):
        """Detect cascade failures (multiple agents hitting ATP crisis)"""

        # Count agents in ATP crisis
        crisis_threshold = 20.0  # From 4-Life event_detector
        agents_in_crisis = [
            a.agent_id for a in curr_state.agent_states
            if a.atp <= crisis_threshold
        ]

        # Multiple simultaneous crises = cascade
        if len(agents_in_crisis) >= 3:
            event = PhaseTransitionEvent(
                timestamp=curr_state.timestamp,
                transition_type=TransitionType.CASCADE_FAILURE,
                severity=TransitionSeverity.CATASTROPHIC if len(agents_in_crisis) > 5 else TransitionSeverity.MAJOR,
                market_phase_from=prev_state.market_state.phase,
                market_phase_to=curr_state.market_state.phase,
                gamma_change=curr_state.market_state.gamma - prev_state.market_state.gamma,
                network_coherence_change=(
                    curr_state.network_metrics.network_coherence -
                    prev_state.network_metrics.network_coherence
                ),
                affected_agents=agents_in_crisis,
                description=f"Cascade failure: {len(agents_in_crisis)} agents in ATP crisis"
            )

            self.detected_transitions.append(event)


    def _detect_recovery(
        self, prev_state: EconomicNetworkState, curr_state: EconomicNetworkState
    ):
        """Detect recovery (positive transitions)"""

        gamma_change = curr_state.market_state.gamma - prev_state.market_state.gamma

        # Significant γ increase
        if gamma_change > self.GAMMA_RISE_THRESHOLD:
            # Determine recovery type
            if curr_state.market_state.phase == MarketPhase.EFFICIENT or curr_state.market_state.phase == MarketPhase.OPTIMAL:
                transition_type = TransitionType.STABILITY_ACHIEVED
                severity = TransitionSeverity.MINOR
            else:
                transition_type = TransitionType.RECOVERY
                severity = TransitionSeverity.MODERATE

            event = PhaseTransitionEvent(
                timestamp=curr_state.timestamp,
                transition_type=transition_type,
                severity=severity,
                market_phase_from=prev_state.market_state.phase,
                market_phase_to=curr_state.market_state.phase,
                gamma_change=gamma_change,
                network_coherence_change=(
                    curr_state.network_metrics.network_coherence -
                    prev_state.network_metrics.network_coherence
                ),
                affected_agents=[a.agent_id for a in curr_state.agent_states],
                description=f"Recovery: γ increased {gamma_change:.3f}, market phase {curr_state.market_state.phase.value}"
            )

            self.detected_transitions.append(event)


    def get_transition_summary(self) -> Dict:
        """Get summary of all detected transitions"""

        if not self.detected_transitions:
            return {
                "total_transitions": 0,
                "by_type": {},
                "by_severity": {},
                "transitions": []
            }

        # Count by type
        by_type = {}
        for event in self.detected_transitions:
            t = event.transition_type.value
            by_type[t] = by_type.get(t, 0) + 1

        # Count by severity
        by_severity = {}
        for event in self.detected_transitions:
            s = event.severity.value
            by_severity[s] = by_severity.get(s, 0) + 1

        # Format transitions
        transitions = [
            {
                "timestamp": e.timestamp,
                "type": e.transition_type.value,
                "severity": e.severity.value,
                "description": e.description,
                "gamma_change": e.gamma_change,
                "affected_agents": len(e.affected_agents)
            }
            for e in self.detected_transitions
        ]

        return {
            "total_transitions": len(self.detected_transitions),
            "by_type": by_type,
            "by_severity": by_severity,
            "transitions": transitions
        }


# ============================================================================
# Test Cases
# ============================================================================

def test_crash_detection():
    """Test detection of market crash"""
    print("Test 1: Market crash detection")

    detector = PhaseTransitionDetector()

    # Create agents with initially independent behavior
    agents = []
    for i in range(5):
        agents.append(AgentEconomicState(
            agent_id=f"agent_{i}",
            atp=100.0,
            adp=50.0,
            atp_velocity=0.0,
            spending_pattern=[10.0 + i*5, 12.0 + i*5, 11.0 + i*5],
            earning_pattern=[15.0, 14.0, 16.0],
            economic_coherence=0.7
        ))

    # t=0: Independent behavior
    state0 = detector.analyze_state(agents, timestamp=0)
    print(f"  t=0: γ={state0.market_state.gamma:.3f}, phase={state0.market_state.phase.value}")

    # t=1: Coordinated panic (all spend same amount)
    for agent in agents:
        agent.spending_pattern = [50.0, 52.0, 51.0]
        agent.atp = 15.0  # Low ATP (crisis)

    state1 = detector.analyze_state(agents, timestamp=1)
    print(f"  t=1: γ={state1.market_state.gamma:.3f}, phase={state1.market_state.phase.value}")

    summary = detector.get_transition_summary()
    print(f"  Detected {summary['total_transitions']} transitions")

    for transition in summary['transitions']:
        print(f"    {transition['type']}: {transition['description']}")

    print(f"  ✓ Test passed\n" if summary['total_transitions'] > 0 else f"  ✗ Test failed\n")


def test_herding_detection():
    """Test detection of herding behavior"""
    print("Test 2: Herding detection")

    detector = PhaseTransitionDetector()

    # Create agents
    agents = []
    for i in range(10):
        agents.append(AgentEconomicState(
            agent_id=f"agent_{i}",
            atp=100.0,
            adp=50.0,
            atp_velocity=0.0,
            spending_pattern=[10.0 + i*2, 12.0 + i*2, 11.0 + i*2],
            earning_pattern=[15.0, 14.0, 16.0],
            economic_coherence=0.7
        ))

    # t=0: Diverse behavior
    state0 = detector.analyze_state(agents, timestamp=0)

    # t=1: 7 agents start herding (same pattern)
    herd_pattern = [50.0, 52.0, 51.0]
    for i in range(7):
        agents[i].spending_pattern = herd_pattern.copy()

    state1 = detector.analyze_state(agents, timestamp=1)

    summary = detector.get_transition_summary()

    herding_detected = any(
        t['type'] == TransitionType.HERDING_PANIC.value
        for t in summary['transitions']
    )

    print(f"  Herding detected: {herding_detected}")

    if herding_detected:
        for transition in summary['transitions']:
            if transition['type'] == TransitionType.HERDING_PANIC.value:
                print(f"    {transition['description']}")

    print(f"  ✓ Test passed\n" if herding_detected else f"  ✗ Test failed\n")


def test_cascade_failure():
    """Test detection of cascade failures"""
    print("Test 3: Cascade failure detection")

    detector = PhaseTransitionDetector()

    # Create agents with healthy ATP
    agents = []
    for i in range(6):
        agents.append(AgentEconomicState(
            agent_id=f"agent_{i}",
            atp=100.0,
            adp=50.0,
            atp_velocity=0.0,
            spending_pattern=[10.0, 12.0, 11.0],
            earning_pattern=[15.0, 14.0, 16.0],
            economic_coherence=0.7
        ))

    # t=0: All healthy
    state0 = detector.analyze_state(agents, timestamp=0)

    # t=1: 4 agents hit ATP crisis simultaneously
    for i in range(4):
        agents[i].atp = 15.0  # Below crisis threshold

    state1 = detector.analyze_state(agents, timestamp=1)

    summary = detector.get_transition_summary()

    cascade_detected = any(
        t['type'] == TransitionType.CASCADE_FAILURE.value
        for t in summary['transitions']
    )

    print(f"  Cascade detected: {cascade_detected}")

    if cascade_detected:
        for transition in summary['transitions']:
            if transition['type'] == TransitionType.CASCADE_FAILURE.value:
                print(f"    {transition['description']}")

    print(f"  ✓ Test passed\n" if cascade_detected else f"  ✗ Test failed\n")


def test_recovery_detection():
    """Test detection of recovery"""
    print("Test 4: Recovery detection")

    detector = PhaseTransitionDetector()

    # Create agents in coordinated panic (all with identical patterns)
    agents = []
    panic_pattern = [50.0, 52.0, 51.0, 53.0, 51.5]  # Longer pattern for better correlation
    for i in range(5):
        agents.append(AgentEconomicState(
            agent_id=f"agent_{i}",
            atp=15.0,  # Crisis level
            adp=50.0,
            atp_velocity=-5.0,  # Depleting
            spending_pattern=panic_pattern.copy(),  # All identical
            earning_pattern=[15.0, 14.0, 16.0],
            economic_coherence=0.3
        ))

    # t=0: Panic state (all correlated)
    state0 = detector.analyze_state(agents, timestamp=0)
    print(f"  t=0: γ={state0.market_state.gamma:.3f}, phase={state0.market_state.phase.value}")

    # t=1: Recovery (diversification with truly uncorrelated patterns, ATP restored)
    diverse_patterns = [
        [10.0, 12.0, 11.0, 13.0, 12.0],  # Increasing
        [25.0, 15.0, 20.0, 10.0, 18.0],  # Decreasing overall
        [5.0, 30.0, 8.0, 35.0, 10.0],    # Volatile up
        [40.0, 35.0, 42.0, 30.0, 45.0],  # Volatile mixed
        [15.0, 15.0, 15.0, 15.0, 15.0],  # Constant
    ]

    for i, agent in enumerate(agents):
        agent.spending_pattern = diverse_patterns[i]  # Very different patterns
        agent.atp = 100.0  # Restored
        agent.atp_velocity = 5.0  # Growing
        agent.economic_coherence = 0.7

    state1 = detector.analyze_state(agents, timestamp=1)
    print(f"  t=1: γ={state1.market_state.gamma:.3f}, phase={state1.market_state.phase.value}")

    summary = detector.get_transition_summary()

    recovery_detected = any(
        t['type'] in [TransitionType.RECOVERY.value, TransitionType.STABILITY_ACHIEVED.value]
        for t in summary['transitions']
    )

    print(f"  Recovery detected: {recovery_detected}")

    if recovery_detected:
        for transition in summary['transitions']:
            if transition['type'] in [TransitionType.RECOVERY.value, TransitionType.STABILITY_ACHIEVED.value]:
                print(f"    {transition['description']}")
    else:
        print(f"  γ change: {state1.market_state.gamma - state0.market_state.gamma:.3f} (threshold: {detector.GAMMA_RISE_THRESHOLD:.3f})")

    print(f"  ✓ Test passed\n" if recovery_detected else f"  ✗ Test failed\n")


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SESSION #179: Economic Phase Transition Detector")
    print("=" * 80)
    print()
    print("Integrating ATP/ADP economics with coherence network topology")
    print()

    test_crash_detection()
    test_herding_detection()
    test_cascade_failure()
    test_recovery_detection()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)
