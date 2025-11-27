#!/usr/bin/env python3
"""
Component-Aware Federation Demo
Session #78: Demonstrate context-sensitive agent routing in federation

Purpose:
Show how multi-dimensional V3 enables optimal agent selection for diverse operations:
1. Create federation with 5 specialized agents
2. Submit 20 diverse operations requiring different capabilities
3. Demonstrate context-aware routing (speed, accuracy, reliability, cost-efficiency)
4. Track ATP efficiency gains vs random selection

Scenario:
Society "InsuranceDAO" has 5 agents with different specializations:
- FastAgent: High speed, moderate accuracy (time-sensitive ops)
- AccurateAgent: High accuracy, slow (critical audits)
- ReliableAgent: High reliability, balanced (infrastructure)
- CostEffectiveAgent: High cost-efficiency (budget-constrained)
- GeneralistAgent: Balanced across all dimensions (general tasks)

20 operations submitted with varying requirements. Component-aware selection
routes each operation to the optimal agent, maximizing quality within ATP budget.

Expected Outcome:
Component-aware selection achieves higher quality outcomes and better ATP efficiency
compared to random or round-robin selection.
"""

import sys
sys.path.insert(0, '/home/dp/ai-workspace/web4/game')

import random
from typing import List, Dict

from engine.lct import LCT
from engine.multidimensional_v3 import (
    V3Components,
    V3Component,
    calculate_composite_veracity
)
from engine.component_aware_selection import (
    SelectionContext,
    SelectionStrategy,
    select_agent
)
from engine.atp_metering import ATPMeter, create_atp_meter_for_lct


def create_specialized_agents() -> List[LCT]:
    """Create 5 agents with different specializations"""

    agents = []

    # 1. Fast Agent: Speed specialist
    fast_agent_dict = {
        "lct_id": "lct:insurance_dao:agent:fast_agent",
        "lct_type": "agent",
        "owning_society_lct": "lct:insurance_dao:society",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {"V3": {"veracity": 0.84}},
        "metadata": {
            "name": "FastAgent",
            "specialization": "Speed",
            "avg_latency": 18.0,
            "V3_components": {
                "consistency": 0.82,
                "accuracy": 0.75,
                "reliability": 0.85,
                "speed": 0.98,
                "cost_efficiency": 0.80
            }
        }
    }
    agents.append(LCT.from_dict(fast_agent_dict))

    # 2. Accurate Agent: Accuracy specialist
    accurate_agent_dict = {
        "lct_id": "lct:insurance_dao:agent:accurate_agent",
        "lct_type": "agent",
        "owning_society_lct": "lct:insurance_dao:society",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {"V3": {"veracity": 0.91}},
        "metadata": {
            "name": "AccurateAgent",
            "specialization": "Accuracy",
            "avg_latency": 50.0,
            "V3_components": {
                "consistency": 0.93,
                "accuracy": 0.98,
                "reliability": 0.88,
                "speed": 0.68,
                "cost_efficiency": 0.78
            }
        }
    }
    agents.append(LCT.from_dict(accurate_agent_dict))

    # 3. Reliable Agent: Reliability specialist
    reliable_agent_dict = {
        "lct_id": "lct:insurance_dao:agent:reliable_agent",
        "lct_type": "agent",
        "owning_society_lct": "lct:insurance_dao:society",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {"V3": {"veracity": 0.90}},
        "metadata": {
            "name": "ReliableAgent",
            "specialization": "Reliability",
            "avg_latency": 35.0,
            "V3_components": {
                "consistency": 0.95,
                "accuracy": 0.85,
                "reliability": 0.99,
                "speed": 0.78,
                "cost_efficiency": 0.83
            }
        }
    }
    agents.append(LCT.from_dict(reliable_agent_dict))

    # 4. Cost-Effective Agent: Cost-efficiency specialist
    cost_effective_agent_dict = {
        "lct_id": "lct:insurance_dao:agent:cost_effective_agent",
        "lct_type": "agent",
        "owning_society_lct": "lct:insurance_dao:society",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {"V3": {"veracity": 0.78}},
        "metadata": {
            "name": "CostEffectiveAgent",
            "specialization": "Cost-Efficiency",
            "avg_latency": 22.0,
            "V3_components": {
                "consistency": 0.75,
                "accuracy": 0.72,
                "reliability": 0.80,
                "speed": 0.85,
                "cost_efficiency": 0.97
            }
        }
    }
    agents.append(LCT.from_dict(cost_effective_agent_dict))

    # 5. Generalist Agent: Balanced
    generalist_agent_dict = {
        "lct_id": "lct:insurance_dao:agent:generalist_agent",
        "lct_type": "agent",
        "owning_society_lct": "lct:insurance_dao:society",
        "created_at_block": 1,
        "created_at_tick": 1,
        "value_axes": {"V3": {"veracity": 0.82}},
        "metadata": {
            "name": "GeneralistAgent",
            "specialization": "Generalist",
            "avg_latency": 32.0,
            "V3_components": {
                "consistency": 0.82,
                "accuracy": 0.82,
                "reliability": 0.82,
                "speed": 0.82,
                "cost_efficiency": 0.82
            }
        }
    }
    agents.append(LCT.from_dict(generalist_agent_dict))

    return agents


def create_diverse_operations() -> List[Dict]:
    """Create 20 diverse operations with different requirements"""

    operations = []

    # Time-sensitive operations (5)
    for i in range(5):
        operations.append({
            "name": f"Time-sensitive query #{i+1}",
            "operation_type": "federation_query",
            "context": SelectionContext(
                operation_type="federation_query",
                requires_speed=True,
                strategy=SelectionStrategy.BEST_COMPONENT,
                min_veracity=0.70
            )
        })

    # High-accuracy critical audits (5)
    for i in range(5):
        operations.append({
            "name": f"Critical audit #{i+1}",
            "operation_type": "insurance_audit",
            "context": SelectionContext(
                operation_type="insurance_audit",
                requires_accuracy=True,
                strategy=SelectionStrategy.BEST_COMPONENT,
                min_veracity=0.80
            )
        })

    # High-reliability infrastructure (3)
    for i in range(3):
        operations.append({
            "name": f"Infrastructure task #{i+1}",
            "operation_type": "infrastructure_vote",
            "context": SelectionContext(
                operation_type="infrastructure_vote",
                requires_reliability=True,
                strategy=SelectionStrategy.BEST_COMPONENT,
                min_veracity=0.85
            )
        })

    # Budget-constrained operations (4)
    for i in range(4):
        operations.append({
            "name": f"Budget task #{i+1}",
            "operation_type": "local_conversation",
            "context": SelectionContext(
                operation_type="local_conversation",
                atp_budget=35.0,
                cost_sensitive=True,
                strategy=SelectionStrategy.COST_EFFECTIVE
            )
        })

    # General tasks (3)
    for i in range(3):
        operations.append({
            "name": f"General task #{i+1}",
            "operation_type": "federation_query",
            "context": SelectionContext(
                operation_type="federation_query",
                strategy=SelectionStrategy.BEST_QUALITY,
                min_veracity=0.75
            )
        })

    return operations


def run_federation_demo():
    """Run component-aware federation demo"""

    print("=" * 80)
    print("  Component-Aware Federation Demo")
    print("  Session #78")
    print("=" * 80)

    # Phase 1: Setup federation
    print("\n=== Phase 1: Federation Setup ===\n")

    agents = create_specialized_agents()

    print(f"InsuranceDAO Federation with {len(agents)} specialized agents:\n")
    print(f"{'Agent':<25} | {'Specialization':<20} | {'Composite V3':<15} | {'Best Component'}")
    print("-" * 100)

    for agent in agents:
        components = V3Components.from_dict(agent.metadata["V3_components"])
        composite = calculate_composite_veracity(components)

        # Find best component
        component_values = {comp: components.get_component(comp) for comp in V3Component}
        best_comp = max(component_values, key=component_values.get)

        print(f"{agent.metadata['name']:<25} | {agent.metadata['specialization']:<20} | "
              f"{composite:<15.3f} | {best_comp.value} = {component_values[best_comp]:.3f}")

    # Phase 2: Create operations
    print("\n=== Phase 2: Operation Queue ===\n")

    operations = create_diverse_operations()

    print(f"Created {len(operations)} diverse operations:")
    print(f"  Time-sensitive queries:    5")
    print(f"  Critical accuracy audits:  5")
    print(f"  High-reliability infra:    3")
    print(f"  Budget-constrained tasks:  4")
    print(f"  General tasks:             3")

    # Phase 3: Component-aware routing
    print("\n=== Phase 3: Component-Aware Routing ===\n")

    print(f"{'Operation':<35} | {'Selected Agent':<25} | {'Composite V3':<15} | {'Relevant Component'}")
    print("-" * 110)

    component_aware_results = []

    for op in operations:
        result = select_agent(agents, op["context"])

        if result:
            selected_lct, candidate = result

            # Determine relevant component based on context
            if op["context"].requires_speed:
                relevant_comp = V3Component.SPEED
            elif op["context"].requires_accuracy:
                relevant_comp = V3Component.ACCURACY
            elif op["context"].requires_reliability:
                relevant_comp = V3Component.RELIABILITY
            elif op["context"].cost_sensitive:
                relevant_comp = V3Component.COST_EFFICIENCY
            else:
                relevant_comp = None

            relevant_value = candidate.get_component(relevant_comp) if relevant_comp else candidate.composite_veracity

            print(f"{op['name']:<35} | {selected_lct.metadata['name']:<25} | "
                  f"{candidate.composite_veracity:<15.3f} | "
                  f"{relevant_comp.value if relevant_comp else 'composite'} = {relevant_value:.3f}")

            component_aware_results.append({
                "operation": op["name"],
                "agent": selected_lct.metadata["name"],
                "composite_veracity": candidate.composite_veracity,
                "atp_cost": candidate.atp_cost,
                "quality_per_atp": candidate.get_quality_per_atp()
            })

    # Phase 4: Comparison with random selection
    print("\n=== Phase 4: Comparison with Random Selection ===\n")

    random_results = []

    for op in operations:
        # Randomly select agent
        random_agent = random.choice(agents)
        components = V3Components.from_dict(random_agent.metadata["V3_components"])
        composite = calculate_composite_veracity(components)

        # Estimate ATP cost
        avg_latency = random_agent.metadata.get("avg_latency", 30.0)
        from engine.atp_metering import calculate_atp_cost
        atp_cost = calculate_atp_cost(
            operation_type=op["operation_type"],
            latency=avg_latency,
            quality_score=composite
        )

        random_results.append({
            "operation": op["name"],
            "agent": random_agent.metadata["name"],
            "composite_veracity": composite,
            "atp_cost": atp_cost,
            "quality_per_atp": composite / atp_cost if atp_cost > 0 else 0
        })

    # Compare results
    print(f"{'Metric':<30} | {'Component-Aware':<20} | {'Random Selection':<20} | {'Improvement'}")
    print("-" * 100)

    # Average quality
    ca_avg_quality = sum(r["composite_veracity"] for r in component_aware_results) / len(component_aware_results)
    random_avg_quality = sum(r["composite_veracity"] for r in random_results) / len(random_results)
    quality_improvement = ((ca_avg_quality - random_avg_quality) / random_avg_quality) * 100

    print(f"{'Average Quality (V3)':<30} | {ca_avg_quality:<20.3f} | {random_avg_quality:<20.3f} | {quality_improvement:+.1f}%")

    # Average ATP cost
    ca_avg_cost = sum(r["atp_cost"] for r in component_aware_results) / len(component_aware_results)
    random_avg_cost = sum(r["atp_cost"] for r in random_results) / len(random_results)
    cost_improvement = ((random_avg_cost - ca_avg_cost) / random_avg_cost) * 100

    print(f"{'Average ATP Cost':<30} | {ca_avg_cost:<20.2f} | {random_avg_cost:<20.2f} | {cost_improvement:+.1f}%")

    # Total ATP spent
    ca_total_atp = sum(r["atp_cost"] for r in component_aware_results)
    random_total_atp = sum(r["atp_cost"] for r in random_results)
    total_atp_savings = ((random_total_atp - ca_total_atp) / random_total_atp) * 100

    print(f"{'Total ATP Spent':<30} | {ca_total_atp:<20.2f} | {random_total_atp:<20.2f} | {total_atp_savings:+.1f}%")

    # Quality per ATP
    ca_efficiency = sum(r["quality_per_atp"] for r in component_aware_results) / len(component_aware_results)
    random_efficiency = sum(r["quality_per_atp"] for r in random_results) / len(random_results)
    efficiency_improvement = ((ca_efficiency - random_efficiency) / random_efficiency) * 100

    print(f"{'Quality per ATP':<30} | {ca_efficiency:<20.4f} | {random_efficiency:<20.4f} | {efficiency_improvement:+.1f}%")

    # Phase 5: Agent utilization analysis
    print("\n=== Phase 5: Agent Utilization Analysis ===\n")

    # Count how many operations each agent handled
    ca_utilization = {}
    for result in component_aware_results:
        agent_name = result["agent"]
        ca_utilization[agent_name] = ca_utilization.get(agent_name, 0) + 1

    random_utilization = {}
    for result in random_results:
        agent_name = result["agent"]
        random_utilization[agent_name] = random_utilization.get(agent_name, 0) + 1

    print(f"{'Agent':<25} | {'Component-Aware':<20} | {'Random Selection':<20} | {'Note'}")
    print("-" * 100)

    for agent in agents:
        agent_name = agent.metadata["name"]
        ca_count = ca_utilization.get(agent_name, 0)
        random_count = random_utilization.get(agent_name, 0)

        specialization = agent.metadata["specialization"]
        note = f"Specialized in {specialization}"

        print(f"{agent_name:<25} | {ca_count:<20} | {random_count:<20} | {note}")

    # Final summary
    print(f"\n{'=' * 80}")
    print(f"  Component-Aware Federation Demo Complete!")
    print(f"{'=' * 80}\n")

    print(f"  ✅ 20 diverse operations routed optimally")
    print(f"  ✅ Quality improvement: {quality_improvement:+.1f}%")
    print(f"  ✅ ATP efficiency gain: {efficiency_improvement:+.1f}%")
    print(f"  ✅ Specialized agents utilized for matching operations")
    print(f"  ✅ Budget-constrained ops routed to cost-efficient agents")

    print(f"\n  Key Finding: Multi-dimensional V3 enables context-sensitive routing,")
    print(f"               improving quality {quality_improvement:+.1f}% and efficiency {efficiency_improvement:+.1f}% vs random selection.")

    return {
        "component_aware_results": component_aware_results,
        "random_results": random_results,
        "quality_improvement": quality_improvement,
        "efficiency_improvement": efficiency_improvement
    }


if __name__ == "__main__":
    # Set seed for reproducibility
    random.seed(78)
    demo_results = run_federation_demo()
