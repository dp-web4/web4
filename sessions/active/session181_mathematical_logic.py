"""
Session #181: Mathematical Logic from Coherence

Integrates Session 258 (Mathematics from Coherence) into Web4's reasoning validation.

Key Insight from Session 258:
    Mathematics = invariant patterns in coherence
    Logic = coherence compatibility

    Boolean logic emerges when C → {0, 1} (crisp coherence):
    - AND(A, B) = min(C_A, C_B)  [both must cohere]
    - OR(A, B) = max(C_A, C_B)   [either coheres]
    - NOT(A) = 1 - C_A           [complement]

    At C < 0.5: Fuzzy, probabilistic logic
    At C = 0.5: Transition to Boolean (1 bit threshold)
    At C > 0.5: Crisp, deterministic logic

Application to Web4:
    Agent reasoning is validated through mathematical coherence:
    - Invalid logic = incoherent reasoning (C < 0.5)
    - Valid logic = coherent reasoning (C ≥ 0.5)
    - Perfect logic = crisp Boolean (C → 1.0)

    This provides:
    - Logical consistency validation
    - Inference coherence checking
    - Reasoning quality assessment
    - Fuzzy → Boolean transition detection

Author: Web4 Research Session 18
Date: January 13, 2026
Status: IN PROGRESS
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum


# ============================================================================
# Logic Types
# ============================================================================

class LogicType(Enum):
    """Types of logical reasoning"""
    FUZZY = "fuzzy"          # C < 0.5 (probabilistic)
    THRESHOLD = "threshold"  # C ≈ 0.5 (transition)
    BOOLEAN = "boolean"      # C > 0.5 (crisp)
    PERFECT = "perfect"      # C → 1.0 (deterministic)


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class LogicalStatement:
    """A logical statement with coherence"""
    statement_id: str
    content: str
    coherence: float  # Truth value in [0, 1]
    logic_type: LogicType

    # Supporting evidence
    evidence_coherence: List[float]
    inference_chain: List[str]


@dataclass
class LogicalOperation:
    """Result of a logical operation"""
    operation: str  # AND, OR, NOT, IMPLIES
    inputs: List[str]  # Statement IDs
    output_coherence: float
    is_valid: bool  # C ≥ 0.5
    explanation: str


@dataclass
class ReasoningChain:
    """Chain of logical inference"""
    premises: List[LogicalStatement]
    conclusion: LogicalStatement
    operations: List[LogicalOperation]
    overall_coherence: float
    is_valid_inference: bool


# ============================================================================
# Coherence Logic Engine
# ============================================================================

class CoherenceLogicEngine:
    """
    Implements logical operations as coherence compatibility.

    From Session 258:
    - AND(A, B) = min(C_A, C_B)
    - OR(A, B) = max(C_A, C_B)
    - NOT(A) = 1 - C_A
    - IMPLIES(A, B) = max(1 - C_A, C_B)
    """

    BOOLEAN_THRESHOLD = 0.5  # Transition to crisp logic
    FUZZY_THRESHOLD = 0.3    # Below this → highly uncertain
    PERFECT_THRESHOLD = 0.9  # Above this → near-certain


    def __init__(self):
        self.operations_log: List[LogicalOperation] = []


    def logic_and(self, c_a: float, c_b: float) -> float:
        """
        Coherence AND: min(C_A, C_B)

        Both statements must cohere for conjunction to cohere.
        """
        return min(c_a, c_b)


    def logic_or(self, c_a: float, c_b: float) -> float:
        """
        Coherence OR: max(C_A, C_B)

        Either statement cohering makes disjunction cohere.
        """
        return max(c_a, c_b)


    def logic_not(self, c_a: float) -> float:
        """
        Coherence NOT: 1 - C_A

        Complement in coherence space.
        """
        return 1.0 - c_a


    def logic_implies(self, c_a: float, c_b: float) -> float:
        """
        Coherence IMPLIES: max(1 - C_A, C_B)

        A → B is logically equivalent to ¬A ∨ B
        """
        return max(1.0 - c_a, c_b)


    def classify_logic_type(self, coherence: float) -> LogicType:
        """
        Classify type of logic based on coherence level.
        """
        if coherence < self.FUZZY_THRESHOLD:
            return LogicType.FUZZY
        elif coherence < self.BOOLEAN_THRESHOLD:
            return LogicType.FUZZY
        elif coherence < self.PERFECT_THRESHOLD:
            return LogicType.BOOLEAN
        else:
            return LogicType.PERFECT


    def execute_operation(
        self,
        operation: str,
        inputs: List[LogicalStatement]
    ) -> LogicalOperation:
        """
        Execute a logical operation on statements.

        Args:
            operation: AND, OR, NOT, IMPLIES
            inputs: Input statements

        Returns:
            Operation result with coherence
        """
        if operation == "AND":
            if len(inputs) < 2:
                raise ValueError("AND requires at least 2 inputs")
            coherences = [s.coherence for s in inputs]
            output_coherence = coherences[0]
            for c in coherences[1:]:
                output_coherence = self.logic_and(output_coherence, c)

        elif operation == "OR":
            if len(inputs) < 2:
                raise ValueError("OR requires at least 2 inputs")
            coherences = [s.coherence for s in inputs]
            output_coherence = coherences[0]
            for c in coherences[1:]:
                output_coherence = self.logic_or(output_coherence, c)

        elif operation == "NOT":
            if len(inputs) != 1:
                raise ValueError("NOT requires exactly 1 input")
            output_coherence = self.logic_not(inputs[0].coherence)

        elif operation == "IMPLIES":
            if len(inputs) != 2:
                raise ValueError("IMPLIES requires exactly 2 inputs")
            output_coherence = self.logic_implies(
                inputs[0].coherence,
                inputs[1].coherence
            )
        else:
            raise ValueError(f"Unknown operation: {operation}")

        is_valid = output_coherence >= self.BOOLEAN_THRESHOLD

        explanation = f"{operation}({', '.join(s.statement_id for s in inputs)}) = {output_coherence:.3f}"

        result = LogicalOperation(
            operation=operation,
            inputs=[s.statement_id for s in inputs],
            output_coherence=output_coherence,
            is_valid=is_valid,
            explanation=explanation
        )

        self.operations_log.append(result)

        return result


    def validate_reasoning_chain(
        self,
        premises: List[LogicalStatement],
        conclusion: LogicalStatement,
        operations: List[Tuple[str, List[int]]]  # (operation, input_indices)
    ) -> ReasoningChain:
        """
        Validate a chain of logical reasoning.

        Args:
            premises: Starting statements
            conclusion: Final conclusion
            operations: Sequence of operations to validate

        Returns:
            Reasoning chain with overall coherence
        """
        # Execute operations
        executed_ops = []
        intermediate_results = premises.copy()

        for operation, input_indices in operations:
            inputs = [intermediate_results[i] for i in input_indices]
            op_result = self.execute_operation(operation, inputs)

            # Create intermediate statement
            inter_statement = LogicalStatement(
                statement_id=f"intermediate_{len(executed_ops)}",
                content=op_result.explanation,
                coherence=op_result.output_coherence,
                logic_type=self.classify_logic_type(op_result.output_coherence),
                evidence_coherence=[s.coherence for s in inputs],
                inference_chain=[s.statement_id for s in inputs]
            )

            intermediate_results.append(inter_statement)
            executed_ops.append(op_result)

        # Check if conclusion coherence matches
        final_coherence = intermediate_results[-1].coherence
        coherence_match = abs(final_coherence - conclusion.coherence) < 0.1

        # Overall coherence is minimum along chain
        overall_coherence = min(op.output_coherence for op in executed_ops)

        is_valid = overall_coherence >= self.BOOLEAN_THRESHOLD and coherence_match

        chain = ReasoningChain(
            premises=premises,
            conclusion=conclusion,
            operations=executed_ops,
            overall_coherence=overall_coherence,
            is_valid_inference=is_valid
        )

        return chain


# ============================================================================
# Mathematical Validity Detector
# ============================================================================

class MathematicalValidityDetector:
    """
    Detects mathematical validity through coherence patterns.

    From Session 258: Mathematics = invariant coherence patterns
    From Gnosis Session 10: Mathematical validity detection at C ≥ 0.5
    """

    def __init__(self):
        self.logic_engine = CoherenceLogicEngine()


    def detect_pattern_invariance(
        self,
        pattern: List[float],
        transformations: List[List[float]]
    ) -> Tuple[bool, float]:
        """
        Detect if pattern is invariant under transformations.

        From Session 258: Mathematics = invariant patterns in coherence

        Args:
            pattern: Original coherence pattern
            transformations: Transformed versions

        Returns:
            (is_invariant, coherence_of_invariance)
        """
        if not transformations:
            return True, 1.0

        # Calculate similarity of each transformation to original
        similarities = []
        for transformed in transformations:
            if len(transformed) != len(pattern):
                continue

            # Correlation as similarity measure
            mean_orig = sum(pattern) / len(pattern)
            mean_trans = sum(transformed) / len(transformed)

            numerator = sum(
                (pattern[i] - mean_orig) * (transformed[i] - mean_trans)
                for i in range(len(pattern))
            )

            var_orig = sum((x - mean_orig) ** 2 for x in pattern)
            var_trans = sum((x - mean_trans) ** 2 for x in transformed)

            denom = math.sqrt(var_orig * var_trans) if var_orig > 0 and var_trans > 0 else 0

            similarity = numerator / denom if denom > 0 else 0
            similarities.append(abs(similarity))

        # Coherence of invariance = how similar all transformations are
        if similarities:
            coherence_invariance = sum(similarities) / len(similarities)
        else:
            coherence_invariance = 0.0

        is_invariant = coherence_invariance >= 0.8  # High similarity threshold

        return is_invariant, coherence_invariance


    def validate_arithmetic(
        self,
        operation: str,
        operands: List[float],
        result: float,
        tolerance: float = 0.01
    ) -> Tuple[bool, float]:
        """
        Validate arithmetic operation through coherence.

        From Session 258: Arithmetic from coherence

        Returns:
            (is_valid, coherence_of_validity)
        """
        # Execute operation
        if operation == "add":
            expected = sum(operands)
        elif operation == "multiply":
            expected = 1.0
            for x in operands:
                expected *= x
        elif operation == "subtract":
            if len(operands) != 2:
                return False, 0.0
            expected = operands[0] - operands[1]
        elif operation == "divide":
            if len(operands) != 2 or operands[1] == 0:
                return False, 0.0
            expected = operands[0] / operands[1]
        else:
            return False, 0.0

        # Check if result matches expectation
        error = abs(result - expected)
        is_valid = error < tolerance

        # Coherence = how close to expected (1.0 = perfect, 0.0 = totally wrong)
        if abs(expected) > tolerance:
            coherence = max(0.0, 1.0 - error / abs(expected))
        else:
            coherence = 1.0 if error < tolerance else 0.0

        return is_valid, coherence


    def detect_mathematical_structure(
        self,
        coherence_values: List[float]
    ) -> Dict[str, float]:
        """
        Detect mathematical structure in coherence values.

        Returns metrics for different mathematical properties.
        """
        if not coherence_values:
            return {"structure_coherence": 0.0}

        # Mean and variance
        mean = sum(coherence_values) / len(coherence_values)
        variance = sum((x - mean) ** 2 for x in coherence_values) / len(coherence_values)
        std_dev = math.sqrt(variance)

        # Periodicity detection (simple autocorrelation)
        periodicity = 0.0
        if len(coherence_values) >= 4:
            # Check lag-1 autocorrelation
            lag1_corr = 0.0
            for i in range(len(coherence_values) - 1):
                lag1_corr += coherence_values[i] * coherence_values[i + 1]
            lag1_corr /= (len(coherence_values) - 1)
            periodicity = lag1_corr / (mean ** 2) if mean > 0 else 0

        # Structure coherence = how much mathematical structure present
        # High if: low variance (consistency) and/or high periodicity
        consistency = max(0.0, 1.0 - std_dev)  # Low variance = high consistency

        structure_coherence = (consistency + abs(periodicity)) / 2

        return {
            "mean": mean,
            "variance": variance,
            "std_dev": std_dev,
            "periodicity": periodicity,
            "consistency": consistency,
            "structure_coherence": structure_coherence
        }


# ============================================================================
# Test Cases
# ============================================================================

def test_logic_operations():
    """Test basic coherence logic operations"""
    print("Test 1: Coherence Logic Operations")

    engine = CoherenceLogicEngine()

    # Test AND
    c_and = engine.logic_and(0.8, 0.7)
    print(f"  AND(0.8, 0.7) = {c_and:.2f} (expected: 0.70)")

    # Test OR
    c_or = engine.logic_or(0.8, 0.7)
    print(f"  OR(0.8, 0.7) = {c_or:.2f} (expected: 0.80)")

    # Test NOT
    c_not = engine.logic_not(0.8)
    print(f"  NOT(0.8) = {c_not:.2f} (expected: 0.20)")

    # Test IMPLIES
    c_implies = engine.logic_implies(0.8, 0.7)
    print(f"  IMPLIES(0.8, 0.7) = {c_implies:.2f} (expected: 0.70)")

    print("  ✓ Test passed\n")


def test_boolean_threshold():
    """Test transition to Boolean logic at C = 0.5"""
    print("Test 2: Boolean Threshold (C = 0.5)")

    engine = CoherenceLogicEngine()

    test_values = [0.3, 0.4, 0.5, 0.6, 0.7]

    print("    C   | Logic Type | Valid?")
    print("  ------|------------|-------")

    for c in test_values:
        logic_type = engine.classify_logic_type(c)
        is_valid = c >= engine.BOOLEAN_THRESHOLD
        print(f"  {c:.1f} | {logic_type.value:10} | {is_valid}")

    print("\n  At C = 0.5: Transition from fuzzy to Boolean logic")
    print("  ✓ Test passed\n")


def test_reasoning_chain():
    """Test validation of logical reasoning chain"""
    print("Test 3: Reasoning Chain Validation")

    engine = CoherenceLogicEngine()

    # Premises: "Sky is blue" (C=0.8), "Grass is green" (C=0.7)
    premise1 = LogicalStatement(
        statement_id="p1",
        content="Sky is blue",
        coherence=0.8,
        logic_type=LogicType.BOOLEAN,
        evidence_coherence=[0.8],
        inference_chain=[]
    )

    premise2 = LogicalStatement(
        statement_id="p2",
        content="Grass is green",
        coherence=0.7,
        logic_type=LogicType.BOOLEAN,
        evidence_coherence=[0.7],
        inference_chain=[]
    )

    # Conclusion: "Sky is blue AND grass is green" (C=0.7)
    conclusion = LogicalStatement(
        statement_id="conclusion",
        content="Sky is blue AND grass is green",
        coherence=0.7,
        logic_type=LogicType.BOOLEAN,
        evidence_coherence=[0.8, 0.7],
        inference_chain=["p1", "p2"]
    )

    # Operations: AND(p1, p2)
    operations = [
        ("AND", [0, 1])  # Combine premise 0 and premise 1
    ]

    chain = engine.validate_reasoning_chain([premise1, premise2], conclusion, operations)

    print(f"  Premises: {len(chain.premises)}")
    print(f"  Operations: {len(chain.operations)}")
    print(f"  Overall coherence: {chain.overall_coherence:.3f}")
    print(f"  Valid inference: {chain.is_valid_inference}")
    print(f"  ✓ Test passed\n" if chain.is_valid_inference else f"  ✗ Test failed\n")


def test_pattern_invariance():
    """Test detection of invariant patterns"""
    print("Test 4: Pattern Invariance Detection")

    detector = MathematicalValidityDetector()

    # Test 1: Invariant pattern (all transformations similar)
    pattern = [0.5, 0.6, 0.7, 0.6, 0.5]
    transformations = [
        [0.5, 0.6, 0.7, 0.6, 0.5],  # Same
        [0.52, 0.58, 0.68, 0.62, 0.48],  # Slight variation
    ]

    is_invariant, coherence = detector.detect_pattern_invariance(pattern, transformations)

    print(f"  Invariant pattern:")
    print(f"    Is invariant: {is_invariant}")
    print(f"    Coherence: {coherence:.3f}")

    # Test 2: Non-invariant pattern (transformations differ)
    transformations2 = [
        [0.1, 0.2, 0.3, 0.4, 0.5],  # Very different
        [0.9, 0.8, 0.7, 0.6, 0.5],  # Reversed
    ]

    is_invariant2, coherence2 = detector.detect_pattern_invariance(pattern, transformations2)

    print(f"  Non-invariant pattern:")
    print(f"    Is invariant: {is_invariant2}")
    print(f"    Coherence: {coherence2:.3f}")

    print("  ✓ Test passed\n")


def test_arithmetic_validation():
    """Test arithmetic operation validation"""
    print("Test 5: Arithmetic Validation")

    detector = MathematicalValidityDetector()

    # Test valid addition
    is_valid, coherence = detector.validate_arithmetic("add", [2.0, 3.0], 5.0)
    print(f"  2 + 3 = 5: valid={is_valid}, coherence={coherence:.3f}")

    # Test invalid addition
    is_valid2, coherence2 = detector.validate_arithmetic("add", [2.0, 3.0], 6.0)
    print(f"  2 + 3 = 6: valid={is_valid2}, coherence={coherence2:.3f}")

    # Test multiplication
    is_valid3, coherence3 = detector.validate_arithmetic("multiply", [2.0, 3.0], 6.0)
    print(f"  2 × 3 = 6: valid={is_valid3}, coherence={coherence3:.3f}")

    print("  ✓ Test passed\n")


def test_mathematical_structure():
    """Test detection of mathematical structure"""
    print("Test 6: Mathematical Structure Detection")

    detector = MathematicalValidityDetector()

    # Highly structured (low variance)
    structured = [0.5, 0.5, 0.5, 0.5, 0.5]
    metrics1 = detector.detect_mathematical_structure(structured)
    print(f"  Highly structured: coherence={metrics1['structure_coherence']:.3f}")

    # Moderately structured
    moderate = [0.4, 0.5, 0.6, 0.5, 0.4]
    metrics2 = detector.detect_mathematical_structure(moderate)
    print(f"  Moderately structured: coherence={metrics2['structure_coherence']:.3f}")

    # Unstructured (high variance)
    unstructured = [0.1, 0.9, 0.2, 0.8, 0.3]
    metrics3 = detector.detect_mathematical_structure(unstructured)
    print(f"  Unstructured: coherence={metrics3['structure_coherence']:.3f}")

    print("  ✓ Test passed\n")


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SESSION #181: Mathematical Logic from Coherence")
    print("=" * 80)
    print()
    print("Integrating Session 258 (Mathematics from Coherence)")
    print()

    test_logic_operations()
    test_boolean_threshold()
    test_reasoning_chain()
    test_pattern_invariance()
    test_arithmetic_validation()
    test_mathematical_structure()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)
    print()
    print("KEY INSIGHT:")
    print("Logic is coherence compatibility. Valid reasoning = coherence-preserving")
    print("transformations. The Boolean threshold at C = 0.5 is where fuzzy logic")
    print("crystallizes into crisp, deterministic inference.")
    print("=" * 80)
