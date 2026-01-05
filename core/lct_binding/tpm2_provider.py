"""
TPM2 Binding Provider (Level 5)
===============================

Provides hardware-bound LCT binding using TPM 2.0.

Features:
- Hardware-protected Ed25519/ECC keys
- Non-extractable private keys
- TPM2 attestation quotes
- Boot integrity verification (PCR values)

Requirements:
- TPM 2.0 chip accessible at /dev/tpm0 or /dev/tpmrm0
- tpm2-tools installed (tpm2_createprimary, tpm2_create, tpm2_sign, etc.)
- User in 'tss' group for TPM access

Trust ceiling: 1.0 (hardware-bound)

STATUS: DRAFT - Requires testing on Legion (native Linux with TPM)
"""

import os
import json
import base64
import subprocess
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

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


class TPM2Provider(LCTBindingProvider):
    """
    TPM 2.0 binding provider for Level 5 LCTs.

    Uses tpm2-tools for TPM operations. Keys are created in the TPM
    and cannot be extracted - only the TPM can perform signing operations.

    STATUS: DRAFT - Written on CBP (no TPM), needs testing on Legion.
    """

    # TPM2 tool commands
    TPM2_CREATEPRIMARY = "tpm2_createprimary"
    TPM2_CREATE = "tpm2_create"
    TPM2_LOAD = "tpm2_load"
    TPM2_SIGN = "tpm2_sign"
    TPM2_VERIFYSIGNATURE = "tpm2_verifysignature"
    TPM2_QUOTE = "tpm2_quote"
    TPM2_READPUBLIC = "tpm2_readpublic"
    TPM2_EVICTCONTROL = "tpm2_evictcontrol"
    TPM2_PCRREAD = "tpm2_pcrread"

    # Persistent handle range for our keys (0x81000000 - 0x810000FF)
    PERSISTENT_HANDLE_BASE = 0x81010000  # Web4 namespace

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize TPM2 provider.

        Args:
            storage_dir: Where to store key metadata (default: ~/.web4/identity/tpm2/)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".web4" / "identity" / "tpm2"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions
        try:
            os.chmod(self.storage_dir, 0o700)
        except:
            pass

        # Cache platform info
        self._platform_info = None

        # Cache loaded key metadata: {key_id: metadata}
        self._keys: Dict[str, Dict] = {}

        # Check TPM availability
        self._tpm_available = self._check_tpm_tools()

    def _check_tpm_tools(self) -> bool:
        """Check if tpm2-tools are available."""
        try:
            result = subprocess.run(
                ["tpm2_getcap", "properties-fixed"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _run_tpm2_command(
        self,
        cmd: list,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a tpm2-tools command."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30
        )
        if check and result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='replace')
            raise RuntimeError(f"TPM2 command failed: {cmd[0]}: {error_msg}")
        return result

    def get_platform_info(self) -> PlatformInfo:
        """Get platform capabilities."""
        if self._platform_info is None:
            self._platform_info = detect_platform()
        return self._platform_info

    @property
    def max_capability_level(self) -> CapabilityLevel:
        """Maximum level for TPM2 binding."""
        return CapabilityLevel.HARDWARE  # Level 5

    @property
    def key_storage_type(self) -> KeyStorage:
        """Keys stored in TPM."""
        return KeyStorage.TPM

    @property
    def hardware_type(self) -> HardwareType:
        """TPM 2.0 hardware security."""
        return HardwareType.TPM2

    def _get_persistent_handle(self, key_id: str) -> int:
        """Get persistent handle for a key ID."""
        # Hash key_id to get consistent handle in our range
        hash_bytes = hashlib.sha256(key_id.encode()).digest()
        offset = int.from_bytes(hash_bytes[:2], 'big') & 0xFF
        return self.PERSISTENT_HANDLE_BASE + offset

    def generate_keypair(self, key_id: str) -> BindingResult:
        """
        Generate ECC keypair in TPM for binding.

        Creates a primary key and a signing key under it.
        The signing key is made persistent for future use.

        Args:
            key_id: Identifier for storage/retrieval

        Returns:
            BindingResult with public key
        """
        if not self._tpm_available:
            return BindingResult(
                success=False,
                error="TPM2 tools not available. Install tpm2-tools package."
            )

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)

                # File paths for TPM objects
                primary_ctx = tmpdir / "primary.ctx"
                key_pub = tmpdir / "key.pub"
                key_priv = tmpdir / "key.priv"
                key_ctx = tmpdir / "key.ctx"
                key_pem = tmpdir / "key.pem"

                # 1. Create primary key (owner hierarchy)
                self._run_tpm2_command([
                    self.TPM2_CREATEPRIMARY,
                    "-C", "o",  # Owner hierarchy
                    "-g", "sha256",
                    "-G", "ecc256",  # ECC P-256 (TPM doesn't support Ed25519 directly)
                    "-c", str(primary_ctx)
                ])

                # 2. Create signing key under primary
                self._run_tpm2_command([
                    self.TPM2_CREATE,
                    "-C", str(primary_ctx),
                    "-g", "sha256",
                    "-G", "ecc256",
                    "-u", str(key_pub),
                    "-r", str(key_priv),
                    "-a", "sign|fixedtpm|fixedparent|sensitivedataorigin|userwithauth"
                ])

                # 3. Load the key
                self._run_tpm2_command([
                    self.TPM2_LOAD,
                    "-C", str(primary_ctx),
                    "-u", str(key_pub),
                    "-r", str(key_priv),
                    "-c", str(key_ctx)
                ])

                # 4. Make key persistent
                persistent_handle = self._get_persistent_handle(key_id)
                persistent_handle_hex = f"0x{persistent_handle:08x}"

                # Try to evict existing key at this handle (ignore errors)
                subprocess.run(
                    [self.TPM2_EVICTCONTROL, "-C", "o", "-c", persistent_handle_hex],
                    capture_output=True
                )

                # Make new key persistent
                self._run_tpm2_command([
                    self.TPM2_EVICTCONTROL,
                    "-C", "o",
                    "-c", str(key_ctx),
                    persistent_handle_hex
                ])

                # 5. Read public key in PEM format
                self._run_tpm2_command([
                    self.TPM2_READPUBLIC,
                    "-c", persistent_handle_hex,
                    "-f", "pem",
                    "-o", str(key_pem)
                ])

                with open(key_pem, 'r') as f:
                    public_key_pem = f.read()

                # 6. Create metadata
                platform = self.get_platform_info()
                metadata = {
                    "key_id": key_id,
                    "algorithm": "ECC-P256",  # TPM uses P-256, not Ed25519
                    "public_key_pem": public_key_pem,
                    "persistent_handle": persistent_handle_hex,
                    "machine_fingerprint": platform.machine_fingerprint,
                    "machine_identity": platform.machine_identity,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "key_storage": "tpm",
                    "hardware_type": "tpm2",
                    "binding_limitations": []  # No limitations for hardware binding
                }

                # 7. Save metadata to disk
                self._save_metadata(key_id, metadata)

                # 8. Cache metadata
                self._keys[key_id] = metadata

                # 9. Create binding proof (signed by TPM)
                binding_data = json.dumps({
                    "key_id": key_id,
                    "public_key": public_key_pem,
                    "machine": metadata["machine_identity"],
                    "created_at": metadata["created_at"],
                    "tpm_handle": persistent_handle_hex
                }, sort_keys=True).encode('utf-8')

                # Sign binding data with TPM
                sig_result = self._tpm_sign(persistent_handle_hex, binding_data, tmpdir)
                binding_proof = sig_result if sig_result else "tpm_signature_pending"

                return BindingResult(
                    success=True,
                    binding={
                        "public_key": public_key_pem,
                        "key_id": key_id,
                        "machine_fingerprint": metadata["machine_fingerprint"],
                        "machine_identity": metadata["machine_identity"],
                        "created_at": metadata["created_at"],
                        "binding_proof": binding_proof,
                        "key_storage": "tpm",
                        "hardware_anchor": persistent_handle_hex,
                        "hardware_type": "tpm2",
                        "binding_limitations": []
                    }
                )

        except Exception as e:
            return BindingResult(
                success=False,
                error=str(e)
            )

    def _tpm_sign(
        self,
        handle: str,
        data: bytes,
        tmpdir: Path
    ) -> Optional[str]:
        """Sign data using TPM key."""
        try:
            # Write data to sign
            data_file = tmpdir / "sign_data.bin"
            sig_file = tmpdir / "signature.bin"

            # Hash the data (TPM signs hashes, not raw data)
            data_hash = hashlib.sha256(data).digest()
            with open(data_file, 'wb') as f:
                f.write(data_hash)

            # Sign with TPM
            self._run_tpm2_command([
                self.TPM2_SIGN,
                "-c", handle,
                "-g", "sha256",
                "-s", "ecdsa",
                "-d", str(data_file),  # -d means input is already a digest
                "-o", str(sig_file)
            ])

            with open(sig_file, 'rb') as f:
                signature = f.read()

            return base64.b64encode(signature).decode('utf-8')

        except Exception:
            return None

    def sign_data(self, key_id: str, data: bytes) -> SignatureResult:
        """
        Sign data with TPM-stored key.

        Args:
            key_id: Identifier of signing key
            data: Bytes to sign

        Returns:
            SignatureResult with signature
        """
        if not self._tpm_available:
            return SignatureResult(
                success=False,
                error="TPM2 tools not available"
            )

        try:
            # Load metadata if needed
            if key_id not in self._keys:
                self._load_metadata(key_id)

            metadata = self._keys[key_id]
            handle = metadata["persistent_handle"]

            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                signature_b64 = self._tpm_sign(handle, data, tmpdir)

                if signature_b64:
                    signature = base64.b64decode(signature_b64)
                    return SignatureResult(
                        success=True,
                        signature=signature,
                        signature_b64=signature_b64,
                        algorithm="ECDSA-P256-SHA256"
                    )
                else:
                    return SignatureResult(
                        success=False,
                        error="TPM signing failed"
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
        Verify signature using TPM.

        Args:
            public_key: Public key (PEM format)
            data: Original data
            signature: Signature to verify

        Returns:
            True if valid
        """
        if not self._tpm_available:
            # Fallback to software verification
            try:
                from cryptography.hazmat.primitives import hashes, serialization
                from cryptography.hazmat.primitives.asymmetric import ec
                from cryptography.hazmat.backends import default_backend

                public_key_obj = serialization.load_pem_public_key(
                    public_key.encode('utf-8'),
                    backend=default_backend()
                )

                data_hash = hashlib.sha256(data).digest()
                public_key_obj.verify(signature, data_hash, ec.ECDSA(hashes.SHA256()))
                return True
            except Exception:
                return False

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)

                # Write files
                key_file = tmpdir / "pubkey.pem"
                data_file = tmpdir / "data.bin"
                sig_file = tmpdir / "sig.bin"

                with open(key_file, 'w') as f:
                    f.write(public_key)

                # Hash the data
                data_hash = hashlib.sha256(data).digest()
                with open(data_file, 'wb') as f:
                    f.write(data_hash)

                with open(sig_file, 'wb') as f:
                    f.write(signature)

                # Verify with TPM
                result = subprocess.run(
                    [
                        self.TPM2_VERIFYSIGNATURE,
                        "-c", str(key_file),
                        "-g", "sha256",
                        "-s", "ecdsa",
                        "-d", str(data_file),
                        "-m", str(sig_file)
                    ],
                    capture_output=True
                )

                return result.returncode == 0

        except Exception:
            return False

    def get_attestation(self, key_id: str) -> AttestationResult:
        """
        Get TPM attestation quote.

        Provides cryptographic proof that:
        - Key exists in TPM
        - Current PCR values (boot integrity)

        Args:
            key_id: Identifier of the key to attest

        Returns:
            AttestationResult with TPM quote
        """
        if not self._tpm_available:
            return AttestationResult(
                success=False,
                attestation_type="none",
                error="TPM2 tools not available"
            )

        try:
            # Load metadata
            if key_id not in self._keys:
                self._load_metadata(key_id)

            metadata = self._keys[key_id]
            handle = metadata["persistent_handle"]

            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                quote_file = tmpdir / "quote.bin"
                sig_file = tmpdir / "quote_sig.bin"
                pcr_file = tmpdir / "pcrs.bin"

                # Read PCR values (0-7 for boot measurements)
                pcr_result = self._run_tpm2_command([
                    self.TPM2_PCRREAD,
                    "sha256:0,1,2,3,4,5,6,7",
                    "-o", str(pcr_file)
                ])

                # Generate quote
                nonce = os.urandom(32)
                nonce_file = tmpdir / "nonce.bin"
                with open(nonce_file, 'wb') as f:
                    f.write(nonce)

                self._run_tpm2_command([
                    self.TPM2_QUOTE,
                    "-c", handle,
                    "-l", "sha256:0,1,2,3,4,5,6,7",
                    "-q", str(nonce_file),
                    "-m", str(quote_file),
                    "-s", str(sig_file)
                ])

                # Read results
                with open(quote_file, 'rb') as f:
                    quote_data = f.read()
                with open(sig_file, 'rb') as f:
                    quote_sig = f.read()
                with open(pcr_file, 'rb') as f:
                    pcr_data = f.read()

                # Parse PCR values (simplified - real implementation needs proper parsing)
                pcr_values = {
                    i: hashlib.sha256(pcr_data[i*32:(i+1)*32]).hexdigest()[:16]
                    for i in range(8)
                    if len(pcr_data) >= (i+1)*32
                }

                # Create attestation token
                attestation_token = base64.b64encode(json.dumps({
                    "type": "tpm2_quote",
                    "quote": base64.b64encode(quote_data).decode(),
                    "signature": base64.b64encode(quote_sig).decode(),
                    "nonce": base64.b64encode(nonce).decode(),
                    "key_handle": handle,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }).encode()).decode()

                return AttestationResult(
                    success=True,
                    attestation_token=attestation_token,
                    attestation_type="tpm2_quote",
                    pcr_values=pcr_values
                )

        except Exception as e:
            return AttestationResult(
                success=False,
                attestation_type="tpm2_quote",
                error=str(e)
            )

    def create_lct(
        self,
        entity_type: EntityType,
        name: str = None
    ) -> LCT:
        """
        Create complete LCT with TPM2 binding.

        Args:
            entity_type: Type of entity
            name: Optional name for ID generation

        Returns:
            LCT at Level 5 with hardware binding
        """
        # Generate name if not provided
        if name is None:
            name = f"{entity_type.value}-{datetime.now().strftime('%H%M%S')}"

        # Generate LCT ID
        lct_id = generate_lct_id(entity_type, name)

        # Generate keypair in TPM
        key_id = lct_id.split(':')[-1]
        binding_result = self.generate_keypair(key_id)

        if not binding_result.success:
            raise RuntimeError(f"TPM binding failed: {binding_result.error}")

        # Create binding object
        binding = LCTBinding(
            entity_type=entity_type.value,
            public_key=binding_result.binding["public_key"],
            hardware_anchor=binding_result.binding["hardware_anchor"],
            hardware_type="tpm2",
            created_at=binding_result.binding["created_at"],
            binding_proof=binding_result.binding["binding_proof"]
        )

        # Create T3 tensor with full trust ceiling
        t3 = T3Tensor.create_minimal(
            trust_ceiling=self.trust_ceiling,  # 1.0 for hardware
            trust_ceiling_reason="tpm2_hardware_binding"
        )

        # Create LCT
        lct = LCT(
            lct_id=lct_id,
            capability_level=CapabilityLevel.HARDWARE,  # Level 5
            entity_type=entity_type,
            subject=f"did:web4:tpm:{key_id}",
            binding=binding,
            mrh=MRH(),
            policy=LCTPolicy(),
            t3_tensor=t3,
            v3_tensor=V3Tensor.create_zero(),
            birth_certificate=BirthCertificate.create_stub("TPM2-bound entity")
        )

        return lct

    def _save_metadata(self, key_id: str, metadata: Dict[str, Any]):
        """Save key metadata to disk."""
        safe_id = self._safe_filename(key_id)
        meta_file = self.storage_dir / f"{safe_id}.json"
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        os.chmod(meta_file, 0o600)

    def _load_metadata(self, key_id: str):
        """Load key metadata from disk."""
        safe_id = self._safe_filename(key_id)
        meta_file = self.storage_dir / f"{safe_id}.json"

        if not meta_file.exists():
            raise ValueError(f"Key {key_id} not found")

        with open(meta_file, 'r') as f:
            metadata = json.load(f)

        self._keys[key_id] = metadata

    def _get_public_key(self, key_id: str) -> str:
        """
        Get public key for a stored key.

        Required for Aliveness Verification Protocol.
        """
        if key_id not in self._keys:
            self._load_metadata(key_id)

        metadata = self._keys.get(key_id)
        if not metadata:
            from .provider import KeyNotFoundError
            raise KeyNotFoundError(f"Key {key_id} not found")

        return metadata.get("public_key_pem", "")

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
                "persistent_handle": metadata.get("persistent_handle"),
                "machine_identity": metadata.get("machine_identity"),
                "created_at": metadata.get("created_at")
            })
        return keys


# Quick test when run directly
if __name__ == "__main__":
    print("=" * 60)
    print("TPM2 BINDING PROVIDER TEST")
    print("=" * 60)

    provider = TPM2Provider()

    # Show platform info
    platform = provider.get_platform_info()
    print(f"Platform: {platform.name}")
    print(f"Has TPM2: {platform.has_tpm2}")
    print(f"Max Level: {provider.max_capability_level.name}")
    print(f"Trust Ceiling: {provider.trust_ceiling}")
    print(f"TPM Tools Available: {provider._tpm_available}")
    print()

    if not provider._tpm_available:
        print("TPM2 tools not available - cannot test further")
        print("Install tpm2-tools and ensure TPM access")
        print("=" * 60)
        exit(1)

    # Create an LCT
    print("Creating Level 5 AI LCT with TPM binding...")
    try:
        lct = provider.create_lct(EntityType.AI, "test-agent")
        print(f"LCT ID: {lct.lct_id}")
        print(f"Level: {lct.capability_level.name}")
        print(f"Entity Type: {lct.entity_type.value}")
        print(f"Hardware Anchor: {lct.binding.hardware_anchor}")
        print(f"T3 Trust Ceiling: {lct.t3_tensor.trust_ceiling}")
        print()

        # Sign some data
        print("Signing test data with TPM...")
        test_data = b"Hello, Web4 with TPM2!"
        key_id = lct.lct_id.split(':')[-1]
        sig_result = provider.sign_data(key_id, test_data)
        print(f"Signature: {sig_result.signature_b64[:32]}...")
        print()

        # Get attestation
        print("Requesting TPM attestation...")
        att_result = provider.get_attestation(key_id)
        print(f"Success: {att_result.success}")
        print(f"Type: {att_result.attestation_type}")
        if att_result.pcr_values:
            print(f"PCR[0]: {att_result.pcr_values.get(0, 'N/A')}")
        print()

    except Exception as e:
        print(f"Error: {e}")

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
