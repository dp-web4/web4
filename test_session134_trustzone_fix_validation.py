#!/usr/bin/env python3
"""
Session 134: TrustZone Double-Hashing Bug Fix Validation

This script validates the fix for the critical double-hashing bug discovered in Session 133.

Bug: TrustZone provider was hashing data manually, then ECDSA library hashed it again.
Result: Sign(SHA256(SHA256(data))) instead of Sign(SHA256(data))
Impact: Software peers couldn't verify TrustZone signatures

Fix: Remove manual hashing, let ECDSA library handle it.

Test Plan:
1. Create TrustZone LCT
2. Sign data with TrustZone
3. Verify signature with SoftwareProvider
4. Verify signature with TrustZoneProvider itself
5. Test cross-verification patterns
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "ai-workspace/web4"))

from core.lct_binding import TrustZoneProvider, SoftwareProvider
from core.lct_capability_levels import EntityType


def test_trustzone_signing():
    """Test basic TrustZone signing and verification."""
    print("=" * 80)
    print("TEST 1: TrustZone Self-Verification")
    print("=" * 80)
    print()

    tz_provider = TrustZoneProvider()
    lct = tz_provider.create_lct(EntityType.AI, "test-trustzone-fix")

    print(f"Created TrustZone LCT: {lct.lct_id}")
    print(f"Capability Level: {lct.capability_level}")
    print()

    # Sign some data
    test_data = b"Session 134: TrustZone fix validation"
    print(f"Test data: {test_data.decode()}")
    print()

    sig_result = tz_provider.sign_data(lct.lct_id, test_data)

    if not sig_result.success:
        print(f"  ✗ Signing FAILED: {getattr(sig_result, 'error', 'Unknown error')}")
        return False

    print(f"Signature generated: {len(sig_result.signature)} bytes")
    print()

    # Verify with same provider
    print("Verifying with TrustZoneProvider...")
    try:
        tz_provider.verify_signature(lct.lct_id, test_data, sig_result.signature)
        print("  ✓ Self-verification PASSED")
        return True
    except Exception as e:
        print(f"  ✗ Self-verification FAILED: {e}")
        return False


def test_software_verification_of_trustzone():
    """Test that SoftwareProvider can verify TrustZone signatures (the critical fix)."""
    print()
    print("=" * 80)
    print("TEST 2: Software → TrustZone Verification (CRITICAL)")
    print("=" * 80)
    print()
    print("This is the test that FAILED in Thor Session 165 due to double-hashing bug.")
    print("After fix, software peers should be able to verify TrustZone signatures.")
    print()

    # Create TrustZone LCT
    tz_provider = TrustZoneProvider()
    tz_lct = tz_provider.create_lct(EntityType.AI, "trustzone-for-software-verification")

    print(f"TrustZone LCT: {tz_lct.lct_id}")
    print()

    # Sign data with TrustZone
    test_data = b"Software should verify this TrustZone signature"
    sig_result = tz_provider.sign_data(tz_lct.lct_id, test_data)
    signature = sig_result.signature

    print(f"Signed data with TrustZone: {len(signature)} bytes")
    print()

    # Create Software LCT (verifier)
    sw_provider = SoftwareProvider()
    sw_lct = sw_provider.create_lct(EntityType.AI, "software-verifier")

    print(f"Software LCT: {sw_lct.lct_id}")
    print()

    # Extract TrustZone public key
    tz_public_key = tz_provider.get_public_key(tz_lct.lct_id)

    print("Attempting cross-verification (Software → TrustZone)...")
    print()

    # Verify TrustZone signature with Software provider
    try:
        sw_provider.verify_signature(tz_public_key, test_data, signature)
        print("  ✓ ✓ ✓ SOFTWARE VERIFICATION OF TRUSTZONE PASSED! ✓ ✓ ✓")
        print()
        print("  This means the double-hashing bug is FIXED!")
        print("  Software peers can now verify TrustZone signatures.")
        return True
    except Exception as e:
        print(f"  ✗ ✗ ✗ SOFTWARE VERIFICATION OF TRUSTZONE FAILED! ✗ ✗ ✗")
        print(f"  Error: {e}")
        print()
        print("  The double-hashing bug may still be present.")
        return False


def test_trustzone_verification_of_software():
    """Test that TrustZone can verify Software signatures (should work)."""
    print()
    print("=" * 80)
    print("TEST 3: TrustZone → Software Verification")
    print("=" * 80)
    print()

    # Create Software LCT
    sw_provider = SoftwareProvider()
    sw_lct = sw_provider.create_lct(EntityType.AI, "software-for-trustzone-verification")

    print(f"Software LCT: {sw_lct.lct_id}")
    print()

    # Sign data with Software
    test_data = b"TrustZone should verify this software signature"
    sig_result = sw_provider.sign_data(sw_lct.lct_id, test_data)

    if not sig_result.success:
        print(f"  ✗ Signing FAILED: {getattr(sig_result, 'error', 'Unknown error')}")
        return False

    signature = sig_result.signature
    print(f"Signed data with Software: {len(signature)} bytes")
    print()

    # Create TrustZone LCT (verifier)
    tz_provider = TrustZoneProvider()
    tz_lct = tz_provider.create_lct(EntityType.AI, "trustzone-verifier")

    print(f"TrustZone LCT: {tz_lct.lct_id}")
    print()

    # Extract Software public key
    sw_public_key = sw_provider.get_public_key(sw_lct.lct_id)

    print("Attempting cross-verification (TrustZone → Software)...")
    print()

    # Verify Software signature with TrustZone provider
    try:
        tz_provider.verify_signature(sw_public_key, test_data, signature)
        print("  ✓ TrustZone verification of Software PASSED")
        return True
    except Exception as e:
        print(f"  ✗ TrustZone verification of Software FAILED: {e}")
        return False


def main():
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  SESSION 134: TRUSTZONE DOUBLE-HASHING BUG FIX VALIDATION".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    results = {}

    # Test 1: TrustZone self-verification
    results["self_verification"] = test_trustzone_signing()

    # Test 2: Software verifying TrustZone (THE CRITICAL TEST)
    results["software_verifies_trustzone"] = test_software_verification_of_trustzone()

    # Test 3: TrustZone verifying Software
    results["trustzone_verifies_software"] = test_trustzone_verification_of_software()

    # Summary
    print()
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")

    print()

    all_passed = all(results.values())

    if all_passed:
        print("╔" + "═" * 78 + "╗")
        print("║" + "  ✓ ✓ ✓ ALL TESTS PASSED! DOUBLE-HASHING BUG IS FIXED! ✓ ✓ ✓".center(78) + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        print("IMPACT:")
        print("  • Software peers can now verify TrustZone signatures")
        print("  • Cross-platform federation with TrustZone is enabled")
        print("  • Thor Session 165 issue is resolved")
        print("  • Ready for Legion ↔ Thor network testing")
    else:
        print("╔" + "═" * 78 + "╗")
        print("║" + "  ✗ ✗ ✗ SOME TESTS FAILED - INVESTIGATE ✗ ✗ ✗".center(78) + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        print("The fix may need adjustment. Review test output above.")

    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
