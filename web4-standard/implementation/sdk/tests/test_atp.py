"""
Tests for web4.atp — ATP/ADP Value Cycle core operations.

Tests all public functions and classes in the ATP module:
- ATPAccount: construction, lock/commit/rollback, recharge, properties
- TransferResult: construction
- transfer(): basic, capped, overflow, insufficient balance
- sliding_scale(): below/in-ramp/above threshold
- check_conservation(): valid and violated
- energy_ratio(): standalone function edge cases
- sybil_cost(): cost analysis
- fee_sensitivity(): sweep calculation

Cross-language test vectors validated from:
  web4-standard/test-vectors/atp/transfer-operations.json
"""

import json
import os
import pytest

from web4.atp import (
    ATPAccount,
    TransferResult,
    transfer,
    sliding_scale,
    check_conservation,
    energy_ratio,
    sybil_cost,
    fee_sensitivity,
)


# ── Helpers ──────────────────────────────────────────────────────

VECTORS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "test-vectors")


def load_vectors(filename):
    path = os.path.join(VECTORS_DIR, "atp", filename)
    with open(path) as f:
        return json.load(f)["vectors"]


# ── ATPAccount Construction ──────────────────────────────────────


class TestATPAccountConstruction:
    """ATPAccount defaults and initialization."""

    def test_default_account(self):
        acct = ATPAccount()
        assert acct.available == 0.0
        assert acct.locked == 0.0
        assert acct.adp == 0.0
        assert acct.initial_balance == 0.0

    def test_funded_account(self):
        acct = ATPAccount(available=100.0)
        assert acct.available == 100.0
        assert acct.initial_balance == 100.0  # auto-set from available

    def test_explicit_initial_balance(self):
        acct = ATPAccount(available=50.0, initial_balance=100.0)
        assert acct.available == 50.0
        assert acct.initial_balance == 100.0  # explicit, not overwritten

    def test_total_property(self):
        acct = ATPAccount(available=70.0, locked=30.0)
        assert acct.total == 100.0

    def test_total_excludes_adp(self):
        acct = ATPAccount(available=70.0, locked=30.0, adp=50.0)
        assert acct.total == 100.0  # adp not counted in total


# ── ATPAccount Energy Ratio ──────────────────────────────────────


class TestATPAccountEnergyRatio:
    """ATPAccount.energy_ratio property."""

    def test_pure_atp(self):
        acct = ATPAccount(available=100.0)
        assert acct.energy_ratio == 1.0

    def test_pure_adp(self):
        acct = ATPAccount(available=0.0, adp=100.0)
        assert acct.energy_ratio == 0.0

    def test_zero_zero(self):
        acct = ATPAccount()
        assert acct.energy_ratio == 0.5  # 0/0 → neutral

    def test_mixed(self):
        acct = ATPAccount(available=80.0, adp=20.0)
        assert acct.energy_ratio == pytest.approx(0.8)

    def test_equal_split(self):
        acct = ATPAccount(available=50.0, adp=50.0)
        assert acct.energy_ratio == pytest.approx(0.5)

    def test_locked_counts_as_atp(self):
        acct = ATPAccount(available=40.0, locked=40.0, adp=20.0)
        # total ATP = 80, adp = 20, ratio = 80/100 = 0.8
        assert acct.energy_ratio == pytest.approx(0.8)


# ── ATPAccount Lock/Commit/Rollback ─────────────────────────────


class TestATPAccountLockLifecycle:
    """ATPAccount.lock(), commit(), rollback()."""

    def test_lock_success(self):
        acct = ATPAccount(available=100.0)
        result = acct.lock(30.0)
        assert result is True
        assert acct.available == 70.0
        assert acct.locked == 30.0
        assert acct.total == 100.0  # conserved

    def test_lock_insufficient(self):
        acct = ATPAccount(available=20.0)
        result = acct.lock(30.0)
        assert result is False
        assert acct.available == 20.0  # unchanged
        assert acct.locked == 0.0

    def test_lock_exact_balance(self):
        acct = ATPAccount(available=50.0)
        result = acct.lock(50.0)
        assert result is True
        assert acct.available == 0.0
        assert acct.locked == 50.0

    def test_commit_full(self):
        acct = ATPAccount(available=70.0, locked=30.0)
        committed = acct.commit(30.0)
        assert committed == 30.0
        assert acct.locked == 0.0
        assert acct.adp == 30.0
        assert acct.available == 70.0

    def test_commit_partial(self):
        acct = ATPAccount(available=70.0, locked=30.0)
        committed = acct.commit(20.0)
        assert committed == 20.0
        assert acct.locked == 10.0
        assert acct.adp == 20.0

    def test_commit_more_than_locked(self):
        acct = ATPAccount(available=70.0, locked=30.0)
        committed = acct.commit(50.0)
        assert committed == 30.0  # capped at locked
        assert acct.locked == 0.0
        assert acct.adp == 30.0

    def test_rollback_full(self):
        acct = ATPAccount(available=70.0, locked=30.0)
        rolled = acct.rollback(30.0)
        assert rolled == 30.0
        assert acct.locked == 0.0
        assert acct.available == 100.0

    def test_rollback_partial(self):
        acct = ATPAccount(available=70.0, locked=30.0)
        rolled = acct.rollback(10.0)
        assert rolled == 10.0
        assert acct.locked == 20.0
        assert acct.available == 80.0

    def test_rollback_more_than_locked(self):
        acct = ATPAccount(available=70.0, locked=30.0)
        rolled = acct.rollback(50.0)
        assert rolled == 30.0  # capped at locked
        assert acct.locked == 0.0
        assert acct.available == 100.0

    def test_lock_commit_cycle(self):
        """Full lock → commit lifecycle."""
        acct = ATPAccount(available=100.0)
        acct.lock(30.0)
        acct.commit(30.0)
        assert acct.available == 70.0
        assert acct.locked == 0.0
        assert acct.adp == 30.0
        assert acct.total == 70.0

    def test_lock_rollback_cycle(self):
        """Full lock → rollback lifecycle (restores available)."""
        acct = ATPAccount(available=100.0)
        acct.lock(30.0)
        acct.rollback(30.0)
        assert acct.available == 100.0
        assert acct.locked == 0.0
        assert acct.total == 100.0


# ── ATPAccount Recharge ──────────────────────────────────────────


class TestATPAccountRecharge:
    """ATPAccount.recharge()."""

    def test_basic_recharge(self):
        acct = ATPAccount(available=40.0, initial_balance=100.0)
        recharged = acct.recharge(rate=0.1)
        assert recharged == pytest.approx(10.0)
        assert acct.available == pytest.approx(50.0)

    def test_recharge_capped_by_max(self):
        acct = ATPAccount(available=295.0, initial_balance=100.0)
        recharged = acct.recharge(rate=0.1, max_multiplier=3.0)
        assert recharged == pytest.approx(5.0)
        assert acct.available == pytest.approx(300.0)

    def test_recharge_at_max(self):
        acct = ATPAccount(available=300.0, initial_balance=100.0)
        recharged = acct.recharge(rate=0.1, max_multiplier=3.0)
        assert recharged == pytest.approx(0.0)
        assert acct.available == pytest.approx(300.0)

    def test_recharge_above_max(self):
        acct = ATPAccount(available=310.0, initial_balance=100.0)
        recharged = acct.recharge(rate=0.1, max_multiplier=3.0)
        assert recharged == pytest.approx(0.0)
        assert acct.available == pytest.approx(310.0)  # no reduction

    def test_recharge_default_params(self):
        acct = ATPAccount(available=50.0, initial_balance=100.0)
        recharged = acct.recharge()  # rate=0.1, max_multiplier=3.0
        assert recharged == pytest.approx(10.0)
        assert acct.available == pytest.approx(60.0)


# ── Transfer Function ────────────────────────────────────────────


class TestTransfer:
    """transfer() function."""

    def test_basic_transfer(self):
        sender = ATPAccount(available=100.0)
        receiver = ATPAccount(available=50.0)
        result = transfer(sender, receiver, 20.0, fee_rate=0.05)
        assert result.fee == pytest.approx(1.0)
        assert sender.available == pytest.approx(79.0)
        assert receiver.available == pytest.approx(70.0)
        assert result.actual_credit == pytest.approx(20.0)
        assert result.overflow == pytest.approx(0.0)

    def test_capped_transfer(self):
        sender = ATPAccount(available=200.0)
        receiver = ATPAccount(available=490.0)
        result = transfer(sender, receiver, 30.0, fee_rate=0.05, max_balance=500.0)
        assert result.fee == pytest.approx(1.5)
        assert result.actual_credit == pytest.approx(10.0)
        assert result.overflow == pytest.approx(20.0)
        assert sender.available == pytest.approx(188.5)
        assert receiver.available == pytest.approx(500.0)

    def test_transfer_to_full_receiver(self):
        sender = ATPAccount(available=100.0)
        receiver = ATPAccount(available=500.0)
        result = transfer(sender, receiver, 50.0, fee_rate=0.05, max_balance=500.0)
        assert result.actual_credit == pytest.approx(0.0)
        assert result.overflow == pytest.approx(50.0)
        assert sender.available == pytest.approx(97.5)  # only fee lost
        assert receiver.available == pytest.approx(500.0)

    def test_transfer_insufficient_balance(self):
        sender = ATPAccount(available=10.0)
        receiver = ATPAccount(available=0.0)
        with pytest.raises(ValueError, match="Insufficient balance"):
            transfer(sender, receiver, 20.0, fee_rate=0.05)

    def test_transfer_no_cap(self):
        sender = ATPAccount(available=1000.0)
        receiver = ATPAccount(available=0.0)
        result = transfer(sender, receiver, 500.0, fee_rate=0.05)
        assert result.actual_credit == pytest.approx(500.0)
        assert result.overflow == pytest.approx(0.0)
        assert sender.available == pytest.approx(475.0)  # 1000 - 500 - 25
        assert receiver.available == pytest.approx(500.0)

    def test_transfer_zero_fee(self):
        sender = ATPAccount(available=100.0)
        receiver = ATPAccount(available=0.0)
        result = transfer(sender, receiver, 50.0, fee_rate=0.0)
        assert result.fee == pytest.approx(0.0)
        assert sender.available == pytest.approx(50.0)
        assert receiver.available == pytest.approx(50.0)

    def test_transfer_result_fields(self):
        sender = ATPAccount(available=1000.0)
        receiver = ATPAccount(available=0.0)
        result = transfer(sender, receiver, 100.0, fee_rate=0.05)
        assert result.sender_balance == sender.available
        assert result.receiver_balance == receiver.available


# ── Sliding Scale ────────────────────────────────────────────────


class TestSlidingScale:
    """sliding_scale() function."""

    def test_below_threshold(self):
        assert sliding_scale(0.2, 100.0, zero_threshold=0.3, full_threshold=0.7) == pytest.approx(0.0)

    def test_at_zero_threshold(self):
        assert sliding_scale(0.3, 100.0, zero_threshold=0.3, full_threshold=0.7) == pytest.approx(0.0)

    def test_in_ramp_midpoint(self):
        assert sliding_scale(0.5, 100.0, zero_threshold=0.3, full_threshold=0.7) == pytest.approx(50.0)

    def test_at_full_threshold(self):
        assert sliding_scale(0.7, 100.0, zero_threshold=0.3, full_threshold=0.7) == pytest.approx(100.0)

    def test_above_full_threshold(self):
        assert sliding_scale(0.85, 100.0, zero_threshold=0.3, full_threshold=0.7) == pytest.approx(100.0)

    def test_quality_zero(self):
        assert sliding_scale(0.0, 100.0, zero_threshold=0.3, full_threshold=0.7) == pytest.approx(0.0)

    def test_quality_one(self):
        assert sliding_scale(1.0, 100.0, zero_threshold=0.3, full_threshold=0.7) == pytest.approx(100.0)

    def test_ramp_quarter(self):
        # (0.4 - 0.3) / (0.7 - 0.3) = 0.1/0.4 = 0.25
        assert sliding_scale(0.4, 100.0, zero_threshold=0.3, full_threshold=0.7) == pytest.approx(25.0)

    def test_different_base_payment(self):
        assert sliding_scale(0.5, 200.0, zero_threshold=0.3, full_threshold=0.7) == pytest.approx(100.0)


# ── Conservation Check ───────────────────────────────────────────


class TestCheckConservation:
    """check_conservation() function."""

    def test_valid_conservation(self):
        assert check_conservation(
            initial_balances=[100.0, 100.0],
            final_balances=[90.0, 105.0],
            total_fees=5.0,
        ) is True

    def test_violated_conservation(self):
        assert check_conservation(
            initial_balances=[100.0, 100.0],
            final_balances=[90.0, 100.0],
            total_fees=5.0,
        ) is False

    def test_exact_conservation(self):
        assert check_conservation(
            initial_balances=[100.0],
            final_balances=[95.0],
            total_fees=5.0,
        ) is True

    def test_within_tolerance(self):
        assert check_conservation(
            initial_balances=[100.0],
            final_balances=[95.00005],
            total_fees=5.0,
            tolerance=0.0001,
        ) is True

    def test_outside_tolerance(self):
        assert check_conservation(
            initial_balances=[100.0],
            final_balances=[95.001],
            total_fees=5.0,
            tolerance=0.0001,
        ) is False


# ── Energy Ratio (Standalone) ────────────────────────────────────


class TestEnergyRatio:
    """energy_ratio() standalone function."""

    def test_basic(self):
        assert energy_ratio(80.0, 20.0) == pytest.approx(0.8)

    def test_pure_atp(self):
        assert energy_ratio(100.0, 0.0) == pytest.approx(1.0)

    def test_pure_adp(self):
        assert energy_ratio(0.0, 100.0) == pytest.approx(0.0)

    def test_zero_zero(self):
        assert energy_ratio(0.0, 0.0) == pytest.approx(0.5)

    def test_equal(self):
        assert energy_ratio(50.0, 50.0) == pytest.approx(0.5)


# ── Sybil Cost ───────────────────────────────────────────────────


class TestSybilCost:
    """sybil_cost() function."""

    def test_basic(self):
        result = sybil_cost(5, 250.0, 50.0, fee_rate=0.05)
        assert result["total_setup_cost"] == pytest.approx(1500.0)
        assert result["per_identity_cost"] == pytest.approx(300.0)
        assert result["circular_flow_loss_per_cycle"] == pytest.approx(12.5)

    def test_single_identity(self):
        result = sybil_cost(1, 100.0, 50.0, fee_rate=0.05)
        assert result["total_setup_cost"] == pytest.approx(150.0)
        assert result["per_identity_cost"] == pytest.approx(150.0)
        assert result["circular_flow_loss_per_cycle"] == pytest.approx(2.5)

    def test_zero_fee(self):
        result = sybil_cost(3, 100.0, 50.0, fee_rate=0.0)
        assert result["circular_flow_loss_per_cycle"] == pytest.approx(0.0)


# ── Fee Sensitivity ──────────────────────────────────────────────


class TestFeeSensitivity:
    """fee_sensitivity() function."""

    def test_basic_sweep(self):
        results = fee_sensitivity(100.0, [0.0, 0.01, 0.05, 0.10, 0.20])
        assert len(results) == 5
        assert results[0]["fee"] == pytest.approx(0.0)
        assert results[0]["net_received"] == pytest.approx(100.0)
        assert results[0]["total_sender_cost"] == pytest.approx(100.0)
        assert results[2]["fee"] == pytest.approx(5.0)
        assert results[2]["total_sender_cost"] == pytest.approx(105.0)
        assert results[4]["fee"] == pytest.approx(20.0)
        assert results[4]["total_sender_cost"] == pytest.approx(120.0)

    def test_all_receive_full_amount(self):
        results = fee_sensitivity(100.0, [0.01, 0.05, 0.10])
        for r in results:
            assert r["net_received"] == pytest.approx(100.0)

    def test_single_rate(self):
        results = fee_sensitivity(50.0, [0.10])
        assert len(results) == 1
        assert results[0]["fee"] == pytest.approx(5.0)
        assert results[0]["fee_rate"] == 0.10


# ── Cross-Language Test Vector Validation ─────────────────────────


class TestATPVectors:
    """Validate against cross-language test vectors."""

    @pytest.fixture(autouse=True)
    def _load_vectors(self):
        self.vectors = load_vectors("transfer-operations.json")

    def _get_vector(self, vector_id):
        for v in self.vectors:
            if v["id"] == vector_id:
                return v
        raise KeyError(f"Vector {vector_id} not found")

    def test_atp001_basic_transfer(self):
        """atp-001: Basic transfer with 5% fee."""
        v = self._get_vector("atp-001")
        inp = v["input"]
        exp = v["expected"]
        sender = ATPAccount(available=inp["sender_balance"])
        receiver = ATPAccount(available=inp["receiver_balance"])
        result = transfer(sender, receiver, inp["amount"], fee_rate=inp["fee_rate"])
        assert result.fee == pytest.approx(exp["fee"], abs=v["tolerance"])
        assert sender.available == pytest.approx(exp["sender_balance"], abs=v["tolerance"])
        assert receiver.available == pytest.approx(exp["receiver_balance"], abs=v["tolerance"])

    def test_atp002_capped_transfer(self):
        """atp-002: Transfer with MAX_BALANCE cap and overflow return."""
        v = self._get_vector("atp-002")
        inp = v["input"]
        exp = v["expected"]
        sender = ATPAccount(available=inp["sender_balance"])
        receiver = ATPAccount(available=inp["receiver_balance"])
        result = transfer(sender, receiver, inp["amount"],
                          fee_rate=inp["fee_rate"], max_balance=inp["max_balance"])
        assert result.fee == pytest.approx(exp["fee"], abs=v["tolerance"])
        assert result.actual_credit == pytest.approx(exp["actual_credit"], abs=v["tolerance"])
        assert result.overflow == pytest.approx(exp["overflow"], abs=v["tolerance"])
        assert sender.available == pytest.approx(exp["sender_balance"], abs=v["tolerance"])
        assert receiver.available == pytest.approx(exp["receiver_balance"], abs=v["tolerance"])

    def test_atp003_transfer_to_full(self):
        """atp-003: Transfer to already-full receiver."""
        v = self._get_vector("atp-003")
        inp = v["input"]
        exp = v["expected"]
        sender = ATPAccount(available=inp["sender_balance"])
        receiver = ATPAccount(available=inp["receiver_balance"])
        result = transfer(sender, receiver, inp["amount"],
                          fee_rate=inp["fee_rate"], max_balance=inp["max_balance"])
        assert result.fee == pytest.approx(exp["fee"], abs=v["tolerance"])
        assert result.actual_credit == pytest.approx(exp["actual_credit"], abs=v["tolerance"])
        assert result.overflow == pytest.approx(exp["overflow"], abs=v["tolerance"])
        assert sender.available == pytest.approx(exp["sender_balance"], abs=v["tolerance"])

    def test_atp004_conservation(self):
        """atp-004: Conservation invariant across multi-party transfers."""
        v = self._get_vector("atp-004")
        inp = v["input"]
        exp = v["expected"]
        accounts = [ATPAccount(available=b) for b in inp["initial_balances"]]
        total_fees = 0.0
        for t in inp["transfers"]:
            result = transfer(accounts[t["from"]], accounts[t["to"]],
                              t["amount"], fee_rate=inp["fee_rate"])
            total_fees += result.fee
        final_balances = [a.available for a in accounts]
        assert sum(inp["initial_balances"]) == pytest.approx(
            sum(final_balances) + total_fees, abs=v["tolerance"]
        )
        assert total_fees == pytest.approx(exp["total_fees"], abs=v["tolerance"])

    def test_atp005_sliding_below(self):
        """atp-005: Sliding scale — below threshold."""
        v = self._get_vector("atp-005")
        inp = v["input"]
        exp = v["expected"]
        payment = sliding_scale(inp["quality"], inp["base_payment"],
                                zero_threshold=inp["zero_threshold"],
                                full_threshold=inp["full_threshold"])
        assert payment == pytest.approx(exp["payment"], abs=v["tolerance"])

    def test_atp006_sliding_ramp(self):
        """atp-006: Sliding scale — in ramp zone."""
        v = self._get_vector("atp-006")
        inp = v["input"]
        exp = v["expected"]
        payment = sliding_scale(inp["quality"], inp["base_payment"],
                                zero_threshold=inp["zero_threshold"],
                                full_threshold=inp["full_threshold"])
        assert payment == pytest.approx(exp["payment"], abs=v["tolerance"])

    def test_atp007_sliding_above(self):
        """atp-007: Sliding scale — above full threshold."""
        v = self._get_vector("atp-007")
        inp = v["input"]
        exp = v["expected"]
        payment = sliding_scale(inp["quality"], inp["base_payment"],
                                zero_threshold=inp["zero_threshold"],
                                full_threshold=inp["full_threshold"])
        assert payment == pytest.approx(exp["payment"], abs=v["tolerance"])

    def test_atp008_lock_lifecycle(self):
        """atp-008: Lock-commit-rollback lifecycle."""
        v = self._get_vector("atp-008")
        inp = v["input"]
        exp = v["expected"]
        tol = v["tolerance"]

        # Lock
        acct = ATPAccount(available=inp["initial_balance"])
        acct.lock(inp["lock_amount"])
        assert acct.available == pytest.approx(exp["after_lock"]["available"], abs=tol)
        assert acct.locked == pytest.approx(exp["after_lock"]["locked"], abs=tol)
        assert acct.total == pytest.approx(exp["after_lock"]["total"], abs=tol)

        # Commit path
        acct_commit = ATPAccount(available=inp["initial_balance"])
        acct_commit.lock(inp["lock_amount"])
        committed = acct_commit.commit(inp["lock_amount"])
        assert acct_commit.available == pytest.approx(exp["after_commit"]["available"], abs=tol)
        assert acct_commit.locked == pytest.approx(exp["after_commit"]["locked"], abs=tol)
        assert acct_commit.total == pytest.approx(exp["after_commit"]["total"], abs=tol)
        assert committed == pytest.approx(exp["after_commit"]["committed_amount"], abs=tol)

        # Rollback path
        acct_rollback = ATPAccount(available=inp["initial_balance"])
        acct_rollback.lock(inp["lock_amount"])
        acct_rollback.rollback(inp["lock_amount"])
        assert acct_rollback.available == pytest.approx(exp["after_rollback_instead"]["available"], abs=tol)
        assert acct_rollback.locked == pytest.approx(exp["after_rollback_instead"]["locked"], abs=tol)
        assert acct_rollback.total == pytest.approx(exp["after_rollback_instead"]["total"], abs=tol)

    def test_atp009_recharge(self):
        """atp-009: Recharge calculation."""
        v = self._get_vector("atp-009")
        inp = v["input"]
        exp = v["expected"]
        acct = ATPAccount(available=inp["current_balance"],
                          initial_balance=inp["initial_balance"])
        recharged = acct.recharge(rate=inp["recharge_rate"],
                                  max_multiplier=inp["max_recharge_multiplier"])
        assert recharged == pytest.approx(exp["recharge_amount"], abs=v["tolerance"])
        assert acct.available == pytest.approx(exp["new_balance"], abs=v["tolerance"])

    def test_atp010_recharge_at_cap(self):
        """atp-010: Recharge at cap."""
        v = self._get_vector("atp-010")
        inp = v["input"]
        exp = v["expected"]
        acct = ATPAccount(available=inp["current_balance"],
                          initial_balance=inp["initial_balance"])
        recharged = acct.recharge(rate=inp["recharge_rate"],
                                  max_multiplier=inp["max_recharge_multiplier"])
        assert recharged == pytest.approx(exp["recharge_amount"], abs=v["tolerance"])
        assert acct.available == pytest.approx(exp["new_balance"], abs=v["tolerance"])

    def test_atp011_sybil_cost(self):
        """atp-011: Sybil cost analysis."""
        v = self._get_vector("atp-011")
        inp = v["input"]
        exp = v["expected"]
        result = sybil_cost(inp["num_identities"],
                            inp["hardware_cost_per_identity"],
                            inp["atp_stake_per_identity"],
                            fee_rate=inp["transfer_fee_rate"])
        assert result["total_setup_cost"] == pytest.approx(exp["total_setup_cost"], abs=v["tolerance"])
        assert result["per_identity_cost"] == pytest.approx(exp["per_identity_cost"], abs=v["tolerance"])
        assert result["circular_flow_loss_per_cycle"] == pytest.approx(
            exp["circular_flow_loss_per_cycle"], abs=v["tolerance"]
        )

    def test_atp012_energy_ratio(self):
        """atp-012: Energy ratio calculation."""
        v = self._get_vector("atp-012")
        inp = v["input"]
        exp = v["expected"]
        ratio = energy_ratio(inp["atp_balance"], inp["adp_accumulated"])
        assert ratio == pytest.approx(exp["energy_ratio"], abs=v["tolerance"])

    def test_atp013_energy_ratio_edge_cases(self):
        """atp-013: Energy ratio edge cases."""
        v = self._get_vector("atp-013")
        inp = v["input"]
        exp = v["expected"]
        for case, expected_ratio in zip(inp["cases"], exp["ratios"]):
            ratio = energy_ratio(case["atp"], case["adp"])
            assert ratio == pytest.approx(expected_ratio, abs=v["tolerance"])

    def test_atp014_fee_sensitivity(self):
        """atp-014: Fee sensitivity sweep."""
        v = self._get_vector("atp-014")
        inp = v["input"]
        exp = v["expected"]
        results = fee_sensitivity(inp["amount"], inp["fee_rates"])
        for i, r in enumerate(results):
            assert r["fee"] == pytest.approx(exp["fees"][i], abs=v["tolerance"])
            assert r["total_sender_cost"] == pytest.approx(
                exp["total_sender_costs"][i], abs=v["tolerance"]
            )

    def test_atp015_quality_settlement(self):
        """atp-015: Quality-based settlement via sliding_scale."""
        v = self._get_vector("atp-015")
        inp = v["input"]
        exp = v["expected"]
        for quality, expected_payment in zip(inp["quality_scores"], exp["payments"]):
            payment = sliding_scale(quality, inp["task_payment"],
                                    zero_threshold=inp["zero_threshold"],
                                    full_threshold=inp["full_threshold"])
            assert payment == pytest.approx(expected_payment, abs=v["tolerance"])
