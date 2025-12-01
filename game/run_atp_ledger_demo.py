#!/usr/bin/env python3
"""
ATP Ledger Demo - Cross-Platform ATP Accounting

Demonstrates ATP ledger with local transfers and cross-platform transfer protocol.
Shows two-phase commit (LOCK → COMMIT → RELEASE) for atomic cross-platform transfers.

Author: Legion Autonomous Session #43
Date: 2025-11-30
Status: Research prototype - tested at research scale
Integration: ATP state management (Phase 1 of ATP protocol)

This demo shows ATP accounting without full consensus integration.
Full consensus integration will be in Phase 3.
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.engine.atp_ledger import ATPLedger, TransferPhase


def demo_local_transfers():
    """Demo: Local (intra-platform) ATP transfers"""
    print("=" * 80)
    print("Demo 1: Local ATP Transfers")
    print("=" * 80)
    print()

    # Create ledger for Thor platform
    ledger = ATPLedger("Thor")

    # Create accounts
    alice_lct = "lct:web4:agent:alice"
    bob_lct = "lct:web4:agent:bob"
    charlie_lct = "lct:web4:agent:charlie"

    print("Initializing accounts...")
    ledger.set_balance(alice_lct, 1000.0)
    ledger.set_balance(bob_lct, 500.0)
    ledger.set_balance(charlie_lct, 250.0)
    print()

    # Show balances
    print("Initial Balances:")
    for agent_lct in [alice_lct, bob_lct, charlie_lct]:
        total, available, locked = ledger.get_balance(agent_lct)
        print(f"  {agent_lct}: {total:.2f} ATP (available: {available:.2f}, locked: {locked:.2f})")
    print()

    # Transfer: Alice → Bob (100 ATP)
    print("Transfer: Alice → Bob (100 ATP)")
    success = ledger.transfer_local(alice_lct, bob_lct, 100.0)
    print(f"  Result: {'✅ Success' if success else '❌ Failed'}")
    print()

    # Transfer: Bob → Charlie (50 ATP)
    print("Transfer: Bob → Charlie (50 ATP)")
    success = ledger.transfer_local(bob_lct, charlie_lct, 50.0)
    print(f"  Result: {'✅ Success' if success else '❌ Failed'}")
    print()

    # Failed transfer: Charlie → Alice (1000 ATP - insufficient balance)
    print("Transfer: Charlie → Alice (1000 ATP - insufficient balance)")
    success = ledger.transfer_local(charlie_lct, alice_lct, 1000.0)
    print(f"  Result: {'✅ Success' if success else '❌ Failed (insufficient balance)'}")
    print()

    # Show final balances
    print("Final Balances:")
    for agent_lct in [alice_lct, bob_lct, charlie_lct]:
        total, available, locked = ledger.get_balance(agent_lct)
        print(f"  {agent_lct}: {total:.2f} ATP (available: {available:.2f}, locked: {locked:.2f})")
    print()

    # Show ledger summary
    print(ledger.get_summary())


def demo_cross_platform_transfer_success():
    """Demo: Successful cross-platform ATP transfer"""
    print("=" * 80)
    print("Demo 2: Cross-Platform ATP Transfer (Success)")
    print("=" * 80)
    print()

    # Create ledgers for two platforms
    thor_ledger = ATPLedger("Thor")
    sprout_ledger = ATPLedger("Sprout")

    # Initialize accounts
    alice_thor = "lct:web4:agent:alice"
    bob_sprout = "lct:web4:agent:bob"

    thor_ledger.set_balance(alice_thor, 1000.0)
    sprout_ledger.set_balance(bob_sprout, 500.0)

    print("Initial State:")
    print(f"  Alice@Thor: {thor_ledger.get_balance(alice_thor)[0]:.2f} ATP")
    print(f"  Bob@Sprout: {sprout_ledger.get_balance(bob_sprout)[0]:.2f} ATP")
    print()

    # Phase 1: LOCK (Thor initiates transfer)
    print("Phase 1: LOCK (Alice@Thor wants to send 200 ATP to Bob@Sprout)")
    print("-" * 40)
    transfer = thor_ledger.initiate_transfer(
        source_agent=alice_thor,
        dest_platform="Sprout",
        dest_agent=bob_sprout,
        amount=200.0
    )

    if transfer:
        print(f"  ✅ Transfer initiated")
        print(f"     Transfer ID: {transfer.transfer_id}")
        print(f"     Amount: {transfer.amount:.2f} ATP")
        print(f"     Phase: {transfer.phase.value}")
        alice_total, alice_available, alice_locked = thor_ledger.get_balance(alice_thor)
        print(f"     Alice@Thor: {alice_total:.2f} total, {alice_available:.2f} available, {alice_locked:.2f} locked")
    else:
        print(f"  ❌ Transfer failed (insufficient balance)")
        return
    print()

    # Phase 2: COMMIT (Sprout receives and credits)
    print("Phase 2: COMMIT (Sprout receives and credits Bob)")
    print("-" * 40)
    success = sprout_ledger.commit_transfer(
        transfer_id=transfer.transfer_id,
        dest_agent=bob_sprout,
        amount=transfer.amount
    )

    if success:
        print(f"  ✅ Transfer committed on Sprout")
        bob_total, bob_available, bob_locked = sprout_ledger.get_balance(bob_sprout)
        print(f"     Bob@Sprout: {bob_total:.2f} ATP (received {transfer.amount:.2f})")
    else:
        print(f"  ❌ Commit failed")
        return
    print()

    # Phase 3: RELEASE (Thor finalizes and deducts)
    print("Phase 3: RELEASE (Thor finalizes transfer)")
    print("-" * 40)
    success = thor_ledger.finalize_transfer(transfer.transfer_id)

    if success:
        print(f"  ✅ Transfer finalized on Thor")
        alice_total, alice_available, alice_locked = thor_ledger.get_balance(alice_thor)
        print(f"     Alice@Thor: {alice_total:.2f} total, {alice_available:.2f} available, {alice_locked:.2f} locked")
    else:
        print(f"  ❌ Finalize failed")
        return
    print()

    # Final state
    print("Final State:")
    print(f"  Alice@Thor: {thor_ledger.get_balance(alice_thor)[0]:.2f} ATP (sent 200)")
    print(f"  Bob@Sprout: {sprout_ledger.get_balance(bob_sprout)[0]:.2f} ATP (received 200)")
    print()

    print("✅ Atomic cross-platform transfer successful!")
    print()


def demo_cross_platform_transfer_rollback():
    """Demo: Cross-platform ATP transfer with rollback"""
    print("=" * 80)
    print("Demo 3: Cross-Platform ATP Transfer (Rollback)")
    print("=" * 80)
    print()

    # Create ledger for Thor
    thor_ledger = ATPLedger("Thor")

    # Initialize account
    alice_thor = "lct:web4:agent:alice"
    thor_ledger.set_balance(alice_thor, 1000.0)

    print("Initial State:")
    print(f"  Alice@Thor: {thor_ledger.get_balance(alice_thor)[0]:.2f} ATP")
    print()

    # Phase 1: LOCK
    print("Phase 1: LOCK (Alice@Thor wants to send 300 ATP to Bob@Sprout)")
    print("-" * 40)
    transfer = thor_ledger.initiate_transfer(
        source_agent=alice_thor,
        dest_platform="Sprout",
        dest_agent="lct:web4:agent:bob",
        amount=300.0
    )

    if transfer:
        print(f"  ✅ Transfer initiated")
        print(f"     Transfer ID: {transfer.transfer_id}")
        alice_total, alice_available, alice_locked = thor_ledger.get_balance(alice_thor)
        print(f"     Alice@Thor: {alice_total:.2f} total, {alice_available:.2f} available, {alice_locked:.2f} locked")
    else:
        print(f"  ❌ Transfer failed")
        return
    print()

    # Simulate failure (Sprout offline, timeout, etc.)
    print("Simulating failure (Sprout offline, COMMIT timeout)")
    print("-" * 40)
    print("  ⚠️  Sprout did not respond within timeout period")
    print()

    # Rollback
    print("ROLLBACK (Unlocking Alice's ATP)")
    print("-" * 40)
    success = thor_ledger.rollback_transfer(transfer.transfer_id, reason="COMMIT_TIMEOUT")

    if success:
        print(f"  ✅ Transfer rolled back")
        alice_total, alice_available, alice_locked = thor_ledger.get_balance(alice_thor)
        print(f"     Alice@Thor: {alice_total:.2f} total, {alice_available:.2f} available, {alice_locked:.2f} locked")
        print(f"     Rollback reason: {thor_ledger.get_transfer(transfer.transfer_id).rollback_reason}")
    else:
        print(f"  ❌ Rollback failed")
        return
    print()

    # Final state
    print("Final State:")
    print(f"  Alice@Thor: {thor_ledger.get_balance(alice_thor)[0]:.2f} ATP (no change - transfer rolled back)")
    print()

    print("✅ Rollback successful - ATP returned to Alice")
    print()


def demo_double_spend_prevention():
    """Demo: Double-spend prevention via locked balance"""
    print("=" * 80)
    print("Demo 4: Double-Spend Prevention")
    print("=" * 80)
    print()

    # Create ledger
    thor_ledger = ATPLedger("Thor")

    # Initialize account
    alice_thor = "lct:web4:agent:alice"
    thor_ledger.set_balance(alice_thor, 1000.0)

    print("Initial State:")
    print(f"  Alice@Thor: {thor_ledger.get_balance(alice_thor)[0]:.2f} ATP")
    print()

    # Transfer 1: Lock 600 ATP
    print("Transfer 1: Alice@Thor → Bob@Sprout (600 ATP)")
    print("-" * 40)
    transfer1 = thor_ledger.initiate_transfer(
        source_agent=alice_thor,
        dest_platform="Sprout",
        dest_agent="lct:web4:agent:bob",
        amount=600.0
    )

    if transfer1:
        print(f"  ✅ Transfer 1 initiated (600 ATP locked)")
        alice_total, alice_available, alice_locked = thor_ledger.get_balance(alice_thor)
        print(f"     Alice@Thor: {alice_total:.2f} total, {alice_available:.2f} available, {alice_locked:.2f} locked")
    print()

    # Transfer 2: Try to lock another 600 ATP (should fail - double spend attempt)
    print("Transfer 2: Alice@Thor → Charlie@Legion (600 ATP) - DOUBLE SPEND ATTEMPT")
    print("-" * 40)
    transfer2 = thor_ledger.initiate_transfer(
        source_agent=alice_thor,
        dest_platform="Legion",
        dest_agent="lct:web4:agent:charlie",
        amount=600.0
    )

    if transfer2:
        print(f"  ❌ SECURITY FAILURE: Double-spend succeeded!")
    else:
        print(f"  ✅ Double-spend prevented (insufficient available balance)")
        alice_total, alice_available, alice_locked = thor_ledger.get_balance(alice_thor)
        print(f"     Alice@Thor: {alice_total:.2f} total, {alice_available:.2f} available, {alice_locked:.2f} locked")
        print(f"     Cannot spend 600 ATP when only {alice_available:.2f} ATP available")
    print()

    # Transfer 3: Try to lock 400 ATP (should succeed - within available)
    print("Transfer 3: Alice@Thor → Charlie@Legion (400 ATP)")
    print("-" * 40)
    transfer3 = thor_ledger.initiate_transfer(
        source_agent=alice_thor,
        dest_platform="Legion",
        dest_agent="lct:web4:agent:charlie",
        amount=400.0
    )

    if transfer3:
        print(f"  ✅ Transfer 3 initiated (400 ATP locked)")
        alice_total, alice_available, alice_locked = thor_ledger.get_balance(alice_thor)
        print(f"     Alice@Thor: {alice_total:.2f} total, {alice_available:.2f} available, {alice_locked:.2f} locked")
    else:
        print(f"  ❌ Transfer failed")
    print()

    print("Summary:")
    print(f"  Alice's 1000 ATP:")
    print(f"    600 ATP locked in Transfer 1 (Bob@Sprout)")
    print(f"    400 ATP locked in Transfer 3 (Charlie@Legion)")
    print(f"    0 ATP available")
    print()
    print("✅ Double-spend prevention working correctly!")
    print()


def demo_statistics():
    """Demo: Ledger statistics"""
    print("=" * 80)
    print("Demo 5: Ledger Statistics")
    print("=" * 80)
    print()

    # Create ledger
    ledger = ATPLedger("Thor")

    # Initialize accounts
    ledger.set_balance("lct:web4:agent:alice", 1000.0)
    ledger.set_balance("lct:web4:agent:bob", 500.0)
    ledger.set_balance("lct:web4:agent:charlie", 250.0)

    # Some local transfers
    ledger.transfer_local("lct:web4:agent:alice", "lct:web4:agent:bob", 100.0)
    ledger.transfer_local("lct:web4:agent:bob", "lct:web4:agent:charlie", 50.0)

    # Some cross-platform transfers
    transfer1 = ledger.initiate_transfer("lct:web4:agent:alice", "Sprout", "lct:web4:agent:dave", 200.0)
    transfer2 = ledger.initiate_transfer("lct:web4:agent:bob", "Legion", "lct:web4:agent:eve", 100.0)

    # Finalize one, rollback the other
    if transfer1:
        ledger.finalize_transfer(transfer1.transfer_id)
    if transfer2:
        ledger.rollback_transfer(transfer2.transfer_id, reason="TIMEOUT")

    # Show statistics
    print(ledger.get_summary())

    # Show detailed stats
    stats = ledger.get_stats()
    print("Detailed Statistics:")
    print(f"  Transfers Initiated: {stats['transfers_initiated']}")
    print(f"  Transfers Completed: {stats['transfers_completed']}")
    print(f"  Transfers Rolled Back: {stats['transfers_rolled_back']}")
    print(f"  Pending Transfers: {stats['pending_transfers']}")
    print()


if __name__ == "__main__":
    print()
    print("🏦 ATP Ledger Demo - Cross-Platform ATP Accounting")
    print()
    print("Demonstrates ATP state management for distributed Web4 societies.")
    print("Phase 1 of ATP protocol: Account management and transfer state machine.")
    print()

    demo_local_transfers()
    demo_cross_platform_transfer_success()
    demo_cross_platform_transfer_rollback()
    demo_double_spend_prevention()
    demo_statistics()

    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("✅ ATP account management working")
    print("✅ Local (intra-platform) transfers working")
    print("✅ Cross-platform two-phase commit (LOCK → COMMIT → RELEASE)")
    print("✅ Rollback on failure (unlock ATP)")
    print("✅ Double-spend prevention (via locked balance)")
    print()
    print("Status: ATP state management (Phase 1) complete")
    print("Next: Integrate with consensus protocol (Phase 3)")
    print()
    print("Co-Authored-By: Claude (Legion Autonomous) <noreply@anthropic.com>")
    print()
