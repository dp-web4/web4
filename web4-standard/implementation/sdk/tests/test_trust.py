"""Tests for web4.trust — T3/V3 tensor enhancements (U10).

Covers: outcome-based evolution, decay/refresh, role requirements,
V3 calculation, team tensor composition, plus existing functionality.
"""

import json
import os
import pytest

from web4.trust import (
    T3, V3, ActionOutcome, OUTCOME_DELTAS,
    TRAINING_DECAY_PER_MONTH, TEMPERAMENT_RECOVERY_PER_MONTH,
    RoleRequirement, RoleTensors, TrustProfile,
    compute_team_t3, trust_bridge, mrh_trust_decay, mrh_zone,
    operational_health, is_healthy, diminishing_returns,
    T3_WEIGHTS, V3_WEIGHTS, HEALTH_THRESHOLD,
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
            atp_earned=50, atp_expected=55,
            recipient_satisfaction=0.95,
            verified_claims=9, total_claims=10,
            witness_confidence=0.9,
            value_transferred=True,
        )
        assert v.valuation == pytest.approx(50 / 55 * 0.95, abs=TOL)
        assert v.veracity == pytest.approx(9 / 10 * 0.9, abs=TOL)
        assert v.validity == 1.0

    def test_value_not_transferred(self):
        v = V3.calculate(
            atp_earned=50, atp_expected=55,
            recipient_satisfaction=0.95,
            verified_claims=9, total_claims=10,
            witness_confidence=0.9,
            value_transferred=False,
        )
        assert v.validity == 0.0

    def test_zero_expected_atp(self):
        v = V3.calculate(
            atp_earned=10, atp_expected=0,
            recipient_satisfaction=0.5,
            verified_claims=5, total_claims=10,
            witness_confidence=0.8,
            value_transferred=True,
        )
        assert v.valuation == 0.0

    def test_zero_total_claims(self):
        v = V3.calculate(
            atp_earned=10, atp_expected=20,
            recipient_satisfaction=0.5,
            verified_claims=0, total_claims=0,
            witness_confidence=0.8,
            value_transferred=True,
        )
        assert v.veracity == 0.0

    def test_clamped_valuation(self):
        v = V3.calculate(
            atp_earned=100, atp_expected=50,
            recipient_satisfaction=1.0,
            verified_claims=10, total_claims=10,
            witness_confidence=1.0,
            value_transferred=True,
        )
        # 100/50 * 1.0 = 2.0, clamped to 1.0
        assert v.valuation == 1.0

    def test_perfect_action(self):
        v = V3.calculate(
            atp_earned=100, atp_expected=100,
            recipient_satisfaction=1.0,
            verified_claims=10, total_claims=10,
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
            "..", "..", "..",
            "test-vectors", "t3v3", "tensor-operations.json",
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
