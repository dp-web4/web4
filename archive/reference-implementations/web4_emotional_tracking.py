#!/usr/bin/env python3
"""
Web4 Session 53: Emotional Coordination Tracking
================================================

Implements emotional-like metrics for coordination based on SAGE Session 48
emotional intelligence framework.

Research Provenance:
- SAGE S48: Emotional intelligence (4D consciousness)
- Web4 S52: Emotional intelligence mapping design
- Web4 S53: Phase 1 implementation (metric computation)

SAGE Emotional Dimensions → Web4 Coordination Metrics:
1. Curiosity → Network diversity exploration
2. Frustration → Coordination quality stagnation
3. Progress → Quality improvement trend
4. Engagement → Priority/salience focus

Usage:
```python
# Initialize tracker
tracker = EmotionalCoordinationTracker()

# Each coordination cycle
emotions = tracker.update({
    'network_density': 0.8,
    'diversity_score': 0.7,
    'quality': 0.85,
    'priority': 0.9
})

# Use emotions for logging, analysis, or modulation
if emotions.frustration > 0.7:
    print("High frustration detected - consider consolidation")
```

Created: December 15, 2025
Session: Autonomous Web4 Research Session 53
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque


@dataclass
class EmotionalCoordinationMetrics:
    """
    Emotional-like metrics for coordination.

    Inspired by SAGE S48 emotional intelligence framework,
    adapted for Web4 coordination context.
    """
    curiosity: float = 0.5          # Network diversity exploration [0-1]
    frustration: float = 0.0        # Coordination quality stagnation [0-1]
    progress: float = 0.5           # Quality improvement trend [0-1]
    engagement: float = 0.5         # Priority/salience focus [0-1]

    # Metadata
    cycle_count: int = 0
    timestamp: float = 0.0

    def to_dict(self) -> Dict:
        """Export metrics as dict"""
        return {
            'curiosity': self.curiosity,
            'frustration': self.frustration,
            'progress': self.progress,
            'engagement': self.engagement,
            'cycle_count': self.cycle_count,
            'timestamp': self.timestamp
        }

    def __str__(self) -> str:
        """Human-readable representation"""
        return (f"Curiosity: {self.curiosity:.2f}, "
                f"Frustration: {self.frustration:.2f}, "
                f"Progress: {self.progress:.2f}, "
                f"Engagement: {self.engagement:.2f}")


class EmotionalCoordinationTracker:
    """
    Track emotional-like states during coordination.

    Computes SAGE-inspired emotional metrics from coordination cycle data
    without requiring full integration into coordinator.

    Phase 1 (this implementation): Metric computation only
    Phase 2: Correlation validation
    Phase 3: Decision modulation
    Phase 4: Cross-domain transfer
    """

    def __init__(self, history_length: int = 20):
        """
        Initialize emotional coordination tracker.

        Args:
            history_length: How many cycles to track for metric computation
        """
        self.history_length = history_length

        # State histories
        self.network_density_history = deque(maxlen=history_length)
        self.diversity_history = deque(maxlen=history_length)
        self.quality_history = deque(maxlen=history_length)
        self.priority_history = deque(maxlen=history_length)
        self.partner_history = deque(maxlen=history_length)

        # Current emotional state
        self.current_emotions = EmotionalCoordinationMetrics()

        # Cycle count
        self.cycle_count = 0

    def update(self, cycle_data: Dict) -> EmotionalCoordinationMetrics:
        """
        Update emotional state from coordination cycle.

        Args:
            cycle_data: Dict with keys:
                - 'network_density': float [0-1]
                - 'diversity_score': float [0-1]
                - 'quality': float [0-1]
                - 'priority': float [0-1]
                - 'partner': str (optional, for partner tracking)

        Returns:
            EmotionalCoordinationMetrics with current emotional state
        """
        self.cycle_count += 1

        # Store histories
        self.network_density_history.append(
            cycle_data.get('network_density', 0.5)
        )
        self.diversity_history.append(
            cycle_data.get('diversity_score', 0.5)
        )

        # Normalize quality to [0-1] if needed
        quality = cycle_data.get('quality', 0.5)
        if quality > 1.0:
            quality = quality / 4.0  # Assume 0-4 scale
        self.quality_history.append(quality)

        self.priority_history.append(
            cycle_data.get('priority', 0.5)
        )

        if 'partner' in cycle_data:
            self.partner_history.append(cycle_data['partner'])

        # Compute emotional scores
        curiosity = self._compute_curiosity()
        frustration = self._compute_frustration()
        progress = self._compute_progress()
        engagement = self._compute_engagement()

        # Update current state
        self.current_emotions = EmotionalCoordinationMetrics(
            curiosity=curiosity,
            frustration=frustration,
            progress=progress,
            engagement=engagement,
            cycle_count=self.cycle_count,
            timestamp=cycle_data.get('timestamp', 0.0)
        )

        return self.current_emotions

    def _compute_curiosity(self) -> float:
        """
        Compute curiosity metric.

        SAGE mapping: Lexical diversity, salience variation → Network diversity exploration

        High curiosity:
        - High diversity scores (exploring diverse partners)
        - High variance in diversity (trying different approaches)
        - High network density variation (exploring different topologies)

        Returns:
            Curiosity score [0-1]
        """
        if len(self.diversity_history) < 5:
            return 0.5  # Neutral until enough data

        # Measure diversity exploration
        diversity_mean = np.mean(list(self.diversity_history))
        diversity_std = np.std(list(self.diversity_history))

        # High mean diversity = exploring diverse options
        # High variance = actively varying exploration
        # Combine: 70% mean, 30% variance
        curiosity = (diversity_mean * 0.7) + (diversity_std * 0.3)

        return max(0.0, min(1.0, curiosity))

    def _compute_frustration(self) -> float:
        """
        Compute frustration metric.

        SAGE mapping: Quality stagnation, response repetition → Coordination quality stagnation

        High frustration:
        - Quality not improving (stagnant)
        - Low variance in quality (stuck at same level)
        - Repeated mediocre/low-quality cycles

        Returns:
            Frustration score [0-1]
        """
        if len(self.quality_history) < 10:
            return 0.0  # No frustration until enough data

        history_list = list(self.quality_history)
        recent_quality = history_list[-5:]
        quality_variance = np.var(recent_quality)
        mean_recent = np.mean(recent_quality)

        # Frustration = stagnation + mediocrity
        # Only high if BOTH variance is low AND quality is not high

        # Component 1: Stagnation (low variance)
        # Variance threshold: 0.01 is very low, 0.1 is high
        # Invert: low variance = high stagnation
        stagnation = max(0.0, 1.0 - (quality_variance * 20))  # Scale: 0.05 var → 0.0 stagnation

        # Component 2: Mediocrity (not high quality)
        # If quality > 0.7, don't be frustrated (even if low variance = consistent success)
        # If quality < 0.5, be frustrated
        if mean_recent > 0.7:
            mediocrity = 0.0  # High quality, no frustration
        elif mean_recent < 0.5:
            mediocrity = 1.0  # Low quality, max frustration
        else:
            # Moderate quality: scale linearly
            mediocrity = (0.7 - mean_recent) / 0.2  # 0.5-0.7 maps to 1.0-0.0

        # Combine: frustration requires BOTH stagnation AND mediocrity
        # Use geometric mean to require both (not just one)
        frustration = np.sqrt(stagnation * mediocrity)

        return max(0.0, min(1.0, frustration))

    def _compute_progress(self) -> float:
        """
        Compute progress metric.

        SAGE mapping: Quality trend → Coordination quality improvement

        High progress:
        - Recent quality > early quality (improving)
        - Positive quality slope
        - Consistent improvement trajectory

        Returns:
            Progress score [0-1]
        """
        if len(self.quality_history) < 10:
            return 0.5  # Neutral until enough data

        # Compare recent vs early quality
        history_list = list(self.quality_history)
        early_quality = np.mean(history_list[:5])
        recent_quality = np.mean(history_list[-5:])

        # Quality delta as progress indicator
        quality_delta = recent_quality - early_quality

        # Scale delta to [0-1]: delta of ±0.25 maps to [0, 1]
        progress = 0.5 + (quality_delta * 2.0)

        return max(0.0, min(1.0, progress))

    def _compute_engagement(self) -> float:
        """
        Compute engagement metric.

        SAGE mapping: Average salience, salience consistency → Priority focus

        High engagement:
        - High average priority (working on important things)
        - Low priority variance (sustained focus)
        - Consistent high-priority coordination

        Returns:
            Engagement score [0-1]
        """
        if len(self.priority_history) < 5:
            return 0.5  # Neutral until enough data

        # Measure priority focus
        priority_mean = np.mean(list(self.priority_history))
        priority_std = np.std(list(self.priority_history))

        # High mean priority = working on important things (80% weight)
        # Low variance = sustained focus (20% weight)
        # Invert std for low variance bonus
        engagement = (priority_mean * 0.8) + ((1.0 - priority_std) * 0.2)

        return max(0.0, min(1.0, engagement))

    def get_emotional_summary(self) -> Dict:
        """
        Get summary of emotional state with interpretations.

        Returns:
            Dict with emotions and human-readable interpretations
        """
        emotions = self.current_emotions

        interpretations = []

        # Curiosity interpretation
        if emotions.curiosity > 0.7:
            interpretations.append("High curiosity: Exploring diverse coordination patterns")
        elif emotions.curiosity < 0.3:
            interpretations.append("Low curiosity: Sticking to familiar patterns")
        else:
            interpretations.append("Moderate curiosity: Balanced exploration")

        # Frustration interpretation
        if emotions.frustration > 0.7:
            interpretations.append("High frustration: Quality stagnating - consider consolidation")
        elif emotions.frustration < 0.3:
            interpretations.append("Low frustration: Making progress")
        else:
            interpretations.append("Moderate frustration: Normal variation")

        # Progress interpretation
        if emotions.progress > 0.7:
            interpretations.append("High progress: Quality improving steadily")
        elif emotions.progress < 0.3:
            interpretations.append("Low progress: Quality declining - need adjustment")
        else:
            interpretations.append("Stable progress: Quality maintaining")

        # Engagement interpretation
        if emotions.engagement > 0.7:
            interpretations.append("High engagement: Focused on high-priority coordination")
        elif emotions.engagement < 0.3:
            interpretations.append("Low engagement: Working on lower-priority items")
        else:
            interpretations.append("Moderate engagement: Mixed priority work")

        return {
            'emotions': emotions.to_dict(),
            'interpretations': interpretations,
            'cycle_count': self.cycle_count
        }

    def reset(self):
        """Reset tracker state"""
        self.network_density_history.clear()
        self.diversity_history.clear()
        self.quality_history.clear()
        self.priority_history.clear()
        self.partner_history.clear()
        self.current_emotions = EmotionalCoordinationMetrics()
        self.cycle_count = 0


# Convenience functions

def track_coordination_emotions(
    coordination_history: List[Dict],
    history_length: int = 20
) -> List[EmotionalCoordinationMetrics]:
    """
    Compute emotional trajectory from coordination history.

    Args:
        coordination_history: List of coordination cycles
        history_length: Window size for metric computation

    Returns:
        List of emotional metrics, one per cycle
    """
    tracker = EmotionalCoordinationTracker(history_length)
    emotions_trajectory = []

    for cycle in coordination_history:
        emotions = tracker.update(cycle)
        emotions_trajectory.append(emotions)

    return emotions_trajectory


def detect_emotional_events(
    emotions_trajectory: List[EmotionalCoordinationMetrics],
    frustration_threshold: float = 0.7,
    curiosity_drop_threshold: float = 0.3,
    progress_drop_threshold: float = 0.3
) -> List[Dict]:
    """
    Detect significant emotional events from trajectory.

    Args:
        emotions_trajectory: Emotional metrics over time
        frustration_threshold: Threshold for high frustration
        curiosity_drop_threshold: Threshold for low curiosity
        progress_drop_threshold: Threshold for low progress

    Returns:
        List of emotional events with cycle numbers and descriptions
    """
    events = []

    for i, emotions in enumerate(emotions_trajectory):
        # High frustration event
        if emotions.frustration > frustration_threshold:
            events.append({
                'cycle': i,
                'type': 'high_frustration',
                'value': emotions.frustration,
                'description': f'High frustration ({emotions.frustration:.2f}) - quality stagnating'
            })

        # Low curiosity event (exploration exhaustion)
        if emotions.curiosity < curiosity_drop_threshold:
            events.append({
                'cycle': i,
                'type': 'low_curiosity',
                'value': emotions.curiosity,
                'description': f'Low curiosity ({emotions.curiosity:.2f}) - stuck in familiar patterns'
            })

        # Low progress event (quality declining)
        if emotions.progress < progress_drop_threshold:
            events.append({
                'cycle': i,
                'type': 'low_progress',
                'value': emotions.progress,
                'description': f'Low progress ({emotions.progress:.2f}) - quality declining'
            })

    return events


__all__ = [
    'EmotionalCoordinationMetrics',
    'EmotionalCoordinationTracker',
    'track_coordination_emotions',
    'detect_emotional_events'
]
