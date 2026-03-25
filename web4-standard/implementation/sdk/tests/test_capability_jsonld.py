"""
Tests for LCT Capability Levels JSON-LD serialization (A3).

Validates that LevelRequirement.to_jsonld(), capability_assessment_to_jsonld(),
and capability_framework_to_jsonld() produce spec-compliant documents and
that from_jsonld() round-trips cleanly.
"""

import json
import pytest

from web4.capability import (
    CapabilityLevel,
    CapabilityAssessment,
    LevelRequirement,
    CAPABILITY_JSONLD_CONTEXT,
    level_requirements,
    capability_assessment_to_jsonld,
    capability_assessment_from_jsonld,
    capability_assessment_from_jsonld_string,
    capability_framework_to_jsonld,
    capability_framework_from_jsonld,
    capability_framework_from_jsonld_string,
)
from web4.lct import LCT, EntityType, Binding, MRH, Policy
from web4.trust import T3, V3


# ── LevelRequirement JSON-LD ─────────────────────────────────────


class TestLevelRequirementJsonLd:
    """LevelRequirement.to_jsonld() / from_jsonld() tests."""

    def test_context_and_type(self):
        """JSON-LD document has correct @context and @type."""
        req = level_requirements(0)
        doc = req.to_jsonld()
        assert doc["@context"] == [CAPABILITY_JSONLD_CONTEXT]
        assert doc["@type"] == "LevelRequirement"

    def test_stub_level(self):
        """Level 0 (Stub) serializes correctly."""
        req = level_requirements(0)
        doc = req.to_jsonld()
        assert doc["level"] == 0
        assert doc["name"] == "Stub"
        assert doc["trust_range"] == [0.0, 0.0]
        assert len(doc["requirements"]) >= 1

    def test_hardware_level(self):
        """Level 5 (Hardware) serializes correctly."""
        req = level_requirements(5)
        doc = req.to_jsonld()
        assert doc["level"] == 5
        assert doc["name"] == "Hardware"
        assert doc["trust_range"] == [0.8, 1.0]

    def test_all_levels_serialize(self):
        """All 6 levels (0-5) serialize without error."""
        for lvl in range(6):
            req = level_requirements(lvl)
            doc = req.to_jsonld()
            assert doc["level"] == lvl
            assert isinstance(doc["trust_range"], list)
            assert len(doc["trust_range"]) == 2

    def test_roundtrip(self):
        """to_jsonld() -> from_jsonld() preserves all fields."""
        for lvl in range(6):
            req = level_requirements(lvl)
            doc = req.to_jsonld()
            restored = LevelRequirement.from_jsonld(doc)
            assert restored.level == req.level
            assert restored.name == req.name
            assert restored.description == req.description
            assert restored.requirements == req.requirements
            assert restored.trust_range == req.trust_range

    def test_string_roundtrip(self):
        """to_jsonld_string() -> from_jsonld_string() round-trips."""
        req = level_requirements(3)
        s = req.to_jsonld_string()
        restored = LevelRequirement.from_jsonld_string(s)
        assert restored == req

    def test_json_valid(self):
        """to_jsonld_string() produces valid JSON."""
        req = level_requirements(4)
        s = req.to_jsonld_string()
        parsed = json.loads(s)
        assert parsed["@type"] == "LevelRequirement"

    def test_trust_range_bounds(self):
        """Trust ranges are within [0, 1] and min <= max."""
        for lvl in range(6):
            req = level_requirements(lvl)
            doc = req.to_jsonld()
            tr = doc["trust_range"]
            assert 0.0 <= tr[0] <= 1.0
            assert 0.0 <= tr[1] <= 1.0
            assert tr[0] <= tr[1]

    def test_level_integer_type(self):
        """Level field serializes as integer, not float."""
        req = level_requirements(2)
        doc = req.to_jsonld()
        assert isinstance(doc["level"], int)


# ── CapabilityAssessment JSON-LD ──────────────────────────────────


class TestCapabilityAssessmentJsonLd:
    """capability_assessment_to_jsonld() tests."""

    def _make_stub_lct(self):
        """Create a minimal LCT (level 0 Stub)."""
        return LCT(
            lct_id="test-stub",
            subject="did:web4:key:stub",
            binding=Binding(
                entity_type=EntityType.HUMAN,
                public_key="",
                created_at="2026-01-01T00:00:00Z",
            ),
            mrh=MRH(),
            policy=Policy(),
            t3=T3(talent=0.0, training=0.0, temperament=0.0),
            v3=V3(valuation=0.0, veracity=0.0, validity=0.0),
        )

    def test_context_and_type(self):
        """Assessment document has correct @context and @type."""
        lct = self._make_stub_lct()
        doc = capability_assessment_to_jsonld(lct)
        assert doc["@context"] == [CAPABILITY_JSONLD_CONTEXT]
        assert doc["@type"] == "CapabilityAssessment"

    def test_stub_assessment(self):
        """Stub LCT assesses to level 0."""
        lct = self._make_stub_lct()
        doc = capability_assessment_to_jsonld(lct)
        assert doc["lct_id"] == "test-stub"
        assert doc["assessed_level"] == 0
        assert doc["level_name"] == "Stub"
        assert doc["trust_tier"] == "untrusted"
        assert doc["trust_range"] == [0.0, 0.0]
        assert doc["requirements_met"] is True
        assert doc["missing_requirements"] == []

    def test_assessment_has_required_fields(self):
        """Assessment document contains all required fields."""
        lct = self._make_stub_lct()
        doc = capability_assessment_to_jsonld(lct)
        required = [
            "@context", "@type", "lct_id", "assessed_level",
            "level_name", "trust_tier", "trust_range",
            "requirements_met", "missing_requirements",
        ]
        for field in required:
            assert field in doc, f"Missing field: {field}"

    def test_assessment_json_serializable(self):
        """Assessment document is JSON-serializable."""
        lct = self._make_stub_lct()
        doc = capability_assessment_to_jsonld(lct)
        s = json.dumps(doc, indent=2)
        parsed = json.loads(s)
        assert parsed["assessed_level"] == 0


# ── CapabilityFramework JSON-LD ───────────────────────────────────


class TestCapabilityFrameworkJsonLd:
    """capability_framework_to_jsonld() tests."""

    def test_context_and_type(self):
        """Framework document has correct @context and @type."""
        doc = capability_framework_to_jsonld()
        assert doc["@context"] == [CAPABILITY_JSONLD_CONTEXT]
        assert doc["@type"] == "CapabilityFramework"

    def test_contains_all_6_levels(self):
        """Framework contains all 6 capability levels (0-5)."""
        doc = capability_framework_to_jsonld()
        assert len(doc["levels"]) == 6

    def test_levels_ordered(self):
        """Levels are ordered 0 through 5."""
        doc = capability_framework_to_jsonld()
        levels = [entry["level"] for entry in doc["levels"]]
        assert levels == [0, 1, 2, 3, 4, 5]

    def test_each_level_has_required_fields(self):
        """Each level entry has all required JSON-LD fields."""
        doc = capability_framework_to_jsonld()
        for entry in doc["levels"]:
            assert "@context" in entry
            assert "@type" in entry
            assert "level" in entry
            assert "name" in entry
            assert "description" in entry
            assert "requirements" in entry
            assert "trust_range" in entry

    def test_framework_json_serializable(self):
        """Full framework is JSON-serializable."""
        doc = capability_framework_to_jsonld()
        s = json.dumps(doc, indent=2)
        parsed = json.loads(s)
        assert len(parsed["levels"]) == 6

    def test_trust_ranges_non_overlapping(self):
        """Trust ranges progress without gaps (each max = next min)."""
        doc = capability_framework_to_jsonld()
        levels = doc["levels"]
        # Level 0 is special (0.0, 0.0), level 1 starts at 0.0
        for i in range(2, len(levels)):
            prev_max = levels[i - 1]["trust_range"][1]
            curr_min = levels[i]["trust_range"][0]
            assert prev_max == pytest.approx(curr_min), \
                f"Gap between level {i-1} max ({prev_max}) and level {i} min ({curr_min})"


# ── CapabilityAssessment from_jsonld() roundtrip ──────────────────


class TestCapabilityAssessmentRoundtrip:
    """capability_assessment_to_jsonld() -> capability_assessment_from_jsonld() roundtrip."""

    def _make_stub_lct(self):
        """Create a minimal LCT (level 0 Stub)."""
        return LCT(
            lct_id="test-stub",
            subject="did:web4:key:stub",
            binding=Binding(
                entity_type=EntityType.HUMAN,
                public_key="",
                created_at="2026-01-01T00:00:00Z",
            ),
            mrh=MRH(),
            policy=Policy(),
            t3=T3(talent=0.0, training=0.0, temperament=0.0),
            v3=V3(valuation=0.0, veracity=0.0, validity=0.0),
        )

    def test_roundtrip_preserves_all_fields(self):
        """to_jsonld -> from_jsonld preserves all assessment fields."""
        lct = self._make_stub_lct()
        doc = capability_assessment_to_jsonld(lct)
        result = capability_assessment_from_jsonld(doc)
        assert isinstance(result, CapabilityAssessment)
        assert result.lct_id == "test-stub"
        assert result.assessed_level == 0
        assert result.level_name == "Stub"
        assert result.trust_tier == "untrusted"
        assert result.trust_range == (0.0, 0.0)
        assert result.requirements_met is True
        assert result.missing_requirements == []

    def test_roundtrip_via_json_string(self):
        """to_jsonld -> JSON string -> from_jsonld_string roundtrip."""
        lct = self._make_stub_lct()
        doc = capability_assessment_to_jsonld(lct)
        s = json.dumps(doc)
        result = capability_assessment_from_jsonld_string(s)
        assert result.lct_id == "test-stub"
        assert result.assessed_level == 0

    def test_assessment_is_frozen(self):
        """CapabilityAssessment is immutable (frozen dataclass)."""
        lct = self._make_stub_lct()
        doc = capability_assessment_to_jsonld(lct)
        result = capability_assessment_from_jsonld(doc)
        with pytest.raises(AttributeError):
            result.lct_id = "changed"

    def test_trust_range_is_tuple(self):
        """trust_range is deserialized as tuple, not list."""
        lct = self._make_stub_lct()
        doc = capability_assessment_to_jsonld(lct)
        result = capability_assessment_from_jsonld(doc)
        assert isinstance(result.trust_range, tuple)
        assert len(result.trust_range) == 2


# ── CapabilityFramework from_jsonld() roundtrip ──────────────────


class TestCapabilityFrameworkRoundtrip:
    """capability_framework_to_jsonld() -> capability_framework_from_jsonld() roundtrip."""

    def test_roundtrip_preserves_all_levels(self):
        """to_jsonld -> from_jsonld preserves all 6 levels."""
        doc = capability_framework_to_jsonld()
        levels = capability_framework_from_jsonld(doc)
        assert len(levels) == 6
        for i, req in enumerate(levels):
            assert isinstance(req, LevelRequirement)
            assert int(req.level) == i

    def test_roundtrip_preserves_level_details(self):
        """Round-tripped levels match the originals."""
        doc = capability_framework_to_jsonld()
        levels = capability_framework_from_jsonld(doc)
        for req in levels:
            original = level_requirements(int(req.level))
            assert req == original

    def test_string_roundtrip(self):
        """to_jsonld -> JSON string -> from_jsonld_string roundtrip."""
        doc = capability_framework_to_jsonld()
        s = json.dumps(doc)
        levels = capability_framework_from_jsonld_string(s)
        assert len(levels) == 6
        assert levels[0].name == "Stub"
        assert levels[5].name == "Hardware"

    def test_roundtrip_preserves_requirements_lists(self):
        """Round-trip preserves requirement strings for each level."""
        doc = capability_framework_to_jsonld()
        levels = capability_framework_from_jsonld(doc)
        # Level 0 has 2 requirements, Level 5 has 2 requirements
        assert len(levels[0].requirements) >= 1
        assert "Valid lct_id" in levels[0].requirements
        assert len(levels[5].requirements) >= 1
        assert "Hardware anchor in binding" in levels[5].requirements[1] or \
               any("hardware" in r.lower() for r in levels[5].requirements)

    def test_roundtrip_preserves_trust_ranges(self):
        """Round-trip preserves trust range tuples."""
        doc = capability_framework_to_jsonld()
        levels = capability_framework_from_jsonld(doc)
        assert levels[0].trust_range == (0.0, 0.0)
        assert levels[5].trust_range == (0.8, 1.0)
