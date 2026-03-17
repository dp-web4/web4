"""
Tests for web4.binding — Multi-Device LCT Binding.

Validates hardware anchor taxonomy, device constellation management,
trust computation, cross-device witnessing, and recovery quorum logic
per multi-device-lct-binding.md.
"""

import json
import pathlib
import pytest

from web4.binding import (
    AnchorType,
    DeviceStatus,
    HardwareAnchor,
    DeviceRecord,
    DeviceConstellation,
    ANCHOR_TRUST_WEIGHT,
    CONSTELLATION_TRUST_CEILING,
    WITNESS_DECAY_TABLE,
    witness_freshness,
    default_recovery_quorum,
    enroll_device,
    remove_device,
    coherence_bonus,
    cross_witness_density,
    constellation_trust_ceiling,
    compute_constellation_trust,
    record_cross_witness,
    check_recovery_quorum,
    can_recover,
)


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def phone_anchor():
    return HardwareAnchor(
        anchor_type=AnchorType.PHONE_SECURE_ELEMENT,
        platform="ios",
        attestation_format="apple_app_attest",
    )


@pytest.fixture
def fido2_anchor():
    return HardwareAnchor(
        anchor_type=AnchorType.FIDO2,
        attestation_format="packed",
    )


@pytest.fixture
def tpm2_anchor():
    return HardwareAnchor(
        anchor_type=AnchorType.TPM2,
        platform="linux",
        manufacturer="Intel",
    )


@pytest.fixture
def software_anchor():
    return HardwareAnchor(
        anchor_type=AnchorType.SOFTWARE,
        platform="browser",
    )


@pytest.fixture
def empty_constellation():
    return DeviceConstellation(root_lct_id="lct:web4:root:test123")


@pytest.fixture
def single_phone_constellation(phone_anchor):
    rec = DeviceRecord(
        device_lct_id="lct:web4:device:phone1",
        anchor=phone_anchor,
        enrolled_at="2026-01-01T00:00:00Z",
        last_witnessed="2026-01-01T00:00:00Z",
    )
    c = DeviceConstellation(root_lct_id="lct:web4:root:test123", devices=[rec])
    c.recovery_quorum = default_recovery_quorum(c.device_count)
    return c


@pytest.fixture
def multi_device_constellation(phone_anchor, fido2_anchor, tpm2_anchor):
    """Phone + FIDO2 + TPM constellation with cross-witnesses."""
    phone = DeviceRecord(
        device_lct_id="lct:web4:device:phone1",
        anchor=phone_anchor,
        enrolled_at="2026-01-01T00:00:00Z",
        last_witnessed="2026-01-15T00:00:00Z",
        cross_witnesses=["lct:web4:device:fido1", "lct:web4:device:laptop1"],
    )
    fido = DeviceRecord(
        device_lct_id="lct:web4:device:fido1",
        anchor=fido2_anchor,
        enrolled_at="2026-01-02T00:00:00Z",
        last_witnessed="2026-01-15T00:00:00Z",
        cross_witnesses=["lct:web4:device:phone1", "lct:web4:device:laptop1"],
    )
    laptop = DeviceRecord(
        device_lct_id="lct:web4:device:laptop1",
        anchor=tpm2_anchor,
        enrolled_at="2026-01-03T00:00:00Z",
        last_witnessed="2026-01-15T00:00:00Z",
        cross_witnesses=["lct:web4:device:phone1", "lct:web4:device:fido1"],
    )
    c = DeviceConstellation(
        root_lct_id="lct:web4:root:test123",
        devices=[phone, fido, laptop],
    )
    c.recovery_quorum = default_recovery_quorum(c.device_count)
    return c


# ── AnchorType Properties ───────────────────────────────────────

class TestHardwareAnchor:
    def test_phone_se_trust_weight(self, phone_anchor):
        assert phone_anchor.trust_weight == 0.95

    def test_fido2_trust_weight(self, fido2_anchor):
        assert fido2_anchor.trust_weight == 0.98

    def test_tpm2_trust_weight(self, tpm2_anchor):
        assert tpm2_anchor.trust_weight == 0.93

    def test_software_trust_weight(self, software_anchor):
        assert software_anchor.trust_weight == 0.40

    def test_hardware_bound_true(self, phone_anchor, fido2_anchor, tpm2_anchor):
        assert phone_anchor.is_hardware_bound is True
        assert fido2_anchor.is_hardware_bound is True
        assert tpm2_anchor.is_hardware_bound is True

    def test_software_not_hardware_bound(self, software_anchor):
        assert software_anchor.is_hardware_bound is False

    def test_anchor_frozen(self, phone_anchor):
        with pytest.raises(AttributeError):
            phone_anchor.platform = "android"


# ── Constellation Management ────────────────────────────────────

class TestConstellationManagement:
    def test_empty_constellation(self, empty_constellation):
        assert empty_constellation.device_count == 0
        assert empty_constellation.active_devices == []

    def test_genesis_enrollment(self, empty_constellation, phone_anchor):
        rec = enroll_device(
            empty_constellation,
            "lct:web4:device:phone1",
            phone_anchor,
            witnesses=[],
            timestamp="2026-01-01T00:00:00Z",
        )
        assert rec.device_lct_id == "lct:web4:device:phone1"
        assert rec.status == DeviceStatus.ACTIVE
        assert empty_constellation.device_count == 1
        assert empty_constellation.recovery_quorum == 1

    def test_additional_enrollment_with_witness(
        self, single_phone_constellation, fido2_anchor
    ):
        rec = enroll_device(
            single_phone_constellation,
            "lct:web4:device:fido1",
            fido2_anchor,
            witnesses=["lct:web4:device:phone1"],
            timestamp="2026-01-02T00:00:00Z",
        )
        assert single_phone_constellation.device_count == 2
        assert single_phone_constellation.recovery_quorum == 2

    def test_additional_enrollment_no_witness_raises(
        self, single_phone_constellation, fido2_anchor
    ):
        with pytest.raises(ValueError, match="existing active device as witness"):
            enroll_device(
                single_phone_constellation,
                "lct:web4:device:fido1",
                fido2_anchor,
                witnesses=[],
                timestamp="2026-01-02T00:00:00Z",
            )

    def test_additional_enrollment_wrong_witness_raises(
        self, single_phone_constellation, fido2_anchor
    ):
        with pytest.raises(ValueError, match="existing active device as witness"):
            enroll_device(
                single_phone_constellation,
                "lct:web4:device:fido1",
                fido2_anchor,
                witnesses=["lct:web4:device:unknown"],
                timestamp="2026-01-02T00:00:00Z",
            )

    def test_duplicate_enrollment_raises(
        self, single_phone_constellation, phone_anchor
    ):
        with pytest.raises(ValueError, match="already enrolled"):
            enroll_device(
                single_phone_constellation,
                "lct:web4:device:phone1",
                phone_anchor,
                witnesses=[],
                timestamp="2026-01-02T00:00:00Z",
            )

    def test_remove_device(self, multi_device_constellation):
        remove_device(
            multi_device_constellation,
            "lct:web4:device:laptop1",
            reason="sold",
            authorizing_devices=[
                "lct:web4:device:phone1",
                "lct:web4:device:fido1",
            ],
            timestamp="2026-02-01T00:00:00Z",
        )
        assert multi_device_constellation.device_count == 2
        laptop = [
            d
            for d in multi_device_constellation.devices
            if d.device_lct_id == "lct:web4:device:laptop1"
        ][0]
        assert laptop.status == DeviceStatus.REVOKED
        assert laptop.revocation_reason == "sold"

    def test_remove_device_quorum_enforcement(self, multi_device_constellation):
        with pytest.raises(ValueError, match="Quorum not met"):
            remove_device(
                multi_device_constellation,
                "lct:web4:device:laptop1",
                reason="lost",
                authorizing_devices=["lct:web4:device:phone1"],
                timestamp="2026-02-01T00:00:00Z",
            )

    def test_remove_device_not_found(self, multi_device_constellation):
        with pytest.raises(ValueError, match="not found"):
            remove_device(
                multi_device_constellation,
                "lct:web4:device:nonexistent",
                reason="lost",
                authorizing_devices=[
                    "lct:web4:device:phone1",
                    "lct:web4:device:fido1",
                ],
                timestamp="2026-02-01T00:00:00Z",
            )

    def test_remove_device_invalid_reason(self, multi_device_constellation):
        with pytest.raises(ValueError, match="Invalid reason"):
            remove_device(
                multi_device_constellation,
                "lct:web4:device:laptop1",
                reason="bored",
                authorizing_devices=[
                    "lct:web4:device:phone1",
                    "lct:web4:device:fido1",
                ],
                timestamp="2026-02-01T00:00:00Z",
            )


# ── Recovery Quorum ──────────────────────────────────────────────

class TestRecoveryQuorum:
    def test_quorum_zero(self):
        assert default_recovery_quorum(0) == 0

    def test_quorum_one(self):
        assert default_recovery_quorum(1) == 1

    def test_quorum_two(self):
        assert default_recovery_quorum(2) == 2

    def test_quorum_three(self):
        assert default_recovery_quorum(3) == 2

    def test_quorum_four(self):
        assert default_recovery_quorum(4) == 2

    def test_quorum_five(self):
        assert default_recovery_quorum(5) == 3

    def test_quorum_six(self):
        assert default_recovery_quorum(6) == 3  # (6+1)//2 = 3 (majority)

    def test_quorum_is_majority_large(self):
        # 10 devices: quorum = (10+1)//2 = 5 (majority)
        assert default_recovery_quorum(10) == 5


# ── Witness Freshness ────────────────────────────────────────────

class TestWitnessFreshness:
    def test_fresh_zero_days(self):
        assert witness_freshness(0) == 1.0

    def test_fresh_seven_days(self):
        assert witness_freshness(7) == 1.0

    def test_eight_days(self):
        assert witness_freshness(8) == 0.9

    def test_thirty_days(self):
        assert witness_freshness(30) == 0.9

    def test_sixty_days(self):
        assert witness_freshness(60) == 0.7

    def test_hundred_days(self):
        assert witness_freshness(100) == 0.5

    def test_two_hundred_days(self):
        assert witness_freshness(200) == 0.3

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            witness_freshness(-1)


# ── Trust Computation ────────────────────────────────────────────

class TestTrustComputation:
    def test_empty_constellation_trust(self, empty_constellation):
        assert compute_constellation_trust(empty_constellation) == 0.0

    def test_single_phone_trust(self, single_phone_constellation):
        trust = compute_constellation_trust(single_phone_constellation)
        # Single phone: 0.95 base, no coherence bonus, no witness density
        # Ceiling: 0.75
        assert trust == 0.75  # capped at ceiling

    def test_single_software_ceiling(self, software_anchor):
        rec = DeviceRecord(
            device_lct_id="lct:web4:device:sw1",
            anchor=software_anchor,
            enrolled_at="2026-01-01T00:00:00Z",
            last_witnessed="2026-01-01T00:00:00Z",
        )
        c = DeviceConstellation(
            root_lct_id="lct:web4:root:sw",
            devices=[rec],
            recovery_quorum=1,
        )
        trust = compute_constellation_trust(c)
        assert trust == 0.40  # software ceiling

    def test_multi_device_full_mesh(self, multi_device_constellation):
        trust = compute_constellation_trust(multi_device_constellation)
        # 3 devices (phone 0.95 + fido 0.98 + tpm 0.93) / 3 = 0.9533
        # Coherence bonus: 3 types → 0.15
        # Witness density: full mesh (3 pairs) → 1.0
        # trust = 0.9533 * 1.15 * 1.1 = ~1.205 → capped at 0.95
        assert trust == 0.95

    def test_witness_decay_reduces_trust(self, single_phone_constellation):
        # 60 days since witness → freshness 0.7
        trust = compute_constellation_trust(
            single_phone_constellation,
            days_since_witness={"lct:web4:device:phone1": 60},
        )
        # 0.95 * 0.7 = 0.665, no bonus, no density → 0.665
        # ceiling 0.75, so not capped
        assert trust == 0.665

    def test_coherence_bonus_values(self, phone_anchor, fido2_anchor, tpm2_anchor):
        # 1 type
        devs_1 = [
            DeviceRecord(
                device_lct_id="a",
                anchor=phone_anchor,
                enrolled_at="",
                last_witnessed="",
            )
        ]
        assert coherence_bonus(devs_1) == 0.0

        # 2 types
        devs_2 = devs_1 + [
            DeviceRecord(
                device_lct_id="b",
                anchor=fido2_anchor,
                enrolled_at="",
                last_witnessed="",
            )
        ]
        assert coherence_bonus(devs_2) == 0.08

        # 3 types
        devs_3 = devs_2 + [
            DeviceRecord(
                device_lct_id="c",
                anchor=tpm2_anchor,
                enrolled_at="",
                last_witnessed="",
            )
        ]
        assert coherence_bonus(devs_3) == 0.15

    def test_coherence_bonus_four_plus(
        self, phone_anchor, fido2_anchor, tpm2_anchor, software_anchor
    ):
        devs = [
            DeviceRecord(device_lct_id="a", anchor=phone_anchor, enrolled_at="", last_witnessed=""),
            DeviceRecord(device_lct_id="b", anchor=fido2_anchor, enrolled_at="", last_witnessed=""),
            DeviceRecord(device_lct_id="c", anchor=tpm2_anchor, enrolled_at="", last_witnessed=""),
            DeviceRecord(device_lct_id="d", anchor=software_anchor, enrolled_at="", last_witnessed=""),
        ]
        assert coherence_bonus(devs) == 0.20

    def test_cross_witness_density_no_devices(self):
        assert cross_witness_density([]) == 0.0

    def test_cross_witness_density_one_device(self, phone_anchor):
        devs = [
            DeviceRecord(
                device_lct_id="a",
                anchor=phone_anchor,
                enrolled_at="",
                last_witnessed="",
            )
        ]
        assert cross_witness_density(devs) == 0.0

    def test_cross_witness_density_full_mesh(self, multi_device_constellation):
        density = cross_witness_density(multi_device_constellation.active_devices)
        assert density == 1.0

    def test_cross_witness_density_partial(self, phone_anchor, fido2_anchor, tpm2_anchor):
        # Only phone↔fido witnessed, laptop not witnessed
        phone = DeviceRecord(
            device_lct_id="a",
            anchor=phone_anchor,
            enrolled_at="",
            last_witnessed="",
            cross_witnesses=["b"],
        )
        fido = DeviceRecord(
            device_lct_id="b",
            anchor=fido2_anchor,
            enrolled_at="",
            last_witnessed="",
            cross_witnesses=["a"],
        )
        laptop = DeviceRecord(
            device_lct_id="c",
            anchor=tpm2_anchor,
            enrolled_at="",
            last_witnessed="",
            cross_witnesses=[],
        )
        # 1 pair out of 3 possible = 1/3 ≈ 0.333
        density = cross_witness_density([phone, fido, laptop])
        assert abs(density - 1 / 3) < 0.001


# ── Trust Ceiling ────────────────────────────────────────────────

class TestTrustCeiling:
    def test_ceiling_empty(self, empty_constellation):
        assert constellation_trust_ceiling(empty_constellation) == 0.0

    def test_ceiling_single_software(self, software_anchor):
        c = DeviceConstellation(
            root_lct_id="lct:web4:root:x",
            devices=[
                DeviceRecord(
                    device_lct_id="sw",
                    anchor=software_anchor,
                    enrolled_at="",
                    last_witnessed="",
                )
            ],
        )
        assert constellation_trust_ceiling(c) == 0.40

    def test_ceiling_single_phone(self, single_phone_constellation):
        assert constellation_trust_ceiling(single_phone_constellation) == 0.75

    def test_ceiling_phone_fido2(self, phone_anchor, fido2_anchor):
        c = DeviceConstellation(
            root_lct_id="lct:web4:root:x",
            devices=[
                DeviceRecord(device_lct_id="a", anchor=phone_anchor, enrolled_at="", last_witnessed=""),
                DeviceRecord(device_lct_id="b", anchor=fido2_anchor, enrolled_at="", last_witnessed=""),
            ],
        )
        assert constellation_trust_ceiling(c) == 0.90

    def test_ceiling_phone_fido_tpm(self, multi_device_constellation):
        assert constellation_trust_ceiling(multi_device_constellation) == 0.95

    def test_ceiling_three_plus_diverse(
        self, phone_anchor, fido2_anchor, tpm2_anchor, software_anchor
    ):
        c = DeviceConstellation(
            root_lct_id="lct:web4:root:x",
            devices=[
                DeviceRecord(device_lct_id="a", anchor=phone_anchor, enrolled_at="", last_witnessed=""),
                DeviceRecord(device_lct_id="b", anchor=fido2_anchor, enrolled_at="", last_witnessed=""),
                DeviceRecord(device_lct_id="c", anchor=tpm2_anchor, enrolled_at="", last_witnessed=""),
                DeviceRecord(device_lct_id="d", anchor=software_anchor, enrolled_at="", last_witnessed=""),
            ],
        )
        # 3 hardware types → 3_plus_diverse
        assert constellation_trust_ceiling(c) == 0.98


# ── Cross-Device Witnessing ──────────────────────────────────────

class TestCrossWitnessing:
    def test_record_mutual_witness(self, empty_constellation, phone_anchor, fido2_anchor):
        p = enroll_device(empty_constellation, "p", phone_anchor, [], "2026-01-01T00:00:00Z")
        f = enroll_device(empty_constellation, "f", fido2_anchor, ["p"], "2026-01-02T00:00:00Z")

        record_cross_witness(empty_constellation, "p", "f", "2026-01-03T00:00:00Z")

        assert "f" in p.cross_witnesses
        assert "p" in f.cross_witnesses
        assert p.last_witnessed == "2026-01-03T00:00:00Z"
        assert f.last_witnessed == "2026-01-03T00:00:00Z"

    def test_witness_idempotent(self, empty_constellation, phone_anchor, fido2_anchor):
        enroll_device(empty_constellation, "p", phone_anchor, [], "2026-01-01T00:00:00Z")
        enroll_device(empty_constellation, "f", fido2_anchor, ["p"], "2026-01-02T00:00:00Z")

        record_cross_witness(empty_constellation, "p", "f", "2026-01-03T00:00:00Z")
        record_cross_witness(empty_constellation, "p", "f", "2026-01-04T00:00:00Z")

        # No duplicate entries
        p = empty_constellation.devices[0]
        assert p.cross_witnesses.count("f") == 1

    def test_witness_unknown_device_raises(self, single_phone_constellation):
        with pytest.raises(ValueError, match="not found"):
            record_cross_witness(
                single_phone_constellation,
                "lct:web4:device:phone1",
                "lct:web4:device:nonexistent",
                "2026-01-03T00:00:00Z",
            )

    def test_witness_revoked_device_raises(self, multi_device_constellation):
        # Revoke laptop first
        remove_device(
            multi_device_constellation,
            "lct:web4:device:laptop1",
            "sold",
            ["lct:web4:device:phone1", "lct:web4:device:fido1"],
            "2026-02-01T00:00:00Z",
        )
        with pytest.raises(ValueError, match="not active"):
            record_cross_witness(
                multi_device_constellation,
                "lct:web4:device:phone1",
                "lct:web4:device:laptop1",
                "2026-02-02T00:00:00Z",
            )


# ── Recovery ─────────────────────────────────────────────────────

class TestRecovery:
    def test_quorum_met(self, multi_device_constellation):
        assert check_recovery_quorum(
            multi_device_constellation,
            ["lct:web4:device:phone1", "lct:web4:device:fido1"],
        )

    def test_quorum_not_met(self, multi_device_constellation):
        assert not check_recovery_quorum(
            multi_device_constellation,
            ["lct:web4:device:phone1"],
        )

    def test_can_recover_yes(self, multi_device_constellation):
        feasible, reason = can_recover(
            multi_device_constellation,
            ["lct:web4:device:phone1", "lct:web4:device:fido1"],
        )
        assert feasible is True
        assert "feasible" in reason

    def test_can_recover_no_quorum(self, multi_device_constellation):
        feasible, reason = can_recover(
            multi_device_constellation,
            ["lct:web4:device:phone1"],
        )
        assert feasible is False
        assert "Quorum not met" in reason

    def test_can_recover_no_hardware(self, software_anchor):
        sw1 = DeviceRecord(
            device_lct_id="sw1",
            anchor=software_anchor,
            enrolled_at="",
            last_witnessed="",
        )
        sw2 = DeviceRecord(
            device_lct_id="sw2",
            anchor=software_anchor,
            enrolled_at="",
            last_witnessed="",
        )
        c = DeviceConstellation(
            root_lct_id="lct:web4:root:sw",
            devices=[sw1, sw2],
            recovery_quorum=2,
        )
        feasible, reason = can_recover(c, ["sw1", "sw2"])
        assert feasible is False
        assert "hardware-bound" in reason


# ── Integration Checks ───────────────────────────────────────────

class TestIntegration:
    def test_entity_device_type_exists(self):
        """EntityType.DEVICE exists for device LCTs."""
        from web4.lct import EntityType

        assert hasattr(EntityType, "DEVICE")
        assert EntityType.DEVICE.value == "device"

    def test_device_witnessing_valid(self):
        """DEVICE-DEVICE WITNESSING is a valid interaction."""
        from web4.entity import valid_interaction, InteractionType
        from web4.lct import EntityType

        assert valid_interaction(
            EntityType.DEVICE, EntityType.DEVICE, InteractionType.WITNESSING
        )

    def test_device_binding_valid(self):
        """SOCIETY→DEVICE binding is valid (delegative can bind)."""
        from web4.entity import valid_interaction, InteractionType
        from web4.lct import EntityType

        assert valid_interaction(
            EntityType.SOCIETY, EntityType.DEVICE, InteractionType.BINDING
        )


# ── Cross-Language Test Vectors ──────────────────────────────────

VECTORS_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "test-vectors" / "binding" / "binding-vectors.json"


class TestVectors:
    @pytest.fixture(autouse=True)
    def load_vectors(self):
        with open(VECTORS_PATH) as f:
            data = json.load(f)
        self.vectors = {v["name"]: v for v in data["vectors"]}

    def test_witness_freshness_decay(self):
        v = self.vectors["witness_freshness_decay"]
        for case in v["cases"]:
            result = witness_freshness(case["input_days"])
            assert result == case["expected_factor"], (
                f"days={case['input_days']}: expected {case['expected_factor']}, got {result}"
            )

    def test_recovery_quorum_calculation(self):
        v = self.vectors["recovery_quorum_calculation"]
        for case in v["cases"]:
            result = default_recovery_quorum(case["input_device_count"])
            assert result == case["expected_quorum"], (
                f"count={case['input_device_count']}: expected {case['expected_quorum']}, got {result}"
            )

    def test_coherence_bonus_by_diversity(self):
        v = self.vectors["coherence_bonus_by_diversity"]
        for case in v["cases"]:
            # Create fake devices with specified anchor types
            devices = []
            for i, atype in enumerate(case["input_anchor_types"]):
                devices.append(
                    DeviceRecord(
                        device_lct_id=f"dev{i}",
                        anchor=HardwareAnchor(anchor_type=AnchorType(atype)),
                        enrolled_at="",
                        last_witnessed="",
                    )
                )
            result = coherence_bonus(devices)
            assert result == case["expected_bonus"], (
                f"types={case['input_anchor_types']}: expected {case['expected_bonus']}, got {result}"
            )

    def test_trust_ceiling_by_config(self):
        v = self.vectors["trust_ceiling_by_config"]
        for case in v["cases"]:
            devices = []
            for i, atype in enumerate(case["input_anchor_types"]):
                devices.append(
                    DeviceRecord(
                        device_lct_id=f"dev{i}",
                        anchor=HardwareAnchor(anchor_type=AnchorType(atype)),
                        enrolled_at="",
                        last_witnessed="",
                    )
                )
            c = DeviceConstellation(root_lct_id="lct:test", devices=devices)
            result = constellation_trust_ceiling(c)
            assert result == case["expected_ceiling"], (
                f"config={case['input_anchor_types']}: expected {case['expected_ceiling']}, got {result}"
            )

    def test_constellation_trust_single(self):
        v = self.vectors["constellation_trust_single_device"]
        anchor = HardwareAnchor(
            anchor_type=AnchorType(v["input"]["anchor_type"]),
        )
        rec = DeviceRecord(
            device_lct_id="dev0",
            anchor=anchor,
            enrolled_at="",
            last_witnessed="",
        )
        c = DeviceConstellation(root_lct_id="lct:test", devices=[rec], recovery_quorum=1)
        trust = compute_constellation_trust(
            c,
            days_since_witness={"dev0": v["input"]["days_since_witness"]},
        )
        assert trust == v["expected"]["trust"]

    def test_constellation_trust_multi(self):
        v = self.vectors["constellation_trust_multi_device"]
        devices = []
        for i, dev_input in enumerate(v["input"]["devices"]):
            devices.append(
                DeviceRecord(
                    device_lct_id=f"dev{i}",
                    anchor=HardwareAnchor(anchor_type=AnchorType(dev_input["anchor_type"])),
                    enrolled_at="",
                    last_witnessed="",
                    cross_witnesses=dev_input.get("cross_witnesses", []),
                )
            )
        c = DeviceConstellation(
            root_lct_id="lct:test",
            devices=devices,
            recovery_quorum=default_recovery_quorum(len(devices)),
        )
        dsw = {
            f"dev{i}": dev_input["days_since_witness"]
            for i, dev_input in enumerate(v["input"]["devices"])
        }
        trust = compute_constellation_trust(c, days_since_witness=dsw)
        assert trust == v["expected"]["trust"]
