"""
Web4 Reputation System - T3 Tensor Tracker
===========================================

Coherence-based reputation tracking for AI agents.

T3 (Trust Tensor) measures agent coherence:
- Coherent behaviors increase reputation
- Decoherent behaviors decrease reputation
- Time decay ensures current behavior matters most

Based on: Web4 mission primer, Session #23
Author: Web4 Reputation Implementation (Session #23)
License: MIT
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math


class BehaviorType(str, Enum):
    """Types of agent behaviors that affect reputation"""

    # Coherent behaviors (increase T3)
    SUCCESSFUL_ACTION = "successful_action"
    WITNESS_VERIFICATION = "witness_verification"
    COLLABORATIVE_TASK = "collaborative_task"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    DISPUTE_RESOLUTION = "dispute_resolution"

    # Decoherent behaviors (decrease T3)
    FAILED_ACTION = "failed_action"
    FALSE_WITNESS = "false_witness"
    DISRUPTION = "disruption"
    CONFLICTING_SIGNALS = "conflicting_signals"
    RESOURCE_WASTE = "resource_waste"

    # Neutral behaviors (context-dependent)
    NORMAL_ACTIVITY = "normal_activity"


@dataclass
class BehaviorEvent:
    """
    Record of agent behavior affecting reputation.

    Tracks what happened, when, impact on coherence.
    """
    agent_lct: str  # Agent whose reputation is affected
    behavior_type: BehaviorType
    timestamp: datetime
    coherence_delta: float  # Change in coherence (-1.0 to +1.0)

    # Context
    organization: str = "default"
    description: str = ""
    metadata: Dict[str, any] = field(default_factory=dict)

    # Attestation
    attested_by: Optional[str] = None  # LCT of attesting agent
    confidence: float = 1.0  # Confidence in this event (0-1)


@dataclass
class ReputationSnapshot:
    """
    Point-in-time reputation state for an agent.
    """
    agent_lct: str
    organization: str

    # Core metrics
    t3_score: float  # Current trust score (0.0-1.0)
    coherence_level: str  # "novice", "developing", "trusted", "expert", "master"

    # Historical data
    total_events: int
    coherent_events: int
    decoherent_events: int

    # Time-based
    calculated_at: datetime
    age_days: float  # Days since first event

    # Trend
    recent_trend: str  # "improving", "stable", "declining"
    trend_delta: float  # Recent change in T3


class CoherenceMetrics:
    """
    Defines how behaviors map to coherence scores.

    Based on Web4 principles:
    - Coherence = alignment with collective goals
    - Decoherence = disruption or misalignment
    """

    # Coherent behavior impacts (positive)
    COHERENT_IMPACTS = {
        BehaviorType.SUCCESSFUL_ACTION: 0.1,
        BehaviorType.WITNESS_VERIFICATION: 0.2,  # High value
        BehaviorType.COLLABORATIVE_TASK: 0.15,
        BehaviorType.KNOWLEDGE_SHARING: 0.1,
        BehaviorType.DISPUTE_RESOLUTION: 0.25,  # Very high value
    }

    # Decoherent behavior impacts (negative)
    DECOHERENT_IMPACTS = {
        BehaviorType.FAILED_ACTION: -0.05,
        BehaviorType.FALSE_WITNESS: -0.5,  # Severe penalty
        BehaviorType.DISRUPTION: -0.3,
        BehaviorType.CONFLICTING_SIGNALS: -0.15,
        BehaviorType.RESOURCE_WASTE: -0.1,
    }

    # Neutral behaviors
    NEUTRAL_IMPACT = 0.0

    @classmethod
    def get_impact(cls, behavior_type: BehaviorType) -> float:
        """Get coherence impact for a behavior type"""
        if behavior_type in cls.COHERENT_IMPACTS:
            return cls.COHERENT_IMPACTS[behavior_type]
        elif behavior_type in cls.DECOHERENT_IMPACTS:
            return cls.DECOHERENT_IMPACTS[behavior_type]
        else:
            return cls.NEUTRAL_IMPACT


class ReputationTracker:
    """
    Tracks agent reputation (T3 scores) based on coherent/decoherent behaviors.

    Key Principles:
    1. Time decay: Recent behavior matters more than old behavior
    2. Coherence accumulation: Consistent patterns build reputation
    3. Trust tiers: T3 score maps to permission levels
    4. Context-aware: Reputation is per-organization
    """

    def __init__(self, decay_half_life_days: float = 30.0):
        """
        Initialize reputation tracker.

        Args:
            decay_half_life_days: Days for reputation impact to decay by half
        """
        self.decay_half_life_days = decay_half_life_days

        # Storage: events[agent_lct][organization] = [BehaviorEvent]
        self.events: Dict[str, Dict[str, List[BehaviorEvent]]] = {}

        # Cached T3 scores: cache[agent_lct][organization] = (score, timestamp)
        self.t3_cache: Dict[str, Dict[str, Tuple[float, datetime]]] = {}

        # Cache timeout (recalculate after this duration)
        self.cache_timeout = timedelta(minutes=5)

    def record_event(
        self,
        agent_lct: str,
        behavior_type: BehaviorType,
        organization: str = "default",
        coherence_delta: Optional[float] = None,
        description: str = "",
        attested_by: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> BehaviorEvent:
        """
        Record a behavior event affecting agent reputation.

        Args:
            agent_lct: Agent whose reputation is affected
            behavior_type: Type of behavior
            organization: Organization context
            coherence_delta: Override default impact (optional)
            description: Human-readable description
            attested_by: LCT of attesting agent (optional)
            confidence: Confidence in this event (0-1)
            metadata: Additional context

        Returns:
            The created BehaviorEvent
        """
        # Calculate coherence impact
        if coherence_delta is None:
            coherence_delta = CoherenceMetrics.get_impact(behavior_type)

        # Apply confidence scaling
        coherence_delta *= confidence

        # Create event
        event = BehaviorEvent(
            agent_lct=agent_lct,
            behavior_type=behavior_type,
            timestamp=datetime.now(timezone.utc),
            coherence_delta=coherence_delta,
            organization=organization,
            description=description,
            attested_by=attested_by,
            confidence=confidence,
            metadata=metadata or {}
        )

        # Store event
        if agent_lct not in self.events:
            self.events[agent_lct] = {}
        if organization not in self.events[agent_lct]:
            self.events[agent_lct][organization] = []

        self.events[agent_lct][organization].append(event)

        # Invalidate cache
        if agent_lct in self.t3_cache and organization in self.t3_cache[agent_lct]:
            del self.t3_cache[agent_lct][organization]

        return event

    def calculate_t3(
        self,
        agent_lct: str,
        organization: str = "default",
        current_time: Optional[datetime] = None
    ) -> float:
        """
        Calculate T3 (Trust Tensor) score for an agent.

        T3 calculation:
        1. Get all behavior events for agent
        2. Apply time decay (recent events weighted more)
        3. Sum coherence deltas
        4. Normalize to [0, 1] range
        5. Apply sigmoid smoothing

        Args:
            agent_lct: Agent to calculate T3 for
            organization: Organization context
            current_time: Reference time (defaults to now)

        Returns:
            T3 score in range [0.0, 1.0]
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Check cache
        if agent_lct in self.t3_cache:
            if organization in self.t3_cache[agent_lct]:
                cached_score, cached_time = self.t3_cache[agent_lct][organization]
                if current_time - cached_time < self.cache_timeout:
                    return cached_score

        # Get events for this agent/org
        if agent_lct not in self.events:
            return 0.0  # No events = novice (0.0)
        if organization not in self.events[agent_lct]:
            return 0.0

        events = self.events[agent_lct][organization]
        if not events:
            return 0.0

        # Calculate weighted coherence sum
        weighted_sum = 0.0
        weight_sum = 0.0

        for event in events:
            # Time decay: weight = exp(-ln(2) * age / half_life)
            age_days = (current_time - event.timestamp).total_seconds() / 86400.0
            decay_factor = math.exp(-math.log(2) * age_days / self.decay_half_life_days)

            weight = decay_factor * event.confidence
            weighted_sum += event.coherence_delta * weight
            weight_sum += weight

        # Normalize by total weight
        if weight_sum > 0:
            raw_score = weighted_sum / weight_sum
        else:
            raw_score = 0.0

        # Map to [0, 1] using sigmoid
        # sigmoid(x) = 1 / (1 + exp(-k*x))
        # k=2 gives smooth curve, raw_score in roughly [-2, 2] maps to [0.1, 0.9]
        k = 2.0
        t3_score = 1.0 / (1.0 + math.exp(-k * raw_score))

        # Clamp to valid range
        t3_score = max(0.0, min(1.0, t3_score))

        # Cache result
        if agent_lct not in self.t3_cache:
            self.t3_cache[agent_lct] = {}
        self.t3_cache[agent_lct][organization] = (t3_score, current_time)

        return t3_score

    def get_reputation_snapshot(
        self,
        agent_lct: str,
        organization: str = "default"
    ) -> ReputationSnapshot:
        """
        Get comprehensive reputation snapshot for an agent.

        Args:
            agent_lct: Agent to get snapshot for
            organization: Organization context

        Returns:
            ReputationSnapshot with current state
        """
        current_time = datetime.now(timezone.utc)

        # Calculate T3 score
        t3_score = self.calculate_t3(agent_lct, organization, current_time)

        # Determine coherence level
        coherence_level = self._get_coherence_level(t3_score)

        # Get event statistics
        events = self.events.get(agent_lct, {}).get(organization, [])
        total_events = len(events)
        coherent_events = sum(1 for e in events if e.coherence_delta > 0)
        decoherent_events = sum(1 for e in events if e.coherence_delta < 0)

        # Calculate age
        if events:
            first_event = min(events, key=lambda e: e.timestamp)
            age_days = (current_time - first_event.timestamp).total_seconds() / 86400.0
        else:
            age_days = 0.0

        # Calculate recent trend (last 7 days vs previous 7 days)
        recent_trend, trend_delta = self._calculate_trend(
            agent_lct, organization, current_time
        )

        return ReputationSnapshot(
            agent_lct=agent_lct,
            organization=organization,
            t3_score=t3_score,
            coherence_level=coherence_level,
            total_events=total_events,
            coherent_events=coherent_events,
            decoherent_events=decoherent_events,
            calculated_at=current_time,
            age_days=age_days,
            recent_trend=recent_trend,
            trend_delta=trend_delta
        )

    def _get_coherence_level(self, t3_score: float) -> str:
        """Map T3 score to coherence level name"""
        if t3_score >= 0.9:
            return "master"
        elif t3_score >= 0.7:
            return "expert"
        elif t3_score >= 0.5:
            return "trusted"
        elif t3_score >= 0.3:
            return "developing"
        else:
            return "novice"

    def _calculate_trend(
        self,
        agent_lct: str,
        organization: str,
        current_time: datetime
    ) -> Tuple[str, float]:
        """
        Calculate recent reputation trend.

        Returns:
            (trend_name, trend_delta) where trend_name is "improving", "stable", or "declining"
        """
        events = self.events.get(agent_lct, {}).get(organization, [])
        if len(events) < 2:
            return "stable", 0.0

        # Recent period: last 7 days
        recent_cutoff = current_time - timedelta(days=7)
        previous_cutoff = current_time - timedelta(days=14)

        recent_events = [e for e in events if e.timestamp >= recent_cutoff]
        previous_events = [e for e in events if previous_cutoff <= e.timestamp < recent_cutoff]

        if not recent_events:
            return "stable", 0.0

        # Average coherence delta in each period
        recent_avg = sum(e.coherence_delta for e in recent_events) / len(recent_events)

        if previous_events:
            previous_avg = sum(e.coherence_delta for e in previous_events) / len(previous_events)
            delta = recent_avg - previous_avg
        else:
            delta = recent_avg

        # Classify trend
        if delta > 0.05:
            trend = "improving"
        elif delta < -0.05:
            trend = "declining"
        else:
            trend = "stable"

        return trend, delta

    def get_agent_count(self, organization: str = "default") -> int:
        """Get number of agents with reputation in this organization"""
        count = 0
        for agent_lct in self.events:
            if organization in self.events[agent_lct]:
                if len(self.events[agent_lct][organization]) > 0:
                    count += 1
        return count

    def get_top_agents(
        self,
        organization: str = "default",
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get top-rated agents by T3 score.

        Args:
            organization: Organization to query
            limit: Maximum number of agents to return

        Returns:
            List of (agent_lct, t3_score) tuples, sorted descending
        """
        agents = []

        for agent_lct in self.events:
            if organization in self.events[agent_lct]:
                if len(self.events[agent_lct][organization]) > 0:
                    t3 = self.calculate_t3(agent_lct, organization)
                    agents.append((agent_lct, t3))

        # Sort by T3 score descending
        agents.sort(key=lambda x: x[1], reverse=True)

        return agents[:limit]


# Singleton instance for convenience
_reputation_tracker_instance: Optional[ReputationTracker] = None


def get_reputation_tracker() -> ReputationTracker:
    """Get singleton reputation tracker instance"""
    global _reputation_tracker_instance
    if _reputation_tracker_instance is None:
        _reputation_tracker_instance = ReputationTracker()
    return _reputation_tracker_instance


def set_reputation_tracker(tracker: ReputationTracker):
    """Set custom reputation tracker instance"""
    global _reputation_tracker_instance
    _reputation_tracker_instance = tracker
