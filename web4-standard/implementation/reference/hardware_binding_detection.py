#!/usr/bin/env python3
"""
Hardware Binding Capability Detection
======================================

Discovers available hardware security mechanisms on the platform.

Checks for:
- TPM 2.0 (Trusted Platform Module)
- TrustZone / OP-TEE (ARM Trusted Execution Environment)
- Secure Boot status
- Platform identification

This is Phase 1 of the hardware binding roadmap.

Author: Legion Autonomous Web4 Research
Date: 2025-12-05
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class HardwareSecurityType(Enum):
    """Types of hardware security mechanisms"""
    TPM_2_0 = "tpm_2.0"
    TRUSTZONE = "trustzone"
    SECURE_ELEMENT = "secure_element"
    NONE = "none"


@dataclass
class HardwareCapability:
    """Hardware security capabilities"""
    device_model: str
    security_types: List[HardwareSecurityType] = field(default_factory=list)
    tpm_device: Optional[str] = None
    tpm_version: Optional[str] = None
    trustzone_version: Optional[str] = None
    secure_boot_enabled: bool = False
    additional_info: Dict[str, str] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class HardwareBindingDetector:
    """Detect available hardware binding mechanisms"""

    def detect_platform(self) -> str:
        """Detect platform/device model"""
        # Try device tree (ARM/embedded)
        device_tree_path = Path("/proc/device-tree/model")
        if device_tree_path.exists():
            try:
                model = device_tree_path.read_text().strip().rstrip('\x00')
                return model
            except Exception as e:
                print(f"Warning: Could not read device tree: {e}")

        # Try DMI (x86)
        dmi_paths = [
            "/sys/class/dmi/id/product_name",
            "/sys/class/dmi/id/board_name"
        ]
        for path in dmi_paths:
            dmi_path = Path(path)
            if dmi_path.exists():
                try:
                    model = dmi_path.read_text().strip()
                    if model and model != "To be filled by O.E.M.":
                        return model
                except Exception:
                    continue

        # Fallback: hostname
        try:
            import socket
            return f"Unknown ({socket.gethostname()})"
        except Exception:
            return "Unknown"

    def check_tpm(self) -> tuple[Optional[str], Optional[str]]:
        """
        Check for TPM 2.0 device.

        Returns:
            (device_path, version_info) tuple
        """
        # Check for TPM character devices
        tpm_devices = [
            "/dev/tpm0",
            "/dev/tpmrm0"  # TPM resource manager
        ]

        for device in tpm_devices:
            if Path(device).exists():
                # Try to get TPM version
                version_info = self._get_tpm_version(device)
                return device, version_info

        # Check sysfs
        tpm_sysfs = Path("/sys/class/tpm")
        if tpm_sysfs.exists():
            tpm_dirs = list(tpm_sysfs.iterdir())
            if tpm_dirs:
                tpm_dir = tpm_dirs[0]

                # Try to read TPM version from sysfs
                version_file = tpm_dir / "tpm_version_major"
                if version_file.exists():
                    try:
                        version = version_file.read_text().strip()
                        return str(tpm_dir), f"TPM {version}.0"
                    except Exception:
                        pass

                return str(tpm_dir), "TPM (version unknown)"

        return None, None

    def _get_tpm_version(self, device: str) -> Optional[str]:
        """Get TPM version using tpm2_getcap if available"""
        try:
            result = subprocess.run(
                ["tpm2_getcap", "properties-fixed"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Parse output for version
                for line in result.stdout.split('\n'):
                    if 'TPM2_PT_REVISION' in line or 'revision' in line.lower():
                        return line.strip()
                return "TPM 2.0 (detected via tpm2-tools)"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return "TPM (version detection unavailable)"

    def check_trustzone(self) -> Optional[str]:
        """Check for TrustZone / OP-TEE"""
        # Check for TEE devices
        tee_devices = [
            "/dev/tee0",
            "/dev/teepriv0"
        ]

        for device in tee_devices:
            if Path(device).exists():
                return self._get_optee_version()

        # Check for secure monitor in kernel messages
        try:
            result = subprocess.run(
                ["dmesg"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "optee" in result.stdout.lower() or "trustzone" in result.stdout.lower():
                return "TrustZone (detected in dmesg)"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    def _get_optee_version(self) -> str:
        """Get OP-TEE version if available"""
        try:
            result = subprocess.run(
                ["tee-supplicant", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return f"OP-TEE ({result.stdout.strip()})"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return "OP-TEE (version unknown)"

    def check_secure_boot(self) -> bool:
        """Check if secure boot is enabled"""
        # Check EFI secure boot variable
        efi_vars_path = Path("/sys/firmware/efi/efivars")
        if efi_vars_path.exists():
            # Look for SecureBoot variable
            for var_file in efi_vars_path.glob("SecureBoot-*"):
                try:
                    # First 4 bytes are attributes, 5th byte is value
                    data = var_file.read_bytes()
                    if len(data) >= 5:
                        secure_boot_value = data[4]
                        return secure_boot_value == 1
                except Exception:
                    continue

        # Check kernel command line for NVIDIA Jetson
        cmdline_path = Path("/proc/cmdline")
        if cmdline_path.exists():
            try:
                cmdline = cmdline_path.read_text()
                if "tegra_fuse" in cmdline or "secure_boot" in cmdline:
                    return True
            except Exception:
                pass

        return False

    def get_additional_info(self) -> Dict[str, str]:
        """Collect additional security-related information"""
        info = {}

        # Kernel version (affects security features)
        try:
            uname_result = subprocess.run(
                ["uname", "-r"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if uname_result.returncode == 0:
                info["kernel_version"] = uname_result.stdout.strip()
        except Exception:
            pass

        # Check for hardware crypto
        crypto_path = Path("/proc/crypto")
        if crypto_path.exists():
            try:
                crypto_data = crypto_path.read_text()
                if "hardware" in crypto_data.lower():
                    info["hardware_crypto"] = "Available"
            except Exception:
                pass

        # Check for ARM features
        cpuinfo_path = Path("/proc/cpuinfo")
        if cpuinfo_path.exists():
            try:
                cpuinfo = cpuinfo_path.read_text()
                features = []
                for line in cpuinfo.split('\n'):
                    if 'Features' in line or 'flags' in line:
                        if 'aes' in line.lower():
                            features.append("AES")
                        if 'sha' in line.lower():
                            features.append("SHA")
                if features:
                    info["cpu_crypto_features"] = ", ".join(features)
            except Exception:
                pass

        return info

    def get_recommendations(
        self,
        security_types: List[HardwareSecurityType],
        platform: str
    ) -> List[str]:
        """Get implementation recommendations based on available hardware"""
        recommendations = []

        if HardwareSecurityType.TPM_2_0 in security_types:
            recommendations.append(
                "✅ Use TPM 2.0 for key generation and sealing (RECOMMENDED)"
            )
            recommendations.append(
                "   - Generate LCT keys in TPM (never export private key)"
            )
            recommendations.append(
                "   - Seal keys to PCR values for boot integrity"
            )
            recommendations.append(
                "   - Implement remote attestation protocol"
            )
            recommendations.append(
                "   - Install: tpm2-tools, tpm2-pytss")

        if HardwareSecurityType.TRUSTZONE in security_types:
            if HardwareSecurityType.TPM_2_0 not in security_types:
                recommendations.append(
                    "✅ Use TrustZone OP-TEE for secure key storage (RECOMMENDED)"
                )
                recommendations.append(
                    "   - Develop Trusted Application for LCT operations"
                )
                recommendations.append(
                    "   - Store keys in secure world storage"
                )
                recommendations.append(
                    "   - Use TEE client API from normal world"
                )
            else:
                recommendations.append(
                    "ℹ️ TrustZone available as backup to TPM"
                )
                recommendations.append(
                    "   - Can use for secondary keys or failover"
                )

        if not security_types or security_types == [HardwareSecurityType.NONE]:
            recommendations.append(
                "⚠️ NO HARDWARE SECURITY DETECTED"
            )
            recommendations.append(
                "   - Cannot deploy production LCT without hardware binding"
            )
            recommendations.append(
                "   - Options:")
            recommendations.append(
                "     1. Install TPM 2.0 module (if motherboard supports)")
            recommendations.append(
                "     2. Enable TrustZone in kernel configuration")
            recommendations.append(
                "     3. Add external secure element (ATECC608, SE050 via I2C)")
            recommendations.append(
                "     4. Use for development only (software keys)")

        # Platform-specific recommendations
        if "Jetson" in platform:
            if HardwareSecurityType.TRUSTZONE not in security_types:
                recommendations.append(
                    "ℹ️ Jetson platform detected but TrustZone not found"
                )
                recommendations.append(
                    "   - Check kernel config for OP-TEE support"
                )
                recommendations.append(
                    "   - May require custom kernel build"
                )

        return recommendations

    def detect_capabilities(self) -> HardwareCapability:
        """Detect all hardware security capabilities"""
        platform = self.detect_platform()
        security_types = []

        # Check TPM
        tpm_device, tpm_version = self.check_tpm()
        if tpm_device:
            security_types.append(HardwareSecurityType.TPM_2_0)

        # Check TrustZone
        trustzone_version = self.check_trustzone()
        if trustzone_version:
            security_types.append(HardwareSecurityType.TRUSTZONE)

        # Default to NONE if nothing found
        if not security_types:
            security_types.append(HardwareSecurityType.NONE)

        # Check secure boot
        secure_boot = self.check_secure_boot()

        # Get additional info
        additional_info = self.get_additional_info()

        # Get recommendations
        recommendations = self.get_recommendations(security_types, platform)

        return HardwareCapability(
            device_model=platform,
            security_types=security_types,
            tpm_device=tpm_device,
            tpm_version=tpm_version,
            trustzone_version=trustzone_version,
            secure_boot_enabled=secure_boot,
            additional_info=additional_info,
            recommendations=recommendations
        )


def print_capability_report(cap: HardwareCapability):
    """Print hardware capability report"""
    print("=" * 70)
    print("HARDWARE BINDING CAPABILITY REPORT")
    print("=" * 70)

    print(f"\n📱 Platform: {cap.device_model}")

    print(f"\n🔐 Security Mechanisms:")
    found_security = False
    for sec_type in cap.security_types:
        if sec_type == HardwareSecurityType.TPM_2_0:
            print(f"  ✅ TPM 2.0")
            print(f"     Device: {cap.tpm_device}")
            if cap.tpm_version:
                print(f"     Version: {cap.tpm_version}")
            found_security = True
        elif sec_type == HardwareSecurityType.TRUSTZONE:
            print(f"  ✅ TrustZone / OP-TEE")
            if cap.trustzone_version:
                print(f"     Version: {cap.trustzone_version}")
            found_security = True
        elif sec_type == HardwareSecurityType.NONE:
            print(f"  ❌ No hardware security detected")

    print(f"\n🔒 Secure Boot: {'✅ Enabled' if cap.secure_boot_enabled else '❌ Disabled or Unknown'}")

    if cap.additional_info:
        print(f"\nℹ️  Additional Information:")
        for key, value in cap.additional_info.items():
            print(f"  {key}: {value}")

    print(f"\n💡 Recommendations:")
    for rec in cap.recommendations:
        print(f"  {rec}")

    # Summary
    print(f"\n{'='*70}")
    if HardwareSecurityType.TPM_2_0 in cap.security_types or \
       HardwareSecurityType.TRUSTZONE in cap.security_types:
        print("✅ HARDWARE BINDING AVAILABLE - Can proceed to Phase 2")
        if HardwareSecurityType.TPM_2_0 in cap.security_types:
            print("   Recommended: TPM 2.0 integration (Phase 2)")
        else:
            print("   Recommended: TrustZone integration (Phase 3)")
    else:
        print("⚠️  NO HARDWARE BINDING - Production LCT deployment blocked")
        print("   Action required: Enable hardware security or use external SE")
    print("=" * 70)


def export_json_report(cap: HardwareCapability, output_path: str):
    """Export capability report as JSON"""
    import json

    data = {
        "device_model": cap.device_model,
        "security_types": [st.value for st in cap.security_types],
        "tpm": {
            "available": cap.tpm_device is not None,
            "device": cap.tpm_device,
            "version": cap.tpm_version
        },
        "trustzone": {
            "available": cap.trustzone_version is not None,
            "version": cap.trustzone_version
        },
        "secure_boot_enabled": cap.secure_boot_enabled,
        "additional_info": cap.additional_info,
        "recommendations": cap.recommendations,
        "production_ready": (
            HardwareSecurityType.TPM_2_0 in cap.security_types or
            HardwareSecurityType.TRUSTZONE in cap.security_types
        )
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ JSON report saved to: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect hardware security capabilities for Web4 LCT binding"
    )
    parser.add_argument(
        "--json",
        type=str,
        help="Export report as JSON to specified file"
    )

    args = parser.parse_args()

    print("Detecting hardware security capabilities...\n")

    detector = HardwareBindingDetector()
    capabilities = detector.detect_capabilities()

    print_capability_report(capabilities)

    if args.json:
        export_json_report(capabilities, args.json)
