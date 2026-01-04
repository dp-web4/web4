"""
Abstract Binding Provider Interface
====================================

Defines the interface all binding providers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class HardwareType(str, Enum):
    """Types of hardware security modules."""
    NONE = "none"
    TPM2 = "tpm2"
    TRUSTZONE = "trustzone"
    SECURE_ELEMENT = "secure_element"


class KeyStorage(str, Enum):
    """Where cryptographic keys are stored."""
    SOFTWARE = "software"
    TPM = "tpm"
    TRUSTZONE = "trustzone"
    SECURE_ENCLAVE = "secure_enclave"


@dataclass
class PlatformInfo:
    """Information about the current platform's capabilities."""
    name: str                          # e.g., "cbp-wsl2", "legion-linux", "thor-arm64"
    os: str                            # e.g., "linux", "wsl2"
    arch: str                          # e.g., "x86_64", "aarch64"

    has_tpm2: bool = False             # TPM 2.0 available
    has_trustzone: bool = False        # ARM TrustZone available
    has_secure_element: bool = False   # Secure Element available

    hardware_type: HardwareType = HardwareType.NONE
    max_level: int = 4                 # Maximum capability level

    # Machine identity
    machine_fingerprint: str = ""
    machine_identity: str = ""

    # Limitations for software-only
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "os": self.os,
            "arch": self.arch,
            "has_tpm2": self.has_tpm2,
            "has_trustzone": self.has_trustzone,
            "has_secure_element": self.has_secure_element,
            "hardware_type": self.hardware_type.value,
            "max_level": self.max_level,
            "machine_identity": self.machine_identity,
            "limitations": self.limitations
        }


@dataclass
class BindingResult:
    """Result of a binding operation."""
    success: bool
    binding: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class SignatureResult:
    """Result of a signing operation."""
    success: bool
    signature: Optional[bytes] = None
    signature_b64: Optional[str] = None
    algorithm: str = "Ed25519"
    error: Optional[str] = None


@dataclass
class AttestationResult:
    """Hardware attestation result."""
    success: bool
    attestation_token: Optional[str] = None  # EAT or similar
    attestation_type: str = "none"           # "eat", "tpm2_quote", "arm_psa"
    pcr_values: Optional[Dict[int, str]] = None
    error: Optional[str] = None


class LCTBindingProvider(ABC):
    """
    Abstract base class for LCT binding providers.

    Implementations:
    - SoftwareProvider: Level 4, file-based keys
    - TPM2Provider: Level 5, TPM 2.0 hardware
    - TrustZoneProvider: Level 5, ARM TrustZone
    """

    @abstractmethod
    def get_platform_info(self) -> PlatformInfo:
        """
        Get information about this platform's capabilities.

        Returns:
            PlatformInfo with hardware detection results
        """
        pass

    @abstractmethod
    def generate_keypair(self, key_id: str) -> BindingResult:
        """
        Generate a new keypair for binding.

        Args:
            key_id: Identifier for the key (used for storage/retrieval)

        Returns:
            BindingResult with public key and binding proof
        """
        pass

    @abstractmethod
    def sign_data(self, key_id: str, data: bytes) -> SignatureResult:
        """
        Sign data with a previously generated key.

        Args:
            key_id: Identifier of the signing key
            data: Raw bytes to sign

        Returns:
            SignatureResult with signature bytes
        """
        pass

    @abstractmethod
    def verify_signature(
        self,
        public_key: str,
        data: bytes,
        signature: bytes
    ) -> bool:
        """
        Verify a signature.

        Args:
            public_key: Public key (PEM or provider-specific format)
            data: Original data that was signed
            signature: Signature bytes to verify

        Returns:
            True if signature is valid
        """
        pass

    @abstractmethod
    def get_attestation(self, key_id: str) -> AttestationResult:
        """
        Get hardware attestation for a key.

        Args:
            key_id: Identifier of the key to attest

        Returns:
            AttestationResult (may indicate no attestation available)
        """
        pass

    @abstractmethod
    def create_lct(self, entity_type, name: str = None):
        """
        Create a complete LCT with binding.

        Args:
            entity_type: Type of entity
            name: Optional name for ID generation

        Returns:
            LCT instance with appropriate binding
        """
        pass

    @property
    @abstractmethod
    def max_capability_level(self):
        """Maximum capability level this provider supports."""
        pass

    @property
    @abstractmethod
    def key_storage_type(self) -> KeyStorage:
        """How keys are stored by this provider."""
        pass

    @property
    @abstractmethod
    def hardware_type(self) -> HardwareType:
        """Type of hardware security (if any)."""
        pass

    @property
    def trust_ceiling(self) -> float:
        """
        Maximum trust score for entities using this provider.

        Hardware-bound: 1.0
        Software-bound: 0.85
        """
        if self.hardware_type != HardwareType.NONE:
            return 1.0
        return 0.85

    @property
    def binding_limitations(self) -> List[str]:
        """
        List of security limitations for this provider.

        Empty for hardware providers.
        """
        if self.hardware_type != HardwareType.NONE:
            return []
        return [
            "keys_extractable",
            "no_boot_integrity",
            "no_hardware_attestation"
        ]
