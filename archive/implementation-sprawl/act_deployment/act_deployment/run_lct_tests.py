#!/usr/bin/env python3
"""
Manual test runner for LCT library (without pytest)

Session #47
"""

from test_lct import *

def run_test(test_func, name):
    """Run a single test and report result"""
    try:
        test_func()
        print(f"✅ {name}")
        return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False

def main():
    print("=" * 70)
    print("LCT Test Suite - Session #47")
    print("=" * 70)
    print()

    if not CRYPTO_AVAILABLE:
        print("⚠️  WARNING: cryptography library not available!")
        print("   Most tests will be skipped.")
        print()

    tests = [
        (test_generate_keypair_deterministic, "Generate keypair (deterministic)"),
        (test_generate_keypair_random, "Generate keypair (random)"),
        (test_keypair_hex_roundtrip, "Keypair hex roundtrip"),
        (test_generate_lct, "Generate LCT"),
        (test_lct_determinism, "LCT determinism"),
        (test_lct_different_contexts, "LCT different contexts"),
        (test_create_lct_identity, "Create LCT identity"),
        (test_sign_and_verify, "Sign and verify"),
        (test_verify_wrong_key, "Verify wrong key"),
        (test_verify_tampered_message, "Verify tampered message"),
        (test_verify_tampered_signature, "Verify tampered signature"),
        (test_valid_lct_formats, "Valid LCT formats"),
        (test_invalid_lct_formats, "Invalid LCT formats"),
        (test_parse_valid_lct, "Parse valid LCT"),
        (test_parse_invalid_lct, "Parse invalid LCT"),
        (test_lct_str, "LCT string representation"),
        (test_lct_equality, "LCT equality"),
        (test_lct_hash, "LCT hash"),
        (test_validate_format, "Validate format"),
        (test_validate_format_invalid, "Validate format invalid"),
        (test_validate_binding, "Validate binding"),
        (test_validate_binding_wrong_keypair, "Validate binding wrong keypair"),
        (test_validate_signature, "Validate signature"),
        (test_validate_signature_wrong_key, "Validate signature wrong key"),
        (test_from_string_formal, "From string (formal)"),
        (test_from_string_legacy, "From string (legacy)"),
        (test_empty_message_signature, "Empty message signature"),
        (test_large_message_signature, "Large message signature"),
        (test_special_characters_in_context, "Special characters in context"),
        (test_unicode_in_context, "Unicode in context"),
        (test_verify_without_public_key, "Verify without public key"),
    ]

    passed = 0
    failed = 0
    skipped = 0

    print("Running tests...")
    print()

    for test_func, name in tests:
        try:
            if run_test(test_func, name):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            if "skip" in str(e).lower() or not CRYPTO_AVAILABLE:
                print(f"⏭️  {name}: SKIPPED")
                skipped += 1
            else:
                print(f"❌ {name}: {e}")
                failed += 1

    print()
    print("=" * 70)
    print("Test Results")
    print("=" * 70)
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total:   {len(tests)}")
    print()

    if failed == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"❌ {failed} tests failed")

if __name__ == "__main__":
    main()
