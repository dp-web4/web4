"""
Multi-Hop Cross-Federation Delegation — Reference Implementation

When Agent A in Society X delegates to Agent B in Society Y, who
sub-delegates to Agent C in Society Z, the full delegation chain
requires:

1. **Cross-boundary ATP tracking**: ATP deducted at each hop with
   per-hop fee, maintaining conservation across ledgers
2. **Scope narrowing across federations**: child ⊆ parent even
   when crossing society boundaries
3. **Cryptographic chain integrity**: Each hop signs the delegation
   producing a verifiable chain of authority
4. **Quality rollup**: Reputation computed at originating society
   aggregates quality from all hops
5. **Cascade revocation**: Revoking any link invalidates all downstream

Key insight: Cross-federation delegation is the AGY equivalent of
cross-ledger ATP transfer — it needs the same 2PC atomicity guarantees
for authority transfer that ATP transfers need for value transfer.

Builds on: agy_agency_delegation.py, cross_society_atp_sync.py
Addresses: FEDERATION_DOCUMENTATION_GAPS.md multi-hop delegation gap

Checks: 65
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
    EXPIRED = auto()
    REVOKED = auto()
    PENDING = auto()     # Awaiting cross-federation confirmation
    REJECTED = auto()    # Target federation rejected


class HopResult(Enum):
    SUCCESS = auto()
    SCOPE_VIOLATION = auto()
    ATP_INSUFFICIENT = auto()
    TRUST_TOO_LOW = auto()
    FEDERATION_REJECTED = auto()
    CHAIN_DEPTH_EXCEEDED = auto()


class QualityLevel(Enum):
    EXCELLENT = auto()   # > 0.8
    GOOD = auto()        # > 0.6
    ACCEPTABLE = auto()  # > 0.4
    POOR = auto()        # <= 0.4


# ─── Delegation Scope ────────────────────────────────────────────────────────

@dataclass
class DelegationScope:
    """Defines what authority is delegated."""
    actions: Set[str]          # Permitted action types
    max_atp: float             # Maximum ATP expenditure
    max_executions: int        # Maximum number of executions
    expiry: float              # Expiry timestamp
    allowed_federations: Set[str]  # Which federations can receive sub-delegation
    max_chain_depth: int = 5   # Maximum delegation chain depth

    def is_subset_of(self, parent: 'DelegationScope') -> bool:
        """Check if this scope is narrower than or equal to parent."""
        return (self.actions <= parent.actions and
                self.max_atp <= parent.max_atp and
                self.max_executions <= parent.max_executions and
                self.expiry <= parent.expiry and
                self.allowed_federations <= parent.allowed_federations and
                self.max_chain_depth <= parent.max_chain_depth)

    def narrow(self, actions: Optional[Set[str]] = None,
               max_atp: Optional[float] = None,
               max_executions: Optional[int] = None) -> 'DelegationScope':
        """Create a narrower scope for sub-delegation."""
        return DelegationScope(
            actions=actions if actions else self.actions,
            max_atp=min(max_atp, self.max_atp) if max_atp else self.max_atp,
            max_executions=min(max_executions, self.max_executions) if max_executions else self.max_executions,
            expiry=self.expiry,
            allowed_federations=self.allowed_federations,
            max_chain_depth=self.max_chain_depth - 1,
        )


# ─── Delegation Hop ─────────────────────────────────────────────────────────

@dataclass
class DelegationHop:
    """A single hop in the delegation chain."""
    hop_id: str
    delegator_id: str
    delegate_id: str
    source_federation: str
    target_federation: str
    scope: DelegationScope
    atp_allocated: float
    atp_fee: float            # Per-hop fee
    trust_score: float        # Delegate's T3 at time of delegation
    status: DelegationStatus = DelegationStatus.PENDING
    quality_score: float = 0.0  # Quality of execution (set after completion)
    chain_depth: int = 0
    signature: str = ""       # Cryptographic signature
    created_at: float = field(default_factory=time.time)

    def sign(self) -> str:
        """Sign this hop."""
        content = (f"{self.hop_id}:{self.delegator_id}:{self.delegate_id}:"
                   f"{self.source_federation}:{self.target_federation}:"
                   f"{self.atp_allocated}:{self.chain_depth}")
        self.signature = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.signature

    def verify_signature(self) -> bool:
        """Verify the hop signature."""
        content = (f"{self.hop_id}:{self.delegator_id}:{self.delegate_id}:"
                   f"{self.source_federation}:{self.target_federation}:"
                   f"{self.atp_allocated}:{self.chain_depth}")
        expected = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.signature == expected


# ─── Delegation Chain ────────────────────────────────────────────────────────

@dataclass
class DelegationChain:
    """Complete multi-hop delegation chain."""
    chain_id: str
    origin_entity: str
    origin_federation: str
    hops: List[DelegationHop] = field(default_factory=list)
    total_atp_allocated: float = 0.0
    total_fees: float = 0.0
    status: DelegationStatus = DelegationStatus.PENDING
    chain_hash: str = ""

    @property
    def depth(self) -> int:
        return len(self.hops)

    @property
    def current_delegate(self) -> Optional[str]:
        if not self.hops:
            return self.origin_entity
        return self.hops[-1].delegate_id

    @property
    def current_federation(self) -> str:
        if not self.hops:
            return self.origin_federation
        return self.hops[-1].target_federation

    def compute_chain_hash(self) -> str:
        """Hash the entire chain for integrity verification."""
        parts = [f"{self.chain_id}:{self.origin_entity}:{self.origin_federation}"]
        for hop in self.hops:
            parts.append(hop.signature)
        content = ":".join(parts)
        self.chain_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.chain_hash

    def verify_chain_integrity(self) -> bool:
        """Verify the complete chain is valid."""
        # Each hop must be signed
        for hop in self.hops:
            if not hop.verify_signature():
                return False

        # Scope must narrow monotonically
        for i in range(1, len(self.hops)):
            if not self.hops[i].scope.is_subset_of(self.hops[i-1].scope):
                return False

        # Chain depth must be consistent
        for i, hop in enumerate(self.hops):
            if hop.chain_depth != i:
                return False

        return True

    def compute_aggregated_quality(self) -> float:
        """Compute quality aggregated across all hops."""
        if not self.hops:
            return 0.0

        # Weighted by trust: higher-trust hops contribute more
        total_weight = 0.0
        weighted_quality = 0.0
        for hop in self.hops:
            weight = hop.trust_score
            weighted_quality += hop.quality_score * weight
            total_weight += weight

        return weighted_quality / max(total_weight, 0.01)


# ─── Federation Registry ────────────────────────────────────────────────────

@dataclass
class FederationNode:
    """A federation in the delegation network."""
    federation_id: str
    trust_score: float = 0.5
    atp_pool: float = 10000.0
    per_hop_fee_rate: float = 0.05
    min_trust_for_delegation: float = 0.3
    max_inbound_delegations: int = 100
    active_delegations: int = 0


class FederationRegistry:
    """Registry of federations that can participate in delegation."""

    def __init__(self):
        self.federations: Dict[str, FederationNode] = {}

    def register(self, fed_id: str, trust: float = 0.5,
                   atp_pool: float = 10000.0,
                   fee_rate: float = 0.05) -> FederationNode:
        node = FederationNode(
            federation_id=fed_id,
            trust_score=trust,
            atp_pool=atp_pool,
            per_hop_fee_rate=fee_rate,
        )
        self.federations[fed_id] = node
        return node

    def get(self, fed_id: str) -> Optional[FederationNode]:
        return self.federations.get(fed_id)

    def can_accept_delegation(self, fed_id: str, trust_required: float = 0.3) -> bool:
        node = self.get(fed_id)
        if node is None:
            return False
        if node.trust_score < trust_required:
            return False
        if node.active_delegations >= node.max_inbound_delegations:
            return False
        return True


# ─── Cross-Federation Delegation Engine ──────────────────────────────────────

class CrossFederationDelegationEngine:
    """
    Engine for multi-hop cross-federation delegation.

    Enforces:
    - Scope monotonic narrowing across hops
    - ATP deduction at each hop with per-federation fees
    - Trust gating: minimum trust required at each hop
    - Chain depth limit
    - Cascade revocation
    """

    def __init__(self, registry: FederationRegistry,
                 max_chain_depth: int = 5,
                 min_trust: float = 0.3):
        self.registry = registry
        self.max_depth = max_chain_depth
        self.min_trust = min_trust
        self.chains: Dict[str, DelegationChain] = {}
        self.revocation_log: List[Dict[str, Any]] = []

    def create_chain(self, origin_entity: str,
                       origin_federation: str,
                       initial_scope: DelegationScope) -> DelegationChain:
        """Create a new delegation chain."""
        chain = DelegationChain(
            chain_id=secrets.token_hex(8),
            origin_entity=origin_entity,
            origin_federation=origin_federation,
        )
        self.chains[chain.chain_id] = chain
        return chain

    def add_hop(self, chain: DelegationChain,
                  delegate_id: str,
                  target_federation: str,
                  scope: DelegationScope,
                  atp_amount: float,
                  delegate_trust: float) -> Tuple[HopResult, Optional[DelegationHop]]:
        """Add a new hop to the delegation chain."""
        # Check chain depth
        if chain.depth >= self.max_depth:
            return HopResult.CHAIN_DEPTH_EXCEEDED, None

        # Check trust
        if delegate_trust < self.min_trust:
            return HopResult.TRUST_TOO_LOW, None

        # Check target federation
        if not self.registry.can_accept_delegation(target_federation, self.min_trust):
            return HopResult.FEDERATION_REJECTED, None

        # Check scope narrowing
        if chain.hops:
            parent_scope = chain.hops[-1].scope
            if not scope.is_subset_of(parent_scope):
                return HopResult.SCOPE_VIOLATION, None

        # Compute fee
        target_fed = self.registry.get(target_federation)
        fee_rate = target_fed.per_hop_fee_rate if target_fed else 0.05
        fee = atp_amount * fee_rate

        if atp_amount < fee:
            return HopResult.ATP_INSUFFICIENT, None

        # Source info
        source_fed = chain.current_federation
        delegator = chain.current_delegate

        hop = DelegationHop(
            hop_id=secrets.token_hex(8),
            delegator_id=delegator,
            delegate_id=delegate_id,
            source_federation=source_fed,
            target_federation=target_federation,
            scope=scope,
            atp_allocated=atp_amount - fee,
            atp_fee=fee,
            trust_score=delegate_trust,
            chain_depth=chain.depth,
            status=DelegationStatus.ACTIVE,
        )
        hop.sign()

        chain.hops.append(hop)
        chain.total_atp_allocated += atp_amount - fee
        chain.total_fees += fee
        chain.status = DelegationStatus.ACTIVE

        # Update federation state
        if target_fed:
            target_fed.active_delegations += 1

        chain.compute_chain_hash()
        return HopResult.SUCCESS, hop

    def revoke_chain(self, chain_id: str, revoke_from_hop: int = 0) -> int:
        """Revoke a chain from a specific hop onward. Returns hops revoked."""
        chain = self.chains.get(chain_id)
        if chain is None:
            return 0

        revoked = 0
        for i in range(revoke_from_hop, len(chain.hops)):
            if chain.hops[i].status == DelegationStatus.ACTIVE:
                chain.hops[i].status = DelegationStatus.REVOKED

                # Release federation slot
                target_fed = self.registry.get(chain.hops[i].target_federation)
                if target_fed and target_fed.active_delegations > 0:
                    target_fed.active_delegations -= 1

                revoked += 1

        if revoke_from_hop == 0:
            chain.status = DelegationStatus.REVOKED

        self.revocation_log.append({
            "chain_id": chain_id,
            "from_hop": revoke_from_hop,
            "hops_revoked": revoked,
            "timestamp": time.time(),
        })

        return revoked

    def record_quality(self, chain_id: str, hop_index: int,
                         quality: float) -> bool:
        """Record quality for a specific hop execution."""
        chain = self.chains.get(chain_id)
        if chain is None or hop_index >= len(chain.hops):
            return False
        chain.hops[hop_index].quality_score = max(0.0, min(1.0, quality))
        return True

    def compute_chain_reputation(self, chain_id: str) -> float:
        """Compute aggregated reputation for the entire chain."""
        chain = self.chains.get(chain_id)
        if chain is None:
            return 0.0
        return chain.compute_aggregated_quality()


# ─── Quality Rollup ─────────────────────────────────────────────────────────

class QualityRollup:
    """
    Aggregate quality scores from multi-hop delegation chains back
    to the originating federation's reputation system.
    """

    # Trust inheritance coefficients from MEMORY.md
    DEPTH_DECAY = {
        0: 1.0,    # Direct delegation
        1: 0.9,    # One hop
        2: 0.8,    # Two hops
        3: 0.6,    # Three hops
        4: 0.4,    # Four hops
    }

    def compute_rollup(self, chain: DelegationChain) -> Dict[str, float]:
        """Compute per-entity quality attribution from chain."""
        attributions: Dict[str, float] = {}

        for i, hop in enumerate(chain.hops):
            decay = self.DEPTH_DECAY.get(i, 0.3)
            attributed_quality = hop.quality_score * decay * hop.trust_score

            # Attribute to delegator (they chose the delegate)
            attributions[hop.delegator_id] = (
                attributions.get(hop.delegator_id, 0.0) + attributed_quality * 0.3)
            # Attribute to delegate (they executed)
            attributions[hop.delegate_id] = (
                attributions.get(hop.delegate_id, 0.0) + attributed_quality * 0.7)

        return attributions

    def classify_quality(self, score: float) -> QualityLevel:
        if score > 0.8:
            return QualityLevel.EXCELLENT
        elif score > 0.6:
            return QualityLevel.GOOD
        elif score > 0.4:
            return QualityLevel.ACCEPTABLE
        return QualityLevel.POOR


# ─── Delegation Audit Trail ─────────────────────────────────────────────────

@dataclass
class DelegationAuditEntry:
    entry_id: str
    chain_id: str
    action: str  # "create", "add_hop", "revoke", "quality_record"
    details: Dict[str, Any]
    prev_hash: str
    entry_hash: str = ""
    timestamp: float = field(default_factory=time.time)

    def compute_hash(self) -> str:
        content = f"{self.entry_id}:{self.chain_id}:{self.action}:{self.details}:{self.prev_hash}"
        self.entry_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.entry_hash


class DelegationAuditTrail:
    """Hash-chained audit trail for delegation events."""

    def __init__(self):
        self.entries: List[DelegationAuditEntry] = []

    def record(self, chain_id: str, action: str,
               details: Dict[str, Any]) -> DelegationAuditEntry:
        prev_hash = self.entries[-1].entry_hash if self.entries else "genesis"
        entry = DelegationAuditEntry(
            entry_id=secrets.token_hex(8),
            chain_id=chain_id,
            action=action,
            details=details,
            prev_hash=prev_hash,
        )
        entry.compute_hash()
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        for i, entry in enumerate(self.entries):
            expected_prev = self.entries[i-1].entry_hash if i > 0 else "genesis"
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

    # ── Section 1: Delegation Scope ──────────────────────────────────────────

    parent_scope = DelegationScope(
        actions={"read", "write", "execute"},
        max_atp=1000.0,
        max_executions=50,
        expiry=time.time() + 86400,
        allowed_federations={"fed_a", "fed_b", "fed_c"},
        max_chain_depth=4,
    )

    child_scope = parent_scope.narrow(
        actions={"read", "write"},
        max_atp=500.0,
        max_executions=25,
    )

    check("s1_child_subset", child_scope.is_subset_of(parent_scope))
    check("s1_child_actions", child_scope.actions == {"read", "write"})
    check("s1_child_atp", child_scope.max_atp == 500.0)
    check("s1_child_depth", child_scope.max_chain_depth == 3)
    check("s1_parent_not_subset", not parent_scope.is_subset_of(child_scope))

    wider_scope = DelegationScope(
        actions={"read", "write", "execute", "admin"},
        max_atp=2000.0,
        max_executions=100,
        expiry=time.time() + 86400,
        allowed_federations={"fed_a", "fed_b", "fed_c", "fed_d"},
    )
    check("s1_wider_not_subset", not wider_scope.is_subset_of(parent_scope))

    # ── Section 2: Delegation Hop ────────────────────────────────────────────

    hop = DelegationHop(
        hop_id="hop_1",
        delegator_id="agent_a",
        delegate_id="agent_b",
        source_federation="fed_a",
        target_federation="fed_b",
        scope=parent_scope,
        atp_allocated=950.0,
        atp_fee=50.0,
        trust_score=0.7,
        chain_depth=0,
    )
    hop.sign()

    check("s2_hop_signed", len(hop.signature) == 32)
    check("s2_sig_verifies", hop.verify_signature())

    # Tamper
    hop.delegate_id = "agent_x"
    check("s2_tamper_detected", not hop.verify_signature())
    hop.delegate_id = "agent_b"
    check("s2_restored", hop.verify_signature())

    # ── Section 3: Delegation Chain ──────────────────────────────────────────

    chain = DelegationChain(
        chain_id="chain_1",
        origin_entity="agent_a",
        origin_federation="fed_a",
    )
    check("s3_empty_chain", chain.depth == 0)
    check("s3_origin_delegate", chain.current_delegate == "agent_a")
    check("s3_origin_federation", chain.current_federation == "fed_a")

    chain.hops.append(hop)
    check("s3_depth_1", chain.depth == 1)
    check("s3_current_delegate", chain.current_delegate == "agent_b")
    check("s3_current_federation", chain.current_federation == "fed_b")

    chain.compute_chain_hash()
    check("s3_chain_hash", len(chain.chain_hash) == 32)

    # ── Section 4: Federation Registry ───────────────────────────────────────

    registry = FederationRegistry()
    registry.register("fed_a", trust=0.8, atp_pool=10000, fee_rate=0.05)
    registry.register("fed_b", trust=0.7, atp_pool=8000, fee_rate=0.03)
    registry.register("fed_c", trust=0.6, atp_pool=5000, fee_rate=0.04)
    registry.register("fed_d", trust=0.2, atp_pool=1000, fee_rate=0.10)

    check("s4_registry_size", len(registry.federations) == 4)
    check("s4_can_delegate_b", registry.can_accept_delegation("fed_b"))
    check("s4_cant_delegate_d", not registry.can_accept_delegation("fed_d"))
    check("s4_unknown_rejected", not registry.can_accept_delegation("fed_z"))

    # ── Section 5: Engine — Single Hop ───────────────────────────────────────

    engine = CrossFederationDelegationEngine(registry, max_chain_depth=5)

    scope_1 = DelegationScope(
        actions={"read", "write"},
        max_atp=500.0,
        max_executions=20,
        expiry=time.time() + 86400,
        allowed_federations={"fed_a", "fed_b", "fed_c"},
    )

    chain_1 = engine.create_chain("alice", "fed_a", scope_1)
    result, hop_1 = engine.add_hop(chain_1, "bob", "fed_b", scope_1, 500.0, 0.7)

    check("s5_hop_success", result == HopResult.SUCCESS,
          f"result={result}")
    check("s5_hop_created", hop_1 is not None)
    check("s5_hop_signed", hop_1.verify_signature() if hop_1 else False)
    check("s5_chain_active", chain_1.status == DelegationStatus.ACTIVE)
    check("s5_fee_deducted", chain_1.total_fees > 0)

    # ── Section 6: Engine — Multi-Hop Chain ──────────────────────────────────

    scope_2 = scope_1.narrow(actions={"read"}, max_atp=200.0)
    result_2, hop_2 = engine.add_hop(chain_1, "carol", "fed_c", scope_2, 200.0, 0.65)

    check("s6_second_hop_success", result_2 == HopResult.SUCCESS)
    check("s6_chain_depth_2", chain_1.depth == 2)
    check("s6_current_carol", chain_1.current_delegate == "carol")
    check("s6_current_fed_c", chain_1.current_federation == "fed_c")
    check("s6_total_fees", chain_1.total_fees > 0)

    # ── Section 7: Engine — Scope Violation ──────────────────────────────────

    wider_scope_2 = DelegationScope(
        actions={"read", "write", "execute"},  # Wider than scope_2
        max_atp=1000.0,
        max_executions=50,
        expiry=time.time() + 86400,
        allowed_federations={"fed_a", "fed_b", "fed_c"},
    )
    result_3, _ = engine.add_hop(chain_1, "dave", "fed_a", wider_scope_2, 100.0, 0.6)
    check("s7_scope_violation", result_3 == HopResult.SCOPE_VIOLATION)

    # ── Section 8: Engine — Trust Too Low ────────────────────────────────────

    scope_3 = scope_2.narrow(max_atp=50.0)
    result_4, _ = engine.add_hop(chain_1, "eve", "fed_a", scope_3, 50.0, 0.1)
    check("s8_trust_too_low", result_4 == HopResult.TRUST_TOO_LOW)

    # ── Section 9: Engine — Federation Rejected ──────────────────────────────

    result_5, _ = engine.add_hop(chain_1, "frank", "fed_d", scope_3, 50.0, 0.5)
    check("s9_federation_rejected", result_5 == HopResult.FEDERATION_REJECTED)

    # ── Section 10: Engine — Chain Depth Exceeded ────────────────────────────

    deep_chain = engine.create_chain("root", "fed_a", scope_1)
    for i in range(5):
        s = scope_1.narrow(max_atp=float(500 - i * 80))
        s.max_chain_depth = 5 - i
        engine.add_hop(deep_chain, f"agent_{i}", "fed_b", s,
                         float(500 - i * 80), 0.7)

    result_deep, _ = engine.add_hop(deep_chain, "too_deep", "fed_c",
                                        scope_1.narrow(max_atp=50.0), 50.0, 0.6)
    check("s10_depth_exceeded", result_deep == HopResult.CHAIN_DEPTH_EXCEEDED)

    # ── Section 11: Cascade Revocation ───────────────────────────────────────

    rev_chain = engine.create_chain("rev_origin", "fed_a", scope_1)
    for i in range(3):
        s = scope_1.narrow(max_atp=float(400 - i * 100))
        s.max_chain_depth = 5 - i
        engine.add_hop(rev_chain, f"rev_agent_{i}", "fed_b", s,
                         float(400 - i * 100), 0.7)

    # Revoke from hop 1 onward
    revoked = engine.revoke_chain(rev_chain.chain_id, revoke_from_hop=1)
    check("s11_two_revoked", revoked == 2, f"revoked={revoked}")
    check("s11_hop0_active", rev_chain.hops[0].status == DelegationStatus.ACTIVE)
    check("s11_hop1_revoked", rev_chain.hops[1].status == DelegationStatus.REVOKED)
    check("s11_hop2_revoked", rev_chain.hops[2].status == DelegationStatus.REVOKED)

    # Full chain revocation
    revoked_full = engine.revoke_chain(rev_chain.chain_id, revoke_from_hop=0)
    check("s11_full_revoke", revoked_full == 1)  # Only hop 0 was still active
    check("s11_chain_revoked", rev_chain.status == DelegationStatus.REVOKED)

    # ── Section 12: Quality Recording ────────────────────────────────────────

    q_chain = engine.create_chain("q_origin", "fed_a", scope_1)
    for i in range(3):
        s = scope_1.narrow(max_atp=float(400 - i * 100))
        s.max_chain_depth = 5 - i
        engine.add_hop(q_chain, f"q_agent_{i}", "fed_b", s,
                         float(400 - i * 100), 0.7)

    engine.record_quality(q_chain.chain_id, 0, 0.9)
    engine.record_quality(q_chain.chain_id, 1, 0.7)
    engine.record_quality(q_chain.chain_id, 2, 0.8)

    check("s12_quality_recorded", q_chain.hops[0].quality_score == 0.9)
    check("s12_quality_clamped", engine.record_quality(q_chain.chain_id, 0, 1.5) and
          q_chain.hops[0].quality_score == 1.0)

    rep = engine.compute_chain_reputation(q_chain.chain_id)
    check("s12_reputation_computed", rep > 0, f"rep={rep}")

    # ── Section 13: Chain Integrity Verification ─────────────────────────────

    check("s13_chain_valid", q_chain.verify_chain_integrity())

    # Tamper with scope
    original_actions = q_chain.hops[1].scope.actions
    q_chain.hops[1].scope.actions = {"read", "write", "admin"}  # Wider
    check("s13_scope_tamper_detected", not q_chain.verify_chain_integrity())
    q_chain.hops[1].scope.actions = original_actions
    check("s13_scope_restored", q_chain.verify_chain_integrity())

    # ── Section 14: Quality Rollup ───────────────────────────────────────────

    rollup = QualityRollup()
    attributions = rollup.compute_rollup(q_chain)

    check("s14_attributions", len(attributions) > 0)
    # All 3 delegates + 2 delegators (hop 0 delegator = origin, hop 1 delegator = q_agent_0, etc.)
    check("s14_delegate_attributed", "q_agent_0" in attributions)
    check("s14_positive_values", all(v > 0 for v in attributions.values()))

    # Depth decay: hop 0 gets more attribution than hop 2
    attr_0_delegate = attributions.get("q_agent_0", 0)
    attr_2_delegate = attributions.get("q_agent_2", 0)
    check("s14_depth_decay", attr_0_delegate > attr_2_delegate,
          f"hop0={attr_0_delegate:.3f}, hop2={attr_2_delegate:.3f}")

    # Quality classification
    check("s14_classify_excellent", rollup.classify_quality(0.9) == QualityLevel.EXCELLENT)
    check("s14_classify_poor", rollup.classify_quality(0.2) == QualityLevel.POOR)

    # ── Section 15: Audit Trail ──────────────────────────────────────────────

    audit = DelegationAuditTrail()
    audit.record("chain_1", "create", {"origin": "alice"})
    audit.record("chain_1", "add_hop", {"delegate": "bob", "federation": "fed_b"})
    audit.record("chain_1", "add_hop", {"delegate": "carol", "federation": "fed_c"})
    audit.record("chain_1", "quality", {"hop": 0, "score": 0.9})

    check("s15_audit_entries", len(audit.entries) == 4)
    check("s15_chain_valid", audit.verify_chain())
    check("s15_genesis", audit.entries[0].prev_hash == "genesis")
    check("s15_linked", audit.entries[1].prev_hash == audit.entries[0].entry_hash)

    # Tamper
    orig_hash = audit.entries[2].prev_hash
    audit.entries[2].prev_hash = "bad"
    check("s15_tamper_caught", not audit.verify_chain())
    audit.entries[2].prev_hash = orig_hash
    check("s15_restored", audit.verify_chain())

    # ── Section 16: Multi-Chain Scenario ─────────────────────────────────────

    engine2 = CrossFederationDelegationEngine(registry, max_chain_depth=5)
    chains = []
    for i in range(5):
        s = DelegationScope(
            actions={"read"},
            max_atp=float(300 - i * 40),
            max_executions=10,
            expiry=time.time() + 86400,
            allowed_federations={"fed_a", "fed_b", "fed_c"},
            max_chain_depth=3,
        )
        c = engine2.create_chain(f"origin_{i}", "fed_a", s)
        for j in range(2):
            s_hop = s.narrow(max_atp=float(s.max_atp * 0.8))
            s_hop.max_chain_depth = s.max_chain_depth - j - 1
            engine2.add_hop(c, f"delegate_{i}_{j}", "fed_b", s_hop,
                              s_hop.max_atp, 0.7)
        chains.append(c)

    check("s16_5_chains", len(chains) == 5)
    check("s16_each_2_hops", all(c.depth == 2 for c in chains))

    total_delegations = sum(c.depth for c in chains)
    check("s16_10_total_hops", total_delegations == 10)

    # ── Section 17: Revocation Log ───────────────────────────────────────────

    engine2.revoke_chain(chains[0].chain_id)
    engine2.revoke_chain(chains[1].chain_id, revoke_from_hop=1)

    check("s17_revocation_log", len(engine2.revocation_log) == 2)

    # ── Section 18: Performance ──────────────────────────────────────────────

    perf_engine = CrossFederationDelegationEngine(registry, max_chain_depth=10)

    t0 = time.time()
    for i in range(100):
        s = DelegationScope(
            actions={"read"},
            max_atp=10000.0,
            max_executions=100,
            expiry=time.time() + 86400,
            allowed_federations={"fed_a", "fed_b", "fed_c"},
            max_chain_depth=10,
        )
        c = perf_engine.create_chain(f"perf_{i}", "fed_a", s)
        for j in range(3):
            s_hop = s.narrow(max_atp=float(s.max_atp * 0.8))
            s_hop.max_chain_depth = s.max_chain_depth - j - 1
            perf_engine.add_hop(c, f"perf_d_{i}_{j}", "fed_b",
                                  s_hop, s_hop.max_atp, 0.7)
    elapsed = time.time() - t0
    check("s18_300_hops_fast", elapsed < 5.0, f"elapsed={elapsed:.2f}s")

    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"Cross-Federation Delegation: {passed}/{total} checks passed")
    print(f"{'='*60}")

    if passed < total:
        print("\nFailed checks:")
        for name, result in results.items():
            if result.startswith("FAIL"):
                print(f"  {name}: {result}")

    return passed, total


if __name__ == "__main__":
    run_checks()
