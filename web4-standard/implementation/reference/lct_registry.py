"""
Web4 LCT Registry
================

Linked Context Token (LCT) identity management system.
Handles minting, storage, verification, and lifecycle of Web4 identities.

Key Concepts:
- LCTs are unforgeable digital identities
- Each entity gets exactly one LCT per society
- Birth certificates prove society membership
- Hardware binding (future) prevents credential theft
- Public/private key pairs for signing
- Immutable ledger (stub) for permanent records

Design Philosophy:
- Identity is sacred - no duplicates, no forgery
- Society witnesses all births
- Hardware binding prevents identity theft
- Cryptographic proof for all operations
- Audit trail for compliance
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import time
import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


class EntityType(Enum):
    """Types of entities that can have LCTs"""
    HUMAN = "HUMAN"
    AI = "AI"
    ORGANIZATION = "ORGANIZATION"
    ROLE = "ROLE"
    TASK = "TASK"
    RESOURCE = "RESOURCE"
    DEVICE = "DEVICE"
    SERVICE = "SERVICE"
    ORACLE = "ORACLE"
    ACCUMULATOR = "ACCUMULATOR"
    DICTIONARY = "DICTIONARY"
    HYBRID = "HYBRID"


@dataclass
class BirthCertificate:
    """
    Birth certificate proving LCT creation by society

    Equivalent to human birth certificate - proves you exist,
    when you were born, who witnessed it, and which society
    you're a member of.
    """
    lct_id: str
    entity_type: EntityType
    society_id: str
    law_oracle_id: str
    law_version: str
    birth_timestamp: float
    witnesses: List[str] = field(default_factory=list)
    genesis_block: Optional[str] = None
    initial_rights: List[str] = field(default_factory=lambda: [
        "exist", "interact", "accumulate_reputation"
    ])
    initial_responsibilities: List[str] = field(default_factory=lambda: [
        "abide_law", "respect_quorum"
    ])
    society_signature: Optional[bytes] = None
    witness_signatures: Dict[str, bytes] = field(default_factory=dict)
    certificate_hash: str = ""

    def __post_init__(self):
        """Generate certificate hash"""
        if not self.certificate_hash:
            self.certificate_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute tamper-evident hash of certificate"""
        cert_data = {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type.value,
            "society_id": self.society_id,
            "law_oracle_id": self.law_oracle_id,
            "law_version": self.law_version,
            "birth_timestamp": self.birth_timestamp,
            "witnesses": sorted(self.witnesses),
            "genesis_block": self.genesis_block,
            "initial_rights": sorted(self.initial_rights),
            "initial_responsibilities": sorted(self.initial_responsibilities)
        }
        cert_json = json.dumps(cert_data, sort_keys=True)
        return hashlib.sha256(cert_json.encode()).hexdigest()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type.value,
            "society_id": self.society_id,
            "law_oracle_id": self.law_oracle_id,
            "law_version": self.law_version,
            "birth_timestamp": self.birth_timestamp,
            "witnesses": self.witnesses,
            "genesis_block": self.genesis_block,
            "initial_rights": self.initial_rights,
            "initial_responsibilities": self.initial_responsibilities,
            "certificate_hash": self.certificate_hash
        }


@dataclass
class LCTCredential:
    """
    Complete LCT credential with keys and birth certificate

    This is the full identity object - contains everything needed
    to prove who you are, sign messages, and verify membership.
    """
    lct_id: str
    entity_type: EntityType
    society_id: str
    birth_certificate: BirthCertificate
    public_key_bytes: bytes
    private_key_bytes: Optional[bytes] = None  # Only for owner
    hardware_binding_hash: Optional[str] = None  # Future: TPM/SE
    created_at: float = field(default_factory=time.time)

    def get_public_key(self) -> ed25519.Ed25519PublicKey:
        """Get public key object"""
        return ed25519.Ed25519PublicKey.from_public_bytes(self.public_key_bytes)

    def get_private_key(self) -> Optional[ed25519.Ed25519PrivateKey]:
        """Get private key object (owner only)"""
        if not self.private_key_bytes:
            return None
        return ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key_bytes)

    def sign(self, message: bytes) -> bytes:
        """Sign a message with private key"""
        private_key = self.get_private_key()
        if not private_key:
            raise ValueError("No private key available for signing")
        return private_key.sign(message)

    def verify_signature(self, message: bytes, signature: bytes) -> bool:
        """Verify a signature with public key"""
        try:
            public_key = self.get_public_key()
            public_key.verify(signature, message)
            return True
        except Exception:
            return False

    def to_public_dict(self) -> Dict:
        """Export public information only (safe to share)"""
        return {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type.value,
            "society_id": self.society_id,
            "birth_certificate": self.birth_certificate.to_dict(),
            "public_key": self.public_key_bytes.hex(),
            "hardware_binding_hash": self.hardware_binding_hash,
            "created_at": self.created_at
        }

    def to_private_dict(self) -> Dict:
        """Export complete credential including private key (owner only)"""
        data = self.to_public_dict()
        if self.private_key_bytes:
            data["private_key"] = self.private_key_bytes.hex()
        return data


class LCTRegistry:
    """
    LCT Registry - Identity management system

    Central registry for all LCTs in a society. Handles:
    - Minting new identities
    - Storing credentials
    - Verifying birth certificates
    - Managing lifecycle (active, suspended, revoked)
    - Preventing duplicate identities
    """

    def __init__(self, society_id: str):
        self.society_id = society_id
        self.law_oracle_id = f"oracle:law:{society_id}"
        self.law_version = "v1.0.0"

        # Storage
        self.lcts: Dict[str, LCTCredential] = {}  # lct_id -> credential
        self.birth_certificates: Dict[str, BirthCertificate] = {}  # cert_hash -> certificate
        self.entity_to_lct: Dict[str, str] = {}  # entity_identifier -> lct_id

        # Lifecycle tracking
        self.active_lcts: Set[str] = set()
        self.suspended_lcts: Set[str] = set()
        self.revoked_lcts: Set[str] = set()

        # Counters
        self.lct_counter = 0

    def mint_lct(
        self,
        entity_type: EntityType,
        entity_identifier: str,  # Unique per entity (email, device_id, etc.)
        witnesses: List[str],
        genesis_block: Optional[str] = None
    ) -> Tuple[Optional[LCTCredential], str]:
        """
        Mint a new LCT identity

        Process:
        1. Check for duplicate entity
        2. Generate key pair
        3. Create birth certificate
        4. Get society/witness signatures
        5. Record in registry
        6. Return credential

        This is the ONLY way to create a new Web4 identity
        """

        # Check for duplicates
        if entity_identifier in self.entity_to_lct:
            return None, f"Entity {entity_identifier} already has LCT: {self.entity_to_lct[entity_identifier]}"

        # Generate key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize keys
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # Create LCT ID
        self.lct_counter += 1
        lct_id = f"lct:web4:{entity_type.value.lower()}:{self.society_id}:{self.lct_counter}"

        # Create birth certificate
        birth_cert = BirthCertificate(
            lct_id=lct_id,
            entity_type=entity_type,
            society_id=self.society_id,
            law_oracle_id=self.law_oracle_id,
            law_version=self.law_version,
            birth_timestamp=time.time(),
            witnesses=witnesses,
            genesis_block=genesis_block
        )

        # Society signs birth certificate (simplified - would use society keys)
        cert_message = birth_cert.certificate_hash.encode()
        birth_cert.society_signature = hashlib.sha256(
            f"society:{self.society_id}:signs:{birth_cert.certificate_hash}".encode()
        ).digest()

        # Witnesses sign (simplified)
        for witness in witnesses:
            birth_cert.witness_signatures[witness] = hashlib.sha256(
                f"witness:{witness}:signs:{birth_cert.certificate_hash}".encode()
            ).digest()

        # Create credential
        credential = LCTCredential(
            lct_id=lct_id,
            entity_type=entity_type,
            society_id=self.society_id,
            birth_certificate=birth_cert,
            public_key_bytes=public_key_bytes,
            private_key_bytes=private_key_bytes
        )

        # Register
        self.lcts[lct_id] = credential
        self.birth_certificates[birth_cert.certificate_hash] = birth_cert
        self.entity_to_lct[entity_identifier] = lct_id
        self.active_lcts.add(lct_id)

        # TODO: Write to immutable ledger

        return credential, ""

    def get_lct(self, lct_id: str) -> Optional[LCTCredential]:
        """Get LCT credential by ID"""
        return self.lcts.get(lct_id)

    def get_birth_certificate(self, cert_hash: str) -> Optional[BirthCertificate]:
        """Get birth certificate by hash"""
        return self.birth_certificates.get(cert_hash)

    def verify_birth_certificate(self, cert: BirthCertificate) -> Tuple[bool, str]:
        """
        Verify birth certificate authenticity

        Checks:
        1. Hash is correct
        2. Society signature valid
        3. Witness signatures valid
        4. Certificate exists in registry
        """

        # Verify hash
        computed_hash = cert.compute_hash()
        if computed_hash != cert.certificate_hash:
            return False, "Certificate hash mismatch"

        # Verify society signature (simplified)
        expected_sig = hashlib.sha256(
            f"society:{cert.society_id}:signs:{cert.certificate_hash}".encode()
        ).digest()

        if cert.society_signature != expected_sig:
            return False, "Invalid society signature"

        # Verify witness signatures (simplified)
        for witness, signature in cert.witness_signatures.items():
            expected_sig = hashlib.sha256(
                f"witness:{witness}:signs:{cert.certificate_hash}".encode()
            ).digest()

            if signature != expected_sig:
                return False, f"Invalid witness signature: {witness}"

        # Check if in registry
        if cert.certificate_hash not in self.birth_certificates:
            return False, "Certificate not in registry"

        return True, ""

    def verify_lct(self, lct_id: str, message: bytes, signature: bytes) -> Tuple[bool, str]:
        """
        Verify LCT credential and signature

        Used during authorization - proves entity has valid identity
        and can sign messages
        """

        # Get credential
        credential = self.get_lct(lct_id)
        if not credential:
            return False, "LCT not found"

        # Check status
        if lct_id in self.revoked_lcts:
            return False, "LCT revoked"

        if lct_id in self.suspended_lcts:
            return False, "LCT suspended"

        # Verify birth certificate
        is_valid, reason = self.verify_birth_certificate(credential.birth_certificate)
        if not is_valid:
            return False, f"Invalid birth certificate: {reason}"

        # Verify signature
        if not credential.verify_signature(message, signature):
            return False, "Invalid signature"

        return True, ""

    def suspend_lct(self, lct_id: str, reason: str) -> bool:
        """Temporarily suspend LCT (can be reactivated)"""
        if lct_id not in self.lcts:
            return False

        self.active_lcts.discard(lct_id)
        self.suspended_lcts.add(lct_id)

        # TODO: Log to ledger
        return True

    def reactivate_lct(self, lct_id: str) -> bool:
        """Reactivate suspended LCT"""
        if lct_id not in self.suspended_lcts:
            return False

        self.suspended_lcts.discard(lct_id)
        self.active_lcts.add(lct_id)

        # TODO: Log to ledger
        return True

    def revoke_lct(self, lct_id: str, reason: str) -> bool:
        """Permanently revoke LCT (cannot be reactivated)"""
        if lct_id not in self.lcts:
            return False

        self.active_lcts.discard(lct_id)
        self.suspended_lcts.discard(lct_id)
        self.revoked_lcts.add(lct_id)

        # TODO: Log to ledger (permanent record)
        return True

    def get_stats(self) -> Dict:
        """Get registry statistics"""
        return {
            "society_id": self.society_id,
            "total_lcts": len(self.lcts),
            "active": len(self.active_lcts),
            "suspended": len(self.suspended_lcts),
            "revoked": len(self.revoked_lcts),
            "entity_types": {
                etype.value: sum(1 for lct in self.lcts.values() if lct.entity_type == etype)
                for etype in EntityType
            }
        }


# Example usage
if __name__ == "__main__":
    import json

    print("="*70)
    print("  Web4 LCT Registry - Demonstration")
    print("="*70)

    # Create registry for a society
    registry = LCTRegistry("society:research_lab")

    print(f"\n✅ Created LCT Registry for: {registry.society_id}")
    print(f"   Law Oracle: {registry.law_oracle_id}")
    print(f"   Law Version: {registry.law_version}")

    # Mint LCT for human
    print(f"\n📝 Minting LCT for human researcher...")

    human_lct, error = registry.mint_lct(
        entity_type=EntityType.HUMAN,
        entity_identifier="alice@research.lab",
        witnesses=["witness:supervisor", "witness:admin"],
        genesis_block="block:12345"
    )

    if human_lct:
        print(f"   ✅ LCT Created: {human_lct.lct_id}")
        print(f"   Birth Certificate: {human_lct.birth_certificate.certificate_hash[:16]}...")
        print(f"   Witnesses: {len(human_lct.birth_certificate.witnesses)}")
        print(f"   Public Key: {human_lct.public_key_bytes.hex()[:32]}...")
    else:
        print(f"   ❌ Failed: {error}")
        exit(1)

    # Mint LCT for AI agent
    print(f"\n🤖 Minting LCT for AI agent...")

    ai_lct, error = registry.mint_lct(
        entity_type=EntityType.AI,
        entity_identifier="assistant_v1_device_001",
        witnesses=["witness:supervisor", "witness:admin"],
        genesis_block="block:12346"
    )

    if ai_lct:
        print(f"   ✅ LCT Created: {ai_lct.lct_id}")
        print(f"   Birth Certificate: {ai_lct.birth_certificate.certificate_hash[:16]}...")
    else:
        print(f"   ❌ Failed: {error}")

    # Test signing and verification
    print(f"\n🔐 Testing Cryptographic Operations...")

    message = b"Hello, Web4! This is a signed message."
    signature = human_lct.sign(message)

    print(f"   Message: {message.decode()}")
    print(f"   Signature: {signature.hex()[:32]}...")

    # Verify signature
    is_valid = human_lct.verify_signature(message, signature)
    print(f"   Signature Valid: {'✅' if is_valid else '❌'}")

    # Test full verification
    print(f"\n✅ Testing Full LCT Verification...")

    verify_result, verify_msg = registry.verify_lct(
        human_lct.lct_id,
        message,
        signature
    )

    print(f"   Verification: {'✅ PASSED' if verify_result else f'❌ FAILED: {verify_msg}'}")

    # Test duplicate prevention
    print(f"\n🚫 Testing Duplicate Prevention...")

    duplicate_lct, error = registry.mint_lct(
        entity_type=EntityType.HUMAN,
        entity_identifier="alice@research.lab",  # Same identifier
        witnesses=["witness:admin"]
    )

    if duplicate_lct:
        print(f"   ❌ VULNERABILITY: Duplicate LCT created!")
    else:
        print(f"   ✅ PROTECTED: {error}")

    # Test lifecycle
    print(f"\n🔄 Testing Lifecycle Management...")

    print(f"   Suspending {ai_lct.lct_id}...")
    registry.suspend_lct(ai_lct.lct_id, "Under review")

    # Try to verify suspended LCT
    verify_result, verify_msg = registry.verify_lct(
        ai_lct.lct_id,
        b"test",
        ai_lct.sign(b"test")
    )

    print(f"   Verification of suspended: {'❌ BLOCKED' if not verify_result else '✅'}")
    print(f"   Reason: {verify_msg}")

    # Reactivate
    print(f"   Reactivating...")
    registry.reactivate_lct(ai_lct.lct_id)

    verify_result, verify_msg = registry.verify_lct(
        ai_lct.lct_id,
        b"test",
        ai_lct.sign(b"test")
    )

    print(f"   Verification after reactivation: {'✅ PASSED' if verify_result else '❌'}")

    # Registry stats
    print(f"\n" + "="*70)
    print("Registry Statistics")
    print("="*70)
    print(json.dumps(registry.get_stats(), indent=2))

    # Export public credential
    print(f"\n" + "="*70)
    print("Public Credential (Safe to Share)")
    print("="*70)
    print(json.dumps(human_lct.to_public_dict(), indent=2, default=str))
