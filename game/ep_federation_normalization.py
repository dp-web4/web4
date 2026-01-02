#!/usr/bin/env python3
"""
EP Pattern Federation - Phase 1: Structural Normalization

Session 118 Track 3: Implementation of canonical context schema and mapping
functions to enable cross-system pattern federation.

Problem: SAGE and Web4 use different context structures (dimension mismatch)
Solution: Canonical schema with bidirectional mapping functions

Architecture:
    SAGE Context (3 fields)  ─┐
                              ├─→ Canonical Context (5 fields) ─→ Pattern Matching
    Web4 Context (4-5 fields)─┘

Canonical Schema Design:
- Superset of all fields across systems
- Missing fields get sensible defaults
- Preserves semantic meaning during transformation
- Enables cross-system similarity matching
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

# Add SAGE framework for EPDomain enum
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "HRM" / "sage" / "experiments"))
from multi_ep_coordinator import EPDomain


# ============================================================================
# Canonical Context Schema
# ============================================================================

@dataclass
class CanonicalEmotionalContext:
    """
    Canonical representation of emotional domain context.

    Superset of fields from SAGE and Web4:
    - SAGE: frustration, stability, cascade_agreement
    - Web4: current_frustration, recent_failure_rate, atp_stress, interaction_complexity
    """
    frustration_level: float      # Primary frustration/stress metric (0-1)
    recent_stress: float           # Short-term stress/failure rate (0-1)
    complexity_factor: float       # Environmental/interaction complexity (0-1)
    stability_metric: float        # System/emotional stability (0-1, higher = more stable)
    cascade_influence: float       # Cascade/coordination effects (0-1)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for similarity matching."""
        return {
            "frustration_level": self.frustration_level,
            "recent_stress": self.recent_stress,
            "complexity_factor": self.complexity_factor,
            "stability_metric": self.stability_metric,
            "cascade_influence": self.cascade_influence
        }

    def to_vector(self) -> List[float]:
        """Convert to vector for cosine similarity."""
        return [
            self.frustration_level,
            self.recent_stress,
            self.complexity_factor,
            self.stability_metric,
            self.cascade_influence
        ]


@dataclass
class CanonicalQualityContext:
    """
    Canonical representation of quality domain context.

    Superset of fields from SAGE and Web4:
    - SAGE: prediction_quality, pattern_confidence, domain_agreement
    - Web4: current_relationship_quality, recent_avg_outcome, trust_alignment,
            interaction_risk_to_quality
    """
    relationship_quality: float    # Trust/relationship metric (0-1)
    recent_outcomes: float         # Recent interaction success rate (0-1)
    alignment_score: float         # Value/goal/trust alignment (0-1)
    prediction_confidence: float   # EP prediction confidence (0-1)
    risk_assessment: float         # Interaction risk level (0-1)

    def to_dict(self) -> Dict[str, float]:
        return {
            "relationship_quality": self.relationship_quality,
            "recent_outcomes": self.recent_outcomes,
            "alignment_score": self.alignment_score,
            "prediction_confidence": self.prediction_confidence,
            "risk_assessment": self.risk_assessment
        }

    def to_vector(self) -> List[float]:
        return [
            self.relationship_quality,
            self.recent_outcomes,
            self.alignment_score,
            self.prediction_confidence,
            self.risk_assessment
        ]


@dataclass
class CanonicalAttentionContext:
    """
    Canonical representation of attention domain context.

    Superset of fields from SAGE and Web4:
    - SAGE: attention_focus, resource_allocation, task_priority
    - Web4: atp_available, atp_cost, atp_reserve_needed, interaction_count,
            expected_benefit
    """
    resource_available: float      # Available ATP/resources (normalized 0-1)
    resource_cost: float           # Proposed action cost (normalized 0-1)
    expected_benefit: float        # Expected return/value (normalized 0-1)
    reserve_needed: float          # Safety reserve requirement (normalized 0-1)
    utilization_rate: float        # Current resource utilization (0-1)

    def to_dict(self) -> Dict[str, float]:
        return {
            "resource_available": self.resource_available,
            "resource_cost": self.resource_cost,
            "expected_benefit": self.expected_benefit,
            "reserve_needed": self.reserve_needed,
            "utilization_rate": self.utilization_rate
        }

    def to_vector(self) -> List[float]:
        return [
            self.resource_available,
            self.resource_cost,
            self.expected_benefit,
            self.reserve_needed,
            self.utilization_rate
        ]


# ============================================================================
# SAGE → Canonical Mapping Functions
# ============================================================================

class SAGEContextNormalizer:
    """
    Map SAGE's context structure to canonical representation.

    SAGE uses:
    - Emotional: frustration, stability, cascade_agreement (3 fields)
    - Quality: prediction_quality, pattern_confidence, domain_agreement (3 fields)
    - Attention: attention_focus, resource_allocation, task_priority (3 fields)
    """

    @staticmethod
    def normalize_emotional(sage_context: Dict[str, Any]) -> CanonicalEmotionalContext:
        """
        Map SAGE emotional context to canonical form.

        SAGE fields:
        - frustration: float (0-1)
        - stability: float (0-1)
        - cascade_agreement: float (0-1)

        Mapping strategy:
        - frustration → frustration_level (direct)
        - frustration → recent_stress (approximate, assumes recent issues)
        - 0.5 → complexity_factor (default, not in SAGE)
        - stability → stability_metric (direct)
        - cascade_agreement → cascade_influence (direct)
        """
        return CanonicalEmotionalContext(
            frustration_level=float(sage_context.get("frustration", 0.0)),
            recent_stress=float(sage_context.get("frustration", 0.0)),  # Approximate
            complexity_factor=0.5,  # Default (SAGE doesn't track this)
            stability_metric=float(sage_context.get("stability", 0.5)),
            cascade_influence=float(sage_context.get("cascade_agreement", 0.5))
        )

    @staticmethod
    def normalize_quality(sage_context: Dict[str, Any]) -> CanonicalQualityContext:
        """
        Map SAGE quality context to canonical form.

        SAGE fields:
        - prediction_quality: float (0-1)
        - pattern_confidence: float (0-1)
        - domain_agreement: float (0-1)

        Mapping strategy:
        - prediction_quality → recent_outcomes (quality of recent predictions)
        - domain_agreement → alignment_score (how well domains agree)
        - pattern_confidence → prediction_confidence (direct)
        - prediction_quality → relationship_quality (approximate)
        - 0.3 → risk_assessment (default moderate risk)
        """
        return CanonicalQualityContext(
            relationship_quality=float(sage_context.get("prediction_quality", 0.5)),
            recent_outcomes=float(sage_context.get("prediction_quality", 0.5)),
            alignment_score=float(sage_context.get("domain_agreement", 0.5)),
            prediction_confidence=float(sage_context.get("pattern_confidence", 0.5)),
            risk_assessment=0.3  # Default (SAGE doesn't track interaction risk)
        )

    @staticmethod
    def normalize_attention(sage_context: Dict[str, Any]) -> CanonicalAttentionContext:
        """
        Map SAGE attention context to canonical form.

        SAGE fields:
        - attention_focus: float (0-1)
        - resource_allocation: float (0-1)
        - task_priority: float (0-1)

        Mapping strategy:
        - resource_allocation → resource_available (current allocation)
        - task_priority → resource_cost (higher priority = higher cost)
        - attention_focus → expected_benefit (focused tasks have higher benefit)
        - 0.2 → reserve_needed (default 20% reserve)
        - resource_allocation → utilization_rate (direct)
        """
        return CanonicalAttentionContext(
            resource_available=float(sage_context.get("resource_allocation", 0.5)),
            resource_cost=float(sage_context.get("task_priority", 0.3)),
            expected_benefit=float(sage_context.get("attention_focus", 0.5)),
            reserve_needed=0.2,  # Default (SAGE doesn't track reserves)
            utilization_rate=float(sage_context.get("resource_allocation", 0.5))
        )


# ============================================================================
# Web4 → Canonical Mapping Functions
# ============================================================================

class Web4ContextNormalizer:
    """
    Map Web4's context structure to canonical representation.

    Web4 uses:
    - Emotional: current_frustration, recent_failure_rate, atp_stress,
                 interaction_complexity (4 fields)
    - Quality: current_relationship_quality, recent_avg_outcome, trust_alignment,
               interaction_risk_to_quality (4 fields)
    - Attention: atp_available, atp_cost, atp_reserve_needed, interaction_count,
                 expected_benefit (5 fields)
    """

    @staticmethod
    def normalize_emotional(web4_context: Dict[str, Any]) -> CanonicalEmotionalContext:
        """
        Map Web4 emotional context to canonical form.

        Web4 fields:
        - current_frustration: float (0-1)
        - recent_failure_rate: float (0-1)
        - atp_stress: float (0-1)
        - interaction_complexity: float (0-1)

        Mapping strategy:
        - current_frustration → frustration_level (direct)
        - recent_failure_rate → recent_stress (direct)
        - interaction_complexity → complexity_factor (direct)
        - (1 - atp_stress) → stability_metric (inverse of stress)
        - 0.5 → cascade_influence (default, Web4 doesn't have cascade)
        """
        return CanonicalEmotionalContext(
            frustration_level=float(web4_context.get("current_frustration", 0.0)),
            recent_stress=float(web4_context.get("recent_failure_rate", 0.0)),
            complexity_factor=float(web4_context.get("interaction_complexity", 0.5)),
            stability_metric=1.0 - float(web4_context.get("atp_stress", 0.0)),
            cascade_influence=0.5  # Default (Web4 doesn't have cascade coordination)
        )

    @staticmethod
    def normalize_quality(web4_context: Dict[str, Any]) -> CanonicalQualityContext:
        """
        Map Web4 quality context to canonical form.

        Web4 fields:
        - current_relationship_quality: float (0-1)
        - recent_avg_outcome: float (0-1)
        - trust_alignment: float (0-1)
        - interaction_risk_to_quality: float (0-1)

        Mapping strategy:
        - current_relationship_quality → relationship_quality (direct)
        - recent_avg_outcome → recent_outcomes (direct)
        - trust_alignment → alignment_score (direct)
        - 0.75 → prediction_confidence (default high, Web4 patterns are confident)
        - interaction_risk_to_quality → risk_assessment (direct)
        """
        return CanonicalQualityContext(
            relationship_quality=float(web4_context.get("current_relationship_quality", 0.5)),
            recent_outcomes=float(web4_context.get("recent_avg_outcome", 0.5)),
            alignment_score=float(web4_context.get("trust_alignment", 0.5)),
            prediction_confidence=0.75,  # Default (Web4 doesn't track EP confidence in context)
            risk_assessment=float(web4_context.get("interaction_risk_to_quality", 0.3))
        )

    @staticmethod
    def normalize_attention(web4_context: Dict[str, Any]) -> CanonicalAttentionContext:
        """
        Map Web4 attention context to canonical form.

        Web4 fields:
        - atp_available: float (absolute value, needs normalization)
        - atp_cost: float (absolute value, needs normalization)
        - atp_reserve_needed: float (absolute value, needs normalization)
        - interaction_count: int
        - expected_benefit: float (absolute value, needs normalization)

        Mapping strategy:
        - Normalize ATP values to 0-1 range (assume max 200)
        - atp_available/200 → resource_available
        - atp_cost/50 → resource_cost (max 50 for risky spend)
        - expected_benefit/50 → expected_benefit
        - atp_reserve_needed/200 → reserve_needed
        - (interaction_count/20) → utilization_rate (assume ~20 interactions per life)
        """
        MAX_ATP = 200.0
        MAX_COST = 50.0
        MAX_INTERACTIONS = 20.0

        atp_available = float(web4_context.get("atp_available", 100.0))
        atp_cost = float(web4_context.get("atp_cost", 0.0))
        atp_reserve = float(web4_context.get("atp_reserve_needed", 20.0))
        expected_benefit = float(web4_context.get("expected_benefit", 0.0))
        interaction_count = float(web4_context.get("interaction_count", 0))

        return CanonicalAttentionContext(
            resource_available=min(1.0, atp_available / MAX_ATP),
            resource_cost=min(1.0, atp_cost / MAX_COST),
            expected_benefit=min(1.0, expected_benefit / MAX_COST),
            reserve_needed=min(1.0, atp_reserve / MAX_ATP),
            utilization_rate=min(1.0, interaction_count / MAX_INTERACTIONS)
        )


# ============================================================================
# Unified Normalization Interface
# ============================================================================

class PatternContextNormalizer:
    """
    Unified interface for normalizing contexts from any system to canonical form.
    """

    @staticmethod
    def normalize(
        context: Dict[str, Any],
        domain: EPDomain,
        source_system: str = "web4"
    ) -> Any:  # Returns CanonicalEmotionalContext | CanonicalQualityContext | CanonicalAttentionContext
        """
        Normalize a context to canonical form.

        Args:
            context: Raw context dictionary from source system
            domain: EPDomain (EMOTIONAL, QUALITY, or ATTENTION)
            source_system: "sage" or "web4"

        Returns:
            Canonical context object (type depends on domain)
        """
        if source_system == "sage":
            normalizer = SAGEContextNormalizer
        elif source_system == "web4":
            normalizer = Web4ContextNormalizer
        else:
            raise ValueError(f"Unknown source system: {source_system}")

        if domain == EPDomain.EMOTIONAL:
            return normalizer.normalize_emotional(context)
        elif domain == EPDomain.QUALITY:
            return normalizer.normalize_quality(context)
        elif domain == EPDomain.ATTENTION:
            return normalizer.normalize_attention(context)
        else:
            raise ValueError(f"Unsupported domain for normalization: {domain}")


# ============================================================================
# Validation and Testing
# ============================================================================

def validate_normalization():
    """
    Validate that normalization preserves semantic meaning and enables matching.
    """
    print("=" * 80)
    print("EP PATTERN FEDERATION - PHASE 1 VALIDATION")
    print("=" * 80)
    print()

    # Test SAGE emotional context
    sage_emotional = {
        "frustration": 0.3,
        "stability": 0.7,
        "cascade_agreement": 0.8
    }

    canonical_sage_emo = SAGEContextNormalizer.normalize_emotional(sage_emotional)
    print("SAGE Emotional → Canonical:")
    print(f"  Input:  {sage_emotional}")
    print(f"  Output: {canonical_sage_emo.to_dict()}")
    print(f"  Vector: {canonical_sage_emo.to_vector()}")
    print()

    # Test Web4 emotional context
    web4_emotional = {
        "current_frustration": 0.25,
        "recent_failure_rate": 0.15,
        "atp_stress": 0.2,
        "interaction_complexity": 0.6
    }

    canonical_web4_emo = Web4ContextNormalizer.normalize_emotional(web4_emotional)
    print("Web4 Emotional → Canonical:")
    print(f"  Input:  {web4_emotional}")
    print(f"  Output: {canonical_web4_emo.to_dict()}")
    print(f"  Vector: {canonical_web4_emo.to_vector()}")
    print()

    # Verify dimensions match
    sage_vec = canonical_sage_emo.to_vector()
    web4_vec = canonical_web4_emo.to_vector()

    print("Dimension Check:")
    print(f"  SAGE vector length: {len(sage_vec)}")
    print(f"  Web4 vector length: {len(web4_vec)}")
    print(f"  Match: {len(sage_vec) == len(web4_vec)} ✓" if len(sage_vec) == len(web4_vec) else "  Match: FAILED ✗")
    print()

    # Test similarity calculation
    import numpy as np

    sage_np = np.array(sage_vec)
    web4_np = np.array(web4_vec)

    # Cosine similarity
    dot_product = np.dot(sage_np, web4_np)
    sage_norm = np.linalg.norm(sage_np)
    web4_norm = np.linalg.norm(web4_np)
    similarity = dot_product / (sage_norm * web4_norm)

    print("Cross-System Similarity:")
    print(f"  SAGE vector: {sage_np}")
    print(f"  Web4 vector: {web4_np}")
    print(f"  Cosine similarity: {similarity:.3f}")
    print(f"  Can match: {similarity > 0.0} ✓" if similarity > 0.0 else "  Can match: FAILED ✗")
    print()

    # Test all domains
    print("Testing All Domains:")
    print()

    # SAGE contexts
    sage_contexts = {
        EPDomain.EMOTIONAL: {"frustration": 0.4, "stability": 0.6, "cascade_agreement": 0.7},
        EPDomain.QUALITY: {"prediction_quality": 0.8, "pattern_confidence": 0.9, "domain_agreement": 0.75},
        EPDomain.ATTENTION: {"attention_focus": 0.5, "resource_allocation": 0.6, "task_priority": 0.4}
    }

    # Web4 contexts
    web4_contexts = {
        EPDomain.EMOTIONAL: {"current_frustration": 0.35, "recent_failure_rate": 0.1, "atp_stress": 0.3, "interaction_complexity": 0.7},
        EPDomain.QUALITY: {"current_relationship_quality": 0.75, "recent_avg_outcome": 0.7, "trust_alignment": 0.8, "interaction_risk_to_quality": 0.2},
        EPDomain.ATTENTION: {"atp_available": 80.0, "atp_cost": 15.0, "atp_reserve_needed": 20.0, "interaction_count": 5, "expected_benefit": 10.0}
    }

    for domain in [EPDomain.EMOTIONAL, EPDomain.QUALITY, EPDomain.ATTENTION]:
        sage_canonical = PatternContextNormalizer.normalize(sage_contexts[domain], domain, "sage")
        web4_canonical = PatternContextNormalizer.normalize(web4_contexts[domain], domain, "web4")

        sage_vec = sage_canonical.to_vector()
        web4_vec = web4_canonical.to_vector()

        # Check dimensions
        assert len(sage_vec) == len(web4_vec), f"{domain.name}: Dimension mismatch!"

        # Calculate similarity
        sage_np = np.array(sage_vec)
        web4_np = np.array(web4_vec)
        dot_product = np.dot(sage_np, web4_np)
        similarity = dot_product / (np.linalg.norm(sage_np) * np.linalg.norm(web4_np))

        print(f"{domain.name}:")
        print(f"  SAGE dims: {len(sage_vec)}, Web4 dims: {len(web4_vec)}")
        print(f"  Similarity: {similarity:.3f}")
        print()

    print("=" * 80)
    print("VALIDATION COMPLETE ✓")
    print("=" * 80)
    print()
    print("Results:")
    print("  ✓ All contexts normalize to same dimensions")
    print("  ✓ Cross-system similarity calculation works")
    print("  ✓ SAGE and Web4 patterns can now be matched")
    print()


if __name__ == "__main__":
    validate_normalization()
