"""
Dynamic Trust Decay - Session 78 Track 3

Adjusts trust decay based on observation diversity (Session 77/83 insight).

Current Limitation (Sessions 70-77):
- Fixed 72% decay rate (Session 70 validated)
- Same decay regardless of observation diversity
- Treats all federated trust equally

Session 77/83 Insight:
- Session 83: 0% benefit with identical observations (high overlap)
- Session 77: +13% benefit with diverse observations (low overlap)
- Observation diversity determines federation value

Dynamic Decay Solution:
- High diversity (complementary) → Low decay (0.85-0.95) - trust more valuable
- Low diversity (redundant) → High decay (0.50-0.70) - trust less valuable
- Measure diversity via observation overlap metrics

Observation Overlap Metrics:
1. Context overlap: % of shared contexts
2. Expert overlap: % of same experts selected
3. Quality correlation: Correlation between quality observations
4. Composite: Weighted combination

Dynamic Decay Formula:
  decay = base_decay + (1 - base_decay) * (1 - overlap)

  Examples:
  - 0% overlap (perfect diversity): decay = 0.72 + 0.28 * 1.0 = 1.00 (no decay!)
  - 50% overlap (moderate diversity): decay = 0.72 + 0.28 * 0.5 = 0.86
  - 100% overlap (identical): decay = 0.72 + 0.28 * 0.0 = 0.72 (original)
"""

import random
import statistics
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Tuple
from collections import defaultdict


# Import base classes from previous sessions
import sys
sys.path.insert(0, '/home/dp/ai-workspace/web4/implementation')
from attestation_deduplication import (
    DedupFederatedTrustFirstSelector,
    Society,
    SimplifiedTrustFirstSelector,
    SelectionResult,
    TaskSpecialization
)


@dataclass
class ObservationOverlapMetrics:
    """Metrics for measuring observation overlap between societies."""
    society_a: str
    society_b: str

    # Overlap metrics
    context_overlap: float  # % of shared contexts
    expert_overlap: float   # % of same experts selected
    quality_correlation: float  # Correlation of quality observations

    # Composite
    composite_overlap: float  # Weighted combination
    diversity_score: float  # 1 - composite_overlap


class DynamicDecayFederatedSelector(DedupFederatedTrustFirstSelector):
    """
    Federated selector with dynamic trust decay based on observation diversity.

    Extends DedupFederatedTrustFirstSelector with:
    - Observation overlap tracking
    - Dynamic decay calculation
    - Diversity-aware trust import
    """

    def __init__(
        self,
        num_experts: int = 128,
        min_trust_evidence: int = 2,
        epsilon: float = 0.2,
        society: Society = None,
        federation_id: str = "web4-primary",
        base_decay_factor: float = 0.72,
        enable_dynamic_decay: bool = True,
        enable_federation: bool = True
    ):
        super().__init__(
            num_experts=num_experts,
            min_trust_evidence=min_trust_evidence,
            epsilon=epsilon,
            society=society,
            federation_id=federation_id,
            trust_decay_factor=base_decay_factor,  # Will be dynamic
            enable_federation=enable_federation
        )

        self.base_decay_factor = base_decay_factor
        self.enable_dynamic_decay = enable_dynamic_decay

        # Track observations for diversity calculation
        self.observations: Dict[str, List[Tuple[int, float]]] = defaultdict(list)  # context -> [(expert, quality)]

        # Track peer observations (for overlap calculation)
        self.peer_observations: Dict[str, Dict[str, List[Tuple[int, float]]]] = defaultdict(
            lambda: defaultdict(list)
        )  # peer_society -> context -> [(expert, quality)]

        # Dynamic decay stats
        self.dynamic_decay_stats = {
            'diversity_scores': [],
            'applied_decays': [],
            'avg_diversity': 0.0,
            'avg_decay': 0.72
        }

    def update_trust_for_expert(
        self,
        expert_id: int,
        context: str,
        quality: float,
        broadcast: bool = True
    ):
        """Update trust and track local observations."""
        # Update local trust
        super().update_trust_for_expert(expert_id, context, quality, broadcast)

        # Track observation
        self.observations[context].append((expert_id, quality))

    def import_attestation_with_dynamic_decay(
        self,
        attestation,
        society_public_key: str,
        peer_society_id: str
    ) -> bool:
        """
        Import attestation with dynamic decay based on observation diversity.

        Args:
            attestation: Trust attestation to import
            society_public_key: Public key for verification
            peer_society_id: ID of peer society for overlap calculation
        """
        # Check if already processed (deduplication)
        if attestation.attestation_id in self.processed_attestations:
            self.federation_stats['duplicates_skipped'] += 1
            return False

        # Verify signature
        if not self.federation.verify_attestation(attestation, society_public_key):
            self.federation_stats['attestations_rejected'] += 1
            return False

        # Parse expert and context
        expert_lct_parts = attestation.expert_lct.split("://")[1].split("@")[0]
        expert_id = int(expert_lct_parts.split("-")[1])
        context_id = f"cluster_{attestation.context}"

        # Track peer observation
        self.peer_observations[peer_society_id][context_id].append(
            (expert_id, attestation.quality)
        )

        # Calculate observation overlap (if dynamic decay enabled)
        if self.enable_dynamic_decay:
            overlap_metrics = self._calculate_overlap(peer_society_id)
            diversity_score = overlap_metrics.diversity_score

            # Dynamic decay formula
            # decay = base + (1 - base) * diversity
            # High diversity → Low decay (trust more valuable)
            # Low diversity → High decay (trust less valuable)
            dynamic_decay = self.base_decay_factor + (1 - self.base_decay_factor) * diversity_score

            # Track stats
            self.dynamic_decay_stats['diversity_scores'].append(diversity_score)
            self.dynamic_decay_stats['applied_decays'].append(dynamic_decay)
            self.dynamic_decay_stats['avg_diversity'] = statistics.mean(
                self.dynamic_decay_stats['diversity_scores']
            )
            self.dynamic_decay_stats['avg_decay'] = statistics.mean(
                self.dynamic_decay_stats['applied_decays']
            )
        else:
            # Fixed decay (Session 70 baseline)
            dynamic_decay = self.base_decay_factor

        # Apply dynamic decay
        decayed_quality = attestation.quality * dynamic_decay

        # Update trust history
        self.trust_history[context_id][expert_id].append(decayed_quality)

        # Mark as processed
        self.processed_attestations.add(attestation.attestation_id)

        self.federation_stats['attestations_imported'] += 1
        return True

    def _calculate_overlap(self, peer_society_id: str) -> ObservationOverlapMetrics:
        """
        Calculate observation overlap with peer society.

        Returns diversity metrics for dynamic decay calculation.
        """
        # Get local and peer observations
        local_obs = self.observations
        peer_obs = self.peer_observations[peer_society_id]

        # 1. Context overlap (% of shared contexts)
        local_contexts = set(local_obs.keys())
        peer_contexts = set(peer_obs.keys())

        if len(local_contexts) > 0 and len(peer_contexts) > 0:
            shared_contexts = local_contexts & peer_contexts
            context_overlap = len(shared_contexts) / len(local_contexts | peer_contexts)
        else:
            context_overlap = 0.0

        # 2. Expert overlap (% of same experts selected in shared contexts)
        expert_overlap_per_context = []
        for context in (local_contexts & peer_contexts):
            local_experts = set(e for e, q in local_obs[context])
            peer_experts = set(e for e, q in peer_obs[context])

            if len(local_experts) > 0 and len(peer_experts) > 0:
                shared_experts = local_experts & peer_experts
                overlap = len(shared_experts) / len(local_experts | peer_experts)
                expert_overlap_per_context.append(overlap)

        expert_overlap = statistics.mean(expert_overlap_per_context) if expert_overlap_per_context else 0.0

        # 3. Quality correlation (for same expert-context pairs)
        quality_pairs = []
        for context in (local_contexts & peer_contexts):
            local_dict = {e: q for e, q in local_obs[context]}
            peer_dict = {e: q for e, q in peer_obs[context]}

            shared_experts = set(local_dict.keys()) & set(peer_dict.keys())
            for expert in shared_experts:
                quality_pairs.append((local_dict[expert], peer_dict[expert]))

        if len(quality_pairs) >= 2:
            local_qualities = [q1 for q1, q2 in quality_pairs]
            peer_qualities = [q2 for q1, q2 in quality_pairs]

            # Pearson correlation
            mean_local = statistics.mean(local_qualities)
            mean_peer = statistics.mean(peer_qualities)

            numerator = sum((l - mean_local) * (p - mean_peer)
                          for l, p in zip(local_qualities, peer_qualities))
            denom_local = sum((l - mean_local) ** 2 for l in local_qualities)
            denom_peer = sum((p - mean_peer) ** 2 for p in peer_qualities)

            if denom_local > 0 and denom_peer > 0:
                correlation = numerator / (denom_local * denom_peer) ** 0.5
                # Convert to [0, 1] range (correlation is [-1, 1])
                quality_correlation = (correlation + 1) / 2
            else:
                quality_correlation = 0.5  # Neutral
        else:
            quality_correlation = 0.5  # Neutral (not enough data)

        # Composite overlap (weighted combination)
        composite_overlap = (
            context_overlap * 0.3 +
            expert_overlap * 0.4 +
            quality_correlation * 0.3
        )

        # Diversity score (inverse of overlap)
        diversity_score = 1 - composite_overlap

        return ObservationOverlapMetrics(
            society_a=self.society.society_id,
            society_b=peer_society_id,
            context_overlap=context_overlap,
            expert_overlap=expert_overlap,
            quality_correlation=quality_correlation,
            composite_overlap=composite_overlap,
            diversity_score=diversity_score
        )


@dataclass
class DynamicDecayTestResult:
    """Result from dynamic decay test."""
    test_id: str

    # Diversity metrics
    avg_diversity_score: float
    avg_applied_decay: float

    # Trust-driven comparison
    fixed_decay_trust_driven: Dict[str, float]
    dynamic_decay_trust_driven: Dict[str, float]
    improvement_pct: Dict[str, float]

    # Validation
    heterogeneous_benefit_increase: float  # Should be > 0 for heterogeneous
    homogeneous_benefit_stable: bool  # Should be ~0 for homogeneous

    passed: bool


class DynamicDecayTester:
    """Tests dynamic trust decay based on observation diversity."""

    def __init__(self):
        pass

    def run_test(
        self,
        generations: int = 90,
        num_experts: int = 128,
        scenario: str = "heterogeneous"  # or "homogeneous"
    ) -> DynamicDecayTestResult:
        """
        Test dynamic decay in heterogeneous vs homogeneous scenarios.

        Heterogeneous: Diverse observations → High diversity → Low decay → Better performance
        Homogeneous: Identical observations → Low diversity → High decay → Similar performance
        """
        # Create societies
        thor = Society(
            society_id="thor",
            society_lct="lct://thor-society@testnet/moe",
            platform="Jetson AGX Thor"
        )

        legion = Society(
            society_id="legion",
            society_lct="lct://legion-society@testnet/moe",
            platform="RTX 4090"
        )

        # Fixed decay baseline
        legion_fixed = DedupFederatedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2,
            society=legion,
            enable_federation=True
        )

        # Dynamic decay test
        legion_dynamic = DynamicDecayFederatedSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2,
            society=legion,
            enable_dynamic_decay=True,
            enable_federation=True
        )

        legion_fixed.register_society(thor.society_id, thor.secret_key)
        legion_dynamic.register_society(thor.society_id, thor.secret_key)

        # Thor selector (shared)
        thor_selector = DedupFederatedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2,
            society=thor,
            enable_federation=True
        )

        # Run test
        random.seed(42)

        for gen in range(generations):
            context_id = f"cluster_{gen % 9}"
            router_logits = [random.random() for _ in range(num_experts)]
            selected_expert_id = gen % num_experts

            # Quality determination based on scenario
            if scenario == "heterogeneous":
                # Diverse observations (Session 77)
                expert_coding_skill = (selected_expert_id % 3 == 0)
                expert_reasoning_skill = (selected_expert_id % 3 == 1)

                thor_quality = 0.9 if expert_coding_skill else 0.5
                legion_quality = 0.9 if expert_reasoning_skill else 0.5
            else:  # homogeneous
                # Identical observations (Session 83)
                quality = random.uniform(0.6, 1.0)
                thor_quality = quality
                legion_quality = quality

            # Thor
            thor_selector.select_experts(router_logits, context_id, k=8)
            thor_selector.update_trust_for_expert(
                selected_expert_id, context_id, thor_quality, broadcast=True
            )

            # Legion (fixed decay)
            for attestation in thor_selector.federation.accepted_attestations:
                legion_fixed.import_attestation(attestation, thor.secret_key)

            legion_fixed.select_experts(router_logits, context_id, k=8)
            legion_fixed.update_trust_for_expert(
                selected_expert_id, context_id, legion_quality, broadcast=True
            )

            # Legion (dynamic decay)
            for attestation in thor_selector.federation.accepted_attestations:
                legion_dynamic.import_attestation_with_dynamic_decay(
                    attestation, thor.secret_key, thor.society_id
                )

            legion_dynamic.select_experts(router_logits, context_id, k=8)
            legion_dynamic.update_trust_for_expert(
                selected_expert_id, context_id, legion_quality, broadcast=True
            )

        # Results
        fixed_trust_driven = legion_fixed.get_trust_driven_rate()
        dynamic_trust_driven = legion_dynamic.get_trust_driven_rate()

        improvement = ((dynamic_trust_driven - fixed_trust_driven) / max(fixed_trust_driven, 0.01)) * 100

        # Get diversity metrics
        avg_diversity = legion_dynamic.dynamic_decay_stats['avg_diversity']
        avg_decay = legion_dynamic.dynamic_decay_stats['avg_decay']

        # Validation criteria
        if scenario == "heterogeneous":
            # Should see benefit increase (higher trust-driven with dynamic decay)
            heterogeneous_benefit_increase = improvement
            homogeneous_benefit_stable = False
            passed = improvement > 5  # At least 5% improvement
        else:  # homogeneous
            # Should see minimal change (dynamic decay ≈ fixed decay)
            heterogeneous_benefit_increase = 0.0
            homogeneous_benefit_stable = abs(improvement) < 5  # Within 5%
            passed = homogeneous_benefit_stable

        return DynamicDecayTestResult(
            test_id=f"dynamic-decay-{scenario}",
            avg_diversity_score=avg_diversity,
            avg_applied_decay=avg_decay,
            fixed_decay_trust_driven={'legion': fixed_trust_driven},
            dynamic_decay_trust_driven={'legion': dynamic_trust_driven},
            improvement_pct={'legion': improvement},
            heterogeneous_benefit_increase=heterogeneous_benefit_increase,
            homogeneous_benefit_stable=homogeneous_benefit_stable,
            passed=passed
        )


def demo_dynamic_trust_decay():
    """
    Demo: Dynamic trust decay based on observation diversity.

    Tests two scenarios:
    1. Heterogeneous: Diverse observations → Dynamic decay should improve performance
    2. Homogeneous: Identical observations → Dynamic decay should match fixed decay
    """
    print("=" * 80)
    print("DYNAMIC TRUST DECAY - Session 78 Track 3")
    print("=" * 80)
    print()
    print("Insight (Sessions 77 & 83):")
    print("  Session 83: 0% benefit with identical observations (high overlap)")
    print("  Session 77: +13% benefit with diverse observations (low overlap)")
    print("  → Observation diversity determines federation value")
    print()
    print("Solution:")
    print("  Dynamic decay = base_decay + (1 - base_decay) * diversity")
    print("  High diversity → Low decay (trust more valuable)")
    print("  Low diversity → High decay (trust less valuable)")
    print()
    print("Test Scenarios:")
    print("  1. Heterogeneous: Diverse observations (Session 77)")
    print("  2. Homogeneous: Identical observations (Session 83)")
    print("=" * 80)
    print()

    tester = DynamicDecayTester()

    # Test 1: Heterogeneous
    print("\n" + "=" * 80)
    print("TEST 1: HETEROGENEOUS (Diverse Observations)")
    print("=" * 80)
    print()

    result_hetero = tester.run_test(generations=90, scenario="heterogeneous")

    print("Diversity Metrics:")
    print("-" * 80)
    print(f"Average diversity score: {result_hetero.avg_diversity_score:.3f}")
    print(f"Average applied decay:   {result_hetero.avg_applied_decay:.3f}")
    print(f"Fixed decay (baseline):  0.720")
    print()

    print("Trust-Driven Performance:")
    print("-" * 80)
    print(f"Fixed decay:    {result_hetero.fixed_decay_trust_driven['legion']:5.1%}")
    print(f"Dynamic decay:  {result_hetero.dynamic_decay_trust_driven['legion']:5.1%}")
    print(f"Improvement:    {result_hetero.improvement_pct['legion']:+5.1f}%")
    print()

    if result_hetero.passed:
        print("✅ PASS - Dynamic decay improves performance with diverse observations")
    else:
        print("❌ FAIL - Dynamic decay should improve performance")
    print()

    # Test 2: Homogeneous
    print("\n" + "=" * 80)
    print("TEST 2: HOMOGENEOUS (Identical Observations)")
    print("=" * 80)
    print()

    result_homo = tester.run_test(generations=90, scenario="homogeneous")

    print("Diversity Metrics:")
    print("-" * 80)
    print(f"Average diversity score: {result_homo.avg_diversity_score:.3f}")
    print(f"Average applied decay:   {result_homo.avg_applied_decay:.3f}")
    print(f"Fixed decay (baseline):  0.720")
    print()

    print("Trust-Driven Performance:")
    print("-" * 80)
    print(f"Fixed decay:    {result_homo.fixed_decay_trust_driven['legion']:5.1%}")
    print(f"Dynamic decay:  {result_homo.dynamic_decay_trust_driven['legion']:5.1%}")
    print(f"Improvement:    {result_homo.improvement_pct['legion']:+5.1f}%")
    print()

    if result_homo.passed:
        print("✅ PASS - Dynamic decay matches fixed decay with identical observations")
    else:
        print("❌ FAIL - Dynamic decay should match fixed decay")
    print()

    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print()
    print("Heterogeneous (diverse observations):")
    print(f"  Diversity score: {result_hetero.avg_diversity_score:.3f}")
    print(f"  Applied decay:   {result_hetero.avg_applied_decay:.3f} (vs 0.720 fixed)")
    print(f"  Improvement:     {result_hetero.improvement_pct['legion']:+.1f}%")
    print()
    print("Homogeneous (identical observations):")
    print(f"  Diversity score: {result_homo.avg_diversity_score:.3f}")
    print(f"  Applied decay:   {result_homo.avg_applied_decay:.3f} (vs 0.720 fixed)")
    print(f"  Improvement:     {result_homo.improvement_pct['legion']:+.1f}%")
    print()

    if result_hetero.passed and result_homo.passed:
        print("✅ OVERALL PASS - Dynamic decay adapts correctly to observation diversity")
        print()
        print("Conclusion:")
        print("  Dynamic decay successfully adjusts based on diversity:")
        print("  - Diverse observations: Lower decay, better performance")
        print("  - Identical observations: Higher decay, stable performance")
        print("  This validates Sessions 77/83 insight and provides adaptive federation.")
    else:
        print("❌ OVERALL FAIL - Dynamic decay needs refinement")
    print()

    # Save results
    results = {
        'heterogeneous': asdict(result_hetero),
        'homogeneous': asdict(result_homo)
    }
    results_file = "/home/dp/ai-workspace/web4/implementation/dynamic_trust_decay_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {results_file}")
    print()


if __name__ == "__main__":
    demo_dynamic_trust_decay()
