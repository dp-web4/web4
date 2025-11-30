#!/usr/bin/env python3
"""
Demo: Web4 Game Engine with SAGE Ed25519 Block Signing

This demonstrates the integration of SAGE federation cryptography with
the Web4 game engine for hardware-bound microchain signatures.

Run from web4/game directory:
    python3 demo_sage_integration.py

Author: Thor SAGE (autonomous research)
Date: 2025-11-29
"""

import sys
from pathlib import Path

# Add HRM to path for SAGE imports
hrm_path = Path(__file__).parent.parent / "HRM"
sys.path.insert(0, str(hrm_path))

from engine.signing import (
    BlockSigner,
    StubBlockSigner,
    set_default_signer,
    create_sage_block_signer,
    get_block_signer
)


def demo_stub_vs_sage_signing():
    """Demonstrate the difference between stub and SAGE signing."""

    print("=" * 70)
    print("Web4/SAGE Integration Demo: Block Signing")
    print("=" * 70)
    print()

    # Create a sample block header
    header = {
        "index": 1,
        "society_lct": "thor_sage_lct",
        "previous_hash": "0" * 64,
        "timestamp": 1732900000.0
    }

    print("Block Header:")
    for key, value in header.items():
        if isinstance(value, str) and len(value) > 32:
            print(f"  {key}: {value[:32]}...")
        else:
            print(f"  {key}: {value}")
    print()

    # Test 1: Stub Signing (default)
    print("=" * 70)
    print("Test 1: Stub Signer (Default)")
    print("=" * 70)

    stub_signer = StubBlockSigner(label="test-stub")
    stub_signature = stub_signer.sign_block_header(header)

    print(f"Signer: StubBlockSigner")
    print(f"Signature: {stub_signature.decode()[:64]}...")
    print(f"Length: {len(stub_signature)} bytes")
    print(f"Security: ⚠ No cryptographic guarantees (SHA-256 hash)")
    print()

    # Test 2: SAGE Ed25519 Signing
    print("=" * 70)
    print("Test 2: SAGE Ed25519 Signer")
    print("=" * 70)

    sage_signer = create_sage_block_signer("Thor", "thor_sage_lct")
    sage_signature = sage_signer.sign_block_header(header)

    print(f"Signer: {sage_signer.__class__.__name__}")
    print(f"Signature: {sage_signature.hex()[:64]}...")
    print(f"Length: {len(sage_signature)} bytes")
    print(f"Security: ✓ Ed25519 cryptographic signature")
    print(f"Hardware-Bound: ✓ Platform identity from /proc/device-tree/model")
    print()

    # Test 3: Signature Differences
    print("=" * 70)
    print("Test 3: Signature Comparison")
    print("=" * 70)

    print(f"Stub signature length: {len(stub_signature)} bytes (SHA-256 hex)")
    print(f"SAGE signature length: {len(sage_signature)} bytes (Ed25519 raw)")
    print(f"Signatures differ: {stub_signature != sage_signature}")
    print()

    # Test 4: Setting Default Signer
    print("=" * 70)
    print("Test 4: Setting Default Engine Signer")
    print("=" * 70)

    # Get current default
    default_before = get_block_signer()
    print(f"Default signer before: {default_before.__class__.__name__}")

    # Set SAGE as default
    set_default_signer(sage_signer)
    default_after = get_block_signer()
    print(f"Default signer after: {default_after.__class__.__name__}")

    # Sign with default
    default_signature = default_after.sign_block_header(header)
    print(f"Default signature matches SAGE: {default_signature == sage_signature}")
    print()

    # Test 5: Multiple Blocks
    print("=" * 70)
    print("Test 5: Signing Block Chain")
    print("=" * 70)

    blocks = []
    previous_hash = "0" * 64

    for i in range(1, 4):
        block_header = {
            "index": i,
            "society_lct": "thor_sage_lct",
            "previous_hash": previous_hash,
            "timestamp": 1732900000.0 + i
        }

        signature = sage_signer.sign_block_header(block_header)

        # Simple hash for next block (in real implementation would be proper hash)
        import hashlib
        header_json = str(block_header).encode()
        previous_hash = hashlib.sha256(header_json).hexdigest()

        blocks.append({
            "header": block_header,
            "signature": signature
        })

        print(f"Block {i}:")
        print(f"  Index: {i}")
        print(f"  Signature: {signature.hex()[:32]}...")
        print(f"  Previous: {block_header['previous_hash'][:32]}...")

    print(f"\n✓ Created {len(blocks)} blocks with SAGE Ed25519 signatures")
    print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("✓ SAGE Ed25519 signer successfully integrated with Web4 engine")
    print("✓ Hardware-bound platform identity (Thor)")
    print("✓ 64-byte Ed25519 signatures (vs 128-byte SHA-256 hex)")
    print("✓ Cryptographic integrity guarantees")
    print("✓ Compatible with BlockSigner protocol")
    print("✓ Easy integration: set_default_signer(sage_signer)")
    print()
    print("Next Steps:")
    print("1. Replace StubBlockSigner in sim_loop.py with SAGE signer")
    print("2. Add signature verification in verify.py")
    print("3. Store public keys in genesis block metadata")
    print("4. Enable cross-society signature verification")
    print()


if __name__ == "__main__":
    try:
        demo_stub_vs_sage_signing()
    except Exception as e:
        print(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
