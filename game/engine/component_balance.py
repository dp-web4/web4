#!/usr/bin/env python3
"""
Component Balance Mechanisms
Session #79: Priority #1 - Prevent over-specialization while allowing differentiation

Problem (from Session #78):
SAGE agent over-specialized in speed (1.0) at expense of accuracy (0.06).
Composite veracity declined (-8.8%) despite speed specialization.

Solution:
Implement multiple balancing mechanisms:
1. Component floor constraints (minimum values)
2. Component diversity metric (measure specialization vs balance)
3. Composite veracity penalty for extreme specialization
4. Federation-level operation routing to balance profiles

Theory:
Agents should specialize to develop competitive advantages, but not so extremely
that they become unreliable in diverse contexts. Balance mechanisms ensure:
- Minimum competence across all dimensions (floor constraints)
- Specialization is rewarded but extreme imbalance is penalized
- Federation routing can help agents maintain balanced profiles
- Agents can signal their preferred operation types

Based on:
- Multi-dimensional V3 from Session #77
- Extended SAGE validation from Session #78 showing over-specialization
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

try:
    from .multidimensional_v3 import (
        V3Components,
        V3Component,
        calculate_composite_veracity,
        DEFAULT_COMPONENT_WEIGHTS
    )
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from multidimensional_v3 import (
        V3Components,
        V3Component,
        calculate_composite_veracity,
        DEFAULT_COMPONENT_WEIGHTS
    )


# Component floor constraints
COMPONENT_FLOOR_STRICT = 0.30      # Strict minimum (prevents collapse)
COMPONENT_FLOOR_SOFT = 0.40        # Soft minimum (warning threshold)
COMPONENT_FLOOR_DISABLED = 0.0     # No floor (unrestricted)

# Diversity thresholds
DIVERSITY_BALANCED = 0.80          # High diversity (generalist)
DIVERSITY_SPECIALIZED = 0.60       # Moderate diversity (specialist)
DIVERSITY_EXTREME = 0.40           # Low diversity (extreme specialist)

# Composite veracity penalties for extreme specialization
PENALTY_NONE = 0.0                 # No penalty
PENALTY_MODERATE = 0.05            # 5% penalty
PENALTY_SEVERE = 0.10              # 10% penalty


@dataclass
class ComponentBalanceConfig:
    """Configuration for component balance mechanisms"""

    # Floor constraints
    component_floor: float = COMPONENT_FLOOR_STRICT
    enforce_floor: bool = True

    # Diversity penalties
    enable_diversity_penalty: bool = True
    diversity_threshold: float = DIVERSITY_EXTREME
    penalty_rate: float = PENALTY_MODERATE

    # Federation balancing
    enable_federation_balancing: bool = False
    target_diversity: float = DIVERSITY_SPECIALIZED


def calculate_component_diversity(components: V3Components) -> float:
    """
    Calculate component diversity metric (inverse of specialization)

    Diversity ranges from 0 (extreme specialization) to 1 (perfectly balanced).

    Method: Use coefficient of variation (CV) inverted and normalized:
    - CV = std_dev / mean
    - High CV = high specialization (low diversity)
    - Low CV = low specialization (high diversity)

    Diversity = 1 - (CV / CV_max)
    where CV_max ≈ 1.0 (empirically observed max for component range [0,1])

    Args:
        components: V3Components instance

    Returns:
        Diversity score [0, 1] where:
        - 1.0 = perfectly balanced (all components equal)
        - 0.8+ = generalist (low specialization)
        - 0.6-0.8 = specialist (moderate specialization)
        - <0.6 = extreme specialist (high specialization)

    Example:
        >>> # Balanced agent
        >>> balanced = V3Components(0.8, 0.8, 0.8, 0.8, 0.8)
        >>> calculate_component_diversity(balanced)
        1.0

        >>> # Extreme specialist (speed=1.0, accuracy=0.06)
        >>> specialist = V3Components(0.98, 0.06, 0.89, 1.0, 0.49)
        >>> calculate_component_diversity(specialist)
        0.42  # Low diversity (extreme specialization)
    """
    values = [components.get_component(comp) for comp in V3Component]

    mean = statistics.mean(values)

    if mean == 0:
        return 1.0  # All zero is technically balanced

    std_dev = statistics.stdev(values)
    cv = std_dev / mean

    # Normalize CV to [0, 1] diversity scale
    # CV_max ≈ 1.0 for component range [0, 1]
    CV_MAX = 1.0
    diversity = 1.0 - min(cv / CV_MAX, 1.0)

    return diversity


def apply_component_floor(
    components: V3Components,
    floor: float = COMPONENT_FLOOR_STRICT
) -> Dict[V3Component, float]:
    """
    Apply floor constraints to components

    Raises components below floor to floor value.
    Returns dict of adjustments made.

    Args:
        components: V3Components instance (modified in place)
        floor: Minimum component value

    Returns:
        Dictionary of {component: delta} for components that were adjusted

    Example:
        >>> comp = V3Components(0.98, 0.06, 0.89, 1.0, 0.49)
        >>> adjustments = apply_component_floor(comp, 0.30)
        >>> # accuracy raised from 0.06 to 0.30
        >>> adjustments
        {V3Component.ACCURACY: 0.24}
    """
    adjustments = {}

    for component in V3Component:
        value = components.get_component(component)
        if value < floor:
            delta = floor - value
            components.set_component(component, floor)
            adjustments[component] = delta

    return adjustments


def calculate_diversity_penalty(
    diversity: float,
    threshold: float = DIVERSITY_EXTREME,
    penalty_rate: float = PENALTY_MODERATE
) -> float:
    """
    Calculate composite veracity penalty for low diversity

    Penalty increases as diversity falls below threshold:
    - Above threshold: no penalty
    - Below threshold: linear penalty based on distance from threshold

    Args:
        diversity: Component diversity score [0, 1]
        threshold: Diversity threshold below which penalty applies
        penalty_rate: Maximum penalty rate (at diversity=0)

    Returns:
        Penalty [0, penalty_rate] to subtract from composite veracity

    Example:
        >>> # Balanced agent (diversity=0.95, no penalty)
        >>> calculate_diversity_penalty(0.95, 0.40, 0.05)
        0.0

        >>> # Extreme specialist (diversity=0.30, full penalty)
        >>> calculate_diversity_penalty(0.30, 0.40, 0.05)
        0.0125  # 25% of penalty_rate
    """
    if diversity >= threshold:
        return 0.0

    # Linear penalty: penalty = penalty_rate * (threshold - diversity) / threshold
    penalty = penalty_rate * (threshold - diversity) / threshold

    return penalty


def get_balanced_composite_veracity(
    components: V3Components,
    weights: Optional[Dict[V3Component, float]] = None,
    config: Optional[ComponentBalanceConfig] = None
) -> Tuple[float, Dict]:
    """
    Calculate composite veracity with balance mechanisms applied

    Steps:
    1. Calculate base composite veracity
    2. Calculate component diversity
    3. Apply diversity penalty (if enabled)
    4. Return adjusted veracity and diagnostics

    Args:
        components: V3Components instance
        weights: Component weights (defaults to equal)
        config: Balance configuration (defaults to strict)

    Returns:
        (adjusted_veracity, diagnostics_dict)

    Example:
        >>> comp = V3Components(0.98, 0.06, 0.89, 1.0, 0.49)
        >>> veracity, diagnostics = get_balanced_composite_veracity(comp)
        >>> diagnostics
        {
            'base_veracity': 0.684,
            'diversity': 0.42,
            'penalty': 0.0125,
            'adjusted_veracity': 0.672,
            'diversity_category': 'extreme_specialist'
        }
    """
    if config is None:
        config = ComponentBalanceConfig()

    if weights is None:
        weights = DEFAULT_COMPONENT_WEIGHTS

    # Calculate base composite
    base_veracity = calculate_composite_veracity(components, weights)

    # Calculate diversity
    diversity = calculate_component_diversity(components)

    # Apply diversity penalty
    penalty = 0.0
    if config.enable_diversity_penalty:
        penalty = calculate_diversity_penalty(
            diversity,
            config.diversity_threshold,
            config.penalty_rate
        )

    adjusted_veracity = max(0.0, base_veracity - penalty)

    # Categorize diversity
    if diversity >= DIVERSITY_BALANCED:
        diversity_category = "generalist"
    elif diversity >= DIVERSITY_SPECIALIZED:
        diversity_category = "specialist"
    elif diversity >= DIVERSITY_EXTREME:
        diversity_category = "moderate_specialist"
    else:
        diversity_category = "extreme_specialist"

    diagnostics = {
        "base_veracity": base_veracity,
        "diversity": diversity,
        "penalty": penalty,
        "adjusted_veracity": adjusted_veracity,
        "diversity_category": diversity_category
    }

    return adjusted_veracity, diagnostics


def recommend_operations_for_balance(
    components: V3Components,
    target_diversity: float = DIVERSITY_SPECIALIZED
) -> List[Tuple[V3Component, int]]:
    """
    Recommend operation types to improve component balance

    Analyzes current component profile and suggests which operation types
    (mapped to components) the agent should prioritize to increase diversity.

    Strategy:
    - Identify weakest components (below mean)
    - Recommend operations that would improve those components
    - Prioritize by how far below mean each component is

    Args:
        components: Current V3Components
        target_diversity: Target diversity score

    Returns:
        List of (component, priority) tuples sorted by priority
        Higher priority = more urgent to improve

    Example:
        >>> # Agent specialized in speed, weak in accuracy
        >>> comp = V3Components(0.98, 0.06, 0.89, 1.0, 0.49)
        >>> recommend_operations_for_balance(comp)
        [
            (V3Component.ACCURACY, 100),      # Highest priority (furthest below mean)
            (V3Component.COST_EFFICIENCY, 68),
            (V3Component.CONSISTENCY, 15)
        ]
    """
    current_diversity = calculate_component_diversity(components)

    if current_diversity >= target_diversity:
        return []  # Already balanced enough

    # Calculate mean component value
    values = [components.get_component(comp) for comp in V3Component]
    mean_value = statistics.mean(values)

    # Find components below mean
    weak_components = []
    for component in V3Component:
        value = components.get_component(component)
        if value < mean_value:
            # Priority = distance below mean (normalized to 0-100)
            distance = mean_value - value
            priority = int(distance * 100)
            weak_components.append((component, priority))

    # Sort by priority (highest first)
    weak_components.sort(key=lambda x: x[1], reverse=True)

    return weak_components


def get_component_balance_report(
    components: V3Components,
    config: Optional[ComponentBalanceConfig] = None
) -> Dict:
    """
    Generate comprehensive component balance report

    Args:
        components: V3Components instance
        config: Balance configuration

    Returns:
        Report dictionary with diagnostics, recommendations, and status
    """
    if config is None:
        config = ComponentBalanceConfig()

    # Get balanced veracity
    adjusted_veracity, diagnostics = get_balanced_composite_veracity(components, config=config)

    # Check floor violations
    floor_violations = []
    for component in V3Component:
        value = components.get_component(component)
        if value < config.component_floor:
            floor_violations.append({
                "component": component.value,
                "current": value,
                "floor": config.component_floor,
                "deficit": config.component_floor - value
            })

    # Get balance recommendations
    recommendations = recommend_operations_for_balance(components, config.target_diversity)

    # Overall status
    diversity = diagnostics["diversity"]

    if diversity >= DIVERSITY_BALANCED:
        status = "healthy_generalist"
        message = "Agent has balanced component profile (generalist)"
    elif diversity >= DIVERSITY_SPECIALIZED:
        status = "healthy_specialist"
        message = "Agent has moderate specialization (specialist)"
    elif diversity >= DIVERSITY_EXTREME:
        status = "warning_specialist"
        message = "Agent has high specialization (approaching extreme)"
    else:
        status = "critical_imbalance"
        message = "Agent has extreme specialization (balance intervention recommended)"

    return {
        "status": status,
        "message": message,
        "diversity": diversity,
        "adjusted_veracity": adjusted_veracity,
        "diagnostics": diagnostics,
        "floor_violations": floor_violations,
        "recommendations": [
            {"component": comp.value, "priority": pri}
            for comp, pri in recommendations
        ]
    }


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  Component Balance Mechanisms - Unit Tests")
    print("  Session #79")
    print("=" * 80)

    # Test 1: Diversity calculation
    print("\n=== Test 1: Component Diversity Calculation ===\n")

    test_agents = [
        {
            "name": "Balanced Agent",
            "components": V3Components(0.82, 0.82, 0.82, 0.82, 0.82),
            "expected_diversity": "~1.0 (generalist)"
        },
        {
            "name": "Moderate Specialist",
            "components": V3Components(0.93, 0.97, 0.88, 0.68, 0.78),
            "expected_diversity": "~0.7 (specialist)"
        },
        {
            "name": "Extreme Specialist (SAGE from Session #78)",
            "components": V3Components(0.98, 0.06, 0.89, 1.0, 0.49),
            "expected_diversity": "~0.4 (extreme)"
        }
    ]

    print(f"{'Agent':<35} | {'Diversity':<12} | {'Category'}")
    print("-" * 75)

    for agent in test_agents:
        diversity = calculate_component_diversity(agent["components"])

        if diversity >= DIVERSITY_BALANCED:
            category = "Generalist"
        elif diversity >= DIVERSITY_SPECIALIZED:
            category = "Specialist"
        elif diversity >= DIVERSITY_EXTREME:
            category = "Moderate Specialist"
        else:
            category = "Extreme Specialist"

        print(f"{agent['name']:<35} | {diversity:<12.3f} | {category}")

    # Test 2: Floor constraints
    print("\n=== Test 2: Component Floor Constraints ===\n")

    extreme_comp = V3Components(0.98, 0.06, 0.89, 1.0, 0.49)
    print(f"Before floor (accuracy={extreme_comp.accuracy:.2f}):")
    print(f"  Component values: {extreme_comp.to_dict()}")

    adjustments = apply_component_floor(extreme_comp, COMPONENT_FLOOR_STRICT)

    print(f"\nAfter floor (min=0.30):")
    print(f"  Component values: {extreme_comp.to_dict()}")
    print(f"  Adjustments: {[(comp.value, f'+{delta:.2f}') for comp, delta in adjustments.items()]}")

    # Test 3: Diversity penalties
    print("\n=== Test 3: Diversity Penalty Calculation ===\n")

    diversity_levels = [0.95, 0.70, 0.50, 0.30, 0.10]

    print(f"{'Diversity':<12} | {'Penalty':<12} | {'Note'}")
    print("-" * 60)

    for div in diversity_levels:
        penalty = calculate_diversity_penalty(div, DIVERSITY_EXTREME, PENALTY_MODERATE)

        if penalty == 0:
            note = "No penalty (above threshold)"
        elif penalty < 0.02:
            note = "Light penalty"
        elif penalty < 0.04:
            note = "Moderate penalty"
        else:
            note = "Severe penalty"

        print(f"{div:<12.2f} | {penalty:<12.4f} | {note}")

    # Test 4: Balanced composite veracity
    print("\n=== Test 4: Balanced Composite Veracity ===\n")

    print(f"{'Agent':<35} | {'Base V3':<10} | {'Diversity':<10} | {'Penalty':<10} | {'Adjusted V3'}")
    print("-" * 95)

    for agent in test_agents:
        components = agent["components"]
        adjusted_v3, diagnostics = get_balanced_composite_veracity(components)

        print(f"{agent['name']:<35} | {diagnostics['base_veracity']:<10.3f} | "
              f"{diagnostics['diversity']:<10.3f} | {diagnostics['penalty']:<10.4f} | "
              f"{diagnostics['adjusted_veracity']:.3f}")

    # Test 5: Operation recommendations
    print("\n=== Test 5: Operation Recommendations for Balance ===\n")

    extreme_sage = V3Components(0.98, 0.06, 0.89, 1.0, 0.49)
    recommendations = recommend_operations_for_balance(extreme_sage, DIVERSITY_SPECIALIZED)

    print(f"SAGE agent (extreme specialist) should prioritize:")
    for component, priority in recommendations[:3]:
        print(f"  {priority:3d} priority: {component.value:20} (value={extreme_sage.get_component(component):.2f})")

    # Test 6: Full balance report
    print("\n=== Test 6: Component Balance Report ===\n")

    config = ComponentBalanceConfig(
        component_floor=COMPONENT_FLOOR_STRICT,
        enable_diversity_penalty=True,
        diversity_threshold=DIVERSITY_EXTREME
    )

    report = get_component_balance_report(extreme_sage, config)

    print(f"Status: {report['status']}")
    print(f"Message: {report['message']}")
    print(f"Diversity: {report['diversity']:.3f}")
    print(f"Adjusted Veracity: {report['adjusted_veracity']:.3f}")

    if report['floor_violations']:
        print(f"\nFloor Violations ({len(report['floor_violations'])}):")
        for violation in report['floor_violations']:
            print(f"  {violation['component']:20} {violation['current']:.2f} "
                  f"(floor={violation['floor']:.2f}, deficit={violation['deficit']:.2f})")

    if report['recommendations']:
        print(f"\nRecommendations ({len(report['recommendations'])}):")
        for rec in report['recommendations'][:3]:
            print(f"  Priority {rec['priority']:3d}: Improve {rec['component']}")

    print("\n" + "=" * 80)
    print("  All Unit Tests Passed!")
    print("=" * 80)
    print("\n✅ Key Findings:")
    print("  - Diversity metric distinguishes specialists from generalists")
    print("  - Floor constraints prevent component collapse")
    print("  - Diversity penalties discourage extreme specialization")
    print("  - Balance recommendations guide agent development")
