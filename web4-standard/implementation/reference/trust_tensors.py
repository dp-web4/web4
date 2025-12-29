#!/usr/bin/env python3
"""
Trust Tensor CI Modulation

Phase 3: Trust Integration
Implements coherence index (CI) modulation of trust application.

Key insight: CI modulates HOW trust is applied, not trust itself.
- High CI (0.9+): Full T3 access, normal ATP costs, normal witness requirements
- Low CI (<0.5): Reduced effective trust, increased ATP costs, more witnesses required

The CI acts as a "trust ceiling" - you can't access more trust than your coherence allows.
This prevents entities from leveraging high trust scores while exhibiting incoherent behavior.

Functions:
- effective_trust() - Applies CI as multiplicative ceiling on T3 tensor
- adjusted_atp_cost() - Increases ATP costs for low coherence (friction, not block)
- required_witnesses() - Increases witness requirements for low coherence
- ci_modulation_curve() - Configurable modulation curve per dimension
"""

from dataclasses import dataclass
from typing import Dict, Optional
from math import ceil, exp
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

# Import T3Tensor from game engine (existing trust implementation)
from game.engine.mrh_aware_trust import T3Tensor


# ============================================================================
# CI Modulation Configuration
# ============================================================================

@dataclass
class CIModulationConfig:
    """
    Society-configurable parameters for CI modulation

    Different societies may have different tolerance for low coherence:
    - High-security: Aggressive modulation (strict=True, high steepness)
    - Casual/experimental: Lenient modulation (strict=False, low steepness)
    """
    # Effective trust modulation
    trust_modulation_steepness: float = 2.0  # Higher = steeper penalty for low CI
    trust_minimum_multiplier: float = 0.1    # Minimum fraction of trust accessible (at CI=0)

    # ATP cost modulation
    atp_threshold_high: float = 0.9          # CI above this = no ATP penalty
    atp_max_multiplier: float = 10.0         # Maximum ATP cost multiplier
    atp_penalty_exponent: float = 2.0        # Penalty curve steepness (quadratic default)

    # Witness requirement modulation
    witness_threshold_high: float = 0.8      # CI above this = no additional witnesses
    witness_max_additional: int = 8          # Maximum additional witnesses required
    witness_penalty_steepness: float = 10.0  # How quickly witnesses increase


# ============================================================================
# Effective Trust Calculation
# ============================================================================

def ci_modulation_curve(ci: float, config: CIModulationConfig) -> float:
    """
    Calculate CI modulation multiplier for trust

    Returns value 0-1 representing fraction of trust accessible:
    - CI = 1.0 → multiplier = 1.0 (full trust)
    - CI = 0.5 → multiplier ≈ 0.25 (using default steepness=2.0)
    - CI = 0.0 → multiplier = config.trust_minimum_multiplier

    Uses power curve: multiplier = ci^steepness
    Ensures minimum multiplier is respected.
    """
    # Power curve with configurable steepness
    raw_multiplier = ci ** config.trust_modulation_steepness

    # Apply minimum multiplier floor
    return max(config.trust_minimum_multiplier, raw_multiplier)


def effective_trust(
    t3: T3Tensor,
    ci: float,
    config: Optional[CIModulationConfig] = None
) -> T3Tensor:
    """
    Apply CI as multiplicative ceiling on T3 tensor

    CI modulates trust application, not trust itself:
    - T3 represents long-term reputation (what others think of you)
    - CI represents current coherence (how consistent you're being right now)
    - Effective trust = T3 × CI_modulation (you can't use more trust than your coherence allows)

    Example:
    - Alice has T3 = {talent: 0.9, training: 0.8, temperament: 0.95}
    - Alice's current CI = 0.4 (suspicious activity pattern)
    - Effective trust ≈ {0.16, 0.14, 0.16} (quadratic penalty)
    - Alice can't leverage her high reputation while being incoherent

    Args:
        t3: Base T3 tensor (talent, training, temperament)
        ci: Current coherence index (0-1)
        config: Modulation configuration (uses defaults if None)

    Returns:
        CI-modulated T3 tensor
    """
    if config is None:
        config = CIModulationConfig()

    # Calculate CI modulation multiplier
    multiplier = ci_modulation_curve(ci, config)

    # Apply multiplicative ceiling to all T3 dimensions
    return T3Tensor(
        talent=t3.talent * multiplier,
        training=t3.training * multiplier,
        temperament=t3.temperament * multiplier
    )


# ============================================================================
# ATP Cost Modulation
# ============================================================================

def adjusted_atp_cost(
    base_cost: float,
    ci: float,
    config: Optional[CIModulationConfig] = None
) -> float:
    """
    Calculate ATP cost with CI-based penalty

    Lower coherence increases ATP costs as friction (not hard block):
    - High CI (≥0.9): No penalty, pay base cost
    - Medium CI (0.5-0.9): Moderate penalty (1.2x - 2x)
    - Low CI (<0.5): Significant penalty (2x - 10x)

    Uses quadratic penalty by default: multiplier = 1 / (ci^2)
    Caps at max_multiplier to prevent completely prohibitive costs.

    Rationale:
    - Incoherent behavior increases operational costs
    - Friction discourages suspicious patterns without hard blocks
    - Legitimate edge cases (travel, upgrades) can still operate

    Example:
    - Base cost: 100 ATP
    - CI = 0.95 → Adjusted: 100 ATP (no penalty, above threshold)
    - CI = 0.7 → Adjusted: 204 ATP (2x penalty)
    - CI = 0.3 → Adjusted: 1000 ATP (10x penalty, capped)

    Args:
        base_cost: Baseline ATP cost for operation
        ci: Current coherence index (0-1)
        config: Modulation configuration (uses defaults if None)

    Returns:
        Adjusted ATP cost with CI penalty
    """
    if config is None:
        config = CIModulationConfig()

    # No penalty above high threshold
    if ci >= config.atp_threshold_high:
        return base_cost

    # Calculate penalty multiplier using power law
    # Default: 1 / (ci^2) for quadratic penalty
    multiplier = 1.0 / (ci ** config.atp_penalty_exponent)

    # Cap at maximum to prevent completely prohibitive costs
    multiplier = min(multiplier, config.atp_max_multiplier)

    return base_cost * multiplier


# ============================================================================
# Witness Requirement Modulation
# ============================================================================

def required_witnesses(
    base_requirement: int,
    ci: float,
    config: Optional[CIModulationConfig] = None
) -> int:
    """
    Calculate required witnesses with CI-based adjustment

    Lower coherence requires more witnesses for validation:
    - High CI (≥0.8): No additional witnesses, use base requirement
    - Medium CI (0.5-0.8): Moderate increase (1-3 additional)
    - Low CI (<0.5): Significant increase (3-8 additional)

    Uses linear penalty scaled by distance below threshold.

    Rationale:
    - Incoherent behavior requires more validation
    - More witnesses = harder to coordinate false attestations
    - Legitimate edge cases can still gather witnesses (just more effort)

    Example:
    - Base requirement: 3 witnesses
    - CI = 0.85 → Required: 3 witnesses (above threshold)
    - CI = 0.6 → Required: 5 witnesses (+2)
    - CI = 0.2 → Required: 9 witnesses (+6)

    Args:
        base_requirement: Baseline witness count
        ci: Current coherence index (0-1)
        config: Modulation configuration (uses defaults if None)

    Returns:
        Total required witnesses (base + CI penalty)
    """
    if config is None:
        config = CIModulationConfig()

    # No penalty above high threshold
    if ci >= config.witness_threshold_high:
        return base_requirement

    # Linear penalty scaled by distance below threshold
    distance_below = config.witness_threshold_high - ci
    additional = ceil(distance_below * config.witness_penalty_steepness)

    # Cap at maximum to prevent completely prohibitive requirements
    additional = min(additional, config.witness_max_additional)

    return base_requirement + additional


# ============================================================================
# Demo Scenarios
# ============================================================================

def demo_ci_modulation():
    """Demonstrate CI modulation across different coherence levels"""
    print("=" * 80)
    print("  CI Modulation Demo")
    print("  Phase 3: Trust Integration")
    print("=" * 80)

    # Base parameters
    base_t3 = T3Tensor(talent=0.85, training=0.80, temperament=0.90)
    base_atp_cost = 100.0
    base_witnesses = 3

    print(f"\nBase Parameters:")
    print(f"  T3 Tensor: talent={base_t3.talent:.2f}, training={base_t3.training:.2f}, "
          f"temperament={base_t3.temperament:.2f}")
    print(f"  T3 Composite: {base_t3.composite():.2f}")
    print(f"  Base ATP Cost: {base_atp_cost:.0f}")
    print(f"  Base Witnesses: {base_witnesses}")

    # Test scenarios with different CI values
    scenarios = [
        (0.95, "High coherence - Normal operations"),
        (0.75, "Medium coherence - Some inconsistency"),
        (0.50, "Low coherence - Suspicious pattern"),
        (0.25, "Very low coherence - Highly suspicious"),
    ]

    print("\n" + "=" * 80)
    print("  CI Modulation Effects")
    print("=" * 80)

    for ci, description in scenarios:
        print(f"\n--- CI = {ci:.2f}: {description} ---")

        # Calculate effective trust
        eff_trust = effective_trust(base_t3, ci)
        print(f"  Effective Trust: talent={eff_trust.talent:.2f}, "
              f"training={eff_trust.training:.2f}, temperament={eff_trust.temperament:.2f}")
        print(f"  Effective Composite: {eff_trust.composite():.2f} "
              f"({eff_trust.composite()/base_t3.composite()*100:.1f}% of base)")

        # Calculate ATP cost
        adj_cost = adjusted_atp_cost(base_atp_cost, ci)
        multiplier = adj_cost / base_atp_cost
        print(f"  ATP Cost: {adj_cost:.0f} ({multiplier:.1f}x base)")

        # Calculate witness requirements
        req_witnesses = required_witnesses(base_witnesses, ci)
        additional = req_witnesses - base_witnesses
        print(f"  Required Witnesses: {req_witnesses} (+{additional})")

    print("\n" + "=" * 80)
    print("  Key Insights")
    print("=" * 80)
    print("  • CI acts as multiplicative ceiling on trust (not additive)")
    print("  • Low coherence creates friction (costs, witnesses) not hard blocks")
    print("  • Legitimate edge cases can still operate, just with more effort")
    print("  • Trust reputation (T3) is preserved - only application is modulated")
    print("=" * 80)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    demo_ci_modulation()
