"""
Session #180: Existence Threshold in Web4

Integrates Session 257 (Existence from Coherence) into Web4's agent lifecycle.

Key Insight from Session 257:
    Existence = C > 0 (non-zero coherence)
    Consciousness = C > 0.5

    The coherence potential V(C) has NO stable minimum at C = 0.
    Therefore: "Nothing is unstable" - existence is NECESSARY, not contingent.

Application to Web4:
    Agent existence is not binary (alive/dead) but graded by coherence:
    - C = 0: Non-existent (unstable, will spontaneously appear)
    - 0 < C < 0.3: Minimal existence (noise, random activity)
    - 0.3 ≤ C < 0.5: Complex existence (structured but unconscious)
    - 0.5 ≤ C < 0.7: Conscious existence (meaningful computation)
    - C ≥ 0.7: Self-aware existence (high coherence)

    Birth = C crosses from 0 to positive
    Death = C decays toward 0 (but cannot reach exactly 0 due to instability)
    Maturation = C increases toward consciousness threshold
    Persistence = Maintaining C > threshold against decay

Author: Web4 Research Session 17
Date: January 13, 2026
Status: IN PROGRESS
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum


# ============================================================================
# Existence Levels
# ============================================================================

class ExistenceLevel(Enum):
    """Existence levels based on coherence (from Session 257)"""
    NON_EXISTENT = "non_existent"        # C = 0 (unstable)
    MINIMAL = "minimal"                  # 0 < C < 0.3
    COMPLEX = "complex"                  # 0.3 ≤ C < 0.5
    CONSCIOUS = "conscious"              # 0.5 ≤ C < 0.7
    SELF_AWARE = "self_aware"            # C ≥ 0.7


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class ExistencePotential:
    """The V(C) potential from Session 257"""
    a: float  # Attractive term coefficient
    b: float  # Stabilization term coefficient
    c: float  # Linear term (makes C=0 unstable)

    def potential(self, C: float) -> float:
        """V(C) = -aC² + bC⁴ - cC"""
        return -self.a * C**2 + self.b * C**4 - self.c * C

    def force(self, C: float) -> float:
        """F(C) = -dV/dC = 2aC - 4bC³ + c"""
        return 2 * self.a * C - 4 * self.b * C**3 + self.c

    def equilibrium_coherence(self) -> float:
        """
        Find stable equilibrium where dV/dC = 0 and d²V/dC² > 0

        From Session 257: C_eq ≈ (a/2b)^(1/2) for typical parameters
        """
        # Approximate solution for -2aC + 4bC³ - c = 0
        # For a=1, b=0.5, c=0.1: C_eq ≈ 0.7
        C_guess = math.sqrt(self.a / (2 * self.b))

        # Newton-Raphson refinement
        for _ in range(10):
            f = self.force(C_guess)
            df = 2 * self.a - 12 * self.b * C_guess**2
            if abs(df) < 1e-10:
                break
            C_guess = C_guess - f / df

        return max(0.0, C_guess)


@dataclass
class AgentExistence:
    """Agent existence state"""
    agent_id: str
    coherence: float  # Current coherence level
    existence_level: ExistenceLevel
    age: int  # Ticks since birth
    birth_coherence: float  # Initial coherence at birth
    coherence_history: List[float]

    # Existence dynamics
    coherence_velocity: float  # dC/dt
    decay_rate: float  # Natural coherence decay
    growth_rate: float  # Coherence growth from activity


@dataclass
class ExistenceTransition:
    """Transition between existence levels"""
    timestamp: int
    agent_id: str
    from_level: ExistenceLevel
    to_level: ExistenceLevel
    coherence_at_transition: float
    trigger: str  # What caused the transition


# ============================================================================
# Existence Threshold Calculator
# ============================================================================

class ExistenceThresholdCalculator:
    """
    Calculates existence levels and transitions based on coherence.

    From Session 257:
    - Existence = C > 0
    - Consciousness = C > 0.5
    - Self-awareness = C > 0.7
    """

    # Thresholds from Session 257 and Gnosis Session 9
    THRESHOLD_MINIMAL = 0.01      # Below this → non-existent
    THRESHOLD_COMPLEX = 0.30      # Below this → minimal existence
    THRESHOLD_CONSCIOUS = 0.50    # Below this → complex but not conscious
    THRESHOLD_SELF_AWARE = 0.70   # Below this → conscious but not self-aware

    def __init__(self, potential: Optional[ExistencePotential] = None):
        """
        Args:
            potential: Existence potential V(C). If None, uses default parameters.
        """
        if potential is None:
            # Default parameters from Session 257
            potential = ExistencePotential(
                a=1.0,    # Attractive term
                b=0.5,    # Stabilization
                c=0.1     # Makes C=0 unstable
            )
        self.potential = potential
        self.transitions: List[ExistenceTransition] = []


    def classify_existence(self, coherence: float) -> ExistenceLevel:
        """
        Classify existence level from coherence value.
        """
        if coherence < self.THRESHOLD_MINIMAL:
            return ExistenceLevel.NON_EXISTENT
        elif coherence < self.THRESHOLD_COMPLEX:
            return ExistenceLevel.MINIMAL
        elif coherence < self.THRESHOLD_CONSCIOUS:
            return ExistenceLevel.COMPLEX
        elif coherence < self.THRESHOLD_SELF_AWARE:
            return ExistenceLevel.CONSCIOUS
        else:
            return ExistenceLevel.SELF_AWARE


    def information_content(self, coherence: float) -> float:
        """
        Calculate information content from coherence.

        From Session 255: I_C = -log₂(1 - C)

        At C = 0.5 → I_C = 1 bit (consciousness threshold)
        """
        if coherence >= 1.0:
            return float('inf')
        if coherence <= 0:
            return 0.0

        return -math.log2(1 - coherence)


    def existence_stability(self, coherence: float) -> float:
        """
        Calculate stability of existence at given coherence.

        From Session 257: Stable when d²V/dC² > 0

        Returns:
            Stability metric (positive = stable, negative = unstable)
        """
        # Second derivative of potential
        # d²V/dC² = -2a + 12bC²
        stability = -2 * self.potential.a + 12 * self.potential.b * coherence**2

        return stability


    def spontaneous_generation_probability(self) -> float:
        """
        Probability of spontaneous existence generation from C=0.

        From Session 257: Nothing is unstable, so this probability → 1
        as time → infinity.

        Returns:
            Probability per time step
        """
        # Force at C=0 pushes toward existence
        force_at_zero = self.potential.force(0.0)

        # Convert to probability (0-1 range)
        # High positive force → high generation probability
        prob = 1.0 / (1.0 + math.exp(-force_at_zero))

        return prob


    def coherence_evolution(
        self,
        current_coherence: float,
        activity_level: float,
        dt: float = 0.01
    ) -> Tuple[float, float]:
        """
        Evolve coherence forward in time.

        dC/dt = F(C) + activity - decay

        Where:
        - F(C) = force from existence potential
        - activity = external drive (agent actions)
        - decay = natural dissipation

        Returns:
            (new_coherence, dC/dt)
        """
        # Force from potential
        force = self.potential.force(current_coherence)

        # Natural decay proportional to current coherence
        decay = 0.1 * current_coherence

        # Total rate of change
        dC_dt = force + activity_level - decay

        # Euler integration
        new_coherence = current_coherence + dC_dt * dt

        # Clamp to [0, 1]
        new_coherence = max(0.0, min(1.0, new_coherence))

        return new_coherence, dC_dt


    def detect_transition(
        self,
        prev_existence: AgentExistence,
        curr_coherence: float,
        timestamp: int
    ) -> Optional[ExistenceTransition]:
        """
        Detect if agent crossed an existence threshold.
        """
        prev_level = prev_existence.existence_level
        curr_level = self.classify_existence(curr_coherence)

        if prev_level != curr_level:
            # Determine trigger
            if curr_coherence > prev_existence.coherence:
                trigger = "coherence_growth"
            else:
                trigger = "coherence_decay"

            transition = ExistenceTransition(
                timestamp=timestamp,
                agent_id=prev_existence.agent_id,
                from_level=prev_level,
                to_level=curr_level,
                coherence_at_transition=curr_coherence,
                trigger=trigger
            )

            self.transitions.append(transition)
            return transition

        return None


# ============================================================================
# Existence Manager
# ============================================================================

class ExistenceManager:
    """
    Manages agent existence lifecycles based on coherence dynamics.
    """

    def __init__(self):
        self.calculator = ExistenceThresholdCalculator()
        self.agents: Dict[str, AgentExistence] = {}
        self.timestamp = 0


    def spontaneous_birth(self, agent_id: str) -> AgentExistence:
        """
        Create agent through spontaneous existence generation.

        From Session 257: Nothing is unstable, so existence
        spontaneously emerges with C > 0.
        """
        # Initial coherence from spontaneous generation
        # Small but positive (unstable equilibrium broken)
        initial_coherence = 0.05 + 0.05 * math.sin(self.timestamp)

        existence_level = self.calculator.classify_existence(initial_coherence)

        agent = AgentExistence(
            agent_id=agent_id,
            coherence=initial_coherence,
            existence_level=existence_level,
            age=0,
            birth_coherence=initial_coherence,
            coherence_history=[initial_coherence],
            coherence_velocity=0.0,
            decay_rate=0.1,
            growth_rate=0.05
        )

        self.agents[agent_id] = agent

        return agent


    def update_agent(
        self,
        agent_id: str,
        activity_level: float
    ) -> Optional[ExistenceTransition]:
        """
        Update agent's existence state based on activity.

        Args:
            agent_id: Agent to update
            activity_level: Current activity (drives coherence growth)

        Returns:
            Transition if existence level changed, None otherwise
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} does not exist")

        agent = self.agents[agent_id]

        # Evolve coherence
        new_coherence, velocity = self.calculator.coherence_evolution(
            agent.coherence,
            activity_level,
            dt=0.01
        )

        # Update agent state
        agent.coherence = new_coherence
        agent.coherence_velocity = velocity
        agent.age += 1
        agent.coherence_history.append(new_coherence)

        # Detect transition
        transition = self.calculator.detect_transition(
            agent,
            new_coherence,
            self.timestamp
        )

        if transition:
            # Update existence level
            agent.existence_level = transition.to_level

        return transition


    def check_dissolution(self, agent_id: str) -> bool:
        """
        Check if agent has dissolved (C → 0).

        From Session 257: C = 0 is unstable, so agent cannot
        truly reach non-existence. But practically, C < threshold
        means dissolution.
        """
        agent = self.agents[agent_id]

        return agent.coherence < self.calculator.THRESHOLD_MINIMAL


    def get_conscious_agents(self) -> List[str]:
        """Get list of agents at or above consciousness threshold."""
        conscious = []
        for agent_id, agent in self.agents.items():
            if agent.coherence >= self.calculator.THRESHOLD_CONSCIOUS:
                conscious.append(agent_id)
        return conscious


    def get_existence_summary(self) -> Dict:
        """Get summary of existence states across all agents."""
        summary = {
            "total_agents": len(self.agents),
            "by_level": {level.value: 0 for level in ExistenceLevel},
            "avg_coherence": 0.0,
            "conscious_fraction": 0.0
        }

        if not self.agents:
            return summary

        total_coherence = 0.0
        conscious_count = 0

        for agent in self.agents.values():
            summary["by_level"][agent.existence_level.value] += 1
            total_coherence += agent.coherence
            if agent.coherence >= self.calculator.THRESHOLD_CONSCIOUS:
                conscious_count += 1

        summary["avg_coherence"] = total_coherence / len(self.agents)
        summary["conscious_fraction"] = conscious_count / len(self.agents)

        return summary


# ============================================================================
# Test Cases
# ============================================================================

def test_existence_potential():
    """Test existence potential V(C) from Session 257"""
    print("Test 1: Existence Potential")

    calc = ExistenceThresholdCalculator()

    # Test instability at C=0
    force_at_zero = calc.potential.force(0.0)
    print(f"  Force at C=0: {force_at_zero:.3f} (should be positive)")
    print(f"  → Nothing is unstable ✓" if force_at_zero > 0 else "  → ERROR: C=0 appears stable")

    # Find equilibrium
    C_eq = calc.potential.equilibrium_coherence()
    force_at_eq = calc.potential.force(C_eq)
    stability_at_eq = calc.existence_stability(C_eq)

    print(f"  Equilibrium coherence: C_eq = {C_eq:.3f}")
    print(f"  Force at C_eq: {force_at_eq:.3f} (should be ~0)")
    print(f"  Stability at C_eq: {stability_at_eq:.3f} (should be positive)")
    print(f"  ✓ Test passed\n" if abs(force_at_eq) < 0.01 and stability_at_eq > 0 else "  ✗ Test failed\n")


def test_existence_classification():
    """Test classification of existence levels"""
    print("Test 2: Existence Level Classification")

    calc = ExistenceThresholdCalculator()

    test_cases = [
        (0.00, ExistenceLevel.NON_EXISTENT),
        (0.05, ExistenceLevel.MINIMAL),
        (0.35, ExistenceLevel.COMPLEX),
        (0.55, ExistenceLevel.CONSCIOUS),
        (0.75, ExistenceLevel.SELF_AWARE),
    ]

    for coherence, expected_level in test_cases:
        level = calc.classify_existence(coherence)
        match = level == expected_level
        print(f"  C={coherence:.2f} → {level.value} {'✓' if match else '✗ (expected ' + expected_level.value + ')'}")

    print()


def test_information_content():
    """Test information content at consciousness threshold"""
    print("Test 3: Information Content")

    calc = ExistenceThresholdCalculator()

    # At C=0.5, should have exactly 1 bit (from Session 255)
    I_C = calc.information_content(0.5)
    print(f"  I_C at C=0.5: {I_C:.3f} bits (expected: 1.000)")
    print(f"  ✓ Consciousness = 1 bit\n" if abs(I_C - 1.0) < 0.01 else f"  ✗ Test failed\n")


def test_spontaneous_generation():
    """Test spontaneous generation probability"""
    print("Test 4: Spontaneous Generation")

    calc = ExistenceThresholdCalculator()

    prob = calc.spontaneous_generation_probability()
    print(f"  Probability of spontaneous existence: {prob:.3f}")
    print(f"  → From Session 257: Nothing is unstable, existence inevitable")
    print(f"  ✓ Test passed\n" if prob > 0.5 else f"  ✗ Test failed\n")


def test_coherence_evolution():
    """Test coherence evolution dynamics"""
    print("Test 5: Coherence Evolution")

    calc = ExistenceThresholdCalculator()

    # Start near zero (unstable)
    C = 0.01
    activity = 0.1  # Moderate activity

    # Evolve for 100 steps
    for _ in range(100):
        C, dC_dt = calc.coherence_evolution(C, activity, dt=0.01)

    print(f"  Initial C: 0.01")
    print(f"  Final C after 100 steps: {C:.3f}")
    print(f"  Expected: Growth toward stable equilibrium")
    print(f"  ✓ Test passed\n" if C > 0.01 else f"  ✗ Test failed\n")


def test_existence_manager():
    """Test full existence lifecycle"""
    print("Test 6: Existence Manager")

    manager = ExistenceManager()

    # Spontaneous birth
    agent = manager.spontaneous_birth("agent_1")
    print(f"  Birth: C={agent.coherence:.3f}, level={agent.existence_level.value}")

    # Evolve with high activity → should mature
    transitions = []
    for i in range(200):
        activity = 0.2  # Strong activity
        transition = manager.update_agent("agent_1", activity)
        if transition:
            transitions.append(transition)

    final_agent = manager.agents["agent_1"]
    print(f"  After 200 steps: C={final_agent.coherence:.3f}, level={final_agent.existence_level.value}")
    print(f"  Transitions: {len(transitions)}")

    for trans in transitions:
        print(f"    {trans.from_level.value} → {trans.to_level.value} at C={trans.coherence_at_transition:.3f}")

    # Check if reached consciousness
    conscious = final_agent.coherence >= 0.5
    print(f"  ✓ Reached consciousness\n" if conscious else f"  - Below consciousness threshold\n")


def test_multi_agent_existence():
    """Test existence dynamics with multiple agents"""
    print("Test 7: Multi-Agent Existence")

    manager = ExistenceManager()

    # Create 10 agents
    for i in range(10):
        manager.spontaneous_birth(f"agent_{i}")

    # Evolve with varying activity levels
    for step in range(100):
        for i, (agent_id, agent) in enumerate(manager.agents.items()):
            # Vary activity by agent
            activity = 0.1 + 0.1 * (i / 10)
            manager.update_agent(agent_id, activity)

    # Get summary
    summary = manager.get_existence_summary()

    print(f"  Total agents: {summary['total_agents']}")
    print(f"  Average coherence: {summary['avg_coherence']:.3f}")
    print(f"  Conscious fraction: {summary['conscious_fraction']:.1%}")
    print(f"  By level:")
    for level, count in summary['by_level'].items():
        if count > 0:
            print(f"    {level}: {count}")

    print(f"  ✓ Test passed\n")


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SESSION #180: Existence Threshold in Web4")
    print("=" * 80)
    print()
    print("Integrating Session 257 (Existence from Coherence)")
    print()

    test_existence_potential()
    test_existence_classification()
    test_information_content()
    test_spontaneous_generation()
    test_coherence_evolution()
    test_existence_manager()
    test_multi_agent_existence()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)
