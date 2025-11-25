#!/usr/bin/env python3
"""
V3 (Value through Verification) Evolution Mechanics

Session #73: Implements automatic V3 veracity updates based on operation outcomes

V3 Axes:
- Veracity (0.0-1.0): Truthfulness, accuracy, reproducibility of agent actions
- Valuation (0.0-1.0): Economic value provided
- Validity (0.0-1.0): Legitimacy of agent's claims and authorization

This module focuses on veracity evolution, which is critical for quality-aware
agent selection (Session #73). Agents with higher veracity are trusted for
critical operations.

Evolution Rules:
- Successful operations increase veracity (slow growth)
- Failed operations decrease veracity (faster decay)
- External validation increases veracity (moderate boost)
- No activity leads to decay (entropy)
- Veracity bounded [0.0, 1.0]

Based on Web4 whitepaper V3 specification and HRM trust evolution patterns.
"""

from typing import Dict, Optional

try:
    from .lct import LCT
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from lct import LCT


# V3 Evolution Parameters
V3_SUCCESS_INCREMENT = 0.01      # Small increase per successful operation
V3_FAILURE_DECREMENT = -0.05     # Larger decrease per failure (5x impact)
V3_VALIDATION_BOOST = 0.02       # External validation boost
V3_DECAY_RATE = 0.001            # Entropy decay per tick without activity
V3_MIN_VERACITY = 0.0            # Lower bound
V3_MAX_VERACITY = 1.0            # Upper bound


def update_v3_on_success(lct: LCT, operation_type: str) -> float:
    """
    Update V3 veracity after successful operation

    Args:
        lct: LCT object to update
        operation_type: Type of operation that succeeded

    Returns:
        New veracity value

    Example:
        >>> agent = LCT(...)
        >>> agent.value_axes = {"V3": {"veracity": 0.80}}
        >>> new_veracity = update_v3_on_success(agent, "insurance_claim")
        >>> # veracity increased from 0.80 to 0.81
    """
    current_veracity = lct.value_axes.get("V3", {}).get("veracity", 0.5)

    # Small increment for successful operations
    new_veracity = min(V3_MAX_VERACITY, current_veracity + V3_SUCCESS_INCREMENT)

    # Update LCT
    if "V3" not in lct.value_axes:
        lct.value_axes["V3"] = {}
    lct.value_axes["V3"]["veracity"] = new_veracity

    return new_veracity


def update_v3_on_failure(lct: LCT, operation_type: str, severity: float = 1.0) -> float:
    """
    Update V3 veracity after failed operation

    Failures have larger impact than successes (5x by default) to quickly
    identify unreliable agents.

    Args:
        lct: LCT object to update
        operation_type: Type of operation that failed
        severity: Failure severity multiplier (1.0 = normal, 2.0 = critical failure)

    Returns:
        New veracity value

    Example:
        >>> agent = LCT(...)
        >>> agent.value_axes = {"V3": {"veracity": 0.80}}
        >>> new_veracity = update_v3_on_failure(agent, "insurance_claim", severity=2.0)
        >>> # veracity decreased from 0.80 to 0.70 (2x severity = -0.10)
    """
    current_veracity = lct.value_axes.get("V3", {}).get("veracity", 0.5)

    # Larger decrement for failures, scaled by severity
    decrement = V3_FAILURE_DECREMENT * severity
    new_veracity = max(V3_MIN_VERACITY, current_veracity + decrement)

    # Update LCT
    if "V3" not in lct.value_axes:
        lct.value_axes["V3"] = {}
    lct.value_axes["V3"]["veracity"] = new_veracity

    return new_veracity


def update_v3_on_validation(lct: LCT, validator_veracity: float) -> float:
    """
    Update V3 veracity after external validation

    When another high-veracity agent validates this agent's work, boost veracity.
    The boost is scaled by the validator's own veracity (high-veracity validators
    provide stronger endorsements).

    Args:
        lct: LCT object to update
        validator_veracity: V3 veracity of validating agent (0.0-1.0)

    Returns:
        New veracity value

    Example:
        >>> agent = LCT(...)
        >>> agent.value_axes = {"V3": {"veracity": 0.70}}
        >>> # High-veracity validator (0.95) validates agent's work
        >>> new_veracity = update_v3_on_validation(agent, validator_veracity=0.95)
        >>> # veracity increased from 0.70 to ~0.72 (scaled by 0.95)
    """
    current_veracity = lct.value_axes.get("V3", {}).get("veracity", 0.5)

    # Validation boost scaled by validator's own veracity
    boost = V3_VALIDATION_BOOST * validator_veracity
    new_veracity = min(V3_MAX_VERACITY, current_veracity + boost)

    # Update LCT
    if "V3" not in lct.value_axes:
        lct.value_axes["V3"] = {}
    lct.value_axes["V3"]["veracity"] = new_veracity

    return new_veracity


def apply_v3_decay(lct: LCT, ticks_inactive: int = 1) -> float:
    """
    Apply entropy decay to V3 veracity

    Without activity or validation, veracity slowly decays toward uncertainty (0.5).
    This models the fact that trust erodes without reinforcement.

    Args:
        lct: LCT object to update
        ticks_inactive: Number of ticks without activity

    Returns:
        New veracity value

    Example:
        >>> agent = LCT(...)
        >>> agent.value_axes = {"V3": {"veracity": 0.90}}
        >>> # Agent inactive for 100 ticks
        >>> new_veracity = apply_v3_decay(agent, ticks_inactive=100)
        >>> # veracity decreased from 0.90 toward 0.5 (uncertainty)
    """
    current_veracity = lct.value_axes.get("V3", {}).get("veracity", 0.5)

    # Decay toward uncertainty (0.5)
    target = 0.5
    decay = V3_DECAY_RATE * ticks_inactive

    if current_veracity > target:
        # Decay downward toward 0.5
        new_veracity = max(target, current_veracity - decay)
    elif current_veracity < target:
        # Decay upward toward 0.5 (low veracity rises with no activity)
        new_veracity = min(target, current_veracity + decay)
    else:
        new_veracity = target

    # Update LCT
    if "V3" not in lct.value_axes:
        lct.value_axes["V3"] = {}
    lct.value_axes["V3"]["veracity"] = new_veracity

    return new_veracity


def record_operation_outcome(
    lct: LCT,
    operation_type: str,
    success: bool,
    severity: float = 1.0
) -> Dict[str, float]:
    """
    Record operation outcome and update V3 veracity

    Convenience function that combines success/failure updates.

    Args:
        lct: LCT object to update
        operation_type: Type of operation
        success: Whether operation succeeded
        severity: Failure severity (only used if success=False)

    Returns:
        Dict with old and new veracity values

    Example:
        >>> agent = LCT(...)
        >>> agent.value_axes = {"V3": {"veracity": 0.75}}
        >>> result = record_operation_outcome(
        ...     agent, "insurance_claim", success=True
        ... )
        >>> print(f"Veracity: {result['old']} → {result['new']}")
    """
    old_veracity = lct.value_axes.get("V3", {}).get("veracity", 0.5)

    if success:
        new_veracity = update_v3_on_success(lct, operation_type)
    else:
        new_veracity = update_v3_on_failure(lct, operation_type, severity)

    return {
        "old": old_veracity,
        "new": new_veracity,
        "delta": new_veracity - old_veracity,
        "operation": operation_type,
        "success": success
    }


def simulate_v3_evolution(
    initial_veracity: float,
    operations: list,
    ticks_between_ops: int = 10
) -> list:
    """
    Simulate V3 veracity evolution over time

    Args:
        initial_veracity: Starting veracity
        operations: List of (operation_type, success, severity) tuples
        ticks_between_ops: Ticks between operations (for decay)

    Returns:
        List of veracity values at each step

    Example:
        >>> operations = [
        ...     ("insurance_claim", True, 1.0),
        ...     ("audit_request", True, 1.0),
        ...     ("treasury_transfer", False, 2.0),  # Critical failure
        ... ]
        >>> history = simulate_v3_evolution(0.80, operations, ticks_between_ops=50)
    """
    # LCT already imported at top

    # Create mock LCT
    agent = LCT(
        lct_id="sim_agent",
        lct_type="agent",
        owning_society_lct="sim_society",
        created_at_block=1,
        created_at_tick=1,
        value_axes={"V3": {"veracity": initial_veracity}}
    )

    history = [initial_veracity]

    for operation_type, success, severity in operations:
        # Apply decay for time between operations
        if ticks_between_ops > 0:
            apply_v3_decay(agent, ticks_inactive=ticks_between_ops)

        # Record operation outcome
        result = record_operation_outcome(agent, operation_type, success, severity)
        history.append(result["new"])

    return history


# Testing utilities
def test_v3_evolution():
    """Test V3 evolution mechanics"""
    # LCT already imported at top

    print("=" * 80)
    print("Testing V3 Evolution Mechanics")
    print("=" * 80)
    print()

    # Create test agent
    agent = LCT(
        lct_id="test_agent",
        lct_type="agent",
        owning_society_lct="test_society",
        created_at_block=1,
        created_at_tick=1,
        value_axes={"V3": {"veracity": 0.75, "valuation": 0.8, "validity": 0.85}}
    )

    print(f"Initial veracity: {agent.value_axes['V3']['veracity']:.3f}")
    print()

    # Test 1: Successful operations
    print("Test 1: Successful Operations (5x)")
    for i in range(5):
        old = agent.value_axes['V3']['veracity']
        new = update_v3_on_success(agent, "insurance_claim")
        print(f"  Op {i+1}: {old:.3f} → {new:.3f} (+{new-old:.3f})")
    print()

    # Test 2: Failed operation
    print("Test 2: Failed Operation (normal severity)")
    old = agent.value_axes['V3']['veracity']
    new = update_v3_on_failure(agent, "audit_request", severity=1.0)
    print(f"  {old:.3f} → {new:.3f} ({new-old:.3f})")
    print()

    # Test 3: Critical failure
    print("Test 3: Critical Failure (2x severity)")
    old = agent.value_axes['V3']['veracity']
    new = update_v3_on_failure(agent, "treasury_transfer", severity=2.0)
    print(f"  {old:.3f} → {new:.3f} ({new-old:.3f})")
    print()

    # Test 4: External validation
    print("Test 4: External Validation (high-veracity validator)")
    old = agent.value_axes['V3']['veracity']
    new = update_v3_on_validation(agent, validator_veracity=0.95)
    print(f"  {old:.3f} → {new:.3f} (+{new-old:.3f})")
    print()

    # Test 5: Decay simulation
    print("Test 5: Entropy Decay (100 ticks inactive)")
    agent.value_axes['V3']['veracity'] = 0.90  # Reset to high veracity
    old = agent.value_axes['V3']['veracity']
    new = apply_v3_decay(agent, ticks_inactive=100)
    print(f"  {old:.3f} → {new:.3f} ({new-old:.3f}) [decaying toward 0.5]")
    print()

    # Test 6: Evolution simulation
    print("Test 6: Evolution Simulation")
    operations = [
        ("insurance_claim", True, 1.0),
        ("insurance_claim", True, 1.0),
        ("audit_request", True, 1.0),
        ("treasury_transfer", False, 1.0),  # One failure
        ("insurance_claim", True, 1.0),
        ("fraud_investigation", False, 2.0),  # Critical failure
    ]
    history = simulate_v3_evolution(0.75, operations, ticks_between_ops=10)
    print(f"  Starting veracity: {history[0]:.3f}")
    for i, veracity in enumerate(history[1:], 1):
        op_type, success, severity = operations[i-1]
        status = "✓" if success else "✗"
        print(f"  Step {i} ({status} {op_type}): {veracity:.3f}")
    print()

    print("=" * 80)
    print("✓ All tests complete")
    print("=" * 80)


if __name__ == "__main__":
    test_v3_evolution()
