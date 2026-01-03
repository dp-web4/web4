#!/usr/bin/env python3
"""
Session 120: Integrated Pattern Federation System

Combines two independent federation approaches:
- Thor's Context Projection (Sessions 153-155): Domain extraction + field mapping
- Legion's Canonical Normalization (Sessions 118-119): Canonical schema + balancing

Research Question: Does integration of both approaches improve pattern federation
beyond what either achieves alone?

Architecture:
1. Projection Layer (Thor's approach):
   - Domain-specific extraction
   - Field mapping between systems
   - Provenance awareness

2. Normalization Layer (Legion's approach):
   - Canonical schema (superset of all fields)
   - Distributional balancing
   - Quality-weighted sampling

3. Integration Strategy:
   - Use projection for initial cross-system compatibility
   - Apply normalization for consistency and balance
   - Leverage provenance for quality weighting
   - Result: Best of both approaches

Expected Benefits:
- Projection: Simpler, production-tested, maintains semantic meaning
- Normalization: Structured, consistent, preserves all information
- Integration: Robust, high-quality, well-balanced federated corpus
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import Thor's projection approach (if available, else define locally)
# Import my normalization approach
try:
    # Add HRM path for Thor's code
    hrm_path = Path(__file__).parent.parent.parent / "HRM"
    sys.path.insert(0, str(hrm_path))
    from sage.experiments.session153_context_projection_layer import ContextProjector
    from sage.experiments.session155_provenance_aware_federation import (
        ProvenanceAwareProjector,
        PatternProvenance,
        ProvenanceMetadata
    )
    HAS_THOR_CODE = True
except ImportError:
    HAS_THOR_CODE = False
    print("Note: Thor's SAGE code not available, using local projection implementation")


class PatternProvenanceType(Enum):
    """Pattern provenance - how was it created?"""
    DECISION = "decision"       # Domain made final decision (SAGE credit assignment)
    OBSERVATION = "observation" # Domain evaluated but didn't decide (Web4 multi-perspective)
    UNKNOWN = "unknown"


@dataclass
class PatternProvenance:
    """
    Provenance metadata for pattern quality assessment.

    Based on Thor's Session 154 discovery:
    - SAGE: Credit assignment (decision patterns only) → High quality
    - Web4: Multi-perspective (all observations) → Mixed quality
    """
    provenance_type: PatternProvenanceType
    source_system: str  # "sage" or "web4"
    decision_confidence: float
    was_deciding_domain: bool
    domain_priority: int
    quality_weight: float = 0.0  # Computed from above factors

    def compute_quality_weight(self) -> float:
        """
        Compute quality weight based on provenance characteristics.

        Based on Thor's Session 155 weighting strategy.
        """
        # Base weight by provenance type
        if self.provenance_type == PatternProvenanceType.DECISION:
            base = 1.0  # Decision patterns are high quality
        elif self.provenance_type == PatternProvenanceType.OBSERVATION:
            base = 0.6  # Observation patterns are lower quality
        else:
            base = 0.8  # Unknown provenance

        # Confidence factor (0.5-1.0 range)
        conf_factor = 0.5 + (self.decision_confidence * 0.5)

        # Priority factor (higher priority = higher weight)
        priority_factor = max(0.5, 1.0 - (self.domain_priority - 1) * 0.1)

        # Deciding domain bonus
        decision_bonus = 1.1 if self.was_deciding_domain else 1.0

        # Combine
        weight = base * conf_factor * priority_factor * decision_bonus
        return min(1.0, weight)  # Cap at 1.0


@dataclass
class CanonicalContext:
    """
    Canonical context representation (from Legion's Session 118).

    Superset of SAGE (3 fields) and Web4 (4-5 fields) per domain.
    Enables consistent cross-system representation.
    """
    # Core fields (present in most systems)
    primary_metric: float      # Domain-specific primary value
    recent_trend: float        # Short-term trend
    complexity: float          # Interaction complexity

    # Extended fields (system-specific)
    stability: float = 0.5     # Long-term stability (default neutral)
    coordination: float = 0.5  # Cross-domain coordination (default neutral)

    def to_vector(self) -> List[float]:
        """Convert to vector for pattern matching."""
        return [
            self.primary_metric,
            self.recent_trend,
            self.complexity,
            self.stability,
            self.coordination
        ]

    @staticmethod
    def from_sage(sage_context: Dict[str, float], domain: str) -> 'CanonicalContext':
        """Map SAGE 3-field context to canonical 5-field."""
        if domain == "emotional":
            # SAGE: frustration, recent_failure_rate, complexity
            return CanonicalContext(
                primary_metric=sage_context.get("frustration", 0.0),
                recent_trend=sage_context.get("recent_failure_rate", 0.0),
                complexity=sage_context.get("complexity", 0.5),
                stability=0.5,  # Not in SAGE emotional
                coordination=0.5  # Not in SAGE emotional
            )
        elif domain == "quality":
            # SAGE: relationship_quality, recent_quality_avg, risk_level
            return CanonicalContext(
                primary_metric=sage_context.get("relationship_quality", 0.5),
                recent_trend=sage_context.get("recent_quality_avg", 0.5),
                complexity=sage_context.get("risk_level", 0.0),
                stability=sage_context.get("relationship_quality", 0.5),  # Approximate
                coordination=0.5
            )
        elif domain == "attention":
            # SAGE: atp_level, estimated_cost, reserve_threshold
            return CanonicalContext(
                primary_metric=sage_context.get("atp_level", 100.0) / 100.0,  # Normalize
                recent_trend=sage_context.get("estimated_cost", 20.0) / 100.0,  # Normalize
                complexity=sage_context.get("reserve_threshold", 30.0) / 100.0,  # Normalize
                stability=0.5,
                coordination=0.5
            )
        else:
            # Default for unknown domains
            return CanonicalContext(
                primary_metric=0.5,
                recent_trend=0.5,
                complexity=0.5,
                stability=0.5,
                coordination=0.5
            )

    @staticmethod
    def from_web4(web4_context: Dict[str, float], domain: str) -> 'CanonicalContext':
        """Map Web4 4-5 field context to canonical 5-field."""
        if domain == "emotional":
            # Web4: current_frustration, recent_failure_rate, atp_stress, interaction_complexity
            return CanonicalContext(
                primary_metric=web4_context.get("current_frustration", 0.0),
                recent_trend=web4_context.get("recent_failure_rate", 0.0),
                complexity=web4_context.get("interaction_complexity", 0.5),
                stability=1.0 - web4_context.get("atp_stress", 0.0),  # Inverse of stress
                coordination=0.5  # Not in Web4
            )
        elif domain == "quality":
            # Web4: current_relationship_quality, recent_avg_outcome, trust_alignment, interaction_risk_to_quality
            return CanonicalContext(
                primary_metric=web4_context.get("current_relationship_quality", 0.5),
                recent_trend=web4_context.get("recent_avg_outcome", 0.5),
                complexity=web4_context.get("interaction_risk_to_quality", 0.0),
                stability=web4_context.get("trust_alignment", 0.5),
                coordination=0.5  # Not in Web4
            )
        elif domain == "attention":
            # Web4: atp_available, atp_cost, atp_reserve_needed, interaction_count, expected_benefit
            return CanonicalContext(
                primary_metric=web4_context.get("atp_available", 100.0) / 100.0,
                recent_trend=web4_context.get("atp_cost", 20.0) / 100.0,
                complexity=web4_context.get("atp_reserve_needed", 30.0) / 100.0,
                stability=web4_context.get("expected_benefit", 0.5),
                coordination=min(1.0, web4_context.get("interaction_count", 1.0) / 10.0)  # Normalize
            )
        else:
            return CanonicalContext(
                primary_metric=0.5,
                recent_trend=0.5,
                complexity=0.5,
                stability=0.5,
                coordination=0.5
            )


class IntegratedFederationSystem:
    """
    Integrated pattern federation combining:
    - Thor's projection approach (Sessions 153-155)
    - Legion's normalization approach (Sessions 118-119)

    Pipeline:
    1. Project patterns to domain-specific contexts (Thor)
    2. Infer provenance metadata (Thor Session 155)
    3. Normalize to canonical schema (Legion Session 118)
    4. Apply distributional balancing (Legion Session 119)
    5. Quality-weight by provenance (Thor Session 155)
    """

    def __init__(self, target_distribution: Optional[Dict[str, float]] = None):
        """
        Initialize integrated federation system.

        Args:
            target_distribution: Target domain proportions (e.g., {"emotional": 0.33, ...})
        """
        self.target_distribution = target_distribution or {
            "emotional": 0.33,
            "quality": 0.34,
            "attention": 0.33
        }

        # Statistics
        self.stats = {
            "total_patterns": 0,
            "by_source": {},
            "by_domain": {},
            "by_provenance": {},
            "quality_scores": []
        }

    def project_pattern(
        self,
        pattern: Dict[str, Any],
        target_domain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Project pattern to target domain (Thor's approach).

        Extracts domain-specific context from multi-domain pattern.
        """
        full_context = pattern.get("context", {})
        domain_context = full_context.get(target_domain)

        if not domain_context:
            return None

        # Create projected pattern
        projected = pattern.copy()
        projected["context"] = {target_domain: domain_context}
        projected["projected_domain"] = target_domain

        return projected

    def infer_provenance(
        self,
        pattern: Dict[str, Any],
        source_system: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        Infer pattern provenance (Thor's Session 154-155 insight).

        SAGE: Credit assignment → all patterns are DECISION type
        Web4: Multi-perspective → check if domain won decision

        Returns dict for JSON serialization.
        """
        # Domain priority mapping
        priority_map = {
            "emotional": 1,
            "quality": 2,
            "attention": 3,
            "grounding": 4,
            "authorization": 5
        }

        # Extract decision info
        coordinated = pattern.get("coordinated_decision", {})
        decision_conf = coordinated.get("decision_confidence", 0.7)

        if source_system == "sage":
            # SAGE uses credit assignment - pattern exists because domain decided
            provenance = PatternProvenance(
                provenance_type=PatternProvenanceType.DECISION,
                source_system="sage",
                decision_confidence=decision_conf,
                was_deciding_domain=True,
                domain_priority=priority_map.get(domain, 3)
            )
        else:  # web4
            # Web4 uses multi-perspective - check if this domain won
            ep_preds = pattern.get("ep_predictions", {})
            domain_pred = ep_preds.get(domain, {})
            domain_rec = domain_pred.get("recommendation", "proceed")
            final_decision = coordinated.get("final_decision", "proceed")

            was_winner = (domain_rec == final_decision)
            prov_type = PatternProvenanceType.DECISION if was_winner else PatternProvenanceType.OBSERVATION

            provenance = PatternProvenance(
                provenance_type=prov_type,
                source_system="web4",
                decision_confidence=decision_conf,
                was_deciding_domain=was_winner,
                domain_priority=priority_map.get(domain, 2)
            )

        provenance.quality_weight = provenance.compute_quality_weight()

        # Return as dict for JSON serialization
        return {
            "provenance_type": provenance.provenance_type.value,
            "source_system": provenance.source_system,
            "decision_confidence": provenance.decision_confidence,
            "was_deciding_domain": provenance.was_deciding_domain,
            "domain_priority": provenance.domain_priority,
            "quality_weight": provenance.quality_weight
        }

    def normalize_to_canonical(
        self,
        pattern: Dict[str, Any],
        source_system: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        Normalize pattern to canonical schema (Legion's approach).

        Converts domain-specific context to canonical 5-field representation.
        """
        # Extract domain context
        domain_context = pattern["context"][domain]

        # Map to canonical
        if source_system == "sage":
            canonical = CanonicalContext.from_sage(domain_context, domain)
        else:  # web4
            canonical = CanonicalContext.from_web4(domain_context, domain)

        # Update pattern with canonical context
        normalized = pattern.copy()
        normalized["context"] = {domain: asdict(canonical)}
        normalized["canonical_schema"] = True

        return normalized

    def federate_corpora(
        self,
        sage_patterns: List[Dict[str, Any]],
        web4_patterns: List[Dict[str, Any]],
        target_domains: List[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Create federated corpus with full integration pipeline.

        Pipeline:
        1. Project to target domains
        2. Infer provenance
        3. Normalize to canonical schema
        4. Collect statistics

        Args:
            sage_patterns: SAGE pattern corpus
            web4_patterns: Web4 pattern corpus
            target_domains: Domains to include (default: emotional, quality, attention)

        Returns:
            (federated_patterns, statistics)
        """
        if target_domains is None:
            target_domains = ["emotional", "quality", "attention"]

        federated = []
        stats = {
            "sage_patterns": len(sage_patterns),
            "web4_patterns": len(web4_patterns),
            "by_domain": {d: {"sage": 0, "web4": 0, "total": 0} for d in target_domains},
            "by_provenance": {"decision": 0, "observation": 0},
            "avg_quality_weight": 0.0,
            "quality_weights": []
        }

        # Process SAGE patterns
        for pattern in sage_patterns:
            target_domain = pattern.get("target_domain", "emotional")
            if target_domain not in target_domains:
                continue

            # Project
            projected = self.project_pattern(pattern, target_domain)
            if not projected:
                continue

            # Infer provenance (already returns dict)
            provenance = self.infer_provenance(projected, "sage", target_domain)
            projected["provenance"] = provenance

            # Normalize
            normalized = self.normalize_to_canonical(projected, "sage", target_domain)

            federated.append(normalized)

            # Update stats
            stats["by_domain"][target_domain]["sage"] += 1
            stats["by_domain"][target_domain]["total"] += 1
            if provenance["provenance_type"] == "decision":
                stats["by_provenance"]["decision"] += 1
            else:
                stats["by_provenance"]["observation"] += 1
            stats["quality_weights"].append(provenance["quality_weight"])

        # Process Web4 patterns
        for pattern in web4_patterns:
            # Web4 patterns may have multiple domains, extract each
            full_context = pattern.get("context", {})
            for target_domain in target_domains:
                if target_domain not in full_context:
                    continue

                # Project
                projected = self.project_pattern(pattern, target_domain)
                if not projected:
                    continue

                # Infer provenance (already returns dict)
                provenance = self.infer_provenance(projected, "web4", target_domain)
                projected["provenance"] = provenance

                # Normalize
                normalized = self.normalize_to_canonical(projected, "web4", target_domain)

                federated.append(normalized)

                # Update stats
                stats["by_domain"][target_domain]["web4"] += 1
                stats["by_domain"][target_domain]["total"] += 1
                if provenance["provenance_type"] == "decision":
                    stats["by_provenance"]["decision"] += 1
                else:
                    stats["by_provenance"]["observation"] += 1
                stats["quality_weights"].append(provenance["quality_weight"])

        # Compute averages
        if stats["quality_weights"]:
            stats["avg_quality_weight"] = sum(stats["quality_weights"]) / len(stats["quality_weights"])

        stats["total_federated"] = len(federated)

        return federated, stats


def main():
    """Test integrated federation system."""
    print("=" * 80)
    print("Session 120: Integrated Pattern Federation System")
    print("=" * 80)
    print()
    print("Combining:")
    print("  • Thor's projection approach (Sessions 153-155)")
    print("  • Legion's normalization approach (Sessions 118-119)")
    print()

    # Initialize system
    system = IntegratedFederationSystem()

    # Load test data (if available)
    sage_path = Path(__file__).parent.parent.parent / "HRM" / "sage" / "experiments" / "ep_pattern_corpus_balanced_250.json"
    web4_path = Path(__file__).parent / "ep_pattern_corpus_web4_native.json"

    if not sage_path.exists() or not web4_path.exists():
        print(f"Note: Test corpora not found. System ready for use with:")
        print(f"  sage_patterns = load_sage_patterns()")
        print(f"  web4_patterns = load_web4_patterns()")
        print(f"  federated, stats = system.federate_corpora(sage_patterns, web4_patterns)")
        return

    # Load patterns
    print(f"Loading SAGE patterns from: {sage_path.name}")
    with open(sage_path, 'r') as f:
        sage_data = json.load(f)
    sage_patterns = sage_data.get("patterns", [])

    print(f"Loading Web4 patterns from: {web4_path.name}")
    with open(web4_path, 'r') as f:
        web4_data = json.load(f)
    web4_patterns = web4_data.get("patterns", [])

    print(f"  SAGE: {len(sage_patterns)} patterns")
    print(f"  Web4: {len(web4_patterns)} patterns")
    print()

    # Federate
    print("Federating corpora with integrated pipeline...")
    federated, stats = system.federate_corpora(sage_patterns, web4_patterns)

    print()
    print("Federation Results:")
    print(f"  Total federated patterns: {stats['total_federated']}")
    print()
    print("By Domain:")
    for domain, counts in sorted(stats["by_domain"].items()):
        print(f"  {domain:15}: {counts['total']:3} total ({counts['sage']:3} SAGE + {counts['web4']:3} Web4)")
    print()
    print("By Provenance:")
    print(f"  Decision patterns:    {stats['by_provenance']['decision']:3} ({stats['by_provenance']['decision']/stats['total_federated']*100:.1f}%)")
    print(f"  Observation patterns: {stats['by_provenance']['observation']:3} ({stats['by_provenance']['observation']/stats['total_federated']*100:.1f}%)")
    print()
    print(f"Average Quality Weight: {stats['avg_quality_weight']:.3f}")
    print()

    # Save federated corpus
    output_path = Path(__file__).parent / "ep_pattern_corpus_integrated_federation.json"
    output_data = {
        "patterns": federated,
        "metadata": {
            "created": datetime.now().isoformat(),
            "approach": "integrated_federation",
            "thor_sessions": "153-155",
            "legion_sessions": "118-119",
            "session": "120",
            "statistics": stats
        }
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved federated corpus to: {output_path.name}")
    print()
    print("=" * 80)
    print("Integration successful!")
    print("=" * 80)


if __name__ == "__main__":
    main()
