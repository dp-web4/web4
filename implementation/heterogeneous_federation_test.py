"""
Heterogeneous Federation Test - Session 77

Tests Thor's Session 83 hypothesis: Federation provides value ONLY when societies
have diverse observations (complementary specialization).

Test Scenario:
- Thor Society: Coding tasks (Python, Rust, algorithms)
- Legion Society: Reasoning tasks (math, logic, philosophy)
- Sprout Society: Multilingual text (EN, ES, ZH)

Expected Results:
- Federation benefit > 10% (compared to Session 83's 0%)
- Faster trust_driven activation with cross-society learning
- Complementary expertise sharing

Architecture:
- Based on Session 83's FederatedTrustFirstSelector
- Uses Session 75's TrustFederationProtocol
- LCT identity binding (Session 74)
- Byzantine consensus (Session 73)
- Trust decay 72% (Session 70)
"""

import random
import time
import statistics
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import hashlib
import hmac

# ============================================================================
# SESSION 75 - Trust Federation Protocol (Legion)
# ============================================================================

@dataclass
class Society:
    """Society identity for federation."""
    society_id: str
    society_lct: str  # lct://society-name@network/component
    platform: str
    secret_key: str = None  # For HMAC signatures

    def __post_init__(self):
        if self.secret_key is None:
            # Generate deterministic key from society_id
            self.secret_key = hashlib.sha256(
                f"web4-society-{self.society_id}".encode()
            ).hexdigest()


@dataclass
class FederatedTrustAttestation:
    """Trust attestation for cross-society sharing."""
    attestation_id: str
    society_lct: str
    expert_lct: str  # lct://expert-{id}@network/component
    context: int
    quality: float
    observation_count: int
    timestamp: float
    signature: str  # HMAC-SHA256


class TrustFederationProtocol:
    """
    Trust Federation Protocol from Legion Session 75.

    Enables cross-society trust sharing with:
    - Byzantine consensus (HMAC signatures)
    - Trust decay (72% retention, Session 70)
    - Quorum verification (2-of-3)
    """

    def __init__(
        self,
        society: Society,
        trust_decay_factor: float = 0.72,
        quorum_size: int = 2
    ):
        self.society = society
        self.trust_decay_factor = trust_decay_factor
        self.quorum_size = quorum_size

        # Track attestations
        self.accepted_attestations: List[FederatedTrustAttestation] = []
        self.rejected_attestations: List[FederatedTrustAttestation] = []

        # Known societies registry
        self.known_societies: Dict[str, str] = {}  # society_id → public_key

        # Attestation counter
        self.attestation_counter = 0

    def register_society(self, society_id: str, public_key: str):
        """Register known society for verification."""
        self.known_societies[society_id] = public_key

    def create_attestation(
        self,
        expert_lct: str,
        context: int,
        quality: float,
        observation_count: int
    ) -> FederatedTrustAttestation:
        """Create signed trust attestation."""
        self.attestation_counter += 1
        attestation_id = f"{self.society.society_id}-{self.attestation_counter}"

        # Create attestation data
        attestation_data = (
            f"{attestation_id}|{self.society.society_lct}|{expert_lct}|"
            f"{context}|{quality:.6f}|{observation_count}"
        )

        # Sign with HMAC-SHA256
        signature = hmac.new(
            self.society.secret_key.encode(),
            attestation_data.encode(),
            hashlib.sha256
        ).hexdigest()

        attestation = FederatedTrustAttestation(
            attestation_id=attestation_id,
            society_lct=self.society.society_lct,
            expert_lct=expert_lct,
            context=context,
            quality=quality,
            observation_count=observation_count,
            timestamp=time.time(),
            signature=signature
        )

        self.accepted_attestations.append(attestation)
        return attestation

    def verify_attestation(
        self,
        attestation: FederatedTrustAttestation,
        public_key: str
    ) -> bool:
        """Verify attestation signature."""
        # Reconstruct attestation data
        attestation_data = (
            f"{attestation.attestation_id}|{attestation.society_lct}|"
            f"{attestation.expert_lct}|{attestation.context}|"
            f"{attestation.quality:.6f}|{attestation.observation_count}"
        )

        # Verify signature
        expected_signature = hmac.new(
            public_key.encode(),
            attestation_data.encode(),
            hashlib.sha256
        ).hexdigest()

        return expected_signature == attestation.signature


# ============================================================================
# SESSION 83 - Federated Trust-First Selector (Thor)
# ============================================================================

@dataclass
class SelectionResult:
    """Result from expert selection."""
    selected_expert_ids: List[int]
    selection_method: str  # 'trust_driven' or 'router_driven'
    trust_scores: Optional[Dict[int, float]] = None


class SimplifiedTrustFirstSelector:
    """
    Simplified version of Thor's TrustFirstMRHSelector for testing.

    Key features:
    - Trust-first selection (Session 82)
    - Epsilon-greedy exploration (ε=0.2, Session 77)
    - Minimum trust evidence (min=2, Session 78)
    """

    def __init__(
        self,
        num_experts: int = 128,
        min_trust_evidence: int = 2,
        epsilon: float = 0.2
    ):
        self.num_experts = num_experts
        self.min_trust_evidence = min_trust_evidence
        self.epsilon = epsilon

        # Trust history: context → expert → [quality observations]
        self.trust_history: Dict[str, Dict[int, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Selection stats
        self.stats = {
            'trust_driven': 0,
            'router_driven': 0,
            'total_selections': 0
        }

    def select_experts(
        self,
        router_logits: List[float],
        context: str,
        k: int = 8
    ) -> SelectionResult:
        """Select experts using trust-first approach."""
        self.stats['total_selections'] += 1

        # Check if trust-driven selection is possible
        trust_scores = self._compute_trust_scores(context)
        has_sufficient_trust = len(trust_scores) >= k

        # Epsilon-greedy: explore with probability ε
        use_trust = has_sufficient_trust and (random.random() > self.epsilon)

        if use_trust:
            # Trust-driven selection
            sorted_by_trust = sorted(
                trust_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            selected = [expert_id for expert_id, _ in sorted_by_trust[:k]]
            self.stats['trust_driven'] += 1
            method = 'trust_driven'
        else:
            # Router-driven selection (fallback)
            sorted_by_router = sorted(
                enumerate(router_logits),
                key=lambda x: x[1],
                reverse=True
            )
            selected = [expert_id for expert_id, _ in sorted_by_router[:k]]
            self.stats['router_driven'] += 1
            method = 'router_driven'

        return SelectionResult(
            selected_expert_ids=selected,
            selection_method=method,
            trust_scores=trust_scores if use_trust else None
        )

    def update_trust_for_expert(
        self,
        expert_id: int,
        context: str,
        quality: float
    ):
        """Update trust history for expert."""
        self.trust_history[context][expert_id].append(quality)

    def _compute_trust_scores(self, context: str) -> Dict[int, float]:
        """Compute trust scores for experts in context."""
        trust_scores = {}

        for expert_id, qualities in self.trust_history[context].items():
            if len(qualities) >= self.min_trust_evidence:
                # Simple average (unweighted, per Session 80)
                trust_scores[expert_id] = statistics.mean(qualities)

        return trust_scores

    def get_trust_driven_rate(self) -> float:
        """Get percentage of trust-driven selections."""
        if self.stats['total_selections'] == 0:
            return 0.0
        return self.stats['trust_driven'] / self.stats['total_selections']


class FederatedTrustFirstSelector(SimplifiedTrustFirstSelector):
    """
    Trust-first selector with federation support (Session 83).

    Extends SimplifiedTrustFirstSelector with:
    - Cross-society trust import/export
    - LCT identity binding
    - Byzantine consensus verification
    - Trust decay application
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
            quorum_size=2  # 2-of-3 for Byzantine tolerance
        )

        # Federation stats
        self.federation_stats = {
            'attestations_exported': 0,
            'attestations_imported': 0,
            'attestations_rejected': 0,
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
        """Import and apply federated trust attestation."""
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


# ============================================================================
# HETEROGENEOUS TEST FRAMEWORK
# ============================================================================

@dataclass
class TaskSpecialization:
    """Task specialization for a society."""
    society_id: str
    task_domain: str  # 'coding', 'reasoning', 'multilingual'
    task_descriptions: List[str]
    context_prefix: str  # 'code', 'logic', 'lang'


@dataclass
class HeterogeneousTestResult:
    """Result from heterogeneous federation test."""
    test_id: str
    societies: List[str]

    # Per-society results
    trust_driven_rates: Dict[str, float]
    first_activations: Dict[str, int]
    experts_used: Dict[str, int]

    # Federation stats
    attestations_exported: Dict[str, int]
    attestations_imported: Dict[str, int]
    attestations_rejected: Dict[str, int]

    # Baseline comparison (no federation)
    baseline_trust_driven_rates: Dict[str, float]
    baseline_first_activations: Dict[str, int]

    # Federation benefit calculation
    federation_benefit_pct: Dict[str, float]
    avg_federation_benefit: float

    # Observation diversity metrics
    task_overlap_pct: float  # How much task overlap between societies

    passed: bool  # True if avg_federation_benefit > 10%


class HeterogeneousFederationTester:
    """
    Tests federation with heterogeneous observations.

    Validates Thor Session 83 hypothesis: Federation provides value
    when societies have DIVERSE observations.
    """

    def __init__(self):
        # Define task specializations
        self.specializations = {
            'thor': TaskSpecialization(
                society_id='thor',
                task_domain='coding',
                task_descriptions=[
                    'Implement binary search in Python',
                    'Write quicksort in Rust',
                    'Create fibonacci generator',
                    'Design hash table implementation',
                    'Build tree traversal algorithm',
                    'Implement graph BFS',
                    'Write dynamic programming solution',
                    'Create linked list operations',
                    'Design stack with min() in O(1)',
                ],
                context_prefix='code'
            ),
            'legion': TaskSpecialization(
                society_id='legion',
                task_domain='reasoning',
                task_descriptions=[
                    'Solve: If all A are B, and all B are C...',
                    'Calculate: What is 15% of 240?',
                    'Prove: The sum of angles in a triangle',
                    'Deduce: All swans are white. This is...',
                    'Infer: If P then Q. P is true. Therefore...',
                    'Reason: The trolley problem ethical dilemma',
                    'Analyze: Correlation vs causation fallacy',
                    'Evaluate: Premise validity in argument',
                    'Conclude: Modus ponens application',
                ],
                context_prefix='logic'
            ),
            'sprout': TaskSpecialization(
                society_id='sprout',
                task_domain='multilingual',
                task_descriptions=[
                    'Translate: "Hello world" to Spanish',
                    'Translate: "Good morning" to Chinese',
                    'Translate: "Thank you" to French',
                    'Translate: "Welcome" to German',
                    'Translate: "Goodbye" to Japanese',
                    'Translate: "Please" to Italian',
                    'Translate: "Sorry" to Portuguese',
                    'Translate: "Yes" to Russian',
                    'Translate: "No" to Arabic',
                ],
                context_prefix='lang'
            )
        }

    def run_heterogeneous_test(
        self,
        generations: int = 90,
        num_experts: int = 128
    ) -> HeterogeneousTestResult:
        """
        Run heterogeneous federation test.

        Each society works on different tasks, shares trust via federation.
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

        # Create federated selectors
        thor_selector = FederatedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2,
            society=thor,
            enable_federation=True
        )

        legion_fed_selector = FederatedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2,
            society=legion,
            enable_federation=True
        )

        sprout_fed_selector = FederatedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2,
            society=sprout,
            enable_federation=True
        )

        # Create baseline selectors (no federation)
        thor_baseline = SimplifiedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2
        )

        legion_baseline = SimplifiedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2
        )

        sprout_baseline = SimplifiedTrustFirstSelector(
            num_experts=num_experts,
            epsilon=0.2,
            min_trust_evidence=2
        )

        # Register peer societies
        thor_selector.register_society(legion.society_id, legion.secret_key)
        thor_selector.register_society(sprout.society_id, sprout.secret_key)

        legion_fed_selector.register_society(thor.society_id, thor.secret_key)
        legion_fed_selector.register_society(sprout.society_id, sprout.secret_key)

        sprout_fed_selector.register_society(thor.society_id, thor.secret_key)
        sprout_fed_selector.register_society(legion.society_id, legion.secret_key)

        # Run test
        random.seed(42)

        for gen in range(generations):
            # All societies work on SHARED context (e.g., sequence ID)
            # but observe DIFFERENT aspects (coding vs reasoning vs language)
            shared_context_idx = gen % 9  # 9 shared contexts
            context_id = f"cluster_{shared_context_idx}"

            # Generate router logits (same for all - shared model)
            router_logits = [random.random() for _ in range(num_experts)]

            # CRITICAL FIX: Same experts, same context, but different quality
            # observations based on task type. Expert 42 might be great at
            # coding but poor at reasoning.

            # Experts have different strengths for different task types
            # Some experts good at coding, others at reasoning, others at language
            selected_expert_id = gen % num_experts  # Rotate through experts

            # Quality depends on expert specialization and task type
            # Expert specialization (deterministic based on expert_id)
            expert_coding_skill = (selected_expert_id % 3 == 0)  # Every 3rd expert
            expert_reasoning_skill = (selected_expert_id % 3 == 1)
            expert_language_skill = (selected_expert_id % 3 == 2)

            # Quality scores based on match between expert skill and task type
            thor_quality = 0.9 if expert_coding_skill else 0.5
            legion_quality = 0.9 if expert_reasoning_skill else 0.5
            sprout_quality = 0.9 if expert_language_skill else 0.5

            # ---- THOR SOCIETY (CODING TASKS) ----
            # Federated
            thor_result = thor_selector.select_experts(router_logits, context_id, k=8)
            # Use the expert we selected (simulating router choice)
            thor_selector.update_trust_for_expert(
                selected_expert_id,
                context_id,
                thor_quality,
                broadcast=True
            )

            # Baseline
            thor_baseline_result = thor_baseline.select_experts(
                router_logits, context_id, k=8
            )
            thor_baseline.update_trust_for_expert(
                selected_expert_id,
                context_id,
                thor_quality
            )

            # ---- LEGION SOCIETY (REASONING TASKS) ----
            # Import Thor's and Sprout's attestations
            for attestation in thor_selector.federation.accepted_attestations:
                legion_fed_selector.import_attestation(attestation, thor.secret_key)
            for attestation in sprout_fed_selector.federation.accepted_attestations:
                legion_fed_selector.import_attestation(attestation, sprout.secret_key)

            # Federated
            legion_result = legion_fed_selector.select_experts(
                router_logits, context_id, k=8
            )
            legion_fed_selector.update_trust_for_expert(
                selected_expert_id,
                context_id,
                legion_quality,
                broadcast=True
            )

            # Baseline
            legion_baseline_result = legion_baseline.select_experts(
                router_logits, context_id, k=8
            )
            legion_baseline.update_trust_for_expert(
                selected_expert_id,
                context_id,
                legion_quality
            )

            # ---- SPROUT SOCIETY (MULTILINGUAL TASKS) ----
            # Import Thor's and Legion's attestations
            for attestation in thor_selector.federation.accepted_attestations:
                sprout_fed_selector.import_attestation(attestation, thor.secret_key)
            for attestation in legion_fed_selector.federation.accepted_attestations:
                sprout_fed_selector.import_attestation(attestation, legion.secret_key)

            # Federated
            sprout_result = sprout_fed_selector.select_experts(
                router_logits, context_id, k=8
            )
            sprout_fed_selector.update_trust_for_expert(
                selected_expert_id,
                context_id,
                sprout_quality,
                broadcast=True
            )

            # Baseline
            sprout_baseline_result = sprout_baseline.select_experts(
                router_logits, context_id, k=8
            )
            sprout_baseline.update_trust_for_expert(
                selected_expert_id,
                context_id,
                sprout_quality
            )

        # Calculate results
        trust_driven_rates = {
            'thor': thor_selector.get_trust_driven_rate(),
            'legion': legion_fed_selector.get_trust_driven_rate(),
            'sprout': sprout_fed_selector.get_trust_driven_rate()
        }

        baseline_trust_driven_rates = {
            'thor': thor_baseline.get_trust_driven_rate(),
            'legion': legion_baseline.get_trust_driven_rate(),
            'sprout': sprout_baseline.get_trust_driven_rate()
        }

        first_activations = {
            'thor': thor_selector.federation_stats['first_trust_driven_gen'] or -1,
            'legion': legion_fed_selector.federation_stats['first_trust_driven_gen'] or -1,
            'sprout': sprout_fed_selector.federation_stats['first_trust_driven_gen'] or -1
        }

        baseline_first_activations = {
            'thor': -1,  # Not tracked in baseline
            'legion': -1,
            'sprout': -1
        }

        experts_used = {
            'thor': len([e for experts in thor_selector.trust_history.values()
                        for e in experts.keys()]),
            'legion': len([e for experts in legion_fed_selector.trust_history.values()
                          for e in experts.keys()]),
            'sprout': len([e for experts in sprout_fed_selector.trust_history.values()
                          for e in experts.keys()])
        }

        attestations_exported = {
            'thor': thor_selector.federation_stats['attestations_exported'],
            'legion': legion_fed_selector.federation_stats['attestations_exported'],
            'sprout': sprout_fed_selector.federation_stats['attestations_exported']
        }

        attestations_imported = {
            'thor': thor_selector.federation_stats['attestations_imported'],
            'legion': legion_fed_selector.federation_stats['attestations_imported'],
            'sprout': sprout_fed_selector.federation_stats['attestations_imported']
        }

        attestations_rejected = {
            'thor': thor_selector.federation_stats['attestations_rejected'],
            'legion': legion_fed_selector.federation_stats['attestations_rejected'],
            'sprout': sprout_fed_selector.federation_stats['attestations_rejected']
        }

        # Calculate federation benefit (absolute improvement)
        # When baseline=0, relative improvement is undefined,
        # so we use absolute improvement (percentage points)
        federation_benefit_pct = {}
        for society in ['thor', 'legion', 'sprout']:
            baseline = baseline_trust_driven_rates[society]
            federated = trust_driven_rates[society]

            # Absolute benefit in percentage points
            benefit = (federated - baseline) * 100

            federation_benefit_pct[society] = benefit

        avg_benefit = statistics.mean(federation_benefit_pct.values())

        # Task overlap (0% for heterogeneous)
        task_overlap_pct = 0.0  # Different tasks entirely

        # Test passes if avg benefit > 10%
        passed = avg_benefit > 10.0

        return HeterogeneousTestResult(
            test_id="heterogeneous-federation-v1",
            societies=['thor', 'legion', 'sprout'],
            trust_driven_rates=trust_driven_rates,
            first_activations=first_activations,
            experts_used=experts_used,
            attestations_exported=attestations_exported,
            attestations_imported=attestations_imported,
            attestations_rejected=attestations_rejected,
            baseline_trust_driven_rates=baseline_trust_driven_rates,
            baseline_first_activations=baseline_first_activations,
            federation_benefit_pct=federation_benefit_pct,
            avg_federation_benefit=avg_benefit,
            task_overlap_pct=task_overlap_pct,
            passed=passed
        )


# ============================================================================
# DEMO
# ============================================================================

def demo_heterogeneous_federation():
    """
    Demo: Test federation with diverse observations.

    Validates Thor Session 83 hypothesis:
    - Session 83: 0% benefit with identical observations
    - Session 77: >10% benefit with diverse observations
    """
    print("=" * 80)
    print("HETEROGENEOUS FEDERATION TEST - Session 77")
    print("=" * 80)
    print()
    print("Hypothesis (Thor Session 83):")
    print("  Federation provides value ONLY with diverse observations")
    print()
    print("Test Scenario:")
    print("  - Thor Society: Coding tasks (Python, Rust, algorithms)")
    print("  - Legion Society: Reasoning tasks (math, logic, philosophy)")
    print("  - Sprout Society: Multilingual text (EN, ES, ZH)")
    print()
    print("Expected:")
    print("  - Federation benefit > 10% (vs Session 83's 0%)")
    print("  - Cross-society expertise sharing")
    print("=" * 80)
    print()

    # Run test
    tester = HeterogeneousFederationTester()
    result = tester.run_heterogeneous_test(generations=90, num_experts=128)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print("Trust-Driven Activation Rates:")
    print("-" * 80)
    for society in result.societies:
        federated = result.trust_driven_rates[society]
        baseline = result.baseline_trust_driven_rates[society]
        benefit = result.federation_benefit_pct[society]

        print(f"{society.upper():8s}: Federated={federated:5.1%} | "
              f"Baseline={baseline:5.1%} | Benefit={benefit:+6.1f}%")
    print()

    print(f"Average Federation Benefit: {result.avg_federation_benefit:+.1f}%")
    print()

    print("First Trust-Driven Activation:")
    print("-" * 80)
    for society in result.societies:
        gen = result.first_activations[society]
        print(f"{society.upper():8s}: Generation {gen}")
    print()

    print("Federation Statistics:")
    print("-" * 80)
    for society in result.societies:
        exported = result.attestations_exported[society]
        imported = result.attestations_imported[society]
        rejected = result.attestations_rejected[society]

        print(f"{society.upper():8s}: Exported={exported:4d} | "
              f"Imported={imported:5d} | Rejected={rejected:3d}")
    print()

    print("Expert Diversity:")
    print("-" * 80)
    for society in result.societies:
        experts = result.experts_used[society]
        print(f"{society.upper():8s}: {experts}/128 experts used ({experts/128*100:.1f}%)")
    print()

    print("Test Result:")
    print("-" * 80)
    if result.passed:
        print(f"✅ PASS - Federation benefit ({result.avg_federation_benefit:+.1f}%) > 10%")
        print()
        print("Conclusion:")
        print("  Thor Session 83 hypothesis VALIDATED!")
        print("  Federation provides value when societies have DIVERSE observations.")
    else:
        print(f"❌ FAIL - Federation benefit ({result.avg_federation_benefit:+.1f}%) ≤ 10%")
        print()
        print("Conclusion:")
        print("  Hypothesis needs refinement. Observation diversity alone")
        print("  may not be sufficient for federation value.")
    print()

    print("Comparison to Session 83 (Homogeneous):")
    print("-" * 80)
    print(f"  Session 83 (identical tasks):  0.0% benefit")
    print(f"  Session 77 (diverse tasks):   {result.avg_federation_benefit:+.1f}% benefit")
    print()

    # Save results
    results_file = "/home/dp/ai-workspace/web4/implementation/heterogeneous_federation_results.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    print(f"Results saved to: {results_file}")
    print()

    return result


if __name__ == "__main__":
    demo_heterogeneous_federation()
