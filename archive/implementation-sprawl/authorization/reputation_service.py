#!/usr/bin/env python3
"""
Web4 Reputation Service for Authorization
==========================================

Bridges reputation tracker with authorization engine.

Provides T3 scores for authorization decisions.

Created: Session #24 (2025-11-13)
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# Add reputation module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "reputation"))

from reputation_tracker import ReputationTracker, get_reputation_tracker


class ReputationService:
    """
    Production reputation service for T3 score lookup.

    Integrates with actual reputation tracking system.
    Replaces mock ReputationService from authorization_engine.py.

    Usage:
        # With global tracker
        rep_service = ReputationService()

        # With custom tracker
        tracker = ReputationTracker(decay_half_life_days=60.0)
        rep_service = ReputationService(reputation_tracker=tracker)

        # Get T3 score
        t3 = rep_service.get_t3("lct:ai:agent_001", "my_org")
    """

    def __init__(self, reputation_tracker: Optional[ReputationTracker] = None):
        """
        Initialize reputation service.

        Args:
            reputation_tracker: Optional custom tracker. If None, uses global tracker.
        """
        self.reputation_tracker = reputation_tracker or get_reputation_tracker()

    def get_t3(self, lct_id: str, organization: str = "default") -> float:
        """
        Get T3 reputation score for an agent.

        Args:
            lct_id: Agent's LCT identifier
            organization: Organization context

        Returns:
            T3 score in [0.0, 1.0] range
        """
        return self.reputation_tracker.calculate_t3(lct_id, organization)

    def set_t3(self, lct_id: str, score: float, organization: str = "default"):
        """
        Set T3 reputation score (for testing only).

        NOTE: In production, reputation is built through behavior events,
        not set directly. This method exists for backward compatibility
        with authorization tests.

        Args:
            lct_id: Agent's LCT identifier
            score: T3 score to set
            organization: Organization context
        """
        # For testing: Record synthetic behavior events to achieve target score
        # This is a hack for test compatibility - production should never use this

        # Clear existing events for this agent/org
        if lct_id in self.reputation_tracker.events:
            if organization in self.reputation_tracker.events[lct_id]:
                self.reputation_tracker.events[lct_id][organization] = []

        # Create synthetic events to reach target score
        # Use inverse sigmoid to find required raw score
        import math

        # Clamp score
        score = max(0.01, min(0.99, score))

        # Inverse sigmoid: raw = -ln((1/score) - 1) / k
        k = 2.0
        raw_target = -math.log((1.0 / score) - 1.0) / k

        # Record single synthetic event with this coherence delta
        # (In production, reputation is built incrementally)
        from reputation_tracker import BehaviorType

        self.reputation_tracker.record_event(
            agent_lct=lct_id,
            behavior_type=BehaviorType.NORMAL_ACTIVITY,  # Neutral synthetic event
            organization=organization,
            description="Synthetic event for testing",
            metadata={"synthetic": True, "target_score": score}
        )

        # Manually set coherence delta to achieve target
        if lct_id in self.reputation_tracker.events:
            if organization in self.reputation_tracker.events[lct_id]:
                events = self.reputation_tracker.events[lct_id][organization]
                if events:
                    # Set the coherence delta directly (hack for testing)
                    events[-1].coherence_delta = raw_target


class MockReputationService:
    """
    Mock reputation service for testing without full reputation tracker.

    Use this for unit tests where you want to control T3 scores directly.
    Use ReputationService (above) for integration tests and production.
    """

    def __init__(self):
        # t3_scores[lct_id][organization] = score
        self.t3_scores: Dict[str, Dict[str, float]] = {}

    def get_t3(self, lct_id: str, organization: str = "default") -> float:
        """Get T3 reputation score for an agent"""
        return self.t3_scores.get(lct_id, {}).get(organization, 0.0)

    def set_t3(self, lct_id: str, score: float, organization: str = "default"):
        """Set T3 reputation score (for testing)"""
        if lct_id not in self.t3_scores:
            self.t3_scores[lct_id] = {}
        self.t3_scores[lct_id][organization] = max(0.0, min(1.0, score))  # Clamp to [0, 1]


# For backward compatibility with existing tests
def create_mock_reputation_service() -> MockReputationService:
    """
    Create a mock reputation service for testing.

    For production, use ReputationService() instead.
    """
    return MockReputationService()


# Example usage
if __name__ == "__main__":
    from reputation_tracker import BehaviorType

    print("=" * 80)
    print("Web4 Reputation Service - Integration Example")
    print("=" * 80)

    # Create reputation service (uses global tracker)
    rep_service = ReputationService()

    agent_lct = "lct:ai:example_agent"
    organization = "test_org"

    # Record some behavior events
    print(f"\nAgent: {agent_lct}")
    print(f"Organization: {organization}")
    print("\nRecording behavior events...")

    # Successful actions
    for i in range(5):
        rep_service.reputation_tracker.record_event(
            agent_lct=agent_lct,
            behavior_type=BehaviorType.SUCCESSFUL_ACTION,
            organization=organization
        )
    print("  - 5 × SUCCESSFUL_ACTION (+0.1 each)")

    # Witness verifications
    for i in range(3):
        rep_service.reputation_tracker.record_event(
            agent_lct=agent_lct,
            behavior_type=BehaviorType.WITNESS_VERIFICATION,
            organization=organization
        )
    print("  - 3 × WITNESS_VERIFICATION (+0.2 each)")

    # Get T3 score via reputation service
    t3_score = rep_service.get_t3(agent_lct, organization)

    print(f"\nT3 Score: {t3_score:.3f}")

    # Get reputation level
    from authorization_engine import get_reputation_level, get_reputation_permissions

    level = get_reputation_level(t3_score)
    permissions = get_reputation_permissions(t3_score)

    print(f"Reputation Level: {level}")
    print(f"Permissions Granted: {len(permissions)}")
    print("\nPermissions:")
    for perm in permissions:
        print(f"  - {perm}")

    print("\n" + "=" * 80)
    print("Reputation Service Integration: OPERATIONAL")
    print("=" * 80)
