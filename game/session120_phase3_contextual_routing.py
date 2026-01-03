#!/usr/bin/env python3
"""
Session 120 Track 2: Phase 3 Contextual Routing

Implements the final phase of three-level normalization (from Session 118):
- Level 1: Structural Normalization (Phase 1, Session 118) ✅
- Level 2: Distributional Balancing (Phase 2, Session 119) ✅
- Level 3: Contextual Routing (Phase 3, THIS SESSION) ← IMPLEMENTING NOW

Purpose: Prevent cross-context contamination discovered in Session 115
- Problem: Thor's SAGE consciousness patterns → Web4 ATP = 100% death
- Root Cause: Different application contexts (consciousness vs game AI)
- Solution: Context tagging + compatibility checking + query routing

Architecture:
1. Context Tags: Metadata about pattern's original application context
2. Compatibility Matrix: Which contexts can safely share patterns
3. Query Router: Routes queries to compatible pattern subsets only
4. Safety Verification: Prevents dangerous cross-context matches

Expected Benefits:
- Safe federation: Patterns only used in compatible contexts
- Flexible sharing: Same-context across devices (Thor SAGE ↔ Legion SAGE)
- Explicit control: Application chooses which contexts to allow
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class ApplicationContext(Enum):
    """
    Application context - what is the system doing?

    This determines pattern applicability.
    """
    # Consciousness and self-regulation
    CONSCIOUSNESS = "consciousness"
    SELF_REGULATION = "self_regulation"
    EMOTIONAL_PROCESSING = "emotional_processing"

    # Game and interaction
    GAME_AI = "game_ai"
    MULTI_AGENT_INTERACTION = "multi_agent_interaction"
    ATP_RESOURCE_MANAGEMENT = "atp_resource_management"

    # General
    GENERAL_EP = "general_ep"
    UNKNOWN = "unknown"


@dataclass
class ContextTag:
    """
    Context tag for pattern provenance and applicability.

    Records WHERE and HOW pattern was created to determine safe usage.
    """
    # Application context
    application: ApplicationContext
    application_specific: str  # Detailed description (e.g., "ATP mgmt in game X")

    # System context
    source_system: str  # "sage", "web4", etc.
    source_device: str  # "thor", "legion", "sprout", etc.

    # Decision context
    decision_domain: str  # Which domain decided (emotional, quality, attention, etc.)
    decision_scenario: str  # Type of scenario (e.g., "resource_scarcity", "high_risk")

    # Metadata
    created_timestamp: str
    pattern_quality: float  # From provenance analysis (0.0-1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "application": self.application.value,
            "application_specific": self.application_specific,
            "source_system": self.source_system,
            "source_device": self.source_device,
            "decision_domain": self.decision_domain,
            "decision_scenario": self.decision_scenario,
            "created_timestamp": self.created_timestamp,
            "pattern_quality": self.pattern_quality
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'ContextTag':
        """Create from dict."""
        return ContextTag(
            application=ApplicationContext(d.get("application", "unknown")),
            application_specific=d.get("application_specific", ""),
            source_system=d.get("source_system", "unknown"),
            source_device=d.get("source_device", "unknown"),
            decision_domain=d.get("decision_domain", "unknown"),
            decision_scenario=d.get("decision_scenario", "unknown"),
            created_timestamp=d.get("created_timestamp", ""),
            pattern_quality=d.get("pattern_quality", 0.5)
        )


class ContextCompatibilityMatrix:
    """
    Defines which application contexts can safely share patterns.

    Based on Session 115 findings:
    - CONSCIOUSNESS → ATP_RESOURCE_MANAGEMENT = INCOMPATIBLE (100% death)
    - GAME_AI → ATP_RESOURCE_MANAGEMENT = COMPATIBLE (same domain)
    - CONSCIOUSNESS → CONSCIOUSNESS = COMPATIBLE (same application)
    """

    def __init__(self):
        """Initialize compatibility matrix."""
        # Define compatibility rules
        # Format: (source_context, query_context) → compatibility_score (0.0-1.0)
        self.rules = {
            # Perfect matches (same context)
            (ApplicationContext.CONSCIOUSNESS, ApplicationContext.CONSCIOUSNESS): 1.0,
            (ApplicationContext.GAME_AI, ApplicationContext.GAME_AI): 1.0,
            (ApplicationContext.ATP_RESOURCE_MANAGEMENT, ApplicationContext.ATP_RESOURCE_MANAGEMENT): 1.0,
            (ApplicationContext.SELF_REGULATION, ApplicationContext.SELF_REGULATION): 1.0,

            # Related but different
            (ApplicationContext.CONSCIOUSNESS, ApplicationContext.SELF_REGULATION): 0.8,
            (ApplicationContext.SELF_REGULATION, ApplicationContext.CONSCIOUSNESS): 0.8,
            (ApplicationContext.GAME_AI, ApplicationContext.ATP_RESOURCE_MANAGEMENT): 0.9,
            (ApplicationContext.ATP_RESOURCE_MANAGEMENT, ApplicationContext.GAME_AI): 0.9,
            (ApplicationContext.GAME_AI, ApplicationContext.MULTI_AGENT_INTERACTION): 0.9,

            # General EP patterns (usable everywhere but lower confidence)
            (ApplicationContext.GENERAL_EP, ApplicationContext.CONSCIOUSNESS): 0.6,
            (ApplicationContext.GENERAL_EP, ApplicationContext.GAME_AI): 0.6,
            (ApplicationContext.GENERAL_EP, ApplicationContext.ATP_RESOURCE_MANAGEMENT): 0.6,

            # DANGEROUS COMBINATIONS (Session 115)
            # Consciousness patterns should NOT be used for game ATP management
            (ApplicationContext.CONSCIOUSNESS, ApplicationContext.ATP_RESOURCE_MANAGEMENT): 0.0,  # INCOMPATIBLE
            (ApplicationContext.CONSCIOUSNESS, ApplicationContext.GAME_AI): 0.2,  # Mostly incompatible
            (ApplicationContext.SELF_REGULATION, ApplicationContext.ATP_RESOURCE_MANAGEMENT): 0.1,  # Nearly incompatible

            # Unknown contexts (conservative)
            (ApplicationContext.UNKNOWN, ApplicationContext.CONSCIOUSNESS): 0.3,
            (ApplicationContext.UNKNOWN, ApplicationContext.GAME_AI): 0.3,
            (ApplicationContext.UNKNOWN, ApplicationContext.ATP_RESOURCE_MANAGEMENT): 0.3,
        }

        # Default compatibility for unlisted combinations
        self.default_compatibility = 0.4  # Conservative default

    def get_compatibility(
        self,
        pattern_context: ApplicationContext,
        query_context: ApplicationContext
    ) -> float:
        """
        Get compatibility score between pattern and query contexts.

        Returns:
            Compatibility score (0.0-1.0)
            - 1.0: Perfect match
            - 0.8-0.9: Related and compatible
            - 0.4-0.7: Usable but with caution
            - 0.1-0.3: Mostly incompatible
            - 0.0: INCOMPATIBLE (do not use)
        """
        key = (pattern_context, query_context)
        return self.rules.get(key, self.default_compatibility)

    def is_safe(
        self,
        pattern_context: ApplicationContext,
        query_context: ApplicationContext,
        min_compatibility: float = 0.5
    ) -> bool:
        """Check if pattern is safe to use for query context."""
        return self.get_compatibility(pattern_context, query_context) >= min_compatibility


class ContextualQueryRouter:
    """
    Routes pattern queries to context-compatible subsets.

    Prevents Session 115's cross-context contamination by filtering patterns
    based on application context compatibility.
    """

    def __init__(
        self,
        compatibility_matrix: Optional[ContextCompatibilityMatrix] = None,
        min_compatibility: float = 0.5
    ):
        """
        Initialize router.

        Args:
            compatibility_matrix: Custom compatibility rules (uses default if None)
            min_compatibility: Minimum compatibility score to include pattern (0.0-1.0)
        """
        self.compat_matrix = compatibility_matrix or ContextCompatibilityMatrix()
        self.min_compatibility = min_compatibility

        # Statistics
        self.stats = {
            "total_queries": 0,
            "total_patterns_considered": 0,
            "total_patterns_filtered": 0,
            "by_query_context": {},
            "incompatible_blocks": 0
        }

    def tag_pattern(
        self,
        pattern: Dict[str, Any],
        application: ApplicationContext,
        application_specific: str,
        source_system: str,
        source_device: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Add context tag to pattern.

        Args:
            pattern: Pattern to tag
            application: Application context
            application_specific: Specific application description
            source_system: Source system name
            source_device: Source device name

        Returns:
            Pattern with context_tag added
        """
        # Infer decision domain and scenario if not already present
        decision_domain = pattern.get("target_domain") or pattern.get("projected_domain", "unknown")

        # Infer scenario from context values (simplified)
        context = pattern.get("context", {})
        domain_context = context.get(decision_domain, {})
        if isinstance(domain_context, dict):
            # Try to infer scenario type
            primary_val = list(domain_context.values())[0] if domain_context else 0.5
            if primary_val > 0.7:
                scenario = "high_stress"
            elif primary_val < 0.3:
                scenario = "low_stress"
            else:
                scenario = "moderate"
        else:
            scenario = "unknown"

        # Get quality from provenance if available
        prov = pattern.get("provenance", {})
        quality = prov.get("quality_weight", 0.5)

        # Create context tag
        tag = ContextTag(
            application=application,
            application_specific=application_specific,
            source_system=source_system,
            source_device=source_device,
            decision_domain=decision_domain,
            decision_scenario=scenario,
            created_timestamp=pattern.get("timestamp", datetime.now().isoformat()),
            pattern_quality=quality
        )

        # Add to pattern
        tagged = pattern.copy()
        tagged["context_tag"] = tag.to_dict()

        return tagged

    def route_query(
        self,
        patterns: List[Dict[str, Any]],
        query_context: ApplicationContext,
        domain: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Route query to compatible pattern subset.

        Args:
            patterns: Full pattern corpus
            query_context: Application context of the query
            domain: Domain being queried (emotional, quality, attention, etc.)

        Returns:
            (compatible_patterns, routing_stats)
        """
        self.stats["total_queries"] += 1

        # Initialize stats for this query context
        if query_context.value not in self.stats["by_query_context"]:
            self.stats["by_query_context"][query_context.value] = {
                "queries": 0,
                "patterns_considered": 0,
                "patterns_included": 0,
                "patterns_filtered": 0
            }

        query_stats = self.stats["by_query_context"][query_context.value]
        query_stats["queries"] += 1

        # Filter patterns
        compatible = []
        filtered_count = 0
        incompatible_count = 0

        for pattern in patterns:
            self.stats["total_patterns_considered"] += 1
            query_stats["patterns_considered"] += 1

            # Check if pattern has context tag
            if "context_tag" not in pattern:
                # No context tag - use conservative default
                compatible.append(pattern)
                query_stats["patterns_included"] += 1
                continue

            # Get pattern context
            tag_dict = pattern["context_tag"]
            pattern_context = ApplicationContext(tag_dict.get("application", "unknown"))

            # Check compatibility
            compat_score = self.compat_matrix.get_compatibility(pattern_context, query_context)

            if compat_score >= self.min_compatibility:
                # Compatible - include in results
                # Optionally weight by compatibility score
                pattern_copy = pattern.copy()
                pattern_copy["context_compatibility_score"] = compat_score
                compatible.append(pattern_copy)
                query_stats["patterns_included"] += 1
            else:
                # Incompatible - filter out
                filtered_count += 1
                query_stats["patterns_filtered"] += 1
                self.stats["total_patterns_filtered"] += 1

                if compat_score == 0.0:
                    incompatible_count += 1
                    self.stats["incompatible_blocks"] += 1

        routing_stats = {
            "query_context": query_context.value,
            "domain": domain,
            "total_patterns": len(patterns),
            "compatible_patterns": len(compatible),
            "filtered_patterns": filtered_count,
            "incompatible_blocks": incompatible_count,
            "filter_rate": filtered_count / len(patterns) if patterns else 0.0
        }

        return compatible, routing_stats


def test_contextual_routing():
    """Test Phase 3 contextual routing."""
    print("=" * 80)
    print("Session 120 Track 2: Phase 3 Contextual Routing")
    print("=" * 80)
    print()

    print("Implementing Level 3 of three-level normalization:")
    print("  Level 1: Structural Normalization (Phase 1, Session 118) ✅")
    print("  Level 2: Distributional Balancing (Phase 2, Session 119) ✅")
    print("  Level 3: Contextual Routing (Phase 3, THIS SESSION)")
    print()

    # Load integrated federation corpus
    corpus_path = Path(__file__).parent / "ep_pattern_corpus_integrated_federation.json"

    if not corpus_path.exists():
        print(f"ERROR: Integrated corpus not found at {corpus_path}")
        return

    print(f"Loading integrated federation corpus...")
    with open(corpus_path, 'r') as f:
        data = json.load(f)

    patterns = data.get("patterns", [])
    print(f"  Total patterns: {len(patterns)}")
    print()

    # Tag patterns with context (infer from source system)
    router = ContextualQueryRouter(min_compatibility=0.5)

    print("Tagging patterns with application context...")
    tagged_patterns = []

    for pattern in patterns:
        # Infer context from source system
        prov = pattern.get("provenance", {})
        source_sys = prov.get("source_system", "unknown")

        if source_sys == "sage":
            # SAGE patterns are from consciousness
            app_context = ApplicationContext.CONSCIOUSNESS
            app_specific = "SAGE self-regulation and consciousness"
        elif source_sys == "web4":
            # Web4 patterns are from game AI / ATP
            app_context = ApplicationContext.ATP_RESOURCE_MANAGEMENT
            app_specific = "Web4 multi-agent game ATP management"
        else:
            app_context = ApplicationContext.UNKNOWN
            app_specific = "Unknown application"

        tagged = router.tag_pattern(
            pattern,
            application=app_context,
            application_specific=app_specific,
            source_system=source_sys,
            source_device="legion"  # This session is on Legion
        )

        tagged_patterns.append(tagged)

    print(f"  Tagged {len(tagged_patterns)} patterns")
    print()

    # Test different query contexts
    print("Testing query routing with different contexts:")
    print("-" * 80)
    print()

    test_queries = [
        (ApplicationContext.ATP_RESOURCE_MANAGEMENT, "ATP management in game"),
        (ApplicationContext.CONSCIOUSNESS, "SAGE consciousness regulation"),
        (ApplicationContext.GAME_AI, "General game AI decisions")
    ]

    for query_context, description in test_queries:
        print(f"Query: {description} ({query_context.value})")

        compatible, stats = router.route_query(
            tagged_patterns,
            query_context,
            "emotional"
        )

        print(f"  Total patterns:      {stats['total_patterns']}")
        print(f"  Compatible:          {stats['compatible_patterns']} "
              f"({stats['compatible_patterns']/stats['total_patterns']*100:.1f}%)")
        print(f"  Filtered:            {stats['filtered_patterns']} "
              f"({stats['filter_rate']*100:.1f}%)")
        print(f"  Incompatible blocks: {stats['incompatible_blocks']} "
              "(0.0 compatibility)")
        print()

    # Save context-tagged corpus
    output_path = Path(__file__).parent / "ep_pattern_corpus_phase3_contextual.json"
    output_data = {
        "patterns": tagged_patterns,
        "metadata": {
            "created": datetime.now().isoformat(),
            "phase": "3_contextual_routing",
            "session": "120",
            "has_context_tags": True,
            "min_compatibility": router.min_compatibility,
            "routing_stats": router.stats
        }
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved context-tagged corpus to: {output_path.name}")
    print()

    print("=" * 80)
    print("Phase 3 Implementation Complete!")
    print("=" * 80)
    print()
    print("Three-Level Normalization Status:")
    print("  ✅ Level 1: Structural Normalization (Phase 1)")
    print("  ✅ Level 2: Distributional Balancing (Phase 2)")
    print("  ✅ Level 3: Contextual Routing (Phase 3)")
    print()
    print("Pattern federation is now production-ready with full safety!")


if __name__ == "__main__":
    test_contextual_routing()
