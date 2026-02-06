"""
Trust Integration Bridge: Hardbound Federation <-> web4-trust-core

This module bridges the Hardbound federation's reputation model with the
web4-trust-core Rust implementation, enabling:

1. Export federation teams as EntityTrust objects
2. Unified trust scoring across both systems
3. Cross-validation of reputation metrics

The mapping:
- witness_score -> T3 reliability
- success_rate -> T3 competence
- witness_count (normalized) -> T3 witnesses
- last_activity -> decay calculations

Track BE: Hardbound + Rust trust integration design
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import json

# Import web4-trust-core Rust backend
try:
    from web4_trust import EntityTrust, T3Tensor, TrustStore, create_memory_store
    RUST_BACKEND_AVAILABLE = True
except ImportError:
    RUST_BACKEND_AVAILABLE = False
    EntityTrust = None
    T3Tensor = None
    TrustStore = None


@dataclass
class TrustMapping:
    """Mapping between Hardbound and T3 trust metrics."""
    team_id: str
    hardbound_witness_score: float
    hardbound_success_rate: float
    hardbound_witness_count: int

    t3_competence: float
    t3_reliability: float
    t3_consistency: float
    t3_witnesses: float
    t3_lineage: float
    t3_alignment: float
    t3_average: float

    discrepancy: float  # Difference between hardbound and T3
    trust_level: str


class TrustIntegrationBridge:
    """
    Bridges Hardbound federation reputation with web4-trust-core.

    Enables cross-validation and unified trust scoring.
    """

    # Normalization constants
    MAX_WITNESS_COUNT = 1000  # For normalizing witness count to 0-1

    def __init__(self, federation_registry, trust_store: Optional["TrustStore"] = None):
        """
        Initialize the bridge.

        Args:
            federation_registry: FederationRegistry instance
            trust_store: Optional TrustStore (creates in-memory if not provided)
        """
        if not RUST_BACKEND_AVAILABLE:
            raise ImportError(
                "web4-trust-core not available. "
                "Install with: pip install web4-trust"
            )

        self.federation = federation_registry
        self.trust_store = trust_store or create_memory_store()

    def team_to_entity_id(self, team_id: str) -> str:
        """Convert Hardbound team_id to EntityTrust entity_id format."""
        # team:alpha -> federation:team:alpha
        return f"federation:{team_id}"

    def entity_id_to_team(self, entity_id: str) -> str:
        """Convert EntityTrust entity_id back to Hardbound team_id."""
        # federation:team:alpha -> team:alpha
        if entity_id.startswith("federation:"):
            return entity_id[len("federation:"):]
        return entity_id

    def export_team_to_entity(self, team_id: str) -> "EntityTrust":
        """
        Export a Hardbound team as an EntityTrust object.

        Maps Hardbound metrics to T3/V3 dimensions:
        - witness_score -> reliability (how reliable are their witnesses)
        - success_rate -> competence (how accurate are they)
        - witness_count -> witnesses (normalized by max count)
        - last_activity -> decay factor

        Args:
            team_id: Hardbound team ID

        Returns:
            EntityTrust object with mapped values
        """
        team = self.federation.get_team(team_id)
        if not team:
            raise ValueError(f"Team not found: {team_id}")

        entity_id = self.team_to_entity_id(team_id)
        entity = EntityTrust(entity_id)

        # Calculate success rate
        total = team.witness_successes + team.witness_failures
        success_rate = team.witness_successes / total if total > 0 else 0.5

        # Normalize witness count
        normalized_witnesses = min(team.witness_count / self.MAX_WITNESS_COUNT, 1.0)

        # Map to T3 updates
        # Each dimension update uses magnitude to move toward target

        # Competence: based on success rate
        for _ in range(max(1, total)):
            entity.update_from_outcome(success_rate > 0.5, success_rate * 0.1)

        # Reliability: use witness_score directly
        # Simulate outcomes that would produce this score
        if team.witness_score > 0.5:
            for _ in range(int(team.witness_score * 10)):
                entity.update_from_outcome(True, 0.05)
        else:
            for _ in range(int((1 - team.witness_score) * 10)):
                entity.update_from_outcome(False, 0.05)

        return entity

    def export_all_teams(self) -> Dict[str, "EntityTrust"]:
        """
        Export all active teams as EntityTrust objects.

        Returns:
            Dict mapping team_id to EntityTrust
        """
        entities = {}
        teams = self.federation.find_teams(limit=1000)

        for team in teams:
            try:
                entity = self.export_team_to_entity(team.team_id)
                entities[team.team_id] = entity
            except Exception as e:
                # Skip problematic teams
                pass

        return entities

    def compare_trust_scores(self, team_id: str) -> TrustMapping:
        """
        Compare Hardbound and T3 trust scores for a team.

        Returns:
            TrustMapping with both scores and discrepancy
        """
        team = self.federation.get_team(team_id)
        if not team:
            raise ValueError(f"Team not found: {team_id}")

        entity = self.export_team_to_entity(team_id)

        # Calculate Hardbound success rate
        total = team.witness_successes + team.witness_failures
        hardbound_success_rate = team.witness_successes / total if total > 0 else 0.5

        # Get T3 dimensions
        t3_avg = entity.t3_average()

        # Calculate discrepancy
        # Compare Hardbound witness_score with T3 average
        discrepancy = abs(team.witness_score - t3_avg)

        return TrustMapping(
            team_id=team_id,
            hardbound_witness_score=team.witness_score,
            hardbound_success_rate=hardbound_success_rate,
            hardbound_witness_count=team.witness_count,
            t3_competence=entity.competence,
            t3_reliability=entity.reliability,
            t3_consistency=entity.consistency,
            t3_witnesses=entity.witnesses,
            t3_lineage=entity.lineage,
            t3_alignment=entity.alignment,
            t3_average=t3_avg,
            discrepancy=discrepancy,
            trust_level=entity.trust_level(),
        )

    def get_unified_trust_report(self) -> Dict:
        """
        Generate unified trust report across both systems.

        Returns:
            Comprehensive trust report with cross-validation
        """
        teams = self.federation.find_teams(limit=100)

        mappings = []
        total_discrepancy = 0.0
        high_discrepancy_teams = []

        for team in teams:
            try:
                mapping = self.compare_trust_scores(team.team_id)
                mappings.append(mapping)
                total_discrepancy += mapping.discrepancy

                if mapping.discrepancy > 0.2:
                    high_discrepancy_teams.append({
                        "team_id": mapping.team_id,
                        "hardbound_score": mapping.hardbound_witness_score,
                        "t3_average": mapping.t3_average,
                        "discrepancy": mapping.discrepancy,
                    })
            except Exception:
                pass

        avg_discrepancy = total_discrepancy / len(mappings) if mappings else 0.0

        # Aggregate T3 stats
        if mappings:
            avg_t3 = sum(m.t3_average for m in mappings) / len(mappings)
            avg_hardbound = sum(m.hardbound_witness_score for m in mappings) / len(mappings)
        else:
            avg_t3 = 0.5
            avg_hardbound = 0.5

        # Determine calibration status
        if avg_discrepancy < 0.1:
            calibration = "excellent"
        elif avg_discrepancy < 0.2:
            calibration = "good"
        elif avg_discrepancy < 0.3:
            calibration = "fair"
        else:
            calibration = "poor"

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "teams_analyzed": len(mappings),
            "average_hardbound_score": round(avg_hardbound, 4),
            "average_t3_score": round(avg_t3, 4),
            "average_discrepancy": round(avg_discrepancy, 4),
            "calibration": calibration,
            "high_discrepancy_teams": high_discrepancy_teams,
            "mappings": [
                {
                    "team_id": m.team_id,
                    "hardbound": round(m.hardbound_witness_score, 3),
                    "t3": round(m.t3_average, 3),
                    "discrepancy": round(m.discrepancy, 3),
                    "trust_level": m.trust_level,
                }
                for m in mappings[:10]  # Top 10 for summary
            ],
        }

    def sync_entity_to_team(self, entity_id: str) -> bool:
        """
        Sync EntityTrust updates back to Hardbound team.

        This allows external trust updates to flow into the federation.

        Args:
            entity_id: EntityTrust entity ID

        Returns:
            True if sync successful
        """
        team_id = self.entity_id_to_team(entity_id)
        team = self.federation.get_team(team_id)

        if not team:
            return False

        # Get entity from store
        entity = self.trust_store.get(entity_id)

        # Map T3 average back to witness_score
        # Use a weighted average that respects both systems
        t3_avg = entity.t3_average()
        blended_score = (team.witness_score * 0.7) + (t3_avg * 0.3)

        # Update Hardbound (requires direct DB access)
        # This is a one-way sync for now
        self.federation._update_witness_score(team_id, blended_score)

        return True


def create_integration_bridge(federation_registry) -> TrustIntegrationBridge:
    """
    Factory function to create a TrustIntegrationBridge.

    Args:
        federation_registry: FederationRegistry instance

    Returns:
        TrustIntegrationBridge instance
    """
    return TrustIntegrationBridge(federation_registry)


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Trust Integration Bridge - Self Test")
    print("=" * 60)

    if not RUST_BACKEND_AVAILABLE:
        print("ERROR: web4-trust-core not available")
        exit(1)

    # Import federation
    from .federation import FederationRegistry
    import tempfile
    from pathlib import Path

    # Create test federation
    db_path = Path(tempfile.mkdtemp()) / "test_integration.db"
    fed = FederationRegistry(db_path=db_path)

    # Register teams
    fed.register_team("team:alpha", "Alpha Corp")
    fed.register_team("team:beta", "Beta Labs")
    fed.register_team("team:gamma", "Gamma Gov")

    # Simulate some witness events
    fed.record_witness_event("team:alpha", "team:beta", "alpha:member", "msig:001")
    fed.record_witness_event("team:beta", "team:alpha", "beta:member", "msig:002")

    # Create bridge
    bridge = TrustIntegrationBridge(fed)

    # Export team to entity
    entity = bridge.export_team_to_entity("team:alpha")
    print(f"\nExported team:alpha -> {entity.entity_id}")
    print(f"  T3 average: {entity.t3_average():.4f}")
    print(f"  Trust level: {entity.trust_level()}")

    # Compare scores
    mapping = bridge.compare_trust_scores("team:alpha")
    print(f"\nScore comparison for {mapping.team_id}:")
    print(f"  Hardbound witness_score: {mapping.hardbound_witness_score:.4f}")
    print(f"  T3 average: {mapping.t3_average:.4f}")
    print(f"  Discrepancy: {mapping.discrepancy:.4f}")

    # Generate unified report
    report = bridge.get_unified_trust_report()
    print(f"\nUnified Trust Report:")
    print(f"  Teams analyzed: {report['teams_analyzed']}")
    print(f"  Avg Hardbound: {report['average_hardbound_score']:.4f}")
    print(f"  Avg T3: {report['average_t3_score']:.4f}")
    print(f"  Calibration: {report['calibration']}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
