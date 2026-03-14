#!/usr/bin/env python3
"""
Regulated Grounding Manager - Integration of Coherence Regulation

Extends GroundingManager with integrated coherence regulation to prevent
cascade failures. Combines lifecycle management (Phase 4) with cascade
prevention (Session 102 Track 2).

Key Integration Points:
1. Maintains CI history for cascade detection
2. Applies regulation before CI-based decisions
3. Tracks regulation metadata for audit trail
4. Provides unified interface for regulated grounding

Motivation:
Session 102 identified that Web4 coherence system can cascade (low CI → high cost →
fewer operations → lower CI → lock-out). This integrated manager applies regulation
mechanisms (temporal decay, soft bounds, cascade detection, grace periods) directly
in the grounding lifecycle.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Import grounding lifecycle components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from mrh_rdf_implementation import GroundingEdge, GroundingContext, MRHGraph
from grounding_lifecycle import (
    GroundingTTLConfig, ContextChangeThresholds, GroundingStatus,
    announce_grounding, grounding_heartbeat, check_grounding_status,
    on_grounding_expired, validate_continuity_chain, GroundingManager
)
from coherence import coherence_index, CoherenceWeights
from coherence_regulation import CoherenceRegulationManager, CoherenceRegulationConfig


# ============================================================================
# Regulated Grounding Manager
# ============================================================================

class RegulatedGroundingManager(GroundingManager):
    """
    Grounding manager with integrated coherence regulation

    Extends base GroundingManager to apply regulation mechanisms:
    - Maintains CI history for cascade detection
    - Applies temporal decay to CI penalties
    - Detects and intervenes in coherence cascades
    - Provides grace periods for first coherence drops
    - Tracks regulation metadata for audit

    All lifecycle methods (announce, heartbeat, check_status) use
    regulated CI values to prevent cascade lock-out.
    """

    def __init__(
        self,
        entity_lct: str,
        mrh_graph: MRHGraph,
        grounding_config: Optional[GroundingTTLConfig] = None,
        context_thresholds: Optional[ContextChangeThresholds] = None,
        coherence_weights: Optional[CoherenceWeights] = None,
        regulation_config: Optional[CoherenceRegulationConfig] = None,
        enable_regulation: bool = True
    ):
        """
        Initialize regulated grounding manager

        Args:
            entity_lct: Entity LCT URI
            mrh_graph: MRH graph for relational coherence
            grounding_config: Grounding TTL configuration
            context_thresholds: Context change thresholds
            coherence_weights: Coherence calculation weights
            regulation_config: Regulation configuration
            enable_regulation: Enable/disable regulation (for testing)
        """
        super().__init__(entity_lct, mrh_graph, grounding_config, context_thresholds)

        self.coherence_weights = coherence_weights or CoherenceWeights()
        self.regulation_manager = CoherenceRegulationManager(regulation_config)
        self.enable_regulation = enable_regulation

        # Track CI history for regulation
        self.ci_history: List[Tuple[float, str]] = []  # (CI, timestamp) tuples
        self.regulation_metadata_history: List[Dict] = []
        self.last_coherence_issue_time: Optional[str] = None

    def calculate_raw_ci(self, grounding: GroundingEdge) -> float:
        """
        Calculate raw coherence index for a grounding

        Args:
            grounding: Grounding to calculate CI for

        Returns:
            Raw CI value (before regulation)
        """
        return coherence_index(
            grounding.target,
            self.grounding_history,
            self.mrh_graph,
            weights=self.coherence_weights
        )

    def calculate_regulated_ci(
        self,
        raw_ci: float,
        timestamp: str
    ) -> Tuple[float, Dict]:
        """
        Apply regulation to raw CI

        Args:
            raw_ci: Raw coherence index
            timestamp: ISO8601 timestamp

        Returns:
            (regulated_ci, regulation_metadata)
        """
        if not self.enable_regulation:
            return (raw_ci, {'raw_ci': raw_ci, 'regulations_applied': []})

        # Apply regulation
        regulated_ci, metadata = self.regulation_manager.regulate_coherence(
            self.entity_lct,
            raw_ci,
            ci_history=self.ci_history if self.ci_history else None,
            last_issue_time=self.last_coherence_issue_time
        )

        # Update last issue time if CI dropped
        if raw_ci < 0.8 and (not self.last_coherence_issue_time or timestamp > self.last_coherence_issue_time):
            self.last_coherence_issue_time = timestamp

        return (regulated_ci, metadata)

    def announce(
        self,
        context: GroundingContext,
        witness_set: Optional[List[str]] = None
    ) -> Tuple[GroundingEdge, float, Dict]:
        """
        Announce new grounding with CI tracking

        Args:
            context: Grounding context
            witness_set: Optional witnesses

        Returns:
            (grounding_edge, regulated_ci, regulation_metadata)
        """
        # Call parent announce
        grounding = super().announce(context, witness_set)

        # Calculate and regulate CI
        raw_ci = self.calculate_raw_ci(grounding)
        regulated_ci, reg_metadata = self.calculate_regulated_ci(raw_ci, grounding.timestamp)

        # Track CI history
        self.ci_history.append((regulated_ci, grounding.timestamp))
        self.regulation_metadata_history.append(reg_metadata)

        return (grounding, regulated_ci, reg_metadata)

    def heartbeat(
        self,
        current_context: GroundingContext
    ) -> Tuple[GroundingEdge, str, float, Dict]:
        """
        Perform heartbeat with CI regulation

        Args:
            current_context: Current grounding context

        Returns:
            (grounding_edge, action, regulated_ci, regulation_metadata)
        """
        if self.current_grounding is None:
            # First grounding
            grounding, ci, metadata = self.announce(current_context)
            return (grounding, "initial announcement", ci, metadata)

        # Call parent heartbeat
        grounding, action = super().heartbeat(current_context)

        # Calculate and regulate CI
        raw_ci = self.calculate_raw_ci(grounding)
        regulated_ci, reg_metadata = self.calculate_regulated_ci(raw_ci, grounding.timestamp)

        # Track CI history
        self.ci_history.append((regulated_ci, grounding.timestamp))
        self.regulation_metadata_history.append(reg_metadata)

        return (grounding, action, regulated_ci, reg_metadata)

    def check_status_with_ci(self) -> Tuple[GroundingStatus, Optional[timedelta], Optional[float], Optional[Dict]]:
        """
        Check status and calculate current regulated CI

        Returns:
            (status, time_remaining_or_overdue, regulated_ci, regulation_metadata)
        """
        status, time = super().check_status()

        if self.current_grounding is None:
            return (status, time, None, None)

        # Calculate current CI
        raw_ci = self.calculate_raw_ci(self.current_grounding)
        regulated_ci, reg_metadata = self.calculate_regulated_ci(raw_ci, datetime.now().isoformat())

        return (status, time, regulated_ci, reg_metadata)

    def get_ci_history(self, window: Optional[timedelta] = None) -> List[Tuple[float, str]]:
        """
        Get CI history, optionally filtered by time window

        Args:
            window: Time window to filter (None = all history)

        Returns:
            List of (CI, timestamp) tuples
        """
        if window is None:
            return self.ci_history.copy()

        cutoff = datetime.now() - window
        return [
            (ci, ts) for ci, ts in self.ci_history
            if datetime.fromisoformat(ts) > cutoff
        ]

    def get_regulation_summary(self) -> Dict:
        """
        Get summary of regulation activity

        Returns:
            Summary statistics about regulation interventions
        """
        total_regulations = len(self.regulation_metadata_history)

        if total_regulations == 0:
            return {
                'total_cycles': 0,
                'regulations_applied': 0,
                'regulation_types': {}
            }

        # Count regulation types
        regulation_counts = {}
        for metadata in self.regulation_metadata_history:
            for reg_type in metadata.get('regulations_applied', []):
                regulation_counts[reg_type] = regulation_counts.get(reg_type, 0) + 1

        # Calculate averages
        avg_raw_ci = sum(m['raw_ci'] for m in self.regulation_metadata_history) / total_regulations
        avg_final_ci = sum(m.get('final_ci', m['raw_ci']) for m in self.regulation_metadata_history) / total_regulations

        # Count cascades detected
        cascades_detected = sum(
            1 for m in self.regulation_metadata_history
            if 'cascade_detection' in m and m['cascade_detection'].get('is_cascade', False)
        )

        return {
            'total_cycles': total_regulations,
            'regulations_applied': sum(regulation_counts.values()),
            'regulation_types': regulation_counts,
            'avg_raw_ci': avg_raw_ci,
            'avg_final_ci': avg_final_ci,
            'avg_ci_boost': avg_final_ci - avg_raw_ci,
            'cascades_detected': cascades_detected,
            'cascade_rate': cascades_detected / total_regulations if total_regulations > 0 else 0.0
        }

    def calculate_regulated_atp_cost(self, base_cost: float) -> float:
        """
        Calculate ATP cost using current regulated CI

        Args:
            base_cost: Base ATP cost

        Returns:
            Regulated ATP cost
        """
        if self.current_grounding is None:
            return base_cost

        # Get current regulated CI
        _, _, regulated_ci, _ = self.check_status_with_ci()

        if regulated_ci is None:
            return base_cost

        return self.regulation_manager.calculate_regulated_atp_cost(base_cost, regulated_ci)


# ============================================================================
# Helper Functions
# ============================================================================

def simulate_grounding_lifecycle(
    entity_lct: str,
    mrh_graph: MRHGraph,
    contexts: List[GroundingContext],
    enable_regulation: bool = True
) -> Dict:
    """
    Simulate grounding lifecycle over multiple contexts

    Useful for testing regulation effectiveness over time.

    Args:
        entity_lct: Entity LCT URI
        mrh_graph: MRH graph
        contexts: Sequence of grounding contexts
        enable_regulation: Enable/disable regulation

    Returns:
        Simulation results with CI history and regulation stats
    """
    manager = RegulatedGroundingManager(
        entity_lct,
        mrh_graph,
        enable_regulation=enable_regulation
    )

    results = {
        'groundings': [],
        'ci_values': [],
        'regulation_metadata': [],
        'actions': []
    }

    for i, context in enumerate(contexts):
        if i == 0:
            grounding, ci, metadata = manager.announce(context)
            action = "initial announcement"
        else:
            grounding, action, ci, metadata = manager.heartbeat(context)

        results['groundings'].append(grounding)
        results['ci_values'].append(ci)
        results['regulation_metadata'].append(metadata)
        results['actions'].append(action)

    results['regulation_summary'] = manager.get_regulation_summary()
    results['final_ci'] = results['ci_values'][-1] if results['ci_values'] else None

    return results


def compare_regulated_vs_unregulated(
    entity_lct: str,
    mrh_graph: MRHGraph,
    contexts: List[GroundingContext]
) -> Dict:
    """
    Compare regulated vs unregulated grounding lifecycle

    Shows effectiveness of regulation in preventing cascades.

    Args:
        entity_lct: Entity LCT URI
        mrh_graph: MRH graph
        contexts: Sequence of grounding contexts

    Returns:
        Comparison results
    """
    # Run with regulation
    regulated = simulate_grounding_lifecycle(
        entity_lct, mrh_graph, contexts, enable_regulation=True
    )

    # Run without regulation
    unregulated = simulate_grounding_lifecycle(
        entity_lct, mrh_graph, contexts, enable_regulation=False
    )

    return {
        'regulated': {
            'final_ci': regulated['final_ci'],
            'avg_ci': sum(regulated['ci_values']) / len(regulated['ci_values']),
            'min_ci': min(regulated['ci_values']),
            'regulation_summary': regulated['regulation_summary']
        },
        'unregulated': {
            'final_ci': unregulated['final_ci'],
            'avg_ci': sum(unregulated['ci_values']) / len(unregulated['ci_values']),
            'min_ci': min(unregulated['ci_values']),
            'regulation_summary': unregulated['regulation_summary']
        },
        'improvement': {
            'final_ci_delta': regulated['final_ci'] - unregulated['final_ci'],
            'avg_ci_delta': (sum(regulated['ci_values']) / len(regulated['ci_values'])) -
                          (sum(unregulated['ci_values']) / len(unregulated['ci_values'])),
            'min_ci_delta': min(regulated['ci_values']) - min(unregulated['ci_values'])
        }
    }
