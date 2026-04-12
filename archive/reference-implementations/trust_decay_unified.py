#!/usr/bin/env python3
"""
Unified Trust Decay Framework — Reference Implementation
==========================================================

Unifies 5 competing decay models into one composable framework:

1. Exponential: Classic time-based decay toward baseline
2. Tidal: Selective stripping of weak outer relationships first
3. Cosmological: Network density modulates decay rate (1/C scaling)
4. Diversity: Observation overlap reduces imported trust
5. Metabolic: Activity + heartbeat state modulates all decay

The unified model:
    trust(t) = baseline + (trust₀ - baseline) × Π(decay_factors)

Where decay_factors is the product of active decay modifiers:
    - Time decay: e^(-λ × Δt)
    - Activity factor: slows decay based on recent interactions
    - Metabolic multiplier: heartbeat state adjusts all rates
    - Diversity correction: reduces cross-society trust by overlap
    - Tidal stripping: removes outer-layer trust under pressure

Integration with R7: reputation deltas from R7 actions feed back
into the decay model as "observations" that reset the decay clock.

Date: 2026-02-21
Consolidates: tidal_trust_decay.py, cosmological_reputation_decay.py,
  atp_demurrage.py, dynamic_trust_decay.py, simulations/trust_decay.py
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# Core Types
# ═══════════════════════════════════════════════════════════════

class DecayModel(Enum):
    """Available decay models."""
    EXPONENTIAL = "exponential"
    TIDAL = "tidal"
    COSMOLOGICAL = "cosmological"
    DIVERSITY = "diversity"
    METABOLIC = "metabolic"


class MetabolicState(Enum):
    """Heartbeat metabolic states (from Hardbound heartbeat system)."""
    ACTIVE = "active"
    FOCUS = "focus"
    REST = "rest"
    SLEEP = "sleep"
    DREAM = "dream"
    CRISIS = "crisis"

    @property
    def decay_multiplier(self) -> float:
        """How much this state modulates decay rate."""
        return {
            MetabolicState.ACTIVE: 1.0,
            MetabolicState.FOCUS: 0.8,     # Focused work: slower decay
            MetabolicState.REST: 0.5,      # Rest: much slower
            MetabolicState.SLEEP: 0.1,     # Sleep: minimal decay
            MetabolicState.DREAM: 0.0,     # Dream: no decay (consolidation)
            MetabolicState.CRISIS: 1.5,    # Crisis: accelerated decay
        }.get(self, 1.0)


class TrustLayer(Enum):
    """Trust relationship layers (tidal model)."""
    CORE = "core"          # Direct, proven trust (most resistant)
    INNER = "inner"        # Close collaborators
    OUTER = "outer"        # Acquaintances
    ENVELOPE = "envelope"  # Peripheral (most vulnerable to stripping)

    @property
    def binding_energy(self) -> float:
        """Minimum force needed to strip this layer."""
        return {
            TrustLayer.CORE: 0.9,
            TrustLayer.INNER: 0.6,
            TrustLayer.OUTER: 0.3,
            TrustLayer.ENVELOPE: 0.1,
        }.get(self, 0.1)


# ═══════════════════════════════════════════════════════════════
# Trust Dimensions (T3-aligned)
# ═══════════════════════════════════════════════════════════════

@dataclass
class TrustDimensions:
    """T3-aligned trust dimensions with per-dimension decay rates."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    # Decay rates per day (talent decays slowest, temperament fastest)
    DECAY_RATES = {
        "talent": 0.01,        # Expertise fades slowly
        "training": 0.02,      # Skills need practice
        "temperament": 0.03,   # Consistency needs demonstration
    }

    # Baselines: trust decays toward these, not zero
    BASELINES = {
        "talent": 0.3,
        "training": 0.3,
        "temperament": 0.3,
    }

    def composite(self) -> float:
        return 0.4 * self.talent + 0.3 * self.training + 0.3 * self.temperament

    def get(self, dim: str) -> float:
        return getattr(self, dim, 0.5)

    def set(self, dim: str, value: float):
        setattr(self, dim, max(0.0, min(1.0, value)))

    def to_dict(self) -> Dict[str, float]:
        return {"talent": self.talent, "training": self.training,
                "temperament": self.temperament}


# ═══════════════════════════════════════════════════════════════
# Decay Context (what modulates decay)
# ═══════════════════════════════════════════════════════════════

@dataclass
class DecayContext:
    """All contextual factors that influence decay rate."""
    # Time
    elapsed_days: float = 1.0

    # Activity (slows decay)
    recent_interactions: int = 0
    activity_window_days: float = 7.0

    # Metabolic
    metabolic_state: MetabolicState = MetabolicState.ACTIVE

    # Network (cosmological model)
    network_density: float = 0.5   # active_agents / total_agents
    density_critical: float = 0.1  # Threshold below which decay accelerates

    # Tidal (relationship pressure)
    tidal_force: float = 0.0       # External pressure (0 = calm, 1 = max)
    trust_layer: TrustLayer = TrustLayer.INNER

    # Diversity (federation import)
    observation_overlap: float = 0.5   # 0 = diverse, 1 = identical
    diversity_base_decay: float = 0.72  # From Session 70 calibration

    # Sustained trust bonus
    sustained_threshold: float = 0.8   # Trust > this decays at half rate

    # R7 observation: most recent R7 action resets decay
    last_r7_observation_days_ago: float = 0.0


# ═══════════════════════════════════════════════════════════════
# Individual Decay Models
# ═══════════════════════════════════════════════════════════════

def exponential_decay(trust: float, baseline: float, rate: float,
                      elapsed_days: float) -> float:
    """Classic exponential decay toward baseline.

    trust(t) = baseline + (trust₀ - baseline) × e^(-λt)
    """
    return baseline + (trust - baseline) * math.exp(-rate * elapsed_days)


def activity_factor(recent_interactions: int, window_days: float) -> float:
    """Activity slows decay. More interactions = less decay.

    Factor in [0.3, 1.0]: 1.0 = no slowing, 0.3 = max slowing
    """
    base_factor = 0.3
    if window_days <= 0:
        return 1.0
    # Normalized activity rate
    activity_rate = recent_interactions / max(1, window_days)
    # Exponential diminishing returns
    return base_factor + (1.0 - base_factor) * math.exp(-0.5 * activity_rate)


def metabolic_multiplier(state: MetabolicState) -> float:
    """Metabolic state multiplier on all decay rates."""
    return state.decay_multiplier


def cosmological_factor(network_density: float, density_critical: float) -> float:
    """Network density modulates decay. Sparse networks → faster decay.

    Coherence C = tanh(2 × log(ρ/ρ_crit + 1))
    Effective multiplier = 1/C (amplifies decay when C < 1)
    """
    if network_density <= 0:
        return 3.0  # Very high decay for disconnected networks
    rho_ratio = network_density / max(density_critical, 0.001)
    coherence = math.tanh(2.0 * math.log(rho_ratio + 1))
    if coherence < 0.01:
        return 3.0  # Cap at 3x acceleration
    return min(3.0, 1.0 / coherence)


def tidal_stripping(trust: float, baseline: float, force: float,
                    layer: TrustLayer) -> float:
    """Tidal model: external pressure strips weak outer trust first.

    Binding energy = layer threshold. If force > binding, trust is stripped.
    If force < binding, no effect.
    """
    binding = layer.binding_energy
    if force < binding:
        return trust  # Force too weak to strip this layer

    # Proportional stripping: force exceeds binding → partial removal
    strip_fraction = min(1.0, (force - binding) / (1.0 - binding + 0.01))
    decay_amount = (trust - baseline) * strip_fraction * 0.1  # 10% per event
    return max(baseline, trust - decay_amount)


def diversity_correction(trust: float, overlap: float,
                         base_decay: float = 0.72) -> float:
    """Diversity model: identical observations decay, diverse preserve.

    decay = base + (1 - base) × (1 - overlap)
    overlap=0 → decay=1.0 (no loss — diverse observations)
    overlap=1 → decay=base (max loss — identical observations)
    """
    diversity = 1.0 - overlap
    factor = base_decay + (1.0 - base_decay) * diversity
    return trust * factor


def r7_observation_reset(elapsed_days: float, days_since_observation: float,
                         observation_weight: float = 0.5) -> float:
    """R7 observations partially reset the decay clock.

    If an R7 action was recently observed, effective elapsed time is reduced.
    observation_weight: how much the observation resets decay (0=none, 1=full)
    """
    if days_since_observation >= elapsed_days:
        return elapsed_days  # No reset (observation before decay window)
    # Effective elapsed = days_since_observation + remaining × (1 - weight)
    remaining = elapsed_days - days_since_observation
    return days_since_observation + remaining * (1.0 - observation_weight)


# ═══════════════════════════════════════════════════════════════
# Unified Decay Engine
# ═══════════════════════════════════════════════════════════════

class UnifiedDecayEngine:
    """
    Composable decay engine combining all models.

    Usage:
        engine = UnifiedDecayEngine()
        engine.enable(DecayModel.EXPONENTIAL)
        engine.enable(DecayModel.METABOLIC)
        new_trust = engine.apply(trust_dims, context)

    Each enabled model contributes a factor that modulates the base
    exponential decay. Factors compose multiplicatively.
    """

    def __init__(self):
        self.enabled_models: set = set()
        self.decay_log: List[Dict] = []

    def enable(self, model: DecayModel):
        """Enable a decay model."""
        self.enabled_models.add(model)

    def disable(self, model: DecayModel):
        """Disable a decay model."""
        self.enabled_models.discard(model)

    def apply(
        self,
        trust: TrustDimensions,
        context: DecayContext,
    ) -> Tuple[TrustDimensions, Dict]:
        """
        Apply unified decay to trust dimensions.

        Returns: (new_trust, decay_report)
        """
        report = {
            "models_applied": [],
            "per_dimension": {},
            "composite_before": trust.composite(),
        }

        result = TrustDimensions(
            talent=trust.talent,
            training=trust.training,
            temperament=trust.temperament,
        )

        for dim in ["talent", "training", "temperament"]:
            current = trust.get(dim)
            baseline = TrustDimensions.BASELINES[dim]
            base_rate = TrustDimensions.DECAY_RATES[dim]

            effective_elapsed = context.elapsed_days
            effective_rate = base_rate

            factors = {}

            # R7 observation: partially reset decay clock
            if context.last_r7_observation_days_ago > 0:
                effective_elapsed = r7_observation_reset(
                    context.elapsed_days,
                    context.last_r7_observation_days_ago,
                )
                factors["r7_observation"] = round(effective_elapsed / max(0.01, context.elapsed_days), 3)

            # Activity factor
            if DecayModel.EXPONENTIAL in self.enabled_models:
                af = activity_factor(
                    context.recent_interactions,
                    context.activity_window_days,
                )
                effective_rate *= af
                factors["activity"] = round(af, 3)

            # Metabolic multiplier
            if DecayModel.METABOLIC in self.enabled_models:
                mm = metabolic_multiplier(context.metabolic_state)
                effective_rate *= mm
                factors["metabolic"] = round(mm, 3)

            # Cosmological scaling
            if DecayModel.COSMOLOGICAL in self.enabled_models:
                cf = cosmological_factor(
                    context.network_density,
                    context.density_critical,
                )
                effective_rate *= cf
                factors["cosmological"] = round(cf, 3)

            # Sustained trust bonus (high trust decays slower)
            if current > context.sustained_threshold:
                effective_rate *= 0.5
                factors["sustained_bonus"] = 0.5

            # Apply exponential decay
            new_val = exponential_decay(
                current, baseline, effective_rate, effective_elapsed,
            )

            # Tidal stripping (additional discrete removal)
            if DecayModel.TIDAL in self.enabled_models and context.tidal_force > 0:
                new_val = tidal_stripping(
                    new_val, baseline, context.tidal_force, context.trust_layer,
                )
                factors["tidal"] = round(context.tidal_force, 3)

            # Diversity correction (for imported trust)
            if DecayModel.DIVERSITY in self.enabled_models:
                new_val = diversity_correction(
                    new_val, context.observation_overlap,
                    context.diversity_base_decay,
                )
                factors["diversity"] = round(context.observation_overlap, 3)

            result.set(dim, new_val)
            report["per_dimension"][dim] = {
                "before": round(current, 4),
                "after": round(new_val, 4),
                "effective_rate": round(effective_rate, 5),
                "factors": factors,
            }

        report["composite_after"] = result.composite()
        report["total_decay"] = round(
            report["composite_before"] - report["composite_after"], 4
        )
        report["models_applied"] = sorted(m.value for m in self.enabled_models)

        self.decay_log.append(report)
        return result, report

    def simulate(
        self,
        initial: TrustDimensions,
        days: int,
        context_fn: Callable[[int], DecayContext],
    ) -> List[Tuple[int, TrustDimensions, Dict]]:
        """
        Simulate decay over multiple days.

        Args:
            initial: Starting trust
            days: Number of days to simulate
            context_fn: Function that returns DecayContext for each day
        """
        results = [(0, initial, {})]
        current = TrustDimensions(
            talent=initial.talent,
            training=initial.training,
            temperament=initial.temperament,
        )

        for day in range(1, days + 1):
            ctx = context_fn(day)
            ctx.elapsed_days = 1.0  # Day-by-day simulation
            current, report = self.apply(current, ctx)
            results.append((day, TrustDimensions(
                talent=current.talent,
                training=current.training,
                temperament=current.temperament,
            ), report))

        return results


# ═══════════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════════

def run_demo():
    """Demonstrate unified trust decay framework."""
    print("=" * 70)
    print("  Unified Trust Decay Framework")
    print("  5 models composed: exponential + tidal + cosmological +")
    print("  diversity + metabolic, with R7 observation reset")
    print("=" * 70)

    checks_passed = 0
    checks_failed = 0

    def check(name, condition, detail=""):
        nonlocal checks_passed, checks_failed
        if condition:
            print(f"  ✓ {name}")
            checks_passed += 1
        else:
            msg = f": {detail}" if detail else ""
            print(f"  ✗ {name}{msg}")
            checks_failed += 1

    # ── Test 1: Pure Exponential Decay ──
    print("\n── Test 1: Pure Exponential Decay (30 days) ──")

    engine = UnifiedDecayEngine()
    engine.enable(DecayModel.EXPONENTIAL)

    initial = TrustDimensions(talent=0.9, training=0.85, temperament=0.8)
    ctx = DecayContext(elapsed_days=30, recent_interactions=0)

    decayed, report = engine.apply(initial, ctx)

    print(f"  Before: T={initial.talent:.3f} Tr={initial.training:.3f} Te={initial.temperament:.3f}")
    print(f"  After:  T={decayed.talent:.3f} Tr={decayed.training:.3f} Te={decayed.temperament:.3f}")
    print(f"  Composite: {report['composite_before']:.3f} → {report['composite_after']:.3f}")

    check("T1: All dimensions decayed", decayed.composite() < initial.composite())
    check("T1: Talent decays slowest (rate=0.01)",
          decayed.talent > decayed.training > decayed.temperament,
          f"T={decayed.talent:.3f} Tr={decayed.training:.3f} Te={decayed.temperament:.3f}")
    check("T1: Trust stays above baseline",
          decayed.talent > 0.3 and decayed.training > 0.3)

    # ── Test 2: Activity Slows Decay ──
    print("\n── Test 2: Activity Slows Decay ──")

    active_ctx = DecayContext(elapsed_days=30, recent_interactions=20)
    inactive_ctx = DecayContext(elapsed_days=30, recent_interactions=0)

    engine2 = UnifiedDecayEngine()
    engine2.enable(DecayModel.EXPONENTIAL)

    active_result, _ = engine2.apply(initial, active_ctx)
    inactive_result, _ = engine2.apply(initial, inactive_ctx)

    check("T2: Active entity decays less",
          active_result.composite() > inactive_result.composite(),
          f"active={active_result.composite():.3f} inactive={inactive_result.composite():.3f}")

    # ── Test 3: Metabolic State Modulation ──
    print("\n── Test 3: Metabolic State Modulation ──")

    engine3 = UnifiedDecayEngine()
    engine3.enable(DecayModel.EXPONENTIAL)
    engine3.enable(DecayModel.METABOLIC)

    sleep_ctx = DecayContext(elapsed_days=30, metabolic_state=MetabolicState.SLEEP)
    crisis_ctx = DecayContext(elapsed_days=30, metabolic_state=MetabolicState.CRISIS)

    sleep_result, sleep_report = engine3.apply(initial, sleep_ctx)
    crisis_result, crisis_report = engine3.apply(initial, crisis_ctx)

    check("T3: Sleep state preserves trust",
          sleep_result.composite() > initial.composite() * 0.9,
          f"sleep={sleep_result.composite():.3f}")
    check("T3: Crisis state accelerates decay",
          crisis_result.composite() < inactive_result.composite(),
          f"crisis={crisis_result.composite():.3f}")
    check("T3: Dream state = zero decay",
          MetabolicState.DREAM.decay_multiplier == 0.0)

    # ── Test 4: Cosmological (Network Density) ──
    print("\n── Test 4: Cosmological Decay (Network Density) ──")

    engine4 = UnifiedDecayEngine()
    engine4.enable(DecayModel.EXPONENTIAL)
    engine4.enable(DecayModel.COSMOLOGICAL)

    dense_ctx = DecayContext(elapsed_days=30, network_density=0.8)
    sparse_ctx = DecayContext(elapsed_days=30, network_density=0.05)

    dense_result, _ = engine4.apply(initial, dense_ctx)
    sparse_result, _ = engine4.apply(initial, sparse_ctx)

    print(f"  Dense network (ρ=0.8): composite={dense_result.composite():.3f}")
    print(f"  Sparse network (ρ=0.05): composite={sparse_result.composite():.3f}")

    check("T4: Sparse network decays faster",
          sparse_result.composite() < dense_result.composite())
    check("T4: Dense network ≈ base decay",
          abs(dense_result.composite() - inactive_result.composite()) < 0.05)

    # ── Test 5: Tidal Stripping ──
    print("\n── Test 5: Tidal Stripping (Layer-Based) ──")

    engine5 = UnifiedDecayEngine()
    engine5.enable(DecayModel.EXPONENTIAL)
    engine5.enable(DecayModel.TIDAL)

    # High pressure on envelope layer
    envelope_ctx = DecayContext(
        elapsed_days=1, tidal_force=0.5, trust_layer=TrustLayer.ENVELOPE,
    )
    # Same pressure on core layer
    core_ctx = DecayContext(
        elapsed_days=1, tidal_force=0.5, trust_layer=TrustLayer.CORE,
    )

    envelope_result, _ = engine5.apply(initial, envelope_ctx)
    core_result, _ = engine5.apply(initial, core_ctx)

    check("T5: Envelope stripped (force > binding)",
          envelope_result.composite() < initial.composite() - 0.01)
    check("T5: Core protected (force < binding)",
          core_result.composite() > envelope_result.composite())

    # ── Test 6: Diversity Correction ──
    print("\n── Test 6: Diversity Correction (Federation) ──")

    engine6 = UnifiedDecayEngine()
    engine6.enable(DecayModel.DIVERSITY)

    diverse_ctx = DecayContext(elapsed_days=0, observation_overlap=0.0)
    identical_ctx = DecayContext(elapsed_days=0, observation_overlap=1.0)

    diverse_result, _ = engine6.apply(initial, diverse_ctx)
    identical_result, _ = engine6.apply(initial, identical_ctx)

    check("T6: Diverse observations preserve trust",
          diverse_result.composite() > identical_result.composite())
    check("T6: Identical observations decay more",
          identical_result.composite() < initial.composite() * 0.8)

    # ── Test 7: R7 Observation Reset ──
    print("\n── Test 7: R7 Observation Resets Decay Clock ──")

    engine7 = UnifiedDecayEngine()
    engine7.enable(DecayModel.EXPONENTIAL)

    # 30 days elapsed, but R7 observation 5 days ago → effective ~5 days
    r7_ctx = DecayContext(
        elapsed_days=30,
        last_r7_observation_days_ago=5.0,
    )
    no_r7_ctx = DecayContext(elapsed_days=30)

    r7_result, _ = engine7.apply(initial, r7_ctx)
    no_r7_result, _ = engine7.apply(initial, no_r7_ctx)

    check("T7: R7 observation slows decay",
          r7_result.composite() > no_r7_result.composite(),
          f"with_r7={r7_result.composite():.3f} without={no_r7_result.composite():.3f}")

    # ── Test 8: All Models Composed ──
    print("\n── Test 8: All 5 Models Composed ──")

    engine_full = UnifiedDecayEngine()
    for model in DecayModel:
        engine_full.enable(model)

    full_ctx = DecayContext(
        elapsed_days=30,
        recent_interactions=5,
        metabolic_state=MetabolicState.ACTIVE,
        network_density=0.3,
        tidal_force=0.2,
        trust_layer=TrustLayer.OUTER,
        observation_overlap=0.4,
        last_r7_observation_days_ago=10.0,
    )

    full_result, full_report = engine_full.apply(initial, full_ctx)

    print(f"  All models active (30 days, moderate context):")
    print(f"  Before: {report['composite_before']:.3f}")
    print(f"  After: {full_result.composite():.3f}")
    for dim, info in full_report["per_dimension"].items():
        print(f"    {dim}: {info['before']:.3f} → {info['after']:.3f} "
              f"(rate={info['effective_rate']:.5f}, factors={info['factors']})")

    check("T8: All 5 models applied",
          len(full_report["models_applied"]) == 5)
    check("T8: Trust decayed with all models",
          full_result.composite() < initial.composite())

    # ── Test 9: Sustained Trust Bonus ──
    print("\n── Test 9: Sustained Trust Bonus ──")

    high_trust = TrustDimensions(talent=0.95, training=0.92, temperament=0.90)
    med_trust = TrustDimensions(talent=0.7, training=0.7, temperament=0.7)

    engine9 = UnifiedDecayEngine()
    engine9.enable(DecayModel.EXPONENTIAL)

    ctx9 = DecayContext(elapsed_days=30, sustained_threshold=0.8)

    high_result, _ = engine9.apply(high_trust, ctx9)
    med_result, _ = engine9.apply(med_trust, ctx9)

    # High trust (>0.8) gets 50% decay rate reduction
    high_decay = high_trust.composite() - high_result.composite()
    med_decay = med_trust.composite() - med_result.composite()

    # High trust should decay proportionally less per unit
    high_decay_rate = high_decay / max(0.01, high_trust.composite() - 0.3)
    med_decay_rate = med_decay / max(0.01, med_trust.composite() - 0.3)

    check("T9: High trust decays at lower rate",
          high_decay_rate < med_decay_rate,
          f"high_rate={high_decay_rate:.4f} med_rate={med_decay_rate:.4f}")

    # ── Test 10: Multi-Day Simulation ──
    print("\n── Test 10: 90-Day Decay Simulation ──")

    engine10 = UnifiedDecayEngine()
    engine10.enable(DecayModel.EXPONENTIAL)
    engine10.enable(DecayModel.METABOLIC)

    def context_fn(day):
        """Simulate a realistic work pattern."""
        if day % 7 in (5, 6):
            # Weekend: rest state, fewer interactions
            return DecayContext(
                metabolic_state=MetabolicState.REST,
                recent_interactions=1,
            )
        elif day % 30 < 25:
            # Working day
            return DecayContext(
                metabolic_state=MetabolicState.ACTIVE,
                recent_interactions=5,
            )
        else:
            # Month-end: focus state
            return DecayContext(
                metabolic_state=MetabolicState.FOCUS,
                recent_interactions=10,
            )

    sim = engine10.simulate(initial, 90, context_fn)

    day_0 = sim[0][1].composite()
    day_30 = sim[30][1].composite()
    day_60 = sim[60][1].composite()
    day_90 = sim[90][1].composite()

    print(f"  Day  0: composite={day_0:.3f}")
    print(f"  Day 30: composite={day_30:.3f}")
    print(f"  Day 60: composite={day_60:.3f}")
    print(f"  Day 90: composite={day_90:.3f}")

    check("T10: Monotonic decay over 90 days", day_0 > day_30 > day_60 > day_90)
    check("T10: Trust still above baseline at 90 days", day_90 > 0.35)
    check("T10: Decay decelerates (diminishing returns)",
          (day_0 - day_30) > (day_60 - day_90))

    # ── Test 11: Zero-Day Context (No Decay) ──
    print("\n── Test 11: Zero Elapsed Time ──")

    engine11 = UnifiedDecayEngine()
    engine11.enable(DecayModel.EXPONENTIAL)

    zero_ctx = DecayContext(elapsed_days=0.0)
    zero_result, _ = engine11.apply(initial, zero_ctx)

    check("T11: Zero elapsed = no exponential decay",
          abs(zero_result.composite() - initial.composite()) < 0.001)

    # ── Test 12: Extreme Conditions ──
    print("\n── Test 12: Extreme Conditions ──")

    engine12 = UnifiedDecayEngine()
    for m in DecayModel:
        engine12.enable(m)

    # Worst case: crisis, sparse network, high tidal, identical observations
    worst_ctx = DecayContext(
        elapsed_days=365,
        metabolic_state=MetabolicState.CRISIS,
        network_density=0.01,
        tidal_force=0.95,
        trust_layer=TrustLayer.ENVELOPE,
        observation_overlap=1.0,
    )

    worst_result, _ = engine12.apply(initial, worst_ctx)
    check("T12: Worst case still above zero",
          worst_result.composite() > 0.0)
    check("T12: Worst case approaches baseline",
          worst_result.composite() < 0.35)

    # Best case: dream state, dense network, no tidal, diverse observations
    best_ctx = DecayContext(
        elapsed_days=365,
        recent_interactions=100,
        metabolic_state=MetabolicState.DREAM,
        network_density=0.9,
        tidal_force=0.0,
        observation_overlap=0.0,
    )

    best_result, _ = engine12.apply(initial, best_ctx)
    check("T12: Best case preserves most trust",
          best_result.composite() > initial.composite() * 0.7)

    # ── Summary ──
    print("\n" + "=" * 70)
    total = checks_passed + checks_failed
    print(f"  Unified Trust Decay: {checks_passed}/{total} checks passed")
    if checks_failed == 0:
        print("  ALL CHECKS PASSED!")

    print(f"\n  5 DECAY MODELS UNIFIED:")
    print(f"    1. Exponential: base time decay toward dimensional baselines")
    print(f"    2. Metabolic: heartbeat state modulates all rates (0.0-1.5x)")
    print(f"    3. Cosmological: network density → coherence → decay scaling")
    print(f"    4. Tidal: external pressure strips weak outer trust layers")
    print(f"    5. Diversity: observation overlap reduces imported trust")

    print(f"\n  R7 INTEGRATION:")
    print(f"    R7 actions generate observations that partially reset decay")
    print(f"    More recent R7 observations = less effective elapsed time")
    print(f"    This creates virtuous cycle: active agents decay less")

    print(f"\n  KEY INSIGHT:")
    print(f"    All models compose multiplicatively:")
    print(f"    effective_rate = base × activity × metabolic × cosmological")
    print(f"    + tidal stripping (discrete) + diversity correction (federated)")
    print(f"    This means any combination of models can be enabled/disabled")
    print(f"    without changing the framework structure.")
    print("=" * 70)

    return checks_failed == 0


if __name__ == "__main__":
    success = run_demo()
    import sys
    sys.exit(0 if success else 1)
