#!/usr/bin/env python3
"""
Governance Stress Test — Metabolic Dynamics Under Sustained Load
================================================================

Simulates 200+ actions across a team to observe:
1. ATP oscillation patterns (depletion → recovery cycles)
2. Metabolic state transition dynamics
3. Recharge equilibrium point
4. Multi-sig queuing under load
5. Policy enforcement consistency
6. Heartbeat block accumulation rates
7. Denial rate vs ATP headroom

This is the first empirical test of the self-regulating governance stack.

Date: 2026-02-20
"""

import sys
import os
import json
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hardbound_cli import (
    HardboundTeam, TeamRole, TeamPolicy, TeamHeartbeat,
    TeamLedger, HARDBOUND_DIR, detect_tpm2,
)
from web4_entity import R6Decision


def run_stress_test(num_actions: int = 200, team_atp: float = 500.0,
                    use_tpm: bool = False):
    """
    Run a sustained load test on the governance stack.

    Simulates a realistic workload: mixed action types, multiple actors,
    policy changes mid-run, multi-sig requests under pressure.
    """
    print("=" * 70)
    print("  GOVERNANCE STRESS TEST")
    print(f"  Actions: {num_actions} | Team ATP: {team_atp} | TPM2: {use_tpm}")
    print("=" * 70)

    # Clean up
    test_dir = HARDBOUND_DIR / "teams" / "stress-test"
    if test_dir.exists():
        shutil.rmtree(test_dir)

    # Create team with constrained ATP to force metabolic dynamics
    team = HardboundTeam("stress-test", use_tpm=use_tpm, team_atp=team_atp)
    team.create()

    # Add diverse members
    members = [
        ("analyst-1", "ai", TeamRole.AGENT),
        ("analyst-2", "ai", TeamRole.AGENT),
        ("deployer", "service", TeamRole.OPERATOR),
        ("security-bot", "ai", TeamRole.AGENT),
        ("infra-ops", "human", TeamRole.OPERATOR),
    ]
    for name, mtype, role in members:
        team.add_member(name, mtype, role=role)

    admin = f"{team.name}-admin"

    # Define action workload (weighted by frequency)
    agent_actions = [
        ("run_analysis", 8),      # 8x weight — most common
        ("review_pr", 6),
        ("validate_schema", 5),
        ("run_diagnostics", 4),
        ("analyze_dataset", 3),
        ("execute_review", 2),
    ]
    operator_actions = [
        ("deploy_staging", 4),
        ("scale_service", 3),
        ("update_config", 3),
        ("restart_service", 2),
    ]
    admin_actions = [
        ("approve_deployment", 2),
        ("set_resource_limit", 1),
    ]

    # Flatten weighted lists
    agent_pool = []
    for action, weight in agent_actions:
        agent_pool.extend([action] * weight)
    operator_pool = []
    for action, weight in operator_actions:
        operator_pool.extend([action] * weight)
    admin_pool = []
    for action, weight in admin_actions:
        admin_pool.extend([action] * weight)

    # Tracking metrics
    metrics = {
        "atp_timeline": [],
        "state_transitions": [],
        "decisions": {"approved": 0, "denied": 0, "pending_multi_sig": 0},
        "denial_reasons": {},
        "actions_by_actor": {},
        "recharge_events": [],
        "heartbeat_blocks": 0,
        "policy_changes": 0,
    }

    # Simulate actions
    import random
    random.seed(42)  # Reproducible

    print(f"\n  Running {num_actions} actions...")
    print(f"  {'#':>4s}  {'Actor':20s}  {'Action':22s}  {'Decision':12s}  "
          f"{'ATP':>8s}  {'State':8s}")
    print(f"  {'─' * 85}")

    # Simulate time by backdating the heartbeat timer relative to NOW
    # (heartbeat.seconds_since_last() uses datetime.now(), so we must
    # set last_heartbeat to a past time relative to the real clock)
    from datetime import timedelta
    cumulative_sim_seconds = 0.0

    for i in range(num_actions):
        # Simulate 15-90 seconds passing between actions
        time_step = random.uniform(15.0, 90.0)
        cumulative_sim_seconds += time_step

        # Set heartbeat's last_heartbeat far enough in the past
        # to trigger recharge based on the simulated interval
        simulated_elapsed = random.uniform(
            team.heartbeat.interval * 0.5,
            team.heartbeat.interval * 2.0
        )
        team.heartbeat.last_heartbeat = (
            datetime.now(timezone.utc) - timedelta(seconds=simulated_elapsed)
        )

        # Choose actor and action based on role distribution
        # 60% agent, 25% operator, 15% admin
        roll = random.random()
        if roll < 0.60:
            actor = random.choice(["analyst-1", "analyst-2", "security-bot"])
            action = random.choice(agent_pool)
        elif roll < 0.85:
            actor = random.choice(["deployer", "infra-ops"])
            action = random.choice(operator_pool)
        else:
            actor = admin
            action = random.choice(admin_pool)

        # Policy change at 25%, 50%, 75%
        if i == num_actions // 4:
            result = team.update_policy(admin, {
                "set_action_costs": {"run_analysis": 3.0, "review_pr": 3.0},
            })
            metrics["policy_changes"] += 1
            print(f"\n  >>> Policy v{result['policy_version']}: "
                  f"reduced agent costs to 3.0 ATP <<<\n")

        if i == num_actions // 2:
            result = team.update_policy(admin, {
                "remove_operator_min": ["restart_service"],
                "set_action_costs": {"deploy_staging": 15.0},
            })
            metrics["policy_changes"] += 1
            print(f"\n  >>> Policy v{result['policy_version']}: "
                  f"opened restart_service, reduced deploy cost <<<\n")

        if i == 3 * num_actions // 4:
            result = team.update_policy(admin, {
                "set_action_costs": {"run_analysis": 2.0, "review_pr": 2.0,
                                     "validate_schema": 2.0},
                "set_custom_rule": {"name": "austerity_mode", "value": "true"},
            })
            metrics["policy_changes"] += 1
            print(f"\n  >>> Policy v{result['policy_version']}: "
                  f"austerity mode — all agent costs to 2.0 ATP <<<\n")

        # Execute action
        record = team.sign_action(actor, action)
        decision = record.get("decision", "unknown")

        # Track metrics
        atp_ratio = team.team_atp / team.team_atp_max if team.team_atp_max > 0 else 0
        metrics["atp_timeline"].append({
            "step": i,
            "atp": round(team.team_atp, 2),
            "ratio": round(atp_ratio, 3),
            "state": team.heartbeat.state,
            "decision": decision,
        })

        if "metabolic_transition" in record:
            metrics["state_transitions"].append({
                "step": i,
                "transition": record["metabolic_transition"],
            })

        if decision in metrics["decisions"]:
            metrics["decisions"][decision] += 1
        else:
            metrics["decisions"][decision] = 1

        if decision == "denied":
            reason = record.get("reason", "unknown")[:40]
            metrics["denial_reasons"][reason] = metrics["denial_reasons"].get(reason, 0) + 1

        if "pre_action_recharge" in record:
            metrics["recharge_events"].append({
                "step": i,
                "recharged": record["pre_action_recharge"]["recharged"],
                "state": record["pre_action_recharge"]["metabolic_state"],
            })

        actor_stats = metrics["actions_by_actor"]
        if actor not in actor_stats:
            actor_stats[actor] = {"total": 0, "approved": 0, "denied": 0, "atp_spent": 0.0}
        actor_stats[actor]["total"] += 1
        if decision == "approved":
            actor_stats[actor]["approved"] += 1
            actor_stats[actor]["atp_spent"] += record.get("atp_cost", 0.0)
        elif decision == "denied":
            actor_stats[actor]["denied"] += 1

        # Print every 10th action + all denials + all transitions
        show = (i % 10 == 0) or decision != "approved" or "metabolic_transition" in record
        if show:
            state = team.heartbeat.state
            marker = "  " if decision == "approved" else "!!" if decision == "denied" else ">>"
            print(f"{marker}{i:4d}  {actor:20s}  {action:22s}  {decision:12s}  "
                  f"{team.team_atp:8.1f}  {state:8s}")

    # Final flush
    team.flush()

    # Analysis
    print(f"\n{'=' * 70}")
    print("  RESULTS")
    print(f"{'=' * 70}")

    print(f"\n  Total actions: {num_actions}")
    print(f"  Approved: {metrics['decisions'].get('approved', 0)}")
    print(f"  Denied: {metrics['decisions'].get('denied', 0)}")
    print(f"  Pending multi-sig: {metrics['decisions'].get('pending_multi_sig', 0)}")
    approval_rate = (metrics['decisions'].get('approved', 0) / num_actions * 100
                     if num_actions > 0 else 0)
    print(f"  Approval rate: {approval_rate:.1f}%")

    print(f"\n  Policy changes: {metrics['policy_changes']}")
    print(f"  State transitions: {len(metrics['state_transitions'])}")
    print(f"  Recharge events: {len(metrics['recharge_events'])}")

    # ATP dynamics
    atp_values = [p["atp"] for p in metrics["atp_timeline"]]
    if atp_values:
        print(f"\n  ATP Dynamics:")
        print(f"    Start: {atp_values[0]:.1f}")
        print(f"    End: {atp_values[-1]:.1f}")
        print(f"    Min: {min(atp_values):.1f}")
        print(f"    Max: {max(atp_values):.1f}")
        print(f"    Mean: {sum(atp_values)/len(atp_values):.1f}")

        # Find equilibrium (average of last 25% of readings)
        quarter = len(atp_values) // 4
        tail_avg = sum(atp_values[-quarter:]) / quarter if quarter > 0 else 0
        print(f"    Tail avg (last 25%): {tail_avg:.1f}")

    # State distribution
    states = [p["state"] for p in metrics["atp_timeline"]]
    state_counts = {}
    for s in states:
        state_counts[s] = state_counts.get(s, 0) + 1
    print(f"\n  Metabolic State Distribution:")
    for state, count in sorted(state_counts.items(), key=lambda x: -x[1]):
        pct = count / len(states) * 100
        bar = "█" * int(pct / 2)
        print(f"    {state:8s} {count:4d} ({pct:5.1f}%) {bar}")

    # State transitions
    if metrics["state_transitions"]:
        print(f"\n  State Transitions ({len(metrics['state_transitions'])}):")
        for t in metrics["state_transitions"][:10]:
            trans = t["transition"]
            print(f"    Step {t['step']:3d}: {trans['from']} → {trans['to']} "
                  f"({trans.get('interval_change', 'n/a')})")
        if len(metrics["state_transitions"]) > 10:
            print(f"    ... ({len(metrics['state_transitions']) - 10} more)")

    # Denial analysis
    if metrics["denial_reasons"]:
        print(f"\n  Denial Reasons:")
        for reason, count in sorted(metrics["denial_reasons"].items(), key=lambda x: -x[1]):
            print(f"    [{count:3d}x] {reason}")

    # Per-actor breakdown
    print(f"\n  Per-Actor Breakdown:")
    print(f"    {'Actor':20s} {'Total':>6s} {'OK':>5s} {'Deny':>5s} {'Rate':>7s} {'ATP':>8s}")
    for actor, stats in sorted(metrics["actions_by_actor"].items()):
        rate = stats["approved"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"    {actor:20s} {stats['total']:6d} {stats['approved']:5d} "
              f"{stats['denied']:5d} {rate:6.1f}% {stats['atp_spent']:8.1f}")

    # Recharge analysis
    if metrics["recharge_events"]:
        total_recharged = sum(r["recharged"] for r in metrics["recharge_events"])
        print(f"\n  Recharge Analysis:")
        print(f"    Events: {len(metrics['recharge_events'])}")
        print(f"    Total recharged: {total_recharged:.1f} ATP")
        print(f"    Total discharged: {team.team_adp_discharged:.1f} ATP")
        net = total_recharged - team.team_adp_discharged
        print(f"    Net flow: {net:+.1f} ATP")
        print(f"    Sustainability: {'SELF-SUSTAINING' if net >= 0 else 'DEPLETING'}")

    # Ledger stats
    print(f"\n  Ledger:")
    verification = team.ledger.verify()
    print(f"    Entries: {verification['entries']}")
    print(f"    Chain valid: {verification['valid']}")
    print(f"    HW-signed: {verification['hw_signed']}")
    print(f"    Head hash: {verification.get('head_hash', 'n/a')[:16]}...")

    # Final team info
    info = team.info()
    print(f"\n  Final Team State:")
    print(f"    ATP: {info['team_atp']['balance']:.1f}/{info['team_atp']['max']:.1f}")
    print(f"    Discharged: {info['team_atp']['discharged']:.1f}")
    print(f"    Recharged: {info['team_atp']['recharged']:.1f}")
    print(f"    Net flow: {info['team_atp']['net_flow']:.1f}")
    print(f"    Heartbeat: {info['heartbeat']['state']} "
          f"({info['heartbeat']['interval_seconds']}s)")
    print(f"    Policy: v{info['policy']['version']}")

    # Generate ASCII ATP chart
    print(f"\n  ATP Timeline (sparkline):")
    chart_width = 70
    if atp_values:
        max_atp = max(atp_values)
        min_atp = min(atp_values)
        atp_range = max_atp - min_atp if max_atp != min_atp else 1
        # Sample down to chart_width points
        step = max(1, len(atp_values) // chart_width)
        sampled = atp_values[::step][:chart_width]

        # Create sparkline with block chars
        chars = " ▁▂▃▄▅▆▇█"
        line = ""
        for v in sampled:
            normalized = (v - min_atp) / atp_range
            idx = min(len(chars) - 1, int(normalized * (len(chars) - 1)))
            line += chars[idx]
        print(f"    {max_atp:6.0f} ┤{line}")
        print(f"    {min_atp:6.0f} ┤{'─' * len(line)}")
        print(f"           ╰{'─' * len(line)}╮")
        print(f"            0{' ' * (len(line) - 4)}{num_actions}")

    print(f"\n{'=' * 70}")
    print(f"  Governance stress test complete. The system {'SURVIVED' if verification['valid'] else 'FAILED'}.")
    print(f"{'=' * 70}")

    # Save metrics
    metrics_file = test_dir / "stress_test_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n  Metrics saved to: {metrics_file}")

    return metrics


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Governance Stress Test")
    parser.add_argument("--actions", type=int, default=200,
                        help="Number of actions to simulate")
    parser.add_argument("--atp", type=float, default=500.0,
                        help="Initial team ATP pool")
    parser.add_argument("--tpm", action="store_true",
                        help="Use real TPM2 hardware")
    args = parser.parse_args()

    run_stress_test(num_actions=args.actions, team_atp=args.atp,
                    use_tpm=args.tpm)
