#!/usr/bin/env python3
"""
Long-Duration Emotional Coordinator Validation - Web4 Session 55

Tests Phase 2d emotional adaptation at scale (5,000+ cycles).

Validation Goals:
1. Consolidation frequency and effectiveness
2. Emotional state evolution across circadian phases
3. Threshold adaptation convergence
4. Emotional-temporal interactions

Research Questions:
- Q1: How often does frustration-triggered consolidation occur?
- Q2: Do emotional states vary by circadian phase?
- Q3: Does dynamic threshold adaptation improve coordination?
- Q4: Are there interaction effects between emotional and temporal dimensions?

Author: Claude (Legion Autonomous Web4 Research Session 55)
Date: 2025-12-15
"""

import sys
import time
from pathlib import Path
from typing import Dict, List
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from web4_phase2d_emotional_coordinator import (
    Web4EmotionalCoordinator,
    EmotionalCoordinationMetrics,
    EmotionalTelemetry
)
from web4_phase2c_circadian_coordinator import CircadianPhase


def generate_phase_dependent_history(num_cycles: int = 5000) -> List[Dict]:
    """
    Generate coordination history with phase-dependent patterns.

    Simulates:
    - DAY: High epistemic diversity, high quality
    - NIGHT: Low epistemic diversity, lower quality
    - Occasional quality stagnation → frustration
    - Varying priority and epistemic factors

    Args:
        num_cycles: Number of cycles to generate

    Returns:
        List of simulated coordination events
    """
    np.random.seed(42)  # Reproducible
    history = []

    for i in range(num_cycles):
        cycle_in_period = i % 100

        # Determine circadianphase
        if 0 <= cycle_in_period < 10:
            phase = CircadianPhase.DAWN
        elif 10 <= cycle_in_period < 50:
            phase = CircadianPhase.DAY
        elif 50 <= cycle_in_period < 60:
            phase = CircadianPhase.DUSK
        elif 60 <= cycle_in_period < 90:
            phase = CircadianPhase.NIGHT
        else:  # 90-100
            phase = CircadianPhase.DEEP_NIGHT

        # Phase-dependent base quality
        if phase in [CircadianPhase.DAY, CircadianPhase.DAWN, CircadianPhase.DUSK]:
            base_quality = 0.75
            base_diversity = 0.7
        else:  # NIGHT, DEEP_NIGHT
            base_quality = 0.60
            base_diversity = 0.4

        # Add stagnation periods (cycles 1000-1100, 2500-2600, 4000-4100)
        if (1000 <= i < 1100) or (2500 <= i < 2600) or (4000 <= i < 4100):
            # Quality stagnates
            quality = base_quality + np.random.uniform(-0.02, 0.02)
            diversity = base_diversity * 0.5  # Low diversity during stagnation
        else:
            # Normal variation
            quality = base_quality + np.random.uniform(-0.1, 0.1)
            diversity = base_diversity + np.random.uniform(-0.2, 0.2)

        # Clip to valid range
        quality = np.clip(quality, 0, 1)
        diversity = np.clip(diversity, 0, 1)

        # Epistemic factors
        local_confidence = np.random.uniform(0.6, 0.9)
        trust_alignment = np.random.uniform(0.5, 0.9)

        # Metabolic/priority factors
        atp_available = np.random.uniform(0.5, 1.0)
        priority = np.random.uniform(0.3, 0.9)

        history.append({
            'cycle': i,
            'quality': quality,
            'epistemic_diversity': diversity,
            'local_confidence': local_confidence,
            'trust_alignment': trust_alignment,
            'atp_available': atp_available,
            'task_priority': priority,
            'circadian_phase': phase
        })

    return history


def run_long_duration_test():
    """Run 5,000 cycle emotional coordinator test."""

    print("=" * 80)
    print("LONG-DURATION EMOTIONAL COORDINATOR VALIDATION")
    print("=" * 80)
    print()

    # Generate history
    print("Generating 5,000-cycle history...")
    history = generate_phase_dependent_history(5000)
    print(f"  ✓ Generated {len(history)} cycles")
    print()

    # Create emotional coordinator
    print("Initializing Phase 2d emotional coordinator...")

    coordinator = Web4EmotionalCoordinator(
        enable_circadian=True,
        enable_emotional=True,
        circadian_period=100,
        consolidate_during_night=True,
        # Emotional parameters (Session 54 defaults)
        frustration_consolidation_threshold=0.6,
        curiosity_diversity_bonus=0.05,
        progress_threshold_adjustment_range=(-0.05, 0.10),
        engagement_priority_threshold=0.7
    )
    print("  ✓ Coordinator initialized")
    print()

    # Run simulation
    print("Running simulation...")
    decisions = []
    consolidations = []
    emotional_states = []
    threshold_adjustments = []

    start_time = time.time()

    for event in history:
        decision, confidence, telemetry = coordinator.should_coordinate(
            event['quality'],
            event['epistemic_diversity'],
            event['local_confidence'],
            event['trust_alignment'],
            event['atp_available'],
            event['task_priority']
        )

        decisions.append({
            'cycle': event['cycle'],
            'decision': decision,
            'confidence': confidence,
            'phase': event['circadian_phase'].value,
            'quality': event['quality']
        })

        # Track emotional state
        if telemetry.emotional_state:
            emotional_states.append({
                'cycle': event['cycle'],
                'frustration': telemetry.emotional_state.frustration,
                'progress': telemetry.emotional_state.progress,
                'curiosity': telemetry.emotional_state.curiosity,
                'engagement': telemetry.emotional_state.engagement,
                'phase': event['circadian_phase'].value
            })

        # Track consolidations
        if telemetry.consolidation_triggered:
            consolidations.append(event['cycle'])

        # Track threshold adjustments
        if telemetry.threshold_adjustment and telemetry.threshold_adjustment != 0:
            threshold_adjustments.append({
                'cycle': event['cycle'],
                'adjustment': telemetry.threshold_adjustment
            })

    elapsed = time.time() - start_time
    print(f"  ✓ Simulation complete ({elapsed:.2f}s)")
    print()

    # Analysis
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print()

    # 1. Consolidation Analysis
    print("1. FRUSTRATION-TRIGGERED CONSOLIDATION")
    print(f"   Total consolidations: {len(consolidations)}")
    if consolidations:
        print(f"   Consolidation cycles: {consolidations}")
        # Check if consolidations occurred during stagnation periods
        stagnation_periods = [(1000, 1100), (2500, 2600), (4000, 4100)]
        stagnation_consolidations = sum(
            1 for c in consolidations
            if any(start <= c < end for start, end in stagnation_periods)
        )
        print(f"   During stagnation periods: {stagnation_consolidations}/{len(consolidations)}")
        print(f"   ✅ CONSOLIDATION WORKING" if stagnation_consolidations > 0 else "⚠️  NO STAGNATION DETECTION")
    else:
        print("   ⚠️  NO CONSOLIDATIONS TRIGGERED")
    print()

    # 2. Emotional State Evolution
    print("2. EMOTIONAL STATE EVOLUTION")
    if emotional_states:
        frustration_values = [s['frustration'] for s in emotional_states]
        progress_values = [s['progress'] for s in emotional_states]
        curiosity_values = [s['curiosity'] for s in emotional_states]
        engagement_values = [s['engagement'] for s in emotional_states]

        print(f"   Frustration:  mean={np.mean(frustration_values):.3f}, "
              f"max={np.max(frustration_values):.3f}, "
              f"threshold_exceeded={sum(1 for f in frustration_values if f > 0.6)}")
        print(f"   Progress:     mean={np.mean(progress_values):.3f}, "
              f"range=[{np.min(progress_values):.3f}, {np.max(progress_values):.3f}]")
        print(f"   Curiosity:    mean={np.mean(curiosity_values):.3f}, "
              f"range=[{np.min(curiosity_values):.3f}, {np.max(curiosity_values):.3f}]")
        print(f"   Engagement:   mean={np.mean(engagement_values):.3f}, "
              f"range=[{np.min(engagement_values):.3f}, {np.max(engagement_values):.3f}]")
    else:
        print("   ⚠️  NO EMOTIONAL STATE DATA")
    print()

    # 3. Threshold Adaptation
    print("3. DYNAMIC THRESHOLD ADAPTATION")
    if threshold_adjustments:
        adjustments = [t['adjustment'] for t in threshold_adjustments]
        print(f"   Total adjustments: {len(threshold_adjustments)}")
        print(f"   Mean adjustment: {np.mean(adjustments):.4f}")
        print(f"   Range: [{np.min(adjustments):.4f}, {np.max(adjustments):.4f}]")
        positive_adjustments = sum(1 for a in adjustments if a > 0)
        negative_adjustments = sum(1 for a in adjustments if a < 0)
        print(f"   Positive (more selective): {positive_adjustments}")
        print(f"   Negative (less selective): {negative_adjustments}")
    else:
        print("   NO THRESHOLD ADJUSTMENTS (progress remained neutral 0.3-0.7)")
    print()

    # 4. Emotional-Temporal Interaction
    print("4. EMOTIONAL-TEMPORAL INTERACTION")
    if emotional_states:
        # Group by phase
        phase_emotions = {}
        for state in emotional_states:
            phase = state['phase']
            if phase not in phase_emotions:
                phase_emotions[phase] = {'frustration': [], 'curiosity': [], 'progress': []}

            phase_emotions[phase]['frustration'].append(state['frustration'])
            phase_emotions[phase]['curiosity'].append(state['curiosity'])
            phase_emotions[phase]['progress'].append(state['progress'])

        print("   Frustration by phase:")
        for phase in sorted(phase_emotions.keys()):
            mean_frust = np.mean(phase_emotions[phase]['frustration'])
            print(f"     {phase:12s}: {mean_frust:.3f}")

        print()
        print("   Curiosity by phase:")
        for phase in sorted(phase_emotions.keys()):
            mean_cur = np.mean(phase_emotions[phase]['curiosity'])
            print(f"     {phase:12s}: {mean_cur:.3f}")
    else:
        print("   NO DATA")
    print()

    # 5. Coordination Rate by Phase
    print("5. COORDINATION RATE BY CIRCADIAN PHASE")
    phase_decisions = {}
    for dec in decisions:
        phase = dec['phase']
        if phase not in phase_decisions:
            phase_decisions[phase] = {'total': 0, 'coordinated': 0}

        phase_decisions[phase]['total'] += 1
        if dec['decision']:
            phase_decisions[phase]['coordinated'] += 1

    for phase in sorted(phase_decisions.keys()):
        total = phase_decisions[phase]['total']
        coordinated = phase_decisions[phase]['coordinated']
        rate = (coordinated / total * 100) if total > 0 else 0
        print(f"   {phase:12s}: {coordinated:4d}/{total:4d} ({rate:5.1f}%)")
    print()

    # Create visualizations
    print("Creating visualizations...")
    create_visualizations(emotional_states, consolidations, decisions)
    print("  ✓ Saved to emotional_long_duration_results.png")
    print()

    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()
    print(f"✅ Simulation complete: 5,000 cycles")
    print(f"✅ Consolidations: {len(consolidations)}")
    print(f"✅ Emotional state tracking: {len(emotional_states)} measurements")
    print(f"✅ Threshold adjustments: {len(threshold_adjustments)}")
    print()

    # Research questions answered
    print("RESEARCH QUESTIONS:")
    print()
    print(f"Q1: Consolidation frequency?")
    print(f"    A: {len(consolidations)} consolidations in 5,000 cycles "
          f"({len(consolidations)/50:.2f} per 100-cycle period)")
    print()
    print(f"Q2: Emotional states vary by phase?")
    if len(phase_emotions) > 1:
        frust_variance = np.var([np.mean(phase_emotions[p]['frustration']) for p in phase_emotions])
        cur_variance = np.var([np.mean(phase_emotions[p]['curiosity']) for p in phase_emotions])
        print(f"    A: YES - Frustration variance across phases: {frust_variance:.4f}")
        print(f"           Curiosity variance across phases: {cur_variance:.4f}")
    else:
        print(f"    A: INSUFFICIENT DATA")
    print()
    print(f"Q3: Threshold adaptation effective?")
    if threshold_adjustments:
        print(f"    A: {len(threshold_adjustments)} adjustments occurred")
        print(f"       (Effectiveness requires quality comparison, not measured here)")
    else:
        print(f"    A: NO EXTREME PROGRESS STATES (0.3-0.7 range)")
    print()


def create_visualizations(emotional_states, consolidations, decisions):
    """Create visualization plots."""
    if not emotional_states:
        print("  ⚠️  No emotional state data to visualize")
        return

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    cycles = [s['cycle'] for s in emotional_states]
    frustration = [s['frustration'] for s in emotional_states]
    progress = [s['progress'] for s in emotional_states]
    curiosity = [s['curiosity'] for s in emotional_states]

    # Plot 1: Frustration over time with consolidation markers
    axes[0].plot(cycles, frustration, label='Frustration', color='red', alpha=0.7)
    axes[0].axhline(y=0.6, color='darkred', linestyle='--', label='Consolidation Threshold')
    for cons_cycle in consolidations:
        axes[0].axvline(x=cons_cycle, color='purple', alpha=0.3, linestyle='-', linewidth=2)
    axes[0].set_xlabel('Cycle')
    axes[0].set_ylabel('Frustration')
    axes[0].set_title('Frustration Evolution & Consolidation Events')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Progress and Curiosity
    axes[1].plot(cycles, progress, label='Progress', color='blue', alpha=0.7)
    axes[1].plot(cycles, curiosity, label='Curiosity', color='green', alpha=0.7)
    axes[1].axhline(y=0.7, color='blue', linestyle='--', alpha=0.5, label='Progress Threshold (High)')
    axes[1].axhline(y=0.3, color='blue', linestyle='--', alpha=0.5, label='Progress Threshold (Low)')
    axes[1].set_xlabel('Cycle')
    axes[1].set_ylabel('Value')
    axes[1].set_title('Progress & Curiosity Evolution')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Coordination rate over time (rolling average)
    window = 100
    coord_decisions = [1 if d['decision'] else 0 for d in decisions]
    rolling_rate = []
    rolling_cycles = []
    for i in range(len(coord_decisions) - window):
        rate = np.mean(coord_decisions[i:i+window]) * 100
        rolling_rate.append(rate)
        rolling_cycles.append(decisions[i+window//2]['cycle'])

    axes[2].plot(rolling_cycles, rolling_rate, color='orange', alpha=0.7)
    axes[2].set_xlabel('Cycle')
    axes[2].set_ylabel('Coordination Rate (%)')
    axes[2].set_title(f'Coordination Rate (Rolling {window}-cycle Average)')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('emotional_long_duration_results.png', dpi=150)
    plt.close()


if __name__ == "__main__":
    run_long_duration_test()
