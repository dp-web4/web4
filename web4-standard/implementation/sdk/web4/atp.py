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

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

__all__ = [
    # Classes
    "ATPAccount", "TransferResult",
    # Functions
    "energy_ratio", "transfer", "sliding_scale",
    "check_conservation", "sybil_cost", "fee_sensitivity",
    # Constants
    "ATP_JSONLD_CONTEXT",
]


# ── JSON-LD Context ──────────────────────────────────────────────

ATP_JSONLD_CONTEXT = "https://web4.io/contexts/atp.jsonld"


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

    def __post_init__(self) -> None:
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

    def to_jsonld(self) -> Dict[str, Any]:
        """
        Serialize to JSON-LD per atp-adp-cycle spec.

        Produces the canonical ATPAccount document structure with:
        - @context header for JSON-LD processors
        - Sub-pool breakdown (available, locked, adp)
        - Computed properties (total, energy_ratio)
        """
        return {
            "@context": [ATP_JSONLD_CONTEXT],
            "@type": "ATPAccount",
            "available": self.available,
            "locked": self.locked,
            "adp": self.adp,
            "initial_balance": self.initial_balance,
            "total": self.total,
            "energy_ratio": self.energy_ratio,
        }

    def to_jsonld_string(self, indent: int = 2) -> str:
        """Serialize to JSON-LD string."""
        return json.dumps(self.to_jsonld(), indent=indent)

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> ATPAccount:
        """
        Deserialize from JSON-LD document.

        Accepts both spec JSON-LD format and plain dict format.
        Ignores @context, @type, and computed properties (total, energy_ratio).
        """
        return cls(
            available=doc.get("available", 0.0),
            locked=doc.get("locked", 0.0),
            adp=doc.get("adp", 0.0),
            initial_balance=doc.get("initial_balance", 0.0),
        )

    @classmethod
    def from_jsonld_string(cls, s: str) -> ATPAccount:
        """Deserialize from JSON-LD string."""
        return cls.from_jsonld(json.loads(s))


# ── Transfer Operations ──────────────────────────────────────────

@dataclass
class TransferResult:
    """Result of an ATP transfer."""
    fee: float
    sender_balance: float
    receiver_balance: float
    actual_credit: float
    overflow: float = 0.0

    def to_jsonld(self) -> Dict[str, Any]:
        """
        Serialize to JSON-LD per atp-adp-cycle spec.

        Captures the outcome of an ATP transfer: fee charged,
        resulting balances, actual credit applied, and any overflow.
        """
        doc: Dict[str, Any] = {
            "@context": [ATP_JSONLD_CONTEXT],
            "@type": "TransferResult",
            "fee": self.fee,
            "sender_balance": self.sender_balance,
            "receiver_balance": self.receiver_balance,
            "actual_credit": self.actual_credit,
        }
        if self.overflow > 0:
            doc["overflow"] = self.overflow
        return doc

    def to_jsonld_string(self, indent: int = 2) -> str:
        """Serialize to JSON-LD string."""
        return json.dumps(self.to_jsonld(), indent=indent)

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> TransferResult:
        """
        Deserialize from JSON-LD document.

        Accepts both spec JSON-LD format and plain dict format.
        Ignores @context and @type fields.
        """
        return cls(
            fee=doc["fee"],
            sender_balance=doc["sender_balance"],
            receiver_balance=doc["receiver_balance"],
            actual_credit=doc["actual_credit"],
            overflow=doc.get("overflow", 0.0),
        )

    @classmethod
    def from_jsonld_string(cls, s: str) -> TransferResult:
        """Deserialize from JSON-LD string."""
        return cls.from_jsonld(json.loads(s))


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
) -> dict[str, float]:
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

def fee_sensitivity(amount: float, fee_rates: List[float]) -> List[dict[str, float]]:
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
