"""
Tests for binding + attestation integration (Sprint 2, H5).

Validates:
- AnchorType ↔ attestation type bidirectional mapping
- DeviceRecord with AttestationEnvelope as proof carrier
- enroll_device() with attestation validation
- compute_device_trust() combining anchor weight × witness × attestation freshness
- compute_constellation_trust() attestation-aware behavior
- Backward compatibility (no attestation → same behavior as before)
"""

import time

import pytest

from web4.binding import (
    AnchorType,
    DeviceStatus,
    HardwareAnchor,
    DeviceRecord,
    DeviceConstellation,
    ANCHOR_TYPE_TO_ATTESTATION,
    ATTESTATION_TO_ANCHOR_TYPE,
    attestation_anchor_type,
    binding_anchor_type,
    enroll_device,
    compute_device_trust,
    compute_constellation_trust,
    witness_freshness,
)
from web4.attestation import (
    AttestationEnvelope,
    AnchorInfo,
    Proof,
)


# ── Fixtures ────────────────────────────────────────────────────


def _make_envelope(
    anchor_type: str = "tpm2",
    purpose: str = "enrollment",
    timestamp: float | None = None,
    entity_id: str = "lct:device-1",
) -> AttestationEnvelope:
    """Helper to build an AttestationEnvelope with sensible defaults."""
    return AttestationEnvelope(
        entity_id=entity_id,
        public_key="PEM_TEST_KEY",
        anchor=AnchorInfo(type=anchor_type),
        proof=Proof(
            format=f"{anchor_type}_quote",
            signature="dGVzdA==",
            challenge="challenge-nonce",
        ),
        timestamp=timestamp if timestamp is not None else time.time(),
        purpose=purpose,
    )


def _make_constellation() -> DeviceConstellation:
    return DeviceConstellation(root_lct_id="lct:root-identity")


# ── AnchorType Bridge Tests ─────────────────────────────────────


class TestAnchorTypeBridge:
    """Tests for bidirectional AnchorType ↔ attestation type mapping."""

    def test_all_anchor_types_mapped(self):
        """Every AnchorType has a corresponding attestation string."""
        for at in AnchorType:
            assert at in ANCHOR_TYPE_TO_ATTESTATION

    def test_phone_se_maps_to_secure_enclave(self):
        assert attestation_anchor_type(AnchorType.PHONE_SECURE_ELEMENT) == "secure_enclave"

    def test_fido2_maps_to_fido2(self):
        assert attestation_anchor_type(AnchorType.FIDO2) == "fido2"

    def test_tpm2_maps_to_tpm2(self):
        assert attestation_anchor_type(AnchorType.TPM2) == "tpm2"

    def test_software_maps_to_software(self):
        assert attestation_anchor_type(AnchorType.SOFTWARE) == "software"

    def test_reverse_mapping_complete(self):
        """Every attestation string maps back to a binding AnchorType."""
        for at_str in ANCHOR_TYPE_TO_ATTESTATION.values():
            assert at_str in ATTESTATION_TO_ANCHOR_TYPE

    def test_bidirectional_roundtrip(self):
        """AnchorType → attestation string → AnchorType is identity."""
        for at in AnchorType:
            at_str = attestation_anchor_type(at)
            roundtripped = binding_anchor_type(at_str)
            assert roundtripped == at

    def test_unknown_attestation_type_raises(self):
        with pytest.raises(KeyError):
            binding_anchor_type("unknown_type")


# ── DeviceRecord with Attestation ───────────────────────────────


class TestDeviceRecordAttestation:
    """Tests for DeviceRecord carrying an AttestationEnvelope."""

    def test_default_no_attestation(self):
        """DeviceRecord defaults to no attestation (backward compat)."""
        record = DeviceRecord(
            device_lct_id="lct:dev-1",
            anchor=HardwareAnchor(anchor_type=AnchorType.TPM2),
            enrolled_at="2026-01-01T00:00:00Z",
            last_witnessed="2026-01-01T00:00:00Z",
        )
        assert record.latest_attestation is None

    def test_with_attestation(self):
        """DeviceRecord can carry an AttestationEnvelope."""
        envelope = _make_envelope(anchor_type="tpm2")
        record = DeviceRecord(
            device_lct_id="lct:dev-1",
            anchor=HardwareAnchor(anchor_type=AnchorType.TPM2),
            enrolled_at="2026-01-01T00:00:00Z",
            last_witnessed="2026-01-01T00:00:00Z",
            latest_attestation=envelope,
        )
        assert record.latest_attestation is envelope
        assert record.latest_attestation.anchor.type == "tpm2"


# ── Enrollment with Attestation ─────────────────────────────────


class TestEnrollWithAttestation:
    """Tests for enroll_device() with optional attestation."""

    def test_enroll_without_attestation(self):
        """Enrollment without attestation still works (backward compat)."""
        c = _make_constellation()
        record = enroll_device(
            c, "lct:dev-1",
            HardwareAnchor(anchor_type=AnchorType.TPM2),
            [], "2026-01-01T00:00:00Z",
        )
        assert record.latest_attestation is None
        assert len(c.devices) == 1

    def test_enroll_with_valid_attestation(self):
        """Enrollment with a valid envelope stores it on the device."""
        c = _make_constellation()
        envelope = _make_envelope(anchor_type="tpm2", purpose="enrollment")
        record = enroll_device(
            c, "lct:dev-1",
            HardwareAnchor(anchor_type=AnchorType.TPM2),
            [], "2026-01-01T00:00:00Z",
            attestation=envelope,
        )
        assert record.latest_attestation is envelope

    def test_enroll_wrong_purpose_raises(self):
        """Enrollment attestation must have purpose='enrollment'."""
        c = _make_constellation()
        envelope = _make_envelope(anchor_type="tpm2", purpose="session_start")
        with pytest.raises(ValueError, match="purpose='enrollment'"):
            enroll_device(
                c, "lct:dev-1",
                HardwareAnchor(anchor_type=AnchorType.TPM2),
                [], "2026-01-01T00:00:00Z",
                attestation=envelope,
            )

    def test_enroll_anchor_type_mismatch_raises(self):
        """Attestation anchor type must match device anchor type."""
        c = _make_constellation()
        # Device is TPM2 but envelope says fido2
        envelope = _make_envelope(anchor_type="fido2", purpose="enrollment")
        with pytest.raises(ValueError, match="does not match"):
            enroll_device(
                c, "lct:dev-1",
                HardwareAnchor(anchor_type=AnchorType.TPM2),
                [], "2026-01-01T00:00:00Z",
                attestation=envelope,
            )

    def test_enroll_phone_se_with_secure_enclave_succeeds(self):
        """PHONE_SECURE_ELEMENT accepts 'secure_enclave' attestation."""
        c = _make_constellation()
        envelope = _make_envelope(anchor_type="secure_enclave", purpose="enrollment")
        record = enroll_device(
            c, "lct:dev-1",
            HardwareAnchor(anchor_type=AnchorType.PHONE_SECURE_ELEMENT),
            [], "2026-01-01T00:00:00Z",
            attestation=envelope,
        )
        assert record.latest_attestation is envelope


# ── compute_device_trust() ──────────────────────────────────────


class TestComputeDeviceTrust:
    """Tests for per-device trust computation."""

    def test_no_attestation_equals_anchor_times_witness(self):
        """Without attestation, trust = anchor_weight × witness_freshness."""
        record = DeviceRecord(
            device_lct_id="lct:dev-1",
            anchor=HardwareAnchor(anchor_type=AnchorType.TPM2),
            enrolled_at="2026-01-01T00:00:00Z",
            last_witnessed="2026-01-01T00:00:00Z",
        )
        # Fresh witness (0 days)
        trust = compute_device_trust(record, days_since_witness=0)
        assert trust == pytest.approx(0.93 * 1.0)

        # Stale witness (60 days → 0.7 decay)
        trust = compute_device_trust(record, days_since_witness=60)
        assert trust == pytest.approx(0.93 * 0.7)

    def test_fresh_attestation_no_decay(self):
        """A just-created attestation has freshness_factor ≈ 1.0."""
        envelope = _make_envelope(anchor_type="tpm2", timestamp=time.time())
        record = DeviceRecord(
            device_lct_id="lct:dev-1",
            anchor=HardwareAnchor(anchor_type=AnchorType.TPM2),
            enrolled_at="2026-01-01T00:00:00Z",
            last_witnessed="2026-01-01T00:00:00Z",
            latest_attestation=envelope,
        )
        trust = compute_device_trust(record, days_since_witness=0)
        # freshness_factor ≈ 1.0 for just-created envelope
        assert trust == pytest.approx(0.93, abs=0.01)

    def test_stale_attestation_reduces_trust(self):
        """An old attestation reduces effective trust via freshness_factor."""
        # Create an envelope that's 4 hours old (session_start max = 8h)
        envelope = _make_envelope(
            anchor_type="tpm2",
            purpose="session_start",
            timestamp=time.time() - 4 * 3600,
        )
        record = DeviceRecord(
            device_lct_id="lct:dev-1",
            anchor=HardwareAnchor(anchor_type=AnchorType.TPM2),
            enrolled_at="2026-01-01T00:00:00Z",
            last_witnessed="2026-01-01T00:00:00Z",
            latest_attestation=envelope,
        )
        trust = compute_device_trust(record, days_since_witness=0)
        # freshness_factor = 1.0 - 4h/8h = 0.5
        expected = 0.93 * 1.0 * 0.5
        assert trust == pytest.approx(expected, abs=0.02)

    def test_expired_attestation_zeroes_trust(self):
        """An expired attestation drives freshness_factor to 0."""
        envelope = _make_envelope(
            anchor_type="tpm2",
            purpose="session_start",
            timestamp=time.time() - 10 * 3600,  # 10h > 8h max
        )
        record = DeviceRecord(
            device_lct_id="lct:dev-1",
            anchor=HardwareAnchor(anchor_type=AnchorType.TPM2),
            enrolled_at="2026-01-01T00:00:00Z",
            last_witnessed="2026-01-01T00:00:00Z",
            latest_attestation=envelope,
        )
        trust = compute_device_trust(record, days_since_witness=0)
        assert trust == 0.0

    def test_enrollment_purpose_never_expires(self):
        """Enrollment attestations have no expiry (freshness_factor = 1.0 always)."""
        envelope = _make_envelope(
            anchor_type="tpm2",
            purpose="enrollment",
            timestamp=time.time() - 365 * 24 * 3600,  # 1 year old
        )
        record = DeviceRecord(
            device_lct_id="lct:dev-1",
            anchor=HardwareAnchor(anchor_type=AnchorType.TPM2),
            enrolled_at="2025-01-01T00:00:00Z",
            last_witnessed="2025-01-01T00:00:00Z",
            latest_attestation=envelope,
        )
        trust = compute_device_trust(record, days_since_witness=0)
        # Enrollment never expires, freshness_factor = 1.0
        assert trust == pytest.approx(0.93)

    def test_software_anchor_low_trust(self):
        """Software anchor with no attestation has low trust ceiling."""
        record = DeviceRecord(
            device_lct_id="lct:dev-sw",
            anchor=HardwareAnchor(anchor_type=AnchorType.SOFTWARE),
            enrolled_at="2026-01-01T00:00:00Z",
            last_witnessed="2026-01-01T00:00:00Z",
        )
        trust = compute_device_trust(record, days_since_witness=0)
        assert trust == pytest.approx(0.40)


# ── Constellation Trust with Attestation ────────────────────────


class TestConstellationTrustWithAttestation:
    """Tests for compute_constellation_trust() attestation awareness."""

    def test_backward_compat_no_attestation(self):
        """Without attestation, result is identical to pre-H5 behavior."""
        c = _make_constellation()
        enroll_device(
            c, "lct:dev-1",
            HardwareAnchor(anchor_type=AnchorType.TPM2),
            [], "2026-01-01T00:00:00Z",
        )
        trust = compute_constellation_trust(c)
        # Single TPM2 device, fresh witness, no attestation → 0.93 × 1.0 × 1.0
        # Clamped to ceiling 0.75 (single_tpm2)
        assert trust == pytest.approx(0.75)

    def test_attestation_reduces_constellation_trust(self):
        """A stale attestation reduces per-device trust, lowering constellation trust."""
        c = _make_constellation()
        # Enroll with enrollment attestation, then update to stale session_start
        enroll_env = _make_envelope(anchor_type="fido2", purpose="enrollment")
        record = enroll_device(
            c, "lct:dev-1",
            HardwareAnchor(anchor_type=AnchorType.FIDO2),
            [], "2026-01-01T00:00:00Z",
            attestation=enroll_env,
        )
        # Simulate: device later gets a session_start attestation that's 4h old
        session_env = _make_envelope(
            anchor_type="fido2",
            purpose="session_start",
            timestamp=time.time() - 4 * 3600,  # 4h of 8h max
        )
        record.latest_attestation = session_env

        trust = compute_constellation_trust(c)
        # Single FIDO2, fresh witness, attestation freshness ≈ 0.5
        # Device trust = 0.98 × 1.0 × 0.5 = 0.49
        # Ceiling = 0.80 (single_fido2)
        # 0.49 < 0.80, so trust = 0.49
        assert trust == pytest.approx(0.49, abs=0.02)

    def test_mixed_attestation_and_no_attestation(self):
        """Constellation with some devices having attestation, others not."""
        c = _make_constellation()

        # Device 1: TPM2 with fresh attestation
        env1 = _make_envelope(anchor_type="tpm2", purpose="enrollment")
        enroll_device(
            c, "lct:dev-1",
            HardwareAnchor(anchor_type=AnchorType.TPM2),
            [], "2026-01-01T00:00:00Z",
            attestation=env1,
        )

        # Device 2: FIDO2 without attestation
        enroll_device(
            c, "lct:dev-2",
            HardwareAnchor(anchor_type=AnchorType.FIDO2),
            ["lct:dev-1"], "2026-01-01T00:00:00Z",
        )

        trust = compute_constellation_trust(c)
        # Device 1: 0.93 × 1.0 × 1.0 = 0.93 (enrollment never expires)
        # Device 2: 0.98 × 1.0 × 1.0 = 0.98 (no attestation → 1.0)
        # Base = (0.93 + 0.98) / 2 = 0.955
        # Coherence bonus: 2 anchor types → 0.08
        # No cross-witnesses yet
        # Trust = 0.955 × 1.08 = 1.0314 → clamped to ceiling
        # With TPM2 + FIDO2: fallback to 0.90 (2 hardware types, no phone)
        assert trust <= 0.90
        assert trust > 0.0


# ── Edge Cases ──────────────────────────────────────────────────


class TestEdgeCases:
    """Edge case tests for integration."""

    def test_empty_constellation_trust(self):
        """Empty constellation returns 0 trust."""
        c = _make_constellation()
        assert compute_constellation_trust(c) == 0.0

    def test_compute_device_trust_with_witness_decay_and_attestation(self):
        """Both witness decay and attestation decay apply multiplicatively."""
        envelope = _make_envelope(
            anchor_type="fido2",
            purpose="session_start",
            timestamp=time.time() - 4 * 3600,  # 50% attestation freshness
        )
        record = DeviceRecord(
            device_lct_id="lct:dev-1",
            anchor=HardwareAnchor(anchor_type=AnchorType.FIDO2),
            enrolled_at="2026-01-01T00:00:00Z",
            last_witnessed="2026-01-01T00:00:00Z",
            latest_attestation=envelope,
        )
        # 60 days → witness_freshness = 0.7
        trust = compute_device_trust(record, days_since_witness=60)
        # 0.98 × 0.7 × ~0.5 ≈ 0.343
        expected = 0.98 * 0.7 * 0.5
        assert trust == pytest.approx(expected, abs=0.02)

    def test_attestation_on_revoked_device_ignored_in_constellation(self):
        """Revoked devices don't contribute to constellation trust."""
        c = _make_constellation()
        env = _make_envelope(anchor_type="tpm2", purpose="enrollment")
        enroll_device(
            c, "lct:dev-1",
            HardwareAnchor(anchor_type=AnchorType.TPM2),
            [], "2026-01-01T00:00:00Z",
            attestation=env,
        )
        # Add second device so we can revoke without quorum issues
        enroll_device(
            c, "lct:dev-2",
            HardwareAnchor(anchor_type=AnchorType.FIDO2),
            ["lct:dev-1"], "2026-01-01T00:00:00Z",
        )
        # Manually revoke device 1
        c.devices[0].status = DeviceStatus.REVOKED
        # Only device 2 is active
        trust = compute_constellation_trust(c)
        assert trust > 0.0
        assert len(c.active_devices) == 1
