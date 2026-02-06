#!/usr/bin/env python3
"""
Quality-Aware Agent Selection

Implements quality-first agent selection using V3 veracity as quality gate.
Based on HRM quality-aware selection experiment (Session #72).

Philosophy: Quality is a hard constraint, not a soft optimization goal.
Better to fail fast with clear errors than succeed with degraded quality.

Key Concepts:
- V3 veracity (0.0-1.0) represents agent quality/trustworthiness
- Operations have minimum quality requirements
- Selection filters by quality FIRST, then optimizes ATP cost
- Budget/quality violations fail explicitly with actionable errors

References:
- Session #72: HRM Quality-Aware Selection Integration
- HRM sage/experiments/quality_aware_edge_experiment.py
- Web4 V3 Implementation (Session #71)
"""

from dataclasses import dataclass
from typing import List, Optional, Dict

try:
    from .lct import LCT
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from lct import LCT


# Custom Exceptions
class InsufficientQualityError(Exception):
    """Raised when no agent meets quality requirements"""
    pass


class InsufficientATPBudgetError(Exception):
    """Raised when qualified agents exceed ATP budget"""
    pass


# Operation → Quality Mapping
OPERATION_QUALITY_REQUIREMENTS = {
    # Critical operations (high veracity required)
    "insurance_claim": 0.90,
    "role_binding": 0.85,
    "treasury_transfer": 0.90,
    "cross_society_authorization": 0.90,
    "fraud_investigation": 0.90,

    # Important operations (medium veracity)
    "audit_request": 0.75,
    "reputation_update": 0.75,
    "federation_join": 0.80,
    "resource_allocation": 0.75,

    # Routine operations (low veracity acceptable)
    "event_logging": 0.50,
    "cache_update": 0.50,
    "metrics_collection": 0.60,
    "status_query": 0.50,
}


@dataclass
class SelectionResult:
    """Result from quality-aware agent selection"""
    agent_lct: str  # Selected agent's LCT ID
    atp_cost: float
    v3_veracity: float
    reason: str  # Selection reason/strategy
    alternatives_count: int  # Number of qualified alternatives


def get_quality_requirement(operation_type: str) -> float:
    """
    Get quality requirement for operation type

    Args:
        operation_type: Type of operation

    Returns:
        Minimum V3 veracity required (0.0-1.0)

    Example:
        >>> get_quality_requirement("insurance_claim")
        0.90
        >>> get_quality_requirement("event_logging")
        0.50
    """
    return OPERATION_QUALITY_REQUIREMENTS.get(operation_type, 0.70)  # Default: medium


def select_agent_with_quality(
    operation_type: str,
    agents: List[LCT],
    atp_costs: Dict[str, float],
    min_quality: Optional[float] = None,
    atp_budget: Optional[float] = None
) -> SelectionResult:
    """
    Select agent with quality-first, then ATP-optimal strategy

    Selection Algorithm (Quality-First):
    1. Auto-infer quality requirement from operation_type (if not specified)
    2. Filter agents by V3 veracity >= min_quality (HARD CONSTRAINT)
    3. Filter by ATP budget if specified (HARD CONSTRAINT)
    4. Select cheapest qualified agent (SOFT OPTIMIZATION)

    This ensures:
    - Quality requirements are NEVER compromised
    - Budget constraints are ALWAYS respected
    - ATP cost is minimized among qualified agents

    Args:
        operation_type: Type of operation (determines quality requirement)
        agents: Available agent LCTs
        atp_costs: ATP cost per agent (keyed by lct_id)
        min_quality: Minimum V3 veracity (or auto-infer from operation_type)
        atp_budget: Maximum ATP to spend (None = unlimited)

    Returns:
        SelectionResult with agent, cost, quality, reason

    Raises:
        InsufficientQualityError: No agent meets quality requirement
        InsufficientATPBudgetError: No qualified agent within budget

    Example:
        >>> # High-quality operation (insurance claim)
        >>> result = select_agent_with_quality(
        ...     operation_type="insurance_claim",
        ...     agents=[agent1, agent2, agent3],
        ...     atp_costs={"agent1": 10, "agent2": 50, "agent3": 100}
        ... )
        >>> # Will select agent with V3 veracity >= 0.90 and lowest ATP cost
    """
    # Step 1: Auto-infer quality if not specified
    if min_quality is None:
        min_quality = get_quality_requirement(operation_type)

    # Step 2: Filter by quality (HARD CONSTRAINT)
    qualified = []
    for agent in agents:
        veracity = agent.value_axes.get("V3", {}).get("veracity", 0.0)
        if veracity >= min_quality:
            qualified.append(agent)

    if not qualified:
        # No agent meets quality requirement - FAIL FAST
        best_available = max(
            agents,
            key=lambda a: a.value_axes.get("V3", {}).get("veracity", 0.0)
        )
        best_veracity = best_available.value_axes.get("V3", {}).get("veracity", 0.0)

        raise InsufficientQualityError(
            f"No agent meets veracity requirement {min_quality:.2f} for {operation_type}. "
            f"Best available: {best_available.lct_id} with veracity {best_veracity:.2f}. "
            f"Consider reducing quality requirement or improving agent capabilities."
        )

    # Step 3: Filter by budget if specified (HARD CONSTRAINT)
    if atp_budget is not None:
        affordable = [a for a in qualified if atp_costs.get(a.lct_id, float('inf')) <= atp_budget]

        if not affordable:
            # Qualified agents exist but exceed budget - FAIL FAST
            min_required_cost = min([atp_costs.get(a.lct_id, float('inf')) for a in qualified])

            raise InsufficientATPBudgetError(
                f"Quality requirement {min_quality:.2f} needs minimum {min_required_cost:.1f} ATP, "
                f"but budget is {atp_budget:.1f}. "
                f"Increase budget or reduce quality requirement."
            )

        qualified = affordable

    # Step 4: Select cheapest qualified agent (SOFT OPTIMIZATION)
    selected = min(qualified, key=lambda a: atp_costs.get(a.lct_id, float('inf')))
    selected_veracity = selected.value_axes.get("V3", {}).get("veracity", 0.0)
    selected_cost = atp_costs.get(selected.lct_id, 0.0)

    return SelectionResult(
        agent_lct=selected.lct_id,
        atp_cost=selected_cost,
        v3_veracity=selected_veracity,
        reason=f"quality_first (Q>={min_quality:.2f}, Cost={selected_cost:.1f})",
        alternatives_count=len(qualified) - 1
    )


def select_agent_with_quality_and_mrh(
    operation_type: str,
    agents: List[LCT],
    atp_costs: Dict[str, float],
    mrh_profile: Optional[Dict[str, str]] = None,
    min_quality: Optional[float] = None,
    atp_budget: Optional[float] = None
) -> SelectionResult:
    """
    Select agent considering both quality and MRH fit

    Extended selection that considers:
    1. Quality (V3 veracity)
    2. MRH horizon fit (deltaR, deltaT, deltaC)
    3. ATP cost optimization

    Selection Algorithm:
    1. Filter by quality requirement (HARD CONSTRAINT)
    2. Filter by MRH fit if specified (SOFT PREFERENCE)
    3. Filter by ATP budget (HARD CONSTRAINT)
    4. Select cheapest qualified agent (SOFT OPTIMIZATION)

    Args:
        operation_type: Type of operation
        agents: Available agent LCTs
        atp_costs: ATP cost per agent
        mrh_profile: Optional MRH profile to match (deltaR, deltaT, deltaC)
        min_quality: Minimum V3 veracity
        atp_budget: Maximum ATP to spend

    Returns:
        SelectionResult

    Raises:
        InsufficientQualityError: No agent meets quality requirement
        InsufficientATPBudgetError: No qualified agent within budget
    """
    # Start with quality-first selection
    result = select_agent_with_quality(
        operation_type=operation_type,
        agents=agents,
        atp_costs=atp_costs,
        min_quality=min_quality,
        atp_budget=atp_budget
    )

    # TODO: Add MRH filtering when MRH profiles are available on LCT objects
    # For now, quality-first selection is sufficient

    return result


def estimate_operation_cost(
    operation_type: str,
    base_atp_cost: float,
    quality_multiplier: Optional[float] = None
) -> float:
    """
    Estimate ATP cost for operation considering quality requirements

    Cost Model:
    - Base cost from MRH profile (spatial, temporal, complexity)
    - Quality multiplier based on operation type
    - Higher quality operations cost more ATP

    Args:
        operation_type: Type of operation
        base_atp_cost: Base ATP cost from MRH profile
        quality_multiplier: Optional quality multiplier (auto-infer if None)

    Returns:
        Estimated ATP cost

    Example:
        >>> estimate_operation_cost("insurance_claim", base_atp_cost=50)
        100.0  # 2x multiplier for high-quality operation
    """
    if quality_multiplier is None:
        # Infer multiplier from quality requirement
        min_quality = get_quality_requirement(operation_type)

        if min_quality >= 0.90:
            quality_multiplier = 2.0  # High quality = 2x cost
        elif min_quality >= 0.75:
            quality_multiplier = 1.5  # Medium quality = 1.5x cost
        else:
            quality_multiplier = 1.0  # Low quality = base cost

    return base_atp_cost * quality_multiplier


# Testing utilities
def test_agent_selection():
    """Test quality-aware agent selection"""
    print("=" * 80)
    print("Testing Quality-Aware Agent Selection")
    print("=" * 80)
    print()

    # Create mock agents with different V3 veracity levels
    # LCT already imported at top

    agents = [
        LCT(
            lct_id="agent_low_quality",
            lct_type="agent",
            owning_society_lct="society_1",
            created_at_block=1,
            created_at_tick=1,
            value_axes={"V3": {"veracity": 0.60, "valuation": 0.8, "validity": 0.9}}
        ),
        LCT(
            lct_id="agent_medium_quality",
            lct_type="agent",
            owning_society_lct="society_1",
            created_at_block=1,
            created_at_tick=1,
            value_axes={"V3": {"veracity": 0.80, "valuation": 0.85, "validity": 0.9}}
        ),
        LCT(
            lct_id="agent_high_quality",
            lct_type="agent",
            owning_society_lct="society_1",
            created_at_block=1,
            created_at_tick=1,
            value_axes={"V3": {"veracity": 0.95, "valuation": 0.95, "validity": 0.95}}
        ),
    ]

    atp_costs = {
        "agent_low_quality": 10,
        "agent_medium_quality": 50,
        "agent_high_quality": 100,
    }

    # Test 1: Routine operation (low quality acceptable)
    print("Test 1: Routine Operation (event_logging)")
    try:
        result = select_agent_with_quality(
            operation_type="event_logging",
            agents=agents,
            atp_costs=atp_costs
        )
        print(f"  ✓ Selected: {result.agent_lct}")
        print(f"    Veracity: {result.v3_veracity:.2f}")
        print(f"    ATP Cost: {result.atp_cost:.1f}")
        print(f"    Reason: {result.reason}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    print()

    # Test 2: Critical operation (high quality required)
    print("Test 2: Critical Operation (insurance_claim)")
    try:
        result = select_agent_with_quality(
            operation_type="insurance_claim",
            agents=agents,
            atp_costs=atp_costs
        )
        print(f"  ✓ Selected: {result.agent_lct}")
        print(f"    Veracity: {result.v3_veracity:.2f}")
        print(f"    ATP Cost: {result.atp_cost:.1f}")
        print(f"    Reason: {result.reason}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    print()

    # Test 3: Budget constraint (insufficient ATP)
    print("Test 3: Budget Constraint (insurance_claim, budget=50)")
    try:
        result = select_agent_with_quality(
            operation_type="insurance_claim",
            agents=agents,
            atp_costs=atp_costs,
            atp_budget=50
        )
        print(f"  ✓ Selected: {result.agent_lct}")
        print(f"    ATP Cost: {result.atp_cost:.1f}")
    except InsufficientATPBudgetError as e:
        print(f"  ✓ Expected error: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
    print()

    # Test 4: Quality requirement too high
    print("Test 4: Quality Requirement Too High (min_quality=0.98)")
    try:
        result = select_agent_with_quality(
            operation_type="insurance_claim",
            agents=agents,
            atp_costs=atp_costs,
            min_quality=0.98
        )
        print(f"  ✓ Selected: {result.agent_lct}")
    except InsufficientQualityError as e:
        print(f"  ✓ Expected error: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
    print()

    print("=" * 80)
    print("✓ All tests complete")
    print("=" * 80)


if __name__ == "__main__":
    test_agent_selection()
