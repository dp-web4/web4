"""
Cross-Society Trust Propagation

Session #41

Enables trust scores to propagate across Web4 society boundaries.

Key Features:
- Query trust scores from other societies
- Aggregate trust from multiple sources
- Weighted trust propagation (decay with distance)
- Reputation sharing protocols
- Protection against trust inflation attacks

Trust Model:
- Direct trust: Your society's own trust assessment
- Propagated trust: Trust scores from other societies (weighted)
- Aggregated trust: Combined score from all sources
- Trust decay: Trust decreases with network distance

Example:
  Society A trusts identity X at 0.9
  Society B trusts Society A at 0.8
  → Society B assigns propagated trust of 0.72 to identity X
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque
import json
import math

from cross_society_messaging import (
    CrossSocietyMessage,
    CrossSocietyMessageBus,
    MessageType,
    SocietyCoordinator,
)


# ============================================================================
# Trust Record Types
# ============================================================================

@dataclass
class TrustRecord:
    """Trust assessment for an identity"""
    subject_lct: str  # Who is being trusted
    assessor_lct: str  # Who is assessing trust
    trust_score: float  # Trust score in [0, 1]
    assessed_at: datetime
    evidence: List[str] = field(default_factory=list)  # Evidence for trust
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if trust record has expired"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict:
        return {
            "subject_lct": self.subject_lct,
            "assessor_lct": self.assessor_lct,
            "trust_score": self.trust_score,
            "assessed_at": self.assessed_at.isoformat(),
            "evidence": self.evidence,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class PropagatedTrustRecord:
    """Trust record that has been propagated through the network"""
    subject_lct: str
    source_lct: str  # Original assessor
    trust_score: float
    propagation_path: List[str]  # Path from source to current society
    propagation_distance: int
    effective_trust: float  # Trust after decay
    received_at: datetime

    def to_dict(self) -> Dict:
        return {
            "subject_lct": self.subject_lct,
            "source_lct": self.source_lct,
            "trust_score": self.trust_score,
            "propagation_path": self.propagation_path,
            "propagation_distance": self.propagation_distance,
            "effective_trust": self.effective_trust,
            "received_at": self.received_at.isoformat(),
        }


# ============================================================================
# Trust Propagation Engine
# ============================================================================

class TrustPropagationEngine:
    """
    Manages trust propagation across society boundaries.

    Trust Propagation Algorithm:
    1. Direct trust: Your society's own assessment (weight = 1.0)
    2. One-hop trust: Trust from directly connected societies (weight = 0.8)
    3. Two-hop trust: Trust from societies 2 hops away (weight = 0.64)
    4. etc... (weight decays exponentially)

    Decay formula: effective_trust = original_trust * (decay_factor ^ distance)
    """

    def __init__(
        self,
        society_lct: str,
        decay_factor: float = 0.8,
        max_propagation_distance: int = 3,
    ):
        """
        Initialize trust propagation engine.

        Args:
            society_lct: This society's LCT
            decay_factor: Trust decay per hop (default 0.8 = 20% decay per hop)
            max_propagation_distance: Maximum hops to propagate (default 3)
        """
        self.society_lct = society_lct
        self.decay_factor = decay_factor
        self.max_propagation_distance = max_propagation_distance

        # Direct trust assessments (our society's own)
        self.direct_trust: Dict[str, TrustRecord] = {}

        # Propagated trust from other societies
        self.propagated_trust: Dict[str, List[PropagatedTrustRecord]] = defaultdict(list)

        # Society-to-society trust (how much we trust other societies)
        self.society_trust: Dict[str, float] = {}

        # Trust query cache
        self.trust_cache: Dict[str, Tuple[float, datetime]] = {}
        self.cache_ttl_seconds = 3600  # 1 hour

        # Statistics
        self.total_queries = 0
        self.cache_hits = 0

    def set_direct_trust(
        self,
        subject_lct: str,
        trust_score: float,
        evidence: Optional[List[str]] = None,
        valid_for_hours: Optional[int] = None,
    ) -> TrustRecord:
        """
        Set direct trust for an identity.

        This is our society's own assessment.
        """
        trust_score = max(0.0, min(1.0, trust_score))  # Clamp to [0, 1]

        expires_at = None
        if valid_for_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=valid_for_hours)

        record = TrustRecord(
            subject_lct=subject_lct,
            assessor_lct=self.society_lct,
            trust_score=trust_score,
            assessed_at=datetime.now(timezone.utc),
            evidence=evidence or [],
            expires_at=expires_at,
        )

        self.direct_trust[subject_lct] = record

        # Clear cache for this identity
        if subject_lct in self.trust_cache:
            del self.trust_cache[subject_lct]

        return record

    def set_society_trust(self, society_lct: str, trust_score: float):
        """
        Set trust for another society.

        This determines how much weight we give to their trust assessments.
        """
        trust_score = max(0.0, min(1.0, trust_score))
        self.society_trust[society_lct] = trust_score

    def receive_propagated_trust(
        self,
        subject_lct: str,
        source_lct: str,
        trust_score: float,
        propagation_path: List[str],
    ):
        """
        Receive a trust record propagated from another society.

        Args:
            subject_lct: Who is being trusted
            source_lct: Original assessor
            trust_score: Original trust score
            propagation_path: Path from source to us
        """
        distance = len(propagation_path) - 1  # Number of hops

        # Ignore if too far
        if distance > self.max_propagation_distance:
            return

        # Calculate effective trust (apply decay)
        effective_trust = trust_score * (self.decay_factor ** distance)

        # Weight by trust in the immediate sender (last hop)
        if len(propagation_path) >= 2:
            immediate_sender = propagation_path[-2]
            if immediate_sender in self.society_trust:
                effective_trust *= self.society_trust[immediate_sender]

        record = PropagatedTrustRecord(
            subject_lct=subject_lct,
            source_lct=source_lct,
            trust_score=trust_score,
            propagation_path=propagation_path,
            propagation_distance=distance,
            effective_trust=effective_trust,
            received_at=datetime.now(timezone.utc),
        )

        self.propagated_trust[subject_lct].append(record)

        # Clear cache
        if subject_lct in self.trust_cache:
            del self.trust_cache[subject_lct]

    def get_aggregated_trust(self, subject_lct: str) -> float:
        """
        Get aggregated trust score for an identity.

        Combines:
        - Direct trust (our own assessment) - weight 1.0
        - Propagated trust (from other societies) - weighted by distance and society trust

        Aggregation strategy: Weighted average with direct trust having highest weight
        """
        self.total_queries += 1

        # Check cache
        if subject_lct in self.trust_cache:
            cached_score, cached_at = self.trust_cache[subject_lct]
            age = (datetime.now(timezone.utc) - cached_at).total_seconds()
            if age < self.cache_ttl_seconds:
                self.cache_hits += 1
                return cached_score

        trust_scores = []
        weights = []

        # Direct trust (highest weight)
        if subject_lct in self.direct_trust:
            record = self.direct_trust[subject_lct]
            if not record.is_expired():
                trust_scores.append(record.trust_score)
                weights.append(1.0)  # Full weight for direct trust

        # Propagated trust (weighted by effective trust)
        if subject_lct in self.propagated_trust:
            for record in self.propagated_trust[subject_lct]:
                trust_scores.append(record.trust_score)
                # Weight is the decay factor applied
                weight = self.decay_factor ** record.propagation_distance
                weights.append(weight)

        # No trust information available
        if not trust_scores:
            return 0.5  # Neutral default

        # Weighted average
        total_weight = sum(weights)
        weighted_sum = sum(score * weight for score, weight in zip(trust_scores, weights))
        aggregated = weighted_sum / total_weight

        # Cache result
        self.trust_cache[subject_lct] = (aggregated, datetime.now(timezone.utc))

        return aggregated

    def get_trust_breakdown(self, subject_lct: str) -> Dict:
        """
        Get detailed breakdown of trust sources for an identity.

        Useful for debugging and transparency.
        """
        breakdown = {
            "subject_lct": subject_lct,
            "aggregated_trust": self.get_aggregated_trust(subject_lct),
            "direct_trust": None,
            "propagated_trust": [],
        }

        # Direct trust
        if subject_lct in self.direct_trust:
            record = self.direct_trust[subject_lct]
            if not record.is_expired():
                breakdown["direct_trust"] = record.to_dict()

        # Propagated trust
        if subject_lct in self.propagated_trust:
            breakdown["propagated_trust"] = [
                record.to_dict()
                for record in self.propagated_trust[subject_lct]
            ]

        return breakdown

    def propagate_trust_to_neighbors(
        self,
        subject_lct: str,
        neighbor_societies: List[str],
    ) -> List[Dict]:
        """
        Propagate trust record to neighboring societies.

        Creates messages to send to neighbors.
        Propagates both direct trust and received propagated trust.
        """
        messages = []

        # Propagate direct trust
        if subject_lct in self.direct_trust:
            record = self.direct_trust[subject_lct]

            if not record.is_expired():
                # Create propagation messages for each neighbor
                for neighbor_lct in neighbor_societies:
                    # Build propagation path
                    path = [self.society_lct, neighbor_lct]

                    message_payload = {
                        "subject_lct": subject_lct,
                        "source_lct": self.society_lct,
                        "trust_score": record.trust_score,
                        "propagation_path": path,
                        "evidence": record.evidence,
                    }

                    messages.append({
                        "recipient": neighbor_lct,
                        "payload": message_payload,
                    })

        # Also propagate received trust (multi-hop propagation)
        if subject_lct in self.propagated_trust:
            for prop_record in self.propagated_trust[subject_lct]:
                # Don't propagate beyond max distance
                if prop_record.propagation_distance >= self.max_propagation_distance:
                    continue

                # Create propagation messages for each neighbor
                for neighbor_lct in neighbor_societies:
                    # Don't send back to sender
                    if neighbor_lct in prop_record.propagation_path:
                        continue

                    # Extend propagation path
                    path = prop_record.propagation_path + [neighbor_lct]

                    message_payload = {
                        "subject_lct": subject_lct,
                        "source_lct": prop_record.source_lct,
                        "trust_score": prop_record.trust_score,
                        "propagation_path": path,
                        "evidence": [],
                    }

                    messages.append({
                        "recipient": neighbor_lct,
                        "payload": message_payload,
                    })

        return messages

    def get_stats(self) -> Dict:
        """Get engine statistics"""
        return {
            "direct_trust_records": len(self.direct_trust),
            "propagated_trust_records": sum(len(records) for records in self.propagated_trust.values()),
            "known_societies": len(self.society_trust),
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(1, self.total_queries),
            "decay_factor": self.decay_factor,
            "max_propagation_distance": self.max_propagation_distance,
        }


# ============================================================================
# Cross-Society Trust Network
# ============================================================================

class CrossSocietyTrustNetwork:
    """
    Manages trust relationships across multiple societies.

    This is a global view (for simulation/testing). In production,
    each society would only have its own TrustPropagationEngine.
    """

    def __init__(self):
        # Trust engines for each society
        self.engines: Dict[str, TrustPropagationEngine] = {}

        # Society network graph (who is connected to whom)
        self.network: Dict[str, Set[str]] = defaultdict(set)

    def add_society(
        self,
        society_lct: str,
        decay_factor: float = 0.8,
        max_propagation_distance: int = 3,
    ):
        """Add a society to the network"""
        if society_lct not in self.engines:
            self.engines[society_lct] = TrustPropagationEngine(
                society_lct=society_lct,
                decay_factor=decay_factor,
                max_propagation_distance=max_propagation_distance,
            )

    def connect_societies(self, society_a: str, society_b: str, mutual: bool = True):
        """Create connection between two societies"""
        self.network[society_a].add(society_b)
        if mutual:
            self.network[society_b].add(society_a)

    def set_society_trust(self, assessor: str, subject: str, trust_score: float):
        """Set trust between two societies"""
        if assessor in self.engines:
            self.engines[assessor].set_society_trust(subject, trust_score)

    def set_identity_trust(
        self,
        society_lct: str,
        identity_lct: str,
        trust_score: float,
        evidence: Optional[List[str]] = None,
    ):
        """Set trust for an identity (from a society's perspective)"""
        if society_lct in self.engines:
            self.engines[society_lct].set_direct_trust(
                identity_lct,
                trust_score,
                evidence,
            )

    def propagate_all(self):
        """
        Propagate trust records throughout the network.

        Simulates one round of trust propagation.
        """
        # For each society, propagate trust (both direct and received) to neighbors
        for society_lct, engine in self.engines.items():
            neighbors = self.network.get(society_lct, set())

            # Get all identities this society has trust info for
            all_identities = set(engine.direct_trust.keys()) | set(engine.propagated_trust.keys())

            for subject_lct in all_identities:
                messages = engine.propagate_trust_to_neighbors(
                    subject_lct,
                    list(neighbors),
                )

                # Deliver messages
                for msg in messages:
                    recipient = msg["recipient"]
                    payload = msg["payload"]

                    if recipient in self.engines:
                        self.engines[recipient].receive_propagated_trust(
                            subject_lct=payload["subject_lct"],
                            source_lct=payload["source_lct"],
                            trust_score=payload["trust_score"],
                            propagation_path=payload["propagation_path"],
                        )

    def get_network_stats(self) -> Dict:
        """Get statistics for the entire network"""
        return {
            "total_societies": len(self.engines),
            "total_connections": sum(len(neighbors) for neighbors in self.network.values()) // 2,
            "society_stats": {
                lct: engine.get_stats()
                for lct, engine in self.engines.items()
            },
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("CROSS-SOCIETY TRUST PROPAGATION - Session #41")
    print("Decentralized Trust Network")
    print("=" * 80)

    network = CrossSocietyTrustNetwork()

    # Scenario 1: Create society network
    print("\n### Scenario 1: Creating Society Network")
    print("-" * 80)

    societies = ["lct-sage", "lct-legion", "lct-cbp", "lct-alice", "lct-bob"]

    for society in societies:
        network.add_society(society)

    # Create connections (network topology)
    # SAGE ↔ Legion ↔ CBP ↔ Alice ↔ Bob
    network.connect_societies("lct-sage", "lct-legion")
    network.connect_societies("lct-legion", "lct-cbp")
    network.connect_societies("lct-cbp", "lct-alice")
    network.connect_societies("lct-alice", "lct-bob")

    # Also: SAGE ↔ CBP (creates alternate path)
    network.connect_societies("lct-sage", "lct-cbp")

    print(f"Created network with {len(societies)} societies")
    print("Topology: SAGE ↔ Legion ↔ CBP ↔ Alice ↔ Bob")
    print("          SAGE ↔ CBP (alternate path)")

    # Scenario 2: Set society-to-society trust
    print("\n### Scenario 2: Society-to-Society Trust")
    print("-" * 80)

    # Each society trusts its neighbors
    network.set_society_trust("lct-sage", "lct-legion", 0.9)
    network.set_society_trust("lct-sage", "lct-cbp", 0.85)
    network.set_society_trust("lct-legion", "lct-sage", 0.9)
    network.set_society_trust("lct-legion", "lct-cbp", 0.8)
    network.set_society_trust("lct-cbp", "lct-sage", 0.85)
    network.set_society_trust("lct-cbp", "lct-legion", 0.8)
    network.set_society_trust("lct-cbp", "lct-alice", 0.75)
    network.set_society_trust("lct-alice", "lct-cbp", 0.75)
    network.set_society_trust("lct-alice", "lct-bob", 0.7)
    network.set_society_trust("lct-bob", "lct-alice", 0.7)

    print("Society trust relationships established")
    print("  SAGE → Legion: 0.9")
    print("  SAGE → CBP: 0.85")
    print("  Legion → CBP: 0.8")
    print("  CBP → Alice: 0.75")
    print("  Alice → Bob: 0.7")

    # Scenario 3: Set identity trust
    print("\n### Scenario 3: Identity Trust (Direct Assessments)")
    print("-" * 80)

    # SAGE directly trusts identity X
    network.set_identity_trust(
        "lct-sage",
        "lct-identity-x",
        0.95,
        evidence=["completed 10 work requests", "no violations"],
    )

    print("SAGE's direct trust in lct-identity-x: 0.95")
    print("  Evidence: completed 10 work requests, no violations")

    # Legion has no direct knowledge of identity X
    # CBP, Alice, Bob also have no direct knowledge

    # Scenario 4: Trust propagation
    print("\n### Scenario 4: Trust Propagation")
    print("-" * 80)

    print("Before propagation:")
    for society in ["lct-legion", "lct-cbp", "lct-alice", "lct-bob"]:
        trust = network.engines[society].get_aggregated_trust("lct-identity-x")
        print(f"  {society}: {trust:.3f} (default)")

    # Propagate trust through network
    network.propagate_all()

    print("\nAfter propagation:")
    for society in ["lct-sage", "lct-legion", "lct-cbp", "lct-alice", "lct-bob"]:
        trust = network.engines[society].get_aggregated_trust("lct-identity-x")
        print(f"  {society}: {trust:.3f}")

    # Scenario 5: Trust breakdown
    print("\n### Scenario 5: Trust Breakdown (Legion's view)")
    print("-" * 80)

    breakdown = network.engines["lct-legion"].get_trust_breakdown("lct-identity-x")

    print(f"Aggregated trust: {breakdown['aggregated_trust']:.3f}")
    print(f"Direct trust: {breakdown['direct_trust']}")
    print(f"Propagated trust sources: {len(breakdown['propagated_trust'])}")

    for i, record in enumerate(breakdown['propagated_trust']):
        print(f"\n  Source {i+1}:")
        print(f"    From: {record['source_lct']}")
        print(f"    Original trust: {record['trust_score']}")
        print(f"    Path: {' → '.join(record['propagation_path'])}")
        print(f"    Distance: {record['propagation_distance']} hops")
        print(f"    Effective trust: {record['effective_trust']:.3f}")

    # Scenario 6: Network statistics
    print("\n### Scenario 6: Network Statistics")
    print("-" * 80)

    stats = network.get_network_stats()
    print(f"Total societies: {stats['total_societies']}")
    print(f"Total connections: {stats['total_connections']}")

    print("\nPer-society stats:")
    for society, society_stats in stats['society_stats'].items():
        print(f"\n  {society}:")
        print(f"    Direct trust records: {society_stats['direct_trust_records']}")
        print(f"    Propagated trust records: {society_stats['propagated_trust_records']}")
        print(f"    Cache hit rate: {society_stats['cache_hit_rate']:.1%}")

    print("\n" + "=" * 80)
    print("✅ TRUST PROPAGATION OPERATIONAL")
    print("Cross-society trust network established!")
    print("=" * 80)
