#!/usr/bin/env python3
"""
Edge Case Discovery: Find Interesting Web4 Narratives

This script systematically explores parameter space to discover edge cases
that reveal Web4's behavior under stress, enabling richer human narratives.

Philosophy:
- Surprise is prize: Unexpected outcomes reveal system truth
- Extremes teach: Edge cases demonstrate boundaries
- Failure informs: Collapsed societies show what's necessary
- Drama engages: Humans learn best from conflict and resolution
"""

import sys
import json
from pathlib import Path
from dataclasses import asdict

# Import playground simulation (lightweight, fast)
sys.path.insert(0, str(Path(__file__).parent))
from playground_simulation import run_playground_simulation, PlaygroundConfig


def detect_interesting_events(result) -> dict:
    """
    Analyze simulation result for interesting patterns.

    Returns dict with:
    - is_interesting: bool
    - reasons: list[str]
    - metrics: dict
    """

    lives = result.lives
    if not lives:
        return {"is_interesting": False, "reasons": [], "metrics": {}}

    interesting = False
    reasons = []

    # Calculate metrics
    total_lives = len(lives)
    deaths = sum(1 for life in lives if life.termination_reason not in ["completed", "none"])
    atp_deaths = sum(1 for life in lives if life.termination_reason == "atp_exhausted")

    # Trust trajectory
    first_life = lives[0]
    last_life = lives[-1]
    initial_trust = first_life.initial_trust
    final_trust = last_life.final_trust
    trust_delta = final_trust - initial_trust

    # ATP trajectory
    initial_atp = first_life.initial_atp
    final_atp = last_life.final_atp

    # Extreme trust growth (>40%)
    if trust_delta > 0.4:
        interesting = True
        reasons.append(f"Extreme trust growth: {initial_trust:.2f} → {final_trust:.2f} (+{trust_delta*100:.0f}%)")

    # Extreme trust collapse (>40%)
    if trust_delta < -0.4:
        interesting = True
        reasons.append(f"Extreme trust collapse: {initial_trust:.2f} → {final_trust:.2f} ({trust_delta*100:.0f}%)")

    # All ATP deaths (metabolic failure pattern)
    if atp_deaths == deaths and deaths > 0:
        interesting = True
        reasons.append(f"Pure metabolic failure: All {deaths} deaths from ATP exhaustion")

    # Survived entire simulation
    if last_life.termination_reason == "completed":
        if total_lives >= 3:
            interesting = True
            reasons.append(f"Marathon survivor: Lived {total_lives} complete lives without death")

    # Quick death (first life < 5 ticks)
    first_life_duration = len(first_life.atp_history) - 1
    if first_life_duration < 5 and first_life.termination_reason != "completed":
        interesting = True
        reasons.append(f"Instant death: First life lasted only {first_life_duration} ticks")

    # Trust threshold crossing (consciousness emergence at 0.5)
    crossed_threshold = False
    for life in lives:
        for i in range(1, len(life.trust_history)):
            if life.trust_history[i-1] < 0.5 and life.trust_history[i] >= 0.5:
                crossed_threshold = True
                break
        if crossed_threshold:
            break

    if crossed_threshold:
        interesting = True
        reasons.append("Consciousness threshold crossed: Trust reached 0.5 (coherence emergence)")

    # ATP windfall (gained 50+ in single tick)
    for life in lives:
        if len(life.atp_history) >= 2:
            max_gain = max(life.atp_history[i] - life.atp_history[i-1] for i in range(1, len(life.atp_history)))
            if max_gain >= 40:
                interesting = True
                reasons.append(f"ATP windfall: Gained {max_gain:.0f} ATP in single tick")
                break

    # ATP crisis recovery (dropped to <10 but recovered to >50)
    for life in lives:
        hit_crisis = any(atp < 10 for atp in life.atp_history)
        if hit_crisis:
            max_recovery = max(life.atp_history) if life.atp_history else 0
            if max_recovery > 50:
                interesting = True
                reasons.append(f"Crisis recovery: ATP dropped to <10 but recovered to {max_recovery:.0f}")
                break

    # High volatility (trust standard deviation > 0.15)
    all_trust_values = []
    for life in lives:
        all_trust_values.extend(life.trust_history)

    if all_trust_values:
        mean_trust = sum(all_trust_values) / len(all_trust_values)
        variance = sum((t - mean_trust) ** 2 for t in all_trust_values) / len(all_trust_values)
        std_dev = variance ** 0.5
        if std_dev > 0.15:
            interesting = True
            reasons.append(f"High trust volatility: std dev = {std_dev:.3f} (unstable behavior)")

    # Perfect stability (trust never changes by more than 0.01)
    max_trust_change = 0
    for life in lives:
        for i in range(1, len(life.trust_history)):
            change = abs(life.trust_history[i] - life.trust_history[i-1])
            max_trust_change = max(max_trust_change, change)

    if max_trust_change < 0.01 and len(lives) > 1:
        interesting = True
        reasons.append(f"Perfect stability: Trust never changed by more than 0.01")

    metrics = {
        "total_lives": total_lives,
        "deaths": deaths,
        "atp_deaths": atp_deaths,
        "initial_trust": initial_trust,
        "final_trust": final_trust,
        "trust_delta": trust_delta,
        "initial_atp": initial_atp,
        "final_atp": final_atp,
    }

    return {
        "is_interesting": interesting,
        "reasons": reasons,
        "metrics": metrics
    }


def run_edge_case_experiments():
    """
    Run systematic parameter sweeps to discover edge cases.
    """

    print("=" * 80)
    print("Edge Case Discovery: Exploring Web4 Parameter Space")
    print("=" * 80)
    print()

    experiments = [
        # 1. ATP Scarcity (rewards barely cover costs)
        {
            "name": "ATP Scarcity",
            "description": "Rewards barely exceed costs - survival is hard",
            "config": PlaygroundConfig(
                num_lives=5,
                ticks_per_life=40,
                initial_atp=50.0,
                action_cost_low=5.0,
                action_cost_medium=12.0,
                action_cost_high=25.0,
                action_reward_low=6.0,  # Only 1 ATP profit
                action_reward_medium=14.0,  # Only 2 ATP profit
                action_reward_high=28.0,  # Only 3 ATP profit
                trust_gain_good=0.02,
                trust_loss_bad=0.05,
            )
        },

        # 2. ATP Abundance (everything is cheap and rewarding)
        {
            "name": "ATP Abundance",
            "description": "Actions are cheap, rewards are high - easy mode",
            "config": PlaygroundConfig(
                num_lives=5,
                ticks_per_life=40,
                initial_atp=200.0,
                action_cost_low=2.0,
                action_cost_medium=5.0,
                action_cost_high=10.0,
                action_reward_low=20.0,
                action_reward_medium=50.0,
                action_reward_high=100.0,
                trust_gain_good=0.08,
                trust_loss_bad=0.02,
            )
        },

        # 3. Trust Fragility (hard to build, easy to lose)
        {
            "name": "Trust Fragility",
            "description": "Trust loss is 10x trust gain - one mistake ruins everything",
            "config": PlaygroundConfig(
                num_lives=5,
                ticks_per_life=40,
                initial_atp=100.0,
                initial_trust=0.6,  # Start higher so we can see collapse
                action_cost_low=5.0,
                action_cost_medium=15.0,
                action_cost_high=30.0,
                action_reward_low=8.0,
                action_reward_medium=20.0,
                action_reward_high=45.0,
                trust_gain_good=0.01,  # Slow growth
                trust_loss_bad=0.10,  # Rapid collapse
            )
        },

        # 4. Trust Stability (nearly impossible to lose)
        {
            "name": "Trust Stability",
            "description": "Trust grows fast, decays slow - forgiving environment",
            "config": PlaygroundConfig(
                num_lives=5,
                ticks_per_life=40,
                initial_atp=100.0,
                action_cost_low=5.0,
                action_cost_medium=15.0,
                action_cost_high=30.0,
                action_reward_low=8.0,
                action_reward_medium=20.0,
                action_reward_high=45.0,
                trust_gain_good=0.12,  # Fast growth
                trust_loss_bad=0.01,  # Minimal decay
            )
        },

        # 5. Karma Compression (huge rebirth advantages)
        {
            "name": "Karma Compression",
            "description": "High-trust rebirths get massive ATP bonuses - compounding advantage",
            "config": PlaygroundConfig(
                num_lives=5,
                ticks_per_life=40,
                initial_atp=50.0,
                action_cost_low=5.0,
                action_cost_medium=15.0,
                action_cost_high=30.0,
                action_reward_low=8.0,
                action_reward_medium=20.0,
                action_reward_high=45.0,
                trust_gain_good=0.05,
                trust_loss_bad=0.05,
                karma_atp_bonus=100.0,  # Huge karma bonus
                karma_trust_boost=0.15,
            )
        },

        # 6. Karma Negligible (rebirth advantage is tiny)
        {
            "name": "Karma Negligible",
            "description": "Karma barely matters - every life is a fresh start",
            "config": PlaygroundConfig(
                num_lives=5,
                ticks_per_life=40,
                initial_atp=100.0,
                action_cost_low=5.0,
                action_cost_medium=15.0,
                action_cost_high=30.0,
                action_reward_low=8.0,
                action_reward_medium=20.0,
                action_reward_high=45.0,
                trust_gain_good=0.05,
                trust_loss_bad=0.05,
                karma_atp_bonus=5.0,  # Tiny karma bonus
                karma_trust_boost=0.01,
            )
        },

        # 7. Short Lives (quick death cycles)
        {
            "name": "Short Lives",
            "description": "Maximum 10 ticks per life - rapid death/rebirth cycling",
            "config": PlaygroundConfig(
                num_lives=8,
                ticks_per_life=10,  # Very short
                initial_atp=80.0,
                action_cost_low=5.0,
                action_cost_medium=15.0,
                action_cost_high=30.0,
                action_reward_low=8.0,
                action_reward_medium=20.0,
                action_reward_high=45.0,
                trust_gain_good=0.05,
                trust_loss_bad=0.05,
            )
        },

        # 8. Long Lives (marathon survival)
        {
            "name": "Long Lives",
            "description": "Maximum 100 ticks per life - test long-term sustainability",
            "config": PlaygroundConfig(
                num_lives=2,
                ticks_per_life=100,  # Very long
                initial_atp=100.0,
                action_cost_low=5.0,
                action_cost_medium=15.0,
                action_cost_high=30.0,
                action_reward_low=8.0,
                action_reward_medium=20.0,
                action_reward_high=45.0,
                trust_gain_good=0.05,
                trust_loss_bad=0.05,
            )
        },

        # 9. Extreme Cost Asymmetry (high-reward actions extremely expensive)
        {
            "name": "Extreme Cost Asymmetry",
            "description": "High-reward actions cost 50 ATP - huge risk/reward imbalance",
            "config": PlaygroundConfig(
                num_lives=5,
                ticks_per_life=40,
                initial_atp=100.0,
                action_cost_low=2.0,
                action_cost_medium=10.0,
                action_cost_high=50.0,  # Extremely expensive
                action_reward_low=5.0,
                action_reward_medium=15.0,
                action_reward_high=60.0,  # High reward but risky
                trust_gain_good=0.05,
                trust_loss_bad=0.05,
            )
        },

        # 10. Trust Death Threshold (high bar for survival)
        {
            "name": "High Trust Death Threshold",
            "description": "Need trust > 0.4 to survive - high performance requirement",
            "config": PlaygroundConfig(
                num_lives=5,
                ticks_per_life=40,
                initial_atp=100.0,
                initial_trust=0.5,
                action_cost_low=5.0,
                action_cost_medium=15.0,
                action_cost_high=30.0,
                action_reward_low=8.0,
                action_reward_medium=20.0,
                action_reward_high=45.0,
                trust_gain_good=0.05,
                trust_loss_bad=0.05,
                trust_threshold_death=0.4,  # High bar
            )
        },
    ]

    interesting_results = []

    for i, experiment in enumerate(experiments, 1):
        print(f"[{i}/{len(experiments)}] Running: {experiment['name']}")
        print(f"  {experiment['description']}")

        try:
            result = run_playground_simulation(experiment["config"])

            # Analyze for interesting patterns
            analysis = detect_interesting_events(result)

            if analysis["is_interesting"]:
                print(f"  ✨ INTERESTING! Reasons:")
                for reason in analysis["reasons"]:
                    print(f"     - {reason}")

                interesting_results.append({
                    "experiment": experiment["name"],
                    "description": experiment["description"],
                    "config": asdict(experiment["config"]),
                    "result": {
                        "lives": [
                            {
                                "life_id": life.life_id,
                                "start_tick": life.start_tick,
                                "end_tick": life.end_tick,
                                "initial_atp": life.initial_atp,
                                "initial_trust": life.initial_trust,
                                "final_atp": life.final_atp,
                                "final_trust": life.final_trust,
                                "termination_reason": life.termination_reason,
                                "atp_history": life.atp_history,
                                "trust_history": life.trust_history,
                                "actions": [asdict(action) for action in life.actions],
                            }
                            for life in result.lives
                        ],
                        "insights": result.insights,
                    },
                    "analysis": analysis
                })
            else:
                print(f"  ⚪ Standard outcome")

            print(f"  Metrics: Lives={analysis['metrics']['total_lives']}, "
                  f"Trust: {analysis['metrics']['initial_trust']:.2f}→{analysis['metrics']['final_trust']:.2f}, "
                  f"Deaths={analysis['metrics']['deaths']}")
            print()

        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()

    # Save interesting results
    if interesting_results:
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / "edge_case_discoveries.json"
        with open(output_file, "w") as f:
            json.dump(interesting_results, f, indent=2)

        print("=" * 80)
        print(f"✅ Discovery complete! Found {len(interesting_results)} interesting edge cases")
        print(f"📁 Results saved to: {output_file}")
        print("=" * 80)
        print()
        print("Interesting scenarios found:")
        for result in interesting_results:
            print(f"\n  • {result['experiment']}: {result['description']}")
            for reason in result['analysis']['reasons'][:2]:
                print(f"    → {reason}")
    else:
        print("=" * 80)
        print("⚪ No particularly interesting edge cases discovered")
        print("   (All simulations produced expected outcomes)")
        print("=" * 80)


if __name__ == "__main__":
    run_edge_case_experiments()
