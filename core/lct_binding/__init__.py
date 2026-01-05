"""
LCT Binding Module
==================

Provides hardware and software binding for LCT identity.

Supports:
- Level 4: Software binding (all platforms)
- Level 5: TPM2 binding (Linux with TPM)
- Level 5: TrustZone binding (ARM64 with OP-TEE)

Includes Aliveness Verification Protocol (AVP) for proving
current hardware access - separating identity persistence (DNA)
from aliveness proof (current hardware binding).

Usage:
    from web4.core.lct_binding import (
        create_bound_lct,
        get_provider,
        get_platform_info,
        AlivenessChallenge,
        TrustDegradationPolicy,
    )

    # Auto-detect best available binding
    lct = create_bound_lct(
        entity_type=EntityType.AI,
        name="my-agent",
        preferred_level=CapabilityLevel.HARDWARE
    )

    # Check what we got
    print(f"Level: {lct.capability_level.name}")
    print(f"Hardware: {lct.binding.hardware_anchor is not None}")

    # Create aliveness challenge
    challenge = AlivenessChallenge.create(purpose="trust_verification")

    # Prove aliveness (signs nonce with hardware-bound key)
    proof = provider.prove_aliveness(key_id, challenge)

    # Verify proof (any entity can do this with public key)
    result = provider.verify_aliveness_proof(challenge, proof, lct.binding.public_key)
"""

from .provider import (
    LCTBindingProvider,
    PlatformInfo,
    BindingResult,
    SignatureResult,
    AttestationResult,
    # SAGE PCR Selection (standardized embodiment checks)
    SAGE_PCR_SELECTION,
    SAGE_PCR_MINIMAL,
    SAGE_PCR_FULL,
    # Aliveness Verification Protocol
    AVP_PROTOCOL_VERSION,
    AlivenessChallenge,
    AlivenessProof,
    AlivenessVerificationResult,
    AlivenessFailureType,
    # Exceptions
    AlivenessError,
    HardwareAccessError,
    HardwareCompromisedError,
    ChallengeExpiredError,
    KeyNotFoundError,
)
from .platform_detection import (
    detect_platform,
    get_platform_info,
)
from .trust_policy import (
    # Trust Actions
    TrustAction,
    RelationshipAction,
    RelationshipState,
    RelationshipType,
    # Policy structures
    TrustDegradationPolicy,
    PolicyTemplates,
    RelationshipAlivenessPolicy,
    MutualTrustRecord,
    LCTReference,
    RelationshipLCT,
    RestorationContext,
    # Verification protocol
    VerificationInitiator,
    CostResponsibility,
    # Succession and revocation
    RevocationPolicy,
    SuccessionCertificate,
    WitnessSignature,
)
from .software_provider import SoftwareProvider

# Import hardware providers
# These are always importable but may fallback to simulation if hardware unavailable
from .tpm2_provider import TPM2Provider
from .trustzone_provider import TrustZoneProvider

HAS_TPM2 = True
HAS_TRUSTZONE = True


def get_provider() -> LCTBindingProvider:
    """
    Get the best available binding provider for this platform.

    Returns provider in order of preference:
    1. TPM2Provider (if TPM available)
    2. TrustZoneProvider (if TrustZone available)
    3. SoftwareProvider (always available)
    """
    platform = detect_platform()

    if platform.has_tpm2 and HAS_TPM2:
        return TPM2Provider()
    elif platform.has_trustzone and HAS_TRUSTZONE:
        return TrustZoneProvider()
    else:
        return SoftwareProvider()


def create_bound_lct(
    entity_type,
    name: str = None,
    preferred_level=None
):
    """
    Create an LCT with best available hardware binding.

    Args:
        entity_type: Type of entity (from EntityType enum)
        name: Entity name (optional, used in ID generation)
        preferred_level: Preferred capability level (will fallback if needed)

    Returns:
        LCT with appropriate binding for this platform
    """
    from .platform_detection import detect_platform
    from ..lct_capability_levels import (
        LCT, CapabilityLevel, EntityType, create_minimal_lct
    )

    if preferred_level is None:
        preferred_level = CapabilityLevel.HARDWARE

    provider = get_provider()
    platform = detect_platform()

    # Determine actual level
    actual_level = min(preferred_level, provider.max_capability_level)

    # Create LCT with binding
    lct = provider.create_lct(entity_type, name)

    return lct


__all__ = [
    # Provider base
    'LCTBindingProvider',
    'PlatformInfo',
    'BindingResult',
    'SignatureResult',
    'AttestationResult',
    # Providers
    'SoftwareProvider',
    'TPM2Provider',
    'TrustZoneProvider',
    # Platform detection
    'detect_platform',
    'get_platform_info',
    'get_provider',
    'create_bound_lct',
    'HAS_TPM2',
    'HAS_TRUSTZONE',
    # SAGE PCR Selection
    'SAGE_PCR_SELECTION',
    'SAGE_PCR_MINIMAL',
    'SAGE_PCR_FULL',
    # Aliveness Verification Protocol
    'AVP_PROTOCOL_VERSION',
    'AlivenessChallenge',
    'AlivenessProof',
    'AlivenessVerificationResult',
    'AlivenessFailureType',
    'AlivenessError',
    'HardwareAccessError',
    'HardwareCompromisedError',
    'ChallengeExpiredError',
    'KeyNotFoundError',
    # Trust Policy
    'TrustAction',
    'RelationshipAction',
    'RelationshipState',
    'RelationshipType',
    'TrustDegradationPolicy',
    'PolicyTemplates',
    'RelationshipAlivenessPolicy',
    'MutualTrustRecord',
    'LCTReference',
    'RelationshipLCT',
    'RestorationContext',
    # Verification protocol
    'VerificationInitiator',
    'CostResponsibility',
    # Succession and revocation
    'RevocationPolicy',
    'SuccessionCertificate',
    'WitnessSignature',
]
