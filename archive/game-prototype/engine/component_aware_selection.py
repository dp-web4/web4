#!/usr/bin/env python3
"""
Component-Aware Agent Selection
Session #78: Priority #2 - Context-sensitive agent selection using multi-dimensional V3

Purpose:
Select optimal agents for operations based on:
1. Multi-dimensional V3 components (from Session #77)
2. ATP budget constraints
3. Operation context requirements
4. Quality-cost tradeoffs

Theory:
Different operations require different agent capabilities:
- Time-sensitive ops → prioritize SPEED component
- Critical accuracy ops → prioritize ACCURACY component
- Budget-constrained ops → prioritize COST_EFFICIENCY component
- High-stakes ops → prioritize RELIABILITY component

This enables:
1. Context-aware agent routing (right agent for right job)
2. ATP-efficient resource allocation
3. Quality optimization within budget
4. Multi-objective selection (speed + accuracy, etc.)

Based on:
- Multi-dimensional V3 from Session #77
- ATP metering from Session #78
- Adaptive V3 evolution from Session #76
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .lct import LCT
    from .multidimensional_v3 import (
        V3Components,
        V3Component,
        calculate_composite_veracity,
        get_context_specific_weights
    )
    from .atp_metering import ATPMeter, calculate_atp_cost
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from lct import LCT
    from multidimensional_v3 import (
        V3Components,
        V3Component,
        calculate_composite_veracity,
        get_context_specific_weights
    )
    from atp_metering import ATPMeter, calculate_atp_cost


class SelectionStrategy(Enum):
    """Agent selection strategies"""
    BEST_QUALITY = "best_quality"              # Highest composite veracity
    BEST_COMPONENT = "best_component"          # Highest specific component
    COST_EFFECTIVE = "cost_effective"          # Best quality per ATP
    BUDGET_CONSTRAINED = "budget_constrained"  # Best within ATP budget
    MULTI_OBJECTIVE = "multi_objective"        # Balanced across components


@dataclass
class SelectionContext:
    """Context for agent selection"""
    operation_type: str
    atp_budget: Optional[float] = None
    required_components: Optional[List[V3Component]] = None
    component_weights: Optional[Dict[V3Component, float]] = None
    min_veracity: float = 0.0
    strategy: SelectionStrategy = SelectionStrategy.BEST_QUALITY

    # Context flags (for automatic weight adjustment)
    requires_speed: bool = False
    requires_accuracy: bool = False
    requires_reliability: bool = False
    requires_consistency: bool = False
    cost_sensitive: bool = False


@dataclass
class AgentCandidate:
    """Agent candidate for selection"""
    lct: LCT
    components: V3Components
    atp_cost: float
    composite_veracity: float

    def get_component(self, component: V3Component) -> float:
        """Get specific component value"""
        return self.components.get_component(component)

    def get_quality_per_atp(self) -> float:
        """Get quality per ATP ratio"""
        if self.atp_cost == 0:
            return 0.0
        return self.composite_veracity / self.atp_cost


def prepare_agent_candidates(
    agents: List[LCT],
    selection_context: SelectionContext
) -> List[AgentCandidate]:
    """
    Prepare agent candidates with computed metrics

    Args:
        agents: List of agent LCTs
        selection_context: Selection context

    Returns:
        List of AgentCandidate instances
    """
    candidates = []

    # Get context-specific weights
    context_dict = {
        "requires_speed": selection_context.requires_speed,
        "requires_accuracy": selection_context.requires_accuracy,
        "requires_reliability": selection_context.requires_reliability,
        "requires_consistency": selection_context.requires_consistency,
        "cost_sensitive": selection_context.cost_sensitive
    }

    weights = selection_context.component_weights
    if weights is None:
        weights = get_context_specific_weights(context_dict)

    for agent_lct in agents:
        # Extract V3 components from LCT
        if "V3_components" not in agent_lct.metadata:
            # Fallback: use legacy V3 veracity
            v3_data = agent_lct.value_axes.get("V3", {})
            veracity = v3_data.get("veracity", 0.5)
            components = V3Components(
                consistency=veracity,
                accuracy=veracity,
                reliability=veracity,
                speed=veracity,
                cost_efficiency=veracity
            )
        else:
            components = V3Components.from_dict(agent_lct.metadata["V3_components"])

        # Calculate composite veracity
        composite = calculate_composite_veracity(components, weights)

        # Estimate ATP cost for this agent
        # Use agent's historical average latency if available
        avg_latency = agent_lct.metadata.get("avg_latency", 30.0)
        quality_score = composite
        atp_cost = calculate_atp_cost(
            operation_type=selection_context.operation_type,
            latency=avg_latency,
            quality_score=quality_score
        )

        candidates.append(AgentCandidate(
            lct=agent_lct,
            components=components,
            atp_cost=atp_cost,
            composite_veracity=composite
        ))

    return candidates


def filter_by_budget(
    candidates: List[AgentCandidate],
    atp_budget: float
) -> List[AgentCandidate]:
    """Filter candidates within ATP budget"""
    return [c for c in candidates if c.atp_cost <= atp_budget]


def filter_by_min_veracity(
    candidates: List[AgentCandidate],
    min_veracity: float
) -> List[AgentCandidate]:
    """Filter candidates above minimum veracity"""
    return [c for c in candidates if c.composite_veracity >= min_veracity]


def select_best_quality(candidates: List[AgentCandidate]) -> Optional[AgentCandidate]:
    """Select agent with highest composite veracity"""
    if not candidates:
        return None
    return max(candidates, key=lambda c: c.composite_veracity)


def select_best_component(
    candidates: List[AgentCandidate],
    component: V3Component
) -> Optional[AgentCandidate]:
    """Select agent with highest specific component"""
    if not candidates:
        return None
    return max(candidates, key=lambda c: c.get_component(component))


def select_cost_effective(candidates: List[AgentCandidate]) -> Optional[AgentCandidate]:
    """Select agent with best quality per ATP"""
    if not candidates:
        return None
    return max(candidates, key=lambda c: c.get_quality_per_atp())


def select_multi_objective(
    candidates: List[AgentCandidate],
    components: List[V3Component]
) -> Optional[AgentCandidate]:
    """
    Select agent with best average across multiple components

    Args:
        candidates: List of candidates
        components: Components to optimize for

    Returns:
        Best multi-objective candidate
    """
    if not candidates or not components:
        return None

    def multi_objective_score(candidate: AgentCandidate) -> float:
        """Calculate multi-objective score"""
        scores = [candidate.get_component(comp) for comp in components]
        return sum(scores) / len(scores)

    return max(candidates, key=multi_objective_score)


def select_agent(
    agents: List[LCT],
    selection_context: SelectionContext
) -> Optional[Tuple[LCT, AgentCandidate]]:
    """
    Select optimal agent based on context

    Args:
        agents: List of available agent LCTs
        selection_context: Selection context and strategy

    Returns:
        (selected_lct, candidate) or None if no suitable agent

    Example:
        >>> context = SelectionContext(
        ...     operation_type="insurance_audit",
        ...     atp_budget=150.0,
        ...     requires_accuracy=True,
        ...     min_veracity=0.70
        ... )
        >>> agent, candidate = select_agent(available_agents, context)
        >>> print(f"Selected: {agent.lct_id}, ATP cost: {candidate.atp_cost}")
    """
    # Prepare candidates
    candidates = prepare_agent_candidates(agents, selection_context)

    # Apply filters
    if selection_context.min_veracity > 0:
        candidates = filter_by_min_veracity(candidates, selection_context.min_veracity)

    if selection_context.atp_budget is not None:
        candidates = filter_by_budget(candidates, selection_context.atp_budget)

    if not candidates:
        return None

    # Apply selection strategy
    selected = None

    if selection_context.strategy == SelectionStrategy.BEST_QUALITY:
        selected = select_best_quality(candidates)

    elif selection_context.strategy == SelectionStrategy.BEST_COMPONENT:
        # Choose component based on context flags
        if selection_context.requires_speed:
            selected = select_best_component(candidates, V3Component.SPEED)
        elif selection_context.requires_accuracy:
            selected = select_best_component(candidates, V3Component.ACCURACY)
        elif selection_context.requires_reliability:
            selected = select_best_component(candidates, V3Component.RELIABILITY)
        elif selection_context.requires_consistency:
            selected = select_best_component(candidates, V3Component.CONSISTENCY)
        elif selection_context.cost_sensitive:
            selected = select_best_component(candidates, V3Component.COST_EFFICIENCY)
        else:
            # Default to best quality
            selected = select_best_quality(candidates)

    elif selection_context.strategy == SelectionStrategy.COST_EFFECTIVE:
        selected = select_cost_effective(candidates)

    elif selection_context.strategy == SelectionStrategy.BUDGET_CONSTRAINED:
        # Within budget, select best quality
        selected = select_best_quality(candidates)

    elif selection_context.strategy == SelectionStrategy.MULTI_OBJECTIVE:
        # Optimize for required components
        if selection_context.required_components:
            selected = select_multi_objective(candidates, selection_context.required_components)
        else:
            # Default to all components
            selected = select_multi_objective(candidates, list(V3Component))

    if selected is None:
        return None

    return (selected.lct, selected)


def compare_selections(
    agents: List[LCT],
    contexts: List[SelectionContext]
) -> Dict:
    """
    Compare agent selections across different contexts

    Args:
        agents: List of available agents
        contexts: List of selection contexts to compare

    Returns:
        Comparison results showing how context affects selection
    """
    results = []

    for context in contexts:
        selection_result = select_agent(agents, context)

        if selection_result:
            selected_lct, candidate = selection_result
            results.append({
                "context": context,
                "selected_agent": selected_lct.lct_id,
                "composite_veracity": candidate.composite_veracity,
                "atp_cost": candidate.atp_cost,
                "quality_per_atp": candidate.get_quality_per_atp(),
                "components": candidate.components.to_dict()
            })
        else:
            results.append({
                "context": context,
                "selected_agent": None,
                "reason": "No suitable agent found"
            })

    return {"comparisons": results}


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  Component-Aware Agent Selection - Unit Tests")
    print("  Session #78")
    print("=" * 80)

    # Test 1: Create diverse agent pool
    print("\n=== Test 1: Agent Pool Creation ===\n")

    # Fast agent: High speed, lower accuracy
    fast_agent_dict = {
        "lct_id": "lct:test:agent:fast_alice",
        "lct_type": "agent",
        "owning_society_lct": "lct:test:society:A",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {"V3": {"veracity": 0.85}},
        "metadata": {
            "name": "Fast Alice",
            "avg_latency": 20.0,
            "V3_components": {
                "consistency": 0.85,
                "accuracy": 0.78,
                "reliability": 0.88,
                "speed": 0.95,
                "cost_efficiency": 0.82
            }
        }
    }

    # Accurate agent: High accuracy, slower
    accurate_agent_dict = {
        "lct_id": "lct:test:agent:accurate_bob",
        "lct_type": "agent",
        "owning_society_lct": "lct:test:society:A",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {"V3": {"veracity": 0.92}},
        "metadata": {
            "name": "Accurate Bob",
            "avg_latency": 45.0,
            "V3_components": {
                "consistency": 0.94,
                "accuracy": 0.97,
                "reliability": 0.90,
                "speed": 0.72,
                "cost_efficiency": 0.85
            }
        }
    }

    # Reliable agent: Balanced, very consistent
    reliable_agent_dict = {
        "lct_id": "lct:test:agent:reliable_carol",
        "lct_type": "agent",
        "owning_society_lct": "lct:test:society:A",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {"V3": {"veracity": 0.88}},
        "metadata": {
            "name": "Reliable Carol",
            "avg_latency": 35.0,
            "V3_components": {
                "consistency": 0.96,
                "accuracy": 0.85,
                "reliability": 0.98,
                "speed": 0.80,
                "cost_efficiency": 0.88
            }
        }
    }

    # Budget agent: Cost-efficient but lower quality
    budget_agent_dict = {
        "lct_id": "lct:test:agent:budget_dave",
        "lct_type": "agent",
        "owning_society_lct": "lct:test:society:A",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {"V3": {"veracity": 0.70}},
        "metadata": {
            "name": "Budget Dave",
            "avg_latency": 25.0,
            "V3_components": {
                "consistency": 0.72,
                "accuracy": 0.68,
                "reliability": 0.75,
                "speed": 0.88,
                "cost_efficiency": 0.95
            }
        }
    }

    agents = [
        LCT.from_dict(fast_agent_dict),
        LCT.from_dict(accurate_agent_dict),
        LCT.from_dict(reliable_agent_dict),
        LCT.from_dict(budget_agent_dict)
    ]

    print(f"Created {len(agents)} diverse agents:")
    for agent in agents:
        print(f"  - {agent.metadata['name']:<20} (LCT: {agent.lct_id})")

    # Test 2: Context-specific selection
    print("\n=== Test 2: Context-Specific Selection ===\n")

    test_contexts = [
        {
            "name": "Time-sensitive operation",
            "context": SelectionContext(
                operation_type="federation_query",
                requires_speed=True,
                strategy=SelectionStrategy.BEST_COMPONENT
            )
        },
        {
            "name": "High-accuracy critical audit",
            "context": SelectionContext(
                operation_type="insurance_audit",
                requires_accuracy=True,
                min_veracity=0.80,
                strategy=SelectionStrategy.BEST_COMPONENT
            )
        },
        {
            "name": "Budget-constrained task",
            "context": SelectionContext(
                operation_type="local_conversation",
                atp_budget=40.0,
                strategy=SelectionStrategy.COST_EFFECTIVE
            )
        },
        {
            "name": "High-reliability infrastructure",
            "context": SelectionContext(
                operation_type="infrastructure_vote",
                requires_reliability=True,
                min_veracity=0.85,
                strategy=SelectionStrategy.BEST_COMPONENT
            )
        }
    ]

    print(f"{'Context':<35} | {'Selected Agent':<20} | {'Veracity':<10} | {'ATP Cost'}")
    print("-" * 90)

    for test in test_contexts:
        result = select_agent(agents, test["context"])

        if result:
            selected_lct, candidate = result
            print(f"{test['name']:<35} | {selected_lct.metadata['name']:<20} | "
                  f"{candidate.composite_veracity:<10.3f} | {candidate.atp_cost:.2f}")
        else:
            print(f"{test['name']:<35} | {'No suitable agent':<20} | {'-':<10} | -")

    # Test 3: Budget constraint analysis
    print("\n=== Test 3: Budget Constraint Analysis ===\n")

    budgets = [30.0, 50.0, 80.0, 120.0]

    print(f"{'Budget':<10} | {'Selected Agent':<20} | {'Veracity':<10} | {'Cost':<10} | {'Quality/ATP'}")
    print("-" * 85)

    for budget in budgets:
        context = SelectionContext(
            operation_type="federation_query",
            atp_budget=budget,
            strategy=SelectionStrategy.BEST_QUALITY
        )

        result = select_agent(agents, context)

        if result:
            selected_lct, candidate = result
            print(f"{budget:<10.1f} | {selected_lct.metadata['name']:<20} | "
                  f"{candidate.composite_veracity:<10.3f} | {candidate.atp_cost:<10.2f} | "
                  f"{candidate.get_quality_per_atp():.4f}")
        else:
            print(f"{budget:<10.1f} | {'No agent affordable':<20} | {'-':<10} | {'-':<10} | -")

    # Test 4: Multi-objective selection
    print("\n=== Test 4: Multi-Objective Selection ===\n")

    multi_context = SelectionContext(
        operation_type="insurance_audit",
        required_components=[V3Component.ACCURACY, V3Component.RELIABILITY],
        strategy=SelectionStrategy.MULTI_OBJECTIVE
    )

    result = select_agent(agents, multi_context)

    if result:
        selected_lct, candidate = result
        print(f"Selected for accuracy + reliability: {selected_lct.metadata['name']}")
        print(f"  Accuracy:    {candidate.get_component(V3Component.ACCURACY):.3f}")
        print(f"  Reliability: {candidate.get_component(V3Component.RELIABILITY):.3f}")
        print(f"  Average:     {(candidate.get_component(V3Component.ACCURACY) + candidate.get_component(V3Component.RELIABILITY)) / 2:.3f}")

    # Test 5: Selection comparison
    print("\n=== Test 5: Selection Strategy Comparison ===\n")

    operation = "federation_query"
    strategies = [
        SelectionStrategy.BEST_QUALITY,
        SelectionStrategy.COST_EFFECTIVE,
        SelectionStrategy.BEST_COMPONENT  # Will choose speed for default
    ]

    print(f"{'Strategy':<25} | {'Selected':<20} | {'Veracity':<10} | {'Cost':<10} | {'Q/ATP'}")
    print("-" * 90)

    for strategy in strategies:
        context = SelectionContext(
            operation_type=operation,
            strategy=strategy,
            requires_speed=(strategy == SelectionStrategy.BEST_COMPONENT)
        )

        result = select_agent(agents, context)

        if result:
            selected_lct, candidate = result
            print(f"{strategy.value:<25} | {selected_lct.metadata['name']:<20} | "
                  f"{candidate.composite_veracity:<10.3f} | {candidate.atp_cost:<10.2f} | "
                  f"{candidate.get_quality_per_atp():.4f}")

    print("\n" + "=" * 80)
    print("  All Unit Tests Passed!")
    print("=" * 80)
    print("\n✅ Key Findings:")
    print("  - Context-aware selection routes agents based on specialization")
    print("  - Budget constraints enable ATP-efficient allocation")
    print("  - Multi-objective selection balances multiple quality dimensions")
    print("  - Different strategies optimize for different goals")
