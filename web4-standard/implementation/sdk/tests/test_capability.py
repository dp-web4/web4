"""
Tests for web4.capability — LCT Capability Levels.

Validates level assessment, validation, upgrade paths, entity-level ranges,
trust tiers, and cross-domain common ground per lct-capability-levels.md.
"""

import json
import pathlib
import pytest

from web4.capability import (
    CapabilityLevel,
    TrustTier,
    ENTITY_LEVEL_RANGES,
    LevelRequirement,
    assess_level,
    validate_level,
    can_upgrade,
    level_requirements,
    trust_tier,
    entity_level_range,
    is_level_typical,
    common_ground,
)
from web4.lct import (
    LCT,
    EntityType,
    Binding,
    MRH,
    MRHPairing,
    BirthCertificate,
    Policy,
)
from web4.trust import T3, V3


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def stub_lct():
    """Level 0: no binding, no MRH, no tensors."""
    return LCT(
        lct_id="lct:web4:pending:placeholder123",
        subject="did:web4:key:stub",
        binding=Binding(
            entity_type=EntityType.AI,
            public_key="",  # empty = no binding
            created_at="2026-01-01T00:00:00Z",
        ),
        mrh=MRH(),
        policy=Policy(),
        t3=T3(talent=0.0, training=0.0, temperament=0.0),
        v3=V3(valuation=0.0, veracity=0.0, validity=0.0),
    )


@pytest.fixture
def minimal_lct():
    """Level 1: binding with public key, default tensors."""
    return LCT(
        lct_id="lct:web4:plugin:vision-abc123",
        subject="did:web4:key:minimal",
        binding=Binding(
            entity_type=EntityType.AI,
            public_key="mb64:ed25519:abc123",
            created_at="2026-01-01T00:00:00Z",
            binding_proof="cose:ES256:proof",
        ),
        mrh=MRH(),
        policy=Policy(),
        t3=T3(talent=0.1, training=0.1, temperament=0.1),
        v3=V3(valuation=0.0, veracity=0.0, validity=0.0),
    )


@pytest.fixture
def basic_lct():
    """Level 2: MRH relationship + non-zero T3 + capability."""
    return LCT(
        lct_id="lct:web4:ai:basic-agent",
        subject="did:web4:key:basic",
        binding=Binding(
            entity_type=EntityType.AI,
            public_key="mb64:ed25519:basic123",
            created_at="2026-01-01T00:00:00Z",
            binding_proof="cose:ES256:proof",
        ),
        mrh=MRH(
            paired=[
                MRHPairing(
                    lct_id="lct:web4:ai:orchestrator",
                    pairing_type="deployment",
                    permanent=False,
                    ts="2026-01-01T00:00:00Z",
                )
            ],
        ),
        policy=Policy(capabilities=["execute:irp", "read:patterns"]),
        t3=T3(talent=0.5, training=0.4, temperament=0.3),
        v3=V3(valuation=0.0, veracity=0.0, validity=0.0),
    )


@pytest.fixture
def standard_lct():
    """Level 3: witnessing + non-zero V3."""
    return LCT(
        lct_id="lct:web4:ai:standard-agent",
        subject="did:web4:key:standard",
        binding=Binding(
            entity_type=EntityType.AI,
            public_key="mb64:ed25519:std123",
            created_at="2026-01-01T00:00:00Z",
            binding_proof="cose:ES256:proof",
        ),
        mrh=MRH(
            paired=[
                MRHPairing(
                    lct_id="lct:web4:role:citizen:platform",
                    pairing_type="birth_certificate",
                    permanent=True,
                    ts="2026-01-01T00:00:00Z",
                )
            ],
            witnessing=["lct:web4:oracle:time:global"],
        ),
        policy=Policy(capabilities=["execute:irp"]),
        t3=T3(talent=0.7, training=0.6, temperament=0.65),
        v3=V3(valuation=0.5, veracity=0.6, validity=0.4),
    )


@pytest.fixture
def full_lct():
    """Level 4: birth certificate with ≥3 witnesses + permanent citizen pairing."""
    return LCT(
        lct_id="lct:web4:human:full-identity",
        subject="did:web4:key:full",
        binding=Binding(
            entity_type=EntityType.HUMAN,
            public_key="mb64:ed25519:full123",
            created_at="2026-01-01T00:00:00Z",
            binding_proof="cose:ES256:proof",
        ),
        mrh=MRH(
            paired=[
                MRHPairing(
                    lct_id="lct:web4:role:citizen:researcher",
                    pairing_type="birth_certificate",
                    permanent=True,
                    ts="2026-01-01T00:00:00Z",
                )
            ],
            witnessing=["lct:web4:oracle:trust:federation"],
        ),
        policy=Policy(capabilities=["exist", "interact", "accumulate_reputation"]),
        t3=T3(talent=0.8, training=0.7, temperament=0.75),
        v3=V3(valuation=0.6, veracity=0.7, validity=0.5),
        birth_certificate=BirthCertificate(
            issuing_society="lct:web4:society:web4-foundation",
            citizen_role="lct:web4:role:citizen:researcher",
            birth_timestamp="2026-01-01T00:00:00Z",
            birth_witnesses=[
                "lct:web4:witness:1",
                "lct:web4:witness:2",
                "lct:web4:witness:3",
            ],
            context="federation",
        ),
    )


@pytest.fixture
def hardware_lct():
    """Level 5: hardware anchor + all Level 4 requirements."""
    return LCT(
        lct_id="lct:web4:device:hw-bound",
        subject="did:web4:key:hardware",
        binding=Binding(
            entity_type=EntityType.DEVICE,
            public_key="mb64:coseKey:hw123",
            created_at="2026-01-01T00:00:00Z",
            binding_proof="cose:ES256:proof",
            hardware_anchor="eat:mb64:hw:tpm2-attestation",
        ),
        mrh=MRH(
            paired=[
                MRHPairing(
                    lct_id="lct:web4:role:citizen:infrastructure",
                    pairing_type="birth_certificate",
                    permanent=True,
                    ts="2026-01-01T00:00:00Z",
                )
            ],
            witnessing=["lct:web4:oracle:trust:federation"],
        ),
        policy=Policy(capabilities=["exist", "interact"]),
        t3=T3(talent=0.9, training=0.85, temperament=0.9),
        v3=V3(valuation=0.8, veracity=0.9, validity=0.7),
        birth_certificate=BirthCertificate(
            issuing_society="lct:web4:society:web4-foundation",
            citizen_role="lct:web4:role:citizen:infrastructure",
            birth_timestamp="2026-01-01T00:00:00Z",
            birth_witnesses=[
                "lct:web4:witness:1",
                "lct:web4:witness:2",
                "lct:web4:witness:3",
            ],
            context="infrastructure",
        ),
    )


# ── Level Assessment Tests ───────────────────────────────────────

class TestAssessLevel:
    """Test assess_level() returns correct capability level."""

    def test_stub_level(self, stub_lct):
        assert assess_level(stub_lct) == CapabilityLevel.STUB

    def test_minimal_level(self, minimal_lct):
        assert assess_level(minimal_lct) == CapabilityLevel.MINIMAL

    def test_basic_level(self, basic_lct):
        assert assess_level(basic_lct) == CapabilityLevel.BASIC

    def test_standard_level(self, standard_lct):
        assert assess_level(standard_lct) == CapabilityLevel.STANDARD

    def test_full_level(self, full_lct):
        assert assess_level(full_lct) == CapabilityLevel.FULL

    def test_hardware_level(self, hardware_lct):
        assert assess_level(hardware_lct) == CapabilityLevel.HARDWARE

    def test_levels_are_ordered(self):
        """Capability levels are strictly ordered 0-5."""
        assert CapabilityLevel.STUB < CapabilityLevel.MINIMAL
        assert CapabilityLevel.MINIMAL < CapabilityLevel.BASIC
        assert CapabilityLevel.BASIC < CapabilityLevel.STANDARD
        assert CapabilityLevel.STANDARD < CapabilityLevel.FULL
        assert CapabilityLevel.FULL < CapabilityLevel.HARDWARE


# ── Validation Tests ─────────────────────────────────────────────

class TestValidateLevel:
    """Test validate_level() checks requirements correctly."""

    def test_stub_always_valid(self, stub_lct):
        valid, missing = validate_level(stub_lct, 0)
        assert valid
        assert missing == []

    def test_minimal_valid(self, minimal_lct):
        valid, missing = validate_level(minimal_lct, 1)
        assert valid
        assert missing == []

    def test_stub_fails_minimal(self, stub_lct):
        valid, missing = validate_level(stub_lct, 1)
        assert not valid
        assert any("Binding" in m for m in missing)

    def test_minimal_fails_basic(self, minimal_lct):
        valid, missing = validate_level(minimal_lct, 2)
        assert not valid
        assert any("MRH" in m for m in missing)

    def test_basic_fails_standard(self, basic_lct):
        valid, missing = validate_level(basic_lct, 3)
        assert not valid
        assert any("witnessing" in m for m in missing)

    def test_standard_fails_full(self, standard_lct):
        """Standard LCT fails full validation (no birth cert with ≥3 witnesses)."""
        valid, missing = validate_level(standard_lct, 4)
        assert not valid
        assert any("birth certificate" in m for m in missing)

    def test_full_fails_hardware(self, full_lct):
        valid, missing = validate_level(full_lct, 5)
        assert not valid
        assert any("Hardware" in m or "hardware" in m for m in missing)

    def test_hardware_valid_at_all_levels(self, hardware_lct):
        """Hardware LCT meets requirements for all levels."""
        for level in range(6):
            valid, missing = validate_level(hardware_lct, level)
            assert valid, f"Hardware LCT should be valid at level {level}, missing: {missing}"


# ── Upgrade Tests ────────────────────────────────────────────────

class TestCanUpgrade:
    """Test can_upgrade() checks upgrade constraints."""

    def test_stub_can_upgrade_to_minimal(self, stub_lct):
        """Stub can't upgrade without meeting requirements."""
        ok, blockers = can_upgrade(stub_lct, 1)
        assert not ok
        assert any("Binding" in b for b in blockers)

    def test_minimal_can_upgrade_to_basic_if_requirements_met(self, basic_lct):
        """Already at basic — downgrade not permitted."""
        ok, blockers = can_upgrade(basic_lct, 1)
        assert not ok
        assert any("downgrade" in b.lower() or "Already" in b for b in blockers)

    def test_downgrade_not_permitted(self, hardware_lct):
        ok, blockers = can_upgrade(hardware_lct, 3)
        assert not ok
        assert any("downgrade" in b.lower() or "Already" in b for b in blockers)

    def test_same_level_not_permitted(self, basic_lct):
        ok, blockers = can_upgrade(basic_lct, 2)
        assert not ok

    def test_hardware_requires_creation_binding(self, full_lct):
        """Full LCT can't upgrade to hardware without hardware anchor."""
        ok, blockers = can_upgrade(full_lct, 5)
        assert not ok
        assert any("hardware" in b.lower() for b in blockers)


# ── Trust Tier Tests ─────────────────────────────────────────────

class TestTrustTier:
    """Test trust_tier() mapping."""

    def test_stub_untrusted(self):
        name, lo, hi = trust_tier(0)
        assert name == TrustTier.UNTRUSTED
        assert lo == 0.0
        assert hi == 0.0

    def test_minimal_low(self):
        name, lo, hi = trust_tier(1)
        assert name == TrustTier.LOW
        assert lo == 0.0
        assert hi == 0.2

    def test_hardware_maximum(self):
        name, lo, hi = trust_tier(5)
        assert name == TrustTier.MAXIMUM
        assert lo == 0.8
        assert hi == 1.0

    def test_all_levels_have_tiers(self):
        for level in CapabilityLevel:
            name, lo, hi = trust_tier(level)
            assert isinstance(name, str)
            assert lo <= hi


# ── Entity-Level Range Tests ─────────────────────────────────────

class TestEntityLevelRanges:
    """Test entity type to capability level range mapping."""

    def test_all_entity_types_covered(self):
        for et in EntityType:
            assert et in ENTITY_LEVEL_RANGES, f"Missing range for {et}"

    def test_human_range(self):
        lo, hi = entity_level_range(EntityType.HUMAN)
        assert lo == 4
        assert hi == 5

    def test_device_range(self):
        lo, hi = entity_level_range(EntityType.DEVICE)
        assert lo == 3
        assert hi == 5

    def test_task_range(self):
        lo, hi = entity_level_range(EntityType.TASK)
        assert lo == 1
        assert hi == 2

    def test_is_level_typical_true(self):
        assert is_level_typical(EntityType.HUMAN, 4)
        assert is_level_typical(EntityType.HUMAN, 5)
        assert is_level_typical(EntityType.AI, 3)

    def test_is_level_typical_false(self):
        assert not is_level_typical(EntityType.HUMAN, 1)
        assert not is_level_typical(EntityType.TASK, 5)

    def test_ranges_are_valid(self):
        for et, (lo, hi) in ENTITY_LEVEL_RANGES.items():
            assert 0 <= lo <= hi <= 5, f"Invalid range for {et}: ({lo}, {hi})"


# ── Level Requirements Tests ─────────────────────────────────────

class TestLevelRequirements:
    """Test level_requirements() returns correct descriptions."""

    def test_all_levels_have_requirements(self):
        for level in CapabilityLevel:
            req = level_requirements(level)
            assert isinstance(req, LevelRequirement)
            assert req.level == level
            assert len(req.requirements) > 0

    def test_stub_description(self):
        req = level_requirements(0)
        assert "Stub" in req.name or "Placeholder" in req.description

    def test_hardware_description(self):
        req = level_requirements(5)
        assert "Hardware" in req.name or "hardware" in req.description.lower()

    def test_trust_ranges_match_tiers(self):
        for level in CapabilityLevel:
            req = level_requirements(level)
            _, lo, hi = trust_tier(level)
            assert req.trust_range == (lo, hi)


# ── Common Ground Tests ──────────────────────────────────────────

class TestCommonGround:
    """Test common_ground() for cross-domain interaction."""

    def test_same_level(self):
        assert common_ground(3, 3) == CapabilityLevel.STANDARD

    def test_different_levels(self):
        assert common_ground(5, 2) == CapabilityLevel.BASIC

    def test_stub_always_wins(self):
        for level in range(6):
            assert common_ground(0, level) == CapabilityLevel.STUB

    def test_symmetric(self):
        for a in range(6):
            for b in range(6):
                assert common_ground(a, b) == common_ground(b, a)


# ── Test Vector Tests ────────────────────────────────────────────

VECTORS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "test-vectors" / "capability"


class TestVectors:
    """Test against cross-language test vectors."""

    @pytest.fixture(autouse=True)
    def load_vectors(self):
        vectors_path = VECTORS_DIR / "capability-levels.json"
        if not vectors_path.exists():
            pytest.skip("Test vectors not found")
        with open(vectors_path) as f:
            self.vectors = json.load(f)["vectors"]

    def _build_lct_from_vector(self, v: dict) -> LCT:
        """Build an LCT from test vector data."""
        inp = v["input"]

        binding = Binding(
            entity_type=EntityType(inp["entity_type"]),
            public_key=inp.get("public_key", ""),
            created_at="2026-01-01T00:00:00Z",
            binding_proof=inp.get("binding_proof", ""),
            hardware_anchor=inp.get("hardware_anchor"),
        )

        paired = [
            MRHPairing(
                lct_id=p["lct_id"],
                pairing_type=p.get("pairing_type", ""),
                permanent=p.get("permanent", False),
                ts=p.get("ts", ""),
            )
            for p in inp.get("paired", [])
        ]

        mrh = MRH(
            bound=inp.get("bound", []),
            paired=paired,
            witnessing=inp.get("witnessing", []),
        )

        policy = Policy(capabilities=inp.get("capabilities", []))

        t3_data = inp.get("t3", {})
        t3 = T3(
            talent=t3_data.get("talent", 0.0),
            training=t3_data.get("training", 0.0),
            temperament=t3_data.get("temperament", 0.0),
        )

        v3_data = inp.get("v3", {})
        v3 = V3(
            valuation=v3_data.get("valuation", 0.0),
            veracity=v3_data.get("veracity", 0.0),
            validity=v3_data.get("validity", 0.0),
        )

        bc = None
        bc_data = inp.get("birth_certificate")
        if bc_data:
            bc = BirthCertificate(
                issuing_society=bc_data["issuing_society"],
                citizen_role=bc_data["citizen_role"],
                birth_timestamp=bc_data.get("birth_timestamp", "2026-01-01T00:00:00Z"),
                birth_witnesses=bc_data.get("birth_witnesses", []),
                context=bc_data.get("context", "platform"),
            )

        return LCT(
            lct_id=inp.get("lct_id", "lct:web4:test:vector"),
            subject=inp.get("subject", "did:web4:key:test"),
            binding=binding,
            mrh=mrh,
            policy=policy,
            t3=t3,
            v3=v3,
            birth_certificate=bc,
        )

    def test_assess_level_vectors(self):
        for v in self.vectors:
            if "expected_level" not in v["expected"]:
                continue
            lct = self._build_lct_from_vector(v)
            result = assess_level(lct)
            assert result == v["expected"]["expected_level"], (
                f"Vector '{v['name']}': expected level {v['expected']['expected_level']}, got {result}"
            )

    def test_trust_tier_vectors(self):
        for v in self.vectors:
            if "trust_tier" not in v["expected"]:
                continue
            level = v["expected"]["expected_level"]
            name, lo, hi = trust_tier(level)
            assert name == v["expected"]["trust_tier"], (
                f"Vector '{v['name']}': expected tier {v['expected']['trust_tier']}, got {name}"
            )

    def test_is_typical_vectors(self):
        for v in self.vectors:
            if "is_typical" not in v["expected"]:
                continue
            et = EntityType(v["input"]["entity_type"])
            level = v["expected"]["expected_level"]
            result = is_level_typical(et, level)
            assert result == v["expected"]["is_typical"], (
                f"Vector '{v['name']}': expected is_typical={v['expected']['is_typical']}, got {result}"
            )
