"""
Test that web4_sdk.py integrates with canonical web4.* modules.

Validates:
- web4_sdk re-exports canonical types
- LCTInfo converts to canonical LCT
- ReputationScore uses canonical T3/V3
- No type duplication between web4_sdk and web4.*
"""

import sys
from pathlib import Path

# Ensure SDK is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from web4.trust import T3, V3, coherence
from web4.lct import LCT, EntityType, RevocationStatus
from web4.atp import ATPAccount, energy_ratio


class TestSDKReexports:
    """Verify web4_sdk re-exports canonical types."""

    def test_imports_from_web4_sdk(self):
        """Canonical types available via web4_sdk import."""
        from web4_sdk import T3, V3, TrustProfile, LCT, EntityType, ATPAccount
        assert T3 is not None
        assert V3 is not None
        assert LCT is not None
        assert EntityType is not None
        assert ATPAccount is not None

    def test_same_objects(self):
        """web4_sdk re-exports are the SAME objects, not copies."""
        from web4_sdk import T3 as SDK_T3, EntityType as SDK_ET
        from web4.trust import T3 as Core_T3
        from web4.lct import EntityType as Core_ET
        assert SDK_T3 is Core_T3
        assert SDK_ET is Core_ET


class TestLCTInfoIntegration:
    """Test LCTInfo ↔ canonical LCT bridge."""

    def _make_lct_info(self):
        from web4_sdk import LCTInfo
        return LCTInfo(
            lct_id="lct:web4:ai:test123",
            entity_type="ai",
            entity_identifier="agent-001",
            society="lct:web4:society:genesis",
            public_key="mb64testkey123456789",
            birth_certificate_hash="abc123",
            witnesses=["w1", "w2", "w3"],
            created_at="2026-03-13T00:00:00Z",
            status="active",
        )

    def test_entity_type_enum(self):
        info = self._make_lct_info()
        assert info.entity_type_enum == EntityType.AI

    def test_entity_type_enum_unknown(self):
        from web4_sdk import LCTInfo
        info = LCTInfo(
            lct_id="x", entity_type="unknown_type", entity_identifier="",
            society="", public_key="", birth_certificate_hash="",
            witnesses=[], created_at="",
        )
        assert info.entity_type_enum is None

    def test_revocation_status(self):
        info = self._make_lct_info()
        assert info.revocation_status == RevocationStatus.ACTIVE

    def test_to_lct(self):
        info = self._make_lct_info()
        lct = info.to_lct()
        assert lct is not None
        assert isinstance(lct, LCT)
        assert lct.lct_id == "lct:web4:ai:test123"
        assert lct.binding.entity_type == EntityType.AI
        assert lct.is_active

    def test_to_lct_with_tensors(self):
        info = self._make_lct_info()
        t3 = T3(talent=0.8, training=0.9, temperament=0.7)
        v3 = V3(valuation=0.6, veracity=0.85, validity=0.9)
        lct = info.to_lct(t3=t3, v3=v3)
        assert lct.t3.talent == 0.8
        assert lct.v3.veracity == 0.85

    def test_to_lct_unknown_type_returns_none(self):
        from web4_sdk import LCTInfo
        info = LCTInfo(
            lct_id="x", entity_type="alien", entity_identifier="",
            society="", public_key="", birth_certificate_hash="",
            witnesses=[], created_at="",
        )
        assert info.to_lct() is None


class TestReputationScoreIntegration:
    """Test ReputationScore with canonical T3/V3."""

    def test_with_canonical_tensors(self):
        from web4_sdk import ReputationScore
        t3 = T3(talent=0.8, training=0.7, temperament=0.9)
        v3 = V3(valuation=0.6, veracity=0.85, validity=0.8)
        score = ReputationScore(
            entity_id="lct:alice",
            role="web4:DataAnalyst",
            t3_score=t3.composite,
            v3_score=v3.composite,
            action_count=42,
            last_updated="2026-03-13T00:00:00Z",
            t3=t3,
            v3=v3,
        )
        assert score.t3.talent == 0.8
        assert score.v3.veracity == 0.85
        assert abs(score.t3_score - 0.8) < 0.001  # t3v3-001 canonical composite

    def test_backward_compat_no_tensors(self):
        from web4_sdk import ReputationScore
        score = ReputationScore(
            entity_id="lct:bob",
            role="web4:Worker",
            t3_score=0.75,
            v3_score=0.60,
            action_count=10,
            last_updated="2026-03-13T00:00:00Z",
        )
        assert score.t3 is None
        assert score.v3 is None
        assert score.t3_score == 0.75

    def test_energy_ratio_from_metadata(self):
        from web4_sdk import ReputationScore
        score = ReputationScore(
            entity_id="lct:carol",
            role="role",
            t3_score=0.8,
            v3_score=0.6,
            action_count=5,
            last_updated="now",
            metadata={"atp": 80.0, "adp": 20.0},
        )
        assert abs(score.energy_ratio - 0.8) < 0.001

    def test_coherence_score(self):
        from web4_sdk import ReputationScore
        score = ReputationScore(
            entity_id="lct:dave",
            role="role",
            t3_score=0.8,
            v3_score=0.6,
            action_count=5,
            last_updated="now",
            metadata={"atp": 70.0, "adp": 30.0},
        )
        expected = coherence(0.8, 0.6, 0.7)
        assert abs(score.coherence_score - expected) < 0.001

    def test_no_energy_data(self):
        from web4_sdk import ReputationScore
        score = ReputationScore(
            entity_id="x", role="r", t3_score=0.5, v3_score=0.5,
            action_count=0, last_updated="now",
        )
        assert score.energy_ratio is None
        assert score.coherence_score is None


class TestAllEntityTypes:
    """Verify all 15 entity types are accessible via SDK."""

    def test_all_types(self):
        from web4_sdk import EntityType
        assert EntityType.HUMAN.value == "human"
        assert EntityType.AI.value == "ai"
        assert EntityType.SOCIETY.value == "society"
        assert EntityType.POLICY.value == "policy"
        assert EntityType.INFRASTRUCTURE.value == "infrastructure"
        assert len(EntityType) == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
