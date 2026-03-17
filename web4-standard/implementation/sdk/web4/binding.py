"""
Web4 Multi-Device Binding

Canonical implementation per web4-standard/core-spec/multi-device-lct-binding.md.

Identity in Web4 is coherence across witnesses — more devices witnessing
the same identity creates stronger unforgeability. This module provides
the data structures and trust logic for managing device constellations.

Key concepts:
- AnchorType: hardware anchor taxonomy (phone SE, FIDO2, TPM2, software)
- DeviceConstellation: collection of devices bound to a root identity
- Trust computation: weighted device trust + coherence bonus + witness density
- Recovery quorum: minimum devices for identity recovery (§5.2)
- Cross-device witnessing: mutual attestation that strengthens constellation

This module provides DATA STRUCTURES and pure-function computations.
Actual cryptographic operations, platform-specific code, and network
protocols are out of scope (they belong in language-specific SDKs).

Patent coverage: 305 family (US 11,477,027 + US 12,278,913).

Validated against: web4-standard/test-vectors/binding/binding-vectors.json
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ── Anchor Types (spec §2.2) ────────────────────────────────────

class AnchorType(str, Enum):
    """Hardware anchor types per spec §2.2."""
    PHONE_SECURE_ELEMENT = "phone_secure_element"  # iOS SE / Android StrongBox
    FIDO2 = "fido2"                                # FIDO2 security keys
    TPM2 = "tpm2"                                  # TPM 2.0 chips
    SOFTWARE = "software"                          # Software-only fallback


# ── Device Status ────────────────────────────────────────────────

class DeviceStatus(str, Enum):
    """Device lifecycle within a constellation."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


# ── Constants (spec §4.2, §4.3, §3.4) ───────────────────────────

ANCHOR_TRUST_WEIGHT: Dict[AnchorType, float] = {
    AnchorType.PHONE_SECURE_ELEMENT: 0.95,
    AnchorType.FIDO2: 0.98,
    AnchorType.TPM2: 0.93,
    AnchorType.SOFTWARE: 0.40,
}

# Coherence bonus by anchor type diversity count (spec §3.4)
_COHERENCE_BONUS_TABLE: Dict[int, float] = {
    1: 0.0,
    2: 0.08,
    3: 0.15,
}
_COHERENCE_BONUS_MAX = 0.20  # 4+ types

# Trust ceilings by constellation composition (spec §4.2)
CONSTELLATION_TRUST_CEILING: Dict[str, float] = {
    "single_software": 0.40,
    "single_phone_se": 0.75,
    "single_fido2": 0.80,
    "single_tpm2": 0.75,
    "phone_fido2": 0.90,
    "phone_fido2_tpm": 0.95,
    "3_plus_diverse": 0.98,
}

# Witness freshness decay (spec §4.3)
WITNESS_DECAY_TABLE: List[Tuple[int, float]] = [
    (7, 1.0),       # ≤7 days: no decay
    (30, 0.9),      # ≤30 days
    (90, 0.7),      # ≤90 days
    (180, 0.5),     # ≤180 days
    (999999, 0.3),  # >180 days
]


# ── Data Structures ──────────────────────────────────────────────

@dataclass(frozen=True)
class HardwareAnchor:
    """Hardware root of trust for a device."""
    anchor_type: AnchorType
    platform: str = ""              # "ios", "android", "linux", "windows"
    attestation_format: str = ""    # "apple_app_attest", "android_key_attestation", "tpm2_quote"
    manufacturer: str = ""

    @property
    def trust_weight(self) -> float:
        """Trust weight for this anchor type per spec §4.2."""
        return ANCHOR_TRUST_WEIGHT[self.anchor_type]

    @property
    def is_hardware_bound(self) -> bool:
        """True if this anchor uses hardware security (not software-only)."""
        return self.anchor_type != AnchorType.SOFTWARE


@dataclass
class DeviceRecord:
    """A device within a constellation."""
    device_lct_id: str
    anchor: HardwareAnchor
    enrolled_at: str                 # ISO 8601 timestamp
    last_witnessed: str              # ISO 8601 timestamp
    status: DeviceStatus = DeviceStatus.ACTIVE
    cross_witnesses: List[str] = field(default_factory=list)  # LCT IDs that witnessed this device
    revoked_at: str = ""
    revocation_reason: str = ""


@dataclass
class DeviceConstellation:
    """Collection of devices bound to a root identity."""
    root_lct_id: str
    devices: List[DeviceRecord] = field(default_factory=list)
    recovery_quorum: int = 1

    @property
    def active_devices(self) -> List[DeviceRecord]:
        """All devices with ACTIVE status."""
        return [d for d in self.devices if d.status == DeviceStatus.ACTIVE]

    @property
    def device_count(self) -> int:
        """Number of active devices."""
        return len(self.active_devices)


# ── Witness Freshness (spec §4.3) ───────────────────────────────

def witness_freshness(days_since_witness: int) -> float:
    """
    Decay factor based on days since last witness event.

    Per spec §4.3 witness decay table:
    ≤7 days → 1.0, ≤30 → 0.9, ≤90 → 0.7, ≤180 → 0.5, >180 → 0.3.
    """
    if days_since_witness < 0:
        raise ValueError("days_since_witness must be non-negative")
    for threshold, factor in WITNESS_DECAY_TABLE:
        if days_since_witness <= threshold:
            return factor
    return WITNESS_DECAY_TABLE[-1][1]  # fallback (shouldn't reach)


# ── Constellation Management ────────────────────────────────────

def default_recovery_quorum(device_count: int) -> int:
    """
    Default recovery quorum per spec §5.2.

    ≤2 devices: all required. ≤4: 2. >4: majority.
    """
    if device_count <= 0:
        return 0
    if device_count <= 2:
        return device_count
    if device_count <= 4:
        return 2
    return max(2, (device_count + 1) // 2)  # ceil(n/2) = majority


def enroll_device(
    constellation: DeviceConstellation,
    device_lct_id: str,
    anchor: HardwareAnchor,
    witnesses: List[str],
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
    # Check for duplicate
    existing_ids = {d.device_lct_id for d in constellation.devices}
    if device_lct_id in existing_ids:
        raise ValueError(f"Device {device_lct_id} already enrolled")

    # Non-genesis: require existing device as witness
    active_ids = {d.device_lct_id for d in constellation.active_devices}
    if active_ids:
        witness_from_constellation = active_ids & set(witnesses)
        if not witness_from_constellation:
            raise ValueError(
                "Non-genesis enrollment requires at least one existing "
                "active device as witness"
            )

    record = DeviceRecord(
        device_lct_id=device_lct_id,
        anchor=anchor,
        enrolled_at=timestamp,
        last_witnessed=timestamp,
        cross_witnesses=list(witnesses),
    )
    constellation.devices.append(record)

    # Auto-update quorum
    constellation.recovery_quorum = default_recovery_quorum(
        constellation.device_count
    )

    return record


def remove_device(
    constellation: DeviceConstellation,
    device_lct_id: str,
    reason: str,
    authorizing_devices: List[str],
    timestamp: str,
) -> None:
    """
    Remove (revoke) a device from the constellation.

    Raises ValueError if quorum not met, device not found, or device
    already revoked.
    """
    valid_reasons = {"lost", "sold", "compromised", "upgrade"}
    if reason not in valid_reasons:
        raise ValueError(f"Invalid reason '{reason}'; must be one of {valid_reasons}")

    # Find the device
    target = None
    for d in constellation.devices:
        if d.device_lct_id == device_lct_id:
            target = d
            break
    if target is None:
        raise ValueError(f"Device {device_lct_id} not found in constellation")
    if target.status == DeviceStatus.REVOKED:
        raise ValueError(f"Device {device_lct_id} already revoked")

    # Check quorum (among remaining active devices, excluding target)
    active_ids = {
        d.device_lct_id
        for d in constellation.active_devices
        if d.device_lct_id != device_lct_id
    }
    authorizing_active = active_ids & set(authorizing_devices)
    if len(authorizing_active) < constellation.recovery_quorum:
        raise ValueError(
            f"Quorum not met: need {constellation.recovery_quorum} "
            f"authorizing active devices, got {len(authorizing_active)}"
        )

    # Revoke
    target.status = DeviceStatus.REVOKED
    target.revoked_at = timestamp
    target.revocation_reason = reason

    # Re-compute quorum for remaining active devices
    constellation.recovery_quorum = default_recovery_quorum(
        constellation.device_count
    )


# ── Trust Computation (spec §3.4) ───────────────────────────────

def coherence_bonus(devices: List[DeviceRecord]) -> float:
    """
    Bonus for anchor type diversity per spec §3.4.

    1 type → 0%, 2 → 8%, 3 → 15%, 4+ → 20%.
    """
    if not devices:
        return 0.0
    anchor_types = {d.anchor.anchor_type for d in devices}
    count = len(anchor_types)
    return _COHERENCE_BONUS_TABLE.get(count, _COHERENCE_BONUS_MAX)


def cross_witness_density(devices: List[DeviceRecord]) -> float:
    """
    Ratio of actual witness pairs to possible pairs.

    Full mesh = 1.0, no witnessing = 0.0.
    Only counts mutual witnesses (A witnessed B AND B witnessed A).
    """
    if len(devices) < 2:
        return 0.0

    possible_pairs = len(devices) * (len(devices) - 1) / 2
    device_ids = {d.device_lct_id for d in devices}

    # Count unique mutual witness pairs
    witness_pairs = set()
    for d in devices:
        for w_id in d.cross_witnesses:
            if w_id in device_ids:
                pair = tuple(sorted([d.device_lct_id, w_id]))
                witness_pairs.add(pair)

    return min(1.0, len(witness_pairs) / possible_pairs)


def constellation_trust_ceiling(constellation: DeviceConstellation) -> float:
    """Max trust achievable given current anchor type mix."""
    active = constellation.active_devices
    if not active:
        return 0.0

    anchor_types = {d.anchor.anchor_type for d in active}
    n_active = len(active)
    hardware_types = anchor_types - {AnchorType.SOFTWARE}

    # Single-device configurations
    if n_active == 1:
        anchor = active[0].anchor.anchor_type
        if anchor == AnchorType.SOFTWARE:
            return CONSTELLATION_TRUST_CEILING["single_software"]
        if anchor == AnchorType.PHONE_SECURE_ELEMENT:
            return CONSTELLATION_TRUST_CEILING["single_phone_se"]
        if anchor == AnchorType.FIDO2:
            return CONSTELLATION_TRUST_CEILING["single_fido2"]
        if anchor == AnchorType.TPM2:
            return CONSTELLATION_TRUST_CEILING["single_tpm2"]

    # Named multi-device configurations (check specific before generic)

    # Phone + FIDO2 + TPM (these 3 types only, no additional types)
    if (
        AnchorType.PHONE_SECURE_ELEMENT in anchor_types
        and AnchorType.FIDO2 in anchor_types
        and AnchorType.TPM2 in anchor_types
        and len(anchor_types) == 3
    ):
        return CONSTELLATION_TRUST_CEILING["phone_fido2_tpm"]

    # 3+ diverse hardware anchors (generic — covers configs not named above)
    if len(hardware_types) >= 3:
        return CONSTELLATION_TRUST_CEILING["3_plus_diverse"]

    # Phone + FIDO2
    if (
        AnchorType.PHONE_SECURE_ELEMENT in anchor_types
        and AnchorType.FIDO2 in anchor_types
    ):
        return CONSTELLATION_TRUST_CEILING["phone_fido2"]

    # Fallback: derive from anchor diversity
    if len(hardware_types) >= 2:
        return 0.90
    if len(hardware_types) == 1:
        return 0.80
    # Software-only with multiple devices
    return CONSTELLATION_TRUST_CEILING["single_software"]


def compute_constellation_trust(
    constellation: DeviceConstellation,
    days_since_witness: Optional[Dict[str, int]] = None,
) -> float:
    """
    Aggregate trust from device constellation per spec §3.4.

    Components:
    1. Weighted device trust (anchor weight × freshness)
    2. Coherence bonus (diverse anchor types: 0–20%)
    3. Cross-witness density (mesh completeness: 0–10%)

    Args:
        constellation: The device constellation.
        days_since_witness: Optional mapping of device_lct_id → days since
            last witness. Defaults to 0 (fully fresh) if not provided.

    Returns:
        Constellation trust score, clamped to [0.0, ceiling].
    """
    active = constellation.active_devices
    if not active:
        return 0.0

    if days_since_witness is None:
        days_since_witness = {}

    # 1. Weighted device trust
    total_weight = 0.0
    weighted_sum = 0.0
    for device in active:
        anchor_w = device.anchor.trust_weight
        days = days_since_witness.get(device.device_lct_id, 0)
        freshness = witness_freshness(days)
        device_trust = anchor_w * freshness
        # Equal weight per device (trust_weight is about the anchor,
        # not a custom per-device weighting in this simplified model)
        total_weight += 1.0
        weighted_sum += device_trust

    base_trust = weighted_sum / total_weight if total_weight > 0 else 0.0

    # 2. Coherence bonus
    cb = coherence_bonus(active)

    # 3. Cross-witness density
    cwd = cross_witness_density(active)

    # Combine per spec §3.4
    trust = base_trust * (1 + cb) * (1 + cwd * 0.1)

    # Clamp to ceiling
    ceiling = constellation_trust_ceiling(constellation)
    return round(min(trust, ceiling), 4)


# ── Cross-Device Witnessing ─────────────────────────────────────

def record_cross_witness(
    constellation: DeviceConstellation,
    device_a_id: str,
    device_b_id: str,
    timestamp: str,
) -> None:
    """
    Record mutual witnessing between two devices.

    Both devices add each other to their cross_witnesses list.
    Both get their last_witnessed updated.

    Raises ValueError if either device not found or not active.
    """
    device_a = None
    device_b = None
    for d in constellation.devices:
        if d.device_lct_id == device_a_id:
            device_a = d
        elif d.device_lct_id == device_b_id:
            device_b = d

    if device_a is None:
        raise ValueError(f"Device {device_a_id} not found")
    if device_b is None:
        raise ValueError(f"Device {device_b_id} not found")
    if device_a.status != DeviceStatus.ACTIVE:
        raise ValueError(f"Device {device_a_id} is not active")
    if device_b.status != DeviceStatus.ACTIVE:
        raise ValueError(f"Device {device_b_id} is not active")

    # Add mutual witness (idempotent — no duplicates)
    if device_b_id not in device_a.cross_witnesses:
        device_a.cross_witnesses.append(device_b_id)
    if device_a_id not in device_b.cross_witnesses:
        device_b.cross_witnesses.append(device_a_id)

    # Update last_witnessed
    device_a.last_witnessed = timestamp
    device_b.last_witnessed = timestamp


# ── Recovery (spec §5.2) ────────────────────────────────────────

def check_recovery_quorum(
    constellation: DeviceConstellation,
    available_devices: List[str],
) -> bool:
    """True if available devices meet recovery quorum."""
    active_ids = {d.device_lct_id for d in constellation.active_devices}
    available_active = active_ids & set(available_devices)
    return len(available_active) >= constellation.recovery_quorum


def can_recover(
    constellation: DeviceConstellation,
    available_devices: List[str],
) -> Tuple[bool, str]:
    """
    Check recovery feasibility.

    Requires: quorum met AND ≥1 hardware-bound device among available.
    Returns (feasible, reason).
    """
    active_ids = {d.device_lct_id for d in constellation.active_devices}
    available_active = active_ids & set(available_devices)

    if len(available_active) < constellation.recovery_quorum:
        return (
            False,
            f"Quorum not met: need {constellation.recovery_quorum}, "
            f"have {len(available_active)} active",
        )

    # Check for at least one hardware-bound device
    has_hardware = False
    for d in constellation.active_devices:
        if d.device_lct_id in available_active and d.anchor.is_hardware_bound:
            has_hardware = True
            break

    if not has_hardware:
        return (False, "Recovery requires at least one hardware-bound device")

    return (True, "Recovery feasible")
