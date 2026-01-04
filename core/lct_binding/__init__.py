"""
LCT Binding Module
==================

Provides hardware and software binding for LCT identity.

Supports:
- Level 4: Software binding (all platforms)
- Level 5: TPM2 binding (Linux with TPM)
- Level 5: TrustZone binding (ARM64 with OP-TEE)

Usage:
    from web4.core.lct_binding import (
        create_bound_lct,
        get_provider,
        get_platform_info
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
"""

from .provider import (
    LCTBindingProvider,
    PlatformInfo,
    BindingResult,
)
from .platform_detection import (
    detect_platform,
    get_platform_info,
)
from .software_provider import SoftwareProvider

# Import hardware providers if available
try:
    from .tpm2_provider import TPM2Provider
    HAS_TPM2 = True
except ImportError:
    HAS_TPM2 = False

try:
    from .trustzone_provider import TrustZoneProvider
    HAS_TRUSTZONE = True
except ImportError:
    HAS_TRUSTZONE = False


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
    'LCTBindingProvider',
    'PlatformInfo',
    'BindingResult',
    'SoftwareProvider',
    'detect_platform',
    'get_platform_info',
    'get_provider',
    'create_bound_lct',
]
