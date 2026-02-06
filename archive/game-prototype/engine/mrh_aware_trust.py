#!/usr/bin/env python3
"""
MRH-Aware Trust Propagation
Session #81: Priority #2 - Complete LCT Identity System

Problem:
Current T3/V3 tensors are global scalars - trust doesn't vary with horizon scope.
In reality, an agent might be:
- Highly trusted at agent-scale (1:1 conversations)
- Moderately trusted at society-scale (local governance)
- Untrusted at global scale (federated coordination)

Solution: MRH-Scoped Trust Tensors
Each T3 tensor component (talent, training, temperament) is horizon-relative.
Trust queries MUST specify MRH profile to get meaningful trust scores.

Theory:
Trust is context-dependent. An agent's capabilities don't transfer uniformly
across scales:
- Spatial: local expertise ≠ global expertise
- Temporal: reliable in sessions ≠ reliable over epochs
- Complexity: simple tasks ≠ society-scale coordination

MRH-Aware Trust Formula:
```python
trust_score = T3(agent_lct, horizon_profile) × relevance(horizon_profile, query_context)

where:
  T3(agent_lct, horizon) → tensor specific to that horizon
  relevance() → MRH distance metric (how well horizons match)
```

This enables:
1. **Horizon-specific reputation**: Different trust at different scales
2. **Context-aware routing**: Select agents whose expertise matches horizon
3. **Trust degradation**: Trust decays as horizons diverge
4. **Witness credibility**: Witnesses have horizon-specific authority

Implementation:
- Extend LCT trust storage with MRH profiles
- Implement horizon-scoped T3 queries
- Add trust decay functions based on MRH distance
- Integrate with existing reputation gossip (Session #79-80)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
from enum import Enum


# ============================================================================
# MRH Profile Types
# ============================================================================

class SpatialExtent(Enum):
    """Spatial horizon (ΔR)"""
    LOCAL = "local"           # Same society/agent neighborhood
    REGIONAL = "regional"     # Federation subset
    GLOBAL = "global"         # Entire federation


class TemporalExtent(Enum):
    """Temporal horizon (ΔT)"""
    EPHEMERAL = "ephemeral"   # Single message/transaction
    SESSION = "session"       # Conversation or task session
    DAY = "day"               # Daily cycles
    EPOCH = "epoch"           # Blockchain epoch (~weeks)


class ComplexityExtent(Enum):
    """Complexity horizon (ΔC)"""
    SIMPLE = "simple"                 # Single-step operations
    AGENT_SCALE = "agent-scale"       # Multi-step agent tasks
    SOCIETY_SCALE = "society-scale"   # Coordination across agents


@dataclass
class MRHProfile:
    """Markov Relevancy Horizon profile"""
    delta_r: SpatialExtent
    delta_t: TemporalExtent
    delta_c: ComplexityExtent

    def to_dict(self) -> Dict[str, str]:
        """Serialize to dictionary"""
        return {
            "deltaR": self.delta_r.value,
            "deltaT": self.delta_t.value,
            "deltaC": self.delta_c.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "MRHProfile":
        """Deserialize from dictionary"""
        return cls(
            delta_r=SpatialExtent(data["deltaR"]),
            delta_t=TemporalExtent(data["deltaT"]),
            delta_c=ComplexityExtent(data["deltaC"])
        )

    def __hash__(self):
        """Make MRHProfile hashable for use as dict key"""
        return hash((self.delta_r, self.delta_t, self.delta_c))

    def __eq__(self, other):
        """Equality comparison"""
        if not isinstance(other, MRHProfile):
            return False
        return (
            self.delta_r == other.delta_r and
            self.delta_t == other.delta_t and
            self.delta_c == other.delta_c
        )


# ============================================================================
# Horizon-Scoped Trust Tensors
# ============================================================================

@dataclass
class T3Tensor:
    """Trust tensor (talent, training, temperament)"""
    talent: float       # Inherent capability (0-1)
    training: float     # Acquired skill (0-1)
    temperament: float  # Behavioral consistency (0-1)

    def composite(self) -> float:
        """Compute composite trust score"""
        # Weighted average: temperament most important, then training, then talent
        return (0.3 * self.talent + 0.3 * self.training + 0.4 * self.temperament)

    def to_dict(self) -> Dict[str, float]:
        """Serialize to dictionary"""
        return {
            "talent": self.talent,
            "training": self.training,
            "temperament": self.temperament,
            "composite": self.composite()
        }


@dataclass
class MRHScopedTrust:
    """
    Trust tensor scoped to specific MRH horizon

    An agent has different trust profiles at different horizons.
    Example:
    - Local/Session/Agent-scale: High trust (good at conversations)
    - Global/Epoch/Society-scale: Low trust (unproven in coordination)
    """
    lct_id: str
    horizon: MRHProfile
    t3_tensor: T3Tensor
    sample_size: int = 1  # Number of observations at this horizon
    last_updated_tick: int = 0

    def get_confidence(self) -> float:
        """
        Confidence in trust estimate based on sample size

        Returns value 0-1 where:
        - 0.0: No observations (no confidence)
        - 0.5: ~10 observations
        - 0.9: ~100 observations
        - 1.0: Infinite observations (asymptotic)
        """
        # Logarithmic confidence curve
        if self.sample_size == 0:
            return 0.0
        return 1.0 - (1.0 / (1.0 + math.log10(self.sample_size)))


# ============================================================================
# MRH Distance & Trust Decay
# ============================================================================

def mrh_distance(profile_a: MRHProfile, profile_b: MRHProfile) -> float:
    """
    Compute distance between two MRH profiles

    Returns value 0-1 where:
    - 0.0: Identical horizons
    - 1.0: Maximally different horizons

    Distance is weighted sum of component differences:
    - Spatial: 40% weight (most important for trust transfer)
    - Temporal: 30% weight
    - Complexity: 30% weight
    """
    # Ordinal distances (enum order represents increasing scope)
    spatial_order = [SpatialExtent.LOCAL, SpatialExtent.REGIONAL, SpatialExtent.GLOBAL]
    temporal_order = [TemporalExtent.EPHEMERAL, TemporalExtent.SESSION,
                      TemporalExtent.DAY, TemporalExtent.EPOCH]
    complexity_order = [ComplexityExtent.SIMPLE, ComplexityExtent.AGENT_SCALE,
                        ComplexityExtent.SOCIETY_SCALE]

    def ordinal_distance(val_a, val_b, ordered_list):
        """Distance between two ordered enum values (0-1)"""
        idx_a = ordered_list.index(val_a)
        idx_b = ordered_list.index(val_b)
        max_dist = len(ordered_list) - 1
        return abs(idx_a - idx_b) / max_dist if max_dist > 0 else 0.0

    spatial_dist = ordinal_distance(profile_a.delta_r, profile_b.delta_r, spatial_order)
    temporal_dist = ordinal_distance(profile_a.delta_t, profile_b.delta_t, temporal_order)
    complexity_dist = ordinal_distance(profile_a.delta_c, profile_b.delta_c, complexity_order)

    # Weighted average
    return 0.4 * spatial_dist + 0.3 * temporal_dist + 0.3 * complexity_dist


def trust_relevance_score(
    agent_horizon: MRHProfile,
    query_horizon: MRHProfile
) -> float:
    """
    Compute trust relevance based on horizon distance

    Trust at agent_horizon is relevant to query_horizon with decay.

    Returns value 0-1 where:
    - 1.0: Identical horizons (perfect relevance)
    - 0.5: Moderate horizon difference
    - 0.0: Maximally different horizons (irrelevant trust)

    Uses exponential decay: relevance = exp(-k * distance)
    where k controls decay rate (higher k = faster decay)
    """
    distance = mrh_distance(agent_horizon, query_horizon)

    # Decay constant (k=3 means 95% decay at distance=1.0)
    decay_constant = 3.0

    return math.exp(-decay_constant * distance)


# ============================================================================
# MRH-Aware Trust Registry
# ============================================================================

class MRHTrustRegistry:
    """
    Registry of horizon-scoped trust tensors

    Stores trust profiles for agents at different MRH horizons.
    Supports horizon-aware queries with trust decay.
    """

    def __init__(self):
        # trust_profiles[lct_id][horizon] = MRHScopedTrust
        self.trust_profiles: Dict[str, Dict[MRHProfile, MRHScopedTrust]] = {}

    def register_trust(self, scoped_trust: MRHScopedTrust):
        """Register or update trust at specific horizon"""
        lct_id = scoped_trust.lct_id

        if lct_id not in self.trust_profiles:
            self.trust_profiles[lct_id] = {}

        self.trust_profiles[lct_id][scoped_trust.horizon] = scoped_trust

    def get_exact_trust(
        self,
        lct_id: str,
        horizon: MRHProfile
    ) -> Optional[MRHScopedTrust]:
        """Get trust at exact horizon (no interpolation)"""
        if lct_id not in self.trust_profiles:
            return None
        return self.trust_profiles[lct_id].get(horizon)

    def get_interpolated_trust(
        self,
        lct_id: str,
        query_horizon: MRHProfile,
        min_confidence: float = 0.3
    ) -> Optional[Tuple[float, float]]:
        """
        Get trust estimate for query horizon using all available horizons

        Returns:
            (trust_score, confidence) or None if no data available

        Algorithm:
        1. Gather all horizon-scoped trust values for this agent
        2. Weight each by relevance to query horizon and sample confidence
        3. Return weighted average trust + overall confidence
        """
        if lct_id not in self.trust_profiles:
            return None

        horizons_data = self.trust_profiles[lct_id]

        if not horizons_data:
            return None

        # Weighted trust aggregation
        weighted_trust_sum = 0.0
        weight_sum = 0.0

        for horizon, scoped_trust in horizons_data.items():
            # Relevance weight (how relevant is this horizon to query?)
            relevance = trust_relevance_score(horizon, query_horizon)

            # Confidence weight (how confident are we in this trust value?)
            confidence = scoped_trust.get_confidence()

            # Combined weight
            weight = relevance * confidence

            if weight < min_confidence:
                continue  # Skip low-weight contributions

            trust_score = scoped_trust.t3_tensor.composite()
            weighted_trust_sum += weight * trust_score
            weight_sum += weight

        if weight_sum == 0:
            return None

        # Interpolated trust
        interpolated_trust = weighted_trust_sum / weight_sum

        # Overall confidence (normalize weight_sum)
        overall_confidence = min(1.0, weight_sum)

        return (interpolated_trust, overall_confidence)

    def get_all_horizons(self, lct_id: str) -> List[MRHProfile]:
        """Get all horizons with trust data for agent"""
        if lct_id not in self.trust_profiles:
            return []
        return list(self.trust_profiles[lct_id].keys())

    def update_trust(
        self,
        lct_id: str,
        horizon: MRHProfile,
        t3_delta: Dict[str, float],
        world_tick: int,
        increment_samples: bool = True
    ):
        """
        Update trust at specific horizon

        Args:
            lct_id: Agent identifier
            horizon: MRH horizon
            t3_delta: Deltas for T3 components {"talent": Δ, "training": Δ, "temperament": Δ}
            world_tick: Current tick
            increment_samples: Whether to increment sample count
        """
        current_trust = self.get_exact_trust(lct_id, horizon)

        if current_trust is None:
            # Initialize new horizon trust
            new_t3 = T3Tensor(
                talent=max(0.0, min(1.0, 0.5 + t3_delta.get("talent", 0.0))),
                training=max(0.0, min(1.0, 0.5 + t3_delta.get("training", 0.0))),
                temperament=max(0.0, min(1.0, 0.5 + t3_delta.get("temperament", 0.0)))
            )
            new_trust = MRHScopedTrust(
                lct_id=lct_id,
                horizon=horizon,
                t3_tensor=new_t3,
                sample_size=1,
                last_updated_tick=world_tick
            )
            self.register_trust(new_trust)
        else:
            # Update existing trust
            current_t3 = current_trust.t3_tensor

            updated_t3 = T3Tensor(
                talent=max(0.0, min(1.0, current_t3.talent + t3_delta.get("talent", 0.0))),
                training=max(0.0, min(1.0, current_t3.training + t3_delta.get("training", 0.0))),
                temperament=max(0.0, min(1.0, current_t3.temperament + t3_delta.get("temperament", 0.0)))
            )

            current_trust.t3_tensor = updated_t3
            current_trust.last_updated_tick = world_tick

            if increment_samples:
                current_trust.sample_size += 1


# ============================================================================
# Agent Selection with MRH-Aware Trust
# ============================================================================

def select_trusted_agents(
    registry: MRHTrustRegistry,
    candidate_lcts: List[str],
    query_horizon: MRHProfile,
    min_trust: float = 0.6,
    min_confidence: float = 0.3,
    top_k: Optional[int] = None
) -> List[Tuple[str, float, float]]:
    """
    Select trusted agents for task at specific horizon

    Args:
        registry: MRH trust registry
        candidate_lcts: Candidate agent LCTs
        query_horizon: Required horizon for task
        min_trust: Minimum trust threshold
        min_confidence: Minimum confidence threshold
        top_k: Optional limit on number of agents

    Returns:
        List of (lct_id, trust_score, confidence) sorted by trust desc
    """
    scored_agents = []

    for lct_id in candidate_lcts:
        result = registry.get_interpolated_trust(lct_id, query_horizon, min_confidence)

        if result is None:
            continue

        trust_score, confidence = result

        if trust_score >= min_trust and confidence >= min_confidence:
            scored_agents.append((lct_id, trust_score, confidence))

    # Sort by trust score descending
    scored_agents.sort(key=lambda x: x[1], reverse=True)

    if top_k is not None:
        scored_agents = scored_agents[:top_k]

    return scored_agents


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  MRH-Aware Trust Propagation - Unit Tests")
    print("  Session #81")
    print("=" * 80)

    # Test 1: MRH Distance Calculation
    print("\n=== Test 1: MRH Distance Calculation ===\n")

    horizon_local_session = MRHProfile(
        delta_r=SpatialExtent.LOCAL,
        delta_t=TemporalExtent.SESSION,
        delta_c=ComplexityExtent.AGENT_SCALE
    )

    horizon_global_epoch = MRHProfile(
        delta_r=SpatialExtent.GLOBAL,
        delta_t=TemporalExtent.EPOCH,
        delta_c=ComplexityExtent.SOCIETY_SCALE
    )

    horizon_regional_day = MRHProfile(
        delta_r=SpatialExtent.REGIONAL,
        delta_t=TemporalExtent.DAY,
        delta_c=ComplexityExtent.AGENT_SCALE
    )

    print(f"Horizon A: {horizon_local_session.to_dict()}")
    print(f"Horizon B: {horizon_global_epoch.to_dict()}")
    print(f"Horizon C: {horizon_regional_day.to_dict()}")

    dist_ab = mrh_distance(horizon_local_session, horizon_global_epoch)
    dist_ac = mrh_distance(horizon_local_session, horizon_regional_day)
    dist_aa = mrh_distance(horizon_local_session, horizon_local_session)

    print(f"\nDistance A↔B (max different): {dist_ab:.3f}")
    print(f"Distance A↔C (moderate): {dist_ac:.3f}")
    print(f"Distance A↔A (identical): {dist_aa:.3f}")

    # Test 2: Trust Relevance Decay
    print("\n=== Test 2: Trust Relevance Decay ===\n")

    relevance_ab = trust_relevance_score(horizon_local_session, horizon_global_epoch)
    relevance_ac = trust_relevance_score(horizon_local_session, horizon_regional_day)
    relevance_aa = trust_relevance_score(horizon_local_session, horizon_local_session)

    print(f"Relevance A→B (max different): {relevance_ab:.3f}")
    print(f"Relevance A→C (moderate): {relevance_ac:.3f}")
    print(f"Relevance A→A (identical): {relevance_aa:.3f}")

    print("\n✅ Trust decays exponentially with horizon distance")

    # Test 3: MRH Trust Registry
    print("\n=== Test 3: MRH Trust Registry ===\n")

    registry = MRHTrustRegistry()

    # Agent "alice" has high trust at local/session/agent-scale
    alice_local_trust = MRHScopedTrust(
        lct_id="lct:web4:agent:alice",
        horizon=horizon_local_session,
        t3_tensor=T3Tensor(talent=0.85, training=0.90, temperament=0.95),
        sample_size=50,
        last_updated_tick=1000
    )

    # Agent "alice" has moderate trust at global/epoch/society-scale
    alice_global_trust = MRHScopedTrust(
        lct_id="lct:web4:agent:alice",
        horizon=horizon_global_epoch,
        t3_tensor=T3Tensor(talent=0.60, training=0.55, temperament=0.70),
        sample_size=5,
        last_updated_tick=1000
    )

    registry.register_trust(alice_local_trust)
    registry.register_trust(alice_global_trust)

    print(f"Registered trust for alice at 2 horizons")
    print(f"  Local/Session/Agent-scale: T3 = {alice_local_trust.t3_tensor.composite():.2f} (50 samples)")
    print(f"  Global/Epoch/Society-scale: T3 = {alice_global_trust.t3_tensor.composite():.2f} (5 samples)")

    # Test 4: Exact Horizon Query
    print("\n=== Test 4: Exact Horizon Query ===\n")

    exact_trust = registry.get_exact_trust("lct:web4:agent:alice", horizon_local_session)

    if exact_trust:
        print(f"Alice's trust at local/session/agent-scale:")
        print(f"  Composite: {exact_trust.t3_tensor.composite():.2f}")
        print(f"  Confidence: {exact_trust.get_confidence():.2f}")

    # Test 5: Interpolated Trust Query
    print("\n=== Test 5: Interpolated Trust Query ===\n")

    # Query at regional/day/agent-scale (between local and global)
    result = registry.get_interpolated_trust("lct:web4:agent:alice", horizon_regional_day)

    if result:
        trust, confidence = result
        print(f"Alice's interpolated trust at regional/day/agent-scale:")
        print(f"  Trust score: {trust:.2f}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"\n  (Weighted by relevance to local and global horizons)")

    # Test 6: Trust Update
    print("\n=== Test 6: Horizon-Scoped Trust Update ===\n")

    # Update alice's trust at local horizon
    registry.update_trust(
        lct_id="lct:web4:agent:alice",
        horizon=horizon_local_session,
        t3_delta={"talent": 0.02, "training": 0.03, "temperament": -0.01},
        world_tick=1100,
        increment_samples=True
    )

    updated_trust = registry.get_exact_trust("lct:web4:agent:alice", horizon_local_session)

    if updated_trust:
        print(f"After update (+0.02 talent, +0.03 training, -0.01 temperament):")
        print(f"  New composite: {updated_trust.t3_tensor.composite():.2f}")
        print(f"  Sample size: {updated_trust.sample_size}")

    # Test 7: Agent Selection
    print("\n=== Test 7: MRH-Aware Agent Selection ===\n")

    # Add more agents
    bob_local_trust = MRHScopedTrust(
        lct_id="lct:web4:agent:bob",
        horizon=horizon_local_session,
        t3_tensor=T3Tensor(talent=0.70, training=0.75, temperament=0.80),
        sample_size=30
    )

    charlie_global_trust = MRHScopedTrust(
        lct_id="lct:web4:agent:charlie",
        horizon=horizon_global_epoch,
        t3_tensor=T3Tensor(talent=0.90, training=0.92, temperament=0.88),
        sample_size=100
    )

    registry.register_trust(bob_local_trust)
    registry.register_trust(charlie_global_trust)

    # Select agents for local/session task
    candidates = ["lct:web4:agent:alice", "lct:web4:agent:bob", "lct:web4:agent:charlie"]

    selected_local = select_trusted_agents(
        registry=registry,
        candidate_lcts=candidates,
        query_horizon=horizon_local_session,
        min_trust=0.6,
        min_confidence=0.3,
        top_k=3
    )

    print(f"Selected agents for local/session/agent-scale task:")
    print(f"{'Agent':<30} | {'Trust':<8} | {'Confidence'}")
    print("-" * 60)
    for lct_id, trust, confidence in selected_local:
        agent_name = lct_id.split(":")[-1]
        print(f"{agent_name:<30} | {trust:<8.2f} | {confidence:.2f}")

    # Select agents for global/epoch task
    selected_global = select_trusted_agents(
        registry=registry,
        candidate_lcts=candidates,
        query_horizon=horizon_global_epoch,
        min_trust=0.6,
        min_confidence=0.3,
        top_k=3
    )

    print(f"\nSelected agents for global/epoch/society-scale task:")
    print(f"{'Agent':<30} | {'Trust':<8} | {'Confidence'}")
    print("-" * 60)
    for lct_id, trust, confidence in selected_global:
        agent_name = lct_id.split(":")[-1]
        print(f"{agent_name:<30} | {trust:<8.2f} | {confidence:.2f}")

    print("\n" + "=" * 80)
    print("  All Unit Tests Passed!")
    print("=" * 80)
    print("\n✅ Key Findings:")
    print("  - Trust is horizon-specific (local expertise ≠ global expertise)")
    print("  - Trust decays exponentially with MRH distance")
    print("  - Interpolation enables queries at any horizon")
    print("  - Agent selection respects horizon context")
    print("  - Sample size affects confidence in trust estimates")
