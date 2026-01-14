"""
Quick script to analyze T001-T011 using Session #20 tools.
"""
import sys
sys.path.append('/home/dp/ai-workspace/web4')

from session200_sage_validation import SAGECoherenceAnalyzer

# Initialize analyzer
analyzer = SAGECoherenceAnalyzer()

# Analyze T001-T011 (extended from T001-T009)
session_ids = [f"T00{i}" for i in range(1, 10)] + ["T010", "T011"]

print(f"Analyzing extended SAGE trajectory: {', '.join(session_ids)}")
print("Including T010 (Track A complete, 100%) and T011 (Track B start, 33%)")

try:
    results = analyzer.analyze_training_trajectory(session_ids)
    
    print("\n" + "=" * 70)
    print("EXTENDED TRAJECTORY ANALYSIS (T001-T011)")
    print("=" * 70)
    
    coherence = results['coherence_analysis']
    print(f"\nCoherence Analysis:")
    print(f"  Range: {coherence['min_coherence']:.2f} → {coherence['max_coherence']:.2f}")
    print(f"  N_corr: {coherence['ncorr_measured']:.2f}")
    print(f"  γ: {coherence['gamma_measured']:.3f}")
    print(f"  Crossed C=0.5: {coherence['crossed_c_threshold']}")
    
    print(f"\nPhase Transitions: {len(results['phase_transitions'])}")
    for i, trans in enumerate(results['phase_transitions']):
        if trans['coherence_change'] > 0.3 or trans['coherence_change'] < -0.3:
            print(f"  {i+1}. Session {trans['from_session']}→{trans['to_session']}: "
                  f"ΔC={trans['coherence_change']:+.2f} ({trans['type']})")
    
    # Focus on T010→T011 transition
    print("\n" + "=" * 70)
    print("TRACK A→B TRANSITION (T010→T011)")
    print("=" * 70)
    
    t010 = results['session_details'][9]  # T010
    t011 = results['session_details'][10]  # T011
    
    print(f"\nT010 (Track A complete):")
    print(f"  Score: {t010['score']:.1%}")
    print(f"  Coherence: {t010['coherence']:.2f}")
    print(f"  α: {t010['alpha_estimate']:.2f}")
    
    print(f"\nT011 (Track B start):")
    print(f"  Score: {t011['score']:.1%}")
    print(f"  Coherence: {t011['coherence']:.2f}")
    print(f"  α: {t011['alpha_estimate']:.2f}")
    
    print(f"\nTransition:")
    print(f"  ΔScore: {t011['score'] - t010['score']:.1%}")
    print(f"  ΔCoherence: {t011['coherence'] - t010['coherence']:+.2f}")
    
    # Check if this is a phase transition
    if abs(t011['coherence'] - t010['coherence']) > 0.3:
        print(f"  ⚠️ PHASE TRANSITION DETECTED")
    else:
        print(f"  → Gradual transition (not phase transition)")
    
    print("\n✓ Extended analysis complete")
    
except Exception as e:
    print(f"Error: {e}")
    print("Using data from state.json observations instead...")
    
    # Fallback: use observed scores
    scores = {
        'T001': 0.80, 'T002': 1.00, 'T003': 0.60, 'T004': 0.40, 'T005': 0.40,
        'T006': 1.00, 'T007': 1.00, 'T008': 0.80, 'T009': 0.80, 
        'T010': 1.00, 'T011': 0.33
    }
    
    print("\nObserved Trajectory:")
    for sid, score in scores.items():
        print(f"  {sid}: {score:.0%}")
    
    print(f"\nT010→T011 transition: {scores['T010']:.0%} → {scores['T011']:.0%}")
    print(f"ΔScore: {scores['T011'] - scores['T010']:.1%} (COLLAPSE)")
    print("\nThis is a TRACK TRANSITION event, not simple performance drop.")
    print("Track A (Basic Completion) → Track B (Memory and Recall)")
    print("Performance reset expected when skill domain changes.")

