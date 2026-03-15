"""
Test web4 SDK against canonical test vectors.

Test vectors: web4-standard/test-vectors/
These vectors define cross-language interop requirements — all implementations
MUST produce identical results.
"""

import json
import os
import pytest

from web4.trust import (
    T3, V3, TrustProfile,
    trust_bridge, mrh_trust_decay, mrh_zone,
    operational_health, is_healthy, diminishing_returns,
)
from web4.atp import (
    ATPAccount, transfer, sliding_scale,
    check_conservation, energy_ratio, sybil_cost,
)
from web4.lct import LCT, EntityType, RevocationStatus

# ── Helpers ──────────────────────────────────────────────────────

VECTORS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "test-vectors")


def load_vectors(path: str) -> dict:
    full_path = os.path.join(VECTORS_DIR, path)
    with open(full_path) as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════════
#  T3/V3 TENSOR TESTS (from tensor-operations.json)
# ══════════════════════════════════════════════════════════════════

class TestT3V3Vectors:
    """Tests against t3v3/tensor-operations.json vectors."""

    @classmethod
    def setup_class(cls):
        cls.vectors = load_vectors("t3v3/tensor-operations.json")["vectors"]

    def _vec(self, vec_id: str) -> dict:
        return next(v for v in self.vectors if v["id"] == vec_id)

    # t3v3-001: T3 composite
    def test_t3_composite(self):
        v = self._vec("t3v3-001")
        inp = v["input"]
        t3 = T3(talent=inp["talent"], training=inp["training"], temperament=inp["temperament"])
        assert abs(t3.composite - v["expected"]["composite"]) < v["tolerance"]

    # t3v3-002: V3 composite
    def test_v3_composite(self):
        v = self._vec("t3v3-002")
        inp = v["input"]
        v3 = V3(valuation=inp["valuation"], veracity=inp["veracity"], validity=inp["validity"])
        assert abs(v3.composite - v["expected"]["composite"]) < v["tolerance"]

    # t3v3-003: T3 update from successful action
    def test_t3_update_success(self):
        v = self._vec("t3v3-003")
        inp = v["input"]
        initial = T3(**inp["initial"])
        updated = initial.update(quality=inp["quality"], success=inp["success"])

        expected = v["expected"]
        assert abs(updated.talent - expected["talent"]) < v["tolerance"]
        assert abs(updated.training - expected["training"]) < v["tolerance"]
        assert abs(updated.temperament - expected["temperament"]) < v["tolerance"]

    # t3v3-004: T3 update from failed action
    def test_t3_update_failure(self):
        v = self._vec("t3v3-004")
        inp = v["input"]
        initial = T3(**inp["initial"])
        updated = initial.update(quality=inp["quality"], success=inp["success"])

        expected = v["expected"]
        assert abs(updated.talent - expected["talent"]) < v["tolerance"]
        assert abs(updated.training - expected["training"]) < v["tolerance"]
        assert abs(updated.temperament - expected["temperament"]) < v["tolerance"]

    # t3v3-005: Lower boundary clamping
    def test_t3_clamp_lower(self):
        v = self._vec("t3v3-005")
        inp = v["input"]
        initial = T3(**inp["initial"])
        updated = initial.update(quality=inp["quality"], success=inp["success"])
        assert updated.talent >= 0.0
        assert updated.training >= 0.0
        assert updated.temperament >= 0.0

    # t3v3-006: Upper boundary clamping
    def test_t3_clamp_upper(self):
        v = self._vec("t3v3-006")
        inp = v["input"]
        initial = T3(**inp["initial"])
        updated = initial.update(quality=inp["quality"], success=inp["success"])
        assert updated.talent <= 1.0
        assert updated.training <= 1.0
        assert updated.temperament <= 1.0

    # t3v3-007: Diminishing returns
    def test_diminishing_returns(self):
        v = self._vec("t3v3-007")
        inp = v["input"]
        expected_factors = v["expected"]["factors"]
        for i, expected in enumerate(expected_factors):
            actual = diminishing_returns(i + 1, inp["base_factor"])
            assert abs(actual - expected) < v["tolerance"], f"repeat {i+1}: {actual} != {expected}"

    # t3v3-008: Trust bridge (6-dim → 3-dim)
    def test_trust_bridge(self):
        v = self._vec("t3v3-008")
        inp = v["input"]["six_dim"]
        result = trust_bridge(**inp)
        expected = v["expected"]
        assert abs(result.talent - expected["talent"]) < v["tolerance"]
        assert abs(result.training - expected["training"]) < v["tolerance"]
        assert abs(result.temperament - expected["temperament"]) < v["tolerance"]

    # t3v3-009: MRH trust decay
    def test_mrh_decay(self):
        v = self._vec("t3v3-009")
        inp = v["input"]
        expected_trusts = v["expected"]["trust_per_hop"]
        expected_zones = v["expected"]["zones"]

        for hop, (exp_trust, exp_zone) in zip(inp["hops"], zip(expected_trusts, expected_zones)):
            actual_trust = mrh_trust_decay(inp["base_trust"], hop, inp["decay_factor"])
            actual_zone = mrh_zone(hop)
            assert abs(actual_trust - exp_trust) < v["tolerance"], f"hop {hop}: trust {actual_trust} != {exp_trust}"
            assert actual_zone == exp_zone, f"hop {hop}: zone {actual_zone} != {exp_zone}"

    # t3v3-010: Operational health (formerly "coherence" — renamed to avoid collision
    # with whitepaper's identity coherence C×S×Phi×R)
    def test_operational_health(self):
        v = self._vec("t3v3-010")
        inp = v["input"]
        h = operational_health(inp["t3_composite"], inp["v3_composite"], inp["energy_ratio"])
        expected = v["expected"]
        assert abs(h - expected["coherence"]) < v["tolerance"]
        assert is_healthy(inp["t3_composite"], inp["v3_composite"], inp["energy_ratio"]) == expected["above_threshold"]


# ══════════════════════════════════════════════════════════════════
#  ATP TESTS (from transfer-operations.json)
# ══════════════════════════════════════════════════════════════════

class TestATPVectors:
    """Tests against atp/transfer-operations.json vectors."""

    @classmethod
    def setup_class(cls):
        cls.vectors = load_vectors("atp/transfer-operations.json")["vectors"]

    def _vec(self, vec_id: str) -> dict:
        return next(v for v in self.vectors if v["id"] == vec_id)

    # atp-001: Basic transfer with 5% fee
    def test_basic_transfer(self):
        v = self._vec("atp-001")
        inp = v["input"]
        sender = ATPAccount(available=inp["sender_balance"])
        receiver = ATPAccount(available=inp["receiver_balance"])
        result = transfer(sender, receiver, inp["amount"], inp["fee_rate"])

        expected = v["expected"]
        tol = v["tolerance"]
        assert abs(result.fee - expected["fee"]) < tol
        assert abs(result.sender_balance - expected["sender_balance"]) < tol
        assert abs(result.receiver_balance - expected["receiver_balance"]) < tol

    # atp-002: Transfer with cap and overflow
    def test_transfer_capped(self):
        v = self._vec("atp-002")
        inp = v["input"]
        sender = ATPAccount(available=inp["sender_balance"])
        receiver = ATPAccount(available=inp["receiver_balance"])
        result = transfer(sender, receiver, inp["amount"], inp["fee_rate"], inp["max_balance"])

        expected = v["expected"]
        tol = v["tolerance"]
        assert abs(result.fee - expected["fee"]) < tol
        assert abs(result.actual_credit - expected["actual_credit"]) < tol
        assert abs(result.overflow - expected["overflow"]) < tol
        assert abs(result.sender_balance - expected["sender_balance"]) < tol
        assert abs(result.receiver_balance - expected["receiver_balance"]) < tol

    # atp-003: Transfer to full receiver
    def test_transfer_full_receiver(self):
        v = self._vec("atp-003")
        inp = v["input"]
        sender = ATPAccount(available=inp["sender_balance"])
        receiver = ATPAccount(available=inp["receiver_balance"])
        result = transfer(sender, receiver, inp["amount"], inp["fee_rate"], inp["max_balance"])

        expected = v["expected"]
        tol = v["tolerance"]
        assert abs(result.fee - expected["fee"]) < tol
        assert abs(result.actual_credit - expected["actual_credit"]) < tol
        assert abs(result.overflow - expected["overflow"]) < tol
        assert abs(result.sender_balance - expected["sender_balance"]) < tol
        assert abs(result.receiver_balance - expected["receiver_balance"]) < tol

    # atp-004: Conservation invariant
    def test_conservation(self):
        v = self._vec("atp-004")
        inp = v["input"]
        balances = list(inp["initial_balances"])
        accounts = [ATPAccount(available=b) for b in balances]
        total_fees = 0.0

        for t in inp["transfers"]:
            result = transfer(accounts[t["from"]], accounts[t["to"]], t["amount"], inp["fee_rate"])
            total_fees += result.fee

        final_balances = [a.available for a in accounts]
        expected = v["expected"]
        tol = v["tolerance"]

        assert abs(total_fees - expected["total_fees"]) < tol
        assert abs(sum(final_balances) - expected["final_total"]) < tol
        assert check_conservation(
            inp["initial_balances"], final_balances, total_fees, tol
        )

    # atp-005 through atp-007: Sliding scale
    def test_sliding_scale_below(self):
        v = self._vec("atp-005")
        inp = v["input"]
        p = sliding_scale(inp["quality"], inp["base_payment"], inp["zero_threshold"], inp["full_threshold"])
        assert abs(p - v["expected"]["payment"]) < v["tolerance"]

    def test_sliding_scale_ramp(self):
        v = self._vec("atp-006")
        inp = v["input"]
        p = sliding_scale(inp["quality"], inp["base_payment"], inp["zero_threshold"], inp["full_threshold"])
        assert abs(p - v["expected"]["payment"]) < v["tolerance"]

    def test_sliding_scale_above(self):
        v = self._vec("atp-007")
        inp = v["input"]
        p = sliding_scale(inp["quality"], inp["base_payment"], inp["zero_threshold"], inp["full_threshold"])
        assert abs(p - v["expected"]["payment"]) < v["tolerance"]

    # atp-008: Lock-commit-rollback lifecycle
    def test_lock_lifecycle(self):
        v = self._vec("atp-008")
        inp = v["input"]
        expected = v["expected"]
        tol = v["tolerance"]

        acct = ATPAccount(available=inp["initial_balance"])

        # Lock
        assert acct.lock(inp["lock_amount"])
        assert abs(acct.available - expected["after_lock"]["available"]) < tol
        assert abs(acct.locked - expected["after_lock"]["locked"]) < tol
        assert abs(acct.total - expected["after_lock"]["total"]) < tol

        # Commit path
        acct_commit = ATPAccount(available=acct.available, locked=acct.locked)
        acct_commit.commit(inp["lock_amount"])
        assert abs(acct_commit.available - expected["after_commit"]["available"]) < tol
        assert abs(acct_commit.locked - expected["after_commit"]["locked"]) < tol
        assert abs(acct_commit.total - expected["after_commit"]["total"]) < tol

        # Rollback path (from locked state, not committed)
        acct_rb = ATPAccount(available=acct.available, locked=acct.locked)
        acct_rb.rollback(inp["lock_amount"])
        assert abs(acct_rb.available - expected["after_rollback_instead"]["available"]) < tol
        assert abs(acct_rb.locked - expected["after_rollback_instead"]["locked"]) < tol
        assert abs(acct_rb.total - expected["after_rollback_instead"]["total"]) < tol

    # atp-009: Recharge
    def test_recharge(self):
        v = self._vec("atp-009")
        inp = v["input"]
        expected = v["expected"]
        tol = v["tolerance"]

        acct = ATPAccount(available=inp["current_balance"], initial_balance=inp["initial_balance"])
        actual = acct.recharge(rate=inp["recharge_rate"], max_multiplier=inp["max_recharge_multiplier"])
        assert abs(actual - expected["recharge_amount"]) < tol
        assert abs(acct.available - expected["new_balance"]) < tol

    # atp-010: Recharge at cap
    def test_recharge_capped(self):
        v = self._vec("atp-010")
        inp = v["input"]
        expected = v["expected"]
        tol = v["tolerance"]

        acct = ATPAccount(available=inp["current_balance"], initial_balance=inp["initial_balance"])
        actual = acct.recharge(rate=inp["recharge_rate"], max_multiplier=inp["max_recharge_multiplier"])
        assert abs(actual - expected["recharge_amount"]) < tol
        assert abs(acct.available - expected["new_balance"]) < tol

    # atp-011: Sybil cost
    def test_sybil_cost(self):
        v = self._vec("atp-011")
        inp = v["input"]
        expected = v["expected"]
        tol = v["tolerance"]

        result = sybil_cost(
            inp["num_identities"], inp["hardware_cost_per_identity"],
            inp["atp_stake_per_identity"], inp["transfer_fee_rate"],
        )
        assert abs(result["total_setup_cost"] - expected["total_setup_cost"]) < tol
        assert abs(result["per_identity_cost"] - expected["per_identity_cost"]) < tol
        assert abs(result["circular_flow_loss_per_cycle"] - expected["circular_flow_loss_per_cycle"]) < tol

    # atp-012: Energy ratio
    def test_energy_ratio(self):
        v = self._vec("atp-012")
        inp = v["input"]
        expected = v["expected"]
        tol = v["tolerance"]
        assert abs(energy_ratio(inp["atp_balance"], inp["adp_accumulated"]) - expected["energy_ratio"]) < tol

    # atp-013: Energy ratio edge cases
    def test_energy_ratio_edges(self):
        v = self._vec("atp-013")
        cases = v["input"]["cases"]
        expected_ratios = v["expected"]["ratios"]
        tol = v["tolerance"]
        for case, expected in zip(cases, expected_ratios):
            actual = energy_ratio(case["atp"], case["adp"])
            assert abs(actual - expected) < tol, f"atp={case['atp']}, adp={case['adp']}: {actual} != {expected}"

    # atp-015: Quality-based settlement
    def test_settlement(self):
        v = self._vec("atp-015")
        inp = v["input"]
        expected_payments = v["expected"]["payments"]
        tol = v["tolerance"]
        for quality, expected in zip(inp["quality_scores"], expected_payments):
            actual = sliding_scale(quality, inp["task_payment"], inp["zero_threshold"], inp["full_threshold"])
            assert abs(actual - expected) < tol, f"quality={quality}: {actual} != {expected}"


# ══════════════════════════════════════════════════════════════════
#  LCT TESTS
# ══════════════════════════════════════════════════════════════════

class TestLCT:
    """Tests for LCT creation and operations."""

    def test_create_basic(self):
        lct = LCT.create(
            entity_type=EntityType.AI,
            public_key="mb64testkey",
            society="lct:web4:society-genesis",
            context="platform",
            witnesses=["lct:web4:witness-w1", "lct:web4:witness-w2"],
            timestamp="2026-02-19T00:00:00Z",
        )
        assert lct.is_active
        assert lct.binding.entity_type == EntityType.AI
        assert lct.binding.public_key == "mb64testkey"
        assert lct.lct_id.startswith("lct:web4:ai:")

    def test_birth_certificate(self):
        lct = LCT.create(
            entity_type=EntityType.HUMAN,
            public_key="testkey",
            context="platform",
            witnesses=["w1", "w2", "w3"],
        )
        assert lct.birth_certificate is not None
        assert lct.birth_certificate.citizen_role == "lct:web4:role:citizen:platform"
        assert len(lct.birth_certificate.birth_witnesses) == 3

    def test_first_pairing_is_citizen_role(self):
        """First pairing MUST be citizen role (per spec)."""
        lct = LCT.create(entity_type=EntityType.AI, public_key="k", context="platform")
        assert len(lct.mrh.paired) == 1
        assert lct.mrh.paired[0].pairing_type == "birth_certificate"
        assert lct.mrh.paired[0].permanent is True
        assert lct.mrh.paired[0].lct_id == "lct:web4:role:citizen:platform"

    def test_default_t3v3(self):
        """New LCT starts with default T3/V3 (0.5, 0.5, 0.5)."""
        lct = LCT.create(entity_type=EntityType.AI, public_key="k")
        assert lct.t3.talent == 0.5
        assert lct.t3.training == 0.5
        assert lct.t3.temperament == 0.5
        assert abs(lct.t3.composite - 0.5) < 0.001

    def test_revocation(self):
        lct = LCT.create(entity_type=EntityType.AI, public_key="k")
        assert lct.is_active
        lct.revoke()
        assert not lct.is_active
        assert lct.revocation_status == RevocationStatus.REVOKED

    def test_add_pairing(self):
        lct = LCT.create(entity_type=EntityType.AI, public_key="k")
        lct.add_pairing("lct:web4:service:foo", "operational")
        assert len(lct.mrh.paired) == 2

    def test_add_witness(self):
        lct = LCT.create(entity_type=EntityType.AI, public_key="k")
        lct.add_witness("lct:web4:witness:alice")
        assert "lct:web4:witness:alice" in lct.mrh.witnessing
        # Idempotent
        lct.add_witness("lct:web4:witness:alice")
        assert lct.mrh.witnessing.count("lct:web4:witness:alice") == 1

    def test_canonical_hash_deterministic(self):
        """Same inputs → same hash."""
        kwargs = dict(
            entity_type=EntityType.AI, public_key="mb64testkey",
            society="lct:web4:society-genesis", context="platform",
            witnesses=["w1", "w2", "w3"], timestamp="2026-02-19T00:00:00Z",
            lct_id="lct:web4:ai:test", subject="did:web4:key:test",
        )
        lct1 = LCT.create(**kwargs)
        lct2 = LCT.create(**kwargs)
        assert lct1.canonical_hash() == lct2.canonical_hash()

    def test_to_dict(self):
        lct = LCT.create(
            entity_type=EntityType.AI, public_key="k",
            lct_id="lct:test", subject="did:test",
        )
        d = lct.to_dict()
        assert d["lct_id"] == "lct:test"
        assert d["binding"]["entity_type"] == "ai"
        assert "t3_tensor" in d
        assert "v3_tensor" in d

    def test_entity_types(self):
        """All 15 entity types from spec are present."""
        assert len(EntityType) == 15
        assert EntityType.HUMAN.value == "human"
        assert EntityType.POLICY.value == "policy"
        assert EntityType.INFRASTRUCTURE.value == "infrastructure"


# ══════════════════════════════════════════════════════════════════
#  TRUST PROFILE TESTS
# ══════════════════════════════════════════════════════════════════

class TestTrustProfile:
    """Tests for role-contextual trust profiles."""

    def test_role_isolation(self):
        """T3 in one role has no effect on another."""
        profile = TrustProfile("lct:alice")
        profile.set_role("web4:DataAnalyst", t3=T3(0.85, 0.90, 0.95))
        profile.set_role("web4:Mechanic", t3=T3(0.20, 0.15, 0.50))

        analyst = profile.get_t3("web4:DataAnalyst")
        mechanic = profile.get_t3("web4:Mechanic")
        assert analyst.talent == 0.85
        assert mechanic.talent == 0.20
        assert analyst.composite != mechanic.composite

    def test_unknown_role_returns_default(self):
        profile = TrustProfile("lct:bob")
        t3 = profile.get_t3("web4:UnknownRole")
        assert t3.talent == 0.5
        assert t3.training == 0.5

    def test_roles_list(self):
        profile = TrustProfile("lct:carol")
        profile.set_role("role:A", t3=T3())
        profile.set_role("role:B", t3=T3())
        assert set(profile.roles) == {"role:A", "role:B"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
