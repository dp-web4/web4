#!/usr/bin/env python3
"""
Universal Pattern Schema for Cross-Domain Learning
==================================================

Shared pattern representation enabling bidirectional learning between:
- SAGE (consciousness/quality patterns)
- Web4 (coordination/success patterns)
- Future: Memory, Portal, other domains

Created: December 13, 2025
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import time


class PatternDomain(Enum):
    """Source domain of the pattern."""
    CONSCIOUSNESS = "consciousness"  # SAGE patterns
    COORDINATION = "coordination"     # Web4 patterns
    MEMORY = "memory"                 # Memory patterns (future)
    COMMUNICATION = "communication"   # Portal patterns (future)


class PatternCategory(Enum):
    """High-level pattern category."""
    SUCCESS = "success"         # What leads to success
    FAILURE = "failure"         # What leads to failure
    QUALITY = "quality"         # Quality improvement patterns
    EFFICIENCY = "efficiency"   # Resource optimization patterns
    ADAPTATION = "adaptation"   # Learning/evolution patterns
    NETWORK = "network"         # Topology/connectivity patterns
    EPISTEMIC = "epistemic"     # Knowledge/confidence patterns


@dataclass
class UniversalPattern:
    """
    Cross-domain pattern representation.

    Enables patterns learned in one domain (e.g., SAGE consciousness)
    to be transferred to another domain (e.g., Web4 coordination).
    """

    # Core identification
    pattern_id: str              # Unique identifier
    source_domain: PatternDomain  # Where pattern was learned
    category: PatternCategory    # High-level category

    # Pattern description
    description: str             # Human-readable description
    characteristics: Dict[str, float]  # Characteristic values (0-1 normalized)

    # Statistical validation
    frequency: int               # How often pattern observed
    confidence: float            # Statistical confidence (0-1)
    sample_size: int             # Number of observations
    quality_correlation: float   # Correlation with quality/success (-1 to 1)

    # Temporal tracking
    extraction_timestamp: float  # When pattern was extracted
    first_observed: float        # When pattern first appeared
    last_observed: float         # When pattern last appeared

    # Domain-specific metadata (preserved for round-trip conversion)
    source_metadata: Dict[str, Any] = field(default_factory=dict)

    # Transfer tracking (populated when pattern is imported to new domain)
    transferred_to: List[str] = field(default_factory=list)  # Domains this pattern has been transferred to
    transfer_effectiveness: Dict[str, float] = field(default_factory=dict)  # How well it worked in each domain

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['source_domain'] = self.source_domain.value
        data['category'] = self.category.value
        return data

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict) -> 'UniversalPattern':
        """Create from dictionary."""
        # Convert strings back to enums
        data['source_domain'] = PatternDomain(data['source_domain'])
        data['category'] = PatternCategory(data['category'])
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'UniversalPattern':
        """Deserialize from JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_characteristic(self, name: str, default: float = 0.5) -> float:
        """Get characteristic value with default."""
        return self.characteristics.get(name, default)

    def set_characteristic(self, name: str, value: float):
        """Set characteristic value (normalized 0-1)."""
        self.characteristics[name] = max(0.0, min(1.0, value))

    def mark_transferred(self, target_domain: str, effectiveness: float):
        """Mark pattern as transferred to another domain."""
        if target_domain not in self.transferred_to:
            self.transferred_to.append(target_domain)
        self.transfer_effectiveness[target_domain] = effectiveness

    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if pattern has high confidence."""
        return self.confidence >= threshold

    def is_well_validated(self, min_samples: int = 20) -> bool:
        """Check if pattern has sufficient validation."""
        return self.sample_size >= min_samples


@dataclass
class CharacteristicMapping:
    """
    Mapping between characteristics across domains.

    Example: Web4's "network_density" maps to SAGE's "context_richness"
    """

    source_characteristic: str      # Name in source domain
    target_characteristic: str      # Name in target domain
    source_domain: PatternDomain   # Source domain
    target_domain: PatternDomain   # Target domain

    mapping_strength: float        # Confidence in mapping (0-1)
    analogy_description: str       # Why these map to each other

    # Optional transformation function
    transformation: str = "linear"  # "linear", "inverse", "squared", "custom"
    custom_transform: Optional[callable] = None

    def transform_value(self, value: float) -> float:
        """Transform value from source to target domain."""
        if self.transformation == "linear":
            return value
        elif self.transformation == "inverse":
            return 1.0 - value
        elif self.transformation == "squared":
            return value ** 2
        elif self.transformation == "sqrt":
            return value ** 0.5
        elif self.transformation == "custom" and self.custom_transform:
            return self.custom_transform(value)
        else:
            return value  # Default to linear


# Standard characteristic mappings
STANDARD_MAPPINGS = {
    # Web4 → SAGE mappings
    ('coordination', 'consciousness'): [
        CharacteristicMapping(
            source_characteristic="network_density",
            target_characteristic="context_richness",
            source_domain=PatternDomain.COORDINATION,
            target_domain=PatternDomain.CONSCIOUSNESS,
            mapping_strength=0.9,
            analogy_description="Both measure connectedness: network of agents vs network of concepts"
        ),
        CharacteristicMapping(
            source_characteristic="trust_score",
            target_characteristic="confidence_level",
            source_domain=PatternDomain.COORDINATION,
            target_domain=PatternDomain.CONSCIOUSNESS,
            mapping_strength=0.85,
            analogy_description="Both measure reliability: external trust vs internal confidence"
        ),
        CharacteristicMapping(
            source_characteristic="diversity_score",
            target_characteristic="epistemic_breadth",
            source_domain=PatternDomain.COORDINATION,
            target_domain=PatternDomain.CONSCIOUSNESS,
            mapping_strength=0.9,
            analogy_description="Both measure variety: agent diversity vs concept diversity"
        ),
        CharacteristicMapping(
            source_characteristic="coordination_confidence",
            target_characteristic="response_confidence",
            source_domain=PatternDomain.COORDINATION,
            target_domain=PatternDomain.CONSCIOUSNESS,
            mapping_strength=0.95,
            analogy_description="Both measure self-assessment of quality"
        ),
        CharacteristicMapping(
            source_characteristic="parameter_stability",
            target_characteristic="learning_stability",
            source_domain=PatternDomain.COORDINATION,
            target_domain=PatternDomain.CONSCIOUSNESS,
            mapping_strength=0.75,
            analogy_description="Both measure consistency over time"
        ),
        CharacteristicMapping(
            source_characteristic="objective_coherence",
            target_characteristic="epistemic_coherence",
            source_domain=PatternDomain.COORDINATION,
            target_domain=PatternDomain.CONSCIOUSNESS,
            mapping_strength=0.9,
            analogy_description="Both measure internal alignment"
        ),
        CharacteristicMapping(
            source_characteristic="improvement_rate",
            target_characteristic="quality_trajectory",
            source_domain=PatternDomain.COORDINATION,
            target_domain=PatternDomain.CONSCIOUSNESS,
            mapping_strength=0.8,
            analogy_description="Both measure evolution over time"
        ),
        CharacteristicMapping(
            source_characteristic="adaptation_frustration",
            target_characteristic="metabolic_stress",
            source_domain=PatternDomain.COORDINATION,
            target_domain=PatternDomain.CONSCIOUSNESS,
            mapping_strength=0.75,
            analogy_description="Both measure difficulty/effort"
        ),
    ],

    # SAGE → Web4 mappings (reverse of above)
    ('consciousness', 'coordination'): [
        CharacteristicMapping(
            source_characteristic="context_richness",
            target_characteristic="network_density",
            source_domain=PatternDomain.CONSCIOUSNESS,
            target_domain=PatternDomain.COORDINATION,
            mapping_strength=0.9,
            analogy_description="Context richness in consciousness maps to network density in coordination"
        ),
        CharacteristicMapping(
            source_characteristic="confidence_level",
            target_characteristic="trust_score",
            source_domain=PatternDomain.CONSCIOUSNESS,
            target_domain=PatternDomain.COORDINATION,
            mapping_strength=0.85,
            analogy_description="Internal confidence maps to external trust"
        ),
        CharacteristicMapping(
            source_characteristic="epistemic_breadth",
            target_characteristic="diversity_score",
            source_domain=PatternDomain.CONSCIOUSNESS,
            target_domain=PatternDomain.COORDINATION,
            mapping_strength=0.9,
            analogy_description="Concept diversity maps to agent diversity"
        ),
        CharacteristicMapping(
            source_characteristic="response_confidence",
            target_characteristic="coordination_confidence",
            source_domain=PatternDomain.CONSCIOUSNESS,
            target_domain=PatternDomain.COORDINATION,
            mapping_strength=0.95,
            analogy_description="Response confidence maps to coordination confidence"
        ),
        CharacteristicMapping(
            source_characteristic="learning_stability",
            target_characteristic="parameter_stability",
            source_domain=PatternDomain.CONSCIOUSNESS,
            target_domain=PatternDomain.COORDINATION,
            mapping_strength=0.75,
            analogy_description="Learning stability maps to parameter stability"
        ),
        CharacteristicMapping(
            source_characteristic="epistemic_coherence",
            target_characteristic="objective_coherence",
            source_domain=PatternDomain.CONSCIOUSNESS,
            target_domain=PatternDomain.COORDINATION,
            mapping_strength=0.9,
            analogy_description="Epistemic coherence maps to objective coherence"
        ),
        CharacteristicMapping(
            source_characteristic="quality_trajectory",
            target_characteristic="improvement_rate",
            source_domain=PatternDomain.CONSCIOUSNESS,
            target_domain=PatternDomain.COORDINATION,
            mapping_strength=0.8,
            analogy_description="Quality trajectory maps to improvement rate"
        ),
        CharacteristicMapping(
            source_characteristic="metabolic_stress",
            target_characteristic="adaptation_frustration",
            source_domain=PatternDomain.CONSCIOUSNESS,
            target_domain=PatternDomain.COORDINATION,
            mapping_strength=0.75,
            analogy_description="Metabolic stress maps to adaptation frustration"
        ),
    ]
}


def get_mappings(
    source_domain: PatternDomain,
    target_domain: PatternDomain
) -> List[CharacteristicMapping]:
    """Get characteristic mappings between two domains."""
    key = (source_domain.value, target_domain.value)
    return STANDARD_MAPPINGS.get(key, [])


def map_characteristic(
    characteristic_name: str,
    source_domain: PatternDomain,
    target_domain: PatternDomain
) -> Optional[str]:
    """
    Map a characteristic name from source to target domain.

    Args:
        characteristic_name: Name of characteristic in source domain
        source_domain: Source domain
        target_domain: Target domain

    Returns:
        Corresponding characteristic name in target domain, or None if no mapping
    """
    mappings = get_mappings(source_domain, target_domain)

    for mapping in mappings:
        if mapping.source_characteristic == characteristic_name:
            return mapping.target_characteristic

    return None


if __name__ == "__main__":
    print("Universal Pattern Schema for Cross-Domain Learning")
    print("=" * 80)
    print()

    print("Supported Domains:")
    for domain in PatternDomain:
        print(f"  - {domain.value}")
    print()

    print("Pattern Categories:")
    for category in PatternCategory:
        print(f"  - {category.value}")
    print()

    print("Standard Characteristic Mappings:")
    print()

    print("Web4 (Coordination) → SAGE (Consciousness):")
    mappings_w2s = get_mappings(PatternDomain.COORDINATION, PatternDomain.CONSCIOUSNESS)
    for mapping in mappings_w2s:
        print(f"  {mapping.source_characteristic:25s} → {mapping.target_characteristic:25s} "
              f"(strength: {mapping.mapping_strength:.2f})")
        print(f"    Analogy: {mapping.analogy_description}")
    print()

    print("SAGE (Consciousness) → Web4 (Coordination):")
    mappings_s2w = get_mappings(PatternDomain.CONSCIOUSNESS, PatternDomain.COORDINATION)
    for mapping in mappings_s2w[:3]:  # Show first 3
        print(f"  {mapping.source_characteristic:25s} → {mapping.target_characteristic:25s} "
              f"(strength: {mapping.mapping_strength:.2f})")
    print(f"  ... and {len(mappings_s2w)-3} more")
    print()

    # Example pattern
    example = UniversalPattern(
        pattern_id="sage_quality_high_context",
        source_domain=PatternDomain.CONSCIOUSNESS,
        category=PatternCategory.QUALITY,
        description="High context richness correlates with high quality responses",
        characteristics={
            "context_richness": 0.85,
            "confidence_level": 0.90,
            "epistemic_breadth": 0.75
        },
        frequency=127,
        confidence=0.92,
        sample_size=150,
        quality_correlation=0.87,
        extraction_timestamp=time.time(),
        first_observed=time.time() - 86400,  # 1 day ago
        last_observed=time.time()
    )

    print("Example Pattern:")
    print(json.dumps(example.to_dict(), indent=2))
    print()
