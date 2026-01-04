"""
Platform Detection
==================

Detects hardware security capabilities of the current platform.

Checks for:
- TPM 2.0 (Linux /dev/tpm0)
- ARM TrustZone (OP-TEE /dev/tee*)
- Secure Elements (platform-specific)
"""

import os
import platform
import socket
import hashlib
import uuid
from pathlib import Path
from typing import Optional
from functools import lru_cache

from .provider import PlatformInfo, HardwareType


def _get_machine_fingerprint() -> str:
    """
    Generate stable machine fingerprint.

    Combines:
    - CPU serial (if available)
    - Primary MAC address
    - Hostname
    """
    components = []

    # Try to get CPU serial (ARM devices often have this)
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'Serial' in line:
                    serial = line.split(':')[1].strip()
                    if serial and serial != '0000000000000000':
                        components.append(f"cpu:{serial}")
                        break
    except:
        pass

    # Get MAC address
    try:
        mac_int = uuid.getnode()
        mac_hex = ':'.join(['{:02x}'.format((mac_int >> elements) & 0xff)
                           for elements in range(0, 8*6, 8)][::-1])
        components.append(f"mac:{mac_hex}")
    except:
        pass

    # Get hostname
    try:
        hostname = socket.gethostname()
        components.append(f"host:{hostname}")
    except:
        pass

    # Hash to fixed-length fingerprint
    fingerprint_str = "|".join(components)
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()


def _get_machine_identity() -> str:
    """
    Get human-readable machine identity.

    Format: "hostname-macaddr_short"
    """
    hostname = socket.gethostname()

    try:
        mac_int = uuid.getnode()
        mac_short = '{:06x}'.format(mac_int & 0xFFFFFF)
    except:
        mac_short = 'unknown'

    return f"{hostname}-{mac_short}"


def _check_tpm2() -> bool:
    """Check if TPM 2.0 is available."""
    # Check for TPM device
    if Path('/dev/tpm0').exists():
        return True
    if Path('/dev/tpmrm0').exists():
        return True

    # Check sysfs
    tpm_class = Path('/sys/class/tpm')
    if tpm_class.exists():
        tpm_devices = list(tpm_class.iterdir())
        if tpm_devices:
            return True

    return False


def _check_trustzone() -> bool:
    """Check if ARM TrustZone/OP-TEE is available."""
    # Check for TEE device (OP-TEE)
    if Path('/dev/tee0').exists():
        return True
    if Path('/dev/teepriv0').exists():
        return True

    # Check for generic TEE
    tee_devices = list(Path('/dev').glob('tee*'))
    if tee_devices:
        return True

    return False


def _check_wsl() -> bool:
    """Check if running in WSL."""
    # Check kernel version string
    try:
        with open('/proc/version', 'r') as f:
            version = f.read().lower()
            if 'microsoft' in version or 'wsl' in version:
                return True
    except:
        pass

    # Check for WSL-specific paths
    if Path('/mnt/c').exists():
        return True

    return False


def _get_arch() -> str:
    """Get CPU architecture."""
    machine = platform.machine().lower()
    if machine in ('x86_64', 'amd64'):
        return 'x86_64'
    elif machine in ('aarch64', 'arm64'):
        return 'aarch64'
    elif machine.startswith('arm'):
        return 'arm'
    return machine


@lru_cache(maxsize=1)
def detect_platform() -> PlatformInfo:
    """
    Detect current platform capabilities.

    Returns:
        PlatformInfo with hardware detection results

    Cached - only runs detection once per process.
    """
    hostname = socket.gethostname()
    arch = _get_arch()
    is_wsl = _check_wsl()

    # Determine OS
    if is_wsl:
        os_name = "wsl2"
    else:
        os_name = platform.system().lower()

    # Check hardware security
    has_tpm2 = _check_tpm2() and not is_wsl  # TPM not accessible in WSL
    has_trustzone = _check_trustzone() and arch == 'aarch64'

    # Determine hardware type and max level
    if has_tpm2:
        hardware_type = HardwareType.TPM2
        max_level = 5
        limitations = []
    elif has_trustzone:
        hardware_type = HardwareType.TRUSTZONE
        max_level = 5
        limitations = []
    else:
        hardware_type = HardwareType.NONE
        max_level = 4
        limitations = [
            "keys_extractable",
            "no_boot_integrity",
            "no_hardware_attestation"
        ]

    # Build platform name
    platform_name = f"{hostname}-{os_name}"

    return PlatformInfo(
        name=platform_name,
        os=os_name,
        arch=arch,
        has_tpm2=has_tpm2,
        has_trustzone=has_trustzone,
        has_secure_element=False,  # Not implemented yet
        hardware_type=hardware_type,
        max_level=max_level,
        machine_fingerprint=_get_machine_fingerprint(),
        machine_identity=_get_machine_identity(),
        limitations=limitations
    )


def get_platform_info() -> PlatformInfo:
    """
    Get platform information (alias for detect_platform).

    Returns:
        PlatformInfo with hardware detection results
    """
    return detect_platform()


def clear_platform_cache():
    """Clear the cached platform detection (for testing)."""
    detect_platform.cache_clear()


# Quick test when run directly
if __name__ == "__main__":
    info = detect_platform()
    print("=" * 60)
    print("PLATFORM DETECTION")
    print("=" * 60)
    print(f"Name:           {info.name}")
    print(f"OS:             {info.os}")
    print(f"Architecture:   {info.arch}")
    print(f"TPM 2.0:        {info.has_tpm2}")
    print(f"TrustZone:      {info.has_trustzone}")
    print(f"Hardware Type:  {info.hardware_type.value}")
    print(f"Max Level:      {info.max_level}")
    print(f"Machine ID:     {info.machine_identity}")
    print(f"Fingerprint:    {info.machine_fingerprint[:32]}...")
    if info.limitations:
        print(f"Limitations:    {', '.join(info.limitations)}")
    print("=" * 60)
