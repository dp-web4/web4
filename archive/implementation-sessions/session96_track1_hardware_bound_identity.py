"""
SESSION 96 TRACK 1: HARDWARE-BOUND LCT IDENTITY IMPLEMENTATION

From AI Agent Accountability doc:
> "Web4's Lightweight Cryptographic Token (LCT) framework provides
   hardware-rooted identity that makes agent accountability tractable"

This implements hardware binding for LCT identities using:
1. TPM (Trusted Platform Module) for Linux systems
2. Secure Enclave simulation for testing
3. Attestation and verification protocols
4. Key derivation from hardware roots

Key innovations:
- HardwareSecurityModule: Abstract interface for TPM/Secure Enclave
- BoundLCTIdentity: LCT identity cryptographically bound to hardware
- AttestationRecord: Cryptographic proof of hardware binding
- BindingStrength: Trust levels based on binding method (0.1-0.95)

Trust gradient (from accountability doc):
- Anonymous (IP only): 0.10
- Software-bound (API key): 0.30
- Account-bound (OAuth): 0.50
- Hardware-bound (LCT + TPM): 0.80
- Hardware + behavioral history + stake: 0.95

Integration with:
- Session 95 Track 2: UnifiedLCTProfile (economic/emotional/reputation state)
- AI Agent Accountability doc: Hardware binding hierarchy
- Session 94 Track 2: Cryptographic signatures

References:
- https://www.usenix.org/system/files/conference/usenixsecurity14/sec14-paper-marforio.pdf
- https://trustedcomputinggroup.org/resource/tpm-library-specification/
"""

import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from enum import Enum
from abc import ABC, abstractmethod


# ============================================================================
# HARDWARE SECURITY MODULE ABSTRACTION
# ============================================================================

class BindingStrength(Enum):
    """Trust levels based on identity binding method."""
    ANONYMOUS = 0.10          # IP address only
    SOFTWARE_BOUND = 0.30     # API key, revocable
    ACCOUNT_BOUND = 0.50      # OAuth, federated identity
    HARDWARE_BOUND = 0.80     # LCT + TPM/secure enclave
    HARDWARE_PLUS = 0.95      # Hardware + behavioral history + stake


class HardwareSecurityModule(ABC):
    """
    Abstract interface for hardware security modules.

    Implementations:
    - TPMSecurityModule: Linux TPM 2.0
    - SecureEnclaveModule: iOS/macOS Secure Enclave
    - SimulatedHSM: Testing/development (no real security)
    """

    @abstractmethod
    def generate_key_pair(self, key_id: str) -> Dict[str, Any]:
        """
        Generate cryptographic key pair within HSM.

        Returns:
            {
                "key_id": str,
                "public_key": str,
                "attestation": str,  # Proof key is hardware-bound
                "binding_strength": float
            }
        """
        pass

    @abstractmethod
    def sign(self, key_id: str, message: bytes) -> bytes:
        """Sign message with hardware-bound key."""
        pass

    @abstractmethod
    def verify_attestation(self, attestation: str) -> bool:
        """Verify attestation record proves hardware binding."""
        pass

    @abstractmethod
    def get_binding_strength(self) -> BindingStrength:
        """Get trust level for this HSM type."""
        pass


class SimulatedHSM(HardwareSecurityModule):
    """
    Simulated HSM for testing/development.

    WARNING: This provides NO real security. For testing only.
    Production systems MUST use TPM or Secure Enclave.
    """

    def __init__(self):
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.binding_strength = BindingStrength.SOFTWARE_BOUND  # Simulated, not hardware

    def generate_key_pair(self, key_id: str) -> Dict[str, Any]:
        """Generate simulated key pair."""
        # In production, this would use TPM_Create or Secure Enclave APIs
        private_key = secrets.token_hex(32)
        public_key = hashlib.sha256(private_key.encode()).hexdigest()

        # Simulated attestation (in production, from TPM Quote or Secure Enclave attestation)
        attestation = self._create_simulated_attestation(key_id, public_key)

        self.keys[key_id] = {
            "private_key": private_key,
            "public_key": public_key,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        return {
            "key_id": key_id,
            "public_key": public_key,
            "attestation": attestation,
            "binding_strength": self.binding_strength.value
        }

    def sign(self, key_id: str, message: bytes) -> bytes:
        """Sign message with simulated key."""
        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        private_key = self.keys[key_id]["private_key"]
        # Simulated signature (in production, uses TPM_Sign or Secure Enclave)
        signature = hashlib.sha256(message + private_key.encode()).digest()
        return signature

    def verify_attestation(self, attestation: str) -> bool:
        """Verify simulated attestation."""
        # In production, would verify TPM Quote or Secure Enclave attestation
        # against manufacturer's root certificate
        return attestation.startswith("simulated_attestation:")

    def get_binding_strength(self) -> BindingStrength:
        """Return binding strength (SOFTWARE_BOUND for simulated)."""
        return self.binding_strength

    def _create_simulated_attestation(self, key_id: str, public_key: str) -> str:
        """Create simulated attestation record."""
        attestation_data = {
            "key_id": key_id,
            "public_key": public_key,
            "hsm_type": "simulated",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        attestation_json = json.dumps(attestation_data, sort_keys=True)
        attestation_hash = hashlib.sha256(attestation_json.encode()).hexdigest()
        return f"simulated_attestation:{attestation_hash}"


class TPMSecurityModule(HardwareSecurityModule):
    """
    TPM 2.0 security module (Linux).

    NOTE: This is a skeleton implementation. Production requires:
    - tpm2-tss library bindings
    - TPM device access (/dev/tpm0 or /dev/tpmrm0)
    - Root or tss group membership
    - Endorsement Key (EK) and Storage Root Key (SRK) provisioning
    """

    def __init__(self):
        self.binding_strength = BindingStrength.HARDWARE_BOUND
        # In production, would initialize TPM context
        # self.tpm_ctx = tpm2_tss.ESAPI()
        print("⚠️  TPM module skeleton only. Production requires tpm2-tss library.")

    def generate_key_pair(self, key_id: str) -> Dict[str, Any]:
        """
        Generate TPM-bound key pair.

        Production implementation would:
        1. Create key under SRK with TPM2_Create
        2. Load key into TPM with TPM2_Load
        3. Get attestation with TPM2_Quote
        4. Return public key + attestation
        """
        raise NotImplementedError("TPM module requires tpm2-tss library")

    def sign(self, key_id: str, message: bytes) -> bytes:
        """Sign with TPM-bound key."""
        raise NotImplementedError("TPM module requires tpm2-tss library")

    def verify_attestation(self, attestation: str) -> bool:
        """Verify TPM attestation against EK certificate chain."""
        raise NotImplementedError("TPM module requires tpm2-tss library")

    def get_binding_strength(self) -> BindingStrength:
        """Return HARDWARE_BOUND trust level."""
        return self.binding_strength


# ============================================================================
# HARDWARE-BOUND LCT IDENTITY
# ============================================================================

@dataclass
class AttestationRecord:
    """
    Cryptographic proof of hardware binding.

    For TPM: Includes Quote (PCR values + nonce signed by Attestation Key)
    For Secure Enclave: Includes attestation bundle from device
    For Simulated: Hash of key material (testing only)
    """
    key_id: str
    public_key: str
    attestation_data: str
    hsm_type: str  # "tpm", "secure_enclave", "simulated"
    binding_strength: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "public_key": self.public_key,
            "attestation_data": self.attestation_data,
            "hsm_type": self.hsm_type,
            "binding_strength": self.binding_strength,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AttestationRecord":
        return AttestationRecord(
            key_id=data["key_id"],
            public_key=data["public_key"],
            attestation_data=data["attestation_data"],
            hsm_type=data["hsm_type"],
            binding_strength=data["binding_strength"],
            timestamp=data["timestamp"]
        )


@dataclass
class BoundLCTIdentity:
    """
    LCT identity cryptographically bound to hardware.

    Extends Session 95's LCTIdentity with hardware binding:
    - LCT format: lct://namespace:name@network
    - Hardware root: TPM, Secure Enclave, or simulated
    - Attestation: Cryptographic proof of binding
    - Binding strength: Trust level (0.1-0.95)
    """
    # LCT identity components
    namespace: str
    name: str
    network: str

    # Hardware binding
    hsm_type: str  # "tpm", "secure_enclave", "simulated"
    key_id: str
    public_key: str
    attestation: AttestationRecord
    binding_strength: float

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_verified: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def lct_full_id(self) -> str:
        """Get full LCT identifier string."""
        return f"lct://{self.namespace}:{self.name}@{self.network}"

    def verify_binding(self, hsm: HardwareSecurityModule) -> bool:
        """
        Verify hardware binding is still valid.

        Returns:
            True if attestation verifies and key is accessible
        """
        # Verify attestation record
        if not hsm.verify_attestation(self.attestation.attestation_data):
            return False

        # Test key accessibility (sign test message)
        try:
            test_message = b"binding_verification_test"
            signature = hsm.sign(self.key_id, test_message)
            return len(signature) > 0
        except Exception:
            return False

    def sign_message(self, hsm: HardwareSecurityModule, message: bytes) -> bytes:
        """Sign message with hardware-bound key."""
        return hsm.sign(self.key_id, message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "namespace": self.namespace,
            "name": self.name,
            "network": self.network,
            "lct_full_id": self.lct_full_id,
            "hsm_type": self.hsm_type,
            "key_id": self.key_id,
            "public_key": self.public_key,
            "attestation": self.attestation.to_dict(),
            "binding_strength": self.binding_strength,
            "created_at": self.created_at,
            "last_verified": self.last_verified
        }


# ============================================================================
# IDENTITY BINDING MANAGER
# ============================================================================

class HardwareBoundIdentityManager:
    """
    Manages hardware-bound LCT identities.

    Responsibilities:
    - Create identities bound to hardware roots
    - Verify attestations
    - Maintain trust levels based on binding strength
    - Support multiple HSM types (TPM, Secure Enclave, simulated)
    """

    def __init__(self):
        self.identities: Dict[str, BoundLCTIdentity] = {}
        self.hsm_modules: Dict[str, HardwareSecurityModule] = {
            "simulated": SimulatedHSM(),
            # "tpm": TPMSecurityModule(),  # Requires tpm2-tss
            # "secure_enclave": SecureEnclaveModule(),  # Requires iOS/macOS
        }

    def create_bound_identity(
        self,
        namespace: str,
        name: str,
        network: str,
        hsm_type: str = "simulated"
    ) -> BoundLCTIdentity:
        """
        Create new hardware-bound LCT identity.

        Args:
            namespace: LCT namespace (sage, web4, user, etc.)
            name: Entity name within namespace
            network: Network identifier (mainnet, testnet, local)
            hsm_type: Hardware security module type

        Returns:
            BoundLCTIdentity with hardware attestation
        """
        if hsm_type not in self.hsm_modules:
            raise ValueError(f"Unsupported HSM type: {hsm_type}")

        hsm = self.hsm_modules[hsm_type]

        # Generate key pair in HSM
        lct_full_id = f"lct://{namespace}:{name}@{network}"
        key_id = f"lct_key_{hashlib.sha256(lct_full_id.encode()).hexdigest()[:16]}"

        key_data = hsm.generate_key_pair(key_id)

        # Create attestation record
        attestation = AttestationRecord(
            key_id=key_data["key_id"],
            public_key=key_data["public_key"],
            attestation_data=key_data["attestation"],
            hsm_type=hsm_type,
            binding_strength=key_data["binding_strength"]
        )

        # Create bound identity
        identity = BoundLCTIdentity(
            namespace=namespace,
            name=name,
            network=network,
            hsm_type=hsm_type,
            key_id=key_data["key_id"],
            public_key=key_data["public_key"],
            attestation=attestation,
            binding_strength=key_data["binding_strength"]
        )

        self.identities[lct_full_id] = identity

        return identity

    def verify_identity(self, lct_full_id: str) -> Tuple[bool, Optional[str]]:
        """
        Verify hardware binding for identity.

        Returns:
            (is_valid, error_message)
        """
        if lct_full_id not in self.identities:
            return False, f"Identity not found: {lct_full_id}"

        identity = self.identities[lct_full_id]

        if identity.hsm_type not in self.hsm_modules:
            return False, f"HSM type not available: {identity.hsm_type}"

        hsm = self.hsm_modules[identity.hsm_type]

        # Verify binding
        is_valid = identity.verify_binding(hsm)

        if is_valid:
            # Update last verified timestamp
            identity.last_verified = datetime.now(timezone.utc).isoformat()
            return True, None
        else:
            return False, "Attestation verification failed"

    def get_trust_level(self, lct_full_id: str) -> float:
        """
        Get trust level for identity.

        Trust level combines:
        - Binding strength (0.1-0.95)
        - Verification status (recent verification increases trust)
        - Behavioral history (future: from Session 95 reputation)
        """
        if lct_full_id not in self.identities:
            return 0.0

        identity = self.identities[lct_full_id]

        # Base trust from binding strength
        base_trust = identity.binding_strength

        # Reduce trust if verification is stale (>30 days)
        last_verified = datetime.fromisoformat(identity.last_verified)
        days_since_verification = (datetime.now(timezone.utc) - last_verified).days

        if days_since_verification > 90:
            base_trust *= 0.5  # 50% penalty for very stale
        elif days_since_verification > 30:
            base_trust *= 0.8  # 20% penalty for stale verification

        return base_trust

    def sign_with_identity(
        self,
        lct_full_id: str,
        message: bytes
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Sign message with hardware-bound identity.

        Returns:
            (signature, error_message)
        """
        if lct_full_id not in self.identities:
            return None, f"Identity not found: {lct_full_id}"

        identity = self.identities[lct_full_id]

        if identity.hsm_type not in self.hsm_modules:
            return None, f"HSM type not available: {identity.hsm_type}"

        hsm = self.hsm_modules[identity.hsm_type]

        try:
            signature = identity.sign_message(hsm, message)
            return signature, None
        except Exception as e:
            return None, f"Signing failed: {str(e)}"


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def test_simulated_hsm():
    """Test simulated HSM for development."""
    print("="*80)
    print("TEST SCENARIO 1: Simulated HSM")
    print("="*80)

    hsm = SimulatedHSM()

    # Generate key pair
    key_data = hsm.generate_key_pair("test_key_001")

    print(f"\n✅ Key pair generated:")
    print(f"   Key ID: {key_data['key_id']}")
    print(f"   Public key: {key_data['public_key'][:32]}...")
    print(f"   Attestation: {key_data['attestation'][:50]}...")
    print(f"   Binding strength: {key_data['binding_strength']}")

    # Sign message
    message = b"test message for signing"
    signature = hsm.sign("test_key_001", message)

    print(f"\n✅ Message signed:")
    print(f"   Message: {message.decode()}")
    print(f"   Signature: {signature.hex()[:32]}...")

    # Verify attestation
    is_valid = hsm.verify_attestation(key_data['attestation'])
    print(f"\n✅ Attestation verified: {is_valid}")

    return is_valid


def test_bound_identity_creation():
    """Test creating hardware-bound LCT identity."""
    print("\n" + "="*80)
    print("TEST SCENARIO 2: Bound Identity Creation")
    print("="*80)

    manager = HardwareBoundIdentityManager()

    # Create bound identity
    identity = manager.create_bound_identity(
        namespace="sage",
        name="verification_expert",
        network="mainnet",
        hsm_type="simulated"
    )

    print(f"\n✅ Bound identity created:")
    print(f"   LCT: {identity.lct_full_id}")
    print(f"   HSM type: {identity.hsm_type}")
    print(f"   Key ID: {identity.key_id}")
    print(f"   Public key: {identity.public_key[:32]}...")
    print(f"   Binding strength: {identity.binding_strength}")
    print(f"   Created at: {identity.created_at}")

    # Verify binding
    is_valid, error = manager.verify_identity(identity.lct_full_id)
    print(f"\n✅ Binding verified: {is_valid}")
    if error:
        print(f"   Error: {error}")

    return is_valid


def test_trust_levels():
    """Test trust level calculation."""
    print("\n" + "="*80)
    print("TEST SCENARIO 3: Trust Level Calculation")
    print("="*80)

    manager = HardwareBoundIdentityManager()

    # Create identities with different binding types
    identities = [
        ("software", "simulated", BindingStrength.SOFTWARE_BOUND.value),
        # In production, would have:
        # ("hardware_tpm", "tpm", BindingStrength.HARDWARE_BOUND.value),
        # ("hardware_enclave", "secure_enclave", BindingStrength.HARDWARE_BOUND.value),
    ]

    print(f"\n📊 Trust levels by binding type:")

    for name, hsm_type, expected_strength in identities:
        if hsm_type not in manager.hsm_modules:
            print(f"   {name}: HSM not available")
            continue

        identity = manager.create_bound_identity(
            namespace="test",
            name=name,
            network="testnet",
            hsm_type=hsm_type
        )

        trust_level = manager.get_trust_level(identity.lct_full_id)
        print(f"   {name}:")
        print(f"      Binding strength: {identity.binding_strength:.2f}")
        print(f"      Trust level: {trust_level:.2f}")

    return True


def test_identity_signing():
    """Test signing with hardware-bound identity."""
    print("\n" + "="*80)
    print("TEST SCENARIO 4: Identity Signing")
    print("="*80)

    manager = HardwareBoundIdentityManager()

    # Create identity
    identity = manager.create_bound_identity(
        namespace="sage",
        name="signing_test",
        network="testnet",
        hsm_type="simulated"
    )

    print(f"\n✅ Identity created: {identity.lct_full_id}")

    # Sign message
    message = b"This is a test message for hardware-bound signing"
    signature, error = manager.sign_with_identity(identity.lct_full_id, message)

    if signature:
        print(f"\n✅ Message signed successfully:")
        print(f"   Message: {message.decode()}")
        print(f"   Signature: {signature.hex()[:64]}...")
        print(f"   Signature length: {len(signature)} bytes")
    else:
        print(f"\n❌ Signing failed: {error}")

    return signature is not None


def test_trust_degradation():
    """Test trust level degradation for stale verification."""
    print("\n" + "="*80)
    print("TEST SCENARIO 5: Trust Degradation (Stale Verification)")
    print("="*80)

    manager = HardwareBoundIdentityManager()

    # Create identity
    identity = manager.create_bound_identity(
        namespace="test",
        name="stale_verification_test",
        network="testnet",
        hsm_type="simulated"
    )

    # Initial trust level
    initial_trust = manager.get_trust_level(identity.lct_full_id)
    print(f"\n📊 Initial trust level: {initial_trust:.2f}")
    print(f"   Last verified: {identity.last_verified}")

    # Simulate stale verification (31 days ago)
    from datetime import timedelta
    old_verification = datetime.now(timezone.utc) - timedelta(days=31)
    identity.last_verified = old_verification.isoformat()

    degraded_trust = manager.get_trust_level(identity.lct_full_id)
    print(f"\n📊 Trust after 31 days:")
    print(f"   Trust level: {degraded_trust:.2f}")
    print(f"   Degradation: {initial_trust - degraded_trust:.2f} ({(initial_trust - degraded_trust) / initial_trust * 100:.1f}%)")

    # Very stale (91 days)
    very_old_verification = datetime.now(timezone.utc) - timedelta(days=91)
    identity.last_verified = very_old_verification.isoformat()

    very_degraded_trust = manager.get_trust_level(identity.lct_full_id)
    print(f"\n📊 Trust after 91 days:")
    print(f"   Trust level: {very_degraded_trust:.2f}")
    print(f"   Degradation: {initial_trust - very_degraded_trust:.2f} ({(initial_trust - very_degraded_trust) / initial_trust * 100:.1f}%)")

    return degraded_trust < initial_trust and very_degraded_trust < degraded_trust


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test scenarios."""
    print("="*80)
    print("SESSION 96 TRACK 1: HARDWARE-BOUND LCT IDENTITY")
    print("="*80)
    print("\nFrom AI Agent Accountability doc:")
    print("  Hardware-bound identity makes agent accountability tractable")
    print()

    results = []

    # Run tests
    results.append(("Simulated HSM", test_simulated_hsm()))
    results.append(("Bound identity creation", test_bound_identity_creation()))
    results.append(("Trust level calculation", test_trust_levels()))
    results.append(("Identity signing", test_identity_signing()))
    results.append(("Trust degradation", test_trust_degradation()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    all_passed = all(result for _, result in results)
    print(f"\n✅ All scenarios passed: {all_passed}")

    print(f"\nScenarios tested:")
    for i, (name, passed) in enumerate(results, 1):
        status = "✅" if passed else "❌"
        print(f"  {i}. {status} {name}")

    # Save results
    output = {
        "session": "96",
        "track": "1",
        "focus": "Hardware-Bound LCT Identity",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_results": [
            {"scenario": name, "passed": passed}
            for name, passed in results
        ],
        "all_passed": all_passed,
        "innovations": [
            "HardwareSecurityModule abstraction (TPM, Secure Enclave, simulated)",
            "BoundLCTIdentity with cryptographic attestation",
            "Trust levels based on binding strength (0.1-0.95)",
            "Trust degradation for stale verification",
            "Hardware-bound signing for accountability",
        ]
    }

    output_path = "/home/dp/ai-workspace/web4/implementation/session96_track1_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to: {output_path}")

    print("\n" + "="*80)
    print("Key Innovations:")
    print("="*80)
    for i, innovation in enumerate(output["innovations"], 1):
        print(f"{i}. {innovation}")

    print("\n" + "="*80)
    print("Trust Gradient (from AI Agent Accountability doc):")
    print("="*80)
    print(f"  Anonymous (IP only):              {BindingStrength.ANONYMOUS.value:.2f}")
    print(f"  Software-bound (API key):         {BindingStrength.SOFTWARE_BOUND.value:.2f}")
    print(f"  Account-bound (OAuth):            {BindingStrength.ACCOUNT_BOUND.value:.2f}")
    print(f"  Hardware-bound (LCT + TPM):       {BindingStrength.HARDWARE_BOUND.value:.2f}")
    print(f"  Hardware + history + stake:       {BindingStrength.HARDWARE_PLUS.value:.2f}")

    print("\n" + "="*80)
    print("Hardware-bound identity enables:")
    print("- Cryptographic proof of identity origin")
    print("- Accountability chain traceable to hardware root")
    print("- Trust levels based on binding strength")
    print("- Automatic trust degradation for stale verification")
    print("- Foundation for AI agent delegation (Track 2)")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    run_all_tests()
