#!/usr/bin/env python3
"""
Temporal Pattern Exchange Protocol
==================================

Extends pattern exchange protocol with circadian/temporal awareness.
Enables transfer of phase-tagged patterns between domains.

Research Provenance:
- Web4 S22: Pattern exchange protocol
- Web4 S51: Circadian integration (Phase 2c)
- Web4 S53: Phase-tagged pattern extraction
- Web4 S54: Temporal pattern transfer (this)

Created: December 15, 2025
Session: Autonomous Web4 Research Session 54
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field

from pattern_exchange_protocol import (
    Web4ToUniversalConverter,
    UniversalToWeb4Converter
)
from universal_pattern_schema import UniversalPattern, PatternDomain, PatternCategory
from web4_phase_tagged_learning import PhaseTaggedPattern, PhaseTaggedLearnings


@dataclass
class TemporalUniversalPattern(UniversalPattern):
    """
    Extended universal pattern with temporal/circadian awareness.

    Adds phase-specific information to enable cross-domain transfer
    of temporally-aware patterns.
    """
    # Temporal applicability
    temporal_applicability: Dict[str, float] = field(default_factory=dict)
    # {phase → confidence that pattern applies in this phase}
    # e.g., {'day': 0.85, 'night': 0.12}

    # Phase-specific quality
    phase_quality: Dict[str, float] = field(default_factory=dict)
    # {phase → quality when pattern used in this phase}

    # Phase-specific frequency
    phase_frequency: Dict[str, int] = field(default_factory=dict)
    # {phase → how often observed in this phase}

    # Circadian period (if applicable)
    circadian_period: Optional[int] = None


class TemporalWeb4ToUniversalConverter(Web4ToUniversalConverter):
    """
    Convert phase-tagged Web4 patterns to temporal universal format.

    Extends base converter with circadian phase awareness.
    """

    def convert_phase_tagged_pattern(
        self,
        pattern: PhaseTaggedPattern,
        pattern_id: Optional[str] = None,
        circadian_period: int = 100
    ) -> TemporalUniversalPattern:
        """
        Convert PhaseTaggedPattern to TemporalUniversalPattern.

        Args:
            pattern: Phase-tagged coordination pattern
            pattern_id: Optional unique identifier
            circadian_period: Circadian cycle period

        Returns:
            TemporalUniversalPattern with phase information
        """
        # Convert base pattern using parent converter
        # Note: parent expects CoordinationPattern, PhaseTaggedPattern inherits from it
        base_universal = self.convert_coordination_pattern(pattern, pattern_id)

        # Add temporal dimensions
        temporal_applicability = {}
        for phase in pattern.applicable_phases:
            # Use phase_confidence if available
            confidence = pattern.phase_confidence.get(phase, pattern.confidence)
            temporal_applicability[phase] = confidence

        # Create temporal universal pattern
        temporal_pattern = TemporalUniversalPattern(
            # Base fields from UniversalPattern
            pattern_id=base_universal.pattern_id,
            source_domain=base_universal.source_domain,
            category=base_universal.category,
            description=base_universal.description,
            characteristics=base_universal.characteristics,
            frequency=base_universal.frequency,
            confidence=base_universal.confidence,
            sample_size=base_universal.sample_size,
            quality_correlation=base_universal.quality_correlation,
            extraction_timestamp=base_universal.extraction_timestamp,
            first_observed=base_universal.first_observed,
            last_observed=base_universal.last_observed,
            source_metadata=base_universal.source_metadata,
            # Temporal fields
            temporal_applicability=temporal_applicability,
            phase_quality=pattern.phase_quality.copy(),
            phase_frequency=pattern.phase_frequency.copy(),
            circadian_period=circadian_period
        )

        return temporal_pattern

    def export_phase_tagged_learnings(
        self,
        learnings: PhaseTaggedLearnings,
        circadian_period: int = 100
    ) -> List[TemporalUniversalPattern]:
        """
        Export all phase-tagged patterns to temporal universal format.

        Args:
            learnings: Phase-tagged learnings to export
            circadian_period: Circadian cycle period

        Returns:
            List of temporal universal patterns
        """
        temporal_patterns = []

        for i, pattern in enumerate(learnings.phase_patterns):
            pattern_id = f"web4_phase_tagged_{i}"
            temporal_pattern = self.convert_phase_tagged_pattern(
                pattern,
                pattern_id,
                circadian_period
            )
            temporal_patterns.append(temporal_pattern)

        return temporal_patterns


class TemporalUniversalToWeb4Converter(UniversalToWeb4Converter):
    """
    Convert temporal universal patterns back to Web4 phase-tagged patterns.

    Enables import of temporally-aware patterns from other domains.
    """

    def convert_to_phase_tagged_pattern(
        self,
        temporal: TemporalUniversalPattern
    ) -> PhaseTaggedPattern:
        """
        Convert TemporalUniversalPattern to PhaseTaggedPattern.

        Args:
            temporal: Temporal universal pattern

        Returns:
            Web4 phase-tagged coordination pattern
        """
        # Convert to base coordination pattern first
        base_pattern = self.convert_to_coordination_pattern(temporal)

        # Extract temporal dimensions
        applicable_phases = list(temporal.temporal_applicability.keys())

        # Create phase-tagged pattern
        phase_pattern = PhaseTaggedPattern(
            # Base fields from CoordinationPattern
            pattern_type=base_pattern.pattern_type,
            description=temporal.description,
            characteristics=base_pattern.characteristics,
            frequency=base_pattern.frequency,
            confidence=base_pattern.confidence,
            average_quality=base_pattern.average_quality,
            quality_improvement=base_pattern.quality_improvement,
            network_density_range=base_pattern.network_density_range,
            trust_score_range=base_pattern.trust_score_range,
            examples=base_pattern.examples,
            # Temporal fields
            applicable_phases=applicable_phases,
            phase_quality=temporal.phase_quality.copy(),
            phase_confidence=temporal.temporal_applicability.copy(),
            phase_frequency=temporal.phase_frequency.copy()
        )

        return phase_pattern

    def import_temporal_patterns(
        self,
        temporal_patterns: List[TemporalUniversalPattern]
    ) -> PhaseTaggedLearnings:
        """
        Import temporal universal patterns as Web4 phase-tagged learnings.

        Args:
            temporal_patterns: List of temporal universal patterns

        Returns:
            PhaseTaggedLearnings with imported patterns
        """
        phase_patterns = []

        for temporal in temporal_patterns:
            phase_pattern = self.convert_to_phase_tagged_pattern(temporal)
            phase_patterns.append(phase_pattern)

        # Create phase-tagged learnings
        learnings = PhaseTaggedLearnings(
            phase_patterns=phase_patterns,
            cycles_analyzed=sum(p.frequency for p in phase_patterns)
        )

        return learnings


def export_phase_tagged_patterns_to_file(
    learnings: PhaseTaggedLearnings,
    output_path: Path,
    circadian_period: int = 100
):
    """
    Export phase-tagged learnings to JSON file.

    Args:
        learnings: Phase-tagged learnings to export
        output_path: Where to save JSON
        circadian_period: Circadian cycle period
    """
    converter = TemporalWeb4ToUniversalConverter()
    temporal_patterns = converter.export_phase_tagged_learnings(
        learnings,
        circadian_period
    )

    # Convert to dict for JSON serialization
    patterns_dict = []
    for p in temporal_patterns:
        p_dict = asdict(p)
        # Convert enums to strings for JSON serialization
        p_dict['source_domain'] = p.source_domain.value
        p_dict['category'] = p.category.value
        patterns_dict.append(p_dict)

    with open(output_path, 'w') as f:
        json.dump({
            'patterns': patterns_dict,
            'circadian_period': circadian_period,
            'export_timestamp': temporal_patterns[0].extraction_timestamp if temporal_patterns else 0,
            'pattern_count': len(temporal_patterns)
        }, f, indent=2)


def import_phase_tagged_patterns_from_file(
    input_path: Path
) -> PhaseTaggedLearnings:
    """
    Import phase-tagged patterns from JSON file.

    Args:
        input_path: JSON file to load

    Returns:
        PhaseTaggedLearnings with imported patterns
    """
    with open(input_path, 'r') as f:
        data = json.load(f)

    # Reconstruct TemporalUniversalPattern objects
    temporal_patterns = []
    for p_dict in data['patterns']:
        # Handle enum conversions
        source_domain = PatternDomain(p_dict['source_domain'])
        category = PatternCategory(p_dict['category'])

        temporal = TemporalUniversalPattern(
            pattern_id=p_dict['pattern_id'],
            source_domain=source_domain,
            category=category,
            description=p_dict['description'],
            characteristics=p_dict['characteristics'],
            frequency=p_dict['frequency'],
            confidence=p_dict['confidence'],
            sample_size=p_dict['sample_size'],
            quality_correlation=p_dict['quality_correlation'],
            extraction_timestamp=p_dict['extraction_timestamp'],
            first_observed=p_dict['first_observed'],
            last_observed=p_dict['last_observed'],
            source_metadata=p_dict['source_metadata'],
            temporal_applicability=p_dict.get('temporal_applicability', {}),
            phase_quality=p_dict.get('phase_quality', {}),
            phase_frequency=p_dict.get('phase_frequency', {}),
            circadian_period=p_dict.get('circadian_period')
        )
        temporal_patterns.append(temporal)

    # Convert to phase-tagged learnings
    converter = TemporalUniversalToWeb4Converter()
    learnings = converter.import_temporal_patterns(temporal_patterns)

    return learnings


__all__ = [
    'TemporalUniversalPattern',
    'TemporalWeb4ToUniversalConverter',
    'TemporalUniversalToWeb4Converter',
    'export_phase_tagged_patterns_to_file',
    'import_phase_tagged_patterns_from_file'
]
