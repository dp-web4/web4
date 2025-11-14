#!/usr/bin/env python3
"""
Tests for Web4 Accountability Layer (WAL)
==========================================

Created: Session #27 (2025-11-14)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from wal import (
    WALEvent,
    WALEventType,
    WALRegistry,
    WALEnforcement,
    TrustImpact,
    Constraint,
    ConstraintType
)

sys.path.insert(0, str(Path(__file__).parent.parent / "reputation"))
from reputation_tracker import ReputationTracker, BehaviorType


def test_wal_event_creation():
    """Test basic WAL event creation"""
    print("\nTest 1: WAL Event Creation")

    trust_impact = TrustImpact(
        delta_score=-0.3,
        new_trust_state=0.2
    )

    constraints = [
        Constraint(
            constraint_type=ConstraintType.QUARANTINE,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            reason="Test quarantine"
        )
    ]

    wal_event = WALEvent.create(
        entity_lct="lct:test:entity",
        event_type=WALEventType.FRAUD_ATTEMPT,
        evidence_refs=["mpe:test123", "fipt:test456"],
        trust_impact=trust_impact,
        constraints=constraints,
        adjudicator="lct:system:test"
    )

    assert wal_event.wal_event_id.startswith("wal:")
    assert wal_event.entity_lct == "lct:test:entity"
    assert wal_event.event_type == WALEventType.FRAUD_ATTEMPT
    assert len(wal_event.evidence_refs) == 2
    assert len(wal_event.constraints) == 1
    print("  ✅ WAL event created successfully")
    print(f"     Event ID: {wal_event.wal_event_id}")


def test_constraint_expiration():
    """Test constraint expiration logic"""
    print("\nTest 2: Constraint Expiration")

    now = datetime.now(timezone.utc)

    # Active constraint (expires in future)
    active_constraint = Constraint(
        constraint_type=ConstraintType.QUARANTINE,
        expires_at=now + timedelta(days=30),
        reason="Active quarantine"
    )

    assert active_constraint.is_active(now)
    print("  ✅ Future-expiring constraint is active")

    # Expired constraint
    expired_constraint = Constraint(
        constraint_type=ConstraintType.QUARANTINE,
        expires_at=now - timedelta(days=1),
        reason="Expired quarantine"
    )

    assert not expired_constraint.is_active(now)
    print("  ✅ Past-expiring constraint is inactive")

    # Permanent constraint (no expiration)
    permanent_constraint = Constraint(
        constraint_type=ConstraintType.ACTION_BLOCK,
        reason="Permanent block"
    )

    assert permanent_constraint.is_active(now)
    print("  ✅ Constraint with no expiration is permanently active")


def test_wal_registry():
    """Test WAL registry event storage and retrieval"""
    print("\nTest 3: WAL Registry")

    registry = WALRegistry()

    # Create and record event
    wal_event = WALEvent.create(
        entity_lct="lct:test:entity1",
        event_type=WALEventType.FRAUD_ATTEMPT,
        evidence_refs=["evidence:1"],
        trust_impact=TrustImpact(-0.3, 0.2),
        constraints=[],
        adjudicator="lct:system:test"
    )

    registry.record_event(wal_event)

    # Retrieve events
    events = registry.get_events_for_entity("lct:test:entity1")
    assert len(events) == 1
    assert events[0].wal_event_id == wal_event.wal_event_id
    print("  ✅ Event recorded and retrieved")

    # Filter by event type
    fraud_events = registry.get_events_for_entity(
        "lct:test:entity1",
        event_type=WALEventType.FRAUD_ATTEMPT
    )
    assert len(fraud_events) == 1
    print("  ✅ Event filtering by type works")


def test_active_constraints_retrieval():
    """Test retrieving active constraints from registry"""
    print("\nTest 4: Active Constraints Retrieval")

    registry = WALRegistry()
    now = datetime.now(timezone.utc)

    # Event with active constraint
    active_event = WALEvent.create(
        entity_lct="lct:test:entity2",
        event_type=WALEventType.FRAUD_ATTEMPT,
        evidence_refs=[],
        trust_impact=TrustImpact(-0.3, 0.2),
        constraints=[
            Constraint(
                constraint_type=ConstraintType.QUARANTINE,
                expires_at=now + timedelta(days=30),
                reason="Active quarantine"
            )
        ],
        adjudicator="lct:system:test"
    )

    # Event with expired constraint
    expired_event = WALEvent.create(
        entity_lct="lct:test:entity2",
        event_type=WALEventType.SUSPICIOUS_ACTIVITY,
        evidence_refs=[],
        trust_impact=TrustImpact(-0.1, 0.4),
        constraints=[
            Constraint(
                constraint_type=ConstraintType.QUARANTINE,
                expires_at=now - timedelta(days=1),
                reason="Expired quarantine"
            )
        ],
        adjudicator="lct:system:test"
    )

    registry.record_event(active_event)
    registry.record_event(expired_event)

    # Get active constraints
    active_constraints = registry.get_active_constraints("lct:test:entity2")
    assert len(active_constraints) == 1
    assert active_constraints[0].reason == "Active quarantine"
    print("  ✅ Only active constraints retrieved")


def test_quarantine_enforcement():
    """Test quarantine constraint enforcement"""
    print("\nTest 5: Quarantine Enforcement")

    registry = WALRegistry()

    # Create quarantine event
    wal_event = WALEvent.create(
        entity_lct="lct:test:quarantined",
        event_type=WALEventType.FRAUD_ATTEMPT,
        evidence_refs=[],
        trust_impact=TrustImpact(-0.5, 0.0),
        constraints=[
            Constraint(
                constraint_type=ConstraintType.QUARANTINE,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                reason="Fraud attempt quarantine"
            )
        ],
        adjudicator="lct:system:test"
    )

    registry.record_event(wal_event)

    # Check quarantine blocks actions
    allowed, reason = registry.check_constraint(
        "lct:test:quarantined",
        ConstraintType.QUARANTINE
    )

    assert not allowed
    assert "quarantined" in reason.lower()
    print("  ✅ Quarantine blocks actions")
    print(f"     Reason: {reason}")


def test_transaction_value_limits():
    """Test transaction value limit enforcement"""
    print("\nTest 6: Transaction Value Limits")

    registry = WALRegistry()

    # Create event with transaction limit
    wal_event = WALEvent.create(
        entity_lct="lct:test:limited",
        event_type=WALEventType.FRAUD_ATTEMPT,
        evidence_refs=[],
        trust_impact=TrustImpact(-0.3, 0.2),
        constraints=[
            Constraint(
                constraint_type=ConstraintType.MAX_TRANSACTION_VALUE,
                value=1000.0,
                reason="Transaction limit $1,000"
            )
        ],
        adjudicator="lct:system:test"
    )

    registry.record_event(wal_event)

    # Transaction below limit should be allowed
    allowed, reason = registry.check_constraint(
        "lct:test:limited",
        ConstraintType.MAX_TRANSACTION_VALUE,
        value=500.0
    )

    assert allowed
    print("  ✅ Transaction below limit allowed ($500 < $1,000)")

    # Transaction above limit should be blocked
    allowed, reason = registry.check_constraint(
        "lct:test:limited",
        ConstraintType.MAX_TRANSACTION_VALUE,
        value=5000.0
    )

    assert not allowed
    assert "5,000" in reason
    assert "1,000" in reason
    print("  ✅ Transaction above limit blocked ($5,000 > $1,000)")
    print(f"     Reason: {reason}")


def test_wal_enforcement_fraud_recording():
    """Test WAL enforcement fraud recording"""
    print("\nTest 7: WAL Enforcement Fraud Recording")

    reputation = ReputationTracker()
    enforcement = WALEnforcement(reputation)

    entity_lct = "lct:test:fraudster"
    org = "test_org"

    # Record fraud attempt
    wal_event = enforcement.record_fraud_attempt(
        entity_lct=entity_lct,
        evidence_refs=["mpe:fraud123", "fipt:fraud456"],
        adjudicator="lct:system:test",
        organization=org,
        description="Test fraud attempt",
        quarantine_days=30,
        max_transaction_value=500.0
    )

    assert wal_event.event_type == WALEventType.FRAUD_ATTEMPT
    assert len(wal_event.constraints) == 2  # Quarantine + transaction limit
    print("  ✅ Fraud event created with constraints")

    # Check reputation was impacted
    t3 = reputation.calculate_t3(entity_lct, org)
    assert t3 < 0.5  # Should be low due to fraud penalty
    print(f"  ✅ Reputation impacted (T3={t3:.3f})")

    # Check event is in registry
    events = enforcement.wal_registry.get_events_for_entity(entity_lct)
    assert len(events) == 1
    print("  ✅ Event recorded in registry")


def test_action_authorization():
    """Test action authorization with WAL constraints"""
    print("\nTest 8: Action Authorization")

    reputation = ReputationTracker()
    enforcement = WALEnforcement(reputation)

    attacker_lct = "lct:test:attacker"
    org = "test_org"

    # Record fraud (creates quarantine)
    enforcement.record_fraud_attempt(
        entity_lct=attacker_lct,
        evidence_refs=["evidence:1"],
        adjudicator="lct:system:test",
        organization=org,
        quarantine_days=30
    )

    # Try to perform action while quarantined
    allowed, reason = enforcement.check_action_allowed(
        attacker_lct,
        "payment",
        value=1000.0,
        organization=org
    )

    assert not allowed
    assert "quarantined" in reason.lower()
    print("  ✅ Action blocked while quarantined")

    # Legitimate entity should be allowed
    legitimate_lct = "lct:test:legitimate"

    # Build some reputation
    for _ in range(5):
        reputation.record_event(
            agent_lct=legitimate_lct,
            behavior_type=BehaviorType.SUCCESSFUL_ACTION,
            organization=org
        )

    allowed, reason = enforcement.check_action_allowed(
        legitimate_lct,
        "payment",
        value=100000.0,
        organization=org
    )

    assert allowed
    print("  ✅ Legitimate entity allowed")


def test_serialization():
    """Test WAL event serialization"""
    print("\nTest 9: Serialization")

    wal_event = WALEvent.create(
        entity_lct="lct:test:entity",
        event_type=WALEventType.FRAUD_ATTEMPT,
        evidence_refs=["evidence:1", "evidence:2"],
        trust_impact=TrustImpact(-0.3, 0.2),
        constraints=[
            Constraint(
                constraint_type=ConstraintType.QUARANTINE,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                reason="Test"
            )
        ],
        adjudicator="lct:system:test",
        description="Test event"
    )

    # Convert to dict
    wal_dict = wal_event.to_dict()
    assert "wal_event_id" in wal_dict
    assert "entity_lct" in wal_dict
    assert "constraints" in wal_dict
    print("  ✅ WAL event serialized to dict")

    # Convert to JSON
    wal_json = wal_event.to_json()
    assert "wal_event_id" in wal_json
    assert "fraud_attempt" in wal_json
    print("  ✅ WAL event serialized to JSON")


def test_multiple_constraints():
    """Test multiple constraints on same entity"""
    print("\nTest 10: Multiple Constraints")

    enforcement = WALEnforcement()
    entity_lct = "lct:test:multi_constraint"
    org = "test_org"

    # First fraud attempt
    enforcement.record_fraud_attempt(
        entity_lct=entity_lct,
        evidence_refs=["fraud:1"],
        adjudicator="lct:system:test",
        organization=org,
        quarantine_days=30,
        max_transaction_value=1000.0
    )

    # Second fraud attempt (different evidence)
    enforcement.record_fraud_attempt(
        entity_lct=entity_lct,
        evidence_refs=["fraud:2"],
        adjudicator="lct:system:test",
        organization=org,
        quarantine_days=60,
        max_transaction_value=500.0
    )

    # Should have multiple events
    events = enforcement.wal_registry.get_events_for_entity(entity_lct)
    assert len(events) == 2
    print(f"  ✅ Multiple events recorded ({len(events)} total)")

    # Should have multiple active constraints
    constraints = enforcement.wal_registry.get_active_constraints(entity_lct)
    assert len(constraints) >= 2
    print(f"  ✅ Multiple active constraints ({len(constraints)} total)")


def run_all_tests():
    """Run all WAL tests"""
    print("=" * 80)
    print("Web4 WAL - Test Suite")
    print("=" * 80)

    tests = [
        test_wal_event_creation,
        test_constraint_expiration,
        test_wal_registry,
        test_active_constraints_retrieval,
        test_quarantine_enforcement,
        test_transaction_value_limits,
        test_wal_enforcement_fraud_recording,
        test_action_authorization,
        test_serialization,
        test_multiple_constraints,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n  ❌ FAILED: {test_func.__name__}")
            print(f"     Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n  ❌ ERROR: {test_func.__name__}")
            print(f"     Error: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    if failed == 0:
        print(f"✅ ALL TESTS PASSED ({passed}/{passed + failed})")
        print("=" * 80)
        print("\nWAL Implementation: VALIDATED")
        print("\nKey Capabilities Tested:")
        print("  ✅ WAL event creation and ID generation")
        print("  ✅ Constraint expiration logic")
        print("  ✅ Event registry storage and retrieval")
        print("  ✅ Active constraint filtering")
        print("  ✅ Quarantine enforcement")
        print("  ✅ Transaction value limits")
        print("  ✅ Fraud recording with reputation impact")
        print("  ✅ Action authorization checks")
        print("  ✅ Serialization (dict/JSON)")
        print("  ✅ Multiple constraint handling")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{passed + failed} passed)")
        print("=" * 80)
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
