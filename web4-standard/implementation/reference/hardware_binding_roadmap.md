# Hardware Binding Implementation Roadmap
## From Design to Production - P0 Blocker Resolution

**Date**: 2025-12-05
**Author**: Legion Autonomous Web4 Research
**Status**: Implementation Plan
**Priority**: P0 (Blocking production deployment)

---

## Executive Summary

Hardware binding is **the foundation** of LCT unforgeability. Without it, Web4 identity is just signed messages - copyable, forgeable, meaningless for trust.

**Current State**: Platform detection working, but keys stored in filesystem (copyable)
**Required State**: Keys generated/sealed in hardware, never exposed to software
**Available Hardware**: Jetson AGX Thor (TPM/TrustZone), Jetson Orin Nano (TrustZone)

This roadmap provides a **4-phase implementation path** from current state to production hardware binding.

---

## Problem Statement

### What We Have (Platform Identification)

```python
# Current: sage/core/lct_identity_integration.py
device_tree_path = Path("/proc/device-tree/model")
model = device_tree_path.read_text().strip()
# Returns: "Jetson AGX Thor" or "Jetson Orin Nano"

# Current: sage/data/keys/Thor_ed25519.key
private_key = Ed25519PrivateKey.generate()
# Key stored in filesystem - COPYABLE!
```

**Attack**: Anyone with filesystem access can copy `Thor_ed25519.key` and impersonate Thor from any machine.

### What We Need (Hardware Binding)

```python
# Required: Keys in TPM/TrustZone
tpm = TPM2Device()
key_handle = tpm.create_primary(hierarchy="owner", template="ecc_p256")
# Key generated INSIDE hardware, NEVER exported

# Signing requires physical access to device
signature = tpm.sign(key_handle, data)
# Even with filesystem access, attacker cannot extract key
```

**Security**: Key exists only in hardware. Cloning filesystem doesn't clone identity.

---

## Available Hardware

### Jetson AGX Thor

**Security Features**:
- ✅ ARM TrustZone (Cortex-A78AE cores)
- ✅ TPM 2.0 (likely - check `ls /dev/tpm*`)
- ✅ Secure Boot support
- ✅ Hardware crypto accelerators

**Best Option**: TPM 2.0 (if present) or TrustZone OP-TEE

### Jetson Orin Nano

**Security Features**:
- ✅ ARM TrustZone (Cortex-A78AE cores)
- ❓ TPM 2.0 (unlikely on dev kit)
- ✅ Secure Boot support
- ✅ Hardware crypto accelerators

**Best Option**: TrustZone OP-TEE

---

## Implementation Phases

### Phase 1: Hardware Detection & Capability Discovery (Week 1)

**Goal**: Determine what hardware security is available on Thor and Sprout.

**Tasks**:
1. Check for TPM 2.0
2. Investigate TrustZone configuration
3. Document available secure storage
4. Identify limitations

**Deliverables**:
- Hardware capability report
- Recommended path per device
- Fallback options if primary unavailable

**Code**: `hardware_binding_detection.py`

```python
"""
Hardware Binding Capability Detection
======================================

Discovers available hardware security on NVIDIA Jetson platforms.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
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
    security_types: List[HardwareSecurityType]
    tpm_device: Optional[str] = None
    trustzone_version: Optional[str] = None
    secure_boot_enabled: bool = False
    recommendations: List[str] = None


class HardwareBindingDetector:
    """Detect available hardware binding mechanisms"""

    def detect_platform(self) -> str:
        """Detect Jetson platform"""
        device_tree_path = Path("/proc/device-tree/model")

        if device_tree_path.exists():
            model = device_tree_path.read_text().strip()
            return model

        return "Unknown"

    def check_tpm(self) -> Optional[str]:
        """Check for TPM 2.0 device"""
        # Check for TPM character devices
        tpm_devices = [
            "/dev/tpm0",
            "/dev/tpmrm0"  # TPM resource manager
        ]

        for device in tpm_devices:
            if Path(device).exists():
                return device

        # Check sysfs
        tpm_sysfs = Path("/sys/class/tpm")
        if tpm_sysfs.exists():
            tpm_dirs = list(tpm_sysfs.iterdir())
            if tpm_dirs:
                return str(tpm_dirs[0])

        return None

    def check_trustzone(self) -> Optional[str]:
        """Check for TrustZone / OP-TEE"""
        # Check for TEE supplicant
        tee_devices = [
            "/dev/tee0",
            "/dev/teepriv0"
        ]

        for device in tee_devices:
            if Path(device).exists():
                return "OP-TEE"

        # Check for secure monitor calls (requires root)
        # This is platform-specific - NVIDIA uses different interfaces

        return None

    def check_secure_boot(self) -> bool:
        """Check if secure boot is enabled"""
        # NVIDIA-specific: Check fuse settings
        # This typically requires reading from tegra_fuse or similar

        # Check EFI secure boot
        efi_secureboot = Path("/sys/firmware/efi/efivars/SecureBoot-*")
        # TODO: Implement proper check

        return False  # Conservative default

    def get_recommendations(
        self,
        security_types: List[HardwareSecurityType]
    ) -> List[str]:
        """Get implementation recommendations based on available hardware"""
        recommendations = []

        if HardwareSecurityType.TPM_2_0 in security_types:
            recommendations.append(
                "Use TPM 2.0 for key generation and sealing (preferred)"
            )
            recommendations.append(
                "Seal keys to PCR values for boot integrity"
            )

        if HardwareSecurityType.TRUSTZONE in security_types:
            if HardwareSecurityType.TPM_2_0 not in security_types:
                recommendations.append(
                    "Use TrustZone OP-TEE for secure key storage (primary)"
                )
            else:
                recommendations.append(
                    "Use TrustZone as backup/fallback to TPM"
                )

        if not security_types or security_types == [HardwareSecurityType.NONE]:
            recommendations.append(
                "⚠️ NO HARDWARE SECURITY AVAILABLE"
            )
            recommendations.append(
                "Cannot deploy production LCT without hardware binding"
            )
            recommendations.append(
                "Consider: External secure element (ATECC608, SE050)"
            )

        return recommendations

    def detect_capabilities(self) -> HardwareCapability:
        """Detect all hardware security capabilities"""
        platform = self.detect_platform()
        security_types = []

        # Check TPM
        tpm_device = self.check_tpm()
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

        # Get recommendations
        recommendations = self.get_recommendations(security_types)

        return HardwareCapability(
            device_model=platform,
            security_types=security_types,
            tpm_device=tpm_device,
            trustzone_version=trustzone_version,
            secure_boot_enabled=secure_boot,
            recommendations=recommendations
        )


def print_capability_report(cap: HardwareCapability):
    """Print hardware capability report"""
    print("=" * 70)
    print("HARDWARE BINDING CAPABILITY REPORT")
    print("=" * 70)

    print(f"\nPlatform: {cap.device_model}")

    print(f"\nSecurity Mechanisms:")
    for sec_type in cap.security_types:
        if sec_type == HardwareSecurityType.TPM_2_0:
            print(f"  ✅ TPM 2.0: {cap.tpm_device}")
        elif sec_type == HardwareSecurityType.TRUSTZONE:
            print(f"  ✅ TrustZone: {cap.trustzone_version}")
        elif sec_type == HardwareSecurityType.NONE:
            print(f"  ❌ No hardware security detected")

    print(f"\nSecure Boot: {'✅ Enabled' if cap.secure_boot_enabled else '❌ Disabled'}")

    print(f"\nRecommendations:")
    for i, rec in enumerate(cap.recommendations, 1):
        print(f"  {i}. {rec}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    detector = HardwareBindingDetector()
    capabilities = detector.detect_capabilities()
    print_capability_report(capabilities)
```

### Phase 2: TPM Integration (Week 2-3)

**Goal**: Implement TPM-based key generation and sealing for Thor (if TPM available).

**Dependencies**:
- Python library: `tpm2-pytss` or `python-tpm2-tools`
- System tools: `tpm2-tools` package

**Tasks**:
1. Install TPM libraries
2. Implement key generation in TPM
3. Implement signing operations via TPM
4. Seal keys to PCR values
5. Test attestation protocol

**Deliverables**:
- `tpm_lct_identity.py` - TPM-bound LCT identity
- `tpm_attestation.py` - Remote attestation
- Tests validating key non-extractability

**API Design**:
```python
class TPMLCTIdentity:
    """TPM-bound LCT identity"""

    def __init__(self, tpm_device: str = "/dev/tpm0"):
        self.tpm = TPM2Device(tpm_device)

    def generate_lct_key(
        self,
        lct_id: str,
        pcr_selection: List[int] = [0, 1, 2, 3, 7]
    ) -> str:
        """
        Generate LCT signing key in TPM, sealed to PCRs.

        Returns: Public key (hex)
        """
        # Create primary key in owner hierarchy
        primary = self.tpm.create_primary(
            hierarchy="owner",
            template="ecc_p256"
        )

        # Create LCT key under primary, sealed to PCRs
        lct_key = self.tpm.create(
            parent=primary,
            template="ecc_p256_sign",
            auth_policy=self._create_pcr_policy(pcr_selection)
        )

        # Save key handle and public key
        self.tpm.persist(lct_key)

        return self.tpm.read_public(lct_key)

    def sign_with_lct(
        self,
        lct_id: str,
        data: bytes
    ) -> bytes:
        """
        Sign data with LCT key (requires correct PCR values).

        This only works if system booted through correct code path.
        """
        key_handle = self._get_lct_key_handle(lct_id)

        # This will fail if PCRs don't match sealed policy
        signature = self.tpm.sign(
            key=key_handle,
            digest=data,
            scheme="ecdsa_sha256"
        )

        return signature

    def create_attestation(
        self,
        lct_id: str,
        nonce: bytes
    ) -> Dict:
        """
        Create TPM attestation proving:
        - Device has TPM with specific EK
        - System booted through measured code path (PCRs)
        - LCT key exists in this TPM
        """
        # Quote PCR values signed by AK
        quote = self.tpm.quote(
            key=self._get_attestation_key(),
            pcr_selection=[0, 1, 2, 3, 7],
            qualifying_data=nonce
        )

        # Include EK certificate
        ek_cert = self.tpm.read_ek_cert()

        return {
            "quote": quote,
            "ek_cert": ek_cert,
            "lct_id": lct_id,
            "pcr_values": self.tpm.read_pcrs([0, 1, 2, 3, 7])
        }
```

### Phase 3: TrustZone Integration (Week 3-4)

**Goal**: Implement TrustZone OP-TEE integration for devices without TPM.

**Dependencies**:
- OP-TEE libraries
- TrustZone-enabled kernel
- Trusted Application development tools

**Tasks**:
1. Set up OP-TEE environment
2. Develop Trusted Application for LCT keys
3. Implement secure storage interface
4. Test key isolation from normal world

**Deliverables**:
- `trustzone_lct_identity.py` - TrustZone-bound LCT
- OP-TEE Trusted Application source
- Integration tests

**Architecture**:
```
┌─────────────────────────────────────┐
│  Normal World (Linux)               │
│  ┌───────────────────────────────┐  │
│  │ Web4 Application              │  │
│  │  - LCT operations             │  │
│  │  - Delegation signing         │  │
│  └───────────┬───────────────────┘  │
│              │ TEE Client API       │
│              ▼                       │
│  ┌───────────────────────────────┐  │
│  │ libteec (TEE Client Library)  │  │
│  └───────────┬───────────────────┘  │
└──────────────┼──────────────────────┘
               │ SMC (Secure Monitor Call)
┌──────────────▼──────────────────────┐
│  Secure World (OP-TEE)              │
│  ┌───────────────────────────────┐  │
│  │ LCT Trusted Application       │  │
│  │  - Key generation             │  │
│  │  - Signing operations         │  │
│  │  - Secure storage             │  │
│  └───────────────────────────────┘  │
│                                     │
│  Hardware: ARM TrustZone           │
└─────────────────────────────────────┘
```

### Phase 4: Integration & Testing (Week 5)

**Goal**: Integrate hardware-bound identity into existing Web4/SAGE systems.

**Tasks**:
1. Update `lct_registry.py` to use hardware binding
2. Migrate existing keys to hardware (one-time ceremony)
3. Update SAGE federation to use hardware-bound keys
4. End-to-end testing with hardware attestation
5. Document migration path

**Deliverables**:
- Updated LCT registry with hardware binding
- Migration scripts
- Updated deployment documentation
- Test suite validating hardware binding

**Code Changes**:
```python
# web4-standard/implementation/reference/lct_registry.py

class LCTRegistry:
    """LCT registry with hardware-bound identity"""

    def __init__(self, hardware_binding: bool = True):
        self.hardware_binding = hardware_binding

        if hardware_binding:
            # Detect available hardware
            detector = HardwareBindingDetector()
            caps = detector.detect_capabilities()

            # Initialize appropriate backend
            if HardwareSecurityType.TPM_2_0 in caps.security_types:
                self.identity_backend = TPMLCTIdentity()
            elif HardwareSecurityType.TRUSTZONE in caps.security_types:
                self.identity_backend = TrustZoneLCTIdentity()
            else:
                raise ValueError("No hardware security available - cannot create production LCT")
        else:
            # Fallback for development/testing only
            self.identity_backend = SoftwareLCTIdentity()
            logging.warning("⚠️ Using software keys - NOT FOR PRODUCTION")

    def mint_lct(
        self,
        entity_type: EntityType,
        entity_identifier: str,
        witnesses: List[str]
    ) -> Tuple[LCT, str]:
        """Mint LCT with hardware-bound key"""

        # Generate key in hardware (TPM/TrustZone)
        public_key = self.identity_backend.generate_key(entity_identifier)

        # Create birth certificate
        birth_cert = self._create_birth_certificate(
            entity_type=entity_type,
            entity_identifier=entity_identifier,
            public_key=public_key,
            witnesses=witnesses
        )

        # Sign with hardware-bound key
        signature = self.identity_backend.sign(
            entity_identifier,
            birth_cert.to_bytes()
        )

        birth_cert.signature = signature

        # Create LCT
        lct = LCT(
            lct_id=f"lct:web4:{entity_type.value.lower()}:{entity_identifier}",
            entity_type=entity_type,
            public_key=public_key,
            birth_certificate=birth_cert,
            hardware_bound=True,
            hardware_type=self.identity_backend.get_hardware_type()
        )

        return lct, ""
```

---

## Testing Strategy

### Unit Tests
- Key generation in hardware
- Signing operations
- Attestation creation
- Key non-extractability

### Integration Tests
- Full LCT lifecycle with hardware binding
- SAGE federation with hardware-bound keys
- Web4 authorization with hardware attestation
- Delegation signing with hardware keys

### Security Tests
- Attempt to extract keys (should fail)
- Clone filesystem, verify keys don't work
- Tamper with PCRs, verify sealed keys inaccessible
- Replay attestation (should fail with nonce)

---

## Migration Path

### Development → Production

**Phase 1**: Development (Software Keys)
- Use software keys for rapid iteration
- Mark all LCTs as `hardware_bound=false`
- Warn: "NOT FOR PRODUCTION"

**Phase 2**: Hardware Binding Available
- Detect hardware capabilities
- Offer hardware-bound key generation
- Coexist software + hardware keys (flagged)

**Phase 3**: Hardware Required
- Refuse to mint production LCTs without hardware
- Migrate existing software keys (one-time ceremony)
- Retire software key support except for testing

### Key Migration Ceremony

For existing deployments with software keys:

1. **Backup**: Export all LCT metadata (not keys!)
2. **Generate Hardware Keys**: Create new keys in TPM/TrustZone
3. **Create New Birth Certificates**: With hardware-bound keys
4. **Witness Attestation**: Existing witnesses attest to key change
5. **Update Trust Oracle**: Map old LCT ID → new hardware-bound key
6. **Deprecation Period**: Accept both keys for 30 days
7. **Retire Software Keys**: After attestation complete

---

## Success Criteria

### Phase 1 Complete
- ✅ Hardware capabilities documented for Thor & Sprout
- ✅ Recommended path identified per device

### Phase 2 Complete
- ✅ TPM integration working on Thor (if available)
- ✅ Keys generated in TPM, never in software
- ✅ Attestation protocol validated

### Phase 3 Complete
- ✅ TrustZone integration working
- ✅ Fallback path for devices without TPM

### Phase 4 Complete
- ✅ LCT registry uses hardware binding by default
- ✅ SAGE federation uses hardware-bound keys
- ✅ Tests validate key non-extractability
- ✅ **Web4 can claim production-ready with hardware binding**

---

## Resources Required

**Software**:
- `tpm2-tools` (TPM utilities)
- `tpm2-pytss` or similar (Python TPM library)
- OP-TEE SDK (TrustZone development)
- Build toolchain for Trusted Applications

**Documentation**:
- NVIDIA Jetson Security documentation
- TPM 2.0 specification
- OP-TEE documentation
- ARM TrustZone Architecture Reference Manual

**Time**:
- Phase 1: 1 week (detection & planning)
- Phase 2: 2 weeks (TPM integration)
- Phase 3: 1-2 weeks (TrustZone integration)
- Phase 4: 1 week (integration & testing)

**Total**: 5-6 weeks for complete hardware binding implementation

---

## Conclusion

Hardware binding is **not optional** for production Web4. It's the foundation of LCT unforgeability.

**This roadmap provides a clear path** from current state (platform detection, software keys) to production state (hardware-bound keys, attestation).

**Recommended Start**: Phase 1 (capability detection) - can be done immediately with no risk, provides data for Phase 2/3 decisions.

**Expected Outcome**: Web4 LCT identity becomes truly unforgeable, enabling production deployment with confidence in the trust model.

---

**Status**: ROADMAP COMPLETE - READY FOR IMPLEMENTATION

**Next Step**: Run Phase 1 capability detection on Thor and Sprout

---

Co-Authored-By: Legion (Claude Sonnet 4.5)
