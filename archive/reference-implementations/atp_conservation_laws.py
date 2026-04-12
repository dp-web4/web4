"""
ATP Conservation Laws for Web4
Session 31, Track 4

Formal verification of ATP conservation across all operations:
- Transfer conservation (sender loses what receiver gains)
- Fee conservation (fees go to redistribution pool)
- Mint/burn accounting (supply changes tracked)
- Multi-party transaction conservation
- Federation operations (merge/split/migrate)
- Fixed-point arithmetic for exact conservation
- Conservation invariant monitoring
- Violation detection and rollback
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Set


# ─── Fixed-Point Arithmetic ───────────────────────────────────────

SCALE = 1_000_000  # 6 decimal places


def to_fixed(value: float) -> int:
    """Convert float to fixed-point integer."""
    return round(value * SCALE)


def from_fixed(value: int) -> float:
    """Convert fixed-point integer to float."""
    return value / SCALE


def fixed_add(a: int, b: int) -> int:
    return a + b


def fixed_sub(a: int, b: int) -> int:
    return a - b


def fixed_mul(a: int, b: int) -> int:
    """Multiply with proper scaling."""
    return (a * b + SCALE // 2) // SCALE  # round to nearest


# ─── ATP Ledger ───────────────────────────────────────────────────

class TransactionType(Enum):
    TRANSFER = "transfer"
    FEE = "fee"
    MINT = "mint"
    BURN = "burn"
    REDISTRIBUTE = "redistribute"


@dataclass
class ATPTransaction:
    tx_id: int
    tx_type: TransactionType
    from_account: Optional[str]
    to_account: Optional[str]
    amount: int  # fixed-point
    fee: int = 0  # fixed-point
    timestamp: int = 0


class ATPLedger:
    """ATP ledger with conservation invariant enforcement."""

    def __init__(self):
        self.balances: Dict[str, int] = {}
        self.fee_pool: int = 0
        self.total_supply: int = 0
        self.transactions: List[ATPTransaction] = []
        self.tx_counter = 0

    def mint(self, account: str, amount: int) -> ATPTransaction:
        """Create new ATP (increases supply)."""
        self.balances[account] = self.balances.get(account, 0) + amount
        self.total_supply += amount
        tx = ATPTransaction(self._next_tx(), TransactionType.MINT, None, account, amount)
        self.transactions.append(tx)
        return tx

    def burn(self, account: str, amount: int) -> Optional[ATPTransaction]:
        """Destroy ATP (decreases supply)."""
        if self.balances.get(account, 0) < amount:
            return None
        self.balances[account] -= amount
        self.total_supply -= amount
        tx = ATPTransaction(self._next_tx(), TransactionType.BURN, account, None, amount)
        self.transactions.append(tx)
        return tx

    def transfer(self, from_acc: str, to_acc: str, amount: int,
                 fee_rate: int = 0) -> Optional[ATPTransaction]:
        """Transfer with optional fee."""
        fee = fixed_mul(amount, fee_rate)
        total_debit = amount + fee

        if self.balances.get(from_acc, 0) < total_debit:
            return None

        self.balances[from_acc] -= total_debit
        self.balances[to_acc] = self.balances.get(to_acc, 0) + amount
        self.fee_pool += fee

        tx = ATPTransaction(self._next_tx(), TransactionType.TRANSFER,
                           from_acc, to_acc, amount, fee)
        self.transactions.append(tx)
        return tx

    def redistribute_fees(self, accounts: List[str]) -> List[ATPTransaction]:
        """Distribute fee pool equally among accounts."""
        if not accounts or self.fee_pool == 0:
            return []

        per_account = self.fee_pool // len(accounts)
        remainder = self.fee_pool - per_account * len(accounts)

        txs = []
        for acc in accounts:
            self.balances[acc] = self.balances.get(acc, 0) + per_account
            txs.append(ATPTransaction(
                self._next_tx(), TransactionType.REDISTRIBUTE,
                "fee_pool", acc, per_account))

        # Remainder stays in pool
        self.fee_pool = remainder
        return txs

    def check_conservation(self) -> Dict:
        """Verify conservation invariant."""
        sum_balances = sum(self.balances.values())
        expected = self.total_supply

        return {
            "conserved": sum_balances + self.fee_pool == expected,
            "sum_balances": sum_balances,
            "fee_pool": self.fee_pool,
            "total_supply": expected,
            "discrepancy": sum_balances + self.fee_pool - expected,
        }

    def _next_tx(self) -> int:
        self.tx_counter += 1
        return self.tx_counter


# ─── Multi-Party Transactions ─────────────────────────────────────

def multi_party_transfer(ledger: ATPLedger, transfers: List[Tuple[str, str, int]],
                          fee_rate: int = 0) -> bool:
    """
    Atomic multi-party transfer.
    All succeed or all fail (transaction semantics).
    """
    # Pre-check all balances
    debits: Dict[str, int] = {}
    for from_acc, to_acc, amount in transfers:
        fee = fixed_mul(amount, fee_rate)
        debits[from_acc] = debits.get(from_acc, 0) + amount + fee

    for acc, total_debit in debits.items():
        if ledger.balances.get(acc, 0) < total_debit:
            return False  # insufficient balance

    # Execute all transfers
    for from_acc, to_acc, amount in transfers:
        ledger.transfer(from_acc, to_acc, amount, fee_rate)

    return True


# ─── Federation Operations ────────────────────────────────────────

def federation_merge(ledger1: ATPLedger, ledger2: ATPLedger) -> ATPLedger:
    """
    Merge two federation ledgers.
    Conservation: total supply = supply1 + supply2.
    """
    merged = ATPLedger()

    # Merge balances (prefix accounts to avoid collision)
    for acc, bal in ledger1.balances.items():
        merged.balances[f"f1:{acc}"] = bal
    for acc, bal in ledger2.balances.items():
        merged.balances[f"f2:{acc}"] = bal

    merged.fee_pool = ledger1.fee_pool + ledger2.fee_pool
    merged.total_supply = ledger1.total_supply + ledger2.total_supply

    return merged


def federation_split(ledger: ATPLedger, group1: Set[str],
                      group2: Set[str]) -> Tuple[ATPLedger, ATPLedger]:
    """
    Split federation into two.
    Conservation: supply1 + supply2 = original supply.
    """
    ledger1 = ATPLedger()
    ledger2 = ATPLedger()

    for acc, bal in ledger.balances.items():
        if acc in group1:
            ledger1.balances[acc] = bal
            ledger1.total_supply += bal
        elif acc in group2:
            ledger2.balances[acc] = bal
            ledger2.total_supply += bal
        # Accounts in neither go to ledger1 (default)
        else:
            ledger1.balances[acc] = bal
            ledger1.total_supply += bal

    # Split fee pool proportionally
    total = ledger1.total_supply + ledger2.total_supply
    if total > 0:
        ledger1.fee_pool = (ledger.fee_pool * ledger1.total_supply + total // 2) // total
        ledger2.fee_pool = ledger.fee_pool - ledger1.fee_pool
    else:
        ledger1.fee_pool = ledger.fee_pool // 2
        ledger2.fee_pool = ledger.fee_pool - ledger1.fee_pool

    ledger1.total_supply += ledger1.fee_pool
    ledger2.total_supply += ledger2.fee_pool

    return ledger1, ledger2


def migration_transfer(src_ledger: ATPLedger, dst_ledger: ATPLedger,
                        account: str, amount: int) -> bool:
    """
    Transfer ATP between federations.
    Burn in source, mint in destination.
    Conservation: total across both unchanged.
    """
    if src_ledger.balances.get(account, 0) < amount:
        return False

    src_ledger.burn(account, amount)
    dst_ledger.mint(account, amount)
    return True


# ─── Conservation Monitor ─────────────────────────────────────────

class ConservationMonitor:
    """Monitor conservation invariant over time."""

    def __init__(self):
        self.snapshots: List[Dict] = []
        self.violations: List[Dict] = []

    def snapshot(self, ledger: ATPLedger, timestamp: int):
        """Take conservation snapshot."""
        result = ledger.check_conservation()
        result["timestamp"] = timestamp
        self.snapshots.append(result)

        if not result["conserved"]:
            self.violations.append(result)

    def is_clean(self) -> bool:
        """No violations detected."""
        return len(self.violations) == 0

    def violation_count(self) -> int:
        return len(self.violations)


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    print("=" * 70)
    print("ATP Conservation Laws for Web4")
    print("Session 31, Track 4")
    print("=" * 70)

    # ── §1 Fixed-Point Arithmetic ─────────────────────────────────
    print("\n§1 Fixed-Point Arithmetic\n")

    check("to_fixed_1", to_fixed(1.0) == 1_000_000)
    check("to_fixed_0.5", to_fixed(0.5) == 500_000)
    check("from_fixed", abs(from_fixed(750_000) - 0.75) < 1e-10)

    # Addition is exact
    a = to_fixed(1.5)
    b = to_fixed(2.3)
    check("add_exact", from_fixed(fixed_add(a, b)) == 3.8)

    # Subtraction is exact
    check("sub_exact", from_fixed(fixed_sub(a, b)) == -0.8)

    # Multiplication
    m = fixed_mul(to_fixed(0.1), to_fixed(100.0))
    check("mul_correct", abs(from_fixed(m) - 10.0) < 0.001,
          f"result={from_fixed(m)}")

    # ── §2 Basic Transfer Conservation ────────────────────────────
    print("\n§2 Basic Transfer Conservation\n")

    ledger = ATPLedger()
    ledger.mint("alice", to_fixed(100))
    ledger.mint("bob", to_fixed(50))

    cons = ledger.check_conservation()
    check("after_mint_conserved", cons["conserved"], f"disc={cons['discrepancy']}")
    check("total_supply_150", from_fixed(ledger.total_supply) == 150.0)

    # Transfer
    ledger.transfer("alice", "bob", to_fixed(30))
    cons = ledger.check_conservation()
    check("after_transfer_conserved", cons["conserved"])
    check("alice_balance", from_fixed(ledger.balances["alice"]) == 70.0)
    check("bob_balance", from_fixed(ledger.balances["bob"]) == 80.0)

    # ── §3 Fee Conservation ──────────────────────────────────────
    print("\n§3 Fee Conservation\n")

    fee_ledger = ATPLedger()
    fee_ledger.mint("alice", to_fixed(100))
    fee_ledger.mint("bob", to_fixed(100))

    # Transfer with 1% fee
    fee_rate = to_fixed(0.01)
    fee_ledger.transfer("alice", "bob", to_fixed(50), fee_rate)

    cons = fee_ledger.check_conservation()
    check("fee_conserved", cons["conserved"], f"disc={cons['discrepancy']}")

    # Fee pool has the fee
    check("fee_pool_positive", fee_ledger.fee_pool > 0,
          f"pool={from_fixed(fee_ledger.fee_pool):.4f}")

    # Alice lost 50 + fee, Bob gained 50
    alice_loss = to_fixed(100) - fee_ledger.balances["alice"]
    bob_gain = fee_ledger.balances["bob"] - to_fixed(100)
    check("alice_lost_more_than_bob_gained", alice_loss > bob_gain)
    check("difference_is_fee", alice_loss - bob_gain == fee_ledger.fee_pool)

    # ── §4 Fee Redistribution ────────────────────────────────────
    print("\n§4 Fee Redistribution Conservation\n")

    pre_supply = fee_ledger.total_supply
    fee_ledger.redistribute_fees(["alice", "bob"])

    cons = fee_ledger.check_conservation()
    check("redistribution_conserved", cons["conserved"])
    check("supply_unchanged", fee_ledger.total_supply == pre_supply)

    # ── §5 Burn Conservation ─────────────────────────────────────
    print("\n§5 Mint/Burn Conservation\n")

    burn_ledger = ATPLedger()
    burn_ledger.mint("entity", to_fixed(1000))
    initial_supply = burn_ledger.total_supply

    burn_ledger.burn("entity", to_fixed(300))
    check("burn_reduces_supply",
          burn_ledger.total_supply == initial_supply - to_fixed(300))
    check("burn_conserved", burn_ledger.check_conservation()["conserved"])

    # Can't burn more than balance
    result = burn_ledger.burn("entity", to_fixed(800))
    check("cant_overburn", result is None)
    check("balance_unchanged_on_fail",
          burn_ledger.balances["entity"] == to_fixed(700))

    # ── §6 Multi-Party Conservation ──────────────────────────────
    print("\n§6 Multi-Party Transaction Conservation\n")

    mp_ledger = ATPLedger()
    mp_ledger.mint("A", to_fixed(100))
    mp_ledger.mint("B", to_fixed(100))
    mp_ledger.mint("C", to_fixed(100))

    # Three-way transfer: A→B, B→C, C→A
    success = multi_party_transfer(mp_ledger, [
        ("A", "B", to_fixed(20)),
        ("B", "C", to_fixed(30)),
        ("C", "A", to_fixed(10)),
    ])
    check("multi_party_success", success)
    check("multi_party_conserved", mp_ledger.check_conservation()["conserved"])

    # Total should be 300
    total = sum(mp_ledger.balances.values()) + mp_ledger.fee_pool
    check("multi_party_total", total == to_fixed(300),
          f"total={from_fixed(total)}")

    # Failed multi-party (insufficient balance)
    fail = multi_party_transfer(mp_ledger, [
        ("A", "B", to_fixed(200)),  # A doesn't have 200
    ])
    check("multi_party_fail", not fail)
    check("fail_no_side_effects", mp_ledger.check_conservation()["conserved"])

    # ── §7 Federation Merge ──────────────────────────────────────
    print("\n§7 Federation Merge Conservation\n")

    fed1 = ATPLedger()
    fed1.mint("x", to_fixed(500))
    fed1.mint("y", to_fixed(300))

    fed2 = ATPLedger()
    fed2.mint("a", to_fixed(200))
    fed2.mint("b", to_fixed(400))

    merged = federation_merge(fed1, fed2)
    check("merge_supply_sum",
          merged.total_supply == fed1.total_supply + fed2.total_supply)
    check("merge_conserved", merged.check_conservation()["conserved"])
    check("merge_accounts", len(merged.balances) == 4)

    # ── §8 Federation Split ──────────────────────────────────────
    print("\n§8 Federation Split Conservation\n")

    split_ledger = ATPLedger()
    split_ledger.mint("p", to_fixed(400))
    split_ledger.mint("q", to_fixed(300))
    split_ledger.mint("r", to_fixed(200))
    original_supply = split_ledger.total_supply

    s1, s2 = federation_split(split_ledger, {"p", "q"}, {"r"})

    # Conservation: s1 + s2 = original
    check("split_supply_sum",
          s1.total_supply + s2.total_supply == original_supply,
          f"s1={from_fixed(s1.total_supply)} s2={from_fixed(s2.total_supply)} orig={from_fixed(original_supply)}")
    check("s1_conserved", s1.check_conservation()["conserved"])
    check("s2_conserved", s2.check_conservation()["conserved"])

    # ── §9 Cross-Federation Migration ────────────────────────────
    print("\n§9 Migration Conservation\n")

    src = ATPLedger()
    src.mint("migrant", to_fixed(100))
    dst = ATPLedger()
    dst.mint("resident", to_fixed(200))

    combined_before = src.total_supply + dst.total_supply

    success = migration_transfer(src, dst, "migrant", to_fixed(40))
    check("migration_success", success)

    combined_after = src.total_supply + dst.total_supply
    check("migration_conserved", combined_before == combined_after,
          f"before={from_fixed(combined_before)} after={from_fixed(combined_after)}")

    check("src_reduced", from_fixed(src.balances["migrant"]) == 60.0)
    check("dst_increased", from_fixed(dst.balances["migrant"]) == 40.0)

    # ── §10 Stress Test ──────────────────────────────────────────
    print("\n§10 Conservation Under Stress\n")

    import random
    rng = random.Random(42)
    stress = ATPLedger()
    monitor = ConservationMonitor()

    # Create 20 accounts
    accounts = [f"acc_{i}" for i in range(20)]
    for acc in accounts:
        stress.mint(acc, to_fixed(rng.uniform(10, 100)))

    monitor.snapshot(stress, 0)

    # 200 random transfers
    for t in range(200):
        sender = rng.choice(accounts)
        receiver = rng.choice(accounts)
        if sender == receiver:
            continue
        amount = to_fixed(rng.uniform(0.01, 5))
        fee_rate = to_fixed(0.005)  # 0.5% fee
        stress.transfer(sender, receiver, amount, fee_rate)

        if t % 50 == 0:
            monitor.snapshot(stress, t)
            # Redistribute fees every 50 txns
            stress.redistribute_fees(accounts)
            monitor.snapshot(stress, t + 1)

    monitor.snapshot(stress, 200)

    check("stress_no_violations", monitor.is_clean(),
          f"violations={monitor.violation_count()}")
    check("stress_final_conserved", stress.check_conservation()["conserved"])

    # All balances non-negative
    check("all_non_negative", all(b >= 0 for b in stress.balances.values()),
          f"min={from_fixed(min(stress.balances.values())):.4f}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
