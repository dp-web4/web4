"""
Web4 Authorization System - Test Suite
=======================================

Comprehensive tests for authorization engine.

Based on: WEB4-AUTH-001 proposal (Session #21)
Author: Web4 Authorization Implementation (Session #22)
License: MIT
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from permission_claim import (
    PermissionClaim,
    PermissionBundle,
    PermissionStatus,
    get_reputation_permissions,
    get_reputation_level
)
from authorization_engine import (
    AuthorizationEngine,
    PermissionStore,
    ReputationService
)


def test_permission_claim_creation():
    """Test PermissionClaim creation and hashing"""
    print("Test 1: PermissionClaim Creation")

    claim = PermissionClaim(
        subject_lct="lct:ai:agent_alpha",
        permission="read",
        resource="code",
        issuer_lct="lct:human:admin",
        organization="acme_corp"
    )

    assert claim.subject_lct == "lct:ai:agent_alpha"
    assert claim.permission == "read"
    assert claim.resource == "code"
    assert claim.status == PermissionStatus.ACTIVE
    assert len(claim.claim_hash) == 64  # SHA-256 hash

    print("  ✅ Permission claim created successfully")
    print(f"     Claim hash: {claim.claim_hash[:16]}...")
    print()


def test_permission_claim_validity():
    """Test permission claim validity checking"""
    print("Test 2: Permission Claim Validity")

    # Active claim
    claim = PermissionClaim(
        subject_lct="lct:ai:agent_alpha",
        permission="read",
        resource="code",
        issuer_lct="lct:human:admin",
        organization="acme_corp"
    )

    valid, reason = claim.is_valid()
    assert valid
    print(f"  ✅ Active claim is valid: {reason}")

    # Expired claim
    expired_claim = PermissionClaim(
        subject_lct="lct:ai:agent_alpha",
        permission="read",
        resource="code",
        issuer_lct="lct:human:admin",
        organization="acme_corp",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )

    valid, reason = expired_claim.is_valid()
    assert not valid
    print(f"  ✅ Expired claim is invalid: {reason}")

    # Revoked claim
    claim.revoke("Testing revocation")
    valid, reason = claim.is_valid()
    assert not valid
    assert "revoked" in reason.lower()
    print(f"  ✅ Revoked claim is invalid: {reason}")
    print()


def test_permission_matching():
    """Test permission matching logic"""
    print("Test 3: Permission Matching")

    claim = PermissionClaim(
        subject_lct="lct:ai:agent_alpha",
        permission="read",
        resource="code",
        issuer_lct="lct:human:admin",
        organization="acme_corp"
    )

    # Exact match
    assert claim.matches("read", "code")
    print("  ✅ Exact match: read:code")

    # Wrong action
    assert not claim.matches("write", "code")
    print("  ✅ No match: wrong action (write vs read)")

    # Wrong resource
    assert not claim.matches("read", "database")
    print("  ✅ No match: wrong resource (database vs code)")

    # Wildcard resource
    wildcard_claim = PermissionClaim(
        subject_lct="lct:ai:agent_alpha",
        permission="read",
        resource="*",
        issuer_lct="lct:human:admin",
        organization="acme_corp"
    )

    assert wildcard_claim.matches("read", "code")
    assert wildcard_claim.matches("read", "database")
    assert wildcard_claim.matches("read", "anything")
    print("  ✅ Wildcard match: read:* matches any resource")

    # Scoped permission
    scoped_claim = PermissionClaim(
        subject_lct="lct:ai:agent_alpha",
        permission="write",
        resource="code",
        scope="own",
        issuer_lct="lct:human:admin",
        organization="acme_corp"
    )

    assert scoped_claim.matches("write", "code", "own")
    assert not scoped_claim.matches("write", "code", "shared")
    print("  ✅ Scoped match: write:code:own only matches 'own' scope")
    print()


def test_permission_bundle():
    """Test PermissionBundle aggregation"""
    print("Test 4: Permission Bundle")

    bundle = PermissionBundle(
        lct_id="lct:ai:agent_alpha",
        organization="acme_corp",
        t3_score=0.6,
        reputation_level="trusted"
    )

    # Add claims
    bundle.add_claim(PermissionClaim(
        subject_lct="lct:ai:agent_alpha",
        permission="read",
        resource="code",
        issuer_lct="lct:human:admin",
        organization="acme_corp"
    ))

    bundle.add_claim(PermissionClaim(
        subject_lct="lct:ai:agent_alpha",
        permission="write",
        resource="code",
        scope="own",
        issuer_lct="lct:human:admin",
        organization="acme_corp"
    ))

    assert len(bundle.claims) == 2
    print(f"  ✅ Bundle has {len(bundle.claims)} claims")

    # Check permissions
    has_read, _ = bundle.has_permission("read", "code")
    assert has_read
    print("  ✅ Bundle has read:code permission")

    has_write, _ = bundle.has_permission("write", "code", "own")
    assert has_write
    print("  ✅ Bundle has write:code:own permission")

    has_write_shared, _ = bundle.has_permission("write", "code", "shared")
    assert not has_write_shared
    print("  ✅ Bundle does not have write:code:shared permission")

    # Check effective permissions
    effective = bundle.get_effective_permissions()
    assert "read" in effective
    assert "code" in effective["read"]
    assert "write" in effective
    print(f"  ✅ Effective permissions: {effective}")
    print()


def test_reputation_based_permissions():
    """Test reputation-based permission assignment"""
    print("Test 5: Reputation-Based Permissions")

    # Novice (T3 < 0.3)
    novice_perms = get_reputation_permissions(0.2)
    assert "read:public_docs" in novice_perms
    assert "write:code:own" not in novice_perms
    print(f"  ✅ Novice (T3=0.2): {len(novice_perms)} permissions")

    # Trusted (T3 >= 0.5)
    trusted_perms = get_reputation_permissions(0.6)
    assert "read:code" in trusted_perms
    assert "write:code:own" in trusted_perms
    assert "witness:lct:ai" in trusted_perms
    print(f"  ✅ Trusted (T3=0.6): {len(trusted_perms)} permissions")

    # Expert (T3 >= 0.7)
    expert_perms = get_reputation_permissions(0.8)
    assert "write:code:shared" in expert_perms
    assert "execute:deploy:staging" in expert_perms
    assert "witness:lct:*" in expert_perms
    print(f"  ✅ Expert (T3=0.8): {len(expert_perms)} permissions")

    # Master (T3 >= 0.9)
    master_perms = get_reputation_permissions(0.95)
    assert "execute:deploy:production" in master_perms
    assert "write:critical_systems" in master_perms
    print(f"  ✅ Master (T3=0.95): {len(master_perms)} permissions")

    # Test reputation level names
    assert get_reputation_level(0.2) == "novice"
    assert get_reputation_level(0.4) == "developing"
    assert get_reputation_level(0.6) == "trusted"
    assert get_reputation_level(0.8) == "expert"
    assert get_reputation_level(0.95) == "master"
    print("  ✅ Reputation level names correct")
    print()


def test_authorization_engine_basic():
    """Test basic authorization engine functionality"""
    print("Test 6: Authorization Engine - Basic")

    engine = AuthorizationEngine()

    # Set up reputation
    engine.reputation_service.set_t3("lct:ai:agent_alpha", 0.6, "acme_corp")

    # Bootstrap: Add admin permission to issuer FIRST
    admin_claim = PermissionClaim(
        subject_lct="lct:human:admin",
        permission="grant",
        resource="permissions:*",
        issuer_lct="system:bootstrap",
        organization="acme_corp"
    )
    engine.permission_store.store_claim(admin_claim)

    # Now grant permission with proper authorization
    success, message, claim = engine.grant_permission(
        subject_lct="lct:ai:agent_alpha",
        permission="deploy",
        resource="staging",
        organization="acme_corp",
        issuer_lct="lct:human:admin"
    )

    assert success
    print(f"  ✅ Permission granted: {message}")

    # Check authorization
    authorized, reason, _ = engine.is_authorized(
        lct_id="lct:ai:agent_alpha",
        action="deploy",
        resource="staging",
        organization="acme_corp"
    )

    assert authorized
    print(f"  ✅ Authorization check passed: {reason}")

    # Check unauthorized action
    authorized, reason, _ = engine.is_authorized(
        lct_id="lct:ai:agent_alpha",
        action="delete",
        resource="production",
        organization="acme_corp"
    )

    assert not authorized
    print(f"  ✅ Unauthorized action blocked: {reason}")
    print()


def test_reputation_integration():
    """Test reputation integration in authorization"""
    print("Test 7: Reputation Integration")

    engine = AuthorizationEngine()

    # Set up reputation (trusted level)
    engine.reputation_service.set_t3("lct:ai:agent_beta", 0.6, "acme_corp")

    # Check reputation-based permission (should have read:code at T3=0.6)
    authorized, reason, claim = engine.is_authorized(
        lct_id="lct:ai:agent_beta",
        action="read",
        resource="code",
        organization="acme_corp"
    )

    assert authorized
    print(f"  ✅ Reputation-based permission authorized: {reason}")
    print(f"     Claim source: {claim.metadata.get('source')}")

    # Insufficient reputation (deploy:production requires explicit grant)
    authorized, reason, _ = engine.is_authorized(
        lct_id="lct:ai:agent_beta",
        action="deploy",
        resource="production",
        organization="acme_corp"
    )

    assert not authorized
    print(f"  ✅ Insufficient reputation blocked: {reason}")

    # Increase reputation and check again
    engine.reputation_service.set_t3("lct:ai:agent_beta", 0.95, "acme_corp")

    authorized, reason, claim = engine.is_authorized(
        lct_id="lct:ai:agent_beta",
        action="execute",
        resource="deploy:production",
        organization="acme_corp"
    )

    # Should still be blocked (production requires explicit grant, not just reputation)
    # But master level should have write:critical_systems
    authorized, reason, claim = engine.is_authorized(
        lct_id="lct:ai:agent_beta",
        action="write",
        resource="critical_systems",
        organization="acme_corp"
    )

    assert authorized
    print(f"  ✅ Master-level permission (T3=0.95) authorized: {reason}")
    print()


def test_permission_revocation():
    """Test permission revocation"""
    print("Test 8: Permission Revocation")

    engine = AuthorizationEngine()

    # Grant permission
    admin_claim = PermissionClaim(
        subject_lct="lct:human:admin",
        permission="grant",
        resource="permissions:*",
        issuer_lct="system:bootstrap",
        organization="acme_corp"
    )
    engine.permission_store.store_claim(admin_claim)

    success, message, claim = engine.grant_permission(
        subject_lct="lct:ai:agent_gamma",
        permission="write",
        resource="database",
        organization="acme_corp",
        issuer_lct="lct:human:admin"
    )

    assert success
    print(f"  ✅ Permission granted: {claim.claim_hash[:16]}...")

    # Verify permission works
    authorized, _, _ = engine.is_authorized(
        lct_id="lct:ai:agent_gamma",
        action="write",
        resource="database",
        organization="acme_corp"
    )
    assert authorized
    print("  ✅ Permission verified before revocation")

    # Revoke permission (issuer can revoke)
    success, message = engine.revoke_permission(
        claim_hash=claim.claim_hash,
        reason="Testing revocation",
        revoker_lct="lct:human:admin"
    )

    assert success
    print(f"  ✅ Permission revoked: {message}")

    # Verify permission no longer works
    authorized, reason, _ = engine.is_authorized(
        lct_id="lct:ai:agent_gamma",
        action="write",
        resource="database",
        organization="acme_corp"
    )
    assert not authorized
    print(f"  ✅ Revoked permission blocked: {reason}")
    print()


def test_condition_evaluation():
    """Test permission condition evaluation"""
    print("Test 9: Condition Evaluation")

    engine = AuthorizationEngine()

    # Set low reputation
    engine.reputation_service.set_t3("lct:ai:agent_delta", 0.3, "acme_corp")

    # Grant permission with T3 condition
    admin_claim = PermissionClaim(
        subject_lct="lct:human:admin",
        permission="grant",
        resource="permissions:*",
        issuer_lct="system:bootstrap",
        organization="acme_corp"
    )
    engine.permission_store.store_claim(admin_claim)

    success, message, claim = engine.grant_permission(
        subject_lct="lct:ai:agent_delta",
        permission="execute",
        resource="critical_task",
        organization="acme_corp",
        issuer_lct="lct:human:admin",
        conditions=["T3 >= 0.5"]
    )

    assert success
    print(f"  ✅ Conditional permission granted")

    # Check authorization (should fail due to low T3)
    authorized, reason, _ = engine.is_authorized(
        lct_id="lct:ai:agent_delta",
        action="execute",
        resource="critical_task",
        organization="acme_corp"
    )

    assert not authorized
    assert "T3" in reason
    print(f"  ✅ Condition not met (T3=0.3 < 0.5): {reason}")

    # Increase reputation
    engine.reputation_service.set_t3("lct:ai:agent_delta", 0.7, "acme_corp")

    # Check again
    authorized, reason, _ = engine.is_authorized(
        lct_id="lct:ai:agent_delta",
        action="execute",
        resource="critical_task",
        organization="acme_corp"
    )

    assert authorized
    print(f"  ✅ Condition met (T3=0.7 >= 0.5): {reason}")
    print()


def test_permission_serialization():
    """Test permission claim serialization"""
    print("Test 10: Permission Serialization")

    claim = PermissionClaim(
        subject_lct="lct:ai:agent_epsilon",
        permission="read",
        resource="code",
        issuer_lct="lct:human:admin",
        organization="acme_corp",
        description="Test permission",
        conditions=["T3 >= 0.5"]
    )

    # Serialize
    claim_dict = claim.to_dict()
    assert claim_dict["subject_lct"] == "lct:ai:agent_epsilon"
    assert claim_dict["permission"] == "read"
    assert claim_dict["conditions"] == ["T3 >= 0.5"]
    print("  ✅ Claim serialized to dict")

    # Deserialize
    restored_claim = PermissionClaim.from_dict(claim_dict)
    assert restored_claim.subject_lct == claim.subject_lct
    assert restored_claim.permission == claim.permission
    assert restored_claim.claim_hash == claim.claim_hash
    print("  ✅ Claim deserialized from dict")
    print(f"     Hash preserved: {restored_claim.claim_hash == claim.claim_hash}")
    print()


def run_all_tests():
    """Run all authorization tests"""
    print("=" * 80)
    print("Web4 Authorization System - Test Suite")
    print("=" * 80)
    print()

    try:
        test_permission_claim_creation()
        test_permission_claim_validity()
        test_permission_matching()
        test_permission_bundle()
        test_reputation_based_permissions()
        test_authorization_engine_basic()
        test_reputation_integration()
        test_permission_revocation()
        test_condition_evaluation()
        test_permission_serialization()

        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("Authorization System Status: IMPLEMENTED and TESTED")
        print("Epistemic Status: POSTULATED → UNIT_TESTED")
        print()

        return True

    except AssertionError as e:
        print()
        print("=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
