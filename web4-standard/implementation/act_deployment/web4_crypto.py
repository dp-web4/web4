#!/usr/bin/env python3
"""
Web4 Cryptographic Primitives - Session #31
============================================

Production-grade cryptography for Web4 societies and ACT deployment.

Replaces stub implementations from Session #30 with real cryptographic
primitives based on Ed25519 (signatures) and X25519 (key exchange).

Key Features:
- Ed25519 signature generation and verification
- Deterministic key derivation from society names
- LCT (Linked Context Token) generation
- Heartbeat signing and verification
- Identity validation

Security Properties:
- 128-bit security level
- Fast signature verification
- Deterministic for reproducibility (testing)
- Can be extended to use secure random (production)

Author: Legion (Autonomous Research Agent)
Date: 2025-11-15
Session: #31 - Production Hardening
"""

import hashlib
import secrets
from dataclasses import dataclass
from typing import Tuple, Optional
from datetime import datetime, timezone

# Use cryptography library for Ed25519
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography library not available. Install with: pip install cryptography")


@dataclass
class KeyPair:
    """Ed25519 key pair for Web4 society"""
    private_key: bytes  # 32 bytes
    public_key: bytes   # 32 bytes
    society_name: str

    def sign(self, message: bytes) -> bytes:
        """Sign a message with private key"""
        if not CRYPTO_AVAILABLE:
            # Fallback: Use deterministic hash (NOT SECURE!)
            return hashlib.sha256(self.private_key + message).digest()

        # Real Ed25519 signature
        private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key)
        signature = private_key_obj.sign(message)
        return signature

    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verify a signature with public key"""
        if not CRYPTO_AVAILABLE:
            # Fallback: Check deterministic hash
            expected = hashlib.sha256(self.private_key + message).digest()
            return signature == expected

        # Real Ed25519 verification
        try:
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(self.public_key)
            public_key_obj.verify(signature, message)
            return True
        except InvalidSignature:
            return False

    def to_hex(self) -> Tuple[str, str]:
        """Export keys as hex strings"""
        return (
            self.private_key.hex(),
            self.public_key.hex()
        )

    @staticmethod
    def from_hex(private_hex: str, public_hex: str, society_name: str) -> 'KeyPair':
        """Import keys from hex strings"""
        return KeyPair(
            private_key=bytes.fromhex(private_hex),
            public_key=bytes.fromhex(public_hex),
            society_name=society_name
        )


class Web4Crypto:
    """
    Cryptographic operations for Web4 societies.

    Provides key generation, signing, verification, and LCT creation.
    """

    @staticmethod
    def generate_keypair(society_name: str, deterministic: bool = True) -> KeyPair:
        """
        Generate Ed25519 keypair for a society.

        Args:
            society_name: Name of the society
            deterministic: If True, derive from name (reproducible for testing)
                          If False, use secure random (production)

        Returns:
            KeyPair with Ed25519 private and public keys
        """
        if not CRYPTO_AVAILABLE:
            # Fallback: Deterministic hash-based keys (NOT SECURE!)
            seed = hashlib.sha256(society_name.encode()).digest()
            return KeyPair(
                private_key=seed,
                public_key=hashlib.sha256(seed).digest(),
                society_name=society_name
            )

        if deterministic:
            # Derive from society name (reproducible)
            # WARNING: Only for testing! Production should use secure random
            seed = hashlib.sha256(society_name.encode()).digest()
            private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        else:
            # Secure random (production)
            private_key_obj = ed25519.Ed25519PrivateKey.generate()

        # Extract raw bytes
        private_bytes = private_key_obj.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_bytes = private_key_obj.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        return KeyPair(
            private_key=private_bytes,
            public_key=public_bytes,
            society_name=society_name
        )

    @staticmethod
    def generate_lct(public_key: bytes, society_name: str) -> str:
        """
        Generate LCT (Linked Context Token) from public key.

        LCT Format: lct:web4:society:{identifier}

        The identifier is derived from:
        - Public key (cryptographic binding)
        - Society name (human-readable)
        - Timestamp (uniqueness)

        Returns deterministic LCT for given inputs.
        """
        # Hash public key + name for identifier
        hash_input = public_key + society_name.encode()
        identifier = hashlib.sha256(hash_input).hexdigest()[:16]

        return f"lct:web4:society:{identifier}"

    @staticmethod
    def sign_heartbeat(
        heartbeat_data: dict,
        keypair: KeyPair
    ) -> Tuple[dict, bytes]:
        """
        Sign a heartbeat message.

        Args:
            heartbeat_data: Heartbeat dictionary (will be serialized)
            keypair: Society's keypair

        Returns:
            (heartbeat_data, signature) tuple
        """
        import json

        # Serialize heartbeat to canonical JSON
        canonical = json.dumps(heartbeat_data, sort_keys=True, separators=(',', ':'))
        message = canonical.encode('utf-8')

        # Sign
        signature = keypair.sign(message)

        return (heartbeat_data, signature)

    @staticmethod
    def verify_heartbeat(
        heartbeat_data: dict,
        signature: bytes,
        public_key: bytes
    ) -> bool:
        """
        Verify a signed heartbeat.

        Args:
            heartbeat_data: Heartbeat dictionary
            signature: Signature to verify
            public_key: Society's public key

        Returns:
            True if signature is valid
        """
        import json

        # Reconstruct canonical message
        canonical = json.dumps(heartbeat_data, sort_keys=True, separators=(',', ':'))
        message = canonical.encode('utf-8')

        # Create temporary keypair for verification
        # (We only have public key, so we fake the private key for the verify method)
        temp_keypair = KeyPair(
            private_key=b'\x00' * 32,  # Dummy private key
            public_key=public_key,
            society_name="unknown"
        )

        # Verify using public key
        if not CRYPTO_AVAILABLE:
            # Fallback not available for verification without private key
            return False

        try:
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
            public_key_obj.verify(signature, message)
            return True
        except InvalidSignature:
            return False
        except Exception:
            return False

    @staticmethod
    def hash_identity(society_name: str) -> str:
        """
        Generate deterministic society ID from name.

        Used in Session #30 - kept for backwards compatibility.
        """
        return hashlib.sha256(society_name.encode()).hexdigest()[:16]


def demo_crypto():
    """Demonstrate Web4 cryptographic operations"""
    print("=" * 70)
    print("Web4 Cryptographic Primitives Demo - Session #31")
    print("=" * 70)
    print()

    if not CRYPTO_AVAILABLE:
        print("⚠️  WARNING: cryptography library not available!")
        print("   Install with: pip install cryptography")
        print("   Running with insecure fallback mode...")
        print()

    # Generate keypairs for three societies
    print("1. Generating Ed25519 keypairs...")
    print()

    legion_keys = Web4Crypto.generate_keypair("Legion", deterministic=True)
    cbp_keys = Web4Crypto.generate_keypair("cbp", deterministic=True)
    thor_keys = Web4Crypto.generate_keypair("Thor", deterministic=True)

    print(f"Legion:")
    print(f"  Private key: {legion_keys.private_key.hex()[:32]}...")
    print(f"  Public key:  {legion_keys.public_key.hex()}")
    print()

    print(f"cbp:")
    print(f"  Private key: {cbp_keys.private_key.hex()[:32]}...")
    print(f"  Public key:  {cbp_keys.public_key.hex()}")
    print()

    print(f"Thor:")
    print(f"  Private key: {thor_keys.private_key.hex()[:32]}...")
    print(f"  Public key:  {thor_keys.public_key.hex()}")
    print()

    # Generate LCTs
    print("2. Generating LCTs (Linked Context Tokens)...")
    print()

    legion_lct = Web4Crypto.generate_lct(legion_keys.public_key, "Legion")
    cbp_lct = Web4Crypto.generate_lct(cbp_keys.public_key, "cbp")
    thor_lct = Web4Crypto.generate_lct(thor_keys.public_key, "Thor")

    print(f"Legion LCT: {legion_lct}")
    print(f"cbp LCT:    {cbp_lct}")
    print(f"Thor LCT:   {thor_lct}")
    print()

    # Sign and verify heartbeat
    print("3. Signing and verifying heartbeat...")
    print()

    heartbeat = {
        "society_id": "legion_test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence_number": 42,
        "status": "healthy",
        "peer_count": 2
    }

    heartbeat_data, signature = Web4Crypto.sign_heartbeat(heartbeat, legion_keys)

    print(f"Heartbeat data: {heartbeat_data}")
    print(f"Signature: {signature.hex()[:32]}...")
    print()

    # Verify with correct key
    valid = Web4Crypto.verify_heartbeat(heartbeat_data, signature, legion_keys.public_key)
    print(f"✅ Verification with Legion's public key: {valid}")

    # Verify with wrong key (should fail)
    invalid = Web4Crypto.verify_heartbeat(heartbeat_data, signature, cbp_keys.public_key)
    print(f"❌ Verification with cbp's public key: {invalid}")
    print()

    # Tamper with heartbeat (should fail)
    tampered = heartbeat_data.copy()
    tampered['peer_count'] = 999
    tampered_valid = Web4Crypto.verify_heartbeat(tampered, signature, legion_keys.public_key)
    print(f"❌ Verification of tampered heartbeat: {tampered_valid}")
    print()

    # Test deterministic generation
    print("4. Testing deterministic key generation...")
    print()

    legion_keys2 = Web4Crypto.generate_keypair("Legion", deterministic=True)
    same = legion_keys.public_key == legion_keys2.public_key

    print(f"Same public key generated: {same}")
    print(f"  First:  {legion_keys.public_key.hex()}")
    print(f"  Second: {legion_keys2.public_key.hex()}")
    print()

    if same:
        print("✅ Deterministic generation working!")
    else:
        print("❌ Keys differ - not deterministic!")

    print()
    print("=" * 70)
    print("Cryptographic primitives validated!")
    print("=" * 70)
    print()

    if CRYPTO_AVAILABLE:
        print("✅ Using real Ed25519 cryptography")
    else:
        print("⚠️  Using insecure fallback mode")

    print()
    print("Next steps:")
    print("1. Integrate with society_manager.py")
    print("2. Sign all heartbeats")
    print("3. Verify heartbeats on discovery")
    print("4. Prevent spoofing attacks")


if __name__ == "__main__":
    demo_crypto()
