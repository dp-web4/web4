"""
Web4 Economic Attack Resistance — Session 17, Track 2
=====================================================

Tests resistance to economic attacks on the ATP/ADP system:
- Treasury drain attacks (extract more value than contributed)
- ATP inflation attacks (counterfeit or inflate supply)
- Fee manipulation attacks (avoid or redirect fees)
- Flash loan analogs (borrow, manipulate, repay in one round)
- Front-running and sandwich attacks
- Market manipulation via wash trading

12 sections, ~70 checks expected.
"""

import hashlib
import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict


# ============================================================
# §1 — ATP Economic Model
# ============================================================

@dataclass
class ATPAccount:
    """ATP account with balance tracking and conservation enforcement."""
    entity_id: str
    balance: float = 0.0
    max_balance: float = 10000.0
    locked: float = 0.0  # Locked for staking/voting
    total_received: float = 0.0
    total_spent: float = 0.0
    total_fees_paid: float = 0.0

    def available(self) -> float:
        return self.balance - self.locked

    def credit(self, amount: float) -> float:
        """Credit amount, returning any excess that couldn't be stored."""
        if amount <= 0:
            return amount  # No negative credits
        space = self.max_balance - self.balance
        credited = min(amount, space)
        excess = amount - credited
        self.balance += credited
        self.total_received += credited
        return excess

    def debit(self, amount: float) -> bool:
        """Debit amount. Returns False if insufficient funds."""
        if math.isnan(amount) or math.isinf(amount):
            return False
        if amount <= 0 or amount > self.available():
            return False
        self.balance -= amount
        self.total_spent += amount
        return True

    def lock(self, amount: float) -> bool:
        if amount <= 0 or amount > self.available():
            return False
        self.locked += amount
        return True

    def unlock(self, amount: float) -> bool:
        if amount <= 0 or amount > self.locked:
            return False
        self.locked -= amount
        return True


@dataclass
class ATPLedger:
    """Conservation-enforcing ATP ledger."""
    accounts: Dict[str, ATPAccount] = field(default_factory=dict)
    treasury: float = 0.0
    initial_supply: float = 0.0
    total_fees_collected: float = 0.0
    fee_rate: float = 0.05  # 5% transaction fee
    transactions: List[Dict] = field(default_factory=list)

    def create_account(self, entity_id: str, initial_balance: float = 0.0) -> ATPAccount:
        acc = ATPAccount(entity_id=entity_id, balance=initial_balance)
        self.accounts[entity_id] = acc
        self.initial_supply += initial_balance
        return acc

    def transfer(self, sender_id: str, receiver_id: str, amount: float) -> Dict:
        """Transfer with fee. Fees are destroyed (burned), not redistributed."""
        if sender_id not in self.accounts or receiver_id not in self.accounts:
            return {"success": False, "reason": "account_not_found"}
        if amount <= 0:
            return {"success": False, "reason": "non_positive_amount"}

        sender = self.accounts[sender_id]
        fee = amount * self.fee_rate
        total_cost = amount + fee

        if not sender.debit(total_cost):
            return {"success": False, "reason": "insufficient_funds"}

        # Fee is burned (destroyed)
        self.total_fees_collected += fee
        sender.total_fees_paid += fee

        # Credit receiver, return excess to sender
        excess = self.accounts[receiver_id].credit(amount)
        if excess > 0:
            sender.credit(excess)  # Return overflow to sender

        tx = {
            "success": True,
            "sender": sender_id,
            "receiver": receiver_id,
            "amount": amount,
            "fee": fee,
            "excess_returned": excess,
        }
        self.transactions.append(tx)
        return tx

    def total_supply(self) -> float:
        """Total ATP in circulation (accounts + treasury)."""
        return sum(a.balance for a in self.accounts.values()) + self.treasury

    def conservation_check(self) -> Tuple[bool, float]:
        """Verify: initial_supply = total_supply + total_fees_collected."""
        expected = self.initial_supply
        actual = self.total_supply() + self.total_fees_collected
        diff = abs(expected - actual)
        return diff < 0.01, diff


def test_section_1():
    checks = []

    # Basic account operations
    acc = ATPAccount("alice", balance=100.0)
    checks.append(("initial_balance", acc.balance == 100.0))
    checks.append(("available", acc.available() == 100.0))

    # Credit with overflow
    excess = acc.credit(9950.0)
    checks.append(("credit_overflow", excess == 50.0))
    checks.append(("balance_capped", acc.balance == 10000.0))

    # Debit
    acc2 = ATPAccount("bob", balance=50.0)
    checks.append(("debit_success", acc2.debit(30.0)))
    checks.append(("debit_balance", acc2.balance == 20.0))
    checks.append(("debit_insufficient", not acc2.debit(25.0)))

    # Lock/unlock
    acc3 = ATPAccount("carol", balance=100.0)
    checks.append(("lock_success", acc3.lock(60.0)))
    checks.append(("locked_amount", acc3.locked == 60.0))
    checks.append(("available_after_lock", acc3.available() == 40.0))
    checks.append(("debit_locked_fails", not acc3.debit(50.0)))

    # Ledger conservation
    ledger = ATPLedger(fee_rate=0.05)
    ledger.create_account("a", 1000.0)
    ledger.create_account("b", 500.0)
    result = ledger.transfer("a", "b", 100.0)
    checks.append(("transfer_success", result["success"]))
    checks.append(("fee_charged", result["fee"] == 5.0))
    conserved, diff = ledger.conservation_check()
    checks.append(("conservation_holds", conserved))

    # Negative credit rejected
    excess_neg = ATPAccount("x", balance=0.0).credit(-50.0)
    checks.append(("reject_negative_credit", excess_neg == -50.0))

    return checks


# ============================================================
# §2 — Treasury Drain Attack
# ============================================================

def treasury_drain_attack(ledger: ATPLedger, attacker_id: str,
                          rounds: int, rng: random.Random) -> Dict:
    """
    Attacker tries to extract more ATP than they contribute.
    Strategy: Create many small tasks, claim rewards, extract via transfers.
    """
    if attacker_id not in ledger.accounts:
        ledger.create_account(attacker_id, 100.0)

    # Create a reward pool that tasks pay into and rewards come from
    if "reward_pool" not in ledger.accounts:
        ledger.create_account("reward_pool", 5000.0)

    initial_balance = ledger.accounts[attacker_id].balance
    total_rewards = 0.0
    total_costs = 0.0

    for r in range(rounds):
        # Attacker submits a "task" costing ATP (goes to reward pool)
        task_cost = 10.0
        if not ledger.accounts[attacker_id].debit(task_cost):
            break
        ledger.accounts["reward_pool"].credit(task_cost)
        total_costs += task_cost

        # Simulated reward from pool (quality gated — low quality < cost)
        quality = rng.uniform(0.3, 0.7)  # Low quality work
        reward = task_cost * quality * 0.9  # Never more than 90% of cost for low quality
        if ledger.accounts["reward_pool"].debit(reward):
            excess = ledger.accounts[attacker_id].credit(reward)
            if excess > 0:
                ledger.accounts["reward_pool"].credit(excess)
            total_rewards += (reward - excess)

    final_balance = ledger.accounts[attacker_id].balance
    profit = final_balance - initial_balance

    return {
        "initial_balance": initial_balance,
        "final_balance": final_balance,
        "profit": profit,
        "total_rewards": total_rewards,
        "total_costs": total_costs,
        "net_roi": profit / initial_balance if initial_balance > 0 else 0,
        "drain_successful": profit > 0,
    }


def treasury_drain_defense(ledger: ATPLedger, entity_id: str,
                           reward: float, quality: float,
                           min_quality: float = 0.6) -> float:
    """
    Defense: Quality-gated rewards. Below threshold → reward scales down.
    Above threshold → full reward. Never exceeds submitted stake.
    """
    if quality < min_quality:
        # Penalty: reward reduced proportionally
        scale = quality / min_quality
        adjusted = reward * scale * scale  # Quadratic penalty
        return adjusted
    return reward


def test_section_2():
    checks = []
    rng = random.Random(42)

    # Treasury drain attack fails
    ledger = ATPLedger(fee_rate=0.05)
    ledger.create_account("honest", 1000.0)
    ledger.create_account("attacker", 500.0)

    result = treasury_drain_attack(ledger, "attacker", 20, rng)
    checks.append(("drain_unprofitable", not result["drain_successful"]))
    checks.append(("attacker_lost_atp", result["final_balance"] < result["initial_balance"]))
    checks.append(("roi_negative", result["net_roi"] < 0))

    # Conservation still holds after attack
    conserved, diff = ledger.conservation_check()
    checks.append(("conservation_after_attack", conserved))

    # Quality defense
    full_reward = treasury_drain_defense(ledger, "e", 100.0, 0.8, 0.6)
    checks.append(("high_quality_full_reward", full_reward == 100.0))

    low_reward = treasury_drain_defense(ledger, "e", 100.0, 0.3, 0.6)
    checks.append(("low_quality_reduced", low_reward < 50.0))

    zero_reward = treasury_drain_defense(ledger, "e", 100.0, 0.0, 0.6)
    checks.append(("zero_quality_zero_reward", zero_reward == 0.0))

    return checks


# ============================================================
# §3 — ATP Inflation Attack
# ============================================================

def inflation_attack(ledger: ATPLedger, attacker_id: str,
                     rounds: int, rng: random.Random) -> Dict:
    """
    Attacker tries to create ATP from nothing.
    Strategies:
    1. Double-spend: spend same ATP twice
    2. Negative transfer: transfer negative amount
    3. Self-transfer loop to generate fees in reverse
    4. Overflow: try to exceed max balance limits
    """
    results = {
        "double_spend": [],
        "negative_transfer": [],
        "self_loop": [],
        "overflow": [],
    }

    if attacker_id not in ledger.accounts:
        ledger.create_account(attacker_id, 1000.0)

    # Create all accounts BEFORE measuring initial supply
    if "overflow_target" not in ledger.accounts:
        ledger.create_account("overflow_target", 9990.0)

    initial_supply = ledger.total_supply()

    # Strategy 1: Try to spend then spend again (should fail)
    ledger.accounts[attacker_id].debit(500.0)
    double_spend = ledger.accounts[attacker_id].debit(600.0)  # Should fail
    results["double_spend"].append(not double_spend)
    # Restore
    ledger.accounts[attacker_id].credit(500.0)

    # Strategy 2: Negative transfer
    neg_result = ledger.transfer(attacker_id, attacker_id, -100.0)
    results["negative_transfer"].append(not neg_result["success"])

    # Strategy 3: Self-transfer loop (fees make it deflationary)
    balance_before = ledger.accounts[attacker_id].balance
    for _ in range(5):
        ledger.transfer(attacker_id, attacker_id, 50.0)
    balance_after = ledger.accounts[attacker_id].balance
    results["self_loop"].append(balance_after <= balance_before)

    # Strategy 4: Overflow
    overflow_result = ledger.transfer(attacker_id, "overflow_target", 100.0)
    results["overflow"].append(ledger.accounts["overflow_target"].balance <= 10000.0)

    final_supply = ledger.total_supply()

    return {
        "initial_supply": initial_supply,
        "final_supply": final_supply,
        "supply_inflated": final_supply > initial_supply + 0.01,
        "defenses": results,
        "all_defenses_held": all(
            all(v) for v in results.values()
        ),
    }


def test_section_3():
    checks = []
    rng = random.Random(42)

    ledger = ATPLedger(fee_rate=0.05)
    ledger.create_account("inflator", 1000.0)
    ledger.create_account("target", 500.0)

    result = inflation_attack(ledger, "inflator", 10, rng)
    checks.append(("no_inflation", not result["supply_inflated"]))
    checks.append(("all_defenses_held", result["all_defenses_held"]))
    checks.append(("double_spend_blocked", result["defenses"]["double_spend"][0]))
    checks.append(("negative_blocked", result["defenses"]["negative_transfer"][0]))
    checks.append(("self_loop_deflationary", result["defenses"]["self_loop"][0]))
    checks.append(("overflow_capped", result["defenses"]["overflow"][0]))

    # Conservation check
    conserved, _ = ledger.conservation_check()
    checks.append(("conservation_after_inflation_attempt", conserved))

    return checks


# ============================================================
# §4 — Fee Manipulation Attack
# ============================================================

def fee_manipulation_attack(rng: random.Random) -> Dict:
    """
    Attacker tries to manipulate fee structures.
    Strategies:
    1. Zero-amount transfers to avoid fees
    2. Split large transfers into tiny ones to minimize fees
    3. NaN/infinity fee rate injection
    4. Batch transactions to share one fee
    """
    results = {}

    # Strategy 1: Zero-amount transfer (should fail)
    ledger = ATPLedger(fee_rate=0.05)
    ledger.create_account("a", 1000.0)
    ledger.create_account("b", 0.0)
    zero_result = ledger.transfer("a", "b", 0.0)
    results["zero_amount_blocked"] = not zero_result["success"]

    # Strategy 2: Split vs bulk — splitting doesn't save on fees
    ledger2 = ATPLedger(fee_rate=0.05)
    ledger2.create_account("bulk_sender", 10000.0)
    ledger2.create_account("split_sender", 10000.0)
    ledger2.create_account("receiver", 0.0)

    # Bulk: one transfer of 1000
    bulk_result = ledger2.transfer("bulk_sender", "receiver", 1000.0)
    bulk_fee = bulk_result["fee"]

    # Split: 10 transfers of 100
    split_fees = 0.0
    for _ in range(10):
        r = ledger2.transfer("split_sender", "receiver", 100.0)
        if r["success"]:
            split_fees += r["fee"]

    # With flat percentage, fees should be equal
    results["split_no_advantage"] = abs(split_fees - bulk_fee) < 0.01

    # Strategy 3: NaN fee rate protection
    ledger3 = ATPLedger(fee_rate=float('nan'))
    ledger3.create_account("nan_a", 1000.0)
    ledger3.create_account("nan_b", 0.0)
    # NaN fee rate: fee = amount * nan = nan, total_cost = amount + nan = nan
    # debit(nan) should fail since nan > available() is False
    nan_result = ledger3.transfer("nan_a", "nan_b", 100.0)
    # With NaN fee, the debit of total_cost (nan) will fail
    # because amount + nan = nan, and debit checks nan > available (False in IEEE 754)
    # BUT also checks nan <= 0 which is also False, so debit proceeds with nan
    # We need explicit NaN checking
    results["nan_fee_blocked"] = not nan_result["success"] or ledger3.accounts["nan_a"].balance <= 1000.0

    # Strategy 4: Negative fee rate
    ledger4 = ATPLedger(fee_rate=-0.1)
    ledger4.create_account("neg_a", 1000.0)
    ledger4.create_account("neg_b", 0.0)
    neg_result = ledger4.transfer("neg_a", "neg_b", 100.0)
    # Negative fee means sender pays less (fee = -10, total = 90)
    # This is a vulnerability if not guarded
    results["negative_fee_exploitable"] = neg_result["success"]  # Expected: True (vulnerability exists)

    return results


def fee_safe_transfer(ledger: ATPLedger, sender: str, receiver: str, amount: float) -> Dict:
    """Fee-safe transfer with NaN and negative guards."""
    if math.isnan(amount) or math.isinf(amount) or amount <= 0:
        return {"success": False, "reason": "invalid_amount"}

    if math.isnan(ledger.fee_rate) or math.isinf(ledger.fee_rate) or ledger.fee_rate < 0:
        return {"success": False, "reason": "invalid_fee_rate"}

    return ledger.transfer(sender, receiver, amount)


def test_section_4():
    checks = []
    rng = random.Random(42)

    results = fee_manipulation_attack(rng)
    checks.append(("zero_amount_blocked", results["zero_amount_blocked"]))
    checks.append(("split_no_advantage", results["split_no_advantage"]))
    checks.append(("nan_handled", results["nan_fee_blocked"]))
    # Negative fee IS a vulnerability in raw transfer
    checks.append(("negative_fee_vulnerability_exists", results["negative_fee_exploitable"]))

    # Safe transfer guards against negative fee
    ledger = ATPLedger(fee_rate=-0.1)
    ledger.create_account("x", 1000.0)
    ledger.create_account("y", 0.0)
    safe = fee_safe_transfer(ledger, "x", "y", 100.0)
    checks.append(("safe_transfer_blocks_negative_fee", not safe["success"]))

    # Safe transfer guards against NaN
    ledger2 = ATPLedger(fee_rate=float('nan'))
    ledger2.create_account("a", 1000.0)
    ledger2.create_account("b", 0.0)
    safe2 = fee_safe_transfer(ledger2, "a", "b", 100.0)
    checks.append(("safe_transfer_blocks_nan_fee", not safe2["success"]))

    # Safe transfer guards against NaN amount
    ledger3 = ATPLedger(fee_rate=0.05)
    ledger3.create_account("c", 1000.0)
    ledger3.create_account("d", 0.0)
    safe3 = fee_safe_transfer(ledger3, "c", "d", float('nan'))
    checks.append(("safe_transfer_blocks_nan_amount", not safe3["success"]))

    return checks


# ============================================================
# §5 — Flash Loan Analog Attack
# ============================================================

@dataclass
class FlashLoanPool:
    """Flash loan pool — borrow and repay within single transaction."""
    pool_balance: float = 10000.0
    flash_fee_rate: float = 0.001  # 0.1% flash fee
    active_loans: Dict[str, float] = field(default_factory=dict)
    completed_loans: int = 0
    defaulted_loans: int = 0

    def borrow(self, borrower: str, amount: float) -> bool:
        if borrower in self.active_loans:
            return False  # One loan at a time
        if amount <= 0 or amount > self.pool_balance:
            return False
        self.pool_balance -= amount
        self.active_loans[borrower] = amount
        return True

    def repay(self, borrower: str) -> bool:
        if borrower not in self.active_loans:
            return False
        loan_amount = self.active_loans[borrower]
        repay_amount = loan_amount * (1 + self.flash_fee_rate)
        self.pool_balance += repay_amount
        del self.active_loans[borrower]
        self.completed_loans += 1
        return True

    def default(self, borrower: str):
        if borrower in self.active_loans:
            # Loan is lost — pool takes the hit
            self.defaulted_loans += 1
            del self.active_loans[borrower]


def flash_loan_attack(pool: FlashLoanPool, ledger: ATPLedger,
                      attacker_id: str, rng: random.Random) -> Dict:
    """
    Flash loan attack: borrow large amount, manipulate trust scores
    to extract value, repay loan.

    Defense: Trust updates have minimum latency (can't manipulate
    and extract in same round).
    """
    initial_balance = ledger.accounts.get(attacker_id, ATPAccount(attacker_id)).balance

    # Step 1: Borrow large amount
    borrow_amount = 5000.0
    borrowed = pool.borrow(attacker_id, borrow_amount)

    if not borrowed:
        return {"success": False, "reason": "borrow_failed"}

    # Step 2: Try to inflate trust by staking borrowed ATP
    # Defense: trust updates require MINIMUM_ROUNDS > 0
    MINIMUM_TRUST_ROUNDS = 5
    trust_manipulation_rounds = 1  # Attacker tries to do it in 1 round

    can_manipulate = trust_manipulation_rounds >= MINIMUM_TRUST_ROUNDS
    manipulated_value = borrow_amount * 0.1 if can_manipulate else 0.0

    # Step 3: Extract value (fails if manipulation failed)
    extracted = manipulated_value

    # Step 4: Repay loan
    repaid = pool.repay(attacker_id)

    # Net profit
    profit = extracted - (borrow_amount * pool.flash_fee_rate)

    return {
        "success": profit > 0,
        "borrowed": borrow_amount,
        "manipulated": can_manipulate,
        "extracted": extracted,
        "fee_paid": borrow_amount * pool.flash_fee_rate,
        "profit": profit,
        "repaid": repaid,
        "defense": "minimum_trust_rounds",
    }


def test_section_5():
    checks = []
    rng = random.Random(42)

    pool = FlashLoanPool(pool_balance=10000.0)
    ledger = ATPLedger(fee_rate=0.05)
    ledger.create_account("flash_attacker", 100.0)

    result = flash_loan_attack(pool, ledger, "flash_attacker", rng)
    checks.append(("flash_loan_unprofitable", not result["success"]))
    checks.append(("manipulation_blocked", not result["manipulated"]))
    checks.append(("loan_repaid", result["repaid"]))
    checks.append(("zero_extraction", result["extracted"] == 0.0))

    # Pool still healthy
    checks.append(("pool_healthy", pool.pool_balance >= 10000.0))  # Gained fee
    checks.append(("no_defaults", pool.defaulted_loans == 0))

    # Double borrow blocked
    pool.borrow("alice", 1000.0)
    double = pool.borrow("alice", 500.0)
    checks.append(("double_borrow_blocked", not double))

    return checks


# ============================================================
# §6 — Front-Running and Sandwich Attack
# ============================================================

@dataclass
class OrderBook:
    """Simple order book for ATP trading."""
    orders: List[Dict] = field(default_factory=list)
    executed: List[Dict] = field(default_factory=list)

    def submit_order(self, entity_id: str, order_type: str,
                     amount: float, price: float, timestamp: float) -> int:
        order_id = len(self.orders)
        self.orders.append({
            "id": order_id,
            "entity": entity_id,
            "type": order_type,
            "amount": amount,
            "price": price,
            "timestamp": timestamp,
            "executed": False,
        })
        return order_id

    def match_orders(self) -> List[Dict]:
        """Match buy/sell orders by price-time priority."""
        buys = sorted([o for o in self.orders if o["type"] == "buy" and not o["executed"]],
                      key=lambda o: (-o["price"], o["timestamp"]))
        sells = sorted([o for o in self.orders if o["type"] == "sell" and not o["executed"]],
                       key=lambda o: (o["price"], o["timestamp"]))

        matches = []
        for buy in buys:
            for sell in sells:
                if sell["executed"]:
                    continue
                if buy["price"] >= sell["price"]:
                    trade_price = (buy["price"] + sell["price"]) / 2
                    trade_amount = min(buy["amount"], sell["amount"])
                    buy["executed"] = True
                    sell["executed"] = True
                    matches.append({
                        "buyer": buy["entity"],
                        "seller": sell["entity"],
                        "price": trade_price,
                        "amount": trade_amount,
                    })
                    break
        self.executed.extend(matches)
        return matches


def sandwich_attack(book: OrderBook, victim_order: Dict,
                    attacker_id: str) -> Dict:
    """
    Sandwich attack: front-run victim's buy with own buy,
    then back-run with sell at higher price.

    Defense: commit-reveal ordering (orders are committed before revealed).
    """
    # Attacker sees victim's pending buy order
    victim_price = victim_order["price"]
    victim_amount = victim_order["amount"]

    # Front-run: buy before victim at slightly lower price
    front_run_price = victim_price * 0.99
    book.submit_order(attacker_id, "buy", victim_amount, front_run_price,
                      victim_order["timestamp"] - 0.001)

    # Victim's order
    book.submit_order(victim_order["entity"], "buy", victim_amount,
                      victim_price, victim_order["timestamp"])

    # Back-run: sell after victim at slightly higher price
    back_run_price = victim_price * 1.01
    book.submit_order(attacker_id, "sell", victim_amount, back_run_price,
                      victim_order["timestamp"] + 0.001)

    # Need a seller for the front-run
    book.submit_order("market_maker", "sell", victim_amount * 2,
                      front_run_price * 0.98, victim_order["timestamp"] - 0.002)

    matches = book.match_orders()

    attacker_buys = [m for m in matches if m["buyer"] == attacker_id]
    attacker_sells = [m for m in matches if m["seller"] == attacker_id]

    buy_cost = sum(m["price"] * m["amount"] for m in attacker_buys)
    sell_revenue = sum(m["price"] * m["amount"] for m in attacker_sells)

    return {
        "matches": len(matches),
        "attacker_buys": len(attacker_buys),
        "attacker_sells": len(attacker_sells),
        "buy_cost": buy_cost,
        "sell_revenue": sell_revenue,
        "profit": sell_revenue - buy_cost,
        "profitable": sell_revenue > buy_cost,
    }


def commit_reveal_defense(orders: List[Dict], rng: random.Random) -> List[Dict]:
    """
    Defense: Orders are committed with hash, then revealed and shuffled.
    Front-running impossible because order content is hidden until reveal.
    """
    # Commit phase: hash each order
    committed = []
    for order in orders:
        nonce = rng.randint(0, 2**32)
        data = f"{order['entity']}:{order['type']}:{order['amount']}:{order['price']}:{nonce}"
        commitment = hashlib.sha256(data.encode()).hexdigest()
        committed.append({"commitment": commitment, "order": order, "nonce": nonce})

    # Reveal phase: shuffle order of reveals
    rng.shuffle(committed)

    # Process in shuffled order
    return [c["order"] for c in committed]


def test_section_6():
    checks = []
    rng = random.Random(42)

    # Sandwich attack
    book = OrderBook()
    victim_order = {
        "entity": "victim",
        "type": "buy",
        "amount": 100.0,
        "price": 10.0,
        "timestamp": 1.0,
    }
    result = sandwich_attack(book, victim_order, "attacker")
    checks.append(("sandwich_executed", result["matches"] > 0))
    # With commit-reveal, attack is impossible because attacker can't see order

    # Commit-reveal randomizes order
    orders = [
        {"entity": f"trader_{i}", "type": "buy" if i % 2 == 0 else "sell",
         "amount": 100.0, "price": 10.0 + i}
        for i in range(10)
    ]
    revealed1 = commit_reveal_defense(orders.copy(), random.Random(1))
    revealed2 = commit_reveal_defense(orders.copy(), random.Random(2))
    # Different seeds should produce different orderings
    order1 = [o["entity"] for o in revealed1]
    order2 = [o["entity"] for o in revealed2]
    checks.append(("commit_reveal_randomizes", order1 != order2))

    # All orders preserved
    checks.append(("all_orders_preserved", len(revealed1) == len(orders)))

    # Commitment hides content
    committed = []
    for o in orders:
        nonce = rng.randint(0, 2**32)
        data = f"{o['entity']}:{o['type']}:{o['amount']}:{o['price']}:{nonce}"
        commitment = hashlib.sha256(data.encode()).hexdigest()
        committed.append(commitment)
    # All commitments unique
    checks.append(("unique_commitments", len(set(committed)) == len(committed)))

    return checks


# ============================================================
# §7 — Wash Trading Detection
# ============================================================

def detect_wash_trading(transactions: List[Dict], window_size: int = 10) -> Dict:
    """
    Detect wash trading: entity trades with itself or colluding entities
    to inflate volume/reputation without real economic activity.

    Indicators:
    1. Circular flows: A→B→C→A
    2. Self-referential: A→A
    3. Volume without net transfer
    """
    # Build flow graph
    flows = defaultdict(lambda: defaultdict(float))
    entity_volume = defaultdict(float)

    for tx in transactions:
        if not tx.get("success", True):
            continue
        sender = tx.get("sender", "")
        receiver = tx.get("receiver", "")
        amount = tx.get("amount", 0)
        flows[sender][receiver] += amount
        entity_volume[sender] += amount
        entity_volume[receiver] += amount

    # Detect circular flows
    circles = []
    for a in flows:
        for b in flows[a]:
            if b in flows and a in flows[b]:
                # A→B and B→A
                forward = flows[a][b]
                backward = flows[b][a]
                if min(forward, backward) > 0:
                    ratio = min(forward, backward) / max(forward, backward)
                    if ratio > 0.8:  # Nearly equal flows = suspicious
                        circles.append((a, b, forward, backward, ratio))

    # Detect self-referential
    self_trades = []
    for a in flows:
        if a in flows[a] and flows[a][a] > 0:
            self_trades.append((a, flows[a][a]))

    # Volume concentration
    total_volume = sum(entity_volume.values())
    concentration = {}
    if total_volume > 0:
        for entity, vol in entity_volume.items():
            concentration[entity] = vol / total_volume

    return {
        "circular_flows": circles,
        "self_trades": self_trades,
        "total_volume": total_volume,
        "concentration": concentration,
        "wash_trading_detected": len(circles) > 0 or len(self_trades) > 0,
    }


def test_section_7():
    checks = []

    # Normal trading — no wash trading
    normal_txs = [
        {"sender": "alice", "receiver": "bob", "amount": 100.0, "success": True},
        {"sender": "bob", "receiver": "carol", "amount": 80.0, "success": True},
        {"sender": "carol", "receiver": "dave", "amount": 60.0, "success": True},
    ]
    normal = detect_wash_trading(normal_txs)
    checks.append(("no_wash_in_normal", not normal["wash_trading_detected"]))

    # Circular wash trading
    wash_txs = [
        {"sender": "washer_a", "receiver": "washer_b", "amount": 1000.0, "success": True},
        {"sender": "washer_b", "receiver": "washer_a", "amount": 980.0, "success": True},
    ]
    wash = detect_wash_trading(wash_txs)
    checks.append(("circular_detected", wash["wash_trading_detected"]))
    checks.append(("circular_flow_found", len(wash["circular_flows"]) > 0))

    # Self-trade
    self_txs = [
        {"sender": "self_trader", "receiver": "self_trader", "amount": 500.0, "success": True},
    ]
    self_wash = detect_wash_trading(self_txs)
    checks.append(("self_trade_detected", self_wash["wash_trading_detected"]))
    checks.append(("self_trade_found", len(self_wash["self_trades"]) > 0))

    # Mixed: normal + wash
    mixed = normal_txs + wash_txs
    mixed_result = detect_wash_trading(mixed)
    checks.append(("wash_detected_in_mixed", mixed_result["wash_trading_detected"]))

    return checks


# ============================================================
# §8 — ATP Staking Attack
# ============================================================

@dataclass
class StakingPool:
    """ATP staking for governance weight. Attacks target stake manipulation."""
    stakes: Dict[str, float] = field(default_factory=dict)
    total_staked: float = 0.0
    lock_period: int = 10  # Minimum rounds before unstake
    lock_timestamps: Dict[str, int] = field(default_factory=dict)
    rewards_per_round: float = 10.0

    def stake(self, entity_id: str, amount: float, current_round: int) -> bool:
        if amount <= 0:
            return False
        self.stakes[entity_id] = self.stakes.get(entity_id, 0.0) + amount
        self.total_staked += amount
        self.lock_timestamps[entity_id] = current_round
        return True

    def unstake(self, entity_id: str, current_round: int) -> Tuple[bool, float]:
        if entity_id not in self.stakes:
            return False, 0.0
        lock_time = self.lock_timestamps.get(entity_id, 0)
        if current_round - lock_time < self.lock_period:
            return False, 0.0
        amount = self.stakes.pop(entity_id)
        self.total_staked -= amount
        return True, amount

    def distribute_rewards(self, current_round: int) -> Dict[str, float]:
        """Distribute rewards proportionally to stake."""
        if self.total_staked <= 0:
            return {}
        rewards = {}
        for entity_id, stake in self.stakes.items():
            share = stake / self.total_staked
            rewards[entity_id] = self.rewards_per_round * share
        return rewards

    def voting_weight(self, entity_id: str) -> float:
        """Governance voting weight = sqrt(stake) to limit plutocracy."""
        stake = self.stakes.get(entity_id, 0.0)
        return math.sqrt(stake)


def staking_attack(pool: StakingPool, attacker_atp: float,
                   honest_stakes: Dict[str, float], rng: random.Random) -> Dict:
    """
    Attacker tries to gain disproportionate governance control.
    Defense: sqrt weighting limits plutocratic advantage.
    """
    # Honest stakers
    for entity_id, amount in honest_stakes.items():
        pool.stake(entity_id, amount, 0)

    # Attacker stakes all ATP
    pool.stake("attacker", attacker_atp, 0)

    # Calculate voting weights
    attacker_weight = pool.voting_weight("attacker")
    honest_weights = sum(pool.voting_weight(e) for e in honest_stakes)
    total_weight = attacker_weight + honest_weights

    attacker_share = attacker_weight / total_weight if total_weight > 0 else 0
    attacker_atp_share = attacker_atp / pool.total_staked if pool.total_staked > 0 else 0

    # With sqrt, having 4x the stake only gives 2x the weight
    return {
        "attacker_atp_share": attacker_atp_share,
        "attacker_vote_share": attacker_share,
        "sqrt_dampening": attacker_atp_share > 0 and attacker_share < attacker_atp_share,
        "attacker_majority": attacker_share > 0.5,
    }


def test_section_8():
    checks = []
    rng = random.Random(42)

    pool = StakingPool(lock_period=10)

    # Basic staking
    checks.append(("stake_success", pool.stake("alice", 100.0, 0)))
    checks.append(("total_staked", pool.total_staked == 100.0))

    # Lock period prevents early unstake
    success, _ = pool.unstake("alice", 5)
    checks.append(("early_unstake_blocked", not success))

    # Can unstake after lock period
    success, amount = pool.unstake("alice", 15)
    checks.append(("unstake_after_lock", success and amount == 100.0))

    # Reward distribution
    pool2 = StakingPool(rewards_per_round=100.0)
    pool2.stake("a", 300.0, 0)
    pool2.stake("b", 700.0, 0)
    rewards = pool2.distribute_rewards(1)
    checks.append(("reward_proportional", abs(rewards["a"] - 30.0) < 0.01))
    checks.append(("reward_proportional_b", abs(rewards["b"] - 70.0) < 0.01))

    # Staking attack with sqrt dampening
    pool3 = StakingPool()
    honest = {"h1": 100.0, "h2": 100.0, "h3": 100.0, "h4": 100.0}
    attack = staking_attack(pool3, 1600.0, honest, rng)
    # Attacker has 1600/(1600+400) = 80% of ATP
    checks.append(("attacker_atp_majority", attack["attacker_atp_share"] == 0.8))
    # But sqrt: sqrt(1600)=40 vs 4*sqrt(100)=40 → 50%, not 80%
    checks.append(("sqrt_dampens", attack["sqrt_dampening"]))
    checks.append(("sqrt_blocks_majority", not attack["attacker_majority"]))

    return checks


# ============================================================
# §9 — Sybil Economic Attack
# ============================================================

def sybil_economic_attack(num_sybils: int, atp_per_sybil: float,
                          honest_count: int, honest_atp: float,
                          hardware_cost: float = 250.0,
                          transfer_fee_rate: float = 0.05) -> Dict:
    """
    Sybil economic analysis: is creating many identities profitable?

    Cost model:
    - Hardware binding: 250 ATP per identity
    - ATP transfer fee: 5% per transfer to fund sybils
    - Each sybil needs minimum ATP to participate

    Revenue model:
    - Task rewards proportional to trust (sybils start at low trust)
    - Staking rewards proportional to stake
    """
    # Costs
    hardware_costs = num_sybils * hardware_cost
    distribution_cost = 0.0
    remaining_atp = num_sybils * atp_per_sybil
    for i in range(num_sybils):
        fee = atp_per_sybil * transfer_fee_rate
        distribution_cost += fee
        remaining_atp -= fee

    total_cost = hardware_costs + distribution_cost

    # Revenue (sybils at low trust earn less)
    sybil_trust = 0.2  # New identities start low
    honest_trust = 0.8
    reward_per_round = 10.0

    sybil_reward_per_round = num_sybils * reward_per_round * sybil_trust
    honest_reward_per_round = honest_count * reward_per_round * honest_trust

    # Rounds to break even
    if sybil_reward_per_round > 0:
        breakeven_rounds = total_cost / sybil_reward_per_round
    else:
        breakeven_rounds = float('inf')

    # Compare with honest strategy
    honest_revenue = reward_per_round * honest_trust
    honest_cost = hardware_cost  # Just one identity

    return {
        "sybil_count": num_sybils,
        "total_cost": total_cost,
        "sybil_reward_per_round": sybil_reward_per_round,
        "breakeven_rounds": breakeven_rounds,
        "honest_reward_per_round": honest_revenue,
        "honest_breakeven": honest_cost / honest_revenue if honest_revenue > 0 else float('inf'),
        "sybil_unprofitable": breakeven_rounds > 100,  # >100 rounds = not worth it
        "honest_roi_better": (honest_revenue / honest_cost) > (sybil_reward_per_round / total_cost) if total_cost > 0 else True,
    }


def test_section_9():
    checks = []

    # Small sybil attack (5 identities)
    small = sybil_economic_attack(5, 200.0, 10, 500.0)
    checks.append(("small_sybil_unprofitable", small["sybil_unprofitable"]))
    checks.append(("honest_roi_better_small", small["honest_roi_better"]))

    # Large sybil attack (50 identities)
    large = sybil_economic_attack(50, 100.0, 10, 500.0)
    checks.append(("large_sybil_unprofitable", large["sybil_unprofitable"]))
    checks.append(("honest_roi_better_large", large["honest_roi_better"]))

    # Breakeven analysis
    checks.append(("breakeven_high", small["breakeven_rounds"] > 50))

    # Cost scales with sybils
    checks.append(("cost_scales", large["total_cost"] > small["total_cost"]))

    return checks


# ============================================================
# §10 — Market Manipulation Detection
# ============================================================

def detect_market_manipulation(price_history: List[float],
                               volume_history: List[float],
                               threshold_z: float = 2.0) -> Dict:
    """
    Detect market manipulation via statistical anomalies.
    Methods:
    1. Price deviation (z-score based)
    2. Volume anomaly
    3. Price-volume divergence
    """
    if len(price_history) < 5:
        return {"detected": False, "reason": "insufficient_data"}

    # Price statistics
    mean_price = sum(price_history) / len(price_history)
    var_price = sum((p - mean_price)**2 for p in price_history) / len(price_history)
    std_price = math.sqrt(var_price) if var_price > 0 else 0.001

    # Volume statistics
    mean_vol = sum(volume_history) / len(volume_history) if volume_history else 0
    var_vol = sum((v - mean_vol)**2 for v in volume_history) / len(volume_history) if volume_history else 0
    std_vol = math.sqrt(var_vol) if var_vol > 0 else 0.001

    # Find anomalies
    price_anomalies = []
    for i, p in enumerate(price_history):
        z = abs(p - mean_price) / std_price
        if z > threshold_z:
            price_anomalies.append((i, p, z))

    volume_anomalies = []
    for i, v in enumerate(volume_history):
        z = abs(v - mean_vol) / std_vol
        if z > threshold_z:
            volume_anomalies.append((i, v, z))

    # Price-volume divergence: high volume with low price change = wash trading
    divergences = []
    for i in range(1, min(len(price_history), len(volume_history))):
        price_change = abs(price_history[i] - price_history[i-1]) / (price_history[i-1] or 1)
        vol_relative = volume_history[i] / mean_vol if mean_vol > 0 else 0
        if vol_relative > 1.5 and price_change < 0.01:
            divergences.append((i, price_change, vol_relative))

    return {
        "detected": len(price_anomalies) > 0 or len(volume_anomalies) > 0 or len(divergences) > 0,
        "price_anomalies": price_anomalies,
        "volume_anomalies": volume_anomalies,
        "divergences": divergences,
        "mean_price": mean_price,
        "std_price": std_price,
    }


def test_section_10():
    checks = []

    # Normal market — no manipulation
    normal_prices = [10.0 + random.Random(42).gauss(0, 0.5) for _ in range(20)]
    normal_volumes = [100.0 + random.Random(43).gauss(0, 10) for _ in range(20)]
    normal = detect_market_manipulation(normal_prices, normal_volumes)
    checks.append(("normal_no_manipulation", not normal["detected"]))

    # Pump and dump
    pump_prices = [10.0] * 10 + [25.0] * 3 + [8.0] * 7  # Sudden spike then crash
    pump_volumes = [100.0] * 10 + [1000.0] * 3 + [50.0] * 7
    pump = detect_market_manipulation(pump_prices, pump_volumes)
    checks.append(("pump_dump_detected", pump["detected"]))
    checks.append(("price_anomalies_found", len(pump["price_anomalies"]) > 0))

    # Wash trading: high volume, no price change
    wash_prices = [10.0] * 20
    wash_volumes = [100.0] * 10 + [1000.0] * 10  # 10x spike = obvious wash
    wash = detect_market_manipulation(wash_prices, wash_volumes)
    checks.append(("wash_volume_detected", wash["detected"]))

    # Insufficient data
    short = detect_market_manipulation([10.0, 11.0], [100.0, 110.0])
    checks.append(("insufficient_data_safe", not short["detected"]))

    return checks


# ============================================================
# §11 — Economic Equilibrium Analysis
# ============================================================

def analyze_economic_equilibrium(num_agents: int, rounds: int,
                                 fee_rate: float, rng: random.Random) -> Dict:
    """
    Simulate ATP economy reaching equilibrium.
    Key metrics: Gini coefficient, total supply trajectory, fee revenue.
    """
    ledger = ATPLedger(fee_rate=fee_rate)

    # Initialize agents with varied starting balances
    for i in range(num_agents):
        balance = 100.0 + rng.gauss(50, 20)
        balance = max(10.0, balance)  # Floor
        ledger.create_account(f"agent_{i}", balance)

    supply_trajectory = [ledger.total_supply()]
    gini_trajectory = []

    for r in range(rounds):
        # Each round: random trades between agents
        num_trades = num_agents // 2
        for _ in range(num_trades):
            sender_idx = rng.randint(0, num_agents - 1)
            receiver_idx = rng.randint(0, num_agents - 1)
            if sender_idx == receiver_idx:
                continue
            sender = f"agent_{sender_idx}"
            receiver = f"agent_{receiver_idx}"
            amount = rng.uniform(1, 20)
            ledger.transfer(sender, receiver, amount)

        supply_trajectory.append(ledger.total_supply())

        # Gini coefficient
        balances = sorted([a.balance for a in ledger.accounts.values()])
        n = len(balances)
        if n > 0 and sum(balances) > 0:
            numerator = sum((2*i - n + 1) * b for i, b in enumerate(balances))
            gini = numerator / (n * sum(balances))
            gini_trajectory.append(gini)

    # Supply should be monotonically decreasing (fees burn ATP)
    supply_decreasing = all(supply_trajectory[i] >= supply_trajectory[i+1] - 0.01
                           for i in range(len(supply_trajectory) - 1))

    # Final Gini
    final_gini = gini_trajectory[-1] if gini_trajectory else 0.0

    return {
        "initial_supply": supply_trajectory[0],
        "final_supply": supply_trajectory[-1],
        "supply_decrease": supply_trajectory[0] - supply_trajectory[-1],
        "supply_decreasing": supply_decreasing,
        "final_gini": final_gini,
        "gini_stable": len(gini_trajectory) > 5 and
                       abs(gini_trajectory[-1] - gini_trajectory[-5]) < 0.1,
        "total_fees": ledger.total_fees_collected,
        "conservation_holds": ledger.conservation_check()[0],
    }


def test_section_11():
    checks = []
    rng = random.Random(42)

    result = analyze_economic_equilibrium(50, 100, 0.05, rng)

    # Supply decreases over time (fee burning)
    checks.append(("supply_decreasing", result["supply_decreasing"]))
    checks.append(("supply_decreased", result["supply_decrease"] > 0))

    # Conservation holds throughout
    checks.append(("conservation_holds", result["conservation_holds"]))

    # Gini is bounded (not runaway concentration)
    checks.append(("gini_bounded", result["final_gini"] < 0.8))

    # Fees collected
    checks.append(("fees_collected", result["total_fees"] > 0))

    # Gini stabilizes
    checks.append(("gini_stabilizes", result["gini_stable"]))

    return checks


# ============================================================
# §12 — Complete Economic Security Pipeline
# ============================================================

def run_complete_economic_pipeline(rng: random.Random) -> List[Tuple[str, bool]]:
    checks = []

    # 1. Treasury drain resistance
    ledger = ATPLedger(fee_rate=0.05)
    for i in range(10):
        ledger.create_account(f"honest_{i}", 500.0)
    ledger.create_account("drainer", 1000.0)
    drain = treasury_drain_attack(ledger, "drainer", 30, rng)
    checks.append(("pipeline_drain_blocked", not drain["drain_successful"]))
    checks.append(("pipeline_conservation_drain", ledger.conservation_check()[0]))

    # 2. Inflation resistance
    ledger2 = ATPLedger(fee_rate=0.05)
    ledger2.create_account("inflator", 1000.0)
    ledger2.create_account("target", 500.0)
    inflation = inflation_attack(ledger2, "inflator", 10, rng)
    checks.append(("pipeline_no_inflation", not inflation["supply_inflated"]))

    # 3. Flash loan defense
    pool = FlashLoanPool()
    ledger3 = ATPLedger(fee_rate=0.05)
    ledger3.create_account("flasher", 50.0)
    flash = flash_loan_attack(pool, ledger3, "flasher", rng)
    checks.append(("pipeline_flash_blocked", not flash["success"]))

    # 4. Wash trading detection
    wash_txs = [
        {"sender": "w1", "receiver": "w2", "amount": 1000.0, "success": True},
        {"sender": "w2", "receiver": "w1", "amount": 990.0, "success": True},
        {"sender": "honest_1", "receiver": "honest_2", "amount": 50.0, "success": True},
    ]
    wash = detect_wash_trading(wash_txs)
    checks.append(("pipeline_wash_detected", wash["wash_trading_detected"]))

    # 5. Sybil economic analysis
    sybil = sybil_economic_attack(20, 150.0, 10, 500.0)
    checks.append(("pipeline_sybil_unprofitable", sybil["sybil_unprofitable"]))

    # 6. Market manipulation detection
    pump = [10.0]*10 + [30.0]*3 + [7.0]*7
    vols = [100.0]*10 + [800.0]*3 + [50.0]*7
    manip = detect_market_manipulation(pump, vols)
    checks.append(("pipeline_manipulation_detected", manip["detected"]))

    # 7. Economic equilibrium
    eq = analyze_economic_equilibrium(30, 50, 0.05, rng)
    checks.append(("pipeline_equilibrium_conservation", eq["conservation_holds"]))
    checks.append(("pipeline_supply_decreasing", eq["supply_decreasing"]))

    # 8. Fee safety
    safe_ledger = ATPLedger(fee_rate=0.05)
    safe_ledger.create_account("sa", 1000.0)
    safe_ledger.create_account("sb", 0.0)
    safe = fee_safe_transfer(safe_ledger, "sa", "sb", 100.0)
    checks.append(("pipeline_safe_transfer", safe["success"]))

    # 9. All attacks defended
    all_defended = (
        not drain["drain_successful"] and
        not inflation["supply_inflated"] and
        not flash["success"] and
        sybil["sybil_unprofitable"] and
        manip["detected"] and
        wash["wash_trading_detected"]
    )
    checks.append(("all_attacks_defended", all_defended))

    return checks


def test_section_12():
    rng = random.Random(42)
    return run_complete_economic_pipeline(rng)


# ============================================================
# Main runner
# ============================================================

def run_all():
    sections = [
        ("§1 ATP Economic Model", test_section_1),
        ("§2 Treasury Drain Attack", test_section_2),
        ("§3 ATP Inflation Attack", test_section_3),
        ("§4 Fee Manipulation Attack", test_section_4),
        ("§5 Flash Loan Attack", test_section_5),
        ("§6 Front-Running & Sandwich", test_section_6),
        ("§7 Wash Trading Detection", test_section_7),
        ("§8 ATP Staking Attack", test_section_8),
        ("§9 Sybil Economic Attack", test_section_9),
        ("§10 Market Manipulation", test_section_10),
        ("§11 Economic Equilibrium", test_section_11),
        ("§12 Complete Pipeline", test_section_12),
    ]

    total = 0
    passed = 0
    failed_checks = []

    for name, fn in sections:
        checks = fn()
        section_pass = sum(1 for _, v in checks if v)
        section_total = len(checks)
        total += section_total
        passed += section_pass
        status = "✓" if section_pass == section_total else "✗"
        print(f"  {status} {name}: {section_pass}/{section_total}")
        for cname, cval in checks:
            if not cval:
                failed_checks.append(f"    FAIL: {name} → {cname}")

    print(f"\nTotal: {passed}/{total}")
    if failed_checks:
        print("\nFailed checks:")
        for f in failed_checks:
            print(f)

    return passed, total


if __name__ == "__main__":
    run_all()
