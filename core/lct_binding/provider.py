"""
Abstract Binding Provider Interface
====================================

Defines the interface all binding providers must implement.

Includes Aliveness Verification Protocol (AVP) for proving
current hardware access - separating identity persistence (DNA)
from aliveness proof (current hardware binding).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import os
import uuid


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


# =============================================================================
# Aliveness Verification Protocol (AVP) Data Structures
# =============================================================================

@dataclass
class AlivenessChallenge:
    """
    Challenge sent by verifier to prove aliveness.

    External entities send this to request proof that the target LCT
    currently has access to its bound hardware.
    """
    nonce: bytes                    # 32 random bytes
    timestamp: datetime             # When challenge was created
    challenge_id: str               # UUID for correlation
    expires_at: datetime            # Challenge expiration

    # Optional context
    verifier_lct_id: Optional[str] = None  # Who is asking
    purpose: Optional[str] = None          # Why verification is requested

    @classmethod
    def create(
        cls,
        verifier_lct_id: Optional[str] = None,
        purpose: Optional[str] = None,
        ttl_seconds: int = 60
    ) -> "AlivenessChallenge":
        """Create a new aliveness challenge with random nonce."""
        now = datetime.now(timezone.utc)
        return cls(
            nonce=os.urandom(32),
            timestamp=now,
            challenge_id=str(uuid.uuid4()),
            expires_at=now + timedelta(seconds=ttl_seconds),
            verifier_lct_id=verifier_lct_id,
            purpose=purpose
        )

    def is_expired(self) -> bool:
        """Check if challenge has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for transmission."""
        return {
            "nonce": self.nonce.hex(),
            "timestamp": self.timestamp.isoformat(),
            "challenge_id": self.challenge_id,
            "expires_at": self.expires_at.isoformat(),
            "verifier_lct_id": self.verifier_lct_id,
            "purpose": self.purpose
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlivenessChallenge":
        """Deserialize from transmission."""
        return cls(
            nonce=bytes.fromhex(data["nonce"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            challenge_id=data["challenge_id"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            verifier_lct_id=data.get("verifier_lct_id"),
            purpose=data.get("purpose")
        )


@dataclass
class AlivenessProof:
    """
    Proof returned by prover demonstrating hardware access.

    The signature proves the entity currently has access to the
    hardware-bound private key.
    """
    challenge_id: str               # Correlates to challenge
    signature: bytes                # Nonce signed by hardware-bound key
    public_key: str                 # PEM-encoded public key (must match LCT)
    hardware_type: str              # "tpm2", "trustzone", or "software"
    timestamp: datetime             # When proof was generated

    # Optional attestation (for additional assurance)
    attestation_quote: Optional[str] = None  # TPM quote or TrustZone attestation
    pcr_values: Optional[Dict[int, str]] = None  # PCR state at signing time

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for transmission."""
        return {
            "challenge_id": self.challenge_id,
            "signature": self.signature.hex(),
            "public_key": self.public_key,
            "hardware_type": self.hardware_type,
            "timestamp": self.timestamp.isoformat(),
            "attestation_quote": self.attestation_quote,
            "pcr_values": self.pcr_values
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlivenessProof":
        """Deserialize from transmission."""
        return cls(
            challenge_id=data["challenge_id"],
            signature=bytes.fromhex(data["signature"]),
            public_key=data["public_key"],
            hardware_type=data["hardware_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            attestation_quote=data.get("attestation_quote"),
            pcr_values=data.get("pcr_values")
        )


@dataclass
class AlivenessVerificationResult:
    """
    Result of verifying an aliveness proof.

    External entities use this to make trust decisions.
    """
    valid: bool                              # Signature verified correctly
    public_key_matches_lct: bool = True      # Public key matches expected LCT
    hardware_type: str = "unknown"           # Type of hardware that signed
    challenge_fresh: bool = True             # Challenge not expired

    # For verifier's trust decision
    trust_recommendation: float = 0.0        # 0.0-1.0 based on verification
    degradation_reason: Optional[str] = None # Why trust might be reduced

    # Details
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "public_key_matches_lct": self.public_key_matches_lct,
            "hardware_type": self.hardware_type,
            "challenge_fresh": self.challenge_fresh,
            "trust_recommendation": self.trust_recommendation,
            "degradation_reason": self.degradation_reason,
            "error": self.error
        }


# =============================================================================
# Aliveness Exceptions
# =============================================================================

class AlivenessError(Exception):
    """Base exception for aliveness verification."""
    pass


class HardwareAccessError(AlivenessError):
    """Hardware is not accessible (destroyed, disconnected, etc.)."""
    pass


class HardwareCompromisedError(AlivenessError):
    """Hardware may be compromised (PCR mismatch, etc.)."""
    pass


class ChallengeExpiredError(AlivenessError):
    """Challenge has expired."""
    pass


class KeyNotFoundError(AlivenessError):
    """Requested key not found in hardware."""
    pass


# =============================================================================
# Abstract Provider Interface
# =============================================================================

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

    # =========================================================================
    # Aliveness Verification Protocol (AVP) Methods
    # =========================================================================

    def prove_aliveness(
        self,
        key_id: str,
        challenge: AlivenessChallenge
    ) -> AlivenessProof:
        """
        Prove aliveness by signing a challenge nonce.

        This method proves that the entity currently has access to the
        hardware-bound private key. If hardware is lost or inaccessible,
        this will raise HardwareAccessError.

        Args:
            key_id: The key to sign with
            challenge: The challenge from verifier

        Returns:
            AlivenessProof with signed nonce

        Raises:
            HardwareAccessError: If hardware is not accessible
            KeyNotFoundError: If key_id doesn't exist
            ChallengeExpiredError: If challenge has expired
        """
        # Check challenge freshness
        if challenge.is_expired():
            raise ChallengeExpiredError(
                f"Challenge {challenge.challenge_id} expired at {challenge.expires_at}"
            )

        # Sign the nonce
        sign_result = self.sign_data(key_id, challenge.nonce)

        if not sign_result.success:
            raise HardwareAccessError(
                f"Failed to sign challenge: {sign_result.error}"
            )

        # Get public key from stored metadata
        public_key = self._get_public_key(key_id)

        return AlivenessProof(
            challenge_id=challenge.challenge_id,
            signature=sign_result.signature,
            public_key=public_key,
            hardware_type=self.hardware_type.value,
            timestamp=datetime.now(timezone.utc)
        )

    def verify_aliveness_proof(
        self,
        challenge: AlivenessChallenge,
        proof: AlivenessProof,
        expected_public_key: str
    ) -> AlivenessVerificationResult:
        """
        Verify an aliveness proof.

        Can be called by any entity to verify another's proof.
        Does not require hardware access (uses public key only).

        Args:
            challenge: Original challenge
            proof: Proof to verify
            expected_public_key: Public key from target's LCT

        Returns:
            AlivenessVerificationResult
        """
        # 1. Check challenge freshness
        if challenge.is_expired():
            return AlivenessVerificationResult(
                valid=False,
                challenge_fresh=False,
                trust_recommendation=0.0,
                degradation_reason="challenge_expired",
                error=f"Challenge expired at {challenge.expires_at}"
            )

        # 2. Check challenge ID matches
        if challenge.challenge_id != proof.challenge_id:
            return AlivenessVerificationResult(
                valid=False,
                trust_recommendation=0.0,
                degradation_reason="challenge_id_mismatch",
                error="Proof does not match challenge"
            )

        # 3. Check public key matches expected
        # Normalize keys for comparison (remove whitespace differences)
        expected_normalized = expected_public_key.strip()
        proof_normalized = proof.public_key.strip()

        if expected_normalized != proof_normalized:
            return AlivenessVerificationResult(
                valid=False,
                public_key_matches_lct=False,
                hardware_type=proof.hardware_type,
                trust_recommendation=0.0,
                degradation_reason="public_key_mismatch",
                error="Proof public key does not match expected LCT binding"
            )

        # 4. Verify signature
        signature_valid = self.verify_signature(
            public_key=proof.public_key,
            data=challenge.nonce,
            signature=proof.signature
        )

        if not signature_valid:
            return AlivenessVerificationResult(
                valid=False,
                public_key_matches_lct=True,
                hardware_type=proof.hardware_type,
                trust_recommendation=0.0,
                degradation_reason="signature_invalid",
                error="Signature verification failed"
            )

        # 5. Success - determine trust recommendation based on hardware type
        trust_rec = 1.0
        if proof.hardware_type == "software":
            trust_rec = 0.85  # Software binding ceiling

        return AlivenessVerificationResult(
            valid=True,
            public_key_matches_lct=True,
            hardware_type=proof.hardware_type,
            challenge_fresh=True,
            trust_recommendation=trust_rec
        )

    def _get_public_key(self, key_id: str) -> str:
        """
        Get public key for a stored key.

        Override in subclasses to retrieve from appropriate storage.
        """
        raise NotImplementedError("Subclasses must implement _get_public_key")
