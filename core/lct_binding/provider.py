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

import hashlib

# AVP Protocol version for payload binding
AVP_PROTOCOL_VERSION = b"AVP-1.1"


@dataclass
class AlivenessChallenge:
    """
    Challenge sent by verifier to prove aliveness.

    External entities send this to request proof that the target LCT
    currently has access to its bound hardware.

    IMPORTANT: The prover signs the CANONICAL PAYLOAD, not just the nonce.
    This binds the proof to a specific verifier, session, and action,
    preventing relay and rebind attacks.
    """
    nonce: bytes                    # 32 random bytes
    timestamp: datetime             # When challenge was created
    challenge_id: str               # UUID for correlation
    expires_at: datetime            # Challenge expiration

    # Binding context (prevents relay attacks)
    verifier_lct_id: Optional[str] = None  # Who is asking (bound into signature)
    session_id: Optional[str] = None       # Unique session ID
    intended_action_hash: Optional[str] = None  # Hash of what this proof authorizes
    purpose: Optional[str] = None          # Human-readable purpose

    @classmethod
    def create(
        cls,
        verifier_lct_id: Optional[str] = None,
        purpose: Optional[str] = None,
        session_id: Optional[str] = None,
        intended_action_hash: Optional[str] = None,
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
            session_id=session_id or str(uuid.uuid4()),
            intended_action_hash=intended_action_hash,
            purpose=purpose
        )

    def get_signing_payload(self) -> bytes:
        """
        Get the canonical payload that must be signed.

        This binds the proof to:
        - Protocol version (prevents cross-version attacks)
        - Challenge ID (correlation)
        - Nonce (freshness)
        - Verifier identity (prevents relay to different verifier)
        - Expiration (time-bounds the proof)
        - Session and action (prevents reuse in different context)

        Provers MUST sign this payload, NOT just the nonce.
        """
        # Build canonical payload
        components = [
            AVP_PROTOCOL_VERSION,
            self.challenge_id.encode('utf-8'),
            self.nonce,
            (self.verifier_lct_id or "").encode('utf-8'),
            self.expires_at.isoformat().encode('utf-8'),
            (self.session_id or "").encode('utf-8'),
            bytes.fromhex(self.intended_action_hash) if self.intended_action_hash else b"",
            (self.purpose or "").encode('utf-8'),
        ]

        # Hash all components together
        hasher = hashlib.sha256()
        for component in components:
            hasher.update(component)

        return hasher.digest()

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
            "session_id": self.session_id,
            "intended_action_hash": self.intended_action_hash,
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
            session_id=data.get("session_id"),
            intended_action_hash=data.get("intended_action_hash"),
            purpose=data.get("purpose")
        )


@dataclass
class AlivenessProof:
    """
    Proof returned by prover demonstrating hardware access.

    The signature proves the entity currently has access to the
    hardware-bound private key.

    SECURITY NOTE: Verifiers MUST use expected_public_key from the LCT,
    NOT any key provided by the prover. The public_key field is deprecated
    and included only for debugging/logging. Trusting prover-supplied keys
    is a critical vulnerability.
    """
    challenge_id: str               # Correlates to challenge
    signature: bytes                # Signature over canonical payload
    hardware_type: str              # "tpm2", "trustzone", or "software"
    timestamp: datetime             # When proof was generated

    # DEPRECATED: Verifiers MUST ignore this and use LCT.binding.public_key
    # Included only for debugging/audit trails
    _public_key_debug: Optional[str] = None

    # Optional attestation (for additional assurance)
    attestation_quote: Optional[str] = None  # TPM quote or TrustZone attestation
    pcr_values: Optional[Dict[int, str]] = None  # PCR state at signing time

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for transmission."""
        return {
            "challenge_id": self.challenge_id,
            "signature": self.signature.hex(),
            "hardware_type": self.hardware_type,
            "timestamp": self.timestamp.isoformat(),
            "attestation_quote": self.attestation_quote,
            "pcr_values": self.pcr_values,
            # Debug only - verifiers must not trust this
            "_public_key_debug": self._public_key_debug
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlivenessProof":
        """Deserialize from transmission."""
        return cls(
            challenge_id=data["challenge_id"],
            signature=bytes.fromhex(data["signature"]),
            hardware_type=data["hardware_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            attestation_quote=data.get("attestation_quote"),
            pcr_values=data.get("pcr_values"),
            _public_key_debug=data.get("_public_key_debug") or data.get("public_key")
        )


class AlivenessFailureType(Enum):
    """
    Types of aliveness failure with different trust implications.

    Verifiers use this to apply appropriate degradation based on WHY
    verification failed, not just that it failed.
    """
    # Success case
    NONE = "none"

    # Network/reachability issues
    TIMEOUT = "timeout"              # Challenge expired before response (network jitter)
    UNREACHABLE = "unreachable"      # Transport failure (no route, refused, offline)
    PROOF_STALE = "proof_stale"      # Prover responded after expiry

    # Hardware issues
    HARDWARE_ACCESS_ERROR = "hardware_access_error"  # Prover reports hardware inaccessible
    HARDWARE_COMPROMISED = "hardware_compromised"    # PCR mismatch outside policy window

    # Cryptographic failures
    SIGNATURE_INVALID = "signature_invalid"  # Signature doesn't verify (fork/clone/tamper)
    KEY_MISMATCH = "key_mismatch"            # Different hardware entirely

    # PCR drift (not necessarily compromise)
    PCR_DRIFT_EXPECTED = "pcr_drift_expected"    # Within policy window (OS update, etc.)
    PCR_DRIFT_UNEXPECTED = "pcr_drift_unexpected"  # Outside window, treat as suspicious

    # Challenge issues
    CHALLENGE_EXPIRED = "challenge_expired"      # Verifier-side expiry
    CHALLENGE_ID_MISMATCH = "challenge_id_mismatch"


@dataclass
class AlivenessVerificationResult:
    """
    Result of verifying an aliveness proof.

    External entities use this to make trust decisions. This structure
    provides the raw facts; the verifier's TrustDegradationPolicy computes
    any trust scores.

    NOTE: We do NOT return a trust_recommendation float. That would blur
    the boundary of verifier autonomy. Instead, we return scores and
    failure_type, letting the policy compute trust.
    """
    valid: bool                              # Signature verified correctly
    challenge_fresh: bool = True             # Challenge not expired
    hardware_type: str = "unknown"           # Type of hardware that signed

    # Failure classification (for policy-based degradation)
    failure_type: AlivenessFailureType = AlivenessFailureType.NONE

    # Two-axis trust scores (raw, before policy)
    # Continuity: "Are you still the embodied instance?"
    # Content: "Is the data consistent and signed?"
    continuity_score: float = 0.0    # 0.0 = no continuity, 1.0 = verified
    content_score: float = 0.0       # 0.0 = no content trust, 1.0 = verified

    # Attestation details (if Quote was used)
    pcr_status: Optional[str] = None  # "match", "drift_expected", "drift_unexpected"
    attestation_verified: bool = False

    # Details
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "challenge_fresh": self.challenge_fresh,
            "hardware_type": self.hardware_type,
            "failure_type": self.failure_type.value,
            "continuity_score": self.continuity_score,
            "content_score": self.content_score,
            "pcr_status": self.pcr_status,
            "attestation_verified": self.attestation_verified,
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
        Prove aliveness by signing the canonical challenge payload.

        This method proves that the entity currently has access to the
        hardware-bound private key. If hardware is lost or inaccessible,
        this will raise HardwareAccessError.

        IMPORTANT: Signs the CANONICAL PAYLOAD (includes verifier, session,
        action hash), not just the nonce. This prevents relay attacks.

        Args:
            key_id: The key to sign with
            challenge: The challenge from verifier

        Returns:
            AlivenessProof with signed canonical payload

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

        # Sign the CANONICAL PAYLOAD, not just the nonce
        signing_payload = challenge.get_signing_payload()
        sign_result = self.sign_data(key_id, signing_payload)

        if not sign_result.success:
            raise HardwareAccessError(
                f"Failed to sign challenge: {sign_result.error}"
            )

        # Get public key for debug/audit only (verifiers must not trust this)
        public_key = self._get_public_key(key_id)

        return AlivenessProof(
            challenge_id=challenge.challenge_id,
            signature=sign_result.signature,
            hardware_type=self.hardware_type.value,
            timestamp=datetime.now(timezone.utc),
            _public_key_debug=public_key  # Debug only - verifiers must ignore
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

        SECURITY: Uses expected_public_key from LCT binding, NOT any key
        provided by the prover. The proof._public_key_debug field is
        intentionally ignored.

        Args:
            challenge: Original challenge
            proof: Proof to verify
            expected_public_key: Public key from target's LCT (TRUST THIS ONLY)

        Returns:
            AlivenessVerificationResult with failure_type and scores
        """
        # 1. Check challenge freshness
        if challenge.is_expired():
            return AlivenessVerificationResult(
                valid=False,
                challenge_fresh=False,
                failure_type=AlivenessFailureType.CHALLENGE_EXPIRED,
                continuity_score=0.0,
                content_score=0.0,
                error=f"Challenge expired at {challenge.expires_at}"
            )

        # 2. Check challenge ID matches
        if challenge.challenge_id != proof.challenge_id:
            return AlivenessVerificationResult(
                valid=False,
                failure_type=AlivenessFailureType.CHALLENGE_ID_MISMATCH,
                continuity_score=0.0,
                content_score=0.0,
                error="Proof does not match challenge"
            )

        # 3. Verify signature over CANONICAL PAYLOAD using expected_public_key
        # NOTE: We use expected_public_key (from LCT), NOT proof._public_key_debug
        signing_payload = challenge.get_signing_payload()
        signature_valid = self.verify_signature(
            public_key=expected_public_key,  # ALWAYS use LCT's key
            data=signing_payload,
            signature=proof.signature
        )

        if not signature_valid:
            return AlivenessVerificationResult(
                valid=False,
                hardware_type=proof.hardware_type,
                failure_type=AlivenessFailureType.SIGNATURE_INVALID,
                continuity_score=0.0,
                content_score=0.5,  # Content may still be valid
                error="Signature verification failed"
            )

        # 4. Success - determine scores based on hardware type
        # Hardware binding provides continuity trust
        # Software binding only provides content trust
        if proof.hardware_type == "software":
            # Software can verify content, but not embodiment continuity
            return AlivenessVerificationResult(
                valid=True,
                hardware_type=proof.hardware_type,
                challenge_fresh=True,
                failure_type=AlivenessFailureType.NONE,
                continuity_score=0.0,   # Software cannot prove continuity
                content_score=0.85      # Can prove content authenticity
            )
        else:
            # Hardware binding proves both continuity and content
            return AlivenessVerificationResult(
                valid=True,
                hardware_type=proof.hardware_type,
                challenge_fresh=True,
                failure_type=AlivenessFailureType.NONE,
                continuity_score=1.0,   # Hardware proves embodiment
                content_score=1.0       # And content authenticity
            )

    def _get_public_key(self, key_id: str) -> str:
        """
        Get public key for a stored key.

        Override in subclasses to retrieve from appropriate storage.
        """
        raise NotImplementedError("Subclasses must implement _get_public_key")
