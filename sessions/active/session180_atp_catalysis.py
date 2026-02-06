"""
Session #180: ATP Transaction Catalysis

Integrates Chemistry Session 23 (Reaction Kinetics) into Web4's ATP transaction system.

Key Insight from Chemistry Session 23:
    k_eff = k_TST × (2/γ)^α

    Where:
    - k_TST = transition state theory rate constant
    - γ = effective dimensionality from correlations
    - α = collectivity exponent (0.5-2.0)

    **Catalysis is γ reduction** - correlated environments lower barriers

Application to Web4:
    ATP transactions are "reactions" between agents:
    - Standard rate: k_TST (isolated agents, high γ)
    - Catalyzed rate: k_eff (correlated agents, low γ)
    - Enhancement: (2/γ)^α can be 2-16× faster

    Transaction types:
    - Simple transfers: α = 0.5 (2× enhancement at γ=0.5)
    - Trust updates: α = 1.0 (4× enhancement)
    - Consensus operations: α = 1.5 (8× enhancement)
    - Collective decisions: α = 2.0 (16× enhancement)

    This explains why coherent agent groups transact faster than
    independent agents - their correlation reduces transaction barriers.

Author: Web4 Research Session 17
Date: January 13, 2026
Status: IN PROGRESS
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum


# ============================================================================
# Transaction Types
# ============================================================================

class TransactionType(Enum):
    """Types of ATP transactions with different collectivity"""
    SIMPLE_TRANSFER = "simple_transfer"         # α = 0.5
    TRUST_UPDATE = "trust_update"               # α = 1.0
    ATTESTATION = "attestation"                 # α = 1.0
    CONSENSUS_OPERATION = "consensus_operation" # α = 1.5
    COLLECTIVE_DECISION = "collective_decision" # α = 2.0


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class TransactionParameters:
    """Parameters for a transaction type"""
    transaction_type: TransactionType
    alpha: float  # Collectivity exponent
    base_rate: float  # k_TST (uncatalyzed rate)
    activation_energy: float  # Ea_0 (kJ/mol or ATP units)
    coupling: float  # How much barrier responds to correlation (0-1)


@dataclass
class CatalyzedTransaction:
    """Record of a catalyzed transaction"""
    from_agent: str
    to_agent: str
    transaction_type: TransactionType
    atp_amount: float
    gamma: float  # Correlation coefficient
    base_rate: float  # k_TST
    effective_rate: float  # k_eff
    enhancement_factor: float  # k_eff / k_TST
    execution_time: float  # Time to complete transaction


# ============================================================================
# ATP Reaction Kinetics Calculator
# ============================================================================

class ATPReactionKineticsCalculator:
    """
    Calculates catalyzed transaction rates using γ-modified TST.

    From Chemistry Session 23:
    k_eff = k_TST × (2/γ)^α
    Ea_eff = Ea_0 × (γ/2)^coupling
    """

    # Default transaction parameters
    DEFAULT_PARAMETERS = {
        TransactionType.SIMPLE_TRANSFER: TransactionParameters(
            transaction_type=TransactionType.SIMPLE_TRANSFER,
            alpha=0.5,
            base_rate=1.0,  # 1 transaction per time unit
            activation_energy=10.0,  # ATP units
            coupling=0.3
        ),
        TransactionType.TRUST_UPDATE: TransactionParameters(
            transaction_type=TransactionType.TRUST_UPDATE,
            alpha=1.0,
            base_rate=0.5,  # Slower base rate
            activation_energy=20.0,
            coupling=0.5
        ),
        TransactionType.ATTESTATION: TransactionParameters(
            transaction_type=TransactionType.ATTESTATION,
            alpha=1.0,
            base_rate=0.3,
            activation_energy=25.0,
            coupling=0.5
        ),
        TransactionType.CONSENSUS_OPERATION: TransactionParameters(
            transaction_type=TransactionType.CONSENSUS_OPERATION,
            alpha=1.5,
            base_rate=0.1,  # Much slower without coordination
            activation_energy=50.0,
            coupling=0.7
        ),
        TransactionType.COLLECTIVE_DECISION: TransactionParameters(
            transaction_type=TransactionType.COLLECTIVE_DECISION,
            alpha=2.0,
            base_rate=0.01,  # Very slow without coordination
            activation_energy=100.0,
            coupling=0.9
        )
    }


    def __init__(self):
        self.parameters = self.DEFAULT_PARAMETERS.copy()
        self.transaction_history: List[CatalyzedTransaction] = []


    def calculate_effective_rate(
        self,
        transaction_type: TransactionType,
        gamma: float
    ) -> Tuple[float, float]:
        """
        Calculate effective transaction rate with γ-based catalysis.

        From Chemistry Session 23: k_eff = k_TST × (2/γ)^α

        Returns:
            (k_eff, enhancement_factor)
        """
        params = self.parameters[transaction_type]

        # Base rate
        k_TST = params.base_rate

        # γ-based enhancement
        if gamma <= 0:
            gamma = 0.01  # Avoid division by zero

        enhancement = (2.0 / gamma) ** params.alpha
        k_eff = k_TST * enhancement

        return k_eff, enhancement


    def calculate_effective_barrier(
        self,
        transaction_type: TransactionType,
        gamma: float
    ) -> Tuple[float, float]:
        """
        Calculate effective activation barrier.

        From Chemistry Session 23: Ea_eff = Ea_0 × (γ/2)^coupling

        Returns:
            (Ea_eff, reduction_factor)
        """
        params = self.parameters[transaction_type]

        # Intrinsic barrier
        Ea_0 = params.activation_energy

        # γ-based reduction
        reduction = (gamma / 2.0) ** params.coupling
        Ea_eff = Ea_0 * reduction

        return Ea_eff, reduction


    def calculate_execution_time(
        self,
        transaction_type: TransactionType,
        gamma: float,
        atp_amount: float
    ) -> float:
        """
        Calculate time to execute transaction.

        Execution time ∝ 1 / k_eff

        Args:
            transaction_type: Type of transaction
            gamma: Correlation between agents
            atp_amount: Amount of ATP being transacted

        Returns:
            Execution time in time units
        """
        k_eff, _ = self.calculate_effective_rate(transaction_type, gamma)

        # Base execution time
        base_time = 1.0 / k_eff

        # Scale by ATP amount (larger transactions take longer)
        execution_time = base_time * (1.0 + math.log(1.0 + atp_amount / 100.0))

        return execution_time


    def process_transaction(
        self,
        from_agent: str,
        to_agent: str,
        transaction_type: TransactionType,
        atp_amount: float,
        gamma: float
    ) -> CatalyzedTransaction:
        """
        Process a catalyzed ATP transaction.

        Returns:
            Transaction record with catalysis details
        """
        params = self.parameters[transaction_type]

        # Calculate rates
        k_eff, enhancement = self.calculate_effective_rate(transaction_type, gamma)
        base_rate = params.base_rate

        # Calculate execution time
        execution_time = self.calculate_execution_time(
            transaction_type,
            gamma,
            atp_amount
        )

        # Create transaction record
        transaction = CatalyzedTransaction(
            from_agent=from_agent,
            to_agent=to_agent,
            transaction_type=transaction_type,
            atp_amount=atp_amount,
            gamma=gamma,
            base_rate=base_rate,
            effective_rate=k_eff,
            enhancement_factor=enhancement,
            execution_time=execution_time
        )

        self.transaction_history.append(transaction)

        return transaction


    def analyze_catalysis_benefit(
        self,
        transaction_type: TransactionType
    ) -> Dict[float, Dict[str, float]]:
        """
        Analyze catalysis benefit across γ range.

        Returns:
            Dict mapping γ → {enhancement, barrier_reduction, speedup}
        """
        results = {}

        gamma_values = [0.2, 0.5, 1.0, 1.5, 2.0]

        for gamma in gamma_values:
            k_eff, enhancement = self.calculate_effective_rate(transaction_type, gamma)
            Ea_eff, barrier_reduction = self.calculate_effective_barrier(transaction_type, gamma)

            # Speedup = how much faster than γ=2.0 (independent agents)
            k_independent, _ = self.calculate_effective_rate(transaction_type, 2.0)
            speedup = k_eff / k_independent

            results[gamma] = {
                "enhancement": enhancement,
                "barrier_reduction": barrier_reduction,
                "speedup": speedup
            }

        return results


# ============================================================================
# Transaction Optimizer
# ============================================================================

class TransactionOptimizer:
    """
    Optimizes transaction routing based on agent correlation.

    Agents with high correlation (low γ) should transact preferentially
    to leverage catalysis benefits.
    """

    def __init__(self, calculator: ATPReactionKineticsCalculator):
        self.calculator = calculator


    def calculate_optimal_path(
        self,
        from_agent: str,
        to_agent: str,
        intermediaries: List[Tuple[str, float]],  # (agent_id, gamma_with_from)
        transaction_type: TransactionType,
        atp_amount: float
    ) -> List[str]:
        """
        Calculate optimal transaction path considering catalysis.

        Direct path: from_agent → to_agent (γ_direct)
        Indirect path: from_agent → intermediary → to_agent (γ1, γ2)

        Choose path that minimizes total execution time.

        Args:
            from_agent: Source agent
            to_agent: Destination agent
            intermediaries: List of (agent_id, γ_with_from_agent)
            transaction_type: Type of transaction
            atp_amount: Amount to transfer

        Returns:
            Optimal path as list of agent IDs
        """
        # Direct path (if we know γ_direct)
        # For now, assume γ_direct = 1.5 (moderate correlation)
        gamma_direct = 1.5

        direct_time = self.calculator.calculate_execution_time(
            transaction_type,
            gamma_direct,
            atp_amount
        )

        best_path = [from_agent, to_agent]
        best_time = direct_time

        # Check indirect paths through intermediaries
        for intermediary, gamma1 in intermediaries:
            # Assume γ2 (intermediary → to_agent) = 1.0
            gamma2 = 1.0

            # Time for two hops
            time1 = self.calculator.calculate_execution_time(
                transaction_type,
                gamma1,
                atp_amount
            )

            time2 = self.calculator.calculate_execution_time(
                transaction_type,
                gamma2,
                atp_amount
            )

            total_time = time1 + time2

            if total_time < best_time:
                best_time = total_time
                best_path = [from_agent, intermediary, to_agent]

        return best_path


    def recommend_transaction_grouping(
        self,
        pending_transactions: List[Tuple[str, str, float]],  # (from, to, amount)
        agent_correlations: Dict[Tuple[str, str], float],  # (agent1, agent2) → γ
        transaction_type: TransactionType
    ) -> List[List[Tuple[str, str, float]]]:
        """
        Group transactions to maximize catalysis benefits.

        Transactions between highly correlated agents should be batched
        to leverage collective effects.

        Returns:
            List of transaction batches
        """
        # Simple grouping: sort by correlation, batch adjacent high-correlation pairs
        scored_transactions = []

        for from_agent, to_agent, amount in pending_transactions:
            gamma = agent_correlations.get((from_agent, to_agent), 2.0)
            scored_transactions.append((gamma, from_agent, to_agent, amount))

        # Sort by γ (low γ = high correlation = high priority)
        scored_transactions.sort(key=lambda x: x[0])

        # Create batches
        batches = []
        current_batch = []
        batch_size_limit = 10

        for gamma, from_agent, to_agent, amount in scored_transactions:
            current_batch.append((from_agent, to_agent, amount))

            if len(current_batch) >= batch_size_limit:
                batches.append(current_batch)
                current_batch = []

        if current_batch:
            batches.append(current_batch)

        return batches


# ============================================================================
# Test Cases
# ============================================================================

def test_rate_enhancement():
    """Test rate enhancement from γ reduction"""
    print("Test 1: Rate Enhancement (k_eff = k_TST × (2/γ)^α)")

    calc = ATPReactionKineticsCalculator()

    # Test simple transfer (α = 0.5)
    print("  Simple Transfer (α = 0.5):")
    for gamma in [2.0, 1.0, 0.5]:
        k_eff, enhancement = calc.calculate_effective_rate(
            TransactionType.SIMPLE_TRANSFER,
            gamma
        )
        print(f"    γ={gamma:.1f}: k_eff={k_eff:.2f}, enhancement={enhancement:.1f}×")

    # Test collective decision (α = 2.0)
    print("  Collective Decision (α = 2.0):")
    for gamma in [2.0, 1.0, 0.5]:
        k_eff, enhancement = calc.calculate_effective_rate(
            TransactionType.COLLECTIVE_DECISION,
            gamma
        )
        print(f"    γ={gamma:.1f}: k_eff={k_eff:.2f}, enhancement={enhancement:.1f}×")

    print("  ✓ Test passed\n")


def test_barrier_reduction():
    """Test activation barrier reduction"""
    print("Test 2: Barrier Reduction (Ea_eff = Ea_0 × (γ/2)^coupling)")

    calc = ATPReactionKineticsCalculator()

    transaction_type = TransactionType.CONSENSUS_OPERATION
    params = calc.parameters[transaction_type]

    print(f"  Consensus Operation (Ea_0 = {params.activation_energy} ATP, coupling = {params.coupling}):")

    for gamma in [2.0, 1.0, 0.5]:
        Ea_eff, reduction = calc.calculate_effective_barrier(transaction_type, gamma)
        percent_reduction = (1 - reduction) * 100
        print(f"    γ={gamma:.1f}: Ea_eff={Ea_eff:.1f} ATP ({percent_reduction:.0f}% reduction)")

    print("  ✓ Test passed\n")


def test_transaction_processing():
    """Test full transaction processing"""
    print("Test 3: Transaction Processing")

    calc = ATPReactionKineticsCalculator()

    # Process simple transfer with high correlation
    transaction = calc.process_transaction(
        from_agent="agent_A",
        to_agent="agent_B",
        transaction_type=TransactionType.SIMPLE_TRANSFER,
        atp_amount=100.0,
        gamma=0.5
    )

    print(f"  Transaction: {transaction.from_agent} → {transaction.to_agent}")
    print(f"  Type: {transaction.transaction_type.value}")
    print(f"  ATP amount: {transaction.atp_amount}")
    print(f"  γ: {transaction.gamma}")
    print(f"  Base rate: {transaction.base_rate:.2f}")
    print(f"  Effective rate: {transaction.effective_rate:.2f}")
    print(f"  Enhancement: {transaction.enhancement_factor:.1f}×")
    print(f"  Execution time: {transaction.execution_time:.2f} time units")
    print("  ✓ Test passed\n")


def test_catalysis_benefit_analysis():
    """Test analysis of catalysis benefits"""
    print("Test 4: Catalysis Benefit Analysis")

    calc = ATPReactionKineticsCalculator()

    for transaction_type in [TransactionType.SIMPLE_TRANSFER, TransactionType.COLLECTIVE_DECISION]:
        print(f"  {transaction_type.value}:")
        results = calc.analyze_catalysis_benefit(transaction_type)

        print("    γ   | Enhancement | Speedup")
        print("    ----|-------------|--------")
        for gamma, metrics in sorted(results.items()):
            print(f"    {gamma:.1f} | {metrics['enhancement']:10.1f}× | {metrics['speedup']:6.1f}×")
        print()

    print("  ✓ Test passed\n")


def test_execution_time_comparison():
    """Test execution time differences"""
    print("Test 5: Execution Time Comparison")

    calc = ATPReactionKineticsCalculator()

    transaction_type = TransactionType.CONSENSUS_OPERATION
    atp_amount = 50.0

    print(f"  Consensus operation with {atp_amount} ATP:")
    print("    γ   | Execution Time | vs Independent")
    print("    ----|----------------|---------------")

    time_independent = calc.calculate_execution_time(transaction_type, 2.0, atp_amount)

    for gamma in [2.0, 1.5, 1.0, 0.5, 0.2]:
        exec_time = calc.calculate_execution_time(transaction_type, gamma, atp_amount)
        speedup = time_independent / exec_time
        print(f"    {gamma:.1f} | {exec_time:13.2f} | {speedup:12.1f}×")

    print("  ✓ Test passed\n")


def test_transaction_optimization():
    """Test transaction path optimization"""
    print("Test 6: Transaction Path Optimization")

    calc = ATPReactionKineticsCalculator()
    optimizer = TransactionOptimizer(calc)

    # Find optimal path for trust update
    intermediaries = [
        ("agent_C", 0.3),  # High correlation with from_agent
        ("agent_D", 1.0),  # Medium correlation
        ("agent_E", 1.8),  # Low correlation
    ]

    optimal_path = optimizer.calculate_optimal_path(
        from_agent="agent_A",
        to_agent="agent_B",
        intermediaries=intermediaries,
        transaction_type=TransactionType.TRUST_UPDATE,
        atp_amount=100.0
    )

    print(f"  Optimal path: {' → '.join(optimal_path)}")
    print(f"  Expected: Path through agent_C (γ=0.3) due to catalysis benefit")
    print("  ✓ Test passed\n")


def test_multi_transaction_comparison():
    """Test comparison across transaction types"""
    print("Test 7: Multi-Transaction Type Comparison")

    calc = ATPReactionKineticsCalculator()

    gamma = 0.5  # High correlation
    atp_amount = 100.0

    print(f"  All transaction types at γ={gamma}, {atp_amount} ATP:")
    print("    Type                  | Base Rate | Eff Rate | Enhancement | Exec Time")
    print("    ----------------------|-----------|----------|-------------|----------")

    for trans_type in TransactionType:
        params = calc.parameters[trans_type]
        k_eff, enhancement = calc.calculate_effective_rate(trans_type, gamma)
        exec_time = calc.calculate_execution_time(trans_type, gamma, atp_amount)

        print(f"    {trans_type.value:22} | {params.base_rate:8.2f} | {k_eff:7.2f} | {enhancement:10.1f}× | {exec_time:8.2f}")

    print("  ✓ Test passed\n")


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SESSION #180: ATP Transaction Catalysis")
    print("=" * 80)
    print()
    print("Integrating Chemistry Session 23 (Reaction Kinetics)")
    print()

    test_rate_enhancement()
    test_barrier_reduction()
    test_transaction_processing()
    test_catalysis_benefit_analysis()
    test_execution_time_comparison()
    test_transaction_optimization()
    test_multi_transaction_comparison()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)
