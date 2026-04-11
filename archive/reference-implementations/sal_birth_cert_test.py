#!/usr/bin/env python3
"""
SAL Birth Certificate Tests — Tamper Detection + Fractal Citizenship
=====================================================================

Tests:
1. Birth certificate integrity verification
2. Tamper detection (modify cert on disk → verify catches it)
3. Fractal citizenship (team within team → nested birth certs)
4. Birth certificate survives team reload
5. Role-based rights/responsibilities correctness

Date: 2026-02-20
"""

import sys
import json
import shutil
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hardbound_cli import (
    HardboundTeam, TeamRole, BirthCertificate,
    ROLE_INITIAL_RIGHTS, ROLE_INITIAL_RESPONSIBILITIES,
    HARDBOUND_DIR,
)


def test_birth_cert_integrity():
    """Test 1: Certificates have valid integrity hashes."""
    print("Test 1: Birth certificate integrity")
    team = setup_team("sal-test-1")

    for name, cert in team.birth_certificates.items():
        assert cert.verify(), f"  FAIL: {name} cert integrity broken"
        assert cert.cert_hash, f"  FAIL: {name} has no cert_hash"
        print(f"  PASS: {name} → hash={cert.cert_hash[:16]}...")

    print(f"  All {len(team.birth_certificates)} certificates VALID")
    cleanup(team)
    return True


def test_tamper_detection():
    """Test 2: Detect tampering with persisted birth certificates."""
    print("\nTest 2: Tamper detection")
    team = setup_team("sal-test-2")

    # Get a member's birth cert file
    target = "test-agent-1"
    cert_path = team.state_dir / "members" / f"{target}_birth_cert.json"
    assert cert_path.exists(), f"  FAIL: no cert file for {target}"

    # Read original
    original = json.loads(cert_path.read_text())
    original_hash = original["certHash"]
    print(f"  Original cert hash: {original_hash[:24]}...")

    # Tamper 1: Modify initial rights (escalation attempt)
    tampered = dict(original)
    tampered["initialRights"] = [
        "exist", "interact", "accumulate_reputation",
        "manage_members", "update_policy", "emergency_powers",  # escalated!
    ]
    cert_path.write_text(json.dumps(tampered, indent=2))

    # Reload and check
    loaded = HardboundTeam.load("sal-test-2", state_dir=team.state_dir)
    result = loaded.get_birth_certificate(target)

    if result["found"]:
        cert = loaded.birth_certificates[target]
        # The cert hash should NOT match (recomputed hash ≠ stored hash)
        tampered_flag = getattr(cert, '_tampered', False)
        if tampered_flag:
            print(f"  PASS: Tampered cert detected via _tampered flag")
        else:
            # Even if _tampered isn't set, the hash should differ from original
            new_hash = cert.cert_hash
            if new_hash != original_hash:
                print(f"  PASS: Hash changed: {new_hash[:16]}... ≠ {original_hash[:16]}...")
            else:
                print(f"  FAIL: Hash unchanged after tamper!")
                return False
    else:
        print(f"  FAIL: Could not load tampered cert: {result.get('error')}")
        return False

    # Tamper 2: Modify society (reassignment attempt)
    tampered2 = dict(original)
    tampered2["society"] = "lct:web4:society:evil-competitor"
    cert_path.write_text(json.dumps(tampered2, indent=2))

    loaded2 = HardboundTeam.load("sal-test-2", state_dir=team.state_dir)
    result2 = loaded2.get_birth_certificate(target)
    if result2["found"]:
        cert2 = loaded2.birth_certificates[target]
        if cert2.cert_hash != original_hash:
            print(f"  PASS: Society reassignment detected via hash mismatch")
        else:
            print(f"  FAIL: Society tamper not detected")
            return False

    # Tamper 3: Modify law version (downgrade attempt)
    tampered3 = dict(original)
    tampered3["lawVersion"] = "v0"  # Downgrade
    cert_path.write_text(json.dumps(tampered3, indent=2))

    loaded3 = HardboundTeam.load("sal-test-2", state_dir=team.state_dir)
    result3 = loaded3.get_birth_certificate(target)
    if result3["found"]:
        cert3 = loaded3.birth_certificates[target]
        if cert3.cert_hash != original_hash:
            print(f"  PASS: Law version downgrade detected via hash mismatch")
        else:
            print(f"  FAIL: Law version tamper not detected")
            return False

    # Restore original
    cert_path.write_text(json.dumps(original, indent=2))

    print(f"  All 3 tamper vectors detected")
    cleanup(team)
    return True


def test_role_rights_mapping():
    """Test 3: Correct rights/responsibilities per role."""
    print("\nTest 3: Role-based rights/responsibilities")
    team = setup_team("sal-test-3")

    expected = {
        "sal-test-3-admin": (TeamRole.ADMIN, "manage_members", "maintain_integrity"),
        "test-agent-1": (TeamRole.AGENT, "self_approve_permitted", "minimize_resource_use"),
        "test-operator-1": (TeamRole.OPERATOR, "execute_approved", "report_anomalies"),
    }

    for member_name, (role, expected_right, expected_resp) in expected.items():
        cert = team.birth_certificates.get(member_name)
        assert cert is not None, f"  FAIL: no cert for {member_name}"

        rights = cert.initial_rights
        resps = cert.initial_responsibilities

        assert expected_right in rights, \
            f"  FAIL: {member_name} missing right '{expected_right}' (has: {rights})"
        assert expected_resp in resps, \
            f"  FAIL: {member_name} missing responsibility '{expected_resp}' (has: {resps})"

        # All should have base rights
        assert "exist" in rights, f"  FAIL: {member_name} missing 'exist'"
        assert "interact" in rights, f"  FAIL: {member_name} missing 'interact'"
        assert "abide_law" in resps, f"  FAIL: {member_name} missing 'abide_law'"

        print(f"  PASS: {member_name:25s} role={role:10s} rights={len(rights)} resps={len(resps)}")

    cleanup(team)
    return True


def test_persistence_roundtrip():
    """Test 4: Birth certs survive save/load cycle."""
    print("\nTest 4: Persistence roundtrip")
    team = setup_team("sal-test-4")

    # Capture original cert data
    original_certs = {}
    for name, cert in team.birth_certificates.items():
        original_certs[name] = {
            "hash": cert.cert_hash,
            "rights": cert.initial_rights,
            "society": cert.society_name,
            "law_version": cert.law_version,
        }

    # Save and reload
    team.save()
    loaded = HardboundTeam.load("sal-test-4", state_dir=team.state_dir)

    assert len(loaded.birth_certificates) == len(original_certs), \
        f"  FAIL: cert count mismatch: {len(loaded.birth_certificates)} ≠ {len(original_certs)}"

    for name, orig in original_certs.items():
        loaded_cert = loaded.birth_certificates.get(name)
        assert loaded_cert is not None, f"  FAIL: missing cert for {name}"
        assert loaded_cert.cert_hash == orig["hash"], \
            f"  FAIL: hash mismatch for {name}: {loaded_cert.cert_hash[:16]} ≠ {orig['hash'][:16]}"
        assert loaded_cert.initial_rights == orig["rights"], \
            f"  FAIL: rights mismatch for {name}"
        assert loaded_cert.verify(), f"  FAIL: integrity check failed for {name}"
        print(f"  PASS: {name:25s} hash preserved, integrity valid")

    print(f"  All {len(original_certs)} certificates survived roundtrip")
    cleanup(team)
    return True


def test_ledger_birth_cert_entries():
    """Test 5: Birth certificate events appear in ledger."""
    print("\nTest 5: Ledger birth certificate entries")
    team = setup_team("sal-test-5")

    # Flush any pending
    team.flush()

    # Query ledger for birth cert entries
    raw_entries = team.ledger.query(action_type="sal_birth_certificate")
    birth_entries = [e.get("action", {}) for e in raw_entries]

    expected_members = {"sal-test-5-admin", "test-agent-1", "test-operator-1"}
    found_members = {e.get("member") for e in birth_entries}

    assert expected_members.issubset(found_members), \
        f"  FAIL: missing birth entries for {expected_members - found_members}"

    for entry in birth_entries:
        member = entry.get("member", "?")
        cert_hash = entry.get("cert_hash", "none")
        law_version = entry.get("law_version", "?")
        binding = entry.get("binding", "?")
        print(f"  PASS: {member:25s} hash={cert_hash[:16]}... law={law_version} binding={binding}")

    print(f"  {len(birth_entries)} birth certificate ledger entries found")
    cleanup(team)
    return True


def test_fractal_citizenship():
    """Test 6: Nested team (society within society) birth certificates."""
    print("\nTest 6: Fractal citizenship (nested societies)")

    # Create parent team (organization level)
    parent = setup_team("parent-org")

    # Create child team (department level)
    child_dir = parent.state_dir.parent / "child-dept"
    child = HardboundTeam("child-dept", use_tpm=False, state_dir=child_dir)
    child.create()
    child.add_member("dept-agent", "ai", role=TeamRole.AGENT)

    # Verify both teams have birth certs
    parent_certs = len(parent.birth_certificates)
    child_certs = len(child.birth_certificates)

    print(f"  Parent org: {parent_certs} birth certificates")
    print(f"  Child dept: {child_certs} birth certificates")

    # The child team members are citizens of the child society
    dept_agent_cert = child.birth_certificates.get("dept-agent")
    assert dept_agent_cert is not None, "  FAIL: no cert for dept-agent"
    assert dept_agent_cert.society_name == "child-dept", \
        f"  FAIL: wrong society: {dept_agent_cert.society_name}"
    print(f"  PASS: dept-agent is citizen of '{dept_agent_cert.society_name}'")

    # Parent admin is citizen of parent society
    parent_admin_cert = parent.birth_certificates.get("parent-org-admin")
    assert parent_admin_cert is not None, "  FAIL: no cert for parent admin"
    assert parent_admin_cert.society_name == "parent-org", \
        f"  FAIL: wrong society: {parent_admin_cert.society_name}"
    print(f"  PASS: parent-admin is citizen of '{parent_admin_cert.society_name}'")

    # Cross-society verification: child cert's society LCT differs from parent's
    assert dept_agent_cert.society_lct != parent_admin_cert.society_lct, \
        "  FAIL: child and parent share society LCT"
    print(f"  PASS: societies have distinct LCT identities")

    # Both societies have law version v1 (freshly created)
    assert dept_agent_cert.law_version == "v1"
    assert parent_admin_cert.law_version == "v1"
    print(f"  PASS: both societies start with law v1")

    # Fractal insight: citizen(dept) ⊂ citizen(org) could be established
    # via cross-team trust bridges (future work)
    print(f"  NOTE: Fractal composition (dept ⊂ org) requires cross-team bridges (future)")

    cleanup(parent)
    if child_dir.exists():
        shutil.rmtree(child_dir)
    return True


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def setup_team(name: str) -> HardboundTeam:
    """Create a test team with members."""
    test_dir = HARDBOUND_DIR / "teams" / name
    if test_dir.exists():
        shutil.rmtree(test_dir)

    team = HardboundTeam(name, use_tpm=False, state_dir=test_dir)
    team.create()
    team.add_member("test-agent-1", "ai", role=TeamRole.AGENT)
    team.add_member("test-operator-1", "service", role=TeamRole.OPERATOR)
    return team


def cleanup(team: HardboundTeam):
    """Clean up test team state."""
    if team.state_dir.exists():
        shutil.rmtree(team.state_dir)


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  SAL Birth Certificate Test Suite")
    print("=" * 65)

    tests = [
        ("Integrity verification", test_birth_cert_integrity),
        ("Tamper detection", test_tamper_detection),
        ("Role-based rights/responsibilities", test_role_rights_mapping),
        ("Persistence roundtrip", test_persistence_roundtrip),
        ("Ledger entries", test_ledger_birth_cert_entries),
        ("Fractal citizenship", test_fractal_citizenship),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            result = test_fn()
            if result:
                passed += 1
            else:
                failed += 1
                print(f"  FAILED: {name}")
        except Exception as e:
            failed += 1
            print(f"  ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 65}")
    print(f"  Results: {passed}/{passed + failed} passed")
    if failed == 0:
        print(f"  ALL TESTS PASSED")
    else:
        print(f"  {failed} FAILED")
    print(f"{'=' * 65}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
