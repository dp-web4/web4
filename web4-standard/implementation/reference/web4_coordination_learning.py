#!/usr/bin/env python3
"""
Web4 Session 22: Coordination Pattern Learning (DREAM Integration)
==================================================================

Applies SAGE S42 DREAM consolidation pattern to Web4 coordination:
Extract learnings from coordination cycles to improve future decisions.

Research Provenance:
- SAGE S42: DREAM state memory consolidation (648 LOC)
- Web4 S19-20: Epistemic coordination validation (67%)
- Web4 S21: Phase 2 runtime tracking design
- Web4 S22: Coordination pattern learning (this session)

SAGE DREAM Pattern Transfer:
- SAGE: Extract learnings from consciousness cycles
- Web4: Extract learnings from coordination cycles

Pattern Types Extracted:
1. **Success Patterns**: What makes coordination succeed
2. **Failure Patterns**: What causes coordination to fail
3. **Network Insights**: Topology and trust evolution
4. **Epistemic Evolution**: How coordination quality changes over time
5. **Resource Patterns**: ATP allocation effectiveness

Design Philosophy:
- Learn from experience (not just static rules)
- Continuous improvement (adapt to changing networks)
- Pattern extraction (generalize beyond specific cases)
- Confidence tracking (know what we know)

Usage:
```python
# Initialize learner
learner = CoordinationLearner(
    min_pattern_frequency=3,
    min_confidence=0.7
)

# After coordination cycles
patterns = learner.extract_patterns(coordination_history)

# Apply learnings to future decisions
should_coordinate = learner.recommend(interaction, context, patterns)
```

Created: December 13, 2025
"""

import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import defaultdict


class PatternType(Enum):
    """Types of coordination patterns"""
    SUCCESS = "success"          # Patterns that lead to good outcomes
    FAILURE = "failure"          # Patterns that lead to poor outcomes
    NETWORK_TOPOLOGY = "network_topology"  # Network structure insights
    TRUST_EVOLUTION = "trust_evolution"    # How trust changes
    EPISTEMIC_SHIFT = "epistemic_shift"    # Coordination quality evolution
    RESOURCE_EFFICIENCY = "resource_efficiency"  # ATP allocation patterns


@dataclass
class CoordinationPattern:
    """
    Extracted coordination pattern.

    Similar to SAGE S42 MemoryPattern but for coordination domain.
    """
    pattern_type: PatternType
    description: str

    # Pattern characteristics
    characteristics: Dict[str, any] = field(default_factory=dict)

    # Evidence
    frequency: int = 0
    confidence: float = 0.0
    examples: List[Dict] = field(default_factory=list)

    # Impact
    average_quality: float = 0.0
    quality_improvement: float = 0.0

    # Context
    network_density_range: Tuple[float, float] = (0.0, 1.0)
    trust_score_range: Tuple[float, float] = (0.0, 1.0)

    def to_dict(self) -> Dict:
        """Export pattern for storage/analysis"""
        return {
            'type': self.pattern_type.value,
            'description': self.description,
            'characteristics': self.characteristics,
            'frequency': self.frequency,
            'confidence': self.confidence,
            'average_quality': self.average_quality,
            'quality_improvement': self.quality_improvement,
            'network_density_range': self.network_density_range,
            'trust_score_range': self.trust_score_range,
            'example_count': len(self.examples)
        }


@dataclass
class SuccessFactorLearning:
    """
    Learning about what factors improve coordination success.

    Similar to SAGE S42 QualityLearning but for coordination domain.
    """
    factor_name: str
    factor_description: str

    # Statistical evidence
    success_with_factor: float  # Success rate when factor present
    success_without_factor: float  # Success rate when factor absent

    # Strength and confidence
    correlation: float  # Positive = helps, negative = hurts
    confidence: float  # How confident we are in this learning
    sample_size: int  # Number of cycles observed

    # Actionable insight
    recommendation: str

    def to_dict(self) -> Dict:
        """Export for storage"""
        return {
            'factor': self.factor_name,
            'description': self.factor_description,
            'success_with': self.success_with_factor,
            'success_without': self.success_without_factor,
            'correlation': self.correlation,
            'confidence': self.confidence,
            'sample_size': self.sample_size,
            'recommendation': self.recommendation
        }


@dataclass
class NetworkInsight:
    """
    Insight about network topology and trust dynamics.

    Captures emergent patterns in distributed coordination.
    """
    insight_type: str  # "density_threshold", "trust_cascade", "partition_risk"
    description: str

    # Network characteristics when insight applies
    min_network_density: float
    typical_trust_distribution: Dict[str, float]  # {"low": 0.2, "medium": 0.5, "high": 0.3}

    # Evidence
    observed_frequency: int
    confidence: float

    # Impact
    impact_on_coordination: str  # Description of how this affects coordination
    recommended_action: str

    def to_dict(self) -> Dict:
        """Export insight"""
        return {
            'type': self.insight_type,
            'description': self.description,
            'min_network_density': self.min_network_density,
            'trust_distribution': self.typical_trust_distribution,
            'frequency': self.observed_frequency,
            'confidence': self.confidence,
            'impact': self.impact_on_coordination,
            'action': self.recommended_action
        }


@dataclass
class ConsolidatedLearnings:
    """
    Complete learning consolidation from coordination cycles.

    Output of DREAM-style pattern extraction.
    """
    # Extracted patterns
    patterns: List[CoordinationPattern] = field(default_factory=list)

    # Success factors
    success_factors: List[SuccessFactorLearning] = field(default_factory=list)

    # Network insights
    network_insights: List[NetworkInsight] = field(default_factory=list)

    # Epistemic evolution
    quality_trajectory: str = ""  # "improving", "declining", "stable"
    confidence_trajectory: str = ""

    # Metadata
    cycles_analyzed: int = 0
    consolidation_timestamp: float = 0.0

    def get_top_patterns(self, n: int = 5) -> List[CoordinationPattern]:
        """Get top N patterns by confidence"""
        sorted_patterns = sorted(self.patterns,
                                key=lambda p: p.confidence,
                                reverse=True)
        return sorted_patterns[:n]

    def get_actionable_factors(self, min_confidence: float = 0.7) -> List[SuccessFactorLearning]:
        """Get high-confidence success factors"""
        return [f for f in self.success_factors
                if f.confidence >= min_confidence]

    def to_dict(self) -> Dict:
        """Export all learnings"""
        return {
            'patterns': [p.to_dict() for p in self.patterns],
            'success_factors': [f.to_dict() for f in self.success_factors],
            'network_insights': [i.to_dict() for i in self.network_insights],
            'quality_trajectory': self.quality_trajectory,
            'confidence_trajectory': self.confidence_trajectory,
            'cycles_analyzed': self.cycles_analyzed,
            'timestamp': self.consolidation_timestamp
        }


class CoordinationLearner:
    """
    Learns coordination patterns from experience.

    Applies SAGE S42 DREAM consolidation pattern to Web4 coordination cycles.

    Process (similar to DREAM 4-stage processing):
    1. Pattern Extraction: Identify recurring patterns
    2. Success Factor Analysis: What improves coordination
    3. Network Insight Discovery: Topology and trust dynamics
    4. Epistemic Evolution: How quality changes over time
    """

    def __init__(
        self,
        min_pattern_frequency: int = 3,
        min_confidence: float = 0.7,
        atp_budget: float = 80.0  # DREAM state ATP (from SAGE S40)
    ):
        """
        Initialize coordination learner.

        Args:
            min_pattern_frequency: Minimum occurrences to consider a pattern
            min_confidence: Minimum confidence to include a learning
            atp_budget: ATP budget for consolidation (DREAM state allocation)
        """
        self.min_frequency = min_pattern_frequency
        self.min_confidence = min_confidence
        self.atp_budget = atp_budget

    def extract_patterns(
        self,
        coordination_history: List[Dict]
    ) -> ConsolidatedLearnings:
        """
        Extract learnings from coordination history.

        Args:
            coordination_history: List of coordination cycles with outcomes

        Returns:
            Consolidated learnings
        """
        if len(coordination_history) < self.min_frequency:
            return ConsolidatedLearnings(
                cycles_analyzed=len(coordination_history)
            )

        learnings = ConsolidatedLearnings(
            cycles_analyzed=len(coordination_history)
        )

        # Stage 1: Pattern Extraction (30% ATP)
        learnings.patterns = self._extract_coordination_patterns(coordination_history)

        # Stage 2: Success Factor Analysis (30% ATP)
        learnings.success_factors = self._analyze_success_factors(coordination_history)

        # Stage 3: Network Insight Discovery (20% ATP)
        learnings.network_insights = self._discover_network_insights(coordination_history)

        # Stage 4: Epistemic Evolution (20% ATP)
        learnings.quality_trajectory, learnings.confidence_trajectory = \
            self._analyze_epistemic_evolution(coordination_history)

        return learnings

    def _extract_coordination_patterns(
        self,
        history: List[Dict]
    ) -> List[CoordinationPattern]:
        """
        Extract recurring coordination patterns.

        Following SAGE S42 pattern extraction approach.
        """
        patterns = []

        # Success patterns: High quality outcomes
        high_quality_cycles = [c for c in history
                              if c.get('quality', 0) > 0.7]

        if len(high_quality_cycles) >= self.min_frequency:
            # Analyze what these successful cycles have in common
            common_chars = self._find_common_characteristics(high_quality_cycles)

            if common_chars:
                pattern = CoordinationPattern(
                    pattern_type=PatternType.SUCCESS,
                    description="High-quality coordination pattern",
                    characteristics=common_chars,
                    frequency=len(high_quality_cycles),
                    confidence=len(high_quality_cycles) / len(history),
                    average_quality=statistics.mean(c.get('quality', 0)
                                                   for c in high_quality_cycles),
                    examples=high_quality_cycles[:5]
                )
                patterns.append(pattern)

        # Failure patterns: Low quality outcomes
        low_quality_cycles = [c for c in history
                             if c.get('quality', 0) < 0.4]

        if len(low_quality_cycles) >= self.min_frequency:
            common_chars = self._find_common_characteristics(low_quality_cycles)

            if common_chars:
                pattern = CoordinationPattern(
                    pattern_type=PatternType.FAILURE,
                    description="Low-quality coordination pattern",
                    characteristics=common_chars,
                    frequency=len(low_quality_cycles),
                    confidence=len(low_quality_cycles) / len(history),
                    average_quality=statistics.mean(c.get('quality', 0)
                                                   for c in low_quality_cycles),
                    examples=low_quality_cycles[:5]
                )
                patterns.append(pattern)

        return patterns

    def _find_common_characteristics(self, cycles: List[Dict]) -> Dict:
        """Find characteristics common to a set of cycles"""
        if not cycles:
            return {}

        common = {}

        # Network density
        densities = [c.get('network_density', 0) for c in cycles]
        if densities:
            common['avg_network_density'] = statistics.mean(densities)
            common['network_density_range'] = (min(densities), max(densities))

        # Trust scores
        trusts = [c.get('trust_score', 0) for c in cycles]
        if trusts:
            common['avg_trust'] = statistics.mean(trusts)
            common['trust_range'] = (min(trusts), max(trusts))

        # Priority levels
        priorities = [c.get('priority', 0) for c in cycles]
        if priorities:
            common['avg_priority'] = statistics.mean(priorities)

        return common

    def _analyze_success_factors(
        self,
        history: List[Dict]
    ) -> List[SuccessFactorLearning]:
        """
        Analyze what factors improve coordination success.

        Similar to SAGE S42 QualityLearning analysis.
        """
        factors = []

        # Factor: High network density
        high_density = [c for c in history if c.get('network_density', 0) > 0.5]
        low_density = [c for c in history if c.get('network_density', 0) <= 0.5]

        if len(high_density) >= self.min_frequency and len(low_density) >= self.min_frequency:
            success_with = statistics.mean(c.get('quality', 0) for c in high_density)
            success_without = statistics.mean(c.get('quality', 0) for c in low_density)
            correlation = success_with - success_without

            if abs(correlation) > 0.1:  # Meaningful difference
                factor = SuccessFactorLearning(
                    factor_name="high_network_density",
                    factor_description="Network density > 0.5",
                    success_with_factor=success_with,
                    success_without_factor=success_without,
                    correlation=correlation,
                    confidence=min(len(high_density), len(low_density)) / len(history),
                    sample_size=len(history),
                    recommendation=f"{'Favor' if correlation > 0 else 'Avoid'} high-density networks"
                )
                factors.append(factor)

        # Factor: High trust
        high_trust = [c for c in history if c.get('trust_score', 0) > 0.7]
        low_trust = [c for c in history if c.get('trust_score', 0) <= 0.7]

        if len(high_trust) >= self.min_frequency and len(low_trust) >= self.min_frequency:
            success_with = statistics.mean(c.get('quality', 0) for c in high_trust)
            success_without = statistics.mean(c.get('quality', 0) for c in low_trust)
            correlation = success_with - success_without

            if abs(correlation) > 0.1:
                factor = SuccessFactorLearning(
                    factor_name="high_trust",
                    factor_description="Trust score > 0.7",
                    success_with_factor=success_with,
                    success_without_factor=success_without,
                    correlation=correlation,
                    confidence=min(len(high_trust), len(low_trust)) / len(history),
                    sample_size=len(history),
                    recommendation=f"{'Prioritize' if correlation > 0 else 'Caution with'} high-trust interactions"
                )
                factors.append(factor)

        return factors

    def _discover_network_insights(
        self,
        history: List[Dict]
    ) -> List[NetworkInsight]:
        """
        Discover insights about network topology and trust dynamics.
        """
        insights = []

        # Insight: Density threshold
        densities = [c.get('network_density', 0) for c in history]
        qualities = [c.get('quality', 0) for c in history]

        if len(densities) >= self.min_frequency:
            # Find if there's a density threshold effect
            sorted_pairs = sorted(zip(densities, qualities))

            # Simple threshold detection: quality improves above certain density
            mid_point = len(sorted_pairs) // 2
            low_half_quality = statistics.mean(q for _, q in sorted_pairs[:mid_point])
            high_half_quality = statistics.mean(q for _, q in sorted_pairs[mid_point:])

            if high_half_quality - low_half_quality > 0.15:
                threshold_density = sorted_pairs[mid_point][0]

                insight = NetworkInsight(
                    insight_type="density_threshold",
                    description=f"Quality improves significantly above density {threshold_density:.2f}",
                    min_network_density=threshold_density,
                    typical_trust_distribution={"analysis": "pending"},
                    observed_frequency=len(history),
                    confidence=0.7,
                    impact_on_coordination="Network density has threshold effect on quality",
                    recommended_action=f"Target network density above {threshold_density:.2f}"
                )
                insights.append(insight)

        return insights

    def _analyze_epistemic_evolution(
        self,
        history: List[Dict]
    ) -> Tuple[str, str]:
        """
        Analyze how coordination quality and confidence evolve over time.
        """
        if len(history) < 10:
            return "insufficient_data", "insufficient_data"

        # Split history into first half and second half
        mid = len(history) // 2
        first_half = history[:mid]
        second_half = history[mid:]

        # Quality trajectory
        first_quality = statistics.mean(c.get('quality', 0) for c in first_half)
        second_quality = statistics.mean(c.get('quality', 0) for c in second_half)

        if second_quality > first_quality + 0.1:
            quality_trajectory = "improving"
        elif second_quality < first_quality - 0.1:
            quality_trajectory = "declining"
        else:
            quality_trajectory = "stable"

        # Confidence trajectory (if available)
        # Try both 'confidence' and 'coordination_confidence' fields
        first_conf_values = [c.get('confidence', c.get('coordination_confidence', 0))
                            for c in first_half
                            if 'confidence' in c or 'coordination_confidence' in c]
        second_conf_values = [c.get('confidence', c.get('coordination_confidence', 0))
                             for c in second_half
                             if 'confidence' in c or 'coordination_confidence' in c]

        if first_conf_values and second_conf_values:
            first_conf = statistics.mean(first_conf_values)
            second_conf = statistics.mean(second_conf_values)
            if second_conf > first_conf + 0.1:
                confidence_trajectory = "improving"
            elif second_conf < first_conf - 0.1:
                confidence_trajectory = "declining"
            else:
                confidence_trajectory = "stable"
        else:
            confidence_trajectory = "unknown"

        return quality_trajectory, confidence_trajectory

    def recommend(
        self,
        interaction: Dict,
        context: Dict,
        learnings: ConsolidatedLearnings
    ) -> Tuple[bool, float, str]:
        """
        Recommend coordination decision based on learned patterns.

        Args:
            interaction: Proposed interaction
            context: Network context
            learnings: Previously extracted learnings

        Returns:
            (should_coordinate, confidence, reasoning)
        """
        # Start with neutral
        score = 0.5
        reasons = []

        # Apply success factors
        for factor in learnings.get_actionable_factors():
            if factor.factor_name == "high_network_density":
                if context.get('network_density', 0) > 0.5:
                    score += factor.correlation * factor.confidence
                    reasons.append(f"+{factor.correlation:.2f} (high density)")

            elif factor.factor_name == "high_trust":
                if interaction.get('trust_score', 0) > 0.7:
                    score += factor.correlation * factor.confidence
                    reasons.append(f"+{factor.correlation:.2f} (high trust)")

        # Apply pattern matching
        for pattern in learnings.get_top_patterns(3):
            if pattern.pattern_type == PatternType.SUCCESS:
                # Check if current interaction matches success pattern
                match_score = self._pattern_match_score(interaction, context, pattern)
                if match_score > 0.7:
                    score += 0.2 * pattern.confidence
                    reasons.append(f"+0.2 (matches success pattern)")

            elif pattern.pattern_type == PatternType.FAILURE:
                # Check if current interaction matches failure pattern
                match_score = self._pattern_match_score(interaction, context, pattern)
                if match_score > 0.7:
                    score -= 0.2 * pattern.confidence
                    reasons.append(f"-0.2 (matches failure pattern)")

        # Decision
        should_coordinate = score > 0.5
        confidence = abs(score - 0.5) * 2  # Map to 0-1
        reasoning = " | ".join(reasons) if reasons else "No patterns matched"

        return should_coordinate, confidence, reasoning

    def _pattern_match_score(
        self,
        interaction: Dict,
        context: Dict,
        pattern: CoordinationPattern
    ) -> float:
        """
        Calculate how well interaction matches a pattern.

        Returns:
            Match score (0-1)
        """
        scores = []
        chars = pattern.characteristics

        # Network density match
        if 'network_density_range' in chars:
            density = context.get('network_density', 0)
            min_d, max_d = chars['network_density_range']
            if min_d <= density <= max_d:
                scores.append(1.0)
            else:
                # How far outside range?
                distance = min(abs(density - min_d), abs(density - max_d))
                scores.append(max(0, 1 - distance))

        # Trust match
        if 'trust_range' in chars:
            trust = interaction.get('trust_score', 0)
            min_t, max_t = chars['trust_range']
            if min_t <= trust <= max_t:
                scores.append(1.0)
            else:
                distance = min(abs(trust - min_t), abs(trust - max_t))
                scores.append(max(0, 1 - distance))

        return statistics.mean(scores) if scores else 0.0


# Example usage
if __name__ == "__main__":
    print("Web4 Session 22: Coordination Pattern Learning")
    print("=" * 80)
    print()
    print("SAGE S42 DREAM consolidation pattern applied to Web4 coordination")
    print()
    print("Capabilities:")
    print("- Extract success/failure patterns from coordination history")
    print("- Learn what factors improve coordination quality")
    print("- Discover network topology insights")
    print("- Track epistemic evolution over time")
    print("- Recommend decisions based on learned patterns")
    print()
    print("Usage:")
    print("  learner = CoordinationLearner()")
    print("  learnings = learner.extract_patterns(coordination_history)")
    print("  should_coord, conf, reason = learner.recommend(interaction, context, learnings)")
    print()
