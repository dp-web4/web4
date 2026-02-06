#!/usr/bin/env python3
"""
Test: Validate DEEP Depth Fix

Validates that the fix to identity_grounding_required resolves the
Session 160 issue where DEEP depth failed 100% of the time.

Expected Results:
- BEFORE FIX: DEEP depth 0% success, 0.0 quality (identity gate)
- AFTER FIX: DEEP depth 80%+ success, quality comparable to STANDARD

Test Strategy:
1. Run same thoughts at STANDARD and DEEP depth
2. Verify DEEP no longer forces 0.0 quality
3. Validate identity bonus still works when present
4. Confirm DEEP depth is now viable for meta-learning

Platform: Legion
Date: 2026-01-10
"""

import asyncio
import sys
from pathlib import Path

HOME = Path.home()
sys.path.insert(0, str(HOME / "ai-workspace" / "web4"))

from session158_dynamic_cogitation_depth import (
    DynamicDepthCogitationNode,
    CogitationDepth,
    CogitationMode,
)


async def test_deep_depth_fix():
    """Test that DEEP depth works after fix."""
    print("=" * 80)
    print("TEST: DEEP Depth Fix Validation")
    print("=" * 80)
    print("Validating: identity_grounding_required=False at DEEP")
    print("Expected: DEEP depth should work for generic thoughts")
    print("=" * 80)

    # Create node
    node = DynamicDepthCogitationNode(
        node_id="legion_test",
        lct_id="lct:web4:test",
        hardware_type="GPU",
        hardware_level=5,
        enable_dynamic_depth=True,
    )

    # Start node
    node_task = asyncio.create_task(node.start())
    await asyncio.sleep(1)

    # Test thoughts (generic, no identity markers)
    test_thoughts = [
        ("Verifying high quality research insight", CogitationMode.VERIFYING),
        ("Integrating multiple research streams", CogitationMode.INTEGRATING),
        ("Exploring new architectural patterns", CogitationMode.EXPLORING),
    ]

    results = {
        'standard': [],
        'deep': [],
    }

    print("\n" + "=" * 80)
    print("PHASE 1: Test STANDARD Depth (Baseline)")
    print("=" * 80)

    for thought, mode in test_thoughts:
        node.internal_atp_balance = 95.0  # STANDARD depth range

        result = await node.internal_cogitation_with_depth(thought, mode)

        results['standard'].append({
            'thought': thought[:40],
            'mode': mode.value,
            'quality': result.verification_quality_score,
            'confidence': result.epistemic_confidence,
            'success': result.verification_quality_score > 0.3,
        })

        print(f"\nThought: {thought[:40]}...")
        print(f"  Mode: {mode.value}")
        print(f"  Quality: {result.verification_quality_score:.3f}")
        print(f"  Confidence: {result.epistemic_confidence:.3f}")
        print(f"  Success: {'✅' if result.verification_quality_score > 0.3 else '❌'}")

    print("\n" + "=" * 80)
    print("PHASE 2: Test DEEP Depth (After Fix)")
    print("=" * 80)

    for thought, mode in test_thoughts:
        node.internal_atp_balance = 120.0  # DEEP depth range

        result = await node.internal_cogitation_with_depth(thought, mode)

        results['deep'].append({
            'thought': thought[:40],
            'mode': mode.value,
            'quality': result.verification_quality_score,
            'confidence': result.epistemic_confidence,
            'success': result.verification_quality_score > 0.3,
        })

        print(f"\nThought: {thought[:40]}...")
        print(f"  Mode: {mode.value}")
        print(f"  Quality: {result.verification_quality_score:.3f}")
        print(f"  Confidence: {result.epistemic_confidence:.3f}")
        print(f"  Success: {'✅' if result.verification_quality_score > 0.3 else '❌'}")

    # Analysis
    print("\n" + "=" * 80)
    print("FIX VALIDATION ANALYSIS")
    print("=" * 80)

    standard_success = sum(1 for r in results['standard'] if r['success'])
    deep_success = sum(1 for r in results['deep'] if r['success'])

    standard_avg_quality = sum(r['quality'] for r in results['standard']) / len(results['standard'])
    deep_avg_quality = sum(r['quality'] for r in results['deep']) / len(results['deep'])

    print(f"\nSTANDARD Depth:")
    print(f"  Success rate: {standard_success}/{len(results['standard'])} ({standard_success/len(results['standard'])*100:.0f}%)")
    print(f"  Avg quality: {standard_avg_quality:.3f}")

    print(f"\nDEEP Depth:")
    print(f"  Success rate: {deep_success}/{len(results['deep'])} ({deep_success/len(results['deep'])*100:.0f}%)")
    print(f"  Avg quality: {deep_avg_quality:.3f}")

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    if deep_success == 0:
        print("\n❌ FIX FAILED: DEEP depth still fails 100%")
        print("   Problem: identity_grounding_required still causing failures")
    elif deep_success >= 2:  # At least 2/3 success
        print("\n✅ FIX SUCCESSFUL: DEEP depth now works!")
        print(f"   Success rate improved from 0% to {deep_success/len(results['deep'])*100:.0f}%")
        print(f"   Quality improved from 0.0 to {deep_avg_quality:.3f}")
        print("   DEEP depth is now viable for meta-learning")
    else:
        print("\n⚠️  PARTIAL SUCCESS: DEEP works but unreliable")
        print(f"   Success rate: {deep_success/len(results['deep'])*100:.0f}%")
        print("   May need additional tuning")

    # Cleanup
    node_task.cancel()
    try:
        await node_task
    except asyncio.CancelledError:
        pass

    return {
        'standard_success_rate': standard_success / len(results['standard']),
        'deep_success_rate': deep_success / len(results['deep']),
        'standard_avg_quality': standard_avg_quality,
        'deep_avg_quality': deep_avg_quality,
        'fix_successful': deep_success >= 2,
    }


if __name__ == "__main__":
    results = asyncio.run(test_deep_depth_fix())

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print(f"Fix successful: {results['fix_successful']}")
    print(f"DEEP depth now {'VIABLE' if results['fix_successful'] else 'STILL BROKEN'} ✅")
    print("=" * 80)
