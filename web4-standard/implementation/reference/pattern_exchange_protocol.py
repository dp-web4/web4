#!/usr/bin/env python3
"""
Pattern Exchange Protocol for Cross-Domain Learning
===================================================

Enables bidirectional pattern transfer between SAGE and Web4:
- Export Web4 coordination patterns → Universal format
- Export SAGE consciousness patterns → Universal format
- Import universal patterns → Web4 coordination patterns
- Import universal patterns → SAGE consciousness patterns

Created: December 13, 2025
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict

from universal_pattern_schema import (
    UniversalPattern,
    PatternDomain,
    PatternCategory,
    CharacteristicMapping,
    get_mappings,
    map_characteristic
)

# Import from Web4 coordination learning
try:
    from web4_coordination_learning import (
        CoordinationPattern,
        PatternType,
        SuccessFactorLearning,
        NetworkInsight,
        ConsolidatedLearnings
    )
    WEB4_AVAILABLE = True
except ImportError:
    WEB4_AVAILABLE = False
    print("Warning: Web4 coordination learning not available")

# Import from SAGE (if available in path)
try:
    import sys
    sys.path.append('/home/dp/ai-workspace/HRM')
    from sage.core.dream_consolidation import (
        MemoryPattern,
        QualityLearning,
        CreativeAssociation,
        ConsolidatedMemory
    )
    SAGE_AVAILABLE = True
except ImportError:
    SAGE_AVAILABLE = False
    print("Warning: SAGE dream consolidation not available")


class Web4ToUniversalConverter:
    """
    Convert Web4 coordination patterns to universal format.

    Enables Web4 to export patterns for import by SAGE or other domains.
    """

    def __init__(self):
        self.mappings = get_mappings(
            PatternDomain.COORDINATION,
            PatternDomain.CONSCIOUSNESS  # Default target, but works for any
        )

    def convert_coordination_pattern(
        self,
        pattern: 'CoordinationPattern',
        pattern_id: Optional[str] = None
    ) -> UniversalPattern:
        """
        Convert Web4 CoordinationPattern to UniversalPattern.

        Args:
            pattern: Web4 coordination pattern
            pattern_id: Optional unique identifier (auto-generated if None)

        Returns:
            UniversalPattern ready for export
        """
        if not WEB4_AVAILABLE:
            raise RuntimeError("Web4 coordination learning not available")

        # Generate pattern ID if not provided
        if pattern_id is None:
            pattern_id = f"web4_{pattern.pattern_type.value}_{int(time.time())}"

        # Map pattern type to category
        category_map = {
            PatternType.SUCCESS: PatternCategory.SUCCESS,
            PatternType.FAILURE: PatternCategory.FAILURE,
            PatternType.NETWORK_TOPOLOGY: PatternCategory.NETWORK,
            PatternType.TRUST_EVOLUTION: PatternCategory.EPISTEMIC,
            PatternType.EPISTEMIC_SHIFT: PatternCategory.EPISTEMIC,
            PatternType.RESOURCE_EFFICIENCY: PatternCategory.EFFICIENCY
        }
        category = category_map.get(pattern.pattern_type, PatternCategory.SUCCESS)

        # Extract characteristics from pattern
        characteristics = {}
        if hasattr(pattern, 'characteristics') and pattern.characteristics:
            for key, value in pattern.characteristics.items():
                # Normalize to 0-1 if needed
                if isinstance(value, (int, float)):
                    characteristics[key] = max(0.0, min(1.0, float(value)))

        # If characteristics not in pattern, extract from known ranges
        if 'network_density_range' in pattern.__dict__:
            nd_range = pattern.network_density_range
            characteristics['network_density'] = (nd_range[0] + nd_range[1]) / 2

        if 'trust_score_range' in pattern.__dict__:
            ts_range = pattern.trust_score_range
            characteristics['trust_score'] = (ts_range[0] + ts_range[1]) / 2

        # Calculate quality correlation from pattern data
        quality_correlation = 0.0
        if pattern.pattern_type == PatternType.SUCCESS:
            quality_correlation = pattern.confidence  # Success patterns correlate positively
        elif pattern.pattern_type == PatternType.FAILURE:
            quality_correlation = -pattern.confidence  # Failure patterns correlate negatively

        # Create universal pattern
        universal = UniversalPattern(
            pattern_id=pattern_id,
            source_domain=PatternDomain.COORDINATION,
            category=category,
            description=pattern.description,
            characteristics=characteristics,
            frequency=pattern.frequency,
            confidence=pattern.confidence,
            sample_size=pattern.frequency,  # Approximate
            quality_correlation=quality_correlation,
            extraction_timestamp=time.time(),
            first_observed=time.time(),  # Unknown, use current
            last_observed=time.time(),
            source_metadata={
                'pattern_type': pattern.pattern_type.value,
                'average_quality': pattern.average_quality,
                'quality_improvement': pattern.quality_improvement,
                'web4_version': '1.0'
            }
        )

        return universal

    def convert_success_factor(
        self,
        factor: 'SuccessFactorLearning',
        pattern_id: Optional[str] = None
    ) -> UniversalPattern:
        """Convert Web4 SuccessFactorLearning to UniversalPattern."""
        if not WEB4_AVAILABLE:
            raise RuntimeError("Web4 coordination learning not available")

        if pattern_id is None:
            pattern_id = f"web4_factor_{factor.factor_name}_{int(time.time())}"

        # Create characteristics from factor
        characteristics = {
            'success_with_factor': factor.success_with_factor,
            'success_without_factor': factor.success_without_factor,
            'correlation_strength': abs(factor.correlation)
        }

        universal = UniversalPattern(
            pattern_id=pattern_id,
            source_domain=PatternDomain.COORDINATION,
            category=PatternCategory.SUCCESS,
            description=f"Success factor: {factor.factor_description}",
            characteristics=characteristics,
            frequency=factor.sample_size,
            confidence=factor.confidence,
            sample_size=factor.sample_size,
            quality_correlation=factor.correlation,
            extraction_timestamp=time.time(),
            first_observed=time.time(),
            last_observed=time.time(),
            source_metadata={
                'factor_name': factor.factor_name,
                'recommendation': factor.recommendation,
                'web4_version': '1.0'
            }
        )

        return universal

    def export_learnings(
        self,
        learnings: 'ConsolidatedLearnings',
        export_path: Optional[Path] = None
    ) -> List[UniversalPattern]:
        """
        Export all Web4 consolidated learnings to universal patterns.

        Args:
            learnings: Web4 consolidated learnings
            export_path: Optional path to save JSON export

        Returns:
            List of universal patterns
        """
        if not WEB4_AVAILABLE:
            raise RuntimeError("Web4 coordination learning not available")

        universal_patterns = []

        # Convert coordination patterns
        for i, pattern in enumerate(learnings.patterns):
            universal = self.convert_coordination_pattern(
                pattern,
                pattern_id=f"web4_pattern_{i}_{int(time.time())}"
            )
            universal_patterns.append(universal)

        # Convert success factors
        for i, factor in enumerate(learnings.success_factors):
            universal = self.convert_success_factor(
                factor,
                pattern_id=f"web4_factor_{i}_{int(time.time())}"
            )
            universal_patterns.append(universal)

        # Save to file if path provided
        if export_path:
            export_data = {
                'export_timestamp': time.time(),
                'source_domain': 'coordination',
                'num_patterns': len(universal_patterns),
                'patterns': [p.to_dict() for p in universal_patterns]
            }

            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            print(f"Exported {len(universal_patterns)} patterns to {export_path}")

        return universal_patterns


class UniversalToWeb4Converter:
    """
    Convert universal patterns to Web4 coordination patterns.

    Enables Web4 to import patterns from SAGE or other domains.
    """

    def __init__(self):
        # Get mappings for consciousness → coordination (SAGE → Web4)
        self.mappings = get_mappings(
            PatternDomain.CONSCIOUSNESS,
            PatternDomain.COORDINATION
        )

    def convert_to_coordination_pattern(
        self,
        universal: UniversalPattern
    ) -> Optional['CoordinationPattern']:
        """
        Convert UniversalPattern to Web4 CoordinationPattern.

        Args:
            universal: Universal pattern (from any domain)

        Returns:
            Web4 CoordinationPattern, or None if conversion not possible
        """
        if not WEB4_AVAILABLE:
            raise RuntimeError("Web4 coordination learning not available")

        # Map category to pattern type
        category_to_type = {
            PatternCategory.SUCCESS: PatternType.SUCCESS,
            PatternCategory.FAILURE: PatternType.FAILURE,
            PatternCategory.NETWORK: PatternType.NETWORK_TOPOLOGY,
            PatternCategory.EPISTEMIC: PatternType.EPISTEMIC_SHIFT,
            PatternCategory.EFFICIENCY: PatternType.RESOURCE_EFFICIENCY
        }

        pattern_type = category_to_type.get(universal.category, PatternType.SUCCESS)

        # Map characteristics from source domain to coordination domain
        coord_characteristics = {}

        for source_char, value in universal.characteristics.items():
            # Find mapping for this characteristic
            target_char = map_characteristic(
                source_char,
                universal.source_domain,
                PatternDomain.COORDINATION
            )

            if target_char:
                coord_characteristics[target_char] = value
            else:
                # No direct mapping - keep original if it's a coordination characteristic
                if source_char in ['network_density', 'trust_score', 'diversity_score',
                                  'coordination_confidence', 'parameter_stability']:
                    coord_characteristics[source_char] = value

        # Extract network density and trust ranges if available
        network_density_range = (
            coord_characteristics.get('network_density', 0.5) - 0.1,
            coord_characteristics.get('network_density', 0.5) + 0.1
        )

        trust_score_range = (
            coord_characteristics.get('trust_score', 0.5) - 0.1,
            coord_characteristics.get('trust_score', 0.5) + 0.1
        )

        # Calculate average quality from quality correlation
        average_quality = 0.5 + (universal.quality_correlation * 0.3)

        # Create coordination pattern
        coord_pattern = CoordinationPattern(
            pattern_type=pattern_type,
            description=f"Imported: {universal.description}",
            characteristics=coord_characteristics,
            frequency=universal.frequency,
            confidence=universal.confidence,
            examples=[],  # No examples from universal pattern
            average_quality=average_quality,
            quality_improvement=universal.quality_correlation * 0.2,
            network_density_range=network_density_range,
            trust_score_range=trust_score_range
        )

        return coord_pattern

    def import_patterns(
        self,
        import_path: Path
    ) -> List['CoordinationPattern']:
        """
        Import universal patterns from file and convert to Web4 format.

        Args:
            import_path: Path to JSON file with exported patterns

        Returns:
            List of Web4 coordination patterns
        """
        if not WEB4_AVAILABLE:
            raise RuntimeError("Web4 coordination learning not available")

        with open(import_path, 'r') as f:
            import_data = json.load(f)

        universal_patterns = [
            UniversalPattern.from_dict(p)
            for p in import_data['patterns']
        ]

        coord_patterns = []
        for universal in universal_patterns:
            coord = self.convert_to_coordination_pattern(universal)
            if coord:
                coord_patterns.append(coord)

        print(f"Imported {len(coord_patterns)} patterns from {import_path}")
        return coord_patterns


# Placeholder classes for SAGE conversion (to be implemented when SAGE is available)
class SAGEToUniversalConverter:
    """Convert SAGE consciousness patterns to universal format."""

    def convert_memory_pattern(
        self,
        pattern: 'MemoryPattern',
        pattern_id: Optional[str] = None
    ) -> UniversalPattern:
        """Convert SAGE MemoryPattern to UniversalPattern."""
        if not SAGE_AVAILABLE:
            raise RuntimeError("SAGE dream consolidation not available")

        # Implementation when SAGE is accessible
        # This would map SAGE's memory patterns to universal format
        raise NotImplementedError("SAGE converter to be implemented")

    def convert_quality_learning(
        self,
        learning: 'QualityLearning',
        pattern_id: Optional[str] = None
    ) -> UniversalPattern:
        """Convert SAGE QualityLearning to UniversalPattern."""
        if not SAGE_AVAILABLE:
            raise RuntimeError("SAGE dream consolidation not available")

        raise NotImplementedError("SAGE quality learning converter to be implemented")


class UniversalToSAGEConverter:
    """Convert universal patterns to SAGE consciousness patterns."""

    def convert_to_memory_pattern(
        self,
        universal: UniversalPattern
    ) -> Optional['MemoryPattern']:
        """Convert UniversalPattern to SAGE MemoryPattern."""
        if not SAGE_AVAILABLE:
            raise RuntimeError("SAGE dream consolidation not available")

        raise NotImplementedError("Universal to SAGE converter to be implemented")


if __name__ == "__main__":
    print("Pattern Exchange Protocol for Cross-Domain Learning")
    print("=" * 80)
    print()

    print("Available Converters:")
    print()

    if WEB4_AVAILABLE:
        print("✅ Web4 → Universal (export coordination patterns)")
        print("✅ Universal → Web4 (import patterns from other domains)")
    else:
        print("❌ Web4 converters not available (coordination learning not imported)")

    print()

    if SAGE_AVAILABLE:
        print("✅ SAGE → Universal (export consciousness patterns)")
        print("✅ Universal → SAGE (import patterns from other domains)")
    else:
        print("⚠️  SAGE converters defined but not yet implemented")

    print()
    print("Usage:")
    print()
    print("# Export Web4 patterns")
    print("converter = Web4ToUniversalConverter()")
    print("universal_patterns = converter.export_learnings(")
    print("    learnings=web4_learnings,")
    print("    export_path='web4_patterns.json'")
    print(")")
    print()
    print("# Import patterns into Web4")
    print("importer = UniversalToWeb4Converter()")
    print("coord_patterns = importer.import_patterns('sage_patterns.json')")
    print()
