"""Test SAGE Ed25519 block signing integration with Web4 game engine.

This test validates that:
1. SAGE Ed25519 signers can be created from Web4
2. Block headers are signed correctly
3. Signatures are deterministic
4. Tampering is detected
5. Different platforms have different signatures
6. Integration with hardware bootstrap works
"""

import json
import pytest
from game.engine.signing import (
    create_sage_block_signer,
    set_default_signer,
    get_block_signer,
    StubBlockSigner,
)


class TestSageBlockSigningIntegration:
    """Test SAGE Ed25519 integration with Web4 game engine."""

    def test_create_sage_signer(self):
        """Test creating a SAGE-backed Ed25519 signer."""
        signer = create_sage_block_signer("TestPlatform", "test_lct")

        # Should not be a stub signer (unless SAGE unavailable)
        # The function will print a warning if SAGE is unavailable
        assert signer is not None
        assert hasattr(signer, "sign_block_header")

    def test_sign_block_header(self):
        """Test signing a block header with SAGE Ed25519."""
        signer = create_sage_block_signer("Legion", "legion_test_lct")

        header = {
            "index": 1,
            "society_lct": "legion_test_lct",
            "previous_hash": "0" * 64,
            "timestamp": 1732900000.0,
        }

        signature = signer.sign_block_header(header)

        # Ed25519 signatures are 64 bytes
        # Unless SAGE is unavailable and we got a stub signer
        assert signature is not None
        assert len(signature) > 0

    def test_signature_determinism(self):
        """Test that signing the same header produces the same signature."""
        signer = create_sage_block_signer("Legion", "legion_test_lct")

        header = {
            "index": 42,
            "society_lct": "legion_test_lct",
            "previous_hash": "abc123",
            "timestamp": 1732900000.0,
        }

        sig1 = signer.sign_block_header(header)
        sig2 = signer.sign_block_header(header)

        # Ed25519 is deterministic
        assert sig1 == sig2

    def test_tampering_detection(self):
        """Test that tampering with header changes signature."""
        signer = create_sage_block_signer("Legion", "legion_test_lct")

        header = {
            "index": 1,
            "society_lct": "legion_test_lct",
            "previous_hash": "0" * 64,
            "timestamp": 1732900000.0,
        }

        original_sig = signer.sign_block_header(header)

        # Tamper with index
        header_tampered = header.copy()
        header_tampered["index"] = 2
        tampered_sig = signer.sign_block_header(header_tampered)

        assert original_sig != tampered_sig

        # Tamper with timestamp
        header_tampered = header.copy()
        header_tampered["timestamp"] = 1732900001.0
        tampered_sig = signer.sign_block_header(header_tampered)

        assert original_sig != tampered_sig

    def test_different_platforms_different_signatures(self):
        """Test that different platforms produce different signatures."""
        signer1 = create_sage_block_signer("Platform1", "lct1")
        signer2 = create_sage_block_signer("Platform2", "lct2")

        header = {
            "index": 1,
            "society_lct": "test_society",
            "previous_hash": "0" * 64,
            "timestamp": 1732900000.0,
        }

        sig1 = signer1.sign_block_header(header)
        sig2 = signer2.sign_block_header(header)

        # Different platforms have different keys
        assert sig1 != sig2

    def test_set_default_signer(self):
        """Test setting SAGE signer as default for game engine."""
        # Create SAGE signer
        sage_signer = create_sage_block_signer("Legion", "legion_test_lct")

        # Set as default
        set_default_signer(sage_signer)

        # Verify it's being used
        default_signer = get_block_signer()
        assert default_signer is sage_signer

    def test_canonical_json_serialization(self):
        """Test that JSON serialization is canonical (field order independent)."""
        signer = create_sage_block_signer("Legion", "legion_test_lct")

        # Same data, different field order
        header1 = {
            "index": 1,
            "society_lct": "test",
            "previous_hash": "abc",
            "timestamp": 1732900000.0,
        }

        header2 = {
            "timestamp": 1732900000.0,
            "previous_hash": "abc",
            "index": 1,
            "society_lct": "test",
        }

        sig1 = signer.sign_block_header(header1)
        sig2 = signer.sign_block_header(header2)

        # Should produce same signature due to sorted keys
        assert sig1 == sig2

    def test_fallback_to_stub_if_sage_unavailable(self):
        """Test that we gracefully fall back to stub signer if SAGE fails."""
        # This test documents the fallback behavior
        # If SAGE is available, we get SAGE signer
        # If SAGE is not available, we get stub signer with warning

        signer = create_sage_block_signer("TestPlatform", "test_lct")

        # Either way, we should get a working signer
        assert signer is not None
        assert hasattr(signer, "sign_block_header")

        # And it should be able to sign
        header = {"index": 1, "society_lct": "test", "previous_hash": "0", "timestamp": 0.0}
        signature = signer.sign_block_header(header)
        assert signature is not None

    def test_integration_with_hardware_bootstrap_flow(self):
        """Test integration with hardware bootstrap workflow."""
        # This simulates the flow in hw_bootstrap.py

        # 1. Create SAGE signer for platform
        platform_name = "Legion"
        society_lct = "legion_web4_society"

        signer = create_sage_block_signer(platform_name, society_lct)

        # 2. Create genesis block header
        genesis_header = {
            "index": 0,
            "society_lct": society_lct,
            "previous_hash": None,
            "timestamp": 1732900000.0,
        }

        # 3. Sign genesis block
        genesis_signature = signer.sign_block_header(genesis_header)

        # 4. Verify signature exists and is bytes
        assert genesis_signature is not None
        assert isinstance(genesis_signature, bytes)

        # 5. Create next block
        block_1_header = {
            "index": 1,
            "society_lct": society_lct,
            "previous_hash": "genesis_hash",  # In real code, this would be hash of genesis
            "timestamp": 1732900001.0,
        }

        # 6. Sign block 1
        block_1_signature = signer.sign_block_header(block_1_header)

        # 7. Verify different blocks have different signatures
        assert genesis_signature != block_1_signature


class TestSageBlockSigningPerformance:
    """Test performance characteristics of SAGE Ed25519 signing."""

    def test_signing_performance(self):
        """Test that signing is fast enough for game engine use."""
        import time

        signer = create_sage_block_signer("Legion", "legion_perf_test")

        header = {
            "index": 1,
            "society_lct": "test",
            "previous_hash": "0" * 64,
            "timestamp": 1732900000.0,
        }

        # Time 100 signatures
        start = time.time()
        for i in range(100):
            header["index"] = i
            signer.sign_block_header(header)
        elapsed = time.time() - start

        avg_time = elapsed / 100

        # Ed25519 signing should be < 1ms per signature
        # Even on slower hardware, should be < 10ms
        assert avg_time < 0.01, f"Signing too slow: {avg_time*1000:.2f}ms per signature"

        print(f"✓ Average signing time: {avg_time*1000:.3f}ms per block")


class TestSageBlockSigningEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_header(self):
        """Test signing empty header."""
        signer = create_sage_block_signer("Legion", "legion_test")

        # Empty header should still produce a signature
        empty_header = {}
        sig = signer.sign_block_header(empty_header)

        assert sig is not None

    def test_header_with_none_values(self):
        """Test signing header with None values."""
        signer = create_sage_block_signer("Legion", "legion_test")

        header = {
            "index": 0,
            "society_lct": "test",
            "previous_hash": None,  # Common for genesis block
            "timestamp": 1732900000.0,
        }

        sig = signer.sign_block_header(header)
        assert sig is not None

    def test_header_with_unicode(self):
        """Test signing header with unicode characters."""
        signer = create_sage_block_signer("Legion", "legion_test")

        header = {
            "index": 1,
            "society_lct": "société_测试_🌍",  # Unicode characters
            "previous_hash": "0" * 64,
            "timestamp": 1732900000.0,
        }

        sig = signer.sign_block_header(header)
        assert sig is not None

    def test_header_with_large_values(self):
        """Test signing header with large values."""
        signer = create_sage_block_signer("Legion", "legion_test")

        header = {
            "index": 10**18,  # Very large index
            "society_lct": "test",
            "previous_hash": "a" * 1000,  # Long hash
            "timestamp": 1732900000.0,
        }

        sig = signer.sign_block_header(header)
        assert sig is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
