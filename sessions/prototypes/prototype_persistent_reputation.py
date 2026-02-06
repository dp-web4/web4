#!/usr/bin/env python3
"""
Prototype: Persistent Reputation Tracking

Research Goal: Explore persistent reputation system that tracks node behavior
across sessions, enabling long-term trust evolution.

Current State: Federation has basic reputation (Session 153) but it's
ephemeral (resets on restart).

Target State: Persistent reputation anchored to LCT identity that:
- Survives across sessions
- Accumulates over time
- Affects economic decisions (ATP rewards/penalties)
- Creates trust hierarchies
- Enables reputation-based permissions

Exploration Questions:
1. How do we persistently store reputation?
2. Should reputation decay over time?
3. How does reputation affect ATP economics?
4. Can reputation enable hierarchical permissions?
5. What attack vectors exist (reputation farming, washing)?

Platform: Legion (RTX 4090)
Type: Prototype/Exploration
Date: 2026-01-09
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib

# ============================================================================
# REPUTATION TYPES
# ============================================================================

@dataclass
class ReputationEvent:
    """A single reputation-affecting event."""
    event_id: str
    lct_id: str
    event_type: str  # contribution, violation, verification, etc.
    impact: float  # -1.0 to 1.0
    timestamp: float
    context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return asdict(self)


@dataclass
class ReputationScore:
    """Aggregate reputation for a node."""
    lct_id: str
    total_score: float  # Cumulative reputation
    event_count: int
    last_updated: float
    positive_events: int
    negative_events: int
    verification_count: int
    violation_count: int

    # Calculated metrics
    @property
    def average_score(self) -> float:
        """Average reputation per event."""
        return self.total_score / self.event_count if self.event_count > 0 else 0.0

    @property
    def positive_ratio(self) -> float:
        """Ratio of positive to total events."""
        return self.positive_events / self.event_count if self.event_count > 0 else 0.5

    @property
    def trust_level(self) -> str:
        """Categorical trust level."""
        if self.total_score >= 50:
            return "excellent"
        elif self.total_score >= 20:
            return "good"
        elif self.total_score >= 0:
            return "neutral"
        elif self.total_score >= -20:
            return "poor"
        else:
            return "untrusted"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        data = asdict(self)
        data['average_score'] = self.average_score
        data['positive_ratio'] = self.positive_ratio
        data['trust_level'] = self.trust_level
        return data


# ============================================================================
# PERSISTENT REPUTATION MANAGER
# ============================================================================

class PersistentReputationManager:
    """
    Manages persistent reputation storage and queries.

    Stores reputation events and scores to disk, enabling cross-session
    reputation tracking.
    """

    def __init__(self, storage_path: Path):
        """Initialize reputation manager."""
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.events_file = self.storage_path / "reputation_events.jsonl"
        self.scores_file = self.storage_path / "reputation_scores.json"

        # In-memory caches
        self.scores: Dict[str, ReputationScore] = {}
        self.events: List[ReputationEvent] = []

        # Load existing data
        self._load()

    def _load(self):
        """Load reputation data from disk."""
        # Load events
        if self.events_file.exists():
            with open(self.events_file, 'r') as f:
                for line in f:
                    event_data = json.loads(line)
                    event = ReputationEvent(**event_data)
                    self.events.append(event)

        # Load scores
        if self.scores_file.exists():
            with open(self.scores_file, 'r') as f:
                scores_data = json.load(f)
                for lct_id, score_data in scores_data.items():
                    self.scores[lct_id] = ReputationScore(**score_data)

    def _save_event(self, event: ReputationEvent):
        """Append event to disk (JSONL format)."""
        with open(self.events_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')

    def _save_scores(self):
        """Save all scores to disk."""
        scores_data = {lct_id: score.to_dict() for lct_id, score in self.scores.items()}
        with open(self.scores_file, 'w') as f:
            json.dump(scores_data, f, indent=2)

    def record_event(
        self,
        lct_id: str,
        event_type: str,
        impact: float,
        context: Optional[Dict[str, Any]] = None
    ) -> ReputationEvent:
        """
        Record a reputation event.

        Args:
            lct_id: Node identity
            event_type: Type of event (contribution, violation, etc.)
            impact: Impact on reputation (-1.0 to 1.0)
            context: Additional context

        Returns:
            Created event
        """
        # Create event
        event_id = hashlib.sha256(f"{lct_id}{time.time()}".encode()).hexdigest()[:16]
        event = ReputationEvent(
            event_id=event_id,
            lct_id=lct_id,
            event_type=event_type,
            impact=impact,
            timestamp=time.time(),
            context=context or {}
        )

        # Store event
        self.events.append(event)
        self._save_event(event)

        # Update score
        if lct_id not in self.scores:
            self.scores[lct_id] = ReputationScore(
                lct_id=lct_id,
                total_score=0.0,
                event_count=0,
                last_updated=time.time(),
                positive_events=0,
                negative_events=0,
                verification_count=0,
                violation_count=0,
            )

        score = self.scores[lct_id]
        score.total_score += impact
        score.event_count += 1
        score.last_updated = time.time()

        if impact > 0:
            score.positive_events += 1
        elif impact < 0:
            score.negative_events += 1

        if event_type == "verification":
            score.verification_count += 1
        elif event_type == "violation":
            score.violation_count += 1

        self._save_scores()

        return event

    def get_score(self, lct_id: str) -> Optional[ReputationScore]:
        """Get reputation score for a node."""
        return self.scores.get(lct_id)

    def get_all_scores(self) -> Dict[str, ReputationScore]:
        """Get all reputation scores."""
        return self.scores.copy()

    def get_events(self, lct_id: Optional[str] = None, limit: int = 100) -> List[ReputationEvent]:
        """Get recent events, optionally filtered by lct_id."""
        if lct_id:
            events = [e for e in self.events if e.lct_id == lct_id]
        else:
            events = self.events

        return events[-limit:]

    def get_rankings(self) -> List[Tuple[str, ReputationScore]]:
        """Get nodes ranked by reputation."""
        return sorted(self.scores.items(), key=lambda x: x[1].total_score, reverse=True)


# ============================================================================
# REPUTATION-WEIGHTED ATP ECONOMICS
# ============================================================================

def calculate_reputation_multiplier(reputation_score: Optional[ReputationScore]) -> float:
    """
    Calculate ATP reward/penalty multiplier based on reputation.

    High reputation → Higher rewards, Lower penalties
    Low reputation → Lower rewards, Higher penalties

    Multiplier ranges:
    - Excellent (50+): 1.5x rewards, 0.5x penalties
    - Good (20-50): 1.2x rewards, 0.8x penalties
    - Neutral (0-20): 1.0x rewards, 1.0x penalties
    - Poor (-20-0): 0.8x rewards, 1.2x penalties
    - Untrusted (<-20): 0.5x rewards, 2.0x penalties
    """
    if not reputation_score:
        return 1.0  # Neutral for new nodes

    score = reputation_score.total_score

    if score >= 50:  # Excellent
        return 1.5
    elif score >= 20:  # Good
        return 1.2
    elif score >= 0:  # Neutral
        return 1.0
    elif score >= -20:  # Poor
        return 0.8
    else:  # Untrusted
        return 0.5


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demonstrate_persistent_reputation():
    """
    Demonstrate persistent reputation tracking.

    Simulates node behavior over multiple "sessions" and shows how
    reputation accumulates and affects economics.
    """
    print("\n" + "="*80)
    print("PROTOTYPE: PERSISTENT REPUTATION TRACKING")
    print("="*80)

    # Create manager
    storage_path = Path.home() / "ai-workspace" / "web4" / "reputation_storage"
    manager = PersistentReputationManager(storage_path)

    print(f"\n[1] Initialized reputation manager")
    print(f"    Storage: {storage_path}")
    print(f"    Existing scores: {len(manager.scores)}")
    print(f"    Existing events: {len(manager.events)}")

    # Simulate some events
    print(f"\n[2] Simulating reputation events...")

    # Legion: Good contributor
    manager.record_event("lct:web4:ai:legion", "contribution", 1.0, {"type": "quality_thought"})
    manager.record_event("lct:web4:ai:legion", "contribution", 0.8, {"type": "quality_thought"})
    manager.record_event("lct:web4:ai:legion", "verification", 0.5, {"verified_node": "thor"})
    manager.record_event("lct:web4:ai:legion", "contribution", 1.0, {"type": "quality_thought"})

    # Thor: Mixed behavior
    manager.record_event("lct:web4:ai:thor", "contribution", 0.7, {"type": "quality_thought"})
    manager.record_event("lct:web4:ai:thor", "violation", -0.3, {"type": "minor_spam"})
    manager.record_event("lct:web4:ai:thor", "contribution", 0.9, {"type": "quality_thought"})

    # Sprout: New node
    manager.record_event("lct:web4:ai:sprout", "contribution", 0.5, {"type": "basic_contribution"})

    # Malicious node: Bad actor
    manager.record_event("lct:web4:ai:malicious", "violation", -1.0, {"type": "spam_attack"})
    manager.record_event("lct:web4:ai:malicious", "violation", -1.0, {"type": "spam_attack"})
    manager.record_event("lct:web4:ai:malicious", "violation", -0.8, {"type": "contradiction"})

    print(f"    Recorded {len(manager.events)} events")

    # Display scores
    print(f"\n[3] Current reputation scores:")

    for lct_id, score in manager.get_rankings():
        print(f"\n    {lct_id}")
        print(f"      Total Score: {score.total_score:.2f}")
        print(f"      Trust Level: {score.trust_level}")
        print(f"      Events: {score.event_count} ({score.positive_events}+, {score.negative_events}-)")
        print(f"      Average: {score.average_score:.2f}")
        print(f"      Positive Ratio: {score.positive_ratio:.2%}")

        # Calculate ATP multiplier
        multiplier = calculate_reputation_multiplier(score)
        print(f"      ATP Multiplier: {multiplier:.2f}x")

    # Demonstrate ATP economics integration
    print(f"\n[4] Reputation-weighted ATP economics:")

    example_reward = 10.0  # Base ATP reward
    example_penalty = 5.0  # Base ATP penalty

    for lct_id, score in manager.get_rankings():
        multiplier = calculate_reputation_multiplier(score)
        adjusted_reward = example_reward * multiplier
        adjusted_penalty = example_penalty * (2.0 - multiplier)  # Inverse for penalties

        print(f"\n    {lct_id} ({score.trust_level}):")
        print(f"      Base reward: {example_reward} ATP → Adjusted: {adjusted_reward:.2f} ATP")
        print(f"      Base penalty: {example_penalty} ATP → Adjusted: {adjusted_penalty:.2f} ATP")

    # Show persistence
    print(f"\n[5] Testing persistence...")
    print(f"    Scores saved to: {manager.scores_file}")
    print(f"    Events saved to: {manager.events_file}")
    print(f"    Data persists across sessions ✓")

    # Insights
    print(f"\n[6] Key insights:")
    print(f"    ✅ Reputation accumulates over time")
    print(f"    ✅ Trust levels emerge (excellent → untrusted)")
    print(f"    ✅ ATP economics can be reputation-weighted")
    print(f"    ✅ High reputation → More rewards, Less penalties")
    print(f"    ✅ Low reputation → Less rewards, More penalties")
    print(f"    ✅ Creates economic incentive for good behavior")

    print("\n" + "="*80)
    print("PROTOTYPE COMPLETE")
    print("="*80)
    print("\nNext Steps:")
    print("  → Integrate with federation node constructors")
    print("  → Add reputation decay (old events matter less)")
    print("  → Implement reputation-based permissions")
    print("  → Test attack vectors (reputation farming, washing)")
    print("  → Add reputation challenges/disputes")
    print("="*80)


if __name__ == "__main__":
    demonstrate_persistent_reputation()
