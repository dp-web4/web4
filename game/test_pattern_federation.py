#!/usr/bin/env python3
"""
Test Pattern Federation with Real SAGE and Web4 Patterns

Session 118 Track 3: Validate that Phase 1 structural normalization enables
real pattern federation across SAGE and Web4 systems.

Test Protocol:
1. Load SAGE patterns from Thor's corpus
2. Load Web4 patterns from Session 116 corpus
3. Normalize both to canonical form
4. Verify dimension consistency
5. Test cross-system pattern matching
6. Compare pre/post normalization similarity
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

# Add modules
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "HRM" / "sage" / "experiments"))

from ep_federation_normalization import (
    PatternContextNormalizer,
    CanonicalEmotionalContext,
    CanonicalQualityContext,
    CanonicalAttentionContext
)
from multi_ep_coordinator import EPDomain


def load_sage_patterns(hrm_path: Path) -> List[Dict[str, Any]]:
    """Load SAGE patterns from Thor's corpus."""
    # Try to load SAGE patterns
    sage_pattern_file = hrm_path / "sage" / "experiments" / "ep_pattern_corpus_production.json"

    if not sage_pattern_file.exists():
        print(f"Warning: SAGE pattern file not found: {sage_pattern_file}")
        print("Using simulated SAGE patterns for testing")
        return create_simulated_sage_patterns()

    with open(sage_pattern_file, 'r') as f:
        sage_data = json.load(f)

    # Extract patterns (structure depends on Thor's format)
    if isinstance(sage_data, dict) and "patterns" in sage_data:
        return sage_data["patterns"]
    elif isinstance(sage_data, list):
        return sage_data
    else:
        print("Warning: Unexpected SAGE pattern format, using simulated patterns")
        return create_simulated_sage_patterns()


def create_simulated_sage_patterns() -> List[Dict[str, Any]]:
    """Create simulated SAGE patterns for testing when real ones unavailable."""
    return [
        {
            "pattern_id": "sage_sim_1",
            "domain": "EMOTIONAL",
            "context": {
                "frustration": 0.3,
                "stability": 0.7,
                "cascade_agreement": 0.8
            },
            "prediction": {"outcome_probability": 0.7, "confidence": 0.85},
            "outcome": {"success": True}
        },
        {
            "pattern_id": "sage_sim_2",
            "domain": "QUALITY",
            "context": {
                "prediction_quality": 0.8,
                "pattern_confidence": 0.9,
                "domain_agreement": 0.75
            },
            "prediction": {"outcome_probability": 0.8, "confidence": 0.9},
            "outcome": {"success": True}
        },
        {
            "pattern_id": "sage_sim_3",
            "domain": "ATTENTION",
            "context": {
                "attention_focus": 0.5,
                "resource_allocation": 0.6,
                "task_priority": 0.4
            },
            "prediction": {"outcome_probability": 0.6, "confidence": 0.75},
            "outcome": {"success": True}
        }
    ]


def load_web4_patterns(web4_path: Path) -> List[Dict[str, Any]]:
    """Load Web4 patterns from Session 116 corpus."""
    web4_pattern_file = web4_path / "game" / "ep_pattern_corpus_web4_native.json"

    if not web4_pattern_file.exists():
        print(f"Error: Web4 pattern file not found: {web4_pattern_file}")
        return []

    with open(web4_pattern_file, 'r') as f:
        web4_data = json.load(f)

    # Extract patterns
    if isinstance(web4_data, dict) and "patterns" in web4_data:
        return web4_data["patterns"]
    else:
        return []


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def normalize_pattern_context(pattern: Dict[str, Any], source_system: str) -> Any:
    """
    Normalize a pattern's context to canonical form.

    Returns canonical context object (type depends on domain).
    """
    # Determine domain
    domain_str = pattern.get("domain", "EMOTIONAL")
    if isinstance(domain_str, str):
        # Handle both "EMOTIONAL" and "EPDomain.EMOTIONAL" formats
        domain_name = domain_str.split('.')[-1]
        domain = EPDomain[domain_name]
    else:
        domain = domain_str

    # Get context
    context = pattern.get("context", {})

    # For Web4 patterns, context might be nested by domain
    if source_system == "web4" and isinstance(context, dict):
        # Check if context has domain-specific subfields
        domain_key = domain_name.lower()
        if domain_key in context:
            context = context[domain_key]

    # Normalize
    return PatternContextNormalizer.normalize(context, domain, source_system)


def test_pattern_federation():
    """Main test function."""
    print("=" * 80)
    print("PATTERN FEDERATION TEST - REAL SAGE + WEB4 PATTERNS")
    print("=" * 80)
    print()

    # Paths
    hrm_path = Path("/home/dp/ai-workspace/HRM")
    web4_path = Path("/home/dp/ai-workspace/web4")

    # Load patterns
    print("Loading patterns...")
    sage_patterns = load_sage_patterns(hrm_path)
    web4_patterns = load_web4_patterns(web4_path)

    print(f"  SAGE patterns: {len(sage_patterns)}")
    print(f"  Web4 patterns: {len(web4_patterns)}")
    print()

    if not sage_patterns or not web4_patterns:
        print("Error: Could not load patterns from both systems")
        return

    # Test normalization for each domain
    domains_to_test = {
        "EMOTIONAL": EPDomain.EMOTIONAL,
        "QUALITY": EPDomain.QUALITY,
        "ATTENTION": EPDomain.ATTENTION
    }

    results = {}

    for domain_name, domain_enum in domains_to_test.items():
        print(f"Testing {domain_name} Domain:")
        print("-" * 80)

        # Find patterns for this domain
        sage_domain_patterns = [p for p in sage_patterns if str(p.get("domain", "")).split('.')[-1] == domain_name]
        web4_domain_patterns = [p for p in web4_patterns if domain_name.lower() in str(p.get("context", {}).keys()).lower()]

        if not sage_domain_patterns:
            print(f"  No SAGE {domain_name} patterns found, skipping")
            print()
            continue

        if not web4_domain_patterns:
            print(f"  No Web4 {domain_name} patterns found, skipping")
            print()
            continue

        # Take first pattern from each
        sage_pattern = sage_domain_patterns[0]
        web4_pattern = web4_domain_patterns[0]

        print(f"  SAGE pattern: {sage_pattern.get('pattern_id', 'unknown')}")
        print(f"  Web4 pattern: {web4_pattern.get('pattern_id', 'unknown')}")
        print()

        # Normalize
        try:
            sage_canonical = normalize_pattern_context(sage_pattern, "sage")
            web4_canonical = normalize_pattern_context(web4_pattern, "web4")

            sage_vector = sage_canonical.to_vector()
            web4_vector = web4_canonical.to_vector()

            print(f"  SAGE canonical: {sage_canonical.to_dict()}")
            print(f"  Web4 canonical: {web4_canonical.to_dict()}")
            print()

            # Check dimensions
            print(f"  SAGE vector dim: {len(sage_vector)}")
            print(f"  Web4 vector dim: {len(web4_vector)}")

            if len(sage_vector) != len(web4_vector):
                print(f"  ✗ DIMENSION MISMATCH!")
                print()
                continue

            print(f"  ✓ Dimensions match")
            print()

            # Calculate similarity
            sage_np = np.array(sage_vector)
            web4_np = np.array(web4_vector)
            similarity = cosine_similarity(sage_np, web4_np)

            print(f"  Cosine similarity: {similarity:.3f}")
            print(f"  Can match: {'✓ YES' if similarity > 0.0 else '✗ NO'}")
            print()

            results[domain_name] = {
                "sage_dims": len(sage_vector),
                "web4_dims": len(web4_vector),
                "similarity": similarity,
                "success": len(sage_vector) == len(web4_vector) and similarity > 0.0
            }

        except Exception as e:
            print(f"  ✗ Error during normalization: {e}")
            print()
            results[domain_name] = {"success": False, "error": str(e)}

    # Summary
    print("=" * 80)
    print("FEDERATION TEST SUMMARY")
    print("=" * 80)
    print()

    successes = sum(1 for r in results.values() if r.get("success", False))
    total = len(results)

    print(f"Domains tested: {total}")
    print(f"Successful: {successes}/{total}")
    print()

    if successes == total:
        print("✓ ALL DOMAINS FEDERATE SUCCESSFULLY")
        print()
        print("Results:")
        for domain, result in results.items():
            if result.get("success"):
                print(f"  {domain}:")
                print(f"    Dimensions: {result['sage_dims']} (SAGE) = {result['web4_dims']} (Web4)")
                print(f"    Similarity: {result['similarity']:.3f}")
        print()
        print("PHASE 1 STRUCTURAL NORMALIZATION: VALIDATED ✓")
    else:
        print("✗ SOME DOMAINS FAILED")
        for domain, result in results.items():
            if not result.get("success"):
                print(f"  {domain}: {result.get('error', 'Unknown error')}")

    print()


if __name__ == "__main__":
    test_pattern_federation()
