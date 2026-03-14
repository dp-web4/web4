#!/usr/bin/env python3
"""
LCT Grounding Registry - Session 104 Track 2

Integrates LCT identity with grounding system to provide:
1. LCT URI → Current Grounding resolution
2. Grounding history tracking per LCT identity
3. Coherence-aware registry (low CI = flagged identity)
4. Authorization query support
5. Reputation lookup integration

This bridges LCT identity (Session 74) with grounding (Sessions 102-104)
to enable coherence-based trust decisions.

Author: Claude (Session 104 Track 2)
Date: 2025-12-29
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

# Import grounding types
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from mrh_rdf_implementation import GroundingEdge, GroundingContext
from coherence import coherence_index, CoherenceWeights
from regulated_grounding_manager import RegulatedGroundingManager


@dataclass
class GroundingRecord:
    """
    Record of a grounding for an LCT identity

    Tracks grounding edge, coherence index, and regulation metadata.
    """
    lct_uri: str  # Identity LCT URI
    grounding: GroundingEdge  # Grounding edge
    coherence_index: float  # CI at time of grounding
    regulation_metadata: Dict  # Regulation interventions applied
    timestamp: str  # ISO8601

    def is_expired(self, ttl: timedelta) -> bool:
        """Check if grounding has expired"""
        grounding_time = datetime.fromisoformat(self.timestamp)
        return datetime.now() - grounding_time > ttl


@dataclass
class IdentityCoherenceProfile:
    """
    Coherence profile for an LCT identity

    Tracks coherence history and flags for anomalies.
    """
    lct_uri: str
    grounding_count: int = 0
    avg_coherence: float = 0.0
    min_coherence: float = 1.0
    max_coherence: float = 0.0
    cascade_count: int = 0  # Number of cascade detections
    regulation_intervention_count: int = 0
    flagged: bool = False  # True if suspicious activity detected
    flag_reason: Optional[str] = None

    def update(self, ci: float, regulation_metadata: Dict):
        """Update profile with new grounding"""
        self.grounding_count += 1

        # Update CI statistics
        self.avg_coherence = (
            (self.avg_coherence * (self.grounding_count - 1) + ci) /
            self.grounding_count
        )
        self.min_coherence = min(self.min_coherence, ci)
        self.max_coherence = max(self.max_coherence, ci)

        # Track regulation
        if regulation_metadata.get('cascades_detected', 0) > 0:
            self.cascade_count += 1

        if regulation_metadata.get('regulations_applied', 0) > 0:
            self.regulation_intervention_count += regulation_metadata['regulations_applied']

        # Flag suspicious patterns
        if self.min_coherence < 0.15 and self.cascade_count > 5:
            self.flagged = True
            self.flag_reason = "Repeated low coherence and cascades (possible spoofing)"

        if self.regulation_intervention_count > 50:
            self.flagged = True
            self.flag_reason = "Excessive regulation interventions (unstable grounding)"


class LCTGroundingRegistry:
    """
    Registry mapping LCT URIs to current groundings

    Provides:
    - Resolution: LCT URI → Current Grounding
    - History: LCT URI → Grounding History
    - Coherence Profiles: LCT URI → Coherence Statistics
    - Flags: Identify suspicious identities
    """

    def __init__(self, grounding_ttl: timedelta = timedelta(hours=24)):
        """
        Initialize registry

        Args:
            grounding_ttl: How long groundings are valid
        """
        self.grounding_ttl = grounding_ttl

        # Current groundings (most recent)
        self.current_groundings: Dict[str, GroundingRecord] = {}

        # Historical groundings (last N per identity)
        self.grounding_history: Dict[str, List[GroundingRecord]] = {}
        self.history_limit = 100  # Keep last 100 groundings per identity

        # Coherence profiles
        self.coherence_profiles: Dict[str, IdentityCoherenceProfile] = {}

    def register_grounding(
        self,
        lct_uri: str,
        grounding: GroundingEdge,
        coherence_index: float,
        regulation_metadata: Dict
    ):
        """
        Register a grounding for an LCT identity

        Args:
            lct_uri: Identity LCT URI
            grounding: Grounding edge
            coherence_index: CI at time of grounding
            regulation_metadata: Regulation metadata
        """
        record = GroundingRecord(
            lct_uri=lct_uri,
            grounding=grounding,
            coherence_index=coherence_index,
            regulation_metadata=regulation_metadata,
            timestamp=grounding.timestamp
        )

        # Update current grounding
        self.current_groundings[lct_uri] = record

        # Update history
        if lct_uri not in self.grounding_history:
            self.grounding_history[lct_uri] = []

        self.grounding_history[lct_uri].append(record)

        # Trim history
        if len(self.grounding_history[lct_uri]) > self.history_limit:
            self.grounding_history[lct_uri] = self.grounding_history[lct_uri][-self.history_limit:]

        # Update coherence profile
        if lct_uri not in self.coherence_profiles:
            self.coherence_profiles[lct_uri] = IdentityCoherenceProfile(lct_uri)

        self.coherence_profiles[lct_uri].update(coherence_index, regulation_metadata)

    def resolve(self, lct_uri: str) -> Optional[GroundingRecord]:
        """
        Resolve LCT URI to current grounding

        Returns None if no grounding or expired.
        """
        if lct_uri not in self.current_groundings:
            return None

        record = self.current_groundings[lct_uri]

        # Check expiration
        if record.is_expired(self.grounding_ttl):
            # Expired, remove
            del self.current_groundings[lct_uri]
            return None

        return record

    def get_history(self, lct_uri: str, limit: Optional[int] = None) -> List[GroundingRecord]:
        """
        Get grounding history for an identity

        Args:
            lct_uri: Identity LCT URI
            limit: Optional limit on number of records

        Returns:
            List of GroundingRecords (most recent first)
        """
        if lct_uri not in self.grounding_history:
            return []

        history = list(reversed(self.grounding_history[lct_uri]))

        if limit:
            return history[:limit]

        return history

    def get_coherence_profile(self, lct_uri: str) -> Optional[IdentityCoherenceProfile]:
        """Get coherence profile for an identity"""
        return self.coherence_profiles.get(lct_uri)

    def get_flagged_identities(self) -> List[Tuple[str, str]]:
        """
        Get list of flagged identities

        Returns:
            List of (lct_uri, flag_reason) tuples
        """
        return [
            (uri, profile.flag_reason)
            for uri, profile in self.coherence_profiles.items()
            if profile.flagged
        ]

    def get_statistics(self) -> Dict:
        """Get registry statistics"""
        return {
            'total_identities': len(self.coherence_profiles),
            'active_groundings': len(self.current_groundings),
            'flagged_identities': len([p for p in self.coherence_profiles.values() if p.flagged]),
            'avg_coherence': sum(p.avg_coherence for p in self.coherence_profiles.values()) / max(len(self.coherence_profiles), 1),
            'total_groundings': sum(len(h) for h in self.grounding_history.values())
        }

    def export_profile(self, lct_uri: str) -> Optional[Dict]:
        """Export coherence profile as dict"""
        profile = self.get_coherence_profile(lct_uri)
        if not profile:
            return None

        return {
            'lct_uri': profile.lct_uri,
            'grounding_count': profile.grounding_count,
            'avg_coherence': profile.avg_coherence,
            'min_coherence': profile.min_coherence,
            'max_coherence': profile.max_coherence,
            'cascade_count': profile.cascade_count,
            'regulation_intervention_count': profile.regulation_intervention_count,
            'flagged': profile.flagged,
            'flag_reason': profile.flag_reason
        }


# ============================================================================
# Integration Helper
# ============================================================================

def create_grounding_with_registry(
    lct_uri: str,
    grounding_manager: RegulatedGroundingManager,
    context: GroundingContext,
    registry: LCTGroundingRegistry,
    witness_set: Optional[List[str]] = None
) -> Tuple[GroundingEdge, float, Dict]:
    """
    Create grounding and register in LCT registry

    Convenience function that:
    1. Announces grounding via manager
    2. Registers in LCT registry
    3. Returns grounding, CI, and metadata

    Args:
        lct_uri: Identity LCT URI
        grounding_manager: Regulated grounding manager
        context: Grounding context
        registry: LCT grounding registry
        witness_set: Optional witnesses

    Returns:
        (grounding_edge, coherence_index, regulation_metadata)
    """
    # Announce grounding
    grounding, ci, metadata = grounding_manager.announce(context, witness_set)

    # Register in LCT registry
    registry.register_grounding(lct_uri, grounding, ci, metadata)

    return (grounding, ci, metadata)


if __name__ == "__main__":
    # Demo
    print("LCT Grounding Registry Demo")
    print("="*60)

    registry = LCTGroundingRegistry()

    print(f"\nRegistry initialized with TTL: {registry.grounding_ttl}")
    print(f"Statistics: {registry.get_statistics()}")

    print("\nRegistry ready for grounding registration.")
    print("Use create_grounding_with_registry() to register groundings.")
