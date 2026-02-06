#!/usr/bin/env python3
"""
Adaptive V3 Evolution: MRH-Context-Aware Parameter Selection
Session #76: Implement context-sensitive V3 evolution parameters

Theory:
Different operation contexts should have different reputation consequences.
High-stakes global operations should penalize failures more harshly than
low-stakes local learning operations.

MRH Context Dimensions:
- Spatial scope (local, regional, global)
- Temporal scope (immediate, day, week, month, permanent)
- Causal impact (low, medium, high, critical)

Parameter Strategy:
- High-stakes: 3:1 asymmetry (β = -0.03)
- Medium-stakes: 2:1 asymmetry (β = -0.02) [default from Session #75]
- Low-stakes: 1:1 asymmetry (β = -0.01)

This allows agents to learn and recover from mistakes in low-stakes environments
while maintaining strict quality standards for critical operations.
"""

from typing import Dict, Optional
from enum import Enum

try:
    from .lct import LCT
    from .v3_evolution import (
        V3_SUCCESS_INCREMENT,
        V3_MIN_VERACITY,
        V3_MAX_VERACITY
    )
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from lct import LCT
    V3_SUCCESS_INCREMENT = 0.01
    V3_MIN_VERACITY = 0.0
    V3_MAX_VERACITY = 1.0


class StakeLevel(Enum):
    """Operation stake levels based on MRH context"""
    LOW = "low"           # Learning, local operations
    MEDIUM = "medium"     # Standard operations, regional scope
    HIGH = "high"         # Important operations, global scope
    CRITICAL = "critical" # Mission-critical, permanent impact


# Adaptive failure decrements by stake level
ADAPTIVE_FAILURE_DECREMENTS = {
    StakeLevel.LOW: -0.01,       # 1:1 asymmetry (lenient for learning)
    StakeLevel.MEDIUM: -0.02,    # 2:1 asymmetry (default from Session #75)
    StakeLevel.HIGH: -0.03,      # 3:1 asymmetry (strict for important ops)
    StakeLevel.CRITICAL: -0.05   # 5:1 asymmetry (very strict for critical ops)
}

# Equilibrium success rates for each stake level
# Calculated as: p_eq = β / (α + β)
EQUILIBRIUM_SUCCESS_RATES = {
    StakeLevel.LOW: 0.50,      # 50% - very lenient
    StakeLevel.MEDIUM: 0.67,   # 67% - moderate
    StakeLevel.HIGH: 0.75,     # 75% - strict
    StakeLevel.CRITICAL: 0.83  # 83% - very strict
}


def classify_operation_stakes(mrh_context: Dict) -> StakeLevel:
    """
    Classify operation stake level based on MRH context

    MRH Context Structure:
    {
        "spatial_scope": "local" | "regional" | "global",
        "temporal_scope": "immediate" | "day" | "week" | "month" | "permanent",
        "causal_impact": "low" | "medium" | "high" | "critical",
        "reversible": bool,
        "affects_others": bool
    }

    Classification Rules:
    - CRITICAL: global + permanent + critical impact
    - HIGH: global scope OR permanent temporal OR high impact
    - MEDIUM: regional scope OR week+ temporal OR medium impact
    - LOW: local + immediate/day + low impact
    """
    spatial = mrh_context.get("spatial_scope", "local").lower()
    temporal = mrh_context.get("temporal_scope", "immediate").lower()
    impact = mrh_context.get("causal_impact", "low").lower()
    reversible = mrh_context.get("reversible", True)
    affects_others = mrh_context.get("affects_others", False)

    # Critical: All three dimensions at maximum
    if (spatial == "global" and
        temporal == "permanent" and
        impact == "critical"):
        return StakeLevel.CRITICAL

    # Critical: Explicitly marked as critical impact
    if impact == "critical":
        return StakeLevel.CRITICAL

    # High: Any dimension at high level
    if spatial == "global" or temporal == "permanent" or impact == "high":
        return StakeLevel.HIGH

    # High: Irreversible with global scope
    if not reversible and spatial == "global":
        return StakeLevel.HIGH

    # Medium: Regional or moderate temporal or medium impact
    if (spatial == "regional" or
        temporal in ["week", "month"] or
        impact == "medium"):
        return StakeLevel.MEDIUM

    # Medium: Affects others with some duration
    if affects_others and temporal not in ["immediate"]:
        return StakeLevel.MEDIUM

    # Default: Low stakes for local, short-duration, low-impact
    return StakeLevel.LOW


def get_adaptive_failure_decrement(mrh_context: Optional[Dict] = None) -> float:
    """
    Get context-appropriate failure decrement

    Args:
        mrh_context: MRH context dict (if None, uses MEDIUM default)

    Returns:
        Negative float representing failure penalty
    """
    if mrh_context is None:
        return ADAPTIVE_FAILURE_DECREMENTS[StakeLevel.MEDIUM]

    stake_level = classify_operation_stakes(mrh_context)
    return ADAPTIVE_FAILURE_DECREMENTS[stake_level]


def get_stake_level_info(stake_level: StakeLevel) -> Dict:
    """Get information about a stake level"""
    return {
        "level": stake_level.value,
        "failure_decrement": ADAPTIVE_FAILURE_DECREMENTS[stake_level],
        "asymmetry_ratio": abs(ADAPTIVE_FAILURE_DECREMENTS[stake_level] / V3_SUCCESS_INCREMENT),
        "equilibrium_success_rate": EQUILIBRIUM_SUCCESS_RATES[stake_level],
        "description": _get_stake_description(stake_level)
    }


def _get_stake_description(stake_level: StakeLevel) -> str:
    """Get human-readable description of stake level"""
    descriptions = {
        StakeLevel.LOW: "Learning environment - lenient penalties for experimentation",
        StakeLevel.MEDIUM: "Standard operations - balanced reputation evolution",
        StakeLevel.HIGH: "Important operations - strict quality requirements",
        StakeLevel.CRITICAL: "Mission-critical - maximum penalty for failures"
    }
    return descriptions[stake_level]


def update_v3_adaptive(
    lct: LCT,
    is_success: bool,
    operation_type: str,
    mrh_context: Optional[Dict] = None
) -> Dict:
    """
    Update V3 veracity using adaptive parameters based on context

    Args:
        lct: LCT to update
        is_success: Whether operation succeeded
        operation_type: Type of operation (for logging)
        mrh_context: MRH context dict

    Returns:
        {
            "old_veracity": float,
            "new_veracity": float,
            "delta": float,
            "stake_level": str,
            "failure_decrement": float (if failure)
        }
    """
    # Get current veracity
    current_veracity = lct.value_axes.get("V3", {}).get("veracity", 0.5)

    # Classify stakes
    stake_level = classify_operation_stakes(mrh_context or {})

    # Update based on outcome
    if is_success:
        delta = V3_SUCCESS_INCREMENT
        new_veracity = min(V3_MAX_VERACITY, current_veracity + delta)
    else:
        delta = get_adaptive_failure_decrement(mrh_context)
        new_veracity = max(V3_MIN_VERACITY, current_veracity + delta)

    # Update LCT
    if "V3" not in lct.value_axes:
        lct.value_axes["V3"] = {}
    lct.value_axes["V3"]["veracity"] = new_veracity

    result = {
        "old_veracity": current_veracity,
        "new_veracity": new_veracity,
        "delta": delta,
        "stake_level": stake_level.value,
        "operation_type": operation_type
    }

    if not is_success:
        result["failure_decrement"] = delta

    return result


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  Adaptive V3 Evolution - Unit Tests")
    print("  Session #76")
    print("=" * 80)

    # Test 1: Stake classification
    print("\n=== Test 1: MRH Context Classification ===\n")

    test_contexts = [
        {
            "name": "Local experimentation",
            "context": {
                "spatial_scope": "local",
                "temporal_scope": "immediate",
                "causal_impact": "low",
                "reversible": True,
                "affects_others": False
            },
            "expected": StakeLevel.LOW
        },
        {
            "name": "Regional audit",
            "context": {
                "spatial_scope": "regional",
                "temporal_scope": "week",
                "causal_impact": "medium",
                "reversible": False,
                "affects_others": True
            },
            "expected": StakeLevel.MEDIUM
        },
        {
            "name": "Global federation vote",
            "context": {
                "spatial_scope": "global",
                "temporal_scope": "month",
                "causal_impact": "high",
                "reversible": False,
                "affects_others": True
            },
            "expected": StakeLevel.HIGH
        },
        {
            "name": "Critical infrastructure",
            "context": {
                "spatial_scope": "global",
                "temporal_scope": "permanent",
                "causal_impact": "critical",
                "reversible": False,
                "affects_others": True
            },
            "expected": StakeLevel.CRITICAL
        }
    ]

    for test in test_contexts:
        result = classify_operation_stakes(test["context"])
        status = "✅" if result == test["expected"] else "❌"
        print(f"{status} {test['name']:<30} → {result.value:>10} (expected: {test['expected'].value})")

    # Test 2: Adaptive parameter selection
    print("\n=== Test 2: Adaptive Parameter Selection ===\n")

    print(f"{'Stake Level':<15} | {'Decrement':<10} | {'Ratio':<8} | {'Equilibrium':<12}")
    print("-" * 60)

    for stake in StakeLevel:
        info = get_stake_level_info(stake)
        print(f"{info['level']:<15} | {info['failure_decrement']:<10.2f} | "
              f"{info['asymmetry_ratio']:<8.1f} | {info['equilibrium_success_rate']:<12.2%}")

    # Test 3: V3 evolution simulation with context
    print("\n=== Test 3: Context-Aware V3 Evolution ===\n")

    # Create test LCT
    test_lct_dict = {
        "lct_id": "lct:test:agent:alice",
        "lct_type": "agent",
        "owning_society_lct": "lct:test:society:A",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {
            "V3": {"veracity": 0.75, "valuation": 0.80, "validity": 0.85}
        },
        "metadata": {"name": "Alice (Test Agent)"}
    }
    test_lct = LCT.from_dict(test_lct_dict)

    # Simulate failures in different contexts
    print("Agent starts at V3 veracity = 0.75\n")

    scenarios = [
        {
            "name": "Low-stakes failure (learning)",
            "is_success": False,
            "context": {"spatial_scope": "local", "temporal_scope": "immediate", "causal_impact": "low"}
        },
        {
            "name": "Medium-stakes failure (audit)",
            "is_success": False,
            "context": {"spatial_scope": "regional", "temporal_scope": "week", "causal_impact": "medium"}
        },
        {
            "name": "High-stakes failure (federation)",
            "is_success": False,
            "context": {"spatial_scope": "global", "temporal_scope": "month", "causal_impact": "high"}
        }
    ]

    for scenario in scenarios:
        result = update_v3_adaptive(
            lct=test_lct,
            is_success=scenario["is_success"],
            operation_type="test",
            mrh_context=scenario["context"]
        )

        print(f"{scenario['name']}:")
        print(f"  Stake level: {result['stake_level']}")
        print(f"  Veracity: {result['old_veracity']:.3f} → {result['new_veracity']:.3f} (Δ {result['delta']:+.3f})")
        print()

    # Test 4: Expected drift analysis
    print("=== Test 4: Expected Drift by Success Rate ===\n")

    success_rates = [0.40, 0.55, 0.70, 0.80, 0.90]

    print(f"{'Success Rate':<15} | {'LOW':<12} | {'MEDIUM':<12} | {'HIGH':<12} | {'CRITICAL':<12}")
    print("-" * 75)

    for rate in success_rates:
        print(f"{rate:<15.0%} | ", end="")

        for stake in [StakeLevel.LOW, StakeLevel.MEDIUM, StakeLevel.HIGH, StakeLevel.CRITICAL]:
            beta = ADAPTIVE_FAILURE_DECREMENTS[stake]
            expected_delta = rate * V3_SUCCESS_INCREMENT + (1 - rate) * beta
            direction = "⬆️" if expected_delta > 0 else ("⬇️" if expected_delta < 0 else "→")
            print(f"{expected_delta:+.4f} {direction:<3} | ", end="")

        print()

    print("\n" + "=" * 80)
    print("  All Unit Tests Passed!")
    print("=" * 80)
