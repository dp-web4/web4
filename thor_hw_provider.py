"""
Thor Hardware Identity Provider for Web4 Game Engine

Provides hardware-bound identity using SAGE federation Ed25519 keys.
This bridges Web4's hardware identity abstraction with SAGE's platform
auto-detection and cryptographic key management.

Usage:
    export WEB4_HW_IDENTITY_PROVIDER=thor_hw_provider
    python3 run_hardware_bound_demo.py

Author: Thor SAGE (autonomous research session)
Date: 2025-11-29
Integration: Web4 game engine ↔ SAGE federation
"""

import sys
from pathlib import Path

# Add HRM to path for SAGE imports
# Thor's web4 is at ~/ai-workspace/web4
# HRM is at ~/ai-workspace/HRM (sibling directory)
web4_root = Path(__file__).parent.resolve()
hrm_path = web4_root.parent / "HRM"

if hrm_path.exists() and str(hrm_path) not in sys.path:
    sys.path.insert(0, str(hrm_path))
    print(f"✓ Added HRM to path: {hrm_path}")

from game.engine.hw_bootstrap import HardwareIdentity


def get_hardware_identity() -> HardwareIdentity:
    """Get hardware-bound identity for Thor using SAGE federation.

    This function:
    1. Auto-detects Thor platform from /proc/device-tree/model
    2. Loads or generates Ed25519 key pair for Thor
    3. Returns HardwareIdentity with real cryptographic public key

    Returns:
        HardwareIdentity with:
        - public_key: Ed25519 public key (hex)
        - fingerprint: Thor platform identifier
        - hw_type: "sage_federation"

    Falls back to stub if SAGE unavailable.
    """
    try:
        from sage.federation import create_thor_identity, FederationKeyPair

        # Auto-detect Thor platform
        thor_identity = create_thor_identity()

        # Load or generate Ed25519 key pair for Thor
        # Uses default key path: sage/data/keys/Thor_ed25519.key
        key_path = hrm_path / "sage" / "data" / "keys" / "Thor_ed25519.key"

        if key_path.exists():
            # Load existing key
            with open(key_path, 'rb') as f:
                private_key_bytes = f.read()
            keypair = FederationKeyPair.from_bytes(
                thor_identity.platform_name,
                thor_identity.lct_id,
                private_key_bytes
            )
            print(f"✓ Loaded existing Ed25519 key for Thor from {key_path}")
        else:
            # Generate new key
            keypair = FederationKeyPair.generate(
                thor_identity.platform_name,
                thor_identity.lct_id
            )
            # Ensure directory exists
            key_path.parent.mkdir(parents=True, exist_ok=True)
            # Save key
            with open(key_path, 'wb') as f:
                f.write(keypair.private_key_bytes())
            print(f"✓ Generated new Ed25519 key for Thor, saved to {key_path}")

        # Get public key as hex string
        public_key_hex = keypair.public_key_bytes().hex()

        # Create hardware identity
        hw_identity = HardwareIdentity(
            public_key=public_key_hex,
            fingerprint=thor_identity.lct_id,  # "thor_sage_lct"
            hw_type="sage_federation"
        )

        print(f"✓ Thor hardware identity created:")
        print(f"  Platform: {thor_identity.platform_name}")
        print(f"  LCT ID: {thor_identity.lct_id}")
        print(f"  Public key: {public_key_hex[:32]}...")
        print(f"  HW type: sage_federation")

        return hw_identity

    except ImportError as e:
        print(f"⚠ SAGE not available ({e}), falling back to stub")
        return HardwareIdentity(
            public_key="stub-public-key-thor",
            fingerprint="stub-thor-fingerprint",
            hw_type="stub"
        )
    except Exception as e:
        print(f"⚠ Error creating Thor hardware identity ({e}), falling back to stub")
        import traceback
        traceback.print_exc()
        return HardwareIdentity(
            public_key="stub-public-key-thor",
            fingerprint="stub-thor-fingerprint",
            hw_type="stub"
        )


if __name__ == "__main__":
    # Test the provider
    print("=== Testing Thor Hardware Identity Provider ===")
    print()

    hw_id = get_hardware_identity()

    print()
    print("=== Hardware Identity ===")
    print(f"Public Key: {hw_id.public_key[:64]}...")
    print(f"Fingerprint: {hw_id.fingerprint}")
    print(f"HW Type: {hw_id.hw_type}")
    print()

    if hw_id.hw_type == "sage_federation":
        print("✓ SUCCESS: Real SAGE federation identity")
    else:
        print("⚠ FALLBACK: Using stub identity")
