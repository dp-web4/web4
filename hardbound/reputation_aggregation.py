"""
Reputation Aggregation: Cross-Federation Trust Scores

Track BV: Aggregates trust relationships into global reputation scores.

Key principles:
1. Reputation = weighted aggregate of incoming trust
2. High-presence federations have more influence on reputation
3. Reputation decays without ongoing endorsements
4. Cross-federation trust contributes more than self-reported

This creates a "PageRank for trust" - reputation emerges from
the network structure of trust relationships.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from pathlib import Path

from hardbound.multi_federation import MultiFederationRegistry, InterFederationTrust
from hardbound.federation_binding import FederationBindingRegistry


class ReputationTier(Enum):
    """Reputation tiers for quick categorization."""
    UNKNOWN = "unknown"       # New federation, no reputation data
    EMERGING = "emerging"     # Building reputation (0.2-0.4)
    ESTABLISHED = "established"  # Solid reputation (0.4-0.6)
    TRUSTED = "trusted"       # High reputation (0.6-0.8)
    EXEMPLARY = "exemplary"   # Top-tier reputation (0.8+)


@dataclass
class ReputationScore:
    """Comprehensive reputation score for a federation."""
    federation_id: str

    # Core metrics
    global_reputation: float  # Aggregated score (0-1)
    tier: ReputationTier

    # Components
    incoming_trust_sum: float  # Sum of trust from others
    incoming_trust_count: int  # Number of inbound trust relationships
    presence_weighted_trust: float  # Trust weighted by source presence
    outgoing_trust_sum: float  # Trust given to others (reciprocity signal)

    # Network position
    trust_ratio: float  # incoming/outgoing ratio
    network_centrality: float  # How connected this federation is

    # Time factors
    reputation_age_days: int  # Days since first trust relationship
    recent_activity_score: float  # Activity in last 30 days

    # Confidence
    confidence: float  # How confident we are in this score (0-1)
    sample_size: int  # Number of data points

    timestamp: str = ""


@dataclass
class ReputationEvent:
    """An event that affects reputation."""
    event_id: str
    federation_id: str
    event_type: str  # trust_received, trust_given, witness_provided, proposal_approved, etc.
    magnitude: float  # Impact magnitude
    source_federation: str = ""
    timestamp: str = ""
    details: Dict = field(default_factory=dict)


class ReputationAggregator:
    """
    Aggregates trust into reputation scores.

    Track BV: "PageRank for trust"

    The algorithm:
    1. Collect all incoming trust relationships
    2. Weight by source federation's presence
    3. Apply network position adjustments
    4. Decay based on relationship age
    5. Calculate confidence based on sample size
    """

    # Weighting factors
    PRESENCE_WEIGHT = 0.4  # How much source presence matters
    TRUST_WEIGHT = 0.5  # How much raw trust matters
    ACTIVITY_WEIGHT = 0.1  # How much recent activity matters

    # Tier thresholds
    TIER_THRESHOLDS = {
        ReputationTier.UNKNOWN: 0.0,
        ReputationTier.EMERGING: 0.2,
        ReputationTier.ESTABLISHED: 0.4,
        ReputationTier.TRUSTED: 0.6,
        ReputationTier.EXEMPLARY: 0.8,
    }

    # Decay factor for old relationships (per 30 days)
    RELATIONSHIP_DECAY = 0.95

    # Minimum relationships for high confidence
    MIN_RELATIONSHIPS_HIGH_CONFIDENCE = 5

    def __init__(
        self,
        federation_registry: MultiFederationRegistry,
        binding_registry: Optional[FederationBindingRegistry] = None,
    ):
        """
        Initialize reputation aggregator.

        Args:
            federation_registry: Source of trust relationships
            binding_registry: Source of presence scores (optional)
        """
        self.registry = federation_registry
        self.binding = binding_registry

        # Cache reputation scores
        self._reputation_cache: Dict[str, ReputationScore] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minute cache

        # Event history
        self._events: List[ReputationEvent] = []

    def calculate_reputation(
        self,
        federation_id: str,
        force_refresh: bool = False,
    ) -> ReputationScore:
        """
        Calculate comprehensive reputation score for a federation.

        Args:
            federation_id: Federation to calculate reputation for
            force_refresh: Bypass cache

        Returns:
            ReputationScore with all components
        """
        # Check cache
        if not force_refresh and federation_id in self._reputation_cache:
            cached = self._reputation_cache[federation_id]
            cache_age = (datetime.now(timezone.utc) -
                        datetime.fromisoformat(cached.timestamp.replace('Z', '+00:00')))
            if cache_age.total_seconds() < self._cache_ttl_seconds:
                return cached

        # Get all trust relationships involving this federation
        incoming = self._get_incoming_trust(federation_id)
        outgoing = self._get_outgoing_trust(federation_id)

        # Calculate components
        incoming_trust_sum = sum(t.trust_score for t in incoming)
        incoming_trust_count = len(incoming)
        outgoing_trust_sum = sum(t.trust_score for t in outgoing)
        outgoing_trust_count = len(outgoing)

        # Presence-weighted trust
        presence_weighted_trust = self._calculate_presence_weighted_trust(incoming)

        # Network centrality (normalized connection count)
        total_federations = len(self._get_all_federation_ids())
        if total_federations > 1:
            network_centrality = (incoming_trust_count + outgoing_trust_count) / (2 * (total_federations - 1))
        else:
            network_centrality = 0.0

        # Trust ratio (incoming vs outgoing)
        if outgoing_trust_sum > 0:
            trust_ratio = incoming_trust_sum / outgoing_trust_sum
        else:
            trust_ratio = incoming_trust_sum if incoming_trust_sum > 0 else 1.0

        # Recent activity
        recent_activity_score = self._calculate_recent_activity(federation_id)

        # Calculate global reputation
        global_reputation = self._calculate_global_reputation(
            presence_weighted_trust=presence_weighted_trust,
            network_centrality=network_centrality,
            trust_ratio=trust_ratio,
            recent_activity=recent_activity_score,
            incoming_count=incoming_trust_count,
        )

        # Determine tier
        tier = self._determine_tier(global_reputation, incoming_trust_count)

        # Calculate confidence
        confidence = self._calculate_confidence(incoming_trust_count, outgoing_trust_count)

        # Calculate reputation age
        reputation_age_days = self._calculate_reputation_age(incoming, outgoing)

        # Build score
        score = ReputationScore(
            federation_id=federation_id,
            global_reputation=global_reputation,
            tier=tier,
            incoming_trust_sum=incoming_trust_sum,
            incoming_trust_count=incoming_trust_count,
            presence_weighted_trust=presence_weighted_trust,
            outgoing_trust_sum=outgoing_trust_sum,
            trust_ratio=trust_ratio,
            network_centrality=network_centrality,
            reputation_age_days=reputation_age_days,
            recent_activity_score=recent_activity_score,
            confidence=confidence,
            sample_size=incoming_trust_count + outgoing_trust_count,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Cache
        self._reputation_cache[federation_id] = score

        return score

    def _get_incoming_trust(self, federation_id: str) -> List[InterFederationTrust]:
        """Get all trust relationships where this federation is the target."""
        all_relationships = self.registry.get_all_relationships()
        return [t for t in all_relationships if t.target_federation_id == federation_id]

    def _get_outgoing_trust(self, federation_id: str) -> List[InterFederationTrust]:
        """Get all trust relationships where this federation is the source."""
        all_relationships = self.registry.get_all_relationships()
        return [t for t in all_relationships if t.source_federation_id == federation_id]

    def _get_all_federation_ids(self) -> Set[str]:
        """Get all federation IDs in the registry."""
        relationships = self.registry.get_all_relationships()
        ids = set()
        for r in relationships:
            ids.add(r.source_federation_id)
            ids.add(r.target_federation_id)
        return ids

    def _calculate_presence_weighted_trust(
        self,
        incoming_trust: List[InterFederationTrust],
    ) -> float:
        """
        Weight incoming trust by source federation's presence.

        Trust from high-presence federations counts more.
        """
        if not incoming_trust:
            return 0.0

        weighted_sum = 0.0
        weight_total = 0.0

        for trust in incoming_trust:
            # Get source presence
            source_presence = 0.5  # Default if no binding registry
            if self.binding:
                status = self.binding.get_federation_binding_status(trust.source_federation_id)
                if status:
                    source_presence = status.presence_score

            # Weight: presence affects how much this trust "counts"
            weight = 0.5 + (source_presence * 0.5)  # 0.5 to 1.0 range
            weighted_sum += trust.trust_score * weight
            weight_total += weight

        if weight_total == 0:
            return 0.0

        return weighted_sum / weight_total

    def _calculate_recent_activity(self, federation_id: str) -> float:
        """
        Calculate activity score based on recent events.

        More recent activity = higher score.
        """
        recent_events = [
            e for e in self._events
            if e.federation_id == federation_id
            and self._is_within_days(e.timestamp, 30)
        ]

        if not recent_events:
            return 0.3  # Default baseline

        # Score based on event count and recency
        activity_score = min(1.0, len(recent_events) * 0.1 + 0.3)
        return activity_score

    def _is_within_days(self, timestamp_str: str, days: int) -> bool:
        """Check if timestamp is within N days of now."""
        if not timestamp_str:
            return False
        try:
            ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            return ts > cutoff
        except:
            return False

    def _calculate_global_reputation(
        self,
        presence_weighted_trust: float,
        network_centrality: float,
        trust_ratio: float,
        recent_activity: float,
        incoming_count: int,
    ) -> float:
        """
        Calculate the final global reputation score.

        Formula:
        - 50% presence-weighted incoming trust
        - 20% network centrality
        - 20% trust ratio (capped)
        - 10% recent activity

        Then adjust for sample size (low sample = lower score).
        """
        # Cap trust ratio contribution (extreme ratios don't add much)
        capped_ratio = min(2.0, trust_ratio) / 2.0  # Normalize to 0-1

        # Base score
        base_score = (
            presence_weighted_trust * 0.50 +
            network_centrality * 0.20 +
            capped_ratio * 0.20 +
            recent_activity * 0.10
        )

        # Sample size adjustment
        # Low sample size reduces score confidence
        if incoming_count == 0:
            return 0.0
        elif incoming_count < 3:
            base_score *= 0.7  # Significant reduction
        elif incoming_count < 5:
            base_score *= 0.85  # Moderate reduction

        return min(1.0, base_score)

    def _determine_tier(self, reputation: float, relationship_count: int) -> ReputationTier:
        """Determine reputation tier based on score and relationships."""
        if relationship_count == 0:
            return ReputationTier.UNKNOWN

        for tier in reversed(list(ReputationTier)):
            if reputation >= self.TIER_THRESHOLDS.get(tier, 0.0):
                return tier

        return ReputationTier.UNKNOWN

    def _calculate_confidence(
        self,
        incoming_count: int,
        outgoing_count: int,
    ) -> float:
        """
        Calculate confidence in the reputation score.

        More relationships = higher confidence.
        """
        total = incoming_count + outgoing_count

        if total == 0:
            return 0.0
        elif total < 3:
            return 0.3
        elif total < self.MIN_RELATIONSHIPS_HIGH_CONFIDENCE:
            return 0.5 + (total - 3) * 0.1
        else:
            return min(1.0, 0.7 + (total - self.MIN_RELATIONSHIPS_HIGH_CONFIDENCE) * 0.05)

    def _calculate_reputation_age(
        self,
        incoming: List[InterFederationTrust],
        outgoing: List[InterFederationTrust],
    ) -> int:
        """Calculate days since first trust relationship."""
        all_relationships = incoming + outgoing
        if not all_relationships:
            return 0

        # Find oldest relationship
        oldest = None
        for r in all_relationships:
            if r.established_at:
                try:
                    ts = datetime.fromisoformat(r.established_at.replace('Z', '+00:00'))
                    if oldest is None or ts < oldest:
                        oldest = ts
                except:
                    pass

        if oldest:
            age = datetime.now(timezone.utc) - oldest
            return age.days

        return 0

    def get_reputation_ranking(
        self,
        limit: int = 10,
    ) -> List[ReputationScore]:
        """
        Get federations ranked by reputation.

        Returns top N federations by global reputation.
        """
        all_ids = self._get_all_federation_ids()
        scores = [self.calculate_reputation(fid) for fid in all_ids]

        # Sort by reputation descending
        scores.sort(key=lambda s: s.global_reputation, reverse=True)

        return scores[:limit]

    def get_tier_distribution(self) -> Dict[ReputationTier, int]:
        """Get distribution of federations across reputation tiers."""
        all_ids = self._get_all_federation_ids()
        distribution = {tier: 0 for tier in ReputationTier}

        for fid in all_ids:
            score = self.calculate_reputation(fid)
            distribution[score.tier] += 1

        return distribution

    def record_event(
        self,
        federation_id: str,
        event_type: str,
        magnitude: float,
        source_federation: str = "",
        details: Optional[Dict] = None,
    ) -> ReputationEvent:
        """
        Record an event that affects reputation.

        Events are used for recent activity calculations.
        """
        import uuid

        event = ReputationEvent(
            event_id=f"rep_evt:{uuid.uuid4().hex[:8]}",
            federation_id=federation_id,
            event_type=event_type,
            magnitude=magnitude,
            source_federation=source_federation,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details or {},
        )

        self._events.append(event)

        # Invalidate cache for affected federation
        if federation_id in self._reputation_cache:
            del self._reputation_cache[federation_id]

        return event

    def compare_reputations(
        self,
        federation_a: str,
        federation_b: str,
    ) -> Dict:
        """
        Compare reputation between two federations.

        Returns detailed comparison with differences highlighted.
        """
        score_a = self.calculate_reputation(federation_a)
        score_b = self.calculate_reputation(federation_b)

        return {
            "federation_a": federation_a,
            "federation_b": federation_b,
            "reputation_a": score_a.global_reputation,
            "reputation_b": score_b.global_reputation,
            "reputation_difference": score_a.global_reputation - score_b.global_reputation,
            "tier_a": score_a.tier.value,
            "tier_b": score_b.tier.value,
            "same_tier": score_a.tier == score_b.tier,
            "confidence_a": score_a.confidence,
            "confidence_b": score_b.confidence,
            "higher_reputation": (
                federation_a if score_a.global_reputation > score_b.global_reputation
                else federation_b if score_b.global_reputation > score_a.global_reputation
                else "equal"
            ),
        }

    def get_reputation_requirements(
        self,
        action: str,
    ) -> Dict:
        """
        Get reputation requirements for various actions.

        Different actions require different reputation levels.
        """
        requirements = {
            "basic_participation": {
                "min_tier": ReputationTier.UNKNOWN,
                "min_reputation": 0.0,
                "description": "Any federation can participate",
            },
            "cross_fed_proposal": {
                "min_tier": ReputationTier.EMERGING,
                "min_reputation": 0.25,
                "description": "Create proposals affecting other federations",
            },
            "witness_service": {
                "min_tier": ReputationTier.ESTABLISHED,
                "min_reputation": 0.4,
                "description": "Provide witness services to others",
            },
            "governance_voting": {
                "min_tier": ReputationTier.ESTABLISHED,
                "min_reputation": 0.35,
                "description": "Vote on network-wide governance",
            },
            "federation_onboarding": {
                "min_tier": ReputationTier.TRUSTED,
                "min_reputation": 0.6,
                "description": "Sponsor new federations joining the network",
            },
            "protocol_changes": {
                "min_tier": ReputationTier.EXEMPLARY,
                "min_reputation": 0.8,
                "description": "Propose changes to core protocol",
            },
        }

        return requirements.get(action, {
            "error": f"Unknown action: {action}",
            "available_actions": list(requirements.keys()),
        })

    def check_reputation_permission(
        self,
        federation_id: str,
        action: str,
    ) -> Dict:
        """
        Check if a federation has sufficient reputation for an action.

        Returns permission status and gap analysis.
        """
        requirements = self.get_reputation_requirements(action)
        if "error" in requirements:
            return requirements

        score = self.calculate_reputation(federation_id)

        has_permission = (
            score.global_reputation >= requirements["min_reputation"] and
            self._tier_meets_requirement(score.tier, requirements["min_tier"])
        )

        reputation_gap = max(0, requirements["min_reputation"] - score.global_reputation)

        return {
            "federation_id": federation_id,
            "action": action,
            "has_permission": has_permission,
            "current_reputation": score.global_reputation,
            "current_tier": score.tier.value,
            "required_reputation": requirements["min_reputation"],
            "required_tier": requirements["min_tier"].value,
            "reputation_gap": reputation_gap,
            "description": requirements["description"],
            "suggestion": (
                None if has_permission
                else f"Need {reputation_gap:.2f} more reputation. Build trust with other federations."
            ),
        }

    def _tier_meets_requirement(
        self,
        actual: ReputationTier,
        required: ReputationTier,
    ) -> bool:
        """Check if actual tier meets or exceeds required tier."""
        tier_order = list(ReputationTier)
        return tier_order.index(actual) >= tier_order.index(required)


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Reputation Aggregation - Self Test")
    print("=" * 60)

    import tempfile

    tmp_dir = Path(tempfile.mkdtemp())

    # Create registries
    fed_registry = MultiFederationRegistry(db_path=tmp_dir / "federation.db")
    binding_registry = FederationBindingRegistry(
        db_path=tmp_dir / "binding.db",
        federation_db_path=tmp_dir / "fed_binding.db",
    )

    # Initialize aggregator
    aggregator = ReputationAggregator(fed_registry, binding_registry)

    # Register federations
    print("\n1. Register federations:")
    fed_registry.register_federation("fed:alpha", "Alpha Federation")
    fed_registry.register_federation("fed:beta", "Beta Federation")
    fed_registry.register_federation("fed:gamma", "Gamma Federation")
    fed_registry.register_federation("fed:delta", "Delta Federation")
    print("   Registered 4 federations")

    # Establish trust relationships
    print("\n2. Establish trust relationships:")
    from hardbound.multi_federation import FederationRelationship
    fed_registry.establish_trust("fed:alpha", "fed:beta", FederationRelationship.PEER, initial_trust=0.6)
    fed_registry.establish_trust("fed:alpha", "fed:gamma", FederationRelationship.PEER, initial_trust=0.5)
    fed_registry.establish_trust("fed:beta", "fed:alpha", FederationRelationship.PEER, initial_trust=0.7)
    fed_registry.establish_trust("fed:gamma", "fed:alpha", FederationRelationship.PEER, initial_trust=0.8)
    fed_registry.establish_trust("fed:delta", "fed:alpha", FederationRelationship.PEER, initial_trust=0.6)
    print("   Alpha receives trust from: beta (0.7), gamma (0.8), delta (0.6)")
    print("   Alpha gives trust to: beta (0.6), gamma (0.5)")

    # Setup binding for presence
    print("\n3. Setup binding registry:")
    binding_registry.register_federation_with_binding("fed:alpha", "Alpha", initial_trust=0.9)
    binding_registry.register_federation_with_binding("fed:beta", "Beta", initial_trust=0.8)
    for i in range(4):
        binding_registry.bind_team_to_federation("fed:alpha", f"team:alpha:{i}")
    for i in range(3):
        binding_registry.bind_team_to_federation("fed:beta", f"team:beta:{i}")
    binding_registry.build_internal_presence("fed:alpha")
    binding_registry.build_internal_presence("fed:beta")
    print("   Built presence for alpha and beta")

    # Calculate reputation
    print("\n4. Calculate reputation:")
    alpha_rep = aggregator.calculate_reputation("fed:alpha")
    print(f"   Alpha Reputation: {alpha_rep.global_reputation:.3f}")
    print(f"   Alpha Tier: {alpha_rep.tier.value}")
    print(f"   Incoming trust: {alpha_rep.incoming_trust_sum:.2f} from {alpha_rep.incoming_trust_count} sources")
    print(f"   Confidence: {alpha_rep.confidence:.2f}")

    beta_rep = aggregator.calculate_reputation("fed:beta")
    print(f"\n   Beta Reputation: {beta_rep.global_reputation:.3f}")
    print(f"   Beta Tier: {beta_rep.tier.value}")

    # Compare
    print("\n5. Compare reputations:")
    comparison = aggregator.compare_reputations("fed:alpha", "fed:beta")
    print(f"   Higher reputation: {comparison['higher_reputation']}")
    print(f"   Difference: {comparison['reputation_difference']:.3f}")

    # Get ranking
    print("\n6. Reputation ranking:")
    ranking = aggregator.get_reputation_ranking(limit=4)
    for i, score in enumerate(ranking, 1):
        print(f"   {i}. {score.federation_id}: {score.global_reputation:.3f} ({score.tier.value})")

    # Check permission
    print("\n7. Check reputation permissions:")
    permission = aggregator.check_reputation_permission("fed:alpha", "witness_service")
    print(f"   Can alpha provide witness service? {permission['has_permission']}")
    if not permission['has_permission']:
        print(f"   Gap: {permission['reputation_gap']:.2f}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
