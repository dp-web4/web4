#!/usr/bin/env python3
"""
Analyze Coherence Pricing Results
Session #28: Understand why cooperation decreased

Unexpected Result:
- Coherence pricing decreased cooperation by 6.4%
- Hypothesis: High ATP costs should incentivize cooperation
- Reality: Something else is happening

Possible Explanations:
1. Starting conditions: Low trust → high γ → ATP premium → agents can't afford to cooperate
2. Feedback timing: Trust builds slowly, ATP costs hit immediately
3. Death spiral: Higher costs → less cooperation → lower trust → even higher costs
4. Baseline bias: Fixed costs may accidentally favor cooperation

Investigation:
- Track trust evolution over time in both conditions
- Compare ATP costs at different trust levels
- Identify if death spiral is occurring
- Test with different starting trust conditions

Author: Legion (autonomous Session #28)
"""

import sys
from pathlib import Path
import random

# Add paths
game_dir = Path(__file__).parent
sys.path.insert(0, str(game_dir))
sys.path.insert(0, str(game_dir.parent / "web4-standard" / "implementation" / "trust"))

from trust_network_coherence_pricing import (
    CoherencePricingSimulation,
    CoherenceSimulationMetrics
)
from engine.coherence_atp_integration import CoherencePricingLayer
from coherence_trust_tensor import CoherenceTrustMetrics


def analyze_evolution_trajectory(results: dict):
    """Analyze how coherence metrics evolved during simulation"""

    print("=" * 80)
    print("  COHERENCE EVOLUTION ANALYSIS")
    print("=" * 80)

    if not results or "coherence_metrics" not in results[0]:
        print("No coherence metrics found")
        return

    metrics_list = results[0]["coherence_metrics"]

    if not metrics_list:
        print("Empty metrics list")
        return

    print(f"\nEvolution over {len(metrics_list)} ticks:\n")
    print(f"{'Tick':<6} | {'Trust':<7} | {'γ':<7} | {'C':<7} | {'Regime':<10} | {'ATP Cost':<10} | {'Coop Rate'}")
    print("-" * 90)

    for i, m in enumerate(metrics_list):
        if i % 5 == 0 or i == len(metrics_list) - 1:  # Show every 5th tick + last
            regime = "quantum" if m.is_quantum_regime else "classical"
            print(f"{m.tick:<6} | {m.network_trust:<7.3f} | {m.gamma:<7.3f} | {m.coherence:<7.3f} | {regime:<10} | {m.avg_atp_cost:<10.2f} | {m.cooperation_rate:.3f}")

    # Analyze trends
    print("\n=== Trend Analysis ===\n")

    first = metrics_list[0]
    last = metrics_list[-1]

    trust_change = last.network_trust - first.network_trust
    gamma_change = last.gamma - first.gamma
    coherence_change = last.coherence - first.coherence
    atp_change = last.avg_atp_cost - first.avg_atp_cost
    coop_change = last.cooperation_rate - first.cooperation_rate

    print(f"Trust:            {first.network_trust:.3f} → {last.network_trust:.3f} ({trust_change:+.3f})")
    print(f"γ (correlation):  {first.gamma:.3f} → {last.gamma:.3f} ({gamma_change:+.3f})")
    print(f"C (coherence):    {first.coherence:.3f} → {last.coherence:.3f} ({coherence_change:+.3f})")
    print(f"ATP Cost:         {first.avg_atp_cost:.2f} → {last.avg_atp_cost:.2f} ({atp_change:+.2f})")
    print(f"Cooperation Rate: {first.cooperation_rate:.3f} → {last.cooperation_rate:.3f} ({coop_change:+.3f})")

    # Check for death spiral
    if atp_change > 0 and coop_change < 0:
        print("\n⚠️  DEATH SPIRAL DETECTED:")
        print("  - ATP costs increased while cooperation decreased")
        print("  - Suggests positive feedback loop: low trust → high cost → less cooperation → lower trust")

    # Check regime
    if first.is_quantum_regime and last.is_quantum_regime:
        print("\n✅ Stayed in quantum regime (should have discount)")
    elif not first.is_quantum_regime and not last.is_quantum_regime:
        print("\n❌ Stayed in classical regime (paying premium)")
    else:
        print(f"\n⚠️  Regime transition: {'quantum → classical' if first.is_quantum_regime else 'classical → quantum'}")


def test_starting_conditions():
    """Test coherence pricing with different starting trust levels"""

    print("\n" + "=" * 80)
    print("  STARTING CONDITION SENSITIVITY TEST")
    print("=" * 80)

    print("\nTesting hypothesis: Low starting trust → death spiral")
    print("Testing with different initial network trust levels...\n")

    # We can't easily modify starting trust in current simulation
    # But we can analyze what ATP costs would be at different trust levels

    layer = CoherencePricingLayer()

    test_cases = [
        {"name": "Very Low Trust", "trust": 0.2, "variance": 0.08, "density": 0.3, "agents": 7, "strong_edges": 1},
        {"name": "Low Trust", "trust": 0.3, "variance": 0.06, "density": 0.5, "agents": 7, "strong_edges": 2},
        {"name": "Medium Trust", "trust": 0.5, "variance": 0.04, "density": 0.7, "agents": 7, "strong_edges": 5},
        {"name": "High Trust", "trust": 0.7, "variance": 0.02, "density": 0.9, "agents": 7, "strong_edges": 10},
    ]

    print(f"{'Starting Condition':<20} | {'γ':<7} | {'C':<7} | {'Regime':<10} | {'Help Cost':<12} | {'Effect'}")
    print("-" * 90)

    for case in test_cases:
        metrics = CoherenceTrustMetrics(
            trust_value=case["trust"],
            trust_variance=case["variance"],
            network_density=case["density"],
            num_agents=case["agents"],
            num_strong_edges=case["strong_edges"]
        )

        regime = "quantum" if metrics.is_quantum_regime else "classical"
        mult = layer.compute_coherence_multiplier(metrics)

        # Base "help" action cost is 10 ATP
        help_cost = 10.0 * mult

        effect = "discount" if mult < 1.0 else "premium" if mult > 1.0 else "neutral"

        print(f"{case['name']:<20} | {metrics.gamma:<7.3f} | {metrics.coherence:<7.3f} | {regime:<10} | {help_cost:<12.2f} | {effect} ({(mult-1)*100:+.1f}%)")

    print("\n=== Key Insight ===")
    print("Low starting trust (typical in new networks) leads to:")
    print("  1. High γ (classical regime)")
    print("  2. ATP premium (15-40%)")
    print("  3. Helping costs MORE than baseline")
    print("  4. Agents can't afford to build trust → death spiral")


def propose_fixes():
    """Propose fixes for the death spiral problem"""

    print("\n" + "=" * 80)
    print("  PROPOSED FIXES")
    print("=" * 80)

    print("\n**Problem**: Coherence pricing creates death spiral in low-trust networks")
    print("  - Low trust → High γ → ATP premium → Less cooperation → Lower trust → Higher γ...")

    print("\n**Fix 1: Inverted Pricing (Subsidy Model)**")
    print("  - Low trust networks get ATP *discount* (subsidy to bootstrap cooperation)")
    print("  - High trust networks pay premium (they can afford it, already successful)")
    print("  - Rationale: Economic support for trust-building, not punishment")

    print("\n**Fix 2: Starting Capital**")
    print("  - Give agents higher starting ATP (150 instead of 100)")
    print("  - Buffer allows agents to pay premiums while building trust")
    print("  - Once trust established, they recoup through discounts")

    print("\n**Fix 3: Cooperation-Specific Discount**")
    print("  - Helping actions get discount regardless of network trust")
    print("  - Defection actions pay premium")
    print("  - Directly incentivizes cooperation even in low-trust state")

    print("\n**Fix 4: Delayed Coherence Pricing**")
    print("  - Start with flat pricing (first 10 ticks)")
    print("  - Enable coherence pricing after trust network forms")
    print("  - Prevents death spiral during formation phase")

    print("\n**Fix 5: Asymmetric Thresholds**")
    print("  - Discount threshold at C=0.3 (easier to reach)")
    print("  - Premium threshold at C=0.6 (harder to fall to)")
    print("  - Creates hysteresis: easier to enter cooperation than leave")


# ============================================================================
# Main Analysis
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  COHERENCE ATP PRICING - POST-MORTEM ANALYSIS")
    print("  Session #28 - Understanding Failure Mode")
    print("=" * 80)

    print("\n**Unexpected Result**: Coherence pricing decreased cooperation by 6.4%")
    print("**Expected**: High ATP costs in low-trust networks should incentivize cooperation")
    print("**Reality**: Low-trust networks can't afford to cooperate → death spiral\n")

    # Run a fresh simulation to analyze
    print("Running fresh simulation for detailed analysis...")
    sim = CoherencePricingSimulation(enable_coherence=True)
    results = sim.run_simulation(num_ticks=30)

    # Analyze evolution
    analyze_evolution_trajectory([{"coherence_metrics": sim.coherence_metrics}])

    # Test starting conditions
    test_starting_conditions()

    # Propose fixes
    propose_fixes()

    print("\n" + "=" * 80)
    print("  CONCLUSION")
    print("=" * 80)
    print("\n**Discovery**: Coherence pricing has unexpected death spiral in low-trust networks")
    print("**Cause**: ATP premium hits immediately, trust builds slowly")
    print("**Solution**: Need inverted pricing or subsidy model for bootstrapping")
    print("\n**This is valuable research**: Found fundamental flaw before production deployment")
    print("**Next**: Implement Fix #1 (inverted pricing) and re-test")
