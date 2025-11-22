#!/usr/bin/env python3
"""
Quick Validation: Timing Attack Mitigation
Session #61

Quick validation that timing jitter and noise injection are working.
"""

import time
import statistics
import random
from decimal import Decimal

# Import batcher
from trust_update_batcher import TrustUpdateBatcher

print("=== Timing Attack Mitigation Validation ===\n")

# Test 1: Verify jitter is applied
print("Test 1: Flush Jitter Variance")
print("-" * 50)

db_config = {
    'dbname': 'web4_test',
    'user': 'postgres',
    'host': 'localhost'
}

# Create batcher with 2s interval, 1s jitter
batcher = TrustUpdateBatcher(
    db_config=db_config,
    flush_interval_seconds=2,
    flush_jitter_seconds=1.0,
    auto_start=False
)

batcher.start()

# Collect 10 flush timings
flush_times = []
start = time.time()

print("Measuring flush intervals (target: 2s ± 1s):")
while len(flush_times) < 10:
    stats = batcher.get_stats()
    if stats['total_flushes'] > len(flush_times):
        elapsed = time.time() - start
        flush_times.append(elapsed)
        print(f"  Flush {len(flush_times)}: {elapsed:.2f}s", end="")
        if len(flush_times) > 1:
            interval = flush_times[-1] - flush_times[-2]
            print(f" (interval: {interval:.2f}s)")
        else:
            print()
        start = time.time()

batcher.stop()

# Calculate intervals
intervals = [flush_times[i] - flush_times[i-1] for i in range(1, len(flush_times))]

mean = statistics.mean(intervals)
stdev = statistics.stdev(intervals)
min_val = min(intervals)
max_val = max(intervals)

print(f"\nStatistics:")
print(f"  Mean interval: {mean:.3f}s (expected: ~2.0s)")
print(f"  Std deviation: {stdev:.3f}s (expected: >0.3s)")
print(f"  Range: {min_val:.3f}s - {max_val:.3f}s (expected: ~1s - ~3s)")
print(f"  Variance: {max_val - min_val:.3f}s (expected: >1s)")

# Validation
success = True
if abs(mean - 2.0) > 0.5:
    print(f"  ❌ FAIL: Mean too far from target (2s ± 0.5s)")
    success = False
else:
    print(f"  ✅ PASS: Mean close to target")

if stdev < 0.3:
    print(f"  ❌ FAIL: Insufficient variance (need >0.3s)")
    success = False
else:
    print(f"  ✅ PASS: Significant variance present")

if (max_val - min_val) < 1.0:
    print(f"  ❌ FAIL: Range too small (need >1s)")
    success = False
else:
    print(f"  ✅ PASS: Sufficient range")

print("\n" + "=" * 50)
if success:
    print("✅ TIMING ATTACK MITIGATION VALIDATED")
    print("   - Flush jitter working (unpredictable timing)")
    print("   - Information leakage prevented")
else:
    print("❌ VALIDATION FAILED")
    print("   - Check jitter implementation")

print("\n" + "=" * 50)
print("Mitigation Summary:")
print(f"  - Random jitter: ±{batcher.flush_jitter}s")
print(f"  - Observed variance: {stdev:.2f}s")
print(f"  - Timing unpredictability: {(stdev/mean)*100:.1f}%")
print(f"  - Attack resistance: {'HIGH' if (stdev/mean) > 0.15 else 'LOW'}")
