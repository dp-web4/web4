"""Tests for web4.trust — T3/V3 tensor enhancements (U10).

Covers: outcome-based evolution, decay/refresh, role requirements,
V3 calculation, team tensor composition, plus existing functionality.
"""

import json
import os
from typing import Any, Dict
import pytest

from web4.trust import (
    T3,
    V3,
    ActionOutcome,
    OUTCOME_DELTAS,
    TRAINING_DECAY_PER_MONTH,
    TEMPERAMENT_RECOVERY_PER_MONTH,
    RoleRequirement,
    RoleTensors,
    TrustProfile,
    TrustQuery,
    TrustQueryResponse,
    DisclosureLevel,
    TRUST_QUERY_MIN_STAKE,
    TRUST_QUERY_MIN_VALIDITY,
    TRUST_QUERY_MAX_VALIDITY,
    compute_team_t3,
    trust_bridge,
    mrh_trust_decay,
    mrh_zone,
    operational_health,
    is_healthy,
    diminishing_returns,
    T3_WEIGHTS,
    V3_WEIGHTS,
    HEALTH_THRESHOLD,
)

TOL = 0.0001


# ── T3 basics ────────────────────────────────────────────────────


class TestT3:
    def test_defaults(self):
        t = T3()
        assert t.talent == 0.5
        assert t.training == 0.5
        assert t.temperament == 0.5

    def test_clamping_low(self):
        t = T3(-0.5, -1.0, -0.1)
        assert t.talent == 0.0
        assert t.training == 0.0
        assert t.temperament == 0.0

    def test_clamping_high(self):
        t = T3(1.5, 2.0, 1.1)
        assert t.talent == 1.0
        assert t.training == 1.0
        assert t.temperament == 1.0

    def test_composite(self):
        t = T3(0.8, 0.7, 0.9)
        expected = 0.8 * 0.4 + 0.7 * 0.3 + 0.9 * 0.3
        assert abs(t.composite - expected) < TOL

    def test_update_positive(self):
        t = T3(0.5, 0.5, 0.5).update(0.8)
        assert t.talent > 0.5
        assert t.training > 0.5
        assert t.temperament > 0.5

    def test_update_negative(self):
        t = T3(0.5, 0.5, 0.5).update(0.3)
        assert t.talent < 0.5
        assert t.training < 0.5
        assert t.temperament < 0.5

    def test_as_dict(self):
        t = T3(0.8, 0.7, 0.9)
        d = t.as_dict()
        assert d == {"talent": 0.8, "training": 0.7, "temperament": 0.9}


# ── Outcome-based evolution (spec §2.3) ──────────────────────────


class TestT3Evolution:
    def test_novel_success(self):
        t = T3(0.5, 0.5, 0.5)
        t2 = t.evolve(ActionOutcome.NOVEL_SUCCESS)
        assert t2.talent == pytest.approx(0.535, abs=TOL)
        assert t2.training == pytest.approx(0.515, abs=TOL)
        assert t2.temperament == pytest.approx(0.51, abs=TOL)

    def test_standard_success(self):
        t = T3(0.5, 0.5, 0.5)
        t2 = t.evolve(ActionOutcome.STANDARD_SUCCESS)
        assert t2.talent == pytest.approx(0.5, abs=TOL)
        assert t2.training == pytest.approx(0.5075, abs=TOL)
        assert t2.temperament == pytest.approx(0.505, abs=TOL)

    def test_expected_failure(self):
        t = T3(0.5, 0.5, 0.5)
        t2 = t.evolve(ActionOutcome.EXPECTED_FAILURE)
        assert t2.talent == pytest.approx(0.49, abs=TOL)
        assert t2.training == pytest.approx(0.5, abs=TOL)
        assert t2.temperament == pytest.approx(0.5, abs=TOL)

    def test_unexpected_failure(self):
        t = T3(0.5, 0.5, 0.5)
        t2 = t.evolve(ActionOutcome.UNEXPECTED_FAILURE)
        assert t2.talent == pytest.approx(0.48, abs=TOL)
        assert t2.training == pytest.approx(0.49, abs=TOL)
        assert t2.temperament == pytest.approx(0.48, abs=TOL)

    def test_ethics_violation(self):
        t = T3(0.5, 0.5, 0.5)
        t2 = t.evolve(ActionOutcome.ETHICS_VIOLATION)
        assert t2.talent == pytest.approx(0.45, abs=TOL)
        assert t2.training == pytest.approx(0.5, abs=TOL)
        assert t2.temperament == pytest.approx(0.4, abs=TOL)

    def test_evolution_clamps_at_zero(self):
        t = T3(0.03, 0.0, 0.05)
        t2 = t.evolve(ActionOutcome.ETHICS_VIOLATION)
        assert t2.talent == 0.0
        assert t2.temperament == 0.0

    def test_evolution_clamps_at_one(self):
        t = T3(0.98, 0.99, 0.995)
        t2 = t.evolve(ActionOutcome.NOVEL_SUCCESS)
        assert t2.talent == 1.0
        assert t2.training == 1.0
        assert t2.temperament == 1.0

    def test_evolution_immutable(self):
        t = T3(0.5, 0.5, 0.5)
        t2 = t.evolve(ActionOutcome.NOVEL_SUCCESS)
        assert t.talent == 0.5  # original unchanged


# ── Decay/refresh (spec §2.3) ────────────────────────────────────


class TestT3Decay:
    def test_training_decays(self):
        t = T3(0.8, 0.8, 0.8)
        t2 = t.decay(12)  # 12 months
        assert t2.training == pytest.approx(0.8 - 0.001 * 12, abs=TOL)

    def test_temperament_recovers(self):
        t = T3(0.8, 0.8, 0.5)
        t2 = t.decay(6)
        assert t2.temperament == pytest.approx(0.5 + 0.01 * 6, abs=TOL)

    def test_talent_stable(self):
        t = T3(0.8, 0.8, 0.8)
        t2 = t.decay(24)
        assert t2.talent == 0.8

    def test_decay_clamps(self):
        t = T3(0.5, 0.0005, 0.995)
        t2 = t.decay(1)
        assert t2.training == 0.0
        assert t2.temperament == 1.0

    def test_zero_months(self):
        t = T3(0.5, 0.5, 0.5)
        t2 = t.decay(0)
        assert t2.training == 0.5
        assert t2.temperament == 0.5


# ── V3 basics ────────────────────────────────────────────────────


class TestV3:
    def test_defaults(self):
        v = V3()
        assert v.valuation == 0.5
        assert v.veracity == 0.5
        assert v.validity == 0.5

    def test_composite(self):
        v = V3(0.3, 0.85, 0.8)
        expected = 0.3 * 0.3 + 0.85 * 0.35 + 0.8 * 0.35
        assert abs(v.composite - expected) < TOL


# ── V3 calculation (spec §3.3) ───────────────────────────────────


class TestV3Calculate:
    def test_basic_calculation(self):
        v = V3.calculate(
            atp_earned=50,
            atp_expected=55,
            recipient_satisfaction=0.95,
            verified_claims=9,
            total_claims=10,
            witness_confidence=0.9,
            value_transferred=True,
        )
        assert v.valuation == pytest.approx(50 / 55 * 0.95, abs=TOL)
        assert v.veracity == pytest.approx(9 / 10 * 0.9, abs=TOL)
        assert v.validity == 1.0

    def test_value_not_transferred(self):
        v = V3.calculate(
            atp_earned=50,
            atp_expected=55,
            recipient_satisfaction=0.95,
            verified_claims=9,
            total_claims=10,
            witness_confidence=0.9,
            value_transferred=False,
        )
        assert v.validity == 0.0

    def test_zero_expected_atp(self):
        v = V3.calculate(
            atp_earned=10,
            atp_expected=0,
            recipient_satisfaction=0.5,
            verified_claims=5,
            total_claims=10,
            witness_confidence=0.8,
            value_transferred=True,
        )
        assert v.valuation == 0.0

    def test_zero_total_claims(self):
        v = V3.calculate(
            atp_earned=10,
            atp_expected=20,
            recipient_satisfaction=0.5,
            verified_claims=0,
            total_claims=0,
            witness_confidence=0.8,
            value_transferred=True,
        )
        assert v.veracity == 0.0

    def test_clamped_valuation(self):
        v = V3.calculate(
            atp_earned=100,
            atp_expected=50,
            recipient_satisfaction=1.0,
            verified_claims=10,
            total_claims=10,
            witness_confidence=1.0,
            value_transferred=True,
        )
        # 100/50 * 1.0 = 2.0, clamped to 1.0
        assert v.valuation == 1.0

    def test_perfect_action(self):
        v = V3.calculate(
            atp_earned=100,
            atp_expected=100,
            recipient_satisfaction=1.0,
            verified_claims=10,
            total_claims=10,
            witness_confidence=1.0,
            value_transferred=True,
        )
        assert v.valuation == 1.0
        assert v.veracity == 1.0
        assert v.validity == 1.0


# ── Role requirements (spec §5.1) ────────────────────────────────


class TestRoleRequirement:
    def test_qualified(self):
        rr = RoleRequirement("web4:Surgeon", min_talent=0.7, min_training=0.9, min_temperament=0.85)
        t = T3(0.95, 0.92, 0.88)
        assert rr.is_qualified(t)

    def test_not_qualified(self):
        rr = RoleRequirement("web4:Surgeon", min_talent=0.7, min_training=0.9, min_temperament=0.85)
        t = T3(0.8, 0.7, 0.9)  # training below threshold
        assert not rr.is_qualified(t)

    def test_evaluate_qualified(self):
        rr = RoleRequirement("web4:Surgeon", min_talent=0.7, min_training=0.9, min_temperament=0.85)
        t = T3(0.95, 0.92, 0.88)
        result = rr.evaluate(t)
        assert result["qualified"] is True
        assert result["trust_score"] == pytest.approx(t.composite, abs=TOL)
        assert result["gaps"]["talent"] == 0.0
        assert result["gaps"]["training"] == 0.0

    def test_evaluate_not_qualified_shows_gaps(self):
        rr = RoleRequirement("web4:Surgeon", min_talent=0.7, min_training=0.9, min_temperament=0.85)
        t = T3(0.6, 0.5, 0.7)
        result = rr.evaluate(t)
        assert result["qualified"] is False
        assert result["trust_score"] == 0.0
        assert result["gaps"]["talent"] == pytest.approx(0.1, abs=TOL)
        assert result["gaps"]["training"] == pytest.approx(0.4, abs=TOL)
        assert result["gaps"]["temperament"] == pytest.approx(0.15, abs=TOL)

    def test_exact_threshold(self):
        rr = RoleRequirement("role", min_talent=0.5, min_training=0.5, min_temperament=0.5)
        t = T3(0.5, 0.5, 0.5)
        assert rr.is_qualified(t)


# ── Team tensor composition (spec §8.2) ──────────────────────────


class TestTeamComposition:
    def _make_team(self):
        """Three-member team with mixed roles."""
        p1 = TrustProfile("alice")
        p1.set_role("surgeon", t3=T3(0.9, 0.95, 0.88))

        p2 = TrustProfile("bob")
        p2.set_role("surgeon", t3=T3(0.8, 0.85, 0.90))

        p3 = TrustProfile("carol")
        p3.set_role("analyst", t3=T3(0.7, 0.8, 0.75))
        # carol is NOT a surgeon
        return [p1, p2, p3]

    def test_team_t3_equal_weight(self):
        team = self._make_team()
        result = compute_team_t3(team, "surgeon")
        assert result is not None
        # Only alice and bob qualify
        assert result.talent == pytest.approx((0.9 + 0.8) / 2, abs=TOL)
        assert result.training == pytest.approx((0.95 + 0.85) / 2, abs=TOL)
        assert result.temperament == pytest.approx((0.88 + 0.90) / 2, abs=TOL)

    def test_team_t3_weighted(self):
        team = self._make_team()
        weights = {"alice": 2.0, "bob": 1.0}
        result = compute_team_t3(team, "surgeon", weights=weights)
        assert result is not None
        total_w = 3.0
        assert result.talent == pytest.approx((0.9 * 2 + 0.8 * 1) / total_w, abs=TOL)

    def test_no_qualified_members(self):
        team = self._make_team()
        result = compute_team_t3(team, "mechanic")
        assert result is None

    def test_single_member(self):
        p = TrustProfile("alice")
        p.set_role("surgeon", t3=T3(0.9, 0.95, 0.88))
        result = compute_team_t3([p], "surgeon")
        assert result is not None
        assert result.talent == pytest.approx(0.9, abs=TOL)


# ── TrustProfile ─────────────────────────────────────────────────


class TestTrustProfile:
    def test_set_and_get(self):
        p = TrustProfile("alice")
        p.set_role("analyst", t3=T3(0.8, 0.7, 0.9))
        assert p.get_t3("analyst").talent == 0.8

    def test_default_for_unknown_role(self):
        p = TrustProfile("alice")
        t = p.get_t3("unknown")
        assert t.talent == 0.5

    def test_roles_list(self):
        p = TrustProfile("alice")
        p.set_role("analyst", t3=T3(0.8, 0.7, 0.9))
        p.set_role("manager", t3=T3(0.6, 0.7, 0.8))
        assert sorted(p.roles) == ["analyst", "manager"]


# ── Existing operations ──────────────────────────────────────────


class TestExistingOperations:
    def test_trust_bridge(self):
        t = trust_bridge(0.7, 0.6, 0.5, 0.8, 0.4, 0.3)
        assert abs(t.talent - 0.62) < 0.01

    def test_mrh_decay(self):
        assert mrh_trust_decay(1.0, 0) == 1.0
        assert abs(mrh_trust_decay(1.0, 1) - 0.7) < TOL
        assert mrh_trust_decay(1.0, 5) == 0.0

    def test_mrh_zones(self):
        assert mrh_zone(0) == "SELF"
        assert mrh_zone(1) == "DIRECT"
        assert mrh_zone(2) == "INDIRECT"
        assert mrh_zone(3) == "PERIPHERAL"
        assert mrh_zone(5) == "BEYOND"

    def test_operational_health(self):
        score = operational_health(0.8, 0.6, 0.7)
        assert abs(score - 0.71) < 0.01

    def test_is_healthy(self):
        assert is_healthy(0.8, 0.6, 0.7)
        assert not is_healthy(0.3, 0.3, 0.3)

    def test_diminishing_returns(self):
        assert diminishing_returns(1) == 1.0
        assert abs(diminishing_returns(2) - 0.8) < TOL
        assert diminishing_returns(0) == 1.0


# ── Cross-language test vectors ──────────────────────────────────


class TestVectors:
    @pytest.fixture
    def vectors(self):
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "test-vectors",
            "t3v3",
            "tensor-operations.json",
        )
        with open(path) as f:
            return json.load(f)["vectors"]

    def _find(self, vectors, vid):
        return next(v for v in vectors if v["id"] == vid)

    def test_t3v3_011_evolution(self, vectors):
        v = self._find(vectors, "t3v3-011")
        t = T3(**v["input"]["initial"])
        outcome = ActionOutcome(v["input"]["outcome"])
        t2 = t.evolve(outcome)
        assert t2.talent == pytest.approx(v["expected"]["talent"], abs=v["tolerance"])
        assert t2.training == pytest.approx(v["expected"]["training"], abs=v["tolerance"])
        assert t2.temperament == pytest.approx(v["expected"]["temperament"], abs=v["tolerance"])

    def test_t3v3_012_decay(self, vectors):
        v = self._find(vectors, "t3v3-012")
        t = T3(**v["input"]["initial"])
        t2 = t.decay(v["input"]["months"])
        assert t2.talent == pytest.approx(v["expected"]["talent"], abs=v["tolerance"])
        assert t2.training == pytest.approx(v["expected"]["training"], abs=v["tolerance"])
        assert t2.temperament == pytest.approx(v["expected"]["temperament"], abs=v["tolerance"])

    def test_t3v3_013_role_requirement(self, vectors):
        v = self._find(vectors, "t3v3-013")
        rr = RoleRequirement(
            v["input"]["role"],
            min_talent=v["input"]["minimums"]["talent"],
            min_training=v["input"]["minimums"]["training"],
            min_temperament=v["input"]["minimums"]["temperament"],
        )
        t = T3(**v["input"]["candidate"])
        result = rr.evaluate(t)
        assert result["qualified"] == v["expected"]["qualified"]
        assert result["trust_score"] == pytest.approx(v["expected"]["trust_score"], abs=v["tolerance"])

    def test_t3v3_014_v3_calculate(self, vectors):
        v = self._find(vectors, "t3v3-014")
        inp = v["input"]
        v3 = V3.calculate(
            atp_earned=inp["atp_earned"],
            atp_expected=inp["atp_expected"],
            recipient_satisfaction=inp["recipient_satisfaction"],
            verified_claims=inp["verified_claims"],
            total_claims=inp["total_claims"],
            witness_confidence=inp["witness_confidence"],
            value_transferred=inp["value_transferred"],
        )
        assert v3.valuation == pytest.approx(v["expected"]["valuation"], abs=v["tolerance"])
        assert v3.veracity == pytest.approx(v["expected"]["veracity"], abs=v["tolerance"])
        assert v3.validity == pytest.approx(v["expected"]["validity"], abs=v["tolerance"])

    def test_t3v3_015_team_composition(self, vectors):
        v = self._find(vectors, "t3v3-015")
        profiles = []
        for m in v["input"]["members"]:
            p = TrustProfile(m["entity_id"])
            p.set_role(v["input"]["role"], t3=T3(**m["t3"]))
            profiles.append(p)
        result = compute_team_t3(profiles, v["input"]["role"])
        assert result is not None
        assert result.talent == pytest.approx(v["expected"]["talent"], abs=v["tolerance"])
        assert result.training == pytest.approx(v["expected"]["training"], abs=v["tolerance"])
        assert result.temperament == pytest.approx(v["expected"]["temperament"], abs=v["tolerance"])


# ── T3/V3 from_dict() round-trip tests ─────────────────────────


class TestT3FromDict:
    """Round-trip tests: T3 -> as_dict() -> from_dict() -> T3."""

    def test_roundtrip_defaults(self):
        t = T3()
        restored = T3.from_dict(t.as_dict())
        assert restored.talent == t.talent
        assert restored.training == t.training
        assert restored.temperament == t.temperament

    def test_roundtrip_custom_values(self):
        t = T3(talent=0.9, training=0.1, temperament=0.75)
        restored = T3.from_dict(t.as_dict())
        assert restored.talent == t.talent
        assert restored.training == t.training
        assert restored.temperament == t.temperament

    def test_roundtrip_boundary_values(self):
        t = T3(talent=0.0, training=1.0, temperament=0.0)
        restored = T3.from_dict(t.as_dict())
        assert restored.talent == 0.0
        assert restored.training == 1.0
        assert restored.temperament == 0.0

    def test_from_dict_missing_keys_uses_defaults(self):
        restored = T3.from_dict({})
        assert restored.talent == 0.5
        assert restored.training == 0.5
        assert restored.temperament == 0.5

    def test_from_dict_ignores_unknown_keys(self):
        d = T3().as_dict()
        d["future_field"] = "something"
        restored = T3.from_dict(d)
        assert restored.talent == 0.5

    def test_roundtrip_composite_preserved(self):
        t = T3(talent=0.8, training=0.6, temperament=0.9)
        restored = T3.from_dict(t.as_dict())
        assert restored.composite == pytest.approx(t.composite, abs=TOL)

    def test_roundtrip_after_evolve(self):
        t = T3(0.7, 0.8, 0.9).evolve(ActionOutcome.NOVEL_SUCCESS)
        restored = T3.from_dict(t.as_dict())
        assert restored.talent == pytest.approx(t.talent, abs=TOL)
        assert restored.training == pytest.approx(t.training, abs=TOL)
        assert restored.temperament == pytest.approx(t.temperament, abs=TOL)

    def test_roundtrip_after_decay(self):
        t = T3(0.5, 0.8, 0.3).decay(6.0)
        restored = T3.from_dict(t.as_dict())
        assert restored.training == pytest.approx(t.training, abs=TOL)
        assert restored.temperament == pytest.approx(t.temperament, abs=TOL)


class TestV3FromDict:
    """Round-trip tests: V3 -> as_dict() -> from_dict() -> V3."""

    def test_roundtrip_defaults(self):
        v = V3()
        restored = V3.from_dict(v.as_dict())
        assert restored.valuation == v.valuation
        assert restored.veracity == v.veracity
        assert restored.validity == v.validity

    def test_roundtrip_custom_values(self):
        v = V3(valuation=0.85, veracity=0.92, validity=0.7)
        restored = V3.from_dict(v.as_dict())
        assert restored.valuation == v.valuation
        assert restored.veracity == v.veracity
        assert restored.validity == v.validity

    def test_roundtrip_boundary_values(self):
        v = V3(valuation=0.0, veracity=1.0, validity=0.0)
        restored = V3.from_dict(v.as_dict())
        assert restored.valuation == 0.0
        assert restored.veracity == 1.0
        assert restored.validity == 0.0

    def test_from_dict_missing_keys_uses_defaults(self):
        restored = V3.from_dict({})
        assert restored.valuation == 0.5
        assert restored.veracity == 0.5
        assert restored.validity == 0.5

    def test_from_dict_ignores_unknown_keys(self):
        d = V3().as_dict()
        d["future_field"] = "something"
        restored = V3.from_dict(d)
        assert restored.valuation == 0.5

    def test_roundtrip_composite_preserved(self):
        v = V3(valuation=0.8, veracity=0.6, validity=0.9)
        restored = V3.from_dict(v.as_dict())
        assert restored.composite == pytest.approx(v.composite, abs=TOL)

    def test_roundtrip_via_calculate(self):
        v = V3.calculate(
            atp_earned=90.0,
            atp_expected=100.0,
            recipient_satisfaction=0.85,
            verified_claims=8,
            total_claims=10,
            witness_confidence=0.9,
            value_transferred=True,
        )
        restored = V3.from_dict(v.as_dict())
        assert restored.valuation == pytest.approx(v.valuation, abs=TOL)
        assert restored.veracity == pytest.approx(v.veracity, abs=TOL)
        assert restored.validity == pytest.approx(v.validity, abs=TOL)


# ── TrustQuery ──────────────────────────────────────────────────


class TestTrustQuery:
    def _make_query(self, **overrides: Any) -> TrustQuery:
        defaults: Dict[str, Any] = {
            "querier": "lct:web4:alice",
            "target_entity": "lct:web4:bob",
            "requested_role": "web4:Surgeon",
            "intended_interaction": "surgical-procedure",
            "atp_stake": 100,
            "validity_period": 3600,
            "signature": "abc123",
        }
        defaults.update(overrides)
        return TrustQuery(**defaults)

    def test_basic_construction(self):
        q = self._make_query()
        assert q.querier == "lct:web4:alice"
        assert q.target_entity == "lct:web4:bob"
        assert q.requested_role == "web4:Surgeon"
        assert q.atp_stake == 100
        assert q.disclosure_level == DisclosureLevel.RANGE

    def test_optional_fields(self):
        q = self._make_query(
            query_justification="Patient requiring surgery",
            disclosure_level=DisclosureLevel.PRECISE,
            timestamp="2025-09-14T12:00:00Z",
        )
        assert q.query_justification == "Patient requiring surgery"
        assert q.disclosure_level == DisclosureLevel.PRECISE
        assert q.timestamp == "2025-09-14T12:00:00Z"

    def test_stake_validation_rejects_below_minimum(self):
        with pytest.raises(ValueError, match="atp_stake must be >= 10"):
            self._make_query(atp_stake=5)

    def test_stake_validation_rejects_zero(self):
        with pytest.raises(ValueError, match="atp_stake must be >= 10"):
            self._make_query(atp_stake=0)

    def test_validity_period_too_short(self):
        with pytest.raises(ValueError, match="validity_period"):
            self._make_query(validity_period=100)

    def test_validity_period_too_long(self):
        with pytest.raises(ValueError, match="validity_period"):
            self._make_query(validity_period=100000)

    def test_roundtrip_to_dict(self):
        q = self._make_query(
            query_justification="Need trust info",
            disclosure_level=DisclosureLevel.PRECISE,
            timestamp="2025-09-14T12:00:00Z",
        )
        d = q.to_dict()
        restored = TrustQuery.from_dict(d)
        assert restored.querier == q.querier
        assert restored.target_entity == q.target_entity
        assert restored.requested_role == q.requested_role
        assert restored.atp_stake == q.atp_stake
        assert restored.validity_period == q.validity_period
        assert restored.query_justification == q.query_justification
        assert restored.disclosure_level == q.disclosure_level
        assert restored.signature == q.signature
        assert restored.timestamp == q.timestamp

    def test_roundtrip_defaults_only(self):
        q = self._make_query()
        d = q.to_dict()
        restored = TrustQuery.from_dict(d)
        assert restored.querier == q.querier
        assert restored.disclosure_level == DisclosureLevel.RANGE
        assert restored.query_justification is None
        assert restored.timestamp is None

    def test_to_dict_structure(self):
        q = self._make_query()
        d = q.to_dict()
        assert "query" in d
        assert "signature" in d
        assert d["query"]["querier"] == "lct:web4:alice"
        assert d["query"]["atp_stake"] == 100
        assert d["signature"] == "abc123"

    def test_to_dict_omits_default_disclosure(self):
        q = self._make_query()
        d = q.to_dict()
        assert "disclosure_level" not in d["query"]

    def test_to_dict_includes_non_default_disclosure(self):
        q = self._make_query(disclosure_level=DisclosureLevel.BINARY)
        d = q.to_dict()
        assert d["query"]["disclosure_level"] == "binary"

    def test_disclosure_level_enum(self):
        assert DisclosureLevel.BINARY.value == "binary"
        assert DisclosureLevel.RANGE.value == "range"
        assert DisclosureLevel.PRECISE.value == "precise"

    def test_jsonld_roundtrip(self):
        q = self._make_query(
            query_justification="Need trust info",
            disclosure_level=DisclosureLevel.PRECISE,
            timestamp="2025-09-14T12:00:00Z",
        )
        doc = q.to_jsonld()
        assert doc["@type"] == "TrustQuery"
        assert "@context" in doc
        restored = TrustQuery.from_jsonld(doc)
        assert restored.querier == q.querier
        assert restored.atp_stake == q.atp_stake
        assert restored.disclosure_level == q.disclosure_level

    def test_jsonld_string_roundtrip(self):
        q = self._make_query()
        s = q.to_jsonld_string()
        restored = TrustQuery.from_jsonld_string(s)
        assert restored.querier == q.querier
        assert restored.atp_stake == q.atp_stake

    def test_jsonld_dispatcher(self):
        from web4.deserialize import from_jsonld

        q = self._make_query()
        doc = q.to_jsonld()
        obj = from_jsonld(doc)
        assert isinstance(obj, TrustQuery)
        assert obj.querier == q.querier


class TestTrustQueryResponse:
    def test_approved_response(self):
        r = TrustQueryResponse(
            status="APPROVED",
            entity="lct:web4:bob",
            role="web4:Surgeon",
            t3_in_role=T3(0.95, 0.92, 0.88),
            validity_until="2025-09-14T13:00:00Z",
            stake_locked=100,
            commitment="Must engage within 3600 seconds",
        )
        assert r.is_approved
        assert r.t3_in_role is not None
        assert r.t3_in_role.talent == 0.95

    def test_rejected_response(self):
        r = TrustQueryResponse(
            status="REJECTED",
            error_code="INSUFFICIENT_STAKE",
            error_message="Trust queries require minimum ATP stake",
            minimum_required=10,
            provided=0,
        )
        assert not r.is_approved
        assert r.error_code == "INSUFFICIENT_STAKE"

    def test_approved_roundtrip(self):
        r = TrustQueryResponse(
            status="APPROVED",
            entity="lct:web4:bob",
            role="web4:Surgeon",
            t3_in_role=T3(0.95, 0.92, 0.88),
            stake_locked=100,
            audit_log={"query_id": "query:web4:1"},
        )
        d = r.to_dict()
        restored = TrustQueryResponse.from_dict(d)
        assert restored.status == "APPROVED"
        assert restored.entity == "lct:web4:bob"
        assert restored.t3_in_role is not None
        assert restored.t3_in_role.talent == pytest.approx(0.95, abs=TOL)
        assert restored.stake_locked == 100
        assert restored.audit_log == {"query_id": "query:web4:1"}

    def test_rejected_roundtrip(self):
        r = TrustQueryResponse(
            status="REJECTED",
            error_code="INSUFFICIENT_STAKE",
            error_message="Trust queries require minimum ATP stake",
            minimum_required=10,
            provided=0,
        )
        d = r.to_dict()
        restored = TrustQueryResponse.from_dict(d)
        assert restored.status == "REJECTED"
        assert restored.error_code == "INSUFFICIENT_STAKE"
        assert restored.minimum_required == 10
        assert restored.provided == 0

    def test_to_dict_approved_structure(self):
        r = TrustQueryResponse(
            status="APPROVED",
            entity="lct:web4:bob",
            role="web4:Surgeon",
            t3_in_role=T3(0.95, 0.92, 0.88),
        )
        d = r.to_dict()
        assert d["status"] == "APPROVED"
        assert "response" in d
        assert "error" not in d
        assert d["response"]["entity"] == "lct:web4:bob"
        assert d["response"]["t3_in_role"]["talent"] == 0.95

    def test_to_dict_rejected_structure(self):
        r = TrustQueryResponse(
            status="REJECTED",
            error_code="INSUFFICIENT_STAKE",
        )
        d = r.to_dict()
        assert d["status"] == "REJECTED"
        assert "error" in d
        assert "response" not in d


# ── Trust Query Test Vectors ────────────────────────────────────


class TestTrustQueryVectors:
    """Exercise the 2 trust-query test vectors."""

    @pytest.fixture
    def valid_vector(self) -> Dict[str, Any]:
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "test-vectors",
            "trust-query",
            "valid-staked-query.json",
        )
        with open(path) as f:
            return json.load(f)

    @pytest.fixture
    def invalid_vector(self) -> Dict[str, Any]:
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "test-vectors",
            "trust-query",
            "invalid-no-stake.json",
        )
        with open(path) as f:
            return json.load(f)

    def test_valid_query_constructs(self, valid_vector: Dict[str, Any]):
        inp = valid_vector["input"]
        q = TrustQuery(
            querier=inp["query"]["querier"],
            target_entity=inp["query"]["target_entity"],
            requested_role=inp["query"]["requested_role"],
            intended_interaction=inp["query"]["intended_interaction"],
            atp_stake=inp["query"]["atp_stake"],
            validity_period=inp["query"]["validity_period"],
            query_justification=inp["query"].get("query_justification"),
            disclosure_level=DisclosureLevel(inp["query"].get("disclosure_level", "range")),
            signature="test-sig",
            timestamp=inp.get("timestamp"),
        )
        assert q.querier == "lct:web4:alice"
        assert q.atp_stake == 100
        assert valid_vector["should_succeed"] is True

    def test_valid_response_constructs(self, valid_vector: Dict[str, Any]):
        exp = valid_vector["expected_output"]
        resp = TrustQueryResponse(
            status=exp["status"],
            entity=exp["response"]["entity"],
            role=exp["response"]["role"],
            t3_in_role=T3(**exp["response"]["t3_in_role"]),
            validity_until=exp["response"]["validity_until"],
            stake_locked=exp["response"]["stake_locked"],
            commitment=exp["response"]["commitment"],
            audit_log=exp.get("audit_log"),
        )
        assert resp.is_approved
        assert resp.t3_in_role is not None
        assert resp.t3_in_role.talent == 0.95

    def test_invalid_query_rejected_for_zero_stake(self, invalid_vector: Dict[str, Any]):
        inp = invalid_vector["input"]
        with pytest.raises(ValueError, match="atp_stake must be >= 10"):
            TrustQuery(
                querier=inp["query"]["querier"],
                target_entity=inp["query"]["target_entity"],
                requested_role=inp["query"]["requested_role"],
                intended_interaction=inp["query"]["intended_interaction"],
                atp_stake=inp["query"]["atp_stake"],
                validity_period=inp["query"]["validity_period"],
                signature="test-sig",
            )
        assert invalid_vector["should_succeed"] is False

    def test_invalid_response_constructs(self, invalid_vector: Dict[str, Any]):
        exp = invalid_vector["expected_output"]
        resp = TrustQueryResponse(
            status=exp["status"],
            error_code=exp["error"]["code"],
            error_message=exp["error"]["message"],
            minimum_required=exp["error"]["minimum_required"],
            provided=exp["error"]["provided"],
        )
        assert not resp.is_approved
        assert resp.error_code == "INSUFFICIENT_STAKE"
        assert resp.minimum_required == 10


# ── TrustQuery JSON-LD ─────────────────────────────────────────


class TestTrustQueryJsonLd:
    """Tests for TrustQuery to_jsonld/from_jsonld round-trip."""

    def _make_query(self, **overrides: Any) -> TrustQuery:
        defaults: Dict[str, Any] = {
            "querier": "lct:web4:alice",
            "target_entity": "lct:web4:bob",
            "requested_role": "web4:Surgeon",
            "intended_interaction": "surgical-procedure",
            "atp_stake": 100,
            "validity_period": 3600,
            "signature": "abc123",
        }
        defaults.update(overrides)
        return TrustQuery(**defaults)

    def test_to_jsonld_has_type_and_context(self):
        q = self._make_query()
        doc = q.to_jsonld()
        assert doc["@type"] == "TrustQuery"
        assert "@context" in doc
        assert "https://web4.io/contexts/trust-query.jsonld" in doc["@context"]

    def test_to_jsonld_preserves_query_structure(self):
        q = self._make_query(
            query_justification="Need trust info",
            disclosure_level=DisclosureLevel.PRECISE,
            timestamp="2025-09-14T12:00:00Z",
        )
        doc = q.to_jsonld()
        assert doc["query"]["querier"] == "lct:web4:alice"
        assert doc["query"]["atp_stake"] == 100
        assert doc["query"]["query_justification"] == "Need trust info"
        assert doc["query"]["disclosure_level"] == "precise"
        assert doc["signature"] == "abc123"
        assert doc["timestamp"] == "2025-09-14T12:00:00Z"

    def test_jsonld_roundtrip(self):
        q = self._make_query(
            query_justification="Patient needs surgery",
            disclosure_level=DisclosureLevel.PRECISE,
            timestamp="2025-09-14T12:00:00Z",
        )
        doc = q.to_jsonld()
        restored = TrustQuery.from_jsonld(doc)
        assert restored.querier == q.querier
        assert restored.target_entity == q.target_entity
        assert restored.requested_role == q.requested_role
        assert restored.atp_stake == q.atp_stake
        assert restored.validity_period == q.validity_period
        assert restored.query_justification == q.query_justification
        assert restored.disclosure_level == q.disclosure_level
        assert restored.signature == q.signature
        assert restored.timestamp == q.timestamp

    def test_jsonld_roundtrip_defaults(self):
        q = self._make_query()
        doc = q.to_jsonld()
        restored = TrustQuery.from_jsonld(doc)
        assert restored.querier == q.querier
        assert restored.disclosure_level == DisclosureLevel.RANGE
        assert restored.query_justification is None

    def test_jsonld_string_roundtrip(self):
        q = self._make_query(timestamp="2025-09-14T12:00:00Z")
        s = q.to_jsonld_string()
        restored = TrustQuery.from_jsonld_string(s)
        assert restored.querier == q.querier
        assert restored.atp_stake == q.atp_stake

    def test_generic_dispatcher_roundtrip(self):
        """TrustQuery.to_jsonld() output is accepted by the generic from_jsonld()."""
        from web4.deserialize import from_jsonld

        q = self._make_query(timestamp="2025-09-14T12:00:00Z")
        doc = q.to_jsonld()
        obj = from_jsonld(doc)
        assert isinstance(obj, TrustQuery)
        assert obj.querier == "lct:web4:alice"
        assert obj.atp_stake == 100

    def test_schema_validation_with_to_dict(self):
        """to_dict() output validates against trust-query.schema.json."""
        from web4.validation import validate

        q = self._make_query(
            query_justification="Testing",
            disclosure_level=DisclosureLevel.PRECISE,
            timestamp="2025-09-14T12:00:00Z",
        )
        d = q.to_dict()
        result = validate(d, "trust-query")
        assert result.valid, f"Validation failed: {result.errors}"
