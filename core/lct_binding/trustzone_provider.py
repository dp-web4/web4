"""
TrustZone Binding Provider (Level 5)
====================================

Provides hardware-bound LCT binding using ARM TrustZone/OP-TEE.

Features:
- Keys stored in Secure World (TEE)
- Non-extractable private keys
- PSA attestation tokens
- Secure boot verification

Requirements:
- ARM64 processor with TrustZone
- OP-TEE installed and running
- TEE device accessible at /dev/tee0 or /dev/teepriv0
- OP-TEE client library (libteec)

Trust ceiling: 1.0 (hardware-bound)

STATUS: DRAFT - Requires testing on Thor/Sprout (ARM64 with OP-TEE)
"""

import os
import json
import base64
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

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


# OP-TEE Trusted Application UUID for Web4 key management
# This TA would need to be developed and deployed to the TEE
WEB4_TA_UUID = "a96e57b0-1b4c-4c3e-8b5a-2f3d4e5f6a7b"


class TrustZoneProvider(LCTBindingProvider):
    """
    ARM TrustZone/OP-TEE binding provider for Level 5 LCTs.

    Keys are created and stored in the Secure World via OP-TEE.
    The Normal World (Linux) never sees private key material.

    STATUS: DRAFT - Written on CBP (x86), needs testing on Thor/Sprout.

    Implementation Notes:
    ---------------------
    Full implementation requires a Trusted Application (TA) running in OP-TEE.
    The TA handles:
    - Key generation (ECC P-256 or Ed25519 if supported)
    - Signing operations
    - Key storage in secure storage
    - PSA attestation

    This provider communicates with the TA via:
    - libteec (OP-TEE Client library) - preferred
    - tee-supplicant commands - fallback

    Current implementation uses command-line tools as proof of concept.
    Production should use python-optee or ctypes bindings to libteec.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize TrustZone provider.

        Args:
            storage_dir: Where to store key metadata (default: ~/.web4/identity/trustzone/)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".web4" / "identity" / "trustzone"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        try:
            os.chmod(self.storage_dir, 0o700)
        except:
            pass

        self._platform_info = None
        self._keys: Dict[str, Dict] = {}

        # Check TEE availability
        self._tee_available = self._check_tee()
        self._optee_test_available = self._check_optee_test()

    def _check_tee(self) -> bool:
        """Check if TEE device is available."""
        tee_devices = [
            Path('/dev/tee0'),
            Path('/dev/teepriv0'),
        ]
        return any(d.exists() for d in tee_devices)

    def _check_optee_test(self) -> bool:
        """Check if OP-TEE test tools are available."""
        try:
            # xtest is the OP-TEE test suite
            result = subprocess.run(
                ["which", "xtest"],
                capture_output=True
            )
            return result.returncode == 0
        except:
            return False

    def _check_ta_installed(self) -> bool:
        """Check if Web4 TA is installed."""
        ta_path = Path(f"/lib/optee_armtz/{WEB4_TA_UUID}.ta")
        return ta_path.exists()

    def get_platform_info(self) -> PlatformInfo:
        """Get platform capabilities."""
        if self._platform_info is None:
            self._platform_info = detect_platform()
        return self._platform_info

    @property
    def max_capability_level(self) -> CapabilityLevel:
        """Maximum level for TrustZone binding."""
        return CapabilityLevel.HARDWARE  # Level 5

    @property
    def key_storage_type(self) -> KeyStorage:
        """Keys stored in TrustZone."""
        return KeyStorage.TRUSTZONE

    @property
    def hardware_type(self) -> HardwareType:
        """ARM TrustZone hardware security."""
        return HardwareType.TRUSTZONE

    def _invoke_ta(
        self,
        command: int,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke Web4 Trusted Application.

        In production, this would use libteec via ctypes or python-optee.
        For now, we use a helper script that wraps the TA invocation.

        Args:
            command: TA command ID
            params: Parameters to pass to TA

        Returns:
            Response from TA
        """
        # Check if helper exists
        helper = Path("/usr/local/bin/web4-tee-helper")
        if not helper.exists():
            # Fallback to simulation mode for development
            return self._simulate_ta(command, params)

        try:
            result = subprocess.run(
                [
                    str(helper),
                    "--uuid", WEB4_TA_UUID,
                    "--cmd", str(command),
                    "--params", json.dumps(params)
                ],
                capture_output=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"TA invocation failed: {result.stderr.decode()}")

            return json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            raise RuntimeError("TA invocation timed out")
        except json.JSONDecodeError:
            raise RuntimeError("Invalid response from TA")

    def _simulate_ta(
        self,
        command: int,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate TA operations for development/testing.

        WARNING: This uses software cryptography!
        Only for development when TEE is not available.

        Returns simulated responses with clear warnings.
        """
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.backends import default_backend

        # Command IDs
        CMD_GENERATE_KEY = 1
        CMD_SIGN = 2
        CMD_GET_ATTESTATION = 3

        if command == CMD_GENERATE_KEY:
            # Generate ECC key in software (simulation only!)
            private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
            public_key = private_key.public_key()

            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

            # In real TA, private key stays in TEE
            # For simulation, we store it (clearly marked)
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')

            # Generate key handle (would be TEE object ID in real impl)
            key_handle = hashlib.sha256(
                params.get("key_id", "unknown").encode()
            ).hexdigest()[:16]

            return {
                "success": True,
                "simulated": True,  # IMPORTANT: Mark as simulated
                "warning": "SIMULATED - Using software crypto, not real TEE!",
                "public_key": public_pem,
                "key_handle": f"sim:{key_handle}",
                "_private_key": private_pem  # Only for simulation!
            }

        elif command == CMD_SIGN:
            # Sign with simulated key
            key_id = params.get("key_id")
            data = base64.b64decode(params.get("data_b64", ""))

            # Load simulated private key
            meta_file = self.storage_dir / f"{self._safe_filename(key_id)}.json"
            if meta_file.exists():
                with open(meta_file) as f:
                    metadata = json.load(f)

                if "_private_key" in metadata:
                    private_key = serialization.load_pem_private_key(
                        metadata["_private_key"].encode(),
                        password=None,
                        backend=default_backend()
                    )

                    # Hash and sign
                    data_hash = hashlib.sha256(data).digest()
                    signature = private_key.sign(
                        data_hash,
                        ec.ECDSA(hashes.SHA256())
                    )

                    return {
                        "success": True,
                        "simulated": True,
                        "warning": "SIMULATED - Not real TEE signature!",
                        "signature": base64.b64encode(signature).decode()
                    }

            return {"success": False, "error": "Key not found"}

        elif command == CMD_GET_ATTESTATION:
            # Simulated attestation (not real!)
            return {
                "success": True,
                "simulated": True,
                "warning": "SIMULATED - Not real PSA attestation!",
                "attestation_type": "psa_simulated",
                "token": base64.b64encode(json.dumps({
                    "type": "simulated_psa",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "warning": "This is NOT a real attestation token"
                }).encode()).decode()
            }

        return {"success": False, "error": f"Unknown command: {command}"}

    def generate_keypair(self, key_id: str) -> BindingResult:
        """
        Generate ECC keypair in TrustZone for binding.

        Args:
            key_id: Identifier for storage/retrieval

        Returns:
            BindingResult with public key
        """
        try:
            # Invoke TA to generate key
            result = self._invoke_ta(1, {"key_id": key_id})

            if not result.get("success"):
                return BindingResult(
                    success=False,
                    error=result.get("error", "TA key generation failed")
                )

            # Check if simulated
            is_simulated = result.get("simulated", False)
            warnings = []
            if is_simulated:
                warnings.append("WARNING: Using simulated TrustZone (software crypto)")
                warnings.append("Deploy Web4 TA for real hardware binding")

            # Create metadata
            platform = self.get_platform_info()
            metadata = {
                "key_id": key_id,
                "algorithm": "ECC-P256",
                "public_key_pem": result["public_key"],
                "key_handle": result["key_handle"],
                "machine_fingerprint": platform.machine_fingerprint,
                "machine_identity": platform.machine_identity,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "key_storage": "trustzone",
                "hardware_type": "trustzone",
                "simulated": is_simulated,
                "binding_limitations": [] if not is_simulated else ["simulated_tee"]
            }

            # Store private key reference for simulation only
            if is_simulated and "_private_key" in result:
                metadata["_private_key"] = result["_private_key"]

            # Save metadata
            self._save_metadata(key_id, metadata)
            self._keys[key_id] = metadata

            # Create binding proof
            binding_data = json.dumps({
                "key_id": key_id,
                "public_key": result["public_key"],
                "machine": metadata["machine_identity"],
                "created_at": metadata["created_at"],
                "tee_handle": result["key_handle"]
            }, sort_keys=True).encode('utf-8')

            # Sign binding proof
            sig_result = self._invoke_ta(2, {
                "key_id": key_id,
                "data_b64": base64.b64encode(binding_data).decode()
            })

            binding_proof = sig_result.get("signature", "pending")

            return BindingResult(
                success=True,
                binding={
                    "public_key": result["public_key"],
                    "key_id": key_id,
                    "machine_fingerprint": metadata["machine_fingerprint"],
                    "machine_identity": metadata["machine_identity"],
                    "created_at": metadata["created_at"],
                    "binding_proof": binding_proof,
                    "key_storage": "trustzone",
                    "hardware_anchor": result["key_handle"],
                    "hardware_type": "trustzone",
                    "binding_limitations": metadata["binding_limitations"]
                },
                warnings=warnings
            )

        except Exception as e:
            return BindingResult(
                success=False,
                error=str(e)
            )

    def sign_data(self, key_id: str, data: bytes) -> SignatureResult:
        """
        Sign data with TrustZone-stored key.

        Args:
            key_id: Identifier of signing key
            data: Bytes to sign

        Returns:
            SignatureResult with signature
        """
        try:
            result = self._invoke_ta(2, {
                "key_id": key_id,
                "data_b64": base64.b64encode(data).decode()
            })

            if not result.get("success"):
                return SignatureResult(
                    success=False,
                    error=result.get("error", "TA signing failed")
                )

            signature_b64 = result["signature"]
            signature = base64.b64decode(signature_b64)

            return SignatureResult(
                success=True,
                signature=signature,
                signature_b64=signature_b64,
                algorithm="ECDSA-P256-SHA256"
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
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.backends import default_backend

            public_key_obj = serialization.load_pem_public_key(
                public_key.encode('utf-8'),
                backend=default_backend()
            )

            # Hash the data (TA signs the hash)
            data_hash = hashlib.sha256(data).digest()
            public_key_obj.verify(signature, data_hash, ec.ECDSA(hashes.SHA256()))
            return True

        except Exception:
            return False

    def get_attestation(self, key_id: str) -> AttestationResult:
        """
        Get PSA attestation token.

        Provides cryptographic proof that:
        - Key exists in TrustZone
        - Device identity and security state

        Args:
            key_id: Identifier of the key to attest

        Returns:
            AttestationResult with PSA token
        """
        try:
            result = self._invoke_ta(3, {"key_id": key_id})

            if not result.get("success"):
                return AttestationResult(
                    success=False,
                    attestation_type="psa",
                    error=result.get("error", "TA attestation failed")
                )

            is_simulated = result.get("simulated", False)

            return AttestationResult(
                success=True,
                attestation_token=result["token"],
                attestation_type="psa_simulated" if is_simulated else "psa"
            )

        except Exception as e:
            return AttestationResult(
                success=False,
                attestation_type="psa",
                error=str(e)
            )

    def create_lct(
        self,
        entity_type: EntityType,
        name: str = None
    ) -> LCT:
        """
        Create complete LCT with TrustZone binding.

        Args:
            entity_type: Type of entity
            name: Optional name for ID generation

        Returns:
            LCT at Level 5 with hardware binding
        """
        if name is None:
            name = f"{entity_type.value}-{datetime.now().strftime('%H%M%S')}"

        lct_id = generate_lct_id(entity_type, name)
        key_id = lct_id.split(':')[-1]
        binding_result = self.generate_keypair(key_id)

        if not binding_result.success:
            raise RuntimeError(f"TrustZone binding failed: {binding_result.error}")

        # Check if simulated (look for simulated_tee in limitations)
        is_simulated = "simulated_tee" in binding_result.binding.get("binding_limitations", [])

        binding = LCTBinding(
            entity_type=entity_type.value,
            public_key=binding_result.binding["public_key"],
            hardware_anchor=binding_result.binding["hardware_anchor"],
            hardware_type="trustzone" if not is_simulated else "trustzone_simulated",
            created_at=binding_result.binding["created_at"],
            binding_proof=binding_result.binding["binding_proof"]
        )

        # Trust ceiling depends on real vs simulated TEE
        if is_simulated:
            trust_ceiling = 0.85
            trust_reason = "simulated_trustzone"
        else:
            trust_ceiling = self.trust_ceiling  # 1.0
            trust_reason = "trustzone_hardware_binding"

        t3 = T3Tensor.create_minimal(
            trust_ceiling=trust_ceiling,
            trust_ceiling_reason=trust_reason
        )

        lct = LCT(
            lct_id=lct_id,
            capability_level=CapabilityLevel.HARDWARE,
            entity_type=entity_type,
            subject=f"did:web4:tz:{key_id}",
            binding=binding,
            mrh=MRH(),
            policy=LCTPolicy(),
            t3_tensor=t3,
            v3_tensor=V3Tensor.create_zero(),
            birth_certificate=BirthCertificate.create_stub(
                "TrustZone-bound entity" if not is_simulated else "Simulated TrustZone entity"
            )
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
                "key_handle": metadata.get("key_handle"),
                "machine_identity": metadata.get("machine_identity"),
                "created_at": metadata.get("created_at"),
                "simulated": metadata.get("simulated", False)
            })
        return keys


# Quick test when run directly
if __name__ == "__main__":
    print("=" * 60)
    print("TRUSTZONE BINDING PROVIDER TEST")
    print("=" * 60)

    provider = TrustZoneProvider()

    # Show platform info
    platform = provider.get_platform_info()
    print(f"Platform: {platform.name}")
    print(f"Architecture: {platform.arch}")
    print(f"Has TrustZone: {platform.has_trustzone}")
    print(f"TEE Device: {provider._tee_available}")
    print(f"Max Level: {provider.max_capability_level.name}")
    print(f"Trust Ceiling: {provider.trust_ceiling}")
    print()

    # Create an LCT (may use simulation if TEE not available)
    print("Creating Level 5 AI LCT with TrustZone binding...")
    try:
        lct = provider.create_lct(EntityType.AI, "test-agent")
        print(f"LCT ID: {lct.lct_id}")
        print(f"Level: {lct.capability_level.name}")
        print(f"Entity Type: {lct.entity_type.value}")
        print(f"Hardware Anchor: {lct.binding.hardware_anchor}")
        print(f"Hardware Type: {lct.binding.hardware_type}")
        print(f"T3 Trust Ceiling: {lct.t3_tensor.trust_ceiling}")
        print(f"T3 Ceiling Reason: {lct.t3_tensor.trust_ceiling_reason}")
        print()

        # Sign some data
        print("Signing test data...")
        test_data = b"Hello, Web4 with TrustZone!"
        key_id = lct.lct_id.split(':')[-1]
        sig_result = provider.sign_data(key_id, test_data)
        if sig_result.success:
            print(f"Signature: {sig_result.signature_b64[:32]}...")
        else:
            print(f"Signing failed: {sig_result.error}")
        print()

        # Get attestation
        print("Requesting attestation...")
        att_result = provider.get_attestation(key_id)
        print(f"Success: {att_result.success}")
        print(f"Type: {att_result.attestation_type}")
        print()

    except Exception as e:
        print(f"Error: {e}")

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
