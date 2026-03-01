"""
Multi-Hop Cross-Federation Delegation — Reference Implementation

When Agent A in Society X delegates to Agent B in Society Y who
sub-delegates to Agent C in Society Z, the full delegation chain
needs:
1. Cryptographic integrity (hash-chained delegation proofs)
2. ATP deduction at each hop (scope narrowing + fee extraction)
3. Quality rollup (quality propagates back through the chain)
4. Cascade revocation (revoking any link invalidates downstream)
5. Cross-federation accountability (audit trail spans boundaries)

Key design principles:
- Delegation scope MONOTONICALLY narrows with each hop
- Child budget ≤ parent available budget
- ATP fee extracted at each crossing (5% per hop)
- Quality aggregated via multiplicative composition
- Revocation cascades forward through the chain

Builds on:
- agy_agency_delegation.py (single-society delegation chains)
- cross_society_atp_sync.py (bilateral ATP tracking)
- cross_ledger_consistency.py (cross-ledger 2PC)
- multi_federation_dynamics.py (federation topology)

Checks: 72
"""
from __future__ import annotations
import hashlib
import math
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ─── Core Types ───────────────────────────────────────────────────────────────

class DelegationStatus(Enum):
    ACTIVE = auto()
    COMPLETED = auto()
    REVOKED = auto()
    EXPIRED = auto()
    FAILED = auto()


class HopType(Enum):
    INTRA_SOCIETY = auto()    # Same society
    CROSS_FEDERATION = auto()  # Different federation society


class QualityRating(Enum):
    EXCELLENT = auto()    # 0.9-1.0
    GOOD = auto()         # 0.7-0.9
    ACCEPTABLE = auto()   # 0.5-0.7
    POOR = auto()         # 0.3-0.5
    FAILED = auto()       # <0.3


# ─── Delegation Chain Model ─────────────────────────────────────────────────

@dataclass
class DelegationScope:
    """What actions the delegate is authorized to perform."""
    allowed_actions: Set[str]
    max_budget: float         # Maximum ATP budget
    max_sub_delegates: int    # How many sub-delegations allowed
    time_limit: float         # Seconds until expiry
    trust_minimum: float      # Minimum T3 for the delegate
    federation_crossing_allowed: bool = True

    def narrow(self, child_actions: Optional[Set[str]] = None,
                child_budget: Optional[float] = None,
                child_max_subs: Optional[int] = None,
                child_crossing: Optional[bool] = None) -> 'DelegationScope':
        """Create a narrower scope for sub-delegation. Scope can only shrink."""
        # federation_crossing can only be further restricted, never expanded
        crossing = self.federation_crossing_allowed
        if child_crossing is not None:
            crossing = crossing and child_crossing

        return DelegationScope(
            allowed_actions=(child_actions & self.allowed_actions
                              if child_actions else set(self.allowed_actions)),
            max_budget=min(child_budget or self.max_budget, self.max_budget),
            max_sub_delegates=min(child_max_subs if child_max_subs is not None
                                    else self.max_sub_delegates,
                                  max(self.max_sub_delegates - 1, 0)),
            time_limit=self.time_limit,
            trust_minimum=self.trust_minimum,
            federation_crossing_allowed=crossing,
        )

    def is_subset_of(self, parent: 'DelegationScope') -> bool:
        """Verify this scope is a subset of parent."""
        return (
            self.allowed_actions <= parent.allowed_actions and
            self.max_budget <= parent.max_budget and
            self.max_sub_delegates <= parent.max_sub_delegates and
            self.trust_minimum >= parent.trust_minimum
        )


@dataclass
class DelegationHop:
    """A single hop in a delegation chain."""
    hop_id: str
    delegator_id: str
    delegate_id: str
    delegator_society: str
    delegate_society: str
    hop_type: HopType
    scope: DelegationScope
    atp_allocated: float
    atp_fee: float           # Cross-federation fee
    status: DelegationStatus = DelegationStatus.ACTIVE
    quality_score: Optional[float] = None
    prev_hop_hash: str = ""
    hop_hash: str = ""
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def compute_hash(self) -> str:
        data = (f"{self.hop_id}:{self.delegator_id}:{self.delegate_id}:"
                f"{self.atp_allocated}:{self.prev_hop_hash}")
        self.hop_hash = hashlib.sha256(data.encode()).hexdigest()[:32]
        return self.hop_hash

    @property
    def net_budget(self) -> float:
        """Budget after fee extraction."""
        return self.atp_allocated - self.atp_fee


@dataclass
class DelegationChain:
    """A full multi-hop delegation chain."""
    chain_id: str
    origin_society: str
    origin_entity: str
    hops: List[DelegationHop] = field(default_factory=list)
    total_atp_allocated: float = 0.0
    total_fees: float = 0.0
    status: DelegationStatus = DelegationStatus.ACTIVE
    created_at: float = field(default_factory=time.time)

    @property
    def depth(self) -> int:
        return len(self.hops)

    @property
    def current_delegate(self) -> Optional[str]:
        if not self.hops:
            return None
        return self.hops[-1].delegate_id

    @property
    def societies_involved(self) -> Set[str]:
        societies = {self.origin_society}
        for hop in self.hops:
            societies.add(hop.delegator_society)
            societies.add(hop.delegate_society)
        return societies

    @property
    def federation_crossings(self) -> int:
        return sum(1 for h in self.hops if h.hop_type == HopType.CROSS_FEDERATION)

    def verify_hash_chain(self) -> bool:
        """Verify the hash chain integrity of all hops."""
        for i, hop in enumerate(self.hops):
            expected_prev = self.hops[i - 1].hop_hash if i > 0 else "genesis"
            if hop.prev_hop_hash != expected_prev:
                return False
        return True

    def aggregate_quality(self) -> float:
        """Multiplicative quality composition across all hops."""
        quality = 1.0
        for hop in self.hops:
            if hop.quality_score is not None:
                quality *= hop.quality_score
        return quality


# ─── Delegation Protocol ────────────────────────────────────────────────────

@dataclass
class EntityInfo:
    """Basic entity information for delegation."""
    entity_id: str
    society_id: str
    trust_score: float
    atp_balance: float


class MultiHopDelegationProtocol:
    """
    Protocol for creating and managing multi-hop cross-federation
    delegation chains.

    Rules:
    1. Scope must narrow at each hop
    2. Budget must fit within parent's remaining budget
    3. Cross-federation hops incur 5% fee
    4. Trust minimum must be met by each delegate
    5. Sub-delegation count decrements at each hop
    """

    def __init__(self, cross_federation_fee_rate: float = 0.05,
                  max_chain_depth: int = 10):
        self.fee_rate = cross_federation_fee_rate
        self.max_chain_depth = max_chain_depth
        self.chains: Dict[str, DelegationChain] = {}

    def create_chain(self, origin: EntityInfo,
                      initial_scope: DelegationScope) -> DelegationChain:
        """Create a new delegation chain."""
        chain = DelegationChain(
            chain_id=secrets.token_hex(8),
            origin_society=origin.society_id,
            origin_entity=origin.entity_id,
            total_atp_allocated=initial_scope.max_budget,
        )
        self.chains[chain.chain_id] = chain
        return chain

    def add_hop(self, chain: DelegationChain,
                 delegator: EntityInfo,
                 delegate: EntityInfo,
                 child_scope: Optional[DelegationScope] = None,
                 budget: Optional[float] = None) -> Tuple[bool, str]:
        """Add a delegation hop to the chain."""
        # Depth check
        if chain.depth >= self.max_chain_depth:
            return False, "max_depth_exceeded"

        # Determine parent scope
        if chain.hops:
            parent_scope = chain.hops[-1].scope
            # Verify delegator is the current delegate
            if delegator.entity_id != chain.hops[-1].delegate_id:
                return False, "delegator_not_current_delegate"
        else:
            # First hop: origin is the delegator
            if delegator.entity_id != chain.origin_entity:
                return False, "delegator_not_origin"
            parent_scope = DelegationScope(
                allowed_actions=child_scope.allowed_actions if child_scope else set(),
                max_budget=chain.total_atp_allocated,
                max_sub_delegates=5,
                time_limit=86400.0,
                trust_minimum=0.3,
            )

        # Narrow scope
        if child_scope:
            narrowed = parent_scope.narrow(
                child_actions=child_scope.allowed_actions,
                child_budget=budget or child_scope.max_budget,
                child_max_subs=child_scope.max_sub_delegates,
                child_crossing=child_scope.federation_crossing_allowed,
            )
        else:
            narrowed = parent_scope.narrow(child_budget=budget)

        # Verify narrowing
        if not narrowed.is_subset_of(parent_scope):
            return False, "scope_not_narrowed"

        # Check sub-delegation allowance
        if parent_scope.max_sub_delegates <= 0 and chain.depth > 0:
            return False, "sub_delegation_exhausted"

        # Trust check
        if delegate.trust_score < narrowed.trust_minimum:
            return False, "trust_below_minimum"

        # Budget check
        hop_budget = budget or narrowed.max_budget
        if hop_budget > parent_scope.max_budget:
            return False, "budget_exceeds_parent"

        # Determine hop type and fee
        hop_type = HopType.INTRA_SOCIETY
        fee = 0.0
        if delegator.society_id != delegate.society_id:
            hop_type = HopType.CROSS_FEDERATION
            if not narrowed.federation_crossing_allowed:
                return False, "federation_crossing_not_allowed"
            fee = hop_budget * self.fee_rate

        # Create hop
        prev_hash = chain.hops[-1].hop_hash if chain.hops else "genesis"
        hop = DelegationHop(
            hop_id=secrets.token_hex(8),
            delegator_id=delegator.entity_id,
            delegate_id=delegate.entity_id,
            delegator_society=delegator.society_id,
            delegate_society=delegate.society_id,
            hop_type=hop_type,
            scope=narrowed,
            atp_allocated=hop_budget,
            atp_fee=fee,
            prev_hop_hash=prev_hash,
        )
        hop.compute_hash()

        chain.hops.append(hop)
        chain.total_fees += fee
        return True, "hop_added"

    def complete_hop(self, chain: DelegationChain,
                      hop_index: int, quality: float) -> bool:
        """Mark a hop as completed with quality score."""
        if hop_index < 0 or hop_index >= len(chain.hops):
            return False

        hop = chain.hops[hop_index]
        if hop.status != DelegationStatus.ACTIVE:
            return False

        hop.quality_score = max(0.0, min(1.0, quality))
        hop.status = DelegationStatus.COMPLETED
        hop.completed_at = time.time()
        return True

    def revoke_hop(self, chain: DelegationChain,
                    hop_index: int) -> int:
        """Revoke a hop and cascade revocation to all downstream hops."""
        if hop_index < 0 or hop_index >= len(chain.hops):
            return 0

        revoked = 0
        for i in range(hop_index, len(chain.hops)):
            if chain.hops[i].status == DelegationStatus.ACTIVE:
                chain.hops[i].status = DelegationStatus.REVOKED
                revoked += 1

        if all(h.status == DelegationStatus.REVOKED for h in chain.hops):
            chain.status = DelegationStatus.REVOKED

        return revoked

    def complete_chain(self, chain: DelegationChain) -> float:
        """Complete the entire chain and compute aggregate quality."""
        quality = chain.aggregate_quality()

        all_completed = all(
            h.status in (DelegationStatus.COMPLETED, DelegationStatus.REVOKED)
            for h in chain.hops
        )

        if all_completed:
            chain.status = DelegationStatus.COMPLETED

        return quality


# ─── Quality Rollup ─────────────────────────────────────────────────────────

@dataclass
class QualityReport:
    """Quality report for a delegation chain."""
    chain_id: str
    per_hop_quality: List[float]
    aggregate_quality: float
    overall_rating: QualityRating
    hop_count: int
    federation_crossings: int
    total_fees: float
    atp_efficiency: float  # net_work / total_allocated


class QualityRollup:
    """Compute quality rollup across a delegation chain."""

    @staticmethod
    def rate(score: float) -> QualityRating:
        if score >= 0.9:
            return QualityRating.EXCELLENT
        elif score >= 0.7:
            return QualityRating.GOOD
        elif score >= 0.5:
            return QualityRating.ACCEPTABLE
        elif score >= 0.3:
            return QualityRating.POOR
        return QualityRating.FAILED

    def compute(self, chain: DelegationChain) -> QualityReport:
        per_hop = []
        for hop in chain.hops:
            if hop.quality_score is not None:
                per_hop.append(hop.quality_score)
            else:
                per_hop.append(0.0)

        aggregate = chain.aggregate_quality()
        efficiency = 0.0
        if chain.total_atp_allocated > 0:
            efficiency = (chain.total_atp_allocated - chain.total_fees) / chain.total_atp_allocated

        return QualityReport(
            chain_id=chain.chain_id,
            per_hop_quality=per_hop,
            aggregate_quality=aggregate,
            overall_rating=self.rate(aggregate),
            hop_count=chain.depth,
            federation_crossings=chain.federation_crossings,
            total_fees=chain.total_fees,
            atp_efficiency=efficiency,
        )


# ─── Cross-Federation Audit Trail ───────────────────────────────────────────

@dataclass
class DelegationAuditEntry:
    """An entry in the cross-federation delegation audit trail."""
    entry_id: str
    chain_id: str
    hop_index: int
    event: str  # "created", "hop_added", "completed", "revoked"
    delegator: str
    delegate: str
    society_from: str
    society_to: str
    atp_amount: float
    quality: Optional[float]
    prev_hash: str
    entry_hash: str = ""
    timestamp: float = field(default_factory=time.time)

    def compute_hash(self) -> str:
        data = f"{self.chain_id}:{self.hop_index}:{self.event}:{self.prev_hash}"
        self.entry_hash = hashlib.sha256(data.encode()).hexdigest()[:32]
        return self.entry_hash


class DelegationAuditTrail:
    """Hash-chained audit trail spanning federation boundaries."""

    def __init__(self):
        self.entries: List[DelegationAuditEntry] = []

    def record_hop(self, chain: DelegationChain, hop_index: int,
                    event: str) -> DelegationAuditEntry:
        prev_hash = self.entries[-1].entry_hash if self.entries else "genesis"
        hop = chain.hops[hop_index]

        entry = DelegationAuditEntry(
            entry_id=secrets.token_hex(8),
            chain_id=chain.chain_id,
            hop_index=hop_index,
            event=event,
            delegator=hop.delegator_id,
            delegate=hop.delegate_id,
            society_from=hop.delegator_society,
            society_to=hop.delegate_society,
            atp_amount=hop.atp_allocated,
            quality=hop.quality_score,
            prev_hash=prev_hash,
        )
        entry.compute_hash()
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        for i, entry in enumerate(self.entries):
            expected_prev = self.entries[i - 1].entry_hash if i > 0 else "genesis"
            if entry.prev_hash != expected_prev:
                return False
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def run_checks():
    results = {}
    total = 0
    passed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal total, passed
        total += 1
        if condition:
            passed += 1
            results[name] = "PASS"
        else:
            results[name] = f"FAIL: {detail}"
            print(f"  FAIL: {name}: {detail}")

    # ── Section 1: Scope Narrowing ───────────────────────────────────────────

    scope = DelegationScope(
        allowed_actions={"read", "write", "compute"},
        max_budget=1000.0,
        max_sub_delegates=3,
        time_limit=86400.0,
        trust_minimum=0.3,
    )

    narrowed = scope.narrow(
        child_actions={"read", "compute"},
        child_budget=500.0,
        child_max_subs=2,
    )
    check("s1_actions_narrowed", narrowed.allowed_actions == {"read", "compute"})
    check("s1_budget_narrowed", narrowed.max_budget == 500.0)
    check("s1_subs_narrowed", narrowed.max_sub_delegates == 2)
    check("s1_is_subset", narrowed.is_subset_of(scope))

    # Cannot widen
    wider = scope.narrow(child_actions={"read", "write", "compute", "delete"})
    check("s1_no_widen", "delete" not in wider.allowed_actions)

    # Budget capped
    over = scope.narrow(child_budget=5000.0)
    check("s1_budget_capped", over.max_budget == 1000.0)

    # ── Section 2: Basic Chain Creation ──────────────────────────────────────

    proto = MultiHopDelegationProtocol()
    origin = EntityInfo("alice", "soc_x", trust_score=0.8, atp_balance=5000)

    chain = proto.create_chain(origin, scope)
    check("s2_chain_created", chain.chain_id != "")
    check("s2_origin", chain.origin_entity == "alice")
    check("s2_depth_0", chain.depth == 0)

    # ── Section 3: Single Hop — Intra-Society ────────────────────────────────

    bob = EntityInfo("bob", "soc_x", trust_score=0.7, atp_balance=3000)
    child_scope = DelegationScope(
        allowed_actions={"read", "compute"},
        max_budget=800.0,
        max_sub_delegates=2,
        time_limit=86400.0,
        trust_minimum=0.3,
    )

    ok, msg = proto.add_hop(chain, origin, bob, child_scope, budget=800.0)
    check("s3_hop_added", ok, msg)
    check("s3_depth_1", chain.depth == 1)
    check("s3_intra_society", chain.hops[0].hop_type == HopType.INTRA_SOCIETY)
    check("s3_no_fee", chain.hops[0].atp_fee == 0.0)
    check("s3_hash_chain", chain.hops[0].hop_hash != "")
    check("s3_prev_genesis", chain.hops[0].prev_hop_hash == "genesis")

    # ── Section 4: Cross-Federation Hop ──────────────────────────────────────

    carol = EntityInfo("carol", "soc_y", trust_score=0.65, atp_balance=2000)
    cross_scope = DelegationScope(
        allowed_actions={"read"},
        max_budget=400.0,
        max_sub_delegates=1,
        time_limit=86400.0,
        trust_minimum=0.3,
    )

    ok, msg = proto.add_hop(chain, bob, carol, cross_scope, budget=400.0)
    check("s4_cross_hop", ok, msg)
    check("s4_cross_type", chain.hops[1].hop_type == HopType.CROSS_FEDERATION)
    check("s4_fee_charged", chain.hops[1].atp_fee == 20.0,
          f"fee={chain.hops[1].atp_fee}")  # 5% of 400
    check("s4_net_budget", chain.hops[1].net_budget == 380.0)
    check("s4_depth_2", chain.depth == 2)
    check("s4_2_societies", len(chain.societies_involved) == 2)
    check("s4_1_crossing", chain.federation_crossings == 1)

    # ── Section 5: Third Hop — Another Federation ────────────────────────────

    dave = EntityInfo("dave", "soc_z", trust_score=0.6, atp_balance=1000)
    third_scope = DelegationScope(
        allowed_actions={"read"},
        max_budget=200.0,
        max_sub_delegates=0,
        time_limit=86400.0,
        trust_minimum=0.3,
    )

    ok, msg = proto.add_hop(chain, carol, dave, third_scope, budget=200.0)
    check("s5_third_hop", ok, msg)
    check("s5_depth_3", chain.depth == 3)
    check("s5_3_societies", len(chain.societies_involved) == 3)
    check("s5_2_crossings", chain.federation_crossings == 2)
    check("s5_total_fees", chain.total_fees == 30.0,
          f"fees={chain.total_fees}")  # 20 + 10

    # ── Section 6: Hash Chain Verification ───────────────────────────────────

    check("s6_hash_chain_valid", chain.verify_hash_chain())

    # Tamper detection
    original_hash = chain.hops[1].prev_hop_hash
    chain.hops[1].prev_hop_hash = "tampered"
    check("s6_tamper_detected", not chain.verify_hash_chain())
    chain.hops[1].prev_hop_hash = original_hash
    check("s6_restored", chain.verify_hash_chain())

    # ── Section 7: Quality Completion ────────────────────────────────────────

    proto.complete_hop(chain, 2, 0.9)   # dave: excellent
    proto.complete_hop(chain, 1, 0.85)  # carol: good
    proto.complete_hop(chain, 0, 0.95)  # bob: excellent

    aggregate = chain.aggregate_quality()
    check("s7_aggregate_quality", 0.7 < aggregate < 0.8,
          f"quality={aggregate:.4f}")  # 0.9 * 0.85 * 0.95 = 0.72675
    check("s7_multiplicative", abs(aggregate - 0.9 * 0.85 * 0.95) < 0.001)

    # ── Section 8: Quality Rollup ────────────────────────────────────────────

    rollup = QualityRollup()
    report = rollup.compute(chain)

    check("s8_per_hop_3", len(report.per_hop_quality) == 3)
    check("s8_rating_good", report.overall_rating == QualityRating.GOOD,
          f"rating={report.overall_rating}")
    check("s8_efficiency", 0.9 < report.atp_efficiency <= 1.0,
          f"eff={report.atp_efficiency}")
    check("s8_crossings_2", report.federation_crossings == 2)

    # ── Section 9: Revocation Cascade ────────────────────────────────────────

    rev_chain = proto.create_chain(origin, scope)
    proto.add_hop(rev_chain, origin, bob, child_scope, budget=800)
    carol2 = EntityInfo("carol2", "soc_y", trust_score=0.65, atp_balance=2000)
    proto.add_hop(rev_chain, bob, carol2, cross_scope, budget=400)
    dave2 = EntityInfo("dave2", "soc_z", trust_score=0.6, atp_balance=1000)
    proto.add_hop(rev_chain, carol2, dave2, third_scope, budget=200)

    # Revoke middle hop — should cascade to downstream
    revoked = proto.revoke_hop(rev_chain, 1)
    check("s9_2_revoked", revoked == 2, f"revoked={revoked}")
    check("s9_hop0_active", rev_chain.hops[0].status == DelegationStatus.ACTIVE)
    check("s9_hop1_revoked", rev_chain.hops[1].status == DelegationStatus.REVOKED)
    check("s9_hop2_revoked", rev_chain.hops[2].status == DelegationStatus.REVOKED)

    # Revoke first hop — all should be revoked
    revoked2 = proto.revoke_hop(rev_chain, 0)
    check("s9_all_revoked", revoked2 == 1)
    check("s9_chain_revoked", rev_chain.status == DelegationStatus.REVOKED)

    # ── Section 10: Scope Violation Rejection ────────────────────────────────

    fail_chain = proto.create_chain(origin, scope)
    proto.add_hop(fail_chain, origin, bob, child_scope, budget=800)

    # Try to widen scope
    wide_scope = DelegationScope(
        allowed_actions={"read", "write", "compute", "admin"},
        max_budget=2000.0,
        max_sub_delegates=5,
        time_limit=86400.0,
        trust_minimum=0.1,
    )
    eve = EntityInfo("eve", "soc_x", trust_score=0.9, atp_balance=5000)
    ok, msg = proto.add_hop(fail_chain, bob, eve, wide_scope, budget=2000)
    check("s10_scope_violation_rejected", not ok, msg)

    # ── Section 11: Trust Minimum Enforcement ────────────────────────────────

    low_trust = EntityInfo("untrusted", "soc_x", trust_score=0.1, atp_balance=5000)
    trust_chain = proto.create_chain(origin, scope)
    ok, msg = proto.add_hop(trust_chain, origin, low_trust, child_scope, budget=500)
    check("s11_trust_rejected", not ok)
    check("s11_trust_reason", msg == "trust_below_minimum", f"msg={msg}")

    # ── Section 12: Sub-Delegation Exhaustion ────────────────────────────────

    exhaust_scope = DelegationScope(
        allowed_actions={"read"},
        max_budget=500.0,
        max_sub_delegates=1,  # Only 1 sub-delegation allowed
        time_limit=86400.0,
        trust_minimum=0.3,
    )

    ex_chain = proto.create_chain(origin, exhaust_scope)
    b1 = EntityInfo("b1", "soc_x", trust_score=0.7, atp_balance=3000)
    ok, msg = proto.add_hop(ex_chain, origin, b1, exhaust_scope, budget=500)
    check("s12_first_hop_ok", ok, msg)

    b2 = EntityInfo("b2", "soc_x", trust_score=0.7, atp_balance=3000)
    # The narrowed scope from first hop should have max_sub_delegates=0
    sub_scope = DelegationScope(
        allowed_actions={"read"},
        max_budget=300.0,
        max_sub_delegates=0,
        time_limit=86400.0,
        trust_minimum=0.3,
    )
    ok, msg = proto.add_hop(ex_chain, b1, b2, sub_scope, budget=300)
    check("s12_second_hop_ok", ok, msg)

    b3 = EntityInfo("b3", "soc_x", trust_score=0.7, atp_balance=3000)
    ok, msg = proto.add_hop(ex_chain, b2, b3, sub_scope, budget=200)
    check("s12_third_hop_blocked", not ok)
    check("s12_exhaustion_reason", msg == "sub_delegation_exhausted", f"msg={msg}")

    # ── Section 13: Audit Trail ──────────────────────────────────────────────

    audit = DelegationAuditTrail()
    for i in range(chain.depth):
        audit.record_hop(chain, i, "hop_added")

    check("s13_3_entries", len(audit.entries) == 3)
    check("s13_chain_valid", audit.verify_chain())
    check("s13_genesis", audit.entries[0].prev_hash == "genesis")
    check("s13_chain_linked",
          audit.entries[1].prev_hash == audit.entries[0].entry_hash)
    check("s13_cross_society_logged",
          any(e.society_from != e.society_to for e in audit.entries))

    # Tamper detection
    audit.entries[1].prev_hash = "tampered"
    check("s13_tamper_detected", not audit.verify_chain())
    audit.entries[1].prev_hash = audit.entries[0].entry_hash
    check("s13_restore_valid", audit.verify_chain())

    # ── Section 14: Chain Completion ─────────────────────────────────────────

    complete_chain = proto.create_chain(origin, scope)
    proto.add_hop(complete_chain, origin, bob, child_scope, budget=800)
    carol3 = EntityInfo("carol3", "soc_y", trust_score=0.65, atp_balance=2000)
    proto.add_hop(complete_chain, bob, carol3, cross_scope, budget=400)

    proto.complete_hop(complete_chain, 0, 0.8)
    proto.complete_hop(complete_chain, 1, 0.75)

    quality = proto.complete_chain(complete_chain)
    check("s14_chain_completed", complete_chain.status == DelegationStatus.COMPLETED)
    check("s14_quality", abs(quality - 0.6) < 0.001,
          f"quality={quality}")  # 0.8 * 0.75 = 0.6

    # ── Section 15: Max Depth Enforcement ────────────────────────────────────

    deep_proto = MultiHopDelegationProtocol(max_chain_depth=3)
    deep_chain = deep_proto.create_chain(origin, scope)

    # Add 3 hops
    entities = [
        EntityInfo(f"e{i}", "soc_x", trust_score=0.7, atp_balance=3000)
        for i in range(4)
    ]
    prev = origin
    for i in range(3):
        sc = scope.narrow(child_budget=scope.max_budget - i * 100)
        ok, _ = deep_proto.add_hop(deep_chain, prev, entities[i], sc,
                                     budget=scope.max_budget - i * 100)
        check(f"s15_hop_{i}_ok", ok)
        prev = entities[i]

    # 4th hop should fail
    ok, msg = deep_proto.add_hop(deep_chain, entities[2], entities[3],
                                   scope.narrow(child_budget=100), budget=100)
    check("s15_max_depth_blocked", not ok)
    check("s15_depth_reason", msg == "max_depth_exceeded")

    # ── Section 16: Wrong Delegator Rejection ────────────────────────────────

    wrong_chain = proto.create_chain(origin, scope)
    proto.add_hop(wrong_chain, origin, bob, child_scope, budget=800)

    # Try to add hop from wrong entity (not bob)
    eve2 = EntityInfo("eve2", "soc_x", trust_score=0.7, atp_balance=3000)
    ok, msg = proto.add_hop(wrong_chain, eve2, carol,
                              cross_scope, budget=400)
    check("s16_wrong_delegator", not ok)
    check("s16_wrong_reason", msg == "delegator_not_current_delegate")

    # ── Section 17: Federation Crossing Disabled ─────────────────────────────

    no_cross_scope = DelegationScope(
        allowed_actions={"read"},
        max_budget=500.0,
        max_sub_delegates=2,
        time_limit=86400.0,
        trust_minimum=0.3,
        federation_crossing_allowed=False,
    )

    nc_chain = proto.create_chain(origin, no_cross_scope)
    proto.add_hop(nc_chain, origin, bob, no_cross_scope, budget=500)

    # Cross-federation should be blocked
    ok, msg = proto.add_hop(nc_chain, bob, carol,
                              no_cross_scope, budget=300)
    check("s17_crossing_blocked", not ok)
    check("s17_crossing_reason", msg == "federation_crossing_not_allowed")

    # ── Section 18: Performance ──────────────────────────────────────────────

    perf_proto = MultiHopDelegationProtocol(max_chain_depth=50)

    t0 = time.time()
    for _ in range(100):
        pc = perf_proto.create_chain(origin, scope)
        prev_ent = origin
        for i in range(5):
            ent = EntityInfo(f"p{i}", "soc_x" if i % 2 == 0 else "soc_y",
                              trust_score=0.7, atp_balance=3000)
            s = scope.narrow(child_budget=scope.max_budget - i * 100)
            perf_proto.add_hop(pc, prev_ent, ent, s,
                                 budget=scope.max_budget - i * 100)
            prev_ent = ent
    elapsed = time.time() - t0
    check("s18_500_hops_fast", elapsed < 2.0, f"elapsed={elapsed:.2f}s")

    # ── Section 19: Quality Rating Boundaries ────────────────────────────────

    check("s19_excellent", QualityRollup.rate(0.95) == QualityRating.EXCELLENT)
    check("s19_good", QualityRollup.rate(0.75) == QualityRating.GOOD)
    check("s19_acceptable", QualityRollup.rate(0.55) == QualityRating.ACCEPTABLE)
    check("s19_poor", QualityRollup.rate(0.35) == QualityRating.POOR)
    check("s19_failed", QualityRollup.rate(0.1) == QualityRating.FAILED)

    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"Multi-Hop Cross-Federation Delegation: {passed}/{total} checks passed")
    print(f"{'='*60}")

    if passed < total:
        print("\nFailed checks:")
        for name, result in results.items():
            if result.startswith("FAIL"):
                print(f"  {name}: {result}")

    return passed, total


if __name__ == "__main__":
    run_checks()
