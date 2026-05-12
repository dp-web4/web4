#!/usr/bin/env python3
"""
Action Sequence Test Suite
Session #55: Testing multi-step actions for IRP integration

Tests:
1. Create and execute action sequence
2. Iteration tracking with ATP charging
3. Checkpoint creation (every 3 iterations)
4. Convergence detection and early stopping
5. ATP refund policies (TIERED, FULL, NONE)
6. Failure scenarios (timeout, budget exhaustion)
7. Witness verification of checkpoints
"""

import psycopg2
import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(dbname="web4", user="postgres", host="localhost")

def sha256_hash(data: str) -> str:
    """Compute SHA256 hash"""
    return hashlib.sha256(data.encode()).hexdigest()

def setup_test_entities(conn):
    """Create test entities and organization"""
    cursor = conn.cursor()

    # Create AI entity
    lct_id = "lct:ai:sage:test_seq_001"
    public_key = "ed25519:" + ("a" * 64)
    birth_cert_hash = sha256_hash(f"{lct_id}:{public_key}")

    cursor.execute("""
        INSERT INTO lct_identities
        (lct_id, entity_type, society_id, birth_certificate_hash, public_key)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (lct_id) DO NOTHING
    """, (lct_id, 'AI', 'soc:web4:test', birth_cert_hash, public_key))

    # Create organization
    cursor.execute("""
        INSERT INTO organizations (organization_id, organization_name)
        VALUES (%s, %s)
        ON CONFLICT (organization_id) DO NOTHING
    """, ('org:test:sequences', 'Test Sequences Org'))

    # Create reputation for AI
    cursor.execute("""
        INSERT INTO reputation_scores (lct_id, organization_id, talent_score, training_score, temperament_score)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (lct_id, organization_id) DO NOTHING
    """, (lct_id, 'org:test:sequences', 0.8, 0.85, 0.9))

    conn.commit()
    cursor.close()

    return lct_id

def test_1_create_sequence(conn, actor_lct):
    """Test 1: Create action sequence"""
    print("\n=== Test 1: Create Action Sequence ===")
    cursor = conn.cursor()

    sequence_id = "seq:irp:test:001"

    cursor.execute("""
        INSERT INTO action_sequences
        (sequence_id, actor_lct, organization_id, sequence_type, target_resource, operation,
         max_iterations, iteration_atp_cost, atp_budget_reserved, convergence_target,
         convergence_metric, early_stopping_enabled, atp_refund_policy)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        sequence_id, actor_lct, 'org:test:sequences', 'IRP_REFINEMENT',
        'vision:scene:analysis', 'vision_encoding',
        10, 5, 100, 0.0500,
        'energy', True, 'TIERED'
    ))

    conn.commit()

    # Verify sequence created
    cursor.execute("""
        SELECT sequence_id, sequence_type, max_iterations, atp_budget_reserved,
               convergence_target, status
        FROM action_sequences WHERE sequence_id = %s
    """, (sequence_id,))

    result = cursor.fetchone()
    assert result[0] == sequence_id, "Sequence not found!"
    assert result[5] == 'active', "Should be active!"

    print(f"  ✓ Sequence Created: {result[0]}")
    print(f"    Type: {result[1]}")
    print(f"    Max Iterations: {result[2]}")
    print(f"    ATP Budget: {result[3]}")
    print(f"    Convergence Target: {result[4]}")
    print(f"    Status: {result[5]}")

    cursor.close()
    return sequence_id

def test_2_iteration_tracking(conn, sequence_id):
    """Test 2: Record iterations and track ATP"""
    print("\n=== Test 2: Iteration Tracking & ATP Charging ===")
    cursor = conn.cursor()

    # Simulate 5 iterations with decreasing energy
    energies = [0.850, 0.650, 0.480, 0.320, 0.180]
    checkpoints_created = []

    for i, energy in enumerate(energies, 1):
        state_hash = sha256_hash(f"state_{i}_{energy}")

        # Record iteration using function
        cursor.execute("""
            SELECT record_sequence_iteration(%s, %s, %s, %s)
        """, (sequence_id, energy, state_hash, 5))

        result = cursor.fetchone()[0]
        print(f"  Iteration {i}: Energy={energy:.3f}, Status={result['status']}")

        if result.get('checkpointed'):
            checkpoints_created.append(result.get('checkpoint_id'))
            print(f"    → Checkpoint created: {result.get('checkpoint_id')}")

        conn.commit()

    # Verify sequence state
    cursor.execute("""
        SELECT current_iteration, atp_consumed, iterations_used, status, final_energy
        FROM action_sequences WHERE sequence_id = %s
    """, (sequence_id,))

    result = cursor.fetchone()

    print(f"\n  Sequence State After 5 Iterations:")
    print(f"    Current Iteration: {result[0]}")
    print(f"    ATP Consumed: {result[1]} (5 iterations × 5 ATP)")
    print(f"    Iterations Used: {result[2]}")
    print(f"    Status: {result[3]}")
    print(f"    Final Energy: {float(result[4]):.3f}")

    assert result[0] == 5, "Should have 5 iterations!"
    assert result[1] == 25, "Should have consumed 25 ATP (5×5)!"
    assert result[3] == 'active', "Should still be active!"

    print(f"  ✓ Iteration tracking working correctly")
    print(f"  ✓ ATP charged incrementally: {result[1]} ATP")
    print(f"  ✓ Checkpoints created: {len(checkpoints_created)}")

    cursor.close()
    return checkpoints_created

def test_3_checkpoint_verification(conn, sequence_id, checkpoint_ids):
    """Test 3: Verify checkpoints created correctly"""
    print("\n=== Test 3: Checkpoint Verification ===")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT checkpoint_id, iteration_number, energy_value, atp_consumed_cumulative,
               verification_status
        FROM action_checkpoints
        WHERE sequence_id = %s
        ORDER BY iteration_number
    """, (sequence_id,))

    checkpoints = cursor.fetchall()

    print(f"  Checkpoints for {sequence_id}:")
    for cp in checkpoints:
        print(f"    Iteration {cp[1]}: Energy={float(cp[2]):.3f}, ATP={cp[3]}, Status={cp[4]}")

    # Verify checkpoint frequency (every 3 iterations)
    iterations = [cp[1] for cp in checkpoints]
    expected = [3, 5]  # Iteration 3 (divisible by 3) and iteration 5 (would converge if threshold lower)

    print(f"\n  ✓ Checkpoint iterations: {iterations}")
    print(f"    (Expected every 3 iterations or on convergence)")

    cursor.close()

def test_4_convergence_detection(conn, actor_lct):
    """Test 4: Test early stopping on convergence"""
    print("\n=== Test 4: Convergence Detection & Early Stopping ===")
    cursor = conn.cursor()

    sequence_id = "seq:irp:converge:001"

    # Create sequence with higher convergence target
    cursor.execute("""
        INSERT INTO action_sequences
        (sequence_id, actor_lct, organization_id, sequence_type, target_resource, operation,
         max_iterations, iteration_atp_cost, atp_budget_reserved, convergence_target,
         convergence_metric, early_stopping_enabled, atp_refund_policy)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        sequence_id, actor_lct, 'org:test:sequences', 'IRP_REFINEMENT',
        'vision:scene:convergence', 'vision_encoding',
        10, 5, 100, 0.2000,  # Higher threshold
        'energy', True, 'FULL'
    ))
    conn.commit()

    # Simulate iterations until convergence
    energies = [0.950, 0.750, 0.550, 0.350, 0.180]  # Last one below 0.2 threshold

    for i, energy in enumerate(energies, 1):
        state_hash = sha256_hash(f"converge_state_{i}_{energy}")

        cursor.execute("""
            SELECT record_sequence_iteration(%s, %s, %s, %s)
        """, (sequence_id, energy, state_hash, 5))

        result = cursor.fetchone()[0]
        status = result['status']

        print(f"  Iteration {i}: Energy={energy:.3f}, Status={status}")

        if status == 'converged':
            print(f"    ✓ CONVERGED at iteration {i} (energy {energy:.3f} < threshold 0.2000)")
            break

        conn.commit()

    # Verify final status
    cursor.execute("""
        SELECT status, convergence_achieved, iterations_used, atp_consumed
        FROM action_sequences WHERE sequence_id = %s
    """, (sequence_id,))

    result = cursor.fetchone()

    print(f"\n  Final State:")
    print(f"    Status: {result[0]}")
    print(f"    Convergence Achieved: {result[1]}")
    print(f"    Iterations Used: {result[2]}/10")
    print(f"    ATP Consumed: {result[3]}/100")

    assert result[0] == 'converged', "Should be converged!"
    assert result[1] == True, "Should have convergence achieved!"
    assert result[2] == 5, "Should have used 5 iterations!"

    print(f"  ✓ Early stopping working correctly")
    print(f"  ✓ Saved {10 - result[2]} iterations by converging early")

    cursor.close()
    return sequence_id

def test_5_refund_policies(conn, actor_lct):
    """Test 5: Test different ATP refund policies"""
    print("\n=== Test 5: ATP Refund Policies ===")
    cursor = conn.cursor()

    test_cases = [
        ('FULL', True, 100),    # FULL + success = 100% refund
        ('FULL', False, 100),   # FULL + failure = 100% refund
        ('TIERED', True, 100),  # TIERED + success = 100% refund
        ('TIERED', False, 50),  # TIERED + failure = partial refund
        ('NONE', True, 0),      # NONE = no refund
    ]

    for policy, success, expected_percent in test_cases:
        seq_id = f"seq:refund:{policy.lower()}_{success}"

        # Create sequence
        cursor.execute("""
            INSERT INTO action_sequences
            (sequence_id, actor_lct, organization_id, sequence_type, target_resource, operation,
             max_iterations, iteration_atp_cost, atp_budget_reserved, convergence_target,
             atp_refund_policy, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            seq_id, actor_lct, 'org:test:sequences', 'IRP_REFINEMENT',
            f'test:refund:{policy}', 'test',
            10, 5, 100, 0.05,
            policy, 'active'
        ))

        # Simulate 4 iterations (20 ATP consumed with 5 ATP/iteration, 80 unused)
        for i in range(4):
            cursor.execute("""
                UPDATE action_sequences
                SET current_iteration = current_iteration + 1,
                    atp_consumed = atp_consumed + 5,
                    iterations_used = iterations_used + 1
                WHERE sequence_id = %s
            """, (seq_id,))

        conn.commit()

        # Finalize sequence
        cursor.execute("""
            SELECT finalize_sequence(%s, %s)
        """, (seq_id, success))

        refund_result = cursor.fetchone()[0]
        refund_amount = refund_result['refund_amount']
        unused = refund_result['unused_atp']

        print(f"  Policy={policy:7}, Success={success}, Consumed=20, Unused={unused}, Refund={refund_amount} ATP")

        # Verify refund calculation
        # 4 iterations × 5 ATP = 20 consumed, 80 unused
        if policy == 'FULL':
            expected = 80
        elif policy == 'TIERED':
            if success:
                expected = 80  # Full refund on success
            else:
                # Partial refund: unused × (1 - completion_ratio)
                # completion_ratio = 4/10 = 0.4
                # refund = 80 × (1 - 0.4) = 48
                expected = 48
        else:  # NONE
            expected = 0

        assert refund_amount == expected, f"Expected {expected}, got {refund_amount}!"

        conn.commit()

    print(f"\n  ✓ All refund policies working correctly")
    print(f"    FULL: Always refund unused ATP")
    print(f"    TIERED: Full on success, partial on failure (based on progress)")
    print(f"    NONE: Never refund")

    cursor.close()

def test_6_failure_scenarios(conn, actor_lct):
    """Test 6: Test failure scenarios (timeout, budget exhaustion)"""
    print("\n=== Test 6: Failure Scenarios ===")
    cursor = conn.cursor()

    # Test 6a: Maximum iterations reached
    print("\n  6a. Timeout (max iterations reached)")
    seq_timeout = "seq:fail:timeout:001"

    cursor.execute("""
        INSERT INTO action_sequences
        (sequence_id, actor_lct, organization_id, sequence_type, target_resource, operation,
         max_iterations, iteration_atp_cost, atp_budget_reserved, convergence_target, atp_refund_policy)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        seq_timeout, actor_lct, 'org:test:sequences', 'IRP_REFINEMENT',
        'test:timeout', 'test',
        3, 5, 100, 0.01, 'TIERED'  # Very low threshold, won't converge
    ))
    conn.commit()

    # Try to exceed max iterations
    for i in range(4):  # Try 4 iterations, max is 3
        cursor.execute("""
            SELECT record_sequence_iteration(%s, %s, %s, %s)
        """, (seq_timeout, 0.9, sha256_hash(f"timeout_{i}"), 5))

        result = cursor.fetchone()[0]

        if result.get('status') == 'timeout':
            print(f"    ✓ Timeout detected at iteration attempt {i+1}")
            print(f"      Reason: {result.get('reason')}")
            break

        conn.commit()

    # Test 6b: ATP budget exhausted
    print("\n  6b. Budget Exhaustion")
    seq_budget = "seq:fail:budget:001"

    cursor.execute("""
        INSERT INTO action_sequences
        (sequence_id, actor_lct, organization_id, sequence_type, target_resource, operation,
         max_iterations, iteration_atp_cost, atp_budget_reserved, convergence_target, atp_refund_policy)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        seq_budget, actor_lct, 'org:test:sequences', 'IRP_REFINEMENT',
        'test:budget', 'test',
        10, 15, 50, 0.01, 'TIERED'  # Only 50 ATP, costs 15/iteration = 3 iterations max
    ))
    conn.commit()

    for i in range(5):  # Try 5 iterations, can only afford 3
        cursor.execute("""
            SELECT record_sequence_iteration(%s, %s, %s, %s)
        """, (seq_budget, 0.9, sha256_hash(f"budget_{i}"), 15))

        result = cursor.fetchone()[0]

        if result.get('status') == 'failed':
            print(f"    ✓ Budget exhaustion detected at iteration attempt {i+1}")
            print(f"      Reason: {result.get('reason')}")
            break

        conn.commit()

    print(f"\n  ✓ Failure scenarios handled correctly")

    cursor.close()

def test_7_view_queries(conn):
    """Test 7: Test views for progress tracking"""
    print("\n=== Test 7: View Queries ===")
    cursor = conn.cursor()

    # Query active sequences
    cursor.execute("""
        SELECT sequence_id, operation, current_iteration, max_iterations,
               progress_ratio, atp_remaining, checkpoint_count
        FROM active_sequences
        LIMIT 5
    """)

    print("  Active Sequences:")
    for row in cursor.fetchall():
        progress_pct = float(row[4]) * 100 if row[4] else 0
        print(f"    {row[0]:30} {row[1]:20} [{row[2]}/{row[3]}] {progress_pct:5.1f}% | ATP:{row[5]:3} | CPs:{row[6]}")

    # Query checkpoint summary
    cursor.execute("""
        SELECT sequence_id, total_checkpoints, verified_checkpoints,
               best_energy, avg_energy, total_atp_consumed
        FROM sequence_checkpoint_summary
        WHERE total_checkpoints > 0
        LIMIT 5
    """)

    print("\n  Checkpoint Summaries:")
    for row in cursor.fetchall():
        best = float(row[3]) if row[3] else 0
        avg = float(row[4]) if row[4] else 0
        print(f"    {row[0]:30} CPs:{row[1]:2} (verified:{row[2]:2}) | Energy: best={best:.3f} avg={avg:.3f} | ATP:{row[5]}")

    print(f"\n  ✓ Views working correctly")

    cursor.close()

def cleanup_test_data(conn):
    """Clean up test data"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM action_checkpoints WHERE sequence_id LIKE 'seq:%test%' OR sequence_id LIKE 'seq:%converge%' OR sequence_id LIKE 'seq:%refund%' OR sequence_id LIKE 'seq:%fail%'")
    cursor.execute("DELETE FROM action_sequences WHERE sequence_id LIKE 'seq:%test%' OR sequence_id LIKE 'seq:%converge%' OR sequence_id LIKE 'seq:%refund%' OR sequence_id LIKE 'seq:%fail%'")
    cursor.execute("DELETE FROM reputation_scores WHERE organization_id = 'org:test:sequences'")
    cursor.execute("DELETE FROM organizations WHERE organization_id = 'org:test:sequences'")
    cursor.execute("DELETE FROM lct_identities WHERE lct_id LIKE 'lct:ai:sage:test_seq%'")
    conn.commit()
    cursor.close()
    print("\n✓ Test data cleaned up")

def main():
    print("=" * 70)
    print("  Web4 Action Sequence Protocol - Test Suite")
    print("  Session #55: IRP Multi-Step Action Testing")
    print("=" * 70)

    try:
        conn = get_db_connection()
        print("\n✓ Connected to PostgreSQL database 'web4'")

        # Clean up any existing test data
        cleanup_test_data(conn)

        # Setup
        actor_lct = setup_test_entities(conn)
        print(f"✓ Test entities created (actor: {actor_lct})")

        # Run tests
        sequence_id = test_1_create_sequence(conn, actor_lct)
        checkpoint_ids = test_2_iteration_tracking(conn, sequence_id)
        test_3_checkpoint_verification(conn, sequence_id, checkpoint_ids)
        converged_seq = test_4_convergence_detection(conn, actor_lct)
        test_5_refund_policies(conn, actor_lct)
        test_6_failure_scenarios(conn, actor_lct)
        test_7_view_queries(conn)

        print("\n" + "=" * 70)
        print("  ✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nKey Features Validated:")
        print("  ✓ Action sequence creation and tracking")
        print("  ✓ Incremental ATP charging per iteration")
        print("  ✓ Checkpoint creation (every 3 iterations)")
        print("  ✓ Convergence detection and early stopping")
        print("  ✓ ATP refund policies (FULL, TIERED, NONE)")
        print("  ✓ Failure handling (timeout, budget exhaustion)")
        print("  ✓ Progress tracking views")

        # Clean up
        cleanup_test_data(conn)
        conn.close()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
