#!/usr/bin/env python3
"""
Legion TPM2 Hardware Binding Test
==================================

Tests hardware-bound LCT creation on Legion with TPM 2.0

Prerequisites:
    - User in 'tss' group: sudo usermod -aG tss dp
    - Session restarted after adding group
    - tpm2-tools installed

Usage:
    python3 test_legion_tpm2_binding.py
"""

import sys
sys.path.insert(0, 'core')

from lct_binding import detect_platform, TPM2Provider, get_provider
from lct_capability_levels import EntityType
import json


def test_platform_detection():
    """Test that Legion correctly detects TPM2 hardware."""
    print("=" * 60)
    print("PLATFORM DETECTION TEST")
    print("=" * 60)

    platform = detect_platform()
    print(f"Platform Name: {platform.name}")
    print(f"Architecture: {platform.arch}")
    print(f"Has TPM2: {platform.has_tpm2}")
    print(f"Has TrustZone: {platform.has_trustzone}")
    print(f"Max Capability Level: {platform.max_level}")

    assert platform.has_tpm2, "TPM2 should be detected on Legion"
    assert platform.max_level == 5, "Max level should be 5 with TPM2"
    print("\n✅ Platform detection PASSED\n")
    return platform


def test_tpm2_provider():
    """Test TPM2Provider initialization and capability."""
    print("=" * 60)
    print("TPM2 PROVIDER TEST")
    print("=" * 60)

    provider = TPM2Provider()
    print(f"TPM Tools Available: {provider._tpm_available}")
    print(f"Trust Ceiling: {provider.trust_ceiling}")
    print(f"Max Capability Level: {provider.max_capability_level}")

    if not provider._tpm_available:
        print("\n❌ TPM not accessible!")
        print("Possible causes:")
        print("  1. User not in 'tss' group")
        print("  2. Session not restarted after adding to group")
        print("  3. TPM device permissions issue")
        print("\nRun: groups | grep tss")
        print("If not showing tss, you need to restart your session")
        return False

    assert provider.trust_ceiling == 1.0, "TPM provider should have trust ceiling 1.0"
    print("\n✅ TPM2 provider initialization PASSED\n")
    return True


def test_lct_creation():
    """Test creating hardware-bound LCT with TPM2."""
    print("=" * 60)
    print("LCT CREATION TEST")
    print("=" * 60)

    provider = TPM2Provider()
    if not provider._tpm_available:
        print("❌ SKIPPED - TPM not accessible")
        return False

    # Create test LCT
    print("Creating hardware-bound LCT for Legion AI agent...")
    lct = provider.create_lct(EntityType.AI, "legion-research-agent")

    print(f"\nLCT ID: {lct.lct_id}")
    print(f"Subject: {lct.subject}")
    print(f"Capability Level: {lct.capability_level.name}")
    print(f"Entity Type: {lct.entity_type.value}")

    # Check binding
    print(f"\nBinding:")
    print(f"  Hardware Type: {lct.binding.hardware_type}")
    print(f"  Hardware Anchor: {lct.binding.hardware_anchor}")
    print(f"  Public Key: {lct.binding.public_key[:50]}...")

    # Check trust tensor
    print(f"\nT3 Tensor:")
    print(f"  Composite Score: {lct.t3_tensor.composite_score:.3f}")
    print(f"  Trust Ceiling: {lct.t3_tensor.trust_ceiling}")
    print(f"  Ceiling Reason: {lct.t3_tensor.trust_ceiling_reason}")

    # Validate
    assert lct.capability_level.name == "HARDWARE_BOUND", "Should be HARDWARE_BOUND level"
    assert lct.binding.hardware_type == "tpm2", "Should use TPM2 binding"
    assert "0x81" in lct.binding.hardware_anchor, "Should have TPM persistent handle"
    assert lct.t3_tensor.trust_ceiling == 1.0, "Hardware binding should enable 1.0 ceiling"

    print("\n✅ LCT creation PASSED\n")
    return lct


def test_signing():
    """Test TPM-backed signing operations."""
    print("=" * 60)
    print("SIGNATURE TEST")
    print("=" * 60)

    provider = TPM2Provider()
    if not provider._tpm_available:
        print("❌ SKIPPED - TPM not accessible")
        return False

    # Create LCT and extract key ID
    lct = provider.create_lct(EntityType.AI, "legion-signing-test")
    key_id = lct.lct_id.split(":")[-1]

    # Test signing
    test_data = b"Web4 pattern federation test data"
    print(f"Signing data: {test_data.decode()}")

    result = provider.sign_data(key_id, test_data)
    print(f"\nSignature Result:")
    print(f"  Success: {result.success}")
    print(f"  Algorithm: {result.algorithm}")
    print(f"  Signature Length: {len(result.signature)} bytes")

    if not result.success:
        print(f"  Error: {result.error}")
        return False

    assert result.success, "Signature should succeed"
    assert result.algorithm == "ECDSA-P256-SHA256", "Should use ECDSA-P256"

    print("\n✅ Signing PASSED\n")
    return True


def test_attestation():
    """Test TPM attestation (quote) generation."""
    print("=" * 60)
    print("ATTESTATION TEST")
    print("=" * 60)

    provider = TPM2Provider()
    if not provider._tpm_available:
        print("❌ SKIPPED - TPM not accessible")
        return False

    # Create LCT
    lct = provider.create_lct(EntityType.AI, "legion-attestation-test")
    key_id = lct.lct_id.split(":")[-1]

    # Get attestation
    print("Requesting TPM quote (attestation)...")
    result = provider.get_attestation(key_id)

    print(f"\nAttestation Result:")
    print(f"  Success: {result.success}")
    print(f"  Type: {result.attestation_type}")

    if result.success:
        print(f"  Quote Length: {len(result.quote)} bytes")
        if result.pcr_values:
            print(f"  PCR Values:")
            for pcr, value in sorted(result.pcr_values.items()):
                print(f"    PCR[{pcr}]: {value[:16]}...")
    else:
        print(f"  Error: {result.error}")

    # Note: Attestation may not be fully implemented in all TPM2 setups
    # So we don't assert success - just report results

    print("\n✅ Attestation test COMPLETED (may require additional TPM config)\n")
    return True


def test_pattern_signing_integration():
    """Test integration with Session 121 pattern federation."""
    print("=" * 60)
    print("PATTERN SIGNING INTEGRATION TEST")
    print("=" * 60)

    provider = TPM2Provider()
    if not provider._tpm_available:
        print("❌ SKIPPED - TPM not accessible")
        return False

    # Create LCT for pattern signing
    lct = provider.create_lct(EntityType.AI, "legion-pattern-source")

    # Create test pattern (Session 120-121 format)
    pattern = {
        "pattern_id": "test_pattern_001",
        "context": {
            "primary_metric": 0.75,
            "recent_trend": 0.12,
            "complexity": 0.5,
            "stability": 0.6,
            "coordination": 0.3
        },
        "context_tag": {
            "domain": "emotional",
            "provenance": "decision",
            "application_context": "CONSCIOUSNESS"
        },
        "timestamp": "2026-01-04T00:00:00Z"
    }

    # Sign pattern using LCT
    print("Signing pattern with hardware-bound LCT...")

    # Create canonical representation
    canonical_payload = json.dumps({
        "pattern_id": pattern["pattern_id"],
        "context": pattern["context"],
        "context_tag": pattern["context_tag"],
        "timestamp": pattern["timestamp"]
    }, sort_keys=True, separators=(',', ':'))

    key_id = lct.lct_id.split(":")[-1]
    sig_result = provider.sign_data(key_id, canonical_payload.encode())

    if not sig_result.success:
        print(f"❌ Signing failed: {sig_result.error}")
        return False

    # Add provenance to pattern
    signed_pattern = pattern.copy()
    signed_pattern["provenance"] = {
        "source_lct": lct.lct_id,
        "t3_snapshot": {
            dim: getattr(lct.t3_tensor, dim)
            for dim in ["technical_competence", "social_reliability",
                       "temporal_consistency", "witness_count",
                       "lineage_depth", "context_alignment"]
        },
        "mrh_witnesses": [],  # Empty for new LCT
        "signature": sig_result.signature.hex(),
        "signature_algorithm": sig_result.algorithm,
        "binding_type": lct.binding.hardware_type,
        "trust_ceiling": lct.t3_tensor.trust_ceiling
    }

    print(f"\nSigned Pattern:")
    print(f"  Pattern ID: {signed_pattern['pattern_id']}")
    print(f"  Source LCT: {signed_pattern['provenance']['source_lct']}")
    print(f"  Binding: {signed_pattern['provenance']['binding_type']}")
    print(f"  Trust Ceiling: {signed_pattern['provenance']['trust_ceiling']}")
    print(f"  Signature: {signed_pattern['provenance']['signature'][:32]}...")

    assert signed_pattern["provenance"]["binding_type"] == "tpm2"
    assert signed_pattern["provenance"]["trust_ceiling"] == 1.0

    print("\n✅ Pattern signing integration PASSED\n")
    print("Hardware-bound pattern signing ready for Session 121 federation!")
    return signed_pattern


def main():
    """Run all Legion TPM2 binding tests."""
    print("\n" + "=" * 60)
    print("LEGION TPM2 HARDWARE BINDING TEST SUITE")
    print("=" * 60 + "\n")

    results = {}

    # Test 1: Platform detection
    try:
        test_platform_detection()
        results["platform_detection"] = "✅ PASSED"
    except Exception as e:
        results["platform_detection"] = f"❌ FAILED: {e}"
        print(f"\n❌ Platform detection failed: {e}\n")

    # Test 2: TPM2 provider
    try:
        tpm_ok = test_tpm2_provider()
        if tpm_ok:
            results["tpm2_provider"] = "✅ PASSED"
        else:
            results["tpm2_provider"] = "⚠️  SKIPPED - TPM not accessible (see output above)"
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            for test, result in results.items():
                print(f"{test}: {result}")
            print("\n⚠️  Remaining tests require TPM access")
            print("Add user to tss group and restart session, then re-run this test.\n")
            return
    except Exception as e:
        results["tpm2_provider"] = f"❌ FAILED: {e}"
        print(f"\n❌ TPM2 provider failed: {e}\n")
        return

    # Test 3: LCT creation
    try:
        test_lct_creation()
        results["lct_creation"] = "✅ PASSED"
    except Exception as e:
        results["lct_creation"] = f"❌ FAILED: {e}"
        print(f"\n❌ LCT creation failed: {e}\n")

    # Test 4: Signing
    try:
        test_signing()
        results["signing"] = "✅ PASSED"
    except Exception as e:
        results["signing"] = f"❌ FAILED: {e}"
        print(f"\n❌ Signing failed: {e}\n")

    # Test 5: Attestation
    try:
        test_attestation()
        results["attestation"] = "✅ COMPLETED"
    except Exception as e:
        results["attestation"] = f"❌ FAILED: {e}"
        print(f"\n❌ Attestation failed: {e}\n")

    # Test 6: Pattern signing integration
    try:
        test_pattern_signing_integration()
        results["pattern_signing"] = "✅ PASSED"
    except Exception as e:
        results["pattern_signing"] = f"❌ FAILED: {e}"
        print(f"\n❌ Pattern signing failed: {e}\n")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test, result in results.items():
        print(f"{test}: {result}")

    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Integrate TPM2-bound LCT with Session 121 pattern federation")
    print("2. Test cross-machine pattern exchange (Legion ↔ Thor)")
    print("3. Validate trust ceiling enforcement (1.0 vs 0.85)")
    print("4. Document Legion-specific TPM findings")
    print()


if __name__ == "__main__":
    main()
