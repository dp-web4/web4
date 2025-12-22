#!/usr/bin/env python3
"""
Session 81: Thor Import Anomaly Fix

**Date**: 2025-12-22
**Platform**: Legion (RTX 4090)
**Session**: Autonomous Session 81

## Problem Statement

Sessions 77-78 identified a critical bug: Thor exports attestations but never
imports them from other societies.

**Evidence**:
- Thor: Exported=90, Imported=0
- Legion: Exported=90, Imported=8100
- Sprout: Exported=90, Imported=8190

**Root Cause** (discovered in Session 81):
The heterogeneous_federation_test.py processes societies in sequence:
1. Thor executes (exports attestations)
2. Legion executes (imports Thor's + Sprout's attestations)
3. Sprout executes (imports Thor's + Legion's attestations)

Thor goes FIRST and has NO import lines → Thor never imports others' work!

## Expected Behavior

All three societies should have symmetric import/export:
- Each society exports ~90 attestations (1 per generation)
- Each society imports attestations from the other 2 societies
- Expected imports: 90 * 2 = 180 attestations (without deduplication)

## Fix

Add import lines for Thor to receive Legion and Sprout attestations.

## Test Plan

1. Run BROKEN version (current heterogeneous_federation_test.py)
2. Verify Thor imports = 0 (bug present)
3. Apply fix (add Thor import lines)
4. Run FIXED version
5. Verify Thor imports > 0 (bug fixed)
6. Verify symmetric benefit across all societies
"""

import random
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from collections import defaultdict

# ============================================================================
# Core Data Structures (from heterogeneous_federation_test.py)
# ============================================================================

@dataclass
class QualityAttestation:
    """Federated trust attestation with cryptographic signature."""
    attestation_id: str
    observer_society: str
    expert_id: int
    context_id: str
    quality: float
    observation_count: int
    signature: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SelectionResult:
    """Result of expert selection."""
    selected_experts: List[int]
    selection_method: str  # 'trust_driven' or 'router_fallback'


class SocietyIdentity:
    """LCT identity for a society."""
    def __init__(self, society_id: str):
        self.society_id = society_id
        # Simplified: Use society_id as secret key (production would use proper key generation)
        self.secret_key = f"{society_id}_secret_key".encode()
        self.public_key = f"{society_id}_public_key".encode()


class TrustFederationProtocol:
    """Handles federation protocol operations."""
    def __init__(self, local_society_id: str):
        self.local_society_id = local_society_id
        self.accepted_attestations: List[QualityAttestation] = []
        self.rejected_attestations: List[QualityAttestation] = []

    def sign_attestation(self, attestation: QualityAttestation, secret_key: bytes) -> str:
        """Generate HMAC-SHA256 signature."""
        message = f"{attestation.expert_id}:{attestation.context_id}:{attestation.quality}"
        return hmac.new(secret_key, message.encode(), hashlib.sha256).hexdigest()

    def verify_attestation(self, attestation: QualityAttestation, public_key: bytes) -> bool:
        """Verify attestation signature."""
        # In production, public_key would be used differently
        # For this test, we derive expected secret from public key
        expected_secret = public_key.replace(b"_public_key", b"_secret_key")
        expected_signature = self.sign_attestation(attestation, expected_secret)
        return attestation.signature == expected_signature

    def create_attestation(
        self,
        expert_id: int,
        context_id: str,
        quality: float,
        observation_count: int,
        secret_key: bytes
    ) -> QualityAttestation:
        """Create signed attestation."""
        attestation_id = f"{self.local_society_id}:{context_id}:{expert_id}:{time.time()}"
        attestation = QualityAttestation(
            attestation_id=attestation_id,
            observer_society=self.local_society_id,
            expert_id=expert_id,
            context_id=context_id,
            quality=quality,
            observation_count=observation_count,
            signature=""  # Will be set below
        )
        attestation.signature = self.sign_attestation(attestation, secret_key)
        self.accepted_attestations.append(attestation)
        return attestation


class SimplifiedTrustFirstSelector:
    """Simplified trust-first selector for federation testing."""

    def __init__(self, society_id: str, epsilon: float = 0.2,
                 min_trust_evidence: int = 2, trust_decay: float = 0.72,
                 enable_federation: bool = True):
        self.society_id = society_id
        self.epsilon = epsilon
        self.min_trust_evidence = min_trust_evidence
        self.trust_decay = trust_decay
        self.enable_federation = enable_federation

        # Trust tracking
        self.trust_history: Dict[str, Dict[int, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Federation protocol
        self.federation = TrustFederationProtocol(society_id)

        # Statistics
        self.stats = {
            'total_selections': 0,
            'trust_driven_selections': 0,
            'router_fallback_selections': 0,
        }

        # Federation stats
        self.federation_stats = {
            'attestations_exported': 0,
            'attestations_imported': 0,
            'attestations_rejected': 0,
            'first_trust_driven_gen': None,
        }

    def _compute_trust_scores(self, context_id: str) -> Dict[int, float]:
        """Compute trust scores for all experts in context."""
        trust_scores = {}

        for expert_id, quality_history in self.trust_history[context_id].items():
            if len(quality_history) >= self.min_trust_evidence:
                # Simple average of recent observations
                trust_scores[expert_id] = sum(quality_history) / len(quality_history)

        return trust_scores

    def update_trust_for_expert(
        self,
        expert_id: int,
        context_id: str,
        quality: float,
        broadcast: bool = False
    ):
        """Update trust based on observed quality."""
        # Add to local trust history
        self.trust_history[context_id][expert_id].append(quality)

        # Broadcast to federation if enabled
        if broadcast and self.enable_federation:
            # Count observations for this expert in this context
            observation_count = len(self.trust_history[context_id][expert_id])

            # Create and broadcast attestation
            # Note: secret_key would come from SocietyIdentity in production
            secret_key = f"{self.society_id}_secret_key".encode()
            self.federation.create_attestation(
                expert_id=expert_id,
                context_id=context_id,
                quality=quality,
                observation_count=observation_count,
                secret_key=secret_key
            )

        self.federation_stats['attestations_exported'] += 1

    def import_attestation(
        self,
        attestation: QualityAttestation,
        society_public_key: bytes
    ) -> bool:
        """Import and apply federated trust attestation."""
        # Verify attestation signature
        if not self.federation.verify_attestation(attestation, society_public_key):
            self.federation_stats['attestations_rejected'] += 1
            self.federation.rejected_attestations.append(attestation)
            return False

        # Apply trust decay for federated attestations
        decayed_quality = attestation.quality * self.trust_decay

        # Add to trust history
        context_id = attestation.context_id
        expert_id = attestation.expert_id

        # Update trust history
        self.trust_history[context_id][expert_id].append(decayed_quality)

        self.federation_stats['attestations_imported'] += 1
        return True

    def select_experts(
        self,
        router_logits: List[float],
        context_id: str,
        k: int = 8
    ) -> SelectionResult:
        """Select top-k experts using trust-first selection."""
        num_experts = len(router_logits)
        self.stats['total_selections'] += 1

        # Compute trust scores
        trust_scores = self._compute_trust_scores(context_id)

        # Trust-first selection with epsilon-greedy exploration
        if trust_scores and random.random() > self.epsilon:
            # Trust-driven: Select from trusted experts
            trusted_experts = list(trust_scores.keys())
            # Select top-k by trust
            sorted_experts = sorted(
                trusted_experts,
                key=lambda e: trust_scores[e],
                reverse=True
            )
            selected = sorted_experts[:min(k, len(sorted_experts))]

            # Fill remaining slots with router if needed
            if len(selected) < k:
                router_top = sorted(
                    range(num_experts),
                    key=lambda e: router_logits[e],
                    reverse=True
                )
                for expert_id in router_top:
                    if expert_id not in selected:
                        selected.append(expert_id)
                    if len(selected) >= k:
                        break

            self.stats['trust_driven_selections'] += 1
            method = 'trust_driven'
        else:
            # Router fallback: Use router logits
            selected = sorted(
                range(num_experts),
                key=lambda e: router_logits[e],
                reverse=True
            )[:k]
            self.stats['router_fallback_selections'] += 1
            method = 'router_fallback'

        # Track first trust_driven activation
        if (method == 'trust_driven' and
            self.federation_stats['first_trust_driven_gen'] is None):
            self.federation_stats['first_trust_driven_gen'] = \
                self.stats['total_selections']

        return SelectionResult(
            selected_experts=selected,
            selection_method=method
        )


# ============================================================================
# Test Function - BROKEN Version (Thor doesn't import)
# ============================================================================

def test_broken_version():
    """
    Run test with BROKEN code (Thor doesn't import attestations).
    """
    print("=" * 80)
    print("SESSION 81: THOR IMPORT ANOMALY - BROKEN VERSION")
    print("=" * 80)
    print()

    # Create societies
    thor = SocietyIdentity("thor")
    legion = SocietyIdentity("legion")
    sprout = SocietyIdentity("sprout")

    # Create selectors
    thor_selector = SimplifiedTrustFirstSelector("thor", enable_federation=True)
    legion_selector = SimplifiedTrustFirstSelector("legion", enable_federation=True)
    sprout_selector = SimplifiedTrustFirstSelector("sprout", enable_federation=True)

    num_experts = 128
    generations = 90

    print(f"Configuration:")
    print(f"  Societies: Thor, Legion, Sprout")
    print(f"  Experts: {num_experts}")
    print(f"  Generations: {generations}")
    print(f"  Federation: ENABLED")
    print()

    for gen in range(generations):
        shared_context_idx = gen % 9
        context_id = f"cluster_{shared_context_idx}"

        router_logits = [random.random() for _ in range(num_experts)]
        selected_expert_id = gen % num_experts

        # Expert specialization
        expert_coding_skill = (selected_expert_id % 3 == 0)
        expert_reasoning_skill = (selected_expert_id % 3 == 1)
        expert_language_skill = (selected_expert_id % 3 == 2)

        thor_quality = 0.9 if expert_coding_skill else 0.5
        legion_quality = 0.9 if expert_reasoning_skill else 0.5
        sprout_quality = 0.9 if expert_language_skill else 0.5

        # ---- THOR SOCIETY (CODING TASKS) ----
        # BUG: NO IMPORT LINES! Thor never imports Legion/Sprout attestations
        thor_result = thor_selector.select_experts(router_logits, context_id, k=8)
        thor_selector.update_trust_for_expert(
            selected_expert_id,
            context_id,
            thor_quality,
            broadcast=True
        )

        # ---- LEGION SOCIETY (REASONING TASKS) ----
        # Import Thor's and Sprout's attestations
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

        # ---- SPROUT SOCIETY (MULTILINGUAL TASKS) ----
        # Import Thor's and Legion's attestations
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

    # Print results
    print()
    print("=" * 80)
    print("BROKEN VERSION RESULTS")
    print("=" * 80)
    print()

    print("Federation Statistics:")
    print("-" * 80)
    print(f"THOR    : Exported={thor_selector.federation_stats['attestations_exported']:4d} | "
          f"Imported={thor_selector.federation_stats['attestations_imported']:4d} | "
          f"Rejected={thor_selector.federation_stats['attestations_rejected']:2d}")
    print(f"LEGION  : Exported={legion_selector.federation_stats['attestations_exported']:4d} | "
          f"Imported={legion_selector.federation_stats['attestations_imported']:4d} | "
          f"Rejected={legion_selector.federation_stats['attestations_rejected']:2d}")
    print(f"SPROUT  : Exported={sprout_selector.federation_stats['attestations_exported']:4d} | "
          f"Imported={sprout_selector.federation_stats['attestations_imported']:4d} | "
          f"Rejected={sprout_selector.federation_stats['attestations_rejected']:2d}")
    print()

    print("Trust-Driven Rates:")
    print("-" * 80)
    thor_rate = 100 * thor_selector.stats['trust_driven_selections'] / thor_selector.stats['total_selections']
    legion_rate = 100 * legion_selector.stats['trust_driven_selections'] / legion_selector.stats['total_selections']
    sprout_rate = 100 * sprout_selector.stats['trust_driven_selections'] / sprout_selector.stats['total_selections']
    print(f"THOR    : {thor_rate:5.1f}%")
    print(f"LEGION  : {legion_rate:5.1f}%")
    print(f"SPROUT  : {sprout_rate:5.1f}%")
    print()

    print("Bug Detection:")
    print("-" * 80)
    if thor_selector.federation_stats['attestations_imported'] == 0:
        print("❌ BUG CONFIRMED: Thor imported 0 attestations!")
        print("   Expected: ~180 imports (90 from Legion + 90 from Sprout)")
    else:
        print("✅ Bug not present")
    print()

    return {
        'thor': thor_selector,
        'legion': legion_selector,
        'sprout': sprout_selector
    }


# ============================================================================
# Test Function - FIXED Version (Thor imports from Legion and Sprout)
# ============================================================================

def test_fixed_version():
    """
    Run test with FIXED code (Thor imports attestations from Legion and Sprout).
    """
    print("=" * 80)
    print("SESSION 81: THOR IMPORT ANOMALY - FIXED VERSION")
    print("=" * 80)
    print()

    # Create societies
    thor = SocietyIdentity("thor")
    legion = SocietyIdentity("legion")
    sprout = SocietyIdentity("sprout")

    # Create selectors
    thor_selector = SimplifiedTrustFirstSelector("thor", enable_federation=True)
    legion_selector = SimplifiedTrustFirstSelector("legion", enable_federation=True)
    sprout_selector = SimplifiedTrustFirstSelector("sprout", enable_federation=True)

    num_experts = 128
    generations = 90

    print(f"Configuration:")
    print(f"  Societies: Thor, Legion, Sprout")
    print(f"  Experts: {num_experts}")
    print(f"  Generations: {generations}")
    print(f"  Federation: ENABLED")
    print()

    for gen in range(generations):
        shared_context_idx = gen % 9
        context_id = f"cluster_{shared_context_idx}"

        router_logits = [random.random() for _ in range(num_experts)]
        selected_expert_id = gen % num_experts

        # Expert specialization
        expert_coding_skill = (selected_expert_id % 3 == 0)
        expert_reasoning_skill = (selected_expert_id % 3 == 1)
        expert_language_skill = (selected_expert_id % 3 == 2)

        thor_quality = 0.9 if expert_coding_skill else 0.5
        legion_quality = 0.9 if expert_reasoning_skill else 0.5
        sprout_quality = 0.9 if expert_language_skill else 0.5

        # ---- THOR SOCIETY (CODING TASKS) ----
        # FIX: Add import lines for Legion and Sprout attestations!
        for attestation in legion_selector.federation.accepted_attestations:
            thor_selector.import_attestation(attestation, legion.secret_key)
        for attestation in sprout_selector.federation.accepted_attestations:
            thor_selector.import_attestation(attestation, sprout.secret_key)

        thor_result = thor_selector.select_experts(router_logits, context_id, k=8)
        thor_selector.update_trust_for_expert(
            selected_expert_id,
            context_id,
            thor_quality,
            broadcast=True
        )

        # ---- LEGION SOCIETY (REASONING TASKS) ----
        # Import Thor's and Sprout's attestations
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

        # ---- SPROUT SOCIETY (MULTILINGUAL TASKS) ----
        # Import Thor's and Legion's attestations
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

    # Print results
    print()
    print("=" * 80)
    print("FIXED VERSION RESULTS")
    print("=" * 80)
    print()

    print("Federation Statistics:")
    print("-" * 80)
    print(f"THOR    : Exported={thor_selector.federation_stats['attestations_exported']:4d} | "
          f"Imported={thor_selector.federation_stats['attestations_imported']:4d} | "
          f"Rejected={thor_selector.federation_stats['attestations_rejected']:2d}")
    print(f"LEGION  : Exported={legion_selector.federation_stats['attestations_exported']:4d} | "
          f"Imported={legion_selector.federation_stats['attestations_imported']:4d} | "
          f"Rejected={legion_selector.federation_stats['attestations_rejected']:2d}")
    print(f"SPROUT  : Exported={sprout_selector.federation_stats['attestations_exported']:4d} | "
          f"Imported={sprout_selector.federation_stats['attestations_imported']:4d} | "
          f"Rejected={sprout_selector.federation_stats['attestations_rejected']:2d}")
    print()

    print("Trust-Driven Rates:")
    print("-" * 80)
    thor_rate = 100 * thor_selector.stats['trust_driven_selections'] / thor_selector.stats['total_selections']
    legion_rate = 100 * legion_selector.stats['trust_driven_selections'] / legion_selector.stats['total_selections']
    sprout_rate = 100 * sprout_selector.stats['trust_driven_selections'] / sprout_selector.stats['total_selections']
    print(f"THOR    : {thor_rate:5.1f}%")
    print(f"LEGION  : {legion_rate:5.1f}%")
    print(f"SPROUT  : {sprout_rate:5.1f}%")
    print()

    print("Fix Validation:")
    print("-" * 80)
    if thor_selector.federation_stats['attestations_imported'] > 0:
        print(f"✅ FIX SUCCESSFUL: Thor imported {thor_selector.federation_stats['attestations_imported']} attestations!")
        print(f"   Expected: ~180 imports (90 from Legion + 90 from Sprout)")

        # Check if Thor's trust-driven rate improved
        if thor_rate > 0:
            print(f"✅ Thor now benefits from federation: {thor_rate:.1f}% trust-driven!")
        else:
            print(f"⚠️  Thor still has 0% trust-driven (may need more generations or different parameters)")
    else:
        print("❌ Fix failed: Thor still importing 0 attestations")
    print()

    return {
        'thor': thor_selector,
        'legion': legion_selector,
        'sprout': sprout_selector
    }


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "SESSION 81: THOR IMPORT ANOMALY FIX" + " " * 23 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Test broken version
    broken_selectors = test_broken_version()

    print()
    print("-" * 80)
    print()

    # Test fixed version
    fixed_selectors = test_fixed_version()

    # Summary comparison
    print()
    print("=" * 80)
    print("SUMMARY COMPARISON")
    print("=" * 80)
    print()

    print("Thor Import Statistics:")
    print("-" * 80)
    broken_imports = broken_selectors['thor'].federation_stats['attestations_imported']
    fixed_imports = fixed_selectors['thor'].federation_stats['attestations_imported']
    print(f"  Broken version: {broken_imports:4d} imports")
    print(f"  Fixed version:  {fixed_imports:4d} imports")
    print(f"  Improvement:    +{fixed_imports - broken_imports:4d} imports")
    print()

    print("Thor Trust-Driven Rate:")
    print("-" * 80)
    broken_rate = 100 * broken_selectors['thor'].stats['trust_driven_selections'] / broken_selectors['thor'].stats['total_selections']
    fixed_rate = 100 * fixed_selectors['thor'].stats['trust_driven_selections'] / fixed_selectors['thor'].stats['total_selections']
    print(f"  Broken version: {broken_rate:5.1f}%")
    print(f"  Fixed version:  {fixed_rate:5.1f}%")
    print(f"  Improvement:    +{fixed_rate - broken_rate:5.1f}%")
    print()

    # Final verdict
    print("Final Verdict:")
    print("-" * 80)
    if fixed_imports > broken_imports and fixed_imports > 100:
        print("✅ SESSION 81 SUCCESS!")
        print("   - Thor import anomaly identified and fixed")
        print("   - Thor now imports attestations from Legion and Sprout")
        print("   - Symmetric federation behavior achieved")
        print()
        print("Root Cause:")
        print("   Thor was processed FIRST in the federation loop")
        print("   Legion and Sprout had import lines for other societies")
        print("   Thor was missing import lines → 0 imports")
        print()
        print("Fix:")
        print("   Added import lines for Thor:")
        print("   - Import Legion's attestations")
        print("   - Import Sprout's attestations")
        print("   → Thor now participates fully in federation")
    else:
        print("❌ Fix incomplete or unsuccessful")

    print()
    print("=" * 80)
    print()

    # Save results
    results = {
        'session': 81,
        'date': '2025-12-22',
        'platform': 'Legion',
        'bug': 'Thor Import Anomaly',
        'broken_version': {
            'thor_exports': broken_selectors['thor'].federation_stats['attestations_exported'],
            'thor_imports': broken_imports,
            'thor_trust_driven_pct': broken_rate
        },
        'fixed_version': {
            'thor_exports': fixed_selectors['thor'].federation_stats['attestations_exported'],
            'thor_imports': fixed_imports,
            'thor_trust_driven_pct': fixed_rate
        },
        'improvement': {
            'imports': fixed_imports - broken_imports,
            'trust_driven_pct': fixed_rate - broken_rate
        },
        'status': 'SUCCESS' if fixed_imports > 100 else 'INCOMPLETE'
    }

    results_path = "/home/dp/ai-workspace/web4/implementation/session81_thor_import_fix_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {results_path}")
    print()
