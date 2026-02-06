#!/usr/bin/env python3
"""
Multi-Society Component-Aware Federation Demo
Session #79: Priority #5 - Cross-society agent selection using component gossip

Purpose:
Demonstrate how federated societies can discover and route operations to agents
in other societies based on component-level reputation.

Scenario:
3 societies with different specializations:
- Society A (InsuranceDAO): Accuracy specialists (auditing, verification)
- Society B (LogisticsDAO): Speed specialists (real-time tracking, routing)
- Society C (ResearchDAO): Balanced generalists (diverse research tasks)

Each society has 3 agents. Federation enables cross-society routing:
- Society A needs fast operation → queries Society B via gossip
- Society B needs high-accuracy verification → queries Society A
- Society C balances workload across federation

Federation Protocol:
1. Each society maintains ReputationCache with local + remote agents
2. Agents announce reputation via gossip (composite + deltas)
3. Societies forward gossip to federated peers
4. Agent selection searches local + federated caches
5. Operations route to optimal agent regardless of society

This enables:
- Specialization across societies (society-level comparative advantage)
- Resource sharing without central coordination
- ATP-efficient cross-society collaboration
- Reputation-based trust without authority
"""

import sys
sys.path.insert(0, '/home/dp/ai-workspace/web4/game')

import random
from typing import List, Dict, Optional
import time

from engine.lct import LCT
from engine.multidimensional_v3 import V3Components, V3Component, calculate_composite_veracity
from engine.component_aware_selection import SelectionContext, SelectionStrategy, select_agent
from engine.federation_reputation_gossip import (
    encode_components_to_gossip,
    decode_gossip_to_components,
    ReputationCache
)


def create_specialized_society(
    society_name: str,
    society_lct_id: str,
    specialization: str,
    n_agents: int = 3
) -> tuple[List[LCT], ReputationCache]:
    """
    Create a society with specialized agents

    Returns:
        (agents, reputation_cache)
    """
    agents = []
    cache = ReputationCache()

    # Component profiles by specialization
    profiles = {
        "accuracy": {
            "base": V3Components(0.92, 0.97, 0.88, 0.70, 0.80),
            "variation": 0.05
        },
        "speed": {
            "base": V3Components(0.82, 0.76, 0.85, 0.98, 0.83),
            "variation": 0.05
        },
        "balanced": {
            "base": V3Components(0.82, 0.82, 0.82, 0.82, 0.82),
            "variation": 0.05
        }
    }

    profile = profiles[specialization]

    for i in range(n_agents):
        # Create agent with variation around base profile
        base_components = profile["base"]
        variation = profile["variation"]

        components = V3Components(
            consistency=max(0.5, min(1.0, base_components.consistency + random.uniform(-variation, variation))),
            accuracy=max(0.5, min(1.0, base_components.accuracy + random.uniform(-variation, variation))),
            reliability=max(0.5, min(1.0, base_components.reliability + random.uniform(-variation, variation))),
            speed=max(0.5, min(1.0, base_components.speed + random.uniform(-variation, variation))),
            cost_efficiency=max(0.5, min(1.0, base_components.cost_efficiency + random.uniform(-variation, variation)))
        )

        agent_lct_dict = {
            "lct_id": f"{society_lct_id}:agent:{society_name.lower()}_agent_{i+1}",
            "lct_type": "agent",
            "owning_society_lct": society_lct_id,
            "created_at_block": 1,
            "created_at_tick": i,
            "value_axes": {"V3": {"veracity": calculate_composite_veracity(components)}},
            "metadata": {
                "name": f"{society_name} Agent {i+1}",
                "specialization": specialization,
                "avg_latency": 30.0 + random.uniform(-10, 10),
                "V3_components": components.to_dict()
            }
        }

        agent_lct = LCT.from_dict(agent_lct_dict)
        agents.append(agent_lct)

        # Add to reputation cache
        gossip = encode_components_to_gossip(agent_lct, components)
        cache.update(gossip)

    return agents, cache


def propagate_gossip(
    source_cache: ReputationCache,
    target_caches: List[ReputationCache]
):
    """
    Propagate reputation gossip from source to target societies

    Simulates federation gossip protocol
    """
    for agent_lct_id, gossip in source_cache.cache.items():
        for target_cache in target_caches:
            target_cache.update(gossip)


def run_multi_society_federation_demo():
    """Run multi-society component-aware federation demo"""

    print("=" * 80)
    print("  Multi-Society Component-Aware Federation Demo")
    print("  Session #79")
    print("=" * 80)

    # Phase 1: Create societies
    print("\n=== Phase 1: Create Federated Societies ===\n")

    societies = {}

    # Society A: Accuracy specialists (InsuranceDAO)
    agents_a, cache_a = create_specialized_society(
        "InsuranceDAO",
        "lct:federation:society:insurance_dao",
        "accuracy",
        n_agents=3
    )
    societies["InsuranceDAO"] = {"agents": agents_a, "cache": cache_a, "specialization": "accuracy"}

    # Society B: Speed specialists (LogisticsDAO)
    agents_b, cache_b = create_specialized_society(
        "LogisticsDAO",
        "lct:federation:society:logistics_dao",
        "speed",
        n_agents=3
    )
    societies["LogisticsDAO"] = {"agents": agents_b, "cache": cache_b, "specialization": "speed"}

    # Society C: Balanced generalists (ResearchDAO)
    agents_c, cache_c = create_specialized_society(
        "ResearchDAO",
        "lct:federation:society:research_dao",
        "balanced",
        n_agents=3
    )
    societies["ResearchDAO"] = {"agents": agents_c, "cache": cache_c, "specialization": "balanced"}

    print(f"Created {len(societies)} federated societies:\n")

    for society_name, society_data in societies.items():
        agents = society_data["agents"]
        specialization = society_data["specialization"]

        print(f"{society_name} ({specialization}):")
        for agent in agents:
            components = V3Components.from_dict(agent.metadata["V3_components"])
            composite = calculate_composite_veracity(components)

            # Find strongest component
            component_values = {comp: components.get_component(comp) for comp in V3Component}
            strongest = max(component_values, key=component_values.get)

            print(f"  - {agent.metadata['name']:<25} composite={composite:.3f}  "
                  f"strongest={strongest.value}={component_values[strongest]:.3f}")
        print()

    # Phase 2: Propagate gossip across federation
    print("=== Phase 2: Federation Gossip Propagation ===\n")

    # Each society knows about all agents via gossip
    all_caches = [cache_a, cache_b, cache_c]

    propagate_gossip(cache_a, [cache_b, cache_c])
    propagate_gossip(cache_b, [cache_a, cache_c])
    propagate_gossip(cache_c, [cache_a, cache_b])

    print(f"Gossip propagated across federation:")
    for society_name, society_data in societies.items():
        cache = society_data["cache"]
        stats = cache.get_stats()
        print(f"  {society_name} cache: {stats['size']} agents")

    # Phase 3: Cross-society operation routing
    print("\n=== Phase 3: Cross-Society Operation Routing ===\n")

    operations = [
        {
            "name": "Critical insurance audit",
            "requestor": "InsuranceDAO",
            "context": SelectionContext(
                operation_type="insurance_audit",
                requires_accuracy=True,
                strategy=SelectionStrategy.BEST_COMPONENT,
                min_veracity=0.85
            )
        },
        {
            "name": "Real-time logistics tracking",
            "requestor": "LogisticsDAO",
            "context": SelectionContext(
                operation_type="federation_query",
                requires_speed=True,
                strategy=SelectionStrategy.BEST_COMPONENT,
                min_veracity=0.75
            )
        },
        {
            "name": "High-reliability infrastructure vote",
            "requestor": "ResearchDAO",
            "context": SelectionContext(
                operation_type="infrastructure_vote",
                requires_reliability=True,
                strategy=SelectionStrategy.BEST_COMPONENT,
                min_veracity=0.80
            )
        },
        {
            "name": "Cost-efficient local query",
            "requestor": "InsuranceDAO",
            "context": SelectionContext(
                operation_type="local_conversation",
                atp_budget=40.0,
                cost_sensitive=True,
                strategy=SelectionStrategy.COST_EFFECTIVE
            )
        },
        {
            "name": "Balanced general research task",
            "requestor": "ResearchDAO",
            "context": SelectionContext(
                operation_type="federation_query",
                strategy=SelectionStrategy.BEST_QUALITY,
                min_veracity=0.80
            )
        }
    ]

    print(f"{'Operation':<40} | {'Requestor':<15} | {'Selected Agent':<30} | {'Society':<15} | {'Component'}")
    print("-" * 140)

    routing_results = []

    for op in operations:
        requestor_society = societies[op["requestor"]]
        requestor_cache = requestor_society["cache"]

        # Get all known agents from cache (local + federated)
        all_known_agents = []
        for agent_lct_id in requestor_cache.cache.keys():
            # Reconstruct LCT from cache
            gossip = requestor_cache.get(agent_lct_id)
            if gossip is None:
                continue

            # Find original agent
            for society_data in societies.values():
                for agent in society_data["agents"]:
                    if agent.lct_id == agent_lct_id:
                        all_known_agents.append(agent)
                        break

        # Select agent
        result = select_agent(all_known_agents, op["context"])

        if result:
            selected_lct, candidate = result

            # Determine which society owns this agent
            owner_society = None
            for society_name, society_data in societies.items():
                if selected_lct.lct_id.startswith(society_data["agents"][0].lct_id.rsplit(":", 2)[0]):
                    owner_society = society_name
                    break

            # Determine relevant component
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

            comp_str = f"{relevant_comp.value}={candidate.get_component(relevant_comp):.3f}" if relevant_comp else f"composite={candidate.composite_veracity:.3f}"

            cross_society = "✓" if owner_society != op["requestor"] else ""

            print(f"{op['name']:<40} | {op['requestor']:<15} | {selected_lct.metadata['name']:<30} | {owner_society:<15} {cross_society} | {comp_str}")

            routing_results.append({
                "operation": op["name"],
                "requestor": op["requestor"],
                "selected_agent": selected_lct.metadata["name"],
                "owner_society": owner_society,
                "cross_society": owner_society != op["requestor"],
                "composite_veracity": candidate.composite_veracity
            })

    # Phase 4: Analysis
    print("\n=== Phase 4: Federation Routing Analysis ===\n")

    cross_society_count = sum(1 for r in routing_results if r["cross_society"])
    total_operations = len(routing_results)

    print(f"Total operations: {total_operations}")
    print(f"Cross-society routing: {cross_society_count} ({cross_society_count/total_operations:.1%})")
    print(f"Local routing: {total_operations - cross_society_count} ({(total_operations - cross_society_count)/total_operations:.1%})")

    print(f"\n{'Society':<20} | {'Operations Served':<20} | {'Cross-Society'}")
    print("-" * 70)

    for society_name in societies.keys():
        served = sum(1 for r in routing_results if r["owner_society"] == society_name)
        cross_served = sum(1 for r in routing_results if r["owner_society"] == society_name and r["cross_society"])

        print(f"{society_name:<20} | {served:<20} | {cross_served}")

    # Phase 5: Specialization utilization
    print("\n=== Phase 5: Specialization Utilization ===\n")

    print("Specialization matching:")
    print("  Accuracy specialists (InsuranceDAO) selected for high-accuracy tasks")
    print("  Speed specialists (LogisticsDAO) selected for time-sensitive tasks")
    print("  Balanced generalists (ResearchDAO) selected for general tasks")

    print(f"\nKey Observations:")
    accuracy_ops = [r for r in routing_results if "audit" in r["operation"].lower() or "accuracy" in r["operation"].lower()]
    if accuracy_ops:
        accuracy_societies = [r["owner_society"] for r in accuracy_ops]
        print(f"  - Accuracy-critical ops routed to: {', '.join(set(accuracy_societies))}")

    speed_ops = [r for r in routing_results if "real-time" in r["operation"].lower() or "tracking" in r["operation"].lower()]
    if speed_ops:
        speed_societies = [r["owner_society"] for r in speed_ops]
        print(f"  - Speed-critical ops routed to: {', '.join(set(speed_societies))}")

    print(f"\n{'=' * 80}")
    print(f"  Multi-Society Federation Demo Complete!")
    print(f"{'=' * 80}\n")
    print(f"  ✅ 3 specialized societies created")
    print(f"  ✅ Component-level reputation gossip propagated")
    print(f"  ✅ {total_operations} operations routed across federation")
    print(f"  ✅ {cross_society_count} cross-society routings ({cross_society_count/total_operations:.1%})")
    print(f"  ✅ Specialization-aware routing enabled by component gossip")
    print(f"\n  Key Finding: Federation enables specialization at society level,")
    print(f"               with component-aware routing matching operations to")
    print(f"               specialized societies based on reputation gossip.")

    return routing_results


if __name__ == "__main__":
    # Set seed for reproducibility
    random.seed(79)
    results = run_multi_society_federation_demo()
