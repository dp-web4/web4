# Hardware Binding Implementation Plan

**Status**: Implementation Plan v1.0
**Date**: 2026-01-03
**Author**: CBP Session (Dennis + Claude)
**Machines**: CBP (L4), Legion (L5), Thor (L5), Sprout (L5)

---

## Executive Summary

This plan implements hardware-bound LCT identity across the 4-machine ecosystem with graceful fallback for environments without hardware security access.

| Machine | Platform | Hardware Security | Max Level | Role |
|---------|----------|-------------------|-----------|------|
| **CBP** | WSL2 | None (TPM not exposed) | Level 4 | Development, federation coordinator |
| **Legion** | Native Linux | TPM 2.0 | Level 5 | Reference implementation, high-trust ops |
| **Thor** | ARM64 Linux | TrustZone/OP-TEE | Level 5 | Edge research platform |
| **Sprout** | ARM64 Linux | TrustZone/OP-TEE | Level 5 | Edge deployment target |

---

## Design Principles

### 1. Graceful Degradation

Hardware binding is **preferred but not required**. Systems without hardware security:
- Operate at Level 4 (FULL) instead of Level 5 (HARDWARE)
- Have lower trust ceiling (0.6-0.8 vs 0.8-1.0)
- Cannot be root of hardware trust chains
- CAN still participate in federation, witnessing, and all other operations

### 2. Explicit Capability Declaration

Every LCT explicitly declares its binding type:

```json
{
  "binding": {
    "hardware_anchor": null,           // null = software-only
    "hardware_type": null,             // null = no hardware
    "key_storage": "software",         // "software" | "tpm" | "trustzone" | "secure_element"
    "binding_limitations": [
      "keys_extractable",
      "no_boot_integrity",
      "no_hardware_attestation"
    ]
  }
}
```

### 3. Trust Tier Adjustment

T3 composite scores are capped based on binding type:

| Binding Type | Trust Ceiling | Rationale |
|--------------|---------------|-----------|
| Hardware (TPM/TZ) | 1.0 | Full hardware attestation |
| Software (secure storage) | 0.85 | Keys protected but extractable |
| Software (basic) | 0.75 | Standard file-based keys |
| No binding | 0.5 | Identity not cryptographically bound |

---

## Architecture

### Binding Provider Interface

All machines implement the same interface with platform-specific backends:

```python
class LCTBindingProvider(ABC):
    """Abstract binding provider - implemented per platform."""

    @abstractmethod
    def get_platform_info(self) -> PlatformInfo:
        """Return platform capabilities."""
        pass

    @abstractmethod
    def generate_binding(self, entity_type: EntityType) -> LCTBinding:
        """Generate cryptographic binding for entity."""
        pass

    @abstractmethod
    def sign_data(self, lct_id: str, data: bytes) -> bytes:
        """Sign data with LCT's private key."""
        pass

    @abstractmethod
    def verify_signature(self, lct_id: str, data: bytes, signature: bytes) -> bool:
        """Verify signature from LCT."""
        pass

    @abstractmethod
    def get_attestation(self, lct_id: str) -> Optional[Attestation]:
        """Get hardware attestation if available."""
        pass

    @property
    @abstractmethod
    def max_capability_level(self) -> CapabilityLevel:
        """Maximum capability level this provider supports."""
        pass
```

### Platform Implementations

```
lct_binding/
├── __init__.py
├── provider.py              # Abstract interface
├── platform_detection.py    # Auto-detect platform
├── software_provider.py     # Level 4 fallback (all platforms)
├── tpm2_provider.py         # Level 5 for Legion
├── trustzone_provider.py    # Level 5 for Thor/Sprout
└── tests/
    ├── test_software.py
    ├── test_tpm2.py
    └── test_trustzone.py
```

---

## Machine-Specific Implementation

### CBP (WSL2) - Level 4 Maximum

**Status**: TPM not accessible from WSL2
**Approach**: Software-only binding with explicit limitations

#### Implementation Steps

1. **Create software provider** (`software_provider.py`)
   - Ed25519 key generation
   - Key storage in `~/.web4/identity/` with chmod 600
   - Machine fingerprint from CPU/MAC/hostname
   - Explicit `binding_limitations` field

2. **Trust ceiling enforcement**
   - Cap T3 composite at 0.85
   - Add `trust_ceiling_reason: "software_binding"` to T3

3. **Federation role**
   - CBP can coordinate federation (Level 4 sufficient)
   - Cannot be root of hardware trust chains
   - Can witness software-bound entities

#### Code Location
```
Web4/core/lct_binding/software_provider.py
```

#### Key Structures
```python
@dataclass
class SoftwareBinding:
    """Level 4 software-only binding."""
    entity_type: str
    public_key: str                    # Ed25519 PEM
    key_storage: str = "software"
    machine_fingerprint: str = ""
    created_at: str = ""
    binding_proof: str = ""            # Self-signed

    # Explicit limitations
    hardware_anchor: None = None
    hardware_type: None = None
    binding_limitations: List[str] = field(default_factory=lambda: [
        "keys_extractable",
        "no_boot_integrity",
        "no_hardware_attestation"
    ])
```

---

### Legion (Native Linux) - Level 5 with TPM2

**Status**: Full TPM2 access via `/dev/tpm0`
**Approach**: Hardware-bound identity with EAT attestation

#### Prerequisites

```bash
# Install TPM2 tools and Python bindings
sudo apt install tpm2-tools libtpm2-tss-dev
pip install tpm2-pytss
```

#### Implementation Steps

1. **TPM2 provider** (`tpm2_provider.py`)
   - Key generation in TPM (cannot be extracted)
   - PCR-based sealing for boot integrity
   - EAT token generation for attestation
   - `/dev/tpm0` access

2. **Attestation chain**
   - Platform attestation (PCR values)
   - Key attestation (prove key is in TPM)
   - Application attestation (SAGE identity)

3. **Trust properties**
   - Full 1.0 trust ceiling
   - Can be root of hardware trust chains
   - Can attest other entities

#### Code Location
```
Web4/core/lct_binding/tpm2_provider.py
```

#### Key Structures
```python
@dataclass
class TPM2Binding:
    """Level 5 TPM2 hardware binding."""
    entity_type: str
    public_key: str                    # TPM-resident key handle
    hardware_anchor: str               # EAT token
    hardware_type: str = "tpm2"
    key_storage: str = "tpm"

    # TPM-specific
    tpm_key_handle: str = ""           # Persistent handle
    pcr_policy: Dict[int, str] = None  # PCR values at binding
    attestation_key: str = ""          # AK for remote attestation

    created_at: str = ""
    binding_proof: str = ""            # TPM-signed
    binding_limitations: List[str] = field(default_factory=list)  # Empty for hardware
```

#### TPM2 Operations
```python
class TPM2Provider(LCTBindingProvider):
    def __init__(self):
        from tpm2_pytss import TCTI, ESAPI
        self.tcti = TCTI(device="/dev/tpm0")
        self.esapi = ESAPI(self.tcti)

    def generate_binding(self, entity_type: EntityType) -> TPM2Binding:
        # Create primary key under owner hierarchy
        primary = self.esapi.create_primary(
            ESAPI.TR_RH_OWNER,
            in_sensitive=None,
            in_public=TPM2B_PUBLIC(
                publicArea=TPMT_PUBLIC(
                    type=TPM2_ALG.ECC,
                    nameAlg=TPM2_ALG.SHA256,
                    parameters=TPMU_PUBLIC_PARMS(
                        eccDetail=TPMS_ECC_PARMS(
                            curveID=TPM2_ECC.NIST_P256
                        )
                    )
                )
            )
        )

        # Make key persistent
        handle = self.esapi.evict_control(
            ESAPI.TR_RH_OWNER,
            primary.handle,
            persistent_handle=0x81000001  # Application key range
        )

        # Get attestation
        attestation = self._create_attestation(handle)

        return TPM2Binding(
            entity_type=entity_type.value,
            public_key=self._export_public_key(primary),
            hardware_anchor=attestation.to_eat(),
            tpm_key_handle=hex(handle),
            pcr_policy=self._read_pcrs([0, 7]),
            binding_proof=self._sign_binding(handle, entity_type)
        )
```

---

### Thor & Sprout (ARM64) - Level 5 with TrustZone

**Status**: TrustZone available, OP-TEE setup required
**Approach**: Hardware-bound identity via Trusted Application

#### Prerequisites

```bash
# OP-TEE client library
sudo apt install optee-client-dev

# Check if OP-TEE is running
ls /dev/tee*
```

#### Implementation Steps

1. **TrustZone provider** (`trustzone_provider.py`)
   - OP-TEE client integration
   - Trusted Application for key storage
   - Secure World key operations
   - ARM attestation

2. **Trusted Application** (separate build)
   - Key generation in Secure World
   - Sign operations without key exposure
   - Attestation generation

3. **Trust properties**
   - Full 1.0 trust ceiling
   - ARM hardware attestation
   - Secure World isolation

#### Code Location
```
Web4/core/lct_binding/trustzone_provider.py
HRM/sage/trusted_apps/lct_identity_ta/  # Trusted Application
```

#### Key Structures
```python
@dataclass
class TrustZoneBinding:
    """Level 5 TrustZone hardware binding."""
    entity_type: str
    public_key: str                    # Secure World key reference
    hardware_anchor: str               # ARM attestation token
    hardware_type: str = "trustzone"
    key_storage: str = "trustzone"

    # TrustZone-specific
    ta_uuid: str = ""                  # Trusted Application UUID
    secure_key_id: str = ""            # Key ID in Secure World

    created_at: str = ""
    binding_proof: str = ""            # TA-signed
    binding_limitations: List[str] = field(default_factory=list)
```

---

## Graceful Fallback Flow

```python
def create_lct_with_best_available_binding(
    entity_type: EntityType,
    preferred_level: CapabilityLevel = CapabilityLevel.HARDWARE
) -> LCT:
    """
    Create LCT with best available hardware binding.

    Gracefully falls back to software if hardware unavailable.
    """
    # Detect platform
    platform = detect_platform()

    # Get appropriate provider
    if platform.has_tpm2 and preferred_level >= CapabilityLevel.HARDWARE:
        provider = TPM2Provider()
        actual_level = CapabilityLevel.HARDWARE
        trust_ceiling = 1.0
    elif platform.has_trustzone and preferred_level >= CapabilityLevel.HARDWARE:
        provider = TrustZoneProvider()
        actual_level = CapabilityLevel.HARDWARE
        trust_ceiling = 1.0
    else:
        # Fallback to software
        provider = SoftwareProvider()
        actual_level = min(preferred_level, CapabilityLevel.FULL)
        trust_ceiling = 0.85

        # Log the fallback
        logger.info(
            f"Hardware binding unavailable on {platform.name}, "
            f"falling back to Level {actual_level.value} software binding. "
            f"Trust ceiling: {trust_ceiling}"
        )

    # Generate binding
    binding = provider.generate_binding(entity_type)

    # Create LCT
    lct = LCT(
        lct_id=generate_lct_id(entity_type, provider.machine_identity),
        capability_level=actual_level,
        entity_type=entity_type,
        binding=binding
    )

    # Apply trust ceiling
    lct.t3_tensor.trust_ceiling = trust_ceiling
    lct.t3_tensor.trust_ceiling_reason = (
        None if actual_level == CapabilityLevel.HARDWARE
        else "software_binding"
    )

    return lct
```

---

## Implementation Timeline

### Phase 1: Software Provider (CBP) - This Session

**Goal**: Working Level 4 binding on CBP

1. Create `lct_binding/` module structure
2. Implement `software_provider.py`
3. Implement `platform_detection.py`
4. Add trust ceiling to T3Tensor
5. Test on CBP

**Deliverables**:
- `Web4/core/lct_binding/software_provider.py`
- `Web4/core/lct_binding/platform_detection.py`
- Updated `Web4/core/lct_capability_levels.py` with trust ceiling

### Phase 2: TPM2 Provider (Legion) - Next Legion Session

**Goal**: Working Level 5 binding on Legion

1. Install TPM2 dependencies
2. Implement `tpm2_provider.py`
3. Test key generation and attestation
4. Verify trust chain with CBP

**Deliverables**:
- `Web4/core/lct_binding/tpm2_provider.py`
- TPM2 integration tests
- Cross-platform trust verification

### Phase 3: TrustZone Provider (Thor/Sprout) - Future Session

**Goal**: Working Level 5 binding on ARM64

1. Set up OP-TEE on Thor
2. Create Trusted Application
3. Implement `trustzone_provider.py`
4. Test on Thor, deploy to Sprout

**Deliverables**:
- `Web4/core/lct_binding/trustzone_provider.py`
- `HRM/sage/trusted_apps/lct_identity_ta/`
- ARM64 integration tests

### Phase 4: Federation Integration - After All Platforms

**Goal**: Cross-platform trust chains

1. CBP (L4) ↔ Legion (L5) trust establishment
2. Legion (L5) ↔ Thor (L5) trust chain
3. Full mesh federation testing
4. Document trust propagation rules

---

## Trust Relationships

### Trust Flow with Mixed Levels

```
                    ┌─────────────────┐
                    │  Legion (L5)    │
                    │  TPM2 Bound     │
                    │  Trust: 1.0     │
                    └────────┬────────┘
                             │ witnesses
                             ▼
    ┌─────────────────┐     ┌─────────────────┐
    │  CBP (L4)       │◄────│  Thor (L5)      │
    │  Software Bound │pair │  TrustZone      │
    │  Trust: 0.85    │     │  Trust: 1.0     │
    └────────┬────────┘     └────────┬────────┘
             │ coordinates           │ witnesses
             ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐
    │  Plugin (L2)    │     │  Sprout (L5)    │
    │  Basic          │     │  TrustZone      │
    │  Trust: 0.4     │     │  Trust: 1.0     │
    └─────────────────┘     └─────────────────┘
```

### Trust Propagation Rules

1. **Witnessing**: L5 can witness any level; L4 can witness L4 and below
2. **Trust inheritance**: Child trust ≤ parent trust × 0.9
3. **Cross-level pairing**: Always use lower level's trust ceiling
4. **Federation**: Coordinator doesn't need highest trust level

---

## API Design

### Unified Interface

```python
# Auto-detect and use best available binding
from web4.core.lct_binding import create_bound_lct

lct = create_bound_lct(
    entity_type=EntityType.AI,
    name="sage-consciousness",
    preferred_level=CapabilityLevel.HARDWARE  # Will fallback if needed
)

print(f"Created {lct.lct_id}")
print(f"Level: {lct.capability_level.name}")
print(f"Hardware bound: {lct.binding.hardware_anchor is not None}")
print(f"Trust ceiling: {lct.t3_tensor.trust_ceiling}")
```

### Platform Query

```python
from web4.core.lct_binding import get_platform_info

info = get_platform_info()
print(f"Platform: {info.name}")
print(f"Max level: {info.max_level.name}")
print(f"Hardware: {info.hardware_type or 'none'}")
print(f"Limitations: {info.limitations}")
```

### Signing Operations

```python
from web4.core.lct_binding import get_provider

provider = get_provider()  # Auto-detect

# Sign pattern
signature = provider.sign_data(lct.lct_id, pattern_bytes)

# Verify
valid = provider.verify_signature(lct.lct_id, pattern_bytes, signature)
```

---

## Testing Strategy

### Unit Tests

```python
def test_software_fallback():
    """Verify graceful fallback on platform without hardware."""
    # Force software provider
    with mock_no_hardware():
        lct = create_bound_lct(
            entity_type=EntityType.AI,
            preferred_level=CapabilityLevel.HARDWARE
        )

    assert lct.capability_level == CapabilityLevel.FULL  # Fell back
    assert lct.binding.hardware_anchor is None
    assert lct.t3_tensor.trust_ceiling == 0.85
    assert "software_binding" in lct.t3_tensor.trust_ceiling_reason

def test_trust_ceiling_enforcement():
    """Verify trust scores cannot exceed ceiling."""
    lct = create_software_bound_lct(EntityType.AI)

    # Try to set trust above ceiling
    lct.t3_tensor.technical_competence = 1.0
    lct.t3_tensor.social_reliability = 1.0
    lct.t3_tensor.recompute_composite()

    assert lct.t3_tensor.composite_score <= 0.85  # Capped
```

### Integration Tests

```python
def test_cross_level_pairing():
    """Test L5 (Legion) pairing with L4 (CBP)."""
    legion_lct = load_lct("lct:web4:device:legion")
    cbp_lct = load_lct("lct:web4:ai:cbp-coordinator")

    # Establish pairing
    pairing = establish_pairing(legion_lct, cbp_lct)

    # Verify trust uses lower ceiling
    assert pairing.trust_basis == cbp_lct.t3_tensor.trust_ceiling
```

---

## Security Considerations

### Software Binding Limitations

Level 4 software binding has known limitations:

1. **Key extraction**: Private keys are in filesystem, could be copied
2. **No boot integrity**: Cannot verify system wasn't tampered
3. **No remote attestation**: Cannot prove to remote party that key is protected

These are **explicitly declared** in the LCT:

```json
{
  "binding_limitations": [
    "keys_extractable",
    "no_boot_integrity",
    "no_hardware_attestation"
  ]
}
```

### Mitigation

- **File permissions**: Keys stored with chmod 600
- **Machine fingerprint**: Binds identity to specific machine
- **Trust ceiling**: Explicitly lower trust than hardware-bound
- **Disclosure**: Other entities can query limitations before trusting

---

## References

- **LCT Capability Levels**: `web4-standard/core-spec/lct-capability-levels.md`
- **LCT Core Spec**: `web4-standard/core-spec/LCT-linked-context-token.md`
- **Existing HRM SimulatedLCTIdentity**: `HRM/sage/core/simulated_lct_identity.py`
- **Web4 Hardware Binding Roadmap**: `web4-standard/implementation/reference/hardware_binding_roadmap.md`

---

**Version**: 1.0.0
**Status**: Implementation Plan
**Last Updated**: 2026-01-03

*"Hardware binding is preferred. Software binding is valid. Both are explicit."*
