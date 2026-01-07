"""
Software Binding Provider (Level 4)
====================================

Provides software-only LCT binding for platforms without hardware security.

Features:
- Ed25519 key generation
- File-based key storage (~/.web4/identity/)
- Machine fingerprinting
- Explicit security limitations

Limitations (explicitly declared):
- keys_extractable: Private keys can be copied
- no_boot_integrity: Cannot verify system integrity
- no_hardware_attestation: Cannot prove key protection

Trust ceiling: 0.85 (vs 1.0 for hardware-bound)
"""

import os
import json
import hashlib
import base64
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.backends import default_backend

from .provider import (
    LCTBindingProvider,
    PlatformInfo,
    BindingResult,
    SignatureResult,
    AttestationResult,
    HardwareType,
    KeyStorage,
)
from .platform_detection import detect_platform

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from lct_capability_levels import (
    LCT, LCTBinding, CapabilityLevel, EntityType,
    T3Tensor, V3Tensor, MRH, LCTPolicy, BirthCertificate,
    generate_lct_id
)


class SoftwareProvider(LCTBindingProvider):
    """
    Software-only binding provider for Level 4 LCTs.

    Used on platforms without hardware security (e.g., WSL2).
    Provides cryptographic identity with explicit limitations.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize software provider.

        Args:
            storage_dir: Where to store keys (default: ~/.web4/identity/)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".web4" / "identity"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions
        try:
            os.chmod(self.storage_dir, 0o700)
        except:
            pass

        # Cache platform info
        self._platform_info = None

        # Cache loaded keys: {key_id: (private_key, public_key, metadata)}
        self._keys: Dict[str, tuple] = {}

    def get_platform_info(self) -> PlatformInfo:
        """Get platform capabilities."""
        if self._platform_info is None:
            self._platform_info = detect_platform()
        return self._platform_info

    @property
    def max_capability_level(self) -> CapabilityLevel:
        """Maximum level for software binding."""
        return CapabilityLevel.FULL  # Level 4

    @property
    def key_storage_type(self) -> KeyStorage:
        """Keys stored in software."""
        return KeyStorage.SOFTWARE

    @property
    def hardware_type(self) -> HardwareType:
        """No hardware security."""
        return HardwareType.NONE

    def generate_keypair(self, key_id: str) -> BindingResult:
        """
        Generate Ed25519 keypair for binding.

        Args:
            key_id: Identifier for storage/retrieval

        Returns:
            BindingResult with public key
        """
        try:
            # Generate Ed25519 keypair
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Create metadata
            platform = self.get_platform_info()
            metadata = {
                "key_id": key_id,
                "algorithm": "Ed25519",
                "public_key_pem": public_pem.decode('utf-8'),
                "machine_fingerprint": platform.machine_fingerprint,
                "machine_identity": platform.machine_identity,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "key_storage": "software",
                "hardware_type": "none",
                "binding_limitations": self.binding_limitations
            }

            # Save to disk
            self._save_key(key_id, private_pem, metadata)

            # Cache in memory
            self._keys[key_id] = (private_key, public_key, metadata)

            # Create binding proof (self-signed)
            binding_data = json.dumps({
                "key_id": key_id,
                "public_key": metadata["public_key_pem"],
                "machine": metadata["machine_identity"],
                "created_at": metadata["created_at"]
            }, sort_keys=True).encode('utf-8')

            binding_proof = base64.b64encode(
                private_key.sign(binding_data)
            ).decode('utf-8')

            return BindingResult(
                success=True,
                binding={
                    "public_key": metadata["public_key_pem"],
                    "key_id": key_id,
                    "machine_fingerprint": metadata["machine_fingerprint"],
                    "machine_identity": metadata["machine_identity"],
                    "created_at": metadata["created_at"],
                    "binding_proof": binding_proof,
                    "key_storage": "software",
                    "hardware_anchor": None,
                    "hardware_type": None,
                    "binding_limitations": self.binding_limitations
                },
                warnings=[
                    "Software-only binding: keys are extractable",
                    f"Trust ceiling: {self.trust_ceiling}"
                ]
            )

        except Exception as e:
            return BindingResult(
                success=False,
                error=str(e)
            )

    def sign_data(self, key_id: str, data: bytes) -> SignatureResult:
        """
        Sign data with stored key.

        Args:
            key_id: Identifier of signing key (can be full lct_id or just hash)
            data: Bytes to sign

        Returns:
            SignatureResult with signature
        """
        try:
            # Normalize key_id (extract hash if it's a full LCT ID)
            normalized_key_id = self._normalize_key_id(key_id)

            # Load key if needed
            if normalized_key_id not in self._keys:
                self._load_key(normalized_key_id)

            private_key = self._keys[normalized_key_id][0]

            # Sign
            signature = private_key.sign(data)
            signature_b64 = base64.b64encode(signature).decode('utf-8')

            return SignatureResult(
                success=True,
                signature=signature,
                signature_b64=signature_b64,
                algorithm="Ed25519"
            )

        except Exception as e:
            return SignatureResult(
                success=False,
                error=str(e)
            )

    def verify_signature(
        self,
        public_key: str,
        data: bytes,
        signature: bytes
    ) -> bool:
        """
        Verify signature.

        Args:
            public_key: Public key (PEM format)
            data: Original data
            signature: Signature to verify

        Returns:
            True if valid
        """
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import ec, ed25519

            # Load public key from PEM
            if isinstance(public_key, str):
                public_key_obj = serialization.load_pem_public_key(
                    public_key.encode('utf-8'),
                    backend=default_backend()
                )
            else:
                public_key_obj = public_key

            # Auto-detect key type and verify accordingly
            if isinstance(public_key_obj, ed25519.Ed25519PublicKey):
                # Ed25519: verify(signature, data)
                public_key_obj.verify(signature, data)
            elif isinstance(public_key_obj, ec.EllipticCurvePublicKey):
                # ECDSA: verify(signature, data, algorithm)
                public_key_obj.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            else:
                # Unknown key type - try generic verification
                public_key_obj.verify(signature, data)

            return True

        except Exception:
            return False

    def get_attestation(self, key_id: str) -> AttestationResult:
        """
        Get attestation (not available for software binding).

        Returns:
            AttestationResult indicating no attestation
        """
        return AttestationResult(
            success=False,
            attestation_type="none",
            error="Hardware attestation not available for software-only binding"
        )

    def create_lct(
        self,
        entity_type: EntityType,
        name: str = None
    ) -> LCT:
        """
        Create complete LCT with software binding.

        Args:
            entity_type: Type of entity
            name: Optional name for ID generation

        Returns:
            LCT at Level 4 with software binding
        """
        # Generate name if not provided
        if name is None:
            name = f"{entity_type.value}-{datetime.now().strftime('%H%M%S')}"

        # Generate LCT ID
        lct_id = generate_lct_id(entity_type, name)

        # Generate keypair
        key_id = lct_id.split(':')[-1]
        binding_result = self.generate_keypair(key_id)

        if not binding_result.success:
            raise RuntimeError(f"Binding generation failed: {binding_result.error}")

        # Create binding object
        binding = LCTBinding(
            entity_type=entity_type.value,
            public_key=binding_result.binding["public_key"],
            hardware_anchor=None,  # Software-only
            hardware_type=None,
            created_at=binding_result.binding["created_at"],
            binding_proof=binding_result.binding["binding_proof"]
        )

        # Create T3 tensor with trust ceiling
        t3 = T3Tensor.create_minimal(
            trust_ceiling=self.trust_ceiling,
            trust_ceiling_reason="software_binding"
        )

        # Create LCT
        lct = LCT(
            lct_id=lct_id,
            capability_level=CapabilityLevel.FULL,  # Level 4
            entity_type=entity_type,
            subject=f"did:web4:key:{key_id}",
            binding=binding,
            mrh=MRH(),
            policy=LCTPolicy(),
            t3_tensor=t3,
            v3_tensor=V3Tensor.create_zero(),
            birth_certificate=BirthCertificate.create_stub("Software-bound entity")
        )

        # Store binding limitations in metadata
        # (We'd add this to the LCT structure in a full implementation)

        return lct

    def _save_key(self, key_id: str, private_pem: bytes, metadata: Dict[str, Any]):
        """Save key to disk with secure permissions."""
        safe_id = self._safe_filename(key_id)

        # Save private key (chmod 600)
        private_file = self.storage_dir / f"{safe_id}.key"
        with open(private_file, 'wb') as f:
            f.write(private_pem)
        os.chmod(private_file, 0o600)

        # Save metadata (chmod 644)
        meta_file = self.storage_dir / f"{safe_id}.json"
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        os.chmod(meta_file, 0o644)

    def _load_key(self, key_id: str):
        """Load key from disk."""
        safe_id = self._safe_filename(key_id)
        private_file = self.storage_dir / f"{safe_id}.key"
        meta_file = self.storage_dir / f"{safe_id}.json"

        if not private_file.exists():
            raise ValueError(f"Key {key_id} not found")

        # Load private key
        with open(private_file, 'rb') as f:
            private_pem = f.read()
        private_key = serialization.load_pem_private_key(
            private_pem, password=None, backend=default_backend()
        )
        public_key = private_key.public_key()

        # Load metadata
        with open(meta_file, 'r') as f:
            metadata = json.load(f)

        # Cache
        self._keys[key_id] = (private_key, public_key, metadata)

    def _normalize_key_id(self, key_id: str) -> str:
        """
        Normalize key_id by extracting hash if it's a full LCT ID.

        Args:
            key_id: Either full lct_id (e.g. "lct:web4:ai:abc123") or just hash (e.g. "abc123")

        Returns:
            Just the hash part
        """
        if ':' in key_id:
            # It's a full LCT ID - extract the hash part
            return key_id.split(':')[-1]
        return key_id

    def get_public_key(self, key_id: str) -> str:
        """
        Get public key PEM for a stored key.

        Args:
            key_id: Identifier of key (can be full lct_id or just hash)

        Returns:
            Public key in PEM format
        """
        normalized_key_id = self._normalize_key_id(key_id)
        return self._get_public_key(normalized_key_id)

    def _get_public_key(self, key_id: str) -> str:
        """
        Get public key PEM for a stored key.

        Overrides base class to retrieve from software storage.
        """
        # Check cache first
        if key_id in self._keys:
            _, _, metadata = self._keys[key_id]
            return metadata.get("public_key_pem")

        # Load from disk
        safe_id = self._safe_filename(key_id)
        meta_file = self.storage_dir / f"{safe_id}.json"

        if not meta_file.exists():
            raise ValueError(f"Key {key_id} not found")

        with open(meta_file, 'r') as f:
            metadata = json.load(f)

        return metadata.get("public_key_pem")

    def _safe_filename(self, key_id: str) -> str:
        """Convert key ID to safe filename."""
        safe = key_id.replace('/', '_').replace('\\', '_')
        safe = safe.replace(':', '_').replace('@', '_at_')
        safe = safe.replace(' ', '_')
        return safe

    def list_keys(self) -> list:
        """List all stored keys."""
        keys = []
        for meta_file in self.storage_dir.glob("*.json"):
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
            keys.append({
                "key_id": metadata.get("key_id"),
                "machine_identity": metadata.get("machine_identity"),
                "created_at": metadata.get("created_at")
            })
        return keys


# Quick test when run directly
if __name__ == "__main__":
    print("=" * 60)
    print("SOFTWARE BINDING PROVIDER TEST")
    print("=" * 60)

    provider = SoftwareProvider()

    # Show platform info
    platform = provider.get_platform_info()
    print(f"Platform: {platform.name}")
    print(f"Max Level: {provider.max_capability_level.name}")
    print(f"Trust Ceiling: {provider.trust_ceiling}")
    print(f"Limitations: {provider.binding_limitations}")
    print()

    # Create an LCT
    print("Creating Level 4 AI LCT...")
    lct = provider.create_lct(EntityType.AI, "test-agent")
    print(f"LCT ID: {lct.lct_id}")
    print(f"Level: {lct.capability_level.name}")
    print(f"Entity Type: {lct.entity_type.value}")
    print(f"Has Hardware Anchor: {lct.binding.hardware_anchor is not None}")
    print(f"T3 Composite: {lct.t3_tensor.composite_score:.3f}")
    print()

    # Sign some data
    print("Signing test data...")
    test_data = b"Hello, Web4!"
    key_id = lct.lct_id.split(':')[-1]
    sig_result = provider.sign_data(key_id, test_data)
    print(f"Signature: {sig_result.signature_b64[:32]}...")
    print()

    # Verify signature
    print("Verifying signature...")
    valid = provider.verify_signature(
        lct.binding.public_key,
        test_data,
        sig_result.signature
    )
    print(f"Valid: {valid}")
    print()

    # Try attestation
    print("Requesting attestation...")
    att_result = provider.get_attestation(key_id)
    print(f"Success: {att_result.success}")
    print(f"Reason: {att_result.error}")
    print()

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
