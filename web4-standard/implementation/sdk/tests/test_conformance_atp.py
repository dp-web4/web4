"""Cross-language conformance tests for ATP/ADP operations.

Loads ``web4-standard/testing/conformance/atp-operations.json`` and asserts
that the Python ``web4.atp`` module produces the documented expected outputs.

The conformance vectors were shipped by the operator (commit 92454d6) and are
declared cross-language: "Any Web4 implementation MUST produce identical results
for these inputs."

Sprint 49 cross-language audit named ATP as the best-aligned pair across Rust
and Python ("identical core semantics"), so a high pass rate is expected.
Where a vector cannot be satisfied without behavioral changes to the SDK, the
test is marked ``xfail`` with a reason citing the specific divergence —
silent fixes (assertion weakening, vector edits, or SDK edits to make vectors
pass) are explicitly forbidden by the Sprint 52 policy review.

Suite version: 0.1.0
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import pytest

from web4.atp import ATPAccount, sliding_scale, transfer

CONFORMANCE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "testing", "conformance")


def _load_suite() -> Dict[str, Any]:
    path = os.path.join(CONFORMANCE_DIR, "atp-operations.json")
    with open(path) as f:
        return json.load(f)


SUITE = _load_suite()


# ── Account vectors ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "vector",
    SUITE["account_vectors"],
    ids=lambda v: v["id"],
)
def test_account_vector(vector: Dict[str, Any]) -> None:
    operation = vector["operation"]
    expected = vector["expected"]

    if operation == "new":
        balance = vector["input"]["initial_balance"]
        account = ATPAccount(available=balance, initial_balance=balance)
        assert account.available == expected["available"]
        assert account.locked == expected["locked"]
        assert account.adp == expected["adp"]
        assert account.total == expected["total"]
        assert account.energy_ratio == expected["energy_ratio"]
        return

    initial = vector["initial"]
    account = ATPAccount(
        available=initial["available"],
        locked=initial["locked"],
        adp=initial["adp"],
    )

    if operation == "lock":
        amount = vector["input"]["amount"]
        ok = account.lock(amount)
        assert ok is True
        assert account.available == expected["available"]
        assert account.locked == expected["locked"]
        assert account.total == expected["total"]
        return

    if operation == "commit":
        amount = vector["input"]["amount"]
        committed = account.commit(amount)
        assert committed == amount
        assert account.available == expected["available"]
        assert account.locked == expected["locked"]
        assert account.adp == expected["adp"]
        assert account.total == expected["total"]
        assert account.energy_ratio == expected["energy_ratio"]
        return

    if operation == "rollback":
        amount = vector["input"]["amount"]
        rolled = account.rollback(amount)
        assert rolled == amount
        assert account.available == expected["available"]
        assert account.locked == expected["locked"]
        assert account.adp == expected["adp"]
        return

    if operation == "energy_ratio":
        # atp-005: zero-balance neutral
        assert account.energy_ratio == expected["energy_ratio"]
        return

    pytest.fail(f"Unknown operation in account vector {vector['id']}: {operation}")


# ── Transfer vectors ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "vector",
    SUITE["transfer_vectors"],
    ids=lambda v: v["id"],
)
def test_transfer_vector(vector: Dict[str, Any]) -> None:
    sender = ATPAccount(available=vector["sender"]["available"])
    receiver = ATPAccount(available=vector["receiver"]["available"])

    inp = vector["input"]
    amount = inp["amount"]
    fee_rate = inp.get("fee_rate", 0.05)
    max_balance = inp.get("max_balance")

    expected = vector["expected"]

    if expected.get("error"):
        with pytest.raises(ValueError):
            transfer(sender, receiver, amount, fee_rate=fee_rate, max_balance=max_balance)
        return

    result = transfer(sender, receiver, amount, fee_rate=fee_rate, max_balance=max_balance)

    if "fee" in expected:
        assert result.fee == expected["fee"]
    assert result.actual_credit == expected["actual_credit"]
    assert result.overflow == expected.get("overflow", 0.0)
    assert result.sender_balance == expected["sender_balance"]
    assert result.receiver_balance == expected["receiver_balance"]

    if expected.get("conservation_holds"):
        # invariant: sender_deducted == actual_credit + fee + overflow
        sender_deducted = vector["sender"]["available"] - result.sender_balance
        assert sender_deducted == pytest.approx(result.actual_credit + result.fee + result.overflow)


# ── Sliding-scale vectors ────────────────────────────────────────


@pytest.mark.parametrize(
    "vector",
    SUITE["sliding_scale_vectors"],
    ids=lambda v: v["id"],
)
def test_sliding_scale_vector(vector: Dict[str, Any]) -> None:
    inp = vector["input"]
    result = sliding_scale(
        quality=inp["quality"],
        base_payment=inp["base_payment"],
        zero_threshold=inp["zero_threshold"],
        full_threshold=inp["full_threshold"],
    )

    if "expected" in vector:
        assert result == vector["expected"]
    else:
        tolerance = vector.get("tolerance", 1e-10)
        assert result == pytest.approx(vector["expected_approx"], abs=tolerance)


# ── Suite-level meta ─────────────────────────────────────────────


def test_suite_metadata() -> None:
    """The suite version and shape are part of the conformance contract."""
    assert SUITE["suite"] == "ATP/ADP Operations"
    assert SUITE["version"] == "0.1.0"

    # Counts match the README's documented vector budget.
    assert len(SUITE["account_vectors"]) == 5
    assert len(SUITE["transfer_vectors"]) == 3
    assert len(SUITE["sliding_scale_vectors"]) == 3


def test_all_vectors_have_ids() -> None:
    """Every vector must have a stable id for cross-language reference."""
    seen: List[str] = []
    for category in ("account_vectors", "transfer_vectors", "sliding_scale_vectors"):
        for v in SUITE[category]:
            assert "id" in v, f"vector missing id in {category}: {v}"
            assert v["id"] not in seen, f"duplicate vector id: {v['id']}"
            seen.append(v["id"])
