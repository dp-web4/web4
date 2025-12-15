#!/usr/bin/env python3
"""
Web4 Session 53: Phase-Tagged Pattern Learning
==============================================

Extends Session 22's coordination learning with circadian phase awareness.
Enables extraction of temporal patterns that work better at specific times.

Research Provenance:
- Web4 S22: Coordination pattern learning (DREAM integration)
- Web4 S51: Phase 2c circadian integration
- Web4 S52: Implicit phase-specific learning validated
- Web4 S53: Explicit phase-tagged pattern extraction (this session)

Problem from Session 52:
"Implicit learning works (all 4 phase-specific patterns detected behaviorally),
but 0 explicit patterns extracted. Need phase-tagged extraction for portability."

Solution:
- Separate coordination history by circadian phase
- Extract patterns per phase
- Tag patterns with applicable phases
- Enable phase-aware pattern retrieval

Usage:
```python
# Initialize phase-aware learner
learner = PhaseTaggedLearner()

# After coordination cycles with circadian context
patterns = learner.extract_phase_patterns(coordination_history)

# Retrieve patterns for current phase
current_phase = CircadianPhase.DAY
relevant_patterns = patterns.get_patterns_for_phase(current_phase)
```

Created: December 15, 2025
Session: Autonomous Web4 Research Session 53
"""

import statistics
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from sage.core.circadian_clock import CircadianPhase
from web4_coordination_learning import (
    CoordinationPattern,
    PatternType,
    SuccessFactorLearning,
    NetworkInsight,
    ConsolidatedLearnings,
    CoordinationLearner
)


@dataclass
class PhaseTaggedPattern(CoordinationPattern):
    """
    Coordination pattern tagged with applicable circadian phases.

    Extends base CoordinationPattern with temporal awareness.
    """
    # Phases where this pattern applies
    applicable_phases: List[str] = field(default_factory=list)

    # Phase-specific quality scores
    phase_quality: Dict[str, float] = field(default_factory=dict)

    # Phase-specific confidence
    phase_confidence: Dict[str, float] = field(default_factory=dict)

    # Frequency by phase
    phase_frequency: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Export with phase information"""
        base = super().to_dict()
        base.update({
            'applicable_phases': self.applicable_phases,
            'phase_quality': self.phase_quality,
            'phase_confidence': self.phase_confidence,
            'phase_frequency': self.phase_frequency
        })
        return base

    def applies_to_phase(self, phase: str, min_confidence: float = 0.6) -> bool:
        """Check if pattern applies to given phase"""
        if phase in self.applicable_phases:
            return self.phase_confidence.get(phase, 0.0) >= min_confidence
        return False

    def get_phase_quality(self, phase: str) -> float:
        """Get quality score for specific phase"""
        return self.phase_quality.get(phase, self.average_quality)


@dataclass
class PhaseTaggedLearnings(ConsolidatedLearnings):
    """
    Extended learnings with phase-tagged patterns.

    Maintains backward compatibility with ConsolidatedLearnings.
    """
    # Phase-tagged patterns
    phase_patterns: List[PhaseTaggedPattern] = field(default_factory=list)

    # Patterns by phase for fast lookup
    _patterns_by_phase: Dict[str, List[PhaseTaggedPattern]] = field(default_factory=dict)

    def get_patterns_for_phase(
        self,
        phase: str,
        min_confidence: float = 0.6
    ) -> List[PhaseTaggedPattern]:
        """
        Get patterns applicable to specific circadian phase.

        Args:
            phase: CircadianPhase (day, night, dawn, dusk, deep_night)
            min_confidence: Minimum phase-specific confidence

        Returns:
            List of patterns that apply to this phase
        """
        # Build index if needed
        if not self._patterns_by_phase:
            self._build_phase_index()

        # Filter by confidence
        patterns = self._patterns_by_phase.get(phase, [])
        return [p for p in patterns if p.applies_to_phase(phase, min_confidence)]

    def _build_phase_index(self):
        """Build phase → patterns index for fast lookup"""
        self._patterns_by_phase = defaultdict(list)

        for pattern in self.phase_patterns:
            for phase in pattern.applicable_phases:
                self._patterns_by_phase[phase].append(pattern)

    def get_top_patterns_for_phase(
        self,
        phase: str,
        n: int = 5
    ) -> List[PhaseTaggedPattern]:
        """Get top N patterns for specific phase by confidence"""
        phase_patterns = self.get_patterns_for_phase(phase)

        sorted_patterns = sorted(
            phase_patterns,
            key=lambda p: p.phase_confidence.get(phase, 0.0),
            reverse=True
        )

        return sorted_patterns[:n]

    def to_dict(self) -> Dict:
        """Export with phase-tagged patterns"""
        base = super().to_dict()
        base['phase_patterns'] = [p.to_dict() for p in self.phase_patterns]
        return base


class PhaseTaggedLearner(CoordinationLearner):
    """
    Learns phase-specific coordination patterns.

    Extends CoordinationLearner with circadian phase awareness.
    Extracts patterns that work better during specific phases.
    """

    def __init__(
        self,
        min_pattern_frequency: int = 3,
        min_confidence: float = 0.6,  # Lower than base (0.7) for phase-specific patterns
        atp_budget: float = 80.0,
        min_phase_samples: int = 5  # Minimum samples per phase for extraction
    ):
        """
        Initialize phase-tagged learner.

        Args:
            min_pattern_frequency: Minimum occurrences for pattern
            min_confidence: Minimum confidence for extraction
            atp_budget: ATP budget for consolidation
            min_phase_samples: Minimum samples per phase
        """
        super().__init__(min_pattern_frequency, min_confidence, atp_budget)
        self.min_phase_samples = min_phase_samples

    def extract_phase_patterns(
        self,
        coordination_history: List[Dict]
    ) -> PhaseTaggedLearnings:
        """
        Extract phase-tagged patterns from coordination history.

        Process:
        1. Separate history by circadian phase
        2. Extract patterns per phase
        3. Identify cross-phase patterns
        4. Tag patterns with applicable phases

        Args:
            coordination_history: List of cycles with 'circadian_phase' field

        Returns:
            Phase-tagged learnings
        """
        if len(coordination_history) < self.min_frequency:
            return PhaseTaggedLearnings(
                cycles_analyzed=len(coordination_history)
            )

        # Separate history by phase
        phase_histories = self._separate_by_phase(coordination_history)

        # Extract base learnings (backward compatibility)
        base_learnings = super().extract_patterns(coordination_history)

        # Create phase-tagged learnings
        learnings = PhaseTaggedLearnings(
            patterns=base_learnings.patterns,
            success_factors=base_learnings.success_factors,
            network_insights=base_learnings.network_insights,
            quality_trajectory=base_learnings.quality_trajectory,
            confidence_trajectory=base_learnings.confidence_trajectory,
            cycles_analyzed=len(coordination_history),
            consolidation_timestamp=base_learnings.consolidation_timestamp
        )

        # Extract phase-specific patterns
        learnings.phase_patterns = self._extract_phase_tagged_patterns(
            phase_histories,
            coordination_history
        )

        return learnings

    def _separate_by_phase(
        self,
        history: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Separate coordination history by circadian phase.

        Args:
            history: Full coordination history

        Returns:
            Dict mapping phase → cycles in that phase
        """
        phase_histories = defaultdict(list)

        for cycle in history:
            phase = cycle.get('circadian_phase', 'unknown')

            # Normalize phase names
            if isinstance(phase, CircadianPhase):
                phase = phase.value

            # Convert CircadianPhase enum to string if needed
            phase_str = phase.lower() if isinstance(phase, str) else str(phase).lower()

            phase_histories[phase_str].append(cycle)

        return phase_histories

    def _extract_phase_tagged_patterns(
        self,
        phase_histories: Dict[str, List[Dict]],
        full_history: List[Dict]
    ) -> List[PhaseTaggedPattern]:
        """
        Extract patterns tagged with applicable phases.

        Strategy:
        1. Extract patterns per phase
        2. Compare patterns across phases
        3. Tag each pattern with phases where it works well

        Args:
            phase_histories: History separated by phase
            full_history: Complete history for comparison

        Returns:
            List of phase-tagged patterns
        """
        patterns = []

        # Group phases for analysis
        day_phases = ['day', 'dawn', 'dusk']
        night_phases = ['night', 'deep_night']

        # Extract DAY patterns
        day_history = []
        for phase in day_phases:
            day_history.extend(phase_histories.get(phase, []))

        if len(day_history) >= self.min_phase_samples:
            day_patterns = self._extract_patterns_for_phase_group(
                day_history,
                day_phases,
                "DAY"
            )
            patterns.extend(day_patterns)

        # Extract NIGHT patterns
        night_history = []
        for phase in night_phases:
            night_history.extend(phase_histories.get(phase, []))

        if len(night_history) >= self.min_phase_samples:
            night_patterns = self._extract_patterns_for_phase_group(
                night_history,
                night_phases,
                "NIGHT"
            )
            patterns.extend(night_patterns)

        # Extract phase-specific patterns (e.g., only during DAY, not NIGHT)
        patterns.extend(
            self._extract_phase_exclusive_patterns(phase_histories)
        )

        return patterns

    def _extract_patterns_for_phase_group(
        self,
        history: List[Dict],
        phases: List[str],
        group_name: str
    ) -> List[PhaseTaggedPattern]:
        """
        Extract patterns for a group of phases (e.g., DAY = dawn+day+dusk).

        Args:
            history: Cycles from this phase group
            phases: Phase names in this group
            group_name: Name for this group (DAY/NIGHT)

        Returns:
            Phase-tagged patterns
        """
        patterns = []

        # Success patterns for this phase group
        high_quality = [c for c in history if c.get('quality', 0) > 0.7]

        if len(high_quality) >= self.min_frequency:
            common_chars = self._find_common_characteristics(high_quality)

            if common_chars:
                # Calculate phase-specific metrics
                phase_quality = {}
                phase_confidence = {}
                phase_frequency = {}

                for phase in phases:
                    phase_cycles = [c for c in high_quality
                                   if c.get('circadian_phase', '').lower() == phase]
                    if phase_cycles:
                        phase_quality[phase] = statistics.mean(
                            c.get('quality', 0) for c in phase_cycles
                        )
                        phase_confidence[phase] = len(phase_cycles) / len(history)
                        phase_frequency[phase] = len(phase_cycles)

                pattern = PhaseTaggedPattern(
                    pattern_type=PatternType.SUCCESS,
                    description=f"{group_name} high-quality coordination pattern",
                    characteristics=common_chars,
                    frequency=len(high_quality),
                    confidence=len(high_quality) / len(history),
                    average_quality=statistics.mean(c.get('quality', 0)
                                                   for c in high_quality),
                    examples=high_quality[:5],
                    applicable_phases=phases,
                    phase_quality=phase_quality,
                    phase_confidence=phase_confidence,
                    phase_frequency=phase_frequency
                )
                patterns.append(pattern)

        return patterns

    def _extract_phase_exclusive_patterns(
        self,
        phase_histories: Dict[str, List[Dict]]
    ) -> List[PhaseTaggedPattern]:
        """
        Extract patterns that work well ONLY during specific phases.

        Identifies patterns that have significantly different outcomes
        in different phases.

        Args:
            phase_histories: History separated by phase

        Returns:
            Phase-exclusive patterns
        """
        patterns = []

        # Check each phase for exclusive success patterns
        for phase, history in phase_histories.items():
            if len(history) < self.min_phase_samples:
                continue

            # Find high-quality cycles in this phase
            high_quality = [c for c in history if c.get('quality', 0) > 0.75]

            if len(high_quality) < self.min_frequency:
                continue

            # Find common characteristics
            chars = self._find_common_characteristics(high_quality)

            if not chars:
                continue

            # Check if this pattern is phase-exclusive
            # (doesn't work as well in other phases)
            is_exclusive = self._is_pattern_phase_exclusive(
                chars,
                phase,
                phase_histories
            )

            if is_exclusive:
                pattern = PhaseTaggedPattern(
                    pattern_type=PatternType.SUCCESS,
                    description=f"Phase-exclusive pattern for {phase}",
                    characteristics=chars,
                    frequency=len(high_quality),
                    confidence=len(high_quality) / len(history),
                    average_quality=statistics.mean(
                        c.get('quality', 0) for c in high_quality
                    ),
                    examples=high_quality[:3],
                    applicable_phases=[phase],
                    phase_quality={phase: statistics.mean(
                        c.get('quality', 0) for c in high_quality
                    )},
                    phase_confidence={phase: len(high_quality) / len(history)},
                    phase_frequency={phase: len(high_quality)}
                )
                patterns.append(pattern)

        return patterns

    def _is_pattern_phase_exclusive(
        self,
        characteristics: Dict,
        target_phase: str,
        phase_histories: Dict[str, List[Dict]],
        quality_threshold: float = 0.15  # 15% quality difference
    ) -> bool:
        """
        Check if pattern works significantly better in target phase.

        Args:
            characteristics: Pattern characteristics to check
            target_phase: Phase where pattern works well
            phase_histories: All phase histories
            quality_threshold: Minimum quality difference for exclusivity

        Returns:
            True if pattern is phase-exclusive
        """
        # Calculate average quality in target phase
        target_history = phase_histories.get(target_phase, [])
        if not target_history:
            return False

        # Find matching cycles in target phase
        target_matches = self._find_matching_cycles(characteristics, target_history)
        if len(target_matches) < self.min_frequency:
            return False

        target_quality = statistics.mean(c.get('quality', 0) for c in target_matches)

        # Calculate average quality in other phases
        other_quality_scores = []

        for phase, history in phase_histories.items():
            if phase == target_phase:
                continue

            matches = self._find_matching_cycles(characteristics, history)
            if len(matches) >= self.min_frequency:
                other_quality = statistics.mean(c.get('quality', 0) for c in matches)
                other_quality_scores.append(other_quality)

        # Pattern is exclusive if significantly better in target phase
        if other_quality_scores:
            avg_other_quality = statistics.mean(other_quality_scores)
            return (target_quality - avg_other_quality) >= quality_threshold

        return True  # No other phases have enough samples

    def _find_matching_cycles(
        self,
        characteristics: Dict,
        history: List[Dict],
        tolerance: float = 0.15
    ) -> List[Dict]:
        """
        Find cycles that match pattern characteristics.

        Args:
            characteristics: Pattern characteristics
            history: Coordination history
            tolerance: Matching tolerance (15%)

        Returns:
            Cycles matching this pattern
        """
        matches = []

        for cycle in history:
            if self._cycle_matches_characteristics(cycle, characteristics, tolerance):
                matches.append(cycle)

        return matches

    def _cycle_matches_characteristics(
        self,
        cycle: Dict,
        characteristics: Dict,
        tolerance: float = 0.15
    ) -> bool:
        """Check if cycle matches pattern characteristics"""
        # Check network density
        if 'avg_network_density' in characteristics:
            target = characteristics['avg_network_density']
            actual = cycle.get('network_density', 0)
            if abs(actual - target) > tolerance:
                return False

        # Check trust score
        if 'avg_trust' in characteristics:
            target = characteristics['avg_trust']
            actual = cycle.get('avg_trust_score', cycle.get('trust_score', 0))
            if abs(actual - target) > tolerance:
                return False

        # Check diversity
        if 'avg_diversity' in characteristics:
            target = characteristics['avg_diversity']
            actual = cycle.get('diversity_score', 0)
            if abs(actual - target) > tolerance:
                return False

        return True

    def _find_common_characteristics(self, cycles: List[Dict]) -> Dict:
        """Find characteristics common to a set of cycles"""
        if not cycles:
            return {}

        common = {}

        # Network density
        densities = [c.get('network_density', 0) for c in cycles]
        if densities:
            common['avg_network_density'] = statistics.mean(densities)
            common['network_density_std'] = statistics.stdev(densities) if len(densities) > 1 else 0.0

        # Trust scores
        trusts = [c.get('avg_trust_score', c.get('trust_score', 0)) for c in cycles]
        if trusts:
            common['avg_trust'] = statistics.mean(trusts)
            common['trust_std'] = statistics.stdev(trusts) if len(trusts) > 1 else 0.0

        # Diversity scores
        diversities = [c.get('diversity_score', 0) for c in cycles]
        if diversities:
            common['avg_diversity'] = statistics.mean(diversities)
            common['diversity_std'] = statistics.stdev(diversities) if len(diversities) > 1 else 0.0

        # Priority levels
        priorities = [c.get('priority', 0) for c in cycles]
        if priorities:
            common['avg_priority'] = statistics.mean(priorities)

        return common


# Backward compatibility: allow importing from this module
__all__ = [
    'PhaseTaggedPattern',
    'PhaseTaggedLearnings',
    'PhaseTaggedLearner'
]
