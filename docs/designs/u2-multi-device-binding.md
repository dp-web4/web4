# U2 Design: Multi-Device Binding Module

**Status**: SCOPED
**Date**: 2026-03-17
**Spec**: `web4-standard/core-spec/multi-device-lct-binding.md`
**Patent**: 305 family (US 11,477,027 + US 12,278,913)

---

## Problem Statement

The multi-device binding spec (v1.0.0 Draft) defines protocols for device
constellations, enrollment, cross-device witnessing, trust computation, and
recovery. The SDK has no module implementing these. The `Binding` dataclass
in `lct.py` has `hardware_anchor: Optional[str]` but nothing beyond that.

**Gap**: spec exists → SDK does not implement it.

## Scope

A `web4.binding` module (~300-400 lines) that provides:
1. Hardware anchor type taxonomy with trust ceilings
2. Device constellation management (add, remove, query)
3. Constellation trust computation
4. Cross-device witness tracking
5. Recovery quorum logic

**Not in scope** (future work):
- Actual cryptographic operations (key generation, signing, attestation)
- Platform-specific code (iOS SecureEnclave, Android StrongBox, WebAuthn)
- TPM2 integration (uses existing `hardware_anchor` string, not raw TPM calls)
- Network protocols for enrollment ceremony (QR/NFC transfer)

The module models the *data structures and trust logic* from the spec.
Real crypto and hardware calls are platform-specific and belong in
language-specific SDKs (Swift, Kotlin, Rust), not this Python reference SDK.

## Patent 305 Alignment

| Patent Concept | SDK Mapping |
|---------------|-------------|
| Controlled Object | Entity (via `EntityType`) |
| Electronic Controller | `HardwareAnchor` (new dataclass) |
| Pairing (patent sense) | `Binding` (LCT) + `DeviceConstellation` enrollment |
| Association (patent sense) | `MRHPairing` (existing) |
| Programmed State | `DeviceStatus` enum (active/suspended/revoked) |
| Access Data | `DeviceLCTInfo.anchor_attestation` |
| Authorization Certificate | Enrollment ceremony witness signatures |
| Authentication Controller | Constellation trust computation + quorum |

The 305CIP protocol (Claim 1: two administrators, authentication controller,
encrypted key portions) maps to the enrollment ceremony where existing device
+ new device + society each hold key material.

## Data Structures

### Enums

```python
class AnchorType(str, Enum):
    """Hardware anchor types per spec §2.2."""
    PHONE_SECURE_ELEMENT = "phone_secure_element"
    FIDO2 = "fido2"
    TPM2 = "tpm2"
    SOFTWARE = "software"

class DeviceStatus(str, Enum):
    """Device lifecycle within constellation."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
```

### Constants

```python
# Trust ceilings per spec §4.2
ANCHOR_TRUST_WEIGHT: dict[AnchorType, float] = {
    AnchorType.PHONE_SECURE_ELEMENT: 0.95,
    AnchorType.FIDO2: 0.98,
    AnchorType.TPM2: 0.93,
    AnchorType.SOFTWARE: 0.40,
}

CONSTELLATION_TRUST_CEILING: dict[str, float] = {
    "single_software": 0.40,
    "single_phone_se": 0.75,
    "single_fido2": 0.80,
    "phone_fido2": 0.90,
    "phone_fido2_tpm": 0.95,
    "3_plus_diverse": 0.98,
}

# Witness decay thresholds per spec §4.3
WITNESS_DECAY_TABLE: list[tuple[int, float]] = [
    (7, 1.0),    # ≤7 days: no decay
    (30, 0.9),   # ≤30 days
    (90, 0.7),   # ≤90 days
    (180, 0.5),  # ≤180 days
    (999999, 0.3),  # >180 days
]
```

### Dataclasses

```python
@dataclass(frozen=True)
class HardwareAnchor:
    """Hardware root of trust for a device."""
    anchor_type: AnchorType
    platform: str = ""              # "ios", "android", "linux", "windows"
    attestation_format: str = ""    # "apple_app_attest", "android_key_attestation", "tpm2_quote"
    manufacturer: str = ""

    @property
    def trust_weight(self) -> float:
        return ANCHOR_TRUST_WEIGHT[self.anchor_type]

    @property
    def is_hardware_bound(self) -> bool:
        return self.anchor_type != AnchorType.SOFTWARE


@dataclass
class DeviceRecord:
    """A device within a constellation."""
    device_lct_id: str
    anchor: HardwareAnchor
    enrolled_at: str
    last_witnessed: str
    trust_weight: float              # Weight within constellation (sums to 1.0)
    status: DeviceStatus = DeviceStatus.ACTIVE
    cross_witnesses: list[str] = field(default_factory=list)  # LCT IDs of devices that witnessed this one
    revoked_at: str = ""
    revocation_reason: str = ""


@dataclass
class DeviceConstellation:
    """Collection of devices bound to a root identity."""
    root_lct_id: str
    devices: list[DeviceRecord] = field(default_factory=list)
    recovery_quorum: int = 1

    @property
    def active_devices(self) -> list[DeviceRecord]:
        return [d for d in self.devices if d.status == DeviceStatus.ACTIVE]

    @property
    def device_count(self) -> int:
        return len(self.active_devices)
```

## Functions

### Constellation Management

```python
def enroll_device(
    constellation: DeviceConstellation,
    device_lct_id: str,
    anchor: HardwareAnchor,
    witnesses: list[str],
    timestamp: str,
) -> DeviceRecord:
    """
    Add a device to the constellation.

    For genesis (first device): witnesses may be empty.
    For additional devices: witnesses must include ≥1 existing constellation device.
    Updates recovery quorum automatically.

    Raises ValueError if device already enrolled or if non-genesis enrollment
    has no existing-device witness.
    """

def remove_device(
    constellation: DeviceConstellation,
    device_lct_id: str,
    reason: str,  # "lost" | "sold" | "compromised" | "upgrade"
    authorizing_devices: list[str],
    timestamp: str,
) -> None:
    """
    Remove a device from the constellation.

    Raises ValueError if quorum not met or device not found.
    """

def default_recovery_quorum(device_count: int) -> int:
    """Per spec §5.2: all if ≤2, 2 if ≤4, majority otherwise."""
```

### Trust Computation

```python
def witness_freshness(days_since_witness: int) -> float:
    """Decay factor per spec §4.3 witness decay table."""

def compute_constellation_trust(constellation: DeviceConstellation) -> float:
    """
    Aggregate trust from device constellation per spec §3.4.

    Components:
    1. Weighted device trust (anchor weight × freshness)
    2. Coherence bonus (diverse anchor types: 0-20%)
    3. Cross-witness density (mesh completeness: 0-10%)

    Returns: clamped [0.0, trust_ceiling] where ceiling depends
    on constellation composition.
    """

def constellation_trust_ceiling(constellation: DeviceConstellation) -> float:
    """Max trust achievable given current anchor type mix."""

def coherence_bonus(devices: list[DeviceRecord]) -> float:
    """Per spec §3.4: 0% for 1 type, 8% for 2, 15% for 3, 20% for 4+."""

def cross_witness_density(devices: list[DeviceRecord]) -> float:
    """Ratio of actual recent witness pairs to possible pairs."""
```

### Cross-Device Witnessing

```python
def record_cross_witness(
    constellation: DeviceConstellation,
    device_a_id: str,
    device_b_id: str,
    timestamp: str,
) -> None:
    """Record mutual witnessing between two devices."""

def check_recovery_quorum(
    constellation: DeviceConstellation,
    available_devices: list[str],
) -> bool:
    """True if available devices meet recovery quorum."""

def can_recover(
    constellation: DeviceConstellation,
    available_devices: list[str],
) -> tuple[bool, str]:
    """
    Check recovery feasibility.

    Returns (feasible, reason).
    Requires: quorum met AND ≥1 hardware-bound device.
    """
```

## Integration Points

### With `lct.py`

The existing `Binding.hardware_anchor: Optional[str]` becomes the link.
For device LCTs, `hardware_anchor` stores a serialized `HardwareAnchor`
reference (e.g., `"tpm2:linux:manufacturer_x"`). No changes to `lct.py`
needed — the binding module interprets the existing field.

### With `trust.py`

`compute_constellation_trust()` produces a float that feeds into T3's
talent dimension for hardware-binding-strength. The spec adds two T3
sub-dimensions (`hardware_binding_strength`, `constellation_coherence`)
— these are RDF extensions via `web4:subDimensionOf`, not changes to
the core T3 dataclass.

### With `entity.py`

`EntityType.DEVICE` already exists with `InteractionType.BINDING` support.
`valid_interaction(DEVICE, DEVICE, WITNESSING)` should return True for
cross-device witnessing — verify this in tests.

### With `federation.py`

Device enrollment uses the society's `QuorumPolicy` for recovery quorum
mode. The `CitizenshipRecord` pattern applies to devices joining a
constellation (analogous to citizens joining a society).

### With `mrh.py`

`RelationType.PARENT_BINDING` and `CHILD_BINDING` model root→device
hierarchy. `RelationType.SIBLING_BINDING` models peer devices.
Cross-device witnessing uses `RelationType.WITNESSED_BY`.

## Test Plan

~35-45 tests organized by function group:

1. **AnchorType properties** (5): trust weights, is_hardware_bound
2. **Constellation management** (10): enroll genesis, enroll additional,
   remove device, quorum auto-update, duplicate enrollment error, remove
   non-existent error, quorum enforcement on removal
3. **Trust computation** (10): single device, multi-device, witness decay,
   coherence bonus, cross-witness density, trust ceiling enforcement,
   software-only ceiling, mixed constellation
4. **Cross-device witnessing** (5): record witness, mutual witness,
   density calculation, witness freshness decay
5. **Recovery** (5): quorum check, hardware requirement, insufficient
   quorum, all-software rejection
6. **Integration** (3-5): with entity.valid_interaction, with MRH
   relation types, with LCT Binding.hardware_anchor

## Test Vectors

5-7 cross-language vectors:

1. `witness_freshness_decay` — days → decay factor
2. `constellation_trust_single_device` — single phone SE → expected trust
3. `constellation_trust_multi_device` — phone + FIDO2 + TPM → expected trust
4. `trust_ceiling_by_config` — various configurations → ceiling values
5. `recovery_quorum_calculation` — device counts → quorum values
6. `coherence_bonus_by_diversity` — anchor type counts → bonus values

## File Plan

| File | Type | Description |
|------|------|-------------|
| `web4/binding.py` | New | Module (~350 lines) |
| `web4/tests/test_binding.py` | New | Tests (~40 tests) |
| `test-vectors/binding/binding-vectors.json` | New | Cross-language vectors |
| `web4/__init__.py` | Modified | Add binding exports |
| `web4_sdk.py` | Modified | Add binding re-exports |
| `docs/SPRINT.md` | Modified | U2 status update |

**New files: 3, Modified files: 3** (within 5-file new-file limit)

## Dependencies

- No new pip dependencies
- Imports only from existing SDK modules (`trust`, `lct`, `entity`)
- Standard library only (`dataclasses`, `enum`, `datetime`)

## Open Questions for Implementation

1. **Serialization**: Should `DeviceConstellation` have `to_dict()` / `from_dict()`
   for JSON round-tripping? (Probably yes, consistent with LCT pattern.)

2. **Timestamp handling**: Use ISO strings (consistent with rest of SDK) or
   `datetime` objects? Current SDK uses strings — stay consistent.

3. **Weight redistribution**: When a device is removed, should remaining device
   `trust_weight` values auto-redistribute to sum to 1.0? (Spec implies yes.)

4. **Event hooks**: Should enrollment/removal/witnessing emit events that
   other modules can observe? (Not for v1 — keep it simple.)

---

*"Identity is not a single point. It is the coherence pattern across all your witnesses."*
— Multi-Device LCT Binding Protocol spec
