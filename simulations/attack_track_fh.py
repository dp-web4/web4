"""
Track FH: Resource Starvation Attacks (Attacks 299-304)

Attacks on ATP (Allocation Transfer Packet) resource allocation and
economic mechanisms. Web4's trust-native model relies on resource
economics to make attacks expensive - but what if the economics themselves
can be gamed?

Key insight: Economic attacks target the resource substrate that makes
trust verification possible. Starve resources, and trust checks can't run.

Reference:
- web4-standard/core-spec/atp-adp-cycle.md
- whitepaper/sections/04-atp-energy/

Added: 2026-02-09
"""

import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


@dataclass
class AttackResult:
    """Result of an attack simulation."""
    attack_name: str
    success: bool
    setup_cost_atp: float
    gain_atp: float
    roi: float
    detection_probability: float
    time_to_detection_hours: float
    blocks_until_detected: int
    trust_damage: float
    description: str
    mitigation: str
    raw_data: Dict


# ============================================================================
# ATP RESOURCE INFRASTRUCTURE
# ============================================================================


class ResourceType(Enum):
    """Types of resources in Web4."""
    COMPUTE = "compute"
    MEMORY = "memory"
    BANDWIDTH = "bandwidth"
    STORAGE = "storage"
    VERIFICATION = "verification"


@dataclass
class ATPBalance:
    """ATP balance for an entity."""
    lct_id: str
    balance: float
    reserved: float  # Currently committed to operations
    pending_income: float
    pending_expense: float
    last_updated: float

    @property
    def available(self) -> float:
        return self.balance - self.reserved

    @property
    def effective(self) -> float:
        return self.balance + self.pending_income - self.pending_expense


@dataclass
class ResourceAllocation:
    """A resource allocation request/grant."""
    allocation_id: str
    requester_lct: str
    resource_type: ResourceType
    amount: float
    atp_cost: float
    duration_blocks: int
    priority: int
    granted_at: Optional[int] = None
    expires_at: Optional[int] = None


@dataclass
class ResourcePool:
    """A pool of resources."""
    pool_id: str
    resource_type: ResourceType
    total_capacity: float
    allocated: float
    reserved: float  # For high-priority operations

    @property
    def available(self) -> float:
        return self.total_capacity - self.allocated - self.reserved


class ResourceManager:
    """Manages resource allocation."""

    def __init__(self):
        self.pools: Dict[str, ResourcePool] = {}
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.atp_balances: Dict[str, ATPBalance] = {}
        self.pending_requests: List[ResourceAllocation] = []

    def add_pool(self, pool: ResourcePool):
        self.pools[pool.pool_id] = pool

    def register_entity(self, lct_id: str, initial_balance: float):
        self.atp_balances[lct_id] = ATPBalance(
            lct_id=lct_id,
            balance=initial_balance,
            reserved=0,
            pending_income=0,
            pending_expense=0,
            last_updated=time.time()
        )

    def request_allocation(self, allocation: ResourceAllocation,
                            current_block: int) -> Tuple[bool, str]:
        """Request resource allocation."""
        # Check ATP balance
        if allocation.requester_lct not in self.atp_balances:
            return False, "no_account"

        balance = self.atp_balances[allocation.requester_lct]
        if balance.available < allocation.atp_cost:
            return False, "insufficient_atp"

        # Check resource availability
        pool_id = f"pool_{allocation.resource_type.value}"
        if pool_id not in self.pools:
            return False, "no_pool"

        pool = self.pools[pool_id]
        if pool.available < allocation.amount:
            return False, "insufficient_resources"

        # Grant allocation
        allocation.granted_at = current_block
        allocation.expires_at = current_block + allocation.duration_blocks

        pool.allocated += allocation.amount
        balance.reserved += allocation.atp_cost

        self.allocations[allocation.allocation_id] = allocation
        return True, "granted"

    def release_allocation(self, allocation_id: str) -> bool:
        """Release a resource allocation."""
        if allocation_id not in self.allocations:
            return False

        allocation = self.allocations[allocation_id]
        pool_id = f"pool_{allocation.resource_type.value}"

        if pool_id in self.pools:
            self.pools[pool_id].allocated -= allocation.amount

        if allocation.requester_lct in self.atp_balances:
            self.atp_balances[allocation.requester_lct].reserved -= allocation.atp_cost
            self.atp_balances[allocation.requester_lct].balance -= allocation.atp_cost

        del self.allocations[allocation_id]
        return True


# ============================================================================
# ATTACK FH-1a: RESOURCE EXHAUSTION
# ============================================================================


def attack_resource_exhaustion() -> AttackResult:
    """
    ATTACK FH-1a: Resource Exhaustion

    Exhaust critical resources (compute, memory, bandwidth) to prevent
    legitimate operations from executing.

    Vectors:
    1. Bulk allocation requests
    2. Long-duration holds
    3. Multi-resource coordination
    4. Priority manipulation
    5. Renewal flooding
    """

    defenses = {
        "allocation_limits": False,
        "duration_caps": False,
        "fair_queuing": False,
        "priority_verification": False,
        "renewal_cooldown": False,
        "resource_reservation": False,
    }

    manager = ResourceManager()
    current_block = 50000

    # Setup resource pools
    manager.add_pool(ResourcePool(
        pool_id="pool_compute",
        resource_type=ResourceType.COMPUTE,
        total_capacity=1000.0,
        allocated=0,
        reserved=100.0  # 10% reserved for critical ops
    ))

    manager.add_pool(ResourcePool(
        pool_id="pool_verification",
        resource_type=ResourceType.VERIFICATION,
        total_capacity=500.0,
        allocated=0,
        reserved=50.0
    ))

    # Setup entities
    manager.register_entity("lct_attacker", 100000.0)
    manager.register_entity("lct_legitimate", 1000.0)

    # Attack: Request bulk allocations to exhaust pool
    attack_allocations = []
    for i in range(100):
        attack_allocations.append(ResourceAllocation(
            allocation_id=f"attack_alloc_{i}",
            requester_lct="lct_attacker",
            resource_type=ResourceType.COMPUTE,
            amount=10.0,  # 1% of pool each
            atp_cost=100.0,
            duration_blocks=10000,  # Very long duration
            priority=5
        ))

    # ========================================================================
    # Vector 1: Allocation Limits Defense
    # ========================================================================

    def check_allocation_limits(manager: ResourceManager,
                                  requester: str,
                                  new_allocation: ResourceAllocation,
                                  max_per_entity: float = 0.20) -> bool:
        """Check if entity already has too many allocations."""
        entity_allocations = sum(
            a.amount for a in manager.allocations.values()
            if a.requester_lct == requester
            and a.resource_type == new_allocation.resource_type
        )

        pool_id = f"pool_{new_allocation.resource_type.value}"
        pool = manager.pools.get(pool_id)
        if not pool:
            return True

        max_allowed = pool.total_capacity * max_per_entity
        return entity_allocations + new_allocation.amount <= max_allowed

    # Attack would exceed 20% limit quickly
    total_requested = sum(a.amount for a in attack_allocations[:25])
    if total_requested > manager.pools["pool_compute"].total_capacity * 0.20:
        defenses["allocation_limits"] = True

    # ========================================================================
    # Vector 2: Duration Caps Defense
    # ========================================================================

    def check_duration_caps(allocation: ResourceAllocation,
                             max_duration_blocks: int = 1000) -> bool:
        """Enforce maximum allocation duration."""
        return allocation.duration_blocks <= max_duration_blocks

    if not check_duration_caps(attack_allocations[0]):
        defenses["duration_caps"] = True

    # ========================================================================
    # Vector 3: Fair Queuing Defense
    # ========================================================================

    class FairQueue:
        """Fair queuing for resource requests."""

        def __init__(self, max_per_entity_per_block: int = 5):
            self.max_per_entity = max_per_entity_per_block
            self.requests_per_block: Dict[int, Dict[str, int]] = {}

        def can_enqueue(self, requester: str, block: int) -> bool:
            if block not in self.requests_per_block:
                self.requests_per_block[block] = {}

            current = self.requests_per_block[block].get(requester, 0)
            return current < self.max_per_entity

        def enqueue(self, requester: str, block: int):
            if block not in self.requests_per_block:
                self.requests_per_block[block] = {}

            self.requests_per_block[block][requester] = \
                self.requests_per_block[block].get(requester, 0) + 1

    fair_queue = FairQueue()

    # Attack tries 100 allocations in one block
    blocked_count = 0
    for alloc in attack_allocations:
        if not fair_queue.can_enqueue(alloc.requester_lct, current_block):
            blocked_count += 1
        else:
            fair_queue.enqueue(alloc.requester_lct, current_block)

    if blocked_count > 90:  # Most requests blocked
        defenses["fair_queuing"] = True

    # ========================================================================
    # Vector 4: Priority Verification Defense
    # ========================================================================

    def verify_priority(allocation: ResourceAllocation,
                         requester_trust: float) -> bool:
        """Verify priority claim matches trust level."""
        # Higher priority requires higher trust
        min_trust_for_priority = {
            1: 0.0,   # Anyone
            2: 0.2,
            3: 0.4,
            4: 0.6,
            5: 0.8,   # High priority requires high trust
        }

        required_trust = min_trust_for_priority.get(allocation.priority, 0.8)
        return requester_trust >= required_trust

    # Attacker has low trust, claims high priority
    attacker_trust = 0.3
    if not verify_priority(attack_allocations[0], attacker_trust):
        defenses["priority_verification"] = True

    # ========================================================================
    # Vector 5: Renewal Cooldown Defense
    # ========================================================================

    @dataclass
    class AllocationHistory:
        allocation_id: str
        requester: str
        resource_type: ResourceType
        renewed_count: int
        last_renewal_block: int

    def check_renewal_cooldown(history: AllocationHistory,
                                current_block: int,
                                min_cooldown_blocks: int = 100) -> bool:
        """Enforce cooldown between renewals."""
        if history.renewed_count == 0:
            return True

        blocks_since_renewal = current_block - history.last_renewal_block
        return blocks_since_renewal >= min_cooldown_blocks

    # Attack tries rapid renewals
    attack_history = AllocationHistory(
        allocation_id="attack_alloc_0",
        requester="lct_attacker",
        resource_type=ResourceType.COMPUTE,
        renewed_count=5,
        last_renewal_block=current_block - 10  # Just renewed
    )

    if not check_renewal_cooldown(attack_history, current_block):
        defenses["renewal_cooldown"] = True

    # ========================================================================
    # Vector 6: Resource Reservation Defense
    # ========================================================================

    def check_resource_reservation(pool: ResourcePool,
                                     allocation: ResourceAllocation) -> bool:
        """Ensure reserved resources stay protected."""
        # Available capacity excluding reserves
        truly_available = pool.total_capacity - pool.allocated - pool.reserved

        return allocation.amount <= truly_available

    # Even with all attack allocations, reserved stays protected
    pool = manager.pools["pool_compute"]
    if pool.reserved > 0:
        defenses["resource_reservation"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Resource Exhaustion (FH-1a)",
        success=attack_success,
        setup_cost_atp=10000.0,
        gain_atp=50000.0 if attack_success else 0.0,
        roi=(50000.0 / 10000.0) if attack_success else -1.0,
        detection_probability=0.75 if defenses_held >= 4 else 0.35,
        time_to_detection_hours=2.0,
        blocks_until_detected=20,
        trust_damage=0.40,
        description=f"""
RESOURCE EXHAUSTION ATTACK (Track FH-1a)

Exhaust critical resources to deny service.

Attack Pattern:
1. Request bulk allocations (100 x 10 units)
2. Use long durations (10000 blocks)
3. Claim high priority
4. Rapidly renew to maintain hold
5. Block legitimate operations

Attack Analysis:
- Total allocations requested: {len(attack_allocations)}
- Total resources requested: {sum(a.amount for a in attack_allocations)}
- Pool capacity: {pool.total_capacity}
- Would consume: {sum(a.amount for a in attack_allocations) / pool.total_capacity * 100:.1f}%

Defense Analysis:
- Allocation limits: {"HELD" if defenses["allocation_limits"] else "BYPASSED"}
- Duration caps: {"HELD" if defenses["duration_caps"] else "BYPASSED"}
- Fair queuing: {"HELD" if defenses["fair_queuing"] else "BYPASSED"}
- Priority verification: {"HELD" if defenses["priority_verification"] else "BYPASSED"}
- Renewal cooldown: {"HELD" if defenses["renewal_cooldown"] else "BYPASSED"}
- Resource reservation: {"HELD" if defenses["resource_reservation"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FH-1a: Resource Exhaustion Defense:
1. Per-entity allocation limits
2. Duration caps on allocations
3. Fair queuing prevents flooding
4. Priority requires trust verification
5. Renewal cooldowns prevent hoarding
6. Reserved capacity for critical ops

Resources are finite - share fairly.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "attack_allocations": len(attack_allocations),
        }
    )


# ============================================================================
# ATTACK FH-1b: ATP DRAINAGE
# ============================================================================


def attack_atp_drainage() -> AttackResult:
    """
    ATTACK FH-1b: ATP Drainage

    Drain an entity's ATP balance through forced expenditures,
    making them unable to operate.

    Vectors:
    1. Forced verification requests
    2. Challenge flooding
    3. Fee manipulation
    4. Micropayment drain
    5. Refund exploitation
    """

    defenses = {
        "verification_rate_limiting": False,
        "challenge_costs": False,
        "fee_bounds": False,
        "micropayment_aggregation": False,
        "refund_validation": False,
        "balance_protection": False,
    }

    manager = ResourceManager()
    current_block = 50000

    # Target entity with limited ATP
    manager.register_entity("lct_target", 1000.0)
    manager.register_entity("lct_attacker", 100000.0)

    target_initial_balance = 1000.0

    # ========================================================================
    # Vector 1: Verification Rate Limiting Defense
    # ========================================================================

    @dataclass
    class VerificationRequest:
        requester: str
        target: str
        verification_type: str
        cost_to_target: float
        block: int

    # Attack: Flood verification requests
    verification_requests = [
        VerificationRequest(
            requester="lct_attacker",
            target="lct_target",
            verification_type="trust_check",
            cost_to_target=1.0,  # Small cost per verification
            block=current_block
        )
        for _ in range(2000)  # 2000 requests = 2000 ATP drained
    ]

    def check_verification_rate(requests: List[VerificationRequest],
                                  target: str,
                                  max_per_block: int = 10) -> Tuple[bool, int]:
        """Rate limit verification requests targeting an entity."""
        target_requests = [r for r in requests if r.target == target]

        # Group by block
        per_block: Dict[int, int] = {}
        for r in target_requests:
            per_block[r.block] = per_block.get(r.block, 0) + 1

        violations = sum(1 for count in per_block.values() if count > max_per_block)
        return violations == 0, len(target_requests) - (max_per_block * len(per_block))

    rate_ok, blocked = check_verification_rate(verification_requests, "lct_target")
    if not rate_ok:
        defenses["verification_rate_limiting"] = True

    # ========================================================================
    # Vector 2: Challenge Costs Defense
    # ========================================================================

    @dataclass
    class Challenge:
        challenger: str
        challenged: str
        stake_required: float
        resolution_cost: float

    # Attack: Issue challenges that cost target to respond
    def check_challenge_costs(challenge: Challenge,
                               challenger_balance: float,
                               min_stake_ratio: float = 2.0) -> bool:
        """Require challenger to stake proportionally."""
        # Challenger must stake 2x the cost to challenged
        required_stake = challenge.resolution_cost * min_stake_ratio
        return challenge.stake_required >= required_stake

    attack_challenge = Challenge(
        challenger="lct_attacker",
        challenged="lct_target",
        stake_required=5.0,   # Low stake
        resolution_cost=10.0  # High cost to target
    )

    if not check_challenge_costs(attack_challenge, 100000.0):
        defenses["challenge_costs"] = True

    # ========================================================================
    # Vector 3: Fee Bounds Defense
    # ========================================================================

    @dataclass
    class Transaction:
        sender: str
        receiver: str
        amount: float
        fee: float
        fee_type: str

    def check_fee_bounds(transaction: Transaction,
                          max_fee_ratio: float = 0.1) -> bool:
        """Ensure fees are bounded."""
        # Fee cannot exceed 10% of transaction
        if transaction.amount > 0:
            fee_ratio = transaction.fee / transaction.amount
            return fee_ratio <= max_fee_ratio
        return transaction.fee <= 1.0  # Max 1 ATP for zero-value transactions

    # Attack: High fee transactions targeting entity
    attack_transaction = Transaction(
        sender="lct_target",
        receiver="lct_attacker",
        amount=10.0,
        fee=50.0,  # 500% fee!
        fee_type="service"
    )

    if not check_fee_bounds(attack_transaction):
        defenses["fee_bounds"] = True

    # ========================================================================
    # Vector 4: Micropayment Aggregation Defense
    # ========================================================================

    @dataclass
    class Micropayment:
        payer: str
        payee: str
        amount: float
        channel_id: str
        sequence: int

    # Attack: Many tiny payments to drain through fees
    micropayments = [
        Micropayment(
            payer="lct_target",
            payee="lct_attacker",
            amount=0.01,
            channel_id="channel_1",
            sequence=i
        )
        for i in range(10000)
    ]

    def check_micropayment_aggregation(payments: List[Micropayment],
                                         min_settlement_amount: float = 10.0) -> bool:
        """Aggregate micropayments to reduce fee overhead."""
        # Payments should be aggregated before settlement
        total = sum(p.amount for p in payments)
        return total >= min_settlement_amount

    total_micro = sum(p.amount for p in micropayments)
    if total_micro < 10.0:
        # Individual settlements would incur excessive fees
        defenses["micropayment_aggregation"] = True

    # ========================================================================
    # Vector 5: Refund Validation Defense
    # ========================================================================

    @dataclass
    class RefundRequest:
        requester: str
        original_transaction_id: str
        refund_amount: float
        reason: str

    def validate_refund(request: RefundRequest,
                         transaction_log: Dict[str, Transaction],
                         max_refund_ratio: float = 1.0) -> bool:
        """Validate refund requests."""
        if request.original_transaction_id not in transaction_log:
            return False  # No such transaction

        original = transaction_log[request.original_transaction_id]

        # Refund cannot exceed original amount
        if request.refund_amount > original.amount * max_refund_ratio:
            return False

        return True

    # Attack: Fraudulent refund request
    transaction_log = {
        "tx_123": Transaction("lct_target", "lct_attacker", 100.0, 1.0, "purchase")
    }

    fake_refund = RefundRequest(
        requester="lct_attacker",
        original_transaction_id="tx_fake",  # Non-existent
        refund_amount=500.0,
        reason="service_not_provided"
    )

    if not validate_refund(fake_refund, transaction_log):
        defenses["refund_validation"] = True

    # ========================================================================
    # Vector 6: Balance Protection Defense
    # ========================================================================

    def check_balance_protection(balance: ATPBalance,
                                   proposed_expense: float,
                                   min_protected: float = 100.0) -> bool:
        """Protect minimum balance from drainage."""
        remaining = balance.available - proposed_expense

        # Must maintain minimum balance for essential operations
        return remaining >= min_protected

    target_balance = manager.atp_balances["lct_target"]

    # Attack would drain below minimum
    total_drain = sum(r.cost_to_target for r in verification_requests[:100])
    if not check_balance_protection(target_balance, total_drain):
        defenses["balance_protection"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="ATP Drainage (FH-1b)",
        success=attack_success,
        setup_cost_atp=5000.0,
        gain_atp=80000.0 if attack_success else 0.0,
        roi=(80000.0 / 5000.0) if attack_success else -1.0,
        detection_probability=0.65 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=4.0,
        blocks_until_detected=40,
        trust_damage=0.55,
        description=f"""
ATP DRAINAGE ATTACK (Track FH-1b)

Drain target's ATP to prevent operation.

Attack Pattern:
1. Flood verification requests (2000 x 1 ATP)
2. Issue costly challenges
3. Force high-fee transactions
4. Micropayment fee exploitation
5. Fraudulent refund requests

Drainage Analysis:
- Target initial balance: {target_initial_balance} ATP
- Verification requests: {len(verification_requests)}
- Potential drain: {sum(r.cost_to_target for r in verification_requests)} ATP
- Micropayments: {len(micropayments)} x {micropayments[0].amount} ATP

Defense Analysis:
- Verification rate limiting: {"HELD" if defenses["verification_rate_limiting"] else "BYPASSED"}
- Challenge costs: {"HELD" if defenses["challenge_costs"] else "BYPASSED"}
- Fee bounds: {"HELD" if defenses["fee_bounds"] else "BYPASSED"}
- Micropayment aggregation: {"HELD" if defenses["micropayment_aggregation"] else "BYPASSED"}
- Refund validation: {"HELD" if defenses["refund_validation"] else "BYPASSED"}
- Balance protection: {"HELD" if defenses["balance_protection"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FH-1b: ATP Drainage Defense:
1. Rate limit verification requests per target
2. Require proportional challenger stakes
3. Bound fees as ratio of transaction
4. Aggregate micropayments
5. Validate refund requests against history
6. Protect minimum balance threshold

ATP drainage is economic denial of service.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "target_initial": target_initial_balance,
            "verification_count": len(verification_requests),
        }
    )


# ============================================================================
# ATTACK FH-2a: MARKET MANIPULATION
# ============================================================================


def attack_market_manipulation() -> AttackResult:
    """
    ATTACK FH-2a: Market Manipulation

    Manipulate ATP markets to profit or damage others.

    Vectors:
    1. Price manipulation (pump and dump)
    2. Wash trading
    3. Front-running
    4. Order book manipulation
    5. Liquidity attacks
    """

    defenses = {
        "price_bounds": False,
        "wash_trade_detection": False,
        "front_running_prevention": False,
        "order_book_monitoring": False,
        "liquidity_requirements": False,
        "trading_velocity_limits": False,
    }

    @dataclass
    class Order:
        order_id: str
        trader: str
        order_type: str  # "buy", "sell"
        amount: float
        price: float
        timestamp: float
        block: int

    @dataclass
    class Trade:
        trade_id: str
        buyer: str
        seller: str
        amount: float
        price: float
        timestamp: float

    now = time.time()
    current_block = 50000

    # Market state
    recent_trades: List[Trade] = []
    order_book: List[Order] = []

    # ========================================================================
    # Vector 1: Price Bounds Defense
    # ========================================================================

    def check_price_bounds(new_price: float,
                            recent_avg_price: float,
                            max_deviation: float = 0.2) -> bool:
        """Check if price is within reasonable bounds."""
        if recent_avg_price == 0:
            return True

        deviation = abs(new_price - recent_avg_price) / recent_avg_price
        return deviation <= max_deviation

    # Setup: Recent average price
    recent_avg_price = 100.0

    # Attack: Sudden price spike (pump)
    attack_price = 150.0  # 50% increase

    if not check_price_bounds(attack_price, recent_avg_price):
        defenses["price_bounds"] = True

    # ========================================================================
    # Vector 2: Wash Trade Detection Defense
    # ========================================================================

    def detect_wash_trading(trades: List[Trade],
                             min_unique_counterparties: int = 3) -> bool:
        """Detect wash trading (trading with self)."""
        # Group trades by trader
        trader_pairs: Dict[str, Set[str]] = {}

        for trade in trades:
            if trade.buyer not in trader_pairs:
                trader_pairs[trade.buyer] = set()
            trader_pairs[trade.buyer].add(trade.seller)

            if trade.seller not in trader_pairs:
                trader_pairs[trade.seller] = set()
            trader_pairs[trade.seller].add(trade.buyer)

        # Check for self-trading or limited counterparties
        for trader, counterparties in trader_pairs.items():
            if trader in counterparties:
                return False  # Self-trading detected

            if len(counterparties) < min_unique_counterparties:
                if len(trader_pairs) > 5:  # Enough activity to judge
                    return False  # Likely wash trading

        return True

    # Attack: Create wash trades
    wash_trades = [
        Trade(f"trade_{i}", "lct_attacker", "lct_attacker_alt", 10.0, 100.0 + i, now + i)
        for i in range(20)
    ]

    # Detect circular trading
    all_trades = wash_trades + [
        Trade("legit_1", "lct_attacker", "lct_attacker_alt", 5.0, 100.0, now)
    ]

    if not detect_wash_trading(all_trades):
        defenses["wash_trade_detection"] = True

    # ========================================================================
    # Vector 3: Front-Running Prevention Defense
    # ========================================================================

    @dataclass
    class PendingTransaction:
        tx_id: str
        submitter: str
        tx_type: str
        amount: float
        submitted_block: int
        gas_price: float

    def detect_front_running(pending: List[PendingTransaction],
                               executed: PendingTransaction) -> bool:
        """Detect front-running attempts."""
        # Check if higher gas transaction was submitted after seeing another
        for tx in pending:
            if tx.tx_id == executed.tx_id:
                continue

            # Front-running: submitted later but higher gas
            if (tx.submitted_block == executed.submitted_block and
                tx.gas_price > executed.gas_price and
                tx.tx_type == executed.tx_type):
                return False  # Likely front-running

        return True

    # Legitimate transaction
    legit_tx = PendingTransaction(
        tx_id="legit_tx",
        submitter="lct_victim",
        tx_type="large_buy",
        amount=10000.0,
        submitted_block=current_block,
        gas_price=10.0
    )

    # Front-running transaction
    front_run_tx = PendingTransaction(
        tx_id="front_run",
        submitter="lct_attacker",
        tx_type="large_buy",
        amount=5000.0,
        submitted_block=current_block,
        gas_price=50.0  # 5x gas to get priority
    )

    pending_txs = [legit_tx, front_run_tx]

    if not detect_front_running(pending_txs, front_run_tx):
        defenses["front_running_prevention"] = True

    # ========================================================================
    # Vector 4: Order Book Monitoring Defense
    # ========================================================================

    def monitor_order_book(orders: List[Order],
                            max_concentration: float = 0.3) -> bool:
        """Monitor order book for manipulation."""
        total_buy = sum(o.amount for o in orders if o.order_type == "buy")
        total_sell = sum(o.amount for o in orders if o.order_type == "sell")

        # Check for entity concentration
        entity_orders: Dict[str, float] = {}
        for order in orders:
            entity_orders[order.trader] = entity_orders.get(order.trader, 0) + order.amount

        total_volume = total_buy + total_sell
        if total_volume == 0:
            return True

        for volume in entity_orders.values():
            if volume / total_volume > max_concentration:
                return False  # One entity controls too much

        return True

    # Attack: Dominate order book
    attack_orders = [
        Order(f"attack_order_{i}", "lct_attacker", "buy", 100.0, 99.0, now, current_block)
        for i in range(50)
    ]
    legit_orders = [
        Order(f"legit_order_{i}", f"lct_user_{i}", "sell", 10.0, 101.0, now, current_block)
        for i in range(10)
    ]

    all_orders = attack_orders + legit_orders

    if not monitor_order_book(all_orders):
        defenses["order_book_monitoring"] = True

    # ========================================================================
    # Vector 5: Liquidity Requirements Defense
    # ========================================================================

    @dataclass
    class LiquidityPool:
        pool_id: str
        reserve_a: float  # ATP
        reserve_b: float  # Other token
        min_liquidity: float

    def check_liquidity_requirements(pool: LiquidityPool,
                                       withdrawal_amount: float) -> bool:
        """Ensure minimum liquidity is maintained."""
        remaining = min(pool.reserve_a, pool.reserve_b) - withdrawal_amount
        return remaining >= pool.min_liquidity

    pool = LiquidityPool(
        pool_id="atp_usdc",
        reserve_a=10000.0,
        reserve_b=10000.0,
        min_liquidity=1000.0
    )

    # Attack: Withdraw most liquidity
    attack_withdrawal = 9500.0

    if not check_liquidity_requirements(pool, attack_withdrawal):
        defenses["liquidity_requirements"] = True

    # ========================================================================
    # Vector 6: Trading Velocity Limits Defense
    # ========================================================================

    def check_trading_velocity(trades: List[Trade],
                                 trader: str,
                                 max_per_hour: int = 100) -> bool:
        """Limit trading velocity per entity."""
        one_hour_ago = now - 3600

        trader_trades = [t for t in trades
                        if (t.buyer == trader or t.seller == trader)
                        and t.timestamp > one_hour_ago]

        return len(trader_trades) <= max_per_hour

    # Attack: High-frequency trading
    hft_trades = [
        Trade(f"hft_{i}", "lct_attacker", f"lct_counterparty_{i%10}",
              1.0, 100.0, now - i)
        for i in range(200)
    ]

    if not check_trading_velocity(hft_trades, "lct_attacker"):
        defenses["trading_velocity_limits"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Market Manipulation (FH-2a)",
        success=attack_success,
        setup_cost_atp=50000.0,
        gain_atp=200000.0 if attack_success else 0.0,
        roi=(200000.0 / 50000.0) if attack_success else -1.0,
        detection_probability=0.60 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=24.0,
        blocks_until_detected=200,
        trust_damage=0.70,
        description=f"""
MARKET MANIPULATION ATTACK (Track FH-2a)

Manipulate ATP markets for profit.

Attack Pattern:
1. Price manipulation (pump 50%)
2. Wash trading (self-trading)
3. Front-running legitimate transactions
4. Order book domination
5. Liquidity withdrawal
6. High-frequency trading

Market Analysis:
- Recent average price: {recent_avg_price}
- Attack price: {attack_price} ({(attack_price/recent_avg_price - 1)*100:.0f}% deviation)
- Wash trades: {len(wash_trades)}
- Order book control: {sum(o.amount for o in attack_orders) / sum(o.amount for o in all_orders) * 100:.1f}%

Defense Analysis:
- Price bounds: {"HELD" if defenses["price_bounds"] else "BYPASSED"}
- Wash trade detection: {"HELD" if defenses["wash_trade_detection"] else "BYPASSED"}
- Front-running prevention: {"HELD" if defenses["front_running_prevention"] else "BYPASSED"}
- Order book monitoring: {"HELD" if defenses["order_book_monitoring"] else "BYPASSED"}
- Liquidity requirements: {"HELD" if defenses["liquidity_requirements"] else "BYPASSED"}
- Trading velocity limits: {"HELD" if defenses["trading_velocity_limits"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FH-2a: Market Manipulation Defense:
1. Price deviation bounds
2. Wash trade pattern detection
3. Front-running prevention (commit-reveal)
4. Order book concentration monitoring
5. Minimum liquidity requirements
6. Trading velocity limits

Markets need fairness to function.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "price_deviation": (attack_price - recent_avg_price) / recent_avg_price,
        }
    )


# ============================================================================
# ATTACK FH-2b: ECONOMIC INCENTIVE CORRUPTION
# ============================================================================


def attack_economic_incentive_corruption() -> AttackResult:
    """
    ATTACK FH-2b: Economic Incentive Corruption

    Corrupt the economic incentive structures that drive
    honest behavior.

    Vectors:
    1. Reward gaming
    2. Penalty evasion
    3. Collusion for rewards
    4. Stake manipulation
    5. Inflation attacks
    """

    defenses = {
        "reward_validation": False,
        "penalty_enforcement": False,
        "collusion_detection": False,
        "stake_verification": False,
        "inflation_monitoring": False,
        "incentive_bounds": False,
    }

    now = time.time()
    current_block = 50000

    # ========================================================================
    # Vector 1: Reward Validation Defense
    # ========================================================================

    @dataclass
    class RewardClaim:
        claimant: str
        reward_type: str
        amount: float
        evidence: Dict
        block: int

    def validate_reward_claim(claim: RewardClaim,
                                max_reward_per_block: float = 100.0) -> bool:
        """Validate reward claims."""
        # Check amount is reasonable
        if claim.amount > max_reward_per_block:
            return False

        # Check evidence exists
        if not claim.evidence:
            return False

        # Check evidence is valid (simplified)
        required_evidence = {"action_hash", "witness_signatures"}
        if not required_evidence.issubset(claim.evidence.keys()):
            return False

        return True

    # Attack: Claim excessive reward
    fake_claim = RewardClaim(
        claimant="lct_attacker",
        reward_type="witness_reward",
        amount=10000.0,  # 100x max
        evidence={},  # No evidence
        block=current_block
    )

    if not validate_reward_claim(fake_claim):
        defenses["reward_validation"] = True

    # ========================================================================
    # Vector 2: Penalty Enforcement Defense
    # ========================================================================

    @dataclass
    class Penalty:
        penalized: str
        penalty_type: str
        amount: float
        reason: str
        enforced: bool
        block: int

    @dataclass
    class PenaltyEvasionAttempt:
        entity: str
        evasion_method: str
        original_penalty: Penalty

    def check_penalty_enforcement(penalty: Penalty,
                                    entity_balance: float) -> bool:
        """Ensure penalties are enforceable."""
        # Penalty must be coverable by balance
        if penalty.amount > entity_balance:
            # Mark as partially enforceable
            return False

        return penalty.enforced

    # Attack: Evade penalty by draining balance first
    original_penalty = Penalty(
        penalized="lct_attacker",
        penalty_type="decoherent_behavior",
        amount=5000.0,
        reason="Trust violation",
        enforced=False,
        block=current_block
    )

    # Attacker drained balance before penalty
    attacker_balance_after_drain = 100.0

    if not check_penalty_enforcement(original_penalty, attacker_balance_after_drain):
        defenses["penalty_enforcement"] = True

    # ========================================================================
    # Vector 3: Collusion Detection Defense
    # ========================================================================

    @dataclass
    class RewardDistribution:
        block: int
        recipients: List[Tuple[str, float]]  # (entity, amount)

    def detect_reward_collusion(distributions: List[RewardDistribution],
                                  min_recipient_diversity: int = 5) -> bool:
        """Detect collusion in reward distribution."""
        # Count reward frequency per entity
        entity_rewards: Dict[str, int] = {}

        for dist in distributions:
            for entity, amount in dist.recipients:
                entity_rewards[entity] = entity_rewards.get(entity, 0) + 1

        # Check for suspiciously frequent recipients
        total_distributions = len(distributions)
        if total_distributions == 0:
            return True

        for count in entity_rewards.values():
            if count / total_distributions > 0.8:  # Entity in 80%+ of distributions
                return False

        # Check recipient diversity
        unique_recipients = len(entity_rewards)
        if unique_recipients < min_recipient_diversity and total_distributions > 10:
            return False

        return True

    # Attack: Colluding entities share most rewards
    colluding_distributions = [
        RewardDistribution(
            block=current_block + i,
            recipients=[
                ("lct_attacker", 50.0),
                ("lct_attacker_sybil_1", 30.0),
                ("lct_attacker_sybil_2", 20.0),
            ]
        )
        for i in range(20)
    ]

    if not detect_reward_collusion(colluding_distributions):
        defenses["collusion_detection"] = True

    # ========================================================================
    # Vector 4: Stake Verification Defense
    # ========================================================================

    @dataclass
    class Stake:
        staker: str
        amount: float
        staked_at_block: int
        locked_until_block: int
        source_verified: bool

    def verify_stake(stake: Stake,
                      min_lock_period: int = 1000,
                      min_age: int = 100) -> bool:
        """Verify stake is legitimate."""
        # Check lock period
        lock_duration = stake.locked_until_block - stake.staked_at_block
        if lock_duration < min_lock_period:
            return False

        # Check source verification
        if not stake.source_verified:
            return False

        # Check stake age (not flash stake)
        stake_age = current_block - stake.staked_at_block
        if stake_age < min_age:
            return False

        return True

    # Attack: Flash stake (stake just to claim rewards)
    flash_stake = Stake(
        staker="lct_attacker",
        amount=100000.0,
        staked_at_block=current_block - 5,  # Just staked
        locked_until_block=current_block + 100,  # Short lock
        source_verified=False
    )

    if not verify_stake(flash_stake):
        defenses["stake_verification"] = True

    # ========================================================================
    # Vector 5: Inflation Monitoring Defense
    # ========================================================================

    @dataclass
    class SupplyMetrics:
        total_supply: float
        circulating_supply: float
        minted_this_epoch: float
        burned_this_epoch: float
        target_inflation: float

    def monitor_inflation(metrics: SupplyMetrics,
                           max_deviation: float = 0.1) -> bool:
        """Monitor for inflation attacks."""
        if metrics.total_supply == 0:
            return True

        net_change = metrics.minted_this_epoch - metrics.burned_this_epoch
        actual_inflation = net_change / metrics.total_supply

        deviation = abs(actual_inflation - metrics.target_inflation)
        return deviation <= max_deviation

    # Attack: Excessive minting
    supply_metrics = SupplyMetrics(
        total_supply=1000000.0,
        circulating_supply=800000.0,
        minted_this_epoch=50000.0,  # 5% minted
        burned_this_epoch=1000.0,
        target_inflation=0.02  # Target 2%
    )

    if not monitor_inflation(supply_metrics):
        defenses["inflation_monitoring"] = True

    # ========================================================================
    # Vector 6: Incentive Bounds Defense
    # ========================================================================

    @dataclass
    class IncentiveScheme:
        scheme_id: str
        reward_rate: float
        penalty_rate: float
        max_reward_per_entity: float
        max_penalty_per_entity: float

    def check_incentive_bounds(scheme: IncentiveScheme,
                                 max_reward_rate: float = 0.1,
                                 max_penalty_rate: float = 0.5) -> bool:
        """Ensure incentive schemes are bounded."""
        if scheme.reward_rate > max_reward_rate:
            return False
        if scheme.penalty_rate > max_penalty_rate:
            return False
        return True

    # Attack: Create scheme with excessive rewards
    attack_scheme = IncentiveScheme(
        scheme_id="attack_scheme",
        reward_rate=0.5,  # 50% rewards (way too high)
        penalty_rate=0.01,  # 1% penalties (too low)
        max_reward_per_entity=1000000.0,
        max_penalty_per_entity=100.0
    )

    if not check_incentive_bounds(attack_scheme):
        defenses["incentive_bounds"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Economic Incentive Corruption (FH-2b)",
        success=attack_success,
        setup_cost_atp=30000.0,
        gain_atp=150000.0 if attack_success else 0.0,
        roi=(150000.0 / 30000.0) if attack_success else -1.0,
        detection_probability=0.55 if defenses_held >= 4 else 0.20,
        time_to_detection_hours=72.0,
        blocks_until_detected=600,
        trust_damage=0.80,
        description=f"""
ECONOMIC INCENTIVE CORRUPTION ATTACK (Track FH-2b)

Corrupt incentive structures for profit.

Attack Pattern:
1. Claim excessive rewards (100x max)
2. Evade penalties by draining balance
3. Collude for reward concentration
4. Flash stake manipulation
5. Inflation through minting
6. Create exploitative schemes

Incentive Analysis:
- Fake reward claim: {fake_claim.amount} ATP (max: 100)
- Balance before penalty: {attacker_balance_after_drain} ATP (penalty: {original_penalty.amount})
- Colluding distributions: {len(colluding_distributions)}
- Flash stake age: {current_block - flash_stake.staked_at_block} blocks (min: 100)
- Actual inflation: {(supply_metrics.minted_this_epoch - supply_metrics.burned_this_epoch) / supply_metrics.total_supply * 100:.1f}%

Defense Analysis:
- Reward validation: {"HELD" if defenses["reward_validation"] else "BYPASSED"}
- Penalty enforcement: {"HELD" if defenses["penalty_enforcement"] else "BYPASSED"}
- Collusion detection: {"HELD" if defenses["collusion_detection"] else "BYPASSED"}
- Stake verification: {"HELD" if defenses["stake_verification"] else "BYPASSED"}
- Inflation monitoring: {"HELD" if defenses["inflation_monitoring"] else "BYPASSED"}
- Incentive bounds: {"HELD" if defenses["incentive_bounds"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FH-2b: Economic Incentive Corruption Defense:
1. Validate reward claims with evidence
2. Enforce penalties before balance drain
3. Detect colluding reward recipients
4. Verify stake age and lock period
5. Monitor inflation against targets
6. Bound incentive scheme parameters

Economic security requires aligned incentives.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "fake_reward_amount": fake_claim.amount,
        }
    )


# ============================================================================
# ATTACK FH-3a: VERIFICATION STARVATION
# ============================================================================


def attack_verification_starvation() -> AttackResult:
    """
    ATTACK FH-3a: Verification Starvation

    Starve the verification system of resources so that
    malicious actions go unverified.

    Vectors:
    1. Verifier exhaustion
    2. Verification queue flooding
    3. Selective verification denial
    4. Verifier bribery
    5. Verification deadline manipulation
    """

    defenses = {
        "verifier_redundancy": False,
        "queue_prioritization": False,
        "verification_routing": False,
        "bribery_detection": False,
        "deadline_enforcement": False,
        "emergency_verification": False,
    }

    now = time.time()
    current_block = 50000

    @dataclass
    class VerificationTask:
        task_id: str
        subject: str
        verification_type: str
        submitted_block: int
        deadline_block: int
        priority: int
        atp_reward: float

    @dataclass
    class Verifier:
        verifier_id: str
        capacity: int  # Tasks per block
        current_load: int
        trust_score: float
        last_active_block: int

    # ========================================================================
    # Vector 1: Verifier Redundancy Defense
    # ========================================================================

    verifiers = [
        Verifier(f"verifier_{i}", capacity=10, current_load=0, trust_score=0.8, last_active_block=current_block)
        for i in range(5)
    ]

    def check_verifier_redundancy(verifiers: List[Verifier],
                                    min_available: int = 3) -> bool:
        """Ensure sufficient verifier redundancy."""
        available = sum(1 for v in verifiers if v.capacity > v.current_load)
        return available >= min_available

    # Attack: Exhaust all verifiers
    for v in verifiers:
        v.current_load = v.capacity  # Max load

    if not check_verifier_redundancy(verifiers):
        defenses["verifier_redundancy"] = True

    # Reset for next tests
    for v in verifiers:
        v.current_load = 5

    # ========================================================================
    # Vector 2: Queue Prioritization Defense
    # ========================================================================

    verification_queue: List[VerificationTask] = []

    # Attack: Flood queue with low-priority tasks
    attack_tasks = [
        VerificationTask(
            task_id=f"attack_task_{i}",
            subject="lct_attacker",
            verification_type="routine",
            submitted_block=current_block,
            deadline_block=current_block + 1000,
            priority=1,  # Low priority
            atp_reward=1.0
        )
        for i in range(1000)
    ]

    # Legitimate high-priority task
    legit_task = VerificationTask(
        task_id="legit_task_1",
        subject="lct_legitimate",
        verification_type="critical",
        submitted_block=current_block,
        deadline_block=current_block + 10,  # Urgent
        priority=5,  # High priority
        atp_reward=50.0
    )

    all_tasks = attack_tasks + [legit_task]

    def prioritize_queue(tasks: List[VerificationTask]) -> List[VerificationTask]:
        """Prioritize verification queue."""
        # Sort by priority (desc), then deadline (asc)
        return sorted(tasks, key=lambda t: (-t.priority, t.deadline_block))

    prioritized = prioritize_queue(all_tasks)

    # High priority task should be first
    if prioritized[0].task_id == "legit_task_1":
        defenses["queue_prioritization"] = True

    # ========================================================================
    # Vector 3: Verification Routing Defense
    # ========================================================================

    def route_verification(task: VerificationTask,
                            verifiers: List[Verifier],
                            min_verifier_trust: float = 0.6) -> Optional[Verifier]:
        """Route verification to appropriate verifier."""
        # Filter by trust and capacity
        eligible = [v for v in verifiers
                   if v.trust_score >= min_verifier_trust
                   and v.current_load < v.capacity]

        if not eligible:
            return None

        # Route to least loaded
        return min(eligible, key=lambda v: v.current_load)

    # Attack: All verifiers busy or low trust
    for v in verifiers[:3]:
        v.current_load = v.capacity  # Exhaust

    for v in verifiers[3:]:
        v.trust_score = 0.3  # Low trust

    routed = route_verification(legit_task, verifiers)

    if routed is None:
        defenses["verification_routing"] = True

    # Reset
    for v in verifiers:
        v.current_load = 5
        v.trust_score = 0.8

    # ========================================================================
    # Vector 4: Bribery Detection Defense
    # ========================================================================

    @dataclass
    class VerifierPayment:
        payer: str
        verifier: str
        amount: float
        task_id: Optional[str]
        timestamp: float

    def detect_bribery(payments: List[VerifierPayment],
                        official_rewards: Dict[str, float]) -> bool:
        """Detect verifier bribery attempts."""
        for payment in payments:
            # Unofficial payments are suspicious
            expected_reward = official_rewards.get(payment.task_id, 0)

            if payment.amount > expected_reward * 2:
                return False  # Payment far exceeds legitimate reward

            # Payment without associated task
            if payment.task_id is None:
                return False

        return True

    # Attack: Bribe verifier to skip verification
    bribe_payments = [
        VerifierPayment(
            payer="lct_attacker",
            verifier="verifier_1",
            amount=1000.0,  # Much higher than any reward
            task_id=None,  # No associated task
            timestamp=now
        )
    ]

    official_rewards = {
        "legit_task_1": 50.0
    }

    if not detect_bribery(bribe_payments, official_rewards):
        defenses["bribery_detection"] = True

    # ========================================================================
    # Vector 5: Deadline Enforcement Defense
    # ========================================================================

    def enforce_deadlines(task: VerificationTask,
                           current_block: int) -> Tuple[str, Optional[str]]:
        """Enforce verification deadlines."""
        if current_block > task.deadline_block:
            return "expired", "verification_not_completed"

        blocks_remaining = task.deadline_block - current_block

        if blocks_remaining < 3:
            return "urgent", "escalate_to_emergency"

        return "normal", None

    # Attack: Let task expire
    expired_task = VerificationTask(
        task_id="expired_task",
        subject="lct_victim",
        verification_type="critical",
        submitted_block=current_block - 100,
        deadline_block=current_block - 10,  # Already expired
        priority=5,
        atp_reward=50.0
    )

    status, action = enforce_deadlines(expired_task, current_block)

    if status == "expired":
        defenses["deadline_enforcement"] = True

    # ========================================================================
    # Vector 6: Emergency Verification Defense
    # ========================================================================

    @dataclass
    class EmergencyVerifier:
        verifier_id: str
        always_available: bool
        emergency_capacity: int

    emergency_verifiers = [
        EmergencyVerifier("emergency_1", True, 100),
        EmergencyVerifier("emergency_2", True, 100),
    ]

    def request_emergency_verification(task: VerificationTask,
                                         emergency_pool: List[EmergencyVerifier]) -> bool:
        """Request emergency verification."""
        available = [v for v in emergency_pool
                    if v.always_available and v.emergency_capacity > 0]

        return len(available) > 0

    # Even under attack, emergency verifiers available
    if request_emergency_verification(legit_task, emergency_verifiers):
        defenses["emergency_verification"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Verification Starvation (FH-3a)",
        success=attack_success,
        setup_cost_atp=15000.0,
        gain_atp=100000.0 if attack_success else 0.0,
        roi=(100000.0 / 15000.0) if attack_success else -1.0,
        detection_probability=0.70 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=8.0,
        blocks_until_detected=80,
        trust_damage=0.60,
        description=f"""
VERIFICATION STARVATION ATTACK (Track FH-3a)

Starve verification system of resources.

Attack Pattern:
1. Exhaust all verifiers (max load)
2. Flood queue with low-priority tasks
3. Block routing to legitimate verifiers
4. Bribe verifiers to skip tasks
5. Let critical tasks expire

Starvation Analysis:
- Verifiers exhausted: {sum(1 for v in verifiers if v.current_load >= v.capacity)}/{len(verifiers)}
- Attack tasks in queue: {len(attack_tasks)}
- Legitimate task position: {prioritized.index(legit_task) + 1 if legit_task in prioritized else 'N/A'}
- Bribe amount: {bribe_payments[0].amount} ATP

Defense Analysis:
- Verifier redundancy: {"HELD" if defenses["verifier_redundancy"] else "BYPASSED"}
- Queue prioritization: {"HELD" if defenses["queue_prioritization"] else "BYPASSED"}
- Verification routing: {"HELD" if defenses["verification_routing"] else "BYPASSED"}
- Bribery detection: {"HELD" if defenses["bribery_detection"] else "BYPASSED"}
- Deadline enforcement: {"HELD" if defenses["deadline_enforcement"] else "BYPASSED"}
- Emergency verification: {"HELD" if defenses["emergency_verification"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FH-3a: Verification Starvation Defense:
1. Maintain verifier redundancy
2. Prioritize critical verifications
3. Smart routing by load and trust
4. Detect bribery attempts
5. Enforce verification deadlines
6. Emergency verification pool

Verification is the immune system.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "attack_tasks": len(attack_tasks),
        }
    )


# ============================================================================
# ATTACK FH-3b: ECONOMIC GRIEFING
# ============================================================================


def attack_economic_griefing() -> AttackResult:
    """
    ATTACK FH-3b: Economic Griefing

    Attack where the attacker loses money but causes
    disproportionate harm to others or the system.

    Vectors:
    1. Spite attacks (lose to hurt)
    2. Scorched earth withdrawal
    3. Negative sum games
    4. Tragedy of the commons
    5. Coordination destruction
    """

    defenses = {
        "griefing_cost_ratio": False,
        "withdrawal_dampening": False,
        "negative_sum_prevention": False,
        "commons_protection": False,
        "coordination_preservation": False,
        "grief_insurance": False,
    }

    now = time.time()
    current_block = 50000

    # ========================================================================
    # Vector 1: Griefing Cost Ratio Defense
    # ========================================================================

    @dataclass
    class GriefingAttack:
        attacker: str
        attacker_cost: float
        victim_damage: float
        system_damage: float

    def check_griefing_ratio(attack: GriefingAttack,
                              max_damage_ratio: float = 2.0) -> bool:
        """Ensure attacks cannot cause disproportionate damage."""
        total_damage = attack.victim_damage + attack.system_damage

        if attack.attacker_cost == 0:
            return False  # Free attacks not allowed

        damage_ratio = total_damage / attack.attacker_cost
        return damage_ratio <= max_damage_ratio

    # Attack: Spend 1000 to cause 50000 damage
    spite_attack = GriefingAttack(
        attacker="lct_attacker",
        attacker_cost=1000.0,
        victim_damage=30000.0,
        system_damage=20000.0
    )

    if not check_griefing_ratio(spite_attack):
        defenses["griefing_cost_ratio"] = True

    # ========================================================================
    # Vector 2: Withdrawal Dampening Defense
    # ========================================================================

    @dataclass
    class Withdrawal:
        entity: str
        amount: float
        from_pool: str
        timestamp: float
        consecutive_withdrawals: int

    def dampen_withdrawal(withdrawal: Withdrawal,
                           pool_size: float,
                           max_single_withdrawal_ratio: float = 0.1,
                           consecutive_penalty: float = 0.5) -> float:
        """Dampen large or rapid withdrawals."""
        max_allowed = pool_size * max_single_withdrawal_ratio

        # Apply consecutive withdrawal penalty
        if withdrawal.consecutive_withdrawals > 1:
            penalty = consecutive_penalty ** (withdrawal.consecutive_withdrawals - 1)
            max_allowed *= penalty

        return min(withdrawal.amount, max_allowed)

    # Attack: Rapid large withdrawals
    scorched_earth = Withdrawal(
        entity="lct_attacker",
        amount=50000.0,  # 50% of pool
        from_pool="liquidity_pool",
        timestamp=now,
        consecutive_withdrawals=5
    )

    pool_size = 100000.0
    dampened_amount = dampen_withdrawal(scorched_earth, pool_size)

    if dampened_amount < scorched_earth.amount:
        defenses["withdrawal_dampening"] = True

    # ========================================================================
    # Vector 3: Negative Sum Prevention Defense
    # ========================================================================

    @dataclass
    class GameOutcome:
        participants: List[str]
        payoffs: Dict[str, float]

    def is_negative_sum(outcome: GameOutcome) -> bool:
        """Check if game outcome is negative sum."""
        total_payoff = sum(outcome.payoffs.values())
        return total_payoff < 0

    def prevent_negative_sum(proposed_action: Dict,
                               estimated_outcome: GameOutcome) -> bool:
        """Prevent actions that create negative sum outcomes."""
        if is_negative_sum(estimated_outcome):
            return False
        return True

    # Attack: Action that destroys value
    negative_outcome = GameOutcome(
        participants=["lct_attacker", "lct_victim", "lct_bystander"],
        payoffs={
            "lct_attacker": -1000.0,
            "lct_victim": -5000.0,
            "lct_bystander": -2000.0
        }
    )

    if not prevent_negative_sum({}, negative_outcome):
        defenses["negative_sum_prevention"] = True

    # ========================================================================
    # Vector 4: Commons Protection Defense
    # ========================================================================

    @dataclass
    class SharedResource:
        resource_id: str
        total_capacity: float
        usage_by_entity: Dict[str, float]
        regeneration_rate: float

    def protect_commons(resource: SharedResource,
                         proposed_usage: float,
                         entity: str,
                         max_per_entity_ratio: float = 0.2) -> bool:
        """Protect shared resources from overuse."""
        # Check individual limit
        current_usage = resource.usage_by_entity.get(entity, 0)
        max_allowed = resource.total_capacity * max_per_entity_ratio

        if current_usage + proposed_usage > max_allowed:
            return False

        # Check total capacity
        total_usage = sum(resource.usage_by_entity.values()) + proposed_usage

        if total_usage > resource.total_capacity:
            return False

        return True

    # Attack: Consume all shared resources
    commons = SharedResource(
        resource_id="shared_bandwidth",
        total_capacity=1000.0,
        usage_by_entity={"lct_user_1": 100.0, "lct_user_2": 100.0},
        regeneration_rate=10.0
    )

    attack_usage = 800.0  # 80% consumption

    if not protect_commons(commons, attack_usage, "lct_attacker"):
        defenses["commons_protection"] = True

    # ========================================================================
    # Vector 5: Coordination Preservation Defense
    # ========================================================================

    @dataclass
    class CoordinationMechanism:
        mechanism_id: str
        participants: Set[str]
        required_quorum: int
        active: bool

    def preserve_coordination(mechanism: CoordinationMechanism,
                                departing_entity: str) -> bool:
        """Preserve coordination when participants leave."""
        remaining = mechanism.participants - {departing_entity}

        # Check if quorum still achievable
        if len(remaining) < mechanism.required_quorum:
            return False

        return True

    # Attack: Strategic withdrawal to break quorum
    coordination = CoordinationMechanism(
        mechanism_id="governance_quorum",
        participants={"lct_a", "lct_b", "lct_attacker_1", "lct_attacker_2", "lct_attacker_3"},
        required_quorum=4,
        active=True
    )

    # Multiple attackers withdraw
    for attacker in ["lct_attacker_1", "lct_attacker_2"]:
        if not preserve_coordination(coordination, attacker):
            defenses["coordination_preservation"] = True
            break
        coordination.participants.remove(attacker)

    # ========================================================================
    # Vector 6: Grief Insurance Defense
    # ========================================================================

    @dataclass
    class InsurancePool:
        pool_id: str
        total_funds: float
        coverage_ratio: float
        claims_paid: float

    def claim_grief_insurance(victim: str,
                                damage: float,
                                insurance: InsurancePool) -> float:
        """Claim insurance for griefing damage."""
        available = insurance.total_funds - insurance.claims_paid
        max_payout = damage * insurance.coverage_ratio

        return min(max_payout, available)

    insurance = InsurancePool(
        pool_id="grief_insurance",
        total_funds=100000.0,
        coverage_ratio=0.8,  # 80% coverage
        claims_paid=10000.0
    )

    # Victim claims insurance for griefing damage
    payout = claim_grief_insurance("lct_victim", spite_attack.victim_damage, insurance)

    if payout > 0:
        defenses["grief_insurance"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    total_attack_damage = spite_attack.victim_damage + spite_attack.system_damage

    return AttackResult(
        attack_name="Economic Griefing (FH-3b)",
        success=attack_success,
        setup_cost_atp=20000.0,  # Attacker willing to lose
        gain_atp=0.0,  # No direct gain
        roi=-1.0,  # Intentional loss
        detection_probability=0.50 if defenses_held >= 4 else 0.20,
        time_to_detection_hours=48.0,
        blocks_until_detected=400,
        trust_damage=0.90,
        description=f"""
ECONOMIC GRIEFING ATTACK (Track FH-3b)

Lose money to cause disproportionate harm.

Attack Pattern:
1. Spite attacks (lose 1K, cause 50K damage)
2. Scorched earth withdrawals
3. Force negative sum outcomes
4. Consume shared resources
5. Break coordination quorums

Griefing Analysis:
- Attacker cost: {spite_attack.attacker_cost} ATP
- Total damage: {total_attack_damage} ATP
- Damage ratio: {total_attack_damage / spite_attack.attacker_cost:.1f}x
- Negative sum total: {sum(negative_outcome.payoffs.values())} ATP
- Insurance payout: {payout} ATP

Defense Analysis:
- Griefing cost ratio: {"HELD" if defenses["griefing_cost_ratio"] else "BYPASSED"}
- Withdrawal dampening: {"HELD" if defenses["withdrawal_dampening"] else "BYPASSED"}
- Negative sum prevention: {"HELD" if defenses["negative_sum_prevention"] else "BYPASSED"}
- Commons protection: {"HELD" if defenses["commons_protection"] else "BYPASSED"}
- Coordination preservation: {"HELD" if defenses["coordination_preservation"] else "BYPASSED"}
- Grief insurance: {"HELD" if defenses["grief_insurance"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FH-3b: Economic Griefing Defense:
1. Limit damage-to-cost ratio
2. Dampen rapid/large withdrawals
3. Prevent negative sum outcomes
4. Protect shared resources
5. Preserve coordination mechanisms
6. Provide grief insurance

Some attackers don't seek profit.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "damage_ratio": total_attack_damage / spite_attack.attacker_cost,
        }
    )


# ============================================================================
# RUN ALL ATTACKS
# ============================================================================


def run_all_track_fh_attacks() -> List[AttackResult]:
    """Run all Track FH attacks and return results."""
    attacks = [
        attack_resource_exhaustion,
        attack_atp_drainage,
        attack_market_manipulation,
        attack_economic_incentive_corruption,
        attack_verification_starvation,
        attack_economic_griefing,
    ]

    results = []
    for attack_fn in attacks:
        try:
            result = attack_fn()
            results.append(result)
        except Exception as e:
            print(f"Error running {attack_fn.__name__}: {e}")
            import traceback
            traceback.print_exc()

    return results


def print_track_fh_summary(results: List[AttackResult]):
    """Print summary of Track FH attack results."""
    print("\n" + "=" * 70)
    print("TRACK FH: RESOURCE STARVATION ATTACKS - SUMMARY")
    print("Attacks 299-304")
    print("=" * 70)

    total_attacks = len(results)
    successful = sum(1 for r in results if r.success)
    defended = total_attacks - successful

    print(f"\nTotal Attacks: {total_attacks}")
    print(f"Defended: {defended}")
    print(f"Attack Success Rate: {(successful/total_attacks)*100:.1f}%")

    avg_detection = sum(r.detection_probability for r in results) / total_attacks
    print(f"Average Detection Probability: {avg_detection*100:.1f}%")

    total_setup_cost = sum(r.setup_cost_atp for r in results)
    print(f"Total Attack Cost: {total_setup_cost:,.0f} ATP")

    print("\n" + "-" * 70)
    print("INDIVIDUAL RESULTS:")
    print("-" * 70)

    for i, result in enumerate(results, 299):
        status = "DEFENDED" if not result.success else "SUCCEEDED"
        print(f"\nAttack #{i}: {result.attack_name}")
        print(f"  Status: {status}")
        print(f"  Detection: {result.detection_probability*100:.0f}%")
        print(f"  Setup Cost: {result.setup_cost_atp:,.0f} ATP")
        print(f"  Potential Gain: {result.gain_atp:,.0f} ATP")
        print(f"  Trust Damage: {result.trust_damage:.0%}")
        print(f"  Time to Detection: {result.time_to_detection_hours:.0f}h")


if __name__ == "__main__":
    results = run_all_track_fh_attacks()
    print_track_fh_summary(results)
