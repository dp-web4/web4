#!/usr/bin/env python3
"""
Web4 Game Simulation Scale Test
Session #69 Track 2: Performance testing with 20 agents, 50 ticks

Goals:
1. Validate system stability at scale
2. Measure performance metrics (time/tick, ATP/event, DB queries)
3. Identify bottlenecks (context edges, event processing, etc.)
4. Test multi-agent fraud scenarios

Scenario:
- 2 societies with 10 agents each
- 3 agent profiles: honest (50%), greedy (30%), adversarial (20%)
- 50-tick simulation (realistic session length)
- SAGE monitors both societies
- Insurance pool with multiple contributors
"""

import sys
import time
sys.path.insert(0, '/home/dp/ai-workspace/web4/game')

from engine.models import World, Agent, Society
from engine.sim_loop import tick_world
from engine.roles import bind_role
from engine.treasury import treasury_spend, treasury_deposit
from engine.policy import apply_simple_policies
from engine.society_trust import update_society_trust
from engine.db_bridge import create_bridge
from engine.insurance import InsurancePool, insure_society

SAGE_LCT = "lct:sage:legion:1763906585"

def generate_agents(society_lct, count=10):
    """Generate agents with different behavioral profiles"""
    agents = []

    profiles = [
        # Honest agents (50%)
        *[{'behavior': 'honest', 'temperament': 0.85 + i*0.02} for i in range(5)],
        # Greedy agents (30%)
        *[{'behavior': 'greedy', 'temperament': 0.35 + i*0.05} for i in range(3)],
        # Adversarial agents (20%)
        *[{'behavior': 'adversarial', 'temperament': 0.15 + i*0.05} for i in range(2)]
    ]

    for i, profile in enumerate(profiles[:count]):
        agent_lct = f"lct:agent:{society_lct.split(':')[-1]}:{i:02d}"
        agent = Agent(
            agent_lct=agent_lct,
            name=f"Agent-{i:02d} ({profile['behavior']})",
            trust_axes={
                "T3": {
                    "talent": 0.7 + (i % 3) * 0.1,
                    "training": 0.6 + (i % 4) * 0.1,
                    "temperament": profile['temperament'],
                    "composite": (0.7 + 0.6 + profile['temperament']) / 3
                }
            },
            capabilities={"witness_general": 0.5 + (i % 5) * 0.1},
            resources={"ATP": 50.0 + i * 10},
            memberships=[society_lct]
        )
        agent.behavior_profile = profile['behavior']
        agents.append(agent)

    return agents

def agent_action(world, agent, society, tick):
    """
    Agent performs action based on behavior profile

    Honest: Deposits ATP occasionally
    Greedy: Attempts treasury withdrawals
    Adversarial: Attempts fraudulent withdrawals
    """
    if not hasattr(agent, 'behavior_profile'):
        return

    # Action frequency based on behavior
    if agent.behavior_profile == 'honest':
        if tick % 10 == agent.agent_lct.__hash__() % 10:  # Every ~10 ticks, staggered
            amount = 20.0
            if agent.resources.get("ATP", 0) >= amount:
                treasury_deposit(
                    world=world,
                    society=society,
                    treasury_lct=f"{society.society_lct}:treasury",
                    source_lct=agent.agent_lct,
                    amount=amount,
                    reason="cooperative contribution"
                )
                agent.resources["ATP"] -= amount

    elif agent.behavior_profile == 'greedy':
        if tick % 7 == agent.agent_lct.__hash__() % 7:  # Every ~7 ticks
            amount = 50.0
            treasury_spend(
                world=world,
                society=society,
                treasury_lct=f"{society.society_lct}:treasury",
                initiator_lct=agent.agent_lct,
                amount=amount,
                reason="questionable allocation for project work"
            )

    elif agent.behavior_profile == 'adversarial':
        if tick % 5 == agent.agent_lct.__hash__() % 5:  # Every ~5 ticks
            amount = 100.0
            treasury_spend(
                world=world,
                society=society,
                treasury_lct=f"{society.society_lct}:treasury",
                initiator_lct=agent.agent_lct,
                amount=amount,
                reason="suspicious self-allocation for personal use"
            )

def main():
    print("="*80)
    print("  Web4 Scale Test")
    print("  Session #69 Track 2")
    print("  Configuration: 2 societies, 20 agents, 50 ticks")
    print("="*80)

    start_time = time.time()

    # Setup
    bridge = create_bridge()
    insurance_pool = InsurancePool()
    world = World()

    # Society A
    society_a = Society(
        society_lct="lct:society:scale-a",
        name="Scale Society A",
        treasury={"ATP": 3000},
        block_interval_seconds=5
    )
    world.add_society(society_a)

    # Society B
    society_b = Society(
        society_lct="lct:society:scale-b",
        name="Scale Society B",
        treasury={"ATP": 2500},
        block_interval_seconds=5
    )
    world.add_society(society_b)

    # Generate agents
    print("\n=== Generating Agents ===")
    agents_a = generate_agents(society_a.society_lct, count=10)
    agents_b = generate_agents(society_b.society_lct, count=10)

    # SAGE
    sage = Agent(
        agent_lct=SAGE_LCT,
        name="SAGE",
        trust_axes={"T3": {"talent": 0.7, "training": 0.8, "temperament": 0.95, "composite": 0.82}},
        capabilities={"witness_general": 0.9, "fraud_detection": 0.85},
        resources={"ATP": 500.0},
        memberships=[society_a.society_lct, society_b.society_lct]
    )

    all_agents = [sage] + agents_a + agents_b

    for agent in all_agents:
        world.add_agent(agent)

    print(f"  Total agents: {len(all_agents)}")
    print(f"    SAGE: 1")
    print(f"    Society A: {len(agents_a)} (5 honest, 3 greedy, 2 adversarial)")
    print(f"    Society B: {len(agents_b)} (5 honest, 3 greedy, 2 adversarial)")

    # Bind SAGE as auditor in both societies
    print("\n=== Binding SAGE as Auditor ===")
    bind_role(world=world, society=society_a, role_name="auditor", subject_lct=SAGE_LCT, reason="SAGE monitoring")
    bind_role(world=world, society=society_b, role_name="auditor", subject_lct=SAGE_LCT, reason="SAGE monitoring")
    print(f"  SAGE → Auditor (Society A)")
    print(f"  SAGE → Auditor (Society B)")

    # Purchase insurance for both societies
    print("\n=== Purchasing Insurance ===")
    policy_a = insure_society(world, society_a, insurance_pool, premium_rate=0.05, coverage_ratio=0.8)
    policy_b = insure_society(world, society_b, insurance_pool, premium_rate=0.05, coverage_ratio=0.8)
    print(f"  Society A: {policy_a['premium_paid']:.0f} ATP premium, {policy_a['max_payout']:.0f} ATP max payout")
    print(f"  Society B: {policy_b['premium_paid']:.0f} ATP premium, {policy_b['max_payout']:.0f} ATP max payout")
    print(f"  Insurance pool: {insurance_pool.get_balance():.0f} ATP")

    # Simulation loop
    print(f"\n{'='*80}")
    print(f"  Running Simulation (50 ticks)")
    print(f"{'='*80}")

    metrics = {
        'ticks': 0,
        'events_total': 0,
        'events_per_tick': [],
        'blocks_sealed': 0,
        'frauds_detected': 0,
        'context_edges': 0
    }

    tick_times = []

    for tick in range(50):
        tick_start = time.time()

        # Agent actions
        for agent in agents_a:
            agent_action(world, agent, society_a, tick)
        for agent in agents_b:
            agent_action(world, agent, society_b, tick)

        # Tick world
        tick_world(world)

        # Apply policies
        apply_simple_policies(world, society_a)
        apply_simple_policies(world, society_b)
        update_society_trust(world, society_a)
        update_society_trust(world, society_b)

        # Metrics
        events_this_tick = len(society_a.pending_events) + len(society_b.pending_events)
        metrics['events_per_tick'].append(events_this_tick)
        metrics['events_total'] += events_this_tick
        metrics['blocks_sealed'] = len(society_a.blocks) + len(society_b.blocks)
        metrics['context_edges'] = len(world.context_edges)

        tick_elapsed = time.time() - tick_start
        tick_times.append(tick_elapsed)

        # Progress every 10 ticks
        if (tick + 1) % 10 == 0:
            print(f"  Tick {tick+1:2d}: {events_this_tick} events, {len(world.context_edges)} edges, {tick_elapsed*1000:.1f}ms")

    # Final statistics
    simulation_elapsed = time.time() - start_time

    print(f"\n{'='*80}")
    print(f"  Simulation Complete")
    print(f"{'='*80}")

    print(f"\n  Performance Metrics:")
    print(f"    Total time: {simulation_elapsed:.2f}s")
    print(f"    Avg time/tick: {simulation_elapsed/50*1000:.1f}ms")
    print(f"    Max time/tick: {max(tick_times)*1000:.1f}ms")
    print(f"    Min time/tick: {min(tick_times)*1000:.1f}ms")

    print(f"\n  Event Metrics:")
    print(f"    Total events: {metrics['events_total']}")
    print(f"    Avg events/tick: {metrics['events_total']/50:.1f}")
    print(f"    Max events/tick: {max(metrics['events_per_tick'])}")
    print(f"    Blocks sealed: {metrics['blocks_sealed']}")

    print(f"\n  System State:")
    print(f"    Total agents: {len(world.agents)}")
    print(f"    Context edges: {len(world.context_edges)}")
    print(f"    Societies: {len(world.societies)}")

    print(f"\n  Treasury State:")
    print(f"    Society A: {society_a.treasury['ATP']:.0f} ATP")
    print(f"    Society B: {society_b.treasury['ATP']:.0f} ATP")

    print(f"\n  Insurance Pool:")
    stats = insurance_pool.get_stats()
    print(f"    Balance: {stats['balance']:.0f} ATP")
    print(f"    Premiums: {stats['total_premiums']:.0f} ATP")
    print(f"    Payouts: {stats['total_payouts']:.0f} ATP")

    # Bottleneck Analysis
    print(f"\n{'='*80}")
    print(f"  Bottleneck Analysis")
    print(f"{'='*80}")

    avg_tick_time = sum(tick_times) / len(tick_times)
    print(f"\n  Average tick time: {avg_tick_time*1000:.2f}ms")

    if avg_tick_time < 0.050:  # < 50ms
        print(f"  ✅ EXCELLENT: System scales well at 20 agents")
    elif avg_tick_time < 0.100:  # < 100ms
        print(f"  ✅ GOOD: Acceptable performance at scale")
    else:
        print(f"  ⚠️  SLOW: May need optimization")

    print(f"\n  Context edge growth:")
    print(f"    Final count: {len(world.context_edges)}")
    print(f"    Growth rate: {len(world.context_edges)/50:.1f} edges/tick")

    if len(world.context_edges) > 10000:
        print(f"    ⚠️  Consider indexing for large edge counts")
    else:
        print(f"    ✅ Edge count manageable")

    print(f"\n{'='*80}")
    print(f"  Scale Test Complete!")
    print(f"{'='*80}")

    print(f"\n  ✅ System stable at 20 agents, 50 ticks")
    print(f"  ✅ Performance: {avg_tick_time*1000:.1f}ms/tick average")
    print(f"  ✅ Total events processed: {metrics['events_total']}")
    print(f"  ✅ No crashes or errors")

    bridge.close()

if __name__ == "__main__":
    main()
