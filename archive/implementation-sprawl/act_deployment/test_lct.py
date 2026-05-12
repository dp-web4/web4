#!/usr/bin/env python3
"""
Test Suite for LCT (Linked Context Token) Library

Session #47

Comprehensive tests for:
- LCT creation and parsing
- Key generation and management
- Signature creation and verification
- Format validation
- Edge cases and error handling
"""

try:
    import pytest
except ImportError:
    # Create minimal pytest stub for when pytest not available
    class PytestStub:
        @staticmethod
        def skip(msg):
            class SkipException(Exception):
                pass
            raise SkipException(msg)
        @staticmethod
        def raises(exc):
            class RaisesContext:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    return exc_type is not None and issubclass(exc_type, exc)
            return RaisesContext()
        @staticmethod
        def main(*args, **kwargs):
            print("pytest not available, use run_lct_tests.py instead")
    pytest = PytestStub()

from lct import (
    LCT,
    KeyPair,
    LCTFactory,
    LCTValidator,
    LCTContext,
    create_lct_identity,
    verify_lct_signature,
    is_valid_lct,
    InvalidLCTFormat,
    SignatureError,
    CryptoUnavailable,
    CRYPTO_AVAILABLE
)


# ============================================================================
# Test Key Generation
# ============================================================================

def test_generate_keypair_deterministic():
    """Test deterministic keypair generation"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    keypair1 = LCTFactory.generate_keypair("TestSociety", deterministic=True)
    keypair2 = LCTFactory.generate_keypair("TestSociety", deterministic=True)

    # Same input should produce same keys
    assert keypair1.private_key == keypair2.private_key
    assert keypair1.public_key == keypair2.public_key
    assert keypair1.context == keypair2.context


def test_generate_keypair_random():
    """Test random keypair generation"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    keypair1 = LCTFactory.generate_keypair("TestSociety", deterministic=False)
    keypair2 = LCTFactory.generate_keypair("TestSociety", deterministic=False)

    # Random generation should produce different keys
    assert keypair1.private_key != keypair2.private_key
    assert keypair1.public_key != keypair2.public_key


def test_keypair_hex_roundtrip():
    """Test keypair hex export and import"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    original = LCTFactory.generate_keypair("TestSociety", deterministic=True)

    # Export to hex
    private_hex, public_hex = original.to_hex()

    # Import from hex
    restored = KeyPair.from_hex(private_hex, public_hex, "TestSociety")

    # Should match
    assert original.private_key == restored.private_key
    assert original.public_key == restored.public_key
    assert original.context == restored.context


# ============================================================================
# Test LCT Generation
# ============================================================================

def test_generate_lct():
    """Test LCT generation from public key"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    keypair = LCTFactory.generate_keypair("SAGE", deterministic=True)
    lct = LCTFactory.generate_lct(keypair.public_key, "SAGE", LCTContext.SOCIETY)

    # Check LCT structure
    assert lct.protocol == "lct"
    assert lct.namespace == "web4"
    assert lct.context == "society"
    assert len(lct.identifier) == 16  # 16 hex chars
    assert lct.public_key == keypair.public_key
    assert lct.context_name == "SAGE"


def test_lct_determinism():
    """Test that same inputs produce same LCT"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    keypair1 = LCTFactory.generate_keypair("SAGE", deterministic=True)
    keypair2 = LCTFactory.generate_keypair("SAGE", deterministic=True)

    lct1 = LCTFactory.generate_lct(keypair1.public_key, "SAGE")
    lct2 = LCTFactory.generate_lct(keypair2.public_key, "SAGE")

    assert str(lct1) == str(lct2)


def test_lct_different_contexts():
    """Test LCTs with different context types"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    keypair = LCTFactory.generate_keypair("Test", deterministic=True)

    society_lct = LCTFactory.generate_lct(keypair.public_key, "Test", LCTContext.SOCIETY)
    member_lct = LCTFactory.generate_lct(keypair.public_key, "Test", LCTContext.MEMBER)
    node_lct = LCTFactory.generate_lct(keypair.public_key, "Test", LCTContext.NODE)

    assert society_lct.context == "society"
    assert member_lct.context == "member"
    assert node_lct.context == "node"

    # Same key/name, different context = same identifier but different string
    assert society_lct.identifier == member_lct.identifier == node_lct.identifier
    assert str(society_lct) != str(member_lct) != str(node_lct)


# ============================================================================
# Test LCT Creation Convenience
# ============================================================================

def test_create_lct_identity():
    """Test convenience function for creating complete identity"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("SAGE", deterministic=True)

    # Check LCT
    assert lct.protocol == "lct"
    assert lct.namespace == "web4"
    assert lct.context_name == "SAGE"

    # Check keypair
    assert keypair.context == "SAGE"
    assert len(keypair.private_key) == 32
    assert len(keypair.public_key) == 32

    # Check binding
    assert lct.public_key == keypair.public_key


# ============================================================================
# Test Signing and Verification
# ============================================================================

def test_sign_and_verify():
    """Test message signing and verification"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("SAGE", deterministic=True)
    message = b"Hello World"

    # Sign
    signature = keypair.sign(message)
    assert len(signature) == 64  # Ed25519 signature is 64 bytes

    # Verify with correct key
    is_valid = verify_lct_signature(message, signature, lct)
    assert is_valid == True

    # Verify with KeyPair.verify
    is_valid_kp = keypair.verify(message, signature)
    assert is_valid_kp == True


def test_verify_wrong_key():
    """Test verification fails with wrong key"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct1, keypair1 = create_lct_identity("SAGE", deterministic=True)
    lct2, keypair2 = create_lct_identity("Legion", deterministic=True)

    message = b"Hello World"
    signature = keypair1.sign(message)

    # Verification with wrong key should fail
    is_valid = verify_lct_signature(message, signature, lct2)
    assert is_valid == False


def test_verify_tampered_message():
    """Test verification fails with tampered message"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("SAGE", deterministic=True)
    message = b"Hello World"
    signature = keypair.sign(message)

    # Tamper with message
    tampered = b"Hello World!"

    # Verification should fail
    is_valid = verify_lct_signature(tampered, signature, lct)
    assert is_valid == False


def test_verify_tampered_signature():
    """Test verification fails with tampered signature"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("SAGE", deterministic=True)
    message = b"Hello World"
    signature = keypair.sign(message)

    # Tamper with signature
    tampered_sig = bytes([b ^ 0xFF for b in signature])

    # Verification should fail
    is_valid = verify_lct_signature(message, tampered_sig, lct)
    assert is_valid == False


# ============================================================================
# Test LCT Format Validation
# ============================================================================

def test_valid_lct_formats():
    """Test validation of valid LCT formats"""
    valid_lcts = [
        "lct:web4:society:0123456789abcdef",
        "lct:web4:member:fedcba9876543210",
        "lct:web4:node:aaaaaaaaaaaaaaaa",
        "lct:web4:service:bbbbbbbbbbbbbbbb"
    ]

    for lct_str in valid_lcts:
        assert is_valid_lct(lct_str) == True


def test_invalid_lct_formats():
    """Test validation rejects invalid LCT formats"""
    invalid_lcts = [
        "not-an-lct",
        "lct:web4:society",  # Missing identifier
        "lct:web4:society:short",  # Identifier too short
        "lct:web4:society:toolongidentifier123",  # Identifier too long
        "lct:web4:society:a1b2c3d4e5f6g7h8",  # Invalid hex char (g)
        "lct:invalid:society:0123456789abcdef",  # Invalid namespace
        "lct:web4:SOCIETY:0123456789abcdef",  # Uppercase context
        "LCT:web4:society:0123456789abcdef",  # Uppercase protocol
        "",  # Empty string
        "lct:",  # Incomplete
    ]

    for lct_str in invalid_lcts:
        assert is_valid_lct(lct_str) == False


def test_parse_valid_lct():
    """Test parsing valid LCT string"""
    lct_str = "lct:web4:society:0123456789abcdef"
    lct = LCT.parse(lct_str)

    assert lct.protocol == "lct"
    assert lct.namespace == "web4"
    assert lct.context == "society"
    assert lct.identifier == "0123456789abcdef"
    assert str(lct) == lct_str


def test_parse_invalid_lct():
    """Test parsing invalid LCT raises exception"""
    with pytest.raises(InvalidLCTFormat):
        LCT.parse("not-an-lct")

    with pytest.raises(InvalidLCTFormat):
        LCT.parse("lct:web4:society")

    with pytest.raises(InvalidLCTFormat):
        LCT.parse("lct:web4:society:invalid")


# ============================================================================
# Test LCT String Representation
# ============================================================================

def test_lct_str():
    """Test LCT string representation"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, _ = create_lct_identity("SAGE", deterministic=True)
    lct_str = str(lct)

    # Check format
    assert lct_str.startswith("lct:web4:")
    assert len(lct_str.split(':')) == 4
    assert is_valid_lct(lct_str) == True


def test_lct_equality():
    """Test LCT equality comparison"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct1, _ = create_lct_identity("SAGE", deterministic=True)
    lct2, _ = create_lct_identity("SAGE", deterministic=True)
    lct3, _ = create_lct_identity("Legion", deterministic=True)

    # Same identity should be equal
    assert lct1 == lct2

    # Different identities should not be equal
    assert lct1 != lct3

    # Equality with string
    assert lct1 == str(lct2)
    assert lct1 != "random-string"


def test_lct_hash():
    """Test LCT hashing (for use in sets/dicts)"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct1, _ = create_lct_identity("SAGE", deterministic=True)
    lct2, _ = create_lct_identity("SAGE", deterministic=True)

    # Same identity should have same hash
    assert hash(lct1) == hash(lct2)

    # Should be usable in sets
    lct_set = {lct1, lct2}
    assert len(lct_set) == 1  # Both are the same


# ============================================================================
# Test LCT Validation
# ============================================================================

def test_validate_format():
    """Test LCT format validation"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, _ = create_lct_identity("SAGE", deterministic=True)

    is_valid, error = LCTValidator.validate_format(lct)
    assert is_valid == True
    assert error is None


def test_validate_format_invalid():
    """Test format validation rejects invalid LCT"""
    invalid_lct = LCT(
        protocol="invalid",
        namespace="web4",
        context="society",
        identifier="0123456789abcdef",
        public_key=b'',
        context_name="Test"
    )

    is_valid, error = LCTValidator.validate_format(invalid_lct)
    assert is_valid == False
    assert "protocol" in error.lower()


def test_validate_binding():
    """Test LCT-keypair binding validation"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("SAGE", deterministic=True)

    is_valid, error = LCTValidator.validate_binding(lct, keypair)
    assert is_valid == True
    assert error is None


def test_validate_binding_wrong_keypair():
    """Test binding validation rejects wrong keypair"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct1, keypair1 = create_lct_identity("SAGE", deterministic=True)
    lct2, keypair2 = create_lct_identity("Legion", deterministic=True)

    # Wrong keypair should fail validation
    is_valid, error = LCTValidator.validate_binding(lct1, keypair2)
    assert is_valid == False
    assert error is not None


def test_validate_signature():
    """Test signature validation"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("SAGE", deterministic=True)
    message = b"Test message"
    signature = keypair.sign(message)

    is_valid, error = LCTValidator.validate_signature(message, signature, lct)
    assert is_valid == True
    assert error is None


def test_validate_signature_wrong_key():
    """Test signature validation fails with wrong key"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct1, keypair1 = create_lct_identity("SAGE", deterministic=True)
    lct2, keypair2 = create_lct_identity("Legion", deterministic=True)

    message = b"Test message"
    signature = keypair1.sign(message)

    # Wrong LCT should fail validation
    is_valid, error = LCTValidator.validate_signature(message, signature, lct2)
    assert is_valid == False
    assert "signature" in error.lower()


# ============================================================================
# Test Backwards Compatibility
# ============================================================================

def test_from_string_formal():
    """Test parsing formal LCT format"""
    lct_str = "lct:web4:society:0123456789abcdef"
    lct = LCTFactory.from_string(lct_str)

    assert str(lct) == lct_str
    assert lct.context == "society"


def test_from_string_legacy():
    """Test parsing legacy string format"""
    legacy_str = "lct-sage-001"
    lct = LCTFactory.from_string(legacy_str)

    # Should create LCT from legacy format
    assert lct.protocol == "lct"
    assert lct.namespace == "web4"
    assert lct.context == "society"  # Assumed for legacy
    assert lct.context_name == "sage-001"


# ============================================================================
# Test Edge Cases
# ============================================================================

def test_empty_message_signature():
    """Test signing empty message"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("SAGE", deterministic=True)
    message = b""

    signature = keypair.sign(message)
    is_valid = verify_lct_signature(message, signature, lct)

    assert is_valid == True


def test_large_message_signature():
    """Test signing large message"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("SAGE", deterministic=True)
    message = b"A" * 1_000_000  # 1 MB message

    signature = keypair.sign(message)
    is_valid = verify_lct_signature(message, signature, lct)

    assert is_valid == True


def test_special_characters_in_context():
    """Test LCT creation with special characters in context name"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("Test-Society_123", deterministic=True)

    # Should create valid LCT
    assert lct.context_name == "Test-Society_123"
    is_valid, _ = LCTValidator.validate_format(lct)
    assert is_valid == True


def test_unicode_in_context():
    """Test LCT creation with Unicode in context name"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct, keypair = create_lct_identity("SAGE🔥", deterministic=True)

    # Should create valid LCT
    assert lct.context_name == "SAGE🔥"
    is_valid, _ = LCTValidator.validate_format(lct)
    assert is_valid == True


# ============================================================================
# Test Error Handling
# ============================================================================

def test_sign_without_crypto():
    """Test signing raises error when crypto unavailable"""
    if CRYPTO_AVAILABLE:
        pytest.skip("Cryptography is available, cannot test unavailable case")

    keypair = KeyPair(b'0' * 32, b'0' * 32, "Test")

    with pytest.raises(CryptoUnavailable):
        keypair.sign(b"message")


def test_verify_without_public_key():
    """Test verification fails gracefully without public key"""
    if not CRYPTO_AVAILABLE:
        pytest.skip("Cryptography library not available")

    lct = LCT(
        protocol="lct",
        namespace="web4",
        context="society",
        identifier="0123456789abcdef",
        public_key=b'',  # No public key
        context_name="Test"
    )

    is_valid, error = LCTValidator.validate_signature(b"message", b'0' * 64, lct)
    assert is_valid == False
    assert "public key" in error.lower()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LCT Test Suite - Session #47")
    print("=" * 70)
    print()

    if not CRYPTO_AVAILABLE:
        print("⚠️  WARNING: cryptography library not available!")
        print("   Most tests will be skipped.")
        print()

    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
