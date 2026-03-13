"""
Web4 ATP/ADP Value Cycle

Canonical implementation per web4-standard/core-spec/atp-adp-cycle.md.

ATP (Allocation Transfer Packet) / ADP (Allocation Discharge Packet)
is Web4's bio-inspired value metabolism. Value flows through work,
not accumulation.

Key invariant: ATP conservation — total ATP + fees always equals initial.
Validated against: web4-standard/test-vectors/atp/transfer-operations.json
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ── ATP Account ──────────────────────────────────────────────────

@dataclass
class ATPAccount:
    """
    An entity's ATP balance with lock support.

    ATP tokens exist in three sub-pools:
    - available: can be transferred or locked
    - locked: reserved for pending operations (commit or rollback)
    - adp: discharged tokens tracking past expenditure

    Invariant: total = available + locked (ADP is separate tracking).
    """

    available: float = 0.0
    locked: float = 0.0
    adp: float = 0.0
    initial_balance: float = 0.0

    def __post_init__(self):
        if self.initial_balance == 0.0:
            self.initial_balance = self.available

    @property
    def total(self) -> float:
        """Total ATP (available + locked)."""
        return self.available + self.locked

    @property
    def energy_ratio(self) -> float:
        """
        Energy ratio: ATP / (ATP + ADP).

        High ratio = entity is earning/conserving.
        Low ratio = entity is spending.
        Zero/zero defaults to 0.5 (neutral).
        (test vector atp-012, atp-013)
        """
        total = self.total + self.adp
        if total == 0:
            return 0.5
        return self.total / total

    def lock(self, amount: float) -> bool:
        """
        Lock ATP for a pending operation.
        Returns False if insufficient available balance.
        """
        if amount > self.available:
            return False
        self.available -= amount
        self.locked += amount
        return True

    def commit(self, amount: float) -> float:
        """
        Commit locked ATP (discharge it).
        Returns actual amount committed (may be less if lock was partial).
        """
        actual = min(amount, self.locked)
        self.locked -= actual
        self.adp += actual
        return actual

    def rollback(self, amount: float) -> float:
        """
        Rollback locked ATP (return to available).
        Returns actual amount rolled back.
        """
        actual = min(amount, self.locked)
        self.locked -= actual
        self.available += actual
        return actual

    def recharge(self, rate: float = 0.1, max_multiplier: float = 3.0) -> float:
        """
        Recharge ATP from ADP pool (test vectors atp-009, atp-010).

        recharge_amount = min(initial * rate, max_balance - current)
        """
        max_balance = self.initial_balance * max_multiplier
        raw_recharge = self.initial_balance * rate
        space = max(0.0, max_balance - self.total)
        actual = min(raw_recharge, space)
        self.available += actual
        return actual


# ── Transfer Operations ──────────────────────────────────────────

@dataclass
class TransferResult:
    """Result of an ATP transfer."""
    fee: float
    sender_balance: float
    receiver_balance: float
    actual_credit: float
    overflow: float = 0.0


def transfer(
    sender: ATPAccount,
    receiver: ATPAccount,
    amount: float,
    fee_rate: float = 0.05,
    max_balance: Optional[float] = None,
) -> TransferResult:
    """
    Transfer ATP between accounts (test vectors atp-001 through atp-003).

    Fee is charged to sender ON TOP of the transfer amount.
    If max_balance is set, overflow is returned to sender.

    Invariant: sender_deducted = amount + fee - overflow
    """
    fee = amount * fee_rate
    total_deduction = amount + fee

    if total_deduction > sender.available:
        raise ValueError(
            f"Insufficient balance: need {total_deduction}, have {sender.available}"
        )

    # Calculate actual credit considering cap
    if max_balance is not None:
        space = max(0.0, max_balance - receiver.available)
        actual_credit = min(amount, space)
        overflow = amount - actual_credit
    else:
        actual_credit = amount
        overflow = 0.0

    # Execute
    sender.available -= total_deduction
    sender.available += overflow  # Return overflow
    receiver.available += actual_credit

    return TransferResult(
        fee=fee,
        sender_balance=sender.available,
        receiver_balance=receiver.available,
        actual_credit=actual_credit,
        overflow=overflow,
    )


# ── Sliding Scale Payment ────────────────────────────────────────

def sliding_scale(
    quality: float,
    base_payment: float,
    zero_threshold: float = 0.3,
    full_threshold: float = 0.7,
) -> float:
    """
    Quality-based sliding scale payment (test vectors atp-005 through atp-007, atp-015).

    Below zero_threshold: 0 payment.
    Between thresholds: linear ramp.
    At or above full_threshold: full base_payment.
    """
    if quality < zero_threshold:
        return 0.0
    if quality >= full_threshold:
        return base_payment
    scale = (quality - zero_threshold) / (full_threshold - zero_threshold)
    return base_payment * scale


# ── Conservation Check ───────────────────────────────────────────

def check_conservation(
    initial_balances: List[float],
    final_balances: List[float],
    total_fees: float,
    tolerance: float = 0.0001,
) -> bool:
    """
    Verify ATP conservation invariant (test vector atp-004).

    initial_total == final_total + total_fees
    """
    initial_total = sum(initial_balances)
    final_total = sum(final_balances)
    return abs(initial_total - (final_total + total_fees)) < tolerance


# ── Energy Ratio (standalone) ────────────────────────────────────

def energy_ratio(atp: float, adp: float) -> float:
    """
    Energy ratio calculation (test vectors atp-012, atp-013).

    atp / (atp + adp), with 0/0 → 0.5 (neutral).
    """
    total = atp + adp
    if total == 0:
        return 0.5
    return atp / total


# ── Sybil Cost Analysis ─────────────────────────────────────────

def sybil_cost(
    num_identities: int,
    hardware_cost: float,
    atp_stake: float,
    fee_rate: float = 0.05,
) -> dict:
    """
    Sybil attack cost analysis (test vector atp-011).

    Returns setup cost and per-cycle circular flow loss.
    """
    per_identity = hardware_cost + atp_stake
    total_setup = num_identities * per_identity
    circular_loss = num_identities * atp_stake * fee_rate

    return {
        "total_setup_cost": total_setup,
        "per_identity_cost": per_identity,
        "circular_flow_loss_per_cycle": circular_loss,
    }


# ── Fee Sensitivity ──────────────────────────────────────────────

def fee_sensitivity(amount: float, fee_rates: List[float]) -> List[dict]:
    """
    Fee sensitivity sweep (test vector atp-014).

    For each fee rate, compute fee, net received, and total sender cost.
    Fee is additive to sender, not deducted from amount.
    """
    results = []
    for rate in fee_rates:
        fee = amount * rate
        results.append({
            "fee_rate": rate,
            "fee": fee,
            "net_received": amount,  # receiver gets full amount
            "total_sender_cost": amount + fee,
        })
    return results
