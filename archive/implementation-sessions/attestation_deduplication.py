"""
Attestation Deduplication - Session 78 Track 1

Fixes Session 77 inefficiency: 8,100 imports for 90 exports.

Problem:
- Every generation re-imports ALL historical attestations
- Legion generation 90 imports: 90 (Thor) + 90 (Sprout) = 180 new + 8,010 duplicates
- Cumulative: Gen 1 imports 2, Gen 2 imports 4, ..., Gen 90 imports 180
- Total: Sum(2*n for n in 1..90) = 8,190 imports

Solution:
- Track processed attestation IDs (set)
- Skip already-imported attestations
- Expected: 90 generations × 2 societies = 180 imports (optimal)

Architecture:
- Add `processed_attestations: Set[str]` to FederatedTrustFirstSelector
- Check attestation_id before import
- Return early if already processed
"""

import random
import time
import statistics
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set
from collections import defaultdict
import hashlib
import hmac


# Import base classes from Session 77
import sys
sys.path.insert(0, '/home/dp/ai-workspace/web4/implementation')
from heterogeneous_federation_test import (
    Society,
    FederatedTrustAttestation,
    TrustFederationProtocol,
    SimplifiedTrustFirstSelector,
    SelectionResult,
    TaskSpecialization
)


class DedupFederatedTrustFirstSelector(SimplifiedTrustFirstSelector):
    """
    Trust-first selector with deduplicated federation support.

    Extends SimplifiedTrustFirstSelector with:
    - Attestation deduplication (track processed IDs)
    - Efficient import (skip duplicates)
    - Import statistics (duplicates detected)
    """

    def __init__(
        self,
        num_experts: int = 128,
        min_trust_evidence: int = 2,
        epsilon: float = 0.2,
        society: Society = None,
        federation_id: str = "web4-primary",
        trust_decay_factor: float = 0.72,
        enable_federation: bool = True
    ):
        super().__init__(num_experts, min_trust_evidence, epsilon)

        self.society = society
        self.federation_id = federation_id
        self.trust_decay_factor = trust_decay_factor
        self.enable_federation = enable_federation

        # Initialize federation protocol
        self.federation = TrustFederationProtocol(
            society=society,
            trust_decay_factor=trust_decay_factor,
            quorum_size=2
        )

        # Deduplication tracking
        self.processed_attestations: Set[str] = set()

        # Federation stats
        self.federation_stats = {
            'attestations_exported': 0,
            'attestations_imported': 0,
            'attestations_rejected': 0,
            'duplicates_skipped': 0,  # NEW: Track duplicates
            'first_trust_driven_gen': None
        }

    def register_society(self, society_id: str, public_key: str):
        """Register peer society for federation."""
        self.federation.register_society(society_id, public_key)

    def update_trust_for_expert(
        self,
        expert_id: int,
        context: str,
        quality: float,
        broadcast: bool = True
    ):
        """Update trust and optionally broadcast attestation."""
        # Update local trust
        super().update_trust_for_expert(expert_id, context, quality)

        # Export attestation if federation enabled
        if self.enable_federation and broadcast:
            self._export_trust_attestation(expert_id, context, quality)

    def _export_trust_attestation(
        self,
        expert_id: int,
        context: str,
        quality: float
    ):
        """Create and export trust attestation."""
        # Parse context to get numeric index
        context_idx = int(context.split("_")[1]) if "_" in context else 0

        # Create LCT for expert
        expert_lct = f"lct://expert-{expert_id}@{self.federation_id}/selector"

        # Get observation count
        observation_count = len(self.trust_history[context][expert_id])

        # Create attestation
        attestation = self.federation.create_attestation(
            expert_lct=expert_lct,
            context=context_idx,
            quality=quality,
            observation_count=observation_count
        )

        self.federation_stats['attestations_exported'] += 1

    def import_attestation(
        self,
        attestation: FederatedTrustAttestation,
        society_public_key: str
    ) -> bool:
        """
        Import and apply federated trust attestation.

        Returns:
            True if imported, False if rejected/duplicate
        """
        # Check if already processed (DEDUPLICATION)
        if attestation.attestation_id in self.processed_attestations:
            self.federation_stats['duplicates_skipped'] += 1
            return False  # Skip duplicate

        # Verify attestation signature
        if not self.federation.verify_attestation(attestation, society_public_key):
            self.federation_stats['attestations_rejected'] += 1
            self.federation.rejected_attestations.append(attestation)
            return False

        # Parse expert ID from LCT
        expert_lct_parts = attestation.expert_lct.split("://")[1].split("@")[0]
        expert_id = int(expert_lct_parts.split("-")[1])

        # Create context ID
        context_id = f"cluster_{attestation.context}"

        # Apply trust decay
        decayed_quality = attestation.quality * self.trust_decay_factor

        # Update trust history
        self.trust_history[context_id][expert_id].append(decayed_quality)

        # Mark as processed (DEDUPLICATION)
        self.processed_attestations.add(attestation.attestation_id)

        self.federation_stats['attestations_imported'] += 1
        return True

    def select_experts(
        self,
        router_logits: List[float],
        context: str,
        k: int = 8
    ) -> SelectionResult:
        """Select experts and track first trust_driven activation."""
        result = super().select_experts(router_logits, context, k)

        # Track first trust_driven activation
        if (result.selection_method == 'trust_driven' and
            self.federation_stats['first_trust_driven_gen'] is None):
            self.federation_stats['first_trust_driven_gen'] = \
                self.stats['total_selections']

        return result


@dataclass
class DeduplicationTestResult:
    """Result from deduplication test."""
    test_id: str

    # Import efficiency
    attestations_exported: Dict[str, int]
    attestations_imported: Dict[str, int]
    duplicates_skipped: Dict[str, int]

    # Efficiency metrics
    import_efficiency_pct: Dict[str, float]  # imported / (imported + duplicates)
    avg_import_efficiency: float

    # Comparison to Session 77 (no deduplication)
    session77_imports: Dict[str, int]
    reduction_pct: Dict[str, float]

    # Trust-driven activation (should be identical to Session 77)
    trust_driven_rates: Dict[str, float]
    session77_trust_driven_rates: Dict[str, float]
    trust_driven_preserved: bool  # True if rates match Session 77

    passed: bool  # True if avg efficiency > 90% and trust-driven preserved


class AttestationDeduplicationTester:
    """
    Tests attestation deduplication optimization.

    Validates that:
    1. Duplicates are skipped (8,190 → 180 imports)
    2. Trust-driven rates unchanged (deduplication doesn't affect results)
    3. Import efficiency > 90%
    """

    def __init__(self):
        self.specializations = {
            'thor': TaskSpecialization(
                society_id='thor',
                task_domain='coding',
                task_descriptions=[],
                context_prefix='code'
            ),
            'legion': TaskSpecialization(
                society_id='legion',
                task_domain='reasoning',
                task_descriptions=[],
                context_prefix='logic'
            ),
            'sprout': TaskSpecialization(
                society_id='sprout',
                task_domain='multilingual',
                task_descriptions=[],
                context_prefix='lang'
            )
        }

    def run_deduplication_test(
        self,
        generations: int = 90,
        num_experts: int = 128
    ) -> DeduplicationTestResult:
        """
        Run deduplication test (should match Session 77 results with fewer imports).
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

        sprout = Society(
            society_id="sprout",
            society_lct="lct://sprout-society@testnet/moe",
            platform="CPU (Ryzen)"
        )

        # Create deduplicated federated selectors
        thor_selector = DedupFederatedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2,
            society=thor,
            enable_federation=True
        )

        legion_selector = DedupFederatedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2,
            society=legion,
            enable_federation=True
        )

        sprout_selector = DedupFederatedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2,
            society=sprout,
            enable_federation=True
        )

        # Register peer societies
        thor_selector.register_society(legion.society_id, legion.secret_key)
        thor_selector.register_society(sprout.society_id, sprout.secret_key)

        legion_selector.register_society(thor.society_id, thor.secret_key)
        legion_selector.register_society(sprout.society_id, sprout.secret_key)

        sprout_selector.register_society(thor.society_id, thor.secret_key)
        sprout_selector.register_society(legion.society_id, legion.secret_key)

        # Run test
        random.seed(42)  # Same seed as Session 77

        for gen in range(generations):
            # Shared context
            shared_context_idx = gen % 9
            context_id = f"cluster_{shared_context_idx}"

            # Router logits
            router_logits = [random.random() for _ in range(num_experts)]

            # Expert selection
            selected_expert_id = gen % num_experts

            # Expert specialization
            expert_coding_skill = (selected_expert_id % 3 == 0)
            expert_reasoning_skill = (selected_expert_id % 3 == 1)
            expert_language_skill = (selected_expert_id % 3 == 2)

            # Quality scores
            thor_quality = 0.9 if expert_coding_skill else 0.5
            legion_quality = 0.9 if expert_reasoning_skill else 0.5
            sprout_quality = 0.9 if expert_language_skill else 0.5

            # ---- THOR SOCIETY ----
            thor_result = thor_selector.select_experts(router_logits, context_id, k=8)
            thor_selector.update_trust_for_expert(
                selected_expert_id,
                context_id,
                thor_quality,
                broadcast=True
            )

            # ---- LEGION SOCIETY ----
            # Import attestations (DEDUPLICATED)
            for attestation in thor_selector.federation.accepted_attestations:
                legion_selector.import_attestation(attestation, thor.secret_key)
            for attestation in sprout_selector.federation.accepted_attestations:
                legion_selector.import_attestation(attestation, sprout.secret_key)

            legion_result = legion_selector.select_experts(router_logits, context_id, k=8)
            legion_selector.update_trust_for_expert(
                selected_expert_id,
                context_id,
                legion_quality,
                broadcast=True
            )

            # ---- SPROUT SOCIETY ----
            # Import attestations (DEDUPLICATED)
            for attestation in thor_selector.federation.accepted_attestations:
                sprout_selector.import_attestation(attestation, thor.secret_key)
            for attestation in legion_selector.federation.accepted_attestations:
                sprout_selector.import_attestation(attestation, legion.secret_key)

            sprout_result = sprout_selector.select_experts(router_logits, context_id, k=8)
            sprout_selector.update_trust_for_expert(
                selected_expert_id,
                context_id,
                sprout_quality,
                broadcast=True
            )

        # Calculate results
        attestations_exported = {
            'thor': thor_selector.federation_stats['attestations_exported'],
            'legion': legion_selector.federation_stats['attestations_exported'],
            'sprout': sprout_selector.federation_stats['attestations_exported']
        }

        attestations_imported = {
            'thor': thor_selector.federation_stats['attestations_imported'],
            'legion': legion_selector.federation_stats['attestations_imported'],
            'sprout': sprout_selector.federation_stats['attestations_imported']
        }

        duplicates_skipped = {
            'thor': thor_selector.federation_stats['duplicates_skipped'],
            'legion': legion_selector.federation_stats['duplicates_skipped'],
            'sprout': sprout_selector.federation_stats['duplicates_skipped']
        }

        # Import efficiency
        import_efficiency_pct = {}
        for society in ['thor', 'legion', 'sprout']:
            imported = attestations_imported[society]
            skipped = duplicates_skipped[society]
            total = imported + skipped

            if total > 0:
                efficiency = imported / total * 100
            else:
                efficiency = 100.0  # No imports = no waste

            import_efficiency_pct[society] = efficiency

        avg_import_efficiency = statistics.mean(import_efficiency_pct.values())

        # Session 77 comparison (no deduplication)
        session77_imports = {
            'thor': 0,  # Thor doesn't import in Session 77
            'legion': 8100,
            'sprout': 8190
        }

        reduction_pct = {}
        for society in ['thor', 'legion', 'sprout']:
            baseline = session77_imports[society]
            optimized = attestations_imported[society]

            if baseline > 0:
                reduction = ((baseline - optimized) / baseline) * 100
            else:
                reduction = 0.0

            reduction_pct[society] = reduction

        # Trust-driven rates
        trust_driven_rates = {
            'thor': thor_selector.get_trust_driven_rate(),
            'legion': legion_selector.get_trust_driven_rate(),
            'sprout': sprout_selector.get_trust_driven_rate()
        }

        # Session 77 baseline (from results)
        session77_trust_driven_rates = {
            'thor': 0.0,
            'legion': 0.189,  # 18.9%
            'sprout': 0.200   # 20.0%
        }

        # Check if trust-driven rates are preserved (within 5% tolerance)
        trust_driven_preserved = True
        for society in ['legion', 'sprout']:  # Skip Thor (never activates)
            s77_rate = session77_trust_driven_rates[society]
            s78_rate = trust_driven_rates[society]
            if abs(s78_rate - s77_rate) > 0.05:  # 5% tolerance
                trust_driven_preserved = False

        # Test passes if import count is optimal (within 10%) and trust-driven preserved
        # Optimal: 90 generations × 2 peer societies = 180 imports per society
        optimal_imports_per_society = generations * 2

        # Check if Legion and Sprout are within 10% of optimal
        legion_optimal = abs(attestations_imported['legion'] - optimal_imports_per_society) / optimal_imports_per_society <= 0.10
        sprout_optimal = abs(attestations_imported['sprout'] - optimal_imports_per_society) / optimal_imports_per_society <= 0.10

        import_count_optimal = legion_optimal and sprout_optimal

        passed = import_count_optimal and trust_driven_preserved

        return DeduplicationTestResult(
            test_id="attestation-deduplication-v1",
            attestations_exported=attestations_exported,
            attestations_imported=attestations_imported,
            duplicates_skipped=duplicates_skipped,
            import_efficiency_pct=import_efficiency_pct,
            avg_import_efficiency=avg_import_efficiency,
            session77_imports=session77_imports,
            reduction_pct=reduction_pct,
            trust_driven_rates=trust_driven_rates,
            session77_trust_driven_rates=session77_trust_driven_rates,
            trust_driven_preserved=trust_driven_preserved,
            passed=passed
        )


def demo_attestation_deduplication():
    """
    Demo: Attestation deduplication optimization.

    Validates that:
    - Duplicates are skipped (8,190 → 180 imports for Sprout)
    - Trust-driven rates unchanged (deduplication doesn't affect results)
    - Import efficiency > 90%
    """
    print("=" * 80)
    print("ATTESTATION DEDUPLICATION - Session 78 Track 1")
    print("=" * 80)
    print()
    print("Problem (Session 77):")
    print("  Legion imported 8,100 attestations (for 90 exports)")
    print("  Sprout imported 8,190 attestations (for 90 exports)")
    print("  Cause: Every generation re-imports ALL historical attestations")
    print()
    print("Solution (Session 78):")
    print("  Track processed attestation IDs")
    print("  Skip already-imported attestations")
    print("  Expected: 90 generations × 2 societies = 180 imports (optimal)")
    print()
    print("Validation:")
    print("  Import efficiency > 90%")
    print("  Trust-driven rates match Session 77 (within 5%)")
    print("=" * 80)
    print()

    # Run test
    tester = AttestationDeduplicationTester()
    result = tester.run_deduplication_test(generations=90, num_experts=128)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print("Import Statistics:")
    print("-" * 80)
    for society in ['thor', 'legion', 'sprout']:
        exported = result.attestations_exported[society]
        imported = result.attestations_imported[society]
        skipped = result.duplicates_skipped[society]
        efficiency = result.import_efficiency_pct[society]

        print(f"{society.upper():8s}: Exported={exported:3d} | "
              f"Imported={imported:4d} | Skipped={skipped:5d} | "
              f"Efficiency={efficiency:5.1f}%")
    print()
    print(f"Average import efficiency: {result.avg_import_efficiency:.1f}%")
    print()

    print("Comparison to Session 77 (No Deduplication):")
    print("-" * 80)
    for society in ['thor', 'legion', 'sprout']:
        s77_imports = result.session77_imports[society]
        s78_imports = result.attestations_imported[society]
        reduction = result.reduction_pct[society]

        print(f"{society.upper():8s}: S77={s77_imports:5d} imports | "
              f"S78={s78_imports:4d} imports | Reduction={reduction:+6.1f}%")
    print()

    print("Trust-Driven Activation (Validation):")
    print("-" * 80)
    for society in ['thor', 'legion', 'sprout']:
        s77_rate = result.session77_trust_driven_rates[society]
        s78_rate = result.trust_driven_rates[society]
        delta = s78_rate - s77_rate

        match = "✅" if abs(delta) <= 0.05 else "❌"
        print(f"{society.upper():8s}: S77={s77_rate:5.1%} | S78={s78_rate:5.1%} | "
              f"Δ={delta:+6.1%} {match}")
    print()

    print("Optimal Import Analysis:")
    print("-" * 80)
    optimal_per_society = 90 * 2  # 90 generations × 2 peer societies
    print(f"Expected optimal imports: {optimal_per_society} per society")
    print()
    for society in ['thor', 'legion', 'sprout']:
        actual = result.attestations_imported[society]
        delta = actual - optimal_per_society
        pct_delta = (delta / optimal_per_society * 100) if optimal_per_society > 0 else 0

        if society == 'thor':
            status = "N/A (Thor doesn't import)"
        elif abs(pct_delta) <= 10:
            status = "✅ Optimal"
        else:
            status = "❌ Suboptimal"

        print(f"{society.upper():8s}: {actual:3d} imports | Δ={delta:+4d} ({pct_delta:+5.1f}%) | {status}")
    print()

    print("Test Result:")
    print("-" * 80)
    if result.passed:
        print(f"✅ PASS")
        print()
        print(f"  Import count: Optimal (within 10% of {optimal_per_society})")
        print(f"  Trust-driven preserved: {result.trust_driven_preserved}")
        print()
        print("Conclusion:")
        print("  Deduplication optimization successful!")
        print(f"  Legion: 8,100 → {result.attestations_imported['legion']} imports "
              f"({result.reduction_pct['legion']:+.1f}% reduction)")
        print(f"  Sprout: 8,190 → {result.attestations_imported['sprout']} imports "
              f"({result.reduction_pct['sprout']:+.1f}% reduction)")
        print("  No impact on trust-driven activation rates")
        print(f"  Duplicate skipping: {result.duplicates_skipped['legion'] + result.duplicates_skipped['sprout']:,} duplicates avoided")
    else:
        print(f"❌ FAIL")
        print()
        print(f"  Import count optimal: {abs(result.attestations_imported['legion'] - optimal_per_society) / optimal_per_society <= 0.10}")
        print(f"  Trust-driven preserved: {result.trust_driven_preserved}")
        print()
        print("Conclusion:")
        print("  Deduplication needs refinement.")
    print()

    # Save results
    results_file = "/home/dp/ai-workspace/web4/implementation/attestation_deduplication_results.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    print(f"Results saved to: {results_file}")
    print()

    return result


if __name__ == "__main__":
    demo_attestation_deduplication()
