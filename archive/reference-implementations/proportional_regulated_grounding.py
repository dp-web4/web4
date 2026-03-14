#!/usr/bin/env python3
"""
Proportional Regulated Grounding - Session 105 Track 3

Integrates proportional coherence regulation (Track 1) with grounding system
to create a complete proportional regulation pipeline.

This replaces binary threshold regulation (coherence_regulation.py) with
gradient-based proportional regulation (proportional_coherence_regulation.py)
for use in the grounding lifecycle.

Components Integrated:
1. ProportionalCoherenceRegulator (Track 1)
2. LCTGroundingRegistry (Session 104 Track 2)
3. Grounding lifecycle (announce, validate, expire)
4. ATP cost calculation with proportional CI

Author: Claude (Session 105 Track 3)
Date: 2025-12-29
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta

# Import components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from proportional_coherence_regulation import (
    ProportionalRegulationConfig,
    ProportionalCoherenceRegulator
)
from lct_grounding_registry import (
    LCTGroundingRegistry,
    GroundingRecord,
    IdentityCoherenceProfile
)
from mrh_rdf_implementation import GroundingEdge, GroundingContext
from coherence import coherence_index, CoherenceWeights
from trust_tensors import CIModulationConfig, adjusted_atp_cost


@dataclass
class ProportionalGroundingConfig:
    """
    Configuration for proportional regulated grounding

    Combines:
    - Proportional regulation parameters
    - ATP cost modulation parameters
    - Grounding registry parameters
    """
    # Proportional regulation
    regulation_config: ProportionalRegulationConfig = None

    # Coherence aggregation strategy
    aggregation_strategy: str = 'min-weighted-critical'  # Session 104 fix

    # ATP cost modulation
    atp_config: CIModulationConfig = None

    # Grounding registry
    grounding_ttl: timedelta = timedelta(hours=24)

    def __post_init__(self):
        """Initialize default configs if not provided"""
        if self.regulation_config is None:
            self.regulation_config = ProportionalRegulationConfig()

        if self.atp_config is None:
            self.atp_config = CIModulationConfig()


class ProportionalGroundingManager:
    """
    Grounding manager with proportional regulation

    Replaces binary threshold regulation with gradient-based proportional
    regulation. Provides:

    1. Proportional CI regulation (not binary thresholds)
    2. LCT identity tracking with coherence profiles
    3. ATP cost calculation based on regulated CI
    4. Grounding history and expiration

    Key Difference from RegulatedGroundingManager:
    - Uses ProportionalCoherenceRegulator (no attractors)
    - Continuous cascade severity (not binary detection)
    - Smooth regulation gradients
    """

    def __init__(self, config: Optional[ProportionalGroundingConfig] = None):
        """Initialize proportional grounding manager"""
        self.config = config or ProportionalGroundingConfig()

        # Components
        self.regulator = ProportionalCoherenceRegulator(self.config.regulation_config)
        self.registry = LCTGroundingRegistry(self.config.grounding_ttl)

        # Coherence weights (use Session 104 aggregation fix)
        self.coherence_weights = CoherenceWeights(
            aggregation_strategy=self.config.aggregation_strategy
        )

    def announce_grounding(
        self,
        lct_uri: str,
        entity_id: str,
        context: GroundingContext,
        mrh_graph,
        witness_set: Optional[List[str]] = None
    ) -> Tuple[object, float, Dict]:
        """
        Announce grounding with proportional regulation

        Args:
            lct_uri: Identity LCT URI
            entity_id: Entity identifier
            context: Current grounding context
            mrh_graph: MRH graph for coherence calculation
            witness_set: Optional witnesses

        Returns:
            (grounding_edge, regulated_ci, metadata)
        """
        from grounding_lifecycle import announce_grounding, GroundingTTLConfig

        # Get grounding history for this identity
        history = self.registry.get_history(lct_uri)
        historical_edges = [record.grounding for record in history]

        # Calculate raw coherence index
        raw_ci = coherence_index(
            context,
            historical_edges,
            mrh_graph,
            self.coherence_weights
        )

        # Extract CI history for cascade detection
        ci_history = [record.coherence_index for record in history]

        # Calculate time since last grounding
        time_since_last = None
        if history:
            last_grounding_time = datetime.fromisoformat(history[0].timestamp)
            current_time = datetime.now()
            time_since_last = current_time - last_grounding_time

        # Apply proportional regulation
        regulated_ci, regulation_metadata = self.regulator.regulate(
            raw_ci,
            time_since_last_grounding=time_since_last,
            ci_history=ci_history
        )

        # Create grounding edge using standard lifecycle
        grounding_edge = announce_grounding(entity_id, context, mrh_graph, GroundingTTLConfig(), witness_set)

        # Register grounding in LCT registry
        self.registry.register_grounding(
            lct_uri,
            grounding_edge,
            regulated_ci,
            regulation_metadata
        )

        # Return grounding with regulated CI and metadata
        return (grounding_edge, regulated_ci, regulation_metadata)

    def calculate_atp_cost(
        self,
        lct_uri: str,
        base_cost: float
    ) -> Tuple[float, Dict]:
        """
        Calculate ATP cost for identity based on coherence

        Args:
            lct_uri: Identity LCT URI
            base_cost: Base ATP cost for operation

        Returns:
            (adjusted_cost, metadata)
        """
        # Get current grounding
        current = self.registry.resolve(lct_uri)

        if not current:
            # No grounding = maximum penalty
            metadata = {
                'has_grounding': False,
                'ci': 0.0,
                'multiplier': self.config.atp_config.atp_max_multiplier,
                'reason': 'no_grounding'
            }
            adjusted = base_cost * self.config.atp_config.atp_max_multiplier
            return (adjusted, metadata)

        # Calculate ATP cost based on regulated CI
        ci = current.coherence_index
        adjusted = adjusted_atp_cost(base_cost, ci, self.config.atp_config)

        metadata = {
            'has_grounding': True,
            'ci': ci,
            'multiplier': adjusted / base_cost,
            'regulation_metadata': current.regulation_metadata,
            'grounding_age': datetime.now() - datetime.fromisoformat(current.timestamp)
        }

        return (adjusted, metadata)

    def get_identity_profile(self, lct_uri: str) -> Optional[IdentityCoherenceProfile]:
        """Get coherence profile for identity"""
        return self.registry.get_coherence_profile(lct_uri)

    def get_flagged_identities(self) -> List[Tuple[str, str]]:
        """Get list of flagged identities"""
        return self.registry.get_flagged_identities()

    def get_statistics(self) -> Dict:
        """Get registry statistics"""
        return self.registry.get_statistics()


# ============================================================================
# Integration Helpers
# ============================================================================

def create_proportional_grounding_system(
    regulation_target: float = 0.7,
    max_boost: float = 0.3,
    atp_max_multiplier: float = 10.0,
    grounding_ttl_hours: int = 24
) -> ProportionalGroundingManager:
    """
    Create a complete proportional grounding system with default configs

    Convenience function for standard deployments.

    Args:
        regulation_target: Target CI for proportional regulation
        max_boost: Maximum CI boost for low coherence
        atp_max_multiplier: Maximum ATP cost multiplier
        grounding_ttl_hours: Grounding TTL in hours

    Returns:
        Configured ProportionalGroundingManager
    """
    regulation_config = ProportionalRegulationConfig(
        target_ci=regulation_target,
        max_boost=max_boost
    )

    atp_config = CIModulationConfig(
        atp_max_multiplier=atp_max_multiplier
    )

    grounding_config = ProportionalGroundingConfig(
        regulation_config=regulation_config,
        atp_config=atp_config,
        grounding_ttl=timedelta(hours=grounding_ttl_hours)
    )

    return ProportionalGroundingManager(grounding_config)


def compare_binary_vs_proportional_systems(
    lct_uri: str,
    context: GroundingContext,
    grounding_edge: GroundingEdge,
    mrh_graph,
    base_atp_cost: float = 100.0
) -> Dict:
    """
    Compare binary threshold regulation vs proportional regulation

    Useful for migration analysis and A/B testing.

    Args:
        lct_uri: Identity LCT URI
        context: Grounding context
        grounding_edge: Grounding edge
        mrh_graph: MRH graph
        base_atp_cost: Base ATP cost

    Returns:
        Comparison statistics
    """
    from regulated_grounding_manager import RegulatedGroundingManager
    from coherence_regulation import CoherenceRegulationConfig

    # Binary system (old)
    binary_config = CoherenceRegulationConfig()
    binary_manager = RegulatedGroundingManager(binary_config)

    # Proportional system (new)
    proportional_manager = create_proportional_grounding_system()

    # Announce in both systems
    binary_edge, binary_ci, binary_meta = binary_manager.announce(
        context,
        grounding_edge=grounding_edge
    )

    prop_edge, prop_ci, prop_meta = proportional_manager.announce_grounding(
        lct_uri,
        context,
        grounding_edge,
        mrh_graph
    )

    # Calculate ATP costs
    binary_atp = adjusted_atp_cost(base_atp_cost, binary_ci)
    prop_atp, prop_atp_meta = proportional_manager.calculate_atp_cost(lct_uri, base_atp_cost)

    return {
        'binary': {
            'ci': binary_ci,
            'atp_cost': binary_atp,
            'atp_multiplier': binary_atp / base_atp_cost,
            'regulations': binary_meta.get('regulations_applied', [])
        },
        'proportional': {
            'ci': prop_ci,
            'atp_cost': prop_atp,
            'atp_multiplier': prop_atp / base_atp_cost,
            'regulations': prop_meta['regulations_applied']
        },
        'comparison': {
            'ci_delta': prop_ci - binary_ci,
            'atp_delta': prop_atp - binary_atp,
            'more_severe': prop_ci < binary_ci
        }
    }


if __name__ == "__main__":
    print("Proportional Regulated Grounding - Session 105 Track 3")
    print("="*70)
    print("\nIntegrates:")
    print("  1. Proportional coherence regulation (Track 1)")
    print("  2. LCT grounding registry (Session 104)")
    print("  3. ATP cost scaling")
    print("\nKey Benefits:")
    print("  - No threshold attractors (smooth gradients)")
    print("  - Continuous cascade detection (not binary)")
    print("  - Identity coherence tracking")
    print("  - Proportional ATP penalties")

    # Demo
    manager = create_proportional_grounding_system()
    print(f"\nManager initialized:")
    print(f"  Target CI: {manager.config.regulation_config.target_ci}")
    print(f"  Max boost: {manager.config.regulation_config.max_boost}")
    print(f"  ATP max multiplier: {manager.config.atp_config.atp_max_multiplier}x")
    print(f"  Grounding TTL: {manager.config.grounding_ttl}")

    stats = manager.get_statistics()
    print(f"\nRegistry statistics: {stats}")
