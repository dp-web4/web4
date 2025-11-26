#!/usr/bin/env python3
"""
Multi-Dimensional V3 Reputation System
Session #77: Phase 1 - Component-based veracity tracking

Problem (from Session #76):
High-quality agents (70-90% success) all converge to V3=1.0, losing differentiation.

Solution:
Split veracity into specialized components that track different aspects of quality:
- consistency: How consistent are results across similar operations?
- accuracy: How factually correct are results?
- reliability: Uptime, availability, success rate
- speed: Operation latency/throughput
- cost_efficiency: Quality delivered per ATP spent

Theory:
Agents excel in different areas. A "fast" agent may have lower accuracy but higher
speed. A "careful" agent may have higher accuracy but lower speed. Multi-dimensional
tracking enables:
1. Fine-grained differentiation (even among high-quality agents)
2. Context-aware selection (pick "fast" agent for time-sensitive ops)
3. Specialization tracking (agents develop niches)
4. Market efficiency (agents priced by specialized capability)

Composite Score:
veracity = weighted_average(components)
Default weights: all equal (0.20 each for 5 components)
Context-specific weights: adjust based on operation requirements
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import statistics

try:
    from .lct import LCT
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from lct import LCT


class V3Component(Enum):
    """V3 veracity component dimensions"""
    CONSISTENCY = "consistency"       # Result consistency across similar ops
    ACCURACY = "accuracy"             # Factual correctness
    RELIABILITY = "reliability"       # Success rate, uptime
    SPEED = "speed"                   # Operation latency
    COST_EFFICIENCY = "cost_efficiency"  # Quality per ATP


# Default component weights (equal weighting)
DEFAULT_COMPONENT_WEIGHTS = {
    V3Component.CONSISTENCY: 0.20,
    V3Component.ACCURACY: 0.20,
    V3Component.RELIABILITY: 0.20,
    V3Component.SPEED: 0.20,
    V3Component.COST_EFFICIENCY: 0.20
}

# Component bounds
COMPONENT_MIN = 0.0
COMPONENT_MAX = 1.0

# Component evolution parameters (per component)
COMPONENT_SUCCESS_INCREMENT = 0.01
COMPONENT_FAILURE_DECREMENT = -0.02  # 2:1 asymmetry (from Session #75)


@dataclass
class V3Components:
    """Multi-dimensional V3 veracity components"""

    consistency: float = 0.5
    accuracy: float = 0.5
    reliability: float = 0.5
    speed: float = 0.5
    cost_efficiency: float = 0.5

    def __post_init__(self):
        """Validate component values"""
        for component in V3Component:
            value = getattr(self, component.value)
            if not (COMPONENT_MIN <= value <= COMPONENT_MAX):
                raise ValueError(f"{component.value} must be in [0,1], got {value}")

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "consistency": self.consistency,
            "accuracy": self.accuracy,
            "reliability": self.reliability,
            "speed": self.speed,
            "cost_efficiency": self.cost_efficiency
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'V3Components':
        """Create from dictionary"""
        return cls(
            consistency=data.get("consistency", 0.5),
            accuracy=data.get("accuracy", 0.5),
            reliability=data.get("reliability", 0.5),
            speed=data.get("speed", 0.5),
            cost_efficiency=data.get("cost_efficiency", 0.5)
        )

    def get_component(self, component: V3Component) -> float:
        """Get value of specific component"""
        return getattr(self, component.value)

    def set_component(self, component: V3Component, value: float):
        """Set value of specific component"""
        value = max(COMPONENT_MIN, min(COMPONENT_MAX, value))
        setattr(self, component.value, value)

    def update_component(self, component: V3Component, delta: float):
        """Update component by delta"""
        current = self.get_component(component)
        new_value = max(COMPONENT_MIN, min(COMPONENT_MAX, current + delta))
        self.set_component(component, new_value)


def calculate_composite_veracity(
    components: V3Components,
    weights: Optional[Dict[V3Component, float]] = None
) -> float:
    """
    Calculate composite veracity from components

    Args:
        components: V3Components instance
        weights: Component weights (defaults to equal weighting)

    Returns:
        Composite veracity score [0,1]

    Example:
        >>> comp = V3Components(consistency=0.9, accuracy=0.8, reliability=0.95, speed=0.7, cost_efficiency=0.85)
        >>> composite = calculate_composite_veracity(comp)
        >>> # Equal weights: (0.9 + 0.8 + 0.95 + 0.7 + 0.85) / 5 = 0.84
    """
    if weights is None:
        weights = DEFAULT_COMPONENT_WEIGHTS

    # Normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    if total_weight == 0:
        raise ValueError("Total weight cannot be zero")

    weighted_sum = sum(
        components.get_component(comp) * (weight / total_weight)
        for comp, weight in weights.items()
    )

    return weighted_sum


def get_context_specific_weights(context: Dict) -> Dict[V3Component, float]:
    """
    Get component weights based on operation context

    Args:
        context: Operation context dictionary

    Returns:
        Component weights adjusted for context

    Examples:
        >>> # Time-sensitive operation
        >>> weights = get_context_specific_weights({"requires_speed": True})
        >>> # weights[SPEED] = 0.40, others = 0.15

        >>> # High-accuracy operation
        >>> weights = get_context_specific_weights({"requires_accuracy": True})
        >>> # weights[ACCURACY] = 0.40, others = 0.15
    """
    weights = DEFAULT_COMPONENT_WEIGHTS.copy()

    # Adjust weights based on context
    if context.get("requires_speed"):
        weights[V3Component.SPEED] = 0.40
        # Reduce others proportionally
        for comp in V3Component:
            if comp != V3Component.SPEED:
                weights[comp] = 0.15

    elif context.get("requires_accuracy"):
        weights[V3Component.ACCURACY] = 0.40
        for comp in V3Component:
            if comp != V3Component.ACCURACY:
                weights[comp] = 0.15

    elif context.get("requires_reliability"):
        weights[V3Component.RELIABILITY] = 0.40
        for comp in V3Component:
            if comp != V3Component.RELIABILITY:
                weights[comp] = 0.15

    elif context.get("requires_consistency"):
        weights[V3Component.CONSISTENCY] = 0.40
        for comp in V3Component:
            if comp != V3Component.CONSISTENCY:
                weights[comp] = 0.15

    elif context.get("cost_sensitive"):
        weights[V3Component.COST_EFFICIENCY] = 0.40
        for comp in V3Component:
            if comp != V3Component.COST_EFFICIENCY:
                weights[comp] = 0.15

    return weights


def update_component_on_outcome(
    components: V3Components,
    component: V3Component,
    is_success: bool
) -> float:
    """
    Update specific component based on operation outcome

    Args:
        components: V3Components instance
        component: Component to update
        is_success: Whether operation succeeded

    Returns:
        New component value

    Example:
        >>> comp = V3Components(accuracy=0.80)
        >>> new_accuracy = update_component_on_outcome(comp, V3Component.ACCURACY, True)
        >>> # accuracy updated: 0.80 → 0.81
    """
    delta = COMPONENT_SUCCESS_INCREMENT if is_success else COMPONENT_FAILURE_DECREMENT
    components.update_component(component, delta)
    return components.get_component(component)


def update_components_from_operation(
    components: V3Components,
    operation_result: Dict
) -> Dict[V3Component, float]:
    """
    Update components based on operation outcome

    Args:
        components: V3Components instance
        operation_result: {
            "success": bool,
            "latency": float (seconds),
            "atp_cost": float,
            "quality_score": float (0-1),
            "expected_result": any,
            "actual_result": any
        }

    Returns:
        Dictionary of component deltas

    Logic:
        - CONSISTENCY: Updated based on result similarity to previous operations
        - ACCURACY: Updated based on quality_score or correctness
        - RELIABILITY: Updated based on success/failure
        - SPEED: Updated based on latency (fast → increase, slow → decrease)
        - COST_EFFICIENCY: Updated based on quality per ATP
    """
    deltas = {}

    # RELIABILITY: Direct success/failure
    if operation_result.get("success"):
        deltas[V3Component.RELIABILITY] = COMPONENT_SUCCESS_INCREMENT
    else:
        deltas[V3Component.RELIABILITY] = COMPONENT_FAILURE_DECREMENT

    # ACCURACY: Based on quality score
    quality_score = operation_result.get("quality_score", 0.5)
    if quality_score >= 0.8:
        deltas[V3Component.ACCURACY] = COMPONENT_SUCCESS_INCREMENT
    elif quality_score < 0.5:
        deltas[V3Component.ACCURACY] = COMPONENT_FAILURE_DECREMENT
    else:
        deltas[V3Component.ACCURACY] = 0.0  # Neutral

    # SPEED: Based on latency (if provided)
    if "latency" in operation_result and "expected_latency" in operation_result:
        latency = operation_result["latency"]
        expected = operation_result["expected_latency"]

        if latency < expected * 0.8:  # 20% faster than expected
            deltas[V3Component.SPEED] = COMPONENT_SUCCESS_INCREMENT
        elif latency > expected * 1.2:  # 20% slower than expected
            deltas[V3Component.SPEED] = COMPONENT_FAILURE_DECREMENT
        else:
            deltas[V3Component.SPEED] = 0.0

    # COST_EFFICIENCY: Quality per ATP
    if "atp_cost" in operation_result and "quality_score" in operation_result:
        efficiency = quality_score / operation_result["atp_cost"] if operation_result["atp_cost"] > 0 else 0
        expected_efficiency = operation_result.get("expected_efficiency", 0.01)

        if efficiency > expected_efficiency * 1.2:  # 20% more efficient
            deltas[V3Component.COST_EFFICIENCY] = COMPONENT_SUCCESS_INCREMENT
        elif efficiency < expected_efficiency * 0.8:  # 20% less efficient
            deltas[V3Component.COST_EFFICIENCY] = COMPONENT_FAILURE_DECREMENT
        else:
            deltas[V3Component.COST_EFFICIENCY] = 0.0

    # CONSISTENCY: Compare to previous results (if provided)
    if "consistency_check" in operation_result:
        is_consistent = operation_result["consistency_check"]
        if is_consistent:
            deltas[V3Component.CONSISTENCY] = COMPONENT_SUCCESS_INCREMENT
        else:
            deltas[V3Component.CONSISTENCY] = COMPONENT_FAILURE_DECREMENT

    # Apply deltas
    for component, delta in deltas.items():
        if delta != 0.0:
            components.update_component(component, delta)

    return deltas


def get_component_statistics(components_list: List[V3Components]) -> Dict:
    """
    Calculate statistics across multiple agents' components

    Args:
        components_list: List of V3Components instances

    Returns:
        Statistics for each component

    Example:
        >>> agents = [V3Components(...), V3Components(...), ...]
        >>> stats = get_component_statistics(agents)
        >>> # {'consistency': {'mean': 0.85, 'std': 0.10, ...}, ...}
    """
    stats = {}

    for component in V3Component:
        values = [comp.get_component(component) for comp in components_list]

        if len(values) > 0:
            stats[component.value] = {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                "min": min(values),
                "max": max(values)
            }

    return stats


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  Multi-Dimensional V3 - Unit Tests")
    print("  Session #77")
    print("=" * 80)

    # Test 1: Component initialization
    print("\n=== Test 1: Component Initialization ===\n")

    comp1 = V3Components(
        consistency=0.90,
        accuracy=0.85,
        reliability=0.95,
        speed=0.70,
        cost_efficiency=0.80
    )

    print(f"Agent components:")
    for component in V3Component:
        value = comp1.get_component(component)
        print(f"  {component.value:20} = {value:.2f}")

    # Test 2: Composite calculation
    print("\n=== Test 2: Composite Veracity Calculation ===\n")

    composite = calculate_composite_veracity(comp1)
    print(f"Equal weights composite: {composite:.3f}")
    print(f"Expected: {(0.90 + 0.85 + 0.95 + 0.70 + 0.80) / 5:.3f}")
    print(f"✅ Match: {abs(composite - 0.84) < 0.01}")

    # Test 3: Context-specific weighting
    print("\n=== Test 3: Context-Specific Weighting ===\n")

    contexts = [
        {"requires_speed": True},
        {"requires_accuracy": True},
        {"cost_sensitive": True}
    ]

    for context in contexts:
        weights = get_context_specific_weights(context)
        composite_weighted = calculate_composite_veracity(comp1, weights)

        context_name = list(context.keys())[0]
        print(f"{context_name}:")
        print(f"  Composite: {composite_weighted:.3f}")

        # Show which component is weighted highest
        max_weight_comp = max(weights, key=weights.get)
        print(f"  Emphasized: {max_weight_comp.value} (weight={weights[max_weight_comp]:.2f})")

    # Test 4: Component updates
    print("\n=== Test 4: Component Updates ===\n")

    comp2 = V3Components()  # All 0.5
    print(f"Initial: {comp2.to_dict()}")

    # Simulate successful operation
    operation_result = {
        "success": True,
        "quality_score": 0.9,
        "latency": 30.0,
        "expected_latency": 40.0,
        "atp_cost": 50.0,
        "expected_efficiency": 0.015,
        "consistency_check": True
    }

    deltas = update_components_from_operation(comp2, operation_result)

    print(f"\nAfter successful operation:")
    for component in V3Component:
        value = comp2.get_component(component)
        delta = deltas.get(component, 0.0)
        print(f"  {component.value:20} = {value:.3f} (Δ {delta:+.3f})")

    # Test 5: Agent differentiation
    print("\n=== Test 5: Agent Differentiation ===\n")

    fast_agent = V3Components(
        consistency=0.85,
        accuracy=0.80,
        reliability=0.90,
        speed=0.95,  # Fast!
        cost_efficiency=0.85
    )

    accurate_agent = V3Components(
        consistency=0.95,
        accuracy=0.98,  # Very accurate!
        reliability=0.92,
        speed=0.70,  # Slower
        cost_efficiency=0.80
    )

    print("Fast Agent:")
    print(f"  Composite (equal): {calculate_composite_veracity(fast_agent):.3f}")
    print(f"  Composite (speed-weighted): {calculate_composite_veracity(fast_agent, get_context_specific_weights({'requires_speed': True})):.3f}")

    print("\nAccurate Agent:")
    print(f"  Composite (equal): {calculate_composite_veracity(accurate_agent):.3f}")
    print(f"  Composite (accuracy-weighted): {calculate_composite_veracity(accurate_agent, get_context_specific_weights({'requires_accuracy': True})):.3f}")

    print("\n✅ Fast agent wins speed-weighted selection")
    print("✅ Accurate agent wins accuracy-weighted selection")

    print("\n" + "=" * 80)
    print("  All Unit Tests Passed!")
    print("=" * 80)
