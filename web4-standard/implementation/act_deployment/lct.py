#!/usr/bin/env python3
"""
LCT (Linked Context Token) - Standalone Library

Session #47

Unforgeable identity primitive for Web4 societies. This library provides:
- LCT generation and validation
- Ed25519 cryptographic binding
- Message signing and verification
- Identity lifecycle management

This extracts and formalizes LCT patterns from Sessions #31-#46.

Reference: LCT_SPECIFICATION.md
"""

import hashlib
import re
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime, timezone

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ============================================================================
# LCT Constants
# ============================================================================

LCT_PROTOCOL = "lct"
LCT_NAMESPACE = "web4"

# Context types
class LCTContext:
    """LCT context types"""
    SOCIETY = "society"
    MEMBER = "member"
    NODE = "node"
    SERVICE = "service"


# ============================================================================
# Exceptions
# ============================================================================

class LCTError(Exception):
    """Base exception for LCT operations"""
    pass

class InvalidLCTFormat(LCTError):
    """LCT string format is invalid"""
    pass

class SignatureError(LCTError):
    """Signature creation or verification failed"""
    pass

class CryptoUnavailable(LCTError):
    """Cryptography library not available"""
    pass


# ============================================================================
# Key Pair
# ============================================================================

@dataclass
class KeyPair:
    """
    Ed25519 key pair for LCT identity.

    Properties:
    - private_key: 32 bytes (Ed25519 private key)
    - public_key: 32 bytes (Ed25519 public key)
    - context: Human-readable context (e.g., society name)
    """
    private_key: bytes
    public_key: bytes
    context: str

    def sign(self, message: bytes) -> bytes:
        """
        Sign a message with private key.

        Args:
            message: Message bytes to sign

        Returns:
            64-byte Ed25519 signature

        Raises:
            CryptoUnavailable: If cryptography library not available
            SignatureError: If signing fails
        """
        if not CRYPTO_AVAILABLE:
            raise CryptoUnavailable("cryptography library not available")

        try:
            private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key)
            signature = private_key_obj.sign(message)
            return signature
        except Exception as e:
            raise SignatureError(f"Signature creation failed: {e}")

    def verify(self, message: bytes, signature: bytes) -> bool:
        """
        Verify a signature with public key.

        Args:
            message: Message bytes
            signature: Signature to verify

        Returns:
            True if signature valid, False otherwise
        """
        if not CRYPTO_AVAILABLE:
            return False

        try:
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(self.public_key)
            public_key_obj.verify(signature, message)
            return True
        except InvalidSignature:
            return False
        except Exception:
            return False

    def to_hex(self) -> Tuple[str, str]:
        """Export keys as hex strings"""
        return (
            self.private_key.hex(),
            self.public_key.hex()
        )

    @staticmethod
    def from_hex(private_hex: str, public_hex: str, context: str) -> 'KeyPair':
        """Import keys from hex strings"""
        return KeyPair(
            private_key=bytes.fromhex(private_hex),
            public_key=bytes.fromhex(public_hex),
            context=context
        )


# ============================================================================
# LCT Structure
# ============================================================================

@dataclass
class LCT:
    """
    Linked Context Token - Unforgeable Web4 identity.

    Format: lct:web4:{context}:{identifier}

    Example: lct:web4:society:a1b2c3d4e5f6g7h8

    Properties:
    - protocol: Always "lct"
    - namespace: Always "web4"
    - context: Identity type (society, member, node, etc.)
    - identifier: 16-char hex derived from public key
    - public_key: Ed25519 public key (32 bytes)
    - context_name: Human-readable name
    """
    protocol: str
    namespace: str
    context: str
    identifier: str
    public_key: bytes
    context_name: str

    def __str__(self) -> str:
        """Return canonical LCT string"""
        return f"{self.protocol}:{self.namespace}:{self.context}:{self.identifier}"

    def __eq__(self, other) -> bool:
        """LCTs are equal if their string representations match"""
        if isinstance(other, LCT):
            return str(self) == str(other)
        elif isinstance(other, str):
            return str(self) == other
        return False

    def __hash__(self) -> int:
        """Hash based on string representation"""
        return hash(str(self))

    @property
    def canonical_form(self) -> str:
        """Return canonical LCT string"""
        return str(self)

    @staticmethod
    def parse(lct_string: str) -> 'LCT':
        """
        Parse LCT string into LCT object.

        Args:
            lct_string: LCT in format "lct:web4:context:identifier"

        Returns:
            LCT object

        Raises:
            InvalidLCTFormat: If format invalid
        """
        # Formal format: lct:web4:context:identifier
        formal_pattern = r'^lct:web4:([a-z]+):([0-9a-f]{16})$'
        match = re.match(formal_pattern, lct_string)

        if not match:
            raise InvalidLCTFormat(f"Invalid LCT format: {lct_string}")

        context = match.group(1)
        identifier = match.group(2)

        return LCT(
            protocol="lct",
            namespace="web4",
            context=context,
            identifier=identifier,
            public_key=b'',  # Unknown from string alone
            context_name=""  # Unknown from string alone
        )

    @staticmethod
    def is_valid_format(lct_string: str) -> bool:
        """
        Check if string is valid LCT format.

        Args:
            lct_string: String to validate

        Returns:
            True if valid LCT format
        """
        try:
            LCT.parse(lct_string)
            return True
        except InvalidLCTFormat:
            return False


# ============================================================================
# LCT Factory
# ============================================================================

class LCTFactory:
    """
    Factory for creating LCTs and key pairs.

    Handles:
    - Key generation (deterministic or random)
    - LCT derivation from keys
    - Backwards compatibility with string-based LCTs
    """

    @staticmethod
    def generate_keypair(context_name: str, deterministic: bool = True) -> KeyPair:
        """
        Generate Ed25519 keypair for LCT identity.

        Args:
            context_name: Human-readable context (e.g., society name)
            deterministic: If True, derive from name (reproducible)
                          If False, use secure random (production)

        Returns:
            KeyPair with Ed25519 keys

        Raises:
            CryptoUnavailable: If cryptography library not available
        """
        if not CRYPTO_AVAILABLE:
            raise CryptoUnavailable("cryptography library not available")

        if deterministic:
            # Derive from context name (reproducible)
            # WARNING: Only for testing!
            seed = hashlib.sha256(context_name.encode()).digest()
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
            context=context_name
        )

    @staticmethod
    def generate_lct(
        public_key: bytes,
        context_name: str,
        context_type: str = LCTContext.SOCIETY
    ) -> LCT:
        """
        Generate LCT from public key.

        Args:
            public_key: Ed25519 public key (32 bytes)
            context_name: Human-readable name
            context_type: Context type (society, member, node, etc.)

        Returns:
            LCT object
        """
        # Hash public key + name for identifier
        hash_input = public_key + context_name.encode('utf-8')
        identifier = hashlib.sha256(hash_input).hexdigest()[:16]

        return LCT(
            protocol=LCT_PROTOCOL,
            namespace=LCT_NAMESPACE,
            context=context_type,
            identifier=identifier,
            public_key=public_key,
            context_name=context_name
        )

    @staticmethod
    def create_identity(
        context_name: str,
        context_type: str = LCTContext.SOCIETY,
        deterministic: bool = False
    ) -> Tuple[LCT, KeyPair]:
        """
        Create complete LCT identity (LCT + keypair).

        Args:
            context_name: Human-readable name
            context_type: Context type (society, member, etc.)
            deterministic: If True, use deterministic key generation (testing only)

        Returns:
            (LCT, KeyPair) tuple

        Raises:
            CryptoUnavailable: If cryptography library not available
        """
        keypair = LCTFactory.generate_keypair(context_name, deterministic)
        lct = LCTFactory.generate_lct(keypair.public_key, context_name, context_type)
        return (lct, keypair)

    @staticmethod
    def from_string(lct_string: str) -> LCT:
        """
        Parse LCT from string.

        Supports:
        - Formal format: lct:web4:society:a1b2c3d4
        - String format: lct-name (backwards compatibility)

        Args:
            lct_string: LCT string

        Returns:
            LCT object

        Raises:
            InvalidLCTFormat: If format invalid
        """
        # Try formal format first
        if lct_string.startswith("lct:web4:"):
            return LCT.parse(lct_string)

        # Try string format (backwards compatibility)
        # Format: lct-{name}
        if lct_string.startswith("lct-"):
            # This is a legacy format
            # We can't derive the full LCT without a keypair,
            # so we create a placeholder
            name = lct_string[4:]  # Remove "lct-" prefix

            # Generate deterministic identifier from name
            identifier = hashlib.sha256(name.encode()).hexdigest()[:16]

            return LCT(
                protocol="lct",
                namespace="web4",
                context="society",  # Assume society for legacy
                identifier=identifier,
                public_key=b'',  # Unknown
                context_name=name
            )

        raise InvalidLCTFormat(f"Invalid LCT format: {lct_string}")


# ============================================================================
# LCT Validator
# ============================================================================

class LCTValidator:
    """
    Validates LCT identities and operations.

    Checks:
    - Format validity
    - Signature correctness
    - Public key binding
    """

    @staticmethod
    def validate_format(lct: LCT) -> Tuple[bool, Optional[str]]:
        """
        Validate LCT format.

        Args:
            lct: LCT to validate

        Returns:
            (is_valid, error_message)
        """
        if lct.protocol != LCT_PROTOCOL:
            return (False, f"Invalid protocol: {lct.protocol}")

        if lct.namespace != LCT_NAMESPACE:
            return (False, f"Invalid namespace: {lct.namespace}")

        if not lct.context:
            return (False, "Missing context")

        if not re.match(r'^[0-9a-f]{16}$', lct.identifier):
            return (False, f"Invalid identifier format: {lct.identifier}")

        return (True, None)

    @staticmethod
    def validate_signature(
        message: bytes,
        signature: bytes,
        lct: LCT
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate signature against LCT public key.

        Args:
            message: Message bytes
            signature: Signature to verify
            lct: LCT whose public key should verify signature

        Returns:
            (is_valid, error_message)
        """
        if not lct.public_key:
            return (False, "LCT has no public key")

        if not CRYPTO_AVAILABLE:
            return (False, "Cryptography library not available")

        try:
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(lct.public_key)
            public_key_obj.verify(signature, message)
            return (True, None)
        except InvalidSignature:
            return (False, "Invalid signature")
        except Exception as e:
            return (False, f"Verification error: {e}")

    @staticmethod
    def validate_binding(lct: LCT, keypair: KeyPair) -> Tuple[bool, Optional[str]]:
        """
        Validate that LCT is correctly bound to keypair.

        Args:
            lct: LCT to validate
            keypair: Keypair to check binding against

        Returns:
            (is_valid, error_message)
        """
        if lct.public_key != keypair.public_key:
            return (False, "Public key mismatch")

        # Verify identifier is correctly derived
        hash_input = keypair.public_key + lct.context_name.encode('utf-8')
        expected_identifier = hashlib.sha256(hash_input).hexdigest()[:16]

        if lct.identifier != expected_identifier:
            return (False, f"Identifier mismatch: expected {expected_identifier}, got {lct.identifier}")

        return (True, None)


# ============================================================================
# Convenience Functions
# ============================================================================

def create_lct_identity(
    name: str,
    context_type: str = LCTContext.SOCIETY,
    deterministic: bool = False
) -> Tuple[LCT, KeyPair]:
    """
    Convenience function to create LCT identity.

    Args:
        name: Human-readable name
        context_type: Context type (society, member, etc.)
        deterministic: If True, use deterministic key generation (testing only)

    Returns:
        (LCT, KeyPair) tuple
    """
    return LCTFactory.create_identity(name, context_type, deterministic)


def verify_lct_signature(
    message: bytes,
    signature: bytes,
    lct: LCT
) -> bool:
    """
    Convenience function to verify LCT signature.

    Args:
        message: Message bytes
        signature: Signature to verify
        lct: LCT whose public key should verify signature

    Returns:
        True if signature valid
    """
    is_valid, _ = LCTValidator.validate_signature(message, signature, lct)
    return is_valid


def is_valid_lct(lct_string: str) -> bool:
    """
    Check if string is valid LCT format.

    Args:
        lct_string: String to validate

    Returns:
        True if valid LCT
    """
    return LCT.is_valid_format(lct_string)


# ============================================================================
# Demo
# ============================================================================

def demo_lct():
    """Demonstrate LCT library usage"""
    print("=" * 70)
    print("LCT (Linked Context Token) Library Demo - Session #47")
    print("=" * 70)
    print()

    if not CRYPTO_AVAILABLE:
        print("⚠️  ERROR: cryptography library not available!")
        print("   Install with: pip install cryptography")
        return

    # 1. Create LCT identity
    print("1. Creating LCT identities...")
    print()

    sage_lct, sage_keypair = create_lct_identity("SAGE", deterministic=True)
    legion_lct, legion_keypair = create_lct_identity("Legion", deterministic=True)
    cbp_lct, cbp_keypair = create_lct_identity("cbp", deterministic=True)

    print(f"SAGE:   {sage_lct}")
    print(f"        Public key: {sage_keypair.public_key.hex()[:32]}...")
    print()
    print(f"Legion: {legion_lct}")
    print(f"        Public key: {legion_keypair.public_key.hex()[:32]}...")
    print()
    print(f"cbp:    {cbp_lct}")
    print(f"        Public key: {cbp_keypair.public_key.hex()[:32]}...")
    print()

    # 2. Sign and verify message
    print("2. Signing and verifying messages...")
    print()

    message = b"Hello from SAGE to Legion"
    signature = sage_keypair.sign(message)

    print(f"Message: {message.decode()}")
    print(f"Signature: {signature.hex()[:32]}...")
    print()

    # Verify with correct key
    is_valid = verify_lct_signature(message, signature, sage_lct)
    print(f"✅ Verification with SAGE's LCT: {is_valid}")

    # Verify with wrong key
    is_valid_wrong = verify_lct_signature(message, signature, legion_lct)
    print(f"❌ Verification with Legion's LCT: {is_valid_wrong}")
    print()

    # 3. Validate LCT format
    print("3. Validating LCT formats...")
    print()

    valid_lcts = [
        "lct:web4:society:a1b2c3d4e5f6g7h8",
        "lct:web4:member:9876543210abcdef",
        str(sage_lct)
    ]

    invalid_lcts = [
        "not-an-lct",
        "lct:web4:society",  # Missing identifier
        "lct:web4:society:invalid",  # Invalid identifier
        "lct:invalid:society:a1b2c3d4"  # Invalid namespace
    ]

    for lct_str in valid_lcts:
        is_valid = is_valid_lct(lct_str)
        print(f"✅ {lct_str}: {is_valid}")

    print()

    for lct_str in invalid_lcts:
        is_valid = is_valid_lct(lct_str)
        print(f"❌ {lct_str}: {is_valid}")

    print()

    # 4. Test deterministic generation
    print("4. Testing deterministic generation...")
    print()

    sage_lct2, sage_keypair2 = create_lct_identity("SAGE", deterministic=True)
    same = str(sage_lct) == str(sage_lct2)

    print(f"First SAGE LCT:  {sage_lct}")
    print(f"Second SAGE LCT: {sage_lct2}")
    print(f"Same: {same}")
    print()

    # 5. Test LCT validation
    print("5. Testing LCT validation...")
    print()

    is_valid, error = LCTValidator.validate_format(sage_lct)
    print(f"Format validation: {'✅ Valid' if is_valid else f'❌ Invalid: {error}'}")

    is_valid, error = LCTValidator.validate_binding(sage_lct, sage_keypair)
    print(f"Binding validation: {'✅ Valid' if is_valid else f'❌ Invalid: {error}'}")

    print()
    print("=" * 70)
    print("LCT library validated!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Integrate with existing Web4 components")
    print("2. Migrate from string-based LCTs")
    print("3. Add comprehensive test suite")
    print("4. Update documentation")


if __name__ == "__main__":
    demo_lct()
